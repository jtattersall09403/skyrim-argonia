"""The story explorer's generator, on a small made-up story tree."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from tools.newworld import story_explorer as se

LINE = """# Many-Root: the line's story

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
    (root / se.LINES / "many-root.md").write_text(LINE)
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
    doc = json.loads((out / "data" / "doc-many-root.json").read_text())
    ids = [b["id"] for b in doc["blocks"]]
    assert len(ids) == len(set(ids))
    assert any("<b>bold</b>" in b.get("html", "") for b in doc["blocks"])
    assert (out / "index.html").exists()
    assert all({"id", "kind", "a", "b"} <= set(e) for e in c["links"])


def test_a_story_status_reaches_the_catalogue(tmp_path):
    root = tree(tmp_path / "r")
    p = root / se.LINES / "many-root.md"
    p.write_text(LINE.replace("Intro with", "**Status: to be rewritten.** Section 3 is untrue.\n\nIntro with"))
    c = se.generate(root, tmp_path / "out")
    assert next(x for x in c["lines"] if x["id"] == "many-root")["status"] == "to be rewritten"
    assert next(x for x in c["docs"] if x["id"] == "many-root")["status"] == "to be rewritten"


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
    (root / se.LINES / "many-root.md").write_text(LINE + "\nChanged.\n")
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
