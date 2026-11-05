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

Actions: pad <seq>; show <ref | {ref, menu, view}> / dialogue <ref> / lockpick <ref> (a screen under check opened directly
by the console's activate, no crosshair; the step fails unless the menu event arrives); key "<K[+K]> <ms>"; talk <ref> (the NPC set 1.1 m before the player facing them, then E once
the crosshair shows it, or the step fails); open <ref> (the same for a crate or lock, aimed low); console <line>; teleport [cell <edid> | pos x y z | ref <id>];
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
import os
import pathlib
import subprocess
import sys
import shutil
import time

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from tools.bridge import Bridge, BridgeError, GameDown, frame_difference  # noqa: E402

BASE_SAVE = "argoniabase"
RESUME = REPO / "out" / "resume"
SCENES = REPO / "tests" / "scenes"
GAME_ROOT = "C:/Program Files (x86)/Steam/steamapps/common/Skyrim Special Edition"
OPS = {"eq": lambda a, b: a == b, "ne": lambda a, b: a != b, "gt": lambda a, b: a > b, "ge": lambda a, b: a >= b,
       "lt": lambda a, b: a < b, "le": lambda a, b: a <= b, "contains": lambda a, b: str(b) in str(a),
       "not_contains": lambda a, b: str(b) not in str(a)}


def _none_safe(f):
    def g(a, b):
        try:
            return f(a, b)
        except TypeError:   # a read that found nothing (None) fails the expectation, never the runner
            return False
    return g


OPS.update({k: _none_safe(v) for k, v in OPS.items()})


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
            if "kinds" in e and (not isinstance(e["kinds"], dict) or not {"ge", "among"} <= set(e["kinds"])):
                raise SystemExit(f"{path}: step {s['name']}: kinds takes {{ge: N, among: [kind names]}}")
            if ("read" in e or "console" in e) and not (set(e) & set(OPS) | {"kinds"}) and "keep" not in e:
                raise SystemExit(f"{path}: step {s['name']}: {e} has no comparison and keeps nothing")
            if "read" in e and not isinstance(e["read"], list):
                raise SystemExit(f"{path}: step {s['name']}: read takes a list [<command>, args...]")
    if "camera" in j and j["camera"] not in ("first", "third"):
        raise SystemExit(f"{path}: `camera:` is `first` or `third`, said once at the top")
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


def kinds_found(actors, among) -> list[str]:
    """The `among` kinds that a live actor of the list is: its name ends the kind's name or the kind's name ends its
    (the mods name an actor "Leech" where the list says "Giant Leech")."""
    names = [str(a.get("name") or "").lower() for a in (actors if isinstance(actors, list) else []) if not a.get("dead")]
    return sorted(k for k in among if any(n and (k.lower().endswith(n) or n.endswith(k.lower())) for n in names))


def dig(value, path: str):
    for part in [p for p in str(path).split(".") if p]:
        value = (value[int(part)] if int(part) < len(value) else None) if isinstance(value, list) else value.get(part) if isinstance(value, dict) else None
    return value


class Runner:
    def __init__(self, bridge, out: pathlib.Path, stills: bool = True, run_sh=None, sent: dict | None = None):
        self.b, self.out, self.stills = bridge, out, stills
        self.run_sh = run_sh or str(REPO / "infra" / "gpu-box" / "run.sh")
        # scene -> the resolved text last put on the machine: a batch shares one, so an unchanged scene is not re-sent
        self.sent = {} if sent is None else sent
        self.calls = []
        self.camera: str | None = None  # the journey's camera mode, re-asserted and read before each still
        self.view_unverified = False  # a load or relaunch happened: the next first-person toggle is checked against the view
        self.kept: dict = {}
        self.scene: str | None = None  # the journey's scene and save, for a relaunch
        self.save = BASE_SAVE
        self.independent = False  # the journey's `independent_steps: true`: a step may be rerun alone after a relaunch
        self.relaunches: list = []  # the camera relaunches this run made (report.json `relaunches`; the batch's `launches`)
        self.resume_dir = RESUME
        self.settle_waits = False  # a batch's `settle_waits: true`: fixed waits after a move become `settle` (settled_do)
        self.settle_since = None  # the event seq at the step's start: `settle` waits on menus opened after it

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
            self.view_unverified = True
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

    def _mouse(self, spec):
        """`mouse: "640 360"` (or `"640 360 event"`): the game's cursor to a screen pixel by the engine (bridge `input
        mouse`); Wind UI reads that cursor, never the OS's (windui.md)."""
        args = str(spec).split()
        r = self.b.call("input", "mouse", *args)
        self.calls.append({"call": ["input", "mouse", *args], "result": r})
        return r

    def _click(self, spec):
        """`click: left` / `click: right` / `click: "left 120"`: a mouse button by the engine route."""
        args = str(spec or "left").split()
        r = self.b.call("input", "click", *args)
        self.calls.append({"call": ["input", "click", *args], "result": r})
        return r

    def _wheel(self, spec):
        """`wheel: "down 3"`: wheel notches by the engine route."""
        args = str(spec).split()
        r = self.b.call("input", "wheel", *args)
        self.calls.append({"call": ["input", "wheel", *args], "result": r})
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
        """`console: <line>`, or `console: {line: <line>, settle: <s>}`: the line is sent again while the game's
        main thread is still busy (a worldspace load after coc/cow holds it past the bridge's own retries), for up
        to `settle` seconds, then the last error stands (bmv-look, 2026-11-01)."""
        # a bare line retries 30 s: the line after a moveto meets the same busy thread (driver, 2026-11-02)
        if not isinstance(line, dict):
            line = {"line": line, "settle": 30}
        if isinstance(line, dict):
            settle, line = float(line.get("settle", 0)), line["line"]
            if "|0x" in line:  # `<file>.esm|0x<hex>`: the runtime id for this launch's load order (editor ids of
                line = self.b.resolve_plugin_forms(line)  # weathers were not resolving on Paris, round 4 batch two)
            end = time.monotonic() + settle
            while True:
                try:
                    return self.b.call("console", line)
                except BridgeError as e:
                    if "did not run the task" not in str(e) or time.monotonic() >= end:
                        raise
                    time.sleep(2)
        return self.b.call("console", line)

    def _camera(self, arg):
        """`camera: first` (or `third`): the play camera, waited for. The bridge's `camera <mode>` calls PlayerCamera
        natively on the main thread, then `camera state` reads currentState natively a frame later: that read is the
        primary assert (1.15-r6 camera-native; r6-chain19 lost first person after every relaunch through the console
        and F key). For first person the frame check (_view_is_first) is the second opinion after a load or relaunch.
        A DLL without the native read falls back to the console's IsPC1stPerson; one without the command to the F key
        and Papyrus's Game.ForceFirstPerson through `cgf`. 7 tries, 3 s apart; fails the step naming the tries."""
        mode = str(arg).strip()
        want = {"first": "1.00", "third": "0.00"}.get(mode)
        if want is None:
            raise StepFailed(f"camera: {arg!r} is `first` or `third`")
        fn = "ForceFirstPerson" if want == "1.00" else "ForceThirdPerson"
        tries = []
        bridge_ok = True
        native_ok = True
        # The command is re-asked on every try: a load or cell change finishing after the first ask resets the camera.
        for n in range(0, 7):
            if bridge_ok:
                try:
                    r = self.b.call("camera", mode)
                    tries.append(f"bridge {r.get('first_person')}")
                except BridgeError as e:
                    bridge_ok = native_ok = False
                    tries.append(f"bridge error {str(e)[:60]}")
            time.sleep(0.5 if n == 0 else 3.0)   # the switch lands a frame or two after the call answers
            now = None
            if native_ok:
                try:
                    st = self.b.call("camera", "state")
                    if "native" not in st:
                        raise BridgeError("no native read")
                    now = "1.00" if st.get("first_person") else "0.00"
                    tries.append(f"native {st.get('state')}")
                except BridgeError as e:
                    native_ok = False
                    tries.append(f"native error {str(e)[:40]}")
            if now is None:
                try:
                    now = self._console("IsPC1stPerson")["output"].strip()
                except BridgeError as e:
                    now = f"error {e}"
                tries.append(f"read {now[-40:]}")
            if now.endswith(want) and want == "1.00" and self.view_unverified and not self._view_is_first(tries):
                now = "view check failed"   # the read says first person, the frame does not move: retried like a bad read
            if now.endswith(want):
                self.calls.append({"call": ["camera", mode], "tries": tries})
                route = "native" if native_ok else ("bridge" if bridge_ok else None)
                return {"camera": mode, "tries": n, **({"route": route} if route and n == 0 else {})}
            if n == 6:
                break
            if not bridge_ok:
                if n % 2 == 0:
                    self.b.call("input", "key", "F", 300, "engine")
                else:
                    try:
                        self.b.call("console", f'cgf "Game.{fn}"')
                    except BridgeError as e:
                        tries.append(f"cgf error {e}")
        if os.environ.get("ARGONIA_CAMERA_SOFT"):   # driver, 2026-11-02: record the readings, carry on (the still may be third person)
            self.calls.append({"call": ["camera", mode], "tries": tries, "soft_fail": True})
            return {"camera": mode, "tries": 6, "soft_fail": True}
        raise StepFailed(f"the camera never became {mode}: reads {tries}; engine state {self._engine_state()}")

    VIEW_CHANGE_MIN = 0.15   # a real third->first switch moves the camera, so far more than this fraction of pixels changes

    def _view_is_first(self, tries, attempts=3) -> bool:
        """After a load or relaunch the console read (and the bridge's own read-back) can say first person while the
        view is still third (r6 sky-ab: the stills after the relaunch showed the player's body). The view is measured:
        the camera put to third and a still taken, put to first and another; the two must differ by VIEW_CHANGE_MIN
        (bridge.frame_difference), else it is toggled again, up to `attempts` times. True when it moved (and the flag is
        cleared), or when no still can be taken (the check is then skipped, not failed)."""
        grab = getattr(self.b, "screenshot", None)
        if grab is None:
            return True
        tmp = self.out / "camera-view-check"
        tmp.mkdir(parents=True, exist_ok=True)
        for k in range(attempts):
            try:
                self.b.call("camera", "third")
                time.sleep(1.5)
                a = grab(tmp / f"third{k}.png")
                self.b.call("camera", "first")
                time.sleep(1.5)
                b = grab(tmp / f"first{k}.png")
            except BridgeError as e:
                tries.append(f"view check skipped {str(e)[:40]}")
                return True
            try:
                d = frame_difference(a, b)
            except Exception as e:   # noqa: BLE001  an unreadable still: the check is skipped, never a failure
                tries.append(f"view check skipped {str(e)[:40]}")
                return True
            tries.append(f"view diff {d:.2f}")
            if d >= self.VIEW_CHANGE_MIN:
                self.view_unverified = False
                shutil.rmtree(tmp, ignore_errors=True)
                return True
        shutil.rmtree(tmp, ignore_errors=True)
        # identical frames on every try (diff 0.00) say the picture is frozen (a load, a paused frame, the first frame
        # after a relaunch), not that the camera did not move: the native state is the primary assert (lane
        # camera-native); a second opinion with no information does not veto it (r6-chain23 river-steps, 01:08: 8 cycles
        # of 'native first' + 'view diff 0.00' failed the whole journey before its first still)
        if all(t == "view diff 0.00" for t in tries[-attempts:] if t.startswith("view diff")):
            try:
                st = self.b.call("camera", "state")
                if st.get("first_person") and st.get("native"):
                    tries.append("view check inconclusive (frozen frames); native first accepted")
                    self.view_unverified = False
                    return True
            except BridgeError:
                pass
        return False

    ENGINE_STATE_READS = ("IsSwimming", "GetSitState", "GetKnockedState", "GetSleepState", "GetDead")

    def _engine_state(self) -> str:
        """Why the engine may refuse first person, read through the console: swimming, sitting or in furniture, knocked
        (kill-move, ragdoll), sleeping, dead. Named in the camera failure so the next one says why."""
        out = []
        for fn in self.ENGINE_STATE_READS:
            try:
                out.append(self._console(f"player.{fn}")["output"].strip()[-40:])
            except BridgeError as e:
                out.append(f"{fn} error {str(e)[:40]}")
        return "; ".join(out)

    def _hud(self, arg):
        """`hud: off`: the vanilla HUD hidden by `tm`, and our PrismaUI HUD hidden by the bridge's dev switch
        (core HudShow off); its state is read back (ViewState hud) and kept in the report."""
        if str(arg).strip() not in ("off", "False"):   # unquoted YAML off is False
            raise StepFailed(f"hud: {arg!r} is `off`")
        self._console({"line": "tm", "settle": 30})
        try:
            self.b.hud("off")
            ours = self.b.core("ViewState", "hud")
        except Exception as e:  # an optional read: never fails the step
            ours = f"unread: {e}"
        self.calls.append({"call": ["hud", "off"], "ours": ours})
        return {"hud": "off", "vanilla": "tm", "ours": ours}

    def _teleport(self, args):
        return self.b.call("teleport", *(args if isinstance(args, list) else str(args).split()))

    def _burst(self, arg):
        """A still loop for a screen too short for a step's still (the Loading Menu, ui-review4): grab.ps1 records
        {frames, fps} in the desktop session without waiting, while the step's next actions run; {burst_fetch: name}
        later copies the frames to out/<name>-NN.png."""
        frames, fps = int(arg.get("frames", 20)), float(arg.get("fps", 2))
        # over 4 fps or 40 frames, grab.ps1 records a video (x264) and cuts it into frames after
        if frames > 900 or frames / fps > 30 or fps > 30:
            raise StepFailed(f"burst {arg}: at most 30 s, at most 30 fps")
        m = self.b.machine
        env = dict(m.env, DESKTOP_JOB="burst", DESKTOP_WAIT="0")
        m.ps(r"Remove-Item C:\argonia\logs\burst_*.png, C:\argonia\logs\burst.mp4, C:\argonia\logs\desktop-burst.done -EA SilentlyContinue; exit 0", 60)
        # started, not awaited: the job's log does not exist yet, so run.sh's last line exits 1 (ignored)
        subprocess.run([m.run, "desktop", rf"& C:\argonia\infra\grab.ps1 C:\argonia\logs\burst.png -Frames {frames} -Fps {fps}"],
                       capture_output=True, timeout=90, env=env)

    def _burst_fetch(self, name):
        m = self.b.machine
        for _ in range(90):   # a fast clip is cut into frames after it ends
            out = m.ps(r"Test-Path C:\argonia\logs\desktop-burst.done", 60)
            if "True" in out:
                break
            time.sleep(1)
        # one zip, one copy: a copy per frame took ~2 s each (a 150-frame clip, five minutes)
        m.ps(r"Remove-Item C:\argonia\logs\burst.zip -EA SilentlyContinue; $f = @(Get-ChildItem C:\argonia\logs\burst_*.png) + @(Get-ChildItem C:\argonia\logs\burst.mp4 -EA SilentlyContinue); if ($f) { Compress-Archive -Path $f.FullName -DestinationPath C:\argonia\logs\burst.zip -CompressionLevel NoCompression -Force }; exit 0", 120)
        z = self.out / f"{name}.zip"
        m.get(r"C:\argonia\logs\burst.zip", z)
        import zipfile
        names = []
        if z.exists():
            with zipfile.ZipFile(z) as zf:
                names = sorted(n for n in zf.namelist() if n.endswith(".png"))
                for k, n in enumerate(names):
                    (self.out / f"{name}-{k:02d}.png").write_bytes(zf.read(n))
                if "burst.mp4" in zf.namelist():
                    (self.out / f"{name}.mp4").write_bytes(zf.read("burst.mp4"))
            z.unlink()
        return {"frames": len(names)}

    def _wait(self, seconds):
        if float(seconds) > 10:
            raise StepFailed(f"wait {seconds}: a step waits at most 10 s (keep steps short; use game_hours)")
        time.sleep(float(seconds))

    def _settle(self, arg):
        """`settle: <cap s>` (or `settle: {cap: 14, min: 1.0}`): the measured settle that replaces fixed waits before a
        still (1.15-r4-fast-loop: the world panel's `wait: 10` + `wait: 4` were 14 of its 25.7 s per still). Returns once
        no Loading Menu or Fader Menu is open since the step began and two `player` reads 0.5 s apart agree within
        `tol` units (the cell attached, the moveto landed), and at least `min` s have passed; at `cap` it returns anyway,
        naming what was still moving (the still is then judged by the driver as any other)."""
        cfg = arg if isinstance(arg, dict) else {"cap": arg}
        cap, least, tol = float(cfg.get("cap", 14)), float(cfg.get("min", 1.0)), float(cfg.get("tol", 1.0))
        if cap > 30:
            raise StepFailed(f"settle cap {cap}: at most 30 s")
        since = self.settle_since if self.settle_since is not None else (self.b.call("events") or {}).get("last")
        waited, prev, why = 0.0, None, "never read"
        while True:
            menus = [e.get("data") or {} for e in ((self.b.call("events", since, "menu") or {}).get("events") or [])]
            open_now = {}
            for d in menus:
                if d.get("menu") in ("Loading Menu", "Fader Menu"):
                    open_now[d["menu"]] = bool(d.get("opening"))
            busy = [m for m, o in open_now.items() if o]
            pos = ((self.b.call("player") or {}).get("pos")) or {}
            here = tuple(float(pos.get(k, 0.0)) for k in ("x", "y", "z"))
            still = prev is not None and max(abs(a - b) for a, b in zip(here, prev)) <= tol
            why = f"open: {', '.join(busy)}" if busy else ("moving" if not still else "")
            if (not why and waited >= least) or waited >= cap:
                break
            prev = here
            time.sleep(0.5)
            waited += 0.5
        rec = {"call": ["settle", cap], "waited": waited}
        if why and waited >= cap:
            rec["capped"] = why
        self.calls.append(rec)
        return rec

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
        self.view_unverified = True
        launched = self.b.launch()  # kills what is left (a quit that hung), lays the DLL, waits for the ping
        self.apply_scene(scene, save)
        r = {"quit_clean": clean, "save": save, "ping": launched.get("ping")}
        self.calls.append({"call": ["relaunch", save], "result": r})
        return r

    def _face(self, ref, units=None, need_crosshair=True, chest_z=None):
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
        seen, end, aimed = None, time.monotonic() + TALK_WAIT_S, time.monotonic()
        while True:
            seen = (self.b.call("crosshair") or {}).get("ref")
            if seen and want is not None and _form_id(seen.get("id")) == want:
                break
            if time.monotonic() - aimed >= 1.0:  # an NPC under AI or a moveto that landed off the mark: aim again
                self._aim(caller, chest_z)
                aimed = time.monotonic()
            if time.monotonic() >= end:
                if not need_crosshair:  # a swing lands on what stands in front; the step's hit expects are the check
                    return
                raise StepFailed(f"talk {ref}: the crosshair never showed it within {TALK_WAIT_S:g} s "
                                 f"(last: {(seen or {}).get('editor_id') or (seen or {}).get('id') or 'nothing'})")
            time.sleep(0.25)

    def _aim(self, caller, chest_z=None):
        """The player turned to the ref's measured position: yaw by atan2 of the offset, pitch down to its chest
        (AIM_CHEST_Z above its feet) from the eye (AIM_EYE_Z above the player's); game-16: a fixed heading and
        a fixed 15-degree pitch missed an NPC that moved or stood off the moveto mark."""
        try:
            tx, ty, tz = (float(str(self.b.call("console", f"{caller}.GetPos {a}").get("output", "")).split(">>")[-1])
                          for a in "XYZ")
        except (ValueError, BridgeError):
            return
        pos = self.b.call("player")["pos"]
        dx, dy = tx - float(pos["x"]), ty - float(pos["y"])
        dz = (tz + (AIM_CHEST_Z if chest_z is None else chest_z)) - (float(pos["z"]) + AIM_EYE_Z)
        yaw = math.degrees(math.atan2(dx, dy)) % 360
        pitch = -math.degrees(math.atan2(dz, max(math.hypot(dx, dy), 1.0)))  # x: positive looks down
        self.b.call("console", f"player.setangle z {yaw:.1f}")
        self.b.call("console", f"player.setangle x {pitch:.1f}")
        self.b.call("input", "key", "W", 40)  # the third-person camera takes setangle only once the player moves

    def _rest(self, marker):
        """`rest: <marker ref>`: rest at the camp spot placed at that marker, the player's way: combat stopped around
        the player (the engine refuses a rest with a hostile in combat), the player set 90 units short of the marker
        and aimed down at it, then E (up to 3 tries) until ArgoniaCore logs the rest or its refusal. StepFailed on a
        refusal or no rest line (game-16: grow-at-rest and die-and-recover never rested; the crosshair was off)."""
        marker = str(marker).strip()
        self.b.call("console", "player.stopcombat")
        self.b.call("console", f"player.moveto {marker} 0 -90 0")
        time.sleep(4)  # the moveto settles (cell attach)
        n0 = len(skse_log(self.b, "ArgoniaCore"))
        for attempt in (1, 2, 3):
            self._aim(marker, chest_z=0)
            time.sleep(0.5)
            self.b.call("input", "key", "E", 120)
            for _ in range(16):
                time.sleep(0.5)
                new = skse_log(self.b, "ArgoniaCore")[n0:]
                done = [ln for ln in new if "rest: at " in ln or "rest: refused" in ln]
                if done:
                    self.b.call("console", "player.setangle x 0")
                    self.calls.append({"call": ["rest", marker], "result": done[-1], "attempt": attempt})
                    if "refused" in done[-1]:
                        raise StepFailed(f"rest at {marker}: refused: {done[-1]}")
                    return done[-1]
        raise StepFailed(f"rest at {marker}: no rest line in ArgoniaCore.log after 3 E presses")

    def _close_menu(self, menu):
        """`close_menu: <menu>`: the open menu closed the way a player does (the first key that works of
        CLOSE_KEYS), checked by its close event; our journal view by the Views read. StepFailed when none closes it."""
        menu = str(menu).strip()
        keys = CLOSE_KEYS
        if menu == "MapMenu":  # our chart owns the map's input: closed by its own close intent, the control it binds
            keys = (("view.close", "intent"),) + CLOSE_KEYS
        for key, route in keys:
            last = (self.b.call("events") or {}).get("last")
            if route == "intent":
                self.b.call("core", "ViewIntent", json.dumps({"type": "view.close", "v": 1, "body": {"view": MENU_VIEWS[menu]}}))
            elif route == "pad":
                self.b.pad(f"{key}:150 -:100")
            else:
                self.b.call("input", "key", key, 100, route)
            time.sleep(1.5)
            view = MENU_VIEWS.get(menu)  # our view over it (the M chart over MapMenu: smoke game-16)
            view_ok = view is None or f"{view} ready closed" in json.dumps(self.b.call("core", "Views"))
            evs = (self.b.call("events", last, "menu") or {}).get("events") or []
            # the router hides MapMenu as the chart opens (its close event comes then): the chart closed is the map closed
            menu_ok = menu in ("journal", "MapMenu", "system", "wait") or any((e.get("data") or {}).get("menu") == menu
                                               and not (e.get("data") or {}).get("opening") for e in evs)
            if view_ok and menu_ok:
                self.calls.append({"call": ["close_menu", menu], "result": [key, route]})
                return [key, route]
        raise StepFailed(f"close_menu {menu}: none of {keys} closed it")

    def _caller(self, ref):
        ref = str(ref).strip().strip('"')
        return ref if ref.startswith("ARG_") else f'"{ref}"'  # a runtime id calls quoted (tools/journey_lint.py)

    def _show(self, ref, menu=None, view=None, label="show", tries=3):
        """Direct opener (owner ruling 2026-11-03: a screen under check is opened by the console, never by lining up
        the crosshair): `<ref>.activate player`, the engine's own activation of that ref, no aim and no key.
        It holds once a menu opened since the call (named `menu` when given) or our `view` reads a body; sent again
        up to `tries` times; StepFailed when the expected menu event never arrives."""
        caller = self._caller(ref)
        for attempt in range(1, tries + 1):
            last = (self.b.call("events") or {}).get("last")
            r = self.b.call("console", f"{caller}.activate player")
            self.calls.append({"call": [label, str(ref)], "result": r, "attempt": attempt})
            for _ in range(6):
                time.sleep(0.5)
                evs = (self.b.call("events", last, "menu") or {}).get("events") or []
                if any((e.get("data") or {}).get("opening") and (menu is None or (e.get("data") or {}).get("menu") == menu)
                       for e in evs):
                    return r
                if view and (self.b.call("core", "ViewState", view) or {}).get("value"):
                    return r
        raise StepFailed(f"{label} {ref}: no {menu or view or 'menu'} event after {tries} activations by console")

    def _place_before(self, ref, units):
        """The ref set `units` in front of the player (no turn, no aim): an NPC to speak to stands near enough."""
        caller = self._caller(ref)
        h = float(self.b.call("player")["heading_deg"])
        dx, dy = units * math.sin(math.radians(h)), units * math.cos(math.radians(h))
        self.b.call("console", f"{caller}.moveto player {dx:.0f} {dy:.0f} 0")

    def _dialogue(self, ref):
        """`dialogue: <ref>`: our dialogue window opened on the NPC directly (placed before the player, then the
        console's activate); holds when ViewState dialogue reads a body, else StepFailed. For a screen under check;
        `talk` stays for a step whose action is the thing checked."""
        self._place_before(ref, TALK_UNITS)
        return self._show(ref, view="dialogue", label="dialogue")

    def _lockpick(self, ref):
        """`lockpick: <ref>`: the Lockpicking Menu on a locked ref. The console's activate skips the lock (151959) and
        opens the container instead, so it is tried first only to learn that: a Container Menu it opens is closed and
        the engine's own pick is used (`open`: the ref set before the player, E once the crosshair holds it); the
        step fails unless a Lockpicking Menu opening is seen."""
        last = (self.b.call("events") or {}).get("last")
        try:
            self._show(ref, menu="Lockpicking Menu", label="lockpick", tries=1)
            return None
        except StepFailed:
            evs = (self.b.call("events", last, "menu") or {}).get("events") or []
            if any((e.get("data") or {}).get("opening") for e in evs):  # the script activate opened the container
                self._close_menu("ContainerMenu")
        self._open(ref)
        evs = (self.b.call("events", last, "menu") or {}).get("events") or []
        if not any((e.get("data") or {}).get("menu") == "Lockpicking Menu" and (e.get("data") or {}).get("opening") for e in evs):
            raise StepFailed(f"lockpick {ref}: no Lockpicking Menu event")

    def _talk(self, ref):
        """`talk: <ref>`: _face, then E (retried while no menu opens)."""
        self._face(ref)
        return self._activate(120)

    def _open(self, ref):
        """`open: <ref>`: a container, door or lock opened the player's way: the ref set OPEN_UNITS before the player,
        the aim pitched to its middle (OPEN_Z, a crate's, not a person's chest), E once the crosshair shows it. A fixed
        heading and pitch with a moveto missed the crate and no lock opened (r5 menus-look 21-lockpicking)."""
        self._face(ref, OPEN_UNITS, chest_z=OPEN_Z)
        return self._activate(120)

    def _show_action(self, spec):
        """`show: <ref>` or `show: {ref, menu, view}`: _show as an action."""
        if isinstance(spec, dict):
            return self._show(spec["ref"], spec.get("menu"), spec.get("view"))
        return self._show(spec)

    def _strike(self, ref):
        """`strike: <ref>`: one real melee swing at the ref with no key or pad on the path (the input path is the
        owner's #17 stream check): the ref faced at reach (_face, STRIKE_UNITS), the weapon drawn (R) and one attack
        (MOUSE1), both engine ButtonEvents (`sae` attack events were refused by the player's graph; the pad was dead
        after another lane's run: game-15), so the engine's hit, our damage and the crime rules all run."""
        # The crosshair is not the hit: at sword reach the third-person pick missed the armed deserter in some runs
        # (g18b, g18c, g19 ten-blows) while the swing still lands, so the strike swings after the aim either way.
        self._face(ref, STRIKE_UNITS, need_crosshair=False)
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
    def check_kinds(self, exp: dict):
        """read + kinds {ge: N, among: [names]}: the read's path lists actors; the distinct `among` kinds among the live
        ones must number at least N. The kinds found are kept (a list) under `keep`."""
        got = dig(self.b.call(*self.fill(exp["read"])), exp.get("path", ""))
        found = kinds_found(got, exp["kinds"]["among"])
        if "keep" in exp:
            self.kept[exp["keep"]] = found
        want = int(exp["kinds"]["ge"])
        return None if len(found) >= want else (f"{' '.join(map(str, exp['read']))} {exp.get('path', '')}: {len(found)} distinct "
                                                f"kinds of the list {found}, wanted at least {want}")

    def check(self, exp: dict, ctx: dict):
        """None when it holds, else the reason in words."""
        if "kinds" in exp and "read" in exp:
            return self.check_kinds(exp)
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

    def run(self, j: dict, save: str, load: bool = True, start: str | None = None, only: bool = False,
            skip: dict | None = None) -> dict:
        """`skip`: step name -> its pass ledger row (tools/pass_ledger.py plan): not run, recorded as passed with the
        ledger's still and run, its kept values restored."""
        self.out.mkdir(parents=True, exist_ok=True)
        rep = {"id": j["id"], "save": save, "scene": j.get("scene"), "steps": [], "passed": False, "loaded": load}
        self.scene, self.save = j.get("scene"), save
        self.independent = bool(j.get("independent_steps"))
        if j.get("stills") is False:  # a state-read journey (creature checks, owner 19:05 #41): a still only on a fail
            self.stills = False
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
            self.camera = j.get("camera")
            if j.get("camera"):  # the journey's camera mode, said once at the top, applied after the load (1.15-r4-journeys)
                rep["camera"] = self._camera(j["camera"])
            for n, step in enumerate(j["steps"], 1):
                if not first < n <= last:
                    continue
                if step.get("owed"):  # not run: what it waits on is named, and the journey goes on past it
                    rep.setdefault("owed", []).append({"n": n, "name": step["name"], "why": step["owed"]})
                    print(f"  {n:2d} {step['name']:<24} OWED: {step['owed']}", flush=True)
                    continue
                if skip and step["name"] in skip:
                    row = skip[step["name"]]
                    self.kept.update(row.get("kept") or {})
                    why = f"skipped: passed {row.get('time')} on the same inputs"
                    rep["steps"].append({"n": n, "name": step["name"], "passed": True, "skipped": why,
                                         "still": row.get("still"), "run": row.get("run"), "seconds": 0.0})
                    print(f"  {n:2d} {step['name']:<24} {why}", flush=True)
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
        if self.relaunches:
            rep["relaunches"] = self.relaunches
        (self.out / "report.json").write_text(json.dumps(rep, indent=1))
        return rep

    def step(self, n: int, step: dict) -> dict:
        """One step. When `camera:` never flips in a journey of independent steps, the game process is the cause
        (measured 2026-11-04: IsPC1stPerson stays 0.00 after the bridge's ForceFirstPerson from about the 9th-12th stop of
        one process, never in a fresh one): relaunch once, put the journey's camera back, retry the step from its `do:`."""
        rec = self._step(n, step)
        if rec["passed"] or not self.independent or "the camera never became" not in rec.get("reason", ""):
            return rec
        first_reason = rec["reason"]
        print(f"  {n:2d} {step['name']:<24} camera never flipped: relaunching the game once", flush=True)
        info = {"step": step["name"], "why": "the camera never became first/third in this game process",
                "first_reason": first_reason[:300]}
        t = time.monotonic()
        try:
            info["result"] = self._relaunch(True)
            if self.camera:
                self._camera(self.camera)
        except GameDown:
            raise
        except (BridgeError, StepFailed) as e:
            info["error"] = str(e)[:300]
            rec = {"n": n, "name": step["name"], "passed": False, "seconds": round(time.monotonic() - t, 1),
                   "reason": f"the relaunch after a camera failure did not complete: {e}", "relaunch": info}
            self.relaunches.append({**info, "seconds": rec["seconds"]})
            return rec
        rec = self._step(n, step)
        info["seconds"] = round(time.monotonic() - t, 1)
        self.relaunches.append(info)
        rec["relaunch"] = info
        if not rec["passed"]:
            rec["reason"] = f"after one relaunch: {rec['reason']} (first try: {first_reason[:200]})"
        return rec

    def scan(self, n: int, step: dict, count: int, s0: pathlib.Path) -> list[dict]:
        """A scan of headings from the stand (owner 19:05 #41, 0036 amended): `count` stills at h0 + k*360/count, the
        stand's own aim k=0 (the step's still, kept under its old name and copied to -s0), the pitch kept, SCAN_SETTLE_S
        each; the stand's heading put back after. A reader names the heading that shows the subject."""
        h0 = float((self.b.call("player") or {}).get("heading_deg") or 0.0)
        out = []
        for k in range(count):
            h = (h0 + k * 360.0 / count) % 360
            path = self.out / f"{n:02d}-{step['name']}-s{k}.png"
            try:
                if k == 0:
                    shutil.copyfile(s0, path)
                else:
                    self.b.call("console", f"player.setangle z {h:.0f}")
                    time.sleep(SCAN_SETTLE_S)
                    path = self.b.screenshot(path)
                out.append({"k": k, "heading": round(h), "still": str(path)})
            except (BridgeError, OSError) as e:
                out.append({"k": k, "heading": round(h), "still": f"none: {e}"})
        if count > 1:
            try:
                self.b.call("console", f"player.setangle z {h0:.0f}")
            except BridgeError:
                pass
        return out

    def _step(self, n: int, step: dict) -> dict:
        t = time.monotonic()
        ctx = {"since": self.b.call("events")["last"], "pos": self.b.call("player")["pos"], "log_lines": {}}
        for name in {e["log"]["name"] for e in step.get("expect", []) if "log" in e}:
            ctx["log_lines"][name] = len(skse_log(self.b, name))
        rec = {"n": n, "name": step["name"], "passed": True}
        kept0 = dict(self.kept)
        retries0 = getattr(self.b, "transport_retries", 0)
        try:
            self.settle_since = ctx["since"]
            for a in (settled_do(step.get("do", [])) if self.settle_waits else step.get("do", [])):
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
        if new := {k: v for k, v in self.kept.items() if k not in kept0 or kept0[k] != v}:
            rec["kept"] = new  # what the step read and kept (e.g. the actors table), in the run's report.json
        if (self.stills or not rec["passed"]) and self.camera:   # a teleport, menu or load can undo it: re-asserted, then read
            try:
                self._camera(self.camera)
            except StepFailed as e:
                if rec["passed"]:
                    rec.update(passed=False, reason=f"StepFailed: {e}")
        if self.stills or not rec["passed"]:
            try:
                rec["still"] = str(self.b.screenshot(self.out / f"{n:02d}-{step['name']}.png"))
            except BridgeError as e:
                rec["still"] = f"none: {e}"
            if step.get("scan") and rec["passed"] and not rec["still"].startswith("none"):
                rec["scan"] = self.scan(n, step, int(step["scan"]), pathlib.Path(rec["still"]))
        rec["seconds"] = round(time.monotonic() - t, 1)
        rec["transport_retries"] = getattr(self.b, "transport_retries", 0) - retries0
        print(f"  {n:2d} {step['name']:<24} {'ok' if rec['passed'] else 'FAIL: ' + rec['reason']}", flush=True)
        return rec


SCAN_SETTLE_S = 0.8  # a scan heading's settle before its still: a turn loads nothing (2.0 cost 54 s a panel stop, r6-chain23)

MOVES = ("moveto", "coc ", "cow ", "setpos", "sw ", "fw ", "set gamehour", "setangle")


def settled_do(do: list) -> list:
    """A step's actions with each run of fixed `wait`s that follows a move (a teleport, a moveto/coc/cow/setpos console
    line, a weather or hour set) replaced by one `settle` capped at the run's total (1.15-r4-fast-loop: fixed waits
    were the largest cost per still). Waits that time an animation or an input (after a key, pad, strike) stay."""
    out, moved, run = [], False, []
    def flush():
        nonlocal run
        if run:
            total = sum(float(a["wait"]) for a in run)
            if moved:
                out.append({"settle": {"cap": min(total, 30.0), "min": min(3.0, total)}})
            else:
                out.extend(run)
            run = []
    for a in do:
        (k, v), = a.items()
        if k == "wait":
            run.append(a)
            continue
        flush()
        line = (v.get("line") if isinstance(v, dict) else v) if k == "console" else ""
        if k == "teleport" or (k == "console" and any(m in str(line) for m in MOVES)):
            moved = True
        elif k in ("camera", "hud", "settle"):
            pass  # neither a move nor a timed input: a wait after them still settles the move before
        else:
            moved = False
        out.append(a)
    flush()
    return out


def _form_id(text) -> int | None:
    """A runtime form id as an int, from `0001A26F`, `0x1A26F` or `"0001A26F"`; None for anything else."""
    t = str(text or "").strip().strip('"')
    try:
        return int(t, 16)
    except ValueError:
        return None


TALK_UNITS, TALK_WAIT_S = 110, 5.0  # 5 s: a player moveto before it may load a cell and fade
STRIKE_UNITS = 80  # inside a sword's reach
MENU_VIEWS = {"journal": "journal", "MapMenu": "chart", "system": "system", "wait": "wait"}  # a menu name and our view that stands for or over it
CLOSE_KEYS = (("B", "pad"), ("ESC", "engine"), ("TAB", "engine"), ("ESC", "os"), ("TAB", "os"))  # tried in order; pad B closes our journal (game-16, live)
AIM_EYE_Z, AIM_CHEST_Z = 110, 90
OPEN_UNITS, OPEN_Z = 100, 20  # a crate at reach, aimed at its middle (units)  # a standing human's eye and chest above the feet (units)
ACTIONS = {"pad": Runner._pad, "talk": Runner._talk, "open": Runner._open, "show": Runner._show_action, "dialogue": Runner._dialogue, "lockpick": Runner._lockpick, "strike": Runner._strike, "rest": Runner._rest, "close_menu": Runner._close_menu, "key": Runner._key, "console": Runner._console, "teleport": Runner._teleport,
           "wait": Runner._wait, "game_hours": Runner._game_hours, "call": Runner._call, "relaunch": Runner._relaunch,
           "burst": Runner._burst, "burst_fetch": Runner._burst_fetch,
           "mouse": Runner._mouse, "click": Runner._click, "wheel": Runner._wheel,
           "camera": Runner._camera, "hud": Runner._hud, "settle": Runner._settle}
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
    for _ in range(3):
        if b.call("console", "IsPC1stPerson")["output"].strip().endswith("0.00"):
            return
        try:   # the engine's own command first: the F key is a toggle, and a one_load batch leaves the last item's camera on
            b.call("camera", "third")
        except BridgeError:
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
        rep["_out"] = str(out)
        from tools import pass_ledger  # each judged step into the pass ledger (owner, 2026-11-03)
        pass_ledger.record(j, rep)
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
