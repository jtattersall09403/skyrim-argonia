"""The adaptation checker's rules on small hand-built ledgers."""
from tools.argonia_world import adaptation_check as ac


def q(line="quest.line.a", code="A01", verdict="adapt", band=1, lore="story/lore/README.md", text="", merged=None):
    return dict(line=line, code=code, verdict=verdict, merged_into=merged, band=band, lore=lore, text=text)


def base():
    lg = ac.Ledger()
    lg.all_quests = {"a1", "a2"}
    lg.quests = {"a1": q(code="A01"), "a2": q(code="A02", band=2)}
    lg.hosts = [("a1", "s1", None, "main", None), ("a2", "s1", None, "main", None)]
    lg.capacity = {"s1": (3, 0)}
    return lg


def test_clean_ledger_passes():
    assert ac.run(base()) == []


def test_coverage_and_hosts():
    lg = base()
    lg.all_quests.add("a3")
    lg.quests["a2"]["verdict"] = "drop"
    lg.hosts.append(("a1", "s1", "c9", "stage", None))
    f = ac.run(lg)
    assert any("a3: no adaptation row" in x for x in f)
    assert any("a2: drop but still has hosts" in x for x in f)
    assert any("host cell c9" in x for x in f)
    lg.edits["we.a1.door"] = dict(kind="door_add", settlement="s1", cell="c9", target=None, race=None, band=None,
                                  lore="story/lore/README.md", text="a door")
    lg.quest_edits.append(("a1", "we.a1.door"))
    assert not any("host cell" in x for x in ac.run(lg))


def test_edit_undoes_another_quests_need():
    lg = base()
    lg.edits["we.a1.gone"] = dict(kind="npc_remove", settlement="s1", cell=None, target="X:P", race=None, band=None,
                                  lore="story/lore/README.md", text="remove")
    lg.quest_edits.append(("a1", "we.a1.gone"))
    lg.needs.append(("a2", "X:P"))
    assert any("which a2 needs" in x for x in ac.run(lg))


def test_cycle_danger_and_seats():
    lg = base()
    lg.prereqs.append(("a1", "a2"))                 # a2 follows a1 by code: a cycle
    lg.quests["a2"]["band"] = 4                     # 1 -> 4 jumps by 3
    lg.hubs = [("l1", "s1", None, "seat", None), ("l2", "s1", None, "seat", None)]
    f = ac.run(lg)
    assert any("cycle" in x for x in f)
    assert any("jumps" in x for x in f)
    assert any("shared by" in x for x in f)


def test_capacity_lore_nordic_levelled():
    lg = base()
    lg.capacity = {"s1": (0, 0)}
    lg.all_quests |= {"a3"}
    lg.quests["a3"] = q(code="A03", lore="nowhere", text="a draugr barrow")
    lg.hosts.append(("a3", "s1", None, "main", None))
    lg.levelled = {"L:P"}
    lg.needs.append(("a1", "L:P"))
    f = ac.run(lg)
    assert any("capacity 2" in x for x in f)
    assert any("a3: lore citation" in x for x in f)
    assert any("Nordic" in x for x in f)
    assert any("levelled" in x for x in f)


def test_a_place_an_edit_makes_hosts_a_quest():
    lg = base()
    lg.hosts.append(("a1", None, None, "stage", "we.a1.new-town"))
    assert any("not a ledgered place-making edit" in x for x in ac.run(lg))
    lg.edits["we.a1.new-town"] = dict(kind="place_new", settlement=None, cell=None, target=None, race=None, band=None,
                                      lore="story/lore/README.md", text="a new stilt village")
    assert any("does not list it" in x for x in ac.run(lg))
    lg.quest_edits.append(("a1", "we.a1.new-town"))
    assert ac.run(lg) == []


def test_empty_ledger_passes():
    lg = ac.Ledger()
    lg.all_quests = {"a1"}
    assert ac.run(lg) == []


def test_a_host_with_levelled_actors_needs_its_clean_up():
    lg = base()
    lg.levelled_at = {"s1": {"P1"}}
    assert any("no clean-up edit we.clean.s1" in x for x in ac.run(lg))
    lg.edits["we.clean.s1"] = dict(kind="creature_remove", settlement="s1", cell=None, target="P1", race=None,
                                   band=None, lore="story/lore/README.md", text="clean")
    lg.quest_edits += [("a1", "we.clean.s1"), ("a2", "we.clean.s1")]
    assert any("leaves 1 placement" in x for x in ac.run(lg))
    lg.edit_targets = {"we.clean.s1": {"P1"}}
    assert ac.run(lg) == []


def test_people_in_a_cell_without_navmesh_need_one():
    lg = base()
    lg.no_navmesh = {"c1"}
    lg.edits["we.a1.people"] = dict(kind="npc_add", settlement="s1", cell="c1", target=None, race="Argonian", band=0,
                                    lore="story/lore/README.md", text="two people")
    lg.quest_edits.append(("a1", "we.a1.people"))
    assert any("no navmesh" in x for x in ac.run(lg))
    lg.edits["we.a1.mesh"] = dict(kind="navmesh_add", settlement="s1", cell="c1", target=None, race=None, band=None,
                                  lore="story/lore/README.md", text="navmesh")
    lg.quest_edits.append(("a1", "we.a1.mesh"))
    assert ac.run(lg) == []
