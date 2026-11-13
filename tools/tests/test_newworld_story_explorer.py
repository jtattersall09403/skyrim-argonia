"""The story explorer's generator, on a small made-up story tree."""
import json
from pathlib import Path

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
