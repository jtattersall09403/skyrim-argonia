"""The studio's walking mesh says it is from the last build when the place files are newer; it never blocks the place."""
import os

from tools.places import navexport


def test_a_walking_mesh_of_other_place_files_is_from_the_last_build(tmp_path):
    """By content, never by time: a newer file of the same bytes leaves the mesh current; a changed one does not."""
    import json
    from tools.places import build as B
    out, pdir = tmp_path / "out", tmp_path / "p"
    pdir.mkdir()
    (pdir / "place.json").write_text("{}")
    shard = out / "shards" / "p"
    shard.mkdir(parents=True)
    (shard / "plan.json").write_text("{}")
    (shard / "files.json").write_text(json.dumps(B.built_files(pdir)))
    exp = out / "nav" / "p.json"
    exp.parent.mkdir()
    exp.write_text("{}")
    os.utime(exp, (100, 100))
    os.utime(pdir / "place.json", (200, 200))
    assert not navexport.older_than_files(exp, pdir)
    (pdir / "place.json").write_text('{"x": 1}')
    assert navexport.older_than_files(exp, pdir)
