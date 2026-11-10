"""The draft's overlap rule (the build's), the fit's separation pass and routine reachability."""
import math

from tools.places.draft import geom, overlap, reach
from tools.places.seat import Ground

BOX = {"bounds": [[-100, -100, 0], [100, 100, 100]], "model": "x/box.nif"}
BASES = {"box": BOX, "small": {"bounds": [[-10, -10, 0], [10, 10, 50]], "model": "x/small.nif"}}


def ref(i, x, y, base="box", kind="static", z=0.0, **kw):
    return {"id": i, "base": base, "kind": kind, "pos": [x, y, z], "rot": [0, 0, 0], "scale": 1.0, **kw}


def flat(h=0.0, water=None):
    return Ground({(c, d): [h] * 33 * 33 for c in range(-2, 2) for d in range(-2, 2)}, {}, water)


def test_inside_uses_shrunk_box_and_height():
    b = ref("b", 0, 0)
    assert overlap.inside([70, 0, 10], b, BASES)          # within 0.8 of the half-width
    assert not overlap.inside([90, 0, 10], b, BASES)      # outside the shrunk box
    assert not overlap.inside([0, 0, 200], b, BASES)      # above its top
    assert overlap.inside([0, 0, 200], b, BASES, z=False)


def test_pairs_exempt_one_cluster_and_seated_on():
    a, b = ref("a", 50, 0, src="s1", cluster="c1"), ref("b", 0, 0, src="s2", cluster="c1")
    assert overlap.pairs([a, b], BASES) == []
    b["cluster"] = "c2"
    assert len(overlap.pairs([a, b], BASES)) == 2
    a["seat"] = {"mode": "on", "on": "b"}
    assert overlap.pairs([a, b], BASES) == []


def test_added_pieces_are_never_exempt():
    a, b = ref("a", 50, 0, cluster="c1"), ref("b", 0, 0, src="s2", cluster="c1")
    assert len(overlap.pairs([a, b], BASES)) == 2


def test_foot_hits_turned_boxes():
    a = ref("a", 0, 0)
    b = ref("b", 230, 0)
    assert not overlap.foot_hits(a, b, BASES)
    b["rot"] = [0, 0, math.pi / 4]          # turned, its corner reaches 141 towards a (to 89)
    assert overlap.foot_hits(a, b, BASES)


class _Cluster:
    def __init__(self, cid, members, centre):
        self.id, self.members, self.centre, self.kind = cid, members, centre, "street"


class _Fit:
    def __init__(self, ids):
        self.per = {i: geom.Xf((0, 0), (0, 0), 0.0) for i in ids}


class _Scorer:
    def misses(self, c, xf):
        return 0


def test_separate_moves_the_smaller_cluster_clear():
    by_src = {"big": ref("big", 0, 0), "little": ref("little", 40, 0, base="small")}
    cl = [_Cluster("A", ["big"], (0, 0)), _Cluster("B", ["little"], (40, 0))]
    fit = _Fit(["A", "B"])
    moves = overlap.separate(_Scorer(), fit, cl, by_src, BASES, lambda r: r["base"])
    assert moves and moves[0]["cluster"] == "B"
    x, y = fit.per["B"].pt(40, 0)
    assert not overlap.inside([x, y], by_src["big"], BASES, z=False)
    assert fit.per["A"].pt(0, 0) == (0, 0)


def test_reach_stop_walled_in_and_open():
    G = flat(0.0)
    street = [{"id": "p", "points": [[-1500, 0], [-1000, 0]], "width": 256}]
    ring = [ref(f"w{k}", 300 * math.sin(k * math.pi / 8), 300 * math.cos(k * math.pi / 8), kind="building")
            for k in range(16)]
    person = {"id": "x", "role": "resident", "routine": [{"at": {"space": "exterior", "pos": [0, 0]}},
                                                          {"at": {"space": "exterior", "pos": [-1200, 0]}}]}
    assert reach.check([person], [], {}, BASES, street, G, lambda d: True) == []
    walled = reach.check([person], ring, {}, BASES, street, G, lambda d: True)
    assert len(walled) == 1 and "no walk" in walled[0]


def test_reach_room_behind_an_unreached_door():
    G = flat(0.0)
    person = {"id": "x", "role": "resident", "routine": [{"at": {"space": "room", "radius": 1024}}]}
    spaces = {"room": {"door_from": "d", "parent": "exterior", "copy_of": None, "room": None}}
    assert reach.check([person], [], spaces, BASES, [], G, lambda d: True) == []
    bad = reach.check([person], [], spaces, BASES, [], G, lambda d: False)
    assert len(bad) == 1 and "reached by no street" in bad[0]


def test_arrival_needs_a_door_pair_and_ground():
    G = flat(0.0)
    street = [{"id": "p", "points": [[0, -400], [0, 400]], "width": 256}]
    door = ref("d", 100, 0, kind="door", base="small",
               door={"to_space": "room", "to_ref": "i", "arrival": [150, 0, 0]})
    inner = {"id": "i", "door": {"to_space": "exterior", "to_ref": "d"}}
    spaces = {"room": {"door_from": "d", "parent": "exterior", "doors": [inner]}}
    assert reach.arrival_faults([door], spaces, BASES, street, G) == []
    spaces["room"]["doors"] = []
    assert "no door pair" in reach.arrival_faults([door], spaces, BASES, street, G)[0]
    spaces["room"]["doors"] = [inner]
    door["door"]["arrival"] = [150, 0, 400]          # high on something no walkway carries
    assert "on no walkway" in reach.arrival_faults([door], spaces, BASES, street, G)[0]
