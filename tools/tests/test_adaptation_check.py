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


def test_motif_warnings_flag_procedure_words():
    from tools.argonia_world import adaptation_check as ac
    lg = ac.Ledger()
    lg.quests = {"q.a": dict(verdict="adapt", premise="It ends in an arbitration before witnesses."),
                 "q.b": dict(verdict="adapt", premise="A beast takes rafts at the landing."),
                 "q.c": dict(verdict="wait", premise="A hearing.")}
    w = ac.motif_warnings(lg, {"q.b": [("s10", "You find the clerk's ledger.")]})
    assert any(x.startswith("q.a premise:") and "arbitration" in x for x in w)
    assert any(x.startswith("q.b s10:") and "ledger" in x for x in w)
    assert not any(x.startswith("q.c") for x in w)


def recs():
    rc = ac.Records()
    rc.census = {"000001:Black Marsh.esm", "000002:Black Marsh.esm", "000003:Black Marsh.esm"}
    rc.names = {"npc.a": "Ana-Tei", "npc.b": "Bo-Sei"}
    rc.placing = "we.q.people: Ana-Tei at the hut"
    rc.people = [("q", "npc.a")]
    rc.stages = {"q": {10: {"succ": [(20, {"inZone"}, set())], "ff": set()}}}
    return rc


def test_clean_records_pass():
    assert ac.record_warnings(recs()) == []


def test_census_and_placement():
    rc = recs()
    rc.needs.append(("we.q.x", "00FFFF:Black Marsh.esm"))
    rc.texts.append(("q", "the door 00EEEE:Black Marsh.esm and 07B91A:Skyrim.esm"))
    rc.people.append(("q", "npc.b"))
    w = ac.record_warnings(rc)
    assert any("00FFFF" in x for x in w) and any("00EEEE" in x for x in w)
    assert not any("07B91A" in x for x in w)
    assert any("npc.b" in x and x.startswith("placed") for x in w)


def test_helgen_rule():
    rc = recs()
    rc.topics = [("q", "npc.a", True, {10})]
    assert any(x.startswith("helgen") for x in ac.record_warnings(rc))
    rc.quest_text = {"q": "Build notes: Ana-Tei is essential until stage 40."}
    assert ac.record_warnings(rc) == []
    rc.quest_text = {}
    rc.stages["q"][10]["ff"] = {"npc.a"}
    assert ac.record_warnings(rc) == []


def test_helgen_rule_across_quests():
    rc = recs()
    rc.people = [("quest.l.a", "npc.a"), ("quest.l.b", "npc.a")]
    rc.stages = {"quest.l.a": {10: {"succ": [], "ff": set()}}, "quest.l.b": {10: {"succ": [(20, {"inZone"}, set())], "ff": set()}}}
    rc.topics = [("quest.l.b", "npc.a", True, {10})]
    rc.quest_text = {"quest.l.a": "Ana-Tei is in the camp.", "quest.l.b": "Ana-Tei is essential to stage 10."}
    w = ac.record_warnings(rc)
    assert any("quest.l.b: stage 10" in x and "quest.l.a first" in x for x in w)
    rc.quest_text["quest.l.a"] = "Ana-Tei is essential from the start."
    assert ac.record_warnings(rc) == []
    rc.quest_text["quest.l.a"] = ""
    rc.stages["quest.l.b"][10]["ff"] = {"npc.a"}
    assert ac.record_warnings(rc) == []


def test_bare_form_id_is_normalised():
    census = {"0F9399:Black Marsh.esm", "000001:Black Marsh.esm", "000001:Other.esm"}
    assert ac.form_keys("the door 0F9399 and 000001 and 0F9399:Black Marsh.esm", census) == ["0F9399:Black Marsh.esm"]
    rc = recs()
    rc.census |= {"0F9399:Black Marsh.esm"}
    rc.texts.append(("q", "locks 0F9399"))
    assert ac.record_warnings(rc) == []


def test_shared_base_vanilla_door_skill_gate():
    rc = recs()
    rc.base_placements = {"000001:Black Marsh.esm": 10}
    rc.edits = {"we.q.sweep": ("npc_change", "000001:Black Marsh.esm")}
    rc.edits["we.q.door"] = ("door_add", None)
    rc.edit_text = {"we.q.door": "a door pair inside the ship"}
    rc.stages["q"][10]["succ"].append((20, {"all", "skillAtLeast"}, set()))
    w = ac.record_warnings(rc)
    assert any(x.startswith("shared_base") for x in w)
    assert any(x.startswith("vanilla_door") for x in w)
    assert any(x.startswith("skill_gate") for x in w)
    rc.edit_text["we.q.door"] = "both doors take BM&V's Argonian door base (1DE5DF)"
    assert not any(x.startswith("vanilla_door") for x in ac.record_warnings(rc))
    rc.edits = {"we.q.sweep": ("record_change", "000002:Black Marsh.esm")}     # BM&V's own door: not checked
    rc.door_base = {"000002:Black Marsh.esm": "0C227B:Skyrim.esm"}
    rc.quest_forms = {"q": {"000002:Black Marsh.esm"}}
    assert not any(x.startswith("vanilla_door") for x in ac.record_warnings(rc))


def test_record_rules_bind_kept_quests_only():
    rc = recs()
    rc.people.append(("quest.x", "npc.b"))
    rc.live = {"quest.x"}
    assert any(x.startswith("placed") for x in ac.record_warnings(rc))
    rc.live = set()
    assert ac.record_warnings(rc) == []


def test_speaker_knows_and_learnable():
    rc = recs()
    rc.uses = [("q", "topic.t", "npc.a", "fact.f")]
    rc.topic_from = {("q", "topic.t"): 30}
    rc.learnable = {"q": {"fact.f"}}
    w = ac.record_warnings(rc)
    assert any(x.startswith("speaker_knows") and "fact.f" in x for x in w)
    assert not any(x.startswith("learnable") for x in w)
    rc.knowers = {("q", "npc.a"): {"fact.f": 50}}          # known only from stage 50: too late for stage 30
    assert any(x.startswith("speaker_knows") for x in ac.record_warnings(rc))
    rc.knowers = {("q", "npc.a"): {"fact.f": 0}}
    assert ac.record_warnings(rc) == []
    rc.learnable = {}
    rc.gives = [("q", "k1", "fact.g")]
    w = ac.record_warnings(rc)
    assert any(x.startswith("learnable") and "topic.t" in x for x in w)
    assert any(x.startswith("learnable") and "clue k1" in x for x in w)


def test_skill_routes():
    rc = recs()
    rc.stages = {"q": {10: {"succ": [(20, set(), set())], "ff": set()}, 20: {"succ": [(30, set(), set())], "ff": set()},
                       30: {"succ": [], "ff": set()}}}
    rc.stage_end = {"q": {30}}
    rc.quest_kind = {"q": ("main", None)}
    assert any("stage 20 names no skill" in x for x in ac.skill_routes(rc))
    assert any("stage 10 names no skill" in x for x in ac.skill_routes(rc))     # the first stage counts
    rc.skill_stages = {"q": {10: {"sneak"}, 20: {"sneak"}}}
    assert any("needs two ways" in x for x in ac.skill_routes(rc))          # one skill is one way through
    rc.stages["q"][25] = {"succ": [(30, set(), set())], "ff": set()}
    rc.skill_stages["q"][25] = {"onehanded"}
    assert ac.skill_routes(rc) == []
    rc.quest_kind = {"q": ("faction", "faction.f")}
    rc.faction_skills = {"faction.f": {"security"}}
    assert any("faction.f" in x for x in ac.skill_routes(rc))
    rc.faction_skills = {"faction.f": {"sneak"}}
    assert ac.skill_routes(rc) == []
    rc.live = set()
    rc.faction_skills = {"faction.f": {"security"}}
    assert ac.skill_routes(rc) == []                                       # only kept or adapted quests


def test_skill_route_can_fail():
    assert ac._can_fail_action("OneHanded", "fight") and ac._can_fail_action("Athletics", "dive")
    assert ac._can_fail_action("Lockpicking", "pick-a-lock") and ac._can_fail_action("Destruction", "burn-a-nest")
    assert not ac._can_fail_action("Sneak", "sneak-past") and not ac._can_fail_action("Speechcraft", "persuade")
    assert ac._hard_check({"speechcraft", "25"}) and not ac._hard_check({"speechcraft", "15"})


def test_skill_routes_choice_stage_exempt():
    rc = recs()
    ch = lambda to, t: (to, {"topicHeardFrom"}, {t})
    rc.stages = {"q": {10: {"succ": [(20, set(), set())], "ff": set()},
                       20: {"succ": [ch(90, "a"), ch(91, "b")], "ff": set()},
                       90: {"succ": [], "ff": set()}, 91: {"succ": [], "ff": set()}}}
    rc.stage_end = {"q": {90, 91}}
    rc.skill_stages = {"q": {10: {"sneak"}}}
    rc.quest_kind = {"q": ("local", None)}
    assert ac.skill_routes(rc) == []                                       # whom to tell: a choice, not a skill
    rc.stages["q"][20]["succ"][1] = ch(91, "a")                            # not distinct topics
    assert any("stage 20 names no skill" in x for x in ac.skill_routes(rc))
    rc.stages["q"][20]["succ"][1] = (91, {"all", "topicHeardFrom", "hasItem"}, {"b", "item.x"})
    assert ac.skill_routes(rc) == []                                       # tell with the evidence in hand
    rc.stages["q"][20]["succ"][1] = (91, {"all", "topicHeardFrom", "inZone"}, {"b", "zone.z"})
    assert any("stage 20 names no skill" in x for x in ac.skill_routes(rc))


def wires(rc):
    return [x for x in ac.wiring(rc)]


def test_reachable():
    rc = recs()
    rc.stages = {"q": {10: {"succ": [(20, set(), set())], "ff": set()}, 20: {"succ": [], "ff": set(), "ff_to": []},
                       30: {"succ": [(20, set(), set())], "ff": set()}, 40: {"succ": [], "ff": set()}}}
    rc.stage_end = {"q": {20, 40}}
    rc.start = {"q": 10}
    w = wires(rc)
    assert any("nothing starts it" in x for x in w)
    assert any("stage 30 cannot be reached" in x for x in w)
    assert not any("stage 40" in x for x in w)                       # an ending is not asked
    rc.start_when = {"q"}
    rc.stages["q"][20]["ff_to"] = [30]                                # a fail-forward is a way in
    assert wires(rc) == []
    rc.start_when = set()
    rc.topics = [("q", "npc.a", False, {10})]
    assert wires(rc) == []                                            # a topic said at the start stage starts it


def test_acquire_prereq():
    rc = recs()
    rc.stages = {"q": {10: {"succ": [(20, {"hasItem"}, {"item.x", "1"})], "ff": set()}}}
    rc.start_when = {"q"}
    assert wires(rc) == []
    rc.given = {"item.x": [("q", 5)]}
    assert any(x.startswith("acquire_prereq") and "item.x" in x for x in wires(rc))
    rc.given = {"item.x": [("q", 15)]}                                 # given only after the stage: fine
    assert wires(rc) == []
    rc.item_states = {"item.x": {"q": {"before-20": "in the box"}}}
    assert any(x.startswith("acquire_prereq") for x in wires(rc))
    rc.item_states = {"item.x": {"q": {"before-20": "absent"}}}
    assert wires(rc) == []


def test_present_before_start():
    rc = recs()
    rc.start_when = {"q"}
    rc.item_states = {"item.x": {"q": {"all": "present"}}}
    rc.thing_edit = {("q", "item.x"): "we.q.thief"}
    rc.edits = {"we.q.thief": ("npc_add", None)}
    rc.edit_text = {"we.q.thief": "the thief on his round"}
    rc.quest_edits = {"q": {"we.q.thief"}}
    assert any(x.startswith("present_before_start") and "we.q.thief" in x for x in wires(rc))
    rc.edit_text["we.q.thief"] = "the thief, under an enable parent that stage 10 turns on"
    rc.enabled_by_quest = {"we.q.thief"}
    assert wires(rc) == []
    rc.enabled_by_quest = set()
    rc.quest_edits["p"] = {"we.q.thief"}                               # an earlier quest needs it too
    assert wires(rc) == []


def test_topic_per_speaker():
    rc = recs()
    rc.start_when = {"q"}
    rc.heard = [("q", "topic.t", "npc.a"), ("q", "topic.t", "npc.b")]
    rc.topic_rows = {("q", "topic.t", "npc.a")}
    w = wires(rc)
    assert len(w) == 1 and "npc.b" in w[0]
    rc.topic_rows.add(("q", "topic.t", "npc.b"))
    assert wires(rc) == []
    rc.topic_rows = set()
    rc.live = set()
    assert wires(rc) == []                                             # kept or adapted quests only


def test_pickpocket_can_fail():
    assert ac._can_fail_action("Pickpocket", "pickpocket") and ac._can_fail_action("pickpocket", None)


def test_hard_check_inside_any_with_gold_alternative():
    assert ac._hard_check({"speechcraft", "25", "100"})          # the skill beside a gold alternative still counts
    assert ac._hard_check({"speechcraft", "25", "bread"})


def test_choice_stage_whatever_it_leads_to():
    ch = lambda to, t: (to, {"topicHeardFrom"}, {t})
    assert ac._choice_stage([ch(20, "a"), ch(30, "b")], {99})     # successors need not be endings
    assert not ac._choice_stage([ch(20, "a"), ch(30, "a")], {99})


def test_skill_routes_scene_stage_exempt():
    rc = recs()
    rc.stages = {"q": {10: {"succ": [(20, {"sceneEnded"}, {"scene.q.s"})], "ff": set()},
                       20: {"succ": [(90, {"all", "sceneEnded", "topicHeardFrom"}, set()), (91, {"sceneEnded"}, set())],
                            "ff": set()},
                       90: {"succ": [], "ff": set()}, 91: {"succ": [], "ff": set()}}}
    rc.stage_end = {"q": {90, 91}}
    rc.quest_kind = {"q": ("local", None)}
    assert ac.skill_routes(rc) == []                                       # a scene's end is not a skill route
    rc.stages["q"][10]["succ"] = [(20, {"inZone"}, set())]
    assert any("stage 10 names no skill" in x for x in ac.skill_routes(rc))
