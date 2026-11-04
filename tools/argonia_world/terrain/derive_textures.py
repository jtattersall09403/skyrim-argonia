"""`terrain derive-textures` (1.15 r6, owner play test 3 findings 16-17): the ground's derived texture files, made at
install on the build VM from what the player's mods ship (decision 0014: a derived file is never shipped).

BM&V's 19 landscape diffuses are 512^2 DXT3 with no mipmaps (they shimmer and tile at distance) and come with no
normal map. For each texture the material paints (`material.TEXTURES`) this writes, under `<out>/textures/`:
- `Tex.diffuse` (`argonia\\landscape\\<name>.dds`): BM&V's diffuse, its full mip chain (box filter), 32-bit BGRA;
- `Tex.normal` (`argonia\\landscape\\<name>_n.dds`): a tangent normal from the diffuse's own luminance relief
  (tileable gradient), its strength set so the mean texel tilt equals Skyrim.esm's own normal of that name, and its
  alpha (the landscape shader's specular) the diffuse's luminance scaled to that vanilla normal's mean alpha (bar:
  Skyrim.esm's 50 landscape normals, mean ~22/255, lane 1.15-r4-materials); mips likewise.
No new art: every texel is a function of BM&V's diffuse; the targets are Skyrim.esm's measured numbers (0034).
`--dry-run` lists every file it would write with its source and targets and writes nothing. The deploy's
"ground textures" step runs it and lays the folder on the machine (C:\\argonia\\ours\\derived\\argonia-ground).
"""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

import numpy as np

from tools.argonia_world.terrain import dds
from tools.argonia_world.terrain import material as M

OUT = Path(__file__).resolve().parents[3] / "out" / "derived" / "argonia-ground"
VERSION = 1  # bump when the derivation changes: the stamp re-makes every file


def write_dds(levels: list[np.ndarray]) -> bytes:
    """(h, w, 4) uint8 RGBA levels (mip 0 first) -> an uncompressed 32-bit BGRA DDS with that mip chain."""
    h, w = levels[0].shape[:2]
    flags = 0x1 | 0x2 | 0x4 | 0x8 | 0x1000 | 0x20000
    hd = struct.pack("<4sIIIIIII", b"DDS ", 124, flags, h, w, w * 4, 0, len(levels)) + b"\0" * 44
    hd += struct.pack("<IIIIIIII", 32, 0x41, 0, 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
    hd += struct.pack("<IIIII", 0x1000 | 0x8 | 0x400000, 0, 0, 0, 0)
    return hd + b"".join(lv[..., [2, 1, 0, 3]].astype(np.uint8).tobytes() for lv in levels)


def mips(px: np.ndarray, normal: bool = False) -> list[np.ndarray]:
    """Mip chain by 2x2 box down to 1x1 (float RGBA 0..255); a normal's xyz renormalised at each level."""
    out, a = [], px.astype(np.float32)
    while True:
        lv = a
        if normal:
            n = lv[..., :3] / 127.5 - 1
            n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-6)
            lv = np.concatenate([(n + 1) * 127.5, lv[..., 3:]], -1)
        out.append(np.clip(np.rint(lv), 0, 255).astype(np.uint8))
        if a.shape[0] == 1 and a.shape[1] == 1:
            return out
        h, w = max(1, a.shape[0] // 2), max(1, a.shape[1] // 2)
        a = a[:h * 2, :w * 2].reshape(h, a.shape[0] // h, w, a.shape[1] // w, 4).mean((1, 3))


def _blur(x: np.ndarray) -> np.ndarray:
    for ax in (0, 1):  # tileable 1-2-1
        x = (np.roll(x, 1, ax) + 2 * x + np.roll(x, -1, ax)) / 4
    return x


def tilt_of(gx, gy, k: float) -> float:
    return float(np.degrees(np.arctan(k * np.hypot(gx, gy))).mean())


def normal_from(diffuse: np.ndarray, tilt_deg: float, alpha_mean: float) -> tuple[np.ndarray, float]:
    """(h, w, 4) float RGBA diffuse -> (RGBA normal 0..255, strength): relief from luminance, mean tilt and mean alpha
    set to the targets."""
    lum = (0.299 * diffuse[..., 0] + 0.587 * diffuse[..., 1] + 0.114 * diffuse[..., 2]) / 255.0
    ht = _blur(lum)
    gx = (np.roll(ht, -1, 1) - np.roll(ht, 1, 1)) / 2
    gy = (np.roll(ht, -1, 0) - np.roll(ht, 1, 0)) / 2
    lo, hi = 0.0, 1.0
    while tilt_of(gx, gy, hi) < tilt_deg and hi < 1e6:
        hi *= 2
    for _ in range(40):  # bisection on the strength: tilt rises monotonically with k
        k = (lo + hi) / 2
        lo, hi = (k, hi) if tilt_of(gx, gy, k) < tilt_deg else (lo, k)
    k = (lo + hi) / 2
    n = np.stack([-k * gx, k * gy, np.ones_like(gx)], -1)  # DirectX tangent space: green up, rows run down
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    a = lum / max(float(lum.mean()), 1e-6) * alpha_mean
    for _ in range(4):  # the clip at 255 lowers the mean: rescale to the target
        a = np.clip(a * alpha_mean / max(float(np.clip(a, 0, 255).mean()), 1e-6), 0, 255)
    return np.concatenate([(n + 1) * 127.5, a[..., None]], -1), k


def plan(stack=None) -> list[dict]:
    """One row per output file: path, source, targets (no pixels read but the sources' and vanilla's)."""
    from tools.argonia_world.terrain import texcheck
    stack = stack or texcheck.Stack(derived=None)
    bar = texcheck.vanilla_bar(stack)
    rows = []
    for t in M.TEXTURES:
        src = stack.get(t.bmv)
        van = stack.get(t.vanilla_normal, stack.vanilla)
        vs = texcheck.normal_stats(van[1]) if van else None
        rows.append({"ltex": t.edid, "source": t.bmv, "source_row": src[0] if src else None,
                     "source_sha": hashlib.sha256(src[1]).hexdigest()[:16] if src else None,
                     "diffuse": t.diffuse, "normal": t.normal, "vanilla_normal": t.vanilla_normal,
                     "tilt_target": vs["tilt_deg"] if vs else bar.get("tilt_p50"),
                     "alpha_target": vs["alpha_mean"] if vs else bar.get("alpha_mean"), "_src": src})
    return rows


def derive(out: Path = OUT, dry_run: bool = False, stack=None) -> dict:
    rows, made, fails = plan(stack), [], []
    stamp_p = out / "derive-stamp.json"
    try:
        old = json.loads(stamp_p.read_text())
    except (OSError, ValueError):
        old = {}
    stamp = {"version": VERSION}
    for r in rows:
        src = r.pop("_src")
        if src is None:
            fails.append(f"{r['ltex']}: source {r['source']} is laid by no row")
            continue
        stamp[r["ltex"]] = [r["source_sha"], r["tilt_target"], r["alpha_target"]]
        fd = out / "textures" / r["diffuse"].replace("\\", "/")
        fn = out / "textures" / r["normal"].replace("\\", "/")
        same = old.get("version") == VERSION and old.get(r["ltex"]) == stamp[r["ltex"]] and fd.exists() and fn.exists()
        r["action"] = "keep" if same else "make"
        if dry_run or same:
            made.append(r)
            continue
        px = dds.mip0(src[1])
        fd.parent.mkdir(parents=True, exist_ok=True)
        fd.write_bytes(write_dds(mips(px)))
        nrm, k = normal_from(px, r["tilt_target"], r["alpha_target"])
        fn.write_bytes(write_dds(mips(nrm, normal=True)))
        r["strength"] = round(k, 2)
        made.append(r)
    if not dry_run and not fails:
        stamp_p.write_text(json.dumps(stamp, indent=1) + "\n")
    return {"out": str(out), "rows": made, "fails": fails, "dry_run": dry_run}


def main(out: Path | None = None, dry_run: bool = False) -> int:
    res = derive(out or OUT, dry_run)
    for r in res["rows"]:
        print(f"{r.get('action', 'make'):4s} textures\\{r['diffuse']} (mips) and textures\\{r['normal']} "
              f"(tilt {r['tilt_target']} deg, alpha {r['alpha_target']}) from {r['source']} [{r['source_row']}]")
    for f in res["fails"]:
        print("FAIL", f)
    print(f"derive-textures: {2 * len(res['rows'])} files {'listed (dry run)' if dry_run else 'in ' + res['out']}, "
          f"{len(res['fails'])} fails")
    return 1 if res["fails"] else 0
