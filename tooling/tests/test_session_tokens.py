import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import session_tokens as st  # noqa: E402


def rec(mid, model, out):
    return json.dumps({"message": {"id": mid, "model": model, "usage": {
        "input_tokens": 1000, "output_tokens": out, "cache_read_input_tokens": 1000000, "cache_creation_input_tokens": 0}}})


def test_fixture_transcript_priced_and_unpriced(tmp_path):
    lines = [rec("m1", "claude-opus-5-5", 5), rec("m1", "claude-opus-5-5", 1000000),  # one call, last record wins
             rec("m2", "claude-future-9", 10)]
    (tmp_path / "s.jsonl").write_text("\n".join(lines) + "\n")
    by = st.usage_by_model(str(tmp_path))
    assert by["claude-opus-5-5"]["output"] == 1000000
    assert round(st.usd("claude-opus-5-5", by["claude-opus-5-5"]), 3) == 4 * 0.001 + 20 + 0.2
    assert st.usd("claude-future-9", by["claude-future-9"]) is None


def test_project_dir_names_the_repo():
    assert st.project_dir("/home/u/a b").endswith("projects/-home-u-a-b")
