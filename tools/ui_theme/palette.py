"""Our palette applied to Dear Diary's art (1.2 §a, the light Black Marsh retheme; ui/DESIGN.md's colour table).

The tokens are read from ui/views/core/theme.css, the one place they live. The map has two parts:

- **tone:** every pixel's luminance runs through a gradient of the paper and ink tokens, so Dear Diary's grey paper
  becomes our warm sheet and its shadows our brown ink, with the mottle kept;
- **tint:** saturated pixels keep their weight but move to our accents by hue family: the warm dark frames and
  wood to marsh moss, the warm bright leather and wax to red clay (rust), anything green or blue to marsh teal.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np

THEME_CSS = Path(__file__).resolve().parents[2] / "ui" / "views" / "core" / "theme.css"


def tokens(css: Path = THEME_CSS) -> dict[str, tuple[int, int, int]]:
    out = {}
    for name, hexv in re.findall(r"--([a-z0-9-]+)\s*:\s*#([0-9a-fA-F]{6})\b", css.read_text()):
        out[name] = tuple(int(hexv[k:k + 2], 16) for k in (0, 2, 4))
    return out


def luma(rgb: np.ndarray) -> np.ndarray:
    return rgb @ np.array([0.2126, 0.7152, 0.0722], np.float32)


def hsv(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Hue in degrees, saturation and value in 0..1, from rgb in 0..1."""
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = mx - mn
    s = np.where(mx > 0, d / np.maximum(mx, 1e-6), 0)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    dd = np.maximum(d, 1e-6)
    h = np.where(mx == r, ((g - b) / dd) % 6, np.where(mx == g, (b - r) / dd + 2, (r - g) / dd + 4)) * 60
    return np.where(d > 0, h, 0), s, mx


class Palette:
    def __init__(self, t: dict[str, tuple[int, int, int]] | None = None):
        t = t or tokens()
        need = ("ink", "ink-soft", "paper-edge", "paper-dark", "paper", "paper-light", "rust", "moss", "link")
        missing = [k for k in need if k not in t]
        if missing:
            raise KeyError(f"theme.css lacks {missing}")
        self.t = {k: np.array(v, np.float32) / 255 for k, v in t.items()}
        ink = self.t["ink"]
        # luminance stops: Dear Diary's paper sits at 0.60-0.68 and its frames at 0.2-0.35; the loading menu's bright
        # parchment (0.85-0.95) holds at the sheet colour, so no sheet outshines the rest (measured 2026-10-30)
        self.stops = [(0.00, ink * 0.45), (0.18, ink), (0.34, self.t["ink-soft"]), (0.48, self.t["paper-edge"]),
                      (0.58, self.t["paper-dark"]), (0.68, self.t["paper"]), (0.88, self.t["paper"]),
                      (1.00, self.t["paper-light"])]

    def tone(self, lum: np.ndarray) -> np.ndarray:
        xs = np.array([s[0] for s in self.stops], np.float32)
        out = np.empty(lum.shape + (3,), np.float32)
        for c in range(3):
            out[..., c] = np.interp(lum, xs, np.array([s[1][c] for s in self.stops], np.float32))
        return out

    def apply(self, rgba: np.ndarray) -> np.ndarray:
        """RGBA uint8 (straight alpha) in, RGBA uint8 out; alpha untouched."""
        rgb = rgba[..., :3].astype(np.float32) / 255
        lum = luma(rgb)
        h, s, v = hsv(rgb)
        neutral = self.tone(lum)
        warm = (h < 50) | (h > 320)
        bright = v >= 0.35  # Dear Diary's frames sit at value 0.2-0.35; its burnt paper edges above
        tint = np.where((warm & ~bright)[..., None], self.t["moss"],
                        np.where(warm[..., None], self.t["rust"], self.t["link"]))
        # the tint carries the tone's luminance, so the mottle and the bevels survive
        tl = luma(tint)
        tinted = np.clip(tint * (luma(neutral) / np.maximum(tl, 1e-3))[..., None], 0, 1)
        # the paper's stains and burnt edges are warm but weak (saturation 0.1-0.45): they keep the tone alone, so
        # they brown rather than go green; the dark frames tint from 0.38, the bright leather and wax from 0.5
        lo = np.where(bright, 0.5, 0.38)
        w = np.clip((s - lo) / 0.15, 0, 1)
        w = (w * w * (3 - 2 * w))[..., None] * 0.8
        out = neutral * (1 - w) + tinted * w
        res = rgba.copy()
        res[..., :3] = np.clip(np.rint(out * 255), 0, 255).astype(np.uint8)
        return res
