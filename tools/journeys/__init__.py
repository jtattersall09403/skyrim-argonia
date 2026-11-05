"""Journeys derived from the build they run on (1.15-r4-journeys).

A data-driven journey's stands (where the player is put) and vantages (where a still is taken from) are numbers of
the build: the game's ground (the LAND heights, every layer applied), the cells' water levels (out/water/cells.jsonl),
the placed refs (build_ref through db.py) and the placement shards (out/terrain/vegetation). The build moves under the
journeys every round, so they are re-derived every time (`python3 -m tools.journeys refresh`) and checked at L1
(`python3 -m tools.journeys check`, tools/tests/test_journeys.py) before any machine time:

- every `player.setpos` stand stands on the ground within TOL_M (or in water the step says is water: `# water`);
- every `player.moveto <ref> [dx dy dz]` target off the ground-placed refs is dry;
- every still's eye line (EYE_HEIGHT_UNITS over the feet, to the subject) keeps CLEAR_M off any placed foliage
  (`frame`, at refresh, moves the stand along the approach line until it does: round 4's first batch framed 14 stills
  inside leaves).

A step names its subject with a `# subject: x y z` comment (units); without one the subject is where the eye line meets
the ground (pitch down), or SUBJECT_M ahead at eye height (a level view).
"""
from __future__ import annotations

import gzip
import json
import math
import re
from pathlib import Path

from tools.argonia_world import skyrim_units as su
from tools.journeys.measures import along, around, memo

ROOT = Path(__file__).resolve().parents[2]
JOURNEYS = ROOT / "tests" / "journeys"
SCENES = ROOT / "tests" / "scenes"
TOL_M = 0.5            # the brief's: a stand within 0.5 m of the ground
SEAT_U = 16.0          # the feet put this far over the ground (0.23 m): inside TOL_M, the engine settles him
CLEAR_M = 2.0          # no foliage within 2 m of the eye line (horizontally)
RAY_NEAR_M, RAY_GROUND_M = 2.0, 0.3   # the eye ray meets nothing within 2 m; the ground within 0.3 m of the ray is a hit
OVER_M = 0.5           # and the line passes a plant's top (or under a crown) by at least this
STEP_M, BACK_M, NEAR_M = 2.0, 30.0, 2.0   # the approach-line search: 2 m steps, up to 30 m back, never nearer than 2 m
SUBJECT_M = 15.0       # a level view's subject distance
SUBJECT_FREE_M = 2.0   # foliage this near the subject is the subject's own (the tree seated, the creature's reeds)
NOT_FOLIAGE = ("rock",)
TRUNKED = ("canopy", "emergent", "palm", "mangrove", "gallery", "cliff-tree", "deadwood")  # leaves only up top
CROWN_FROM, TRUNK_U = 0.4, 25.0   # a tree's crown from 0.4 of its height up; below it a trunk ~0.35 m round
# The data-driven journeys: refresh re-derives them, the L1 test checks them.
DERIVED = ("world-panel", "river-steps", "water-types", "road-look", "claywater-walk", "claywater-look", "creature-spots", "tree-seat",
           "rock-booth", "creatures-kinds", "sky-ab", "bridge-look", "junction-dry",
           "grade-ab")

SETPOS = re.compile(r"player\.setpos ([xyz]) (-?\d+(?:\.\d+)?)")
SETANGLE = re.compile(r"player\.setangle ([xz]) (-?\d+(?:\.\d+)?)")
MOVETO = re.compile(r"player\.moveto (ARG_Ref_\w+)((?: -?\d+(?:\.\d+)?){3})?")
SUBJECT = re.compile(r"#\s*subject:\s*(-?[\d.]+) (-?[\d.]+) (-?[\d.]+)")
STEP = re.compile(r"^\s*-\s+name:\s*(\S+)|^\s*\{?\s*\"name\":\s*\"([^\"]+)\"")


DRY_FOOTING_M = 0.5     # a stand's ground is at least this far above the cell water level (else it is not dry)


class Build:
    """The current build's ground, water, foliage and refs, loaded lazily (ground 2 s; the DB ~13 s, only for refs)."""

    def __init__(self, ground=None, water=None, foliage=None, refs=None, statics=None):
        self._ground, self._water, self._foliage, self._refs = ground, water, foliage, refs
        self._statics = statics
        self.real = ground is None and water is None and foliage is None and refs is None   # only the real build's measures are cached

    # -- the ground and the water ------------------------------------------------------------------------------------
    @property
    def ground(self):
        if self._ground is None:
            from tools.world_sample import Ground
            self._ground = Ground().H
        return self._ground

    def ground_u(self, x: float, y: float) -> float:
        """The game's ground at a worldspace point, units (bilinear over the LAND vertices)."""
        H = self.ground
        n = H.shape[0] - 1
        xm, ym = su.skyrim_to_province(x, y)
        c, r = xm / su.PROVINCE_SAMPLE_M, ym / su.PROVINCE_SAMPLE_M
        r0, c0 = min(max(int(math.floor(r)), 0), n - 1), min(max(int(math.floor(c)), 0), n - 1)
        fr, fc = min(max(r - r0, 0.0), 1.0), min(max(c - c0, 0.0), 1.0)
        h = (H[r0, c0] * (1 - fr) * (1 - fc) + H[r0, c0 + 1] * (1 - fr) * fc + H[r0 + 1, c0] * fr * (1 - fc)
             + H[r0 + 1, c0 + 1] * fr * fc)
        return su.metres_to_units(float(h))

    @property
    def water(self) -> dict:
        if self._water is None:
            self._water = {}
            with open(ROOT / "out" / "water" / "cells.jsonl") as f:
                for ln in f:
                    d = json.loads(ln)
                    self._water[(d["x"], d["y"])] = float(d["waterHeight"])
        return self._water

    def water_u(self, x: float, y: float) -> float | None:
        return self.water.get(su.cell_of(x, y))

    def wet(self, x: float, y: float) -> bool:
        lv = self.water_u(x, y)
        return lv is not None and self.ground_u(x, y) < lv

    def margin_u(self, x: float, y: float) -> float | None:
        """Ground minus the cell's water level, units (None where the cell holds no water)."""
        lv = self.water_u(x, y)
        return None if lv is None else self.ground_u(x, y) - lv

    def soaked(self, x: float, y: float) -> bool:
        """Not dry footing: the ground is under the cell's water or within DRY_FOOTING_M of it. A stand with its feet that
        close to the water level is a wade or a swim to the engine (no first person); the eye 1.7 m up proves nothing."""
        m = self.margin_u(x, y)
        return m is not None and m < su.metres_to_units(DRY_FOOTING_M)

    # -- foliage -----------------------------------------------------------------------------------------------------
    def foliage_near(self, x: float, y: float, reach_u: float) -> list[tuple]:
        """(x, y, z, radius, height) units of every placed plant (not rock) within reach_u of a point."""
        if self._foliage is None:
            self._foliage = {}
        cx, cy = su.cell_of(x, y)
        k = int(reach_u // su.CELL_UNITS) + 1
        out = []
        for i in range(cx - k, cx + k + 1):
            for j in range(cy - k, cy + k + 1):
                for f in self._cell_foliage(i, j):
                    if math.hypot(f[0] - x, f[1] - y) <= reach_u + f[3]:
                        out.append(f)
        return out

    def _cell_foliage(self, cx: int, cy: int) -> list[tuple]:
        if (cx, cy) not in self._foliage:
            self._load_row(cy)
        return self._foliage.get((cx, cy), [])

    def _load_row(self, cy: int):
        shapes = self.shapes()
        p = ROOT / "out" / "terrain" / "vegetation" / f"cy{cy:+04d}.jsonl.gz"
        row = {}
        if p.is_file():
            with gzip.open(p, "rt", encoding="ascii") as f:
                for ln in f:
                    c = json.loads(ln)
                    fs = []
                    for r in c["refs"]:
                        s = shapes.get(c["bases"][r[1]])
                        if s:   # the 7th: the OBND bottom under the pivot (the seat sinks the pivot; z0 is the mesh's own)
                            fs.append((r[2], r[3], r[4], s[0] * r[8], s[1] * r[8], s[2], s[3] * r[8]))
                    row[(c["x"], c["y"])] = fs
        for cx in range(-200, 200):
            self._foliage.setdefault((cx, cy), row.get((cx, cy), []))

    _shapes = None

    def shapes(self) -> dict:
        """form key -> (horizontal radius, height, bushy, OBND bottom z) units of each placed plant form, from its bounds (object_form)."""
        if Build._shapes is None:
            from tools.argonia_world import db
            Build._shapes = {r["form_key"]: (max(1.0, abs(r["bound_x0"] or 0), abs(r["bound_x1"] or 0),
                                                 abs(r["bound_y0"] or 0), abs(r["bound_y1"] or 0)),
                                             max(1.0, (r["bound_z1"] or 0) - (r["bound_z0"] or 0)),
                                             r["role_id"] not in TRUNKED, r["bound_z0"] or 0.0)
                             for r in db.open().query("SELECT form_key, role_id, bound_x0, bound_x1, bound_y0, bound_y1, "
                                                      "bound_z0, bound_z1 FROM object_form")
                             if r["role_id"] not in NOT_FOLIAGE}
            from tools.journeys import canopy
            Build._shapes = canopy.reach(Build._shapes, canopy.load())   # fronds hung past the OBND (data/canopy-radius.json)
        return Build._shapes

    # -- placed refs -------------------------------------------------------------------------------------------------
    def ref(self, edid: str) -> dict | None:
        """A placed exterior ref by editor id: its worldspace x, y, z (units) and whether its z is its own (a porch,
        a deck) or the ground's."""
        if self._refs is None:
            from tools.argonia_world import db
            from tools.argonia_world.place_build import ref_edid
            w = db.open()
            ext = {r["id"] for r in w.query("SELECT id FROM build_cell WHERE kind = 'exterior'")}
            self._refs = {}
            for r in w.query("SELECT id, cell_id, x_m, y_m, z_m, z_over_m FROM build_ref"):
                if r["cell_id"] not in ext:  # an interior's ref: no province ground under it
                    self._refs[ref_edid(r["id"])] = {"id": r["id"], "interior": True}
                    continue
                x, y = su.province_to_skyrim(r["x_m"], r["y_m"])
                own = r["z_m"] is not None
                # a studio marker (the panel's, the probes') stands on the ground it was put over: its z is checked
                self._refs[ref_edid(r["id"])] = {"id": r["id"], "x": x, "y": y, "own_z": own,
                                                 "marker": r["cell_id"].startswith("cell.studio."),
                                                 "z": su.metres_to_units(r["z_m"]) if own else None,
                                                 "over": r["z_over_m"]}
        return self._refs.get(edid)

    # -- placed statics (lane 1.15-r6-claywater-look-derived) --------------------------------------------------------
    def statics(self) -> list[dict]:
        """Every placed exterior static's box (units): {edid, x0, y0, z0, x1, y1, z1}. The box is the AABB of the
        collision triangles (out/navmesh/province/in/objects.f32: navmesh/placed.py read each piece's own Havok
        collision on the machine that has the meshes) nearest that ref (STATIC_ASSIGN_M), at the ref's current xy
        from the DB; a piece with no collision (a candle, a reed) has no box, as in game."""
        if self._statics is None:
            self._statics = static_boxes(static_refs(), OBJECTS)
        return self._statics

    # -- the eye line ------------------------------------------------------------------------------------------------
    def blockers(self, eye: tuple, subj: tuple) -> list[tuple]:
        """The plants within CLEAR_M of the eye line (eye -> subject), the subject's own excepted."""
        ex, ey, ez = eye
        sx, sy, sz = subj
        dx, dy = sx - ex, sy - ey
        L2 = dx * dx + dy * dy
        clear, over = CLEAR_M * su.UNITS_PER_METRE, OVER_M * su.UNITS_PER_METRE
        free = SUBJECT_FREE_M * su.UNITS_PER_METRE
        mid = ((ex + sx) / 2, (ey + sy) / 2)
        out = []
        for f in self.foliage_near(mid[0], mid[1], math.sqrt(L2) / 2 + clear):
            fx, fy, fz, fr, fh, bushy = f[:6]
            if math.hypot(fx - sx, fy - sy) <= free:
                continue
            t = 0.0 if L2 == 0 else ((fx - ex) * dx + (fy - ey) * dy) / L2
            if t < 0 and math.hypot(fx - ex, fy - ey) > fr:
                continue  # behind the eye and not round it: out of the still
            t = min(max(t, 0.0), 1.0)
            d = math.hypot(ex + t * dx - fx, ey + t * dy - fy)
            zl = ez + t * (sz - ez)
            # the plant as one cylinder (a shrub, a fern) or a trunk under a crown: the 3-D gap to the nearer part
            parts = [(fr, fz, fz + fh)] if bushy else [(min(fr, TRUNK_U), fz, fz + CROWN_FROM * fh),
                                                         (fr, fz + CROWN_FROM * fh, fz + fh)]
            # 2 m round the line, 0.5 m over a top: a fern a metre under the eye line is ground in the still's lower half,
            # not leaves on the lens (the first pass's 14 stills were framed inside crowns and fronds)
            if any(d - r < clear and lo - over <= zl <= hi + over for r, lo, hi in parts):
                out.append(f)
        return out


@memo("eye_hits", reach=lambda eye, subj: around(eye[0], eye[1], RAY_NEAR_M + 2.0))
def _eye_hits(b: Build, eye: tuple, subj: tuple) -> list[str]:
    """What the eye ray meets within RAY_NEAR_M of the eye: the ground rising to it, or a plant's trunk or leaves (3-D
    distance from the ray's near stretch, the eye's own point included: a stand inside a trunk)."""
    u = su.UNITS_PER_METRE
    ex, ey, ez = eye
    dx, dy, dz = subj[0] - ex, subj[1] - ey, subj[2] - ez
    L = math.sqrt(dx * dx + dy * dy + dz * dz) or 1.0
    ux, uy, uz = dx / L, dy / L, dz / L
    why = []
    for k in range(0, int(RAY_NEAR_M * 2) + 1):
        t = min(k * 0.5 * u, L)
        if b.ground_u(ex + ux * t, ey + uy * t) + RAY_GROUND_M * u >= ez + uz * t:
            why.append(f"ground at {k * 0.5:.1f} m")
            break
    reach = RAY_NEAR_M * u
    for f_ in b.foliage_near(ex, ey, reach + 2 * u):
        fx, fy, fz, fr, fh, bushy = f_[:6]
        parts = [(fr, fz, fz + fh)] if bushy else [(min(fr, TRUNK_U), fz, fz + CROWN_FROM * fh), (fr, fz + CROWN_FROM * fh, fz + fh)]
        for r, lo, hi in parts:
            for k in range(0, int(RAY_NEAR_M * 2) + 1):
                t = min(k * 0.5 * u, L)
                px, py, pz = ex + ux * t, ey + uy * t, ez + uz * t
                if math.hypot(px - fx, py - fy) < r and lo <= pz <= hi:
                    why.append(f"plant at {k * 0.5:.1f} m")
                    break
            else:
                continue
            break
        if len(why) > 1:
            break
    return why


CLEAR_LINE_M, CANOPY_M = 60.0, 10.0   # the clearance measure: the eye line to 60 m, the canopy within 10 m of the eye


@memo("clearance", dec=tuple, reach=lambda eye, heading, line_m, canopy_m: along(eye[0], eye[1], heading, line_m, canopy_m))
def clearance(b: Build, eye: tuple, heading: float, line_m: float = CLEAR_LINE_M, canopy_m: float = CANOPY_M) -> tuple[int, int]:
    """(line, canopy): the plant volumes crossing the level eye line along `heading` out to line_m, and the plant volumes
    over the eye within canopy_m above it (footprint over the eye point, reaching from under eye + canopy_m to over the eye). Each plant is its whole OBND volume, no trunk
    exemption: a cylinder of its widest half-extent from pivot + z0 to pivot + z0 + height (the pivot already carries
    the seat), scaled. Round 5's sea stand stood under a leaf canopy and its river and corridor stands inside willow
    fronds while the trunk-and-crown model (blockers) read them clear; this one reads them as hits."""
    u = su.UNITS_PER_METRE
    ex, ey, ez = eye
    a = math.radians(heading)
    dx, dy = math.sin(a) * line_m * u, math.cos(a) * line_m * u
    L2 = dx * dx + dy * dy
    line = canopy = 0
    for f in b.foliage_near(ex + dx / 2, ey + dy / 2, line_m * u / 2):
        fx, fy, fz, fr, fh = f[:5]
        lo = fz + (f[6] if len(f) > 6 else 0.0)
        hi = lo + fh
        dh = math.hypot(fx - ex, fy - ey)
        if dh < fr and hi > ez and lo < ez + canopy_m * u:
            canopy += 1
            continue
        t = min(max(((fx - ex) * dx + (fy - ey) * dy) / L2, 0.0), 1.0)
        if math.hypot(ex + t * dx - fx, ey + t * dy - fy) < fr and lo <= ez <= hi:
            line += 1
    return line, canopy


TALL_REACH_M, TALL_OFF_M, TALL_M = 15.0, 4.0, 1.0   # the river stand's near field: nothing over 1 m within 4 m of the line to 15 m


def tall_near(b: Build, eye: tuple, heading: float, reach_m: float = TALL_REACH_M, off_m: float = TALL_OFF_M,
              tall_m: float = TALL_M) -> int:
    """The plants whose volume (canopy-widened radius) comes within off_m of the eye line's footprint out to reach_m
    and whose top stands more than tall_m over the ground at its pivot (lane 1.15-r6-water-stands-5: the river stand's
    s0 looked through a palm's fronds 0.5 m off the line)."""
    u = su.UNITS_PER_METRE
    ex, ey = eye[0], eye[1]
    a = math.radians(heading)
    dx, dy = math.sin(a) * reach_m * u, math.cos(a) * reach_m * u
    L2 = dx * dx + dy * dy
    n = 0
    for f in b.foliage_near(ex + dx / 2, ey + dy / 2, reach_m * u / 2 + off_m * u):
        fx, fy, fz, fr, fh = f[:5]
        top = fz + (f[6] if len(f) > 6 else 0.0) + fh
        t = min(max(((fx - ex) * dx + (fy - ey) * dy) / L2, 0.0), 1.0)
        if math.hypot(ex + t * dx - fx, ey + t * dy - fy) - fr < off_m * u and top - b.ground_u(fx, fy) > tall_m * u:
            n += 1
    return n


def far_bank_m(b: Build, x: float, y: float, heading: float, limit_m: float = 60.0, step_m: float = 0.5) -> float | None:
    """The footprint along `heading` from (x, y): the distance to the first dry sample past the water (the far bank),
    or None when the line meets no water, or no far bank, within limit_m."""
    u = su.UNITS_PER_METRE
    sx, sy = math.sin(math.radians(heading)), math.cos(math.radians(heading))
    seen = False
    for k in range(1, int(limit_m / step_m) + 1):
        w = b.wet(x + sx * k * step_m * u, y + sy * k * step_m * u)
        if w:
            seen = True
        elif seen:
            return k * step_m
    return None


@memo("ground_slope_deg", reach=lambda x, y: around(x, y, 4.0))
def ground_slope_deg(b: Build, x: float, y: float) -> float:
    """The ground's steepest slope at a point, degrees, over a LAND quad either side (VERTEX_SPACING_UNITS)."""
    h = su.VERTEX_SPACING_UNITS
    gx = (b.ground_u(x + h, y) - b.ground_u(x - h, y)) / (2 * h)
    gy = (b.ground_u(x, y + h) - b.ground_u(x, y - h)) / (2 * h)
    return math.degrees(math.atan(math.hypot(gx, gy)))


@memo("stand_bad", reach=lambda x, y, subj: around(x, y, RAY_NEAR_M + 4.0))
def stand_bad(b: Build, x: float, y: float, subj: tuple) -> list[str]:
    """Why a stand fails: the eye ray meets geometry within RAY_NEAR_M, or the ground is too steep to stand on."""
    why = _eye_hits(b, eye_of(b, x, y), subj)
    if (s := ground_slope_deg(b, x, y)) > su.STAND_SLOPE_MAX_DEG:
        why.append(f"slope {s:.0f} deg")
    return why


def eye_of(b: Build, x: float, y: float) -> tuple[float, float, float]:
    return x, y, b.ground_u(x, y) + SEAT_U + su.EYE_HEIGHT_UNITS


def subject_of(b: Build, x: float, y: float, heading: float, pitch: float) -> tuple[float, float, float]:
    """Where the step looks: the eye line's meeting with the ground (pitch down), else SUBJECT_M ahead, level."""
    ex, ey, ez = eye_of(b, x, y)
    sx, sy = math.sin(math.radians(heading)), math.cos(math.radians(heading))
    if pitch > 3:
        d = min(max((ez - b.ground_u(x, y)) / math.tan(math.radians(pitch)), NEAR_M * su.UNITS_PER_METRE),
                40 * su.UNITS_PER_METRE)
        return ex + sx * d, ey + sy * d, ez - d * math.tan(math.radians(pitch))
    d = SUBJECT_M * su.UNITS_PER_METRE
    return ex + sx * d, ey + sy * d, ez - d * math.tan(math.radians(pitch))


def aim(eye: tuple, subj: tuple) -> tuple[float, float]:
    """(heading, pitch down) degrees from the eye to the subject: Skyrim's 0 = north, clockwise; x positive = down."""
    dx, dy = subj[0] - eye[0], subj[1] - eye[1]
    h = math.degrees(math.atan2(dx, dy)) % 360
    p = math.degrees(math.atan2(eye[2] - subj[2], max(math.hypot(dx, dy), 1.0)))
    return h, max(-60.0, min(60.0, p))


def stand_near(b: Build, x: float, y: float, heading: float, reach_m: float = 16.0, water: bool = False) -> dict | None:
    """The nearest stand to (x, y), on a 2 m grid out to reach_m, that is dry, stands on ground the player can stand on and
    whose level eye ray along `heading` (degrees) meets nothing within RAY_NEAR_M and no plant on the line; None if none."""
    u = su.UNITS_PER_METRE
    a = math.radians(heading)
    d = SUBJECT_M * u
    n = int(reach_m / 2)
    cands = sorted(((i, j) for i in range(-n, n + 1) for j in range(-n, n + 1)), key=lambda c: c[0] ** 2 + c[1] ** 2)
    for i, j in cands:
        if math.hypot(i, j) * 2 > reach_m:
            break
        px, py = x + i * 2 * u, y + j * 2 * u
        if not water and b.wet(px, py):
            continue
        ex, ey, ez = eye_of(b, px, py)
        subj = (ex + math.sin(a) * d, ey + math.cos(a) * d, ez)
        if not stand_bad(b, px, py, subj) and not b.blockers((ex, ey, ez), subj):
            return {"x": px, "y": py, "moved_m": round(math.hypot(i, j) * 2, 1)}
    return None


def frame(b: Build, x: float, y: float, subj: tuple, water: bool = False, band: tuple | None = None) -> dict:
    """The stand on the approach line (subject -> stand) nearest the given one, dry (unless `water`) and with a clear
    eye line: first the given distance, then back STEP_M at a time up to BACK_M, then nearer down to NEAR_M. With
    `band` (lo, hi metres) only stands in the band are tried, the nearest to the given distance first."""
    sx, sy = subj[0], subj[1]
    d0 = math.hypot(x - sx, y - sy)
    ux, uy = ((x - sx) / d0, (y - sy) / d0) if d0 > 1 else (0.0, -1.0)
    u = su.UNITS_PER_METRE
    ds = [d0] + [d0 + k * STEP_M * u for k in range(1, int(BACK_M / STEP_M) + 1)]
    ds += [d0 - k * STEP_M * u for k in range(1, int(d0 / (STEP_M * u)) + 1) if d0 - k * STEP_M * u >= NEAR_M * u - 1]
    if band:
        ds = sorted((v * u for v in range(int(band[0]), int(band[1]) + 1)), key=lambda d: abs(d - d0))
    first, best = None, None
    for d in ds:
        px, py = sx + ux * d, sy + uy * d
        dry = water or not b.wet(px, py)
        n = len(b.blockers(eye_of(b, px, py), subj)) + len(stand_bad(b, px, py, subj))
        if first is None:
            first = {"wet": not dry, "blockers": n}
        if dry and n == 0:
            return {"x": px, "y": py, "moved_m": round(abs(d - d0) / u, 1), "why": _why(first), "clear": True,
                    "blockers": 0, "dry": True}
        k = (not dry, n, abs(d - d0))
        if best is None or k < best[0]:
            best = (k, px, py, d, n, dry)
    _, px, py, d, n, dry = best  # none clear: the dry stand with the fewest plants on the line, nearest the given
    return {"x": px, "y": py, "moved_m": round(abs(d - d0) / u, 1), "why": _why(first), "clear": False,
            "blockers": n, "dry": dry}


def _why(first: dict) -> str:
    return ", ".join(w for w in ("in water" if first["wet"] else "", f"{first['blockers']} plants on the eye line"
                                 if first["blockers"] else "") if w) or "clear"


def place(b: Build, subj: tuple, d0_u: float, bearings, band: tuple | None = None) -> dict:
    """A stand d0_u off the subject on the first bearing (degrees, Skyrim: the stand's bearing from the subject) whose
    approach line gives a dry stand with a clear eye line; else the first dry one; else the first bearing's."""
    tried = []
    for brg in bearings:
        x = subj[0] + math.sin(math.radians(brg)) * d0_u
        y = subj[1] + math.cos(math.radians(brg)) * d0_u
        f = frame(b, x, y, subj, band=band)
        f["bearing"] = brg
        if f["clear"]:
            return f
        tried.append(f)
    return min(tried, key=lambda f: (not f["dry"], f["blockers"]))  # the dry one with the fewest plants on the line


# -- the placed-static clearance (lane 1.15-r6-claywater-look-derived) -------------------------------------------------
# r6-chain23's Claywater stills stood inside the station's walls (a frame of one clay texture, the camera under a floor):
# the plant measure knows only foliage. A stand keeps STATIC_CLEAR_M off every placed static's box and its eye line
# meets no static within STATIC_AIM_M.
OBJECTS = ROOT / "out" / "navmesh" / "province" / "in" / "objects.f32"
STATIC_CLEAR_M, STATIC_AIM_M = 1.5, 3.0
STATIC_ASSIGN_M = 15.0     # a collision triangle belongs to the nearest placed static within this
NOT_STATIC = ("000034:Skyrim.esm",)    # the XMarker (markers have no body)
NOT_STATIC_PREFIX = ("ARG_Npc_", "ARG_Misc_", "ARG_Book_")   # people, creatures and loose items move


def static_refs() -> list[dict]:
    """The placed exterior statics (not markers, actors or loose items): edid, x, y (units)."""
    from tools.argonia_world import db
    from tools.argonia_world.place_build import ref_edid
    w = db.open()
    out = []
    for r in w.query("SELECT r.id, r.x_m, r.y_m, r.base FROM build_ref r JOIN build_cell c ON c.id = r.cell_id "
                     "WHERE c.kind = 'exterior' AND r.npc_id IS NULL AND COALESCE(r.actor, 0) = 0 "
                     "AND COALESCE(r.disabled, 0) = 0"):
        b = r["base"] or ""
        if b in NOT_STATIC or b.startswith(NOT_STATIC_PREFIX):
            continue
        x, y = su.province_to_skyrim(r["x_m"], r["y_m"])
        out.append({"edid": ref_edid(r["id"]), "x": x, "y": y})
    return out


def static_boxes(refs: list[dict], objects) -> list[dict]:
    """Each ref's box from the collision triangles nearest it (within STATIC_ASSIGN_M); objects: a path to the
    (n, 3, 3) float32 triangles, or the array. Refs that get no triangle are left out."""
    import numpy as np
    if not refs:
        return []
    if not isinstance(objects, np.ndarray):
        if not Path(objects).is_file():
            return []
        objects = np.fromfile(objects, np.float32).reshape(-1, 3, 3)
    c = objects.mean(axis=1)[:, :2]
    rx = np.array([[r["x"], r["y"]] for r in refs])
    near = np.full(len(c), -1)
    best = np.full(len(c), STATIC_ASSIGN_M * su.UNITS_PER_METRE)
    for i in range(0, len(rx), 256):
        d = np.hypot(c[:, None, 0] - rx[None, i:i + 256, 0], c[:, None, 1] - rx[None, i:i + 256, 1])
        k = d.argmin(axis=1)
        dk = d[np.arange(len(c)), k]
        hit = dk < best
        best[hit], near[hit] = dk[hit], k[hit] + i
    out = []
    for i in np.unique(near[near >= 0]):
        t = objects[near == i].reshape(-1, 3)
        lo, hi = t.min(axis=0), t.max(axis=0)
        out.append({"edid": refs[i]["edid"], "x0": float(lo[0]), "y0": float(lo[1]), "z0": float(lo[2]),
                    "x1": float(hi[0]), "y1": float(hi[1]), "z1": float(hi[2])})
    return out


def box_dist_u(bx: dict, x: float, y: float) -> float:
    """The horizontal distance from a point to a box (0 inside)."""
    return math.hypot(max(bx["x0"] - x, 0.0, x - bx["x1"]), max(bx["y0"] - y, 0.0, y - bx["y1"]))


def _in_box(bx: dict, p: tuple, pad_u: float = 0.0) -> bool:
    return (bx["x0"] - pad_u <= p[0] <= bx["x1"] + pad_u and bx["y0"] - pad_u <= p[1] <= bx["y1"] + pad_u
            and bx["z0"] - pad_u <= p[2] <= bx["z1"] + pad_u)


def static_hits(b: Build, x: float, y: float, subj: tuple, own: tuple = ()) -> dict:
    """The placed-static measure of a stand looking at `subj`: `stand`, the statics whose box (grown STATIC_CLEAR_M)
    the body (feet to eye) stands in; `aim`, those the eye line enters within STATIC_AIM_M of the eye; `line`, those it
    crosses further on before the subject (the subject's own boxes, edids in `own`, and any box within 1 m of the subject
    excepted)."""
    u = su.UNITS_PER_METRE
    eye = eye_of(b, x, y)
    feet = eye[2] - su.EYE_HEIGHT_UNITS
    clear = STATIC_CLEAR_M * u
    L = math.dist(eye, subj) or 1.0
    reach = L + clear
    stand, aim_, line = [], [], []
    for bx in b.statics():
        if bx["edid"] in own or box_dist_u(bx, x, y) > reach or _in_box(bx, subj, u):
            continue   # the subject's own, out of reach, or what the subject stands on or in (the poler's deck)
        if box_dist_u(bx, x, y) <= clear and bx["z0"] - clear <= eye[2] and bx["z1"] + clear >= feet:
            stand.append(bx["edid"])
            continue
        for k in range(1, int(L / (0.25 * u)) + 1):
            t = k * 0.25 * u
            p = tuple(eye[i] + (subj[i] - eye[i]) * t / L for i in range(3))
            if _in_box(bx, p):
                (aim_ if t <= STATIC_AIM_M * u else line).append(bx["edid"])
                break
    return {"stand": stand, "aim": aim_, "line": line}


# -- the journey text ------------------------------------------------------------------------------------------------
def steps_of(text: str) -> list[tuple[str, int, int]]:
    """(name, first line, end line) of each step block."""
    lines = text.splitlines()
    starts = [(i, m.group(1) or m.group(2)) for i, ln in enumerate(lines) if (m := STEP.match(ln))]
    return [(n, i, starts[k + 1][0] if k + 1 < len(starts) else len(lines)) for k, (i, n) in enumerate(starts)]


def stands(text: str) -> list[dict]:
    """Every stand a journey puts the player at: setpos triples and moveto targets, per step."""
    lines = text.splitlines()
    out = []
    for name, a, z in steps_of(text):
        blk = "\n".join(lines[a:z])
        pos = {k: float(v) for k, v in SETPOS.findall(blk)}
        if {"x", "y"} <= set(pos):
            out.append({"step": name, "kind": "setpos", "x": pos["x"], "y": pos["y"], "z": pos.get("z"),
                        "water": "# water" in blk, "deck": "# deck" in blk})
        for ref, off in MOVETO.findall(blk):
            o = [float(v) for v in off.split()] if off else [0.0, 0.0, 0.0]
            out.append({"step": name, "kind": "moveto", "ref": ref, "off": o, "water": "# water" in blk})
    return out


def scene_stands(scene: str) -> list[dict]:
    p = SCENES / f"{scene}.txt"
    if not p.is_file():
        return []
    return [{"step": f"scene:{scene}", "kind": "moveto", "ref": r, "off": [float(v) for v in o.split()] if o else
             [0.0, 0.0, 0.0], "water": False} for r, o in MOVETO.findall(p.read_text())]


def check_stand(b: Build, s: dict) -> str | None:
    """None when the stand is on the current build's ground (or water it says is water), else why not."""
    tol = TOL_M * su.UNITS_PER_METRE
    if s["kind"] == "setpos":
        x, y, z = s["x"], s["y"], s["z"]
        if s.get("deck"):
            return None   # a deck stop (`# deck`): over the channel, its z is the deck's top (infra), not the ground
        g = b.ground_u(x, y)
        if z is not None and abs(z - g) > tol and not (s["water"] and (lv := b.water_u(x, y)) is not None
                                                     and abs(z - lv) <= tol):
            return f"{s['step']}: z {z:.0f} is {su.units_to_metres(z - g):+.2f} m off the ground {g:.0f}"
    else:
        r = b.ref(s["ref"])
        if r is None:
            return f"{s['step']}: {s['ref']} is no placed exterior ref of the build"
        if r.get("interior"):
            return None  # inside: the interior's own floor
        x, y = r["x"] + s["off"][0], r["y"] + s["off"][1]
        if r["marker"]:
            g = b.ground_u(x, y)
            z = (g + su.metres_to_units(r["over"]) if r.get("over") is not None else r["z"]) + s["off"][2]
            if abs(z - g) > tol:
                return f"{s['step']}: {s['ref']} at z {z:.0f} is {su.units_to_metres(z - g):+.2f} m off the ground {g:.0f}"
        elif r["own_z"]:
            return None  # its own z: a porch or a deck the place build seats; the ref is the stand
    if not s["water"] and b.wet(x, y):
        return (f"{s['step']}: stands in water ({su.units_to_metres(b.water_u(x, y) - b.ground_u(x, y)):.1f} m deep)"
                f" at {x:.0f} {y:.0f}")
    return None


def check(b: Build, names=DERIVED) -> dict[str, list[str]]:
    """Every derived journey's stands against the build: {journey: [why each is stale]}."""
    import yaml
    out = {}
    for n in names:
        p = JOURNEYS / f"{n}.yaml"
        if not p.is_file():
            continue
        text = p.read_text()
        if n == "sky-ab":   # derived from the panel markers' positions, not stands
            from tools.journeys import gen
            out[n] = gen.sky_ab_stale(b)
            continue
        if n == "grade-ab":   # derived from sky-ab's marker and road-look's stand
            from tools.journeys import gen
            out[n] = [] if text == gen.grade_ab(b) else ["grade-ab differs from its generator (refresh --only grade-ab)"]
            continue
        j = yaml.safe_load(text)
        ss = stands(text) + scene_stands(j.get("scene") or "")
        out[n] = [e for s in ss if (e := check_stand(b, s))]
        if n in WATER_JOURNEYS:
            out[n] += [e for s in water_stops(text) if (e := water_stop_bad(b, s))]
    return out


def reframe(b: Build, text: str, log: list) -> str:
    """Each setpos step re-seated on the ground and moved along its approach line out of water and foliage; the
    heading and pitch re-aimed at the subject. Idempotent on a clear journey."""
    lines = text.splitlines()
    for name, a, z in steps_of(text):
        blk = "\n".join(lines[a:z])
        pos = {k: float(v) for k, v in SETPOS.findall(blk)}
        if not {"x", "y"} <= set(pos):
            continue
        ang = {k: float(v) for k, v in SETANGLE.findall(blk)}
        m = SUBJECT.search(blk)
        subj = tuple(float(v) for v in m.groups()) if m else subject_of(b, pos["x"], pos["y"], ang.get("z", 0.0),
                                                                          ang.get("x", 0.0))
        water = "# water" in blk
        f = frame(b, pos["x"], pos["y"], subj, water)
        turned = False
        if not f["clear"] and (m or not f["dry"]):  # a named subject may be seen from any side: the other bearings, nearest first
            d0 = math.hypot(pos["x"] - subj[0], pos["y"] - subj[1])
            brg = math.degrees(math.atan2(pos["x"] - subj[0], pos["y"] - subj[1])) % 360
            alt = place(b, subj, d0, [(brg + s_ * k * 45) % 360 for k in range(1, 5) for s_ in (1, -1)][:7])
            if (alt["clear"], alt["dry"], -alt["blockers"]) > (f["clear"], f["dry"], -f["blockers"]):
                f = {**alt, "moved_m": round(math.hypot(alt["x"] - pos["x"], alt["y"] - pos["y"]) / su.UNITS_PER_METRE, 1)}
                turned = True
        x, y = f["x"], f["y"]
        zz = (b.water_u(x, y) if water else b.ground_u(x, y)) + SEAT_U
        h, p = aim(eye_of(b, x, y), subj)
        if not m:  # an inferred subject keeps the authored pitch (a level view stays level), and its heading unless turned
            h, p = (h if turned else ang.get("z", h)), ang.get("x", 0.0)
        new = {"x": x, "y": y, "z": zz}
        for i in range(a, z):
            lines[i] = SETPOS.sub(lambda mm: f"player.setpos {mm.group(1)} {new[mm.group(1)]:.0f}", lines[i])
            lines[i] = SETANGLE.sub(lambda mm: f"player.setangle {mm.group(1)} {(h if mm.group(1) == 'z' else p):.0f}",
                                    lines[i])
        log.append({"step": name, **{k: f[k] for k in ("moved_m", "why", "clear")}})
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


# -- water stops: the eye must hold water (lane harness-r5-water-aim) ---------------------------------------------------
WATER_NEAR_M, WATER_HALF_DEG, WATER_MIN_SHARE = 60.0, 30.0, 0.4   # near field 0-60 m, +-30 degrees, >= 40% water
WATER_JOURNEYS = ("water-types",)
# A creek is a few metres wide: no stand can have 40% of a 60 m, 60 degree field in it (the widest possible is ~20%), so a
# stream holds the share its width allows; its aim point must still be water and its channel in frame.
WATER_MIN_SHARE_BY_STEP = {"stream": 0.08}


def min_share(step: str) -> float:
    return WATER_MIN_SHARE_BY_STEP.get(step, WATER_MIN_SHARE)


@memo("water_share", reach=lambda x, y, heading, near_m, half_deg: around(x, y, near_m))
def water_share(b: Build, x: float, y: float, heading: float, near_m: float = WATER_NEAR_M,
                half_deg: float = WATER_HALF_DEG) -> float:
    """The share (by ground area) of the near field, 0-near_m along `heading` (Skyrim bearing) and +-half_deg, that is
    water at or below the eye and in sight: the ground there lies under the water level, the level is not above the eye,
    and the ground between does not rise over the line from the eye to it."""
    u = su.UNITS_PER_METRE
    ex, ey, ez = eye_of(b, x, y)
    tot = hit = 0.0
    n_r, n_a = 15, 13
    for i in range(n_r):
        r = (i + 0.5) * near_m / n_r
        for j in range(n_a):
            a = math.radians(heading + (j / (n_a - 1) - 0.5) * 2 * half_deg)
            wgt = r  # polar area weight
            tot += wgt
            px, py = x + math.sin(a) * r * u, y + math.cos(a) * r * u
            lv = b.water_u(px, py)
            if lv is None or lv > ez or b.ground_u(px, py) >= lv:
                continue
            seen = True
            for k in range(1, 9):   # the ground between the eye and the point must not rise over the line
                t = k / 9
                qx, qy = x + (px - x) * t, y + (py - y) * t
                if b.ground_u(qx, qy) > ez + (lv - ez) * t:
                    seen = False
                    break
            if seen:
                hit += wgt
    return hit / tot if tot else 0.0


SHORTFALL = re.compile(r"#\s*shortfall: water (\d+)%")   # a kept stop below its floor: the generator's own share, whole %


def water_stops(text: str) -> list[dict]:
    """The stops of a water journey: name, stand (x, y), heading, subject (x, y)."""
    lines = text.splitlines()
    out = []
    for name, a, z in steps_of(text):
        blk = "\n".join(lines[a:z])
        pos = {k: float(v) for k, v in SETPOS.findall(blk)}
        ang = {k: float(v) for k, v in SETANGLE.findall(blk)}
        m = SUBJECT.search(blk)
        if {"x", "y"} <= set(pos) and m and "z" in ang:
            sf = SHORTFALL.search(blk)
            out.append({"step": name, "x": pos["x"], "y": pos["y"], "heading": ang["z"],
                        "pitch": ang.get("x", 0.0), "subject": tuple(float(v) for v in m.groups()),
                        "shortfall": int(sf.group(1)) if sf else None})
    return out


def water_stop_bad(b: Build, s: dict) -> str | None:
    """Why a water stop does not look at water, else None: the aim point is not a water cell, the aim does not point at the
    subject, or the near field holds under WATER_MIN_SHARE water."""
    sx, sy = s["subject"][0], s["subject"][1]
    want = math.degrees(math.atan2(sx - s["x"], sy - s["y"])) % 360
    off = abs((s["heading"] - want + 180) % 360 - 180)
    if off > 3:
        return f"{s['step']}: heading {s['heading']:.0f} is {off:.0f} deg off its subject (bearing {want:.0f})"
    if not b.wet(sx, sy):
        return f"{s['step']}: the aim point {sx:.0f} {sy:.0f} is not a water cell"
    if b.soaked(s["x"], s["y"]):
        return (f"{s['step']}: no dry footing: ground {su.units_to_metres(b.margin_u(s['x'], s['y'])):+.2f} m over the cell "
                f"water level (needs {DRY_FOOTING_M} m)")
    if s["step"] == "sea-far":   # the horizon stop: the open water within SEA_FAR_M, as the generator reads it
        from tools.journeys import gen
        rays = sum(frame_read(b, s["x"], s["y"], s["heading"], 0.0, near_m=gen.SEA_FAR_M)[1].values())
        return None if rays >= gen.SEA_FAR_MIN_RAYS else (
            f"sea-far: {rays} wet rays to {gen.SEA_FAR_M:.0f} m, under {gen.SEA_FAR_MIN_RAYS}: it looks at land")
    sh = frame_share(b, s["x"], s["y"], s["heading"], s.get("pitch", 0.0))
    fl = frame_floor(s["step"])
    if sh < fl and s.get("shortfall") == round(sh * 100):   # kept short by the generator: current until the build moves it
        return None
    if sh < fl:
        return f"{s['step']}: water is {sh:.0%} of the lower frame (0-60 m, +-30 deg), under its floor {fl:.0%}"
    return None


# -- landscape grass: the LTEX under each LAND vertex and the grass it grows (lane 1.15-r6-water-stands-2) -------------
# Round 6's sea, river and brackish stands read 0/0 on the placed plants and still stood in reeds and ferns: the engine
# grows grass from the LTEX under each vertex (GNAM), which the placed-plant count never saw. The vertex's textures come
# from the build's LAND records (out/terrain/land, base + layers with 17x17 alpha per quad); each LTEX's grass list is
# the plan's (`ltex_grass`, which tools/argonia_world/terrain/grass.py `check` holds equal to what the game loads), each
# GRAS's model from out/ltex-scan.json. GRASS_HEIGHT_M is the height class of each grass model, by its mesh (the scan
# carries no bounds): a class, not a measurement; tall is anything that reaches a standing eye's lower frame.
GRASS_HEIGHT_M = {
    "marshgrassobj01.nif": 1.2, "cattailgrass.nif": 1.8, "grassfern01.nif": 0.9, "grassplant01.nif": 0.8,
    "tundragrassobj03.nif": 0.7, "tundragrassobj04.nif": 0.7, "tundragrass01.nif": 0.4, "forestgrass01.nif": 0.4,
    "rockgrass01.nif": 0.2, "rockgrasswater01.nif": 0.3, "tbprockgrasswater03.nif": 0.3, "tbpalgae01.nif": 0.1,
    "waterkelptall01.nif": 1.5, "waterkelptall02.nif": 1.5, "waterkelptall03.nif": 1.5, "waterkelpshort01.nif": 0.5,
    "tbpcoastdriftwood01.nif": 0.3, "tbpcoastdriftwood02.nif": 0.3, "tbp_coralsmall01.nif": 0.3,
    "tbp_seaweed02test.nif": 0.8, "tbp_seaweed06.nif": 0.8,
}
TALL_GRASS_M = 0.5          # a grass this tall or taller fills the lower frame of a standing eye
GRASS_NEAR_M, GRASS_LINE_M = 6.0, 20.0   # no tall grass within 6 m of the eye point or under the first 20 m of the eye line
GRASS_TEX_MIN = 0.3         # a texture this much of a vertex's blend grows its grass there
QUADS = {"BottomLeft": (0, 0), "BottomRight": (16, 0), "TopLeft": (0, 16), "TopRight": (16, 16)}


def ltex_grass_heights(world=None) -> dict[str, float]:
    """LTEX form key -> the tallest grass its list grows (metres), from the plan rows and the scan's GRAS models."""
    from tools.argonia_world import db
    from tools.argonia_world.terrain import grass as G
    w = world or db.open()
    model = {g["formKey"]: g["model"].rsplit("/", 1)[-1].lower() for g in G.load_scan()["grass"]}
    out: dict[str, float] = {}
    for lt, g in w.query("SELECT ltex_form_key, grass_form_key FROM ltex_grass"):
        out[lt] = max(out.get(lt, 0.0), GRASS_HEIGHT_M.get(model.get(g, ""), 0.0))
    return out


def vertex_textures(quads: list[dict]) -> dict[tuple[int, int], dict[str, float]]:
    """(i, j) 0..32 (east, north) -> {LTEX: blend weight} from a LAND record's quads (each layer over the ones before)."""
    import base64
    out: dict[tuple[int, int], dict[str, float]] = {}
    for q in quads:
        oi, oj = QUADS[q["q"]]
        alphas = [(l["ltex"], base64.b64decode(l["alpha"])) for l in q["layers"]]
        for r in range(17):
            for c in range(17):
                w = {q["base"]: 1.0}
                for lt, a in alphas:
                    v = a[r * 17 + c] / 255.0 if len(a) > r * 17 + c else 0.0
                    if v:
                        w = {k: x * (1 - v) for k, x in w.items()}
                        w[lt] = w.get(lt, 0.0) + v
                out.setdefault((oi + c, oj + r), w)
    return out


class Grass:
    """The tallest grass the ground grows at each LAND vertex (metres), loaded per cell row from out/terrain/land."""
    def __init__(self, heights: dict[str, float] | None = None, root: Path | None = None):
        self._h, self._root, self._cells = heights, root or ROOT / "out" / "terrain" / "land", {}

    def heights(self) -> dict[str, float]:
        if self._h is None:
            self._h = ltex_grass_heights()
        return self._h

    def _row(self, cy: int):
        p = self._root / f"cy{cy:+04d}.jsonl.gz"
        if p.is_file():
            with gzip.open(p, "rt", encoding="ascii") as f:
                for ln in f:
                    d = json.loads(ln)
                    self._cells[(d["x"], d["y"])] = {k: max((self.heights().get(t, 0.0) for t, w in v.items()
                                                             if w >= GRASS_TEX_MIN), default=0.0)
                                                     for k, v in vertex_textures(d["quads"]).items()}
        for cx in range(-200, 200):
            self._cells.setdefault((cx, cy), {})

    def at(self, x: float, y: float) -> float:
        """The tallest grass grown at the LAND vertex nearest (x, y), metres (0 where none)."""
        cx, cy = su.cell_of(x, y)
        if (cx, cy) not in self._cells:
            self._row(cy)
        ox, oy = su.cell_origin(cx, cy)
        i, j = round((x - ox) / su.VERTEX_SPACING_UNITS), round((y - oy) / su.VERTEX_SPACING_UNITS)
        return self._cells[(cx, cy)].get((i, j), 0.0)


@memo("grass_hits", reach=lambda eye, heading, near_m, line_m, first: around(eye[0], eye[1], max(near_m, line_m) + 3.0))
def grass_hits(b: Build, eye: tuple, heading: float, near_m: float = GRASS_NEAR_M, line_m: float = GRASS_LINE_M,
               first: bool = False) -> int:
    """The LAND vertices growing tall grass (TALL_GRASS_M, its top over any water there) within near_m of the eye point
    or within one vertex spacing of the first line_m of the eye line (the ground under it). `first`: stop at one."""
    g = getattr(b, "grass", None)
    if g is None:
        g = b.grass = Grass()
    u, s = su.UNITS_PER_METRE, su.VERTEX_SPACING_UNITS
    ex, ey, _ = eye
    a = math.radians(heading)
    dx, dy = math.sin(a), math.cos(a)
    reach = max(near_m, line_m) * u + s
    hits = 0
    gx0, gy0 = math.floor((ex - reach) / s), math.floor((ey - reach) / s)
    for gi in range(gx0, gx0 + int(2 * reach / s) + 2):
        for gj in range(gy0, gy0 + int(2 * reach / s) + 2):
            px, py = gi * s, gj * s
            rx, ry = px - ex, py - ey
            t = rx * dx + ry * dy
            near = math.hypot(rx, ry) <= near_m * u
            on = 0 <= t <= line_m * u and abs(rx * dy - ry * dx) <= s
            if not (near or on):
                continue
            h = g.at(px, py)
            if h < TALL_GRASS_M:
                continue
            lv = b.water_u(px, py)
            if lv is not None and b.ground_u(px, py) + h * u <= lv:
                continue   # submerged: kelp under the surface is not in the eye's way
            hits += 1
            if first:
                return hits
    return hits


def clearance3(b: Build, eye: tuple, heading: float) -> tuple[int, int, int]:
    """(line, canopy, grass): `clearance`'s placed-plant counts and the tall landscape grass (grass_hits)."""
    return (*clearance(b, eye, heading), grass_hits(b, eye, heading))


# -- the frame share: what the lower half of the still shows (lane 1.15-r6-water-stands-2) -----------------------------
FRAME_HALF_H_DEG, FRAME_HALF_V_DEG = 30.0, 25.0   # the share's field: +-30 degrees across, the lower half down 25 degrees
FRAME_NEAR_M, FRAME_MIN_SHARE = 60.0, 0.5
FRAME_FLOOR_BY_STEP = {"stream": 0.3}   # a narrow channel cannot fill half the lower frame (planner, round 6)


def frame_floor(step: str) -> float:
    return FRAME_FLOOR_BY_STEP.get(step, FRAME_MIN_SHARE)


@memo("frame_read", skip=("types",), dec=lambda r: (r[0], {(a, c): n for a, c, n in r[1]}),
      enc=lambda r: [r[0], [[c[0], c[1], n] for c, n in r[1].items()]],
      reach=lambda x, y, heading, pitch, near_m, types: around(x, y, near_m))
def frame_read(b: Build, x: float, y: float, heading: float, pitch: float = 0.0, near_m: float = FRAME_NEAR_M,
               types: dict | None = None) -> tuple[float, dict]:
    """(share, wet cells): the share of the still's lower half (rays from the eye at `heading` +-30 deg, from the pitch
    line down 25 deg; pitch positive is down) whose first meeting within near_m is a water surface over lower ground (a
    ray that meets the ground first, or nothing within near_m, is not water), and per cell (cx, cy) the rays that met
    its water. Marched over the build's ground and cell water heights."""
    u = su.UNITS_PER_METRE
    ex, ey, ez = eye_of(b, x, y)
    n_h, n_v, step = 9, 8, 1.0 * u
    hit = tot = 0
    cells: dict = {}
    for i in range(n_h):
        a = math.radians(heading + (i / (n_h - 1) - 0.5) * 2 * FRAME_HALF_H_DEG)
        sa, ca = math.sin(a), math.cos(a)
        for j in range(n_v):
            dn = math.radians(pitch + (j + 0.5) / n_v * FRAME_HALF_V_DEG)
            tot += 1
            if dn <= 0:
                continue
            tn = math.tan(dn)
            r = step
            while r <= near_m * u:
                px, py, pz = ex + sa * r, ey + ca * r, ez - tn * r
                g = b.ground_u(px, py)
                lv = b.water_u(px, py)
                if lv is not None and lv > g and pz <= lv:
                    hit += 1
                    c = su.cell_of(px, py)
                    cells[c] = cells.get(c, 0) + 1
                    break
                if pz <= g:
                    break
                r += step
    return (hit / tot if tot else 0.0), cells


def frame_share(b: Build, x: float, y: float, heading: float, pitch: float = 0.0, near_m: float = FRAME_NEAR_M) -> float:
    """frame_read's share alone."""
    return frame_read(b, x, y, heading, pitch, near_m)[0]


TYPE_MIN_SHARE = 0.7   # the wet rays of the lower frame whose cell carries the stop's own water type


def type_share(cells: dict, types: dict, want) -> tuple[float, list]:
    """(share, others): of frame_read's wet rays, the share whose cell's type (types[(cx, cy)]) is in `want`; others the
    (cx, cy, type, rays) rows that are not, most rays first (a neighbouring body, or a cell the type was not applied to)."""
    tot = sum(cells.values())
    own = sum(n for c, n in cells.items() if types.get(c) in want)
    others = sorted(((c[0], c[1], types.get(c), n) for c, n in cells.items() if types.get(c) not in want),
                    key=lambda r: -r[3])
    return (own / tot if tot else 0.0), others


# -- the frustum cover: what the near frame shows, not only the eye line (lane 1.15-r6-water-stands-3) -----------------
FRUSTUM_H_DEG, FRUSTUM_V_DEG, FRUSTUM_FAR_M = 32.0, 20.0, 25.0   # the camera frustum: +-32 across, +-20 up/down, 0-25 m
NEAR_FRAME_M, NEAR_COVER_MAX, EYE_CLEAR_M = 10.0, 0.05, 2.5     # near frame 0-10 m: cover under 5 %, no bounds within 2.5 m
UPPER_COVER_MAX = 0.10                                           # the sea: plant cover of the upper frame under 10 %


def _span(lo: float, hi: float, a: float, b_: float) -> float:
    return max(0.0, min(hi, b_) - max(lo, a))


@memo("frustum_cover", reach=lambda eye, heading, pitch: around(eye[0], eye[1], FRUSTUM_FAR_M + 3.0))
def frustum_cover(b: Build, eye: tuple, heading: float, pitch: float = 0.0) -> dict:
    """The angular cover of the frame by each placed plant (its seated OBND as a cylinder: widest half-extent, pivot + z0
    to + height) and tall-grass vertex inside the frustum (+-FRUSTUM_H_DEG across, +-FRUSTUM_V_DEG up/down from the aim,
    0-FRUSTUM_FAR_M): each as the angular rectangle it subtends at its nearest distance, clipped to the frame, over the
    frame's area. Returns near (plants, 0-NEAR_FRAME_M), upper (plants 0-25 m, the frame above the aim), all (plants
    0-25 m), grass (tall-grass vertices 0-NEAR_FRAME_M; reported, not gated) and nearest_m (the nearest plant bounds to
    the eye, any direction). Covers are summed (overlaps count twice: conservative)."""
    u = su.UNITS_PER_METRE
    ex, ey, ez = eye
    W, H = 2 * FRUSTUM_H_DEG, 2 * FRUSTUM_V_DEG
    near = upper = allc = grass = 0.0
    nearest = float("inf")

    def rect(cx, cy, r, lo, hi):
        hyp = math.hypot(cx - ex, cy - ey)
        dn = max(hyp - r, 0.3 * u)
        hw = 90.0 if hyp <= r else math.degrees(math.asin(min(1.0, r / hyp)))
        dh = (math.degrees(math.atan2(cx - ex, cy - ey)) - heading + 180) % 360 - 180
        if hyp <= r:
            dh = 0.0
        w = _span(-FRUSTUM_H_DEG, FRUSTUM_H_DEG, dh - hw, dh + hw)
        v0 = math.degrees(math.atan2(lo - ez, dn)) + pitch
        v1 = math.degrees(math.atan2(hi - ez, dn)) + pitch
        return dn, w, v0, v1

    for f in b.foliage_near(ex, ey, FRUSTUM_FAR_M * u):
        fx, fy, fz, fr, fh = f[:5]
        lo = fz + (f[6] if len(f) > 6 else 0.0)
        hi = lo + fh
        dz = 0.0 if lo <= ez <= hi else min(abs(lo - ez), abs(hi - ez))
        nearest = min(nearest, math.hypot(max(0.0, math.hypot(fx - ex, fy - ey) - fr), dz) / u)
        dn, w, v0, v1 = rect(fx, fy, fr, lo, hi)
        if dn > FRUSTUM_FAR_M * u or not w:
            continue
        c = w * _span(-FRUSTUM_V_DEG, FRUSTUM_V_DEG, v0, v1) / (W * H)
        allc += c
        upper += w * _span(0.0, FRUSTUM_V_DEG, -v1, -v0) / (W * FRUSTUM_V_DEG)   # up is negative pitch
        if dn <= NEAR_FRAME_M * u:
            near += c
    g = getattr(b, "grass", None)
    if g is None:
        g = b.grass = Grass()
    s = su.VERTEX_SPACING_UNITS
    reach = NEAR_FRAME_M * u
    gx0, gy0 = math.floor((ex - reach) / s), math.floor((ey - reach) / s)
    for gi in range(gx0, gx0 + int(2 * reach / s) + 2):
        for gj in range(gy0, gy0 + int(2 * reach / s) + 2):
            px, py = gi * s, gj * s
            if math.hypot(px - ex, py - ey) > reach:
                continue
            h = g.at(px, py)
            if h < TALL_GRASS_M:
                continue
            gz = b.ground_u(px, py)
            lv = b.water_u(px, py)
            if lv is not None and gz + h * u <= lv:
                continue
            dn, w, v0, v1 = rect(px, py, s / 2, gz, gz + h * u)
            if w:
                grass += w * _span(-FRUSTUM_V_DEG, FRUSTUM_V_DEG, v0, v1) / (W * H)
    cap = lambda v: min(v, 1.0)   # overlaps sum: a region of the frame is at most wholly covered (lane 1.15-r6-panel-stands)
    return {"near": cap(near), "upper": cap(upper), "all": cap(allc), "grass": cap(grass), "nearest_m": nearest}


def cover_ok(fc: dict, sea: bool = False) -> bool:
    """The frustum rule: near-frame plant cover under NEAR_COVER_MAX and for the sea the upper frame under
    UPPER_COVER_MAX. nearest_m is reported only: a plant beside or behind the camera is harmless (planner, round 6)."""
    return fc["near"] < NEAR_COVER_MAX and (not sea or fc["upper"] < UPPER_COVER_MAX)


def cover_text(fc: dict) -> str:
    return (f"cover near {fc['near']:.1%} upper {fc['upper']:.1%} all {fc['all']:.1%} grass {fc['grass']:.1%} "
            f"nearest {fc['nearest_m']:.1f} m")
