"""infra/gpu-box/backstep.py: the standing backstep's AMR root motion cut to its first push (owner, 2026-11-08)."""
import importlib.util
import pathlib
import struct

import pytest

spec = importlib.util.spec_from_file_location(
    "backstep", pathlib.Path(__file__).resolve().parents[2] / "infra" / "gpu-box" / "backstep.py")
backstep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backstep)

# Dynamic Dodge's StepDodgeBack keys (time, y), as measured from the player's copy on 2026-11-08
KEYS = [(0.0, "0.000"), (0.033, "-4.513"), (0.067, "-16.331"), (0.117, "-38.723"), (0.183, "-72.328"),
        (0.25, "-96.972"), (0.3, "-116.910"), (0.333, "-130.070"), (0.433, "-207.680"), (0.533, "-261.980"), (0.667, "-334.210"), (0.833, "-379.300")]


def packfile(keys) -> bytes:
    """A minimal hk 2010 packfile: header, a __data__ section header, the annotations ({float time; pad; char*}),
    their strings, then local fixups (annotation pointer -> string), ended by -1."""
    ann, strings, fix = b"", b"", []
    base = 16 * len(keys)
    for t, y in keys:
        fix.append((len(ann) + 8, base + len(strings)))
        ann += struct.pack("<f4xQ", t, 0)
        strings += f"animmotion 0 {y} 0".encode() + b"\x00"
    strings += b"\x00" * (-len(strings) % 16)
    body = ann + strings
    local = len(body)
    fixups = b"".join(struct.pack("<2i", s, d) for s, d in fix) + struct.pack("<2i", -1, -1)
    head = b"\x57\xe0\xe0\x57\x10\xc0\xc0\x10" + b"\x00" * 56
    start = len(head) + 48
    sec = b"__data__".ljust(19, b"\x00") + b"\xff" + struct.pack(
        "<7i", start, local, local + len(fixups), local + len(fixups), local + len(fixups), local + len(fixups),
        local + len(fixups))
    return head + sec + body + fixups


def test_measure_reads_every_key_and_the_first_push():
    b = packfile(KEYS)
    ks = backstep.keys(b)
    assert [round(k[0], 3) for k in ks] == [k[0] for k in KEYS]
    assert ks[-1][2] == pytest.approx(-379.3)
    assert backstep.pushes(ks)[0] == (0, 7)  # 0-0.333 s; the 0.1 s gap after it ends the push


def test_cut_holds_the_first_push_end_and_keeps_every_offset():
    b = packfile(KEYS)
    out, old, new = backstep.cut(b)
    assert len(out) == len(b)
    assert (old, new) == (pytest.approx(379.3), pytest.approx(130.07))
    ks = backstep.keys(out)
    assert [k[2] for k in ks[:8]] == [float(y) for _, y in KEYS[:8]]
    assert all(k[2] == pytest.approx(-130.07) for k in ks[8:])
    assert [round(k[0], 3) for k in ks] == [k[0] for k in KEYS]  # times untouched: the clip plays whole
    assert backstep.cut(out)[2] == pytest.approx(130.07)  # a second cut changes nothing


def test_a_longer_hold_text_is_refused():
    with pytest.raises(ValueError):
        backstep.cut(packfile([(0.0, "0"), (0.033, "-130.070"), (0.2, "-9")]))
