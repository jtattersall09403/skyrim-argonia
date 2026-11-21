"""The source place's own exterior navmesh, carried to our place at the wholesale transform (place.json `fit` and
`wholesale.offset`): every triangle of the source cells' NAVMs inside the footprint, in our coordinates, assigned to
our cell by its middle, with three narrow rules where the town or ground was changed by hand:

1. a vertex ON the source's ground (within ON_GROUND of the source terrain) follows our ground: it takes our ground's
   height there (our relief is the source's + offset, so it moves only where a mound, a bank or the edge band changed
   it); a vertex on a deck keeps its height (decks moved only with their pieces);
2. a triangle whose middle lies under a source piece we deleted or moved is dropped (its floor is gone or elsewhere);
   the build meshes again only those holes and what we added;
3. a triangle outside the footprint radius is dropped: the footprint's edge is where the build's generated mesh,
   over our ground, takes over and is joined to it (finish at the seam as the interior copy does).

Read only from the source bundle under out/ (nothing extracted is committed).

    python -m tools.places.draft.srcnav <place_id> [--cell cx,cy] [--out FILE]
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ON_GROUND = 40.0
CELL = 4096.0


def _transform(place: dict):
    fit = place["fit"]
    pv, an = fit["pivot"], fit["anchor"]
    rot = math.radians(float(fit.get("rot_deg", 0.0)))
    c, s = math.cos(rot), math.sin(rot)
    off = float((place.get("wholesale") or {}).get("offset", 0.0))

    def ours(x, y, z):
        dx, dy = x - pv[0], y - pv[1]
        return an[0] + dx * c - dy * s, an[1] + dx * s + dy * c, z + off
    return ours, off


def carry(place: dict, navs: list[dict], src_ground, our_ground, changed_boxes: list, radius: float) -> dict:
    """{cells: {(cx,cy): {verts, tris}}, stats}: `src_ground(x,y)` the source terrain, `our_ground(x,y)` ours,
    `changed_boxes` [(x0,y0,x1,y1)] in our coordinates of source pieces deleted or moved."""
    ours, off = _transform(place)
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
    ours, off = _transform(place)
    # source pieces we deleted or moved: the wholesale row's position against the piece as it now stands
    src_of = {r["id"]: r.get("src") for r in (json.loads(ln) for ln in
              (Path("newworld/places") / pid / "spaces/exterior/refs.jsonl").read_text().splitlines() if ln.strip())}
    now = {src_of.get(p["id"]): p for p in sc.pieces if src_of.get(p["id"])}
    changed = []
    led = Path("newworld/places") / pid / "ledger.jsonl"
    dropped = {e.get("src") for e in (json.loads(ln) for ln in led.read_text().splitlines() if ln.strip())
               if e.get("status") == "dropped"}
    for r in (json.loads(ln) for ln in (bdir / "spaces/exterior/refs.jsonl").read_text().splitlines() if ln.strip()):
        if r.get("kind") in ("actor", "marker", "light", "plant", "tree", "clutter"):
            continue
        X, Y, _ = ours(*r["pos"])
        p = now.get(r["id"])
        if p is None and math.dist((X, Y), place["fit"]["anchor"]) <= place["radius_m"] * 70:
            if r["id"] in dropped:     # never laid (wholesale's own drops: water, people, levelled)
                continue
            changed.append((X - 150, Y - 150, X + 150, Y + 150))
        elif p is not None and math.dist((p["m"][0][3], p["m"][1][3], p["m"][2][3]), (X, Y, r["pos"][2] + off)) > 10:
            changed.append((X - 150, Y - 150, X + 150, Y + 150))
    res = carry(place, navs, sg.height, sc.ground.height, changed, place["radius_m"] * 70)
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
