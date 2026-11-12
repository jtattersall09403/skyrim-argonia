"""The quest form's structural checks: what the schema alone cannot say (docs/design/quest-form.md, "The rules").

`check(form)` returns every failure as (rule, one line). The schema runs first; a form that breaks it gets no
structural check (its shape is not known). Stage windows, as the paper game and the builder read them:
- a line is open at every stage numbered from its first stage to its last;
- a trigger is open at every stage numbered from its prerequisite up to, not including, the stage it sets;
- an objective is active at a stage it is shown at and is not completed at.
"""
from __future__ import annotations

import math
from collections import defaultdict

from tools.questform import validate

# A switch on or off happens "away from the player": the switched reference stands in another interior cell than
# the speaker or thing that causes it, or across the interior/exterior line from it, or, both outdoors, at least this
# many units from it (docs/research/skyrim/quest-form-engine-facts.md).
AWAY_UNITS = 18000.0
# The engine's limits on result rows: all of a quest's stages together, and one line.
MAX_STAGE_RESULTS = 128
MAX_LINE_RESULTS = 128

RULES = ("schema", "vocabulary", "unique-ids", "stages-exist", "refs-exist", "placement", "journal-text",
         "way-out", "reachable", "objective-target-on", "asked-is-target", "completes-on-target", "hand-in", "line-window",
         "switch-cause", "away", "must-live-fails", "main-message", "death-hostile", "result-limits", "speaks-first-has-line")


def _schema(form) -> list[tuple[str, str]]:
    out = []
    for e in validate.errors(form):
        rule = "vocabulary" if (".conditions[" in e or ".results[" in e) else "schema"
        out.append((rule, e))
    return out


def _stage_sets(results) -> list[int]:
    return [r["stage"] for r in results if r["do"] == "set_stage"]


class Form:
    def __init__(self, f: dict):
        self.f = f
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
        return [t for t in self.triggers
                if (t["prerequisite"] <= n < t["sets"]) or (t["sets"] <= t["prerequisite"] == n)]

    def edges(self, n) -> set[int]:
        out = set(_stage_sets(self.stages[n]["results"]))
        for ln in self.open_lines(n):
            out |= set(_stage_sets(ln["results"]))
        out |= {t["sets"] for t in self.open_triggers(n)}
        out.discard(n)
        return out

    def causes(self, n) -> list[tuple[str, str | None]]:
        """How stage n can be set, as (kind, reference): a line (its speaker), a take, use or death trigger (its
        reference), another quest's stage, the quest's start, a who-must-live death, another stage's results."""
        out = [("line", ln["speaker"]) for ln in self.lines if n in _stage_sets(ln["results"])]
        out += [(t["kind"], t.get("ref")) for t in self.triggers if t["sets"] == n]
        if self.f["quest"]["start"]["stage"] == n:
            out.append(("start", None))
        out += [("death", m["ref"]) for m in self.f["must_live"] if m["fail_stage"] == n]
        out += [("stage", None) for s in self.f["stages"] if n in _stage_sets(s["results"])]
        return out

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
        state = r["enabled"]
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
        box = r["placement"].get("container")
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
    for m in fm.f["must_live"]:
        yield f"who-must-live {m['ref']}", m["fail_stage"]


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
        box = r["placement"].get("container")
        if box:
            yield f"ref {r['id']}", box


def check(form) -> list[tuple[str, str]]:
    out = _schema(form)
    if out:
        return out
    fm = Form(form)
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
    out += _placement(fm)
    if out:
        return out          # the graph rules below need every named stage and ref to exist
    out += _journal(fm)
    out += _graph(fm)
    out += _objectives(fm)
    out += _asked(fm)
    out += _completes(fm)
    out += _hand_in(fm)
    out += _windows(fm)
    out += _switch_cause(fm)
    out += _away(fm)
    out += _must_live(fm)
    out += _death_hostile(fm)
    out += _limits(fm)
    out += _speaks_first(fm)
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
        if t["kind"] == "take":
            base = fm.refs[t["ref"]]["placement"].get("base", {})
            if base.get("kind") == "item":
                taken_bases[base["id"]].append(t)
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
        has_anchor, box = "anchor" in p, p.get("container")
        if has_anchor == bool(box):
            out.append(("placement", f"ref {r['id']}: a new placement has an anchor or a container, exactly one"))
        if box and (r["kind"] != "thing" or fm.refs.get(box, {}).get("kind") != "thing"):
            out.append(("placement", f"ref {r['id']}: only a thing sits in a container, and the container is a thing"))
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
        elif not any(fm.on_at(t, n) for o in objs for t in o["targets"]):
            out.append(("objective-target-on", f"stage {n}: no objective active at it has a target switched on"))
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
    n = sum(len(s["results"]) for s in fm.f["stages"])
    if n > MAX_STAGE_RESULTS:
        out.append(("result-limits", f"the stages hold {n} results in all, over {MAX_STAGE_RESULTS}"))
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
                    if t in _stage_sets(ln["results"]) and ln["speaker"] not in o["targets"]:
                        out.append(("completes-on-target", f"objective {o['number']} is completed by line "
                                    f"{ln['id']}, whose speaker {ln['speaker']} is not one of its targets"))
                for tr in fm.open_triggers(s):
                    if tr["sets"] == t and tr.get("ref") not in o["targets"]:
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


def summary(fails) -> dict[str, int]:
    by = defaultdict(int)
    for rule, _ in fails:
        by[rule] += 1
    return dict(by)
