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

Actions: pad <seq>; key "<K[+K]> <ms>"; talk <ref> (the NPC set 1.1 m before the player facing them, then E once
the crosshair shows it, or the step fails); console <line>; teleport [cell <edid> | pos x y z | ref <id>];
wait <seconds, at most 10>; game_hours <n> (time passes at a raised timescale, the game's own clock, then the
timescale is put back); call [<command>, args...] (any bridge read, kept in the report); relaunch <save | true>
(the game quit cleanly by the console's qqq, launched again through the bridge's `launch` to the main menu with the
bridge answering, then the save loaded, the journey's own with `true`, and the journey's scene applied again: a
step after it sees a restarted game, e.g. what a view remembers between sessions; `{save: <name>, scene: false}`
loads the save without the scene, so the player resumes where the save left them).
Expectations: read [<command>, args...] with path a.b.c and one of eq ne gt ge lt le contains not_contains;
console <line> with contains / not_contains; event {kind, match} since the step began; moved {gt|lt: units} on the
ground since the step began; quests_running {allowed: <json>} (the bridge's running quests against the file's
`running` list); music {allowed: [<edid>, ...]} (the music type playing is one of them, or none plays);
event {kind, match, absent: true} holds when no such event came; log {name: ArgoniaCore, contains: <text>} an SKSE
plugin's log has the text in a line written since the step began.

Owed (game-8): a step with `owed: <what it waits on>` is not run; the report lists it under `owed` and the
journey goes on past it (a step whose game side cannot exist yet, e.g. a Papyrus fragment before the compiler).

Kept values (1.7): an expectation with `keep: <name>` stores what it read (a read with only `keep` always holds);
a later comparison value `{kept: <name>}` compares against it (`{kept: <name>, plus: -32}` against it plus a number,
for a measured change within a tolerance), and `{name}` or `{name.2}` in an action's text is
replaced by it (a kept string is split on spaces for the index), so a step can go back to where a pile fell.

A soak (1.7) has `soak: {journey: <id>, minutes: 60, frames: 600, bars: {...}}` instead of steps: the journey is
run again and again until the minutes pass, and after each loop the Papyrus queue (`papyrus-queue`), the rest save
and its co-save sizes and the frame times are measured; it passes with no crash, the queue flat, the co-save flat
after the first loop and the frame times within the 0.2 §d bar. Out: soak.json beside the loops' reports.

Resume (step saves): after each passed step the runner saves the game natively (console `save argj-<id>-<step>`)
and removes the journey's previous step save, so one is kept per journey; the kept values go beside it in
out/resume/<id>.json. `--from <step>` loads the save of the step before it and runs from there, `--only <step>` runs
that one step; neither applies the scene again. A journey that counts saves (SaveCount) or tests that nothing but a
rest saves sets `step_saves: false`, and has no resume.

--dry validates a journey (or a soak and the journey it loops) and its scene without the game.

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
RESUME = REPO / "out" / "resume"
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
    if "soak" in j:
        s = j["soak"]
        if "id" not in j or not isinstance(s, dict) or "journey" not in s:
            raise SystemExit(f"{path}: a soak needs `id` and `soak: {{journey: <id>}}`")
        unknown = set(s.get("bars", {})) - set(SOAK_BARS)
        if unknown:
            raise SystemExit(f"{path}: unknown soak bars {sorted(unknown)} (known: {sorted(SOAK_BARS)})")
        inner = load_journey(path.parent / f"{s['journey']}.yaml")
        if "soak" in inner:
            raise SystemExit(f"{path}: a soak loops a journey, not another soak")
        return j
    for k in ("id", "steps"):
        if k not in j:
            raise SystemExit(f"{path}: no `{k}`")
    for i, s in enumerate(j["steps"]):
        if "name" not in s:
            raise SystemExit(f"{path}: step {i} has no name")
        if "owed" in s and not (isinstance(s["owed"], str) and s["owed"].strip()):
            raise SystemExit(f"{path}: step {s['name']}: `owed` names what the step waits on")
        for a in s.get("do", []):
            if len(a) != 1 or next(iter(a)) not in ACTIONS:
                raise SystemExit(f"{path}: step {s['name']}: unknown action {a}")
        for e in s.get("expect", []):
            if not set(e) & set(EXPECTS):
                raise SystemExit(f"{path}: step {s['name']}: unknown expectation {e}")
            if ("read" in e or "console" in e) and not (set(e) & set(OPS)) and "keep" not in e:
                raise SystemExit(f"{path}: step {s['name']}: {e} has no comparison and keeps nothing")
            if "read" in e and not isinstance(e["read"], list):
                raise SystemExit(f"{path}: step {s['name']}: read takes a list [<command>, args...]")
    names = [s["name"] for s in j["steps"]]
    if len(set(names)) != len(names):
        raise SystemExit(f"{path}: step names repeat: {sorted({n for n in names if names.count(n) > 1})}")
    return j


def dry(path: pathlib.Path) -> str:
    """Validate without the game: the journey (and a soak's journey), each scene file, every kept name used after
    it is kept. The summary line, or SystemExit with the reason."""
    j = load_journey(path)
    if "soak" in j:
        inner = load_journey(path.parent / f"{j['soak']['journey']}.yaml")
        return f"{path.name}: soak of {inner['id']} for {j['soak'].get('minutes', 60)} min; " + dry(path.parent / f"{inner['id']}.yaml")
    if j.get("scene") and not (SCENES / f"{j['scene']}.txt").is_file():
        raise SystemExit(f"{path}: no scene tests/scenes/{j['scene']}.txt")
    kept: set[str] = set()
    for s in j["steps"]:
        for a in s.get("do", []):
            for name in _refs(next(iter(a.values()))):
                if name not in kept:
                    raise SystemExit(f"{path}: step {s['name']}: action uses {{{name}}} before it is kept")
        for e in s.get("expect", []):
            for v in e.values():
                if isinstance(v, dict) and "kept" in v and v["kept"] not in kept:
                    raise SystemExit(f"{path}: step {s['name']}: compares with {v['kept']!r} before it is kept")
            if "keep" in e:
                kept.add(e["keep"])
    from tools import journey_lint
    vocab = _vocab()
    errs = journey_lint.lint(j, vocab)
    if errs:
        raise SystemExit(f"{path}: lint:\n  " + "\n  ".join(errs))
    return f"{path.name}: {len(j['steps'])} steps, scene {j.get('scene')}, {len(kept)} kept values: ok" + (
        "" if vocab else " (lint: static only, no vocab cache)")


_VOCAB: list = []


def _vocab():
    """The linter's vocabulary cache, read once; one warning when it is absent (tools/fetch_vocab.py fills it)."""
    if not _VOCAB:
        from tools import journey_lint
        _VOCAB.append(journey_lint.load_vocab())
        if _VOCAB[0] is None:
            print(f"warning: no {journey_lint.vocab_path()}: the journey lint checks the console grammar only "
                  "(fill it on the game machine: python3 tools/fetch_vocab.py)", file=sys.stderr)
    return _VOCAB[0]


def _refs(value) -> list[str]:
    import re
    return [m.split(".")[0] for m in re.findall(r"\{([A-Za-z_][A-Za-z0-9_]*(?:\.\d+)?)\}", json.dumps(value))]


def dig(value, path: str):
    for part in [p for p in str(path).split(".") if p]:
        value = value[int(part)] if isinstance(value, list) else value.get(part) if isinstance(value, dict) else None
    return value


class Runner:
    def __init__(self, bridge, out: pathlib.Path, stills: bool = True, run_sh=None, sent: dict | None = None):
        self.b, self.out, self.stills = bridge, out, stills
        self.run_sh = run_sh or str(REPO / "infra" / "gpu-box" / "run.sh")
        # scene -> the resolved text last put on the machine: a batch shares one, so an unchanged scene is not re-sent
        self.sent = {} if sent is None else sent
        self.calls = []
        self.kept: dict = {}
        self.scene: str | None = None  # the journey's scene and save, for a relaunch
        self.save = BASE_SAVE
        self.resume_dir = RESUME

    def fill(self, value):
        """`{name}` / `{name.i}` in an action's text: the kept value (a string split on spaces for the index)."""
        import re
        def one(m):
            name, _, idx = m.group(1).partition(".")
            if name not in self.kept:
                raise StepFailed(f"{{{m.group(1)}}}: nothing kept as {name!r} yet")
            v = self.kept[name]
            if idx:
                v = (v.split() if isinstance(v, str) else v)[int(idx)]
            return str(v)
        if isinstance(value, str):
            return re.sub(r"\{([A-Za-z_][A-Za-z0-9_]*(?:\.\d+)?)\}", one, value)
        if isinstance(value, list):
            return [self.fill(v) for v in value]
        return value

    # -- the scene -----------------------------------------------------------------------------------------
    def apply_scene(self, scene: str | None, save: str, load: bool = True):
        """The save loaded (not when `load` is false: a batch chaining journeys of one scene family), the play
        camera, then the scene sent (only when its resolved text changed since the last put) and run by `bat`."""
        if load:
            since = self.b.call("events")["last"]
            self.b.call("load", save)
            self.wait_load(since, appear=5.0)  # act only on a settled world: the travel line inside a load's tail
            # crashed the engine twice (diag2-crash-misc, batch 20261030T151243)
        third_person(self.b)
        if scene:
            src = SCENES / f"{scene}.txt"
            if not src.exists():
                raise StepFailed(f"no scene {src}")
            # refs as runtime ids: the game keeps no ref's editor id (tools/ref_ids.py, game-7)
            self.out.mkdir(parents=True, exist_ok=True)
            sent, text = self.out / f"scene-{scene}.txt", self.b.resolve_refs(src.read_text())
            sent.write_text(text)
            if self.sent.get(scene) != text:
                subprocess.run([self.run_sh, "put", str(sent), f"{GAME_ROOT}/{scene}.txt"], check=True, capture_output=True)
                self.sent[scene] = text
            since = self.b.call("events")["last"]
            out = self.b.call("console", f"bat {scene}")["output"]
            self.wait_load(since)  # a coc/moveto in the scene loads a cell; input before it ends is lost
            return out
        return ""

    def wait_load(self, since: int, appear: float = 2.0, cap: float = 30.0):
        """Wait on the bridge's menu events: until a Loading Menu close (opening:false) has arrived since `since`, or
        no Loading Menu opened within `appear` s (the scene loaded nothing); then 1 s for the fade-in. Capped at `cap`."""
        waited = 0.0  # counted in polls, not the clock: the bridge call's own time is slack in the caller's favour
        while True:
            menus = [e["data"] for e in self.b.call("events", since, "menu")["events"]]
            evs = [d for d in menus if d.get("menu") == "Loading Menu"]
            fades = [d for d in menus if d.get("menu") == "Fader Menu"]
            fading = bool(fades) and fades[-1].get("opening")  # a key under the Fader Menu is lost (menus-quit, 20261030)
            if waited >= cap or (not fading and (any(not d.get("opening") for d in evs) or (not evs and waited >= appear))):
                break
            time.sleep(0.25)
            waited += 0.25
        time.sleep(1)  # the fade-in

    # -- actions -------------------------------------------------------------------------------------------
    def act(self, action: dict):
        (kind, arg), = action.items()
        return ACTIONS[kind](self, self.fill(arg))

    def _pad(self, seq):
        return self.b.pad(str(seq))

    def _key(self, spec):
        keys, ms, *route = str(spec).split()  # `key: "TAB 120"` or `key: "TAB 120 engine"`; the bridge picks per key
        if keys == "E" and not route:
            return self._activate(int(ms))
        r = self.b.call("input", "key", keys, int(ms), *route)
        self.calls.append({"call": ["input", "key", keys, int(ms), *route], "result": r})
        return r

    def _activate(self, ms=120):
        """E, then again (3 tries, 3.5 s apart) while no menu opened and the player's cell is unchanged: the first E
        after a scene's setup is lost; a second, 3.5 s later, opens the dialogue (game-15, live, engine route)."""
        cell0 = (self.b.call("player") or {}).get("cell")
        for attempt in (1, 2, 3):
            last = (self.b.call("events") or {}).get("last")
            r = self.b.call("input", "key", "E", ms)  # engine route by default (bridge: activation keys)
            self.calls.append({"call": ["input", "key", "E", ms], "result": r, "attempt": attempt})
            time.sleep(1.5)
            evs = (self.b.call("events") or {}).get("events") or []
            if any(e.get("kind") == "menu" and (e.get("data") or {}).get("opening") and (last is None or e.get("seq", 0) > last)
                   for e in evs) or (self.b.call("player") or {}).get("cell") != cell0:
                break
            time.sleep(2.0)
        return r

    def _console(self, line):
        return self.b.call("console", line)

    def _teleport(self, args):
        return self.b.call("teleport", *(args if isinstance(args, list) else str(args).split()))

    def _wait(self, seconds):
        if float(seconds) > 10:
            raise StepFailed(f"wait {seconds}: a step waits at most 10 s (keep steps short; use game_hours)")
        time.sleep(float(seconds))

    def _game_hours(self, hours):
        """Game time passes on the game's own clock: the timescale raised, then put back. An hour is 0.6 s (6000) for a
        short span; a span over two days runs ten times faster (60000), so a 50-day quarantine soak takes about 75 s,
        not 12 minutes (2026-10-30 batch)."""
        before = self.b.call("time")
        old = float(self.b.call("global", "TimeScale")["value"])
        scale = 60000 if float(hours) > 48 else 6000
        self.b.call("console", f"set timescale to {scale}")
        try:
            want = float(before["days_passed"]) + float(hours) / 24
            for _ in range(int(float(hours) * 3 * 6000 / scale) + 30):
                time.sleep(0.5)
                if float(self.b.call("time")["days_passed"]) >= want:
                    break
        finally:
            self.b.call("console", f"set timescale to {old:g}")
        return {"from": before["days_passed"], "to": self.b.call("time")["days_passed"]}

    def _relaunch(self, save):
        """Quit cleanly, relaunch, load `save` (true: the journey's own) and apply the journey's scene again; with
        `{save: <name>, scene: false}` the save is loaded and no scene is applied (the player resumes where it left)."""
        scene = self.scene
        if isinstance(save, dict):
            scene = self.scene if save.get("scene", True) else None
            save = save.get("save", True)
        save = self.save if save is True else str(save)
        try:
            self.b.call("console", "qqq", timeout=10)  # the reply may not come: the game is going down
        except (BridgeError, OSError, ValueError):
            pass
        clean = False
        for _ in range(QUIT_WAIT_S):
            if not self.b.health().get("alive"):
                clean = True
                break
            time.sleep(1)
        launched = self.b.launch()  # kills what is left (a quit that hung), lays the DLL, waits for the ping
        self.apply_scene(scene, save)
        r = {"quit_clean": clean, "save": save, "ping": launched.get("ping")}
        self.calls.append({"call": ["relaunch", save], "result": r})
        return r

    def _face(self, ref, units=None):
        """The NPC moved TALK_UNITS (or `units`) in front of the player, turned to face them, then E once the
        crosshair's ref is that NPC (the bridge's `crosshair` read), polled for TALK_WAIT_S; StepFailed when it never
        is. An NPC under AI walked out of the crosshair during a fixed wait before E (diag2-dialogue-crime)."""
        ref = str(ref).strip().strip('"')
        # The third-person camera keeps its own orbit until the player moves, so after console-only setup the
        # crosshair ray ignores setangle (diag3-g15): one short step re-syncs it before the NPC is placed.
        # Pitched 15 degrees down: level, the ray passed over the NPC's head at talk range and E did nothing (game-15:
        # with x 10-20 the crosshair held Livia and engine E opened the dialogue).
        self.b.call("console", "player.setangle x 15")
        self.b.call("input", "key", "W", 80)
        caller = ref if ref.startswith("ARG_") else f'"{ref}"'  # a runtime id calls quoted (tools/journey_lint.py)
        h = float(self.b.call("player")["heading_deg"])
        dx, dy = (units or TALK_UNITS) * math.sin(math.radians(h)), (units or TALK_UNITS) * math.cos(math.radians(h))
        self.b.call("console", f"{caller}.moveto player {dx:.0f} {dy:.0f} 0")
        self.b.call("console", f"{caller}.setangle z {(h + 180) % 360:.0f}")
        want = _form_id(self.b.resolve_refs(ref))
        seen, end = None, time.monotonic() + TALK_WAIT_S
        while True:
            seen = (self.b.call("crosshair") or {}).get("ref")
            if seen and want is not None and _form_id(seen.get("id")) == want:
                break
            if time.monotonic() >= end:
                raise StepFailed(f"talk {ref}: the crosshair never showed it within {TALK_WAIT_S:g} s "
                                 f"(last: {(seen or {}).get('editor_id') or (seen or {}).get('id') or 'nothing'})")
            time.sleep(0.25)

    def _talk(self, ref):
        """`talk: <ref>`: _face, then E (retried while no menu opens)."""
        self._face(ref)
        return self._activate(120)

    def _strike(self, ref):
        """`strike: <ref>`: one real melee swing at the ref with no key or pad on the path (the input path is the
        owner's #17 stream check): the ref faced at reach (_face, STRIKE_UNITS), the weapon drawn (R) and one attack
        (MOUSE1), both engine ButtonEvents (`sae` attack events were refused by the player's graph; the pad was dead
        after another lane's run: game-15), so the engine's hit, our damage and the crime rules all run."""
        self._face(ref, STRIKE_UNITS)
        out = []
        if str(self.b.call("console", "player.IsWeaponOut").get("output", "")).split(">>")[-1].strip().startswith("0"):
            out.append(self.b.call("input", "key", "R", 150))  # Ready Weapon (engine route)
            time.sleep(1.5)
        out.append(self.b.call("input", "key", "MOUSE1", 150))  # Right Attack (engine route: a mouse ButtonEvent)
        self.calls.append({"call": ["strike", ref], "result": out})
        time.sleep(1.2)
        return out


    def _call(self, args):
        r = self.b.call(*args)
        self.calls.append({"call": args, "result": r})
        return r

    # -- expectations ----------------------------------------------------------------------------------------
    def check(self, exp: dict, ctx: dict):
        """None when it holds, else the reason in words."""
        op = next((k for k in OPS if k in exp), None)
        want = exp.get(op)
        if isinstance(want, dict) and "kept" in want:
            want = self.kept[want["kept"]] + want["plus"] if "plus" in want else self.kept[want["kept"]]
        if "read" in exp or "console" in exp:
            if "read" in exp:
                got = dig(self.b.call(*self.fill(exp["read"])), exp.get("path", ""))
                what = f"{' '.join(map(str, exp['read']))} {exp.get('path', '')}"
            else:
                got = self.b.call("console", self.fill(exp["console"]))["output"].strip()
                what = f"console `{exp['console']}` printed"
            if op is None:  # a keep-only read
                self.kept[exp["keep"]] = got
                return None
            ok = OPS[op](got, want)
            if ok and "keep" in exp:
                self.kept[exp["keep"]] = got
            return None if ok else f"{what} = {got!r}, wanted {op} {want!r}"
        if "event" in exp:
            ev = exp["event"]
            seen = self.b.call("events", ctx["since"], ev["kind"])["events"]
            want = str(ev.get("match", "*"))
            hit = [e for e in seen if want == "*" or want.lower() in json.dumps(e["data"]).lower()]
            if ev.get("absent"):  # none may come: e.g. a menu that must stay open (`"opening": false` is its close)
                return None if not hit else f"{len(hit)} {ev['kind']} events matching {want!r} since the step began: {hit[0]['data']}"
            return None if hit else f"no {ev['kind']} event matching {want!r} since the step began ({len(seen)} {ev['kind']} events)"
        if "log" in exp:
            lines = skse_log(self.b, exp["log"]["name"])
            start = ctx["log_lines"].get(exp["log"]["name"], 0)
            lines = lines[start:] if len(lines) >= start else lines
            want = exp["log"]["contains"]
            return None if any(want in ln for ln in lines) else f"{exp['log']['name']}.log has no line with {want!r} since the step began ({len(lines)} new lines)"
        if "moved" in exp:
            p = self.b.call("player")["pos"]
            d = math.hypot(p["x"] - ctx["pos"]["x"], p["y"] - ctx["pos"]["y"])
            (o, v), = exp["moved"].items()
            return None if OPS[o](d, v) else f"moved {d:.0f} units on the ground, wanted {o} {v}"
        if "quests_running" in exp:
            allowed = json.loads((REPO / exp["quests_running"]["allowed"]).read_text())
            ok = {q["edid"].lower() for q in allowed["running"]}
            ours = {p.lower() for p in allowed.get("ours", {}).get("plugins", [])}
            running = running_quests(self.b)
            ctx.setdefault("notes", {})["running_quests"] = sorted(f"{q['editor_id']} ({q['plugin']})" for q in running)
            extra = sorted({q["editor_id"] or f"{q['id']}:{q['plugin']}" for q in running
                            if q["editor_id"].lower() not in ok and q["plugin"].lower() not in ours})
            return None if not extra else f"{len(extra)} quests running that the allowed list lacks: {', '.join(extra[:20])}"
        if "music" in exp:
            m = self.b.music()
            ctx.setdefault("notes", {})["music"] = m
            cur = m.get("current")
            want = {w.lower() for w in exp["music"]["allowed"]}
            if cur is None or cur.get("engine") or (cur.get("editor_id") or "").lower() in want:  # engine: NoMusic
                return None
            return f"music type {cur.get('editor_id') or cur.get('id')} plays, wanted one of {sorted(want)} or none"
        raise StepFailed(f"unknown expectation {exp}")

    def expect(self, exp: dict, ctx: dict):
        end = time.monotonic() + float(exp.get("within", 5))
        while True:
            why = self.check(exp, ctx)
            if why is None or time.monotonic() >= end:
                return why
            time.sleep(0.5)

    # -- a run -----------------------------------------------------------------------------------------------
    def resume_point(self, j: dict, step: str) -> tuple[str | None, dict, int]:
        """For --from/--only <step>: the step save to load (None: the journey's start), the values kept up to it, and
        the step's index. SystemExit when the step is unknown or its predecessor's save was never made."""
        names = [s["name"] for s in j["steps"]]
        if step not in names:
            raise SystemExit(f"{j['id']}: no step {step!r}")
        i = names.index(step)
        before = [s["name"] for s in j["steps"][:i] if not s.get("owed")]
        if not before:
            return None, {}, i
        f = self.resume_dir / f"{j['id']}.json"
        state = json.loads(f.read_text()) if f.is_file() else {}
        have = state.get("saves", {})
        if before[-1] not in have:
            raise SystemExit(f"{j['id']}: no step save after {before[-1]!r} (run the journey through it first)")
        return have[before[-1]]["save"], have[before[-1]]["kept"], i

    def step_save(self, j: dict, step: str) -> None:
        """The game saved natively after a passed step; the journey's previous step save removed (one per journey)."""
        name = f"argj-{j['id']}-{step}"
        self.b.call("console", f"save {name}")
        f = self.resume_dir / f"{j['id']}.json"
        state = json.loads(f.read_text()) if f.is_file() else {}
        old = state.get("latest")
        saves = {k: v for k, v in state.get("saves", {}).items() if v["save"] != old or old == name}
        saves[step] = {"save": name, "kept": self.kept}
        if old and old != name:
            try:
                self.b.delete_save(old)
            except (BridgeError, AttributeError):
                pass
            saves = {k: v for k, v in saves.items() if v["save"] != old}
        self.resume_dir.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({"latest": name, "saves": saves}, indent=1, default=str))

    def run(self, j: dict, save: str, load: bool = True, start: str | None = None, only: bool = False) -> dict:
        self.out.mkdir(parents=True, exist_ok=True)
        rep = {"id": j["id"], "save": save, "scene": j.get("scene"), "steps": [], "passed": False, "loaded": load}
        self.scene, self.save = j.get("scene"), save
        first, scene = 0, j.get("scene")
        if start:
            resumed, kept, first = self.resume_point(j, start)
            if resumed:
                save, scene, load = resumed, None, True
                self.kept = dict(kept)
                rep.update(resumed_from=resumed, save=resumed)
        saves = j.get("step_saves", False)  # off by default: the console `save` was silently refused in game-13 (0 argj-*.ess after 30 items)
        last = first + 1 if only else len(j["steps"])
        t0 = time.monotonic()
        try:
            rep["scene_output"] = self.apply_scene(scene, save, load=load)
            rep["scene_s"] = round(time.monotonic() - t0, 1)
            for n, step in enumerate(j["steps"], 1):
                if not first < n <= last:
                    continue
                if step.get("owed"):  # not run: what it waits on is named, and the journey goes on past it
                    rep.setdefault("owed", []).append({"n": n, "name": step["name"], "why": step["owed"]})
                    print(f"  {n:2d} {step['name']:<24} OWED: {step['owed']}", flush=True)
                    continue
                rec = self.step(n, step)
                rep["steps"].append(rec)
                if rec["passed"] and saves:
                    self.step_save(j, step["name"])
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
        if not rep["passed"]:
            rep["logs"] = fetch_failure_logs(self.b, self.out, crash=bool(rep.get("crash")))
        rep["seconds"] = round(time.monotonic() - t0, 1)
        rep["calls"] = self.calls
        (self.out / "report.json").write_text(json.dumps(rep, indent=1))
        return rep

    def step(self, n: int, step: dict) -> dict:
        t = time.monotonic()
        ctx = {"since": self.b.call("events")["last"], "pos": self.b.call("player")["pos"], "log_lines": {}}
        for name in {e["log"]["name"] for e in step.get("expect", []) if "log" in e}:
            ctx["log_lines"][name] = len(skse_log(self.b, name))
        rec = {"n": n, "name": step["name"], "passed": True}
        retries0 = getattr(self.b, "transport_retries", 0)
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
        rec["transport_retries"] = getattr(self.b, "transport_retries", 0) - retries0
        print(f"  {n:2d} {step['name']:<24} {'ok' if rec['passed'] else 'FAIL: ' + rec['reason']}", flush=True)
        return rec


def _form_id(text) -> int | None:
    """A runtime form id as an int, from `0001A26F`, `0x1A26F` or `"0001A26F"`; None for anything else."""
    t = str(text or "").strip().strip('"')
    try:
        return int(t, 16)
    except ValueError:
        return None


TALK_UNITS, TALK_WAIT_S = 110, 5.0  # 5 s: a player moveto before it may load a cell and fade
STRIKE_UNITS = 80  # inside a sword's reach
ACTIONS = {"pad": Runner._pad, "talk": Runner._talk, "strike": Runner._strike, "key": Runner._key, "console": Runner._console, "teleport": Runner._teleport,
           "wait": Runner._wait, "game_hours": Runner._game_hours, "call": Runner._call, "relaunch": Runner._relaunch}
QUIT_WAIT_S = 60  # a clean quit (a suspend save first, 2.8 §c) gets this long before launch kills what is left
EXPECTS = ("read", "console", "event", "moved", "quests_running", "music", "log")
SKSE_LOGS = "$env:USERPROFILE\\Documents\\My Games\\Skyrim Special Edition\\SKSE"


def skse_log(b, name: str) -> list[str]:
    """An SKSE plugin's log on the machine (ArgoniaCore, ArgoniaBridge), as lines; a step compares the lines past
    its start. A log that a launch rewrote is shorter: then every line counts as new."""
    import re
    if not re.fullmatch(r"[A-Za-z0-9_]+", name):
        raise StepFailed(f"log {name!r}: a plugin's name")
    out = b.machine.ps(f"Get-Content \"{SKSE_LOGS}\\{name}.log\" -EA SilentlyContinue", timeout=60)
    return out.splitlines()


GAME_DOCS = "$env:USERPROFILE\\Documents\\My Games\\Skyrim Special Edition"
FAIL_LOG_LINES = 200
CRASH_HEAD_LINES = 120  # a crash log's header, probable call stack and objects sit in its first ~60-120 lines


def fetch_failure_logs(b, out: pathlib.Path, crash: bool = False) -> list[str]:
    """On a failed run only: the last 200 lines of ArgoniaCore.log, ArgoniaBridge.log and Papyrus.0.log (and, on a
    crash, the newest crash-*.log) from the machine into the item's folder. Never raises: a fetch that fails is noted."""
    srcs = {"ArgoniaCore.log": f"{SKSE_LOGS}\\ArgoniaCore.log", "ArgoniaBridge.log": f"{SKSE_LOGS}\\ArgoniaBridge.log",
            "Papyrus.0.log": f"{GAME_DOCS}\\Logs\\Script\\Papyrus.0.log"}
    if crash:
        srcs["crash.log"] = None
        srcs["crash-head.log"] = "head"
    got = []
    out.mkdir(parents=True, exist_ok=True)
    for name, path in srcs.items():
        newest = (f"Get-ChildItem \"{SKSE_LOGS}\\crash-*.log\" -EA SilentlyContinue | Sort-Object LastWriteTime | "
                  "Select-Object -Last 1 | ")
        cmd = (newest + f"Get-Content -Tail {FAIL_LOG_LINES}" if path is None else
               newest + f"Get-Content -TotalCount {CRASH_HEAD_LINES}" if path == "head" else
               f"Get-Content \"{path}\" -Tail {FAIL_LOG_LINES} -EA SilentlyContinue")
        try:
            text = b.machine.ps(cmd, timeout=60)
        except Exception as e:  # a dead machine or a stalled shell must not hide the failure it reports
            text = f"(fetch failed: {e})"
        fname = name if path == "head" else f"tail-{name}"
        (out / fname).write_text(text)
        got.append(fname)
    return got


# The 0.2 §d bar (60 fps median, 45 fps 1% lows) as frame times, and the soak's flatness tolerances.
SOAK_BARS = {"p50_ms": 1000 / 60, "p99_ms": 1000 / 45, "queue_growth": 5, "cosave_growth_bytes": 512}


def soak(b, j: dict, journeys: pathlib.Path, out: pathlib.Path, save: str, clock=time.monotonic) -> dict:
    """Loop the journey for `minutes`, measuring after each loop; judged once at the end (all loops kept)."""
    s = j["soak"]
    inner = load_journey(journeys / f"{s['journey']}.yaml")
    bars = {**SOAK_BARS, **s.get("bars", {})}
    end = clock() + 60 * float(s.get("minutes", 60))
    loops, verdict = [], {"id": j["id"], "journey": inner["id"], "bars": bars, "passed": False}
    out.mkdir(parents=True, exist_ok=True)
    while clock() < end:
        n = len(loops) + 1
        rep = Runner(b, out / f"loop-{n:03d}", stills=False).run(inner, save)
        loop = {"n": n, "passed": rep["passed"], "seconds": rep["seconds"], "failed_at": rep.get("failed_at")}
        if rep.get("crash"):
            loop["crash"] = rep["crash"]
            loops.append(loop)
            break
        try:
            loop["papyrus"] = b.papyrus_queue()
            loop["save_bytes"] = b.save_bytes("ArgoniaRest")
            loop["frames"] = b.call("frametime", int(s.get("frames", 600)))
        except GameDown as e:
            loop["crash"] = str(e)
            loops.append(loop)
            break
        except BridgeError as e:
            loop["measure_error"] = str(e)
        loops.append(loop)
        print(f"soak loop {n}: {'ok' if loop['passed'] else 'FAIL at ' + str(loop['failed_at'])}; "
              f"queue {loop.get('papyrus', {}).get('stacks')}, co-save {loop.get('save_bytes', {}).get('skse')}, "
              f"p50 {loop.get('frames', {}).get('p50_ms')}", flush=True)
    verdict["loops"] = loops
    verdict["reasons"] = judge_soak(loops, bars)
    verdict["passed"] = not verdict["reasons"]
    (out / "soak.json").write_text(json.dumps(verdict, indent=1))
    return verdict


def judge_soak(loops: list[dict], bars: dict) -> list[str]:
    """Every reason the soak fails (none: it passed)."""
    why = []
    if not loops:
        return ["no loop ran"]
    why += [f"loop {x['n']}: the game went down ({x['crash']})" for x in loops if x.get("crash")]
    why += [f"loop {x['n']}: failed at {x['failed_at']}" for x in loops if not x["passed"] and not x.get("crash")]
    why += [f"loop {x['n']}: not measured ({x['measure_error']})" for x in loops if x.get("measure_error")]
    q = [x["papyrus"]["stacks"] for x in loops if "papyrus" in x]
    if q and max(q) - q[0] > bars["queue_growth"]:
        why.append(f"Papyrus queue grew {q[0]} -> {max(q)} stacks (bar +{bars['queue_growth']})")
    c = [x["save_bytes"]["skse"] for x in loops[1:] if "save_bytes" in x]
    if c and max(c) - min(c) > bars["cosave_growth_bytes"]:
        why.append(f"co-save after the first loop ranged {min(c)}..{max(c)} bytes (bar {bars['cosave_growth_bytes']})")
    for x in loops:
        f = x.get("frames") or {}
        if f.get("p50_ms", 0) > bars["p50_ms"] or f.get("p99_ms", 0) > bars["p99_ms"]:
            why.append(f"loop {x['n']}: frame time p50 {f.get('p50_ms')} / p99 {f.get('p99_ms')} ms over the bar "
                       f"({bars['p50_ms']:.1f} / {bars['p99_ms']:.1f})")
    return why


def third_person(b):
    """The play camera is third person (owner, 2026-10-29); a save can hold first, where TDM is off. Setup only."""
    for _ in range(2):
        if b.call("console", "IsPC1stPerson")["output"].strip().endswith("0.00"):
            return
        b.call("input", "key", "F", 300)  # Toggle POV: a 100 ms press did not take (2026-10-30)
        time.sleep(1.0)
    raise StepFailed("the camera stays in first person")


def running_quests(b) -> list[dict]:
    """The running quests, from the bridge's `quests` read ({"editor_id", "plugin", ...}). Not the console's `sq`: its
    output is the console buffer's tail, 1,567 "(Off)" lines with the running ones cut off (game-7, 2026-10-30)."""
    return b.running_quests()


def signature(rep: dict) -> str:
    bad = next((s for s in rep["steps"] if not s["passed"]), None)
    return f"{rep.get('failed_at')}|{(bad or {}).get('reason') or rep.get('error') or rep.get('crash')}"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("journey", type=pathlib.Path)
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--save", default=None)
    p.add_argument("--no-stills", action="store_true", help="stills only for a failed step")
    p.add_argument("--dry", action="store_true", help="validate the file and its scene; no game")
    p.add_argument("--from", dest="start", default=None, help="load the step save before this step and run from it")
    p.add_argument("--only", default=None, help="load the step save before this step and run it alone")
    a = p.parse_args(argv)
    if a.dry:
        print(dry(a.journey))
        return 0
    j = load_journey(a.journey)
    save = a.save or j.get("save") or BASE_SAVE
    if "soak" in j:
        out = REPO / "out" / "runs" / j["id"] / time.strftime("%Y%m%dT%H%M%S")
        v = soak(Bridge(), j, a.journey.parent, out, save)
        print(f"{j['id']}: {'PASS' if v['passed'] else 'FAIL'} after {len(v['loops'])} loops: {out / 'soak.json'}")
        for r in v["reasons"]:
            print("  " + r)
        return 0 if v["passed"] else 2 if any(x.get("crash") for x in v["loops"]) else 1
    b, fails, worst = Bridge(), {}, 0
    for r in range(1, a.runs + 1):
        out = REPO / "out" / "runs" / j["id"] / time.strftime("%Y%m%dT%H%M%S")
        print(f"{j['id']} run {r}: {out}", flush=True)
        rep = Runner(b, out, stills=not a.no_stills).run(j, save, **({"start": a.only or a.start, "only": bool(a.only)}
                                                           if a.only or a.start else {}))
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
