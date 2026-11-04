"""The creature journeys are state checks (owner 19:05 #41, lane 1.15-r6-creatures-state): no still at any stop, and every
stop reads its spawn's own reference and the actors near it, with a kind assertion against our roster's lists."""
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[4]
REF = re.compile(r"^ArgoniaWorld\.esm\|0x[0-9A-F]{6}$")


@pytest.mark.parametrize("name", ["creature-spots", "creatures-kinds"])
def test_generated_journey_takes_no_still_and_reads_kinds(name):
    j = yaml.safe_load((ROOT / "tests" / "journeys" / f"{name}.yaml").read_text())
    assert j["stills"] is False and "camera" not in j and "look" not in j
    for s in j["steps"]:
        flat = yaml.safe_dump(s)
        assert "reader" not in flat and "screenshot" not in flat and "setangle" not in flat and " fw " not in flat
        ex = s["expect"]
        actors = [e for e in ex if e.get("read", [None])[0] == "actors"]
        assert actors, s["name"]
        if s["name"] == "guar-pen":   # the kept guar, by editor id: alive, enabled, near
            continue
        kinds = [e for e in actors if "kinds" in e]
        assert any(e["path"] == "listed" for e in kinds), s["name"]   # the actors near, of the list's kinds
        spawn = [e for e in kinds if e["path"] == "refs"]
        assert spawn and REF.match(spawn[0]["read"][2]), s["name"]   # the spawn's own reference, of its list
        assert all(e["kinds"]["ge"] >= 1 and e["kinds"]["among"] for e in kinds)
        assert any(e.get("path") == "refs.0.loaded_3d" and e.get("eq") is True for e in actors), s["name"]


def test_ref_ids_number_refs_per_cell_as_the_shards_do():
    from tools.argonia_world.creatures import journey, records
    refs = [{"cell": (0, 0)}, {"cell": (1, 0)}, {"cell": (0, 0)}]
    ids = journey.ref_ids(refs)
    assert ids[id(refs[2])] == f"ArgoniaWorld.esm|0x{records.ref_id(0, 0, 1):06X}"
    assert ids[id(refs[1])] == f"ArgoniaWorld.esm|0x{records.ref_id(1, 0, 0):06X}"
