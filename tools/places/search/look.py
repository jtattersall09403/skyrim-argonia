"""The looked-at index: a thumbnail of every distinct model in the catalogue and a CLIP vector of each, so a query
finds a model by what it looks like, not only by its names. Derived, under out/places/search/look/, never committed.

  thumbs/<k[:2]>/<k>.webp      256-pixel three-quarter view (south-west, 25 degrees up), k = model_key(model)
  thumbs/<k[:2]>/<k>.f.webp    256-pixel front view (south, 8 degrees up)
  status.jsonl                 one line per model looked at: {k, model, ok, why, ms}; `ok` false says why we could
                               not look (not found, stand-in box, conversion failed, empty, black, unresolved
                               texture, error), which is never the same as "not held"
  vectors.npy, keys.jsonl      float16 [M, 512] unit CLIP image vectors (mean of the two views), keys in row order

`thumbs` draws every model not yet in status.jsonl (mods first, then vanilla) on N processes, appending as it
goes, so an interrupted run resumes where it stopped. `embed` adds a vector for every looked model not yet
embedded. Both are run by `python -m tools.places search look` under tooling/job_guard.sh."""
from __future__ import annotations

import hashlib
import io
import json
import os
import time
from pathlib import Path

import numpy as np

from tools.places.search.index import catalogue_path, out_dir, read_jsonl

SIZE = 256
VIEWS = {"": (225.0, 25.0), ".f": (180.0, 8.0)}
BG = np.array([0.82, 0.86, 0.9]) * 255
# A thumbnail drawn but not looked at by the image model (nothing of the thing is in it).
NO_LOOK = ("not found", "stand-in box", "conversion failed", "empty", "black", "error")


def look_dir() -> Path:
    return out_dir() / "search" / "look"


def model_key(model: str) -> str:
    return hashlib.sha1(model.lower().replace("\\", "/").encode()).hexdigest()[:16]


def thumb_path(k: str, view: str = "") -> Path:
    return look_dir() / "thumbs" / k[:2] / f"{k}{view}.webp"


def models(catalogue: Path | None = None) -> list[tuple[str, bool]]:
    """Every distinct model path (lower case) with whether a mod uses it, mods first, each group sorted."""
    seen: dict[str, bool] = {}
    for b in read_jsonl(catalogue_path(str(catalogue) if catalogue else None)):
        m = (b.get("model") or "").lower().replace("\\", "/")
        if m:
            seen[m] = seen.get(m, False) or b.get("source") != "skyrim"
    return sorted(seen.items(), key=lambda kv: (not kv[1], kv[0]))


def judge(img) -> str | None:
    """Why a drawn picture shows nothing to look at, or None."""
    a = np.asarray(img, np.float32)
    fg = np.abs(a - BG).sum(2) > 12
    if fg.mean() < 0.004:
        return "empty: nothing drawn in the frame"
    if a[fg].mean() < 14:
        return "black: the model draws black"
    return None


def look_one(model: str) -> dict:
    """Draw one model's views; never raises."""
    import tools.places.assets as A
    from tools.places.assets import render
    k, t0 = model_key(model), time.time()
    rec = {"k": k, "model": model, "ok": True, "why": None}
    try:
        info = A.mesh_info(model, 1)
        why = None
        if info.get("placeholder"):
            w = info.get("why") or ""
            why = ("not found: " if "not found" in w else "stand-in box: ") + w
        elif info.get("retry"):
            why = "conversion failed: " + (info.get("why") or "")
        elif not info.get("tris"):
            why = "empty: no triangles"
        data = Path(info["glb"]).read_bytes()
        for view, (az, el) in VIEWS.items():
            img = render.render(data, SIZE, az, el)
            if why is None and view == "":
                why = judge(img)
            p = thumb_path(k, view)
            p.parent.mkdir(parents=True, exist_ok=True)
            buf = io.BytesIO()
            img.save(buf, "WEBP", quality=72)
            tmp = p.with_suffix(".tmp")
            tmp.write_bytes(buf.getvalue())
            tmp.replace(p)
        tex = info.get("textures") or []
        if why is None and tex and all(A.tex_info(t, 512) is None for t in tex):
            why = "unresolved texture: " + ", ".join(tex[:3])
        rec["ok"], rec["why"] = why is None, why
    except Exception as e:   # noqa: BLE001 - one model's failure is a status row, not a stopped run
        rec["ok"], rec["why"] = False, f"error: {type(e).__name__}: {str(e)[:200]}"
    rec["ms"] = int((time.time() - t0) * 1000)
    return rec


def status() -> dict[str, dict]:
    p = look_dir() / "status.jsonl"
    out: dict[str, dict] = {}
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue   # a line cut by an interruption: that model is drawn again
            out[r["k"]] = r
    return out


def thumbs(jobs: int = 4, limit: int | None = None, only_mods: bool = False, retry_errors: bool = False) -> dict:
    from multiprocessing import get_context
    done = status()
    if retry_errors:
        done = {k: r for k, r in done.items() if not (r.get("why") or "").startswith("error")}
    todo = [m for m, mod in models() if model_key(m) not in done and (mod or not only_mods)]
    if limit:
        todo = todo[:limit]
    look_dir().mkdir(parents=True, exist_ok=True)
    n, t0 = 0, time.time()
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    with open(look_dir() / "status.jsonl", "a", encoding="utf-8") as f, get_context("fork").Pool(jobs) as pool:
        for rec in pool.imap_unordered(look_one, todo, chunksize=2):
            f.write(json.dumps(rec) + "\n")
            f.flush()
            n += 1
            if n % 200 == 0:
                print(f"{n}/{len(todo)} {(time.time() - t0) / n:.2f} s/model wall", flush=True)
    return {"looked": n, "left": len(todo) - n, "s_per_model_wall": round((time.time() - t0) / max(n, 1), 3)}


def lookable(r: dict) -> bool:
    return r.get("ok") or not (r.get("why") or "").startswith(NO_LOOK)


def embed(batch: int = 64, save_every: int = 2048) -> dict:
    """A CLIP vector for every looked model with something to look at; only new keys are embedded, and what is done
    is saved every `save_every` pictures, so an interrupted run keeps its work."""
    from PIL import Image

    from tools.places.search.clip import DIM, Clip
    keys, vec = load_vectors()
    have = set(keys)
    todo = [r["k"] for r in status().values() if lookable(r) and r["k"] not in have and thumb_path(r["k"]).exists()]
    clip = Clip(threads=int(os.environ.get("SEARCH_THREADS", "4")))
    new_k, new_v = [], []

    def pic(k: str, view: str):
        p = thumb_path(k, view)
        return Image.open(p if p.exists() else thumb_path(k))
    for s in range(0, len(todo), batch):
        ks = todo[s:s + batch]
        a, b = clip.images([pic(k, "") for k in ks]), clip.images([pic(k, ".f") for k in ks])
        new_k += ks
        new_v.append(a + b)
        if len(new_k) >= save_every or s + batch >= len(todo):
            keys, vec = save_vectors(keys + new_k, np.concatenate([vec.astype(np.float32)] + new_v))
            print(f"embedded {s + len(ks)}/{len(todo)}", flush=True)
            new_k, new_v = [], []
    return {"embedded": len(todo), "total": len(keys), "dim": DIM}


def save_vectors(keys: list[str], v: np.ndarray) -> tuple[list[str], np.ndarray]:
    d = look_dir()
    v = (v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)).astype(np.float16)
    tmp_k, tmp_v = d / "keys.jsonl.tmp", d / "vectors.tmp.npy"
    np.save(tmp_v, v)
    tmp_k.write_text("".join(json.dumps(k) + "\n" for k in keys))
    tmp_v.replace(d / "vectors.npy")   # keys follow; load_vectors refuses a pair whose lengths differ
    tmp_k.replace(d / "keys.jsonl")
    return keys, v


def load_vectors() -> tuple[list[str], np.ndarray]:
    from tools.places.search.clip import DIM
    d = look_dir()
    kp, vp = d / "keys.jsonl", d / "vectors.npy"
    if kp.exists() and vp.exists():
        keys = [json.loads(x) for x in kp.read_text().splitlines() if x.strip()]
        v = np.load(vp)
        if len(keys) == len(v):
            return keys, v
    return [], np.zeros((0, DIM), np.float16)


def report() -> dict:
    st = status()
    allm = models()
    from collections import Counter
    why = Counter((r.get("why") or "").split(":")[0] for r in st.values() if not r.get("ok"))
    return {"models": len(allm), "looked": sum(model_key(m) in st for m, _ in allm),
            "mods_left": sum(mod and model_key(m) not in st for m, mod in allm),
            "ok": sum(1 for r in st.values() if r.get("ok")), "failed": dict(why.most_common()),
            "embedded": len(load_vectors()[0])}
