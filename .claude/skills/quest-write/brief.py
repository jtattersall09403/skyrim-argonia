"""Build one dialogue brief per cast member from a quest record (quest-record.md).

Usage: python3 brief.py QUEST.yaml OUT_DIR [--place-facts PLACE_FACTS.json]

Every fact, thing, clue and person the record names must resolve, or no brief is written: the briefs are
made only from a record that is whole. Place-fact ids (fact.<place>.*) resolve against --place-facts.
"""
import argparse
import json
import pathlib
import re
import sys

import yaml

VOICES = pathlib.Path(__file__).resolve().parents[1] / "dialogue-write" / "voices.md"


def voice_row(race: str) -> str:
    for line in VOICES.read_text().splitlines():
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and cells[0].lower() == race.lower():
            return " | ".join(cells[1:])
    return f"no voice card for {race!r}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("quest")
    ap.add_argument("out")
    ap.add_argument("--place-facts")
    a = ap.parse_args()

    q = yaml.safe_load(pathlib.Path(a.quest).read_text())
    claims = {f["id"]: f["claim"] for f in q["facts"]}
    if a.place_facts:
        for f in json.loads(pathlib.Path(a.place_facts).read_text())["facts"]:
            claims[f["id"]] = f["claim"]
    things = {t["id"]: t for t in q["things"]}
    cast = {c["id"]: c for c in q["cast"]}
    truth = {t["id"] for t in q["truth"]}

    # Resolve every reference before writing anything.
    missing = []
    for f in q["facts"]:
        if f["from"] not in truth and f["from"] not in claims and not f["from"].startswith("culture."):
            missing.append(f"fact {f['id']}: from {f['from']}")
    for fid in q.get("playerStart", []):
        if fid not in claims:
            missing.append(f"playerStart: {fid}")
    for c in q["cast"]:
        for fid in c["knowledge"]:
            if fid not in claims:
                missing.append(f"{c['name']} knowledge: {fid}")
        for ch in c.get("changes", []):
            if ch["fact"] not in claims:
                missing.append(f"{c['name']} change: {ch['fact']}")
    for k in q["clues"]:
        if k["carrier"] not in things and k["carrier"] not in cast:
            missing.append(f"clue {k['id']}: carrier {k['carrier']}")
        missing += [f"clue {k['id']}: {g}" for g in k["gives"] if g not in claims]
    for s in q["stages"]:
        missing += [f"stage {s['id']}: {g}" for g in s.get("learns", []) if g not in claims]
    for t in q["topics"]:
        if t["person"] not in cast:
            missing.append(f"topic {t['topic']}: person {t['person']}")
        missing += [f"topic {t['topic']}: {g}" for g in t.get("uses", []) + t.get("hides", []) if g not in claims]
    for con in q["conclusions"]:
        if len(con["clues"]) < 3:
            missing.append(f"conclusion {con['id']}: {len(con['clues'])} clues, needs 3")
    if missing:
        print("record is not whole; no briefs written:\n  " + "\n  ".join(missing))
        return 1

    def knows_at(stage: int) -> list:
        learned = list(q.get("playerStart", []))
        for s in q["stages"]:
            if s["id"] < stage:
                learned += s.get("learns", [])
        return learned

    def column(c: dict, stage: int) -> dict:
        col = dict(c["knowledge"])
        for ch in c.get("changes", []):
            if ch["atStage"] <= stage:
                col[ch["fact"]] = ch["to"]
        return col

    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for c in q["cast"]:
        p = c["persona"]
        my_topics = [t for t in q["topics"] if t["person"] == c["id"]]
        lines = [f"# Dialogue brief: {c['name']} ({q['code']} {q['title']})", "",
                 "Built by quest-write/brief.py from the quest record. Do not add facts; ask for them.", "",
                 "## What the player can see", f"- {p['race']}, {p['sex']}; {p['visible']}", "",
                 "## What the player cannot see",
                 f"- Role: {p['role']}", f"- Chattiness: {p['chattiness']}; friendliness: {p['friendliness']}; "
                 f"formality: {p['formality']}"]
        if p.get("backstory"):
            lines.append(f"- Backstory: {p['backstory']}")
        lines += [f"- Wants: {c['wants']}", f"- Fears: {c['fears']}"]
        if p.get("invented"):
            lines.append(f"- Invented, awaiting the registry: {', '.join(p['invented'])}")
        lines += ["", "## Voice", f"- {p['race']}: {voice_row(p['race'])} (dialogue-write/voices.md)", "",
                  "## Others in the quest (the player may be sent to them)"]
        lines += [f"- {o['name']}: {o['persona']['role']}; {o['persona']['visible']}"
                  for o in q["cast"] if o is not c]
        lines += ["", "## Things lines may name (and only these)"]
        lines += [f"- `{t['id']}`: {t['kind']}; {t.get('where', t['source'])}; {t['states']}" for t in q["things"]]
        lines += ["", "## Topics"]
        for t in my_topics:
            first = t["stages"][0]
            col = column(c, first)
            lines += [f"### {t['topic']} (stages {t['stages']}; {'essential: no refusal band' if t['essential'] else 'not essential'})",
                      f"- Intent: {t['intent']}",
                      "- May state:"] + [f"  - `{f}`: {claims[f]}" for f in t.get("uses", [])]
            if t.get("hides"):
                lines += ["- Hides (until the intent says otherwise):"] + [f"  - `{f}`: {claims[f]}" for f in t["hides"]]
            if t.get("grants"):
                lines.append(f"- Words that become topic links: {', '.join(t['grants'])}")
            lines += [f"- {c['name']}'s knowledge at stage {first}:"]
            lines += [f"  - `{f}`: {v}" for f, v in col.items()]
            lines += [f"- The player already knows at stage {first} (anything else is explained when first named):"]
            lines += [f"  - `{f}`: {claims[f]}" for f in knows_at(first)]
            lines.append("")
        name = re.sub(r"[^a-z0-9]+", "-", c["name"].lower()).strip("-")
        (out / f"{q['code'].lower()}-{name}.md").write_text("\n".join(lines) + "\n")
        print(f"wrote {out / (q['code'].lower() + '-' + name + '.md')} ({len(my_topics)} topics)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
