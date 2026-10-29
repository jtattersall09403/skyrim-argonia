"""L1: the water classes, the stepped river and the migration on small hand-made graphs (no numpy, no game data)."""
from tools.argonia_world.water import classify, migrate, steps
from tools.argonia_world.water.model import Body, Reach


def reach(**kw):
    base = dict(id="reach.a", river="river.a", kind="horizontal-channel", surface="channel", water="clearwater",
                width_m=6.0, depth_m=0.5, length_m=200.0, level_from_m=14.0, level_to_m=10.0, speed_ms=1.0,
                tidal=False, body=None, downstream=None, fall_drop_m=None, fall_plunge_body=None,
                points=tuple((float(x), 0.0) for x in range(0, 201, 5)))
    base.update(kw)
    return Reach(**base)


def test_the_sample_reach_steps_within_its_grade():
    st = steps.reach_steps(reach())  # 4 m over 200 m: the stepped-river proof's reach
    assert len(st) == 8
    drops = [a.level_m - b.level_m for a, b in zip(st, st[1:])]
    assert all(abs(d - 0.5) < 1e-9 for d in drops)
    assert all(s.profile_lo_m <= s.level_m <= s.profile_hi_m for s in st)


def test_steep_reach_keeps_steps_at_least_step_min_long():
    st = steps.reach_steps(reach(length_m=40.0, level_from_m=30.0, level_to_m=10.0,
                                 points=tuple((float(x), 0.0) for x in range(0, 41, 5))))
    assert len(st) == 5 and all(s.s1 - s.s0 >= steps.STEP_MIN_M for s in st)


def test_classes_and_water_types():
    def body(kind, level=2.0, area=100.0, band="lowland"):
        return Body("body.x", kind, "measured", level, area, band, None, None, None)
    assert classify.body_rule(body("ocean", 0.0)).cls == "sea"
    assert classify.body_rule(body("lagoon", 0.0)).rule == "default"
    assert classify.body_rule(body("marsh-deep", area=20000.0)).cls == "lake"
    assert classify.body_rule(body("swamp")).water == "black"
    assert classify.body_rule(body("mudflat")).water == "brackish"
    assert classify.reach_rule(reach(kind="vertical-fall", fall_drop_m=4.0)).cls == "falls"
    assert classify.reach_rule(reach(kind="sloped-rapid")).rule == "stepped"


def test_migration_keeps_every_field():
    g = {"rivers": [{"id": "river.a", "name": None, "reaches": ["reach.a"], "tributaryOf": None,
                     "mouth": {"kind": "sea", "bodyId": "body.ocean"}}],
         "reaches": [{"id": "reach.a", "river": "river.a", "upstream": [], "centreline": [[1.0, 2.0], [3.0, 4.0]],
                      "terrainPrecondition": {"kind": "trench", "widthM": 5.0}}],
         "junctions": [], "bodies": [{"id": "body.ocean", "kind": "ocean", "inflow": [], "approved": None,
                                      "deepestCell": None, "bboxCells": None}],
         "thresholds": {}, "grid": {}, "vocabulary": {}, "sourceHeightSha256": "x", "contentSha256": "y",
         "schemaVersion": 1}
    rows = list(migrate.rows(g))
    tables = {t for t, _ in rows}
    assert {"hydrology_river", "hydrology_reach", "hydrology_reach_point", "hydrology_river_reach"} <= tables
    reach_row = next(r for t, r in rows if t == "hydrology_reach")
    assert reach_row["terrain_precondition_width_m"] == 5.0 and reach_row["river_id"] == "river.a"
    body_row = next(r for t, r in rows if t == "hydrology_body")
    assert body_row["approved_unreviewed"] is True
