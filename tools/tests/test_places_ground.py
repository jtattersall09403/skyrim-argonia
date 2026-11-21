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


PIECES = [(-800.0, -800.0), (800.0, -800.0), (800.0, 800.0), (-800.0, 800.0)]


def run(ours, src, **kw):
    rows, rep = gr.carry(ours, src, (0, 0), (0, 0), 0.0, PIECES, **kw)
    g = Ground({k: list(v) for k, v in ours.cells.items()}, ours.water_by_cell, None)
    g.apply_patches(rows)
    return rows, rep, g


def test_relief_carried():
    _, rep, g = run(flat(100), flat(500, f=mound))
    assert rep["ref"] == "the footprint's edge" and rep["our_ref"] == 100.0
    edge = rep["src_ref"] - 500                   # the mound's height round the footprint's edge
    assert abs(g.vertex(0, 0) - (100 + 300 - edge)) < 1          # the mound's top stands its relief over our ground
    assert abs(g.vertex(4, 0) - (100 + mound(4 * STEP, 0) - edge)) < 1


def test_blend_stays_gentle_and_outside_unchanged():
    ours = flat(100, f=lambda x, y: -200.0 if x > 0 else 0.0)     # our ground has a step the source lacks
    src = flat(0, f=mound)
    rows, rep, g = run(ours, src)
    reach = gr.MARGIN + rep["band"]
    for (cx, cy), h in g.cells.items():
        for row in range(33):
            for col in range(33):
                x, y = (cx * 32 + col) * STEP, (cy * 32 + row) * STEP
                if max(abs(x), abs(y)) > 800 + reach + STEP:
                    assert h[row * 33 + col] == ours.cells[(cx, cy)][row * 33 + col]
    # the blend's own slope: the source has none steeper than the mound, so the band holds 35 degrees
    assert rep["slope_limit_deg"] == 35.0


def test_cap():
    _, rep, g = run(flat(0), flat(0, f=lambda x, y: 2000.0 * (math.hypot(x, y) < 300)))
    assert max(max(h) for h in g.cells.values()) <= gr.CAP + 0.1
    assert rep["capped"] > 0


def test_water_line_held():
    # our water at 50: ground at 0 is under it and stays under; the mound may not lift it out
    _, _, g = run(flat(0, water=50.0), flat(0, f=mound))
    assert max(max(h) for h in g.cells.values()) <= 50.0 - 8.0 + 0.1
    # dry ground at 100 over water at 90 may not be dug under it
    _, _, g = run(flat(100, water=90.0), flat(0, f=lambda x, y: -mound(x, y)))
    assert min(min(h) for h in g.cells.values()) >= 90.0 + 8.0 - 0.1


def test_source_water_not_brought():
    # the source's ground near its origin stood under its own water at -50: there our ground is not changed
    src = flat(0, water=-50.0, f=lambda x, y: -mound(x, y))
    _, rep, g = run(flat(100), src)
    assert abs(g.vertex(0, 0) - 100) < 1
    assert rep["source_water_area_m2"] > 0


def test_taken_cells_untouched():
    ours = flat(100)
    _, _, g = run(ours, flat(0, f=mound), taken={(0, 0)})
    assert g.cells[(0, 0)] == ours.cells[(0, 0)]
    assert g.cells[(-1, -1)] != ours.cells[(-1, -1)]


def test_idempotent():
    ours, src = flat(100), flat(0, f=mound)
    r1, _ = gr.carry(ours, src, (0, 0), (0, 0), 0.0, PIECES)
    r2, _ = gr.carry(ours, src, (0, 0), (0, 0), 0.0, PIECES)
    assert r1 == r2 and all(r["by"] == "ground" for r in r1)


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


def test_blend_no_steeper_than_the_limit():
    # our ground falls 300 east of x=900; the source is flat: the footprint is lifted level and its east edge must
    # blend down to our ground at 35 degrees or less
    ours = flat(0, f=lambda x, y: -300.0 if x > 900 else 0.0)
    rows, rep = gr.carry(flat(0), flat(0), (0, 0), (0, 0), 0.0, PIECES)
    assert rows == []                               # a flat source on flat ground changes nothing
    rows, rep = gr.carry(ours, flat(0), (0, 0), (0, 0), 0.0, PIECES)
    assert rep["raised_max"] == 300.0 and rep["band"] > gr.BAND_MIN
    assert rep["band_steepest_deg"] <= 35.5, rep


def test_a_cluster_set_apart_reads_through_its_own_map():
    # the cluster east of the origin was moved 1000 east by the fit: under it the mound it stood on comes with it
    src = flat(0, f=mound)
    pieces = [(-800.0, -800.0), (-800.0, 800.0), (1800.0, -800.0), (1800.0, 800.0)]
    maps = [((0, 0), (0, 0), 0.0, (-800.0, 0.0)), ((0, 0), (1000.0, 0), 0.0, (1800.0, 0.0))]
    rows, rep = gr.carry(flat(0), src, (0, 0), (0, 0), 0.0, pieces, maps=maps)
    g = flat(0)
    g.apply_patches(rows)
    top = g.height(1000.0, 0) - rep["our_ref"] + rep["src_ref"]       # the source's height read at x=1000
    assert top > 250                    # its mound's top (300), not the main map's reading there (50)


def test_a_cluster_set_apart_carries_its_own_relief_at_its_own_level():
    # the fit moved a cluster 3000 east from a spot of the source 2000 higher than the main body, onto our flat
    # ground: it keeps the mound round itself, not a 2000 step, and the gap between the two is not carried
    def f(x, y):
        return mound(x, y) + mound(x - 9000.0, y) + (2000.0 if x > 4000 else 0.0)
    main = [(-800.0, -800.0), (-800.0, 800.0), (800.0, -800.0), (800.0, 800.0)]
    east = [(5200.0, -800.0), (5200.0, 800.0), (6800.0, -800.0), (6800.0, 800.0)]
    global CELLS
    keep = CELLS
    CELLS = [(cx, cy) for cx in range(-3, 6) for cy in range(-3, 3)]
    try:
        src, ours = flat(0, f=f), flat(0)
        maps = [((0, 0), (0, 0), 0.0, (0.0, 0.0), main, False),
                ((9000.0, 0), (6000.0, 0), 0.0, (6000.0, 0.0), east, True)]
        rows, rep = gr.carry(ours, src, (0, 0), (0, 0), 0.0, main + east, maps=maps)
        g = flat(0)
        g.apply_patches(rows)
    finally:
        CELLS = keep
    assert rep["clusters_own_levels"] == 1
    assert abs(rep["raised_max"]) < 400 and rep["capped"] == 0, rep      # no 2000 step, nothing capped
    assert g.height(6000.0, 0) - g.height(5200.0, 900.0) > 150          # the source's mound read at 9000 (its own)
    assert abs(g.height(3000.0, 0) - ours.height(3000.0, 0)) < 1.0      # the gap between them untouched
