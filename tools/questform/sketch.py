"""The outline's sketch: a quest form written beside a story's outline before any place is built, checked by the same
rules as a built quest with the measured spots left out (.claude/skills/story-line/buildable.md, "The sketch").

A sketch is a fenced block in the story document, one per quest:

    ```sketch
    quest BC01 faction "Four Months for a Boat"
    ...
    ```

in a small fixed text format (one statement a line; words, "quoted text", commas between list items, `#` comments).
`read(path)` parses every block of a file; `expand(sk)` turns one into the quest form the record compiler would write
(tools/questform/compile.py): a line only moves a stage and every other result is a stage's; a take adds its held
check to the stage it opens from; a trigger that would come late closes at the step it stands for; a checked line's
refusal is its own line; the job offered at a hidden start is gated on who must live; an objective is done when the
quest moves on from its stage. Places stand in for spots: each reference stands in a named place, indoors or
outdoors, and an outdoor place marked `far` is out of sight of every other place, so `away` is judged; the rest of
placement is checked when the quest is built. `check(path)` runs the schema, every rule of `rules.check` and
`rules.check_set`, the design rules below and the reach walk, and prints each failure with the story line to change.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from tools.questform import rules

KINDS = ("main", "faction", "minor")
SKILLS = {"speech": "Speech", "persuade": "Speech", "intimidate": "Speech", "sneak": "Sneak",
          "lockpicking": "Lockpicking", "pickpocket": "Pickpocket", "alchemy": "Alchemy", "archery": "Archery",
          "block": "Block", "onehanded": "OneHanded", "one-handed": "OneHanded", "twohanded": "TwoHanded",
          "two-handed": "TwoHanded", "heavyarmor": "HeavyArmor", "lightarmor": "LightArmor", "smithing": "Smithing",
          "enchanting": "Enchanting", "alteration": "Alteration", "conjuration": "Conjuration",
          "destruction": "Destruction", "illusion": "Illusion", "restoration": "Restoration"}
LOCKS = ("novice", "apprentice", "adept", "expert", "master", "key")
STOCK = {"gold": "item.gold", "lockpick": "item.lockpick", "lockpicks": "item.lockpick"}
HARD = ("skill_at_least", "gold_at_least")
FAILS = HARD + ("item_count_at_least",)
FAR_STEP = 200000.0           # far places stand this far apart: well beyond rules.AWAY_UNITS
NEAR_STEP = 1000.0            # near outdoor places stand this far apart: well inside it

# The words a writer reaches for that name something the game cannot know or do, each with the nearest thing it can.
CANNOT = {
    "enter": "the game cannot know the player is somewhere: let a thing used or a person spoken to there move it",
    "arrive": "the game cannot know the player is somewhere: let a thing used or a person spoken to there move it",
    "reach": "the game cannot know the player is somewhere: let a thing used or a person spoken to there move it",
    "find": "finding moves nothing: the thing found is taken or used, or the person found is spoken to",
    "see": "the game cannot know a thing was looked at: a thing used (a body searched, a note read) moves it",
    "look": "the game cannot know a thing was looked at: a thing used (a body searched, a note read) moves it",
    "seen": "the quest cannot know a deed was seen: Skyrim's crime system answers a theft; the quest knows the "
            "thing is held",
    "wait": "the clock moves nothing: let a line, a take, a use or a death move it",
    "time": "the clock moves nothing: let a line, a take, a use or a death move it",
    "night": "the clock moves nothing: night and dusk are words people say",
    "count": "the quest cannot count: one named thing or one named death per stage, or a hand-in gated on things "
             "held (`holds jar 3`)",
    "kills": "the quest cannot count: one named death per stage, or a line gated on each named person dead",
    "cast": "the quest cannot know a spell was cast: a skill check on a line (`skill Restoration 25`) stands in",
    "flee": "the quest cannot know a fight was fled: what the player still holds, or who is still alive, stands in",
    "spare": "the quest cannot know someone was spared: a line said to them while they live stands in",
    "follow": "nobody walks for a quest: a person who has gone ahead is a second placement, switched on away "
              "from the player",
    "walk": "nobody walks for a quest: place the person where they are needed",
    "move": "nothing moves for a quest: switch one placement off and another on, away from the player",
    "scene": "there are no scenes: tell it in a line, or let it have happened already where the player finds it",
    "teach": "no result teaches a skill: give a skill book (an item)",
    "price": "no result changes a trader's price: a gold check on a line is the price",
    "met": "the record cannot gate on having spoken before: gate on a stage done at which they spoke",
    "not": "a gate is never negated: use its opposite (alive or dead) or a stage",
    "hostile": "a line cannot turn its speaker hostile: a person is placed hostile, or the player starts the fight "
               "(mark the death `choice`)",
}

CHECKED_WHEN_BUILT = (
    "each person's and thing's exact spot (navmesh or surface), and the person who speaks first a step from the "
    "player's arrival",
    "every place, person and form key the outline names exists in the built world, and each place reads as what "
    "it is called (place-build)",
    "the name the player sees on each thing, door and room",
    "the words: journal entries, lines and refusals (dialogue-write, text-review)",
)


class SketchError(Exception):
    pass


# -- reading -------------------------------------------------------------------------------------------------------

_TOKEN = re.compile(r'"((?:[^"\\]|\\.)*)"|(->)|(,)|(#.*)|([^\s,"#]+)')


def tokens(text: str) -> list[tuple[str, str]]:
    out = []
    pos = 0
    text = text.rstrip()
    while pos < len(text):
        if text[pos].isspace():
            pos += 1
            continue
        m = _TOKEN.match(text, pos)
        if not m:
            raise SketchError(f"cannot read from here: {text[pos:pos + 20]!r} (is a quote left open?)")
        pos = m.end()
        if m.group(1) is not None:
            out.append(("str", m.group(1).replace('\\"', '"')))
        elif m.group(2):
            out.append(("arrow", "->"))
        elif m.group(3):
            out.append(("comma", ","))
        elif m.group(4):
            break
        else:
            out.append(("word", m.group(5)))
    return out


def blocks(path: Path) -> list[tuple[int, list[str]]]:
    """Every sketch block of a file: (the file line of its first statement, its lines). A file of no fences that ends
    `.sketch` is one block."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    if path.suffix == ".sketch":
        return [(1, lines)]
    out, cur, start = [], None, 0
    for i, ln in enumerate(lines, 1):
        s = ln.strip()
        if cur is None and s.startswith("```sketch"):
            cur, start = [], i + 1
        elif cur is not None and s.startswith("```"):
            out.append((start, cur))
            cur = None
        elif cur is not None:
            cur.append(ln)
    if cur is not None:
        raise SketchError(f"{path}:{start - 1}: a sketch block is not closed with ```")
    return out


class Sketch:
    """One quest's sketch as read: what the writer wrote, each part with its file line."""

    def __init__(self, path: Path, first: int):
        self.path, self.first = path, first
        self.qid = self.kind = self.name = None
        self.start = None
        self.places: dict[str, dict] = {}
        self.people: dict[str, dict] = {}
        self.things: dict[str, dict] = {}
        self.items: dict[str, dict] = {}
        self.stages: dict[int, dict] = {}
        self.objectives: list[dict] = []
        self.lines: list[dict] = []
        self.triggers: list[dict] = []
        self.must_live: list[dict] = []
        self.errors: list[tuple[int, str, str]] = []      # (line, rule, message)
        self.src: dict[tuple, int] = {}

    def where(self, key) -> int | None:
        return self.src.get(key)


class _Stream:
    def __init__(self, toks, at):
        self.t, self.i, self.at = toks, 0, at

    def more(self):
        return self.i < len(self.t)

    def peek(self, kind=None):
        if self.i < len(self.t) and (kind is None or self.t[self.i][0] == kind):
            return self.t[self.i]
        return None

    def word(self, what="a word") -> str:
        if self.i >= len(self.t) or self.t[self.i][0] != "word":
            got = self.t[self.i][1] if self.i < len(self.t) else "the end of the line"
            raise SketchError(f"expected {what}, found {got!r}")
        self.i += 1
        return self.t[self.i - 1][1]

    def text(self, what="a quoted text") -> str:
        if self.i >= len(self.t) or self.t[self.i][0] != "str":
            got = self.t[self.i][1] if self.i < len(self.t) else "the end of the line"
            raise SketchError(f"expected {what} in double quotes, found {got!r}")
        self.i += 1
        return self.t[self.i - 1][1]

    def number(self, what="a number") -> int:
        w = self.word(what)
        try:
            return int(w)
        except ValueError:
            raise SketchError(f"expected {what}, found {w!r}") from None

    def take(self, w) -> bool:
        if self.i < len(self.t) and self.t[self.i] == ("word", w):
            self.i += 1
            return True
        return False

    def arrow(self) -> bool:
        if self.peek("arrow"):
            self.i += 1
            return True
        return False

    def comma(self) -> bool:
        if self.peek("comma"):
            self.i += 1
            return True
        return False

    def until_words(self, stop) -> list[tuple[str, str]]:
        """The tokens up to the next clause word in `stop` (or the end)."""
        out = []
        while self.i < len(self.t) and not (self.t[self.i][0] == "word" and self.t[self.i][1] in stop) and \
                self.t[self.i][0] not in ("arrow", "str"):
            out.append(self.t[self.i])
            self.i += 1
        return out


def _split(toks):
    """A comma-separated list of tokens."""
    out, cur = [], []
    for t in toks:
        if t[0] == "comma":
            if cur:
                out.append(cur)
            cur = []
        else:
            cur.append(t)
    if cur:
        out.append(cur)
    return out


def _stages(spec: str) -> tuple[int, int]:
    m = re.fullmatch(r"(\d+)(?:-(\d+))?", spec)
    if not m:
        raise SketchError(f"expected a stage or a span of stages (20 or 20-39), found {spec!r}")
    a = int(m.group(1))
    return a, int(m.group(2)) if m.group(2) else a


def _item(sk: Sketch, w: str) -> str:
    return STOCK.get(w, w)


def condition(sk: Sketch, toks) -> dict:
    s = _Stream(toks, 0)
    w = s.word("a gate")
    if w in ("stage",):
        q = s.word("a quest id")
        op = s.word("is or >=")
        n = s.number("a stage")
        if op not in ("is", ">=", "="):
            raise SketchError(f"a stage gate is `stage <quest> is <n>` or `stage <quest> >= <n>`, not {op!r}")
        c = {"is": "stage_is" if op in ("is", "=") else "stage_at_least", "quest": q, "stage": n}
    elif w == "done":
        c = {"is": "stage_done", "quest": s.word("a quest id"), "stage": s.number("a stage")}
    elif w == "number":
        num = s.word("a number's id")
        op = s.word("= or >=")
        if op not in ("=", ">="):
            raise SketchError(f"a number gate is `number <id> = <v>` or `number <id> >= <v>`, not {op!r}")
        c = {"is": "number_compare", "number": num, "op": op, "value": s.number("a value")}
    elif w == "rank":
        c = {"is": "rank_at_least", "faction": s.word("a faction"), "rank": s.number("a rank")}
    elif w == "holds":
        it = _item(sk, s.word("a thing or item"))
        n = s.number("a count") if s.peek("word") and s.peek()[1].isdigit() else 1
        c = {"is": "item_count_at_least", "item": it, "count": n}
    elif w == "gold":
        c = {"is": "gold_at_least", "gold": s.number("an amount of gold")}
    elif w == "skill":
        sw = s.word("a skill")
        if sw.lower() not in SKILLS:
            raise SketchError(f"{sw!r} is no skill the game can check (one of {', '.join(sorted(set(SKILLS.values())))})")
        c = {"is": "skill_at_least", "skill": SKILLS[sw.lower()], "value": s.number("a level")}
    elif w in ("alive", "dead"):
        c = {"is": w, "ref": s.word("a person")}
    elif w == "regard":
        c = {"is": "regard_at_least", "ref": s.word("a person"), "value": s.number("a regard, -3 to 4")}
    elif w in ("race", "sex"):
        c = {"is": f"{w}_is", "value": s.word(f"a {w}")}
    elif w in CANNOT:
        raise SketchError(f"`{w}` is no gate: {CANNOT[w]}")
    else:
        raise SketchError(f"`{w}` is no gate the game can check (stage, done, number, rank, holds, gold, skill, "
                          "alive, dead, regard, race, sex)")
    if s.more():
        raise SketchError(f"left over in a gate: {' '.join(t[1] for t in s.t[s.i:])!r} (a comma between gates?)")
    return c


def result(sk: Sketch, toks) -> dict:
    s = _Stream(toks, 0)
    w = s.word("a result")
    if w in ("give", "take"):
        it = _item(sk, s.word("a thing or item"))
        n = s.number("a count") if s.peek("word") and s.peek()[1].isdigit() else 1
        r = {"do": f"{w}_item", "item": it, "count": n}
    elif w in ("give-gold", "take-gold"):
        r = {"do": w.replace("-", "_"), "amount": s.number("an amount")}
    elif w in ("set", "add"):
        r = {"do": f"{w}_number", "number": s.word("a number's id"), "value": s.number("a value")}
    elif w == "join":
        r = {"do": "join_faction", "faction": s.word("a faction")}
    elif w == "rank":
        r = {"do": "set_rank", "faction": s.word("a faction"), "rank": s.number("a rank")}
    elif w == "regard":
        r = {"do": "change_regard", "ref": s.word("a person"), "by": s.number("a step, -4 to 4")}
    elif w in ("on", "off"):
        r = {"do": f"switch_{w}", "ref": s.word("a person or thing")}
    elif w in ("lock", "unlock"):
        r = {"do": f"{w}_door", "ref": s.word("a door")}
    elif w == "own":
        r = {"do": "give_ownership", "ref": s.word("an owned container or thing")}
    elif w == "message":
        r = {"do": "show_message", "text": s.text("the message's words")}
    elif w == "start":
        r = {"do": "start_quest", "quest": s.word("a quest id"), "stage": s.number("its stage")}
    elif w == "stage":
        r = {"do": "set_stage", "stage": s.number("a stage")}
    elif w in CANNOT:
        raise SketchError(f"`{w}` is no result: {CANNOT[w]}")
    else:
        raise SketchError(f"`{w}` is no result the game can do (give, take, give-gold, take-gold, set, add, join, "
                          "rank, regard, on, off, lock, unlock, own, message, start, stage)")
    if s.more():
        raise SketchError(f"left over in a result: {' '.join(t[1] for t in s.t[s.i:])!r} (a comma between results?)")
    return r


def _place(sk: Sketch, s: _Stream, what: str) -> str:
    p = s.word("a place id")
    if p not in sk.places:
        raise SketchError(f"{what} stands at {p!r}, which is no `place` of this sketch (declare places first)")
    return p


def statement(sk: Sketch, n: int, toks) -> None:
    s = _Stream(toks, n)
    w = s.word("a statement")
    if w == "quest":
        sk.qid = s.word("the quest's id")
        sk.kind = s.word("main, faction or minor")
        if sk.kind not in KINDS:
            raise SketchError(f"a quest is main, faction or minor, not {sk.kind!r}")
        sk.name = s.text("the quest's name")
        sk.src[("quest",)] = n
    elif w == "start":
        how = s.word("game, when or from")
        if how == "game":
            sk.start = {"by": "game", "stage": s.number("the start stage")}
        elif how == "when":
            q, qs = s.word("a quest id"), s.number("its stage")
            if not s.take("at"):
                raise SketchError("`start when <quest> <stage> at <this quest's stage>`")
            sk.start = {"by": "quest_stage", "quest": q, "quest_stage": qs, "stage": s.number("a stage")}
        elif how == "from":
            q = s.word("the quest whose stage starts it")
            if not s.take("at"):
                raise SketchError("`start from <quest> at <this quest's stage>`")
            sk.start = {"by": "start_quest", "stage": s.number("a stage"), "_from": q}
        else:
            raise SketchError("a quest starts `game <stage>`, `when <quest> <stage> at <stage>` or `from <quest> at "
                              "<stage>`")
        sk.src[("start",)] = n
    elif w == "place":
        pid = s.word("a place id")
        io = s.word("indoors or outdoors")
        if io not in ("indoors", "outdoors"):
            raise SketchError(f"a place is indoors or outdoors, not {io!r}")
        far = s.take("far")
        if far and io == "indoors":
            raise SketchError("`far` is for an outdoor place: every indoor place is already out of sight")
        sk.places[pid] = {"name": s.text("the place's name"), "interior": io == "indoors", "far": far, "line": n}
    elif w == "person":
        pid = s.word("a person id")
        if not s.take("at"):
            raise SketchError("`person <id> at <place> [level N] [hostile] [existing] \"name\"`")
        p = {"id": pid, "place": _place(sk, s, f"person {pid}"), "line": n}
        while s.peek("word"):
            k = s.word()
            if k == "level":
                p["level"] = s.number("a level")
            elif k in ("hostile", "existing", "off"):
                p[k] = True
            elif k == "dead":
                sk.errors.append((n, "body", f"person {pid}: nobody is placed dead: a container that is theirs (a "
                                  "satchel, a strongbox) holds what their body would, or they are alive and killed"))
            elif k in CANNOT:
                raise SketchError(f"`{k}`: {CANNOT[k]}")
            else:
                raise SketchError(f"a person takes level, hostile, existing or off, not {k!r}")
        p["name"] = s.text("the person's name")
        sk.people[pid] = p
        sk.src[("ref", pid)] = n
    elif w in ("thing", "door"):
        tid = s.word("an id")
        t = {"id": tid, "kind": w, "line": n}
        where = s.word("at, in or on")
        if where == "at":
            t["place"] = _place(sk, s, f"{w} {tid}")
        elif where == "in" and w == "thing":
            t["in"] = s.word("a container")
        elif where == "on" and w == "thing":
            t["on"] = s.word("a person")
        else:
            raise SketchError(f"a {w} stands `at <place>`" + (", lies `in <container>` or is carried `on <person>`"
                                                              if w == "thing" else ""))
        while s.peek("word"):
            k = s.word()
            if k == "container" and w == "thing":
                t["container"] = True
            elif k == "locked":
                lv = s.word("a lock level")
                if lv not in LOCKS:
                    raise SketchError(f"a lock is {', '.join(LOCKS)}, not {lv!r}")
                t["lock"] = {"level": lv}
                if s.take("key"):
                    t["lock"]["key"] = s.word("the key's id")
            elif k == "owner":
                t["owner"] = s.word("a person or faction")
            elif k == "holds" and w == "thing":
                rows = _split(s.until_words(("readable", "stock", "owner", "locked", "container")))
                t["holds"] = []
                for row in rows:
                    if row[-1][0] == "word" and row[-1][1].isdigit() and len(row) == 2:
                        t["holds"].append({"item": _item(sk, row[0][1]), "count": int(row[-1][1])})
                    elif len(row) == 1:
                        t["holds"].append({"item": _item(sk, row[0][1]), "count": 1})
                    else:
                        raise SketchError("`holds <item> [count], <item> [count]`")
            elif k == "off":
                t["off"] = True
            elif k == "readable" and w == "thing":
                t["readable"] = True
            elif k == "stock" and w == "thing":
                t["stock"] = _item(sk, s.word("a stock item"))
                if s.take("count"):
                    t["count"] = s.number("a count")
            else:
                raise SketchError(f"a {w} takes " + ("container, locked, owner, holds, readable or stock"
                                                     if w == "thing" else "locked or owner") + f", not {k!r}")
        t["name"] = s.text("its name")
        sk.things[tid] = t
        sk.src[("ref", tid)] = n
    elif w == "item":
        iid = s.word("an item id")
        it = {"id": iid, "line": n, "readable": s.take("readable")}
        it["name"] = s.text("its name")
        sk.items[iid] = it
        sk.src[("item", iid)] = n
    elif w == "stage":
        num = s.number("a stage number")
        st = {"number": num, "line": n, "ending": "none", "shown": True, "journal": None, "results": []}
        if s.take("hidden"):
            st["shown"] = False
        else:
            if s.peek("word") and s.peek()[1] in ("completed", "failed"):
                st["ending"] = s.word()
            st["journal"] = s.text("its journal entry")
        if s.take("do"):
            st["results"] = [result(sk, r) for r in _split(s.t[s.i:])]
            s.i = len(s.t)
        sk.stages[num] = st
        sk.src[("stage", num)] = n
    elif w == "objective":
        num = s.number("an objective number")
        if not s.take("at"):
            raise SketchError("`objective <n> at <stage>[, <stage>] \"words\" -> <target>[, <target>]`")
        shown = []
        while s.peek("word"):
            shown.append(s.number("a stage"))
            s.comma()
        text = s.text("the objective's words")
        if not s.arrow():
            raise SketchError("an objective points its marker at someone or something: `-> <target>`")
        targets = [x[0][1] for x in _split(s.t[s.i:])]
        s.i = len(s.t)
        sk.objectives.append({"number": num, "shown_at": shown, "text": text, "targets": targets, "line": n})
        sk.src[("objective", num)] = n
    elif w == "line":
        lid = s.word("a line id")
        ln = {"id": lid, "speaker": s.word("its speaker"), "kind": "topic", "prompt": None, "if": [], "to": None,
              "else": None, "asks": [], "says": None, "line": n}
        stop = ("first", "greeting", "answer", "at", "ask", "if", "else", "asks", "says", "do", "hostile")
        while s.more():
            if s.arrow():
                ln["to"] = s.number("the stage it moves to")
                continue
            k = s.word("a clause (at, ask, if, ->, else, asks, says)")
            if k in ("first", "greeting", "answer"):
                ln["kind"] = {"first": "speaks_first"}.get(k, k)
            elif k == "at":
                ln["window"] = _stages(s.word("a stage or span"))
            elif k == "ask":
                ln["prompt"] = s.text("the player's words")
            elif k == "if":
                ln["if"] = [condition(sk, c) for c in _split(s.until_words(stop))]
            elif k == "else":
                ln["else"] = s.text("the refusal's gist")
            elif k == "asks":
                ln["asks"] = [x[0][1] for x in _split(s.until_words(stop))]
            elif k == "says":
                ln["says"] = s.text("the gist of what is said")
            elif k == "do":
                while s.more() and s.peek() != ("word", "says") and not s.peek("arrow"):
                    s.i += 1
                sk.errors.append((n, "line-result", f"line {lid}: a line only moves a stage (`-> <stage>`); what it "
                                  "gives, takes, sets, switches or unlocks is that stage's `do`"))
            elif k == "hostile":
                sk.errors.append((n, "line-hostile", f"line {lid}: {CANNOT['hostile']}"))
            elif k in CANNOT:
                raise SketchError(f"`{k}`: {CANNOT[k]}")
            else:
                raise SketchError(f"a line takes first, greeting, answer, at, ask, if, ->, else, asks and says, "
                                  f"not {k!r}" + (" (a line only moves a stage: put its results on the stage it "
                                                  "moves to)" if k == "do" else ""))
        if "window" not in ln:
            raise SketchError(f"line {lid}: `at <stage>` or `at <first>-<last>`: when it is offered")
        if ln["says"] is None:
            raise SketchError(f"line {lid}: `says \"...\"`, the gist of what is said")
        if ln["kind"] in ("topic", "answer") and ln["prompt"] is None:
            raise SketchError(f"line {lid}: a topic or answer has the player's words (`ask \"...\"`)")
        sk.lines.append(ln)
        sk.src[("line", lid)] = n
    elif w in ("take", "use", "death"):
        ref = s.word("a thing or person")
        t = {"kind": w, "ref": ref, "line": n}
        _trigger_tail(s, t)
        sk.triggers.append(t)
    elif w == "when":
        t = {"kind": "quest_stage", "quest": s.word("a quest id"), "quest_stage": s.number("its stage"), "line": n}
        _trigger_tail(s, t)
        sk.triggers.append(t)
    elif w == "must-live":
        ref = s.word("a person")
        if not s.take("fails"):
            raise SketchError("`must-live <person> fails <failed ending> [from <stage>] [to <stage>]`")
        m = {"ref": ref, "fail_stage": s.number("the failed ending"), "line": n}
        while s.peek("word"):
            k = s.word()
            if k not in ("from", "to"):
                raise SketchError(f"a who-must-live row takes from and to, not {k!r}")
            m[k] = s.number("a stage")
        sk.must_live.append(m)
        sk.src[("must", ref)] = n
    elif w in CANNOT:
        raise SketchError(f"`{w}` moves nothing: {CANNOT[w]}")
    else:
        raise SketchError(f"`{w}` is no statement (quest, start, place, person, thing, door, item, stage, objective, "
                          "line, take, use, death, when, must-live)")
    if s.more():
        raise SketchError(f"left over: {' '.join(t[1] for t in s.t[s.i:])!r}")


def _trigger_tail(s: _Stream, t: dict):
    if ("word", "do") in s.t[s.i:]:
        raise SketchError(f"a {t['kind']} moves a stage (`-> <stage>`); what it shows or sets is that stage's `do`")
    if not s.take("from"):
        raise SketchError(f"`{t['kind']} <id> from <stage> -> <stage> [until <stage>]`: the stage it is open from")
    t["prerequisite"] = s.number("a stage")
    if not s.arrow():
        raise SketchError("`-> <stage>`: the stage it moves the quest to")
    t["sets"] = s.number("a stage")
    while s.peek("word"):
        k = s.word()
        if k == "until":
            t["until"] = s.number("a stage")
        elif k == "choice" and t["kind"] == "death":
            t["choice"] = True
        else:
            raise SketchError("a trigger takes until" + (" and choice" if t["kind"] == "death" else "") +
                              f", not {k!r}")


def parse(path: Path, first: int, lines: list[str]) -> Sketch:
    sk = Sketch(path, first)
    for i, raw in enumerate(lines):
        n = first + i
        try:
            toks = tokens(raw)
            if toks:
                statement(sk, n, toks)
        except SketchError as e:
            sk.errors.append((n, "sketch", str(e)))
    if sk.qid is None:
        sk.errors.append((first, "sketch", "the block has no `quest <id> <kind> \"name\"` statement"))
    if sk.start is None:
        sk.errors.append((first, "sketch", "the quest says how it starts: `start game <stage>`, `start when ...` or "
                                           "`start from ...`"))
    return sk


def read(path) -> list[Sketch]:
    path = Path(path)
    return [parse(path, first, lines) for first, lines in blocks(path)]


# -- expanding to the quest form ------------------------------------------------------------------------------------

def _pos(sk: Sketch) -> dict[str, dict]:
    """A stand-in spot per place: every indoor place its own cell; outdoor places near one another unless `far`."""
    out, near, far = {}, 0, 0
    for pid, p in sk.places.items():
        if p["interior"]:
            out[pid] = {"cell": f"sketch:{pid}", "interior": True, "x": 0.0, "y": 0.0, "z": 0.0}
        elif p["far"]:
            far += 1
            out[pid] = {"cell": f"sketch:{pid}", "interior": False, "x": FAR_STEP * far, "y": FAR_STEP * far, "z": 0.0}
        else:
            out[pid] = {"cell": f"sketch:{pid}", "interior": False, "x": NEAR_STEP * near, "y": 0.0, "z": 0.0}
            near += 1
    return out


def _refs(sk: Sketch) -> list[dict]:
    spots, out, count = _pos(sk), [], defaultdict(int)

    def at(place):
        count[place] += 1
        a = dict(spots[place])
        a["x"] += 10.0 * count[place]
        return a
    switched_on = {r["ref"] for st in sk.stages.values() for r in st["results"] if r["do"] == "switch_on"}
    for pid, p in sk.people.items():
        ref = {"id": pid, "kind": "person", "enabled": pid not in switched_on and not p.get("off"),
               "name": p["name"], "at": at(p["place"])}
        if p.get("existing"):
            ref["placement"] = {"existing": f"sketch:{pid}"}
        else:
            ref["placement"] = {"base": {"kind": "template_person", "id": "sketch:person"},
                                "anchor": {"place": f"sketch:{p['place']}", "rule": "navmesh"}}
            if "level" in p:
                ref["level"] = p["level"]
        if p.get("hostile"):
            ref["hostile"] = True
        out.append(ref)
    for tid, t in sk.things.items():
        ref = {"id": tid, "kind": t["kind"], "enabled": tid not in switched_on and not t.get("off"), "name": t["name"]}
        if t["kind"] == "door":
            ref["placement"] = {"existing": f"sketch:{tid}"}
        elif "in" in t:
            ref["placement"] = {"base": {"kind": "template_item", "id": "sketch:item"}, "container": t["in"]}
            ref["enabled"] = True
        elif "on" in t:
            ref["placement"] = {"base": {"kind": "item" if t.get("stock") else "template_item",
                                         "id": t.get("stock") or "sketch:item"}, "carried_by": t["on"]}
        elif t.get("container"):
            ref["placement"] = {"base": {"kind": "existing_base", "id": "sketch:container"},
                                "anchor": {"place": f"sketch:{t['place']}", "rule": "surface"}}
        elif t.get("stock"):
            ref["placement"] = {"base": {"kind": "item", "id": t["stock"]},
                                "anchor": {"place": f"sketch:{t['place']}", "rule": "surface"}}
            if t.get("count"):
                ref["count"] = t["count"]
        else:
            ref["placement"] = {"base": {"kind": "template_item", "id": "sketch:item"},
                                "anchor": {"place": f"sketch:{t['place']}", "rule": "surface"}}
        if "place" in t:
            ref["at"] = at(t["place"])
        for f in ("lock", "owner"):
            if f in t:
                ref[f] = dict(t[f]) if isinstance(t[f], dict) else t[f]
        if "lock" in ref and "key" in ref["lock"]:
            ref["lock"]["key"] = _item(sk, ref["lock"]["key"])
        if t.get("holds"):
            ref["contents"] = t["holds"]
        if t.get("readable"):
            ref["text"] = "(its words are written with the quest)"
        out.append(ref)
    return out


def _exits(form, n) -> set[int]:
    """The stages the quest moves to from stage n, as `objective-left` reads them."""
    stages = {s["number"]: s for s in form["stages"]}
    out = {r["stage"] for r in stages[n]["results"] if r["do"] == "set_stage"}
    out |= {t["sets"] for t in form["triggers"] if t["prerequisite"] == n}
    out |= {r["stage"] for ln in form["lines"] if ln["first_stage"] <= n <= ln["last_stage"]
            for r in ln["results"] if r["do"] == "set_stage"}
    return out


def _key(c) -> str:
    return json.dumps(c, sort_keys=True)


def expand(sk: Sketch) -> tuple[dict | None, dict]:
    """The quest form the record compiler would write for this sketch, and where each of its parts was written: {("line",
    form line id) | ("stage", n) | ("trigger", id) | ("ref", id) | ("objective", n) | ("must", ref): file line}."""
    if sk.qid is None or sk.start is None:
        return None, {}
    src = dict(sk.src)
    stage_nums = sorted(sk.stages)
    endings = {n for n, s in sk.stages.items() if s["ending"] != "none"}
    stages = [{"number": n, "shown": s["shown"], "journal": s["journal"], "ending": s["ending"],
               "results": [dict(r) for r in s["results"]]} for n, s in sorted(sk.stages.items())]
    start = {k: v for k, v in sk.start.items() if not k.startswith("_")}
    # triggers
    triggers = []
    for t in sk.triggers:
        tid = f"{t['kind']}.{t.get('ref') or t.get('quest')}.{t['prerequisite']}-{t['sets']}"
        row = {"id": tid, **{k: v for k, v in t.items() if k != "line"}}
        triggers.append(row)
        src[("trigger", tid)] = t["line"]
    # who must live
    shown = [n for n in stage_nums if sk.stages[n]["shown"] and n not in endings]
    must = []
    for m in sk.must_live:
        row = {"ref": m["ref"], "fail_stage": m["fail_stage"], "main_message": sk.kind != "minor"}
        lo = m.get("from", shown[0] if shown else start["stage"])
        if lo > start["stage"]:
            row["from"] = lo
        if "to" in m:
            row["to"] = m["to"]
        must.append(row)
    # lines: a line moves at most one stage; one line per stage it moves from; a check's refusal after its group
    lines, groups, order = [], defaultdict(list), []
    for ln in sk.lines:
        a, b = ln["window"]
        base = {"speaker": ln["speaker"], "kind": "topic" if ln["kind"] == "speaks_first" else ln["kind"],
                "prompt": None if ln["kind"] == "greeting" else ln["prompt"], "text": ln["says"], "written": False,
                "answers": list(ln["asks"])}
        made = []
        if ln["to"] is not None:
            for s in [n for n in stage_nums if a <= n <= b and n not in endings] or [a]:
                made.append({**base, "id": f"{ln['id']}@{s}", "conditions": [dict(c) for c in ln["if"]],
                             "results": [{"do": "set_stage", "stage": ln["to"]}], "first_stage": s, "last_stage": s})
        else:
            inside = [n for n in stage_nums if a <= n <= b]
            a, b = (inside[0], inside[-1]) if inside else (a, b)
            made.append({**base, "id": ln["id"], "conditions": [dict(c) for c in ln["if"]], "results": [],
                         "first_stage": a, "last_stage": b})
        for m in made:
            src[("line", m["id"])] = ln["line"]
        if ln["kind"] == "speaks_first":
            twin = {**made[0], "id": f"{ln['id']}.first", "kind": "speaks_first", "prompt": None}
            made.append(twin)
            src[("line", twin["id"])] = ln["line"]
        key = (ln["speaker"], ln["prompt"])
        groups[key].append((ln, made))
        order.append((key, made))
    seen_group = defaultdict(int)
    errors = []
    for key, made in order:
        lines.extend(made)
        seen_group[key] += 1
        if seen_group[key] < len(groups[key]) or key[1] is None:
            continue
        # the group's last line: its checks' refusal comes after it
        members = groups[key]
        movers = [m for _, ms in members for m in ms if m["results"] and m["kind"] != "speaks_first"]
        gate_sets = [m["conditions"] for m in movers]
        hard = [m for m in movers if any(c["is"] in HARD for c in m["conditions"])
                and not any(o is not m and {_key(c) for c in o["conditions"]} <=
                            {_key(c) for c in m["conditions"] if c["is"] not in HARD} for o in movers)]
        refusal = next((ln for ln, _ in members if ln["else"]), None)
        if hard and refusal is None:
            first = hard[0]
            errors.append((src[("line", first["id"])], "refusal",
                           f"line {first['id']}: its check of skill or gold has no refusal: add `else \"...\"`, what "
                           "the speaker says when it fails"))
            continue
        if refusal is None or not gate_sets:
            continue
        fails = HARD if any(c["is"] in HARD for gs in gate_sets for c in gs) else FAILS
        for s in sorted({m["first_stage"] for m in movers}):
            here = [gs for m, gs in zip(movers, gate_sets) if m["first_stage"] == s]
            soft = [c for c in here[0] if c["is"] not in fails and all(_key(c) in {_key(x) for x in gs}
                                                                       for gs in here)]
            if any({_key(c) for c in soft} == {_key(c) for c in gs} for gs in here):
                errors.append((refusal["line"], "refusal", f"line {refusal['id']}: its refusal has every gate of "
                               "the line before it, so it is never said: gate the line on a check the player can "
                               "fail (skill, gold, a thing held), or drop the `else`"))
                continue
            fid = f"{refusal['id']}@{s}.else"
            lines.append({"id": fid, "speaker": key[0], "kind": refusal["kind"] if refusal["kind"] != "speaks_first"
                          else "topic", "prompt": key[1], "text": refusal["else"], "written": False,
                          "conditions": soft, "results": [], "first_stage": s, "last_stage": s, "answers": []})
            src[("line", fid)] = refusal["line"]
    # answers name the expanded ids of answer lines open with the question
    ids = defaultdict(list)
    for ln in lines:
        ids[ln["id"].split("@")[0].split(".first")[0]].append(ln)
    for ln in lines:
        ln["answers"] = [a["id"] for x in ln["answers"] for a in ids.get(x, [])
                         if a["first_stage"] <= ln["last_stage"] and ln["first_stage"] <= a["last_stage"]]
    # checks shown on prompts
    want = defaultdict(set)
    for ln in lines:
        if ln["prompt"]:
            want[(ln["speaker"], ln["prompt"])] |= set(rules.checks(ln["conditions"]))
    for ln in lines:
        if ln["prompt"]:
            w = sorted(want[(ln["speaker"], ln["prompt"])], key=lambda c: (c[0] != "skill", str(c)))
            ln["prompt"] = rules.labelled(ln["prompt"], w)
    # a job offered at a hidden start is offered only while who must live lives
    if start["by"] == "game" and not sk.stages.get(start["stage"], {}).get("shown", True):
        for m in must:
            if m.get("from", start["stage"]) <= start["stage"]:
                continue
            for ln in lines:
                if ln["first_stage"] <= start["stage"] <= ln["last_stage"] and ln["results"]:
                    g = {"is": "alive", "ref": m["ref"]}
                    if g not in ln["conditions"]:
                        ln["conditions"].append(g)
    # a take: the stage it opens from moves on at once for a thing already held
    by = {s["number"]: s for s in stages}
    for t in triggers:
        if t["kind"] == "take" and t["prerequisite"] in by:
            row = {"do": "set_stage", "stage": t["sets"], "if_held": _item(sk, t["ref"])}
            th = sk.things.get(t["ref"])
            if th and th.get("stock"):
                row["if_held"] = th["stock"]
            if row not in by[t["prerequisite"]]["results"]:
                by[t["prerequisite"]]["results"].append(row)
    form = {"version": 1,
            "quest": {"id": sk.qid, "editor_id": f"ARG_{sk.qid}", "name": sk.name, "kind": sk.kind, "start": start},
            "stages": stages, "objectives": [], "refs": _refs(sk), "lines": lines, "triggers": triggers,
            "must_live": must}
    # an objective is done when the quest moves on from a stage it is shown at
    for o in sk.objectives:
        done = set()
        for s in o["shown_at"]:
            if s in by:
                done |= {x for x in _exits(form, s) if x not in endings and x in by}
        form["objectives"].append({"number": o["number"], "text": o["text"], "shown_at": o["shown_at"],
                                   "completed_at": sorted(done - set(o["shown_at"])), "targets": o["targets"]})
    names = {i["id"]: i["name"] for i in sk.items.values()}
    texts = {i["id"]: "(its words are written with the quest)" for i in sk.items.values() if i["readable"]}
    names.update({STOCK[k]: k.capitalize() for k in ("gold", "lockpick")})
    form["names"] = names
    if texts:
        form["texts"] = texts
    form["places"] = {f"sketch:{pid}": {"name": p["name"], "interior": p["interior"]} for pid, p in sk.places.items()}
    # a trigger that could come late closes at the step it stands for, as the compiler closes it
    try:
        late = rules.late_triggers(rules.Form(form)) if not _broken(form) else {}
    except (KeyError, TypeError):
        late = {}
    for t in triggers:
        if t["id"] in late and "until" not in t:
            ex = sorted(x for x in _exits(form, t["prerequisite"]) if x != t["sets"] and x > t["prerequisite"]
                        and x not in endings and x in by)
            if ex:
                t["until"] = ex[0]
    form["_errors"] = errors
    return form, src


def _broken(form) -> bool:
    """A form the graph walks cannot read yet (a stage or ref named that is not there): the rules say which."""
    nums = {s["number"] for s in form["stages"]}
    named = {t["prerequisite"] for t in form["triggers"]} | {t["sets"] for t in form["triggers"]} | \
        {r["stage"] for s in form["stages"] for r in s["results"] if r["do"] == "set_stage"} | \
        {r["stage"] for ln in form["lines"] for r in ln["results"] if r["do"] == "set_stage"} | \
        {ln["first_stage"] for ln in form["lines"]} | {ln["last_stage"] for ln in form["lines"]} | \
        {form["quest"]["start"]["stage"]}
    refs = {r["id"] for r in form["refs"]}
    return not named <= nums or any(t.get("ref") and t["ref"] not in refs for t in form["triggers"])


# -- the design rules: what a writer most often gets wrong that the form's rules do not name ---------------------

DESIGN = ("rank-set", "take-unheld", "give-twice", "hostile-speaks", "hostile-must-live", "death-both-ways", "one-name", "give-placed", "dead-early",
          "early-death", "needs-living", "number-set", "refusal")


def design(form: dict, sk: Sketch, numbers_set: set[str], factions_set: set[str] = frozenset()) -> list[tuple[str, str]]:
    out = []
    fm = rules.Form(form)
    lives = {m["ref"] for m in form["must_live"]}
    people = {r["id"]: r for r in form["refs"] if r["kind"] == "person"}
    speakers = defaultdict(list)
    for ln in form["lines"]:
        speakers[ln["speaker"]].append(ln)
    for pid, r in people.items():
        if r.get("hostile") and speakers.get(pid):
            out.append(("hostile-speaks", f"ref {pid} is hostile and has lines ({speakers[pid][0]['id']}): a person "
                        "attacks on sight or speaks, never both"))
        if r.get("hostile") and pid in lives:
            out.append(("hostile-must-live", f"ref {pid} is hostile and the quest cannot go on without them"))
    deaths = {t["ref"] for t in form["triggers"] if t["kind"] == "death"}
    out += [("death-both-ways", f"ref {p}: their death both fails the quest (must-live) and moves it on") for p in
            sorted(deaths & lives)]
    # one name for one thing: two refs or items the player would see under one name, unless one is the other's
    # second placement (one starts off and the stage that switches it on switches the other off)
    shown = defaultdict(list)
    named = {ln["speaker"] for ln in form["lines"]} | {t for o in form["objectives"] for t in o["targets"]} | \
        {t.get("ref") for t in form["triggers"]} | lives | \
        {x.get("ref") or x.get("item") for _, res in rules._all_results(fm) for x in res} | \
        {c.get("ref") or c.get("item") for ln in form["lines"] for c in ln["conditions"]}
    for r in form["refs"]:
        if r["id"] in named:
            shown[r["name"].strip().lower()].append(r["id"])
    stocked = {fm.item_of(r["id"]) for r in form["refs"] if r["kind"] == "thing"}
    for i, n in form.get("names", {}).items():
        if not i.startswith("item.") and i not in stocked:
            shown[n.strip().lower()].append(i)
    for nm, ids in shown.items():
        if len(ids) < 2:
            continue
        pairs = [(a, b) for k, a in enumerate(ids) for b in ids[k + 1:]]
        bad = [(a, b) for a, b in pairs if not _second_placement(form, a, b) and not _same_stock(fm, a, b)]
        if bad:
            out.append(("one-name", f"ref {bad[0][0]} and {bad[0][1]} are both \"{nm}\": one name for one thing (a "
                        "person met in two places is two placements, one switched off where the other is switched "
                        "on)"))
    placed = {r["id"] for r in form["refs"] if r["kind"] == "thing" and fm.item_of(r["id"]) == r["id"]}
    for where, res in rules._all_results(fm):
        for x in res:
            if x["do"] == "give_item" and x["item"] in placed:
                out.append(("give-placed", f"{where} gives {x['item']}, which already lies in the world: a person "
                            "cannot hand over a thing that is placed elsewhere (give a second item of its own, or "
                            "let the player take the placed one)"))
    first_shown = min((s["number"] for s in form["stages"] if s["shown"] and s["ending"] == "none"), default=None)
    start = form["quest"]["start"]["stage"]
    for t in form["triggers"]:
        if t["kind"] != "death":
            continue
        if first_shown is not None and t["prerequisite"] < first_shown:
            out.append(("early-death", f"trigger {t['id']}: the death of {t['ref']} is open from stage "
                        f"{t['prerequisite']}, before the player has been given the quest: open it from the stage "
                        "that gives the job, with a line there for a kill made earlier"))
        elif t["prerequisite"] > start:
            caught = any(ln["first_stage"] <= t["prerequisite"] and ln["results"] and
                         {"is": "dead", "ref": t["ref"]} in ln["conditions"] for ln in form["lines"])
            if not caught:
                out.append(("dead-early", f"trigger {t['id']}: if {t['ref']} is killed before stage "
                            f"{t['prerequisite']}, their death moves nothing: add a line open at "
                            f"{t['prerequisite']} gated on `dead {t['ref']}`"))
    # nobody the quest cannot go on without, unless named: a person whose death leaves a stage with no way on
    endings = {s["number"] for s in form["stages"] if s["ending"] == "completed"}
    reach = _reachable(fm, None)
    for pid in sorted(people):
        if pid in lives or people[pid].get("hostile") or not speakers.get(pid):
            continue
        stuck = sorted(n for n in reach if fm.stages[n]["ending"] == "none" and fm.stages[n]["shown"]
                       and not (_reachable(fm, pid, n) & endings))
        if stuck:
            out.append(("needs-living", f"ref {pid}: if they die at stage {stuck[0]}, nothing moves the quest on to a "
                        "completed ending: name them in must-live, or leave another way that does not need them"))
    # a stage that takes a thing or gold from the player is reached only where the player holds it; a stage that gives
    # a thing is not also reached by taking it
    for s in form["stages"]:
        n = s["number"]
        takes = [r for r in s["results"] if r["do"] in ("take_item", "take_gold")]
        gives = {r["item"] for r in s["results"] if r["do"] == "give_item"}
        movers = [ln for ln in form["lines"] if n in rules._stage_sets(ln["results"])]
        trig = [t for t in form["triggers"] if t["sets"] == n]
        for r in takes:
            what = r.get("item") or "gold"
            def holds(ln):
                return any((c["is"] == "item_count_at_least" and c["item"] == r.get("item")) or
                           (c["is"] == "gold_at_least" and "amount" in r and c["gold"] >= r["amount"])
                           for c in ln["conditions"])
            loose = [ln["id"] for ln in movers if not holds(ln)]
            loose += [t["id"] for t in trig if not (t["kind"] == "take" and fm.item_of(t["ref"]) == r.get("item"))]
            if loose:
                out.append(("take-unheld", f"stage {n} takes {what} from the player and is reached by "
                            f"{loose[0]}, which does not ask that it be held: give each way its own stage, or "
                            "gate the line on holding it"))
        for t in trig:
            if t["kind"] == "take" and fm.item_of(t["ref"]) in gives:
                out.append(("give-twice", f"stage {n} gives {fm.item_of(t['ref'])} and is reached by taking it "
                            f"(trigger {t['id']}): the player would hold two"))
    for ln in form["lines"]:
        for c in ln["conditions"]:
            if c["is"] == "rank_at_least" and c["faction"] not in factions_set:
                out.append(("rank-set", f"line {ln['id']} asks rank in {c['faction']}, which no stage of this file "
                            "gives: gate on the stage of the earlier quest that gave it, and keep that quest's sketch "
                            "in the same file"))
            if c["is"] == "number_compare" and c["number"] not in numbers_set:
                out.append(("number-set", f"line {ln['id']} reads the number {c['number']}, which no stage of this "
                            "file sets"))
    return out


def _second_placement(form, a, b) -> bool:
    """One person (or thing) met in two places: one starts off and is switched on, and the other is switched off."""
    refs = {r["id"]: r for r in form["refs"]}
    if a not in refs or b not in refs:
        return False
    res = {(r["do"], r.get("ref")) for s in form["stages"] for r in s["results"]}
    return any(not refs[x]["enabled"] and ("switch_on", x) in res and ("switch_off", y) in res
               for x, y in ((a, b), (b, a)))


def _same_stock(fm, a, b) -> bool:
    """Two of one stock item (three ash eggs): one thing, counted."""
    return a in fm.refs and b in fm.refs and fm.item_of(a) == fm.item_of(b) != a


def _reachable(fm: rules.Form, dead: str | None, frm: int | None = None) -> set[int]:
    """The stages reachable from `frm` (the start) by lines, triggers and results, the person `dead` speaking no
    line and every line that needs them alive shut."""
    start = fm.f["quest"]["start"]["stage"] if frm is None else frm
    seen, todo = {start}, [start]
    while todo:
        n = todo.pop()
        if fm.stages[n]["ending"] != "none":
            continue
        nxt = set(rules._stage_sets(fm.stages[n]["results"]))
        for ln in fm.open_lines(n):
            if dead and (ln["speaker"] == dead or {"is": "alive", "ref": dead} in ln["conditions"]):
                continue
            nxt |= set(rules._stage_sets(ln["results"]))
        nxt |= {t["sets"] for t in fm.open_triggers(n) if t.get("ref") != dead or t["kind"] != "use"}
        for m in nxt - seen:
            if m in fm.stages:
                seen.add(m)
                todo.append(m)
    return seen


# -- checking a file ----------------------------------------------------------------------------------------------

GLOSS = {
    "sketch": "the sketch cannot be read as written",
    "schema": "a part of the quest is missing or misspelt",
    "vocabulary": "a gate or result the game does not have",
    "unique-ids": "two parts share one id",
    "stages-exist": "a stage is named that the table does not have",
    "refs-exist": "a person, thing or door is named that the sketch does not declare",
    "placement": "a thing is placed where it cannot be (a container holds things; a person carries items)",
    "lock": "a lock is on something that is no door or container, or its key is not a thing",
    "owner": "an owner is on something that is not a thing, or is no person; or a giving names a thing with no owner",
    "contents": "what a container holds is stock items, not the quest's own things (put those `in` it)",
    "item-id": "an item is named by the wrong id",
    "journal-text": "a shown stage has no journal entry, or an ending does not show",
    "way-out": "a dead end: nothing moves the quest on from this stage (buildable.md, The shape that always works)",
    "reachable": "a stage nothing leads to",
    "objective-target-on": "a stage the player reads has no objective, or its marker points at someone switched off",
    "asked-is-target": "the thing to take or use, or the person whose line moves the quest, has no marker there",
    "completes-on-target": "an objective is done by someone or something its marker does not point at",
    "hand-in": "a hand-in that takes a thing is not gated on holding it, or is not open while the thing can be held",
    "held-take": "a thing taken before its stage would move nothing",
    "line-window": "a line is offered at stages that cannot both hold",
    "switch-cause": "a switch made where the player may be standing: switch only by a line, a take or a use",
    "away": "a switch made in sight: what is switched must stand in another indoor place, or a far outdoor one, "
            "from the speaker or thing that causes it",
    "must-live-fails": "a who-must-live row's stage is not a failed ending",
    "must-live-window": "a who-must-live row holds before the player has the quest",
    "main-message": "a minor quest's death shows no message",
    "death-hostile": "a death moves the quest, but the person is neither hostile nor marked the player's choice",
    "result-limits": "the quest holds more results than the engine allows",
    "speaks-first-has-line": "the person who speaks first has no topic that says the same",
    "stage-order": "stages out of order: every stage moves only to a higher one",
    "trigger": "one thing or person carries two triggers of a kind: let one move the quest",
    "speaks-first": "more than one person speaks first",
    "answer": "an answer is no question's answer",
    "prompt": "a topic has no words for the player",
    "speaker": "a line's speaker is not a person",
    "hostile": "only a new person of ours can be placed hostile",
    "created": "a thing in a container is there from the start and is taken, never switched or used",
    "line-said": "a line can never be said: an earlier line of the same person and words holds whenever it does",
    "regard-range": "regard runs -4 to 4, in steps of 1 to 4",
    "objective-left": "an objective stays shown after the quest moved on",
    "late-trigger": "a take, use or death can fire after the step it stands for",
    "check-label": "a check is not shown on the player's words",
    "set-start": "a quest is started more than one way, or by nothing",
    "set-stages": "another quest's stage is named that it does not have",
    "hostile-speaks": "a hostile person who must also speak, sell or hand over",
    "hostile-must-live": "a person to be fought whom the quest cannot go on without",
    "death-both-ways": "a death that both fails the quest and moves it on",
    "one-name": "one name for two things",
    "give-placed": "a person hands over a thing they do not hold",
    "dead-early": "a person killed before the stage that expects their death",
    "early-death": "a kill open before the player has the job",
    "needs-living": "a person the quest cannot go on without, not named",
    "number-set": "a number read that nothing sets",
    "rank-set": "a rank asked for that no quest in the file gives",
    "refusal": "a check with no refusal of its own",
    "take-unheld": "a hand-over the player may not be able to make: the stage takes what a way to it never asked for",
    "give-twice": "one thing given and taken: the player would hold two",
    "line-result": "a line does something besides moving a stage: every result belongs to a stage",
    "line-hostile": "a person who speaks and then turns hostile by a line",
    "body": "a body placed in the world",
    "reach": "a stage or ending no player reaches",
}


def _where(msg: str, src: dict) -> int | None:
    for pat, kind in ((r"line (\S+?)[:,) ]", "line"), (r"trigger (\S+?)[:,) ]", "trigger"),
                      (r"who-must-live (\S+?)[:,) ]", "must"), (r"objective (\d+)", "objective"),
                      (r"ref (\S+?)[:,) ]", "ref"), (r"stage (\d+)", "stage")):
        for m in re.finditer(pat, msg + " "):
            v = m.group(1)
            key = (kind, int(v)) if kind in ("objective", "stage") else (kind, v)
            if key in src:
                return src[key]
    return None


def check(path, quest: str | None = None, walk: bool = True, max_states: int | None = None) -> list[dict]:
    """Every fault of the sketches in `path` (or of the one quest `quest`, the others loaded with it), each {line,
    quest, rule, message, gloss}."""
    path = Path(path)
    faults = []
    sketches = read(path)
    forms, srcs = {}, {}
    for sk in sketches:
        for n, rule, msg in sk.errors:
            faults.append({"line": n, "quest": sk.qid, "rule": rule, "message": msg})
        form, src = expand(sk)
        if form is None:
            continue
        for n, rule, msg in form.pop("_errors"):
            faults.append({"line": n, "quest": sk.qid, "rule": rule, "message": msg})
        forms[sk.qid] = (form, sk)
        srcs[sk.qid] = src
    every = [f for f, _ in forms.values()]
    numbers_set = {r["number"] for f in every for s in f["stages"] for r in s["results"]
                   if r["do"] in ("set_number", "add_number")}
    factions_set = {r["faction"] for f in every for s in f["stages"] for r in s["results"]
                    if r["do"] in ("join_faction", "set_rank")}
    walkable = not faults
    for qid, (form, sk) in forms.items():
        fails = rules.check(form, every)
        walkable = walkable and not fails
        if quest and qid != quest:
            continue
        src = srcs[qid]
        if not any(r in ("schema", "vocabulary", "stages-exist", "refs-exist") for r, _ in fails):
            fails = fails + design(form, sk, numbers_set, factions_set)
        for rule, msg in fails:
            msg = msg.replace("sketch:", "")
            faults.append({"line": _where(msg, src) or src.get(("quest",)), "quest": qid, "rule": rule,
                           "message": msg})
    if forms and walkable:
        for rule, msg in rules.check_set(every):
            q = msg.split(":")[0]
            walkable = False
            faults.append({"line": srcs.get(q, {}).get(("start",)), "quest": q, "rule": rule, "message": msg})
    if walk and forms and walkable:
        faults += _reach(every, srcs, quest, max_states)
    out, seen = [], {}
    for f in faults:          # one fault per rule and story line: a line offered at several stages is one line
        key = (f["quest"], f["rule"], f["line"]) if f["line"] and f["rule"] != "_ok" else id(f)
        if key in seen:
            seen[key]["more"] += 1
            continue
        f["gloss"], f["more"] = GLOSS.get(f["rule"], ""), 0
        seen[key] = f
        out.append(f)
    return out


def _reach(every, srcs, quest, max_states) -> list[dict]:
    from tools.playtest import walk
    from tools.playtest import world as W
    world = W.snapshot(every, use_db=False)
    kw = {"max_states": max_states} if max_states else {}
    rows = walk.reach(every, world, only={quest} if quest else None, **kw)
    out = []
    for b in walk.unreached(rows):
        q = b.split(":")[0].split(",")[0]
        m = re.search(r"(?:stage|ending) (\d+) not reached", b)
        line = srcs.get(q, {}).get(("stage", int(m.group(1)))) if m else srcs.get(q, {}).get(("quest",))
        out.append({"line": line, "quest": q, "rule": "reach", "message": b})
    if not out:
        out.append({"line": None, "quest": None, "rule": "_ok", "message": walk.report(rows)})
    return out


def report(path, faults: list[dict]) -> tuple[str, int]:
    """The faults as the writer reads them, one block each, and the closing lines; (text, the number of faults)."""
    real = [f for f in faults if f["rule"] != "_ok"]
    out = []
    for f in sorted(real, key=lambda f: (f["line"] or 0, f["rule"])):
        where = f"{path}:{f['line']}" if f["line"] else str(path)
        more = f" (and {f['more']} more like it from this line)" if f.get("more") else ""
        out.append(f"{where}: {f['quest'] or ''} {f['rule']}: {f['message']}{more}")
        if f.get("gloss"):
            out.append(f"    meaning: {f['gloss']}")
    out.append("checked when built: " + "; ".join(CHECKED_WHEN_BUILT) + ".")
    ok = [f for f in faults if f["rule"] == "_ok"]
    if not real:
        out.append("reach: every stage and ending reached by an able character and a new one with gold, after each "
                   "ending of the quests before it" if ok else "reach: not walked")
    out.append(f"sketch: {path}: " + ("passes" if not real else f"{len(real)} fault(s)"))
    return "\n".join(out), len(real)


def main(path, quest=None, walk=True, show_paths=False) -> int:
    try:
        faults = check(path, quest, walk)
    except SketchError as e:
        print(f"sketch: {e}")
        return 1
    text, n = report(path, faults)
    if show_paths:
        for f in faults:
            if f["rule"] == "_ok":
                print(f["message"])
    print(text)
    return 1 if n else 0
