"""The name each room of a place shows: on its door, looked at from outside, and on entering (the cell's name).

A player knows a room by this name, so it says what the room is, from what the place data already holds:

1. the agent's call in place.json `draft.room_names` {space: {name, why}}, for a room nothing below names;
2. the place a promise names, where that promise is kept in the room: a station of it stands there or the person who
   gives it works there, and the record's detail names a place ("the tree-minders' hall" names the room where its
   enchanter stands "Tree-Minders' Hall"; "the boatmen's lodge" the room its innkeeper keeps);
3. the household that lives there, by its head, as Skyrim names its homes ("Alvor's House");
4. the source's own name for the cell, unless it reads as a builder's leftover ("Quick Test Cell").

A room still without a name, two rooms with one name, or a leftover name is a fault `draft check` reports.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


def title(detail: str) -> str:
    """A record's place words as the name the game shows: 'the tree-minders' hall' -> "Tree-Minders' Hall"."""
    words = re.sub(r"^the\s+", "", detail.strip(), flags=re.I).split()
    return " ".join("-".join(p[:1].upper() + p[1:] for p in w.split("-")) for w in words)


def leftover(name: str | None) -> bool:
    """A name a builder left in the source (a test cell, an editor id), never one a player should read."""
    if not name:
        return False
    return bool(re.search(r"\b(test|temp|duplicate|unused|delete)\b", name, re.I)) or bool(
        re.fullmatch(r"[0-9A-Za-z_]+", name) and re.search(r"\d|_|[a-z][A-Z]", name))


def _people_source(place_id: str, places: Path) -> dict:
    p = places.parent / "sources" / "people" / f"{place_id}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def room_names(place_id: str, files: dict, place: dict, gives: list[dict], places: Path,
               source_names: dict[str, str | None] | None = None) -> dict[str, tuple[str | None, str]]:
    """{space: (name, why)} for every room of the place, by the rules above."""
    rooms = [sid for sid in files["spaces"] if sid != "exterior"]
    calls = (place.get("draft") or {}).get("room_names") or {}
    detail = {g["seq"]: g.get("detail") or "" for g in gives}
    kind_detail = {g["give_kind_id"]: g.get("detail") or "" for g in gives}
    where = {r["id"]: sid for sid, sp in files["spaces"].items() for r in sp["refs"]}
    st = place.get("stations") or {}
    kept: dict[str, list[str]] = {sid: [] for sid in rooms}
    for a in st.get("added") or []:
        if a.get("space") in kept and kind_detail.get(a.get("station")):
            kept[a["space"]].append(kind_detail[a["station"]])
    for kind, ids in (st.get("found") or {}).items():
        for i in ids:
            if where.get(i) in kept and kind_detail.get(kind):
                kept[where[i]].append(kind_detail[kind])
    for p in files.get("people") or []:
        sid = (p.get("work") or {}).get("space")
        if sid in kept:
            kept[sid] += [detail.get(s.get("seq"), "") for s in p.get("services") or []]
    src = _people_source(place_id, places)
    names = {p["id"]: p.get("name") for p in src.get("people", [])}
    heads = {(p.get("household") or {}).get("id"): p["id"] for p in src.get("people", [])
             if (p.get("household") or {}).get("role") == "head"}
    home = {h["home_space"]: h for h in src.get("households", []) if h.get("home_space") in kept}
    out: dict[str, tuple[str | None, str]] = {}
    for sid in rooms:
        call = calls.get(sid)
        places_named = Counter(d for d in kept[sid] if re.match(r"the\s", d, re.I))
        hh = home.get(sid)
        head = names.get(heads.get((hh or {}).get("id")))
        own = (source_names or {}).get(sid, (files["spaces"][sid].get("space") or {}).get("name"))
        if call:
            out[sid] = (call["name"], call.get("why") or "the agent's call (place.json draft.room_names)")
        elif places_named:
            d = max(places_named, key=lambda k: (places_named[k], -kept[sid].index(k)))
            out[sid] = (title(d), f"the record's promise kept in it: {d}")
        elif head:
            out[sid] = (f"{head}'s House", f"the home of {head}'s household (people source)")
        elif own and not leftover(own):
            out[sid] = (own, "the source's own name for the cell")
        else:
            out[sid] = (None, "nothing names it: give it a name in place.json draft.room_names")
    return out


def faults(files: dict, names: dict[str, tuple[str | None, str]] | None = None) -> list[str]:
    """What a player would misread on a room's door: no name, a builder's leftover, two rooms with one name."""
    got = {sid: (sp.get("space") or {}).get("name") for sid, sp in files["spaces"].items() if sid != "exterior"}
    out = [f"room {sid}: shows no name" for sid, n in sorted(got.items()) if not n]
    out += [f"room {sid}: shows the builder's leftover name {n!r}" for sid, n in sorted(got.items()) if leftover(n)]
    seen = Counter(n for n in got.values() if n)
    out += [f"rooms {sorted(s for s, x in got.items() if x == n)}: share the name {n!r}" for n, c in sorted(seen.items()) if c > 1]
    for sid, (want, why) in sorted((names or {}).items()):
        if want and got.get(sid) != want:
            out.append(f"room {sid}: shows {got.get(sid)!r}, its rule gives {want!r} ({why}): run `draft names`")
    return out


def owner_named(pdir: Path) -> set[str]:
    """The rooms an owner's finalised studio save created (and so named): never renamed by a stage."""
    out = set()
    for p in sorted((pdir / "edits").glob("*.json")) if (pdir / "edits").exists() else []:
        save = json.loads(p.read_text(encoding="utf-8"))
        if save.get("final"):
            out |= {op.get("space") for op in save.get("ops") or [] if op.get("space_copy_of")}
    return out


def apply(st, log=print) -> None:
    """The `names` stage: each room's space.json `name` by the rules above; an owner's room keeps its name."""
    from tools.places.draft.run import place_record
    gives = place_record(st.place_id)[1]
    source = {}
    for sid, sp in st.files["spaces"].items():
        info = sp.get("space") or {}
        copied = (info.get("copy_of") or "").split("/", 1)[-1]
        if sid != "exterior":
            source[sid] = st.src.spaces[copied].meta.get("name") if copied in st.src.spaces else info.get("name")
    mine = owner_named(st.pdir)
    for sid, (name, why) in sorted(room_names(st.place_id, st.files, st.place, gives, st.pdir.parent, source).items()):
        sp = st.files["spaces"][sid].get("space")
        if sp is None or sid in mine or name is None or sp.get("name") == name:
            if name is None:
                log(f"draft names {st.place_id}: {sid}: {why}")
            continue
        log(f"draft names {st.place_id}: {sid}: {sp.get('name')!r} -> {name!r} ({why})")
        sp["name"] = name
