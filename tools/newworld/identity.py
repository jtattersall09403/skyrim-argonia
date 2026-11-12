"""The regions' identity sheets: one row per region (newworld/sources/identity/regions.json) naming its light, how far
you see, its weather, its sound, its ground colour, its water look, one small signature thing and one creature, each
cited to the lore or stated as an extrapolation. The atmosphere (tools/newworld/atmosphere.py) reads the light, sight
and weather from it; the water types (tools/newworld/world/water_types.py) its water look; the sound its beds.
The recipe is docs/design/identity.md.

    python3 -m tools.newworld.identity check        # every row whole; every two neighbours differ on >= 3 of 6
    python3 -m tools.newworld.identity table        # the neighbour contrast table (markdown)
    python3 -m tools.newworld.identity adjacency    # re-measure the neighbours from the region raster

The six measured differences between two regions (DIMS):
- light: haze hue angle (CIE Lab, both chroma >= CHROMA_MIN) >= HUE_MIN degrees, or haze luminance x brightness
  ratio >= LUM_RATIO;
- sight: visibility (fraction of Skyrim's fog distances) ratio >= SIGHT_RATIO;
- weather: the most likely weather kind differs;
- sound: the day bed or the night bed differs;
- ground: the ground colour family differs;
- water: the water look differs.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "newworld/sources/identity"
SHEET = SRC / "regions.json"
ADJ = SRC / "adjacency.json"
ECOLOGY = REPO / "newworld/sources/ecology/regions"
LANDCOVER = REPO / "out/newworld/landcover"

HUE_MIN, CHROMA_MIN, LUM_RATIO, SIGHT_RATIO, NEED = 40.0, 12.0, 1.3, 1.5, 3
DIMS = ("light", "sight", "weather", "sound", "ground", "water")
KINDS = ("fair", "cloudy", "mist", "rain", "storm", "steam")
RANGES = {"brightness": (0.6, 1.3), "saturation": (0.6, 1.3), "night": (0.5, 1.2), "visibility": (0.3, 1.2)}
FIELDS = ("light", "sight", "weather", "sound", "ground", "water", "signature", "creature")


def load(path: Path = SHEET) -> dict:
    return json.loads(path.read_text())


def adjacency(path: Path = ADJ) -> list[tuple[str, str]]:
    return [tuple(p.split("|")) for p in json.loads(path.read_text())["pairs"]]


# ---- colour (sRGB -> Lab, as atmosphere.py) ------------------------------------------------------------------------

def _lin(c: float) -> float:
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lab(c) -> tuple[float, float, float]:
    r, g, b = (_lin(v) for v in c)
    X, Y, Z = 0.4124 * r + 0.3576 * g + 0.1805 * b, 0.2126 * r + 0.7152 * g + 0.0722 * b, 0.0193 * r + 0.1192 * g + 0.9505 * b
    f = [v ** (1 / 3) if v > 0.008856 else 7.787 * v + 16 / 116 for v in (X / 0.95047, Y, Z / 1.08883)]
    return 116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])


def lum(c) -> float:
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def hue_chroma(c) -> tuple[float, float]:
    _, a, b = lab(c)
    return math.degrees(math.atan2(b, a)) % 360, math.hypot(a, b)


def dominant(chances: dict) -> str:
    return max(KINDS, key=lambda k: (chances.get(k, 0), -KINDS.index(k)))


# ---- the measures --------------------------------------------------------------------------------------------------

def differences(a: dict, b: dict) -> dict[str, tuple[bool, str]]:
    """Per dimension: (differs, the measure)."""
    out = {}
    (ha, ca), (hb, cb) = hue_chroma(a["light"]["haze"]), hue_chroma(b["light"]["haze"])
    dh = min(abs(ha - hb), 360 - abs(ha - hb)) if min(ca, cb) >= CHROMA_MIN else 0.0
    la, lb = lum(a["light"]["haze"]) * a["light"]["brightness"], lum(b["light"]["haze"]) * b["light"]["brightness"]
    lr = max(la, lb) / max(1e-6, min(la, lb))
    out["light"] = (dh >= HUE_MIN or lr >= LUM_RATIO, f"hue {dh:.0f} deg, lum x{lr:.2f}")
    va, vb = a["sight"]["visibility"], b["sight"]["visibility"]
    sr = max(va, vb) / min(va, vb)
    out["sight"] = (sr >= SIGHT_RATIO, f"x{sr:.2f}")
    da, db_ = dominant(a["weather"]["chances"]), dominant(b["weather"]["chances"])
    out["weather"] = (da != db_, f"{da}/{db_}")
    sa, sb = (a["sound"]["day"], a["sound"]["night"]), (b["sound"]["day"], b["sound"]["night"])
    out["sound"] = (sa[0] != sb[0] or sa[1] != sb[1], f"{'/'.join(sa)} vs {'/'.join(sb)}")
    out["ground"] = (a["ground"]["family"] != b["ground"]["family"], f"{a['ground']['family']}/{b['ground']['family']}")
    out["water"] = (a["water"]["look"] != b["water"]["look"], f"{a['water']['look']}/{b['water']['look']}")
    return out


def faults(sheet: dict, pairs: list[tuple[str, str]], ecology: Path | None = ECOLOGY) -> list[str]:
    rows = sheet["regions"]
    out = []
    beds, looks, fams = set(sheet["sound_beds"]), set(sheet["water_looks"]), set(sheet["ground_families"])
    slots = [r["slot"] for r in rows.values()]
    if len(set(slots)) != len(slots):
        out.append("two regions share a slot")
    for rid, r in rows.items():
        for f in FIELDS:
            if f not in r:
                out.append(f"{rid}: no {f}")
            elif not (r[f].get("cite") or r[f].get("extrapolation")):
                out.append(f"{rid}: {f} has neither a cite nor an extrapolation")
        if any(f not in r for f in FIELDS):
            continue
        for k, (lo, hi) in RANGES.items():
            v = r["sight"][k] if k == "visibility" else r["light"][k]
            if not lo <= v <= hi:
                out.append(f"{rid}: {k} {v} outside {lo}..{hi}")
        ch = r["weather"]["chances"]
        if sorted(ch) != sorted(KINDS) or sum(ch.values()) != 100 or min(ch.values()) < 1:
            out.append(f"{rid}: weather chances are not the six kinds summing to 100, each at least 1")
        for t in ("day", "night"):
            if r["sound"][t] not in beds:
                out.append(f"{rid}: sound bed {r['sound'][t]!r} is not a sound_beds row")
        if r["water"]["look"] not in looks:
            out.append(f"{rid}: water look {r['water']['look']!r} is not a water_looks row")
        if r["ground"]["family"] not in fams:
            out.append(f"{rid}: ground family {r['ground']['family']!r} is not a ground_families row")
        if ecology is not None and (ecology / f"{rid}.json").exists():
            kinds = {c["kind"] for c in json.loads((ecology / f"{rid}.json").read_text())["creatures"]}
            if r["creature"]["kind"] not in kinds:
                out.append(f"{rid}: creature {r['creature']['kind']} is not in its ecology file")
    for a, b in pairs:
        if a not in rows or b not in rows:
            out.append(f"{a}|{b}: a neighbour has no row")
            continue
        d = differences(rows[a], rows[b])
        n = sum(ok for ok, _ in d.values())
        if n < NEED:
            out.append(f"{a}|{b}: differ on {n} of 6 ({', '.join(k + ' ' + m for k, (ok, m) in d.items())})")
    return out


def table(sheet: dict, pairs) -> str:
    rows = sheet["regions"]
    lines = ["| neighbours | " + " | ".join(DIMS) + " | differ |", "|---" * (len(DIMS) + 2) + "|"]
    for a, b in pairs:
        d = differences(rows[a], rows[b])
        lines.append(f"| {a} / {b} | " + " | ".join(("**" if ok else "") + m + ("**" if ok else "") for ok, m in d.values())
                     + f" | {sum(ok for ok, _ in d.values())} |")
    return "\n".join(lines)


def measure_adjacency() -> dict:
    """Neighbouring regions from the landcover's region raster: two regions whose samples touch (side by side)."""
    import numpy as np
    r = np.load(LANDCOVER / "region.npy", mmap_mode="r")
    names = json.loads((LANDCOVER / "legend.json").read_text())["regions"]
    seen: dict[tuple[int, int], int] = {}
    for i in range(0, r.shape[0] - 1, 256):
        a = np.asarray(r[i:i + 257]).astype(np.int32)
        for x, y in ((a[:, :-1], a[:, 1:]), (a[:-1], a[1:])):
            m = x != y
            u, n = np.unique(np.minimum(x[m], y[m]) * 256 + np.maximum(x[m], y[m]), return_counts=True)
            for p, k in zip(u.tolist(), n.tolist()):
                seen[(p // 256, p % 256)] = seen.get((p // 256, p % 256), 0) + k
    pairs = sorted(f"{names[a]}|{names[b]}" for (a, b) in seen if a < len(names) and b < len(names))
    doc = {"about": "Neighbouring regions: pairs whose samples touch on the landcover's region raster "
                    "(out/newworld/landcover/region.npy), measured by `python -m tools.newworld.identity adjacency`.",
           "pairs": pairs}
    ADJ.write_text(json.dumps(doc, indent=1) + "\n")
    return doc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=("check", "table", "adjacency"))
    a = ap.parse_args(argv)
    if a.cmd == "adjacency":
        print(f"{len(measure_adjacency()['pairs'])} neighbouring pairs -> {ADJ}")
        return 0
    sheet, pairs = load(), adjacency()
    if a.cmd == "table":
        print(table(sheet, pairs))
        return 0
    bad = faults(sheet, pairs)
    for f in bad:
        print("FAIL ", f)
    print(f"identity: {len(sheet['regions'])} regions, {len(pairs)} neighbouring pairs, {len(bad)} faults")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
