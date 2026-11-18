"""A quest record read as the play: what happens at each stage, what the player is told, and how one quest leads to
the next. Markdown for the story explorer's quest pages and a line's whole-story page; no ids are shown, every id
is mapped to the name the player sees. Spoken words come from a topic's written `lines` when it has them, else from
its `intent` (the gist the paper game plays)."""
from __future__ import annotations

import re

from tools.playtest.record import humanize

GIST_NOTE = ("Where a person's words are not written yet, what they say is given as its gist, from the quest record; "
             "written lines are quoted as they stand.")


def one(s) -> str:
    return re.sub(r"\s+", " ", str(s)).strip()


def _args(a) -> list:
    return a if isinstance(a, list) else [a]


def intent_parts(s: str) -> dict:
    """A topic intent split into its setting (before Tells), Tells, Checks and Does."""
    parts = re.split(r"\b(Tells|Checks|Does):\s*", one(s or ""))
    out = {"setting": parts[0].strip()}
    for k, v in zip(parts[1::2], parts[2::2]):
        out[k.lower()] = v.strip()
    return out


def code_of(qid: str) -> str:
    return str(qid).split(".")[-1].upper()


def link(code: str, title: str = "") -> str:
    return f"[{code}{'. ' + one(title) if title else ''}](#q-{code.lower()})"


from tools.playtest.record import world_place_names as _PLACE_NAMES  # noqa: E402,N812,F401 - the one helper


class Play:
    """One record's names and where things stand, for describing its play."""

    def __init__(self, q: dict, records: dict[str, dict] | None = None):
        self.q, self.records = q, records or {}
        self.names: dict[str, str] = {}
        for p in q.get("placements") or []:
            if isinstance(p, dict) and p.get("ref"):
                self.names[p["ref"]] = p.get("name") or p.get("placeName") or self.names.get(p["ref"], "")
        for t in q.get("things") or []:
            if isinstance(t, dict) and t.get("name"):
                self.names[t["id"]] = one(t["name"])
        for c in q.get("cast") or []:
            if isinstance(c, dict):
                per = c.get("persona") if isinstance(c.get("persona"), dict) else {}
                self.names[c["id"]] = c.get("name") or per.get("name") or self.names.get(c["id"]) or humanize(c["id"])
        self.place_of = {p["ref"]: p for p in q.get("placements") or [] if isinstance(p, dict) and p.get("ref")}
        self.things = {t["id"]: t for t in q.get("things") or [] if isinstance(t, dict) and t.get("id")}
        self.topics = {t["id"]: t for t in q.get("topics") or [] if isinstance(t, dict) and t.get("id")}
        self.messages = {m["id"]: m for m in q.get("messages") or [] if isinstance(m, dict) and m.get("id")}
        self.stages = [s for s in q.get("stages") or [] if isinstance(s, dict)]
        self.hooks = [h for h in q.get("hooks") or [] if isinstance(h, dict)]

    # ---- names --------------------------------------------------------------------------------------------------
    def name(self, i) -> str:
        i = str(i)
        if i in self.names and self.names[i]:
            return one(self.names[i])
        if i.startswith("quest."):
            r = self.records.get(i)
            return code_of(i) + (f" ({one(r['title'])})" if r else "")
        return humanize(i).replace("-", " ") if not i.startswith(("npc.", "thing.", "door.")) else humanize(i)

    def place(self, pid) -> str:
        """A place id named as the world's records name it (outpost-m11-m63 -> Reed-Sill Weir)."""
        return one(_PLACE_NAMES().get(str(pid)) or humanize(pid))

    def where(self, ref) -> str:
        """Where a person or thing stands, in a few words."""
        p = self.place_of.get(ref)
        if p and isinstance(p.get("anchor"), dict):
            a = p["anchor"]
            need = re.sub(r"\s*\([^)]*\)", "", one(a.get("need", ""))).split(";")[0].split(",")[0].strip()
            at = self.place(a.get("place")) if a.get("place") else ""
            if need and at and at.lower() not in need.lower():
                return f"{need}, at {at}"
            return need or at
        t = self.things.get(ref)
        if t and t.get("where"):
            return one(t["where"])
        if p and p.get("carriedBy"):
            return f"carried by {self.name(p['carriedBy'])}"
        if p and p.get("container"):
            return f"in {self.name(p['container'])}"
        return ""

    def who(self, ref) -> str:
        w, n = self.where(ref), self.name(ref)
        w = re.sub(rf"^{re.escape(n)}\s*,?\s*", "", w) if w else w
        return f"{n} ({w})" if w else n

    # ---- words --------------------------------------------------------------------------------------------------
    def said(self, t: dict) -> list[str]:
        """What a topic's speaker says: the written lines when the record has them, else the gist."""
        sp = self.name(t.get("person", ""))
        lines = t.get("lines")
        if isinstance(lines, str):
            lines = [lines]
        if lines:
            out = [f"**{sp}**, written lines{' (' + one(t['linesSource']) + ')' if t.get('linesSource') else ''}:"]
            return out + [f"*“{one(x.get('text', x) if isinstance(x, dict) else x)}”*" for x in lines]
        ip = intent_parts(t.get("intent", ""))
        setting = re.sub(rf"^{re.escape(sp)}[,.]?\s*", "", ip.get("setting", "")).strip().rstrip(".")
        if ip.get("tells"):
            out = [f"**{sp}**" + (f", {setting}," if setting else "") + " says (the gist):", f"*{ip['tells']}*"]
        else:
            out = [f"**{sp}** (the gist):", f"*{setting or one(t.get('intent', ''))}*"]
        if t.get("fallback"):
            out.append(f"If the player cannot meet what is asked, {sp} says: *“{one(t['fallback'])}”*")
        return out

    def ask(self, t: dict) -> str:
        k = t.get("kind")
        sp = self.name(t.get("person", ""))
        label = re.sub(r"^\(speaks first\)\s*", "", one(t.get("label", "")))
        if k == "speaks-first":
            return f"{self.who(t.get('person'))} speaks to you first: “{label}”"
        if k == "greeting":
            return f"{self.who(t.get('person'))} greets you: “{label}”"
        return f"you say to {self.who(t.get('person'))}: “{label}”" if sp else f"you pick “{label}”"

    def cond(self, c, topics: list | None = None) -> str:
        """A condition in plain words; topics heard are collected into `topics`."""
        if topics is None:
            topics = []
        if isinstance(c, list):
            return " and ".join(self.cond(x, topics) for x in c)
        if not isinstance(c, dict):
            return one(c)
        parts = []
        for k, a in c.items():
            a = _args(a)
            if k == "all":
                parts.append(" and ".join(self.cond(x, topics) for x in a))
            elif k == "any":
                parts.append("either " + ", or ".join(self.cond(x, topics) for x in a))
            elif k == "not":
                inner = a[0] if len(a) == 1 else a
                if isinstance(inner, dict) and "npcAlive" in inner:
                    parts.append(f"{self.name(_args(inner['npcAlive'])[0])} dies")
                elif isinstance(inner, dict) and "hasItem" in inner:
                    parts.append(f"you no longer carry {self.name(_args(inner['hasItem'])[0])}")
                else:
                    parts.append("it is not so that " + self.cond(inner, topics))
            elif k == "topicHeardFrom":
                t = self.topics.get(a[0])
                if t:
                    topics.append(t)
                    parts.append(self.ask(t))
                else:
                    parts.append(f"{self.name(a[1]) if len(a) > 1 else 'someone'} is asked about {self.name(a[0])}")
            elif k == "hasItem":
                n = a[1] if len(a) > 1 else 1
                w = self.where(a[0])
                parts.append(f"you have {self.name(a[0])}" + (f" ({n})" if n not in (1, "1") else "")
                             + (f", first found {w}" if w else ""))
            elif k == "npcAlive":
                parts.append(f"{self.name(a[0])} is alive")
            elif k in ("questStage", "stageEverReached"):
                op = a[1] if len(a) > 2 else "≥"
                n = a[-1]
                r = self.records.get(a[0])
                st = next((s for s in (r or {}).get("stages") or [] if str(s.get("id")) == str(n)), None)
                if st and st.get("ending") and op in ("=", "≥", ">="):
                    parts.append(f"{self.name(a[0])} ends at its stage {n}")
                elif a[0] == self.q.get("id"):
                    parts.append(f"this quest reaches stage {n}")
                else:
                    parts.append(f"{self.name(a[0])} reaches stage {n}")
            elif k == "flag":
                h = next((h for h in self.hooks if h.get("setsFlag") == a[0]), None)
                if h:
                    verb = "read" if h.get("hook") == "read" else "use"
                    w = self.where(h.get("thing"))
                    parts.append(f"you {verb} {self.name(h.get('thing'))}" + (f" ({w})" if w else ""))
                else:
                    parts.append(f"{self.name(a[0])} is so" if a[1:] in ([], [True]) else f"{self.name(a[0])} is {a[1]}")
            elif k == "goldAtLeast":
                parts.append(f"you carry at least {a[0]} gold")
            elif k == "skillAtLeast":
                parts.append(f"your {a[0]} is at least {a[1] if len(a) > 1 else ''}".strip())
            elif k == "objectiveComplete":
                parts.append(f"the objective {a[-1]} is done")
            elif k == "counterAtLeast":
                parts.append(f"{self.name(a[0])} reaches {a[1] if len(a) > 1 else ''}".strip())
            elif k == "spellCastNear":
                parts.append(f"you cast {self.name(a[0])} near {self.name(a[1]) if len(a) > 1 else 'it'}")
            else:
                parts.append(f"{humanize(k)} {', '.join(self.name(x) for x in a)}")
        return " and ".join(parts)

    def act(self, a) -> str:
        if not isinstance(a, dict) or len(a) != 1:
            return ""
        (k, v), = a.items()
        v = _args(v)
        n = lambda: self.name(v[0])  # noqa: E731
        return {"takeItem": lambda: f"{n()} is taken from you",
                "removeItem": lambda: f"{n()} is taken from you",
                "giveItem": lambda: f"you are given {n()}" + (f" ({v[1]})" if len(v) > 1 and v[1] != 1 else ""),
                "giveGold": lambda: f"you are given {v[0]} gold",
                "takeGold": lambda: f"{v[0]} gold is taken from you",
                "removeGold": lambda: f"{v[0]} gold is taken from you",
                "enableRef": lambda: f"{n()} is now there" + (f" ({self.where(v[0])})" if self.where(v[0]) else ""),
                "disableRef": lambda: f"{n()} is gone",
                "killNpc": lambda: f"{n()} dies", "killRef": lambda: f"{n()} dies",
                "grantMapMarker": lambda: f"{n()} is marked on your map",
                "setFactionRank": lambda: f"you are given a place in {n()}",
                "giveHome": lambda: f"{n()} is now your home",
                "grantAbility": lambda: f"you gain {n()}",
                "fadeToBlack": lambda: "the screen fades to black",
                "makePeace": lambda: f"{n()} is no longer hostile", "makeEnemy": lambda: f"{n()} turns hostile",
                }.get(k, lambda: "")()

    # ---- the play -----------------------------------------------------------------------------------------------
    def into(self, sid) -> list[tuple[list, object, str]]:
        """Every way into a stage: (from stages, condition, kind), same conditions merged."""
        ways: dict[str, list] = {}
        for s in self.stages:
            for kind in ("successors", "failForward"):
                for x in s.get(kind) or []:
                    if isinstance(x, dict) and str(x.get("to")) == str(sid):
                        key = repr(x.get("when"))
                        if key not in ways:
                            ways[key] = [[], x.get("when"), kind]
                        ways[key][0].append(s["id"])
        return [tuple(w) for w in ways.values()]

    def opened(self, sid) -> list[dict]:
        """Topics that first become open at this stage."""
        return [t for t in self.topics.values() if (t.get("stages") or [None])[0] == sid]

    def moves(self, t: dict) -> str | None:
        """The stage a topic moves the quest to, if any."""
        for s in self.stages:
            for x in [*(s.get("successors") or []), *(s.get("failForward") or [])]:
                if isinstance(x, dict) and re.search(rf"'{re.escape(t['id'])}'", repr(x.get("when"))):
                    return str(x.get("to"))
        return None

    def start_words(self) -> str:
        sw = self.q.get("startWhen")
        return f"The quest begins when {self.cond(sw)}." if sw else "The quest begins at the start of the game."

    def stage_play(self, s: dict, lvl: str = "####", journal_only: bool = False) -> list[str]:
        """What happens, what the player is told, then (unless journal_only is False for the page) the rest."""
        out: list[str] = []
        sid = s["id"]
        heard: list[dict] = []
        if sid == self.q.get("start"):
            out.append(f"**What happens.** {self.start_words()}")
        ways = self.into(sid)
        for frm, when, kind in ways:
            frm_s = ", ".join(map(str, frm))
            lead = (f"At any point from stage {frm_s}, if " if kind == "failForward" and len(frm) > 1
                    else f"From stage {frm_s}, when ")
            words = self.cond(when, heard)
            label = "What happens" if len(ways) == 1 else "One way it happens"
            out.append(f"**{label}.** {lead}{words}.")
        acts = [x for x in map(self.act, s.get("onEnter") or []) if x]
        if acts:
            out.append("**Then.** " + "; ".join(a[0].upper() + a[1:] for a in acts) + ".")
        told = []
        for t in heard:
            told += self.said(t)
        for a in s.get("onEnter") or []:
            if isinstance(a, dict) and "showMessage" in a:
                m = self.messages.get(_args(a["showMessage"])[0])
                if m and m.get("text"):
                    told += ["A message appears on the screen:", f"*“{one(m['text'])}”*"]
        if told:
            out.append("**What you are told.**")
            out += told
        if journal_only:
            if s.get("journalText"):
                out.append(f"**Journal.** *{one(s['journalText'])}*")
            return out
        ended = next((e for e in self.q.get("endings") or [] if e.get("id") == s.get("endingId")), None)
        if ended:
            gives = [x for x in map(self.act, [*(ended.get("rewards") or []), *(ended.get("world") or [])]) if x]
            if gives:
                out.append("**At the end.** " + "; ".join(g[0].upper() + g[1:] for g in gives) + ".")
        new = [t for t in self.opened(sid) if t not in heard]
        if new:
            out.append("**New things to ask from here.**")
            items = []
            for t in new:
                ip = intent_parts(t.get("intent", ""))
                to = self.moves(t)
                lab = re.sub(r"^\(speaks first\)\s*", "", one(t.get("label", "")))
                if to:
                    items.append(f"“{lab}”, asked of {self.name(t.get('person'))}: this moves the quest on to stage {to}"
                                 f"{', where the answer is given' if to != str(sid) else ''}.")
                else:
                    gist = ip.get("tells") or one(t.get("intent", ""))
                    items.append(f"“{lab}”, asked of {self.name(t.get('person'))}: {gist}")
            out.append("- " + "\n- ".join(items))
        return out

    def stage_rest(self, s: dict) -> list[str]:
        out = []
        if s.get("journalText"):
            out.append(f"**Journal.** *{one(s['journalText'])}*")
        for o in s.get("objectives") or []:
            if isinstance(o, dict) and o.get("objectiveText"):
                t = o.get("target")
                w = self.where(t) if t else ""
                out.append(f"**Objective.** {one(o['objectiveText'])}"
                           + (f" The marker points at {self.name(t)}" + (f", {w}" if w else "") + "." if t else ""))
        info = s.get("information") if isinstance(s.get("information"), dict) else {}
        for k, lab in (("going", "What is going on"), ("next", "What to do next"), ("ways", "Ways through")):
            if info.get(k):
                out.append(f"**{lab}.** {one(info[k])}")
        if s.get("directions"):
            out.append(f"**Directions.** {one(s['directions'])}")
        carriers = [c for c in info.get("carriers") or [] if isinstance(c, dict)]
        if carriers:
            out.append("**How the player knows each thing.**")
            out.append("- " + "\n- ".join(self.carrier(c) for c in carriers))
        return out

    def carrier(self, c: dict) -> str:
        know = c.get("know")
        if not know:  # a key the YAML split at a comma
            know = next((k for k in c if k != "by"), "")
        by = []
        for b in _args(c.get("by") or []):
            b = str(b)
            k, _, v = b.partition(":")
            t = self.topics.get(v)
            lab = f"“{one(t.get('label', ''))}”" if t else ""
            by.append({"journal": "the journal", "objective": "the objective",
                       "marker": f"the map marker on {self.name(v)}", "name": f"the name {self.name(v)} shows",
                       "line": f"what {self.name(t.get('person')) if t else 'someone'} answers to {lab}",
                       "ask": f"asking {self.name(t.get('person')) if t else 'someone'} {lab}",
                       "look": f"seeing {self.name(v)}", "read": f"reading {self.name(v)}",
                       "message": f"the message on the screen at stage {v}"}.get(k, one(b)))
        return f"{one(know)[:1].upper()}{one(know)[1:]}: " + ", ".join(by) + "."

    def readables(self) -> list[str]:
        out = []
        for t in self.things.values():
            if t.get("text"):
                w = f" ({one(t['where'])})" if t.get("where") else ""
                out += [f"**{one(t.get('name', ''))}**{w}:", f"*“{one(t['text'])}”*"]
        for p in self.place_of.values():
            if p.get("text") and p["ref"] not in self.things:
                out += [f"**{self.name(p['ref'])}**:", f"*“{one(p['text'])}”*"]
        return out


def ending_stages(q: dict) -> list[dict]:
    return [s for s in q.get("stages") or [] if isinstance(s, dict) and s.get("ending")
            and str(s.get("ending")) in ("complete", "True", "true")]


def follows(q: dict, records: dict[str, dict]) -> list[tuple[dict, object]]:
    """The quests this one follows (named in its startWhen), with the stage it starts from."""
    found = []
    for m in re.finditer(r"'(quest\.[\w.-]+)', '[^']*', (\d+)", repr(q.get("startWhen"))):
        if m.group(1) in records:
            found.append((records[m.group(1)], m.group(2)))
    return found


def before_this(q: dict, records: dict[str, dict]) -> list[str]:
    prev = follows(q, records)
    if not prev:
        return ["Nothing comes before this quest: it is where the story begins."] if q.get("startWhen") is None else \
            [Play(q, records).start_words()]
    out = []
    for r, st in prev:
        s = next((x for x in r.get("stages") or [] if str(x.get("id")) == st), None)
        out.append(f"This follows {link(r['code'], r['title'])}, from its stage {st}.")
        if s and s.get("journalText"):
            out.append(f"**Where that left you.** *{one(s['journalText'])}*")
        info = (s or {}).get("information") or {}
        if info.get("going"):
            out.append(f"**What you know.** {one(info['going'])}")
        others = [e for e in ending_stages(r) if str(e["id"]) != st]
        for e in others:
            out.append(f"Another way {r['code']} can end (stage {e['id']}): *{one(e.get('journalText', ''))}*")
    return out


def leads_on(q: dict, records: dict[str, dict]) -> list[str]:
    out = []
    nxt = [(r, st) for r in records.values() for (p, st) in follows(r, records) if p["id"] == q["id"]]
    for r, st in sorted(nxt, key=lambda x: x[0]["code"]):
        rp = Play(r, records)
        first = next((s for s in rp.stages if s["id"] == r.get("start")), rp.stages[0] if rp.stages else None)
        out.append(f"From stage {st} of this quest, {link(r['code'], r['title'])} begins.")
        if first and first.get("journalText"):
            out.append(f"**Its first beat.** *{one(first['journalText'])}*")
        objs = [one(o["objectiveText"]) for o in (first or {}).get("objectives") or [] if o.get("objectiveText")]
        if objs:
            out.append("**Its first objective.** " + " ".join(objs))
    if not nxt:
        out.append("No quest record follows this one yet.")
    return out


def stage_heading(p: Play, s: dict) -> str:
    return f"Stage {s['id']}" + (f" at {p.place(s['place'])}" if s.get("place") else "")


def whole_story(title: str, recs: list[dict], records: dict[str, dict]) -> str:
    """A line's quests, every beat in order, on one page: each quest's beats told as the play, no ids."""
    from tools.newworld import quest_graph as QG
    out = [f"# {title}: the whole story", GIST_NOTE]
    for q in recs:
        p = Play(q, records)
        w = QG.Words(p, records)
        out.append(f"## {q['code']}. {one(q['title'])}")
        if q.get("premise"):
            out.append(f"*{w.scrub(one(q['premise']))}*")
        for b in QG.beats(q, records):
            head = b["title"] + (f", at {b['place']}" if b.get("place") else "")
            out.append(f"### {q['code']}: {head}")
            out += [re.sub(r"\[([^\]]+)\]\(#beat-[\w-]+\)", r"\1", x) for x in b["prose"]]
        nx = leads_on(q, records)
        out.append("**Leads on.** " + " ".join(x for x in nx if not x.startswith("**")))
    return "\n\n".join(out) + "\n"
