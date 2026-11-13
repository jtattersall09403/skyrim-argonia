"""The sight test's input for a place (docs/design/place-studio.md, "What the stories need of a place").

For each need of the place, the spot it rests on (or, when nothing does yet, the spot where the story puts it)
described only as a player would meet it: what stands there in plain kinds (tools/argonia_world/surroundings.py's
KINDS, read over each base's model and editor id), the names the game itself shows (a door's room name, a map
marker's name, a named thing such as "Arcane Enchanter"), and the people there as a player sees them (a person's
name, what they look like, what they offer when spoken to). Never our names for things, ids or the story. A fresh
reader is given the sheet and asked what each spot is; the agent then records against each need whether the reader
recognised it (the need's `sight` in newworld/sources/needs/<place>.json).

    python -m tools.places sight <place> [--radius 2000]     writes out/places/sight/<place>/sheet.md and key.json

The base catalogue is $PLACES_OUT/catalogue/bases.jsonl (default out/places), the place's source bundle
$PLACES_OUT/bundles/src.<source>/ (for the rooms a copied interior holds).
"""
from __future__ import annotations

import argparse
import json
import math
import os
from collections import Counter
from pathlib import Path

from tools.argonia_world.surroundings import compass, count, how_far, kind_of
from tools.places import needs as N

ROOT = Path(__file__).resolve().parents[2]
SERVICE_WORDS = {"trader-spells": "sells spell tomes", "trainer": "offers training", "trader-general": "trades goods",
                 "trader-apothecary": "sells potions and ingredients", "trader-blacksmith": "sells weapons and armour",
                 "trader-innkeeper": "sells food and drink", "inn-room": "rents a bed for the night",
                 "rootworm-stop": "offers to call a rootworm to carry you to other towns",
                 "boat-stop": "offers passage by boat to other towns"}
NAMED_TYPES = {"FURN", "CONT", "ACTI", "DOOR", "BOOK", "MISC", "FLOR", "WEAP", "ARMO", "ALCH", "INGR", "KEYM"}


def _out() -> Path:
    return Path(os.environ.get("PLACES_OUT") or ROOT / "out" / "places")


def _jsonl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def bases_for(keys: set[str], cat: Path) -> dict:
    out = {}
    with open(cat, encoding="utf-8") as f:
        for ln in f:
            k = ln[9:ln.find('"', 9)] if ln.startswith('{"key": "') else None
            if k in keys:
                out[k] = json.loads(ln)
    return out


def space_rows(pid: str, sid: str, places: Path, out: Path) -> list[dict]:
    sdir = places / pid / "spaces" / sid
    rows = _jsonl(sdir / "refs.jsonl")
    info = N._json(sdir / "space.json")
    if not info or not info.get("copy_of"):
        return rows
    if info.get("room"):
        return []   # one room of a shared cell: read only by the build's room rule (not here)
    src = out / "bundles" / f"src.{info['copy_of'].split('/', 1)[0]}"
    from tools.places.draft_bundle import copy_space
    return copy_space(info, rows, src)


def _what(rows: list[dict], bases: dict, spaces: dict, x0: float, y0: float, radius: float | None) -> tuple:
    kinds, labels = Counter(), []
    for r in rows:
        if radius is not None and math.hypot(r["pos"][0] - x0, r["pos"][1] - y0) > radius:
            continue
        b = bases.get(r["base"], {})
        if (r.get("map_marker") or {}).get("Name"):
            labels.append(f"the world map marks a place here named \"{r['map_marker']['Name']}\"")
            continue
        door = r.get("door") or {}
        if door.get("to_space") and door["to_space"] != "exterior":
            nm = (spaces.get(door["to_space"]) or {}).get("name")
            labels.append(f"a door; looking at it, the game shows \"{nm}\"" if nm else
                          "a door; looking at it, the game shows no name")
            continue
        if b.get("type") in NAMED_TYPES and b.get("name"):
            labels.append(f"a {b['type'] == 'DOOR' and 'door' or 'thing'} the game names \"{b['name']}\"")
            continue
        k = kind_of(f"{(b.get('model') or '').lower()} {(b.get('edid') or '').lower()}")
        if k and k[0] == "skip":
            continue
        kinds[k[1] if k else "unrecognised objects"] += 1
    things = [f"{count(n)} {k}" if n > 1 else f"one {k.rstrip('s') if k.endswith('s') and k != 'unrecognised objects' else k}"
              for k, n in kinds.most_common(14)]
    return things, sorted(Counter(labels).items())


def _person(p: dict, ident: dict, place_row: dict) -> str:
    race = (ident.get("race") or "").replace("Race", "")
    sex = {"male": "man", "female": "woman"}.get(ident.get("sex"), "person")
    bits = [f"{'an' if race[:1] in 'AEIOU' else 'a'} {race} {sex} the game names \"{ident.get('name') or p.get('name')}\""]
    if place_row.get("role") == "guard":
        bits.append("dressed and armed as a guard")
    offers = [SERVICE_WORDS[s.get("kind") or s.get("give_kind_id")] for s in place_row.get("services", [])
              if (s.get("kind") or s.get("give_kind_id")) in SERVICE_WORDS]
    if offers:
        bits.append("who, spoken to, " + " and ".join(dict.fromkeys(offers)))
    return ", ".join(bits)


def sheet(pid: str, radius: float = 2000.0, places: Path = N.PLACES, root: Path = N.NEEDS) -> tuple[str, dict]:
    out = _out()
    doc = N.read(pid, root)
    spaces = {d.name: (N._json(d / "space.json") or {}) for d in (places / pid / "spaces").iterdir() if d.is_dir()}
    ext = _jsonl(places / pid / "spaces" / "exterior" / "refs.jsonl")
    by_id = {r["id"]: r for r in ext}
    people = _jsonl(places / pid / "people.jsonl")
    idents = {p["id"]: p for p in (N._json(N.PEOPLE / f"{pid}.json") or {"people": []})["people"]}
    rooms: dict[str, list[dict]] = {}
    spots, key = [], {}
    for n in doc.get("needs", []):
        r = n.get("rests") or {}
        near = n.get("near") or {}
        at, room = None, None
        if r.get("person"):
            w = next((p.get("work") or {} for p in people if p["id"] == r["person"]), {})
            if w.get("space") == "exterior" and w.get("pos"):
                at = w["pos"][:2]
            elif w.get("space"):
                room = w["space"]
                door = by_id.get(spaces.get(room, {}).get("door_from"))
                at = door["pos"][:2] if door else None
        elif r.get("space") and r["space"] != "exterior":
            room = r["space"]
            door = by_id.get(spaces[room].get("door_from"))
            at = door["pos"][:2] if door else None
        elif r.get("ref") in by_id:
            at = by_id[r["ref"]]["pos"][:2]
        if at is None and near.get("pos"):
            at = near["pos"][:2]
        if at is None:
            continue
        sp = next((s for s in spots if math.hypot(s["at"][0] - at[0], s["at"][1] - at[1]) < 300 and s["room"] == room), None)
        if sp is None:
            sp = {"at": at, "room": room, "needs": []}
            spots.append(sp)
        sp["needs"].append(n["seq"])
    keys = {r["base"] for r in ext}
    for sp in spots:
        if sp["room"]:
            rooms.setdefault(sp["room"], space_rows(pid, sp["room"], places, out))
            keys |= {r["base"] for r in rooms[sp["room"]]}
    bases = bases_for(keys, out / "catalogue" / "bases.jsonl")
    centre = next((r["pos"] for r in ext if (r.get("map_marker") or {}).get("Name")), ext[0]["pos"] if ext else [0, 0])
    lines = [f"# What a player sees at {len(spots)} spots of one town",
             "", "You are a player walking through a town in a game you know nothing about. Below is what you would "
             "see at a few spots: what stands there, the names the game shows you when you look at a door, a map "
             "marker or a thing, and the people there. Nothing else is known.", ""]
    for i, sp in enumerate(spots):
        letter = chr(65 + i)
        key[letter] = sp["needs"]
        x, y = sp["at"]
        dx, dy = x - centre[0], y - centre[1]
        lines.append(f"## Spot {letter}")
        lines.append(f"Where: {how_far(math.hypot(dx, dy))} {compass(dx, dy)} of the town's map marker." if math.hypot(dx, dy) > 300
                     else "Where: at the town's map marker.")
        things, labels = _what(ext, bases, spaces, x, y, radius)
        lines.append(f"Within about {round(radius / 70)} metres: " + ("; ".join(things) or "nothing standing") + ".")
        for lab, c in labels:
            lines.append(f"- {lab}" + (f" (x{c})" if c > 1 else ""))
        who = [p for p in people if (p.get("work") or {}).get("space") == "exterior" and (p.get("work") or {}).get("pos")
               and math.hypot(p["work"]["pos"][0] - x, p["work"]["pos"][1] - y) <= radius]
        if who:
            lines.append(f"People standing here by day ({len(who)}):")
            lines += [f"- {_person(p, idents.get(p['id'], {}), p)}" for p in who[:20]]
            if len(who) > 20:
                lines.append(f"- and {len(who) - 20} more townsfolk")
        if sp["room"]:
            rrows = rooms.get(sp["room"]) or []
            nm = spaces[sp["room"]].get("name")
            lines.append(f"A door here leads inside. Through it, the game names the place \"{nm}\"." if nm else
                         "A door here leads inside. Through it, the game shows no name for the place.")
            if rrows:
                t, labs = _what(rrows, bases, spaces, 0, 0, None)
                lines.append("Inside: " + ("; ".join(t) or "nothing standing") + ".")
                lines += [f"- {lab}" + (f" (x{c})" if c > 1 else "") for lab, c in labs]
            inside = [p for p in people if (p.get("work") or {}).get("space") == sp["room"]]
            if inside:
                lines.append("People inside by day:")
                lines += [f"- {_person(p, idents.get(p['id'], {}), p)}" for p in inside]
        lines.append("")
    things = "\n".join(f"- {n['thing']}" for n in doc.get("needs", []))
    lines += ["## Questions", "",
              "1. Answer this first, for each spot in turn, before reading question 2: in a few words, what is this "
              "spot to you, what would you call the place or the building there, and what would you expect to do there?",
              "2. Only then: here are some things a story might want this town to have. For each, which spot (if any) "
              "would you, as a player who has been told nothing, take to be it without being told? Say 'none' when "
              "nothing you saw would tell you, and why.", "", things, ""]
    return "\n".join(lines), key


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places sight", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("place")
    ap.add_argument("--radius", type=float, default=2000.0)
    a = ap.parse_args(argv)
    text, key = sheet(a.place, a.radius)
    d = _out() / "sight" / a.place
    d.mkdir(parents=True, exist_ok=True)
    (d / "sheet.md").write_text(text, encoding="utf-8")
    (d / "key.json").write_text(json.dumps(key, indent=1) + "\n", encoding="utf-8")
    print(f"{d / 'sheet.md'}: {len(key)} spots; the key (spot to need) is {d / 'key.json'}, never shown to the reader")
    return 0
