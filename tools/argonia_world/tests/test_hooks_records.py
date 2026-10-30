"""L1: the dialogue-intercept hook records (native map P3) carry the perk's entry point, flags, condition and fragment."""
from __future__ import annotations

from tools.argonia_world import hooks_records as hr


class Stub:
    def form_key(self, edid, record_type=None, entity_key=None):
        return {"KYWD": "000801", "PERK": "000802"}[record_type] + ":Argonia.esm"


def recs():
    lay = hr.layer(Stub())
    assert lay.name == "base:hooks"
    return {r["type"]: r for r in lay.records}


def test_two_records():
    r = recs()
    assert set(r) == {"KYWD", "PERK"}
    assert r["KYWD"]["edid"] == "ARG_Speaker" and r["PERK"]["edid"] == "ARG_Perk_DialogueIntercept"


def test_perk_fields():
    p = recs()["PERK"]
    assert p["hidden"] and not p["playable"] and not p["trait"] and p["level"] == 0 and p["ranks"] == 1
    (e,) = p["effects"]
    assert (e["entryPoint"], e["function"], e["tabCount"], e["fragment"]) == ("Activate", "AddActivateChoice", 2, 0)
    assert e["flags"] == ["RunImmediately", "ReplaceDefault"] and e["buttonLabel"] == "Speak"
    assert p["fragments"] == {"script": "ARG_PRKF_DialogueIntercept", "entries": [{"index": 0, "name": "Fragment_0"}]}


def test_condition_is_on_tab_1_and_names_the_speaker_keyword():
    r = recs()
    (c,) = r["PERK"]["effects"][0]["conditions"]
    assert c["tab"] == 1 and c["function"] == "HasKeyword" and c["op"] == "EqualTo" and c["value"] == 1
    assert c["keyword"] == r["KYWD"]["formKey"]
