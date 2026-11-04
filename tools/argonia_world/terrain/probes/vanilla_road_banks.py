"""Probe (0034, lane 1.15-r6-roads-dry): Skyrim.esm's roadside embankments, from vanilla_roads.py's dump. At each
road-surface mesh, across the road: the lateral fall from the road edge (EDGE_M from the centre) over the BAND_M
beside it, on the sides where the road stands above the land there; and the steepest 1 m step in that band. Prints
percentiles; reads only.
Usage: python3 -m tools.argonia_world.terrain.probes.vanilla_road_banks DUMP.npz"""
import sys

import numpy as np

from tools.argonia_world import skyrim_units as su

U = su.UNITS_PER_METRE
EDGE_M, BAND_M = 3.0, 8.0


def main():
    d = np.load(sys.argv[1])
    cells, H = d["cells"], d["H"]
    cx0, cy0 = cells[:, 0].min(), cells[:, 1].min()
    nx, ny = cells[:, 0].max() - cx0 + 1, cells[:, 1].max() - cy0 + 1
    G = np.full((ny * 32 + 1, nx * 32 + 1), np.nan)
    for i, (x, y) in enumerate(cells):
        r, c = (y - cy0) * 32, (x - cx0) * 32
        G[r:r + 33, c:c + 33] = H[i]

    def sample(xu, yu):
        c = (xu - cx0 * su.CELL_UNITS) / su.VERTEX_SPACING_UNITS
        r = (yu - cy0 * su.CELL_UNITS) / su.VERTEX_SPACING_UNITS
        c0, r0 = np.floor(c).astype(int), np.floor(r).astype(int)
        ok = (c0 >= 0) & (r0 >= 0) & (c0 < G.shape[1] - 1) & (r0 < G.shape[0] - 1)
        c0, r0 = np.clip(c0, 0, G.shape[1] - 2), np.clip(r0, 0, G.shape[0] - 2)
        fc, fr = c - c0, r - r0
        v = (G[r0, c0] * (1 - fc) * (1 - fr) + G[r0, c0 + 1] * fc * (1 - fr)
             + G[r0 + 1, c0] * (1 - fc) * fr + G[r0 + 1, c0 + 1] * fc * fr)
        return np.where(ok, v, np.nan)

    rn = d["refname"].astype(str)
    surf = np.array([n.startswith("Road") and "Sign" not in n and "Chunk" not in n and "Marker" not in n for n in rn])
    P = d["refs"][surf][:, :2]
    offs = np.arange(EDGE_M, EDGE_M + BAND_M + 0.5, 1.0)
    fall, step = [], []
    for p in P:
        nb = P[np.hypot(*(P - p).T) < 40 * U]
        if len(nb) < 3:
            continue
        v = np.linalg.svd(nb - nb.mean(0))[2][0]
        n = np.array([-v[1], v[0]])
        for sg in (-1, 1):
            z = sample(p[0] + sg * n[0] * offs * U, p[1] + sg * n[1] * offs * U) / U
            if not np.isfinite(z).all() or z[-1] >= z[0]:
                continue  # the road not above the land on this side
            fall.append((z[0] - z[-1]) / BAND_M)
            step.append(float(np.max(z[:-1] - z[1:])))
    fall, step = np.array(fall), np.array(step)
    print(f"road meshes {surf.sum()}, sides with the road above the land {len(fall)}")
    print("fall over %g m beside the edge: p50 %.3f p90 %.3f p95 %.3f p99 %.3f max %.3f" % (
        BAND_M, *np.percentile(fall, [50, 90, 95, 99, 100])))
    print("steepest 1 m step in the band: p50 %.3f p90 %.3f p95 %.3f p99 %.3f max %.3f" % (
        *np.percentile(step, [50, 90, 95, 99, 100]),))


if __name__ == "__main__":
    main()
