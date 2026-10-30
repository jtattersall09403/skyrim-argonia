"""The quest generator's first rung (1.4; 2.12 §a): quest record rows -> one QUST, its begin fragments and its stage
graph as core data.

From the rows (read through quest_record.export, so the record's own view is the input) it derives three things,
each regenerated and never edited:

- **the QUST** as an intermediate record (tools/ArgoniaGen/QuestRecords.cs writes it): stages with their log
  entries (the stage's journal text; a stage still waiting for its text gets a placeholder the records check
  flags), objectives with their text and *no target data* (no markers, old 0137), a reference alias per cast
  member and thing, forced to the reference a built place lays for it (Optional, never Essential or Protected: nobody is unkillable, old 0138), and the begin
  fragments bound to their stages. Stage 0 is the generator's own start-up stage: it hands the quest to ArgoniaCore.
- **the begin fragments** (papyrus/generated/ARG_QF_<code>.psc, compiled on the game machine by the CK's
  compiler): only what needs the engine's own quest functions (objectives shown, all completed or failed) and one
  ArgoniaCore native per action. No condition is evaluated in Papyrus.
- **the stage graph** (skse/core/generated/argonia/core/quests.h): each stage's edges in the rule's order
  (fail-forwards first, then successors, each in record order) with their conditions as predicate trees, the
  objectives' completion conditions and the start condition. skse/core's quest_runtime walks it on every fact
  change and returns the stage to set; ArgoniaCore calls SetStage.

Native names: an action verb `fooBar` is the global native `ArgoniaCore.FooBar`, every id a String, a count Int, a
flag Bool. The quest's own setStage is Papyrus's SetStage.

    python3 -m tools.argonia_world.quest_gen            # write the fragments and quests.h
    python3 -m tools.argonia_world.quest_gen --check    # exit 1 when they are stale or the records check fails
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from tools.argonia_world import db, quest_record, stage_walk
from tools.argonia_world import skyrim_units as su
from tools.argonia_world.core_tables import ident, num, sv

REPO = Path(__file__).resolve().parents[2]
PAPYRUS = REPO / "papyrus" / "generated"
HEADER = REPO / "skse" / "core" / "generated" / "argonia" / "core" / "quests.h"

# The quests in the game. 1.4: one; 2.12 widens it to every slice quest once its record is reviewed.
QUESTS = ("quest.local.lf83",)

# Tier protection (old 0030; 40-factions §30b): tier 0 main, 2 faction, 3 everything else. The QUST's priority
# carries the tier (a higher tier's quest wins any shared engine arbitration); the write rule is the records check.
PRIORITY_BY_TIER = {0: 90, 1: 70, 2: 60, 3: 40}
TYPE_BY_GROUP = {"main": "MainQuest", "faction": "Misc", "daedric": "Daedric"}  # anything else: SideQuest
# Action verbs that change what they name: a quest may use them only on ids its touches list writes.
BREAKING = {"setFlag", "applyLocalVariant", "clearLocalVariant", "disableRef", "enableRef", "moveRef", "setSchedule",
            "promoteSuccessor", "setDoorAccess", "removeTopic", "setStage", "completeQuest", "failQuest", "setAmbience",
            "setMaterialFlag", "addCounter"}
PLACEHOLDER = "[not yet written: "
KIND = {None: 0, "complete": 1, "failed": 2}  # journal::Kind
STARTUP = 0  # the generator's start-up stage


def edid(q: dict) -> str:
    return f"ARG_Q_{q['code']}"


def script(q: dict) -> str:
    return f"ARG_QF_{q['code']}"


def _as_list(a) -> list:
    return a if isinstance(a, list) else [a]


@dataclass
class Plan:
    """One quest's record (the YAML view) and the indices the generator gives it."""
    q: dict
    objectives: dict = field(default_factory=dict)   # (stage, objective id) -> objective index

    @property
    def stages(self) -> list[dict]:
        return self.q.get("stages") or []

    @property
    def endings(self) -> dict:
        return {e["id"]: e for e in self.q.get("endings") or []}


def plan(w: db.World, quest_id: str) -> Plan:
    p = Plan(quest_record.export(w, quest_id))
    for st in p.stages:
        if st["id"] == STARTUP:
            raise ValueError(f"{quest_id}: stage 0 is the generator's start-up stage")
        objs = st.get("objectives") or []
        if len(objs) > 9:
            raise ValueError(f"{quest_id} stage {st['id']}: more than nine objectives")
        for i, o in enumerate(objs):
            p.objectives[(st["id"], o["id"])] = st["id"] + i
    if len(set(p.objectives.values())) != len(p.objectives):
        raise ValueError(f"{quest_id}: two objectives share an index (stages closer than ten apart)")
    return p


# --- the QUST (intermediate record) ----------------------------------------------------------------------------
def _alias_name(i: str) -> str:
    return "".join(x.capitalize() for x in re.split(r"[^0-9A-Za-z]+", i.rsplit(".", 1)[-1]) if x)[:60]


def qust(alloc, p: Plan, forced: dict[str, str] | None = None) -> dict:
    """`forced`: cast or thing id -> the FormKey of the reference a built place lays for it (place_build.placed)."""
    q = p.q
    stages = [{"index": STARTUP, "flags": ["StartUpStage"]}]
    for st in p.stages:
        kind = st.get("ending")
        text = st.get("journalText") or f"{PLACEHOLDER}{st.get('journal') or q['code'] + ' stage ' + str(st['id'])}]"
        entry = {"text": text}
        if kind:
            entry["flags"] = ["CompleteQuest" if kind == "complete" else "FailQuest"]
        stages.append({"index": st["id"], "log": [entry]})
    objectives = [{"index": p.objectives[(st["id"], o["id"])],
                   "text": o.get("objectiveText") or f"{PLACEHOLDER}{o['text']}]"}
                  for st in p.stages for o in st.get("objectives") or []]
    aliases = [{"id": i, "name": _alias_name(x["id"]), "flags": ["Optional", "AllowDead", "AllowDisabled"]}
               for i, x in enumerate([*(q.get("cast") or []), *(q.get("things") or [])])]
    for a, x in zip(aliases, [*(q.get("cast") or []), *(q.get("things") or [])]):
        if (forced or {}).get(x["id"]):
            a["forcedRef"] = forced[x["id"]]
    if len({a["name"] for a in aliases}) != len(aliases):
        raise ValueError(f"{q['id']}: two aliases share a name {[a['name'] for a in aliases]}")
    key = alloc.form_key(edid(q), "QUST", q["id"])
    return {
        "type": "QUST", "edid": edid(q), "formKey": key, "name": q["title"],
        "flags": ["StartGameEnabled", "RunOnce"], "priority": PRIORITY_BY_TIER[q["tier"]],
        "questType": TYPE_BY_GROUP.get(q["group"], "SideQuest"),
        "stages": stages, "objectives": objectives, "aliases": aliases,
        "scripts": [{"name": script(q), "properties": []}],
        "fragments": {"script": script(q), "stages": [s["index"] for s in stages]},
    }


def layers(alloc, w: db.World):
    from tools.argonia_world.intermediate import Layer
    from tools.argonia_world import place_build
    forced = {k: place_build.ref_form_key(alloc, w.get("build_ref", v)) for k, v in place_build.placed(w).items()}
    return [Layer(f"quest:{qid.rsplit('.', 1)[-1]}", [qust(alloc, plan(w, qid), forced)]) for qid in QUESTS]


# --- the begin fragments (Papyrus) -----------------------------------------------------------------------------
def _pv(v) -> str:
    if isinstance(v, bool):
        return "True" if v else "False"
    if isinstance(v, (int, float)):
        return str(num(v)) if not float(v).is_integer() else str(int(v))
    if not re.fullmatch(r"[0-9A-Za-z._' -]+", str(v)):
        raise ValueError(f"{v!r}: not a Papyrus-safe id")
    return f'"{v}"'


def native(term: str) -> str:
    return "ArgoniaCore." + term[0].upper() + term[1:]


def _action(p: Plan, a: dict) -> str:
    (term, args), = a.items()
    args = _as_list(args)
    if term == "setStage" and args[0] == p.q["id"]:
        return f"SetStage({int(args[1])})"
    return f"{native(term)}({', '.join(_pv(x) for x in args)})"


def fragment_calls(p: Plan, st: dict | None) -> list[str]:
    """The lines of one stage's begin fragment (None: the start-up stage)."""
    if st is None:
        return ["ArgoniaCore.WatchQuest(self)"]
    out = [f"ArgoniaCore.AddJournalEntry(self, {st['id']}, {KIND[st.get('ending')]})"]
    out += [f"SetObjectiveDisplayed({p.objectives[(st['id'], o['id'])]})" for o in st.get("objectives") or []]
    out += [_action(p, a) for a in st.get("onEnter") or []]
    if st.get("ending"):
        e = p.endings.get(st.get("endingId"))
        if e is None:
            raise ValueError(f"{p.q['id']} stage {st['id']}: ending {st.get('endingId')!r} has no row")
        out += [_action(p, a) for a in (e.get("world") or []) + (e.get("rewards") or [])]
        out += ["CompleteAllObjectives()" if st["ending"] == "complete" else "FailAllObjectives()",
                "ArgoniaCore.UnwatchQuest(self)"]
    return out


def papyrus(p: Plan) -> str:
    q = p.q
    lines = [";GENERATED by tools/argonia_world/quest_gen.py from the world database; never edited (decision 0009).",
             f";{q['code']} {q['title']}: begin fragments only. The stage graph is skse/core quest_runtime's (quests.h);",
             ";ArgoniaCore sets each stage, and a fragment does only what needs the engine or an ArgoniaCore action native.",
             f"Scriptname {script(q)} Extends Quest Hidden", ""]
    for st in [None, *p.stages]:
        n = STARTUP if st is None else st["id"]
        lines += [f";BEGIN FRAGMENT Fragment_{n}", f"Function Fragment_{n}()", ";BEGIN CODE"]
        lines += ["  " + c for c in fragment_calls(p, st)]
        lines += [";END CODE", "EndFunction", ";END FRAGMENT", ""]
    return "\n".join(lines)


NATIVE_CALL = re.compile(r"ArgoniaCore\.(\w+)\(([^()]*)\)")


def natives(texts) -> dict[str, list[str]]:
    """Every ArgoniaCore native the fragments call, with its Papyrus argument types."""
    out: dict[str, list[str]] = {}
    for t in texts:
        for name, args in NATIVE_CALL.findall(t):
            kinds = []
            for a in [x.strip() for x in args.split(",") if x.strip()]:
                kinds.append("Quest" if a == "self" else "String" if a.startswith('"') else
                             "Bool" if a in ("True", "False") else "Int" if re.fullmatch(r"-?\d+", a) else "Float")
            if out.setdefault(name, kinds) != kinds:
                raise ValueError(f"ArgoniaCore.{name}: called as {out[name]} and as {kinds}")
    return dict(sorted(out.items()))


# --- the stage graph (C++ data for quest_runtime) --------------------------------------------------------------
def graph(p: Plan) -> dict:
    """The stage graph in the record's own condition form, edges in the rule's order: what quests.h encodes and
    what stage_walk walks back (the L2 check)."""
    q = p.q
    return {"id": q["id"], "start": q.get("start", min(s["id"] for s in p.stages)), "startWhen": q.get("startWhen"),
            "stages": [{"id": st["id"], "ending": st.get("ending"),
                        "objectives": [{"id": o["id"], "index": p.objectives[(st["id"], o["id"])],
                                        "completeWhen": o["completeWhen"]} for o in st.get("objectives") or []],
                        "failForward": [{"to": e["to"], "when": e["when"]} for e in st.get("failForward") or []],
                        "successors": [{"to": e["to"], "when": e["when"]} for e in st.get("successors") or []]}
                       for st in p.stages]}


def _cpp_arg(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return num(v)
    return f"std::string({sv(str(v))})"


def _cpp_pred(c) -> str:
    (term, a), = c.items()
    if term in ("all", "any"):
        return f"P{{T::{ident(term)}, {{}}, {{{', '.join(_cpp_pred(k) for k in a)}}}}}"
    if term == "not":
        return f"P{{T::not_, {{}}, {{{_cpp_pred(a)}}}}}"
    return f"P{{T::{ident(term)}, {{{', '.join(_cpp_arg(x) for x in _as_list(a))}}}, {{}}}}"


def header(graphs: list[dict]) -> str:
    b = ["// quests.h: GENERATED by tools/argonia_world/quest_gen.py from the world database (decision 0030).",
         "// The stage graph of every quest in the game, for quest_runtime. Do not edit: change the rows and regenerate.",
         "#pragma once", '#include "argonia/core/quest_runtime.h"', "", "#include <string>", "#include <vector>", "",
         "namespace argonia::core::gen {", "",
         "inline std::vector<::argonia::core::quest_runtime::Graph> quest_graphs() {",
         "  using P = ::argonia::core::conditions::Pred;", "  using T = Term;",
         "  using namespace ::argonia::core::quest_runtime;",
         "  std::vector<Graph> out;"]
    for g in graphs:
        sw = f"std::optional<P>({_cpp_pred(g['startWhen'])})" if g["startWhen"] else "std::nullopt"
        b += [f"  {{  // {g['id']}", f"    Graph q{{{sv(g['id'])}, {g['start']}, {sw}, {{}}}};"]
        for st in g["stages"]:
            ending = {"complete": "Ending::complete", "failed": "Ending::failed"}.get(st["ending"], "Ending::none")
            b += [f"    q.stages.push_back(Stage{{{st['id']}, {ending}, {{}}, {{}}}});"]
            for o in st["objectives"]:
                b += [f"    q.stages.back().objectives.push_back(Objective{{{o['index']}, {sv(o['id'])}, "
                      f"{_cpp_pred(o['completeWhen'])}}});"]
            for kind, key in (("true", "failForward"), ("false", "successors")):
                for e in st[key]:
                    b += [f"    q.stages.back().edges.push_back(Edge{{{e['to']}, {kind}, {_cpp_pred(e['when'])}}});"]
        b += ["    out.push_back(std::move(q));", "  }"]
    b += ["  return out;", "}", "", "}  // namespace argonia::core::gen", ""]
    return "\n".join(b)


# --- the records check (L1) ------------------------------------------------------------------------------------
def check_records(records: list[dict]) -> list[str]:
    """No objective carries target data, no map marker shows before it is reached, no placeholder text, no alias
    the engine protects (old 0137, 0138)."""
    errs = []
    for r in records:
        if r["type"] == "QUST":
            for o in r.get("objectives") or []:
                if set(o) - {"index", "text", "flags"}:
                    errs.append(f"{r['edid']} objective {o['index']}: carries {sorted(set(o) - {'index', 'text', 'flags'})} "
                                "(no target markers: objective target data is omitted)")
                if o["text"].startswith(PLACEHOLDER):
                    errs.append(f"{r['edid']} objective {o['index']}: text not written ({o['text']})")
            for s in r.get("stages") or []:
                for e in s.get("log") or []:
                    if e["text"].startswith(PLACEHOLDER):
                        errs.append(f"{r['edid']} stage {s['index']}: journal text not written ({e['text']})")
            for a in r.get("aliases") or []:
                if {"Essential", "Protected"} & set(a.get("flags") or []):
                    errs.append(f"{r['edid']} alias {a['name']}: Essential or Protected (nobody is unkillable)")
        for ref in r.get("refs") or []:
            mm = ref.get("mapMarker")
            if (ref.get("base") == su.MAP_MARKER or mm is not None) and {"Visible", "CanTravelTo"} & set((mm or {}).get("flags") or []):
                errs.append(f"{r.get('edid')} ref {ref.get('edid') or ref['formKey']}: map marker shown before it is "
                            "reached (old 0137: it appears only on discovery)")
    return errs


def check_yaml(root: Path) -> list[str]:
    """The same rule on the serialised plugin: no quest objective target, no map marker visible from the start."""
    errs = []
    for f in sorted(root.rglob("*.yaml")):
        t = f.read_text(encoding="utf-8")
        if "Quests" in f.parts and re.search(r"^\s+Targets:", t, re.M):
            errs.append(f"{f.relative_to(root)}: a quest objective carries target data")
        if re.search(r"MapMarker:(?:\n\s+.*)*?\n\s+-\s+(Visible|CanTravelTo)\b", t):
            errs.append(f"{f.relative_to(root)}: a map marker is visible before it is reached")
    return errs


def check_fragments(texts: dict[str, str]) -> list[str]:
    errs = []
    for name, t in texts.items():
        for bad in ("AddToMap", "SetObjectiveTarget", "ShowOnMap", "SetEssential", "SetProtected"):
            if bad in t:
                errs.append(f"{name}: calls {bad} (no markers; nobody is unkillable)")
        if re.search(r"^\s*(If|ElseIf|While)\b", t, re.M):
            errs.append(f"{name}: evaluates a condition in Papyrus (the stage graph is quest_runtime's)")
    return errs


def check_tiers(w: db.World, quest_id: str) -> list[str]:
    """Tier protection (40-factions §30b): every breaking action names an id the quest's touches list writes, and
    no quest of a higher tier (a lower number) touches or casts that id."""
    p = plan(w, quest_id)
    q, errs = p.q, []
    writes = {t["id"] for t in q.get("touches") or [] if t["access"] == "write"}
    acts = [a for st in p.stages for a in st.get("onEnter") or []]
    acts += [a for e in p.endings.values() for a in (e.get("world") or []) + (e.get("rewards") or [])]
    for a in acts:
        (term, args), = a.items()
        target = _as_list(args)[0]
        if term in BREAKING and target != q["id"] and target not in writes:
            errs.append(f"{quest_id}: {term} {target} is not in its touches as a write")
    for t in sorted(writes):
        higher = w.values('SELECT DISTINCT q.id FROM quest q JOIN quest_touch t ON t.quest_id = q.id WHERE t.id = ? '
                          'AND q.tier < ? UNION SELECT DISTINCT q.id FROM quest q JOIN quest_cast c ON c.quest_id = q.id '
                          'WHERE c.id = ? AND q.tier < ?', t, q["tier"], t, q["tier"])
        errs += [f"{quest_id}: writes {t}, which {h} (a higher tier) owns" for h in higher]
    return errs


def walk_graph(g: dict) -> stage_walk.Report:
    """stage_walk over the generated graph (the record view it was made from, rebuilt from the graph alone)."""
    rec = {"id": g["id"], "start": g["start"],
           "stages": [{"id": s["id"], **({"ending": s["ending"]} if s["ending"] else {}),
                       "objectives": [{"id": o["id"], "completeWhen": o["completeWhen"]} for o in s["objectives"]],
                       "failForward": s["failForward"], "successors": s["successors"]} for s in g["stages"]]}
    return stage_walk.walk_record(rec)


def fnv1a32(s: str) -> int:
    """quest_state::key: the QSTA family's key for a world id (FNV-1a, 32 bits)."""
    h = 2166136261
    for b in s.encode("utf-8"):
        h = ((h ^ b) * 16777619) & 0xFFFFFFFF
    return h


STATE_TERMS = ("flag", "setFlag", "counterAtLeast", "addCounter", "deedCountAtLeast")


def check_state_keys(w: db.World) -> list[str]:
    """No two flag, counter, faction or deed-class ids in use share a QSTA key."""
    ids = set(w.values("SELECT DISTINCT a.value FROM condition c JOIN condition_arg a ON a.condition_id = c.id "
                       f"WHERE c.term IN ({', '.join('?' * len(STATE_TERMS))}) AND typeof(a.value) = 'text'",
                       *STATE_TERMS))
    ids |= set(w.values("SELECT DISTINCT a.value FROM action x JOIN action_arg a ON a.list_id = x.list_id AND "
                        f"a.ord = x.ord WHERE x.term IN ({', '.join('?' * len(STATE_TERMS))}) "
                        "AND typeof(a.value) = 'text'", *STATE_TERMS))
    seen: dict[int, str] = {}
    errs = []
    for i in sorted(ids):
        k = fnv1a32(i)
        if k in seen:
            errs.append(f"QSTA key {k:08x}: both {seen[k]} and {i}")
        seen[k] = i
    return errs


# --- write and check -------------------------------------------------------------------------------------------
def render(w: db.World) -> dict[Path, str]:
    plans = [plan(w, qid) for qid in QUESTS]
    out = {PAPYRUS / f"{script(p.q)}.psc": papyrus(p) for p in plans}
    out[HEADER] = header([graph(p) for p in plans])
    return out


def full_check(w: db.World) -> list[str]:
    from tools.argonia_world.formids import Allocator
    errs = [f"{f.relative_to(REPO)}: stale (run `python3 -m tools.argonia_world.quest_gen`)"
            for f, t in render(w).items() if not f.exists() or f.read_text(encoding="utf-8") != t]
    alloc = Allocator(world=w, frozen=False)  # never saved: the check allocates nothing for good
    recs = [r for lay in layers(alloc, w) for r in lay.records]
    errs += check_records(recs)
    errs += check_fragments({f.name: t for f, t in render(w).items() if f.suffix == ".psc"})
    errs += check_state_keys(w)
    for qid in QUESTS:
        errs += check_tiers(w, qid)
        errs += [f"{qid}: {e}" for e in walk_graph(graph(plan(w, qid))).errors]
    return errs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="fail when an output is stale or the records check fails")
    args = ap.parse_args(argv)
    w = db.open()
    if args.check:
        errs = full_check(w)
        for e in errs:
            print(f"quest_gen: {e}", file=sys.stderr)
        if not errs:
            print(f"quest_gen: {len(QUESTS)} quest(s) current and clean")
        return 1 if errs else 0
    for f, t in render(w).items():
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(t, encoding="utf-8")
        print(f"quest_gen: wrote {f.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
