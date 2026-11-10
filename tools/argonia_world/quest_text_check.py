"""Off-game checks of the slice quests' player-visible text, from the story data alone (review-writing section E).

    python -m tools.argonia_world.quest_text_check check

Reads the quest lines (quest_lines/*.json, quest_people.json, the dialogue-writer TSVs, written dialogue_line rows),
the journal entries and objectives, and the topic labels; runs E1 E2 E3 E8 E9 E10 E16 E17 E18 and the echoes check
(E15). The checks that need the built plugin (E4-E7, E11-E14, E19, E20) live elsewhere. Allow-lists, retired nouns
and role phrases: story/data/quest_text_allow.json.
"""

from __future__ import annotations

import argparse
import collections
import csv
import dataclasses
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "story" / "data"
ALLOW = DATA / "quest_text_allow.json"
SLICE = ["MQ01", "MQ03", "MQ04", "MQ05", "BC01", "BC02", "BC03", "TG01", "TG02", "LQ25", "LQ30"]

COLUMNS = ["E1", "E2", "E3", "E8", "E9", "E10", "E16", "E17", "E18"]


@dataclasses.dataclass
class Item:
    quest: str          # quest id, e.g. quest.main.mq01
    key: str            # topic key / row key
    kind: str           # spoken | prompt | journal | ending | objective
    text: str
    info: dict = dataclasses.field(default_factory=dict)   # the JSON info or row: replies, gives, hidden, target


@dataclasses.dataclass
class Hit:
    check: str
    quest: str
    key: str
    problem: str
    text: str
    warn: bool = False

    def line(self) -> str:
        return f"{self.check} {self.quest} {self.key} : {self.problem} : {self.text[:90]!r}"


def _jl(name: str, root: pathlib.Path = DATA) -> list[dict]:
    p = root / "db" / f"{name}.jsonl"
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []


def sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]


def words(text: str) -> int:
    return len(text.split())


# ---------------------------------------------------------------- loaders

def slice_ids(root: pathlib.Path = DATA, codes=SLICE) -> dict[str, str]:
    return {q["code"].upper(): q["id"] for q in _jl("quest", root) if q.get("code", "").upper() in codes}


def _texts(info: dict) -> list[str]:
    return [s for k, v in info.items() if k not in ("facts", "when", "replies", "gives") and isinstance(v, list)
            for s in v if isinstance(s, str)]


def json_items(ids: dict[str, str], root: pathlib.Path = DATA) -> list[Item]:
    out = []
    for path in sorted((root / "quest_lines").glob("*.json")):
        data = json.loads(path.read_text())
        if path.name == "quest_people.json":
            for base, entries in data.items():
                if base.startswith("_"):
                    continue
                q = ids.get(base.split("_")[1].upper())
                for e in entries if q else []:
                    out.append(Item(q, base, "prompt", e.get("prompt", "")))
                    out += [Item(q, base, "spoken", t, e) for t in _texts(e)]
            continue
        q = ids.get(path.stem.upper())
        if not q:
            continue
        for topic, body in data.items():
            if topic.startswith("_") or not isinstance(body, dict):
                continue
            for info in body.get("infos", [body]):
                key = f"{topic}#{info.get('variant', 'main')}"
                if info.get("prompt"):
                    out.append(Item(q, key, "prompt", info["prompt"]))
                out += [Item(q, key, "spoken", t, info) for t in _texts(info)]
    return out


_CODE = re.compile(r"(?:(?:topic|greet)\.|ARG_)([A-Za-z]+\d+)[-_]")


def tsv_items(ids: dict[str, str], root: pathlib.Path = DATA) -> list[Item]:
    out = []
    for path in sorted((root / "dialogue-writer" / "quest").rglob("*.tsv")):
        rows = [r for r in csv.reader(path.read_text().splitlines(), delimiter="\t") if r and not r[0].startswith("#")]
        if not rows:
            continue
        head = rows[0]
        named = "line" in head
        li = head.index("line") if named else 1
        pi = head.index("prompt") if "prompt" in head else None
        for r in rows[1:] if named else rows:
            m = _CODE.match(r[0])
            q = ids.get(m.group(1).upper()) if m else None
            if not q or len(r) <= li:
                continue
            if pi is not None and len(r) > pi and r[pi]:
                out.append(Item(q, r[0], "prompt", r[pi]))
            out.append(Item(q, r[0], "spoken", r[li]))
    return out


def row_items(ids: dict[str, str], root: pathlib.Path = DATA) -> list[Item]:
    """Written dialogue_line rows of a slice quest's topics, with the topic label as the prompt."""
    qs = set(ids.values())
    topics = {t["id"]: t for t in _jl("quest_topic", root) if t["quest_id"] in qs}
    out, seen = [], set()
    for r in _jl("dialogue_line", root):
        t = topics.get(r.get("keys_topic") or "")
        if r.get("status") == "imported" or not t:
            continue
        if t["id"] not in seen:
            seen.add(t["id"])
            out.append(Item(t["quest_id"], t["id"], "prompt", t.get("label") or ""))
        for x in (r.get("words"), r.get("variants_low"), r.get("variants_high")):
            if x:
                out.append(Item(t["quest_id"], f"{t['id']}#{r['id']}", "spoken", x, r))
    return out


def record_items(ids: dict[str, str], root: pathlib.Path = DATA) -> list[Item]:
    qs = set(ids.values())
    hidden = {(s["quest_id"], s["ord"]) for s in _jl("quest_stage", root) if s.get("hidden")}
    out = []
    for s in _jl("quest_stage", root):
        if s["quest_id"] in qs and s.get("journal_text"):
            out.append(Item(s["quest_id"], f"stage {s['id']}", "ending" if s.get("ending") else "journal",
                            s["journal_text"], s))
    for o in _jl("quest_objective", root):
        if o["quest_id"] in qs and o.get("objective_text"):
            info = dict(o, hidden=(o["quest_id"], o["stages_ord"]) in hidden)
            out.append(Item(o["quest_id"], f"objective {o['stages_ord']}.{o['id']}", "objective",
                            o["objective_text"], info))
    return out


def load(root: pathlib.Path = DATA) -> list[Item]:
    ids = slice_ids(root)
    return json_items(ids, root) + tsv_items(ids, root) + row_items(ids, root) + record_items(ids, root)


def people(root: pathlib.Path = DATA) -> dict[str, str]:
    """name -> 'male'|'female' for the named people of known sex whose name does not clash."""
    seen: dict[str, set] = collections.defaultdict(set)
    for n in _jl("npc", root):
        if n.get("sex") in ("male", "female") and n.get("kind") != "creature" and n.get("name"):
            seen[n["name"].removeprefix("Root-Herald ")].add(n["sex"])
    return {k: next(iter(v)) for k, v in seen.items() if len(v) == 1 and len(k) >= 4}


def load_allow(path: pathlib.Path = ALLOW) -> dict:
    d = json.loads(path.read_text()) if path.exists() else {}
    return {k: d.get(k, v) for k, v in (("rhetorical", []), ("gives_ok", []), ("retired", {}), ("roles", {}))}


def _allowed(entries: list[dict], it: Item) -> bool:
    return any(e.get("key") in (it.key, it.key.split("#")[0]) and (not e.get("text") or e["text"] in it.text)
               for e in entries)


# ---------------------------------------------------------------- checks

def e1(items: list[Item]) -> list[Hit]:
    """Every objective of a non-hidden stage names its target (a cast, thing or ref id, or `none`)."""
    return [Hit("E1", it.quest, it.key, "objective has no target", it.text) for it in items
            if it.kind == "objective" and not it.info.get("hidden") and not str(it.info.get("target") or "").strip()]


def e2(items: list[Item]) -> list[Hit]:
    """A non-ending, non-hidden journal entry has one "I'm to" and at most 60 words."""
    out = []
    for it in items:
        if it.kind != "journal" or it.info.get("hidden"):
            continue
        n = len(re.findall(r"\bI(?:'m| am) to\b", it.text))
        if n != 1:
            out.append(Hit("E2", it.quest, it.key, f"{n} \"I'm to\" (need 1)", it.text))
        if words(it.text) > 60:
            out.append(Hit("E2", it.quest, it.key, f"{words(it.text)} words (max 60)", it.text))
    return out


_ASK = re.compile(r"(?:^|[.!?]\s+)(?:Give me a|Tell me|Show me)\b")


def e3(items: list[Item], allow: dict) -> list[Hit]:
    """A spoken line with "?" or a Give/Tell/Show-me opening has declared replies, or is allow-listed."""
    return [Hit("E3", it.quest, it.key, "asks the player with no declared reply", it.text) for it in items
            if it.kind == "spoken" and ("?" in it.text or _ASK.search(it.text))
            and not it.info.get("replies") and not _allowed(allow["rhetorical"], it)]


def e8(items: list[Item], allow: dict) -> list[Hit]:
    """Nouns of what the build cut do not appear in the quest's lines, entries or objectives."""
    return [Hit("E8", it.quest, it.key, f"retired noun {noun!r}", it.text) for it in items
            for noun in allow["retired"].get(it.quest, []) if re.search(rf"\b{re.escape(noun)}\b", it.text, re.I)]


_MALE, _FEMALE = {"he", "him", "his", "himself"}, {"she", "her", "hers", "herself"}


def e9(items: list[Item], sexes: dict[str, str]) -> list[Hit]:
    """Pronouns in the sentence naming a person of known sex, and the next, agree; with two names only a warning."""
    out = []
    pats = {n: re.compile(rf"\b{re.escape(n)}\b") for n in sexes}
    for it in items:
        if it.kind == "prompt":
            continue
        sents = sentences(it.text)
        for i, s in enumerate(sents):
            first = {n for n, p in pats.items() if p.search(s)}
            if not first:
                continue
            window = " ".join(sents[i:i + 2])
            named = {n for n, p in pats.items() if p.search(window)}
            have = {w for w in re.findall(r"[a-z]+", window.lower()) if w in _MALE | _FEMALE}
            for n in sorted(first):
                bad = have & (_FEMALE if sexes[n] == "male" else _MALE)
                if bad:
                    out.append(Hit("E9", it.quest, it.key, f"{n} is {sexes[n]}; text says {sorted(bad)}", window,
                                   warn=len(named) > 1))
    return out


def e10(items: list[Item]) -> list[Hit]:
    """A prompt starts with a capital or "(", ends with . ? ! or ), and is not a bare label."""
    out = []
    for it in items:
        t = it.text.strip()
        if it.kind != "prompt":
            continue
        ends = bool(re.search(r"[.?!)]$", t))
        if words(t) < 3 and not ends:
            out.append(Hit("E10", it.quest, it.key, "prompt is a bare label", t))
        elif not (t[:1].isupper() or t[:1] == "(") or not ends:
            out.append(Hit("E10", it.quest, it.key, "prompt must start with a capital or '(' and end . ? ! or )", t))
    return out


def e16(items: list[Item], allow: dict) -> list[Hit]:
    """An entry or objective that names a person by role gives the person's name in the same sentence."""
    return [Hit("E16", it.quest, it.key, f"{role!r} without {name}", s) for it in items
            if it.kind in ("journal", "ending", "objective")
            for role, name in allow["roles"].get(it.quest, {}).items() for s in sentences(it.text)
            if re.search(rf"\b{re.escape(role)}\b", s, re.I) and name.lower() not in s.lower()]


_TIME = re.compile(r"\b(hours ago|yesterday|tonight|this morning|last night)\b", re.I)


def e17(items: list[Item]) -> list[Hit]:
    """Warn on a clock word a line cannot keep true."""
    return [Hit("E17", it.quest, it.key, f"time word {m.group(1)!r}", it.text, warn=True)
            for it in items if it.kind != "prompt" for m in [_TIME.search(it.text)] if m]


_GIVE = re.compile(r"(?:^|[.!?]\s+)(?:Here is|Here are|Take this)\b")


def e18(items: list[Item], allow: dict) -> list[Hit]:
    """A line that hands something over declares `gives`, or is allow-listed."""
    return [Hit("E18", it.quest, it.key, "hands over something with no `gives`", it.text)
            for it in items if it.kind == "spoken" and _GIVE.search(it.text)
            and not it.info.get("gives") and not _allowed(allow["gives_ok"], it)]


def run(items: list[Item], allow: dict, sexes: dict[str, str]) -> list[Hit]:
    return (e1(items) + e2(items) + e3(items, allow) + e8(items, allow) + e9(items, sexes) + e10(items)
            + e16(items, allow) + e17(items) + e18(items, allow))


def echoes_failed() -> bool:
    """E15: the echoes check, as `python -m tools.argonia_world.echoes check` runs it."""
    from tools.argonia_world import echoes
    found = echoes.clusters(echoes.speech(), echoes.load_allow())
    print(f"E15 echoes: {len(found)} clusters outside the allow-list")
    return bool(found)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["check"])
    ap.add_argument("--allow", default=str(ALLOW))
    ap.add_argument("--out", help="also write every hit to this file")
    ap.add_argument("--no-echoes", action="store_true", help="skip E15")
    a = ap.parse_args()
    hits = run(load(), load_allow(pathlib.Path(a.allow)), people())
    lines = [("WARN " if h.warn else "") + h.line() for h in hits]
    print("\n".join(lines))
    if a.out:
        pathlib.Path(a.out).write_text("\n".join(lines) + "\n")
    hard = collections.Counter(h.check for h in hits if not h.warn)
    warn = collections.Counter(h.check for h in hits if h.warn)
    print("hard: " + " ".join(f"{c}={hard.get(c, 0)}" for c in COLUMNS))
    print("warn: " + " ".join(f"{c}={warn.get(c, 0)}" for c in COLUMNS))
    bad = bool(hard)
    if not a.no_echoes:
        bad = echoes_failed() or bad
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
