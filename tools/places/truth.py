"""Do the measuring tools agree with each other and with what the build writes? No build, no browser, no lock.

    python -m tools.places truth <place> [<place> ...] [--sample N] [--tier ground,pieces,kinds,fresh] [--json]

Four tiers, each printing every disagreement (point or piece, and both values), and a count per tier:

  ground  the place's ground height read by an independent reference (global vertex table, every land row applied by
          the build's rule) against seat.py's reader (which units, the look scene, draft check, ground and sap all
          use), the studio page's per-cell reading of land rows, and the heights a built shard wrote for the place's
          patched cells (out/places/shards/<place>/plan.json; skipped and said when the shard is older than the
          place files). Land-row faults the build would refuse or misread are listed: two rows giving one vertex
          different heights, and an edge vertex patched in one cell's copy but not its neighbour's.
  pieces  every piece's pose as the place file, the look scene (seated) and the built plan give it; its world box by
          the look scene (geom), by draft check (obvious / seat.model_bounds) and by draft geom (bounds and tilt); its
          lowest point over the ground by each box. Boxes agree within 2 units; poses within 1 unit, 0.001 rad.
  kinds   every base's class by the one classifier (tools/places/classify.py) beside how units, the look tool and
          draft geom treat it; every contradiction, and every base classed by the fallback, with its count.
  fresh   what each tool reads: working tree or commit (a dirty place dir means units and draft check read files the
          studio's pictures, drawn from the commit, do not), bundle and catalogue ages, the shard's age, the builder.

Exit 1 when any tier finds a disagreement. The golden fixture (tools/tests/test_places_truth.py) holds the known
answers; this command holds the real drafts to agreement.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GROUND_TOL = 1.0
BOX_TOL = 2.0
POS_TOL = 1.0
ROT_TOL = 1e-3
BUILT_TOL = 4.0     # the build stores heights in 8-unit steps (VHGT): a height is within half a step of what we meant


# ---------------- ground ----------------
class Reference:
    """An independent ground: one table of global vertices (world / 128), the bundle's heights with every land row's
    dz applied once per vertex, the game's triangle split. Written without seat.py so the two can be compared."""

    def __init__(self, cells: dict, rows: list[dict]):
        self.v: dict[tuple[int, int], float] = {}
        for (cx, cy), h in cells.items():
            for row in range(33):
                for col in range(33):
                    self.v.setdefault((cx * 32 + col, cy * 32 + row), float(h[row * 33 + col]))
        self.clashes, self.one_sided, done = [], [], {}
        for r in rows:
            cx, cy = int(r["cell"][0]), int(r["cell"][1])
            if (cx, cy) not in cells:
                continue
            for row, col, dz in r["verts"]:
                g = (cx * 32 + int(col), cy * 32 + int(row))
                if g in done:
                    if abs(done[g] - float(dz)) > 1e-6:
                        self.clashes.append((g, done[g], float(dz)))
                    continue
                done[g] = float(dz)
                self.v[g] += float(dz)
        # an edge vertex named in one cell's row and not in a loaded neighbour's: the page reads the two copies apart
        named: dict[tuple[int, int], set] = {}
        for r in rows:
            cx, cy = int(r["cell"][0]), int(r["cell"][1])
            for row, col, _ in r["verts"]:
                named.setdefault((cx * 32 + int(col), cy * 32 + int(row)), set()).add((cx, cy))
        for (gx, gy), have in named.items():
            holders = {(cx, cy) for cx in {gx // 32, (gx - 1) // 32} for cy in {gy // 32, (gy - 1) // 32}
                       if (cx, cy) in cells and 0 <= gx - cx * 32 <= 32 and 0 <= gy - cy * 32 <= 32}
            if holders - have:
                self.one_sided.append(((gx, gy), sorted(have), sorted(holders - have)))

    def height(self, x: float, y: float) -> float | None:
        fx, fy = x / 128.0, y / 128.0
        gx, gy = math.floor(fx), math.floor(fy)
        tx, ty = fx - gx, fy - gy
        v = [self.v.get((gx, gy)), self.v.get((gx + 1, gy)), self.v.get((gx, gy + 1)), self.v.get((gx + 1, gy + 1))]
        if any(a is None for a in v):
            return None
        if tx + ty <= 1:
            return v[0] + (v[1] - v[0]) * tx + (v[2] - v[0]) * ty
        return v[3] + (v[2] - v[3]) * (1 - tx) + (v[1] - v[3]) * (1 - ty)


class PageGround:
    """The studio page's reading (web/js/edits.js modelFromFiles + seat.js): each cell keeps its own copy of the land
    rows' dz, the last row at a vertex wins, and a point reads the cell it lies in."""

    def __init__(self, cells: dict, rows: list[dict]):
        from tools.places.seat import Ground
        over: dict = {}
        for r in rows:
            cm = over.setdefault((int(r["cell"][0]), int(r["cell"][1])), {})
            for row, col, dz in r["verts"]:
                cm[int(row) * 33 + int(col)] = float(dz)
        cs = {k: list(v) for k, v in cells.items()}
        for k, cm in over.items():
            if k in cs:
                for i, dz in cm.items():
                    cs[k][i] += dz
        self.g = Ground(cs, {})

    def height(self, x, y):
        return self.g.height(x, y)


def place_points(files: dict, rows: list[dict], step: float, sample: int | None) -> list[tuple[float, float, str]]:
    refs = [r for r in files["spaces"]["exterior"]["refs"] if r.get("pos") and not r.get("removed")]
    pts: list[tuple[float, float, str]] = []
    if refs:
        xs, ys = [r["pos"][0] for r in refs], [r["pos"][1] for r in refs]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        nx, ny = int((x1 - x0) / step) + 1, int((y1 - y0) / step) + 1
        stride = max(1, int(math.sqrt(nx * ny / sample))) if sample else 1
        for i in range(0, nx, stride):
            for j in range(0, ny, stride):
                pts.append((x0 + i * step + 7.3, y0 + j * step + 3.1, "grid"))
    for r in rows:
        cx, cy = r["cell"]
        for row, col, _ in r["verts"]:
            pts.append(((cx * 32 + col) * 128.0, (cy * 32 + row) * 128.0, f"vertex {cx},{cy}:{row},{col}"))
    return pts


def built_heights(pid: str, shards: Path) -> tuple[dict | None, str]:
    """Global vertex -> height the shard's LAND overrides store, or (None, why)."""
    plan = shards / pid / "plan.json"
    if not plan.exists():
        return None, "no built shard"
    import base64

    import numpy as np

    from tools.newworld.world import quantize
    d = json.loads(plan.read_text())
    out = {}
    for c in d.get("land") or []:
        hs = c.get("heights")
        if not hs:
            continue
        steps = quantize.decode(float(hs["offset"]), np.frombuffer(base64.b64decode(hs["deltas"]), np.int8).reshape(33, 33))
        cx, cy = int(c["x"]), int(c["y"])
        for row in range(33):
            for col in range(33):
                out[(cx * 32 + col, cy * 32 + row)] = float(steps[row, col]) * 8.0
    return out, f"{len(out)} built vertices"


def tier_ground(pid: str, files: dict, ctx: dict, sample: int | None, out: list) -> None:
    from tools.places import seat
    base = seat.Ground.load(ctx["bundles"] / f"ground.{pid}")
    rows = files.get("land") or []
    ref = Reference(base.cells, rows)
    mine = seat.Ground({k: list(v) for k, v in base.cells.items()}, base.water_by_cell, base.default_water)
    mine.apply_patches(rows)
    page = PageGround(base.cells, rows)
    for g, a, b in ref.clashes:
        out.append(("ground", f"vertex {g}: two land rows give dz {a:.1f} and {b:.1f} (the build refuses it)"))
    for g, have, miss in ref.one_sided:
        out.append(("ground", f"vertex {g} on a cell edge patched in {have} but not in {miss}: the page reads it apart"))
    for x, y, what in place_points(files, rows, 64.0, sample):
        r = ref.height(x, y)
        if r is None:
            continue
        for name, h in (("seat.py (units, scene, draft check, sap)", mine.height(x, y)), ("studio page", page.height(x, y))):
            if h is None or abs(h - r) > GROUND_TOL:
                out.append(("ground", f"{what} ({x:.0f},{y:.0f}): reference {r:.1f}, {name} {h if h is None else round(h, 1)}"))
    if ctx.get("stale_shard"):
        out.append(("note", f"built heights skipped: {ctx['stale_shard']}"))
        return
    bh, why = built_heights(pid, ctx["shards"])
    if bh is None:
        out.append(("note", f"built heights skipped: {why}"))
        return
    for g, h in bh.items():
        r = ref.v.get(g)
        if r is not None and abs(h - r) > BUILT_TOL:
            out.append(("ground", f"built vertex {g}: reference {r:.1f}, the shard's LAND {h:.1f}"))


# ---------------- pieces ----------------
def _box_draft(r: dict, bases: dict):
    import numpy as np

    from tools.places import xform
    from tools.places.draft import geom as dgeom
    b = dgeom.bounds(r, bases)
    if not b:
        return None
    rot = xform.rotation(r.get("rot") or [0, 0, 0])
    pts = np.array([[x, y, z] for x in (b[0][0], b[1][0]) for y in (b[0][1], b[1][1]) for z in (b[0][2], b[1][2])])
    w = (np.asarray(rot) @ pts.T).T + np.asarray(r["pos"], float)
    return w.min(0), w.max(0)


def tier_pieces(pid: str, files: dict, ctx: dict, sample: int | None, out: list) -> None:
    from tools.places.draft import obvious
    from tools.places.look import geom
    from tools.places.look.scene import Scene
    sc = Scene(pid)
    raw = {r["id"]: r for r in files["spaces"]["exterior"]["refs"]}
    built = {}
    plan = ctx["shards"] / pid / "plan.json"
    if plan.exists() and not ctx.get("stale_shard"):
        built = {r["id"]: r for r in json.loads(plan.read_text()).get("refs") or [] if r.get("space") in (None, "exterior")}
    pieces = sc.pieces[::max(1, len(sc.pieces) // sample)] if sample else sc.pieces
    for p in pieces:
        r = sc.refs[p["id"]]
        f = raw.get(p["id"]) or {}
        for k in (0, 1):
            if abs(r["pos"][k] - f["pos"][k]) > POS_TOL:
                out.append(("pieces", f"{p['id']}: pos[{k}] file {f['pos'][k]}, scene {r['pos'][k]}"))
        b = built.get(p["id"])
        if b:
            for k in range(3):
                if abs(float(b["pos"][k]) - float(r["pos"][k])) > POS_TOL:
                    out.append(("pieces", f"{p['id']}: pos[{k}] scene (seated) {r['pos'][k]:.1f}, built {b['pos'][k]}"))
                if abs(float((b.get("rot") or [0, 0, 0])[k]) - float((r.get("rot") or [0, 0, 0])[k])) > ROT_TOL:
                    out.append(("pieces", f"{p['id']}: rot[{k}] scene {r.get('rot')}, built {b.get('rot')}"))
            if abs(float(b.get("scale") or 1) - float(r.get("scale") or 1)) > 1e-3:
                out.append(("pieces", f"{p['id']}: scale scene {r.get('scale')}, built {b.get('scale')}"))
        if not p.get("model") or p.get("missing"):
            continue
        a = geom.aabb(p)
        o = geom.aabb(obvious.piece(r, sc.bases))
        d = _box_draft(r, sc.bases)
        for name, bx in (("draft check", o), ("draft geom", d)):
            if bx is None:
                continue
            gap = max(float(abs(bx[0] - a[0]).max()), float(abs(bx[1] - a[1]).max()))
            if gap > BOX_TOL:
                out.append(("boxes", f"{p['id']} ({p.get('edid')}): look box {_fmt(a)}, {name} box {_fmt(bx)} (off {gap:.0f})"))


def _fmt(b) -> str:
    return "[" + ",".join(f"{v:.0f}" for v in list(b[0]) + list(b[1])) + "]"


# ---------------- kinds ----------------
def tier_kinds(pid: str, files: dict, ctx: dict, sample: int | None, out: list) -> None:
    from collections import Counter

    from tools.places import classify, units
    from tools.places.draft import geom as dgeom
    from tools.places.look import geom
    from tools.places.look.scene import Scene
    sc = ctx.get("scene") or Scene(pid)
    seen, fallback = {}, Counter()
    for p in sc.pieces:
        if p["base"] in seen:
            continue
        cls, fb = classify.classify(p)
        seen[p["base"]] = cls
        if fb:
            fallback[(p["base"], p.get("edid"), p.get("model"))] += 1
            continue
        role = units._role0(p)
        name = f"{p['base']} ({p.get('edid')}, {p.get('model')})"
        if cls in classify.NOT_STRUCTURE and role in ("body", "span", "steps"):
            out.append(("kinds", f"{name}: classifier {cls}, units {role}"))
        if cls in ("light", "effect", "marker") and geom.solid(p):
            out.append(("kinds", f"{name}: classifier {cls}, the look tool holds things up on it (solid)"))
        base = sc.bases.get(p["base"]) or {}
        if p.get("resolved") and geom.solid(p) != dgeom.solid(base) and cls not in ("plant", "light", "marker"):
            out.append(("kinds", f"{name}: classifier {cls}, look solid {geom.solid(p)}, draft geom solid {dgeom.solid(base)}"))
    n = Counter(seen.values())
    out.append(("note", "classes: " + ", ".join(f"{k} {v}" for k, v in sorted(n.items()))))
    for (b, e, m), c in sorted(fallback.items(), key=lambda kv: -kv[1]):
        out.append(("fallback", f"{b} ({e}, {m}): no rule matched; classed 'thing' ({c} base)"))


# ---------------- fresh ----------------
def _git(*a) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True).stdout.strip()


def tier_fresh(pid: str, files: dict, ctx: dict, sample: int | None, out: list) -> None:
    pdir = ctx["places"] / pid
    dirty = _git("status", "--porcelain", "--", str(pdir))
    if dirty:
        out.append(("fresh", f"{pid}: the place files differ from the commit ({len(dirty.splitlines())} paths): units, "
                    "draft check and truth read the working tree; the studio's pictures draw the committed files"))
    # the place files' age: their last commit, or now when the working tree differs (checkout times mean nothing)
    import time
    newest = time.time() if dirty else float(_git("log", "-1", "--format=%ct", "--", str(pdir)) or 0)
    cat = ROOT / "out" / "places" / "catalogue" / "bases.jsonl"
    for b in sorted(ctx["bundles"].glob(f"ground.{pid}")) + sorted(ctx["bundles"].glob(f"src.{files['place'].get('source_id')}")):
        bj = b / "bundle.json"
        if cat.exists() and bj.exists() and bj.stat().st_mtime < cat.stat().st_mtime:
            out.append(("note", f"{b.name}: bundle older than the catalogue (a base added since reads as missing until it is rebuilt)"))
    shard = ctx["shards"] / pid / "plan.json"
    if shard.exists() and shard.stat().st_mtime < newest:
        ctx["stale_shard"] = f"the built shard ({shard}) is older than the place files"
        out.append(("note", ctx["stale_shard"]))
    from tools.places import build
    if build.TOOL.exists():
        src = max((p.stat().st_mtime for p in build.TOOL_PROJ.parent.rglob("*.cs")), default=0)
        if build.TOOL.stat().st_mtime < src:
            out.append(("fresh", f"the compiled builder {build.TOOL} is older than its source"))
        try:
            build.TOOL.resolve().relative_to(ROOT)
        except ValueError:
            out.append(("note", f"the compiled builder is another checkout's: {build.TOOL.resolve()}"))


TIERS = {"fresh": tier_fresh, "ground": tier_ground, "pieces": tier_pieces, "kinds": tier_kinds}


def run(pid: str, tiers=tuple(TIERS), sample: int | None = None, places: Path | None = None,
        bundles: Path | None = None, shards: Path | None = None) -> list[tuple[str, str]]:
    from tools.places import edits
    from tools.places.seat import BUNDLES, PLACES
    ctx = {"places": places or PLACES, "bundles": bundles or BUNDLES, "shards": shards or ROOT / "out" / "places" / "shards"}
    files = edits.load_place(ctx["places"] / pid)
    out: list[tuple[str, str]] = []
    for t in ("fresh", "ground", "pieces", "kinds"):
        if t in tiers:
            TIERS[t](pid, files, ctx, sample, out)
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places truth")
    ap.add_argument("places", nargs="+")
    ap.add_argument("--sample", type=int)
    ap.add_argument("--tier", default=",".join(TIERS))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    bad = 0
    for pid in a.places:
        got = run(pid, tuple(a.tier.split(",")), a.sample)
        if a.json:
            print(json.dumps({"place": pid, "lines": got}))
        else:
            from collections import Counter
            c = Counter(k for k, _ in got if k != "note")
            print(f"== {pid}: " + (", ".join(f"{k} {v}" for k, v in sorted(c.items())) or "all agree"))
            for k, line in got:
                print(f"  [{k}] {line}")
        bad += sum(1 for k, _ in got if k not in ("note",))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
