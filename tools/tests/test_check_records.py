"""tools/check_records.py: green on agreeing records, red on each kind of stale row (owner, 2026-10-31)."""
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import check_records as cr  # noqa: E402

README = """# Part 0
| Id | Chunk | Depends on | Status |
|---|---|---|---|
| 0.1 | [One](0.1-one.md) | - | {a} |
| 0.2 | [Two](0.2-two.md) | 0.1 | todo |
"""
PROGRESS = """# Progress
| Part | Chunk | Title | Status |
|---|---|---|---|
| 0 | 0.1 | One | {row} |
| 0 | 0.2 | Two | todo |
"""


def tree(tmp: pathlib.Path, row: str, a: str = "done", ledger: str | None = None) -> pathlib.Path:
    (tmp / "docs/phases/0-x").mkdir(parents=True, exist_ok=True)
    (tmp / "docs/research/d").mkdir(parents=True, exist_ok=True)
    (tmp / "infra/gpu-box").mkdir(parents=True, exist_ok=True)
    (tmp / "docs/research/d/lane-game-7.md").write_text("x")
    (tmp / "docs/research/d/lane-game-9.md").write_text("x")
    (tmp / "infra/gpu-box/machines.conf").write_text("#name region address\nargonia-play eu-west-3 public\n")
    (tmp / "docs/phases/0-x/README.md").write_text(README.format(a=a))
    (tmp / "docs/phases/0-x/0.1-one.md").write_text(f"# One\n\n**Status.** {a}.\n")
    (tmp / "docs/PROGRESS.md").write_text(PROGRESS.format(row=row))
    if ledger:
        (tmp / "docs/phases/0-x/checks.md").write_text(ledger)
    subprocess.run(["git", "init", "-q", str(tmp)], check=True)
    subprocess.run(["git", "-C", str(tmp), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(tmp), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"], check=True)
    return tmp


def head(tmp):
    return subprocess.run(["git", "-C", str(tmp), "rev-parse", "--short=8", "HEAD"], capture_output=True,
                          text=True).stdout.strip()


def test_agreeing_records_pass(tmp_path):
    t = tree(tmp_path, "done (lane-game-9.md)")
    errs, notes = cr.check(t)
    assert errs == [] and notes  # no ledger: the owed check is skipped and says so


def test_seeded_stale_rows_fail(tmp_path):
    t = tree(tmp_path, "done (L4 [from batch], game-7; LOD by the Creation Kit on the g4dn; lane-gone; argonia-play-2)")
    text = "\n".join(cr.check(t)[0])
    for want in ("[from batch]", "bare game-7", "xLODGen", "g4dn", "lane-gone has no report", "argonia-play-2"):
        assert want in text, want


def test_status_word_mismatch_and_no_evidence_fail(tmp_path):
    t = tree(tmp_path, "in progress (nothing cited)", a="done")
    text = "\n".join(cr.check(t)[0])
    assert "PROGRESS says 'in progress'" in text and "cites no evidence" in text


def test_unknown_commit_fails_and_known_passes(tmp_path):
    t = tree(tmp_path, "done (deadbee1)")
    assert any("deadbee1 is unknown" in e for e in cr.check(t)[0])
    (t / "docs/PROGRESS.md").write_text(PROGRESS.format(row=f"done ({head(t)})"))
    assert cr.check(t)[0] == []


def test_done_with_owed_ledger_row_fails(tmp_path):
    ledger = "## 0.1 One\n\n| Check | From | Level | Status | Evidence |\n|---|---|---|---|---|\n| cosave | 0.1 | L4 | owed | |\n"
    t = tree(tmp_path, "done (lane-game-9.md)", ledger=ledger)
    assert any("done but its ledger owes: cosave" in e for e in cr.check(t)[0])
    (t / "docs/phases/0-x/checks.md").write_text(ledger.replace("| owed | |", "| proven | lane-game-9.md |"))
    assert cr.check(t)[0] == []


def test_the_repo_records_pass():
    errs, _ = cr.check()
    assert errs == [], errs
