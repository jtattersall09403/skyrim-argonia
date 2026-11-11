"""Placed-object collision for the navmesh job: references as the triangles of their meshes' own collision, in
world units.

Each reference's base is looked up in its own plugin (esm.py: MODL and OBND) unless the reference names its mesh. The
mesh is found as the game finds it (meshes.py: the laid mod stack's loose files, then BSAs) and its Havok collision
read (nif.py: compressed mesh, packed strips, convex hulls, boxes, capsules; the solid layers only). The triangles
are scaled, turned by the reference's rotation and moved to its position. A mesh with no solid collision (a fern, a
reed, a mist effect) adds nothing, as in game: that, never the producer or the kind of thing, is the rule for what
can cut the navmesh.

The new world's scatter (nw-02 step 8: trees, plants, rocks, cliffs, logs, road dressing, mist; every producer's
shards under `<plugin>/refs/<producer>/cy<+NNN>.jsonl`) is streamed one cell row at a time and only stands in the
way: ArgoniaNav fills each reference as a solid body and lays no mesh on it. What Skyrim's own navmesh does round
such things is measured by vanilla.py (docs/research/nw-02-walk5-navmesh.md): it is cut round whatever rises above
stepping height, whatever its width, and left whole over what stays below.

A built place's references (the old intermediate, out/build/argonia.json: `place:` layers and the route
infrastructure's persistent references) are one array, and carry an actor where a face is level enough. There a
reference with a `box` (a collision marker's primitive, half extents round its origin) is that box, and a base whose
mesh is not on the VM falls back to its OBND box, counted.

    write_rows(refs_dir, data, out, box, pad) -> tally              the new world's refs shards, one file a cell row
    collidable_count(refs_dir, data) -> int                         the shards' references that can cut the navmesh
    footprint(tris, ground) -> Footprint | None                     what of a collision stands in an actor's way
    from_shards(refs_dir, data) -> ((n, 3, 3), tally)               the shards as one array (a small world)
    triangles(data) -> ((n, 3, 3) float64 world units, tally)       the old intermediate's references
"""
from __future__ import annotations

import json
import math
import re
import struct
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from tools.navmesh import esm, nif, params

ROOT = Path(__file__).resolve().parents[2]
INTERMEDIATE = ROOT / "out" / "build" / "argonia.json"
CELL = 4096.0
REACH_ROWS = 2  # a shard this many cell rows outside the box can still reach into it (the largest scaled mesh spans under two cells)
SOLID = {b"STAT", b"ACTI", b"DOOR", b"CONT", b"FURN", b"MSTT", b"TREE", b"FLOR"}  # items (MISC, BOOK) move: left out


def bases(data: Path, keys: set[str]) -> dict[str, tuple[str, tuple[int, ...] | None]]:
    """FormKey -> (MODL, OBND or None) for the keys found in their own plugin as a solid type, the plugin read where the
    game loads it (meshes.plugin_file: Data, else the laid stack's mod)."""
    out: dict[str, tuple[str, tuple[int, ...] | None]] = {}
    by_plugin: dict[str, set[int]] = {}
    for k in keys:
        local, plugin = k.split(":", 1)
        by_plugin.setdefault(plugin, set()).add(int(local, 16))
    from tools.navmesh.meshes import plugin_file
    for plugin, ids in sorted(by_plugin.items()):
        path = plugin_file(plugin, data)
        if path is None:
            continue
        own = len(esm.masters(path)) << 24
        want = {own | i for i in ids}
        for r in esm.records(path, SOLID, groups=SOLID):
            if r.fid in want:
                modl, ob = "", None
                for sig, p in esm.subrecords(r.data):
                    if sig == b"MODL":
                        modl = p.rstrip(b"\0").decode("cp1252")
                    elif sig == b"OBND" and len(p) == 12:
                        b = struct.unpack("<6h", p)
                        if b[3] > b[0] and b[4] > b[1] and b[5] > b[2]:
                            ob = b
                out[f"{r.fid & 0xFFFFFF:06X}:{plugin}"] = (modl, ob)
    return out


def rotation(rx: float, ry: float, rz: float) -> np.ndarray:
    """A reference's rotation as a matrix on column vectors: Skyrim's angles turn clockwise seen down each axis,
    applied z, then y, then x (the CK's order: the world matrix is Rx(-x) Ry(-y) Rz(-z) on the mesh)."""
    def rot(axis, a):
        c, s = math.cos(a), math.sin(a)
        m = np.eye(3)
        i, j = [(1, 2), (2, 0), (0, 1)][axis]
        m[i, i], m[i, j], m[j, i], m[j, j] = c, -s, s, c
        return m
    return rot(0, -rx) @ rot(1, -ry) @ rot(2, -rz)


BAND = (params.AGENT_CLIMB, params.AGENT_HEIGHT)  # above the ground: what stands in an actor's body's way; lower is stepped over


@dataclass
class Footprint:
    centre: np.ndarray  # plan (x, y) of the hull's vertex mean
    stand: np.ndarray  # plan (x, y) of a point on the collision itself in the band: of its points, the nearest the centre
    radius: float  # of the circle with the hull's area
    reach: float  # the hull's farthest point from the centre
    top: float  # the collision's highest point above the ground


def footprint(tris: np.ndarray, ground: float, band=BAND) -> Footprint | None:
    """The plan footprint of collision triangles ((n, 3, 3) world units) within `band` above `ground`: the convex
    hull of the triangles cut to that slab. None when nothing solid lies in the band."""
    if not len(tris):
        return None
    lo, hi = ground + band[0], ground + band[1]
    z = tris[:, :, 2]
    live = (z.max(axis=1) > lo) & (z.min(axis=1) < hi)
    t = tris[live]
    if not len(t):
        return None
    pts = [t[(t[:, :, 2] >= lo) & (t[:, :, 2] <= hi)][:, :2]]
    for i, j in ((0, 1), (1, 2), (2, 0)):
        a, b = t[:, i], t[:, j]
        for lvl in (lo, hi):
            cross = (a[:, 2] - lvl) * (b[:, 2] - lvl) < 0
            if cross.any():
                s = ((lvl - a[cross, 2]) / (b[cross, 2] - a[cross, 2]))[:, None]
                pts.append((a[cross] + s * (b[cross] - a[cross]))[:, :2])
    p = np.unique(np.round(np.concatenate(pts), 2), axis=0)
    if len(p) < 3:
        return None
    try:
        from scipy.spatial import ConvexHull, QhullError
        hull = ConvexHull(p)
    except (QhullError, ValueError):
        return None
    hp = p[hull.vertices]
    c = hp.mean(axis=0)
    return Footprint(c, p[np.hypot(*(p - c).T).argmin()], float(np.sqrt(hull.volume / np.pi)), float(np.hypot(*(hp - c).T).max()), float(tris[:, :, 2].max() - ground))


def _refs(intermediate: Path, recs: list[dict] | None = None) -> list[dict]:
    """The built places' exterior references plus the route infrastructure's persistent ones (the WRLD override's
    `persistentRefs`: gates, landings, bridges; routes/infra.py), each with the same keys."""
    if recs is None:
        recs = json.loads(intermediate.read_text(encoding="utf-8"))["records"]
    out = [x for r in recs if r.get("layer", "").startswith("place:") and r["type"] == "CELL" and r.get("worldspace")
           for x in r.get("refs", []) if not x.get("actor") and not x.get("disabled")]
    out += [x for r in recs if r["type"] == "WRLD" for x in r.get("persistentRefs", [])
            if not x.get("actor") and not x.get("disabled") and x.get("base") and x.get("pos")]
    return out


def own_models(recs: list[dict]) -> dict[str, str]:
    """FormKey -> MODL of the base records the intermediate itself defines (the infrastructure's gate ACTI, signs,
    new STATs), which no plugin on the VM holds yet."""
    return {r["formKey"]: r["model"] for r in recs if r.get("model") and r.get("formKey") and r["type"] in ("STAT", "ACTI")}


def shard_files(refs_dir: Path) -> list[Path]:
    """Every producer's shards of the new world's placed references (tools/newworld/world/cells.py: the refs hook,
    `<refs_dir>/<producer>/cy<+NNN>.jsonl`), and any laid flat in `<refs_dir>` itself, in a fixed order."""
    return sorted(set(refs_dir.glob("*/cy*.jsonl")) | set(refs_dir.glob("*.jsonl")), key=lambda q: (q.name, q.parent.name))


def shard_row(path: Path) -> int | None:
    """The cell row a shard holds (`cy-150.jsonl` -> -150), or None for a file not named by row."""
    m = re.fullmatch(r"cy([+-]\d+)\.jsonl", path.name)
    return int(m.group(1)) if m else None


def read_shard(path: Path) -> list[dict]:
    """One shard's references, one JSON object a line, each given the keys collide() reads whatever its producer
    wrote: `base` (the FormKey `XXXXXX:Plugin`, from `key` when `base` names an editor id as `Plugin:EditorID`,
    else `edid`), `pos` and `rot` (from x, y, z and rx, ry, rz when not given), `scale`, optional `model` (its MODL).
    Disabled ones are left out; the order is by position, so a shard rewritten in another order reads the same."""
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        x = json.loads(ln)
        if x.get("disabled"):
            continue
        pos = x.get("pos") or [x.get("x"), x.get("y"), x.get("z")]
        if x.get("key"):
            base, edid = x["key"], None
        elif FORMKEY.fullmatch(str(x.get("base", ""))):
            base, edid = x["base"], None
        else:
            base, edid = None, x.get("base")
        if None in pos or not (base or edid):
            continue
        out.append({"base": base, "edid": edid, "pos": pos, "rot": x.get("rot") or [x.get("rx", 0.0), x.get("ry", 0.0), x.get("rz", 0.0)],
                    "scale": x.get("scale"), "model": x.get("model"), "box": x.get("box")})
    out.sort(key=lambda r: (r["pos"], r["base"] or r["edid"]))
    return out


def shard_refs(refs_dir: Path) -> list[dict]:
    return [x for f in shard_files(refs_dir) for x in read_shard(f)]


FORMKEY = re.compile(r"[0-9A-Fa-f]{6}:.+")


def models_by_edid(data: Path, names: set[str]) -> dict[str, str]:
    """`Plugin:EditorID` -> MODL for bases a producer names by editor id (the mist's effects), read from the plugin."""
    from tools.navmesh.meshes import plugin_file
    out: dict[str, str] = {}
    by_plugin: dict[str, set[str]] = {}
    for k in names:
        plugin, edid = k.split(":", 1)
        by_plugin.setdefault(plugin, set()).add(edid)
    for plugin, edids in sorted(by_plugin.items()):
        path = plugin_file(plugin, data)
        if path is None:
            continue
        for r in esm.records(path, SOLID, groups=SOLID):
            sub = dict(esm.subrecords(r.data))
            e = sub.get(b"EDID", b"").rstrip(b"\0").decode("cp1252")
            if e in edids and b"MODL" in sub:
                out[f"{plugin}:{e}"] = sub[b"MODL"].rstrip(b"\0").decode("cp1252")
    return out


class Models:
    """Each reference's mesh and its solid collision, looked up once a base: the rule for what can cut the navmesh
    is the mesh's own collision (meshes.Resolver.collision), never the producer or the kind of thing."""

    def __init__(self, data: Path, resolver=None):
        from tools.navmesh import meshes
        self.data = data
        self.res = resolver or meshes.Resolver(data)
        self.modl: dict[str, str] = {}
        self.tris: dict[str, np.ndarray | None] = {}

    def learn(self, refs: list[dict]) -> None:
        for x in refs:
            if x.get("model") and x["base"]:
                self.modl.setdefault(x["base"], x["model"])
        keys = {x["base"] for x in refs if x["base"] and x["base"] not in self.modl}
        if keys:
            got = bases(self.data, keys)
            self.modl.update({k: got[k][0] if k in got else "" for k in keys})
        names = {x["edid"] for x in refs if x["edid"] and x["edid"] not in self.modl}
        if names:
            got = models_by_edid(self.data, names)
            self.modl.update({k: got.get(k, "") for k in names})

    def collision(self, x: dict) -> np.ndarray | None:
        """The reference's base's solid collision triangles in mesh units (empty: the mesh has none), or None when
        its mesh is not found or not readable."""
        k = x["base"] or x["edid"]
        if k not in self.tris:
            m = self.modl.get(k, "")
            c = self.res.collision(m) if m else None
            self.tris[k] = None if c is None or c.tris is None else c.tris
        return self.tris[k]


def write_rows(refs_dir: Path, data: Path, out: Path, box, pad: float, ground=None, resolver=None, sample: int = 8) -> dict:
    """The new world's placed collision for the cells of `box`, one file a cell row: `out/cy<+NNN>.f32`, the world
    triangles (3 corners x 3 floats) that reach within `pad` of the row, from every producer's shards, and beside it
    `cy<+NNN>.n.i32`, the triangle count of each reference in turn (ArgoniaNav fills each as one solid body).

    `out/tally.json`: `refs` (in the box), `collidable` (those whose base's mesh has solid collision: counted by
    base), `fed` (those whose triangles were written: counted as they are written), `no_collision`, `unresolved`
    (mesh not found or not readable: a fault), `triangles`, and per producer the same counts.
    `out/probe.npy`: every `sample`-th fed reference whose collision stands in an actor's way (footprint() over the
    ground under it, `ground(x, y)`): x, y of a point on its collision, footprint radius, the collision's top above the ground; the built
    navmesh is checked against these (checks.py: a hole where each stands)."""
    x0, y0, x1, y1 = box
    out.mkdir(parents=True, exist_ok=True)
    for f in list(out.glob("cy*.f32")) + list(out.glob("cy*.i32")) + list(out.glob("*.tmp")):
        f.unlink()
    models = Models(data, resolver)
    lo_x, hi_x = x0 * CELL - pad, (x1 + 1) * CELL + pad
    tally = {"refs": 0, "collidable": 0, "fed": 0, "no_collision": 0, "unresolved": 0, "triangles": 0, "producers": {}, "unresolved_models": []}
    per_base: dict[str, int] = {}
    files: dict[int, object] = {}
    runs: dict[int, list[int]] = {}
    probe = []
    try:
        for path in shard_files(refs_dir):
            row = shard_row(path)
            if row is not None and not y0 - REACH_ROWS <= row <= y1 + REACH_ROWS:
                continue
            refs = read_shard(path)
            models.learn(refs)
            who = tally["producers"].setdefault(path.parent.name if path.parent != refs_dir else "", {"refs": 0, "fed": 0})
            for x in refs:
                inside = x0 <= x["pos"][0] // CELL <= x1 and y0 <= x["pos"][1] // CELL <= y1
                local = models.collision(x) if x.get("box") is None else nif._box_tris(-np.array(x["box"], float), np.array(x["box"], float))
                k = x["base"] or x["edid"]
                if inside:
                    tally["refs"] += 1
                    who["refs"] += 1
                    per_base[k] = per_base.get(k, 0) + 1
                if local is None:
                    if inside:
                        tally["unresolved"] += 1
                        if len(tally["unresolved_models"]) < 10 and k not in tally["unresolved_models"]:
                            tally["unresolved_models"].append(k)
                    continue
                if not len(local):
                    tally["no_collision"] += inside
                    continue
                m = rotation(*x["rot"]) * float(x.get("scale") or 1.0)
                w = (local.reshape(-1, 3) @ m.T + np.array(x["pos"], float)).reshape(-1, 3, 3)
                keep = (w[:, :, 0].max(axis=1) >= lo_x) & (w[:, :, 0].min(axis=1) <= hi_x)
                ra = np.floor((w[:, :, 1].min(axis=1) - pad) / CELL).astype(int)
                rb = np.floor((w[:, :, 1].max(axis=1) + pad) / CELL).astype(int)
                wrote = False
                for r in range(max(y0, int(ra.min())), min(y1, int(rb.max())) + 1):
                    t = w[keep & (ra <= r) & (rb >= r)]
                    if not len(t):
                        continue
                    if r not in files:
                        files[r] = open(out / f"cy{r:+04d}.f32.tmp", "wb")
                    files[r].write(t.astype(np.float32).tobytes())
                    runs.setdefault(r, []).append(len(t))
                    tally["triangles"] += len(t)
                    wrote = True
                if inside and wrote:
                    tally["fed"] += 1
                    who["fed"] += 1
                    if ground is not None and tally["fed"] % sample == 0:
                        f = footprint(w, float(ground(x["pos"][0], x["pos"][1])))
                        if f is not None:
                            probe.append((f.stand[0], f.stand[1], f.radius, f.top))
    finally:
        for fh in files.values():
            fh.close()
    for r in files:
        np.array(runs[r], np.int32).tofile(out / f"cy{r:+04d}.n.i32")
        (out / f"cy{r:+04d}.f32.tmp").replace(out / f"cy{r:+04d}.f32")
    # the collidable references counted the other way, by base: every reference of a base whose mesh has collision
    tally["collidable"] = sum(n for k, n in per_base.items() if models.tris.get(k) is not None and len(models.tris[k]))
    np.save(out / "probe.npy", np.array(probe, np.float64).reshape(-1, 4))
    (out / "tally.json").write_text(json.dumps(tally, indent=1, sort_keys=True) + "\n")
    return tally


def navmesh_box(refs_dir: Path):
    """The cells the province's navmesh is built over, for the refs folder of a world plugin (`<plugin>/refs`): the
    land grid one cell in from its edge (__main__.build's default box). None when there is no land beside it."""
    from tools.navmesh import world
    try:
        b = world.Land.load(refs_dir.parent).box
    except (OSError, ValueError, KeyError):
        return None
    return b[0] + 1, b[1] + 1, b[2] - 1, b[3] - 1


def collidable_count(refs_dir: Path, data: Path, box=None, resolver=None) -> int:
    """How many references of the producers' shards can cut the navmesh: those whose base's mesh has solid
    collision, standing in the cells the navmesh is built over (`box`, by default navmesh_box). The build's own
    count of what it fed (build.json placed.objects) must equal this (tools/newworld/world/navobjects.py)."""
    from tools.navmesh import meshes
    if resolver is None:
        meshes.PROFILE = "NewWorld"
    box = navmesh_box(refs_dir) if box is None else box
    models = Models(data, resolver)
    n = 0
    for path in shard_files(refs_dir):
        refs = read_shard(path)
        models.learn(refs)
        for x in refs:
            if box is not None and not (box[0] <= x["pos"][0] // CELL <= box[2] and box[1] <= x["pos"][1] // CELL <= box[3]):
                continue
            t = models.collision(x)
            n += x.get("box") is not None or (t is not None and len(t) > 0)
    return n


def from_shards(refs_dir: Path, data: Path, resolver=None) -> tuple[np.ndarray, dict]:
    """Every shard's collision as one array (a small world, a test): the province is fed by write_rows."""
    refs = shard_refs(refs_dir)
    models = Models(data, resolver)
    models.learn(refs)
    for x in refs:
        x["base"] = x["base"] or x["edid"]
    return collide(refs, data, {k: m for k, m in models.modl.items() if m}, models.res)


def triangles(data: Path, intermediate: Path = INTERMEDIATE, resolver=None) -> tuple[np.ndarray, dict]:
    recs = json.loads(intermediate.read_text(encoding="utf-8"))["records"]
    return collide(_refs(intermediate, recs), data, own_models(recs), resolver)


def collide(refs: list[dict], data: Path, own: dict[str, str], resolver=None) -> tuple[np.ndarray, dict]:
    """The references' collision triangles in world units: own base models first, then each base's MODL/OBND."""
    from tools.navmesh import meshes
    info = bases(data, {x["base"] for x in refs if x["base"] not in own})
    info.update({k: (m, None) for k, m in own.items()})
    res = resolver or meshes.Resolver(data)
    out: list[np.ndarray] = []
    tally = {"refs": len(refs), "collision": 0, "no_collision": 0, "box_fallback": 0, "no_base": 0, "triangles": 0}
    tally["primitive"] = 0
    for x in sorted(refs, key=lambda r: r.get("formKey", "")):
        modl, ob = info.get(x["base"], ("", None))
        c = res.collision(modl) if modl and x.get("box") is None else None
        if x.get("box") is not None:  # a collision marker: its primitive's box (half extents round its origin) is the solid
            b = np.array(x["box"], float)
            local = nif._box_tris(-b, b)
            tally["primitive"] += 1
        elif c is not None and c.tris is not None:
            local = c.tris
            tally["collision" if len(local) else "no_collision"] += 1
        elif ob is not None:
            local = nif._box_tris(np.array(ob[:3], float), np.array(ob[3:], float))
            tally["box_fallback"] += 1
        else:
            tally["no_base"] += 1
            continue
        if not len(local):
            continue
        m = rotation(*x["rot"]) * float(x.get("scale") or 1.0)
        out.append(local.reshape(-1, 3) @ m.T + np.array(x["pos"], float))
    tris = np.concatenate(out).reshape(-1, 3, 3) if out else np.zeros((0, 3, 3))
    tally["triangles"] = len(tris)
    return tris, tally
