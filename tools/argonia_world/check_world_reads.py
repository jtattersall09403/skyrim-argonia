#!/usr/bin/env python3
"""The gate's world-reads check (decision 0030 §3): no file under tools/ or .claude/ but db.py names a `world/`
data path. Every tool, skill and agent reads and writes the world through `tools/argonia_world/db.py`.

A hit is a path to `world/sources`, `world/db`, `world/schema(s)` written as a string (`world/db/npc.jsonl`) or
as a path join (`"world" / "sources"`). Exit 0 clean, 1 with one line per hit (file:line: text).

    python3 tools/argonia_world/check_world_reads.py [--root DIR]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCAN = ("tools", ".claude")
HIT = re.compile(r"""(?<![\w.-])world[/\\]+(?:sources|db|schemas?)\b|["']world["']\s*[/,]\s*["'](?:sources|db|schemas?)["']""")
# Families not yet tables (decision 0030 §6): a skill's instructions may send an agent to read them from the import,
# read-only, until the chunk named here migrates them. Code never reads them; the list shrinks to nothing.
UNMIGRATED = {"lore": "the lore family (prose dossiers), with the chunk that first reads it as data",
              "blueprints": "the place builds (0.4 §d and the world track)"}
UNMIGRATED_HIT = re.compile(r"world/sources/(" + "|".join(UNMIGRATED) + r")/")
# The only files allowed to name a world/ data path, each with its reason.
ALLOW = {
    "tools/argonia_world/db.py": "the one reader and writer of world/ (decision 0030 §3)",
    "tools/argonia_world/check_world_reads.py": "this check: names the paths it forbids",
    "tools/import_old.py": "the one-off 0.1 importer that wrote world/sources; it never runs again on a migrated family",
}
# Folders of exports from the database (quest_record.py export): their world/ strings are provenance values in the
# rows (a quest's `sources`), not reads.
EXPORTS = (".claude/skills/quest-write/examples/",)
SKIP_DIRS = {"__pycache__", "bin", "obj", "node_modules", ".pytest_cache"}
TEXT = {".py", ".md", ".yaml", ".yml", ".json", ".sh", ".ps1", ".cs", ".toml", ".txt", ".sql"}


def scan(root: Path) -> list[str]:
    out = []
    for top in SCAN:
        base = root / top
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*")):
            if not p.is_file() or p.suffix not in TEXT or SKIP_DIRS & set(p.relative_to(root).parts):
                continue
            rel = p.relative_to(root).as_posix()
            if rel in ALLOW or rel.startswith(EXPORTS):
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if HIT.search(line) and not (p.suffix == ".md" and not HIT.search(UNMIGRATED_HIT.sub("", line))):
                    out.append(f"{rel}:{i}: {line.strip()[:120]}")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=str(REPO))
    a = ap.parse_args(argv)
    hits = scan(Path(a.root))
    if hits:
        print(f"world-reads: {len(hits)} direct world/ path(s) outside db.py (read through tools/argonia_world/db.py):")
        print("\n".join("  " + h for h in hits))
        return 1
    print("world-reads: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
