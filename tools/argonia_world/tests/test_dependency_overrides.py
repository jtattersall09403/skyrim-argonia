"""L1: every file a dependencies.json row lays (the Community Shaders override files) has a path and parses."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def _rows():
    return json.loads((ROOT / "data/dependencies.json").read_text(encoding="utf-8"))["mods"]


def test_every_laid_file_parses_and_cs_overrides_are_named_right():
    seen = 0
    for m in _rows():
        for f in m.get("files", []):
            seen += 1
            assert f["path"] and f.get("text"), (m["id"], f)
            if f["path"].endswith(".json"):
                body = json.loads(f["text"])
                if "/CommunityShaders/Overrides/" in f["path"]:
                    name = Path(f["path"]).stem
                    assert name.startswith("Argonia_"), name
                    assert body["_metadata"]["modName"] == "Argonia", name
                    assert body["_metadata"]["description"], name
    assert seen >= 5


def test_cs_overrides_cover_the_owner_features():
    paths = {f["path"] for m in _rows() for f in m.get("files", [])}
    for feat in ("ExponentialHeightFog", "VolumetricLighting", "CloudShadows", "TerrainShadows", "GrassLighting"):
        assert f"SKSE/Plugins/CommunityShaders/Overrides/Argonia_{feat}.json" in paths
