import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("doc_index", ROOT / "tools/doc_index.py")
di = importlib.util.module_from_spec(spec)
spec.loader.exec_module(di)


def test_heading_and_first_sentence():
    t = "# 0033 — Water first\n\n**Date:** now\n\nThe world is [rebuilt](x.md) once. More text.\n"
    assert di.purpose(t) == "0033 — Water first — The world is rebuilt once."


def test_purpose_line_wins():
    assert di.purpose("# H\n\npurpose: the thing\n\nBody.") == "the thing"


def test_heading_only_and_cap():
    assert di.purpose("# Only heading\n") == "Only heading"
    assert len(di.purpose("# H\n\n" + "word " * 100 + ".")) <= di.MAX


def test_check_goes_stale(tmp_path, monkeypatch):
    monkeypatch.setattr(di, "ROOT", tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "world").mkdir()
    (tmp_path / "world/IMPORTED_FROM.md").write_text("# Imported\n")
    (tmp_path / "docs/a.md").write_text("# A\n\nFirst.\n")
    assert di.main(["--write"]) == 0
    assert di.main(["--check"]) == 0
    (tmp_path / "docs/b.md").write_text("# B\n")
    assert di.main(["--check"]) == 1
    di.main(["--write"])
    (tmp_path / "docs/b.md").write_text("# B2\n")
    assert di.main(["--check"]) == 1
