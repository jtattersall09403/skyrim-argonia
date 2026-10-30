"""The quest generator's first rung (1.4; 2.12 §a) on LF83.

L2: the generated stage graph (the data quests.h encodes) walks exactly as the record does, and the generated QUST
holds the record's stages, endings and objectives. L1: the records check (no objective target data, no map
marker shown before it is reached, no placeholder text, no protected alias), each rule made to fail once; tier
protection and the dead-NPC fail-forward (old 0030, 0138); the fragments evaluate nothing and name every native."""
import copy
import re

import pytest

from tools.argonia_world import db, quest_gen as G, stage_walk as S
from tools.argonia_world.formids import Allocator

LF83 = "quest.local.lf83"


@pytest.fixture(scope="module")
def w():
    world = db.open()
    yield world
    world.con.rollback()


@pytest.fixture(scope="module")
def plan(w):
    return G.plan(w, LF83)


@pytest.fixture(scope="module")
def qust(w, plan):
    return G.qust(Allocator(world=w), plan)


def test_l2_generated_graph_walks_as_the_record(w, plan):
    want, got = S.walk(w, LF83), G.walk_graph(G.graph(plan))
    assert got.errors == [] and want.errors == []
    assert sorted(got.edges) == sorted(want.edges) and got.reached == want.reached
    assert {(a, b) for a, b, k, _ in got.edges if k == "failForward"} >= {(s, t) for s in (10, 20, 30) for t in (90, 92, 93)}


def test_l2_qust_holds_the_record(plan, qust):
    rec = {s["id"]: s for s in plan.stages}
    assert [s["index"] for s in qust["stages"]] == [0, *rec]
    assert qust["stages"][0]["flags"] == ["StartUpStage"]
    for s in qust["stages"][1:]:
        flags = s["log"][0].get("flags", [])
        assert flags == {"complete": ["CompleteQuest"], "failed": ["FailQuest"], None: []}[rec[s["index"]].get("ending")]
    assert [o["index"] for o in qust["objectives"]] == [10, 11, 20, 21, 22, 30, 31]
    assert qust["fragments"]["stages"] == [s["index"] for s in qust["stages"]]
    assert {a["name"] for a in qust["aliases"]} >= {"WellKeeper", "LandingSPoler", "EcoCrocodile", "ClayBasket"}
    psc = G.papyrus(plan)
    assert re.findall(r"^Function Fragment_(\d+)\(\)", psc, re.M) == [str(s["index"]) for s in qust["stages"]]


def test_outputs_current_and_full_check_clean(w):
    assert G.full_check(w) == []


def test_l1_no_markers_fails_on_purpose(qust):
    assert G.check_records([qust]) == []
    bad = copy.deepcopy(qust)
    bad["objectives"][0]["targets"] = [{"alias": 0}]
    cell = {"type": "CELL", "edid": "ARG_X", "refs": [{"formKey": "000900:Argonia.esm", "base": "000010:Skyrim.esm",
                                                      "mapMarker": {"flags": ["Visible"]}}]}
    errs = G.check_records([bad, cell])
    assert len(errs) == 2 and "no target markers" in errs[0] and "map marker" in errs[1]


def test_l1_yaml_no_markers(tmp_path):
    assert G.check_yaml(G.REPO / "plugin" / "Argonia" / "Quests") == []
    q = tmp_path / "Quests"
    q.mkdir()
    (q / "x.yaml").write_text("Objectives:\n- Index: 10\n  Targets:\n  - AliasID: 0\n")
    (tmp_path / "m.yaml").write_text("MapMarker:\n  Flags:\n  - Visible\n")
    assert len(G.check_yaml(tmp_path)) == 2


def test_l1_placeholder_and_protected_alias_flagged(w):
    p = copy.deepcopy(G.plan(w, LF83))
    del p.stages[1]["journalText"]
    del p.stages[0]["objectives"][0]["objectiveText"]
    q = G.qust(Allocator(world=w), p)
    q["aliases"][0]["flags"].append("Essential")
    errs = G.check_records([q])
    assert len(errs) == 3 and any("stage 20: journal text not written" in e for e in errs)


def test_tier_protection(w):
    assert G.check_tiers(w, LF83) == []
    w.insert("quest_touch", quest_id="quest.mr.mr01", ord=999, id="place.imperial-fringe.claywater-station",
             access="read")
    try:
        errs = G.check_tiers(w, LF83)
    finally:
        w.con.execute("DELETE FROM quest_touch WHERE quest_id = 'quest.mr.mr01' AND ord = 999")
    assert errs == [f"{LF83}: writes place.imperial-fringe.claywater-station, which quest.mr.mr01 (a higher tier) owns"]


def test_dead_npc_fail_forward_required(plan):
    g = copy.deepcopy(G.graph(plan))
    g["stages"][0]["failForward"] = [e for e in g["stages"][0]["failForward"] if e["to"] != 93]
    errs = G.walk_graph(g).errors
    assert any("stage 10: names npc.imperial-fringe.claywater-station.landing-s-poler" in e and "0138" in e for e in errs)


def test_fragments_name_every_native_and_evaluate_nothing(w, plan):
    psc = G.papyrus(plan)
    assert G.check_fragments({"x": psc}) == []
    assert G.check_fragments({"x": psc + "\n  If ArgoniaCore.Flag(\"a\", True)\n"}) != []
    actions = {t[0].upper() + t[1:] for t in w.values("SELECT id FROM condition_term WHERE kind = 'action'")}
    used = G.natives([psc])
    assert set(used) - actions == {"WatchQuest", "UnwatchQuest"}
    assert used["AddJournalEntry"] == ["Quest", "Int", "Int"] and used["SetFlag"] == ["String", "Bool"]


def test_state_keys_hash_like_the_core():
    assert G.fnv1a32("") == 2166136261 and G.fnv1a32("a") == 0xE40C292C
