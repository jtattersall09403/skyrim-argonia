"""The story explorer's generator, on a small made-up story tree."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from tools.newworld import story_explorer as se

LINE = """# Sisei-Xul: the line's story

Intro with **bold** and *the Hist*.

### The later quests, at arc level

**MR03, What the Sleeper Dreams.** *Place*: Tsonac. Druja-Seel minds the tree.

## 3. The first two quests

### MR01. The Bitter Root

**The hidden truth (X).** Korydon is a town.

| Who | Where they stand | What they want | If they die |
|---|---|---|---|
| Okeeh-Ja, the Listener (man) | the hall | the cause found | fails |

| Stage | What moves it | Journal gist | Objective and its marker |
|---|---|---|---|
| 10 | a line | went | speak |
| 20 | a line | saw | find |

```sketch
place hall indoors "the Tree-Minders' Hall at Helstrom"
place korydon outdoors "Korydon"
person okeeh at hall "Okeeh-Ja"
```

## 5. Read on paper

Readers liked MR01.
"""

REGION = """# Ultherus Swamp

## Its places

### Korydon

A town of chime-smiths on a ring of dry ground.
"""


def tree(root: Path) -> Path:
    (root / se.LINES).mkdir(parents=True)
    (root / se.WORLD / "regions").mkdir(parents=True)
    (root / se.LINES / "sisei-xul.md").write_text(LINE)
    (root / se.LINES / "old.md").write_text("# Old\n")
    (root / se.LINES / "old-newworld.md").write_text("# New\n")
    (root / se.WORLD / "regions" / "ultherus-swamp.md").write_text(REGION)
    return root


def test_generate(tmp_path):
    root = tree(tmp_path / "r")
    out = tmp_path / "out"
    c = se.generate(root, out)
    assert "story/design/quests/lines/old.md" not in [d["path"] for d in c["docs"]]
    q = {x["id"]: x for x in c["quests"]}
    assert q["MR01"]["status"] == "reviewed" and len(q["MR01"]["stages"]) == 2
    assert q["MR01"]["cast"][0]["name"].startswith("Okeeh-Ja")
    assert q["MR03"]["status"] == "outlined" and q["MR03"]["title"] == "What the Sleeper Dreams"
    korydon = next(p for p in c["places"] if p["name"] == "Korydon")
    assert korydon["region"] == "Ultherus Swamp" and "MR01" in korydon["quests"] and "chime" in korydon["about"]
    assert "MR01" in next(p for p in c["people"] if p["name"] == "Okeeh-Ja")["quests"]
    doc = json.loads((out / "data" / "doc-sisei-xul.json").read_text())
    ids = [b["id"] for b in doc["blocks"]]
    assert len(ids) == len(set(ids))
    assert any("<b>bold</b>" in b.get("html", "") for b in doc["blocks"])
    assert (out / "index.html").exists()
    assert all({"id", "kind", "a", "b"} <= set(e) for e in c["links"])


def test_a_story_status_reaches_the_catalogue(tmp_path):
    root = tree(tmp_path / "r")
    p = root / se.LINES / "sisei-xul.md"
    p.write_text(LINE.replace("Intro with", "**Status: to be rewritten.** Section 3 is untrue.\n\nIntro with"))
    c = se.generate(root, tmp_path / "out")
    assert next(x for x in c["lines"] if x["id"] == "sisei-xul")["status"] == "to be rewritten"
    assert next(x for x in c["docs"] if x["id"] == "sisei-xul")["status"] == "to be rewritten"


def test_block_ids_stable_when_another_section_changes():
    a = se.build_doc(Path("x.md"), LINE)
    b = se.build_doc(Path("x.md"), LINE.replace("Readers liked MR01.", "Readers liked MR01.\n\nMore."))
    mr01 = lambda d: [x["id"] for x in d["blocks"] if x["section"].endswith("MR01. The Bitter Root")]  # noqa: E731
    assert mr01(a) == mr01(b)


def test_inline_is_safe():
    assert se.inline("<script>x</script> [link](http://a) `c`") == "&lt;script&gt;x&lt;/script&gt; link <code>c</code>"


def test_check_follows_sources(tmp_path):
    root = tree(tmp_path / "r")
    rec = tmp_path / "rec.json"
    rec.write_text(json.dumps({"url": "u", "published_hash": se.sources_hash(root)}))
    assert se.check(root, rec) is None
    (root / se.LINES / "sisei-xul.md").write_text(LINE + "\nChanged.\n")
    assert "behind" in se.check(root, rec)


def _merge(local, gone, remote):
    """Run the page's own mergeDrafts in node on one case."""
    node = shutil.which("node")
    if not node:
        pytest.skip("node not installed")
    page = se.PAGE.read_text()
    fn = page.split("/* merge:start")[1].split("/* merge:end */")[0].split("*/", 1)[1]
    js = fn + f"\nconsole.log(JSON.stringify(mergeDrafts({json.dumps(local)}, {json.dumps(gone)}, {json.dumps(remote)})));"
    return json.loads(subprocess.run([node, "-e", js], capture_output=True, text=True, check=True).stdout)


def test_merge_uploads_local_only_drafts_and_keeps_old_shape():
    m = _merge([{"id": "n1", "note": "old draft"}], {}, [])
    assert [d["id"] for d in m["drafts"]] == ["n1"] and [d["id"] for d in m["upload"]] == ["n1"]


def test_merge_loads_drafts_from_the_store():
    m = _merge([], {}, [{"id": "n2", "note": "from phone", "updatedAt": 5, "deleted": False, "by": "u"}])
    assert m["drafts"] == [{"id": "n2", "note": "from phone", "updatedAt": 5}] and not m["upload"]


def test_merge_removed_stays_removed_both_ways():
    gone_here = _merge([], {"n3": 9}, [{"id": "n3", "note": "x", "updatedAt": 4, "deleted": False}])
    assert gone_here["drafts"] == [] and gone_here["tomb"] == ["n3"]
    gone_there = _merge([{"id": "n4", "note": "x", "updatedAt": 3}], {}, [{"id": "n4", "updatedAt": 8, "deleted": True}])
    assert gone_there["drafts"] == [] and gone_there["gone"] == {"n4": 8}


def test_merge_newest_edit_wins():
    m = _merge([{"id": "n5", "note": "new", "updatedAt": 9}], {}, [{"id": "n5", "note": "old", "updatedAt": 2, "deleted": False}])
    assert m["drafts"][0]["note"] == "new" and m["upload"][0]["note"] == "new"
    m = _merge([{"id": "n5", "note": "old", "updatedAt": 2}], {}, [{"id": "n5", "note": "new", "updatedAt": 9, "deleted": False}])
    assert m["drafts"][0]["note"] == "new" and not m["upload"]


PLOT = """# The Chainbreakers: the plot

The faction's plot, whole.

**Words.** *The Owing*: the marsh's sentence.

## 1. What the faction is

The Chainbreakers buy the bound out of their Owing.

## 2. The people who matter

| Who | What they want | What they hide |
|---|---|---|
| **Never-Sold**, the Chainbreakers' head, at Reedfall | every debtor freed | her own past |

## 3. The acts

### Act I: the gate

1. **The Gate** (Reedfall). The player buys three people out.
2. **The Broker** (Ussa-Rekh). The broker sells a debt.

## 4. What it needs

| Place | The thing | Quest |
|---|---|---|
| Reedfall | a gate with a keeper | 1. The Gate |
"""


def plot_tree(root: Path) -> Path:
    (root / se.LINES).mkdir(parents=True)
    (root / se.LINES / "main-plot.md").write_text(PLOT.replace("The Chainbreakers: the plot", "The Eye and the Root: the plot"))
    (root / se.LINES / "chainbreakers.md").write_text(PLOT)
    return root


def test_a_plot_form_faction_story_is_read_as_the_main_plot_is(tmp_path):
    c = se.generate(plot_tree(tmp_path / "r"), tmp_path / "out")
    lines = {x["id"]: x for x in c["lines"]}
    assert lines["chainbreakers"]["kind"] == lines["main-plot"]["kind"] == "plot"
    assert lines["chainbreakers"]["summary"].startswith("The Chainbreakers buy")
    assert c["quests"] == [] and lines["chainbreakers"]["quests"] == []
    assert "chainbreakers" in next(p for p in c["people"] if p["name"] == "Never-Sold")["docs"]
    assert "chainbreakers" in next(p for p in c["places"] if p["name"] == "Reedfall")["docs"]
    assert not any(d["kind"] == "spells" for d in c["docs"])


def test_a_page_with_neither_acts_nor_quests_is_background_not_a_line(tmp_path):
    root = plot_tree(tmp_path / "r")
    (root / se.LINES / "owing-house.md").write_text("# The house\n\nA family of Thorn.\n\n## Who leads it\n\nThe matriarch.\n")
    c = se.generate(root, tmp_path / "out")
    assert "owing-house" not in {x["id"] for x in c["lines"]}
    assert next(d for d in c["docs"] if d["id"] == "owing-house")["kind"] == "background"


def test_a_numbered_item_is_its_own_block_and_keeps_its_number():
    d = se.build_doc(Path("chainbreakers.md"), PLOT)
    items = [b for b in d["blocks"] if b["t"] == "list"]
    assert [len(b["items"]) for b in items] == [1, 1] and [b["start"] for b in items] == [1, 2]
    assert len({b["id"] for b in items}) == 2 and "The Broker" in items[1]["items"][0]


def test_spells_by_use_appears_when_its_source_exists(tmp_path):
    root = plot_tree(tmp_path / "r")
    (root / se.SPELLS).write_text("# Spells by use\n\n## Healing\n\nRestore Health heals.\n")
    c = se.generate(root, tmp_path / "out")
    doc = next(d for d in c["docs"] if d["id"] == "spell-groups")
    assert doc["kind"] == "spells" and doc["title"] == "Spells by use"
    assert (tmp_path / "out" / "data" / "doc-spell-groups.json").exists()


def test_the_note_bar_sits_under_the_header_clear_of_chrome_android():
    """Chrome on Android covers the bottom of the screen (touch to search) and the words' surroundings (its
    selection toolbar); the note bar is fixed under the sticky header, its top set from the header's bottom."""
    page = se.PAGE.read_text()
    rule = page.split(".act{", 1)[1].split("}", 1)[0]
    assert "position:fixed" in rule and "top:var(--act-top" in rule and "bottom:" not in rule
    assert "getBoundingClientRect" in page.split("function placeAct", 1)[1][:200]


RECORD_YAML = """id: quest.main.mn02
code: MN02
title: The Dry Tree
line: quest.line.main
premise: A dying tree and a herald who wants it saved.
anchorPlaces: [jal-veesa]
cast:
- {id: npc.mn.vosh-leera, name: Vosh-Leera, persona: {role: root-herald, race: Argonian, home: jal-veesa}, wants: the tree saved}
stages:
- {id: 10, place: jal-veesa, journalText: I am to see Vosh-Leera., objectives: [{objectiveText: Speak to Vosh-Leera.}],
   information: {next: Go to Jal-Veesa.}}
- {id: 90, ending: true, journalText: It is done.}
endings:
- {id: e-done, when: the tree was saved, seen: the herald thanks the player, rewards: [{giveGold: 50}]}
"""


def record_tree(root: Path) -> Path:
    plot_tree(root)
    (root / se.RECORDS / "main").mkdir(parents=True)
    (root / se.RECORDS / "main" / "mn02.yaml").write_text(RECORD_YAML)
    return root


def test_a_quest_record_is_a_quest_with_its_stages(tmp_path):
    root = record_tree(tmp_path / "r")
    c = se.generate(root, tmp_path / "out")
    q = next(x for x in c["quests"] if x["id"] == "MN02")
    assert (q["title"], q["line"], q["status"], q["doc"]) == ("The Dry Tree", "main-plot", "written", "mn02")
    assert [s["stage"] for s in q["stages"]] == ["10", "90"]
    assert [f["name"] for f in q["fields"]] == ["Premise", "Before this", "People", "Places", "Stages",
                                                  "Endings", "Leads on"]
    assert "MN02" in next(x for x in c["lines"] if x["id"] == "main-plot")["quests"]
    doc = json.loads((tmp_path / "out" / "data" / "doc-mn02.json").read_text())
    text = json.dumps(doc)
    assert "Speak to Vosh-Leera." in text and "50 gold" in text
    assert all(b["id"].startswith("mn02/") for b in doc["blocks"])
    assert "MN02" in next(p for p in c["people"] if p["name"] == "Vosh-Leera")["quests"]
    grade = root / se.PLAYTESTS / "quest.main.mn02" / "run1" / "grade.md"
    grade.parent.mkdir(parents=True)
    grade.write_text("pass: all clear\n")
    assert next(x for x in se.generate(root, tmp_path / "out")["quests"] if x["id"] == "MN02")["status"] == "reviewed"


def test_a_record_change_changes_the_hash(tmp_path):
    root = record_tree(tmp_path / "r")
    before = se.sources_hash(root)
    p = root / se.RECORDS / "main" / "mn02.yaml"
    p.write_text(p.read_text().replace("Dry Tree", "Wet Tree"))
    assert se.sources_hash(root) != before


PLAY_YAML = """
id: quest.main.mn02
code: MN02
title: The Dry Tree
line: quest.line.main
start: 10
startWhen: {questStage: [quest.main.mn01, '=', 90]}
cast:
- {id: npc.mn.minder, persona: {name: Weeltul}}
placements:
- {ref: npc.mn.minder, kind: person, anchor: {place: jal-veesa, need: beside the sick tree}}
stages:
- {id: 10, journalText: Bring the moss., successors: [{to: 30, when: {topicHeardFrom: [topic.give, npc.mn.minder]}}]}
- {id: 30, ending: complete, journalText: I am to go to Vosh-Leera's House.}
topics:
- {id: topic.give, label: I brought the moss., person: npc.mn.minder, stages: [10], essential: true,
   intent: 'Weeltul. Tells: Vosh-Leera waits in her house on the bank. Does: sets stage 30.'}
- {id: topic.eggs, label: Tell me about the eggs., person: npc.mn.minder, stages: [10],
   intent: 'Weeltul. Tells: the eggs are cooling.'}
"""

PREV_YAML = """
id: quest.main.mn01
code: MN01
title: No Name
line: quest.line.main
start: 90
stages:
- {id: 90, ending: complete, journalText: Go east to Jal-Veesa., information: {next: Go east.}}
"""


def test_a_stage_shows_who_moved_it_what_they_said_and_the_thread():
    import yaml
    from tools.newworld import quest_play as QP
    q, prev = yaml.safe_load(PLAY_YAML), yaml.safe_load(PREV_YAML)
    recs = {q["id"]: q, prev["id"]: prev}
    md = se.record_markdown(q, recs)
    s30 = md.split("### Stage 30")[1]
    assert "you say to Weeltul (beside the sick tree, at Jal-Veesa): “I brought the moss.”" in s30
    assert "Vosh-Leera waits in her house on the bank." in s30
    assert s30.index("What you are told") < s30.index("Journal.")
    assert "“Tell me about the eggs.”, asked of Weeltul: the eggs are cooling." in md
    assert "[MN01. No Name](#q-mn01)" in md.split("## Before this")[1]
    assert "[MN02. The Dry Tree](#q-mn02)" in se.record_markdown(prev, recs)
    assert "### MN02 Stage 30" in QP.whole_story("Main", [prev, q], recs)
    assert '<a href="#q-mn01">' in se.inline("[MN01](#q-mn01)") and "http" not in se.inline("[x](http://e)")
