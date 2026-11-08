"""The tile reads made one list of map symbols: each read placed on the map, snapped to its glyph, duplicates (one
symbol read by two neighbouring tiles) merged, the corrections applied, and the pixels measured where the reads
only named colours: the glyph's fill and the tint of its culture square.

Inputs: `newworld/sources/reads/tile_*.json` (the readers' records), `newworld/sources/reads/corrections.json`,
`out/newworld/glyphs.json` (tools/newworld/glyphs.py). Output: `out/newworld/symbols.json`.

    python3 -m tools.newworld.consolidate
"""
from __future__ import annotations

import glob
import json
import math

import numpy as np
from PIL import Image

from tools.newworld import frame as f

READS = f.ROOT / "sources" / "reads"
SNAP_PX = 30      # an icon read lies within about three quarters of a cell of its glyph
DUP_PX = 14       # two reads this close are one symbol


def reads() -> list[dict]:
    out = []
    for p in sorted(glob.glob(str(READS / "tile_*.json"))):
        d = json.loads(open(p).read())
        for i, s in enumerate(d["symbols"]):
            l, t, _, _ = f.cell_px_box(*s["cell"])
            s = dict(s, tile=d["tile"], index=i, px=l + 40 * float(s.get("fx", 0.5)), py=t + 40 * float(s.get("fy", 0.5)))
            out.append(s)
    corr = json.loads((READS / "corrections.json").read_text())
    drop = {(d["tile"], d["index"]) for d in corr["drop"]}
    out = [s for s in out if (s["tile"], s["index"]) not in drop]
    for st in corr["set"]:
        for s in out:
            if (s["tile"], s["index"]) == (st["tile"], st["index"]):
                s.update(st["fields"])
    for a in corr["add"]:
        out.append(dict(a, tile="corrections", index=len(out)))
    return out


def snap(syms: list[dict], glyphs: list[dict]) -> None:
    """Each read moves to the centre of the nearest detected glyph within SNAP_PX; a glyph serves one read."""
    G = np.array([[g["px"], g["py"]] for g in glyphs])
    taken: set[int] = set()
    pairs = []
    for k, s in enumerate(syms):
        d = np.hypot(G[:, 0] - s["px"], G[:, 1] - s["py"])
        for i in np.argsort(d)[:4]:
            if d[i] <= SNAP_PX:
                pairs.append((float(d[i]), k, int(i)))
    for dist, k, i in sorted(pairs):
        s = syms[k]
        if "glyph_id" in s or i in taken:
            continue
        taken.add(i)
        s["glyph_id"] = i
        s["snap_px"] = round(dist, 1)
        s["px"], s["py"] = glyphs[i]["px"], glyphs[i]["py"]


def snap_settlements(syms: list[dict], a: np.ndarray) -> None:
    """A settlement glyph is drawn with a white outline: its centre is the centre of the nearest white ring (the
    outline with its hole filled) within 36 px of the read."""
    from scipy import ndimage as ndi
    for s in syms:
        if s.get("glyph") != "settlement":
            continue
        x, y = int(round(s["px"])), int(round(s["py"]))
        x0, y0 = max(x - 36, 0), max(y - 36, 0)
        win = a[y0:y + 37, x0:x + 37].astype(int)
        white = (win.min(-1) > 225)
        lab, n = ndi.label(ndi.binary_fill_holes(white))
        best = None
        for i, sl in enumerate(ndi.find_objects(lab), start=1):
            h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
            if max(h, w) < 6 or max(h, w) > 48:
                continue
            cy, cx = ndi.center_of_mass(lab == i)
            d = math.hypot(x0 + cx - s["px"], y0 + cy - s["py"])
            if best is None or d < best[0]:
                best = (d, x0 + cx, y0 + cy, max(h, w))
        if best and best[0] <= 36:
            s["snap_px"], s["px"], s["py"], s["glyph_px"] = round(best[0], 1), best[1], best[2], best[3]
            s["glyph_id"] = "white-ring"


def merge_duplicates(syms: list[dict]) -> list[dict]:
    out: list[dict] = []
    for s in sorted(syms, key=lambda s: (not s.get("sure", True), s["tile"])):
        dup = next((o for o in out if math.hypot(o["px"] - s["px"], o["py"] - s["py"]) < DUP_PX
                    and (o.get("label") == s.get("label") or not o.get("label") or not s.get("label"))), None)
        if dup:
            dup.setdefault("also_read_in", []).append(s["tile"])
            if not dup.get("label") and s.get("label"):
                dup["label"] = s["label"]
            continue
        out.append(s)
    return out


def measure(syms: list[dict], a: np.ndarray, water: np.ndarray) -> None:
    """The glyph's fill (the median of the inner 5 x 5 px) and the culture square's tint: the median colour of
    land pixels 9 to 18 px from the centre that differ from plain land (the square's tinted ground)."""
    yy, xx = np.mgrid[-18:19, -18:19]
    rr = np.hypot(yy, xx)
    ring = (rr >= 9) & (rr <= 18)
    for s in syms:
        x, y = int(round(s["px"])), int(round(s["py"]))
        if not (18 <= x < f.WIDTH_PX - 18 and 18 <= y < f.HEIGHT_PX - 18):
            continue
        s["fill_rgb"] = [int(v) for v in np.median(a[y - 2:y + 3, x - 2:x + 3].reshape(-1, 3), 0)]
        win = a[y - 18:y + 19, x - 18:x + 19]
        wl = ~water[y - 18:y + 19, x - 18:x + 19]
        px = win[ring & wl]
        r, g, b = px[:, 0].astype(int), px[:, 1].astype(int), px[:, 2].astype(int)
        plain = (np.abs(r - 216) < 14) & (np.abs(g - 194) < 14) & (np.abs(b - 178) < 16)
        band = (np.abs(r - 226) < 10) & (np.abs(g - 210) < 10) & (np.abs(b - 188) < 12)
        lum = (r + g + b) / 3
        tint = px[~plain & ~band & (lum > 60) & (lum < 240)]
        if len(tint) >= 40 and len(tint) >= 0.35 * len(px):
            s["tint_rgb"] = [int(v) for v in np.median(tint, 0)]


def main() -> None:
    glyphs = json.loads((f.OUT / "glyphs.json").read_text())
    syms = reads()
    a = np.asarray(Image.open(f.BASE_MAP).convert("RGB"))
    snap_settlements(syms, a)
    snap([x for x in syms if x.get("glyph") != "settlement"], glyphs)
    syms = merge_duplicates(syms)
    water = np.asarray(Image.open(f.OUT / "raster" / "water.png").convert("L")) > 127
    measure(syms, a, water)
    for s in syms:
        s["cell"] = list(f.px_to_cell(s["px"], s["py"]))
        s["px"], s["py"] = round(s["px"], 1), round(s["py"], 1)
    syms.sort(key=lambda s: (-s["cell"][1], s["cell"][0], s["px"]))
    (f.OUT / "symbols.json").write_text(json.dumps(syms, indent=0))
    unsnapped = sum(1 for s in syms if "glyph_id" not in s)
    print(len(syms), "symbols;", unsnapped, "not snapped to a detected glyph;",
          sum(1 for s in syms if s.get("also_read_in")), "merged duplicates")


if __name__ == "__main__":
    main()
