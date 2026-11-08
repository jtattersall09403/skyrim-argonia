"""infra/gpu-box/backstep.py: the standing backstep cut at the end of its first push (owner, walk 3, 2026-11-08)."""
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
        (0.25, "-96.972"), (0.3, "-116.910"), (0.333, "-130.070"), (0.433, "-207.680"), (0.533, "-261.980"),
        (0.667, "-334.210"), (0.833, "-379.300")]


def section(name: bytes, start: int, local: int, end: int) -> bytes:
    return name.ljust(19, b"\x00") + b"\xff" + struct.pack("<7i", start, local, end, end, end, end, end)


def packfile(items, duration=0.9333) -> bytes:
    """A minimal 64-bit hk 2010 packfile, laid out as the player's StepDodgeBack: a __classnames__ section naming
    hkaSplineCompressedAnimation; __data__ with the animation (duration at +20, annotation tracks {ptr, size} at
    +40), one track at 64 ({name, annotations ptr, size}), its annotations at 96 ({float time; pad; char*}) in the
    given order, their strings; then local fixups (pointer -> target) and one virtual fixup (object -> class)."""
    anim = bytearray(64)
    struct.pack_into("<if", anim, 16, 5, duration)
    struct.pack_into("<i", anim, 48, 1)
    track = bytearray(32)
    struct.pack_into("<i", track, 16, len(items))
    ann, strings, fix = b"", b"", [(40, 64), (72, 96)]
    base = 96 + 16 * len(items)
    for t, text in items:
        fix.append((96 + len(ann) + 8, base + len(strings)))
        ann += struct.pack("<f4xQ", t, 0)
        strings += text.encode() + b"\x00"
    body = bytes(anim) + bytes(track) + ann + strings
    body += b"\x00" * (-len(body) % 16)
    local = len(body)
    lf = b"".join(struct.pack("<2i", s, d) for s, d in fix) + struct.pack("<2i", -1, -1)
    vf = struct.pack("<3i", 0, 0, 0) + struct.pack("<3i", -1, -1, -1)
    classes = b"hkaSplineCompressedAnimation\x00".ljust(32, b"\x00")
    head = bytearray(64)
    head[0:8] = b"\x57\xe0\xe0\x57\x10\xc0\xc0\x10"
    head[16] = 8
    cstart = len(head) + 96
    dstart = cstart + len(classes)
    glob = local + len(lf)
    return (bytes(head) + section(b"__classnames__", cstart, len(classes), len(classes))
            + b"__data__".ljust(19, b"\x00") + b"\xff"
            + struct.pack("<7i", dstart, local, glob, glob, glob + len(vf), glob + len(vf), glob + len(vf))
            + classes + body + lf + vf)


def motion(keys):
    return [(t, f"animmotion 0 {y} 0") for t, y in keys]


# the author's order is not by time: a late key and the 0.6 s footstep come first
ITEMS = [motion(KEYS)[-1], (0.6, "SoundPlay.FSTPlayerDirtJumpDownSD")] + motion(KEYS)[:-1] + \
        [(0.333, "SoundPlay.FSTPlayerDirtJumpDownSD")]


def test_measure_reads_every_key_and_the_first_push():
    b = packfile(ITEMS)
    ks = backstep.keys(b)
    assert [round(k[0], 3) for k in ks] == [k[0] for k in KEYS]
    assert ks[-1][2] == pytest.approx(-379.3)
    assert backstep.pushes(ks)[0] == (0, 7)  # 0-0.333 s; the 0.1 s gap after it ends the push
    assert backstep.Clip(b).duration == pytest.approx(0.9333)


def test_cut_ends_the_clip_at_the_first_push_and_keeps_every_offset():
    b = packfile(ITEMS)
    out, old, new = backstep.cut(b)
    assert len(out) == len(b)
    assert (old, new) == (pytest.approx(379.3), pytest.approx(130.07))
    assert backstep.Clip(out).duration == pytest.approx(0.333)
    ks = backstep.keys(out)
    assert [(round(k[0], 3), k[2]) for k in ks] == [(t, float(y)) for t, y in KEYS[:8]]
    kept = [txt for _, items in backstep.Clip(out).track_items() for _, txt in items]
    assert kept.count("SoundPlay.FSTPlayerDirtJumpDownSD") == 1  # the 0.333 s footstep stays, the 0.6 s one goes
    assert backstep.cut(out)[0] == out  # a second cut changes nothing


def test_a_clip_without_motion_is_refused():
    with pytest.raises(ValueError):
        backstep.cut(packfile([(0.1, "SoundPlay.X")]))
