"""Whether a place is ready to hand over as built: its built check is current against its files, by the consistency
stage's own rule (built_check_current here, which tools/newworld/consistency reads; `edits/` aside). Run it as the last step before
returning: an edit of any kind after the final build and check makes the check old, and the landing is refused.

    python -m tools.places handover <place_id>      # exit 1 when the built check is older than the place files,
                                                    # or `stock reach` flags a stock row (material reach,
                                                    # region, trade kit)
"""
from __future__ import annotations

import argparse
from pathlib import Path

from tools.places import build as B


def out_root(repo: Path = B.ROOT) -> Path:
    """out/ is untracked; a lane's worktree reads the main checkout's."""
    if (repo / "out" / "newworld").exists():
        return repo / "out"
    parts = repo.parts
    if ".claude" in parts:
        return Path(*parts[:parts.index(".claude")]) / "out"
    return repo / "out"


def changed_at(root: Path, d: Path) -> float:
    """When a place's files last changed: the later of its last commit and any uncommitted edit (a checkout's
    file times are the checkout's, so the commit time is the honest one). The owner's saves and notes (`edits/`) are
    records of studio work, not the draft: a save does not make the built check old. The promise list and the quest
    states (`promises.jsonl`, `states.jsonl`) are read by the checks, never built into the plugin: they do not either."""
    import subprocess
    rel = str(d.relative_to(root)); only = [rel, f":(exclude){rel}/edits", f":(exclude){rel}/promises.jsonl", f":(exclude){rel}/states.jsonl"]
    try:
        ct = float(subprocess.run(["git", "-C", str(root), "log", "-1", "--format=%ct", "--", *only],
                                  capture_output=True, text=True, timeout=30).stdout.strip() or 0)
        dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--", *only],
                               capture_output=True, text=True, timeout=30).stdout.strip()
    except (OSError, ValueError, subprocess.SubprocessError):
        ct, dirty = 0.0, "x"
    if dirty or not ct:
        ct = max([ct] + [f.stat().st_mtime for f in d.rglob("*.json*") if f.relative_to(d).parts[0] not in ("edits", "promises.jsonl", "states.jsonl")])
    return ct


def built_check_current(root: Path, out: Path, pid: str) -> tuple[bool, str]:
    """(current, a line saying so): the place's built check (out/places/shards/<pid>/check.json) is no older than
    its files' last change (changed_at, which leaves `edits/` out): the draft family's rule."""
    from datetime import datetime
    chk = out / "places/shards" / pid / "check.json"
    if not chk.exists():
        return False, f"built check NOT CURRENT: {pid} has no built check; build and check it after the last edit"
    made, changed = chk.stat().st_mtime, changed_at(root, root / "newworld/places" / pid)

    def at(t):
        return datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")
    if made >= changed:
        return True, f"built check current: made {at(made)}, the place files last changed {at(changed)} (edits/ aside)"
    return False, (f"built check NOT CURRENT: made {at(made)}, the place files changed after it ({at(changed)}): "
                   f"build and check again after the last edit, or the consistency stage refuses the landing")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places handover", description=__doc__.split("\n\n")[0])
    ap.add_argument("place_id")
    ap.add_argument("--places-dir", default=str(B.PLACES))
    a = ap.parse_args(argv)
    root = Path(a.places_dir).resolve().parents[1]
    ok, line = built_check_current(root, out_root(root), a.place_id)
    print(line)
    reach_ok, reach_line = stock_reach(a.place_id)
    print(reach_line)
    return 0 if ok and reach_ok else 1


def stock_reach(pid: str) -> tuple[bool, str]:
    """(passes, a line saying so): every stock row's material is one the place reaches (tools/places/stock/reach.py;
    docs/design/items.md). A place with no stock source passes."""
    from tools.argonia_world import db
    from tools.newworld import frame
    from tools.places.stock import reach
    doc = reach.load_source(pid)
    if not doc:
        return True, "stock reach: no stock source yet"
    bad = reach.flagged(db.open(frame.ROOT), pid, doc)
    if not bad:
        return True, "stock reach: every stock row fits the place's reach, its region and its holder's trade kit"
    return False, (f"stock reach FAILS: {len(bad)} stock row(s) flagged by the material reach, region or trade kit "
                   f"rules (`python -m tools.places stock reach {pid}` lists them with their rules)")
