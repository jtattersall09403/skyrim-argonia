"""Probe: the generated ground about each world-panel vantage (tests/journeys/world-panel.yaml): height, local
relief, max slope, cliff share, roles, the nearest entrance sites and the N/NW border distance, to map a still's
finding to the generator rule that made it. python3 -m tools.argonia_world.terrain.probes.vantage_ground [OUTDIR]"""
import json
import math
import sys
from pathlib import Path

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.terrain.cellwater import C, CX0, CY0, N, Q

ROOT = Path(__file__).resolve().parents[4]


def rc(x, y):
    cx, cy = math.floor(x / 4096), math.floor(y / 4096)
    return ((C - 1 - (cy - CY0)) * Q + (Q - (y - cy * 4096) / 128), (cx - CX0) * Q + (x - cx * 4096) / 128)


def main(out=ROOT / "out" / "terrain"):
    g = np.load(out / "ground-f32.npy")
    cl = np.load(out / "cliff-u8.npy")
    ro = np.load(out / "role-u8.npy")
    sites = json.loads((out / "entrance-sites.json").read_text())
    t = (ROOT / "tests/journeys/world-panel.yaml").read_text()
    d = json.loads(t[t.index("{"):])
    seen = set()
    m = su.PROVINCE_SAMPLE_M
    for s in d["steps"]:
        v = {}
        for e in s.get("expect", []):
            if e.get("path") in ("pos.x", "pos.y"):
                v.setdefault(e["path"], []).append(e.get("gt", e.get("lt")))
        if not v or s["name"].rsplit("-", 1)[0] in seen:
            continue
        seen.add(s["name"].rsplit("-", 1)[0])
        x, y = sum(v["pos.x"]) / 2, sum(v["pos.y"]) / 2
        r, c = (int(round(a)) for a in rc(x, y))
        k = int(300 / m)
        w = g[max(r - k, 0):r + k + 1, max(c - k, 0):c + k + 1].astype(float)
        gy, gx = np.gradient(w, m)
        sl = np.degrees(np.arctan(np.hypot(gx, gy)))
        near = sorted(((math.hypot(si["x_m"] / m - c, si["y_m"] / m - r) * m, si) for si in sites))[:2]
        bd = min(r, c) * m
        roles = np.bincount(ro[max(r - k, 0):r + k + 1, max(c - k, 0):c + k + 1].ravel(), minlength=5)
        print(f"{s['name'].rsplit('-', 1)[0]:32s} rc {r},{c} z {g[r, c]:.1f} win {w.min():.0f}..{w.max():.0f} "
              f"slope p50/p99 {np.median(sl):.0f}/{np.percentile(sl, 99):.0f} cliff {cl[max(r-k,0):r+k+1, max(c-k,0):c+k+1].mean():.2f} "
              f"roles {roles.tolist()} border {bd:.0f} m sites " +
              "; ".join(f"{si['place_id'].split('.')[-1]}/{si['shape']} r{si['radius_m']:.0f} at {dd:.0f} m" for dd, si in near))


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "out" / "terrain")
