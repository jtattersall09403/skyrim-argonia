"""The studio always serves the latest landed version of every place (owner, #100, 2026-11-25).

The studio reads place files from the main tree it runs in, fresh on every open (the draft bundle is rebuilt when its
key moves). This module keeps that tree level with origin/main through tooling/level_main.sh, which clears only
provably stale leftovers and never touches the owner's edits folders or his autosave (out/, ignored by git):
  - at the service's start, every minute after, and before the start sheet or a place's draft is served (at most
    once in THROTTLE_S); a level that cannot be done is said on the start sheet beside each place that is behind, and
    level_main itself tells an agent and posts or updates one owner-inbox issue;
  - when landed code the service runs (any module it loaded from the repository) changed, the service restarts
    itself under systemd, only once no request is in flight, nothing waits to be committed, no write came in the last
    QUIET_S seconds and no finalise is running, so no stroke of the owner's is ever dropped (the page also re-sends a
    write that failed)."""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
THROTTLE_S = 30
QUIET_S = 60
TICK_S = 60


def run_level(root: Path = ROOT) -> dict:
    """One automatic level of the tree (tooling/level_main.sh --auto --json); its JSON line."""
    try:
        r = subprocess.run([sys.executable, str(root / "tooling" / "level_main.py"), "--tree", str(root), "--auto",
                            "--json", "--quiet"], capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.SubprocessError) as e:
        return {"code": 1, "why": str(e), "places_behind": []}
    last = (r.stdout.strip().splitlines() or ["{}"])[-1]
    try:
        res = json.loads(last)
    except ValueError:
        res = {"code": r.returncode, "why": r.stdout[-300:] + r.stderr[-300:]}
    print(f"level: code {res.get('code')}" + (f", cleared {len(res.get('cleared') or [])}" if res.get("cleared") else "")
          + (f", {res.get('why')}" if res.get("why") else ""), flush=True)
    return res


def behind_message(title: str) -> str:
    return (f"{title} is not the latest version here: finished changes to it have landed, but unfinished files in the "
            f"studio's folder are in the way of the update. Your saves and unsaved work are safe. An agent has been "
            f"told; the studio shows the latest version by itself once the files are cleared.")


async def ensure(app, force: bool = False) -> dict:
    """Level the served tree before serving (at most once in THROTTLE_S); the last result."""
    st = app["served"]
    if not app["cfg"].level:
        return st["res"]
    async with st["lock"]:
        if force or time.time() - st["at"] >= THROTTLE_S:
            st["res"] = await asyncio.get_running_loop().run_in_executor(None, run_level)
            st["at"] = time.time()
    return st["res"]


def places_behind(app) -> set[str]:
    res = app["served"]["res"]
    return set(res.get("places_behind") or []) if res.get("code") in (1, 5) else set()


def code_files() -> dict[str, str]:
    """sha256 of every module file loaded from the repository (the code the running service is)."""
    out = {}
    for m in list(sys.modules.values()):
        f = getattr(m, "__file__", None)
        if not f:
            continue
        p = Path(f).resolve()
        if ROOT in p.parents and ".venv" not in p.parts and p.suffix == ".py":
            try:
                out[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
            except OSError:
                out[str(p)] = ""
    return out


def code_changed(snapshot: dict[str, str]) -> list[str]:
    changed = []
    for f, h in snapshot.items():
        try:
            now = hashlib.sha256(Path(f).read_bytes()).hexdigest()
        except OSError:
            now = ""
        if now != h:
            changed.append(f)
    return changed


def idle(app) -> str | None:
    """Why a restart would lose something now, or None."""
    if app["served"]["inflight"]:
        return "a request is in flight"
    if not app["commit_q"].empty() or app["pending"]:
        return "a save waits to be committed"
    if time.time() - app["served"]["last_write"] < QUIET_S:
        return "the owner wrote in the last minute"
    from tools.places.studio.server import finalising
    if any(finalising(app, p, s) for p, s in list(app["finalising"])):
        return "a finalise is running"
    if any(lk.locked() for lk in list(app["draft_locks"].values())):
        return "a draft is being rebuilt"
    return None


def restart() -> bool:
    """Ask systemd to restart this service (only when systemd runs it)."""
    if not os.environ.get("INVOCATION_ID"):
        print("code changed: not under systemd, so not restarted", flush=True)
        return False
    unit = os.environ.get("STUDIO_UNIT", "argonia-studio.service")
    print(f"code changed: restarting {unit}", flush=True)
    subprocess.Popen(["systemctl", "--user", "restart", "--no-block", unit])
    return True


async def watch(app) -> None:
    """Every TICK_S: level the tree, and restart once the code changed and nothing of the owner's is in flight."""
    snap = app["served"]["code"]
    while True:
        await ensure(app, force=True)
        for f, h in code_files().items():   # a module first imported since: as it was when it was loaded
            snap.setdefault(f, h)
        changed = code_changed(snap)
        if changed and idle(app) is None:
            print(f"landed code changed ({', '.join(Path(f).name for f in changed[:5])})", flush=True)
            if restart():
                return
        await asyncio.sleep(TICK_S)


def setup(app) -> None:
    app["served"] = {"lock": asyncio.Lock(), "at": 0.0, "res": {"code": 0, "places_behind": []}, "inflight": 0,
                     "last_write": 0.0, "code": code_files()}
