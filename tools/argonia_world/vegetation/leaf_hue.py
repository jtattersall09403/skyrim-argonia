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
Round 5 (lane 1.15-r5-crimson): the owner still saw crimson and pink canopies with no red diffuse placed. The cause was
not a texture: King of the Murkmire's Erut trees (eruttree01-04 and the tall 01/03/04) and SwampPlant08/08a (forms
ArgoniaTreeErut01-08, ArgoniaTreeSwampPlant02A/B) bake a crimson or pink VERTEX COLOUR into their leaf shape (mean RGB
(209,48,113) ... (255,74,168), every vertex), which the engine multiplies into the green leaf diffuse. `hue build-nif`
reads each manifest mesh's BSTriShape vertex colours (SSE NIF, vertex-desc colour attribute) and writes the per-shape
means into data/leaf-hue.json "meshes"; `red_vertex()` flags a shape whose mean is red or magenta, and lists.usable and
the check treat it exactly like a red diffuse.

A texture not in MEASURED is unmeasured (the vanilla `_resourcepack` set is read on the game machine only).
"""
from __future__ import annotations

import colorsys
import io
import json
import struct
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
ALLOWED_MESH = ("ztree's/plants/water lily",
                "hist trees/histflower")  # the Hist's flowers are the lore's red (topics/hist-and-sap.md:23)


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


def nif_shapes(d: bytes) -> list[dict]:
    """Per BSTriShape of a Skyrim SE NIF (BS version 100): {n, mean RGB, red-ish share} of its vertex colours, only the
    shapes that carry any. A shape without the colour attribute (or an old NiTriShape) multiplies by white: skipped."""
    p = d.index(b"\n") + 1 + 4 + 1
    _, nb, _ = struct.unpack_from("<III", d, p)
    p += 12
    for _ in range(3):
        p += 1 + d[p]
    nt, = struct.unpack_from("<H", d, p)
    p += 2
    types = []
    for _ in range(nt):
        n, = struct.unpack_from("<I", d, p)
        types.append(d[p + 4:p + 4 + n].decode("latin-1"))
        p += 4 + n
    idx = struct.unpack_from(f"<{nb}H", d, p)
    p += 2 * nb
    sizes = struct.unpack_from(f"<{nb}I", d, p)
    p += 4 * nb
    ns, = struct.unpack_from("<I", d, p)
    p += 8
    for _ in range(ns):
        n, = struct.unpack_from("<I", d, p)
        p += 4 + n
    p += 4
    out = []
    for i in range(nb):
        o, p = p, p + sizes[i]
        if types[idx[i]] not in ("BSTriShape", "BSMeshLODTriShape", "BSSubIndexTriShape"):
            continue
        q = o + 4
        q += 4 + 4 * struct.unpack_from("<I", d, q)[0] + 4 + 4 + 12 + 36 + 4 + 4 + 16 + 12
        desc, = struct.unpack_from("<Q", d, q)
        nv, = struct.unpack_from("<H", d, q + 10)
        q += 8 + 4 + 4
        if not (desc >> 44) & 0x20 or not nv:
            continue
        vs, co = (desc & 0xF) * 4, ((desc >> 24) & 0xF) * 4
        a = [d[q + v * vs + co:q + v * vs + co + 3] for v in range(nv)]
        a = [(c[0], c[1], c[2]) for c in a if len(c) == 3]
        r, g, b = (sum(c[k] for c in a) / len(a) for k in range(3))
        red = sum(1 for c in a if c[0] > 1.3 * max(c[1], 1) and c[0] > 1.3 * max(c[2], 1)) / len(a)
        out.append({"n": nv, "rgb": [round(r), round(g), round(b)], "red_share": round(red, 2)})
    return out


def red_shape(sh: dict) -> bool:
    """A vertex colour tints the leaf diffuse (multiplied): a mean in the red-magenta band at saturation, or most
    vertices red-dominant, is a crimson canopy whatever the diffuse says."""
    r, g, b = (c / 255 for c in sh["rgb"])
    h, s, _ = colorsys.rgb_to_hsv(r, g, b)
    return (s >= 0.3 and (h * 360 < RED_HUE[0] or h * 360 > RED_HUE[1])) or sh["red_share"] >= 0.5


def build_nif(mo2: Path, vanilla: Path, out: Path = MEASURED) -> dict:
    """Read every manifest mesh from the laid stack (as mesh_textures.build finds it: vanilla BSAs, then each row's
    loose files and BSAs, a later row winning) and write the per-shape vertex colours: numbers only."""
    from tools.argonia_world.vegetation import mesh_textures as mt
    where = {}
    for b in sorted(vanilla.glob("*Meshes*.bsa")):
        for n, sz, fo in mt._bsa(b)[2]:
            if n.endswith(".nif"):
                where.setdefault(n, (b, (sz, fo)))
    for m in sorted(x for x in mo2.iterdir() if x.is_dir()):
        for f in sorted(m.rglob("*")):
            r = str(f.relative_to(m)).lower().replace("\\", "/")
            if f.is_file() and r.endswith(".bsa"):
                for n, sz, fo in mt._bsa(f)[2]:
                    if n.endswith(".nif"):
                        where[n] = (f, (sz, fo))
            elif f.is_file() and r.endswith(".nif"):
                where[r] = (f, None)
    cache, res = {}, {}
    for mp in sorted(mt.load()["meshes"]):
        hit = where.get(mp)
        if hit is None:
            continue
        f, rec = hit
        if rec is None:
            data = f.read_bytes()
        else:
            if f not in cache:
                cache.clear()
                cache[f] = mt._bsa(f)[:2]
            data = mt._bsa_file(*cache[f], *rec)
        try:
            res[mp] = nif_shapes(data)
        except (struct.error, ValueError):
            res[mp] = None  # not a BS 100 NIF: unread, not claimed clean
    doc = json.loads(out.read_text(encoding="utf-8"))
    doc["meshes"] = dict(sorted(res.items()))
    out.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return doc


def load_meshes(path: Path = MEASURED) -> dict:
    return json.loads(path.read_text(encoding="utf-8")).get("meshes", {}) if path.exists() else {}


def red_vertex(model: str, shapes: dict) -> list[str]:
    """The vertex-colour means (as text) of a model's red shapes, [] when none (or a water lily, the flower's subject)."""
    from tools.argonia_world.vegetation import mesh_textures
    mp = mesh_textures.mesh_path(model or "")
    if any(a in mp for a in ALLOWED_MESH):
        return []
    return [f"vertex colour rgb{tuple(s['rgb'])}" for s in (shapes.get(mp) or []) if red_shape(s)]


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
    doc = {"about": "mean leaf colour per diffuse and vertex colour per mesh shape (vegetation/leaf_hue.py build, "
                    "build-nif); numbers only",
           "textures": dict(sorted({**old, **got}.items())),
           "meshes": load_meshes(out)}
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
    return [f"{f['form_key']} {f['model']}: red leaf {', '.join(ts)}"
            for f in placed if (ts := red_textures(f["model"], man, measured))]


def vertex_report(placed: list[dict], shapes: dict | None = None) -> list[str]:
    """Placed forms whose leaf shape carries a red vertex colour: a report, never a red. The owner ruled red leaves
    fine if they look reasonable (#37, 2026-11-03 11:54; lane 1.15-r5-trees-2 reverses lane 1.15-r5-crimson's drop)."""
    shapes = load_meshes() if shapes is None else shapes
    return [f"{f['form_key']} {f['model']}: {', '.join(ts)}" for f in placed if (ts := red_vertex(f["model"], shapes))]
