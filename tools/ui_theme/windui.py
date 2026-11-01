"""Wind UI's frame art retinted to the frame style (1.12 §3; 0014: derived at install, never committed).

Wind UI (its DLL and files are never touched, its licence) draws four frame pieces from vector shapes in two game
SWFs and caches them as PNGs keyed by each source's size and hash (`SKSE/Plugins/WindUI/ArtCache/windui_100/stamp.txt`),
so a changed source is redrawn on the next launch (measured: panel9 and knot from the 63,896-byte vanilla
`interface/inventory components/itemcard.swf`, the caps from our 23,994-byte `interface/tweenmenu.swf`). It finds each
shape by its size ("menu art: no shape of WxH"), so we change colours only, never geometry or bounds:

- every shape colour runs through a luminance ramp of the frame tokens in ui/views/core/theme.css: black to the pane
  ground, Skyrim's grey rules to the gold-green trim, its white to the lit trim;
- the shapes that carry Nordic knotwork (KNOTS, measured by drawing every shape's outline, 2026-10-31) are cleared:
  alpha 0 where the tag carries alpha, else the pane ground, so they vanish on Wind UI's black panes (0006).

    python -m tools.ui_theme.windui --mods <mods>/argonia-theme <mods>/dear-diary --game-data <Skyrim>/Data --out <dir>
"""
from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

import numpy as np

from tools.ui_theme import swf
from tools.ui_theme.palette import tokens

SOURCES = ("interface/inventory components/itemcard.swf", "interface/tweenmenu.swf", "interface/quest_journal.swf")
BSA = "Skyrim - Interface.bsa"
# shape character id -> what it is; cleared, not recoloured
KNOTS = {
    "interface/inventory components/itemcard.swf": {78: "the knot (Nordic interlace, 30x32)"},
    "interface/quest_journal.swf": {},
    "interface/tweenmenu.swf": {48: "the tall rule's interlace foot", 53: "the right rule's knot end",
                                55: "the left rule's knot end", 57: "the drop rule's interlace head"},
}


# itemcard's card frames (one is panel9): a double rule whose four corners are knotted squares. Redrawn as our own
# frame (UI art, 0006) inside the identical bounds rect, so Wind UI's size match holds: an outer rule, an inner rule
# and a small solid lozenge at each corner, all in the lit trim.
FRAMES = {"interface/inventory components/itemcard.swf": (32, 64, 111, 144, 202, 216, 219)}
TW = 20  # twips per pixel
# Dear Diary's System page level bar (quest_journal #284, 612x22): a box between two knotted end caps. Redrawn as the
# box alone, a double rule in the ink, over 43%-74.5% of its width (measured from its outline), bounds kept.
BARS = {"interface/quest_journal.swf": {284: (0.43, 0.745)}}


def _poly(pts: list[tuple[int, int]]) -> list[tuple[int, int]]:
    return pts + [pts[0]]


def bar_contours(xmin: int, xmax: int, ymin: int, ymax: int, span: tuple[float, float]) -> list[list[tuple[int, int]]]:
    """One ring (outer path, reversed inner path) around the bar's box, 1.2 px thick."""
    a, b = xmin + int((xmax - xmin) * span[0]), xmin + int((xmax - xmin) * span[1])
    t, y0, y1 = int(1.2 * TW), ymin + 3 * TW, ymax - 3 * TW
    return [_poly([(a, y0), (b, y0), (b, y1), (a, y1)]),
            _poly([(a + t, y0 + t), (a + t, y1 - t), (b - t, y1 - t), (b - t, y0 + t)])]


def frame_contours(xmin: int, xmax: int, ymin: int, ymax: int) -> list[list[tuple[int, int]]]:
    """Closed polygons (twips): rings as an outer path and a reversed inner path, so a nonzero fill leaves the hole."""
    def ring(inset: float, width: float):
        a, b = int(inset * TW), int((inset + width) * TW)
        out = [(xmin + a, ymin + a), (xmax - a, ymin + a), (xmax - a, ymax - a), (xmin + a, ymax - a)]
        inn = [(xmin + b, ymin + b), (xmin + b, ymax - b), (xmax - b, ymax - b), (xmax - b, ymin + b)]
        return [_poly(out), _poly(inn)]
    polys = ring(0.5, 1.5) + ring(4.0, 0.75)
    r = 4 * TW
    for cx, cy in ((xmin + 3 * TW, ymin + 3 * TW), (xmax - 3 * TW, ymin + 3 * TW),
                   (xmax - 3 * TW, ymax - 3 * TW), (xmin + 3 * TW, ymax - 3 * TW)):
        polys.append(_poly([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]))
    return polys


def define_frame(cid: int, bounds: tuple[int, int, int, int], rgb, contours=None) -> swf.Tag:
    """A DefineShape3 of the contours (default frame_contours) in one solid fill (fill style 1 right of each edge)."""
    w = swf.BitWriter()
    body = bytearray(struct.pack("<H", cid) + swf.rect(*bounds) + bytes([1, 0x00, *[int(v) for v in rgb], 255, 0]))
    body.append(0x10)  # 1 fill bit, 0 line bits
    for poly in contours if contours is not None else frame_contours(*bounds):
        x0, y0 = poly[0]
        w.u(0, 1)
        w.u(0b00101, 5)  # fill1 + move
        n = swf.sbits(x0, y0)
        w.u(n, 5); w.s(x0, n); w.s(y0, n)
        w.u(1, 1)
        x, y = x0, y0
        for nx, ny in poly[1:]:
            dx, dy = nx - x, ny - y
            n = max(swf.sbits(dx, dy), 2)
            w.u(1, 1); w.u(1, 1); w.u(n - 2, 4)
            if dx and dy:
                w.u(1, 1); w.s(dx, n); w.s(dy, n)
            else:
                w.u(0, 1); w.u(1 if dx == 0 else 0, 1); w.s(dy if dx == 0 else dx, n)
            x, y = nx, ny
    w.u(0, 6)
    return swf.Tag(32, bytes(body) + w.flush(), True)


def redraw_frames(movie: swf.Movie, ids, rgb, bars: dict | None = None) -> list[int]:
    done = []
    bars = bars or {}
    for k, tag in enumerate(movie.tags):
        if tag.code in swf.SHAPE_TAGS and (cid := struct.unpack_from("<H", tag.data)[0]) in set(ids) | set(bars):
            bounds = swf.read_rect(swf.BitReader(tag.data, 2))
            movie.tags[k] = define_frame(cid, bounds, rgb, bar_contours(*bounds, bars[cid]) if cid in bars else None)
            done.append(cid)
    return done


def ramp(t: dict | None = None) -> list[tuple[float, np.ndarray]]:
    t = t or tokens()
    ground = np.array(t.get("frame-ground", (14, 19, 13)), np.float32)
    return [(0.0, ground), (0.25, ground * 1.6), (0.6, np.array(t["frame-trim"], np.float32)),
            (1.0, np.array(t["frame-trim-hi"], np.float32))]


def apply_ramp(rgb: np.ndarray, stops) -> np.ndarray:
    lum = (rgb.astype(np.float32) / 255) @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    xs = np.array([s[0] for s in stops], np.float32)
    out = np.stack([np.interp(lum, xs, np.array([s[1][c] for s in stops])) for c in range(3)], -1)
    return np.clip(np.rint(out), 0, 255).astype(np.uint8)


def retint(movie: swf.Movie, knots: dict[int, str], stops) -> tuple[int, list[int]]:
    """Colours changed and knot ids cleared, in place."""
    n, cleared = 0, []
    ground = stops[0][1].astype(np.uint8)
    for k, tag in enumerate(movie.tags):
        if tag.code not in swf.SHAPE_TAGS:
            continue
        offs, alpha = swf.shape_colours(tag)
        if not offs:
            continue
        cid = struct.unpack_from("<H", tag.data)[0]
        data = bytearray(tag.data)
        if cid in knots:
            for o in offs:
                data[o:o + 3] = bytes(ground)
                if alpha:
                    data[o + 3] = 0
            cleared.append(cid)
        else:
            rgb = np.array([list(data[o:o + 3]) for o in offs], np.uint8)
            for o, c in zip(offs, apply_ramp(rgb, stops)):
                data[o:o + 3] = bytes(int(v) for v in c)
        n += len(offs)
        movie.tags[k] = swf.Tag(tag.code, bytes(data), tag.long)
    return n, cleared


def source(rel: str, roots: list[Path], game_data: Path | None) -> tuple[bytes, str] | None:
    """The winning file: the first root (highest priority first) that has it, else the game's interface BSA."""
    for root in roots:
        p = root / rel
        if p.is_file():
            return p.read_bytes(), str(p)
    if game_data and (game_data / BSA).is_file():
        from tools.navmesh import bsa  # noqa: PLC0415

        try:
            return bsa.Archive(bsa.local(game_data / BSA)).get(rel), f"{game_data / BSA}:{rel}"
        except KeyError:
            return None
    return None


def run(roots: list[Path], game_data: Path | None, out: Path, stops=None) -> tuple[dict, list[str]]:
    stops = stops or ramp()
    report, warnings = {}, []
    for rel in SOURCES:
        got = source(rel, roots, game_data)
        if got is None:
            warnings.append(f"{rel}: not found in the mods or the game's {BSA}")
            continue
        movie = swf.read(got[0])
        n, cleared = (0, []) if rel in BARS else retint(movie, KNOTS[rel], stops)
        framed = redraw_frames(movie, FRAMES.get(rel, ()), tokens()["ink"] if rel in BARS else stops[-1][1], BARS.get(rel))
        missing = set(KNOTS[rel]) - set(cleared)
        if missing:
            warnings.append(f"{rel}: knot shapes {sorted(missing)} not found (a changed file?)")
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(movie.to_bytes())
        report[rel] = {"from": got[1], "colours": n, "cleared": sorted(cleared), "frames": framed}
    return report, warnings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mods", type=Path, nargs="+", required=True, help="mod roots, HIGHEST priority first")
    ap.add_argument("--game-data", type=Path, help="Skyrim's Data folder (for the interface BSA)")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    report, warnings = run(a.mods, a.game_data, a.out)
    for rel, r in report.items():
        print(f"{a.out / rel}: {r['colours']} colours, knots cleared {r['cleared']}, frames redrawn {r['frames']} (from {r['from']})")
    for w in warnings:
        print("warning:", w)
    return 1 if warnings else 0


if __name__ == "__main__":
    sys.exit(main())
