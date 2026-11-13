"""python -m tools.places notes-batch <place_id>: the notes the owner sent from the studio, actioned by one headless
agent (docs/design/place-studio.md, Notes for the agent).

The studio's Send (tools/places/notes.py: send) marks every unsent note of the place sent as one batch and calls
`start`, which launches this under tooling/job_guard.sh as the finalise chain launches its own (the machine stays
awake while it runs, and a stopped machine relaunches it at boot). One notes agent runs at a time: each run holds a
lock for its whole length, so a batch sent while another runs waits for it and then takes every sent note still
open. The agent reads the notes with `python -m tools.places notes`, answers each with a narrow change to the place
and closes it with `notes done ... --reply`; a question for the owner, or a change larger than a narrow one, is
answered with a reply that says so and is not done. What it cost and said is kept in out/places/notes-runs/.

    python -m tools.places notes-batch helstrom          run the agent on the place's sent, open notes
    python -m tools.places notes-batch helstrom --dry    print the prompt and the command; run nothing
NOTES_AGENT_CMD replaces the agent's command (tests): it is run with the place id and the prompt's file appended."""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

from tools.places import notes

CODE_REPO = Path(__file__).resolve().parents[2]
OUT = CODE_REPO / "out" / "places" / "notes-runs"
BUDGET_USD = 10.0   # half a percent of the weekly allowance (1% is about $19); a batch of a few notes uses far less
MAX_TURNS = 80
VENV_PY = Path.home() / ".argonia/venv/bin/python"
PY = str(VENV_PY) if VENV_PY.exists() else sys.executable


def open_notes(place_id: str, places: Path) -> list[dict]:
    return [n for n in notes.read(place_id, places) if notes.state(n) == "sent"]


def prompt(place_id: str, places: Path, rows: list[dict]) -> str:
    ours = places.resolve() == notes.PLACES.resolve()
    where = "" if ours else f" --places {places}"
    commit = (f"""
Commit what you changed by path, with the notes file, in one commit: `tooling/lane_commit.sh -m "{place_id}: the
owner's studio notes <ids>" -- <each file you changed> newworld/places/{place_id}/edits/notes.jsonl`.""" if ours else """
This is a test place outside the repository: commit nothing.""")
    listed = "\n\n".join(notes.show(place_id, n) for n in rows)
    return f"""The owner wrote notes on the place {place_id} in the place studio and sent them to you as one batch. Read
them with `{PY} -m tools.places notes {place_id}{where}` (they are also below, as they stood when sent). Answer every
one of them:
- A note that asks for a change to the place: make it as a narrow change. Follow the place-build skill
  ({CODE_REPO / '.claude/skills/place-build/SKILL.md'}) for which stage owns the change and how it is made. Apply only
  the step that needs changing to the committed place files and keep every other row as it is: never redraft the
  whole place, and never regenerate over the owner's studio edits.
- Then close it: `{PY} -m tools.places notes done {place_id} <note id>{where} --reply "..."`, the reply one or two
  plain English sentences for the owner, who reads it beside the note in the studio: what you changed and where.
- A note that is a question for the owner, or that asks for more than a narrow change (a whole redraft, a new
  building, anything you cannot do correctly as a narrow change): change nothing for it, and close it with a reply
  that says so plainly and what it would take.
Touch nothing outside this place's files and its notes. Do not post to GitHub or start other agents.{commit}

The notes:

{listed}
"""


def agent_cmd(place_id: str, text: str, prompt_file: Path, budget: float, turns: int) -> list[str]:
    override = os.environ.get("NOTES_AGENT_CMD")
    if override:
        return shlex.split(override) + [place_id, str(prompt_file)]
    tools = ["Read", "Glob", "Grep", "Edit", "Write", "Skill",
             f"Bash({PY} -m tools.places:*)", "Bash(python -m tools.places:*)", "Bash(python3 -m tools.places:*)",
             "Bash(tooling/lane_commit.sh:*)", "Bash(git status:*)", "Bash(git diff:*)", "Bash(git log:*)"]
    return ["claude", "-p", text, "--output-format", "json", "--max-budget-usd", f"{budget:.2f}",
            "--max-turns", str(turns), "--permission-mode", "acceptEdits", "--allowedTools", ",".join(tools),
            "--no-session-persistence"]


def run(place_id: str, places: Path = notes.PLACES, out: Path = OUT, budget: float = BUDGET_USD,
        turns: int = MAX_TURNS) -> int:
    """One batch: wait for any other notes agent, then run the agent on every sent, open note of the place."""
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "agent.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        rows = open_notes(place_id, places)
        if not rows:
            print(f"{place_id}: no sent, open notes (another run answered them)")
            return 0
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        text = prompt(place_id, places, rows)
        pf = out / f"{place_id}.{stamp}.prompt.md"
        pf.write_text(text)
        cmd = agent_cmd(place_id, text, pf, budget, turns)
        ids = [n["id"] for n in rows]
        print(f"{place_id}: the agent started on {len(ids)} note(s) {' '.join(ids)} (budget ${budget:.2f}, {turns} turns)",
              flush=True)
        env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE_CODE_")}
        try:
            r = subprocess.run(cmd, cwd=CODE_REPO, capture_output=True, text=True, env=env, timeout=3600)
            rc, said, err = r.returncode, r.stdout, r.stderr
        except (OSError, subprocess.TimeoutExpired) as e:
            rc, said, err = -1, "", str(e)
        try:
            meta = json.loads(said) if said.strip().startswith("{") else {}
        except json.JSONDecodeError:
            meta = {}
        left = [n["id"] for n in open_notes(place_id, places) if n["id"] in ids]
        record = {"place_id": place_id, "at": stamp, "notes": ids, "rc": rc, "cost_usd": meta.get("total_cost_usd"),
                  "turns": meta.get("num_turns"), "still_open": left, "result": str(meta.get("result", ""))[-2000:],
                  "stderr": err[-1000:]}
        (out / f"{place_id}.{stamp}.json").write_text(json.dumps(record, indent=1) + "\n")
        print(f"{place_id}: agent rc {rc}, cost ${record['cost_usd']}, turns {record['turns']}; "
              f"{len(ids) - len(left)} closed, still open: {' '.join(left) or 'none'}")
        return 0 if rc == 0 and not left else 1


def start(place_id: str, places: Path = notes.PLACES, repo: Path = CODE_REPO) -> str:
    """Launch a batch under tooling/job_guard.sh; returns the job's name. Each send is its own job; the run's lock
    keeps them one at a time."""
    name = f"notes.{place_id}.{time.strftime('%Y%m%dT%H%M%S', time.gmtime())}"
    cmd = [str(repo / "tooling/job_guard.sh"), "run", name, "--", PY, "-m", "tools.places", "notes-batch", place_id]
    if places.resolve() != notes.PLACES.resolve():
        cmd += ["--places", str(places)]
    subprocess.Popen(cmd, cwd=repo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    return name


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places notes-batch")
    ap.add_argument("place_id")
    ap.add_argument("--places", type=Path, default=notes.PLACES, help="the places folder (a test place's)")
    ap.add_argument("--budget", type=float, default=BUDGET_USD)
    ap.add_argument("--max-turns", type=int, default=MAX_TURNS)
    ap.add_argument("--dry", action="store_true", help="print the prompt and the command; run nothing")
    a = ap.parse_args(argv)
    if a.dry:
        text = prompt(a.place_id, a.places, open_notes(a.place_id, a.places))
        print(text)
        print(shlex.join(agent_cmd(a.place_id, "<the prompt above>", Path("<prompt file>"), a.budget, a.max_turns)))
        return 0
    return run(a.place_id, a.places, budget=a.budget, turns=a.max_turns)
