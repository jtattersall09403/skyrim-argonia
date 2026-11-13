"""Seating of every placed kind, read from each base's own mesh against the ground under it: the audit (fault classes
by kind, from written shards) and the rule that seats a thing so it shows none of them.

A base's mesh (as the game finds it on the New World card) gives its profile (`profile`):
    trunk  the trunk's foot ring: the solid column round the mesh's axis at TRUNK_BAND_M, followed down while its
           cylinder stays closed; None for a mesh that stands on no trunk.
    bulk   the underside as columns of COL_M (each column's lowest surface point), and which columns are bulk (at
           least BULK_SHARE of the thick columns' thickness: a log's body, not a root tip, a branch or a twig).
    rim    points along the open rim (edges of one face only, coincident vertices welded): where the rim stands above
           the ground one sees into the mesh (an open underside, a shell's hollow back).
    open   the openness: |sum of the faces' area vectors| / area (0 for a closed mesh), sideways and downwards.
A placed thing is judged by its kind's measure (`judge`), a height in metres of the posed mesh over the lower of the
quad's two triangulations:
    trunk  canopy_tree, palm, understorey, mushroom, and an upright log (a stump): the foot ring's highest point;
    bulk   a lying log: the median underside height of its bulk columns;
    rim    boulder, cliff, seabed_rock and road dressing rocks open by OPEN_MIN or more: the RIM_Q quantile of the
           rim's height;
    low    every thing: its lowest point (above FLOAT_M it floats).
Fault classes (`faults`): trunk_hovers, bulk_hovers, hollow_shows, floats; the rule (`seat`) sets z so the measure is
RULE[m]["target"]; for a rim, the shell is turned (its own tilt, or laid on the ground's plane, at each of YAWS
yaws) to the pose that needs the least burial. The spot is refused
(the kind is not placed on that ground) when a rim's burial passes EXTRA_SINK_MAX of the mesh's height, when the
ground under a trunk's foot ring spreads more than the tree slope window (35 deg) allows across it plus
SPREAD_SLACK_M (a trunk half over a bank), or when a log's bulk still spans a hollow (p90 over BULK_SPAN_M) in every
pose of its own tilt or the ground's plane at each of YAWS yaws. RULE comes from Skyrim.esm (`vanilla`, Tamriel's
natural refs of the same kinds of mesh standing on the land alone): research in docs/phases/new-worldspace-plan/walk2/seat.md.

    python -m tools.newworld.place.audit refs [DIR ...] [--json OUT]   every fault class by kind, from written shards
    python -m tools.newworld.place.audit vanilla PICKLE [--json OUT]   Skyrim.esm's measures (PICKLE: bases, refs, land)
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from tools.navmesh.placed import rotation
from tools.newworld.place import place as P

UPM = P.UPM
COL_M = 0.5
BULK_SHARE = 0.4
FLOAT_M = 0.5
OPEN_MIN = 0.2
TRUNK_BAND_M = (0.3, 1.2)
TRUNK_REACH_M = 4.0
RIM_STEP_M = 0.25
RIM_Q = 95
SAMPLE_MAX = 1500
ISOLATED_M = 6.0
YAWS = 16
TILT_MAX_DEG = 45  # a shell laid on the ground's plane: tipped at most this far
SPREAD_SLACK_M = 0.3   # the foot ring's height spread allowed past the tree slope window across its width
BULK_SPAN_M = 0.5      # a seated log's bulk p90 above the ground past this spans a hollow: not placed there
TRUNK_KINDS = ("canopy_tree", "palm", "understorey", "mushroom")
BULK_KINDS = ("log",)
RIM_KINDS = ("boulder", "cliff", "seabed_rock", "road_rock_pile", "road_boulder", "road_cairn")
# metres: `target` the height the rule seats the measure to; `fault` the height above which the thing is out of rule
RULE = {"trunk": {"target": -0.10, "fault": 0.10},
        "stump": {"target": -0.25, "fault": 0.10},
        "bulk": {"target": 0.0, "fault": 0.25},
        "rim": {"target": -0.05, "fault": 0.10}}
FAULTS = ("trunk_hovers", "bulk_hovers", "hollow_shows", "floats")


def surface(model: str, resolver=None):
    """(V, F) of a model's drawable shapes in its own frame, or None when the game would find no mesh."""
    from tools.places.assets import nifglb
    from tools.places.assets.resolve import default, norm
    data = (resolver or default()).read(norm(model, "meshes"))
    if data is None:
        return None
    try:
        shapes = nifglb.drawable(nifglb.dump(data))
    except Exception:  # a mesh nifdump cannot read: judged as missing
        return None
    if not shapes:
        return None
    vs, fs, off = [], [], 0
    for s in shapes:
        m = np.array(s["m"], float).reshape(3, 4)
        vs.append(s["P"] @ m[:, :3].T + m[:, 3])
        fs.append(s["I"].astype(np.int64) + off)
        off += len(s["P"])
    return np.concatenate(vs), np.concatenate(fs)


def _samples(V, F, step):
    """Points over every triangle at most `step` apart (vertices, edges and faces)."""
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    L = np.maximum.reduce([np.linalg.norm(b - a, axis=1), np.linalg.norm(c - b, axis=1), np.linalg.norm(a - c, axis=1)])
    n = np.clip(np.ceil(L / step).astype(int), 1, 60)
    out = [V]
    for k in np.unique(n):
        if k == 1:
            continue
        sel = n == k
        i, j = np.meshgrid(np.arange(k + 1), np.arange(k + 1))
        m = (i + j) <= k
        u, v = i[m] / k, j[m] / k
        A, B, C = a[sel], b[sel], c[sel]
        out.append((A[:, None] + (B - A)[:, None] * u[None, :, None] + (C - A)[:, None] * v[None, :, None]).reshape(-1, 3))
    return np.concatenate(out)


def _cap(pts, low=200):
    if len(pts) <= SAMPLE_MAX:
        return pts
    keep = np.r_[np.argsort(pts[:, 2])[:low], np.random.default_rng(0).choice(len(pts), SAMPLE_MAX, replace=False)]
    return pts[np.unique(keep)]


def _trunk(V, F) -> np.ndarray | None:
    reach = TRUNK_REACH_M * UPM
    lo_b, hi_b = TRUNK_BAND_M[0] * UPM, TRUNK_BAND_M[1] * UPM
    near = (np.linalg.norm(V[:, :2], axis=1) <= reach * 1.5) & (V[:, 2] <= hi_b)
    Fn = F[near[F].any(1)]
    if not len(Fn):
        return None
    S = _samples(V, Fn, 0.05 * UPM)
    band = S[(S[:, 2] >= lo_b) & (S[:, 2] <= hi_b) & (np.linalg.norm(S[:, :2], axis=1) <= reach)]
    if len(band) < 8:
        return None
    rb = np.linalg.norm(band[:, :2], axis=1)
    c = np.median(band[rb <= np.percentile(rb, 30)][:, :2], axis=0)
    rc = np.linalg.norm(band[:, :2] - c, axis=1)
    R = float(np.percentile(rc[rc <= 2 * np.percentile(rc, 30) + 0.3 * UPM], 70))
    if R <= 0:
        return None
    d = S[:, :2] - c
    rr = np.linalg.norm(d, axis=1)
    sec = np.floor((np.arctan2(d[:, 1], d[:, 0]) + np.pi) / (np.pi / 4)).astype(int) % 8
    shell = (rr >= 0.5 * R) & (rr <= 1.5 * R)
    step, z, zt = 0.1 * UPM, lo_b, lo_b
    while z > S[:, 2].min():
        m = shell & (S[:, 2] >= z - step) & (S[:, 2] < z)
        if len(np.unique(sec[m])) < 5:
            break
        z -= step
        zt = z
    ang = np.linspace(0, 2 * np.pi, 8, endpoint=False)
    return np.vstack([np.column_stack([c[0] + R * np.cos(ang), c[1] + R * np.sin(ang), np.full(8, zt)]), [c[0], c[1], zt]])


def _rim(V, F) -> np.ndarray:
    q = np.round(V / 0.5).astype(np.int64)
    _, inv = np.unique(q, axis=0, return_inverse=True)
    inv = inv.ravel()
    Fw = inv[F]
    Fw = Fw[(Fw[:, 0] != Fw[:, 1]) & (Fw[:, 1] != Fw[:, 2]) & (Fw[:, 0] != Fw[:, 2])]
    e = np.sort(np.concatenate([Fw[:, [0, 1]], Fw[:, [1, 2]], Fw[:, [2, 0]]]), axis=1)
    u, cnt = np.unique(e, axis=0, return_counts=True)
    b = u[cnt == 1]
    if not len(b):
        return np.zeros((0, 3))
    rep = np.zeros(inv.max() + 1, np.int64)
    rep[inv] = np.arange(len(inv))
    a, c = V[rep[b[:, 0]]], V[rep[b[:, 1]]]
    n = np.clip(np.ceil(np.linalg.norm(c - a, axis=1) / (RIM_STEP_M * UPM)).astype(int), 1, 200)
    t = np.concatenate([np.arange(k) / k for k in n])
    i = np.repeat(np.arange(len(b)), n)
    return _cap(a[i] + (c[i] - a[i]) * t[:, None], low=0)


def profile(model: str, resolver=None) -> dict | None:
    sf = surface(model, resolver)
    if sf is None:
        return None
    V, F = sf
    av = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]) / 2
    o = -av.sum(0) / max(float(np.linalg.norm(av, axis=1).sum()), 1e-9)
    col = COL_M * UPM
    S = _samples(V, F, col / 2)
    ij = np.floor(S[:, :2] / col).astype(np.int64)
    key = ij[:, 0] * 1_000_003 + ij[:, 1]
    order = np.lexsort((S[:, 2], key))
    ks = key[order]
    first, last = np.r_[True, ks[1:] != ks[:-1]], np.r_[ks[1:] != ks[:-1], True]
    under = S[order[first]]
    thick = S[order[last]][:, 2] - under[:, 2]
    zmin = float(V[:, 2].min())
    height = float(V[:, 2].max()) - zmin
    trunk = _trunk(V, F)
    return {"model": model, "pts": _cap(V), "under": under,
            "bulk": thick >= BULK_SHARE * float(np.percentile(thick, 90)), "trunk": trunk, "rim": _rim(V, F),
            "open_side": float(math.hypot(o[0], o[1])), "open_down": float(-o[2]), "height": height,
            "upright": bool(height >= 0.5 * float(np.ptp(V[:, :2], axis=0).max()))}


def measure_of(kind: str, prof: dict) -> str:
    if kind in TRUNK_KINDS and prof["trunk"] is not None:
        return "trunk"
    if kind in BULK_KINDS:
        return "stump" if prof["trunk"] is not None and prof["upright"] else "bulk"
    if kind in RIM_KINDS and len(prof["rim"]) and max(prof["open_side"], prof["open_down"]) >= OPEN_MIN:
        return "rim"
    return "low"


def _h(pts, M, pos, ground):
    q = pts @ M.T + pos
    return (q[:, 2] - ground(q[:, 0], q[:, 1])) / UPM


def judge(prof: dict, kind: str, pos, rot, scale: float, ground) -> dict:
    """{"measure": its name, <measure>: metres, "low": metres}; `ground(xs, ys)` -> heights (units)."""
    M = rotation(*rot) * float(scale)
    pos = np.asarray(pos, float)
    m = measure_of(kind, prof)
    out = {"measure": m, "low": float(_h(prof["pts"], M, pos, ground).min())}
    if m in ("trunk", "stump"):
        out[m] = float(_h(prof["trunk"], M, pos, ground).max())
    elif m == "bulk":
        g = _h(prof["under"], M, pos, ground)
        out[m] = float(np.median(g[prof["bulk"]] if prof["bulk"].any() else g))
    elif m == "rim":
        out[m] = float(np.percentile(_h(prof["rim"], M, pos, ground), RIM_Q))
    return out


def faults(j: dict) -> list[str]:
    m = j["measure"]
    f = []
    if m in ("trunk", "stump") and j[m] > RULE[m]["fault"]:
        f.append("trunk_hovers")
    if m == "bulk" and j[m] > RULE[m]["fault"]:
        f.append("bulk_hovers")
    if m == "rim" and j[m] > RULE[m]["fault"]:
        f.append("hollow_shows")
    if j["low"] > FLOAT_M:
        f.append("floats")
    return f


def _plane_tilt(pos, ground, d=2.0 * UPM):
    """rx, ry that lay a mesh on the ground's plane round pos (tipped at most TILT_MAX_DEG)."""
    gx = float(ground(np.array([pos[0] + d]), np.array([pos[1]]))[0] - ground(np.array([pos[0] - d]), np.array([pos[1]]))[0]) / (2 * d)
    gy = float(ground(np.array([pos[0]]), np.array([pos[1] + d]))[0] - ground(np.array([pos[0]]), np.array([pos[1] - d]))[0]) / (2 * d)
    return P.tilt_rot(min(math.degrees(math.atan(math.hypot(gx, gy))), TILT_MAX_DEG), gx, gy)


def seat(prof: dict, kind: str, pos, rot, scale: float, ground) -> tuple[float, tuple] | None:
    """(z, (rx, ry, rz)) that seat the thing by its kind's rule, or None when no pose seats it on this ground (the
    module's head: the kind is not placed there). A rock's z is never raised above where its own sink set it."""
    pos = [float(v) for v in pos]
    m = measure_of(kind, prof)
    cap = P.EXTRA_SINK_MAX * prof["height"] * float(scale) / UPM
    if m == "low":
        lo = judge(prof, kind, pos, rot, scale, ground)["low"]
        return pos[2] - (max(lo - 0.1, 0.0) if lo > FLOAT_M else 0.0) * UPM, tuple(rot)
    M = rotation(*rot) * float(scale)
    if m in ("trunk", "stump"):  # the foot ring's highest point to its target; refused on ground rougher under the
        h = _h(prof["trunk"], M, np.asarray(pos), ground)  # trunk than the tree slope window allows across it
        r = float(np.linalg.norm(prof["trunk"][0, :2] - prof["trunk"][8, :2])) * float(scale) / UPM
        if h.max() - h.min() > 2 * r * math.tan(math.radians(P.SLOPE_MAX["canopy_tree"])) + SPREAD_SLACK_M:
            return None
        return pos[2] - (float(h.max()) - RULE[m]["target"]) * UPM, tuple(rot)
    tilts = [tuple(rot[:2]), _plane_tilt(pos, ground)]
    if m == "bulk":  # the bulk's median to its target, in the first pose (its own tilt, or laid on the ground's plane,
        for rx, ry in tilts:  # at each of YAWS yaws) where no part of the bulk still spans a hollow; else refused
            for k in range(YAWS):
                r3 = (rx, ry, (rot[2] + 2 * math.pi * k / YAWS) % (2 * math.pi))
                h = _h(prof["under"], rotation(*r3) * float(scale), np.asarray(pos), ground)
                h = h[prof["bulk"]] if prof["bulk"].any() else h
                dz = float(np.median(h)) - RULE[m]["target"]
                if float(np.percentile(h, 90)) - dz <= BULK_SPAN_M:
                    return pos[2] - dz * UPM, r3
        return None
    best = None
    for rx, ry in tilts:
        for k in range(YAWS):
            r3 = (rx, ry, (rot[2] + 2 * math.pi * k / YAWS) % (2 * math.pi))
            dz = max(judge(prof, kind, pos, r3, scale, ground)["rim"] - RULE["rim"]["target"], 0.0)
            if best is None or dz < best[0] - 1e-6:
                best = (dz, r3)
            if dz == 0.0:
                break
        if best[0] == 0.0:
            break
    if best[0] > cap:
        return None
    return pos[2] - best[0] * UPM, best[1]


class Profiles:
    """model -> profile, read once."""

    def __init__(self, resolver=None):
        self.R, self.c = resolver, {}

    def __call__(self, model):
        if model not in self.c:
            self.c[model] = profile(model, self.R)
        return self.c[model]


def world_ground(W):
    def ground(xs, ys):
        t1, t2 = W.tri_grounds(np.asarray(xs, float), np.asarray(ys, float))
        return np.minimum(t1, t2)
    return ground


def audit(refs, ground, prof=None) -> dict:
    """refs: shard rows (model, cls, pos, rot, scale, base). Per fault class: total, by kind, the worst five."""
    prof = prof or Profiles()
    by, n, nomesh, worst = defaultdict(Counter), Counter(), Counter(), defaultdict(list)
    name = {"trunk_hovers": ("trunk", "stump"), "bulk_hovers": ("bulk",), "hollow_shows": ("rim",), "floats": ("low",)}
    for o in refs:
        kind = o.get("cls") or "?"
        n[kind] += 1
        p = prof(o["model"]) if o.get("model") else None
        if p is None:
            nomesh[kind] += 1
            continue
        j = judge(p, kind, o["pos"], o["rot"], o["scale"], ground)
        for fl in faults(j):
            by[fl][kind] += 1
            v = next(j[k] for k in name[fl] if k in j)
            worst[fl].append((round(v, 2), o.get("base"), o["pos"]))
    out = {"refs": sum(n.values()), "by_kind": dict(n.most_common()), "no_mesh": dict(nomesh), "faults": {}}
    for fl in FAULTS:
        out["faults"][fl] = {"total": sum(by[fl].values()), "by_kind": dict(by[fl].most_common()),
                             "worst": sorted(worst[fl], key=lambda t: -t[0])[:5]}
    return out


def shard_refs(dirs):
    for d in dirs:
        for f in sorted(Path(d).glob("cy*.jsonl")):
            for ln in f.read_text(encoding="utf-8").splitlines():
                if ln.strip():
                    yield json.loads(ln)


def vanilla(pickle_path: str, per_model: int = 30) -> dict:
    """Skyrim.esm's measures over Tamriel's natural refs standing on the land alone (no rock or cliff within
    ISOLATED_M: a vanilla thing set on a rock is not seated on the land). PICKLE: {bases, refs: (base, (x, y, z, rx,
    ry, rz), scale), land: (cx, cy) -> 33 x 33 heights}."""
    import pickle
    from scipy.spatial import cKDTree
    v = pickle.load(open(pickle_path, "rb"))
    land = v["land"]

    def ground(xs, ys):
        xs, ys = np.atleast_1d(np.asarray(xs, float)), np.atleast_1d(np.asarray(ys, float))
        cx, cy = np.floor(xs / 4096).astype(int), np.floor(ys / 4096).astype(int)
        out = np.full(len(xs), np.nan)
        for key in set(zip(cx.tolist(), cy.tolist())):
            h = land.get(key)
            if h is None:
                continue
            s = (cx == key[0]) & (cy == key[1])
            c, r = (xs[s] - key[0] * 4096) / 128, (ys[s] - key[1] * 4096) / 128
            c0, r0 = np.minimum(c.astype(int), 31), np.minimum(r.astype(int), 31)
            u, w = c - c0, r - r0
            a, b, d, e = h[r0, c0], h[r0, c0 + 1], h[r0 + 1, c0], h[r0 + 1, c0 + 1]
            t1 = np.where(u >= w, a + (b - a) * u + (e - b) * w, a + (d - a) * w + (e - d) * u)
            t2 = np.where(u + w <= 1, a + (b - a) * u + (d - a) * w, e + (d - e) * (1 - u) + (b - e) * (1 - w))
            out[s] = np.minimum(t1, t2)
        return out

    def kind(b):
        m = b["modl"].lower()
        if not m.startswith("landscape"):
            return None
        if "log" in m or "stump" in m or "fallen" in m:
            return "log"
        if b["sig"] == "TREE" or "\\trees\\" in m:
            return "canopy_tree"
        if "cliff" in m or "rock" in m or "boulder" in m:
            return "boulder"
        return None
    stone = cKDTree(np.array([r[1][:2] for r in v["refs"] if kind(v["bases"][r[0]]) == "boulder"]))
    refs = [r for r in v["refs"] if kind(v["bases"][r[0]]) and len(stone.query_ball_point(r[1][:2], ISOLATED_M * UPM))
            <= (1 if kind(v["bases"][r[0]]) == "boulder" else 0)]
    np.random.default_rng(0).shuffle(refs)
    prof, per, seen = Profiles(), defaultdict(list), Counter()
    for base, dat, sc in refs:
        b = v["bases"][base]
        k = kind(b)
        if seen[b["modl"]] >= per_model:
            continue
        p = prof(b["modl"])
        if p is None:
            continue
        j = judge(p, k, dat[:3], dat[3:], sc, ground)
        m = j["measure"]
        if m != "low" and np.isfinite(j[m]):
            per[m].append(j[m])
            per[f"low_{m}"].append(j["low"])
            seen[b["modl"]] += 1
    return {m: {"n": len(a), **{f"p{q}": round(float(np.percentile(a, q)), 3) for q in (5, 25, 50, 75, 95)}}
            for m, a in per.items() if a}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["refs", "vanilla"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    if a.cmd == "vanilla":
        rep = vanilla(a.args[0])
        for k, v in rep.items():
            print(f"  {k}: {v}")
    else:
        rep = audit(shard_refs([Path(x) for x in a.args] or [P.REFS]), world_ground(P.World()))
        print(f"seat audit: {rep['refs']} refs; no mesh {rep['no_mesh']}")
        for fl, r in rep["faults"].items():
            print(f"  {fl}: {r['total']}  {r['by_kind']}")
    if a.json:
        Path(a.json).write_text(json.dumps(rep, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
