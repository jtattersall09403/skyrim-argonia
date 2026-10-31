"""L2: the quarantine is an allowlist (decision 0012; planner ruling, game-7, 2026-10-30). Every scanned
self-starting quest is shelled, whether the base game's, the Creation Club's or a mod's, except the dependency mods'
controllers the allowlist names by plugin and editor id. Shelling TK Dodge's controller took the roll's perk away
(game-6); King of the Murkmire's quests must not run (we borrow only its cells)."""
import json
from pathlib import Path

from tools.argonia_world.intermediate import quarantined

ALLOWED = json.loads((Path(__file__).resolve().parents[3] / "data/quarantine/allowed-quests.json").read_text())


def test_everything_but_the_allowlist_is_shelled():
    rows = [{"formKey": "03372B:Skyrim.esm", "edid": "MQ101", "plugin": "Skyrim.esm"},
            {"formKey": "000801:ccBGSSSE001-Fish.esm", "edid": "ccFish", "plugin": "ccBGSSSE001-Fish.esm"},
            {"formKey": "000D62:King of the Murkmire.esp", "edid": "KoTMQuest00", "plugin": "King of the Murkmire.esp"},
            {"formKey": "009802:TKDodgeAddon.esp", "edid": "StyyTKDodgeControllerQuest", "plugin": "TKDodgeAddon.esp"},
            {"formKey": "000802:SkyUI_SE.esp", "edid": "SKI_ConfigManagerInstance"},
            {"formKey": "000D63:Sailable Ship.esm", "edid": "aaaShipInputQuest", "plugin": "Sailable Ship.esm"}]
    got = [r["edid"] for r in quarantined(rows, ALLOWED["running"])]
    assert got == ["MQ101", "ccFish", "KoTMQuest00"]


def test_an_allowed_name_in_another_plugin_is_still_shelled():
    rows = [{"formKey": "000900:Other.esp", "edid": "StyyTKDodgeControllerQuest", "plugin": "Other.esp"}]
    assert [r["edid"] for r in quarantined(rows, ALLOWED["running"])] == ["StyyTKDodgeControllerQuest"]


def test_every_allowed_row_says_why():
    assert all(r.get("why") and r.get("plugin") and r.get("edid") for r in ALLOWED["running"])


def test_every_loaded_loading_screen_but_ours_is_disabled():
    from tools.argonia_world.intermediate import loading_screen_errors
    scan = {"loadScreens": [{"formKey": "0FF0A1:Skyrim.esm", "edid": "LoadScreenDragon", "plugin": "Skyrim.esm"},
                            {"formKey": "000D10:Black Marsh.esm", "edid": "", "plugin": "Black Marsh.esm"}]}
    never = [{"function": "GetGlobalValue", "global": "000800:Argonia.esm", "op": "EqualTo", "value": 1}]
    ours = [{"type": "LSCR", "formKey": f"00090{i}:Argonia.esm", "text": "t"} for i in range(3)]
    shells = [{"type": "LSCR", "override": True, "formKey": r["formKey"], "conditions": never} for r in scan["loadScreens"]]
    assert loading_screen_errors(scan, shells + ours) == []
    assert loading_screen_errors(scan, shells[:1] + ours) == ["Black Marsh.esm 000D10:Black Marsh.esm: not disabled"]
    assert loading_screen_errors(scan, shells) == ["our loading screens: 0, each needs text and no model"]


def test_our_loading_screens_have_text_and_no_nordic_word():
    from tools.argonia_world.intermediate import LOADING_SCREENS
    rows = json.loads(LOADING_SCREENS.read_text())["screens"]
    assert len(rows) >= 3 and all(r["fact"].startswith("fact.") and r["text"] for r in rows)
    assert not any(w in r["text"].lower() for r in rows for w in ("skyrim", "nord", "dragonborn"))
