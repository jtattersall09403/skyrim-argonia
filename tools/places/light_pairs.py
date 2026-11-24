"""Which bases carry a light, measured on how the plugins themselves place them (docs/design/place-studio.md, A light
source comes with its light; the skill place-dressing).

`ArgoniaPlacesBuild lightpairs <out.json> <plugin...>` reads every interior cell and worldspace of Skyrim.esm, its
DLCs and the mods our places draw from, binds each placed light to the nearest other placed ref within 128 units (the
lights stage's own rule, tools/places/draft/lights.py), and counts per base how often it stands with a light, which
light and at what offset in the base's own frame. `table()` keeps every base placed with a light at least MIN_LIT times
and in at least MIN_SHARE of its placements: its light is the one most often beside it, at the median offset of
those. The table (`light_pairs.json`, form keys and offsets only) is the one pairing the lights stage and the studio
use; `python -m tools.places.light_pairs <evidence.json>` writes it and reports the light-looking bases it leaves out.
"""
from __future__ import annotations

import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

TABLE = Path(__file__).with_name("light_pairs.json")
MIN_LIT = 3         # a base seen lit fewer times is a coincidence of placement
MIN_SHARE = 0.1    # ... or lit in fewer of its placements (a crate that happens to stand by a lantern)
LOOKS_LIT = re.compile(r"candle|lantern|lamp|torch|sconce|brazier|fire|hearth|forge|glow|crystal|mushroom|chandel|ember", re.I)


def table(ev: dict) -> tuple[dict, list[dict]]:
    """({base: {light, offset [x, y, z], lit, placed, edid}}, [left-out light-looking bases with their reason])."""
    out, left = {}, []
    for b in ev["bases"]:
        lights, placed = b["lights"], max(1, int(b["placed"]))
        looks = bool(LOOKS_LIT.search(f"{b.get('edid') or ''} {b.get('model') or ''}"))
        share = len(lights) / placed
        if len(lights) >= MIN_LIT and share >= MIN_SHARE:
            light, _ = Counter(x[0] for x in lights).most_common(1)[0]
            mine = [x for x in lights if x[0] == light]
            off = [round(statistics.median(x[k] for x in mine), 1) for k in (1, 2, 3)]
            out[b["base"]] = {"light": light, "offset": off, "lit": len(lights), "placed": placed, "edid": b.get("edid") or ""}
        elif looks and b.get("type") not in ("LIGH",):
            why = ("never placed in these plugins" if not b["placed"] else "never placed with a light (self-lit, or lit by a light further off)" if not lights else
                   f"placed with a light {len(lights)} of {placed} times (under {MIN_LIT} or {int(MIN_SHARE * 100)}%)")
            left.append({"base": b["base"], "edid": b.get("edid") or "", "type": b.get("type"), "why": why})
    return dict(sorted(out.items())), sorted(left, key=lambda r: r["base"])


_cache: dict | None = None


def pairs() -> dict:
    """The committed table: {base key: {light, offset, ...}}."""
    global _cache
    if _cache is None:
        _cache = json.loads(TABLE.read_text())["pairs"] if TABLE.exists() else {}
    return _cache


def light_row(fix: dict, light_id: str, exterior: bool = True) -> dict | None:
    """The light a light source carries, as a place row: the table's light at its offset in the fixture's own frame
    (turned and tilted with it, scaled with it), seated `on` it outside; None when the table holds no light for it."""
    from tools.places import xform
    t = pairs().get(fix.get("base"))
    if not t or fix.get("kind") == "light":
        return None
    s = float(fix.get("scale", 1.0))
    R = xform.rotation(fix.get("rot") or [0, 0, 0])
    o = [sum(R[i][j] * t["offset"][j] * s for j in range(3)) for i in range(3)]
    pos = [round(fix["pos"][i] + o[i], 2) for i in range(3)]
    return {"id": light_id, "base": t["light"], "kind": "light", "pos": pos, "rot": [0.0, 0.0, 0.0], "scale": 1.0,
            "layer": "place", "flags": [],
            "seat": {"mode": "on", "on": fix["id"], "dz": round(o[2], 2)} if exterior else {"mode": "free"},
            "why": f"the light {fix['base']} carries where the game places it"}


def main(argv: list[str]) -> int:
    ev = json.loads(Path(argv[0]).read_text())
    t, left = table(ev)
    TABLE.write_text(json.dumps({"plugins": ev["plugins"], "min_lit": MIN_LIT, "min_share": MIN_SHARE, "pairs": t},
                                indent=0, ensure_ascii=False) + "\n")
    print(f"light pairs: {len(t)} bases carry a light (of {len(ev['bases'])} measured; {ev['bound']} of {ev['lights']} lights bound)")
    print(f"light-looking bases left out: {len(left)}")
    for r in left[:int(argv[1]) if len(argv) > 1 else 0]:
        print(f"  {r['base']} {r['edid']} ({r['type']}): {r['why']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
