"""Whether a place is ready to hand over as built: its built check is current against its files, by the consistency
stage's own rule (built_check_current here, by content, which tools/newworld/consistency reads). Run it as the last step before
returning: a change to any file the build or the checks read after the final build and check makes the check stale, and the landing is refused.

    python -m tools.places handover <place_id>      # exit 1 when the built check is stale (names the file),
                                                    # or `stock reach` flags a stock row (material reach,
                                                    # region, trade kit), or a blocker owed in a road or walk
                                                    # (newworld/places/ways_owed.jsonl) has no reason,
                                                    # or a submitted note is still open past its answer time
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


def _committed_at(root: Path, d: Path) -> float:
    """For a check made before content stamps only: when the files the build or the checks read were last
    committed (uncommitted changes: now); the time log, `edits/` and prose never count."""
    import subprocess
    import time
    rel = str(d.relative_to(root))
    only = [rel, f":(exclude){rel}/edits", f":(exclude){rel}/timelog.jsonl", f":(exclude){rel}/*.md"]
    try:
        ct = float(subprocess.run(["git", "-C", str(root), "log", "-1", "--format=%ct", "--", *only],
                                  capture_output=True, text=True, timeout=30).stdout.strip() or 0)
        dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--", *only],
                               capture_output=True, text=True, timeout=30).stdout.strip()
    except (OSError, ValueError, subprocess.SubprocessError):
        return time.time()
    return time.time() if dirty or not ct else ct


KEPT_CHECKS = 12


def keep_by_content(shard: Path, report: dict) -> None:
    """A current check is kept under checks/<key of the content it was built from>.json (written once, when the
    check reads itself current at its end, and whenever a tree finds it current): each tree is then judged by the
    check of its own content, so a build from another tree with other place files never makes this tree's check
    stale, and one from identical files counts. The newest KEPT_CHECKS are kept."""
    import hashlib
    import json
    key = hashlib.sha256(json.dumps(report.get("stamp"), sort_keys=True).encode()).hexdigest()[:20]
    d = shard / "checks"
    p = d / f"{key}.json"
    try:
        if not p.exists():
            d.mkdir(parents=True, exist_ok=True)
            tmp = p.with_name(f".{p.name}.tmp")
            tmp.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
            tmp.replace(p)
        for old in sorted(d.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)[KEPT_CHECKS:]:
            old.unlink(missing_ok=True)
    except OSError:
        pass   # a read-only out/: the check itself still stands


def current_check(root: Path, out: Path, pid: str) -> tuple[dict | None, bool, str]:
    """(the built check that stands for the place as this tree has it, current, a line saying so): by content, every
    file the build and the checks read unchanged, and the code and records the plan stands on (check.stamp_stale);
    file times never count, and files no build or check reads (the time log, `edits/`) never make it stale. The
    shard's check.json is the newest build's; a check kept by content (checks/<key>.json) of another tree's build
    with the same place files stands as well, so a build from a tree with other files never makes this one stale.
    The line names what changed."""
    import json
    from tools.places import check as C
    shard = out / "places/shards" / pid
    chk = shard / "check.json"
    if not chk.exists():
        return None, False, f"built check NOT CURRENT: {pid} has no built check; build and check it after the last edit"
    report = json.loads(chk.read_text())
    stamp = report.get("stamp")
    if stamp is None:   # a check made before content stamps: no rebuild for that alone; its next check stamps it
        ok = chk.stat().st_mtime >= _committed_at(root, root / "newworld/places" / pid)
        return report, ok, (f"built check {'current' if ok else 'NOT CURRENT'}: made before content stamps, so judged "
                            f"by the place files' last commit until its next check stamps it by content")
    pdir = root / "newworld/places" / pid
    why = C.stamp_stale(stamp, pdir, shard)
    if not why:
        keep_by_content(shard, report)
        return report, True, "built check current: every file the build and the checks read is as it was checked (by content)"
    for kept in sorted((shard / "checks").glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True):
        try:
            k = json.loads(kept.read_text())
        except (OSError, ValueError):
            continue
        if k.get("stamp") and not C.stamp_stale(k["stamp"], pdir, shard):
            return k, True, ("built check current: a check built from these same files (by content) stands, though "
                             "another tree built the place since")
    return report, False, (f"built check NOT CURRENT: {'; '.join(why[:8])}{f' (and {len(why) - 8} more)' if len(why) > 8 else ''}: "
                           f"build and check again, or the consistency stage refuses the landing")


def built_check_current(root: Path, out: Path, pid: str) -> tuple[bool, str]:
    """(current, a line saying so): current_check without the check itself."""
    _, ok, line = current_check(root, out, pid)
    return ok, line


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
    log_ok, log_line = timelog_marked(Path(a.places_dir) / a.place_id)
    print(log_line)
    from tools.places import ways
    ways_ok, ways_line = ways.handover_line(a.place_id, Path(a.places_dir))
    print(ways_line)
    notes_ok, notes_line = notes_answered(a.place_id, Path(a.places_dir))
    print(notes_line)
    return 0 if ok and reach_ok and log_ok and ways_ok and notes_ok else 1


def notes_answered(pid: str, places: Path) -> tuple[bool, str]:
    """(passes, a line saying so): no note the owner submitted has stayed unanswered past notes.ANSWER_HOURS; each
    late one is named, so a hold on his work cannot sit unseen."""
    from tools.places import notes
    late = notes.overdue(pid, places)
    if not late:
        return True, "notes: every submitted note answered in time"
    return False, ("notes FAILS: " + "; ".join(f"{n['id']} (submitted {n.get('sent_at') or n.get('at')}): "
                                                f"\"{str(n.get('text', ''))[:80]}\"" for n in late)
                   + f" not answered within {notes.ANSWER_HOURS:g} hours: land the change on main now, over his open "
                   "session, and close it with `notes done`")


def timelog_marked(d: Path) -> tuple[bool, str]:
    """(passes, a line saying so): a place whose time log has commands (tools/places/timelog.py) has phase markers too,
    one for each step of the order of work the draft did. A place with no log passes (drafted before the log)."""
    import json
    try:
        rows = [json.loads(x) for x in (d / "timelog.jsonl").read_text().splitlines() if x.strip()]
    except (OSError, ValueError):
        return True, "time log: none (drafted before the log)"
    phases = {r["name"] for r in rows if r.get("t") == "phase"}
    if any(r.get("t") == "cmd" for r in rows) and not phases:
        return False, "time log FAILS: commands logged but no phase marked; `python -m tools.places timelog <place> phase \"<step>\"` at each step (place-system)"
    op = [r for r in rows if r.get("t") == "pass"][-1:]
    if op and op[0].get("edge") == "start":
        return True, (f"time log: pass {op[0].get('what')!r} is still open; end it (`timelog <place> pass end`) and put "
                      f"`timelog <place> report --md` in the hand-back")
    return True, f"time log: {len(rows)} rows, {len(phases)} phases marked"


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
