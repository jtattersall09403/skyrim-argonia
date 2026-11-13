"""The world a paper game is played in (docs/design/paper-playtest.md): what the player sees beyond the quest forms.

A snapshot, kept in the session so a run never changes under the player:
- names: the name the player sees for each ref, item and cell id;
- places: each cell's name, whether it is indoors, and for an interior the outside position of its door;
- talkers: every authored talker standing in the places the forms involve (the cells of their refs, and the
  settlements those cells belong to), with each topic's prompt, its lines in order, and its gate as the build makes
  it (talk.md: every topic gated to the talker; the stranger greeting; a rumour gated on its quest's stages);
- doors: where a door leads (the position of its other side), for a door the census knows.

- people: a person's race and sex ({ref or talker id: {race, sex}}), for "an Argonian woman".

Sources, first winning: the forms (their `names`, a ref's `name`, a door's `destination`, a marker's `name` as its
cell's place name), then each names file given (`--names`, JSON with "names" {id: name}, "places" {cell: {name,
interior, entrance}} and "people" {id: {race, sex}}), then the world database (story/data/db). A name nobody gives is
a harness error at the start of the run (game.py), never made up.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

QUEST_SOURCE = re.compile(r"^quest (ARG_\w+) stages? (\d+)(?:-(\d+))?;")


def _cells(forms) -> set[str]:
    return {r["at"]["cell"] for f in forms for r in f["refs"] if r.get("at")}


def from_db(forms: list[dict]) -> dict:
    """The snapshot's parts the world database knows. Empty parts when a form's keys are not in it."""
    from tools.argonia_world import db
    w = db.open()
    names, places, doors, people = {}, {}, {}, {}
    cells = _cells(forms)
    q = w.query
    sets = {r["settlement"] for c in cells for r in q("SELECT settlement FROM bmv_settlement_cell WHERE cell = ?", c)}
    rows = [dict(r) for r in q("SELECT b.*, t.known_as FROM bmv_talker b JOIN talker t ON t.id = b.id")]
    here = [r for r in rows if r["cell"] in cells or (r["settlement"] and r["settlement"] in sets)]
    prompts = {r["id"]: r["prompt"] for r in q("SELECT id, prompt FROM talk_topic")}
    facts = {r["id"]: r["source"] for r in q("SELECT id, source FROM talk_fact WHERE topic = 'talk.rumours'")}
    talkers = []
    for r in here:
        topics = []
        for tt in q("SELECT topic, facts FROM talker_topic WHERE talker = ? ORDER BY topic", r["id"]):
            lines = [x["text"] for x in q("SELECT text FROM talk_line WHERE talker = ? AND topic = ? ORDER BY ord",
                                          r["id"], tt["topic"])]
            if not lines:
                continue
            gate = None
            for fid in (f.strip() for f in tt["facts"].split(",")):
                m = QUEST_SOURCE.match(facts.get(fid, ""))
                if m:
                    gate = {"quest": m.group(1), "first": int(m.group(2)),
                            "last": int(m.group(3)) if m.group(3) else None}
                    break
            topics.append({"topic": tt["topic"], "prompt": prompts.get(tt["topic"], tt["topic"]), "lines": lines,
                           "gate": gate})
        talkers.append({"id": r["id"], "name": r["known_as"], "cell": r["cell"], "interior": bool(r["interior"]),
                        "x": float(r["x"]), "y": float(r["y"]), "topics": topics, "race": r["race"],
                        "sex": r["sex"]})
    for c in cells | {t["cell"] for t in talkers}:
        places[c] = _place(w, c)
    fallback = []
    for f in forms:
        for ref in f["refs"]:
            p = ref["placement"]
            key = p.get("existing") or (p.get("base") or {}).get("id")
            if not key:
                continue
            own = None
            if not p.get("existing") and not ref.get("name") and ref.get("kind") == "person":
                # a person placed from a template has no name of our own on the form: the quest cast's name
                own = q("SELECT name AS n FROM npc WHERE id = ?", ref["id"])
                own = own[0]["n"] if own and own[0]["n"] else None
                if not own:
                    fallback.append(ref["id"])
            got = own and [{"n": own}] or q("SELECT t.known_as AS n FROM talker t WHERE t.id = ?", key) or \
                q("SELECT n.name AS n FROM bmv_placement p JOIN bmv_npc n ON n.id = p.npc WHERE p.id = ?", key) or \
                q("SELECT name AS n FROM bmv_npc WHERE id = ?", key)
            if got and got[0]["n"]:
                names[ref["id"]] = got[0]["n"]
            if ref.get("kind") == "person":
                who = q("SELECT race, sex FROM npc WHERE id = ?", ref["id"]) or \
                    q("SELECT race, sex FROM bmv_talker WHERE id = ?", key) or \
                    q("SELECT r.name AS race, n.sex FROM bmv_placement p JOIN bmv_npc n ON n.id = p.npc "
                      "LEFT JOIN bmv_race r ON r.id = n.race WHERE p.id = ?", key) or \
                    q("SELECT r.name AS race, n.sex FROM bmv_npc n LEFT JOIN bmv_race r ON r.id = n.race "
                      "WHERE n.id = ?", key)
                if who and (who[0]["race"] or who[0]["sex"]):
                    people[ref["id"]] = {"race": who[0]["race"], "sex": who[0]["sex"]}
            d = q("SELECT d.*, t.cell AS to_cell, t.x AS tx, t.y AS ty, t.z AS tz FROM bmv_door d "
                  "LEFT JOIN bmv_door t ON t.id = d.target WHERE d.id = ?", key)
            if d and d[0]["to_cell"]:
                to = _place(w, d[0]["to_cell"])
                places.setdefault(d[0]["to_cell"], to)
                names.setdefault(ref["id"], f"Door to {to['name']}" if to.get("name") else "Door")
                doors[ref["id"]] = {"cell": d[0]["to_cell"], "interior": to["interior"], "x": d[0]["tx"],
                                    "y": d[0]["ty"], "z": d[0]["tz"]}
    return {"names": names, "places": places, "talkers": talkers, "doors": doors, "fallback": fallback,
            "people": people}


def _place(w, cell) -> dict:
    from tools.questform.compile import place
    return place(w, cell)


def from_forms(forms: list[dict]) -> tuple[dict, dict]:
    """What the forms alone say the player sees: (names, places). The form's `names` for its items, a ref's `name` (a
    door that leads somewhere is "Door to <destination>" unless it has a name of its own), and a marker's `name` as
    the name of the place its cell is."""
    names, places = {}, {}
    for f in forms:
        names.update(f.get("names", {}))
        for r in f.get("refs", []):
            n, dest = r.get("name"), r.get("destination")
            if r.get("kind") == "door" and dest and n in (None, "Door"):
                n = f"Door to {dest}"
            if n:
                names[r["id"]] = n
            if r.get("kind") == "marker" and n and r.get("at"):
                places[r["at"]["cell"]] = {"name": n, "interior": r["at"]["interior"]}
    return names, places


def load_names(path: Path) -> dict:
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    return {"names": d.get("names", {}), "places": d.get("places", {}), "people": d.get("people", {})}


def snapshot(forms: list[dict], names_files: list[Path] = (), use_db: bool = True) -> dict:
    """A name comes from the form first, then a names file, then the world database. `from_names_file` lists the
    ids (and cells) whose name only a names file gave: what the forms still lack. A person placed from a template
    with no name of our own on the form or in a names file gets the quest cast's name from the story database, else
    the template's, with one warning line saying so."""
    snap = from_db(forms) if use_db else {"names": {}, "places": {}, "talkers": [], "doors": {}, "fallback": [],
                                          "people": {}}
    names, places = from_forms(forms)
    used = set()
    for p in names_files:
        extra = load_names(p)
        for k, v in extra["names"].items():
            if k not in names:
                snap["names"][k] = v
                used.add(k)
        for c, v in extra["places"].items():
            if c not in places:
                snap["places"][c] = {**snap["places"].get(c, {}), **v}
                used.add(c)
        for k, v in extra["people"].items():
            snap["people"][k] = {**snap["people"].get(k, {}), **v}
    snap["names"].update(names)
    for c, v in places.items():
        snap["places"][c] = {**snap["places"].get(c, {}), **v}
    text = json.dumps(forms)
    snap["from_names_file"] = sorted(k for k in used if json.dumps(k) in text)      # only what these forms name
    snap["fallback"] = [r for r in snap["fallback"] if r not in names and r not in used]
    for r in snap["fallback"]:
        n = snap["names"].get(r)
        print(f"WARNING: {r} is placed from a template with no name of its own on the form or in the story "
              f"database; the player sees the template's name" + (f" ({n})" if n else "") + ".", file=sys.stderr)
    return snap
