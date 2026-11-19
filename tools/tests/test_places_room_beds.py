"""A bed is a bed of its room only on that room's walkable mesh (interiors.beds_in)."""
from tools.places.draft import interiors


def test_a_bed_off_its_rooms_mesh_is_no_bed(monkeypatch):
    mesh = {"verts": [[0, 0, 0], [200, 0, 0], [0, 200, 0]], "tris": [[0, 1, 2]]}
    monkeypatch.setattr(interiors, "_partition",
                        lambda copy_of: {"door": {"refs": ["in", "void"], "mesh": mesh}})
    bases = {"bed": {"edid": "DarkElfBed01L", "model": "furniture/bed01.nif"}}
    refs = [{"id": "in", "kind": "furniture", "base": "bed", "pos": [60, 60, 0]},
            {"id": "void", "kind": "furniture", "base": "bed", "pos": [900, 60, 0]}]
    assert [b["ref"] for b in interiors.beds_in(refs, bases, "door", "src/cell")] == ["in"]
