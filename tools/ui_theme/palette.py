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


class FramePalette(Palette):
    """The frame style (DESIGN.md, 1.12 §3) for the Dear Diary pages our System pane hands over: Settings and Load
    (the Journal's System page), the Mod configuration pages, message boxes and lockpicking (owner look 1).

    The page is inverted onto the frame tokens: the paper becomes the frame ground, the ink the frame text, the sheet's
    rim the gold-green trim. The saturated wood and leather frames take Wind UI's trim ramp by luminance (ground,
    trim, lit trim), so they read as the filigree rule rather than as light text.
    """

    def __init__(self, t: dict[str, tuple[int, int, int]] | None = None):
        t = t or tokens()
        need = ("frame-ground", "frame-trim", "frame-trim-hi", "frame-text", "frame-text-soft", "frame-head")
        missing = [k for k in need if k not in t]
        if missing:
            raise KeyError(f"theme.css lacks {missing}")
        self.t = {k: np.array(v, np.float32) / 255 for k, v in t.items()}
        g = self.t["frame-ground"]
        # the art carries no ink (the text is the movies' own fields): the paper (luminance 0.4-0.7) flattens to the
        # ground with a faint mottle, and its drop shadow stays dark, so nothing outshines the pane
        self.stops = [(0.00, g * 0.4), (0.30, g * 0.8), (0.45, g), (0.60, g * 1.15), (1.00, g * 1.4)]
        self.trim = [(0.00, g), (0.06, self.t["frame-trim"]), (0.22, self.t["frame-trim-hi"]), (0.60, self.t["frame-trim-hi"]),
                     (1.00, self.t["frame-trim-hi"])]

    def apply(self, rgba: np.ndarray) -> np.ndarray:
        rgb = rgba[..., :3].astype(np.float32) / 255
        lum = luma(rgb)
        _h, s, _v = hsv(rgb)
        page = self.tone(lum)
        xs = np.array([k[0] for k in self.trim], np.float32)
        trim = np.stack([np.interp(lum, xs, np.array([k[1][c] for k in self.trim], np.float32)) for c in range(3)], -1)
        # the wood frames are dark and saturated (value 0.2-0.35, saturation from 0.5); the paper's stains are
        # bright or weak and stay page
        w = np.clip((s - 0.45) / 0.12, 0, 1) * np.clip((0.28 - lum) / 0.08, 0, 1)
        w = (w * w * (3 - 2 * w))[..., None]
        out = page * (1 - w) + trim * w
        res = rgba.copy()
        res[..., :3] = np.clip(np.rint(out * 255), 0, 255).astype(np.uint8)
        return res

    def text(self, rgb: tuple[int, int, int]) -> tuple[int, int, int]:
        """A text field's colour on the frame ground: dark ink and grey become the body text, white the title text,
        so every field reads light (DESIGN.md: frame-text, frame-head)."""
        lum = float(luma(np.array(rgb, np.float32) / 255))
        key = "frame-head" if lum > 0.9 else "frame-text"
        return tuple(int(round(v * 255)) for v in self.t[key])

    def edge(self, rgba: np.ndarray) -> np.ndarray:
        """The System pane's panel edge drawn on a bare sheet (message box, lockpicking): a lit trim rule inset from
        the opaque bounds, a fainter inner rule, and a lozenge at each corner."""
        out = rgba.copy()
        ys, xs = np.nonzero(rgba[..., 3] > 128)
        if len(xs) == 0:
            return out
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        hi = np.rint(self.t["frame-trim-hi"] * 255).astype(np.uint8)
        lo = np.rint(self.t["frame-trim"] * 255).astype(np.uint8)

        def rule(k: int, w: int, c: np.ndarray) -> None:
            a, b, c0, c1 = y0 + k, y1 - k, x0 + k, x1 - k
            if b - a < 2 * w or c1 - c0 < 2 * w:
                return
            for sl in ((slice(a, a + w), slice(c0, c1 + 1)), (slice(b - w + 1, b + 1), slice(c0, c1 + 1)),
                       (slice(a, b + 1), slice(c0, c0 + w)), (slice(a, b + 1), slice(c1 - w + 1, c1 + 1))):
                out[sl][..., :3] = c
                out[sl][..., 3] = 255

        rule(2, 8, lo)  # the band, as heavy as the large pages' painted frames
        rule(3, 2, hi)  # its lit edge
        rule(8, 1, hi)
        rule(14, 2, lo)  # the inner rule
        r = 9
        yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
        diamond = (np.abs(yy) + np.abs(xx)) <= r
        for cy, cx in ((y0 + 6, x0 + 6), (y0 + 6, x1 - 6), (y1 - 6, x0 + 6), (y1 - 6, x1 - 6)):
            ya, xa = max(cy - r, 0), max(cx - r, 0)
            sub = out[ya:cy + r + 1, xa:cx + r + 1]
            m = diamond[ya - (cy - r):ya - (cy - r) + sub.shape[0], xa - (cx - r):xa - (cx - r) + sub.shape[1]]
            sub[m, :3] = hi
            sub[m, 3] = 255
        return out


class EdgedFramePalette(FramePalette):
    """FramePalette with the panel edge added: for the sheets whose own art carries no frame."""

    def apply(self, rgba: np.ndarray) -> np.ndarray:
        return self.edge(super().apply(rgba))


def _box(mask: np.ndarray, r: int) -> np.ndarray:
    """The mean of a boolean mask over a (2r+1)^2 box, by an integral image (no scipy on the player's machine)."""
    m = np.pad(mask.astype(np.float32), r + 1, mode="edge")
    ii = m.cumsum(0).cumsum(1)
    k = 2 * r + 1
    s = ii[k:, k:] - ii[:-k, k:] - ii[k:, :-k] + ii[:-k, :-k]
    return s[:mask.shape[0], :mask.shape[1]] / (k * k)


def _components(mask: np.ndarray, step: int = 4) -> list[tuple[int, int, int, int]]:
    """Bounding boxes (x0, y0, x1, y1) of a mask's 4-connected parts, found on a 1/step grid."""
    m = mask[::step, ::step]
    seen = np.zeros_like(m)
    out = []
    for y0, x0 in zip(*np.nonzero(m)):
        if seen[y0, x0]:
            continue
        stack, ys, xs = [(y0, x0)], [], []
        seen[y0, x0] = True
        while stack:
            y, x = stack.pop()
            ys.append(y)
            xs.append(x)
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < m.shape[0] and 0 <= xx < m.shape[1] and m[yy, xx] and not seen[yy, xx]:
                    seen[yy, xx] = True
                    stack.append((yy, xx))
        out.append((min(xs) * step, min(ys) * step, max(xs) * step + step - 1, max(ys) * step + step - 1))
    return out


class JournalFramePalette(FramePalette):
    """The Journal's System page sheet (Wood and Paper's quest_journal_BG, 1036x687; lane 1.12-r5-system-pages).

    Recolouring keeps its torn wood band, which reads as a wide cream rag at play size. Here the sheet is redrawn on
    its own panel layout: each panel (a part of the sheet inside the band) becomes a straight rectangle on the frame
    ground with the System pane's double rule (lit trim, inner trim), the rag goes, and the empty header slots above
    the panels are cleared.
    """

    def apply(self, rgba: np.ndarray) -> np.ndarray:
        rgb = rgba[..., :3].astype(np.float32) / 255
        lum = luma(rgb)
        _h, s, _v = hsv(rgb)
        opaque = rgba[..., 3] > 128
        band = opaque & (s > 0.45) & (lum < 0.28)
        inner = (_box(opaque, 6) > 0.5) & ~(_box(band, 6) > 0.35)
        boxes = [b for b in _components(inner) if (b[2] - b[0]) * (b[3] - b[1]) > 0.01 * inner.size]
        out = np.zeros_like(rgba)
        if not boxes:
            return super().apply(rgba)
        top = min(b[1] for b in boxes if (b[3] - b[1]) > 0.3 * rgba.shape[0])
        boxes = [b for b in boxes if b[1] >= top - 8]  # the header slots sit above the panels
        # the button tab under the panels runs to the pane's right edge: the Load page's three buttons (Delete,
        # Character Selection, Cancel) overran its 370 px (r5 still 11)
        bottom, right = max(b[3] for b in boxes if b[1] < top + 8), max(b[2] for b in boxes)
        boxes = [(b[0], b[1], right, b[3]) if b[1] > bottom else b for b in boxes]
        g = np.rint(self.t["frame-ground"] * 255).astype(np.uint8)
        hi = np.rint(self.t["frame-trim-hi"] * 255).astype(np.uint8)
        lo = np.rint(self.t["frame-trim"] * 255).astype(np.uint8)
        h, w = rgba.shape[:2]

        def rect(x0, y0, x1, y1, c, a, fill=False, t=1):
            x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, w - 1), min(y1, h - 1)
            if fill:
                out[y0:y1 + 1, x0:x1 + 1, :3] = c
                out[y0:y1 + 1, x0:x1 + 1, 3] = a
                return
            for sl in ((slice(y0, y0 + t), slice(x0, x1 + 1)), (slice(y1 - t + 1, y1 + 1), slice(x0, x1 + 1)),
                       (slice(y0, y1 + 1), slice(x0, x0 + t)), (slice(y0, y1 + 1), slice(x1 - t + 1, x1 + 1))):
                out[sl[0], sl[1], :3] = c
                out[sl[0], sl[1], 3] = a

        for x0, y0, x1, y1 in boxes:  # the ground first, 10 px beyond each panel, so neighbours share one sheet
            rect(x0 - 10, y0 - 10, x1 + 10, y1 + 10, g, 255, fill=True)  # opaque, as 08 (0.95 let play show through)
        for x0, y0, x1, y1 in boxes:
            rect(x0 - 6, y0 - 6, x1 + 6, y1 + 6, hi, 255, t=2)  # the lit rule
            rect(x0 - 2, y0 - 2, x1 + 2, y1 + 2, lo, 255)  # the inner trim
        return out
