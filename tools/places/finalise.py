"""python -m tools.places finalise <place_id> <save_id>: the owner's save into the place, the build, the lessons,
the report (docs/design/place-studio.md, Finalise).

Four steps: record, build, learn, report. Each writes `<step>.done` under out/places/runs/<run_id>/ when it ends; a
rerun skips every step with a stamp, so a run killed anywhere resumes at the first step without one. state.json is
what the studio reads (`read_run`); run.log is the log. `start` launches the chain under tooling/job_guard.sh.

A conflict in the save stops the chain at record (nothing is applied; the save is untouched). A failed build or
check does not: the edits stay recorded and the report says what failed and what it means. A lessons agent that
fails or runs over budget leaves the skill as it was; the chain completes and the report says how to rerun it
(`--relearn`).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shlex
import signal
import subprocess
import sys
from pathlib import Path

from tools.places import edits

CODE_REPO = Path(__file__).resolve().parents[2]
STEPS = ("record", "build", "learn", "report")
BUILD_VERBS = ("seat", "build", "check")
BUDGET_USD = 30.0   # the owner was told 1 to 2% of the weekly allowance per finalise (1% is about $19)
MAX_TURNS = 60
VENV_PY = Path.home() / ".argonia/venv/bin/python"
PY = str(VENV_PY) if VENV_PY.exists() else sys.executable   # the project's interpreter, as the Makefile picks it


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Run:
    def __init__(self, repo: Path, place_id: str, save_id: str, run_id: str | None = None,
                 skill: Path | None = None):
        self.repo = Path(repo).resolve()
        self.place_id, self.save_id = place_id, save_id
        self.run_id = run_id or f"{place_id}.{save_id}"
        self.dir = self.repo / "out/places/runs" / self.run_id
        self.place = self.repo / "newworld/places" / place_id
        self.save_path = self.place / "edits" / f"{save_id}.json"
        self.skill = (Path(skill) if skill else self.repo / ".claude/skills/place-build/SKILL.md").resolve()
        self.fixes = self.repo / "docs/skill-fixes.md"
        self.draft_skill = self.dir / "place-build.SKILL.md"   # the agent's rewrite, put in place by finalise
        self.dir.mkdir(parents=True, exist_ok=True)

    # ---- state ----
    def state(self) -> dict:
        p = self.dir / "state.json"
        if p.exists():
            return json.loads(p.read_text())
        return {"run_id": self.run_id, "place_id": self.place_id, "save_id": self.save_id, "state": "running",
                "step": STEPS[0], "steps": {}, "started": now(), "report": None}

    def put(self, **kw) -> dict:
        st = self.state()
        steps = kw.pop("steps", {})
        st["steps"].update(steps)
        st.update(kw, updated=now())
        tmp = self.dir / "state.json.tmp"
        tmp.write_text(json.dumps(st, indent=1))
        tmp.replace(self.dir / "state.json")
        return st

    def log(self, msg: str) -> None:
        line = f"{now()} {msg}"
        print(line, flush=True)
        with open(self.dir / "run.log", "a") as f:
            f.write(line + "\n")

    def done(self, step: str):
        p = self.dir / f"{step}.done"
        return json.loads(p.read_text()) if p.exists() else None

    def stamp(self, step: str, result: dict) -> None:
        (self.dir / f"{step}.done").write_text(json.dumps(dict(result, at=now()), indent=1))
        self.put(steps={step: result})

    # ---- git ----
    def git(self, *args, check=True) -> str:
        return subprocess.run(["git", "-C", str(self.repo), *args], check=check, capture_output=True,
                              text=True).stdout.strip()

    def commit(self, msg: str, paths: list[Path]) -> str | None:
        rel = [str(Path(p).resolve().relative_to(self.repo)) for p in paths]
        if not self.git("status", "--porcelain", "--", *rel):
            return None
        lane = self.repo / "tooling/lane_commit.sh"
        if lane.exists() and os.environ.get("FINALISE_PLAIN_COMMIT") != "1":
            r = subprocess.run([str(lane), "-m", msg, "--", *rel], cwd=self.repo, capture_output=True, text=True)
            self.log(r.stdout.strip() + r.stderr.strip())
            if r.returncode:
                raise RuntimeError(f"lane_commit failed: {r.stderr.strip() or r.stdout.strip()}")
        else:
            self.git("add", "--", *rel)
            self.git("commit", "-q", "-m", msg + "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>",
                     "--", *rel)
        return self.git("rev-parse", "HEAD")


def crash_point(step: str) -> None:
    """Test hook: FINALISE_CRASH_IN=<step> kills this process mid-step, as a stopped machine would."""
    if os.environ.get("FINALISE_CRASH_IN") == step:
        os.kill(os.getpid(), signal.SIGKILL)


# ---------- 1. record ----------

def step_record(run: Run) -> dict:
    save = json.loads(run.save_path.read_text())
    edits.check_save(save, run.place_id)
    files = edits.load_place(run.place)
    if save["save_id"] in files["place"].get("saves_applied", []):
        run.log("record: the save is already in the place files (a resumed run)")
    else:
        (run.dir / "before.json").write_text(json.dumps(files, sort_keys=True))
        out = edits.apply_save(files, save, edits.bundle_source(run.repo / "out/places/bundles"))
        edits.write_place(run.place, out)
        (run.dir / "after.json").write_text(json.dumps(out, sort_keys=True))
        run.log(f"record: {len(save['ops'])} edits applied to {run.place.relative_to(run.repo)}")
    crash_point("record")
    if not save.get("final"):
        save["final"] = True
        run.save_path.write_text(json.dumps(save, indent=1) + "\n")
    sha = run.commit(f"{run.place_id}: the owner's edits recorded (save {run.save_id}, finalised)", [run.place])
    calls = [op.get("call", "fault") for op in save["ops"]]
    return {"status": "ok", "commit": sha or run.git("rev-parse", "HEAD"), "ops": len(calls),
            "faults": calls.count("fault"), "taste": calls.count("taste")}


# ---------- 2. build ----------

def verb_available(repo: Path, verb: str) -> bool:
    return (repo / "tools/places" / f"{verb}.py").exists() or (repo / "tools/places" / verb / "__init__.py").exists()


def step_build(run: Run, skip: bool) -> dict:
    results = {}
    for verb in BUILD_VERBS:
        if skip or not verb_available(run.repo, verb):
            results[verb] = {"rc": None, "status": "skipped" if skip else "not available yet", "tail": ""}
            run.log(f"build: {verb} {results[verb]['status']}")
            continue
        cmd = [PY, "-m", "tools.places", verb, run.place_id]
        run.log("build: " + shlex.join(cmd))
        r = subprocess.run(cmd, cwd=run.repo, capture_output=True, text=True)   # the repo's own tools and files
        out = (r.stdout + r.stderr).strip().splitlines()
        with open(run.dir / "run.log", "a") as f:
            f.write("\n".join(out) + "\n")
        results[verb] = {"rc": r.returncode, "status": "ok" if r.returncode == 0 else "failed",
                         "tail": "\n".join(out[-30:])}
        if r.returncode and verb != "check":
            break   # a failed seat or build leaves nothing to check
    crash_point("build")
    sha = run.commit(f"{run.place_id}: seated after the owner's edits (save {run.save_id})", [run.place])
    ok = all(v["status"] in ("ok", "skipped", "not available yet") for v in results.values())
    return {"status": "ok" if ok else "failed", "verbs": results, "commit": sha}


# ---------- 3. learn ----------

def agent_prompt(run: Run) -> str:
    places = run.repo / "newworld/places"
    return f"""Follow the skill place-lessons ({CODE_REPO / '.claude/skills/place-lessons/SKILL.md'}) on this finalised
save. Inputs:
- the save's fault edits, one per line: {run.dir / 'faults.jsonl'} (the whole save, taste included: {run.save_path})
- the place files before the save and after it, as one JSON each: {run.dir / 'before.json'}, {run.dir / 'after.json'}
  (large: search them for the ids and positions you need rather than reading them whole)
- the build and check results: {run.dir / 'build.done'}
- every place's place.json (for taste preferences across places): {places}/*/place.json
- the place-build skill: {run.skill}
- the skill-fixes list for tool changes owed: {run.fixes}
Write the whole rewritten place-build skill to {run.draft_skill} (only when the recipe changes; finalise puts it in
place), and the lessons file to {run.dir / 'lessons.json'}. Edit nothing else but the skill-fixes list."""


def agent_cmd(run: Run, budget: float, turns: int) -> list[str]:
    override = os.environ.get("FINALISE_AGENT_CMD")
    if override:
        return shlex.split(override) + [str(run.dir), str(run.skill)]
    dirs = sorted({str(run.dir), str(run.repo), str(run.skill.parent), str(run.fixes.parent)})
    return ["claude", "-p", agent_prompt(run), "--agent", "place-lessons", "--output-format", "json",
            "--max-budget-usd", f"{budget:.2f}", "--max-turns", str(turns), "--permission-mode", "acceptEdits",
            "--allowedTools", "Read,Glob,Grep,Edit,Write", "--no-session-persistence",
            *[a for d in dirs for a in ("--add-dir", d)]]


def file_git(path: Path, *args) -> str:
    return subprocess.run(["git", "-C", str(path.parent), *args], capture_output=True, text=True).stdout


def restore_from_head(path: Path) -> None:
    """Put a file back to its committed text (a lessons run that did not finish)."""
    top = Path(file_git(path, "rev-parse", "--show-toplevel").strip())
    text = file_git(path, "show", f"HEAD:{path.resolve().relative_to(top)}")
    if text:
        path.write_text(text)


def step_learn(run: Run, budget: float, turns: int) -> dict:
    save = json.loads(run.save_path.read_text())
    if not any(op.get("call", "fault") == "fault" for op in save["ops"]):
        return {"status": "nothing to learn", "why": "every edit was marked as a taste call"}
    if not run.skill.exists():
        return {"status": "did not run", "why": f"the place-build skill is not at {run.skill}"}
    started = run.dir / "learn.started"
    if started.exists():          # a killed run may have left a half-written skill
        restore_from_head(run.skill)
        restore_from_head(run.fixes) if run.fixes.exists() else None
    started.write_text(now())
    with open(run.dir / "faults.jsonl", "w") as fh:
        for op in save["ops"]:
            if op.get("call", "fault") == "fault":
                fh.write(json.dumps(op, separators=(",", ":")) + "\n")
    (run.dir / "lessons.json").unlink(missing_ok=True)
    run.draft_skill.unlink(missing_ok=True)
    cmd = agent_cmd(run, budget, turns)
    run.log("learn: the lessons agent started (budget $%.2f, %d turns)" % (budget, turns))
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE_CODE_")}
    try:
        r = subprocess.run(cmd, cwd=CODE_REPO, capture_output=True, text=True, env=env, timeout=3600)
        rc, out, err = r.returncode, r.stdout, r.stderr
    except (OSError, subprocess.TimeoutExpired) as e:
        rc, out, err = -1, "", str(e)
    (run.dir / "agent.out.json").write_text(out)
    meta = {}
    try:
        meta = json.loads(out) if out.strip().startswith("{") else {}
    except json.JSONDecodeError:
        pass
    cost = meta.get("total_cost_usd")
    turns_used = meta.get("num_turns")
    run.log(f"learn: agent rc {rc}, cost ${cost}, turns {turns_used}, {meta.get('subtype', '')} {err[-300:]}")
    crash_point("learn")
    lessons_p = run.dir / "lessons.json"
    failed = rc != 0 or meta.get("is_error") or not lessons_p.exists()
    if failed:
        restore_from_head(run.skill)
        if run.fixes.exists():
            restore_from_head(run.fixes)
        why = ("it went over its budget" if "budget" in str(meta.get("subtype", "")) + err
               else "it ran out of turns" if "max_turns" in str(meta.get("subtype", ""))
               else "it stopped with an error" if rc != 0 or meta.get("is_error")
               else "it finished without writing its lessons")
        return {"status": "did not run", "why": why, "cost_usd": cost, "turns": turns_used}
    lessons = json.loads(lessons_p.read_text())
    if run.draft_skill.exists() and run.draft_skill.read_text().strip():
        run.skill.write_text(run.draft_skill.read_text())
    titles = "; ".join(lz.get("lesson", "")[:90] for lz in lessons.get("lessons", []))
    paths = [run.skill] + ([run.fixes] if run.fixes.exists() else [])
    sha = commit_skill(run, f"place-build: lessons from {run.place_id} (save {run.save_id}): {titles or 'nothing general'}",
                       paths)
    return {"status": "ok", "commit": sha, "cost_usd": cost, "turns": turns_used}


def commit_skill(run: Run, msg: str, paths: list[Path]) -> str | None:
    """The skill change is its own commit, so one git revert removes the lesson. The skill may live in another
    repository (a scratch copy in a proof); the commit is made in the skill's own repository."""
    top = Path(file_git(run.skill, "rev-parse", "--show-toplevel").strip())
    if top == run.repo:
        return run.commit(msg, [p for p in paths if p.resolve().is_relative_to(run.repo)])
    rel = [str(p.resolve().relative_to(top)) for p in paths if p.resolve().is_relative_to(top)]
    if not file_git(run.skill, "status", "--porcelain", "--", *rel):
        return None
    file_git(run.skill, "add", "--", *rel)
    file_git(run.skill, "commit", "-q", "-m", msg + "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>",
             "--", *rel)
    return file_git(run.skill, "rev-parse", "HEAD").strip()


# ---------- 4. report ----------

VERB_WORDS = {"seat": "Seating everything on the ground", "build": "Building the place into the game file",
              "check": "Checking the built place"}


def step_report(run: Run) -> dict:
    rec, bld, lrn = run.done("record") or {}, run.done("build") or {}, run.done("learn") or {}
    save = json.loads(run.save_path.read_text())
    lessons = {}
    if (run.dir / "lessons.json").exists() and lrn.get("status") == "ok":
        lessons = json.loads((run.dir / "lessons.json").read_text())
    title = save.get("name") or run.save_id
    L = [f"# Your edits to {run.place_id.title()}: what happened", ""]
    L += ["## Your edits are saved into the place", "",
          f"All {rec.get('ops', 0)} of your edits from the save \"{title}\" are now part of the place. "
          f"You marked {rec.get('faults', 0)} as the builder's mistakes and {rec.get('taste', 0)} as your own "
          "preference. From now on the build uses your version, not the builder's first draft.", ""]
    L += ["## The build", ""]
    for verb, v in bld.get("verbs", {}).items():
        word = VERB_WORDS.get(verb, verb)
        if v["status"] == "ok":
            L.append(f"- {word}: done.")
        elif v["status"] == "not available yet":
            L.append(f"- {word}: this part of the tooling is not finished yet, so it did not run. Your edits are "
                     "kept and will be built when it is.")
        elif v["status"] == "skipped":
            L.append(f"- {word}: not run this time (a test run).")
        else:
            meaning = ("the place was built, but something in it is not right yet. Your edits are kept; the "
                       "problems below need fixing before the place goes into the game."
                       if verb == "check" else
                       "the place could not be built, so nothing was checked. Your edits are kept.")
            tail = v.get("tail", "")
            if "Traceback" in tail:
                last = tail.strip().splitlines()[-1] if tail.strip() else ""
                L.append(f"- {word}: failed, because the tool itself broke: a fault in our code, not in your edits. "
                         "Your edits are kept; an agent needs to fix the tool and run this step again. "
                         f"(The tool's last words, for that agent: `{last[:200]}`)")
            else:
                L.append(f"- {word}: failed. This means {meaning}")
                L += ["", f"  What the {'checker' if verb == 'check' else 'tool'} said:", ""]
                L += ["      " + x for x in tail.splitlines()[-12:]]
    L.append("")
    L += ["## What the builder has learned", ""]
    if lrn.get("status") == "ok" and lessons:
        recipe = [x for x in lessons.get("lessons", []) if x.get("where") == "recipe"]
        tools_owed = [x for x in lessons.get("lessons", []) if x.get("where") == "tool"]
        if recipe:
            L.append("The builder's instructions now say something different. For each change: the mistake, "
                     "why the old instructions led to it, and what they say now.")
            L.append("")
            for x in recipe:
                L += [f"- **{x.get('lesson', '')}** {x.get('why', '')} {x.get('change', '')}".rstrip(), ""]
        else:
            L += ["The builder's instructions did not need to change.", ""]
        if tools_owed:
            L += ["Some mistakes come from a tool's fixed rule rather than the instructions. These were not "
                  "changed automatically; each is listed for an agent to fix in the tool:", ""]
            L += [f"- {x.get('lesson', '')} {x.get('why', '')}".rstrip() for x in tools_owed] + [""]
        if lessons.get("one_offs"):
            L += ["Mistakes that happened once, with no pattern behind them, are fixed in this place only:", ""]
            L += [f"- {x.get('what', '')}" for x in lessons["one_offs"]] + [""]
        if lrn.get("commit"):
            L += [f"To undo these changes to the builder's instructions, ask an agent to revert commit "
                  f"{lrn['commit'][:10]} (one command: git revert {lrn['commit'][:10]}). Your edits to the place "
                  "stay either way.", ""]
    elif lrn.get("status") == "nothing to learn":
        L += ["You marked every edit as your own preference, so there was nothing for the builder to learn.", ""]
    else:
        L += [f"The learning step did not run: {lrn.get('why', 'it did not finish')}. Your edits are saved and the "
              "builder's instructions are unchanged. To run it again, ask an agent to run "
              f"`python -m tools.places finalise {run.place_id} {run.save_id} --relearn`.", ""]
    prefs = [p for p in edits.load_place(run.place)["place"].get("preferences", []) if p.get("save") == run.save_id]
    L += ["## Your preferences for this place", ""]
    if prefs:
        L += ["These edits were your taste, not the builder's mistakes. They are kept as this place's own "
              "preferences and never become rules for other places:", ""]
        L += [f"- {p.get('note') or describe(p)}" for p in prefs] + [""]
    else:
        L += ["None this time.", ""]
    cands = lessons.get("taste_candidates", []) if lessons else []
    if cands:
        L += ["You have made these preference calls in several places. They are not rules yet; if you want any of "
              "them to become one, say so:", ""] + [f"- {c.get('what', c) if isinstance(c, dict) else c}" for c in cands] + [""]
    (run.dir / "report.md").write_text("\n".join(L).rstrip() + "\n")
    crash_point("report")
    return {"status": "ok", "report": str(run.dir / "report.md")}


def describe(p: dict) -> str:
    return {"ref.move": "an object moved", "ref.remove": "an object removed", "ref.add": "an object added",
            "veg.clear": "plants cleared", "veg.restore": "plants put back", "land.patch": "the ground reshaped"
            }.get(p["op"], p["op"].replace(".", " ")) + f" ({p.get('what')})"


# ---------- the chain ----------

STEP_WORDS = {"record": "writing your changes into the place files", "build": "building and checking the place",
              "learn": "improving the place-building recipe", "report": "writing the report"}


def finalise(run: Run, skip_build=False, budget=BUDGET_USD, turns=MAX_TURNS) -> int:
    run.put(state="running")
    for step in STEPS:
        if run.done(step):
            continue
        run.put(step=step)
        run.log(f"step {step}")
        try:
            if step == "record":
                res = step_record(run)
            elif step == "build":
                res = step_build(run, skip_build)
            elif step == "learn":
                res = step_learn(run, budget, turns)
            else:
                res = step_report(run)
        except edits.EditError as e:
            run.log(f"record: the save could not be applied: {e}")
            (run.dir / "report.md").write_text(
                f"# Your edits to {run.place_id.title()} were not applied\n\nThe save no longer matches the place: "
                f"{e}.\n\nNothing was changed and your save is kept as it was. This happens when the place changed "
                "after you started editing. Open the save in the studio again; it will show the edit that no "
                "longer fits.\n")
            run.put(state="failed", steps={step: {"status": "failed", "why": str(e)}},
                    report=str(run.dir / "report.md"))
            return 1
        except Exception as e:  # noqa: BLE001  the tool itself broke: say so plainly, keep what was recorded
            run.log(f"{step}: stopped: {e!r}")
            kept = ("Your edits are recorded in the place's files." if run.done("record")
                    else "Nothing was changed and your save is kept as it was.")
            (run.dir / "report.md").write_text(
                f"# Finalising {run.place_id.title()} stopped\n\nThe step \"{STEP_WORDS.get(step, step)}\" could not "
                f"finish because the tool itself failed, not because of anything in your edits. {kept}\n\n"
                f"What it said: `{str(e)[:400]}`\n\nRunning finalise again on the same save carries on from this "
                "step.\n")
            run.put(state="failed", steps={step: {"status": "failed", "why": str(e)[:400]}},
                    report=str(run.dir / "report.md"))
            return 1
        run.stamp(step, res)
    run.put(state="done", step="report", report=str(run.dir / "report.md"))
    run.log("finalise: done")
    return 0


def read_run(run_dir: Path, tail: int = 40) -> dict:
    """What GET /api/place/<id>/runs/<run_id> returns: state, step, log tail, the report when done."""
    run_dir = Path(run_dir)
    st = json.loads((run_dir / "state.json").read_text()) if (run_dir / "state.json").exists() else {"state": "queued"}
    log = run_dir / "run.log"
    st["log_tail"] = log.read_text().splitlines()[-tail:] if log.exists() else []
    rep = run_dir / "report.md"
    st["report_md"] = rep.read_text() if rep.exists() and st.get("state") in ("done", "failed") else None
    return st


def start(place_id: str, save_id: str, repo: Path = CODE_REPO) -> str:
    """Launch the chain under tooling/job_guard.sh (the machine stays awake until it ends); returns run_id."""
    run_id = f"{place_id}.{save_id}"
    subprocess.Popen([str(repo / "tooling/job_guard.sh"), "run", f"finalise.{run_id}", "--",
                      PY, "-m", "tools.places", "finalise", place_id, save_id],
                     cwd=repo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    return run_id


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places finalise")
    ap.add_argument("place_id")
    ap.add_argument("save_id")
    ap.add_argument("--repo", default=str(CODE_REPO), help="the repository holding newworld/places and out/places")
    ap.add_argument("--skill", help="the place-build skill to rewrite (default: the repo's)")
    ap.add_argument("--relearn", action="store_true", help="run the lessons step and the report again")
    ap.add_argument("--skip-build", action="store_true", help="do not seat, build or check (a test run)")
    ap.add_argument("--budget", type=float, default=BUDGET_USD)
    ap.add_argument("--max-turns", type=int, default=MAX_TURNS)
    a = ap.parse_args(argv)
    run = Run(Path(a.repo), a.place_id, a.save_id, skill=a.skill)
    if a.relearn:
        for s in ("learn", "report"):
            (run.dir / f"{s}.done").unlink(missing_ok=True)
        (run.dir / "learn.started").unlink(missing_ok=True)
    return finalise(run, a.skip_build, a.budget, a.max_turns)
