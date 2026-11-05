"""The BM&V census (phase 1): read Black Marsh.esm (and the masters it points at, for the names of their forms) into
the bmv_* tables of the story data, then group its cells into settlements. Only derived values are written: form keys,
editor ids, names, coordinates, counts and links. Rerunning replaces every bmv_* row (the mapping tables are kept),
so an interrupted run is simply run again.

    python3 -m tools.argonia_world.bmv_census build  [--esm PATH] [--masters DIR]
    python3 -m tools.argonia_world.bmv_census verify [--esm PATH]    # recount from the ESM and compare with the db
"""
from __future__ import annotations

import argparse
import math
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

from tools.argonia_world import db, esm

ESM = Path.home() / ".argonia/stack/MO2/mods/bmv/Black Marsh.esm"
MASTERS = Path.home() / "games/skyrimse/Data"
CELL_GROUPS = (6, 8, 9, 10)          # cell children, persistent, temporary, visible-distant
GRID = 4096.0
ACTOR_NPC = "013794:Skyrim.esm"      # the ActorTypeNPC keyword: a race of people, not creatures
DISABLED = 0x800
TABLES = ["bmv_interior_exit", "bmv_settlement_cell", "bmv_settlement", "bmv_door", "bmv_placement", "bmv_npc_faction", "bmv_quest",
          "bmv_npc", "bmv_faction", "bmv_class", "bmv_race", "bmv_cell", "bmv_location", "bmv_worldspace"]
MAPS = ["place_bmv", "npc_bmv", "faction_bmv"]   # ours, kept across a rebuild
LINK_GRID = 2       # named exterior cells this close (Chebyshev, in squares) are one settlement
PREFIX_GRID = 5     # ... or this close when their editor ids share a first word (Blackrose, Blackrosemarket)
# named cells that stay their own settlement however close: Hereguard Plantation is "one of the few Breton settlements
# outside Lilmoth", not a ward of it (story/lore/regions/murkmire.md:71; place.mercantile-coast.hereguard-plantation)
STANDALONE = {"HereguardPlantation"}
AREA_GRID = 8       # a square with content joins the nearest settlement this close
DOOR_GRID = 2       # an interior joins the settlement whose cells lie this close to its exterior door


def _u32(d: bytes, o: int = 0) -> int:
    return struct.unpack_from("<I", d, o)[0]


def cell_of(r: esm.Record) -> int | None:
    return next((lab for t, lab in reversed(r.parents) if t in CELL_GROUPS), None)


def world_of(r: esm.Record) -> int | None:
    return next((lab for t, lab in r.parents if t == 1), None)


def is_interior(c: esm.Record) -> bool:
    d = c.sub("DATA")
    return bool(d and d[0] & 1)


def grid_of(x: float, y: float) -> tuple[int, int]:
    return math.floor(x / GRID), math.floor(y / GRID)


def pos(r: esm.Record) -> tuple[float, float, float]:
    return struct.unpack_from("<fff", r.sub("DATA"))


def read(path: Path) -> esm.Plugin:
    return esm.Plugin.read(path)


class Resolver:
    """The winning record of a form key: Black Marsh.esm's when it has one, else the last master's."""

    def __init__(self, p: esm.Plugin, masters: Path, sigs: set[str]):
        self.win: dict[str, esm.Record] = {}
        for m in p.masters:
            mp = masters / m
            if mp.exists():
                for r in esm.Plugin.read(mp, sigs).records():
                    if r.sig in sigs:
                        self.win[r.key] = r
        for r in p.records():
            if r.sig in sigs:
                self.win[r.key] = r

    def row(self, key: str, **extra) -> dict:
        r = self.win.get(key)
        owner = r.plugin.name if r else key.split(":", 1)[1]
        return {"id": key, "editor_id": r.edid if r else None, "name": r.name if r else None, "defined_in": owner,
                **extra}


def census(p: esm.Plugin, masters: Path) -> dict[str, list[dict]]:
    res = Resolver(p, masters, {"RACE", "CLAS", "FACT", "NPC_", "LVLN", "LCTN"})
    T: dict[str, list[dict]] = defaultdict(list)
    T["bmv_worldspace"] = [{"id": r.key, "editor_id": r.edid, "name": r.name, "defined_in": p.name}
                           for r in p.records("WRLD")]
    ws_keys = {r.formid: r.key for r in p.records("WRLD")}

    cells = {r.formid: r for r in p.records("CELL")}
    refs_in = Counter(cell_of(r) for r in p.records() if r.sig in ("REFR", "ACHR", "PGRE"))
    nav = {cell_of(r) for r in p.records("NAVM")}
    locs = {r.key: res.row(r.key, parent=r.ref("PNAM"), in_bmv=True) for r in p.records("LCTN")}
    for c in cells.values():
        k = c.ref("XLCN")
        if k and k not in locs:
            loc = res.win.get(k)
            locs[k] = res.row(k, parent=loc.ref("PNAM") if loc else None, in_bmv=False)
    T["bmv_location"] = list(locs.values())
    for fid, c in cells.items():
        inter = is_interior(c)
        g = c.sub("XCLC")
        persistent = not inter and (bool(c.flags & 0x400) or c.parents[-1][0] == 0 or g is None)
        gx, gy = struct.unpack_from("<ii", g) if (g and not inter and not persistent) else (None, None)
        T["bmv_cell"].append({
            "id": c.key, "editor_id": c.edid, "name": c.name, "interior": inter,
            "worldspace": None if inter else ws_keys[world_of(c)], "grid_x": gx, "grid_y": gy,
            "persistent": persistent, "location": c.ref("XLCN"), "has_navmesh": bool(fid in nav),
            "refs": refs_in[fid], "defined_in": p.name if c.own else c.key.split(":", 1)[1]})

    # actors: every NPC_ in the file and every base its ACHRs place
    achrs = p.records("ACHR")
    bases = {r.key for r in p.records("NPC_")} | {a.ref("NAME") for a in achrs}
    races, classes, facs = set(), set(), {r.key for r in p.records("FACT")}
    for k in sorted(bases):
        r = res.win.get(k)
        if r is None:
            raise SystemExit(f"actor base {k} is in no plugin read")
        row = res.row(k, record=r.sig, race=None, **{"class": None}, sex=None, template=r.ref("TPLT"),
                      template_flags=None, person=None, in_bmv=bool(r.plugin is p))
        if r.sig == "NPC_":
            row["race"], row["class"] = r.ref("RNAM"), r.ref("CNAM")
            row["sex"] = "female" if _u32(r.sub("ACBS")) & 1 else "male"
            row["template_flags"] = struct.unpack_from("<H", r.sub("ACBS"), 18)[0] if row["template"] else None
            race = res.win.get(row["race"])
            kw = race.sub("KWDA") if race else None
            row["person"] = bool(kw and any(race.plugin.form_key(_u32(kw, i)) == ACTOR_NPC
                                            for i in range(0, len(kw) - 3, 4)))
            races |= {row["race"]} - {None}
            classes |= {row["class"]} - {None}
            for s in r.all("SNAM"):
                fk = p.form_key(_u32(s)) if r.plugin is p else r.plugin.form_key(_u32(s))
                facs.add(fk)
                if r.plugin is p:
                    T["bmv_npc_faction"].append({"npc": k, "faction": fk, "rank": struct.unpack_from("<b", s, 4)[0]})
        T["bmv_npc"].append(row)
    T["bmv_race"] = [res.row(k) for k in sorted(races)]
    T["bmv_class"] = [res.row(k) for k in sorted(classes)]
    T["bmv_faction"] = [res.row(k, in_bmv=bool(k in {r.key for r in p.records("FACT")})) for k in sorted(facs)]

    def where(r):
        x, y, z = pos(r)
        c = cells[cell_of(r)]
        gx, gy = (None, None) if is_interior(c) else grid_of(x, y)
        return {"id": r.key, "cell": c.key, "x": round(x, 1), "y": round(y, 1), "z": round(z, 1),
                "grid_x": gx, "grid_y": gy}

    T["bmv_placement"] = [{**where(a), "npc": a.ref("NAME"), "disabled": bool(a.flags & DISABLED),
                           "enable_parent": a.ref("XESP")} for a in achrs]
    for q in p.records("QUST"):
        d = q.sub("DNAM")
        T["bmv_quest"].append({"id": q.key, "editor_id": q.edid, "name": q.name,
                               "start_game_enabled": bool(d[0] & 1), "priority": d[2],
                               "defined_in": p.name if q.own else q.key.split(":", 1)[1]})
    doors = [r for r in p.records("REFR") if r.sub("XTEL")]
    dkeys = {r.key for r in doors}
    at = {(c["worldspace"], c["grid_x"], c["grid_y"]): c["id"] for c in T["bmv_cell"] if c["grid_x"] is not None}
    for r in doors:
        t = p.form_key(_u32(r.sub("XTEL")))
        wh = where(r)
        ws = None if is_interior(cells[cell_of(r)]) else ws_keys[world_of(cells[cell_of(r)])]
        T["bmv_door"].append({**wh, "worldspace": ws, "ext_cell": at.get((ws, wh["grid_x"], wh["grid_y"])),
                              "target": t if t in dkeys else None, "target_elsewhere": None if t in dkeys else t})
    settle(T)
    return dict(T)


def _cheb(a, b) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def settle(T: dict[str, list[dict]]) -> None:
    """Group cells: named exterior cells clustered by distance, their neighbour squares, and the interiors whose load
    doors lead out near them; interiors that lead out elsewhere form a site at their exterior door."""
    cells = {c["id"]: c for c in T["bmv_cell"]}
    named = [c for c in T["bmv_cell"] if not c["interior"] and c["grid_x"] is not None and c["editor_id"]
             and c["worldspace"].endswith("Black Marsh.esm")]
    parent = {c["id"]: c["id"] for c in named}

    def find(k):
        while parent[k] != k:
            k = parent[k]
        return k
    for i, a in enumerate(named):
        for b in named[i + 1:]:
            if a["worldspace"] != b["worldspace"]:
                continue
            d = _cheb((a["grid_x"], a["grid_y"]), (b["grid_x"], b["grid_y"]))
            same = a["editor_id"].lower()[:6] == b["editor_id"].lower()[:6]
            if {a["editor_id"], b["editor_id"]} & STANDALONE and not same:
                continue
            if d <= LINK_GRID or (same and d <= PREFIX_GRID):
                parent[find(a["id"])] = find(b["id"])
    clusters = defaultdict(list)
    for c in named:
        clusters[find(c["id"])].append(c)

    member: dict[str, tuple[str, str]] = {}
    squares: dict[str, list] = {}
    for group in clusters.values():
        group.sort(key=lambda c: (len(c["editor_id"]), c["editor_id"]))
        # the anchor whose editor id begins the most others (Blackrose: Blackrosemarket, Blackrosegate), else the
        # busiest
        head = max(group, key=lambda c: (sum(o["editor_id"].lower().startswith(c["editor_id"].lower())
                                             for o in group), c["refs"]))
        sid = "bmv." + head["editor_id"].lower()
        gx = round(sum(c["grid_x"] for c in group) / len(group))
        gy = round(sum(c["grid_y"] for c in group) / len(group))
        others = ", ".join(c["editor_id"] for c in group if c is not head)
        T["bmv_settlement"].append({
            "id": sid, "name": head["editor_id"], "kind": "settlement", "worldspace": head["worldspace"],
            "grid_x": gx, "grid_y": gy,
            "why": f"named exterior cell {head['editor_id']}" + (f" with {others} within {PREFIX_GRID} squares"
                                                                   if others else "")})
        squares[sid] = [(c["worldspace"], c["grid_x"], c["grid_y"]) for c in group]
        for c in group:
            member[c["id"]] = (sid, "anchor")
    # neighbour squares: the nearest settlement's anchor within one square
    anchors = [(sid, sq) for sid, sqs in squares.items() for sq in sqs]
    for c in T["bmv_cell"]:
        if c["interior"] or c["grid_x"] is None or c["id"] in member:
            continue
        near = [(_cheb(sq[1:], (c["grid_x"], c["grid_y"])), sid) for sid, sq in anchors if sq[0] == c["worldspace"]]
        near = [n for n in near if n[0] <= 1]
        if near:
            member[c["id"]] = (min(near)[1], "neighbour")
    # area squares: any other square with content, to the nearest settlement's anchor within AREA_GRID
    for c in T["bmv_cell"]:
        if c["interior"] or c["grid_x"] is None or c["id"] in member or not c["refs"]:
            continue
        near = [(_cheb(sq[1:], (c["grid_x"], c["grid_y"])), sid) for sid, sq in anchors if sq[0] == c["worldspace"]]
        near = [n for n in near if n[0] <= AREA_GRID]
        if near:
            member[c["id"]] = (min(near)[1], "area")
    # interiors through load doors
    doors = {d["id"]: d for d in T["bmv_door"]}
    edges = defaultdict(set)
    exits = defaultdict(set)          # interior cell -> exterior door ids it reaches directly
    for d in doors.values():
        t = doors.get(d["target"]) if d["target"] else None
        if not t:
            continue
        a, b = cells[d["cell"]], cells[t["cell"]]
        if a["interior"] and b["interior"]:
            edges[a["id"]].add(b["id"])
        elif a["interior"]:
            exits[a["id"]].add(t["id"])
    sites = {}
    for c in sorted((c for c in T["bmv_cell"] if c["interior"]), key=lambda c: c["id"]):
        seen, todo, outs = {c["id"]}, [c["id"]], set()
        while todo:
            k = todo.pop()
            outs |= exits[k]
            for n in edges[k] - seen:
                seen.add(n)
                todo.append(n)
        if not outs:
            continue
        # its exits: a ship has one per port, a shared house interior one per house door
        best = []
        for o in sorted(outs):
            out = doors[o]
            ws = cells[out["cell"]]["worldspace"]
            sq = (out["grid_x"], out["grid_y"])
            near = sorted((_cheb(s[1:], sq), sid) for sid, ss in squares.items() for s in ss if s[0] == ws)
            best.append((near[0] if near else (10 ** 6, ""), o, ws, sq, near))
        for b in best:
            T["bmv_interior_exit"].append({"interior": c["id"], "door": b[1],
                                           "settlement": b[0][1] if b[0][0] <= DOOR_GRID else None})
        votes = Counter(b[0][1] for b in best if b[0][0] <= DOOR_GRID)
        if votes:       # the settlement most of its exits lead to (a shared house interior behind many doors)
            top = max(votes.values())
            pick = min(b for b in best if b[0][0] <= DOOR_GRID and votes[b[0][1]] == top)
        else:
            pick = min(best)
        _, _, ws, sq, near = pick
        if near and near[0][0] <= DOOR_GRID:
            member[c["id"]] = (near[0][1], "interior")
            continue
        sk = (ws, sq)
        if sk not in sites:
            sid = f"bmv.site.{(c['editor_id'] or c['id']).lower()}"
            sites[sk] = sid
            T["bmv_settlement"].append({
                "id": sid, "name": c["name"] or c["editor_id"] or c["id"], "kind": "site", "worldspace": ws,
                "grid_x": sq[0], "grid_y": sq[1],
                "why": f"interiors whose load doors lead out at {ws.split(':')[0]} square {sq}, "
                       f"no named exterior cell within {DOOR_GRID}"})
        member[c["id"]] = (sites[sk], "interior")
    T["bmv_settlement_cell"] = [{"settlement": s, "cell": k, "role": r} for k, (s, r) in member.items()]


def build(esm_path: Path, masters: Path) -> dict[str, int]:
    T = census(read(esm_path), masters)
    w = db.load(strict=False)      # a schema change leaves the old bmv rows unloadable; they are replaced here
    kept = {t: [dict(r) for r in w.query(f'SELECT * FROM "{t}"')] for t in MAPS}
    w._begin()
    for t in MAPS + TABLES:
        w.con.execute(f'DELETE FROM "{t}"')
        w.dirty.add(t)
    for t in reversed(TABLES):
        w.insert_many(t, T.get(t, []))
    for t in MAPS:
        w.insert_many(t, kept[t])
    errs = w.save()
    if errs:
        raise SystemExit("\n".join(errs))
    return {t: len(T.get(t, [])) for t in reversed(TABLES)}


def verify(esm_path: Path) -> list[str]:
    """Recount straight from the file (a different path from census()) and compare with the saved rows."""
    raw = Counter()
    data = esm_path.read_bytes()
    p = esm.Plugin.read(esm_path)
    for r in p.records():
        raw[r.sig] += 1
        if r.sig == "CELL" and r.flags & 0x400:
            raw["persistent"] += 1
        if r.sig == "REFR" and r.sub("XTEL"):
            raw["door"] += 1
    raw["placed"] = sum(1 for r in p.records() if r.sig in ("REFR", "ACHR", "PGRE"))
    w = db.load()
    n = lambda sql: w.values(sql)[0]  # noqa: E731
    want = {
        "bmv_worldspace": raw["WRLD"], "bmv_cell": raw["CELL"], "bmv_quest": raw["QUST"],
        "bmv_placement": raw["ACHR"], "bmv_door": raw["door"], "bmv_npc in file": raw["NPC_"],
        "refs in cells": raw["placed"], "persistent cells": raw["persistent"],
        "LCTN in file": raw["LCTN"], "FACT in file": raw["FACT"],
        "cell signature in bytes": data.count(b"CELL") >= raw["CELL"] and raw["CELL"],
    }
    got = {
        "bmv_worldspace": n("SELECT count(*) FROM bmv_worldspace"), "bmv_cell": n("SELECT count(*) FROM bmv_cell"),
        "bmv_quest": n("SELECT count(*) FROM bmv_quest"), "bmv_placement": n("SELECT count(*) FROM bmv_placement"),
        "bmv_door": n("SELECT count(*) FROM bmv_door"),
        "bmv_npc in file": n("SELECT count(*) FROM bmv_npc WHERE in_bmv = 1 AND record = 'NPC_'"),
        "refs in cells": n("SELECT sum(refs) FROM bmv_cell"),
        "persistent cells": n("SELECT count(*) FROM bmv_cell WHERE persistent"),
        "LCTN in file": n("SELECT count(*) FROM bmv_location WHERE in_bmv = 1"),
        "FACT in file": n("SELECT count(*) FROM bmv_faction WHERE in_bmv = 1"),
        "cell signature in bytes": raw["CELL"],
    }
    return [f"{k}: esm {want[k]} db {got[k]}" for k in want if want[k] != got[k]]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=["build", "verify"])
    ap.add_argument("--esm", type=Path, default=ESM)
    ap.add_argument("--masters", type=Path, default=MASTERS)
    a = ap.parse_args(argv)
    if a.cmd == "build":
        for t, k in build(a.esm, a.masters).items():
            print(f"{t}\t{k}")
        return 0
    bad = verify(a.esm)
    print("\n".join(bad) or "census matches the ESM")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
