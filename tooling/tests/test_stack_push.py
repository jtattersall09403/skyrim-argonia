"""stack.py's push carries every file name (game-10: Windows tar skipped 20 non-ASCII names, so combat set A came
back with 20 files missing from Data)."""
import importlib.util
import pathlib
import stat
import tarfile
import zipfile

HERE = pathlib.Path(__file__).resolve().parents[2] / "infra" / "gpu-box" / "stack.py"
spec = importlib.util.spec_from_file_location("stack", HERE)
stack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stack)


def test_push_sends_wide_names_by_zip(tmp_path, monkeypatch):
    src, out, machine = tmp_path / "mod", tmp_path / "out", tmp_path / "machine"
    for p in (src / "Sound" / "Buff", out, machine):
        p.mkdir(parents=True)
    (src / "Sound" / "Buff" / "BuffMelee1.wav").write_bytes(b"a")
    (src / "Sound" / "Buff" / "BuffMelee1 - 副本.wav").write_bytes(b"b")
    (src / "deg °.txt").write_bytes(b"c")
    fake = tmp_path / "run.sh"  # `run.sh put FILE DEST`: copied to the "machine"
    fake.write_text(f'#!/bin/sh\n[ "$1" = put ] && cp "$2" "{machine}/"\n')
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setattr(stack, "RUN", str(fake))
    assert stack.wide_names(src) == ["Sound/Buff/BuffMelee1 - 副本.wav", "deg °.txt"]
    assert stack.send_tar(src, out, "m") == 2
    parts = sorted(machine.glob("m.tar.*"))
    (tmp_path / "m.tar").write_bytes(b"".join(p.read_bytes() for p in parts))
    with tarfile.open(tmp_path / "m.tar") as t:
        assert sorted(n for n in t.getnames() if t.getmember(n).isfile()) == ["./Sound/Buff/BuffMelee1.wav"]
    with zipfile.ZipFile(machine / "m.wide.zip") as z:
        infos = z.infolist()
        assert [i.filename for i in infos] == ["Sound/Buff/BuffMelee1 - 副本.wav", "deg °.txt"]
        assert all(i.flag_bits & 0x800 for i in infos)  # UTF-8 names, read exactly by .NET's ZipFile
        assert z.read("deg °.txt") == b"c"
    assert not list(out.iterdir())  # parts and zip removed once sent


def test_unpack_fails_loudly_and_lays_the_zip():
    s = stack.unpack_script("rim-parry")
    assert "if ($LASTEXITCODE)" in s and "exit 1" in s
    assert s.index("tar -xf") < s.index("ExtractToDirectory")
