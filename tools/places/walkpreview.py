"""Rebuild a place's walking mesh from the studio: the place files with the studio's save applied (never written to
the place), planned by the build with its navmesh (the owner's walking zones, the seventeen checks' navmesh rules
and all), and the mesh exported for the studio. No plugin is written and nothing is committed: what the owner sees
is the build's mesh for the edits in hand (docs/design/place-studio.md, Walking mesh).

    python -m tools.places walkpreview <place_id> [--save autosave|<save_id>] [--out out/places]

Run by the studio under tooling/job_guard.sh as the job `walkmesh.<place_id>`, under the machine-wide heavy lock (one
place build at a time). Writes <out>/walkpreview/<place_id>/run.json {state: running|done|failed, step, steps,
started, at, save, error?, notes, problems} as it goes, and nav.json (navexport's shape, `from: "preview"`) at the
end; the place files' copy and the build's scratch are deleted when it ends."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
import traceback
from pathlib import Path

from tools.places import build as B

STEPS = ("copy", "apply", "build", "export")
STEP_WORDS = {"copy": "Copying the place", "apply": "Applying your changes", "build": "Building the walking mesh",
              "export": "Reading the mesh back"}


def run_dir(out: Path, place_id: str) -> Path:
    return out / "walkpreview" / place_id


def read_run(out: Path, place_id: str) -> dict | None:
    p = run_dir(out, place_id) / "run.json"
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return None


def _state(d: Path, **kw) -> dict:
    p = d / "run.json"
    cur = {}
    try:
        cur = json.loads(p.read_text())
    except (OSError, ValueError):
        pass
    cur.update(kw, at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    tmp = p.with_name(".run.json.tmp")
    tmp.write_text(json.dumps(cur, indent=1))
    tmp.replace(p)
    return cur


def preview(place_id: str, save_id: str, places: Path, out: Path) -> dict:
    from tools.places import edits, navexport
    from tools.places.heavy_lock import heavy_lock
    d = run_dir(out, place_id)
    d.mkdir(parents=True, exist_ok=True)
    work = d / "work"
    shutil.rmtree(work, ignore_errors=True)
    _state(d, state="running", step="copy", steps=list(STEPS), started=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           save=save_id, error=None, notes=[], problems=[], words=STEP_WORDS["copy"])
    try:
        root = work / "places"
        shutil.copytree(places / place_id, root / place_id, ignore=shutil.ignore_patterns("edits"))
        if (places / "formid_blocks.json").exists():
            shutil.copy2(places / "formid_blocks.json", root / "formid_blocks.json")
        _state(d, step="apply", words=STEP_WORDS["apply"])
        sp = (out / "autosave" / f"{place_id}.json") if save_id == "autosave" else (places / place_id / "edits" / f"{save_id}.json")
        save = json.loads(sp.read_text()) if sp.exists() else None
        if save and save.get("ops") and save_id not in json.loads((root / place_id / "place.json").read_text()).get("saves_applied", []):
            files = edits.apply_save(edits.load_place(root / place_id), save, edits.bundle_source(out / "bundles"))
            edits.write_place(root / place_id, files, work / "sources")
        _state(d, step="build", words=STEP_WORDS["build"])
        B.PROBLEMS.clear()
        B.build_tool()
        with heavy_lock():
            plan = B.plan_place(place_id, root / place_id, work / "out", no_navmesh=False)
        problems = list(B.PROBLEMS)
        _state(d, step="export", words=STEP_WORDS["export"])
        walk_notes = [n for n in plan.get("notes", []) if n.startswith("walking zone")]
        navexport.export_plan(plan, d / "nav.json", time.time(), {"save": save_id, "notes": walk_notes})
        return _state(d, state="done", step="export", words="Done", notes=walk_notes, problems=problems[:40])
    except BaseException as e:   # noqa: BLE001  the page says what went wrong in plain words; the log has the trace
        traceback.print_exc()
        msg = str(e) if isinstance(e, SystemExit) else f"{type(e).__name__}: {e}"
        _state(d, state="failed", error=msg[:600])
        raise
    finally:
        shutil.rmtree(work, ignore_errors=True)


def start(place_id: str, save_id: str, repo: Path) -> str:
    """Launch a preview under tooling/job_guard.sh; returns the job's name."""
    import subprocess
    name = f"walkmesh.{place_id}"
    py = os.environ.get("PLACES_PY") or sys.executable
    subprocess.Popen([str(repo / "tooling/job_guard.sh"), "run", name, "--", py, "-m", "tools.places", "walkpreview", place_id,
                      "--save", save_id], cwd=repo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    return name


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places walkpreview")
    ap.add_argument("place_id")
    ap.add_argument("--save", default="autosave")
    ap.add_argument("--places-dir", default=str(B.PLACES))
    ap.add_argument("--out", default=str(B.OUT))
    a = ap.parse_args(argv)
    st = preview(a.place_id, a.save, Path(a.places_dir), Path(a.out))
    print(json.dumps({k: st.get(k) for k in ("state", "notes", "problems")}))
    return 0
