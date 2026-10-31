"""L1/L2: the Custom Skills Framework set (1.12 §4): 13 CSF skills + 14 vanilla-AV mirrors = the DB's 27 skills."""
from __future__ import annotations

import json

from tools.argonia_world import core_tables, csf_records as csf, db
from tools.argonia_world import skyrim_units as su


class Stub:
    """An allocator that numbers each EditorID once."""

    def __init__(self):
        self.ids = {}

    def get(self, edid, record_type=None, entity_key=None):
        return self.ids.setdefault(edid, 0x800 + len(self.ids))

    def form_key(self, edid, record_type=None, entity_key=None):
        return f"{self.get(edid):06X}:Argonia.esm"


W = db.open()


def test_thirteen_csf_fourteen_mirrored_twentyseven_total():
    csf_set, mirrored = csf.csf_ids(W), csf.vanilla_ids(W)
    assert len(csf_set) == 13 and len(mirrored) == 14
    assert sorted(csf_set + mirrored) == sorted(W.values("SELECT id FROM skill")) and len(csf_set + mirrored) == 27
    assert not set(csf_set) & set(mirrored)


def test_mirror_table_is_the_units_map_in_skill_order():
    ids = W.values("SELECT id FROM skill ORDER BY id")
    text = core_tables.mirrors(W)
    for i in ids:
        assert f'"{su.PLAYER_SKILL_AV[i] or ""}",  // {i}\n' in text + "\n"
    assert text.count('"",  //') == 13 and len(ids) == 27


def test_layer_has_five_globals_and_one_placeholder_perk_per_csf_skill():
    lay = csf.layer(Stub(), W)
    kinds = [r["type"] for r in lay.records]
    assert kinds.count("GLOB") == 65 and kinds.count("PERK") == 13
    assert all(r["valueType"] == "float" for r in lay.records if r["type"] == "GLOB")
    for r in lay.records:
        if r["type"] == "PERK":
            assert r["name"] == "No perks yet" and r["effects"] == [] and len(r["edid"]) <= su.EDITOR_ID_MAX
    colour = [r for r in lay.records if r["edid"].endswith("_Color")]
    assert len(colour) == 13 and {r["value"] for r in colour} == {0xFFFFFF}


def test_config_lists_27_skills_with_13_objects_naming_real_records():
    st = Stub()
    lay = csf.layer(st, W)
    cfg = json.loads(csf.render(st, W))
    assert cfg["version"] == 1 and len(cfg["skills"]) == 27
    objs = [s for s in cfg["skills"] if isinstance(s, dict)]
    names = [s for s in cfg["skills"] if isinstance(s, str)]
    assert len(objs) == 13 and len(names) == 14 and sorted(names) == sorted(v for v in su.PLAYER_SKILL_AV.values() if v)
    made = {int(r["formKey"].split(":")[0], 16) for r in lay.records}
    for o in objs:
        assert len(o["nodes"]) == 1 and len({o[g] for g in csf.GLOBALS}) == 5
        refs = [o[g] for g in csf.GLOBALS] + [o["nodes"][0]["perk"]]
        assert all(int(x.split("|")[1], 16) in made and x.startswith("Argonia.esm|") for x in refs)


def test_committed_json_is_current():
    from tools.argonia_world.formids import Allocator
    assert csf.CONFIG.read_text(encoding="utf-8") == csf.render(Allocator(W, frozen=True), W)
