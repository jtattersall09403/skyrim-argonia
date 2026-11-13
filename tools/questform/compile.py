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
HARD = ("skill_at_least", "gold_at_least")    # a check the player can fail in front of the speaker: it has a fallback
FAILS = HARD + ("item_count_at_least",)       # with no skill or gold check, a thing held is the check that fails
VARIANTS = ("main", "fail")                   # the written infos a topic carries: its line and its fallback
REGARD = 4                                    # regard is Skyrim's relationship rank, -4 to 4


# The skills a record names, as Skyrim's actor value names (the form holds only these; blocks.md, "How record terms map
# to blocks"). Morrowind's skills go to the nearest Skyrim one; one with none is refused.
SKILL_OF = {
    "speech": "Speech", "speechcraft": "Speech", "mercantile": "Speech",
    "sneak": "Sneak", "pickpocket": "Pickpocket", "lockpicking": "Lockpicking", "security": "Lockpicking",
    "alchemy": "Alchemy", "archery": "Archery", "marksman": "Archery", "block": "Block",
    "onehanded": "OneHanded", "shortblade": "OneHanded", "longblade": "OneHanded", "axe": "OneHanded",
    "blunt": "OneHanded", "bluntweapon": "OneHanded", "twohanded": "TwoHanded", "spear": "TwoHanded",
    "heavyarmor": "HeavyArmor", "lightarmor": "LightArmor", "smithing": "Smithing", "armorer": "Smithing",
    "enchanting": "Enchanting", "enchant": "Enchanting", "alteration": "Alteration", "conjuration": "Conjuration",
    "destruction": "Destruction", "illusion": "Illusion", "restoration": "Restoration",
}


def skill_of(word: str) -> str | None:
    """A record's skill word as the form's Skyrim skill name, or None when Skyrim has no such skill."""
    k = word.lower()
    for pre in ("skill.", "stat."):
        k = k.removeprefix(pre)
    return SKILL_OF.get(k.replace("-", "").replace("_", "").replace(" ", ""))


def place(w: db.World, cell: str) -> dict:
    """A cell as the player sees it: its name and whether it is indoors, and for an interior its door's outside
    position (`entrance`). An exterior without a name of its own takes its settlement's (`settlement_name`); an
    interior's name carries that settlement name after it."""
    c = w.query("SELECT name, interior FROM bmv_cell WHERE id = ?", cell)
    if not c:
        return {}
    out = {"name": c[0]["name"], "interior": bool(c[0]["interior"])}
    town = settlement_name(w, cell)
    if town and not out["interior"] and not out["name"]:
        out["name"] = town
    elif town and out["interior"] and out["name"] and town not in out["name"]:
        out["name"] = f"{out['name']}, {town}"
    if out["interior"]:
        e = w.query("SELECT t.x, t.y FROM bmv_interior_exit x JOIN bmv_door d ON d.id = x.door "
                    "JOIN bmv_door t ON t.id = d.target JOIN bmv_cell c ON c.id = t.cell "
                    "WHERE x.interior = ? AND c.interior = 0", cell) or \
            w.query("SELECT t.x, t.y FROM bmv_door d JOIN bmv_door t ON t.id = d.target JOIN bmv_cell c ON c.id = t.cell "
                    "WHERE d.cell = ? AND c.interior = 0 ORDER BY d.id", cell)
        if e:
            out["entrance"] = {"x": e[0]["x"], "y": e[0]["y"]}
    return out


def settlement_name(w: db.World, cell: str) -> str | None:
    """The name of the settlement a cell belongs to: the designed place it lands as (place_bmv), else the name of
    BM&V's map marker there (the last, when it has several), else the settlement's census name."""
    s = w.query("SELECT s.id, s.name, s.marker_name FROM bmv_settlement_cell x JOIN bmv_settlement s "
                "ON s.id = x.settlement WHERE x.cell = ? ORDER BY x.role = 'neighbour'", cell)
    if not s:
        return None
    story = w.query("SELECT p.name FROM place_bmv b JOIN place p ON p.id = b.place WHERE b.cell = ? "
                    "OR b.settlement = ? ORDER BY b.cell = ? DESC", cell, s[0]["id"], cell)
    if story and story[0]["name"]:
        return story[0]["name"]
    if s[0]["marker_name"]:
        return s[0]["marker_name"].split(";")[-1].strip()
    return s[0]["name"]


class Refusal(Exception):
    pass


def _args(v):
    return v if isinstance(v, list) else [v]


def _one(c):
    (term, a), = c.items()
    return term, a


def _key(x) -> str:
    return json.dumps(x, sort_keys=True)


def written_lines(code: str) -> dict:
    """The written lines of a quest (`story/data/quest_lines/<code>.json`), each topic as {speaker, infos}: a topic
    written as one info (`prompt`, `lines`) is one info of variant `main`; an info's `variant` is `main` (said when
    the line's conditions hold) or `fail` (its fallback, said when its check fails)."""
    p = QUEST_LINES / f"{code.lower()}.json"
    if not p.exists():
        return {}
    out = {}
    for topic, body in json.loads(p.read_text(encoding="utf-8")).items():
        if topic.startswith("_") or not isinstance(body, dict):
            continue
        out[topic] = {"speaker": body.get("speaker"), "infos": body.get("infos", [body])}
    return out


class Compiler:
    def __init__(self, w: db.World, qid: str):
        self.w, self.qid = w, qid
        self.rec = export(w, qid)
        self.refused: list[tuple[str, str, str]] = []
        self.stage_ids = [s["id"] for s in self.rec.get("stages", [])]
        self.stage_of = {s["id"]: s for s in self.rec.get("stages", [])}
        self.hooks = {r["sets_flag"]: (r["thing_id"], r["hook"])
                      for r in w.query("SELECT * FROM thing_hook WHERE quest_id = ?", qid)}
        self.rows = {r["ref"]: dict(r) for r in w.query("SELECT * FROM quest_placement WHERE quest_id = ? ORDER BY ord",
                                                         qid)}
        self.things = {r["id"]: dict(r) for r in w.query("SELECT * FROM quest_thing WHERE quest_id = ? ORDER BY ord", qid)}
        self.movers: dict[tuple[str, str, int], list[tuple[int, list]]] = {}
        self.triggers: list[dict] = []
        self.must_live: dict[str, int] = {}
        self.must_live_at: dict[str, set[int]] = {}
        self.death_moves: set[str] = set()
        self.used_refs: dict[str, str] = {}
        self.kill_choice: set[str] = set()

    def refuse(self, term, where, hint):
        self.refused.append((term, where, hint))

    def use(self, ref, where):
        self.used_refs.setdefault(ref, where)
        return ref

    # -- items: one id for one thing ----------------------------------------------------------------------------
    def unique(self, ref) -> bool:
        """A thing of ours that is one of a kind (a new item on a template, or an item whose id is the thing's own):
        the form names it by its ref id. Any other placed item (gold, lockpicks) is stock, named by its base."""
        r = self.rows.get(ref)
        return r is not None and (r["base_kind"] == "template_item" or (r["base_kind"] == "item" and r["base"] == ref))

    def item(self, x, where) -> str:
        """The form's id for an item a record names: a unique thing by its ref id, a stock thing by its base, any
        other item as it is. Naming the base of a unique thing is refused (it would count every item of that base)."""
        r = self.rows.get(x)
        if r is not None and r["base_kind"] in ("item", "template_item"):
            return self.use(x, where) if self.unique(x) else r["base"]
        owner = [ref for ref, row in self.rows.items() if row["base"] == x and self.unique(ref) and ref != x]
        if owner:
            self.refuse("item id", where, f"{x} is the base of the quest thing {owner[0]}: name the thing")
        return x

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
            return [{"is": "item_count_at_least", "item": self.item(a[0], where),
                     "count": int(a[1]) if len(a) > 1 else 1}]
        if term == "goldAtLeast":
            return [{"is": "gold_at_least", "gold": int(a[0])}]
        if term == "skillAtLeast":
            sk = skill_of(str(a[0]))
            if sk is None:
                self.refuse("skillAtLeast", where, f"{a[0]} is no Skyrim skill and maps to none: name one of the "
                            "form's skills (Speech, Sneak, Lockpicking, Pickpocket, Alchemy, OneHanded, ...)")
                return []
            return [{"is": "skill_at_least", "skill": sk, "value": int(a[1])}]
        if term == "npcAlive":
            return [{"is": "alive", "ref": self.use(a[0], where)}]
        if term == "dispositionAtLeast":
            if not -REGARD < int(a[1]) <= REGARD:
                self.refuse("dispositionAtLeast", where, f"regard is Skyrim's relationship rank, -{REGARD} to "
                            f"{REGARD}: ask for 1 to {REGARD}")
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
            self.item(a[0], where)
            self._trigger("take", self.use(a[0], where), frm, to)
        elif term == "not" and _one(a[0])[0] == "npcAlive":
            npc = self.use(_args(_one(a[0])[1])[0], where)
            if self.stage_of.get(to, {}).get("ending") == "failed":
                self.must_live.setdefault(npc, to)
                self.must_live_at.setdefault(npc, set()).add(frm)
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
                if not 0 < abs(int(a[1])) <= REGARD:
                    self.refuse("changeDisposition", where, f"regard is Skyrim's relationship rank, -{REGARD} to "
                                f"{REGARD}: change it by 1 to {REGARD} (4 is as far as it goes)")
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
                out.append({"do": "give_item" if term == "giveItem" else "take_item", "item": self.item(a[0], where),
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
            if any(True for _ in self._started_by()):    # another quest's setStage of it: its start_quest result
                return {"by": "start_quest", "stage": first}
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
            # an objective is done when the quest leaves its stage, by a successor or a fail-forward; an ending is
            # never named (it closes every objective)
            done = sorted({x["to"] for x in (s.get("successors") or []) + (s.get("failForward") or [])
                           if self.stage_of.get(x["to"], {}).get("ending") not in ("complete", "failed")})
            for i, o in enumerate(s.get("objectives") or []):
                ow = f"{where} objective {o['id']}"
                self.scan(o.get("completeWhen") or {"all": []}, ow)
                target = o.get("target")
                if not target or target == "none":
                    self.refuse("objective target", ow, "every objective names the person, thing, door or marker "
                                "its marker points at")
                if not o.get("objectiveText"):
                    self.refuse("objective text", ow, "write the objective's words (objectiveText)")
                targets = [t.strip() for t in (target or "").split(",") if t.strip() and t.strip() != "none"]
                objectives.append({"number": n + i, "text": o.get("objectiveText") or o["id"], "shown_at": [n],
                                   "completed_at": done, "targets": [self.use(t, ow) for t in targets]})
        objectives = _merged(objectives)
        for npc in sorted(self.death_moves & set(self.must_live)):
            self.refuse("death both ways", f"ref {npc}", "a person's death either fails the quest (who must live) "
                        "or moves it on, at every stage alike")
        self._held(stages)
        lines = self.lines(q)
        triggers = [{"id": f"{t['kind']}.{t.get('ref') or t['quest']}.{t['prerequisite']}-{t['sets']}", **t}
                    for t in self._one_per_ref(start)]
        kind = q["group"] if q["group"] in ("main", "faction") else "minor"
        must_live = self.windows(stages, start, kind)
        self._unable_to_start(lines, must_live, start, stages)
        refs = self.refs()
        for t in triggers:
            if t["kind"] == "death" and t["ref"] in self.kill_choice:
                t["choice"] = True
        if self.refused:
            return None
        form = {"version": 1,
                "quest": {"id": q["id"], "editor_id": f"ARG_{q['code']}", "name": q["title"],
                          "kind": kind, "start": start},
                "stages": stages, "objectives": objectives, "refs": refs, "lines": lines, "triggers": triggers,
                "must_live": must_live}
        names, texts = self.item_names(form)
        if names:
            form["names"] = names
        if texts:
            form["texts"] = texts
        places = self.places(refs)
        if places:
            form["places"] = places
        if self.refused:
            return None
        return form

    # -- a thing already held: the take trigger's stage checks the count as it begins ----------------------------
    def _held(self, stages):
        """A take trigger moves the quest only when the thing is taken while it is open; a player who already holds it
        as its prerequisite stage begins is moved on by that stage's own result (set_stage if_held)."""
        by = {s["number"]: s for s in stages}
        for t in self.triggers:
            if t["kind"] == "take" and t["prerequisite"] in by:
                r = self.rows.get(t["ref"])
                item = t["ref"] if r is None or self.unique(t["ref"]) else r["base"]
                row = {"do": "set_stage", "stage": t["sets"], "if_held": item}
                if row not in by[t["prerequisite"]]["results"]:
                    by[t["prerequisite"]]["results"].append(row)

    # -- one trigger of a kind on a ref ------------------------------------------------------------------------
    def _one_per_ref(self, start) -> list[dict]:
        """A ref carries one trigger of a kind (a placed thing may also be taken towards a second stage: the builder
        puts that take on the thing itself). Two that set one stage are one trigger: the one with the lower
        prerequisite, when every way to the other's passes it (it is open whenever either is); otherwise refused, as
        any other pair is: the record must say it one way."""
        succ = {}
        for s in self.rec["stages"]:
            succ[s["id"]] = {x["to"] for x in (s.get("successors") or []) + (s.get("failForward") or [])}
        if start["stage"] not in succ:
            succ[start["stage"]] = {t["sets"] for t in self.triggers if t["prerequisite"] == start["stage"]}

        def passes(lo, hi) -> bool:       # every way from the start to `hi` passes `lo`
            if lo == start["stage"]:
                return True
            seen, todo = {start["stage"]}, [start["stage"]]
            while todo:
                n = todo.pop()
                for m in succ.get(n, ()):
                    if m != lo and m not in seen:
                        seen.add(m)
                        todo.append(m)
            return hi not in seen
        out = []
        for t in self.triggers:
            same = [x for x in out if x["kind"] == t["kind"] and x.get("ref") is not None and x.get("ref") == t.get("ref")
                    and (t["kind"] != "take" or x["sets"] == t["sets"])]
            if not same:
                out.append(t)
                continue
            x = same[0]

            lo, hi = sorted((x, t), key=lambda y: y["prerequisite"])
            if x["sets"] == t["sets"] and passes(lo["prerequisite"], hi["prerequisite"]):
                out[out.index(x)] = lo
            else:
                self.refuse("trigger", f"ref {t['ref']}", f"two {t['kind']} triggers (stage {x['prerequisite']} to "
                            f"{x['sets']}, stage {t['prerequisite']} to {t['sets']}): a ref carries one trigger of a "
                            "kind; let one take, use or death move the quest, and the stage it sets decide the rest")
                out.append(t)
        return out

    # -- who must live, and when -------------------------------------------------------------------------------
    def windows(self, stages, start, kind) -> list[dict]:
        """A who-must-live row holds over the stages whose fail-forwards name the person, never before the quest's
        first shown stage (a quest still hidden has not begun for the player). `from` and `to` are written only
        where they narrow the quest's own span."""
        shown = sorted(s["number"] for s in stages if s["shown"] and s["ending"] == "none")
        live = sorted(s["number"] for s in stages if s["ending"] == "none")
        first = shown[0] if shown else (live[0] if live else start["stage"])
        out = []
        for r, n in sorted(self.must_live.items()):
            at = sorted(self.must_live_at.get(r, set()))
            row = {"ref": r, "fail_stage": n, "main_message": kind != "minor"}
            lo, hi = max(at[0], first), at[-1]
            if lo > start["stage"]:
                row["from"] = lo
            if live and hi < live[-1]:
                row["to"] = hi
            out.append(row)
        return out

    def _unable_to_start(self, lines, must_live, start, stages):
        """A who-must-live person dead before the quest is shown leaves it unable to start, saying nothing: every line
        that moves the quest on from its hidden start stage is gated on that person being alive."""
        hidden = next((s for s in stages if s["number"] == start["stage"] and not s["shown"]), None)
        if hidden is None:
            return
        for m in must_live:
            if m.get("from", start["stage"]) <= start["stage"]:
                continue
            for ln in lines:
                if ln["first_stage"] <= start["stage"] <= ln["last_stage"] and \
                        any(r["do"] == "set_stage" for r in ln["results"]):
                    g = {"is": "alive", "ref": m["ref"]}
                    if g not in ln["conditions"]:
                        ln["conditions"].append(g)

    # -- lines -------------------------------------------------------------------------------------------------
    def _written(self, code):
        return written_lines(code)

    def lines(self, q) -> list[dict]:
        """One line per stage window of each topic: a line that moves a stage carries its successor's gates; a stage
        whose movers are all gated has no ungated copy, only the record's own fallback (its written `fail` info, else
        the topic's `fallback` gist), which a check of skill or gold must have. A topic's `when` gates all its lines."""
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
        self.people = {}
        for t in rows:
            self.people.setdefault(t["id"], set()).add(t["person"])
        replies = {r for v in written.values() for info in v["infos"] for r in info.get("replies", [])}
        order = sorted(set(self.stage_ids) | {0})
        out, ids_of = [], {}
        for t in rows:
            topic, npc = t["id"], self.use(t["person"], f"topic {t['id']}")
            where = f"topic {topic} ({npc})"
            when = self.gate(t["when"], where) if t.get("when") else []
            text, prompt, ok, answers = self._text(written, t)
            kind = "answer" if topic in replies else {"greeting": "greeting", "speaks-first": "topic"}.get(
                t.get("kind"), "topic")
            base = {"speaker": npc, "kind": kind, "prompt": None if kind == "greeting" else prompt, "text": text,
                    "written": ok, "answers": answers}
            made, fall = [], []
            st = sorted(t.get("stages") or [])
            plain = [s for s in st if (topic, npc, s) not in self.movers]
            for s in st:
                moves = self.movers.get((topic, npc, s), [])
                for to, gates in moves:
                    made.append({**base, "conditions": when + gates, "results": [{"do": "set_stage", "stage": to}],
                                 "first_stage": s, "last_stage": s})
                if moves and all(g for _, g in moves):
                    fall.append((s, s, [when + g for _, g in moves]))
            for a, b in _runs(sorted(plain), order):
                made.append({**base, "conditions": list(when), "results": [], "first_stage": a, "last_stage": b})
                if when:
                    fall.append((a, b, [when]))
            for a, b, gate_sets in fall:
                hard = any(_bare_hard(gs, gate_sets) for gs in gate_sets)
                fb = self._text(written, t, fail=True)
                if fb is None:
                    if hard:
                        self.refuse("fallback", where, "a check of skill or gold has a line for when it fails: write "
                                    "its `fail` info, or the topic's `fallback` gist")
                    continue
                # said when the line's check fails: every gate but its skill or gold check, or, with neither, but
                # the thing it asks the player to hold
                fails = HARD if any(g["is"] in HARD for gs in gate_sets for g in gs) else FAILS
                soft = [g for g in gate_sets[0] if g["is"] not in fails
                        and all(_key(g) in {_key(x) for x in gs} for gs in gate_sets)]
                if any({_key(g) for g in soft} == {_key(g) for g in gs} for gs in gate_sets):
                    self.refuse("unsaid line", f"{where} fallback at stage {a}", "the fallback has every gate of the "
                                "line before it, so it is never said: gate the line on a check the player can fail "
                                "(skill, gold, a thing held), or drop the fallback")
                    continue
                ftext, fprompt, fok, fanswers = fb
                made.append({**base, "text": ftext, "written": fok, "answers": fanswers, "prompt": base["prompt"],
                             "conditions": soft, "results": [], "first_stage": a, "last_stage": b})
            if t.get("kind") == "speaks-first" and made:     # a quest has one speaks-first line: the first
                made.append({**made[0], "kind": "speaks_first", "prompt": None})
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

    def _text(self, written, t, fail: bool = False):
        """(words, prompt, written, answers) of a topic's line, or of its fallback (None when the record has none)."""
        w = written.get(t["id"])
        if w and (w.get("speaker") == t["person"] or len(self.people.get(t["id"], ())) == 1):
            if not fail:
                for i in w["infos"]:
                    if i.get("variant", "main") not in VARIANTS:
                        self.refuse("variant", f"topic {t['id']}", f"the written variant `{i['variant']}` is never "
                                    "said: the form carries a topic's line and its fallback only; give these words "
                                    "a topic of their own with the condition that says when (spoken before, "
                                    "regard, a death)")

            infos = [i for i in w["infos"] if (i.get("variant", "main") == "fail") == fail]
            if infos:
                info = infos[0]
                return " ".join(info.get("lines") or []) or t["intent"], info.get("prompt") or t["label"], True, \
                    list(info.get("replies") or [])
        if fail:
            return (t["fallback"], t["label"], False, []) if t.get("fallback") else None
        rows = self.w.query("SELECT words FROM dialogue_line WHERE keys_topic = ? AND speaker = ? AND status = "
                            "'written' ORDER BY id", t["id"], t["person"])
        if rows:
            return rows[0]["words"], t["label"], True, []
        return t.get("intent") or t["label"], t["label"], False, []

    # -- refs: every row of the record's placements --------------------------------------------------------------
    def refs(self) -> list[dict]:
        for ref, where in sorted(self.used_refs.items()):
            if ref not in self.rows:
                self.refuse("placement", where, f"{ref}: add a placements row (an existing reference by form key, "
                            "or a base and an anchor)")
        out = []
        for ref in sorted(self.rows):
            r = self.rows[ref]
            where = f"placement {ref}"
            if r["form_key"]:
                placement = {"existing": r["form_key"]}
            else:
                placement = {"base": {"kind": r["base_kind"], "id": r["base"]}}
                if r["near"] or r["place"]:
                    placement["anchor"] = ({"near": r["near"]} if r["near"] else {"place": r["place"]}) | \
                        {"rule": r["rule"]}
                if r["container"]:
                    placement["container"] = r["container"]
                if r["carried_by"]:
                    placement["carried_by"] = r["carried_by"]
            for box in (r["container"], r["carried_by"], r["owner"] if r["owner"] in self._all_refs() else None):
                if box and box not in self.rows:
                    self.refuse("placement", where, f"{box}: add a placements row for it")
            o = {"id": ref, "kind": r["kind"], "placement": placement, "enabled": bool(r["enabled"])}
            if r["hostile"]:
                o["hostile"] = True
            if r["kill_choice"]:
                self.kill_choice.add(ref)
            if r["lock_level"]:
                o["lock"] = {"level": r["lock_level"]}
                if r["lock_key"]:
                    o["lock"]["key"] = self.item(r["lock_key"], where)
            if r["owner"]:
                o["owner"] = r["owner"]
            if r["count"]:
                o["count"] = r["count"]
            if r["level"]:
                o["level"] = r["level"]
            at = self._at(r)
            if at:
                o["at"] = at
            self._name(o, r)
            text = r["text"] or (self.things.get(ref) or {}).get("text")
            if text:
                o["text"] = text
            out.append(o)
        return out

    def _all_refs(self):
        return set(self.rows) | set(self.used_refs)

    # -- the names the player sees: a person's, a thing's, a door's and where it leads, a marker's place ------------
    def _name(self, o: dict, r) -> None:
        q = self.w.query
        key = r["form_key"] or r["base"]
        own = r.get("name") or (self.things.get(o["id"]) or {}).get("name") or self._thing_name(o["id"])
        got = [{"n": own}] if own else None
        if o["kind"] == "person" and not got:
            got = (q("SELECT name AS n FROM npc WHERE id = ?", o["id"])
                   or q("SELECT known_as AS n FROM talker WHERE id = ?", key)
                   or q("SELECT n.name AS n FROM bmv_placement p JOIN bmv_npc n ON n.id = p.npc WHERE p.id = ?", key)
                   or q("SELECT name AS n FROM bmv_npc WHERE id = ?", key))
        elif o["kind"] == "thing" and not got:
            got = (q("SELECT name AS n FROM item WHERE id = ?", key) or q("SELECT name AS n FROM bmv_book WHERE id = ?", key))
        elif o["kind"] == "door":
            got = got or q("SELECT base_name AS n FROM bmv_door WHERE id = ?", key)
            to = self._door_to(key, r)
            if to and to.get("name"):
                o["destination"] = to["name"]
        elif o["kind"] == "marker" and o.get("at") and not got:
            got = [{"n": self._place(o["at"]["cell"]).get("name")}]
        if got and got[0]["n"]:
            o["name"] = got[0]["n"]

    def _thing_name(self, thing_id) -> str | None:
        """A thing's name as another quest's record gives it (a thing two quests place, like a container MQ01 puts
        out for MQ03)."""
        got = self.w.query("SELECT name FROM quest_thing WHERE id = ? AND name IS NOT NULL", thing_id)
        return got[0]["name"] if got else None

    def _place(self, cell) -> dict:
        """A cell as the player knows it: the census's place, named by a placement's `place_name` where it gives one
        (a door's names where it leads)."""
        out = place(self.w, cell)
        own = next((r["place_name"] for r in self.rows.values() if r["place_name"] and r["kind"] != "door"
                    and self._cell(r) == cell), None)
        if own:
            out = {**out, "name": own}
        return out

    def _door_to(self, key, r=None) -> dict | None:
        """Where a door leads, as a place: {cell, name, interior, entrance}. A door into a worldspace's persistent cell
        (which has no grid) is named by the cell of the grid square it opens on. The door's own `place_name` names it."""
        if not key:
            return None
        t = self.w.query("SELECT t.cell AS c, t.x, t.y FROM bmv_door d JOIN bmv_door t ON t.id = d.target "
                         "WHERE d.id = ?", key)
        if not t:
            return None
        cell = t[0]["c"]
        out = self._place(cell)
        if out and not out["interior"] and not out.get("name"):
            ws = self.w.query("SELECT worldspace FROM bmv_cell WHERE id = ? AND grid_x IS NULL", cell)
            if ws and t[0]["x"] is not None:
                g = self.w.query("SELECT id FROM bmv_cell WHERE worldspace = ? AND grid_x = ? AND grid_y = ?",
                                 ws[0]["worldspace"], int(t[0]["x"] // 4096), int(t[0]["y"] // 4096))
                if g:
                    out = {**out, "name": self._place(g[0]["id"]).get("name")}
        if r is not None and r.get("place_name"):
            out = {**out, "name": r["place_name"]}
        return {"cell": cell, **out} if out else None

    def _cell(self, r):
        at = self._at(r)
        return at["cell"] if at else None

    def places(self, refs) -> dict:
        """Every cell the form's refs stand in or lead to, as the player knows it: {cell: {name, interior,
        entrance}}. A cell with no name the player could know is refused."""
        cells = {r["at"]["cell"] for r in refs if r.get("at")}
        doors = {}
        for r in refs:
            if r["kind"] == "door":
                to = self._door_to(r["placement"].get("existing"), self.rows[r["id"]])
                if to:
                    doors[to.pop("cell")] = to
        out = {}
        for c in sorted(cells | set(doors)):
            p = self._place(c) if c in cells else doors[c]
            if c in cells and c in doors and not p.get("name"):
                p = doors[c]
            if not p:
                continue
            if not p.get("name"):
                self.refuse("place name", f"cell {c}", "the census names no place for it: give a placement standing "
                            "there its placeName")
                continue
            out[c] = p
        return out

    def item_names(self, form: dict) -> tuple[dict, dict]:
        """The name (and a readable item's words) of every item id the form names that is not a ref: a result's, a
        condition's, a stock thing's base, a lock's key. A thing of any quest's record names it first, then the item
        table."""
        ids = {r["placement"]["base"]["id"] for r in form["refs"]
               if r["placement"].get("base", {}).get("kind") == "item"}
        ids |= {x["item"] for s in form["stages"] for x in s["results"] if "item" in x}
        ids |= {x["if_held"] for s in form["stages"] for x in s["results"] if "if_held" in x}
        for ln in form["lines"]:
            ids |= {x["item"] for x in ln["results"] + ln["conditions"] if "item" in x}
        ids |= {r["lock"]["key"] for r in form["refs"] if r.get("lock", {}).get("key")}
        ids -= {r["id"] for r in form["refs"]}
        names, texts = {}, {}
        for i in sorted(ids):
            th = self.w.query("SELECT name, text FROM quest_thing WHERE id = ? AND (name IS NOT NULL OR text IS NOT "
                              "NULL) ORDER BY quest_id = ? DESC", i, self.qid)
            got = self.w.query("SELECT name FROM item WHERE id = ?", i)
            n = (th[0]["name"] if th else None) or (got[0]["name"] if got else None)
            if n:
                names[i] = n
            if th and th[0]["text"]:
                texts[i] = th[0]["text"]
        return names, texts

    def _at(self, r):
        if r["cell"] is not None and r["x"] is not None:
            return {"cell": r["cell"], "interior": bool(r["interior"]), "x": r["x"], "y": r["y"], "z": r["z"]}
        if r["form_key"]:
            for sql in ("SELECT p.cell, c.interior, p.x, p.y, p.z FROM bmv_placement p JOIN bmv_cell c "
                        "ON c.id = p.cell WHERE p.id = ?",
                        "SELECT d.cell, c.interior, d.x, d.y, d.z FROM bmv_door d JOIN bmv_cell c "
                        "ON c.id = d.cell WHERE d.id = ?"):
                got = self.w.query(sql, r["form_key"])
                if got:
                    return {**dict(got[0]), "interior": bool(got[0]["interior"])}
        return None


def _merged(objectives) -> list[dict]:
    """One objective for the same words, targets and completion shown at several stages (a branch's twin stages):
    the engine closes each objective on every ending, so each one costs rows."""
    out = []
    for o in objectives:
        twin = next((x for x in out if (x["text"], x["targets"], x["completed_at"]) ==
                     (o["text"], o["targets"], o["completed_at"])), None)
        if twin is None:
            out.append(o)
        else:
            twin["shown_at"] = sorted(set(twin["shown_at"]) | set(o["shown_at"]))
    return out


def _bare_hard(gates, gate_sets) -> bool:

    """A line gated on skill or gold whose failure no other line of the stage catches: no other line's gates are all
    among its own without the skill or gold (the line that haggles when the persuasion fails)."""
    if not any(g["is"] in HARD for g in gates):
        return False
    soft = {_key(g) for g in gates if g["is"] not in HARD}
    return not any(gs is not gates and {_key(g) for g in gs} <= soft for gs in gate_sets)


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
