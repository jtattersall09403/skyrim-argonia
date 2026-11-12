"""The compiler from a quest record (story data) to its quest form (docs/design/quest-form.md, "Compiling").

Each record term maps to the form's vocabulary or is refused with the term, where it stands and a re-author hint.
A quest with any refusal gets no form; its refused terms are its row on the owed list.
"""
from __future__ import annotations

import json
from pathlib import Path

from tools.argonia_world import db
from tools.argonia_world.quest_record import export

QUEST_LINES = db.REPO / "story/data/quest_lines"

HINT_PLACE = "a stage moves when the player talks, takes, uses or kills; where the player stands moves nothing"
HINT_CLOCK = "the clock moves and gates nothing: drop the wait, or let a line or a happening move the stage"
HINT_SEEN = "being seen or unseen gates nothing: let the deed itself (a take, a use, a line) move the stage"
HINT_SCENE = "scenes are cut: tell it in a line, or let it have happened already where the player finds it"
CUT = {
    "inZone": HINT_PLACE, "inSettlement": HINT_PLACE, "inCell": HINT_PLACE, "inRegion": HINT_PLACE,
    "discovered": "finding a place moves nothing: give the place a thing to use or a person to speak to",
    "timeOfDay": HINT_CLOCK, "daysSince": HINT_CLOCK, "dateAfter": HINT_CLOCK, "dateBefore": HINT_CLOCK,
    "calendarIs": HINT_CLOCK, "seasonIs": HINT_CLOCK, "weatherIs": HINT_CLOCK, "tideState": HINT_CLOCK,
    "startTimer": HINT_CLOCK,
    "detectedBy": HINT_SEEN, "seenBy": HINT_SEEN, "witnessed": HINT_SEEN, "recordWitnessed": HINT_SEEN,
    "sceneEnded": HINT_SCENE, "startScene": HINT_SCENE,
    "npcAtMark": "people are not walked to a mark: place them standing where they are needed",
    "setSchedule": "no package keeps a timetable for a quest: place the person where they are needed",
    "knowsTopic": "what the player has heard gates nothing: gate on the stage at which they heard it",
    "placeCleared": "a cleared place moves nothing: name each person whose death matters (a death trigger each)",
    "applyLocalVariant": "a variant switches an unnamed set: name each reference switched (switch on or off)",
    "clearLocalVariant": "a variant switches an unnamed set: name each reference switched (switch on or off)",
    "setDoorAccess": "a door is only locked or unlocked (lock_door, unlock_door)",
    "setWeather": HINT_CLOCK, "setAmbience": HINT_SCENE,
}
HINT_OTHER = "not in the form's vocabulary: re-author it with the form's conditions and results"
DROPPED = {"grantTopic", "removeTopic"}       # a line's first and last stage open and close it


class Refusal(Exception):
    pass


def _args(v):
    return v if isinstance(v, list) else [v]


def _one(c):
    (term, a), = c.items()
    return term, a


class Compiler:
    def __init__(self, w: db.World, qid: str):
        self.w, self.qid = w, qid
        self.rec = export(w, qid)
        self.refused: list[tuple[str, str, str]] = []
        self.stage_ids = [s["id"] for s in self.rec.get("stages", [])]
        self.stage_of = {s["id"]: s for s in self.rec.get("stages", [])}
        self.hooks = {r["sets_flag"]: (r["thing_id"], r["hook"])
                      for r in w.query("SELECT * FROM thing_hook WHERE quest_id = ?", qid)}
        self.movers: dict[tuple[str, str, int], list[tuple[int, list]]] = {}
        self.triggers: list[dict] = []
        self.must_live: dict[str, int] = {}
        self.death_moves: set[str] = set()
        self.used_refs: dict[str, str] = {}
        self.kill_choice: set[str] = set()

    def refuse(self, term, where, hint):
        self.refused.append((term, where, hint))

    def use(self, ref, where):
        self.used_refs.setdefault(ref, where)
        return ref

    # -- conditions --------------------------------------------------------------------------------------------
    def gate(self, c, where) -> list[dict]:
        """A condition as the form's gates (all must hold), or a refusal."""
        term, a = _one(c)
        a = _args(a)
        if term == "all":
            return [g for kid in a for g in self.gate(kid, where)]
        if term == "not":
            kt, ka = _one(a[0])
            if kt == "npcAlive":
                return [{"is": "dead", "ref": self.use(_args(ka)[0], where)}]
            self.refuse("not", where, "a gate is never negated: use its opposite (alive or dead) or a stage")
            return []
        if term == "questStage":
            q, op, n = a
            n = int(n)
            if op == "=":
                return [{"is": "stage_is", "quest": q, "stage": n}]
            if op in ("≥", ">"):
                return [{"is": "stage_at_least", "quest": q, "stage": n + (op == ">")}]
            self.refuse(f"questStage {op}", where, "a stage gate is 'is', 'at least' or 'done'")
            return []
        if term == "stageEverReached":
            return [{"is": "stage_done", "quest": a[0], "stage": int(a[1])}]
        if term == "flag":
            return [{"is": "number_compare", "number": a[0], "op": "=", "value": 1 if a[1] in (True, 1, "true") else 0}]
        if term == "counterAtLeast":
            return [{"is": "number_compare", "number": a[0], "op": ">=", "value": int(a[1])}]
        if term in ("factionStandingAtLeast", "settlementStandingAtLeast"):
            return [{"is": "number_compare", "number": f"standing.{a[0]}", "op": ">=", "value": int(a[1])}]
        if term == "factionRankAtLeast":
            return [{"is": "rank_at_least", "faction": a[0], "rank": int(a[1])}]
        if term == "hasItem":
            return [{"is": "item_count_at_least", "item": a[0], "count": int(a[1]) if len(a) > 1 else 1}]
        if term == "goldAtLeast":
            return [{"is": "gold_at_least", "gold": int(a[0])}]
        if term == "skillAtLeast":
            return [{"is": "skill_at_least", "skill": a[0], "value": int(a[1])}]
        if term == "npcAlive":
            return [{"is": "alive", "ref": self.use(a[0], where)}]
        if term == "dispositionAtLeast":
            return [{"is": "regard_at_least", "ref": self.use(a[0], where), "value": int(a[1])}]
        if term in ("raceIs", "sexIs"):
            return [{"is": "race_is" if term == "raceIs" else "sex_is", "value": a[0]}]
        self.refuse(term, where, CUT.get(term, "an 'any' is not a gate: split it into one line per case"
                                         if term == "any" else HINT_OTHER))
        return []

    def mover(self, c, frm: int, to: int, where: str, fail: bool = False):
        """A successor's or fail-forward's condition: what moves stage `frm` to `to`."""
        term, a = _one(c)
        a = _args(a)
        if term == "any":
            for kid in a:
                self.mover(kid, frm, to, where, fail)
        elif term == "all":
            lines = [k for k in a if _one(k)[0] == "topicHeardFrom"]
            if len(lines) != 1:
                self.refuse("all", where, "a trigger carries no condition: gate the stage before it, or make it a line")
                return
            gates = [g for k in a if k is not lines[0] for g in self.gate(k, where)]
            topic, npc = _args(_one(lines[0])[1])
            self.movers.setdefault((topic, self.use(npc, where), frm), []).append((to, gates))
        elif term == "topicHeardFrom":
            topic, npc = a
            self.movers.setdefault((topic, self.use(npc, where), frm), []).append((to, []))
        elif term == "hasItem":
            if len(a) > 1 and int(a[1]) > 1:
                self.refuse("hasItem count", where, "taking one named thing moves a stage; a count is a gate")
                return
            self._trigger("take", self.use(a[0], where), frm, to)
        elif term == "not" and _one(a[0])[0] == "npcAlive":
            npc = self.use(_args(_one(a[0])[1])[0], where)
            if self.stage_of.get(to, {}).get("ending") == "failed":
                self.must_live.setdefault(npc, to)
            else:
                self.death_moves.add(npc)
                self._trigger("death", npc, frm, to)
        elif term in ("questStage", "stageEverReached"):
            q, n = (a[0], a[2]) if term == "questStage" else (a[0], a[1])
            if term == "questStage" and a[1] not in ("=", "≥"):
                self.refuse(f"questStage {a[1]}", where, "another quest's stage moves this one when it is set")
                return
            self.triggers.append({"kind": "quest_stage", "quest": q, "quest_stage": int(n),
                                  "prerequisite": frm, "sets": to})
        elif term == "flag" and a[0] in self.hooks and a[1] in (True, 1, "true"):
            thing, _hook = self.hooks[a[0]]
            self._trigger("use", self.use(thing, where), frm, to)
        elif term == "objectiveComplete" and a[0] == self.qid:
            obj = next((o for s in self.rec["stages"] for o in s.get("objectives") or [] if o["id"] == a[1]), None)
            if obj is None:
                self.refuse("objectiveComplete", where, f"no objective {a[1]} in the quest")
            else:
                self.mover(obj["completeWhen"], frm, to, where, fail)
        elif term == "flag":
            self.refuse("flag as a mover", where, "set the stage where the flag is set, by the same line or happening")
        elif term in CUT:
            self.refuse(term, where, CUT[term])
        else:
            self.refuse(f"{term} as a mover", where, "a gate moves nothing: a line, a take, a use, a death or "
                        "another quest's stage moves a stage")

    def _trigger(self, kind, ref, frm, to):
        self.triggers.append({"kind": kind, "ref": ref, "prerequisite": frm, "sets": to})

    def scan(self, c, where):
        """Refuse any term of a condition the form never carries (an objective's own completion test)."""
        term, a = _one(c)
        if term in ("all", "any"):
            for kid in _args(a):
                self.scan(kid, where)
        elif term == "not":
            self.scan(_args(a)[0], where)
        elif term in CUT:
            self.refuse(term, where, CUT[term])

    # -- actions -----------------------------------------------------------------------------------------------
    def results(self, acts, where) -> list[dict]:
        out = []
        for act in acts or []:
            term, a = _one(act)
            a = _args(a)
            if term in DROPPED:
                continue
            if term == "setFlag":
                out.append({"do": "set_number", "number": a[0], "value": 1 if a[1] in (True, 1, "true") else 0})
            elif term == "addCounter":
                out.append({"do": "add_number", "number": a[0], "value": int(a[1])})
            elif term in ("changeStanding", "changeSettlementStanding"):
                out.append({"do": "add_number", "number": f"standing.{a[0]}", "value": int(a[1])})
            elif term == "changeDisposition":
                out.append({"do": "change_regard", "ref": self.use(a[0], where), "by": int(a[1])})
            elif term in ("enableRef", "disableRef"):
                out.append({"do": "switch_on" if term == "enableRef" else "switch_off", "ref": self.use(a[0], where)})
            elif term == "moveRef":
                self.refuse("moveRef", where, "nobody is moved for a quest, the player included: place the person "
                            "where they are needed, or switch one placement off and another on away from the player")
            elif term == "setDoorAccess" and a[1] in ("locked", "unlocked"):
                out.append({"do": "lock_door" if a[1] == "locked" else "unlock_door", "ref": self.use(a[0], where)})
            elif term in ("giveGold", "takeGold"):
                out.append({"do": "give_gold" if term == "giveGold" else "take_gold", "amount": int(a[0])})
            elif term in ("giveItem", "takeItem"):
                out.append({"do": "give_item" if term == "giveItem" else "take_item", "item": a[0],
                            "count": int(a[1]) if len(a) > 1 else 1})
            elif term == "setFactionRank":
                out.append({"do": "set_rank", "faction": a[0], "rank": int(a[1])})
            elif term == "setStage" and a[0] == self.qid:
                out.append({"do": "set_stage", "stage": int(a[1])})
            elif term == "setStage":
                out.append({"do": "start_quest", "quest": a[0], "stage": int(a[1])})
            else:
                self.refuse(term, where, CUT.get(term, HINT_OTHER))
        return out

    # -- the whole quest ---------------------------------------------------------------------------------------
    def start(self):
        q = self.rec
        first = q.get("start") or (self.stage_ids[0] if self.stage_ids else 0)
        sw = q.get("startWhen")
        if sw is None:
            for qid, sid in self._started_by():
                return {"by": "quest_stage", "quest": qid, "quest_stage": sid, "stage": first}
            if q.get("start") is not None:      # a first stage and nothing that starts it: running from a new game
                return {"by": "game", "stage": first}
            self.refuse("start", "the quest", "the record does not say how the quest starts: a startWhen, or "
                        "another quest's setStage of it")
            return {"by": "game", "stage": first}
        term, a = _one(sw)
        a = _args(a)
        if term in ("questStage", "stageEverReached"):
            n = a[2] if term == "questStage" else a[1]
            return {"by": "quest_stage", "quest": a[0], "quest_stage": int(n), "stage": first}
        if term in ("topicHeardFrom", "hasItem", "any", "all"):
            self.mover(sw, 0, first, "startWhen")
            return {"by": "game", "stage": 0}
        self.refuse(term, "startWhen", CUT.get(term, HINT_OTHER))
        return {"by": "game", "stage": first}

    def _started_by(self):
        rows = self.w.query("SELECT a.list_id FROM action a JOIN action_arg x ON x.list_id = a.list_id AND x.ord = a.ord "
                            "AND x.arg_ord = 0 WHERE a.term = 'setStage' AND x.value = ?", self.qid)
        for r in rows:
            for s in self.w.query("SELECT quest_id, id FROM quest_stage WHERE on_enter = ?", r["list_id"]):
                if s["quest_id"] != self.qid:
                    yield s["quest_id"], s["id"]

    def compile(self) -> dict | None:
        q = self.rec
        if not self.stage_ids:
            self.refuse("stages", "the quest", "the record has no stages")
            return None
        start = self.start()
        endings = {e["id"]: e for e in q.get("endings") or []}
        stages, objectives = [], []
        if start["by"] == "game" and start["stage"] == 0 and 0 not in self.stage_of:
            stages.append({"number": 0, "shown": False, "journal": None, "ending": "none", "results": []})
        for s in q["stages"]:
            n, where = s["id"], f"stage {s['id']}"
            res = self.results(s.get("onEnter"), where)
            if s.get("endingId") in endings:
                e = endings[s["endingId"]]
                res += self.results(e.get("world"), f"{where} ending {e['id']}")
                res += self.results(e.get("rewards"), f"{where} ending {e['id']}")
            hidden = bool(s.get("hidden"))
            stages.append({"number": n, "shown": not hidden, "journal": s.get("journalText"),
                           "ending": {"complete": "completed", "failed": "failed"}.get(s.get("ending"), "none"),
                           "results": res})
            for i, succ in enumerate(s.get("successors") or []):
                self.mover(succ["when"], n, succ["to"], f"{where} successor to {succ['to']}")
            for ff in s.get("failForward") or []:
                self.mover(ff["when"], n, ff["to"], f"{where} fail-forward to {ff['to']}", fail=True)
            done = sorted({x["to"] for x in s.get("successors") or []})
            for i, o in enumerate(s.get("objectives") or []):
                ow = f"{where} objective {o['id']}"
                self.scan(o.get("completeWhen") or {"all": []}, ow)
                target = o.get("target")
                if not target or target == "none":
                    self.refuse("objective target", ow, "every objective names the person, thing, door or marker "
                                "its marker points at")
                if not o.get("objectiveText"):
                    self.refuse("objective text", ow, "write the objective's words (objectiveText)")
                # several targets are one comma-separated `target` (the record's column holds one string)
                targets = [t.strip() for t in target.split(",") if t.strip()] if target and target != "none" else []
                objectives.append({"number": n + i, "text": o.get("objectiveText") or o["id"], "shown_at": [n],
                                   "completed_at": done, "targets": [self.use(t, ow) for t in targets]})
        for npc in sorted(self.death_moves & set(self.must_live)):
            self.refuse("death both ways", f"ref {npc}", "a person's death either fails the quest (who must live) "
                        "or moves it on, at every stage alike")
        lines = self.lines(q)
        triggers = [{"id": f"{t['kind']}.{t.get('ref') or t['quest']}.{t['prerequisite']}-{t['sets']}", **t}
                    for t in self.triggers]
        kind = q["group"] if q["group"] in ("main", "faction") else "minor"
        must_live = [{"ref": r, "fail_stage": n, "main_message": kind != "minor"}
                     for r, n in sorted(self.must_live.items())]
        refs = self.refs()
        for t in triggers:
            if t["kind"] == "death" and t["ref"] in self.kill_choice:
                t["choice"] = True
        if self.refused:
            return None
        return {"version": 1,
                "quest": {"id": q["id"], "editor_id": f"ARG_{q['code']}", "name": q["title"],
                          "kind": kind, "start": start},
                "stages": stages, "objectives": objectives, "refs": refs, "lines": lines, "triggers": triggers,
                "must_live": must_live}

    # -- lines -------------------------------------------------------------------------------------------------
    def _written(self, code):
        p = QUEST_LINES / f"{code.lower()}.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

    def lines(self, q) -> list[dict]:
        written = self._written(q["code"])
        rows = [dict(t) for t in q.get("topics") or []]
        have = {(t["id"], t["person"]) for t in rows}
        for (topic, npc, frm) in self.movers:
            if (topic, npc) not in have:
                lab = self.w.query("SELECT label FROM topic WHERE id = ?", topic)
                rows.append({"id": topic, "person": npc, "stages": [frm],
                             "label": lab[0]["label"] if lab else topic, "intent": lab[0]["label"] if lab else topic})
                have.add((topic, npc))
            else:
                row = next(t for t in rows if (t["id"], t["person"]) == (topic, npc))
                if frm not in (row.get("stages") or []):
                    row["stages"] = sorted(set(row.get("stages") or []) | {frm})
        replies = {r for v in written.values() for info in v.get("infos", []) for r in info.get("replies", [])}
        order = sorted(set(self.stage_ids) | {0})
        out, ids_of = [], {}
        for t in rows:
            topic, npc = t["id"], self.use(t["person"], f"topic {t['id']}")
            text, prompt, ok, answers = self._text(written, t)
            kind = "answer" if topic in replies else {"greeting": "greeting", "speaks-first": "topic"}.get(
                t.get("kind"), "topic")
            base = {"speaker": npc, "kind": kind, "prompt": None if kind == "greeting" else prompt, "text": text,
                    "written": ok, "answers": answers}
            made = []
            st = sorted(t.get("stages") or [])
            plain = [s for s in st if not any(k[0] == topic and k[1] == npc and k[2] == s for k in self.movers)]
            for s in st:
                for to, gates in self.movers.get((topic, npc, s), []):
                    made.append({**base, "conditions": gates, "results": [{"do": "set_stage", "stage": to}],
                                 "first_stage": s, "last_stage": s})
                    if gates and not any(not g for _, g in self.movers[(topic, npc, s)]) and s not in plain:
                        plain.append(s)
            for a, b in _runs(sorted(plain), order):
                made.append({**base, "conditions": [], "results": [], "first_stage": a, "last_stage": b})
            if t.get("kind") == "speaks-first":
                made += [{**m, "kind": "speaks_first", "prompt": None} for m in list(made)]
            for i, m in enumerate(made):
                m["id"] = f"{topic}@{npc}#{m['first_stage']}-{m['last_stage']}" + (f".{i}" if len(made) > 1 else "")
                ids_of.setdefault(topic, []).append(m)
            out += made
        for m in out:      # an answer names the answer lines of the same speaker open at an overlapping stage
            m["answers"] = [a["id"] for t in m["answers"] for a in ids_of.get(t, [])
                            if a["speaker"] == m["speaker"] and a["first_stage"] <= m["last_stage"]
                            and m["first_stage"] <= a["last_stage"]]
        return [{k: m[k] for k in ("id", "speaker", "kind", "prompt", "text", "written", "conditions", "results",
                                   "first_stage", "last_stage", "answers")} for m in out]

    def _text(self, written, t):
        w = written.get(t["id"])
        if w and w.get("speaker") == t["person"] and w.get("infos"):
            info = w["infos"][0]
            return " ".join(info.get("lines") or []) or t["intent"], info.get("prompt") or t["label"], True, \
                list(info.get("replies") or [])
        rows = self.w.query("SELECT words FROM dialogue_line WHERE keys_topic = ? AND speaker = ? AND status = "
                            "'written' ORDER BY id", t["id"], t["person"])
        if rows:
            return rows[0]["words"], t["label"], True, []
        return t.get("intent") or t["label"], t["label"], False, []

    # -- refs --------------------------------------------------------------------------------------------------
    def refs(self) -> list[dict]:
        rows = {r["ref"]: r for r in self.w.query("SELECT * FROM quest_placement WHERE quest_id = ? ORDER BY ord",
                                                  self.qid)}
        out = []
        for ref in sorted(self.used_refs):
            r = rows.get(ref)
            if r is None:
                self.refuse("placement", self.used_refs[ref], f"{ref}: add a placements row (an existing reference "
                            "by form key, or a base and an anchor)")
                continue
            if r["form_key"]:
                placement = {"existing": r["form_key"]}
            else:
                placement = {"base": {"kind": r["base_kind"], "id": r["base"]}}
                if r["near"] or r["place"]:
                    placement["anchor"] = ({"near": r["near"]} if r["near"] else {"place": r["place"]}) | \
                        {"rule": r["rule"]}
                if r["container"]:
                    placement["container"] = r["container"]
            o = {"id": ref, "kind": r["kind"], "placement": placement, "enabled": bool(r["enabled"])}
            if r["hostile"]:
                o["hostile"] = True
            if r["kill_choice"]:
                self.kill_choice.add(ref)
            at = self._at(r)
            if at:
                o["at"] = at
            out.append(o)
        return out

    def _at(self, r):
        if r["cell"] is not None and r["x"] is not None:
            return {"cell": r["cell"], "interior": bool(r["interior"]), "x": r["x"], "y": r["y"], "z": r["z"]}
        if r["form_key"]:
            got = self.w.query("SELECT p.cell, c.interior, p.x, p.y, p.z FROM bmv_placement p JOIN bmv_cell c "
                               "ON c.id = p.cell WHERE p.id = ?", r["form_key"])
            if got:
                return {**dict(got[0]), "interior": bool(got[0]["interior"])}
        return None


def _runs(stages, order):
    """Stages grouped into runs that are consecutive in the quest's stage order, as (first, last)."""
    out = []
    for s in stages:
        if out and s in order and out[-1][1] in order and order.index(s) == order.index(out[-1][1]) + 1:
            out[-1] = (out[-1][0], s)
        else:
            out.append((s, s))
    return out


def compile_quest(w: db.World, qid: str) -> tuple[dict | None, list[tuple[str, str, str]]]:
    c = Compiler(w, qid)
    form = c.compile()
    return form, c.refused


def staged_quests(w: db.World) -> list[str]:
    return [r["quest_id"] for r in w.query("SELECT DISTINCT quest_id FROM quest_stage ORDER BY quest_id")]


def write(form: dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"{form['quest']['id']}.json"
    p.write_text(json.dumps(form, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return p
