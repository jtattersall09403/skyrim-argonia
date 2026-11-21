"""Variant drafts (tools/places/variant.py): held beside a place as <place>@<variant>, read with the place's ground and
record, never walked by anything that builds the game or counts for the gate, and swapped in by `variant use`."""
import json
import re
from pathlib import Path

import pytest

from tools.places import variant

ROOT = Path(__file__).resolve().parents[2]


def place(root: Path, pid: str, **extra):
    d = root / pid
    d.mkdir(parents=True)
    (d / "place.json").write_text(json.dumps({"place_id": pid, "source_id": "s", **extra}))
    (d / "land.jsonl").write_text("")
    return d


@pytest.fixture
def places(tmp_path):
    root = tmp_path / "places"
    place(root, "jv", mark="current")
    place(root, "jv@pipeline", variant_of="jv", variant="pipeline", title="JV (pipeline draft)", mark="pipeline")
    place(root, "other")
    return root


def test_ids_resolve_to_the_place():
    assert variant.record_id("jv@pipeline") == "jv" and variant.record_id("jv") == "jv"
    assert variant.ground("jv@pipeline") == "ground.jv" and variant.bundle("ground.jv@pipeline") == "ground.jv"
    assert variant.bundle("draft.jv@pipeline") == "draft.jv@pipeline"


def test_game_places_never_yield_a_variant(places):
    assert variant.game_places(places) == ["jv", "other"]
    assert variant.variants_of("jv", places) == ["pipeline"]


def test_use_swaps_and_keeps_the_current_draft_as_previous(places, tmp_path):
    said = variant.use("jv", "pipeline", places, tmp_path / "auto")
    assert "jv@previous" in said
    cur = json.loads((places / "jv" / "place.json").read_text())
    prev = json.loads((places / "jv@previous" / "place.json").read_text())
    assert cur["mark"] == "pipeline" and cur["place_id"] == "jv" and "variant_of" not in cur and "title" not in cur
    assert prev["mark"] == "current" and prev["variant_of"] == "jv" and prev["variant"] == "previous"
    assert prev["place_id"] == "jv@previous" and prev["title"].endswith("(previous draft)")
    assert not (places / "jv@pipeline").exists() and variant.variants_of("jv", places) == ["previous"]
    variant.use("jv", "previous", places, tmp_path / "auto")       # and back
    assert json.loads((places / "jv" / "place.json").read_text())["mark"] == "current"
    assert json.loads((places / "jv@previous" / "place.json").read_text())["mark"] == "pipeline"


def test_use_refuses_unsaved_studio_edits_and_a_taken_previous(places, tmp_path):
    auto = tmp_path / "auto"
    auto.mkdir()
    (auto / "jv@pipeline.json").write_text(json.dumps({"final": False, "ops": [{"op": "move"}]}))
    with pytest.raises(ValueError, match="unsaved"):
        variant.use("jv", "pipeline", places, auto)
    (auto / "jv@pipeline.json").write_text(json.dumps({"final": False, "ops": [], "notes": []}))
    place(places, "jv@previous", variant_of="jv", variant="previous")
    with pytest.raises(ValueError, match="taken"):
        variant.use("jv", "pipeline", places, auto)
    assert variant.drop("jv", "previous", places, auto) == "dropped jv@previous"
    variant.use("jv", "pipeline", places, auto)
    with pytest.raises(ValueError, match="no variant"):
        variant.use("jv", "nothing", places, auto)


def test_the_layer_plugin_build_refuses_a_variant():
    from tools.places import build
    assert build.main(["jal-veesa@pipeline", "--plan"]) == 2


def test_consistency_never_counts_a_variant(places, tmp_path):
    from tools.newworld import consistency
    root = tmp_path
    (root / "newworld").mkdir()
    (root / "newworld" / "places").symlink_to(places)
    d = consistency.load_drafts(root, tmp_path / "out")
    assert sorted(d) == ["jv", "other"]


def test_nothing_that_builds_or_gates_walks_the_place_folders_by_itself():
    """Every walk over all place folders for the game or the gate goes through variant.game_places: no module but the
    studio's dev server globs `*/place.json` or lists the places folder itself."""
    pat = re.compile(r'glob\(\s*["\']\*/place\.json|PLACES\.iterdir\(\)|places"\)\.glob\("\*/|str\(places / "\*"')
    hits = []
    for p in sorted((ROOT / "tools").rglob("*.py")) + sorted((ROOT / "tooling").rglob("*.py")):
        rel = p.relative_to(ROOT).as_posix()
        if "/tests/" in rel or rel.endswith("variant.py") or "/web/dev/" in rel:
            continue
        for n, ln in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if pat.search(ln):
                hits.append(f"{rel}:{n}: {ln.strip()}")
    assert not hits, "\n".join(hits)


def test_the_committed_variant_is_marked_and_not_built():
    d = ROOT / "newworld" / "places" / "jal-veesa@pipeline"
    if not d.exists():
        pytest.skip("no committed variant")
    pl = json.loads((d / "place.json").read_text())
    assert pl["variant_of"] == "jal-veesa" and pl["variant"] == "pipeline" and pl["place_id"] == "jal-veesa@pipeline"
    assert "jal-veesa@pipeline" not in variant.game_places()
