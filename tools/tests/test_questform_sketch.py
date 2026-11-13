"""The outline's sketch (tools/questform/sketch.py): the worked example and patterns pass; each fault class a writer
meets is named on the story line that holds it."""
from pathlib import Path

import pytest

from tools.questform import sketch

REPO = Path(__file__).resolve().parents[2]
BUILDABLE = REPO / ".claude/skills/story-line/buildable.md"

GOOD = '''# a story

```sketch
quest T01 minor "The Toll at the Bridge"
start game 0

place bridge outdoors "the reed bridge"
place town outdoors far "Lilyhall"
place hall indoors "Sarel's hall"

person giver at hall "Sarel"
person tollman at bridge level 8 "the tollman"
thing purse on tollman "the toll purse"

stage 0 hidden
stage 10 "Sarel wants the toll purse from the tollman at the reed bridge."
stage 20 "The tollman told me to take the purse."
stage 30 "I have the toll purse."
stage 90 completed "I gave Sarel the toll purse." do take purse, give-gold 50
stage 95 failed "Sarel is dead."

objective 10 at 10, 20 "Get the toll purse" -> purse, tollman
objective 30 at 30 "Bring the purse to Sarel" -> giver

line job giver at 0 ask "Any work?" -> 10 says "the purse"
line ask tollman at 10 ask "Give me the purse." if skill Speech 30 -> 20 else "Pay or swim." says "take it, then"
line hand giver at 30 ask "Here is the purse." if holds purse -> 90 says "she pays"

take purse from 10 -> 30
must-live giver fails 95
```
'''


def run(tmp_path, text, walk=True):
    p = tmp_path / "story.md"
    p.write_text(text, encoding="utf-8")
    return sketch.check(p, walk=walk)


def rules_of(faults):
    return {f["rule"] for f in faults if f["rule"] != "_ok"}


def test_buildable_examples_pass():
    faults = sketch.check(BUILDABLE)
    assert rules_of(faults) == set(), [f["message"] for f in faults]
    assert len(sketch.read(BUILDABLE)) >= 9


def test_good_sketch_passes_and_is_walked(tmp_path):
    faults = run(tmp_path, GOOD)
    assert rules_of(faults) == set(), [f["message"] for f in faults]
    assert any(f["rule"] == "_ok" for f in faults)         # the reach walk ran and found every ending


def test_take_gets_its_held_check_and_a_late_take_closes(tmp_path):
    form, _ = sketch.expand(sketch.read(_write(tmp_path, GOOD))[0])
    st10 = next(s for s in form["stages"] if s["number"] == 10)
    assert {"do": "set_stage", "stage": 30, "if_held": "purse"} in st10["results"]
    refusal = [ln for ln in form["lines"] if ln["id"].endswith(".else")]
    assert refusal and refusal[0]["conditions"] == [] and "(Persuade)" in refusal[0]["prompt"]


def _write(tmp_path, text):
    p = tmp_path / "s.md"
    p.write_text(text, encoding="utf-8")
    return p


BREAKS = [
    # (what the writer wrote instead, the fault named)
    ('line hand giver at 30 ask "Here is the purse." if holds purse -> 90 says "she pays"',
     'line hand giver at 30 ask "Here is the purse." if holds purse -> 90 do give-gold 50 says "she pays"',
     "line-result"),
    ('line ask tollman at 10 ask "Give me the purse." if skill Speech 30 -> 20 else "Pay or swim." says "take it, then"',
     'line ask tollman at 10 ask "Give me the purse." hostile says "he draws"', "line-hostile"),
    ('person tollman at bridge level 8 "the tollman"', 'person tollman at bridge hostile level 8 "the tollman"',
     "hostile-speaks"),
    ('person giver at hall "Sarel"', 'person giver at hall "Sarel"\nperson old at bridge dead "an old body"', "body"),
    ('thing purse on tollman "the toll purse"', 'thing purse on tollman "the toll purse"\nthing purse2 at bridge "the toll purse"\nobjective 11 at 10 "Look" -> purse2',
     "one-name"),
    ('stage 20 "The tollman told me to take the purse."', 'stage 20 "The tollman gave me the purse." do give purse',
     "give-placed"),
    ('stage 30 "I have the toll purse."', 'stage 30 "I have the toll purse." do give purse', "give-twice"),
    ('line hand giver at 30 ask "Here is the purse." if holds purse -> 90 says "she pays"',
     'line hand giver at 30 ask "Here is the purse." -> 90 says "she pays"', "take-unheld"),
    ('take purse from 10 -> 30', 'take purse from 10 -> 30\ndeath tollman from 10 -> 30 choice', "dead-early"),
    ('take purse from 10 -> 30', 'take purse from 10 -> 30\ndeath tollman from 0 -> 30 choice', "early-death"),
    ('must-live giver fails 95', '', "needs-living"),
    ('line hand giver at 30 ask "Here is the purse." if holds purse -> 90 says "she pays"',
     'line hand giver at 30 ask "Here is the purse." if holds purse, number t01.told = 1 -> 90 says "she pays"',
     "number-set"),
    ('if skill Speech 30 -> 20 else "Pay or swim."', 'if skill Speech 30 -> 20', "refusal"),
    ('line job giver at 0 ask "Any work?" -> 10 says "the purse"',
     'line job giver at 0 ask "Any work?" if regard giver 1 -> 10 says "the purse"\nline why giver at 0-30 ask "Why?" says "the purse"',
     "before-offer"),
    ('thing purse on tollman "the toll purse"', 'thing purse on tollman "the toll purse"\nthing stakes at bridge off "eleven grave-stakes"\nobjective 12 at 30 "See" -> stakes', "one-ref-many"),
    ('person tollman at bridge level 8 "the tollman"', 'person tollman at bridge existing level 8 "the tollman"', "existing"),
    ('line job giver at 0 ask "Any work?" -> 10', 'line job giver at 0 ask "Any work?" if rank reed 0 -> 10', "rank-set"),
    ('stage 20 "The tollman told me to take the purse."',
     'stage 20 "The tollman told me to take the purse." do off tollman', "away"),
    ('must-live giver fails 95', 'must-live giver fails 95\ndeath giver from 10 -> 30 choice', "death-both-ways"),
    ('line job giver at 0 ask "Any work?" -> 10 says "the purse"',
     'line job giver at 0 ask "Any work?" -> 10 says "the purse"\nline back giver at 30 ask "Wait." -> 20 says "x"',
     "stage-order"),
    ('stage 30 "I have the toll purse."', 'stage 30 "I have the toll purse."\nstage 40 "A dead end."\n'
     'line odd tollman at 20 ask "Odd." -> 40 says "x"', "way-out"),
    ('objective 10 at 10, 20 "Get the toll purse" -> purse, tollman', 'objective 10 at 10, 20 "Get the toll purse" -> tollman',
     "asked-is-target"),
    ('if skill Speech 30 -> 20 else "Pay or swim."', 'if gold 5000 -> 20 else "Pay or swim."', None),
]


@pytest.mark.parametrize("old, new, rule", BREAKS, ids=[b[2] or "unreachable" for b in BREAKS])
def test_each_fault_is_named_on_its_line(tmp_path, old, new, rule):
    assert old in GOOD
    text = GOOD.replace(old, new, 1)
    faults = [f for f in run(tmp_path, text) if f["rule"] != "_ok"]
    if rule is None:            # a stage only gold beyond any player opens: the walk names it, the rules do not
        assert rules_of(faults) == {"reach"}, [f["message"] for f in faults]
        return
    got = [f for f in faults if f["rule"] == rule]
    assert got, (rule, [(f["rule"], f["message"]) for f in faults])
    lines = text.splitlines()
    assert got[0]["line"] and lines[got[0]["line"] - 1].strip(), got[0]
    assert got[0]["gloss"]


@pytest.mark.parametrize("word", ["enter", "count", "see", "wait", "cast"])
def test_what_the_game_cannot_know_is_refused_with_its_nearest(tmp_path, word):
    text = GOOD.replace("take purse from 10 -> 30", f"{word} bridge from 10 -> 30\ntake purse from 10 -> 30")
    faults = run(tmp_path, text, walk=False)
    msg = [f["message"] for f in faults if f["rule"] == "sketch"]
    assert msg and sketch.CANNOT[word] in msg[0]


def test_report_names_the_file_line_and_what_is_left_for_the_build(tmp_path):
    p = _write(tmp_path, GOOD.replace('if skill Speech 30 -> 20 else "Pay or swim."', 'if skill Speech 30 -> 20'))
    text, n = sketch.report(p, sketch.check(p, walk=False))
    at = 1 + next(i for i, ln in enumerate(p.read_text().splitlines()) if ln.startswith("line ask tollman"))
    assert n == 1 and f"{p}:{at}:" in text and "checked when built" in text and text.endswith("1 fault(s)")


MORE_BREAKS = [
    ('objective 10 at 10, 20 "Get the toll purse" -> purse, tollman', 'objective 10 at 10, 20 "Get the toll purse" -> tollman',
     "marker-dead"),
    ('line job giver at 0 ask "Any work?" -> 10 says "the purse"',
     'line job giver at 0 ask "Any work?" -> 10 says "the purse"\nline point tollman at 0 ask "Any work?" says "see Sarel"',
     "pointer-alive"),
    ('stage 90 completed "I gave Sarel the toll purse." do take purse, give-gold 50',
     'stage 90 completed "I gave Sarel the toll purse." do take purse, teach shadow "Shadow"', "spell"),
    ('stage 90 completed "I gave Sarel the toll purse." do take purse, give-gold 50',
     'stage 90 completed "I gave Sarel the toll purse." do take purse, enemy thalmor', "enemy"),
]


@pytest.mark.parametrize("old, new, rule", MORE_BREAKS, ids=[b[2] for b in MORE_BREAKS])
def test_each_new_fault_is_named(tmp_path, old, new, rule):
    test_each_fault_is_named_on_its_line(tmp_path, old, new, rule)


def test_a_pointer_with_the_offers_gates_passes(tmp_path):
    text = GOOD.replace('line job giver at 0 ask "Any work?" -> 10 says "the purse"',
                        'line job giver at 0 ask "Any work?" -> 10 says "the purse"\n'
                        'line point tollman at 0 ask "Any work?" if alive giver says "see Sarel"')
    assert "pointer-alive" not in rules_of(run(tmp_path, text, walk=False))


def test_the_gift_words_are_stage_results_with_their_names(tmp_path):
    text = GOOD.replace('do take purse, give-gold 50', 'do take purse, give-gold 50, teach 017122:Skyrim.esm "Shadow", '
                        'enemy 039F26:Skyrim.esm, leave reed')
    assert rules_of(run(tmp_path, text)) == set()
    form, _ = sketch.expand(sketch.read(_write(tmp_path, text))[0])
    st90 = next(s for s in form["stages"] if s["number"] == 90)
    assert {"do": "teach_spell", "spell": "017122:Skyrim.esm"} in st90["results"]
    assert {"do": "make_enemy", "faction": "039F26:Skyrim.esm"} in st90["results"]
    assert {"do": "leave_faction", "faction": "reed"} in st90["results"]
    assert form["names"]["017122:Skyrim.esm"] == "Shadow"


def test_the_power_words_are_stage_results(tmp_path):
    text = GOOD.replace('place hall indoors "Sarel\'s hall"', 'place hall indoors "Sarel\'s hall"\nmarker hill at bridge "the hill"')
    text = text.replace('do take purse, give-gold 50', 'do take purse, give-gold 50, perk 0BE123:Skyrim.esm "Agility", '
                        'map hill, bounty 10CEE9:Skyrim.esm 0, home "0AA665:Black Marsh.esm", skill-up Sneak 2, '
                        'unperk 0BE123:Skyrim.esm')
    assert rules_of(run(tmp_path, text)) == set()
    form, _ = sketch.expand(sketch.read(_write(tmp_path, text))[0])
    st90 = next(s for s in form["stages"] if s["number"] == 90)
    for want in ({"do": "add_perk", "perk": "0BE123:Skyrim.esm"}, {"do": "mark_on_map", "ref": "hill"},
                 {"do": "set_bounty", "faction": "10CEE9:Skyrim.esm", "amount": 0},
                 {"do": "own_room", "cell": "0AA665:Black Marsh.esm"}, {"do": "raise_skill", "skill": "Sneak", "by": 2},
                 {"do": "remove_perk", "perk": "0BE123:Skyrim.esm"}):
        assert want in st90["results"]
    assert form["names"]["0BE123:Skyrim.esm"] == "Agility"
    assert next(r for r in form["refs"] if r["id"] == "hill")["kind"] == "marker"


def test_a_map_word_names_a_marker_and_a_perk_its_name(tmp_path):
    base = GOOD.replace('do take purse, give-gold 50', 'do take purse, give-gold 50, {}')
    assert "map-marker" in rules_of(run(tmp_path, base.format("map giver"), walk=False))
    assert "perk" in rules_of(run(tmp_path, base.format("unperk 0BE123:Skyrim.esm"), walk=False))
    assert "bounty" in rules_of(run(tmp_path, base.format("bounty thalmor 5"), walk=False))
    assert "room" in rules_of(run(tmp_path, base.format("home hall"), walk=False))
