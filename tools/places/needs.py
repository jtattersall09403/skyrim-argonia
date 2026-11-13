"""What the stories need of a place (docs/design/place-studio.md, "What the stories need of a place").

Each line story lists, per place, the physical things its quests rely on ("What each quest needs of its places").
Those rows are loaded onto the place as needs, each judged from the player's side: met only when the thing exists in
the place files and a player would know it for what it is (its look, the game's own label, what stands in or by it,
a named person who tells them). The source is `newworld/sources/needs/<place_id>.json`; the owner's changes to what
a need rests on come from the studio into `<place_id>.changed.jsonl`; tools/newworld/needsdb.py loads both into the
database.

    python -m tools.places needs propose <place>             read every line story's needs tables for the place
                                                             and list the rows not yet confirmed or dismissed
    python -m tools.places needs confirm <place> <key> [--into <seq>]
                                                             a proposal becomes a need (or one more source of need
                                                             <seq>); its judgement is then written by hand
    python -m tools.places needs dismiss <place> <key> --why "..."
    python -m tools.places needs show <place>                each need in plain words, met or not met
    python -m tools.places needs changed [<place>]           the owner's changes to what needs rest on: the stories
                                                             to change to fit the place
    python -m tools.places needs check <place>               every rest and person exists in the place files
    python -m tools.places needs load                        the database's needs tables from the sources

A story's needs table is any markdown table under a "needs of (its) places" heading whose header has a thing column
("The thing", "The thing needed", "Need"); its place is the table's Place column or the bold place name heading the
table. Nothing outside such a table is read: anything else is entered by hand.
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
PLACE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,95}$")
CHANGES = ("removed", "moved", "renamed")
MAX_WHAT = 600

THING_COLS = ("the thing", "the thing needed", "need")
QUEST_COLS = ("quest", "case", "quests")
DOES_COLS = ("what happens there", "what the quest does there", "what the case does there")
KNOW_COLS = ("how the player knows it", "how the player knows what it is")
SECTION = re.compile(r"^#{2,3}\s.*needs of (its )?places", re.I)
HEADING = re.compile(r"^\*\*([^*]+)\*\*")
SIGN_WORDS = {"look": "By its look", "label": "By the name the game shows", "beside": "By what stands in or by it",
              "person": "Told by a person"}
KEEP_WORDS = {"reachable": "must stand where the player can speak to them",
              "alive": "must stay alive",
              "reachable and alive": "must stay alive and stand where the player can speak to them"}
ROLE_WORDS = {"partner": "partner", "grown child": "grown child", "elder": "elder", "sibling": "sibling",
              "cousin": "cousin", "lodger": "lodger", "levy": "levy member"}


def _json(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def source_path(pid: str, root: Path = NEEDS) -> Path:
    if not PLACE_ID.match(pid):
        raise ValueError("bad place id")
    return root / f"{pid}.json"


def read(pid: str, root: Path = NEEDS) -> dict:
    return _json(source_path(pid, root)) or {"place_id": pid, "needs": [], "people": [], "proposed": [],
                                             "dismissed": []}


def write(doc: dict, root: Path = NEEDS) -> None:
    p = source_path(doc["place_id"], root)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(f".{p.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(p)


# ---- reading the line stories' tables ------------------------------------------------------------------------------

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


def read_tables(path: Path, names: set[str]) -> list[dict]:
    """Every needs row of one line story for a place called by one of `names` (lower case)."""
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
                    for line_id in _line_ids(c[li] if li is not None else "", path.stem):
                        row = {"story": f"{path.relative_to(ROOT)}:{j + 1}", "line": line_id, "thing": c[ti],
                               "quests": c[qi] if qi is not None else "", "does": c[di] if di is not None else "",
                               "know": c[ki] if ki is not None else ""}
                        row["key"] = hashlib.sha1(f"{path.name}|{line_id}|{c[ti]}".encode()).hexdigest()[:10]
                        rows.append(row)
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


def propose(pid: str, root: Path = NEEDS, lines_dir: Path = LINES, names: set[str] | None = None) -> list[dict]:
    """Every story row for the place not yet confirmed (a need's `from`) or dismissed; kept as the source's
    `proposed` list, which is rewritten whole each time."""
    names = names or place_names(pid)
    doc = read(pid, root)
    taken = {k for n in doc.get("needs", []) for k in n.get("from", [])} | {d["key"] for d in doc.get("dismissed", [])}
    rows = [r for p in sorted(lines_dir.glob("*.md")) for r in read_tables(p, names)]
    doc["proposed"] = [r for r in rows if r["key"] not in taken]
    write(doc, root)
    return doc["proposed"]


def confirm(pid: str, key: str, into: int | None = None, root: Path = NEEDS) -> dict:
    doc = read(pid, root)
    prop = next((p for p in doc.get("proposed", []) if p["key"] == key), None)
    if prop is None:
        raise ValueError(f"no proposal {key} for {pid}: run `needs propose {pid}` first")
    if into is not None:
        need = next((n for n in doc["needs"] if n["seq"] == into), None)
        if need is None:
            raise ValueError(f"{pid} has no need {into}")
        need.setdefault("from", []).append(key)
        need.setdefault("stories", []).append(prop["story"])
    else:
        need = {"seq": max([n["seq"] for n in doc["needs"]], default=-1) + 1, "thing": prop["thing"],
                "line": prop["line"], "quests": prop["quests"], "does": prop["does"] or prop["thing"],
                "firmness": "first-draft", "signs": [], "stories": [prop["story"]], "from": [key],
                "rests": None, "met": False, "why": "not met: not yet judged from the player's side",
                "story_know": prop["know"], "tier": "AGENT_INVENTED"}
        doc["needs"].append(need)
    doc["proposed"] = [p for p in doc["proposed"] if p["key"] != key]
    write(doc, root)
    return need


def dismiss(pid: str, key: str, why: str, root: Path = NEEDS) -> None:
    doc = read(pid, root)
    if not any(p["key"] == key for p in doc.get("proposed", [])):
        raise ValueError(f"no proposal {key} for {pid}")
    doc.setdefault("dismissed", []).append({"key": key, "why": why})
    doc["proposed"] = [p for p in doc["proposed"] if p["key"] != key]
    write(doc, root)


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
    p = changes_path(pid, root)
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


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
        if not any(u["person"] == body["person"] for u in doc.get("people", [])):
            raise ValueError("no story uses that person")
        row["person"] = str(body["person"])
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


def line_words(line_id: str, lines: dict) -> str:
    r = lines.get(line_id)
    return f"{r['plain']} ({r['name']})" if r else line_id


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


def know_sentence(n: dict) -> str:
    signs = n.get("signs") or []
    if not signs:
        return "The story does not yet say how a player would know it."
    return " ".join(f"{SIGN_WORDS[s['sign']]}: {s['detail'].rstrip('.')}." for s in signs)


def payload(pid: str, root: Path = NEEDS, people_root: Path = PEOPLE) -> dict:
    """GET /api/place/<id>/needs: every need and every story use of a person, in plain words."""
    doc, lines, who = read(pid, root), lines_table(root), who_words(pid, people_root)
    ch = changes(pid, root)
    needs = []
    for n in doc.get("needs", []):
        needs.append({
            "seq": n["seq"], "thing": n["thing"], "line": line_words(n["line"], lines), "quests": n["quests"],
            "does": n["does"], "first_draft": n["firmness"] == "first-draft", "know": know_sentence(n),
            "signs": [{"sign": s["sign"], "words": SIGN_WORDS[s["sign"]], "detail": s["detail"],
                       "person": s.get("person")} for s in n.get("signs", [])],
            "rests": n.get("rests"), "met": bool(n["met"]), "why": n["why"], "fit": n.get("fit"),
            "narrow": n.get("narrow"), "sight": n.get("sight"),
            "changed": [c for c in ch if c.get("need") == n["seq"]]})
    people = {pid_: {"who": w["who"], "name": w["name"], "uses": []} for pid_, w in who.items()}
    for u in doc.get("people", []):
        people.setdefault(u["person"], {"who": u["person"], "name": u["person"], "uses": []})["uses"].append({
            "line": line_words(u["line"], lines), "quests": u["quests"], "for": u["for"],
            "keep": KEEP_WORDS[u["keep"]], "first_draft": u["firmness"] == "first-draft",
            "changed": [c for c in ch if c.get("person") == u["person"]]})
    return {"place_id": pid, "needs": needs, "people": people}


# ---- checks and listings -------------------------------------------------------------------------------------------

def _place_refs(pid: str, places: Path = PLACES) -> dict[str, set[str]]:
    out = {}
    for sdir in (places / pid / "spaces").iterdir():
        ids = set()
        p = sdir / "refs.jsonl"
        if p.exists():
            for x in p.read_text(encoding="utf-8").splitlines():
                if x.strip():
                    r = json.loads(x)
                    ids |= {r["id"], r.get("src") or r["id"]}
        out[sdir.name] = ids
    return out


def check(pid: str, root: Path = NEEDS, places: Path = PLACES, people_root: Path = PEOPLE) -> list[str]:
    """Every need's rest and every person exists in the place files; every need is judged; a met need rests on
    something and carries a way the player knows it."""
    doc, errs = read(pid, root), []
    refs = _place_refs(pid, places)
    people = {p["id"] for p in (_json(people_root / f"{pid}.json") or {"people": []})["people"]}
    lines = lines_table(root)
    for n in doc.get("needs", []):
        tag = f"need {n['seq']} ({n['thing'][:40]})"
        r = n.get("rests") or {}
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
        if n["line"] not in lines:
            errs.append(f"{tag}: unknown line {n['line']}")
        for s in n.get("signs", []):
            if s["sign"] not in SIGN_WORDS:
                errs.append(f"{tag}: unknown sign {s['sign']}")
            if s.get("person") and s["person"] not in people:
                errs.append(f"{tag}: no person {s['person']}")
    for u in doc.get("people", []):
        if u["person"] not in people:
            errs.append(f"person use {u['seq']}: no person {u['person']}")
        if u["keep"] not in KEEP_WORDS:
            errs.append(f"person use {u['seq']}: keep must be one of {', '.join(KEEP_WORDS)}")
    return errs


def show(pid: str, root: Path = NEEDS) -> str:
    d = payload(pid, root)
    out = []
    for met in (True, False):
        rows = [n for n in d["needs"] if n["met"] == met]
        out.append(f"{'Met' if met else 'Not met'} ({len(rows)})")
        for n in rows:
            out.append(f"  {n['seq']}. {n['thing']} - {n['line']}, {n['quests']}: {n['does']}")
            out.append(f"     how a player knows it: {n['know']}")
            out.append(f"     {n['why']}")
            if n.get("fit"):
                out.append(f"     instead: {n['fit']}")
            if n.get("narrow"):
                out.append(f"     narrow addition: {n['narrow']}")
            if n.get("sight"):
                out.append(f"     sight test: {n['sight']['result']} ({n['sight'].get('said', '')})")
    used = [(p, u) for p in d["people"].values() for u in p["uses"]]
    out.append(f"People the stories use ({len(used)})")
    out += [f"  {p['who']} {u['line']}, {u['quests']}: {u['for']} ({u['keep']})" for p, u in used]
    return "\n".join(out)


def changed_listing(pids: list[str], root: Path = NEEDS) -> str:
    out = []
    for pid in pids:
        doc = read(pid, root)
        by_seq = {n["seq"]: n for n in doc.get("needs", [])}
        uses = {u["person"]: u for u in doc.get("people", [])}
        lines = lines_table(root)
        for c in changes(pid, root):
            if c.get("need") is not None:
                n = by_seq.get(c["need"], {})
                about = (f"need {c['need']}: {n.get('thing', '?')} ({line_words(n.get('line', '?'), lines)}, "
                         f"{n.get('quests', '')}; {', '.join(n.get('stories', []))})")
            else:
                u = uses.get(c["person"], {})
                about = (f"person {c['person']} ({line_words(u.get('line', '?'), lines)}, {u.get('quests', '')}: "
                         f"{u.get('for', '')}; {u.get('story', '')})")
            out.append(f"{pid} {c['at']} {c['change']} by the owner ({c.get('tier', 'OWNER_STATED')}) - {about}\n"
                       f"    {c['what']}" + (f"\n    in save {c['save']}" if c.get("save") else ""))
    return "\n".join(out) if out else "No owner changes to anything a story needs."


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places needs", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="verb", required=True)
    for v in ("propose", "show", "check"):
        sub.add_parser(v).add_argument("place")
    c = sub.add_parser("confirm")
    c.add_argument("place")
    c.add_argument("key")
    c.add_argument("--into", type=int)
    d = sub.add_parser("dismiss")
    d.add_argument("place")
    d.add_argument("key")
    d.add_argument("--why", required=True)
    sub.add_parser("changed").add_argument("place", nargs="?")
    sub.add_parser("load")
    a = ap.parse_args(argv)
    if a.verb == "propose":
        rows = propose(a.place)
        for r in rows:
            print(f"{r['key']}  {r['line']:<12} {r['thing']}\n            {r['quests']} | {r['does']} | "
                  f"knows: {r['know'] or '(the story does not say)'}\n            {r['story']}")
        print(f"{len(rows)} proposal(s) for {a.place}; confirm each with `needs confirm {a.place} <key> [--into <seq>]`"
              f" or dismiss it with a reason")
    elif a.verb == "confirm":
        n = confirm(a.place, a.key, a.into)
        print(f"need {n['seq']}: {n['thing']}; now judge it from the player's side in {source_path(a.place)}")
    elif a.verb == "dismiss":
        dismiss(a.place, a.key, a.why)
    elif a.verb == "show":
        print(show(a.place))
    elif a.verb == "check":
        errs = check(a.place)
        print("\n".join(errs) or f"{a.place}: every need is judged and rests on what the place files hold")
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
