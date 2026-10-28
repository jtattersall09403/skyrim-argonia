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
SHAPES = pathlib.Path(__file__).with_name("shapes.yaml")
USES = pathlib.Path(__file__).with_name("skill-uses.yaml")
WEAPONS = ["long-blade", "short-blade", "axe", "blunt-weapon", "spear", "marksman", "hand-to-hand"]


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

    # The sections the quest's shapes and line require (shapes.yaml), and an action in every stage
    # except an ending or a WONDER (principles/actions.md).
    routing = yaml.safe_load(SHAPES.read_text())
    data = q.get("shapeData", {})
    for shape in q.get("shapes", []):
        keys = [shape] + ([f"{shape}/{data['theftMode']}"] if shape == "THEFT" and "theftMode" in data else [])
        for key in keys:
            if key not in routing["shapes"]:
                missing.append(f"shape {key}: not in shapes.yaml")
                continue
            missing += [f"shapeData.{r}: required by {key}" for r in routing["shapes"][key]["require"] if r not in data]
    if q.get("line") not in routing["lines"]:
        missing.append(f"line {q.get('line')!r}: not one of {', '.join(routing['lines'])}")
    catalogue = yaml.safe_load(USES.read_text())["skills"]

    def stage_actions(s):
        return list(s.get("actions", [])) + [x for ap_ in s.get("approaches", []) for x in ap_.get("actions", [])]

    for s in q["stages"]:
        for x in stage_actions(s):
            skills = WEAPONS if x.get("skill") == "any-weapon" else [x.get("skill")]
            if not any(sk in catalogue and x.get("use") in catalogue[sk]["uses"] for sk in skills):
                missing.append(f"stage {s['id']}: {x.get('skill')}: {x.get('use')} is not in skill-uses.yaml")
    if "actionPlan" not in q:
        missing.append("actionPlan: missing (principles/actions.md)")
    if "WONDER" not in q.get("shapes", []):
        for s in q["stages"]:
            if not s.get("ending") and not (s.get("actions") or any(a.get("actions") for a in s.get("approaches", []))):
                missing.append(f"stage {s['id']}: no actions (principles/actions.md)")
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
            acts = [x for s_ in q["stages"] if s_["id"] in t["stages"] for x in stage_actions(s_)]
            if acts:
                lines += ["- What the player does at these stages (set it up: who, where, what danger, what they need):"]
                lines += [f"  - {x['skill']}: {x['use']}" + (f" ({x['target']})" if x.get("target") else "")
                          + (f", {x['setting']}" if x.get("setting") else "") for x in acts]
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
