"""The paper game on a quest record's YAML view (docs/design/paper-playtest.md; quest-playtest §2, moment 1).

It plays `newworld/story/quests/<line>/<code>.yaml` (or any exported record) directly, with no database. The state
is the current stage, the things held, gold, flags, the dead, the topics heard and where the player stands. A
topic's `intent` stands for its words. Every journal change is a milestone (tools/playtest/milestone.py).

What it reads of the record: `id`, `title`, `start`; `stages[]` (`id`, `place`, `journalText`, `hidden`,
`objectives[]` `objectiveText` and `target`, `successors[]` and `failForward[]` `to` and `when`, `onEnter`,
`ending`, `endingId`, `information`); `endings[]` (`id`, `world`, `rewards`); `topics[]` (`id`, `label`, `person`,
`kind`, `stages`, `when`, `intent`, `fallback`); `things[]` (`id`, `kind`, `name`, `text`); `cast[]` (`id`, `name`);
`placements[]` (`ref`, `kind`, `name`, `base`, `anchor.place`, `container`, `carriedBy`, `count`, `lock`, `enabled`,
`text`, `placeName`); `hooks[]` (`thing`, `hook` activate or read, `setsFlag`); `terms[]`; `messages[]` (`id`, `text`).
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import yaml

from tools.playtest import milestone as M
from tools.playtest.game import HarnessError

LOCKPICK = "item.lockpick"
COND_TERMS = {"all", "any", "not", "topicHeardFrom", "hasItem", "goldAtLeast", "skillAtLeast", "npcAlive",
              "questStage", "stageEverReached", "flag", "objectiveComplete", "counterAtLeast", "spellCastNear"}
ACT_TERMS = {"giveItem", "takeItem", "removeItem", "giveGold", "takeGold", "removeGold", "setFlag", "enableRef",
             "disableRef", "giveOwnership", "setStage", "killRef", "showMessage", "fadeToBlack", "showChoice",
             "endingScene", "setPlayerName", "killNpc", "raiseSkill", "grantMapMarker", "setFactionRank", "makePeace",
             "makeEnemy", "grantAbility", "giveHome", "addCounter", "setDoorAccess"}
COMMANDS = ("look", "journal", "talk", "say", "take", "use", "read", "fight", "pick", "pickpocket", "go", "answer",
            "choose", "name")
HELP = ("Commands: look, journal, talk <person>, say <topic or number> [pass|fail], take <thing>, use <thing or door>, "
        "read <thing>, fight <who> win|lose, pick <lock> win|fail, pickpocket <person> win|fail, "
        "go <place, person, thing or marker N>, choose <button label or number> (when a message box has buttons), "
        "name <your name> (when the game asks it), answer '<text>'.")


class NeedCheck(Exception):
    """A skill or gold check met with no word from the player on how it goes."""


def load(path) -> dict:
    p = Path(path)
    try:
        q = yaml.safe_load(p.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as e:
        raise HarnessError(f"{path}: not a readable record ({e})") from e
    if not isinstance(q, dict) or not q.get("id") or not q.get("stages"):
        raise HarnessError(f"{path}: not a quest record (no id or no stages)")
    return q


def humanize(pid: str) -> str:
    tail = str(pid).split(".")[-1]
    return " ".join("-".join(w.capitalize() for w in part.split("-")) for part in tail.split("_"))


def _terms(c):
    """Every (term, args) of a condition, nested ones included."""
    if isinstance(c, list):
        for x in c:
            yield from _terms(x)
    elif isinstance(c, dict):
        for k, a in c.items():
            if k in ("all", "any"):
                yield k, None
                yield from _terms(a)
            elif k == "not":
                yield k, None
                yield from _terms(a)
            else:
                yield k, a


def _args(a) -> list:
    return a if isinstance(a, list) else [a]


def _actions(v) -> list[tuple[str, list]]:
    out = []
    for a in ([v] if isinstance(v, dict) else (v or [])):
        if isinstance(a, dict) and "endingScene" in a:
            out.append(("endingScene", [a["endingScene"], a.get("messages") or [], a.get("before") or []]))
            out += [(k, _args(x)) for k, x in a.items() if k not in ("endingScene", "messages", "before")]
        elif isinstance(a, dict):
            for k, x in a.items():
                out.append((k, _args(x)))
    return out


class Record:
    """The record read once: its stages, topics, things, people and places by id."""

    def __init__(self, q: dict):
        self.q = q
        self.id = q["id"]
        self.title = q.get("title") or q["id"]
        self.stages = {s["id"]: s for s in q.get("stages") or [] if isinstance(s, dict) and "id" in s}
        self.topics = [t for t in q.get("topics") or [] if isinstance(t, dict)]
        self.topic = {t.get("id"): t for t in self.topics}
        self.things = {t["id"]: t for t in q.get("things") or [] if isinstance(t, dict) and "id" in t}
        self.cast = {c["id"]: c for c in q.get("cast") or [] if isinstance(c, dict) and "id" in c}
        self.rows = {p["ref"]: p for p in q.get("placements") or [] if isinstance(p, dict) and "ref" in p}
        self.endings = {e["id"]: e for e in q.get("endings") or [] if isinstance(e, dict) and "id" in e}
        self.hooks = [h for h in q.get("hooks") or [] if isinstance(h, dict)]
        self.terms = [t for t in q.get("terms") or [] if isinstance(t, dict)]
        self.messages = {m["id"]: m.get("text") for m in q.get("messages") or [] if isinstance(m, dict) and "id" in m}
        names = {}
        for r in self.rows.values():
            pl = (r.get("anchor") or {}).get("place")
            if pl and r.get("placeName") and r.get("kind") != "door":
                names.setdefault(pl, r["placeName"])
        self.place_names = names

    @property
    def start(self):
        s = self.q.get("start")
        return s if s in self.stages else min(self.stages) if s is None else s

    def kind(self, ref) -> str | None:
        if ref in self.rows:
            return self.rows[ref].get("kind")
        if ref in self.cast:
            return "person"
        if ref in self.things:
            return "container" if self.things[ref].get("kind") == "container" else "thing"
        return None

    def item_id(self, ref) -> str:
        """What the player holds for a ref: a stock item's id (five lockpicks are `item.lockpick`), else the ref."""
        base = (self.rows.get(ref) or {}).get("base") or {}
        return base["id"] if base.get("kind") == "item" and str(base.get("id", "")).startswith("item.") else ref

    def name(self, ref) -> str | None:
        r = self.rows.get(ref) or {}
        if r.get("kind") == "door":
            to = r.get("name") or (f"Door to {r['placeName']}" if r.get("placeName") else None)
            return to
        for src in (r, self.things.get(ref) or {}, self.cast.get(ref) or {}):
            if src.get("name"):
                return src["name"]
        iid = self.item_id(ref)
        if str(iid).startswith("item.") and iid != ref or str(ref).startswith("item."):
            return humanize(iid)
        return None

    def must_name(self, ref) -> str:
        n = self.name(ref)
        if not n:
            raise HarnessError(f"{ref} has no name the game could show: give it a `name` in its placement, thing or "
                               "cast row")
        return n

    def place_name(self, pid) -> str:
        return self.place_names.get(pid) or (pid if not str(pid).startswith(("place.",)) and " " in str(pid)
                                             else humanize(pid))

    def text(self, ref) -> str | None:
        return (self.rows.get(ref) or {}).get("text") or (self.things.get(ref) or {}).get("text")

    def home(self, ref):
        """The place a placement stands at to begin with (None: wherever the player is)."""
        r = self.rows.get(ref) or {}
        return (r.get("anchor") or {}).get("place") or (r.get("at") or {}).get("place")

    def door_to(self, ref):
        to = (self.rows.get(ref) or {}).get("placeName")
        if not to:
            return None
        for pid in self.places():
            if self.place_name(pid) == to:
                return pid
        return to

    def places(self) -> list:
        out = []
        for s in self.stages.values():
            if s.get("place"):
                out.append(s["place"])
        for ref in self.rows:
            if self.home(ref):
                out.append(self.home(ref))
        return list(dict.fromkeys(out))

    def path_topics(self) -> set:
        """Topics on the path: those a successor or fail-forward names, and greetings and force-greets."""
        out = {t["id"] for t in self.topics if t.get("kind") in ("greeting", "speaks-first")}
        for s in self.stages.values():
            for sc in (s.get("successors") or []) + (s.get("failForward") or []):
                for k, a in _terms(sc.get("when")):
                    if k == "topicHeardFrom":
                        out.add(_args(a)[0])
        return out

    def known(self, ref) -> bool:
        return ref in self.rows or ref in self.things or ref in self.cast or str(ref).startswith("item.")

    def label(self, ref) -> str:
        """A name for a person, place, faction or rank: the record's name, else the id capitalised."""
        if isinstance(ref, int):
            return str(ref)
        n = self.name(ref)
        if n:
            return n
        for t in self.terms:
            if t.get("term") and str(t["term"]).lower() == str(ref).lower():
                return str(t["term"])
        if ref in self.places():
            return self.place_name(ref)
        return humanize(ref)

    def message(self, ref) -> str:
        return self.messages.get(ref) or str(ref)


# -- the check: a record the game can play -------------------------------------------------------------------------
def check(q: dict) -> list[str]:
    """Every fault that would stop or mislead the game, one line each."""
    R = Record(q)
    bad = []
    if q.get("start") is not None and q["start"] not in R.stages:
        bad.append(f"start: stage {q['start']} is not a stage of the record")
    for sid, s in R.stages.items():
        where = f"stage {sid}"
        for kind in ("successors", "failForward"):
            for sc in s.get(kind) or []:
                if sc.get("to") not in R.stages:
                    bad.append(f"{where} {kind}: stage {sc.get('to')} is not a stage of the record")
                bad += _cond_faults(R, sc.get("when"), f"{where} {kind} to {sc.get('to')}")
        for o in s.get("objectives") or []:
            if not o.get("objectiveText"):
                bad.append(f"{where} objective {o.get('id')}: no objectiveText")
            for t in [x.strip() for x in str(o.get("target") or "").split(",") if x.strip()]:
                if not R.known(t):
                    bad.append(f"{where} objective {o.get('id')}: target {t} is not a placement, thing or cast row")
            if not o.get("target"):
                bad.append(f"{where} objective {o.get('id')}: no target for the marker")
        if s.get("ending") and s.get("endingId") and s["endingId"] not in R.endings:
            bad.append(f"{where}: endingId {s['endingId']} is not an endings row")
        bad += _act_faults(R, s.get("onEnter"), f"{where} onEnter")
        if not s.get("hidden"):
            if not s.get("journalText"):
                bad.append(f"{where}: a shown stage with no journalText")
            info = s.get("information")
            if not isinstance(info, dict):
                bad.append(f"{where}: a shown stage with no information (going, next, ways)")
            else:
                for k in ("going", "next", "ways"):
                    if not info.get(k) and not (k in ("next", "ways") and s.get("ending")):
                        bad.append(f"{where} information: no {k}")
                bad += _carrier_faults(R, sid, info.get("carriers") or [])
    for e in R.endings.values():
        bad += _act_faults(R, e.get("world"), f"ending {e['id']} world")
        bad += _act_faults(R, e.get("rewards"), f"ending {e['id']} rewards")
    for t in R.topics:
        where = f"topic {t.get('id')}"
        if not t.get("person") or not R.known(t["person"]):
            bad.append(f"{where}: person {t.get('person')} is not a placement or cast row")
        elif not R.name(t["person"]) and t["person"] not in R.rows:
            bad.append(f"{where}: person {t['person']} has no name")
        if not t.get("label") and t.get("kind") not in ("greeting", "speaks-first"):
            bad.append(f"{where}: no label (the prompt the player picks)")
        if not t.get("intent"):
            bad.append(f"{where}: no intent (what the person says until the lines are written)")
        for n in t.get("stages") or []:
            if n not in R.stages:
                bad.append(f"{where}: stage {n} is not a stage of the record")
        bad += _cond_faults(R, t.get("when"), f"{where} when")
    for h in R.hooks:
        if h.get("thing") not in R.rows and h.get("thing") not in R.things:
            bad.append(f"hook: thing {h.get('thing')} is not a placement or thing row")
        if h.get("hook") not in ("activate", "read"):
            bad.append(f"hook on {h.get('thing')}: hook is activate or read, not {h.get('hook')!r}")
        if not h.get("setsFlag"):
            bad.append(f"hook on {h.get('thing')}: no setsFlag")
    for ref, r in R.rows.items():
        if r.get("kind") in ("person", "thing", "door", "container") and not R.name(ref):
            what = "placeName (the place it leads to)" if r.get("kind") == "door" else "name"
            bad.append(f"placement {ref}: a {r.get('kind')} the player can see with no {what}")
        for k in ("container", "carriedBy"):
            if r.get(k) and r[k] not in R.rows:
                bad.append(f"placement {ref}: {k} {r[k]} is not a placement")
    for tid, t in R.things.items():
        if tid not in R.rows and not t.get("name") and t.get("kind") != "container":
            bad.append(f"thing {tid}: no name the game could show")
    for t in R.terms:
        if t.get("ask") and t["ask"] not in R.topic:
            bad.append(f"term {t.get('term')}: ask {t['ask']} is not a topic of the record")
    return bad


def _cond_faults(R, c, where) -> list[str]:
    bad = []
    for k, a in _terms(c):
        if k not in COND_TERMS:
            bad.append(f"{where}: condition term {k} is not one the paper game plays")
            continue
        args = _args(a) if a is not None else []
        if k == "topicHeardFrom":
            if args[0] not in R.topic:
                bad.append(f"{where}: topicHeardFrom {args[0]} is not a topic of the record")
            elif len(args) > 1 and R.topic[args[0]].get("person") != args[1]:
                bad.append(f"{where}: topicHeardFrom {args[0]} from {args[1]}, but the topic is "
                           f"{R.topic[args[0]].get('person')}'s")
        if k in ("hasItem", "npcAlive") and args and not R.known(args[0]):
            bad.append(f"{where}: {k} {args[0]} is not a placement, thing or cast row")
    return bad


def _act_faults(R, v, where) -> list[str]:
    bad = []
    for k, args in _actions(v):
        if k not in ACT_TERMS:
            bad.append(f"{where}: action term {k} is not one the paper game plays")
            continue
        if k == "showMessage" and args and isinstance(args[0], str) and args[0] not in R.messages \
                and re.fullmatch(r"[\w.-]+", args[0]):
            bad.append(f"{where}: showMessage {args[0]} is neither a row of messages nor a text")
        if k == "showChoice":
            c = args[0] if args and isinstance(args[0], dict) else {}
            if not c.get("text") or not c.get("buttons"):
                bad.append(f"{where}: showChoice needs a text and buttons")
            for b in c.get("buttons") or []:
                if not isinstance(b, dict) or not b.get("label"):
                    bad.append(f"{where}: showChoice button with no label")
                elif b.get("sets") not in R.stages:
                    bad.append(f"{where}: showChoice button {b['label']!r} sets stage {b.get('sets')}, which is not "
                               "a stage of the record")
        if k == "endingScene":
            if not args[1]:
                bad.append(f"{where}: endingScene {args[0]} has no messages")
            bad += _act_faults(R, args[2], f"{where} endingScene {args[0]} before")
        if k in ("killNpc", "setDoorAccess") and args and not R.known(args[0]):
            bad.append(f"{where}: {k} {args[0]} is not a placement or cast row")
        if k in ("grantMapMarker", "giveHome") and args and not R.known(args[0]) and args[0] not in R.places():
            bad.append(f"{where}: {k} {args[0]} is not a placement or a place of the record")
        if k == "setDoorAccess" and (len(args) < 2 or args[1] not in ("open", "locked")):
            bad.append(f"{where}: setDoorAccess takes [door, open|locked]")
        if k in ("raiseSkill", "setFactionRank", "grantAbility", "addCounter") and len(args) < 2:
            bad.append(f"{where}: {k} takes two values")
        if k in ("giveItem", "takeItem", "removeItem", "enableRef", "disableRef", "giveOwnership") and args \
                and not R.known(args[0]):
            bad.append(f"{where}: {k} {args[0]} is not a placement or thing row")
        if k in ("giveItem",) and args and R.known(args[0]) and not R.name(args[0]):
            bad.append(f"{where}: giveItem {args[0]} has no name the game could show")
    return bad


def _carrier_faults(R, sid, carriers) -> list[str]:
    bad = []
    path = R.path_topics()
    for c in carriers:
        by = _args(c.get("by") or [])
        what = f"stage {sid} carrier '{str(c.get('know', ''))[:40]}'"
        if not by or all(str(b).startswith("ask:") for b in by):
            bad.append(f"{what}: no channel other than ask:")
        for b in map(str, by):
            ch, _, ref = b.partition(":")
            if ch in ("line", "ask") and ref not in R.topic:
                bad.append(f"{what}: {b} is not a topic of the record")
            elif ch == "line" and ref not in path:
                bad.append(f"{what}: {b} is not on the path (no successor names it, and it is no greeting): use ask:")
            elif ch in ("marker", "name", "read", "look") and not R.known(ref):
                bad.append(f"{what}: {b} is not a placement or thing row")
            elif ch == "message" and not (ref.isdigit() and int(ref) in R.stages):
                bad.append(f"{what}: {b} is not a stage")
            elif ch not in ("journal", "objective", "line", "ask", "marker", "name", "read", "look", "message"):
                bad.append(f"{what}: {b} is not a channel")
    return bad


# -- the game ----------------------------------------------------------------------------------------------------
class Game:
    def __init__(self, q: dict, state: dict | None = None):
        self.R = Record(q)
        self.s = state if state is not None else self._fresh()
        for k, v in self._fresh().items():
            self.s.setdefault(k, v)
        self.word = None          # pass or fail, said with the command, for a skill or gold check

    def _fresh(self) -> dict:
        return {"stage": None, "done": [], "items": {}, "gold": 0, "flags": {}, "dead": [], "heard": [],
                "at": None, "taken": [], "enabled": {}, "unlocked": [], "opened": [], "talking": None, "menu": [],
                "ended": None, "pending": [], "want_notes": False, "over": False, "milestones": [], "commands": 0,
                "choice": None, "ask_name": False, "name": None, "counters": {}, "doors": {}, "skills": {},
                "ranks": {}, "peace": {}, "spells": [], "scenes": []}

    # -- state reads
    def stage(self) -> dict:
        return self.R.stages[self.s["stage"]]

    def _enabled(self, ref) -> bool:
        if ref in self.s["enabled"]:
            return self.s["enabled"][ref]
        return (self.R.rows.get(ref) or {}).get("enabled", True) is not False

    def where(self, ref):
        """The place a ref is at now, or None (wherever the player is)."""
        r = self.R.rows.get(ref) or {}
        if r.get("container"):
            return self.where(r["container"])
        if r.get("carriedBy"):
            return self.where(r["carriedBy"])
        return self.R.home(ref)

    def _here(self, ref) -> bool:
        w = self.where(ref)
        return w is None or w == self.s["at"]

    def _alive(self, ref) -> bool:
        return ref not in self.s["dead"]

    def _locked(self, ref) -> bool:
        if self.s["doors"].get(ref) == "locked":
            return ref not in self.s["unlocked"]
        if self.s["doors"].get(ref) == "open":
            return False
        lock = (self.R.rows.get(ref) or {}).get("lock")
        return bool(lock) and ref not in self.s["unlocked"]

    def visible(self) -> list[str]:
        out = []
        for ref, r in self.R.rows.items():
            if r.get("kind") == "marker" or not self._enabled(ref) or ref in self.s["taken"]:
                continue
            if r.get("container") or r.get("carriedBy"):
                continue
            if self._here(ref):
                out.append(ref)
        return out

    def loose(self) -> list[str]:
        """Things the player can take here: on the ground, in an opened container, on a body."""
        out = []
        for ref, r in self.R.rows.items():
            if ref in self.s["taken"] or not self._enabled(ref) or r.get("kind") not in ("thing", None):
                continue
            c, by = r.get("container"), r.get("carriedBy")
            if c:
                if c in self.s["opened"] and self._here(c) and c not in self.s["taken"]:
                    out.append(ref)
            elif by:
                if not self._alive(by) and self._here(by):
                    out.append(ref)
            elif self._here(ref):
                out.append(ref)
        return out

    def markers(self) -> list[str]:
        if self.s["ended"] or self.s["stage"] is None or self.stage().get("hidden"):
            return []
        out = []
        for o in self.stage().get("objectives") or []:
            for t in str(o.get("target") or "").split(","):
                t = t.strip()
                if t and t not in out and (t not in self.s["dead"]) and t not in self.s["taken"] \
                        and self.R.item_id(t) not in self.s["items"]:
                    out.append(t)
        return out

    # -- conditions
    def holds(self, c, lenient=False) -> bool:
        if c is None or c == [] or c == {}:
            return True
        if isinstance(c, list):
            return all(self.holds(x, lenient) for x in c)
        if not isinstance(c, dict):
            raise HarnessError(f"{c!r} is not a condition")
        if len(c) > 1:
            return all(self.holds({k: v}, lenient) for k, v in c.items())
        k, a = next(iter(c.items()))
        args = _args(a)
        s = self.s
        if k == "all":
            return all(self.holds(x, lenient) for x in a)
        if k == "any":
            return any(self.holds(x, lenient) for x in a)
        if k == "not":
            return not self.holds(a, lenient)
        if k == "topicHeardFrom":
            return any(h[0] == args[0] and (len(args) < 2 or h[1] == args[1]) for h in s["heard"])
        if k == "hasItem":
            return s["items"].get(args[0], 0) >= (args[1] if len(args) > 1 else 1)
        if k == "counterAtLeast":
            return s["counters"].get(args[0], 0) >= args[1]
        if k in ("goldAtLeast", "skillAtLeast", "spellCastNear"):
            if lenient:
                return True
            if self.word is None:
                raise NeedCheck(f"{args[0]} {args[1]}" if k == "skillAtLeast" else f"{args[0]} gold"
                                if k == "goldAtLeast" else
                                f"({humanize(args[0])}) a spell cast near {self.R.label(args[1])}")
            return self.word == "pass"
        if k == "npcAlive":
            return self._alive(args[0])
        if k == "questStage":
            if args[0] != self.R.id:
                return False
            op, n = (args[1], args[2]) if len(args) > 2 else ("=", args[1])
            cur = s["stage"] if s["stage"] is not None else -1
            return {"≥": cur >= n, ">=": cur >= n, "=": cur == n, "==": cur == n, ">": cur > n, "<": cur < n,
                    "≤": cur <= n, "<=": cur <= n}.get(op, False)
        if k == "stageEverReached":
            return args[0] == self.R.id and args[1] in s["done"]
        if k == "flag":
            want = args[1] if len(args) > 1 else True
            return s["flags"].get(args[0], False) == want
        if k == "objectiveComplete":
            return any(o.get("id") == args[0] for sid in s["done"] if sid != s["stage"]
                       for o in self.R.stages[sid].get("objectives") or [])
        raise HarnessError(f"condition term {k} is not one the paper game plays")

    # -- actions and stages
    def apply(self, acts) -> list[str]:
        out = []
        for k, a in _actions(acts):
            if k == "giveItem":
                iid = self.R.item_id(a[0])
                self.s["items"][iid] = self.s["items"].get(iid, 0) + (a[1] if len(a) > 1 else 1)
                out.append(f"Added: {self.R.must_name(a[0])}")
            elif k in ("takeItem", "removeItem"):
                iid = self.R.item_id(a[0])
                n = self.s["items"].get(iid, 0) - (a[1] if len(a) > 1 else 1)
                self.s["items"].pop(iid, None) if n <= 0 else self.s["items"].__setitem__(iid, n)
                out.append(f"Removed: {self.R.name(a[0]) or a[0]}")
            elif k == "giveGold":
                self.s["gold"] += a[0]
                out.append(f"{a[0]} gold added")
            elif k in ("takeGold", "removeGold"):
                self.s["gold"] = max(0, self.s["gold"] - a[0])
                out.append(f"{a[0]} gold removed")
            elif k == "setFlag":
                self.s["flags"][a[0]] = a[1] if len(a) > 1 else True
            elif k in ("enableRef", "disableRef"):
                self.s["enabled"][a[0]] = k == "enableRef"
            elif k == "giveOwnership":
                pass
            elif k == "showMessage":
                out.append(self._box(self.R.message(a[0])))
            elif k == "fadeToBlack":
                out.append("The screen goes black.")
            elif k == "showChoice":
                c = a[0]
                self.s["choice"] = {"text": c.get("text"), "buttons": [
                    {"label": b.get("label"), "sets": b.get("sets")} for b in c.get("buttons") or []]}
                out.append(self._prompt())
            elif k == "endingScene":
                self.apply(a[2])
                self.s["scenes"].append(a[0])
                out.append("The screen fades to black.")
                out += [self._box(self.R.message(m)) for m in a[1]]
            elif k == "setPlayerName":
                self.s["ask_name"] = True
                out.append(self._prompt())
            elif k == "killNpc":
                if a[0] not in self.s["dead"]:
                    self.s["dead"].append(a[0])
                    out.append(f"{self.R.label(a[0])} is dead.")
            elif k == "raiseSkill":
                n = a[1]
                self.s["skills"][a[0]] = self.s["skills"].get(a[0], 0) + n
                out.append(f"{str(a[0])[:1].upper() + str(a[0])[1:]} increased by {n}.")
            elif k == "grantMapMarker":
                out.append(f"Map marker added: {self.R.label(a[0])}")
            elif k == "setFactionRank":
                self.s["ranks"][a[0]] = a[1]
                out.append(f"You are now {self.R.label(a[1])} of {self.R.label(a[0])}")
            elif k in ("makePeace", "makeEnemy"):
                self.s["peace"][a[0]] = k == "makePeace"
                out.append(f"{self.R.label(a[0])} is now {'friendly' if k == 'makePeace' else 'hostile'} to you")
            elif k == "grantAbility":
                if a[0] not in self.s["spells"]:
                    self.s["spells"].append(a[0])
                out.append(f"Spell learned: {a[1]}")
            elif k == "giveHome":
                out.append(f"{self.R.label(a[0])} is now yours.")
            elif k == "addCounter":
                self.s["counters"][a[0]] = self.s["counters"].get(a[0], 0) + a[1]
            elif k == "setDoorAccess":
                self.s["doors"][a[0]] = a[1]
            elif k == "setStage":
                if a[0] == self.R.id:
                    out += self.enter(a[1])
            elif k == "killRef":
                self.s["dead"].append(a[0])
        return out

    def enter(self, n) -> list[str]:
        if n not in self.R.stages:
            raise HarnessError(f"stage {n} is not a stage of the record")
        if n in self.s["done"] or self.s["ended"]:
            return []
        first = not any(not self.R.stages[d].get("hidden") for d in self.s["done"])
        st = self.R.stages[n]
        self.s["stage"] = n
        self.s["done"].append(n)
        out = self.apply(st.get("onEnter"))
        if st.get("ending"):
            e = self.R.endings.get(st.get("endingId")) or {}
            out += self.apply(e.get("world")) + self.apply(e.get("rewards"))
            self.s["ended"] = st["ending"]
        if not st.get("hidden"):
            objs = []
            if not st.get("ending"):
                for o in st.get("objectives") or []:
                    names = [self.R.must_name(t.strip()) for t in str(o.get("target") or "").split(",") if t.strip()]
                    objs.append(f"{o.get('objectiveText')}" + (f" (marker: {', '.join(names)})" if names else ""))
            kind = "ending" if st.get("ending") else "start" if first else "stage"
            self.s["pending"].append({"stage": n, "kind": kind, "ending": st.get("ending"), "title": self.R.title,
                                      "journal": st.get("journalText") or "", "objectives": objs,
                                      "plan": M.plan_of(st, self.R.terms)})
        return out

    def advance(self) -> list[str]:
        out = []
        for _ in range(100):
            if self.s["ended"] or self.s["stage"] is None:
                return out
            st = self.stage()
            for sc in (st.get("successors") or []) + (st.get("failForward") or []):
                if self.holds(sc.get("when")):
                    out += self.enter(sc["to"])
                    break
            else:
                return out
        raise HarnessError("the stages move in a loop")

    def begin(self, at=None) -> str:
        self.s["stage"] = None
        first = self.R.start
        st0 = self.R.stages.get(first)
        if st0 is None:
            raise HarnessError(f"start stage {first} is not a stage of the record")
        self.s["at"] = at or st0.get("place") or (self.R.places() or [None])[0]
        out = self.enter(first) + self.advance()
        return "\n".join(["A new game."] + out + ["", self.c_look()] + self._speaks_first() + self._gate())

    # -- message boxes the player must answer
    @staticmethod
    def _box(text) -> str:
        return "[Message box]\n" + "\n".join("  " + ln for ln in str(text).splitlines())

    def _prompt(self) -> str:
        c = self.s["choice"]
        if c:
            return "\n".join([self._box(c["text"])] + [f"  {i}. [{b['label']}]" for i, b in enumerate(c["buttons"], 1)]
                              + ["Pick a button: choose <label or number>"])
        if self.s["ask_name"]:
            return self._box("What is your name?") + "\nTell the game: name <your name>"
        return ""

    def _blocked(self) -> str | None:
        if self.s["choice"]:
            return "A message box is open. Pick one of its buttons first.\n" + self._prompt()
        if self.s["ask_name"]:
            return "The game is waiting for your name.\n" + self._prompt()
        return None

    def c_choose(self, arg) -> str:
        c = self.s["choice"]
        if not c:
            return "There is no message box with buttons open."
        a = arg.lower().strip().strip("'\"")
        bs = c["buttons"]
        b = bs[int(a) - 1] if a.isdigit() and 0 < int(a) <= len(bs) else \
            next((x for x in bs if x["label"].lower() == a), None) or \
            next((x for x in bs if a and a in x["label"].lower()), None)
        if b is None:
            return "That is not one of the buttons.\n" + self._prompt()
        self.s["choice"] = None
        return "\n".join([f"You press [{b['label']}]."] + self.enter(b["sets"]))

    def c_name(self, arg) -> str:
        if not self.s["ask_name"]:
            return "Nobody is asking your name."
        if not arg.strip():
            return "Give a name: name <your name>"
        self.s["name"] = arg.strip().strip("'\"")
        self.s["ask_name"] = False
        return f"You are {self.s['name']}."

    # -- the milestone gate
    def _gate(self) -> list[str]:
        if self.s["pending"]:
            return ["", M.ask(self.s["pending"][0])]
        return []

    def answer(self, text: str) -> str:
        if not text.strip():
            return "Answer in words: answer '...'"
        if self.s["pending"]:
            m = self.s["pending"].pop(0)
            m["answers"] = M.split_answers(text)
            m["raw"] = text
            self.s["milestones"].append(m)
            if self.s["pending"]:
                return "Noted.\n\n" + M.ask(self.s["pending"][0])
            if self.s["ended"]:
                self.s["want_notes"] = True
                return "Noted.\n\n" + M.NOTES_ASK
            return "\n".join(["Noted. The game goes on."] + ([self._prompt()] if self._blocked() else []))
        if self.s["want_notes"]:
            self.s["notes"] = text.strip()
            self.s["want_notes"] = False
            self.s["over"] = True
            return "Thank you. Your notes are kept; the game is over. You can stop now."
        return "There is nothing to answer just now."

    # -- commands
    def do(self, command: str) -> str:
        if self.s["over"]:
            return "The game is over."
        words = command.strip().split()
        if not words:
            return HELP
        verb, arg = words[0].lower(), command.strip()[len(words[0]):].strip()
        if verb == "answer":
            return self.answer(arg.strip("'\""))
        if self.s["pending"]:
            return M.refusal()
        if self.s["want_notes"]:
            return M.NOTES_ASK
        if self._blocked() and verb not in ("choose", "name"):
            return self._blocked()
        if verb not in COMMANDS:
            return f"'{verb}' is not something you can do here. {HELP}"
        self.s["commands"] += 1
        self.word = None
        m = re.search(r"\s+(pass|fail)$", arg, re.I)
        if m and verb in ("say", "take", "use", "read", "talk"):
            self.word, arg = m.group(1).lower(), arg[:m.start()]
        before = copy.deepcopy(self.s)
        if verb not in ("say", "journal", "choose", "name"):
            self.s["talking"] = None
        try:
            out = getattr(self, "c_" + verb)(arg)
            out = "\n".join([out] + self.advance()) if out else "\n".join(self.advance())
        except NeedCheck as e:
            self.s = before
            return (f"That needs a check ({e}). Say how it goes by adding pass or fail at the end: "
                    f"{verb} {arg} pass, or {verb} {arg} fail.")
        return "\n".join([out] + self._gate())

    def _find(self, text, pool) -> str | None:
        t = text.lower().strip().strip("'\"")
        if not t:
            return None
        named = [(r, (self.R.name(r) or "").lower()) for r in pool]
        for r, n in named:
            if n == t:
                return r
        for r, n in named:
            if n and (t in n or n.startswith(t)):
                return r
        return None

    def c_look(self, _arg="") -> str:
        here = self.visible()
        mk = set(self.markers())
        tag = lambda r: " (quest marker)" if r in mk else ""   # noqa: E731
        people = [r for r in here if self.R.kind(r) == "person"]
        things = [r for r in here if self.R.kind(r) in ("thing", "container")]
        doors = [r for r in here if self.R.kind(r) == "door"]
        who = f"You are {self.s['name']}, at" if self.s["name"] else "You are at"
        out = [f"{who} {self.R.place_name(self.s['at'])}."]
        if people:
            out.append("People: " + "; ".join(
                (self.R.must_name(r) if self._alive(r) else f"the body of {self.R.must_name(r)}") + tag(r)
                for r in people))
        if things:
            out.append("Things: " + "; ".join(self.R.must_name(r) + (" (locked)" if self._locked(r) else "") + tag(r)
                                              for r in things))
        if doors:
            state = lambda r: " (locked)" if self._locked(r) else \
                " (open)" if self.s["doors"].get(r) == "open" else ""   # noqa: E731
            out.append("Doors: " + "; ".join(self.R.must_name(r) + state(r) + tag(r)
                                             for r in doors))
        off = [r for r in mk if r not in here and self.where(r) and self.where(r) != self.s["at"]]
        for r in off:
            out.append(f"A quest marker points to {self.R.must_name(r)}, at {self.R.place_name(self.where(r))}.")
        if not (people or things or doors):
            out.append("Nobody and nothing of note is here.")
        return "\n".join(out)

    def c_journal(self, _arg="") -> str:
        entries = [self.R.stages[d].get("journalText") for d in self.s["done"]
                   if not self.R.stages[d].get("hidden") and self.R.stages[d].get("journalText")]
        if not entries:
            return "Your journal is empty."
        out = [f"{self.R.title}" + (f" ({self.s['ended']})" if self.s["ended"] else "")]
        out += [f"- {e}" for e in entries]
        if not self.s["ended"]:
            for o in self.stage().get("objectives") or []:
                out.append(f"Objective: {o.get('objectiveText')}")
            for i, r in enumerate(self.markers(), 1):
                w = self.where(r)
                out.append(f"Marker {i}: {self.R.must_name(r)}" + (f", at {self.R.place_name(w)}" if w else ""))
        out.append("You carry: " + (", ".join(f"{self._iname(i)}" + (f" x{n}" if n > 1 else "")
                                               for i, n in self.s["items"].items()) or "nothing")
                   + f"; {self.s['gold']} gold.")
        return "\n".join(out)

    def _iname(self, iid) -> str:
        if iid in self.R.rows or iid in self.R.things:
            return self.R.must_name(iid)
        return humanize(iid)

    def _open_topics(self, who) -> list[dict]:
        out = []
        for t in self.R.topics:
            if t.get("person") != who or t.get("kind") in ("greeting",):
                continue
            if t.get("stages") and self.s["stage"] not in t["stages"]:
                continue
            if self.s["ended"] and not t.get("stages"):
                pass
            if self.holds(t.get("when"), lenient=True):
                out.append(t)
        return out

    def c_talk(self, arg) -> str:
        who = self._find(arg, [r for r in self.visible() if self.R.kind(r) == "person"])
        if who is None:
            return f"There is nobody called '{arg}' here."
        if not self._alive(who):
            return f"{self.R.must_name(who)} is dead."
        self.s["talking"] = who
        out = []
        for t in self.R.topics:
            if t.get("person") == who and t.get("kind") == "greeting" and \
                    (not t.get("stages") or self.s["stage"] in t["stages"]) and self.holds(t.get("when"), True):
                out += self._said(t)
                break
        else:
            out.append(f"{self.R.must_name(who)} turns to you.")
        out.append(self._menu(who))
        return "\n".join(out)

    def _menu(self, who) -> str:
        ts = self._open_topics(who)
        self.s["menu"] = [t["id"] for t in ts]
        if not ts:
            return f"{self.R.must_name(who)} has nothing more to say to you just now."
        return "Topics you can pick:\n" + "\n".join(f"{i}. {t.get('label') or t['id']}" for i, t in enumerate(ts, 1))

    def _said(self, t) -> list[str]:
        """The topic said: its gate checked, its successors tried; its intent, or its fallback when a check fails."""
        who = t["person"]
        if not self.holds(t.get("when")):
            return [f"{self.R.must_name(who)}: {t.get('fallback') or 'They will not talk about that now.'}"]
        key = [t["id"], who]
        if key not in self.s["heard"]:
            self.s["heard"].append(key)
        cands = [sc for sc in (self.stage().get("successors") or []) if not self.s["ended"]
                 and any(k == "topicHeardFrom" and _args(a)[0] == t["id"] for k, a in _terms(sc.get("when")))]
        if cands and t.get("fallback") and not any(self.holds(sc.get("when")) for sc in cands):
            self.s["heard"].remove(key)
            return [f"{self.R.must_name(who)}: {t['fallback']}"]
        return [f"{self.R.must_name(who)}: {t.get('intent')}"]

    def c_say(self, arg) -> str:
        who = self.s["talking"]
        if who is None:
            return "You are not talking to anyone: talk <person> first."
        ts = self._open_topics(who)
        t = None
        if arg.strip().isdigit():
            ids = self.s["menu"]
            i = int(arg) - 1
            if 0 <= i < len(ids):
                t = self.R.topic.get(ids[i])
        else:
            a = arg.lower().strip().strip("'\"")
            t = next((x for x in ts if (x.get("label") or "").lower() == a), None) or \
                next((x for x in ts if a and a in (x.get("label") or "").lower()), None)
        if t is None or t not in ts:
            return f"That is not a topic {self.R.must_name(who)} will take up now.\n" + self._menu(who)
        out = self._said(t) + self.advance()
        out.append(self._menu(who) if not self.s["pending"] else "")
        return "\n".join(x for x in out if x)

    def c_take(self, arg) -> str:
        r = self._find(arg, self.loose())
        if r is None:
            inside = self._find(arg, [x for x, row in self.R.rows.items() if row.get("container")
                                      and self._here(x) and x not in self.s["taken"] and self._enabled(x)])
            if inside:
                return f"{self.R.must_name(inside)} is in {self.R.must_name(self.R.rows[inside]['container'])}: " \
                       "open it first (use it)."
            if self._find(arg, [x for x in self.visible() if self.R.kind(x) in ("person", "door", "container")]):
                return "You cannot carry that."
            return f"There is no '{arg}' here you can take."
        self.s["taken"].append(r)
        iid = self.R.item_id(r)
        n = (self.R.rows.get(r) or {}).get("count") or 1
        self.s["items"][iid] = self.s["items"].get(iid, 0) + n
        return f"Added: {self.R.must_name(r)}" + (f" x{n}" if n > 1 else "")

    def _hook(self, r, how) -> list[str]:
        for h in self.R.hooks:
            if h.get("thing") == r and h.get("hook") == how:
                self.s["flags"][h["setsFlag"]] = True
        return []

    def c_use(self, arg) -> str:
        held = [x for x in list(self.R.rows) + list(self.R.things) if self.R.item_id(x) in self.s["items"]]
        r = self._find(arg, self.visible() + held)
        if r is None:
            return f"There is no '{arg}' here."
        k = self.R.kind(r)
        lock = (self.R.rows.get(r) or {}).get("lock") or {}
        if self._locked(r):
            key = lock.get("key")
            if key and self.R.item_id(key) in self.s["items"]:
                self.s["unlocked"].append(r)
                pre = [f"You unlock {self.R.must_name(r)} with {self.R.must_name(key)}."]
            else:
                lvl = lock.get("level") or "key"
                return f"{self.R.must_name(r)} is locked ({lvl}). Pick it (pick <lock> win|fail) or find its key."
        else:
            pre = []
        if k == "door":
            to = self.R.door_to(r)
            if not to:
                raise HarnessError(f"door {r} leads nowhere: give it a placeName")
            self.s["at"] = to
            self._hook(r, "activate")
            return "\n".join(pre + [f"You go through {self.R.must_name(r)}.", "", self.c_look()] + self._speaks_first())
        contents = [x for x, row in self.R.rows.items() if row.get("container") == r and x not in self.s["taken"]
                    and self._enabled(x)]
        self._hook(r, "activate")
        if contents or k == "container" or any(row.get("container") == r for row in self.R.rows.values()):
            if r not in self.s["opened"]:
                self.s["opened"].append(r)
            return "\n".join(pre + [f"{self.R.must_name(r)} holds: " +
                                    ("; ".join(self.R.must_name(x) for x in contents) or "nothing")])
        return "\n".join(pre + [f"You use {self.R.must_name(r)}."])

    def c_read(self, arg) -> str:
        held = [x for x in list(self.R.rows) + list(self.R.things) if self.R.item_id(x) in self.s["items"]]
        r = self._find(arg, self.visible() + self.loose() + held)
        if r is None:
            return f"There is no '{arg}' here to read."
        text = self.R.text(r)
        if not text:
            return f"There is nothing written on {self.R.must_name(r)}."
        self._hook(r, "read")
        return f"{self.R.must_name(r)}:\n{text}"

    def _outcome(self, arg, words):
        m = re.search(r"\s+(" + "|".join(words) + r")$", arg, re.I)
        return (arg[:m.start()], m.group(1).lower()) if m else (arg, None)

    def c_fight(self, arg) -> str:
        text, how = self._outcome(arg, ("win", "lose"))
        if how is None:
            return "Say how the fight ends: fight <who> win, or fight <who> lose."
        who = self._find(text, [r for r in self.visible() if self.R.kind(r) == "person" and self._alive(r)])
        if who is None:
            return f"There is nobody called '{text}' here to fight."
        if how == "lose":
            return "You fall. You load your last save; nothing has changed."
        self.s["dead"].append(who)
        on = [x for x, row in self.R.rows.items() if row.get("carriedBy") == who and x not in self.s["taken"]]
        return f"You kill {self.R.must_name(who)}." + (
            f" On the body: {'; '.join(self.R.must_name(x) for x in on)}." if on else "")

    def c_pick(self, arg) -> str:
        text, how = self._outcome(arg, ("win", "fail"))
        if how is None:
            return "Say how the lock goes: pick <lock> win, or pick <lock> fail."
        r = self._find(text, [x for x in self.visible() if self.R.kind(x) in ("thing", "container", "door")])
        if r is None:
            return f"There is no lock called '{text}' here."
        if not self._locked(r):
            return f"{self.R.must_name(r)} is not locked."
        if ((self.R.rows.get(r) or {}).get("lock") or {}).get("level") == "key":
            return f"{self.R.must_name(r)} opens only with its key."
        if self.s["items"].get(LOCKPICK, 0) < 1:
            return "You have no lockpicks."
        if how == "fail":
            self.s["items"][LOCKPICK] -= 1
            if not self.s["items"][LOCKPICK]:
                del self.s["items"][LOCKPICK]
            return "Your lockpick breaks; the lock holds."
        self.s["unlocked"].append(r)
        return f"You pick the lock of {self.R.must_name(r)}."

    def c_pickpocket(self, arg) -> str:
        text, how = self._outcome(arg, ("win", "fail"))
        who = self._find(text, [r for r in self.visible() if self.R.kind(r) == "person" and self._alive(r)])
        if who is None:
            return f"There is nobody called '{text}' here."
        on = [x for x, row in self.R.rows.items() if row.get("carriedBy") == who and x not in self.s["taken"]]
        if how is None:
            return f"{self.R.must_name(who)} carries: " + ("; ".join(self.R.must_name(x) for x in on) or "nothing "
                   "you could lift") + ". Say how it goes: pickpocket <person> win, or pickpocket <person> fail."
        if how == "fail":
            return f"{self.R.must_name(who)} catches your hand. Nothing is taken."
        for x in on:
            self.s["taken"].append(x)
            iid = self.R.item_id(x)
            self.s["items"][iid] = self.s["items"].get(iid, 0) + ((self.R.rows.get(x) or {}).get("count") or 1)
        return "You lift: " + ("; ".join(self.R.must_name(x) for x in on) or "nothing") + "."

    def c_go(self, arg) -> str:
        a = arg.lower().strip().strip("'\"")
        to = None
        m = re.fullmatch(r"(?:marker\s*)?(\d+)", a)
        if m:
            mk = self.markers()
            i = int(m.group(1)) - 1
            if not 0 <= i < len(mk):
                return "There is no such marker. Your journal lists them."
            to = self.where(mk[i]) or self.s["at"]
        else:
            for pid in self.R.places():
                if self.R.place_name(pid).lower() == a or a and a in self.R.place_name(pid).lower():
                    to = pid
                    break
            if to is None:
                pool = [r for r in self.R.rows if self._enabled(r) and r not in self.s["taken"]
                        and not self.R.rows[r].get("container") and self.R.kind(r) in ("person", "thing", "container")
                        and self.where(r)]
                r = self._find(a, pool)
                if r:
                    to = self.where(r)
        if to is None:
            return f"You do not know a way to '{arg}'. Go to a place, a person or thing you know of, or a marker."
        self.s["at"] = to
        return "\n".join([f"You travel to {self.R.place_name(to)}.", "", self.c_look()] + self._speaks_first())

    def _speaks_first(self) -> list[str]:
        out = []
        for t in self.R.topics:
            p = t.get("person")
            if t.get("kind") != "speaks-first" or [t["id"], p] in self.s["heard"] or not self._alive(p):
                continue
            if p not in self.visible() or (t.get("stages") and self.s["stage"] not in t["stages"]):
                continue
            if self.holds(t.get("when"), lenient=True):
                out.append(f"{self.R.must_name(p)} walks up to you and speaks.")
                out += self._said(t) + self.advance()
                self.s["talking"] = p
                if not self.s["pending"]:
                    out.append(self._menu(p))
        return out

    def summary(self) -> dict:
        return {"stage": self.s["stage"], "at": self.s["at"], "items": dict(self.s["items"]), "gold": self.s["gold"],
                "flags": dict(self.s["flags"]), "dead": list(self.s["dead"]), "heard": [h[0] for h in self.s["heard"]],
                "ended": self.s["ended"]}


# -- the session: a run folder story/playtests/<quest id>/<utc>-designed/ -----------------------------------------
def is_session(folder) -> bool:
    p = Path(folder) / "session.json"
    return p.exists() and '"record_path"' in p.read_text(encoding="utf-8")[:4000]


def _load(folder) -> dict:
    return json.loads((Path(folder) / "session.json").read_text(encoding="utf-8"))


def _save(folder, sess) -> None:
    (Path(folder) / "session.json").write_text(json.dumps(sess, ensure_ascii=False) + "\n", encoding="utf-8")


def _append(folder, row) -> None:
    with open(Path(folder) / "transcript.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _rel(p) -> str:
    from tools.playtest.session import REPO
    try:
        return str(Path(p).resolve().relative_to(REPO))
    except ValueError:
        return str(p)


def new(path, *, root: Path, know=None, way=None, choose=None, model=None, effort=None,
        max_commands=60) -> tuple[Path, str]:
    """A new record session: (its run folder, the opening screen). A record with faults is refused, each fault
    a line of the HarnessError."""
    from tools.playtest import session as S
    q = load(path)
    bad = check(q)
    if bad:
        raise HarnessError(f"{path}: the record has {len(bad)} fault(s):\n  " + "\n  ".join(bad))
    g = Game(q)
    screen = g.begin()
    folder = Path(root) / q["id"] / f"{S.utc_stamp()}-designed"
    n = 1
    while folder.exists():
        n += 1
        folder = folder.with_name(f"{folder.name.split('~')[0]}~{n}")
    folder.mkdir(parents=True)
    sess = {"quest": q["id"], "record_path": _rel(path), "record": q, "state": g.s, "know": know,
            "know_text": S.know_text(know), "way": way, "choose": choose, "model": model, "effort": effort,
            "max_commands": max_commands, "created": S.utc_stamp(), "broken": None}
    _save(folder, sess)
    _append(folder, {"time": S.utc_stamp(), "think": None, "command": "(new game)", "result": screen,
                     "summary": g.summary()})
    _keep(folder, sess)
    return folder, screen


def do(folder, command: str, think: str | None) -> tuple[int, str]:
    from tools.playtest import session as S
    sess = _load(folder)
    if sess["broken"]:
        return 3, f"HARNESS ERROR (the run has stopped): {sess['broken']}"
    if not (think or "").strip():
        _append(folder, {"time": S.utc_stamp(), "think": think or "", "command": command, "refused": True,
                         "result": "Refused: every command needs --think.", "summary": None})
        return 2, "Refused: every command needs --think: say what you believe is going on and why you do this."
    st = sess["state"]
    if st["commands"] >= sess["max_commands"] and not command.strip().lower().startswith("answer"):
        return 2, (f"You have used all {sess['max_commands']} commands. Stop now and give your notes: "
                   "play end '<what you now know and have>'")
    g = Game(sess["record"], st)
    try:
        screen, code = g.do(command), 0
    except HarnessError as e:
        sess["broken"] = str(e)
        screen, code = f"HARNESS ERROR (the run has stopped): {e}", 3
    sess["state"] = g.s
    _save(folder, sess)
    _append(folder, {"time": S.utc_stamp(), "think": think, "command": command, "result": screen,
                     "summary": g.summary()})
    _keep(folder, sess)
    return code, screen


def end(folder, notes: str) -> tuple[int, str]:
    """The player stops before an ending (stuck, or out of commands): their notes are kept as they are."""
    sess = _load(folder)
    sess["state"]["notes"] = notes.strip()
    sess["state"]["over"] = True
    _save(folder, sess)
    _keep(folder, sess)
    return 0, "Thank you. Your notes are kept; you can stop now."


def _keep(folder, sess, extra: dict | None = None) -> dict:
    """milestones.md, milestones.json, notes.md and run.json from the session."""
    folder = Path(folder)
    st = sess["state"]
    rows = list(st["milestones"]) + [dict(m, answers=None) for m in st["pending"]]
    M.write(folder, sess["quest"], rows)
    if st.get("notes"):
        (folder / "notes.md").write_text(st["notes"] + "\n", encoding="utf-8")
    tr = folder / "transcript.jsonl"
    cmds = [json.loads(x)["command"] for x in tr.read_text(encoding="utf-8").splitlines() if x.strip()] \
        if tr.exists() else []
    old = json.loads((folder / "run.json").read_text()) if (folder / "run.json").exists() else {}
    run = {**old, "quest": sess["quest"], "moment": "designed", "record": sess["record_path"],
           "model": sess.get("model"), "effort": sess.get("effort"), "way": sess.get("way"),
           "choose": sess.get("choose"), "know": sess.get("know"), "created": sess["created"],
           "stages": st["done"], "ended": st["ended"] or ("harness error" if sess["broken"] else
                                                        "stopped" if st.get("over") else "open"),
           "milestones": len(st["milestones"]), "notes": bool(st.get("notes")),
           "commands_used": [c for c in cmds if c != "(new game)"], **(extra or {})}
    (folder / "run.json").write_text(json.dumps(run, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return run


def write_run(folder, extra: dict | None = None) -> dict:
    return _keep(folder, _load(folder), extra)


def has_notes(folder) -> bool:
    return bool(_load(folder)["state"].get("notes"))
