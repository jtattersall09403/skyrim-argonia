"""How Bethesda's hand-made navmesh treats placed natural objects (decision 0034): the measurements behind the
navmesh's rule for what is placed (docs/research/nw-02-walk5-navmesh.md).

    python -m tools.navmesh.vanilla [--world 0x3C] [--every N] [--out FILE.json]     objects against the navmesh
    python -m tools.navmesh.vanilla islands [--world 0x3C] [--out FILE.json]         the navmesh's own cut-off pieces

Reads Skyrim.esm's Tamriel in place: every exterior NAVM, and every reference whose base is a TREE, a FLOR or a STAT
with a mesh. For each reference with navmesh near it, the solid collision of its mesh (meshes.Resolver over the
game's own archives) is cut to the band an actor's body fills (placed.BAND above the ground, the ground taken as
the nearest navmesh vertex), and its plan footprint (placed.footprint) is measured. The reference is then one of:

    hole     a point of its collision in the band (Footprint.stand: the nearest the footprint's centre) lies on no
             navmesh triangle: the navmesh is cut round it
    through  the point lies on a triangle at ground level: the navmesh runs through it (actors' avoidance copes)
    over     the point lies on a triangle more than OVER above the ground: the navmesh walks over its top
    none     its mesh has no solid collision in the band (a plant, a low stone): nothing to cut

Printed and written: per kind (tree, rock, cliff, log, plant, other) and footprint radius bin, the counts and the
share cut; for the holes, the gap from that point to the nearest navmesh edge; and per kind how many references
stand on navmeshed ground with a mesh that has no solid collision at all (`no_collision`).

`islands` joins every exterior NAVM of the world by its triangles' neighbours and edge links and measures the pieces
apart from the largest: how many, their area, and the share of the navmesh they hold, over the whole world and over
its forest and rock cells (FOREST_REFS trees or rocks in the cell), by size (ISLAND_BINS, m2).
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from tools.navmesh import esm, meshes, nvnm, placed

CELL = 4096.0
NEAR = 384.0  # a reference counts when navmesh lies within this of its footprint: it stands on navmeshed ground
OVER = 48.0  # a triangle this far above the ground at the centre is the object's top, not the ground
BINS = [0, 8, 12, 16, 20, 24, 28, 32, 40, 48, 64, 96, 128, 192, 256, 512, 1e9]
TOPS = [-1e9, 0, 16, 32, 48, 64, 96, 128, 1e9]  # the collision's highest point above the ground
BASES = {b"TREE", b"FLOR", b"STAT"}


def kind(sig: bytes, modl: str) -> str:
    m = modl.lower().replace("/", "\\")
    if "cliff" in m or "mountain" in m:
        return "cliff"
    if "rock" in m or "boulder" in m or "stone" in m:
        return "rock"
    if "log" in m or "stump" in m or "driftwood" in m or "deadwood" in m:
        return "log"
    if sig == b"TREE" and "\\trees\\" in m and "shrub" not in m and "bush" not in m:
        return "tree"
    if sig in (b"TREE", b"FLOR") or "plants" in m or "shrub" in m:
        return "plant"
    return "other"


def read(path: Path, world: int):
    bases, navm, refs = {}, {}, []
    for r in esm.records(path, BASES, groups=BASES):
        modl = next((p.rstrip(b"\0").decode("cp1252") for s, p in esm.subrecords(r.data) if s == b"MODL"), "")
        if modl:
            bases[r.fid] = (r.sig, modl)
    label = struct.pack("<I", world)
    for r in esm.records(path, {b"NAVM", b"REFR"}, groups={b"WRLD"}):
        if (esm.GROUP_WORLD_CHILDREN, label) not in r.parents:
            continue
        sub = dict(esm.subrecords(r.data))
        if r.sig == b"NAVM":
            n = nvnm.decode(sub[b"NVNM"])
            if n.grid_xy is not None and len(n.tris):
                navm.setdefault(n.grid_xy, []).append(n.verts.astype(np.float64)[n.tris["v"].astype(int)])
        elif r.flags & 0x820 == 0 and sub.get(b"NAME") and len(sub.get(b"DATA", b"")) == 24:  # not deleted or disabled
            base = struct.unpack("<I", sub[b"NAME"])[0]
            if base in bases:
                d = struct.unpack("<6f", sub[b"DATA"])
                s = struct.unpack("<f", sub[b"XSCL"])[0] if b"XSCL" in sub else 1.0
                refs.append((base, d[:3], d[3:], s))
    return bases, {k: np.concatenate(v) for k, v in navm.items()}, refs


def point_tris(p, t):
    """(covering triangle's height at p or None, plan distance from p to the nearest triangle edge)."""
    a, b, c = t[:, 0], t[:, 1], t[:, 2]
    den = (b[:, 1] - c[:, 1]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 1] - c[:, 1])
    with np.errstate(divide="ignore", invalid="ignore"):
        l1 = ((b[:, 1] - c[:, 1]) * (p[0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (p[1] - c[:, 1])) / den
        l2 = ((c[:, 1] - a[:, 1]) * (p[0] - c[:, 0]) + (a[:, 0] - c[:, 0]) * (p[1] - c[:, 1])) / den
    l3 = 1 - l1 - l2
    inside = (l1 >= 0) & (l2 >= 0) & (l3 >= 0) & (den != 0)
    z = None
    if inside.any():
        i = np.nonzero(inside)[0]
        zs = l1[i] * a[i, 2] + l2[i] * b[i, 2] + l3[i] * c[i, 2]
        z = float(zs.min())
    best = np.inf
    for u, w in ((a, b), (b, c), (c, a)):
        e = w[:, :2] - u[:, :2]
        ll = (e * e).sum(axis=1)
        s = np.clip(((p[0] - u[:, 0]) * e[:, 0] + (p[1] - u[:, 1]) * e[:, 1]) / np.where(ll > 0, ll, 1), 0, 1)
        best = min(best, float(np.hypot(p[0] - u[:, 0] - s * e[:, 0], p[1] - u[:, 1] - s * e[:, 1]).min()))
    return z, best


def measure(path: Path, world: int = 0x3C, every: int = 1) -> dict:
    bases, navm, refs = read(path, world)
    res = meshes.Resolver(path.parent, stack=Path("/nonexistent"))
    by_cell = defaultdict(list)
    for x in refs:
        by_cell[(int(x[1][0] // CELL), int(x[1][1] // CELL))].append(x)
    rows = []
    bare: dict = defaultdict(int)  # kind -> references on navmeshed ground whose mesh has no solid collision
    for n_cell, ((cx, cy), xs) in enumerate(sorted(by_cell.items())):
        if n_cell % every:
            continue
        t = [navm[(cx + i, cy + j)] for i in (-1, 0, 1) for j in (-1, 0, 1) if (cx + i, cy + j) in navm]
        if not t:
            continue
        t = np.concatenate(t)
        tv = t.reshape(-1, 3)
        for base, pos, rot, s in xs:
            sig, modl = bases[base]
            c = res.collision(modl)
            if c is None or c.tris is None:
                continue
            pos = np.array(pos)
            near = np.hypot(tv[:, 0] - pos[0], tv[:, 1] - pos[1])
            k = int(near.argmin())
            if not len(c.tris):
                if near[k] <= NEAR:
                    bare[kind(sig, modl)] += 1
                continue
            w = c.tris.reshape(-1, 3) @ (placed.rotation(*rot) * s).T + pos if len(c.tris) else np.zeros((0, 3))
            zg = float(tv[k, 2])
            f = placed.footprint(w.reshape(-1, 3, 3), zg)
            if f is None:
                if near[k] <= NEAR and len(w):
                    z, _ = point_tris(pos, t)
                    rows.append((kind(sig, modl), modl, 0.0, 0.0, float(w[:, 2].max() - zg), "none", 0.0 if z is None else 1.0))
                continue
            z, d = point_tris(f.stand, t)
            if z is None and d > f.radius + NEAR:
                continue  # no navmesh round it: off the walkable world
            state = "hole" if z is None else ("over" if z > zg + OVER else "through")
            rows.append((kind(sig, modl), modl, f.radius, f.reach, f.top, state, d if z is None else 0.0))
    return summarise(rows, bare)


def summarise(rows, bare=None) -> dict:
    out = {"refs": len(rows), "kinds": {}, "models": {}}
    for kd in sorted({r[0] for r in rows} | set(bare or ())):
        sub = [r for r in rows if r[0] == kd]
        table = []
        for lo, hi in zip(BINS, BINS[1:]):
            b = [r for r in sub if r[5] != "none" and lo <= r[2] < hi]
            if not b:
                continue
            n = len(b)
            holes = [r for r in b if r[5] == "hole"]
            table.append({"radius": [lo, hi if hi < 1e8 else None], "n": n, "hole": round(len(holes) / n, 3),
                          "through": round(sum(r[5] == "through" for r in b) / n, 3),
                          "over": round(sum(r[5] == "over" for r in b) / n, 3),
                          "clearance_p50": round(float(np.median([r[6] for r in holes])), 1) if holes else None})
        tops = []
        for lo, hi in zip(TOPS, TOPS[1:]):
            b = [r for r in sub if lo <= r[4] < hi]
            if b:
                cut = sum(r[5] == "hole" or (r[5] == "none" and r[6] == 0.0) for r in b)
                tops.append({"top": [lo, hi if hi < 1e8 else None], "n": len(b), "hole": round(cut / len(b), 3)})
        out["kinds"][kd] = {"by_top": tops, "n": len(sub), "no_collision": int((bare or {}).get(kd, 0)), "no_collision_in_band": sum(r[5] == "none" for r in sub),
                            "low_on_navmesh": sum(r[5] == "none" and r[6] == 1.0 for r in sub), "by_radius": table}
    per = defaultdict(list)
    for r in rows:
        per[(r[0], r[1].lower())].append(r)
    for (kd, m), b in sorted(per.items(), key=lambda kv: -len(kv[1]))[:120]:
        live = [r for r in b if r[5] != "none"]
        out["models"][m] = {"kind": kd, "n": len(b), "none": len(b) - len(live),
                            "radius_p50": round(float(np.median([r[2] for r in live])), 1) if live else None,
                            "top_p50": round(float(np.median([r[4] for r in live])), 1) if live else None,
                            "hole": round(sum(r[5] == "hole" for r in live) / len(live), 3) if live else None}
    return out


FOREST_REFS = 20  # a cell with this many trees is forest, with this many rocks or cliff pieces rock
ISLAND_BINS = [0, 10, 25, 50, 100, 250, 1000, 1e12]  # m2
UNITS_PER_M2 = 70.0 ** 2


def islands(path: Path, world: int = 0x3C) -> dict:
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    bases, _, refs = read(path, world)
    per_cell: dict = defaultdict(lambda: defaultdict(int))
    for base, pos, _, _ in refs:
        per_cell[(int(pos[0] // CELL), int(pos[1] // CELL))][kind(*bases[base])] += 1
    label = struct.pack("<I", world)
    navm = []
    for r in esm.records(path, {b"NAVM"}, groups={b"WRLD"}):
        if (esm.GROUP_WORLD_CHILDREN, label) in r.parents:
            n = nvnm.decode(dict(esm.subrecords(r.data))[b"NVNM"])
            if n.grid_xy is not None and len(n.tris):
                navm.append((r.fid, n))
    off, at = {}, 0
    for fid, n in navm:
        off[fid] = at
        at += len(n.tris)
    area, cell_of, ed = np.zeros(at), [], []
    for fid, n in navm:
        o = off[fid]
        v = n.verts.astype(np.float64)
        tv = n.tris["v"].astype(int)
        a, b, c = v[tv[:, 0]], v[tv[:, 1]], v[tv[:, 2]]
        area[o:o + len(tv)] = np.abs((b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])) / 2 / UNITS_PER_M2
        cell_of += [n.grid_xy] * len(tv)
        e, fl = n.tris["e"].astype(int), n.tris["flags"].astype(int)
        for k in range(3):
            linked = (fl & nvnm.EDGE_LINK[k]) != 0
            ti = np.nonzero(~linked & (e[:, k] >= 0))[0]
            ed.append(np.stack([o + ti, o + e[ti, k]], 1))
            for t in np.nonzero(linked)[0]:
                lk = n.links[int(e[t, k])]
                if int(lk["navm"]) in off:
                    ed.append(np.array([[o + t, off[int(lk["navm"])] + int(lk["tri"])]]))
    ed = np.concatenate(ed)
    _, lab = connected_components(coo_matrix((np.ones(len(ed), np.int8), (ed[:, 0], ed[:, 1])), shape=(at, at)), directed=False)
    comp = np.bincount(lab, weights=area)
    main = int(comp.argmax())
    tri_comp = comp[lab]
    forest = np.array([per_cell[c]["tree"] >= FOREST_REFS for c in cell_of])
    rock = np.array([per_cell[c]["rock"] + per_cell[c]["cliff"] >= FOREST_REFS for c in cell_of])

    def part(sel):
        total = float(area[sel].sum())
        small = sel & (lab != main)
        bins = [{"m2": [lo, hi if hi < 1e11 else None], "pieces": int(len(set(lab[small & (tri_comp >= lo) & (tri_comp < hi)]))),
                 "area_m2": round(float(area[small & (tri_comp >= lo) & (tri_comp < hi)].sum())),
                 "share": round(float(area[small & (tri_comp >= lo) & (tri_comp < hi)].sum()) / total, 5) if total else None}
                for lo, hi in zip(ISLAND_BINS, ISLAND_BINS[1:])]
        return {"area_m2": round(total), "off_the_main_m2": round(float(area[small].sum())),
                "off_the_main_share": round(float(area[small].sum()) / total, 5) if total else None, "by_size": bins}
    return {"navm": len(navm), "triangles": at, "pieces": int(len(comp)), "main_share": round(float(comp[main] / comp.sum()), 4),
            "smallest_m2": round(float(comp.min()), 2), "all": part(np.ones(at, bool)), "forest": part(forest), "rock": part(rock)}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["islands"]:
        ap = argparse.ArgumentParser(prog="python -m tools.navmesh.vanilla islands")
        ap.add_argument("--world", default="0x3C")
        ap.add_argument("--out")
        a = ap.parse_args(argv[1:])
        from tools.navmesh.__main__ import game_data
        res = islands(game_data() / "Skyrim.esm", int(a.world, 16))
        if a.out:
            Path(a.out).write_text(json.dumps(res, indent=1) + "\n")
        print(json.dumps({k: v for k, v in res.items() if k not in ("all", "forest", "rock")}))
        for name in ("all", "forest", "rock"):
            p = res[name]
            print(f"{name}: {p['area_m2']} m2, off the main piece {p['off_the_main_m2']} m2 ({p['off_the_main_share']})")
            print("   " + "  ".join(f"{b['m2'][0]:g}-{b['m2'][1]}: {b['pieces']} pieces {b['area_m2']} m2 ({b['share']})" for b in p["by_size"]))
        return 0
    ap = argparse.ArgumentParser(prog="python -m tools.navmesh.vanilla")
    ap.add_argument("--world", default="0x3C")
    ap.add_argument("--every", type=int, default=1, help="measure every n-th cell that holds references")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    from tools.navmesh.__main__ import game_data
    res = measure(game_data() / "Skyrim.esm", int(a.world, 16), a.every)
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=1) + "\n")
    for kd, k in res["kinds"].items():
        print(f"{kd}: {k['n']} refs with collision, {k['no_collision']} with none; {k['no_collision_in_band']} with collision only below the band ({k['low_on_navmesh']} of them on the navmesh)")
        for r in k["by_radius"]:
            print(f"   r {r['radius'][0]:>4}-{str(r['radius'][1]):<5} n {r['n']:>6}  hole {r['hole']:.3f}  through {r['through']:.3f}"
                  f"  over {r['over']:.3f}  clearance p50 {r['clearance_p50']}")
        print("   by top above ground: " + "  ".join(f"{r['top'][0]:g}-{r['top'][1]}: {r['hole']:.2f} of {r['n']}" for r in k["by_top"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
