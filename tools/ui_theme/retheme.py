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
EMBEDDERS = "interface/*.swf"  # menu SWFs carrying copies of the BG bitmaps (fallbacks): matched by their pixels
# Nordic marks (0006), by path and the bitmap's measured size (w, h); cleared to transparent, not recoloured.
CLEAR = {
    "interface/deardiary/map/map_bonus_bg.swf": ((542, 577), "the horned Dragonborn helmet watermark"),
    "interface/deardiary/inventory/craftingmenu_enchanting_bg.swf": ((197, 408), "Skyrim's barbed enchanting sigil"),
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


def treat(bm: swf.Bitmap, palette: Palette, clear: bool) -> swf.Bitmap:
    if clear:
        return swf.Bitmap(bm.char_id, np.zeros_like(bm.rgba))
    return swf.Bitmap(bm.char_id, palette.apply(bm.rgba))


def rewrite(path: Path, decide) -> tuple[bytes | None, list[str]]:
    """The movie with each bitmap decide(bitmap) returns a treatment for replaced; None when nothing changed."""
    movie = swf.read(path.read_bytes())
    notes, changed = [], False
    for k, bm in swf.bitmaps(movie):
        verdict = decide(bm)
        if verdict is None:
            continue
        new = treat(bm, *verdict)
        movie.tags[k] = swf.Tag(swf.DEFINE_BITS_LOSSLESS2, swf.encode_lossless2(new), True)
        notes.append(f"{'cleared' if verdict[1] else 'recoloured'} #{bm.char_id} {bm.rgba.shape[1]}x{bm.rgba.shape[0]}")
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
            want = CLEAR.get(rel)

            def decide(bm, want=want, rel=rel):
                if want and (bm.rgba.shape[1], bm.rgba.shape[0]) != want[0]:
                    report["warnings"].append(f"{rel}: expected {want[0]} for {want[1]}, found {bm.rgba.shape[1::-1]}")
                return palette, bool(want)
        elif fnmatch(rel, EMBEDDERS) and p.suffix.lower() == ".swf":
            def decide(bm):
                c = seen.get(digest(bm.rgba))
                return None if c is None else (palette, c)
        else:
            continue
        blob, notes = rewrite(p, decide)
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
