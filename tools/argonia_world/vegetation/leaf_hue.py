"""Leaf colour (lane 1.15-r4-red-trees; owner play test 3, finding 5): no placed form's leaf diffuse is red or magenta.

Batch two's readers saw crimson, pink and rose foliage in twelve of nineteen world stills. Named from the placement
shards at the stills' positions, they were two King of the Murkmire families whose own diffuse is red, not a fault of
ours: Hoddminir's meadowsweet 04 (`espmeadowsweet04.dds`, mean hue 14 deg, 66 % of its pixels red: ArgoniaFern01 and
ArgoniaFernCluster01A-C) and the rose-tinted lake plant (`ewplake10_rose.dds`, 30 % red: ArgoniaTreeSwampPlant03A/B).
Black Marsh's undergrowth is "ferns and flowered grasses ... under canopies of blue moss" (lore
topics/loading-facts.md:301, The Argonian Account); red is the Hist's flowers (topics/hist-and-sap.md:23), never a
fern's or a shrub's leaf. The same families' green variants stay (meadowsweet 05: ArgoniaFernCluster02*).

    python3 -m tools.argonia_world.vegetation hue build <bsa or loose dir>...   (machine-local, needs Pillow: reads
        each placed or candidate mesh's slot-0 textures and writes MEASURED: numbers only, never a file's content)

`red(t)` reads MEASURED; `lists.usable` drops a form any of whose diffuses is red unless ALLOWED names it with a why,
and `check()` (make check's world step, through `textures check`) fails on any placed form that still has one.
A texture not in MEASURED is unmeasured (the vanilla `_resourcepack` set is read on the game machine only).
"""
from __future__ import annotations

import colorsys
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MEASURED = ROOT / "data" / "leaf-hue.json"
RED_HUE = (20.0, 290.0)   # degrees: a mean hue below the first or above the second is the red-magenta band
MIN_SAT = 0.2             # a grey-brown mean is no colour at all
RED_SHARE = 0.25          # or a quarter of the opaque pixels are saturated red or magenta
NOT_LEAF = ("bark", "trunk", "stump", "wood", "root", "cut")  # a bark's warm brown is no canopy colour
# texture -> why it may stay red (a flower the lore grounds, low in the water, never a canopy)
ALLOWED = {
    "textures/plants/groundplants1/lily1.dds": "water-lily flower, aquatic: the Path of the Lily (lore "
                                               "topics/loading-facts.md:465), flowered marsh (:301)",
    "textures/plants/groundplants1/lily2.dds": "water-lily flower, aquatic (as lily1)",
    "textures/plants/groundplants1/lily1_violet.dds": "water-lily flower, aquatic (as lily1)",
    "textures/tr_flora_cupling_02.dds": "a cupling fungus's brown-orange cap, not a leaf: mushrooms of the marsh "
                                        "floor (lore topics/fauna-hazards.md:100, lucan mold and marsh fungi)",
}
# a lily's pad shares the rose lake-plant diffuse; the flower is the subject, the pad lies on the water
ALLOWED_MESH = ("ztree's/plants/water lily",)


def _stats(data: bytes) -> dict:
    from PIL import Image  # build only
    import numpy as np
    im = Image.open(io.BytesIO(data))
    im.load()
    if max(im.size) > 256:
        im = im.resize((256, 256 * im.size[1] // im.size[0] or 1))
    a = np.asarray(im.convert("RGBA")).astype(float) / 255
    keep = a[..., 3] > 0.5 if a[..., 3].min() < 0.99 else np.ones(a.shape[:2], bool)
    p = a[keep][:, :3]
    if not len(p):
        return {"opaque": 0}
    r, g, b = p.mean(0)
    h, s, _ = colorsys.rgb_to_hsv(r, g, b)
    mx, mn = p.max(1), p.min(1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    d = np.maximum(mx - mn, 1e-6)
    hue = np.where(mx == p[:, 0], ((p[:, 1] - p[:, 2]) / d) % 6,
                   np.where(mx == p[:, 1], (p[:, 2] - p[:, 0]) / d + 2, (p[:, 0] - p[:, 1]) / d + 4)) * 60
    red = ((hue < RED_HUE[0]) | (hue > RED_HUE[1])) & (sat > 0.25)
    return {"rgb": [round(r * 255), round(g * 255), round(b * 255)], "hue": round(h * 360), "sat": round(float(s), 2),
            "red_share": round(float(red.mean()), 2)}


def wanted() -> set[str]:
    from tools.argonia_world.vegetation import mesh_textures
    man = mesh_textures.load()
    return {t for m in man["meshes"].values() for s, t in m["slots"] if s == 0}


def build(sources: list[tuple[str, Path]], out: Path = MEASURED) -> dict:
    """Measure every manifest diffuse found in `sources` ((row, BSA or loose Data tree)), each from the row the
    manifest says supplies it on the player's machine."""
    from tools.argonia_world.vegetation import mesh_textures
    supplier = mesh_textures.load()["sources"]
    want, got = wanted(), {}
    old = load(out)
    for row, src in sources:
        want = {t for t in wanted() if supplier.get(t) == row}
        if src.is_file():
            b, flags, recs = mesh_textures._bsa(src)
            for n, sz, fo in recs:
                if n in want:
                    got[n] = _stats(mesh_textures._bsa_file(b, flags, sz, fo))
        else:
            for p in src.rglob("*.dds"):
                n = mesh_textures.norm(str(p.relative_to(src)))
                if n in want:
                    got[n] = _stats(p.read_bytes())
    doc = {"about": "mean leaf colour per diffuse (vegetation/leaf_hue.py build); numbers only",
           "textures": dict(sorted({**old, **got}.items()))}
    out.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return doc


def load(path: Path = MEASURED) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))["textures"] if path.exists() else {}


def red(t: str, measured: dict) -> bool:
    m = measured.get(t)
    if not m or "hue" not in m or t in ALLOWED or any(n in t.rsplit("/", 1)[-1] for n in NOT_LEAF):
        return False
    band = (m["hue"] < RED_HUE[0] or m["hue"] > RED_HUE[1]) and m["sat"] >= MIN_SAT
    return band or m["red_share"] >= RED_SHARE


def red_textures(model: str, man: dict, measured: dict) -> list[str]:
    from tools.argonia_world.vegetation import mesh_textures
    mp = mesh_textures.mesh_path(model or "")
    if any(a in mp for a in ALLOWED_MESH):
        return []
    slots = man["meshes"].get(mp, {}).get("slots", [])
    return sorted({t for s, t in slots if s == 0 and red(t, measured)})


def problems(placed: list[dict], man: dict, measured: dict) -> list[str]:
    return [f"{f['form_key']} {f['model']}: red leaf diffuse {', '.join(ts)}"
            for f in placed if (ts := red_textures(f["model"], man, measured))]
