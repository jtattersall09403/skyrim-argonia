"""What the record does not promise, the source does not bring: its traps and hazards, its treasures beyond the
record's count, and any Nordic sign (decision 0006).

The record says what the place is (place-system, "Who decides what"). A source's trap field (a vine
snare, a gas vent, a poison bloom) stays only where the record names a danger of that kind and the place is not
friendly; a friendly or safe place has none. A source's loot containers (Bethesda's `Treas*`) keep the record's
treasure promises and no more: each treasure the draft adds by hand (`draft.add` containers) counts first, then the
source's own, nearest the source's middle first; the rest are dropped.
"""
from __future__ import annotations

import math
import re

# a trap, a hazard or a trap field's own piece, by editor id (Skyrim's Trap*, Dawnguard's poison bloom, the marsh's
# vine traps, gas fissures and pustules)
TRAP = re.compile(r"(^|[a-z0-9])trap|gasfissure|pustule|poisonbloom|beartrap|tripwire|pressureplate", re.I)
# words of a record's dangers that name such a thing
TRAP_WORDS = re.compile(r"\btraps?\b(?! (?:are|were|is) (?:robbed|kept))|\bsnares?\b|\bgas\b|\bvents?\b|\bspikes?\b|"
                        r"\bpoison\w*|\bblooms?\b|\bfissures?\b|\bpustules?\b|\btripwires?\b", re.I)
TREASURE = re.compile(r"^Treas", re.I)


def record(place_id: str) -> dict:
    """{disposition, dangers, treasure} of the place from the database (place_danger, place_note, place_give)."""
    from tools.argonia_world import db
    w = db.open("newworld")

    def rows(t):
        return [r if isinstance(r, dict) else dict(vars(r)) for r in w.rows(t)]
    d = next((r for r in rows("place_danger") if r.get("place_id") == place_id), {})
    notes = [n for n in rows("place_note") if n.get("place_id") == place_id and n.get("aspect_id") == "dangers"]
    tr = sum(int(g.get("count") or 1) for g in rows("place_give")
             if g.get("place_id") == place_id and g.get("give_kind_id") == "treasure")
    return {"disposition": d.get("disposition_id"), "dangers": " ".join(n.get("text") or "" for n in notes),
            "treasure": tr}


def traps_allowed(rec: dict) -> bool:
    """A place keeps a source's traps only when it is not friendly and its dangers name one."""
    if (rec.get("disposition") or "").lower() == "friendly":
        return False
    return bool(TRAP_WORDS.search(rec.get("dangers") or ""))


def is_trap(base: dict) -> bool:
    return bool(TRAP.search(base.get("edid") or ""))


def is_treasure(base: dict) -> bool:
    return str(base.get("type")) in ("CONT", "Container") and bool(TREASURE.match(base.get("edid") or ""))


def drops(ext: list[dict], bases: dict, rec: dict, added: list[dict] | None = None) -> dict[str, str]:
    """{source ref id: why} for each source trap the record does not allow and each treasure beyond its count."""
    from tools.places.draft.io import is_nordic_sign
    out: dict[str, str] = {}
    for r in ext:
        if is_nordic_sign(bases.get(r.get("base")) or {}):
            out[r["id"]] = "a Nordic sign (a Doomstone, a word wall, a shrine of Talos): decision 0006"
    if not traps_allowed(rec):
        why = ("a trap or hazard of the source's: the record names no such danger"
               + (" and the place is friendly" if (rec.get("disposition") or "") == "friendly" else ""))
        for r in ext:
            if is_trap(bases.get(r.get("base")) or {}):
                out[r["id"]] = why
    own = [r for r in ext if is_treasure(bases.get(r.get("base")) or {})]
    by_hand = sum(1 for a in added or [] if a.get("kind") == "container" and (a.get("need") is not None or
                                                                              is_treasure(bases.get(a["base"]) or {})
                                                                              or a.get("name")))
    room = max(0, int(rec.get("treasure") or 0) - by_hand)
    if own:
        mx = sum(r["pos"][0] for r in ext) / len(ext)
        my = sum(r["pos"][1] for r in ext) / len(ext)
        own.sort(key=lambda r: (math.hypot(r["pos"][0] - mx, r["pos"][1] - my), r["id"]))
        for r in own[room:]:
            out[r["id"]] = (f"a treasure beyond the record's promises (it promises {rec.get('treasure', 0)}, "
                            f"{by_hand} placed by hand)")
    return out
