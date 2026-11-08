"""lodsettings.py: a world's .lod from its .btr names, in Valenwood.lod's layout; worlds with a .lod are left alone."""
import importlib.util
import pathlib
import struct

HERE = pathlib.Path(__file__).resolve().parents[2] / "infra" / "gpu-box" / "lodsettings.py"
spec = importlib.util.spec_from_file_location("lodsettings", HERE)
lod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lod)


def names(world, lo, hi_x, hi_y):
    out = []
    for lvl in (4, 8, 16, 32):
        out += [f"{world}.{lvl}.{x}.{y}.btr" for x in range(lo, hi_x + 1, lvl) for y in range(lo, hi_y + 1, lvl)]
    return out


def test_valenwood_rule_gives_bmv_own_file():
    # BM&V's Valenwood: level-32 chunks -32..32 both ways; its shipped .lod is e0ff e0ff 80000000 04000000 20000000
    assert lod.settings(names("valenwood", -32, 63, 63)) == bytes.fromhex("e0ffe0ff800000000400000020000000")


def test_strides_are_powers_of_two():
    assert struct.unpack("<hhiii", lod.settings(names("blackmarsh2", -32, 31, 31))) == (-32, -32, 64, 4, 32)
    assert struct.unpack("<hhiii", lod.settings(names("blackmarshnorth", -32, 31, 63))) == (-32, -32, 128, 4, 32)
    assert lod.settings(["readme.txt"]) is None


def test_derive_skips_worlds_with_a_lod(tmp_path):
    mods, out = tmp_path / "mods", tmp_path / "mods" / "argonia-lodsettings"
    for w in ("BlackMarsh", "Valenwood"):
        d = mods / "bmv" / "meshes" / "Terrain" / w
        d.mkdir(parents=True)
        for n in names(w.lower(), -64, 63, 63)[:3] + [f"{w.lower()}.32.-64.-64.btr", f"{w.lower()}.32.32.32.btr"]:
            (d / n).write_bytes(b"")
    (mods / "bmv" / "lodsettings").mkdir()
    (mods / "bmv" / "lodsettings" / "Valenwood.lod").write_bytes(b"x")
    made = lod.derive(mods, out)
    assert list(made) == ["BlackMarsh"]
    assert struct.unpack("<hhiii", (out / "LODSettings" / "BlackMarsh.lod").read_bytes()) == (-64, -64, 128, 4, 32)
