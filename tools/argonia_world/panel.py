"""The world panel (1.15 §0, §f; decision 0033 §5): two fixed vantages per exterior region class, picked once from the
generated data and written as a runnable scene and journey, the in-game oracle of the rebuilt world.

Per eco class (`eco_class` rows with land regions in `cell_region_run`):
- **shore**: on dry ground (0.5 to 3 m above its cell's solved water, `cell_water`) within 4 samples of water of the
  class's commonest water type, the candidate nearest the class's centroid, facing the water;
- **high**: the class's highest ground sample, facing the compass direction whose ground 300 to 1500 m out is lowest
  (the longest view).
Each still pair is noon and dawn under the land region's weathers (`regions.panel_weather`). The vantages are fixed
by cell and position once written; `--write` refuses to move them (pass `--force` after a ruling).

    python3 -m tools.argonia_world.panel            prints the vantages as JSON lines
    python3 -m tools.argonia_world.panel --write    writes tests/scenes/world-panel.txt and tests/journeys/world-panel.yaml
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

from tools.argonia_world import db
from tools.argonia_world import skyrim_units as su

ROOT = Path(__file__).resolve().parents[2]
SCENE = ROOT / "tests" / "scenes" / "world-panel.txt"
JOURNEY = ROOT / "tests" / "journeys" / "world-panel.yaml"
N = su.PROVINCE_SAMPLES - 1          # 4032
Q = su.QUADS_PER_CELL                 # 32
C = su.PROVINCE_CELLS                 # 126
CX0, CY0 = su.PROVINCE_CELL_SW
MPP = su.PROVINCE_SAMPLE_M
SHORE_LO_M, SHORE_HI_M, SHORE_REACH = 0.5, 3.0, 4  # dry ground just above the water, within 4 samples (7 m) of it
VIEW_NEAR_M, VIEW_FAR_M = 300.0, 1500.0
EDGE_CELLS = 3                        # a vantage stays 3 cells inside the province edge (no apron seam in frame)
EYE_M = 0.23                          # the player is put this far above the ground (tools/journeys SEAT_U)
LAND_TOL_UNITS = 300                  # the teleport landed: the player within this of the vantage in x and y
# A `cow` grid change crashed the culling job and a raw `teleport pos` across cells likewise (diag5-g17 §2,
# tools/tests/test_world_sample.py): each vantage is a persistent XMarker (`build_ref` rows `ref.panel.<id>` in
# MARKER_CELL, synced by `--write` through db.py, emitted by `make plugin`) and the player arrives by `player.moveto`.
MARKER_CELL = "cell.studio.world-panel"


def _dilate(m: np.ndarray, r: int) -> np.ndarray:
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dy or dx:
                out |= np.roll(np.roll(m, dy, 0), dx, 1)
    return out


def _cell_rasters(w):
    """Per cell (row 0 north): eco class index, land region id, water level (NaN none), water type."""
    cls = np.full((C, C), "", object)
    reg = np.full((C, C), "", object)
    eco = {r["id"]: r["eco_class_id"] for r in w.query("SELECT id, eco_class_id FROM land_region WHERE border = 0")}
    for r in w.query("SELECT * FROM cell_region_run"):
        i = C - 1 - (r["cy"] - CY0)
        if 0 <= i < C and eco.get(r["land_region_id"]):
            a, b = max(r["cx0"] - CX0, 0), min(r["cx1"] - CX0 + 1, C)
            cls[i, a:b] = eco[r["land_region_id"]]
            reg[i, a:b] = r["land_region_id"]
    lev = np.full((C, C), np.nan, np.float32)
    typ = np.full((C, C), "", object)
    for r in w.query("SELECT cx, cy, level_m, water_type FROM cell_water"):
        i, j = C - 1 - (r["cy"] - CY0), r["cx"] - CX0
        if 0 <= i < C and 0 <= j < C:
            lev[i, j], typ[i, j] = r["level_m"], r["water_type"]
    return cls, reg, lev, typ


def _up(a: np.ndarray) -> np.ndarray:
    """A (126, 126) cell raster as the (4033, 4033) sample raster (the last row and column repeat their neighbour)."""
    s = np.repeat(np.repeat(a, Q, 0), Q, 1)
    return np.pad(s, ((0, 1), (0, 1)), mode="edge")


def _yaw(dx_m: float, dy_south_m: float) -> float:
    """Skyrim heading (0 north, clockwise) of a province direction (x east, y south)."""
    return math.degrees(math.atan2(dx_m, -dy_south_m)) % 360


def vantages(w=None, ground: np.ndarray | None = None) -> list[dict]:
    from tools.argonia_world.terrain.grid import Sources
    from tools.argonia_world.regions import panel_weather

    w = w if w is not None else db.open()
    g = np.asarray(ground if ground is not None else Sources.load().ground, np.float32)
    cls, reg, lev, typ = _cell_rasters(w)
    weather = {r["land_region"]: r for r in panel_weather.table(w)}
    level = _up(lev)
    wet = g < level                                    # NaN level compares False: no water
    rows, cols = np.mgrid[0:N + 1, 0:N + 1]
    inner = np.zeros_like(wet)
    inner[EDGE_CELLS * Q:N + 1 - EDGE_CELLS * Q, EDGE_CELLS * Q:N + 1 - EDGE_CELLS * Q] = True
    out = []
    for k in sorted({c for c in cls.ravel() if c}):
        in_cls = _up(cls == k) & inner
        kinds = typ[(cls == k) & (typ != "")]
        if not kinds.size:
            continue
        kind = max(sorted(set(kinds)), key=lambda t: int((kinds == t).sum()))
        near = _dilate(wet & _up(typ == kind), SHORE_REACH)
        klev = _up(np.where(typ == kind, lev, np.nan))  # the cell's own water, where it is of the kind
        above = g - klev
        cand = in_cls & near & ~wet & (above >= SHORE_LO_M) & (above <= SHORE_HI_M)
        cy_, cx_ = rows[in_cls].mean(), cols[in_cls].mean()
        picks = []
        if cand.any():
            rr, cc = np.nonzero(cand)
            n = int(np.argmin((rr - cy_) ** 2 + (cc - cx_) ** 2))
            r, c = int(rr[n]), int(cc[n])
            win = wet[max(r - 8, 0):r + 9, max(c - 8, 0):c + 9]
            wy, wx = np.nonzero(win)
            dy = (wy + max(r - 8, 0)).mean() - r
            dx = (wx + max(c - 8, 0)).mean() - c
            picks.append(("shore", r, c, _yaw(dx, dy)))
        hg = np.where(in_cls, g, -np.inf)
        r, c = (int(v) for v in np.unravel_index(int(np.argmax(hg)), hg.shape))
        best = None
        for deg in range(0, 360, 45):
            sx, sy = math.sin(math.radians(deg)), -math.cos(math.radians(deg))  # sy: south positive
            d = np.arange(VIEW_NEAR_M, VIEW_FAR_M, 50.0) / MPP
            pr = np.clip(np.rint(r + sy * d).astype(int), 0, N)
            pc = np.clip(np.rint(c + sx * d).astype(int), 0, N)
            m = float(g[pr, pc].mean())
            if best is None or m < best[0]:
                best = (m, float(deg))
        picks.append(("high", r, c, best[1]))
        for view, r, c, yaw in picks:
            x_m, y_m = c * MPP, r * MPP
            x, y = su.province_to_skyrim(x_m, y_m)
            z_m = float(g[r, c])
            ci, cj = min(r // Q, C - 1), min(c // Q, C - 1)
            lr = reg[ci, cj]
            wx_ = weather.get(lr)
            out.append({"id": f"{k}-{view}", "eco_class": k, "view": view, "water_type": kind,
                        "land_region": lr, "cell": [CX0 + cj, CY0 + (C - 1 - ci)],
                        "x_m": round(x_m, 2), "y_m": round(y_m, 2), "ground_m": round(z_m, 2),
                        "water_m": None if math.isnan(lev[ci, cj]) else round(float(lev[ci, cj]), 2),
                        "pos": [round(x), round(y), round((z_m + EYE_M) * su.UNITS_PER_METRE)], "yaw_deg": round(yaw),
                        "noon": wx_["noon"]["edid"] if wx_ else None, "dawn": wx_["dawn"]["edid"] if wx_ else None})
    return out


def marker_ref(v: dict) -> str:
    return f"ref.panel.{v['id']}"


def marker_edid(v: dict) -> str:
    from tools.argonia_world.place_build import ref_edid
    return ref_edid(marker_ref(v))


def marker_rows(vs: list[dict]) -> list[dict]:
    return [{"id": marker_ref(v), "cell_id": MARKER_CELL, "base": su.ENGINE_MARKER_HEADING, "x_m": v["x_m"],
             "y_m": v["y_m"], "z_m": round(v["ground_m"] + EYE_M, 3), "yaw_deg": float(v["yaw_deg"]), "persistent": True,
             "why": f"world-panel vantage {v['id']} (tools/argonia_world/panel.py)"} for v in vs]


def sync_markers(w, vs: list[dict], write: bool) -> bool:
    """True when the DB's vantage markers match the vantages; with `write`, make them match and save."""
    from tools.argonia_world.vegetation.build import PROBE_PLACE  # the footprints skip the studio markers' place
    have = {r["id"]: dict(r) for r in w.query("SELECT * FROM build_ref WHERE cell_id = ?", MARKER_CELL)}
    want = {r["id"]: r for r in marker_rows(vs)}
    same = set(have) == set(want) and all(
        all(have[k][c] == v or (isinstance(v, float) and abs(have[k][c] - v) < 1e-6) for c, v in r.items())
        for k, r in want.items())
    if same or not write:
        return same
    if w.get("place", PROBE_PLACE) is None:
        w.insert("place", id=PROBE_PLACE, name="World sample probes")
    if w.get("build_cell", MARKER_CELL) is None:
        w.insert("build_cell", id=MARKER_CELL, place_id=PROBE_PLACE, kind="exterior")
    for k in have:
        w.delete("build_ref", k)
    for r in want.values():
        w.insert("build_ref", **r)
    w.save()
    return True


def scene_text(vs: list[dict]) -> str:
    v = vs[0]
    lines = ["; the world panel (1.15 §0; tools/argonia_world/panel.py writes it): the first vantage, staged last",
             "tgm", "tcai",   # god mode and no AI at step 0: the player is neither harmed nor engaged during the stills
             "set gamehour to 12", f"player.moveto {marker_edid(v)}"]
    return "\r\n".join(lines) + "\r\n"


def journey_text(vs: list[dict]) -> str:
    from tools.journeys import look   # the scan of headings each look stop takes (look.SCAN)
    head = ("# The world panel (1.15 §0, §f; decision 0033 §5), written by `python3 -m tools.argonia_world.panel --write`\n"
            "# from the generated data: two fixed vantages per region class (shore: dry ground beside water of the\n"
            "# class's commonest kind; high: the class's highest point, facing its longest view), each at noon (the\n"
            "# region's clear-dry) and dawn 06:30 (its mist regime's weather), first person (`camera: first`, waited\n"
            "# for), the HUD `hud: off`. Read by a `reader` with the 1.15 §0 checklist and feel question, docs/design/world/vibe-board.md the\n"
            "# vibe check (not the bar), and god rays and volumetric fog where the weather has them (dawn mist over\n"
            "# water; light shafts through canopy; owner, 2026-11-01); each step\n"
            "# checks only that the teleport landed. The vantages are re-derived from each build and pulled out of foliage\n"
            "# (`python3 -m tools.journeys refresh`).\n")
    steps = [{"name": "first-person-no-hud", "setup": True, "do": [{"wait": 10}, {"hud": "off"}],
              "expect": []}]
    wthr = {r.editor_id: (r.plugin, r.form_id) for r in db.open().rows("formid") if r.record_type == "WTHR"}
    for v in vs:
        x, y, z = v["pos"]
        land = [{"console": "player.GetInWorldspace ARG_Province", "contains": ">> 1"},
                {"read": ["player"], "path": "pos.x", "gt": x - LAND_TOL_UNITS},
                {"read": ["player"], "path": "pos.x", "lt": x + LAND_TOL_UNITS},
                {"read": ["player"], "path": "pos.y", "gt": y - LAND_TOL_UNITS},
                {"read": ["player"], "path": "pos.y", "lt": y + LAND_TOL_UNITS}]
        for when, hour in (("noon", 12), ("dawn", 6.5)):
            do = [{"hud": "off"},
                  {"console": {"line": f"player.moveto {marker_edid(v)}", "settle": 60}},
                  {"console": f"player.setangle z {v['yaw_deg']:.0f}"},
                  {"console": "player.setangle x 0"}, {"console": "player.setangle y 0"}, {"console": f"set gamehour to {hour}"}]
            # `sw` (set, no transition) after the moveto's settle: the region's own list had replaced `fw`'s weather
            # (round 3: storm, wet_rain from vanilla ClearCO); the bridge `weather` read proves the sky took it
            # before the still (a null read means a menu is open: it is polled until it holds)
            ex = list(land)
            if v[when]:
                # the weather by its runtime form id (`<plugin>|0x<id>`, resolved by the runner: `sw <editor id>` left
                # the region's own pick in place twice in round 4), set then forced so the region list cannot replace it
                fid = wthr.get(v[when])
                ref = f"{fid[0]}|0x{fid[1]:06X}" if fid else v[when]
                do.append({"console": f"sw {ref}"})
                do.append({"console": f"fw {ref}"})
                ex.append({"read": ["weather"], "path": "current.editor_id", "eq": v[when], "within": 20})
            # the measured settle, not 14 s of fixed waits (1.15-r4-fast-loop): menus closed and the player still,
            # at least 3 s for the sky and near textures after `sw`, capped at the old 14 s
            do += [{"settle": {"cap": 14, "min": 3}}]
            steps.append({"name": f"{v['id']}-{when}", "scan": look.SCAN, "do": do, "expect": ex})
    # reach: the records and cells are added by tools/journeys/reach_records.py (refresh)
    j = {"id": "world-panel", "look": "world", "reach": ["tests/scenes/world-panel.txt", "data/dependencies.json"],
         "independent_steps": True, "runner": 1, "crash_risk": "medium", "scene": "world-panel", "camera": "first",
         "steps": steps}
    from tools.journeys import aims   # a reader-named heading for a stop (tests/journeys/aims.yaml)
    marks = {marker_edid(v): tuple(v["pos"][:2]) for v in vs}
    return aims.apply_text("world-panel", head + json.dumps(j, indent=1) + "\n", marks.get)  # JSON is YAML; one writer


def main(argv: list[str]) -> int:
    vs = vantages()
    if "--write" not in argv:
        for v in vs:
            print(json.dumps(v))
        return 0
    if JOURNEY.is_file() and "--force" not in argv and '"runner": 1' in JOURNEY.read_text():
        old = [s["name"] for s in json.loads("".join(ln for ln in JOURNEY.read_text().splitlines(True) if not ln.startswith("#")))["steps"]]
        if old != ["first-person-no-hud"] + [f"{v['id']}-{t}" for v in vs for t in ("noon", "dawn")]:
            print("world-panel: the vantages are fixed; pass --force after a ruling", file=sys.stderr)
            return 1
    w = db.open()
    sync_markers(w, vs, True)
    SCENE.write_bytes(scene_text(vs).encode())
    JOURNEY.write_text(journey_text(vs))
    print(f"{len(vs)} vantages -> {SCENE.relative_to(ROOT)}, {JOURNEY.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
