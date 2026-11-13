"""The quest form's structural checks: what the schema alone cannot say (docs/design/quest-form.md, "The rules").

`check(form)` returns every failure as (rule, one line). The schema runs first; a form that breaks it gets no
structural check (its shape is not known). Stages are by "done", as the engine has them: setting a stage already done
does nothing, and a quest's stage as a line's window reads it is the highest stage done (`stage-order` keeps every
stage set above the stage it is set from). Windows:
- a line is open while the quest's stage is from its first stage to its last;
- a trigger is open while its prerequisite stage is done, the stage it sets is not and the quest's stage is below its
  `until` (the graph below takes it as open at every such stage from its prerequisite on, an over-reach that `reach`
  in the paper game and `late-trigger`'s walk over what is done do not make);
- an objective is active at a stage it is shown at and is not completed at.

Every refusal of the builder (tools/ArgoniaPlugin/QuestForm.cs) that a form alone can show is a rule here, so a form
that passes `check` (and `check_set`) builds.
"""
from __future__ import annotations

import math
import re
from collections import defaultdict

from tools.questform import validate

# A switch on or off happens "away from the player": the switched reference stands in another interior cell than
# the speaker or thing that causes it, or across the interior/exterior line from it, or, both outdoors, at least this
# many units from it (docs/research/skyrim/quest-form-engine-facts.md).
AWAY_UNITS = 18000.0
# The engine's limits on result rows, as the builder counts them: all of a quest's stage rows together, and one line.
MAX_STAGE_RESULTS = 128
MAX_LINE_RESULTS = 128
# Regard is Skyrim's relationship rank, kept between these by the engine (ARG_Effects ChangeRegard).
REGARD_MIN, REGARD_MAX = -4, 4
# The ways of a quest the late-trigger walk follows at most (each a set of stages done); a quest with more is not walked.
MAX_WAYS = 50000

RULES = ("schema", "vocabulary", "unique-ids", "stages-exist", "refs-exist", "placement", "lock", "owner", "contents",
         "item-id", "journal-text",
         "way-out", "reachable", "objective-target-on", "asked-is-target", "completes-on-target", "hand-in", "held-take",
         "line-window", "switch-cause", "away", "must-live-fails", "must-live-window", "main-message", "death-hostile",
         "result-limits", "speaks-first-has-line", "stage-order", "trigger", "speaks-first", "answer", "prompt",
         "speaker", "hostile", "created", "line-said", "regard-range", "objective-left", "late-trigger", "check-label")

# A check on a prompt, as Skyrim shows it: in brackets, "(Persuade)" for Speech, the skill's name for any other,
# "(<n> gold)" for gold; never a threshold.
SKILL_LABEL = {"Speech": "Persuade", "OneHanded": "One-handed", "TwoHanded": "Two-handed", "HeavyArmor": "Heavy Armor",
               "LightArmor": "Light Armor"}
SPEECH_LABELS = ("Persuade", "Intimidate")
_SKILLS = ("Speech", "Sneak", "Lockpicking", "Pickpocket", "Alchemy", "OneHanded", "TwoHanded", "Archery", "Block",
           "HeavyArmor", "LightArmor", "Smithing", "Enchanting", "Alteration", "Conjuration", "Destruction", "Illusion",
           "Restoration")
_SKILL_WORDS = {w.lower(): s for s in _SKILLS for w in (s, SKILL_LABEL.get(s, s))} | \
    {w.lower(): "Speech" for w in SPEECH_LABELS}


def checks(conditions) -> list[tuple[str, object]]:
    """A line's checks the player can fail in front of the speaker: ("skill", skill) and ("gold", amount)."""
    out = []
    for c in conditions:
        if c.get("not"):
            continue
        if c["is"] == "skill_at_least":
            out.append(("skill", c["skill"]))
        elif c["is"] == "gold_at_least":
            out.append(("gold", c["gold"]))
    return out


def label_of(check) -> str:
    kind, v = check
    return f"{v} gold" if kind == "gold" else SKILL_LABEL.get(v, v)


def prompt_labels(prompt: str | None) -> list[tuple[str, object, str]]:
    """The check labels a prompt carries, as (kind, value, the words in brackets): ("skill", skill), ("gold", n), or
    ("threshold", skill) for a skill with a number; any other bracketed words are not a label."""
    out = []
    for inner in re.findall(r"\(([^()]*)\)", prompt or ""):
        w = inner.strip()
        m = re.fullmatch(r"(\d+) gold", w, re.IGNORECASE)
        if m:
            out.append(("gold", int(m.group(1)), w))
        elif w.lower() in _SKILL_WORDS:
            out.append(("skill", _SKILL_WORDS[w.lower()], w))
        else:
            m = re.fullmatch(r"([A-Za-z -]+?)\s+\d+", w)
            if m and m.group(1).lower() in _SKILL_WORDS:
                out.append(("threshold", _SKILL_WORDS[m.group(1).lower()], w))
    return out


def labelled(prompt: str, wanted) -> str:
    """The prompt with the label of every check in `wanted` it does not already carry, appended in brackets."""
    have = {(k, v) for k, v, _ in prompt_labels(prompt)}
    add = [label_of(c) for c in wanted if c not in have]
    return " ".join([prompt] + [f"({a})" for a in add])
# The rules over a set of forms played together (check_set).
SET_RULES = ("set-start", "set-stages", "result-limits")


def _schema(form) -> list[tuple[str, str]]:
    out = []
    for e in validate.errors(form):
        rule = "vocabulary" if (".conditions[" in e or ".results[" in e) else "schema"
        out.append((rule, e))
    return out


def _stage_sets(results) -> list[int]:
    return [r["stage"] for r in results if r["do"] == "set_stage"]


def start_on(form: dict, others: list[dict] | None) -> set[str] | None:
    """The refs on as the quest begins because the stages that start it switched them on: a stage of another form
    that is its `quest_stage` start or holds a `start_quest` result for it, its switches read in order; a ref counts
    when every such stage leaves it on. None when the quest is started by another quest and no starting stage is
    among `others` (the quest cannot be judged alone); an empty set for a quest a new game starts."""
    q = form["quest"]
    if q["start"]["by"] == "game":
        return set()
    stages = []
    for f in others or []:
        for s in f["stages"]:
            if (q["start"]["by"] == "quest_stage" and f["quest"]["id"] == q["start"]["quest"]
                    and s["number"] == q["start"]["quest_stage"]) or any(
                    r["do"] == "start_quest" and r["quest"] == q["id"] for r in s["results"]):
                stages.append(s)
    if not stages:
        return None
    ons = []
    for s in stages:
        on: dict[str, bool] = {}
        for r in s["results"]:
            if r["do"] in ("switch_on", "switch_off"):
                on[r["ref"]] = r["do"] == "switch_on"
        ons.append({ref for ref, v in on.items() if v})
    return set.intersection(*ons)


class Form:
    def __init__(self, f: dict, start_on: set[str] | None = frozenset()):
        self.f = f
        self.start_on = start_on        # refs on as the quest begins (start_on()); None: its starter is not known
        self.qid = f["quest"]["id"]
        self.stages = {s["number"]: s for s in f["stages"]}
        self.numbers = sorted(self.stages)
        self.refs = {r["id"]: r for r in f["refs"]}
        self.lines = f["lines"]
        self.triggers = f["triggers"]
        self.endings = [n for n, s in self.stages.items() if s["ending"] != "none"]
        self.first_end = min(self.endings) if self.endings else None

    def open_lines(self, n):
        return [ln for ln in self.lines if ln["first_stage"] <= n <= ln["last_stage"]]

    def open_triggers(self, n):
        return [t for t in self.triggers if t["prerequisite"] <= n and t["sets"] != n and n < t.get("until", 256)]

    def edges(self, n) -> set[int]:
        out = set(_stage_sets(self.stages[n]["results"]))
        for ln in self.open_lines(n):
            out |= set(_stage_sets(ln["results"]))
        out |= {t["sets"] for t in self.open_triggers(n)}
        out.discard(n)
        return out

    def causes(self, n, seen=None) -> list[tuple[str, str | None]]:
        """How stage n can be set, as (kind, reference): a line (its speaker), a take, use or death trigger (its
        reference), another quest's stage, the quest's start, a who-must-live death, another stage's results. A
        stage's `if_held` result happens as that stage begins, so it has that stage's causes."""
        seen = (seen or set()) | {n}
        out = [("line", ln["speaker"]) for ln in self.lines if n in _stage_sets(ln["results"])]
        out += [(t["kind"], t.get("ref")) for t in self.triggers if t["sets"] == n]
        if self.f["quest"]["start"]["stage"] == n:
            out.append(("start", None))
        out += [("death", m["ref"]) for m in self.f["must_live"] if m["fail_stage"] == n]
        for s in self.f["stages"]:
            for r in s["results"]:
                if r["do"] == "set_stage" and r["stage"] == n:
                    if "if_held" in r and s["number"] not in seen:
                        out += self.causes(s["number"], seen)
                    elif "if_held" not in r:
                        out.append(("stage", None))
        return out

    def item_of(self, ref_id) -> str:
        """The form's id for a placed item thing: a unique thing (a template item, or an item whose id is its own) by
        its ref id; a stock thing (gold, lockpicks) by its base."""
        r = self.refs[ref_id]
        base = r["placement"].get("base", {})
        if base.get("kind") == "item" and base.get("id") != ref_id:
            return base["id"]
        return ref_id

    def switches(self):
        """(stage from which it holds, ref, on) for every switch: a stage's own at that stage; a line's at the stage
        it sets, else (counted against the player) an off from its first stage and an on from its last."""
        out = []
        for n, s in self.stages.items():
            out += [(n, r["ref"], r["do"] == "switch_on") for r in s["results"] if r["do"] in ("switch_on", "switch_off")]
        for ln in self.lines:
            sets = _stage_sets(ln["results"])
            for r in ln["results"]:
                if r["do"] in ("switch_on", "switch_off"):
                    on = r["do"] == "switch_on"
                    at = min(sets) if sets else (ln["last_stage"] if on else ln["first_stage"])
                    out.append((at, r["ref"], on))
        return out

    def on_at(self, ref_id, n) -> bool:
        r = self.refs.get(ref_id)
        if r is None:
            return False
        state = r["enabled"] or ref_id in (self.start_on or ())
        for at, ref, on in sorted((s for s in self.switches() if s[1] == ref_id), key=lambda s: (s[0], s[2])):
            if at <= n:
                state = on
        return state

    def active_objectives(self, n):
        return [o for o in self.f["objectives"] if n in o["shown_at"] and n not in o["completed_at"]]

    def position(self, ref_id):
        r = self.refs.get(ref_id)
        if r is None:
            return None
        if "at" in r:
            return r["at"]
        box = r["placement"].get("container") or r["placement"].get("carried_by")
        return self.position(box) if box else None


def _named_stages(fm: Form):
    q = fm.f["quest"]
    yield "the quest's start", q["start"]["stage"]
    for o in fm.f["objectives"]:
        for n in o["shown_at"] + o["completed_at"]:
            yield f"objective {o['number']}", n
    for ln in fm.lines:
        yield f"line {ln['id']}", ln["first_stage"]
        yield f"line {ln['id']}", ln["last_stage"]
        for n in _stage_sets(ln["results"]):
            yield f"line {ln['id']}", n
        for c in ln["conditions"]:
            if c["is"].startswith("stage_") and c["quest"] == fm.qid:
                yield f"line {ln['id']}", c["stage"]
    for s in fm.f["stages"]:
        for n in _stage_sets(s["results"]):
            yield f"stage {s['number']}", n
    for t in fm.triggers:
        yield f"trigger {t['id']}", t["prerequisite"]
        yield f"trigger {t['id']}", t["sets"]
        if "until" in t:
            yield f"trigger {t['id']}", t["until"]
    for m in fm.f["must_live"]:
        yield f"who-must-live {m['ref']}", m["fail_stage"]
        for k in ("from", "to"):
            if k in m:
                yield f"who-must-live {m['ref']}", m[k]


def _named_refs(fm: Form):
    def from_results(where, results):
        for r in results:
            if "ref" in r:
                yield where, r["ref"]
    for ln in fm.lines:
        w = f"line {ln['id']}"
        yield w, ln["speaker"]
        yield from from_results(w, ln["results"])
        for c in ln["conditions"]:
            if "ref" in c:
                yield w, c["ref"]
    for s in fm.f["stages"]:
        yield from from_results(f"stage {s['number']}", s["results"])
    for o in fm.f["objectives"]:
        for t in o["targets"]:
            yield f"objective {o['number']}", t
    for t in fm.triggers:
        if "ref" in t:
            yield f"trigger {t['id']}", t["ref"]
    for m in fm.f["must_live"]:
        yield "who-must-live", m["ref"]
    for r in fm.f["refs"]:
        for box in (r["placement"].get("container"), r["placement"].get("carried_by")):
            if box:
                yield f"ref {r['id']}", box


def check(form, others: list[dict] | None = None) -> list[tuple[str, str]]:
    """Every rule over one form. `others`: the forms it is played with, from which the stage that starts it is read
    (what that stage switches on is on as the quest begins)."""
    out = _schema(form)
    if out:
        return out
    fm = Form(form, start_on(form, others))
    out += _unique(fm)
    out += [("stages-exist", f"{w} names stage {n}, which the quest does not have")
            for w, n in _named_stages(fm) if n not in fm.stages]
    out += [("refs-exist", f"{w} names {r}, which is not one of the form's refs")
            for w, r in _named_refs(fm) if r not in fm.refs]
    line_ids = {ln["id"] for ln in fm.lines}
    out += [("refs-exist", f"line {ln['id']} answers with {a}, which is not one of the form's lines")
            for ln in fm.lines for a in ln["answers"] if a not in line_ids]
    out += [("refs-exist", f"{w} locks or unlocks {r}, which is not a door")
            for w, res in _all_results(fm) for x in res if x["do"] in ("lock_door", "unlock_door")
            for r in [x["ref"]] if r in fm.refs and fm.refs[r]["kind"] != "door"]
    out += [("vocabulary", f"stage {s['number']}: speaker_hostile is a line's result (the speaker turns hostile)")
            for s in form["stages"] if any(r["do"] == "speaker_hostile" for r in s["results"])]
    out += [("vocabulary", f"line {ln['id']}: if_held is a stage's result (checked as the stage begins)")
            for ln in fm.lines if any("if_held" in r for r in ln["results"])]
    out += _placement(fm)
    out += _lock_owner_contents(fm)
    if out:
        return out          # the graph rules below need every named stage and ref to exist
    out += _item_ids(fm)
    out += _journal(fm)
    out += _graph(fm)
    out += _objectives(fm)
    out += _asked(fm)
    out += _completes(fm)
    out += _hand_in(fm)
    out += _held_take(fm)
    out += _windows(fm)
    out += _switch_cause(fm)
    out += _away(fm)
    out += _must_live(fm)
    out += _death_hostile(fm)
    out += _limits(fm)
    out += _speaks_first(fm)
    out += _stage_order(fm)
    out += _builder(fm)
    out += _said(fm)
    out += _regard(fm)
    out += _left(fm)
    out += _late(fm)
    out += _labels(fm)
    return out


def ways(fm: Form, cap: int = MAX_WAYS):
    """Every way the quest can stand, as (stage, the stages done, the triggers open): walked from the start over what
    is done, as the engine has it (a trigger is open while its prerequisite is done, its stage is not and the quest's
    stage is below its `until`); every result, line and trigger that sets a stage is taken as able to fire, but a line
    that asks the player to hold a thing a take trigger is still waiting for (taking it, or holding it as the
    trigger's prerequisite began, sets the trigger's stage); no other condition, nor an `if_held`, is read. None when
    the quest has more than `cap` ways."""
    start = fm.f["quest"]["start"]["stage"]
    lines = [(ln["first_stage"], ln["last_stage"], _stage_sets(ln["results"]),
              {c["item"] for c in ln["conditions"] if c["is"] == "item_count_at_least" and not c.get("not")})
             for ln in fm.lines]
    takes = [(fm.item_of(t["ref"]), t) for t in fm.triggers if t["kind"] == "take" and t["ref"] in fm.refs]

    def open_at(n, done):
        return [t for t in fm.triggers if t["prerequisite"] in done and t["sets"] not in done
                and n < t.get("until", 256)]

    def held(items, done):
        return not any(i in items and t["prerequisite"] in done and t["sets"] not in done for i, t in takes)
    seen, todo, out = {frozenset({start})}, [frozenset({start})], []
    while todo:
        done = todo.pop()
        n = max(done)
        trig = open_at(n, done)
        out.append((n, done, trig))
        if fm.stages[n]["ending"] != "none":
            continue
        nxt = set(_stage_sets(fm.stages[n]["results"])) | {t["sets"] for t in trig}
        nxt |= {m for a, b, sets, items in lines if a <= n <= b and held(items, done) for m in sets}
        for m in nxt - done:
            if m not in fm.stages:
                continue
            d = done | {m}
            if d not in seen:
                if len(seen) >= cap:
                    return None
                seen.add(d)
                todo.append(d)
    return out


def late_triggers(fm: Form) -> dict[str, int]:
    """Each death, take or use trigger that can fire after the quest has passed the stage it sets (it is open while a
    later stage, not an ending, is the quest's stage): its journal entry and objectives would come late and be untrue.
    By trigger id, the highest such stage."""
    w = ways(fm)
    out = {}
    for n, _done, trig in w or []:
        if fm.stages[n]["ending"] != "none":
            continue
        for t in trig:
            if t["kind"] in ("death", "take", "use") and n > t["sets"] and fm.stages[t["sets"]]["ending"] == "none":
                out[t["id"]] = max(out.get(t["id"], 0), n)
    return out


def _late(fm: Form):
    """A death, take or use trigger that sets a stage is open only while that stage can still come next: once the
    quest can stand at a later stage while it is open, it carries `until`, the stage from which it no longer fires.
    An `until` is above its prerequisite (else the trigger is never open)."""
    out = [("late-trigger", f"trigger {t['id']}: until {t['until']} is not above its prerequisite "
            f"{t['prerequisite']}, so it never fires") for t in fm.triggers
           if "until" in t and t["until"] <= t["prerequisite"]]
    for tid, n in sorted(late_triggers(fm).items()):
        t = next(x for x in fm.triggers if x["id"] == tid)
        out.append(("late-trigger", f"trigger {tid} can still set stage {t['sets']} once the quest is at stage {n}: "
                    "give it `until`, the stage from which it no longer fires"))
    return out


def _labels(fm: Form):
    """Every line with a skill or gold check says so on its prompt, as Skyrim does: "(Persuade)" for Speech, the
    skill's name for another, "(<n> gold)"; the lines of one speaker and prompt (a check and its fallback) share it.
    A label no line of the prompt checks, a check of another amount, or a threshold shown is refused."""
    out, groups = [], defaultdict(list)
    for ln in fm.lines:
        if ln["prompt"]:
            groups[(ln["speaker"], ln["prompt"])].append(ln)
    for (_who, prompt), lns in groups.items():
        want = {c for ln in lns for c in checks(ln["conditions"])}
        have = prompt_labels(prompt)
        ids = ", ".join(ln["id"] for ln in lns)
        for kind, v, words in have:
            if kind == "threshold":
                out.append(("check-label", f"line {ids}: the prompt shows a threshold ({words}): a check shows only "
                            f"its label ({label_of(('skill', v))})"))
            elif (kind, v) not in want:
                out.append(("check-label", f"line {ids}: the prompt's ({words}) is no check of the line"))
        got = {(k, v) for k, v, _ in have}
        out += [("check-label", f"line {ids}: its {c[0]} check {c[1]} is not on its prompt: add "
                 f"({label_of(c)})") for c in sorted(want - got, key=str)]
    return out


def _stage_order(fm: Form):
    """No result or trigger sets a stage at or below a stage that must already be done for it to fire: a stage's
    results set stages above it, a line's above its last stage, a trigger's above its prerequisite, a who-must-live
    row's failed ending above every stage of its window. What the engine reports after a lower stage is set was never
    measured, and nothing rests on it."""
    out = []
    for s in fm.f["stages"]:
        out += [("stage-order", f"stage {s['number']} sets stage {n}, not above it") for n in _stage_sets(s["results"])
                if n <= s["number"]]
    for ln in fm.lines:
        out += [("stage-order", f"line {ln['id']} (open to stage {ln['last_stage']}) sets stage {n}, not above its "
                 "window") for n in _stage_sets(ln["results"]) if n <= ln["last_stage"]]
    out += [("stage-order", f"trigger {t['id']} sets stage {t['sets']}, not above its prerequisite {t['prerequisite']}")
            for t in fm.triggers if t["sets"] <= t["prerequisite"]]
    live = [n for n in fm.numbers if fm.stages[n]["ending"] == "none"]
    for m in fm.f["must_live"]:
        top = max([n for n in live if n <= m.get("to", n)] or [0])
        if m["fail_stage"] <= top:
            out.append(("stage-order", f"who-must-live {m['ref']}: its failed ending {m['fail_stage']} is not above "
                        f"stage {top} of its window"))
    return out


def built_rows(fm: Form) -> int:
    """The quest's stage rows as the builder writes them (QuestForm.cs, "The stage rows"), without the rows other
    forms add (check_set counts those): the start checks, every result (a set_stage `if_held` is two), each objective
    completed and shown, the one SetActive, and on each ending the one row closing every objective, the side-quest
    count (not on a main quest) and Stop."""
    f, start = fm.f, fm.f["quest"]["start"]["stage"]
    n = sum(1 for m in f["must_live"] if m.get("from", start) <= start <= m.get("to", start))
    n += sum(1 for t in fm.triggers if t["kind"] == "death" and t["prerequisite"] == start)
    n += sum(1 + ("if_held" in r) for s in f["stages"] for r in s["results"])
    objs = f["objectives"]
    n += sum(len([x for x in o["completed_at"] if x in fm.stages]) + len([x for x in o["shown_at"] if x in fm.stages])
             for o in objs)
    n += 1 if objs else 0
    for s in f["stages"]:
        if s["ending"] != "none":
            n += bool(objs) + (s["ending"] == "completed" and f["quest"]["kind"] != "main") + 1
    return n


def added_rows(forms: list[dict]) -> dict[str, int]:
    """The rows each quest's stages carry for other forms: a quest started by its stage (one), another form's
    quest-stage trigger on it (two)."""
    out = defaultdict(int)
    for f in forms:
        st = f["quest"]["start"]
        if st["by"] == "quest_stage":
            out[st["quest"]] += 1
        for t in f["triggers"]:
            if t["kind"] == "quest_stage":
                out[t["quest"]] += 2
    return out


def _builder(fm: Form):
    """The builder's refusals a form alone shows (QuestForm.cs): one trigger script of a kind per ref (a who-must-live
    row without the message and without a window is a death script too); one speaks-first line in a quest; an answer
    line is some topic's answer, a topic or an answer has a prompt; a line's speaker is a person; only a new person is
    hostile; a thing made in a container is on from the start and is never switched, locked or used. (The builder's
    refusals that need the load order, an owner sharing a base or a lock that states what the reference has, are
    not here.)"""
    out, seen = [], defaultdict(list)
    for t in fm.triggers:
        if t.get("ref"):
            seen[(t["ref"], t["kind"])].append(t)
    for m in fm.f["must_live"]:
        if not m["main_message"]:
            seen[(m["ref"], "death")].append({"id": f"who-must-live {m['ref']}", "sets": None})
    for (ref, kind), ts in seen.items():
        names = ", ".join(t["id"] for t in ts)
        if kind == "take":          # takes setting one stage are one script; a new placement takes a second stage
            stages = {t["sets"] for t in ts}
            fresh = "existing" not in fm.refs[ref]["placement"] and not fm.refs[ref]["placement"].get("container")
            if len(stages) > (2 if fresh else 1):
                out.append(("trigger", f"{ref} is taken towards {len(stages)} stages ({names}): a placed thing of "
                            "ours is taken towards two at most, any other thing one"))
        elif len(ts) > 1:
            out.append(("trigger", f"{ref} carries {len(ts)} {kind} scripts ({names}): one trigger of a kind per "
                        "ref; make them one"))

    first = [ln["id"] for ln in fm.lines if ln["kind"] == "speaks_first"]
    if len(first) > 1:
        out.append(("speaks-first", f"{len(first)} speaks-first lines ({', '.join(first)}): a quest has one"))
    asked = {a for ln in fm.lines if ln["kind"] == "topic" for a in ln["answers"]}
    by_id = {ln["id"]: ln for ln in fm.lines}
    out += [("answer", f"answer line {ln['id']} is no topic's answer") for ln in fm.lines
            if ln["kind"] == "answer" and ln["id"] not in asked]
    out += [("answer", f"line {ln['id']} answers with {a}, which is not an answer line") for ln in fm.lines
            for a in ln["answers"] if a in by_id and by_id[a]["kind"] != "answer"]
    out += [("prompt", f"{ln['kind']} line {ln['id']} has no prompt") for ln in fm.lines
            if ln["kind"] in ("topic", "answer") and not ln["prompt"]]
    out += [("speaker", f"line {ln['id']}: {ln['speaker']} is not a person") for ln in fm.lines
            if fm.refs[ln["speaker"]]["kind"] != "person"]
    for r in fm.f["refs"]:
        p = r["placement"]
        if r.get("hostile") and (r["kind"] != "person" or "existing" in p):
            out.append(("hostile", f"ref {r['id']}: only a new person is hostile (its base of ours is made "
                        "aggressive)"))
        if p.get("container") and not r["enabled"]:
            out.append(("created", f"ref {r['id']}: a thing made in a container is there from the start (enabled)"))
    made = {r["id"] for r in fm.f["refs"] if r["placement"].get("container")}
    for where, res in _all_results(fm):
        out += [("created", f"{where} {x['do']} {x['ref']}, a thing made in a container, which has no reference")
                for x in res if x.get("ref") in made and x["do"] in ("switch_on", "switch_off", "lock_door",
                                                                     "unlock_door", "give_ownership")]
    out += [("created", f"trigger {t['id']}: a thing made in a container is taken, not used") for t in fm.triggers
            if t["kind"] == "use" and t.get("ref") in made]
    return out


def _said(fm: Form):
    """Every line can be said: no line has all the conditions of an earlier line of the same speaker, kind and prompt
    whose window covers its own (the engine says the first that holds, so the later never would)."""
    out = []
    for i, ln in enumerate(fm.lines):
        mine = {_ck(c) for c in ln["conditions"]}
        for e in fm.lines[:i]:
            if e["speaker"] == ln["speaker"] and e["kind"] == ln["kind"] and e["prompt"] == ln["prompt"] and \
                    e["first_stage"] <= ln["first_stage"] and ln["last_stage"] <= e["last_stage"] and \
                    {_ck(c) for c in e["conditions"]} <= mine:
                out.append(("line-said", f"line {ln['id']} can never be said: line {e['id']} before it holds whenever "
                            "it does"))
                break
    return out


def _ck(c) -> str:
    import json
    return json.dumps(c, sort_keys=True)


def _regard(fm: Form):
    out = []
    for where, res in _all_results(fm):
        out += [("regard-range", f"{where} changes regard by {x['by']}: regard is Skyrim's relationship rank, "
                 f"{REGARD_MIN} to {REGARD_MAX}; a step is 1 to 4") for x in res
                if x["do"] == "change_regard" and not 0 < abs(x["by"]) <= REGARD_MAX]
    out += [("regard-range", f"line {ln['id']} asks regard at least {c['value']}, outside {REGARD_MIN} to "
             f"{REGARD_MAX}") for ln in fm.lines for c in ln["conditions"]
            if c["is"] == "regard_at_least" and not REGARD_MIN < c["value"] <= REGARD_MAX]
    return out


def _left(fm: Form):
    """Leaving a stage completes every objective shown at it: each stage the quest moves to from a stage an
    objective is shown at (by the stage's results, a line open there or a trigger whose prerequisite it is; an ending
    closes every objective) is one of its `completed_at`."""
    out = []
    for o in fm.f["objectives"]:
        for s in o["shown_at"]:
            if s not in fm.stages:
                continue
            nxt = set(_stage_sets(fm.stages[s]["results"])) | {t["sets"] for t in fm.triggers if t["prerequisite"] == s}
            nxt |= {n for ln in fm.open_lines(s) for n in _stage_sets(ln["results"])}

            for t in sorted(nxt):
                if t in fm.stages and fm.stages[t]["ending"] == "none" and t not in o["completed_at"] and \
                        t not in o["shown_at"]:
                    out.append(("objective-left", f"objective {o['number']} shown at {s} stays shown when the quest "
                                f"moves to {t}: add {t} to its completed_at"))
    return out


def _all_results(fm: Form):
    yield from ((f"stage {s['number']}", s["results"]) for s in fm.f["stages"])
    yield from ((f"line {ln['id']}", ln["results"]) for ln in fm.lines)


def _hand_in(fm: Form):
    """A line that takes a thing from the player is gated on holding it, and is open from the stage at which any take
    trigger for that thing becomes open until the stage it sets: holding it early still lets the player hand it in,
    so the take trigger only ever moves an in-between stage."""
    out = []
    taken_bases = defaultdict(list)
    for t in fm.triggers:
        if t["kind"] == "take" and fm.refs[t["ref"]]["placement"].get("base", {}).get("kind") in ("item", "template_item"):
            taken_bases[fm.item_of(t["ref"])].append(t)
    for ln in fm.lines:
        for r in ln["results"]:
            if r["do"] != "take_item":
                continue
            if not any(c["is"] == "item_count_at_least" and not c.get("not") and c["item"] == r["item"]
                       and c["count"] >= r["count"]
                       for c in ln["conditions"]):
                out.append(("hand-in", f"line {ln['id']} takes {r['item']} and is not gated on the player holding it"))
            for t in taken_bases.get(r["item"], []):
                if not (ln["first_stage"] <= t["prerequisite"] and t["sets"] <= ln["last_stage"]):
                    out.append(("hand-in", f"line {ln['id']} takes {r['item']} and is not open from stage "
                                f"{t['prerequisite']} (where trigger {t['id']} opens) to stage {t['sets']}"))
    return out


def _unique(fm: Form):
    out = []
    for what, ids in (("stage", [s["number"] for s in fm.f["stages"]]),
                      ("objective", [o["number"] for o in fm.f["objectives"]]),
                      ("ref", [r["id"] for r in fm.f["refs"]]),
                      ("line", [ln["id"] for ln in fm.lines]),
                      ("trigger", [t["id"] for t in fm.triggers]),
                      ("who-must-live", [m["ref"] for m in fm.f["must_live"]])):
        seen = set()
        for i in ids:
            if i in seen:
                out.append(("unique-ids", f"{what} {i} appears twice"))
            seen.add(i)
    return out


def _placement(fm: Form):
    out = []
    for r in fm.f["refs"]:
        p = r["placement"]
        if "existing" in p:
            continue
        box, holder = p.get("container"), p.get("carried_by")
        if ("anchor" in p) + bool(box) + bool(holder) != 1:
            out.append(("placement", f"ref {r['id']}: a new placement has an anchor, a container or a carrier, exactly one"))
        if box and (r["kind"] != "thing" or fm.refs.get(box, {}).get("kind") != "thing"):
            out.append(("placement", f"ref {r['id']}: only a thing sits in a container, and the container is a thing"))
        if holder and (r["kind"] != "thing" or p["base"]["kind"] not in ("item", "template_item")
                       or fm.refs.get(holder, {}).get("kind") != "person"):
            out.append(("placement", f"ref {r['id']}: only an item thing is carried, and the carrier is a person"))
        if p["base"]["kind"] == "template_item" and (r["kind"] != "thing" or not r.get("name")):
            out.append(("placement", f"ref {r['id']}: a new item of ours is a thing with its own name"))
        if "level" in r and (r["kind"] != "person" or p["base"]["kind"] != "template_person"):
            out.append(("placement", f"ref {r['id']}: a fixed level is a new person's or creature's"))
        if "count" in r and (r["kind"] != "thing" or p["base"]["kind"] != "item" or "anchor" not in p):
            out.append(("placement", f"ref {r['id']}: a count is on a stock item placed by an anchor"))
    return out


def _lock_owner_contents(fm: Form):
    """A lock is on a door or a thing (a container), its key an item; an owner is on a thing and is a person of the
    form or a faction; contents are on a new container (an existing base placed by an anchor), each an item."""
    out = []

    def item_ref(rid, what, rule, word):
        if rid in fm.refs and fm.refs[rid]["kind"] != "thing":
            out.append((rule, f"ref {what}: {word} {rid} is a {fm.refs[rid]['kind']}, not an item"))
    for r in fm.f["refs"]:
        rid = r["id"]
        if "lock" in r:
            if r["kind"] not in ("door", "thing"):
                out.append(("lock", f"ref {rid}: only a door or a thing (a container) is locked"))
            if "key" in r["lock"]:
                item_ref(r["lock"]["key"], rid, "lock", "its key")
        if "owner" in r:
            if r["kind"] != "thing":
                out.append(("owner", f"ref {rid}: only a thing has an owner"))
            if r["owner"] in fm.refs and fm.refs[r["owner"]]["kind"] != "person":
                out.append(("owner", f"ref {rid}: its owner {r['owner']} is a {fm.refs[r['owner']]['kind']}, not a person or a faction"))
        if "contents" in r:
            p = r["placement"]
            if r["kind"] != "thing" or "anchor" not in p or p["base"]["kind"] != "existing_base":
                out.append(("contents", f"ref {rid}: contents are set on a new container: a thing of an existing base placed by an anchor"))
            out += [("contents", f"ref {rid}: content {c['item']} is a ref of the form: name an item by its own id")
                    for c in r["contents"] if c["item"] in fm.refs]
    for where, res in _all_results(fm):
        for x in res:
            if x["do"] == "give_ownership" and x["ref"] in fm.refs:
                r = fm.refs[x["ref"]]
                if r["kind"] != "thing" or "owner" not in r:
                    out.append(("owner", f"{where} gives the player {x['ref']}, which is not a thing with an owner"))
    return out


def _journal(fm: Form):
    out = []
    for n, s in sorted(fm.stages.items()):
        if s["shown"] and not (s["journal"] or "").strip():
            out.append(("journal-text", f"stage {n} shows in the journal and has no journal text"))
        if s["ending"] != "none" and not s["shown"]:
            out.append(("journal-text", f"stage {n} ends the quest and does not show in the journal"))
    return out


def _graph(fm: Form):
    out = []
    for n in fm.numbers:
        if fm.stages[n]["ending"] == "none" and not fm.edges(n):
            out.append(("way-out", f"stage {n} is not an ending and nothing moves the quest on from it"))
    start = fm.f["quest"]["start"]["stage"]
    seen, todo = {start}, [start]
    while todo:
        n = todo.pop()
        nxt = set(fm.edges(n))
        if fm.stages[n]["ending"] == "none":
            nxt |= {m["fail_stage"] for m in fm.f["must_live"]}
        for m in nxt - seen:
            seen.add(m)
            todo.append(m)
    out += [("reachable", f"stage {n} cannot be reached from the start (stage {start})")
            for n in fm.numbers if n not in seen]
    return out


def _objectives(fm: Form):
    out = []
    for n in fm.numbers:
        s = fm.stages[n]
        if not s["shown"] or s["ending"] != "none":
            continue
        objs = fm.active_objectives(n)
        if not objs:
            out.append(("objective-target-on", f"stage {n} shows in the journal and has no objective active at it"))
        for o in objs:
            for t in o["targets"]:
                if fm.on_at(t, n):
                    continue
                if fm.start_on is None:
                    out.append(("objective-target-on", f"stage {n}: objective {o['number']}'s target {t} is not on "
                                "by this form's own switches, and the stage that starts the quest is not among the "
                                "forms checked: check it with that quest's form"))
                else:
                    out.append(("objective-target-on", f"stage {n}: objective {o['number']}'s target {t} is not "
                                "switched on there (enabled, switched on by a stage at or before it, or by the stage "
                                "that starts the quest)"))
    return out


def _asked(fm: Form):
    out = []

    def asking(n):
        s = fm.stages.get(n)
        return s is not None and s["shown"] and s["ending"] == "none"

    def targeted(ref, n):
        return any(ref in o["targets"] for o in fm.active_objectives(n))
    for t in fm.triggers:
        if t["kind"] in ("take", "use") and asking(t["prerequisite"]) and not targeted(t["ref"], t["prerequisite"]):
            out.append(("asked-is-target", f"trigger {t['id']}: {t['ref']} is to be {'taken' if t['kind'] == 'take' else 'used'} at stage "
                        f"{t['prerequisite']} and no objective active there targets it"))
    for ln in fm.lines:
        if not _stage_sets(ln["results"]):
            continue
        for n in fm.numbers:
            if ln["first_stage"] <= n <= ln["last_stage"] and asking(n) and not targeted(ln["speaker"], n):
                out.append(("asked-is-target", f"line {ln['id']} moves the quest at stage {n} and no objective "
                            f"active there targets its speaker {ln['speaker']}"))
    return out


def _windows(fm: Form):
    out = []
    for ln in fm.lines:
        if ln["first_stage"] > ln["last_stage"]:
            out.append(("line-window", f"line {ln['id']}: first stage {ln['first_stage']} is after its last"))
        elif fm.first_end is not None and ln["first_stage"] < fm.first_end <= ln["last_stage"]:
            out.append(("line-window", f"line {ln['id']} is offered before the first ending ({fm.first_end}) "
                        f"and stays open to stage {ln['last_stage']}"))
    return out


def _away_one(fm: Form, cause, ref, where):
    a, b = fm.position(cause), fm.position(ref)
    if a is None or b is None:
        who = cause if a is None else ref
        return [("away", f"{where} switches {ref}: {who} has no position, so it cannot be shown away from the player")]
    if a["cell"] == b["cell"]:
        return [("away", f"{where} switches {ref} in the same cell as {cause}, where the player is")]
    if a["interior"] or b["interior"]:
        return []
    d = math.dist((a["x"], a["y"], a["z"]), (b["x"], b["y"], b["z"]))
    if d < AWAY_UNITS:
        return [("away", f"{where} switches {ref} {d:.0f} units from {cause} outdoors (away is {AWAY_UNITS:.0f} "
                 "or more)")]
    return []


def _limits(fm: Form):
    out = []
    n = built_rows(fm)
    if n > MAX_STAGE_RESULTS:
        out.append(("result-limits", f"the stages hold {n} rows once built, over {MAX_STAGE_RESULTS}"))

    out += [("result-limits", f"line {ln['id']} holds {len(ln['results'])} results, over {MAX_LINE_RESULTS}")
            for ln in fm.lines if len(ln["results"]) > MAX_LINE_RESULTS]
    return out


def _switch_results(results):
    return [r for r in results if r["do"] in ("switch_on", "switch_off")]


def _away(fm: Form):
    out = []
    for ln in fm.lines:
        for r in _switch_results(ln["results"]):
            out += _away_one(fm, ln["speaker"], r["ref"], f"line {ln['id']}")
    for n in fm.numbers:
        for r in _switch_results(fm.stages[n]["results"]):
            for kind, c in fm.causes(n):
                if kind in ("line", "take", "use"):
                    out += _away_one(fm, c, r["ref"], f"stage {n}")
    return out


def _switch_cause(fm: Form):
    out = []
    for n in fm.numbers:
        if not _switch_results(fm.stages[n]["results"]):
            continue
        for kind, c in sorted(set(fm.causes(n)), key=str):
            if kind not in ("line", "take", "use"):
                what = {"death": f"the death of {c}", "quest_stage": "another quest's stage",
                        "start": "the quest's start", "stage": "another stage's results"}[kind]
                out.append(("switch-cause", f"stage {n} switches a reference and can be set by {what}, where the "
                            "player could be anywhere: switch only on a line, a take or a use"))
    return out


def _completes(fm: Form):
    out = []
    for o in fm.f["objectives"]:
        for s in o["shown_at"]:
            for t in o["completed_at"]:
                for ln in fm.open_lines(s):
                    concerns = {ln["speaker"]} | {x["item"] for x in ln["conditions"] + ln["results"] if "item" in x}
                    if t in _stage_sets(ln["results"]) and not concerns & set(o["targets"]):
                        out.append(("completes-on-target", f"objective {o['number']} is completed by line "
                                    f"{ln['id']}, whose speaker {ln['speaker']} is not one of its targets"))
                for tr in fm.open_triggers(s):
                    if tr["sets"] == t and tr["kind"] in ("take", "use") and tr.get("ref") not in o["targets"]:
                        out.append(("completes-on-target", f"objective {o['number']} is completed by trigger "
                                    f"{tr['id']}, which concerns none of its targets"))
    return out


def _death_hostile(fm: Form):
    lives = {m["ref"] for m in fm.f["must_live"]}
    return [("death-hostile", f"trigger {t['id']}: {t['ref']} is neither hostile nor a who-must-live person, and "
             "the kill is not marked the player's choice")
            for t in fm.triggers if t["kind"] == "death" and not fm.refs[t["ref"]].get("hostile")
            and t["ref"] not in lives and not t.get("choice")]


def _must_live(fm: Form):
    out = [("must-live-fails", f"who-must-live {m['ref']}: stage {m['fail_stage']} is not a failed ending")
           for m in fm.f["must_live"] if fm.stages[m["fail_stage"]]["ending"] != "failed"]
    first = min((n for n, s in fm.stages.items() if s["shown"] and s["ending"] == "none"), default=None)
    for m in fm.f["must_live"]:
        lo = m.get("from", fm.f["quest"]["start"]["stage"])
        if "to" in m and lo > m["to"]:
            out.append(("must-live-window", f"who-must-live {m['ref']}: from {lo} is after to {m['to']}"))
        if first is not None and lo < first:
            out.append(("must-live-window", f"who-must-live {m['ref']} holds from stage {lo}, before the quest's "
                        f"first shown stage {first}: a death there would fail a quest the player has not begun"))
    if fm.f["quest"]["kind"] == "minor":
        out += [("main-message", f"who-must-live {m['ref']}: a minor quest's death shows no message; it only fails "
                 "the quest") for m in fm.f["must_live"] if m["main_message"]]
    return out


def _speaks_first(fm: Form):
    out = []
    for ln in fm.lines:
        if ln["kind"] != "speaks_first":
            continue
        twin = [m for m in fm.lines if m["kind"] in ("topic", "greeting") and m["speaker"] == ln["speaker"]
                and m["text"] == ln["text"] and m["results"] == ln["results"]
                and m["first_stage"] <= ln["first_stage"] and ln["last_stage"] <= m["last_stage"]]
        if not twin:
            out.append(("speaks-first-has-line", f"line {ln['id']} speaks first and has no ordinary line with the "
                        "same speaker, words, results and stages"))
    return out


def _item_ids(fm: Form):
    """One id for one thing: a condition, a result, an if_held or a lock's key names a unique thing by its ref id and a
    stock item by its base, never a unique thing's base (it would count every item of that base) nor a stock thing's
    ref."""
    out = []
    unique_base = {}
    for r in fm.f["refs"]:
        b = r["placement"].get("base", {})
        if r["kind"] == "thing" and b.get("kind") in ("item", "template_item") and fm.item_of(r["id"]) == r["id"] \
                and b["id"] != r["id"]:
            unique_base[b["id"]] = r["id"]

    def one(where, item):
        if item in fm.refs:
            r = fm.refs[item]
            if r["kind"] != "thing" or r["placement"].get("base", {}).get("kind") not in ("item", "template_item"):
                out.append(("item-id", f"{where} names {item}, which is no item thing"))
            elif fm.item_of(item) != item:
                out.append(("item-id", f"{where} names the stock thing {item}: name its item {fm.item_of(item)}"))
        elif item in unique_base:
            out.append(("item-id", f"{where} names {item}, the base of the quest thing {unique_base[item]}: name the "
                        "thing"))
    for where, res in _all_results(fm):
        for x in res:
            for k in ("item", "if_held"):
                if k in x:
                    one(where, x[k])
    for ln in fm.lines:
        for c in ln["conditions"]:
            if "item" in c:
                one(f"line {ln['id']}", c["item"])
    for r in fm.f["refs"]:
        if r.get("lock", {}).get("key"):
            one(f"ref {r['id']} lock", r["lock"]["key"])
    return out


def _held_take(fm: Form):
    """A take trigger moves the quest only when the thing is taken while it is open; a thing already held as its
    prerequisite stage begins moves it by that stage's own result: set_stage to the trigger's stage if_held the item."""
    out = []
    for t in fm.triggers:
        if t["kind"] != "take":
            continue
        item = fm.item_of(t["ref"])
        want = {"do": "set_stage", "stage": t["sets"], "if_held": item}
        if want not in fm.stages[t["prerequisite"]]["results"]:
            out.append(("held-take", f"trigger {t['id']}: stage {t['prerequisite']} does not set stage {t['sets']} "
                        f"as it begins when {item} is already held"))
    return out


def check_set(forms: list[dict]) -> list[tuple[str, str]]:
    """The rules over forms played together. `set-start`: a quest not running from a new game is started one way
    only: by its `quest_stage` start (no form's result starts it as well), or by `start_quest` results that all set
    its start stage and can only fire once in a play (all on one stage, or each on an ending of one quest); a quest
    running from a new game is started by nothing else. `set-stages`: every other quest's stage a form names (its
    start, a trigger, a condition, a start_quest result) is a stage of a form of the set."""
    out = []
    by_id = {f["quest"]["id"]: f for f in forms}
    stages = {q: {s["number"]: s for s in f["stages"]} for q, f in by_id.items()}
    starters = defaultdict(list)          # quest -> [(from quest, where, stage set, the source stage or None)]
    for f in forms:
        q = f["quest"]["id"]
        for s in f["stages"]:
            for r in s["results"]:
                if r["do"] == "start_quest":
                    starters[r["quest"]].append((q, f"stage {s['number']}", r["stage"], s["number"]))
        for ln in f["lines"]:
            for r in ln["results"]:
                if r["do"] == "start_quest":
                    starters[r["quest"]].append((q, f"line {ln['id']}", r["stage"], None))

    def named(q, where, other, n):
        if other not in by_id:
            out.append(("set-stages", f"{q}: {where} names {other}, which is not in the set"))
        elif n not in stages[other]:
            out.append(("set-stages", f"{q}: {where} names stage {n} of {other}, which it does not have"))
    for q, f in sorted(by_id.items()):
        st = f["quest"]["start"]
        got = starters.get(q, [])
        if st["by"] == "quest_stage":
            named(q, "its start", st["quest"], st["quest_stage"])
        for frm, where, n, _src in got:
            if n != st["stage"]:
                out.append(("set-start", f"{q}: {frm} {where} starts it at stage {n}, not its start stage "
                            f"{st['stage']}"))
        if st["by"] in ("game", "quest_stage") and got:
            how = "a new game" if st["by"] == "game" else f"{st['quest']}'s stage {st['quest_stage']}"
            out += [("set-start", f"{q}: started by {how} and also by {frm} {where}") for frm, where, _, _ in got]
        if st["by"] == "start_quest":
            if not got:
                out.append(("set-start", f"{q}: started by a start_quest result and no form of the set has one"))
            else:
                srcs = {(frm, src) for frm, _, _, src in got}
                quests = {frm for frm, _ in srcs}
                once = len(srcs) == 1 or (len(quests) == 1 and all(
                    src is not None and stages[frm][src]["ending"] != "none" for frm, src in srcs))
                if not once:
                    out.append(("set-start", f"{q}: started by {len(got)} results that can fire in one play: "
                                + ", ".join(f"{frm} {where}" for frm, where, _, _ in got)))
        for t in f["triggers"]:
            if t["kind"] == "quest_stage":
                named(q, f"trigger {t['id']}", t["quest"], t["quest_stage"])
        for ln in f["lines"]:
            for c in ln["conditions"]:
                if c["is"].startswith("stage_") and c["quest"] != q:
                    named(q, f"line {ln['id']}", c["quest"], c["stage"])
    extra = added_rows(forms)
    for q, f in sorted(by_id.items()):
        n = built_rows(Form(f)) + extra.get(q, 0)
        if extra.get(q) and n > MAX_STAGE_RESULTS:
            out.append(("result-limits", f"{q}: its stages hold {n} rows once built with the rows other forms add, "
                        f"over {MAX_STAGE_RESULTS}"))
    for target, got in sorted(starters.items()):
        for frm, where, n, _ in got:
            named(frm, where, target, n)
    return out


def summary(fails) -> dict[str, int]:
    by = defaultdict(int)
    for rule, _ in fails:
        by[rule] += 1
    return dict(by)
