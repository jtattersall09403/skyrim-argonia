

def test_upland_trees_are_not_boreal_or_weeping():
    """Round-1 session 1b: drooping cypress, willow, birch read Nordic in the hills (decision 0006)."""
    from tools.argonia_world.vegetation import lists
    f = {"edid": "01cypressmoss", "model": "landscape\\trees\\cypress1.nif", "role_id": "canopy",
         "bound_z0": 0, "bound_z1": 100}
    assert not lists.admits("northern-transition", f)
    assert lists.admits("flooded-forest", f)
    oak = dict(f, edid="ArgoniaTreeOak01", model="argonia\\trees\\treeofwolene2.nif")
    assert lists.admits("western-frontier", oak)
