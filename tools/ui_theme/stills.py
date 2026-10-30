"""L3 stills for the theme (1.2 §a): before and after mocks of the main menu and the inventory, composited from the
real bitmaps (Dear Diary's as installed, then the recoloured overlay) with the text drawn from the real font library
SWFs (Dear Diary's fonts_fritzq.swf before, our fonts_pelagiad.swf after). A static mock: the layout is an
approximation of the screens in Dear Diary's own previews; the colours, frames and glyphs are the files the game
loads. Output stays in out/ (derived art from mod files, never committed).

    python -m tools.ui_theme.stills --mods <dear-diary> <wood-and-paper> --theme out/ui_theme/argonia-theme \
        --fontlib out/ui_theme/fonts/interface/fonts_pelagiad.swf --out out/ui_theme/stills
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from tools.ui_theme import swf
from tools.ui_theme.retheme import WALLPAPER, winners

SCREEN = (1920, 1080)
WALL_VIEW = (140, 309, 1850, 1270)  # the wallpaper's texels the main menu shows, fitted to Dear Diary's preview


def load_font(path: Path) -> swf.Font:
    movie = swf.read(path.read_bytes())
    return swf.parse_define_font3(next(t.data for t in movie.tags if t.code == swf.DEFINE_FONT3))


def flatten(contour, k: float, ox: float, oy: float, steps: int = 6) -> list[tuple[float, float]]:
    (sx, sy), segs = contour
    pts, x, y = [(ox + sx * k, oy + sy * k)], sx, sy
    for seg in segs:
        if seg[0] == "L":
            x, y = seg[1], seg[2]
            pts.append((ox + x * k, oy + y * k))
        else:
            cx, cy, ex, ey = seg[1:]
            for i in range(1, steps + 1):
                t = i / steps
                px = (1 - t) ** 2 * x + 2 * (1 - t) * t * cx + t * t * ex
                py = (1 - t) ** 2 * y + 2 * (1 - t) * t * cy + t * t * ey
                pts.append((ox + px * k, oy + py * k))
            x, y = ex, ey
    return pts


def text(img: Image.Image, font: swf.Font, s: str, xy: tuple[float, float], size: float, rgba, anchor="l"):
    """Draw s with the font library's own glyphs (even-odd fill, 4x supersampled); xy is the baseline start."""
    ss = 4
    k = size / swf.FONT_EM
    width = sum(font.glyphs[ord(c)].advance * k if ord(c) in font.glyphs else size * 0.3 for c in s)
    x0 = xy[0] - (width / 2 if anchor == "m" else width if anchor == "r" else 0)
    top = int(xy[1] - size * 1.1)
    w, h = int(width + size) + 2, int(size * 1.6) + 2
    mask = np.zeros((h * ss, w * ss), bool)
    pen = 0.0
    for c in s:
        g = font.glyphs.get(ord(c))
        if g is None:
            pen += size * 0.3
            continue
        for contour in swf.decode_glyph(g.shape):
            pts = flatten(contour, k * ss, (pen + size * 0.5) * ss, (xy[1] - top) * ss)
            if len(pts) > 2:
                layer = Image.new("1", (w * ss, h * ss), 0)
                ImageDraw.Draw(layer).polygon(pts, fill=1)
                mask ^= np.asarray(layer, bool)
        pen += g.advance * k
    alpha = Image.fromarray((mask * 255).astype(np.uint8)).resize((w, h), Image.Resampling.BOX)
    a = (np.asarray(alpha, np.float32) * (rgba[3] / 255)).astype(np.uint8)
    tile = np.zeros((h, w, 4), np.uint8)
    tile[..., :3] = rgba[:3]
    tile[..., 3] = a
    img.alpha_composite(Image.fromarray(tile), (int(x0 - size * 0.5), top))


def bg(files: dict[str, Path], rel: str) -> Image.Image:
    return Image.fromarray(swf.bitmaps(swf.read(files[rel].read_bytes()))[0][1].rgba)


def fit(im: Image.Image, h: int) -> Image.Image:
    return im.resize((round(im.width * h / im.height), h), Image.Resampling.LANCZOS)


def main_menu(files, font, ink, wallpaper: Image.Image) -> Image.Image:
    shot = wallpaper.convert("RGBA").crop(WALL_VIEW).resize(SCREEN, Image.Resampling.LANCZOS)
    panel = fit(bg(files, "interface/deardiary/startmenu/startmenu_load_bg.swf"), 960)
    px = SCREEN[0] - panel.width - 10
    shot.alpha_composite(panel, (px, 60))
    cx = px + panel.width // 2
    text(shot, font, "Ashlander's Rest, Level 3", (cx, 380), 23, ink, "m")
    text(shot, font, "Day 4, Second Seed", (cx, 416), 24, ink, "m")
    for i, row in enumerate(["Gideon", "Stormhold Docks", "The Hist Grove", "Lilmoth Market", "Thorn Landing"]):
        text(shot, font, f"{12 - i}   {row}", (px + 80, 510 + i * 42), 26, ink if i == 0 else (*ink[:3], 140))
    for i, row in enumerate(["CONTINUE", "NEW", "LOAD", "SETTINGS", "QUIT"]):
        text(shot, font, row, (1180, 560 + i * 48), 26, (241, 232, 207, 255), "r")
    return shot


def inventory(files, font, ink, accent) -> Image.Image:
    yy = np.linspace(0, 1, SCREEN[1], dtype=np.float32)[:, None, None]
    sky = (np.array([52, 60, 44], np.float32) * (1 - yy) + np.array([20, 24, 16], np.float32) * yy)
    shot = Image.fromarray(np.broadcast_to(sky, (SCREEN[1], SCREEN[0], 3)).astype(np.uint8)).convert("RGBA")
    lists = fit(bg(files, "interface/deardiary/inventory/inventorylists_bg.swf"), 900)
    shot.alpha_composite(lists, (60, 60))
    card = fit(bg(files, "interface/deardiary/inventory/itemcard_1_bg.swf"), 260)
    shot.alpha_composite(card, ((SCREEN[0] - card.width) // 2 + 300, 760))
    cats = ["ALL", "WEAPONS", "APPAREL", "POTIONS", "FOOD", "MISC"]
    for i, c in enumerate(cats):
        text(shot, font, c, (150, 220 + i * 52), 28, accent if i == 1 else ink)
    items = [("Chitin Spear", "9"), ("Bonemold Dagger", "6"), ("Reed Bow", "8"), ("Marsh Hatchet", "7")]
    for i, (n, v) in enumerate(items):
        text(shot, font, n, (420, 220 + i * 52), 28, ink)
        text(shot, font, v, (740, 220 + i * 52), 28, ink, "r")
    cx = (SCREEN[0] - card.width) // 2 + 300 + card.width // 2
    text(shot, font, "Chitin Spear", (cx, 840), 34, ink, "m")
    text(shot, font, "Damage 9    Weight 6    Value 40", (cx, 900), 26, ink, "m")
    return shot


def run(mods: list[Path], theme: Path, fontlib: Path, before_font: Path, out: Path, ttf: Path | None) -> list[Path]:
    before = winners(mods)
    after = dict(before)
    after.update(winners([theme]))
    out.mkdir(parents=True, exist_ok=True)
    fb, fa = load_font(before_font), load_font(fontlib)
    ink_b, ink_a = (40, 32, 24, 255), (42, 32, 21, 255)  # Dear Diary's text colour is set in its SWFs; ours is --ink
    shots = {
        "main-menu-before": main_menu(before, fb, ink_b, Image.open(before[WALLPAPER])),
        "main-menu-after": main_menu(after, fa, ink_a, Image.open(after[WALLPAPER])),
        "inventory-before": inventory(before, fb, ink_b, (120, 30, 20, 255)),
        "inventory-after": inventory(after, fa, ink_a, (123, 47, 29, 255)),
    }
    paths = []
    for name, im in shots.items():
        p = out / f"{name}.png"
        im.convert("RGB").save(p)
        paths.append(p)
    return paths


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mods", type=Path, nargs="+", required=True)
    ap.add_argument("--theme", type=Path, required=True)
    ap.add_argument("--fontlib", type=Path, required=True)
    ap.add_argument("--before-font", type=Path, help="Dear Diary's fonts_fritzq.swf (default: found in --mods)")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    before_font = a.before_font or winners(a.mods)["interface/fonts_fritzq.swf"]
    for p in run(a.mods, a.theme, a.fontlib, before_font, a.out, None):
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
