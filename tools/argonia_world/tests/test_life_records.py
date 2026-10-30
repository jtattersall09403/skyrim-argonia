"""L1: the life-hook records (native map P3, P4): keywords, the two activators, the rest-intercept perk, the GMST overrides."""
from __future__ import annotations

from types import SimpleNamespace as NS

import pytest

from tools.argonia_world import life_records as lr


class Alloc:
    def __init__(self):
        self.n = 0x900
        self.keys = {}

    def form_key(self, edid, record_type=None, entity_key=None):
        self.n += 1
        self.keys[entity_key] = self.n
        return f"{self.n:06X}:Argonia.esm"


class World:
    def __init__(self, settings):
        self.t = {"core_respawn_class": [NS(id="never", on_rest=False), NS(id="onRest", on_rest=True)],
                  "place_build_hostility": [NS(place_id="place.r.the-broke-column", clearable=True),
                                            NS(place_id="place.r.claywater-station", clearable=False)],
                  "game_setting": settings}

    def get(self, table, key):
        assert table == "place" and key == "place.r.the-broke-column"
        return NS(id=key, name="The Broke Column")

    def rows(self, table, order=None, **where):
        return self.t[table]


SCAN = {"gameSettings": {"fBlah": {"formKey": "1A0001:Skyrim.esm", "kind": "float"},
                         "iHoursToRespawnCell": {"formKey": "1A0002:Skyrim.esm", "kind": "int"}}}
ROWS = [NS(edid="fBlah", kind="float", value=0.0), NS(edid="iHoursToRespawnCell", kind="int", value=1000000.0)]


def recs():
    a = Alloc()
    lay = lr.layer(a, World(ROWS), SCAN)
    assert lay.name == "base:life"
    return a, {r["edid"]: r for r in lay.records}


def test_keywords_and_no_respawn_keyword():
    a, r = recs()
    assert {"ARG_RestSpot", "ARG_VasteiPile", "ARG_LocType_Settlement", "ARG_LocType_Dungeon"} <= set(r)
    assert not [e for e in r if e.startswith("ARG_Respawn_")]  # the runtime reads the NPC_ Respawn flag instead
    assert {"hook.rest-spot", "hook.vastei-pile", "hook.loc-settlement", "hook.loc-dungeon",
            "rest.camp-spot", "death.vastei-pile",
            "hook.rest-intercept"} <= set(a.keys)


def test_clearable_place_has_a_location_keyworded_clearable():
    a, r = recs()
    loc = r["ARG_Loc_TheBrokeColumn"]
    assert (loc["type"], loc["name"], loc["keywords"]) == ("LCTN", "The Broke Column", [r["ARG_LocType_Clearable"]["formKey"]])
    assert "loc.place.r.the-broke-column" in a.keys and "loc.place.r.claywater-station" not in a.keys
    assert "hook.loc-clearable" in a.keys


def test_activators():
    _, r = recs()
    camp, pile = r["ARG_CampSpot"], r["ARG_VasteiPileActivator"]
    assert (camp["name"], camp["activateTextOverride"], camp["keywords"]) == ("Camp", "Rest", [r["ARG_RestSpot"]["formKey"]])
    assert (pile["name"], pile["activateTextOverride"], pile["keywords"]) == ("Vastei", "Take", [r["ARG_VasteiPile"]["formKey"]])
    assert camp["model"].lower().endswith(".nif") and pile["model"].lower().endswith(".nif")
    # The camp spot must be seen and picked: bedrollground.nif is a furniture marker with no geometry or collision
    # (quarantine verdict 00085F); the borrowed model is the one the verdict names.
    assert camp["model"].lower() != "furniture\\bedroll\\bedrollground.nif"
    assert camp["model"].lower() == "furniture\\bedroll\\bedroll01.nif"


def test_perk_two_choices():
    _, r = recs()
    p = r["ARG_Perk_RestIntercept"]
    e0, e1 = p["effects"]
    assert (e0["buttonLabel"], e0["fragment"], e1["buttonLabel"], e1["fragment"]) == ("Rest", 0, "Take Vastei", 1)
    assert e0["conditions"][0]["keyword"] == r["ARG_RestSpot"]["formKey"] and e0["conditions"][0]["tab"] == 1
    assert e1["conditions"][0]["keyword"] == r["ARG_VasteiPile"]["formKey"]
    assert e0["flags"] == e1["flags"] == ["RunImmediately", "ReplaceDefault"]
    assert p["fragments"]["script"] == "ARG_PRKF_RestIntercept"
    assert [f["name"] for f in p["fragments"]["entries"]] == ["Fragment_0", "Fragment_1"]


def test_game_settings_are_master_overrides():
    _, r = recs()
    g = r["fBlah"]
    assert (g["type"], g["override"], g["formKey"], g["kind"], g["value"]) == ("GMST", True, "1A0001:Skyrim.esm", "float", 0.0)
    assert r["iHoursToRespawnCell"]["value"] == 1000000 and isinstance(r["iHoursToRespawnCell"]["value"], int)


def test_mistyped_setting_is_an_error():
    with pytest.raises(ValueError):
        lr.game_settings(Alloc(), World([NS(edid="fBlah", kind="int", value=1.0)]), SCAN)


def test_setting_without_a_master_record_is_a_new_record():
    (g,) = lr.game_settings(Alloc(), World([NS(edid="fNope", kind="float", value=0.0)]), SCAN)
    assert "override" not in g and g["formKey"].endswith(":Argonia.esm") and g["value"] == 0.0
