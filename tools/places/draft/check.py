"""`draft check <place_id>`: the draft's self-checks, on the place files, the source bundle and the ground bundle.

Fails on: a source ref not accounted for (placed, adapted, replaced, or dropped with a reason); a ref not seated as
its rule says (floating or buried); a building on ground steeper than the source's own with no patch; a door no
path reaches; a promised service with nobody giving it; fewer beds than people; anything in water that the source
had on land, or the reverse; a Nordic or levelled base placed; a person whose bed or routine points at nothing;
and every check of the build (`tools/places/check.py`, its streets on the main walked network among them) on the
draft built.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from tools.places.draft import geom, interiors, io, people
from tools.places.draft import paths as paths_mod
from tools.places.draft.geom import LEVELLED
from tools.places.draft.fit import relief_allowed
from tools.places.draft.paths import connected, dist_to_paths
from tools.places.seat import Ground, foot_points, foot_relief, seat_all

SEAT_TOL = 1.0
RELIEF_SLACK_ALL = 48.0
SOLID = {"building", "static", "furniture", "container", "door", "activator"}
summary: dict = {}       # the last check's measures (patches, streets, aligned pieces), printed by main
DOOR_REACH = 160.0


def check(place_id: str, bundles: Path = io.BUNDLES, places: Path = io.PLACES, gives: list | None = None) -> list[str]:
    pdir = places / place_id
    place = json.loads((pdir / "place.json").read_text())
    src = io.load(f"src.{place['source_id']}", bundles)
    grd = io.load(f"ground.{place_id}", bundles)
    bases = io.place_bases(src, grd, place)
    if gives is None:
        from tools.places.draft.run import place_record
        gives = place_record(place_id)[1]
    G = Ground.load(grd.path)
    land = io.read_jsonl(pdir / "land.jsonl")
    G.apply_patches(land)
    S = src.ground
    refs = io.read_jsonl(pdir / "spaces" / "exterior" / "refs.jsonl")
    ledger = io.read_jsonl(pdir / "ledger.jsonl")
    paths = io.read_jsonl(pdir / "paths.jsonl")
    folk = io.read_jsonl(pdir / "people.jsonl")
    bad: list[str] = []
    summary.clear()

    # 1. every source ref accounted for
    seen = {(r["space"], r["src"]) for r in ledger}
    for sid, sp in src.spaces.items():
        whole = (sid, "*") in seen
        for r in sp.refs:
            if (sid, r["id"]) not in seen and not (whole and r.get("kind") != "actor"):
                bad.append(f"unaccounted source ref {sid}/{r['id']}")
    for r in ledger:
        if r["status"] not in ("placed", "adapted", "replaced", "dropped"):
            bad.append(f"ledger {r['src']}: unknown status {r['status']}")
        if r["status"] == "dropped" and not r.get("why"):
            bad.append(f"ledger {r['src']}: dropped without a reason")

    # 2. seated as the rule says
    want = [dict(r, pos=list(r["pos"])) for r in refs]
    seat_all(want, G)
    for r, w in zip(refs, want):
        if abs(r["pos"][2] - w["pos"][2]) > SEAT_TOL:
            bad.append(f"{r['id']} ({r['base']}) not seated: z {r['pos'][2]:.1f}, its rule gives {w['pos'][2]:.1f}")

    # 3. buildings on ground no steeper than the source's (or patched)
    src_by = {r["id"]: r for r in src.exterior.refs}
    patched = {tuple(p["cell"]) for p in land}
    for r in refs:
        if r.get("kind") != "building" or not r["seat"].get("foot"):
            continue
        f = r["seat"]["foot"]
        s = src_by.get(r.get("src"))
        src_rel = foot_relief(S, s["pos"][0], s["pos"][1], s["rot"][2], f) if s else 0.0
        rel = foot_relief(G, r["pos"][0], r["pos"][1], r["rot"][2], f)
        allow = relief_allowed(src_rel, r["seat"], place["fit"].get("relief_norm", 64.0))
        if allow is not None and rel > allow + 1:
            cell = (math.floor(r["pos"][0] / 4096), math.floor(r["pos"][1] / 4096))
            bad.append(f"{r['id']} on ground rising {rel:.0f} (source {src_rel:.0f})"
                       f"{' despite a patch' if cell in patched else ' with no patch'}")

    # 4. water where the source had water, land where it had land
    for r in refs:
        s = src_by.get(r.get("src"))
        if not s or r["seat"].get("mode") in ("on", "free", "above"):
            continue
        sw, ow = S.wet(s["pos"][0], s["pos"][1], 16), G.wet(r["pos"][0], r["pos"][1], 16)
        if r.get("kind") in ("building", "static", "furniture", "container", "door") and sw != ow:
            bad.append(f"{r['id']} ({r['kind']}) {'in water' if ow else 'on land'}; the source had it "
                       f"{'in water' if sw else 'on land'}")

    # 5. every door reached by a path, one network
    doors = [r for r in refs if r.get("door") and r["door"].get("to_space") not in (None, "exterior")]
    ends = {}
    for p in paths:
        ends.setdefault(p.get("from"), p["points"][0])
        ends.setdefault(p.get("to"), p["points"][-1])
    reached = set()
    for d in doors:
        p = ends.get(d.get("src"))
        if p is None or dist_to_paths(p, paths) > DOOR_REACH:
            bad.append(f"door {d['id']} reached by no path")
        else:
            reached.add(d["id"])
    if not connected(paths):
        bad.append("the paths are not one network")
    for d in doors:
        sid = d["door"]["to_space"]
        if not (pdir / "spaces" / sid / "space.json").exists():
            bad.append(f"door {d['id']} leads to {sid}, which is not drafted")

    # 6. services, beds, people
    given = {(g["seq"]) for p in folk for g in p.get("services") or []}
    for g in gives:
        if g["give_kind_id"] in people.PERSON_GIVES and g["seq"] not in given:
            bad.append(f"promised {g['give_kind_id']} ({g.get('detail')}) has nobody giving it")
    beds_total = 0
    bed_refs = {}
    for sdir in sorted((pdir / "spaces").iterdir()):
        sj = sdir / "space.json"
        if sdir.name == "exterior" or not sj.exists():
            continue
        sj = json.loads(sj.read_text())
        copy_of = sj["copy_of"].split("/", 1)[1]
        for b in interiors.beds_in(src.spaces[copy_of].refs, bases, sj.get("room"), sj["copy_of"]):
            beds_total += b["sleeps"]
            bed_refs[(sdir.name, b["ref"])] = b["sleeps"]
    for r in refs:   # the guard camp's beds, outdoors
        if r.get("kind") == "furniture" and not r.get("removed") and interiors.is_bed(bases.get(r.get("base")) or {}):
            n_ = interiors.sleeps(bases.get(r["base"]) or {})
            beds_total += n_
            bed_refs[("exterior", r["id"])] = n_
    sleepers = [p for p in folk if p["role"] not in people.NO_BED]   # innkeepers keep the inn all night (Skyrim)
    if beds_total < len(sleepers):
        bad.append(f"{len(sleepers)} sleepers for {beds_total} beds")
    use: dict = {}
    for p in folk:
        hours = sum(s["hours"] for s in p["routine"])
        if hours != 24:
            bad.append(f"{p['id']} routine covers {hours} hours")
        if p["role"] in people.NO_BED:
            if any(s["kind"] == "sleep" for s in p["routine"]):
                bad.append(f"{p['id']} ({p['role']}) sleeps, but the role keeps its post all day and night")
            continue
        if not p.get("bed"):
            bad.append(f"{p['id']} ({p['role']}) has no bed")
            continue
        k = (p["bed"]["space"], p["bed"]["ref"])
        if k not in bed_refs:
            bad.append(f"{p['id']} sleeps in {k}, which is not a bed of the draft")
        use[k] = use.get(k, 0) + 1
    for k, n in use.items():
        if n > bed_refs.get(k, 0):
            bad.append(f"bed {k} slept in by {n}")
    # an inn that rents a room keeps a bed nobody owns; guards sleep in their camp or barracks, never the inn's rooms
    for p in folk:
        if not any((g.get("give_kind_id") or g.get("kind")) == "inn-room" for g in p.get("services") or []):
            continue
        inn = (p.get("work") or {}).get("space")
        if not any(sp_ == inn and k_ not in use for (sp_, k_) in bed_refs):
            bad.append(f"{p['id']} rents the inn's room, but every bed of {inn} is owned")
        for q in folk:
            if q["role"] == "guard" and (q.get("bed") or {}).get("space") == inn:
                bad.append(f"guard {q['id']} sleeps in the inn {inn}")
    homes: dict = {}
    for p in folk:
        hh = (p.get("household") or {}).get("id")
        if hh:
            homes.setdefault(hh, set()).add(p.get("home"))
        elif p["role"] == "resident":
            bad.append(f"resident {p['id']} belongs to no household")
    for hh, hs in homes.items():
        if len(hs) != 1:
            bad.append(f"household {hh} lives in several homes {sorted(map(str, hs))}")
    for p in folk:
        if p["role"] == "guard" and len((p.get("patrol") or {}).get("points") or []) < 2:
            bad.append(f"guard {p['id']} has no patrol")
        if not p.get("base_from"):
            bad.append(f"{p['id']} ({p['role']}) has no actor base")
        elif p["base_from"] in src.npcs and not people.usable(src.npcs[p["base_from"]], src.npcs):
            bad.append(f"{p['id']} built on a Nordic or levelled actor {p['base_from']}")

    # 8. land patches: small, bounded, never across the waterline
    G0 = Ground.load(grd.path)
    pmax = place.get("fit", {}).get("patch_max", 105.0)
    points = 0
    for p in land:
        cx, cy = p["cell"]
        for row, col, dz in p["verts"]:
            points += 1
            if abs(dz) > pmax + 0.5:
                bad.append(f"land patch at cell {p['cell']} ({row},{col}) changes the ground by {dz:.0f} (bound {pmax:.0f})")
            gx, gy = cx * 32 + col, cy * 32 + row
            h0 = G0.vertex(gx, gy)
            w = G0.water(gx * 128.0, gy * 128.0)
            if h0 is not None and w is not None and (h0 < w) != (h0 + dz < w):
                bad.append(f"land patch at cell {p['cell']} ({row},{col}) moves the ground across the waterline")
    summary["patch_cells"], summary["patch_points"] = len(land), points
    summary["patch_largest"] = max((abs(v[2]) for p in land for v in p["verts"]), default=0.0)

    # 9. streets: never through a building, never over open water without a walkway
    walk = [r for r in refs if paths_mod.WALKWAY.search(str((bases.get(r["base"]) or {}).get("model", "")))
            or "street" in str(r.get("why", ""))]
    solid_b = [r for r in refs if r.get("kind") == "building" and r not in walk and r["seat"].get("foot")
               and not geom.underfoot(r, bases, G)]
    total = 0.0
    for p in paths:
        pts = p["points"]
        # a link walks the building an end of it stands in (a ship's hatch is on its ship), and no other
        own = {r["id"] for r in solid_b for e in (pts[0], pts[-1]) if geom.contains_xy(r, bases, e[0], e[1], 64)}
        for a, b in zip(pts, pts[1:]):
            n = max(1, int(math.dist(a, b) // 128))
            total += math.dist(a, b)
            for k in range(1, n):
                q = (a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n)
                if min(math.dist(q, pts[0]), math.dist(q, pts[-1])) < DOOR_REACH:
                    continue      # the step up to a door
                if any(geom.contains_xy(r, bases, q[0], q[1], -48) for r in solid_b if r["id"] not in own):
                    bad.append(f"street {p['id']} runs through a building at {q[0]:.0f},{q[1]:.0f}")
                    break
                if G.wet(q[0], q[1], 32) and not any(geom.contains_xy(r, bases, q[0], q[1], 96) for r in walk):
                    bad.append(f"street {p['id']} crosses open water at {q[0]:.0f},{q[1]:.0f} with no walkway")
                    break
    summary["streets"], summary["street_length_m"] = len(paths), round(total / 70.0)

    # 10. every promised crafting station placed and worked by someone
    st = place.get("stations") or {}
    for s_ in st.get("missing") or []:
        bad.append(f"promised station {s_} is missing")
    ref_by = {r["id"]: r for r in refs}
    for a in st.get("added") or []:
        if a["station"] == "shrine":     # a shrine is used by the passer-by, not worked
            if a["id"] not in ref_by:
                bad.append(f"shrine {a['id']} is not placed")
            continue
        w = next((p["work"] for p in folk if p["id"] == a["by"]), None)
        if w is None:
            bad.append(f"station {a['station']} has nobody to work it")
        elif a["space"] == "exterior":
            r = ref_by.get(a["id"])
            c = w.get("pos") or (ref_by.get(w.get("ref")) or {}).get("pos")
            if r is None or c is None or math.dist(r["pos"][:2], c[:2]) > w.get("radius", 384) + 256:
                bad.append(f"station {a['station']} stands away from its worker's work stop")
        elif w.get("space") != a["space"]:
            bad.append(f"station {a['station']} is not where its worker works")

    # 11. a replaced door or directional piece lies in the original's plane
    for r in refs:
        al = r.get("align")
        if not al:
            continue
        old, new = geom.plane(bases.get(al["of"]) or {}), geom.plane(bases.get(r["base"]) or {})
        if not old or not new:
            bad.append(f"{r['id']}: no geometry to prove its plane against {al['of']}")
            continue
        rz = r["rot"][2]
        rz0 = rz - math.radians(al["turn_deg"])
        o = geom.turn(old["centre"], rz0)
        n_ = geom.turn(new["centre"], rz)
        ow = (r["pos"][0] - al["shift"][0] + o[0], r["pos"][1] - al["shift"][1] + o[1])
        nw = (r["pos"][0] + n_[0], r["pos"][1] + n_[1])
        ao = geom.turn((1.0, 0.0) if old["axis"] == 0 else (0.0, 1.0), rz0)
        an = geom.turn((1.0, 0.0) if new["axis"] == 0 else (0.0, 1.0), rz)
        if abs(ao[0] * an[0] + ao[1] * an[1]) < 0.97:
            bad.append(f"{r['id']} ({r['kind']}) faces across the original's plane")
        if math.dist(ow, nw) > 16:
            bad.append(f"{r['id']} ({r['kind']}) plane {math.dist(ow, nw):.0f} units from the original's")
        summary.setdefault("aligned", 0)
        summary["aligned"] += 1

    # 12. nothing floating or buried: the gap between a thing's underside along its true outline and the ground,
    # against how it sat in the source
    norm = place.get("fit", {}).get("relief_norm", 64.0)
    for r in refs:
        f = r["seat"].get("foot")
        s_ = src_by.get(r.get("src"))
        if not f or not s_ or r["seat"].get("mode") not in ("ground", "clear") or r.get("base") != s_.get("base") \
                or r.get("kind") not in SOLID:
            continue
        b = geom.bounds(r, bases)
        if not b:
            continue

        def gaps(g_, x, y, z, rz):
            hs = [g_.height(px, py) for px, py in foot_points(x, y, rz, f, 5)]
            return [z + b[0][2] - h for h in hs if h is not None]
        go = gaps(G, r["pos"][0], r["pos"][1], r["pos"][2], r["rot"][2])
        gs = gaps(S, s_["pos"][0], s_["pos"][1], s_["pos"][2], s_["rot"][2])
        if not go or not gs:
            continue
        if r["seat"]["mode"] == "ground" and max(go) > max(max(gs), 0.0) + 16:
            bad.append(f"{r['id']} ({r['kind']}) floats {max(go):.0f} above our ground (source {max(gs):.0f})")
        src_rel = foot_relief(S, s_["pos"][0], s_["pos"][1], s_["rot"][2], f)
        allow = relief_allowed(src_rel, r["seat"], norm) or max(norm, RELIEF_SLACK_ALL)
        if -min(go) > -min(gs) + allow + 16:
            bad.append(f"{r['id']} ({r['kind']}) buried {-min(go):.0f} into our ground (source {-min(gs):.0f})")

    # 13. every door opens the way out: its arrival on our ground, clear of collision, its plane across the way out
    for d in doors:
        a = (d["door"] or {}).get("arrival")
        if not a:
            bad.append(f"door {d['id']} has no arrival point outside it")
            continue
        if not G.has(a[0], a[1]):
            bad.append(f"door {d['id']} arrival is off our ground")
        elif (G.wet(a[0], a[1], 16) and not G.wet(d["pos"][0], d["pos"][1], 16)
              and not (len(a) > 2 and G.water(a[0], a[1]) is not None and a[2] > G.water(a[0], a[1]))):
            bad.append(f"door {d['id']} arrival is in the water")
        pl = geom.plane(bases.get(d["base"]) or {})
        if pl and math.dist(a[:2], d["pos"][:2]) > 16:
            n_ = geom.turn((1.0, 0.0) if pl["axis"] == 0 else (0.0, 1.0), d["rot"][2])
            out = ((a[0] - d["pos"][0]) / math.dist(a[:2], d["pos"][:2]), (a[1] - d["pos"][1]) / math.dist(a[:2], d["pos"][:2]))
            if abs(n_[0] * out[0] + n_[1] * out[1]) < 0.5:
                bad.append(f"door {d['id']} opens along its wall, not toward its way out")
        f = geom.front(bases.get(d["base"]) or {}) if d.get("align") else None
        if f is not None and math.dist(a[:2], d["pos"][:2]) > 16:
            n_, lc = geom.turn(f, d["rot"][2]), geom.turn(pl["centre"], d["rot"][2])
            if n_[0] * (a[0] - d["pos"][0] - lc[0]) + n_[1] * (a[1] - d["pos"][1] - lc[1]) < 0:
                bad.append(f"door {d['id']} faces in: its front is away from its arrival")

    # 7. no Nordic or levelled base placed
    for r in refs:
        b = bases.get(r["base"]) or {}
        if b.get("nordic"):
            bad.append(f"{r['id']} places a Nordic base {r['base']}")
        if str(b.get("type")) in LEVELLED:
            bad.append(f"{r['id']} places a levelled base {r['base']}")
    bad += nordic_in_copies(pdir, src, bases)

    # 14. no world plant left standing in what we placed or on a street (the build's clear check)
    from tools.places.draft import clear as clearmod
    world = [r for r in (grd.exterior.refs if grd.exterior else []) if r.get("layer", "world") == "world"]
    cleared = {c.get("ref") for c in io.read_jsonl(pdir / "clear.jsonl")}
    placed = [r for r in refs if r.get("kind") in geom.SOLID_KINDS]
    bad += clearmod.stray(world, cleared, placed, bases, paths)
    return bad


def nordic_in_copies(pdir: Path, src, bases: dict) -> list[str]:
    """An interior copy brings its source room whole: every ref it keeps unchanged, and every override, must be of a
    base the Nordic review (or, unreviewed, the folder rule) passes."""
    bad = []
    for sj in sorted((pdir / "spaces").glob("*/space.json")):
        sp = json.loads(sj.read_text())
        if sp.get("space_id") == "exterior" or not sp.get("copy_of"):
            continue
        rows = {r["src"]: r for r in io.read_jsonl(sj.parent / "refs.jsonl") if r.get("src")}
        keep = interiors.kept(sp["copy_of"], sp.get("room"))
        src_sp = src.spaces.get(sp["copy_of"].split("/", 1)[1])
        for r in (src_sp.refs if src_sp else []):
            if r.get("kind") == "actor" or (keep is not None and r["id"] not in keep):
                continue
            row = rows.get(r["id"], r)
            if not row.get("removed") and (bases.get(row.get("base")) or {}).get("nordic"):
                bad.append(f"{sp['space_id']}/{r['id']} keeps a Nordic base {row['base']}")
        for row in io.read_jsonl(sj.parent / "refs.jsonl"):
            if not row.get("src") and (bases.get(row.get("base")) or {}).get("nordic"):
                bad.append(f"{sp['space_id']}/{row['id']} adds a Nordic base {row['base']}")
    return bad


def round_trip(place_id: str, places: Path = io.PLACES) -> list[str]:
    """The place files are in the contract's canonical order and text: the studio's load then write is byte-equal."""
    import tempfile
    from tools.places import edits
    pdir = places / place_id
    with tempfile.TemporaryDirectory() as tmp:
        td = Path(tmp) / "places" / place_id     # the writer keeps a place's sources beside its places folder
        edits.write_place(td, edits.load_place(pdir))
        return [f"{f.relative_to(td)} is not in the canonical order and text (load then write changes it)"
                for f in sorted(td.rglob("*")) if f.is_file()
                and (not (pdir / f.relative_to(td)).exists() or (pdir / f.relative_to(td)).read_bytes() != f.read_bytes())]


def build_check(place_id: str, places: Path = io.PLACES) -> list[str]:
    """The build's own checks on this draft: the place built as `draft.walk.network` builds it (cached by the place
    files' key), then every check of `tools/places/check.py` on that plugin. The same code as `check <place_id>` on
    the real build, so a draft that passes here passes there."""
    from tools.places import check as C
    from tools.places.draft import walk
    ctx, bad = walk.network(place_id, places)
    if ctx is None:
        return bad
    res = C.run(ctx)
    summary["network"] = ctx.get("streets")
    summary["build_check"] = {k: len(v) for k, v in res.items()}
    full = walk.CHECK_OUT / "shards" / place_id / "check_failures"
    full.mkdir(parents=True, exist_ok=True)
    for k, v in res.items():
        (full / f"{k}.txt").write_text("".join(f"{f}\n" for f in v))
    return bad + [f"check {k}: {f}" for k, v in res.items() for f in v] + unsettled(ctx, places / place_id)


def unsettled(ctx: dict, pdir: Path) -> list[str]:
    """The streets are settled on the built mesh: mending them again (`walk.mend`, the join's own pass) re-lays
    nothing."""
    from tools.places import check as C
    from tools.places.draft import walk
    W = walk.Walkable(ctx, *C.surfaces(ctx))
    bad = []
    for p in io.read_jsonl(pdir / "paths.jsonl") if (pdir / "paths.jsonl").exists() else []:
        n = walk.mend(dict(p, points=[list(q) for q in p["points"]]), W)
        if n is None or n:
            bad.append(f"street {p['id']} is not settled on the built mesh: a second mend "
                       f"{'finds no way for a stretch' if n is None else f're-lays {n} stretch(es)'}")
    summary["second_mend"] = len(bad)
    return bad


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python -m tools.places draft check <place_id>")
        return 2
    bad = check(argv[0]) + round_trip(argv[0]) + build_check(argv[0])
    for b in bad[:200]:
        print("FAIL", b)
    if len(bad) > 200:
        print(f"... and {len(bad) - 200} more")
    print("measures:", json.dumps(summary))
    print(f"draft check {argv[0]}: {'PASS' if not bad else f'{len(bad)} problems'}")
    return 0 if not bad else 1

