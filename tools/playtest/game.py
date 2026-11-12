"""The game on paper (docs/design/paper-playtest.md): a deterministic state machine over quest forms and the talk of
the people standing in the places involved. Each command returns exactly what the player would see, as plain text.

Inputs: the forms (tools/questform/schema.json) and a world snapshot (tools/playtest/world.py): names the player
sees, places, the talkers with their topics. The state is plain JSON, so a session file holds it between commands.
A condition or result word the game does not know, a quest a form names that this run did not load, a ref or item
with no name: each stops the run with a HarnessError naming it, never a guess.
"""
from __future__ import annotations

import copy
import math

from tools.playtest.vocab import CONDITIONS, RESULTS, HarnessError, race_key  # noqa: F401 (the vocabularies)
from tools.questform import validate

# Skyrim units: about 70 to a metre. "Near" is close enough to notice and to talk (outdoors); speaks-first fires
# when the player arrives this near its speaker.
UNITS_PER_M = 70.0
NEAR = 1500.0
SPEAKS_FIRST_NEAR = 1500.0
MAX_COMMANDS = 60
# The main quest's message on a must-live death (docs/research/morrowind-level-scripting.md section 5, the
# recommended text; the builder's message box carries the same words).
MAIN_MESSAGE = ("With this death the root of what was to come is cut: the main story can no longer be finished. "
                "Load an earlier save to let it grow again, or go on in the marsh as it now is.")
SKILLS = ("Alchemy", "Alteration", "Archery", "Block", "Conjuration", "Destruction", "Enchanting", "Heavy Armor",
          "Illusion", "Light Armor", "Lockpicking", "One-handed", "Pickpocket", "Restoration", "Smithing", "Sneak",
          "Speech", "Two-handed")
# A new character: every skill 15, the race's skills raised (+10 the first, +5 the rest), as Skyrim's races.
RACE_SKILLS = {
    "argonian": ("Lockpicking", "Alteration", "Light Armor", "Pickpocket", "Restoration", "Sneak"),
    "khajiit": ("Sneak", "Alchemy", "Archery", "Lockpicking", "One-handed", "Pickpocket"),
    "dunmer": ("Destruction", "Alchemy", "Alteration", "Illusion", "Light Armor", "Sneak"),
    "bosmer": ("Archery", "Alchemy", "Light Armor", "Lockpicking", "Pickpocket", "Sneak"),
    "imperial": ("Restoration", "Block", "Destruction", "Enchanting", "Heavy Armor", "One-handed"),
    "breton": ("Conjuration", "Alchemy", "Alteration", "Illusion", "Restoration", "Speech"),
    "altmer": ("Illusion", "Alteration", "Conjuration", "Destruction", "Enchanting", "Restoration"),
    "nord": ("Two-handed", "Block", "Light Armor", "One-handed", "Smithing", "Speech"),
    "redguard": ("One-handed", "Alteration", "Archery", "Block", "Destruction", "Smithing"),
    "orc": ("Heavy Armor", "Block", "Enchanting", "One-handed", "Smithing", "Two-handed"),
}


def new_sheet(race="Argonian", sex="male", **skills) -> dict:
    first, *rest = RACE_SKILLS.get(race_key(race), ("",))
    sk = {s: 15 + (10 if s == first else 5 if s in rest else 0) for s in SKILLS}
    for k, v in skills.items():
        name = next((s for s in SKILLS if s.lower().replace("-", "").replace(" ", "") ==
                     k.lower().replace("-", "").replace(" ", "").replace("_", "")), None)
        if name is None:
            raise HarnessError(f"sheet: '{k}' is not a skill ({', '.join(SKILLS)})")
        sk[name] = int(v)
    return {"race": race, "sex": sex, "skills": sk}


def _dist(a, b) -> float | None:
    """Units between two positions, or None when one is indoors in another cell (no straight line the player sees)."""
    if a["interior"] or b["interior"]:
        return 0.0 if a["cell"] == b["cell"] else None
    return math.dist((a["x"], a["y"]), (b["x"], b["y"]))


def _compass(a, b) -> str:
    ang = math.degrees(math.atan2(b["x"] - a["x"], b["y"] - a["y"])) % 360
    return ("north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west")[
        int((ang + 22.5) // 45) % 8]


def _how_far(units: float) -> str:
    m = units / UNITS_PER_M
    if m < 10:
        return "a few steps"
    if m < 200:
        return f"a short walk (about {int(round(m, -1))} m)"
    if m < 1000:
        return f"a walk of about {int(round(m, -1))} m"
    return f"a long way (about {m / 1000:.1f} km)"


class Game:
    """One paper game: forms + world snapshot + state. Every public command returns the player's screen text."""

    def __init__(self, forms: list[dict], world: dict, state: dict | None = None, sheet: dict | None = None):
        self.forms = {f["quest"]["id"]: f for f in forms}
        self.by_editor = {f["quest"]["editor_id"]: f["quest"]["id"] for f in forms}
        self.world = world
        for f in forms:
            errs = validate.errors(f)
            if errs:
                raise HarnessError(f"form {f.get('quest', {}).get('id')}: not a quest form: {'; '.join(errs[:5])}")
            self._scan(f)
        self.ents = self._entities()
        self._check_names()
        self.s = state if state is not None else self._fresh(sheet or new_sheet())

    # -- loading -------------------------------------------------------------------------------------------------
    def _scan(self, f):
        qid = f["quest"]["id"]
        rs = [r for s in f["stages"] for r in s["results"]] + [r for ln in f["lines"] for r in ln["results"]]
        for r in rs:
            if r["do"] not in RESULTS:
                raise HarnessError(f"{qid}: result word '{r['do']}' is not one the paper game knows")
            if r["do"] == "start_quest" and r["quest"] not in self.forms:
                raise HarnessError(f"{qid}: start_quest names {r['quest']}, a quest this run did not load")
        for ln in f["lines"]:
            for c in ln["conditions"]:
                if c["is"] not in CONDITIONS:
                    raise HarnessError(f"{qid}: condition word '{c['is']}' is not one the paper game knows")
                if "quest" in c and c["quest"] not in self.forms:
                    raise HarnessError(f"{qid}: line {ln['id']} names quest {c['quest']}, which this run did not "
                                       "load: add its form")
        st = f["quest"]["start"]
        others = [t["quest"] for t in f["triggers"] if t["kind"] == "quest_stage"]
        if st["by"] == "quest_stage":
            others.append(st["quest"])
        for q in others:
            if q not in self.forms:
                raise HarnessError(f"{qid}: waits on quest {q}, which this run did not load: add its form")

    def _entities(self) -> dict:
        """Everyone and everything the player can meet: the forms' refs and the talkers, one entry each (a talker
        who is also a quest's existing ref is one entity)."""
        ents = {}
        talkers = {t["id"]: t for t in self.world.get("talkers", [])}
        for f in self.forms.values():
            for r in f["refs"]:
                key = r["placement"].get("existing")
                e = ents.setdefault(r["id"], {"id": r["id"], "kind": r["kind"], "enabled": r["enabled"],
                                              "hostile": bool(r.get("hostile")), "at": r.get("at"),
                                              "container": r["placement"].get("container"),
                                              "item": (r["placement"].get("base") or {}).get("id")
                                              if (r["placement"].get("base") or {}).get("kind") == "item" else None,
                                              "talker": None, "quest": f["quest"]["id"]})
                if key in talkers:
                    e["talker"] = talkers.pop(key)
        for t in talkers.values():
            ents[t["id"]] = {"id": t["id"], "kind": "person", "enabled": True, "hostile": False,
                             "at": {"cell": t["cell"], "interior": t["interior"], "x": t["x"], "y": t["y"], "z": 0.0},
                             "container": None, "item": None, "talker": t, "quest": None}
        return ents

    def _check_names(self):
        names = self.world.get("names", {})
        missing = {e["id"] for e in self.ents.values() if not (e["talker"] and e["talker"].get("name"))
                   and e["kind"] != "marker" and not names.get(e["id"])}
        for f in self.forms.values():
            for r in [r for s in f["stages"] for r in s["results"]] + [r for ln in f["lines"] for r in ln["results"]]:
                if r["do"] in ("give_item", "take_item") and not names.get(r["item"]):
                    missing.add(r["item"])
        if missing:
            raise HarnessError("no name the player would see for: " + ", ".join(sorted(missing)) +
                               " (give each a name in the run's names file)")

    def _fresh(self, sheet) -> dict:
        return {"quests": {}, "order": [], "items": {}, "gold": 0, "numbers": {}, "factions": {}, "regard": {},
                "dead": [], "switched": {}, "locked": {}, "taken": [], "pos": None, "visited": [], "spoken": [],
                "fired": [], "talking": None, "question": None, "message_shown": False, "hostile": [],
                "sheet": sheet, "commands": 0, "ended": False}

    # -- the opening -------------------------------------------------------------------------------------------
    def begin(self, start: str | None = None, at: str | None = None) -> str:
        """A new game: every quest that runs from a new game starts (or only `start`, at its start stage); the player
        stands at `at` (a ref id), else at the first target of the first objective shown."""
        out = []
        qids = [start] if start else [q for q, f in self.forms.items() if f["quest"]["start"]["by"] == "game"]
        if start and start not in self.forms:
            raise HarnessError(f"--start {start}: no such quest in this run")
        for q in qids:
            out += self._set_stage(q, self.forms[q]["quest"]["start"]["stage"], None)
        if at is None:
            tg = [t for q in self.s["order"] for o in self._active(q) for t in o["targets"]]
            at = tg[0] if tg else next(iter(self.ents), None)
        if at not in self.ents or self._pos(at) is None:
            raise HarnessError(f"start position: {at} is not a placed ref of this run")
        self.s["pos"] = dict(self._pos(at))
        self._visit()
        sh = self.s["sheet"]
        head = [f"A new game. You are a {sh['sex']} {race_key(sh['race']).capitalize()}."]
        return "\n".join(head + out + ["", self.look()] + self._speaks_first())

    # -- names and places ------------------------------------------------------------------------------------------
    def name(self, eid: str) -> str:
        e = self.ents.get(eid)
        if e and e["talker"] and e["talker"].get("name") and not self.world.get("names", {}).get(eid):
            return e["talker"]["name"]
        n = self.world.get("names", {}).get(eid)
        if n is None:
            raise HarnessError(f"no name the player would see for {eid}")
        return n

    def place_name(self, pos) -> str:
        p = self.world.get("places", {}).get(pos["cell"], {})
        return p.get("name") or self.world.get("names", {}).get(pos["cell"]) or \
            ("somewhere indoors" if pos["interior"] else "outdoors (no place name shows)")

    def _pos(self, eid):
        e = self.ents.get(eid)
        if e is None:
            return None
        if hasattr(self, "s") and eid in self.s["taken"]:
            return self.s["pos"]
        if e["container"]:
            return self._pos(e["container"])
        return e["at"]

    def _on(self, eid) -> bool:
        return self.s["switched"].get(eid, self.ents[eid]["enabled"])

    def _alive(self, eid) -> bool:
        return eid not in self.s["dead"]

    def _near(self, eid) -> bool:
        p = self._pos(eid)
        if p is None or eid in self.s["taken"]:
            return False
        d = _dist(self.s["pos"], p)
        return d is not None and (p["interior"] or d <= NEAR)

    def _visit(self):
        c = self.s["pos"]["cell"]
        if c not in self.s["visited"]:
            self.s["visited"].append(c)

    # -- quest state ---------------------------------------------------------------------------------------------
    def stage(self, q):
        st = self.s["quests"].get(q)
        return None if st is None else st["stage"]

    def _active(self, q):
        st = self.s["quests"].get(q)
        if st is None or st["ended"]:
            return []
        return [o for o in self.forms[q]["objectives"] if o["number"] in st["shown"] and o["number"] not in st["done_obj"]]

    def _set_stage(self, q, n, speaker) -> list[str]:
        f = self.forms[q]
        stage = next((s for s in f["stages"] if s["number"] == n), None)
        if stage is None:
            raise HarnessError(f"{q}: set_stage {n}, a stage the quest does not have")
        st = self.s["quests"].get(q)
        out = []
        if st is None:
            st = self.s["quests"][q] = {"stage": None, "done": [], "shown": [], "done_obj": [], "ended": None}
            self.s["order"].append(q)
        if st["ended"]:
            return []
        first_shown = stage["shown"] and not any(
            s["shown"] for s in f["stages"] if s["number"] in st["done"])
        st["stage"] = n
        if n not in st["done"]:
            st["done"].append(n)
        if first_shown and stage["ending"] == "none":
            out.append(f"Quest started: {f['quest']['name']}")
        for o in f["objectives"]:
            if n in o["completed_at"] and o["number"] in st["shown"] and o["number"] not in st["done_obj"]:
                st["done_obj"].append(o["number"])
                out.append(f"Objective completed: {o['text']}")
        if stage["shown"]:
            out.append(f"Journal entry ({f['quest']['name']}): {stage['journal']}")
        if stage["ending"] != "none":
            st["ended"] = stage["ending"]
            out.append(f"Quest {stage['ending']}: {f['quest']['name']}")
        else:
            for o in f["objectives"]:
                if n in o["shown_at"] and o["number"] not in st["shown"]:
                    st["shown"].append(o["number"])
                    out.append(f"New objective: {o['text']}")
        out += self._apply(q, stage["results"], speaker)
        for other, g in self.forms.items():
            if other == q:
                continue
            s0 = g["quest"]["start"]
            if s0["by"] == "quest_stage" and s0["quest"] == q and s0["quest_stage"] == n and other not in self.s["quests"]:
                out += self._set_stage(other, s0["stage"], None)
            for t in g["triggers"]:
                if t["kind"] == "quest_stage" and t["quest"] == q and t["quest_stage"] == n and self._trig_open(other, t):
                    out += self._set_stage(other, t["sets"], None)
        return out

    def _trig_open(self, q, t) -> bool:
        n = self.stage(q)
        if n is None or self.s["quests"][q]["ended"]:
            return False
        return t["prerequisite"] <= n < t["sets"] or t["sets"] <= t["prerequisite"] == n

    def _apply(self, q, results, speaker) -> list[str]:
        out = []
        for r in results:
            fn = RESULTS.get(r["do"])
            if fn is None:
                raise HarnessError(f"{q}: result word '{r['do']}' is not one the paper game knows")
            out += fn(self, q, r, speaker)
        return out

    def holds(self, q, conds, speaker) -> bool:
        for c in conds:
            fn = CONDITIONS.get(c["is"])
            if fn is None:
                raise HarnessError(f"{q}: condition word '{c['is']}' is not one the paper game knows")
            if not fn(self, q, c, speaker):
                return False
        return True

    def _lines_of(self, speaker, kinds, skip_skill=False):
        """(quest, line) open now for this speaker, in form order: the stage window and every condition hold (with
        `skip_skill`, every condition but a skill threshold: a persuasion is offered and checked when said)."""
        out = []
        for q, f in self.forms.items():
            n = self.stage(q)
            if n is None:
                continue
            for ln in f["lines"]:
                if ln["speaker"] == speaker and ln["kind"] in kinds and ln["first_stage"] <= n <= ln["last_stage"] \
                        and self.holds(q, [c for c in ln["conditions"]
                                           if not (skip_skill and c["is"] == "skill_at_least")], speaker):
                    out.append((q, ln))
        return out

    # -- dialogue ------------------------------------------------------------------------------------------------
    @staticmethod
    def _spoken(ln) -> str:
        return ln["text"] if ln["written"] else f"[not yet written; the gist:] {ln['text']}"

    def _talk_open(self, t) -> list[dict]:
        """A talker's own topics open now (talk.md): every topic but the greetings; a rumour only while its quest can
        start (a quest this run did not load waits at its start, as on a new game)."""
        out = []
        for tp in t.get("topics", []):
            if tp["topic"].startswith("talk.greet"):
                continue
            g = tp.get("gate")
            if g:
                q = self.by_editor.get(g["quest"])
                if q is None:
                    if g.get("last") is not None:
                        continue
                else:
                    n = self.stage(q)
                    hi = g["first"] if g.get("last") is None else g["last"]
                    if n is None or not (g["first"] <= n <= hi):
                        continue
            out.append(tp)
        return out

    def _menu(self, who) -> list[tuple[str, str, object]]:
        """The topics on screen: (label, kind, payload); quest topics first, then the person's own."""
        out = []
        for q, ln in self._lines_of(who, ("topic",), skip_skill=True):
            label = ln["prompt"] or "(no prompt)"
            if any(c["is"] == "skill_at_least" and c["skill"].lower() == "speech" for c in ln["conditions"]):
                label = f"(Persuade) {label}"
            elif not self.holds(q, [c for c in ln["conditions"] if c["is"] == "skill_at_least"], who):
                continue
            if label not in [m[0] for m in out]:
                out.append((label, "line", (q, ln)))
        t = self.ents[who]["talker"]
        if t:
            out += [(tp["prompt"], "talk", tp) for tp in self._talk_open(t)]
        return out

    def _menu_text(self, who) -> str:
        if self.s["question"]:
            return "Your answers:\n" + "\n".join(f"  {i + 1}. {lab}" for i, (lab, _, _) in enumerate(self._answers()))
        m = self._menu(who)
        if not m:
            return f"{self.name(who)} has nothing more to say to you."
        return "Topics:\n" + "\n".join(f"  {i + 1}. {lab}" for i, (lab, _, _) in enumerate(m))

    def _answers(self):
        q, ids = self.s["question"]["quest"], self.s["question"]["answers"]
        who = self.s["talking"]
        lines = {ln["id"]: ln for ln in self.forms[q]["lines"]}
        return [(lines[i]["prompt"] or "(no prompt)", "line", (q, lines[i])) for i in ids
                if i in lines and self.holds(q, lines[i]["conditions"], who)]

    def _say_line(self, q, ln, who) -> list[str]:
        out = [f'{self.name(who)}: "{self._spoken(ln)}"']
        out += self._apply(q, ln["results"], who)
        if who not in self.s["spoken"]:
            self.s["spoken"].append(who)
        self.s["question"] = {"quest": q, "answers": ln["answers"]} if ln["answers"] else None
        return out

    def _speaks_first(self) -> list[str]:
        out = []
        for q, f in self.forms.items():
            n = self.stage(q)
            if n is None or self.s["quests"][q]["ended"]:
                continue
            for ln in f["lines"]:
                who = ln["speaker"]
                if ln["kind"] != "speaks_first" or ln["id"] in self.s["fired"] or not ln["first_stage"] <= n <= ln["last_stage"]:
                    continue
                p = self._pos(who)
                d = _dist(self.s["pos"], p) if p else None
                if d is None or d > SPEAKS_FIRST_NEAR or not self._alive(who) or not self._on(who):
                    continue
                if not self.holds(q, ln["conditions"], who):
                    continue
                self.s["fired"].append(ln["id"])
                self.s["talking"] = who
                out += ["", f"{self.name(who)} walks up to you and speaks."] + self._say_line(q, ln, who)
                out.append(self._menu_text(who))
        return out

    # -- the commands --------------------------------------------------------------------------------------------
    def do(self, command: str) -> str:
        if self.s["ended"]:
            return "The session has ended."
        words = command.strip().split()
        if not words:
            return "Type a command: look, journal, map, go, talk, say, take, use, fight, pick, pickpocket, persuade, wait."
        verb, arg = words[0].lower(), " ".join(words[1:])
        fn = {"look": self.look, "journal": self.journal, "map": self.map, "go": self.go, "talk": self.talk,
              "say": self.say, "take": self.take, "use": self.use, "fight": self.fight, "pick": self.pick,
              "pickpocket": self.pickpocket, "persuade": self.persuade, "wait": self.wait}.get(verb)
        if fn is None:
            return f"'{verb}' is not something you can do here. Commands: look, journal, map, go, talk, say, take, " \
                   "use, fight, pick, pickpocket, persuade, wait."
        self.s["commands"] += 1
        if verb not in ("say", "persuade", "journal", "map"):
            if verb != "look":
                self.s["talking"] = None
                self.s["question"] = None
        return fn(arg) if verb not in ("look", "journal", "map", "wait") else fn()

    def _find(self, text, pool) -> tuple[str | None, str | None]:
        """An entity among `pool` by the name the player typed: exact, then a unique start, then a unique part."""
        t = text.lower().strip().removeprefix("the ").strip()
        if not t:
            return None, "Name who or what."
        named = [(self.name(e), e) for e in pool]
        for test in (lambda n: n.lower() == t, lambda n: n.lower().startswith(t), lambda n: t in n.lower()):
            hits = [e for n, e in named if test(n)]
            if len(hits) == 1:
                return hits[0], None
            if len(hits) > 1:
                return None, "Which one? " + ", ".join(sorted({self.name(e) for e in hits}))
        return None, None

    def _visible(self):
        return [e for e in self.ents if self.ents[e]["kind"] != "marker" and self._on(e) and self._near(e)
                and e not in self.s["taken"]]

    def look(self) -> str:
        pos = self.s["pos"]
        out = [f"You are in {self.place_name(pos)}." if pos["interior"] else f"You are at {self.place_name(pos)}."]
        people = [e for e in self._visible() if self.ents[e]["kind"] == "person"]
        things = [e for e in self._visible() if self.ents[e]["kind"] == "thing"]
        doors = [e for e in self._visible() if self.ents[e]["kind"] == "door"]

        def word(e):
            if not self._alive(e):
                return "dead"
            if self.ents[e]["hostile"] or e in self.s["hostile"]:
                return "hostile"
            t = self.ents[e]["talker"]
            return (t.get("word") if t else None) or "a person"
        out.append("People: " + ("; ".join(f"{self.name(e)} ({word(e)})" for e in people) if people else "nobody"))
        out.append("Things: " + ("; ".join(
            self.name(e) + (f" (in {self.name(self.ents[e]['container'])})" if self.ents[e]["container"] else "")
            for e in things) if things else "nothing of note"))
        out.append("Doors: " + ("; ".join(self.name(e) + (" (locked)" if self._locked(e) else "") for e in doors)
                                if doors else "none"))
        return "\n".join(out)

    def _locked(self, e) -> bool:
        return self.s["locked"].get(e, self.world.get("locked", {}).get(e, False))

    def journal(self) -> str:
        if not self.s["order"]:
            return "Your journal is empty."
        out = []
        for q in self.s["order"]:
            f, st = self.forms[q], self.s["quests"][q]
            entries = [s for n in st["done"] for s in f["stages"] if s["number"] == n and s["shown"]]
            if not entries:
                continue
            status = {"completed": " (completed)", "failed": " (failed)"}.get(st["ended"], "")
            out.append(f"== {f['quest']['name']}{status}")
            out += [f"- {s['journal']}" for s in entries]
            act = self._active(q)
            if act:
                out.append("Objectives:")
                out += [f"  [ ] {o['text']}" for o in act]
        return "\n".join(out) if out else "Your journal is empty."

    def _markers(self):
        out = []
        for q in self.s["order"]:
            for o in self._active(q):
                for t in o["targets"]:
                    if t in self.ents and self._on(t) and (self._pos(t) is not None):
                        out.append((q, o, t))
        return out

    def _where(self, p):
        """A position as the map shows it: outdoors its coordinates; indoors, the place and its way in if known."""
        if not p["interior"]:
            return p, f"({p['x']:.0f}, {p['y']:.0f})"
        ent = self.world.get("places", {}).get(p["cell"], {}).get("entrance")
        if ent:
            return {"cell": "", "interior": False, "x": ent["x"], "y": ent["y"]}, \
                f"inside {self.place_name(p)}; its door is at ({ent['x']:.0f}, {ent['y']:.0f})"
        return None, f"inside {self.place_name(p)} (where its door is, the map does not show)"

    def map(self) -> str:
        pos = self.s["pos"]
        me, mine = self._where(pos)
        out = [f"You: {self.place_name(pos)}, {mine}"]
        marks = self._markers()
        if not marks:
            out.append("No quest markers.")
        for i, (q, o, t) in enumerate(marks, 1):
            p = self._pos(t)
            there, desc = self._where(p)
            what = {"person": "a person", "thing": "a thing", "door": "a door", "marker": "a place"}[self.ents[t]["kind"]]
            label = self.name(t) if self.ents[t]["kind"] != "marker" else self.place_name(p)
            line = f"Marker {i}: {label} ({what}), for \"{o['text']}\": {desc}"
            if pos["interior"] and p["interior"] and pos["cell"] == p["cell"]:
                line += "; here, in this place"
            elif me and there:
                d = _dist(me, there)
                line += f"; {_how_far(d)} to the {_compass(me, there)}" if d > NEAR else "; right here"
            out.append(line)
        known = [c for c in self.s["visited"]] + [self._pos(t)["cell"] for _, _, t in marks]
        names = []
        for c in known:
            n = self.world.get("places", {}).get(c, {}).get("name") or self.world.get("names", {}).get(c)
            if n and n not in names:
                names.append(n)
        out.append("Places you know: " + (", ".join(names) if names else "none"))
        return "\n".join(out)

    def _places(self) -> dict[str, str]:
        cells = {self._pos(e)["cell"] for e in self.ents if self._pos(e)}
        out = {}
        for c in sorted(cells):
            n = self.world.get("places", {}).get(c, {}).get("name") or self.world.get("names", {}).get(c)
            if n:
                out.setdefault(n.lower(), c)
        return out

    def go(self, arg) -> str:
        a = arg.lower().strip()
        marks = self._markers()
        target = None
        if a.removeprefix("marker").strip().isdigit():
            i = int(a.removeprefix("marker").strip())
            if not 1 <= i <= len(marks):
                return f"There is no marker {i} on your map."
            target = self._pos(marks[i - 1][2])
        if target is None:
            pool = [e for e in self.ents if self.ents[e]["kind"] != "marker" and self._on(e) and e not in self.s["taken"]
                    and self._pos(e)]
            e, err = self._find(arg, pool)
            if err:
                return err
            if e:
                target = self._pos(e)
        if target is None:
            c = self._places().get(a.removeprefix("to ").strip())
            if c:
                target = next(self._pos(e) for e in self.ents if self._pos(e) and self._pos(e)["cell"] == c)
        if target is None:
            return f"You know of no person, thing or place called '{arg}'."
        here = self.s["pos"]
        if here["cell"] == target["cell"] and here["interior"]:
            how = "It is here, in this place."
        else:
            d = _dist(here, target)
            if d is not None:
                how = "It was right here." if d <= NEAR / 3 else \
                    f"You arrive. It was {_how_far(d)} to the {_compass(here, target)}."
            else:
                a_out, _ = self._where(here)
                b_in, _ = self._where(target)
                d2 = _dist(a_out, b_in) if a_out and b_in else None
                trip = f" It was {_how_far(d2)} to the {_compass(a_out, b_in)}." if d2 else ""
                how = (f"You arrive and go in through a door.{trip}" if target["interior"]
                       else f"You go out through a door and on.{trip}")
        self.s["pos"] = dict(target)
        self._visit()
        return "\n".join([how, self.look()] + self._speaks_first())

    def talk(self, arg) -> str:
        people = [e for e in self._visible() if self.ents[e]["kind"] == "person"]
        e, err = self._find(arg, people)
        if err or e is None:
            return err or f"Nobody called '{arg}' is near you."
        if not self._alive(e):
            return f"{self.name(e)} is dead."
        if self.ents[e]["hostile"] or e in self.s["hostile"]:
            return f"{self.name(e)} attacks you rather than talk."
        self.s["talking"] = e
        out = []
        greet = self._lines_of(e, ("greeting",))
        t = self.ents[e]["talker"]
        if greet:
            q, ln = greet[0]
            out += [f'{self.name(e)}: "{self._spoken(ln)}"'] + self._apply(q, ln["results"], e)
        elif t and any(tp["topic"] == "talk.greet-stranger" for tp in t.get("topics", [])):
            tp = next(tp for tp in t["topics"] if tp["topic"] == "talk.greet-stranger")
            out.append(f'{self.name(e)}: "{" ".join(tp["lines"])}"')
        else:
            out.append(f"{self.name(e)} looks at you and waits.")
        out.append(self._menu_text(e))
        return "\n".join(out)

    def say(self, arg) -> str:
        who = self.s["talking"]
        if who is None:
            return "You are not talking to anyone. Talk to someone first."
        menu = self._answers() if self.s["question"] else self._menu(who)
        a = arg.strip().strip('"').strip()
        pick = None
        if a.isdigit() and 1 <= int(a) <= len(menu):
            pick = menu[int(a) - 1]
        else:
            low = a.lower()
            for test in (lambda m: m.lower() == low, lambda m: m.lower().removeprefix("(persuade) ") == low,
                         lambda m: low in m.lower()):
                hits = [m for m in menu if test(m[0])]
                if len(hits) == 1:
                    pick = hits[0]
                    break
        if pick is None:
            return f"That is not one of the choices.\n{self._menu_text(who)}"
        label, kind, payload = pick
        if kind == "talk":
            out = [f'{self.name(who)}: "{" ".join(payload["lines"])}"']
            if who not in self.s["spoken"]:
                self.s["spoken"].append(who)
            return "\n".join(out + [self._menu_text(who)])
        q, ln = payload
        need = [c for c in ln["conditions"] if c["is"] == "skill_at_least"]
        if need and not self.holds(q, need, who):
            c = need[0]
            have = self._skill(c["skill"])
            self.s["question"] = None
            return "\n".join([f"{self.name(who)} is not persuaded. (Your {c['skill']} is {have}; this needed "
                              f"{c['value']}.)", self._menu_text(who)])
        out = self._say_line(q, ln, who)
        if self.s["talking"] == who:
            out.append(self._menu_text(who))
        return "\n".join(out)

    def persuade(self, arg) -> str:
        return self.say(arg)

    def take(self, arg) -> str:
        e, err = self._find(arg, self._visible())
        if err or e is None:
            return err or f"There is no '{arg}' near you."
        if self.ents[e]["kind"] != "thing":
            return f"You cannot take {self.name(e)}."
        self.s["taken"].append(e)
        key = self.ents[e]["item"] or e
        self.s["items"][key] = self.s["items"].get(key, 0) + 1
        out = [f"Added: {self.name(e)}"]
        out += self._fire("take", e)
        return "\n".join(out)

    def use(self, arg) -> str:
        held = [e for e in self.s["taken"]]
        e, err = self._find(arg, self._visible() + held)
        if err or e is None:
            return err or f"There is no '{arg}' near you."
        kind = self.ents[e]["kind"]
        if kind == "person":
            return f"To speak with {self.name(e)}, talk to them."
        out = []
        if kind == "door":
            if self._locked(e):
                return f"{self.name(e)} is locked."
            dest = self.world.get("doors", {}).get(e)
            if dest:
                self.s["pos"] = dict(dest)
                self._visit()
                out += [f"You go through {self.name(e)}.", self.look()]
            else:
                out.append(f"You open {self.name(e)}.")
        else:
            out.append(f"You use {self.name(e)}.")
        out += self._fire("use", e)
        if kind == "door" and self.world.get("doors", {}).get(e):
            out += self._speaks_first()
        return "\n".join(out)

    def _fire(self, kind, ref) -> list[str]:
        out = []
        for q, f in self.forms.items():
            for t in f["triggers"]:
                if t["kind"] == kind and t.get("ref") == ref and self._trig_open(q, t):
                    out += self._set_stage(q, t["sets"], None)
        return out

    def fight(self, arg) -> str:
        words = arg.split()
        outcome = words[-1].lower() if words and words[-1].lower() in ("win", "lose", "flee") else None
        if outcome is None:
            return "Say how the fight ends: fight <who> win, fight <who> lose, or fight <who> flee."
        e, err = self._find(" ".join(words[:-1]), [x for x in self._visible() if self.ents[x]["kind"] == "person"])
        if err or e is None:
            return err or f"Nobody called '{' '.join(words[:-1])}' is near you."
        if not self._alive(e):
            return f"{self.name(e)} is already dead."
        if outcome == "lose":
            return "You died. You load your last save."
        if outcome == "flee":
            return f"You get away from {self.name(e)}."
        return "\n".join([f"{self.name(e)} is dead."] + self.kill(e))

    def kill(self, e) -> list[str]:
        self.s["dead"].append(e)
        out = self._fire("death", e)
        message = False
        for q, f in self.forms.items():
            for m in f["must_live"]:
                if m["ref"] != e:
                    continue
                st = self.s["quests"].get(q)
                if st is not None and not st["ended"]:
                    out += self._set_stage(q, m["fail_stage"], None)
                message |= m["main_message"] and f["quest"]["kind"] in ("main", "faction") and \
                    not (st is not None and st["ended"] == "completed")
        if message and not self.s["message_shown"]:
            self.s["message_shown"] = True
            out.append(f"[Message box] {MAIN_MESSAGE}")
        return out

    def pick(self, arg) -> str:
        words = arg.split()
        outcome = words[-1].lower() if words and words[-1].lower() in ("win", "fail") else None
        if outcome is None:
            return "Say how the lock goes: pick <lock> win, or pick <lock> fail."
        e, err = self._find(" ".join(words[:-1]), self._visible())
        if err or e is None:
            return err or "There is no such lock near you."
        if not self._locked(e):
            return f"{self.name(e)} is not locked."
        if outcome == "fail":
            return "Your pick breaks; the lock holds."
        self.s["locked"][e] = False
        return f"You pick the lock of {self.name(e)}. (Lockpicking {self._skill('Lockpicking')}.)"

    def pickpocket(self, arg) -> str:
        e, err = self._find(arg, [x for x in self._visible() if self.ents[x]["kind"] == "person"])
        if err or e is None:
            return err or f"Nobody called '{arg}' is near you."
        return f"You find nothing on {self.name(e)} worth taking."

    def wait(self) -> str:
        return "You wait an hour."

    def _skill(self, skill) -> int:
        k = {"speechcraft": "speech"}.get(skill.lower(), skill.lower()).replace("-", "").replace(" ", "")  # the Morrowind word
        for s, v in self.s["sheet"]["skills"].items():
            if s.lower().replace("-", "").replace(" ", "") == k:
                return v
        raise HarnessError(f"skill '{skill}' is not one of the character sheet's skills")

    # -- what the transcript keeps ---------------------------------------------------------------------------
    def summary(self) -> dict:
        return {"stages": {q: self.s["quests"][q]["stage"] for q in self.s["order"]},
                "ended": {q: self.s["quests"][q]["ended"] for q in self.s["order"] if self.s["quests"][q]["ended"]},
                "position": {"cell": self.s["pos"]["cell"], "place": self.place_name(self.s["pos"]),
                             "x": round(self.s["pos"]["x"]), "y": round(self.s["pos"]["y"])},
                "markers": [t for _, _, t in self._markers()], "talking": self.s["talking"]}

    def all_ended(self) -> bool:
        return bool(self.s["order"]) and all(self.s["quests"][q]["ended"] for q in self.s["order"])

    def snapshot(self) -> dict:
        return copy.deepcopy(self.s)
