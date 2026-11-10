"""The converted-asset cache: out/places/assets/{mesh,tex,thumb}/<2 hex>/<source sha256 + converter version>.<variant>.

A file is keyed by the hash of the bytes it was made from, so a changed source never serves a stale conversion and
two paths to the same bytes share one file. Writes go to a temporary file renamed into place, and one conversion
per key runs at a time (an flock on locks/<first two hex of the key>), so concurrent callers are safe and convert once. A hit touches the
file's mtime; when the cache is over its cap (ARGONIA_ASSET_CAP_MB, default 4096) the least recently used files are
deleted down to 90% of it."""
from __future__ import annotations

import fcntl
import os
import threading
import time
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CHECK_EVERY_S = 30


def root() -> Path:
    base = Path(os.environ.get("PLACES_OUT", ROOT / "out" / "places"))
    return base / "assets"


def cap_bytes() -> int:
    return int(float(os.environ.get("ARGONIA_ASSET_CAP_MB", "4096")) * 1024 * 1024)


def path(kind: str, key: str, variant: str) -> Path:
    return root() / kind / key[:2] / f"{key}.{variant}"


def touch(p: Path) -> None:
    try:
        os.utime(p)
    except OSError:
        pass


@contextmanager
def lock(key: str):
    d = root() / "locks"
    d.mkdir(parents=True, exist_ok=True)
    with open(d / key[:2], "a") as f:  # 256 stripes: few files, rare contention
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def write(p: Path, data: bytes) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(f".{p.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    tmp.write_bytes(data)
    os.replace(tmp, p)
    maybe_evict()


_last = 0.0
_elock = threading.Lock()


def maybe_evict() -> None:
    global _last
    with _elock:
        if time.time() - _last < CHECK_EVERY_S:
            return
        _last = time.time()
    evict()


def usage() -> tuple[int, list[tuple[float, int, Path]]]:
    files = []
    for kind in ("mesh", "tex", "thumb", "land"):
        d = root() / kind
        if not d.is_dir():
            continue
        for dp, _, names in os.walk(d):
            for n in names:
                p = Path(dp) / n
                try:
                    st = p.stat()
                except OSError:
                    continue
                files.append((st.st_mtime, st.st_size, p))
    return sum(f[1] for f in files), files


def evict(cap: int | None = None) -> dict:
    """Delete least recently used files until the cache is at 90% of the cap; returns what it did."""
    cap = cap_bytes() if cap is None else cap
    total, files = usage()
    removed = freed = 0
    if total > cap:
        files.sort()
        target = int(cap * 0.9)
        for _, size, p in files:
            if total - freed <= target:
                break
            if p.parent.name == "land":  # the land set (land/<file>) is small and always wanted
                continue
            try:
                p.unlink()
            except OSError:
                continue
            removed += 1
            freed += size
    return {"before": total, "after": total - freed, "removed": removed, "cap": cap}
