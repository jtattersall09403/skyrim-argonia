"""The light Black Marsh retheme of Dear Diary (1.2 §a), as a recipe run at install on the player's machine (0014).

Dear Diary's menus draw their paper, frames and ornaments from bitmaps embedded in SWFs (DefineBitsLossless2): every
menu loads its interface/deardiary/**/<menu>_BG.swf at run time, and Wood and Paper (44174) replaces some of those.
The Oblivion-like Loading Menu (38708) draws its sheet from a bitmap in its loadingmenu.swf. Only the main menu's
wallpaper is a DDS, and it is Skyrim's map with the "Skyrim" wordmark, so it is replaced outright by our title
wallpaper (ui/title/title.py), not recoloured.

    python -m tools.ui_theme.retheme --mods <dear-diary> <wood-and-paper> \
        --ttf Pelagiad.ttf --out out/ui_theme/argonia-theme

The mod roots are the installed folders, lowest priority first. The output is an overlay mod laid above them: every
*_BG.swf winner and the loading menu with its bitmaps recoloured to our palette (tools/ui_theme/palette.py), the
Nordic watermarks cleared, the copies of those bitmaps the menu SWFs embed treated alike, and the wallpaper DDS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from fnmatch import fnmatch
from pathlib import Path

import numpy as np

from tools.ui_theme import swf
from tools.ui_theme.palette import EdgedFramePalette, FramePalette, JournalFramePalette, Palette

SCOPE = ("interface/deardiary/*_bg.swf", "interface/loadingmenu.swf")
# SWFs whose vector shapes (DefineShape fills and lines) are recoloured too: the menus and SkyUI's lists, plates and
# icons; ui-review4 found the barter and container name plates' red knot drawn as a shape, not a bitmap.
SHAPES = ("interface/*.swf", "interface/skyui/*.swf", "interface/deardiary/*_bg.swf")
NO_SHAPES = ("interface/fonts_*.swf",)
# The pages our System pane hands over (owner look 1): Settings and Load (the Journal's System page; the Journal's
# quests are our paper book, so this movie shows nothing else), the Mod configuration pages, message boxes and
# lockpicking. Their art, shapes and embedded copies take the frame style (FramePalette), not the light sheet.
FRAME = ("interface/quest_journal.swf", "interface/deardiary/quest_journal/*_bg.swf",
         "interface/skyui/configpanel.swf", "interface/deardiary/configpanel/*_bg.swf",
         "interface/messagebox.swf", "interface/deardiary/messagebox/*_bg.swf",
         "interface/lockpickingmenu.swf", "interface/deardiary/lockpickingmenu/*_bg.swf")
# Of those, the sheets whose own art has no frame: they take the System pane's panel edge too.
EDGED = ("interface/deardiary/messagebox/*_bg.swf", "interface/deardiary/lockpickingmenu/*_bg.swf")
# The Journal's System page sheet: redrawn on its panel layout, not recoloured (its torn band read as a cream rag).
JOURNAL = ("interface/deardiary/quest_journal/*_bg.swf",)
EMBEDDERS = "interface/*.swf"  # menu SWFs carrying copies of the BG bitmaps (fallbacks): matched by their pixels
# Nordic marks (0006), by path and the bitmap's measured size (w, h); cleared to transparent, not recoloured.
CLEAR = {
    "interface/deardiary/map/map_bonus_bg.swf": ((542, 577), "the horned Dragonborn helmet watermark"),
    "interface/deardiary/inventory/craftingmenu_enchanting_bg.swf": ((197, 408), "Skyrim's barbed enchanting sigil"),
}
WALLPAPER = "textures/interface/objects/mainmenuwallpaper.dds"
# Movies the engine stretches to the screen (exact fit): a 16:9 stage on the phone's near-square stream squashed the
# loading fact sideways (owner play test 8; g21-load2, 2240x2068). `showAll` keeps the stage's aspect (1.9 §6).
# The pause hub and the Journal's System page squashed their labels sideways the same way (owner play test 10).
SCALE_MODE = {"interface/loadingmenu.swf": "showAll", "interface/tweenmenu.swf": "showAll",
              "interface/quest_journal.swf": "showAll"}


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


DO_ACTION, DO_INIT_ACTION, ACTION_PUSH, ACTION_POOL, ACTION_SET_MEMBER = 12, 59, 0x96, 0x88, 0x4F


def script_text_colours(data: bytes, base: int) -> list[tuple[int, int]]:
    """(offset, value) of every int32 an AS2 action stream pushes as a `textColor` it then sets: the list rows'
    run-time colours (BSScrollingList and QuestCenteredList SetEntryText), which no DefineEditText carries."""
    out, pool, armed, p = [], [], False, base
    while p < len(data):
        code = data[p]
        if code < 0x80:
            if code == ACTION_SET_MEMBER:
                armed = False
            p += 1
            continue
        n = int.from_bytes(data[p + 1:p + 3], "little")
        body, start = data[p + 3:p + 3 + n], p + 3
        if code == ACTION_POOL:
            pool, q = [], 2
            for _ in range(int.from_bytes(body[:2], "little")):
                e = body.index(0, q)
                pool.append(body[q:e])
                q = e + 1
        elif code == ACTION_PUSH:
            q = 0
            while q < len(body):
                ty = body[q]
                q += 1
                if ty == 0:
                    e = body.index(0, q)
                    armed |= body[q:e] in (b"textColor", b"color")
                    q = e + 1
                elif ty == 7:
                    if armed:
                        out.append((start + q, int.from_bytes(body[q:q + 4], "little", signed=True)))
                    q += 4
                elif ty in (8, 9):
                    k = body[q] if ty == 8 else int.from_bytes(body[q:q + 2], "little")
                    armed |= k < len(pool) and pool[k] in (b"textColor", b"color")
                    q += 1 if ty == 8 else 2
                else:
                    q += {1: 4, 2: 0, 3: 0, 4: 1, 5: 1, 6: 8}.get(ty, len(body))
        p += 3 + n
    return out


def recolour_script_text(movie: swf.Movie, palette: FramePalette) -> int:
    """The list rows' run-time text colours moved onto the frame text tokens in place: the dark-red mark (Dear
    Diary's highlighted row, 0x640000) to the head colour, the rest to the body text; the count."""
    n = 0
    for k, tag in enumerate(movie.tags):
        if tag.code not in (DO_ACTION, DO_INIT_ACTION):
            continue
        base = 2 if tag.code == DO_INIT_ACTION else 0
        hits = script_text_colours(tag.data, base)
        if not hits:
            continue
        data = bytearray(tag.data)
        for off, v in hits:
            rgb = ((v >> 16) & 255, (v >> 8) & 255, v & 255)
            if rgb[0] > 2 * max(rgb[1], rgb[2]) + 40:
                r, g, b = (int(round(c * 255)) for c in palette.t["frame-head"])
            else:
                r, g, b = palette.text(rgb)
            data[off:off + 4] = ((r << 16) | (g << 8) | b).to_bytes(4, "little", signed=True)
        movie.tags[k] = swf.Tag(tag.code, bytes(data), tag.long)
        n += len(hits)
    return n


def edit_text_colour(data: bytes) -> int | None:
    """The offset of a DefineEditText's RGBA text colour, or None when it sets none."""
    nbits = data[2] >> 3
    p = 2 + (5 + 4 * nbits + 7) // 8
    f1, f2 = data[p], data[p + 1]
    p += 2
    if f1 & 1:  # HasFont: the font id
        p += 2
    if f2 & 0x80:  # HasFontClass: a string
        p = data.index(0, p) + 1
    if f1 & 1:  # the font height
        p += 2
    return p if f1 & 4 else None


def recolour_text(movie: swf.Movie, palette: FramePalette) -> int:
    """Every text field's own colour moved onto the frame text tokens in place, alpha kept; the count."""
    n = 0
    for k, tag in enumerate(movie.tags):
        if tag.code != DEFINE_EDIT_TEXT or (o := edit_text_colour(tag.data)) is None:
            continue
        data = bytearray(tag.data)
        data[o:o + 3] = bytes(palette.text(tuple(data[o:o + 3])))
        # the initial HTML text's own <font color="#rrggbb"> overrides the field colour (r5 16:03: the category list,
        # the date line, Level and the button labels stayed black): each moves to the same token, same length
        data = bytearray(HTML_COLOUR.sub(lambda m: b'color="#%02x%02x%02x"' % palette.text(
            tuple(int(m.group(1)[i:i + 2], 16) for i in (0, 2, 4))), bytes(data)))
        movie.tags[k] = swf.Tag(tag.code, bytes(data), tag.long)
        n += 1
    return n


DEFINE_EDIT_TEXT = 37
HTML_COLOUR = re.compile(rb'color="#([0-9a-fA-F]{6})"')


def rewrite(path: Path, decide, palette: Palette | None = None, scale_mode: str | None = None
            ) -> tuple[bytes | None, list[str]]:
    """The movie with each bitmap decide(bitmap) returns a treatment for replaced, its vector colours mapped when
    a palette is given, and its stage scale mode set when one is given; None when nothing changed."""
    movie = swf.read(path.read_bytes())
    notes, changed = [], False
    if scale_mode:
        swf.set_stage_scale_mode(movie, scale_mode)
        notes.append(f"stage scale mode {scale_mode}")
        changed = True
    if palette is not None and (n := recolour_shapes(movie, palette)):
        notes.append(f"recoloured {n} shape colours")
        changed = True
    if isinstance(palette, FramePalette) and (n := recolour_text(movie, palette)):
        notes.append(f"recoloured {n} text field colours")
        changed = True
    if isinstance(palette, FramePalette) and (n := recolour_script_text(movie, palette)):
        notes.append(f"recoloured {n} run-time text colours")
        changed = True
    for k, bm in swf.bitmaps(movie):
        verdict = decide(bm)
        if verdict is None:
            continue
        new = treat(bm, *verdict)
        movie.tags[k] = swf.Tag(swf.DEFINE_BITS_LOSSLESS2, swf.encode_lossless2(new), True)
        notes.append(f"{'cleared' if verdict[1] else 'recoloured'} #{bm.char_id} {bm.rgba.shape[1]}x{bm.rgba.shape[0]}")
        changed = True
    return (movie.to_bytes() if changed else None), notes


def framed(rel: str) -> bool:
    return any(fnmatch(rel, s) for s in FRAME)


def run(roots: list[Path], out: Path, palette: Palette, ttf: Path | None, frame: Palette | None = None) -> dict:
    files = winners(roots)
    frame = frame or FramePalette()
    light = palette
    edged = EdgedFramePalette()
    report: dict = {"files": {}, "warnings": []}
    seen: dict[str, bool] = {}  # pixel digest of every in-scope bitmap, from every root -> cleared?
    for root in roots:
        for p in root.rglob("*"):
            rel = str(p.relative_to(root)).replace("\\", "/").lower()
            if p.is_file() and any(fnmatch(rel, s) for s in SCOPE):
                for _k, bm in swf.bitmaps(swf.read(p.read_bytes())):
                    seen[digest(bm.rgba)] = rel in CLEAR
    for rel, p in sorted(files.items()):
        palette = frame if framed(rel) else light
        in_scope = any(fnmatch(rel, s) for s in SCOPE)
        if in_scope:
            want = CLEAR.get(rel)

            bg_palette = edged if any(fnmatch(rel, e) for e in EDGED) else palette
            if any(fnmatch(rel, j) for j in JOURNAL):
                bg_palette = JournalFramePalette()

            def decide(bm, want=want, rel=rel, palette=bg_palette):
                if want and (bm.rgba.shape[1], bm.rgba.shape[0]) != want[0]:
                    report["warnings"].append(f"{rel}: expected {want[0]} for {want[1]}, found {bm.rgba.shape[1::-1]}")
                return palette, bool(want)
        elif fnmatch(rel, EMBEDDERS) and p.suffix.lower() == ".swf":
            def decide(bm, palette=palette):
                c = seen.get(digest(bm.rgba))
                return None if c is None else (palette, c)
        elif any(fnmatch(rel, s) for s in SHAPES):
            def decide(bm):
                return None
        else:
            continue
        shapes = any(fnmatch(rel, s) for s in SHAPES) and not any(fnmatch(rel, s) for s in NO_SHAPES)
        blob, notes = rewrite(p, decide, palette if shapes else None, SCALE_MODE.get(rel))
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
        title.wallpaper(ttf, light).save(dest, pixel_format="DXT1")
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
