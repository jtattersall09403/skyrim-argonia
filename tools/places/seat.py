"""Seating: the one place that turns a ref's `seat` rule and a ground bundle into its height.

Used by the draft (to measure the source and seat our refs), the studio's /seat endpoint and the build's check.
`python -m tools.places seat <place_id>` re-seats a whole place on the current ground bundle and its land patches;
it rewrites only `pos[2]` of exterior refs and the ground stamp in place.json, and is idempotent.

Seat rule (`ref.seat`): `{mode, dz, on?, foot?}`
  ground  z = lowest ground under the footprint + dz (dz measured the same way in the source)
  above   z = ground at the origin + dz (things that stand off the ground at the source's height)
  water   z = water surface at the origin + dz
  stilts  z = max(ground, water) under the footprint + dz; posts reach the bed
  clear   z = highest ground under the footprint + dz (a raised thing whose underside cleared the ground everywhere)
  on      z = the supporting ref's seated z + dz (`on` is that ref's id in the same space)
  free    z is kept (interiors, markers the source placed in the air)
`foot` is the footprint `[x0, y0, x1, y1]` in the ref's own frame (yaw only), from the model's true geometry
(`model_bounds`), omitted for a point.
"""
from __future__ import annotations

import json
import math
import sys
from array import array
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUNDLES = ROOT / "out" / "places" / "bundles"
PLACES = ROOT / "newworld" / "places"
CELL = 4096.0
STEP = CELL / 32
NO_WATER = -1.0e6


class Ground:
    """Heights and water of one exterior space: a ground or source bundle, plus land patches."""

    def __init__(self, cells: dict[tuple[int, int], list[float]], water: dict[tuple[int, int], float],
                 default_water: float | None = None, sha: str | None = None):
        self.cells = cells          # (cx, cy) -> 33*33 heights, row-major south to north
        self.water_by_cell = water
        self.default_water = default_water
        self.sha = sha
        self.patched: set[tuple[int, int]] = set()

    @classmethod
    def load(cls, bundle_dir: Path | str, space: str = "exterior") -> "Ground":
        bdir = Path(bundle_dir)
        sdir = bdir / "spaces" / space
        meta = json.loads((sdir / "terrain.json").read_text())
        raw = array("f")
        raw.frombytes((sdir / "terrain.f32").read_bytes())
        if sys.byteorder != "little":
            raw.byteswap()
        cells, water = {}, {}
        n = 33 * 33
        for i, c in enumerate(meta["cells"]):
            key = (int(c["cell"][0]), int(c["cell"][1]))
            idx = c.get("heights_index", c.get("index", i))
            if idx is None:
                continue        # a cell without land
            cells[key] = list(raw[int(idx) * n:int(idx) * n + n])
            w = c.get("water")
            w = w.get("height") if isinstance(w, dict) else w
            if w is not None and abs(float(w)) < 1e30:   # 3.4e38: the worldspace's default level
                water[key] = float(w)
        sj = sdir / "space.json"
        dw = None
        if sj.exists():
            dw = (json.loads(sj.read_text()).get("water") or {}).get("default_height")
        sha = None
        bj = bdir / "bundle.json"
        if bj.exists():
            bmeta = json.loads(bj.read_text())
            stamp = bmeta.get("stamp") or {}
            ins = stamp.get("inputs") or {}
            sha = (bmeta.get("esm") or {}).get("sha256") or next(
                (v for k, v in sorted(ins.items()) if k.lower().endswith(".esm")), None)
        return cls(cells, water, dw, sha)

    # --- land patches (land.jsonl rows: {cell:[cx,cy], verts:[[row,col,dz]...]}) ---
    def apply_patches(self, rows: list[dict]) -> None:
        for r in rows:
            key = (int(r["cell"][0]), int(r["cell"][1]))
            h = self.cells.get(key)
            if h is None:
                continue
            for row, col, dz in r["verts"]:
                h[int(row) * 33 + int(col)] += float(dz)
            self.patched.add(key)

    # --- queries ---
    def vertex(self, gx: int, gy: int) -> float | None:
        """Height at global vertex index (gx, gy) = world / 128; shared edges read from either cell."""
        cx, col = divmod(gx, 32)
        cy, row = divmod(gy, 32)
        h = self.cells.get((cx, cy))
        if h is not None:
            return h[row * 33 + col]
        for dcx, dcy in ((-1, 0), (0, -1), (-1, -1)):
            h = self.cells.get((cx + dcx, cy + dcy))
            c2, r2 = col - 32 * dcx, row - 32 * dcy
            if h is not None and c2 <= 32 and r2 <= 32:
                return h[r2 * 33 + c2]
        return None

    def has(self, x: float, y: float) -> bool:
        return (math.floor(x / CELL), math.floor(y / CELL)) in self.cells

    def height(self, x: float, y: float) -> float | None:
        fx, fy = x / STEP, y / STEP
        gx, gy = math.floor(fx), math.floor(fy)
        tx, ty = fx - gx, fy - gy
        v = [self.vertex(gx, gy), self.vertex(gx + 1, gy), self.vertex(gx, gy + 1), self.vertex(gx + 1, gy + 1)]
        if any(a is None for a in v):
            known = [a for a in v if a is not None]
            return sum(known) / len(known) if known else None
        # the land's own triangles: split along the cell quad's diagonal like the game's mesh
        if tx + ty <= 1:
            return v[0] + (v[1] - v[0]) * tx + (v[2] - v[0]) * ty
        return v[3] + (v[2] - v[3]) * (1 - tx) + (v[1] - v[3]) * (1 - ty)

    def water(self, x: float, y: float) -> float | None:
        w = self.water_by_cell.get((math.floor(x / CELL), math.floor(y / CELL)), self.default_water)
        return None if w is None or w <= NO_WATER else w

    def wet(self, x: float, y: float, margin: float = 0.0) -> bool:
        w, h = self.water(x, y), self.height(x, y)
        return w is not None and h is not None and h < w - margin

    def normal(self, x: float, y: float, d: float = STEP) -> tuple[float, float, float]:
        hx0, hx1 = self.height(x - d, y), self.height(x + d, y)
        hy0, hy1 = self.height(x, y - d), self.height(x, y + d)
        if None in (hx0, hx1, hy0, hy1):
            return (0.0, 0.0, 1.0)
        nx, ny, nz = -(hx1 - hx0) / (2 * d), -(hy1 - hy0) / (2 * d), 1.0
        m = math.sqrt(nx * nx + ny * ny + nz * nz)
        return (nx / m, ny / m, nz / m)

    def slope(self, x: float, y: float) -> float:
        """Slope in degrees at a point."""
        return math.degrees(math.acos(max(-1.0, min(1.0, self.normal(x, y)[2]))))

    def at(self, x: float, y: float) -> dict:
        """The /seat endpoint's answer."""
        h = self.height(x, y)
        return {"x": x, "y": y, "ground": h, "water": self.water(x, y), "slope": round(self.slope(x, y), 2),
                "normal": [round(a, 4) for a in self.normal(x, y)], "sha": self.sha}


# --- footprints ---
FOOTPRINTS = ROOT / "out" / "places" / "footprints.json"
_fp: dict | None = None


def model_bounds(base: dict) -> list | None:
    """A base's true extent [[x0, y0, z0], [x1, y1, z1]] in its own frame: the mesh's own geometry (lane A's
    converter), cached per model under out/places/footprints.json; the record's bounds when there is no mesh.
    Bounds need not be centred on the origin: every footprint is taken from this, offsets and all."""
    global _fp
    m = str(base.get("model") or "").lower()
    if not m:
        return base.get("bounds")
    if _fp is None:
        try:
            _fp = json.loads(FOOTPRINTS.read_text())
        except (OSError, ValueError):
            _fp = {}
    if m not in _fp:
        b = None
        try:
            from tools.places import assets
            info = assets.mesh_info(m, bounds=base.get("bounds"))
            if info.get("tris"):
                b = info.get("bounds")
        except Exception:
            b = None
        _fp[m] = b
        try:
            FOOTPRINTS.parent.mkdir(parents=True, exist_ok=True)
            FOOTPRINTS.write_text(json.dumps(_fp, sort_keys=True))
        except OSError:
            pass
    return _fp[m] or base.get("bounds")


def foot_box(foot) -> tuple[float, float, float, float]:
    """A seat rule's footprint as (x0, y0, x1, y1) in the ref's frame; the older [hx, hy] form is centred."""
    if len(foot) == 2:
        return (-foot[0], -foot[1], foot[0], foot[1])
    return tuple(foot)


def foot_radius(foot) -> float:
    x0, y0, x1, y1 = foot_box(foot)
    return max(math.hypot(x, y) for x in (x0, x1) for y in (y0, y1))


def foot_area(foot) -> float:
    x0, y0, x1, y1 = foot_box(foot)
    return (x1 - x0) * (y1 - y0)


def to_local(x: float, y: float, rz: float, px: float, py: float) -> tuple[float, float]:
    """A world point in a ref's frame (the inverse of its clockwise yaw)."""
    c, s = math.cos(rz), math.sin(rz)
    dx, dy = px - x, py - y
    return (dx * c - dy * s, dx * s + dy * c)


def foot_points(x: float, y: float, rz: float, foot: list[float] | None, n: int = 3) -> list[tuple[float, float]]:
    """Sample points over a footprint (n x n grid incl. corners) at its true place in the ref's frame, yaw only;
    the origin when foot is None."""
    if not foot:
        return [(x, y)]
    x0, y0, x1, y1 = foot_box(foot)
    c, s = math.cos(rz), math.sin(rz)
    pts = []
    for i in range(n):
        for j in range(n):
            u = x0 + (x1 - x0) * i / (n - 1)
            v = y0 + (y1 - y0) * j / (n - 1)
            # Skyrim's yaw turns clockwise seen from above
            pts.append((x + u * c + v * s, y - u * s + v * c))
    return pts


def foot_ground(g: Ground, x: float, y: float, rz: float, foot, stilts: bool = False) -> float | None:
    hs = []
    for px, py in foot_points(x, y, rz, foot, 5):
        h = g.height(px, py)
        if h is None:
            continue
        if stilts:
            w = g.water(px, py)
            h = max(h, w) if w is not None else h
        hs.append(h)
    return min(hs) if hs else None


def foot_high(g: Ground, x: float, y: float, rz: float, foot) -> float | None:
    hs = [h for h in (g.height(px, py) for px, py in foot_points(x, y, rz, foot, 5)) if h is not None]
    return max(hs) if hs else None


def foot_relief(g: Ground, x: float, y: float, rz: float, foot) -> float:
    hs = [h for h in (g.height(px, py) for px, py in foot_points(x, y, rz, foot, 5)) if h is not None]
    return (max(hs) - min(hs)) if hs else 0.0


def reference_z(g: Ground, mode: str, x: float, y: float, rz: float, foot, on_z: float | None = None) -> float | None:
    """The height a seat rule measures from (dz is added to this)."""
    if mode == "ground":
        return foot_ground(g, x, y, rz, foot)
    if mode == "above":
        return g.height(x, y)
    if mode == "clear":
        return foot_high(g, x, y, rz, foot)
    if mode == "water":
        w = g.water(x, y)
        return w if w is not None else g.height(x, y)
    if mode == "stilts":
        return foot_ground(g, x, y, rz, foot, stilts=True)
    if mode == "on":
        return on_z
    return None


def seat_z(ref: dict, g: Ground, placed: dict[str, dict] | None = None) -> float:
    """The seated z of one ref; `placed` maps ids to already-seated refs of the same space (for mode `on`)."""
    s = ref.get("seat") or {"mode": "free"}
    mode = s.get("mode", "free")
    x, y, z = ref["pos"]
    if mode == "free":
        return z
    on_z = None
    if mode == "on":
        sup = (placed or {}).get(s.get("on"))
        if sup is None:
            return z
        on_z = sup["pos"][2]
    base = reference_z(g, mode, x, y, ref.get("rot", [0, 0, 0])[2], s.get("foot"), on_z)
    if base is None:
        return z
    return round(base + float(s.get("dz", 0.0)), 3)


def seat_all(refs: list[dict], g: Ground) -> int:
    """Seat refs in dependency order (supporters first); returns how many z values changed."""
    by_id = {r["id"]: r for r in refs}
    done: dict[str, dict] = {}
    changed = 0

    def visit(r, stack=()):
        nonlocal changed
        if r["id"] in done:
            return
        on = (r.get("seat") or {}).get("on")
        if on and on in by_id and on not in stack:
            visit(by_id[on], stack + (r["id"],))
        z = seat_z(r, g, done)
        if abs(z - r["pos"][2]) > 1e-3:
            changed += 1
            r["pos"][2] = z
        done[r["id"]] = r

    for r in refs:
        visit(r)
    return changed


# --- place files ---
def read_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def write_jsonl(p: Path, rows: list[dict]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r, separators=(",", ":"), ensure_ascii=False) + "\n" for r in rows))


def ground_for(place_id: str, bundles: Path = BUNDLES, places: Path = PLACES) -> Ground:
    g = Ground.load(bundles / f"ground.{place_id}")
    g.apply_patches(read_jsonl(places / place_id / "land.jsonl"))
    return g


def reseat_place(place_id: str, bundles: Path = BUNDLES, places: Path = PLACES) -> int:
    g = ground_for(place_id, bundles, places)
    pdir = places / place_id
    p = pdir / "spaces" / "exterior" / "refs.jsonl"
    refs = read_jsonl(p)
    n = seat_all(refs, g)
    write_jsonl(p, sorted(refs, key=lambda r: r["id"]))
    pj = pdir / "place.json"
    if pj.exists():
        place = json.loads(pj.read_text())
        if place.get("ground", {}).get("sha") != g.sha:
            place.setdefault("ground", {})["sha"] = g.sha
            pj.write_text(json.dumps(place, indent=1, ensure_ascii=False) + "\n")
    return n


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python -m tools.places seat <place_id>", file=sys.stderr)
        return 2
    n = reseat_place(argv[0])
    print(f"seat {argv[0]}: {n} refs moved")
    return 0
