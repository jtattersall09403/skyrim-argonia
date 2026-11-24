from tools.places.own_bases import SAP_POOL
from tools.places.stock.plan import plugins_of


def test_own_bases_pseudo_plugin_is_never_read_as_a_file():
    names = plugins_of([SAP_POOL, "Skyrim.esm:000001", "King of the Murkmire.esp:0000AA"])
    assert "ArgoniaOwn.esp" not in names and "King of the Murkmire.esp" in names


def test_hammock_bed_and_weathered_twins_are_planned_with_their_records():
    from tools.places import own_bases as ob
    twin = next(iter(ob.TWINS))
    refs = [{"base": ob.HAMMOCK_BED}, {"base": twin}, {"base": twin}]
    seen = []

    def ids(name):
        seen.append(name)
        return f"Argonia.esp:{len(seen):06X}"

    rows = ob.plan_own(refs, ids, "test-place")
    kinds = [r["kind"] for r in rows]
    assert kinds.count("furniture") == 1 and kinds.count("material") == 1 and kinds.count("static") == 1
    bed = next(r for r in rows if r["kind"] == "furniture")
    assert bed["copy"] == "Journey to Baan Malur.esp:0FFA2B" and bed["edid"].startswith("ArgoniaHammockBed_")
    st = next(r for r in rows if r["kind"] == "static")
    mat = next(r for r in rows if r["kind"] == "material")
    assert st["material"] == mat["fk"] and st["angle"] in (75, 90)
    assert all(r["base"].startswith("Argonia.esp:") for r in refs)


def test_twin_family_is_three_per_model_with_unique_keys_and_rows():
    from tools.places import own_bases as ob
    assert len(ob.TWINS) == 3 * len(ob.TWIN_FAMILY) and 10 <= len(ob.TWIN_FAMILY) <= 20
    assert len({t["edid"] for t in ob.TWINS.values()}) == len(ob.TWINS)
    keys = {r["key"] for r in ob.own_rows()}
    assert ob.HAMMOCK_BED in keys and set(ob.TWINS) <= keys


def test_pack_statics_are_unique_own_keys_and_planned_as_model_statics():
    from tools.places import own_bases as ob
    ps = ob.PACK_STATICS
    assert ps and all(ob.is_own(k) for k in ps)
    assert len({a["edid"] for a in ps.values()}) == len(ps)
    assert not set(ps) & (set(ob.TWINS) | set(ob.STATICS) | set(ob.FURNITURE) | set(ob.ACTIVATORS))
    assert {a["pack"] for a in ps.values()} == {"ships-and-boats-of-tamriel", "incaendo-banner-resource",
                                                "morrowind-hlaalu-architecture", "phitt-velothi-resources"}
    k = next(iter(ps))
    refs = [{"base": k}]
    rows = ob.plan_own(refs, lambda n: f"Argonia.esp:{abs(hash(n)) % 0xFFFFFF:06X}", "test-place")
    assert rows[0]["kind"] == "modelstatic" and rows[0]["model"] == ps[k]["model"]
    assert refs[0]["base"].startswith("Argonia.esp:")
    assert any(r["key"] == k and r["type"] == "STAT" for r in ob.own_rows())
