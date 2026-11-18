"""The studio's offline mode, server side and the device's own arithmetic (docs/design/place-studio.md, Offline):
the manifest of everything a place needs, a tablet's save sent twice stored once, a tablet's note sent twice kept
once, and the seat answer worked out in the browser equal to tools/places/seat.py's on sample points."""
import asyncio
import json
import random
import shutil
import struct
import subprocess
from array import array
from pathlib import Path

import pytest

aiohttp = pytest.importorskip("aiohttp")
from aiohttp.test_utils import TestClient, TestServer  # noqa: E402

from tools.places import seat  # noqa: E402
from tools.places.studio import offline  # noqa: E402

WEB = Path(__file__).resolve().parents[1] / "places" / "studio" / "web"


def glb(uri: str) -> bytes:
    g = {"asset": {"version": "2.0"}, "images": [{"uri": uri}, {"uri": "/api/asset/tex?path=textures/a_n.dds&size=256"}],
         "textures": [{"source": 0}, {"source": 1}],
         "materials": [{"pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}, "normalTexture": {"index": 1}}]}
    j = json.dumps(g).encode()
    j += b" " * (-len(j) % 4)
    return b"glTF" + struct.pack("<II", 2, 20 + len(j)) + struct.pack("<II", len(j), 0x4E4F534A) + j


def jl(p: Path, rows):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))


@pytest.fixture()
def env(tmp_path, monkeypatch):
    out, places, web, cache = tmp_path / "out", tmp_path / "places", tmp_path / "web", tmp_path / "cache"
    (places / "fx" ).mkdir(parents=True)
    (places / "fx" / "place.json").write_text(json.dumps({"place_id": "fx", "source_id": "fx.src", "similar": []}))
    for sub in ("js", "test", "dev"):
        (web / sub).mkdir(parents=True)
    (web / "index.html").write_text("<!doctype html><title>Place Studio</title>")
    (web / "js" / "main.js").write_text("// main")
    (web / "test" / "t.mjs").write_text("// a test")
    (web / "dev" / "d.py").write_text("# dev")
    bases = [{"key": "A:000801", "model": "meshes/Hut.nif", "kind": "building"},
             {"key": "A:000802", "model": "meshes/tree.nif", "kind": "tree"}]
    for bid, kind in (("ground.fx", "ground"), ("draft.fx", "draft"), ("src.fx.src", "source")):
        b = out / "bundles" / bid
        spaces = ["exterior"] + (["Hall 1"] if bid != "ground.fx" else [])
        (b / "spaces").mkdir(parents=True)
        (b / "bundle.json").write_text(json.dumps({"bundle_id": bid, "kind": kind, "spaces": spaces, "stamp": {"key": f"k-{bid}"}}))
        jl(b / "bases.jsonl", bases)
        jl(b / "spaces" / "exterior" / "refs.jsonl", [{"id": "r1", "base": "A:000801", "kind": "building"},
                                                      {"id": "r2", "base": "A:000802", "kind": "tree"}])
        (b / "spaces" / "exterior" / "space.json").write_text("{}")
        (b / "spaces" / "exterior" / "terrain.json").write_text(json.dumps({"cells": [], "ltex": {"L:1": {"diffuse": "textures/l.dds", "grasses": [{"model": "meshes/grass.nif"}]}}}))
        (b / "spaces" / "exterior" / "terrain.f32").write_bytes(b"\0" * 8)
        if bid != "ground.fx":
            (b / "spaces" / "Hall 1").mkdir()
            (b / "spaces" / "Hall 1" / "space.json").write_text(json.dumps({"copy_of": "fx.src/Hall 1"} if bid == "draft.fx" else {}))
            jl(b / "spaces" / "Hall 1" / "refs.jsonl", [])
        if bid == "draft.fx":
            for f in ("people", "paths", "clear", "land"):
                jl(b / f"{f}.jsonl", [])
    cache.mkdir()
    (cache / "land").mkdir()
    (cache / "land" / "land.json").write_text(json.dumps({"L:1": {"file": "l 1.webp"}}))
    (cache / "land" / "l 1.webp").write_bytes(b"x" * 10)

    def asset(kind, *args):
        if kind == "land":
            return cache / "land" / "land.json"
        p = cache / f"{kind}-{abs(hash(args))}"
        p.write_bytes(glb("/api/asset/tex?path=textures/hut.dds&size=512") if kind == "mesh" else b"y" * 7)
        return p
    for k, v in {"PLACES_OUT": out, "PLACES_DIR": places, "STUDIO_WEB": web, "STUDIO_COMMIT": "0", "STUDIO_BUCKET_SYNC": "0",
                 "STUDIO_AWAKE": "0", "STUDIO_ZCACHE": tmp_path / "z", "JOBS_DIR": tmp_path / "jobs"}.items():
        monkeypatch.setenv(k, str(v))
    from tools.places.studio import links
    monkeypatch.setattr(links, "asset", asset)
    from tools.places import draft_bundle
    monkeypatch.setattr(draft_bundle, "build", lambda *a, **k: None)
    return {"out": out, "places": places, "web": web, "asset": asset}


def test_manifest_lists_exactly_what_the_front_end_asks_for(env):
    m = offline.manifest("fx", env["out"], env["places"], env["web"], env["asset"], ["autosave", "first"])
    urls = {f["url"]: f for f in m["files"]}
    assert "/js/main.js" in urls and "/" in urls and not any(u.startswith(("/test/", "/dev/")) for u in urls)
    for u in ("/api/places", "/api/status", "/api/place/fx/stock", "/api/place/fx/needs", "/api/place/fx/nav",
              "/api/place/fx/notes", "/api/place/fx/saves", "/api/place/fx/saves/autosave", "/api/place/fx/saves/first",
              "/api/bundle/ground.fx/spaces/exterior/terrain.f32", "/api/bundle/draft.fx/people.jsonl",
              "/api/bundle/src.fx.src/spaces/Hall%201/space.json",
              "/api/asset/mesh?model=meshes%2FHut.nif&level=0", "/api/asset/mesh?model=meshes%2Ftree.nif&level=1",
              "/api/asset/mesh?model=meshes%2Fgrass.nif&level=1",
              "/api/asset/tex?path=textures/hut.dds&size=512", "/api/asset/tex?path=textures/hut.dds&size=256",
              "/api/asset/thumb?model=meshes%2FHut.nif", "/api/asset/land", "/api/asset/land/l%201.webp"):
        assert u in urls, u
    # the ground's refs are drawn, but the ground is no source of things to add: no ground-only people, no draft rows
    assert "/api/bundle/ground.fx/people.jsonl" not in urls
    # a normal map is never fetched by the views
    assert not any("a_n.dds" in u for u in urls)
    assert urls["/api/bundle/ground.fx/spaces/exterior/terrain.f32"]["bytes"] == 8
    assert m["bytes"] == sum(f["bytes"] for f in m["files"]) and m["stamps"] == {"ground": "k-ground.fx", "draft": "k-draft.fx", "src": "k-src.fx.src"}
    assert m["web"] == offline.web_version(env["web"])
    (env["web"] / "js" / "main.js").write_text("// main, changed")
    assert offline.web_version(env["web"]) != m["web"]


def run(body):
    from tools.places.studio.server import make_app

    async def go():
        async with TestClient(TestServer(make_app())) as c:
            await body(c)
    asyncio.run(go())


def test_offline_endpoint_and_a_tablet_write_sent_twice_is_kept_once(env):
    async def body(c):
        r = await c.get("/api/place/fx/offline")
        m = await r.json()
        assert r.status == 200 and m["place_id"] == "fx" and any(f["url"] == "/api/place/fx/saves" for f in m["files"])
        assert (await c.get("/api/place/nope/offline")).status == 404
        ops = [{"n": 1, "at": "t", "op": "ref.remove", "space": "exterior", "call": "fault", "id": "r1", "before": {}}]
        save = {"name": "Offline", "ops": ops, "rev": 0, "client_token": "tok-1"}
        r1 = await (await c.put("/api/place/fx/saves/autosave", json=save)).json()
        r2 = await c.put("/api/place/fx/saves/autosave", json=save)   # the answer was lost: sent again
        assert r2.status == 200 and (await r2.json())["rev"] == r1["rev"] == 1
        # another version of the tablet's copy, on a rev the server moved past: refused, nothing overwritten
        r3 = await c.put("/api/place/fx/saves/autosave", json=save | {"client_token": "tok-2", "ops": []})
        assert r3.status == 409 and (await r3.json())["current"]["rev"] == 1
        assert len((await (await c.get("/api/place/fx/saves/autosave")).json())["ops"]) == 1
        note = {"text": "Move the hut", "client_id": "t-abc", "written_at": "2026-11-18T10:00:00Z"}
        n1 = await (await c.post("/api/place/fx/notes", json=note)).json()
        n2 = await (await c.post("/api/place/fx/notes", json=note)).json()
        notes = await (await c.get("/api/place/fx/notes")).json()
        assert n1["id"] == n2["id"] and len(notes) == 1 and notes[0]["sent"] is False and notes[0]["written_at"] == note["written_at"]
        assert (await c.post("/api/place/fx/notes", json={"text": "x", "client_id": "bad id!"})).status == 400
    run(body)


NODE = shutil.which("node")


@pytest.mark.skipif(not NODE, reason="node is not installed")
def test_seat_on_the_device_equals_seat_py(tmp_path):
    rnd = random.Random(7)
    cells = [(0, 0), (1, 0), (0, 1), (-1, -1)]
    heights = {c: [rnd.uniform(-300, 900) for _ in range(33 * 33)] for c in cells}
    rows = [{"cell": [cx, cy], "heights_index": i, "water": {"height": -50.0} if (cx, cy) == (1, 0) else None,
             "layers": []} for i, (cx, cy) in enumerate(cells)]
    raw = array("f", [h for c in cells for h in heights[c]])
    (tmp_path / "terrain.f32").write_bytes(raw.tobytes())
    (tmp_path / "terrain.json").write_text(json.dumps({"cells": rows, "ltex": {}}))
    patches = [{"cell": [0, 0], "verts": [[5, 6, 40.0], [5, 7, -32.0], [32, 32, 16.0]]}, {"cell": [1, 0], "verts": [[0, 0, 8.0]]}]
    g = seat.Ground({c: list(array("f", heights[c])) for c in cells}, {(1, 0): -50.0}, default_water=12.5)
    g.apply_patches(json.loads(json.dumps(patches)))
    pts = [(rnd.uniform(-4096, 8192), rnd.uniform(-4096, 8192)) for _ in range(300)]
    pts += [(4096.0, 100.0), (0.0, 0.0), (128.0 * 6, 128.0 * 5), (8191.0, 4095.9), (-1.0, -1.0), (8200.0, 9000.0)]
    want = [g.at(x, y) for x, y in pts]
    script = tmp_path / "seat_run.mjs"
    script.write_text(f"""
import {{ readFileSync }} from 'node:fs';
import {{ Terrain }} from '{(WEB / 'js' / 'bundle.js').as_uri()}';
import {{ normaliseCell }} from '{(WEB / 'js' / 'terrain_cells.js').as_uri()}';
import {{ seatAt }} from '{(WEB / 'js' / 'seat.js').as_uri()}';
const json = JSON.parse(readFileSync('{tmp_path / 'terrain.json'}', 'utf8'));
const buf = readFileSync('{tmp_path / 'terrain.f32'}');
const f32 = new Float32Array(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength));
const t = new Terrain(json, f32, json.cells.map((c) => normaliseCell(c, 33 * 33)));
const land = new Map();
for (const p of {json.dumps(patches)}) {{ const m = land.get(p.cell.join(',')) || new Map(); for (const [r, c, dz] of p.verts) m.set(r * 33 + c, (m.get(r * 33 + c) || 0) + dz); land.set(p.cell.join(','), m); }}
t.override = land;
console.log(JSON.stringify({json.dumps(pts)}.map(([x, y]) => seatAt(t, x, y, 12.5))));
""")
    r = subprocess.run([NODE, str(script)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr[-2000:]
    got = json.loads(r.stdout)
    for (x, y), w, j in zip(pts, want, got):
        assert (w["ground"] is None) == (j["ground"] is None), (x, y)
        if w["ground"] is not None:
            assert abs(w["ground"] - j["ground"]) < 1e-6, (x, y, w["ground"], j["ground"])
        assert w["water"] == j["water"], (x, y)
        assert abs(w["slope"] - j["slope"]) <= 0.01 and all(abs(a - b) <= 1e-4 for a, b in zip(w["normal"], j["normal"])), (x, y)
