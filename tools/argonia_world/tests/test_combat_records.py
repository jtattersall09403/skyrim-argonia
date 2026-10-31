"""L1/L2: the combat wiring's tables and records (lane 1.6-wiring; docs/research/2026-10-30/combat-wiring.md)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.argonia_world import combat_records as cr
from tools.argonia_world import db
from tools.argonia_world import skyrim_units as su

ROOT = Path(__file__).resolve().parents[3]
ARCH = "npc.imperial-fringe.claywater-station.ambush-deserter"


@pytest.fixture(scope="module")
def w():
    return db.open()


class FakeAlloc:
    """FormKeys without touching the formid table: a stable key per EditorID."""
    def __init__(self):
        self.ids: dict[str, int] = {}

    def form_key(self, edid, record_type=None, entity_key=None):
        return f"{self.ids.setdefault(edid, 0x800 + len(self.ids)):06X}:Argonia.esm"


def test_settings_name_combat_rows_of_the_manifest(w):
    mods = {m["id"]: m for m in json.loads((ROOT / "data/dependencies.json").read_text())["mods"]}
    for s in w.rows("combat_mod_setting"):
        assert s.mod in mods, s.mod
        assert mods[s.mod].get("group") == "combat", s.mod
        manifest_keys = {k for e in mods[s.mod].get("ini", []) if e["file"].lower() == s.file.lower() for k in e["set"]}
        assert s.key not in manifest_keys, f"{s.mod} {s.key}: one home (the db), not the manifest too"


def test_every_routed_row_has_its_carrier(w):
    settings = {s.wiring for s in w.rows("combat_mod_setting")}
    gmsts = {g.wiring for g in w.rows("game_setting_combat")}
    carriers = {c.wiring for c in w.rows("combat_carrier")}
    for r in w.rows("combat_wiring"):
        if r.route == "mod_setting" and r.writer == "data":
            assert r.id in settings, r.id
        if r.route == "gmst":
            assert r.id in gmsts, r.id
        if r.route == "perk_entry" and r.writer == "runtime":
            # a bow is a right-hand weapon: ArgoniaCore writes the right-hand carrier without the Strength term
            shared = {"w.archery.damage": "right.attack-damage"}
            assert r.id in carriers or w.get("combat_carrier", shared.get(r.id, "")) is not None, r.id
        if r.journey:
            assert (ROOT / "tests/journeys" / f"{r.journey}.yaml").exists(), r.journey


def test_carriers_are_neutral_when_unwritten_and_known_entry_points(w):
    perk = cr.carrier_perk(FakeAlloc(), w)
    wired = [c for c in w.rows("combat_carrier") if c.wired]
    assert len(perk["effects"]) == len(wired) >= 4
    for e in perk["effects"]:
        assert e["function"] == "MultiplyOnePlusAVMult"  # AV 0 -> x1
        assert e["tabCount"] == su.PERK_ENTRY_TABS[e["entryPoint"]]


def test_listed_damage_steel_sword(w):
    assert cr.listed_damage(w, "item.steel-sword") == pytest.approx(24.0)  # 1.0 x steel 1.0 x 24 (76 §121.1)


def test_archetype_compiles_to_its_band(w):
    c = cr.compiled(w, ARCH)
    band = w.get("danger_band_combat", c["band"])
    assert c["band"] == "D2" and c["level"] == 10
    assert band.health_lo <= c["health"] <= band.health_hi
    assert band.light_hit_lo <= c["damage_mult"] * 24 <= band.light_hit_hi
    assert c["health"] == pytest.approx(44.5) and c["light_hit"] == pytest.approx(32.0)
    # 76 §121.4 at the reference blow: AR 31.5 / (31.5 + 135.6 + 0.6 x 24)
    assert c["incoming_mult"] == pytest.approx(1 - 31.5 / (31.5 + 135.6 + 14.4))


def test_archetype_records(w):
    recs = cr.archetype_records(FakeAlloc(), w, ARCH)
    by = {r["type"]: r for r in recs}
    assert by["ECZN"]["minLevel"] == by["ECZN"]["maxLevel"] == 10  # soul contract C14
    npc = by["NPC_"]
    assert npc["level"] == 10 and npc["healthOffset"] == round(44.5 - 50)
    assert npc["templateFlags"] == ["Traits"] and npc["items"] == []
    # armed at spawn: the kit is the default outfit, equipped by the engine (diag6 6), and a humanoid combat style
    assert npc["outfit"] == by["OTFT"]["formKey"] and len(by["OTFT"]["items"]) == 2
    assert npc["combatStyle"] == by["CSTY"]["formKey"] and by["CSTY"]["edid"] == "ARG_CSTY_SwordAndShield"
    assert npc["perks"] == [by["PERK"]["formKey"]]
