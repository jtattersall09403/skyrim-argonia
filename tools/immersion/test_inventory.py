"""L1 tests for the immersion inventory (chunk 0.4 §c): the binding gate, the SWF listing (the interface BSA's
name tables only), and reachability over a generated fixture. Nothing here loads a real master: the full run is
`python3 tools/immersion/inventory.py`, never part of the gate."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bsa  # noqa: E402
import inventory  # noqa: E402

DATA = inventory.data_dir()
needs_dotnet = pytest.mark.skipif(not Path(inventory.dotnet()[0]).exists(), reason="needs dotnet (build VM)")


def _row(id_, reach, verdict="unreviewed", **kw):
    return {"id": id_, "kind": "record", "type": "STAT", "edid": None, "source": "Skyrim.esm", "plugins": [],
            "surface": "record", "reach": reach, "verdict": verdict, **kw}


def _write(path: Path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return path


def test_bind_fails_on_reachable_unreviewed_row(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(inventory, "VERDICTS", tmp_path / "none.jsonl")
    inv = _write(tmp_path / "inv.jsonl", [_row("000001:Skyrim.esm", "world"), _row("000002:Skyrim.esm", None)])
    assert inventory.gate(inv, tmp_path / "c.json", bind=False) == 0  # through Part 1 the gate only reports
    assert inventory.gate(inv, tmp_path / "c.json", bind=True) == 1
    assert "000001:Skyrim.esm (STAT): reachable via world, unreviewed" in capsys.readouterr().out


def test_bind_passes_when_reachable_rows_have_verdicts(tmp_path, monkeypatch):
    verdicts = _write(tmp_path / "v.jsonl", [{"id": "000001:Skyrim.esm", "verdict": "keep"}])
    monkeypatch.setattr(inventory, "VERDICTS", verdicts)
    inv = _write(tmp_path / "inv.jsonl", [_row("000001:Skyrim.esm", "world"), _row("000002:Skyrim.esm", None)])
    assert inventory.gate(inv, tmp_path / "c.json", bind=True) == 0


def test_bind_fails_on_replace_without_passing_check(tmp_path, monkeypatch):
    verdicts = _write(tmp_path / "v.jsonl", [{"id": "000001:Skyrim.esm", "verdict": "replace", "check": "bat x"}])
    monkeypatch.setattr(inventory, "VERDICTS", verdicts)
    inv = _write(tmp_path / "inv.jsonl", [_row("000001:Skyrim.esm", "world")])
    assert inventory.gate(inv, tmp_path / "c.json", bind=True) == 1


def test_unknown_verdict_is_refused(tmp_path):
    with pytest.raises(SystemExit):
        inventory.load_verdicts(_write(tmp_path / "v.jsonl", [{"id": "x", "verdict": "maybe"}]))


def test_no_views_yet_is_empty_not_an_error():
    assert isinstance(inventory.view_rows(), list)


@pytest.mark.skipif(not (DATA / "Skyrim - Interface.bsa").is_file(), reason="needs the interface BSA")
def test_every_interface_swf_is_a_menu_row():
    swfs = {p for p in bsa.listing(DATA / "Skyrim - Interface.bsa") if p.endswith(".swf")}
    rows, per_archive = inventory.menu_rows(DATA)
    assert per_archive["Skyrim - Interface.bsa"] == len(swfs) > 0
    assert swfs <= {r["id"] for r in rows}


@needs_dotnet
def test_fixture_block_reaches_every_record_it_references(tmp_path):
    """Two tiny generated plugins (no game data, no real masters): the block's records and everything they use
    are reached from the block; the start-enabled quest and its topic from the start pass; an unused static not."""
    made = json.loads(inventory.run_dump("fixture", "--out", str(tmp_path)))
    out = tmp_path / "rows.jsonl"
    inventory.run_dump("dump", "--load-order", made["base_plugin"], "--root", made["block"], "--out", str(out))
    rows = {r["formkey"]: r for r in map(json.loads, out.read_text().splitlines())}
    for label, keys in (("world", made["world"]), ("start-quest", made["start_quest"]), (None, made["unreached"])):
        for k in keys:
            assert rows[k]["reach"] == label, rows[k]


@needs_dotnet
def test_fixture_block_walk_labels_what_the_cell_shows_and_stops_at_quests(tmp_path):
    """--block-cells: the cell's refs, their bases and the NPC's race and voice get hops from the cell; the quest
    (never placed), the start quest and the unused static get none. Fails on purpose without the walk."""
    made = json.loads(inventory.run_dump("fixture", "--out", str(tmp_path)))
    out = tmp_path / "rows.jsonl"
    cell, npc, quest, weap, rock, barrel, race, voice = made["world"]
    inventory.run_dump("dump", "--load-order", made["base_plugin"], "--root", made["block"], "--block-cells", cell,
                       "--out", str(out))
    rows = {r["formkey"]: r for r in map(json.loads, out.read_text().splitlines())}
    assert rows[cell]["block"] == 0
    assert rows[rock]["block"] == rows[barrel]["block"] == rows[npc]["block"] == 2  # cell -> ref -> base
    assert rows[race]["block"] == rows[voice]["block"] == 3
    for k in (quest, weap, *made["start_quest"], *made["unreached"]):
        assert rows[k].get("block") is None, rows[k]
