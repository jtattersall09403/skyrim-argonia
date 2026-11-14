"""What the stories need of a place (docs/design/place-studio.md, "What the stories need of a place").

The story panel is generated from the story sources each time it is asked for, so it is never behind the story:

- every line story under story/design/quests/lines/ (the main quest's plot, the faction lines, the province plan)
  lists, per place, the physical things its quests rely on in a "What each quest needs of its places" table; each
  row naming this place is a need, with the story's own words and a link to its file and line;
- the place's people (newworld/sources/people/<place>.json) are matched by name against the same stories and the
  cast roster: each mention is why a story uses that person;
- a story whose head carries `**Status: to be rewritten.**` still counts, each of its rows marked so; one whose
  status begins "replaced" is not read at all (its work has moved to the story that replaces it);
- an old-world story with a `-newworld` twin is not read.

The one thing kept by hand is the place's side: `newworld/sources/needs/<place>.json` holds each judgement of a need
from the player's side (what in the place files it rests on, how a player knows it, met or not, what the place has
instead, the sight test), keyed to the story rows it judges by their keys. A judgement whose rows no story still
has is shown as "placed for a story that has changed", with every thing and person placed for it, so the owner
decides in the studio; nothing is deleted. The owner's changes to what a need rests on come from the studio into
`<place>.changed.jsonl`; tools/newworld/needsdb.py loads the place's side into the database.

    python -m tools.places needs show <place>               each need in plain words, met, not met or not judged
    python -m tools.places needs open <place>               the story rows no judgement covers, with their keys
    python -m tools.places needs dismiss <place> <key> --why "..."     a row that names the place by mistake
    python -m tools.places needs changed [<place>]          the owner's changes: the stories to change to fit
    python -m tools.places needs check <place>              every rest and person exists in the place files
    python -m tools.places needs load                       the database's needs tables from the sources

A judgement: {seq, from: [story row keys], thing (the row it judged), line, rests, signs, placed?: [{person} |
{space, ref}], met, why, fit?, narrow?, near?, sight?, tier}. A new judgement copies a row's key from `needs open`.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = Path(os.environ.get("NEWWORLD_SOURCES") or ROOT / "newworld" / "sources")   # as the studio's server reads it
NEEDS = SOURCES / "needs"
PEOPLE = SOURCES / "people"
PLACES = ROOT / "newworld" / "places"
LINES = ROOT / "story" / "design" / "quests" / "lines"
ROSTER = ROOT / "story" / "design" / "quests" / "36-cast-roster.md"
EXPLORER = ROOT / "tools" / "newworld" / "story_explorer.json"
PLACE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,95}$")
CHANGES = ("removed", "moved", "renamed")
MAX_WHAT = 600
MAX_MENTIONS = 4

THING_COLS = ("the thing", "the thing needed", "need")
QUEST_COLS = ("quest", "case", "quests")
DOES_COLS = ("what happens there", "what the quest does there", "what the case does there")
KNOW_COLS = ("how the player knows it", "how the player knows what it is")
SECTION = re.compile(r"^#{2,3}\s.*needs of (its )?places", re.I)
HEADING = re.compile(r"^\*\*([^*]+)\*\*")
STATUS = re.compile(r"^\*\*Status:\s*([^*]+?)\.?\*\*\s*(.*)$")
SIGN_WORDS = {"look": "By its look", "label": "By the name the game shows", "beside": "By what stands in or by it",
              "person": "Told by a person"}
ROLE_WORDS = {"partner": "partner", "grown child": "grown child", "elder": "elder", "sibling": "sibling",
              "cousin": "cousin", "lodger": "lodger", "levy": "levy member"}
LINE_IDS = {"main-plot": "main"}   # a story file whose line is named otherwise
LEDGERS = ("consistency", "province-plan")   # lists of every name: a mention there says nothing of why one matters


def _json(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _jsonl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def source_path(pid: str, root: Path = NEEDS) -> Path:
    if not PLACE_ID.match(pid):
        raise ValueError("bad place id")
    return root / f"{pid}.json"


def read(pid: str, root: Path = NEEDS) -> dict:
    """The place's side: its judgements and its dismissed rows."""
    return _json(source_path(pid, root)) or {"place_id": pid, "needs": [], "dismissed": []}


def write(doc: dict, root: Path = NEEDS) -> None:
    p = source_path(doc["place_id"], root)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(f".{p.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(p)


# ---- the story sources -------------------------------------------------------------------------------------------

def line_id(path: Path) -> str:
    stem = path.stem
    return LINE_IDS.get(stem, stem[: -len("-newworld")] if stem.endswith("-newworld") else stem)


def status(path: Path) -> dict | None:
    """A story's status from its head (`**Status: to be rewritten.** what is untrue...`), or None."""
    for ln in path.read_text(encoding="utf-8").splitlines()[:40]:
        m = STATUS.match(ln.strip())
        if m:
            return {"status": m.group(1).strip().lower(), "says": m.group(2).strip()}
    return None


def stories(lines_dir: Path = LINES) -> list[tuple[Path, dict | None]]:
    """Every story the panel reads, with its status: not an old-world twin, not replaced."""
    files = sorted(lines_dir.glob("*.md"))
    stems = {p.stem for p in files}
    out = []
    for p in files:
        if f"{p.stem}-newworld" in stems:
            continue
        st = status(p)
        if st and st["status"].startswith("replaced"):
            continue
        out.append((p, st))
    return out


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _col(header: list[str], names: tuple[str, ...]) -> int | None:
    low = [h.lower().strip("* ") for h in header]
    return next((i for i, h in enumerate(low) if h in names), None)


def _line_ids(cell: str, default: str) -> list[str]:
    out = []
    for part in re.split(r",| and ", cell or ""):
        w = re.sub(r"^the\s+", "", part.strip().lower()).replace(" ", "-")
        if w:
            out.append(w)
    return out or [default]


def row_key(path: Path, line: str, thing: str) -> str:
    return hashlib.sha1(f"{path.name}|{line}|{thing}".encode()).hexdigest()[:10]


def read_tables(path: Path, names: set[str]) -> list[dict]:
    """Every needs row of one story for a place called by one of `names` (lower case)."""
    rows, in_section, heading = [], False, None
    lines = path.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("#"):
            in_section = bool(SECTION.match(ln)) or ln.lower().startswith("## needs of places")
            heading = None
        elif in_section and HEADING.match(ln):
            heading = HEADING.match(ln).group(1).strip().rstrip(".")
        elif in_section and ln.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1]):
            header = _cells(ln)
            ti = _col(header, THING_COLS)
            if ti is None:
                i += 1
                continue
            pi, qi, di, ki = (_col(header, ("place",)), _col(header, QUEST_COLS), _col(header, DOES_COLS),
                              _col(header, KNOW_COLS))
            li = _col(header, ("line",))
            here = {n.strip().lower() for n in re.split(r",| and ", heading or "")}
            j = i + 2
            while j < len(lines) and lines[j].startswith("|"):
                c = _cells(lines[j])
                c += [""] * (len(header) - len(c))
                place = c[pi].lower() if pi is not None else None
                if (place in names) if pi is not None else bool(here & names):
                    for lid in _line_ids(c[li] if li is not None else "", line_id(path)):
                        rows.append({"story": f"{_rel(path)}:{j + 1}", "line": lid, "thing": c[ti],
                                     "quests": c[qi] if qi is not None else "", "does": c[di] if di is not None else "",
                                     "know": c[ki] if ki is not None else "", "key": row_key(path, lid, c[ti])})
                j += 1
            i = j
            continue
        i += 1
    return rows


def place_names(pid: str) -> set[str]:
    """The place's name and aliases in the database, lower case; the id itself if the database cannot be read."""
    try:
        from tools.argonia_world import db
        w = db.open(ROOT / "newworld")
        row = w.get("place", pid)
        names = {row.name.lower()} if row else set()
        names |= {r.alias.lower() for r in w.rows("place_alias", place_id=pid)}
        return names or {pid.lower()}
    except Exception:   # noqa: BLE001 - a scratch root without the database still reads by id
        return {pid.lower(), pid.replace("-", " ").lower()}


def story_rows(pid: str, lines_dir: Path = LINES, names: set[str] | None = None) -> list[dict]:
    """Every current story row for the place, each with its story's status."""
    names = names or place_names(pid)
    out = []
    for p, st in stories(lines_dir):
        for r in read_tables(p, names):
            out.append(r | {"rewrite": bool(st and st["status"].startswith("to be rewritten")),
                            "doc": p.stem})
    return out


def _plain(s: str) -> str:
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    s = re.sub(r"`([^`]+)`", r"\1", s)
    return re.sub(r"\*+", "", s).strip()


def mentions(name: str, files: list[tuple[Path, dict | None]]) -> list[dict]:
    """Where the stories name a person: the table row or the sentence, with its file and line."""
    pat = re.compile(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])")
    out = []
    for p, st in files:
        for n, ln in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if not pat.search(ln):
                continue
            if ln.lstrip().startswith("|"):
                text = " | ".join(c for c in (_plain(x) for x in _cells(ln)) if c)
            else:
                text = next((s for s in re.split(r"(?<=[.!?])\s+", _plain(ln.strip(" -"))) if pat.search(s)), _plain(ln))
            out.append({"story": f"{_rel(p)}:{n}", "line": "roster" if p.name == ROSTER.name else line_id(p),
                        "doc": p.stem, "for": text[:400],
                        "rewrite": bool(st and st["status"].startswith("to be rewritten"))})
    return out


# ---- the owner's changes (the studio) ------------------------------------------------------------------------------

@contextmanager
def _locked(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    fd = os.open(root, os.O_RDONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def changes_path(pid: str, root: Path = NEEDS) -> Path:
    if not PLACE_ID.match(pid):
        raise ValueError("bad place id")
    return root / f"{pid}.changed.jsonl"


def changes(pid: str, root: Path = NEEDS) -> list[dict]:
    return _jsonl(changes_path(pid, root))


def record_change(pid: str, body: dict, root: Path = NEEDS) -> dict:
    """The owner carried on past a warning: the change stands as any other edit, and the need (or the person a
    story uses) is marked changed by the owner, so the story is changed to fit the place."""
    doc = read(pid, root)
    if body.get("change") not in CHANGES:
        raise ValueError(f"change must be one of {', '.join(CHANGES)}")
    what = str(body.get("what") or "").strip()[:MAX_WHAT]
    if not what:
        raise ValueError("say what changed")
    row: dict = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "change": body["change"],
                 "what": what, "tier": "OWNER_STATED"}
    if body.get("need") is not None:
        if not any(n["seq"] == body["need"] for n in doc.get("needs", [])):
            raise ValueError("no such need")
        row["need"] = int(body["need"])
    elif body.get("person"):
        row["person"] = str(body["person"])[:96]
    else:
        raise ValueError("name the need or the person")
    if body.get("save"):
        row["save"] = str(body["save"])[:96]
    with _locked(root):
        p = changes_path(pid, root)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
    return row


# ---- plain words ---------------------------------------------------------------------------------------------------

def lines_table(root: Path = NEEDS) -> dict:
    return {r["id"]: r for r in (_json(root / "lines.json") or {}).get("lines", [])}


def line_words(lid: str, lines: dict) -> str:
    if lid == "roster":
        return "the cast roster"
    r = lines.get(lid)
    return f"{r['plain']} ({r['name']})" if r else lid.replace("-", " ")


def who_words(pid: str, people_root: Path = PEOPLE) -> dict:
    """Each person of the place in one plain line: their trade and their household, as a player would learn them."""
    doc = _json(people_root / f"{pid}.json") or {"people": [], "households": []}
    heads = {p["household"]["id"]: p["name"] for p in doc["people"] if (p.get("household") or {}).get("role") == "head"}
    out = {}
    for p in doc["people"]:
        hh = p.get("household") or {}
        role = hh.get("role")
        if role == "head":
            home = "heads a household in the town"
        elif hh.get("id") in heads:
            home = f"{ROLE_WORDS.get(role, role or 'member')} in {heads[hh['id']]}'s household"
        else:
            home = "of no household here"
        sex = {"male": "man", "female": "woman"}.get(p.get("sex"), "person")
        race = "Argonian" if p.get("race") == "ArgonianRace" else (p.get("race") or "").replace("Race", "")
        art = "an" if race[:1] in "AEIOU" else "a"
        out[p["id"]] = {"name": p["name"], "who": f"{p['name']}, {art} {race} {sex}: {p['trade']}; {home}.",
                        "status": p.get("status", "alive")}
    return out


def know_sentence(signs: list[dict], story_know: str = "") -> str:
    if signs:
        return " ".join(f"{SIGN_WORDS[s['sign']]}: {s['detail'].rstrip('.')}." for s in signs)
    if story_know:
        return f"The story says: {story_know.rstrip('.')}. Not yet judged in the place."
    return "The story does not yet say how a player would know it."


def explorer_url() -> str | None:
    return (_json(EXPLORER) or {}).get("url")


def _link(src: dict, url: str | None, lines: dict) -> dict:
    return {"story": src["story"], "line": line_words(src["line"], lines), "rewrite": src["rewrite"],
            "url": f"{url}#d-{re.sub(r'[^a-z0-9]+', '-', src['doc'].lower()).strip('-')}" if url else None}


def _placed_things(pid: str, places: Path) -> dict[int, list[dict]]:
    """Every thing in the place files that carries the seq of the need it was placed for."""
    out: dict[int, list[dict]] = {}
    sp_root = places / pid / "spaces"
    if not sp_root.exists():
        return out
    for sdir in sorted(sp_root.iterdir()):
        for r in _jsonl(sdir / "refs.jsonl"):
            if r.get("need") is not None:
                out.setdefault(int(r["need"]), []).append({"space": sdir.name, "ref": r["id"], "why": r.get("why", ""),
                                                           "name": r.get("name") or r.get("why", "").split(",")[0]})
    return out


def compose(pid: str, root: Path = NEEDS, people_root: Path = PEOPLE, lines_dir: Path = LINES,
            names: set[str] | None = None, places: Path = PLACES, roster: Path = ROSTER) -> dict:
    """The panel's content, generated: the stories' needs of the place with the place's judgement of each, the
    people the stories use and why, and what stands placed for a story that no longer needs it."""
    doc, lines, who, url = read(pid, root), lines_table(root), who_words(pid, people_root), explorer_url()
    gone = {d["key"] for d in doc.get("dismissed", [])}
    rows = [r for r in story_rows(pid, lines_dir, names) if r["key"] not in gone]
    by_key: dict[str, list[dict]] = {}
    for r in rows:
        by_key.setdefault(r["key"], []).append(r)
    ch = changes(pid, root)
    needs, used, changed = [], set(), []
    placed = _placed_things(pid, places)
    for j in doc.get("needs", []):
        srcs = [r for k in j.get("from", []) for r in by_key.get(k, [])]
        if not srcs:
            things = [{"kind": "thing", **t} for t in placed.get(j["seq"], [])]
            r = j.get("rests") or {}
            ppl = [x for x in [r.get("person")] + [s.get("person") for s in j.get("signs", [])]
                   + [p.get("person") for p in j.get("placed", [])] if x]
            things += [{"kind": "person", "person": x, "name": who.get(x, {}).get("name", x)}
                       for x in dict.fromkeys(ppl)]
            changed.append({"seq": j["seq"], "was_for": j.get("thing", ""), "line": line_words(j.get("line", ""), lines),
                            "placed": things})
            continue
        used |= {r["key"] for r in srcs}
        first = srcs[0]
        needs.append({
            "seq": j["seq"], "key": first["key"], "thing": first["thing"], "line": line_words(first["line"], lines),
            "quests": "; ".join(dict.fromkeys(r["quests"] for r in srcs if r["quests"])),
            "does": first["does"] or first["thing"], "rewrite": any(r["rewrite"] for r in srcs),
            "sources": [_link(r, url, lines) for r in srcs], "judged": True,
            "know": know_sentence(j.get("signs", []), first["know"]),
            "signs": [{"sign": s["sign"], "words": SIGN_WORDS[s["sign"]], "detail": s["detail"],
                       "person": s.get("person")} for s in j.get("signs", [])],
            "rests": j.get("rests"), "near": j.get("near"), "met": bool(j["met"]), "why": j["why"], "fit": j.get("fit"),
            "narrow": j.get("narrow"), "sight": j.get("sight"),
            "changed": [c for c in ch if c.get("need") == j["seq"]]})
    for r in rows:
        if r["key"] in used:
            continue
        used.add(r["key"])
        needs.append({"seq": None, "key": r["key"], "thing": r["thing"], "line": line_words(r["line"], lines),
                      "quests": r["quests"], "does": r["does"] or r["thing"], "rewrite": r["rewrite"],
                      "sources": [_link(r, url, lines)], "judged": False, "know": know_sentence([], r["know"]),
                      "signs": [], "rests": None, "near": None, "met": False,
                      "why": "Not yet judged: nobody has looked for it in the place from the player's side.",
                      "fit": None, "narrow": None, "sight": None, "changed": []})
    files = [(p, st) for p, st in stories(lines_dir) if p.stem not in LEDGERS]
    files += [(roster, status(roster))] if roster.exists() else []
    people = {}
    for p_id, w in who.items():
        ms = mentions(w["name"], files)
        people[p_id] = {"who": w["who"], "name": w["name"], "uses": [
            {"for": m["for"], "line": line_words(m["line"], lines), "rewrite": m["rewrite"],
             "sources": [_link(m, url, lines)],
             "changed": [c for c in ch if c.get("person") == p_id]} for m in ms[:MAX_MENTIONS]]}
    return {"place_id": pid, "needs": needs, "people": people, "changed_story": changed}


def payload(pid: str, root: Path = NEEDS, people_root: Path = PEOPLE, places: Path = PLACES,
            lines_dir: Path = LINES) -> dict:
    """GET /api/place/<id>/needs: generated from the story sources at each request (compose)."""
    return compose(pid, root, people_root, lines_dir, places=places)


# ---- checks and listings -------------------------------------------------------------------------------------------

def _place_refs(pid: str, places: Path = PLACES) -> dict[str, set[str]]:
    out = {}
    for sdir in (places / pid / "spaces").iterdir():
        out[sdir.name] = {i for r in _jsonl(sdir / "refs.jsonl") for i in (r["id"], r.get("src") or r["id"])}
    return out


def check(pid: str, root: Path = NEEDS, places: Path = PLACES, people_root: Path = PEOPLE) -> list[str]:
    """Every judgement's rest and person exists in the place files; a met need rests on something and carries a way
    the player knows it; an unmet one says what the place has instead."""
    doc, errs = read(pid, root), []
    refs = _place_refs(pid, places)
    people = {p["id"] for p in (_json(people_root / f"{pid}.json") or {"people": []})["people"]}
    for n in doc.get("needs", []):
        tag = f"need {n['seq']} ({n.get('thing', '')[:40]})"
        r = n.get("rests") or {}
        if not n.get("from"):
            errs.append(f"{tag}: judges no story row (from)")
        if r.get("space") and r["space"] not in refs:
            errs.append(f"{tag}: no space {r['space']}")
        if r.get("ref") and r.get("space") in refs and r["ref"] not in refs[r["space"]]:
            errs.append(f"{tag}: no ref {r['ref']} in {r['space']}")
        if r.get("person") and r["person"] not in people:
            errs.append(f"{tag}: no person {r['person']}")
        if n["met"] and not (r.get("space") or r.get("person")):
            errs.append(f"{tag}: met, but rests on nothing")
        if n["met"] and not n.get("signs"):
            errs.append(f"{tag}: met, but no way a player knows it")
        if not n["met"] and not n.get("fit"):
            errs.append(f"{tag}: not met, and no fit says what the place has instead")
        for s in n.get("signs", []):
            if s["sign"] not in SIGN_WORDS:
                errs.append(f"{tag}: unknown sign {s['sign']}")
            if s.get("person") and s["person"] not in people:
                errs.append(f"{tag}: no person {s['person']}")
        for x in n.get("placed", []):
            if x.get("person") and x["person"] not in people:
                errs.append(f"{tag}: no person {x['person']}")
    seqs = [n["seq"] for n in doc.get("needs", [])]
    if len(seqs) != len(set(seqs)):
        errs.append("two judgements share a seq")
    return errs


def show(pid: str, root: Path = NEEDS) -> str:
    d = payload(pid, root)
    out = []
    for title, pick in (("Met", lambda n: n["met"]), ("Not met", lambda n: n["judged"] and not n["met"]),
                        ("Not yet judged", lambda n: not n["judged"])):
        rows = [n for n in d["needs"] if pick(n)]
        out.append(f"{title} ({len(rows)})")
        for n in rows:
            mark = " [its story is to be rewritten]" if n["rewrite"] else ""
            out.append(f"  {n['seq'] if n['seq'] is not None else n['key']}. {n['thing']} - {n['line']}, "
                       f"{n['quests']}: {n['does']}{mark}")
            out.append(f"     from {', '.join(s['story'] for s in n['sources'])}")
            out.append(f"     how a player knows it: {n['know']}")
            out.append(f"     {n['why']}")
            if n.get("fit"):
                out.append(f"     instead: {n['fit']}")
    used = [(p, u) for p in d["people"].values() for u in p["uses"]]
    out.append(f"People the stories name ({len({p['name'] for p, _ in used})})")
    out += [f"  {p['name']}: {u['for']} ({u['sources'][0]['story']}{', to be rewritten' if u['rewrite'] else ''})"
            for p, u in used]
    out.append(f"Placed for a story that has changed ({len(d['changed_story'])})")
    for c in d["changed_story"]:
        out.append(f"  was for: {c['was_for']} ({c['line']})")
        out += [f"     {t.get('name') or t.get('ref') or t.get('person')}" for t in c["placed"]]
    return "\n".join(out)


def open_rows(pid: str, root: Path = NEEDS) -> list[dict]:
    return [n for n in payload(pid, root)["needs"] if not n["judged"]]


def dismiss(pid: str, key: str, why: str, root: Path = NEEDS) -> None:
    if not any(n["key"] == key for n in open_rows(pid, root)):
        raise ValueError(f"no open story row {key} for {pid}")
    doc = read(pid, root)
    doc.setdefault("dismissed", []).append({"key": key, "why": why})
    write(doc, root)


def changed_listing(pids: list[str], root: Path = NEEDS) -> str:
    out = []
    for pid in pids:
        by_seq = {n["seq"]: n for n in read(pid, root).get("needs", [])}
        for c in changes(pid, root):
            if c.get("need") is not None:
                n = by_seq.get(c["need"], {})
                about = f"need {c['need']}: {n.get('thing', '?')} (story rows {', '.join(n.get('from', []))})"
            else:
                about = f"person {c['person']}"
            out.append(f"{pid} {c['at']} {c['change']} by the owner ({c.get('tier', 'OWNER_STATED')}) - {about}\n"
                       f"    {c['what']}" + (f"\n    in save {c['save']}" if c.get("save") else ""))
    return "\n".join(out) if out else "No owner changes to anything a story needs."


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places needs", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="verb", required=True)
    for v in ("open", "show", "check"):
        sub.add_parser(v).add_argument("place")
    d = sub.add_parser("dismiss")
    d.add_argument("place")
    d.add_argument("key")
    d.add_argument("--why", required=True)
    sub.add_parser("changed").add_argument("place", nargs="?")
    sub.add_parser("load")
    a = ap.parse_args(argv)
    if a.verb == "open":
        rows = open_rows(a.place)
        for r in rows:
            print(f"{r['key']}  {r['thing']}\n            {r['quests']} | {r['does']}\n"
                  f"            {', '.join(s['story'] for s in r['sources'])}")
        print(f"{len(rows)} story row(s) for {a.place} not yet judged: judge each in {source_path(a.place)} "
              f"(a judgement's `from` holds the key), or dismiss it with a reason")
    elif a.verb == "dismiss":
        dismiss(a.place, a.key, a.why)
    elif a.verb == "show":
        print(show(a.place))
    elif a.verb == "check":
        errs = check(a.place)
        print("\n".join(errs) or f"{a.place}: every judgement rests on what the place files hold")
        return 1 if errs else 0
    elif a.verb == "changed":
        from tools.newworld.needsdb import places as all_places
        print(changed_listing([a.place] if a.place else all_places(NEEDS)))
    elif a.verb == "load":
        from tools.newworld import needsdb
        w = needsdb.reload()
        print({t: len(w.rows(t)) for t in needsdb.TABLES})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
