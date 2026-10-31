"""L1/L2 for the theme recipe (1.2 §a): the SWF codec, the font library, the palette, the retheme and the title source.
Small synthetic fixtures only; the real run (Dear Diary as installed, Pelagiad) is the lane's command, not the gate."""
import struct
import sys
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("fontTools")
from fontTools.fontBuilder import FontBuilder  # noqa: E402
from fontTools.pens.ttGlyphPen import TTGlyphPen  # noqa: E402

from tools.ui_theme import build, fontlib, retheme, swf  # noqa: E402
from tools.ui_theme.palette import Palette, tokens  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]


def drop_zero(contours):
    out = []
    for start, segs in contours:
        kept, at = [], start
        for s in segs:
            end = s[-2:]
            if s[0] == "L" and tuple(end) == tuple(at):
                continue
            kept.append(s)
            at = end
        out.append((start, kept))
    return out


def test_glyph_round_trip():
    contours = [((0, -14000), [("L", 9000, -14000), ("Q", 12000, -7000, 9000, 0), ("L", 0, 0), ("L", 0, -14000)]),
                ((3000, -9000), [("L", 3000, -3000), ("L", 6000, -6000), ("L", 3000, -9000)])]
    assert swf.decode_glyph(swf.encode_glyph(contours)) == contours
    assert swf.sbits(-1, 0) == 1 and swf.sbits(1) == 2 and swf.sbits(-20480, 20479) == 16


def tiny_ttf(path: Path):
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder([".notdef", "A", "space"])
    fb.setupCharacterMap({ord("A"): "A", ord(" "): "space"})
    pen = TTGlyphPen(None)
    pen.moveTo((50, 0))
    pen.lineTo((50, 700))
    pen.qCurveTo((300, 900), (550, 700))
    pen.lineTo((550, 0))
    pen.closePath()
    glyph_a = pen.glyph()
    fb.setupGlyf({".notdef": TTGlyphPen(None).glyph(), "A": glyph_a, "space": TTGlyphPen(None).glyph()})
    fb.setupHorizontalMetrics({".notdef": (500, 0), "A": (600, 50), "space": (250, 0)})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": "Tiny", "styleName": "Regular", "copyright": "test"})
    fb.setupOS2()
    fb.setupPost()
    fb.save(str(path))


def test_font_library(tmp_path):
    ttf = tmp_path / "tiny.ttf"
    tiny_ttf(ttf)
    assert fontlib.main(["--ttf", str(ttf), "--out", str(tmp_path / "out")]) == 0
    movie = swf.read((tmp_path / "out/interface/fonts_pelagiad.swf").read_bytes())
    codes = [t.code for t in movie.tags]
    assert codes == [swf.SET_BACKGROUND, swf.DEFINE_FONT3, swf.DEFINE_FONT_NAME, swf.EXPORT_ASSETS,
                     swf.SHOW_FRAME, swf.END]  # the layout of Dear Diary's working fonts_fritzq.swf
    font = swf.parse_define_font3(movie.tags[1].data)
    assert font.name == "Pelagiad" and sorted(font.glyphs) == [32, 65]
    a = font.glyphs[65]
    assert a.advance == round(600 * swf.FONT_EM / 1000)
    assert font.ascent == round(800 * swf.FONT_EM / 1000) and font.descent == round(200 * swf.FONT_EM / 1000)
    (start, segs), = swf.decode_glyph(a.shape)
    k = swf.FONT_EM / 1000
    assert start == (round(50 * k), 0) and ("Q", round(300 * k), round(-900 * k), round(550 * k), round(-700 * k)) in segs
    assert a.bounds == (round(50 * k), round(550 * k), round(-900 * k), 0)  # bounds include the control point
    assert movie.tags[3].data == struct.pack("<HH", 1, 1) + b"Pelagiad\0"
    cfg = (tmp_path / "out/interface/fontconfig.txt").read_text("utf-8-sig")
    assert 'fontlib "Interface\\fonts_pelagiad.swf"' in cfg
    assert 'map "$EverywhereFont" = "Pelagiad" Normal' in cfg and 'map "$DragonFont" = "Daedric" Normal' in cfg
    assert 'validNameChars "A "' in cfg  # only characters the font draws


def menu(tmp: Path, rel: str, imports=(), bitmaps=()):
    tags = []
    for k, name in enumerate(imports, start=1):
        tags.append(swf.Tag(swf.IMPORT_ASSETS2, b"gfxfontlib.swf\0" + b"\x01\x00" + struct.pack("<HH", 1, k)
                            + name.encode() + b"\0"))
    for k, rgba in enumerate(bitmaps, start=10):
        tags.append(swf.Tag(swf.DEFINE_BITS_LOSSLESS2, swf.encode_lossless2(swf.Bitmap(k, rgba)), True))
    tags += [swf.Tag(swf.SHOW_FRAME, b""), swf.Tag(swf.END, b"")]
    p = tmp / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(swf.Movie(b"CWS", 10, swf.rect(0, 100, 0, 100) + struct.pack("<HH", 6144, 1), tags).to_bytes())
    return p


def test_unmapped_imports(tmp_path):
    menu(tmp_path, "interface/a.swf", imports=["$EverywhereFont", "$NewFont"])
    assert fontlib.unmapped_imports([tmp_path]) == ["interface/a.swf: $NewFont"]


def test_lossless2_round_trip():
    rgba = np.zeros((3, 5, 4), np.uint8)
    rgba[..., :3] = [200, 120, 40]
    rgba[0, :, 3] = 255
    rgba[1, :, 3] = 128
    back = swf.decode_lossless2(swf.encode_lossless2(swf.Bitmap(7, rgba)))
    assert back.char_id == 7
    assert (back.rgba[0] == rgba[0]).all()  # opaque: exact
    assert np.abs(back.rgba[1].astype(int) - rgba[1]).max() <= 2  # premultiplied: within rounding
    assert (back.rgba[2] == 0).all()  # transparent: nothing kept


def test_palette_reads_theme_css():
    t = tokens()
    assert t["paper"] == (0xE6, 0xD9, 0xB8) and t["moss"] == (0x4B, 0x5A, 0x2A)


def test_palette_maps_dear_diary_to_ours():
    p = Palette()
    px = np.array([[[170, 160, 145, 255],    # Dear Diary's paper (value 0.65, saturation 0.12), measured
                    [74, 40, 26, 200],       # its frame (hue 18, saturation 0.5, value 0.29)
                    [30, 25, 20, 255]]], np.uint8)  # ink
    out = p.apply(px)
    assert (out[..., 3] == px[..., 3]).all()
    paper = out[0, 0, :3].astype(int)
    assert np.abs(paper - np.array(tokens()["paper-dark"])).max() < 40  # onto our sheet
    r, g, b = out[0, 1, :3].astype(int)
    assert g > r and g > b  # the frame leaves Skyrim's red-brown for moss
    assert out[0, 2, :3].astype(int).max() < 60  # ink stays ink


def test_retheme_overlay(tmp_path):
    paper = np.full((4, 4, 4), [170, 160, 145, 255], np.uint8)
    other = np.full((4, 4, 4), [150, 150, 150, 255], np.uint8)
    dd, wp = tmp_path / "dd", tmp_path / "wp"
    menu(dd, "interface/deardiary/inventory/inventorylists_BG.swf", bitmaps=[paper])
    menu(dd, "interface/deardiary/startmenu/startmenu_load_BG.swf", bitmaps=[other])
    menu(wp, "interface/deardiary/startmenu/startmenu_load_BG.swf", bitmaps=[paper])  # the skin wins
    mark = np.full((577, 542, 4), [20, 20, 20, 120], np.uint8)
    menu(dd, "interface/deardiary/map/map_bonus_BG.swf", bitmaps=[mark])
    menu(dd, "interface/skyui/configpanel.swf", bitmaps=[paper, np.zeros((2, 2, 4), np.uint8)])  # a fallback copy
    menu(dd, "interface/other.swf", bitmaps=[np.full((2, 2, 4), 255, np.uint8)])
    out = tmp_path / "out"
    report = retheme.run([dd, wp], out, Palette(), None)
    assert report["warnings"] == []
    assert sorted(report["files"]) == ["interface/deardiary/inventory/inventorylists_bg.swf",
                                       "interface/deardiary/map/map_bonus_bg.swf",
                                       "interface/deardiary/startmenu/startmenu_load_bg.swf",
                                       "interface/skyui/configpanel.swf"]
    assert str(wp) in report["files"]["interface/deardiary/startmenu/startmenu_load_bg.swf"]["from"]

    def first(rel):
        return swf.bitmaps(swf.read((out / rel).read_bytes()))[0][1].rgba

    want = Palette().apply(paper)
    assert (first("interface/deardiary/inventory/inventorylists_bg.swf") == want).all()
    assert (first("interface/deardiary/map/map_bonus_bg.swf")[..., 3] == 0).all()
    assert (first("interface/skyui/configpanel.swf") == want).all()


def test_title_svg_is_generated_from_its_source():
    sys.path.insert(0, str(ROOT))
    from ui.title import title

    assert (ROOT / "ui/title/argonia-title.svg").read_text() == title.svg()
    assert "ARGONIA" in title.svg() and "Skyrim" not in title.svg()


def test_skyui_list_sizes_are_raised_and_a_changed_config_fails():
    cfg = "defaults.entry.textFormat.size = 14\n  defaults.label.textFormat.size=12\ncolumns.x.size = 9\n"
    out, missing = build.list_sizes(cfg)
    assert "defaults.entry.textFormat.size = 20" in out and "defaults.label.textFormat.size=16" in out
    assert "columns.x.size = 9" in out and missing == []
    assert build.list_sizes("nothing here\n")[1] == list(build.LIST_SIZES)
