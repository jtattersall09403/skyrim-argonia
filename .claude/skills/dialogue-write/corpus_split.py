#!/usr/bin/env python3
"""Split the private Morrowind corpus into topic-group files for the corpus-find agents.

Usage: python3 corpus_split.py [CORPUS.json] [OUT_DIR]
Defaults: $ARGONIA_PRIVATE/dialogue/morrowind/morrowind-full.json -> $ARGONIA_PRIVATE/dialogue/morrowind/groups/
Both stay under $ARGONIA_PRIVATE, never in the repo (decision 0003).
"""
import json
import os
import pathlib
import re
import sys

RACES = ["argonian", "breton", "dunmer", "altmer", "imperial", "khajiit", "nord", "orc", "redguard", "bosmer"]
GROUPS = {
    **{f"greetings-{r}": (lambda r: lambda e: e["kind"] in ("greeting", "refusal", "bark") and e["speakerRace"] == r)(r)
       for r in RACES},
    "greetings-any": lambda e: e["kind"] in ("greeting", "refusal", "bark") and e["speakerRace"] not in RACES,
    "trade-and-service": lambda e: e["kind"] == "service" or re.search(r"\b(my trade|services|training|travel)\b", e["topic"], re.I),
    "place-and-directions": lambda e: e["kind"] == "directions" or e["topic"] in ("specific place", "someone in particular"),
    "rumours-and-advice": lambda e: e["kind"] == "rumour",
    "creatures-and-danger": lambda e: re.search(r"\b(creature|beast|monster|blight|disease|danger|wolves|rats|mudcrab|racers?|undead|ghost|daedra)\b", e["topic"] + " " + e["text"], re.I),
    "quest-arcs": lambda e: e["source"] not in ("GDV",) and not e["source"].startswith("GD-"),
}
# Topic answers no group above took: places, people, lore, factions.
_taken = list(GROUPS.values())
GROUPS["topics-general"] = lambda e: e["kind"] == "topic" and not any(g(e) for g in _taken)


def main() -> int:
    if "ARGONIA_PRIVATE" not in os.environ and len(sys.argv) < 3:
        sys.exit("set ARGONIA_PRIVATE or pass CORPUS.json and OUT_DIR")
    base = pathlib.Path(os.environ.get("ARGONIA_PRIVATE", ".")) / "dialogue" / "morrowind"
    corpus = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else base / "morrowind-full.json"
    out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else base / "groups"
    out.mkdir(parents=True, exist_ok=True)
    entries = json.loads(corpus.read_text())["entries"]
    header = "# id | kind | race/sex | faction-or-class | register | disposition band | topic | text\n"
    for name, test in GROUPS.items():
        rows = [f"{e['id']} | {e['kind']} | {e['speakerRace']}/{e['speakerSex']} | {e['factionOrClass']} | "
                f"{e['register']} | disp:{e['dispositionBand']} | topic:{e['topic']} | {e['text']}"
                for e in entries if test(e)]
        (out / f"{name}.txt").write_text(header + "\n".join(rows) + "\n")
        print(f"{name}: {len(rows)} lines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
