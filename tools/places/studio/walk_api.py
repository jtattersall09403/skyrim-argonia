"""The studio's walking-mesh calls (docs/design/place-studio.md, Walking mesh): what the Walking mesh view needs beside
the mesh itself (the checks' findings, when the mesh was built against when the place last changed, a rebuild's
progress) and the rebuild itself, run as a job (tools/places/walkpreview.py).

    GET  /api/place/<id>/walkmesh           {nav: {from, built_at, save} | null, files_at, check: {at, results} | null,
                                             run: walkpreview's run.json | null, busy: null | plain words}
    POST /api/place/<id>/walkmesh/rebuild   {save_id} -> 202 {job}; 409 {error} while a build runs"""
from __future__ import annotations

import asyncio
import datetime
import fcntl
import json
import os
from pathlib import Path

from aiohttp import web

from tools.places import navexport, walkpreview
from tools.places.heavy_lock import lock_path

ROOT = Path(__file__).resolve().parents[3]
CHECKS = ("doors", "navmesh", "streets", "people")     # the checks whose findings the Walking mesh view pins


def _iso(t: float | None) -> str | None:
    return None if t is None else datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _built(out: Path, pid: str) -> float | None:
    bj, plan = out / "plugin" / "build.json", out / "shards" / pid / "plan.json"
    return max(bj.stat().st_mtime, plan.stat().st_mtime) if bj.exists() and plan.exists() else None


def nav_path(pid: str, out: Path) -> Path | None:
    """The walking mesh the studio draws: a preview rebuilt from the studio when it is newer than the place's last
    build, else the build's own export (navexport.current)."""
    pv = walkpreview.run_dir(out, pid) / "nav.json"
    built = _built(out, pid)
    if pv.exists() and (built is None or pv.stat().st_mtime > built):
        return pv
    return navexport.current(pid, out)


def files_at(places: Path, pid: str) -> float | None:
    """When the place files last changed (its edits folder aside: saves and notes are not the place yet)."""
    d = places / pid
    ts = [p.stat().st_mtime for p in d.rglob("*") if p.is_file() and "edits" not in p.relative_to(d).parts and p.name != "formids.json"]
    return max(ts) if ts else None


def heavy_busy() -> str | None:
    """Plain words when another place build holds the machine-wide lock, else None (the lock is not taken)."""
    p = lock_path()
    if not p.exists():
        return None
    fd = os.open(p, os.O_RDONLY)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError:
            holder = os.pread(fd, 400, 0).decode(errors="replace").strip()
            since = holder.split("since ")[-1] if "since " in holder else None
            return f"Another place build is running{f' (since {since})' if since else ''}."
        fcntl.flock(fd, fcntl.LOCK_UN)
        return None
    finally:
        os.close(fd)


def _job_alive(jobs: Path, name: str) -> bool:
    pidf = jobs / f"{name}.pid"
    if not pidf.exists() or (jobs / f"{name}.rc").exists():
        return False
    try:
        os.kill(int(pidf.read_text().split()[0]), 0)
        return True
    except (OSError, ValueError):
        return False


def _check(out: Path, pid: str) -> dict | None:
    p = out / "shards" / pid / "check.json"
    try:
        d = json.loads(p.read_text())
    except (OSError, ValueError):
        return None
    res = d.get("results") or {}
    return {"at": _iso(p.stat().st_mtime), "results": {k: {"failures": (res.get(k) or {}).get("failures", [])} for k in CHECKS}}


def state(cfg, pid: str) -> dict:
    out = cfg.out
    np_ = nav_path(pid, out)
    nav = None
    if np_:
        pv = np_ == walkpreview.run_dir(out, pid) / "nav.json"
        nav = {"from": "preview" if pv else "build", "built_at": _iso(np_.stat().st_mtime if pv else _built(out, pid))}
    run = walkpreview.read_run(out, pid)
    if run and run.get("state") in ("starting", "running") and not _job_alive(cfg.jobs, f"walkmesh.{pid}"):
        started = run.get("at")
        stale = started and (datetime.datetime.now(datetime.timezone.utc)
                             - datetime.datetime.strptime(started, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)).total_seconds() > 60
        if stale:   # the job ended without a word (killed, the machine stopped): said once as a failure
            run = dict(run, state="failed", error=run.get("error") or "the rebuild stopped before it finished")
    return {"nav": nav, "files_at": _iso(files_at(cfg.places, pid)), "check": _check(out, pid), "run": run,
            "busy": heavy_busy()}


async def get_walkmesh(req: web.Request) -> web.Response:
    from tools.places.studio.server import PLACE_ID, jerr, jok
    pid = req.match_info["place_id"]
    if not PLACE_ID.match(pid):
        return jerr(400, "bad place id")
    return jok(await asyncio.get_running_loop().run_in_executor(None, state, req.app["cfg"], pid))


async def post_rebuild(req: web.Request) -> web.Response:
    from tools.places.studio.server import AUTOSAVE, PLACE_ID, SAVE_ID, jerr, jok, json_capped
    pid, cfg = req.match_info["place_id"], req.app["cfg"]
    body = await json_capped(req, 4096)
    sid = (body.get("save_id") if isinstance(body, dict) else None) or AUTOSAVE
    if not PLACE_ID.match(pid) or not (sid == AUTOSAVE or SAVE_ID.match(sid)):
        return jerr(400, "bad place or save id")
    from tools.places import variant
    if variant.is_variant(pid):
        return jerr(409, "A variant's walking mesh is not rebuilt from the studio: it is built when the variant is "
                         "chosen as the place. Your walking zones are kept with it.")
    if not (cfg.places / pid / "place.json").exists():
        return jerr(404, "no such place")
    async with req.app["walk_lock"]:
        run = walkpreview.read_run(cfg.out, pid)
        if _job_alive(cfg.jobs, f"walkmesh.{pid}") or (run and run.get("state") == "starting"):
            return jerr(409, "The walking mesh of this place is being rebuilt already. Its progress is shown here.")
        busy = heavy_busy()
        if busy:
            return jerr(409, f"{busy} The walking mesh can be rebuilt when it ends; nothing has been lost.")
        d = walkpreview.run_dir(cfg.out, pid)
        d.mkdir(parents=True, exist_ok=True)
        (d / "run.json").write_text(json.dumps({"state": "starting", "step": "copy", "steps": list(walkpreview.STEPS),
                                                "words": "Starting", "save": sid,
                                                "at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}))
        job = await asyncio.get_running_loop().run_in_executor(None, req.app["walk_start"], pid, sid)
    return jok({"job": job}, status=202)


def add_routes(app: web.Application) -> None:
    app["walk_lock"] = asyncio.Lock()
    app.setdefault("walk_start", lambda pid, sid: walkpreview.start(pid, sid, ROOT, app["cfg"].out, app["cfg"].places))
    app.router.add_get("/api/place/{place_id}/walkmesh", get_walkmesh)
    app.router.add_post("/api/place/{place_id}/walkmesh/rebuild", post_rebuild)
