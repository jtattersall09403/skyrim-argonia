"""L2 (decision 0037): the restage resumes. A build VM killed mid-stage (spot reclaim) leaves step marks on disk; a
rerun skips the done steps, redoes a cut one and starts clean on a changed key; one inner rar is on disk at a time. The push resends only unsent parts."""
import os
import pathlib
import stat
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "infra" / "gpu-box"))
import stack  # noqa: E402

M = {"id": "bmv", "nested": ["Data1.rar", "Data2.rar"]}


class Killed(Exception):
    pass


def rig(tmp_path, size=4):
    calls = []

    def get_fn(m, archive, name, dest):
        calls.append("get " + name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(name)
        return dest

    def list_fn(inner):
        return {inner.name + ".out": size}

    def unrar(inner, data):
        calls.append(inner.name)
        (data / (inner.name + ".out")).write_text("laid")
        if os.environ.get("KILL_AT") == inner.name:
            raise Killed

    return calls, get_fn, unrar, list_fn


def run_stage(tmp_path, key, get_fn, unrar, list_fn):
    return stack.stage_nested(M, key, tmp_path / "a.tar", tmp_path / "work", tmp_path / "data",
                              tmp_path / "progress" / "bmv.json", get_fn, unrar, list_fn)


def test_resume_skips_done_steps(tmp_path, monkeypatch):
    calls, get, unrar, ls = rig(tmp_path)
    monkeypatch.setenv("KILL_AT", "Data2.rar")  # killed during the second rar
    with pytest.raises(Killed):
        run_stage(tmp_path, "k1", get, unrar, ls)
    assert calls == ["get Data1.rar", "Data1.rar", "get Data2.rar", "Data2.rar"]
    assert not list((tmp_path / "work").iterdir())  # each inner rar is deleted, laid or cut
    monkeypatch.delenv("KILL_AT")
    calls.clear()
    r = run_stage(tmp_path, "k1", get, unrar, ls)  # the rerun: Data1 kept, Data2 fetched and laid again
    assert calls == ["get Data2.rar", "Data2.rar"] and not r.fresh
    assert (tmp_path / "data" / "Data1.rar.out").exists()


def test_changed_key_starts_clean(tmp_path):
    calls, get, unrar, ls = rig(tmp_path)
    run_stage(tmp_path, "k1", get, unrar, ls)
    (tmp_path / "data" / "stale").write_text("old")
    calls.clear()
    run_stage(tmp_path, "k2", get, unrar, ls)
    assert calls == ["get Data1.rar", "Data1.rar", "get Data2.rar", "Data2.rar"]
    assert not (tmp_path / "data" / "stale").exists()


def test_room_refuses_a_lay_before_the_disk_fills(tmp_path, monkeypatch):
    """The peak is the laid copy plus one inner rar: room is asked for what the rar lays before unrar runs."""
    calls, get, unrar, ls = rig(tmp_path, size=6 << 30)
    monkeypatch.setattr(stack.shutil, "disk_usage", lambda p: type("U", (), {"free": 12 << 30})())
    with pytest.raises(SystemExit, match="lay Data1.rar"):
        run_stage(tmp_path, "k1", get, unrar, ls)
    assert calls == ["get Data1.rar"] and not (tmp_path / "work" / "Data1.rar").exists()


def test_inner_archive_from_the_tar_or_the_cache(tmp_path, monkeypatch):
    import tarfile
    src = tmp_path / "src" / "x"
    src.mkdir(parents=True)
    (src / "Data1.rar").write_bytes(b"one" * 1000)
    (src / "Data2.rar").write_bytes(b"two" * 3000)
    tar = tmp_path / "vault-bmv.tar"
    with tarfile.open(tar, "w") as tf:
        tf.add(src.parent, arcname="top")
    got = stack.inner_archive(M, tar, "data2.RAR", tmp_path / "w" / "Data2.rar")
    assert got.read_bytes() == b"two" * 3000

    class Fake(stack.CachedArchive):  # the cache read by range, here from the same tar
        def __init__(self, name):
            self.pos, self.size = 0, tar.stat().st_size

        def get(self, start, n, dest):
            with open(tar, "rb") as f:
                f.seek(start)
                pathlib.Path(dest).write_bytes(f.read(n))
    monkeypatch.setattr(stack, "CachedArchive", Fake)
    got = stack.inner_archive(M, tmp_path / "absent" / "vault-bmv.tar", "Data2.rar", tmp_path / "w2" / "Data2.rar")
    assert got.read_bytes() == b"two" * 3000
    with pytest.raises(SystemExit, match="Data3.rar not in"):
        stack.inner_archive(M, tar, "Data3.rar", tmp_path / "w" / "Data3.rar")


def test_complete_reads_kept_listings_and_fetches_a_missing_one(tmp_path, monkeypatch):
    calls, get, unrar, ls = rig(tmp_path)
    r = run_stage(tmp_path, "k1", get, unrar, ls)
    r.listing("Data1.rar").unlink()  # laid by an older stage that kept no listing
    calls.clear()
    monkeypatch.setattr(stack, "inner_archive", get)
    monkeypatch.setattr(stack, "rar_listing", ls)
    stack.complete_nested(M, tmp_path / "a.tar", tmp_path / "data", tmp_path / "work", r)
    assert calls == ["get Data1.rar"]
    (tmp_path / "data" / "Data2.rar.out").unlink()
    with pytest.raises(SystemExit, match="1 archive files not laid"):
        stack.complete_nested(M, tmp_path / "a.tar", tmp_path / "data", tmp_path / "work", r)
    r.clear()
    assert not list((tmp_path / "progress").iterdir())


def test_rar_listing_reads_each_file_block(monkeypatch):
    out = ("Archive: x.rar\nDetails: RAR 5\n\n        Name: Meshes\\a.nif\n        Type: File\n        Size: 196412\n"
           " Packed size: 1\n\n        Name: Meshes\n        Type: Directory\n\n        Name: b.dds\n        Type: File\n"
           "        Size: 7\n")
    monkeypatch.setattr(stack.subprocess, "run", lambda *a, **k: type("R", (), {"stdout": out})())
    assert stack.rar_listing("x.rar") == {"Meshes/a.nif": 196412, "b.dds": 7}


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
