"""The 0030 migrator writes only the tables it migrates: a re-run leaves formid.jsonl and a table it does not know
byte-identical, and keeps a table block another lane appended to schema.sql."""
import pytest

from tools.argonia_world import db

run = pytest.importorskip("tools.argonia_world.migrate_0030.run")

FOREIGN = '\n-- Home of a test lane\'s rows.\nCREATE TABLE "zz_foreign" (\n  "id" TEXT NOT NULL PRIMARY KEY\n);\n'


def test_rerun_leaves_other_tables(tmp_path):
    (tmp_path / "world" / "db").mkdir(parents=True)
    (tmp_path / db.SCHEMA).write_text((db.REPO / db.SCHEMA).read_text() + FOREIGN)
    (tmp_path / db.DB_DIR / "zz_foreign.jsonl").write_text('{"id":"b"}\n{"id":"a"}\n')   # unsorted on purpose
    live = (db.REPO / db.DB_DIR / "formid.jsonl").read_bytes()
    assert run.main(["--root", str(tmp_path)]) == 0
    assert (tmp_path / db.DB_DIR / "formid.jsonl").read_bytes() == live
    assert (tmp_path / db.DB_DIR / "zz_foreign.jsonl").read_text() == '{"id":"b"}\n{"id":"a"}\n'
    schema = (tmp_path / db.SCHEMA).read_text()
    assert schema.count('CREATE TABLE "zz_foreign"') == 1 and schema.count(run.MARK) == 1
    assert run.main(["--root", str(tmp_path)]) == 0                       # idempotent, tail kept once
    assert (tmp_path / db.SCHEMA).read_text() == schema
    assert db.load(tmp_path).get("zz_foreign", "a") is not None
    assert (db.REPO / db.DB_DIR / "formid.jsonl").read_bytes() == live
