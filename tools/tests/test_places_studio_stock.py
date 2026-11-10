"""The studio's stock and identity reads (tools/places/studio/stock.py) and their routes, over the dev fixture's
sources: the payload the panels read, the item search with each refusal and its reason."""
import asyncio
import importlib.util
import json
from pathlib import Path

import pytest

from tools.places.studio import stock

WEB = Path(__file__).resolve().parents[1] / "places/studio/web"


@pytest.fixture(scope="module")
def fx(tmp_path_factory):
    spec = importlib.util.spec_from_file_location("make_fixture", WEB / "dev/make_fixture.py")
    mf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mf)
    out = tmp_path_factory.mktemp("fx")
    dint = {"FixHouse01": [{"id": "fixplaceFixHouse01.chest"}, {"id": "fixplaceFixHouse01.table"}],
            "FixHouse02": [{"id": "fixplaceFixHouse02.chest"}]}
    mf.write_stock(out, dint)
    return out


def test_payload(fx):
    p = stock.payload("fixplace", stock.Sources(fx / "sources"), stock.Catalogue.open(fx / "catalogue/bases.jsonl"))
    assert p["facts"]["ceiling_tier"] == "T2" and p["facts"]["band_label"] == "Modest"
    assert [x["name"] for x in p["identities"]["people"]] == ["Ada Fixwright", "Bram Fixguard"]
    assert p["stock"]["containers"][0]["ref"] == "fixplaceFixHouse01.chest"
    sword = p["items"]["Fix.esm:00B001"]
    assert (sword["name"], sword["kind"], sword["tier"], sword["value"], sword["measured"]) == ("Iron Sword", "weapon", "T1", 25, True)
    dagger = p["items"]["Fix.esm:00B002"]   # not measured: its tier from its material, its value unknown
    assert (dagger["name"], dagger["tier"], dagger["value"], dagger["measured"]) == ("Steel Dagger", "T1", None, False)
    assert [t["id"] for t in p["scale"]["tiers"]] == ["T1", "T2", "T3", "T4", "T5", "T6"]
    assert "Novice" in p["scale"]["lock_levels"] and p["scale"]["person_wealth_bands"][0]["id"] == "W1"
    assert set(p["items"]) == stock.item_keys(p["stock"])


def test_search_refuses_with_reasons(fx):
    src, cat = stock.Sources(fx / "sources"), stock.Catalogue.open(fx / "catalogue/bases.jsonl")
    r = stock.search("fixplace", "sword", None, 10, src, cat)
    by = {x["name"]: x for x in r["results"]}
    assert r["ceiling"] == "T2" and set(by) == {"Iron Sword", "Glass Sword"}
    assert by["Iron Sword"]["allowed"] and not by["Glass Sword"]["allowed"]
    assert "above this place's ceiling T2" in by["Glass Sword"]["why"]
    axe = {x["name"]: x for x in stock.search("fixplace", "war axe", None, 10, src, cat)["results"]}
    assert not axe["Nordic War Axe"]["allowed"] and "decision 0006" in axe["Nordic War Axe"]["why"]
    assert stock.search("fixplace", "Iron Sword", None, 10, src, cat)["results"][0]["name"] == "Iron Sword", "an exact name first"
    assert [x["name"] for x in stock.search("fixplace", "i", "jewellery", 10, src, cat)["results"]] == ["Gold Ring"]
    assert stock.search("fixplace", "", None, 10, src, cat)["results"] == []
    assert len(stock.search("fixplace", "o", None, 2, src, cat)["results"]) == 2, "capped"


def test_an_owner_overrule_moves_the_ceiling(fx, tmp_path):
    import shutil
    shutil.copytree(fx / "sources", tmp_path / "sources")
    w = tmp_path / "sources/stock/place_wealth.json"
    d = json.loads(w.read_text())
    d["places"][0]["owner"] = {"band": "P4", "why": "the owner says so"}
    w.write_text(json.dumps(d))
    r = stock.search("fixplace", "glass", None, 5, stock.Sources(tmp_path / "sources"), None)
    assert r["ceiling"] == "T4" and r["results"] == [], "no catalogue: only what items.json measured is found"
    f = stock.payload("fixplace", stock.Sources(tmp_path / "sources"), None)["facts"]
    assert f["by"] == "owner" and f["ceiling_tier"] == "T4" and f["why"].startswith("owner: the owner says so")


def test_routes(fx, tmp_path, monkeypatch):
    aiohttp = pytest.importorskip("aiohttp")   # noqa: F841
    from aiohttp.test_utils import TestClient, TestServer
    out = tmp_path / "out"
    (out / "catalogue").mkdir(parents=True)
    (out / "catalogue/bases.jsonl").write_text((fx / "catalogue/bases.jsonl").read_text())
    for k, v in {"PLACES_OUT": out, "PLACES_DIR": tmp_path / "places", "NEWWORLD_SOURCES": fx / "sources",
                 "STUDIO_COMMIT": "0", "STUDIO_BUCKET_SYNC": "0", "STUDIO_AWAKE": "0", "STUDIO_ZCACHE": tmp_path / "z",
                 "JOBS_DIR": tmp_path / "jobs"}.items():
        monkeypatch.setenv(k, str(v))
    from tools.places.studio import server
    monkeypatch.setattr(server, "warm_search", lambda out: None)

    async def go():
        async with TestClient(TestServer(server.make_app())) as c:
            r = await c.get("/api/place/fixplace/stock")
            p = await r.json()
            assert r.status == 200 and p["items"]["Fix.esm:00B001"]["name"] == "Iron Sword"
            r = await c.get("/api/place/fixplace/items?q=glass&limit=5")
            j = await r.json()
            assert j["results"][0]["allowed"] is False and "ceiling" in j["results"][0]["why"]
            assert (await c.get("/api/place/BAD..ID/stock")).status == 400
            assert (await c.get("/api/place/fixplace/items?limit=x")).status == 400
    asyncio.run(go())
