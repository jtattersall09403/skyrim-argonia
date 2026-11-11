"""Placed-object collision for the navmesh job: references as the triangles of their meshes' own collision, in
world units.

Each reference's base is looked up in its own plugin (esm.py: MODL and OBND) unless the reference names its mesh. The
mesh is found as the game finds it (meshes.py: the laid mod stack's loose files, then BSAs) and its Havok collision
read (nif.py: compressed mesh, packed strips, convex hulls, boxes, capsules; the solid layers only). The triangles
are scaled, turned by the reference's rotation and moved to its position. A mesh with no solid collision (a fern, a
reed, a mist effect) adds nothing, as in game: that, never the producer or the kind of thing, is the rule for what
can cut the navmesh.

The new world's scatter (nw-02 step 8: trees, plants, rocks, cliffs, logs, road dressing, mist; every producer's
shards under `<plugin>/refs/<producer>/cy<+NNN>.jsonl`) only stands in the way: each reference is reduced to the
voxel columns its solid blocks (solid.py), a cell row at a time and cached by row, and ArgoniaNav lays no mesh there. What Skyrim's own navmesh does round
such things is measured by vanilla.py (docs/research/nw-02-walk5-navmesh.md): it is cut round whatever rises above
stepping height, whatever its width, and left whole over what stays below.

A built place's references (the old intermediate, out/build/argonia.json: `place:` layers and the route
infrastructure's persistent references) are one array, and carry an actor where a face is level enough. There a
reference with a `box` (a collision marker's primitive, half extents round its origin) is that box, and a base whose
mesh is not on the VM falls back to its OBND box, counted.

    write_rows(refs_dir, data, out, box, heights, frame) -> tally   the new world's refs shards as blocked columns, a file a cell row
    blocked_columns(tris, heights, frame) -> (runs, faces)          the voxel columns one thing blocks (solid.py)
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


PREP = "rows/2"  # bump when what a row's blocked columns are made from changes: every cached row is then built again
_JOB: dict = {}  # what a row's worker reads (set before the pool forks)


def world_tris(local: np.ndarray, x: dict) -> np.ndarray:
    """A base's collision (mesh units) as the reference's own triangles in world units."""
    m = rotation(*x["rot"]) * float(x.get("scale") or 1.0)
    return (local.reshape(-1, 3) @ m.T + np.array(x["pos"], float)).reshape(-1, 3, 3)


def blocked_columns(tris: np.ndarray, heights: np.ndarray, frame) -> tuple[np.ndarray, int]:
    """The voxel columns one thing's collision (world triangles) blocks, as rows (j, first i, last i), and how many
    of its faces lie in the band: solid.columns, and every column those close in, over the ground raster `heights` (row 0 north; `frame` = the
    world x and y of its first sample and the sample spacing)."""
    from tools.navmesh import solid
    hit, i0, j0, band = solid.columns(np.ascontiguousarray(tris, np.float64), heights, float(frame[0]), float(frame[1]), float(frame[2]),
                                      params.CELL_SIZE, params.AGENT_CLIMB, params.AGENT_HEIGHT)
    if hit.shape[0] > 2 and hit.shape[1] > 2:
        from scipy import ndimage
        hit = ndimage.binary_fill_holes(hit)  # ground its own columns close in is inside it: under a shell, within a ring
    return solid.runs(hit, i0, j0), int(band)


def _row_job(s: int):
    """One cell row's references reduced to the columns they block: (row, runs, the row's record)."""
    from tools.navmesh import solid
    J = _JOB
    h, frame, (i_lo, i_hi, j_lo, j_hi) = J["h"], J["frame"], J["window"]
    x0u, ytop, step = frame
    got, probe = [], []
    rec = {"fed": 0, "triangles": 0, "band_triangles": 0, "producers": {}}
    for x in J["rows"][s]:
        w = world_tris(J["tris"][x["k"]] if x.get("box") is None else nif._box_tris(-np.array(x["box"], float), np.array(x["box"], float)), x)
        rr, band = blocked_columns(w, h, frame)
        rec["triangles"] += len(w)
        rec["band_triangles"] += band
        if len(rr):
            got.append(rr)
        if x["inside"]:
            rec["fed"] += 1
            rec["producers"][x["who"]] = rec["producers"].get(x["who"], 0) + 1
            if rec["fed"] % J["sample"] == 0:
                gz = float(h[min(max(int(round((ytop - x["pos"][1]) / step)), 0), h.shape[0] - 1), min(max(int(round((x["pos"][0] - x0u) / step)), 0), h.shape[1] - 1)])
                f = footprint(w, gz)
                if f is not None:
                    probe.append([float(f.stand[0]), float(f.stand[1]), f.radius, f.top])
    runs = np.zeros((0, 3), np.int32)
    if got:  # one raster over what the row's things reach of the box, so columns two things block are held once
        rr = np.concatenate(got)
        ja, jb = max(int(rr[:, 0].min()), j_lo), min(int(rr[:, 0].max()), j_hi - 1)
        if jb >= ja:
            mask = np.zeros((jb - ja + 1, i_hi - i_lo), bool)
            solid.paint(mask, i_lo, ja, rr)
            runs = solid.runs(mask, i_lo, ja)
    rec["columns"] = int((runs[:, 2] - runs[:, 1] + 1).sum()) if len(runs) else 0
    rec["probe"] = probe
    return s, runs, rec


def write_rows(refs_dir: Path, data: Path, out: Path, box, heights: np.ndarray, frame, cache: Path | None = None, resolver=None,
               sample: int = 8, workers: int | None = None) -> dict:
    """The new world's placed collision for the cells of `box`, reduced to the voxel columns it blocks (solid.py):
    `out/cy<+NNN>.runs.i32` for each cell row that holds any, rows of (j, first i, last i) over the row's cells and
    the border ArgoniaNav reads round them. `heights` is the ground raster (row 0 north), `frame` the world x and y
    of its first sample and the sample spacing.

    The work is done a row of references at a time and kept under `cache` (`cy<+NNN>.npy` with `.json`), each row
    under the digest of what it is made from: its references, their bases' collision, the ground they can reach,
    the box and the rule's numbers. A row whose digest stands is not built again.

    `out/tally.json`: `refs` (in the box), `collidable` (those whose base's mesh has solid collision: counted by
    base), `fed` (those reduced to columns: counted by the rows as they do it), `no_collision`, `unresolved` (mesh
    not found or not readable: a fault), `triangles` (the collision instanced), `band_triangles` (the faces that
    reach the band of some column: what is cut to columns), `columns` (blocked), and per producer the counts.
    `out/probe.npy`: every `sample`-th fed reference of a row whose collision stands in an actor's way (footprint()
    over the ground under it): x, y of a point on its collision, footprint radius, the collision's top above the
    ground; the built navmesh is checked against these (checks.py: a hole where each stands)."""
    import hashlib
    import multiprocessing as mp
    import os
    import shutil
    from tools.navmesh import solid
    x0, y0, x1, y1 = box
    x0u, ytop, step = (float(v) for v in frame)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    cs = params.CELL_SIZE
    per, bcols = int(round(CELL / cs)), int(round(params.BORDER_SAMPLES * step / cs))
    window = (x0 * per - bcols, (x1 + 1) * per + bcols, y0 * per - bcols, (y1 + 1) * per + bcols)  # i, j: first, one past the last
    models = Models(data, resolver)
    tally = {"refs": 0, "collidable": 0, "fed": 0, "no_collision": 0, "unresolved": 0, "triangles": 0, "band_triangles": 0,
             "columns": 0, "producers": {}, "unresolved_models": []}
    per_base: dict[str, int] = {}
    reach: dict[str, float] = {}
    digest: dict[str, bytes] = {}
    rows: dict[int, list[dict]] = {}
    far = 0.0
    for path in shard_files(refs_dir):
        row = shard_row(path)
        if row is not None and not y0 - REACH_ROWS <= row <= y1 + REACH_ROWS:
            continue
        refs = read_shard(path)
        models.learn(refs)
        name = path.parent.name if path.parent != refs_dir else ""
        who = tally["producers"].setdefault(name, {"refs": 0, "fed": 0})
        for x in refs:
            inside = x0 <= x["pos"][0] // CELL <= x1 and y0 <= x["pos"][1] // CELL <= y1
            k = x["base"] or x["edid"]
            local = models.collision(x) if x.get("box") is None else nif._box_tris(-np.array(x["box"], float), np.array(x["box"], float))
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
            if x.get("box") is None and k not in reach:
                reach[k] = float(np.linalg.norm(local.reshape(-1, 3), axis=1).max())
                digest[k] = hashlib.blake2b(np.ascontiguousarray(local, np.float64).tobytes(), digest_size=16).digest()
            r = (reach[k] if x.get("box") is None else float(np.linalg.norm(x["box"]))) * float(x.get("scale") or 1.0) + cs
            px, py = x["pos"][0], x["pos"][1]
            if px + r < window[0] * cs or px - r > window[1] * cs or py + r < window[2] * cs or py - r > window[3] * cs:
                continue  # it cannot reach a cell of the box
            far = max(far, r)
            rows.setdefault(int(py // CELL), []).append({"k": k, "pos": x["pos"], "rot": x["rot"], "scale": x.get("scale"), "box": x.get("box"),
                                                         "inside": bool(inside), "who": name, "reach": r})
    if far > REACH_ROWS * CELL - bcols * cs:  # then one in a row not read could reach the box as well
        raise ValueError(f"navmesh: a placed thing reaches {far:.0f} units, past the {REACH_ROWS} cell rows of shards read either side of the box")
    # the collidable references counted the other way, by base: every reference of a base whose mesh has collision
    tally["collidable"] = sum(n for k, n in per_base.items() if models.tris.get(k) is not None and len(models.tris[k]))
    h = np.ascontiguousarray(heights, np.float32)
    keys = {}
    for s, xs in rows.items():
        hk = hashlib.blake2b(digest_size=16)
        hk.update(json.dumps([PREP, cs, params.AGENT_CLIMB, params.AGENT_HEIGHT, list(window), [x0u, ytop, step], list(h.shape), sample]).encode())
        far_s = max(x["reach"] for x in xs)
        ra = max(int((ytop - ((s + 1) * CELL + far_s)) // step) - 1, 0)
        rb = min(int((ytop - (s * CELL - far_s)) // step) + 3, h.shape[0])
        ca = max(int((window[0] * cs - x0u) // step) - 2, 0)
        cb = min(int((window[1] * cs - x0u) // step) + 3, h.shape[1])
        hk.update(np.ascontiguousarray(h[ra:rb, ca:cb]).tobytes())
        for x in xs:
            hk.update(json.dumps([x["k"], x["pos"], x["rot"], x["scale"], x["box"], x["inside"], x["who"]]).encode())
            hk.update(digest.get(x["k"], b""))
        keys[s] = hk.hexdigest()
    built: dict[int, tuple] = {}
    stale = []
    if cache is not None:
        cache.mkdir(parents=True, exist_ok=True)
        for f in cache.glob("cy*"):  # a row that holds nothing now
            if shard_row(Path(f.name.split(".")[0] + ".jsonl")) not in rows:
                f.unlink()
    for s in sorted(rows):
        try:
            rec = json.loads((cache / f"cy{s:+04d}.json").read_text())
            if rec["key"] != keys[s]:
                raise ValueError
            built[s] = (np.load(cache / f"cy{s:+04d}.npy"), rec)
        except (OSError, ValueError, KeyError, TypeError):
            stale.append(s)
    reused = len(built)
    _JOB.update(h=h, frame=(x0u, ytop, step), window=window, rows=rows, tris=models.tris, sample=sample)
    n_proc = workers if workers is not None else min(4, os.cpu_count() or 1)
    try:
        if n_proc > 1 and len(stale) > 2:
            with mp.get_context("fork").Pool(n_proc) as pool:
                done = list(pool.imap_unordered(_row_job, stale))
        else:
            done = [_row_job(s) for s in stale]
    finally:
        _JOB.clear()
    for s, runs, rec in done:
        rec["key"] = keys[s]
        built[s] = (runs, rec)
        if cache is not None:
            tmp = cache / f"cy{s:+04d}.npy.tmp"
            with open(tmp, "wb") as fh:
                np.save(fh, runs)
            tmp.replace(cache / f"cy{s:+04d}.npy")
            (cache / f"cy{s:+04d}.json.tmp").write_text(json.dumps(rec, sort_keys=True) + "\n")
            (cache / f"cy{s:+04d}.json.tmp").replace(cache / f"cy{s:+04d}.json")
    probe = []
    for s in sorted(built):
        rec = built[s][1]
        for k in ("fed", "triangles", "band_triangles"):
            tally[k] += rec[k]
        for name, n in rec["producers"].items():
            tally["producers"][name]["fed"] += n
        probe += rec["probe"]
    for r in range(y0, y1 + 1):  # each cell row's file: the blocked columns of its cells and their border, from every row that reaches it
        ja, jb = r * per - bcols, (r + 1) * per + bcols
        parts = [a[(a[:, 0] >= ja) & (a[:, 0] < jb)] for s in sorted(built) for a in [built[s][0]] if len(a)]
        parts = [a for a in parts if len(a)]
        if not parts:
            continue
        mask = np.zeros((jb - ja, window[1] - window[0]), bool)
        for a in parts:
            solid.paint(mask, window[0], ja, a)
        rr = solid.runs(mask, window[0], ja)
        tally["columns"] += int(mask[bcols:bcols + per].sum())
        rr.tofile(out / f"cy{r:+04d}.runs.i32")
    np.save(out / "probe.npy", np.array(probe, np.float64).reshape(-1, 4))
    (out / "tally.json").write_text(json.dumps(tally, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"placed rows": {"built": len(stale), "reused": reused}}), flush=True)
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
