"""L1 (lane npc-ai, w3-infra): a person's NPC_ carries packages, AI data, outfit, class, a faction and a crime faction; each PACK its template's input count
(place_build.check_people). game-7 saw Claywater's people stand without AI or clothes."""
import pytest

from tools.argonia_world.packages import SANDBOX_TEMPLATE, SLEEP_TEMPLATE, TEMPLATE_INPUTS
from tools.argonia_world.place_build import PEOPLE_AI, PEOPLE_TEMPLATE_FLAGS, check_people


def _recs(**npc):
    person = {"type": "NPC_", "edid": "ARG_Npc_T", "templateFlags": PEOPLE_TEMPLATE_FLAGS, "class": "000806:Argonia.esm",
              "packages": ["000900:Argonia.esm"], "outfit": "4C52C2:King of the Murkmire.esp", **PEOPLE_AI,
              "factions": [{"faction": "000990:Argonia.esm", "rank": 0}], "crimeFaction": "000990:Argonia.esm"}
    person.update(npc)
    return [person,
            {"type": "PACK", "edid": "ARG_Npc_T_Day0", "template": SANDBOX_TEMPLATE, "inputCount": 12},
            {"type": "PACK", "edid": "ARG_Npc_T_Sleep", "template": SLEEP_TEMPLATE, "inputCount": 17}]


def test_vanilla_counts():  # read from Skyrim.esm's templated packages with `ArgoniaGen npcai`
    assert TEMPLATE_INPUTS == {SANDBOX_TEMPLATE: 12, SLEEP_TEMPLATE: 17}


def test_complete_person_passes():
    check_people(_recs())


@pytest.mark.parametrize("field", ["packages", "outfit", "class", "energy", "factions", "crimeFaction"])
def test_missing_field_fails(field):  # proven on purpose: each missing field fails the build
    with pytest.raises(ValueError, match=f"no {field}"):
        check_people(_recs(**{field: None}))


def test_wrong_input_count_fails():
    recs = _recs()
    recs[2]["inputCount"] = 16
    with pytest.raises(ValueError, match="16 data inputs"):
        check_people(recs)
