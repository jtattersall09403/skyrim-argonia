"""`record --after`: earlier records played to a completed ending before the player starts (docs/design/paper-playtest.md).

Each earlier record is played by a shortest-path search over the record game's own state, by an able character who
passes every check and wins every fight. The search takes what a condition or action wants held, sets the flags a
condition reads, hears the topics a successor waits on, kills the people a condition needs dead and presses each
button of a choice; it never chooses a `fail` ending unless that stage is named."""
from __future__ import annotations

import copy
import json

from tools.playtest import record as R
from tools.playtest.game import HarnessError

MAX_STATES = 20000
CARRIED = ("items", "gold", "flags", "counters", "dead", "enabled", "doors", "skills", "ranks", "peace", "spells",
           "heard", "scenes")
KEY = ("stage", "done", "items", "gold", "flags", "dead", "counters", "enabled", "heard", "loaded", "doors",
       "taken", "ranks", "peace", "skills", "spells")


def _conds(q):
    for s in q.get("stages") or []:
        for sc in (s.get("successors") or []) + (s.get("failForward") or []):
            yield sc.get("when")
    for t in q.get("topics") or []:
        yield t.get("when")


def _acts(q):
    for s in q.get("stages") or []:
        yield s.get("onEnter")
    for e in q.get("endings") or []:
        yield e.get("world")
        yield e.get("rewards")


def _wants(q: dict) -> dict:
    """What the record's conditions and actions ask for: items, flags, topics, people."""
    w = {"items": set(), "flags": set(), "topics": set(), "npcs": set()}
    for c in _conds(q):
        for k, a in R._terms(c):
            args = R._args(a) if a is not None else []
            if k == "hasItem":
                w["items"].add(args[0])
            elif k == "flag":
                w["flags"].add(args[0])
            elif k == "topicHeardFrom":
                w["topics"].add(args[0])
            elif k == "npcAlive":
                w["npcs"].add(args[0])
    for acts in _acts(q):
        for k, a in R._actions(acts):
            if k in ("takeItem", "removeItem"):
                w["items"].add(a[0])
    return w


class Search:
    def __init__(self, q, earlier_qs, state):
        self.q, self.earlier_qs = q, earlier_qs
        self.want = _wants(q)
        self.g0 = self.make(state)

    def make(self, state):
        g = R.Game(self.q, state, earlier=self.earlier_qs)
        g.word = "pass"
        return g

    def clone(self, g):
        return self.make(copy.deepcopy(g.s))

    def settle(self, g):
        """What an able character does without being asked, then the stages that follow, until nothing changes."""
        for _ in range(200):
            before = self.key(g)
            for ref, row in g.R.rows.items():
                if row.get("kind") not in ("thing", None) or ref in g.s["taken"] or not g._enabled(ref):
                    continue
                iid = g.R.item_id(ref)
                if iid in self.want["items"] or ref in self.want["items"]:
                    g.s["taken"].append(ref)
                    g.s["items"][iid] = g.s["items"].get(iid, 0) + (row.get("count") or 1)
            for h in g.R.hooks:
                if h.get("setsFlag") in self.want["flags"]:
                    g.s["flags"][h["setsFlag"]] = True
            g.advance()
            g.s["pending"].clear()
            if g.s["ask_name"]:
                g.s["ask_name"], g.s["name"] = False, "Player"
            if self.key(g) == before:
                return
        raise HarnessError(f"{g.R.id}: the stages move in a loop")

    @staticmethod
    def key(g) -> str:
        return json.dumps({k: g.s[k] for k in KEY}, sort_keys=True, default=str)

    def moves(self, g):
        if g.s["choice"]:
            for b in g.s["choice"]["buttons"]:
                c = self.clone(g)
                c.s["choice"] = None
                c.enter(b["sets"])
                yield c
            return
        for t in g.R.topics:
            who = t.get("person")
            if t["id"] not in self.want["topics"] or [t["id"], who] in g.s["heard"] or not g._alive(who):
                continue
            if t.get("stages") and g.s["stage"] not in t["stages"] or not g.holds(t.get("when"), lenient=True):
                continue
            c = self.clone(g)
            c._said(t)
            yield c
        for n in sorted(self.want["npcs"]):
            if g._alive(n):
                c = self.clone(g)
                c.s["dead"].append(n)
                yield c

    def run(self, ending, label):
        g = self.g0
        qid = g.R.id
        sw = self.q.get("startWhen")
        if sw and not g.holds(sw, lenient=True):
            raise HarnessError(f"--after {label}: the state before it does not satisfy its startWhen {sw}")
        if ending is not None and not (g.R.stages.get(ending) or {}).get("ending"):
            raise HarnessError(f"--after {label}: stage {ending} is not an ending stage of {qid}")
        g.s["at"] = None
        g.enter(g.R.start)
        self.settle(g)
        seen, frontier = {self.key(g)}, [g]
        while frontier:
            nxt = []
            for g in frontier:
                if g.s["ended"] and not g.s["choice"]:
                    if (g.s["stage"] == ending) if ending is not None else g.s["ended"] != "fail":
                        return g
                    continue
                for c in self.moves(g):
                    self.settle(c)
                    k = self.key(c)
                    if k in seen:
                        continue
                    seen.add(k)
                    if len(seen) > MAX_STATES:
                        raise HarnessError(f"--after {label}: no ending found in {MAX_STATES} states")
                    nxt.append(c)
            frontier = nxt
        raise HarnessError(f"--after {label}: {qid} cannot reach "
                           + (f"ending stage {ending}" if ending is not None else "a completed ending")
                           + " by an able character")


def play_before(specs) -> tuple[list[dict], dict]:
    """specs: [(record, ending stage or None, path)]. Returns the earlier quests [{path, ending, record}] and the
    state the played quest starts from."""
    shared = R.Game._fresh(None)
    done = []
    for q, ending, path in specs:
        bad = R.check(q)
        if bad:
            raise HarnessError(f"--after {path}: the record has {len(bad)} fault(s):\n  " + "\n  ".join(bad))
        st = copy.deepcopy(shared)
        g = Search(q, [d["record"] for d in done], st).run(ending, path)
        for k in CARRIED:
            shared[k] = g.s[k]
        shared["loaded"] = g.s["loaded"]
        shared["loaded"][q["id"]] = {"stage": g.s["stage"], "done": g.s["done"], "ended": g.s["ended"]}
        done.append({"path": str(path), "ending": g.s["stage"], "record": q})
    return done, shared
