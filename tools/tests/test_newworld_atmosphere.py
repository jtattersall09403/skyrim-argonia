"""The new world's atmosphere (tools/newworld/atmosphere.py) and low mist (tools/newworld/world/mist.py): the colour
rules, the sources, the spec built over synthetic vanilla records, the mist's measures."""
from __future__ import annotations

import json

import pytest

from tools.newworld import atmosphere as A
from tools.newworld.world import mist as M


def test_kelvin_runs_from_orange_to_blue_white():
    low, d65, high = A.kelvin_rgb(2000), A.kelvin_rgb(6500), A.kelvin_rgb(12000)
    assert low[0] > low[1] > low[2]
    assert min(d65) >= 245
    assert high[2] >= high[0]
    assert abs(A.cct(A.kelvin_rgb(5000)) - 5000) < 400


def test_recolour_keeps_the_source_level_and_takes_the_target_hue():
    src, tgt = [99, 115, 139], [210, 190, 150]
    out = A.recolour(src, tgt)
    assert abs(A.lum(out) - A.lum(src)) < 1.5
    assert A.warmth(out) > 0 > A.warmth(src)
    assert A.recolour(src, tgt, strength=0.0) == src
    assert max(A.recolour([250, 250, 250], [255, 120, 0], gain=2.0)) <= 255


def test_visibility_falls_with_humidity_and_aerosol():
    cls, _ = A.load_sources()
    mid = cls["bands"]["middle"]
    dry = {"rh": 0.6, "aerosol": 1.0}
    wet = {"rh": 0.88, "aerosol": 1.0}
    smoky = {"rh": 0.88, "aerosol": 1.15}
    assert A.visibility(dry, mid, cls) > A.visibility(wet, mid, cls) > A.visibility(smoky, mid, cls)
    assert A.visibility({"rh": cls["rh_reference"], "aerosol": 1.0}, mid, cls) == pytest.approx(1.0)


def test_sources_are_whole():
    cls, regs = A.load_sources()
    kinds = cls["kinds"]
    for cid, c in cls["classes"].items():
        assert c["family"] in cls["families"], cid
        assert set(c["chances"]) == set(kinds) and sum(c["chances"].values()) == 100, cid
        for f in ("sun_k", "haze", "fill", "sky"):
            assert set(c[f]) == set(A.TODS), (cid, f)
        assert 0 < c["mist"]["full_vis"] <= 1 and c["mist"]["scale"][0] < c["mist"]["scale"][1]
    for fam in cls["families"].values():
        assert set(kinds) <= set(fam)
    for rid, (cid, _aspect, why) in regs["regions"].items():
        assert cid in cls["classes"] and why, rid
    for band in cls["bands"].values():
        for k, ch in band["chances"].items():
            assert k in kinds and isinstance(ch, int)


def test_every_region_of_the_database_has_a_class():
    from tools.argonia_world import db
    w = db.open("newworld")
    regions = {r.id for r in w.rows("region")}
    rc = A.region_classes(w)
    assert set(rc) == regions
    assert {b for _, b in rc.values()} <= set(A.BANDS)
    aspects = {a.id for a in w.rows("note_aspect")}
    _, regs = A.load_sources()
    assert {aspect for _c, aspect, _w in regs["regions"].values()} <= aspects  # load() refuses any other


@pytest.mark.parametrize("band", A.BANDS)
def test_chances_sum_to_a_hundred_with_every_kind(band):
    cls, _ = A.load_sources()
    for c in cls["classes"].values():
        ch = A.chances(c, cls["bands"][band], cls["kinds"])
        assert sum(ch.values()) == 100 and min(ch.values()) >= 1


def _colour_set(seed: int) -> dict:
    return {t: [(seed * 37 + i * 11 + 60) % 200 + 20 for i in range(3)] for t in A.TODS}


def synthetic_study() -> dict:
    """Vanilla-shaped records for every source weather the families name, with their image spaces and VOLI."""
    cls, _ = A.load_sources()
    wthr, imgs, voli, n = [], [], [], 0x100
    slots = list(A.SLOT_ROLE) + ["WaterMultiplierColor"]
    vl = {}
    for ti, t in enumerate(A.TODS):
        fk = f"{0xD50 + ti:06X}:Update.esm"
        voli.append({"FormKey": fk, "EditorID": f"VL{t}", "DensityContribution": 0.3})
        vl[t] = fk
    names = {src.split(":")[1] for fam in [*cls["families"].values(), cls["reference_fog"]] for k, src in fam.items() if k != "why"}
    for edid in sorted(names):
        n += 1
        ims = {}
        for ti, t in enumerate(A.TODS):
            ifk = f"{0x2000 + n * 4 + ti:06X}:Skyrim.esm"
            imgs.append({"FormKey": ifk, "EditorID": f"IS{edid}{t}", "Tint": {"Color": [200, 200, 200], "Amount": 0.5},
                         "Cinematic": {"Saturation": 1.2}})
            ims[t] = ifk
        rec = {"FormKey": f"{n:06X}:Skyrim.esm", "EditorID": edid, "FogDistanceDayFar": 80000.0, "FogDistanceNightFar": 40000.0,
               "ImageSpaces": ims, "VolumetricLighting": vl,
               "DirectionalAmbientLightingColors": {t: {s: [90, 100, 110] for s in A.DALC_SIDES + ("DirectionalZPlus", "DirectionalZMinus")}
                                                    for t in A.TODS}}
        for i, s in enumerate(slots):
            rec[s] = _colour_set(n + i)
        wthr.append(rec)
    return {"Skyrim.esm": {"WTHR": wthr, "IMGS": imgs, "VOLI": []}, "Update.esm": {"WTHR": [], "IMGS": [], "VOLI": voli}}


def test_spec_over_synthetic_records():
    cls, regs = A.load_sources()
    rec = A.Records(synthetic_study(), A.VANILLA)
    rc = {rid: (cid, ("north", "middle", "south")[i % 3]) for i, (rid, (cid, _a, _w)) in enumerate(sorted(regs["regions"].items()))}
    sp = A.build_spec(rec, rc)
    ids = [e["formid"] for k in ("weathers", "imagespaces", "volumetric") for e in sp[k]] + [sp["climate"]["formid"]]
    assert len(ids) == len(set(ids))
    for sig, key in (("WTHR", "weathers"), ("IMGS", "imagespaces"), ("VOLI", "volumetric")):
        lo = A.BASE[sig]
        hi = min(v for v in A.BASE.values() if v > lo)
        assert all(lo <= e["formid"] < hi for e in sp[key]), sig
    edids = {e["edid"] for e in sp["weathers"]}
    for rid, lst in sp["regions"].items():
        assert sum(ch for _, ch in lst) == 100 and all(w in edids for w, _ in lst), rid
        assert len(lst) == len(cls["kinds"])
    fair = next(e for e in sp["weathers"] if e["kind"] == "fair")
    assert fair["set"]["FogDistanceNightFar"] == cls["classes"][fair["class"]]["night_mist"]["far"]
    steam = next(e for e in sp["weathers"] if e["kind"] == "steam" and e["class"] == fair["class"] and e["band"] == fair["band"])
    mist = next(e for e in sp["weathers"] if e["kind"] == "mist" and e["class"] == fair["class"] and e["band"] == fair["band"])
    assert steam["set"]["FogDistanceDayFar"] < mist["set"]["FogDistanceDayFar"]
    assert all("volumetric" not in e for e in sp["weathers"] if e["kind"] in ("rain", "storm"))
    json.dumps(sp)


def test_class_distances_pick_the_closest_band_set():
    c = {"Day": [100, 100, 100], "Sunrise": [100, 100, 100]}
    far = {"Day": [200, 100, 50], "Sunrise": [200, 100, 50]}
    cols = {"a/north": {"list": {s: c for s in A.MEASURE_SLOTS}}, "a/south": {"list": {s: far for s in A.MEASURE_SLOTS}},
            "b/middle": {"list": {s: far for s in A.MEASURE_SLOTS}}}
    assert A.class_distances(cols)["a vs b"] == pytest.approx(0.0)


def test_mist_measures():
    assert M.per_site(0.0) == 0 and M.per_site(1.0) < M.per_site(2.0) <= 1.0
    assert M.spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
    assert M.spearman([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)
    cells = {"0,0": {"water": "green-marsh", "region": "x"}, "1,0": {"region": "x"}, "2,0": {"water": "river-SE", "region": "x"}}
    d = M.density([(0, 0), (0, 0), (2, 0)], cells)
    assert d["green-marsh"]["refs"] == 2 and d["green-marsh"]["per_ha"] == pytest.approx(2 / M.CELL_HA, abs=0.01)
    assert d["river"]["refs"] == 1 and d["land"]["refs"] == 0
