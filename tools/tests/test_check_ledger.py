"""tools/check_ledger.py: the check ledgers' format and evidence (L1), and run_batch's end-of-run rewrite."""
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from tools import check_ledger as cl  # noqa: E402

HEAD = "| Check | From | Level | Status | Evidence |\n|---|---|---|---|---|\n"


def make_repo(tmp_path, rows: str, batch=("a",)):
    r = tmp_path / "repo"
    (r / "tests" / "journeys" / "batches").mkdir(parents=True)
    (r / "docs" / "phases" / "1-x").mkdir(parents=True)
    (r / "docs" / "research").mkdir(parents=True)
    for j in ("a", "b"):
        (r / "tests" / "journeys" / f"{j}.yaml").write_text(f"id: {j}\n")
    (r / "tests" / "journeys" / "batches" / "all.yaml").write_text(
        "id: all\nitems:\n" + "".join(f"  - {j}\n" for j in batch))
    (r / "docs" / "owner-brief.md").write_text("| Date | Ruling |\n|---|---|\n| 2026-10-30 | No soak. |\n")
    (r / "docs" / "research" / "lane.md").write_text("one\ntwo\n")
    subprocess.run(["git", "init", "-q", str(r)], check=True)
    subprocess.run(["git", "-C", str(r), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q",
                    "--allow-empty", "-m", "x"], check=True)
    sha = subprocess.run(["git", "-C", str(r), "rev-parse", "--short=7", "HEAD"], capture_output=True,
                         text=True).stdout.strip()
    (r / "docs" / "phases" / "1-x" / "checks.md").write_text(
        "# Ledger\n\n## 1.1 A chunk\n\n" + HEAD + rows.replace("SHA", sha))
    return r


GOOD = ("| a passes | 1.1 | L4 | proven | journey:a pass out/batch/all/20261031T010203 |\n"
        "| b owed | 1.1 | L4 | owed | journey:b |\n"
        "| from a report | 1.1 | L4 | proven | docs/research/lane.md:2 |\n"
        "| from a commit | 1.1 | L5 | proven | SHA |\n"
        "| a soak | 1.1 | L4 | dropped | owner-brief:2026-10-30 |\n")


def test_good_ledger_passes(tmp_path):
    assert cl.check(make_repo(tmp_path, GOOD)) == []


def test_seeded_bad_rows_fail(tmp_path):
    bad = GOOD + ("| bad status | 1.1 | L4 | done | journey:a |\n"
                  "| no evidence | 1.1 | L4 | proven |  |\n"
                  "| journey without its run | 1.1 | L4 | proven | journey:a |\n"
                  "| unknown journey | 1.1 | L4 | owed | journey:nope |\n"
                  "| missing report | 1.1 | L4 | proven | docs/research/gone.md:3 |\n"
                  "| line past the end | 1.1 | L4 | proven | docs/research/lane.md:9 |\n"
                  "| missing commit | 1.1 | L4 | proven | deadbee1 |\n"
                  "| dropped, no ruling | 1.1 | L4 | dropped | docs/research/lane.md |\n"
                  "| undated ruling | 1.1 | L4 | dropped | owner-brief:2026-01-01 |\n")
    errs = cl.check(make_repo(tmp_path, bad))
    text = "\n".join(errs)
    for want in ("Status 'done'", "proven needs evidence", "needs its `pass out/...` run", "journey:nope",
                 "gone.md:3 does not resolve", "lane.md:9 does not resolve", "commit deadbee1",
                 "dropped needs owner-brief", "owner-brief:2026-01-01"):
        assert want in text, (want, errs)
    assert len(errs) == 9


def test_batch_journey_missing_from_every_ledger_fails(tmp_path):
    errs = cl.check(make_repo(tmp_path, GOOD.replace("journey:b |", "x |"), batch=("a", "b")))
    assert errs == ["tests/journeys/batches/all.yaml: journey b is in no ledger"]


def test_cli_on_the_repo_ledgers_exits_0():
    r = subprocess.run([sys.executable, str(REPO / "tools" / "check_ledger.py")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout


def test_update_sets_proven_and_owed_and_keeps_dropped():
    text = ("## 1.5 X\n\n" + HEAD
            + "| whole | 1.5 | L4 | owed | journey:a |\n"
              "| was proven | 1.5 | L4 | proven | journey:b pass out/batch/all/20261030T000000 |\n"
              "| steps passed | 1.5 | L4 | owed | journey:c#take |\n"
              "| steps not reached | 1.5 | L4 | proven | journey:c#later pass out/batch/all/20261030T000000 |\n"
              "| dropped | 1.5 | L4 | dropped | journey:a owner-brief:2026-10-30 |\n")
    res = {"a": {"passed": True, "run": "out/batch/all/20261031T010203/01-a-1", "steps": []},
           "b": {"passed": False, "run": "out/batch/all/20261031T010203/02-b-1", "steps": []},
           "c": {"passed": False, "run": "out/batch/all/20261031T010203/03-c-1",
                 "steps": [{"name": "take-pile", "passed": True}, {"name": "die", "passed": False}]}}
    new, n = cl.update_text(text, res)
    rows = {c[0]: c for _, _, c in cl.rows(new)}
    assert n == 3
    assert rows["whole"][3:] == ["proven", "journey:a pass out/batch/all/20261031T010203/01-a-1"]
    assert rows["was proven"][3:] == ["owed", "journey:b fail out/batch/all/20261031T010203/02-b-1"]
    assert rows["steps passed"][3] == "proven"
    assert rows["steps not reached"][3] == "proven"  # untouched: the run never reached those steps
    assert rows["dropped"][3] == "dropped"
    assert cl.update_text(new, res) == (new, 0)
