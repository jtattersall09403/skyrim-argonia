"""L1: every exterior build_ref with no explicit z sits on the final game ground (the river regrade and the place
ground edits applied: place_build.GameGround), not on the frozen 2.W1 array. The clay cut's marker floated 2 m up and
first-place's teleport to the clay cut landed at the water's edge. The old ground fails it (proven on purpose)."""
import pytest

from tools.argonia_world import db, place_build
from tools.argonia_world import skyrim_units as su

TOL_M = 0.5


@pytest.fixture(scope="module")
def final():
    try:
        return place_build.GameGround()
    except (FileNotFoundError, OSError) as e:
        pytest.skip(f"no terrain grid: {e}")


def _implicit():
    w = db.open()
    cells = {c.id for c in w.rows("build_cell") if c.kind == "exterior"}
    return [r for r in w.rows("build_ref") if r.cell_id in cells and r.z_m is None]


def _off(ground, final):
    """(metres off the final ground, ref id) of every implicit-z ref, as place_build._pos places it."""
    ctx = type("Ctx", (), {"ground": ground})
    return [(abs(place_build._pos(ctx, "exterior", r)[2] / su.UNITS_PER_METRE - final.z(r.x_m, r.y_m)), r.id)
            for r in _implicit()]


def test_implicit_refs_within_half_a_metre_of_the_final_ground(final):
    off = _off(final, final)
    assert off
    bad = [(round(d, 2), i) for d, i in off if d > TOL_M]
    assert not bad, bad


def test_the_frozen_ground_fails_it_on_purpose(final):
    from tools.argonia_world.routes.build import Ground
    bad = [i for d, i in _off(Ground(), final) if d > TOL_M]
    assert bad, "the pre-regrade ground should put some ref (the clay cut) off the final ground"
    print("old behaviour fails:", bad)
