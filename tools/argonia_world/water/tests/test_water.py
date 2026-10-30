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


def test_steep_reach_becomes_step_and_pool():
    # 20 m over 64 m: pools STEP_MIN_M (16 m) long, each dropping 5 m at a falls piece
    r = reach(length_m=64.0, level_from_m=30.0, level_to_m=10.0, points=tuple((float(x), 0.0) for x in range(0, 65, 4)))
    st = steps.reach_steps(r)
    assert len(st) == 4 and all(abs(s.s1 - s.s0 - steps.STEP_MIN_M) < 1e-9 for s in st)
    assert all(abs((a.level_m - b.level_m) - 5.0) < 1e-9 for a, b in zip(st, st[1:]))
    assert steps.piece_for(5.0) == "falls" and steps.piece_for(1.0) == "cascade" and steps.piece_for(0.5) == "rapids"


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


def test_a_body_sharing_another_bodys_water_takes_its_outcome():
    # two measured swamps on the same nine samples (field step 2 shares them): the first holds them and is a puddle,
    # so the second is dropped with it, never left as an own-level body with no water (body.1746-2172)
    import numpy as np
    from tools.argonia_world.water import design, field
    from tools.argonia_world.water.model import Graph
    n = 24
    ground = np.full((n, n), 2.0, dtype=np.float32)
    ground[10:13, 10:13] = 1.0
    idx = np.array([r * n + c for r in range(10, 13) for c in range(10, 13)])
    lvl = np.full((n, n), np.nan, dtype=np.float32)
    lvl.ravel()[idx] = 1.5
    wt = np.full((n, n), field.DRY, dtype=np.uint8)
    wt.ravel()[idx] = 0
    src = np.zeros((n, n), dtype=np.uint8)
    src.ravel()[idx] = 1
    own = np.full((n, n), -1, dtype=np.int32)
    own.ravel()[idx] = 0
    body = dict(kind="swamp", origin="measured", level_m=1.5, area_m2=30.0, altitude_band="lowland", region=1,
                deepest=(11, 11), bbox=(10, 10, 12, 12))
    g = Graph({b: Body(id=b, **body) for b in ("body.a", "body.b")}, {}, {}, {}, {}, {"pondMinM2": 500.0})
    f = field.Field(lvl, wt, src, body_samples={"body.a": idx, "body.b": idx}, owner=own, owners=["body.a", "body.b"])
    d = design.design(g, f, ground)
    out, basin, _ = d.body["body.a"]
    assert out == "dropped" and "puddle" in next(b.reason for b in d.basins if b.id == basin)
    assert d.body["body.b"][:2] == (out, basin) and d.body["body.b"][2] == "it shares the water of body.a"


def test_the_carve_never_cuts_below_adjoining_lower_water():
    # a pool at 0.84 carved to -0.66 beside a marsh at 0.34 (the report's (-31,-22)): its edge bed rises to 0.34,
    # its inner bed and a bed beside its own reach's water stay carved
    import numpy as np
    from tools.argonia_world.water import field, oriented
    n = 6
    lvl = np.full((n, n), np.nan, dtype=np.float32)
    own = np.full((n, n), -1, dtype=np.int32)
    lvl[:, :2], own[:, :2] = 0.34, 0       # the marsh
    lvl[:, 2:], own[:, 2:] = 0.84, 1       # the pool
    f = field.Field(lvl, np.zeros((n, n), np.uint8), np.ones((n, n), np.uint8), owner=own, owners=["body.m", "reach.r"])
    beds = {r * n + c: (-0.66, "reach.r") for r in range(n) for c in (2, 3, 4)}
    assert oriented.clamp_beds(beds, f) == n
    assert all(beds[r * n + 2][0] == 0.34 for r in range(n))
    assert all(beds[r * n + c][0] == -0.66 for r in range(n) for c in (3, 4))
