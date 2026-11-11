"""The navmesh is cut round what is placed on the new world: every producer's refs shards are read, the collidable
references are the ones fed, each reduced to the voxel columns it blocks (a boulder right through: a solid, not a
shell; a low stone and a high bough none), a second run reuses every row and writes the same bytes, moving a boulder
rebuilds only the cells it touches, the flora placer keeps a road's walking width clear of a thing's collision, a
world reference a place clears is left out by where it stands, and a row kept under other code is built again. Synthetic ground and meshes (no game data;
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
FRAME = (CX0 * 4096.0, (CY_TOP + 1) * 4096.0, 128.0)  # the ground raster's first sample and its spacing


def test_every_producers_shards_are_read_and_the_collidable_are_fed(tmp_path):
    write_refs(tmp_path / "refs", ROCK)
    assert [f.parent.name for f in placed.shard_files(tmp_path / "refs")] == ["flora", "mist", "flora"]
    kw = dict(cache=tmp_path / "rows", resolver=Resolver(), sample=1)
    t = placed.write_rows(tmp_path / "refs", tmp_path, tmp_path / "objects", BOX, ground(), FRAME, **kw)
    assert (t["refs"], t["collidable"], t["fed"], t["no_collision"], t["unresolved"]) == (4, 2, 2, 2, 0)
    assert t["producers"] == {"flora": {"refs": 3, "fed": 2}, "mist": {"refs": 1, "fed": 0}}
    assert placed.collidable_count(tmp_path / "refs", tmp_path, BOX, Resolver()) == 2
    runs = np.fromfile(tmp_path / "objects" / "cy-016.runs.i32", np.int32).reshape(-1, 3)  # the boulder's columns
    assert t["columns"] == int((runs[:, 2] - runs[:, 1] + 1).sum()) and 1350 <= t["columns"] <= 1650  # 600 x 600 units of 16
    assert ((runs[:, 1] + 0.5) * 16 > ROCK[0] - 450).all() and ((runs[:, 2] + 0.5) * 16 < ROCK[0] + 450).all()
    assert not (tmp_path / "objects" / "cy-017.runs.i32").exists()  # the low stone blocks nothing
    probe = np.load(tmp_path / "objects" / "probe.npy")  # the boulder alone stands in an actor's way
    assert len(probe) == 1 and abs(probe[0, 0] - ROCK[0]) <= 300 and probe[0, 3] > 128
    first = {f.name: f.read_bytes() for f in (tmp_path / "objects").iterdir()}
    stamp = {f.name: f.stat().st_mtime_ns for f in (tmp_path / "rows").iterdir()}
    assert placed.write_rows(tmp_path / "refs", tmp_path, tmp_path / "objects", BOX, ground(), FRAME, **kw) == t
    assert {f.name: f.read_bytes() for f in (tmp_path / "objects").iterdir()} == first  # the same bytes,
    assert {f.name: f.stat().st_mtime_ns for f in (tmp_path / "rows").iterdir()} == stamp  # from the rows kept


def test_a_cleared_reference_is_left_out_by_where_it_stands(tmp_path):
    write_refs(tmp_path / "refs", ROCK)
    kw = dict(cache=tmp_path / "rows", resolver=Resolver(), sample=1)
    run = lambda at_: placed.write_rows(tmp_path / "refs", tmp_path, tmp_path / "objects", BOX, ground(), FRAME,
                                        exclude=placed.Cleared([at_]), **kw)
    near = [ROCK[0] + 0.06, ROCK[1] - 0.06, ROCK[2] + 0.03]  # as the world file holds it: a 32-bit float of the shard's
    t = run(near)
    assert (t["refs"], t["collidable"], t["fed"], t["cleared"]) == (3, 1, 1, 1)  # the boulder is not there
    assert not (tmp_path / "objects" / "cy-016.runs.i32").exists() and len(np.load(tmp_path / "objects" / "probe.npy")) == 0
    t = run([ROCK[0] + 2.0, ROCK[1], ROCK[2]])  # another thing's place: nothing is left out
    assert (t["refs"], t["fed"], t["cleared"]) == (4, 2, 0) and (tmp_path / "objects" / "cy-016.runs.i32").exists()
    assert "cleared" not in placed.write_rows(tmp_path / "refs", tmp_path, tmp_path / "objects", BOX, ground(), FRAME, **kw)


def test_a_row_kept_under_other_code_is_built_again(tmp_path, monkeypatch, capsys):
    write_refs(tmp_path / "refs", ROCK)
    code = []
    for f in placed.ROW_CODE:
        code.append(tmp_path / f.name)
        code[-1].write_bytes(f.read_bytes())
    assert [f.name for f in code] == ["solid.py", "placed.py"]
    monkeypatch.setattr(placed, "ROW_CODE", tuple(code))

    def run():
        placed.write_rows(tmp_path / "refs", tmp_path, tmp_path / "objects", BOX, ground(), FRAME, cache=tmp_path / "rows",
                          resolver=Resolver(), sample=1)
        return json.loads(capsys.readouterr().out.strip().splitlines()[-1])["placed rows"]
    assert run() == {"built": 2, "reused": 0}
    assert run() == {"built": 0, "reused": 2}
    for f in code:  # an edit to either file: every kept row is stale
        f.write_bytes(f.read_bytes() + b"\n# edited\n")
        assert run() == {"built": 2, "reused": 0}
        assert run() == {"built": 0, "reused": 2}


def test_what_blocks_a_column():
    h = np.zeros((40, 40), np.float32)
    def cols(t):
        runs, _ = placed.blocked_columns(np.asarray(t, float), h, (0.0, 40 * 128.0, 128.0))
        return int((runs[:, 2] - runs[:, 1] + 1).sum()) if len(runs) else 0
    assert cols(box_tris(100, 100, 200, 180, -20, 300)) == 7 * 6  # a body through the band: every column it stands in
    assert cols(box_tris(100, 100, 200, 180, -20, 30)) == 0  # under the climb: stepped over
    assert cols(nif._box_tris(np.array([100.0, 100, 130]), np.array([200.0, 180, 300]))) == 0  # a closed body over an actor's head: walked under
    shell = box_tris(100, 100, 600, 600, -20, 900)
    assert cols(shell[[i for i in range(len(shell)) if not (shell[i][:, 2] < 0).all()]]) == 32 * 32  # no underside: solid all the same
    ring = np.concatenate([box_tris(4, 4, 396, 12, 0, 200), box_tris(4, 388, 396, 396, 0, 200), box_tris(4, 4, 12, 396, 0, 200),
                           box_tris(388, 4, 396, 396, 0, 200)])
    assert cols(ring) == 25 * 25  # the ground one thing closes in is inside it


def test_the_placer_keeps_a_roads_walking_width_clear():
    from scipy.spatial import cKDTree
    from tools.newworld.place import place

    class W:
        h, ox, oy, H, W = np.zeros((64, 64), np.float32), 0.0, 64 * 128.0, 64, 64

    class P:
        reach = {"hull": 500.0, "bare": 0.0}

        def collision(self, key):
            return box_tris(-100, -100, 100, 100, -20, 300) if key == "hull" else np.zeros((0, 3, 3))

    class R:
        pts = np.column_stack([np.arange(0, 8000.0, 70.0), np.full(115, 4000.0)])  # a minor road running east
        edge = np.full(115, 2.0)
        tree = cKDTree(pts)

    def short(key, y, scale=1.0):
        return place.road_shortfall(W, P(), R, {"base": key, "pos": [4000.0, y, 0.0], "rot": [0, 0, 0], "scale": scale})
    assert short("hull", 4000.0 + 192 + 48 + 100 + 24) == 0  # its near side past the walking width and the clearance
    assert 30 < short("hull", 4000.0 + 192 + 100) < 70  # a collision at the walking width's edge is inside the clear line
    assert short("hull", 4700.0, scale=5.0) > 0  # the same base at scale 5 reaches the road from 10 m out
    assert short("bare", 4000.0) == 0  # no collision, no rule


def test_a_mesh_that_is_not_found_is_a_fault(tmp_path):
    (tmp_path / "refs" / "flora").mkdir(parents=True)
    (tmp_path / "refs" / "flora" / "cy-016.jsonl").write_text(json.dumps(
        {"key": "000009:Mod.esp", "pos": ROCK, "rot": [0, 0, 0], "scale": 1.0, "model": "gone.nif"}) + "\n")
    t = placed.write_rows(tmp_path / "refs", tmp_path, tmp_path / "objects", BOX, ground(), FRAME, resolver=Resolver())
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
    assert ck["green"] and ck["objects"] > 0
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
