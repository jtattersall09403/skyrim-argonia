"""Read helpers over the world database for the writing skills' briefs (decision 0030 §5): a person, their stance,
a culture sheet, a place's facts and its last build, the topic web, the vocabulary. Each returns plain values from
db.World queries; nothing here reads a file.
"""
from __future__ import annotations


def num(v):
    return int(v) if isinstance(v, float) and v.is_integer() else v


def _bool_positions(w) -> dict[str, set[int]]:
    """term -> the argument positions its shape types `bool` (an untyped SQLite value stores true as 1)."""
    cache = getattr(w, "_bool_positions", None)
    if cache is None:
        from .checks import _split
        cache = {}
        for r in w.query("SELECT id, args FROM condition_term WHERE args IS NOT NULL"):
            cache[r["id"]] = {i for i, part in enumerate(_split(r["args"])) if part.strip().strip("`").endswith("bool")}
        w._bool_positions = cache
    return cache


def typed(w, term: str, args: list) -> list:
    """Arguments with the vocabulary's types restored (`bool` positions as True/False)."""
    pos = _bool_positions(w).get(term, set())
    return [bool(v) if i in pos and v in (0, 1) else num(v) for i, v in enumerate(args)]


def condition(w, cid, collapse: bool = False):
    """A condition tree as the record writes it: {term: [args]} (or {term: arg} for one argument when `collapse`),
    {all|any: [...]}, {not: ...}."""
    term = w.query("SELECT term FROM condition WHERE id = ?", cid)[0]["term"]
    kids = w.values("SELECT id FROM condition WHERE parent_id = ? ORDER BY ord", cid)
    if term in ("all", "any"):
        return {term: [condition(w, k, collapse) for k in kids]}
    if term == "not":
        return {"not": condition(w, kids[0], collapse)}
    args = typed(w, term, w.values("SELECT value FROM condition_arg WHERE condition_id = ? ORDER BY ord", cid))
    return {term: args[0] if collapse and len(args) == 1 else args}


def actions(w, aid, collapse: bool = False):
    out = []
    for a in w.query("SELECT ord, term FROM action WHERE list_id = ? ORDER BY ord", aid):
        args = typed(w, a["term"], w.values("SELECT value FROM action_arg WHERE list_id = ? AND ord = ? "
                                            "ORDER BY arg_ord", aid, a["ord"]))
        out.append({a["term"]: args[0] if collapse and len(args) == 1 else args})
    return out


def person(w, npc_id: str) -> dict | None:
    r = w.get("npc", npc_id)
    if r is None:
        return None
    return {"id": r.id, "name": r.name, "race": r.race, "sex": r.sex, "role": r.role, "notes": r.notes,
            "outfit": r.look_outfit, "depth": r.depth, "name_form": r.name_form, "home": r.home_place_id,
            "factions": w.values("SELECT faction_id FROM npc_faction WHERE npc_id = ? ORDER BY ord", npc_id)}


def stance(w, npc_id: str) -> dict | None:
    r = w.get("stance", npc_id)
    if r is None:
        return None
    topics = {t["opinion_class"]: {"lean": num(t["lean"]), "from": t["from"], "deviation_lean": t["deviation_lean"],
                                   "deviation_reason": t["deviation_reason"]}
              for t in w.query("SELECT * FROM stance_topic WHERE person_id = ?", npc_id)}
    return {"chain": w.values("SELECT value FROM stance_chain WHERE person_id = ? ORDER BY ord", npc_id),
            "voice": {"chatter": r.voice_chatter, "contraction_rate": r.voice_contraction_rate,
                      "address_term": r.voice_address_term, "favourite_subject": r.voice_favourite_subject,
                      "quirk": r.voice_quirk,
                      "never_mentions": w.values("SELECT value FROM stance_never_mentions WHERE person_id = ? "
                                                 "ORDER BY ord", npc_id)},
            "topics": topics}


def sheet(w, sheet_id: str) -> dict | None:
    r = w.get("culture_sheet", sheet_id)
    if r is None:
        return None
    entries: dict[str, list[str]] = {}
    for e in w.query("SELECT kind, text FROM culture_entry WHERE culture_sheet_id = ? ORDER BY kind, ord", sheet_id):
        entries.setdefault(e["kind"], []).append(e["text"])
    opinions = {o["opinion_class"]: o["text"]
                for o in w.query("SELECT opinion_class, text FROM culture_opinion WHERE culture_sheet_id = ?", sheet_id)}
    return {"id": r.id, "name": r.name, "level": r.level, "formality": r.speech_formality, "entries": entries,
            "opinions": opinions}


def place_facts(w, place_id: str) -> list:
    """The place's facts in the order the place states them."""
    return w.query("SELECT * FROM fact WHERE place_id = ? ORDER BY ord, id", place_id)


def topic_ids(w) -> set[str]:
    return set(w.values("SELECT id FROM topic"))


def vocabulary(w) -> tuple[set[str], set[str]]:
    """(predicates, action verbs) of the condition vocabulary."""
    return (set(w.values("SELECT id FROM condition_term WHERE kind = 'predicate'")),
            set(w.values("SELECT id FROM condition_term WHERE kind = 'action'")))
