"""The easy-swap table (newworld/sources/dressing/swaps.json) seeds a new place's draft.replace."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.places.draft import io  # noqa: E402


def test_boat_stops_get_the_native_boats():
    k = "King of the Murkmire.esp:"
    assert io.stop_boats("lujei-ferry") == [k + "ALPABoat04"]
    assert io.stop_boats("korydon") == [k + "ALPABoat02", k + "ALPABoat03"]
    assert io.stop_boats("lilmoth") == [] and io.stop_boats("helstrom") == [k + "ALPABoat02", k + "ALPABoat03"]


def test_swap_table_seeds_replace_from_held_native_pieces():
    rows = json.loads(io.SWAPS.read_text())["swaps"]
    assert len(rows) >= 15 and all(r["keeps_function"] and r["looked"] for r in rows)
    if io.CATALOGUE.exists():
        got = io.seed_swaps({"Skyrim.esm:0800E2": {"edid": "NorTentSmall"}}, {})
        assert got == {"Skyrim.esm:0800E2": "Black Marsh.esm:2001F3"}
    assert io.seed_swaps({"Skyrim.esm:0800E2": {}}, {"Skyrim.esm:0800E2": "X:1"}) == {}   # the place's own row stands
    assert io.seed_swaps({"Skyrim.esm:000001": {}}, {}) == {}
