"""The sight sheet names a cage a cage, and a map marker carried from the source by the place's own name."""
from tools.argonia_world.surroundings import kind_of
from tools.places.sight import marker_name


def test_a_cage_reads_as_a_cage():
    assert kind_of("clutter/cage/metalcage01.nif MetalCage01") == ("cage", "cages")
    assert kind_of("dungeons/gibbetcage01.nif GibbetCage01") == ("torture pole", "torture poles")


def test_a_carried_source_marker_shows_the_place_name():
    carried = {"src": "King of the Murkmire.esp:85A226", "map_marker": {"Name": "Ree-An-Wo"}}
    added = {"map_marker": {"Name": "Old Landing"}}
    assert marker_name(carried, "Karsh-Naal Camp") == "Karsh-Naal Camp"
    assert marker_name(added, "Karsh-Naal Camp") == "Old Landing"
    assert marker_name(carried, None) == "Ree-An-Wo"
