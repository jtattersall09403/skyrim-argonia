"""The ground stage: the source's relief carried under a place's footprint (tools/places/draft/ground.py)."""
import math

from tools.places.draft import ground as gr
from tools.places.draft.stages import diff
from tools.places.seat import STEP, Ground

CELLS = [(cx, cy) for cx in range(-2, 2) for cy in range(-2, 2)]


def flat(z=0.0, water=None, f=None):
    cells = {}
    for cx, cy in CELLS:
        h = []
        for row in range(33):
            for col in range(33):
                x, y = (cx * 32 + col) * STEP, (cy * 32 + row) * STEP
                h.append(z + (f(x, y) if f else 0.0))
        cells[(cx, cy)] = h
    return Ground(cells, {k: water for k in CELLS} if water is not None else {}, None)


def mound(x, y):        # a mound 300 high, 1200 across, at the source's origin
    return 300.0 * max(0.0, 1 - math.hypot(x, y) / 1200)


PIECES = [(-800.0, -800.0), (800.0, -800.0), (800.0, 800.0), (-800.0, 800.0), (0.0, 0.0), (400.0, -300.0)]
MAP = ((0, 0), (0, 0), 0.0)


def one(pts=PIECES, m=MAP, cid="b01"):
    return [{"id": cid, "map": m, "pts": list(pts)}]


def run(ours, src, clusters=None, **kw):
    rows, rep = gr.carry(ours, src, clusters or one(), **kw)
    g = Ground({k: list(v) for k, v in ours.cells.items()}, ours.water_by_cell, None)
    g.apply_patches(rows)
    return rows, rep, g


def test_a_mound_inside_the_body_stays():
    # the trend is fitted at the footprint's edge: a mound inside the body is the body's own relief and comes
    _, rep, g = run(flat(100), flat(500, f=mound))
    assert g.vertex(0, 0) - g.vertex(9, 0) > 200, rep      # the mound's top stands over its foot
    assert rep["bodies_patched"] == 1


def test_the_hills_slope_goes_beyond_what_the_feet_need():
    # the source climbs 1 in 1 (45 degrees) across the body: the feet carry at most TILT_DEG of it, reported
    _, rep, g = run(flat(0), flat(0, f=lambda x, y: x), cap=2000.0)
    tilt = (g.vertex(6, 0) - g.vertex(-6, 0)) / (12 * STEP)
    assert abs(tilt - math.tan(math.radians(gr.TILT_DEG))) < 0.03, tilt
    assert rep["tilts_limited"] == 1


def test_a_gentle_slope_under_the_feet_is_kept():
    _, rep, g = run(flat(0), flat(0, f=lambda x, y: 0.15 * x))
    assert abs((g.vertex(5, 0) - g.vertex(-5, 0)) / (10 * STEP) - 0.15) < 0.02
    assert rep["tilts_limited"] == 0


def test_blend_stays_gentle_and_outside_unchanged():
    ours = flat(100, f=lambda x, y: -200.0 if x > 0 else 0.0)
    rows, rep, g = run(ours, flat(0, f=mound))
    reach = gr.MARGIN + max(b.get("band", 0) for b in rep["per_body"]) + STEP
    for (cx, cy), h in g.cells.items():
        for row in range(33):
            for col in range(33):
                x, y = (cx * 32 + col) * STEP, (cy * 32 + row) * STEP
                if max(abs(x), abs(y)) > 800 + reach + STEP:
                    assert h[row * 33 + col] == ours.cells[(cx, cy)][row * 33 + col]


def test_cap():
    _, rep, g = run(flat(0), flat(0, f=lambda x, y: 2000.0 * (math.hypot(x, y) < 300)))
    assert max(max(h) for h in g.cells.values()) <= gr.CAP + 0.1
    assert rep["capped_share_max"] > 0


def test_water_line_held():
    _, _, g = run(flat(0, water=50.0), flat(0, f=mound))
    assert max(max(h) for h in g.cells.values()) <= 50.0 - 8.0 + 0.1
    _, _, g = run(flat(100, water=90.0), flat(0, f=lambda x, y: -mound(x, y)))
    assert min(min(h) for h in g.cells.values()) >= 90.0 + 8.0 - 0.1


def test_change_fades_before_our_water():
    # our channel along x > 600 (ground under water there): the mound's change is nothing at the channel's edge
    ours = flat(0, f=lambda x, y: -100.0 if x > 600 else 0.0)
    ours.water_by_cell = {k: -20.0 for k in CELLS}
    src = flat(0, f=lambda x, y: 300.0 * max(0.0, 1 - math.hypot(x - 400, y) / 1200))
    _, rep, g = run(ours, src)
    assert abs(g.height(640.0, 0.0) - ours.height(640.0, 0.0)) < 1      # at the water: nothing
    assert abs(g.height(512.0, 0.0) - ours.height(512.0, 0.0)) < 70     # one step short: a quarter
    assert g.height(0.0, 0.0) - ours.height(0.0, 0.0) > 100              # clear of it the relief comes
    assert rep["faded_for_our_water_m2"] > 0


def test_source_water_not_brought():
    src = flat(0, water=-50.0, f=lambda x, y: -mound(x, y))
    _, rep, g = run(flat(100), src)
    assert abs(g.vertex(0, 0) - 100) < 1
    assert rep["faded_for_source_water_m2"] > 0


def test_taken_cells_untouched():
    ours = flat(100)
    _, _, g = run(ours, flat(0, f=mound), taken={(0, 0)})
    assert g.cells[(0, 0)] == ours.cells[(0, 0)]
    assert g.cells[(-1, -1)] != ours.cells[(-1, -1)]


def test_idempotent():
    ours, src = flat(100), flat(0, f=mound)
    r1, _ = gr.carry(ours, src, one())
    r2, _ = gr.carry(ours, src, one())
    assert r1 == r2 and all(r["by"] == "ground" for r in r1)


def test_a_cluster_left_out_changes_nothing():
    rows, rep = gr.carry(flat(0), flat(0, f=mound), one(), leave_out={"b01"})
    assert rows == [] and rep["per_body"][0]["left_out"]


def test_feet_meet_the_ground_better():
    _, rep, _ = run(flat(0), flat(0, f=mound))
    assert rep["feet_after"]["median_worst"] < rep["feet_before"]["median_worst"] / 3, rep


def test_stage_owns_only_ground_rows():
    import json
    a = json.dumps({"cell": [0, 0], "verts": [[1, 1, -3.0]], "by": "sap"})
    g1 = json.dumps({"cell": [0, 0], "verts": [[2, 2, 5.0]], "by": "ground"})
    g2 = json.dumps({"cell": [0, 0], "verts": [[2, 2, 9.0]], "by": "ground"})
    owns = {"land.jsonl": (None, True, "ground")}
    _, bad = diff({"land.jsonl": a + "\n" + g1}, {"land.jsonl": a + "\n" + g2}, owns)
    assert not bad
    _, bad = diff({"land.jsonl": a + "\n" + g1}, {"land.jsonl": g1}, owns)
    assert bad


def test_build_adds_a_vertexs_changes():
    from tools.places.build import summed_land
    s = summed_land([{"cell": [0, 0], "verts": [[1, 1, 40.0]]}, {"cell": [0, 0], "verts": [[1, 1, -10.0]]}])
    assert s[(0, 0)][(1, 1)] == 30.0


def test_slope_hold():
    import numpy as np
    dz = np.zeros((5, 9))
    dz[:, :4] = 300.0
    dz[:, 5:] = -300.0
    free = np.ones(dz.shape, bool)
    free[:, 0] = free[:, 8] = False
    out = gr.slope_hold(dz, free, 35.0)
    assert np.abs(np.diff(out, axis=1)).max() <= math.tan(math.radians(35)) * STEP + 0.01
    assert out[0, 0] == 300.0 and out[0, 8] == -300.0


def test_bodies_split_by_map_and_distance():
    m2 = ((0, 0), (5000.0, 0), 0.0)
    cs = [{"id": "a", "map": MAP, "pts": [(0.0, 0.0)]}, {"id": "b", "map": MAP, "pts": [(300.0, 0.0)]},
          {"id": "c", "map": MAP, "pts": [(3000.0, 0.0)]}, {"id": "d", "map": m2, "pts": [(400.0, 0.0)]}]
    assert sorted(b["ids"] for b in gr.bodies(cs)) == [["a", "b"], ["c"], ["d"]]


def test_a_cluster_set_apart_carries_its_own_relief_not_the_step():
    # the fit moved a cluster from a spot of the source 2000 higher: it keeps the mound round itself, no step,
    # and the gap between the two bodies is untouched
    def f(x, y):
        return mound(x, y) + mound(x - 9000.0, y) + (2000.0 if x > 4000 else 0.0)
    main = [(-800.0, -800.0), (-800.0, 800.0), (800.0, -800.0), (800.0, 800.0), (0.0, 0.0)]
    east = [(5200.0, -800.0), (5200.0, 800.0), (6800.0, -800.0), (6800.0, 800.0), (6000.0, 0.0)]
    global CELLS
    keep = CELLS
    CELLS = [(cx, cy) for cx in range(-3, 6) for cy in range(-3, 3)]
    try:
        src, ours = flat(0, f=f), flat(0)
        cs = [{"id": "m", "map": MAP, "pts": main}, {"id": "e", "map": ((9000.0, 0), (6000.0, 0), 0.0), "pts": east}]
        rows, rep, g = run(ours, src, cs)
    finally:
        CELLS = keep
    assert rep["largest_change"] <= gr.CAP and rep["bodies"] == 2, rep
    assert g.height(6000.0, 0) - g.height(5200.0, 900.0) > 150
    assert abs(g.height(3000.0, 0) - ours.height(3000.0, 0)) < 1.0
