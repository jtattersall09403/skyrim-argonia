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
from tools.questform.rules import Form

# Skyrim units: about 70 to a metre. "Near" is close enough to notice and to talk (outdoors); speaks-first fires
# when the player arrives this near its speaker.
UNITS_PER_M = 70.0
NEAR = 1500.0
SPEAKS_FIRST_NEAR = 1500.0
MAX_COMMANDS = 60
# The message on a must-live death, by the quest's kind (docs/research/morrowind-level-scripting.md section 5, the
# recommended text; the builder's message boxes carry the same words).
MESSAGES = {
    "main": "With this death the root of what was to come is cut: the main story can no longer be finished. Load an "
            "earlier save to let it grow again, or go on in the marsh as it now is.",
    "faction": "With this death the root of what was to come is cut: this faction's story can no longer be finished. "
               "Load an earlier save to let it grow again, or go on in the marsh as it now is.",
}
SKILLS = ("Alchemy", "Alteration", "Archery", "Block", "Conjuration", "Destruction", "Enchanting", "Heavy Armor",
          "Illusion", "Light Armor", "Lockpicking", "One-handed", "Pickpocket", "Restoration", "Smithing", "Sneak",
          "Speech", "Two-handed")
# The story vocabulary's skill ids (85-condition-vocabulary, skillAtLeast) that Skyrim names otherwise.
SKILL_ALIASES = {"speechcraft": "speech", "security": "lockpicking", "marksman": "archery"}
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
# Skyrim's own lockpick and gold: a form's thing or container entry of these bases is a lockpick or gold coins.
LOCKPICK, GOLD = "00000A:Skyrim.esm", "00000F:Skyrim.esm"
VANILLA_NAMES = {LOCKPICK: "Lockpick", GOLD: "Gold"}
# The same two as the story database's item ids, which a compiled form names stock things by.
STOCK = {"item.lockpick": LOCKPICK, "item.gold": GOLD}
# The Lockpicking a lock level plausibly needs: above it the lock is said to be beyond the player (the one table).
LOCK_SKILL = {"novice": 0, "apprentice": 15, "adept": 25, "expert": 50, "master": 75}
CHOICES = ("unseen", "seen")
# A person's race and sex in a word: Skyrim's race names, and the story database's race words.
RACE_WORDS = {"argonian": "Argonian", "breton": "Breton", "dunmer": "Dark Elf", "darkelf": "Dark Elf",
              "altmer": "High Elf", "highelf": "High Elf", "bosmer": "Wood Elf", "woodelf": "Wood Elf",
              "imperial": "Imperial", "khajiit": "Khajiit", "nord": "Nord", "orc": "Orc", "orsimer": "Orc",
              "redguard": "Redguard"}


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

    def __init__(self, forms: list[dict], world: dict, state: dict | None = None, sheet: dict | None = None,
                 strict: bool = True):
        """`strict` False (the walker's): a name nobody gives shows as its id instead of stopping the run."""
        self.forms = {f["quest"]["id"]: f for f in forms}
        self.by_editor = {f["quest"]["editor_id"]: f["quest"]["id"] for f in forms}
        self.world = world
        self.strict = strict
        self.quiet = False                  # the walker's: a move shows no `look` (it reads states, not screens)
        for f in forms:
            errs = validate.errors(f)
            if errs:
                raise HarnessError(f"form {f.get('quest', {}).get('id')}: not a quest form: {'; '.join(errs[:5])}")
            self._scan(f)
        self.ents = self._entities()
        for f in forms:                     # a door a result unlocks and the form does not lock starts locked, key only
            for r in [r for s in f["stages"] for r in s["results"]] + [r for ln in f["lines"] for r in ln["results"]]:
                if r["do"] == "unlock_door" and r["ref"] in self.ents and not self.ents[r["ref"]]["lock"]:
                    self.ents[r["ref"]]["lock"] = {"level": "key"}
        self.holders = {e["container"] for e in self.ents.values() if e["container"]} | \
            {e["carried_by"] for e in self.ents.values() if e["carried_by"]} | \
            {k for k, e in self.ents.items() if e["contents"] or (e["lock"] and e["kind"] == "thing")}
        if strict:
            self._check_names()
        self.s = state if state is not None else self._fresh(sheet or new_sheet())
        fresh = self._fresh(self.s["sheet"])
        for k, v in fresh.items():          # a session saved before a field existed, or a state from fewer forms
            self.s.setdefault(k, v)
        for k, v in fresh["contents"].items():
            self.s["contents"].setdefault(k, v)

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
            form = Form(f)
            for r in f["refs"]:
                key = r["placement"].get("existing")
                base = r["placement"].get("base") or {}
                item = LOCKPICK if base.get("id") == LOCKPICK else form.item_of(r["id"])
                item = STOCK.get(item, item)
                e = ents.setdefault(r["id"], {"id": r["id"], "kind": r["kind"], "enabled": r["enabled"],
                                              "hostile": bool(r.get("hostile")), "at": r.get("at"),
                                              "container": r["placement"].get("container"),
                                              "carried_by": r["placement"].get("carried_by"),
                                              "item": item, "count": r.get("count") or 1, "lock": r.get("lock"), "owner": r.get("owner"),
                                              "contents": r.get("contents") or [], "text": r.get("text"),
                                              "talker": None, "quest": f["quest"]["id"]})
                for k in ("lock", "owner", "contents", "text", "container", "carried_by"):      # a ref two
                    e[k] = e[k] or (r.get(k) if k not in ("container", "carried_by")                # forms share
                                    else r["placement"].get(k)) or ([] if k == "contents" else None)
                if key in talkers:
                    e["talker"] = talkers.pop(key)
        for t in talkers.values():
            ents[t["id"]] = {"id": t["id"], "kind": "person", "enabled": True, "hostile": False,
                             "at": {"cell": t["cell"], "interior": t["interior"], "x": t["x"], "y": t["y"], "z": 0.0},
                             "container": None, "carried_by": None, "item": None, "count": 1, "lock": None, "owner": None,
                             "contents": [], "text": None, "talker": t, "quest": None}
        return ents

    def _check_names(self):
        names = self.world.get("names", {})
        missing = {e["id"] for e in self.ents.values() if not (e["talker"] and e["talker"].get("name"))
                   and e["kind"] != "marker" and not names.get(e["id"])}
        items = {c["item"] for e in self.ents.values() for c in e["contents"]} | \
            {e["lock"]["key"] for e in self.ents.values() if e["lock"] and e["lock"].get("key")}
        for f in self.forms.values():
            for r in [r for s in f["stages"] for r in s["results"]] + [r for ln in f["lines"] for r in ln["results"]]:
                if r["do"] in ("give_item", "take_item"):
                    items.add(r["item"])
        missing |= {i for i in items if self._item_name(i) is None}
        if missing:
            raise HarnessError("no name the player would see for: " + ", ".join(sorted(missing)) +
                               " (give each a name in the run's names file)")

    def _fresh(self, sheet) -> dict:
        return {"quests": {}, "order": [], "items": {}, "gold": 0, "numbers": {}, "factions": {}, "regard": {},
                "dead": [], "switched": {}, "locked": {}, "taken": [], "pos": None, "visited": [], "spoken": [],
                "fired": [], "talking": None, "question": None, "hostile": [],
                "opened": [], "owned": [], "contents": {k: {c["item"]: c["count"] for c in e["contents"]}
                                           for k, e in self.ents.items() if e["contents"]},
                "crimes": [], "sheet": sheet, "commands": 0, "ended": False}

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

    def resume(self, start: str | None = None, at: str | None = None) -> str:
        """The player takes over a game already played on (by the walker, for --after): `start` begins at its start
        stage if it has not begun; the player stands at `at`, else at the first target of an active objective. The
        screen shows each running quest's latest journal entry and objectives, then the `look`."""
        out = []
        if start:
            if start not in self.forms:
                raise HarnessError(f"--start {start}: no such quest in this run")
            if start not in self.s["quests"]:
                out += self._set_stage(start, self.forms[start]["quest"]["start"]["stage"], None)
        self.s.update(commands=0, talking=None, question=None, opened=[])
        if at is None:
            tg = [t for q in self.s["order"] for o in self._active(q) for t in o["targets"] if self._pos(t)]
            at = tg[0] if tg else None
        if at is None or at not in self.ents or self._pos(at) is None:
            raise HarnessError(f"start position: {at} is not a placed ref of this run (give --at)")
        self.s["pos"] = dict(self._pos(at))
        self._visit()
        sh = self.s["sheet"]
        head = [f"Your game goes on. You are a {sh['sex']} {race_key(sh['race']).capitalize()}."]
        for q in self.s["order"]:
            st, f = self.s["quests"][q], self.forms[q]
            if st["ended"]:
                continue
            last = next((s for n in reversed(st["done"]) for s in f["stages"] if s["number"] == n and s["shown"]), None)
            if last:
                head.append(f"Journal ({f['quest']['name']}): {last['journal']}")
            head += [f"Objective: {o['text']}" for o in self._active(q)]
        return "\n".join(head + out + ["", self.look()] + self._speaks_first())

    def item_of(self, x: str) -> str:
        """The item id the player holds for `x`: a thing ref's item (the form's item id: a unique thing by its ref id,
        a stock thing by its base), else `x` itself (already an item id); Skyrim's lockpick and gold by one id."""
        e = self.ents.get(x)
        return e["item"] if e and e["kind"] == "thing" and e["item"] else STOCK.get(x, x)

    def _text(self, e) -> str | None:
        """A readable thing's words: its ref's, else the form's `texts` for its item."""
        texts = self.world.get("texts", {})
        return self.ents[e]["text"] or texts.get(self.ents[e]["item"]) or texts.get(e)

    # -- names and places ------------------------------------------------------------------------------------------
    def name(self, eid: str) -> str:
        e = self.ents.get(eid)
        if e and e["talker"] and e["talker"].get("name") and not self.world.get("names", {}).get(eid):
            return e["talker"]["name"]
        n = self.world.get("names", {}).get(eid)
        if n is None:
            if not self.strict:
                return eid
            raise HarnessError(f"no name the player would see for {eid}")
        return n

    def _item_name(self, item) -> str | None:
        n = self.world.get("names", {}).get(item) or VANILLA_NAMES.get(item)
        if n is None:
            ref = next((k for k, e in self.ents.items() if e["item"] == item and e["kind"] == "thing"), None)
            n = self.world.get("names", {}).get(ref) if ref else None
        return n

    def item_name(self, item) -> str:
        """An item id's name: the form's (or a names file's) for it, else its thing's, else Skyrim's own."""
        n = self._item_name(item)
        if n is None:
            if not self.strict:
                return item
            raise HarnessError(f"no name the player would see for {item}")
        return n

    def who(self, eid) -> str | None:
        """A person in a word, "an Argonian woman", where the form or the world database says race or sex."""
        e = self.ents[eid]
        p = {**(e["talker"] or {}), **self.world.get("people", {}).get(eid, {})}
        race = RACE_WORDS.get(race_key(p.get("race") or "").replace("_", ""), p.get("race"))
        sex = {"female": "woman", "male": "man"}.get((p.get("sex") or "").lower())
        words = " ".join(w for w in (race, sex) if w)
        if not words:
            return None
        return ("an " if words[0].lower() in "aeiou" else "a ") + words

    def _owner_name(self, owner) -> str:
        if owner in self.ents:
            return self.name(owner)
        return self.world.get("names", {}).get(owner) or "the owner"

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
        if e["container"] or e["carried_by"]:
            return self._pos(e["container"] or e["carried_by"])
        return e["at"]

    def _on(self, eid) -> bool:
        e = self.ents[eid]
        holder = None if eid in self.s["taken"] else e["container"] or e["carried_by"]
        return self.s["switched"].get(eid, e["enabled"]) and (holder is None or self._on(holder))

    def _loose(self, eid) -> bool:
        """On the ground: not in a container, not carried, not taken."""
        e = self.ents[eid]
        return not (e["container"] or e["carried_by"]) and eid not in self.s["taken"]

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
        """The quest's stage as a line's window reads it: the highest stage done (nothing sets a stage below one done:
        the `stage-order` rule); None before it starts."""
        st = self.s["quests"].get(q)
        return max(st["done"]) if st and st["done"] else None

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
            st = self.s["quests"][q] = {"done": [], "shown": [], "done_obj": [], "ended": None}
            self.s["order"].append(q)
        if st["ended"] or n in st["done"]:
            return []               # as the engine: a stage already done is never set again, nor its results run
        first_shown = stage["shown"] and not any(
            s["shown"] for s in f["stages"] if s["number"] in st["done"])
        st["done"].append(n)
        if first_shown and stage["ending"] == "none":
            out.append(f"Quest started: {f['quest']['name']}")
        for o in f["objectives"]:
            if n in o["completed_at"] and o["number"] in st["shown"] and o["number"] not in st["done_obj"]:
                st["done_obj"].append(o["number"])
                out.append(f"Objective completed: {o['text']}")
        if stage["shown"]:
            out.append(f"Journal entry ({f['quest']['name']}): {stage['journal']}")
        if n == f["quest"]["start"]["stage"]:    # the start check: a who-must-live person, or a death trigger's, dead
            for ref, to in [(m["ref"], m["fail_stage"]) for m in f["must_live"] if self._within(q, m, n)] + \
                    [(t["ref"], t["sets"]) for t in f["triggers"] if t["kind"] == "death" and t["prerequisite"] == n]:
                if not self._alive(ref):
                    return out + self._set_stage(q, to, None)       # the rest of the start stage is skipped
        if stage["ending"] != "none":            # an ending closes every objective still shown
            word = "completed" if stage["ending"] == "completed" else "failed"
            for o in f["objectives"]:
                if o["number"] in st["shown"] and o["number"] not in st["done_obj"]:
                    st["done_obj"].append(o["number"])
                    out.append(f"Objective {word}: {o['text']}")
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
        """As the vanilla trigger scripts: the quest runs, its prerequisite stage is done and the stage it sets is not;
        with `until`, the quest's stage is below it."""
        st = self.s["quests"].get(q)
        return bool(st) and not st["ended"] and t["prerequisite"] in st["done"] and t["sets"] not in st["done"] and \
            ("until" not in t or self.stage(q) < t["until"])

    def _within(self, q, m, n=None) -> bool:
        """A who-must-live row's window as the builder guards it: its `from` stage done (or beginning: `n`, for the
        start check) and the stage at most its `to`."""
        st = self.s["quests"].get(q)
        done = st["done"] if st else []
        stage = n if n is not None else (self.stage(q) or 0)
        return (m.get("from") is None or m["from"] in done or m["from"] == n) and \
            (m.get("to") is None or stage <= m["to"])

    def _apply(self, q, results, speaker) -> list[str]:
        out = []
        for r in results:
            fn = RESULTS.get(r["do"])
            if fn is None:
                raise HarnessError(f"{q}: result word '{r['do']}' is not one the paper game knows")
            out += fn(self, q, r, speaker)
        return out

    def holds(self, q, conds, speaker) -> bool:
        """Every condition holds; `not: true` turns a condition round."""
        for c in conds:
            fn = CONDITIONS.get(c["is"])
            if fn is None:
                raise HarnessError(f"{q}: condition word '{c['is']}' is not one the paper game knows")
            if bool(fn(self, q, c, speaker)) == bool(c.get("not")):
                return False
        return True

    def _can_say(self, q, ln, speaker) -> bool:
        """A line can be said now: its quest's stage is within its window and every condition holds."""
        n = self.stage(q)
        return n is not None and ln["first_stage"] <= n <= ln["last_stage"] and self.holds(q, ln["conditions"], speaker)

    def _lines_of(self, speaker, kinds):
        """(quest, line) that can be said now by this speaker, in form order."""
        return [(q, ln) for q, f in self.forms.items() for ln in f["lines"]
                if ln["speaker"] == speaker and ln["kind"] in kinds and self._can_say(q, ln, speaker)]

    @staticmethod
    def _first_per_prompt(pairs) -> list[tuple[str, str, object]]:
        """One entry per prompt, holding the first line that can be said (the engine tries a topic's lines in order)."""
        out = []
        for q, ln in pairs:
            label = ln["prompt"] or "(no prompt)"
            if label not in [m[0] for m in out]:
                out.append((label, "line", (q, ln)))
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
        out = self._first_per_prompt(self._lines_of(who, ("topic",)))
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
        return self._first_per_prompt([(q, lines[i]) for i in ids if i in lines and self._can_say(q, lines[i], who)])

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
            if self.stage(q) is None or self.s["quests"][q]["ended"]:
                continue
            for ln in f["lines"]:
                who = ln["speaker"]
                if ln["kind"] != "speaks_first" or ln["id"] in self.s["fired"]:
                    continue
                p = self._pos(who)
                d = _dist(self.s["pos"], p) if p else None
                if d is None or d > SPEAKS_FIRST_NEAR or not self._alive(who) or not self._on(who):
                    continue
                if not self._can_say(q, ln, who):
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
        self.s["commands"] += 1             # every command counts towards the limit, one the game refuses too
        self.s.pop("travel", None)
        if not words:
            return "Type a command: look, journal, map, go, talk, say, take, use, fight, pick, pickpocket, wait."
        verb, arg = words[0].lower(), " ".join(words[1:])
        fn = {"look": self.look, "journal": self.journal, "map": self.map, "go": self.go, "talk": self.talk,
              "say": self.say, "take": self.take, "use": self.use, "fight": self.fight, "pick": self.pick,
              "pickpocket": self.pickpocket, "wait": self.wait}.get(verb)
        if fn is None:
            return f"'{verb}' is not something you can do here. Commands: look, journal, map, go, talk, say, take, " \
                   "use, fight, pick, pickpocket, wait."
        if verb not in ("say", "journal", "map"):
            if verb != "look":
                self.s["talking"] = None
                self.s["question"] = None
        return fn(arg) if verb not in ("look", "journal", "map", "wait") else fn()

    def _find(self, text, pool) -> tuple[str | None, str | None]:
        """An entity among `pool` by the name the player typed: exact, then a unique start, then a unique part."""
        t = text.lower().strip().removeprefix("the ").strip()
        if t.startswith("#"):                # the walker's way: the key itself, no names needed
            return next((k for k in pool if k.lower() == t[1:]), None), None
        return self._find_in(text, [(self.label(e, pool), e) for e in pool])

    def label(self, e, pool) -> str:
        """A name as the player tells it from others near: two people or things of one name are "<name> 1" and
        "<name> 2", in the order they are listed."""
        n = self.name(e)
        same = [x for x in pool if self.name(x) == n]
        return n if len(same) < 2 else f"{n} {same.index(e) + 1}"

    @staticmethod
    def _find_in(text, named) -> tuple[str | None, str | None]:
        """A key among (name, key) pairs by the name typed; `#<key>` names a key itself (the walker's way)."""
        t = text.lower().strip().removeprefix("the ").strip()
        if not t:
            return None, "Name who or what."
        if t.startswith("#"):
            hit = [k for _, k in named if k.lower() == t[1:]]
            return (hit[0], None) if hit else (None, None)
        for test in (lambda n: n.lower() == t, lambda n: n.lower().startswith(t), lambda n: t in n.lower()):
            hits = [k for n, k in named if test(n)]
            if len(set(hits)) == 1:
                return hits[0], None
            if len(hits) > 1:
                return None, "Which one? " + ", ".join(sorted({n for n, k in named if k in hits}))
        return None, None

    @staticmethod
    def _choice(arg, words) -> tuple[str, str | None]:
        """The text before a trailing outcome word, and that word (or None)."""
        w = arg.split()
        if w and w[-1].lower() in words:
            return " ".join(w[:-1]), w[-1].lower()
        return arg, None

    def _visible(self):
        """Everyone and everything near and in plain sight (not inside a container or carried)."""
        return [e for e in self.ents if self.ents[e]["kind"] != "marker" and self._on(e) and self._near(e)
                and self._loose(e)]

    def look(self) -> str:
        pos = self.s["pos"]
        out = [f"You are in {self.place_name(pos)}." if pos["interior"] else f"You are at {self.place_name(pos)}."]
        people = [e for e in self._visible() if self.ents[e]["kind"] == "person"]
        things = [e for e in self._visible() if self.ents[e]["kind"] == "thing" and self._loose(e)]
        doors = [e for e in self._visible() if self.ents[e]["kind"] == "door"]

        def word(e):
            words = [self.who(e)] if self.who(e) else []
            if not self._alive(e):
                words.append("dead")
            elif self.ents[e]["hostile"] or e in self.s["hostile"]:
                words.append("hostile")
            return ", ".join(words) or "a person"

        def marks(e):
            m = ["locked" + (f", {self._lock_word(e)}" if self.ents[e]["lock"] else "")] if self._locked(e) else []
            m += ["owned"] if self._owner(e) else []
            return f" ({'; '.join(m)})" if m else ""
        here = self._visible()
        out.append("People: " + ("; ".join(f"{self.label(e, here)} ({word(e)})" for e in people) if people
                                 else "nobody"))
        out.append("Things: " + ("; ".join(self.label(e, here) + marks(e) for e in things) if things
                                 else "nothing of note"))
        out.append("Doors: " + ("; ".join(self.label(e, here) + marks(e) for e in doors) if doors else "none"))
        return "\n".join(out)

    def _locked(self, e) -> bool:
        return self.s["locked"].get(e, bool(self.ents[e]["lock"]))

    def _lock_word(self, e) -> str:
        lk = self.ents[e]["lock"]
        if not lk:
            return "a lock"
        return "needs a key" if lk["level"] == "key" else lk["level"].capitalize()

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
        target, travel = None, None
        if a.removeprefix("marker").strip().isdigit():
            i = int(a.removeprefix("marker").strip())
            if not 1 <= i <= len(marks):
                return f"There is no marker {i} on your map."
            target, travel = self._pos(marks[i - 1][2]), "marker"
        if target is None:
            pool = [k for k in self.ents if (not a.startswith("#") or k.lower() == a[1:]) and
                    self.ents[k]["kind"] != "marker" and self._on(k) and k not in self.s["taken"] and self._pos(k)]
            e, err = self._find(arg, pool)
            if err:
                return err
            if e:
                target = self._pos(e)
                travel = "marker" if e in [t for _, _, t in marks] else "in sight" if e in self._visible() else \
                    "known place" if target["cell"] in self.s["visited"] else "name only"
        if target is None:
            c = self._places().get(a.removeprefix("to ").strip())
            if c:
                target = next(self._pos(e) for e in self.ents if self._pos(e) and self._pos(e)["cell"] == c)
                travel = "known place" if c in self.s["visited"] or c in [self._pos(t)["cell"] for _, _, t in marks] \
                    else "name only"
        if target is None:
            return f"You know of no person, thing or place called '{arg}'."
        here = self.s["pos"]
        shut = self._shut(target)
        if shut:
            return shut
        self.s["travel"] = travel
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
        self.s["opened"] = []
        self._visit()
        return "\n".join([how] + ([] if self.quiet else [self.look()]) + self._speaks_first())

    def _shut(self, target) -> str | None:
        """Going into another interior: when every door of the run that leads there is locked and no key of one is
        held, the way is shut (go to the door to pick it, or find what opens it). A held key opens its door."""
        here = self.s["pos"]
        if not target["interior"] or (here["interior"] and here["cell"] == target["cell"]):
            return None
        doors = [d for d, to in self.world.get("doors", {}).items() if d in self.ents and to["cell"] == target["cell"]]
        if not doors or not all(self._locked(d) for d in doors):
            return None
        for d in doors:
            if self._has_key(d):
                self.s["locked"][d] = False
                return None
        return f"The way in is shut: {self._locked_text(doors[0])}"

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
        who = self.who(e)
        out = [f"{self.name(e)}, {who}."] if who else []
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
        if e not in self.s["spoken"]:           # the first conversation makes "spoken before" true
            self.s["spoken"].append(e)
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
            for test in (lambda m: m.lower() == low, lambda m: low in m.lower()):
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
        out = self._say_line(q, ln, who)
        if self.s["talking"] == who:
            out.append(self._menu_text(who))
        return "\n".join(out)

    # -- things: taking, containers, locks, theft, reading -----------------------------------------------------
    def _held_refs(self) -> list[str]:
        """The things the player holds: those taken, and a thing whose item a result gave."""
        return list(self.s["taken"]) + [k for k, e in self.ents.items() if e["kind"] == "thing" and e["item"] != k
                                        and k not in self.s["taken"] and self.s["items"].get(e["item"], 0) > 0]

    def _inside(self, h) -> list[tuple[str, str]]:
        """What a container, a person or a body holds now, as (name, key): its refs by id, its listed items as
        `<holder>|<item id>`."""
        out = [(self.name(k), k) for k, e in self.ents.items() if (e["container"] == h or e["carried_by"] == h)
               and k not in self.s["taken"] and self.s["switched"].get(k, e["enabled"])]
        out += [(self.item_name(i), f"{h}|{i}") for i, n in self.s["contents"].get(h, {}).items() if n > 0]
        return out

    def _listing(self, h) -> str:
        names = {}
        for n, k in self._inside(h):
            c = self.s["contents"][h][k.split("|", 1)[1]] if "|" in k else 1
            names[n] = names.get(n, 0) + c
        return "; ".join(n + (f" x{c}" if c > 1 else "") for n, c in names.items())

    def _has_key(self, e) -> str | None:
        k = (self.ents[e]["lock"] or {}).get("key")
        if not k:
            return None
        items = {k} | ({self.ents[k]["item"]} if k in self.ents else set())
        return k if any(self.s["items"].get(i, 0) > 0 for i in items) or k in self.s["taken"] else None

    def _locked_text(self, e) -> str:
        lk = self.ents[e]["lock"]
        out = f"{self.name(e)} is locked" + (f" ({self._lock_word(e)})." if lk else ".")
        if lk and lk["level"] == "key":
            out += " It opens only with its key."
        return out

    @staticmethod
    def _ask(verb, text, what) -> str:
        return f"{what} Say whether anyone sees you: {verb} {text} unseen, or {verb} {text} seen."

    def _owner(self, e) -> str | None:
        """Who owns a thing, as the engine has it: its owner, until a result gave it to the player."""
        return None if e in self.s["owned"] else self.ents[e]["owner"]

    def _crime(self, owner, what, choice) -> list[str]:
        self.s["crimes"].append({"what": what, "owner": owner, "seen": choice == "seen"})
        if choice == "seen":
            return [f"You are seen. {self._owner_name(owner)} or a guard confronts you: as in Skyrim, you pay a "
                    "fine or you fight. The game goes no further with it here."]
        return ["Nobody sees you."]

    def take(self, arg) -> str:
        text, choice = self._choice(arg, CHOICES)
        here = self._visible()
        pairs = [(self.name(e), e) for e in here if self.ents[e]["kind"] == "thing" and e not in self.holders]
        for h in self.s["opened"]:
            if h in self.ents and self._near(h):
                pairs += self._inside(h)
        key, err = self._find_in(text, pairs)
        if err:
            return err
        if key is None:
            e, _ = self._find(text, here + [k for k, x in self.ents.items() if x["kind"] == "thing" and k not in
                                            self.s["taken"] and not self._loose(k) and self._on(k) and self._near(k)])
            if e and e in self.holders and self.ents[e]["kind"] == "thing":
                return f"You cannot carry {self.name(e)}. Use it to open it."
            if e and self.ents[e]["carried_by"]:
                return f"{self.name(self.ents[e]['carried_by'])} carries {self.name(e)}."
            if e and self.ents[e]["container"]:
                return f"{self.name(e)} is in {self.name(self.ents[e]['container'])}: open it first."
            if e:
                return f"You cannot take {self.name(e)}."
            return f"There is no '{text}' near you."
        if "|" in key:
            holder, item = key.split("|", 1)
            name = self.item_name(item)
        else:
            holder, item = self.ents[key]["container"] or self.ents[key]["carried_by"], self.ents[key]["item"]
            name = self.name(key)
        out = []
        pocket = holder if holder and self.ents[holder]["kind"] == "person" and self._alive(holder) else None
        # as Skyrim: a thing is stolen when it, or the container it is taken from, is owned by another; a key that
        # opened the container does not change whose it is
        box = holder if holder and self.ents[holder]["kind"] == "thing" else None
        owner = pocket or (self._owner(box) if box else None) or (None if "|" in key else self._owner(key))
        if owner:
            if choice is None:
                return self._ask("take", text, f"Taking from {self.name(pocket)} is pickpocketing." if pocket
                                 else f"{name} is not yours: taking it is stealing." if box is None
                                 else f"{name} is in {self.name(box)}, which is {self._owner_name(owner)}'s: taking "
                                 "it is stealing.")
            out += self._crime(owner, f"take {name}", choice)
        if "|" in key:                      # a container's or a body's row: the whole stack
            n = self.s["contents"][holder][item]
            self.s["contents"][holder][item] = 0
        else:                               # a placed reference: its count
            n = self.ents[key]["count"]
            self.s["taken"].append(key)
        if item == GOLD:
            self.s["gold"] += n
            out.append(f"{n} gold added")
        else:
            self.s["items"][item] = self.s["items"].get(item, 0) + n
            out.append(f"Added: {name}" + (f" x{n}" if n > 1 else ""))
        return "\n".join(out + self._fire("take", item if "|" in key else key))

    def _open(self, e) -> list[str]:
        if e not in self.s["opened"]:
            self.s["opened"].append(e)
        inside = self._listing(e)
        owner = self._owner(e) if self.ents[e]["kind"] == "thing" else None
        whose = f" It is {self._owner_name(owner)}'s: what you take from it is stolen." if owner and inside else ""
        return [(f"{self.name(e)} holds: {inside}." if inside else f"{self.name(e)} is empty.") + whose]

    def use(self, arg) -> str:
        text, choice = self._choice(arg, CHOICES)
        here = self._visible()
        e, err = self._find(text, here + [k for k in self._held_refs() if k not in here])
        if err or e is None:
            return err or f"There is no '{text}' near you."
        kind = self.ents[e]["kind"]
        if kind == "person":
            if self._alive(e):
                return f"To speak with {self.name(e)}, talk to them."
            inside = self._listing(e)
            if not inside:
                return f"You search the body of {self.name(e)} and find nothing worth taking."
            self.s["opened"] = [e]
            return f"You search the body of {self.name(e)}. It carries: {inside}."
        out = []
        if self._locked(e):
            k = self._has_key(e)
            if not k:
                return self._locked_text(e)
            self.s["locked"][e] = False
            out.append(f"You unlock {self.name(e)} with {self.name(k) if k in self.ents else self.item_name(k)}.")
        if kind == "door":
            dest = self.world.get("doors", {}).get(e)
            if dest:
                self.s["pos"] = dict(dest)
                self.s["opened"] = []
                self._visit()
                out += [f"You go through {self.name(e)}."] + ([] if self.quiet else [self.look()])
            else:
                out.append(f"You open {self.name(e)}.")
        elif e in self.holders:             # opening an owned container is no crime; taking from it is
            out += self._open(e)
        elif self._text(e):
            out += [f"You read {self.name(e)}:", self._text(e)]
        else:
            out.append(f"You use {self.name(e)}.")
        out += self._fire("use", e)
        if kind == "door" and self.world.get("doors", {}).get(e):
            out += self._speaks_first()
        return "\n".join(out)

    def _fire(self, kind, ref) -> list[str]:
        """A take matches by the item taken (the form's item id), so a thing taken from a container or a pocket moves
        the trigger on its ref."""
        out = []
        same = (lambda r: self.item_of(r) == self.item_of(ref)) if kind == "take" else (lambda r: r == ref)
        # the triggers open as the event happens: a stage one of them sets does not open another for the same event
        fired = [(q, t) for q, f in self.forms.items() for t in f["triggers"]
                 if t["kind"] == kind and t.get("ref") is not None and same(t["ref"]) and self._trig_open(q, t)]
        for q, t in fired:
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
        """A death: the death triggers open now; each who-must-live row within its window shows its kind's message
        (a main or faction quest that has not ended, started or not, as the mortal watch) and fails its quest if it
        runs."""
        self.s["dead"].append(e)
        out = self._fire("death", e)
        for q, f in self.forms.items():
            for m in f["must_live"]:
                if m["ref"] != e or not self._within(q, m):
                    continue
                st = self.s["quests"].get(q)
                if m["main_message"] and f["quest"]["kind"] in MESSAGES and not (st and st["ended"]):
                    out.append(f"[Message box] {MESSAGES[f['quest']['kind']]}")
                if st is not None and not st["ended"]:
                    out += self._set_stage(q, m["fail_stage"], None)
        return out

    def pick(self, arg) -> str:
        text, choice = self._choice(arg, CHOICES)
        text, outcome = self._choice(text, ("win", "fail"))
        if outcome is None:
            return "Say how the lock goes: pick <lock> win, or pick <lock> fail."
        e, err = self._find(text, [x for x in self._visible() if self.ents[x]["kind"] in ("door", "thing")])
        if err or e is None:
            return err or "There is no such lock near you."
        if not self._locked(e):
            return f"{self.name(e)} is not locked."
        level = (self.ents[e]["lock"] or {}).get("level")
        if level == "key":
            return f"The lock of {self.name(e)} cannot be picked: it opens only with its key."
        if self.s["items"].get(LOCKPICK, 0) < 1:
            return "You have no lockpicks."
        have = self._skill("Lockpicking")
        if outcome == "win" and have < LOCK_SKILL.get(level or "novice", 0):
            return (f"The lock of {self.name(e)} ({self._lock_word(e)}) is beyond your Lockpicking ({have}): you "
                    "would only break your picks.")
        out = []
        owner = self._owner(e)
        if owner:
            if choice is None:
                return self._ask("pick", f"{text} {outcome}", f"{self.name(e)} is not yours: picking its lock is "
                                 "a crime.")
            out += self._crime(owner, f"pick {self.name(e)}", choice)
        if outcome == "fail":
            self.s["items"][LOCKPICK] -= 1
            if not self.s["items"][LOCKPICK]:
                del self.s["items"][LOCKPICK]
            return "\n".join(out + ["Your lockpick breaks; the lock holds."])
        self.s["locked"][e] = False
        out.append(f"You pick the lock of {self.name(e)}. (Lockpicking {have}.)")
        if e in self.holders:
            out += self._open(e)
        return "\n".join(out)

    def pickpocket(self, arg) -> str:
        e, err = self._find(arg, [x for x in self._visible() if self.ents[x]["kind"] == "person"])
        if err or e is None:
            return err or f"Nobody called '{arg}' is near you."
        if not self._alive(e):
            return f"{self.name(e)} is dead: search the body (use {self.name(e)})."
        inside = self._listing(e)
        if not inside:
            return f"You find nothing on {self.name(e)} worth taking."
        self.s["opened"] = [e]
        return f"{self.name(e)} carries: {inside}. Take one with: take <thing> unseen, or take <thing> seen."

    def wait(self) -> str:
        return "You wait an hour."

    def _skill(self, skill) -> int:
        k = skill.lower().replace("-", "").replace(" ", "")
        k = SKILL_ALIASES.get(k, k)
        for s, v in self.s["sheet"]["skills"].items():
            if s.lower().replace("-", "").replace(" ", "") == k:
                return v
        raise HarnessError(f"skill '{skill}' is not one of the character sheet's skills")

    # -- what the transcript keeps ---------------------------------------------------------------------------
    def summary(self) -> dict:
        return {"stages": {q: self.stage(q) for q in self.s["order"]},
                "ended": {q: self.s["quests"][q]["ended"] for q in self.s["order"] if self.s["quests"][q]["ended"]},
                "position": {"cell": self.s["pos"]["cell"], "place": self.place_name(self.s["pos"]),
                             "x": round(self.s["pos"]["x"]), "y": round(self.s["pos"]["y"])},
                "markers": [t for _, _, t in self._markers()], "talking": self.s["talking"],
                **({"travel": self.s["travel"]} if self.s.get("travel") else {})}


    def all_ended(self) -> bool:
        return bool(self.s["order"]) and all(self.s["quests"][q]["ended"] for q in self.s["order"])

    def snapshot(self) -> dict:
        return copy.deepcopy(self.s)
