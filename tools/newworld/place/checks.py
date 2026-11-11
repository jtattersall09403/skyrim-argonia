"""Off-game checks of the placement (nw-02 step 8), read back from its shards as the ESM writer reads them: the
things the rules placed (place.PLACED). The edits of single things are judged by the same rules in edits.py.

Writes check.json beside the shards and prints one line per check; exit 1 when a hard check fails.
Hard (must be 0 / true): refs on a road surface; trees in flowing water; trees in standing water against the rule
(habitat or the family's standing_water_max_m); trunk seating outside the base's measured sink window by more than
the LAND quantisation (4 units) plus the two triangulations' difference; rocks and cliffs with the mesh bottom above
the lowest ground of their footprint; pairs closer than 1 m; a base from a plugin that is not a master; a model that
does not resolve in the NewWorld profile. Reported: trees in standing water by habitat, cliff open sides within 45 deg
of uphill, refs per cell against vanilla, distinct bases per region and the regions' Jaccard similarity.
"""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict

import numpy as np
from scipy.spatial import cKDTree

from tools.newworld.place import place as P

QUANT_M = 4 / P.UPM


def load(d=None):
    refs = []
    for f in sorted((d or P.PLACED).glob("cy*.jsonl")):
        refs += [json.loads(ln) for ln in f.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return refs


def run(folder=None, refs=None) -> int:
    """`folder`: the folder of shards judged, with its bases.json (default: the placement); `refs`: its references
    when the caller holds them already (the read-back's, from the world file)."""
    folder = folder or P.PLACED
    W = P.World(); Pa = P.Palette(W); R = P.Roads()
    bases = json.loads((folder / "bases.json").read_text())["bases"]
    rec = {b["key"]: b for b in bases}
    refs = load(folder) if refs is None else refs
    n = len(refs)
    xs = np.array([r["pos"][0] for r in refs]); ys = np.array([r["pos"][1] for r in refs])
    zs = np.array([r["pos"][2] for r in refs]); sc = np.array([r["scale"] for r in refs])
    cls = np.array([r["cls"] for r in refs])
    src = [r["key"] for r in refs]
    res, fails = {}, []

    def hard(name, val, ok):
        res[name] = val
        if not ok:
            fails.append(name)

    clear = R.clear(xs, ys)
    hard("refs_on_road_surface", int((clear < 0).sum()), (clear < 0).sum() == 0)
    trees = np.isin(cls, P.TREES)
    res["trees_within_2m_of_road_edge"] = int((trees & (clear < 2.0)).sum())
    g = W.ground(xs, ys); depth = -g / P.UPM
    kind = W.at("kind", xs, ys); hab = W.at("habitat", xs, ys)
    flows = Pa.kind_flows[kind]
    wet = trees & (depth > 0.05)
    hard("trees_in_flowing_water", int((wet & flows).sum()), (wet & flows).sum() == 0)
    habs = W.legend["habitats"]
    bad_still, by_hab = 0, Counter()
    for i in np.flatnonzero(wet & ~flows):
        fam = Pa.fam[Pa.base[refs[i]["db"]]["flora_family_id"]]
        by_hab[habs[hab[i]]] += 1
        if habs[hab[i]] not in P.TREE_IN_WATER or depth[i] > (fam.get("standing_water_max_m") or 0) + 0.05:
            bad_still += 1
    res["trees_in_standing_water"] = {"count": int(wet.sum() - (wet & flows).sum()), "by_habitat": dict(by_hab),
                                      "share_of_trees": round(float(wet.sum()) / max(1, trees.sum()), 4)}
    hard("trees_in_standing_water_against_rule", bad_still, bad_still == 0)
    # seating: the trunk's sink against the base's measured window, under either triangulation
    t1, t2 = W.tri_grounds(xs, ys)
    err_max, err_at, n_seat = 0.0, None, 0
    hover, rock_n = 0, 0
    for i, r in enumerate(refs):
        b = Pa.base.get(r["db"])
        if b is None:
            continue
        c = Pa.class_of[r["db"]]
        if c in P.ROCKS:
            rock_n += 1
            ob = rec[src[i]]["obnd"]
            if P.underside_gap(W, xs[i], ys[i], zs[i], ob, sc[i], r["rot"]) > 0.5:  # the shard's rounding (0.1 unit, 1e-5 rad)
                hover += 1
            continue
        lo, hi = b.get("sink_lo_m"), b.get("sink_hi_m")
        if lo is None or hi is None or hi <= lo:
            s0 = b.get("sink_m") if b.get("sink_m") is not None else Pa.cls[c].get("sink_m", 0.1)
            lo = hi = s0
        n_seat += 1
        for gg in (t1[i], t2[i]):
            s = (gg - zs[i]) / P.UPM / sc[i]
            e = max(0.0, lo - s, s - hi) * sc[i]  # metres in the world
            if e > err_max:
                err_max, err_at = e, f"{r['db']} at {r['pos']}"
    hard("seating_error_max_m", round(err_max, 3), err_max <= QUANT_M + P.TWIST_MAX_M + 0.01)
    res["seating_checked"] = n_seat
    res["seating_worst"] = err_at
    hard("rocks_with_open_underside_above_ground", hover, hover == 0)
    tall = sum(1 for i, r in enumerate(refs) if cls[i] == "cliff" and P.overtop(W, xs[i], ys[i], zs[i], rec[src[i]]["obnd"], sc[i])
               > max(P.OVERTOP_MIN_M * P.UPM, P.OVERTOP_SHARE * (rec[src[i]]["obnd"][5] - rec[src[i]]["obnd"][2]) * sc[i]) + 0.5)
    hard("cliffs_taller_than_their_hill", tall, tall == 0)
    res["rocks_checked"] = rock_n
    # cliff open sides
    within, total = 0, 0
    for i, r in enumerate(refs):
        b = Pa.base.get(r["db"])
        if not b or Pa.class_of[r["db"]] not in P.ROCKS or not isinstance(b.get("open_az"), (int, float)):
            continue
        gx, gy = W.gradient(xs[i], ys[i])
        if math.hypot(gx, gy) < 1e-6:
            continue
        up = math.degrees(math.atan2(gy, gx))
        world_open = b["open_az"] - math.degrees(r["rot"][2])
        d = abs((world_open - up + 180) % 360 - 180)
        total += 1; within += d <= 45
    res["open_sides_facing_uphill"] = {"within_45deg": within, "of": total, "share": round(within / max(1, total), 4)}
    hard("open_sides_uphill_share_ok", res["open_sides_facing_uphill"]["share"], total == 0 or within / total >= 0.95)
    # spacing
    tree = cKDTree(np.column_stack([xs, ys]))
    pairs = tree.query_pairs(P.MIN_SPACING_M * P.UPM - 1e-6, output_type="ndarray")
    hard("pairs_closer_than_1m", int(len(pairs)), len(pairs) == 0)
    # masters: a base outside them is copied by the writer (ForeignCopy); the ESM read-back (newworld check) counts
    # links into any other plugin. Here: every base names its record (plugin:editor id) and is a placeable type.
    copied = Counter(b["plugin"] for b in bases if b["copied"])
    res["bases_copied_by_plugin"] = dict(copied)
    badref = [b["key"] for b in bases if b["ref"] != f"{b['plugin']}:{b['edid']}" or b["sig"] not in ("STAT", "TREE", "FLOR", "MSTT")]
    hard("bases_not_named_or_not_placeable", len(badref), not badref)
    # models resolve in the NewWorld profile
    from tools.navmesh import meshes
    meshes.PROFILE = "NewWorld"
    rv = meshes.Resolver(P.DATA)
    missing = sorted({b["model"] for b in bases if rv.where(b["model"]) is None})
    hard("models_not_resolved", {"count": len(missing), "first": missing[:10]}, not missing)
    # budgets
    per = Counter(tuple(r["cell"]) for r in refs if not r["cls"].startswith("road_"))
    g_ = W.grid
    cells = [(cx, cy) for cy in range(g_["cy_bottom"], g_["cy_top"] + 1) for cx in range(g_["cx0"], g_["cx1"] + 1)]
    cnt = np.array([per.get(c, 0) for c in cells])
    nz = cnt[cnt > 0]
    res["refs_per_cell"] = {"p50": float(np.percentile(cnt, 50)), "p99": float(np.percentile(cnt, 99)), "max": int(cnt.max()),
                            "nonempty_p50": float(np.percentile(nz, 50)), "nonempty_p95": float(np.percentile(nz, 95)),
                            "vanilla_forested": {"p95": 83, "max": 162}}
    hard("cells_over_budget", int((cnt > P.CAP).sum()), (cnt > P.CAP).sum() == 0)
    # variety
    regs = W.legend["regions"]
    rg = W.at("region", xs, ys)
    sets = defaultdict(set)
    for i, r in enumerate(refs):
        if not r["cls"].startswith("road_"):
            sets[regs[rg[i]]].add(src[i])
    names = sorted(k for k, v in sets.items() if len(v) >= 10)
    jac = {}
    for a in range(len(names)):
        for b in range(a + 1, len(names)):
            A, B = sets[names[a]], sets[names[b]]
            jac[f"{names[a]}|{names[b]}"] = round(len(A & B) / len(A | B), 3)
    jv = np.array(list(jac.values())) if jac else np.zeros(1)
    res["variety"] = {"distinct_bases_per_region": {k: len(sets[k]) for k in sorted(sets)},
                      "jaccard_max": float(jv.max()), "jaccard_mean": round(float(jv.mean()), 3),
                      "jaccard_max_pair": max(jac, key=jac.get) if jac else None}
    res["total_refs"] = n
    res["by_class"] = dict(Counter(cls.tolist()))
    res["fails"] = fails
    (folder / "check.json").write_text(json.dumps(res, indent=1))
    for k, v in res.items():
        if k not in ("variety", "by_class"):
            print(f"  {k}: {v}")
    print(f"  variety: jaccard max {res['variety']['jaccard_max']} ({res['variety']['jaccard_max_pair']}), mean "
          f"{res['variety']['jaccard_mean']}; distinct bases/region min "
          f"{min(res['variety']['distinct_bases_per_region'].values())} max {max(res['variety']['distinct_bases_per_region'].values())}")
    print("PASS" if not fails else f"FAIL {fails}")
    return 0 if not fails else 1
