"""The world plugin's form id table (tools/newworld/idspace.py): no two allocators' ranges overlap, each allocator's
own constants are its row, the province fits, the rule-placed references never take a navmesh id, and the check of
what is built names an id used twice or in another allocator's range before the long stages run."""
import base64
import hashlib
import json
import re
import struct
from pathlib import Path

from tools.navmesh import stitch
from tools.newworld import atmosphere, idspace as I
from tools.newworld import rebuild as R
from tools.newworld.place import edits as E
from tools.newworld.place import place as P

REPO = Path(__file__).resolve().parents[2]
CS = REPO / "tools/ArgoniaPlugin"


def consts(path: Path) -> dict[str, int]:
    return {k: int(v, 16) for k, v in re.findall(r"\b(Id\w+) = (0x[0-9A-Fa-f]+)", path.read_text(encoding="utf-8"))}


def test_no_two_ranges_overlap_and_the_province_fits_each():
    assert I.table_faults() == []
    rows = sorted(I.RANGES, key=lambda r: r[1])
    assert all(a[2] < b[1] for a, b in zip(rows, rows[1:])) and rows[0][1] >= 0x800 and rows[-1][2] <= 0xFFFFFF
    cells = I.SCOPE[0] * I.SCOPE[1]
    assert I.size("navmesh") >= cells and I.size("cells") >= 2 * cells
    assert all(n <= hi - lo + 1 for _, lo, hi, _, n in I.RANGES)
    placed = dict((r[0], r[4]) for r in I.RANGES)["placed"]
    assert placed <= (P.FID_LAST - P.FID_FIRST + 1) // 2      # form_ids' own limit: half the slots


def test_a_range_reaching_into_another_or_too_small_for_the_province_is_named(monkeypatch):
    rows = tuple(("navmesh", lo, hi + 1, how, n) if name == "navmesh" else (name, lo, hi, how, n) for name, lo, hi, how, n in I.RANGES)
    monkeypatch.setattr(I, "RANGES", rows)
    assert any("navmesh" in f and "placed-high" in f and "overlap" in f for f in I.table_faults())
    rows = tuple((name, lo, hi, how, hi - lo + 2) if name == "cells" else (name, lo, hi, how, n) for name, lo, hi, how, n in I.RANGES)
    monkeypatch.setattr(I, "RANGES", rows)
    assert any(f.startswith("cells: the province's") for f in I.table_faults())


def test_every_allocators_own_constants_are_its_row_of_the_table():
    w, m = consts(CS / "NewWorld.cs"), consts(CS / "NewWorldMap.cs")
    assert (w["IdWorld"], w["IdMarker"]) == I.SPAN["world"] and w["IdTopCell"] == w["IdWorld"] + 1
    assert (w["IdCells"], w["IdRefs"] - 1) == I.SPAN["cells"]
    assert (w["IdRefs"], w["IdRefsCounted"] - 1) == (I.SPAN["placed"][0], I.SPAN["added"][1])
    assert (w["IdRefsCounted"], w["IdRefsEnd"]) == I.SPAN["counted"]
    assert (w["IdNavmesh"], w["IdNavmeshEnd"]) == I.SPAN["navmesh"] == I.HOLE
    assert (m["IdCoc"], m["IdMarkers"] - 1) == I.SPAN["teleports"] and m["IdMarkers"] == I.SPAN["map-markers"][0]
    assert stitch.NAVM_FIRST == I.SPAN["navmesh"][0]
    assert (P.FID_FIRST, P.FID_LAST) == I.PLACED == (I.SPAN["placed"][0], I.SPAN["placed-high"][1]) and P.FID_HOLE == I.HOLE
    assert (E.ADD_FIRST, E.ADD_LAST) == I.SPAN["added"]
    lo, hi = I.SPAN["atmosphere"]
    assert min(atmosphere.BASE.values()) == lo and all(lo <= v <= hi for v in atmosphere.BASE.values())
    doc = json.loads((REPO / "newworld/sources/world_formids.json").read_text(encoding="utf-8"))
    span = lambda s: tuple(int(x, 16) for x in s.split("-"))
    assert {k: span(v) for k, v in doc["blocks"].items()} == {k: I.SPAN[k] for k in I.REGISTRY}
    assert span(doc["seeded"]) == I.SPAN["seeded"]
    text = (CS / "FormIds.cs").read_text(encoding="utf-8")
    blocks = {k: (int(a, 16), int(b, 16)) for k, a, b in re.findall(r'\("(\w+)", (0x[0-9A-F]+), (0x[0-9A-F]+)\)', text)}
    assert blocks == {k: I.SPAN[k] for k in I.REGISTRY}
    assert tuple(int(x, 16) for x in re.search(r"WorldSeeded = \((0x[0-9A-F]+), (0x[0-9A-F]+)\)", text).groups()) == I.SPAN["seeded"]


def _plain(idents) -> dict[str, int]:
    """The slots with no hole: each identity's digest, a taken slot passed over in sorted order."""
    n = P.FID_LAST - P.FID_FIRST + 1
    taken, out = set(), {}
    for i in sorted(idents):
        s = int.from_bytes(hashlib.sha256(i.encode()).digest()[:8], "big") % n
        while s in taken:
            s = (s + 1) % n
        taken.add(s)
        out[i] = P.FID_FIRST + s
    return out


def test_a_rule_placed_reference_never_takes_a_navmesh_id_and_only_those_that_would_are_moved():
    names = [f"flora/{k % 200},{k // 200}/{hashlib.sha1(str(k).encode()).hexdigest()[:10]}" for k in range(40000)]
    plain, ids = _plain(names), P.form_ids(names)
    inside = {i for i in names if I.HOLE[0] <= plain[i] <= I.HOLE[1]}
    assert len(inside) > 100                                           # the sample reaches the navmesh's range
    assert len(set(ids.values())) == len(names) and ids == P.form_ids(reversed(names))
    assert not any(I.HOLE[0] <= v <= I.HOLE[1] for v in ids.values())
    assert all(P.FID_FIRST <= v <= P.FID_LAST for v in ids.values())
    assert {i for i in names if ids[i] != plain[i]} == inside          # every other reference keeps its slot


def shard(d: Path, cy: int, fids: list) -> None:
    d.mkdir(parents=True, exist_ok=True)
    (d / f"cy{cy:+04d}.jsonl").write_text("".join(
        json.dumps({"base": "a:b", "x": 1.0, **({"fid": f"{f:06X}"} if f is not None else {})}, separators=(",", ":")) + "\n" for f in fids))


def navi(path: Path, ids: list) -> None:
    raw = b"\0" * 24 + b"".join(b"NVMI" + struct.pack("<HI", 8, (1 << 24) | i) + b"\0" * 4 for i in ids)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"navi": base64.b64encode(raw).decode()}))


def plugin(tmp_path, flora, mist=(None, None), navm=(0x600000, 0x600005)) -> Path:
    p = tmp_path / "plugin"
    shard(p / "refs/flora", 0, flora)
    shard(p / "refs/mist", 0, list(mist))
    (p / "land").mkdir(parents=True)
    (p / "land/manifest.json").write_text(json.dumps({"grid": {"cells_x": 4, "cells_y": 3}}))
    navi(p / "navmesh/navi.json", list(navm))
    (p / "map").mkdir()
    (p / "map/teleports.json").write_text(json.dumps({"teleports": [{}, {}]}))
    (p / "map/markers.json").write_text(json.dumps({"markers": [{}]}))
    (p / "atmosphere.json").write_text(json.dumps({"weathers": [{"formid": 0x80500}]}))
    return p


def test_what_is_built_is_read_whole_and_a_clean_build_has_no_fault(tmp_path):
    bad, n = I.faults(plugin(tmp_path, [0x200010, 0x6FFFF0, 0x700000]))
    assert bad == []
    assert n["refs/flora"] == 3 and n["refs/mist"] == 2 and n["references counted in shard order"] == 2
    assert n["cells and their LAND"] == 24 and n["navmesh records"] == 2 and n["teleports"] == 2 and n["map markers"] == 1
    assert n["registered names"] > 7000 and n["ids"] == 3 + 24 + 2 + 3 + 2 + 2 + 1 + 1 + n["registered names"]


def test_a_reference_on_a_navmesh_id_is_named_twice_over(tmp_path):
    bad, _ = I.faults(plugin(tmp_path, [0x200010, 0x600005, 0x609000]))
    assert any("refs/flora" in b and "2 ids outside its range" in b and "600005 (navmesh's)" in b for b in bad)
    assert any("refs/flora" in b and "1 ids used twice" in b and "600005 (held by navmesh records)" in b for b in bad)


def test_one_id_in_two_producers_shards_and_an_id_in_no_range_are_named(tmp_path):
    p = plugin(tmp_path, [0x200010, 0x200011])
    shard(p / "refs/reeds", 3, [0x200011, 0x740000, 0xF00000])
    bad, _ = I.faults(p)
    assert any("refs/reeds" in b and "used twice" in b and "200011 (held by references of refs/flora)" in b for b in bad)
    assert any("refs/reeds" in b and "outside its range" in b and "740000 (counted's)" in b and "F00000 (no allocator's)" in b for b in bad)
    assert any("counted in shard order" in b and "used twice" in b for b in bad)      # 740000 is the first counted id


def test_a_grid_or_a_navmesh_record_past_its_range_is_named(tmp_path):
    p = plugin(tmp_path, [0x200010], navm=(0x600000, 0x609678))
    (p / "land/manifest.json").write_text(json.dumps({"grid": {"cells_x": 215, "cells_y": 180}}))
    bad, _ = I.faults(p)
    assert any(b.startswith("navmesh: the grid's 38700 cells do not fit") for b in bad)
    assert any("navmesh records" in b and "609678 (placed-high's)" in b for b in bad)
    assert I.faults(p, skip=frozenset({"navmesh"}))[0] == []                           # a part whose stage runs first is not read


def test_the_edits_check_stops_on_a_form_id_fault(tmp_path):
    p = plugin(tmp_path, [0x200010, 0x600001])
    said = []
    assert E.form_id_faults(p / "refs/flora", said.append) == 1 and any("FAIL form ids" in s for s in said)
    shard(p / "refs/flora", 0, [0x200010, 0x610001])
    assert E.form_id_faults(p / "refs/flora", said.append) == 0 and "none used twice" in said[-1]
    shard(tmp_path / "alone", 0, [0x200010, 0x200010])                                 # a hook outside a plugin: its own shards
    assert E.form_id_faults(tmp_path / "alone", said.append) == 1


def test_preflight_judges_the_current_outputs_and_leaves_a_stale_stages_to_its_run(tmp_path, monkeypatch):
    p = plugin(tmp_path / "out/newworld", [0x200010, 0x600001])
    assert p == tmp_path / "out/newworld/plugin"
    monkeypatch.setattr(R, "others_running", lambda: [])
    stages = (R.Stage("edits", "", writes=("out:newworld/plugin/refs/flora/manifest.json",)),)
    tree = R.Tree(repo=tmp_path, stages=stages)
    row = lambda state: next(r for r in R.preflight(tree, [{"stage": "edits", "state": state}]) if r[0].startswith("form ids"))
    red = row("current")
    assert red[1] is False and "600001" in red[2]
    ok = row("stale")
    assert ok[1] is True and "refs/flora" in ok[2]
    assert not any(r[0].startswith("form ids") for r in R.preflight(R.Tree(repo=tmp_path, stages=()), []))
