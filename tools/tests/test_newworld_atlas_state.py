"""The Atlas freshness check: a changed place name or fast travel fare makes it fail."""
import shutil
from pathlib import Path

from tools.newworld import atlas_state as a


def test_place_change_makes_atlas_behind(tmp_path: Path):
    for rel in [*(a.DB / f"{t}.jsonl" for t in a.TABLES), a.TEMPLATE]:
        src = a.ROOT / rel
        if src.exists():
            (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, tmp_path / rel)
    rec = tmp_path / "atlas.json"
    rec.write_text('{"url": "u", "published_hash": "%s"}' % a.sources_hash(tmp_path))
    assert a.check(tmp_path, rec) is None
    place = tmp_path / a.DB / "place.jsonl"
    place.write_text(place.read_text().replace('"name":"', '"name":"X', 1))
    msg = a.check(tmp_path, rec)
    assert msg and "Atlas behind" in msg and "mark-published" in msg


def test_travel_change_makes_atlas_behind(tmp_path: Path):
    for rel in [*(a.DB / f"{t}.jsonl" for t in a.TABLES), a.TEMPLATE, a.NETWORK]:
        src = a.ROOT / rel
        if src.exists():
            (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, tmp_path / rel)
    rec = tmp_path / "atlas.json"
    rec.write_text('{"url": "u", "published_hash": "%s"}' % a.sources_hash(tmp_path))
    assert a.check(tmp_path, rec) is None
    net = tmp_path / a.NETWORK
    net.write_text(net.read_text().replace('"fare_base": 10', '"fare_base": 11', 1))
    assert "Atlas behind" in (a.check(tmp_path, rec) or "")
    shutil.copy(a.ROOT / a.NETWORK, net)
    route = tmp_path / a.DB / "travel_route.jsonl"
    route.write_text(route.read_text().replace('"fare":', '"fare":1', 1))
    assert "Atlas behind" in (a.check(tmp_path, rec) or "")
