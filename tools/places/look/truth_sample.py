"""The look audit on a real draft: N pieces chosen at random across kinds, each taken by the tool's own `at <piece>`;
from its id buffer the piece must be in frame and its drawn silhouette's centre within 5% of the frame of where its
box projects (a wrong transform, a wrong model or a piece not drawn fails). Counts of what was sent, loaded and drawn
and the models that failed to load come with it."""
from __future__ import annotations

import json
import random
import re
import time

import numpy as np

from tools.places.look import capture, geom, verbs

TOL = 0.05   # the silhouette's centre within this share of the frame of the box's projected centre
SEEN = 0.9   # ... when the capture sees at least this share of the piece (else what hides it moves the centre)
SPARSE = 0.25  # ... and its drawn pixels fill at least this share of its box's projection: an alpha-cut plant (hanging
               # moss, fronds) whose quads are mostly see-through draws a silhouette whose middle is not its box's


def judged(out: float, seen: float, off: float, fill: float) -> bool:
    """Drawn where its box is: (almost) no pixel outside the box's projection, and the silhouette centred on the box's
    unless the piece is partly hidden or drawn sparsely inside its box (alpha-cut foliage)."""
    return out <= 0.01 and (seen < SEEN or off <= TOL or (out == 0.0 and fill < SPARSE))
# effects (fire, mist, glows) are never drawn by the viewer (objects.js isEffect): not sampled, counted in the census
EFFECT = re.compile(r"^effects[\\/]|(^|[\\/])fx[^\\/]*\.nif$", re.I)


def is_effect(p: dict) -> bool:
    return bool(EFFECT.search(str(p.get("model") or "")) or re.match(r"fx", str(p.get("edid") or ""), re.I))


def run(d, place, n, check):
    sess = {"strokes": [], "snapshots": {}, "n": 0}
    t0 = time.time()
    d.open(place)
    sc = d.scene(place, [])
    load = round(time.time() - t0, 1)
    by: dict = {}
    for p in sc.pieces:
        if p.get("model") and not capture.helper_kind(p) and not is_effect(p) and p.get("kind") not in ("light", "actor"):
            by.setdefault(p.get("kind") or "other", []).append(p)
    rng = random.Random(f"{place}|{n}")
    pick, kinds = [], sorted(by)
    while len(pick) < n and any(by.values()):   # round the kinds, so every kind is sampled
        for k in kinds:
            if by[k] and len(pick) < n:
                pick.append(by[k].pop(rng.randrange(len(by[k]))))
    census, times, rows = None, [], []
    for p in pick:
        t1 = time.time()
        try:
            res = verbs.run(d, place, sess, "at", [p["id"], "--plain"])
        except Exception as e:
            check("B sample", f"{p['id']}: a capture was made", False, f"{type(e).__name__}: {e}")
            continue
        times.append(round(time.time() - t1, 1))
        census = res.get("census") or census
        cam = json.loads(open(res["png"] + ".json").read())
        cam = (cam.get("tiles") or [cam])[0]
        npz = np.load(res["png"] + ".ids.npz")
        ids, table = npz["ids0"], json.loads(str(npz["tables"]))[0]
        h, w = ids.shape
        ks = [int(npz["id0"]) + i for i, row in enumerate(table) if row[0] == p["id"]]
        m = np.isin(ids, ks)
        pp = geom.project(cam | {"w": w, "h": h}, geom.corners(p))
        front = pp[pp[:, 2] > 0]
        seen = ((res.get("views") or [{}])[0]).get("subject_seen", 0)
        if not m.any():
            ok, why = False, f"not drawn in its own view ({(res.get('views') or [{}])[0].get('why', '')})"
        elif not len(front):
            ok, why = False, "its box is behind the camera"
        else:
            bx = [max(0, front[:, 0].min()), max(0, front[:, 1].min()), min(w, front[:, 0].max()), min(h, front[:, 1].max())]
            ys, xs = np.nonzero(m)
            # every drawn pixel inside the box's projection (a wrong transform or a wrong model draws outside it)
            pad = 0.02 * w
            out = float(((xs < bx[0] - pad) | (xs > bx[2] + pad) | (ys < bx[1] - pad) | (ys > bx[3] + pad)).mean())
            sil = [(xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2]
            box = [(bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2]
            off = max(abs(sil[0] - box[0]) / w, abs(sil[1] - box[1]) / h)
            fill = float(m.sum()) / max(1.0, (bx[2] - bx[0]) * (bx[3] - bx[1]))
            ok = judged(out, seen, off, fill)
            why = (f"{out:.1%} of its pixels outside its box's projection; seen {seen:.0%}, fills {fill:.0%} of it, silhouette centre {off:.1%} "
                   f"of the frame from the box's ({p.get('edid')}, {p.get('model')})")
        rows.append({"id": p["id"], "kind": p.get("kind"), "ok": ok, "why": why, "png": res["png"]})
        check("B sample", f"{p['id']} ({p.get('kind')}): drawn where its box is", ok, why, png=res["png"])
    c = census or {}
    check("B sample", "every piece of the draft sent to the page", c.get("sent") == c.get("scene_pieces"),
          f"page {c.get('sent')}, scene {c.get('scene_pieces')}")
    check("B sample", "no model failed to load", not c.get("failed"), f"{c.get('stand_in')} stand-ins: {c.get('failed')}")
    print(json.dumps({"place": place, "load_s": load, "per_at_s": times, "census": c,
                      "passed": sum(r["ok"] for r in rows), "sampled": len(rows)}, default=str))
