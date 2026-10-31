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

SOURCES = ("interface/inventory components/itemcard.swf", "interface/tweenmenu.swf")
BSA = "Skyrim - Interface.bsa"
# shape character id -> what it is; cleared, not recoloured
KNOTS = {
    "interface/inventory components/itemcard.swf": {78: "the knot (Nordic interlace, 30x32)"},
    "interface/tweenmenu.swf": {48: "the tall rule's interlace foot", 53: "the right rule's knot end",
                                55: "the left rule's knot end", 57: "the drop rule's interlace head"},
}


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
        n, cleared = retint(movie, KNOTS[rel], stops)
        missing = set(KNOTS[rel]) - set(cleared)
        if missing:
            warnings.append(f"{rel}: knot shapes {sorted(missing)} not found (a changed file?)")
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(movie.to_bytes())
        report[rel] = {"from": got[1], "colours": n, "cleared": sorted(cleared)}
    return report, warnings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mods", type=Path, nargs="+", required=True, help="mod roots, HIGHEST priority first")
    ap.add_argument("--game-data", type=Path, help="Skyrim's Data folder (for the interface BSA)")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    report, warnings = run(a.mods, a.game_data, a.out)
    for rel, r in report.items():
        print(f"{a.out / rel}: {r['colours']} colours, knots cleared {r['cleared']} (from {r['from']})")
    for w in warnings:
        print("warning:", w)
    return 1 if warnings else 0


if __name__ == "__main__":
    sys.exit(main())
