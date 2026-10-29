"""Named checks: the world's rules that SQL constraints cannot state (decision 0030 §3).

Each check reads the loaded world through db.World and returns one line per violation. The load itself (types,
keys, foreign keys, CHECKs) is the rest of the integrity gate; a rule goes here only when the schema cannot hold it:
a column whose target table depends on another column or on the value's prefix, and the vocabulary's argument
shapes, which are prose in `condition_term.args`.
"""
from __future__ import annotations

import re
from typing import Callable

CHECKS: dict[str, tuple[Callable, tuple[str, ...]]] = {}


def check(name: str, *tables: str):
    """Register a named check over `tables`; it runs on a world whose schema has them all (a test's small schema
    skips it)."""
    def deco(fn):
        CHECKS[name] = (fn, tables)
        return fn
    return deco


def run(w, only: list[str] | None = None) -> list[str]:
    out = []
    for name, (fn, tables) in CHECKS.items():
        if (only and name not in only) or not set(tables) <= set(w.tables):
            continue
        out += [f"[{name}] {e}" for e in fn(w)]
    return out


# -- polymorphic references ------------------------------------------------------------------------------------
LOCK_OWNER = {"person": "npc", "household": "npc", "faction": "faction"}  # a household is named by its head


@check("lock-owner", "lock", "npc", "faction")
def lock_owner(w) -> list[str]:
    """lock.owner_id names a row of the table its owner_kind says (person, household -> npc; faction)."""
    out = []
    for r in w.query('SELECT id, owner_kind, owner_id FROM "lock" ORDER BY id'):
        table = LOCK_OWNER.get(r["owner_kind"])
        if table is None:
            out.append(f"lock {r['id']}: owner_kind {r['owner_kind']!r} has no owner table in checks.LOCK_OWNER")
        elif w.get(table, r["owner_id"]) is None:
            out.append(f"lock {r['id']}: owner {r['owner_kind']} {r['owner_id']!r} has no row in {table}")
    return out


@check("journal-grounding", "journal_entry_grounding", "fact", "promise")
def journal_grounding(w) -> list[str]:
    """journal_entry_grounding.value is a fact id or a promise id."""
    return [f"journal_entry {r[0]}: groundedIn {r[1]!r} is neither a fact nor a promise"
            for r in w.query("SELECT journal_entry_id, value FROM journal_entry_grounding g "
                             "WHERE value NOT IN (SELECT id FROM fact) AND value NOT IN (SELECT id FROM promise) "
                             "ORDER BY 1, ord")]


@check("quest-topic", "quest_topic", "quest_essential_topic", "topic")
def quest_topic(w) -> list[str]:
    """A quest's topic is a topic row, or is marked `new` (2.5 adds it); an essential topic is a topic row or one
    of the quest's `new` topics (quest-record.md, field 12)."""
    out = [f"quest {r[0]}: topic {r[1]!r} is not a topic row and is not marked new"
           for r in w.query("SELECT quest_id, id FROM quest_topic WHERE NOT coalesce(new, 0) "
                            "AND id NOT IN (SELECT id FROM topic) ORDER BY 1, ord")]
    out += [f"quest {r[0]}: essential topic {r[1]!r} is neither a topic row nor one of the quest's new topics"
            for r in w.query("SELECT quest_id, value FROM quest_essential_topic e "
                             "WHERE value NOT IN (SELECT id FROM topic) AND NOT EXISTS (SELECT 1 FROM quest_topic t "
                             "WHERE t.quest_id = e.quest_id AND t.id = e.value AND t.new) ORDER BY 1, ord")]
    return out


# -- the vocabulary's argument shapes --------------------------------------------------------------------------
def _split(args: str) -> list[str]:
    """Top-level comma parts of an args shape (commas inside {...} or (...) belong to their part)."""
    parts, depth, cur = [], 0, ""
    for ch in args:
        depth += ch in "{(" and 1 or ch in "})" and -1 or 0
        if ch == "," and depth == 0:
            parts.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur.strip())
    return parts


DEFAULTABLE = re.compile(r"(`bool`|\bbool|\bcount)$")   # a trailing flag (true) or count (1) may be left out


def arity(args: str | None) -> tuple[int, int]:
    """(fewest, most) arguments an args shape allows. `none` is no argument; `a *or* b + c` takes one or two;
    `optional ...` may be left out; a trailing `bool` or count may be left out (flag(x) is flag(x, true),
    hasItem(x) is hasItem(x, 1): how every authored record writes them)."""
    if not args or args.strip() == "none":
        return 0, 0
    lo = hi = 0
    parts = _split(re.sub(r"\([^)]*\)", "", args))
    for i, part in enumerate(parts):
        alts = [a.count("+") + 1 for a in re.split(r"\*or\*", part)]
        a_lo, a_hi = min(alts), max(alts)
        if part.startswith("optional"):
            a_lo = 0
        hi += a_hi
        lo += a_lo
    # trailing defaultable parts lower the minimum
    for part in reversed(parts):
        if DEFAULTABLE.search(part.strip()) and not part.startswith("optional"):
            lo -= 1
        else:
            break
    return lo, hi


@check("term-arity", "condition_term", "condition", "condition_arg", "action", "action_arg")
def term_arity(w) -> list[str]:
    """Every condition node and action has the argument count its vocabulary term's shape allows; a combinator
    has no arguments and its children (all/any: at least one; not: exactly one)."""
    shapes = {r["id"]: (r["kind"], arity(r["args"]) if r["kind"] != "combinator" else (0, 0))
              for r in w.query("SELECT id, kind, args FROM condition_term")}
    out = []
    for r in w.query("SELECT c.id, c.term, (SELECT count(*) FROM condition_arg a WHERE a.condition_id = c.id), "
                     "(SELECT count(*) FROM condition k WHERE k.parent_id = c.id) FROM condition c ORDER BY c.id"):
        cid, term, n, kids = r
        kind, (lo, hi) = shapes[term]
        if kind == "action":
            out.append(f"condition {cid}: {term} is an action verb, not a predicate")
        elif not lo <= n <= hi:
            out.append(f"condition {cid}: {term} takes {lo}-{hi} argument(s), has {n}")
        if kind == "combinator" and not (kids == 1 if term == "not" else kids >= 1):
            out.append(f"condition {cid}: {term} has {kids} child condition(s)")
        if kind != "combinator" and kids:
            out.append(f"condition {cid}: predicate {term} has {kids} child condition(s)")
    for r in w.query("SELECT a.list_id, a.ord, a.term, (SELECT count(*) FROM action_arg x WHERE x.list_id = a.list_id "
                     "AND x.ord = a.ord) FROM action a ORDER BY 1, 2"):
        lid, ord_, term, n = r
        kind, (lo, hi) = shapes[term]
        if kind != "action":
            out.append(f"action {lid}[{ord_}]: {term} is a {kind}, not an action verb")
        elif not lo <= n <= hi:
            out.append(f"action {lid}[{ord_}]: {term} takes {lo}-{hi} argument(s), has {n}")
    return out
