"""The parchment chart (2.W4 §c, 1.2 §e): a deterministic renderer from our own data, no game asset (0003, 0006 §UI).

Three layers on one canvas (the master is MASTER^2 px, 2^12; the province fills [M, size - M) at one pixel per terrain sample):
- base      opaque: the paper, the sea's wash;
- ink       RGBA: the sketch, always shown: the coast with its water lines, the marsh hatching, the major rivers
            and roads, the province's land border, the frame, the seven cities drawn and labelled;
- revealed  RGBA: what exploring fills in, masked per cell by the view: the relief (hillshade and contours), the
            land cover's wash, the minor rivers and tracks, every other place drawn and labelled.
The view stacks base, revealed (masked), ink. There is no player-position marker (C9).

Every stroke is drawn at twice the size into 8-bit masks and box-reduced (antialiasing); every random choice comes
from a generator seeded by a fixed string, so two runs give the same pixels.

    render(features, size) -> Chart      the layers as uint8 arrays, the masks the checks read, the index
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from tools.chart.data import FOREST, MARSH, ROCK, SEA, Features

MASTER = 1 << 12  # the master chart, pixels a side (a pixel count, not a Skyrim unit)
MARGIN = 32  # master pixels round the province: one cell
SS = 2  # supersampling of the stroke masks

# Colours (sRGB). The ink is sepia and the water ink a grey-green, never the Nordic grey-blue of the vanilla map.
PAPER = (232, 216, 178)
PAPER_EDGE = (168, 128, 78)
INK = (52, 36, 22)
WATER_INK = (22, 78, 84)
BORDER_INK = (128, 62, 30)
MARSH_INK = (84, 86, 44)
SEA_WASH = (150, 168, 146)
SHADE = (92, 64, 38)
LIGHT = (246, 236, 208)
FOREST_WASH = (88, 104, 52)
MARSH_WASH = (124, 128, 66)
ROCK_WASH = (120, 104, 86)

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


def stroke(pen: Pen, p: np.ndarray, width: float, rng: np.random.Generator, vary: float = 0.25,
           fill: int = 255, chunk: int = 7) -> None:
    """A pen stroke along p (canvas px) whose width swells and thins along its length."""
    q = p * SS
    for i in range(0, len(q) - 1, chunk - 1):
        c = q[i:i + chunk]
        if len(c) < 2:
            break
        w = max(1, round(width * SS * (1 + vary * rng.uniform(-1, 1))))
        pen.d.line([tuple(map(float, x)) for x in c], fill=fill, width=w, joint="curve")


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
            sel = (s >= pos) & (s <= pos + ln)
            if sel.sum() >= 2:
                out.append(p[sel])
        pos += ln
        k += 1
        if period <= 0:
            break
    return out


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
        forest = np.isin(cover, FOREST)
        rock = np.isin(cover, ROCK)
        del cover

        base = self.paper(land, inside)
        ink_layers, masks = self.sketch(land, inside, marsh)
        ground = self._sample(self.f.ground, np.float32)
        rev_layers = self.relief(ground, land, inside, forest, marsh, rock)
        del ground, forest, rock, marsh
        rev_layers += self.minor_lines()
        place_layers, places = self.places()
        rev_layers += place_layers

        ink = compose_over(s, ink_layers)
        revealed = compose_over(s, rev_layers)
        chart = Chart(s, m, self.scale, base, ink, revealed, masks=masks, land=land & inside)
        chart.index = self.make_index(places)
        return chart

    # -- base --
    def noise(self, cells: int, name: str, r0: int, r1: int) -> np.ndarray:
        """Smooth value noise in [-1, 1] for canvas rows [r0, r1): a `cells`-across random grid, smoothstep-blended,
        so any band is the same as the whole."""
        s = self.size
        g = seed(name).random((cells + 2, cells + 2)).astype(np.float32) * 2 - 1

        def axis(lo, hi):
            x = (np.arange(lo, hi, dtype=np.float32) + 0.5) / s * cells
            i = np.floor(x).astype(np.int64)
            t = x - i
            return i, (t * t * (3 - 2 * t)).astype(np.float32)

        ci, ct = axis(0, s)
        cols = g[:, ci] * (1 - ct) + g[:, ci + 1] * ct  # (cells + 2, s)
        ri, rt = axis(r0, r1)
        return cols[ri] * (1 - rt[:, None]) + cols[ri + 1] * rt[:, None]

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

    # -- base --
    def paper(self, land: np.ndarray, inside: np.ndarray) -> np.ndarray:
        s, u = self.size, self.u
        rw = max(1, int(3 * u))
        rng = seed("paper.stains")
        stains = [(rng.uniform(0.1, 0.9) * s, rng.uniform(0.1, 0.9) * s, rng.uniform(0.04, 0.12) * s)
                  for _ in range(5)]
        sea = ((~land) & inside)
        x = np.arange(s, dtype=np.float32) / (s - 1) * 2 - 1
        out = np.empty((s, s, 3), np.uint8)
        pad, band = 2 * (rw + 1) + 2, 512
        for r0 in range(0, s, band):
            r1 = min(s, r0 + band)
            tone = 1 + 0.035 * self.noise(12, "paper.coarse", r0, r1) + 0.02 * self.noise(96, "paper.mid", r0, r1)
            tone += 0.012 * self.noise(max(16, int(700 * u)), "paper.fine", r0, r1)
            y = (np.arange(r0, r1, dtype=np.float32) / (s - 1) * 2 - 1)[:, None]
            edge = np.maximum(np.abs(x)[None, :], np.abs(y)) + 0.02 * self.noise(40, "paper.edge", r0, r1)
            burn = (np.clip((edge - 0.86) / 0.14, 0, 1) ** 2.2)[..., None]
            rgb = np.asarray(PAPER, np.float32) * tone[..., None]
            rgb = rgb * (1 - 0.55 * burn) + np.asarray(PAPER_EDGE, np.float32) * 0.55 * burn
            del tone, edge, burn
            yy = np.arange(r0, r1, dtype=np.float32)[:, None]
            for k, (cx, cy, r) in enumerate(stains):  # a few faint tea-dark blots
                if cy + r * 1.2 < r0 or cy - r * 1.2 > r1:
                    continue
                d = np.hypot(yy - cy, np.arange(s, dtype=np.float32)[None, :] - cx) / r
                d = d + 0.35 * self.noise(max(6, int(s / r * 3)), f"paper.stain.{k}", r0, r1)
                rgb *= 1 - (np.clip(1 - d, 0, 1) ** 0.7 * 0.03)[..., None]
            e0, e1 = max(0, r0 - pad), min(s, r1 + pad)  # the sea's wash, on the paper under the ink
            wash = (blur(sea[e0:e1].astype(np.float32), rw, 2) * 0.28)[r0 - e0:r1 - e0, :, None]
            rgb = rgb * (1 - wash) + np.asarray(SEA_WASH, np.float32) * wash
            out[r0:r1] = np.clip(np.rint(rgb), 0, 255).astype(np.uint8)
        return out

    # -- the sketch --
    def sketch(self, land, inside, marsh):
        s, u = self.size, self.u
        layers, masks = [], {}

        # the water lines' field: distance from the shore out to sea, measured at a quarter resolution
        q = 4
        lq = land[::q, ::q].copy()
        dist = np.full(lq.shape, 255, np.uint8)
        dist[lq] = 0
        cur = lq
        for k in range(1, 40):
            cur = dilate(cur, diag=k % 2 == 0)
            dist[cur & (dist == 255)] = k
        dist = dist.astype(np.float32) * (q / u)  # master pixels from shore
        dq_cols = lerp(dist, s, axis=1)  # (s / q, s)
        del dist, lq, cur
        rc, rd = max(1, int(3 * u)), max(1, int(2 * u))
        sea_in = (~land) & inside

        def coast_band(e0, e1):
            # the coast: the blurred land's half level, nudged by slow noise, drawn twice like a sketching hand
            f = blur(land[e0:e1].astype(np.float32), rc, 2) + 0.22 * self.noise(max(8, int(160 * u)), "coast.wobble", e0, e1)
            ins = inside[e0:e1]
            coast = iso_line(f, 0.5, 1.1 * u) * ins
            f += 0.18 * self.noise(max(8, int(300 * u)), "coast.second", e0, e1)
            coast = np.maximum(coast, iso_line(f, 0.5, 0.55 * u) * ins * 0.7)
            del f
            dq = lerp(dq_cols, s, axis=0, lo=e0, hi=e1)
            dq = blur(dq, rd, 1) + 3.0 * self.noise(max(8, int(120 * u)), "waterlines.wobble", e0, e1)
            water = np.zeros(dq.shape, np.float32)
            for t, a in ((11, 0.8), (24, 0.6), (40, 0.42), (62, 0.26)):
                water = np.maximum(water, iso_line(dq, t, 0.6 * u) * a)
            return {"coast": coast, "water": water * sea_in[e0:e1]}

        got = self.banded(2 * (rc + 1) + rd + 4, coast_band, ("coast", "water"))
        masks["coast"] = got["coast"]
        layers.append((got["water"], WATER_INK, 0.85))
        del got

        # the marsh: the cartographer's tufts on short level strokes, where the marsh is dense
        pen = Pen(s)
        rng = seed("marsh.hatch")
        dens = blur(marsh[::8, ::8].astype(np.float32), 2, 2)
        sp = 34 * u
        nx = int(s / sp)
        for j in range(nx):
            for i in range(nx):
                x = (i + 0.5) * sp + rng.uniform(-0.3, 0.3) * sp
                y = (j + 0.5) * sp + rng.uniform(-0.3, 0.3) * sp
                ix, iy = int(x), int(y)
                r = rng.random()
                if not (0 <= ix < s and 0 <= iy < s) or not inside[iy, ix] or not land[iy, ix]:
                    continue
                d = dens[min(iy // 8, dens.shape[0] - 1), min(ix // 8, dens.shape[1] - 1)]
                if d < 0.3 or r > d * 1.25:
                    continue
                self.tuft(pen, x, y, rng)
        hatch = pen.done()
        layers.append((hatch, MARSH_INK, 0.8))
        del pen, dens

        # the major rivers: tapering from source to mouth
        pen = Pen(s)
        for r in self.f.rivers:
            if r.major:
                p = wobble(self.line_px(r.pts), seed(r.id), 3 * u + 0.5, 2.6 * u, 70 * u)
                self.river(pen, p, (3.0 + 1.6 * (r.weight - 1)) * u, seed(r.id + ".w"))
        masks["rivers"] = pen.done()
        layers.append((masks["rivers"], WATER_INK, 0.95))

        # the major roads: long dashes of sepia, a second faint hand beside
        pen = Pen(s)
        for r in self.f.roads:
            if r.major:
                p = wobble(self.line_px(r.pts), seed(r.id), 3 * u + 0.5, 2.4 * u, 80 * u)
                rng = seed(r.id + ".w")
                off = (3.2 + 0.8 * r.weight) * u
                tx, ty = np.gradient(p[:, 0]), np.gradient(p[:, 1])
                nn = np.stack([-ty, tx], 1) / (np.hypot(tx, ty)[:, None] + 1e-9)
                for side in (-1, 1):
                    stroke(pen, p + side * off * nn, 2.1 * u, rng, 0.35)
        masks["roads"] = pen.done()
        layers.append((masks["roads"], INK, 1.0))

        layers.append((masks["coast"], INK, 0.95))

        # the frame and the land border (dash-dot along the province's edge where it meets land)
        pen = Pen(s)
        rng = seed("frame")
        for inset, w in ((12, 2.2), (20, 1.0)):
            a, b = inset * u, s - inset * u
            for p in ([(a, a), (b, a)], [(b, a), (b, b)], [(b, b), (a, b)], [(a, b), (a, a)]):
                stroke(pen, wobble(np.array(p), rng, 6 * u + 1, 0.6 * u, 200 * u, 1), w * u, rng, 0.15)
        frame = pen.done()
        pen = Pen(s)
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
            for piece in dashes(p, (30 * u, 12 * u)):
                idx = [int(np.argmin(np.hypot(*(p - piece[0]).T)))]
                if keep[idx[0]]:
                    stroke(pen, piece, 4.4 * u, rng, 0.15)
        border = pen.done()
        rb = max(1, int(14 * u))
        band = self.banded(2 * (rb + 1) + 2, lambda e0, e1: {"b": np.clip(blur(
            border[e0:e1].astype(np.float32) / 255, rb, 2) * 4, 0, 1) * (land[e0:e1] & inside[e0:e1])}, ("b",))["b"]
        layers.append((band, BORDER_INK, 0.3))
        layers.append((frame, INK, 0.85))
        layers.append((border, BORDER_INK, 1.0))

        # the seven cities
        halo, glyph, text = Pen(s), Pen(s), Pen(s)
        cities = [p for p in self.f.places if p.city]
        self.city_px = {}
        for c in cities:
            x, y = self.px(c.x_m, c.y_m)
            self.city_px[c.id] = (x, y)
            R = 42 * u
            self.boxes.append((x - R, y - R, x + R, y + R))
            self.city_glyph(glyph, halo, x, y, R, seed(c.id))
        self.label_ring = {}
        for c in cities:
            x, y = self.city_px[c.id]
            self.label_ring[c.id] = self.label(text, halo, c.name, x, y, 92, 50 * u, seed(c.id + ".label"),
                                               halo_w=7)
        masks["cities"] = glyph.done()
        layers.append((halo.done(), PAPER, 0.72))
        layers.append((masks["cities"], INK, 1.0))
        layers.append((text.done(), INK, 1.0))
        return layers, masks

    def tuft(self, pen: Pen, x: float, y: float, rng: np.random.Generator) -> None:
        u = self.u * SS
        L = rng.uniform(11, 16) * u
        tilt = rng.uniform(-0.06, 0.06)
        X, Y = x * SS, y * SS
        w = max(1, round(1.9 * u))
        pen.d.line([(X - L, Y - tilt * L), (X + L, Y + tilt * L)], fill=255, width=w)
        for dx, lean in ((-0.5, -0.35), (0.0, 0.0), (0.5, 0.35)):
            h = rng.uniform(7, 12) * u
            bx = X + dx * L * 0.9
            pen.d.line([(bx, Y - 1 * u), (bx + lean * h + rng.uniform(-1, 1) * u, Y - h)], fill=255, width=w)
        if rng.random() < 0.45:
            l2 = L * rng.uniform(0.35, 0.6)
            ox = rng.uniform(-0.4, 0.4) * L
            pen.d.line([(X + ox - l2, Y + 5 * u), (X + ox + l2, Y + 5 * u)], fill=255, width=w)

    def river(self, pen: Pen, p: np.ndarray, width: float, rng) -> None:
        """Rivers run source to mouth: the line thickens toward the mouth."""
        q = p * SS
        n = len(q)
        for i in range(0, n - 1, 5):
            c = q[i:i + 6]
            if len(c) < 2:
                break
            t = i / max(1, n - 1)
            w = width * SS * (0.55 + 0.75 * t) * (1 + 0.15 * rng.uniform(-1, 1))
            pen.d.line([tuple(map(float, x)) for x in c], fill=255, width=max(1, round(w)), joint="curve")

    def city_glyph(self, glyph: Pen, halo: Pen, x, y, R, rng) -> None:
        """A rough ring round three domed stilt-houses: drawn, not stamped."""
        X, Y, r = x * SS, y * SS, R * SS
        halo.d.ellipse([X - r * 1.15, Y - r * 1.15, X + r * 1.15, Y + r * 1.15], fill=255)
        a0 = rng.uniform(0, 2 * np.pi)
        a = np.linspace(a0, a0 + 2 * np.pi + 0.35, 90)
        rad = r * (1 + 0.05 * np.sin(3 * a + rng.uniform(0, 6)) + 0.02 * rng.normal(size=a.size).cumsum() / 9)
        pts = np.stack([X + rad * np.cos(a), Y + rad * np.sin(a)], 1)
        w = max(1, round(2.8 * self.u * SS))
        glyph.d.line([tuple(map(float, q)) for q in pts], fill=255, width=w, joint="curve")
        a = np.linspace(a0 + 1.0, a0 + 2.6, 30)
        pts = np.stack([X + r * 0.82 * np.cos(a), Y + r * 0.82 * np.sin(a)], 1)
        glyph.d.line([tuple(map(float, q)) for q in pts], fill=255, width=max(1, w // 2), joint="curve")
        k = self.u * SS
        wh = max(1, round(1.8 * self.u * SS))
        for hx, hy, sc in ((-11, 4, 1.0), (11, 5, 0.9), (0, -9, 1.15)):
            cx, cy, h = X + hx * k + rng.uniform(-1, 1) * k, Y + hy * k, 8 * k * sc
            glyph.d.arc([cx - h, cy - h, cx + h, cy + h * 0.6], 180, 360, fill=255, width=wh)
            glyph.d.line([(cx - h * 1.15, cy - h * 0.2), (cx + h * 1.15, cy - h * 0.2)], fill=255, width=wh)
            for lx in (-0.7, 0.7):
                glyph.d.line([(cx + lx * h, cy - h * 0.2), (cx + lx * h, cy + h * 0.6)], fill=255, width=wh)

    def label(self, text: Pen, halo: Pen, name: str, x, y, size_px, gap, rng, halo_w=5, required=True):
        """Place a label beside its point where it overlaps nothing placed; returns its box or None."""
        fnt = self.font(size_px)
        l, t, r, b = fnt.getbbox(name)
        w, h = (r - l) / SS, (b - t) / SS
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
        halo.d.text((ox, oy), name, font=fnt, fill=255, stroke_width=sw, stroke_fill=255)
        text.d.text((ox, oy), name, font=fnt, fill=255)
        return [round(v, 1) for v in pick]

    # -- the revealed layer --
    def relief(self, ground, land, inside, forest, marsh, rock):
        """Hillshade lit from the north-west (up-left), the land cover's washes and 20 m contours (every fifth
        bolder), on land only; banded, so the memory is a few bands, not the canvas."""
        u = self.u
        mpp = 1 / self.scale  # metres per canvas pixel
        sea = self.f.sea_level_m
        alt = np.radians(45)
        c = np.cos(alt) / np.sqrt(2)
        lx, ly, lz = -c, -c, np.sin(alt)  # towards the light: west (-x) and north (-y)
        r1_, r4, r5 = max(1, int(2 * u)), max(1, int(4 * u)), max(1, int(5 * u))

        def band(e0, e1):
            lnd = land[e0:e1] & inside[e0:e1]
            on = blur(lnd.astype(np.float32), r1_, 1)
            g = ground[e0:e1]
            h = blur(g, r1_, 1)
            gy, gx = np.gradient(h, mpp)
            del h
            shade = (-gx * lx - gy * ly + lz) / np.sqrt(gx * gx + gy * gy + 1)
            del gx, gy
            d = shade - lz
            res = {"dark": np.tanh(np.clip(-d, 0, None) * 2.0) * 0.55 * on,
                   "light": np.tanh(np.clip(d, 0, None) * 1.6) * 0.4 * on}
            del d, shade
            for k, m_ in (("forest", forest), ("marsh", marsh), ("rock", rock)):
                res[k] = blur(m_[e0:e1].astype(np.float32), r4, 2) * on
            hs = blur(g, r5, 2)
            k20 = np.rint(hs / 20)
            cl = iso_line(hs, k20 * 20, 0.45 * u) * ((hs > sea + 1) & lnd)
            res["contour"] = cl * np.where(np.abs(k20) % 5 == 0, 1.0, 0.55)
            return res

        got = self.banded(2 * (r5 + 1) + 4, band, ("dark", "light", "forest", "marsh", "rock", "contour"))
        return [(got["forest"], FOREST_WASH, 0.20), (got["marsh"], MARSH_WASH, 0.16), (got["rock"], ROCK_WASH, 0.22),
                (got["light"], LIGHT, 0.8), (got["dark"], SHADE, 0.8), (got["contour"], SHADE, 0.6)]

    def minor_lines(self):
        s, u = self.size, self.u
        layers = []
        pen = Pen(s)
        for r in self.f.rivers:
            if not r.major:
                p = wobble(self.line_px(r.pts), seed(r.id), 3 * u + 0.5, 1.0 * u, 80 * u)
                self.river(pen, p, 0.9 * u, seed(r.id + ".w"))
        layers.append((pen.done(), WATER_INK, 0.85))
        pen = Pen(s)
        for r in self.f.roads:
            if not r.major:
                p = wobble(self.line_px(r.pts), seed(r.id), 3 * u + 0.5, 1.2 * u, 90 * u)
                rng = seed(r.id + ".w")
                for d in dashes(p, (5 * u, 6 * u)):
                    stroke(pen, d, 1.6 * u * r.weight, rng, 0.15)
        layers.append((pen.done(), INK, 0.75))
        return layers

    def places(self):
        s, u = self.size, self.u
        halo, glyph, text = Pen(s), Pen(s), Pen(s)
        out = {}
        others = sorted((p for p in self.f.places if not p.city), key=lambda p: (-p.magnitude, p.kind, p.id))
        for p in others:
            x, y = self.px(p.x_m, p.y_m)
            r = (5 + 1.2 * p.magnitude) * u
            self.place_glyph(glyph, halo, p.kind, x, y, r, seed(p.id))
            self.boxes.append((x - r, y - r, x + r, y + r))
        for p in others:
            x, y = self.px(p.x_m, p.y_m)
            r = (5 + 1.2 * p.magnitude) * u
            lab = self.label(text, halo, p.name, x, y, 22 + 3 * p.magnitude, r + 5 * u, seed(p.id + ".label"),
                             halo_w=4, required=False)
            out[p.id] = (p, x, y, lab)
        for p in self.f.places:
            if p.city:
                x, y = self.city_px[p.id]
                out[p.id] = (p, x, y, self.label_ring[p.id])
        layers = [(halo.done(), PAPER, 0.6), (glyph.done(), INK, 0.95), (text.done(), INK, 0.95)]
        return layers, out

    def place_glyph(self, glyph: Pen, halo: Pen, kind: str, x, y, r, rng) -> None:
        X, Y, R = x * SS, y * SS, r * SS
        w = max(1, round(1.6 * self.u * SS))
        halo.d.ellipse([X - R * 1.4, Y - R * 1.4, X + R * 1.4, Y + R * 1.4], fill=255)
        j = lambda: rng.uniform(-0.12, 0.12) * R
        if kind == "settlement" or kind == "civic":
            glyph.d.ellipse([X - R + j(), Y - R + j(), X + R + j(), Y + R + j()], outline=255, width=w)
            glyph.d.ellipse([X - R * 0.3, Y - R * 0.3, X + R * 0.3, Y + R * 0.3], fill=255)
        elif kind == "ruin":
            glyph.d.line([(X - R, Y + R * 0.7), (X - R * 0.2 + j(), Y - R)], fill=255, width=w)
            glyph.d.line([(X - R * 0.2, Y - R), (X + R * 0.4 + j(), Y - R * 0.2)], fill=255, width=w)
            glyph.d.line([(X - R, Y + R * 0.7), (X + R, Y + R * 0.7 + j())], fill=255, width=w)
        elif kind == "camp":
            glyph.d.line([(X - R, Y + R * 0.7), (X + j(), Y - R), (X + R, Y + R * 0.7)], fill=255, width=w,
                         joint="curve")
        elif kind == "lair":
            glyph.d.line([(X - R * 0.8, Y - R * 0.8), (X + R * 0.8 + j(), Y + R * 0.8)], fill=255, width=w)
            glyph.d.line([(X + R * 0.8, Y - R * 0.8), (X - R * 0.8 + j(), Y + R * 0.8)], fill=255, width=w)
        elif kind == "martial":
            glyph.d.rectangle([X - R * 0.8 + j(), Y - R * 0.8, X + R * 0.8, Y + R * 0.8 + j()], outline=255, width=w)
        else:
            glyph.d.ellipse([X - R * 0.45, Y - R * 0.45, X + R * 0.45, Y + R * 0.45], fill=255)

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
