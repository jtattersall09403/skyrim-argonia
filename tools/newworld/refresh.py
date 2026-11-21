"""Bring everything generated from the new world's story-facing sources up to date, in order, in one command.

    ~/.argonia/venv/bin/python -m tools.newworld.refresh           # refresh what is stale; say what changed
    ~/.argonia/venv/bin/python -m tools.newworld.refresh --dry     # say what is stale; write nothing
    ~/.argonia/venv/bin/python -m tools.newworld.refresh --atlas   # and build the Atlas page when it is behind

A change to a place's story-facing data (its research record, its people source, its needs judgements, its stock)
reaches three generated things, each read from the one before:

1. the database tables (newworld/story/data/db): `build_db`, whole (it loads the stock, people and needs tables
   too), then `wealth derive` (each place's wealth, from the tables), then `stockdb load` when the wealth file
   changed. Run only when a source the world rebuild's db stage reads (rebuild.DB_SOURCES) or a table differs from
   the last refresh's stamp (out/newworld/refresh/stamp.json): quick when nothing changed.
2. the story digest (story/design/world, `story_digest`): rewritten only when a fresh generation differs, dates aside.
3. the story explorer page (`story_explorer build`, out/story-explorer): built when the published page is behind.

It ends by saying which committed files changed (commit them by path) and whether the story explorer and the Atlas
now need republishing, with the steps (the story-feedback skill, and world-build for the Atlas).
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DB = Path("newworld/story/data/db")
STAMP = Path("out/newworld/refresh/stamp.json")
WEALTH = Path("newworld/sources/stock/place_wealth.json")
PY = sys.executable


def _files(root: Path, spec: str) -> list[Path]:
    """The files one rebuild source names ("src:glob" under the repository, "out:glob" under out/; a "#fields" tail
    names fields of the file, which is hashed whole here)."""
    kind, _, pat = spec.partition(":")
    pat = pat.split("#", 1)[0]
    base = root if kind == "src" else root / "out" if kind == "out" else None
    if base is None:
        return []
    return sorted(Path(p) for p in glob.glob(str(base / pat), recursive=True) if Path(p).is_file())


def _digest(paths) -> str:
    h = hashlib.sha256()
    for p in paths:
        h.update(str(p).encode() + b"\0" + p.read_bytes() + b"\0")
    return h.hexdigest()[:20]


def table_files(root: Path) -> list[Path]:
    return sorted((root / DB).glob("*.jsonl"))


def tables_key(root: Path) -> str:
    """The digest of everything the tables are made from, and of the tables themselves."""
    from tools.newworld.rebuild import DB_SOURCES
    srcs = sorted({p for s in DB_SOURCES for p in _files(root, s)})
    return _digest(srcs + table_files(root))


def _snapshot(paths) -> dict[str, str]:
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def _changed(before: dict, after: dict, root: Path) -> list[str]:
    return sorted(str(Path(k).relative_to(root)) for k in set(before) | set(after) if before.get(k) != after.get(k))


def _run(*args: str, root: Path) -> None:
    r = subprocess.run([PY, "-m", *args], cwd=root, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"refresh: `python -m {' '.join(args)}` failed (exit {r.returncode}):\n{r.stdout[-2000:]}{r.stderr[-2000:]}")


def refresh_tables(root: Path, dry: bool) -> tuple[bool, list[str]]:
    """(stale, committed files changed)."""
    stamp = root / STAMP
    key = tables_key(root)
    if stamp.exists() and json.loads(stamp.read_text()).get("tables") == key:
        return False, []
    if dry:
        return True, []
    watch = table_files(root) + [root / WEALTH]
    before = _snapshot(watch)
    _run("tools.newworld.build_db", root=root)
    w0 = _snapshot([root / WEALTH])
    _run("tools.newworld.wealth", "derive", root=root)
    if _snapshot([root / WEALTH]) != w0:
        _run("tools.newworld.stockdb", "load", root=root)
    changed = _changed(before, _snapshot(table_files(root) + [root / WEALTH]), root)
    stamp.parent.mkdir(parents=True, exist_ok=True)
    stamp.write_text(json.dumps({"tables": tables_key(root)}) + "\n")
    return True, changed


def _undated(p: Path) -> str | None:
    return re.sub(r"\d{4}-\d{2}-\d{2}", "D", p.read_text(encoding="utf-8")) if p.exists() else None


def refresh_digest(root: Path, dry: bool) -> list[str]:
    """The digest files a fresh generation changes (dates aside); rewritten unless dry."""
    from tools.newworld import story_digest as sd
    out = root / sd.OUT.relative_to(sd.REPO) if sd.OUT.is_relative_to(sd.REPO) else sd.OUT
    with tempfile.TemporaryDirectory() as td:
        sd.generate(Path(td), today="0000-00-00")
        new = {f.relative_to(td): _undated(f) for f in Path(td).rglob("*.md")}
    stale = sorted(str((out / rel).relative_to(root)) for rel, text in new.items() if _undated(out / rel) != text)
    if stale and not dry:
        sd.generate(out)
    return stale


def explorer_state(root: Path, dry: bool) -> str | None:
    """None when the published story explorer is current; else what to do (built first, unless dry)."""
    from tools.newworld import story_explorer as se
    msg = se.check(root)
    if msg and not dry:
        se.generate(root)
    return msg


def atlas_state(root: Path, dry: bool, build: bool) -> str | None:
    from tools.newworld import atlas_state as at
    msg = at.check(root)
    if msg and build and not dry:
        _run("tools.newworld.map_page", root=root)
    return msg


def refresh(root: Path = REPO, dry: bool = False, atlas: bool = False, say=print) -> dict:
    """The chain in order. Returns {tables_stale, changed, digest, explorer, atlas}."""
    stale, changed = refresh_tables(root, dry)
    say(f"tables: {'stale' if stale else 'current'}"
        + (f"; {len(changed)} file(s) changed: {', '.join(changed[:12])}{' ...' if len(changed) > 12 else ''}" if changed
           else ("; rebuilt, nothing changed" if stale and not dry else "")))
    digest = refresh_digest(root, dry)
    say(f"story digest: {'current' if not digest else ('stale: ' if dry else 'rewritten: ') + ', '.join(digest)}")
    ex = explorer_state(root, dry)
    say("story explorer: published page current" if not ex else
        f"story explorer: NEEDS REPUBLISHING{' (built out/story-explorer)' if not dry else ''}. {ex}")
    at = atlas_state(root, dry, atlas)
    say("Atlas: published page current" if not at else f"Atlas: NEEDS REPUBLISHING. {at}")
    files = changed + digest
    if files and not dry:
        say(f"commit by path: {' '.join(files)}")
    return {"tables_stale": stale, "changed": changed, "digest": digest, "explorer": ex, "atlas": at}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.newworld.refresh", description=__doc__.split("\n\n")[0])
    ap.add_argument("--dry", action="store_true", help="say what is stale; write nothing")
    ap.add_argument("--atlas", action="store_true", help="build the Atlas page (map_page) when it is behind")
    a = ap.parse_args(argv)
    refresh(REPO, a.dry, a.atlas)
    return 0


if __name__ == "__main__":
    sys.exit(main())
