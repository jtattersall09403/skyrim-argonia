"""Light identities of a place's people (nw-03, Stocking: light identities come first): a name, a household, a
trade, a wealth band and a line or two of backstory per person. They are world facts, kept in the new world's
database source `newworld/sources/people/<place>.json` (tables person, household, person_note; loaded by
tools/newworld/stockdb.py), one person per person id of the place's people.jsonl, which keeps only placement. The
drafter writes each person's name onto its placement row.

    python -m tools.places identities check helstrom

read() gives each person as {id, name, household: {id, role}, trade, wealth: W1..W5, backstory, cites: [...]}
(the backstory note and its cites). The check proves:
every person has one row and every row a person; names unique in the place, never another place's talker's, and by
35-cast.md section 54 and 86-never-reuse-names.md (no never-reuse or canon name, nothing Nordic, at most a third
Verb-the-Noun, an image once); a household is one roof (its members share a home in people.jsonl, it has one head,
and a person the drafter put in a house's household keeps that household id and its head or partner place); a guard
belongs to the levy; one or two sentences of backstory; every cite exists (a repo path, or place_note:<place>/<aspect>,
place_give:<place>/<seq>, culture:<id>, region:<id> in the new world's database)."""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
PLACES = ROOT / "newworld" / "places"
WEALTH = ("W1", "W2", "W3", "W4", "W5")
FIXED_ROLES = ("head", "partner")     # the drafter's household places an identity keeps
SENTENCE = re.compile(r"[.!?](?:\s+|$)")


def source(place_id: str, places: Path = PLACES) -> Path:
    """The people source file of a place: newworld/sources/people/<place>.json beside newworld/places."""
    return places.parent / "sources" / "people" / f"{place_id}.json"


def person_rows(place_id: str, places: Path = PLACES) -> list[dict]:
    """Every person row of the place's people source, as identities (duplicates kept, for the check)."""
    p = source(place_id, places)
    if not p.exists():
        return []
    out = []
    for r in json.loads(p.read_text(encoding="utf-8")).get("people", []):
        note = next((n for n in r.get("notes", []) if n.get("aspect") == "backstory"), {})
        out.append({"id": r.get("id"), "name": r.get("name"), "household": r.get("household"), "trade": r.get("trade"),
                    "wealth": r.get("wealth"), "role": r.get("role"), "backstory": note.get("text"),
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


def name_rules() -> tuple[set[str], set[str]]:
    """(banned, taken): the never-reuse and canon names, and every talker's name already given elsewhere."""
    from tools.argonia_world import db, talk_check
    banned = talk_check.never_reuse() | talk_check.CANON | talk_check.lore_names()
    taken = {t.known_as.lower() for t in db.open().rows("talker") if t.known_as}
    return banned, taken


def check(place_id: str, places: Path = PLACES, resolve: Callable[[str], bool] | None = None,
          names: tuple[set[str], set[str]] | None = None) -> list[str]:
    from tools.argonia_world.talk_check import IMAGES, NORDIC, VERB_NOUN
    resolve = resolve or db_resolver()
    banned, taken = names if names is not None else name_rules()
    pdir = places / place_id
    people = {p["id"]: p for p in (json.loads(ln) for ln in (pdir / "people.jsonl").read_text().splitlines() if ln)}
    rows_ = person_rows(place_id, places)
    bad: list[str] = []
    if not rows_:
        return [f"{place_id}: no people source at {source(place_id, places)}"]
    bad += [f"{r['id']}: role {r['role']!r} but people.jsonl has {people[r['id']].get('role')!r}"
            for r in rows_ if r["id"] in people and r.get("role") != people[r["id"]].get("role")]
    rows = rows_
    seen: dict[str, int] = defaultdict(int)
    for r in rows:
        seen[r.get("id")] += 1
    bad += [f"{i}: {n} rows" for i, n in seen.items() if n > 1]
    bad += [f"{i}: no person of that id in people.jsonl" for i in seen if i not in people]
    bad += [f"{i}: person without an identity" for i in people if i not in seen]

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
            if name.lower() in banned:
                bad.append(f"{pid}: {name!r} is a canon or never-reuse name")
            if name.lower() in taken:
                bad.append(f"{pid}: {name!r} is already a talker's name")
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
        elif p.get("role") == "guard" and "levy" not in r["trade"].lower():
            bad.append(f"{pid}: a guard whose trade is not the levy")
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
