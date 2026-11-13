"""The walker (docs/design/paper-playtest.md): the paper game played by itself, breadth first over the commands a
player could give, so the first path found to a state is a shortest one. Deterministic: the same forms give the same
paths.

- `complete(game, quest)` plays one quest to a completed ending along a shortest path (for `--after`), or raises a
  HarnessError naming the stages every path stops at;
- `reach(forms)` reports, for each quest of a set, each ending: reached by which shortest path from a new game (the
  quests it waits on first played to a completed ending), or the stages every path stops at.

It tries what the quest could ask of a player: say every quest line on offer, talk to everyone, take and use every
thing, open containers, pick locks with lockpicks held, pickpocket and search bodies (always unseen), fight a person
who is hostile, who-must-live or watched by a death trigger (always won), and go to every person, thing and door. A
person's own topics outside the forms move nothing and are not tried.
"""
from __future__ import annotations

import json
from collections import deque
from pathlib import Path

from tools.playtest import game as G
from tools.playtest.vocab import HarnessError

MAX_STATES = 20000
# `reach` asks whether any character can reach an ending: its default player has every skill at 100.
ABLE = G.new_sheet("Argonian", "female", **{s.replace(" ", "").replace("-", ""): 100 for s in G.SKILLS})


def _copy(s: dict) -> dict:
    return json.loads(json.dumps(s))      # the state is plain JSON; this is several times quicker than deepcopy


def _key(s: dict, spoken: bool) -> str:
    """A state as far as what can happen next goes: lists as sets; who was spoken to only when a condition asks; who
    the player is talking to only while a question waits (any topic is one `talk` away); where the player stands only
    while a container is open or a question waits (any person, thing or door is one `go` away)."""
    drop = {"commands", "visited", "crimes"} | (set() if spoken else {"spoken"}) | \
        (set() if s["question"] else {"talking"}) | (set() if s["opened"] or s["question"] else {"pos"})
    return json.dumps({k: sorted(v) if k in ("taken", "dead", "fired", "spoken", "opened", "hostile") else v
                       for k, v in s.items() if k not in drop}, sort_keys=True)


def _asks_spoken(g) -> bool:
    return any(c["is"] in ("spoken_before", "not_spoken_before")
               for f in g.forms.values() for ln in f["lines"] for c in ln["conditions"])


def _fightable(g) -> set[str]:
    out = {e for e, x in g.ents.items() if x["hostile"]}
    for f in g.forms.values():
        out |= {m["ref"] for m in f["must_live"]}
        out |= {t["ref"] for t in f["triggers"] if t["kind"] == "death"}
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
    elif x["kind"] == "thing":
        out.append(("take", e, "unseen"))
    if picks and g._locked(e) and (x["lock"] or {}).get("level") != "key":
        out.append(("pick", e, "win unseen"))
    return out


def actions(g, fightable: set[str], speakers: set[str]) -> list[tuple]:
    """Every move worth trying now, each a tuple of steps. Going somewhere is never a move of its own (but to a
    person who speaks first): it is the first step of doing something there, so only the places acted at count."""
    s, out = g.s, []
    if s["talking"] and s["question"]:
        out += [(("say", None, str(i), m[0]),) for i, m in enumerate(g._answers(), 1) if m[1] == "line"]
    used = {t["ref"] for f in g.forms.values() for t in f["triggers"] if t["kind"] == "use"}
    picks = s["items"].get(G.LOCKPICK, 0) > 0
    here = g._visible()
    for e in here:
        out += [(step,) for step in _at(g, e, fightable, used, picks)]
    for h in s["opened"]:
        if h in g.ents and g._near(h):
            out += [(("take", k, "unseen"),) for _, k in g._inside(h)]
    for e, x in g.ents.items():
        if e in here or x["kind"] == "marker" or not g._loose(e) or not g._on(e) or g._pos(e) is None:
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


def search(g, goals: dict, over=None, max_states: int = MAX_STATES) -> dict:
    """Breadth first from the game's state. `goals` {name: test(state)}; a state `over(state)` holds for is not
    played on. Talking to someone is followed at once by each quest line on offer. Returns {"paths": {name: [step...]},
    "stages": {quest: stages seen}, "states": n, "cut": the search hit max_states, "errors": harness errors met}."""
    start = _copy(g.s)
    fightable = _fightable(g)
    speakers = {ln["speaker"] for f in g.forms.values() for ln in f["lines"] if ln["kind"] == "speaks_first"}
    paths, stages, errors = {}, {}, []
    spoken = _asks_spoken(g)
    seen = {_key(start, spoken)}
    todo = deque([(start, [])])
    cut = False

    def run(s, steps):
        g.s = _copy(s)
        try:
            for step in steps:
                g.do(command(step))
        except HarnessError as e:
            if str(e) not in errors:
                errors.append(str(e))
            return None
        return g.s

    def push(s, path) -> bool:
        k = _key(s, spoken)
        if k not in seen:
            seen.add(k)
            todo.append((s, path))
        return len(seen) >= max_states

    while todo and len(paths) < len(goals) and not cut:
        s, path = todo.popleft()
        for q, st in s["quests"].items():
            stages.setdefault(q, set()).update(st["done"])
        for name, test in goals.items():
            if name not in paths and test(s):
                paths[name] = path
        if len(paths) == len(goals):
            break
        if over and over(s):
            continue
        g.s = s
        for a in actions(g, fightable, speakers):
            s1 = run(s, a)
            if s1 is None:
                continue
            if a[-1][0] == "talk" and s1["talking"] and not s1["question"]:
                lines = [(("say", None, str(i), m[0]),) for i, m in enumerate(g._menu(s1["talking"]), 1)
                         if m[1] == "line"]
                for say in lines:
                    s2 = run(s1, say)
                    if s2 is not None and push(s2, path + list(a) + list(say)):
                        cut = True
                        break
            if cut or push(s1, path + list(a)):
                cut = True
                break
    g.s = start
    return {"paths": paths, "stages": {q: sorted(v) for q, v in stages.items()}, "states": len(seen), "cut": cut,
            "errors": errors}


def _stops(res, q, g) -> str:
    st = res["stages"].get(q)
    ends = {s["number"] for s in g.forms[q]["stages"] if s["ending"] != "none"}
    last = max([n for n in st or [] if n not in ends] or [None], key=lambda n: -1 if n is None else n)
    where = ("the quest never starts" if not st else
             f"every path stops by stage {last} (stages reached: {', '.join(map(str, st))})" if last is not None
             else f"stages reached: {', '.join(map(str, st))}")
    if res["cut"]:
        where += f"; search cut at {res['states']} states"
    if res["errors"]:
        where += f"; harness error: {res['errors'][0]}"
    return where


def _ended(q):
    """A state where quest `q` has ended: the search plays no further from it."""
    return lambda s: bool((s["quests"].get(q) or {}).get("ended"))


def complete(g, q: str, max_states: int = MAX_STATES) -> list[tuple[str, str]]:
    """Play quest `q` to a completed ending along a shortest path; the game keeps the state it leaves. Returns the
    (command as typed, what it showed) of each step."""
    def done(s):
        st = s["quests"].get(q)
        return st is not None and st["ended"] == "completed"
    res = search(g, {"done": done}, _ended(q), max_states)
    if "done" not in res["paths"]:
        raise HarnessError(f"--after {q}: no completed ending can be reached from here: {_stops(res, q, g)}")
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
               memo: dict | None = None) -> tuple[dict, list[tuple[str, str]]]:
    """Play each quest of `after` in turn to a completed ending, each in a game of only the quests it and those
    before it name (a small space to search); (the state left, the steps shown). Raises a HarnessError when one
    cannot be completed."""
    state, steps = None, []
    for i, d in enumerate(after):
        key = tuple(after[:i + 1])
        if memo is not None and key in memo:
            state, steps = memo[key]
            if isinstance(state, HarnessError):
                raise state
            continue
        g = game_on(forms, list(after[:i + 1]), world, state, sheet, strict)
        try:
            steps = steps + complete(g, d, max_states)
        except HarnessError as e:
            if memo is not None:
                memo[key] = (e, steps)
            raise
        state = g.s
        if memo is not None:
            memo[key] = (state, steps)
    return state, steps


def reach(forms: list[dict], world: dict | None = None, sheet: dict | None = None,
          max_states: int = MAX_STATES) -> list[dict]:
    """For each quest of the set: {quest, name, after, endings: [{stage, ending, path or None, why}]}."""
    from tools.playtest import world as W
    by_id = {f["quest"]["id"]: f for f in forms}
    world = world or W.snapshot(forms, use_db=False)
    sheet = sheet or ABLE
    out, memo = [], {}
    for q, f in by_id.items():
        chain = order(q, by_id)
        row = {"quest": q, "name": f["quest"]["name"], "after": chain[:-1], "endings": []}
        out.append(row)
        try:
            state, _ = play_after(by_id, chain[:-1], world, sheet, max_states=max_states, memo=memo)
            g = game_on(by_id, chain, world, state, sheet)
        except HarnessError as e:
            row["blocked"] = str(e)
            continue
        ends = {s["number"]: s["ending"] for s in f["stages"] if s["ending"] != "none"}
        res = search(g, {n: (lambda s, n=n: n in (s["quests"].get(q) or {}).get("done", [])) for n in ends},
                     _ended(q), max_states)
        for n, kind in ends.items():
            p = res["paths"].get(n)
            row["endings"].append({"stage": n, "ending": kind, "path": None if p is None else [shown(g, a) for a in p],
                                   "why": None if p is not None else _stops(res, q, g)})
    return out


def report(rows: list[dict]) -> str:
    lines = []
    for r in rows:
        after = f", after {', '.join(r['after'])}" if r["after"] else ""
        lines.append(f"{r['quest']} ({r['name']}){after}:")
        if r.get("blocked"):
            lines.append(f"  blocked: {r['blocked']}")
        for e in r["endings"]:
            if e["path"] is not None:
                lines.append(f"  {e['stage']} {e['ending']}: reached in {len(e['path'])}: " + "; ".join(e["path"]))
            else:
                lines.append(f"  {e['stage']} {e['ending']}: NOT REACHED: {e['why']}")
    return "\n".join(lines)


def unreached(rows: list[dict]) -> list[str]:
    """What the gate fails on: a quest blocked, or one whose every completed ending is out of reach."""
    bad = []
    for r in rows:
        if r.get("blocked"):
            bad.append(f"{r['quest']}: {r['blocked']}")
        elif not any(e["path"] is not None for e in r["endings"] if e["ending"] == "completed"):
            bad.append(f"{r['quest']}: no completed ending can be reached")
    return bad


OWED = Path(__file__).with_name("reach_owed.json")


def gate(bad: list[str]) -> list[str]:
    """make check's view: a quest out of reach that is not on reach_owed.json, or one on it that now reaches a
    completed ending (take it off: the list only shrinks)."""
    owed = json.loads(OWED.read_text(encoding="utf-8"))["quests"]
    out = [b + " (and it is not on tools/playtest/reach_owed.json)" for b in bad if b.split(":")[0] not in owed]
    now = {b.split(":")[0] for b in bad}
    out += [f"{q} now reaches a completed ending: take it off tools/playtest/reach_owed.json" for q in owed
            if q not in now]
    return out


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
