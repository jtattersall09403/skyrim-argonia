"""The 0030 migrator never rebuilds a table another tool owns: re-running it leaves formid.jsonl byte-identical."""
import pytest

from tools.argonia_world import db

run = pytest.importorskip("tools.argonia_world.migrate_0030.run")


def test_rerun_keeps_formid():
    live = (db.REPO / db.DB_DIR / "formid.jsonl").read_bytes()
    assert run.main(["--no-write"]) == 0
    out = db.REPO / "out" / "migrate" / db.DB_DIR / "formid.jsonl"
    assert out.read_bytes() == live
    assert (db.REPO / db.DB_DIR / "formid.jsonl").read_bytes() == live
