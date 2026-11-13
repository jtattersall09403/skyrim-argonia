"""Placement of the new world's flora, rocks, cliffs, seabed and road dressing (nw-02 step 8).

Inputs: the landcover (out/newworld/landcover: habitat, region, water kind, shore/run/road distances, canopy,
slope, flags; legend.json), the heightmap it was built on (out/newworld/terrain/heightmap.npy), the land manifest's
cell grid (out/newworld/plugin/land/manifest.json), the db (region_flora, flora_base, flora_family, flora_class,
flora_guild(_member), habitat, water_kind, road, road_vertex, road_class, road_node, place), the flora catalogue's
cliff open-side measures (out/newworld/research/flora_catalogue.json) and the base records' own plugins (OBND, MODL,
record type, read with tools/navmesh/esm.py).

Output (out/newworld/plugin/placed/flora/, never git): the placement as the rules made it. The edits pass
(edits.py) writes it, with the owner's edits of single things applied, to out/newworld/plugin/refs/flora/, the shared
placed-refs hook (tools/newworld/world/cells.py; written into the ESM by ArgoniaPlugin `newworld write`, which links
a base in an allowed master and copies any other as our own record with ForeignCopy.cs). Both folders hold:
    cy+NNN.jsonl     one placed reference a line, cells of that row west to east:
                     {"base": "<plugin>:<editor id>", "x", "y", "z" (units), "rx", "ry", "rz" (radians: Skyrim's
                      clockwise angles, z then y then x), "scale", "cell": [cx, cy], "cls" (flora class or
                      road_<kind>), "db" (flora_base id or dressing kind), "key": the base's "XXXXXX:<plugin>",
                      "pos": [x, y, z], "rot": [rx, ry, rz], "model": its MODL (the navmesh's obstacle reader uses
                      pos, rot, scale and model), "id": the reference's identity, "fid": its form id (six hex
                      digits) in the world file}
    bases.json       every base used: key, ref, copied (not in a master), sig, model, obnd, edid, plugin, db_id
    manifest.json    key, build id, counts, per-cell budget, refusal tally, timing.

A reference's identity is `flora/<cx>,<cy>/<h>`: this producer, the cell the rules put it in, and ten hex digits of
the digest of what the rules decided there (its base and the x, y drawn for it). It is the same after any rebuild
that puts the same thing on the same spot, whatever else is placed or in what order, and it stays the thing's name
when an edit moves it or changes its base. Its form id follows from the identity alone (form_ids): a slot of
FID_FIRST..FID_LAST by the identity's digest, a taken slot passed over in the identities' sorted order, so a
reference keeps its id while it stands and an edit renumbers nothing. The navmesh's ids lie inside that range and
are never given (FID_HOLE).

The recipe (numbers from research/nw-02-flora-rules.md, nw-02-ground-water-rules.md, nw-02-salvage.md):
1. Per cell (seeded by the seed and the cell: a cell rebuilds alone and identically), per (region, habitat) stratum
   of its samples, per base of region_flora: clump centres ~ Poisson(density x area / cluster size), members
   1 + Poisson(cluster - 1) scattered round the centre; guild partners (flora_guild) stamped beside an anchor.
   The first 20 m from water (shore distance) get 1.7 x the small-scatter density (vanilla 2.0-2.8 vs 1.3-1.5 per
   100 m2). Margin cells: canopy trees, palms, boulders and cliffs only, at 0.15 x.
2. Refusals: another habitat under the point; a place pad; within the road surface edge (class paint_full_m) plus a
   clearance (trees 2.5 m, rocks 1.0 m, other flora 0.5 m, from the study's p5); anything whose collision at
   walking height comes within an actor's clearance of the road's walking width, whatever its position (step 6);
   water: flowing kinds carry no tree,
   shrub or log; standing water only to the family's standing_water_max_m and trees only in the habitats where
   trees stand in water; water-only plants 0.2 m and deeper; seabed families in their depth band; slope windows
   (trees and palms 35 deg, shrubs 40, herbs 45, cliffs from 28); the canopy field thins trees (landcover glades,
   verges, banks); dry trees keep 2 m from running water.
3. Seating: pivot z = ground - sink x scale, the sink drawn in the base's measured IQR (flora_base sink_lo/hi) or its
   median, the class value when unmeasured; rocks and cliffs sink their base's measured sink (class ratio x height
   when under 20 measured refs) and further when needed so the mesh bottom is under the lowest ground of its
   footprint (no visible open underside). Tilt: class tilt factor x ground slope, capped; a quarter of boulders
   upright. Yaw uniform, except cliff and pile shells with an open back: yaw = open azimuth - uphill azimuth
   (clockwise yaw) +- 30 deg, so the open side faces into the hill; shells of unmeasured open side are not placed.
4. Spacing: 1 m between any two refs (points within 0.5 m of a cell edge are refused, so it holds across cells),
   2.2 m between trunks, cliffs 0.6 x footprint, nothing small inside a rock's footprint. Budget: 162 natural refs
   a cell (vanilla max), lowest priority dropped first.
5. Road dressing per km within 10 m of the edge (study 2.4): rock piles 40 at 1-4 m out, boulders 30 at 2.5-7 m,
   cairns 3 at 1.5-4 m (KoTM's Argonian-textured vanilla rocks); BM&V's own signpost beside each junction at 0.8 m;
   KoTM's woven and Saxhleel fences along roads within 150 m of a farm, estate or homestead.
6. The road's walking width stays clear (road_shortfall): no voxel column a reference's collision blocks (solid
   over the climb and under an actor's height: tools/navmesh/solid.py, the navmesh's own reading) has its centre
   within ROAD_BODY_CLEAR of the walking width, the wider of the class's surface (paint_full_m) and the strip the
   navmesh marks as road (tools.navmesh.inputs.ROAD_HALF_UNITS) either side of the spine. Skyrim's navmesh is cut
   round a plant, a rock or a log whose collision rises to body height whatever its width
   (docs/research/nw-02-walk5-navmesh.md), so a wide hull at a large scale is kept off the road by that hull. A
   natural reference that falls short is refused; road dressing is moved straight out from the road by what it
   falls short (its offset is its collision's near side), and dropped only when four moves do not clear it.
7. Seating by the mesh (audit.py), last, over every placed thing, its x, y and form id kept: a standing tree's or a
   stump's trunk foot ring at or below the ground all round (slope included), a lying log's bulk resting on the ground
   along its length, a rock or cliff shell's open rim buried (its yaw turned to the one that needs least burial). A
   thing that would need burial past EXTRA_SINK_MAX of its height is not placed there. The audit is the stage's check.
"""
from __future__ import annotations

import functools
import hashlib
import json
import math
import os
import time
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from tools.newworld import idspace

REPO = Path(__file__).resolve().parents[3]
DB = REPO / "newworld/story/data/db"
OUT = REPO / "out/newworld"
LC = OUT / "landcover"
PLACED = OUT / "plugin/placed/flora"  # the placement as the rules made it: read by the edits pass alone
REFS = OUT / "plugin/refs/flora"  # this producer's shards with the edits applied (tools/newworld/world/cells.py: the refs hook)
FID_FIRST, FID_LAST = idspace.PLACED  # the world file's form ids for references placed by rule (NewWorld.cs),
FID_HOLE = idspace.HOLE  # but for the navmesh's own in their midst (tools/newworld/idspace.py: every allocator's range)
MANIFEST = OUT / "plugin/land/manifest.json"
CATALOGUE = OUT / "research/flora_catalogue.json"
DATA = Path(os.environ.get("ARGONIA_GAME_ROOT", Path.home() / "games/skyrimse")) / "Data"
MO2 = Path(os.environ.get("ARGONIA_STACK") or Path.home() / ".argonia/stack") / "MO2/mods"
ESM = "ArgoniaNewWorld.esm"
MASTERS = ("Skyrim.esm", "Update.esm", "Black Marsh.esm")
SEED = 0x5EA7
UPM = 70.0
SAMPLE = 128.0
CELL = 4096.0
SAMPLE_HA = (SAMPLE / UPM) ** 2 / 10_000
CAP = 162  # natural refs a cell: vanilla forested max (salvage: VANILLA_MAX)
EDGE_M = 0.5  # refused within this of a cell edge: the 1 m spacing holds across cells
MIN_SPACING_M = 1.0
TRUNK_SPACING_M = 2.2
EDGE_BOOST = 1.7
TWIST_MAX_M = 0.45  # a stem on a quad whose two triangulations differ more is refused (salvage: placer bounds)
EDGE_BAND_DM = 200
MARGIN_FACTOR = 0.15
SEA_KINDS = ("ocean", "shallow-coast", "bay", "estuary")
TREE_IN_WATER = ("cypress_swamp", "drowned_forest", "mangrove_fringe")
TREES = ("canopy_tree", "palm")
NO_FLOW = ("canopy_tree", "palm", "understorey", "log", "mushroom")
ROCKS = ("boulder", "cliff", "seabed_rock")
SMALL = ("herb", "fern", "reed", "mushroom", "log", "boulder", "understorey")
MARGIN_CLASSES = ("canopy_tree", "palm", "boulder", "cliff")
SLOPE_MAX = {"canopy_tree": 35, "palm": 35, "understorey": 40, "herb": 45, "fern": 45, "reed": 40, "mushroom": 45,
             "log": 40, "vine_moss": 40, "water_plant": 90, "seabed_plant": 90, "seabed_rock": 90, "boulder": 90,
             "cliff": 90}
SLOPE_MIN = {"cliff": 28}
ROAD_CLEAR = {"canopy_tree": 2.5, "palm": 2.5, "boulder": 1.0, "cliff": 1.0, "seabed_rock": 1.0}  # else 0.5
ORDER = ("cliff", "boulder", "canopy_tree", "palm", "understorey", "log", "mushroom", "herb", "fern", "reed",
         "water_plant", "seabed_rock", "seabed_plant")
SPREAD_M = {"canopy_tree": 5.0, "palm": 4.0, "cliff": 8.0, "boulder": 3.0, "seabed_rock": 3.0}  # else 1.5
SKIP_FAMILIES = ("hanging_moss",)  # hangs from a tree: never stands (salvage, tree seating)
# road dressing: (kind, per km, offset lo, hi from the surface edge in m, db ids or plugin keys)
DRESS = (
    ("rock_pile", 40.0, 1.0, 4.0, ("kotm-argoniarockpiles01mud", "kotm-argoniarockpiles02mud", "kotm-argoniarockpiles03mud",
                                   "kotm-argoniarockpiles04rainforest", "kotm-argoniarockpilem01mud", "kotm-argoniarockpilem02mud",
                                   "kotm-argoniarockpilem03marshgrass")),
    ("boulder", 30.0, 2.5, 7.0, ("kotm-argoniarockm01", "kotm-argoniarockm02", "kotm-argoniarockm04", "kotm-argoniarocks02",
                                 "kotm-argoniarocks03", "kotm-argoniarockl02", "kotm-argoniarockl03")),
    ("cairn", 3.0, 1.5, 4.0, ("kotm-rockcairn01ls", "kotm-rockcairn02ls", "kotm-rockcairn03ls", "kotm-rockcairn04ls")),
)
SIGNPOST = "23298A:Black Marsh.esm"  # 01housedressignpost: BM&V's own roadside signpost (aldredanyia\signpost.nif)
FENCES = ("0157FF:King of the Murkmire.esp", "0157FB:King of the Murkmire.esp", "1AD5F2:King of the Murkmire.esp",
          "1AD5F1:King of the Murkmire.esp")
FARM_KINDS = ("farm", "estate", "homestead")
FARM_RADIUS_M = 150.0
ROAD_NEAR_DM = 730  # the landcover holds the distance to a road up to 73 m (past the widest collision placed): a reference further out is not tested against one
ROAD_BODY_CLEAR = 48.0  # units from a blocked column's centre to the road's walking width: the actor's radius the
# navmesh is made for (tools.navmesh.params.AGENT_RADIUS, 32) and one voxel of its grid (CELL_SIZE, 16)


def ident(base_key: str, x: float, y: float, cell) -> str:
    """The identity of the reference the rules put at (x, y) of `cell` with this base (the base's `XXXXXX:<plugin>`)."""
    h = hashlib.sha1(f"{base_key.lower()}|{x:.1f}|{y:.1f}".encode()).hexdigest()[:10]
    return f"flora/{int(cell[0])},{int(cell[1])}/{h}"


def form_ids(idents) -> dict[str, int]:
    """identity -> form id in FID_FIRST..FID_LAST outside FID_HOLE (the navmesh's ids, idspace.py). Each identity
    asks for the slot its digest names and, when that is taken, the next free one after it; they are served in sorted
    order, so the answer follows from the set alone. An identity whose slot lies in the hole is served after the
    rest, at the first slot outside the hole that its digest salted 1, 2, ... names, so it moves no other's.
    Two references with one identity stop the build."""
    n = FID_LAST - FID_FIRST + 1
    h0, h1 = FID_HOLE[0] - FID_FIRST, FID_HOLE[1] - FID_FIRST
    names = sorted(idents)
    if len(set(names)) != len(names):
        seen: set = set()
        twice = [i for i in names if i in seen or seen.add(i)]
        raise ValueError(f"placed references share an identity: {twice[:3]}")
    if len(names) > n // 2:
        raise ValueError(f"{len(names)} placed references are too many for the form ids {FID_FIRST:06X}..{FID_LAST:06X}")

    def slot(text: str) -> int:
        return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big") % n

    taken, out, held = set(), {}, []

    def give(i: str, s: int) -> None:
        while s in taken or h0 <= s <= h1:
            s = (s + 1) % n
        taken.add(s)
        out[i] = FID_FIRST + s

    for i in names:
        s = slot(i)
        if h0 <= s <= h1:
            held.append(i)
        else:
            give(i, s)
    for i in held:
        k, s = 1, slot(f"{i}|1")
        while h0 <= s <= h1:
            k += 1
            s = slot(f"{i}|{k}")
        give(i, s)
    return out


def shard_line(r: dict, rec: dict) -> str:
    """One reference as its shard line (`r`: cell, base key, pos, rot, scale, cls, db, id, fid; `rec`: its base's
    plugin, edid and model)."""
    (x, y, z), (rx, ry, rz) = r["pos"], r["rot"]
    o = {"base": f"{rec['plugin']}:{rec['edid']}", "x": x, "y": y, "z": z, "rx": rx, "ry": ry, "rz": rz,
         "scale": r["scale"], "cell": r["cell"], "cls": r["cls"], "db": r["db"], "key": r["base"],
         "pos": r["pos"], "rot": r["rot"], "model": rec["model"], "id": r["id"], "fid": r["fid"]}
    if r.get("seated"):  # lowered by its mesh off a float (step 7): its sink is no longer its base's window
        o["seated"] = True
    return json.dumps(o, separators=(",", ":"))


def base_row(key: str, rec: dict, audit: dict, db_id, cls) -> dict:
    """A base's row of bases.json (`rec`: read_bases' record; `audit`: its model's texture audit; `cls`: its flora
    class, None for a base the flora tables do not hold)."""
    return {"key": key, "ref": f"{rec['plugin']}:{rec['edid']}", "copied": key.split(":", 1)[1] not in MASTERS,
            **{kk: rec[kk] for kk in ("sig", "model", "obnd", "edid", "plugin")}, "db_id": db_id, "cls": cls,
            **({"alt_textures": audit["repairs"]} if audit["repairs"] else {}),
            "missing_non_diffuse": len(audit["missing_other"])}


def jsonl(name):
    return [json.loads(ln) for ln in (DB / f"{name}.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()]


def log(*a):
    print("place:", *a, flush=True)


def plugin_path(name: str) -> Path:
    p = DATA / name
    if p.exists():
        return p
    for d in sorted(MO2.iterdir()):
        q = d / name
        if q.exists():
            return q
    raise FileNotFoundError(name)


def canon(key: str) -> str:
    """'0d864c:black marsh.esm' -> '0D864C:Black Marsh.esm' (the plugin's file name as on disk)."""
    fid, plugin = key.split(":", 1)
    return f"{fid.upper()}:{plugin_path_name(plugin)}"


_NAMES: dict[str, str] = {}


def plugin_path_name(plugin: str) -> str:
    low = plugin.lower()
    if low not in _NAMES:
        for d in [DATA, *sorted(MO2.iterdir())]:
            for p in d.glob("*.es[mpl]"):
                _NAMES.setdefault(p.name.lower(), p.name)
    return _NAMES.get(low, plugin)


def read_bases(keys: set[str]) -> dict[str, dict]:
    """key -> {sig, model, obnd, edid} from each base's own plugin."""
    from tools.navmesh import esm
    want = {b"STAT", b"TREE", b"FLOR", b"MSTT"}
    by_plugin: dict[str, set[int]] = defaultdict(set)
    for k in keys:
        fid, plugin = k.split(":", 1)
        by_plugin[plugin].add(int(fid, 16))
    out = {}
    for plugin, ids in sorted(by_plugin.items()):
        path = plugin_path(plugin)
        own = len(esm.masters(path))
        for r in esm.records(path, want, groups=want):
            if r.fid >> 24 != own or (r.fid & 0xFFFFFF) not in ids:
                continue
            d = {"sig": r.sig.decode(), "model": "", "obnd": None, "edid": "", "plugin": plugin, "path": str(path)}
            for s, p in esm.subrecords(r.data):
                if s == b"MODL":
                    d["model"] = p.rstrip(b"\0").decode("cp1252")
                elif s == b"EDID":
                    d["edid"] = p.rstrip(b"\0").decode("cp1252")
                elif s == b"OBND" and len(p) == 12:
                    import struct
                    d["obnd"] = list(struct.unpack("<6h", p))
            out[f"{r.fid & 0xFFFFFF:06X}:{plugin}"] = d
    return out


def first_edids(plugin: str) -> dict[str, int]:
    """editor id (lower) -> the form id of its first record in the plugin: the record ForeignCopy.Find resolves."""
    from tools.navmesh import esm
    out: dict[str, int] = {}
    for r in esm.records(plugin_path(plugin), None):
        for s_, p in esm.subrecords(r.data):
            if s_ == b"EDID":
                out.setdefault(p.rstrip(b"\0").decode("cp1252").lower(), r.fid & 0xFFFFFF)
                break
    return out


def open_sides() -> dict[str, float | None]:
    """mesh file name (lower) -> open-side azimuth in degrees (mesh frame, CCW from +X), or None when the shell has
    no open back (every horizontal ray direction sees under 0.3 back faces)."""
    cat = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    out: dict[str, float | None] = {}
    extra = OUT / "research/hollow_extra.json"  # place/hollow.py: shells the study could not reach
    measured = dict(cat["hollow_backs_vanilla_meshes"])
    if extra.exists():
        measured.update({k: v for k, v in json.loads(extra.read_text()).items() if "back_by_az" in v})
    for path, h in measured.items():
        b = h.get("back_by_az") or []
        name = path.replace("\\", "/").rsplit("/", 1)[-1].lower()
        if b and max(b) < 0.3:
            out[name] = None
        elif b:
            out[name] = (int(np.argmax(b)) * 45 + 180) % 360  # rays travelling at az see back faces: open at az+180
    for name, o in cat["cliff_open_back_orientation"].items():
        out[name.lower()] = float(o["open_az_deg"])
    return out


class World:
    """The landcover and heightmap arrays (memory-mapped) and the grid."""

    def __init__(self):
        self.legend = json.loads((LC / "legend.json").read_text(encoding="utf-8"))
        man = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.grid = man["grid"]
        self.build_id = self.legend["build_id"]
        if man["build_id"] != self.build_id:
            raise SystemExit(f"land manifest {man['build_id']} and landcover {self.build_id} differ: rebuild one")
        self.ox, self.oy = self.legend["origin_world"]
        self.h = np.load(OUT / "terrain/heightmap.npy", mmap_mode="r")
        for n in ("habitat", "region", "kind", "shore", "run", "road", "roadcls", "canopy", "slope", "flags"):
            setattr(self, n, np.load(LC / f"{n}.npy", mmap_mode="r"))
        self.H, self.W = self.h.shape

    def rc(self, x, y):
        return (self.oy - y) / SAMPLE, (x - self.ox) / SAMPLE

    def ground(self, x, y):
        """Bilinear ground (units) and the larger half-difference of the quad's two triangulations."""
        r, c = self.rc(np.asarray(x, float), np.asarray(y, float))
        r0 = np.clip(np.floor(r).astype(int), 0, self.H - 2)
        c0 = np.clip(np.floor(c).astype(int), 0, self.W - 2)
        fr, fc = r - r0, c - c0
        a, b = self.h[r0, c0], self.h[r0, c0 + 1]
        d, e = self.h[r0 + 1, c0], self.h[r0 + 1, c0 + 1]
        bil = a * (1 - fr) * (1 - fc) + b * (1 - fr) * fc + d * fr * (1 - fc) + e * fr * fc
        return bil

    def tri_grounds(self, x, y):
        """The ground under both triangulations of the quad (the engine uses one of them)."""
        r, c = self.rc(np.asarray(x, float), np.asarray(y, float))
        r0 = np.clip(np.floor(r).astype(int), 0, self.H - 2)
        c0 = np.clip(np.floor(c).astype(int), 0, self.W - 2)
        u, v = c - c0, r - r0  # u east, v south
        a, b = self.h[r0, c0], self.h[r0, c0 + 1]
        d, e = self.h[r0 + 1, c0], self.h[r0 + 1, c0 + 1]
        t1 = np.where(u >= v, a + (b - a) * u + (e - b) * v, a + (d - a) * v + (e - d) * u)  # diagonal a-e
        t2 = np.where(u + v <= 1, a + (b - a) * u + (d - a) * v, e + (d - e) * (1 - u) + (b - e) * (1 - v))  # b-d
        return t1, t2

    def gradient(self, x, y):
        """dh/dx, dh/dy (y north) at the nearest sample."""
        r, c = self.rc(np.asarray(x, float), np.asarray(y, float))
        r = np.clip(np.rint(r).astype(int), 1, self.H - 2)
        c = np.clip(np.rint(c).astype(int), 1, self.W - 2)
        gx = (self.h[r, c + 1] - self.h[r, c - 1]) / (2 * SAMPLE)
        gy = -(self.h[r + 1, c] - self.h[r - 1, c]) / (2 * SAMPLE)
        return gx, gy

    def at(self, name, x, y):
        r, c = self.rc(np.asarray(x, float), np.asarray(y, float))
        r = np.clip(np.floor(r).astype(int), 0, self.H - 1)
        c = np.clip(np.floor(c).astype(int), 0, self.W - 1)
        return getattr(self, name)[r, c]


class Roads:
    """Road spines densified to 1 m (bridges over water left out, as the landcover does) and their surface edge."""

    def __init__(self):
        cls = {r["id"]: r for r in jsonl("road_class")}
        roads = {r["id"]: r for r in jsonl("road")}
        verts = defaultdict(list)
        for v in jsonl("road_vertex"):
            verts[v["road_id"]].append(v)
        pts, edge, segs = [], [], []
        for rid, vs in verts.items():
            vs.sort(key=lambda v: v["seq"])
            c = cls[roads[rid]["road_class_id"]]
            for a, b in zip(vs, vs[1:]):
                if a["on_water"] or b["on_water"]:
                    continue
                p0 = np.array([a["world_x"], a["world_y"]]); p1 = np.array([b["world_x"], b["world_y"]])
                n = max(1, int(np.linalg.norm(p1 - p0) / UPM))
                t = np.linspace(0, 1, n + 1)[:, None]
                pts.append(p0 + (p1 - p0) * t)
                edge.append(np.full(n + 1, c["paint_full_m"]))
                segs.append((p0, p1, c["paint_full_m"], rid))
        self.pts = np.concatenate(pts)
        self.edge = np.concatenate(edge)
        self.segs = segs
        self.tree = cKDTree(self.pts)

    def clear(self, x, y):
        """Metres from the nearest road surface edge (negative on the surface)."""
        d, i = self.tree.query(np.column_stack([x, y]), distance_upper_bound=60 * UPM)
        out = np.full(len(x), 1e9)
        ok = np.isfinite(d)
        out[ok] = d[ok] / UPM - self.edge[i[ok]]
        return out


class Palette:
    """The db's flora rules, indexed for the placer."""

    def __init__(self, world: World):
        self.cls = {r["id"]: r for r in jsonl("flora_class")}
        self.fam = {r["id"]: r for r in jsonl("flora_family")}
        self.base = {r["id"]: r for r in jsonl("flora_base")}
        self.hab = {r["id"]: r for r in jsonl("habitat")}
        self.kinds = world.legend["kinds"]
        flows = {r["id"]: r["flows"] for r in jsonl("water_kind")}
        self.kind_flows = np.array([flows.get(k, False) for k in self.kinds] + [False] * (256 - len(self.kinds)))
        self.kind_sea = np.array([k in SEA_KINDS for k in self.kinds] + [False] * (256 - len(self.kinds)))
        guild_members = defaultdict(lambda: {"anchor": [], "partner": []})
        for m in jsonl("flora_guild_member"):
            guild_members[m["flora_guild_id"]][m["role"]].append(m["flora_family_id"])
        self.partners = defaultdict(set)
        for g in guild_members.values():
            for a in g["anchor"]:
                self.partners[a].update(g["partner"])
        sides = open_sides()
        keys = {canon(b["form_key"]) for b in self.base.values()}
        dress_keys = {SIGNPOST, *FENCES}
        self.rec = read_bases(keys | dress_keys)
        self.key_of = {bid: canon(b["form_key"]) for bid, b in self.base.items()}
        self.skipped = defaultdict(list)
        self.usable = set()
        from tools.navmesh import meshes
        meshes.PROFILE = "NewWorld"  # the new world's card: the BM&V stack plus the world-asset mods
        self.resolver = meshes.Resolver(DATA)
        firsts: dict[str, dict[str, int]] = {}
        for bid, b in self.base.items():
            k = self.key_of[bid]
            fam = self.fam[b["flora_family_id"]]
            if b["flora_family_id"] in SKIP_FAMILIES:
                self.skipped["hangs from a tree"].append(bid); continue
            rec = self.rec.get(k)
            if not rec or not rec["obnd"] or not rec["model"]:
                self.skipped["record, OBND or model not found"].append(bid); continue
            if rec["plugin"] not in firsts:
                firsts[rec["plugin"]] = first_edids(rec["plugin"])
            if not rec["edid"] or firsts[rec["plugin"]].get(rec["edid"].lower()) != int(k.split(":")[0], 16):
                self.skipped["editor id does not name this record in its plugin"].append(bid); continue
            if self.resolver.where(rec["model"]) is None:
                self.skipped["model not in the NewWorld profile"].append(bid); continue
            if self.tex_audit(rec["model"])["missing_diffuse"]:
                self.skipped["a diffuse texture inside the model not in the NewWorld profile"].append(bid); continue
            c = fam["flora_class_id"]
            name = rec["model"].replace("\\", "/").rsplit("/", 1)[-1].lower()
            b["open_az"] = sides.get(name, "unknown")
            if c == "cliff" and b["open_az"] == "unknown":
                self.skipped["cliff shell with unmeasured open side"].append(bid); continue
            self.usable.add(bid)
        regions = world.legend["regions"]; habs = world.legend["habitats"]
        self.rows = defaultdict(list)  # (region idx, habitat idx) -> [(base id, density/ha)]
        for r in jsonl("region_flora"):
            if r["flora_base_id"] in self.usable:
                self.rows[(regions.index(r["region_id"]) if r["region_id"] in regions else -1,
                           habs.index(r["habitat_id"]))].append((r["flora_base_id"], r["density_per_ha"]))
        self.dress_ok = {k for k in dress_keys if k in self.rec and self.rec[k]["model"]
                         and self.resolver.where(self.rec[k]["model"]) and not self.tex_audit(self.rec[k]["model"])["missing_diffuse"]}
        self.class_of = {bid: self.fam[b["flora_family_id"]]["flora_class_id"] for bid, b in self.base.items()}
        self.prio = {c: i for i, c in enumerate(ORDER)}

    def tex_audit(self, model: str) -> dict:
        """The model's texture sets against the NewWorld profile (texsets.py): missing diffuses (the base is refused),
        missing other slots (a warning) and the alternate-texture repairs the writer puts on our copy."""
        from tools.newworld import verify
        from tools.newworld.place import texsets
        if not hasattr(self, "_tex"):
            self._tex = {}
            self._audit = texsets.Audit(verify.assets(), mod_textures)
        if model not in self._tex:
            self._tex[model] = self._audit.model(self.resolver.read(model) or b"", model_mod(self.resolver, model))
        return self._tex[model]

    def collision(self, key: str):
        """The base's solid collision triangles in mesh units (empty when its mesh has none; None when unreadable),
        as the navmesh reads it; `reach[key]` is its farthest point from the origin."""
        if not hasattr(self, "_coll"):
            self._coll, self.reach = {}, {}
        if key not in self._coll:
            c = self.resolver.collision(self.rec[key]["model"]) if self.rec.get(key, {}).get("model") else None
            t = None if c is None or c.tris is None else c.tris
            self._coll[key] = t
            self.reach[key] = float(np.linalg.norm(t.reshape(-1, 3), axis=1).max()) if t is not None and len(t) else 0.0
        return self._coll[key]

    def sink_m(self, bid, rng):
        """Metres at scale 1 the pivot is set under the ground."""
        b = self.base[bid]; c = self.cls[self.class_of[bid]]
        if self.class_of[bid] in ROCKS:
            if (b.get("placed_refs") or 0) >= 20 and b.get("sink_m") is not None:
                return max(b["sink_m"], 0.0)
            return c.get("sink_ratio", 0.26) * b["height_m"]
        lo, hi = b.get("sink_lo_m"), b.get("sink_hi_m")
        if lo is not None and hi is not None and hi > lo:
            return rng.uniform(lo, hi)
        if b.get("sink_m") is not None:
            return b["sink_m"]
        return c.get("sink_m", 0.1)


BOTTOM_SHRINK = 0.7  # a rock's base outline against its OBND (meshes taper below their widest)
OVERTOP_MIN_M, OVERTOP_SHARE = 3.0, 0.15  # a cliff's top may stand this far above its footprint's highest ground
EXTRA_SINK_MAX = 0.35  # extra burial allowed beyond the rule, x the mesh height; past it the spot is refused


def underside_gap(W, x, y, z, ob, sc, rot) -> float:
    """Units by which the mesh's bottom (the OBND floor, 0.7 of its x/y extent, on a 5 x 5 grid, turned by the ref's
    rotation) stands above the ground anywhere: > 0 means part of an open underside shows."""
    from tools.navmesh.placed import rotation
    m = rotation(*rot) * sc
    u = np.linspace(-1, 1, 5)
    gx_, gy_ = np.meshgrid(u, u)
    px = np.where(gx_ < 0, -gx_ * ob[0], gx_ * ob[3]) * BOTTOM_SHRINK
    py = np.where(gy_ < 0, -gy_ * ob[1], gy_ * ob[4]) * BOTTOM_SHRINK
    pts = np.column_stack([px.ravel(), py.ravel(), np.full(25, float(ob[2]))]) @ m.T + np.array([x, y, z])
    t1, t2 = W.tri_grounds(pts[:, 0], pts[:, 1])
    return float(np.max(pts[:, 2] - np.minimum(t1, t2)))


def overtop(W, x, y, z, ob, sc) -> float:
    """Units by which a shell's top stands above the highest ground of its footprint (a cliff piece taller than the
    hill it is set in reads as a wall on the plain)."""
    r, c = W.rc(x, y)
    rr = max(abs(ob[0]), abs(ob[1]), ob[3], ob[4]) * sc / SAMPLE
    win = W.h[int(max(0, r - rr)):int(r + rr) + 2, int(max(0, c - rr)):int(c + rr) + 2]
    return float(z + ob[5] * sc - np.max(win))


def tilt_rot(theta_deg, gx, gy):
    """rx, ry (radians) that tip the mesh's up axis theta degrees down the slope (gx, gy: dh/dx, dh/dy).
    Skyrim's matrix Rx(-rx) Ry(-ry) Rz(-rz) takes up (0,0,1) to (-sin ry, sin rx cos ry, cos rx cos ry)."""
    g = math.hypot(gx, gy)
    if g < 1e-9 or theta_deg <= 0:
        return 0.0, 0.0
    t = math.radians(theta_deg)
    tx, ty, tz = -gx / g * math.sin(t), -gy / g * math.sin(t), math.cos(t)
    ry = -math.asin(tx)
    rx = math.atan2(ty, tz)
    return rx, ry


def road_shortfall(W: World, P: Palette, R: Roads, r: dict) -> float:
    """Units by which a reference's collision at walking height (pos, rot, scale, base key) is inside the clear line
    of the road's walking width; 0 when it keeps clear (step 6 of the recipe)."""
    from tools.navmesh import placed
    from tools.navmesh.inputs import ROAD_HALF_UNITS
    local = P.collision(r["base"])
    if local is None or not len(local):
        return 0.0
    d, i = R.tree.query(np.array(r["pos"][:2], float))
    if d - P.reach[r["base"]] * float(r["scale"]) > max(R.edge[i] * UPM, ROAD_HALF_UNITS) + ROAD_BODY_CLEAR + 2 * UPM:
        return 0.0
    w = placed.world_tris(local, r)
    ra = max(int((W.oy - w[:, :, 1].max()) // SAMPLE) - 1, 0)
    ca = max(int((w[:, :, 0].min() - W.ox) // SAMPLE) - 1, 0)
    rb = min(int((W.oy - w[:, :, 1].min()) // SAMPLE) + 3, W.H)
    cb = min(int((w[:, :, 0].max() - W.ox) // SAMPLE) + 3, W.W)
    runs, _ = placed.blocked_columns(w, np.ascontiguousarray(W.h[ra:rb, ca:cb], np.float32), (W.ox + ca * SAMPLE, W.oy - ra * SAMPLE, SAMPLE))
    if not len(runs):
        return 0.0
    cs = placed.params.CELL_SIZE
    jj = np.repeat(runs[:, 0], runs[:, 2] - runs[:, 1] + 1)  # the centres of each run's columns, a point a column
    ii = np.concatenate([np.arange(a, b + 1) for a, b in runs[:, 1:]])
    dd, k = R.tree.query(np.column_stack([(ii + 0.5) * cs, (jj + 0.5) * cs]))
    return max(float((np.maximum(R.edge[k] * UPM, ROAD_HALF_UNITS) + ROAD_BODY_CLEAR - dd).max()), 0.0)


_W: World | None = None
_P: Palette | None = None
_R: Roads | None = None
_DRESS: dict | None = None
_MARGIN: set | None = None
_PROF = None  # audit.Profiles of a worker: each base's mesh read once
_FACTOR: dict = {}  # habitat idx -> density factor (calibrate(): the habitat's mean refs/ha hits its target)


def margin_skyrim_cells(map_cells) -> set:
    """margin_cells.json is in map cells (8192 units); the cells placed here are Skyrim cells (4096): two a side."""
    return {(2 * x + a, 2 * y + b) for x, y in map_cells for a in (0, 1) for b in (0, 1)}


def _init():
    global _W, _P, _R, _MARGIN
    if _W is None:
        _W = World(); _P = Palette(_W); _R = Roads()
        _MARGIN = margin_skyrim_cells(json.loads((OUT / "margin_cells.json").read_text()))


def place_cell(cx: int, cy: int, pre: list[dict]) -> tuple[list[dict], dict]:
    """The natural refs of one cell (after the road dressing `pre` already in it)."""
    W, P, R = _W, _P, _R
    g = W.grid
    rng = np.random.default_rng([SEED, cx & 0xFFFF, cy & 0xFFFF])
    r0 = (g["cy_top"] - cy) * 32; c0 = (cx - g["cx0"]) * 32
    hab = np.asarray(W.habitat[r0:r0 + 32, c0:c0 + 32]); reg = np.asarray(W.region[r0:r0 + 32, c0:c0 + 32])
    shore = np.asarray(W.shore[r0:r0 + 32, c0:c0 + 32])
    canopy_s = np.asarray(W.canopy[r0:r0 + 32, c0:c0 + 32])
    margin = (cx, cy) in _MARGIN
    x0, y1 = W.ox + c0 * SAMPLE, W.oy - r0 * SAMPLE  # west edge, north edge of the cell
    cand = []  # (x, y, bid, habitat idx)

    def near(x, y, sd, mask):
        """A clump member round (x, y), redrawn (up to 4 times) until it lands on its stratum in this cell."""
        for _ in range(4):
            px, py = x + rng.normal(0, sd), y + rng.normal(0, sd)
            cc_, rr_ = int((px - x0) // SAMPLE), int((y1 - py) // SAMPLE)
            if 0 <= cc_ < 32 and 0 <= rr_ < 32 and mask[rr_, cc_]:
                break
        return px, py
    tally = defaultdict(int)
    for (ri, hi) in sorted(set(zip(reg.ravel().tolist(), hab.ravel().tolist()))):
        if hi == 0:
            continue
        rows = P.rows.get((ri, hi))
        if not rows:
            continue
        m = (reg == ri) & (hab == hi)
        for edge_part in (True, False):
            mm = m & ((shore >= 0) & (shore < EDGE_BAND_DM)) if edge_part else m & ~((shore >= 0) & (shore < EDGE_BAND_DM))
            idx = np.flatnonzero(mm)
            if not len(idx):
                continue
            area = len(idx) * SAMPLE_HA
            mm2 = mm.reshape(32, 32)
            cmean = max(float(canopy_s.ravel()[idx].mean()) / 255, 0.2)  # the canopy field moves trees, keeps the mean
            fams = defaultdict(list)
            for bid, dens in rows:
                fams[P.base[bid]["flora_family_id"]].append((bid, dens))
            for bid, dens in rows:
                c = P.class_of[bid]
                f = P.fam[P.base[bid]["flora_family_id"]]
                if margin and c not in MARGIN_CLASSES:
                    continue
                k = max(1, int(f.get("cluster_size") or 1))
                lam = dens * area / k * (MARGIN_FACTOR if margin else 1.0) * _FACTOR.get(hi, 1.0)
                if edge_part and c in SMALL:
                    lam *= EDGE_BOOST
                if c in TREES:
                    lam /= cmean
                elif c == "understorey":
                    lam /= 0.5 + 0.5 * cmean
                n = rng.poisson(lam)
                if not n:
                    continue
                spread = SPREAD_M.get(c, 1.5) * UPM
                same = fams[f["id"]]
                sw = np.array([d for _, d in same]); sw = sw / sw.sum()
                for _ in range(n):
                    s = idx[rng.integers(len(idx))]
                    cxp = x0 + (s % 32 + rng.random()) * SAMPLE; cyp = y1 - (s // 32 + rng.random()) * SAMPLE
                    cand.append((cxp, cyp, bid, hi))
                    for _ in range(rng.poisson(k - 1) if k > 1 else 0):
                        b2 = same[rng.choice(len(same), p=sw)][0]
                        cand.append((*near(cxp, cyp, spread, mm2), b2, hi))
                    for pf in sorted(P.partners.get(f["id"], ())):  # in a fixed order: a set's own differs from run to run
                        if pf in fams and rng.random() < 0.5:
                            pr = fams[pf]
                            for _ in range(1 + rng.poisson(1)):
                                b2 = pr[rng.integers(len(pr))][0]
                                cand.append((*near(cxp, cyp, spread * 1.5, mm2), b2, hi))
    if not cand:
        return [], tally
    xs = np.array([c[0] for c in cand]); ys = np.array([c[1] for c in cand])
    bids = [c[2] for c in cand]; his = np.array([c[3] for c in cand])
    classes = np.array([P.class_of[b] for b in bids])
    keep = (xs >= x0 + EDGE_M * UPM) & (xs <= x0 + CELL - EDGE_M * UPM) & (ys <= y1 - EDGE_M * UPM) & (ys >= y1 - CELL + EDGE_M * UPM)
    tally["candidates"] += len(cand)
    xs = np.round(xs, 1); ys = np.round(ys, 1)  # as the shard holds them; every test below reads these
    keep &= W.at("habitat", xs, ys) == his
    flags = W.at("flags", xs, ys)
    keep &= (flags & 2) == 0
    t1, t2 = W.tri_grounds(xs, ys)
    z0 = (t1 + t2) / 2  # within the twist of the engine's ground whichever diagonal it uses
    twist = np.abs(t1 - t2) / 2 / UPM
    depth = -np.minimum(t1, t2) / UPM  # the deeper diagonal: wet under either triangulation counts as wet
    kind = W.at("kind", xs, ys)
    flows = P.kind_flows[kind]
    sea = P.kind_sea[kind]
    slope = W.at("slope", xs, ys).astype(float)
    canopy = W.at("canopy", xs, ys).astype(float) / 255
    run = W.at("run", xs, ys)
    road = W.at("road", xs, ys)
    u = rng.random(len(cand))
    near = road < ROAD_NEAR_DM  # the landcover's distance to a road, decimetres
    clear = np.full(len(cand), 1e9)
    if near.any():
        clear[near] = R.clear(xs[near], ys[near])
    for i, (b, c) in enumerate(zip(bids, classes)):
        if not keep[i]:
            continue
        f = P.fam[P.base[b]["flora_family_id"]]
        why = None
        if clear[i] < ROAD_CLEAR.get(c, 0.5):
            why = "road"
        elif f.get("seabed_min_m") is not None:
            if not (f["seabed_min_m"] <= depth[i] <= f["seabed_max_m"]):
                why = "seabed depth"
        elif depth[i] > 0.05:
            wmax = f.get("standing_water_max_m") or 0.0
            if flows[i] and c in NO_FLOW:
                why = "flowing water"
            elif depth[i] > (wmax if not f.get("water_only") else wmax or 2.0):
                why = "water depth"
            elif c in TREES and P.hab[W.legend["habitats"][his[i]]]["id"] not in TREE_IN_WATER:
                why = "tree in water outside its habitat"
            elif c in TREES and sea[i] and f["id"] != "mangrove":
                why = "tree in sea water"
            elif f.get("water_only") and depth[i] < 0.2:
                why = "too shallow"
        elif f.get("water_only"):
            why = "dry"
        if why is None and c in TREES and depth[i] <= 0.05 and run[i] < 20:
            why = "running-water bank"
        if why is None and c not in ROCKS and twist[i] > TWIST_MAX_M:
            why = "quad twist"
        if why is None and not (SLOPE_MIN.get(c, 0) <= slope[i] <= SLOPE_MAX.get(c, 45)):
            why = "slope"
        if why is None and c in TREES and u[i] > canopy[i]:
            why = "canopy"
        elif why is None and c in ("understorey",) and u[i] > 0.5 + 0.5 * canopy[i]:
            why = "canopy"
        if why:
            keep[i] = False
            tally[f"refused: {why}"] += 1
    order = sorted(np.flatnonzero(keep), key=lambda i: (P.prio[classes[i]], u[i]))
    placed = []
    occ = [(p["pos"][0], p["pos"][1], p["_r"], p["cls"]) for p in pre]
    grid = defaultdict(list)
    for o in occ:
        grid[(int(o[0] // 700), int(o[1] // 700))].append(o)
    natural = 0
    for i in order:
        if natural >= CAP:
            tally["refused: budget"] += 1
            continue
        b = bids[i]; c = classes[i]; rec = P.rec[P.key_of[b]]
        ob = rec["obnd"]
        sc = (P.base[b].get("scale_med") or 1.0) * rng.uniform(0.85, 1.15)
        rad = max(abs(ob[0]), abs(ob[1]), abs(ob[3]), abs(ob[4])) * sc
        x, y = round(float(xs[i]), 1), round(float(ys[i]), 1)  # as the shard holds it
        bad = False
        gk = (int(x // 700), int(y // 700))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for (ox_, oy_, orad, oc) in grid.get((gk[0] + dx, gk[1] + dy), ()):
                    d = math.hypot(x - ox_, y - oy_)
                    need = MIN_SPACING_M * UPM + 0.5  # the shard rounds positions to 0.1 unit
                    if c in TREES and oc in TREES:
                        need = TRUNK_SPACING_M * UPM
                    if oc == "cliff" and c == "cliff":
                        need = 0.6 * max(rad, orad)
                    elif oc in ("cliff", "boulder") and c not in ("cliff", "boulder"):
                        need = max(need, 0.8 * orad)
                    if d < need:
                        bad = True; break
                if bad: break
            if bad: break
        if bad:
            tally["refused: spacing"] += 1
            continue
        gx, gy = W.gradient(x, y)
        gx, gy = float(gx), float(gy)
        slope_deg = math.degrees(math.atan(math.hypot(gx, gy)))
        cl = P.cls[c]
        theta = min(cl["tilt_factor"] * slope_deg, cl["tilt_max_deg"])
        if c == "boulder" and rng.random() < 0.25:
            theta = 0.0
        rx, ry = tilt_rot(theta, gx, gy)
        oa = P.base[b].get("open_az")
        if c in ("cliff", "boulder", "seabed_rock") and isinstance(oa, (int, float)):
            uphill = math.degrees(math.atan2(gy, gx))
            rz = math.radians((oa - uphill + rng.uniform(-30, 30)) % 360)
        else:
            rz = rng.uniform(0, 2 * math.pi)
        g0 = float(z0[i])
        sink = P.sink_m(b, rng)
        z = g0 - sink * UPM * sc
        if c in ROCKS:
            gap = underside_gap(W, x, y, z, ob, sc, (rx, ry, rz)) + 0.05 * UPM
            if gap > 0:
                if gap > EXTRA_SINK_MAX * (ob[5] - ob[2]) * sc:
                    tally["refused: underside would show"] += 1
                    continue
                z -= gap
                tally["rocks sunk further to bury the underside"] += 1
            if c == "cliff" and overtop(W, x, y, z, ob, sc) > max(OVERTOP_MIN_M * UPM, OVERTOP_SHARE * (ob[5] - ob[2]) * sc):
                tally["refused: cliff taller than its hill"] += 1
                continue
        p = {"cell": [cx, cy], "base": P.key_of[b], "pos": [round(float(x), 1), round(float(y), 1), round(float(z), 1)],
             "rot": [round(rx, 5), round(ry, 5), round(rz, 5)], "scale": round(float(sc), 4), "cls": c, "db": b,
             "_r": rad, "_h": int(his[i])}
        if near[i] and road_shortfall(W, P, R, p) > 0:
            tally["refused: collision on the road"] += 1
            continue
        placed.append(p)
        grid[gk].append((x, y, rad, c))
        natural += 1
        tally[f"placed {c}"] += 1
    return placed, tally


def dressing(W: World, P: Palette, R: Roads) -> list[dict]:
    """Road dressing along every dry road run (deterministic by seed and road)."""
    out = []
    places = [p for p in jsonl("place") if p.get("place_kind_id") in FARM_KINDS]
    farms = cKDTree(np.array([[p["world_x"], p["world_y"]] for p in places])) if places else None
    by_id = {}
    for kind, per_km, lo, hi, ids in DRESS:
        by_id[kind] = [i for i in ids if i in P.usable]
    # junction nodes: endpoints shared by 3 or more roads
    deg = defaultdict(int)
    for r in jsonl("road"):
        deg[r["from_node_id"]] += 1; deg[r["to_node_id"]] += 1
    nodes = {n["id"]: n for n in jsonl("road_node")}
    for si, (p0, p1, edge, rid) in enumerate(R.segs):
        rng = np.random.default_rng([SEED, 7, int(rid) if str(rid).isdigit() else 0, si])
        L = float(np.linalg.norm(p1 - p0)) / UPM
        if L <= 0:
            continue
        t = (p1 - p0) / (L * UPM); nrm = np.array([-t[1], t[0]])
        yaw_road = math.atan2(t[1], t[0])
        for kind, per_km, lo, hi, _ in DRESS:
            ids = by_id[kind]
            for _ in range(rng.poisson(per_km * L / 1000.0)):
                s = rng.uniform(0, L); side = rng.choice((-1, 1)); off = edge + rng.uniform(lo, hi)
                q = p0 + t * s * UPM + nrm * side * off * UPM
                out.append(("dress", kind, ids[rng.integers(len(ids))], q, None))
        if farms is not None:
            mid = (p0 + p1) / 2
            if farms.query(mid)[0] < FARM_RADIUS_M * UPM:
                fk = FENCES[(si + int(rid) if str(rid).isdigit() else si) % len(FENCES)]
                ob = P.rec[fk]["obnd"]; flen = (ob[3] - ob[0]) / UPM
                side = 1 if si % 2 else -1
                for s in np.arange(flen / 2, L - flen / 2, flen * 0.98):
                    q = p0 + t * s * UPM + nrm * side * (edge + 2.0) * UPM
                    out.append(("fence", "fence", fk, q, yaw_road))
    for nid, n in nodes.items():
        if deg[nid] >= 3 and n.get("kind") != "place":
            rng = np.random.default_rng([SEED, 9, int(nid) if str(nid).isdigit() else 0])
            q = np.array([n["world_x"], n["world_y"]], float)
            d, i = R.tree.query(q)
            a = rng.uniform(0, 2 * math.pi)
            q = R.pts[i] + np.array([math.cos(a), math.sin(a)]) * (R.edge[i] + 0.8) * UPM
            out.append(("sign", "signpost", SIGNPOST, q, a + math.pi))
    out = [o for o in out if o[0] == "dress" or o[2] in P.dress_ok]
    refs = []
    xs = np.array([o[3][0] for o in out]); ys = np.array([o[3][1] for o in out])
    z0 = W.ground(xs, ys); flags = W.at("flags", xs, ys); slope = W.at("slope", xs, ys)
    clear = R.clear(xs, ys)
    def seat(q, kind_, base_, sc_, sink_, rz_):
        """The spot's ground and the reference seated on it (tilted with the slope when it is a rock), or None when
        the spot is wet, on a place's pad, steep or on the road's surface."""
        g = float(W.ground(q[0], q[1]))
        if g <= 0.05 * UPM or int(W.at("flags", q[0], q[1])) & 2 or float(W.at("slope", q[0], q[1])) > 35 \
                or R.clear(np.array([q[0]]), np.array([q[1]]))[0] < 0.5:
            return None
        rx_ = ry_ = 0.0
        if kind_ == "dress":
            gx, gy = W.gradient(q[0], q[1]); gx, gy = float(gx), float(gy)
            rx_, ry_ = tilt_rot(min(0.85 * math.degrees(math.atan(math.hypot(gx, gy))), 30), gx, gy)
        return g, {"base": base_, "pos": [float(q[0]), float(q[1]), g - sink_ * UPM * sc_], "rot": [rx_, ry_, rz_], "scale": sc_}

    for i, (src, kind, base, q, yaw) in enumerate(out):
        if z0[i] <= 0.05 * UPM or flags[i] & 2 or slope[i] > 35 or clear[i] < 0.5:
            continue
        key = P.key_of[base] if src == "dress" else base
        rec = P.rec[key]
        rng = np.random.default_rng([SEED, 11, i])
        sc, sink = 1.0, 0.0
        if src == "dress":
            sc = (P.base[base].get("scale_med") or 1.0) * rng.uniform(0.85, 1.15)
            sink = P.sink_m(base, rng)
            rz = rng.uniform(0, 2 * math.pi)
        else:
            rz = (math.pi / 2 - yaw) % (2 * math.pi)  # clockwise yaw that turns the mesh +X along the road
        got = seat(q, src, key, sc, sink, rz)
        for _ in range(5):  # step 6: its collision's near side keeps the walking width clear, or it moves straight out
            short = road_shortfall(W, P, R, got[1]) if got else 0.0
            if not short:
                break
            d, k = R.tree.query(q)
            q = q + (q - R.pts[k]) / max(d, 1e-6) * (short + 8.0)
            got = seat(q, src, key, sc, sink, rz)
        else:
            got = None
        if got is None:
            continue
        g0, trial = got
        rx, ry = trial["rot"][0], trial["rot"][1]
        if src == "dress":
            z = trial["pos"][2]
            ob = rec["obnd"]
            gap = underside_gap(W, q[0], q[1], z, ob, sc, (rx, ry, rz)) + 0.05 * UPM
            if gap > EXTRA_SINK_MAX * (ob[5] - ob[2]) * sc:
                continue
            z -= max(gap, 0.0)
            db = base
        else:
            z = g0; db = kind
        cx = int(math.floor(q[0] / CELL)); cy = int(math.floor(q[1] / CELL))
        refs.append({"cell": [cx, cy], "base": key, "pos": [round(float(q[0]), 1), round(float(q[1]), 1), round(z, 1)],
                     "rot": [round(rx, 5), round(ry, 5), round(rz, 5)], "scale": round(float(sc), 4),
                     "cls": f"road_{kind}", "db": db,
                     "_r": max(abs(rec["obnd"][0]), abs(rec["obnd"][1])) * sc})
    # 1 m between dressing refs: first come first kept, in a fixed order
    tree = cKDTree(np.array([r["pos"][:2] for r in refs]))
    drop = set()
    for i, j in sorted(tree.query_pairs(MIN_SPACING_M * UPM)):
        if i not in drop:
            drop.add(j)
    def inside(r):  # off the cell edge by EDGE_M, as the natural refs: 1 m holds across cells
        fx = r["pos"][0] / CELL - math.floor(r["pos"][0] / CELL); fy = r["pos"][1] / CELL - math.floor(r["pos"][1] / CELL)
        e = EDGE_M * UPM / CELL
        return e <= fx <= 1 - e and e <= fy <= 1 - e
    return [r for k, r in enumerate(refs) if k not in drop and inside(r)]


def _row(args):
    global _FACTOR
    cy, cxs, pre_by_cell, factor = args
    _FACTOR = factor
    _init()
    out, tally = [], defaultdict(int)
    for cx in cxs:
        pre = pre_by_cell.get((cx, cy), [])
        refs, t = place_cell(cx, cy, pre)
        out.append((cx, pre + refs))
        for k, v in t.items():
            tally[k] += v
    return cy, out, dict(tally)


def model_mod(resolver, model: str) -> str | None:
    """The MO2 mod that lays the model (loose or in one of its archives), None for the game's own archives."""
    w = resolver.where(model)
    if w is None:
        return None
    if w.startswith("loose:"):
        return w[6:]
    for m in resolver.mods:
        if (m / w).is_file():
            return m.name
    return None


@functools.lru_cache(maxsize=None)
def mod_textures(mod: str) -> frozenset[str]:
    """Every texture path the mod lays, loose or archived (lower case, backslashes, data-relative)."""
    from tools.navmesh import bsa
    root = MO2 / mod
    out = set()
    for d in (p for p in root.iterdir() if p.is_dir() and p.name.lower() == "textures") if root.is_dir() else ():
        out |= {str(f.relative_to(root)).lower().replace("/", "\\") for f in d.rglob("*") if f.is_file()}
    for p in sorted(root.glob("*.bsa")):
        try:
            out |= {f.replace("/", "\\") for f in bsa.Archive(bsa.local(p)).files if f.startswith("textures/")}
        except (ValueError, OSError):
            continue
    return frozenset(out)


def dropped_by_region(P: Palette) -> dict:
    """Per region: distinct db bases in its region_flora rows, how many were kept, and the dropped ones by reason."""
    rows = defaultdict(set)
    for r in jsonl("region_flora"):
        rows[r["region_id"]].add(r["flora_base_id"])
    why = {b: w for w, bs in P.skipped.items() for b in bs}
    out = {}
    for g, b in sorted(rows.items()):
        d = defaultdict(list)
        for x in sorted(b - P.usable):
            d[why.get(x, "unknown")].append(x)
        out[g] = {"bases": len(b), "kept": len(b & P.usable), "dropped": dict(d)}
    return out


CAL_ROWS = 4  # calibration pilots run every 4th row
CAL_PASSES = 3
CAL_CLAMP = (0.2, 12.0)


def density(W: World, P: Palette, results: dict, rows: list[int]) -> dict:
    """Per habitat (idx): natural refs placed and the hectares it covers in those rows where its region has flora rows
    for it (a stratum without rows can hold nothing: "bare_ha" is that share, a gap in region_flora), margin cells left
    out (they carry 0.15 x on purpose)."""
    g = W.grid
    hab = np.asarray(W.habitat); reg = np.asarray(W.region)
    area = defaultdict(float); bare = defaultdict(float); cells = defaultdict(int); n = defaultdict(int)
    for cy in rows:
        r0 = (g["cy_top"] - cy) * 32
        band = hab[r0:r0 + 32]; rband = reg[r0:r0 + 32]
        for cx, refs in results[cy]:
            if (cx, cy) in _MARGIN:
                continue
            c0 = (cx - g["cx0"]) * 32
            pair = band[:, c0:c0 + 32].astype(np.int64) * 65536 + (rband[:, c0:c0 + 32].astype(np.int64) & 0xFFFF)
            v, cnt = np.unique(pair, return_counts=True)
            seen = set()
            for pv, k in zip(v.tolist(), cnt.tolist()):
                hi, ri = pv >> 16, pv & 0xFFFF
                ri = ri - 65536 if ri >= 32768 else ri
                if not hi:
                    continue
                if P.rows.get((ri, hi)):
                    area[hi] += k * SAMPLE_HA
                    if hi not in seen:
                        cells[hi] += 1; seen.add(hi)
                else:
                    bare[hi] += k * SAMPLE_HA
            for r in refs:
                if "_h" in r:
                    n[r["_h"]] += 1
    return {hi: {"refs": n[hi], "ha": area[hi], "cells": cells[hi], "bare_ha": bare[hi]} for hi in set(area) | set(bare)}


def targets(W: World, P: Palette) -> dict:
    return {i: float(P.hab[h]["density_per_ha"]) for i, h in enumerate(W.legend["habitats"])
            if h in P.hab and P.hab[h].get("density_per_ha")}


def _seat_row(args):
    """Step 7 for one row of cells: each thing seated by its kind's rule from its own mesh (audit.seat); a thing that
    cannot be seated on its ground is dropped (None in its place, so the form ids of the rest stand)."""
    from tools.newworld.place import audit
    global _PROF
    cy, out = args
    _init()
    if _PROF is None:
        _PROF = audit.Profiles()
    ground = audit.world_ground(_W)
    tally, rows = defaultdict(int), []
    for cx, refs in out:
        kept = []
        for r in refs:
            prof = _PROF(_P.rec[r["base"]]["model"])
            if prof is None:
                kept.append(r)
                continue
            m = audit.measure_of(r["cls"], prof)
            got = audit.seat(prof, r["cls"], r["pos"], r["rot"], r["scale"], ground)
            if got is None:
                tally[f"seat: refused, no pose seats its {m} on this ground"] += 1
                kept.append(None)
                continue
            z, rot = round(got[0], 1), [round(float(a), 5) for a in got[1]]
            if z != r["pos"][2] or rot != r["rot"]:
                tally[f"seat: {m} reseated"] += 1
                r["seated"] = m == "low"
            r["pos"] = [r["pos"][0], r["pos"][1], z]
            r["rot"] = rot
            kept.append(r)
        rows.append((cx, kept))
    return cy, rows, dict(tally)


def seat_all(results, workers) -> dict:
    tally = defaultdict(int)
    with Pool(workers) as pool:
        for cy, out, t in pool.imap_unordered(_seat_row, list(results.items())):
            results[cy] = out
            for a, b in t.items():
                tally[a] += b
    return tally


def place_rows(jobs, factor, workers):
    results, tally = {}, defaultdict(int)
    with Pool(workers) as pool:
        for cy, out, t in pool.imap_unordered(_row, [(*j, factor) for j in jobs]):
            results[cy] = out
            for a, b in t.items():
                tally[a] += b
    return results, tally


def calibrate(W: World, P: Palette, jobs, workers) -> dict:
    """Density factor per habitat: pilot runs on every CAL_ROWS-th row, each pass scaling the factor by target /
    achieved refs per hectare (the refusals, canopy, budget and spacing all thin what the rows ask for)."""
    tg = targets(W, P)
    factor = {hi: 1.0 for hi in tg}
    pilot = jobs[::CAL_ROWS]
    for k in range(CAL_PASSES):
        res, _ = place_rows(pilot, factor, workers)
        d = density(W, P, res, [j[0] for j in pilot])
        for hi, t in tg.items():
            got = d.get(hi, {}).get("refs", 0) / max(d.get(hi, {}).get("ha", 0), 1e-9)
            if d.get(hi, {}).get("ha", 0) > 1 and got > 0:
                factor[hi] = float(np.clip(factor[hi] * t / got, *CAL_CLAMP))
        log(f"calibration pass {k + 1}: " + ", ".join(f"{W.legend['habitats'][h]} {f:.2f}" for h, f in sorted(factor.items())))
    return factor


def key() -> str:
    h = hashlib.sha256()
    for p in [Path(__file__), Path(__file__).with_name("audit.py"), LC / "legend.json", MANIFEST, *sorted(DB.glob("flora_*.jsonl")), DB / "region_flora.jsonl",
              DB / "habitat.jsonl", DB / "road_vertex.jsonl", DB / "place.jsonl"]:
        h.update(p.read_bytes())
    h.update((LC / "key.txt").read_bytes())
    return h.hexdigest()[:16]


def run(force: bool = False, workers: int = 3) -> dict:
    t0 = time.time()
    PLACED.mkdir(parents=True, exist_ok=True)
    k = key()
    mpath = PLACED / "manifest.json"
    if not force and mpath.exists() and json.loads(mpath.read_text()).get("key") == k:
        log(f"refs current ({k})")
        return json.loads(mpath.read_text())
    _init()
    W, P, R = _W, _P, _R
    g = W.grid
    log(f"build {W.build_id}; {len(P.usable)} usable bases; skipped:", {k2: len(v) for k2, v in P.skipped.items()})
    dress = dressing(W, P, R)
    log(f"road dressing: {len(dress)} refs ({time.time() - t0:.0f} s)")
    pre = defaultdict(list)
    dress = [d for d in dress if g["cx0"] <= d["cell"][0] <= g["cx1"] and g["cy_bottom"] <= d["cell"][1] <= g["cy_top"]]
    for d in dress:
        pre[tuple(d["cell"])].append(d)
    cxs = list(range(g["cx0"], g["cx1"] + 1))
    rows = list(range(g["cy_top"], g["cy_bottom"] - 1, -1))
    jobs = [(cy, cxs, {c: v for c, v in pre.items() if c[1] == cy}) for cy in rows]
    factor = calibrate(W, P, jobs, workers)
    results, tally = place_rows(jobs, factor, workers)
    tg = targets(W, P)
    dens = {}
    for hi, d in sorted(density(W, P, results, rows).items()):
        name = W.legend["habitats"][hi]; got = d["refs"] / d["ha"] if d["ha"] else 0.0
        dens[name] = {"target_ha": tg.get(hi), "achieved_ha": round(got, 1), "cells": d["cells"], "ha": round(d["ha"], 1),
                      "bare_share": round(d["bare_ha"] / max(d["ha"] + d["bare_ha"], 1e-9), 3),
                      "factor": round(factor.get(hi, 1.0), 3),
                      "within_20pct": bool(tg.get(hi) and abs(got - tg[hi]) <= 0.2 * tg[hi])}
    used = sorted({r["base"] for out in results.values() for _, refs in out for r in refs})
    db_of = {v: kk for kk, v in P.key_of.items()}
    bases = [base_row(b, P.rec[b], P.tex_audit(P.rec[b]["model"]), db_of.get(b), P.class_of.get(db_of.get(b))) for b in used]
    mpath.unlink(missing_ok=True)  # a stopped write leaves no manifest: the shards are written again
    for old in PLACED.glob("cy*.jsonl"):
        old.unlink()
    for out in results.values():
        for _, refs in out:
            for r in refs:
                r["id"] = ident(r["base"], r["pos"][0], r["pos"][1], r["cell"])
    fids = form_ids([r["id"] for out in results.values() for _, refs in out for r in refs])
    for k2, v in seat_all(results, workers).items():  # after the form ids: a thing dropped here moves no other's id
        tally[k2] += v
    per_cell = {}
    total = 0
    h = hashlib.sha256()
    for cy in rows:
        lines = []
        for cx, refs in results[cy]:
            refs = [r for r in refs if r is not None]
            per_cell[(cx, cy)] = sum(1 for r in refs if not r["cls"].startswith("road_"))
            for r in refs:
                r.pop("_r", None); r.pop("_h", None)
                r["fid"] = f"{fids[r['id']]:06X}"
                lines.append(shard_line(r, P.rec[r["base"]]))
        total += len(lines)
        txt = "\n".join(lines) + ("\n" if lines else "")
        h.update(txt.encode())
        tmp = PLACED / f".cy{cy:+04d}.jsonl.tmp"
        tmp.write_text(txt, encoding="utf-8")
        tmp.replace(PLACED / f"cy{cy:+04d}.jsonl")
    (PLACED / "bases.json").write_text(json.dumps({"schema": 1, "key": k, "build_id": W.build_id, "bases": bases}, indent=1))
    counts = np.array(list(per_cell.values()))
    land = np.array([v for c, v in per_cell.items() if v > 0])
    man = {"key": k, "build_id": W.build_id, "refs": total, "dressing": len(dress), "bases": len(used),
           "copied_bases": sum(1 for b in bases if b["copied"]), "shard_sha256": h.hexdigest()[:16], "seconds": round(time.time() - t0, 1),

           "per_cell_natural": {"p50": float(np.percentile(counts, 50)), "p99": float(np.percentile(counts, 99)),
                                "max": int(counts.max()), "p50_nonempty": float(np.percentile(land, 50)) if len(land) else 0,
                                "vanilla": {"p95": 83, "max": 162}},
           "skipped_bases": {k2: v for k2, v in P.skipped.items()},
           "density_by_habitat": dens,
           "region_flora_dropped": dropped_by_region(P), "tally": dict(sorted(tally.items()))}
    mpath.write_text(json.dumps(man, indent=1))
    log(f"{total} refs in {len(rows)} shards, {len(used)} bases, {man['seconds']} s")
    return man
