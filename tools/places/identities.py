"""Light identities of a place's people (nw-03, Stocking: light identities come first): a name, a household, a
trade, a wealth band and a line or two of backstory per person. They are world facts, kept in the new world's
database source `newworld/sources/people/<place>.json` (tables person, household, person_note; loaded by
tools/newworld/stockdb.py), one person per person id of the place's people.jsonl, which keeps only placement. The
drafter writes each person's name onto its placement row.

    python -m tools.places identities check helstrom

read() gives each person as {id, name, household: {id, role}, trade, wealth: W1..W5, backstory, cites: [...]}
(the backstory note and its cites). The check proves:
every person has one row and every row a person; names unique in the place and in the new world (never a person's of
another place's people source, a person's of the story's roster, or a BM&V talker's), and by 35-cast.md section 54
and 86-never-reuse-names.md (no never-reuse or canon name, nothing Nordic, at most a third Verb-the-Noun, an image
once); a household is one roof (its members share a home in people.jsonl, it has one head, and a person the drafter
put in a house's household keeps that household id and its head or partner place); a guard belongs to the place's
own guard body (the people source's `guard_body`, one of the lookups' guard_body ids, chosen from the record's
`held_by`: "levy" where a tribal levy keeps the guard) and says so in the trade; one or two sentences of backstory; every cite exists (a repo path, or place_note:<place>/<aspect>,
place_give:<place>/<seq>, culture:<id>, region:<id> in the new world's database).

A person a quest record places at the place (a `placements` row of kind person anchored `{place: <this place>}` in
newworld/story/quests/) is that place's person in that role, one person: the row names the placement's ref as its
`cast` and carries the record's name. A cast row's name is the record's and is no clash; a cast names a person the
record places here, and one row only; a name a quest record gives anyone, carried without that cast, is taken."""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
QUESTS = ROOT / "newworld" / "story" / "quests"
PLACES = ROOT / "newworld" / "places"
WEALTH = ("W1", "W2", "W3", "W4", "W5")
FIXED_ROLES = ("head", "partner")     # the drafter's household places an identity keeps
SENTENCE = re.compile(r"[.!?](?:\s+|$)")


def source(place_id: str, places: Path = PLACES) -> Path:
    """The people source file of a place: newworld/sources/people/<place>.json beside newworld/places."""
    from tools.places import variant
    return places.parent / "sources" / "people" / f"{variant.record_id(place_id)}.json"


def person_rows(place_id: str, places: Path = PLACES) -> list[dict]:
    """Every person row of the place's people source, as identities (duplicates kept, for the check)."""
    p = source(place_id, places)
    if not p.exists():
        return []
    out = []
    for r in json.loads(p.read_text(encoding="utf-8")).get("people", []):
        note = next((n for n in r.get("notes", []) if n.get("aspect") == "backstory"), {})
        out.append({"id": r.get("id"), "name": r.get("name"), "household": r.get("household"), "trade": r.get("trade"),
                    "wealth": r.get("wealth"), "role": r.get("role"), "cast": r.get("cast"),
                    "backstory": note.get("text"),
                    "cites": note.get("cites") or []})
    return out


def read(place_id: str, places: Path = PLACES) -> dict[str, dict]:
    """The place's identities by person id; {} when it has none yet."""
    return {r["id"]: r for r in person_rows(place_id, places)}


def db_resolver() -> Callable[[str], bool]:
    """A cite exists: a path under the repo, or a row of the new world's database."""
    from tools.argonia_world import db
    con = db.open("newworld").con
    sql = {"place_note": "SELECT 1 FROM place_note WHERE place_id=? AND aspect_id=?",
           "place_give": "SELECT 1 FROM place_give WHERE place_id=? AND seq=?",
           "culture": "SELECT 1 FROM culture WHERE id=?", "region": "SELECT 1 FROM region WHERE id=?"}

    def ok(cite: str) -> bool:
        kind, sep, rest = cite.partition(":")
        if sep and kind in sql:
            args = rest.split("/", 1) if kind.startswith("place_") else [rest]
            return len(args) == sql[kind].count("?") and con.execute(sql[kind], args).fetchone() is not None
        return bool(cite) and not cite.startswith("/") and ".." not in cite and (ROOT / cite.split("#")[0]).exists()
    return ok


def names_given(place_id: str, places: Path = PLACES) -> dict[str, str]:
    """Every name the new world's other people sources give, lower-cased, to whose it is."""
    out: dict[str, str] = {}
    for p in sorted(source(place_id, places).parent.glob("*.json")):
        doc = json.loads(p.read_text(encoding="utf-8"))
        if p.name == "lookups.json" or doc.get("place_id", p.stem) == place_id:
            continue
        for r in doc.get("people", []):
            if r.get("name"):
                out.setdefault(r["name"].lower(), f"the name of {r.get('id')} ({doc.get('place_id', p.stem)})")
    return out


def name_rules(place_id: str, places: Path = PLACES) -> tuple[set[str], dict[str, str]]:
    """(banned, taken): the never-reuse and canon names; and every name already given, to whose it is: the people
    of every other place's people source, the people of the story's roster (npc, kind person) and BM&V's talkers."""
    from tools.argonia_world import db, talk_check
    banned = talk_check.never_reuse() | talk_check.CANON | talk_check.lore_names()
    w = db.open()
    taken = {t.known_as.lower(): "a talker's name" for t in w.rows("talker") if t.known_as}
    for n in w.rows("npc"):
        if n.kind == "person" and n.name:
            taken.setdefault(n.name.lower(), f"the name of the story's {n.id}")
    for k, v in names_given(place_id, places).items():
        taken.setdefault(k, v)
    return banned, taken


def story_people(quests: Path = QUESTS) -> dict[str, dict]:
    """Every person the quest records place: {ref: {name, places, quest}} (`places` the place ids its rows anchor
    it at; `quest` the first record naming it)."""
    import yaml
    out: dict[str, dict] = {}
    for p in sorted(quests.rglob("*.yaml")):
        q = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        for r in q.get("placements") or []:
            if r.get("kind") == "person" and r.get("ref") and r.get("name"):
                o = out.setdefault(r["ref"], {"name": r["name"], "places": set(), "quest": p.stem})
                if (r.get("anchor") or {}).get("place"):
                    o["places"].add(r["anchor"]["place"])
    return out


def guard_bodies(places: Path = PLACES) -> set[str]:
    """The guard bodies a place may name (lookups.json, guard_body)."""
    p = places.parent / "sources" / "people" / "lookups.json"
    return {r["id"] for r in json.loads(p.read_text(encoding="utf-8")).get("guard_body", [])} if p.exists() else set()


def guard_body(place_id: str, places: Path = PLACES) -> str | None:
    """The place's own name for its watch: the people source's `guard_body`."""
    p = source(place_id, places)
    return json.loads(p.read_text(encoding="utf-8")).get("guard_body") if p.exists() else None


def check(place_id: str, places: Path = PLACES, resolve: Callable[[str], bool] | None = None,
          names: tuple[set[str], set[str] | dict[str, str]] | None = None,
          story: dict[str, dict] | None = None) -> list[str]:
    from tools.argonia_world.talk_check import IMAGES, NORDIC, VERB_NOUN
    resolve = resolve or db_resolver()
    banned, taken = names if names is not None else name_rules(place_id, places)
    if not isinstance(taken, dict):
        taken = {n: "a talker's name" for n in taken}
    story = story_people() if story is None else story
    story_name = {v["name"].lower(): k for k, v in story.items()}
    pdir = places / place_id
    people = {p["id"]: p for p in (json.loads(ln) for ln in (pdir / "people.jsonl").read_text().splitlines() if ln)}
    rows_ = person_rows(place_id, places)
    bad: list[str] = []
    if not rows_:
        return [f"{place_id}: no people source at {source(place_id, places)}"]
    bad += [f"{r['id']}: role {r['role']!r} but people.jsonl has {people[r['id']].get('role')!r}"
            for r in rows_ if r["id"] in people and r.get("role") != people[r["id"]].get("role")]
    rows = rows_
    watch = guard_body(place_id, places)
    if any(p.get("role") == "guard" for p in people.values()) and watch not in guard_bodies(places):
        bad.append(f"{place_id}: the people source's guard_body {watch!r} is not one of the lookups' guard_body ids")
        watch = None
    seen: dict[str, int] = defaultdict(int)
    for r in rows:
        seen[r.get("id")] += 1
    bad += [f"{i}: {n} rows" for i, n in seen.items() if n > 1]
    bad += [f"{i}: no person of that id in people.jsonl" for i in seen if i not in people]
    bad += [f"{i}: person without an identity" for i in people if i not in seen]

    cast_by: dict[str, str] = {}
    for r in rows:
        ref = r.get("cast")
        if not ref:
            continue
        cast = story.get(ref)
        if cast is None:
            bad.append(f"{r.get('id')}: cast {ref!r} is no person a quest record places")
        elif place_id not in cast["places"]:
            bad.append(f"{r.get('id')}: cast {ref!r} is placed at {sorted(cast['places'])}, not here")
        elif (r.get("name") or "").strip() != cast["name"]:
            bad.append(f"{r.get('id')}: cast {ref!r} is named {cast['name']!r} by {cast['quest']}, not {r.get('name')!r}")
        if ref in cast_by:
            bad.append(f"{r.get('id')}: cast {ref!r} is already {cast_by[ref]}")
        cast_by.setdefault(ref, r.get("id"))

    by_name: dict[str, str] = {}
    images: dict[str, str] = {}
    homes: dict[str, set] = defaultdict(set)
    heads: dict[str, int] = defaultdict(int)
    for r in rows:
        pid, name = r.get("id"), (r.get("name") or "").strip()
        p = people.get(pid, {})
        if not name:
            bad.append(f"{pid}: no name")
        elif name.lower() in by_name:
            bad.append(f"{pid}: name {name!r} also {by_name[name.lower()]}")
        else:
            by_name[name.lower()] = pid
            ref = story_name.get(name.lower())
            cast_ok = bool(ref) and r.get("cast") == ref
            if ref and not cast_ok:
                bad.append(f"{pid}: {name!r} is the story's {ref} ({story[ref]['quest']}, placed at "
                           f"{sorted(story[ref]['places'])}): one person, so only the row that names it as its cast "
                           f"carries it")
            if name.lower() in banned and not cast_ok:
                bad.append(f"{pid}: {name!r} is a canon or never-reuse name")
            if name.lower() in taken and not cast_ok:
                bad.append(f"{pid}: {name!r} is already {taken[name.lower()]}")
            if NORDIC.search(name):
                bad.append(f"{pid}: {name!r} has a Nordic element")
            for img, rx in IMAGES.items():
                if re.search(rf"(?i)(^|-)({rx})", name):
                    if img in images:
                        bad.append(f"{pid}: {name!r} repeats the image {img!r} of {images[img]!r}")
                    images.setdefault(img, name)
        hh = r.get("household") or {}
        if not hh.get("id") or not hh.get("role"):
            bad.append(f"{pid}: household needs an id and a role")
        else:
            homes[hh["id"]].add(p.get("home"))
            heads[hh["id"]] += hh["role"] == "head"
            drafted = p.get("household")
            if drafted:
                if drafted["id"] != hh["id"]:
                    bad.append(f"{pid}: household {hh['id']} but people.jsonl has {drafted['id']}")
                fixed = drafted.get("relation") if drafted.get("relation") in FIXED_ROLES else None
                if (fixed or hh["role"] in FIXED_ROLES) and fixed != hh["role"]:
                    bad.append(f"{pid}: household role {hh['role']} but people.jsonl has {drafted.get('relation')}")
        if r.get("wealth") not in WEALTH:
            bad.append(f"{pid}: wealth {r.get('wealth')!r} not one of W1..W5")
        if not (r.get("trade") or "").strip():
            bad.append(f"{pid}: no trade")
        elif p.get("role") == "guard" and watch and not re.search(rf"\b{re.escape(watch)}\b", r["trade"], re.I):
            bad.append(f"{pid}: a guard whose trade does not name the place's {watch}")
        n = len(SENTENCE.findall((r.get("backstory") or "").strip()))
        if not 1 <= n <= 2:
            bad.append(f"{pid}: backstory of {n} sentences (one or two)")
        cites = r.get("cites") or []
        if not cites:
            bad.append(f"{pid}: cites nothing")
        bad += [f"{pid}: cite {c!r} does not exist" for c in cites if not resolve(c)]
    vn = [r["name"] for r in rows if r.get("name") and VERB_NOUN.match(r["name"])]
    if len(vn) * 3 > len(rows):
        bad.append(f"{len(vn)} of {len(rows)} names Verb-the-Noun (at most a third): {vn}")
    for hid, hs in homes.items():
        if len(hs) > 1:
            bad.append(f"household {hid}: members live in {sorted(map(str, hs))}")
        if heads[hid] != 1:
            bad.append(f"household {hid}: {heads[hid]} heads")
    return bad


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places identities")
    ap.add_argument("verb", choices=["check"])
    ap.add_argument("place")
    a = ap.parse_args(argv)
    bad = check(a.place)
    for b in bad:
        print(b)
    print(f"identities {a.place}: {len(read(a.place))} rows, {len(bad)} problems")
    return 1 if bad else 0
