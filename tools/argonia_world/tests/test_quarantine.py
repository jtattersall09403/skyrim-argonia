"""L2: the quarantine shells the base game's and the Creation Club's self-starting quests only (decision 0012). A
dependency mod's start-game quest is its machinery: shelling TK Dodge's controller took the roll's perk away
(game-6, 2026-10-30)."""
from tools.argonia_world.intermediate import quarantined


def test_only_vanilla_and_creation_club_quests_are_shelled():
    rows = [{"formKey": "03372B:Skyrim.esm", "edid": "MQ101", "plugin": "Skyrim.esm"},
            {"formKey": "000801:ccBGSSSE001-Fish.esm", "edid": "ccFish", "plugin": "ccBGSSSE001-Fish.esm"},
            {"formKey": "009802:TKDodgeAddon.esp", "edid": "StyyTKDodgeControllerQuest", "plugin": "TKDodgeAddon.esp"},
            {"formKey": "000802:SkyUI_SE.esp", "edid": "SKI_ConfigManagerInstance"}]
    got = [r["edid"] for r in quarantined(rows, {"skyrim.esm", "ccbgssse001-fish.esm"})]
    assert got == ["MQ101", "ccFish"]
