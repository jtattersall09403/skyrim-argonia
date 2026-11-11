"""tooling/tidy.py: a lane worktree goes only when its content is on main, compared by content; the bucket keeps
what is referenced or newest; a job's spool goes only once the job has ended and aged."""
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tidy  # noqa: E402

ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@t", "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"}


def g(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True, env=ENV).stdout.strip()


def write(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A bare origin, a main tree with a few files; lane() adds a worktree on its own branch."""
    for k, v in ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setattr(tidy, "JOBS", tmp_path / "jobs")
    (tmp_path / "jobs").mkdir()
    origin, main = tmp_path / "o.git", tmp_path / "main"
    g(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    g(tmp_path, "clone", "-q", str(origin), str(main))
    g(main, "checkout", "-q", "-B", "main")
    write(main / "doc.md", "".join(f"line {i} of the plan stays as it is\n" for i in range(30)))
    write(main / "code.py", "def a():\n    return 1\n")
    write(main / "plugin/Argonia/Npcs/Old - 000001_Argonia.esp.yaml", "FormKey: 000001\n")
    g(main, "add", "-A")
    g(main, "commit", "-qm", "base")
    g(main, "push", "-q", "origin", "HEAD:main")
    g(main, "fetch", "-q", "origin")
    return main


def lane(main, name):
    wt = main / ".claude/worktrees" / name
    g(main, "worktree", "add", "-q", "-b", f"worktree-{name}", str(wt), "origin/main")
    return wt


def land_on_main(main, *lane_commits, before=None):
    """Main moves first (another lane's commit), then takes the lane's commits by cherry-pick: new ids."""
    write(main / "other.txt", f"another lane {time.time()}\n")
    g(main, "add", "other.txt")
    g(main, "commit", "-qm", "another lane")
    if before:
        before()
    for c in lane_commits:
        g(main, "cherry-pick", c)
    g(main, "push", "-q", "origin", "HEAD:main")
    g(main, "fetch", "-q", "origin")


def test_landed_by_rebase_with_new_ids(repo):
    wt = lane(repo, "a")
    write(wt / "code.py", "def a():\n    return 2\n")
    write(wt / "new.py", "x = 1\n")
    g(wt, "add", "-A")
    g(wt, "commit", "-qm", "lane a")
    c = g(wt, "rev-parse", "HEAD")
    assert [f for f, _ in tidy.unlanded(repo, wt)] == ["code.py", "new.py"]  # before it lands
    land_on_main(repo, c)
    assert g(repo, "rev-parse", "origin/main") != c
    assert tidy.unlanded(repo, wt) == []


def test_landed_then_main_moved_on(repo):
    """Main took the lane's change, then rewrote the same lines: the lane's version is in main's history."""
    wt = lane(repo, "a")
    write(wt / "code.py", "def a():\n    return 2\n")
    g(wt, "commit", "-qam", "lane a")
    land_on_main(repo, g(wt, "rev-parse", "HEAD"))
    write(repo / "code.py", "def a():\n    return 3  # later work\n")
    g(repo, "commit", "-qam", "later")
    g(repo, "push", "-q", "origin", "HEAD:main")
    g(repo, "fetch", "-q", "origin")
    assert tidy.unlanded(repo, wt) == []


def test_landed_among_parallel_edits_to_the_same_paragraph(repo):
    """The landing resolved a conflict: main never held the lane's exact file, but holds every clause it added."""
    wt = lane(repo, "a")
    write(wt / "doc.md", (wt / "doc.md").read_text().replace(
        "line 5 of the plan stays as it is\n", "line 5 of the plan: the placement check reads 120 actors; some routes are long.\n"))
    g(wt, "commit", "-qam", "lane a")
    text = (repo / "doc.md").read_text().replace(
        "line 5 of the plan stays as it is\n",
        "line 5 of the plan: the placement check reads 120\n  actors; and a clause main added in parallel.\n")
    write(repo / "doc.md", text)
    g(repo, "commit", "-qam", "landed by hand, re-wrapped, one clause replaced")
    g(repo, "push", "-q", "origin", "HEAD:main")
    g(repo, "fetch", "-q", "origin")
    left = tidy.unlanded(repo, wt)
    assert [f for f, _ in left] == ["doc.md"]  # "some routes are long." never reached main: real, kept
    write(repo / "doc.md", text.replace("in parallel.\n", "in parallel. some routes are long.\n"))
    g(repo, "commit", "-qam", "the last clause")
    g(repo, "push", "-q", "origin", "HEAD:main")
    g(repo, "fetch", "-q", "origin")
    assert tidy.unlanded(repo, wt) == []


def test_uncommitted_generated_files_superseded_by_a_later_run(repo):
    wt = lane(repo, "a")
    old = time.time() - 3600
    # the lane's build regenerated the record tree: a renamed record (form id in the name), never committed
    (wt / "plugin/Argonia/Npcs/Old - 000001_Argonia.esp.yaml").unlink()
    f = wt / "plugin/Argonia/Npcs/Old - 000002_Argonia.esp.yaml"
    write(f, "FormKey: 000002\n")
    os.utime(f, (old, old))
    write(wt / "doc.md", (repo / "doc.md").read_text())  # touched, identical to main
    assert [x for x, _ in tidy.unlanded(repo, wt)] == [
        "plugin/Argonia/Npcs/Old - 000001_Argonia.esp.yaml", "plugin/Argonia/Npcs/Old - 000002_Argonia.esp.yaml"]
    # main's later run of the generator
    g(repo, "mv", "plugin/Argonia/Npcs/Old - 000001_Argonia.esp.yaml", "plugin/Argonia/Npcs/Old - 000003_Argonia.esp.yaml")
    g(repo, "commit", "-qam", "plugin regenerated")
    g(repo, "push", "-q", "origin", "HEAD:main")
    g(repo, "fetch", "-q", "origin")
    assert tidy.unlanded(repo, wt) == []


def test_real_unlanded_work_is_kept(repo):
    wt = lane(repo, "a")
    write(wt / "code.py", "def a():\n    return 2\n")
    g(wt, "commit", "-qam", "lane a, never landed")
    write(wt / "notes.md", "an untracked file nobody committed\n")
    write(wt / "doc.md", (wt / "doc.md").read_text() + "an uncommitted paragraph of real work\n")
    land_on_main(repo)  # main moves on without it, and edits the same hand-written file elsewhere
    assert sorted(f for f, _ in tidy.unlanded(repo, wt)) == ["code.py", "doc.md", "notes.md"]
    # the snapshot never touched the lane's own index or files
    assert g(wt, "diff", "--cached", "--name-only") == "" and g(wt, "diff", "--name-only") == "doc.md"
    assert g(wt, "ls-files", "-o", "--exclude-standard") == "notes.md"


def test_hand_file_is_not_superseded_by_date(repo):
    """Only generated trees count as landed because main changed them later; a hand-written file never does."""
    wt = lane(repo, "a")
    f = wt / "code.py"
    write(f, "def a():\n    return 2\n")
    os.utime(f, (time.time() - 3600,) * 2)
    write(repo / "code.py", "def a():\n    return 1\n\n\ndef b():\n    return 5\n")
    g(repo, "commit", "-qam", "main edits the same file later")
    g(repo, "push", "-q", "origin", "HEAD:main")
    g(repo, "fetch", "-q", "origin")
    assert [x for x, _ in tidy.unlanded(repo, wt)] == ["code.py"]


def test_tidy_removes_landed_and_keeps_unlanded(repo, monkeypatch):
    done, kept = lane(repo, "done"), lane(repo, "kept")
    write(done / "code.py", "def a():\n    return 2\n")
    g(done, "commit", "-qam", "lane done")
    write(done / "out.log", "left behind, ignored by nobody\n")
    write(kept / "doc.md", (kept / "doc.md").read_text() + "work that never landed\n")

    def also_out_log():
        write(repo / "out.log", "left behind, ignored by nobody\n")
        g(repo, "add", "out.log")
        g(repo, "commit", "-qm", "the log too")

    land_on_main(repo, g(done, "rev-parse", "HEAD"), before=also_out_log)
    lines = []
    # fresh worktrees are not idle yet: nothing goes
    monkeypatch.setattr(tidy, "IDLE_H", 3)
    assert tidy.tidy_worktrees(repo, False, True, lines.append) == [] and done.is_dir()
    monkeypatch.setattr(tidy, "IDLE_H", 0)
    monkeypatch.setattr(tidy, "LOUD_H", 1e9)
    dry = tidy.tidy_worktrees(repo, True, True, lines.append)
    assert done.is_dir() and any("would remove worktree done" in s for s in dry)
    said = tidy.tidy_worktrees(repo, False, True, lines.append)
    assert not done.exists() and kept.is_dir()
    assert "worktree-done" not in g(repo, "branch", "--list") and "worktree-kept" in g(repo, "branch", "--list")
    assert any("removed worktree done" in s for s in said)
    k = next(s for s in said if "keep kept" in s)
    assert "doc.md" in k and "ABANDONED" not in k
    monkeypatch.setattr(tidy, "LOUD_H", 0)
    assert any(s.startswith("ABANDONED WORK") for s in tidy.tidy_worktrees(repo, False, True, lines.append))
    # a lane branch whose worktree someone removed by hand: the same rule on its tip
    g(repo, "branch", "worktree-gone-landed", g(repo, "rev-parse", "origin/main~1"))
    gone = lane(repo, "gone")
    write(gone / "code.py", "def never_landed():\n    return 9\n")
    g(gone, "commit", "-qam", "never landed")
    g(repo, "worktree", "remove", "--force", str(gone))
    said = tidy.tidy_worktrees(repo, False, True, lines.append)
    branches = g(repo, "branch", "--list")
    assert "worktree-gone-landed" not in branches and "worktree-gone" in branches
    assert any("keep branch worktree-gone " in s and "code.py" in s for s in said)
    # a second run changes nothing
    assert kept.is_dir() and (kept / "doc.md").read_text().endswith("work that never landed\n")


def test_in_use_worktree_is_kept_and_interrupted_removal_finishes(repo, monkeypatch):
    monkeypatch.setattr(tidy, "IDLE_H", 0)
    wt = lane(repo, "a")
    # a job_guard job started from it
    for ext, text in (("state", "running"), ("pid", str(os.getpid())), ("cwd", str(wt / "sub"))):
        (tidy.JOBS / f"build.{ext}").write_text(text)
    lines = []
    tidy.tidy_worktrees(repo, False, False, lines.append)
    assert wt.is_dir() and any("job build runs from it" in s for s in lines)
    (tidy.JOBS / "build.state").write_text("done")
    # a live session's lock, then a dead session's
    g(repo, "worktree", "lock", "--reason", f"claude agent a (pid {os.getpid()})", str(wt))
    tidy.tidy_worktrees(repo, False, False, lines.append)
    assert wt.is_dir()
    g(repo, "worktree", "unlock", str(wt))
    g(repo, "worktree", "lock", "--reason", "claude agent a (pid 2147483646 start 1)", str(wt))
    # a removal that was cut off after its proof: half the files gone, the marker there
    gd = Path(g(wt, "rev-parse", "--path-format=absolute", "--git-dir"))
    (gd / "tidy-landed").write_text("x")
    (wt / "code.py").unlink()
    tidy.tidy_worktrees(repo, False, False, lines.append)
    assert not wt.exists() and "worktree-a" not in g(repo, "branch", "--list")


def obj(key, gb, days_old, now):
    return {"key": key, "size": int(gb * 2**30), "mtime": now - days_old * 86400}


def test_bucket_keeps_referenced_or_newest():
    now = time.time()
    objects = [obj(f"nw/terrain/{b}/heightmap.npy", 0.1, d, now) for b, d in
               (("20261101T000000Z", 10), ("20261105T000000Z", 6), ("20261109T204317Z", 2), ("20261111T100156Z", 0.5))]
    objects += [obj(f"nw/plugin/{b}/ArgoniaNewWorld.esm", 0.3, d, now) for b, d in
                (("20261105T000000Z", 6), ("20261109T204317Z", 2), ("20261111T100156Z", 0.5))]
    objects += [obj("nw/lod/aaaa.tar", 1.6, 5, now), obj("nw/lod/bbbb.tar", 1.6, 3, now), obj("nw/lod/cccc.tar", 1.6, 2, now)]
    objects += [obj("mods/big.7z", 15, 30, now), obj("nw/maps/map.png", 0.01, 30, now), obj("nw/lodmodels/k.tar", 0.2, 9, now)]
    refs = {"nw/terrain/": {"20261109T204317Z": "helstrom's held ground", "20261111T100156Z": "the current terrain build"},
            "nw/plugin/": {"20261109T204317Z": "the world file on the play machine"},
            "nw/lod/": {"bbbb": "the LOD on argonia-play"}}
    delete, keep, other = tidy.bucket_plan(objects, refs, now)
    assert sorted(n for n, *_ in delete) == ["nw/lod/aaaa", "nw/plugin/20261105T000000Z", "nw/terrain/20261101T000000Z",
                                              "nw/terrain/20261105T000000Z"]
    kept = {n: why for n, _, _, why in keep}
    assert kept["nw/terrain/20261109T204317Z"] == "helstrom's held ground"
    assert kept["nw/plugin/20261111T100156Z"] == "the newest there" and kept["nw/lod/cccc"] == "the newest there"
    assert kept["nw/lod/bbbb"] == "the LOD on argonia-play"
    assert set(other) == {"mods/", "nw/maps/", "nw/lodmodels/"}
    assert not any(k.startswith(("mods/", "nw/maps/", "nw/lodmodels/")) for _, _, keys, _ in delete for k in keys)


def test_bucket_grace_keeps_what_was_just_written():
    now = time.time()
    objects = [obj("nw/lod/old.tar", 1, 0.2, now), obj("nw/lod/new.tar", 1, 0.1, now), obj("nw/lod/ancient.tar", 1, 9, now)]
    delete, keep, _ = tidy.bucket_plan(objects, {}, now)
    assert [n for n, *_ in delete] == ["nw/lod/ancient"]
    assert {n: w for n, _, _, w in keep}["nw/lod/old"].startswith("written under")


def test_stale_jobs_spare_live_and_recent(tmp_path):
    now, old = time.time(), time.time() - 5 * 86400

    def job(name, state, rc=None, pid="2147483646", t=old):
        for ext, text in (("state", state), ("pid", pid), ("log", "x"), ("cmd", "x")) + ((("rc", rc),) if rc else ()):
            f = tmp_path / f"{name}.{ext}"
            f.write_text(text)
            os.utime(f, (t, t))

    job("old-done", "done", rc="0")
    job("old.dotted-name", "done", rc="1")
    job("old-cut-off", "running")            # no rc: job_resume.sh still owes it a relaunch
    job("old-alive", "running", pid=str(os.getpid()))
    job("fresh", "done", rc="0", t=now)
    for n in (".seq", ".seq.lock", "gpu.lock", "gpu.lock.slot", "RESUMED-new"):
        (tmp_path / n).write_text("1")
    (tmp_path / "RESUMED-old").write_text("1")
    os.utime(tmp_path / "RESUMED-old", (old, old))
    assert [n for n, _ in tidy.stale_jobs(tmp_path, now, 2)] == ["RESUMED-old", "old-done", "old.dotted-name"]


def test_a_live_sessions_scratch_is_never_removed(tmp_path):
    """A session's scratch folder goes only when no process of the session runs, its transcript has not been
    written for SESSION_DAYS and nothing in it changed for the scratch age."""
    now, old = time.time(), time.time() - 10 * 86400
    tmp, projects = tmp_path / "tmp", tmp_path / "projects"
    base = tmp / f"claude-{os.getuid()}" / "-home-proj"

    def session(sid, transcript_age_days=None, in_project="-home-proj", sub=False):
        f = base / sid / "scratchpad" / "run.sh"
        write(f, "x")
        for q in (f, f.parent, f.parent.parent):
            os.utime(q, (old, old))                      # the scratch itself is old in every case
        if transcript_age_days is not None:
            t = projects / in_project / (f"{sid}/subagents/a.jsonl" if sub else f"{sid}.jsonl")
            write(t, "{}")
            for q in (t, *(t.parents[:2] if sub else ())):
                os.utime(q, (now - transcript_age_days * 86400,) * 2)

    session("ended", transcript_age_days=10)
    session("no-transcript")
    session("waiting", transcript_age_days=1)            # silent for a day (a long job, the owner away): live
    session("other-project", transcript_age_days=0.1, in_project="-home-proj--claude-worktrees-x")
    session("only-subagents-write", transcript_age_days=0.1, sub=True)
    session("has-process", transcript_age_days=10)       # e.g. its hold job still runs
    got = {p.name for p, _ in tidy.stale_scratch(now, 2, tmp=tmp, projects=projects, procs={"has-process"})}
    assert got == {"ended", "no-transcript"}
    # scratch written a minute ago is kept even when the session cannot be found at all
    write(base / "no-transcript" / "scratchpad" / "new.sh", "x")
    got = {p.name for p, _ in tidy.stale_scratch(now, 2, tmp=tmp, projects=projects, procs=set())}
    assert got == {"ended", "has-process"}


def test_session_procs_reads_this_process_tree(monkeypatch):
    sid = "test-session-of-tidy"
    p = subprocess.Popen(["sleep", "30"], env={**os.environ, "CLAUDE_CODE_SESSION_ID": sid})
    try:
        assert sid in tidy.session_procs()
        assert tidy.session_live(sid, time.time(), tidy.session_procs(), projects=Path("/nonexistent"))
    finally:
        p.kill()
        p.wait()
    assert tidy.session_live(sid, time.time(), tidy.session_procs(), projects=Path("/nonexistent")) is None


def test_a_job_that_only_waits_is_left_out_on_request(tmp_path):
    def job(name, argv, cwd):
        (tmp_path / f"{name}.state").write_text("running\n")
        (tmp_path / f"{name}.pid").write_text(f"{os.getpid()}\n")
        (tmp_path / f"{name}.cmd").write_bytes(b"".join(a.encode() + b"\0" for a in argv))
        (tmp_path / f"{name}.cwd").write_text(f"{cwd}\n")

    job("hold", ["sleep", "14400"], "/main")
    job("hold2", ["/usr/bin/sleep", "4h"], "/main")
    job("build", ["tools/newworld/rebuild.sh", "run"], "/main")
    job("sleepy", ["bash", "-c", "sleep 5; make"], "/main")
    assert {n for n, _ in tidy.job_cwds(tmp_path)} == {"hold", "hold2", "build", "sleepy"}
    assert {n for n, _ in tidy.job_cwds(tmp_path, waits=False)} == {"build", "sleepy"}
