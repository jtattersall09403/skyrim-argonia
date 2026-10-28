"""Build a dialogue brief for one person's place topics (greeting, my trade, the place, rumours, danger, work,
directions) from the place record and culture sheets, in the same shape as quest-write/brief.py.

Usage: python3 place_brief.py --place-facts PLACE.json --sheets SHEET.json [SHEET.json ...]
                              --person PERSON_ID --persona PERSONA.yaml --out BRIEF.md

PERSONA.yaml holds what the people registry will hold after the P0 import: race, sex, role, visible,
chattiness, friendliness, formality, backstory, faction. Facts are the person's own (the place record names
them as carrier) plus what the player can see; opinions come from the culture sheets, most specific first.
"""
import argparse
import json
import pathlib
import sys

import yaml

VOICES = pathlib.Path(__file__).with_name("voices.md")
TOPICS = [  # topic, the culture-sheet opinion keys it draws on, its intent
    ("greeting", [], "the first thing said; warmth by band; listener variants by race, faction and crime"),
    ("my trade", ["work", "trade"], "what this person does, sells or offers, and for how much"),
    ("{place}", ["place", "people"], "what the place is and why people come, as this person sees it"),
    ("latest rumours", ["rumour"], "what people here are talking about; a held-back answer says so"),
    ("danger near {place}", ["danger"], "what can hurt a traveller here and how to avoid it (fixed danger)"),
    ("work at {place}", ["work"], "who needs help or hands; a hook only if the place record holds one"),
    ("directions", ["directions"], "the way to named places, by landmark, direction and distance"),
]


def voice_row(race: str) -> str:
    for line in VOICES.read_text().splitlines():
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and cells[0].lower() == race.lower():
            return " | ".join(cells[1:])
    return f"no voice card for {race!r}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--place-facts", required=True)
    ap.add_argument("--sheets", nargs="+", required=True)
    ap.add_argument("--person", required=True)
    ap.add_argument("--persona", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    place = json.loads(pathlib.Path(a.place_facts).read_text())
    world = place["world"]
    persona = yaml.safe_load(pathlib.Path(a.persona).read_text())
    people = {p["id"]: p for p in world["people"]}
    if a.person not in people:
        print(f"{a.person} is not in the place's people roster; no brief written")
        return 1
    me = people[a.person]
    uid = "npc-" + a.person.rsplit(".", 1)[-1]

    def carrier(f):
        c = f.get("carrier", {})
        return c.get("built", {}).get("uid") or c.get("queued", {}).get("ref")

    mine = [f for f in place["facts"] if carrier(f) in (uid, a.person)]
    seen = [f for f in place["facts"] if f.get("carrier", {}).get("built", {}).get("type") in ("piece-set", "visual-cue")]

    sheets = []
    for s in a.sheets:
        sheets += json.loads(pathlib.Path(s).read_text())["entries"]
    chain = [s for s in sheets if s.get("placeId") == place["placeId"] or a.person in s.get("members", [])]
    order = {"settlement": 0, "group": 1, "household": 2}
    chain.sort(key=lambda s: order.get(s["level"], 3))
    if not chain:
        print("no culture sheet covers this person; no brief written")
        return 1

    name = world["name"]
    L = [f"# Dialogue brief: {me['name']}, place topics ({name})", "",
         "Built by dialogue-write/place_brief.py. Do not add facts; ask for them.", "",
         "## What the player can see", f"- {persona['race']}, {persona['sex']}; {persona['visible']}", "",
         "## What the player cannot see", f"- Role: {persona.get('role', me['role'])}",
         f"- Chattiness: {persona['chattiness']}; friendliness: {persona['friendliness']}; "
         f"formality: {persona.get('formality') or chain[-1]['speech']['formality']}",
         f"- Faction: {persona.get('faction', 'none')}"]
    if persona.get("backstory"):
        L.append(f"- Backstory: {persona['backstory']}")
    L += ["", "## Voice", f"- {persona['race']}: {voice_row(persona['race'])} (voices.md)", "",
          "## Culture (most specific last; a person may differ only where a dissent row says so)"]
    for s in chain:
        sp = s["speech"]
        L.append(f"- **{s['name']}** ({s['level']}): formality {sp['formality']}; "
                 f"address: {'; '.join(x['text'] for x in sp['addressTerms'])}; "
                 f"oaths: {'; '.join(x['text'] for x in sp['oaths']) or 'none'}; "
                 f"never says: {'; '.join(x['text'] for x in sp['neverSaid']) or 'nothing listed'}")
        for k in ("norms", "taboos", "values", "contempts"):
            if s.get(k):
                L.append(f"  - {k}: {'; '.join(x['text'] for x in s[k])}")
        for d in s.get("dissent", []):
            if d["personId"] == a.person:
                L.append(f"  - **this person dissents on {d['topic']}:** {d['text']}")
    L += ["", "## Others here (the player may be sent to them)"]
    L += [f"- {p['name']}: {p['role']}" for p in world["people"] if p["id"] != a.person]
    L += ["", "## What the player can see of the place"] + [f"- `{f['id']}`: {f['claim']}" for f in seen]
    L += ["", "## Facts this person carries (may state)"] + [f"- `{f['id']}`: {f['claim']}" for f in mine]
    L += ["", "## Topics"]
    for topic, keys, intent in TOPICS:
        t = topic.format(place=name)
        L += [f"### {t}", f"- Intent: {intent}"]
        for s in chain:
            for k in keys:
                op = s.get("opinions", {}).get(k)
                if op:
                    L.append(f"- Opinion ({s['level']}, {k}, lean {op['lean']}): {op['text']}")
            if "rumour" in keys:
                L += [f"- Rumour ({s['level']}): {r['text']}" for r in s.get("talk", {}).get("rumours", [])]
            if "danger" in keys:
                L += [f"- Grievance ({s['level']}): {g['text']}" for g in s.get("talk", {}).get("grievances", [])]
        L.append("")
    pathlib.Path(a.out).write_text("\n".join(L) + "\n")
    print(f"wrote {a.out}: {len(mine)} carried facts, {len(chain)} culture sheets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
