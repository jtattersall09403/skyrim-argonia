"""The read-back rows for music (a cell's music plays; combat plays our pieces in the world) and for the location
that names the region to the player (walk 2 L9, L14, L29)."""
from tools.newworld.music import readback as M

W = "000800:ArgoniaNewWorld.esm"
ON_PLAYER = {"runon": "Reference", "reference": M.PLAYER}


def cond(value, world=W, **on):
    return {"fn": "GetInWorldspace", "runon": "Subject", "reference": None, "world": world, "op": "EqualTo", "or": False,
            "value": value, **on}


def track(edid, file, *conds):
    return {"edid": edid, "type": "SingleTrack", "file": file, "conds": list(conds)}


def header(combat):
    return {"world": {"form_key": W, "music": "ANW_MUSExplore_a"},
            "regions": [{"edid": "ANW_Region_a", "music": "ANW_MUSExplore_a", "map_name": "Aa"},
                        {"edid": "ANW_Region_b", "music": "ANW_MUSExplore_b", "map_name": "Bb"}],
            "music_types": {"ANW_MUSExplore_a": {"tracks": [track("ANW_MUS_x", "Data\\Music\\argonia\\x.wav")]},
                            "ANW_MUSExplore_b": {"tracks": [{"edid": "_Spacer", "type": "SilentTrack", "file": None, "conds": []}]},
                            "MUSCombat": {"tracks": combat}},
            "locations": [{"edid": "ANW_Loc_World", "name": "Black Marsh", "parent": None},
                          {"edid": "ANW_Loc_a", "name": "Aa", "parent": "ANW_Loc_World"}]}


def has(p):
    return p.startswith("music\\argonia\\")


def combat_row(H, cells, has_):
    return next(r for r in M.music_rows(H, cells, has_) if r[0].startswith("MUSCombat "))


def test_a_cell_whose_type_has_no_track_that_plays_is_silent():
    cells = {(0, 0): {"region": "ANW_Region_a"}, (1, 0): {"region": "ANW_Region_b"}}
    row = M.music_rows(header([]), cells, has)[0]
    assert row[1] == "1/2" and not row[2]


def test_combat_tracks_conditioned_on_the_subject_never_play():
    """The first build's GetInWorldspace ran on the subject; Skyrim's tracks run actor conditions on PlayerRef."""
    cells = {(0, 0): {"region": "ANW_Region_a"}}
    ours = track("ANW_MUS_battle", "Data\\Music\\argonia\\b.wav", cond(1))
    sky = track("MUSCombat01", "\\Data\\Music\\Combat\\MUS_Combat_01.wav", cond(0))
    assert not combat_row(header([ours, sky]), cells, has)[2]
    ours = track("ANW_MUS_battle", "Data\\Music\\argonia\\b.wav", cond(1, **ON_PLAYER))
    sky = track("MUSCombat01", "\\Data\\Music\\Combat\\MUS_Combat_01.wav", cond(0, **ON_PLAYER))
    row = combat_row(header([ours, sky]), cells, lambda p: True)
    assert row[2] and row[1] == "1 ours, 0 Skyrim's"


def test_every_cell_names_its_region_by_location():
    cells = {(0, 0): {"region": "ANW_Region_a", "location": "ANW_Loc_a"}, (1, 0): {"region": "ANW_Region_b", "location": ""}}
    rows = M.location_rows(header([]), cells)
    assert rows[0][1] == "1/2" and not rows[0][2]
    assert rows[1][2]
