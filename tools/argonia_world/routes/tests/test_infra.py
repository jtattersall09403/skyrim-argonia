"""L1 (lane w3-infra): every planned exit gate, ferry landing and signpost resolves and stands on the final game ground
(within 0.5 m, the f6177a7 rule), every signpost carries two or more arms and every arm has text (infra.check); the
written references match the plan one for one, and the closed road's perk shows its message."""
import pytest

from tools.argonia_world import db
from tools.argonia_world.formids import Allocator
from tools.argonia_world.routes import infra


@pytest.fixture(scope="module")
def world():
    from tools.argonia_world.pieces import Index, Resolver
    from tools.argonia_world.place_build import GameGround
    try:
        return db.open(), Resolver(Index.load()), GameGround()
    except (FileNotFoundError, OSError) as e:
        pytest.skip(f"no pieces index or terrain grid: {e}")


def test_every_placement_resolves_on_the_ground_with_text(world):
    w, res, g = world
    assert infra.check(w, res, g.z) == []


def test_refs_match_the_plan(world):
    w, res, g = world
    plan = infra.placements(w, g.z)
    refs, bases, pending = infra.refs(Allocator(w), w, res, g.z)
    assert pending == []
    assert len(refs) == len(plan) and len({r["edid"] for r in refs}) == len(refs)
    kinds = {k: sum(1 for p in plan if p["kind"] == k) for k in ("gate", "landing", "signpost", "arm")}
    assert kinds["gate"] == 2 and kinds["landing"] == 2 and kinds["signpost"] == w.values("SELECT count(*) FROM signpost")[0]
    by = {b["edid"]: b for b in bases}
    arms = [b for b in bases if b["edid"].startswith("ARG_ACTI_SignArm")]
    assert arms and all(b["name"] and b["activateTextOverride"] == infra.ARM_VERB for b in arms)
    perk = by[infra.PERK[0]]
    assert perk["fragments"]["properties"] == [{"name": "RoadClosed", "object": by[infra.MESSAGE[0]]["formKey"]}]
    assert by[infra.MESSAGE[0]]["text"] == infra.CLOSED_MESSAGE
    assert by[infra.GATE_ACTI[0]]["keywords"] == [by[infra.KEYWORD[0]]["formKey"]]


def test_a_floating_post_and_a_blank_arm_fail_on_purpose(world, monkeypatch):
    w, res, g = world
    real = infra.placements(w, g.z)
    lifted = [dict(p, at_m=[*p["at_m"][:2], p["at_m"][2] + 1.0]) if p["kind"] == "signpost" else
              dict(p, text="") if p["id"].endswith(".arm0") else p for p in real]
    monkeypatch.setattr(infra, "placements", lambda *_: lifted)
    errs = infra.check(w, res, g.z)
    n = sum(1 for p in real if p["kind"] == "signpost")
    assert sum("off the final ground" in e for e in errs) == n
    assert sum("has no text" in e for e in errs) == n


def test_no_signpost_inside_a_footprint_and_one_planted_fails(world, monkeypatch):
    w, res, g = world
    plan = infra.placements(w, g.z)
    assert not any("footprint" in e for e in infra.check(w, res, g.z))
    fps = infra.footprints(w)
    assert fps
    f = fps[0]
    sites = infra.road_edge_site(w, {"x_m": f[1], "y_m": f[2], "place_id": f[0]}, fps)
    assert not infra.in_footprint(sites[0], sites[1], fps, f[0])  # the site search steps out of the footprints
    planted = [dict(p, at_m=[f[1], f[2], p["at_m"][2]]) if p["kind"] == "signpost" else p for p in plan]
    monkeypatch.setattr(infra, "placements", lambda *_: planted)
    errs = infra.check(w, res, g.z)
    assert sum("footprint" in e for e in errs) == sum(1 for p in plan if p["kind"] == "signpost")


def test_place_signposts_stand_on_the_road_edge(world):
    w, res, g = world
    plan = {p["id"]: p for p in infra.placements(w, g.z)}
    for r in w.query("SELECT s.id, s.x_m, s.y_m FROM signpost s JOIN route_node n ON n.id = s.node_id "
                     "WHERE n.kind = 'place'"):
        x, y, _ = plan[r["id"]]["at_m"]
        assert 0 < ((x - r["x_m"]) ** 2 + (y - r["y_m"]) ** 2) ** .5 <= 10


def test_edids():
    assert infra.edid({"id": "gate.tear-road", "kind": "gate"}) == "ARG_Ref_GateTearRoad"
    assert infra.edid({"id": "sign.place.imperial-fringe.gideon.arm1", "kind": "arm",
                       "signpost": "sign.place.imperial-fringe.gideon"}) == "ARG_Ref_SignImperialFringeGideonArm1"
    assert infra.edid({"id": "sign.road.gideon-soulrest.1234", "kind": "signpost",
                       "signpost": "sign.road.gideon-soulrest.1234"}) == "ARG_Ref_SignGideonSoulrest1234"
    assert infra.arm_edid("Ridge Runners' Post") == "ARG_ACTI_SignArmRidgeRunnersPost"
