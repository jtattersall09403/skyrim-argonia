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
  stock       what each container, person, trader and loose ref holds, from the place's stock rows (stock/plan.py)
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
COLLISION_BASES = {"Skyrim.esm:000021"}  # CollisionMarker: its primitive is an invisible wall or floor, solid to people
PERSISTENT_KINDS = {"door"}
# a style of one land texture (texture.py ids); every other style (road, street, path, dirt, track, boardwalk) is painted
# with the road set of the ground province it crosses (tools/newworld/world/roadpaint.py)
PATH_STYLE_LTEX = {"skirt": "verge", "mud": "swamp_mud", "sand": "sand", "stone": "rock"}
WORLD_LTEX_PREFIX = "ANW_Ground_"
PATH_WALK_REACH = 96.0  # units beyond a path's half width that count as the path itself (the cells its navmesh changes)
PATH_SEAM_FADE = 4.0  # vertices over which a texture a repainted quadrant cannot keep fades out toward it
PLACE_MASTERS = {"Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm", "Black Marsh.esm"}  # Write.cs Masters
NAV_RING = 3  # the navmesh window: the touched cells plus this many rings (ring 1 overridden, ring 2 must match)
DOTNET_ENV = dict(os.environ, DOTNET_ROOT=str(Path.home() / ".dotnet"), DOTNET_NOLOGO="1", DOTNET_CLI_TELEMETRY_OPTOUT="1",
                  PATH=f"{Path.home() / '.dotnet'}:{os.environ.get('PATH', '')}")


PROBLEMS: list[str] = []  # every fault planning finds; --plan lists them all, a build stops on any


def problem(msg: str) -> None:
    PROBLEMS.append(msg)


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
    """Build the C# tool once; concurrent runs (a draft check's --plan beside a build) wait on one lock, so none
    reads a half-written tool or sees the other's `dotnet build` fail."""
    import fcntl
    TOOL_DIR.mkdir(parents=True, exist_ok=True)
    with open(TOOL_DIR / ".build.lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        _build_tool()


def _build_tool() -> None:
    if TOOL.exists() and all(p.stat().st_mtime < TOOL.stat().st_mtime for p in TOOL_PROJ.glob("*.cs*")):
        return  # up to date: `dotnet build` alone takes seconds
    r = subprocess.run(["dotnet", "build", str(TOOL_PROJ), "-c", "Release", "-o", str(TOOL_DIR), "-nologo", "-v", "q"],
                       env=DOTNET_ENV, capture_output=True, text=True)
    if r.returncode:
        errs = [ln for ln in (r.stdout + r.stderr).splitlines() if "error" in ln.lower()]
        raise SystemExit("build: the C# tool did not build\n" + "\n".join(errs[-40:] or [(r.stdout + r.stderr)[-3000:]]))


def tool(*args: str) -> None:
    r = subprocess.run(["dotnet", str(TOOL), *args], env=DOTNET_ENV, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"ArgoniaPlacesBuild {args[0]} failed\n{(r.stdout + r.stderr)[-4000:]}")
    if r.stdout.strip():
        log(r.stdout.strip())


def code_key() -> str:
    h = hashlib.sha256()
    world = ROOT / "tools" / "newworld" / "world"  # the road rule and the ground's road sets the paths are painted by
    for p in sorted([Path(__file__), Path(__file__).with_name("people.py"), world / "roadpaint.py", world / "texture.py"]
                    + list(TOOL_PROJ.glob("*.cs"))):
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
    from tools.places.stock import plan as stockplan
    h = hashlib.sha256((world_sha + code_key() + stockplan.key(pdir.name)).encode())
    h.update(json.dumps([[s for s in jsonl(DB / "travel_stop.jsonl") if s["place_id"] == pdir.name],
                         travel_routes(pdir.name)], sort_keys=True).encode())  # the network's part in the place
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
    bdir = OUT / "bundles" / f"src.{src}"
    sj = bdir / "spaces" / cell / "space.json"
    own = row["plugins"] + row.get("extra_refs_plugins", [])
    if sj.exists():  # the extractor's own record of where the cell is (its key, in whichever plugin of the source)
        b = json.loads(sj.read_text())
        bj = bdir / "bundle.json"
        order = (json.loads(bj.read_text()).get("plugins") if bj.exists() else None) or own
        return "|".join(cell_holders(list(dict.fromkeys(order + [b["plugin"]] + own)), b["key"])), b["key"]
    return "|".join(own), cell


def cell_holders(order: list[str], key: str) -> list[str]:
    """The plugins of a source's load order (the extractor's: masters first) that can hold the record `key`: the plugin
    it originates in and every plugin mastering that one, in load order, so the last that holds it wins (a cell BM&V
    overrides from Dawnguard.esm is Dawnguard's refs with BM&V's changes over them, never BM&V's alone)."""
    origin = key.split(":", 1)[0].lower()
    out = []
    for p in order:
        try:
            masters = {m.lower() for m in source_names(p)[:-1]}
        except SystemExit:
            continue  # a plugin not on this machine holds nothing we can read
        if p.lower() == origin or origin in masters:
            out.append(p)
    return out


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
                problem(f"land.jsonl: vertex {gx},{gy} patched to two heights")
                continue
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
                problem(f"land patch reaches cell {cx},{cy}, which has no LAND in the world")
                continue
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


def _world_quadrant(layers: list[dict], q: int) -> dict[str, np.ndarray]:
    """One quadrant of a world LAND (facts layers) -> its composite weight per land texture key at the 289 vertices,
    stacked as the engine stacks them (base 1, each alpha layer replaces (1 - o) of what is under it)."""
    mine = [x for x in layers if x["quadrant"] == q]
    base = [x for x in mine if x.get("alpha") is None]
    alphas = sorted((x for x in mine if x.get("alpha") is not None), key=lambda x: x["layer"])
    w: dict[str, np.ndarray] = {}
    if base:
        w[base[0]["texture"]] = np.ones(289)
    for a in alphas:
        o = np.zeros(289)
        for pos, op in a["alpha"]:
            if pos < 289:
                o[int(pos)] = op
        for k in w:
            w[k] = w[k] * (1 - o)
        w[a["texture"]] = w.get(a["texture"], np.zeros(289)) + o
    return w


_LC = None


def _landcover():
    """The world's landcover legend and region raster (where a place path finds its ground province)."""
    global _LC
    if _LC is None:
        from tools.newworld.world import texture as tx
        legend = json.loads((tx.LC / "legend.json").read_text())
        _LC = (legend, np.load(tx.LC / "region.npy", mmap_mode="r"))
    return _LC


def path_road_set(x: float, y: float) -> tuple[str, str, str]:
    """The road set (two track materials and the verge, texture.py ids) of the ground province at a world point."""
    from tools.newworld.world import roadpaint as rp, texture as tx
    legend, region = _landcover()
    ox, oy = legend["origin_world"]
    r = int(np.clip(round((oy - y) / legend["sample_units"]), 0, region.shape[0] - 1))
    c = int(np.clip(round((x - ox) / legend["sample_units"]), 0, region.shape[1] - 1))
    prov = int(tx.province_of(legend["regions"])[int(region[r, c])])
    return rp.ROAD_SETS[tx.PROVINCES[tx.PROV[prov - 1]]["road"] if prov else tx.DEFAULT_ROAD]


def plan_paths(paths: list[dict], facts: dict, walked: set | None = None) -> dict[tuple[int, int], list[dict]]:
    """Paths -> the land textures of every quadrant they reach, painted by the world's road rule
    (tools/newworld/world/roadpaint.py, which the studio's path_paint.js follows): from the path's edge (its half width)
    its straight ramp (full on the path, 0 by 8.55 m out for a road or a street, 6.8 m for a path, a dirt track or a
    boardwalk ashore); the track core (the two track materials of the ground province's road set, varying along it as
    the world's roads do) falls away over 6.5 m and the verge holds the rest. A style naming one land texture (`mud`, `sand`, `stone`,
    `skirt`) or a land texture key the owner picked paints that texture alone, on the same ramp. Each reached quadrant
    is repainted whole: the world's composite there, the path blended over it, at most six textures kept (the path's
    first, then the heaviest), as a base and alpha layers that replace the world's in that quadrant. A texture a
    quadrant cannot keep fades to nothing over PATH_SEAM_FADE vertices toward it, in it and in its neighbours (which
    are then repainted too, with what the world paints there), so every vertex two quadrants share reads the same
    from both, repainted or not. -> {cell: [{quadrant, base, layers: [{texture, alpha}], paths, dropped}]}.
    `walked`, when given, is filled with the cells the paths themselves cross (a vertex within PATH_WALK_REACH of a
    path's edge): the cells whose navmesh a path changes. Paint reaches further and changes no navmesh."""
    from tools.newworld.world import roadpaint as rp, texture as tx
    ltex = {t["edid"]: t["fk"] for t in facts["ltex"]}
    world_keys = set(ltex.values())

    def mat(mid: str) -> str | None:
        # the world names a ground material's land texture ANW_Ground_<id> (NewWorld.cs): the whole id, so `verge` is
        # never `clay_verge`
        return next((fk for e, fk in ltex.items() if e and e.lower() == (WORLD_LTEX_PREFIX + mid).lower()), None)

    specs = []
    for p in paths:
        style = str(p.get("style") or p.get("kind") or "path")
        if ":" in style:
            # a land texture named by its key (the ground the owner picked in the studio): the world's own, or one of
            # a plugin the place layer masters (the source place's road texture)
            if style not in world_keys and split_key(style)[0] not in PLACE_MASTERS:
                problem(f"path {p['id']}: land texture {style} is in no plugin the place layer loads")
                continue
            keys = (style, style, style)
        else:
            pts_ = np.asarray(p["points"], float)
            mid = pts_[len(pts_) // 2]
            want = (PATH_STYLE_LTEX[style],) * 3 if style in PATH_STYLE_LTEX else path_road_set(float(mid[0]), float(mid[1]))
            keys = tuple(mat(w) for w in want)
            if None in keys:
                problem(f"path {p['id']}: no world land texture for style {style!r} ({', '.join(want)})")
                continue
        specs.append((p, style, keys, rp.SCALE[rp.STYLE_CLASS.get(style, "minor")]))
    if not specs:
        return {}
    # per cell vertex: the path with the strongest pull there, and its materials' weights
    best: dict[tuple[int, int], dict] = {}
    for p, style, keys, scale in specs:
        pts = np.asarray(p["points"], float)
        half = float(p.get("width", 256)) / 2
        reach = half + rp.reach_m(scale) / rp.M_PER_UNIT
        lo, hi = pts.min(axis=0) - reach, pts.max(axis=0) + reach
        for cx in range(cell_of(*lo)[0], cell_of(*hi)[0] + 1):
            for cy in range(cell_of(*lo)[1], cell_of(*hi)[1] + 1):
                gx = cx * CELL + np.arange(VERTS) * QUAD
                gy = cy * CELL + np.arange(VERTS) * QUAD
                X, Y = np.meshgrid(gx, gy)  # [y from the south, x]
                d = np.full(X.shape, np.inf)
                for a, b in zip(pts[:-1], pts[1:]):
                    d = np.minimum(d, seg_dist(X, Y, a[0], a[1], b[0], b[1]))
                e = (d - half) * rp.M_PER_UNIT
                mix = tx.road_mix(np.floor(-Y / QUAD + 0.5).astype(np.int64), np.floor(X / QUAD + 0.5).astype(np.int64))
                pull, wa, wb, wv = rp.road_weights(e, scale, mix)
                on = d - half < PATH_WALK_REACH
                if style == "boardwalk":
                    # a boardwalk's line is walked on its decks: only where it comes ashore is it a path on the ground
                    c = facts.get("by_cell", {}).get((cx, cy)) or {}
                    w = c.get("water")
                    if c.get("deltas") and w is not None and abs(w) < 1e8:
                        from tools.newworld.world.units import VHGT_STEP_UNITS
                        wet = cell_steps(c) * VHGT_STEP_UNITS < w - 8
                        pull, wa, wb, wv = (np.where(wet, 0.0, v) for v in (pull, wa, wb, wv))
                        on = on & ~wet
                if walked is not None and on.any():
                    walked.add((cx, cy))
                if not (pull > 1e-3).any():
                    continue
                cur = best.setdefault((cx, cy), {"pull": np.zeros((VERTS, VERTS)), "w": {}, "paths": set()})
                take = pull > cur["pull"]
                if not take.any():
                    continue
                cur["paths"].add(p["id"])
                cur["pull"] = np.where(take, pull, cur["pull"])
                for k in list(cur["w"]):
                    cur["w"][k] = np.where(take, 0.0, cur["w"][k])
                for k, v in zip(keys, (wa, wb, wv)):
                    cur["w"][k] = cur["w"].get(k, np.zeros((VERTS, VERTS))) + np.where(take, v, 0.0)
    path_keys = {k for _, _, keys, _ in specs for k in keys}
    by_cell = facts.get("by_cell", {})

    def world_quadrant(gq):
        """A quadrant by its place on the world's quadrant lattice (2 cx + qx, 2 cy + qy) -> (cell, quadrant number,
        its world composite or None when the world has no land texture layers there)."""
        c, q = (gq[0] // 2, gq[1] // 2), (gq[1] % 2) * 2 + gq[0] % 2
        layers = (by_cell.get(c) or {}).get("layers")
        return c, q, (_world_quadrant(layers, q) if layers else None)

    # every quadrant a path reaches: the world's composite with the path over it, and the six textures it keeps (the
    # path's first, then the heaviest)
    quads: dict[tuple[int, int], dict] = {}
    for c, cur in best.items():
        for q, (y0, x0) in enumerate(((0, 0), (0, 16), (16, 0), (16, 16))):  # BL, BR, TL, TR
            pull = cur["pull"][y0:y0 + 17, x0:x0 + 17].ravel()
            if not (pull > 1e-3).any():
                continue
            gq = (2 * c[0] + x0 // 16, 2 * c[1] + y0 // 16)
            world = world_quadrant(gq)[2]
            if world is None:
                problem(f"path reaches cell {c} quadrant {q}, which has no world land texture layers")
                continue
            w = {k: v * (1 - pull) for k, v in world.items()}
            for k, v in cur["w"].items():
                w[k] = w.get(k, np.zeros(289)) + v[y0:y0 + 17, x0:x0 + 17].ravel()
            tot = {k: float(v.sum()) for k, v in w.items() if v.max() > 1e-4}
            # kept first: the heaviest texture at each corner (every quadrant round a corner reads the same weights
            # there, so they always keep one texture in common), then the path's, then the heaviest
            names = sorted(tot)
            corners = [max(names, key=lambda k: round(float(w[k][i]), 4)) for i in (0, 16, 272, 288)]
            mine = sorted((k for k in tot if k in path_keys and tot[k] > 0.5), key=lambda k: -tot[k])
            rest = sorted(tot, key=lambda k: -tot[k])
            keep = list(dict.fromkeys(corners + mine + rest))[:tx.MAXL]
            gone = [k for k in tot if k not in keep]
            quads[gq] = {"cell": c, "quadrant": q, "w": w, "keep": keep, "gone": set(gone), "paths": sorted(cur["paths"]),
                         "dropped": float(np.max(sum(w[k] for k in gone))) if gone else 0.0}
    # a quadrant that could not keep a texture: its neighbours are repainted too (with what the world paints there),
    # so the texture can fade out toward it from both sides and every shared vertex still reads the same
    ring = ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1))
    for gq, Q in list(quads.items()):
        if not Q["dropped"]:
            continue
        for dx, dy in ring:
            n = (gq[0] + dx, gq[1] + dy)
            if n in quads:
                continue
            c, q, world = world_quadrant(n)
            if world is None:
                continue
            keep = sorted((k for k in world if world[k].max() > 1e-4), key=lambda k: -float(world[k].sum()))[:tx.MAXL]
            quads[n] = {"cell": c, "quadrant": q, "w": world, "keep": keep, "gone": set(), "paths": [], "dropped": 0.0}
    if not quads:
        return {}
    # the repainted quadrants' vertices as one lattice, so every shared vertex is painted once and read by each quadrant
    from scipy import ndimage as ndi
    gx0, gy0 = min(g[0] for g in quads), min(g[1] for g in quads)
    nx, ny = max(g[0] for g in quads) - gx0 + 1, max(g[1] for g in quads) - gy0 + 1
    keys = sorted({k for Q in quads.values() for k in Q["keep"]})
    ki = {k: i for i, k in enumerate(keys)}
    Wt = np.zeros((ny * 16 + 1, nx * 16 + 1, len(keys)))          # weights, [y from the south, x, texture]
    lack = np.zeros((ny * 16 + 1, nx * 16 + 1, len(keys)), bool)   # a quadrant there does not keep it (closed squares)
    cut = np.zeros((ny * 16 + 1, nx * 16 + 1, len(keys)), bool)    # a quadrant there could not keep it though it had it
    inside = np.zeros((ny * 16 + 1, nx * 16 + 1), bool)
    road = np.zeros((ny * 16 + 1, nx * 16 + 1))                    # the paths' share of each vertex, kept or not
    for gq, Q in quads.items():
        r, c = (gq[1] - gy0) * 16, (gq[0] - gx0) * 16
        sl = (slice(r, r + 17), slice(c, c + 17))
        inside[sl] = True
        road[sl] = sum((v for k, v in Q["w"].items() if k in path_keys), np.zeros(289)).reshape(17, 17)
        for k in keys:
            if k in Q["keep"]:
                Wt[sl + (ki[k],)] = Q["w"][k].reshape(17, 17)
            else:
                lack[sl + (ki[k],)] = True
                cut[sl + (ki[k],)] |= k in Q["gone"]
    allow = np.ones_like(Wt)
    for i in range(len(keys)):
        if cut[..., i].any():   # it fades out toward the quadrants that could not keep it
            allow[..., i] = np.clip(ndi.distance_transform_edt(~cut[..., i]) / PATH_SEAM_FADE, 0, 1)
    allow[lack] = 0
    F = Wt * allow
    # what the cut and the fade took is given back from what is kept nearby (a blur over 3 vertices), else from
    # whatever is kept there: a path's loss to the path's textures and the ground's to the ground (a cut never thins
    # a path), then whatever is still owed to anything kept
    near = ndi.gaussian_filter(F, (3, 3, 0), mode="constant") * allow
    is_path = np.array([k in path_keys for k in keys])
    for grp, share in ((is_path, road), (~is_path, 1 - road), (np.ones(len(keys), bool), None)):
        if not grp.any():
            continue
        need = np.clip((1.0 if share is None else share) - F[..., grp].sum(-1), 0, 1)[..., None]
        ns, as_ = near[..., grp].sum(-1, keepdims=True), allow[..., grp].sum(-1, keepdims=True)
        F[..., grp] += need * np.where(ns > 1e-6, near[..., grp] / np.maximum(ns, 1e-9),
                                       np.where(as_ > 1e-6, allow[..., grp] / np.maximum(as_, 1e-9), 0))
    bare = inside & (F.sum(-1) < 1e-6)
    if bare.any():
        problem(f"path painting: {int(bare.sum())} land vertices are left with no texture their quadrants all keep")
    out: dict[tuple[int, int], list[dict]] = {}
    for gq, Q in sorted(quads.items()):
        r, c = (gq[1] - gy0) * 16, (gq[0] - gx0) * 16
        keep = Q["keep"]
        flat = F[r:r + 17, c:c + 17][..., [ki[k] for k in keep]].reshape(289, len(keep))
        flat = flat / np.maximum(flat.sum(1, keepdims=True), 1e-9)
        order = sorted(range(len(keep)), key=lambda i: -float(flat[:, i].sum()))
        ops = tx.quad_opacities(flat, order)
        alpha = [{"texture": keep[order[k + 1]], "alpha": [[int(i), round(float(ops[k, i]), 4)] for i in np.flatnonzero(ops[k] > 1 / 512)]}
                 for k in range(len(order) - 1)]
        out.setdefault(Q["cell"], []).append({"quadrant": Q["quadrant"], "base": keep[order[0]], "layers": [a for a in alpha if a["alpha"]],
                                              "paths": Q["paths"], "dropped": round(Q["dropped"], 4)})
    return out


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
            problem(f"clear.jsonl: {r.get('id')}: no world ref of {r['base']} within {CLEAR_TOL:.0f} units of {x:.0f},{y:.0f}")
            continue
        taken.add(best["fk"])
        out.append({"fk": best["fk"], "base": best["base"], "pos": best["pos"], "cell": list(cell_of(*best["pos"][:2]))})
    return out


# ---- refs, interiors, doors -----------------------------------------------------------------------------------------

def is_disabled(r: dict) -> bool:
    """A place row is built Initially Disabled when its flags say so (the ref shape's `initially_disabled`)."""
    fl = r.get("flags")
    return bool(r.get("disabled")) or (isinstance(fl, list) and "initially_disabled" in fl)


def collision_box(r: dict) -> list[float] | None:
    """A collision marker's solid box: its primitive's half extents round its origin in its own frame (XPRM; a plane
    is a box of its own thinness, a sphere or an ellipsoid the box round it), else None."""
    p = r.get("primitive")
    if r.get("base") not in COLLISION_BASES or not isinstance(p, dict) or not p.get("bounds"):
        return None
    return [max(abs(float(v)), 0.5) for v in p["bounds"]]


def norm_ref(r: dict) -> dict:
    r = dict(r)
    r.setdefault("rot", [0.0, 0.0, 0.0])
    r.setdefault("scale", 1.0)
    return r


def source_cell(plugin: str, cell: str, tmp: Path) -> dict | None:
    """A source plugin's interior cell as the C# reader gives it (None: not in that plugin), cached under
    out/places/srccells by the plugin file's size and time and the reader's code (reading a large plugin takes seconds)."""
    try:
        st = _plugin_path(plugin).stat()
    except SystemExit:
        return None
    code = sha256(TOOL_PROJ / "Read.cs") + sha256(TOOL_PROJ / "Common.cs")  # the reader and the ref shape it writes
    h = hashlib.sha256(f"{plugin}|{cell}|{st.st_size}|{st.st_mtime_ns}|{code}".encode()).hexdigest()[:20]
    cache = OUT / "srccells" / f"{plugin}__{cell.replace(':', '_')}.{h}.json"
    if cache.exists():
        got = json.loads(cache.read_text())
        return got or None
    try:
        tool("source", plugin, cell, str(tmp))
        got = json.loads(tmp.read_text())
        tmp.unlink()
    except SystemExit:
        got = {}
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.with_suffix(".tmp").write_text(json.dumps(got))
    cache.with_suffix(".tmp").replace(cache)
    return got or None


def source_light_fields(source_id: str | None) -> dict[str, dict]:
    """The source bundle's exterior refs' own light fields (a light's `light_data`, a window's `emittance`), by source
    ref key with its base: an exterior row whose base is still the source's carries them into the build as a copied
    interior ref does (the writer reads a row's own fields)."""
    if not source_id:
        return {}
    d = OUT / "bundles" / f"src.{source_id}" / "spaces" / "exterior"
    rows = jsonl(d / "refs.jsonl") if (d / "refs.jsonl").exists() else []
    if not rows and (d / "refs.jsonl.gz").exists():
        import gzip
        rows = [json.loads(ln) for ln in gzip.open(d / "refs.jsonl.gz", "rt") if ln.strip()]
    return {r["id"]: {"base": r.get("base"), **{k: r[k] for k in ("light_data", "emittance") if r.get(k) is not None}}
            for r in rows if r.get("light_data") is not None or r.get("emittance") is not None}


def plan_spaces(P: dict, ids: Ids, tmp: Path) -> dict:
    """Every space's refs as rows of ours; interiors with their copied header and navmesh source."""
    refs, interiors, by_our = [], [], {}
    for sid, S in P["spaces"].items():
        if sid == "exterior":
            light_of = source_light_fields(P["place"].get("source_id"))
            for r in map(norm_ref, S["refs"]):
                if r.get("removed"):
                    continue
                got = light_of.get(r.get("src"))
                if got and got["base"] == r.get("base"):  # the source ref's own light fields while its base is the source's
                    r = {**{k: v for k, v in got.items() if k != "base"}, **r}
                row = {**r, "fk": ids(f"ref:{r['id']}"), "space": "exterior", "cell": list(cell_of(*r["pos"][:2])),
                       "persistent": "persistent" in (r.get("flags") or []) or bool(r.get("persistent")),
                       "disabled": is_disabled(r)}
                row.pop("flags", None)
                refs.append(row)
                by_our[r["id"]] = row
            continue
        sp = S["space"]
        plugin, cell_edid = resolve_copy(sp["copy_of"]) if sp.get("copy_of") else (None, None)
        src_rows = []
        src = {}
        src_plugins: list[str] = []
        if plugin:
            out = tmp / f"src_{sid}.json"
            # the cell as the game shows it with the source's load order: each holder's version in load order, the
            # last holder's version of a ref (or navmesh, or the header) winning, a ref its winner deletes gone
            got = []
            for cand in plugin.split("|"):
                cell = source_cell(cand, cell_edid, out)
                if cell is not None:
                    got.append((cand, cell))
            if not got:
                problem(f"space {sid}: no plugin of {sp['copy_of']} holds an interior cell {cell_edid}")
                continue
            plugin, src = got[-1]
            src = dict(src)
            src_plugins = [cand for cand, _ in got]
            win_refs: dict[str, dict] = {}
            win_navs: dict[str, dict] = {}
            for _, held in got:
                win_refs.update((r["fk"], r) for r in held["refs"])
                win_navs.update((n["fk"], n) for n in held["navmesh"])
            src["refs"] = list(win_refs.values())
            src["navmesh"] = list(win_navs.values())
            room = None
            if sp.get("room"):  # one room of a cell the source shares between houses (the Build recipe's room rule)
                part = room_partition(sp["copy_of"], src["refs"], tmp)
                room = part["rooms"].get(sp["room"])
                if room is None:
                    problem(f"space {sid}: room {sp['room']} is not a door of {sp['copy_of']} that leads out of it "
                            f"(its doors: {sorted(part['rooms'])})")
            for r in src["refs"]:
                if "pos" not in r or r.get("deleted") or r.get("base_type") in ("NPC_", "LVLN"):
                    continue  # people are ours (people.jsonl), never the source's
                if room is not None and r["fk"] not in room["refs"]:
                    continue
                src_rows.append(r)
        kept = {r["fk"] for r in src_rows}
        changes = {r["src"]: r for r in S["refs"] if r.get("src") and (not plugin or r["src"] in kept)}
        fk_of_src = {}
        for r in src_rows:
            ch = changes.get(r["fk"], {})
            if ch.get("removed"):
                continue
            # a copied ref is known by its space and source ref whether or not the place files list a change to it
            # (the studio's change row carries the source id as its id): its form id is the same before and after an
            # edit, and its own in every copy of the room
            our_id = ch["id"] if ch.get("id") and ch["id"] != r["fk"] else f"{sid}/{r['fk']}"
            row = {"id": our_id, "src": r["fk"], "base": ch.get("base", r["base"]), "kind": ch.get("kind", kind_of(r)),
                   "base_edid": r.get("base_edid") if "base" not in ch else None,
                   "pos": ch.get("pos", r["pos"]), "rot": ch.get("rot", r["rot"]), "scale": ch.get("scale", r.get("scale", 1.0)),
                   "src_flags": r.get("flags", 0), "src_door": r.get("door"), "src_linked": r.get("linked"),
                   "primitive": ch.get("primitive", r.get("primitive")),
                   "src_enable_parent": r.get("enable_parent"), "lock": ch.get("lock", r.get("lock")),
                   "owner": ch.get("owner"), "door": ch.get("door"), "seat": ch.get("seat"), "persistent": bool(r.get("persistent")),
                   "disabled": is_disabled(ch) if "flags" in ch or "disabled" in ch else bool(int(r.get("flags") or 0) & 0x800)}
            row.update({"fk": ids(f"ref:{our_id}"), "space": sid})
            refs.append(row)
            by_our[our_id] = row
            fk_of_src[r["fk"]] = row["fk"]
        for r in map(norm_ref, S["refs"]):
            if r.get("removed") or (r.get("src") and (not plugin or r["src"] in kept)):
                continue
            if r.get("src") and plugin:
                continue  # a row of a source ref outside the kept room: not in this copy
            row = {**r, "fk": ids(f"ref:{r['id']}"), "space": sid, "disabled": is_disabled(r)}
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
                          "copy_of": sp.get("copy_of"), "room": sp.get("room"),
                          "light": sp.get("light"), "owner": sp.get("owner"), "room_mesh": room and room["mesh"],
                          "src_navmesh": list(dict.fromkeys(n["fk"] for n in src.get("navmesh", []))),
                          "src_plugins": src_plugins, "fk_of_src": fk_of_src})
    # links our place files write by our ids (exterior rows, added rows) become form keys; one to nothing is a problem
    import re
    is_key = re.compile(r".+:[0-9A-Fa-f]{6}$").match
    for row in refs:
        for ln in row.get("linked") or []:
            if not is_key(str(ln.get("ref"))):
                tgt = by_our.get(ln.get("ref"))
                if tgt is None:
                    problem(f"refs.jsonl: {row['id']}: linked ref {ln.get('ref')} is not in the place")
                    ln["drop"] = True
                else:
                    ln["ref"] = tgt["fk"]
            if not ln.get("keyword"):
                ln["keyword"] = ""
        if row.get("linked"):
            row["linked"] = [ln for ln in row["linked"] if not ln.get("drop")]
        ep = row.get("enable_parent")
        if isinstance(ep, dict):  # {ref, flags} as the source writes it
            row["enable_parent_flags"] = ep.get("flags")
            ep = row["enable_parent"] = ep.get("ref")
        if ep and not is_key(str(ep)):
            tgt = by_our.get(ep)
            if tgt is None:
                problem(f"refs.jsonl: {row['id']}: enable parent {ep} is not in the place")
                row.pop("enable_parent")
            else:
                row["enable_parent"] = tgt["fk"]
    return {"refs": refs, "interiors": interiors, "by_id": by_our}


def kind_of(r: dict) -> str:
    return {"STAT": "static", "DOOR": "door", "FURN": "furniture", "CONT": "container", "LIGH": "light", "ACTI": "activator",
            "MSTT": "static", "FLOR": "plant", "TREE": "tree", "IDLM": "marker"}.get(r.get("base_type", ""), "clutter")


def pair_doors(S: dict) -> list[str]:
    """Each load door's teleport and arrival marker, both ways (the contract's door pair, place-studio.md). A place
    door names its partner by door.to_space + door.to_ref (the partner's id, or its source ref key in a copied space);
    the partner's own door field may be absent (it is paired from this side). One using door x lands at x's
    door.to_pos / to_rot when the place files give it (beside the partner, in the partner's space); else at
    `marker_by` (the source's marker carried to our door, or in front of the partner)."""
    by_id = S["by_id"]
    by_src = {(r["space"], r.get("src")): r for r in S["refs"] if r.get("src")}
    notes, pairs = [], []
    for r in S["refs"]:
        d = r.get("door")
        if not d or not d.get("to_space"):
            continue
        other = by_id.get(d["to_ref"]) or by_src.get((d["to_space"], d["to_ref"]))
        if other is None:
            problem(f"door {r['id']}: partner {d['to_space']}/{d['to_ref']} is not in the place")
            continue
        pairs.append((r, other))
    paired = set()
    for a, b in pairs:
        for x, y in ((a, b), (b, a)):
            d = x.get("door") or {}
            if d.get("to_pos") is not None and d.get("to_space") in (None, y["space"]):
                at = {"pos": [float(v) for v in d["to_pos"]], "rot": [float(v) for v in d.get("to_rot") or [0, 0, 0]]}
            else:
                at = marker_by(y, x)
            x["teleport"] = {"to": y["fk"], **at}
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


def tri_near(n, p) -> tuple[int, float]:
    """The triangle nearest p in plan and height together, and how far it is: a roof or deck over the spot never wins
    over the ground a step away beside it (a door's arrival under an overhang stands on the ground, not on the
    overhang's top). (-1, inf) for a mesh with no triangles."""
    t = np.asarray(n.tris["v"], np.int64)
    if not len(t):
        return -1, float("inf")
    v = np.asarray(n.verts, np.float64)
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    px, py, pz = float(p[0]), float(p[1]), float(p[2])
    d1 = (px - b[:, 0]) * (a[:, 1] - b[:, 1]) - (a[:, 0] - b[:, 0]) * (py - b[:, 1])
    d2 = (px - c[:, 0]) * (b[:, 1] - c[:, 1]) - (b[:, 0] - c[:, 0]) * (py - c[:, 1])
    d3 = (px - a[:, 0]) * (c[:, 1] - a[:, 1]) - (c[:, 0] - a[:, 0]) * (py - a[:, 1])
    inside = ~(((d1 < 0) | (d2 < 0) | (d3 < 0)) & ((d1 > 0) | (d2 > 0) | (d3 > 0)))
    cen = (a + b + c) / 3
    d = np.where(inside, 0.0, np.hypot(cen[:, 0] - px, cen[:, 1] - py)) + np.abs(cen[:, 2] - pz)
    i = int(np.argmin(d))
    return i, float(d[i])


def tri_under(n, p) -> int:
    return tri_near(n, p)[0]


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


_SRC_NAVM: dict[str, dict[str, bytes | None]] = {}  # plugin file -> navmesh form key -> its NVNM bytes (None: not in it)
_SRC_NAMES: dict[str, list[str]] = {}  # plugin file -> its masters then itself (a raw form id's index into these)


def source_names(plugin: str) -> list[str]:
    from tools.navmesh import esm
    if plugin not in _SRC_NAMES:
        _SRC_NAMES[plugin] = esm.masters(_plugin_path(plugin)) + [plugin]
    return _SRC_NAMES[plugin]


def raw_key(names: list[str], raw: int) -> str:
    """A raw form id of a plugin as a form key: its top byte indexes the plugin's masters, anything past them is its own."""
    return key_of(names[min(raw >> 24, len(names) - 1)], raw & 0xFFFFFF)


def source_navms(plugin: str, want: set[str]) -> dict[str, bytes | None]:
    """The interior navmeshes `want` (form keys) as `plugin` holds them: one read of the plugin for every key not
    asked of it before, so a run that asks for all its interiors' keys at once reads each plugin once."""
    from tools.navmesh import esm
    got = _SRC_NAVM.setdefault(plugin, {})
    miss = set(want) - got.keys()
    if miss:
        names = source_names(plugin)
        got.update(dict.fromkeys(miss))
        for rec in esm.records(_plugin_path(plugin), {b"NAVM"}, {b"CELL"}):
            k = raw_key(names, rec.fid)
            if k in miss:
                got[k] = next((p for s, p in esm.subrecords(rec.data) if s == b"NVNM"), None)
    return got


def source_interior_navmesh(I: dict) -> dict[str, dict]:
    """The source cell's own navmeshes by form key, each read from the plugin of the source whose version wins (the
    one no other holder masters): {tris, verts, cover, links: [(type, target navmesh key, triangle)]}. A link into
    another navmesh of the cell is kept; one out of the cell is opened. Door triangles are cleared (ours are set from
    our door pairs)."""
    from tools.navmesh import nvnm
    want = list(dict.fromkeys(I["src_navmesh"]))
    srcs: dict[str, tuple] = {}
    for pl in I.get("src_plugins") or [I["copy"]["plugin"]]:
        try:
            names = source_names(pl)
        except SystemExit:
            continue
        for key, payload in source_navms(pl, set(want)).items():
            if payload is None or key not in want:
                continue
            if key not in srcs or srcs[key][2] in names[:-1]:  # a plugin mastered on the holder so far overrides it
                srcs[key] = (nvnm.decode(payload), names, pl)
    srcs = {key: v for key, v in srcs.items() if len(v[0].tris)}
    out = {}
    for key in sorted(srcs):
        n, names, _ = srcs[key]
        tris = n.tris.copy()
        links = []
        for k in range(3):
            for i in np.flatnonzero(tris["flags"] & nvnm.EDGE_LINK[k]):
                e = int(tris["e"][i][k])
                ln = n.links[e] if 0 <= e < len(n.links) else None
                target = raw_key(names, int(ln["navm"])) if ln is not None else None
                if target in srcs and 0 <= int(ln["tri"]) < len(srcs[target][0].tris):
                    links.append((int(ln["type"]), target, int(ln["tri"])))
                    tris["e"][i][k] = len(links) - 1
                else:
                    tris["flags"][i] &= ~nvnm.EDGE_LINK[k] & 0xFFFF
                    tris["e"][i][k] = -1
        tris["flags"] &= ~nvnm.DOOR & 0xFFFF
        out[key] = {"tris": tris, "verts": n.verts.copy(), "cover": n.cover.copy(), "links": links}
    return out


def nav_islands(meshes: dict[str, dict]) -> int:
    """How many walkable islands a cell's navmeshes make: triangles joined by a shared edge or an edge link are one."""
    from tools.navmesh import nvnm
    par: dict = {}

    def root(x):
        while par.setdefault(x, x) != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    for key, m in meshes.items():
        t = m["tris"]
        for i in range(len(t)):
            root((key, i))
            for k in range(3):
                e = int(t["e"][i][k])
                if t["flags"][i] & nvnm.EDGE_LINK[k]:
                    _, target, tri = m["links"][e]
                    par[root((key, i))] = root((target, tri))
                elif 0 <= e < len(t):
                    par[root((key, i))] = root((key, e))
    return len({root(x) for x in list(par)})


def interior_navmesh(I: dict, S: dict, ids: Ids) -> list[dict]:
    """An interior's navmesh: its room's island (a `room` copy); else the source cell's own navmeshes when they make
    one walkable island (a source cell meshed in pieces that do not join is meshed again from its collision by the
    caller: `src_islands` on the interior says how many it had)."""
    from tools.navmesh import nvnm
    rm = I.get("room_mesh")
    if rm and rm["tris"]:
        return [mesh_navm(I, ids, rm["verts"], rm["tris"])]
    if rm or not I["copy"] or not I["src_navmesh"]:
        return []
    meshes = source_interior_navmesh(I)
    I["src_islands"] = nav_islands(meshes)
    if I["src_islands"] != 1:
        return []
    ours = {key: ids.local(f"navm:{I['space']}:{split_key(key)[1]:06X}") for key in meshes}
    cell_raw = raw_fid(NAV_SELF, split_key(I["fk"])[1])
    out = []
    for key, m in meshes.items():
        links = [(ty, raw_fid(NAV_SELF, ours[target]), tri) for ty, target, tri in m["links"]]
        nv = nvnm.Nvnm(0, None, cell_raw, m["verts"], m["tris"], np.array(links, nvnm.LINK) if links else np.zeros(0, nvnm.LINK))
        nv.cover = m["cover"]
        out.append({"fid": raw_fid(NAV_SELF, ours[key]), "nv": nv, "space": I["space"], "cell_raw": cell_raw})
    return out


def recast_refs(rows: list[dict], work: Path, tag: str, ground: bool) -> tuple[list, list]:
    """Collision of `rows` (refs of one interior) meshed by the same Recast run as the world's (ArgoniaNav, the same
    params): moved into synthetic cells, meshed, moved back and welded. `ground`: a plane just under the lowest
    collision (the floor a room's walls stand on), cut away outside the collision's bounds. -> (verts, tris)."""
    from tools.navmesh import params, stitch
    from tools.navmesh.__main__ import NAV_BIN, build_tool as nav_tool, game_data
    from tools.navmesh import placed
    coll = []
    for r in rows:
        f, local = split_key(r["base"])
        coll.append({"base": f"{local:06X}:{f}", "pos": r["pos"], "rot": r.get("rot") or [0.0, 0.0, 0.0],
                     "scale": r.get("scale", 1.0), "formKey": r["fk"], "box": collision_box(r)})
    tris, _ = placed.collide(coll, game_data(), {})
    if not len(tris):
        return [], []
    lo, hi = tris.reshape(-1, 3).min(axis=0), tris.reshape(-1, 3).max(axis=0)
    span = hi[:2] - lo[:2]
    ncx, ncy = int(span[0] // (CELL - 512)) + 1, int(span[1] // (CELL - 512)) + 1
    shift = np.array([256.0 - lo[0], 256.0 - lo[1], 0.0])  # the south-west corner 256 units into cell (0, 0)
    deep = float(lo[2]) - 2.0 if ground else -1.0e6
    mg = params.BORDER_SAMPLES + 2  # samples of margin round the box: ArgoniaNav's window reaches past the cell
    rows_n, cols_n = ncy * 32 + 1 + 2 * mg, ncx * 32 + 1 + 2 * mg
    d = work / f"int_{tag}"
    (d / "in").mkdir(parents=True, exist_ok=True)
    np.full((rows_n, cols_n), deep, np.float32).tofile(d / "in" / "height.f32")
    np.full((rows_n, cols_n), np.nan, np.float32).tofile(d / "in" / "water.f32")
    np.zeros((rows_n, cols_n), np.uint8).tofile(d / "in" / "flags.u8")
    np.zeros((ncy, ncx), np.uint8).tofile(d / "in" / "skip.u8")
    (tris + shift).astype(np.float32).tofile(d / "in" / "objects.f32")
    (d / "in" / "grid.json").write_text(json.dumps({"rows": rows_n, "cols": cols_n, "x0": -mg * 128.0, "ytop": float(ncy * CELL) + mg * 128.0, "step": 128.0,
                                                    "cells": [0, 0, ncx - 1, ncy - 1], "build_id": f"interior:{tag}", "water": -1e9,
                                                    "params": params.recast(), "objects": len(tris)}, indent=1))
    nav_tool()
    r = subprocess.run([str(NAV_BIN), "cells", "--in", str(d / "in"), "--out", str(d)], env=DOTNET_ENV, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"interior navmesh {tag}: ArgoniaNav failed\n{(r.stdout + r.stderr)[-2000:]}")
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
                if ground and not (lo[0] + 32 < cx_ < hi[0] - 32 and lo[1] + 32 < cy_ < hi[1] - 32):
                    continue  # the ground plane outside the room's walls
                tri_l.append([local[t[0]], local[t[1]], local[t[2]]])
    import shutil
    shutil.rmtree(d)
    used = sorted({i for t in tri_l for i in t})
    remap = {o: n for n, o in enumerate(used)}
    return [[float(c) for c in verts[i]] for i in used], [[remap[i] for i in t] for t in tri_l]


def mesh_navm(I: dict, ids: Ids, verts: list, tris: list) -> dict:
    from tools.navmesh import nvnm, stitch
    if len(tris) > 0x7FFF or len(verts) > 0xFFFF:  # NVNM counts triangles in 16 signed bits and vertices in 16
        problem(f"space {I['space']}: its generated navmesh has {len(tris)} triangles and {len(verts)} vertices, more than "
                f"one navmesh record holds (32767 and 65535)")
    mesh = stitch.Mesh(0, 0, verts, tris, [0] * len(tris))
    nb = stitch.neighbours(mesh)
    tr = np.zeros(len(mesh.tris), nvnm.TRI)
    for i, t in enumerate(mesh.tris):
        tr[i] = (t, nb[i], nvnm.FOUND, 0)
    cell_raw = raw_fid(NAV_SELF, split_key(I["fk"])[1])
    fid = raw_fid(NAV_SELF, ids.local(f"navm:{I['space']}:generated"))
    n = nvnm.Nvnm(0, None, cell_raw, np.asarray(mesh.verts, np.float32), tr)
    return {"fid": fid, "nv": n, "space": I["space"], "cell_raw": cell_raw}


def generate_interior_navmesh(I: dict, S: dict, ids: Ids, work: Path) -> list[dict]:
    """An interior's navmesh when its source has none: its own collision meshed (recast_refs, with a ground plane)."""
    rows = [r for r in S["refs"] if r["space"] == I["space"] and not r.get("disabled")
            and (r.get("kind") not in ("marker", "light", "door") or collision_box(r))]
    verts, tris = recast_refs(rows, work, I["space"], ground=True)
    return [mesh_navm(I, ids, verts, tris)] if tris else []


def components(tris: list) -> np.ndarray:
    """Each triangle's walkable island: triangles sharing an edge are one island."""
    par = list(range(len(tris)))

    def root(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    edge = {}
    for i, t in enumerate(tris):
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            k = (min(a, b), max(a, b))
            if k in edge:
                par[root(i)] = root(edge[k])
            else:
                edge[k] = i
    return np.array([root(i) for i in range(len(tris))], np.int64)


ROOM_RULE = "3"  # bump when room_partition's rule changes: its cache is keyed by it


def room_partition(copy_of: str, refs: list[dict], work: Path) -> dict:
    """The rooms of a source cell several houses share (the Build recipe's room rule; no hand numbers): the whole
    cell's collision (doors open) is meshed by our Recast run; a room is the island reached from one of the cell's
    load doors that lead out; every source ref belongs to the door island its position is nearest (islands reached from
    any door of the cell compete, so refs behind a door that leads nowhere stay in no room). Cached under
    out/places/rooms by the source refs' hash. -> {"rooms": {door fk: {"refs": set, "mesh": {verts, tris}}}}."""
    placed_rows = []
    for r in refs:  # the C# reader's rows (fk, base_type) or a bundle's (id, kind): one shape
        if "pos" not in r or r.get("deleted") or r.get("base_type") in ("NPC_", "LVLN") or r.get("kind") in ("actor", "npc"):
            continue
        d = r.get("door") or None
        placed_rows.append({"fk": r.get("fk") or r["id"], "base": r["base"], "pos": r["pos"], "rot": r.get("rot"),
                            "scale": r.get("scale", 1.0), "kind": kind_of(r) if "base_type" in r else r.get("kind"),
                            "out": bool(d) and (d.get("to_space") is not None if "to_space" in d else True),
                            "primitive": r.get("primitive")})
    src, cell = copy_of.split("/", 1)
    stamp = OUT / "bundles" / f"src.{src}" / "bundle.json"  # one key per source cell, whoever asks (drafter, studio, build)
    h = hashlib.sha256(f"{copy_of}|{sha256(stamp) if stamp.exists() else json.dumps([[r['fk'], r['pos']] for r in placed_rows])}|{ROOM_RULE}".encode()).hexdigest()[:20]
    cache = OUT / "rooms" / f"{copy_of.replace('/', '__')}.{h}.json"
    if cache.exists():
        got = json.loads(cache.read_text())
        return {"rooms": {k: {"refs": set(v["refs"]), "mesh": v["mesh"]} for k, v in got["rooms"].items()}}
    solid = [r for r in placed_rows if r["kind"] not in ("marker", "light", "door") or collision_box(r)]
    verts, tris = recast_refs(solid, work, "rooms", ground=False)
    V = np.asarray(verts, np.float64)
    comp = components(tris)
    cen = V[np.asarray(tris)].mean(axis=1)

    def island(p):
        return int(comp[np.argmin(np.linalg.norm(cen - np.asarray(p), axis=1))])
    doors = [r for r in placed_rows if r["kind"] == "door"]
    seed = {r["fk"]: island(r["pos"]) for r in doors}
    out_doors = {r["fk"] for r in doors if r["out"]}
    isl = sorted(set(seed.values()))
    best = np.full(len(placed_rows), np.inf)
    owner = np.full(len(placed_rows), -1)
    P = np.asarray([r["pos"] for r in placed_rows], np.float64)
    for c in isl:
        cc = cen[comp == c]
        d = np.array([np.linalg.norm(cc - p, axis=1).min() for p in P])
        better = d < best
        best[better], owner[better] = d[better], c
    rooms = {}
    for fk in sorted(out_doors):
        c = seed[fk]
        ti = np.nonzero(comp == c)[0]
        used = sorted({int(v) for t in ti for v in tris[t]})
        remap = {o: n for n, o in enumerate(used)}
        rooms[fk] = {"refs": sorted(placed_rows[i]["fk"] for i in np.nonzero(owner == c)[0]),
                     "mesh": {"verts": [verts[i] for i in used], "tris": [[remap[v] for v in tris[t]] for t in ti]}}
    cache.parent.mkdir(parents=True, exist_ok=True)
    tmpf = cache.with_suffix(".tmp")
    tmpf.write_text(json.dumps({"copy_of": copy_of, "rooms": rooms}))
    tmpf.replace(cache)
    return {"rooms": {k: {"refs": set(v["refs"]), "mesh": v["mesh"]} for k, v in rooms.items()}}


def exterior_navmesh(touched: set, objects, patched: dict, polylines, out: Path, cleared=()) -> tuple[list[dict], dict]:
    """tools.navmesh over the window (touched cells + NAV_RING rings) with the place's land and collision, cut
    round everything the world has placed there (its refs shards, as the world's own navmesh is) but the world
    refs the place switches off (`cleared`: their positions); the touched cells and their first ring are ours
    (their seams are re-split at the changed neighbour), the second ring must come out byte-equal to the world's
    own NAVM (the join is then edge for edge)."""
    from tools.navmesh import __main__ as nav, meshes, nvnm, stitch, world
    land = world.Land.load(WORLD_DIR)
    xs = [c[0] for c in touched]
    ys = [c[1] for c in touched]
    heights = None
    if patched:
        g = land.grid
        heights = np.array(land.heights(), np.float32)
        for (gx, gy), v in patched.items():
            heights[g.cy_top * 32 + 32 - gy, gx - g.cx0 * 32] = v * 8.0

    def rings(n):
        out_, cur = [set(touched)], set(touched)
        for _ in range(n):
            nxt = {(x + dx, y + dy) for x, y in cur for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
            out_.append(nxt - cur)
            cur = nxt
        return out_

    # grow the window until its last trusted ring (the one inside the cut edge) matches the world's own NAVM:
    # we ship ring 1 and every cell inside that came out different, so every link out lands on an unchanged mesh
    reach = NAV_RING
    while True:
        box = (min(xs) - reach, min(ys) - reach, max(xs) + reach, max(ys) + reach)
        was = stitch.STACKED, meshes.PROFILE
        stitch.STACKED = True  # decks and steps on a cell line: seams split and linked by height too (the world's off)
        meshes.PROFILE = "NewWorld"  # the world's placed meshes are found by the new world's mod order
        try:
            res = nav.build(out, box, WORLD_DIR, run_check=False, objects=objects, heights=heights, polylines=polylines, land=land,
                            refs=WORLD_DIR / "refs", cleared=cleared)
        finally:
            stitch.STACKED, meshes.PROFILE = was
        pl = res.get("placed") or {}
        if pl.get("cleared") != len(cleared) or pl.get("unresolved"):
            problem(f"navmesh: the world's refs shards hold {pl.get('cleared')} of the {len(cleared)} world refs the place clears, and "
                    f"{pl.get('unresolved')} of their meshes are not read: the world file and out/newworld/plugin/refs are not of one build")
        built, world_rows = {}, {}
        for p in sorted((out / "navm").glob("cy*.jsonl.gz")):
            for ln in gzip.open(p, "rt"):
                e = json.loads(ln)
                built[(e["x"], e["y"])] = e
        for p in sorted((WORLD_NAV / "navm").glob("cy*.jsonl.gz")):
            cy = int(p.name[2:6])
            if box[1] <= cy <= box[3]:
                for ln in gzip.open(p, "rt"):
                    e = json.loads(ln)
                    world_rows[(e["x"], e["y"])] = e
        R = rings(reach)

        def differ(cells):
            return [c for c in sorted(cells) if (c in built or c in world_rows)
                    and built.get(c, {}).get("navm") != world_rows.get(c, {}).get("navm")]
        inner = set().union(*R[2:reach])          # rings 2 .. reach-1: built far enough from the cut to be trusted
        last = R[reach - 1]
        if not differ(last) or reach >= NAV_RING + 3:
            break
        reach += 1
    ring1 = R[0] | R[1]
    seam = {"reach": reach, "placed": {k: pl.get(k) for k in ("refs", "collidable", "fed", "cleared")}, "trusted_cells": sum(1 for c in inner if c in built or c in world_rows),
            "differ": [list(c) for c in differ(inner)], "last_ring_differ": [list(c) for c in differ(last)]}
    if seam["last_ring_differ"]:
        problem(f"navmesh: {reach} rings out from the place its cells still come out unlike the world's "
                f"({seam['last_ring_differ'][:6]}): the place's navmesh cannot be joined to the world's edge for edge")
    ship = ring1 | {tuple(c) for c in seam["differ"]}
    mine = []
    navi = json.loads((out / "navi.json").read_text())
    nvmis = {}
    from tools.navmesh.esm import subrecords
    import struct
    rec = base64.b64decode(navi["navi"])
    for s, p in subrecords(rec[24:]):
        if s == b"NVMI":
            nvmis[struct.unpack_from("<I", p, 0)[0]] = p
    for c in sorted(ship):
        e = built.get(c)
        if e is None:
            if c in world_rows:  # the world's mesh stays in the game, linked to neighbours that no longer answer it
                problem(f"navmesh: cell {c[0]},{c[1]} has walkable ground in the world and none once the place stands on it")
            continue
        rec = base64.b64decode(e["navm"])
        nv = nvnm.decode(next(p for s, p in subrecords(rec[24:]) if s == b"NVNM"))
        fid = struct.unpack_from("<I", rec, 12)[0]
        mine.append({"fid": fid, "nv": nv, "space": "exterior", "cell": list(c), "nvmi": nvmis.get(fid)})
    seam["one_way_unlinked"] = unlink_one_way(mine)
    seam["joined_edges"] = join_seams(mine)
    return mine, {"box": list(box), "times": res.get("times"), "seam": seam}


def unlink_one_way(navs: list[dict]) -> int:
    """Open every edge link between two shipped meshes that the other side does not answer (the stitch can leave a
    few); join_seams then pairs those edges again edge for edge. Returns how many links were opened."""
    from tools.navmesh import nvnm
    by_fid = {n["fid"] & 0xFFFFFF: n for n in navs if n["space"] == "exterior"}

    def answers(o, tt, fid, i):
        t = o["nv"].tris[tt]
        return any(t["flags"] & nvnm.EDGE_LINK[q] and int(o["nv"].links[t["e"][q]]["navm"]) & 0xFFFFFF == fid
                   and int(o["nv"].links[t["e"][q]]["tri"]) == i for q in range(3))
    drop = []
    for f, n in by_fid.items():
        nv = n["nv"]
        for i, t in enumerate(nv.tris):
            for k in range(3):
                if not t["flags"] & nvnm.EDGE_LINK[k]:
                    continue
                L = nv.links[t["e"][k]]
                o = by_fid.get(int(L["navm"]) & 0xFFFFFF)
                tt = int(L["tri"])
                if o is not None and (not 0 <= tt < len(o["nv"].tris) or not answers(o, tt, f, i)):
                    drop.append((n, i, k))
    for n, i, k in drop:
        n["nv"].tris["e"][i][k] = -1
        n["nv"].tris["flags"][i] &= ~nvnm.EDGE_LINK[k] & 0xFFFF
        n["joined"] = True
    for n in {id(n): n for n, _, _ in drop}.values():
        prune_links(n["nv"])
    return len(drop)


def prune_links(nv) -> int:
    """Drop every edge link no triangle edge names (an opened link's row), renumbering the rest: the NVNM's link table
    and the NVMI's list of linked navmeshes, read from it, then say only what is joined. Returns how many went."""
    from tools.navmesh import nvnm
    if not len(nv.tris) or not len(nv.links):
        return 0
    linked = [(nv.tris["flags"] & nvnm.EDGE_LINK[k]) != 0 for k in range(3)]
    used = np.unique(np.concatenate([nv.tris["e"][linked[k], k] for k in range(3)]).astype(np.int64))
    used = used[(used >= 0) & (used < len(nv.links))]
    gone = len(nv.links) - len(used)
    if gone:
        remap = -np.ones(len(nv.links), np.int64)
        remap[used] = np.arange(len(used))
        for k in range(3):
            nv.tris["e"][linked[k], k] = remap[nv.tris["e"][linked[k], k]]
        nv.links = nv.links[used].copy()
    return gone


def join_seams(navs: list[dict], tol_z: float = 32.0) -> int:
    """Join, edge for edge, every open edge on the seam between two shipped cells to the matching open edge across it
    (same two end points in plan, heights within tol_z): a portal link both ways. Returns how many pairs joined."""
    from tools.navmesh import nvnm
    by_cell = {tuple(n["cell"]): n for n in navs if n["space"] == "exterior"}

    def open_edges(n, line_axis, line_v):
        """The mesh's open edges lying on one cell line: (the edge's span along the line, triangle, edge, mean height)."""
        nv, out = n["nv"], []
        v = np.asarray(nv.verts, np.float64)
        for k in range(3):
            a, b = v[nv.tris["v"][:, k]], v[nv.tris["v"][:, (k + 1) % 3]]
            on = (nv.tris["e"][:, k] == -1) & ((nv.tris["flags"] & nvnm.EDGE_LINK[k]) == 0) \
                & (np.abs(a[:, line_axis] - line_v) < 1) & (np.abs(b[:, line_axis] - line_v) < 1)
            for i in np.flatnonzero(on):
                key = tuple(sorted((round(float(a[i, 1 - line_axis])), round(float(b[i, 1 - line_axis])))))
                out.append((key, int(i), k, (float(a[i, 2]) + float(b[i, 2])) / 2))
        return sorted(out)

    def link(n, i, k, fid, ti):
        nv = n["nv"]
        nv.links = np.append(nv.links, np.array([(nvnm.PORTAL, fid, ti)], nvnm.LINK))
        nv.tris["e"][i][k] = len(nv.links) - 1
        nv.tris["flags"][i] |= nvnm.EDGE_LINK[k]
        n["joined"] = True

    joined = 0
    for (cx, cy), n in sorted(by_cell.items()):
        for axis, o_cell in ((0, (cx + 1, cy)), (1, (cx, cy + 1))):
            o = by_cell.get(o_cell)
            if o is None:
                continue
            v = (cx + 1) * CELL if axis == 0 else (cy + 1) * CELL
            mine_e, theirs = open_edges(n, axis, v), open_edges(o, axis, v)
            # pair by the longest shared stretch of seam at a like height (the two sides may split the seam differently)
            pairs = []
            for ka, i, k, za in mine_e:
                for kb, j, q, zb in theirs:
                    ov = min(ka[1], kb[1]) - max(ka[0], kb[0])
                    if ov > 0 and abs(za - zb) <= tol_z and ov >= 0.5 * min(ka[1] - ka[0], kb[1] - kb[0]):
                        pairs.append((-ov, i, k, j, q))
            used_a, used_b = set(), set()
            for _, i, k, j, q in sorted(pairs):
                if (i, k) in used_a or (j, q) in used_b:
                    continue
                used_a.add((i, k))
                used_b.add((j, q))
                link(n, i, k, o["fid"], j)
                link(o, j, q, n["fid"], i)
                joined += 1
    return joined


def finish_navmesh(navs: list[dict], S: dict, world_fid: int) -> tuple[list[dict], list[str]]:
    """Door triangles both sides; then each NAVM record and its NVMI."""
    from tools.navmesh import nvnm
    doors_of: dict[int, list[int]] = {}
    by_space: dict[str, list[dict]] = {}
    by_cell: dict[tuple, dict] = {}
    for n in navs:
        by_space.setdefault(n["space"], []).append(n)
        if n["space"] == "exterior":
            by_cell[tuple(n["cell"])] = n
    by_fk = {r["fk"]: r for r in S["refs"]}
    notes = []
    for r in S["refs"]:
        t = r.get("teleport")
        if not t or r.get("kind") == "marker":
            continue  # a prison marker's teleport is an arrest's, never a way people walk: no door triangle
        at = by_fk[t["to"]]["teleport"]["pos"]  # one arrives by r through the partner: the partner's marker stands by r
        if r["space"] == "exterior":  # the arrival's own cell first, then the cells round it (an arrival by a cell line)
            cx, cy = cell_of(at[0], at[1])
            cand = [by_cell[c] for c in [(cx, cy)] + [(cx + dx, cy + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
                    if c in by_cell]
        else:
            cand = by_space.get(r["space"], [])
        # the mesh that holds the triangle nearest the arrival: an interior may have several, a cell line may run by
        near = [(tri_near(n["nv"], at)[1], i) for i, n in enumerate(cand)]
        near = [x for x in near if x[0] < float("inf")]
        if not near:
            notes.append(f"door {r['id']}: no navmesh under its arrival point")
            continue
        n = cand[min(near)[1]]
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
            if mi is None or doors or n.get("joined"):  # rebuild the NVMI with the doors and joins: same layout as the stitch's
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
        box = collision_box(r)
        if r["space"] != "exterior" or (r.get("kind") not in SOLID_KINDS and box is None) or r.get("disabled"):
            continue
        f, local = split_key(r["base"])
        rows.append({"base": f"{local:06X}:{f}", "pos": r["pos"], "rot": r["rot"], "scale": r.get("scale", 1.0), "formKey": r["fk"],
                     "box": box})
    if not rows:
        return None, {"refs": 0}
    return placed.collide(rows, game_data(), {})


# ---- one place --------------------------------------------------------------------------------------------------------

def plan_place(pid: str, pdir: Path, out: Path, no_navmesh: bool, plan_only: bool = False) -> dict:
    import shutil
    import tempfile
    (out / "tmp").mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=f"{pid}.", dir=out / "tmp"))  # this run's own: runs side by side never collide
    try:
        return _plan_place(pid, pdir, out, no_navmesh, plan_only, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---- shrines ----------------------------------------------------------------------------------------------------

SHRINE = {  # the vanilla blessing, measured on Skyrim.esm's TempleBlessingScript shrines
    "spell_from": "Skyrim.esm:0FB999",      # AltarStendarrSpell: Self, Fire and Forget, a fortify effect for 28800 s, then Cure Disease 25
    "mgef_from": "Skyrim.esm:0FB991",       # FortifyBlockFFSelf: Fire and Forget, Self, 28800 s; its keyword + DispelWithKeywords make blessings replace each other
    "swap_effect": "Skyrim.esm:0FB991",     # the spell's fortify effect, replaced by ours
    "remove_msg": "Skyrim.esm:10E4F9",      # AltarRemoveMsg, shared by every vanilla shrine
    "magnitude": 10, "duration": 28800,     # vanilla: 25 for Health, Magicka, Stamina; 10 for every other blessed value
    "activator": "Hist", "spell": "Blessing of the Hist", "message": "You are blessed by the Hist.",
    "effect_text": "Resist <mag>% of disease for <dur> seconds.",
}


def plan_shrines(P: dict, S: dict, ids: Ids) -> list[dict]:
    """Each `shrine` row of place.json stations.added becomes the vanilla temple shrine: the ref keeps its id and form
    key, its base becomes an activator of ours with the old base's model and TempleBlessingScript, whose blessing is a
    spell of ours (Resist Disease, fixed magnitude, eight hours), a message of ours and vanilla's remove message."""
    from tools.places import people as ppl
    out = []
    for row in ((P["place"].get("stations") or {}).get("added") or []):
        if row.get("station") != "shrine":
            continue
        ref = S["by_id"].get(row.get("id"))
        if ref is None:
            problem(f"place.json: stations.added shrine {row.get('id')} is not a ref of the place")
            continue
        n = ppl._edid(ref["id"])
        pid = ids.path.parent.name
        acti, spel, mesg, mgef = (ids(f"{k}:shrine:{ref['id']}") for k in ("acti", "spel", "mesg", "mgef"))
        out.append({
            "ref": ref["fk"], "ref_id": ref["id"],
            "activator": {"fk": acti, "edid": f"ANP_{pid}_Shrine_{n}", "name": SHRINE["activator"], "model_from": ref["base"],
                          "scripts": [{"name": "TempleBlessingScript", "props": [
                              {"name": "TempleBlessing", "type": "object", "value": spel},
                              {"name": "BlessingMessage", "type": "object", "value": mesg},
                              {"name": "AltarRemoveMsg", "type": "object", "value": SHRINE["remove_msg"]}]}]},
            "mgef": {"fk": mgef, "edid": f"ANP_{pid}_ResistDiseaseFFSelf", "from": SHRINE["mgef_from"], "actor_value": "ResistDisease",
                     "name": "Resist Disease", "description": SHRINE["effect_text"]},
            "spell": {"fk": spel, "edid": f"ANP_{pid}_Blessing_{n}", "name": SHRINE["spell"], "from": SHRINE["spell_from"],
                      "swap_effect": SHRINE["swap_effect"], "mgef": mgef, "magnitude": SHRINE["magnitude"], "duration": SHRINE["duration"]},
            "message": {"fk": mesg, "edid": f"ANP_{pid}_BlessingMsg_{n}", "text": SHRINE["message"]},
        })
        ref["base"] = acti  # last: the navmesh and the clearance read the old base's model
    return out


# ---- travel -----------------------------------------------------------------------------------------------------

TRAVEL = {  # vanilla's carriage (Skyrim.esm DialogueCarriageSystem), measured: a start-game-enabled quest holding the
    # topics; each destination's INFO gates on the player's gold and runs a fragment that takes the fare and
    # fast-travels (Game.FastTravel, which works with map travel off, as the carriages do in Survival). One compiled
    # script (papyrus/TIF_ARG_BoatTravel.psc) serves every line of every mode; its properties are set per INFO.
    "script": "TIF_ARG_BoatTravel", "gold": "Skyrim.esm:00000F", "quest_name": "Passage",
    "lines": {
        "boat": {"hub": "I need passage.", "hub_reply": "Where to? Say the name.",
                 "prompt": "Take me to {name} ({fare} gold).", "reply": "{name}, then. Sit low in the boat."},
        "coach": {"hub": "I need a ride.", "hub_reply": "We keep to the old road. Where to?",
                  "prompt": "Take me to {name} ({fare} gold).", "reply": "{name}, then. Climb up and hold on."},
        "rootworm": {"hub": "I would ride the rootworm.", "hub_reply": "The worm follows the roots. Which tree?",
                     "prompt": "To the tree at {name} ({fare} gold).", "reply": "{name}. Breathe out. Do not fight it."},
    },
}


def arrival(dest: str, markers: dict) -> str | None:
    """Where a passage to a place lands: the place's map marker in the world ESM (every settlement has one, on its
    ground); None when the world gives none, and the route then waits on that place."""
    return markers.get("ANW_MapMarker_" + dest.replace("-", "_"))


def travel_routes(pid: str) -> dict[str, list[dict]]:
    """The place's routes by mode, from the network (travel_route), nearest first."""
    out: dict[str, list[dict]] = {}
    for r in sorted(jsonl(DB / "travel_route.jsonl"), key=lambda r: (r["travel_mode_id"], r["distance_m"])):
        if r["from_place_id"] == pid:
            out.setdefault(r["travel_mode_id"], []).append(r)
    return out


def plan_travel(P: dict, people: dict, ids: Ids, facts: dict) -> tuple[list[dict], list[str]]:
    """The place's travel service, as vanilla's carriages do it: per place a quest of ours (start-game-enabled); per
    operator of a stop (the person whose people.jsonl service is the stop's give) a top-level topic, whose line links
    one topic per route of the stop's mode; each destination's INFO needs the operator's travel faction and the
    route's fare in gold, and runs TIF_ARG_BoatTravel with the destination's arrival point and the fare. A route whose
    destination has no arrival point yet is not offered: it is returned as waiting on that place (the record keeps
    the promise). A stop with nobody serving it is a problem."""
    pid = P["place"]["place_id"]
    routes = travel_routes(pid)
    stops = [s for s in jsonl(DB / "travel_stop.jsonl") if s["place_id"] == pid]
    if not stops:
        return [], []
    from tools.places import people as ppl
    names = {r["id"]: r["name"] for r in jsonl(DB / "place.jsonl")}
    markers = facts.get("map_markers") or {}
    line = {"fk": ids("quest:boat"), "edid": f"ANP_{pid}_Travel", "name": TRAVEL["quest_name"]}
    out = {"place_id": pid, "script": TRAVEL["script"], "gold": TRAVEL["gold"], "quest": line, "boatmen": []}
    waiting: list[str] = []
    npcs = (people or {}).get("npcs", [])
    for s in stops:
        mode = s["travel_mode_id"]
        ops = [n for n in npcs if mode in (n.get("travel") or {})]
        if not ops:
            problem(f"travel: the {mode} stop (give {s['give_seq']}) has nobody serving it: people.jsonl lists no "
                    f"service at seq {s['give_seq']}")
            continue
        words = TRAVEL["lines"][mode]
        for n in ops:
            who = n["id"]
            e = ppl._edid(who)
            key = f"{mode}:{who}" if mode != "boat" else who   # a boatman's keys stand from before the other modes
            hub = {"topic": ids(f"dial:boat:{key}"), "info": ids(f"info:boat:{key}"), "edid": f"ANP_{pid}_{mode.title()}_{e}_Hub",
                   "prompt": words["hub"], "reply": words["hub_reply"]}
            dests = []
            for r in routes.get(mode, []):
                did = r["to_place_id"]
                mk = arrival(did, markers)
                if mk is None:
                    waiting.append(f"{mode} to {names[did]} ({did}): waits on that place (no arrival point in {WORLD})")
                    continue
                dests.append({"place": did, "name": names[did], "marker": mk, "fare": r["fare"],
                              "topic": ids(f"dial:boat:{key}:{did}"), "info": ids(f"info:boat:{key}:{did}"),
                              "edid": f"ANP_{pid}_{mode.title()}_{e}_{ppl._edid(did)}",
                              "prompt": words["prompt"].format(name=names[did], fare=r["fare"]),
                              "reply": words["reply"].format(name=names[did])})
            out["boatmen"].append({"who": who, "mode": mode, "npc": n["fk"], "faction": n["travel"][mode],
                                   "branch": ids(f"brnc:boat:{key}"), "branch_edid": f"ANP_{pid}_{mode.title()}_{e}_Branch",
                                   "hub": hub, "dests": dests})
    return ([out] if out["boatmen"] else []), sorted(set(waiting))


def _plan_place(pid: str, pdir: Path, out: Path, no_navmesh: bool, plan_only: bool, tmp: Path) -> dict:
    t0 = time.time()
    P = read_place(pdir)
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
    path_walked: set = set()
    path_layers = plan_paths(P["paths"], facts, path_walked)
    clear = plan_clear(P["clear"], facts)
    facts["patched"] = patched  # the land as built: people's stops outside are seated on it
    from tools.places import people as ppl
    people = ppl.plan(P, S, ids, facts, notes)
    from tools.places.stock import plan as stockplan  # the place's stock (place-studio.md, Stock), before the navmesh reads the refs
    stock = stockplan.plan(P, S, people, ids, problem, notes)
    # land rows: heights and path layers merged per cell
    by_cell = {(r["x"], r["y"]): r for r in land}
    for c, quads in path_layers.items():
        f = facts["by_cell"].get(c)
        if f is None or f.get("land") is None:
            problem(f"path reaches cell {c}, which the world has no LAND for")
            continue
        row = by_cell.setdefault(c, {"x": c[0], "y": c[1], "land": f["land"]})
        row["quads"] = quads
    # navmesh
    nav_info = {}
    navs: list[dict] = []
    if not no_navmesh:
        solid = [r for r in S["refs"] if r["space"] == "exterior" and (r.get("kind") in SOLID_KINDS or collision_box(r))]
        touched = {tuple(r["cell"]) for r in solid} | land_changed | path_walked
        if touched:
            objects, tally = collision_objects(S["refs"])
            polylines = navworld.road_polylines() + [[(x, y, False) for x, y in p["points"]] for p in P["paths"]]
            ext, nav_info = exterior_navmesh(touched, objects, patched, polylines, out / "navmesh" / pid,
                                              [r["pos"] for r in clear])
            nav_info["collision"] = tally
            navs += ext
        copied = [I for I in S["interiors"] if I["copy"] and not I.get("room_mesh")]
        for pl in dict.fromkeys(pl for I in copied for pl in I["src_plugins"]):  # each source plugin is read once
            try:
                source_navms(pl, {k for I in copied if pl in I["src_plugins"] for k in I["src_navmesh"]})
            except SystemExit:
                pass
        for I in S["interiors"]:
            got = interior_navmesh(I, S, ids)
            if not got:
                got = generate_interior_navmesh(I, S, ids, tmp)
                if got:
                    why = (f"the source's navmesh is in {I['src_islands']} pieces that do not join" if I.get("src_islands", 0) > 1
                           else "the source has no navmesh over the kept room")
                    notes.append(f"interior {I['space']}: {why}; generated ({sum(len(n['nv'].tris) for n in got)} triangles)")
                else:
                    problem(f"space {I['space']}: no navmesh (the source has none and its collision gives no floor): "
                            f"nobody can walk in it")
            navs += got
    world_raw = nav_fid(facts["worldspace"])
    nav_rows, n2 = finish_navmesh(navs, S, world_raw)
    notes += n2
    boats, waiting = plan_travel(P, people, ids, facts)
    notes += [f"travel: {x}" for x in waiting]
    shrines = plan_shrines(P, S, ids)  # after the navmesh: it swaps the shrine refs' bases, which the navmesh reads
    if not plan_only:
        ids.save()  # a plan-only run never writes form ids: it may run beside a build
    plan = {
        "place_id": pid, "world": {"worldspace": facts["worldspace"], "top_cell": facts["top_cell"], "esm": WORLD},
        "cells": sorted([{"x": c[0], "y": c[1], "cell": facts["by_cell"][c]["fk"]} for c in ask if c in facts["by_cell"]],
                        key=lambda r: (r["x"], r["y"])),
        "refs": S["refs"], "interiors": [{k: v for k, v in I.items() if k != "fk_of_src"} for I in S["interiors"]],
        "land": sorted(by_cell.values(), key=lambda r: (r["x"], r["y"])), "clear": clear,
        "navmesh": {"masters": NAV_MASTERS, "self": PLUGIN, "navi": key_of("Skyrim.esm", NAVI_FID), "navm": nav_rows},
        "people": people, "boats": boats, "travel_waiting": waiting, "shrines": shrines, "stock": stock, "notes": notes,
        "stats": {"plan_s": round(time.time() - t0, 1), "nav": nav_info},
    }
    return plan


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places build")
    ap.add_argument("places", nargs="*")
    ap.add_argument("--places-dir", default=str(PLACES))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--no-navmesh", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--keep-going", action="store_true", help="build despite problems (they are still listed): to see what else fails")
    ap.add_argument("--plan", action="store_true", help="plan only (no navmesh, no plugin): list every problem, exit 1 if any")
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
        if not a.force and not a.plan and kp.exists() and kp.read_text() == key and (shard / "plan.json").exists():
            report["places"][pid] = {"rebuilt": False}
            log(f"build {pid}: unchanged")
            continue
        t1 = time.time()
        PROBLEMS.clear()
        plan = plan_place(pid, pdir, out, a.no_navmesh or a.plan, plan_only=a.plan)
        if PROBLEMS or a.plan:
            for m in PROBLEMS:
                print(f"{pid}: {m}")
            log(f"build {pid}: planned in {time.time() - t1:.1f} s; {len(PROBLEMS)} problems")
            if PROBLEMS and not a.keep_going:
                return 1
            if a.plan:
                continue
        atomic_json(shard / "plan.json", plan)
        kp.write_text(key)
        report["places"][pid] = {"rebuilt": True, "plan_s": round(time.time() - t1, 1), "notes": plan["notes"]}
        log(f"build {pid}: planned in {time.time() - t1:.1f} s; {len(plan['refs'])} refs, {len(plan['interiors'])} interiors, "
            f"{len(plan['land'])} land cells, {len(plan['clear'])} cleared, {len(plan['navmesh']['navm'])} navmeshes")
        for n in plan["notes"]:
            log(f"  note: {n}")
    if a.plan:
        return 0
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
