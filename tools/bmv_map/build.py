"""The offline BM&V map (phase 1): one self-contained HTML page, out/bmv-map/index.html, of BM&V's two worldspaces
(BlackMarsh, BlackMarsh2). The land is drawn from Black Marsh.esm's own LAND height grids (hillshade, and water where
the land lies below the cell's water); the census tables (bmv_* through tools/argonia_world/db.py), place_bmv and our
markers in plugin/Argonia sit on top as layers. The page and its terrain are derived from BM&V's files, so they live
under out/ and are never committed (decision 0003). Rerunning rewrites the page whole.

    python3 -m tools.bmv_map.build build  [--esm PATH] [--out out/bmv-map/index.html]   # `make map`
    python3 -m tools.bmv_map.build verify [--out ...]   # read the built page back and check it against the db and ESM
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
from tools.argonia_world.bmv_census import ESM, MASTERS, GRID, cell_of, is_interior, world_of

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out/bmv-map/index.html"
WORLDS = ("BlackMarsh", "BlackMarsh2")
PLUGIN = ROOT / "plugin/Argonia/Worldspaces"
BUDGET = 13_000_000          # bytes of base64 terrain across both worlds; the page stays under ~15 MB
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


def lands(p: esm.Plugin, wid: dict[int, str]) -> dict[str, dict[tuple[int, int], tuple[np.ndarray, float | None]]]:
    """Per worldspace editor id: (grid x, grid y) -> (33x33 heights, water height or None when the cell has none)."""
    default = {}
    for w in p.records("WRLD"):
        if w.formid in wid:
            dn = w.sub("DNAM")
            default[w.formid] = struct.unpack_from("<f", dn, 4)[0] if dn else 0.0
    cells = {}
    for c in p.records("CELL"):
        wf = world_of(c)
        if wf in wid and not is_interior(c) and c.sub("XCLC"):
            gx, gy = struct.unpack_from("<ii", c.sub("XCLC"))
            d = c.sub("DATA")
            has = bool(d and d[0] & 2)
            xw = c.sub("XCLW")
            wl = struct.unpack_from("<f", xw)[0] if xw else NO_WATER * 2
            if wl > NO_WATER:
                wl = default[wf]
            cells[c.formid] = (wid[wf], gx, gy, wl if has else None)
    out: dict = defaultdict(dict)
    for r in p.records("LAND"):
        cf = cell_of(r)
        d = r.sub("VHGT")
        if cf in cells and d:
            ws, gx, gy, wl = cells[cf]
            out[ws][(gx, gy)] = (vhgt(d), wl)
    return out


def terrain(cells: dict, ppc: int) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """The RGBA image of one worldspace at `ppc` pixels per cell, and its grid bounds (x0, y0, x1, y1) inclusive."""
    xs = [g[0] for g in cells]
    ys = [g[1] for g in cells]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    n = 32
    W, H = (x1 - x0 + 1) * n, (y1 - y0 + 1) * n
    hgt = np.full((H, W), np.nan)
    wat = np.full((H, W), np.nan)
    for (gx, gy), (h, wl) in cells.items():
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
    worlds = {r["editor_id"]: r for r in q("SELECT * FROM bmv_worldspace WHERE editor_id IN (?, ?)", *WORLDS)}
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

    def label(cid):
        c = cells.get(cid)
        return (c["name"] or c["editor_id"] or cid) if c else cid

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
                      "interiors": sorted(label(k) for k in sc if cells[k]["interior"]),
                      "npcs": sorted(s_npcs[s["id"]]), "places": place_of[s["id"]]})
        D = []
        for d in doors.values():
            if d["worldspace"] != wid:
                continue
            t = doors.get(d["target"]) if d["target"] else None
            to = {"elsewhere": d["target_elsewhere"]}
            if t:
                tc = cells[t["cell"]]
                to = {"door": t["id"], "cell": t["cell"], "label": label(t["cell"]),
                      "interior": bool(tc["interior"]), "ws": t["worldspace"], "x": t["x"], "y": t["y"]}
                m = member.get(t["cell"])
                if m:
                    to["settlement"] = sett[m["settlement"]]["name"]
            D.append({"id": d["id"], "x": d["x"], "y": d["y"], "z": d["z"], "cell": d["cell"],
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
                P.append({**p, "gx": c["grid_x"], "gy": c["grid_y"], "at": label(c["id"])})
        M = [m for m in markers() if m["ws"] == wid]
        out[ed] = {"id": wid, "name": wr["name"], "settlements": S, "doors": D, "actors": A, "cells": C,
                   "places": P, "markers": M, "waiting": [p for p in places if p["status"] == "waiting"]}
    return out


# --- the page ---------------------------------------------------------------------------------------------------------

def build(esm_path: Path, out: Path) -> dict:
    p = esm.Plugin.read(esm_path)
    wid = {w.formid: w.edid for w in p.records("WRLD") if w.edid in WORLDS and w.own}
    land = lands(p, wid)
    data = layers(db.open())
    for ppc in (32, 16, 8, 4):
        imgs = {ws: terrain(land[ws], ppc) for ws in WORLDS}
        uris = {ws: base64.b64encode(png(im)).decode() for ws, (im, _) in imgs.items()}
        if sum(map(len, uris.values())) <= BUDGET:
            break
    for ws, (im, (x0, y0, x1, y1)) in imgs.items():
        data[ws]["terrain"] = {"ppc": ppc, "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                               "land": sorted(f"{x},{y}" for x, y in land[ws])}
    page = TEMPLATE.replace("/*DATA*/null", json.dumps(data, separators=(",", ":")).replace("</", "<\\/")).replace(
        "/*IMAGES*/null", json.dumps({ws: "data:image/png;base64," + u for ws, u in uris.items()}))
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    tmp.write_text(page)
    tmp.replace(out)
    return {"ppc": ppc, "bytes": len(page.encode()), **{ws: len(land[ws]) for ws in WORLDS}}


def read_page(out: Path) -> tuple[dict, dict]:
    page = out.read_text()
    data = json.loads(re.search(r"const DATA = (.*?);\n", page).group(1))
    images = json.loads(re.search(r"const IMAGES = (.*?);\n", page).group(1))
    return data, images


def verify(esm_path: Path, out: Path) -> list[str]:
    """Read the built page back: every census row with coordinates present, the terrain over every LAND cell, the
    opening marker on land at Lilmoth. Returns the problems (empty: the map is right)."""
    bad = []
    data, images = read_page(out)
    w = db.open()
    for ws in WORLDS:
        d = data[ws]
        wid = d["id"]
        cnt = lambda sql: w.query(sql, wid)[0][0]  # noqa: E731
        want = {"settlements": cnt("SELECT count(*) FROM bmv_settlement WHERE worldspace = ?"),
                "doors": cnt("SELECT count(*) FROM bmv_door WHERE worldspace = ?"),
                "actors": cnt("SELECT count(*) FROM bmv_placement a JOIN bmv_cell c ON c.id = a.cell "
                              "WHERE c.worldspace = ?"),
                "cells": cnt("SELECT count(*) FROM bmv_cell WHERE worldspace = ? AND grid_x IS NOT NULL")}
        for k, n in want.items():
            if len(d[k]) != n:
                bad.append(f"{ws}: {k} {len(d[k])} on the page, {n} in the db")
        t = d["terrain"]
        img = unpng(base64.b64decode(images[ws].split(",", 1)[1]))
        ppc = t["ppc"]
        for key in t["land"]:
            gx, gy = map(int, key.split(","))
            r0, c0 = (t["y1"] - gy) * ppc, (gx - t["x0"]) * ppc
            if not (img[r0:r0 + ppc, c0:c0 + ppc, 3] == 255).all():
                bad.append(f"{ws}: cell {key} has LAND but the terrain is not drawn there")
        print(f"{ws}: {len(t['land'])} LAND cells drawn at {ppc} px/cell ({img.shape[1]}x{img.shape[0]}); "
              + ", ".join(f"{k} {len(d[k])}" for k in want))
    # the opening marker: on land (above the cell's water) and in a cell of Lilmoth's settlement
    p = esm.Plugin.read(esm_path)
    wid = {x.formid: x.edid for x in p.records("WRLD") if x.edid in WORLDS and x.own}
    land = lands(p, wid)
    mk = [m for m in data["BlackMarsh"]["markers"] if m["edid"] == "ARG_OpeningMarker"]
    if not mk:
        bad.append("ARG_OpeningMarker is not on the BlackMarsh page")
    for m in mk:
        gx, gy = int(m["x"] // GRID), int(m["y"] // GRID)
        h, wl = land["BlackMarsh"].get((gx, gy), (None, None))
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
            deck = standing_on(p, m["x"], m["y"])
            print(f"  ground below the water; standing on: {deck}")
            if not deck:
                bad.append(f"ARG_OpeningMarker: ground {ground:.0f} is below the water {wl:.0f} and no dock is there")
        if not inlil:
            bad.append(f"ARG_OpeningMarker: cell {gx},{gy} is not one of Lilmoth's cells")
    return bad


def standing_on(p: esm.Plugin, x: float, y: float) -> str | None:
    """The editor id of a dock or pier static (BM&V's or a master's) whose footprint holds (x, y), if any."""
    bases = {}
    for m in p.masters:
        mp = MASTERS / m
        if mp.exists():
            bases.update({r.key: r for r in esm.Plugin.read(mp, {"STAT"}).records("STAT")})
    bases.update({r.key: r for r in p.records("STAT")})
    for r in p.records("REFR"):
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
    ap.add_argument("--esm", type=Path, default=ESM)
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args(argv)
    if a.cmd == "build":
        print(json.dumps(build(a.esm, a.out)), a.out)
        return 0
    bad = verify(a.esm, a.out)
    for b in bad:
        print("BAD", b)
    print("MAP GREEN" if not bad else f"MAP RED: {len(bad)} problems")
    return 1 if bad else 0


TEMPLATE = (Path(__file__).with_name("page.html")).read_text()

if __name__ == "__main__":
    sys.exit(main())
