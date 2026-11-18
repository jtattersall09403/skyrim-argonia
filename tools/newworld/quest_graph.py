"""A quest record as a branching sequence of events: the beats (where the player starts and what they know, each
stage, each ending), the moves between them (a word with a named person, a choice, a check passed or failed, a thing
taken, someone dying) in plain words, and the gaps the record leaves (a sneak with no caught edge, a check with no
failure reply, a stage that leads nowhere). The story explorer draws the graph on each quest page and tells the same
beats under it as a chronology; no id is ever shown.

    python -m tools.newworld.quest_graph gaps      # every quest's gaps, for the record writers
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.newworld import quest_play as QP  # noqa: E402
from tools.playtest.record import humanize  # noqa: E402

ID = re.compile(r"\b(npc|thing|door|topic|flag|quest|fact|text|item)\.[a-z0-9][a-z0-9_.-]*[a-z0-9]")
SNEAKS = {"sneak-past", "slip-past", "pass-unseen", "steal-unseen", "steal", "pickpocket"}
CAUGHT = re.compile(r"\b(caught|seen|spotted|detect\w*|notic\w*|alarm|raise[sd]? the|turns? hostile|hostile|thief)\b",
                    re.I)
VERB = {"pickpocket": "pick {t}'s pocket", "persuade": "persuade {t}", "sneak-past": "sneak past {t}",
        "slip-past": "slip past {t}", "pass-unseen": "get past {t} unseen", "steal-unseen": "steal {t} unseen",
        "steal": "steal {t}", "pick-a-lock": "pick the lock of {t}", "fight": "fight {t}",
        "fight-at-range": "fight {t} at range", "fight-people": "fight {t}", "fight-guards": "fight {t}",
        "fight-raiders": "fight {t}", "fight-creature": "fight {t}", "fight-undead": "fight {t}",
        "fight-with-magic": "fight {t} with magic", "shoot-from-cover": "shoot {t} from cover", "calm": "calm {t}",
        "cure": "cure {t}", "barter": "barter with {t}", "pay": "pay {t}", "duel": "duel {t}", "block": "block {t}",
        "turn-undead": "turn {t}", "cast-as-test": "cast a spell before {t}", "summon": "summon help against {t}",
        "waterbreathing": "breathe water to reach {t}", "learn-a-recipe": "learn {t}", "report": "report to {t}",
        "brew-or-buy-a-potion": "brew or buy {t}"}

_INDEX: dict[str, str] | None = None


def index(records: dict[str, dict]) -> dict[str, str]:
    """Every id any record names, as the plain words for it (people by name, things by name, topics by label)."""
    global _INDEX
    if _INDEX is not None and _INDEX.get("__n") == str(len(records)):
        return _INDEX
    out: dict[str, str] = {"__n": str(len(records))}
    for q in records.values():
        p = QP.Play(q, records)
        for i in [*p.names, *p.things, *p.place_of]:
            out.setdefault(i, Words(p).plain(i, look=False))
        for t in p.topics.values():
            out.setdefault(t["id"], f"“{QP.one(t.get('label', ''))}”")
        out.setdefault(q["id"], f"{q.get('code')} ({QP.one(q.get('title', ''))})")
    _INDEX = out
    return out


class Words:
    """Plain words for a record's ids."""

    def __init__(self, play: QP.Play, records: dict[str, dict] | None = None):
        self.p, self.records = play, records or {}

    def plain(self, i, full: bool = False, look: bool = True) -> str:
        i = str(i).strip()
        p = self.p
        th, pl = p.things.get(i, {}), p.place_of.get(i, {})
        if i.startswith("topic."):
            t = p.topics.get(i)
            if t:
                return f"“{re.sub(r'^\(speaks first\)\s*', '', QP.one(t.get('label', '')))}”"
        elif i.startswith("quest."):
            r = self.records.get(i) or {}
            return f"{QP.code_of(i)}" + (f" ({QP.one(r['title'])})" if r.get("title") else "")
        elif th.get("kind") == "door" or pl.get("kind") == "door" or i.startswith("door."):
            nm = pl.get("placeName") or th.get("name") or pl.get("name")
            if nm:
                w = self.where(i) if full else ""
                return f"the door to {QP.one(nm)}" + (f" ({w})" if w else "")
        elif i.startswith("flag."):
            h = next((h for h in p.hooks if h.get("setsFlag") == i), None)
            if h:
                return f"having {'read' if h.get('hook') == 'read' else 'used'} {self.plain(h.get('thing'))}"
            return humanize(i.split(".")[-1]).replace("-", " ").lower()
        if i in p.names and p.names[i] and not ID.fullmatch(p.names[i]):
            n = QP.one(p.names[i])
            w = self.where(i) if full else ""
            w = re.sub(rf"^{re.escape(n)}\s*,?\s*", "", w) if w else w
            return f"{n} ({w})" if w else n
        if look and ID.fullmatch(i):
            g = index(self.records).get(i)
            if g:
                return g
        tail = i.split(".")[-1].replace("-", " ")
        return ("the " if i.startswith("thing.") else "") + (tail.title() if i.startswith("npc.") else tail)

    def where(self, i) -> str:
        w = self.p.where(i)
        return self.scrub(w) if w else ""

    def scrub(self, s) -> str:
        """Every id in a text turned into its plain words."""
        s = ID.sub(lambda m: self.plain(m.group(0)), str(s))
        return re.sub(r"\bsetFlag\s+", "marks ", s)


def _cond(p: QP.Play, w: Words, c, brief: bool) -> str:
    if brief:
        keep = p.who, p.where
        p.who = lambda r: w.plain(r)  # type: ignore[method-assign]
        p.where = lambda r: ""  # type: ignore[method-assign]
        try:
            s = p.cond(c)
        finally:
            p.who, p.where = keep  # type: ignore[method-assign]
    else:
        s = p.cond(c)
    s = re.sub(r"^you say to ", "you ask ", s)
    return w.scrub(s)


def short(s: str, n: int = 44) -> str:
    s = QP.one(s)
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"


def _acts(s: dict) -> list[dict]:
    out = [a for a in s.get("actions") or [] if isinstance(a, dict)]
    for ap in s.get("approaches") or []:
        out += [a for a in (ap.get("actions") or []) if isinstance(a, dict)] if isinstance(ap, dict) else []
    seen, uniq = set(), []
    for a in out:
        k = (a.get("use"), str(a.get("target")))
        if k not in seen:
            seen.add(k)
            uniq.append(a)
    return uniq


def action_words(w: Words, a: dict) -> str:
    t = w.scrub(a.get("target") or "it")
    v = VERB.get(str(a.get("use")), humanize(str(a.get("use", ""))).lower() + " {t}").format(t=t)
    note = f"; {w.scrub(QP.one(a['note']))}" if a.get("note") else ""
    return f"{v} ({a.get('skill')}{note})" if a.get("skill") else v + (f" ({note[2:]})" if note else "")


def build(q: dict, records: dict[str, dict]) -> dict:
    """The quest's graph: nodes (start, stages, endings), edges in plain words, and the gaps."""
    p = QP.Play(q, records)
    w = Words(p, records)
    stages = {str(s["id"]): s for s in p.stages}
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    start = str(q.get("start") or (p.stages[0]["id"] if p.stages else ""))
    sw = q.get("startWhen")
    nodes["start"] = {"id": "start", "kind": "start", "title": "Where you start",
                      "place": p.place(stages[start]["place"]) if start in stages and stages[start].get("place") else ""}
    if start in stages:
        edges.append({"from": "start", "to": f"s{start}", "kind": "go",
                      "label": _cond(p, w, sw, True) if sw else "the game begins",
                      "full": _cond(p, w, sw, False) if sw else "the game begins"})
    ends = {e.get("id"): e for e in q.get("endings") or [] if isinstance(e, dict)}
    for sid, s in stages.items():
        kind = "stage"
        if s.get("ending"):
            kind = "won" if str(s.get("ending")) in ("complete", "True", "true") else "lost"
        e = ends.get(s.get("endingId"), {})
        obj = next((QP.one(o["objectiveText"]) for o in s.get("objectives") or [] if o.get("objectiveText")), "")
        title = (QP.one(e.get("when", "")) if kind != "stage" and e.get("when") else
                 obj or QP.one(s.get("journalText", "")).split(". ")[0])
        nodes[f"s{sid}"] = {"id": f"s{sid}", "kind": kind, "stage": sid, "title": w.scrub(title).rstrip("."),
                            "place": p.place(s["place"]) if s.get("place") else ""}
        for k in ("successors", "failForward"):
            for x in s.get(k) or []:
                if isinstance(x, dict) and str(x.get("to")) in stages:
                    edges.append({"from": f"s{sid}", "to": f"s{x['to']}", "kind": "go" if k == "successors" else "fail",
                                  "label": _cond(p, w, x.get("when"), True), "full": _cond(p, w, x.get("when"), False)})
    merged: dict[tuple, dict] = {}
    for e in edges:   # moves between the same two beats are one arrow with every way listed
        m = merged.get((e["from"], e["to"], e["kind"]))
        if m:
            m["ways"].append(e["full"])
        else:
            merged[(e["from"], e["to"], e["kind"])] = e | {"ways": [e["full"]]}
    edges = list(merged.values())
    for e in edges:
        if len(e["ways"]) > 1:
            e["label"] = f"{e['label']} (or {len(e['ways']) - 1} other way{'s' if len(e['ways']) > 2 else ''})"
            e["full"] = "either " + "; or ".join(e["ways"])
    seen: dict[str, list[str]] = {}
    for n in nodes.values():
        seen.setdefault(n["title"], []).append(n["id"])
    for t, ids in seen.items():   # beats that share an objective are told apart by their journal's first sentence
        if len(ids) > 1:
            for i in ids:
                s = stages.get(nodes[i].get("stage") or "", {})
                j = w.scrub(QP.one(s.get("journalText", ""))).split(". ")[0].rstrip(".")
                if j:
                    nodes[i]["title"] = j
    gaps = find_gaps(q, p, w, stages, edges, start)
    for g in gaps:
        nodes.get(g["node"], nodes["start"]).setdefault("gaps", []).append(g["text"])
    rank(nodes, edges)
    return {"nodes": list(nodes.values()), "edges": edges, "gaps": gaps}


def rank(nodes: dict, edges: list[dict]) -> None:
    """Each node's row (longest path from the start along forward moves) and its place in the row."""
    out: dict[str, list[str]] = {}
    for e in edges:
        out.setdefault(e["from"], []).append(e["to"])
    back: set[tuple[str, str]] = set()
    state: dict[str, int] = {}

    def dfs(n):
        state[n] = 1
        for m in out.get(n, []):
            if state.get(m) == 1:
                back.add((n, m))
            elif m not in state:
                dfs(m)
        state[n] = 2
    dfs("start")
    for n in nodes:
        if n not in state:
            dfs(n)
    r = {n: 0 for n in nodes}
    for _ in range(len(nodes) + 1):
        moved = False
        for e in edges:
            if (e["from"], e["to"]) in back or e["kind"] == "fail":
                continue
            if r[e["to"]] < r[e["from"]] + 1:
                r[e["to"]], moved = r[e["from"]] + 1, True
        if not moved:
            break
    for e in edges:   # a failure reached from anywhere sits one row below the last stage it is reached from
        if e["kind"] == "fail" and not any(x["to"] == e["to"] and x["kind"] == "go" for x in edges):
            r[e["to"]] = max(r[e["to"]], r[e["from"]] + 1)
    maxr = max(r.values()) if r else 0
    for n, d in nodes.items():   # endings at the foot
        if d["kind"] in ("won", "lost") and not out.get(n):
            r[n] = max(r[n], maxr) if d["kind"] == "lost" else r[n]
    rows: dict[int, list[str]] = {}
    for n in nodes:
        rows.setdefault(r[n], []).append(n)
    pos: dict[str, float] = {}
    for k in sorted(rows):
        def bary(n):
            ps = [pos[e["from"]] for e in edges if e["to"] == n and e["from"] in pos and e["kind"] == "go"]
            return sum(ps) / len(ps) if ps else 99 + (nodes[n]["kind"] == "lost")
        rows[k].sort(key=lambda n: (bary(n), int(re.sub(r"\D", "", str(nodes[n].get("stage") or 0)) or 0)))
        for i, n in enumerate(rows[k]):
            pos[n] = i
            nodes[n]["row"], nodes[n]["col"] = k, i
    for e in edges:
        e["back"] = (e["from"], e["to"]) in back


def find_gaps(q, p: QP.Play, w: Words, stages: dict, edges: list[dict], start: str) -> list[dict]:
    gaps: list[dict] = []
    add = lambda node, text: gaps.append({"node": node, "text": text})  # noqa: E731
    reach, todo = set(), ["start"]
    while todo:
        n = todo.pop()
        if n not in reach:
            reach.add(n)
            todo += [e["to"] for e in edges if e["from"] == n]
    opened = {}
    for t in p.topics.values():
        for st in t.get("stages") or []:
            opened.setdefault(str(st), []).append(t)
    for sid, s in stages.items():
        n = f"s{sid}"
        outs = [e for e in edges if e["from"] == n]
        if not s.get("ending") and not outs:
            add(n, "Nothing in the record moves the quest on from here: this stage is a dead end.")
        if n not in reach:
            add(n, "No move in the record leads here: the player can never reach this beat.")
        if s.get("ending"):
            continue
        talk = " ".join(json.dumps(t, ensure_ascii=False) for t in opened.get(sid, []))
        here = json.dumps({k: v for k, v in s.items() if k not in ("journalText", "information")}, ensure_ascii=False)
        for a in _acts(s):
            use = str(a.get("use"))
            if use in SNEAKS and not CAUGHT.search(here + " " + talk):
                add(n, f"If you are caught trying to {action_words(w, a).split(' (')[0]}, the record does not say "
                       "what happens.")
            if use == "pick-a-lock":
                tgt = str(a.get("target") or "")
                lock = (p.place_of.get(tgt) or {}).get("lock")
                if ID.fullmatch(tgt) and not lock:
                    add(n, f"The record does not say {w.plain(tgt)} is locked, or how hard its lock is.")
        for t in opened.get(sid, []):
            if t.get("when") and (re.search(r"skillAtLeast|goldAtLeast", repr(t["when"])) and not t.get("fallback")):
                add(n, f"If you fail the check for {w.plain(t['id'])} (asked of {w.plain(t.get('person'))}), "
                       "the record gives no reply.")
        for t in opened.get(sid, []):
            for to in re.findall(r"sets stage (\d+)", t.get("intent", "")):
                if to != sid and not any(e["from"] == n and e["to"] == f"s{to}" for e in edges):
                    add(n, f"{w.plain(t['id'])}, asked of {w.plain(t.get('person'))}, is meant to move the quest to "
                           f"stage {to}, but no move in the record goes there from here.")
        needed = set(re.findall(r"'topicHeardFrom': \['[^']+', '([^']+)'\]", repr(s.get("successors"))))
        guarded = set(re.findall(r"'npcAlive': '([^']+)'|'npcAlive': \['([^']+)'", repr(s.get("failForward"))))
        guarded = {x for pair in guarded for x in pair if x}
        for npc in sorted(needed - guarded):
            add(n, f"The quest moves on only by talking to {w.plain(npc)}; if {w.plain(npc)} dies here, nothing "
                   "handles it.")
    placed = {r for r, pl in p.place_of.items() if pl.get("kind") == "person" and pl.get("enabled", True) is not False
              and pl.get("name")}
    enabled_later = {QP._args(a.get("enableRef"))[0] for s in stages.values() for a in s.get("onEnter") or []
                     if isinstance(a, dict) and "enableRef" in a}
    order = list(stages)
    for npc in sorted(placed - enabled_later):
        theirs = [t for t in p.topics.values() if t.get("person") == npc]
        if not theirs:
            continue
        first = min((order.index(str(st)) for t in theirs for st in t.get("stages") or [] if str(st) in order),
                    default=None)
        if first and order[first] != start and stages[order[first]].get("place") != stages[start].get("place"):
            add(f"s{order[first]}", f"{w.plain(npc)} stands in the world from the start, but has nothing to say "
                                    f"about this quest before stage {order[first]}; meeting them early is not handled.")
    return gaps


# ---- the chronology --------------------------------------------------------------------------------------------

def beats(q: dict, records: dict[str, dict], g: dict | None = None) -> list[dict]:
    """The quest told beat by beat, in the graph's order: each beat's prose and its folded detail, in markdown."""
    g = g or build(q, records)
    p = QP.Play(q, records)
    w = Words(p, records)
    nodes = {n["id"]: n for n in g["nodes"]}
    stages = {str(s["id"]): s for s in p.stages}
    order = sorted(g["nodes"], key=lambda n: (n["row"], n["col"]))
    title = lambda nid: nodes[nid]["title"]  # noqa: E731
    out = []
    for n in order:
        prose, detail = [], []
        ins = [e for e in g["edges"] if e["to"] == n["id"]]
        outs = [e for e in g["edges"] if e["from"] == n["id"]]
        if n["kind"] == "start":
            prev = QP.follows(q, records)
            for r, st in prev:
                s = next((x for x in r.get("stages") or [] if str(x.get("id")) == st), None)
                if s and s.get("journalText"):
                    prose.append(f"You come to this from {QP.link(r['code'], r['title'])}. What you know: "
                                 f"*{w.scrub(QP.one(s['journalText']))}*")
            if q.get("playerStart"):
                prose.append("At the start of the game: " + w.scrub(QP.one(", ".join(map(str, q["playerStart"])))) + ".")
            if not prev and not q.get("playerStart"):
                prose.append(w.scrub(p.start_words()))
        else:
            s = stages[n["stage"]]
            heard: list[dict] = []
            go = [e for e in ins if e["kind"] == "go"]
            fail = [e for e in ins if e["kind"] == "fail"]
            for e in go:
                p.cond(_when(stages, e), heard)
            if go:
                ways = [f"from [{title(e['from'])}](#beat-{e['from']})" +
                        (f", when {e['full']}" if e["from"] != "start" else "") for e in go]
                prose.append(("You get here " + ways[0] + ".") if len(ways) == 1 else
                             "You get here in one of " + str(len(ways)) + " ways: " +
                             "; or ".join(ways) + ".")
            if fail:
                frm = sorted({e["from"] for e in fail}, key=lambda x: nodes[x]["row"])
                prose.append(f"This happens at any point from {_list([f'[{title(x)}](#beat-{x})' for x in frm])} "
                             f"if {fail[0]['full']}.")
            acts = [x for x in map(p.act, s.get("onEnter") or []) if x]
            if acts:
                prose.append("Then " + w.scrub("; ".join(acts)) + ".")
            told = []
            for t in heard:
                told += p.said(t)
            for a in s.get("onEnter") or []:
                if isinstance(a, dict) and "showMessage" in a:
                    m = p.messages.get(QP._args(a["showMessage"])[0])
                    if m and m.get("text"):
                        told += ["A message appears on the screen:", f"*“{QP.one(m['text'])}”*"]
            prose += [w.scrub(x) for x in told]
            learned = [f for f in q.get("facts") or [] if isinstance(f, dict) and f.get("id") in (s.get("learns") or [])]
            if learned:
                prose.append("Now you know: " + " ".join(w.scrub(QP.one(f["claim"])) for f in learned))
            e = next((e for e in q.get("endings") or [] if e.get("id") == s.get("endingId")), None)
            if e:
                gives = [x for x in map(p.act, [*(e.get("rewards") or []), *(e.get("world") or [])]) if x]
                if e.get("seen"):
                    prose.append(f"The quest ends here. Afterwards: {w.scrub(QP.one(e['seen']))}.")
                if gives:
                    prose.append("At the end " + w.scrub("; ".join(gives)) + ".")
            acts_here = _acts(s)
            if acts_here:
                prose.append("What you can do here: " + "; ".join(action_words(w, a) for a in acts_here) + ".")
            opened = [t for t in p.topics.values() if (t.get("stages") or [None])[0] == s["id"] and t not in heard]
            if opened:
                detail.append("**What you can ask from here.**")
                items = []
                for t in opened:
                    ip = QP.intent_parts(t.get("intent", ""))
                    lab = re.sub(r"^\(speaks first\)\s*", "", QP.one(t.get("label", "")))
                    to = p.moves(t)
                    sp = w.plain(t.get("person"))
                    gist = ip.get("tells") or re.sub(rf"^{re.escape(sp)}[,.]?\s*", "", ip.get("setting", ""))
                    if not ip.get("tells") and not gist.strip(" ."):
                        gist = ""
                    line = f"“{lab}”, asked of {w.plain(t.get('person'))}"
                    if t.get("when"):
                        line += f" (only when {_cond(p, w, t['when'], True)})"
                    line += f": {gist}" if gist else ""
                    does = re.sub(r"\s*\bsets stage \d+\.?", "", ip.get("does") or "").strip(" .;")
                    if does and does.lower() != "nothing":
                        line += f" Then {does[0].lower() + does[1:]}."
                    if to and to != str(s["id"]):
                        line += f" This moves the quest to [{title('s' + to)}](#beat-s{to})."
                    if t.get("fallback"):
                        line += f" If you cannot: *“{QP.one(t['fallback'])}”*"
                    items.append(w.scrub(line))
                detail.append("- " + "\n- ".join(items))
            if s.get("journalText"):
                detail.append(f"**The journal.** *{w.scrub(QP.one(s['journalText']))}*")
            for o in s.get("objectives") or []:
                if isinstance(o, dict) and o.get("objectiveText"):
                    tg = [x.strip() for x in str(o.get("target") or "").split(",") if x.strip()]
                    marks = [w.plain(x, full=True) for x in tg]
                    detail.append(f"**Objective.** {w.scrub(QP.one(o['objectiveText']))}"
                                  + (f" The marker points at {_list(marks)}." if marks else ""))
            if s.get("directions"):
                detail.append(f"**Directions.** {w.scrub(QP.one(s['directions']))}")
            info = s.get("information") if isinstance(s.get("information"), dict) else {}
            if info.get("ways") and str(info["ways"]).strip().lower() != "none":
                detail.append(f"**The ways through, as designed.** {w.scrub(QP.one(info['ways']))}")
            carriers = [c for c in info.get("carriers") or [] if isinstance(c, dict)]
            if carriers:
                detail.append("**How you find each thing out.**")
                detail.append("- " + "\n- ".join(w.scrub(p.carrier(c)) for c in carriers))
        nxt = []
        for e in outs:
            to = f"[{title(e['to'])}](#beat-{e['to']})"
            if e["kind"] == "go":
                nxt.append(f"If {e['full']}: {to}." if n["kind"] != "start" else
                           f"It begins when {e['full']}: {to}." if e["full"] != "the game begins" else
                           f"It begins when the game begins: {to}.")
        fails = [e for e in outs if e["kind"] == "fail"]
        if nxt:
            prose.append(("What comes next. " if len(nxt) == 1 else "What comes next depends on you. ")
                         + " ".join(x[0].upper() + x[1:] for x in nxt))
        if fails:
            detail.append("**If things go wrong here.** " + " ".join(
                f"If {e['full']}: [{title(e['to'])}](#beat-{e['to']})." for e in fails))
        if n.get("gaps"):
            detail.append("**Gaps in the record.**")
            detail.append("- " + "\n- ".join(n["gaps"]))
        head = n["title"] if n["kind"] == "start" else (
            ("The end: " if n["kind"] == "won" else "It fails: " if n["kind"] == "lost" else "") + n["title"])
        out.append({"node": n["id"], "kind": n["kind"], "title": head, "place": n.get("place", ""), "stage": n.get("stage"),
                    "prose": prose, "detail": detail, "gaps": n.get("gaps", [])})
    return out


def _when(stages: dict, e: dict):
    s = stages.get(e["from"][1:], {})
    for k in ("successors", "failForward"):
        for x in s.get(k) or []:
            if isinstance(x, dict) and f"s{x.get('to')}" == e["to"]:
                return x.get("when")
    return None


def _list(xs: list[str]) -> str:
    xs = list(dict.fromkeys(xs))
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1] if xs else ""


def loops(g: dict) -> list[list[str]]:
    """Beats that lead into one another in any order (four or more on one loop), each as one group."""
    adj: dict[str, list[str]] = {}
    for e in g["edges"]:
        if e["kind"] == "go":
            adj.setdefault(e["from"], []).append(e["to"])
    idx, low, stack, on, out, k = {}, {}, [], set(), [], [0]

    def visit(v):
        idx[v] = low[v] = k[0]
        k[0] += 1
        stack.append(v)
        on.add(v)
        for x in adj.get(v, []):
            if x not in idx:
                visit(x)
                low[v] = min(low[v], low[x])
            elif x in on:
                low[v] = min(low[v], idx[x])
        if low[v] == idx[v]:
            comp = []
            while True:
                x = stack.pop()
                on.discard(x)
                comp.append(x)
                if x == v:
                    break
            if len(comp) >= 4:
                out.append(comp)
    for n in g["nodes"]:
        if n["id"] not in idx:
            visit(n["id"])
    return out


def diagram(g: dict) -> dict:
    """The graph as the page draws it: nodes with their row, column, title and gap count; edges with a short label.
    Beats that loop into one another in any order are drawn as one box that lists them."""
    nodes = {n["id"]: dict(n) for n in g["nodes"]}
    into: dict[str, str] = {}
    for i, comp in enumerate(loops(g)):
        comp.sort(key=lambda x: (nodes[x]["row"], nodes[x]["col"]))
        gid = f"g{i}"
        first = nodes[comp[0]]
        nodes[gid] = {"id": gid, "kind": "group", "title": f"{len(comp)} beats, in any order",
                      "place": first.get("place", ""), "row": first["row"], "col": first["col"],
                      "members": comp, "gaps": [x for c in comp for x in nodes[c].get("gaps", [])]}
        for c in comp:
            into[c] = gid
            del nodes[c]
    edges: dict[tuple, dict] = {}
    for e in g["edges"]:
        a, b = into.get(e["from"], e["from"]), into.get(e["to"], e["to"])
        if a == b:
            continue
        key = (a, b, e["kind"])
        if key in edges:
            edges[key]["n"] += 1
        else:
            edges[key] = {"from": a, "to": b, "kind": e["kind"], "back": e.get("back", False), "label": e["label"], "n": 1}
    for e in edges.values():
        if e["n"] > 1:
            e["label"] = f"one of {e['n']} ways"
    rows: dict[int, list[dict]] = {}
    for n in nodes.values():
        rows.setdefault(n["row"], []).append(n)
    for r, (_, ns) in enumerate(sorted(rows.items())):   # close the rows a group emptied
        for c, n in enumerate(sorted(ns, key=lambda n: n["col"])):
            n["row"], n["col"] = r, c
    return {"nodes": [{"id": n["id"], "kind": n["kind"], "title": n["title"], "place": n.get("place", ""),
                       "stage": n.get("stage"), "row": n["row"], "col": n["col"], "gaps": len(n.get("gaps", [])),
                       **({"members": n["members"]} if n.get("members") else {})} for n in nodes.values()],
            "edges": [{k: v for k, v in e.items() if k != "n"} | {"label": short(re.sub(r"\byou ask [^:“]+: ", "", e["label"]))} for e in edges.values()]}


def main(argv: list[str]) -> int:
    from tools.newworld.story_explorer import ROOT, record_files
    from tools.playtest.record import load
    recs = {}
    for f in record_files(ROOT):
        try:
            q = load(f)
        except Exception:  # noqa: BLE001 - a record that does not load has no graph
            continue
        recs[q["id"]] = q
    for q in sorted(recs.values(), key=lambda r: str(r.get("code"))):
        g = build(q, recs)
        if g["gaps"]:
            print(f"{q.get('code')}. {QP.one(q.get('title', ''))}")
            for x in g["gaps"]:
                n = next(n for n in g["nodes"] if n["id"] == x["node"])
                print(f"  - [{('stage ' + str(n['stage'])) if n.get('stage') else 'start'}] {x['text']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
