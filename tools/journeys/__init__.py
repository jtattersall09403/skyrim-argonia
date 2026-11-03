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

ROOT = Path(__file__).resolve().parents[2]
JOURNEYS = ROOT / "tests" / "journeys"
SCENES = ROOT / "tests" / "scenes"
TOL_M = 0.5            # the brief's: a stand within 0.5 m of the ground
SEAT_U = 16.0          # the feet put this far over the ground (0.23 m): inside TOL_M, the engine settles him
CLEAR_M = 2.0          # no foliage within 2 m of the eye line (horizontally)
OVER_M = 0.5           # and the line passes a plant's top (or under a crown) by at least this
STEP_M, BACK_M, NEAR_M = 2.0, 30.0, 2.0   # the approach-line search: 2 m steps, up to 30 m back, never nearer than 2 m
SUBJECT_M = 15.0       # a level view's subject distance
SUBJECT_FREE_M = 2.0   # foliage this near the subject is the subject's own (the tree seated, the creature's reeds)
NOT_FOLIAGE = ("rock",)
TRUNKED = ("canopy", "emergent", "palm", "mangrove", "gallery", "cliff-tree", "deadwood")  # leaves only up top
CROWN_FROM, TRUNK_U = 0.4, 25.0   # a tree's crown from 0.4 of its height up; below it a trunk ~0.35 m round
# The data-driven journeys: refresh re-derives them, the L1 test checks them.
DERIVED = ("world-panel", "river-steps", "water-types", "road-look", "claywater-walk", "claywater-look", "creature-spots", "tree-seat",
           "rock-booth", "creatures-kinds")

SETPOS = re.compile(r"player\.setpos ([xyz]) (-?\d+(?:\.\d+)?)")
SETANGLE = re.compile(r"player\.setangle ([xz]) (-?\d+(?:\.\d+)?)")
MOVETO = re.compile(r"player\.moveto (ARG_Ref_\w+)((?: -?\d+(?:\.\d+)?){3})?")
SUBJECT = re.compile(r"#\s*subject:\s*(-?[\d.]+) (-?[\d.]+) (-?[\d.]+)")
STEP = re.compile(r"^\s*-\s+name:\s*(\S+)|^\s*\{?\s*\"name\":\s*\"([^\"]+)\"")


class Build:
    """The current build's ground, water, foliage and refs, loaded lazily (ground 2 s; the DB ~13 s, only for refs)."""

    def __init__(self, ground=None, water=None, foliage=None, refs=None):
        self._ground, self._water, self._foliage, self._refs = ground, water, foliage, refs

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
                        if s:
                            fs.append((r[2], r[3], r[4], s[0] * r[8], s[1] * r[8], s[2]))
                    row[(c["x"], c["y"])] = fs
        for cx in range(-200, 200):
            self._foliage.setdefault((cx, cy), row.get((cx, cy), []))

    _shapes = None

    def shapes(self) -> dict:
        """form key -> (horizontal radius, height) units of each placed plant form, from its bounds (object_form)."""
        if Build._shapes is None:
            from tools.argonia_world import db
            Build._shapes = {r["form_key"]: (max(1.0, abs(r["bound_x0"] or 0), abs(r["bound_x1"] or 0),
                                                 abs(r["bound_y0"] or 0), abs(r["bound_y1"] or 0)),
                                             max(1.0, (r["bound_z1"] or 0) - (r["bound_z0"] or 0)),
                                             r["role_id"] not in TRUNKED)
                             for r in db.open().query("SELECT form_key, role_id, bound_x0, bound_x1, bound_y0, bound_y1, "
                                                      "bound_z0, bound_z1 FROM object_form")
                             if r["role_id"] not in NOT_FOLIAGE}
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
            for r in w.query("SELECT id, cell_id, x_m, y_m, z_m FROM build_ref"):
                if r["cell_id"] not in ext:  # an interior's ref: no province ground under it
                    self._refs[ref_edid(r["id"])] = {"id": r["id"], "interior": True}
                    continue
                x, y = su.province_to_skyrim(r["x_m"], r["y_m"])
                own = r["z_m"] is not None
                # a studio marker (the panel's, the probes') stands on the ground it was put over: its z is checked
                self._refs[ref_edid(r["id"])] = {"id": r["id"], "x": x, "y": y, "own_z": own,
                                                 "marker": r["cell_id"].startswith("cell.studio."),
                                                 "z": su.metres_to_units(r["z_m"]) if own else None}
        return self._refs.get(edid)

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
            fx, fy, fz, fr, fh, bushy = f
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
        n = len(b.blockers(eye_of(b, px, py), subj))
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
                        "water": "# water" in blk})
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
            g, z = b.ground_u(x, y), r["z"] + s["off"][2]
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
        j = yaml.safe_load(text)
        ss = stands(text) + scene_stands(j.get("scene") or "")
        out[n] = [e for s in ss if (e := check_stand(b, s))]
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
