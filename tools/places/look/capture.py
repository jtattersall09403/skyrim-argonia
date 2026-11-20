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
MIN_SEEN = 0.35       # a capture shows under this share of its subject: failed
LENS = 0.5            # one piece other than the subject over this share of the frame: it covers the lens
SOLID_KINDS = {"building", "static", "rock", "tree", "door", "furniture", "container", "activator", "clutter"}

# Things the game never draws: editor markers, collision boxes, triggers, occlusion planes (agent.js isHelper).
HELPER_RE = re.compile(r"(^|[\\/])(x?marker|editormarker|idlemarker|furnituremarker|patrolmarker|collision|trigger|"
                       r"occlusion|roommarker|portal)[^\\/]*$|markers?[\\/]", re.I)
HELPER_EDID = re.compile(r"marker$|^xmarker|trigger|collision|occlusion", re.I)
HELPER_NAMES = (("heading", "heading marker"), ("xmarker", "x-marker"), ("idle", "idle marker"),
                ("furniture", "furniture marker"), ("patrol", "patrol marker"), ("collision", "collision box"),
                ("trigger", "trigger"), ("occlusion", "occlusion plane"), ("portal", "room portal"),
                ("roommarker", "room marker"), ("marker", "editor marker"))


def helper_kind(p: dict) -> str | None:
    """What a piece the game never draws is ('heading marker', 'collision box', ...); None for anything drawn."""
    model, edid = str(p.get("model") or ""), str(p.get("edid") or "")
    if not (p.get("kind") == "marker" or HELPER_RE.search(model) or HELPER_EDID.search(edid)):
        return None
    name = f"{model.rsplit('/', 1)[-1]} {edid}".lower()
    return next((says for word, says in HELPER_NAMES if word in name), "editor marker")


def decode(b64: str, w: int, h: int) -> np.ndarray:
    """The id buffer (RGBA bytes, bottom row first, as WebGL reads) as an (h, w) int array, top row first."""
    a = np.frombuffer(base64.b64decode(b64), np.uint8).reshape(h, w, 4).astype(np.int32)
    return (a[..., 0] | (a[..., 1] << 8) | (a[..., 2] << 16))[::-1]


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


def camera_inside(pos, pieces: list[dict], ground_z: float | None, room: bool = False) -> str | None:
    """Why the camera stands where it cannot see: under the ground, or inside a piece's box (a tree's: its crown)."""
    if ground_z is not None and pos[2] < ground_z - 2 and not room:
        return f"the camera is under the ground ({ground_z - pos[2]:.0f} u under it)"
    for p in pieces:
        if p.get("kind") not in SOLID_KINDS or helper_kind(p) or not p.get("model"):
            continue
        if p.get("kind") == "clutter" and _size(p) < 120:
            continue
        if not point_in_piece(p, pos, 4.0):
            continue
        if p.get("kind") == "tree":   # a tree's box is mostly air: inside its crown (the upper part) or its trunk
            part = tree_part(p, pos)
            if part is None:
                continue
            return f"the camera is inside a tree's {part} ({p.get('edid') or p.get('id')})"
        return f"the camera is inside {p.get('edid') or p.get('id')} ({p.get('kind')}, {p.get('id')})"
    return None


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
    if abs(f[0] - 0.5) <= TRUNK and abs(f[1] - 0.5) <= TRUNK:
        return "trunk"
    return None


def _size(p: dict) -> float:
    return float(np.max(np.asarray(p["hi"], float) - np.asarray(p["lo"], float)))


def score(ids: np.ndarray, table: list, id0: int, subject: set[str], wide: dict | None, names: dict,
          inside: str | None = None, ground_needed: bool = True, part: bool = False) -> dict:
    """The capture's score. names: ref id -> {edid, kind} for the occluder list. part: the view frames a part of its
    subject (a tall thing's base), so what is seen is measured against the subject inside the frame."""
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
    total = (wide or {}).get("total") or 0.0
    if part:
        total = (wide or {}).get("in_frame") or 0.0
    seen = min(1.0, subj / total) if total else 0.0
    occ = sorted(by.items(), key=lambda kv: -kv[1])[:3]
    res = {
        "subject_seen": round(seen, 3),
        "subject_in_frame": round(min(1.0, (wide or {}).get("in_frame", 0) / total), 3) if total else 0.0,
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
    f = draw.font(13, True)
    words, lines, cur = f"CAPTURE FAILED: {text}".split(), [], ""
    for wd in words:
        if d.textlength(cur + " " + wd, font=f) > img.width - 16 and cur:
            lines.append(cur)
            cur = wd
        else:
            cur = (cur + " " + wd).strip()
    lines.append(cur)
    y0 = img.height // 2 - 10 * len(lines)
    d.rectangle([0, y0 - 6, img.width, y0 + 20 * len(lines) + 4], fill=(200, 20, 20, 235))
    for i, ln in enumerate(lines):
        d.text((8, y0 + 20 * i), ln, fill=(255, 255, 255, 255), font=f)
    return img


def strike(img):
    """A failed tile struck through."""
    from PIL import ImageDraw
    img = img.convert("RGBA")
    d = ImageDraw.Draw(img)
    d.line([0, 0, img.width, img.height], fill=(220, 20, 20, 255), width=5)
    d.line([0, img.height, img.width, 0], fill=(220, 20, 20, 255), width=5)
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
    stripes = ((xx + yy) // 6) % 2 == 0
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
        draw.tag(d, (int(xs.mean()), int(ys.min()) - 14), text[:60])
    return img
