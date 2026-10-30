"""Pelagiad everywhere (1.2 §a, 0014 §7): the font library SWF and fontconfig.txt for every vanilla and SkyUI menu
that remains. Run at install on the player's machine, from the player's copy of the OFL font; the output is a
derived file and never enters the repo.

    python -m tools.ui_theme.fontlib --ttf Pelagiad.ttf --out out/ui_theme/fonts [--check <mod roots...>]

writes <out>/interface/fonts_pelagiad.swf and <out>/interface/fontconfig.txt. --check reads every menu SWF under the
given mod roots and fails if any font a menu imports from gfxfontlib.swf is not mapped by our fontconfig.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont

from tools.ui_theme import swf

NAME = "Pelagiad"
LIBRARY = "fonts_pelagiad.swf"

# Every font name the vanilla and SkyUI menus import (vanilla fontconfig.txt's map lines, plus Dear Diary's
# additions), and what it maps to. Pelagiad carries every word the player reads; the glyph and script fonts stay
# vanilla, except the Nordic scripts (0006), which read as Daedric.
MAP = {
    "$ListFont": NAME, "$StartMenuFont": NAME, "$DialogueFont": NAME, "$EverywhereFont": NAME,
    "$EverywhereBoldFont": NAME, "$EverywhereMediumFont": NAME, "$SkyrimBooks": NAME, "$HandwrittenFont": NAME,
    "$HandwrittenBold": NAME,
    "$ConsoleFont": "Arial",  # the console is the hands' (SkyLink), not the player's; vanilla fonts_console.swf
    "$DragonFont": "Daedric", "$FalmerFont": "Daedric",  # no Nordic script survives (0006)
    "$DwemerFont": "Dwemer", "$DaedricFont": "Daedric", "$MageScriptFont": "Mage Script",
    "$SkyrimSymbolsFont": "SkyrimSymbols", "$SkyrimBooks_UnreadableFont": "SkyrimBooks_Unreadable",
}
VANILLA_LIBS = ("fonts_console.swf", "fonts_en.swf")  # in Skyrim - Interface.bsa: Arial, the scripts, the symbols
KEYBOARD = ("`1234567890-=~!@#$%^&*():_+QWERTYUIOP[]ASDFGHJKL;'ZXCVBNM,./qwertyuiop{}\\asdfghjkl;'zxcvbnm<>?| "
            "ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝßàáâãäåæçèéêëìíîïñòóôõöøùúûüýÿ")


class SwfPen(BasePen):
    """TrueType outlines (quadratic, y up, units per em) to SWF contours (y down, the 20x 1024 em)."""

    def __init__(self, glyphset, scale: float):
        super().__init__(glyphset)
        self.k, self.contours, self.start, self.at = scale, [], None, None

    def _p(self, pt):
        return round(pt[0] * self.k), round(-pt[1] * self.k)

    def _moveTo(self, pt):
        self.start = self.at = self._p(pt)
        self.contours.append((self.start, []))

    def _lineTo(self, pt):
        self.at = self._p(pt)
        self.contours[-1][1].append(("L", *self.at))

    def _qCurveToOne(self, c, pt):
        cc, self.at = self._p(c), self._p(pt)
        self.contours[-1][1].append(("Q", *cc, *self.at))

    def _curveToOne(self, c1, c2, pt):  # a cubic (CFF) outline: two quadratics at the midpoint
        p0 = self._pcur()
        mid = [(a + 3 * b + 3 * c + d) / 8 for a, b, c, d in zip(p0, c1, c2, pt)]
        q1 = [(a + 3 * b) / 4 for a, b in zip(p0, c1)]
        q2 = [(3 * c + d) / 4 for c, d in zip(c2, pt)]
        self._qCurveToOne(q1, mid)
        self._qCurveToOne(q2, pt)

    def _pcur(self):
        return self._getCurrentPoint()

    def _closePath(self):
        if self.at != self.start:
            self.contours[-1][1].append(("L", *self.start))
        self.at = self.start

    _endPath = _closePath


def bounds(contours) -> tuple[int, int, int, int]:
    pts = [c[0] for c in contours] + [p for _s, segs in contours for seg in segs for p in zip(seg[1::2], seg[2::2])]
    if not pts:
        return 0, 0, 0, 0
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), max(xs), min(ys), max(ys)


def build_font(ttf: Path) -> tuple[bytes, str, dict[int, swf.Glyph]]:
    """The DefineFont3 for the font's whole BMP cmap, with its kern table's pairs."""
    font = TTFont(ttf)
    k = swf.FONT_EM / font["head"].unitsPerEm
    glyphset, cmap, hmtx = font.getGlyphSet(), font.getBestCmap(), font["hmtx"]
    glyphs = {}
    for code, gname in sorted(cmap.items()):
        if code > 0xFFFF:
            continue
        pen = SwfPen(glyphset, k)
        glyphset[gname].draw(pen)
        glyphs[code] = swf.Glyph(code, swf.encode_glyph(pen.contours), round(hmtx[gname][0] * k), bounds(pen.contours))
    kerning = []
    if "kern" in font:
        rev: dict[str, list[int]] = {}
        for code, gname in cmap.items():
            if code in glyphs:
                rev.setdefault(gname, []).append(code)
        for table in font["kern"].kernTables:
            for (a, b), v in getattr(table, "kernTable", {}).items():
                for ca in rev.get(a, ()):
                    for cb in rev.get(b, ()):
                        kerning.append((ca, cb, round(v * k)))
    hhea = font["hhea"]
    define = swf.define_font3(1, NAME, list(glyphs.values()), round(hhea.ascent * k), round(-hhea.descent * k),
                              round(hhea.lineGap * k), sorted(kerning))
    names = font["name"]
    copyright_ = (names.getDebugName(0) or "").strip() + " (SIL Open Font License 1.1)"
    return define, copyright_, glyphs


def fontconfig(glyphs: dict[int, swf.Glyph]) -> str:
    lines = ["; Argonia's font config (1.2 §a, 0014 §7): generated at install by tools/ui_theme/fontlib.py", ""]
    lines += [f'fontlib "Interface\\{lib}"' for lib in (*VANILLA_LIBS, LIBRARY)]
    lines.append("")
    lines += [f'map "{key}" = "{value}" Normal' for key, value in MAP.items()]
    valid = "".join(ch for ch in KEYBOARD if ord(ch) in glyphs)
    lines.append(f'validNameChars "{valid}"')
    return "\r\n".join(lines) + "\r\n"


def unmapped_imports(roots: list[Path]) -> list[str]:
    """Every '<swf>: <font>' a menu imports from gfxfontlib.swf that MAP does not name."""
    out = []
    for root in roots:
        for p in sorted(root.rglob("*")):
            if p.suffix.lower() not in (".swf", ".gfx") or not p.is_file():
                continue
            try:
                movie = swf.read(p.read_bytes())
            except Exception:  # noqa: BLE001 - a foreign movie is reported, not fatal
                out.append(f"{p}: unreadable")
                continue
            for url, name in swf.imports(movie):
                if url.lower().endswith("gfxfontlib.swf") and name not in MAP:
                    out.append(f"{p.relative_to(root)}: {name}")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ttf", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--check", type=Path, nargs="*", default=[])
    a = ap.parse_args(argv)
    define, copyright_, glyphs = build_font(a.ttf)
    iface = a.out / "interface"
    iface.mkdir(parents=True, exist_ok=True)
    (iface / LIBRARY).write_bytes(swf.font_library([(NAME, define, copyright_)]).to_bytes())
    (iface / "fontconfig.txt").write_bytes(fontconfig(glyphs).encode("utf-8-sig"))  # a BOM, as Dear Diary's working file has
    print(f"{iface / LIBRARY}: {len(glyphs)} glyphs; {iface / 'fontconfig.txt'}: {len(MAP)} maps")
    gaps = unmapped_imports(a.check)
    for g in gaps:
        print("unmapped:", g)
    return 1 if gaps else 0


if __name__ == "__main__":
    sys.exit(main())
