"""The story explorer: the new world's story and quests as one private page for the owner to read and annotate.

Reads the new world's story sources (the line stories, the main quest's plot, the province plan and the
consistency ledger under story/design/quests/lines/, and the province digest under story/design/world/) and writes
out/story-explorer/: the page (copied from story_explorer_page.html, never edited per story) and its data files.
Nothing is hand-copied: a new line, quest, person or place appears on the next generation.

    python -m tools.newworld.story_explorer build            # write out/story-explorer/
    python -m tools.newworld.story_explorer check            # fail when the sources changed since the last publish
    python -m tools.newworld.story_explorer mark-published   # after publishing: record the sources' hash

The published page's url and the hash of the sources it was published from live in story_explorer.json beside
this file. The owner's notes are read and answered by the skill story-feedback.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.playtest.game import HarnessError  # noqa: E402
from tools.playtest.record import humanize, load  # noqa: E402  the quest tools' one reader of a record
from tools.newworld import quest_play as QP  # noqa: E402  a record read as the play

ROOT = Path(__file__).resolve().parents[2]
LINES = Path("story/design/quests/lines")
WORLD = Path("story/design/world")
WORLD_FILES = ("index.md", "province.md", "people.md")
SPELLS = Path("story/design/quests/spell-groups.md")   # the spells grouped by use: a plain document, when it exists
PAGE = Path(__file__).with_name("story_explorer_page.html")
RECORD = Path(__file__).with_name("story_explorer.json")
OUT = ROOT / "out" / "story-explorer"
PLUGIN_QUESTS = Path("plugin/Argonia/Quests")
RECORDS = Path("newworld/story/quests")          # quest records, one YAML view each: <line>/<code>.yaml
PLAYTESTS = Path("story/playtests")             # paper playtest runs: <quest id>/<run>/grade.md

QUEST_HEAD = re.compile(r"^([A-Z]{2}\d{2})\.\s+(.+)$")
ARC_QUEST = re.compile(r"^\*\*([A-Z]{2}\d{2})[.,]?\s+(.+?)\*\*\s*(.*)$")
FIELD = re.compile(r"^\*\*([^*]{2,80}?)\*\*\s*(.*)$")
STATUS = re.compile(r"^\*\*Status:\s*([^*]+?)\.?\*\*")   # a story's status at its head: "to be rewritten", "replaced by ..."


# ---- sources -------------------------------------------------------------------------------------------------

def sources(root: Path = ROOT) -> list[Path]:
    """Every file the explorer reads, relative to root, in a fixed order. A story with a `-newworld` twin is the
    old world's and is left out."""
    lines = sorted((root / LINES).glob("*.md"))
    names = {p.stem for p in lines}
    out = [p for p in lines if f"{p.stem}-newworld" not in names]
    out += [root / WORLD / f for f in WORLD_FILES if (root / WORLD / f).exists()]
    out += sorted((root / WORLD / "regions").glob("*.md"))
    if (root / SPELLS).exists():
        out.append(root / SPELLS)
    out += record_files(root)
    out += sorted((root / PLAYTESTS).glob("*/*/grade.md"))
    return [p.relative_to(root) for p in out]


def record_files(root: Path = ROOT) -> list[Path]:
    """The new world's quest records: each record's YAML view, the quest skills' source for it."""
    return sorted((root / RECORDS).glob("*/*.yaml"))


def sources_hash(root: Path = ROOT) -> str:
    h = hashlib.sha256()
    for rel in sources(root):
        h.update(str(rel).encode() + b"\0" + (root / rel).read_bytes() + b"\0")
    return h.hexdigest()[:16]


# ---- markdown to blocks --------------------------------------------------------------------------------------

def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60] or "x"


def inline(s: str) -> str:
    """Markdown inline markup to safe HTML: code, bold, italic; links keep their text."""
    s = re.sub(r"<!--.*?-->", "", s)
    s = html.escape(s, quote=False)
    s = re.sub(r"\[([^\]]+)\]\((#[\w-]+)\)", r'<a href="\2">\1</a>', s)   # a link within the page stays a link
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", s)
    return s.strip()


def plain(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", inline(s)))


def cells(row: str) -> list[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]


def parse(text: str) -> list[dict]:
    """Markdown to a flat list of blocks: h (level, text), p, list, table (head, rows), code (lang, text)."""
    blocks: list[dict] = []
    lines = re.sub(r"<!--.*?-->", "", text, flags=re.S).splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        if ln.startswith("```"):
            lang, body = ln[3:].strip(), []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                body.append(lines[i])
                i += 1
            blocks.append({"t": "code", "lang": lang, "text": "\n".join(body)})
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m:
            blocks.append({"t": "h", "level": len(m.group(1)), "text": m.group(2).strip()})
            i += 1
            continue
        if ln.lstrip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                if not re.match(r"^\s*\|[\s:|-]+\|?\s*$", lines[i]):
                    rows.append(cells(lines[i]))
                i += 1
            blocks.append({"t": "table", "head": rows[0], "rows": rows[1:]})
            continue
        if re.match(r"^\s*([-*]|\d+\.)\s+", ln):
            items: list[str] = []
            while i < len(lines) and lines[i].strip():
                if re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]):
                    items.append(re.sub(r"^\s*([-*]|\d+\.)\s+", "", lines[i]))
                else:
                    items[-1] += " " + lines[i].strip()
                i += 1
            ordered = bool(re.match(r"^\s*\d", ln))
            if ordered:  # each numbered item is its own block, so it can be noted on its own; it keeps its number
                start = int(re.match(r"^\s*(\d+)", ln).group(1))
                blocks += [{"t": "list", "ordered": True, "items": [x], "start": start + k} for k, x in enumerate(items)]
            elif any(ARC_QUEST.match(x) for x in items):  # a list of quests: one block each, so each is its own quest
                blocks += [{"t": "list", "ordered": ordered, "items": [x]} for x in items]
            else:
                blocks.append({"t": "list", "ordered": ordered, "items": items})
            continue
        para = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,6}\s|```|\s*\||\s*([-*]|\d+\.)\s)", lines[i]):
            para.append(lines[i].strip())
            i += 1
        blocks.append({"t": "p", "text": " ".join(para)})
    return blocks


def render(b: dict) -> dict:
    """A block as the page shows it: inline markup already safe HTML."""
    if b["t"] == "p":
        return {"t": "p", "html": inline(b["text"])}
    if b["t"] == "h":
        return {"t": "h", "level": b["level"], "html": inline(b["text"])}
    if b["t"] == "list":
        return {"t": "list", "ordered": b["ordered"], "items": [inline(x) for x in b["items"]], "start": b.get("start", 1)}
    if b["t"] == "table":
        return {"t": "table", "head": [inline(x) for x in b["head"]], "rows": [[inline(x) for x in r] for r in b["rows"]]}
    return {"t": "code", "lang": b["lang"], "text": b["text"]}


# ---- documents, sections, quests -----------------------------------------------------------------------------

PLOT_ACTS = re.compile(r"^#{2,3}\s+(\d+\.\s+)?The acts\s*$", re.M | re.I)


def doc_kind(rel: Path, text: str = "") -> str:
    """A line file in the plot form (a short page with a section "The acts", as main-plot.md) is a plot; the main
    quest's plot is the one with the id main-plot, every other plot is a faction's. A line file with neither acts nor
    quests is a line's background page."""
    if rel == SPELLS:
        return "spells"
    if rel.parent == WORLD / "regions":
        return "region"
    if rel.parent == WORLD:
        return "world"
    if rel.stem == "main-plot" or PLOT_ACTS.search(text):
        return "plot"
    if rel.stem in ("consistency", "province-plan"):
        return "ledger"
    if not re.search(r"^#{2,4}\s+[A-Z]{2}\d{2}\.|^\*\*[A-Z]{2}\d{2}[.,]", text, re.M):
        return "background"   # a page with no acts and no quests: the background of a line (owing-house.md)
    return "line"


def build_doc(rel: Path, text: str) -> dict:
    """One source file as a document: its title, and its blocks each with a stable id (section slug and the
    block's number within the section) and the section it sits in."""
    blocks = parse(text)
    title = next((plain(b["text"]) for b in blocks if b["t"] == "h" and b["level"] == 1), rel.stem)
    did = slug(rel.stem)
    out, path, seen, count = [], [], set(), 0
    for b in blocks:
        if b["t"] == "h":
            path = path[: b["level"] - 1] + [plain(b["text"])]
            sid = slug(path[-1])
            while sid in seen:
                sid += "-2"
            seen.add(sid)
            count = 0
            b2 = render(b) | {"id": f"{did}/{sid}", "section": " / ".join(path[1:]) or title}
        else:
            count += 1
            sid = slug(path[-1]) if path else "top"
            b2 = render(b) | {"id": f"{did}/{sid if path else 'top'}/{count}", "section": " / ".join(path[1:]) or title}
        b2["_raw"] = b
        b2["h"] = hashlib.sha1(json.dumps(b, sort_keys=True).encode()).hexdigest()[:8]
        out.append(b2)
    status = next((STATUS.match(b["text"]).group(1).strip().lower() for b in blocks[:6]
                   if b["t"] == "p" and STATUS.match(b["text"])), None)
    return {"id": did, "path": str(rel), "kind": doc_kind(rel, text), "title": title, "blocks": out, "status": status}


def parse_sketch(text: str) -> dict:
    """The quest form's sketch: its places, people and things."""
    places, people, things = [], [], []
    for ln in text.splitlines():
        m = re.match(r'^(place|person|thing)\s+(\S+)(.*?)"([^"]+)"', ln.strip())
        if not m:
            continue
        kind, key, mid, name = m.groups()
        at = re.search(r"\bat\s+(\S+)", mid)
        row = {"key": key, "name": name, "at": at.group(1) if at else None}
        if kind == "place":
            row["indoors"] = "indoors" in mid
            places.append(row)
        elif kind == "person":
            row["existing"] = "existing" in mid
            row["hostile"] = "hostile" in mid
            people.append(row)
        else:
            things.append(row)
    return {"places": places, "people": people, "things": things}


def quests_of(doc: dict, built: dict[str, str]) -> list[dict]:
    """The quests a line's story holds: written in full (a `### XX01. Title` section), or outlined at arc level
    (a paragraph opening `**XX03, Title.**`)."""
    if doc["kind"] not in ("line", "plot"):
        return []
    quests: dict[str, dict] = {}
    cur, field = None, None
    read_on_paper = ""
    in_read, read_level = False, 0
    for b in doc["blocks"]:
        raw = b["_raw"]
        if raw["t"] == "h":
            head = plain(raw["text"])
            if in_read and raw["level"] <= read_level:
                in_read = False
            if re.match(r"^(\d+\.\s+)?read on paper", head, re.I):
                in_read, read_level = True, raw["level"]
            m = QUEST_HEAD.match(head)
            if m:
                cur = quests.setdefault(m.group(1), {"id": m.group(1), "title": m.group(2).strip(), "full": True,
                                                       "blocks": [], "level": raw["level"]})
                cur["full"] = True
                field = "Opening"
                continue
            if cur and raw["level"] <= cur["level"]:
                cur = None
            if cur:
                field = head
            continue
        if in_read:
            read_on_paper += " " + json.dumps(raw)
        lead = raw["text"] if raw["t"] == "p" else raw["items"][0] if raw["t"] == "list" and len(raw["items"]) == 1 else ""
        if lead:
            am = ARC_QUEST.match(lead)
            if am and am.group(1) not in quests and not (cur and cur["full"] and cur["id"] == am.group(1)):
                cur = quests.setdefault(am.group(1), {"id": am.group(1), "title": am.group(2).rstrip("."),
                                                       "full": False, "blocks": [], "level": 99})
                field = "Outline"
            if cur:
                fm = FIELD.match(lead)
                if cur["full"] and fm:
                    field = fm.group(1).strip().rstrip(".")
        if cur:
            cur["blocks"].append((field, b))
    out = []
    for q in quests.values():
        fields: list[dict] = []
        cast, stages, sketch = [], [], {"places": [], "people": [], "things": []}
        for field, b in q["blocks"]:
            raw = b["_raw"]
            if raw["t"] == "code" and raw["lang"] == "sketch":
                sketch = parse_sketch(raw["text"])
            if raw["t"] == "table":
                head = [plain(x).lower() for x in raw["head"]]
                if head and head[0] == "who":
                    cast += [{"name": plain(r[0]), "row": dict(zip(head, (plain(x) for x in r)))} for r in raw["rows"]]
                if head and head[0] == "stage":
                    stages += [dict(zip(head, (plain(x) for x in r))) for r in raw["rows"]]
            if not fields or fields[-1]["name"] != field:
                fields.append({"name": field, "blocks": []})
            fields[-1]["blocks"].append(b["id"])
        text = " ".join(json.dumps(b["_raw"]) for _, b in q["blocks"])
        status = "written" if q["full"] and stages else "outlined"
        if status == "written" and q["id"] in read_on_paper:
            status = "reviewed"
        if q["title"] and built.get(q["id"], "").find(q["title"]) >= 0:
            status = "built"
        out.append({"id": q["id"], "title": q["title"], "line": doc["id"], "lineTitle": doc["title"],
                    "status": status, "fields": fields, "cast": cast, "stages": stages, "sketch": sketch,
                    "_text": text})
    return out


def built_records(root: Path) -> dict[str, str]:
    """Our plugin's quest records by quest id, as text: a quest counts as built when its record names its title."""
    out = {}
    for p in (root / PLUGIN_QUESTS).glob("ARG_*.yaml"):
        m = re.match(r"ARG_([A-Z]{2}\d{2})\b", p.name)
        if m:
            out[m.group(1)] = p.read_text(errors="ignore")
    return out


# ---- quest records -------------------------------------------------------------------------------------------

def _one(s) -> str:
    return re.sub(r"\s+", " ", str(s)).strip()


def _reward(a) -> str:
    """An ending's reward or world action in plain words."""
    if isinstance(a, dict) and len(a) == 1:
        (k, v), = a.items()
        if k == "giveGold":
            return f"{v} gold"
        if k == "giveItem" and isinstance(v, list):
            return f"{humanize(v[0])}" + (f" ({v[1]})" if len(v) > 1 and v[1] != 1 else "")
        if k == "setFactionRank" and isinstance(v, list):
            return f"a place in {humanize(v[0])}"
        return ""
    return _one(a) if isinstance(a, str) else ""


def record_markdown(q: dict, records: dict[str, dict] | None = None) -> str:
    """A quest record as a readable page: one section per kind of content, only those the record has; its stages
    read as the play (what happens, what the player is told, then the journal), between what came before and what
    leads on."""
    records = records or {q.get("id"): q}
    names = {c["id"]: c.get("name") or humanize(c["id"]) for c in q.get("cast") or [] if isinstance(c, dict)}
    pname = {p.get("anchor", {}).get("place") if isinstance(p.get("anchor"), dict) else None: p.get("placeName")
             for p in q.get("placements") or [] if isinstance(p, dict) and p.get("placeName")}
    place = lambda pid: pname.get(pid) or humanize(pid)  # noqa: E731
    out = [f"# {q['code']}. {_one(q['title'])}"]
    if q.get("premise"):
        out += ["## Premise", _one(q["premise"])]
    out += ["## Before this", *QP.before_this(q, records)]
    if q.get("playerStart") or q.get("facts"):
        out.append("## What the player learns")
        if q.get("playerStart"):
            out.append("At the start: " + _one(", ".join(map(str, q["playerStart"]))) + ".")
        out += ["- " + _one(f["claim"]) for f in q.get("facts") or [] if isinstance(f, dict) and f.get("claim")]
    if q.get("cast"):
        out.append("## People")
        for c in q["cast"]:
            per = c.get("persona") if isinstance(c.get("persona"), dict) else {}
            bits = [x for x in (per.get("role"), per.get("race")) if x]
            home = f", at {place(str(per['home']).split(' ')[0])}" if per.get("home") else ""
            line = f"- **{names[c['id']]}**" + (f", {', '.join(map(str, bits))}" if bits else "") + home + "."
            if c.get("wants"):
                line += f" Wants {_one(c['wants'])}."
            if c.get("fears"):
                line += f" Fears {_one(c['fears'])}."
            out.append(line)
    places = list(dict.fromkeys([*(q.get("anchorPlaces") or []), *(s.get("place") for s in q.get("stages") or [])]))
    places = [p for p in places if p]
    if places:
        out += ["## Places", "- " + "\n- ".join(place(p) for p in places)]
    if q.get("things"):
        out.append("## Things")
        for t in q["things"]:
            if isinstance(t, dict) and t.get("name"):
                out.append(f"- **{_one(t['name'])}**" + (f": {_one(t['where'])}" if t.get("where") else "") + ".")
    if q.get("stages"):
        play = QP.Play(q, records)
        out += ["## Stages", QP.GIST_NOTE]
        for s in play.stages:
            out.append(f"### {QP.stage_heading(play, s)}")
            out += play.stage_play(s) + play.stage_rest(s)
        readable = play.readables()
        if readable:
            out += ["## Things you can read", *readable]
    if q.get("endings"):
        out.append("## Endings")
        for e in q["endings"]:
            line = f"- **When {_one(e.get('when', e['id']))}.**"
            if e.get("seen"):
                line += f" What follows: {_one(e['seen'])}."
            gives = [x for x in [*map(_reward, e.get("rewards") or []), *map(_reward, e.get("world") or [])] if x]
            gives += [_one(x) for x in (e.get("gives") or []) if isinstance(x, str)] if isinstance(e.get("gives"), list) \
                else ([_one(e["gives"])] if e.get("gives") else [])
            if gives:
                line += f" Gives: {'; '.join(gives)}."
            costs = e.get("costs")
            if costs:
                line += f" Costs: {'; '.join(map(_one, costs)) if isinstance(costs, list) else _one(costs)}."
            out.append(line)
    out += ["## Leads on", *QP.leads_on(q, records)]
    return "\n\n".join(out) + "\n"


def playtest_passed(root: Path, qid: str) -> bool:
    return any(g.read_text(errors="ignore").lstrip().lower().startswith("pass")
               for g in (root / PLAYTESTS / qid).glob("*/grade.md"))


def line_doc(line: str, docs: list[dict]) -> dict | None:
    """The explorer's line page for a record's `line` (quest.line.main -> main-plot)."""
    tail = str(line).split(".")[-1]
    ids = {d["id"]: d for d in docs if d["kind"] in ("line", "plot")}
    return next((ids[c] for c in (f"{tail}-plot", f"{tail}-newworld", tail) if c in ids), None)


def record_quests(root: Path, docs: list[dict], built: dict[str, str]) -> tuple[list[dict], list[dict]]:
    """Every quest record as a quest of the Quests tab, with the record's own page as a document."""
    quests, rdocs = [], []
    loaded = []
    for p in record_files(root):
        try:
            loaded.append((p, load(p)))
        except HarnessError:
            continue
    records = {q["id"]: q for _, q in loaded}
    by_line: dict[str, list[dict]] = {}
    for p, q in loaded:
        ld = line_doc(q.get("line", ""), docs)
        if not ld or not q.get("code"):
            continue
        by_line.setdefault(ld["id"], []).append(q)
        rel = p.relative_to(root)
        d = build_doc(rel, record_markdown(q, records))
        d["kind"] = "record"
        rdocs.append(d)
        fields: list[dict] = []
        for b in d["blocks"]:
            if b["_raw"]["t"] == "h" and b["_raw"]["level"] == 1:
                continue
            name = b["section"].split(" / ")[0]
            if not fields or fields[-1]["name"] != name:
                fields.append({"name": name, "blocks": []})
            fields[-1]["blocks"].append(b["id"])
        status = "reviewed" if playtest_passed(root, q["id"]) else "written"
        if built.get(q["code"], "").find(str(q["title"])) >= 0:
            status = "built"
        cast = [{"name": c.get("name") or humanize(c["id"]), "row": {"what they want": _one(c.get("wants", ""))}}
                for c in q.get("cast") or [] if isinstance(c, dict)]
        places = [b for b in d["blocks"] if b["section"] == "Places" and b["_raw"]["t"] == "list"]
        sketch = {"places": [{"name": plain(x)} for b in places for x in b["_raw"]["items"]], "people": [], "things": []}
        stages = [{"stage": str(s["id"]), "journal": _one(s.get("journalText", ""))} for s in q["stages"]]
        quests.append({"id": q["code"], "title": _one(q["title"]), "line": ld["id"], "lineTitle": ld["title"],
                       "doc": d["id"], "status": status, "fields": fields, "cast": cast, "stages": stages,
                       "sketch": sketch, "_text": " ".join(json.dumps(b["_raw"]) for b in d["blocks"])})
    for lid, recs in by_line.items():   # each line's quests as one story, beat by beat
        ld = next(x for x in docs if x["id"] == lid)
        recs = sorted(recs, key=lambda r: str(r["code"]))
        d = build_doc(Path(f"{lid}-whole-story.md"), QP.whole_story(ld["title"], recs, records))
        d["kind"], d["path"], d["line"] = "story", f"{RECORDS}/{recs[0]['line'].split('.')[-1]}", lid
        rdocs.append(d)
    return quests, rdocs


# ---- people and places ---------------------------------------------------------------------------------------

def people_and_places(docs: list[dict], quests: list[dict]) -> tuple[list[dict], list[dict]]:
    people: dict[str, dict] = {}
    places: dict[str, dict] = {}

    def person(name: str, src: str, what: str = ""):
        name = re.split(r"[;(]", name)[0].strip()
        if len(name) < 3 or len(name) > 40 or not name[0].isupper():
            return
        p = people.setdefault(slug(name), {"id": slug(name), "name": name, "about": [], "quests": [], "docs": []})
        if what and what not in p["about"]:
            p["about"].append(what)
        if src and src not in p["docs"]:
            p["docs"].append(src)

    def place(name: str, src: str, what: str = "", region: str = ""):
        name = re.sub(r"\s*\(.*?\)\s*$", "", name).strip()
        if len(name) < 3:
            return
        p = places.setdefault(slug(name), {"id": slug(name), "name": name, "about": "", "region": region,
                                           "quests": [], "docs": [], "block": None})
        if what and not p["about"]:
            p["about"] = what
        if region and not p["region"]:
            p["region"] = region
        if src and src not in p["docs"]:
            p["docs"].append(src)

    for d in docs:
        if d["kind"] == "region":
            blocks = d["blocks"]
            in_places = False
            for i, b in enumerate(blocks):
                raw = b["_raw"]
                if raw["t"] == "h" and raw["level"] == 2:
                    in_places = "places" in raw["text"].lower()
                if in_places and raw["t"] == "h" and raw["level"] == 3:
                    nxt = next((x["_raw"]["text"] for x in blocks[i + 1:i + 3] if x["_raw"]["t"] == "p"), "")
                    place(plain(raw["text"]), d["id"], plain(nxt)[:280], d["title"])
                    places[slug(re.sub(r"\s*\(.*?\)\s*$", "", plain(raw["text"])))]["block"] = b["id"]
        if d["kind"] == "plot":  # a plot names its people in a "Who" table and its places in the needs table
            for b in d["blocks"]:
                raw = b["_raw"]
                if raw["t"] != "table" or not raw["head"]:
                    continue
                head = plain(raw["head"][0]).lower()
                for r in raw["rows"]:
                    if head == "who":
                        bold = re.match(r"^\*\*(.+?)\*\*", r[0].strip())
                        person(plain(bold.group(1)) if bold else plain(r[0]).split(",")[0], d["id"],
                               plain(r[1]) if len(r) > 1 else "")
                    elif head == "place":
                        place(plain(r[0]), d["id"])
        if d["id"] == "people":
            for b in d["blocks"]:
                raw = b["_raw"]
                if raw["t"] == "table" and raw["head"] and plain(raw["head"][0]).lower() == "name":
                    for r in raw["rows"]:
                        person(plain(r[0]), d["id"], "; ".join(plain(x) for x in r[1:3]))
    for q in quests:
        for c in q["cast"]:
            person(c["name"].split(",")[0], q["line"], c["row"].get("what they want", ""))
        for s in q["sketch"]["people"]:
            if not s["name"].startswith(("the ", "a ", "an ")) and not s["name"][0].islower():
                person(s["name"], q["line"])
        for s in q["sketch"]["places"]:
            place(s["name"], q["line"])
    for coll in (people, places):
        for p in coll.values():
            pat = re.compile(r"(?<![\w-])" + re.escape(p["name"]) + r"(?![\w-])")
            p["quests"] = [q["id"] for q in quests if pat.search(q["_text"])]
    keep_people = [p for p in people.values() if p["quests"] or p["docs"]]
    return (sorted(keep_people, key=lambda p: p["name"].lower()),
            sorted(places.values(), key=lambda p: p["name"].lower()))


# ---- links between lines -------------------------------------------------------------------------------------

def links(docs: list[dict], quests: list[dict], people: list[dict], places: list[dict]) -> list[dict]:
    """Every link between two lines, generated: a crossing the consistency ledger rules on (section 3), a person or
    a place two lines' quests share, and a quest that names another line's quest. Each has a stable id made of its
    kind and its two ends, which is what a note on it is anchored to."""
    code_line = {q["id"][:2]: q["line"] for q in quests}
    qline = {q["id"]: q["line"] for q in quests}
    out: dict[str, dict] = {}

    def add(kind, a, b, label, why="", qa=None, qb=None, block=None):
        if a == b:
            return
        if (a, qa or "") > (b, qb or ""):
            a, b, qa, qb = b, a, qb, qa
        lid = f"{kind}:{qa or a}:{qb or b}" + (f":{slug(label)}" if kind in ("person", "place") else "")
        out.setdefault(lid, {"id": lid, "kind": kind, "a": a, "b": b, "qa": qa, "qb": qb, "label": label,
                             "why": why[:600], "block": block})

    led = next((d for d in docs if d["id"] == "consistency"), None)
    if led:
        on = False
        for b in led["blocks"]:
            raw = b["_raw"]
            if raw["t"] == "h" and raw["level"] == 2:
                on = "crossing" in raw["text"].lower()
            if not on or raw["t"] != "table":
                continue
            for r in raw["rows"]:
                text = " ".join(plain(x) for x in r)
                ends = sorted({code_line[c] for c in re.findall(r"\b([A-Z]{2})(?=\d{2}\b|\b)", text) if c in code_line})
                label = plain(r[1]) if len(r) > 1 else plain(r[0])
                label = re.sub(r"\s*\(.*?\)\s*$", "", label)[:90]
                for i, x in enumerate(ends):
                    for y in ends[i + 1:]:
                        add("crossing", x, y, f"{plain(r[0])} {label}".strip(), text, block=b["id"])
    for kind, rows in (("person", people), ("place", places)):
        for p in rows:
            by = {}
            for qid in p["quests"]:
                by.setdefault(qline[qid], qid)
            ls = sorted(by)
            for i, x in enumerate(ls):
                for y in ls[i + 1:]:
                    add(kind, x, y, p["name"], f"{p['name']} is in {by[x]} and {by[y]}.", by[x], by[y])
    for q in quests:
        for m in sorted(set(re.findall(r"\b([A-Z]{2}\d{2})\b", q["_text"]))):
            if m in qline and qline[m] != q["line"]:
                add("reference", q["line"], qline[m], f"{q['id']} names {m}", "", q["id"], m)
    return sorted(out.values(), key=lambda e: e["id"])


# ---- the whole -----------------------------------------------------------------------------------------------

def summary(d: dict) -> str:
    """A line's card text: a plot's first paragraph under its first section (what the faction is), else the
    story's first paragraph; a status line is never the summary."""
    blocks = d["blocks"]
    if d["kind"] == "plot":
        first = next((i for i, b in enumerate(blocks) if b["_raw"]["t"] == "h" and b["_raw"]["level"] == 2), None)
        if first is not None:
            blocks = blocks[first:]
    return next((plain(b["_raw"]["text"])[:400] for b in blocks
                 if b["_raw"]["t"] == "p" and not STATUS.match(b["_raw"]["text"])), "")


def generate(root: Path = ROOT, out: Path = OUT) -> dict:
    version = sources_hash(root)
    built = built_records(root)
    docs = [build_doc(rel, (root / rel).read_text()) for rel in sources(root)
            if rel.suffix == ".md" and not rel.is_relative_to(PLAYTESTS)]
    quests = [q for d in docs for q in quests_of(d, built)]
    rquests, rdocs = record_quests(root, docs, built)
    have = {q["id"] for q in rquests}
    quests = [q for q in quests if q["id"] not in have] + rquests   # a record replaces its outline
    people, places = people_and_places(docs, quests)
    lines = []
    for d in docs:
        if d["kind"] in ("line", "plot"):
            qs = [q for q in quests if q["line"] == d["id"]]
            reviewed = any(re.match(r"^(\d+\.\s+)?read on paper", plain(b["_raw"]["text"]), re.I)
                           for b in d["blocks"] if b["_raw"]["t"] == "h")
            lines.append({"id": d["id"], "title": d["title"], "kind": d["kind"], "quests": [q["id"] for q in qs],
                          "readOnPaper": reviewed, "status": d["status"],
                          "summary": summary(d)})
    docs += rdocs
    catalog = {
        "version": version,
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "docs": [{"id": d["id"], "title": d["title"], "kind": d["kind"], "path": d["path"], "status": d["status"],
                  **({"line": d["line"]} if d.get("line") else {}),
                  "hash": hashlib.sha1("".join(b["h"] for b in d["blocks"]).encode()).hexdigest()[:10],
                  "words": sum(len(json.dumps(b["_raw"]).split()) for b in d["blocks"])} for d in docs],
        "lines": lines,
        "quests": [{k: v for k, v in q.items() if not k.startswith("_")} for q in quests],
        "people": people,
        "places": places,
        "links": links(docs, quests, people, places),
    }
    if out.exists():
        shutil.rmtree(out)
    (out / "data").mkdir(parents=True)
    for d in docs:
        body = {"id": d["id"], "title": d["title"], "kind": d["kind"], "path": d["path"],
                "blocks": [{k: v for k, v in b.items() if k != "_raw"} for b in d["blocks"]]}
        (out / "data" / f"doc-{d['id']}.json").write_text(json.dumps(body, ensure_ascii=False, separators=(",", ":")))
    (out / "data" / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, separators=(",", ":")))
    shutil.copy(PAGE, out / "index.html")
    return catalog


def record(path: Path = RECORD) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def check(root: Path = ROOT, path: Path = RECORD) -> str | None:
    """None when the published explorer is current; otherwise what to do."""
    rec, now = record(path), sources_hash(root)
    if rec.get("published_hash") == now:
        return None
    return (f"story explorer behind: the new world's story sources are at {now}, the published page at "
            f"{rec.get('published_hash')}. Regenerate and republish it ({rec.get('url', 'no url recorded')}): "
            "python -m tools.newworld.story_explorer build, publish out/story-explorer/ to that url, then "
            "python -m tools.newworld.story_explorer mark-published")


def files_map(out: Path = OUT) -> dict[str, str]:
    """The supporting files to publish beside index.html, as the Artifact tool's `files` map."""
    return {f"data/{p.name}": str(p) for p in sorted((out / "data").glob("*.json"))}


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "build"
    if cmd == "build":
        c = generate()
        print(f"story explorer {c['version']}: {len(c['docs'])} documents, {len(c['lines'])} lines, "
              f"{len(c['quests'])} quests, {len(c['people'])} people, {len(c['places'])} places, {len(c['links'])} links -> {OUT}")
        return 0
    if cmd == "files":
        print(json.dumps(files_map(), indent=1))
        return 0
    if cmd == "check":
        msg = check()
        print(msg or "story explorer current")
        return 1 if msg else 0
    if cmd == "mark-published":
        rec = record()
        rec["published_hash"] = sources_hash()
        rec["published"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        RECORD.write_text(json.dumps(rec, indent=2) + "\n")
        print(f"recorded {rec['published_hash']}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
