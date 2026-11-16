"""Every place record says what it is built from: a `source` note (FORMAT.md), shown in the atlas as "Built from"."""
import json
from pathlib import Path

DB = Path(__file__).resolve().parents[2] / "newworld" / "story" / "data" / "db"


def rows(name: str) -> list[dict]:
    return [json.loads(x) for x in (DB / f"{name}.jsonl").read_text().splitlines() if x.strip()]


def test_source_is_a_place_aspect():
    a = {r["id"]: r for r in rows("note_aspect")}
    assert a["source"]["applies_to"] == "place"


def test_every_place_has_a_source_note():
    places = {r["id"] for r in rows("place")}
    noted = {r["place_id"] for r in rows("place_note") if r["aspect_id"] == "source"}
    assert places - noted == set()


def test_atlas_heads_it_built_from():
    from tools.newworld import map_page
    assert map_page.HEADING["source"] == "Built from"
