"""The look model: OpenAI CLIP ViT-B/32 (MIT), float32 ONNX export (Xenova/clip-vit-base-patch32), run on CPU
by onnxruntime. One 512-dimension space for pictures and words: a thumbnail's vector (the vision tower) and a query's
vector (the text tower) are compared by cosine, so a query finds a model by what it looks like. Fetched once into
~/.argonia/models (580 MB), never committed; the sha256 of each file is checked against MODEL_FILES. Float32, not
the int8 export: on our thumbnails int8 ranked the grave-stakes 234th of 1,520 for "grave marker post", float32
10th, at the same speed (about 0.1 s a picture)."""
from __future__ import annotations

import hashlib
import os
import urllib.request
from pathlib import Path

import numpy as np

MODEL = "clip-vit-base-patch32"
REPO = "https://huggingface.co/Xenova/clip-vit-base-patch32/resolve/main/"
MODEL_FILES = {
    "vision_model.onnx": ("onnx/vision_model.onnx", "fd6e1402a588279d1723c7534d4bcba5bc0b14b47dfab0e46f8c47b8270d7d40"),
    "text_model.onnx": ("onnx/text_model.onnx", "3f6571f5bad13a97c469c1622e1cfc4d9aef78b79fdbfcff804ca357bfada8cc"),
    "tokenizer.json": ("tokenizer.json", "f7f3b7af117d467b58374797691a6438d3e6b9e9cef800dfd5dced7f697a90cd"),
}
DIM = 512
SIZE = 224
EOS = 49407
MEAN = np.array([0.48145466, 0.4578275, 0.40821073], np.float32)
STD = np.array([0.26862954, 0.26130258, 0.27577711], np.float32)


def model_dir() -> Path:
    return Path(os.environ.get("ARGONIA_MODELS", Path.home() / ".argonia" / "models")) / MODEL


def fetch() -> Path:
    d = model_dir()
    d.mkdir(parents=True, exist_ok=True)
    for name, (remote, sha) in MODEL_FILES.items():
        p = d / name
        if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest() == sha:
            continue
        tmp = p.with_suffix(".part")
        urllib.request.urlretrieve(REPO + remote, tmp)
        got = hashlib.sha256(tmp.read_bytes()).hexdigest()
        if got != sha:
            tmp.unlink()
            raise RuntimeError(f"{name}: sha256 {got} is not the pinned {sha}")
        tmp.replace(p)
    return d


def _session(p: Path, threads: int):
    import onnxruntime as ort
    so = ort.SessionOptions()
    so.intra_op_num_threads = threads
    so.inter_op_num_threads = 1
    return ort.InferenceSession(str(p), so, providers=["CPUExecutionProvider"])


def pixels(img) -> np.ndarray:
    """A PIL image as CLIP's input: RGB, resized to 224 (square thumbnails need no crop), normalised, CHW."""
    from PIL import Image
    a = np.asarray(img.convert("RGB").resize((SIZE, SIZE), Image.BICUBIC), np.float32) / 255.0
    return ((a - MEAN) / STD).transpose(2, 0, 1)


def unit(x: np.ndarray) -> np.ndarray:
    return x / np.maximum(np.linalg.norm(x, axis=1, keepdims=True), 1e-9)


class Clip:
    def __init__(self, threads: int | None = None) -> None:
        self.dir = fetch()
        self.threads = threads or int(os.environ.get("SEARCH_THREADS", "2"))
        self._text = self._vision = self._tok = None

    def text(self, texts: list[str]) -> np.ndarray:
        if self._text is None:
            from tokenizers import Tokenizer
            self._tok = Tokenizer.from_file(str(self.dir / "tokenizer.json"))
            self._tok.enable_truncation(77)
            self._text = _session(self.dir / "text_model.onnx", self.threads)
        enc = [self._tok.encode(t.lower()).ids for t in texts]
        n = max(len(e) for e in enc)
        ids = np.array([e + [EOS] * (n - len(e)) for e in enc], np.int64)   # the tower pools at the first EOS
        return unit(self._text.run(None, {"input_ids": ids})[0].astype(np.float32))

    def images(self, imgs: list, batch: int = 32) -> np.ndarray:
        if self._vision is None:
            self._vision = _session(self.dir / "vision_model.onnx", self.threads)
        out = np.zeros((len(imgs), DIM), np.float32)
        for s in range(0, len(imgs), batch):
            px = np.stack([pixels(i) for i in imgs[s:s + batch]])
            out[s:s + len(px)] = self._vision.run(None, {"pixel_values": px})[0]
        return unit(out)
