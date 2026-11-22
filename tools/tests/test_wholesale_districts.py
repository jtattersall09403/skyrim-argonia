"""Districts (place.json `fit.districts`, tools/places/draft/heights.py): a source town whose districts sat at
different heights on a hill is laid on flat ground of ours with one offset per district body: each district's pieces
rigidly at its offset ("auto": our ground less the source's under its buildings), the ground under it its own terrace
at that offset (so a house stands on ours, not on a pedestal or in a pit), and a loose piece following the carried
ground; the carried walking mesh and the rooms' arrivals read the same heights."""
import math
import types

from tools.places.draft import heights, srcnav, wholesale
from tools.places.seat import Ground


def _ground(fn):
    cells = {}
    for cx in range(-1, 3):
        for cy in range(-1, 2):
            cells[(cx, cy)] = [fn(cx * 4096 + c * 128, cy * 4096 + r * 128) for r in range(33) for c in range(33)]
    return Ground(cells, {}, None)


def _hill(x, y):           # the source: low ground west of x=3000, a terrace at 1000 east of x=5000, a slope between
    return 0.0 if x < 3000 else 1000.0 if x > 5000 else (x - 3000) / 2


def _standing(monkeypatch, districts):
    import tools.places.extract as extract
    ours = _ground(lambda x, y: 100.0)
    monkeypatch.setattr(extract, "load_place", lambda pid: {"world_x": 4000.0, "world_y": 2000.0})
    monkeypatch.setattr(wholesale.Ground, "load", staticmethod(lambda p: _ground(lambda x, y: 100.0)))
    refs = [{"id": "low.house", "base": "b", "kind": "building", "pos": [1000.0, 2000.0, 40.0]},
            {"id": "low.door", "base": "b", "kind": "door", "pos": [1200.0, 2000.0, 10.0]},
            {"id": "high.house", "base": "b", "kind": "building", "pos": [7000.0, 2000.0, 1040.0]},
            {"id": "high.post", "base": "b", "kind": "static", "pos": [7300.0, 2000.0, 1000.0]},
            {"id": "slope.plant", "base": "b", "kind": "plant", "pos": [4000.0, 2000.0, 500.0]}]
    of = {"low.house": "b01", "low.door": "b01", "high.house": "b02", "high.post": "b02"}
    place = {"fit": {"pivot": [4000.0, 2000.0], "anchor": [4000.0, 2000.0], "rot_deg": 0.0, "districts": districts},
             "radius_m": 100}
    return types.SimpleNamespace(place_id="x", place=place, src_ext=refs, by_src={r["id"]: r for r in refs}, bases={},
                                 clusters=(None, of, None), grd=types.SimpleNamespace(path="g"), S=_ground(_hill),
                                 G=ours)


def test_each_district_stands_on_our_ground(monkeypatch):
    st = _standing(monkeypatch, [{"name": "low", "clusters": ["b01"], "offset": "auto"},
                                 {"name": "high", "clusters": ["b02"], "offset": "auto"}])
    ext, ledger, land, rep = wholesale.lay(st, 0.0, cap=280.0)
    z = {r["src"]: r["pos"][2] for r in ext}
    offs = {d["name"]: d["offset"] for d in rep["districts"]}
    assert offs == {"low": 100.0, "high": -900.0}
    assert z["low.house"] == 140.0 and z["low.door"] == 110.0          # its own height over its own ground, on ours
    assert z["high.house"] == 140.0 and z["high.post"] == 100.0        # the hill's terrace brought down whole
    G1 = _ground(lambda x, y: 100.0)
    G1.apply_patches(land)
    assert abs(G1.height(7000, 2000) - 100.0) < 1 and abs(G1.height(1000, 2000) - 100.0) < 1   # no pedestal, no pit
    plant = z["slope.plant"]                                            # the loose plant follows the carried ground
    assert abs((plant - 500.0) - (G1.height(4000, 2000) - _hill(4000, 2000))) < 1
    rise = {lr["src"]: lr["rise"] for lr in ledger if lr["status"] == "placed"}
    assert rise["high.house"] == -900.0 and rise["low.door"] == 100.0


def test_a_fixed_offset_and_the_terrace_capped(monkeypatch):
    st = _standing(monkeypatch, [{"name": "high", "clusters": ["b02"], "offset": -700}])
    ext, _, land, rep = wholesale.lay(st, 0.0, cap=280.0)
    z = {r["src"]: r["pos"][2] for r in ext}
    assert z["high.house"] == 340.0
    G1 = _ground(lambda x, y: 100.0)
    G1.apply_patches(land)
    # the terrace wants 200 more here (-700 + 1000 against our 100); held softly within the cap
    assert 100.0 + 150 < G1.height(7000, 2000) < 100.0 + 200


def test_a_district_without_its_terrace(monkeypatch):
    # a landing whose source ground was the sea bed: laid rigidly at its offset, our ground kept about it
    st = _standing(monkeypatch, [{"name": "landing", "clusters": ["b02"], "offset": 0, "terrace": False}])
    ext, _, land, rep = wholesale.lay(st, 0.0, cap=280.0)
    assert {r["src"]: r["pos"][2] for r in ext}["high.house"] == 1040.0
    assert rep["districts"][0]["terrace"] is False
    G1 = _ground(lambda x, y: 100.0)
    G1.apply_patches(land)
    assert abs(G1.height(7000, 2000) - 100.0) < 1


def test_rooms_of_a_shared_cell_keep_their_own_doors():
    # the source packs two houses' rooms into one cell; each copy keeps its own way out and its door leads into it
    def door(i, to, pos):
        return {"id": i, "base": "d", "kind": "door", "pos": pos, "door": {"to_ref": to, "to_pos": pos, "to_space": "x"}}
    cell = [door("q1", "e1", [0.0, 0.0, 0.0]), door("q2", "e2", [500.0, 0.0, 0.0])]
    ext = [{"id": "x.e1", "src": "e1", "door": {"to_space": "cell", "to_ref": "q1"}},
           {"id": "x.e2", "src": "e2", "door": {"to_space": "cell", "to_ref": "q2"}}]
    spaces = {"exterior": {"refs": ext},
              "cell": {"space": {"copy_of": "src/cell", "room": "q1"}, "refs": []},
              "cell.2": {"space": {"copy_of": "src/cell", "room": "q2"}, "refs": []},
              "cell.3": {"space": {"copy_of": "src/cell", "room": "q1", "added": True}, "refs": [{"id": "own"}]}}
    st = types.SimpleNamespace(place_id="x", place={"source_id": "src", "fit": {"pivot": [0, 0], "anchor": [0, 0]}},
                               files={"spaces": spaces}, src=types.SimpleNamespace(spaces={"cell": types.SimpleNamespace(refs=cell)}),
                               by_src={"e1": {}, "e2": {}}, ext=ext, S=None, G=None)
    assert sorted(wholesale.carry_rooms(st, 7.0)) == ["cell", "cell.2"]
    assert [r["src"] for r in spaces["cell"]["refs"]] == ["q1"] and [r["src"] for r in spaces["cell.2"]["refs"]] == ["q2"]
    assert ext[1]["door"]["to_space"] == "cell.2" and ext[1]["door"]["to_ref"] == spaces["cell.2"]["refs"][0]["id"]
    assert ext[0]["door"]["arrival"] == [0.0, 0.0, 7.0]
    assert spaces["cell.3"]["refs"] == [{"id": "own"}] and ext[0]["door"]["to_space"] == "cell"   # an added room is its own


def test_a_room_lands_before_its_door_as_the_door_now_stands():
    # the landing (pier, ship and its door) moved by hand: a later rooms carry lands the hold's way out before the
    # door where it stands, never where the source put it
    q = {"id": "q1", "base": "d", "kind": "door", "pos": [0.0, 0.0, 0.0],
         "door": {"to_ref": "e1", "to_pos": [100.0, 0.0, 10.0], "to_space": "x", "to_rot": [0, 0, 0]}}
    ext = [{"id": "x.e1", "src": "e1", "pos": [5000.0, 5000.0, 50.0], "rot": [0, 0, math.pi / 2],
            "door": {"to_space": "ship", "to_ref": "q1"}}]
    spaces = {"exterior": {"refs": ext}, "ship": {"space": {"copy_of": "src/ship"}, "refs": []}}
    st = types.SimpleNamespace(place_id="x", place={"source_id": "src", "fit": {"pivot": [0, 0], "anchor": [0, 0]}},
                               files={"spaces": spaces}, src=types.SimpleNamespace(spaces={"ship": types.SimpleNamespace(refs=[q])}),
                               by_src={"e1": {"pos": [0.0, 0.0, 0.0], "rot": [0, 0, 0]}}, ext=ext, S=None, G=None)
    wholesale.carry_rooms(st, 0.0)
    land = spaces["ship"]["refs"][0]["door"]["to_pos"]
    assert [round(v) for v in land] == [5000, 4900, 60] and ext[0]["door"]["arrival"] == land


def test_a_light_turns_with_the_place():
    # a wholesale baseline turns every piece by fit.rot_deg: a light's offset from its fixture turns with it, so the
    # lights stage and the draft check judge it in the place's frame (a fit's own cluster turn wins where it has one)
    from tools.places.draft import lights
    place = {"fit": {"rot_deg": 90.0}, "wholesale": {}}
    assert abs(lights.turn_of(place)("b01") - math.pi / 2) < 1e-9
    place["fit"]["clusters"] = {"b01": {"rot": 0.25}}
    assert lights.turn_of(place)("b01") == 0.25 and abs(lights.turn_of(place)("b02") - math.pi / 2) < 1e-9
    assert lights.turn_of({"fit": {"rot_deg": 90.0}})("b01") == 0.0     # the clustered method's own frame
    lt, fx = {"pos": [100.0, 0.0, 50.0]}, {"pos": [0.0, 0.0, 0.0]}
    assert [round(v) for v in lights.offset(lt, fx, math.pi / 2)] == [0, -100]


def test_the_carried_mesh_reads_the_districts():
    place = {"fit": {"pivot": [0.0, 0.0], "anchor": [0.0, 0.0], "rot_deg": 0.0},
             "wholesale": {"offset": 5.0, "districts": [{"name": "high", "offset": -900.0, "at": [[7000.0, 0.0]]}]}}
    ours, _ = srcnav._transform(place, lambda x, y: 1000.0 if x > 5000 else 0.0, lambda X, Y: 100.0)
    assert ours(7100.0, 0.0, 1100.0)[2] == 200.0          # within the district: its offset
    assert ours(1000.0, 0.0, 30.0)[2] == 130.0            # elsewhere: the carried ground followed
    ours, _ = srcnav._transform(place)
    assert ours(1000.0, 0.0, 30.0)[2] == 35.0             # no grounds given: the one offset
    H = heights.of_place(place)
    w, o = H.field([7000.0, 7000.0 + heights.R_OUT + 1], [0.0, 0.0])
    assert list(w) == [1.0, 0.0] and list(o) == [-900.0, -900.0]
