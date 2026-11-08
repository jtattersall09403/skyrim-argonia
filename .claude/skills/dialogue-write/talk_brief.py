#!/usr/bin/env python3
"""Talk briefs: one BM&V person's topics (docs/design/talk.md), built from the talk tables, and their written lines
loaded back.

    python3 .claude/skills/dialogue-write/talk_brief.py brief --talker "02A1E7:Black Marsh.esm" --out BRIEF.md
    python3 .claude/skills/dialogue-write/talk_brief.py load LINES.tsv --talker "02A1E7:Black Marsh.esm"

Reads, through the world database: the census row (`bmv_talker`: race, sex, class, factions, cell, spot), the
authored `talker` row (name, trade, spot, backstory, lore, personality), the person's `talker_topic` rows and the `talk_fact`
rows they name, the `talk_topic` catalogue, and the race's voice card. Nothing is hand-made; a missing row stops it.

LINES.tsv: one reply per line, `<topic id>\\t<text>`; a topic's second line is the reply's next response (the
person goes on speaking). `load` replaces the person's talk_line rows and marks the talker written.
"""
import argparse
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from tools.argonia_world import db  # noqa: E402

RACE = {"ArgonianRace": "Argonian", "DarkElfRace": "Dunmer", "ImperialRace": "Imperial", "KhajiitRace": "Khajiit",
        "NordRace": "Nord", "BretonRace": "Breton", "HighElfRace": "Altmer", "WoodElfRace": "Bosmer",
        "OrcRace": "Orc", "RedguardRace": "Redguard"}
# The talker row's personality columns (docs/design/talk.md, "Personality"), in brief order.
PERSONALITY = {"temperament": "Temperament", "manner": "Manner of speech", "wants": "Wants", "grudge": "Grudge",
               "notices": "Notices", "opinions": "Opinions", "secret": "Secret (hidden)"}


def voice_row(race: str) -> str:
    for line in (HERE / "voices.md").read_text().splitlines():
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and cells[0].lower() == race.lower():
            return " | ".join(cells[1:])
    return f"no voice card for {race!r}"


def brief(w, who: str, out: pathlib.Path) -> int:
    c, t = w.get("bmv_talker", who), w.get("talker", who)
    if c is None or t is None:
        print(f"{who}: no census or talker row; no brief written")
        return 1
    race = RACE.get(c.race or "", c.race or "unknown")
    tts = w.rows("talker_topic", talker=who)
    if not tts:
        print(f"{who}: no topics assigned; no brief written")
        return 1
    L = [f"# Talk brief: {t.known_as} ({who})", "",
         "Write each topic's reply in this person's voice. State only the facts listed under the topic; add none. "
         "One to three sentences a reply (a route may take four); a second line only where the person would go on. "
         "No Skyrim place, person or thing (decision 0006). British English.", "",
         "**Directions** are routes from where the person stands, as Morrowind gives them: retell the legs in order "
         "with their landmarks and headings (\"walk west until you see the wrecked boat, then follow the shore "
         "north...\"), in this person's words; drop a leg's count of paces or round it as a local would, merge two "
         "short legs, but never add a landmark, change a heading or skip a turn. Vary the telling with the person; "
         "a place in sight is paces and a compass point only.", "",
         "**Standing.** The player is a stranger unless they become a friend. Every topic reply is said to a "
         "stranger: neutral or cool by temperament, no warm address. The friend greeting is the one place a warm "
         "word fits; at most two warm address terms (\"my friend\", \"brother\", \"dear\") in all of this person's "
         "lines (lint B11).", "",
         "## Who", "",
         f"- Seen: {race}, {c.sex}; census class {c.class_name}; factions {c.factions or 'none'}; "
         f"voice type {c.voice or 'none (our silent voice)'}.",
         f"- Trade: {t.trade}. Spot: {t.spot}.",
         f"- Backstory: {t.backstory}",
         f"- Lore it rests on: {t.lore}",
         f"- Voice card ({race}): {voice_row(race)}", ""]
    pers = [(k, getattr(t, k, "")) for k in PERSONALITY]
    if any(v for _, v in pers):
        L += ["## Personality", "",
              "Every reply carries this person: their temperament and manner shape the wording, what they want, resent "
              "and notice colours what they choose to say, and their opinions come out where a topic touches the people "
              "or places named. None of it is a fact to state as news; the secret stays hidden unless a topic asks for "
              "it, and then it comes out only grudgingly. Two people given the same topic must not sound alike.", ""]
        L += [f"- {PERSONALITY[k]}: {v}" for k, v in pers if v]
        L.append("")
    L += ["## Topics", ""]
    for tt in tts:
        tp = w.get("talk_topic", tt.topic)
        L += [f"### {tt.topic}: \"{tp.prompt}\"", "", f"About: {tp.about}.", ""]
        ids = [f.strip() for f in tt.facts.split(",") if f.strip()]
        if not ids:
            L += ["Facts: none beyond the backstory above.", ""]
        for fid in ids:
            f = w.get("talk_fact", fid)
            if f is None:
                print(f"{who}: fact {fid} missing; no brief written")
                return 1
            L.append(f"- `{fid}`: {f.claim}")
        L.append("")
    L += ["## Output", "", "A TSV file, one reply per line: `<topic id>` TAB `<text>`. Every topic above once or "
          "twice; nothing else."]
    out.write_text("\n".join(L) + "\n")
    print(f"brief: {out} ({len(tts)} topics)")
    return 0


def load(w, who: str, path: pathlib.Path) -> int:
    allowed = {tt.topic for tt in w.rows("talker_topic", talker=who)}
    rows, n = [], {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        topic, text = line.split("\t", 1)
        if topic not in allowed:
            print(f"{topic}: not one of {who}'s topics")
            return 1
        n[topic] = n.get(topic, 0) + 1
        rows.append(dict(talker=who, topic=topic, ord=n[topic], text=text.strip()))
    missing = allowed - set(n)
    if missing:
        print(f"topics with no line: {sorted(missing)}")
        return 1
    w.delete("talk_line", talker=who)
    w.insert_many("talk_line", rows)
    w.update("talker", who, status="written")
    w.save()
    print(f"talk_line: {len(rows)} rows for {who}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["brief", "load"])
    ap.add_argument("--talker", required=True)
    ap.add_argument("--out")
    ap.add_argument("lines", nargs="?")
    a = ap.parse_args()
    w = db.open()
    if a.cmd == "brief":
        return brief(w, a.talker, pathlib.Path(a.out))
    return load(w, a.talker, pathlib.Path(a.lines))


if __name__ == "__main__":
    sys.exit(main())
