"""A way drawn by hand into a person's stop (a routine stop's `route`) makes the walking mesh under it the preferred
way: build.drawn_ways reads them, carrynav.prefer_along marks the carried triangles, and the generated mesh takes
them with the paths as road polylines."""
from tools.places import carrynav as cn
from tools.places.build import drawn_ways


def test_drawn_ways_read_outdoor_stops_only():
    people = [{"id": "a", "routine": [
        {"start": 8, "hours": 4, "kind": "work", "at": {"space": "exterior", "pos": [0, 0, 0]}, "route": [[0, 0, 5], [500, 0, 5]]},
        {"start": 12, "hours": 1, "kind": "eat", "at": {"space": "room1", "pos": [0, 0, 0]}, "route": [[1, 1, 1], [2, 2, 2]]},
        {"start": 20, "hours": 10, "kind": "sleep", "at": {"space": "exterior", "pos": [0, 0, 0]}}]}]
    assert drawn_ways(people) == [[(0.0, 0.0, False), (500.0, 0.0, False)]]
    assert drawn_ways([{"id": "b", "routine": []}]) == []


def test_prefer_along_marks_the_triangles_under_the_way():
    # a strip of triangles along X, 64 wide, from 0 to 1024; and one far off to the north
    verts, tris = [], []
    for k in range(8):
        x0, x1 = k * 128.0, (k + 1) * 128.0
        b = len(verts)
        verts += [[x0, 0, 0], [x1, 0, 0], [x1, 64, 0], [x0, 64, 0]]
        tris += [(b, b + 1, b + 2), (b, b + 2, b + 3)]
    b = len(verts)
    verts += [[0, 2000, 0], [100, 2000, 0], [0, 2100, 0]]
    tris.append((b, b + 1, b + 2))
    cell = {"verts": verts, "tris": tris, "flags": [0] * len(tris)}
    n = cn.prefer_along(cell, [[(0, 32, False), (1024, 32, False)]])
    assert n == 16
    assert all(f & cn.PREFERRED for f in cell["flags"][:16]) and not cell["flags"][16] & cn.PREFERRED
    assert cn.prefer_along(cell, []) == 0
