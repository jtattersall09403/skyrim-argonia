"""L2 for the Flash still renderer: the AVM1 assembler (run by Ruffle when the exporter is installed), the text
measure on synthetic images. The real proof (Dear Diary's System page, pre-fix black and fixed cream) is the lane's
command: python -m tools.ui_theme.flash_still <swf> --state system-load --measure --out ..."""
import struct

import numpy as np
import pytest
from PIL import Image

from tools.ui_theme import flash_still, swf
from tools.ui_theme.avm1 import Asm, Ref, text_walker

needs_ruffle = pytest.mark.skipif(not flash_still.EXPORTER.is_file(), reason="ruffle-exporter not installed")


def _movie(script: Asm) -> swf.Movie:
    frame = swf.rect(0, 4000, 0, 3000) + struct.pack("<HH", 30 << 8, 1)
    return swf.Movie(b"FWS", 10, frame, [swf.Tag(12, script.bytes()), swf.Tag(1, b""), swf.Tag(0, b"")])


def test_push_and_jump_encoding():
    a = Asm().push("x", 3, True, None, 1.5).jump("end", cond=True).push("skipped").label("end")
    b = a.bytes()
    assert b[0] == 0x96 and b"x\0" in b and b[-1] == 0
    i = b.index(0x9D)
    assert struct.unpack("<h", b[i + 3:i + 5])[0] == len(Asm().push("skipped").bytes(end=False))


@needs_ruffle
def test_ruffle_runs_our_bytecode(tmp_path):
    """Arrays, objects, method calls, a defined function with a for..in walk, and the translate step, in Ruffle."""
    a = Asm()
    a.var("o", {"k": [1, 2, "three"]}).path("o.k").push(2).op(0x4E).op(0x26)  # trace(o.k[2])
    a.call("_root", "createTextField", "tf", 1, 0, 0, 200, 40)
    a.set("_root.tf", "text", "$GREETING")
    a.out += text_walker("__w", Asm().path("c.text").op(0x26)).out
    a.callf("__w", Ref("_root"))
    src = tmp_path / "t.swf"
    src.write_bytes(_movie(a).to_bytes())
    (tmp_path / "translate_english.txt").write_bytes("$GREETING\tHello\r\n".encode("utf-16"))
    out = tmp_path / "t.png"
    log = flash_still.render(src, out, state=None, label=None, frame=None, width=200, height=150,
                             roots=[tmp_path], fontlib=tmp_path / "none.swf", script=a)
    assert "trace: three" in log and "trace: $GREETING" in log and out.is_file()


def test_measure_finds_ink_and_contrast(tmp_path):
    bare = np.full((200, 400, 3), 20, np.uint8)
    full = bare.copy()
    full[50:70, 40:200] = (230, 220, 190)  # a cream line
    full[120:140, 40:120] = (25, 25, 25)  # a near-black line on the dark ground
    Image.fromarray(full).save(tmp_path / "f.png")
    Image.fromarray(bare).save(tmp_path / "b.png")
    items = flash_still.measure(tmp_path / "f.png", tmp_path / "b.png")
    assert [i["ink"] for i in items] == ["#e6dcbe", "#191919"]
    assert items[0]["contrast"] > 10 and items[1]["contrast"] < 1.2  # the black-on-dark the game showed
