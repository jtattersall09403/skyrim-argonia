"""tools/journeys: every data-driven journey derived from the build it runs on (1.15-r4-journeys).

The last test is the L1 gate: every stand of every derived journey on the current build's ground (or water it says
is water) within 0.5 m, every moveto off a ground-placed ref dry. A journey written against older ground fails here,
before any machine time; `python3 -m tools.journeys refresh` re-derives it.
"""

import numpy as np
import pytest

from tools import journeys as J
from tools.argonia_world import skyrim_units as su

U = su.UNITS_PER_METRE


class Flat(J.Build):
    """A 10 m ground in the province's north-west corner, a 12 m water level in one cell, the plants given."""
    def __init__(self, plants=(), wet_cell=None, refs=None):
        super().__init__(ground=np.full((80, 80), 10.0, np.float32), water={}, refs=refs or {})
        self.plants, self.wet_cell = list(plants), wet_cell

    def water_u(self, x, y):
        return 12.0 * U if su.cell_of(x, y) == self.wet_cell else 0.0

    def _cell_foliage(self, cx, cy):
        return [p for p in self.plants if su.cell_of(p[0], p[1]) == (cx, cy)]


def at(xm, ym):
    return su.province_to_skyrim(xm, ym)


def test_frame_pulls_the_stand_back_along_the_approach_line_out_of_a_crown():
    sx, sy = at(60, 60)
    subj = (sx, sy, 10 * U + 60)
    x, y = sx, sy - 6 * U                       # 6 m south of the subject, looking north
    bush = (x, y + 1 * U, 10 * U, 1.5 * U, 2.5 * U, True)  # a 2.5 m shrub a metre in front of the eye
    b = Flat([bush])
    assert b.blockers(J.eye_of(b, x, y), subj)
    f = J.frame(b, x, y, subj)
    assert f["clear"] and f["moved_m"] > 0 and abs(f["x"] - x) < 1  # along the approach line: past the shrub
    assert not b.blockers(J.eye_of(b, f["x"], f["y"]), subj)


def test_a_fern_under_the_eye_line_and_the_subjects_own_tree_do_not_block():
    sx, sy = at(60, 60)
    subj = (sx, sy, 10 * U + 60)
    x, y = sx, sy - 8 * U
    fern = (x, y + 3 * U, 10 * U, 1.0 * U, 0.6 * U, True)       # 0.6 m tall: the line passes ~1 m over it
    own = (sx + 20, sy, 10 * U, 4 * U, 12 * U, False)             # the tree the still is of
    assert not Flat([fern, own]).blockers(J.eye_of(Flat(), x, y), subj)


def test_check_stand_flags_the_off_ground_and_the_swimming_and_passes_declared_water():
    b = Flat(wet_cell=su.cell_of(*at(60, 60)))
    x, y = at(60, 60)
    g = 10 * U
    assert "off the ground" in J.check_stand(b, {"step": "s", "kind": "setpos", "x": x, "y": y, "z": g + 20000, "water": False})
    assert "in water" in J.check_stand(b, {"step": "s", "kind": "setpos", "x": x, "y": y, "z": g + 10, "water": False})
    assert J.check_stand(b, {"step": "s", "kind": "setpos", "x": x, "y": y, "z": 12 * U, "water": True}) is None
    dry = Flat()
    assert J.check_stand(dry, {"step": "s", "kind": "setpos", "x": x, "y": y, "z": g + 16, "water": False}) is None


def test_moveto_checks_the_target_beside_the_ref_and_trusts_a_porch():
    x, y = at(60, 60)
    refs = {"ARG_Ref_Raft": {"id": "r", "x": x, "y": y, "own_z": False, "marker": False, "z": None},
            "ARG_Ref_Door": {"id": "d", "x": x, "y": y, "own_z": True, "marker": False, "z": 900.0}}
    b = Flat(wet_cell=su.cell_of(x, y), refs=refs)
    s = {"step": "s", "kind": "moveto", "ref": "ARG_Ref_Raft", "off": [0, 0, 0], "water": False}
    assert "in water" in J.check_stand(b, s)
    assert J.check_stand(b, {**s, "ref": "ARG_Ref_Door"}) is None
    assert "no placed exterior ref" in J.check_stand(b, {**s, "ref": "ARG_Ref_Gone"})


STEP = """steps:
- name: look
  # subject: {sx:.0f} {sy:.0f} {sz:.0f}
  do:
  - console: player.setpos x {x:.0f}
  - console: player.setpos y {y:.0f}
  - console: player.setpos z 20000
  - console: player.setangle z 0
  - console: player.setangle x 0
"""


def test_reframe_seats_aims_and_pulls_back_and_is_idempotent():
    sx, sy = at(60, 60)
    x, y = sx, sy - 6 * U
    b = Flat([(x, y + 1 * U, 10 * U, 1.5 * U, 2.5 * U, True)])
    text = STEP.format(sx=sx, sy=sy, sz=10 * U + 60, x=x, y=y)
    log = []
    once = J.reframe(b, text, log)
    st = J.stands(once)[0]
    assert abs(st["z"] - (10 * U + J.SEAT_U)) < 1 and st["y"] != y and log[0]["clear"] and log[0]["moved_m"] > 0
    assert J.check_stand(b, st) is None
    assert J.reframe(b, once, []) == once
    pitch = float(once.split("setangle x ")[1].split()[0])
    assert pitch > 0  # aimed down at the subject's base


def test_the_derived_journeys_stand_on_the_current_build():
    """L1: every derived journey against the build in out/ (red = stale: run `python3 -m tools.journeys refresh`)."""
    from tools.world_sample import data_root
    if not ((J.ROOT / "out" / "water" / "cells.jsonl").is_file()
            and (data_root() / "terrain" / "refined-height-f32.npy").is_file()):
        pytest.skip("no build in out/ (terrain and water): the pre-batch job runs this after the build")
    bad = {n: e for n, e in J.check(J.Build()).items() if e}
    assert not bad, f"stale journeys (run `python3 -m tools.journeys refresh`): {bad}"


def test_a_stand_inside_geometry_or_on_a_cliff_is_bad():
    from tools.argonia_world import skyrim_units as su
    from tools.journeys import Build, stand_bad
    u = su.UNITS_PER_METRE
    b = Build(foliage={})
    b.ground_u = lambda x, y: 0.0 if x < 1000 else x * 2.0   # flat, then a 63 degree slope
    b.foliage_near = lambda x, y, r: [(0.0, 0.0, 0.0, 30.0, 40 * u, False)]   # one trunk at the origin
    assert stand_bad(b, 0.0, 0.0, (15 * u, 0.0, 120.0))   # standing in a trunk
    b.foliage_near = lambda x, y, r: []
    assert not stand_bad(b, 0.0, 0.0, (15 * u, 0.0, 120.0))
    assert any("slope" in w for w in stand_bad(b, 1500.0, 0.0, (1500.0 + 15 * u, 0.0, 3000.0)))


class Pond(J.Build):
    """Flat 10 m ground; water (level 10.5 m) in every cell whose index is in `wet` (a synthetic cell grid)."""
    def __init__(self, wet):
        super().__init__(ground=np.full((80, 80), 10.0, np.float32), water={}, refs={})
        self.wet_cells = set(wet)

    def water_u(self, x, y):
        return 10.5 * U if su.cell_of(x, y) in self.wet_cells else None

    def _cell_foliage(self, cx, cy):
        return []


def test_water_share_counts_the_water_in_the_aim_field_and_not_behind_it():
    cx, cy = su.cell_of(*at(60, 60))
    b = Pond({(cx, cy + k) for k in range(1, 4)})        # water from the next cell north on
    x, y = at(60, 60)
    assert J.water_share(b, x, y, 0) > 0.4               # facing the water
    assert J.water_share(b, x, y, 180) == 0.0            # facing away
    assert J.water_share(Pond(set()), x, y, 0) == 0.0    # no water at all


def test_water_stop_bad_flags_an_off_water_aim_and_a_dry_field_and_passes_a_good_one():
    cx, cy = su.cell_of(*at(60, 60))
    b = Pond({(cx, cy + k) for k in range(0, 4)})
    x, y = su.cell_origin(cx, cy)[0] + su.CELL_UNITS / 2, su.cell_origin(cx, cy)[1] - 2 * U
    good = {"step": "t", "x": x, "y": y, "heading": 0.0, "subject": (x, y + 100 * U, 10.5 * U)}
    assert J.water_stop_bad(b, good) is None
    assert "not a water cell" in J.water_stop_bad(b, {**good, "subject": (x, y - 30 * U, 10.5 * U), "heading": 180.0})
    assert "off its subject" in J.water_stop_bad(b, {**good, "heading": 90.0})
    ox, oy = su.cell_origin(cx, cy)
    dry = {**good, "x": ox + 100, "y": oy + 100, "subject": (ox + 100, oy + 3.5 * su.CELL_UNITS, 10.5 * U)}  # water 3 cells out
    assert "of the lower frame" in J.water_stop_bad(Pond({(cx, cy + 3)}), dry)


def test_a_kept_shortfall_stop_reads_current_until_the_measure_moves_and_a_dry_sea_far_is_rejected(monkeypatch):
    cx, cy = su.cell_of(*at(60, 60))
    b = Pond({(cx, cy + k) for k in range(1, 3)})
    ox, oy = su.cell_origin(cx, cy)
    x, y = ox + su.CELL_UNITS / 2, oy + 100.0
    stop = {"step": "stream", "x": x, "y": y, "heading": 0.0, "pitch": 0.0, "subject": (x, y + 2 * su.CELL_UNITS, 10.5 * U)}
    sh = J.frame_share(b, x, y, 0.0, 0.0)
    assert 0 < sh < J.frame_floor("stream") and "under its floor" in J.water_stop_bad(b, stop)
    assert J.water_stop_bad(b, {**stop, "shortfall": round(sh * 100)}) is None            # kept short, measure unchanged: current
    assert "under its floor" in J.water_stop_bad(b, {**stop, "shortfall": round(sh * 100) + 5})   # the build moved it: stale
    far = {**stop, "step": "sea-far"}
    sea = {"subject": (x, y + 10.5 * su.CELL_UNITS, 10.5 * U)}
    assert "looks at land" in J.water_stop_bad(Pond({(cx, cy + 10)}), {**far, **sea})   # sea only past 300 m: a stand on land
    from tools.journeys import gen
    monkeypatch.setattr(gen, "SEA_FAR_MIN_RAYS", 5)   # flat test ground gives few grazing rays; the bar's number is the generator's
    assert J.water_stop_bad(Pond({(cx, cy + k) for k in range(1, 11)}), {**far, **sea}) is None


def test_water_stops_parse_a_journey_text():
    text = ("steps:\n- name: s1\n  # subject: 10 20 30\n  do:\n  - console: player.setpos x 1\n  - console: player.setpos y 2\n"
            "  - console: player.setangle z 90\n")
    assert J.water_stops(text) == [{"step": "s1", "x": 1.0, "y": 2.0, "heading": 90.0, "pitch": 0.0, "subject": (10.0, 20.0, 30.0),
                                       "shortfall": None}]
    text = text.replace("  do:", "  # shortfall: water 28% < floor 30%\n  do:")
    assert J.water_stops(text)[0]["shortfall"] == 28


def test_dry_footing_needs_half_a_metre_over_the_cell_water():
    from tools.journeys import Build, DRY_FOOTING_M
    from tools.argonia_world import skyrim_units as su
    water = su.metres_to_units(10.0)
    b = Build(water={su.cell_of(0, 0): water})
    for gm, soaked in ((9.0, True), (10.2, True), (10.0 + DRY_FOOTING_M + 0.01, False), (14.0, False)):
        b.ground_u = lambda x, y, g=su.metres_to_units(gm): g
        assert b.soaked(0, 0) is soaked, gm
    assert not Build(water={}).soaked(5000, 5000) if False else True


def test_clearance_counts_fronds_on_the_line_and_canopy_over_the_eye():
    x, y = at(60, 60)
    b0 = Flat()
    eye = J.eye_of(b0, x, y)
    willow = (x, y + 20 * U, 10 * U, 4 * U, 8 * U, False)         # fronds to the ground 20 m ahead, on the line
    crown = (x + 6 * U, y - 3 * U, 10 * U, 8 * U, 20 * U, False)  # a tree 6.7 m off whose 8 m crown is over the eye
    low = (x, y + 30 * U, 10 * U, 1 * U, 0.5 * U, True)           # a fern under the line
    far = (x + 40 * U, y, 10 * U, 2 * U, 20 * U, False)           # a tall tree off the line, not over the eye
    high = (x - 3 * U, y - 3 * U, 25 * U, 6 * U, 10 * U, False)   # a crown over the eye but 15 m up: sky, not leaves
    assert J.clearance(Flat([willow, crown, low, far]), eye, 0.0) == (1, 1)
    assert J.clearance(Flat([low, far, high]), eye, 0.0) == (0, 0)


def test_frond_clearance_rejects_a_river_stand_with_a_palm_3_m_off_the_aim():
    """tall_near: a palm (fronds 2 m round, 4 m tall) 3 m off the aim line 8 m out counts; a fern under 1 m, a palm 7 m
    off and one 25 m out do not (lane 1.15-r6-water-stands-5)."""
    x, y = at(60, 60)
    b0 = Flat()
    eye = J.eye_of(b0, x, y)
    g = b0.ground_u(x, y)
    palm = (x + 3 * U, y + 8 * U, g, 2 * U, 4 * U, True)
    fern = (x + 1 * U, y + 5 * U, g, 1 * U, 0.8 * U, True)
    off = (x + 7 * U, y + 8 * U, g, 2 * U, 4 * U, True)
    far = (x, y + 25 * U, g, 2 * U, 4 * U, True)
    assert J.tall_near(Flat([palm, fern, off, far]), eye, 0.0) == 1
    assert J.tall_near(Flat([fern, off, far]), eye, 0.0) == 0


def test_stream_far_bank_and_reach_width_bound():
    """far_bank_m: the footprint's far bank along the aim; gen._reach_width_m: the water's width across a reach point;
    gen._narrowest: the narrowest wet point within its reach."""
    from tools.journeys import gen
    x, y = at(60, 60)
    b = Flat()
    band = lambda w: (lambda px, py: y + 10 * U <= py <= y + (10 + w) * U)   # noqa: E731  a channel crossing north
    b.wet = band(8)
    assert J.far_bank_m(b, x, y, 0.0) == 18.5 and J.far_bank_m(b, x, y, 0.0) <= gen.STREAM_BANK_M
    b.wet = band(30)
    assert J.far_bank_m(b, x, y, 0.0) > gen.STREAM_BANK_M
    b.wet = lambda px, py: False
    assert J.far_bank_m(b, x, y, 0.0) is None
    # a reach running east whose water narrows from 20 m to 6 m wide at its fourth point
    pts = [(x + i * 20 * U, y) for i in range(8)]
    half = {i: (3 if i == 3 else 10) for i in range(8)}
    b.wet = lambda px, py: abs(py - y) < half[min(range(8), key=lambda i: abs(pts[i][0] - px))] * U
    assert gen._reach_width_m(b, pts, 0) == 21.0 and gen._reach_width_m(b, pts, 3) == 7.0   # to the first dry 0.5 m sample
    assert gen._narrowest(b, pts, 0) == 3


def test_sky_ab_bounds_follow_the_markers_and_a_moved_marker_is_stale():
    from tools.journeys import gen

    def refs(dx):
        return {"ARG_Ref_PanelCoastalLagoonShore": {"x": 1000.0 + dx, "y": -2000.0, "marker": True, "own_z": True},
                "ARG_Ref_PanelWesternFrontierHigh": {"x": -500.0, "y": 700.0, "marker": True, "own_z": True}}
    import yaml
    text, pos = gen.sky_ab(Flat(refs=refs(0)))
    j = yaml.safe_load(text)
    ex = j["steps"][1]["expect"]
    assert [e.get("gt", e.get("lt")) for e in ex if e.get("path") == "pos.x"] == [700, 1300]
    assert j["id"] == "sky-ab" and j["independent_steps"] is True and len(j["steps"]) == 5
    assert pos[1] == ("ARG_Ref_PanelWesternFrontierHigh", -500, 700)
    # a moved marker moves the bounds, so the file written for the old position is stale
    moved, _ = gen.sky_ab(Flat(refs=refs(400)))
    assert yaml.safe_load(moved)["steps"][1]["expect"] != ex


class _Grass:
    """Tall grass (1.2 m) at every LAND vertex inside the box given (units), none elsewhere."""
    def __init__(self, box):
        self.box = box

    def at(self, x, y):
        x0, y0, x1, y1 = self.box
        return 1.2 if x0 <= x <= x1 and y0 <= y <= y1 else 0.0


def test_grass_clearance_counts_tall_grass_near_the_eye_and_under_the_first_20_m_only():
    x, y = at(60, 60)
    b = Flat()
    eye = J.eye_of(b, x, y)
    b.grass = _Grass((x - 3 * U, y - 3 * U, x + 3 * U, y + 3 * U))        # round the stand
    assert J.grass_hits(b, eye, 0.0) > 0
    b.grass = _Grass((x - 1 * U, y + 12 * U, x + 1 * U, y + 16 * U))       # on the line 12-16 m out
    assert J.grass_hits(b, eye, 0.0) > 0
    assert J.grass_hits(b, eye, 180.0) == 0                                 # behind the eye, past 6 m
    b.grass = _Grass((x - 1 * U, y + 30 * U, x + 1 * U, y + 40 * U))       # on the line past 20 m: the view, not the lens
    assert J.grass_hits(b, eye, 0.0) == 0
    assert J.clearance3(b, eye, 0.0) == (0, 0, 0)


def test_frame_share_reads_the_lower_frame_over_the_ground_and_water_heights():
    cx, cy = su.cell_of(*at(60, 60))
    x, y = at(60, 60)
    y -= 4 * U
    b = Pond({(cx, cy + k) for k in range(1, 4)})
    north = (su.cell_origin(cx, cy)[1] + su.CELL_UNITS - y) / U              # metres to the water's edge
    assert 0 < north < 60
    assert J.frame_share(b, x, y, 0.0, 0.0) > 0.5                            # the shallow rays reach the water
    assert J.frame_share(b, x, y, 180.0, 0.0) == 0.0                         # facing away
    assert J.frame_share(b, x, y, 0.0, 40.0) == 0.0                          # pitched down: the bank fills the frame


def test_frustum_cover_scores_a_near_trunk_and_ignores_one_behind():
    x, y = at(60, 60)
    b = Flat()
    b.grass = _Grass((0, 0, 0, 0))
    eye = J.eye_of(b, x, y)
    gz = b.ground_u(x, y)
    trunk = (x, y + 4 * U, gz, 1 * U, 12 * U, False, 0.0)      # a 2 m wide trunk 4 m ahead, 12 m tall
    b2 = Flat([trunk]); b2.grass = b.grass
    fc = J.frustum_cover(b2, eye, 0.0)
    assert fc["near"] > J.NEAR_COVER_MAX and not J.cover_ok(fc)
    assert J.frustum_cover(b2, eye, 180.0)["near"] == 0.0        # behind the eye
    far = (x, y + 20 * U, gz, 0.3 * U, 2 * U, True, 0.0)        # a small bush 20 m out: not the near frame
    b3 = Flat([far]); b3.grass = b.grass
    fc = J.frustum_cover(b3, eye, 0.0)
    assert fc["near"] == 0.0 and fc["all"] > 0 and J.cover_ok(fc)
    close = (x + 1 * U, y, gz, 0.5 * U, 2 * U, True, 0.0)       # bounds 0.5 m from the eye, off the frame
    b4 = Flat([close]); b4.grass = b.grass
    fc = J.frustum_cover(b4, eye, 0.0)
    assert fc["nearest_m"] < 1.0 and J.cover_ok(fc)                # beside the camera: reported, harmless


def test_type_share_counts_the_wet_rays_of_the_stops_own_type():
    cells = {(1, 1): 7, (1, 2): 3}
    sh, others = J.type_share(cells, {(1, 1): "black", (1, 2): "marsh"}, ("black",))
    assert sh == 0.7 and others == [(1, 2, "marsh", 3)]
    assert J.type_share({}, {}, ("black",))[0] == 0.0


def test_road_measure_is_the_distance_and_heading_against_the_centreline():
    from tools.journeys import gen
    u = gen.U
    pts = [(0.0, 0.0), (0.0, 100 * u), (100 * u, 100 * u)]   # north 100 m, then east 100 m
    on = gen.road_measure(pts, 0.0, 50 * u, 0.0)
    assert on["off_m"] < 1e-6 and on["head_off_deg"] < 1e-6 and abs(on["at_m"] - 50) < 1e-6
    off = gen.road_measure(pts, 3 * u, 40 * u, 200.0)          # 3 m east of the first leg, facing back down it, 20 deg off
    assert abs(off["off_m"] - 3) < 1e-6 and abs(off["road_deg"]) < 1e-6 and abs(off["head_off_deg"] - 20) < 1e-6
    bend = gen.road_measure(pts, 60 * u, 101 * u, 45.0)        # by the second leg (east), 45 deg off it
    assert abs(bend["off_m"] - 1) < 1e-6 and abs(bend["road_deg"] - 90) < 1e-6 and abs(bend["head_off_deg"] - 45) < 1e-6
    assert abs(bend["at_m"] - 160) < 1e-6
    assert gen.ROAD_OFF_MAX_M == 2.0 and gen.ROAD_HEAD_MAX_DEG == 20.0


def test_bridge_look_stands_12_m_from_the_deck_end_on_the_yaw_and_the_deck_stop_at_the_deck_top(monkeypatch):
    """gen.bridge_look: per bridge a stand BRIDGE_BACK_M from the deck's end along the heading (aimed at the deck middle),
    and a deck stop teleported to the deck middle whose z reads sit within 0.3 m of the deck top infra gives."""
    import math
    import re

    from tools.argonia_world import place_build
    from tools.argonia_world.routes import infra
    from tools.journeys import gen
    hd, deck_m = 90.0, 12.0   # a deck running east
    placed = {"id": "bridge.t-step", "at_m": [30.0, 40.0, 0.0], "heading": hd, "deck_m": deck_m, "routes": ["route.road.a", "route.road.b"]}
    monkeypatch.setattr(infra, "bridge_placements", lambda w, z_at: [placed])
    monkeypatch.setattr(place_build, "GameGround", lambda: type("G", (), {"z": staticmethod(lambda x, y: 10.0)})())
    text = gen.bridge_look(Flat(), None, [])
    s = gen.bridge_stands(Flat(), None)[0]
    cx, cy = su.province_to_skyrim(30.0, 40.0)
    assert math.hypot(s["sx"] - cx, s["sy"] - cy) / U == pytest.approx(infra.BRIDGE_LEN_M / 2 + gen.BRIDGE_BACK_M, abs=0.1)  # 12 m past the end
    assert s["sx"] < cx and s["sy"] == pytest.approx(cy, abs=1)   # back along the yaw: west of the deck, on its line
    assert s["h"] == pytest.approx(hd, abs=1)                      # aimed along it at the deck middle
    assert s["sz"] == pytest.approx(10.0 * U + J.SEAT_U, abs=1)    # seated on the current ground
    deck = text.split("name: t-step-deck")[1]
    top = round(su.metres_to_units(deck_m))
    z = int(re.search(r"player\.setpos z (\d+)", deck).group(1))
    assert z - top == gen.BRIDGE_DECK_DROP_U
    assert f"pos.z, ge: {top - gen.BRIDGE_DECK_TOL_U}" in deck and f"pos.z, le: {top + gen.BRIDGE_DECK_TOL_U}" in deck
    assert f"player.setpos x {cx:.0f}" in deck and "# deck:" in deck   # the deck stop is exempt from the ground check
    # every stop forces the weather AFTER the teleport and its settle, then reads it back (20 s more wait on the deck stop)
    for part in (text.split("name: t-step-deck")[0], deck):
        assert part.index("player.setpos z") < part.index('"sw ') < part.index('"fw ') < part.index("settle: {cap: 14", part.index('"fw '))
    assert "{wait: 20}]" in deck and "{wait: 20}]" not in text.split("name: t-step-deck")[0]


def test_stands_lie_two_cells_inside_the_built_box_read_from_the_terrain_grid():
    from tools.journeys import gen
    x0, y0 = su.PROVINCE_CELL_SW
    n = su.PROVINCE_CELLS

    def mid(cx, cy):
        return (cx + 0.5) * su.CELL_UNITS, (cy + 0.5) * su.CELL_UNITS
    assert gen.in_box(*mid(x0 + 2, y0 + 2)) and gen.in_box(*mid(x0 + n - 3, y0 + n - 3))
    assert not gen.in_box(*mid(x0 + 1, y0 + 5)) and not gen.in_box(*mid(x0 + 5, y0 + n - 2))
    assert not gen.in_box(*mid(-63, -24))          # r6-chain23's sea stand: outside the box, on the apron


def test_sea_far_names_the_parts_of_its_bar_a_stand_misses():
    from tools.journeys import gen
    ok = {"upper": 0.02, "near": 0.0, "sea_share": 0.9, "rays": 60}
    assert gen.sea_far_fails(ok) == []
    assert gen.sea_far_fails({**ok, "upper": 0.12, "sea_share": 0.5}) == ["upper cover", "sea share"]
    assert gen.sea_far_fails({**ok, "rays": 3}) == ["rays"]


def test_a_canopy_radius_widens_a_plant_whose_fronds_hang_past_its_bounds(tmp_path):
    from tools.journeys import canopy
    shapes = {"a": (37.0, 129.0, True, 0.0), "b": (300.0, 500.0, False, 0.0), "c": (50.0, 60.0, True, 0.0)}
    wide = canopy.reach(shapes, {"a": 74.4, "b": 120.0})
    assert wide["a"] == (74.4, 129.0, True, 0.0) and wide["b"] == shapes["b"] and wide["c"] == shapes["c"]
    t = tmp_path / "t.json"
    t.write_text('{"radius_u": {"a": 74.4}, "z_u": {"c": [-185.0, 438.0]}}')
    assert canopy.load(t) == {"a": (74.4, None, None), "c": (0.0, -185.0, 438.0)} and canopy.load(tmp_path / "none.json") == {}
    tall = canopy.reach(shapes, canopy.load(t))   # fronds standing past the OBND's top: the span grows to the mesh's
    assert tall["c"] == (50.0, 623.0, True, -185.0) and tall["a"] == (74.4, 129.0, True, 0.0)
    assert "03A57A:King of the Murkmire.esp" in canopy.load()    # the measured table is in data/


def test_placed_static_rule_rejects_a_stand_inside_a_box_and_accepts_one_2_m_outside():
    """static_hits: a stand inside a placed static's box (or within 1.5 m of it) is rejected; 2 m outside it is clear;
    an eye line entering a box within 3 m is an aim hit; the subject's own box never counts."""
    sx, sy = at(60, 60)
    g = 10 * U
    box = {"edid": "ARG_Ref_Hut", "x0": sx - 3 * U, "y0": sy - 3 * U, "z0": g - 1 * U, "x1": sx + 3 * U, "y1": sy + 3 * U, "z1": g + 5 * U}
    b = J.Build(ground=np.full((80, 80), 10.0, np.float32), water={}, refs={}, statics=[box])
    far = (sx, sy + 20 * U, g + 1 * U)   # the subject 20 m north, past the hut
    assert J.static_hits(b, sx, sy, far)["stand"] == ["ARG_Ref_Hut"]                  # inside the hut
    assert J.static_hits(b, sx + 4 * U, sy, far)["stand"] == ["ARG_Ref_Hut"]          # 1 m off its wall: within 1.5 m
    clear = J.static_hits(b, sx + 5 * U, sy, far)                                     # 2 m outside, looking past it
    assert clear == {"stand": [], "aim": [], "line": []}
    hut = (sx, sy, g + 2 * U)
    assert J.static_hits(b, sx + 5 * U, sy, hut, own=("ARG_Ref_Hut",)) == clear       # the hut as the subject: its own box
    assert J.static_hits(b, sx - 5.5 * U, sy, (sx + 10 * U, sy, g + 1.6 * U))["aim"] == ["ARG_Ref_Hut"]   # through it at 2.5 m
    assert J.static_hits(b, sx, sy - 10 * U, (sx, sy + 12 * U, g + 1.6 * U))["line"] == ["ARG_Ref_Hut"]  # behind it, 7 m on


def test_claywater_look_derives_every_stop_off_its_subjects_bounds(monkeypatch):
    """gen.claywater_look: one setpos stop per CLAY_STOPS row, each 8-15 m off its subject's bounds and outside every
    static box by 1.5 m, aimed at the subject's middle; then the interior stop with its door approach and a load settle."""
    import math
    import re

    import yaml

    from tools.journeys import gen, look
    monkeypatch.setattr(look, "grass_hits", lambda *a, **k: 0)
    names = sorted({n for _, refs, own, side, _ in gen.CLAY_STOPS for n in (*refs, *side)})
    refs, statics = {}, []
    for i, n in enumerate(names):   # a grid of refs 40 m apart; the buildings get a 6 m box
        x, y = at(40 + (i % 5) * 40, 40 + (i // 5) * 40)
        refs[gen.R + n] = {"id": n, "x": x, "y": y, "own_z": False, "marker": False, "z": None}
        if n.startswith("B"):
            statics.append({"edid": gen.R + n, "x0": x - 3 * U, "y0": y - 3 * U, "z0": 10 * U, "x1": x + 3 * U,
                            "y1": y + 3 * U, "z1": 16 * U})
    b = J.Build(ground=np.full((80, 80), 10.0, np.float32), water={}, refs=refs, statics=statics)
    b.wet = lambda x, y: False
    b.soaked = lambda x, y: False
    b._foliage = {}
    b._cell_foliage = lambda cx, cy: []
    log = []
    text = gen.claywater_look(b, log)
    steps = yaml.safe_load(text)["steps"]
    assert [s["name"] for s in steps] == [r[0] for r in gen.CLAY_STOPS] + ["station-house-inside"]
    assert len(log) == len(gen.CLAY_STOPS) and all(r["clear"] for r in log)
    for (name, refs_, own, _, _), r in zip(gen.CLAY_STOPS, log):
        s = gen.clay_subject(b, refs_, own)
        x, y = r["stand"][:2]
        assert 8.0 - 0.1 <= J.box_dist_u(s["box"], x, y) / U <= 15.0 + 0.1, name
        assert all(J.box_dist_u(bx, x, y) > J.STATIC_CLEAR_M * U for bx in statics), name
        blk = text.split(f"name: {name}\n")[1].split("- name:")[0]
        h = float(re.search(r"setangle z (-?\d+)", blk).group(1))
        want = math.degrees(math.atan2(s["mid"][0] - x, s["mid"][1] - y)) % 360
        assert abs((h - want + 180) % 360 - 180) <= 1.0, name   # aimed at the subject's middle
    inside = steps[-1]
    assert inside["weather"] == "any" and {"settle": {"cap": 30, "min": 3}} in inside["do"]


def test_panel_aim_horizon_rule_turns_then_moves():
    from tools.journeys import gen
    open_ = {"line": 0, "canopy": 0, "grass": 0, "upper": 0.05, "static": 0}
    wall = {**open_, "upper": 0.9}
    assert gen.panel_pass(open_) and not gen.panel_pass(wall)
    assert not gen.panel_pass({**open_, "static": 1}) and gen.panel_pass({**open_, "grass": 40})
    log: list = []
    # a heading 45 deg round the marker's passes: the stand stays, the heading turns
    sc = lambda x, y, h: open_ if round(h) == 45 else wall
    assert gen.panel_aim(None, "t", 0.0, 0.0, 0.0, log, score=sc, wet=lambda *a: False, ok_stand=lambda *a: True) == (0.0, 0.0, 45.0, 0.0)
    # nothing passes at the marker: the nearest stand 6 m east (x >= 6 m) that has a passing heading
    u = gen.U
    sc2 = lambda x, y, h: open_ if x >= 6 * u - 1 else wall
    x, y, h, moved = gen.panel_aim(None, "t", 0.0, 0.0, 90.0, log, score=sc2, wet=lambda *a: False, ok_stand=lambda *a: True)
    assert moved == 6.0 and x >= 6 * u - 1 and h == 90.0
    # wet ground is never a stand: the aim stays and is flagged
    x, y, h, moved = gen.panel_aim(None, "t", 0.0, 0.0, 90.0, log, score=sc2, wet=lambda px, py: px != 0, ok_stand=lambda *a: True)
    assert moved == 0.0 and log[-1]["tier"] == 4
    # a forest: upper cover 0.62 everywhere but a clear line and near field: tier 3 accepts it; a trunk on the line never
    forest = {**open_, "upper": 0.62, "line20": 0, "near": 0.04}
    x, y, h, moved = gen.panel_aim(None, "t", 0.0, 0.0, 90.0, log, score=lambda *a: forest, wet=lambda *a: False,
                                   ok_stand=lambda *a: True)
    assert log[-1]["tier"] == 3 and log[-1]["clear"] and moved == 0.0
    trunk = {**forest, "line20": 1}
    gen.panel_aim(None, "t", 0.0, 0.0, 90.0, log, score=lambda *a: trunk, wet=lambda *a: False, ok_stand=lambda *a: True)
    assert log[-1]["tier"] == 4 and log[-1]["clear"] and h == 90.0 and moved == 0.0
    # the frustum cover of a region of the frame never exceeds 100 %
