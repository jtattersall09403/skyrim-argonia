"""A carried source ref never keeps the source's map marker: the place's marker on the world map is the world ESM's,
named from the place record (a source marker carried as Seekhat Yol told the sight test the town was Seekhat Yol)."""
from pathlib import Path

from tools.places.draft import io

DRAFT = Path(__file__).resolve().parents[1] / "places" / "draft"


def test_carried_keys_leave_out_the_map_marker():
    assert "map_marker" not in io.CARRIED_KEYS and "door" in io.CARRIED_KEYS


def test_every_carry_uses_the_one_list():
    for name in ("wholesale.py", "run.py", "stages.py"):
        src = (DRAFT / name).read_text()
        assert "io.CARRIED_KEYS" in src and '"primitive", "map_marker"' not in src, name
