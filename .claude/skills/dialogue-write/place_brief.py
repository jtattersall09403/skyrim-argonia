#!/usr/bin/env python3
"""Build a dialogue brief for one person's place topics from the imported world records, in the same shape as
quest-write/brief.py.

Usage: python3 place_brief.py --person NPC_ID --out BRIEF.md

Reads, through the world database (tools/argonia_world/db.py, decision 0030), for the person: the `npc` row (name,
race, sex, role, look, factions, home place); the `stance` rows (culture chain, per-topic lean and deviation,
voice); the `culture_sheet` rows the chain names; the place's `fact` rows (facts the person carries, what the
player sees) and its last build (`place_build`, `place_person`: the place's people and their topics, hostility);
and the `topic` rows for the labels of the person's topics. Nothing is hand-made; a missing record stops the brief.
"""
import argparse
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from tools.argonia_world import db, records  # noqa: E402
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
    a = ap.parse_args()
    w = db.open()

    me = records.person(w, a.person)
    if me is None:
        print(f"{a.person} is not an npc row; no brief written")
        return 1
    place_id = me["home"]
    build = w.get("place_build", place_id) if place_id else None
    if build is None:
        print(f"no place facts for {place_id}; no brief written")
        return 1
    people = w.query("SELECT * FROM place_person WHERE place_id = ? ORDER BY ord", place_id)
    row = next((p for p in people if p["id"] == a.person), None)
    if row is None:
        print(f"{a.person} is not in {place_id}'s people; no brief written")
        return 1
    services = w.values("SELECT value FROM place_person_services WHERE place_id = ? AND people_ord = ? ORDER BY ord",
                        place_id, row["ord"])
    my_topics = w.values("SELECT value FROM place_person_topics WHERE place_id = ? AND people_ord = ? ORDER BY ord",
                         place_id, row["ord"])
    stance = records.stance(w, a.person)
    if stance is None:
        print(f"no stance row for {a.person}; 2.4 composes one first; no brief written")
        return 1
    sheets = {s_: sh for s_ in stance["chain"] if (sh := records.sheet(w, s_)) is not None}
    chain = [sheets[s_] for s_ in stance["chain"] if s_ in sheets]
    lost = [s_ for s_ in stance["chain"] if s_ not in sheets]
    if lost:
        print(f"culture sheets missing: {', '.join(lost)}; no brief written")
        return 1
    facts = records.place_facts(w, place_id)

    slot = a.person.rsplit(".", 1)[-1]
    # A fact names its carrier by the person's id, its roster uid (npc-<slot>) or the place's npc socket for the
    # person's roster slot (socket.<place>.npc-<slot>, whose roster_slot_id is the slot).
    carriers = {a.person, "npc-" + slot} | set(w.values(
        "SELECT id FROM socket WHERE place_id = ? AND kind = 'npc' AND roster_slot_id = ?", place_id, slot))

    mine = [f for f in facts if (f["carrier_built_uid"] or f["carrier_queued_ref"]) in carriers]
    seen = [f for f in facts if f["carrier_built_type"] in ("piece-set", "visual-cue")]
    v = stance["voice"]
    facs = ", ".join(me["factions"]) or "none"

    L = [f"# Dialogue brief: {me['name']}, place topics ({build.name})", "",
         "Built by dialogue-write/place_brief.py from the world records. Do not add facts; ask for them.", "",
         "## What the player can see",
         f"- {me['race']}, {me['sex']}; {me['notes'] or ''} Outfit: {me['outfit']}", "",
         "## What the player cannot see", f"- Role: {me['role']}; services: {', '.join(services) or 'none'}",
         f"- Factions: {facs}", f"- Depth: {me['depth']}; name form: {me['name_form']}", "",
         "## Voice", f"- {me['race']}: {voice_row(me['race'])} (voices.md)",
         f"- Stance: chatter {v['chatter']}; contraction rate {v['contraction_rate']}; "
         f"addresses the player as \"{v['address_term']}\"; favourite subject {v['favourite_subject']}",
         f"- Quirk: {v['quirk']}"]
    L += [f"- Never mentions: {x}" for x in v["never_mentions"]]
    L += ["", "## Culture (most specific last; the person differs only where the stance row says so)"]
    for s in chain:
        e = s["entries"]
        L.append(f"- **{s['name']}** ({s['level']}): formality {s['formality']}; "
                 f"address: {'; '.join(e.get('address-term', [])) or 'none'}; "
                 f"oaths: {'; '.join(e.get('oath', [])) or 'none'}; "
                 f"never says: {'; '.join(e.get('never-said', [])) or 'nothing listed'}")
        for k, kind in (("norms", "norm"), ("taboos", "taboo"), ("values", "value"), ("contempts", "contempt")):
            if e.get(kind):
                L.append(f"  - {k}: {'; '.join(e[kind])}")
    h = w.get("place_build_hostility", place_id)
    if h:
        flips = "; ".join(f"{f['to']} when {records.condition(w, f['when'])}" for f in
                          w.query("SELECT * FROM place_build_hostility_flips WHERE place_id = ? ORDER BY ord", place_id))
        L += ["", "## When this talk happens", f"- The place is {h.baseline}" + (f"; it turns {flips}" if flips else ".")]
    L += ["", "## Others here (the player may be sent to them)"]
    L += [f"- {p['name']}: {p['role']}" for p in people if p["id"] != a.person]
    L += ["", "## What the player can see of the place"] + [f"- `{f['id']}`: {f['claim']}" for f in seen]
    L += ["", "## Facts this person carries (may state)"] + [f"- `{f['id']}`: {f['claim']}" for f in mine]
    L += ["", "## Topics (the person's topics in the place record)"]
    for tid in my_topics:
        t = w.get("topic", tid)
        if t is None:
            L += [f"### `{tid}`", "- Not a topic row: ask for the topic row before writing.", ""]
            continue
        L += [f"### {t.label} (`{tid}`, {t.topic_class})"]
        for cls in CLASS_KEYS.get(t.topic_class, []):
            st = stance["topics"].get(cls)
            if not st:
                continue
            src = sheets.get(st["from"]) or records.sheet(w, st["from"]) or {}
            op = src.get("opinions", {}).get(cls, "")
            L.append(f"- Opinion ({cls}, lean {st['lean']}, from {st['from']}): {op}")
            if st["deviation_lean"] is not None or st["deviation_reason"] is not None:
                L.append(f"  - This person differs: lean {st['deviation_lean']}: {st['deviation_reason']}")
        if t.topic_class == "rumour":
            L += [f"- Rumour ({s['level']}): {r}" for s in chain for r in s["entries"].get("rumour", [])]
            L += [f"- Grievance ({s['level']}): {g}" for s in chain for g in s["entries"].get("grievance", [])]
        if t.topic_class == "quest":
            L.append(f"- Quest topic of {t.keys_quest}: written from that quest's brief (quest-write/brief.py), not here.")
        L.append("")
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n")
    print(f"wrote {out}: {len(mine)} carried facts, {len(chain)} culture sheets, {len(my_topics)} topics")
    return 0


if __name__ == "__main__":
    sys.exit(main())
