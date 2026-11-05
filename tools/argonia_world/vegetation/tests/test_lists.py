

def test_upland_trees_are_not_boreal_or_weeping():
    """Round-1 session 1b: drooping cypress, willow, birch read Nordic in the hills (decision 0006)."""
    from tools.argonia_world.vegetation import lists
    f = {"edid": "01cypressmoss", "model": "landscape\\trees\\cypress1.nif", "role_id": "canopy",
         "bound_z0": 0, "bound_z1": 100}
    assert not lists.admits("northern-transition", f)
    assert lists.admits("flooded-forest", f)
    oak = dict(f, edid="ArgoniaTreeOak01", model="argonia\\trees\\treeofwolene2.nif")
    assert lists.admits("western-frontier", oak)


def test_the_willow_is_the_floodplains_signature_and_gorse_is_no_marsh_plant():
    """Lane 1.15-r6-tree-look (0032): the willow curtain only in its own classes; BM&V's gorse nowhere."""
    from tools.argonia_world.vegetation import lists
    w = {"edid": "ArgoniaTreeWillow04", "model": "argonia\\trees\\Willow04.nif", "role_id": "gallery",
         "bound_z0": 0, "bound_z1": 100}
    assert lists.admits("flooded-forest", w) and not lists.admits("interior-swamp", w)
    assert not lists.admits("coastal-lagoon", w)
    g = {"edid": "01giantmushroom", "model": "landscape\\trees\\ztGorsebush04statwhite.nif", "role_id": "shrub",
         "bound_z0": 0, "bound_z1": 100}
    assert not any(lists.admits(e, g) for e in ("flooded-forest", "interior-swamp", "rootland"))
