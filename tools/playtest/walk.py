"""The walker (docs/design/paper-playtest.md): the paper game played by itself, breadth first over the commands a
player could give, so the first path found to a state is a shortest one. Deterministic: the same forms give the same
paths.

- `complete(game, quest)` plays one quest to a completed ending along a shortest path (for `--after`), or raises a
  HarnessError saying what was found;
- `reach(forms)` proves, for each quest of a set, every stage and every ending reachable, for each character of
  `SHEETS`, from each distinct state the completed endings of the quests it waits on can leave (`Reads`); each one
  not reached is named, and a search cut at its limit says so (never that no path exists).

It tries what the quest could ask of a player: say every quest line on offer, talk to everyone, take every thing that
is not a container, use every door, container, readable or used thing, open containers, pick locks with lockpicks
held, pickpocket and search bodies (always unseen), fight a person who is hostile, who-must-live, watched by a death
trigger or needed dead by a condition (always won), and go to every person, thing and door. It acts on
the walked quest's own refs first, and on every loaded ref only when that leaves a goal unreached. A person's own
topics outside the forms move nothing and are not tried.
"""
from __future__ import annotations

import json
import time
from collections import deque
from pathlib import Path

from tools.playtest import game as G
from tools.playtest.vocab import HarnessError

MAX_STATES = 50000   # the states a search looks through before it is cut (and says so)
# A search over every loaded ref, after the walked quest's own leave a goal unreached, looks this much less far: a
# quest of the form names every ref it needs, so the wider search seldom finds more and costs most of the time.
FALLBACK_SHARE = 10
PROOFS = 3           # the paths found earlier to one goal that are tried from another state before it is searched
# The characters `reach` plays, each with this much gold: one able in every skill, and a new character.
GOLD = 1000
ABLE = G.new_sheet("Argonian", "female", **{s.replace(" ", "").replace("-", ""): 100 for s in G.SKILLS})
SHEETS = {"able": ABLE, "new": G.new_sheet("Argonian", "female")}


def _copy(s: dict) -> dict:
    """A state copied as deep as the game changes it in place: its lists, its tables (a quest's own lists, a
    container's rows); the sheet, the position, a waiting question and an ended quest's own lists are never
    changed in place."""
    out = s.copy()
    for k, v in s.items():
        t = type(v)
        if t is list:
            out[k] = v.copy()
        elif t is dict and v and k not in _WHOLE:
            if k == "quests":
                out[k] = {q: st if st["ended"] else {a: x.copy() if type(x) is list else x for a, x in st.items()}
                          for q, st in v.items()}
            else:
                out[k] = {a: x.copy() if type(x) is dict or type(x) is list else x for a, x in v.items()}
        elif t is dict and k not in _WHOLE:
            out[k] = {}
    return out


_WHOLE = frozenset(("sheet", "pos", "question"))


def _key(s: dict, spoken: bool) -> str:
    """A state as far as what can happen next goes: lists as sets; who was spoken to only when a condition asks; who
    the player is talking to only while a question waits (any topic is one `talk` away); where the player stands only
    while a container is open or a question waits (any person, thing or door is one `go` away)."""
    drop = {"commands", "visited", "crimes", "travel"} | (set() if spoken else {"spoken"}) | \
        (set() if s["question"] else {"talking"}) | (set() if s["opened"] or s["question"] else {"pos"})
    return json.dumps({k: sorted(v) if k in ("taken", "dead", "fired", "spoken", "opened", "hostile", "spells",
                                                    "enemies", "perks", "mapped", "rooms", "ingredients") else v
                       for k, v in s.items() if k not in drop}, sort_keys=True)


def _asks_spoken(g) -> bool:
    return any(c["is"] in ("spoken_before", "not_spoken_before")
               for f in g.forms.values() for ln in f["lines"] for c in ln["conditions"])


def _fightable(g) -> set[str]:
    """Who a fight can help against: the hostile, who must live, a death trigger's (of a quest not ended), and a person
    a line needs dead. A death that could only shut a line needing them alive is never tried (what they carry is
    pickpocketed)."""
    out = {e for e, x in g.ents.items() if x["hostile"]}
    for q, f in g.forms.items():
        if not (g.s["quests"].get(q) or {}).get("ended"):
            out |= {m["ref"] for m in f["must_live"]}
            out |= {t["ref"] for t in f["triggers"] if t["kind"] == "death"}
        out |= {c["ref"] for ln in f["lines"] for c in ln["conditions"]
                if (c["is"] == "dead") != bool(c.get("not")) and c["is"] in ("alive", "dead")}
    return out


def _at(g, e, fightable, used, picks) -> list[tuple]:
    """What can be done to one person, thing or door standing beside it, as steps (verb, id, the words after)."""
    s, x, out = g.s, g.ents[e], []
    if x["kind"] == "person":
        if g._alive(e):
            if not (x["hostile"] or e in s["hostile"]):
                out.append(("talk", e, ""))
                if g._listing(e):
                    out.append(("pickpocket", e, ""))
            if e in fightable:
                out.append(("fight", e, "win"))
        elif g._listing(e):
            out.append(("use", e, ""))
        return out
    if x["kind"] == "door" or e in g.holders or g._text(e) or e in used:
        out.append(("use", e, "unseen"))
    if x["kind"] == "thing" and e not in g.holders:
        out.append(("take", e, "unseen"))
    if picks and g._locked(e) and (x["lock"] or {}).get("level") != "key":
        out.append(("pick", e, "win unseen"))
    return out


def actions(g, fightable: set[str], speakers: set[str], refs: set[str] | None = None) -> list[tuple]:
    """Every move worth trying now, each a tuple of steps, on `refs` only when given. Going somewhere is never a move
    of its own (but to a person who speaks first): it is the first step of doing something there, so only the places
    acted at count."""
    s, out = g.s, []
    if s["talking"] and s["question"]:
        out += [(("say", None, str(i), m[0]),) for i, m in enumerate(g._answers(), 1) if m[1] == "line"]
    used = {t["ref"] for f in g.forms.values() for t in f["triggers"] if t["kind"] == "use"}
    picks = s["items"].get(G.LOCKPICK, 0) > 0
    here = [e for e in g._visible() if refs is None or e in refs]
    for e in here:
        out += [(step,) for step in _at(g, e, fightable, used, picks)]
    for h in s["opened"]:
        if h in g.ents and g._near(h):
            out += [(("take", k, "unseen"),) for _, k in g._inside(h)]
    for e, x in g.ents.items():
        if e in here or x["kind"] == "marker" or not g._loose(e) or not g._on(e) or g._pos(e) is None or \
                (refs is not None and e not in refs):
            continue
        go = ("go", e, "")
        if e in speakers:
            out.append((go,))
        out += [(go, step) for step in _at(g, e, fightable, used, picks)]
    return out


def command(step) -> str:
    verb, e, rest = step[:3]
    return " ".join(w for w in (verb, f"#{e}" if e else "", rest) if w)


def shown(g, step) -> str:
    """A step as a player would type it: names, not ids; a line by its words."""
    verb, e, rest = step[:3]
    if e is None:
        return f"say {step[3]}" if len(step) > 3 else command(step)
    name = g.item_name(e.split("|", 1)[1]) if "|" in e else g.name(e)
    return " ".join(w for w in (verb, name, rest.replace("unseen", "").strip()) if w)


def search(g, goals: dict, over=None, max_states: int = MAX_STATES, refs: set[str] | None = None, key=None) -> dict:
    """Breadth first from the game's state, acting on `refs` first (when given) and on every ref only when that
    leaves a goal unreached. `goals` {name: test(state)}; a state `over(state)` holds for is not played on. Talking to
    someone is followed at once by each quest line on offer. Returns {"paths": {name: [step...]}, "stages": {quest:
    stages seen}, "states": n, "cut": the search hit max_states, "errors": harness errors met}. `key(state)` says
    which states are one (default `_key`; `Reads.key` for a quest whose goals are its own stages)."""
    return Search(g, over, max_states, refs, key).answer(goals)


class TimeLimit(Exception):
    """A search ran past its deadline: `states` searched, `missing` the goals not yet found."""

    def __init__(self, states: int, missing: list[str]):
        super().__init__(f"{states} states searched")
        self.states, self.missing = states, missing


class Explorer:
    """One breadth-first search from one state, kept: the order states are met in does not depend on the goals, so
    every set of goals asked of it is answered from the states already met, and the search goes on only as far as a
    goal not yet found needs. Each answer is the one a search for those goals alone would give. A goal reads a
    state's quests (`state["quests"]`), the one part of each state met that is kept. The explorer plays on its game
    `g`, whose state is the start again after each answer."""

    def __init__(self, g, over, max_states, refs, key=None, deadline: float | None = None, reads=()):
        """`reads`: the fields of a state `key` reads (pos and talking only while a container is open or a question
        waits): a state equal to the one it was reached from in them is that state again."""
        self.g, self.over, self.max_states, self.refs, self.deadline = g, over, max_states, refs, deadline
        self.reads = reads
        self.start = _copy(g.s)
        self.fightable = _fightable(g)
        self.speakers = {ln["speaker"] for f in g.forms.values() for ln in f["lines"] if ln["kind"] == "speaks_first"}
        spoken = _asks_spoken(g)
        self.key = key or (lambda s: _key(s, spoken))
        self.seen = {self.key(self.start)}
        self.todo = deque([(self.start, None, ())])     # (state, the met state it was reached from, the steps)
        self.met: list[tuple] = []      # each state taken from the queue: (its quests, from, steps, seen, errors)
        self.last = None                # the last state met, while it is not yet played on
        self.errors: list[str] = []
        self.cut = False

    def path(self, i: int) -> list:
        """The steps to the i-th state met."""
        out = []
        while i is not None:
            _, i, steps = self.met[i][:3]
            out.append(steps)
        return [step for steps in reversed(out) for step in steps]

    def _run(self, s, steps):
        g = self.g
        g.s = _copy(s)
        try:
            for step in steps:
                g.do(command(step))
        except HarnessError as e:
            if str(e) not in self.errors:
                self.errors.append(str(e))
            return None
        return g.s

    def _push(self, s, i, steps, parent=None) -> bool:
        if parent is not None and self.reads and all(s[f] == parent[f] for f in self.reads) and \
                (not (parent["opened"] or parent["question"]) or
                 (s["pos"] == parent["pos"] and s["talking"] == parent["talking"])):
            return False                    # the state it came from, met already
        k = self.key(s)
        if k not in self.seen:
            self.seen.add(k)
            self.todo.append((s, i, steps))
        return len(self.seen) >= self.max_states

    def _play(self, s, i):
        """Every move from `s` (the i-th state met), each state not met before queued. A move that goes somewhere
        first goes there once for all that is done there."""
        g = self.g
        g.s = s
        gone = {}
        for a in actions(g, self.fightable, self.speakers, self.refs):
            if len(a) == 2 and a[0][0] == "go":
                e = a[0][1]
                if e not in gone:
                    gone[e] = self._run(s, a[:1])
                s1 = None if gone[e] is None else self._run(gone[e], a[1:])
            else:
                s1 = self._run(s, a)
            if s1 is None:
                continue
            if a[-1][0] == "talk" and s1["talking"] and not s1["question"]:
                lines = [(("say", None, str(n), m[0]),) for n, m in enumerate(g._menu(s1["talking"]), 1)
                         if m[1] == "line"]
                for say in lines:
                    s2 = self._run(s1, say)
                    if s2 is not None and self._push(s2, i, a + say, s):
                        self.cut = True
                        return
            if self._push(s1, i, a, s):
                self.cut = True
                return

    def _more(self) -> bool:
        """Meet the next state: play on the last one met (unless it is over), then take the next from the queue.
        False when there is none (the search is done, or cut)."""
        if self.last is not None:
            s = self.last
            if not (self.over and self.over(s)):
                if self.deadline is not None and time.monotonic() > self.deadline:
                    raise TimeLimit(len(self.seen), [])
                quiet, self.g.quiet = self.g.quiet, True
                try:
                    self._play(s, len(self.met) - 1)
                finally:
                    self.g.s, self.g.quiet = _copy(self.start), quiet
            self.last = None
        if self.cut or not self.todo:
            return False
        s, i, steps = self.todo.popleft()
        self.met.append((s["quests"], i, steps, len(self.seen), len(self.errors)))
        self.last = s
        return True

    def answer(self, goals: dict) -> dict:
        """As `search` over this explorer's refs alone."""
        found, stages, i = {}, {}, 0
        if not goals:
            return {"paths": {}, "stages": {}, "states": 1, "cut": False, "errors": []}
        while True:
            if i == len(self.met):
                try:
                    if not self._more():
                        break
                except TimeLimit as e:
                    raise TimeLimit(e.states, [n for n in goals if n not in found]) from None
            quests, _, _, n, errs = self.met[i]
            for q, st in quests.items():
                stages.setdefault(q, set()).update(st["done"])
            view = {"quests": quests}
            for name, test in goals.items():
                if name not in found and test(view):
                    found[name] = i
            if len(found) == len(goals):
                break
            i += 1
        out = {"paths": {name: self.path(j) for name, j in found.items()},
               "stages": {q: sorted(v) for q, v in stages.items()}}
        if len(found) == len(goals):
            return {**out, "states": n, "cut": False, "errors": self.errors[:errs]}
        return {**out, "states": len(self.seen), "cut": self.cut, "errors": list(self.errors)}


class Search:
    """`search` kept for more goals: an explorer over `refs`, and (made only when needed) one over every ref, both
    from the state `g` holds now."""

    def __init__(self, g, over, max_states, refs, key=None, reads=()):
        self.args, self.start, self.reads = (over, max_states, refs, key), _copy(g.s), reads
        self.first = Explorer(g, over, max_states, refs, key, reads=reads)
        self.wide = None

    def answer(self, goals: dict, deadline: float | None = None) -> dict:
        """The answer for `goals`; past `deadline` (time.monotonic()) a TimeLimit."""
        over, max_states, refs, key = self.args
        for x in (self.first, self.wide):
            if x is not None:
                x.deadline = deadline
        if refs is not None:
            res = self.first.answer(goals)
            if len(res["paths"]) == len(goals) or res["cut"]:      # a cut search would only be cut again
                return res
            if self.wide is None:
                g = self.first.g
                g.s = _copy(self.start)
                self.wide = Explorer(g, over, max_states // FALLBACK_SHARE, None, key, deadline, self.reads)
            return self.wide.answer(goals)
        return self.first.answer(goals)


def _stops(res, q, g) -> str:
    """What the search found, truthfully: not found within its limit when cut, else that no path reaches it."""
    st = res["stages"].get(q)
    where = (f"not found within {res['states']} states (the search was cut)" if res["cut"] else
             "no path reaches it") + ("; the quest never starts" if not st else
                                     f"; stages reached: {', '.join(map(str, st))}")
    if res["errors"]:
        where += f"; harness error: {res['errors'][0]}"
    return where


def _replay(g, start: dict, path: list, test) -> list | None:
    """The steps of `path` played from `start` up to the first state `test` holds for; None when none does."""
    g.s = _copy(start)
    try:
        for j in range(len(path) + 1):
            if test(g.s):
                return path[:j]
            if j < len(path):
                g.do(command(path[j]))
    except HarnessError:
        pass
    return None


def _ended(q):
    """A state where quest `q` has ended: the search plays no further from it."""
    return lambda s: bool((s["quests"].get(q) or {}).get("ended"))


def own_refs(g, q: str) -> set[str]:
    return {r["id"] for r in g.forms[q]["refs"]}


def complete(g, q: str, max_states: int = MAX_STATES, ending: int | None = None, key=None) -> list[tuple[str, str]]:
    """Play quest `q` to a completed ending (or to the stage `ending`) along a shortest path; the game keeps the state
    it leaves. Returns the (command as typed, what it showed) of each step."""
    def done(s):
        st = s["quests"].get(q)
        return st is not None and (st["ended"] == "completed" if ending is None else ending in st["done"])
    res = search(g, {"done": done}, _ended(q), max_states, own_refs(g, q), key)
    if "done" not in res["paths"]:
        raise HarnessError(f"--after {q}: {'no completed ending' if ending is None else f'stage {ending}'} reached "
                           f"from here: {_stops(res, q, g)}")
    return [(shown(g, a), g.do(command(a))) for a in res["paths"]["done"]]


# -- reach: every ending of a set of forms ------------------------------------------------------------------------

def waits_on(f: dict, forms: dict) -> set[str]:
    """The other loaded quests a form waits on: its start (the quest whose stage starts it, or whose start_quest result
    does), its quest-stage triggers, the quests its conditions name,
    and the quests that set a number it reads or give an item it checks."""
    q = f["quest"]["id"]
    out = {t["quest"] for t in f["triggers"] if t["kind"] == "quest_stage"}
    if f["quest"]["start"]["by"] == "quest_stage":
        out.add(f["quest"]["start"]["quest"])
    conds = [c for ln in f["lines"] for c in ln["conditions"]]
    out |= {c["quest"] for c in conds if "quest" in c}
    numbers = {c["number"] for c in conds if c["is"] == "number_compare"}
    items = {c["item"] for c in conds if c["is"] == "item_count_at_least"}
    own = {r["id"] for r in f["refs"]}
    for o, g in forms.items():
        if o == q:
            continue
        rs = [r for s in g["stages"] for r in s["results"]] + [r for ln in g["lines"] for r in ln["results"]]
        if f["quest"]["start"]["by"] == "start_quest" and any(r["do"] == "start_quest" and r["quest"] == q for r in rs):
            out.add(o)
        if any(r.get("number") in numbers for r in rs if r["do"] in ("set_number", "add_number")) or \
                any(r["item"] in items - own for r in rs if r["do"] == "give_item"):
            out.add(o)
    out.discard(q)
    return {x for x in out if x in forms}


def order(q: str, forms: dict) -> list[str]:
    """The quests `q` waits on, each after those it waits on in turn (q itself last)."""
    out: list[str] = []

    def visit(x, path):
        if x in out or x in path:
            return
        for d in sorted(waits_on(forms[x], forms)):
            visit(d, path | {x})
        out.append(x)
    visit(q, set())
    return out


def named(qs: list[str], forms: dict) -> list[str]:
    """`qs` and every loaded quest they name in turn (a start_quest result, a condition, a trigger, a start), as the
    game must load them; in the order given, then form order."""
    out, todo = list(qs), list(qs)
    while todo:
        f = forms[todo.pop()]
        rs = [r for s in f["stages"] for r in s["results"]] + [r for ln in f["lines"] for r in ln["results"]]
        more = {r["quest"] for r in rs if r["do"] == "start_quest"} | waits_on(f, forms)
        for x in sorted(more & set(forms)):
            if x not in out:
                out.append(x)
                todo.append(x)
    return out


def game_on(forms: dict, qs: list[str], world: dict, state: dict | None, sheet=None, strict=False) -> G.Game:
    """A game over `qs` and the quests they name, from a new game (state None) or carrying on from `state`: a quest
    not loaded before starts now if it runs from a new game or the stage it waits on is done (one started by another
    form's start_quest result starts when that result runs)."""
    g = G.Game([forms[x] for x in named(qs, forms)], world, state=_copy(state) if state else None, sheet=sheet,
               strict=strict)
    if state is None:
        g.begin()
    else:
        for q, f in g.forms.items():
            st = f["quest"]["start"]
            if q in g.s["quests"]:
                continue
            if st["by"] == "game" or (st["by"] == "quest_stage" and
                                      st["quest_stage"] in (g.s["quests"].get(st["quest"]) or {}).get("done", [])):
                g._set_stage(q, st["stage"], None)
    return g


def play_after(forms: dict, after: list[str], world: dict, sheet=None, strict=False, max_states=MAX_STATES,
               memo: dict | None = None, endings: tuple = (), gold: int = 0) -> tuple[dict, list[tuple[str, str]]]:
    """Play each quest of `after` in turn to a completed ending (the i-th to `endings[i]` where given), each in a game
    of only the quests it and those before it name (a small space to search); (the state left, the steps shown).
    Raises a HarnessError when one cannot be completed."""
    state, steps = None, []
    for i, d in enumerate(after):
        end = endings[i] if i < len(endings) else None
        key = (tuple(after[:i + 1]), tuple(endings[:i + 1]), json.dumps(sheet, sort_keys=True))
        if memo is not None and key in memo:
            state, steps = memo[key]
            if isinstance(state, HarnessError):
                raise state
            continue
        g = game_on(forms, list(after[:i + 1]), world, state, sheet, strict)
        if state is None:
            g.s["gold"] = gold
        try:
            steps = steps + complete(g, d, max_states, end)
        except HarnessError as e:
            if memo is not None:
                memo[key] = (e, steps)
            raise
        state = g.s
        if memo is not None:
            memo[key] = (state, steps)
    return state, steps


def _completed(f) -> list[int]:
    return [s["number"] for s in f["stages"] if s["ending"] == "completed"]


# -- the carried state: what a later quest can read of what the earlier ones left ----------------------------------

def _results(f, lines=None) -> list[dict]:
    lines = f["lines"] if lines is None else lines
    return ([r for s in f["stages"] for r in s["results"]] if lines is f["lines"] else []) + \
        [r for ln in lines for r in ln["results"]]


def _lingering(f) -> list[dict]:
    """A quest's lines still said once it has ended (its stage at an ending within their window) that change
    something: an ended quest acts through nothing else."""
    ends = [s["number"] for s in f["stages"] if s["ending"] != "none"]
    return [ln for ln in f["lines"] if ends and ln["last_stage"] >= min(ends) and (ln["results"] or ln["answers"])]


class Reads:
    """Everything the rest of a chain can read or change: the whole forms of the quests still to play (and every
    loaded quest not yet played), and the lingering lines of the quests already ended. A field of the state none of
    them names cannot change what happens next, so two states equal on what they name are one carried state.

    Gold and a held count are read only against thresholds (a condition's, a take's, a key's or a lockpick's), and
    change only by results (a stage's runs once) and by things taken: two amounts no threshold tells apart after any
    set of those changes are one (a count a line's result changes, which may come again, is kept exact)."""

    def __init__(self, forms: dict, rest: list[str], ended: list[str]):
        self.refs, self.numbers, self.factions, self.lines, self.triggered = set(), set(), set(), set(), set()
        self.quests, self.stages, self.staged = set(rest), {}, set()   # whole entries; done stages read; stage read
        self.spoken, self._at, self._by, self._exact, self._g, self._negated = False, [], [], set(), None, set()
        parts = [(forms[x], None) for x in rest] + [(forms[d], _lingering(forms[d])) for d in ended]
        for f, lines in parts:
            whole = lines is None
            lines = f["lines"] if whole else lines
            q = f["quest"]["id"]
            if not whole and lines:
                self.staged.add(q)                  # the window of its lingering lines is read
            if whole:
                self.refs |= {r["id"] for r in f["refs"]} | {m["ref"] for m in f["must_live"]} | \
                    {t["ref"] for t in f["triggers"] if t.get("ref")} | {t for o in f["objectives"] for t in o["targets"]}
                self.triggered |= {t["ref"] for t in f["triggers"] if t.get("ref")}
                for t in f["triggers"]:
                    if t["kind"] == "quest_stage":
                        self.stages.setdefault(t["quest"], set()).add(t["quest_stage"])
                st = f["quest"]["start"]
                if st["by"] == "quest_stage":
                    self.stages.setdefault(st["quest"], set()).add(st["quest_stage"])
                for s in f["stages"]:
                    self._results(s["results"], once=True)
            self.lines |= {ln["id"] for ln in lines}
            self.refs |= {ln["speaker"] for ln in lines}
            for c in [c for ln in lines for c in ln["conditions"]]:
                self.refs |= {c["ref"]} if "ref" in c else set()
                if c["is"] == "stage_done":
                    self.stages.setdefault(c["quest"], set()).add(c["stage"])
                elif "quest" in c:
                    self.staged.add(c["quest"])
                if c["is"] == "number_compare":
                    self.numbers.add(c["number"])
                if "faction" in c:
                    self.factions.add(c["faction"])
                if c["is"] in ("item_count_at_least", "gold_at_least"):
                    what = c["item"] if "item" in c else G.GOLD
                    self._at.append((what, c["count"] if "item" in c else c["gold"]))
                    if c.get("not"):
                        self._negated.add(what)     # more of it can shut a line: no richer state is covered
                if c["is"] in ("spoken_before", "not_spoken_before"):
                    self.spoken = True
            for ln in lines:
                self._results(ln["results"], once=False)

    @property
    def fields(self) -> tuple[str, ...]:
        """The fields of a state `key` reads, but pos and talking (read only while a container is open or a question
        waits)."""
        return ("quests", "gold", "items", "numbers", "factions", "regard", "switched", "locked", "contents", "fired",
                "opened", "ended", "sheet", "dead", "hostile", "owned", "taken", "question") + \
            (("spoken",) if self.spoken else ())

    def _results(self, rs, once: bool):
        for r in rs:
            self.refs |= {r["ref"]} if "ref" in r else set()
            if "if_held" in r:
                self._at.append((r["if_held"], 1))
            if r["do"] in ("set_number", "add_number"):
                self.numbers.add(r["number"])
            if "faction" in r:
                self.factions.add(r["faction"])
            if r["do"] == "start_quest":
                self.quests.add(r["quest"])
            if r["do"] in ("give_item", "take_item", "give_gold", "take_gold"):
                what, n = (r["item"], r["count"]) if "item" in r else (G.GOLD, r["amount"])
                if r["do"].startswith("take"):
                    self._at.append((what, n))      # a take of more than is held takes what there is
                    n = -n
                if once:
                    self._by.append((what, n))
                else:
                    self._exact.add(what)

    def _prepare(self, g):
        """The refs the rest reads (with their holders and keys), and each read count's thresholds as amounts held
        now: the points no amount can cross without a threshold telling it after some set of changes."""
        refs = set(self.refs)
        for _ in range(2):
            for r in list(refs):
                e = g.ents.get(r)
                if e:
                    refs |= {x for x in (e["container"], e["carried_by"]) if x}
            refs |= {(g.ents[r]["lock"] or {}).get("key") for r in refs if r in g.ents} - {None}
        keys = {(g.ents[r]["lock"] or {}).get("key") for r in refs if r in g.ents} - {None}
        at = [(g.item_of(i), n) for i, n in self._at] + [(g.item_of(k), 1) for k in keys] + \
            [(k, 1) for k in keys] + [(G.LOCKPICK, 1)]
        by = [(g.item_of(i), n) for i, n in self._by]
        by += [(e["item"], e["count"]) for e in g.ents.values() if e["kind"] == "thing" and e["item"]]
        by += [(c["item"], c["count"]) for e in g.ents.values() for c in e["contents"]]
        self._refs, self._exact_ids = refs, {g.item_of(i) for i in self._exact}
        # a thing taken matters only when something reads it: its item's count, a trigger on it, what it holds, a lock
        self._kept = {r for r in refs if r in g.ents and (g.ents[r]["kind"] != "thing" or r in self.triggered or
                                                           r in g.holders or r in keys or g.ents[r]["item"] in
                                                           {i for i, _ in at})}
        negated = {g.item_of(i) for i in self._negated}
        self._points = {}
        for i in {i for i, _ in at}:
            sums = {0}
            for j, n in by:
                if j == i:
                    sums |= {s + n for s in sums}
            self._points[i] = sorted({t - d for j, t in at if j == i for d in sums})
        # an amount read only as "at least" (more never shuts a line, and a take of more than is held takes what
        # there is): a state with more of it, and all else the same, reaches all a poorer one does
        self._more = sorted(i for i in self._points if i not in negated and i not in self._exact_ids)
        self._g, self._amounts, self._ended = g, {}, {}

    def _amount(self, i, n):
        from bisect import bisect_right
        return n if i in self._exact_ids else bisect_right(self._points[i], n)

    def key(self, g, s: dict) -> tuple[tuple, tuple]:
        """The state as the rest of the chain sees it (`g` a game over the whole chain, for its refs and items): (all
        but the amounts where more is never worse, those amounts in order). Lists are read as sets (but a waiting
        question's answers), tables by their entries."""
        if self._g is not g:
            self._prepare(g)
        refs = self._refs
        quests, ended = [], self._ended
        for x, st in s["quests"].items():
            if st["ended"] and ended.get(id(st), (None,))[0] is st:     # an ended quest's entry is never changed
                part = ended[id(st)][1]
            elif x in self.quests:
                part = (x, tuple(sorted((k, tuple(sorted(v)) if type(v) is list else v) for k, v in st.items())))
            elif x in self.stages or x in self.staged:
                part = (x, (tuple(sorted(set(st["done"]) & self.stages.get(x, set()))), st["ended"],
                            max(st["done"]) if x in self.staged and st["done"] else None))
            else:
                part = None
            if st["ended"]:
                ended[id(st)] = (st, part)
            if part is not None:
                quests.append(part)
        quests.sort(key=_first)
        opened = _among(s["opened"], refs)
        points, more, amounts = self._points, self._more, self._amounts
        amount = {}
        for i in points:
            n = s["gold"] if i == G.GOLD else s["items"].get(i, 0)
            a = amounts.get((i, n))
            amount[i] = a if a is not None else amounts.setdefault((i, n), self._amount(i, n))
        numbers, factions = self.numbers, self.factions
        question = s["question"]
        base = (tuple(quests), _rows((i, n) for i, n in amount.items() if i not in more),
                _rows((n, v) for n, v in s["numbers"].items() if n in numbers) if s["numbers"] else (),
                _rows((f, v) for f, v in s["factions"].items() if f in factions) if s["factions"] else (),
                _rows((r, v) for r, v in s["regard"].items() if r in refs) if s["regard"] else (),
                _rows((r, v) for r, v in s["switched"].items() if r in refs) if s["switched"] else (),
                _rows((r, v) for r, v in s["locked"].items() if r in refs) if s["locked"] else (),
                _rows((h, tuple(sorted(c.items()))) for h, c in s["contents"].items()
                      if h in refs or not points.keys().isdisjoint(c)) if s["contents"] else (),
                _among(s["fired"], self.lines), opened, s["ended"], _sheet(s["sheet"]),
                _among(s["dead"], refs), _among(s["hostile"], refs), _among(s["owned"], refs),
                _among(s["taken"], self._kept), _among(s["spoken"], refs) if self.spoken else None,
                (_frozen(question), s["talking"]) if question else None,
                _frozen(s["pos"]) if opened or question else None)
        return base, tuple(amount[i] for i in more)


def _first(x):
    return x[0]


def _rows(pairs) -> tuple:
    """A table's entries (unique first items) in order."""
    return tuple(sorted(pairs, key=_first))


def _among(xs: list, keep) -> tuple:
    """The members of `xs` in `keep`, as a set in order."""
    return tuple(sorted(set(xs) & keep)) if xs else ()


_SHEET = {"race", "sex", "skills"}


def _sheet(sh):
    """`_frozen` of a character sheet, the common shape read straight."""
    if sh.keys() == _SHEET:
        return ("race", sh["race"]), ("sex", sh["sex"]), ("skills", tuple(sorted(sh["skills"].items())))
    return _frozen(sh)


def _frozen(v):
    """A value as one that can be told apart from others like it: tables by their entries, lists in order."""
    t = type(v)
    if t is dict:
        return tuple(sorted(((k, _frozen(x)) for k, x in v.items()), key=_first))
    if t is list or t is tuple:
        return tuple(_frozen(x) for x in v)
    return v


def _covers(a: tuple, b: tuple) -> bool:
    """Amounts `a` no more than `b` in every place: what is reached from a is reached from b."""
    return all(x <= y for x, y in zip(a, b))


def reach(forms: list[dict], world: dict | None = None, sheets: dict | None = None,
          max_states: int = MAX_STATES, skip: set[str] = frozenset(), only: set[str] | None = None,
          memo: dict | None = None, deadline: float | None = None, store=None) -> list[dict]:
    """For each quest of the set (but `skip`, or only those of `only`) and each way through the quests it waits on
    (each a completed ending of each), a row: {quest, name, after: [[quest, ending]...], stages: [{stage, ending, by:
    {sheet: path or None}, why}], completes: {sheet: bool}, blocked: {sheet: why}, walked: {sheet: the way through
    whose carried state was searched for this row}}. Every stage and ending is searched for by each sheet of `sheets`
    (default SHEETS), each starting with GOLD gold.

    The earlier quests are played one at a time, each from every distinct state the ones before it can leave (`Reads`:
    states the rest of the chain cannot tell apart are one). Of states that differ only in amounts the rest reads as
    "at least" (gold, a count held), the poorest is played on: what it reaches, a richer one reaches by the same
    steps; a richer one is played on itself only where the poorest is blocked or misses a goal. So the walked quest
    starts once per distinct carried state that is not covered so, never once per way through.

    One search serves every question asked from one state of one game (`Explorer`): a quest's walk and its plays to
    each of its endings for the quests after it share it. `memo` (a dict) keeps those searches and plays between
    calls over the same forms, world, sheets and max_states; `store` (get(parts) / put(parts, value)) keeps the plays
    between runs. Past `deadline` (time.monotonic()) the walk stops with a TimeLimit naming what was not yet reached
    and how many states were searched."""
    from itertools import product

    from tools.playtest import world as W
    by_id = {f["quest"]["id"]: f for f in forms}
    world = world or W.snapshot(forms, use_db=False)
    sheets = sheets or SHEETS
    memo = {} if memo is None else memo
    plays, searches = memo.setdefault("plays", {}), memo.setdefault("searches", {})
    out = []

    def start(state, sheet) -> str:
        return json.dumps(state, sort_keys=True) if state else json.dumps(sheet, sort_keys=True)

    def searcher(qids, state, sheet, ended, q) -> Search:
        """The search for quest `q` in a game of `qids` (and what they name) from `state`, its states told apart as
        the quests not `ended` (whole) and the lingering lines of those `ended` read them."""
        k = (tuple(qids), start(state, sheet), tuple(ended), q)
        if k not in searches:
            g = game_on(by_id, list(qids), world, state, sheet)
            if state is None:
                g.s["gold"] = GOLD
            reads = Reads(by_id, [x for x in named(list(qids), by_id) if x not in ended], list(ended))
            searches[k] = Search(g, _ended(q), max_states, own_refs(g, q), lambda s, g=g: reads.key(g, s),
                                 reads.fields)
        return searches[k]

    def play(before, i, end, state, sheet):
        """Quest before[i] played to `end` from `state`, in a game of only the quests it and those before it name."""
        q = before[i]
        k = (q, end, start(state, sheet))
        if k in plays:
            return plays[k]
        parts = ["play", list(before[:i + 1]), end, json.loads(k[2]), GOLD, max_states]
        kept = store.get(parts) if store is not None else None
        if kept is not None:
            plays[k] = HarnessError(kept["error"]) if "error" in kept else kept["state"]
            return plays[k]

        def done(s):
            st = s["quests"].get(q)
            return st is not None and end in st["done"]
        try:
            res = searcher(before[:i + 1], state, sheet, before[:i], q).answer({"done": done}, deadline)
        except TimeLimit as e:
            raise TimeLimit(e.states, [f"{q}'s stage {end}, played to for the quests after it"]) from None
        if "done" not in res["paths"]:
            plays[k] = HarnessError(f"--after {q}: stage {end} reached from here: {_stops(res, q, None)}")
        else:
            g = game_on(by_id, list(before[:i + 1]), world, state, sheet)
            if state is None:
                g.s["gold"] = GOLD
            for a in res["paths"]["done"]:
                g.do(command(a))
            plays[k] = g.s
        if store is not None:
            store.put(parts, {"error": str(plays[k])} if isinstance(plays[k], HarnessError) else {"state": plays[k]})
        return plays[k]

    def proven(qids, state, sheet, goals, proofs, first, ends):
        """A walk's result without a search, when for each goal a path an earlier search of the quest found to it
        (from another carried state, or for another character; for a completed ending, to any of `ends`) reaches it
        from here as well: each is then reached by those steps, played here. None when one does not."""
        tries = {n: proofs.get(n, [])[-PROOFS:] + ([p for e in ends for p in proofs.get(e, [])[-1:]]
                                                   if n == "completed" else []) for n in goals}
        if not all(tries.values()):
            return None
        g = game_on(by_id, list(qids), world, state, sheet)
        if state is None:
            g.s["gold"] = GOLD
        start, g.quiet, paths = _copy(g.s), True, {}
        for n, test in goals.items():
            paths[n] = next((r for p in tries[n] if (r := _replay(g, start, p, test)) is not None), None)
            if paths[n] is None:
                return None
        g.s = start
        return first, {n: [shown(g, a) for a in p] for n, p in paths.items()}, ""

    def groups(classes):
        """Each group of carried states alike but for amounts, poorest first."""
        by: dict[str, list] = {}
        for (base, more), v in classes.items():
            by.setdefault(base, []).append((more, *v))
        return [sorted(g, key=lambda m: (sum(m[0]), m[0])) for g in by.values()]

    for q, f in by_id.items():
        if q in skip or (only is not None and q not in only):
            continue
        chain = order(q, by_id)
        before = chain[:-1]
        loaded = named(chain, by_id)
        whole = G.Game([by_id[x] for x in loaded], world, strict=False)
        reads = [Reads(by_id, [x for x in loaded if x not in before[:i]], before[:i]) for i in range(len(before) + 1)]
        rows = {}
        for ends in product(*[_completed(by_id[d]) for d in before]):
            rows[ends] = {"quest": q, "name": f["quest"]["name"], "after": [list(x) for x in zip(before, ends)],
                          "stages": [{"stage": s["number"], "ending": s["ending"], "by": {}, "why": {}}
                                     for s in f["stages"]], "completes": {}, "blocked": {}, "walked": {}}
        out += rows.values()
        proofs: dict = {}                   # each goal: the paths an earlier search of this quest found to it
        for name, sheet in sheets.items():
            classes = {("", ()): (None, [()])}      # carried state -> (a state that carries it, the ways to it)
            for i, d in enumerate(before):
                new: dict = {}
                for group in groups(classes):
                    for end in _completed(by_id[d]):
                        done = []                   # (amounts, the class its result went to) of each one played
                        for more, state, ways in group:
                            ways1 = [w + (end,) for w in ways]
                            hit = next((ck for m, ck in done if _covers(m, more)), None)
                            if hit is not None:
                                new[hit][1].extend(ways1)
                                continue
                            s1 = play(before, i, end, state, sheet)
                            if isinstance(s1, HarnessError):
                                for ends, row in rows.items():
                                    if ends[:i + 1] in ways1:
                                        row["blocked"][name] = str(s1)
                                continue
                            ck = reads[i + 1].key(whole, s1)
                            new.setdefault(ck, (s1, []))[1].extend(ways1)
                            done.append((more, ck))
                classes = new
            for group in groups(classes):
                done = []                           # (amounts, wanted, result) of each searched and found whole
                for more, state, ways in group:
                    # each stage no character before has reached on one of these ways, and a completed ending
                    wanted = tuple(s["number"] for j, s in enumerate(f["stages"])
                                   if any(not any(p is not None for p in rows[w]["stages"][j]["by"].values())
                                          for w in ways))
                    hit = next((r for m, wt, r in done if _covers(m, more) and set(wanted) <= set(wt)), None)
                    goals = {n: (lambda st, n=n: n in (st["quests"].get(q) or {}).get("done", [])) for n in wanted}
                    goals["completed"] = lambda st: (st["quests"].get(q) or {}).get("ended") == "completed"
                    if hit is None:
                        hit = proven(chain, state, sheet, goals, proofs, ways[0], _completed(f))
                        if hit is not None:
                            done.append((more, wanted, hit))
                    if hit is None:
                        x = searcher(chain, state, sheet, before, q)
                        try:
                            res = x.answer(goals, deadline)
                        except TimeLimit as e:
                            after = ", ".join(f"{d} {n}" for d, n in zip(before, ways[0]))
                            raise TimeLimit(e.states, [("the completed ending" if n == "completed" else f"stage {n}") +
                                                       f" for the {name} character" + (f", after {after}" if after
                                                                                      else "") for n in e.missing]
                                            ) from None
                        g = x.first.g
                        for n, p in res["paths"].items():
                            proofs.setdefault(n, []).append(p)
                        hit = (ways[0], {n: [shown(g, a) for a in p] for n, p in res["paths"].items()},
                               _stops(res, q, g))
                        if len(res["paths"]) == len(goals):
                            done.append((more, wanted, hit))
                    first, paths, why = hit
                    for w in ways:
                        row = rows[w]
                        row["walked"][name] = [list(x) for x in zip(before, first)]
                        for s in row["stages"]:
                            if s["stage"] in wanted and not any(p is not None for p in s["by"].values()):
                                s["by"][name] = paths.get(s["stage"])
                                if s["by"][name] is None:
                                    s["why"][name] = why
                        row["completes"][name] = "completed" in paths
    return out


def starts(rows: list[dict]) -> dict[str, int]:
    """How many times each quest was started and searched, over every character: once per distinct carried state."""
    out: dict[str, int] = {}
    for r in rows:
        out.setdefault(r["quest"], 0)
        out[r["quest"]] += sum(1 for w in r["walked"].values() if [list(x) for x in w] == r["after"])
    return out


def _after(r) -> str:
    return f", after {', '.join(f'{q} {n}' for q, n in r['after'])}" if r["after"] else ""


def report(rows: list[dict]) -> str:
    """Each quest's endings by the shortest path any sheet found, and what no sheet reached."""
    lines = []
    for r in rows:
        lines.append(f"{r['quest']} ({r['name']}){_after(r)}:")
        for name, why in r["blocked"].items():
            lines.append(f"  blocked for the {name} character: {why}")
        for s in r["stages"]:
            paths = [(n, p) for n, p in s["by"].items() if p is not None]
            if paths:
                if s["ending"] != "none":
                    n, p = min(paths, key=lambda x: len(x[1]))
                    lines.append(f"  {s['stage']} {s['ending']}: reached in {len(p)} ({n}): " + "; ".join(p))
            elif s["by"]:
                lines.append(f"  {s['stage']}{' ' + s['ending'] if s['ending'] != 'none' else ''}: NOT REACHED: "
                             + "; ".join(f"{n}: {w}" for n, w in s["why"].items()))
    return "\n".join(lines)


def unreached(rows: list[dict]) -> list[str]:
    """What the gate fails on: a way through the earlier quests that no character can take; a stage or ending that
    no character reaches; a character who takes the way through and cannot complete the quest. A way one character
    cannot take (an earlier ending only a skill opens) is that character's limit, not a fault."""
    bad = []
    for r in rows:
        head = f"{r['quest']}{_after(r)}"
        if r["blocked"] and not r["completes"]:
            bad += [f"{head}: blocked for the {n} character: {w}" for n, w in r["blocked"].items()]
        for s in r["stages"]:
            if s["by"] and all(p is None for p in s["by"].values()):
                what = "ending" if s["ending"] != "none" else "stage"
                bad.append(f"{head}: {what} {s['stage']} not reached: {next(iter(s['why'].values()))}")
        bad += [f"{head}: the {n} character reaches no completed ending" for n, ok in r["completes"].items()
                if not ok]
    return bad



OWED = Path(__file__).with_name("reach_owed.json")


def _qid(bad: str) -> str:
    return bad.split(":")[0].split(",")[0]


def owed() -> dict[str, str]:
    """The quests parked on reach_owed.json, each with why: `make check` does not walk them."""
    return json.loads(OWED.read_text(encoding="utf-8"))["quests"]


def ratchet(rows: list[dict]) -> list[str]:
    """The owed quests the rows (walked with `only=` the owed list) now find wholly in reach: each is taken off
    reach_owed.json (the list only shrinks); returns them."""
    data = json.loads(OWED.read_text(encoding="utf-8"))
    bad = {_qid(b) for b in unreached(rows)}
    done = sorted(q for q in data["quests"] if q in {r["quest"] for r in rows} and q not in bad)
    if done:
        data["quests"] = {q: w for q, w in data["quests"].items() if q not in done}
        OWED.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return done


def compiled() -> list[dict]:
    """Every staged quest record that fits the quest form, compiled now (the forms `make check`'s questform gate
    builds)."""
    from tools.argonia_world import db
    from tools.questform import __main__ as QF
    from tools.questform import compile as qc
    w = db.open()
    out = []
    for qid in qc.staged_quests(w):
        form, terms, _ = QF.terms_of(w, qid)
        if form is not None and not terms:
            out.append(form)
    return out
