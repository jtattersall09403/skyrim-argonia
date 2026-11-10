"""The builder's path dressing: which land texture a path is painted with."""
from tools.places import build

FACTS = {"ltex": [{"edid": "ANW_dirt_road", "fk": "ArgoniaNewWorld.esm:000900"},
                  {"edid": "ANW_swamp_mud", "fk": "ArgoniaNewWorld.esm:000901"}]}
LINE = [[100.0, 100.0], [900.0, 100.0]]


def layers(style):
    build.PROBLEMS.clear()
    out = build.plan_paths([{"id": "p.1", "kind": "path", "style": style, "points": LINE, "width": 160}], FACTS)
    return {row["texture"] for rows in out.values() for row in rows}, list(build.PROBLEMS)


def test_a_style_word_takes_the_worlds_texture_of_that_look():
    assert layers("mud") == ({"ArgoniaNewWorld.esm:000901"}, [])
    assert layers("dirt") == ({"ArgoniaNewWorld.esm:000900"}, [])


def test_a_texture_picked_by_key_is_the_one_painted():
    assert layers("ArgoniaNewWorld.esm:000901") == ({"ArgoniaNewWorld.esm:000901"}, [])
    assert layers("Black Marsh.esm:0A1B2C") == ({"Black Marsh.esm:0A1B2C"}, [])   # a master's own road texture


def test_a_texture_of_a_plugin_that_is_not_loaded_is_a_listed_problem():
    tex, problems = layers("Some Mod.esp:000123")
    assert tex == set() and len(problems) == 1 and "Some Mod.esp:000123" in problems[0]


def test_a_boardwalk_is_painted_only_where_its_line_is_on_dry_land():
    import base64
    flat = base64.b64encode(bytes(33 * 33)).decode()

    def painted(offset_steps):
        build.PROBLEMS.clear()
        facts = dict(FACTS, by_cell={(x, y): {"x": x, "y": y, "water": 0.0, "offset": offset_steps, "deltas": flat}
                                     for x in (-1, 0) for y in (-1, 0)})   # the line's feather reaches the cells beside
        return bool(build.plan_paths([{"id": "p.1", "kind": "walkway", "style": "boardwalk", "points": LINE,
                                       "width": 160}], facts))
    assert painted(5.0)        # the land stands 40 units over the water: the path is on the ground
    assert not painted(-5.0)   # the bed lies 40 units under it: the line is a deck's, nothing is painted
