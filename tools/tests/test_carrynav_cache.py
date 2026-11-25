"""carrynav keeps each cell's cut and finish on disk by everything it reads (_kept, _cut_key, _finish_one): the same
key answers from disk, another key or another code makes it again, a torn file is made again, and the cells built
with the cache are the cells built without it."""
import json

from tools.places import carrynav as cn


def canon(cells: dict) -> str:
    return json.dumps({str(k): v for k, v in cells.items()}, sort_keys=True, default=lambda a: a.tolist() if hasattr(a, "tolist") else str(a))


def test_a_cells_work_is_kept_by_what_it_reads(tmp_path, monkeypatch):
    monkeypatch.setattr(cn, "CELL_CACHE", tmp_path / "cc")
    made = []

    def f(v):
        made.append(v)
        return {"v": v}
    assert cn._kept("cut", ("c", 1), lambda: f(1)) == {"v": 1}
    assert cn._kept("cut", ("c", 1), lambda: f(99)) == {"v": 1} and made == [1]
    assert cn._kept("cut", ("c", 2), lambda: f(2)) == {"v": 2} and made == [1, 2]
    for p in (tmp_path / "cc").rglob("*.pkl"):
        p.write_bytes(b"torn")
    assert cn._kept("cut", ("c", 1), lambda: f(3)) == {"v": 3}
    monkeypatch.setattr(cn, "_CODE", ["othercode"])
    assert cn._kept("cut", ("c", 2), lambda: f(4)) == {"v": 4}


def _inputs():
    zone = [(1000.0, 1000.0), (1400.0, 1000.0), (1400.0, 1400.0), (1000.0, 1400.0)]
    region = cn.Region(cn.disk((2048.0, 2048.0), 1500.0), [zone])
    carried = [([[x, y, 0.0], [x + 300, y, 0.0], [x, y + 300, 0.0]], 0, 0)
               for x in range(600, 3400, 400) for y in range(600, 3400, 400)]
    gen = {(0, 0): [([[x, y, 0.0], [x + 512, y, 0.0], [x, y + 512, 0.0]], 0) for x in range(0, 3584, 512) for y in range(0, 3584, 512)]}
    return region, carried, gen


def test_cells_with_the_cache_are_the_cells_without(tmp_path, monkeypatch):
    monkeypatch.setattr(cn, "CELL_CACHE", tmp_path / "cc")
    region, carried, gen = _inputs()
    a = cn.build_cells(carried, gen, region)
    region, carried, gen = _inputs()
    b = cn.build_cells(carried, gen, region)            # every cell from disk
    monkeypatch.setattr(cn, "_kept", lambda kind, key, make: make())
    region, carried, gen = _inputs()
    c = cn.build_cells(carried, gen, region)
    assert a and canon(a) == canon(b) == canon(c)


def test_a_moved_zone_redoes_its_cell(tmp_path, monkeypatch):
    monkeypatch.setattr(cn, "CELL_CACHE", tmp_path / "cc")
    region, carried, gen = _inputs()
    a = cn.build_cells(carried, gen, region)
    region, carried, gen = _inputs()
    region = cn.Region(region.outer, [[(1100.0, 1000.0), (1500.0, 1000.0), (1500.0, 1400.0), (1100.0, 1400.0)]])
    b = cn.build_cells(carried, gen, region)
    monkeypatch.setattr(cn, "_kept", lambda kind, key, make: make())
    region, carried, gen = _inputs()
    region = cn.Region(region.outer, [[(1100.0, 1000.0), (1500.0, 1000.0), (1500.0, 1400.0), (1100.0, 1400.0)]])
    c = cn.build_cells(carried, gen, region)
    assert canon(b) == canon(c) and canon(b) != canon(a)


def test_a_change_inside_a_cell_leaves_its_neighbours_finish_kept(tmp_path, monkeypatch):
    """A cell's finish reads only its neighbours' vertices on its border: a change in a cell's middle redoes that cell
    alone, and what is kept is what a build without the cache makes."""
    monkeypatch.setattr(cn, "CELL_CACHE", tmp_path / "cc")
    monkeypatch.setattr(cn, "JOBS", 1)
    C = cn.CELL

    def gen(dz):
        rows = {}
        for cx in (0, 1):
            for cy in (0, 1):
                x0, y0 = cx * C, cy * C
                pts = [(x0, y0), (x0 + C, y0), (x0 + C, y0 + C), (x0, y0 + C)]
                mid = (x0 + C / 2, y0 + C / 2, dz if (cx, cy) == (0, 0) else 0.0)
                rows[(cx, cy)] = [([[*pts[i], 0.0], [*pts[(i + 1) % 4], 0.0], list(mid)], 0) for i in range(4)]
        return rows
    region = cn.Region(cn.disk((-50000.0, -50000.0), 10.0), [])
    cn.build_cells([], gen(0.0), region)
    made = []
    real = cn._kept

    def spy(kind, key, make):
        return real(kind, key, lambda: (made.append((kind, key[0])), make())[1])
    monkeypatch.setattr(cn, "_kept", spy)
    got = cn.build_cells([], gen(40.0), region)
    assert ("finish", (0, 0)) in made and not [m for m in made if m[0] == "finish" and m[1] != (0, 0)]
    monkeypatch.setattr(cn, "_kept", lambda kind, key, make: make())
    assert canon(got) == canon(cn.build_cells([], gen(40.0), region))
