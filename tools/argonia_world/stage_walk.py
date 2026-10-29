"""Walk a quest's stage graph in data (2.12 §a's L2 check; 1.4's first rung): every successor and fail-forward of
every stage is driven by a world state that satisfies its condition, and the stage's transition rule must take it.

The rule the generator implements: at a stage, fail-forwards are tested first (a death or a deadline overrides
progress), then successors, each in record order; the first whose condition holds is taken. A witness state is
built from the edge's own condition (all: every child; any: each child in turn; not npcAlive: that person dead),
so an edge that an earlier edge shadows, a dangling target, an ending that cannot be reached or a non-ending stage
with no way out are all failures.

    from tools.argonia_world import db, stage_walk
    report = stage_walk.walk(db.open(), "quest.local.lf83")   # raises nothing; report.errors lists every failure
"""
from __future__ import annotations

import dataclasses
import itertools

from tools.argonia_world import quest_record


@dataclasses.dataclass
class State:
    """The facts the vocabulary's predicates read, as sets and maps (no engine)."""
    heard: set = dataclasses.field(default_factory=set)         # (topic, npc)
    known: set = dataclasses.field(default_factory=set)         # topic
    items: dict = dataclasses.field(default_factory=dict)       # item -> count
    flags: dict = dataclasses.field(default_factory=dict)       # flag -> bool
    dead: set = dataclasses.field(default_factory=set)          # npc
    days: dict = dataclasses.field(default_factory=dict)        # event -> days since
    done: set = dataclasses.field(default_factory=set)          # (quest, objective)
    disposition: dict = dataclasses.field(default_factory=dict)

    def merged(self, other: "State") -> "State":
        return State(self.heard | other.heard, self.known | other.known, {**self.items, **other.items},
                     {**self.flags, **other.flags}, self.dead | other.dead, {**self.days, **other.days},
                     self.done | other.done, {**self.disposition, **other.disposition})


class Unsupported(Exception):
    pass


def holds(c, s: State, objectives: dict) -> bool:
    """Evaluate a condition tree (the record's form) against a state. `objectives`: (quest, id) -> condition."""
    (term, a), = c.items()
    args = a if isinstance(a, list) else [a]
    if term == "all":
        return all(holds(k, s, objectives) for k in a)
    if term == "any":
        return any(holds(k, s, objectives) for k in a)
    if term == "not":
        return not holds(a, s, objectives)
    if term == "topicHeardFrom":
        return (args[0], args[1]) in s.heard
    if term == "knowsTopic":
        return args[0] in s.known or any(t == args[0] for t, _ in s.heard)
    if term == "hasItem":
        return s.items.get(args[0], 0) >= (args[1] if len(args) > 1 else 1)
    if term == "flag":
        return s.flags.get(args[0], False) == (args[1] if len(args) > 1 else True)
    if term == "npcAlive":
        return args[0] not in s.dead
    if term == "daysSince":
        return s.days.get(args[0], -1) >= args[1]
    if term == "dispositionAtLeast":
        return s.disposition.get(args[0], 50) >= args[1]
    if term == "objectiveComplete":
        key = (args[0], args[1])
        return key in s.done or (key in objectives and holds(objectives[key], s, objectives))
    raise Unsupported(term)


def witnesses(c, objectives: dict) -> list[State]:
    """States that each make `c` hold (one per alternative of every `any`)."""
    (term, a), = c.items()
    args = a if isinstance(a, list) else [a]
    if term == "all":
        out = [State()]
        for k in a:
            out = [x.merged(y) for x, y in itertools.product(out, witnesses(k, objectives))]
        return out
    if term == "any":
        return [w for k in a for w in witnesses(k, objectives)]
    if term == "not":
        (t2, a2), = a.items()
        if t2 == "npcAlive":
            return [State(dead={a2 if not isinstance(a2, list) else a2[0]})]
        raise Unsupported(f"not {t2}")
    if term == "topicHeardFrom":
        return [State(heard={(args[0], args[1])})]
    if term == "knowsTopic":
        return [State(known={args[0]})]
    if term == "hasItem":
        return [State(items={args[0]: args[1] if len(args) > 1 else 1})]
    if term == "flag":
        return [State(flags={args[0]: args[1] if len(args) > 1 else True})]
    if term == "npcAlive":
        return [State()]
    if term == "daysSince":
        return [State(days={args[0]: args[1]})]
    if term == "dispositionAtLeast":
        return [State(disposition={args[0]: args[1]})]
    if term == "objectiveComplete":
        key = (args[0], args[1])
        if key not in objectives:
            raise Unsupported(f"objectiveComplete {key}: no such objective")
        return witnesses(objectives[key], objectives)
    raise Unsupported(term)


def _npcs(conds) -> set:
    out = set()
    for c in conds:
        (term, a), = c.items()
        if term in ("all", "any"):
            out |= _npcs(a)
        elif term == "not":
            out |= _npcs([a])
        else:
            out |= {x for x in (a if isinstance(a, list) else [a]) if isinstance(x, str) and x.startswith("npc.")}
    return out


def _killed(c) -> set:
    """The people whose death alone makes `c` hold."""
    (term, a), = c.items()
    if term == "any":
        return {x for k in a for x in _killed(k)}
    if term == "not":
        (t2, a2), = a.items()
        if t2 == "npcAlive":
            return {a2 if not isinstance(a2, list) else a2[0]}
    return set()


def step(stage: dict, s: State, objectives: dict):
    """The stage the rule takes from `stage` in state `s`, or None."""
    for e in (stage.get("failForward") or []) + (stage.get("successors") or []):
        if holds(e["when"], s, objectives):
            return e["to"]
    return None


@dataclasses.dataclass
class Report:
    edges: list = dataclasses.field(default_factory=list)       # (from, to, kind, witness index) walked green
    reached: set = dataclasses.field(default_factory=set)
    errors: list = dataclasses.field(default_factory=list)


def walk(w, quest_id: str) -> Report:
    return walk_record(quest_record.export(w, quest_id))


def walk_record(q: dict) -> Report:
    """Walk a record in its YAML-view form (as exported), so a test can walk a mutated copy without writing it."""
    quest_id = q["id"]
    stages = {s["id"]: s for s in q.get("stages") or []}
    objectives = {(quest_id, o["id"]): o["completeWhen"] for s in stages.values() for o in s.get("objectives") or []}
    r = Report()
    start = q.get("start", min(stages))
    todo, seen = [start], set()
    while todo:
        sid = todo.pop()
        if sid in seen:
            continue
        seen.add(sid)
        st = stages.get(sid)
        if st is None:
            r.errors.append(f"stage {sid}: no such stage")
            continue
        edges = [(e, "failForward") for e in st.get("failForward") or []] + \
                [(e, "successor") for e in st.get("successors") or []]
        if st.get("ending"):
            if edges:
                r.errors.append(f"stage {sid}: an ending stage has ways out")
            continue
        if not edges:
            r.errors.append(f"stage {sid}: not an ending and no way out")
        for e, kind in edges:
            if e["to"] not in stages:
                r.errors.append(f"stage {sid} -> {e['to']}: no such stage")
                continue
            try:
                ws = witnesses(e["when"], objectives)
            except Unsupported as x:
                r.errors.append(f"stage {sid} -> {e['to']}: the walker cannot drive {x}")
                continue
            for i, ws_ in enumerate(ws):
                got = step(st, ws_, objectives)
                if got != e["to"]:
                    r.errors.append(f"stage {sid} -> {e['to']} ({kind}, witness {i}): the rule takes {got}")
                else:
                    r.edges.append((sid, e["to"], kind, i))
            todo.append(e["to"])
    r.reached = seen
    for sid, st in stages.items():
        if st.get("ending"):
            continue
        named = _npcs([o["completeWhen"] for o in st.get("objectives") or []] +
                      [e["when"] for e in st.get("successors") or []])
        dies = {x for e in st.get("failForward") or [] for x in _killed(e["when"])}
        for npc in sorted(named - dies):
            r.errors.append(f"stage {sid}: names {npc} but has no fail-forward for their death (old 0138)")
    for sid, st in stages.items():
        if sid not in seen:
            r.errors.append(f"stage {sid}: unreachable from the start ({start})")
    return r
