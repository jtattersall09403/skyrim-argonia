

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


def test_no_northern_palette_form_in_any_list():
    """Lane 1.15-r6-no-birch (0006, 0032): no birch, poplar, juniper, bristlecone, pine, spruce, fir or aspen form is
    admitted to any region class, whatever the pool holds (01BIRCH stood in the coastal lagoon's lists)."""
    from tools.argonia_world import db
    from tools.argonia_world.vegetation import lists
    ecos = {r["eco_class_id"] for r in db.open().query("SELECT eco_class_id FROM land_region")}
    for edid, model in (("01BIRCH", "landscape\\trees\\birch-.nif"), ("01redbirch", "landscape\\trees\\birch-red.nif"),
                        ("01Juniper", "landscape\\trees\\dwarfjunip01.nif"), ("01popular", "landscape\\trees\\poplar.nif"),
                        ("01briscone", "landscape\\trees\\vurt_bristlecone1.nif"),
                        ("x", "landscape\\trees\\pinetree01.nif"), ("x", "landscape\\trees\\spruce2.nif"),
                        ("x", "landscape\\trees\\aspen1.nif")):
        f = {"edid": edid, "model": model, "role_id": "canopy", "bound_z0": 0, "bound_z1": 100}
        assert not any(lists.admits(e, f) for e in ecos), edid
    cy = {"edid": "01cypressmoss", "model": "landscape\\trees\\cypress1.nif", "role_id": "canopy",
          "bound_z0": 0, "bound_z1": 100}
    assert lists.admits("flooded-forest", cy)


def test_the_pool_holds_no_northern_form_in_the_built_lists():
    from tools.argonia_world import db
    from tools.argonia_world.vegetation import lists
    for r in db.open().query("SELECT edid, model, role_id FROM object_form"):
        f = dict(r, bound_z0=0, bound_z1=100)
        if any(n in f"{r['edid']} {r['model']}".lower() for n in lists.NORTHERN_PALETTE):
            assert not any(lists.admits(e, f) for e in ("coastal-lagoon", "flooded-forest", "northern-transition"))
