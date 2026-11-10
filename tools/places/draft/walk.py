"""The walkable network of a drafted place, by the build's own navmesh, and the joins the draft lays across it.

`network` builds the place (`build <place_id>` into out/places/draft_check, cached by the place files' key, so an
unchanged draft is not rebuilt) and loads it exactly as `check` does; `islands` lists each door's exterior navmesh
that is not on the place's main walkable network; `join` lays walkway pieces from each such island to the nearest
point of the network at a walkable height and reseats, until no door is on an island (or no join is possible).
`draft check` and `check` read the same network, so what `join` makes walkable the build's check finds walkable.
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np

from tools.places.draft import io, overlap
from tools.places.draft import paths as paths_mod

CHECK_OUT = io.ROOT / "out" / "places" / "draft_check"
LEVEL = 48.0         # units of height a join may leave between its two ends (a step the navmesh climbs)
JOIN_ROUNDS = 6
TRIES = 200        # joins tried per island, shortest first, for one no house or ship stands across


def build(place_id: str, places: Path = io.PLACES, out: Path = CHECK_OUT) -> list[str]:
    """`build <place_id> --keep-going` into `out`: the build's problems, or the failure."""
    p = subprocess.run([sys.executable, "-m", "tools.places", "build", place_id, "--keep-going", "--places-dir", str(places),
                        "--out", str(out)], cwd=io.ROOT, capture_output=True, text=True)
    lines = [x.strip() for x in (p.stdout + p.stderr).splitlines() if x.strip()]
    bad = [f"build: {x}" for x in lines if x.startswith(f"{place_id}: ")]
    if p.returncode != 0:
        bad += [f"build failed ({p.returncode}): {x}" for x in lines[-10:]]
    return bad


def network(place_id: str, places: Path = io.PLACES, out: Path = CHECK_OUT) -> tuple[dict | None, list[str]]:
    """The built place as `check` loads it (its context dict), and the build's problems."""
    bad = build(place_id, places, out)
    if any(b.startswith("build failed") for b in bad):
        return None, bad
    from tools.places import check as C
    ctx = C.load(place_id, out)
    ctx["place_dir"] = places / place_id
    return ctx, bad


def islands(ctx: dict) -> tuple[dict, np.ndarray, np.ndarray]:
    """({door id: island triangle centres}, every exterior triangle centre, the main network's mask over them)."""
    from tools.places import check as C
    comp = C.components(ctx["navs"], C.door_pairs(ctx))
    sizes = Counter(comp.values())
    main = max(sizes, key=sizes.get)
    keys, pts = [], []
    for n in ctx["navs"].values():
        if n.space == "exterior":
            for i, t in enumerate(n.tri):
                keys.append(comp[(n.fk, i)])
                pts.append(n.verts[t].mean(axis=0))
    P = np.asarray(pts, float)
    K = np.asarray([hash(k) for k in keys])
    m = C.mine(ctx)
    out: dict = {}
    for n in ctx["navs"].values():
        if n.space != "exterior" or getattr(n, "world", False):
            continue
        for ti, d in n.doors:
            c = comp[(n.fk, ti)]
            row = m["rows"].get(d)
            if c != main and row is not None and row["id"] not in out:
                out[row["id"]] = P[K == hash(c)]
    return out, P, K == hash(main)


def dry(pts: np.ndarray, G) -> np.ndarray:
    """The triangle centres one walks on out of the water (a seabed under our water is no street)."""
    keep = []
    for p in pts:
        w = G.water(float(p[0]), float(p[1]))
        keep.append(w is None or p[2] >= w - 8)
    return pts[np.asarray(keep, bool)] if len(pts) else pts


def pairs(isl: np.ndarray, net: np.ndarray) -> list[tuple[float, np.ndarray, np.ndarray]]:
    """Level joins from an island to the network (ends within LEVEL of each other), shortest first: [(plan length, from, to)], one per
    island point (its nearest such network point)."""
    out = []
    for p in isl:
        d = np.linalg.norm(net[:, :2] - p[:2], axis=1)
        ok = np.abs(net[:, 2] - p[2]) <= LEVEL  # flat pieces: a join never climbs more than a step
        if ok.any():
            j = int(np.argmin(np.where(ok, d, np.inf)))
            out.append((float(d[j]), p, net[j]))
    return sorted(out, key=lambda t: t[0])


def walk_base(rows: list[dict], bases: dict) -> str | None:
    """The walkway piece the place's own joins and bridges use: the commonest the draft already laid, else the
    commonest walkway piece of the place."""
    laid = Counter(r["base"] for r in rows if not r.get("src") and r.get("kind") == "building" and r.get("why"))
    if laid:
        return sorted(laid, key=lambda b: (-laid[b], b))[0]
    ways = Counter(r["base"] for r in rows if r.get("kind") == "building"
                   and paths_mod.WALKWAY.search(str((bases.get(r["base"]) or {}).get("model", ""))))
    return sorted(ways, key=lambda b: (-ways[b], b))[0] if ways else None


def piece_length(bases: dict, base: str) -> float:
    bb = bases[base]["bounds"]
    return max(64.0, bb[1][1] - bb[0][1] - 16)


def lay(place_id: str, door_id: str, a, b, base: str, rows: list[dict], bases: dict, G) -> list[dict]:
    """Walkway pieces end to end from a to b ([x, y, z] each), their decks (the top surface of the mesh, geom.walk) on
    the line between the two heights."""
    from tools.places.draft import geom
    top = geom.walk(bases[base]) or 0.0
    length = piece_length(bases, base)
    near = [r for r in rows if r.get("kind") in overlap.SOLID and math.dist(r["pos"][:2], a[:2]) < math.dist(a[:2], b[:2]) + 4096]
    run = math.dist(a[:2], b[:2])
    n = max(1, math.ceil(run / length))
    yaw = math.atan2(b[0] - a[0], b[1] - a[1]) % (2 * math.pi)
    out = []
    for j in range(n):
        t = (j + 0.5) / n if run > length else 0.5
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        deck = float(a[2] + (b[2] - a[2]) * t)
        cand = {"id": io.mint(place_id, "join", door_id, str(j)), "base": base, "kind": "building",
                "pos": [round(x, 2), round(y, 2), round(deck - top, 2)], "rot": [0.0, 0.0, round(yaw, 5)], "scale": 1.0,
                "layer": "place", "flags": [], "src": None, "walk": top,
                "seat": {"mode": "free"},
                "why": f"joins door {door_id}'s walkable island to the town's network"}
        hit = [o for o in near if overlap.inside(o["pos"], cand, bases) or overlap.inside(cand["pos"], o, bases)]
        ways = [o for o in hit if paths_mod.WALKWAY.search(str((bases.get(o["base"]) or {}).get("model", "")))]
        if len(hit) > 1 or (hit and not ways):
            continue  # a door, a house or two pieces stand there: the join leaves that piece out
        if ways:
            cand["seat"]["on"] = ways[0]["id"]  # it rests on the walkway it continues
        out.append(cand)
    return out


def cut(place_id: str, door_ids: list[str], rows: list[dict], pdir: Path, log=print) -> int:
    """A door left on an island no level join reaches (a ship's hatch with no way aboard in the source) leads
    nowhere one can walk to: its room is left out with it, with the reason in the ledger, unless someone lives or
    works in that room (then it stays, and `draft check` lists the island). Returns the rooms left out."""
    import shutil
    used = set()
    for p in io.read_jsonl(pdir / "people.jsonl") if (pdir / "people.jsonl").exists() else []:
        used.add(p.get("home"))
        for k in ("bed", "work"):
            used.add((p.get(k) or {}).get("space"))
        used.update(s.get("space") for s in p.get("stops") or [] if isinstance(s, dict))
    by_id = {r["id"]: r for r in rows}
    gone, ledger = set(), []
    for did in door_ids:
        sid = ((by_id.get(did) or {}).get("door") or {}).get("to_space")
        sdir = pdir / "spaces" / str(sid)
        if not sid or sid == "exterior" or sid in used or not sdir.is_dir():
            continue
        sp = json.loads((sdir / "space.json").read_text())
        if sp.get("door_from") != did:
            continue   # a room with another way in stays
        why = (f"its only door {did} stands on a walkable island with no way to the town (the source gives no "
               f"way aboard) and nobody lives or works in it")
        gone.add(did)
        ledger.append({"src": by_id[did].get("src") or did, "space": "exterior", "status": "dropped", "why": why})
        ledger.append({"src": "*", "space": sid, "status": "dropped", "why": why})
        shutil.rmtree(sdir)
        log(f"join {place_id}: left out room {sid} and its door {did}: no way to it")
    if gone:
        dropped = {r["space"] for r in ledger if r["src"] == "*"}
        srcs = {r["src"] for r in ledger if r["src"] != "*"}
        # the links that led to a door left out go with it, and the walkway pieces laid to carry them
        pj, carried = pdir / "paths.jsonl", ()
        if pj.exists():
            paths = io.read_jsonl(pj)
            dead = [p for p in paths if p.get("from") in srcs or p.get("to") in srcs]
            if dead:
                carried = tuple(f"carries street {p['id'].rsplit('.', 1)[-1]} " for p in dead)
                io.write_jsonl(pj, [p for p in paths if p not in dead])
        io.write_jsonl(pdir / "spaces" / "exterior" / "refs.jsonl",
                       [r for r in rows if r["id"] not in gone and not str(r.get("why", "")).startswith(carried or ("\0",))])
        old = [r for r in io.read_jsonl(pdir / "ledger.jsonl") if r.get("space") not in dropped
               and not (r.get("space") == "exterior" and r.get("src") in srcs)]
        io.write_jsonl(pdir / "ledger.jsonl", old + ledger)
    return len(gone)


def rehome(place_id: str, ctx: dict, bases: dict, src, pdir: Path, log=print) -> int:
    """A person whose bed outdoors (a camp bed) stands where the town's walkable network does not reach (a tent shut
    in by blocks) sleeps instead in a free bed of a home: the first room, by name, with a bed nobody has (never the inn's, whose beds are let); with none free, the last resident (residents only fill the beds left over) gives up theirs. Returns the
    people moved."""
    from tools.places import check as C
    from tools.places.draft import interiors
    comp = C.components(ctx["navs"], C.door_pairs(ctx))
    main = Counter(comp.values()).most_common(1)[0][0]
    rows = {r["id"]: r for r in io.read_jsonl(pdir / "spaces" / "exterior" / "refs.jsonl")}

    def reached(pos) -> bool:
        for n in ctx["navs"].values():
            if n.space == "exterior":
                t = n.tri_at(pos)
                if t >= 0:
                    return comp[(n.fk, t)] == main   # the first mesh holding it, as `check` finds a stop's
        return False
    ppl = io.read_jsonl(pdir / "people.jsonl")
    inns = {(p.get("work") or {}).get("space") for p in ppl
            if any((g.get("give_kind_id") or g.get("kind")) == "inn-room" for g in p.get("services") or [])}
    taken = Counter(((p.get("bed") or {}).get("space"), (p.get("bed") or {}).get("ref")) for p in ppl)
    free = []
    for sdir in sorted((pdir / "spaces").iterdir()):
        sp = json.loads((sdir / "space.json").read_text()) if (sdir / "space.json").exists() else None
        if not sp or sp["space_id"] == "exterior" or sp.get("parent") != "exterior" or sp["space_id"] in inns:
            continue
        src_space = str(sp.get("copy_of") or "").split("/")[-1]
        if src_space not in src.spaces:
            continue
        for b in interiors.beds_in(src.spaces[src_space].refs, bases, sp.get("room"), sp.get("copy_of")):
            free += [(sp["space_id"], b["ref"])] * max(0, b["sleeps"] - taken[(sp["space_id"], b["ref"])])
    moved = 0
    for p in ppl:
        bed = p.get("bed") or {}
        r = rows.get(bed.get("ref")) if bed.get("space") == "exterior" else None
        if r is None or reached(r["pos"]):
            continue
        if not free:   # residents only fill the beds left over: the last of them gives up a bed
            res = sorted((q for q in ppl if q.get("role") == "resident" and not q.get("_gone")
                          and (q.get("bed") or {}).get("space") not in (None, "exterior", *inns)), key=lambda q: q["id"])
            if not res:
                continue
            res[-1]["_gone"] = True
            free.append((res[-1]["bed"]["space"], res[-1]["bed"]["ref"]))
            log(f"join {place_id}: resident {res[-1]['id']} left out: a guard needs the bed")
        sid, ref = free.pop(0)
        log(f"join {place_id}: {p['id']} sleeps in {sid}: the camp bed {r['id']} is off the town's walkable network")
        p["bed"] = {**bed, "space": sid, "ref": ref}
        p["home"] = sid
        for st in p.get("routine") or []:
            if st.get("at") == bed:
                st["at"] = p["bed"]
        moved += 1
    if moved:
        io.write_jsonl(pdir / "people.jsonl", [q for q in ppl if not q.get("_gone")])
    return moved


def join(place_id: str, places: Path = io.PLACES, out: Path = CHECK_OUT, log=print) -> int:
    """Lay joins until no door's navmesh is an island; the number of pieces laid."""
    pdir = places / place_id
    place = json.loads((pdir / "place.json").read_text())
    src = io.load(f"src.{place['source_id']}")
    grd = io.load(f"ground.{place_id}")
    bases = io.place_bases(src, grd, place)
    from tools.places.seat import Ground
    G = Ground.load(grd.path)
    laid = 0
    for _ in range(JOIN_ROUNDS):
        ctx, bad = network(place_id, places, out)
        if ctx is None:
            log(f"join {place_id}: the build failed: {bad[-1:]}")
            return laid
        isl, P, main = islands(ctx)
        if rehome(place_id, ctx, bases, src, pdir, log):
            laid += 1   # people moved: the place is rebuilt and checked again
            continue
        if not isl:
            break
        rows = io.read_jsonl(pdir / "spaces" / "exterior" / "refs.jsonl")
        base = walk_base(rows, bases)
        if base is None:
            log(f"join {place_id}: no walkway piece to join islands with")
            return laid
        have = {r["id"] for r in rows}
        # the island nearest the network is joined first; the next round sees it as the network
        net = dry(P[main], G)
        new, said = [], None
        for door_id, pts in sorted(isl.items()):
            for d, a, b in pairs(dry(pts, G), net)[:TRIES]:
                n = max(1, math.ceil(math.dist(a[:2], b[:2]) / piece_length(bases, base)))
                got = [r for r in lay(place_id, door_id, list(a), list(b), base, rows, bases, G) if r["id"] not in have]
                if len(got) == n and (not new or d < said[1]):
                    new, said = got, (door_id, d, a, b)
                    break
        if not new:
            log(f"join {place_id}: no island ({', '.join(sorted(isl))}) has a clear walkable way to the network")
            cut(place_id, sorted(isl), rows, pdir, log)
            break
        door_id, d, a, b = said
        log(f"join {place_id}: door {door_id}: {len(new)} pieces over {d:.0f} units, z {a[2]:.0f} -> {b[2]:.0f}")
        if not new:
            break
        laid += len(new)
        io.write_jsonl(pdir / "spaces" / "exterior" / "refs.jsonl", rows + new)
    return laid
