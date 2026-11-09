"""The studio server against a fixture bundle: every endpoint, saves round trip and version conflict, compression,
ETag and range, a concurrent load burst, and search quality on plain-English queries."""
import asyncio
import json
import shutil
import time
from pathlib import Path

import pytest

aiohttp = pytest.importorskip("aiohttp")
pytest.importorskip("onnxruntime")
from aiohttp.test_utils import TestClient, TestServer  # noqa: E402

FIX = Path(__file__).parent / "fixtures" / "places"
MODEL_DIR = Path.home() / ".argonia" / "models" / "bge-small-en-v1.5"


@pytest.fixture(scope="module")
def env(tmp_path_factory):
    if not (MODEL_DIR / "model_quantized.onnx").exists():
        pytest.skip("search model not fetched (python -m tools.places search build fetches it)")
    t = tmp_path_factory.mktemp("studio")
    out, places, web = t / "out", t / "places", t / "web"
    b = out / "bundles" / "src.fx.village"
    (b / "spaces" / "exterior").mkdir(parents=True)
    shutil.copy(FIX / "bases.jsonl", b / "bases.jsonl")
    (b / "bundle.json").write_text(json.dumps({"bundle_id": "src.fx.village", "kind": "source", "stamp": {"tool": "t"}}))
    (b / "spaces" / "exterior" / "refs.jsonl").write_text(
        "".join(json.dumps({"id": f"r{i}", "base": "Fixture.esm:000800", "kind": "static", "pos": [i, 0, 0],
                            "rot": [0, 0, 0], "scale": 1.0, "layer": "place"}) + "\n" for i in range(3000)))
    d = out / "bundles" / "draft.fxplace"
    d.mkdir(parents=True)
    (d / "bundle.json").write_text(json.dumps({"bundle_id": "draft.fxplace", "kind": "draft", "stamp": {"tool": "d"}}))
    (places / "fxplace").mkdir(parents=True)
    (places / "fxplace" / "place.json").write_text(json.dumps({"place_id": "fxplace", "source_id": "fx.village",
                                                                "similar": []}))
    web.mkdir()
    (web / "index.html").write_text("<!doctype html><title>Place studio</title>" + "<p>studio</p>" * 200)
    mp = pytest.MonkeyPatch()
    for k, v in {"PLACES_OUT": out, "PLACES_DIR": places, "STUDIO_WEB": web, "STUDIO_COMMIT": "0",
                 "STUDIO_BUCKET_SYNC": "0", "STUDIO_AWAKE": "0", "STUDIO_ZCACHE": t / "z", "JOBS_DIR": t / "jobs"}.items():
        mp.setenv(k, str(v))
    from tools.places.search.index import Index
    Index._open.clear()
    Index.open(out / "search").update(FIX / "bases.jsonl")
    yield t
    mp.undo()


def run(env, body):
    from tools.places.studio.server import make_app

    async def go():
        async with TestClient(TestServer(make_app())) as c:
            await body(c)
    asyncio.run(go())


def test_places_bundle_and_web(env):
    async def body(c):
        r = await c.get("/api/places")
        rows = await r.json()
        assert [p["place_id"] for p in rows] == ["fxplace"] and rows[0]["source_id"] == "fx.village"
        r = await c.get("/api/bundle/src.fx.village/spaces/exterior/refs.jsonl", headers={"Accept-Encoding": "br"})
        assert r.status == 200 and r.headers["Content-Encoding"] == "br"
        text = await r.text()
        assert text.count("\n") == 3000
        etag = r.headers["ETag"]
        r = await c.get("/api/bundle/src.fx.village/spaces/exterior/refs.jsonl",
                        headers={"Accept-Encoding": "br", "If-None-Match": etag})
        assert r.status == 304
        r = await c.get("/api/bundle/src.fx.village/bases.jsonl", headers={"Range": "bytes=0-9"})
        assert r.status == 206 and len(await r.read()) == 10
        assert (await c.get("/api/bundle/src.fx.village/../../x")).status in (400, 404)
        r = await c.get("/", headers={"Accept-Encoding": "gzip"})
        assert r.status == 200 and "Place studio" in await r.text()
    run(env, body)


def test_saves_round_trip_and_conflict(env):
    async def body(c):
        ops = [{"n": 1, "at": "t", "op": "ref.remove", "space": "exterior", "call": "fault", "id": "r1", "before": {}}]
        r = await c.put("/api/place/fxplace/saves/first-pass", json={"name": "First pass", "ops": ops, "rev": 0})
        assert r.status == 200 and (await r.json())["rev"] == 1
        r = await c.put("/api/place/fxplace/saves/first-pass", json={"name": "First pass", "ops": ops * 2, "rev": 1})
        assert (await r.json())["rev"] == 2
        r = await c.put("/api/place/fxplace/saves/first-pass", json={"name": "stale tab", "ops": [], "rev": 1})
        assert r.status == 409 and (await r.json())["current"]["rev"] == 2
        r = await c.put("/api/place/fxplace/saves/autosave", json={"ops": ops, "rev": 0})
        assert r.status == 200
        saves = await (await c.get("/api/place/fxplace/saves")).json()
        assert {s["save_id"] for s in saves} == {"first-pass", "autosave"}
        assert (env / "places" / "fxplace" / "edits" / "first-pass.json").exists()
        assert (env / "out" / "autosave" / "fxplace.json").exists()
        assert (await c.put("/api/place/fxplace/saves/Bad Id", json={"ops": []})).status in (400, 404)
    run(env, body)

    async def after_restart(c):
        s = await (await c.get("/api/place/fxplace/saves/first-pass")).json()
        assert s["rev"] == 2 and len(s["ops"]) == 2 and s["name"] == "First pass"
    run(env, after_restart)


def test_status_seat_heartbeat_assets_runs(env):
    async def body(c):
        s = await (await c.get("/api/status")).json()
        assert {"ground_sha", "deployed_sha", "match", "versions"} <= set(s)
        assert (await c.get("/api/place/fxplace/seat?x=1")).status == 400
        assert (await c.get("/api/place/fxplace/seat?x=1&y=2")).status in (200, 404, 503)
        assert (await (await c.post("/api/heartbeat")).json())["disabled"] is True
        assert (await c.get("/api/asset/mesh")).status == 400
        assert (await c.get("/api/place/fxplace/runs/nope")).status == 404
        assert (await c.post("/api/place/fxplace/finalise", json={"save_id": "missing"})).status == 404
    run(env, body)


def test_search_quality_and_speed(env):
    want = {"wooden walkway": "Boardwalk", "fishing net": "FishingNet", "argonian hut door": "HutDoor",
            "lantern": "Lantern"}

    async def body(c):
        for q, frag in want.items():
            t = time.perf_counter()
            r = await (await c.get("/api/search", params={"q": q, "scope": "all", "limit": "3"})).json()
            ms = (time.perf_counter() - t) * 1000
            top = [h["edid"] for h in r["results"]]
            assert any(frag in e for e in top[:2]), (q, top)
            assert ms < 300, (q, ms)
        r = await (await c.get("/api/search", params={"q": "FxCanoe01"})).json()
        assert r["results"][0]["edid"] == "FxCanoe01"
        r = await (await c.get("/api/search", params={"q": "house", "kind": "door"})).json()
        assert r["results"] and all(h["kind"] == "door" for h in r["results"])
        r = await (await c.get("/api/search", params={"q": "nord house", "scope": "source",
                                                      "source_id": "fx.village"})).json()
        assert r["results"][0]["nordic"] is True and r["results"][0]["thumb"].startswith("/api/asset/thumb")
        assert (await c.get("/api/search", params={"q": "x", "scope": "source"})).status == 400
    run(env, body)


def test_load_burst(env):
    async def body(c):
        await c.get("/api/search", params={"q": "warm up"})
        t = time.perf_counter()
        reqs = [c.get("/api/places") for _ in range(100)] + [c.get("/api/search", params={"q": "rope"}) for _ in range(50)]
        res = await asyncio.gather(*reqs)
        assert all(r.status == 200 for r in res)
        assert time.perf_counter() - t < 10
    run(env, body)
