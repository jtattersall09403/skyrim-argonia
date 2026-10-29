#!/usr/bin/env python3
"""Build a dialogue brief for one person's place topics from the imported world records, in the same shape as
quest-write/brief.py.

Usage: python3 place_brief.py --person NPC_ID --out BRIEF.md [--repo ROOT]

Reads, for the person: the registry row (world/sources/registries/npcs.json: name, race, sex, role, look,
factions, home place); the stance row (world/sources/dialogue/stance/<slug>.json: culture chain, per-topic
lean and deviation, voice); the culture sheets the chain names (world/sources/dialogue/cultures/); the place
facts (world/sources/placement/facts/<placeId>.json: facts the person carries, what the player sees, the
place's people and their topics, hostility); and the topic web (world/sources/dialogue/topics.json) for the
labels of the person's topics. Nothing is hand-made; a missing record stops the brief.
"""
import argparse
import glob
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
VOICES = HERE / "voices.md"
CLASS_KEYS = {  # topic class -> the culture-sheet opinion classes it draws on
    "local": ["place", "people", "work"], "role": ["work", "trade"], "rumour": ["rumour"],
    "faction": ["faction"], "newcomer": ["hist", "empire", "people"], "trade": ["trade"],
    "quest": [], "advice": ["danger", "directions"],
}


def voice_row(race: str) -> str:
    for line in VOICES.read_text().splitlines():
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and cells[0].lower() == (race or "").lower():
            return " | ".join(cells[1:])
    return f"no voice card for {race!r}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--person", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--repo", default=str(HERE.parents[2]))
    a = ap.parse_args()
    root = pathlib.Path(a.repo)

    npcs = {e["id"]: e for e in json.loads((root / "world/sources/registries/npcs.json").read_text())["entries"]}
    me = npcs.get(a.person)
    if me is None:
        print(f"{a.person} is not in npcs.json; no brief written")
        return 1
    place_id = (me.get("home") or {}).get("placeId")
    pf = root / f"world/sources/placement/facts/{place_id}.json"
    if not pf.exists():
        print(f"no place facts for {place_id}; no brief written")
        return 1
    place = json.loads(pf.read_text())
    world = place["world"]
    row = next((p for p in world["people"] if p["id"] == a.person), None)
    if row is None:
        print(f"{a.person} is not in {place_id}'s people; no brief written")
        return 1
    stance = None
    for f in glob.glob(str(root / "world/sources/dialogue/stance/*.json")):
        d = json.loads(pathlib.Path(f).read_text())
        stance = next((e for e in d["entries"] if e["personId"] == a.person), None) or stance
    if stance is None:
        print(f"no stance row for {a.person}; 2.4 composes one first; no brief written")
        return 1
    sheets = {}
    for f in glob.glob(str(root / "world/sources/dialogue/cultures/**/*.json"), recursive=True):
        sheets.update({e["id"]: e for e in json.loads(pathlib.Path(f).read_text()).get("entries", [])})
    chain = [sheets[s] for s in stance["chain"] if s in sheets]
    lost = [s for s in stance["chain"] if s not in sheets]
    if lost:
        print(f"culture sheets missing: {', '.join(lost)}; no brief written")
        return 1
    topics = {e["id"]: e for e in json.loads((root / "world/sources/dialogue/topics.json").read_text())["entries"]}

    uid = "npc-" + a.person.rsplit(".", 1)[-1]

    def carrier(f):
        c = f.get("carrier", {})
        return c.get("built", {}).get("uid") or c.get("queued", {}).get("ref")

    mine = [f for f in place["facts"] if carrier(f) in (uid, a.person)]
    seen = [f for f in place["facts"] if f.get("carrier", {}).get("built", {}).get("type") in ("piece-set", "visual-cue")]
    v = stance.get("voice", {})
    facs = ", ".join(x.get("factionId", str(x)) + (f" ({x['rank']})" if x.get("rank") else "")
                     for x in me.get("factions", []) if isinstance(x, dict)) or "none"

    L = [f"# Dialogue brief: {me['name']}, place topics ({world['name']})", "",
         "Built by dialogue-write/place_brief.py from the world records. Do not add facts; ask for them.", "",
         "## What the player can see",
         f"- {me.get('race')}, {me.get('sex')}; {me.get('notes', '')} Outfit: {me.get('look', {}).get('outfit')}", "",
         "## What the player cannot see", f"- Role: {me['role']}; services: {', '.join(row.get('services', [])) or 'none'}",
         f"- Factions: {facs}", f"- Depth: {me.get('depth')}; name form: {me.get('nameForm')}", "",
         "## Voice", f"- {me.get('race')}: {voice_row(me.get('race'))} (voices.md)",
         f"- Stance: chatter {v.get('chatter')}; contraction rate {v.get('contractionRate')}; "
         f"addresses the player as \"{v.get('addressTerm')}\"; favourite subject {v.get('favouriteSubject')}",
         f"- Quirk: {v.get('quirk')}"]
    L += [f"- Never mentions: {x}" for x in v.get("neverMentions", [])]
    L += ["", "## Culture (most specific last; the person differs only where the stance row says so)"]
    for s in chain:
        sp = s.get("speech", {})
        L.append(f"- **{s['name']}** ({s['level']}): formality {sp.get('formality')}; "
                 f"address: {'; '.join(x['text'] for x in sp.get('addressTerms', [])) or 'none'}; "
                 f"oaths: {'; '.join(x['text'] for x in sp.get('oaths', [])) or 'none'}; "
                 f"never says: {'; '.join(x['text'] for x in sp.get('neverSaid', [])) or 'nothing listed'}")
        for k in ("norms", "taboos", "values", "contempts"):
            if s.get(k):
                L.append(f"  - {k}: {'; '.join(x['text'] for x in s[k])}")
    h = world.get("hostility", {})
    if h:
        flips = "; ".join(f"{f['to']} when {f['when']}" for f in h.get("flips", []))
        L += ["", "## When this talk happens", f"- The place is {h.get('baseline')}" + (f"; it turns {flips}" if flips else ".")]
    L += ["", "## Others here (the player may be sent to them)"]
    L += [f"- {p['name']}: {p['role']}" for p in world["people"] if p["id"] != a.person]
    L += ["", "## What the player can see of the place"] + [f"- `{f['id']}`: {f['claim']}" for f in seen]
    L += ["", "## Facts this person carries (may state)"] + [f"- `{f['id']}`: {f['claim']}" for f in mine]
    L += ["", "## Topics (the person's topics in the place record)"]
    for tid in row.get("topics", []):
        t = topics.get(tid)
        if t is None:
            L += [f"### `{tid}`", "- Not in topics.json: ask for the topic row before writing.", ""]
            continue
        L += [f"### {t['label']} (`{tid}`, {t['topicClass']})"]
        for cls in CLASS_KEYS.get(t["topicClass"], []):
            st = stance["topics"].get(cls)
            if not st:
                continue
            src = sheets.get(st["from"], {})
            op = src.get("opinions", {}).get(cls, {})
            L.append(f"- Opinion ({cls}, lean {st['lean']}, from {st['from']}): {op.get('text', '')}")
            if st.get("deviation"):
                L.append(f"  - This person differs: lean {st['deviation']['lean']}: {st['deviation']['reason']}")
        if t["topicClass"] == "rumour":
            L += [f"- Rumour ({s['level']}): {r['text']}" for s in chain for r in s.get("talk", {}).get("rumours", [])]
            L += [f"- Grievance ({s['level']}): {g['text']}" for s in chain for g in s.get("talk", {}).get("grievances", [])]
        if t["topicClass"] == "quest":
            L.append(f"- Quest topic of {t.get('keys', {}).get('quest')}: written from that quest's brief (quest-write/brief.py), not here.")
        L.append("")
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n")
    print(f"wrote {out}: {len(mine)} carried facts, {len(chain)} culture sheets, {len(row.get('topics', []))} topics")
    return 0


if __name__ == "__main__":
    sys.exit(main())
