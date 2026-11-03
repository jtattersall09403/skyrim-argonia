"""L1/L2 on small fixtures: the migration's rows, the classifier's helpers, the region record writers' maths."""
from tools.argonia_world import skyrim_units as su
from tools.argonia_world.regions import api
from tools.argonia_world.regions import classify as K
from tools.argonia_world.regions import migrate as M


def _docs():
    states = [{"id": s, "name": s.title(), "visibilityFactor": 1.0, "wetness": 0.0}
              for s in ("clear-humid", "ground-mist", "storm")]
    weather = {"states": states, "regionFrequencies": {k: {"clear-humid": 5, "storm": 1} for k in M.GROUPS},
               "seasons": [{"id": "wet", "name": "Wet", "share": 0.5, "effects": "rain"},
                           {"id": "dry", "name": "Dry", "share": 0.5, "effects": "sun"}]}
    pal = {"byRegionClass": {str(rid): {"note": None, "layers": [
        {"role": next(iter(M.ROLE_OF)), "instances_per_hectare": 4, "clump_size_median": 2, "clump_radius_m": 3}]}
        for rid, _, _, _ in M.RASTER}}
    over = {"confidence": "owner", "overrides": [{"id": "o1", "regionClass": M.RASTER[0][0],
                                                  "polygonUV": [[0, 0], [1, 0], [1, 1]],
                                                  "appliesToClasses": [M.RASTER[1][0]]}]}
    return weather, over, pal


def test_rows_from_keys_every_table():
    out = M.rows_from(*_docs())
    assert len(out["weather_state"]) == 3
    assert len(out["weather_group_weight"]) == 2 * len(M.GROUPS)
    assert [p["ord"] for p in out["region_class_override_point"]] == [0, 1, 2]
    assert len(out["region_class_profile"]) == len(M.RASTER)
    assert {r["season_id"] for r in out["season"] and out["season_factor"]} <= {"wet", "dry", "hatching"}


def test_runs_tile_each_row():
    grid = [["a", "a", "b"], ["c", "c", "c"]]
    rs = K.runs(grid)
    assert [(r["cx1"] - r["cx0"] + 1, r["land_region_id"]) for r in rs] == [(2, "a"), (1, "b"), (3, "c")]
    assert rs[0]["cy"] != rs[2]["cy"]


def test_majority_removes_speckle_only():
    g = [["a"] * 3, ["a", "b", "a"], ["a"] * 3]
    assert K.majority(g)[1][1] == "a"
    g = [["a", "b", "b"], ["a", "b", "a"], ["a"] * 3]
    assert K.majority(g)[1][1] == "b"  # it has a neighbour of its own class


def test_in_polygon():
    sq = [(0, 0), (1, 0), (1, 1), (0, 1)]
    assert K.in_polygon(0.5, 0.5, sq) and not K.in_polygon(1.5, 0.5, sq)


def test_vote_is_deterministic():
    assert K.vote(["b", "a", "b", "a"]) == "a"


def test_rectangles_merge_rows_and_cover_every_cell():
    runs = [{"cy": 0, "cx0": 0, "cx1": 2}, {"cy": 1, "cx0": 0, "cx1": 2}, {"cy": 2, "cx0": 1, "cx1": 1},
            {"cy": 4, "cx0": 0, "cx1": 2}]
    rects = api.rectangles(runs)
    assert rects == [(0, 0, 2, 1), (1, 2, 1, 2), (0, 4, 2, 4)]
    cells = {(x, y) for x0, y0, x1, y1 in rects for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)}
    assert len(cells) == 3 + 3 + 1 + 3


def test_area_is_the_cells_outline_in_units():
    pts = api.area(-1, 2, 0, 2)
    assert pts[0] == [-su.CELL_UNITS, 2 * su.CELL_UNITS] and pts[2] == [su.CELL_UNITS, 3 * su.CELL_UNITS]


def test_slot_check_catches_the_old_ladder_and_passes_authored():
    from tools.argonia_world.checks import derived_colours
    base = (140, 154, 110)
    ladder = {(slot, "day"): tuple(round(v * k) for v in base) for slot, k in (("a", 0.7), ("b", 1.0), ("c", 1.2))}
    assert derived_colours(ladder)  # a scaled copy
    mixed = {("a", "day"): (100, 120, 80), ("b", "day"): (200, 100, 60), ("c", "day"): (150, 110, 70)}
    assert derived_colours(mixed)  # c is halfway between a and b
    assert not derived_colours({("a", "day"): (100, 120, 80), ("b", "day"): (90, 140, 70), ("s", "day"): (0, 0, 0)})


def test_seed_palettes_author_every_slot_and_none_is_derived():
    from tools.argonia_world.checks import _rgb, derived_colours
    from tools.argonia_world.regions import weather_seed as S
    assert set(S.P) == set(S.WEATHERS) == set(S.SKY) == set(S.WHY_SLOT)
    for wid, pal in S.P.items():
        assert set(pal) == set(S.ROLE), wid
        assert not derived_colours({(s, t): _rgb(h) for s, r in pal.items() for t, h in zip(S.TOD, r)}), wid
        assert sum(_rgb(pal["skyUpper"][3])) < sum(_rgb(pal["skyUpper"][1]))  # night darker than day


def test_regime_rule():
    eco = {"name": "x", "weather_group_id": "marsh", "misty": 1}
    assert M.regime_of(eco, {"border-mountains": 6, "firm-lowland": 4})[0] == "montane"
    assert M.regime_of(dict(eco, weather_group_id="coastal"), {"ocean": 3})[0] == "sea_fog"
    assert M.regime_of(eco, {"fringe-marsh": 3})[0] == "radiation"
    assert M.regime_of(dict(eco, misty=0), {"firm-lowland": 3})[0] == "none"


def test_ambient_reads_the_authored_faces():
    col = {s: {t: [i, i + 1, i + 2] for t in api.TOD} for i, s in enumerate(("dalcUp", "dalcSide", "dalcDown"))}
    amb = api.ambient(col)
    assert amb["day"]["zPlus"] == [0, 1, 2] and amb["day"]["xMinus"] == [1, 2, 3] and amb["night"]["zMinus"] == [2, 3, 4]


def test_object_list_mixes_classes_by_share(monkeypatch):
    class W:
        def query(self, sql, *a):
            if "object_form" in sql:
                return [{"form_key": "000001:Skyrim.esm", "role_id": "rock"},
                        {"form_key": "000002:Skyrim.esm", "role_id": "rock"}]
            return [{"role_id": "rock", "per_ha": 4.0 if a[0] == "x" else 0.0, "clump_median": 2,
                     "clump_radius_m": 5, "slope_max_deg": 30, "water_min_m": None, "water_max_m": None}]
    out = K.object_list(W(), {"x": 1, "y": 1})
    assert [o["density_per_ha"] for o in out] == [1.0, 1.0]  # 4/ha over half the cells, split over two forms
    assert all(o["conform"] for o in out)


def test_border_has_a_shell_every_cell_lists():
    # game-19 s09: the engine holds the player only at a border region the cell's XCLR lists (Skyrim.esm lists
    # BorderRegionSkyrim in 5,610 cells); ours linked none and the player walked 16 m past the west edge.
    from tools.argonia_world import db
    w = db.open()
    border = api.border_shell_key(w)
    assert border and border.endswith(":ArgoniaWorld.esm")
    assert border in {r["formKey"] for r in api.shell_records(w)}
    from tools.argonia_world.terrain import world as tw
    assert tw.document((0, 0, 0, 0), __import__("pathlib").Path("."), w)["borderRegion"] == border


def test_border_listed_only_on_cells_inside_the_polygon():
    # vanilla's rule (Skyrim.esm: 5,609 of 5,610 listed cells have a corner inside BorderRegionSkyrim's polygon);
    # listing every cell let the player walk 2 km past the west edge (game-20 s09)
    from tools.argonia_world import skyrim_units as su
    runs = api.border_cell_runs()
    x0, y0 = su.PROVINCE_CELL_SW
    n = su.PROVINCE_CELLS
    assert {(r["cx0"], r["cx1"]) for r in runs} == {(x0, x0 + n - 1)}
    assert [r["cy"] for r in runs] == list(range(y0, y0 + n))
    tri = [[0.0, 0.0], [4096.0 * 3, 0.0], [0.0, 4096.0 * 3]]  # a triangle: the diagonal cells straddle the edge
    cells = {(cx, r["cy"]) for r in api.border_cell_runs(tri) for cx in range(r["cx0"], r["cx1"] + 1)}
    assert (0, 0) in cells and (2, 0) in cells and (1, 1) in cells and (2, 2) not in cells and (-1, 0) not in cells


def test_border_wall_closes_the_polygon():
    # the native fallback: CollisionMarker boxes on every border edge, overlapping, no gap at the corners
    import math
    poly = api.border_polygon()
    pieces = api.border_wall_pieces(poly)
    assert len(pieces) == 4 * su.PROVINCE_CELLS
    for e in range(4):
        ps = [p for p in pieces if p["edge"] == e]
        assert math.isclose(sum(p["length"] for p in ps), su.PROVINCE_CELLS * su.CELL_UNITS)
    south = [p for p in pieces if p["edge"] == 0]  # SW -> SE: along +x, the box's x already runs east
    assert all(math.isclose(p["yaw"], 0.0) and math.isclose(p["y"], poly[0][1]) for p in south)
    west = [p for p in pieces if p["edge"] == 3]  # NW -> SW: along -y, yaw 90 turns the box's x to north-south
    assert all(math.isclose(p["yaw"], 90.0) for p in west)

    class A:
        def form_key(self, e, t, k):
            return "000800:Argonia.esm"
    refs = api.border_wall_refs(A(), lambda x, y: 3.0)
    assert {r["base"] for r in refs} == {"000021:Skyrim.esm"}
    assert all(r["primitive"]["bounds"][0] >= r["primitive"]["bounds"][1] for r in refs)


def test_hundred_sums_to_exactly_100():
    from tools.argonia_world.regions.season import hundred
    for raw in ({"a": 1, "b": 1, "c": 1}, {"a": 35, "b": 13.3, "c": 51.7}, {"a": 0.2, "b": 7}):
        assert sum(hundred(raw).values()) == 100
    assert hundred({"a": 0}) == {"a": 0}


def test_fog_check_holds_vanilla_ranges():
    """The old mist (180/120 m, below SkyrimFog) and the old clear-dry (3,800 m day far) fail; the seed passes."""
    from tools.argonia_world import checks as C
    from tools.argonia_world.regions import weather_seed as S

    class W:
        def __init__(self, cls):
            self.cls = cls

        def query(self, *_):
            return [{"classification": self.cls}]

    def row(wid, dn, df, nn, nf):
        return {"id": wid, "fog_day_near_m": dn, "fog_day_far_m": df, "fog_night_near_m": nn, "fog_night_far_m": nf}

    assert C.fog_outside_vanilla(W("Cloudy"), row("mist", 0, 180, 0, 120), True)
    assert C.fog_outside_vanilla(W("Pleasant"), row("clear-dry", 60, 3800, 20, 1400), False)
    for wid, v in S.WEATHERS.items():
        assert not C.fog_outside_vanilla(W(S.SKY[wid][0]), row(wid, *v[3:7]), wid in ("mist", "sea-fog",
                                                                                      "montane-haze")), wid


def test_regimes_hold_marsh_fog_in_vanilla_band():
    from tools.argonia_world.regions import weather_seed as S
    assert all(28 <= c <= 35 for c, _ in S.REGIMES["radiation"][2].values())
    assert all(sum(map(len, st.values())) <= 5 for st in S.REALISE.values())  # + the mist weather: <= 6 entries


def test_no_weather_hides_the_sky():
    """Owner play test 3 finding 18: every weather's fog far at least vanilla's class median (day and night: sunrise
    and sunset lie between them), near above 0, fog max at most SkyrimFog's 0.95, and an authored, non-grey zenith at
    every time of day. The old mist (night far 215 m, near 0, max 1.0) and a grey dusk zenith fail."""
    from tools.argonia_world import checks as C
    from tools.argonia_world import skyrim_units as su
    from tools.argonia_world.regions import weather_seed as S

    class W:
        def __init__(self, cls):
            self.cls = cls

        def query(self, *_):
            return [{"classification": self.cls}]

    def row(wid, dn, df, nn, nf):
        return {"id": wid, "fog_day_near_m": dn, "fog_day_far_m": df, "fog_night_near_m": nn, "fog_night_far_m": nf}

    old = C.fog_outside_vanilla(W("Cloudy"), row("mist", 0, 700, 0, 215), True)
    assert any("median" in e for e in old) and any("starts at the eye" in e for e in old)
    assert C.sky_blocked("Cloudy", {"fog_day_max": 1.0, "fog_night_max": 1.0}, {"sunset": (0x6B, 0x6A, 0x6A)})
    for wid, v in S.WEATHERS.items():
        cls, fmax = S.SKY[wid][0], S.SKY[wid][10:12]
        assert not C.fog_outside_vanilla(W(cls), row(wid, *v[3:7]), False), wid
        upper = dict(zip(S.TOD, (C._rgb(h) for h in S.P[wid]["skyUpper"])))
        assert not C.sky_blocked(cls, {"fog_day_max": fmax[0], "fog_night_max": fmax[1]}, upper), wid
        assert all(su.metres_to_units(m) > 0 for m in (v[3], v[5])), wid


def test_height_fog_lies_below_the_eye():
    """The Community Shaders Exponential Height Fog the stack lays (data/dependencies.json, community-shaders' files):
    density 2^(-falloff/1000 * (z - fogHeight)) (ExponentialHeightFog.hlsli), so the bank's top (a tenth of its
    density) is fogHeight + log2(10) * 1000 / falloff. On the flattest ground the world panel stands on (its shore
    vantage's lowest, 0.3 m above sea-level water) that top is below the play camera, and the volumetric part is on."""
    import json
    import math
    from pathlib import Path
    from tools.argonia_world import panel
    from tools.argonia_world import skyrim_units as su
    deps = json.loads((Path(__file__).resolve().parents[4] / "data" / "dependencies.json").read_text())
    rows = deps if isinstance(deps, list) else deps.get("dependencies", deps.get("mods", []))
    text = next(f["text"] for d in rows for f in d.get("files", [])
                if f["path"].endswith("Argonia_ExponentialHeightFog.json"))
    fog = json.loads(text)
    assert fog["enabled"] == 1 and fog["volumetricFogEnabled"] == 1 and fog["volumetricFogDistance"] > 0
    assert fog["fogDensity"] > 0 and fog["disableVanillaFog"] == 0
    top = fog["fogHeight"] + math.log2(10) * 1000 / fog["fogHeightFalloff"]
    eye = su.metres_to_units(panel.SHORE_LO_M) + su.EYE_HEIGHT_UNITS
    assert top < eye, (top, eye)
    assert fog["fogHeight"] <= su.metres_to_units(panel.SHORE_LO_M)  # the bank is densest on the ground, not above it


def test_every_mist_region_has_a_bank_between_its_water_and_eye():
    """Planner's decision (round 4): the CS height fog is one absolute Z per weather, so each regime's mist weather is
    copied per water-level band (weather_mist_band); every region with a mist regime lists a band whose bank top
    (fogHeight + BANK_TOP_U) lies between its median water level and that water's eye, and the per-weather files the
    stack lays match the bands."""
    from tools.argonia_world import db
    from tools.argonia_world import skyrim_units as su
    from tools.argonia_world.formids import Allocator
    from tools.argonia_world.regions import api, migrate
    from tools.argonia_world.regions import weather_seed as S
    w = db.open()
    water = migrate.region_water_m(w)
    top = {r["weather_id"]: r["fog_height_u"] + S.BANK_TOP_U for r in w.query("SELECT * FROM weather_mist_band")}
    bad = []
    for r in w.values("SELECT land_region_id FROM region_mist WHERE regime != 'none'"):
        lv = su.metres_to_units(water[r])
        if not any(lv <= top[x] <= lv + su.EYE_HEIGHT_UNITS
                   for x in w.values("SELECT weather_id FROM land_region_weather WHERE land_region_id = ?", r) if x in top):
            bad.append((r, water[r]))
    assert not bad and len(water) == len(w.values("SELECT 1 FROM region_mist WHERE regime != 'none'")), bad
    assert not api.sync_cs_fog(False)
    assert len(api.cs_fog_files(Allocator(w, frozen=True), w)) == len(top)


def test_panel_journey_forces_each_regions_own_current_weather():
    """world-panel.yaml's `sw` and its read-back are, per vantage and hour, the region's own weather (a band copy
    re-seeded to new ids leaves an old edid forcing the wrong weather: round 4's first batch), and that weather is in
    the region's list and has a FormID."""
    import json
    from pathlib import Path
    from tools.argonia_world import db, panel
    w = db.open()
    text = (Path(__file__).resolve().parents[4] / "tests" / "journeys" / "world-panel.yaml").read_text()
    steps = {s["name"]: s for s in json.loads(text[text.index('{\n "id"'):])["steps"]}
    keyed = {r.editor_id for r in w.rows("formid") if r.record_type == "WTHR"}
    by_ref = {f"{r.plugin}|0x{r.form_id:06X}": r.editor_id for r in w.rows("formid") if r.record_type == "WTHR"}
    for v in panel.vantages(w):
        lr_list = {r["edid"] for r in w.query("SELECT w.edid FROM land_region_weather l JOIN weather w "
                                              "ON w.id = l.weather_id WHERE l.land_region_id = ?", v["land_region"])}
        for when in ("noon", "dawn"):
            edid = v[when]
            s = steps[f"{v['id']}-{when}"]
            lines = [d["console"] if isinstance(d["console"], str) else d["console"]["line"]
                     for d in s["do"] if "console" in d]
            forced = [by_ref.get(ln.split(" ", 1)[1], ln.split(" ", 1)[1]) for ln in lines if ln.startswith(("sw ", "fw "))]
            assert forced and set(forced) == {edid}, (s["name"], edid, forced)  # set and forced by its runtime form id
            assert [e["eq"] for e in s["expect"] if e.get("read") == ["weather"]] == [edid], s["name"]
            assert edid in lr_list and edid in keyed, (s["name"], edid)
