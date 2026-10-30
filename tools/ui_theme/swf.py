"""The SWF reader and writer the theme tools need (SWF 10 file format spec), pure Python on Linux (0014 §7).

Only what the font library and the retheme use: the tag stream (read, replace, write back byte-identical where
untouched), the DefineFont3 glyph table (encode from outlines, decode for the stills and tests), and the
DefineBitsLossless2 bitmaps Dear Diary's *_BG.swf frames are drawn from (decode to RGBA, encode back).
"""
from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass, field

import numpy as np

DEFINE_BITS_LOSSLESS2 = 36
DEFINE_FONT3 = 75
DEFINE_FONT_NAME = 88
EXPORT_ASSETS = 56
IMPORT_ASSETS2 = 71
SET_BACKGROUND = 9
SHOW_FRAME = 1
END = 0
FONT_EM = 1024 * 20  # DefineFont3 glyphs are drawn on a 1024 em at 20x resolution


@dataclass
class Tag:
    code: int
    data: bytes
    long: bool = False  # the record header's form, kept so an untouched tag round-trips byte for byte

    def encode(self) -> bytes:
        n = len(self.data)
        if self.long or n >= 63:
            return struct.pack("<HI", (self.code << 6) | 63, n) + self.data
        return struct.pack("<H", (self.code << 6) | n) + self.data


@dataclass
class Movie:
    signature: bytes  # b"FWS", b"CWS", b"GFX" or b"CFX"
    version: int
    frame: bytes  # the RECT, the frame rate and the frame count, raw
    tags: list[Tag] = field(default_factory=list)

    def body(self) -> bytes:
        return self.frame + b"".join(t.encode() for t in self.tags)

    def to_bytes(self) -> bytes:
        body = self.body()
        length = struct.pack("<I", 8 + len(body))
        if self.signature in (b"CWS", b"CFX"):
            return self.signature + bytes([self.version]) + length + zlib.compress(body, 9)
        return self.signature + bytes([self.version]) + length + body


def read(blob: bytes) -> Movie:
    sig, version = blob[:3], blob[3]
    if sig in (b"CWS", b"CFX"):
        body = zlib.decompress(blob[8:])
    elif sig in (b"FWS", b"GFX"):
        body = blob[8:]
    else:
        raise ValueError(f"not an uncompressed or zlib SWF: {sig!r}")
    nbits = body[0] >> 3
    i = (5 + 4 * nbits + 7) // 8 + 4
    movie = Movie(sig, version, body[:i])
    while i < len(body):
        head = struct.unpack_from("<H", body, i)[0]
        i += 2
        code, n, long = head >> 6, head & 63, False
        if n == 63:
            n, long = struct.unpack_from("<I", body, i)[0], True
            i += 4
        movie.tags.append(Tag(code, body[i:i + n], long))
        i += n
        if code == END:
            break
    return movie


# --- bits ---------------------------------------------------------------------------------------------------------

class BitWriter:
    def __init__(self):
        self.out, self.acc, self.n = bytearray(), 0, 0

    def u(self, value: int, bits: int):
        for k in range(bits - 1, -1, -1):
            self.acc = (self.acc << 1) | ((value >> k) & 1)
            self.n += 1
            if self.n == 8:
                self.out.append(self.acc)
                self.acc, self.n = 0, 0

    def s(self, value: int, bits: int):
        self.u(value & ((1 << bits) - 1), bits)

    def flush(self) -> bytes:
        if self.n:
            self.out.append(self.acc << (8 - self.n))
            self.acc, self.n = 0, 0
        return bytes(self.out)


class BitReader:
    def __init__(self, data: bytes, pos: int = 0):
        self.data, self.bit = data, pos * 8

    def u(self, bits: int) -> int:
        v = 0
        for _ in range(bits):
            byte = self.data[self.bit >> 3]
            v = (v << 1) | ((byte >> (7 - (self.bit & 7))) & 1)
            self.bit += 1
        return v

    def s(self, bits: int) -> int:
        v = self.u(bits)
        return v - (1 << bits) if bits and v >> (bits - 1) else v

    def align(self) -> int:
        self.bit = (self.bit + 7) & ~7
        return self.bit >> 3


def sbits(*values: int) -> int:
    """The fewest bits a signed field needs to hold every value."""
    n = 1
    for v in values:
        while not -(1 << (n - 1)) <= v < (1 << (n - 1)):
            n += 1
    return n


def rect(xmin: int, xmax: int, ymin: int, ymax: int) -> bytes:
    n = sbits(xmin, xmax, ymin, ymax)
    w = BitWriter()
    w.u(n, 5)
    for v in (xmin, xmax, ymin, ymax):
        w.s(v, n)
    return w.flush()


def read_rect(r: BitReader) -> tuple[int, int, int, int]:
    n = r.u(5)
    return tuple(r.s(n) for _ in range(4))  # type: ignore[return-value]


# --- glyph shapes -------------------------------------------------------------------------------------------------
# A contour is a start point and a list of segments, each ("L", x, y) or ("Q", cx, cy, x, y), absolute coordinates
# in SWF space (y down).

def encode_glyph(contours: list[tuple[tuple[int, int], list[tuple]]]) -> bytes:
    """A SHAPE with one fill bit and no line bits; the first move sets FillStyle0 = 1 (the spec's rule for fonts)."""
    w = BitWriter()
    w.u(1, 4)
    w.u(0, 4)
    x = y = 0
    for k, (start, segs) in enumerate(contours):
        mx, my = start
        n = sbits(mx, my)
        w.u(0, 1)  # style change
        w.u(0, 1)  # new styles
        w.u(0, 1)  # line style
        w.u(0, 1)  # fill style 1
        w.u(1 if k == 0 else 0, 1)  # fill style 0
        w.u(1, 1)  # move to
        w.u(n, 5)
        w.s(mx, n)
        w.s(my, n)
        if k == 0:
            w.u(1, 1)
        x, y = mx, my
        for seg in segs:
            if seg[0] == "L":
                dx, dy = seg[1] - x, seg[2] - y
                if dx == 0 and dy == 0:
                    continue
                n = max(2, sbits(dx, dy))
                w.u(1, 1)
                w.u(1, 1)
                w.u(n - 2, 4)
                w.u(1, 1)  # general line
                w.s(dx, n)
                w.s(dy, n)
                x, y = seg[1], seg[2]
            else:
                cdx, cdy = seg[1] - x, seg[2] - y
                adx, ady = seg[3] - seg[1], seg[4] - seg[2]
                n = max(2, sbits(cdx, cdy, adx, ady))
                w.u(1, 1)
                w.u(0, 1)
                w.u(n - 2, 4)
                for v in (cdx, cdy, adx, ady):
                    w.s(v, n)
                x, y = seg[3], seg[4]
    w.u(0, 6)  # end of shape
    return w.flush()


def decode_glyph(data: bytes) -> list[tuple[tuple[int, int], list[tuple]]]:
    r = BitReader(data)
    nfill, nline = r.u(4), r.u(4)
    contours: list = []
    x = y = 0
    while True:
        if r.u(1) == 0:
            flags = r.u(5)
            if flags == 0:
                break
            new, line, f1, f0, move = [(flags >> k) & 1 for k in (4, 3, 2, 1, 0)]
            if new:
                raise ValueError("a glyph has no new styles")
            if move:
                n = r.u(5)
                x, y = r.s(n), r.s(n)
                contours.append(((x, y), []))
            for on, bits in ((f0, nfill), (f1, nfill), (line, nline)):
                if on:
                    r.u(bits)
        elif r.u(1) == 1:
            n = r.u(4) + 2
            if r.u(1):
                dx, dy = r.s(n), r.s(n)
            elif r.u(1):
                dx, dy = 0, r.s(n)
            else:
                dx, dy = r.s(n), 0
            x, y = x + dx, y + dy
            contours[-1][1].append(("L", x, y))
        else:
            n = r.u(4) + 2
            cdx, cdy, adx, ady = (r.s(n) for _ in range(4))
            cx, cy = x + cdx, y + cdy
            x, y = cx + adx, cy + ady
            contours[-1][1].append(("Q", cx, cy, x, y))
    return contours


# --- DefineFont3 --------------------------------------------------------------------------------------------------

@dataclass
class Glyph:
    code: int
    shape: bytes
    advance: int
    bounds: tuple[int, int, int, int]  # xmin, xmax, ymin, ymax


def define_font3(font_id: int, name: str, glyphs: list[Glyph], ascent: int, descent: int, leading: int,
                 kerning: list[tuple[int, int, int]] = ()) -> bytes:
    glyphs = sorted(glyphs, key=lambda g: g.code)
    n = len(glyphs)
    shapes = b"".join(g.shape for g in glyphs)
    wide = 2 * (n + 1) + len(shapes) > 0xFFFF
    size = 4 if wide else 2
    offsets, at = [], size * (n + 1)
    for g in glyphs:
        offsets.append(at)
        at += len(g.shape)
    fmt = "<I" if wide else "<H"
    table = b"".join(struct.pack(fmt, o) for o in offsets) + struct.pack(fmt, at) + shapes
    flags = 0x80 | (0x08 if wide else 0) | 0x04  # HasLayout, WideOffsets, WideCodes (DefineFont3 always)
    raw = name.encode() + b"\0"
    out = struct.pack("<HBBB", font_id, flags, 0, len(raw)) + raw + struct.pack("<H", n) + table
    out += b"".join(struct.pack("<H", g.code) for g in glyphs)
    out += struct.pack("<hhh", ascent, descent, leading)
    out += b"".join(struct.pack("<h", g.advance) for g in glyphs)
    out += b"".join(rect(*g.bounds) for g in glyphs)
    out += struct.pack("<H", len(kerning)) + b"".join(struct.pack("<HHh", a, b, k) for a, b, k in kerning)
    return out


@dataclass
class Font:
    font_id: int
    name: str
    glyphs: dict[int, Glyph]
    ascent: int
    descent: int
    leading: int


def parse_define_font3(data: bytes) -> Font:
    font_id, flags, _lang, nlen = struct.unpack_from("<HBBB", data, 0)
    name = data[5:5 + nlen].rstrip(b"\0").decode("latin-1")
    i = 5 + nlen
    n = struct.unpack_from("<H", data, i)[0]
    i += 2
    base = i
    wide = bool(flags & 0x08)
    size, fmt = (4, "<I") if wide else (2, "<H")
    offs = [struct.unpack_from(fmt, data, base + k * size)[0] for k in range(n + 1)]
    shapes = [data[base + offs[k]:base + (offs[k + 1] if k + 1 < n else offs[n])] for k in range(n)]
    i = base + offs[n]
    codes = list(struct.unpack_from(f"<{n}H", data, i))
    i += 2 * n
    ascent = descent = leading = 0
    adv = [0] * n
    bounds = [(0, 0, 0, 0)] * n
    if flags & 0x80:
        ascent, descent, leading = struct.unpack_from("<hhh", data, i)
        i += 6
        adv = list(struct.unpack_from(f"<{n}h", data, i))
        i += 2 * n
        r = BitReader(data, i)
        bounds = []
        for _ in range(n):
            bounds.append(read_rect(r))
            r.align()
    glyphs = {c: Glyph(c, s, a, b) for c, s, a, b in zip(codes, shapes, adv, bounds)}
    return Font(font_id, name, glyphs, ascent, descent, leading)


def font_library(fonts: list[tuple[str, bytes, str]]) -> Movie:
    """A Scaleform font library laid out as the working ones are (Dear Diary's fonts_fritzq.swf, measured 2026-10-30):
    SetBackgroundColor, then per font DefineFont3, DefineFontName and ExportAssets under the font's name, one frame."""
    tags = [Tag(SET_BACKGROUND, b"\xff\xff\xff")]
    for k, (name, define, copyright_) in enumerate(fonts, start=1):
        tags.append(Tag(DEFINE_FONT3, struct.pack("<H", k) + define[2:], True))
        tags.append(Tag(DEFINE_FONT_NAME, struct.pack("<H", k) + name.encode() + b"\0" + copyright_.encode() + b"\0"))
        tags.append(Tag(EXPORT_ASSETS, struct.pack("<HH", 1, k) + name.encode() + b"\0"))
    tags += [Tag(SHOW_FRAME, b""), Tag(END, b"")]
    frame = rect(0, 11000, 0, 8000) + struct.pack("<HH", 24 << 8, 1)
    return Movie(b"CWS", 10, frame, tags)


# --- DefineBitsLossless2 ------------------------------------------------------------------------------------------

@dataclass
class Bitmap:
    char_id: int
    rgba: np.ndarray  # H x W x 4, straight (not premultiplied) alpha, uint8


def decode_lossless2(data: bytes) -> Bitmap:
    char_id, fmt, w, h = struct.unpack_from("<HBHH", data, 0)
    if fmt == 5:
        raw = zlib.decompress(data[7:])
        argb = np.frombuffer(raw, np.uint8)[:w * h * 4].reshape(h, w, 4)
        rgba = argb[..., [1, 2, 3, 0]].astype(np.float32)
    elif fmt == 3:
        ncol = data[7] + 1
        raw = zlib.decompress(data[8:])
        pal = np.frombuffer(raw[:ncol * 4], np.uint8).reshape(ncol, 4).astype(np.float32)
        stride = (w + 3) & ~3
        idx = np.frombuffer(raw[ncol * 4:], np.uint8)[:stride * h].reshape(h, stride)[:, :w]
        rgba = pal[idx]
    else:
        raise ValueError(f"lossless2 format {fmt} (15-bit) is not drawn by Dear Diary")
    a = rgba[..., 3:4]
    rgb = np.where(a > 0, rgba[..., :3] * 255.0 / np.maximum(a, 1), 0)  # premultiplied in the file
    out = np.concatenate([np.clip(np.rint(rgb), 0, 255), a], axis=2).astype(np.uint8)
    return Bitmap(char_id, out)


def encode_lossless2(bitmap: Bitmap) -> bytes:
    """Always format 5 (32-bit premultiplied ARGB), whatever the source's format was."""
    h, w = bitmap.rgba.shape[:2]
    f = bitmap.rgba.astype(np.float32)
    a = f[..., 3:4]
    rgb = np.clip(np.rint(f[..., :3] * a / 255.0), 0, 255)
    argb = np.concatenate([a, rgb], axis=2).astype(np.uint8)
    return struct.pack("<HBHH", bitmap.char_id, 5, w, h) + zlib.compress(argb.tobytes(), 9)


def bitmaps(movie: Movie) -> list[tuple[int, Bitmap]]:
    """(tag index, bitmap) for every DefineBitsLossless2 in the movie."""
    return [(k, decode_lossless2(t.data)) for k, t in enumerate(movie.tags) if t.code == DEFINE_BITS_LOSSLESS2]


def imports(movie: Movie) -> list[tuple[str, str]]:
    """(library url, exported name) for every ImportAssets2 in the movie."""
    out = []
    for t in movie.tags:
        if t.code != IMPORT_ASSETS2:
            continue
        end = t.data.index(b"\0")
        url = t.data[:end].decode("latin-1")
        i = end + 3
        count = struct.unpack_from("<H", t.data, i)[0]
        i += 2
        for _ in range(count):
            i += 2
            e = t.data.index(b"\0", i)
            out.append((url, t.data[i:e].decode("latin-1")))
            i = e + 1
    return out
