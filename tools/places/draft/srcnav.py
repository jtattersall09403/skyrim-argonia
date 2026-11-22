"""The source place's own exterior navmesh, carried to our place at the wholesale transform (place.json `fit` and
`wholesale.offset`): every triangle of the source cells' NAVMs inside the footprint, in our coordinates, assigned to
our cell by its middle, with four narrow rules where the town or ground was changed:

1. a vertex ON the source's ground (within ON_GROUND of the source terrain) follows our ground: it takes our ground's
   height there (our relief is the source's + offset, so it moves only where a mound, a bank or the edge band changed
   it); a vertex on a deck keeps its height (decks moved only with their pieces);
2. a triangle whose middle lies under a source piece we deleted or moved is dropped (its floor is gone or elsewhere);
   the build meshes again only those holes and what we added;
3. a triangle the source laid more than FLOAT_OVER over its own terrain with no source piece under it is dropped (the
   source's land there changed after its mesh was made: it floats over nothing); the build meshes our ground there;
4. a triangle outside the footprint radius is dropped: the footprint's edge is where the build's generated mesh,
   over our ground, takes over and is joined to it (finish at the seam as the interior copy does).

Read only from the source bundle under out/ (nothing extracted is committed).

    python -m tools.places.draft.srcnav <place_id> [--cell cx,cy] [--out FILE]
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ON_GROUND = 40.0
FLOAT_OVER = 96.0   # a source triangle this far over the source's own terrain stands on something, or on nothing
JOINT_DZ = 32.0   # tools.navmesh.params.AGENT_CLIMB
CELL = 4096.0


def _transform(place: dict, src_ground=None, our_ground=None):
    """(ours(x, y, z), the one offset): a source point in our coordinates. Under districts (place.json
    `wholesale.districts`, tools/places/draft/heights.py) a point takes its district's offset, or follows the carried
    ground where the grounds are given."""
    from tools.places.draft.heights import of_place
    fit = place["fit"]
    pv, an = fit["pivot"], fit["anchor"]
    rot = math.radians(float(fit.get("rot_deg", 0.0)))
    c, s = math.cos(rot), math.sin(rot)
    off = float((place.get("wholesale") or {}).get("offset", 0.0))
    H = of_place(place)

    def ours(x, y, z):
        dx, dy = x - pv[0], y - pv[1]
        X, Y = an[0] + dx * c + dy * s, an[1] - dx * s + dy * c   # clockwise, as geom.Xf
        if not H:
            return X, Y, z + off
        return X, Y, z + H.dz(x, y, src_ground=src_ground, our_xy=(X, Y), our_ground=our_ground)
    return ours, off


def carry(place: dict, navs: list[dict], src_ground, our_ground, changed_boxes: list, radius: float) -> dict:
    """{cells: {(cx,cy): {verts, tris}}, stats}: `src_ground(x,y)` the source terrain, `our_ground(x,y)` ours,
    `changed_boxes` [(x0,y0,x1,y1)] in our coordinates of source pieces deleted or moved."""
    ours, off = _transform(place, src_ground, our_ground)
    centre = place["fit"]["anchor"]
    cells: dict[tuple[int, int], dict] = {}
    st = {"tris_in": 0, "kept": 0, "outside": 0, "under_changed": 0, "verts_on_ground": 0, "verts_on_deck": 0,
          "ground_moved_max": 0.0}
    for m in navs:
        V = []
        for x, y, z in (v[:3] for v in m["verts"]):
            X, Y, Z = ours(x, y, z)
            g = src_ground(x, y)
            if g is not None and abs(z - g) <= ON_GROUND:
                h = our_ground(X, Y)
                if h is not None:
                    st["ground_moved_max"] = max(st["ground_moved_max"], abs(h - (z - (z - g) + off)))
                    Z = h + (z - g)
                V.append((X, Y, Z, True))
            else:
                V.append((X, Y, Z, False))
        for t in m["tris"]:
            st["tris_in"] += 1
            a, b, c = (V[i] for i in t[:3])
            mx, my = (a[0] + b[0] + c[0]) / 3, (a[1] + b[1] + c[1]) / 3
            if math.dist((mx, my), centre) > radius:
                st["outside"] += 1
                continue
            if any(x0 <= mx <= x1 and y0 <= my <= y1 for x0, y0, x1, y1 in changed_boxes):
                st["under_changed"] += 1
                continue
            key = (math.floor(mx / CELL), math.floor(my / CELL))
            cl = cells.setdefault(key, {"verts": [], "tris": [], "_ix": {}})
            ids = []
            for v in (a, b, c):
                k = (round(v[0], 1), round(v[1], 1), round(v[2], 1))
                if k not in cl["_ix"]:
                    cl["_ix"][k] = len(cl["verts"])
                    cl["verts"].append(list(k))
                    st["verts_on_ground" if v[3] else "verts_on_deck"] += 1
                ids.append(cl["_ix"][k])
            cl["tris"].append(ids)
            st["kept"] += 1
    for cl in cells.values():
        cl.pop("_ix")
    return {"cells": cells, "stats": st}


def carried_tris(place: dict, navs: list[dict], src_ground, our_ground, radius: float) -> dict:
    """Every source triangle whose middle lies within `radius` of the anchor, in our coordinates, flat (the build cuts
    them on our cell lines and the footprint): {tris: [(tri, flags, ground_moved)], steep: [tri], stats}. Rule 1 as
    `carry`; a triangle a ground vertex of which moved (our ground differs there) and is now steeper than the walkable
    angle, or that joins a deck or stair to the ground (corners on both) where the ground fell away by more than a
    climb (JOINT_DZ), or a corner of which off the source's ground now lies more than a climb under ours (a walkway our
    raised ground buries), is dropped and listed in `steep` (the build meshes that patch again, over the real pieces
    and ground)."""
    from tools.places.carrynav import MAX_SLOPE_DEG, slope_deg
    ours, off = _transform(place, src_ground, our_ground)
    centre = place["fit"]["anchor"]
    st = {"tris_in": 0, "kept": 0, "outside": 0, "steep": 0, "joints": 0, "buried": 0, "regrounded": 0, "ground_moved_max": 0.0}
    tris, steep, high = [], [], set()
    for m in navs:
        V, moved, on, buried, fell, over = [], [], [], set(), [], []
        for x, y, z in (v[:3] for v in m["verts"]):
            X, Y, Z = ours(x, y, z)
            g = src_ground(x, y)
            dz = 0.0
            grounded = g is not None and abs(z - g) <= ON_GROUND
            if grounded:
                h = our_ground(X, Y)
                if h is not None:
                    dz = (h + (z - g)) - Z
                    Z = h + (z - g)
            else:                       # a deck vertex our ground has risen over by more than a climb: buried
                h = our_ground(X, Y)
                if h is not None and Z < h - JOINT_DZ:
                    buried.add(len(V))
            V.append((X, Y, Z))
            over.append(None if g is None else z - g)
            moved.append(abs(dz))
            fell.append(-dz)
            on.append(grounded)
        for t in m["tris"]:
            st["tris_in"] += 1
            tri = [V[i] for i in t[:3]]
            mx, my = sum(p[0] for p in tri) / 3, sum(p[1] for p in tri) / 3
            if math.dist((mx, my), centre) > radius:
                st["outside"] += 1
                continue
            if any(i in buried for i in t[:3]):
                st["buried"] += 1
                steep.append(tri)
                continue
            dz = max(moved[i] for i in t[:3])
            st["ground_moved_max"] = round(max(st["ground_moved_max"], dz), 1)
            if dz > 1.0:
                st["regrounded"] += 1
                mixed = len({on[i] for i in t[:3]}) == 2
                # a deck's or stair's foot whose ground fell away by more than a climb: the foot hangs (ground that rose
                # over the bottom steps is walked onto the stair, and the slope rule judges it)
                if mixed and max(fell[i] for i in t[:3] if on[i]) > JOINT_DZ:
                    st["joints"] += 1
                    steep.append(tri)
                    continue
                if slope_deg(tri) > MAX_SLOPE_DEG:
                    st["steep"] += 1
                    steep.append(tri)
                    continue
            if all(over[i] is not None and over[i] > FLOAT_OVER for i in t[:3]):
                high.add(len(tris))     # over the source's terrain: held by a source piece, or by nothing
            tris.append((tri, int(t[3]) if len(t) > 3 else 0, dz))
            st["kept"] += 1
    return {"tris": tris, "steep": steep, "high": high, "stats": st}


def on_surface(posed, tri, r: float = 24.0, dz: float = 24.0) -> bool:
    """A triangle rests on a piece's walked surface (tools/places/shape.py): its middle, or every corner, within r in
    plan and dz in height of the piece's top or walked height there."""
    mx, my, mz = (sum(p[i] for p in tri) / 3 for i in range(3))
    if posed.surface_near(mx, my, mz, r, dz) is not None:
        return True
    return all(posed.surface_near(p[0], p[1], p[2], r, dz) is not None for p in tri)


SOLID = {"building", "static", "furniture", "door", "container", "rock", "tree", "activator"}
SKIP_KINDS = ("actor", "marker", "light", "plant", "clutter")


def laid_rise(led: Path) -> dict[str, float]:
    """The rise each source piece was laid at (ledger `rise`, written by `draft wholesale` under districts): the
    height its laid pose stands at, against which a hand's move is told."""
    if not led.exists():
        return {}
    return {e["src"]: float(e["rise"]) for e in (json.loads(ln) for ln in led.read_text().splitlines() if ln.strip())
            if e.get("status") == "placed" and e.get("rise") is not None}


def carried_disc(place: dict) -> tuple[list, float, float]:
    """Where the source's walking mesh is carried: (centre, radius, reach past it). The whole footprint round the
    anchor, reaching 512 past it; or, for a place that takes one part of its source (place.json `wholesale.take`,
    units round the pivot), only that part round the anchor, reaching no further, the rest meshed as ours."""
    take = (place.get("wholesale") or {}).get("take")
    if take:
        return place["fit"]["anchor"], float(take), 0.0
    return place["fit"]["anchor"], place["radius_m"] * 70, 512.0


def place_carry(pid: str, places: Path | None = None) -> dict:
    """The carried mesh of a wholesale place and the zones the build meshes again (carrynav): the source's triangles
    (carried_tris), and a zone for every source piece deleted (its true outline at the source pose, grown), moved (both
    outlines; its own triangles, those resting on its walked surface, move with it as a patch of their own), every
    solid piece we added (its outline, grown), every triangle too steep after re-grounding (the triangle itself).
    {tris, zones, moved: [(tri, flags, tag)], moved_on: [Posed now], ground, radius, centre, stats}."""
    from tools.places import carrynav as cn
    from tools.places.look.scene import Scene
    from tools.places.seat import Ground
    from tools.places.shape import Posed
    root = Path(__file__).resolve().parents[3]
    places = places or root / "newworld" / "places"
    sc = Scene(pid, places=places)
    place = sc.files["place"]
    bdir = root / "out" / "places" / "bundles" / f"src.{place['source_id']}"
    navs = [json.loads(ln) for ln in (bdir / "spaces/exterior/navmesh.jsonl").read_text().splitlines() if ln.strip()]
    sg = Ground.load(bdir)
    ours, off = _transform(place, sg.height, sc.ground.height)
    rot = math.radians(float(place["fit"].get("rot_deg", 0.0)))
    centre, radius, reach = carried_disc(place)
    got = carried_tris(place, navs, sg.height, sc.ground.height, radius + reach)
    led = places / pid / "ledger.jsonl"
    dropped = {e.get("src") for e in (json.loads(ln) for ln in led.read_text().splitlines() if ln.strip())
               if e.get("status") == "dropped"} if led.exists() else set()
    rises = laid_rise(led)
    now = {r["src"]: sc.by_id[r["id"]] for r in sc.refs.values() if r.get("src") and r["id"] in sc.by_id}
    zones, moved_pairs, holds = [], [], []
    st = {"deleted": 0, "moved": 0, "added": 0}

    def zone_of(p):
        po = Posed(p)
        h = po.outline()
        return (cn.grow(h) if len(h) >= 3 else None), po
    for r in (json.loads(ln) for ln in (bdir / "spaces/exterior/refs.jsonl").read_text().splitlines() if ln.strip()):
        if r.get("kind") in SKIP_KINDS:
            continue
        X, Y, Z = ours(*r["pos"])
        if r["id"] in rises:
            Z = r["pos"][2] + rises[r["id"]]
        if math.dist((X, Y), centre) > radius + reach:
            continue
        rr = list(r.get("rot") or [0, 0, 0])
        rr[2] = float(rr[2]) + rot
        sp = sc.piece({"id": "src:" + r["id"], "base": r["base"], "kind": r.get("kind"), "pos": [X, Y, Z], "rot": rr,
                       "scale": r.get("scale", 1)})
        if r.get("kind") in SOLID:
            h = Posed(sp).outline()
            if len(h) >= 3:
                holds.append(np.asarray(h, float))
        p = now.get(r["id"])
        if p is None:
            if r["id"] in dropped:      # never laid (wholesale's own drops: water, people, levelled)
                continue
            z, _ = zone_of(sp)
            if z:
                zones.append(z)
                st["deleted"] += 1
            continue
        A, B = np.asarray(p["m"], float), np.asarray(sp["m"], float)
        if np.abs(A[:3, 3] - B[:3, 3]).max() > 10 or np.abs(A[:3, :3] - B[:3, :3]).max() > 0.01:
            z0, po0 = zone_of(sp)
            z1, po1 = zone_of(p)
            zones += [z for z in (z0, z1) if z]
            moved_pairs.append((po0, po1, A @ np.linalg.inv(B)))
            st["moved"] += 1
    for p in sc.pieces:
        r = sc.refs.get(p["id"]) or {}
        if r.get("src") or p.get("kind") not in SOLID or r.get("disabled"):
            continue
        if math.dist((p["m"][0][3], p["m"][1][3]), centre) > radius + reach:
            continue
        z, _ = zone_of(p)
        if z:
            zones.append(z)
            st["added"] += 1
    zones += [cn.ccw([(q[0], q[1]) for q in t]) for t in got["steep"]]
    # a triangle the source laid well over its own terrain with no source piece under it floats over nothing (the
    # source's land under it was changed after its mesh was made): the build meshes our ground there instead
    unheld = unheld_tris(got["tris"], got.get("high", set()), holds)
    zones += [cn.ccw([(q[0], q[1]) for q in got["tris"][i][0]]) for i in sorted(unheld)]
    st["floating"] = len(unheld)
    moved, keep = [], []
    for i, (tri, flags, _) in enumerate(got["tris"]):
        if i in unheld:
            continue
        k = next((j for j, (po0, _, _) in enumerate(moved_pairs) if on_surface(po0, tri)), None)
        if k is None:
            keep.append((tri, flags, 0))
            continue
        M = moved_pairs[k][2]
        moved.append(([list((M @ np.array([*q, 1.0]))[:3]) for q in tri], flags, k + 1))
    st["zones"] = len(zones)
    st["moved_tris"] = len(moved)
    return {"tris": keep, "zones": zones, "moved": moved, "moved_on": [po1 for _, po1, _ in moved_pairs],
            "ground": sc.ground, "radius": radius, "centre": centre, "stats": {**got["stats"], **st}}


def _inside(poly: np.ndarray, x: float, y: float) -> bool:
    """(x, y) inside the plan polygon (even-odd rule)."""
    px, py = poly[:, 0], poly[:, 1]
    qx, qy = np.roll(px, -1), np.roll(py, -1)
    cross = (py > y) != (qy > y)
    xs = px + (y - py) * (qx - px) / np.where(qy - py == 0, 1e-9, qy - py)
    return bool(np.count_nonzero(cross & (x < xs)) % 2)


def unheld_tris(tris: list, high: set, holds: list, pad: float = 48.0) -> set:
    """The indices in `high` (triangles laid well over the source's terrain) whose middle lies under no source piece's
    outline (grown by pad in its box test): mesh floating over nothing."""
    boxes = [(h[:, 0].min() - pad, h[:, 1].min() - pad, h[:, 0].max() + pad, h[:, 1].max() + pad) for h in holds]
    out = set()
    for i in high:
        tri = tris[i][0]
        mx, my = sum(p[0] for p in tri) / 3, sum(p[1] for p in tri) / 3
        if not any(b[0] <= mx <= b[2] and b[1] <= my <= b[3] and _inside(h, mx, my) for b, h in zip(boxes, holds)):
            out.add(i)
    return out


def edge_report(cell: dict) -> dict:
    """The cell's open edges (used by one triangle): the seam the build must join to its generated mesh."""
    use: dict[tuple[int, int], int] = {}
    for t in cell["tris"]:
        for j in range(3):
            e = tuple(sorted((t[j], t[(j + 1) % 3])))
            use[e] = use.get(e, 0) + 1
    open_ = [e for e, n in use.items() if n == 1]
    return {"tris": len(cell["tris"]), "verts": len(cell["verts"]), "edges": len(use), "open_edges": len(open_)}


def main(argv: list[str]) -> int:
    sys.path.insert(0, ".")
    from tools.places.look.scene import Scene
    from tools.places.seat import Ground
    pid = argv[0]
    only = None
    out = None
    if "--cell" in argv:
        only = tuple(int(v) for v in argv[argv.index("--cell") + 1].split(","))
    if "--out" in argv:
        out = Path(argv[argv.index("--out") + 1])
    sc = Scene(pid)
    place = json.loads((Path("newworld/places") / pid / "place.json").read_text())
    bdir = Path("out/places/bundles") / f"src.{place['source_id']}"
    navs = [json.loads(ln) for ln in (bdir / "spaces/exterior/navmesh.jsonl").read_text().splitlines() if ln.strip()]
    sg = Ground.load(bdir)
    ours, off = _transform(place, sg.height, sc.ground.height)
    # source pieces we deleted or moved: the wholesale row's position against the piece as it now stands
    src_of = {r["id"]: r.get("src") for r in (json.loads(ln) for ln in
              (Path("newworld/places") / pid / "spaces/exterior/refs.jsonl").read_text().splitlines() if ln.strip())}
    now = {src_of.get(p["id"]): p for p in sc.pieces if src_of.get(p["id"])}
    changed = []
    centre, radius, _ = carried_disc(place)
    led = Path("newworld/places") / pid / "ledger.jsonl"
    rises = laid_rise(led)
    dropped = {e.get("src") for e in (json.loads(ln) for ln in led.read_text().splitlines() if ln.strip())
               if e.get("status") == "dropped"}
    for r in (json.loads(ln) for ln in (bdir / "spaces/exterior/refs.jsonl").read_text().splitlines() if ln.strip()):
        if r.get("kind") in ("actor", "marker", "light", "plant", "tree", "clutter"):
            continue
        X, Y, Z = ours(*r["pos"])
        if r["id"] in rises:
            Z = r["pos"][2] + rises[r["id"]]
        p = now.get(r["id"])
        if p is None and math.dist((X, Y), centre) <= radius:
            if r["id"] in dropped:     # never laid (wholesale's own drops: water, people, levelled)
                continue
            changed.append((X - 150, Y - 150, X + 150, Y + 150))
        elif p is not None and math.dist((p["m"][0][3], p["m"][1][3], p["m"][2][3]), (X, Y, Z)) > 10:
            changed.append((X - 150, Y - 150, X + 150, Y + 150))
    res = carry(place, navs, sg.height, sc.ground.height, changed, radius)
    rep = {"stats": res["stats"], "changed_pieces": len(changed),
           "cells": {f"{k[0]},{k[1]}": edge_report(v) for k, v in sorted(res["cells"].items())}}
    if only:
        cl = res["cells"].get(only, {"verts": [], "tris": []})
        rep["cell"] = {"id": list(only), **edge_report(cl)} if cl["tris"] else None
        if out:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps({"cell": list(only), **cl}))
    print(json.dumps(rep, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
