"""A place's baseline: every source exterior piece inside the place's footprint at one transform (place.json `fit`:
`pivot` in the source, `anchor` in ours, `rot_deg`) and its source height plus one common offset, with the source's
relief inside the footprint carried as land rows at the same offset (the band's slope held to SLOPE_DEG; our water
line kept by the ground stage's own rule). Nothing is fitted per cluster or seated; the only pieces left out are an
actor (people come from the place's people rows), the source's water plane (our water stands where it stands) and a
levelled base (decision 0035). The place's people, quest spots, interiors and stock rows are left as they are; the
draft's added pieces, streets, land rows and agent edits are cleared, since the baseline starts from the source.
What is laid: every source piece in the footprint, or with `--take <u>` only the part of the source within u of the
pivot (a place taking one part of a source another place shares; its walking mesh carried for that part alone).
How much ground comes: all of it (default), only within `--carry-radius` of the centre (a camp's own platform), at
most `--cap` units of change; `--keep-wet` carries a source pond's bed as a mud hollow. Then `--rooms` carries the
source's rooms and door pairs onto the laid doors and `--walks x,y` its walks as path rows; place.json
`wholesale.navmesh: "source"` makes the build write the source's own walking mesh (docs/design/place-studio.md,
Navmesh; skill place-site).

    python -m tools.places draft wholesale <place_id> --offset <units> [--take u] [--carry-radius u] [--cap u] [--keep-wet] [--dry]
    python -m tools.places draft wholesale <place_id> --offset <units> --rooms | --walks x,y
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import sys

from tools.places.draft import geom, ground, heights, io
from tools.places.draft.stages import Standing
from tools.places.seat import Ground

SLOPE_DEG = 35.0
LEVELLED = {"LVLN", "LVLI", "LVLC"}


def lay(st: Standing, offset: float, carry_radius: float | None = None, cap: float = 1e9, keep_wet: bool = False,
        take: float | None = None) -> tuple[list[dict], list[dict], list[dict], dict]:
    from tools.places.extract import load_place
    fit = st.place["fit"]
    pv, an = fit["pivot"], fit["anchor"]
    rot = math.radians(float(fit.get("rot_deg", 0.0)))
    c, s = math.cos(rot), math.sin(rot)
    rec = load_place(st.place_id)
    centre = (float(rec["world_x"]), float(rec["world_y"]))
    radius = float(st.place["radius_m"]) * ground.UNITS_PER_M

    def pt(x, y):
        dx, dy = x - pv[0], y - pv[1]
        return an[0] + dx * c + dy * s, an[1] - dx * s + dy * c   # clockwise, as geom.Xf and ground.carry
    ext, ledger, our_id = [], [], {}
    _, of, _ = st.clusters        # the source's own groups, as names for the look tool only; nothing is moved by them
    for r in st.src_ext:
        rid = r["id"]
        x, y = pt(r["pos"][0], r["pos"][1])
        b = st.bases.get(r["base"]) or {}
        why = None
        if math.dist((x, y), centre) > radius:
            why = "outside the place's footprint"
        elif take and math.dist(r["pos"][:2], pv[:2]) > take:
            why = f"outside the part of the source this place takes (within {take:g} of the pivot)"
        elif r.get("kind") == "actor":
            why = "a person: the place's people come from its people rows"
        elif r.get("kind") == "water":
            why = "the source's water plane; our world's water stands where it stands"
        elif (b.get("type") or b.get("sig")) in LEVELLED:
            why = "levelled (decision 0035)"
        if why:
            ledger.append({"src": rid, "space": "exterior", "status": "dropped", "why": why})
            continue
        rz = list(r.get("rot") or [0, 0, 0])
        rz[2] = round(float(rz[2]) + rot, 5)
        row = {"id": io.mint(st.place_id, "exterior", rid), "base": r["base"], "kind": r.get("kind"),
               "pos": [round(x, 2), round(y, 2), round(float(r["pos"][2]) + offset, 2)], "rot": rz,
               "scale": r.get("scale", 1.0), "layer": "place", "flags": r.get("flags") or [], "src": rid,
               "seat": {"mode": "free", "dz": 0.0}}
        if of.get(rid):
            row["cluster"] = of[rid]
        w = geom.walk(b)       # a walked deck's height over its origin: one stands on it, not in it (as adds.py)
        if w is not None:
            row["walk"] = w
        for k in io.CARRIED_KEYS:
            if r.get(k) is not None:
                row[k] = r[k]
        our_id[rid] = row["id"]
        ext.append(row)
        ledger.append({"src": rid, "space": "exterior", "status": "placed", "as": row["id"]})
    for row in ext:
        ep = row.get("enable_parent")
        if ep:
            if ep["ref"] in our_id:
                row["enable_parent"] = {**ep, "ref": our_id[ep["ref"]]}
            else:
                row.pop("enable_parent")
        if row.get("linked"):
            row["linked"] = [{**lk, "ref": our_id[lk["ref"]]} for lk in row["linked"] if lk.get("ref") in our_id]
            if not row["linked"]:
                row.pop("linked")
    G0 = Ground.load(st.grd.path)
    pieces = [(r["pos"][0], r["pos"][1]) for r in ext]
    g_centre, g_radius = ((an[0], an[1]), carry_radius or take) if take else (centre, carry_radius or radius)
    dist = resolve_districts(st, ext, G0, pt, of) if fit.get("districts") else []
    H = heights.Heights(dist, offset)
    land, rep = ground.carry(G0, st.S, pv, an, float(fit.get("rot_deg", 0.0)), pieces, g_centre, g_radius,
                             cap=cap, offset=offset, slope=SLOPE_DEG, keep_wet=keep_wet, field=H.field if H else None)
    for r in land:
        r["why"] = (f"the source's terrace of each district carried at its own offset ({', '.join(d['name'] for d in dist)})"
                    f", ours between them" if dist else f"the source's whole relief carried wholesale at offset {offset:g}")
    if dist:
        rises = raise_pieces(st, ext, of, dist, land, G0, offset)
        for lr in ledger:      # the rise each piece was laid at: the carried mesh reads it (srcnav.laid_rise)
            if lr["status"] == "placed":
                lr["rise"] = rises[lr["src"]]
        rep["districts"] = dist
    rep.update(pieces=len(ext), dropped=sum(1 for lr in ledger if lr["status"] == "dropped"))
    return ext, ledger, land, rep


def resolve_districts(st: Standing, ext: list[dict], G0: Ground, pt, of: dict) -> list[dict]:
    """place.json `fit.districts` resolved: each district's offset (`"auto"`: the median over its buildings and doors
    of our ground less the source's under each) and its pieces' source positions (`at`, thinned)."""
    by_src = {r["src"]: r for r in ext}
    out = []
    for d in st.place["fit"]["districts"]:
        cl = set(d["clusters"])
        mine = [st.by_src[s] for s in by_src if of.get(s) in cl]
        if not mine:
            raise ValueError(f"district {d['name']}: none of its clusters {sorted(cl)} has a piece laid")
        off = d.get("offset", "auto")
        if off == "auto":
            need = []
            for r in mine:
                if r.get("kind") not in ("building", "door"):
                    continue
                g, h = st.S.height(r["pos"][0], r["pos"][1]), G0.height(*pt(r["pos"][0], r["pos"][1]))
                if g is not None and h is not None:
                    need.append(h - g)
            if not need:
                raise ValueError(f"district {d['name']}: no building or door to take its offset from; give a number")
            need.sort()
            off = need[len(need) // 2]
        out.append({"name": d["name"], "offset": round(float(off), 1), "clusters": sorted(cl),
                    **({"terrace": False} if d.get("terrace") is False else {}),
                    "at": heights.thin((r["pos"][0], r["pos"][1]) for r in mine)})
    return out


def raise_pieces(st: Standing, ext: list[dict], of: dict, dist: list[dict], land: list[dict], G0: Ground,
                 offset: float) -> dict[str, float]:
    """Each laid piece's height under districts: a district's cluster at the district's offset; another source cluster
    whole, by its pieces' median rise over their own ground onto the carried ground; a loose piece by its own."""
    import copy
    G1 = copy.deepcopy(G0)
    G1.apply_patches(land)
    d_of = {c: d["offset"] for d in dist for c in d["clusters"]}

    def follow(r):
        s = st.by_src[r["src"]]
        g, h = st.S.height(s["pos"][0], s["pos"][1]), G1.height(r["pos"][0], r["pos"][1])
        return (h - g) if g is not None and h is not None else offset
    rise: dict[str, float] = {}
    out: dict[str, float] = {}
    groups: dict[str, list] = {}
    for r in ext:
        c = of.get(r["src"])
        if c and c not in d_of:
            groups.setdefault(c, []).append(follow(r))
    for c, v in groups.items():
        v.sort()
        rise[c] = v[len(v) // 2]
    for r in ext:
        c = of.get(r["src"])
        dz = d_of[c] if c in d_of else rise[c] if c in rise else follow(r)
        r["pos"][2] = round(float(st.by_src[r["src"]]["pos"][2]) + dz, 2)
        out[r["src"]] = round(float(dz), 2)
    return out


def carry_rooms(st: Standing, offset: float, drop_removals: set[str] = frozenset()) -> list[str]:
    """The source's rooms carried with their doors working: each way out of a room copied from this source leads to our
    copy of the source's own exterior door and lands where the source landed one, at the one transform (the room's door
    rows written afresh from the source's); `drop_removals`: rooms whose earlier `removed` rows are let go, so the room
    stands whole as the source built it. A copy of one room of a cell the source shares among several doors (its
    `room`: that room's way out) keeps its own way out alone, and the outside door leads into that copy. Rooms copied
    from another source are left as they are."""
    fit = st.place["fit"]
    pv, an = fit["pivot"], fit["anchor"]
    rot = math.radians(float(fit.get("rot_deg", 0.0)))
    c, s_ = math.cos(rot), math.sin(rot)
    H = heights.of_place(st.place)
    said = []
    for sp, space in st.files["spaces"].items():
        meta = space.get("space") or {}
        if sp == "exterior" or not str(meta.get("copy_of", "")).startswith(st.place["source_id"] + "/"):
            continue
        if meta.get("added"):     # a room the draft added behind its own added door (place-rooms): not the source's
            continue
        src_sp = st.src.spaces.get(sp) or st.src.spaces.get(str(meta["copy_of"]).split("/", 1)[1])
        if not src_sp:
            continue
        own = meta.get("room")   # a copy of one room of a shared cell: its own way out alone
        rows = [r for r in space["refs"] if not (r.get("door") and (r["door"].get("to_space") == "exterior"))
                and not (sp in drop_removals and r.get("removed"))]
        first = None
        for q in src_sp.refs:
            d = q.get("door") or {}
            if not d.get("to_ref") or d["to_ref"] not in st.by_src:     # a way out to the source's exterior only
                continue
            if own and q["id"] != own:
                continue
            x, y, z = d["to_pos"]
            dx, dy = x - pv[0], y - pv[1]
            to_rot = list(d.get("to_rot") or [0, 0, 0])
            to_rot[2] = round(float(to_rot[2]) + rot, 6)
            row = {k: q[k] for k in ("edid", "base", "kind", "pos", "rot", "scale", "layer", "flags") if k in q}
            row = {"id": io.mint(st.place_id, sp, q["id"]), **row, "src": q["id"],
                   "door": {**d, "to_space": "exterior", "to_ref": io.mint(st.place_id, "exterior", d["to_ref"]),
                            "to_pos": [round(an[0] + dx * c + dy * s_, 2), round(an[1] - dx * s_ + dy * c, 2),
                                       round(float(z) + rise(H, offset, st, x, y, an[0] + dx * c + dy * s_,
                                                                  an[1] - dx * s_ + dy * c), 2)], "to_rot": to_rot},
                   "seat": {"mode": "free"}}
            ext_door = next((r for r in st.ext if r.get("src") == d["to_ref"]), None)
            src_door = st.by_src.get(d["to_ref"]) or {}
            if ext_door is not None and src_door.get("pos"):   # the landing follows the door as it stands (a hand's move)
                a = float(ext_door["rot"][2]) - float((src_door.get("rot") or [0, 0, 0])[2])
                ca, sa = math.cos(a), math.sin(a)
                vx, vy = x - src_door["pos"][0], y - src_door["pos"][1]
                row["door"]["to_pos"] = [round(ext_door["pos"][0] + vx * ca + vy * sa, 2),
                                         round(ext_door["pos"][1] - vx * sa + vy * ca, 2),
                                         round(ext_door["pos"][2] + float(z) - src_door["pos"][2], 2)]
                row["door"]["to_rot"] = list(to_rot[:2]) + [round(float((d.get("to_rot") or [0, 0, 0])[2]) + a, 6)]
            rows.append(row)
            first = first or io.mint(st.place_id, "exterior", d["to_ref"])
            if ext_door is not None and ext_door.get("door"):     # the outside door's arrival: the same landing
                ext_door["door"].update(arrival=list(row["door"]["to_pos"]), to_space=sp, to_ref=row["id"])
        space["refs"][:] = rows
        if first:
            meta["door_from"] = first
        said.append(sp)
    return said


def rise(H: heights.Heights, offset: float, st: Standing, x: float, y: float, X: float, Y: float) -> float:
    """The rise of source point (x, y), at (X, Y) in ours: the one offset, or under districts its district's offset or
    the carried ground followed (heights.Heights.dz)."""
    if not H:
        return offset
    return H.dz(x, y, src_ground=st.S.height, our_xy=(X, Y), our_ground=st.G.height)


GAP = 160.0     # units: the widest break in the source's own mesh a carried walk steps across
SEAM_STEP = 48.0   # units: an open edge sampled this often to find the edge of another mesh it runs along
SEAM_REACH = 24.0  # units: two open edges this close in plan meet
SEAM_DZ = 48.0     # units: ... and this close in height


def _island(adj: dict, start: int) -> set:
    seen, stack = {start}, [start]
    while stack:
        for v in adj.get(stack.pop(), ()):
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return seen


def source_walks(st: Standing, offset: float, hub_xy: tuple[float, float]) -> list[dict]:
    """The source's own walked network carried as path rows: one row from each exterior door of the source (its landing,
    where the source's room lands one) to the hub, routed over the source's own exterior navmesh (its triangles'
    middles, joined across shared edges, within a mesh and between meshes), at the one transform; each point at the
    mesh's height plus the offset."""
    import heapq
    fit = st.place["fit"]
    pv, an = fit["pivot"], fit["anchor"]
    rot = math.radians(float(fit.get("rot_deg", 0.0)))
    c, s_ = math.cos(rot), math.sin(rot)
    H = heights.of_place(st.place)

    def ours(x, y, z):
        dx, dy = x - pv[0], y - pv[1]
        X, Y = an[0] + dx * c + dy * s_, an[1] - dx * s_ + dy * c
        return (round(X, 1), round(Y, 1), round(z + rise(H, offset, st, x, y, X, Y), 1))
    navs = io.read_jsonl(st.src.path / "spaces" / "exterior" / "navmesh.jsonl")
    nodes, adj, base_of, links, seam, open_pts = [], {}, {}, [], {}, []

    def join(u, v):
        adj.setdefault(u, set()).add(v)
        adj.setdefault(v, set()).add(u)
    for m in navs:
        V = m["verts"]
        base_of[m["id"]] = base = len(nodes)
        for t in m["tris"]:
            a, b, cc = (V[i] for i in t[:3])
            nodes.append(((a[0] + b[0] + cc[0]) / 3, (a[1] + b[1] + cc[1]) / 3, (a[2] + b[2] + cc[2]) / 3))
        for i, (t, te) in enumerate(zip(m["tris"], m["tri_edges"])):
            for j in range(3):
                if t[3] & (1 << j):                     # a portal edge (NVNM flag bit j): te[j] indexes edge_links
                    lk = m["edge_links"][te[j]]
                    links.append((base + i, lk["mesh"], lk["tri"]))
                elif 0 <= te[j] < len(m["tris"]):       # the mesh's own neighbour across this edge
                    join(base + i, base + te[j])
                else:                                   # an open edge: joined to another mesh's sharing its two ends
                    e = tuple(sorted((tuple(round(v / 32) for v in V[t[j]][:2]),
                                      tuple(round(v / 32) for v in V[t[(j + 1) % 3]][:2]))))
                    for k in seam.get(e, []):
                        if k < base:
                            join(base + i, k)
                    seam.setdefault(e, []).append(base + i)
                    p, q = V[t[j]], V[t[(j + 1) % 3]]
                    n = max(1, int(math.dist(p[:2], q[:2]) // SEAM_STEP))
                    for s in range(n + 1):
                        f = s / n
                        open_pts.append((p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f, p[2] + (q[2] - p[2]) * f,
                                         base + i, base))
    # meshes the source left unlinked (one per cell piece, their shared edges split differently): an open edge of
    # one that runs along an open edge of another is a seam the source's walkers cross
    if open_pts:
        from scipy.spatial import cKDTree
        P = [(o[0], o[1]) for o in open_pts]
        for a, b in cKDTree(P).query_pairs(SEAM_REACH):
            oa, ob = open_pts[a], open_pts[b]
            if oa[4] != ob[4] and abs(oa[2] - ob[2]) <= SEAM_DZ:
                join(oa[3], ob[3])
    for u, mesh, tri in links:
        if mesh in base_of:
            join(u, base_of[mesh] + tri)

    def near(x, y, z=None):
        return min(range(len(nodes)), key=lambda k: math.dist(nodes[k][:2], (x, y)) + (abs(nodes[k][2] - z) if z is not None else 0))

    def route(a, b):
        dist, prev, q = {a: 0.0}, {}, [(0.0, a)]
        while q:
            d, u = heapq.heappop(q)
            if u == b:
                break
            if d > dist.get(u, 1e18):
                continue
            for v in adj.get(u, ()):
                nd = d + math.dist(nodes[u], nodes[v])
                if nd < dist.get(v, 1e18):
                    dist[v], prev[v] = nd, u
                    heapq.heappush(q, (nd, v))
        if b not in dist:
            return None
        out = [b]
        while out[-1] != a:
            out.append(prev[out[-1]])
        return out[::-1]
    hx, hy = hub_xy[0] - an[0], hub_xy[1] - an[1]
    hub = near(pv[0] + hx * c + hy * s_, pv[1] - hx * s_ + hy * c)
    rows, lost = [], []
    for sp in sorted(st.src.spaces):
        if sp == "exterior":
            continue
        for q in st.src.spaces[sp].refs:
            d = q.get("door") or {}
            if d.get("to_ref") not in st.by_src:
                continue
            x, y, z = d["to_pos"]
            start = near(x, y, z)
            got = route(start, hub)
            if not got:   # the door's patch of mesh is cut off in the source: hop the narrowest gap (<= GAP) at level
                isl = _island(adj, start)
                main = _island(adj, hub)
                gap = min(((math.dist(nodes[i], nodes[j]), i, j) for i in isl for j in main), default=None)
                if gap and gap[0] <= GAP:
                    print(f"{d['to_ref']}: its patch of the source's mesh is cut off; joined across {gap[0]:.0f} units")
                    a_ = route(start, gap[1]) or [start]
                    got = a_ + (route(gap[2], hub) or [])
            if not got:
                lost.append(d["to_ref"])
                continue
            pts = [ours(x, y, z)]
            for k in got:
                p_ = ours(*nodes[k])
                if math.dist(p_[:2], pts[-1][:2]) >= 96:
                    pts.append(p_)
            rows.append({"id": io.mint(st.place_id, "walk", d["to_ref"]), "kind": "walkway", "points": [list(p_) for p_ in pts],
                         "width": 128.0, "style": "boardwalk", "from": d["to_ref"], "to": "landing",
                         "laid": "the source's own walked network (its exterior navmesh), from the door's landing to the "
                                 "landing, carried at the one transform"})
    if lost:
        print("no walk on the source's navmesh from:", lost)
    return rows


def hand_refusal(pdir) -> str | None:
    """Why a whole re-lay of this place is refused, or None: it re-lays every exterior piece and clears paths, land
    rows and agent edits, so the hands' work (agent saves, the owner's studio saves, hand-placed rows) would be lost."""
    from tools.places import hands
    from tools.places.draft.stages import owner_saves
    rows = hands.placed(pdir)
    agent = sorted(p.stem for p in (pdir / "agent-edits").glob("*.json")) if (pdir / "agent-edits").exists() else []
    owner = owner_saves(pdir)
    if not (rows or agent or owner):
        return None
    return (f"draft wholesale {pdir.name}: refused: the place holds hand edits ({len(rows)} hand-placed rows; agent "
            f"saves {', '.join(agent) or 'none'}; owner's finalised saves {', '.join(owner) or 'none'}), and a whole "
            f"re-lay replaces every exterior piece and clears paths, land rows and agent edits. Change it narrowly "
            f"instead: `--rooms` re-carries the rooms and `--walks x,y` the walks without touching pieces; a piece or "
            f"unit is changed by hand (look, `look commit`); a rule's output by its stage (`draft <stage>`). A "
            f"deliberate whole re-lay that loses them: --discard-hand-edits.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places draft wholesale", description=__doc__.split("\n")[0])
    ap.add_argument("place_id")
    ap.add_argument("--offset", type=float, required=True)
    ap.add_argument("--carry-radius", type=float, default=None,
                    help="units: the relief carried only this far from the centre (the camp's own platform), faded to ours by it")
    ap.add_argument("--cap", type=float, default=1e9, help="units: the most the carried relief changes our ground")
    ap.add_argument("--take", type=float, default=None,
                    help="units round the pivot: only this part of the source is laid (and its walking mesh and ground "
                         "carried); for a place taking one part of a source another place shares")
    ap.add_argument("--keep-wet", action="store_true", help="the source's pond bed carried as a mud hollow (not faded to ours)")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--rooms", action="store_true", help="carry the source's rooms, door pairs and arrivals onto the laid doors (the pieces as they stand)")
    ap.add_argument("--walks", default="", help="x,y of the hub: the source's walks carried as path rows")
    ap.add_argument("--discard-hand-edits", action="store_true",
                    help="re-lay the whole baseline over a place that holds hand edits, losing them")
    ap.add_argument("--whole", default="", help="rooms (comma-separated) whose removals are let go")
    a = ap.parse_args(argv)
    from tools.places.draft import differs
    owe = [f for f in differs.faults(a.place_id, io.PLACES, laying=True) if "the same part of the source" not in f]
    if owe:
        print(f"draft wholesale {a.place_id}: refused: this place shares its source with a place laid first, and its "
              f"plan does not yet say how it differs:\n  " + "\n  ".join(owe), file=sys.stderr)
        return 1
    st = Standing(a.place_id)
    if a.walks:
        hub = tuple(float(v) for v in a.walks.split(","))
        rows = source_walks(st, a.offset, hub)
        keep = [p for p in st.files["paths"] if not p["id"].startswith(f"{st.place_id}.walk.")]
        print(len(rows), "walks:", [(r["from"][-6:], len(r["points"])) for r in rows])
        if not a.dry:
            io.write_jsonl(st.pdir / "paths.jsonl", keep + rows)
        return 0
    if a.rooms:
        from tools.places import edits
        said = carry_rooms(st, a.offset, set(filter(None, a.whole.split(","))))
        if not a.dry:
            edits.write_place(st.pdir, st.files)
        print("rooms carried:", ", ".join(said))
        return 0
    if not a.dry and not a.discard_hand_edits:
        why = hand_refusal(st.pdir)
        if why:
            print(why, file=sys.stderr)
            return 1
    ext, ledger, land, rep = lay(st, a.offset, a.carry_radius, a.cap, a.keep_wet, a.take)
    print(json.dumps({k: ([{**d, "at": len(d["at"])} for d in v] if k == "districts" else v)
                      for k, v in rep.items() if k != "hull"}))
    if a.dry:
        return 0
    pdir = st.pdir
    old = io.read_jsonl(pdir / "ledger.jsonl")
    keep = [lr for lr in old if lr.get("space") != "exterior"]
    io.write_jsonl(pdir / "spaces" / "exterior" / "refs.jsonl", ext)
    io.write_jsonl(pdir / "ledger.jsonl", keep + ledger)
    io.write_jsonl(pdir / "land.jsonl", land)
    io.write_jsonl(pdir / "paths.jsonl", [])
    place = json.loads((pdir / "place.json").read_text())
    walk = (place.get("wholesale") or {}).get("navmesh")    # the drafter's choice of walking mesh stays (build.source_navmesh)
    place["wholesale"] = {k: rep.get(k) for k in ("offset", "band", "pieces", "dropped", "raised_max", "lowered_max",
                                                  "band_steepest_deg", "source_water_area_m2", "held_by_water", "districts")
                          if rep.get(k) is not None}
    if walk:
        place["wholesale"]["navmesh"] = walk
    if a.take:
        place["wholesale"]["take"] = a.take       # the part of the source taken: srcnav.carried_disc carries only it
    import datetime   # when the baseline was laid: which of two places on one source came first (differs.py)
    place["wholesale"]["laid"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    place["agent_saves_applied"] = []
    place.pop("steps", None)
    (pdir / "place.json").write_text(json.dumps(place, indent=1, ensure_ascii=False) + "\n")
    shutil.rmtree(pdir / "agent-edits", ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
