"""L1 (lane 1.15-r4-claywater; owner play test 3, findings 22, 23, 31): a place's explicit heights stand on today's
game ground, and every dock, landing and boat stands on its cell's water, not on the bed under it.

The round-3 regrade lifted Claywater's ground about 33 m; the absolute z_m of its station house, stable and hut doors
stayed at the old ground, so all of them stood buried ('no doors', 'no house or stables'). The landing stage and raft
had no z and stood on the river bed ('landings and dock stuff underwater')."""
import pytest

from tools.argonia_world import db, place_build
from tools.argonia_world.routes import infra

BELOW_M, ABOVE_M = 1.5, 3.0  # a doorway sits 1.2 m under its door, a door frame 1.9 m over the pad
POST_M = 4.0  # a deck stands no higher than this over the ground under it (its posts reach the bed)
MARKERS = ("ref.panel.", "ref.probe.")  # camera stands, placed in the air on purpose


@pytest.fixture(scope="module")
def ground():
    try:
        return place_build.GameGround()
    except (FileNotFoundError, OSError) as e:
        pytest.skip(f"no terrain grid: {e}")


@pytest.fixture(scope="module")
def world():
    return db.open()


def _exterior(w):
    cells = {c.id for c in w.rows("build_cell") if c.kind == "exterior"}
    return [r for r in w.rows("build_ref") if r.cell_id in cells and not r.id.startswith(MARKERS)]


def test_explicit_heights_stand_on_the_game_ground(world, ground):
    bad = [(r.id, round(_z(world, ground, r) - ground.z(r.x_m, r.y_m), 2)) for r in _exterior(world)
           if (r.z_m is not None or r.z_over_m is not None)
           and not -BELOW_M <= _z(world, ground, r) - ground.z(r.x_m, r.y_m) <= ABOVE_M]
    assert not bad, f"{len(bad)} refs off the ground: {bad}"


def _z(w, ground, r) -> float:
    ctx = type("C", (), {"ground": ground, "world": w})
    return place_build._pos(ctx, "exterior", r)[2] / place_build.su.UNITS_PER_METRE


# A piece whose origin stands under its support on purpose: (ref id suffix, its support, metres under the ground).
# KotM's house origin is its sunk floor slab, its stairs foot a step under the door; a doorway's origin is 1.22 m under
# its door (KotM's door-local offset). Each is checked against its support, which stands on the ground.
STACKED = {"b1": ("b1-door", -1.34), "b1-stairs": ("b1-door", -0.52), "b1-doorframe": ("b1-door", 1.11),
           "b4-doorway": ("b4-door", -1.22), "b5-doorway": ("b5-door", -1.22), "b6-doorway": ("b6-door", -1.22)}
SEAT_M = 0.3


def test_no_exterior_ref_buried_or_afloat(world, ground):
    """Every exterior ref of every place stands within 0.3 m of the game ground at plugin time, unless it is a water
    seat (a dock, a boat, a person on a deck: over the cell water) or a stacked piece, checked against its support."""
    refs = {r.id: r for r in _exterior(world) if not r.id.startswith(MARKERS)}
    bad = []
    for r in refs.values():
        z, g = _z(world, ground, r), ground.z(r.x_m, r.y_m)
        if place_build.water_seat(r.piece) is not None:
            continue  # test_docks_and_boats_on_the_water_with_posts_in_the_ground
        lv = place_build.water_level(world, r.x_m, r.y_m)
        if r.z_m is None and r.z_over_m is None and lv is not None and g < lv and place_build._is_person_spot(world, r):
            continue  # a person on the deck over the cell water (test_no_person_stands_under_the_ground...)
        short = r.id.rsplit(".", 1)[-1]
        if short in STACKED:
            sup, off = STACKED[short]
            s = refs[r.id.rsplit(".", 1)[0] + "." + sup]
            if abs(z - _z(world, ground, s) - off) > SEAT_M:
                bad.append((r.id, "off its support", sup, round(z - _z(world, ground, s), 2)))
            continue
        if abs(z - g) > SEAT_M:
            bad.append((r.id, round(z - g, 2)))
    assert not bad, f"{len(bad)} exterior refs buried or afloat: {bad}"


def _decks(w, ground):
    out = []
    ctx = type("C", (), {"ground": ground, "world": w})
    for r in _exterior(w):
        if r.z_m is None and place_build.water_seat(r.piece) is not None:
            z = place_build._pos(ctx, "exterior", r)[2] / place_build.su.UNITS_PER_METRE
            out.append((r.id, r.x_m, r.y_m, z, place_build.water_seat(r.piece)))
    for p in infra.placements(w, ground.z):
        if p["kind"] == "landing":
            out.append((p["id"], p["at_m"][0], p["at_m"][1], p["at_m"][2], place_build.DOCK_DECK_M))
    return out


def test_docks_and_boats_on_the_water_with_posts_in_the_ground(world, ground):
    decks = _decks(world, ground)
    assert any(i.startswith("ref.claywater-station.land-dock") for i, *_ in decks)
    bad = []
    for i, x, y, z, h in decks:
        lv = place_build.water_level(world, x, y)
        g = ground.z(x, y)
        if lv is not None and z < lv + h - 0.01:
            bad.append((i, "under its water", round(z - lv, 2)))
        if h and z - g > POST_M:
            bad.append((i, "posts short of the ground", round(z - g, 2)))
    assert not bad, bad


def test_the_bed_seat_fails_on_purpose(world, ground):
    """The old seat (the ground under the dock) puts Claywater's landing stage under its water."""
    r = world.get("build_ref", "ref.claywater-station.land-dock2")
    assert ground.z(r.x_m, r.y_m) < place_build.water_level(world, r.x_m, r.y_m)


def test_no_person_stands_under_the_ground_or_the_cell_water(world, ground):
    """Round 5 (lane 1.3-r5-livia): a person's placement is on the ground and over the cell's water, never under either."""
    people = {p.npc_id for p in world.rows("build_person")}
    bad = []
    for r in _exterior(world):
        if r.npc_id not in people or place_build._is_person_spot(world, r) is False:
            continue
        ctx = type("C", (), {"ground": ground, "world": world})
        z = place_build._pos(ctx, "exterior", r)[2] / place_build.su.UNITS_PER_METRE  # where the build puts them
        g = ground.z(r.x_m, r.y_m)
        lv = place_build.water_level(world, r.x_m, r.y_m)
        if z < g - 0.5 or (lv is not None and z < lv):
            bad.append((r.id, round(z, 2), round(g, 2), lv))
    assert not bad, f"people under the ground or the water: {bad}"


def test_a_kept_animal_is_not_a_predator():
    """Round 5: the pen's guar carried the predator AI (VeryAggressive, aggro 2000) and mauled Livia at the well."""
    from tools.argonia_world import place_build as pb
    w = db.open()
    kept = {n.id for n in w.rows("npc") if n.kind == "creature" and n.hostility == "neutral"}
    assert kept and pb.KEPT_AI["aggression"] == "Unaggressive" and "aggro" not in pb.KEPT_AI
    pb.check_creatures([{"type": "NPC_", "edid": "ARG_Npc_G", "templateFlags": pb.CREATURE_TEMPLATE_FLAGS, **pb.KEPT_AI}])
