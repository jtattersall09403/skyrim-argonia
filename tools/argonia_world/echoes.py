"""Echo windows: who the player hears within one space and one stretch of play, and what each of them owns saying.

A window is where lines meet the player in quick succession, over the slice (the live quests and every talker):
- a quest stage at its place (`MQ01 stage 10 at lilmoth`): every quest topic live at that stage (the record's topic
  stages; the lines in story/data/quest_lines/<code>.json or the written `dialogue_line` rows), every quest person
  whose `when` covers it (quest_lines/quest_people.json; stage 0 is before the quest starts, at its first stage's
  place);
- a settlement (`talk bmv.lilmoth`): every talker of it (`bmv_talker.settlement`); a talker also stands in the quest
  windows whose place is their settlement (place id's last part and the settlement id's, letters only, match).
Windows come from the records alone, so they follow a quest when its places or stages change.

Within a window each fact has one owner: the speaker of the first topic that states it, in the order the player meets
them (quest topics in record order, then quest people, then talkers in `talker_topic` order). The others say their
own thing and may point to the owner by name; `brief_section` writes that for a brief, and `clusters` is the check.
A cluster, unless `echoes.yaml` (dialogue-write) names it:
- fact: two different speakers of one window state one fact id;
- clause: two different speakers share a run of `SHARED` words, `CONTENT` of them more than glue, numbers and compass
  points (two routes, `talk.directions`, may name the same landmark alike);
- again: one speaker says such a run in two different topics (a topic's variants are alternatives, heard once);
- opening: two greetings' first sentences carry the same content words (one row per window, everyone named).
`assign` gives each talk fact one holder in its settlement and points the others to them.

    python3 -m tools.argonia_world.echoes check [--allow PATH] [--window SUBSTRING]
    python3 -m tools.argonia_world.echoes assign --settlement S [--owner FACT=REF] [--write]
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import pathlib
import re
import sys

import yaml

from tools.argonia_world import db, quest_record, records

ROOT = pathlib.Path(__file__).resolve().parents[2]
LINES = ROOT / "story" / "data" / "quest_lines"
ALLOW = ROOT / ".claude" / "skills" / "dialogue-write" / "echoes.yaml"
SHARED, CONTENT = 7, 4
STOP = set("""a an the and or but if so of to in on at by for from with into onto over under up down out off as is was
are were be been being am do does did done have has had having i me my mine you your yours we us our ours he him his
she her hers it its they them their theirs this that these those there here then than when where who whom whose which
what why how not no nor never all any each every some one ones too very just only also still even yet again more most
will would can could shall should may might must let lets s t d ll ve re""".split())
NUMBER = set("""zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen
seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred hundreds thousand half
dozen few some about or so""".split())
COMPASS = {"north", "south", "east", "west", "northeast", "northwest", "southeast", "southwest"}


@dataclasses.dataclass
class Speech:
    """One speaker's lines on one topic: where it comes from, who says it, what it states and where it is heard."""
    source: str                 # quest_lines/mq01.json, quest_people.json, talk_line
    key: str                    # topic id / quest-people base / talker ref + topic
    speaker: str                # identity: letters of the name, lower case
    name: str
    topic: str                  # prompt or topic id
    texts: list[str]
    facts: list[str]
    windows: set[str]
    order: int = 0


def ident(name: str) -> str:
    return re.sub(r"[^a-z]", "", (name or "").lower())


def _texts(obj: dict) -> list[str]:
    """Every spoken line of a topic or info: each key holding a list of strings, except `facts` and `when`."""
    return [s for k, v in obj.items() if k not in ("facts", "when") and isinstance(v, list)
            for s in v if isinstance(s, str)]


def _quest_ids(w) -> dict[str, str]:
    """The slice: the quests that are live (built into the game)."""
    return {q.code.lower(): q.id for q in w.rows("quest") if q.code and q.status == "live"}


class Windows:
    """The quest records' stage places, read once."""

    def __init__(self, w):
        self.w, self.ids, self.rec = w, _quest_ids(w), {}

    def record(self, code: str) -> dict | None:
        code = code.lower()
        if code not in self.rec:
            try:
                self.rec[code] = quest_record.export(self.w, self.ids[code]) if code in self.ids else None
            except KeyError:
                self.rec[code] = None
        return self.rec[code]

    def stages(self, code: str) -> list[tuple[int, str]]:
        """(stage, place letters) for stage 0 and every record stage, in order."""
        q = self.record(code)
        st = sorted((s["id"], (s.get("place") or "").split(".")[-1]) for s in (q or {}).get("stages", []))
        return ([(0, st[0][1])] + st) if st else []

    def at(self, code: str, keep) -> set[str]:
        return {f"{code.upper()} stage {s} at {p}" for s, p in self.stages(code) if keep(s)}


def quest_speech(w, win: Windows, root: pathlib.Path = LINES) -> list[Speech]:
    out = []
    for path in sorted(root.glob("*.json")):
        if path.name == "quest_people.json":
            continue
        code = path.stem
        q = win.record(code) or {}
        stages = {t["id"]: set(t["stages"]) for t in q.get("topics", [])}
        names = {}
        for topic, body in json.loads(path.read_text()).items():
            if topic.startswith("_") or not isinstance(body, dict):
                continue
            pid = body.get("speaker", "")
            if pid not in names:
                names[pid] = (records.person(w, pid) or {}).get("name") or next(
                    (c.get("persona", {}).get("name") for c in q.get("cast", []) if c["id"] == pid), None) or pid
            live = stages.get(topic, set())
            windows = win.at(code, lambda s, live=live: s in live)
            for info in body.get("infos", [body]):
                out.append(Speech(f"quest_lines/{path.name}", f"{topic}#{info.get('variant', 'main')}", ident(names[pid]),
                                  names[pid], info.get("prompt", topic), _texts(info), list(info.get("facts", [])),
                                  windows))
    return out


def people_speech(w, win: Windows, path: pathlib.Path = LINES / "quest_people.json") -> list[Speech]:
    out = []
    for base, entries in json.loads(path.read_text()).items():
        if base.startswith("_"):
            continue
        code = base.split("_")[1]
        for e in entries:
            name = e.get("speaker") or re.sub(r"(?<=[a-z])(?=[A-Z])", "-", base.split("_", 2)[2])
            if e.get("when"):
                quest, lo, hi = e["when"]
                windows = win.at(quest.split("_")[1], lambda s, lo=lo, hi=hi: lo <= s < hi)
            else:
                windows = win.at(code, lambda s: True)
            out.append(Speech("quest_people.json", base, ident(name), name, e["prompt"], _texts(e),
                              list(e.get("facts", [])), windows))
    return out


def talk_speech(w, win: Windows) -> list[Speech]:
    census = {t.id: t for t in w.rows("bmv_talker")}
    lines: dict[tuple[str, str], list[str]] = {}
    for ln in sorted(w.rows("talk_line"), key=lambda r: (r.talker, r.topic, r.ord)):
        lines.setdefault((ln.talker, ln.topic), []).append(ln.text)
    quests = {}
    for code in win.ids:
        for s, p in win.stages(code):
            quests.setdefault(ident(p), set()).add(f"{code.upper()} stage {s} at {p}")
    talkers = {t.id: t for t in w.rows("talker")}
    out = []
    for tt in w.rows("talker_topic"):
        t, c = talkers.get(tt.talker), census.get(tt.talker)
        if t is None or c is None or not c.settlement or (tt.talker, tt.topic) not in lines:
            continue
        place = ident(c.settlement.split(".")[-1])
        windows = {f"talk {c.settlement}"} | quests.get(place, set())
        facts = [f.strip() for f in (tt.facts or "").split(",") if f.strip()]
        out.append(Speech("talk_line", f"{tt.talker} {tt.topic}", ident(t.known_as), t.known_as, tt.topic,
                          lines[(tt.talker, tt.topic)], facts, windows))
    return out


def line_speech(w, win: Windows) -> list[Speech]:
    """Written `dialogue_line` rows of a slice quest's topics (MQ04, MQ05: QuestKit reads them), at that topic's
    record stages."""
    stages: dict[str, tuple[str, set]] = {}
    for code in win.ids:
        for t in (win.record(code) or {}).get("topics", []):
            stages[t["id"]] = (code, set(t["stages"]))
    names: dict[str, str] = {}
    out = []
    for r in w.query("SELECT * FROM dialogue_line WHERE status = 'written' ORDER BY id"):
        pid = r["speaker"] or ""
        if pid not in names:
            names[pid] = (records.person(w, pid) or {}).get("name") or pid
        topic = r["keys_topic"] or r["slot"] or r["id"]
        if topic in stages:
            code, live = stages[topic]
            windows = win.at(code, lambda s, live=live: s in live)
        else:
            continue
        texts = [x for x in (r["words"], r["variants_low"], r["variants_high"]) if x]
        out.append(Speech("dialogue_line", f"{topic}#{r['id']}", ident(names[pid]), names[pid], topic, texts, [],
                          windows))
    return out


def record_speech(w, win: Windows, q: dict) -> list[Speech]:
    """A quest record's topics as speech before any line is written: each topic states its `uses`, at its stages."""
    out = []
    for t in q.get("topics", []):
        r = records.person(w, t["person"]) or {}
        name = r.get("name") or next((c.get("persona", {}).get("name") for c in q.get("cast", [])
                                      if c["id"] == t["person"]), None) or t["person"]
        live = set(t["stages"])
        out.append(Speech(f"record {q['code']}", t["id"], ident(name), name, t.get("label") or t["id"], [],
                          list(t.get("uses", [])), win.at(q["code"], lambda s, live=live: s in live)))
    return out


def speech(w=None, record: dict | None = None) -> list[Speech]:
    """Everything said in the slice, in play order. With `record` (a quest record export), that quest's topics come
    from the record (what each topic may state) in place of its written lines, so a brief can be built first."""
    w = w or db.open()
    win = Windows(w)
    quests = quest_speech(w, win)
    lines = line_speech(w, win)
    if record is not None:
        quests = record_speech(w, win, record) + [s for s in quests
                                                  if s.source != f"quest_lines/{record['code'].lower()}.json"]
        mine = {t["id"] for t in record.get("topics", [])}
        lines = [s for s in lines if s.topic not in mine]
    items = quests + lines + people_speech(w, win) + talk_speech(w, win)
    for i, s in enumerate(items):
        s.order = i
    return items


def claims(w) -> dict[str, str]:
    """Every fact's claim: the quest facts and the talk facts."""
    out = {r["id"]: r["claim"] for r in w.query("SELECT id, claim FROM fact")}
    out.update({f.id: f.claim for f in w.rows("talk_fact")})
    return out


# --- the check -------------------------------------------------------------------------------------------------------

def words(text: str) -> list[str]:
    """Lower-case words with every number word and compass point folded to one mark each (# and ~), runs collapsed."""
    out = []
    for t in re.findall(r"[a-z]+", text.lower()):
        t = "#" if t in NUMBER else "~" if t in COMPASS else t
        if not (out and t in "#~" and out[-1] == t):
            out.append(t)
    return out


def shared_clauses(a: list[str], b: list[str], n: int = SHARED, content: int = CONTENT) -> list[str]:
    """Runs of `n` words found in both texts with at least `content` words that are not glue or marks."""
    def grams(texts):
        g = set()
        for t in texts:
            ws = words(t)
            g |= {tuple(ws[i:i + n]) for i in range(len(ws) - n + 1)}
        return g
    hits = grams(a) & grams(b)
    return sorted(" ".join(g) for g in hits if sum(x not in STOP and x not in "#~" for x in g) >= content)


OPENED = {"talk.greet-friend", "talk.greet-stranger"}     # topics whose first sentence is a set phrase people copy


def same_opening(a: list[str], b: list[str]) -> bool:
    """Two greetings open alike: the content words of one's first sentence are all in the other's (two or more)."""
    def first(texts):
        return {x for x in words(re.split(r"[.!?]", texts[0])[0]) if x not in STOP and x not in "#~"} if texts else set()
    x, y = first(a), first(b)
    small, big = sorted((x, y), key=len)
    return len(small) >= 2 and small <= big


@dataclasses.dataclass
class Cluster:
    window: str
    kind: str                   # fact | clause (two speakers) | again (one speaker, two topics) | opening
    what: str                   # the fact id or the shared clause
    speakers: list[str]         # names
    keys: list[str]


def load_allow(path: pathlib.Path = ALLOW) -> list[dict]:
    return (yaml.safe_load(path.read_text()) or []) if path.exists() else []


def allowed(c: Cluster, allow: list[dict]) -> bool:
    """An allow entry names a fact id or a clause, the speakers (all of them, by name) and why."""
    for a in allow:
        if a.get("fact", a.get("clause")) is None or not a.get("why"):
            continue
        if a.get("fact") and (c.kind != "fact" or a["fact"] != c.what):
            continue
        if a.get("clause") and (c.kind == "fact" or a["clause"] not in c.what):
            continue
        if a.get("speakers") and not {ident(s) for s in c.speakers} <= {ident(s) for s in a["speakers"]}:
            continue
        return True
    return False


def by_window(items: list[Speech]) -> dict[str, list[Speech]]:
    out: dict[str, list[Speech]] = {}
    for s in items:
        for wdw in s.windows:
            out.setdefault(wdw, []).append(s)
    return out


def clusters(items: list[Speech], allow: list[dict] | None = None) -> list[Cluster]:
    """Every fact or long clause two different speakers of one window both say; one row per (fact or clause, set of
    speakers), at its first window."""
    allow = allow or []
    seen, out = set(), []
    # a settlement's own window first, so a talker's echo is reported where it is heard most
    for wdw, group in sorted(by_window(items).items(), key=lambda kv: (not kv[0].startswith("talk "), kv[0])):
        facts: dict[str, list[Speech]] = {}
        for s in group:
            for f in s.facts:
                facts.setdefault(f, []).append(s)
        found = [("fact", f, ss) for f, ss in facts.items() if len({s.speaker for s in ss}) > 1]
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                if a.speaker == b.speaker:
                    # one person saying the same thing twice in different topics (a topic's variants are
                    # alternatives the player hears one of)
                    if a.key.split("#")[0] != b.key.split("#")[0]:
                        found += [("again", cl, [a, b]) for cl in shared_clauses(a.texts, b.texts)]
                    continue
                if not (a.topic == b.topic == "talk.directions"):   # two routes past one landmark name it alike
                    found += [("clause", cl, [a, b]) for cl in shared_clauses(a.texts, b.texts)]
                if a.topic in OPENED and a.topic == b.topic and same_opening(a.texts, b.texts):
                    found.append(("opening", a.texts[0].split(".")[0], [a, b]))
        for kind, what, ss in found:
            names = sorted({s.name for s in ss})
            tag = (kind, what if kind == "fact" else "", tuple(names), tuple(sorted({s.key for s in ss})))
            if tag in seen:
                continue
            seen.add(tag)
            c = Cluster(wdw, kind, what, names, sorted({s.key for s in ss}))
            if not allowed(c, allow):
                out.append(c)
    # one clause row per speaker pair and key pair: the longest shared run stands for its overlapping n-grams
    # and one opening row per window, naming everyone whose greeting opens like another's
    merged: dict[tuple, Cluster] = {}
    for c in out:
        k = (c.kind, c.window) if c.kind == "opening" else (c.kind, c.what if c.kind == "fact" else "", tuple(c.keys))
        if k not in merged:
            merged[k] = c
        elif c.kind == "opening":
            m = merged[k]
            m.speakers, m.keys = sorted(set(m.speakers) | set(c.speakers)), sorted(set(m.keys) | set(c.keys))
            m.what = f"{len(m.speakers)} greetings open alike"
    return list(merged.values())


# --- the brief section -----------------------------------------------------------------------------------------------

def owners(items: list[Speech]) -> dict[tuple[str, str], Speech]:
    """(window, fact) -> the speaker who owns saying it there: the first in play order."""
    out = {}
    for s in sorted(items, key=lambda x: x.order):
        for wdw in s.windows:
            for f in s.facts:
                out.setdefault((wdw, f), s)
    return out


def brief_section(items: list[Speech], speaker: str, claims: dict[str, str] | None = None,
                  topics: set[str] | None = None) -> list[str]:
    """The 'Already said near you' lines for one speaker (a name): per window they stand in, who else speaks there,
    which facts each owns and the facts this speaker must leave to its owner. `topics` limits a talker's neighbours to
    the topics this speaker also answers (a settlement holds dozens of people)."""
    me = ident(speaker)
    claims = claims or {}
    mine = [s for s in items if s.speaker == me]
    own = owners(items)
    L = ["## Already said near you", "",
         "These people stand in the same place during the same stretch of play, and the player hears them one after "
         "another. Each fact below is theirs to say: do not restate it. Say what only you would say, from your own "
         "work and stake; where the player needs the fact, point to its owner by name (\"ask Wuleen-Sei about the "
         "months\") in a few words. Do not reuse their wording.", ""]
    here = {x for s in mine for x in s.windows}
    keep = topics if topics is not None else TELLABLE
    others: dict[str, list[Speech]] = {}
    for s in items:
        if s.speaker != me and s.windows & here and (s.source != "talk_line" or s.topic in keep):
            others.setdefault(s.name, []).append(s)
    if not others:
        return L + ["- Nobody else speaks near this person.", ""]
    for name, ss in others.items():
        shared = sorted({x for s in ss for x in s.windows & here})
        fs = sorted({f for s in ss for f in s.facts for x in shared if own.get((x, f)) in ss})
        row = f"- {name} ({compact(shared)}): answers {', '.join(sorted({s.topic for s in ss}))}"
        if fs:
            row += "; owns " + "; ".join(f"`{f}`" + (f" ({_short(claims[f])})" if f in claims else "") for f in fs)
        L.append(row)
    give_up = sorted({f"- `{f}`: {o.name} says it ({x}); you only point to {o.name}."
                      for s in mine for f in s.facts for x in s.windows
                      if (o := own.get((x, f))) is not None and o.speaker != me})
    if give_up:
        L += ["", "### Facts you leave to their owner", ""] + give_up
    return L + [""]


TELLABLE = {"talk.lore", "talk.rumours", "talk.someone", "talk.secret"}   # a talker's knowledge a quest line could echo


def compact(windows) -> str:
    """'MQ01 stages 40, 41, 90 at hereguard-plantation; talk bmv.lilmoth' from the window names."""
    by: dict[tuple, list[str]] = {}
    for x in sorted(windows):
        m = re.match(r"(\S+) stage (\d+) at (.+)", x)
        by.setdefault((m[1], m[3]) if m else (x, None), []).extend([m[2]] if m else [])
    return "; ".join(f"{k[0]} stage{'s' if len(v) > 1 else ''} {', '.join(sorted(v, key=int))} at {k[1]}"
                     if k[1] else k[0] for k, v in by.items())


def _short(text: str, n: int = 110) -> str:
    return text if len(text) <= n else text[:n].rsplit(" ", 1)[0] + "..."


POINTER = "echo: owner "


def assign(w, settlement: str, owner: dict[str, str] | None = None, write: bool = False) -> list[str]:
    """One holder for each talk fact of a settlement: a fact several talkers cite stays with its owner (`owner`
    fact -> talker ref, else the first talker by ref) and every other holder cites a pointer fact instead
    (`<fact>.ask-<ref6>`: "Ask <owner> about it: <claim>", source "echo: owner <ref> holds <fact>"), so their line
    names the owner and the subject and never tells it. A quest rumour named in echoes.yaml stays shared. Returns
    one line per change; writes the talker_topic and talk_fact rows when `write`."""
    owner = owner or {}
    keep = {a["fact"] for a in load_allow() if a.get("fact")}
    census = {t.id: t for t in w.rows("bmv_talker")}
    talkers = {t.id: t for t in w.rows("talker")}
    facts = {f.id: f for f in w.rows("talk_fact")}
    rows = [tt for tt in w.rows("talker_topic") if tt.talker in talkers
            and getattr(census.get(tt.talker), "settlement", None) == settlement]
    holders: dict[str, list] = {}
    for tt in sorted(rows, key=lambda r: (r.talker, r.topic)):
        for f in (tt.facts or "").split(","):
            if f.strip() and f.strip() in facts:
                holders.setdefault(f.strip(), []).append(tt)
    out = []
    now = {(tt.talker, tt.topic): tt.facts or "" for tt in rows}   # a topic may give up two facts: edit it in turn
    for fid, tts in sorted(holders.items()):
        if len({tt.talker for tt in tts}) < 2 or fid in keep:
            continue
        own = owner.get(fid) or tts[0].talker
        if own not in {tt.talker for tt in tts}:
            raise KeyError(f"{fid}: {own} does not hold it")
        name = talkers[own].known_as
        for tt in tts:
            if tt.talker == own:
                continue
            pid = f"{fid}.ask-{tt.talker[:6].lower()}"
            cited = [x.strip() for x in now[(tt.talker, tt.topic)].split(",") if x.strip()]
            new = now[(tt.talker, tt.topic)] = ", ".join(pid if x == fid else x for x in cited)
            out.append(f"{settlement} {fid}: {talkers[tt.talker].known_as} ({tt.topic}) points to {name}")
            if write:
                f = facts[fid]
                w.upsert("talk_fact", id=pid, topic=tt.topic, settlement=f.settlement,
                         claim=f"Ask {name} about it: {f.claim}", source=f"{POINTER}{own} holds {fid}")
                w.update("talker_topic", tt.talker, tt.topic, facts=new)
    if write and out:
        w.save()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["check", "assign"])
    ap.add_argument("--allow", default=str(ALLOW))
    ap.add_argument("--window", help="check: report only windows containing this text")
    ap.add_argument("--settlement", action="append", help="assign: the settlements (bmv.lilmoth ...)")
    ap.add_argument("--owner", action="append", default=[], help="assign: FACT=REF, the talker who keeps a fact")
    ap.add_argument("--write", action="store_true", help="assign: write the rows (else print the plan)")
    a = ap.parse_args()
    if a.cmd == "assign":
        w = db.open()
        own = dict(x.split("=", 1) for x in a.owner)
        for s in a.settlement or []:
            print("\n".join(assign(w, s, own, a.write)) or f"{s}: every fact has one holder")
        return 0
    found = clusters(speech(), load_allow(pathlib.Path(a.allow)))
    if a.window:
        found = [c for c in found if a.window in c.window]
    for c in found:
        print(f"ECHO {c.window} | {c.kind} {c.what!r} | {' + '.join(c.speakers)} | {', '.join(c.keys)}")
    print(f"echoes: {len(found)} clusters outside the allow-list")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
