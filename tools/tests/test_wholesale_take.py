"""A place that takes one part of its source (`draft wholesale --take u`): only the source pieces within u of the pivot
are laid, the ground is carried round the anchor for that part, and the walking mesh is carried for that part alone
(srcnav.carried_disc), so the rest of the footprint is meshed as ours."""
import types

from tools.places.draft import ground, srcnav, wholesale


def _standing(refs):
    return types.SimpleNamespace(
        place_id="x", place={"fit": {"pivot": [0.0, 0.0], "anchor": [1000.0, 1000.0], "rot_deg": 0.0}, "radius_m": 50},
        src_ext=refs, bases={}, clusters=(None, {}, None), grd=types.SimpleNamespace(path="g"), S=None)


def test_take_lays_only_the_part(monkeypatch):
    import tools.places.extract as extract
    monkeypatch.setattr(extract, "load_place", lambda pid: {"world_x": 1000.0, "world_y": 1000.0})
    monkeypatch.setattr(wholesale.Ground, "load", staticmethod(lambda p: None))
    seen = {}

    def carry(G0, S, pv, an, rot, pieces, centre, radius, **kw):
        seen.update(centre=centre, radius=radius)
        return [], {}
    monkeypatch.setattr(ground, "carry", carry)
    refs = [{"id": "near", "base": "b", "kind": "static", "pos": [300.0, 0.0, 5.0]},
            {"id": "far", "base": "b", "kind": "static", "pos": [0.0, 900.0, 5.0]}]
    ext, ledger, _, _ = wholesale.lay(_standing(refs), 0.0, take=500.0)
    assert [r["src"] for r in ext] == ["near"]
    assert any(lr["src"] == "far" and "part of the source" in lr["why"] for lr in ledger)
    assert tuple(seen["centre"]) == (1000.0, 1000.0) and seen["radius"] == 500.0
    ext, _, _, _ = wholesale.lay(_standing(refs), 0.0)
    assert sorted(r["src"] for r in ext) == ["far", "near"]


def test_carried_disc():
    place = {"fit": {"anchor": [1.0, 2.0]}, "radius_m": 40, "wholesale": {}}
    assert srcnav.carried_disc(place) == ([1.0, 2.0], 2800, 512.0)
    place["wholesale"]["take"] = 600
    assert srcnav.carried_disc(place) == ([1.0, 2.0], 600.0, 0.0)
