"""The push digest of a mod folder is its own row's staged files, not the merged profile records: a newworld row's
override at a play row's path must not hide an edit to the play row's copy."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "infra" / "gpu-box"))
import stack  # noqa: E402

OV = "skse\\plugins\\communityshaders\\overrides\\argonia_volumetriclighting.json"


def test_a_row_digest_covers_a_file_another_row_overrides(tmp_path):
    keys = tmp_path / "staged"
    keys.mkdir()
    (keys / "cs-height-fog.files.json").write_text(json.dumps({OV: "new"}))
    (keys / "community-shaders.files.json").write_text(json.dumps({OV: "a", "x.dll": "d"}))
    before = stack.row_digest(keys, "community-shaders")
    (keys / "community-shaders.files.json").write_text(json.dumps({OV: "b", "x.dll": "d"}))   # its own copy edited
    assert stack.row_digest(keys, "community-shaders") != before
    assert stack.row_digest(keys, "cs-height-fog") == stack.row_digest(keys, "cs-height-fog")
    assert stack.row_digest(keys, "absent") == stack.row_digest(keys, "also-absent")   # no record: the empty digest
