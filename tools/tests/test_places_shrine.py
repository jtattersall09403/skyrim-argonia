from tools.places.draft.run import shrine_swap

BASES = {"K:young": {"key": "K:young", "edid": "HistTree04", "bounds": [[-254, -278, -24], [333, 296, 593]]},
         "K:great": {"key": "K:great", "edid": "HistTree03", "bounds": [[-658, -731, -162], [734, 713, 1381]]}}


def row():
    return {"id": "p.station.shrine", "base": "K:young", "kind": "static", "pos": [0.0, 0.0, 0.0],
            "rot": [0.0, 0.0, 0.0], "scale": 1.0, "seat": {"mode": "ground", "dz": 0.0},
            "why": "shrine: the record promises a Hist blessing"}


def test_a_city_great_tree_takes_the_named_base_and_scale_in_place():
    r = row()
    assert shrine_swap(r, {"shrine": {"base": "K:great", "scale": 1.5}}, BASES)
    assert (r["base"], r["scale"], r["pos"], r["id"]) == ("K:great", 1.5, [0.0, 0.0, 0.0], "p.station.shrine")
    assert not shrine_swap(r, {"shrine": {"base": "K:great", "scale": 1.5}}, BASES)


def test_no_draft_shrine_or_another_row_is_left_alone():
    r = row()
    assert not shrine_swap(r, {}, BASES) and r["base"] == "K:young"
    other = dict(row(), why="a lantern")
    assert not shrine_swap(other, {"shrine": {"base": "K:great"}}, BASES) and other["base"] == "K:young"
