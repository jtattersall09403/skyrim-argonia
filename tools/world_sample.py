#!/usr/bin/env python3
"""The world track's in-game sample (docs/phases/1-core-loop/README.md, "The world track's in-game sample"): the 13
stops as one runnable journey, `tests/journeys/world-sample.yaml`, and one scene per stop,
`tests/scenes/world-sample-NN-<name>.txt`. Both are DERIVED here from the world database (through db.py), the
terrain (`build.game_heights_m`, the numbers the LAND stores), the water plan and the navmesh, so the expected
values in the journey are data, not hand-typed.

    python3 tools/world_sample.py --write     # regenerate the journey and the scenes
    python3 tools/world_sample.py --check     # exit 1 when the files on disk differ from what the data gives

Every stop: a scene (month, day, hour, a weather from the stop's own region list, never Skyrim's SkyrimClear
0000081A; the travel line last), then steps that read what a number decides. A distant stop is reached by the
journey's `console: bat <scene>` (the scene files reach the machine with `make deploy`; only the first is sent by
the runner), then a `player.moveto` to a placed probe marker (an XMarker of the world DB) and a read of the player's z against the expected ground.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from tools.argonia_world import skyrim_units as su  # noqa: E402

JOURNEY = REPO / "tests" / "journeys" / "world-sample.yaml"
SCENES = REPO / "tests" / "scenes"
TOL_M = 0.5  # 2.W1 §a: ground within 0.5 m of the heightfield
DROP_U = 100  # a probe starts this far above the ground (about 1.4 m) and falls to it
NO_WEATHER = {"clear"}  # weather ids never used: SkyrimClear (0000081A) is Skyrim's own
NAV_SEED = 2026
NAV_PAIRS = 20
FRAMES = 600
DRY_MONTH, DRY_DAY = 2, 15  # the dry season (days 0-127)

CLIFF_CELL = (-19, 58)  # 2.W1's worst limited cell (docs/research/2026-10-29/lane-2.W1-terrain.md)
VEG_NOTE = "out/terrain/vegetation/summary.json densest[0]"
HIGH_CELL = (-53, 3)  # the LOD lane's distant-view cell, about 440 m (docs/research/2026-10-29/lane-2.W4-lod.md)
CLAYWATER_REF = "ARG_Ref_ClaywaterStationRoadIn"
CLAYWATER_BUILD_REF = "ref.claywater-station.road-in"
CLAYWATER_BLOCK = (-60, 8, -53, 15)


class Missing(Exception):
    """A data file the sample is derived from is not on this machine."""


def data_root() -> Path:
    return Path(os.environ.get("ARGONIA_DATA", str(Path.home() / ".argonia" / "data")))


def need(path: Path) -> Path:
    if not path.exists():
        raise Missing(str(path))
    return path


# --- the terrain ----------------------------------------------------------------------------------------------
class Ground:
    """The game's ground (LAND vertices, every layer applied) for the whole province, in metres, by sample index."""

    def __init__(self):
        from tools.argonia_world.terrain import build as tb
        from tools.argonia_world.terrain.grid import N, Sources
        need(data_root() / "terrain" / "refined-height-f32.npy")
        self.n = N
        src = Sources.load()
        self.H = tb.game_heights_m(src, src.pad, src.pad + N + 1, src.pad, src.pad + N + 1)

    def vertex(self, cx: int, cy: int, i: int, j: int) -> tuple[int, int]:
        """(row, col) of vertex i (0 = west .. 32) and j (0 = south .. 32) of exterior cell (cx, cy)."""
        x0, y0 = su.PROVINCE_CELL_SW
        return self.n - ((cy - y0) * su.QUADS_PER_CELL + j), (cx - x0) * su.QUADS_PER_CELL + i

    def window(self, cx: int, cy: int):
        r_s, c_w = self.vertex(cx, cy, 0, 0)
        return self.H[r_s - su.QUADS_PER_CELL:r_s + 1, c_w:c_w + su.QUADS_PER_CELL + 1]  # row 0 north

    def snap(self, x_m: float, y_south_m: float) -> tuple[int, int]:
        return (min(max(round(y_south_m / su.PROVINCE_SAMPLE_M), 0), self.n),
                min(max(round(x_m / su.PROVINCE_SAMPLE_M), 0), self.n))

    def units(self, r: int, c: int) -> tuple[float, float, float]:
        x, y = su.province_to_skyrim(c * su.PROVINCE_SAMPLE_M, r * su.PROVINCE_SAMPLE_M)
        return su.rounded(x, 2), su.rounded(y, 2), su.rounded(su.metres_to_units(float(self.H[r, c])), 2)

    def cell(self, r: int, c: int) -> tuple[int, int]:
        x, y, _ = self.units(r, c)
        return su.cell_of(x, y)

    def slope_deg(self, r: int, c: int) -> float:
        r0, r1, c0, c1 = max(r - 1, 0), min(r + 1, self.n), max(c - 1, 0), min(c + 1, self.n)
        dzdy = (self.H[r1, c] - self.H[r0, c]) / ((r1 - r0) * su.PROVINCE_SAMPLE_M)
        dzdx = (self.H[r, c1] - self.H[r, c0]) / ((c1 - c0) * su.PROVINCE_SAMPLE_M)
        return math.degrees(math.atan(math.hypot(dzdx, dzdy)))


# --- probe markers ----------------------------------------------------------------------------------------------
# A raw `teleport pos` (SetPosition) across cells crashed the engine (diag4 fix 1); every probe point is a placed,
# persistent XMarker of the world DB (`build_ref` rows `ref.probe.<step>` in PROBE_CELL) and the journey moves the
# player with `player.moveto`, the engine's normal path. `--write` syncs the rows through db.py; `make plugin` emits them.
from tools.argonia_world.vegetation.build import PROBE_PLACE  # noqa: E402 - footprints skip it
PROBE_CELL = "cell.studio.world-sample"
PROBES: dict[str, tuple[float, float, float]] = {}  # ref id -> (x_m, y_m south, z_m), filled by build()


def probe_ref(step: str) -> str:
    return f"ref.probe.{step}"


def probe_edid(step: str) -> str:
    from tools.argonia_world.place_build import ref_edid
    return ref_edid(probe_ref(step))


def probe_go(step: str, x_u: float, y_u: float, z_u: float) -> dict:
    """Record a marker at these worldspace units and return the step's move to it."""
    xm, ym = _province_m(x_u, y_u)
    PROBES[probe_ref(step)] = (round(xm, 3), round(ym, 3), round(su.units_to_metres(z_u), 3))
    return {"console": f"player.moveto {probe_edid(step)}"}


def probe_rows() -> list[dict]:
    return [{"id": rid, "cell_id": PROBE_CELL, "base": su.ENGINE_MARKER_HEADING, "x_m": x, "y_m": y, "z_m": z,
             "yaw_deg": 0.0, "persistent": True, "why": f"world-sample probe {rid.split('.', 2)[2]} (tools/world_sample.py)"}
            for rid, (x, y, z) in sorted(PROBES.items())]


def sync_probes(db, write: bool) -> bool:
    """True when the DB's probe rows match PROBES; with `write`, make them match and save."""
    have = {r["id"]: dict(r) for r in db.query("SELECT * FROM build_ref WHERE cell_id = ?", PROBE_CELL)}
    want = {r["id"]: r for r in probe_rows()}
    same = set(have) == set(want) and all(
        all(have[k][c] == v or (isinstance(v, float) and abs(have[k][c] - v) < 1e-6) for c, v in r.items())
        for k, r in want.items())
    if same or not write:
        return same
    if db.get("place", PROBE_PLACE) is None:
        db.insert("place", id=PROBE_PLACE, name="World sample probes")
    if db.get("build_cell", PROBE_CELL) is None:
        db.insert("build_cell", id=PROBE_CELL, place_id=PROBE_PLACE, kind="exterior")
    for k in have:
        db.delete("build_ref", k)
    for r in want.values():
        db.insert("build_ref", **r)
    db.save()
    return True


def probe_step(g: Ground, name: str, r: int, c: int, why: str, hi_extra_u: float = 0.0,
               above_ground_only: bool = True, reader: list | None = None) -> dict:
    """Teleport 1.4 m above the vertex, let it fall, read z against the ground the LAND stores (+-0.5 m)."""
    x, y, z = g.units(r, c)
    tol = su.metres_to_units(TOL_M)
    step = {
        "name": name, "why": why,
        "do": [probe_go(name, x, y, z + DROP_U), {"wait": 4}],
        "expect": [{"read": ["player"], "path": "pos.z", "ge": su.rounded(z - tol, 2), "within": 3},
                   {"read": ["player"], "path": "pos.z", "le": su.rounded(z + tol + hi_extra_u, 2), "within": 3}],
        "expected_ground_m": round(float(g.H[r, c]), 3),
    }
    if reader:
        step["reader"] = reader
    return step


# --- the database ----------------------------------------------------------------------------------------------
class World:
    def __init__(self):
        from tools.argonia_world import db
        self.db = db.open()

    def region_of(self, cx: int, cy: int) -> str | None:
        rows = self.db.query("SELECT land_region_id FROM cell_region_run WHERE cy = ? AND cx0 <= ? AND cx1 >= ?",
                             cy, cx, cx)
        return rows[0][0] if rows else None

    def nearest_region(self, cx: int, cy: int) -> str:
        r = self.region_of(cx, cy)
        if r:
            return r
        rows = self.db.query("SELECT land_region_id, cx0, cx1, cy FROM cell_region_run")
        best = min(rows, key=lambda x: (x[3] - cy) ** 2 + (min(max(cx, x[1]), x[2]) - cx) ** 2)
        return best[0]

    def weather_for(self, cx: int, cy: int, prefer: tuple[str, ...] = ("dry-haze", "clear-humid")) -> dict:
        """A weather from the region's own list, never SkyrimClear: the first of its states in `prefer` (the dry
        season's tannin haze, then the clear restyles; the mist, storm and squall hide the view), ours before
        Tropical Skyrim's restyles, the most likely first."""
        region = self.nearest_region(cx, cy)
        rows = self.db.query(
            "SELECT w.id, w.edid, l.chance, w.weather_state_id FROM land_region_weather l JOIN weather w ON w.id = l.weather_id "
            "WHERE l.land_region_id = ? ORDER BY l.chance DESC, w.id", region)
        ok = [r for r in rows if r[0] not in NO_WEATHER]
        if not ok:
            raise KeyError(f"{region}: no usable weather in its list")
        pick = None
        for state in prefer:
            hit = [r for r in ok if r[3] == state]
            hit.sort(key=lambda r: not r[1].startswith("ARG_"))
            if hit:
                pick = hit[0]
                break
        pick = pick or ok[0]
        return {"region": region, "id": pick[0], "edid": pick[1], "list": [r[1] for r in rows]}


# --- scenes ----------------------------------------------------------------------------------------------------
def scene_text(stop: dict) -> str:
    out = [f"; world sample stop {stop['n']} ({stop['title']}): {stop['summary']}",
           "; generated by tools/world_sample.py from the world data; edit the generator, not this file",
           f"; region {stop['weather']['region']}, weather from its own list: {', '.join(stop['weather']['list'])}",
           "; the travel line is last: a line after a travel ran during its load and crashed the game (game-6)",
           f"set GameMonth to {stop.get('month', DRY_MONTH)}", f"set GameDay to {DRY_DAY}",
           f"set gamehour to {stop.get('hour', 12)}",
           f"{stop.get('weather_cmd', 'fw')} {stop['weather']['edid']}", stop["travel"]]
    return "\r\n".join(out) + "\r\n"


def in_world(n: int) -> dict:
    return {"read": ["player"], "path": "worldspace.editor_id", "eq": "ARG_Province", "within": 20}


# Every stop after the first is reached through the interior holding cell: a cow straight from a stop whose steps
# moved the player with the bridge's `teleport pos` (a raw SetPosition) crashed the engine unloading the old grid
# (game-12, BSMultiBoundAABB; diag-croc-move-crash §3). From an interior, cow attaches a fresh grid.
HOLD = [{"console": "coc ARG_HoldingCell"}, {"wait": 5}]


def arrive(stop: dict, first: bool) -> dict:
    # One fresh process per stop: a second cross-cell cow in one process crashed the engine at stop 2 (diag3-g15
    # §world-sample, game, not our DLL). The relaunch loads the journey's save (the holding cell) without a scene.
    # The quit itself goes from the holding cell: qqq straight after a `teleport pos` probe crashed (game-16, twice).
    do = [] if first else [*HOLD, {"relaunch": {"save": True, "scene": False}}, {"console": f"bat {stop['scene']}"}, {"wait": 8}]
    return {"name": f"s{stop['n']:02d}-arrive", "do": do, "expect": [in_world(stop["n"])]}


def travel(g: "Ground", name: str, cx: int, cy: int) -> str:
    """The move to a placed arrival marker 1.4 m above the ground at the cell's centre: `cow` drove the culling job
    into a crash on the grid change (diag5-g17 §2); `player.moveto` a persistent XMarker is the engine's normal path."""
    x, y, z = g.units(*g.vertex(cx, cy, su.QUADS_PER_CELL // 2, su.QUADS_PER_CELL // 2))
    return probe_go(name, x, y, z + DROP_U)["console"]


def new_stop(n: int, key: str, title: str, summary: str, cell: tuple[int, int], world: World, **kw) -> dict:
    s = {"n": n, "key": key, "title": title, "summary": summary, "cell": list(cell),
         "scene": f"world-sample-{n:02d}-{key}", "travel": kw.pop("travel", None) or travel(world.ground, f"s{n:02d}-arrive", *cell),
         "weather": world.weather_for(*cell, *([kw.pop("prefer")] if "prefer" in kw else [])), "steps": []}
    s.update(kw)
    return s


NORDIC = "no pine, spruce, birch, snow, frost, heather, Nordic architecture or Nordic-grey rock anywhere in frame"


# --- the stops -------------------------------------------------------------------------------------------------
def stop_1(w: World, g: Ground) -> dict:
    ref = next(iter(w.db.query("SELECT x_m, y_m FROM build_ref WHERE id = ?", CLAYWATER_BUILD_REF)))
    r, c = g.snap(ref[0], ref[1])
    cell = g.cell(r, c)
    s = new_stop(1, "claywater", "Claywater block, on the road in",
                 "heights vs the heightfield, grass on the paint, region trees, the road surface", cell, w,
                 travel=f"player.moveto {CLAYWATER_REF}", hour=10)
    s["steps"] = [arrive(s, True)]
    for tag, dc in (("road-in", 0), ("east-30m", 16), ("west-30m", -16)):
        s["steps"].append(probe_step(g, f"s01-probe-{tag}", r, c + dc, f"ground at the {tag} point of the road"))
    s["steps"][-1]["reader"] = [
        "grass blades stand on the painted ground and stop where the paint stops",
        "trees are Black Marsh region trees (mangrove, cypress, palm, bald cypress); " + NORDIC,
        "the road reads as a worn road surface with no seam or hard edge to the verge",
        "no stretched or smeared ground texture"]
    s["cell_check"] = list(cell)
    return s


def stop_2(w: World, g: Ground) -> dict:
    cell = CLIFF_CELL
    win = g.window(*cell)
    r_s, c_w = g.vertex(*cell, 0, 0)
    r_n = r_s - su.QUADS_PER_CELL
    dr = np_abs(win[1:, :] - win[:-1, :])
    dc = np_abs(win[:, 1:] - win[:, :-1])
    if dr.max() >= dc.max():
        a, b = np_argmax2(dr)
        pair = ((a, b), (a + 1, b))
    else:
        a, b = np_argmax2(dc)
        pair = ((a, b), (a, b + 1))
    (ar, ac), (br, bc) = pair
    hi, lo = ((ar, ac), (br, bc)) if win[ar, ac] >= win[br, bc] else ((br, bc), (ar, ac))
    steep = float(abs(win[ar, ac] - win[br, bc]))
    clamp = lambda v: min(max(v, 0), su.QUADS_PER_CELL)  # noqa: E731
    def standable(start, away):
        """The first vertex out along `away` (from 2 samples) whose slope is under 35 deg: the limiter spreads this
        cell's cliff into an ~83 deg VHGT ramp several samples wide, and a probe set on it slides (game-18: the top
        shelf read 3 to 47 m low after 4 s; quantize.py's limit)."""
        last = None
        for k in range(2, 3 * su.QUADS_PER_CELL):
            rr, cc = start[0] + away[0] * k, start[1] + away[1] * k
            last = (rr, cc)
            if g.slope_deg(r_n + rr, c_w + cc) < 35.0:
                return last
        return last
    top = standable(hi, (hi[0] - lo[0], hi[1] - lo[1]))
    foot = standable(lo, (lo[0] - hi[0], lo[1] - hi[1]))
    s = new_stop(2, "cliff", "The steepest limited cliff", "the cliff ramp, seams, texture stretching", cell, w)
    s["cliff"] = {"step_m": round(steep, 2), "slope_deg": round(math.degrees(math.atan(steep / su.PROVINCE_SAMPLE_M)), 1)}
    s["steps"] = [arrive(s, False),
                  probe_step(g, "s02-probe-top-shelf", r_n + top[0], c_w + top[1],
                             "the shelf two samples behind the cliff edge"),
                  probe_step(g, "s02-probe-foot", r_n + foot[0], c_w + foot[1], "the foot two samples below the face",
                             reader=["the cliff reads as one rock face on a ramp, not a stair of terraces",
                                     "no seam, crack or hard edge across the cell border", "no stretched texture on the face",
                                     NORDIC])]
    return s


def stop_3(w: World, g: Ground) -> dict:
    x0, y0 = su.PROVINCE_CELL_SW
    best = None
    for cx in range(x0 + 1, x0 + su.PROVINCE_CELLS):
        for cy in range(y0 + 1, y0 + su.PROVINCE_CELLS):
            r, c = g.vertex(cx, cy, 0, 0)
            if g.H[r, c] < 10.0:  # land, clear of the water and the coast
                continue
            sl = g.slope_deg(r, c)
            if sl < 25.0 and (best is None or sl > best[0]):
                best = (sl, cx, cy, r, c)
    sl, cx, cy, r, c = best
    s = new_stop(3, "corner", "Four cells meet on a slope", "seams in height, normals and texture", (cx, cy), w)
    s["corner"] = {"cell_sw": [cx, cy], "slope_deg": round(sl, 1)}
    s["steps"] = [arrive(s, False), probe_step(g, "s03-probe-corner", r, c, "the shared corner vertex")]
    for tag, dr_, dc_ in (("ne", -1, 1), ("nw", -1, -1), ("se", 1, 1), ("sw", 1, -1)):
        s["steps"].append(probe_step(g, f"s03-probe-{tag}", r + dr_, c + dc_, f"one sample into the {tag.upper()} cell"))
    s["steps"][-1]["reader"] = ["the ground is one surface across all four cells: no step, crack or lighting seam on the lines",
                                "the ground texture runs across the lines without a hard edge", NORDIC]
    return s


def np_abs(a):
    import numpy as np
    return np.abs(a)


def np_argmax2(a):
    import numpy as np
    i = np.unravel_index(int(np.argmax(a)), a.shape)
    return int(i[0]), int(i[1])


def water_plan() -> dict:
    return json.loads(need(REPO / "out" / "water" / "plan.json").read_text())


def stop_4(w: World, g: Ground) -> dict:
    reach = water_plan()["sampleReach"]
    pieces = reach["pieces"]
    first, last = pieces[0], pieces[-1]
    r0, c0 = g.snap(first["eastM"], first["southM"])
    cell = g.cell(r0, c0)
    s = new_stop(4, "rapids", "A stepped river reach with rapids",
                 "step lines hidden, z-fighting, flow look", cell, w)
    s["reach"] = {"id": reach["id"], "length_m": reach["lengthM"], "drop_m": reach["dropM"], "pieces": len(pieces)}
    s["steps"] = [arrive(s, False)]
    for tag, p in (("top", first), ("bottom", last)):
        r, c = g.snap(p["eastM"], p["southM"])
        x, y, z = g.units(r, c)
        water_u = su.metres_to_units(p["zM"])
        tol = su.metres_to_units(TOL_M)
        s["steps"].append({
            "name": f"s04-{tag}-of-reach",
            "why": f"the {tag} of {reach['id']}: on the bed or the surface, not under the ground or in the air",
            "do": [probe_go(f"s04-{tag}-of-reach", x, y, max(z, water_u) + DROP_U), {"wait": 4}],
            "expect": [{"read": ["player"], "path": "pos.z", "ge": su.rounded(z - tol, 2), "within": 3},
                       {"read": ["player"], "path": "pos.z", "le": su.rounded(water_u + tol, 2), "within": 3},
                       {"read": ["player"], "path": "in_air", "eq": False, "within": 3}],
            "expected_ground_m": round(float(g.H[r, c]), 3), "expected_water_m": p["zM"]})
    s["steps"][-1]["reader"] = [
        "each step of the river reads as a short drop with water over it: no visible line where one sheet ends",
        "no z-fighting or flicker between two water sheets", "no sheet edge standing in the air",
        "the flow look: water moves downstream over the rapids pieces", "water colour reads fresh and green-brown, not blue"]
    return s


def piece_keys() -> dict:
    """The FormKeys the water plan places for its falls and mist pieces: the piece resolver's answer over the full
    dependency set's index (data/pieces-preference.json), never a record named here, so a change of preference or
    of the index cannot leave the stop counting no falls."""
    from tools.argonia_world import pieces as pz
    from tools.argonia_world.water import steps
    resolver = pz.Resolver(pz.Index.load(need(REPO / "out" / "pieces-index.json")))
    return {k: resolver.resolve(steps.PIECES[k][0])[0].form_key for k in ("falls", "mist")}


def stop_5(w: World, g: Ground) -> dict:
    mist, falls = [], []
    keys = piece_keys()
    for line in need(REPO / "out" / "water" / "cells.jsonl").read_text().splitlines():
        d = json.loads(line)
        for ref in d["refs"]:
            if ref["base"] == keys["mist"]:
                mist.append(ref["pos"])
            elif ref["base"] == keys["falls"]:
                falls.append(ref["pos"])
    ref_pt = water_plan()["sampleReach"]["pieces"][0]
    rx, ry = su.province_to_skyrim(ref_pt["eastM"], ref_pt["southM"])
    m = min(mist, key=lambda p: (p[0] - rx) ** 2 + (p[1] - ry) ** 2)  # the fall nearest the river stop
    near = [f for f in falls if (f[0] - m[0]) ** 2 + (f[1] - m[1]) ** 2 < 1200 ** 2]
    top_z = max(f[2] for f in near) if near else m[2]
    r, c = g.snap(*_province_m(m[0], m[1]))
    cell = su.cell_of(m[0], m[1])
    s = new_stop(5, "waterfall", "A waterfall", "the falls piece seated on the step", cell, w)
    s["falls"] = {"mist_at": [m[0], m[1]], "top_z": round(top_z, 1), "pieces_near": len(near)}
    s["steps"] = [arrive(s, False)]
    x, y, z = g.units(r, c)
    tol = su.metres_to_units(TOL_M)
    s["steps"].append({
        "name": "s05-at-the-falls",
        "why": "the player stands at the foot of the fall: on the ground (or swimming in its pool), below the lip",
        "do": [probe_go("s05-at-the-falls", x, y, max(z, 0) + DROP_U), {"wait": 4}],
        "expect": [{"read": ["player"], "path": "pos.z", "ge": su.rounded(z - tol, 2), "within": 3},
                   {"read": ["player"], "path": "pos.z", "le": su.rounded(top_z, 2), "within": 3}],
        "expected_ground_m": round(float(g.H[r, c]), 3),
        "reader": ["the falls piece stands on the step: its top meets the upper water and its foot the pool, no gap, no overhang in the air",
                   "mist at the foot", "the water above the lip and the pool below read as one river", NORDIC]})
    return s


def _province_m(x_u: float, y_u: float) -> tuple[float, float]:
    """Skyrim units back to province metres, by inverting the affine `province_to_skyrim` from two of its values."""
    x0, y0 = su.province_to_skyrim(0.0, 0.0)
    x1, y1 = su.province_to_skyrim(1.0, 1.0)
    return (x_u - x0) / (x1 - x0), (y_u - y0) / (y1 - y0)


def stop_6(w: World, g: Ground) -> dict:
    row = w.db.query(
        "SELECT b.id, b.deepest_x, b.deepest_y, b.area_m2, a.level_m, a.depth_m, a.id FROM hydrology_body b "
        "JOIN water_body_design d ON d.body_id = b.id JOIN water_basin a ON a.id = d.basin_id "
        "WHERE d.outcome = 'basin' AND a.outcome = 'kept' AND b.kind = 'marsh-deep' ORDER BY b.area_m2 DESC, b.id")[0]
    c, r = int(row[1]), int(row[2])
    level_u = su.metres_to_units(row[4])
    cell = g.cell(r, c)
    s = new_stop(6, "marsh", "A marsh basin", "the designed marsh level, no floating or missing water", cell, w)
    s["basin"] = {"body": row[0], "basin": row[6], "level_m": row[4], "depth_m": row[5], "area_m2": row[3]}
    x, y, z = g.units(r, c)
    tol = su.metres_to_units(TOL_M)
    s["steps"] = [arrive(s, False), {
        "name": "s06-deepest-point",
        "why": f"the deepest sample of {row[0]}: below the basin level {row[4]} m; the player stands on the bed or swims at the level",
        "do": [probe_go("s06-deepest-point", x, y, max(z, level_u) + DROP_U), {"wait": 4}],
        "expect": [{"read": ["player"], "path": "pos.z", "ge": su.rounded(z - tol, 2), "within": 3},
                   {"read": ["player"], "path": "pos.z", "le": su.rounded(level_u + tol, 2), "within": 3}],
        "expected_ground_m": round(float(g.H[r, c]), 3), "expected_water_m": row[4],
        "reader": ["a water surface at one level across the basin, reaching the reeds and the bank", "no floating plane over dry ground",
                   "no hole in the water where the basin is", "black-brown marsh colour", NORDIC]}]
    return s


def stop_7(w: World, g: Ground) -> dict:
    import numpy as np
    lake = w.db.query("SELECT id, deepest_x, deepest_y, level_m, area_m2 FROM hydrology_body "
                      "WHERE kind = 'lake-lowland' ORDER BY area_m2 DESC, id")[0]
    c, r = int(lake[1]), int(lake[2])
    level = float(lake[3])
    cc = c
    while cc > 0 and g.H[r, cc] < level:  # west along the row to the shore
        cc -= 1
    shore_c = cc - 3  # three samples inland, on the dry bank, walked on west to ground under 35 deg (game-18: the
    while shore_c > 0 and g.slope_deg(r, shore_c) >= 35.0:  # bank probe slid 14 m into the lake off a steep bank)
        shore_c -= 1
    s = new_stop(7, "lake-coast", "A lake shore and a coast", "banks, the sea default at 0, the apron through the haze",
                 g.cell(r, shore_c), w)
    s["lake"] = {"body": lake[0], "level_m": level, "area_m2": lake[4]}
    s["steps"] = [arrive(s, False), probe_step(g, "s07-lake-bank", r, shore_c, "dry bank three samples inland of the lake shore",
                                                reader=["the bank meets the water without a gap, step or floating edge",
                                                        "the lake surface is one level; shore texture is mud/sand/reed, not Nordic", NORDIC])]
    # the coast: a cell more than 30 % and under 70 % sea with a gentle slope; its middle row crosses the shore
    from tools.argonia_world.regions import cells as rc
    f = rc.load_or_compute()
    ok = np.argwhere((f["sea"] > 0.3) & (f["sea"] < 0.7) & (f["slope"] < 6.0))
    j, i = (int(v) for v in ok[0])
    ccx, ccy = rc.cell_of_index(i, j)
    rr = j * su.QUADS_PER_CELL + su.QUADS_PER_CELL // 2
    row = g.H[rr, i * su.QUADS_PER_CELL:(i + 1) * su.QUADS_PER_CELL + 1]
    land = np.nonzero(row >= 0.0)[0]
    sea = np.nonzero(row < 0.0)[0]
    if not len(land) or not len(sea):
        raise KeyError(f"cell {ccx},{ccy}: the middle row does not cross the coast")
    # the land sample next to the sea, then three samples back from the sea
    edge = int(land[np.argmin(np.abs(land - sea.mean()))])
    toward = 1 if sea.mean() > edge else -1
    shore_pt = i * su.QUADS_PER_CELL + edge - 3 * toward
    sea_pt = i * su.QUADS_PER_CELL + int(sea[np.argmin(np.abs(sea - edge))]) + 3 * toward
    s["coast"] = {"cell": [ccx, ccy], "sea_share": round(float(f["sea"][j, i]), 2)}
    s["steps"] += [{"name": "s07-coast-travel", "do": [*HOLD, {"console": travel(g, "s07-coast-arrive", ccx, ccy)}, {"wait": 8}], "expect": [in_world(7)]},
                   probe_step(g, "s07-coast-land", rr, shore_pt, "land three samples back from the sea edge"),
                   {"name": "s07-coast-sea",
                    "why": "three samples out in the sea: the sea default is level 0, no land above it",
                    "do": [probe_go("s07-coast-sea", *g.units(rr, sea_pt)[:2], su.metres_to_units(1.5)),
                           {"wait": 4}],
                    # not `swimming` (owner, 2026-10-31: swimming is base Skyrim): our part is no land above the sea
                    "expect": [{"read": ["player"], "path": "pos.z", "le": su.rounded(su.metres_to_units(1.5), 2), "within": 5}],
                    "reader": ["the sea meets the shore without a gap; the water plane is at one level",
                               "the apron beyond the coast fades through haze with no hard edge", NORDIC]}]
    return s


def stop_8(w: World, g: Ground) -> dict:
    summary = json.loads(need(REPO / "out" / "terrain" / "vegetation" / "summary.json").read_text())
    cx, cy, refs = summary["densest"][0]
    r, c = g.vertex(cx, cy, 16, 16)
    s = new_stop(8, "dense-vegetation", "The densest vegetation cell",
                 "frame time against the 0.2 §d bar, no Nordic flora (including the three vanilla rocks)", (cx, cy), w)
    s["cell"] = [cx, cy]
    s["vegetation"] = {"source": VEG_NOTE, "refs_in_cell": refs}
    from tools import run_journey as rj
    bars = rj.SOAK_BARS
    s["steps"] = [arrive(s, False), probe_step(g, "s08-probe-centre", r, c, f"the cell's centre vertex ({refs} vegetation refs)")]
    s["steps"].append({"name": "s08-frametime", "why": "the 0.2 section d bar: p50 at 60 fps, p99 at 45 fps, in the densest view",
                       "do": [{"wait": 3}],
                       "expect": [{"read": ["frametime", FRAMES], "path": "p50_ms", "le": round(bars["p50_ms"], 2), "within": 120},
                                  {"read": ["frametime", FRAMES], "path": "p99_ms", "le": round(bars["p99_ms"], 2), "within": 120}]})
    for k, deg in enumerate((0, 90, 180, 270)):
        st = {"name": f"s08-look-{deg:03d}", "do": [{"pad": "+RX=1:1100 -:100"}] if k else [],
              "expect": [{"read": ["player"], "path": "dead", "eq": False, "within": 2}]}
        if k == 3:
            st["reader"] = ["every tree and plant is Black Marsh flora (mangrove, cypress, palm, reeds, ferns); " + NORDIC,
                            "rocks read as marsh stone (wet, mossy), not northern granite", "trunks stand on the ground: none floating or sunk to the crown",
                            "no bare ground patch where the grass should run", "no pop-in line across the view"]
        s["steps"].append(st)
    return s


def _gate(w: World) -> dict:
    """The Tear road's exit gate as 2.W3 places it (routes/infra.py), with its reference EditorID."""
    from tools.argonia_world.routes import infra
    gate = next(p for p in infra.placements(w.db, lambda x, y: 0.0) if p["id"] == "gate.tear-road")
    return dict(gate, edid=infra.edid(gate))


def _before(ref: str, yaw_deg: float, back_m: float, side_m: float = 0.0) -> str:
    """`player.moveto` to `back_m` behind and `side_m` right of a reference facing `yaw_deg` (offsets are world axes)."""
    a = math.radians(yaw_deg)
    dx = -math.sin(a) * back_m + math.cos(a) * side_m
    dy = -math.cos(a) * back_m - math.sin(a) * side_m
    return f"player.moveto {ref} {su.rounded(su.metres_to_units(dx), 1)} {su.rounded(su.metres_to_units(dy), 1)} 0"


def stop_9(w: World, g: Ground) -> dict:
    from tools.argonia_world.terrain import edges
    poly = edges.border_polygon()
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    gate = _gate(w)
    inset = su.metres_to_units(30.0)
    # a west border segment, a third of the way down the province's west side
    seg_y_m = (su.PROVINCE_SAMPLES - 1) * su.PROVINCE_SAMPLE_M / 3
    wr, wc = g.snap(30.0, seg_y_m)
    seg_x, seg_y, seg_z = g.units(wr, wc)
    gr, gc = g.snap(gate["at_m"][0], gate["at_m"][1])
    gx, gy, gz = g.units(gr, gc)
    cell = su.cell_of(gx, gy)
    s = new_stop(9, "border", "A border segment and the Tear road gate",
                 "the player cannot leave; the closed-road message", cell, w)
    s["border"] = {"min_x": min(xs), "max_y": max(ys), "gate_pos": [gx, gy], "inset_u": round(inset, 1),
                   "gate_ref": gate["edid"]}
    push = [{"pad": "+LY=1:2900 -:100"} for _ in range(3)]
    face = round(gate["yaw"] % 360, 1)
    s["steps"] = [
        arrive(s, False),
        {"name": "s09-gate-push-north", "why": "5 m before the Tear road gate (20 m inside the border), facing out, "
                                               "walking at it for 9 s",
         "do": [{"console": _before(gate["edid"], gate["yaw"], 5.0)}, {"wait": 3},
                {"console": f"player.setangle z {face}"}, *push],
         "expect": [{"read": ["player"], "path": "pos.y", "le": max(ys), "within": 1},
                    {"read": ["player"], "path": "dead", "eq": False, "within": 1}],
         "reader": ["the road ends at a closed cypress gate across it; nothing beyond it is walkable; " + NORDIC]},
        {"name": "s09-gate-message", "why": "3 m before the gate, facing it, activate: the closed road's notice",
         "do": [{"console": _before(gate["edid"], gate["yaw"], 3.0)}, {"wait": 2},
                {"console": f"player.setangle z {face}"}, {"wait": 1}, {"key": "E 120"}, {"wait": 1}],
         "expect": [{"console": f"{gate['edid']}.GetDisabled", "contains": ">> 0"},
                    {"console": "player.HasPerk ARG_Perk_RoadClosed", "contains": ">> 1"}],
         "reader": [f"the notice reads \"{gate['message']}\" in our own words", "the crosshair named the gate \"Border Gate\""]},
        {"name": "s09-segment-travel", "do": [*HOLD, {"console": travel(g, "s09-segment-arrive", *g.cell(wr, wc))}, {"wait": 8}], "expect": [in_world(9)]},
        {"name": "s09-segment-push-west", "why": "30 m inside the west border, facing west, walking out for 9 s",
         "do": [probe_go("s09-segment-push-west", seg_x, seg_y, seg_z + DROP_U), {"wait": 3},
                {"console": "player.setangle z 270"}, *push],
         "expect": [{"read": ["player"], "path": "pos.x", "le": su.rounded(seg_x - 300, 2), "within": 1},
                    {"read": ["player"], "path": "pos.x", "ge": min(xs), "within": 1},
                    {"read": ["player"], "path": "dead", "eq": False, "within": 1}]}]
    return s


def stop_10(w: World, g: Ground) -> dict:
    from tools.argonia_world.routes import infra
    sign = w.db.query("SELECT s.id, s.x_m, s.y_m, s.yaw_deg, count(a.ord) n FROM signpost s "
                      "JOIN signpost_arm a ON a.signpost_id = s.id GROUP BY s.id ORDER BY n DESC, s.id")[0]
    texts = infra.arm_texts(w.db)
    arms = [(a["bearing_deg"], texts[(sign[0], a["ord"])])
            for a in w.db.query("SELECT ord, bearing_deg FROM signpost_arm WHERE signpost_id = ? ORDER BY ord", sign[0])]
    post = infra.edid({"id": sign[0], "kind": "signpost", "signpost": sign[0]})
    arm0 = infra.edid({"id": f"{sign[0]}.arm0", "kind": "arm", "signpost": sign[0]})
    r, c = g.snap(sign[1], sign[2])
    sx, sy, sz = g.units(r, c)
    yaw = math.radians(sign[3])
    d = su.metres_to_units(5.0)
    px, py = sx + math.sin(yaw) * d, sy + math.cos(yaw) * d
    pr, pc = g.snap(*_province_m(px, py))
    px, py, pz = g.units(pr, pc)
    heading = round((sign[3] + 180.0) % 360.0, 1)
    cell = su.cell_of(px, py)
    s = new_stop(10, "signpost", "A signpost at a junction", "sign text and arms", cell, w)
    s["signpost"] = {"id": sign[0], "post_ref": post, "arms": [[round(b, 1), n] for b, n in arms]}
    names = ", ".join(f"{n} ({b:.0f} deg)" for b, n in arms)
    # in front of arm 0's board (0.6 m out along it), 1.5 m to its right, looking at it and up to the board's height
    b0 = arms[0][0]
    look_up = round(-math.degrees(math.atan2(infra.ARM_TOP_M - 1.6, 1.5)), 1)
    a = math.radians(b0)
    out_dx, out_dy = math.sin(a) * 0.6 + math.cos(a) * 1.5, math.cos(a) * 0.6 - math.sin(a) * 1.5
    s["steps"] = [arrive(s, False), {
        "name": "s10-face-the-sign", "why": f"5 m in front of {sign[0]}, facing it",
        "do": [probe_go("s10-face-the-sign", px, py, pz + DROP_U), {"wait": 4}, {"console": f"player.setangle z {heading}"}, {"wait": 1}],
        "expect": [{"read": ["player"], "path": "pos.z", "ge": su.rounded(pz - su.metres_to_units(TOL_M), 2), "within": 3},
                   {"read": ["player"], "path": "pos.z", "le": su.rounded(pz + su.metres_to_units(TOL_M), 2), "within": 3}],
        "reader": [f"the signpost stands upright on the ground, with {len(arms)} arms", f"the arms point the way: {names}",
                   "wood and rope are marsh-made, not Nordic; any lettering on the boards is no Nordic rune or Skyrim "
                   "place name; " + NORDIC]},
        {"name": "s10-sign-text", "why": f"before arm 0 of {sign[0]}, looking at its board: the crosshair reads it",
         "do": [{"console": f"player.moveto {post} {su.rounded(su.metres_to_units(out_dx), 1)} "
                            f"{su.rounded(su.metres_to_units(out_dy), 1)} 0"}, {"wait": 2},
                {"console": f"player.setangle z {round((b0 - 90.0) % 360, 1)}"},
                {"console": f"player.setangle x {look_up}"}, {"wait": 1}],
         "expect": [{"console": f"{post}.GetDisabled", "contains": ">> 0"},
                    {"console": f"{arm0}.GetDisabled", "contains": ">> 0"}],
         "reader": [f"the crosshair reads \"{infra.ARM_VERB} {arms[0][1]}\" over the board",
                    f"the board points away from the post towards {b0:.0f} deg (the way to {arms[0][1]})"]}]
    return s


def stop_11(w: World, g: Ground, claywater: dict) -> dict:
    cell = tuple(claywater["cell"])
    s = new_stop(11, "weather-skip", "Weather: a 7-day skip at the Claywater block",
                 "the region's weather cycles; the light is green-gold", cell, w,
                 travel=claywater["travel"], hour=10, weather_cmd="sw", month=DRY_MONTH)
    s["steps"] = [arrive(s, False), {
        "name": "s11-day-0", "do": [{"wait": 3}],
        "expect": [{"read": ["weather"], "path": "current.id", "keep": "w0"}],
        "reader": ["the light is green-gold (tannin and canopy), not blue-white or grey-blue", "no snow, frost or Nordic sky", NORDIC]}]
    for d in range(1, 8):
        st = {"name": f"s11-day-{d}", "do": [{"game_hours": 24}], "expect": [{"read": ["weather"], "path": "current.id", "keep": f"w{d}"}]}
        if d == 7:
            st["expect"].append({"read": ["weather"], "path": "current.id", "ne": {"kept": "w0"}, "within": 8})
        if d == 3:
            st["reader"] = ["the light is green-gold or grey-green under this weather; no snow, frost or Nordic sky"]
        s["steps"].append(st)
    s["steps"] += [{"name": "s11-quarantine", "why": "after 7 days only the allowlist's quests run and only our silence plays",
                    "expect": [{"quests_running": {"allowed": "data/quarantine/allowed-quests.json"}, "within": 0},
                               {"music": {"allowed": ["ARG_MusicSilence"]}, "within": 0}]}]
    return s


def stop_12(w: World, g: Ground) -> dict:
    import numpy as np
    from tools.navmesh import paths, stitch
    root = REPO / "out" / "navmesh" / "claywater"
    need(root / "navm")
    place = w.db.get("place", "place.imperial-fringe.claywater-station")
    cx, cy = su.cell_of(*su.province_to_skyrim(place.position_m_x, place.position_m_y))
    assert CLAYWATER_BLOCK[0] <= cx <= CLAYWATER_BLOCK[2] and CLAYWATER_BLOCK[1] <= cy <= CLAYWATER_BLOCK[3]
    loaded = {(x, y) for x in range(cx - 2, cx + 3) for y in range(cy - 2, cy + 3)}  # the 5 x 5 the engine holds
    navms, cells = [], {}
    for x, y, fk, n in stitch.read_navm(root):
        if (x, y) in loaded:
            key = int(fk.split(":")[0], 16)
            navms.append((key, n))
            cells[key] = (x, y)
    graph = paths.Graph(navms)
    nodes = [(k, t) for k, n in graph.n.items() for t in range(len(n.tris["v"]))]
    seen, best = set(), set()
    for nd in nodes:  # the largest walkable component among the loaded cells
        if nd in seen:
            continue
        cc = graph.component_of(nd)
        seen |= cc
        if len(cc) > len(best):
            best = cc
    comp = sorted(best)
    water_flag = 0x0200
    water = [nd for nd in comp if int(graph.n[nd[0]].tris["flags"][nd[1]]) & water_flag]
    rng = np.random.default_rng(NAV_SEED)

    def point(nd):
        c = graph.cent[nd[0]][nd[1]]
        return [round(float(c[0]), 1), round(float(c[1]), 1), round(float(c[2]), 1)]

    def length(a, b):
        p = graph.path(a, b)
        if not p:
            return None
        pts = [graph.cent[k][t] for k, t in p]
        return float(sum(np.linalg.norm(pts[i + 1] - pts[i]) for i in range(len(pts) - 1)))

    pairs = []
    tries = 0
    while len(pairs) < NAV_PAIRS and tries < 5000:
        tries += 1
        a, b = comp[int(rng.integers(len(comp)))], comp[int(rng.integers(len(comp)))]
        d = float(np.linalg.norm(graph.cent[a[0]][a[1]][:2] - graph.cent[b[0]][b[1]][:2]))
        near = len(pairs) % 2 == 0  # half within about a cell, half across two to four
        if (near and not 200 < d < su.CELL_UNITS) or (not near and not 2 * su.CELL_UNITS < d < 4 * su.CELL_UNITS):
            continue
        ln = length(a, b)
        if ln:
            pairs.append((a, b, ln))
    if len(pairs) < NAV_PAIRS:
        raise KeyError(f"only {len(pairs)} reachable pairs drawn from the Claywater navmesh")
    swim = None
    if water:
        wnd = water[int(rng.integers(len(water)))]
        for _ in range(500):
            a = comp[int(rng.integers(len(comp)))]
            ln = length(a, wnd)
            if ln and ln > 400:
                swim = (a, wnd, ln)
                break
    s = new_stop(12, "navmesh", "Navmesh: 20 path requests across the block and one swim",
                 "walkable ground, door and water links", (cx, cy), w)
    s["navmesh"] = {"cells_loaded": sorted(map(list, loaded))[:1] + ["..."], "nodes_in_component": len(comp),
                    "water_triangles": len(water), "seed": NAV_SEED}
    s["steps"] = [arrive(s, False)]
    for k, (a, b, ln) in enumerate(pairs, 1):
        pa, pb = point(a), point(b)
        s["steps"].append({"name": f"s12-path-{k:02d}", "why": f"a path over the mesh, at most 1.5 x the centroid path ({ln:.0f} units)",
                           "expect": [{"read": ["nav", *pa, *pb], "path": "length", "gt": 0},
                                      {"read": ["nav", *pa, *pb], "path": "length", "le": round(1.5 * ln, 1)}],
                           "from": pa, "to": pb, "mesh_units": round(ln, 1)})
    if swim:
        a, b, ln = swim
        pa, pb = point(a), point(b)
        s["steps"].append({"name": "s12-path-swim", "why": "a path that ends on a water triangle",
                           "expect": [{"read": ["nav", *pa, *pb], "path": "length", "gt": 0},
                                      {"read": ["nav", *pa, *pb], "path": "length", "le": round(1.5 * ln, 1)}],
                           "from": pa, "to": pb, "mesh_units": round(ln, 1)})
    else:
        s["steps"].append({"name": "s12-path-swim", "owed": "the Claywater 5 x 5 has no water-flagged triangle in its main component",
                           "expect": [{"console": "player.GetInWorldspace ARG_Province", "contains": ">> 1"}]})
    s["steps"][-1]["reader"] = ["the player stands on the walkable ground at the block's centre, nothing floating or sunk"]
    return s


def stop_13(w: World, g: Ground) -> dict:
    import numpy as np
    win = g.window(*HIGH_CELL)
    i, j = np.unravel_index(int(np.argmax(win)), win.shape)
    r_s, c_w = g.vertex(*HIGH_CELL, 0, 0)
    r, c = r_s - su.QUADS_PER_CELL + int(i), c_w + int(j)
    s = new_stop(13, "distant-view", "A distant view from a high point",
                 "terrain and tree LOD, no missing tiles", HIGH_CELL, w,
                 prefer=("clear-humid", "dry-haze"))
    s["high_point_m"] = round(float(g.H[r, c]), 1)
    s["steps"] = [arrive(s, False), probe_step(g, "s13-probe-summit", r, c, f"the cell's highest vertex ({g.H[r, c]:.0f} m)"),
                  {"name": "s13-frametime", "why": "the 0.2 section d bar with the whole view loaded",
                   "do": [{"wait": 5}],
                   "expect": [{"read": ["frametime", FRAMES], "path": "p50_ms", "le": round(1000 / 60, 2), "within": 120},
                              {"read": ["frametime", FRAMES], "path": "p99_ms", "le": round(1000 / 45, 2), "within": 120}]}]
    for k, deg in enumerate((0, 90, 180, 270)):
        st = {"name": f"s13-view-{deg:03d}", "do": [{"pad": "+RX=1:1100 -:100"}] if k else [],
              "expect": [{"read": ["player"], "path": "dead", "eq": False, "within": 2}]}
        if k == 3:
            st["reader"] = ["distant terrain is present to the horizon in every direction: no missing tile, no hole showing sky",
                            "tree LOD is Black Marsh trees (mangrove, cypress, palm), thinning with distance; " + NORDIC,
                            "no hard edge where the near ground meets the LOD or where the apron meets the sea",
                            "no flicker or pop between terrain LOD levels"]
        s["steps"].append(st)
    return s


# --- assembly --------------------------------------------------------------------------------------------------
def build(w: World | None = None, g: Ground | None = None) -> list[dict]:
    w, g = w or World(), g or Ground()
    w.ground = g
    stops = [stop_1(w, g)]
    stops += [stop_2(w, g), stop_3(w, g), stop_4(w, g), stop_5(w, g), stop_6(w, g), stop_7(w, g), stop_8(w, g),
              stop_9(w, g), stop_10(w, g)]
    stops += [stop_11(w, g, stops[0]), stop_12(w, g), stop_13(w, g)]
    return stops


def journey(stops: list[dict]) -> dict:
    steps = []
    for s in stops:
        for st in s["steps"]:
            steps.append(st)
    return {"id": "world-sample", "runner": 1, "crash_risk": "high", "relaunch_before": True, "scene": stops[0]["scene"],  # travel across the province
            "stops": [{"n": s["n"], "title": s["title"], "scene": s["scene"], "cell": s["cell"],
                       "region": s["weather"]["region"], "weather": s["weather"]["edid"],
                       **{k: s[k] for k in ("cliff", "corner", "reach", "falls", "basin", "lake", "coast", "vegetation", "border",
                                            "signpost", "navmesh", "high_point_m") if k in s}} for s in stops],
            "steps": steps}


HEADER = """# The world track's in-game sample (docs/phases/1-core-loop/README.md): 13 stops, one journey, run once per world-track
# change set on one machine. GENERATED by tools/world_sample.py from the world database, the terrain, the water plan
# and the navmesh: edit the generator and run `python3 tools/world_sample.py --write`, never this file.
# Each stop's scene (tests/scenes/world-sample-NN-*.txt) ends with its travel line; the journey applies it with
# `bat` (make deploy sends every scene; the runner sends the first). Expected ground z is in game units, from the LAND
# vertices (terrain build.game_heights_m), within 0.5 m. Steps with `reader:` list what a `reader` checks on the still.
"""


def render() -> dict[Path, str]:
    import yaml
    w, g = World(), Ground()
    PROBES.clear()
    stops = build(w, g)
    render.world = w
    files = {JOURNEY: HEADER + yaml.safe_dump(journey(stops), sort_keys=False, width=140, allow_unicode=True)}
    for s in stops:
        files[SCENES / f"{s['scene']}.txt"] = scene_text(s)
    return files


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    try:
        files = render()
    except Missing as e:
        print(f"world_sample: data not on this machine: {e}", file=sys.stderr)
        return 2
    probes_ok = sync_probes(render.world.db, a.write)
    if a.write:
        for p, t in files.items():
            p.write_bytes(t.encode())
        print(f"wrote {len(files)} files")
        return 0
    stale = [str(p.relative_to(REPO)) for p, t in files.items() if not p.exists() or p.read_bytes() != t.encode()]
    if not probes_ok:
        stale.append("the probe markers (build_ref rows)")
    if stale:
        print("stale (run tools/world_sample.py --write): " + ", ".join(stale))
        return 1
    print(f"{len(files)} files current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
