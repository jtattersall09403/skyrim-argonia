#!/usr/bin/env python3
"""The gate's world-reads check (decision 0030 §3): no file under tools/ or .claude/ but db.py names a `world/`
data path. Every tool, skill and agent reads and writes the world through `tools/argonia_world/db.py`.

A hit is a path to `world/sources`, `world/db`, `world/schema(s)` written as a string (`world/db/npc.jsonl`) or
as a path join (`"world" / "sources"`). Exit 0 clean, 1 with one line per hit (file:line: text).

    python3 tools/argonia_world/check_world_reads.py [--root DIR]
"""
from __future__ import annotations

import argparse
import ast
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


HASH_COMMENT = {".sh", ".ps1", ".yaml", ".yml", ".toml"}
SUB = {"sources", "db", "schema", "schemas"}


def _str(n: ast.AST) -> str | None:
    return n.value if isinstance(n, ast.Constant) and isinstance(n.value, str) else None


def py_hits(text: str) -> list[int] | None:
    """Line numbers of code that names a world/ path: string constants in expressions and path joins, never comments
    (the AST has none) or docstrings. None when the file does not parse."""
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return None
    doc = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and n.body:
            f = n.body[0]
            if isinstance(f, ast.Expr) and _str(f.value) is not None:
                doc.add(id(f.value))
    lines = set()
    for n in ast.walk(tree):
        v = _str(n)
        if v is not None and id(n) not in doc and HIT.search(v):
            lines.add(n.lineno)
        elif isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div) and _str(n.right) in SUB:
            left = n.left.right if isinstance(n.left, ast.BinOp) else n.left
            if _str(left) == "world":
                lines.add(n.lineno)
        elif isinstance(n, ast.Call):
            vals = [_str(a) for a in n.args]
            if any(a == "world" and b in SUB for a, b in zip(vals, vals[1:])):
                lines.add(n.lineno)
    return sorted(lines)


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
            src = text.splitlines()
            if p.suffix == ".py":
                found = py_hits(text)
                if found is not None:
                    out += [f"{rel}:{i}: {src[i - 1].strip()[:120]}" for i in found]
                    continue
            for i, line in enumerate(src, 1):
                if p.suffix in HASH_COMMENT and line.lstrip().startswith("#"):
                    continue
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
