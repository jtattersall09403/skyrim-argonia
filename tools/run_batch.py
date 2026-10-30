#!/usr/bin/env python3
"""One game slot, one batch (owner, 2026-10-30): many journeys and scenes in sequence under ONE `job_guard --gpu`
job, keeping going past failures. DEV ONLY: it drives the running game through tools/bridge.py.

    tooling/job_guard.sh run --gpu batch -- python3 tools/run_batch.py tests/journeys/batches/game-12.yaml
    python3 tools/run_batch.py --dry tests/journeys/batches/game-12.yaml      # validate every item; no game
    python3 tools/run_batch.py smoke croc-den:2 scene:world-sample-03-corner  # an ad hoc batch, id "adhoc"

A batch file:

    id: game-12
    relaunch_mb: 6000          # relaunch the game before an item when SkyrimSE's private memory is past this
    relaunch_every: 0          # and/or every N items (0: never on count alone)
    items:
      - smoke                              # a journey (tests/journeys/<id>.yaml), run once
      - {journey: croc-den, runs: 2}       # run twice
      - {journey: lf83-endings, chain: true}   # no save load: the scene is applied over the last item's game
      - {scene: world-sample-03-corner}    # a scene alone: loaded, `bat`, a still (passes when it applies)

`chain: true` saves a full save load (about 7 s, and the memory it grows) when the item follows one of the same
scene family and needs nothing the base save resets; it is ignored after a relaunch or a failed item.

A crash is a failure: the item is recorded with its crash, the game is relaunched (bridge `launch`) and the batch
goes on. Out: out/batch/<id>/<stamp>/summary.json, rewritten after every item: per item pass/fail, the failing step
and its reason, seconds (and the scene apply's), private MB before and after, and whether the game was relaunched;
the totals and the time per step class (launch, scene apply, steps). Each journey's own report sits beside it.
Exit 0 every item passed, 1 any failed, 2 the game could not be launched again.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import time

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from tools import run_journey as rj  # noqa: E402
from tools.bridge import Bridge, BridgeError  # noqa: E402

JOURNEYS = REPO / "tests" / "journeys"
RELAUNCH_MB = 6000  # game-10's long run crashed after ~230 MB per loop; a relaunch costs ~70 s
LAUNCH_TRIES = 2


def parse_items(spec: list) -> list[dict]:
    """Each item as {kind: journey|scene, id, runs, chain}."""
    items = []
    for it in spec:
        if isinstance(it, str):
            kind, _, rest = it.partition(":") if it.startswith("scene:") else ("journey", "", it)
            name, _, runs = rest.partition(":")
            it = {kind: name, **({"runs": int(runs)} if runs else {})}
        if not isinstance(it, dict) or len({"journey", "scene"} & set(it)) != 1:
            raise SystemExit(f"batch item {it!r}: one of journey or scene")
        unknown = set(it) - {"journey", "scene", "runs", "chain", "save"}
        if unknown:
            raise SystemExit(f"batch item {it!r}: unknown keys {sorted(unknown)}")
        kind = "journey" if "journey" in it else "scene"
        items.append({"kind": kind, "id": str(it[kind]), "runs": int(it.get("runs", 1)), "chain": bool(it.get("chain")),
                      "save": it.get("save")})
    return items


def load_batch(argv_items: list[str]) -> dict:
    if len(argv_items) == 1 and argv_items[0].endswith((".yaml", ".yml")):
        import yaml
        b = yaml.safe_load(pathlib.Path(argv_items[0]).read_text())
        if not isinstance(b, dict) or "items" not in b:
            raise SystemExit(f"{argv_items[0]}: a batch has `items`")
        return {"id": b.get("id", pathlib.Path(argv_items[0]).stem), "items": parse_items(b["items"]),
                "relaunch_mb": float(b.get("relaunch_mb", RELAUNCH_MB)), "relaunch_every": int(b.get("relaunch_every", 0))}
    return {"id": "adhoc", "items": parse_items(argv_items), "relaunch_mb": RELAUNCH_MB, "relaunch_every": 0}


def dry(batch: dict) -> list[str]:
    lines = []
    for it in batch["items"]:
        if it["kind"] == "journey":
            j = rj.load_journey(JOURNEYS / f"{it['id']}.yaml")
            if "soak" in j:
                raise SystemExit(f"{it['id']}: a soak is not a batch item")
            lines.append(rj.dry(JOURNEYS / f"{it['id']}.yaml") + (f" x{it['runs']}" if it["runs"] > 1 else ""))
        elif not (rj.SCENES / f"{it['id']}.txt").is_file():
            raise SystemExit(f"no scene tests/scenes/{it['id']}.txt")
        else:
            lines.append(f"scene {it['id']}: ok")
    return lines


def private_mb(b) -> float | None:
    """SkyrimSE's private bytes in MB (the growth that crashed the long run), None when it is not running."""
    try:
        out = b.machine.ps("$p = Get-Process SkyrimSE -EA SilentlyContinue; if ($p) { 'MB ' + [int]($p.PrivateMemorySize64/1MB) } else { 'MB none' }",
                           timeout=90)
    except BridgeError:
        return None
    m = re.findall(r"MB (\d+)", out)
    return float(m[-1]) if m else None


class Batch:
    def __init__(self, bridge, batch: dict, out: pathlib.Path, stills: bool = True, clock=time.monotonic):
        self.b, self.batch, self.out, self.stills, self.clock = bridge, batch, out, stills, clock
        self.sent: dict = {}  # scenes already on the machine (run_journey's Runner skips an unchanged re-put)
        self.summary = {"id": batch["id"], "out": str(out), "items": [], "launches": [], "passed": False}
        self.since_launch = 0

    def write(self):
        self.out.mkdir(parents=True, exist_ok=True)
        (self.out / "summary.json").write_text(json.dumps(self.summary, indent=1))

    def launch(self, why: str) -> bool:
        """Relaunch to the main menu (the next item loads its save); False when it fails twice."""
        for attempt in range(1, LAUNCH_TRIES + 1):
            t = self.clock()
            try:
                self.b.launch()
                self.summary["launches"].append({"why": why, "seconds": round(self.clock() - t, 1), "attempt": attempt})
                self.since_launch = 0
                return True
            except BridgeError as e:
                self.summary["launches"].append({"why": why, "seconds": round(self.clock() - t, 1), "attempt": attempt,
                                                 "error": str(e)[-400:]})
        return False

    def need_relaunch(self, mb: float | None) -> str | None:
        if mb is None:
            return "the game is not running"
        if mb > self.batch["relaunch_mb"]:
            return f"private memory {mb:.0f} MB > {self.batch['relaunch_mb']:.0f}"
        n = self.batch["relaunch_every"]
        if n and self.since_launch >= n:
            return f"{n} items since the last launch"
        return None

    def run_one(self, it: dict, run: int, load: bool) -> dict:
        stamp = time.strftime("%Y%m%dT%H%M%S")
        out = self.out / f"{len(self.summary['items']) + 1:02d}-{it['id']}-{run}-{stamp}"
        runner = rj.Runner(self.b, out, stills=self.stills, sent=self.sent)
        if it["kind"] == "journey":
            j = rj.load_journey(JOURNEYS / f"{it['id']}.yaml")
            save = it["save"] or j.get("save") or rj.BASE_SAVE
        else:  # a scene alone: applied, one still; it passes when the bridge and the game took it
            j = {"id": it["id"], "scene": it["id"], "steps": [{"name": "applied", "do": [{"wait": 2}]}]}
            save = it["save"] or rj.BASE_SAVE
        rep = runner.run(j, save, load=load)
        rep["_out"] = str(out)
        return rep

    def run(self) -> dict:
        t0, prev_ok = self.clock(), False
        for it in self.batch["items"]:
            for run in range(1, it["runs"] + 1):
                mb = private_mb(self.b)
                why = self.need_relaunch(mb)
                relaunched = False
                if why:
                    if not self.launch(why):
                        self.summary["aborted"] = f"the game could not be launched ({why})"
                        self.summary["seconds"] = round(self.clock() - t0, 1)
                        self.write()
                        return self.summary
                    relaunched, prev_ok = True, False
                load = not (it["chain"] and prev_ok and run == 1)
                rep = self.run_one(it, run, load)
                bad = next((s for s in rep["steps"] if not s["passed"]), None)
                rec = {"kind": it["kind"], "id": it["id"], "run": run, "passed": rep["passed"],
                       "failed_at": rep.get("failed_at"),
                       "reason": (bad or {}).get("reason") or rep.get("error") or rep.get("crash"),
                       "crash": bool(rep.get("crash")), "seconds": rep["seconds"], "scene_s": rep.get("scene_s"),
                       "steps_s": round(sum(s.get("seconds", 0) for s in rep["steps"]), 1),
                       "loaded": load, "relaunched_before": relaunched, "mb_before": mb, "mb_after": private_mb(self.b),
                       "owed": [o["name"] for o in rep.get("owed", [])], "report": rep["_out"]}
                self.summary["items"].append(rec)
                self.since_launch += 1
                prev_ok = rep["passed"]
                print(f"{it['id']} run {run}: {'PASS' if rep['passed'] else 'CRASH' if rec['crash'] else 'FAIL'} "
                      f"in {rep['seconds']} s, {rec['mb_before']} -> {rec['mb_after']} MB"
                      + ("" if rep["passed"] else f" at {rec['failed_at']}: {rec['reason']}"), flush=True)
                self.totals(t0)
                self.write()
        self.totals(t0)
        self.write()
        return self.summary

    def totals(self, t0):
        items, s = self.summary["items"], self.summary
        s["seconds"] = round(self.clock() - t0, 1)
        s["passed_n"] = sum(1 for i in items if i["passed"])
        s["failed"] = [f"{i['id']}#{i['run']}: {i['failed_at']}: {i['reason']}" for i in items if not i["passed"]]
        s["passed"] = bool(items) and not s["failed"] and "aborted" not in s
        s["step_classes_s"] = {"launch": round(sum(x["seconds"] for x in s["launches"]), 1),
                               "scene_apply": round(sum(i["scene_s"] or 0 for i in items), 1),
                               "steps": round(sum(i["steps_s"] for i in items), 1)}
        mbs = [i["mb_after"] for i in items if i["mb_after"]]
        s["mb_peak"] = max(mbs) if mbs else None


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("items", nargs="+", help="a batch .yaml, or journeys (id[:runs]) and scene:<id>")
    p.add_argument("--dry", action="store_true", help="validate every item and its scene; no game")
    p.add_argument("--no-stills", action="store_true", help="stills only for a failed step")
    p.add_argument("--relaunch-mb", type=float, default=None)
    a = p.parse_args(argv)
    batch = load_batch(a.items)
    if a.relaunch_mb:
        batch["relaunch_mb"] = a.relaunch_mb
    if a.dry:
        for line in dry(batch):
            print(line)
        return 0
    dry(batch)  # a bad item fails before the game is touched
    out = REPO / "out" / "batch" / batch["id"] / time.strftime("%Y%m%dT%H%M%S")
    s = Batch(Bridge(), batch, out, stills=not a.no_stills).run()
    print(f"{batch['id']}: {s['passed_n']}/{len(s['items'])} passed in {s['seconds']} s; {out / 'summary.json'}")
    for f in s["failed"]:
        print("  FAIL " + f)
    if s.get("aborted"):
        print("  ABORTED: " + s["aborted"])
        return 2
    return 0 if s["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
