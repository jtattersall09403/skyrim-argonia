"""The record is the brief: the source brings no trap, no treasure and no Nordic sign the record does not promise,
and a draft carries a plan judged against the record."""
from tools.places import check as C
from tools.places.draft import io, promised
from tools.places.draft.check import plan_checks

from tools.tests.test_places_check import ctx

BASES = {
    "a": {"edid": "ArgoniaVineTrap01", "type": "ACTI"},
    "b": {"edid": "TrapPoisonGas", "type": "ACTI"},
    "c": {"edid": "DLC1TrapPoisonBloom01", "type": "ACTI"},
    "d": {"edid": "ArgoniaGasFissure01MarshGrass", "type": "ACTI"},
    "box": {"edid": "TreasStrongBox", "type": "Container"},
    "chest": {"edid": "ALPARusticChest01Empty_NoRespawn", "type": "Container"},
    "doom": {"edid": "DoomstoneCircle03", "model": "clutter/powershrines/powshrinecircle03.nif", "type": "STAT"},
    "tent": {"edid": "ALPAScaleTent02", "type": "STAT"},
}


def ref(i, base, x=0.0):
    return {"id": i, "base": base, "pos": [x, 0.0, 0.0]}


EXT = [ref("1", "a"), ref("2", "b"), ref("3", "c"), ref("4", "d"), ref("5", "box", 10), ref("6", "box", 900),
       ref("7", "chest"), ref("8", "doom"), ref("9", "tent")]


def test_a_friendly_place_takes_no_trap_and_one_treasure_per_promise():
    rec = {"disposition": "friendly", "dangers": "Poison gas seeps from the vents.", "treasure": 1}
    out = promised.drops(EXT, BASES, rec)
    assert {"1", "2", "3", "4"} <= set(out)      # friendly: traps go whatever the dangers say
    assert "6" in out and "5" not in out         # the nearer strongbox keeps the one promise
    assert "7" not in out and "9" not in out     # a household chest and a tent are no treasure or trap
    assert "8" in out                            # a Doomstone is a Nordic sign


def test_a_hostile_place_keeps_the_traps_its_dangers_name():
    rec = {"disposition": "hostile", "dangers": "Gas vents and vine snares guard the ruin.", "treasure": 2}
    out = promised.drops(EXT, BASES, rec)
    assert not {"1", "2", "3", "4", "5", "6"} & set(out)
    rec = {"disposition": "wary", "dangers": "Crocodiles gather under the log boom.", "treasure": 1}
    assert {"1", "2", "3", "4"} <= set(promised.drops(EXT, BASES, rec))


def test_a_treasure_placed_by_hand_counts_first():
    rec = {"disposition": "friendly", "dangers": "", "treasure": 1}
    out = promised.drops(EXT, BASES, rec, [{"base": "x", "kind": "container", "name": "Thief's Sack"}])
    assert "5" in out and "6" in out


def test_a_doomstone_is_nordic_even_as_the_sources_own_piece():
    assert io.is_nordic_sign(BASES["doom"]) and not io.is_nordic_sign(BASES["tent"])
    c = ctx()
    d = c["dump"]["refs"][0]
    d.update(model="clutter/powershrines/powshrinecircle03.nif", base_type="STAT", base_edid="DoomstoneCircle03")
    c["plan"]["refs"][0]["base"] = "Skyrim.esm:0C1ADD"
    c["source_bases"] = {"Skyrim.esm:0C1ADD"}
    c["nordic_review"] = {}
    assert C.check_nordic(c)


def test_a_draft_needs_its_plan_and_judges_each_structure():
    refs = [{"id": "r1", "src": "s1", "kind": "building", "cluster": "c1"}]
    assert any("missing" in m for m in plan_checks({"draft": {}}, refs))
    plan = {"look": [{"line": "pale hide tents", "by": "ALPAScaleTent02 x3"}, {"line": "a weir", "by": ""}],
            "structures": []}
    got = plan_checks({"draft": {"plan": plan}}, refs)
    assert any("delivered by nothing" in m for m in got) and any("without a verdict" in m for m in got)
    plan["look"][1]["by"] = "woven fences"
    plan["structures"] = [{"cluster": "c1", "what": "Xanmeer ruin", "verdict": "dropped", "why": "no ruin"}]
    assert any("still stands" in m for m in plan_checks({"draft": {"plan": plan}}, refs))
    plan["structures"][0]["verdict"] = "kept"
    assert not plan_checks({"draft": {"plan": plan}}, refs)
