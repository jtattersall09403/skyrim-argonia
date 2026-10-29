"""The parchment chart's command line (2.W4 §c). Output under out/chart/ (gitignored); nothing here is committed.

    python -m tools.chart render [--size MASTER] [--out out/chart] the layers, copies, tiles, index, L1 checks
    python -m tools.chart twice [--size MASTER]                     two renders in two processes: the same hashes
    python -m tools.chart sample                                    the synthetic sample's hash (the gate's test)
    python -m tools.chart fetch-font                                Pelagiad (OFL) into $ARGONIA_PRIVATE/fonts
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

from tools.chart import checks, render

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "out" / "chart"
COPIES = (2048, 1024)


def flatten(base: np.ndarray, *rgba: np.ndarray, band: int = 512) -> np.ndarray:
    out = np.empty_like(base)
    for r0 in range(0, base.shape[0], band):
        c = base[r0:r0 + band].astype(np.float32)
        for L in rgba:
            a = L[r0:r0 + band, :, 3:4].astype(np.float32) / 255
            c = c * (1 - a) + L[r0:r0 + band, :, :3].astype(np.float32) * a
        out[r0:r0 + band] = np.clip(np.rint(c), 0, 255).astype(np.uint8)
    return out


def digest(*arrays: np.ndarray, extra: bytes = b"") -> str:
    h = hashlib.sha256()
    for a in arrays:
        h.update(str(a.shape).encode())
        h.update(np.ascontiguousarray(a).tobytes())
    h.update(extra)
    return h.hexdigest()


def save(arr: np.ndarray, path: Path) -> None:
    Image.fromarray(arr).save(path, optimize=False, compress_level=6)


def write(chart: render.Chart, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    s = chart.size
    idx = json.dumps(chart.index, sort_keys=True, separators=(",", ":")).encode()
    hashes = {"base": digest(chart.base), "ink": digest(chart.ink), "revealed": digest(chart.revealed),
              "index": hashlib.sha256(idx).hexdigest()}
    hashes["render"] = digest(chart.base, chart.ink, chart.revealed, extra=idx)
    (out / "index.json").write_bytes(idx)
    layers = {"base": chart.base, "ink": chart.ink, "revealed": chart.revealed}
    sketch = flatten(chart.base, chart.ink)
    full = flatten(chart.base, chart.revealed, chart.ink)
    layers |= {"sketch": sketch, "full": full}
    files = []
    for name, a in layers.items():
        im = Image.fromarray(a)
        im.save(out / f"{name}-{s}.png", compress_level=6)
        files.append(f"{name}-{s}.png")
        for c in COPIES + ((512,) if name == "sketch" else ()):
            if c < s:
                im.resize((c, c), Image.LANCZOS).save(out / f"{name}-{c}.png", compress_level=6)
                files.append(f"{name}-{c}.png")
        del im
    # the revealed layer as tiles: each cell lies in exactly one tile (tiles and cells both on the 32-px lattice)
    t = chart.index["tile"]
    tdir = out / "tiles" / "revealed"
    tdir.mkdir(parents=True, exist_ok=True)
    for old in tdir.glob("*.png"):  # a tile now empty must not survive from an earlier render
        old.unlink()
    n_tiles = 0
    for ty in range(0, s, t):
        for tx in range(0, s, t):
            tile = chart.revealed[ty:ty + t, tx:tx + t]
            if tile[..., 3].any():
                Image.fromarray(tile).save(tdir / f"{tx // t}-{ty // t}.png", compress_level=6)
                n_tiles += 1
    # a demonstration still: the sketch with the revealed layer only round Claywater (1.2 §e's acceptance walk)
    demo = demo_reveal(chart, "Claywater")
    if demo is not None:
        Image.fromarray(demo).resize((s // 2, s // 2), Image.LANCZOS).save(out / f"explored-demo-{s // 2}.png")
        files.append(f"explored-demo-{s // 2}.png")
    (out / "hashes.json").write_text(json.dumps(hashes, indent=1, sort_keys=True) + "\n")
    return {"hashes": hashes, "files": files, "tiles": n_tiles}


def demo_reveal(chart: render.Chart, name: str, radius_cells: int = 9) -> np.ndarray | None:
    pl = [p for p in chart.index["places"].values() if p["name"] == name]
    if not pl:
        return None
    cx, cy = pl[0]["cell"]
    mask = np.zeros(chart.revealed.shape[:2], np.float32)
    for key, (_tx, _ty, x, y, w, h) in chart.index["cells"].items():
        a, b = map(int, key.split(","))
        if (a - cx) ** 2 + (b - cy) ** 2 <= radius_cells ** 2:
            mask[int(y):int(np.ceil(y + h)), int(x):int(np.ceil(x + w))] = 1
    mask = render.blur(mask, max(1, int(8 * chart.size / render.MASTER)), 2)
    rev = chart.revealed.copy()
    rev[..., 3] = np.rint(rev[..., 3] * mask).astype(np.uint8)
    return flatten(chart.base, rev, chart.ink)


def cmd_render(a) -> int:
    from tools.chart.data import Features

    out = Path(a.out)
    f = Features.load()
    chart = render.Renderer(f, a.size).run()
    res = write(chart, out)
    rep = checks.run_all(chart, f)
    (out / "checks.json").write_text(json.dumps(rep, indent=1, sort_keys=True) + "\n")
    bad = [k for k, v in rep.items() if not v["ok"]]
    print(f"chart {a.size}: render {res['hashes']['render'][:16]}, {len(res['files'])} images, {res['tiles']} tiles; "
          f"L1 {'FAIL ' + ', '.join(bad) if bad else 'ok'} -> {out}")
    return 1 if bad else 0


def cmd_twice(a) -> int:
    hs = []
    with tempfile.TemporaryDirectory(dir=REPO / "out") as d:
        for k in range(2):
            o = Path(d) / str(k)
            subprocess.run([sys.executable, "-m", "tools.chart", "render", "--size", str(a.size), "--out", str(o)],
                           check=False, cwd=REPO)
            hs.append(json.loads((o / "hashes.json").read_text()))
    same = hs[0] == hs[1]
    print(f"two renders at {a.size}: {'identical' if same else 'DIFFER'} render {hs[0]['render'][:16]} "
          f"/ {hs[1]['render'][:16]}")
    return 0 if same else 1


def cmd_sample(_a) -> int:
    from tools.chart import sample

    print(sample.sample_hash())
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tools.chart")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render")
    r.add_argument("--size", type=int, default=render.MASTER)
    r.add_argument("--out", default=str(OUT))
    t = sub.add_parser("twice")
    t.add_argument("--size", type=int, default=render.MASTER)
    sub.add_parser("sample")
    sub.add_parser("fetch-font")
    a = ap.parse_args(argv)
    if a.cmd == "fetch-font":
        print(render.fetch_font())
        return 0
    return {"render": cmd_render, "twice": cmd_twice, "sample": cmd_sample}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
