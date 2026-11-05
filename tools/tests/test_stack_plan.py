"""L2: the stage's row stamp, shared by `stage` and deploy's pre-flight (`stack.py plan`). A row
stays staged while its key and files hold; a changed manifest entry is a stale stamp and re-stages; a note does not."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "infra" / "gpu-box"))
import stack  # noqa: E402


def test_stage_key_and_staged_ok(tmp_path):
    keys, mods, tools = tmp_path / "staged", tmp_path / "mods", tmp_path / "tools"
    for d in (keys, mods / "bmv", tools):
        d.mkdir(parents=True)
    m = {"id": "bmv", "group": "world", "file_id": 1}
    k = stack.stage_key(m)
    (keys / "bmv.json").write_text(json.dumps({"key": k, "fomod": []}))
    assert stack.staged_ok(m, k, keys, mods, tools)
    m2 = dict(m, file_id=2)  # a new archive: a stale stamp
    assert not stack.staged_ok(m2, stack.stage_key(m2), keys, mods, tools)
    noted = {**m, next(iter(stack.DOC_FIELDS)): "a note"}  # a doc field leaves the key alone
    assert stack.stage_key(noted) == k
    (mods / "bmv").rmdir()  # the files gone: re-stage
    assert not stack.staged_ok(m, k, keys, mods, tools)
