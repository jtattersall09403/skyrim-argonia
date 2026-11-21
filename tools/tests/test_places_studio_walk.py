"""The studio's walking-mesh calls (tools/places/studio/walk_api.py): the view's state (the checks' findings, when the
mesh was built, a rebuild's progress), the mesh a studio rebuild made served over the build's when newer, and a
rebuild started as a job, refused politely while one runs or another place build holds the heavy lock."""
import asyncio
import subprocess
import sys
import json
import os
import time

import pytest

aiohttp = pytest.importorskip("aiohttp")
from aiohttp.test_utils import TestClient, TestServer  # noqa: E402


@pytest.fixture
def env(tmp_path, monkeypatch):
    out, places = tmp_path / "out", tmp_path / "places"
    (places / "fxplace").mkdir(parents=True)
    (places / "fxplace" / "place.json").write_text(json.dumps({"place_id": "fxplace", "source_id": "fx.village", "similar": []}))
    (out / "plugin").mkdir(parents=True)
    (out / "shards" / "fxplace").mkdir(parents=True)
    (out / "plugin" / "build.json").write_text("{}")
    (out / "shards" / "fxplace" / "plan.json").write_text("{}")
    (out / "shards" / "fxplace" / "check.json").write_text(json.dumps({"results": {
        "doors": {"failures": ["door fx.1: its arrival point [10, 20, 30] is on no navmesh (facing a wall?)"]},
        "overlap": {"failures": ["fx.2 stands inside fx.3"]},
        "streets": {"failures": ["street fx.p point [100, 200, 5] is off the built walkable network"]}}}))
    for k, v in {"PLACES_OUT": out, "PLACES_DIR": places, "STUDIO_COMMIT": "0", "STUDIO_BUCKET_SYNC": "0", "STUDIO_AWAKE": "0",
                 "STUDIO_ZCACHE": tmp_path / "z", "JOBS_DIR": tmp_path / "jobs",
                 "ARGONIA_PLACES_LOCK_FILE": tmp_path / "heavy.lock"}.items():
        monkeypatch.setenv(k, str(v))
    (tmp_path / "jobs").mkdir()
    return tmp_path


def run(body, started=None):
    from tools.places.studio.server import make_app

    async def go():
        app = make_app()
        app["walk_start"] = lambda pid, sid: (started.append((pid, sid)) if started is not None else None) or f"walkmesh.{pid}"
        async with TestClient(TestServer(app)) as c:
            await body(c)
    asyncio.run(go())


def test_state_pins_only_the_walking_checks_and_says_when_built(env):
    async def body(c):
        r = await c.get("/api/place/fxplace/walkmesh")
        d = await r.json()
        assert r.status == 200
        assert set(d["check"]["results"]) == {"doors", "navmesh", "streets", "people"}
        assert d["check"]["results"]["doors"]["failures"][0].startswith("door fx.1")
        assert d["run"] is None and d["busy"] is None and d["files_at"]
    run(body)


def test_a_studio_rebuild_newer_than_the_build_is_the_mesh_served(env):
    from tools.places.studio import walk_api
    out = env / "out"
    pv = out / "walkpreview" / "fxplace"
    pv.mkdir(parents=True)
    (pv / "nav.json").write_text(json.dumps({"from": "preview", "spaces": {}}))
    later = time.time() + 10
    os.utime(pv / "nav.json", (later, later))
    assert walk_api.nav_path("fxplace", out) == pv / "nav.json"
    st = walk_api.state(type("C", (), {"out": out, "places": env / "places", "jobs": env / "jobs"})(), "fxplace")
    assert st["nav"]["from"] == "preview"
    # a place build after it wins again
    os.utime(out / "plugin" / "build.json", (later + 10, later + 10))
    os.utime(out / "shards" / "fxplace" / "plan.json", (later + 10, later + 10))
    from tools.places import navexport
    navexport._failed.clear()
    assert walk_api.nav_path("fxplace", out) != pv / "nav.json"


def test_rebuild_starts_once_and_refuses_politely(env):
    started = []

    async def body(c):
        r = await c.post("/api/place/fxplace/walkmesh/rebuild", json={"save_id": "autosave"})
        assert r.status == 202 and (await r.json())["job"] == "walkmesh.fxplace"
        assert started == [("fxplace", "autosave")]
        d = await (await c.get("/api/place/fxplace/walkmesh")).json()
        assert d["run"]["state"] == "starting"
        r = await c.post("/api/place/fxplace/walkmesh/rebuild", json={"save_id": "autosave"})
        assert r.status == 409 and "already" in (await r.json())["error"]
    run(body, started)


def test_rebuild_waits_for_another_place_build(env):
    lock = env / "heavy.lock"
    lock.write_text("pid 1 cwd /x since 10:00:00")
    # the holder is another process, as a place build is
    holder = subprocess.Popen([sys.executable, "-c", "import fcntl, sys, time; f = open(sys.argv[1]); fcntl.flock(f, fcntl.LOCK_EX); "
                               "print('held', flush=True); time.sleep(30)", str(lock)], stdout=subprocess.PIPE, text=True)
    try:
        assert holder.stdout.readline().strip() == "held"

        async def body(c):
            r = await c.post("/api/place/fxplace/walkmesh/rebuild", json={})
            e = (await r.json())["error"]
            assert r.status == 409 and "Another place build is running (since 10:00:00)" in e and "nothing has been lost" in e
            d = await (await c.get("/api/place/fxplace/walkmesh")).json()
            assert d["busy"].startswith("Another place build")
        run(body)
    finally:
        holder.kill()
        holder.wait()


def test_rebuild_rejects_a_bad_place(env):
    async def body(c):
        assert (await c.post("/api/place/nowhere/walkmesh/rebuild", json={})).status == 404
        assert (await c.post("/api/place/fxplace/walkmesh/rebuild", json={"save_id": "../x"})).status == 400
    run(body)
