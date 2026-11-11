"""A built place is current against the world while the world records it stands on are unchanged
(tools/places/worldparts.py): a rewrite of the world file that touches none of them leaves its ground bundle and its
build current, one that touches any names which. On a synthetic world file: no game data needed."""
import json
import struct

import pytest

from tools.places import bundle as B
from tools.places import ground_check
from tools.places import worldparts as W
from tools.tests.test_newworld_lodkeys import grup, rec, sub
from tools.tests.test_places_bundle import make_bundle

OWN, FAR = (3, -4), (40, 40)


def refr(fid, base, x=0.0, edid=b""):
    return rec(b"REFR", fid, (sub(b"EDID", edid + b"\0") if edid else b"") + sub(b"NAME", struct.pack("<I", base))
               + sub(b"DATA", struct.pack("<6f", x, 0, 0, 0, 0, 0)))


def cell(fid, grid, land, refs, name=b""):
    c = rec(b"CELL", fid, (sub(b"EDID", name + b"\0") if name else b"") + sub(b"DATA", b"\x02\x00") + sub(b"XCLC", struct.pack("<iiI", *grid, 0)))
    return c + grup(struct.pack("<I", fid), 6, grup(struct.pack("<I", fid), 9, rec(b"LAND", fid + 1, sub(b"VHGT", land), compress=True) + refs))


def esm(land=b"\x01" * 40, far_land=b"\x02" * 40, tree_x=10.0, far_x=5.0, coc_x=0.0, marker_x=0.0, marker_id=0xFF0000, mnam=b"\0" * 28,
        records=7, model=b"t.nif", desc=b"land build B1", own_name=b"", water=-2048.0, other_marker=True):
    """A world file of one master-less plugin: a tree base, a land texture, the world's persistent cell with its map
    markers, the place's own cell (a tree, a teleport marker) and a far cell."""
    head = rec(b"TES4", 0, sub(b"HEDR", struct.pack("<fiI", 1.7, records, 0x900)) + sub(b"CNAM", b"us\0") + sub(b"SNAM", desc + b"\0"))
    stat = grup(b"STAT", 0, rec(b"STAT", 0x800, sub(b"EDID", b"Tree\0") + sub(b"MODL", model + b"\0"))
                + rec(b"STAT", 0x801, sub(b"EDID", b"Rock\0") + sub(b"MODL", b"r.nif\0")))
    ltex = grup(b"LTEX", 0, rec(b"LTEX", 0x500, sub(b"EDID", b"Mud\0")))
    marks = refr(marker_id, 0x10, marker_x, b"ANW_MapMarker_there")
    if other_marker:
        marks += refr(0xFF0001, 0x10, 1.0, b"ANW_MapMarker_elsewhere")
    top = rec(b"CELL", 0x601, sub(b"DATA", b"\x02\x00") + sub(b"XCLC", struct.pack("<iiI", 0, 0, 0)), flags=0x400)
    top += grup(struct.pack("<I", 0x601), 6, grup(struct.pack("<I", 0x601), 8, marks))
    own = cell(0x700, OWN, land, refr(0x900, 0x800, tree_x) + refr(0x901, 0x32, coc_x), own_name)
    far = cell(0x710, FAR, far_land, refr(0x910, 0x801, far_x))
    wrld = rec(b"WRLD", 0x600, sub(b"EDID", b"ArgoniaBlackMarsh\0") + sub(b"DNAM", struct.pack("<ff", water, 0)) + sub(b"MNAM", mnam))
    blocks = grup(struct.pack("<i", 0), 4, grup(struct.pack("<i", 0), 5, own)) + grup(struct.pack("<i", 1), 4, grup(struct.pack("<i", 1), 5, far))
    return head + stat + ltex + grup(b"WRLD", 0, wrld + grup(struct.pack("<I", 0x600), 1, top + blocks))


@pytest.fixture
def world(tmp_path, monkeypatch):
    monkeypatch.setattr(B, "_SHA_CACHE", tmp_path / "sha.json")
    monkeypatch.setattr(W, "CACHE", tmp_path / "worldparts.json")
    f = tmp_path / "W.esm"

    def write(**kw):
        f.write_bytes(esm(**kw))
        return f
    write()
    return f, write


MARKER = ["ANW_MapMarker_there"]


def test_the_parts_read_are_the_cells_asked_their_bases_and_the_markers_linked(world):
    f, _ = world
    st = W.stamp(f, [OWN, (3, -3)], MARKER)
    p = st["parts"]
    assert list(p["cells"]) == ["3,-4"] and list(p["bases"]) == ["000800"]          # the far cell's rock is not this place's
    assert p["markers"] == {"ANW_MapMarker_there": "FF0000"} and st["file"] == "W.esm" and len(st["sha256"]) == 64
    assert all(p[k] for k in ("header", "world", "ltex", "persistent"))
    assert W.changed(st, f) == [] and W.read(f, [])["markers"]["ANW_MapMarker_elsewhere"] == "FF0001"


@pytest.mark.parametrize("rewrite", [
    {"marker_x": 900.0},                # a map marker moved (the map stage's rewrite for a teleport marker)
    {"mnam": b"\x05" * 28},             # the world's map box
    {"records": 99},                    # the header's record count
    {"coc_x": 64.0},                    # a teleport marker in the place's own cell
    {"far_land": b"\x09" * 40},         # another cell's land
    {"far_x": 77.0},                    # another cell's placed thing
    {"other_marker": False},            # a map marker the place does not link
])
def test_a_world_rewrite_that_touches_none_of_them_leaves_the_place_current(world, rewrite):
    f, write = world
    st = W.stamp(f, [OWN], MARKER)
    write(**rewrite)
    now = W.again(st, f)
    assert now["sha256"] != st["sha256"] and now["key"] == st["key"] and W.changed(st, f) == []


@pytest.mark.parametrize("rewrite, names", [
    ({"land": b"\x07" * 40}, "1 cell (3,-4)"),
    ({"tree_x": 12.0}, "1 cell (3,-4)"),
    ({"own_name": b"ANW_there"}, "1 cell (3,-4)"),            # the place's plugin overrides its cells' records whole
    ({"model": b"t2.nif"}, "1 base record (000800)"),
    ({"marker_id": 0xFF0009}, "1 map marker (ANW_MapMarker_there)"),
    ({"water": -1000.0}, "the worldspace record"),
    ({"desc": b"land build B2"}, "the file's masters or description"),
])
def test_a_world_rewrite_that_touches_one_names_it(world, rewrite, names):
    f, write = world
    st = W.stamp(f, [OWN], MARKER)
    write(**rewrite)
    assert W.changed(st, f) == [names]


def test_a_marker_the_world_did_not_hold_is_seen_when_it_arrives(world):
    f, write = world
    st = W.stamp(f, [OWN], ["ANW_MapMarker_elsewhere"])
    write(other_marker=False)
    assert W.changed(st, f) == ["1 map marker (ANW_MapMarker_elsewhere)"]
    gone = W.stamp(f, [OWN], ["ANW_MapMarker_elsewhere"])
    assert gone["parts"]["markers"] == {"ANW_MapMarker_elsewhere": None}
    write()
    assert W.changed(gone, f) == ["1 map marker (ANW_MapMarker_elsewhere)"] and W.changed(st, f) == []


def test_a_built_place_reads_stale_by_what_moved_under_its_bundle_or_its_build(world, tmp_path):
    f, write = world
    bundles, shards = tmp_path / "bundles", tmp_path / "shards"
    assert len(W.stale("t", f, bundles, shards)) == 2                                   # neither names what it stands on
    d = make_bundle(bundles)
    meta = json.loads((d / "bundle.json").read_text())
    B.write_json(d / "bundle.json", dict(meta, world=W.stamp(f, [OWN, FAR])))            # the bundle reads far around the place
    (shards / "t").mkdir(parents=True)
    (shards / "t" / "world.json").write_text(json.dumps(W.stamp(f, [OWN], MARKER)))     # the build its own cells and ring
    assert W.stale("t", f, bundles, shards) == []
    write(marker_x=500.0, mnam=b"\x01" * 28)
    assert W.stale("t", f, bundles, shards) == [] and W.main(["t"]) == 1                # (main reads the real out/: no stamp there)
    write(far_x=1.0)
    why = W.stale("t", f, bundles, shards)
    assert len(why) == 1 and "ground bundle" in why[0] and "1 cell (40,40)" in why[0] and "extract --ground t" in why[0]
    write(land=b"\x08" * 40)
    why = W.stale("t", f, bundles, shards)
    assert len(why) == 2 and "under its build the world changed: 1 cell (3,-4)" in why[1] and "tools.places build t" in why[1]


# ---- the ground check: the bundle against the world file here and the play machine's ---------------------------------

@pytest.fixture
def gc(world, tmp_path, monkeypatch):
    f, write = world
    monkeypatch.setattr(ground_check, "BUNDLES", tmp_path / "bundles")
    monkeypatch.setattr(ground_check, "ESM", f)
    monkeypatch.setattr(ground_check, "PLAY_SHA", tmp_path / "play-esm.sha256")
    monkeypatch.setattr(ground_check, "REPO", tmp_path)

    def bundle():
        d = tmp_path / "bundles" / "ground.t"
        if not d.exists():
            make_bundle(tmp_path / "bundles")
        st = W.stamp(f, [OWN])
        meta = json.loads((d / "bundle.json").read_text())
        B.write_json(d / "bundle.json", dict(meta, world=st, esm={"file": "W.esm", "sha256": st["sha256"]}))
        return st
    return tmp_path, write, bundle


def test_ground_check_cases(gc):
    root, write, bundle = gc
    assert not ground_check.check("t")["ok"]                                    # no bundle
    make_bundle(root / "bundles")
    r = ground_check.check("t")
    assert not r["ok"] and "names no world records" in r["reason"]              # a bundle with a file hash alone
    sha = bundle()["sha256"]
    r = ground_check.check("t")
    assert not r["ok"] and "absent" in r["reason"]                              # no play record: never a silent pass
    (root / "play-esm.sha256").write_text("garbage\n")
    assert not ground_check.check("t")["ok"]
    (root / "play-esm.sha256").write_text("b" * 64 + "\n")
    r = ground_check.check("t")
    assert not r["ok"] and r["play_sha"] == "b" * 64 and "never read here" in r["reason"]
    (root / "play-esm.sha256").write_text(sha.upper() + "\n")
    assert ground_check.check("t")["ok"] and ground_check.main(["t"]) == 0


def test_ground_check_holds_through_a_rewrite_that_moves_only_a_map_marker(gc):
    root, write, bundle = gc
    old = bundle()["sha256"]
    (root / "play-esm.sha256").write_text(old)
    write(marker_x=300.0)                                                       # built here, not yet sent
    r = ground_check.check("t")
    assert r["ok"] and r["built_sha"] != old and "not yet sent" in r["reason"] and r["changed"] == []
    (root / "play-esm.sha256").write_text(r["built_sha"])                       # sent: the play machine has the rewrite
    assert ground_check.check("t")["ok"]
    write(marker_x=600.0)                                                       # a second rewrite before the next send
    r = ground_check.check("t")
    assert r["ok"] and r["play_sha"] not in (old, r["built_sha"])              # that file was read here: it holds the same


def test_ground_check_names_what_moved_under_the_bundle(gc):
    root, write, bundle = gc
    sha = bundle()["sha256"]
    (root / "play-esm.sha256").write_text(sha)
    write(land=b"\x05" * 40)
    r = ground_check.check("t")
    assert not r["ok"] and r["changed"] == ["1 cell (3,-4)"] and "extract --ground t" in r["reason"]
    bundle()                                                                    # extracted again; the play machine has the old land
    r = ground_check.check("t")
    assert not r["ok"] and "holds other records under this ground" in r["reason"] and "lod.sh send" in r["reason"]


def test_status_shape(gc):
    root, write, bundle = gc
    assert ground_check.status()["match"] is False
    sha = bundle()["sha256"]
    (root / "play-esm.sha256").write_text(sha)
    s = ground_check.status()
    assert s["match"] and s["ground_sha"] == sha == s["deployed_sha"] and s["place_id"] == "t"
