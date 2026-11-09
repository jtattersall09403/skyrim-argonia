"""Build the place layer: place files -> out/places/plugin/ArgoniaNWPlaces.esp (docs/design/place-studio.md, Build).

    python -m tools.places build [place_id ...] [--places DIR] [--out DIR] [--no-navmesh] [--force]

No place id: every place directory that has a place.json. Each place is planned into one shard,
`<out>/shards/<place_id>/plan.json`, keyed on its place files, the world ESM's sha256 and this code; a shard whose
key holds is not planned again. Then every shard on disk is assembled into the one plugin by
tools/ArgoniaPlaces/Build (`write`), mastered on ArgoniaNewWorld.esm, which is read and never written.

The plan is the place made explicit, with every decision taken here and nothing left to the writer:
  refs        every placed ref of the place as a new ref of ours (exterior: in the world's own cell, or in the
              world's persistent cell when persistent; interior: in our copy of the source cell)
  interiors   our copies of source cells (header from the source; refs from the source plus our changes)
  doors       each load door paired both ways; the arrival marker of a copied door moved with its exterior door
  land        LAND overrides (VHGT and VNML) for the cells a land patch changes, and path texture layers
  clear       the world's refs matched from clear.jsonl, switched off (Initially Disabled)
  people      actor bases, placed actors, packages, factions, services (people.py's plan, below)
  navmesh     the touched exterior cells and their ring regenerated with tools.navmesh over the patched land and the
              place's collision; interiors' navmesh copied (trimmed to the kept room); door triangles both sides
Form ids are stable for life: newworld/places/<place_id>/formids.json (committed beside the place files) maps each of
our keys to its id; newworld/places/formid_blocks.json gives each place its own block.
"""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PLACES = ROOT / "newworld" / "places"
OUT = ROOT / "out" / "places"
WORLD_DIR = ROOT / "out" / "newworld" / "plugin"
WORLD_ESM = WORLD_DIR / "ArgoniaNewWorld.esm"
WORLD_NAV = WORLD_DIR / "navmesh"
TOOL_PROJ = ROOT / "tools" / "ArgoniaPlaces" / "Build"
TOOL_DIR = ROOT / "out" / "tools" / "ArgoniaPlacesBuild"
TOOL = TOOL_DIR / "ArgoniaPlacesBuild.dll"
DB = ROOT / "newworld" / "story" / "data" / "db"

PLUGIN = "ArgoniaNWPlaces.esp"
WORLD = "ArgoniaNewWorld.esm"
# The masters our navmesh bytes are written against (index = position; our own records one past them); the
# world's stitched NAVMs use Skyrim.esm = 0 and the world = 1 already, so their bytes carry over unchanged.
NAV_MASTERS = ["Skyrim.esm", WORLD]
NAV_SELF = len(NAV_MASTERS)
NAVI_FID = 0x012FB4  # Skyrim.esm's NAVI: every plugin registers its navmeshes by overriding it with its own NVMI
BLOCK_FIRST, BLOCK_SIZE = 0x10000, 0x8000  # place n's ids: BLOCK_FIRST + n * BLOCK_SIZE onward
CELL, VERTS, QUAD = 4096, 33, 128
CLEAR_TOL = 64.0  # units in plan: a clear row matches the world's ref of its base nearest it, within this
DOOR_MARKER_UNITS = 128.0  # a new door's arrival marker: this far in front of it (Skyrim's door markers sit 64-160 out)
SOLID_KINDS = {"building", "static", "furniture", "door", "container", "rock", "tree", "activator", "clutter"}
PERSISTENT_KINDS = {"door"}
PATH_STYLE_LTEX = {"road": "dirt_road", "street": "dirt_road", "path": "dirt_road", "track": "dirt_grass",
                   "skirt": "road_skirt", "mud": "swamp_mud", "sand": "sand", "stone": "rock"}
ROOM_RADIUS = 1200.0  # units: a `room` of a shared source cell keeps the source refs this near its room ref
PATH_FEATHER = 96.0  # units beyond the half width over which a path's opacity falls to 0
NAV_RING = 3  # the navmesh window: the touched cells plus this many rings (ring 1 overridden, ring 2 must match)
DOTNET_ENV = dict(os.environ, DOTNET_ROOT=str(Path.home() / ".dotnet"), DOTNET_NOLOGO="1", DOTNET_CLI_TELEMETRY_OPTOUT="1",
                  PATH=f"{Path.home() / '.dotnet'}:{os.environ.get('PATH', '')}")


def log(*a):
    print(*a, file=sys.stderr, flush=True)


# ---- small helpers ------------------------------------------------------------------------------------------------

def jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()] if p.exists() else []


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def atomic_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=None, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, p)


def key_of(plugin: str, local: int) -> str:
    return f"{plugin}:{local:06X}"


def split_key(k: str) -> tuple[str, int]:
    f, i = k.rsplit(":", 1)
    return f, int(i, 16)


def cell_of(x: float, y: float) -> tuple[int, int]:
    return int(math.floor(x / CELL)), int(math.floor(y / CELL))


def rotation(rx: float, ry: float, rz: float) -> np.ndarray:
    from tools.navmesh.placed import rotation as r  # the one rotation the navmesh collision also uses
    return r(rx, ry, rz)


def angles(m: np.ndarray) -> list[float]:
    """The inverse of rotation(): rotation() = Rx(-x) Ry(-y) Rz(-z), so with A, B, C = -x, -y, -z:
    m[0,2] = sin B, m[1,2] = -sin A cos B, m[2,2] = cos A cos B, m[0,1] = -cos B sin C, m[0,0] = cos B cos C."""
    B = math.asin(float(np.clip(m[0, 2], -1.0, 1.0)))
    if abs(math.cos(B)) > 1e-6:
        A = math.atan2(-m[1, 2], m[2, 2])
        C = math.atan2(-m[0, 1], m[0, 0])
    else:
        A, C = 0.0, math.atan2(m[1, 0], m[1, 1])
    return [-A, -B, -C]


def transform(pos, rot, at) -> np.ndarray:
    return np.asarray(pos, float) + rotation(*rot) @ np.asarray(at, float)


def relative_move(src_pos, src_rot, our_pos, our_rot, p, r) -> tuple[list[float], list[float]]:
    """Point p with angles r, rigidly attached to the source ref, carried to our ref's frame."""
    R0, R1 = rotation(*src_rot), rotation(*our_rot)
    local = R0.T @ (np.asarray(p, float) - np.asarray(src_pos, float))
    q = R1 @ local + np.asarray(our_pos, float)
    m = R1 @ R0.T @ rotation(*r)
    return [float(v) for v in q], angles(m)


# ---- the tool -----------------------------------------------------------------------------------------------------

def build_tool() -> None:
    r = subprocess.run(["dotnet", "build", str(TOOL_PROJ), "-c", "Release", "-o", str(TOOL_DIR), "-nologo", "-v", "q"],
                       env=DOTNET_ENV, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"build: the C# tool did not build\n{(r.stdout + r.stderr)[-3000:]}")


def tool(*args: str) -> None:
    r = subprocess.run(["dotnet", str(TOOL), *args], env=DOTNET_ENV, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"ArgoniaPlacesBuild {args[0]} failed\n{(r.stdout + r.stderr)[-4000:]}")
    if r.stdout.strip():
        log(r.stdout.strip())


def code_key() -> str:
    h = hashlib.sha256()
    for p in sorted([Path(__file__), Path(__file__).with_name("people.py")] + list(TOOL_PROJ.glob("*.cs"))):
        if p.exists():
            h.update(p.name.encode() + p.read_bytes())
    return h.hexdigest()[:16]


# ---- form ids -------------------------------------------------------------------------------------------------------

class Ids:
    """Our keys -> form ids, stable for life: newworld/places/<place>/formids.json, the place's block from
    <places>/formid_blocks.json. A key never seen gets the next id of the block; nothing is ever renumbered."""

    def __init__(self, places: Path, place_id: str):
        self.blocks_path = places / "formid_blocks.json"
        blocks = json.loads(self.blocks_path.read_text()) if self.blocks_path.exists() else {}
        if place_id not in blocks:
            blocks[place_id] = max(blocks.values(), default=-1) + 1
            atomic_json(self.blocks_path, blocks)
        self.first = BLOCK_FIRST + blocks[place_id] * BLOCK_SIZE
        if self.first + BLOCK_SIZE > 0xFFFFFF:
            raise SystemExit("form id blocks exhausted")
        self.path = places / place_id / "formids.json"
        self.ids: dict[str, int] = json.loads(self.path.read_text()) if self.path.exists() else {}
        self.used: set[str] = set()

    def __call__(self, key: str) -> str:
        self.used.add(key)
        if key not in self.ids:
            n = len(self.ids)
            if n >= BLOCK_SIZE:
                raise SystemExit(f"form id block full for {self.path}")
            self.ids[key] = self.first + n
        return key_of(PLUGIN, self.ids[key])

    def local(self, key: str) -> int:
        self(key)
        return self.ids[key]

    def save(self) -> None:
        atomic_json(self.path, self.ids)


# ---- inputs ---------------------------------------------------------------------------------------------------------

def read_place(pdir: Path) -> dict:
    spaces = {}
    sp = pdir / "spaces"
    for d in sorted(sp.iterdir()) if sp.is_dir() else []:
        if d.is_dir():
            spaces[d.name] = {"space": json.loads((d / "space.json").read_text()) if (d / "space.json").exists() else {},
                              "refs": jsonl(d / "refs.jsonl")}
    return {"place": json.loads((pdir / "place.json").read_text()), "spaces": spaces,
            "people": jsonl(pdir / "people.jsonl"), "clear": jsonl(pdir / "clear.jsonl"),
            "land": jsonl(pdir / "land.jsonl"), "paths": jsonl(pdir / "paths.jsonl")}


def place_key(pdir: Path, world_sha: str) -> str:
    h = hashlib.sha256((world_sha + code_key()).encode())
    for p in sorted(pdir.rglob("*")):
        if p.is_file() and p.name != "formids.json" and "edits" not in p.parts:
            h.update(str(p.relative_to(pdir)).encode() + p.read_bytes())
    return h.hexdigest()


def sources() -> dict:
    return {r["source_id"]: r for r in jsonl(PLACES / "sources.jsonl")}


def resolve_copy(copy_of: str) -> tuple[str, str]:
    """`<source_id>/<cell edid>` -> (plugin file, cell edid). A source id names its plugins in sources.jsonl; a prefix
    that is itself a plugin file name is taken as that plugin (fixtures)."""
    src, cell = copy_of.split("/", 1)
    if src.lower().endswith((".esm", ".esp", ".esl")):
        return src, cell
    row = sources().get(src)
    if not row:
        raise SystemExit(f"copy_of {copy_of}: source {src} is not in newworld/places/sources.jsonl")
    sj = OUT / "bundles" / f"src.{src}" / "spaces" / cell / "space.json"
    if sj.exists():  # the extractor's own record of where the cell is (its key, in whichever plugin of the source)
        b = json.loads(sj.read_text())
        return "|".join(dict.fromkeys([b["plugin"]] + row["plugins"] + row.get("extra_refs_plugins", []))), b["key"]
    return "|".join(row["plugins"] + row.get("extra_refs_plugins", [])), cell


# ---- world facts ----------------------------------------------------------------------------------------------------

def world_facts(cells: set, tmp: Path) -> dict:
    req = tmp / "world_req.json"
    out = tmp / "world.json"
    atomic_json(req, {"cells": sorted([list(c) for c in cells])})
    tool("world", str(WORLD_ESM), str(req), str(out))
    w = json.loads(out.read_text())
    req.unlink()
    out.unlink()
    w["by_cell"] = {(c["x"], c["y"]): c for c in w["cells"]}
    return w


def cell_steps(c: dict) -> np.ndarray:
    from tools.newworld.world import quantize
    d = np.frombuffer(base64.b64decode(c["deltas"]), np.int8).reshape(VERTS, VERTS)
    return quantize.decode(float(c["offset"]), d)  # [y from south, x]


# ---- land -----------------------------------------------------------------------------------------------------------

def plan_land(rows: list[dict], facts: dict) -> tuple[list[dict], dict, set]:
    """Land patches -> LAND overrides: heights (VHGT) and normals (VNML) of every cell whose heights or normals the
    patches change. Returns (overrides, patched global vertex steps {(gx, gy): steps}, changed cells)."""
    from tools.newworld.world import land as nwland, quantize
    if not rows:
        return [], {}, set()
    target: dict[tuple[int, int], int] = {}
    for r in rows:
        cx, cy = r["cell"]
        base = cell_steps(facts["by_cell"][(cx, cy)])
        for row, col, dz in r["verts"]:
            gx, gy = cx * 32 + int(col), cy * 32 + int(row)  # global vertex index: x east, y north
            v = int(round(base[int(row), int(col)] + dz / 8.0))
            if target.get((gx, gy), v) != v:
                raise SystemExit(f"land.jsonl: vertex {gx},{gy} patched to two heights")
            target[(gx, gy)] = v
    xs = [k[0] for k in target]
    ys = [k[1] for k in target]
    # window: the cells the patched vertices touch, plus a ring for the normals
    c0x, c1x = (min(xs) - 1) // 32 - 1, max(xs) // 32 + 1
    c0y, c1y = (min(ys) - 1) // 32 - 1, max(ys) // 32 + 1
    nx, ny = (c1x - c0x + 1) * 32 + 1, (c1y - c0y + 1) * 32 + 1
    win = np.full((ny, nx), np.nan)  # [y from south, x]
    for cx in range(c0x, c1x + 1):
        for cy in range(c0y, c1y + 1):
            c = facts["by_cell"].get((cx, cy))
            if c is None or c.get("deltas") is None:
                continue
            ox, oy = (cx - c0x) * 32, (cy - c0y) * 32
            win[oy:oy + VERTS, ox:ox + VERTS] = cell_steps(c)
    before = np.nan_to_num(win, nan=0.0)
    after = before.copy()
    for (gx, gy), v in target.items():
        after[gy - c0y * 32, gx - c0x * 32] = v
    # normals as the world computes them (land.normals: row 0 north)
    nb = nwland.normals(before[::-1].astype(np.int64))[::-1]
    na = nwland.normals(after[::-1].astype(np.int64))[::-1]
    out, changed = [], set()
    for cx in range(c0x + 1, c1x):
        for cy in range(c0y + 1, c1y):
            ox, oy = (cx - c0x) * 32, (cy - c0y) * 32
            sl = (slice(oy, oy + VERTS), slice(ox, ox + VERTS))
            if np.array_equal(before[sl], after[sl]) and np.array_equal(nb[sl], na[sl]):
                continue
            c = facts["by_cell"].get((cx, cy))
            if c is None or c.get("land") is None:
                raise SystemExit(f"land patch reaches cell {cx},{cy}, which has no LAND in the world")
            offset, d = quantize.encode(after[sl].astype(np.int64))
            out.append({"x": cx, "y": cy, "land": c["land"], "heights": {
                "offset": offset, "deltas": base64.b64encode(d.tobytes()).decode(),
                "normals": base64.b64encode(np.ascontiguousarray(na[sl]).astype(np.int8).tobytes()).decode()}})
            changed.add((cx, cy))
    return out, target, changed


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = np.clip(((px - ax) * dx + (py - ay) * dy) / L, 0, 1) if L else 0.0
    return np.hypot(px - (ax + t * dx), py - (ay + t * dy))


def plan_paths(paths: list[dict], facts: dict) -> dict[tuple[int, int], list[dict]]:
    """Paths -> texture layers: per cell quadrant one alpha layer of the world's own LTEX for the path's style,
    opacity 1 within the half width and feathered beyond it (the way Skyrim's roads are painted)."""
    ltex = {t["edid"]: t["fk"] for t in facts["ltex"]}
    layers: dict[tuple[int, int], list[dict]] = {}
    for p in paths:
        want = PATH_STYLE_LTEX.get(p.get("style") or p.get("kind") or "path", "dirt_road")
        tex = next((fk for e, fk in ltex.items() if e and e.lower().endswith(want)), None)
        if tex is None:
            raise SystemExit(f"path {p['id']}: no world land texture for style {p.get('style')!r} (*{want})")
        pts = np.asarray(p["points"], float)
        half = float(p.get("width", 256)) / 2
        reach = half + PATH_FEATHER
        lo, hi = pts.min(axis=0) - reach, pts.max(axis=0) + reach
        for cx in range(cell_of(*lo)[0], cell_of(*hi)[0] + 1):
            for cy in range(cell_of(*lo)[1], cell_of(*hi)[1] + 1):
                gx = cx * CELL + np.arange(VERTS) * QUAD
                gy = cy * CELL + np.arange(VERTS) * QUAD
                X, Y = np.meshgrid(gx, gy)  # [y, x]
                d = np.full(X.shape, np.inf)
                for a, b in zip(pts[:-1], pts[1:]):
                    d = np.minimum(d, seg_dist(X, Y, a[0], a[1], b[0], b[1]))
                op = np.clip(1 - (d - half) / PATH_FEATHER, 0, 1)
                if not (op > 0).any():
                    continue
                for q, (y0, x0) in enumerate(((0, 0), (0, 16), (16, 0), (16, 16))):  # BL, BR, TL, TR
                    sub = op[y0:y0 + 17, x0:x0 + 17]
                    alpha = [[int(i), round(float(sub.flat[i]), 4)] for i in np.flatnonzero(sub > 0)]
                    if alpha:
                        layers.setdefault((cx, cy), []).append({"quadrant": q, "texture": tex, "alpha": alpha, "path": p["id"]})
    return layers


# ---- clearance ------------------------------------------------------------------------------------------------------

def plan_clear(rows: list[dict], facts: dict) -> list[dict]:
    out, taken = [], set()
    for r in rows:
        x, y = r["pos"][0], r["pos"][1]
        cx, cy = cell_of(x, y)
        best, bd = None, CLEAR_TOL
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for ref in (facts["by_cell"].get((cx + dx, cy + dy)) or {}).get("refs", []):
                    if ref.get("base") != r["base"] or ref["fk"] in taken or "pos" not in ref:
                        continue
                    d = math.hypot(ref["pos"][0] - x, ref["pos"][1] - y)
                    if d <= bd:
                        best, bd = ref, d
        if best is None:
            raise SystemExit(f"clear.jsonl: no world ref of {r['base']} within {CLEAR_TOL:.0f} units of {x:.0f},{y:.0f}")
        taken.add(best["fk"])
        out.append({"fk": best["fk"], "base": best["base"], "pos": best["pos"], "cell": list(cell_of(*best["pos"][:2]))})
    return out


# ---- refs, interiors, doors -----------------------------------------------------------------------------------------

def norm_ref(r: dict) -> dict:
    r = dict(r)
    r.setdefault("rot", [0.0, 0.0, 0.0])
    r.setdefault("scale", 1.0)
    return r


def plan_spaces(P: dict, ids: Ids, tmp: Path) -> dict:
    """Every space's refs as rows of ours; interiors with their copied header and navmesh source."""
    refs, interiors, by_our = [], [], {}
    for sid, S in P["spaces"].items():
        if sid == "exterior":
            for r in map(norm_ref, S["refs"]):
                if r.get("removed"):
                    continue
                row = {**r, "fk": ids(f"ref:{r['id']}"), "space": "exterior", "cell": list(cell_of(*r["pos"][:2])),
                       "persistent": "persistent" in (r.get("flags") or []) or bool(r.get("persistent"))}
                row.pop("flags", None)
                refs.append(row)
                by_our[r["id"]] = row
            continue
        sp = S["space"]
        plugin, cell_edid = resolve_copy(sp["copy_of"]) if sp.get("copy_of") else (None, None)
        src_rows = []
        src = {}
        if plugin:
            out = tmp / f"src_{sid}.json"
            got = []  # the cell as each of the source's plugins has it: a cell's refs may come from several
            for cand in plugin.split("|"):
                try:
                    tool("source", cand, cell_edid, str(out))
                except SystemExit:
                    continue
                got.append((cand, json.loads(out.read_text())))
                out.unlink()
            if not got:
                raise SystemExit(f"space {sid}: no plugin of {sp['copy_of']} holds an interior cell {cell_edid}")
            plugin, src = got[0]
            seen = {r["fk"] for r in src["refs"]}
            for _, more in got[1:]:
                src["refs"] += [r for r in more["refs"] if r["fk"] not in seen]
                src["navmesh"] += more["navmesh"]
            keep = sp.get("keep_within")
            if not keep and sp.get("room"):  # one room of a cell the source shares between houses: the refs round it
                rr = next((r for r in src["refs"] if r["fk"] == sp["room"] and "pos" in r), None)
                if rr is not None:
                    keep = {"pos": rr["pos"], "radius": ROOM_RADIUS}
                    sp["keep_within"] = keep
            for r in src["refs"]:
                if "pos" not in r or r.get("deleted") or r.get("base_type") in ("NPC_", "LVLN"):
                    continue  # people are ours (people.jsonl), never the source's
                if keep and math.dist(r["pos"], keep["pos"]) > keep["radius"]:
                    continue
                src_rows.append(r)
        kept = {r["fk"] for r in src_rows}
        changes = {r["src"]: r for r in S["refs"] if r.get("src") and (not plugin or r["src"] in kept)}
        fk_of_src = {}
        for r in src_rows:
            ch = changes.get(r["fk"], {})
            if ch.get("removed"):
                continue
            our_id = ch.get("id") or f"{sid}/{r['fk']}"
            row = {"id": our_id, "src": r["fk"], "base": ch.get("base", r["base"]), "kind": ch.get("kind", kind_of(r)),
                   "pos": ch.get("pos", r["pos"]), "rot": ch.get("rot", r["rot"]), "scale": ch.get("scale", r.get("scale", 1.0)),
                   "src_flags": r.get("flags", 0), "src_door": r.get("door"), "src_linked": r.get("linked"),
                   "src_enable_parent": r.get("enable_parent"), "lock": ch.get("lock", r.get("lock")),
                   "owner": ch.get("owner"), "door": ch.get("door"), "seat": ch.get("seat"), "persistent": bool(r.get("persistent"))}
            row.update({"fk": ids(f"ref:{our_id}"), "space": sid})
            refs.append(row)
            by_our[our_id] = row
            fk_of_src[r["fk"]] = row["fk"]
        for r in map(norm_ref, S["refs"]):
            if r.get("removed") or (r.get("src") and (not plugin or r["src"] in kept)):
                continue
            if r.get("src") and plugin:
                continue  # a row of a source ref outside the kept room: not in this copy
            row = {**r, "fk": ids(f"ref:{r['id']}"), "space": sid}
            refs.append(row)
            by_our[r["id"]] = row
        # source links within the copy follow the copy; links out of it are dropped
        for row in refs:
            if row["space"] != sid or not row.get("src"):
                continue
            row["linked"] = [{"ref": fk_of_src[x["ref"]], "keyword": x["keyword"]} for x in row.pop("src_linked") or []
                             if x["ref"] in fk_of_src]
            ep = row.pop("src_enable_parent")
            if ep in fk_of_src:
                row["enable_parent"] = fk_of_src[ep]
        interiors.append({"space": sid, "fk": ids(f"space:{sid}"), "edid": f"ANP_{sid}",
                          "name": sp.get("name") or src.get("name") or sid, "copy": {"plugin": plugin, "cell": src.get("fk")} if plugin else None,
                          "light": sp.get("light"), "owner": sp.get("owner"), "keep_within": sp.get("keep_within"),
                          "src_navmesh": [n["fk"] for n in src.get("navmesh", [])], "fk_of_src": fk_of_src})
    return {"refs": refs, "interiors": interiors, "by_id": by_our}


def kind_of(r: dict) -> str:
    return {"STAT": "static", "DOOR": "door", "FURN": "furniture", "CONT": "container", "LIGH": "light", "ACTI": "activator",
            "MSTT": "static", "FLOR": "plant", "TREE": "tree", "IDLM": "marker"}.get(r.get("base_type", ""), "clutter")


def pair_doors(S: dict) -> list[str]:
    """Each load door's teleport and arrival marker, both ways. A place door names its partner by
    door.to_space + door.to_ref (the partner's id, or its source ref key in a copied space); the partner's own
    door field may be absent (it is paired from this side)."""
    by_id = S["by_id"]
    by_src = {(r["space"], r.get("src")): r for r in S["refs"] if r.get("src")}
    notes, pairs = [], []
    for r in S["refs"]:
        d = r.get("door")
        if not d or not d.get("to_space"):
            continue
        other = by_id.get(d["to_ref"]) or by_src.get((d["to_space"], d["to_ref"]))
        if other is None:
            raise SystemExit(f"door {r['id']}: partner {d['to_space']}/{d['to_ref']} is not in the place")
        pairs.append((r, other))
    paired = set()
    for a, b in pairs:
        for x, y in ((a, b), (b, a)):
            x["teleport"] = {"to": y["fk"], **marker_by(y, x)}
            x["persistent"] = True
            paired.add(x["fk"])
    for r in S["refs"]:
        if r.get("src_door") and r["fk"] not in paired:
            notes.append(f"door {r['id']}: the source's load door has no partner in the place; built as a plain door")
    for r in S["refs"]:
        r.pop("src_door", None)
    return notes


def marker_by(door: dict, partner: dict) -> dict:
    """The arrival marker standing by `door` (where one lands using `partner`).
    - `door` is a copy of a source load door: the marker its source partner's teleport named (copies keep their frame);
    - `partner` is a copy of a source load door: the source's marker by the source partner, moved rigidly from that
      source door to `door` (our door stands in for it);
    - else DOOR_MARKER_UNITS in front of the door (its local -Y), facing away from it."""
    sd = door.get("src_door") or {}
    if sd.get("partner_to_pos") is not None:
        return {"pos": sd["partner_to_pos"], "rot": sd["partner_to_rot"]}
    sp = partner.get("src_door") or {}
    if sp.get("partner_pos") is not None:
        p, q = relative_move(sp["partner_pos"], sp["partner_rot"], door["pos"], door["rot"], sp["to_pos"], sp["to_rot"])
        return {"pos": p, "rot": q}
    fwd = rotation(*door["rot"]) @ np.array([0.0, -DOOR_MARKER_UNITS, 0.0])
    p = np.asarray(door["pos"], float) + fwd
    return {"pos": [float(v) for v in p], "rot": [0.0, 0.0, float(door["rot"][2]) + math.pi]}


# ---- navmesh --------------------------------------------------------------------------------------------------------

def raw_fid(index: int, local: int) -> int:
    return (index << 24) | local


def nav_fid(key: str) -> int:
    f, local = split_key(key)
    if f == PLUGIN:
        return raw_fid(NAV_SELF, local)
    if f in NAV_MASTERS:
        return raw_fid(NAV_MASTERS.index(f), local)
    raise SystemExit(f"navmesh: {key} is in no master of the navmesh contract ({NAV_MASTERS})")


def tri_under(n, p) -> int:
    """The triangle whose plan contains p (nearest centroid in plan and height when none contains it)."""
    v = n.verts
    best, bd = -1, float("inf")
    for i, t in enumerate(n.tris["v"]):
        a, b, c = v[t[0]], v[t[1]], v[t[2]]
        d1 = (p[0] - b[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (p[1] - b[1])
        d2 = (p[0] - c[0]) * (b[1] - c[1]) - (b[0] - c[0]) * (p[1] - c[1])
        d3 = (p[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (p[1] - a[1])
        inside = not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))
        zc = (a[2] + b[2] + c[2]) / 3
        cen = ((a[0] + b[0] + c[0]) / 3, (a[1] + b[1] + c[1]) / 3)
        d = (0 if inside else math.hypot(cen[0] - p[0], cen[1] - p[1])) + abs(zc - p[2]) * (0.01 if inside else 1)
        if d < bd:
            best, bd = i, d
    return best


def add_door_tri(n, door_raw: int, at) -> int:
    from tools.navmesh import nvnm
    ti = tri_under(n, at)
    if ti < 0:
        return -1
    n.tris["flags"][ti] |= nvnm.DOOR
    n.doors = np.concatenate([n.doors, np.array([(ti, nvnm.PATHING_DOOR, door_raw)], nvnm.DOOR_TRI)])
    return ti


def nvmi_interior(navm: int, cell: int, centre, edge_navms, doors) -> bytes:
    import struct
    from tools.navmesh import nvnm
    b = [struct.pack("<II3ff", navm, 0, *[float(c) for c in centre], 0.0)]
    el = sorted(set(edge_navms))
    b.append(struct.pack(f"<I{len(el)}I", len(el), *el))
    b.append(struct.pack("<I", 0))
    ds = sorted(set(doors))
    b.append(struct.pack("<I", len(ds)) + b"".join(struct.pack("<II", nvnm.PATHING_DOOR, d) for d in ds))
    b.append(struct.pack("<BIII", 0, nvnm.PATHING_CELL, 0, cell))
    return b"".join(b)


def navm_record(fid: int, nv_bytes: bytes) -> str:
    from tools.navmesh import stitch
    from tools.navmesh.esm import pack_subrecord
    return base64.b64encode(stitch.record(b"NAVM", fid, pack_subrecord(b"NVNM", nv_bytes))).decode()


def _plugin_path(file: str) -> Path:
    data = Path(os.environ.get("ARGONIA_GAME_ROOT", Path.home() / "games" / "skyrimse")) / "Data"
    p = data / file
    if p.exists():
        return p
    mods = Path.home() / ".argonia" / "stack" / "MO2" / "mods"
    for d in sorted(mods.iterdir()) if mods.is_dir() else []:
        if (d / file).exists():
            return d / file
    raise SystemExit(f"{file} not in {data} nor the staged mods")


def interior_navmesh(I: dict, S: dict, ids: Ids) -> list[dict]:
    from tools.navmesh import esm, nvnm
    if not I["copy"] or not I["src_navmesh"]:
        return []
    plugin = I["copy"]["plugin"]
    path = _plugin_path(plugin)
    own = len(esm.masters(path))
    want = {raw_fid(own, split_key(k)[1]) for k in I["src_navmesh"]}
    srcs = {}
    for rec in esm.records(path, {b"NAVM"}, {b"CELL"}):
        if rec.fid in want:
            nv = next(p for s, p in esm.subrecords(rec.data) if s == b"NVNM")
            srcs[rec.fid] = nvnm.decode(nv)
    ours = {f: ids.local(f"navm:{I['space']}:{f & 0xFFFFFF:06X}") for f in srcs}
    cell_raw = raw_fid(NAV_SELF, split_key(I["fk"])[1])
    out = []
    keep = I.get("keep_within")
    for f, n in sorted(srcs.items()):
        tri_keep = np.ones(len(n.tris), bool)
        if keep:
            v = n.verts
            cen = v[n.tris["v"]].mean(axis=1)
            tri_keep = np.linalg.norm(cen - np.asarray(keep["pos"], np.float32), axis=1) <= keep["radius"]
        idx = -np.ones(len(n.tris), np.int64)
        idx[tri_keep] = np.arange(int(tri_keep.sum()))
        tris = n.tris[tri_keep].copy()
        links_keep = []
        for t in tris:
            for k in range(3):
                e = int(t["e"][k])
                if t["flags"] & nvnm.EDGE_LINK[k]:
                    ln = n.links[e]
                    # a link into another navmesh of the copy is kept when that navmesh is copied; else dropped
                    target = int(ln["navm"])
                    if target in ours:
                        links_keep.append((raw_fid(NAV_SELF, ours[target]), int(ln["tri"]), int(ln["type"])))
                        t["e"][k] = len(links_keep) - 1
                    else:
                        t["flags"] &= ~nvnm.EDGE_LINK[k]
                        t["e"][k] = -1
                else:
                    t["e"][k] = idx[e] if e >= 0 else -1
            t["flags"] &= ~nvnm.DOOR
        # vertices: keep only the used ones
        used = np.unique(tris["v"].reshape(-1)) if len(tris) else np.zeros(0, int)
        vmap = -np.ones(len(n.verts), np.int64)
        vmap[used] = np.arange(len(used))
        for t in tris:
            t["v"] = [vmap[x] for x in t["v"]]
        if not len(tris):
            continue  # nothing of this navmesh lies in the kept room
        m = nvnm.Nvnm(0, None, cell_raw, n.verts[used].copy(), tris,
                      np.array([(ty, nf, tr) for nf, tr, ty in links_keep], nvnm.LINK) if links_keep else np.zeros(0, nvnm.LINK))
        m.cover = np.zeros(0, "<i2")
        out.append({"fid": raw_fid(NAV_SELF, ours[f]), "nv": m, "space": I["space"], "cell_raw": cell_raw})
    return out


def generate_interior_navmesh(I: dict, S: dict, ids: Ids, work: Path) -> list[dict]:
    """An interior's navmesh by the same Recast run as the world's (ArgoniaNav, the same params), when its source
    has none over the kept room: the room's collision is moved into synthetic cells with a ground plane just under
    its lowest collision (the floor its walls stand on), meshed, moved back, cut to the room's bounds (and the kept
    radius), welded, and made one NAVM of the cell."""
    from tools.navmesh import nvnm, params, stitch
    from tools.navmesh.__main__ import NAV_BIN, build_tool as nav_tool, game_data
    from tools.navmesh import placed
    rows = []
    for r in S["refs"]:
        if r["space"] == I["space"] and r.get("kind") not in ("marker", "light") and not r.get("disabled"):
            f, local = split_key(r["base"])
            rows.append({"base": f"{local:06X}:{f}", "pos": r["pos"], "rot": r["rot"], "scale": r.get("scale", 1.0), "formKey": r["fk"]})
    tris, _ = placed.collide(rows, game_data(), {})
    if not len(tris):
        return []
    lo, hi = tris.reshape(-1, 3).min(axis=0), tris.reshape(-1, 3).max(axis=0)
    span = hi[:2] - lo[:2]
    ncx, ncy = int(span[0] // (CELL - 512)) + 1, int(span[1] // (CELL - 512)) + 1
    shift = np.array([256.0 - lo[0], 256.0 - lo[1], 0.0])  # the room's south-west corner 256 units into cell (0, 0)
    deep = float(lo[2]) - 2.0  # a ground plane just under the lowest collision: the floor the room's walls stand on
    mg = params.BORDER_SAMPLES + 2  # samples of margin round the box: ArgoniaNav's window reaches past the cell
    rows_n, cols_n = ncy * 32 + 1 + 2 * mg, ncx * 32 + 1 + 2 * mg
    d = work / f"int_{I['space']}"
    (d / "in").mkdir(parents=True, exist_ok=True)
    np.full((rows_n, cols_n), deep, np.float32).tofile(d / "in" / "height.f32")
    np.full((rows_n, cols_n), np.nan, np.float32).tofile(d / "in" / "water.f32")
    np.zeros((rows_n, cols_n), np.uint8).tofile(d / "in" / "flags.u8")
    np.zeros((ncy, ncx), np.uint8).tofile(d / "in" / "skip.u8")
    (tris + shift).astype(np.float32).tofile(d / "in" / "objects.f32")
    (d / "in" / "grid.json").write_text(json.dumps({"rows": rows_n, "cols": cols_n, "x0": -mg * 128.0, "ytop": float(ncy * CELL) + mg * 128.0, "step": 128.0,
                                                    "cells": [0, 0, ncx - 1, ncy - 1], "build_id": f"interior:{I['space']}", "water": -1e9,
                                                    "params": params.recast(), "objects": len(tris)}, indent=1))
    nav_tool()
    r = subprocess.run([str(NAV_BIN), "cells", "--in", str(d / "in"), "--out", str(d)], env=DOTNET_ENV, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"interior navmesh {I['space']}: ArgoniaNav failed\n{(r.stdout + r.stderr)[-2000:]}")
    verts, tri_l, index = [], [], {}
    for p in sorted((d / "raw").glob("cy*.bin")):
        for m in stitch.read_raw(p):
            local = []
            for v in m.verts:
                k = (round(v[0] * 2), round(v[1] * 2), round(v[2] * 2))
                if k not in index:
                    index[k] = len(verts)
                    verts.append([v[0] - shift[0], v[1] - shift[1], v[2]])
                local.append(index[k])
            for t in m.tris:
                cx_ = sum(m.verts[t[q]][0] for q in range(3)) / 3 - shift[0]
                cy_ = sum(m.verts[t[q]][1] for q in range(3)) / 3 - shift[1]
                keep = I.get("keep_within")
                if not (lo[0] + 32 < cx_ < hi[0] - 32 and lo[1] + 32 < cy_ < hi[1] - 32):
                    continue  # the ground plane outside the room's walls
                if keep and math.dist((cx_, cy_), keep["pos"][:2]) > keep["radius"]:
                    continue
                tri_l.append([local[t[0]], local[t[1]], local[t[2]]])
    import shutil
    shutil.rmtree(d)
    if not tri_l:
        return []
    used = sorted({i for t in tri_l for i in t})
    remap = {o: n for n, o in enumerate(used)}
    mesh = stitch.Mesh(0, 0, [verts[i] for i in used], [[remap[i] for i in t] for t in tri_l], [0] * len(tri_l))
    nb = stitch.neighbours(mesh)
    tr = np.zeros(len(mesh.tris), nvnm.TRI)
    for i, t in enumerate(mesh.tris):
        tr[i] = (t, nb[i], nvnm.FOUND, 0)
    cell_raw = raw_fid(NAV_SELF, split_key(I["fk"])[1])
    fid = raw_fid(NAV_SELF, ids.local(f"navm:{I['space']}:generated"))
    n = nvnm.Nvnm(0, None, cell_raw, np.asarray(mesh.verts, np.float32), tr)
    return [{"fid": fid, "nv": n, "space": I["space"], "cell_raw": cell_raw}]


def exterior_navmesh(touched: set, objects, patched: dict, polylines, out: Path) -> tuple[list[dict], dict]:
    """tools.navmesh over the window (touched cells + NAV_RING rings) with the place's land and collision; the
    touched cells and their first ring are ours (their seams are re-split at the changed neighbour), the second
    ring must come out byte-equal to the world's own NAVM (the join is then edge for edge)."""
    from tools.navmesh import __main__ as nav, nvnm, world
    land = world.Land.load(WORLD_DIR)
    xs = [c[0] for c in touched]
    ys = [c[1] for c in touched]
    box = (min(xs) - NAV_RING, min(ys) - NAV_RING, max(xs) + NAV_RING, max(ys) + NAV_RING)
    heights = None
    if patched:
        g = land.grid
        heights = np.array(land.heights(), np.float32)
        for (gx, gy), v in patched.items():
            heights[g.cy_top * 32 + 32 - gy, gx - g.cx0 * 32] = v * 8.0
    res = nav.build(out, box, WORLD_DIR, run_check=False, objects=objects, heights=heights, polylines=polylines, land=land)
    ring1 = {(x + dx, y + dy) for x, y in touched for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    ring2 = {(x + dx, y + dy) for x, y in ring1 for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - ring1
    mine, built = [], {}
    for p in sorted((out / "navm").glob("cy*.jsonl.gz")):
        for ln in gzip.open(p, "rt"):
            e = json.loads(ln)
            built[(e["x"], e["y"])] = e
    world_rows = {}
    for p in sorted((WORLD_NAV / "navm").glob("cy*.jsonl.gz")):
        cy = int(p.name[2:6])
        if box[1] <= cy <= box[3]:
            for ln in gzip.open(p, "rt"):
                e = json.loads(ln)
                world_rows[(e["x"], e["y"])] = e
    seam = {"ring2_cells": 0, "ring2_equal": 0, "ring2_differ": []}
    for c in sorted(ring2):
        if c in built or c in world_rows:
            seam["ring2_cells"] += 1
            if built.get(c, {}).get("navm") == world_rows.get(c, {}).get("navm"):
                seam["ring2_equal"] += 1
            else:
                seam["ring2_differ"].append(list(c))
    navi = json.loads((out / "navi.json").read_text())
    nvmis = {}
    from tools.navmesh.esm import subrecords
    import struct
    rec = base64.b64decode(navi["navi"])
    for s, p in subrecords(rec[24:]):
        if s == b"NVMI":
            nvmis[struct.unpack_from("<I", p, 0)[0]] = p
    for c in sorted(ring1):
        e = built.get(c)
        if e is None:
            continue
        rec = base64.b64decode(e["navm"])
        nv = nvnm.decode(next(p for s, p in subrecords(rec[24:]) if s == b"NVNM"))
        fid = struct.unpack_from("<I", rec, 12)[0]
        mine.append({"fid": fid, "nv": nv, "space": "exterior", "cell": list(c), "nvmi": nvmis.get(fid)})
    return mine, {"box": list(box), "times": res.get("times"), "seam": seam}


def finish_navmesh(navs: list[dict], S: dict, world_fid: int) -> tuple[list[dict], list[str]]:
    """Door triangles both sides; then each NAVM record and its NVMI."""
    from tools.navmesh import nvnm
    doors_of: dict[int, list[int]] = {}
    by_space: dict[str, list[dict]] = {}
    for n in navs:
        by_space.setdefault(n["space"], []).append(n)
    notes = []
    for r in S["refs"]:
        t = r.get("teleport")
        if not t:
            continue
        partner = next(x for x in S["refs"] if x["fk"] == t["to"])
        at = partner["teleport"]["pos"]  # one arrives by r through the partner: the partner's marker stands by r
        cand = by_space.get(r["space"], [])
        if r["space"] == "exterior":
            cx, cy = cell_of(at[0], at[1])
            cand = [n for n in cand if tuple(n["cell"]) == (cx, cy)]
        if not cand:
            notes.append(f"door {r['id']}: no navmesh under its arrival point")
            continue
        n = cand[0]
        if add_door_tri(n["nv"], nav_fid(r["fk"]), at) >= 0:
            doors_of.setdefault(n["fid"], []).append(nav_fid(r["fk"]))
    out = []
    for n in navs:
        nv = n["nv"]
        nvnm.build_grid(nv)
        centre = nv.verts.mean(axis=0) if len(nv.verts) else np.zeros(3)
        doors = doors_of.get(n["fid"], [])
        if n["space"] == "exterior":
            mi = n["nvmi"]
            if doors:  # rebuild the NVMI with the doors: same layout as the stitch's
                edge = sorted({int(x) for x in nv.links["navm"]})
                pref = float(np.mean((nv.tris["flags"] & nvnm.PREFERRED) > 0)) if len(nv.tris) else 0.0
                mi = nvnm.nvmi(n["fid"], centre, edge, doors, world_fid, tuple(n["cell"]), preferred=pref)
        else:
            edge = sorted({int(x) for x in nv.links["navm"]})
            mi = nvmi_interior(n["fid"], n["cell_raw"], centre, edge, doors)
        out.append({"space": n["space"], "cell": n.get("cell"), "record": navm_record(n["fid"], nvnm.encode(nv)),
                    "nvmi": base64.b64encode(mi).decode(), "tris": int(len(nv.tris)), "doors": len(doors)})
    return out, notes


def collision_objects(refs: list[dict]):
    from tools.navmesh import placed
    from tools.navmesh.__main__ import game_data
    rows = []
    for r in refs:
        if r["space"] != "exterior" or r.get("kind") not in SOLID_KINDS or r.get("disabled"):
            continue
        f, local = split_key(r["base"])
        rows.append({"base": f"{local:06X}:{f}", "pos": r["pos"], "rot": r["rot"], "scale": r.get("scale", 1.0), "formKey": r["fk"]})
    if not rows:
        return None, {"refs": 0}
    return placed.collide(rows, game_data(), {})


# ---- one place --------------------------------------------------------------------------------------------------------

def plan_place(pid: str, pdir: Path, out: Path, no_navmesh: bool) -> dict:
    t0 = time.time()
    P = read_place(pdir)
    tmp = out / "tmp" / pid
    tmp.mkdir(parents=True, exist_ok=True)
    ids = Ids(pdir.parent, pid)
    notes: list[str] = []
    S = plan_spaces(P, ids, tmp)
    notes += pair_doors(S)
    for r in P["paths"]:
        r.setdefault("points", [])
    path_cells = set()
    for p in P["paths"]:
        for x, y in p["points"]:
            path_cells.add(cell_of(x, y))
    ext_cells = {tuple(r["cell"]) for r in S["refs"] if r["space"] == "exterior"}
    land_cells = {tuple(r["cell"]) for r in P["land"]}
    clear_cells = {cell_of(*r["pos"][:2]) for r in P["clear"]}
    ask = set()
    for c in ext_cells | land_cells | path_cells | clear_cells:
        ask |= {(c[0] + dx, c[1] + dy) for dx in (-2, -1, 0, 1, 2) for dy in (-2, -1, 0, 1, 2)}
    facts = world_facts(ask, tmp)
    from tools.navmesh import world as navworld
    land_build = navworld.Land.load(WORLD_DIR).build_id
    if land_build not in (facts.get("description") or ""):
        raise SystemExit(f"the world ESM is not of the land build {land_build} its navmesh inputs hold: rebuild the world first")
    land, patched, land_changed = plan_land(P["land"], facts)
    path_layers = plan_paths(P["paths"], facts)
    clear = plan_clear(P["clear"], facts)
    from tools.places import people as ppl
    people = ppl.plan(P, S, ids, facts, notes)
    # land rows: heights and path layers merged per cell
    by_cell = {(r["x"], r["y"]): r for r in land}
    for c, layers in path_layers.items():
        f = facts["by_cell"].get(c)
        if f is None or f.get("land") is None:
            raise SystemExit(f"path reaches cell {c}, which the world has no LAND for")
        row = by_cell.setdefault(c, {"x": c[0], "y": c[1], "land": f["land"]})
        row["layers"] = layers
    # navmesh
    nav_info = {}
    navs: list[dict] = []
    if not no_navmesh:
        solid = [r for r in S["refs"] if r["space"] == "exterior" and r.get("kind") in SOLID_KINDS]
        touched = {tuple(r["cell"]) for r in solid} | land_changed | set(path_layers)
        if touched:
            objects, tally = collision_objects(S["refs"])
            polylines = navworld.road_polylines() + [[(x, y, False) for x, y in p["points"]] for p in P["paths"]]
            ext, nav_info = exterior_navmesh(touched, objects, patched, polylines, out / "navmesh" / pid)
            nav_info["collision"] = tally
            navs += ext
        for I in S["interiors"]:
            got = interior_navmesh(I, S, ids)
            if not got:
                got = generate_interior_navmesh(I, S, ids, out / "tmp" / pid)
                notes.append(f"interior {I['space']}: the source has no navmesh over the kept room; generated ({sum(len(n['nv'].tris) for n in got)} triangles)")
            navs += got
    world_raw = nav_fid(facts["worldspace"])
    nav_rows, n2 = finish_navmesh(navs, S, world_raw)
    notes += n2
    ids.save()
    plan = {
        "place_id": pid, "world": {"worldspace": facts["worldspace"], "top_cell": facts["top_cell"], "esm": WORLD},
        "cells": sorted([{"x": c[0], "y": c[1], "cell": facts["by_cell"][c]["fk"]} for c in ask if c in facts["by_cell"]],
                        key=lambda r: (r["x"], r["y"])),
        "refs": S["refs"], "interiors": [{k: v for k, v in I.items() if k != "fk_of_src"} for I in S["interiors"]],
        "land": sorted(by_cell.values(), key=lambda r: (r["x"], r["y"])), "clear": clear,
        "navmesh": {"masters": NAV_MASTERS, "self": PLUGIN, "navi": key_of("Skyrim.esm", NAVI_FID), "navm": nav_rows},
        "people": people, "notes": notes,
        "stats": {"plan_s": round(time.time() - t0, 1), "nav": nav_info},
    }
    for f in tmp.iterdir():
        f.unlink()
    tmp.rmdir()
    return plan


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places build")
    ap.add_argument("places", nargs="*")
    ap.add_argument("--places-dir", default=str(PLACES))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--no-navmesh", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    t0 = time.time()
    root, out = Path(a.places_dir), Path(a.out)
    ids = a.places or sorted(d.name for d in root.iterdir() if (d / "place.json").exists())
    build_tool()
    world_sha = sha256(WORLD_ESM)
    report = {"places": {}, "world_sha256": world_sha}
    for pid in ids:
        pdir = root / pid
        if not (pdir / "place.json").exists():
            raise SystemExit(f"no place files at {pdir}")
        shard = out / "shards" / pid
        key = place_key(pdir, world_sha) + (":nonav" if a.no_navmesh else "")
        kp = shard / "key.txt"
        if not a.force and kp.exists() and kp.read_text() == key and (shard / "plan.json").exists():
            report["places"][pid] = {"rebuilt": False}
            log(f"build {pid}: unchanged")
            continue
        t1 = time.time()
        plan = plan_place(pid, pdir, out, a.no_navmesh)
        atomic_json(shard / "plan.json", plan)
        kp.write_text(key)
        report["places"][pid] = {"rebuilt": True, "plan_s": round(time.time() - t1, 1), "notes": plan["notes"]}
        log(f"build {pid}: planned in {time.time() - t1:.1f} s; {len(plan['refs'])} refs, {len(plan['interiors'])} interiors, "
            f"{len(plan['land'])} land cells, {len(plan['clear'])} cleared, {len(plan['navmesh']['navm'])} navmeshes")
        for n in plan["notes"]:
            log(f"  note: {n}")
    shards = sorted(str(p) for p in (out / "shards").glob("*/plan.json"))
    esp = out / "plugin" / PLUGIN
    esp.parent.mkdir(parents=True, exist_ok=True)
    t2 = time.time()
    tool("write", str(esp), str(WORLD_ESM), *shards)
    report["write_s"] = round(time.time() - t2, 1)
    report["total_s"] = round(time.time() - t0, 1)
    report["esp"] = str(esp.relative_to(ROOT)) if esp.is_relative_to(ROOT) else str(esp)
    report["esp_sha256"] = sha256(esp)
    atomic_json(out / "plugin" / "build.json", report)
    print(json.dumps(report, sort_keys=True))
    return 0
