"""A place's time log: where a place draft's time went, kept beside the place and committed with it.

`newworld/places/<id>/timelog.jsonl`, one JSON row per line, appended (never rewritten):
  - cmd rows, written by `python -m tools.places` itself when any verb ends (tools/places/__main__.py calls `record`):
    place, verb, sub (the look verb), kind (looking|editing|building|checking|walking|surveying|content|other), start,
    end, secs, rc, queue (seconds a job_guard run waited between the ask and its start), depth (a verb run inside
    another one is depth 1 and never counted twice), counts (what the verb knew: views, checks...).
  - phase rows, by the agent:   timelog <place> phase "<name>" [--note "..."]
  - pass rows, by the agent:    timelog <place> pass start|end "<what the lead asked>"
The log is read by nothing but its report: the build, the handover check, the consistency stage and the gate leave it out.

    python -m tools.places timelog <place> report [--md] [--gap 60]
Logging never fails a command: a read-only log, a missing place or a bad row is passed over.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

PHASES = ("plan", "site", "adapt", "streets", "rooms", "routines", "story", "dressing", "stock", "check",
          "walk loop", "fixes after lead's read", "tool fix", "waiting on lead")
KINDS = {  # look sub-verbs and top-level verbs -> the kind of activity
    "editing": {"move", "turn", "sink", "delete", "duplicate", "steps", "paint", "undo", "commit", "release", "reset",
                "snapshot", "restore", "draft", "seat", "edits", "people"},
    "building": {"build", "bundle", "finalise"},
    "checking": {"check", "handover", "probe", "truth", "units", "needs", "promises", "states", "versus", "compare"},
    "walking": {"playwalk"},
    "surveying": {"survey"},
    "content": {"stock"},
    "looking": {"at", "orbit", "walk", "section", "overview", "measure", "pick", "in", "status", "stop"},
}
COUNT: dict[str, int] = {}


def count(name: str, n: int = 1) -> None:
    """A verb says what it did (views captured, checks run); the row for its command carries it."""
    COUNT[name] = COUNT.get(name, 0) + n


def places_dir() -> Path:
    return Path(os.environ.get("ARGONIA_PLACES_DIR") or Path(__file__).resolve().parents[2] / "newworld/places")


def log_path(place: str) -> Path:
    return places_dir() / place / "timelog.jsonl"


def append(place: str, row: dict) -> bool:
    """One O_APPEND write of one line: atomic between processes. False when it could not."""
    try:
        if not log_path(place).parent.is_dir():
            return False
        fd = os.open(log_path(place), os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
        try:
            os.write(fd, (json.dumps(row, ensure_ascii=False) + "\n").encode())
        finally:
            os.close(fd)
        return True
    except Exception:
        return False


def find_place(argv: list[str]) -> str | None:
    pd = places_dir()
    for a in argv[1:]:
        if a and not a.startswith("-") and "/" not in a and a not in (".", "..") and (pd / a).is_dir():
            return a
    e = os.environ.get("ARGONIA_PLACE")
    return e if e and (pd / e).is_dir() else None


def classify(argv: list[str]) -> tuple[str, str, str]:
    verb = argv[0] if argv else ""
    sub = ""
    if verb == "look":
        rest = [a for a in argv[1:] if not a.startswith("-")][1:]  # after the place
        sub = next((a for a in rest if any(a in v for v in KINDS.values())), rest[0] if rest else "")
    key = sub or verb
    kind = next((k for k, v in KINDS.items() if key in v), "other")
    return verb, sub, kind


def job_wait(argv: list[str], now: float) -> tuple[float, str]:
    """(seconds waited, job name) when this command is a job_guard job that has just got the lock: the spool
    (~/.argonia/jobs, JOBS_DIR) holds `<name>.cmd` written at the ask and `<name>.started` touched at the start, for the
    newest started job with no result whose command names this verb. Nothing found: (0, "")."""
    jobs = Path(os.environ.get("JOBS_DIR") or Path.home() / ".argonia/jobs")
    want = " ".join(argv[:2])
    best = None
    try:
        for s in jobs.glob("*.started"):
            n = s.name[:-8]
            if (jobs / f"{n}.rc").exists() or not 0 <= now - s.stat().st_mtime < 120:
                continue
            cmd = (jobs / f"{n}.cmd").read_text(errors="replace").replace("\0", " ")
            if "tools.places" in cmd and want in cmd and (best is None or s.stat().st_mtime > best[0]):
                best = (s.stat().st_mtime, n, (jobs / f"{n}.cmd").stat().st_mtime)
    except Exception:
        return 0.0, ""
    return (round(max(0.0, best[0] - best[2]), 1), best[1]) if best else (0.0, "")


def begin(argv: list[str] | None = None) -> dict:
    """At a command's start: its clock, its depth, and its queue wait when job_guard ran it."""
    t = time.time()
    st = {"start": t, "depth": 0, "queue": 0.0, "job": ""}
    try:
        st["depth"] = int(os.environ.get("ARGONIA_TIMELOG_DEPTH", "0"))
        if st["depth"] == 0:
            st["queue"], st["job"] = job_wait(argv, t)
        os.environ["ARGONIA_TIMELOG_DEPTH"] = str(st["depth"] + 1)
        COUNT.clear()
    except Exception:
        pass
    return st


def record(argv: list[str], st: dict, rc: int) -> None:
    try:
        if not argv or argv[0] == "timelog":
            return
        place = find_place(argv)
        if not place:
            return
        end = time.time()
        verb, sub, kind = classify(argv)
        append(place, {"t": "cmd", "place": place, "verb": verb, "sub": sub, "kind": kind, "start": round(st["start"], 2),
                       "end": round(end, 2), "secs": round(end - st["start"], 1), "rc": rc, "queue": st["queue"],
                       "depth": st["depth"], "job": st.get("job", ""),
                       "args": " ".join(argv[1:])[:160], "counts": dict(COUNT)})
    except Exception:
        pass


# ---- the report -------------------------------------------------------------------------------------------------

def load(place: str) -> list[dict]:
    rows = []
    try:
        for ln in log_path(place).read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(ln))
            except ValueError:
                pass
    except OSError:
        pass
    return rows


def _t(r: dict) -> float:
    return r.get("start", r.get("at", 0.0))


def _is_full_walk(r: dict) -> bool:
    if r["verb"] == "playwalk" or r.get("sub") == "playwalk":
        return not any(f in r.get("args", "") for f in ("--changed", "--plan"))
    return False


def _phase_at(marks: list[dict], x: float) -> str:
    cur = ""
    for m in marks:
        if m["at"] <= x:
            cur = m["name"]
    return cur


def _sum_counts(cmds: list[dict]) -> dict:
    out: dict[str, int] = {}
    for r in cmds:
        for k, v in (r.get("counts") or {}).items():
            out[k] = out.get(k, 0) + v
    return out


def report(rows: list[dict], gap: float = 60.0) -> dict:
    """Sums from the event stream alone. A phase marker holds until the next one; a gap between commands (the end of
    the latest finished command to the next one's ask) is thinking/reading when over `gap` seconds, and away when no
    pass is open or the phase is waiting on the lead."""
    rows = sorted(rows, key=_t)
    if not rows:
        return {"empty": True}
    cmds = [r for r in rows if r.get("t") == "cmd" and r.get("depth", 0) == 0]
    marks = [r for r in rows if r.get("t") == "phase"]
    passes = [r for r in rows if r.get("t") == "pass"]
    t0 = min(_t(r) for r in rows)
    t1 = max(r.get("end", r.get("at", 0.0)) for r in rows)
    ph: dict[str, float] = {}
    for i, m in enumerate(marks):
        b = marks[i + 1]["at"] if i + 1 < len(marks) else t1
        ph[m["name"]] = ph.get(m["name"], 0.0) + max(0.0, b - m["at"])
    before = (marks[0]["at"] - t0) if marks else (t1 - t0)
    if before > 0.5:
        ph["(before the first phase marker)"] = before
    pas, openp = [], None
    for p in passes:
        if p["edge"] == "start":
            openp = p
        elif openp:
            pas.append((openp["what"], openp["at"], p["at"]))
            openp = None
    if openp:
        pas.append((openp["what"], openp["at"], t1))

    def inpass(x):
        return any(a <= x <= b for _, a, b in pas)
    act: dict[str, float] = {}
    queue = think = short = away = 0.0
    for r in cmds:
        act[r["kind"]] = act.get(r["kind"], 0.0) + r["secs"]
        queue += r.get("queue", 0.0)
    busy_end = None
    for r in sorted(cmds, key=lambda r: r["start"] - r.get("queue", 0.0)):
        s = r["start"] - r.get("queue", 0.0)
        if busy_end is not None and s > busy_end:
            g = s - busy_end
            mid = busy_end + g / 2
            if (pas and not inpass(mid)) or _phase_at(marks, mid) == "waiting on lead":
                away += g
            elif g > gap:
                think += g
            else:
                short += g
        busy_end = max(busy_end or 0.0, r["end"])
    act["waiting in a queue"] = queue
    act[f"thinking/reading (gaps over {gap:g}s)"] = think
    act["short gaps between commands"] = short
    act["away: between passes or waiting on lead"] = away
    return {"empty": False, "wall": t1 - t0, "phases": ph, "activity": {k: v for k, v in act.items() if v > 0},
            "longest": sorted(cmds, key=lambda r: -r["secs"])[:10],
            "tool_fix": sum(v for k, v in ph.items() if k.startswith("tool fix")),
            "builds": sum(1 for r in cmds if r["verb"] == "build"), "full_walks": sum(1 for r in cmds if _is_full_walk(r)),
            "commands": len(cmds), "passes": [(w, b - a) for w, a, b in pas], "counts": _sum_counts(cmds)}


def fmt(s: float) -> str:
    s = int(round(s))
    return f"{s // 3600}h{s % 3600 // 60:02d}m" if s >= 3600 else f"{s // 60}m{s % 60:02d}s"


def render(place: str, rep: dict, md: bool = False) -> str:
    if rep.get("empty"):
        return f"{place}: no time log yet"
    wall = rep["wall"] or 1.0
    out = [f"time log of {place}: wall {fmt(wall)}, {rep['commands']} commands, {rep['builds']} builds, "
           f"{rep['full_walks']} full walks, {fmt(rep['tool_fix'])} in tool fixes (not a future place's cost)"
           + (f"; counts {rep['counts']}" if rep["counts"] else "")]

    def table(title: str, items: list[tuple[str, float]]):
        if md:
            out.append(f"\n| {title} | time | share |\n|---|---|---|")
            out.extend(f"| {k} | {fmt(v)} | {100 * v / wall:.0f}% |" for k, v in items)
        else:
            out.append(f"\n{title}")
            out.extend(f"  {fmt(v):>8} {100 * v / wall:3.0f}%  {k}" for k, v in items)
    table("by phase", sorted(rep["phases"].items(), key=lambda kv: -kv[1]))
    table("by kind of activity", sorted(rep["activity"].items(), key=lambda kv: -kv[1]))
    if rep["passes"]:
        table("elapsed per pass", rep["passes"])
    if md:
        out.append("\n| ten longest commands | time | rc |\n|---|---|---|")
        out.extend(f"| {r['verb']} {r.get('args', '')[:70]} | {fmt(r['secs'])} | {r['rc']} |" for r in rep["longest"])
    else:
        out.append("\nten longest commands")
        out.extend(f"  {fmt(r['secs']):>8} rc{r['rc']}  {r['verb']} {r.get('args', '')[:80]}" for r in rep["longest"])
    return "\n".join(out)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places timelog", description=__doc__.split("\n\n")[0])
    ap.add_argument("place")
    ap.add_argument("what", choices=["phase", "pass", "report"])
    ap.add_argument("args", nargs="*", help="phase: <name>; pass: start|end <what the lead asked>")
    ap.add_argument("--note", default="")
    ap.add_argument("--md", action="store_true")
    ap.add_argument("--gap", type=float, default=60.0, help="a gap between commands over this many seconds is thinking/reading")
    a = ap.parse_args(argv)
    if not places_dir().joinpath(a.place).is_dir():
        print(f"no place {a.place!r}", file=sys.stderr)
        return 2
    if a.what == "report":
        print(render(a.place, report(load(a.place), a.gap), a.md))
        return 0
    now = round(time.time(), 2)
    if a.what == "phase":
        if not a.args:
            print("phase needs a name; the steps: " + ", ".join(PHASES), file=sys.stderr)
            return 2
        ok = append(a.place, {"t": "phase", "at": now, "name": " ".join(a.args), "note": a.note})
    else:
        if not a.args or a.args[0] not in ("start", "end"):
            print('pass needs start|end and what the lead asked: timelog <place> pass start "<ask>"', file=sys.stderr)
            return 2
        ok = append(a.place, {"t": "pass", "at": now, "edge": a.args[0], "what": " ".join(a.args[1:]) or "(unnamed)"})
    if not ok:
        print("timelog: could not write the log (not fatal)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
