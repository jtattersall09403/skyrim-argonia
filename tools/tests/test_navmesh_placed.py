"""The navmesh is cut round what is placed on the new world: every producer's refs shards are read, the collidable
references are the ones fed, a placed boulder leaves a hole all the way through (a solid, not a shell), a low stone is
stepped over, and moving a boulder rebuilds only the cells it touches. Synthetic ground and meshes (no game data;
the build tests need the .NET SDK, else they are skipped)."""
import json

import numpy as np
import pytest

from tools.navmesh import __main__ as nav
from tools.navmesh import checks, nif, placed, world
from tools.tests.test_navmesh_newworld import CX0, CY_TOP, N, box_tris, ground, land, navms

SHELL = box_tris(-300, -300, 300, 300, -100, 900)  # a boulder's collision: sides and a top, no underside
SLAB = box_tris(-100, -100, 100, 100, -50, 16)  # a low stone, under the climb height
MESHES = {"rock.nif": SHELL, "slab.nif": SLAB, "mist.nif": np.zeros((0, 3, 3)), "fern.nif": np.zeros((0, 3, 3))}


class Resolver:
    def collision(self, modl):
        t = MESHES.get(modl)
        return None if t is None else nif.Collision(t, np.ones(len(t), np.uint8), {})


def at(cx, cy, dx, dy):
    """A position in a cell, on the ground (dx and dy on the LAND's own samples)."""
    x, y = cx * 4096 + dx, cy * 4096 + dy
    return [x, y, float(ground()[((CY_TOP + 1) * 4096 - y) // 128, (x - CX0 * 4096) // 128])]


def write_refs(root, rock_at):
    """Two producers' shards, as the placer and the mist write them."""
    (root / "flora").mkdir(parents=True, exist_ok=True)
    (root / "mist").mkdir(exist_ok=True)
    rows = [{"base": "Mod.esp:Rock", "key": "000001:Mod.esp", "pos": rock_at, "rot": [0, 0, 0.3], "scale": 1.0, "model": "rock.nif"},
            {"base": "Mod.esp:Slab", "key": "000002:Mod.esp", "pos": at(14, -17, 1920, 1920), "rot": [0, 0, 0], "scale": 1.0, "model": "slab.nif"},
            {"base": "Mod.esp:Fern", "key": "000003:Mod.esp", "pos": at(13, -17, 896, 896), "rot": [0, 0, 0], "scale": 1.0, "model": "fern.nif"}]
    by_row = {}
    for r in rows:
        by_row.setdefault(int(r["pos"][1] // 4096), []).append(r)
    for f in (root / "flora").glob("cy*.jsonl"):
        f.unlink()
    for cy, rs in by_row.items():
        (root / "flora" / f"cy{cy:+04d}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rs))
    x, y, z = at(12, -16, 512, 512)
    (root / "mist" / "cy-016.jsonl").write_text(json.dumps({"base": "000004:Mod.esp", "x": x, "y": y, "z": z, "rx": 0, "ry": 0, "rz": 1.0,
                                                           "scale": 1.5, "model": "mist.nif"}) + "\n")


BOX = (CX0 + 1, CY_TOP - N + 2, CX0 + N - 2, CY_TOP - 1)
ROCK = at(13, -16, 1920, 1920)


def test_every_producers_shards_are_read_and_the_collidable_are_fed(tmp_path):
    write_refs(tmp_path / "refs", ROCK)
    assert [f.parent.name for f in placed.shard_files(tmp_path / "refs")] == ["flora", "mist", "flora"]
    t = placed.write_rows(tmp_path / "refs", tmp_path, tmp_path / "objects", BOX, 384.0, ground=lambda x, y: 200.0, resolver=Resolver(), sample=1)
    assert (t["refs"], t["collidable"], t["fed"], t["no_collision"], t["unresolved"]) == (4, 2, 2, 2, 0)
    assert t["producers"] == {"flora": {"refs": 3, "fed": 2}, "mist": {"refs": 1, "fed": 0}}
    assert placed.collidable_count(tmp_path / "refs", tmp_path, BOX, Resolver()) == 2
    rows = np.fromfile(tmp_path / "objects" / "cy-016.f32", np.float32).reshape(-1, 3, 3)
    assert len(rows) == len(SHELL) and np.fromfile(tmp_path / "objects" / "cy-016.n.i32", np.int32).tolist() == [len(SHELL)]
    probe = np.load(tmp_path / "objects" / "probe.npy")  # the boulder alone stands in an actor's way
    assert len(probe) == 1 and abs(probe[0, 0] - ROCK[0]) <= 300 and probe[0, 3] > 128


def test_a_mesh_that_is_not_found_is_a_fault(tmp_path):
    (tmp_path / "refs" / "flora").mkdir(parents=True)
    (tmp_path / "refs" / "flora" / "cy-016.jsonl").write_text(json.dumps(
        {"key": "000009:Mod.esp", "pos": ROCK, "rot": [0, 0, 0], "scale": 1.0, "model": "gone.nif"}) + "\n")
    t = placed.write_rows(tmp_path / "refs", tmp_path, tmp_path / "objects", BOX, 384.0, resolver=Resolver())
    assert t["unresolved"] == 1 and t["unresolved_models"] == ["000009:Mod.esp"]


def test_a_leaning_capsule_keeps_its_thickness():
    t = nif._capsule_tris(np.array([0.0, 0, 0]), np.array([300.0, 0, 300.0]), 10.0).reshape(-1, 3)
    axis = np.array([1.0, 0, 1.0]) / np.sqrt(2)
    off = t - np.outer(t @ axis, axis)
    assert np.linalg.norm(off, axis=1).max() == pytest.approx(10.0)
    assert (t @ axis).min() == pytest.approx(-10.0) and (t @ axis).max() == pytest.approx(300 * np.sqrt(2) + 10)


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("navplaced")
    try:
        nav.build_tool()
    except Exception as e:  # no SDK here
        pytest.skip(f"no .NET SDK: {e}")
    cells = {(x, y) for x in range(BOX[0], BOX[2] + 1) for y in range(BOX[1], BOX[3] + 1)}
    write_refs(tmp / "refs", ROCK)
    old = world.settlements
    world.settlements = lambda: []
    try:
        kw = dict(cells=cells, land=land(tmp), heights=ground(), polylines=[], refs=tmp / "refs", resolver=Resolver())
        first = nav.build(tmp / "out", BOX, run_check=True, **kw)
        again = nav.build(tmp / "out", BOX, run_check=False, **kw)
        write_refs(tmp / "refs", at(13, -16, 2432, 1920))  # a re-scatter: the boulder moves inside its cell
        moved = nav.build(tmp / "out", BOX, run_check=False, **kw)
    finally:
        world.settlements = old
    return tmp / "out", first, again, moved


def test_a_placed_boulder_leaves_a_hole_right_through(built):
    out, first, again, moved = built
    ck = first["check"]
    assert ck["green"] and ck["objects"] == len(SHELL) + len(SLAB)
    pl = ck["placed"]
    assert pl["fed"] == pl["collidable"] == 2 and pl["green"] and first["placed"]["objects"] == 2
    assert pl["stands_tall"] == {"probed": 0, "in_a_hole": 0, "share": None} or pl["stands_tall"]["share"] == 1.0
    n = navms(out)[(13, -16)]  # after the move: no mesh anywhere under the boulder, its hollow middle included
    v, tv = n.verts.astype(np.float64), n.tris["v"].astype(int)
    cx, cy = at(13, -16, 2432, 1920)[:2]
    under = np.array([[cx + dx, cy + dy] for dx in (-200, 0, 200) for dy in (-200, 0, 200)], float)
    assert not checks.covered(under, v, tv).any()
    assert checks.covered(np.array([[ROCK[0] - 250.0, ROCK[1]]]), v, tv).all()  # where it stood is ground again


def test_a_low_stone_is_stepped_over(built):
    out, *_ = built
    n = navms(out)[(14, -17)]
    p = np.array([at(14, -17, 1920, 1920)[:2]], float)
    assert checks.covered(p, n.verts.astype(np.float64), n.tris["v"].astype(int)).all()


def test_a_rescatter_rebuilds_only_the_cells_it_touches(built):
    out, first, again, moved = built
    assert again["totals"]["built"] == 0 and again["sha256"] == first["sha256"]
    assert 1 <= moved["totals"]["built"] <= 9 and moved["sha256"] != first["sha256"]


def test_a_shard_reads_the_same_in_any_order(tmp_path):
    rows = [{"key": "000001:Mod.esp", "pos": [3.0, 2.0, 1.0], "rot": [0, 0, 0], "scale": 1.0, "model": "rock.nif"},
            {"base": "Skyrim.esm:FXMist", "x": 1.0, "y": 2.0, "z": 3.0, "rz": 0.5, "scale": 2.0}]
    a, b = tmp_path / "cy+000.jsonl", tmp_path / "b.jsonl"
    a.write_text("".join(json.dumps(r) + "\n" for r in rows))
    b.write_text("".join(json.dumps(r) + "\n" for r in rows[::-1]))
    assert placed.read_shard(a) == placed.read_shard(b)
    mist = placed.read_shard(a)[0]
    assert (mist["base"], mist["edid"], mist["pos"], mist["rot"]) == (None, "Skyrim.esm:FXMist", [1.0, 2.0, 3.0], [0.0, 0.0, 0.5])
    assert placed.shard_row(a) == 0 and placed.shard_row(b) is None
