"""Leaf colour (lane 1.15-r4-red-trees): a red or magenta leaf diffuse drops its form; bark, lilies and the unmeasured stay."""
from tools.argonia_world.vegetation import leaf_hue as lh

M = {"t/fern_red.dds": {"hue": 14, "sat": 0.42, "red_share": 0.66},
     "t/plant_rose.dds": {"hue": 67, "sat": 0.55, "red_share": 0.30},
     "t/leaves_green.dds": {"hue": 72, "sat": 0.39, "red_share": 0.0},
     "t/epinebark04.dds": {"hue": 24, "sat": 0.34, "red_share": 0.24},
     "t/greybrown.dds": {"hue": 5, "sat": 0.1, "red_share": 0.0},
     "textures/plants/groundplants1/lily2.dds": {"hue": 352, "sat": 0.42, "red_share": 0.75}}
MAN = {"meshes": {"meshes/a.nif": {"slots": [[0, "t/fern_red.dds"], [1, "t/fern_red_n.dds"]]},
                  "meshes/b.nif": {"slots": [[0, "t/leaves_green.dds"], [0, "t/epinebark04.dds"]]},
                  "meshes/ztree's/plants/water lily5.nif": {"slots": [[0, "t/plant_rose.dds"]]}}}


def test_red():
    assert lh.red("t/fern_red.dds", M) and lh.red("t/plant_rose.dds", M)
    assert not any(lh.red(t, M) for t in ("t/leaves_green.dds", "t/epinebark04.dds", "t/greybrown.dds",
                                          "textures/plants/groundplants1/lily2.dds", "t/unmeasured.dds"))


def test_forms():
    assert lh.red_textures("a.nif", MAN, M) == ["t/fern_red.dds"]
    assert lh.red_textures("b.nif", MAN, M) == []
    assert lh.red_textures("ztree's\\plants\\water lily5.nif", MAN, M) == []
    bad = lh.problems([{"form_key": "1:x", "model": "a.nif"}, {"form_key": "2:x", "model": "b.nif"}], MAN, M)
    assert len(bad) == 1 and bad[0].startswith("1:x")
