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


# What a light-looking base is, by its record's editor id and model: the class decides which paired bases lend it
# their light. Read in this order; the first that matches wins.
CLASSES = (
    ("unlit", re.compile(r"(?<![a-z])off(?![a-z])|off\d|unlit|dead|extinguish|burnt ?out|nolight|nofire|cold(?![a-z])|_off|empty", re.I)),
    ("not a source", re.compile(r"firewood|woodpile|log(pile|s)?\d|poker|tongs|firesalt|fireproof|lighthouse|light ?armou?r|flamboyant|fireball|"
                                r"spell|scroll|book|potion|ingredient|recipe|ward|lightning|daylight|skylight|lightbeam|lightray|godray", re.I)),
    ("ember", re.compile(r"ember|coals?(?![a-z])|ashpile|smoulder", re.I)),
    ("flame", re.compile(r"candle|torch|brazier|campfire|firepit|fire ?pit|bonfire|hearth|forge|cookfire|fire(?![a-z]*wood)|flame|sconce", re.I)),
    ("lamp", re.compile(r"lamp|lantern|chandel", re.I)),
    ("crystal", re.compile(r"crystal|gem(?![a-z])|soulgem|welkynd|varla|aetherium|geode", re.I)),
    ("fungus", re.compile(r"mushroom|fungus|shroom|gleamblossom|glowcap|nirnroot", re.I)),
    ("window", re.compile(r"window", re.I)),
    ("glow", re.compile(r"glow|magic|wisp|shrine|soul|portal|light|lit(?![a-z])", re.I)),
)
SIZES = ((60.0, "small"), (200.0, "medium"), (float("inf"), "large"))


def kind_of(edid: str, model: str) -> str | None:
    name = f"{edid or ''} {model or ''}"
    return next((k for k, rx in CLASSES if rx.search(name)), None)


def size_of(height: float) -> str:
    return next(n for h, n in SIZES if height < h)


def table(ev: dict, shapes=None) -> tuple[dict, list[dict]]:
    """({base: {light, offset [x, y, z], how, lit, placed, edid, class}}, [light-looking bases left out, with their
    reason]). `how` is `measured` (placed with that light at least MIN_LIT times and in MIN_SHARE of its placements),
    `measured, rarely` (placed with a light fewer times: the light it is given most often) or `by class` (never placed
    with one: the light the nearest measured base of its class and size carries, at the offset its own mesh gives,
    `mesh_offset`). `shapes(model)` gives (class offset, height) from a model's mesh, or None when there is none."""
    out, left, never = {}, [], []
    for b in ev["bases"]:
        lights, placed = b["lights"], max(1, int(b["placed"]))
        name = f"{b.get('edid') or ''} {b.get('model') or ''}"
        looks = bool(LOOKS_LIT.search(name))
        share = len(lights) / placed
        if b.get("type") == "LIGH":
            continue
        if lights and (len(lights) >= MIN_LIT and share >= MIN_SHARE or looks):
            light, _ = Counter(x[0] for x in lights).most_common(1)[0]
            mine = [x for x in lights if x[0] == light]
            off = [round(statistics.median(x[k] for x in mine), 1) for k in (1, 2, 3)]
            how = "measured" if len(lights) >= MIN_LIT and share >= MIN_SHARE else "measured, rarely"
            out[b["base"]] = {"light": light, "offset": off, "how": how, "lit": len(lights), "placed": placed,
                              "edid": b.get("edid") or "", "class": kind_of(b.get("edid"), b.get("model"))}
        elif looks:
            never.append(b)
    if shapes is not None:
        # the measured bases by class and size, with their heights: a never-lit base takes the light of the nearest
        measured: dict = {}
        for k, r in out.items():
            src = next((b for b in ev["bases"] if b["base"] == k), None)
            got = shapes(src.get("model")) if src and src.get("model") else None
            if got and r["class"] not in (None, "unlit", "not a source"):
                measured.setdefault(r["class"], []).append((got[1], r["light"], k))
    for b in never:
        cls = kind_of(b.get("edid"), b.get("model"))
        if cls in (None, "unlit", "not a source"):
            why = {"unlit": "an unlit variant (its name says off, unlit, dead or empty)", "not a source": "not a light source (its name says what it is)",
                   None: "its name names no kind of light source"}[cls]
            left.append({"base": b["base"], "edid": b.get("edid") or "", "type": b.get("type"), "why": why})
            continue
        got = shapes(b.get("model")) if shapes is not None and b.get("model") else None
        if got is None:
            left.append({"base": b["base"], "edid": b.get("edid") or "", "type": b.get("type"), "why": "no mesh the game would draw"})
            continue
        off, h = got
        pool = measured.get(cls) or []
        same = [m for m in pool if size_of(m[0]) == size_of(h)] or pool
        if not same:
            left.append({"base": b["base"], "edid": b.get("edid") or "", "type": b.get("type"), "why": f"no measured {cls} to take a light from"})
            continue
        hh, light, near = min(same, key=lambda m: abs(m[0] - h))
        out[b["base"]] = {"light": light, "offset": [round(v, 1) for v in off], "how": "by class", "lit": 0,
                          "placed": int(b["placed"]), "edid": b.get("edid") or "", "class": cls, "like": near}
    return dict(sorted(out.items())), sorted(left, key=lambda r: r["base"])


def mesh_offset(cls: str, model: str):
    """(where the light goes in the model's frame, the mesh's height) from its real shapes: the middle of its effect
    shapes (a fire's flames, a torch's glow) or of its glow-mapped shapes; else, for a flame or an ember, the middle of
    its topmost vertices (a wick's or a log's tip, a twentieth of the height); else the middle of all its vertices (a
    crystal's, a mushroom's, a lamp's body). None when the game would draw no mesh."""
    import numpy as np
    from tools.places.assets import nifglb
    from tools.places.assets.resolve import default, norm
    try:
        data = default().read(norm(model, "meshes"))
        head = nifglb.dump(data) if data is not None else None
    except Exception:
        return None
    if not head:
        return None
    shapes = [s for s in head["shapes"] if not s.get("hidden") and s["tris"] > 0]
    if not shapes:
        return None

    def pts(ss):
        out = []
        for s in ss:
            m = np.array(s["m"], float).reshape(3, 4)
            P = np.asarray(s["P"], float).reshape(-1, 3) if s.get("P") is not None else np.zeros((0, 3))
            if len(P):
                out.append(P @ m[:, :3].T + m[:, 3])
        return np.concatenate(out) if out else np.zeros((0, 3))
    every = pts(shapes)
    if not len(every):
        return None
    h = float(every[:, 2].max() - every[:, 2].min())
    lit = [s for s in shapes if nifglb.is_effect(s)] or [s for s in shapes if len(s.get("tex") or []) > 2 and (s["tex"][2] or "")]
    if lit and len(pts(lit)):
        return pts(lit).mean(axis=0).tolist(), h
    if cls in ("flame", "ember"):
        top = every[every[:, 2] >= every[:, 2].max() - max(1.0, h / 20)]
        return top.mean(axis=0).tolist(), h
    return every.mean(axis=0).tolist(), h


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
    memo: dict = {}

    def shapes(model):
        if model not in memo:
            memo[model] = mesh_offset(kind_of("", model) or "glow", model)
        return memo[model]
    t, left = table(ev, shapes)
    TABLE.write_text(json.dumps({"plugins": ev["plugins"], "min_lit": MIN_LIT, "min_share": MIN_SHARE, "pairs": t},
                                indent=0, ensure_ascii=False) + "\n")
    hows = Counter(r["how"] for r in t.values())
    print(f"light pairs: {len(t)} bases carry a light ({', '.join(f'{n} {k}' for k, n in sorted(hows.items()))}; "
          f"{len(ev['bases'])} bases measured, {ev['bound']} of {ev['lights']} lights bound)")
    print("left out by reason: " + ", ".join(f"{n} {k}" for k, n in Counter(r["why"] for r in left).most_common()))
    print(f"light-looking bases left out: {len(left)}")
    for r in left[:int(argv[1]) if len(argv) > 1 else 0]:
        print(f"  {r['base']} {r['edid']} ({r['type']}): {r['why']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
