"""L2: refs are named by runtime id at the console; the game keeps no ref's editor id (game-7, 2026-10-30)."""
from tools import ref_ids


def test_a_ref_becomes_its_runtime_id_and_a_cell_keeps_its_name():
    fix = ref_ids.resolver({"Argonia.esm": "10", "ArgoniaWorld.esm": "11"}.__getitem__)
    assert fix("player.moveto ARG_Ref_ClaywaterStationRoadIn 0 -150 0") == "player.moveto 100008E9 0 -150 0"
    assert fix("coc ARG_HoldingCell") == "coc ARG_HoldingCell"
    assert fix("ARG_Ref_ClaywaterStationRoadIn.GetDisabled") == '"100008E9".GetDisabled'


def test_a_light_plugin_prefix():
    assert ref_ids.runtime_id("FE001", 0x8E9) == "FE0018E9"
    assert ref_ids.runtime_id("10", 0x8E9) == "100008E9"


def test_a_borrowed_cells_ref_is_named_like_ours():
    fix = ref_ids.resolver({"King of the Murkmire.esp": "08"}.__getitem__)
    assert fix("player.moveto ARG_Ref_ClaywaterStationStationHouseDoor") == "player.moveto 088933E1"
