"""How tall the ground's grass stands: every GRAS a painted material carries, against Skyrim's tallest.

    python3 -m tools.newworld.world.grasscheck [--data <Skyrim Data>]

A GRAS has no scale of its own: its height is its mesh's (the record's OBND top, in game units) and the engine varies
each blade's scale by up to the record's height range (DATA float at 16), so the tallest a grass stands is
top x (1 + range). Skyrim.esm's tallest land grass is TundraGrass01, 69 x 1.30 = 90 units (1.28 m); FieldGrass01
stands 87, every other land grass under 80; its kelp (up to 371) stands under water only. A third-person camera
sits at the head of a 1.0-scale race (about 120 units), so a grass no taller than Skyrim's own never hides the
player's view. The row: every grass a land material carries (texture.py material_rows) stands at most GRASS_MAX;
underwater grass (the river and sea floor materials) is not held to it. A record whose OBND is unset (Flower Fields'
flowers) is listed under no_bounds, not judged. Each record is read from the plugin that
wins it in the load order (newworld/sources/dressing/grass_census.json), else from the plugin its key names.
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

from tools.newworld.world import texture as tx

GRASS_MAX = 90  # game units: Skyrim.esm's tallest land grass at full height range (TundraGrass01, 69 x 1.30)
UNDERWATER = {"river_bottom", "river_mud", "ocean_floor"}
DATA = Path.home() / "games/skyrimse/Data"
CENSUS = tx.REPO / "newworld/sources/dressing/grass_census.json"


def heights(keys: set[str], data: Path = DATA) -> dict[str, tuple[int, float, float]]:
    """'plugin:edid' -> (OBND top, height range, tallest) read from the winning plugin."""
    from tools.argonia_world.esm import Plugin
    win = {}
    if CENSUS.exists():
        for g in json.loads(CENSUS.read_text())["grasses"]:
            win[f"{g['key'].split(':', 1)[1]}:{g['edid']}"] = g.get("winner")
    by_plugin: dict[str, set[str]] = {}
    for k in keys:
        plugin, edid = k.split(":", 1)
        by_plugin.setdefault(win.get(k) or plugin, set()).add(edid)
    out = {}
    for plugin, edids in by_plugin.items():
        p = Plugin.read(data / plugin, {"GRAS"})
        for r in p.records("GRAS"):
            if r.edid not in edids:
                continue
            ob, d = r.sub("OBND"), r.sub("DATA")
            top = struct.unpack("<6h", ob)[5] if ob else 0
            hr = struct.unpack_from("<f", d, 16)[0] if d and len(d) >= 20 else 0.0
            for k in keys:
                if k.split(":", 1)[1] == r.edid and (win.get(k) or k.split(":", 1)[0]) == plugin:
                    out[k] = (top, round(hr, 3), round(top * (1 + hr), 1))
    return out


def check(data: Path = DATA) -> dict:
    keys = {g for m in tx.material_rows() if m["id"].partition("~")[0] not in UNDERWATER for g in m["grass"]}
    h = heights(keys, data)
    tall = sorted((v[2], k) for k, v in h.items() if v[2] > GRASS_MAX)
    missing = sorted(keys - set(h))
    return {"grasses": len(keys), "tallest": max(((v[2], k) for k, v in h.items()), default=(0, None)),
            "no_bounds": sorted(k for k, v in h.items() if v[0] == 0),
            "over": [{"grass": k, "tallest": t} for t, k in tall], "unread": missing, "limit": GRASS_MAX,
            "pass": not tall and not missing}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", type=Path, default=DATA)
    a = ap.parse_args(argv)
    r = check(a.data)
    print(json.dumps(r, indent=1))
    print("grasscheck", "PASS" if r["pass"] else f"FAIL: {len(r['over'])} grasses over {GRASS_MAX} units, {len(r['unread'])} unread")
    return 0 if r["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
