#!/usr/bin/env python3
"""What the plan already says about a topic: one search over every place the plan lives.

    plan_find.py spell tome            lines holding ANY of the words, grouped by layer, the fullest files first
    plan_find.py --all hist blessing   lines holding ALL of the words
    plan_find.py --layer story spell   one layer in full (every file, up to --lines hits each)
    plan_find.py --map                 the layers: where each kind of answer lives

Run it before a proposal, a brief, or a claim that something is missing, with the topic's words and their
synonyms; read the fullest files it names. It searches the plan (rulings, decisions, records, story, lore, design),
not the built game: say "as planned" for what it finds and measure the game for "as built".
A word matches inside longer words (spell finds spells, spellmaking); case is ignored.
"""
import argparse
import glob
import json
import os
import re
import sys

ROOT = os.environ.get("PLAN_FIND_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# layer: (what kind of answer lives there, globs). The order is the order of authority and of the report.
LAYERS = {
    "rulings": ("what the owner has ruled, and his bar for quests, story and writing",
                ["docs/owner-rulings.md", "story/design/owner-bar.md", "docs/research/writing/owner-rulings-on-factions.md"]),
    "decisions": ("the numbered decisions and the binding rules",
                  ["docs/decisions/*.md", "CLAUDE.md"]),
    "plan": ("the plan, its phases and what is done or parked for later",
             ["docs/PLAN.md", "docs/PROGRESS.md", "docs/phases/**/*.md"]),
    "records": ("what each place, person and culture of the new world promises (sellers, trainers, blessings, "
                "foes, rewards): the story database",
                ["newworld/story/data/db/*.jsonl"]),
    "story": ("what the main quest and each faction's line teach, give, require and stage; quest records",
              ["story/design/quests/lines/*.md", "story/design/quests/*.md", "newworld/story/quests/**/*.yaml"]),
    "lore": ("the lore dossiers and our extrapolations from them",
             ["story/lore/**/*.md"]),
    "design": ("how things are built: the design pages and the skills' recipes",
               ["docs/design/*.md", ".claude/skills/**/*.md", ".claude/skills/**/*.yaml"]),
    "research": ("evidence gathered before: mods, Skyrim's own records, earlier proposals",
                 ["docs/research/**/*.md"]),
}
# geometry and bulk tables of the database that hold no prose
SKIP = {"cell.jsonl", "border.jsonl", "border_vertex.jsonl", "loading-facts.md"}
MAX_BYTES = 4_000_000


def files(layer):
    seen = []
    for pat in LAYERS[layer][1]:
        for p in sorted(glob.glob(os.path.join(ROOT, pat), recursive=True)):
            if os.path.isfile(p) and os.path.basename(p) not in SKIP and os.path.getsize(p) <= MAX_BYTES and p not in seen:
                seen.append(p)
    return seen


def show(line, path):
    """A hit as one short line; a database row shows its ids and its prose."""
    line = line.strip()
    if path.endswith(".jsonl"):
        try:
            d = json.loads(line)
            ids = " ".join(str(v) for k, v in d.items() if k.endswith("_id") or k == "id")
            text = " | ".join(str(v) for k, v in d.items() if isinstance(v, str) and not (k.endswith("_id") or k == "id"))
            line = f"{ids}: {text}" if ids else text
        except ValueError:
            pass
    return line[:200]


def search(words, need_all, layers):
    pats = [re.compile(re.escape(w), re.I) for w in words]
    out = {}
    for layer in layers:
        for p in files(layer):
            hits = []
            try:
                with open(p, encoding="utf-8", errors="replace") as f:
                    for n, line in enumerate(f, 1):
                        m = [bool(r.search(line)) for r in pats]
                        if (all(m) if need_all else any(m)):
                            hits.append((n, show(line, p)))
            except OSError:
                continue
            if hits:
                out.setdefault(layer, []).append((os.path.relpath(p, ROOT), hits))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("words", nargs="*")
    ap.add_argument("--all", action="store_true", help="a line must hold every word")
    ap.add_argument("--layer", choices=list(LAYERS), help="one layer, every file")
    ap.add_argument("--files", type=int, default=6, help="files shown per layer (default 6)")
    ap.add_argument("--lines", type=int, default=3, help="hits shown per file (default 3; 40 with --layer)")
    ap.add_argument("--map", action="store_true")
    a = ap.parse_args(argv)
    if a.map or not a.words:
        for name, (what, pats) in LAYERS.items():
            print(f"{name}: {what}\n    {', '.join(pats)}")
        print("not searched: the built game (the plugins, the stack, the place files): measure it and say 'as built'")
        return 0 if a.map else 2
    layers = [a.layer] if a.layer else list(LAYERS)
    n_files = 10**6 if a.layer else a.files
    n_lines = 40 if a.layer and a.lines == 3 else a.lines
    found = search(a.words, a.all, layers)
    for layer in layers:
        rows = sorted(found.get(layer, []), key=lambda r: -len(r[1]))
        total = sum(len(h) for _, h in rows)
        print(f"\n== {layer}: {total} lines in {len(rows)} files ({LAYERS[layer][0]})")
        for path, hits in rows[:n_files]:
            print(f"  {path}  ({len(hits)})")
            for n, text in hits[:n_lines]:
                print(f"    {n}: {text}")
        if len(rows) > n_files:
            rest = ", ".join(f"{os.path.basename(p)} ({len(h)})" for p, h in rows[n_files:n_files + 12])
            print(f"  and {len(rows) - n_files} more files: {rest}{' ...' if len(rows) > n_files + 12 else ''}")
    if not found:
        print("\nnothing found: try synonyms before calling it absent from the plan")
    return 0


if __name__ == "__main__":
    sys.exit(main())
