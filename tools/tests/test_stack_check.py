import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import stack_check as sc  # noqa: E402


def make_dll(exports, vdata=None):
    """Minimal PE32+ with one section at rva 0x1000 = file 0x400 holding the export table and data."""
    names = list(exports)
    sec = bytearray(0x600)
    base = 0x1000
    data_off = 0x300
    if vdata:
        sec[data_off:data_off + len(vdata)] = vdata
    nm_off = 0x200
    name_rvas = []
    for n in names:
        name_rvas.append(base + nm_off)
        sec[nm_off:nm_off + len(n) + 1] = n.encode() + b"\0"
        nm_off += len(n) + 1
    fn_t, nm_t, or_t = 0x80, 0xA0, 0xC0
    for i, n in enumerate(names):
        struct.pack_into("<I", sec, fn_t + 4 * i, base + data_off)
        struct.pack_into("<I", sec, nm_t + 4 * i, name_rvas[i])
        struct.pack_into("<H", sec, or_t + 2 * i, i)
    struct.pack_into("<IIIII", sec, 20, len(names), len(names), base + fn_t, base + nm_t, base + or_t)
    pe = 0x40
    hdr = bytearray(0x400)
    hdr[0:2] = b"MZ"
    struct.pack_into("<I", hdr, 0x3C, pe)
    hdr[pe:pe + 4] = b"PE\0\0"
    struct.pack_into("<HHIIIHH", hdr, pe + 4, 0x8664, 1, 0, 0, 0, 240, 0x2022)
    opt = pe + 24
    struct.pack_into("<H", hdr, opt, 0x20B)
    struct.pack_into("<II", hdr, opt + 112, base, 0x60)
    s = opt + 240
    hdr[s:s + 8] = b".rdata\0\0"
    struct.pack_into("<IIII", hdr, s + 8, 0x600, base, 0x600, 0x400)
    return bytes(hdr) + bytes(sec)


def vdata(ind, ex=0, compat=(), name="Test", dv=1):
    b = bytearray(848)
    struct.pack_into("<II", b, 0, dv, 0x01000010)
    b[8:8 + len(name)] = name.encode()
    struct.pack_into("<II", b, 772, ex, ind)
    for i, c in enumerate(compat):
        struct.pack_into("<I", b, 780 + 4 * i, c)
    return bytes(b)


def verdict(tmp_path, exports, vd=None):
    p = tmp_path / "x.dll"
    p.write_bytes(make_dll(exports, vd))
    info, err = sc.analyse_dll(p)
    return sc.judge(info)[0]


def test_pack():
    assert sc.pack_runtime(1, 7, 104) == 0x01070680


def test_version_data_verdicts(tmp_path):
    ok = vdata(sc.F_ADDRLIB | sc.F_STRUCT)
    assert verdict(tmp_path, ["SKSEPlugin_Version"], ok) == "loads"
    assert verdict(tmp_path, ["SKSEPlugin_Version"], vdata(sc.F_SIG)) == "refused"          # structs unsafe
    assert verdict(tmp_path, ["SKSEPlugin_Version"], vdata(sc.F_SIG, ex=sc.FX_NOSTRUCT)) == "loads"
    assert verdict(tmp_path, ["SKSEPlugin_Version"], vdata(0, compat=[sc.pack_runtime(1, 6, 1170)])) == "refused"
    assert verdict(tmp_path, ["SKSEPlugin_Version"], vdata(0, compat=[sc.pack_runtime(1, 7, 104)])) == "loads"


def test_legacy_and_non_plugin(tmp_path):
    assert verdict(tmp_path, ["SKSEPlugin_Query", "SKSEPlugin_Load"]) == "refused"
    assert verdict(tmp_path, ["Foo"]) == "unknown"


def tes4(masters):
    sub = b"".join(b"MAST" + struct.pack("<H", len(m) + 1) + m.encode() + b"\0" + b"DATA" + struct.pack("<H", 8) + bytes(8)
                   for m in masters)
    return b"TES4" + struct.pack("<IIIII", len(sub), 0, 0, 0, 0) + sub


def test_masters_and_conflicts(tmp_path):
    mods = tmp_path / "mods"
    for m in ("a", "b"):
        (mods / m).mkdir(parents=True)
    (mods / "a" / "A.esp").write_bytes(tes4(["Skyrim.esm", "B.esp"]))   # B is later: out of order
    (mods / "b" / "B.esp").write_bytes(tes4(["Missing.esm"]))
    rows = {n: i for n, _, i in sc.master_check(mods, ["a", "b"], ["A.esp", "B.esp"])}
    assert rows["A.esp"] == ["B.esp is later in the load order"]
    assert rows["B.esp"] == ["Missing.esm is missing"]
    (mods / "a" / "d").mkdir()
    (mods / "a" / "d" / "x.hkx").write_text("1")
    (mods / "b" / "D").mkdir()
    (mods / "b" / "D" / "X.hkx").write_text("2")
    assert sc.file_conflicts(mods, ["a", "b"]) == {("a", "b"): ["D/X.hkx"]}
