"""L1 (1.10): the generated Argonia.esm overrides Skyrim.esm's Player (0x7) with ArgonianRace, an Argonian race
preset's head parts and natural scale tints, and nothing of the Nord default (owner play test 1, item 6)."""
import json
from pathlib import Path

import pytest
import yaml

from tools.argonia_world.intermediate import QUARANTINE, player_layer

REPO = Path(__file__).resolve().parents[3]
PLAYER = REPO / "plugin" / "Argonia" / "Npcs" / "Player - 000007_Skyrim.esm.yaml"
ARGONIAN_RACE = "013740:Skyrim.esm"
# Skyrim.esm's male Argonian head parts (ArgoniaGen read of ArgonianRace and its presets, lane-1.10)
ARGONIAN_PARTS = {"0B2FDC:Skyrim.esm": "MarksMaleArgonianScars03", "09D749:Skyrim.esm": "MaleEyesArgonianBlue",
                  "0B2FCB:Skyrim.esm": "BrowsMaleArgonian02", "0D334E:Skyrim.esm": "HairArgonianMale05 (frills)"}
NORD_HAIR = "051507:Skyrim.esm"  # HairMaleNord01, the default Player's
FEATHER_BLACK = "0829CF:Skyrim.esm"
SKIN_TONE = 38  # ArgonianRace's SkinTone tint mask index


def test_the_plugin_overrides_the_player_as_an_argonian():
    rec = yaml.safe_load(PLAYER.read_text(encoding="utf-8"))
    assert rec["FormKey"] == "000007:Skyrim.esm" and rec["EditorID"] == "Player"
    assert rec["Race"] == ARGONIAN_RACE
    assert set(rec["HeadParts"]) == set(ARGONIAN_PARTS) and NORD_HAIR not in rec["HeadParts"]
    assert rec["HairColor"] == FEATHER_BLACK
    assert "HeadTexture" not in rec  # the race's own face texture: the head's scales match the body's
    tints = {t["Index"]: t for t in rec["TintLayers"]}
    skin = tints[SKIN_TONE]["Color"]  # '#AARRGGBB'
    r, g, b = (int(skin[i:i + 2], 16) for i in (3, 5, 7))
    assert g > r and g > b and max(r, g, b) < 128, f"skin tone {skin} is not a dark natural green"
    assert not {t["Preset"] for t in rec["TintLayers"]} & {98, 103, 135, 138, 143}  # the Nord default's tint presets


def test_the_player_layer_comes_from_start_json():
    player = json.loads((QUARANTINE / "start.json").read_text(encoding="utf-8"))["player"]
    (rec,) = player_layer(player).records
    assert rec == {"type": "NPC_", "override": True, "edid": "Player", "formKey": "000007:Skyrim.esm",
                   "race": ARGONIAN_RACE, "preset": "0B2E10:Skyrim.esm", "presetEdid": "ArgonianMalePreset06",
                   "items": []}
    with pytest.raises(ValueError):
        player_layer(dict(player, formKey="000014:Skyrim.esm"))
