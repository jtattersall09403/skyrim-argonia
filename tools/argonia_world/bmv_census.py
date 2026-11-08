"""The BM&V census (phase 1): read BM&V's four plugins in load order (BosmerArmorMATY743.esm, Black Marsh.esm, Black
Marsh North.esp, Valenwood.esp; the masters they point at give their forms' names) into the bmv_* tables of the story
data, resolving overrides as the engine does (the last plugin's version of a form wins; a winner flagged deleted
removes it), then group the cells into settlements. Only derived values are written: form keys, editor ids, names,
coordinates, counts and links. Rerunning replaces every bmv_* row (the mapping tables are kept), so an interrupted run
is simply run again.

    python3 -m tools.argonia_world.bmv_census build  [--dir DIR] [--masters DIR]
    python3 -m tools.argonia_world.bmv_census verify [--dir DIR]   # the completeness proof: per plugin, per type
"""
from __future__ import annotations

import argparse
import math
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

from tools.argonia_world import db, esm

DIR = Path.home() / ".argonia/stack/MO2/mods/bmv"
PLUGINS = ("BosmerArmorMATY743.esm", "Black Marsh.esm", "Black Marsh North.esp", "Valenwood.esp")
ESM = DIR / "Black Marsh.esm"
MASTERS = Path.home() / "games/skyrimse/Data"
MASTER_FILES = ("Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm")
CELL_GROUPS = (6, 8, 9, 10)          # cell children, persistent, temporary, visible-distant
GRID = 4096.0
KM2_PER_CELL = (GRID / 70.0 / 1000.0) ** 2   # 70 units a metre (Bethesda's scale): a cell is 58.5 m a side
ACTOR_NPC = "013794:Skyrim.esm"      # the ActorTypeNPC keyword: a race of people, not creatures
DISABLED = 0x800
DELETED = 0x20
MAPMARKER = "000010:Skyrim.esm"
TABLES = ["bmv_book", "bmv_map_marker", "bmv_interior_exit", "bmv_settlement_cell", "bmv_settlement", "bmv_door",
          "bmv_placement", "bmv_npc_faction", "bmv_quest", "bmv_npc", "bmv_faction", "bmv_class", "bmv_race",
          "bmv_cell", "bmv_location", "bmv_worldspace"]
MAPS = ["place_bmv", "npc_bmv", "faction_bmv", "bmv_shell"]   # kept across a rebuild (bmv_shell: rerun its build)
OLD_WORLDS = ("23D689:Black Marsh.esm", "0D6960:Black Marsh.esm")   # their settlements keep the bare bmv.<edid> ids
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


class Load:
    """BM&V's plugins in load order. `chain[key]` is every BM&V record of a form, in order; the last one wins."""

    def __init__(self, d: Path = DIR, names=PLUGINS):
        self.plugins = [esm.Plugin.read(d / n) for n in names]
        self.names = [p.name for p in self.plugins]
        self.chain: dict[str, list[esm.Record]] = defaultdict(list)
        for p in self.plugins:
            for r in p.records():
                self.chain[r.key].append(r)
        self.deleted = {k for k, rs in self.chain.items() if rs[-1].flags & DELETED}

    def win(self, key: str) -> esm.Record | None:
        rs = self.chain.get(key)
        return rs[-1] if rs and key not in self.deleted else None

    def live(self, *sigs: str) -> list[esm.Record]:
        return [rs[-1] for k, rs in self.chain.items() if rs[-1].sig in sigs and k not in self.deleted]

    def meta(self, key: str) -> dict:
        rs = self.chain.get(key)
        if not rs:
            return {"plugin": None, "overridden_by": None}
        return {"plugin": rs[0].plugin.name, "overridden_by": " ".join(r.plugin.name for r in rs[1:]) or None}

    @staticmethod
    def cell_key(r: esm.Record) -> str | None:
        c = cell_of(r)
        return r.plugin.form_key(c) if c is not None else None

    @staticmethod
    def world_key(r: esm.Record) -> str | None:
        w = world_of(r)
        return r.plugin.form_key(w) if w is not None else None


class Resolver:
    """The winning record of a form key over the masters then BM&V's plugins (names, races, keywords)."""

    def __init__(self, L: Load, masters: Path, sigs: set[str]):
        self.win: dict[str, esm.Record] = {}
        for m in MASTER_FILES:
            mp = masters / m
            if mp.exists():
                for r in esm.Plugin.read(mp, sigs).records():
                    if r.sig in sigs:
                        self.win[r.key] = r
        for k, rs in L.chain.items():
            if rs[-1].sig in sigs:
                self.win[k] = rs[-1]

    def row(self, key: str, L: Load, **extra) -> dict:
        r = self.win.get(key)
        return {"id": key, "editor_id": r.edid if r else None, "name": r.name if r else None,
                "defined_in": key.split(":", 1)[1], **L.meta(key), **extra}


def master_cell_edids(masters: Path, keys: set[str]) -> dict[str, str | None]:
    """The masters' own editor ids of the given cell form keys (a byte walk; only those CELL records are opened)."""
    out = {}
    for m in MASTER_FILES:
        want = {int(k.split(":")[0], 16) for k in keys if k.endswith(":" + m)}
        mp = masters / m
        if not want or not mp.exists():
            continue
        data = mp.read_bytes()
        off, end = 24 + _u32(data, 4), len(data)
        while off < end:
            sig, size = data[off:off + 4], _u32(data, off + 4)
            if sig == b"GRUP":
                off += 24
                continue
            fid = _u32(data, off + 12)
            if sig == b"CELL" and (fid & 0xFFFFFF) in want:
                body = data[off + 24:off + 24 + size]
                if _u32(data, off + 8) & esm.COMPRESSED:
                    body = esm.zlib.decompress(body[4:])
                subs = dict(esm._subs(body))
                e = subs.get("EDID")
                out[f"{fid & 0xFFFFFF:06X}:{m}"] = e.split(b"\0", 1)[0].decode("cp1252") if e else None
            off += 24 + size
    return out


def census(L: Load, masters: Path) -> dict[str, list[dict]]:
    res = Resolver(L, masters, {"RACE", "CLAS", "FACT", "NPC_", "LVLN", "LCTN", "DOOR", "STAT"})
    T: dict[str, list[dict]] = defaultdict(list)
    cells = {c.key: c for c in L.live("CELL")}
    ext_ws = {k: L.world_key(c) for k, c in cells.items() if not is_interior(c)}
    refs = [r for r in L.live("REFR", "ACHR", "PGRE") if L.cell_key(r) in cells]
    refs_in = Counter(L.cell_key(r) for r in refs)
    nav = {L.cell_key(r) for r in L.live("NAVM")}
    land_cells = {L.cell_key(r) for r in L.live("LAND")} & set(cells)

    T["bmv_location"] = []
    locs = {r.key: res.row(r.key, L, parent=r.ref("PNAM"), in_bmv=True) for r in L.live("LCTN")}
    for c in cells.values():
        k = c.ref("XLCN")
        if k and k not in locs:
            loc = res.win.get(k)
            locs[k] = res.row(k, L, parent=loc.ref("PNAM") if loc else None, in_bmv=False)
    T["bmv_location"] = list(locs.values())

    def grid(c):
        g = c.sub("XCLC")
        inter = is_interior(c)
        persistent = not inter and (bool(c.flags & 0x400) or c.parents[-1][0] == 0 or g is None)
        return inter, persistent, (struct.unpack_from("<ii", g) if (g and not inter and not persistent) else (None, None))

    cellrow = {}
    for k, c in cells.items():
        inter, persistent, (gx, gy) = grid(c)
        cellrow[k] = {
            "id": k, **L.meta(k), "editor_id": c.edid, "name": c.name, "interior": inter,
            "worldspace": None if inter else ext_ws[k], "grid_x": gx, "grid_y": gy,
            "persistent": persistent, "location": c.ref("XLCN"), "has_navmesh": k in nav,
            "refs": refs_in[k], "defined_in": k.split(":", 1)[1]}
    T["bmv_cell"] = list(cellrow.values())
    # a master's interior BM&V edits but keeps as the master made it (its editor id unchanged: Dawnstar's Windpeak
    # Inn, Riverwood's Sleeping Giant Inn) is Skyrim's, not a BM&V place: the settlements leave it out
    ext_master = {k for k, r in cellrow.items() if r["interior"] and r["defined_in"] in MASTER_FILES}
    medid = master_cell_edids(masters, ext_master)
    T["_skyrim_interiors"] = [k for k in ext_master if k in medid and medid[k] == cellrow[k]["editor_id"]]
    worlds = {w.key: w for w in L.live("WRLD")}
    wland = Counter(cellrow[k]["worldspace"] for k in land_cells if cellrow[k]["grid_x"] is not None)
    T["bmv_worldspace"] = [{"id": k, **L.meta(k), "editor_id": w.edid, "name": w.name, "defined_in": k.split(":", 1)[1],
                            "parent": w.ref("WNAM"), "land_cells": wland[k]} for k, w in worlds.items()]

    # actors: every NPC_ in the files and every base their ACHRs place
    achrs = [r for r in refs if r.sig == "ACHR"]
    own_facts = {r.key for r in L.live("FACT")}
    bases = {r.key for r in L.live("NPC_")} | {a.ref("NAME") for a in achrs}
    races, classes, facs = set(), set(), set(own_facts)
    for k in sorted(bases):
        r = res.win.get(k)
        if r is None:
            raise SystemExit(f"actor base {k} is in no plugin read")
        bm = L.win(k) is not None
        row = res.row(k, L, record=r.sig, race=None, **{"class": None}, sex=None, template=r.ref("TPLT"),
                      template_flags=None, person=None, in_bmv=bm)
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
            seen = set()
            for s in r.all("SNAM"):
                fk = r.plugin.form_key(_u32(s))
                facs.add(fk)
                if bm and fk not in seen:
                    seen.add(fk)
                    T["bmv_npc_faction"].append({"npc": k, "faction": fk, "rank": struct.unpack_from("<b", s, 4)[0]})
        T["bmv_npc"].append(row)
    T["bmv_race"] = [res.row(k, L) for k in sorted(races)]
    T["bmv_class"] = [res.row(k, L) for k in sorted(classes)]
    T["bmv_faction"] = [res.row(k, L, in_bmv=k in own_facts) for k in sorted(facs)]

    def where(r):
        x, y, z = pos(r)
        c = cellrow[L.cell_key(r)]
        gx, gy = (None, None) if c["interior"] else grid_of(x, y)
        return {"id": r.key, **L.meta(r.key), "cell": c["id"], "x": round(x, 1), "y": round(y, 1), "z": round(z, 1),
                "grid_x": gx, "grid_y": gy}

    T["bmv_placement"] = [{**where(a), "npc": a.ref("NAME"), "disabled": bool(a.flags & DISABLED),
                           "enable_parent": a.ref("XESP")} for a in achrs]
    for q in L.live("QUST"):
        d = q.sub("DNAM")
        T["bmv_quest"].append({"id": q.key, **L.meta(q.key), "editor_id": q.edid, "name": q.name,
                               "start_game_enabled": bool(d[0] & 1), "priority": d[2],
                               "defined_in": q.key.split(":", 1)[1]})
    doors = [r for r in refs if r.sub("XTEL")]
    dkeys = {r.key for r in doors}
    at = {(c["worldspace"], c["grid_x"], c["grid_y"]): c["id"] for c in T["bmv_cell"] if c["grid_x"] is not None}
    for r in doors:
        t = r.plugin.form_key(_u32(r.sub("XTEL")))
        wh = where(r)
        ws = cellrow[wh["cell"]]["worldspace"]
        b = res.win.get(r.ref("NAME"))
        T["bmv_door"].append({**wh, "worldspace": ws, "ext_cell": at.get((ws, wh["grid_x"], wh["grid_y"])),
                              "target": t if t in dkeys else None, "target_elsewhere": None if t in dkeys else t,
                              "base": r.ref("NAME"), "base_editor_id": b.edid if b else None,
                              "base_name": b.name if b else None})
    for r in refs:
        if r.sub("XMRK") is not None and r.ref("NAME") == MAPMARKER:
            x, y, _ = pos(r)
            ws = cellrow[L.cell_key(r)]["worldspace"]
            if ws is None:
                continue
            gx, gy = grid_of(x, y)
            T["bmv_map_marker"].append({"id": r.key, **L.meta(r.key), "name": r.zstr("FULL"), "worldspace": ws,
                                        "x": round(x, 1), "y": round(y, 1), "grid_x": gx, "grid_y": gy,
                                        "settlement": None})
    placed = defaultdict(list)
    for r in refs:
        placed[r.ref("NAME")].append(r)
    for b in L.live("BOOK"):
        ps = placed.get(b.key, [])
        T["bmv_book"].append({"id": b.key, **L.meta(b.key), "editor_id": b.edid, "name": b.name, "placed": len(ps),
                              "first_cell": L.cell_key(ps[0]) if ps else None})
    settle(T)
    return dict(T)


def _cheb(a, b) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def _sid(ws: str, edid: str, worlds: dict[str, str]) -> str:
    return "bmv." + ("" if ws in OLD_WORLDS else worlds[ws].lower() + ".") + edid.lower()


def settle(T: dict[str, list[dict]]) -> None:
    """Group cells: named exterior cells clustered by distance, their neighbour squares, and the interiors whose load
    doors lead out near them; interiors that lead out elsewhere form a site at their exterior door."""
    cells = {c["id"]: c for c in T["bmv_cell"]}
    worlds = {w["id"]: w["editor_id"] for w in T["bmv_worldspace"]}
    own_worlds = {w["id"] for w in T["bmv_worldspace"] if w["defined_in"] in PLUGINS}
    named = [c for c in T["bmv_cell"] if not c["interior"] and c["grid_x"] is not None and c["editor_id"]
             and c["worldspace"] in own_worlds]
    parent = {c["id"]: c["id"] for c in named}

    def find(k):
        while parent[k] != k:
            k = parent[k]
        return k
    by_ws = defaultdict(list)
    for c in named:
        by_ws[c["worldspace"]].append(c)
    for group in by_ws.values():
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                d = _cheb((a["grid_x"], a["grid_y"]), (b["grid_x"], b["grid_y"]))
                if d > PREFIX_GRID:
                    continue
                same = a["editor_id"].lower()[:6] == b["editor_id"].lower()[:6]
                if {a["editor_id"], b["editor_id"]} & STANDALONE and not same:
                    continue
                if d <= LINK_GRID or same:
                    parent[find(a["id"])] = find(b["id"])
    clusters = defaultdict(list)
    for c in named:
        clusters[find(c["id"])].append(c)

    member: dict[str, tuple[str, str]] = {}
    squares: dict[str, list] = {}
    used = set()
    for group in sorted(clusters.values(), key=lambda g: min(c["id"] for c in g)):
        group.sort(key=lambda c: (len(c["editor_id"]), c["editor_id"]))
        # the anchor whose editor id begins the most others (Blackrose: Blackrosemarket, Blackrosegate), else the
        # busiest
        head = max(group, key=lambda c: (sum(o["editor_id"].lower().startswith(c["editor_id"].lower())
                                             for o in group), c["refs"]))
        sid = _sid(head["worldspace"], head["editor_id"], worlds)
        n = 2
        while sid in used:            # two clusters whose heads share an editor id in one worldspace
            sid = _sid(head["worldspace"], head["editor_id"], worlds) + f".{n}"
            n += 1
        used.add(sid)
        gx = round(sum(c["grid_x"] for c in group) / len(group))
        gy = round(sum(c["grid_y"] for c in group) / len(group))
        others = ", ".join(c["editor_id"] for c in group if c is not head)
        T["bmv_settlement"].append({
            "id": sid, "name": head["editor_id"], "kind": "settlement", "worldspace": head["worldspace"],
            "grid_x": gx, "grid_y": gy, "marker_name": None,
            "why": f"named exterior cell {head['editor_id']}" + (f" with {others} within {PREFIX_GRID} squares"
                                                                   if others else "")})
        squares[sid] = [(c["worldspace"], c["grid_x"], c["grid_y"]) for c in group]
        for c in group:
            member[c["id"]] = (sid, "anchor")
    anchors = defaultdict(list)
    for sid, sqs in squares.items():
        for sq in sqs:
            anchors[sq[0]].append((sid, sq[1:]))

    def nearest(c, lim):
        near = [(_cheb(sq, (c["grid_x"], c["grid_y"])), sid) for sid, sq in anchors[c["worldspace"]]]
        near = [n for n in near if n[0] <= lim]
        return min(near)[1] if near else None
    for c in T["bmv_cell"]:      # neighbour squares: the nearest settlement's anchor within one square
        if not c["interior"] and c["grid_x"] is not None and c["id"] not in member:
            s = nearest(c, 1)
            if s:
                member[c["id"]] = (s, "neighbour")
    for c in T["bmv_cell"]:      # area squares: any other square with content, nearest anchor within AREA_GRID
        if not c["interior"] and c["grid_x"] is not None and c["id"] not in member and c["refs"]:
            s = nearest(c, AREA_GRID)
            if s:
                member[c["id"]] = (s, "area")
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
    skyrim = set(T.pop("_skyrim_interiors", []))
    for c in sorted((c for c in T["bmv_cell"] if c["interior"] and c["id"] not in skyrim), key=lambda c: c["id"]):
        seen, todo, outs = {c["id"]}, [c["id"]], set()
        while todo:
            k = todo.pop()
            outs |= exits[k]
            for n in edges[k] - seen - skyrim:
                seen.add(n)
                todo.append(n)
        if not outs:
            continue
        best = []           # its exits: a ship has one per port, a shared house interior one per house door
        for o in sorted(outs):
            out = doors[o]
            ws = cells[out["cell"]]["worldspace"]
            sq = (out["grid_x"], out["grid_y"])
            near = sorted((_cheb(s, sq), sid) for sid, s in anchors[ws])
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
                "grid_x": sq[0], "grid_y": sq[1], "marker_name": None,
                "why": f"interiors whose load doors lead out at {worlds.get(ws, ws)} square {sq}, "
                       f"no named exterior cell within {DOOR_GRID}"})
        member[c["id"]] = (sites[sk], "interior")
    T["bmv_settlement_cell"] = [{"settlement": s, "cell": k, "role": r} for k, (s, r) in member.items()]
    # BM&V's map markers belong to the settlement whose squares they stand on, and name it when on an anchor or neighbour
    sq_of = {(cells[k]["worldspace"], cells[k]["grid_x"], cells[k]["grid_y"]): (s, r) for k, (s, r) in member.items()
             if cells[k]["grid_x"] is not None}
    sett = {s["id"]: s for s in T["bmv_settlement"]}
    for m in T.get("bmv_map_marker", []):
        s, role = sq_of.get((m["worldspace"], m["grid_x"], m["grid_y"]), (None, None))
        m["settlement"] = s
        if s and role in ("anchor", "neighbour") and sett[s]["kind"] == "settlement" and m["name"]:
            prev = sett[s]["marker_name"]
            sett[s]["marker_name"] = m["name"] if not prev or m["name"] in prev else f"{prev}; {m['name']}"


def build(d: Path, masters: Path) -> dict[str, int]:
    T = census(Load(d), masters)
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
    w.save()                       # raises on any dangling key; nothing is written then
    return {t: len(T.get(t, [])) for t in reversed(TABLES)}


# --- the completeness proof -------------------------------------------------------------------------------------------

def _raw_sigs(path: Path) -> Counter:
    """Every record signature in a plugin, counted by walking the bytes (groups opened, records skipped unread): a
    second path, independent of esm.Plugin."""
    data = path.read_bytes()
    out = Counter()
    off = 24 + _u32(data, 4)
    stack = [len(data)]
    while off < len(data):
        while off >= stack[-1]:
            stack.pop()
        sig = data[off:off + 4]
        size = _u32(data, off + 4)
        if sig == b"GRUP":
            stack.append(off + size)
            off += 24
        else:
            out[sig.decode()] += 1
            off += 24 + size
    return out


PROOF = ("WRLD", "CELL", "LAND", "ACHR", "NPC_", "FACT", "QUST", "LCTN", "BOOK", "door", "mapmarker")


def proof(d: Path = DIR) -> tuple[list[dict], list[str]]:
    """Per plugin and type: records in the file (by bytes, and as read), how many are the load order's live winner
    and in the census, how many a later plugin overrides, how many are deleted, and how many fall out (a winner
    whose cell is deleted). Accounted when file = in census + overridden later + deleted + dropped, and the census
    rows equal the live winners."""
    L = Load(d)
    w = db.load()
    ids = {
        "WRLD": "bmv_worldspace", "CELL": "bmv_cell", "ACHR": "bmv_placement", "QUST": "bmv_quest",
        "LCTN": "bmv_location", "BOOK": "bmv_book", "door": "bmv_door", "mapmarker": "bmv_map_marker"}
    have = {t: set(w.values(f'SELECT id FROM "{t}"')) for t in set(ids.values())}
    have["NPC_"] = set(w.values("SELECT id FROM bmv_npc WHERE record = 'NPC_' AND in_bmv = 1"))
    have["FACT"] = set(w.values("SELECT id FROM bmv_faction WHERE in_bmv = 1"))
    for k, t in ids.items():
        have.setdefault(k, have[t])
    land_db = {}
    for c in w.query("SELECT id FROM bmv_cell"):
        land_db[c[0]] = True
    rows, bad = [], []
    for i, p in enumerate(L.plugins):
        raw = _raw_sigs(d / p.name)
        for sig in PROOF:
            def is_kind(r):
                if sig == "door":
                    return r.sig == "REFR" and r.sub("XTEL") is not None
                if sig == "mapmarker":
                    return r.sig == "REFR" and r.sub("XMRK") is not None and r.ref("NAME") == MAPMARKER
                return r.sig == sig
            recs = [r for r in p.records() if is_kind(r)]
            n_bytes = raw[sig] if sig not in ("door", "mapmarker") else None
            later = deleted = inc = drop = 0
            for r in recs:
                rs = L.chain[r.key]
                if rs[-1] is not r:
                    later += 1
                elif r.key in L.deleted:
                    deleted += 1
                elif sig == "LAND":
                    ck = L.cell_key(r)
                    inc += 1 if ck in land_db else 0
                    drop += 0 if ck in land_db else 1
                elif r.key in have[sig]:
                    inc += 1
                else:
                    drop += 1
            ok = (n_bytes is None or n_bytes == len(recs)) and len(recs) == inc + later + deleted + drop and drop == 0
            rows.append({"plugin": p.name, "type": sig, "bytes": n_bytes, "read": len(recs), "census": inc,
                         "later": later, "deleted": deleted, "dropped": drop, "ok": ok})
            if not ok:
                bad.append(f"{p.name} {sig}: {rows[-1]}")
    # and the other way: every census row of a BM&V record is a live winner of that kind
    for sig, t in ids.items():
        kind = {"door": "REFR", "mapmarker": "REFR"}.get(sig, sig)
        live = {r.key for r in L.live(kind)}
        extra = {k for k in have[sig] if L.chain.get(k)} - live
        if extra:
            bad.append(f"{t}: {len(extra)} rows are not live {kind} winners, e.g. {sorted(extra)[:3]}")
    return rows, bad


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=["build", "verify"])
    ap.add_argument("--dir", type=Path, default=DIR)
    ap.add_argument("--masters", type=Path, default=MASTERS)
    a = ap.parse_args(argv)
    if a.cmd == "build":
        for t, k in build(a.dir, a.masters).items():
            print(f"{t}\t{k}")
        return 0
    rows, bad = proof(a.dir)
    print("plugin\ttype\tbytes\tread\tcensus\tlater\tdeleted\tdropped\tok")
    for r in rows:
        print("\t".join(str(r[k]) for k in ("plugin", "type", "bytes", "read", "census", "later", "deleted",
                                             "dropped", "ok")))
    print("\n".join(bad) or "census accounts for every record")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
