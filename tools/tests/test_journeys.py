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
