"""The light Black Marsh retheme of Dear Diary (1.2 §a), as a recipe run at install on the player's machine (0014).

Dear Diary's menus draw their paper, frames and ornaments from bitmaps embedded in SWFs (DefineBitsLossless2): every
menu loads its interface/deardiary/**/<menu>_BG.swf at run time, and Wood and Paper (44174) replaces some of those.
The Oblivion-like Loading Menu (38708) draws its sheet from a bitmap in its loadingmenu.swf. Only the main menu's
wallpaper is a DDS, and it is Skyrim's map with the "Skyrim" wordmark, so it is replaced outright by our title
wallpaper (ui/title/title.py), not recoloured.

    python -m tools.ui_theme.retheme --mods <dear-diary> <wood-and-paper> <oblivion-loading-menu> \
        --ttf Pelagiad.ttf --out out/ui_theme/argonia-theme

The mod roots are the installed folders, lowest priority first. The output is an overlay mod laid above them: every
*_BG.swf winner and the loading menu with its bitmaps recoloured to our palette (tools/ui_theme/palette.py), the
Nordic watermarks cleared, the copies of those bitmaps the menu SWFs embed treated alike, and the wallpaper DDS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from fnmatch import fnmatch
from pathlib import Path

import numpy as np

from tools.ui_theme import swf
from tools.ui_theme.palette import Palette

SCOPE = ("interface/deardiary/*_bg.swf", "interface/loadingmenu.swf")
# SWFs whose vector shapes (DefineShape fills and lines) are recoloured too: the menus and SkyUI's lists, plates and
# icons; ui-review4 found the barter and container name plates' red knot drawn as a shape, not a bitmap.
SHAPES = ("interface/*.swf", "interface/skyui/*.swf", "interface/deardiary/*_bg.swf")
NO_SHAPES = ("interface/fonts_*.swf",)
EMBEDDERS = "interface/*.swf"  # menu SWFs carrying copies of the BG bitmaps (fallbacks): matched by their pixels
# Nordic marks (0006), by path and the bitmap's measured size (w, h); cleared to transparent, not recoloured.
CLEAR = {
    "interface/deardiary/map/map_bonus_bg.swf": ((542, 577), "the horned Dragonborn helmet watermark"),
    "interface/deardiary/inventory/craftingmenu_enchanting_bg.swf": ((197, 408), "Skyrim's barbed enchanting sigil"),
}
# Frames painted into a sheet bitmap, not separate (1.9): by path, the bitmap's size, the ring box (x0, y0, x1, y1)
# around the transparent picture window. The ring is re-textured from the sheet's own clean margins and our plain ink
# line is drawn around the window; the window and its torn edge are kept.
REFRAME = {
    "interface/loadingmenu.swf": ((1280, 720), (250, 25, 1035, 565),
                                  "the Oblivion-like Loading Menu's Celtic-knot frame, crest and corner knots"),
}
WALLPAPER = "textures/interface/objects/mainmenuwallpaper.dds"


def winners(roots: list[Path]) -> dict[str, Path]:
    """Relative path (lower case, forward slashes) to the file that wins, the last root that has it."""
    out: dict[str, Path] = {}
    for root in roots:
        for p in root.rglob("*"):
            if p.is_file():
                out[str(p.relative_to(root)).replace("\\", "/").lower()] = p
    return out


def digest(rgba: np.ndarray) -> str:
    return hashlib.sha256(rgba.shape.__repr__().encode() + rgba.tobytes()).hexdigest()


def _fold(d: np.ndarray, width: int) -> np.ndarray:
    """Distances walked into a margin of `width`, mirrored back and forth so the texture never jumps."""
    k = d % (2 * width)
    return np.where(k < width, k, 2 * width - 1 - k)


def reframe(rgba: np.ndarray, ring: tuple[int, int, int, int], edge: int = 60, seam: int = 24) -> np.ndarray:
    """The sheet with its painted frame replaced: the ring box outside the picture window is filled, row by row, with
    the row's own clean margins mirrored inwards (left half from the left margin, right half from the right, blended
    over `seam` px at the middle), then our ink line is drawn 10 px outside the window."""
    h, w = rgba.shape[:2]
    x0, y0, x1, y1 = ring
    out = rgba.astype(np.float32)
    ys, xs = np.where(rgba[..., 3] < 128)
    wx0, wx1, wy0, wy1 = xs.min(), xs.max(), ys.min(), ys.max()
    x = np.arange(x0, x1)
    left = x0 - 1 - _fold(x - x0, x0 - edge)
    right = x1 + _fold(x1 - 1 - x, w - edge - x1)
    mid = (x0 + x1) / 2
    t = np.clip((x - (mid - seam / 2)) / seam, 0, 1)[None, :, None]
    rows = rgba[y0:y1].astype(np.float32)
    fill = (1 - t) * rows[:, left] + t * rows[:, right]
    keep = np.zeros((y1 - y0, x1 - x0), bool)  # the window and its torn rim, 4 px
    keep[max(wy0 - 4 - y0, 0):wy1 + 5 - y0, max(wx0 - 4 - x0, 0):wx1 + 5 - x0] = True
    region = out[y0:y1, x0:x1]
    region[~keep] = fill[~keep]
    ink = np.array([92, 70, 46], np.float32)
    for pad, a in ((10, 0.55), (9, 0.25), (12, 0.25)):  # a 2 px line with a soft halo
        bx0, bx1, by0, by1 = wx0 - pad, wx1 + pad, wy0 - pad, wy1 + pad
        for sl in ((slice(by0, by0 + 2), slice(bx0, bx1 + 1)), (slice(by1 - 1, by1 + 1), slice(bx0, bx1 + 1)),
                   (slice(by0, by1 + 1), slice(bx0, bx0 + 2)), (slice(by0, by1 + 1), slice(bx1 - 1, bx1 + 1))):
            out[sl][..., :3] = out[sl][..., :3] * (1 - a) + ink * a
    return np.clip(out, 0, 255).astype(np.uint8)


def treat(bm: swf.Bitmap, palette: Palette, clear: bool, ring=None) -> swf.Bitmap:
    if clear:
        return swf.Bitmap(bm.char_id, np.zeros_like(bm.rgba))
    rgba = reframe(bm.rgba, ring) if ring else bm.rgba
    return swf.Bitmap(bm.char_id, palette.apply(rgba))


def recolour_shapes(movie: swf.Movie, palette: Palette) -> int:
    """Every DefineShape fill, gradient and line colour mapped through the palette in place, alpha kept; the count."""
    n = 0
    for k, tag in enumerate(movie.tags):
        if tag.code not in swf.SHAPE_TAGS:
            continue
        offs, alpha = swf.shape_colours(tag)
        if not offs:
            continue
        data = bytearray(tag.data)
        rgba = np.array([[list(data[o:o + 3]) + [data[o + 3] if alpha else 255] for o in offs]], np.uint8)
        new = palette.apply(rgba)[0]
        for o, c in zip(offs, new):
            data[o:o + 3] = bytes(int(v) for v in c[:3])
        movie.tags[k] = swf.Tag(tag.code, bytes(data), tag.long)
        n += len(offs)
    return n


def rewrite(path: Path, decide, palette: Palette | None = None) -> tuple[bytes | None, list[str]]:
    """The movie with each bitmap decide(bitmap) returns a treatment for replaced, and its vector colours mapped when
    a palette is given; None when nothing changed."""
    movie = swf.read(path.read_bytes())
    notes, changed = [], False
    if palette is not None and (n := recolour_shapes(movie, palette)):
        notes.append(f"recoloured {n} shape colours")
        changed = True
    for k, bm in swf.bitmaps(movie):
        verdict = decide(bm)
        if verdict is None:
            continue
        new = treat(bm, *verdict)
        movie.tags[k] = swf.Tag(swf.DEFINE_BITS_LOSSLESS2, swf.encode_lossless2(new), True)
        what = "cleared" if verdict[1] else "reframed and recoloured" if len(verdict) > 2 and verdict[2] else "recoloured"
        notes.append(f"{what} #{bm.char_id} {bm.rgba.shape[1]}x{bm.rgba.shape[0]}")
        changed = True
    return (movie.to_bytes() if changed else None), notes


def run(roots: list[Path], out: Path, palette: Palette, ttf: Path | None) -> dict:
    files = winners(roots)
    report: dict = {"files": {}, "warnings": []}
    seen: dict[str, bool] = {}  # pixel digest of every in-scope bitmap, from every root -> cleared?
    for root in roots:
        for p in root.rglob("*"):
            rel = str(p.relative_to(root)).replace("\\", "/").lower()
            if p.is_file() and any(fnmatch(rel, s) for s in SCOPE):
                for _k, bm in swf.bitmaps(swf.read(p.read_bytes())):
                    seen[digest(bm.rgba)] = rel in CLEAR
    for rel, p in sorted(files.items()):
        in_scope = any(fnmatch(rel, s) for s in SCOPE)
        if in_scope:
            want, frame = CLEAR.get(rel), REFRAME.get(rel)

            def decide(bm, want=want, frame=frame, rel=rel):
                size = (bm.rgba.shape[1], bm.rgba.shape[0])
                if want and size != want[0]:
                    report["warnings"].append(f"{rel}: expected {want[0]} for {want[1]}, found {size}")
                if frame and size != frame[0]:
                    report["warnings"].append(f"{rel}: expected {frame[0]} for {frame[2]}, found {size}")
                return palette, bool(want), (frame[1] if frame and size == frame[0] else None)
        elif fnmatch(rel, EMBEDDERS) and p.suffix.lower() == ".swf":
            def decide(bm):
                c = seen.get(digest(bm.rgba))
                return None if c is None else (palette, c)
        elif any(fnmatch(rel, s) for s in SHAPES):
            def decide(bm):
                return None
        else:
            continue
        shapes = any(fnmatch(rel, s) for s in SHAPES) and not any(fnmatch(rel, s) for s in NO_SHAPES)
        blob, notes = rewrite(p, decide, palette if shapes else None)
        if blob is None:
            continue
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(blob)
        report["files"][rel] = {"from": str(p), "bitmaps": notes}
    if ttf is not None:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from ui.title import title  # noqa: PLC0415 - the title is its own source folder

        dest = out / WALLPAPER
        dest.parent.mkdir(parents=True, exist_ok=True)
        title.wallpaper(ttf, palette).save(dest, pixel_format="DXT1")
        report["files"][WALLPAPER] = {"from": "ui/title/title.py", "bitmaps": ["generated 2048x2048 DXT1"]}
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mods", type=Path, nargs="+", required=True, help="installed mod roots, lowest priority first")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--ttf", type=Path, help="Pelagiad.ttf: also write the title wallpaper DDS")
    a = ap.parse_args(argv)
    report = run(a.mods, a.out, Palette(), a.ttf)
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "argonia-theme.json").write_text(json.dumps(report, indent=1))
    n = sum(len(v["bitmaps"]) for v in report["files"].values())
    print(f"{a.out}: {len(report['files'])} files, {n} bitmaps; {len(report['warnings'])} warnings")
    for w in report["warnings"]:
        print("warning:", w)
    return 1 if report["warnings"] else 0


if __name__ == "__main__":
    sys.exit(main())
