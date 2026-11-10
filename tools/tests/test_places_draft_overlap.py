"""The draft's overlap rule (the build's own functions) and the fit's separation pass."""
import math

from tools.places.draft import geom, overlap
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


def test_inside_turns_with_full_rotation():
    """A piece flipped about X (rot[0] = pi) has its box below its origin: the build's geometry, not the yaw alone."""
    flipped = ref("f", 0, 0, z=100.0)
    flipped["rot"] = [math.pi, 0, 0]
    assert overlap.inside([0, 0, 50], flipped, BASES)          # inside the flipped box, under the origin
    assert not overlap.inside([0, 0, 150], flipped, BASES)     # where the unflipped box would be


def test_standing_on_a_top_is_not_inside():
    deck = ref("d", 0, 0)
    assert geom.stands_in(deck, BASES, (0, 0, 50))
    assert not geom.stands_in(deck, BASES, (0, 0, 100))        # on its top


def test_fit_turns_tilted_refs_about_the_world_axis():
    from tools.places import xform
    xf = geom.Xf((0, 0), (0, 0), 0.7)
    r = [3.01, -0.03, 0.64]
    p = [100.0, 50.0, 30.0]
    a = xform.apply(xform.matrix([0, 0, 0], r), p)
    b = xform.apply(xform.matrix([0, 0, 0], xf.rot3(r)), p)
    assert math.dist(xf.pt(a[0], a[1]), b[:2]) < 0.01 and abs(a[2] - b[2]) < 0.01
