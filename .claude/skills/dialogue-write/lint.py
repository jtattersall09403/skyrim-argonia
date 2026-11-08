#!/usr/bin/env python3
"""Flag banned constructions in dialogue lines (bans.yaml next to this file).

Usage: python3 lint.py LINES.txt --race argonian
LINES.txt holds one line of dialogue per row; blank rows and rows starting with # are skipped.
Prints one row per hit (line number, ban id, matched text) and every `review` ban id to check by hand.
A ban with `severity: warn` is printed as a warning and never fails the run. A ban with `max_per_file: N` fails only
when it hits more than N times in the file (one person's lines: B11's warm address).
Exit code 1 when any other regex ban hits, 0 when none does, 2 on a usage error. The speaker's race is required
(any case): a missing or misspelt race used to skip the race bans silently and pass a line that breaks them.
"""
import argparse
import pathlib
import re
import sys

import yaml

BANS = pathlib.Path(__file__).with_name("bans.yaml")
RACES = ["argonian", "breton", "dunmer", "altmer", "imperial", "khajiit", "nord", "orc", "redguard", "bosmer"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("lines")
    ap.add_argument("--race", required=True, type=str.lower, choices=RACES, help="speaker race, for bans with appliesTo")
    args = ap.parse_args()

    bans = [b for b in yaml.safe_load(BANS.read_text())
            if b.get("appliesTo") is None or args.race in [r.lower() for r in b["appliesTo"]]]
    rows = pathlib.Path(args.lines).read_text().splitlines()
    hits = warns = 0
    counted: dict[str, list] = {}
    for n, row in enumerate(rows, 1):
        if not row.strip() or row.lstrip().startswith("#"):
            continue
        for b in bans:
            if b["detect"] == "review":
                continue
            for m in re.finditer(b["detect"], row):
                if b.get("max_per_file") is not None:
                    counted.setdefault(b["id"], []).append((n, m.group(0)))
                elif b.get("severity") == "warn":
                    print(f"{n}: warn {b['id']}: {m.group(0)!r}")
                    warns += 1
                else:
                    print(f"{n}: {b['id']}: {m.group(0)!r}")
                    hits += 1
    for b in bans:
        got = counted.get(b["id"], [])
        if len(got) > b.get("max_per_file", len(got)):
            print(f"{b['id']}: {len(got)} in the file, at most {b['max_per_file']}: {got}")
            hits += 1
    review = [b["id"] for b in bans if b["detect"] == "review" or b.get("severity") == "warn"]
    print(f"{hits} regex hits, {warns} warnings; review by hand: {', '.join(review)}")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
