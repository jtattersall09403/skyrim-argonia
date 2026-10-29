"""The parchment chart (2.W4 §c, 1.2 §e): a deterministic renderer from our own data, no game asset (0003, 0006 §UI).

The look is the old project's "chart" map treatment, which the owner liked (ruling 2026-10-29; the elements and
where each lives in the old repo are in docs/research/journals/chart.md): bone paper; water the lightest ground,
washed pale blue-grey at the shore with three fading ripples; one olive-black ink for the coast, its hachure on the
land side, the tree crowns, the stipple and the marsh tufts; slate water ink for rivers; red-brown lane ink for
roads over a paper casing; explored land a warm tint with contours; Pelagiad labels on a paper glow; the Argonia
place glyphs. Only the look is reused (0026): this renderer is ours, over our own data.

Three layers on one canvas (the master is MASTER^2 px, 2^12; the province fills [M, size - M) at one pixel per terrain sample):
- base      opaque: the paper, and the sea's wash and ripples (water the lightest ground);
- ink       RGBA: the sketch, always shown: the coast and its hachure, the major rivers and roads, the province's
            land border, a compass rose, the seven cities drawn and labelled;
- revealed  RGBA: what exploring fills in, masked per cell by the view: the land's warm tint, relief and 50 m
            contours, the woods (crowns and stipple), the marsh tufts, the minor rivers and tracks, every other
            place drawn and labelled (as the old chart showed land only where it was explored).
The view stacks base, revealed (masked), ink. There is no player-position marker (C9).

Ink weights are set for the 2048 copy (a desktop view) to match the old chart's screen weights: a master pixel is
half an old css pixel. Every stroke is drawn at twice the size into 8-bit masks and box-reduced (antialiasing);
every random choice comes from a generator seeded by a fixed string, so two runs give the same pixels.

    render(features, size) -> Chart      the layers as uint8 arrays, the masks the checks read, the index
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from tools.chart.data import CANOPY as CANOPY_OF, MARSH, SEA, Features

MASTER = 1 << 12  # the master chart, pixels a side (a pixel count, not a Skyrim unit)
MARGIN = 32  # master pixels round the province: one cell
SS = 2  # supersampling of the stroke masks

# Colours (sRGB): the old chart's tokens (old repo packages/ui/src/tokens/map.ts MAP_CHART @ b581910f).
PAPER = (222, 210, 172)
PAPER_DARK = (196, 182, 140)
LAND = (204, 186, 138)
CANOPY = (170, 170, 118)
WATER_OPEN = (238, 234, 214)
WATER_WASH = (198, 212, 204)
INK = (43, 46, 28)
WATER_INK = (40, 62, 60)
LANE_INK = (92, 46, 28)
SHADOW = (40, 34, 20)  # the hillshade's darkening (the old chart scaled the land tint by 0.8-1.06)

GLYPHS = Path(__file__).with_name("glyphs.json")  # the old map's Argonia place glyphs (see glyphs-SOURCE.md)
# A place kind's glyph (old repo packages/ui/src/map/pins.ts PIN; cities are pin-city).
PIN = {"settlement": "pin-settlement", "ruin": "pin-ruin", "lair": "pin-cave", "sacred": "pin-shrine",
       "transit": "pin-docks", "works": "pin-mine", "camp": "pin-camp", "lone": "pin-farm", "martial": "pin-fort",
       "civic": "pin-landmark"}

FONT_SHA256 = "b282ea043af32e15bab8cf9e01d9625c0fa5032761ffbc57d7a5f939098a7d92"
FONT_URL = "https://raw.githubusercontent.com/isaskar/Pelagiad/f981301916d0e5a7ea9ce39d2af4e56df09677ca/Pelagiad.ttf"


def font_path() -> Path:
    env = os.environ.get("ARGONIA_CHART_FONT")
    if env:
        return Path(env)
    root = Path(os.environ.get("ARGONIA_PRIVATE") or Path.home() / "argonia-private")
    return root / "fonts" / "pelagiad" / "Pelagiad.ttf"


def fetch_font() -> Path:
    """Download Pelagiad (OFL) at the pinned upstream commit into the private tree; never into the repo."""
    import urllib.request

    p = font_path()
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(FONT_URL, timeout=60) as r:
            p.write_bytes(r.read())
        lic = p.parent / "LICENSE.txt"
        if not lic.exists():
            with urllib.request.urlopen(FONT_URL.rsplit("/", 1)[0] + "/LICENSE.txt", timeout=60) as r:
                lic.write_bytes(r.read())
    got = hashlib.sha256(p.read_bytes()).hexdigest()
    if got != FONT_SHA256:
        raise SystemExit(f"{p}: sha256 {got}, expected {FONT_SHA256}")
    return p


def seed(name: str) -> np.random.Generator:
    return np.random.default_rng(int.from_bytes(hashlib.sha256(name.encode()).digest()[:8], "little"))


# ---- array helpers ---------------------------------------------------------------------------------------------
def box(a: np.ndarray, r: int, axis: int) -> np.ndarray:
    if r <= 0:
        return a
    pad = [(0, 0)] * a.ndim
    pad[axis] = (r + 1, r)
    c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis, dtype=np.float32)
    hi = np.take(c, np.arange(2 * r + 1, c.shape[axis]), axis=axis)
    lo = np.take(c, np.arange(0, c.shape[axis] - 2 * r - 1), axis=axis)
    return (hi - lo) / np.float32(2 * r + 1)


def blur(a: np.ndarray, r: int, passes: int = 2) -> np.ndarray:
    a = a.astype(np.float32)
    for _ in range(passes):
        a = box(box(a, r, 0), r, 1)
    return a


def lerp(a: np.ndarray, size: int, axis: int, lo: int = 0, hi: int | None = None) -> np.ndarray:
    """Linear upsampling of `a` along `axis` to `size` samples (pixel centres aligned), output rows [lo, hi)."""
    n = a.shape[axis]
    x = (np.arange(lo, size if hi is None else hi, dtype=np.float32) + 0.5) * n / size - 0.5
    x = np.clip(x, 0, n - 1)
    i = np.minimum(np.floor(x).astype(np.int64), n - 2) if n > 1 else np.zeros(x.shape, np.int64)
    t = (x - i).astype(np.float32)
    a0, a1 = np.take(a, i, axis=axis), np.take(a, np.minimum(i + 1, n - 1), axis=axis)
    shape = [1] * a.ndim
    shape[axis] = -1
    t = t.reshape(shape)
    return (a0 * (1 - t) + a1 * t).astype(np.float32)


def iso_line(f: np.ndarray, t, half_w: float) -> np.ndarray:
    """Antialiased alpha of the level set f = t (t a scalar or an array), half_w pixels either side."""
    gy, gx = np.gradient(f)
    g = np.hypot(gx, gy)
    del gx, gy
    d = np.abs(f - t) / np.maximum(g, 1e-6)
    return np.clip(half_w + 0.5 - d, 0, 1).astype(np.float32)


def smooth(a: float, b: float, v):
    t = np.clip((v - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def to_u8(a: np.ndarray) -> np.ndarray:
    return np.clip(np.rint(a * 255), 0, 255).astype(np.uint8)


def dilate(m: np.ndarray, diag: bool) -> np.ndarray:
    o = m.copy()
    o[1:] |= m[:-1]
    o[:-1] |= m[1:]
    o[:, 1:] |= m[:, :-1]
    o[:, :-1] |= m[:, 1:]
    if diag:
        o[1:, 1:] |= m[:-1, :-1]
        o[:-1, :-1] |= m[1:, 1:]
        o[1:, :-1] |= m[:-1, 1:]
        o[:-1, 1:] |= m[1:, :-1]
    return o


# ---- strokes ---------------------------------------------------------------------------------------------------
class Pen:
    """A supersampled 8-bit mask to draw strokes and text on; `done()` box-reduces it to the canvas."""

    def __init__(self, size: int):
        self.im = Image.new("L", (size * SS, size * SS), 0)
        self.d = ImageDraw.Draw(self.im)

    def done(self) -> np.ndarray:
        return np.asarray(self.im.reduce(SS))


def wobble(pts: np.ndarray, rng: np.random.Generator, step: float, amp: float, wavelength: float,
           smooth: int = 5) -> np.ndarray:
    """A polyline (n, 2 px) resampled every `step` px, its tracing jags smoothed, with a hand's slow wobble."""
    seg = np.hypot(*np.diff(pts, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    if s[-1] <= 0:
        return pts[:1]
    t = np.linspace(0, s[-1], max(2, int(s[-1] / step) + 1))
    p = np.stack([np.interp(t, s, pts[:, 0]), np.interp(t, s, pts[:, 1])], axis=1)
    if len(p) > smooth > 1:
        k = np.ones(smooth) / smooth
        q = np.pad(p, ((smooth // 2, smooth // 2), (0, 0)), mode="edge")
        p = np.stack([np.convolve(q[:, 0], k, "valid"), np.convolve(q[:, 1], k, "valid")], axis=1)
    if amp > 0 and len(p) > 2:
        w = max(3, int(wavelength / step))
        r = rng.normal(size=len(p) + 2 * w)
        h = np.hanning(w)
        r = np.convolve(r, h / h.sum(), "same")[w:w + len(p)]
        r = np.clip(r / (r.std() + 1e-9), -2, 2) * amp  # a hand wanders, within two amplitudes
        tx, ty = np.gradient(p[:, 0]), np.gradient(p[:, 1])
        n = np.hypot(tx, ty) + 1e-9
        p = p + np.stack([-ty / n * r, tx / n * r], axis=1)
    return p


def line(pen: Pen, p: np.ndarray, width: float) -> None:
    """One even stroke along p (canvas px), round-jointed."""
    if len(p) >= 2:
        pen.d.line([(float(x) * SS, float(y) * SS) for x, y in p], fill=255, width=max(1, round(width * SS)),
                   joint="curve")


def dashes(p: np.ndarray, pattern: tuple[float, ...]) -> list[np.ndarray]:
    """Cut a resampled polyline into on-pieces by a (on, off, on, off...) arc-length pattern."""
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(p, axis=0).T))])
    out, period = [], sum(pattern)
    if s[-1] <= 0:
        return out
    pos, k = 0.0, 0
    while pos < s[-1]:
        ln = pattern[k % len(pattern)]
        if k % 2 == 0:
            a, b = pos, min(pos + ln, s[-1])
            sel = (s > a) & (s < b)
            piece = np.concatenate([[[np.interp(a, s, p[:, 0]), np.interp(a, s, p[:, 1])]], p[sel],
                                    [[np.interp(b, s, p[:, 0]), np.interp(b, s, p[:, 1])]]])
            if b > a:
                out.append(piece)
        pos += ln
        k += 1
        if period <= 0:
            break
    return out


_GLYPH_RINGS: dict[str, list[np.ndarray]] = {}


def glyph_rings(name: str) -> list[np.ndarray]:
    """The rings of one old-map glyph (a 100-unit box, one even-odd path of M...Z polygons)."""
    if not _GLYPH_RINGS:
        for k, v in json.loads(GLYPHS.read_text()).items():
            _GLYPH_RINGS[k] = [np.array(list(map(float, ring.split())), np.float64).reshape(-1, 2) / 100
                               for ring in re.findall(r"M([^MZ]*)Z", v["d"])]
    return _GLYPH_RINGS.get(name) or _GLYPH_RINGS["pin-landmark"]


_GLYPH_IM: dict[tuple[str, int], Image.Image] = {}


def glyph_image(name: str, side: int) -> Image.Image:
    """The glyph filled even-odd into a side x side 8-bit image (supersampled px)."""
    key = (name, side)
    if key not in _GLYPH_IM:
        acc = np.zeros((side, side), bool)
        for ring in glyph_rings(name):
            im = Image.new("L", (side, side), 0)
            ImageDraw.Draw(im).polygon([tuple(q) for q in ring * side], fill=255)
            acc ^= np.asarray(im) > 127
        _GLYPH_IM[key] = Image.fromarray((acc * 255).astype(np.uint8))
    return _GLYPH_IM[key]


# ---- the chart -------------------------------------------------------------------------------------------------
@dataclass
class Chart:
    size: int
    margin: int
    scale: float  # px per metre
    base: np.ndarray  # (s, s, 3) uint8
    ink: np.ndarray  # (s, s, 4) uint8
    revealed: np.ndarray  # (s, s, 4) uint8
    masks: dict = field(default_factory=dict)  # the checks' masks (uint8, canvas size)
    index: dict = field(default_factory=dict)
    land: np.ndarray | None = None  # bool canvas: province land


def compose_over(size: int, layers: list[tuple[np.ndarray, tuple[int, int, int], float]], band: int = 512,
                 under: np.ndarray | None = None) -> np.ndarray:
    """Masks (uint8, colour, opacity) stacked in order, "over", band by band: RGBA, or RGB over `under`."""
    ch = 3 if under is not None else 4
    out = np.empty((size, size, ch), dtype=np.uint8)
    for r0 in range(0, size, band):
        r1 = min(size, r0 + band)
        if under is not None:
            c = under[r0:r1].astype(np.float32) / 255
        else:
            c = np.zeros((r1 - r0, size, 3), np.float32)
            a = np.zeros((r1 - r0, size), np.float32)
        for m, col, op in layers:
            al = m[r0:r1].astype(np.float32) * (op / 255)
            colv = np.asarray(col, np.float32) / 255
            c = c * (1 - al[..., None]) + colv * al[..., None]
            if under is None:
                a = a * (1 - al) + al
        if under is not None:
            out[r0:r1] = to_u8(c)
        else:
            rgb = c / np.maximum(a[..., None], 1e-6)
            out[r0:r1, :, :3] = to_u8(rgb)
            out[r0:r1, :, 3] = to_u8(a)
    return out


class Renderer:
    def __init__(self, f: Features, size: int = MASTER, font: Path | None = None):
        self.f, self.size = f, size
        self.u = size / MASTER  # every master pixel dimension scales by u
        self.m = round(MARGIN * self.u)
        self.P = size - 2 * self.m
        self.scale = self.P / f.span_m
        self.font_file = str(font or font_path())
        self._fonts: dict[int, ImageFont.FreeTypeFont] = {}
        self.boxes: list[tuple[float, float, float, float]] = []  # placed labels and glyphs (canvas px)

    def font(self, px: float) -> ImageFont.FreeTypeFont:
        k = max(6, round(px * self.u * SS))
        if k not in self._fonts:
            self._fonts[k] = ImageFont.truetype(self.font_file, k)
        return self._fonts[k]

    def px(self, x_m, y_m) -> tuple[float, float]:
        return self.m + x_m * self.scale, self.m + y_m * self.scale

    def line_px(self, pts_m: np.ndarray) -> np.ndarray:
        return self.m + pts_m * self.scale

    # -- terrain on the canvas --
    def _sample(self, a: np.ndarray, dtype) -> np.ndarray:
        """A province array resampled (nearest) onto the province box, then edge-padded to the canvas."""
        n = self.f.n
        idx = np.clip(((np.arange(self.P) + 0.5) * n / self.P).astype(np.int64), 0, n)
        box_ = np.asarray(a[idx])[:, idx].astype(dtype)
        return np.pad(box_, self.m, mode="edge")

    def run(self) -> Chart:
        s, m = self.size, self.m
        cover = self._sample(self.f.cover, np.int16)
        land = ~np.isin(cover, SEA)
        inside = np.zeros((s, s), bool)
        inside[m:s - m, m:s - m] = True
        self.inside = inside
        marsh = np.isin(cover, MARSH)
        wood = np.zeros(cover.shape, np.float32)
        for k, v in CANOPY_OF.items():
            wood[cover == k] = v
        forest = wood
        del cover

        fields = self.shore(land, inside)
        base = self.paper(fields)
        ink_layers, masks = self.sketch(land, inside, fields)
        ground = self._sample(self.f.ground, np.float32)
        rev_layers = self.relief(ground, fields, forest)
        del ground
        rev_layers += self.woods(fields, forest, marsh)
        del forest, marsh
        rev_layers += self.minor_lines()
        place_layers, places = self.places()
        rev_layers += place_layers

        ink = compose_over(s, ink_layers)
        revealed = compose_over(s, rev_layers)
        chart = Chart(s, m, self.scale, base, ink, revealed, masks=masks, land=land & inside)
        chart.index = self.make_index(places)
        return chart

    # -- noise --
    def _grid(self, cells: int, name: str) -> np.ndarray:
        return seed(name).random((cells + 2, cells + 2)).astype(np.float32) * 2 - 1

    def noise(self, cells: int, name: str, r0: int, r1: int) -> np.ndarray:
        """Smooth value noise in [-1, 1] for canvas rows [r0, r1): a `cells`-across random grid, smoothstep-blended,
        so any band is the same as the whole."""
        s = self.size
        g = self._grid(cells, name)

        def axis(lo, hi):
            x = (np.arange(lo, hi, dtype=np.float32) + 0.5) / s * cells
            i = np.floor(x).astype(np.int64)
            t = x - i
            return i, (t * t * (3 - 2 * t)).astype(np.float32)

        ci, ct = axis(0, s)
        cols = g[:, ci] * (1 - ct) + g[:, ci + 1] * ct  # (cells + 2, s)
        ri, rt = axis(r0, r1)
        return cols[ri] * (1 - rt[:, None]) + cols[ri + 1] * rt[:, None]

    def noise_at(self, cells: int, name: str, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """The same noise as `noise`, at points (canvas px)."""
        g = self._grid(cells, name)
        fx, fy = (x + 0.5) / self.size * cells, (y + 0.5) / self.size * cells
        ix, iy = np.floor(fx).astype(np.int64), np.floor(fy).astype(np.int64)
        tx, ty = fx - ix, fy - iy
        tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        a = g[iy, ix] * (1 - tx) + g[iy, ix + 1] * tx
        b = g[iy + 1, ix] * (1 - tx) + g[iy + 1, ix + 1] * tx
        return a * (1 - ty) + b * ty

    def banded(self, pad: int, fn, names: tuple[str, ...], band: int = 512) -> dict:
        """fn(e0, e1) -> {name: float array for rows [e0, e1)} over bands padded by `pad` rows; uint8 results."""
        s = self.size
        out = {k: np.empty((s, s), np.uint8) for k in names}
        for r0 in range(0, s, band):
            r1 = min(s, r0 + band)
            e0, e1 = max(0, r0 - pad), min(s, r1 + pad)
            res = fn(e0, e1)
            for k in names:
                out[k][r0:r1] = to_u8(res[k][r0 - e0:r1 - e0])
        return out

    def soft(self, mask: np.ndarray, r: float, gain: float = 1.6) -> np.ndarray:
        """A glow: the mask blurred by r px and lifted (the old labels' paper text-shadow)."""
        k = max(1, round(r))
        return self.banded(2 * (k + 1) + 2, lambda e0, e1: {"m": np.clip(
            blur(mask[e0:e1].astype(np.float32) / 255, k, 1) * gain, 0, 1)}, ("m",))["m"]

    def at(self, a: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        s = self.size
        return a[np.clip(y.astype(np.int64), 0, s - 1), np.clip(x.astype(np.int64), 0, s - 1)]

    # -- the shore: one wobbled land field for the coast, the land tint and the sea's wash --
    def shore(self, land, inside) -> dict:
        s, u = self.size, self.u
        q = 4  # the sea-distance field, measured at a quarter resolution
        lq = land[::q, ::q].copy()
        dist = np.full(lq.shape, 255, np.uint8)
        dist[lq] = 0
        cur = lq
        for k in range(1, 40):
            cur = dilate(cur, diag=k % 2 == 0)
            dist[cur & (dist == 255)] = k
        dq_cols = lerp(dist.astype(np.float32) * (q / u), s, axis=1)  # master px from shore, (s / q, s)
        del dist, lq, cur
        rc, rd = max(1, int(3 * u)), max(1, int(2 * u))
        pad = 2 * (rc + 1) + rd + 4
        out = {k: np.empty((s, s), np.uint8) for k in ("coast", "landf", "wash", "ripple")}
        seeds = []  # hachure ticks: (x, y, nx, ny), the normal pointing inland
        step = max(2, round(8 * u))  # the old hachure's 4 css px
        for r0 in range(0, s, 512):
            r1 = min(s, r0 + 512)
            e0, e1 = max(0, r0 - pad), min(s, r1 + pad)
            f = blur(land[e0:e1].astype(np.float32), rc, 2) + 0.22 * self.noise(max(8, int(160 * u)), "coast.wobble", e0, e1)
            gy, gx = np.gradient(f)
            g = np.maximum(np.hypot(gx, gy), 1e-6)
            sd = (f - 0.5) / g  # signed px from the coast, + inland
            ins = inside[e0:e1]
            res = {"coast": np.clip(1.6 * u + 0.5 - np.abs(sd), 0, 1) * ins,
                   "landf": np.clip(sd / (1.5 * u) + 0.5, 0, 1)}
            dq = blur(lerp(dq_cols, s, axis=0, lo=e0, hi=e1), rd, 1) + 2.0 * self.noise(max(8, int(120 * u)), "waterlines.wobble", e0, e1)
            dq = np.maximum(dq, 0)
            res["wash"] = np.exp(-dq / (30 * u))
            # three ripples fading from the shore (the old chart's 2.4, 5 and 8 pack px), broken like a raster's
            rip = np.zeros(dq.shape, np.float32)
            for d0, peak in ((14, 0.42), (30, 0.26), (48, 0.14)):
                rip = np.maximum(rip, np.clip(peak - np.abs(dq - d0 * u) * peak / (3.2 * u), 0, None))
            rip *= np.clip(0.55 + 1.6 * self.noise(max(16, int(380 * u)), "waterlines.break", e0, e1), 0, 1)
            res["ripple"] = rip
            del dq
            core = slice(r0 - e0, r1 - e0)
            on = (res["coast"][core] > 0.7)
            yy, xx = np.nonzero(on)
            if len(yy):
                key = (yy + r0) // step * (s // step + 1) + xx // step
                _, first = np.unique(key, return_index=True)
                yy, xx = yy[first], xx[first]
                nx_, ny_ = gx[core][yy, xx] / g[core][yy, xx], gy[core][yy, xx] / g[core][yy, xx]
                seeds.append(np.stack([xx + 0.5, yy + r0 + 0.5, nx_, ny_], 1))
            for k in out:
                out[k][r0:r1] = to_u8(res[k][core])
            del f, gx, gy, g, sd, res, rip
        out["seeds"] = np.concatenate(seeds) if seeds else np.zeros((0, 4))
        return out

    # -- base --
    def paper(self, fields) -> np.ndarray:
        """Bone paper mottled toward its dark tone; the sea the lightest ground, washed and rippled near the shore."""
        s, u = self.size, self.u
        out = np.empty((s, s, 3), np.uint8)
        P, PD = np.asarray(PAPER, np.float32), np.asarray(PAPER_DARK, np.float32)
        WO, WW, WI = (np.asarray(c, np.float32) for c in (WATER_OPEN, WATER_WASH, WATER_INK))
        for r0 in range(0, s, 512):
            r1 = min(s, r0 + 512)
            fine = 0.5 + 0.5 * self.noise(max(16, int(512 * u)), "paper.fine", r0, r1)
            mid = 0.5 + 0.5 * self.noise(max(8, int(140 * u)), "paper.mid", r0, r1)
            v = fine * 0.6 + mid * 0.4
            coarse = 0.5 + 0.5 * self.noise(24, "paper.coarse", r0, r1)
            t = (smooth(0.25, 0.95, coarse) * 0.35 + v * 0.25)[..., None]
            rgb = P * (1 - t) + PD * t
            wash = (fields["wash"][r0:r1].astype(np.float32) / 255 * (0.75 + v * 0.25))[..., None]
            water = WO * (1 - wash) + WW * wash
            rip = (fields["ripple"][r0:r1].astype(np.float32) / 255)[..., None]
            water = water * (1 - rip) + WI * rip
            lf = (fields["landf"][r0:r1].astype(np.float32) / 255)[..., None]
            out[r0:r1] = np.clip(np.rint(rgb * lf + water * (1 - lf)), 0, 255).astype(np.uint8)
        return out

    # -- the sketch --
    def sketch(self, land, inside, fields):
        s, u = self.size, self.u
        layers, masks = [], {}

        # the coast's hachure: short ticks every 4 old px from the shore into the land
        pen = Pen(s)
        rng = seed("coast.hachure")
        sd = fields["seeds"]
        k = 0.55 + rng.random(len(sd)) * 0.45
        L = 8.8 * u * k
        w = max(1, round(1.6 * u * SS))
        for (x, y, nx, ny), ln in zip(sd, L):
            pen.d.line([(x * SS, y * SS), ((x + nx * ln) * SS, (y + ny * ln) * SS)], fill=255, width=w)
        layers.append((pen.done(), INK, 0.5))
        del pen

        # the major rivers: slate water ink, widening a little toward the mouth
        pen = Pen(s)
        for r in self.f.rivers:
            if r.major:
                p = wobble(self.line_px(r.pts), seed(r.id), 3 * u + 0.5, 1.6 * u, 70 * u)
                self.river(pen, p, min(9.0, 6.0 + 1.0 * (r.weight - 2)) * u)
        masks["rivers"] = pen.done()
        layers.append((masks["rivers"], WATER_INK, 0.9))

        # the major roads: red-brown lane ink over a paper casing
        casing, pen = Pen(s), Pen(s)
        for r in self.f.roads:
            if r.major:
                p = wobble(self.line_px(r.pts), seed(r.id), 3 * u + 0.5, 1.2 * u, 80 * u)
                main = (5.4 if r.cls == "trunk" else 4.6) * u
                line(casing, p, main + 4 * u)
                line(pen, p, main)
        layers.append((casing.done(), PAPER, 0.85))
        masks["roads"] = pen.done()
        layers.append((masks["roads"], LANE_INK, 0.9))
        del casing, pen

        masks["coast"] = fields["coast"]
        layers.append((masks["coast"], INK, 0.92))

        # the land border (a lane-ink dash along the province's edge where it meets land)
        pen = Pen(s)
        rng = seed("frame")
        m, P = self.m, self.P
        ins = 14 * u
        edges = (  # (start, end, the land test along it)
            ((m + ins, m + ins), (m + P - ins, m + ins), land[m + 1, m:m + P]),
            ((m + ins, m + ins), (m + ins, m + P - ins), land[m:m + P, m + 1]),
            ((m + P - ins, m + ins), (m + P - ins, m + P - ins), land[m:m + P, m + P - 2]),
            ((m + ins, m + P - ins), (m + P - ins, m + P - ins), land[m + P - 2, m:m + P]),
        )
        for k, (a, b, on) in enumerate(edges):
            p = wobble(np.array([a, b], float), seed(f"border.{k}"), 3 * u + 0.5, 0.8 * u, 160 * u, 1)
            t = np.clip(((np.arange(len(p)) / max(1, len(p) - 1)) * (len(on) - 1)).astype(int), 0, len(on) - 1)
            keep = on[t]
            for piece in dashes(p, (24 * u, 10 * u)):
                if keep[int(np.argmin(np.hypot(*(p - piece[0]).T)))]:
                    line(pen, piece, 3.2 * u)
        border = pen.done()
        rb = max(1, int(12 * u))
        band = self.banded(2 * (rb + 1) + 2, lambda e0, e1: {"b": np.clip(blur(
            border[e0:e1].astype(np.float32) / 255, rb, 2) * 4, 0, 1) * (land[e0:e1] & inside[e0:e1])}, ("b",))["b"]
        layers.append((band, LANE_INK, 0.14))
        layers.append((border, LANE_INK, 0.9))
        del pen, band

        # a small inked rose in a hairline ring on a paper disc, in an open-sea corner
        layers += self.compass(land)

        # the seven cities: the pin-city glyph on a paper glow, the name in spaced capitals-and-lower
        halo, glyph, text = Pen(s), Pen(s), Pen(s)
        cities = [p for p in self.f.places if p.city]
        self.city_px = {}
        R = 32 * u
        for c in cities:
            x, y = self.px(c.x_m, c.y_m)
            self.city_px[c.id] = (x, y)
            self.boxes.append((x - R, y - R, x + R, y + R))
            self.glyph(glyph, halo, "pin-city", x, y, 2 * R, 5 * u)
        self.label_ring = {}
        for c in cities:
            x, y = self.city_px[c.id]
            self.label_ring[c.id] = self.label(text, halo, c.name, x, y, 64, R + 6 * u, track=0.12, halo_w=6)
        masks["cities"] = glyph.done()
        layers.append((self.soft(halo.done(), 3 * u), PAPER, 0.8))
        layers.append((masks["cities"], INK, 1.0))
        layers.append((text.done(), INK, 1.0))
        return layers, masks

    def compass(self, land):
        s, u = self.size, self.u
        R = 64 * u
        m = self.m + 40 * u
        spots = [(s - m - R, m + R), (m + R, m + R), (s - m - R, s - m - R), (m + R, s - m - R)]
        cx, cy = spots[0]
        for x, y in spots:
            if not land[int(y - R):int(y + R), int(x - R):int(x + R)].any():
                cx, cy = x, y
                break
        disc, pen = Pen(s), Pen(s)
        X, Y = cx * SS, cy * SS
        r = R * SS
        disc.d.ellipse([X - r * 1.12, Y - r * 1.12, X + r * 1.12, Y + r * 1.12], fill=255)
        w = max(1, round(1.4 * u * SS))
        pen.d.ellipse([X - r, Y - r, X + r, Y + r], outline=255, width=w)
        for k in range(8):
            a = k * np.pi / 4 - np.pi / 2
            ln = r * (0.86 if k % 2 == 0 else 0.5)
            side = r * (0.13 if k % 2 == 0 else 0.09)
            tip = (X + ln * np.cos(a), Y + ln * np.sin(a))
            lft = (X + side * np.cos(a - np.pi / 2), Y + side * np.sin(a - np.pi / 2))
            rgt = (X + side * np.cos(a + np.pi / 2), Y + side * np.sin(a + np.pi / 2))
            pen.d.polygon([tip, lft, (X, Y)], fill=255)  # one half filled, one half outlined
            pen.d.line([tip, rgt, (X, Y)], fill=255, width=w)
        fnt = self.font(26)
        l, t, rr, b = fnt.getbbox("N")
        pen.d.text((X - (rr - l) / 2 - l, Y - r * 0.98 - (b - t) - t - 4 * u * SS), "N", font=fnt, fill=255)
        self.boxes.append((cx - R * 1.3, cy - R * 1.5, cx + R * 1.3, cy + R * 1.3))
        return [(disc.done(), PAPER, 0.85), (pen.done(), INK, 0.85)]

    def river(self, pen: Pen, p: np.ndarray, width: float) -> None:
        """Rivers run source to mouth: the line widens a little toward the mouth."""
        q = p * SS
        n = len(q)
        for i in range(0, n - 1, 5):
            c = q[i:i + 6]
            if len(c) < 2:
                break
            w = width * SS * (0.75 + 0.25 * i / max(1, n - 1))
            pen.d.line([tuple(map(float, x)) for x in c], fill=255, width=max(1, round(w)), joint="curve")

    def glyph(self, glyph: Pen, halo: Pen, name: str, x, y, side_px, halo_px) -> None:
        """An old-map place glyph centred on (x, y), side_px across, with a paper halo round its shape."""
        side = max(4, round(side_px * SS))
        im = glyph_image(name, side)
        ox, oy = round(x * SS - side / 2), round(y * SS - side / 2)
        glyph.im.paste(255, (ox, oy), im)
        k = max(3, round(halo_px * SS) | 1)
        big = Image.new("L", (side + 2 * k, side + 2 * k), 0)
        big.paste(im, (k, k))
        halo.im.paste(255, (ox - k, oy - k), big.filter(ImageFilter.MaxFilter(k)))

    def label(self, text: Pen, halo: Pen, name: str, x, y, size_px, gap, track=0.0, halo_w=4, required=True):
        """Place a label beside its point where it overlaps nothing placed; returns its box or None.
        `track` spaces the letters (em), as the old chart set its city names."""
        fnt = self.font(size_px)
        l, t, r, b = fnt.getbbox(name)
        sp = track * fnt.size
        adv = [fnt.getlength(ch) for ch in name]
        w, h = (r - l + sp * (len(name) - 1)) / SS, (b - t) / SS
        s, edge = self.size, self.m + 4 * self.u
        cands = [(x + gap, y - h / 2), (x - gap - w, y - h / 2), (x - w / 2, y - gap - h), (x - w / 2, y + gap),
                 (x + gap * 0.8, y - gap * 0.8 - h), (x - gap * 0.8 - w, y - gap * 0.8 - h),
                 (x + gap * 0.8, y + gap * 0.8), (x - gap * 0.8 - w, y + gap * 0.8)]
        pick = None
        for cx, cy in cands:
            bx = (cx, cy, cx + w, cy + h)
            if bx[0] < edge or bx[1] < edge or bx[2] > s - edge or bx[3] > s - edge:
                continue
            if any(bx[0] < o[2] and o[0] < bx[2] and bx[1] < o[3] and o[1] < bx[3] for o in self.boxes):
                continue
            pick = bx
            break
        if pick is None:
            if not required:
                return None
            pick = next(((cx, cy, cx + w, cy + h) for cx, cy in cands
                         if cx >= edge and cy >= edge and cx + w <= s - edge and cy + h <= s - edge),
                        (cands[0][0], cands[0][1], cands[0][0] + w, cands[0][1] + h))
        self.boxes.append(pick)
        ox, oy = pick[0] * SS - l, pick[1] * SS - t
        sw = max(1, round(halo_w * self.u * SS))
        if sp:
            cx = ox
            for ch, a in zip(name, adv):
                halo.d.text((cx, oy), ch, font=fnt, fill=255, stroke_width=sw, stroke_fill=255)
                text.d.text((cx, oy), ch, font=fnt, fill=255)
                cx += a + sp
        else:
            halo.d.text((ox, oy), name, font=fnt, fill=255, stroke_width=sw, stroke_fill=255)
            text.d.text((ox, oy), name, font=fnt, fill=255)
        return [round(v, 1) for v in pick]

    # -- the revealed layer --
    def relief(self, ground, fields, forest):
        """The explored land's warm tint and canopy tint, a north-west hillshade folded into the tint as the old
        chart did, and 50 m contours (every fourth bolder); banded, so the memory is a few bands, not the canvas."""
        u, s = self.u, self.size
        mpp = 1 / self.scale  # metres per canvas pixel
        sea = self.f.sea_level_m
        alt = np.radians(45)
        c = np.cos(alt) / np.sqrt(2)
        lx, ly, lz = -c, -c, np.sin(alt)  # towards the light: west (-x) and north (-y)
        q = 4
        self.canopy_q = blur(forest[::q, ::q], max(1, int(3 * u)), 2)
        cq_cols = lerp(self.canopy_q, s, axis=1)
        r1_, r5 = max(1, int(2 * u)), max(1, int(5 * u))

        def band(e0, e1):
            lf = fields["landf"][e0:e1].astype(np.float32) / 255 * self.inside[e0:e1]
            g = ground[e0:e1]
            h = blur(g, r1_, 1)
            gy, gx = np.gradient(h, mpp)
            del h
            shade = (-gx * lx - gy * ly + lz) / np.sqrt(gx * gx + gy * gy + 1)
            del gx, gy
            d = shade - lz
            res = {"tint": lf, "canopy": smooth(0.1, 0.9, lerp(cq_cols, s, axis=0, lo=e0, hi=e1)) * lf,
                   "dark": np.tanh(np.clip(-d, 0, None) * 6.0) * lf,
                   "light": np.tanh(np.clip(d, 0, None) * 5.0) * lf}
            del d, shade
            hs = blur(g, r5, 2)
            k50 = np.rint(hs / 50)
            cl = iso_line(hs, k50 * 50, 0.6 * u) * ((hs > sea + 1) & (lf > 0.5))
            res["contour"] = cl * np.where(np.abs(k50) % 4 == 0, 1.0, 0.56)
            return res

        got = self.banded(2 * (r5 + 1) + 4, band, ("tint", "canopy", "dark", "light", "contour"))
        return [(got["tint"], LAND, 0.72), (got["canopy"], CANOPY, 0.45), (got["light"], WATER_OPEN, 0.06),
                (got["dark"], SHADOW, 0.2), (got["contour"], INK, 0.5)]

    def woods(self, fields, forest, marsh):
        """The old chart's tree cover (clumped two-lobed crowns on a stem, a dot stipple thinning into the
        clearings) and its brushed marsh tufts (a base stroke and three blades)."""
        s, u = self.size, self.u
        lf = fields["landf"]
        layers = []
        rng = seed("woods")
        sp = 24 * u
        n = int(s / sp) + 1
        gy, gx = np.mgrid[0:n, 0:n].astype(np.float64)
        x = (gx + rng.random(gx.shape)) * sp
        y = (gy + rng.random(gy.shape)) * sp
        x, y = x.ravel(), y.ravel()
        ok = (x < s - 1) & (y < s - 1)
        x, y = x[ok], y[ok]
        cq = self.canopy_q
        c = cq[np.clip((y / 4).astype(int), 0, cq.shape[0] - 1), np.clip((x / 4).astype(int), 0, cq.shape[1] - 1)]
        on = (self.at(lf, x, y) > 200) & self.at(self.inside, x, y) & (c >= 0.08)
        x, y, c = x[on], y[on], c[on]
        clump = (0.5 + 0.5 * self.noise_at(max(4, int(s / (96 * u))), "woods.clump", x, y)) * 0.65 + \
                (0.5 + 0.5 * self.noise_at(max(4, int(s / (30 * u))), "woods.clump2", x, y)) * 0.35
        roll = rng.random(len(x))
        crown = (c > 0.25) & (roll < smooth(0.3, 0.55, clump + (c - 0.5) * 0.6))
        dot = ~crown & (roll < smooth(0.08, 0.6, c) * 0.85)
        pen, dots = Pen(s), Pen(s)
        w = max(1, round(1.8 * u * SS))
        for X, Y, cc in zip(x[crown] * SS, y[crown] * SS, c[crown]):
            r = 7.0 * u * SS * (0.7 + cc * 0.6)
            pen.d.arc([X - r * 1.05, Y - r * 1.15, X + r * 0.15, Y + r * 0.05], 171, 315, fill=255, width=w)
            pen.d.arc([X - r * 0.15, Y - r * 1.15, X + r * 1.05, Y + r * 0.05], 225, 369, fill=255, width=w)
            pen.d.line([(X, Y - r * 0.2), (X, Y + r * 0.7)], fill=255, width=w)
        for X, Y, cc in zip(x[dot] * SS, y[dot] * SS, c[dot]):
            d = (1.1 + 0.9 * cc) * u * SS / 2
            dots.d.rectangle([X - d, Y - d, X + d, Y + d], fill=255)
        layers += [(dots.done(), INK, 0.45), (pen.done(), INK, 0.66)]
        del pen, dots

        rng = seed("marsh.tufts")
        sp = 42 * u
        n = int(s / sp) + 1
        gy, gx = np.mgrid[0:n, 0:n].astype(np.float64)
        x = ((gx + rng.random(gx.shape)) * sp).ravel()
        y = ((gy + rng.random(gy.shape)) * sp).ravel()
        lean = (rng.random(x.shape) - 0.5) * 0.3
        ok = (x < s - 1) & (y < s - 1)
        x, y, lean = x[ok], y[ok], lean[ok]
        on = self.at(marsh, x, y) & (self.at(lf, x, y) > 200) & self.at(self.inside, x, y)
        pen = Pen(s)
        S = 14 * u * SS
        w = max(1, round(1.8 * u * SS))
        for X, Y, j in zip(x[on] * SS, y[on] * SS, lean[on]):
            pen.d.line([(X - S * 0.55, Y), (X + S * 0.55, Y)], fill=255, width=w)
            pen.d.line([(X, Y), (X + j * S, Y - S * 0.75)], fill=255, width=w)
            pen.d.line([(X - S * 0.3, Y), (X - S * 0.45, Y - S * 0.5)], fill=255, width=w)
            pen.d.line([(X + S * 0.3, Y), (X + S * 0.45, Y - S * 0.5)], fill=255, width=w)
        layers.append((pen.done(), INK, 0.7))
        return layers

    def minor_lines(self):
        """Minor rivers in water ink; tracks dashed, footpaths dotted, boardwalks and causeways a hairline crossed
        by rungs, all in the one lane ink (old draw.ts CHART_ROADS)."""
        s, u = self.size, self.u
        layers = []
        pen = Pen(s)
        for r in self.f.rivers:
            if not r.major:
                p = wobble(self.line_px(r.pts), seed(r.id), 3 * u + 0.5, 1.0 * u, 80 * u)
                self.river(pen, p, 3.4 * u)
        layers.append((pen.done(), WATER_INK, 0.9))
        pen = Pen(s)
        for r in self.f.roads:
            if r.major:
                continue
            p = wobble(self.line_px(r.pts), seed(r.id), 1.5 * u + 0.25, 1.2 * u, 90 * u, smooth=9)
            if r.cls in ("boardwalk", "causeway"):
                line(pen, p, 1.3 * u)
                for d in dashes(p, (2 * u, 5 * u)):
                    line(pen, d, 5.5 * u)
            elif r.cls == "footpath":
                for d in dashes(p, (3 * u, 6 * u)):
                    line(pen, d, 1.8 * u)
            else:
                for d in dashes(p, (10 * u, 6 * u)):
                    line(pen, d, 2.2 * u)
        layers.append((pen.done(), LANE_INK, 0.9))
        return layers

    def places(self):
        s, u = self.size, self.u
        halo, glyph, text = Pen(s), Pen(s), Pen(s)
        out = {}
        others = sorted((p for p in self.f.places if not p.city), key=lambda p: (-p.magnitude, p.kind, p.id))
        for p in others:
            x, y = self.px(p.x_m, p.y_m)
            r = (12 + 1.5 * p.magnitude) * u
            self.glyph(glyph, halo, PIN.get(p.kind, "pin-landmark"), x, y, 2 * r, 3 * u)
            self.boxes.append((x - r, y - r, x + r, y + r))
        for p in others:
            x, y = self.px(p.x_m, p.y_m)
            r = (12 + 1.5 * p.magnitude) * u
            # names for the places of magnitude 2 and up, where there is room (the rest carry the glyph; the view
            # names them on demand from index.places)
            lab = None if p.magnitude < 2 else self.label(text, halo, p.name, x, y, 22 + 3 * p.magnitude, r + 4 * u,
                                                          halo_w=4, required=False)
            out[p.id] = (p, x, y, lab)
        for p in self.f.places:
            if p.city:
                x, y = self.city_px[p.id]
                out[p.id] = (p, x, y, self.label_ring[p.id])
        layers = [(self.soft(halo.done(), 2 * u), PAPER, 0.75), (glyph.done(), INK, 0.95), (text.done(), INK, 0.95)]
        return layers, out

    # -- the index --
    def make_index(self, places: dict) -> dict:
        f, m = self.f, self.m
        q = f.cell_samples
        cell_px = q * self.scale * f.sample_m
        span = f.n // q
        x0, y0 = f.cell_sw
        cells = {}
        tile = round(256 * self.u)
        for j in range(span):
            for i in range(span):
                cx, cy = x0 + i, y0 + j
                px0 = m + i * cell_px
                py0 = m + (span - 1 - j) * cell_px  # cell y runs north: its north row from the top
                cells[f"{cx},{cy}"] = [int(px0 // tile), int(py0 // tile), round(px0, 2), round(py0, 2),
                                       round(cell_px, 2), round(cell_px, 2)]
        pl = {}
        for pid, (p, x, y, lab) in sorted(places.items()):
            i = int((p.x_m / f.sample_m) // q)
            jn = int((p.y_m / f.sample_m) // q)
            pl[pid] = {"name": p.name, "px": [round(x, 2), round(y, 2)], "cell": [x0 + i, y0 + span - 1 - jn],
                       "kind": p.kind, "city": p.city, "label": lab}
        return {"size": self.size, "margin": m, "px_per_m": self.scale, "tile": tile,
                "origin": "pixel = margin + metres * px_per_m; x east, y south of the province's NW corner",
                "layers": ["base", "revealed", "ink"], "cells": cells, "places": pl}
