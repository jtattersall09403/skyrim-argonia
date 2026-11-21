"""The studio's walking mesh says it is from the last build when the place files are newer; it never blocks the place."""
import os

from tools.places import navexport


def test_a_walking_mesh_older_than_the_place_files_is_from_the_last_build(tmp_path):
    exp, pdir = tmp_path / "nav.json", tmp_path / "p"
    pdir.mkdir()
    exp.write_text("{}")
    (pdir / "place.json").write_text("{}")
    os.utime(exp, (100, 100))
    os.utime(pdir / "place.json", (200, 200))
    assert navexport.older_than_files(exp, pdir)
    os.utime(exp, (300, 300))
    assert not navexport.older_than_files(exp, pdir)
