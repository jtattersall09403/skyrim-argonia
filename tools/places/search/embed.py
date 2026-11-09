"""The embedding model: BAAI bge-small-en-v1.5 (MIT), int8-quantised ONNX export (Xenova/bge-small-en-v1.5), run
on CPU by onnxruntime. 384 dimensions, CLS pooling, unit length. Fetched once into ~/.argonia/models (34 MB),
never committed; the sha256 of each file is checked against MODEL_FILES."""
from __future__ import annotations

import hashlib
import os
import urllib.request
from pathlib import Path

import numpy as np

MODEL = "bge-small-en-v1.5"
REPO = "https://huggingface.co/Xenova/bge-small-en-v1.5/resolve/main/"
MODEL_FILES = {
    "model_quantized.onnx": ("onnx/model_quantized.onnx",
                             "6c9c6101a956d62dfb5e7190c538226c0c5bb9cb27b651234b6df063ee7dbfe4"),
    "tokenizer.json": ("tokenizer.json", "d241a60d5e8f04cc1b2b3e9ef7a4921b27bf526d9f6050ab90f9267a1f9e5c66"),
}
DIM = 384
MAX_TOKENS = 64


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


class Embedder:
    def __init__(self) -> None:
        import onnxruntime as ort
        from tokenizers import Tokenizer
        d = fetch()
        self.tok = Tokenizer.from_file(str(d / "tokenizer.json"))
        self.tok.enable_truncation(MAX_TOKENS)
        self.tok.enable_padding()
        so = ort.SessionOptions()
        so.intra_op_num_threads = int(os.environ.get("SEARCH_THREADS", "2"))
        so.inter_op_num_threads = 1
        self.sess = ort.InferenceSession(str(d / "model_quantized.onnx"), so, providers=["CPUExecutionProvider"])
        self.inputs = {i.name for i in self.sess.get_inputs()}

    def __call__(self, texts: list[str], batch: int = 64) -> np.ndarray:
        out = np.zeros((len(texts), DIM), np.float32)
        for s in range(0, len(texts), batch):
            enc = self.tok.encode_batch(texts[s:s + batch])
            feed = {"input_ids": np.array([e.ids for e in enc], np.int64),
                    "attention_mask": np.array([e.attention_mask for e in enc], np.int64)}
            if "token_type_ids" in self.inputs:
                feed["token_type_ids"] = np.zeros_like(feed["input_ids"])
            cls = self.sess.run(None, feed)[0][:, 0, :]
            out[s:s + len(enc)] = cls / np.linalg.norm(cls, axis=1, keepdims=True)
        return out
