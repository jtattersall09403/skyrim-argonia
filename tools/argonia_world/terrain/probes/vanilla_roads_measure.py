"""Measure a road from vanilla_roads.py's dump (0034, 1.15-r4 roads): the cross profile of the ground (crown and
ditch), the grade along, the land-texture weights across (the paint and its blend width), and the road-edge statics
(lateral offset, spacing along). The centreline is the road-surface meshes (Road* statics but signs and chunks), their
heading from the line through their neighbours. Prints numbers; reads only.
Usage: python3 -m tools.argonia_world.terrain.probes.vanilla_roads_measure DUMP.npz [MESH_PREFIX]"""
import sys

import numpy as np

from tools.argonia_world import skyrim_units as su

U = su.UNITS_PER_METRE
OFFS = np.arange(-16, 16.5, 1.0)  # metres across


def main():
    d = np.load(sys.argv[1])
    cells, H, W = d["cells"], d["H"], d["W"]
    names = d["texname"].astype(str)
    cx0, cy0 = cells[:, 0].min(), cells[:, 1].min()
    nx, ny = cells[:, 0].max() - cx0 + 1, cells[:, 1].max() - cy0 + 1
    G = np.full((ny * 32 + 1, nx * 32 + 1), np.nan)
    T = np.zeros((len(names), ny * 32 + 1, nx * 32 + 1), np.float32)
    for i, (x, y) in enumerate(cells):
        r, c = (y - cy0) * 32, (x - cx0) * 32
        G[r:r + 33, c:c + 33] = H[i]
        T[:, r:r + 33, c:c + 33] = np.maximum(T[:, r:r + 33, c:c + 33], W[i])

    def sample(A, xu, yu):
        c = (xu - cx0 * su.CELL_UNITS) / su.VERTEX_SPACING_UNITS
        r = (yu - cy0 * su.CELL_UNITS) / su.VERTEX_SPACING_UNITS
        c0, r0 = np.floor(c).astype(int), np.floor(r).astype(int)
        ok = (c0 >= 0) & (r0 >= 0) & (c0 < A.shape[-1] - 1) & (r0 < A.shape[-2] - 1)
        c0, r0 = np.clip(c0, 0, A.shape[-1] - 2), np.clip(r0, 0, A.shape[-2] - 2)
        fc, fr = c - c0, r - r0
        v = (A[..., r0, c0] * (1 - fc) * (1 - fr) + A[..., r0, c0 + 1] * fc * (1 - fr)
             + A[..., r0 + 1, c0] * (1 - fc) * fr + A[..., r0 + 1, c0 + 1] * fc * fr)
        return np.where(ok, v, np.nan)

    rn = d["refname"].astype(str)
    R = d["refs"]
    pre = sys.argv[2] if len(sys.argv) > 2 else "Road"
    surf = np.array([n.startswith(pre) and "Sign" not in n and "Chunk" not in n and "Marker" not in n for n in rn])
    P = R[surf][:, :2]
    print(f"road-surface meshes: {surf.sum()}")
    prof, tex, grade, heads = [], [], [], []
    for p in P:
        nb = P[np.hypot(*(P - p).T) < 40 * U]
        if len(nb) < 3:
            continue
        v = np.linalg.svd(nb - nb.mean(0))[2][0]
        n = np.array([-v[1], v[0]])
        heads.append(v)
        xs, ys = p[0] + n[0] * OFFS * U, p[1] + n[1] * OFFS * U
        h = sample(G, xs, ys) / U
        prof.append(h - h[len(OFFS) // 2])
        tex.append(sample(T, xs, ys))
        a = sample(G, p[0] + v[0] * 4 * U * np.array([-1, 1]), p[1] + v[1] * 4 * U * np.array([-1, 1])) / U
        grade.append(abs(a[1] - a[0]) / 8.0)
    prof, tex, grade = np.array(prof), np.array(tex), np.array(grade)
    # fold the two sides: the profile is symmetric by construction of a road; report the mean of |left|,|right|
    med = np.nanmedian(prof, 0)
    sym = np.nanmedian((prof + prof[:, ::-1]) / 2, 0)
    print("offset_m  " + " ".join(f"{o:5.0f}" for o in OFFS))
    print("dh_med_m  " + " ".join(f"{x:5.2f}" for x in med))
    print("dh_sym_m  " + " ".join(f"{x:5.2f}" for x in sym))
    print("dh_p25_m  " + " ".join(f"{x:5.2f}" for x in np.nanpercentile((prof + prof[:, ::-1]) / 2, 25, 0)))
    print("dh_p75_m  " + " ".join(f"{x:5.2f}" for x in np.nanpercentile((prof + prof[:, ::-1]) / 2, 75, 0)))
    mt = np.nanmean(tex, 0)  # (ntex, noffs)
    for k in np.argsort(-mt.max(1))[:6]:
        print(f"{names[k]:24s}" + " ".join(f"{x:5.2f}" for x in mt[k]))
    print("grade_along: p50 %.3f p90 %.3f p95 %.3f p99 %.3f max %.3f (n=%d)" % (
        *np.nanpercentile(grade, [50, 90, 95, 99, 100]), np.isfinite(grade).sum()))
    # edge statics: offset across and spacing along, by name group
    for grp in ("RoadChunk", "Rock", "Fence", "RoadSign", "Bridge", "Post", "Lantern", "Lamp"):
        m = np.array([grp in n for n in rn]) & ~surf
        if not m.any():
            continue
        Q = R[m][:, :2]
        lat, near = [], []
        for q in Q:
            dd = np.hypot(*(P - q).T)
            j = dd.argmin()
            if dd[j] > 30 * U:
                continue
            nb = P[np.hypot(*(P - P[j]).T) < 40 * U]
            if len(nb) < 3:
                continue
            v = np.linalg.svd(nb - nb.mean(0))[2][0]
            w_ = q - P[j]
            lat.append(abs(v[0] * w_[1] - v[1] * w_[0]) / U)
        Qn = Q[[np.hypot(*(P - q).T).min() < 30 * U for q in Q]]
        for q in Qn:
            dd = np.hypot(*(Qn - q).T)
            dd = dd[dd > 0]
            if len(dd):
                near.append(dd.min() / U)
        if lat:
            print(f"{grp:10s} n_within30m={len(lat):4d} lateral_m p25/p50/p75 "
                  f"{np.percentile(lat, 25):.1f}/{np.percentile(lat, 50):.1f}/{np.percentile(lat, 75):.1f}"
                  f"  nearest_same_m p50 {np.median(near) if near else float('nan'):.1f}")
    # mesh spacing along the road
    nn = [np.sort(np.hypot(*(P - p).T))[1] / U for p in P]
    print("surface mesh nearest spacing m p50 %.1f" % np.median(nn))


if __name__ == "__main__":
    main()
