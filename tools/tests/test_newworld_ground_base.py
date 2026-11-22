"""The province's ground as a fixed base (tools/newworld/rebuild.py, stages marked base; owner, 2026-11-22): no place,
road, people or note change makes a base stage stale, a changed base output refuses the run, the base is regenerated
only by the owner's override; and a ground patch (tools/newworld/world/patches.py) rewrites only the cells it reaches,
the rest of every row it writes the base's bytes."""
import dataclasses
import json
from pathlib import Path

import numpy as np
import pytest

from tools.newworld import rebuild as R
from tools.newworld.world import land as nwland, patches as P
from tools.newworld.world import units as su

BASE = tuple(dataclasses.replace(s, after=()) for s in R.STAGES if s.base)


def test_the_base_is_the_provinces_ground():
    assert {s.name for s in BASE} == {"scope", "regions", "terrain", "water", "land", "landcover", "cells", "paint"}
    patch = {s.name: s for s in R.STAGES}["ground-patch"]
    assert not patch.base and R.PATCH_LAND in patch.writes
    # no stage but the base writes the base's outputs: a patch writes beside them
    tree = R.Tree(stages=R.STAGES)
    held = {spec for s in BASE for spec in tree.base_specs(s)}
    for s in R.STAGES:
        if not s.base:
            assert not [w for w in s.writes for h in held if R._feeds(w, h) and w.startswith("out:")], s.name


def _tree(tmp_path: Path) -> R.Tree:
    repo, out, db = tmp_path / "repo", tmp_path / "out", tmp_path / "db"
    tree = R.Tree(repo=repo, stages=BASE, out=out, db=db, state=out / "newworld/rebuild", pin_path=repo / R.BASE_PIN)
    for s in BASE:
        for spec in tree.base_specs(s):
            p = tree.path_of(spec)
            if p.suffix:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json.dumps({"id": "b1", "sha256": "x", "key": "k", "build_id": "b1"}))
            else:
                p.mkdir(parents=True, exist_ok=True)
                (p / "cy+000.bin").write_bytes(b"\0" * 64)
    (out / "newworld/terrain/build.json").write_text(json.dumps({"id": "b1", "sha256": "x"}))
    db.mkdir(parents=True)
    for t, rows in (("place", [{"id": "jal-veesa", "px": 1, "py": 2, "footprint_radius_m": 110.0, "summary": "a"}]),
                    ("road", [{"id": "r1"}]), ("road_vertex", [{"road_id": "r1", "seq": 0, "px": 1, "py": 1}]),
                    ("region_note", [{"region_id": "g", "aspect_id": "look", "text": "reeds"}]),
                    ("symbol", [{"id": "s", "settlement_tier_id": "town", "meaning": "m"}])):
        (db / f"{t}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    places = repo / "newworld/places/jal-veesa"
    places.mkdir(parents=True)
    for f in ("land.jsonl", "paint.jsonl", "people.jsonl", "place.json"):
        (places / f).write_text("{}\n")
    R.pin_base(tree)
    return tree


def test_no_place_road_people_or_note_change_makes_the_base_stale(tmp_path):
    tree = _tree(tmp_path)
    assert {r["state"] for r in R.plan(tree)} == {"base"}
    db, places = tree.db, tree.repo / "newworld/places/jal-veesa"
    (db / "place.jsonl").write_text(json.dumps({"id": "jal-veesa", "px": 9, "py": 9, "footprint_radius_m": 120.0,
                                                "on_water": True, "summary": "b"}) + "\n")
    (db / "road.jsonl").write_text('{"id": "r1"}\n{"id": "join-new"}\n')
    (db / "road_vertex.jsonl").write_text('{"road_id": "join-new", "seq": 0, "px": 5, "py": 5}\n')
    (db / "region_note.jsonl").write_text('{"region_id": "g", "aspect_id": "look", "text": "mud"}\n')
    (db / "symbol.jsonl").write_text('{"id": "s", "settlement_tier_id": "city", "meaning": "n"}\n')
    for f in ("land.jsonl", "paint.jsonl", "people.jsonl", "place.json"):
        (places / f).write_text('{"changed": true}\n')
    tree2 = R.Tree(repo=tree.repo, stages=BASE, out=tree.out, db=tree.db, state=tree.state, pin_path=tree.pin_path)
    rows = R.plan(tree2)
    assert {r["state"] for r in rows} == {"base"}, rows
    assert "fixed base, never regenerated" in R.base_line(tree2, rows)
    assert [o.split(":")[0] for o in R.owed_patches(tree2)] == ["road join-new"]


def test_a_changed_base_output_refuses_the_run_and_the_override_alone_regenerates(tmp_path, capsys):
    tree = _tree(tmp_path)
    (tree.out / "newworld/plugin/land/cy+000.bin").write_bytes(b"\1" * 64)
    t = R.Tree(repo=tree.repo, stages=BASE, out=tree.out, db=tree.db, state=tree.state, pin_path=tree.pin_path)
    rows = R.plan(t)
    assert {r["stage"]: r["state"] for r in rows}["land"] == "broken"
    assert R.run(t, check_first=False) == 2
    err = capsys.readouterr().err
    assert "Only the owner can ask" in err and R.OVERRIDE in err
    t = R.Tree(repo=tree.repo, stages=BASE, out=tree.out, db=tree.db, state=tree.state, pin_path=tree.pin_path)
    (tree.out / "newworld/plugin/land/cy+000.bin").write_bytes(b"\0" * 64)
    assert R.run(t, force=("terrain",), check_first=False) == 2
    assert "would regenerate the province's ground" in capsys.readouterr().err
    over = R.Tree(repo=tree.repo, stages=BASE, out=tree.out, db=tree.db, state=tree.state, pin_path=tree.pin_path,
                  regenerate_base=True)
    assert {r["state"] for r in R.plan(over)} <= {"stale", "follows"}     # with the owner's word they run as stages


def test_pin_base_refuses_a_second_pin_without_the_override(tmp_path, monkeypatch, capsys):
    tree, real = _tree(tmp_path), R.Tree
    monkeypatch.setattr(R, "Tree", lambda **k: real(repo=tree.repo, stages=BASE, out=tree.out, db=tree.db,
                                                     state=tree.state, pin_path=tree.pin_path, **k))
    was = tree.pin_path.read_text()
    assert R.main(["pin-base"]) == 2
    err = capsys.readouterr().err
    assert "pinned already" in err and "Only the owner can ask" in err
    assert tree.pin_path.read_text() == was


# ---- a ground patch: only the cells it reaches ---------------------------------------------------------------------

def _plugin(tmp_path: Path, cells=(5, 4)) -> Path:
    nx, ny = cells
    g = su.Grid(build_id="t1", width=nx * 32 + 1, height=ny * 32 + 1, origin_x=0.0, origin_y=float(ny * 4096), water=0.0)
    rng = np.random.default_rng(7)
    lim = np.cumsum(np.cumsum(rng.integers(-1, 2, (g.height, g.width)), 0), 1).astype(np.int32) // 4 + 40
    plugin = tmp_path / "plugin"
    (plugin / "land").mkdir(parents=True)
    np.save(plugin / "land/limited.npy", lim)
    nrm = nwland.normals(lim)
    rows = range(g.cy_top, g.cy_bottom - 1, -1)
    for cy in rows:
        (plugin / "land" / nwland.shard_name(cy)).write_bytes(nwland.row_bytes(g, lim, nrm, cy))
    (plugin / "land/manifest.json").write_text(json.dumps({"key": "t1:base", "grid": g.to_dict(),
                                                           "shards": [nwland.shard_name(cy) for cy in rows]}))
    return plugin


def test_a_patch_rewrites_only_the_cells_it_reaches(tmp_path):
    plugin = _plugin(tmp_path)
    g, _ = P._grid(plugin)
    base = {p.name: p.read_bytes() for p in (plugin / "land").glob("cy*.bin")}
    patches = tmp_path / "ground_patches.jsonl"
    cell = [2, 1]
    patches.write_text(json.dumps({"id": "patch.0001", "by": "agent", "why": "a landing's pad",
                                   "cell": cell, "verts": [[r, c, 48.0] for r in range(10, 20) for c in range(10, 20)]}) + "\n")
    doc = P.apply(plugin, patches)
    assert doc["cells"] == [cell]
    assert P.check(plugin, patches) == []
    near = P.reach(P.read_rows(patches))
    out = plugin / "patch/land"
    for name in base:
        cy = int(name[2:-4])
        got = (out / name).read_bytes() if (out / name).exists() else base[name]
        for i in range(g.cells_x):
            sl = slice(i * P.CELL_BYTES, (i + 1) * P.CELL_BYTES)
            if (g.cx0 + i, cy) not in near:
                assert got[sl] == base[name][sl], (name, i)
        assert (plugin / "land" / name).read_bytes() == base[name]        # the base itself is never written
    first = {p.name: p.read_bytes() for p in out.glob("cy*.bin")}
    P.apply(plugin, patches)                                              # applied again: the same bytes
    assert {p.name: p.read_bytes() for p in out.glob("cy*.bin")} == first
    patches.write_text("")                                                # removed: the base stands alone
    assert P.apply(plugin, patches)["cells"] == [] and not list(out.glob("cy*.bin"))


def test_a_patch_on_an_edge_vertex_moves_both_cells_alike(tmp_path):
    plugin = _plugin(tmp_path)
    patches = tmp_path / "p.jsonl"
    patches.write_text(json.dumps({"id": "e", "why": "a road's bed at a cell edge", "cell": [2, 1],
                                   "verts": [[16, 32, -24.0]]}) + "\n" +
                       json.dumps({"id": "e2", "why": "the same vertex from the east", "cell": [3, 1],
                                   "verts": [[16, 0, -24.0]]}) + "\n")
    assert {tuple(c) for c in P.apply(plugin, patches)["cells"]} >= {(2, 1), (3, 1)}
    assert P.check(plugin, patches) == []
    patches.write_text(json.dumps({"id": "e", "why": "w", "cell": [2, 1], "verts": [[16, 32, -24.0]]}) + "\n" +
                       json.dumps({"id": "e2", "why": "w", "cell": [3, 1], "verts": [[16, 0, 40.0]]}) + "\n")
    with pytest.raises(P.PatchError):
        P.apply(plugin, patches)
