"""The offline BM&V map (phase 1): one self-contained HTML page, out/bmv-map/index.html, of every worldspace BM&V's
four plugins add or edit (a switcher). The land is drawn from the load order's winning LAND height grids (hillshade,
and water where the land lies below the cell's water; a LAND without heights is drawn flat at the worldspace's default
land height); the census tables (bmv_* through tools/argonia_world/db.py), place_bmv, BM&V's own map markers and our
markers in plugin/Argonia sit on top as layers. The page and its terrain are derived from BM&V's files, so they live
under out/ and are never committed (decision 0003). Rerunning rewrites the page whole.

    python3 -m tools.bmv_map.build build  [--dir DIR] [--out out/bmv-map/index.html]   # `make map`
    python3 -m tools.bmv_map.build verify [--out ...]   # read the built page back and check it against the db and files
"""
from __future__ import annotations

import argparse
import base64
import json
import math
import re
import struct
import sys
import zlib
from collections import defaultdict
from pathlib import Path

import numpy as np

from tools.argonia_world import db, esm
from tools.argonia_world.bmv_census import DIR, MASTERS, MASTER_FILES, GRID, Load, is_interior

CELL_KM2 = (GRID / 70 / 1000) ** 2   # a cell is 4096 units a side at 70 units a metre: 58.5 m, 0.00342 km²
DRY = 0.02                  # a cell is dry ground when more than 2% of its height points stand above its water
TEST = re.compile(r"test|^fix$", re.I)   # BM&V's internal test cells and labels (Quick Test Cell, test1, misttest, fix)
# BM&V's own worldspaces with LAND, in the overview's order, with their role
ROLES = {"Valenwood": ("Valenwood", "Valenwood.esp's whole province: Elden Root, Falinesti, Arenthia, Woodhearth..."),
         "BlackMarsh": ("Black Marsh: the south", "Lilmoth, Blackrose, Hereguard Plantation, Longmont, Alten Merihall"),
         "BlackMarsh2": ("Black Marsh: the interior", "Helstrom, Murkmire, Murkwood, Temple Pass"),
         "BlackMarshNorth": ("Black Marsh: the north", "Thorn, Tear, Dres village, the Morrowind border")}
# the province dossier's sub-regions and the dossiers' own places (story/lore/black-marsh-province.md, regions/)
LORE_EXTRA = [("Shadowfen", "story/lore/regions/shadowfen.md"), ("Thornmarsh", "story/lore/regions/thornmarsh-and-east.md"),
              ("Arnesia", "story/lore/regions/thornmarsh-and-east.md"), ("Tear", "story/lore/regions/thornmarsh-and-east.md"),
              ("Middle Argonia", "story/lore/regions/middle-argonia.md"), ("Murkmire", "story/lore/regions/murkmire.md"),
              ("Deepmire", "story/lore/regions/murkmire.md"), ("Murkwood", "story/lore/regions/middle-argonia.md"),
              ("Blackwood", "story/lore/regions/blackwood-and-gloommire.md"),
              ("Gloommire", "story/lore/regions/blackwood-and-gloommire.md"),
              ("Blackwood Bog", "story/lore/regions/blackwood-and-gloommire.md")]

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out/bmv-map/index.html"
PLUGIN = ROOT / "plugin/Argonia/Worldspaces"
BUDGET = 4_000_000           # bytes of base64 terrain per worldspace (the page stays under ~20 MB)
NO_WATER = 1e30              # XCLW at FLT_MAX means "the worldspace's default"


# --- the land ---------------------------------------------------------------------------------------------------------

def vhgt(d: bytes) -> np.ndarray:
    """A LAND's VHGT as a 33x33 array of heights in game units, row 0 the cell's south edge, column 0 its west."""
    off = struct.unpack_from("<f", d)[0]
    g = np.frombuffer(d, dtype=np.int8, count=33 * 33, offset=4).astype(np.float64).reshape(33, 33)
    g[:, 0] = np.cumsum(g[:, 0])
    return (off + np.cumsum(g, axis=1)) * 8.0


def png(rgba: np.ndarray) -> bytes:
    """An RGBA uint8 (h, w, 4) array as PNG bytes (stdlib zlib, filter 'up' per row)."""
    h, w, _ = rgba.shape
    raw = rgba.astype(np.uint8)
    up = raw.copy()
    up[1:] = raw[1:] - raw[:-1]
    rows = np.concatenate([np.full((h, 1), 2, np.uint8), up.reshape(h, w * 4)], axis=1)

    def chunk(t: bytes, b: bytes) -> bytes:
        return struct.pack(">I", len(b)) + t + b + struct.pack(">I", zlib.crc32(t + b) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows.tobytes(), 9)) + chunk(b"IEND", b""))


def unpng(b: bytes) -> np.ndarray:
    """The inverse of png() (only what png() writes: 8-bit RGBA, filters none or up)."""
    w, h = struct.unpack_from(">II", b, 16)
    i, data = 8, b""
    while i < len(b):
        n = struct.unpack_from(">I", b, i)[0]
        if b[i + 4:i + 8] == b"IDAT":
            data += b[i + 8:i + 8 + n]
        i += 12 + n
    rows = np.frombuffer(zlib.decompress(data), np.uint8).reshape(h, w * 4 + 1)
    px = rows[:, 1:].copy()
    for r in range(1, h):
        if rows[r, 0] == 2:
            px[r] = px[r] + px[r - 1]
    return px.reshape(h, w, 4)


def lands(L: Load) -> dict[str, dict[tuple[int, int], tuple[np.ndarray, float | None]]]:
    """Per worldspace form key: (grid x, grid y) -> (33x33 heights, water height or None when the cell has none), from
    the load order's winning LAND of each exterior cell."""
    default = {}
    for w in L.live("WRLD"):
        dn = w.sub("DNAM")
        default[w.key] = struct.unpack_from("<ff", dn) if dn else (0.0, 0.0)
    cells = {}
    for c in L.live("CELL"):
        if not is_interior(c) and c.sub("XCLC") and not c.flags & 0x400:
            wk = L.world_key(c)
            gx, gy = struct.unpack_from("<ii", c.sub("XCLC"))
            d = c.sub("DATA")
            has = bool(d and d[0] & 2)
            xw = c.sub("XCLW")
            wl = struct.unpack_from("<f", xw)[0] if xw else NO_WATER * 2
            if wl > NO_WATER:
                wl = default.get(wk, (0.0, 0.0))[1]
            cells[c.key] = (wk, gx, gy, wl if has else None)
    out: dict = defaultdict(dict)
    for r in L.live("LAND"):
        ck = L.cell_key(r)
        if ck in cells:
            ws, gx, gy, wl = cells[ck]
            d = r.sub("VHGT")
            h = vhgt(d) if d else np.full((33, 33), default.get(ws, (0.0, 0.0))[0])
            out[ws][(gx, gy)] = (h, wl)
    return out


def terrain(cells: dict, ppc: int, extra=()) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """The RGBA image of one worldspace at `ppc` pixels per cell, and its grid bounds (x0, y0, x1, y1) inclusive,
    widened to hold the `extra` squares (cells and content with no LAND)."""
    xs = [g[0] for g in cells] + [g[0] for g in extra]
    ys = [g[1] for g in cells] + [g[1] for g in extra]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    n = 32
    if not any(h is not None for h, _ in cells.values()):     # no LAND: an empty (transparent) frame of the bounds
        return np.zeros(((y1 - y0 + 1) * ppc, (x1 - x0 + 1) * ppc, 4), np.uint8), (x0, y0, x1, y1)
    W, H = (x1 - x0 + 1) * n, (y1 - y0 + 1) * n
    hgt = np.full((H, W), np.nan)
    wat = np.full((H, W), np.nan)
    for (gx, gy), (h, wl) in cells.items():
        if h is None:
            continue
        r0 = (y1 - gy) * n          # image row 0 is the north edge
        c0 = (gx - x0) * n
        hgt[r0:r0 + n, c0:c0 + n] = h[:n, :n][::-1]
        if wl is not None:
            wat[r0:r0 + n, c0:c0 + n] = wl
    k = n // ppc
    hgt, wat = hgt[::k, ::k], wat[::k, ::k]
    land = ~np.isnan(hgt)
    hf = np.where(land, hgt, np.nanmin(hgt))
    gy_, gx_ = np.gradient(hf, 4096.0 / ppc)
    slope = np.arctan(np.hypot(gx_, gy_) * 1.5)
    aspect = np.arctan2(-gx_, gy_)
    az, alt = np.radians(315), np.radians(45)
    shade = np.clip(np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect), 0, 1)
    lo, hi = np.nanpercentile(hgt, 2), np.nanpercentile(hgt, 99.5)
    t = np.clip((hf - lo) / max(hi - lo, 1), 0, 1)
    stops = np.array([[0.0, 74, 92, 52], [0.25, 96, 112, 60], [0.5, 128, 120, 72], [0.75, 140, 128, 104],
                      [1.0, 220, 220, 214]])
    rgb = np.stack([np.interp(t, stops[:, 0], stops[:, i]) for i in (1, 2, 3)], axis=-1)
    rgb *= (0.45 + 0.75 * shade)[..., None]
    under = land & ~np.isnan(wat) & (hf < np.nan_to_num(wat, nan=-1e9))
    depth = np.clip((np.nan_to_num(wat) - hf) / 1500.0, 0, 1)[..., None]
    water = np.array([70, 120, 140]) * (1 - depth) + np.array([24, 52, 82]) * depth
    rgb = np.where(under[..., None], water * (0.85 + 0.15 * shade[..., None]), rgb)
    img = np.zeros(hgt.shape + (4,), np.uint8)
    img[..., :3] = np.clip(rgb, 0, 255)
    img[..., 3] = np.where(land, 255, 0)
    return img, (x0, y0, x1, y1)


# --- the layers -------------------------------------------------------------------------------------------------------

def markers() -> list[dict]:
    """Our placed references in plugin/Argonia's worldspaces: editor id, worldspace form key, position."""
    out = []
    for f in sorted(PLUGIN.glob("*/RecordData.yaml")):
        m = re.match(r"(.+?) - ([0-9A-F]{6})_(.+)$", f.parent.name)
        ws = f"{m.group(2)}:{m.group(3)}" if m else None
        text = f.read_text()
        for e in re.finditer(r"EditorID: (\S+)(?:(?!EditorID:).)*?Position: (-?[\d.]+), (-?[\d.]+), (-?[\d.]+)",
                             text, re.S):
            out.append({"edid": e.group(1), "ws": ws, "x": float(e.group(2)), "y": float(e.group(3)),
                        "z": float(e.group(4))})
    return out


def layers(w: db.World) -> dict[str, dict]:
    q = lambda sql, *a: [dict(r) for r in w.query(sql, *a)]  # noqa: E731
    worlds = {r["editor_id"]: r for r in q("SELECT * FROM bmv_worldspace")}
    mms = q("SELECT * FROM bmv_map_marker")
    cells = {r["id"]: r for r in q("SELECT * FROM bmv_cell")}
    member = {r["cell"]: r for r in q("SELECT * FROM bmv_settlement_cell")}
    sett = {r["id"]: r for r in q("SELECT * FROM bmv_settlement")}
    npcs = {r["id"]: r for r in q("SELECT * FROM bmv_npc")}
    places = q("SELECT pb.*, p.name AS place_name FROM place_bmv pb JOIN place p ON p.id = pb.place")
    place_of = defaultdict(list)
    for p in places:
        if p["settlement"]:
            place_of[p["settlement"]].append(p)
        if p["cell"]:
            place_of[p["cell"]].append(p)
    doors = {r["id"]: r for r in q("SELECT * FROM bmv_door")}
    plac = q("SELECT * FROM bmv_placement")
    s_npcs = defaultdict(list)
    for a in plac:
        s = member.get(a["cell"])
        if s:
            n = npcs[a["npc"]]
            s_npcs[s["settlement"]].append(n["name"] or n["editor_id"])

    mm_names = defaultdict(list)                                   # a settlement's in-game names: its map markers'
    for m in mms:
        if m["settlement"] and m["name"] not in mm_names[m["settlement"]]:
            mm_names[m["settlement"]].append(m["name"])

    def display(s):
        """A settlement's in-game name: the census's marker name, else a map marker of the same name as its editor id
        within 10 cells (Helstrom, Murkmire, Temple Pass), else the markers standing in it, else none."""
        if s["marker_name"]:
            return s["marker_name"]
        k = re.sub(r"[^a-z]", "", (s["name"] or "").lower())
        same = [m["name"] for m in mms if m["worldspace"] == s["worldspace"] and k and
                re.sub(r"[^a-z]", "", m["name"].lower()) == k and
                max(abs(m["grid_x"] - s["grid_x"]), abs(m["grid_y"] - s["grid_y"])) <= 10]
        return same[0] if same else "; ".join(mm_names[s["id"]]) or None

    def label(cid):
        """A cell's in-game name (its FULL, unless a test name), else its settlement's map-marker name, else none."""
        c = cells.get(cid)
        if not c:
            return None
        if c["name"] and not TEST.search(c["name"]):
            return c["name"]
        m = member.get(cid)
        return display(sett[m["settlement"]]) if m else None

    out = {}
    for ed, wr in worlds.items():
        wid = wr["id"]
        cl = [c for c in cells.values() if c["worldspace"] == wid and c["grid_x"] is not None]
        S = []
        for s in sett.values():
            if s["worldspace"] != wid:
                continue
            sc = [k for k, m in member.items() if m["settlement"] == s["id"]]
            S.append({**s, "cells": [[cells[k]["grid_x"], cells[k]["grid_y"], member[k]["role"]] for k in sc
                                     if cells[k]["grid_x"] is not None],
                      "label": display(s), "test": bool(TEST.search(s["name"] or "")) and not display(s),
                      "interiors": sorted(f"{cells[k]['name'] or 'no name'} ({cells[k]['editor_id']})" for k in sc
                                          if cells[k]["interior"]),
                      "npcs": sorted(s_npcs[s["id"]]), "places": place_of[s["id"]]})
        D = []
        for d in doors.values():
            if d["worldspace"] != wid:
                continue
            t = doors.get(d["target"]) if d["target"] else None
            to = {"elsewhere": d["target_elsewhere"]}
            if t:
                tc = cells[t["cell"]]
                to = {"door": t["id"], "cell": t["cell"], "label": label(t["cell"]), "edid": tc["editor_id"],
                      "test": bool(TEST.search(tc["name"] or "") or TEST.search(tc["editor_id"] or "")),
                      "interior": bool(tc["interior"]), "ws": t["worldspace"], "x": t["x"], "y": t["y"]}
                m = member.get(t["cell"])
                if m:
                    to["settlement"] = sett[m["settlement"]]["name"]
            D.append({"id": d["id"], "x": d["x"], "y": d["y"], "z": d["z"], "cell": d["cell"], "base": d["base_editor_id"],
                      "base_name": d["base_name"], "plugin": d["plugin"],
                      "portal": bool(re.search(r"book|portal", d["base_editor_id"] or "", re.I)),
                      "ext_cell": d["ext_cell"], "to": to})
        A = []
        for a in plac:
            c = cells[a["cell"]]
            if c["worldspace"] != wid:
                continue
            n = npcs[a["npc"]]
            m = member.get(a["cell"])
            A.append({"id": a["id"], "npc": n["id"], "edid": n["editor_id"], "name": n["name"], "rec": n["record"],
                      "person": n["person"], "x": a["x"], "y": a["y"], "z": a["z"], "disabled": a["disabled"],
                      "cell": a["cell"], "settlement": sett[m["settlement"]]["name"] if m else None})
        C = {f"{c['grid_x']},{c['grid_y']}": {"id": c["id"], "edid": c["editor_id"], "name": c["name"],
                                              "test": bool(TEST.search(c["editor_id"] or "")),
                                              "nav": c["has_navmesh"], "refs": c["refs"],
                                              "settlement": sett[member[c["id"]]["settlement"]]["name"]
                                              if c["id"] in member else None,
                                              "places": place_of.get(c["id"], [])} for c in cl}
        P = []
        for p in places:
            if p["status"] != "mapped":
                continue
            s = sett.get(p["settlement"]) if p["settlement"] else None
            c = cells.get(p["cell"]) if p["cell"] else None
            if s and s["worldspace"] == wid:
                P.append({**p, "gx": s["grid_x"], "gy": s["grid_y"], "at": s["name"]})
            elif c and c["worldspace"] == wid and c["grid_x"] is not None:
                P.append({**p, "gx": c["grid_x"], "gy": c["grid_y"], "at": label(c["id"]) or c["editor_id"]})
        M = [m for m in markers() if m["ws"] == wid]
        B = [{**m, "settlement": sett[m["settlement"]]["name"] if m["settlement"] else None}
             for m in mms if m["worldspace"] == wid]
        out[ed] = {"id": wid, "name": wr["name"], "plugin": wr["plugin"], "settlements": S, "doors": D, "actors": A,
                   "cells": C, "places": P, "markers": M, "bmvmarkers": B,
                   "waiting": [p for p in places if p["status"] == "waiting"]}
    return out


# --- the overview, islands, links and lore places ----------------------------------------------------------------------

def dry_cells(cells: dict) -> set[tuple[int, int]]:
    """The cells whose ground stands above their water at more than DRY of their height points."""
    return {k for k, (h, wl) in cells.items() if h is not None
            and (h[:32, :32] > (wl if wl is not None else -1e30)).mean() > DRY}


def size(cells: dict) -> dict:
    n, d = len(cells), len(dry_cells(cells))
    frac = float(np.mean([(h[:32, :32] > (wl if wl is not None else -1e30)).mean() for h, wl in cells.values()])) \
        if cells else 0.0
    return {"cells": n, "km2": round(n * CELL_KM2, 2), "dry_km2": round(n * frac * CELL_KM2, 2), "dry_cells": d}


def tamriel() -> dict | None:
    """Skyrim's Tamriel measured the same way, from Skyrim.esm and Update.esm's LAND (None if the masters are absent)."""
    if not (MASTERS / "Skyrim.esm").exists():
        return None
    t = lands(Load(MASTERS, ("Skyrim.esm", "Update.esm"))).get("00003C:Skyrim.esm", {})
    return size(t)


def islands(d: dict, cells: dict) -> None:
    """The dry ground of a worldspace as islands (8-connected dry cells), each with what stands on it; sets
    d["islands"] (largest first) and d["island_of"] ("x,y" -> index)."""
    dry = dry_cells(cells)
    seen, comps = set(), []
    for s in sorted(dry):
        if s in seen:
            continue
        st, comp = [s], []
        seen.add(s)
        while st:
            c = st.pop()
            comp.append(c)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    n = (c[0] + dx, c[1] + dy)
                    if n in dry and n not in seen:
                        seen.add(n)
                        st.append(n)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    sq = lambda o: f"{math.floor(o['x'] / GRID)},{math.floor(o['y'] / GRID)}"  # noqa: E731
    acts, doors, mks = defaultdict(int), defaultdict(int), defaultdict(list)
    for a in d["actors"]:
        acts[sq(a)] += 1
    for o in d["doors"]:
        doors[sq(o)] += 1
    for m in d["bmvmarkers"]:
        mks[sq(m)].append(m["name"])
    out, of = [], {}
    for i, comp in enumerate(comps):
        keys = [f"{x},{y}" for x, y in comp]
        xs, ys = [c[0] for c in comp], [c[1] for c in comp]
        refs = sum((d["cells"].get(k) or {}).get("refs") or 0 for k in keys)
        npl = sum(acts[k] for k in keys)
        sts = sorted({st["label"] or st["name"] for st in d["settlements"] if any(f"{c[0]},{c[1]}" in keys
                                                                                 for c in st["cells"])})
        verdict = ("bare LAND: nothing placed on it (no object, no actor, no door)" if refs == 0 else
                   "objects only: no actor placed" if npl == 0 else "inhabited")
        out.append({"i": i, "cells": len(comp), "km2": round(len(comp) * CELL_KM2, 2), "x0": min(xs), "x1": max(xs),
                    "y0": min(ys), "y1": max(ys), "cx": (min(xs) + max(xs) + 1) / 2, "cy": (min(ys) + max(ys) + 1) / 2,
                    "refs": refs, "placements": npl, "doors": sum(doors[k] for k in keys),
                    "markers": sorted({n for k in keys for n in mks[k]}), "settlements": sts, "verdict": verdict})
        for k in keys:
            of[k] = i
    d["islands"], d["island_of"] = out, of


def links(w: db.World, data: dict) -> list[dict]:
    """The ways between worldspaces: each group of interiors joined by load doors (a ship, a house, a cave run, an
    inn) that has doors out to more than one worldspace, or to one of BM&V's and a vanilla Skyrim interior."""
    q = lambda sql: [dict(r) for r in w.query(sql)]  # noqa: E731
    cells = {c["id"]: c for c in q("SELECT id, editor_id, name, interior, worldspace, defined_in FROM bmv_cell")}
    doors = {d["id"]: d for d in q("SELECT * FROM bmv_door")}
    ed = {r["id"]: r["editor_id"] for r in q("SELECT id, editor_id FROM bmv_worldspace")}
    sett = {r["cell"]: r["settlement"] for r in q("SELECT cell, settlement FROM bmv_settlement_cell")}
    names = {s["id"]: s["label"] for d in data.values() for s in d["settlements"]}
    par: dict = {}

    def find(x):
        while par.setdefault(x, x) != x:
            x = par[x]
        return x
    for d in doors.values():
        t = doors.get(d["target"])
        if t and cells[d["cell"]]["interior"] and cells[t["cell"]]["interior"]:
            par[find(d["cell"])] = find(t["cell"])
    ends, members, bases = defaultdict(dict), defaultdict(set), defaultdict(set)
    for d in doors.values():
        t = doors.get(d["target"])
        for a, b in ((d, t), (t, d)):
            if not a or not b or not cells[a["cell"]]["interior"] or cells[b["cell"]]["interior"]:
                continue
            g = find(a["cell"])
            members[g].add(a["cell"])
            bases[g].update(x["base_editor_id"] or "" for x in (a, b))
            wsd = ed.get(cells[b["cell"]]["worldspace"])
            s = sett.get(b["cell"])
            ends[g][b["id"]] = {"ws": wsd, "x": b["x"], "y": b["y"], "door": b["id"], "settlement": s,
                                "at": names.get(s) if s else None}
    for e in ends.values():                # an end with no named settlement: the nearest map marker within 3 cells
        for x in e.values():
            if x["at"] or x["ws"] not in data:
                continue
            g = [math.floor(x["x"] / GRID), math.floor(x["y"] / GRID)]
            own = [st["label"] for st in data[x["ws"]]["settlements"] if st["label"] and any(c[:2] == g for c in st["cells"])]
            if own:
                x["at"] = own[0]
                continue
            mk = sorted((math.hypot(m["x"] - x["x"], m["y"] - x["y"]), m["name"]) for m in data[x["ws"]]["bmvmarkers"])
            if mk and mk[0][0] <= 3 * GRID:
                x["at"] = f"by {mk[0][1]}"
    locs = [(r["editor_id"][:-len("Location")], r["name"]) for r in q("SELECT editor_id, name FROM bmv_location")
            if (r["editor_id"] or "").endswith("Location")]

    def vname(c):
        """A vanilla interior's name as Skyrim shows it: its location's name where the cell's own is generic."""
        loc = [n for e, n in locs if (c["editor_id"] or "").startswith(e)]
        return loc[0] if loc else c["name"] or c["editor_id"]
    out = []
    for g, e in ends.items():
        vanilla = sorted(vname(cells[m]) for m in members[g]
                         if cells[m]["defined_in"] in MASTER_FILES and not (cells[m]["editor_id"] or "").startswith("01"))
        wss = {x["ws"] for x in e.values()}
        if len(wss) < 2 and not vanilla:
            continue
        b = " ".join(bases[g])
        mem = sorted(members[g], key=lambda m: cells[m]["editor_id"] or "")
        kind = ("book portal" if re.search(r"book", b, re.I) else "magic portal" if re.search(r"portal", b, re.I)
                else "ship" if any(re.search(r"ship|dock", cells[m]["editor_id"] or "", re.I) for m in mem)
                else "door")
        via = ", ".join(f"{cells[m]['name'] or 'no name'} ({cells[m]['editor_id']})" for m in mem)
        out.append({"kind": kind, "via": via, "skyrim": vanilla, "ends": sorted(e.values(), key=lambda x: (x["ws"], x["x"]))})
    out.sort(key=lambda r: (bool(r["skyrim"]), r["via"]))
    return out


def norm(s: str) -> str:
    return re.sub(r"[^a-z]", "", (s or "").lower())


def lore_places(w: db.World, data: dict) -> list[dict]:
    """Every Black Marsh place story/lore names (the place table's canon-named places, the dossiers' own places and the
    province dossier's sub-regions) with where it is in BM&V: a ruled mapping (place_bmv), a name match, or none."""
    rows = [dict(r) for r in w.query("SELECT id, name, region FROM place WHERE provenance = 'canon-named'")]
    pb = {r["place"]: dict(r) for r in w.query("SELECT * FROM place_bmv")}
    seen = {norm(r["name"]) for r in rows}
    rows += [{"id": None, "name": n, "region": None, "source": src} for n, src in LORE_EXTRA if norm(n) not in seen]
    # every BM&V name with a position: map markers, settlement names (marker names), cell names and editor ids
    cand = []
    for wsd, d in data.items():
        for m in d["bmvmarkers"]:
            cand.append((norm(m["name"]), wsd, m["x"], m["y"], f"BM&V map marker \"{m['name']}\""))
        for s in d["settlements"]:
            cand.append((norm(s["name"]), wsd, (s["grid_x"] + .5) * GRID, (s["grid_y"] + .5) * GRID,
                         f"cell editor id {s['name']}" + (f" (\"{s['label']}\")" if s["label"] else "")))
    out = []
    for r in sorted(rows, key=lambda r: r["name"]):  # sorted again below: mapped, name matches, absent
        p = pb.get(r["id"]) if r["id"] else None
        e = {"name": r["name"], "place": r["id"], "region": r["region"], "source": r.get("source")}
        if p and p["status"] == "mapped":
            for wsd, d in data.items():
                hit = [x for x in d["places"] if x["place"] == r["id"]]
                if hit:
                    h = hit[0]
                    s = next((x for x in d["settlements"] if x["id"] == h["settlement"]), None)
                    at = (s["label"] or "an unnamed place (no in-game name; click for its editor id)") if s else h["at"]
                    e.update(status="mapped", ws=wsd, x=(h["gx"] + .5) * GRID, y=(h["gy"] + .5) * GRID,
                             what=f"ruled mapping ({p['confidence']}): {at}", reason=p["reason"])
            if "status" not in e:
                c = w.query("SELECT editor_id, name FROM bmv_cell WHERE id = ?", p["cell"])
                what = (f"{c[0][0]}, a vanilla test cell BM&V reuses (in-game name \"{c[0][1]}\"): no real prison"
                        if c else p["cell"])
                e.update(status="mapped", what=f"ruled mapping ({p['confidence']}) to an interior: {what}",
                         reason=p["reason"])
        else:
            n = norm(r["name"])
            hit = [c for c in cand if c[0] == n] or [c for c in cand if len(n) > 4 and c[0].startswith(n)]
            if hit:
                c = hit[0]
                e.update(status="name", ws=c[1], x=c[2], y=c[3], what=f"name match only, not a ruled mapping: {c[4]}")
            else:
                e.update(status="absent", what="not in BM&V" + (": the census searched every record of the four "
                                                                "files" if p else ": no BM&V marker or cell name matches"))
        out.append(e)
    return out


# --- the page ---------------------------------------------------------------------------------------------------------

def bounds(d: dict) -> dict[tuple[int, int], None]:
    """The squares a worldspace's layers touch, for a world with no LAND of BM&V's (a vanilla override)."""
    sq = {tuple(map(int, k.split(","))): None for k in d["cells"]}
    for o in d["doors"] + d["actors"] + d["bmvmarkers"] + d["markers"]:
        sq[(math.floor(o["x"] / GRID), math.floor(o["y"] / GRID))] = None
    return sq or {(0, 0): None}


def build(bdir: Path, out: Path) -> dict:
    L = Load(bdir)
    land = lands(L)
    data = layers(db.open())
    uris, stats = {}, {}
    for ed, d in data.items():
        cells = land.get(d["id"]) or {k: (None, None) for k in bounds(d)}
        for ppc in (32, 16, 8, 4, 2):
            im, (x0, y0, x1, y1) = terrain(cells, ppc, list(bounds(d)))
            u = base64.b64encode(png(im)).decode()
            if len(u) <= BUDGET:
                break
        uris[ed] = "data:image/png;base64," + u
        d["terrain"] = {"ppc": ppc, "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                        "land": sorted(f"{x},{y}" for x, y in land.get(d["id"], {}))}
        stats[ed] = f"{len(d['terrain']['land'])} LAND at {ppc} px"
        islands(d, land.get(d["id"], {}))
        d["size"] = size(land.get(d["id"], {}))
        d["role"] = ROLES.get(ed)
        d["unfinished"] = [m for m in d["bmvmarkers"] if re.search(r"coming soon", m["name"] or "", re.I)]
    w = db.open()
    ov = {"order": [e for e in ROLES if e in data], "tamriel": tamriel(), "links": links(w, data),
          "lore": lore_places(w, data)}
    mine = [data[e]["size"] for e in ov["order"]]
    ov["total"] = {k: round(sum(m[k] for m in mine), 2) for k in ("cells", "km2", "dry_km2")}
    bm = [data[e]["size"] for e in ov["order"] if e != "Valenwood"]
    ov["black_marsh"] = {k: round(sum(m[k] for m in bm), 2) for k in ("cells", "km2", "dry_km2")}
    stats["overview"] = {"total": ov["total"], "black_marsh": ov["black_marsh"], "tamriel": ov["tamriel"],
                         "links": len(ov["links"])}
    page = TEMPLATE.replace("/*DATA*/null", json.dumps(data, separators=(",", ":")).replace("</", "<\\/")).replace(
        "/*IMAGES*/null", json.dumps(uris)).replace("/*OVERVIEW*/null", json.dumps(ov, separators=(",", ":")).replace(
            "</", "<\\/"))
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    tmp.write_text(page)
    tmp.replace(out)
    return {"bytes": len(page.encode()), **stats}


def read_page(out: Path) -> tuple[dict, dict]:
    page = out.read_text()
    data = json.loads(re.search(r"const DATA = (.*?);\n", page).group(1))
    images = json.loads(re.search(r"const IMAGES = (.*?);\n", page).group(1))
    return data, images


def verify(bdir: Path, out: Path) -> list[str]:
    """Read the built page back: every worldspace of the census on the switcher, every census row with coordinates
    present, the terrain over every LAND cell, the opening marker at Lilmoth. Returns the problems (empty: right)."""
    bad = []
    data, images = read_page(out)
    w = db.open()
    worlds = {r[0]: r[1] for r in w.query("SELECT editor_id, id FROM bmv_worldspace")}
    for ed in set(worlds) ^ set(data):
        bad.append(f"worldspace {ed}: in the census or on the page, not both")
    L = Load(bdir)
    land = lands(L)
    for ws, wid in sorted(worlds.items()):
        if ws not in data:
            continue
        d = data[ws]
        cnt = lambda sql: w.query(sql, wid)[0][0]  # noqa: E731
        want = {"settlements": cnt("SELECT count(*) FROM bmv_settlement WHERE worldspace = ?"),
                "doors": cnt("SELECT count(*) FROM bmv_door WHERE worldspace = ?"),
                "actors": cnt("SELECT count(*) FROM bmv_placement a JOIN bmv_cell c ON c.id = a.cell "
                              "WHERE c.worldspace = ?"),
                "cells": cnt("SELECT count(*) FROM bmv_cell WHERE worldspace = ? AND grid_x IS NOT NULL"),
                "bmvmarkers": cnt("SELECT count(*) FROM bmv_map_marker WHERE worldspace = ?")}
        for k, n in want.items():
            if len(d[k]) != n:
                bad.append(f"{ws}: {k} {len(d[k])} on the page, {n} in the db")
        t = d["terrain"]
        if set(t["land"]) != {f"{x},{y}" for x, y in land.get(wid, {})}:
            bad.append(f"{ws}: the page's LAND list differs from the files'")
        n_land = cnt("SELECT land_cells FROM bmv_worldspace WHERE id = ?")
        if len(t["land"]) != n_land:
            bad.append(f"{ws}: {len(t['land'])} LAND cells drawn, the census counts {n_land}")
        img = unpng(base64.b64decode(images[ws].split(",", 1)[1]))
        ppc = t["ppc"]
        for key in t["land"]:
            gx, gy = map(int, key.split(","))
            r0, c0 = (t["y1"] - gy) * ppc, (gx - t["x0"]) * ppc
            if not (img[r0:r0 + ppc, c0:c0 + ppc, 3] == 255).all():
                bad.append(f"{ws}: cell {key} has LAND but the terrain is not drawn there")
        for key in d["cells"]:                            # every census cell inside the drawn frame
            gx, gy = map(int, key.split(","))
            if not (t["x0"] <= gx <= t["x1"] and t["y0"] <= gy <= t["y1"]):
                bad.append(f"{ws}: cell {key} lies outside the drawn frame")
        for k in ("doors", "actors", "bmvmarkers"):    # every point inside the drawn frame
            for o in d[k]:
                gx, gy = math.floor(o["x"] / GRID), math.floor(o["y"] / GRID)
                if not (t["x0"] <= gx <= t["x1"] and t["y0"] <= gy <= t["y1"]):
                    bad.append(f"{ws}: {k} {o['id']} at {gx},{gy} lies outside the drawn frame")
        print(f"{ws}: {len(t['land'])} LAND cells drawn at {ppc} px/cell ({img.shape[1]}x{img.shape[0]}); "
              + ", ".join(f"{k} {len(d[k])}" for k in want))
    # the opening marker: on land (above the cell's water) or a dock, and in a cell of Lilmoth's settlement
    mk = [m for m in data["BlackMarsh"]["markers"] if m["edid"] == "ARG_OpeningMarker"]
    if not mk:
        bad.append("ARG_OpeningMarker is not on the BlackMarsh page")
    for m in mk:
        gx, gy = int(m["x"] // GRID), int(m["y"] // GRID)
        h, wl = land[data["BlackMarsh"]["id"]].get((gx, gy), (None, None))
        if h is None:
            bad.append(f"ARG_OpeningMarker: cell {gx},{gy} has no LAND")
            continue
        fx, fy = (m["x"] - gx * GRID) / 128, (m["y"] - gy * GRID) / 128
        ground = h[round(fy), round(fx)]
        lil = [s for s in data["BlackMarsh"]["settlements"] if s["name"] == "Lilmoth"]
        inlil = bool(lil) and any(c[0] == gx and c[1] == gy for c in lil[0]["cells"])
        print(f"ARG_OpeningMarker at {m['x']:.0f},{m['y']:.0f},{m['z']:.0f}: cell {gx},{gy}, ground {ground:.0f}, "
              f"water {wl}, in Lilmoth's cells: {inlil}")
        if wl is not None and ground < wl:
            deck = standing_on(L, m["x"], m["y"])
            print(f"  ground below the water; standing on: {deck}")
            if not deck:
                bad.append(f"ARG_OpeningMarker: ground {ground:.0f} is below the water {wl:.0f} and no dock is there")
        if not inlil:
            bad.append(f"ARG_OpeningMarker: cell {gx},{gy} is not one of Lilmoth's cells")
    return bad


def standing_on(L: Load, x: float, y: float) -> str | None:
    """The editor id of a dock or pier static (BM&V's or a master's) whose footprint holds (x, y), if any."""
    bases = {}
    for m in MASTER_FILES:
        mp = MASTERS / m
        if mp.exists():
            bases.update({r.key: r for r in esm.Plugin.read(mp, {"STAT"}).records("STAT")})
    bases.update({r.key: r for r in L.live("STAT")})
    for r in L.live("REFR"):
        d, b = r.sub("DATA"), bases.get(r.ref("NAME"))
        if not d or not b or not re.search(r"dock|pier", b.edid or "", re.I) or not b.sub("OBND"):
            continue
        rx, ry, _z, _ax, _ay, az = struct.unpack_from("<6f", d)
        if abs(rx - x) > 3000 or abs(ry - y) > 3000:
            continue
        x0, y0, _, x1, y1, _ = struct.unpack("<6h", b.sub("OBND"))
        sc = struct.unpack_from("<f", r.sub("XSCL"))[0] if r.sub("XSCL") else 1.0
        dx, dy = (x - rx) / sc, (y - ry) / sc
        lx, ly = dx * math.cos(az) - dy * math.sin(az), dx * math.sin(az) + dy * math.cos(az)
        if x0 <= lx <= x1 and y0 <= ly <= y1:
            return f"{b.edid} ({r.key})"
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "verify"])
    ap.add_argument("--dir", type=Path, default=DIR)
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args(argv)
    if a.cmd == "build":
        print(json.dumps(build(a.dir, a.out)), a.out)
        return 0
    bad = verify(a.dir, a.out)
    for b in bad:
        print("BAD", b)
    print("MAP GREEN" if not bad else f"MAP RED: {len(bad)} problems")
    return 1 if bad else 0


TEMPLATE = (Path(__file__).with_name("page.html")).read_text()

if __name__ == "__main__":
    sys.exit(main())
