#!/usr/bin/env python3
"""Is a captured still usable?  (decision 0036: the driver agent's first look, before any image is judged)

    python3 tools/still_ok.py <still.png> [--prev <previous.png>] [--min-std N] [--json]

Exit 0 when usable; exit 1 with one reason line when blank / near-uniform, all black or all white, the same as --prev,
or truncated / unreadable.  --min-std is the smallest pixel standard deviation (0-255 luma) that counts as a picture.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from argonia_world.terrain import png  # noqa: E402
from bridge import frame_difference  # noqa: E402

# Default: half the flattest real still under out/batch/** (std 8.0, 01-lilmoth-dawn.png, 60 smallest of 1619 files, 2026-11-01).
DEFAULT_MIN_STD = 4.0
SAME_FRACTION = 0.001  # under 0.1 % of pixels differing by more than 8 levels is "the same still"


def luma(img: np.ndarray) -> np.ndarray:
    a = img.astype(np.float64)
    return a if a.ndim == 2 else a[..., :3].mean(axis=-1)


def pixel_difference(a: np.ndarray, b: np.ndarray) -> float:
    """The fraction of pixels differing by more than 8 levels (the same measure as bridge.frame_difference)."""
    if a.shape[:2] != b.shape[:2]:
        return 1.0
    return float((np.abs(luma(a) - luma(b)) > 8).mean())


def check(path: Path, prev: Path | None = None, min_std: float = DEFAULT_MIN_STD) -> tuple[bool, str, dict]:
    """(usable, reason, numbers)."""
    path = Path(path)
    try:
        img = png.read(path)
    except Exception as e:  # truncated zlib, bad signature, missing file ...
        return False, f"unreadable or truncated: {path} ({type(e).__name__}: {e})", {}
    if img.size == 0:
        return False, f"empty image: {path}", {}
    g = luma(img)
    nums = {"std": round(float(g.std()), 3), "mean": round(float(g.mean()), 2), "size": [int(img.shape[1]), int(img.shape[0])]}
    if g.max() <= 8:
        return False, f"all black (max luma {g.max():.0f})", nums
    if g.min() >= 247:
        return False, f"all white (min luma {g.min():.0f})", nums
    if nums["std"] < min_std:
        return False, f"blank or near-uniform (std {nums['std']} < {min_std})", nums
    if prev is not None:
        try:
            # bridge.frame_difference is exact on bytes without Pillow; the decoded compare catches near-duplicates
            diff = 0.0 if Path(prev).read_bytes() == path.read_bytes() else frame_difference(path, prev)
            if 0.0 < diff < 1.0 or diff == 1.0:
                diff = pixel_difference(img, png.read(Path(prev)))
        except Exception as e:
            return False, f"previous still unreadable: {prev} ({type(e).__name__}: {e})", nums
        nums["diff"] = round(diff, 5)
        if diff < SAME_FRACTION:
            return False, f"same as previous still ({diff:.4%} of pixels differ)", nums
    return True, "ok", nums


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("still")
    ap.add_argument("--prev")
    ap.add_argument("--min-std", type=float, default=DEFAULT_MIN_STD)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    ok, reason, nums = check(Path(a.still), Path(a.prev) if a.prev else None, a.min_std)
    if a.json:
        print(json.dumps({"ok": ok, "reason": reason, **nums}))
    elif not ok:
        print(reason)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
