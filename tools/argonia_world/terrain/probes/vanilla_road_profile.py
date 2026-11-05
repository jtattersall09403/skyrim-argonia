"""Probe (0034, lane 1.15-r6-road-profile): Skyrim.esm's road across, from vanilla_roads.py's dump. At each Road*
surface mesh (its axis from the meshes within 40 m), the LAND every 0.5 m to 12 m each side of the centre: the
flat width (|dz| < 0.1 m, contiguous), the fold at 2..8 m, the steepest second difference across, and the mean land
texture weights across; with --marsh only the meshes with marsh paint (FrozenMarsh*, RiverMud*) beyond 8 m: the
road through wet ground. Prints percentiles; reads only (the dump stays under a scratch dir, never the repo).
Usage: python3 -m tools.argonia_world.terrain.probes.vanilla_road_profile DUMP.npz [--marsh]"""
import sys

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.routes.census import flat_width

U = su.UNITS_PER_METRE
OFFS = np.arange(-12.0, 12.01, 0.5)


def main():
    d = np.load(sys.argv[1])
    marsh_only = "--marsh" in sys.argv
    cells, H, W = d["cells"], d["H"], d["W"]
    names = list(d["texname"].astype(str))
    cx0, cy0 = cells[:, 0].min(), cells[:, 1].min()
    nx, ny = cells[:, 0].max() - cx0 + 1, cells[:, 1].max() - cy0 + 1
    G = np.full((ny * 32 + 1, nx * 32 + 1), np.nan)
    T = np.zeros((W.shape[1],) + G.shape)
    for i, (x, y) in enumerate(cells):
        r, c = (y - cy0) * 32, (x - cx0) * 32
        G[r:r + 33, c:c + 33] = H[i]
        T[:, r:r + 33, c:c + 33] = np.maximum(T[:, r:r + 33, c:c + 33], W[i])

    def samp(A, xu, yu):
        c = (xu - cx0 * su.CELL_UNITS) / su.VERTEX_SPACING_UNITS
        r = (yu - cy0 * su.CELL_UNITS) / su.VERTEX_SPACING_UNITS
        c0 = np.clip(np.floor(c).astype(int), 0, G.shape[1] - 2)
        r0 = np.clip(np.floor(r).astype(int), 0, G.shape[0] - 2)
        fc, fr = c - c0, r - r0
        return (A[..., r0, c0] * (1 - fc) * (1 - fr) + A[..., r0, c0 + 1] * fc * (1 - fr)
                + A[..., r0 + 1, c0] * (1 - fc) * fr + A[..., r0 + 1, c0 + 1] * fc * fr)

    rn = d["refname"].astype(str)
    surf = np.array([n.startswith("Road") and not any(k in n for k in ("Sign", "Chunk", "Marker")) for n in rn])
    P = d["refs"][surf][:, :2]
    marsh = [i for i, nm in enumerate(names) if "FrozenMarsh" in nm or "RiverMud" in nm]
    far = np.abs(OFFS) >= 8
    pr, tx = [], []
    for p in P:
        nb = P[np.hypot(*(P - p).T) < 40 * U]
        if len(nb) < 3:
            continue
        v = np.linalg.svd(nb - nb.mean(0))[2][0]
        n = np.array([-v[1], v[0]])
        xs, ys = p[0] + n[0] * OFFS * U, p[1] + n[1] * OFFS * U
        z = samp(G, xs, ys) / U
        if not np.isfinite(z).all():
            continue
        t = samp(T, xs, ys)
        if marsh_only and t[marsh][:, far].sum(0).mean() < 0.4:
            continue
        pr.append(z - z[len(OFFS) // 2])
        tx.append(t)
    pr, tx = np.array(pr), np.array(tx)
    c = len(OFFS) // 2
    fw = np.array([flat_width(z, c, 0.5) for z in pr])
    sd = np.abs(np.diff(pr, 2, axis=1)).max(1)
    print(f"road meshes {surf.sum()}, measured {len(pr)}{' (marsh)' if marsh_only else ''}")
    print("flat width p50 %.1f p75 %.1f p95 %.1f max %.1f m" % tuple(np.percentile(fw, [50, 75, 95, 100])))
    print("second difference across p50 %.3f p95 %.3f p99 %.3f max %.3f" % tuple(np.percentile(sd, [50, 95, 99, 100])))
    for o in (1, 2, 3, 4, 5, 6, 8, 10, 12):
        a = (pr[:, np.isclose(OFFS, o)] + pr[:, np.isclose(OFFS, -o)]).ravel() / 2
        print(f"fold {o:>2} m p25 %.2f p50 %.2f p75 %.2f" % tuple(np.percentile(a, [25, 50, 75])))
    print("raised (both sides under the centre at 12 m):", int((pr[:, [0, -1]].max(1) < -0.2).sum()))
    mt = tx.mean(0)
    for i in np.argsort(-mt[:, c])[:4]:
        print(f"{names[i]:<28}", " ".join(f"{a:.2f}" for a in mt[i, c::2]), "(0..12 m)")


if __name__ == "__main__":
    main()
