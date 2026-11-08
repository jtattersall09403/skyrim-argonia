"""L2 (decision 0037): the restage resumes. A build VM killed mid-stage (spot reclaim) leaves step marks on disk; a
rerun skips the done steps, redoes a cut one and starts clean on a changed key. The push resends only unsent parts."""
import os
import stat
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "infra" / "gpu-box"))
import stack  # noqa: E402

M = {"id": "bmv", "nested": ["Data1.rar", "Data2.rar"]}


class Killed(Exception):
    pass


def rig(tmp_path):
    calls = []

    def unpack_fn(archive, dest):
        calls.append("unpack")
        (dest / "x").mkdir(parents=True)
        (dest / "x" / "Data1.rar").write_text("1")
        (dest / "x" / "Data2.rar").write_text("2")

    def unrar(inner, data):
        calls.append(inner.name)
        (data / (inner.name + ".out")).write_text("laid")
        if os.environ.get("KILL_AT") == inner.name:
            raise Killed

    return calls, unpack_fn, unrar


def run_stage(tmp_path, key, unpack_fn, unrar):
    return stack.stage_nested(M, key, tmp_path / "a.tar", tmp_path / "src", tmp_path / "data",
                              tmp_path / "progress" / "bmv.json", unpack_fn, unrar)


def test_resume_skips_done_steps(tmp_path, monkeypatch):
    calls, up, unrar = rig(tmp_path)
    monkeypatch.setenv("KILL_AT", "Data2.rar")  # killed during the second rar
    with pytest.raises(Killed):
        run_stage(tmp_path, "k1", up, unrar)
    assert calls == ["unpack", "Data1.rar", "Data2.rar"]
    monkeypatch.delenv("KILL_AT")
    calls.clear()
    r = run_stage(tmp_path, "k1", up, unrar)  # the rerun: no unpack, no Data1, Data2 redone
    assert calls == ["Data2.rar"] and not r.fresh
    assert (tmp_path / "data" / "Data1.rar.out").exists()  # the first rar's files were kept


def test_changed_key_starts_clean(tmp_path):
    calls, up, unrar = rig(tmp_path)
    run_stage(tmp_path, "k1", up, unrar)
    (tmp_path / "data" / "stale").write_text("old")
    calls.clear()
    run_stage(tmp_path, "k2", up, unrar)
    assert calls == ["unpack", "Data1.rar", "Data2.rar"]
    assert not (tmp_path / "data" / "stale").exists()


def test_mark_survives_cut_write(tmp_path):
    r = stack.Resume(tmp_path / "p.json", "k")
    r.mark("unpack")
    (tmp_path / "p.tmp").write_text("{half")  # a kill mid-write of the next mark leaves only the .tmp
    assert stack.Resume(tmp_path / "p.json", "k").done("unpack")
    r.clear()
    assert stack.Resume(tmp_path / "p.json", "k").fresh


def test_part_markers_keep_only_what_the_machine_holds(tmp_path):
    d = tmp_path / "d"
    d.mkdir()
    (d / "m.tar.000").write_text("100")
    (d / "m.tar.001").write_text("100")
    (d / "m.tar.002").write_text("100")
    kept = stack.part_markers(d, {"m.tar.000": 100, "m.tar.001": 7})  # 001 cut short, 002 gone
    assert kept == {"m.tar.000": 100} and sorted(p.name for p in d.iterdir()) == ["m.tar.000"]


def test_send_tar_resends_only_unmarked_parts(tmp_path, monkeypatch):
    src, out, machine = tmp_path / "src", tmp_path / "out", tmp_path / "machine"
    src.mkdir(), out.mkdir(), machine.mkdir()
    for i in range(3):
        (src / f"f{i}.bin").write_bytes(os.urandom(3000))
    fake = tmp_path / "run.sh"  # put copies the file to the fake machine; a flag file makes it fail
    fake.write_text(f'#!/bin/bash\n[ "$1" = put ] || exit 0\n[ -e {tmp_path}/fail ] && exit 1\ncp "$2" {machine}/\n')
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setattr(stack, "RUN", str(fake))
    monkeypatch.setattr(stack, "PART", 4096)
    monkeypatch.setattr(stack, "machine_part_sizes",
                        lambda n: {p.name: p.stat().st_size for p in machine.glob(f"{n}.tar.*")})
    monkeypatch.setattr(stack, "run", lambda *a, **k: "")
    stack.send_tar(src, out, "m", "d1")
    first = sorted(p.name for p in machine.iterdir())
    assert len(first) >= 2
    (machine / first[-1]).unlink()  # the last part lost with the reclaim, and its marker too
    (out / "parts" / "m-d1" / first[-1]).unlink()
    seen = []
    real = stack.part_markers
    monkeypatch.setattr(stack, "part_markers", lambda d, s: seen.append(sorted(s)) or real(d, s))
    stack.send_tar(src, out, "m", "d1")
    assert sorted(p.name for p in machine.iterdir()) == first  # only the lost part came back
    stack.send_tar(src, out, "m", "d2")  # new content: markers of d1 are dropped
    assert not (out / "parts" / "m-d1").exists()


def test_rerun_after_tar_removed(tmp_path):
    # every rar laid, then the caller removed the unpacked tar and a later check failed (2026-11-08): the rerun lays
    # nothing and needs no tar
    import shutil
    calls, up, unrar = rig(tmp_path)
    run_stage(tmp_path, "k1", up, unrar)
    shutil.rmtree(tmp_path / "src")
    calls.clear()
    r = run_stage(tmp_path, "k1", up, unrar)
    assert calls == [] and not r.fresh


def test_rerun_with_rar_left_and_tar_gone_unpacks_again(tmp_path, monkeypatch):
    import shutil
    calls, up, unrar = rig(tmp_path)
    monkeypatch.setenv("KILL_AT", "Data2.rar")
    with pytest.raises(Killed):
        run_stage(tmp_path, "k1", up, unrar)
    monkeypatch.delenv("KILL_AT")
    shutil.rmtree(tmp_path / "src")
    calls.clear()
    run_stage(tmp_path, "k1", up, unrar)
    assert calls == ["unpack", "Data2.rar"]
