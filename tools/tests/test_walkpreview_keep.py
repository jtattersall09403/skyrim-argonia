"""walkpreview builds the navmesh in a folder kept between rebuilds (its per-cell caches), and deletes only that
folder's rasters and its own scratch when it ends."""
import json

from tools.places import build as B
from tools.places import navexport
from tools.places import walkpreview as W


def test_the_navmesh_folder_is_kept_between_rebuilds(tmp_path, monkeypatch):
    places, out = tmp_path / "places", tmp_path / "out"
    (places / "fx").mkdir(parents=True)
    (places / "fx" / "place.json").write_text(json.dumps({"place_id": "fx"}))
    seen = []

    def plan(pid, pdir, o, no_navmesh, **_):
        nav_dir = o / "navmesh" / pid      # where build.plan_place builds the exterior navmesh
        seen.append(nav_dir)
        for sub in ("in", "cache", "stitch"):
            (nav_dir / sub).mkdir(parents=True, exist_ok=True)
            (nav_dir / sub / "x").write_text("1")
        return {"notes": []}
    monkeypatch.setattr(B, "plan_place", plan)
    monkeypatch.setattr(B, "build_tool", lambda: None)
    monkeypatch.setattr(navexport, "export_plan", lambda *a, **k: None)
    for _ in range(2):
        assert W.preview("fx", "autosave", places, out)["state"] == "done"
    d = W.run_dir(out, "fx")
    nav = d / "plan" / "navmesh" / "fx"
    assert seen == [nav] * 2
    assert (nav / "cache" / "x").exists() and (nav / "stitch" / "x").exists()
    assert not (nav / "in").exists() and not (d / "work").exists()
