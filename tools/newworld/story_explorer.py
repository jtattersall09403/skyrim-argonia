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

ROOT = Path(__file__).resolve().parents[2]
LINES = Path("story/design/quests/lines")
WORLD = Path("story/design/world")
WORLD_FILES = ("index.md", "province.md", "people.md")
PAGE = Path(__file__).with_name("story_explorer_page.html")
RECORD = Path(__file__).with_name("story_explorer.json")
OUT = ROOT / "out" / "story-explorer"
PLUGIN_QUESTS = Path("plugin/Argonia/Quests")

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
    return [p.relative_to(root) for p in out]


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
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    s = html.escape(s, quote=False)
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
            if any(ARC_QUEST.match(x) for x in items):  # a list of quests: one block each, so each is its own quest
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
        return {"t": "list", "ordered": b["ordered"], "items": [inline(x) for x in b["items"]]}
    if b["t"] == "table":
        return {"t": "table", "head": [inline(x) for x in b["head"]], "rows": [[inline(x) for x in r] for r in b["rows"]]}
    return {"t": "code", "lang": b["lang"], "text": b["text"]}


# ---- documents, sections, quests -----------------------------------------------------------------------------

def doc_kind(rel: Path) -> str:
    if rel.parent == WORLD / "regions":
        return "region"
    if rel.parent == WORLD:
        return "world"
    if rel.stem == "main-plot":
        return "plot"
    if rel.stem in ("consistency", "province-plan"):
        return "ledger"
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
    return {"id": did, "path": str(rel), "kind": doc_kind(rel), "title": title, "blocks": out, "status": status}


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

def generate(root: Path = ROOT, out: Path = OUT) -> dict:
    version = sources_hash(root)
    built = built_records(root)
    docs = [build_doc(rel, (root / rel).read_text()) for rel in sources(root)]
    quests = [q for d in docs for q in quests_of(d, built)]
    people, places = people_and_places(docs, quests)
    lines = []
    for d in docs:
        if d["kind"] in ("line", "plot"):
            qs = [q for q in quests if q["line"] == d["id"]]
            reviewed = any(re.match(r"^(\d+\.\s+)?read on paper", plain(b["_raw"]["text"]), re.I)
                           for b in d["blocks"] if b["_raw"]["t"] == "h")
            lines.append({"id": d["id"], "title": d["title"], "kind": d["kind"], "quests": [q["id"] for q in qs],
                          "readOnPaper": reviewed, "status": d["status"],
                          "summary": next((plain(b["_raw"]["text"])[:400] for b in d["blocks"] if b["_raw"]["t"] == "p"), "")})
    catalog = {
        "version": version,
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "docs": [{"id": d["id"], "title": d["title"], "kind": d["kind"], "path": d["path"], "status": d["status"],
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
