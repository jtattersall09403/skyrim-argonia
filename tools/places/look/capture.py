"""What a capture shows: the id buffer drawn with each image (agent.js idPass) read into a score. Every view says how
much of its subject is seen (of the subject's own projected pixels, the share visible and inside the frame), how much
of the frame the subject fills, what covers the rest, and whether the camera stands inside or under something or the
ground is not drawn. A capture that fails says why, in its JSON and in a red banner across the image.

Pure functions over arrays and dicts (tested in tools/tests/test_places_look.py); the page draws, this judges."""
from __future__ import annotations

import base64
import re

import numpy as np

NOTHING, LAND, WATER, OTHER, HELPER = 0, 1, 2, 3, 4
# Every judgement's threshold, in one place (docs/design/agent-view.md, What a capture guarantees; proved by
# `look truth`). A capture with a subject fails when:
MIN_SEEN = 0.35       # under this share of its subject is seen (visible and in the frame, of its whole projection)
MIN_FILL = 0.03       # the subject fills under this share of the frame and some other piece fills more than it
LENS = 0.5            # one piece other than the subject covers over this share of the frame
NEAR = 200.0          # a piece other than the subject within this many units of the camera ...
NEAR_SHARE = 0.04     # ... covers over this share of the frame (a leaf, a sail, a post across the lens)
ON_SUBJECT = 1.5      # the camera stands inside its subject's box or on it (up to this many eye heights over its top)
# `seen` counts the subject's pixels at the id pass's own resolution (at most 768 wide) against the subject drawn
# alone at that resolution in the same frame (plus its part outside the frame from a wider pass): occlusion by thin
# branches is counted pixel for pixel; the error is about one pixel along the subject's outline (SEEN_ERROR).
SEEN_ERROR = 0.02
SOLID_KINDS = {"building", "static", "rock", "tree", "door", "furniture", "container", "activator", "clutter"}

# Things the game never draws: editor markers, collision boxes, triggers, occlusion planes (agent.js isHelper).
HELPER_RE = re.compile(r"(^|[\\/])(x?marker|editormarker|idlemarker|furnituremarker|patrolmarker|collision|trigger|"
                       r"occlusion|roommarker|portal)[^\\/]*$|markers?[\\/]", re.I)
HELPER_EDID = re.compile(r"marker$|^xmarker|trigger|collision|occlusion", re.I)
CRAFT = re.compile(r"crafting", re.I)   # a crafting station is drawn, whatever its model is called
HELPER_NAMES = (("heading", "heading marker"), ("xmarker", "x-marker"), ("idle", "idle marker"),
                ("furniture", "furniture marker"), ("patrol", "patrol marker"), ("collision", "collision box"),
                ("trigger", "trigger"), ("occlusion", "occlusion plane"), ("portal", "room portal"),
                ("roommarker", "room marker"), ("marker", "editor marker"))


def helper_kind(p: dict) -> str | None:
    """What a piece the game never draws is ('heading marker', 'collision box', ...); None for anything drawn."""
    model, edid = str(p.get("model") or ""), str(p.get("edid") or "")
    if CRAFT.match(edid) or not (p.get("kind") == "marker" or HELPER_RE.search(model) or HELPER_EDID.search(edid)):
        return None
    base = model.replace("\\", "/").rsplit("/", 1)[-1].lower()
    if base.startswith("markerx") and "heading" not in base or edid.lower() == "xmarker":
        return "x-marker"
    name = f"{base} {edid}".lower()
    return next((says for word, says in HELPER_NAMES if word in name and word != "xmarker"), "editor marker")


def decode(b64: str, w: int, h: int) -> np.ndarray:
    """The id buffer (RGBA bytes, bottom row first, as WebGL reads) as an (h, w) int array, top row first."""
    a = np.frombuffer(base64.b64decode(b64), np.uint8).reshape(h, w, 4).astype(np.int32)
    return (a[..., 0] | (a[..., 1] << 8) | (a[..., 2] << 16))[::-1]


def enlarge(ids: np.ndarray, w: int, h: int) -> np.ndarray:
    """An id buffer at the size of the image it belongs to: each pixel takes the id of the pass pixel it lies in."""
    if ids.shape == (h, w):
        return ids
    return ids[(np.arange(h) * ids.shape[0] // h)][:, (np.arange(w) * ids.shape[1] // w)]


def ref_at(ids: np.ndarray, table: list, id0: int, px: int, py: int) -> dict:
    """What is drawn at a pixel: a piece ({ref, kind, model, placeholder, helper}) or {'what': land|water|...}."""
    v = int(ids[int(py), int(px)])
    if v >= id0 and v - id0 < len(table):
        r = table[v - id0]
        return {"ref": r[0], "kind": r[1], "model": r[2], "placeholder": bool(r[3]), "helper": bool(r[4])}
    return {"what": {NOTHING: "sky", LAND: "land", WATER: "water", HELPER: "helper", OTHER: "other"}.get(v, "other")}


def point_in_piece(p: dict, pt, pad: float = 0.0) -> bool:
    """A world point inside a piece's oriented box (shrunk by pad)."""
    m = np.asarray(p["m"], float)
    try:
        loc = np.linalg.solve(m, np.array([*pt[:3], 1.0]))[:3]
    except np.linalg.LinAlgError:
        return False
    lo, hi = np.asarray(p["lo"], float) + pad, np.asarray(p["hi"], float) - pad
    return bool(np.all(loc >= lo) and np.all(loc <= hi))


def camera_inside(pos, pieces: list[dict], ground_z: float | None, room: bool = False,
                  crowns_cut: float | None = None) -> str | None:
    """Why the camera stands where it cannot see: under the ground, or inside a piece's box (a tree's: its crown,
    unless the crowns are cut away under the camera)."""
    if ground_z is not None and pos[2] < ground_z - 2 and not room:
        return f"the camera is under the ground ({ground_z - pos[2]:.0f} u under it)"
    for p in pieces:
        if p.get("kind") not in SOLID_KINDS or helper_kind(p) or not p.get("model"):
            continue
        if p.get("kind") == "clutter" and _size(p) < 120:
            continue
        if not point_in_piece(p, pos, 4.0):
            continue
        if p.get("kind") == "building" and not enclosed(p, pos):   # under a porch or an eave: its box, not its walls
            continue
        if p.get("kind") == "rock" and not in_rock(p, pos):   # over a mound or beside a boulder: its box, not its stone
            continue
        if treelike(p):   # a tree's box (a Hist's too) is mostly air: inside its crown (the upper part) or its trunk
            if crowns_cut is not None and pos[2] > crowns_cut:
                continue
            part = tree_part(p, pos)
            if part is None:
                continue
            return f"the camera is inside a tree's {part} ({p.get('edid') or p.get('id')})"
        return f"the camera is inside {p.get('edid') or p.get('id')} ({p.get('kind')}, {p.get('id')})"
    return None


def in_rock(p: dict, pos) -> bool:
    """A point inside a rock's box is inside the rock when its mesh's column there holds it: between the lowest and
    the highest surface over that spot (a grassy mound's box reaches far over the open ground round its hump, and a
    person stands on the mound). A rock with no mesh read counts as solid (its box, as before)."""
    try:
        from tools.places import shape
        S = shape.posed(p)
        if not S.mesh:
            return True
        top, under = S.at(pos[0], pos[1], "top"), S.at(pos[0], pos[1], "under")
    except Exception:
        return True
    if top is None:
        return False
    return (under if under is not None else -1e9) - 4.0 <= pos[2] <= top + 4.0


ENCLOSE_R = 1200.0   # how far round a point a building's walls are looked for
ENCLOSE_BAND = (-40.0, 120.0)   # the wall height band about the point that counts
ENCLOSE_GAP = 100.0   # degrees: a wider opening round the point than this is the open side of a porch


def enclosed(p: dict, pos) -> bool:
    """A point inside a building's box is inside the building when its mesh closes round it: the surface points
    within ENCLOSE_R and a wall's height band of it leave no opening wider than ENCLOSE_GAP degrees, and some of
    the mesh lies over it. Under a porch or an eave the open side leaves a wide gap. A building with no mesh read
    counts as enclosed (its box, as before)."""
    try:
        from tools.places import shape
        P = shape.posed(p).P
    except Exception:
        return True
    if not len(P):
        return True
    d = P - np.asarray(pos[:3], float)
    over = d[(np.hypot(d[:, 0], d[:, 1]) < 200.0) & (d[:, 2] > 0)]
    if not len(over):
        return False
    h = np.hypot(d[:, 0], d[:, 1])
    m = (h > 24.0) & (h < ENCLOSE_R) & (d[:, 2] > ENCLOSE_BAND[0]) & (d[:, 2] < ENCLOSE_BAND[1])
    if m.sum() < 8:
        return False
    a = np.sort(np.degrees(np.arctan2(d[m, 1], d[m, 0])))
    gaps = np.diff(np.concatenate([a, [a[0] + 360.0]]))
    return bool(gaps.max() <= ENCLOSE_GAP)


HIST_TREE = re.compile(r"^(ArgoniaTreeHist|HistTree|HistTrunk)", re.I)   # a Hist placed as a static is still a tree


def treelike(p: dict) -> bool:
    """A tree: its kind, or a Hist's tree or trunk (a static whose box is a crown and a trunk over open air)."""
    return p.get("kind") == "tree" or bool(HIST_TREE.match(str(p.get("edid") or "")))


CROWN_FROM = 0.4   # a tree's crown: the box over this share of its height
TRUNK = 0.15       # a tree's trunk: this share of its width about its middle


def tree_part(p: dict, pt) -> str | None:
    """'crown' or 'trunk' when a point inside a tree's box is in one; None for the open air under the crown."""
    m = np.asarray(p["m"], float)
    loc = np.linalg.solve(m, np.array([*pt[:3], 1.0]))[:3]
    lo, hi = np.asarray(p["lo"], float), np.asarray(p["hi"], float)
    f = (loc - lo) / np.maximum(hi - lo, 1e-6)
    if f[2] >= CROWN_FROM:
        return "crown"
    tr = trunk_at(p, float(pt[2]))
    if tr is not None:
        x0, y0, cell, grid = tr
        i, j = int((pt[0] - x0) // cell), int((pt[1] - y0) // cell)
        return "trunk" if 0 <= i < grid.shape[0] and 0 <= j < grid.shape[1] and grid[i, j] else None
    if abs(f[0] - 0.5) <= TRUNK and abs(f[1] - 0.5) <= TRUNK:
        return "trunk"
    return None


TRUNK_SLAB = 64.0   # units of height: a tree's trunk is read from its mesh's points this near the point's height
TRUNK_CELL = 24.0   # units: the cell its cut is drawn on
_TRUNKS: dict = {}


def trunk_at(p: dict, z: float):
    """A tree's trunk where it stands at height z: the cut of its mesh's points within TRUNK_SLAB of z, drawn on a
    TRUNK_CELL grid with what they close round filled in, as (x0, y0, cell, grid of bools); an empty cut (the open
    air) gives an empty grid. A tree's box is its crown's width and its middle is seldom over the trunk (a leaning
    cypress's box runs off to one side; one mesh can hold several trunks), and a great tree's roots spread far round
    its foot under an eye: only the wood at the eye's own height walls the eye off. None when no mesh is read (the
    box rule then)."""
    k = (str(p.get("model") or "").lower(), tuple(np.round(np.asarray(p["m"], float).ravel(), 3)))
    if k not in _TRUNKS:
        try:
            from tools.places import shape
            S = shape.posed(p)
            P = S.P
            _TRUNKS[k] = P[np.argsort(P[:, 2])] if S.mesh and len(P) >= 8 else None
        except Exception:
            _TRUNKS[k] = None
    P = _TRUNKS[k]
    if P is None:
        return None
    sk = (k, int(z // (TRUNK_SLAB / 2)))
    if sk in _TRUNKS:
        return _TRUNKS[sk]
    zc = (sk[1] + 0.5) * TRUNK_SLAB / 2
    lo, hi = np.searchsorted(P[:, 2], [zc - TRUNK_SLAB, zc + TRUNK_SLAB])
    cut = P[lo:hi]
    if not len(cut):
        got = (0.0, 0.0, TRUNK_CELL, np.zeros((0, 0), bool))
    else:
        from scipy import ndimage
        x0, y0 = float(cut[:, 0].min()) - TRUNK_CELL, float(cut[:, 1].min()) - TRUNK_CELL
        ij = ((cut[:, :2] - [x0, y0]) // TRUNK_CELL).astype(int)
        grid = np.zeros(tuple(ij.max(axis=0) + 2), bool)
        grid[ij[:, 0], ij[:, 1]] = True
        got = (x0, y0, TRUNK_CELL, ndimage.binary_fill_holes(grid))
    _TRUNKS[sk] = got
    return got


def _size(p: dict) -> float:
    return float(np.max(np.asarray(p["hi"], float) - np.asarray(p["lo"], float)))


def score(ids: np.ndarray, table: list, id0: int, subject: set[str], wide: dict | None, names: dict,
          inside: str | None = None, ground_needed: bool = True, part: bool = False, near: dict | None = None,
          on_subject: str | None = None) -> dict:
    """The capture's score. names: ref id -> {edid, kind} for the occluder list. part: the view frames a part of its
    subject (a tall thing's base), so what is seen is measured against the subject inside the frame. near: ref id ->
    its distance from the camera, for the pieces that cover the frame. on_subject: why the camera stands on or in its
    subject."""
    h, w = ids.shape
    n = float(w * h)
    vals, counts = np.unique(ids, return_counts=True)
    by: dict[str, int] = {}
    land = water = sky = helper = 0
    subj = 0
    for v, c in zip(vals.tolist(), counts.tolist()):
        if v >= id0 and v - id0 < len(table):
            rid = table[v - id0][0]
            if rid in subject:
                subj += c
            else:
                by[rid] = by.get(rid, 0) + c
        elif v == LAND:
            land += c
        elif v == WATER:
            water += c
        elif v == NOTHING:
            sky += c
        elif v == HELPER:
            helper += c
    wide = wide or {}
    alone = wide.get("alone")
    if alone is not None:   # the subject alone at this resolution in this frame, plus its part outside the frame
        outside = max(0.0, (wide.get("total") or 0.0) - (wide.get("in_frame") or 0.0))
        total = alone + (0.0 if part else outside)
        in_frame = alone
    else:
        total = wide.get("in_frame") if part else wide.get("total")
        total, in_frame = total or 0.0, wide.get("in_frame", 0)
    seen = min(1.0, subj / total) if total else 0.0
    occ = sorted(by.items(), key=lambda kv: -kv[1])[:3]
    res = {
        "subject_seen": round(seen, 3),
        "subject_in_frame": round(min(1.0, in_frame / total), 3) if total else 0.0,
        "subject_fills": round(subj / n, 3),
        "land": round(land / n, 3), "water": round(water / n, 3), "sky": round(sky / n, 3),
        "occluders": [{"piece": rid, "edid": (names.get(rid) or {}).get("edid"), "kind": (names.get(rid) or {}).get("kind"),
                       "share": round(c / n, 3)} for rid, c in occ],
    }
    why = []
    if not subject:
        pass
    elif not total:
        why.append("the subject is not drawn in this frame")
    elif seen < MIN_SEEN:
        why.append(f"only {seen:.0%} of the subject is seen")
    if inside:
        why.append(inside)
    if ground_needed and land + water == 0:
        why.append("no ground is drawn")
    if occ and occ[0][1] / n > LENS:
        o = res["occluders"][0]
        why.append(f"{o['edid'] or o['piece']} ({o['kind']}) covers {o['share']:.0%} of the lens")
    elif near:
        close = [(rid, c) for rid, c in by.items() if c / n > NEAR_SHARE and near.get(rid, 1e9) < NEAR]
        if close:
            rid, c = max(close, key=lambda kv: kv[1])
            why.append(f"{(names.get(rid) or {}).get('edid') or rid} lies {near[rid]:.0f} u from the lens and covers {c / n:.0%} of it")
    if subject and total and subj / n < MIN_FILL and occ and occ[0][1] > subj:
        o = res["occluders"][0]
        why.append(f"the subject fills {subj / n:.1%} of the frame and {o['edid'] or o['piece']} fills more ({o['share']:.0%})")
    if subject and on_subject:
        why.append(on_subject)
    res["capture"] = "failed" if why else "good"
    if why:
        res["why"] = "; ".join(why)
    return res


def banner(img, text: str):
    """A red banner across the image saying why a capture failed."""
    from PIL import ImageDraw
    from tools.places.look import draw
    img = img.convert("RGBA")
    d = ImageDraw.Draw(img)
    k = draw.unit(img.width)
    f = draw.font(round(13 * k), True)
    words, lines, cur = f"CAPTURE FAILED: {text}".split(), [], ""
    for wd in words:
        if d.textlength(cur + " " + wd, font=f) > img.width - 16 * k and cur:
            lines.append(cur)
            cur = wd
        else:
            cur = (cur + " " + wd).strip()
    lines.append(cur)
    lh = 20 * k
    y0 = img.height // 2 - lh / 2 * len(lines)
    d.rectangle([0, y0 - 6 * k, img.width, y0 + lh * len(lines) + 4 * k], fill=(200, 20, 20, 235))
    for i, ln in enumerate(lines):
        d.text((8 * k, y0 + lh * i), ln, fill=(255, 255, 255, 255), font=f)
    return img


def strike(img):
    """A failed tile struck through."""
    from PIL import ImageDraw
    img = img.convert("RGBA")
    from tools.places.look import draw
    d = ImageDraw.Draw(img)
    wd = round(5 * draw.unit(img.width))
    d.line([0, 0, img.width, img.height], fill=(220, 20, 20, 255), width=wd)
    d.line([0, img.height, img.width, 0], fill=(220, 20, 20, 255), width=wd)
    return img


def hatch(img, ids: np.ndarray, table: list, id0: int, label_of=None):
    """Stand-ins for models that did not load drawn hatched, and each helper labelled with what it is."""
    from PIL import Image, ImageDraw
    from tools.places.look import draw
    img = img.convert("RGBA")
    marks = []
    for k, row in enumerate(table):
        if not (row[3] or row[4]):
            continue
        ys, xs = np.nonzero(ids == id0 + k)
        if not len(xs):
            continue
        marks.append((row, xs, ys))
    if not marks:
        return img
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    o = np.zeros((img.height, img.width, 4), np.uint8)
    yy, xx = np.mgrid[0:img.height, 0:img.width]
    stripes = ((xx + yy) // max(6, round(6 * draw.unit(img.width)))) % 2 == 0
    for row, xs, ys in marks:
        m = np.zeros(stripes.shape, bool)
        m[ys, xs] = True
        if row[3]:
            o[m & stripes] = (255, 230, 0, 230)
            o[m & ~stripes] = (20, 20, 20, 230)
    over = Image.fromarray(o, "RGBA")
    img = Image.alpha_composite(img, over)
    d = ImageDraw.Draw(img)
    for row, xs, ys in marks:
        text = (label_of(row) if label_of else None) or (
            f"model did not load: {row[2]}" if row[3] else f"helper: {row[2]}")
        draw.tag(d, (int(xs.mean()), int(ys.min()) - round(14 * draw.unit(img.width))), text[:60])
    return img
