"""The paper game's vocabularies: every condition and result word of the quest form (tools/questform/schema.json),
each a function of the game, the quest, the row and the speaker. A word not here is a HarnessError where it is met.
"""
from __future__ import annotations

# A person's regard for the player before any change, and its bounds: Skyrim's relationship rank, kept between -4
# and 4 (ARG_Effects ChangeRegard).
REGARD_START, REGARD_MIN, REGARD_MAX = 0, -4, 4


class HarnessError(Exception):
    """The paper game cannot model something: the run stops and names it."""


def race_key(v: str) -> str:
    v = (v or "").lower().replace(" ", "")
    return v[:-4] if v.endswith("race") else v


def _c_stage(op):
    def f(g, q, c, _):
        n = g.stage(c["quest"])
        if c["quest"] not in g.forms:
            raise HarnessError(f"condition names quest {c['quest']}, which this run did not load")
        if op == "done":
            st = g.s["quests"].get(c["quest"])
            return st is not None and c["stage"] in st["done"]
        return n is not None and (n == c["stage"] if op == "is" else n >= c["stage"])
    return f


_OPS = {"=": lambda a, b: a == b, "!=": lambda a, b: a != b, "<": lambda a, b: a < b, "<=": lambda a, b: a <= b,
        ">": lambda a, b: a > b, ">=": lambda a, b: a >= b}


def _c_number(g, q, c, _):
    if c["op"] not in _OPS:
        raise HarnessError(f"number_compare op '{c['op']}' is not one the paper game knows")
    return _OPS[c["op"]](g.s["numbers"].get(c["number"], 0), c["value"])


def _c_ref(g, c):
    if c["ref"] not in g.ents:
        raise HarnessError(f"condition names {c['ref']}, which is not a ref of this run")
    return c["ref"]


CONDITIONS = {
    "stage_is": _c_stage("is"),
    "stage_at_least": _c_stage("at_least"),
    "stage_done": _c_stage("done"),
    "number_compare": _c_number,
    "in_faction": lambda g, q, c, _: c["faction"] in g.s["factions"],
    "rank_at_least": lambda g, q, c, _: g.s["factions"].get(c["faction"], -1) >= c["rank"],
    "item_count_at_least": lambda g, q, c, _: g.s["items"].get(g.item_of(c["item"]), 0) >= c["count"],
    "gold_at_least": lambda g, q, c, _: g.s["gold"] >= c["gold"],
    "skill_at_least": lambda g, q, c, _: g._skill(c["skill"]) >= c["value"],
    "alive": lambda g, q, c, _: g._alive(_c_ref(g, c)),
    "dead": lambda g, q, c, _: not g._alive(_c_ref(g, c)),
    "speaker_is": lambda g, q, c, sp: sp == _c_ref(g, c),
    "regard_at_least": lambda g, q, c, _: g.s["regard"].get(_c_ref(g, c), REGARD_START) >= c["value"],
    "race_is": lambda g, q, c, _: race_key(g.s["sheet"]["race"]) == race_key(c["value"]),
    "sex_is": lambda g, q, c, _: g.s["sheet"]["sex"].lower() == c["value"].lower(),
    "spoken_before": lambda g, q, c, sp: sp in g.s["spoken"],
    "not_spoken_before": lambda g, q, c, sp: sp not in g.s["spoken"],
}


def _r_item(sign):
    def f(g, q, r, _):
        item = g.item_of(r["item"])
        have = g.s["items"].get(item, 0)
        n = r["count"] if sign > 0 else min(have, r["count"])
        g.s["items"][item] = have + sign * n
        if not g.s["items"][item]:
            del g.s["items"][item]
        if not n:
            return []
        word = "Added" if sign > 0 else "Removed"
        return [f"{word}: {g.item_name(item)}" + (f" x{n}" if n > 1 else "")]
    return f


def _r_gold(sign):
    def f(g, q, r, _):
        n = r["amount"] if sign > 0 else min(g.s["gold"], r["amount"])
        g.s["gold"] += sign * n
        return [f"{n} gold {'added' if sign > 0 else 'removed'}"] if n else []
    return f


def _r_switch(on):
    def f(g, q, r, _):
        g.s["switched"][_c_ref(g, r)] = on
        return []
    return f


def _r_lock(locked):
    def f(g, q, r, _):
        g.s["locked"][_c_ref(g, r)] = locked
        return []
    return f


def _r_hostile(g, q, r, speaker):
    if speaker is None:
        raise HarnessError(f"{q}: speaker_hostile outside a line")
    g.s["hostile"].append(speaker)
    g.s["talking"] = None
    g.s["question"] = None
    return [f"{g.name(speaker)} attacks you!"]


def _r_number(add):
    def f(g, q, r, _):
        g.s["numbers"][r["number"]] = (g.s["numbers"].get(r["number"], 0) if add else 0) + r["value"]
        return []
    return f


def _r_regard(g, q, r, _):
    k = _c_ref(g, r)
    g.s["regard"][k] = max(REGARD_MIN, min(REGARD_MAX, g.s["regard"].get(k, REGARD_START) + r["by"]))
    return []


def _r_spell(teach):
    """A spell, power or ability learned or lost: the player is told by its name (the form's `names`), and `magic`
    lists what is known."""
    def f(g, q, r, _):
        known, name = g.s["spells"], g.spell_name(r["spell"])
        if teach and r["spell"] not in known:
            known.append(r["spell"])
            return [f"Learned: {name}"]
        if not teach and r["spell"] in known:
            known.remove(r["spell"])
            return [f"Forgotten: {name}"]
        return []
    return f


def _r_enemy(on):
    def f(g, q, r, _):
        if on and r["faction"] not in g.s["enemies"]:
            g.s["enemies"].append(r["faction"])
        elif not on and r["faction"] in g.s["enemies"]:
            g.s["enemies"].remove(r["faction"])
        return []
    return f


RESULTS = {
    # `if_held`: a stage's result that moves on only when the player already holds the item as the stage begins
    "set_stage": lambda g, q, r, sp: [] if "if_held" in r and not g.s["items"].get(g.item_of(r["if_held"]), 0)
    else g._set_stage(q, r["stage"], sp),
    "give_item": _r_item(1),
    "take_item": _r_item(-1),
    "give_gold": _r_gold(1),
    "take_gold": _r_gold(-1),
    "set_number": _r_number(False),
    "add_number": _r_number(True),
    "join_faction": lambda g, q, r, _: (g.s["factions"].setdefault(r["faction"], 0), [])[1],
    "set_rank": lambda g, q, r, _: (g.s["factions"].__setitem__(r["faction"], r["rank"]), [])[1],
    "change_regard": _r_regard,
    "switch_on": _r_switch(True),
    "switch_off": _r_switch(False),
    "lock_door": _r_lock(True),
    "unlock_door": _r_lock(False),
    # the thing (a container) becomes the player's, as SetActorOwner(the player's base): what it holds is not stolen
    "give_ownership": lambda g, q, r, _: (g.s["owned"].append(_c_ref(g, r)), [])[1],
    "show_message": lambda g, q, r, _: [f"[Message box] {r['text']}"],
    "speaker_hostile": _r_hostile,
    "start_quest": lambda g, q, r, sp: g._set_stage(r["quest"], r["stage"], None),
    "leave_faction": lambda g, q, r, _: (g.s["factions"].pop(r["faction"], None), [])[1],
    # a faction's people attack on sight (SetPlayerEnemy): the engine says nothing; who they are, the lines must show
    "make_enemy": _r_enemy(True),
    "make_peace": _r_enemy(False),
    "teach_spell": _r_spell(True),
    "forget_spell": _r_spell(False),
}
