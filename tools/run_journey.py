#!/usr/bin/env python3
"""The journey runner (chunk 0.3 §d; decision 0021): a scene, then short steps, each judged on state and events,
with a still at every step. DEV ONLY: it drives the running game through tools/bridge.py.

    python3 tools/run_journey.py tests/journeys/smoke.yaml [--runs 2] [--no-stills] [--save argoniabase]

A runnable journey has `runner: 1` (the drafts beside it are prose for a lane to turn into steps):

    id: smoke
    runner: 1
    save: argoniabase            # optional: the base save (make deploy writes it)
    scene: smoke-floor           # tests/scenes/<id>.txt, sent to the machine and applied with `bat`
    steps:
      - name: walk
        do:                      # each action one key; inputs are capped at 3 s by the bridge
          - pad: "+LY=1:1500 -:100"
        expect:                  # each polled until it holds or `within` seconds pass (default 5)
          - moved: {gt: 100}

Actions: pad <seq>; key "<K[+K]> <ms>"; console <line>; teleport [cell <edid> | pos x y z | ref <id>];
wait <seconds, at most 10>; game_hours <n> (time passes at a raised timescale, the game's own clock, then the
timescale is put back); call [<command>, args...] (any bridge read, kept in the report).
Expectations: read [<command>, args...] with path a.b.c and one of eq ne gt ge lt le contains not_contains;
console <line> with contains / not_contains; event {kind, match} since the step began; moved {gt|lt: units} on the
ground since the step began; quests_running {allowed: <json>} (the console's running-quest list against a file).

Out: out/runs/<id>/<stamp>/ with report.json, a still per step (<n>-<name>.png) and, for a failed step,
failure.json: the step, the expectation and its still, ready for a `reader`. Exit 0 every run passed, 1 a step
failed, 2 the game went down (a crash is a failure, reported within 60 s by the bridge). With --runs N, three
identical failures stop the batch.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import subprocess
import sys
import time

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from tools.bridge import Bridge, BridgeError, GameDown  # noqa: E402

BASE_SAVE = "argoniabase"
SCENES = REPO / "tests" / "scenes"
GAME_ROOT = "C:/Program Files (x86)/Steam/steamapps/common/Skyrim Special Edition"
OPS = {"eq": lambda a, b: a == b, "ne": lambda a, b: a != b, "gt": lambda a, b: a > b, "ge": lambda a, b: a >= b,
       "lt": lambda a, b: a < b, "le": lambda a, b: a <= b, "contains": lambda a, b: str(b) in str(a),
       "not_contains": lambda a, b: str(b) not in str(a)}


class StepFailed(Exception):
    pass


def load_journey(path: pathlib.Path) -> dict:
    import yaml
    j = yaml.safe_load(path.read_text())
    if not isinstance(j, dict) or j.get("runner") != 1:
        raise SystemExit(f"{path}: not a runnable journey (no `runner: 1`; a draft is prose)")
    for k in ("id", "steps"):
        if k not in j:
            raise SystemExit(f"{path}: no `{k}`")
    for i, s in enumerate(j["steps"]):
        if "name" not in s:
            raise SystemExit(f"{path}: step {i} has no name")
        for a in s.get("do", []):
            if len(a) != 1 or next(iter(a)) not in ACTIONS:
                raise SystemExit(f"{path}: step {s['name']}: unknown action {a}")
        for e in s.get("expect", []):
            if not set(e) & set(EXPECTS):
                raise SystemExit(f"{path}: step {s['name']}: unknown expectation {e}")
    return j


def dig(value, path: str):
    for part in [p for p in str(path).split(".") if p]:
        value = value[int(part)] if isinstance(value, list) else value.get(part) if isinstance(value, dict) else None
    return value


class Runner:
    def __init__(self, bridge, out: pathlib.Path, stills: bool = True, run_sh=None):
        self.b, self.out, self.stills = bridge, out, stills
        self.run_sh = run_sh or str(REPO / "infra" / "gpu-box" / "run.sh")
        self.calls = []

    # -- the scene -----------------------------------------------------------------------------------------
    def apply_scene(self, scene: str | None, save: str):
        self.b.call("load", save)
        time.sleep(3)  # the load screen fades
        third_person(self.b)
        if scene:
            src = SCENES / f"{scene}.txt"
            if not src.exists():
                raise StepFailed(f"no scene {src}")
            subprocess.run([self.run_sh, "put", str(src), f"{GAME_ROOT}/{scene}.txt"], check=True, capture_output=True)
            out = self.b.call("console", f"bat {scene}")["output"]
            time.sleep(2)  # a coc in the scene loads a cell
            return out
        return ""

    # -- actions -------------------------------------------------------------------------------------------
    def act(self, action: dict):
        (kind, arg), = action.items()
        return ACTIONS[kind](self, arg)

    def _pad(self, seq):
        return self.b.pad(str(seq))

    def _key(self, spec):
        keys, ms = str(spec).split()
        return self.b.call("input", "key", keys, int(ms))

    def _console(self, line):
        return self.b.call("console", line)

    def _teleport(self, args):
        return self.b.call("teleport", *(args if isinstance(args, list) else str(args).split()))

    def _wait(self, seconds):
        if float(seconds) > 10:
            raise StepFailed(f"wait {seconds}: a step waits at most 10 s (keep steps short; use game_hours)")
        time.sleep(float(seconds))

    def _game_hours(self, hours):
        """Game time passes on the game's own clock: the timescale raised so an hour is 0.6 s, then put back."""
        before = self.b.call("time")
        old = float(self.b.call("global", "TimeScale")["value"])
        self.b.call("console", "set timescale to 6000")
        try:
            want = float(before["days_passed"]) + float(hours) / 24
            for _ in range(int(float(hours) * 3) + 30):
                time.sleep(0.5)
                if float(self.b.call("time")["days_passed"]) >= want:
                    break
        finally:
            self.b.call("console", f"set timescale to {old:g}")
        return {"from": before["days_passed"], "to": self.b.call("time")["days_passed"]}

    def _call(self, args):
        r = self.b.call(*args)
        self.calls.append({"call": args, "result": r})
        return r

    # -- expectations ----------------------------------------------------------------------------------------
    def check(self, exp: dict, ctx: dict):
        """None when it holds, else the reason in words."""
        op = next((k for k in OPS if k in exp), None)
        if "read" in exp:
            got = dig(self.b.call(*exp["read"]), exp.get("path", ""))
            return None if OPS[op](got, exp[op]) else f"{' '.join(map(str, exp['read']))} {exp.get('path', '')} = {got!r}, wanted {op} {exp[op]!r}"
        if "console" in exp:
            got = self.b.call("console", exp["console"])["output"].strip()
            return None if OPS[op](got, exp[op]) else f"console `{exp['console']}` printed {got!r}, wanted {op} {exp[op]!r}"
        if "event" in exp:
            ev = exp["event"]
            seen = self.b.call("events", ctx["since"], ev["kind"])["events"]
            want = str(ev.get("match", "*"))
            hit = [e for e in seen if want == "*" or want.lower() in json.dumps(e["data"]).lower()]
            return None if hit else f"no {ev['kind']} event matching {want!r} since the step began ({len(seen)} {ev['kind']} events)"
        if "moved" in exp:
            p = self.b.call("player")["pos"]
            d = math.hypot(p["x"] - ctx["pos"]["x"], p["y"] - ctx["pos"]["y"])
            (o, v), = exp["moved"].items()
            return None if OPS[o](d, v) else f"moved {d:.0f} units on the ground, wanted {o} {v}"
        if "quests_running" in exp:
            allowed = json.loads((REPO / exp["quests_running"]["allowed"]).read_text())
            ok = {q["edid"].lower() for q in allowed["running"] + allowed.get("keepVanilla", [])}
            running = running_quests(self.b)
            ctx.setdefault("notes", {})["running_quests"] = running
            extra = sorted(q for q in running if q.lower() not in ok)
            return None if not extra else f"{len(extra)} quests running that the allowed list lacks: {', '.join(extra[:20])}"
        raise StepFailed(f"unknown expectation {exp}")

    def expect(self, exp: dict, ctx: dict):
        end = time.monotonic() + float(exp.get("within", 5))
        while True:
            why = self.check(exp, ctx)
            if why is None or time.monotonic() >= end:
                return why
            time.sleep(0.5)

    # -- a run -----------------------------------------------------------------------------------------------
    def run(self, j: dict, save: str) -> dict:
        self.out.mkdir(parents=True, exist_ok=True)
        rep = {"id": j["id"], "save": save, "scene": j.get("scene"), "steps": [], "passed": False}
        t0 = time.monotonic()
        try:
            rep["scene_output"] = self.apply_scene(j.get("scene"), save)
            rep["scene_s"] = round(time.monotonic() - t0, 1)
            for n, step in enumerate(j["steps"], 1):
                rec = self.step(n, step)
                rep["steps"].append(rec)
                if not rec["passed"]:
                    rep["failed_at"] = step["name"]
                    fail = {"journey": j["id"], "step": step["name"], "do": step.get("do"), "expect": step.get("expect"),
                            "reason": rec["reason"], "still": rec.get("still"),
                            "ask_reader": "Does this still agree with the step's expectation? Say what it shows."}
                    (self.out / "failure.json").write_text(json.dumps(fail, indent=1))
                    break
            else:
                rep["passed"] = True
        except GameDown as e:
            rep["crash"] = str(e)
            rep["failed_at"] = rep.get("failed_at") or "game down"
        except (BridgeError, StepFailed) as e:
            rep["failed_at"] = rep.get("failed_at") or "scene"
            rep["error"] = str(e)
        rep["seconds"] = round(time.monotonic() - t0, 1)
        rep["calls"] = self.calls
        (self.out / "report.json").write_text(json.dumps(rep, indent=1))
        return rep

    def step(self, n: int, step: dict) -> dict:
        t = time.monotonic()
        ctx = {"since": self.b.call("events")["last"], "pos": self.b.call("player")["pos"]}
        rec = {"n": n, "name": step["name"], "passed": True}
        try:
            for a in step.get("do", []):
                self.act(a)
            for e in step.get("expect", []):
                why = self.expect(e, ctx)
                if why:
                    rec.update(passed=False, reason=why)
                    break
        except GameDown:
            raise
        except (BridgeError, StepFailed) as e:
            rec.update(passed=False, reason=f"{type(e).__name__}: {e}")
        if ctx.get("notes"):
            rec["notes"] = ctx["notes"]
        if self.stills or not rec["passed"]:
            try:
                rec["still"] = str(self.b.screenshot(self.out / f"{n:02d}-{step['name']}.png"))
            except BridgeError as e:
                rec["still"] = f"none: {e}"
        rec["seconds"] = round(time.monotonic() - t, 1)
        print(f"  {n:2d} {step['name']:<24} {'ok' if rec['passed'] else 'FAIL: ' + rec['reason']}", flush=True)
        return rec


ACTIONS = {"pad": Runner._pad, "key": Runner._key, "console": Runner._console, "teleport": Runner._teleport,
           "wait": Runner._wait, "game_hours": Runner._game_hours, "call": Runner._call}
EXPECTS = ("read", "console", "event", "moved", "quests_running")


def third_person(b):
    """The play camera is third person (owner, 2026-10-29); a save can hold first, where TDM is off. Setup only."""
    for _ in range(2):
        if b.call("console", "IsPC1stPerson")["output"].strip().endswith("0.00"):
            return
        b.call("input", "key", "F", 300)  # Toggle POV: a 100 ms press did not take (2026-10-30)
        time.sleep(1.0)
    raise StepFailed("the camera stays in first person")


def running_quests(b) -> list[str]:
    """The running quests by editor id, from the console's `sqs`-free list: `sq` prints every started quest."""
    out = b.call("console", "sq")["output"]
    names = []
    for line in out.splitlines():
        word = line.strip().split(" ", 1)[0]
        if word and word.replace("_", "").isalnum() and not word.isdigit() and word.lower() != "sq":
            names.append(word)
    return sorted(set(names))


def signature(rep: dict) -> str:
    bad = next((s for s in rep["steps"] if not s["passed"]), None)
    return f"{rep.get('failed_at')}|{(bad or {}).get('reason') or rep.get('error') or rep.get('crash')}"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("journey", type=pathlib.Path)
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--save", default=None)
    p.add_argument("--no-stills", action="store_true", help="stills only for a failed step")
    a = p.parse_args(argv)
    j = load_journey(a.journey)
    save = a.save or j.get("save") or BASE_SAVE
    b, fails, worst = Bridge(), {}, 0
    for r in range(1, a.runs + 1):
        out = REPO / "out" / "runs" / j["id"] / time.strftime("%Y%m%dT%H%M%S")
        print(f"{j['id']} run {r}: {out}", flush=True)
        rep = Runner(b, out, stills=not a.no_stills).run(j, save)
        verdict = "PASS" if rep["passed"] else "CRASH" if rep.get("crash") else "FAIL"
        print(f"{j['id']} run {r}: {verdict} in {rep['seconds']} s"
              + ("" if rep["passed"] else f" at {rep['failed_at']}: {signature(rep).split('|', 1)[1]}"), flush=True)
        if not rep["passed"]:
            worst = max(worst, 2 if rep.get("crash") else 1)
            sig = signature(rep)
            fails[sig] = fails.get(sig, 0) + 1
            if fails[sig] >= 3:
                print("three identical failures: stopped (diagnose before running again)")
                break
            if rep.get("crash"):
                break
    return worst


if __name__ == "__main__":
    sys.exit(main())
