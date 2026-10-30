"""L1 (1.4, lane fixes-2): LF83's three thing hooks. The well head and the mortar tub carry the hook keyword and
"Examine"; the hidden perk's Activate entry on that keyword runs ARG_PRKF_ThingHook (one native call); the ledger is
read through the Book Menu. Each resolves to the record's world id, which ArgoniaCore's thing table (things_table.h)
is keyed by, and sets a flag the quest writes."""
import pytest

from tools.argonia_world import db, thing_hooks
from tools.argonia_world.formids import Allocator


def test_lf83s_three_hooks_resolve():
    rows, bad = thing_hooks.hooks(db.open())
    assert not bad, bad
    assert {(r[0], r[2], r[3]) for r in rows} == {
        ("thing.lf83.well-head", "activate", "flag.lf83.crack-seen"),
        ("thing.lf83.mortar-tub", "activate", "flag.lf83.tub-seen"),
        ("document.station-water-ledger", "read", "flag.lf83.ledger-read")}


def test_the_perk_calls_the_fragment_on_the_keyword():
    w = db.open()
    kw, perk = thing_hooks.records(Allocator(w))
    (e,) = perk["effects"]
    assert e["entryPoint"] == "Activate" and e["conditions"][0]["keyword"] == kw["formKey"]
    assert "RunImmediately" in e["flags"] and perk["fragments"]["script"] == thing_hooks.FRAGMENT_SCRIPT


def test_the_activators_carry_the_keyword():
    from tools.argonia_world import place_build as pb
    w = db.open()
    ctx = pb._Ctx(Allocator(w), w, None, None)
    pb._items(ctx, w, [r for r in w.rows("build_ref") if r.thing_id])
    kw = ctx.alloc.form_key(thing_hooks.KEYWORD[0], "KYWD", thing_hooks.KEYWORD[1])
    for e in ("ARG_ACTI_LF83WellHead", "ARG_ACTI_LF83MortarTub"):
        assert ctx.records[e]["keywords"] == [kw] and ctx.records[e]["activateTextOverride"] == thing_hooks.VERB


def test_a_flag_the_quest_does_not_write_is_refused():  # proven on purpose
    w = db.open()

    class W:
        def __getattr__(self, k):
            return getattr(w, k)

        def rows(self, table, **kw):
            rows = w.rows(table, **kw)
            if table == "thing_hook":
                import dataclasses
                rows = [dataclasses.replace(rows[0], sets_flag="flag.lf83.never")] + rows[1:]
            return rows
    _, bad = thing_hooks.hooks(W())
    assert any("does not write flag.lf83.never" in b for b in bad)
    with pytest.raises(ValueError):
        thing_hooks.render(W())
