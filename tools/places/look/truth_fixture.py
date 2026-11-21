"""The look audit on the golden scene (tools/tests/fixtures/look_truth): every check with its exact expectation.

The oracle: every model of the scene is a set of boxes (make.MODELS), so a ray caster over those boxes, written here
apart from the page, says which piece each pixel must show. The page's id buffer is held to it."""
from __future__ import annotations

import json
import math
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from tools.places.look import capture, geom, verbs
from tools.places.look.scene import ROOT, data_out

PLACE = "fx_truth"
sys.path.insert(0, str(ROOT / "tools" / "tests" / "fixtures" / "look_truth"))
import make as FX  # noqa: E402  the golden scene's own description

PX = 2.0   # geometry: a silhouette's edges within this many pixels of where its boxes project
TIMES: dict = {}


# ---------- the oracle ----------
def boxes_of(sc, helpers=False, only=None) -> list:
    """(piece id, world-from-local matrix, lo, hi) for each box of each piece the page draws."""
    out = []
    for p in sc.pieces:
        if only is not None and p["id"] not in only:
            continue
        if capture.helper_kind(p) and not helpers:
            continue
        m = np.asarray(p["m"], float)
        bs = FX.MODELS.get(p.get("model"))
        if bs is None:   # a model that is missing: its stand-in, the base's bounds
            bs = [(p["lo"], p["hi"], None)]
        for lo, hi, _ in bs:
            out.append((p["id"], m, np.asarray(lo, float), np.asarray(hi, float)))
    return out


def rays(cam, w, h):
    x, y, z = geom.axes(cam)
    PXg, PYg = np.meshgrid((np.arange(w) + 0.5), (np.arange(h) + 0.5))
    nx, ny = PXg / w * 2 - 1, 1 - PYg / h * 2
    pos = np.asarray(cam["pos"], float)
    if cam.get("ortho"):
        O = pos + nx[..., None] * x * cam["ortho"]["halfW"] + ny[..., None] * y * cam["ortho"]["halfH"]
        D = np.broadcast_to(-z, O.shape)
    else:
        t = math.tan(math.radians(cam.get("fov", 50.0)) / 2)
        D = -z + nx[..., None] * x * t * w / h + ny[..., None] * y * t
        D = D / np.linalg.norm(D, axis=-1, keepdims=True)
        O = np.broadcast_to(pos, D.shape)
    return O.reshape(-1, 3), D.reshape(-1, 3)


def oracle(sc, cam, w, h, helpers=False, only=None) -> tuple[np.ndarray, list]:
    """(h, w) array of indices into the returned id list (-1: no piece), by ray casting the boxes."""
    O, D = rays(cam, w, h)
    if not cam.get("ortho"):   # the perspective camera's near plane cuts at depth `near` along the view axis
        z = geom.axes(cam)[2]
        depth = -(D @ z)
        tmin = (cam.get("near") or 10) / np.maximum(depth, 1e-9)
        tmax = (cam.get("far") or 2e5) / np.maximum(depth, 1e-9)
    else:
        tmin = np.full(len(O), float(cam.get("near") or 1))
        tmax = np.full(len(O), float(cam.get("far") or 2e5))
    planes = [np.asarray(c, float) for c in cam.get("clip") or []]
    best = np.full(len(O), np.inf)
    who = np.full(len(O), -1)
    ids = []
    for pid, m, lo, hi in boxes_of(sc, helpers, only):
        if pid not in ids:
            ids.append(pid)
        k = ids.index(pid)
        inv = np.linalg.inv(m)
        Ol = O @ inv[:3, :3].T + inv[:3, 3]
        Dl = D @ inv[:3, :3].T
        with np.errstate(divide="ignore", invalid="ignore"):
            a = (lo - Ol) / Dl
            b = (hi - Ol) / Dl
        a = np.where(np.isnan(a), -np.inf, a)
        b = np.where(np.isnan(b), np.inf, b)
        t0 = np.max(np.minimum(a, b), axis=1)
        t1 = np.min(np.maximum(a, b), axis=1)
        hit = t1 >= np.maximum(t0, 0)
        # the first face the clipping keeps: the near face, else the far one (faces are drawn both sides)
        t = np.full(len(O), np.inf)
        for cand in (t0, t1):
            ok = hit & (cand >= tmin) & (cand <= tmax) & np.isinf(t)
            P = O + D * cand[:, None]
            for pl in planes:
                ok &= (P @ pl[:3] + pl[3]) >= 0
            t = np.where(ok, cand, t)
        closer = t < best
        best = np.where(closer, t, best)
        who = np.where(closer, k, who)
    # a hit under the ground there is hidden by it (exact looking down; near enough elsewhere on this gentle ground)
    hitp = np.nonzero(who >= 0)[0]
    if len(hitp):
        P = O[hitp] + D[hitp] * best[hitp, None]
        g = np.array([sc.ground.height(x, y) if sc.ground.has(x, y) else -1e9 for x, y in P[:, :2]])
        who[hitp[g > P[:, 2] + 1.0]] = -1
    return who.reshape(h, w), ids


def gpu_ids(r, cam) -> tuple[np.ndarray, list, int]:
    ids = capture.decode(r["ids"], *r["ref"])
    return ids, r["table"], r["id0"]


def mask_gpu(ids, table, id0, pid) -> np.ndarray:
    ks = [i for i, row in enumerate(table) if row[0] == pid]
    return np.isin(ids, [id0 + k for k in ks]) if ks else np.zeros(ids.shape, bool)


def bbox(mask):
    ys, xs = np.nonzero(mask)
    return None if not len(xs) else (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


def shot(d, cam, subject=(), helpers=False):
    d.helpers = helpers
    t0 = time.time()
    img, r = d.shot(cam | {"ids": True, "subject": list(subject)})
    TIMES.setdefault("shot_s", []).append(round(time.time() - t0, 2))
    return img, r


def save(img, root, name) -> str:
    p = str(root / f"{name}.png")
    img.convert("RGB").save(p)
    return p


# ---------- the checks ----------
def run(d, root, check):
    sess = {"strokes": [], "snapshots": {}, "n": 0}
    t0 = time.time()
    d.open(PLACE)
    TIMES["open_s"] = round(time.time() - t0, 1)
    sc = d.scene(PLACE, [])
    geometry(d, sc, root, check)
    sections(d, sc, root, check, sess)
    cameras(d, sc, root, check)
    scoring(d, sc, root, check)
    picking(d, sc, root, check, sess)
    census(d, sc, root, check)
    freshness(d, root, check, sess)
    rooms(d, root, check, sess)
    (root / "times.json").write_text(json.dumps(TIMES))
    # speed, measured against the stored budget (tools/tests/fixtures/look_truth/budget.json)
    budget = json.loads((ROOT / "tools" / "tests" / "fixtures" / "look_truth" / "budget.json").read_text())
    TIMES["checks_s"] = round(time.time() - t0, 1)
    for k, lim in budget.items():
        got = max(TIMES[k]) if isinstance(TIMES.get(k), list) else TIMES.get(k)
        check("A10 speed", f"{k} within its budget", got is not None and got <= lim, f"{got} s, budget {lim} s")


def geometry(d, sc, root, check):
    """A.1: every piece drawn where its boxes are, in views from the side, above and the eye."""
    W, H = 768, 576
    views = {
        "oblique-se": geom.frame([300, 300, 0], [3300, 2800, 1500], "se", "oblique", W, H) | {"far": 2e5},
        "top": geom.frame([300, 300, 0], [3300, 2800, 600], "s", "top", W, H) | {"far": 2e5},
        "eye-s": {"pos": [1800, -1400, 112], "target": [1800, 1400, 300], "up": [0, 0, 1], "fov": 60, "w": W, "h": H, "near": 10, "far": 2e5},
        "pool-top": geom.frame([1158, 5254, -62], [1658, 5754, -60], "s", "top", W, H) | {"far": 2e5},
    }
    agree_all = []
    for name, cam in views.items():
        img, r = shot(d, cam)
        png = save(img, root, f"a1-{name}")
        ids, table, id0 = gpu_ids(r, cam)
        want, wid = oracle(sc, cam, *ids.shape[::-1])
        for k, pid in enumerate(wid):
            mo = want == k
            if mo.sum() < 30:
                continue
            bo = bbox(mo)
            if bo[0] <= 1 or bo[1] <= 1 or bo[2] >= ids.shape[1] - 2 or bo[3] >= ids.shape[0] - 2:
                continue   # cut by the frame's edge: its extent is the frame's
            bg = bbox(mask_gpu(ids, table, id0, pid))
            err = None if bg is None else max(abs(a - b) for a, b in zip(bo, bg))
            ok = check("A1 geometry", f"{name}: {pid.split('.')[-1]} drawn where its boxes project", err is not None and err <= PX,
                       f"oracle box {bo}, drawn {bg} (off by {err} px)", png=png)
            if not ok:
                np.savez_compressed(root / f"a1-{name}-{pid.split('.')[-1]}.npz", gpu=mask_gpu(ids, table, id0, pid), oracle=mo, ids=ids)
        # the whole frame: each pixel's piece as the oracle says
        g = np.full(ids.shape, -1)
        for k, pid in enumerate(wid):
            g[mask_gpu(ids, table, id0, pid)] = k
        anyp = (want >= 0) | (g >= 0)
        agree = float((want[anyp] == g[anyp]).mean()) if anyp.any() else 1.0
        agree_all.append(agree)
        check("A1 geometry", f"{name}: pixels showing the piece the oracle says", agree >= 0.97, f"{agree:.1%} agree", png=png)
    # --top is north-up and to scale: the house's north edge above its south edge, its width as the frame says
    cam = views["top"]
    a, b = geom.project(cam, [[1000, 750, 600], [1000, 1250, 600]])
    check("A1 geometry", "top view is north-up", b[1] < a[1] and abs(a[0] - b[0]) < 1, f"south {a[:2]}, north {b[:2]}")


def fx_height(x, y):
    """The golden scene's ground, read from its own description (the bundle's heights plus every land row, added),
    apart from the tool's reader."""
    cx, cy = math.floor(x / FX.CELL), math.floor(y / FX.CELL)
    Hm = np.array(FX.ground_heights(cx, cy), float).reshape(33, 33)
    for row in FX.LAND:
        if tuple(row["cell"]) == (cx, cy):
            for r, c, dz in row["verts"]:
                Hm[r, c] += dz
    fx_, fy_ = (x - cx * FX.CELL) / FX.STEP, (y - cy * FX.CELL) / FX.STEP
    c0, r0 = min(int(fx_), 31), min(int(fy_), 31)
    tx, ty = fx_ - c0, fy_ - r0
    return float((Hm[r0, c0] * (1 - tx) + Hm[r0, c0 + 1] * tx) * (1 - ty) + (Hm[r0 + 1, c0] * (1 - tx) + Hm[r0 + 1, c0 + 1] * tx) * ty)


def sections(d, sc, root, check, sess):
    """A.1 and A.7: a section's ground line at the row the heights say, on flat ground, the slope, the mound and the
    hollow of two land rows; the page's land and the numbers both add the land rows."""
    from PIL import Image
    lines = {
        "flat": ([200, 3400], [3800, 3400]),
        "slope": ([4300, 2400], [7900, 2400]),
        "mound": ([4096 + 6 * 128, 4096 + 16 * 128], [4096 + 24 * 128, 4096 + 16 * 128]),
        "hollow": ([400, 4096 + 11 * 128], [2400, 4096 + 11 * 128]),
    }
    for name, (A, B) in lines.items():
        res = verbs.run(d, PLACE, sess, "section", [f"{A[0]},{A[1]}", f"{B[0]},{B[1]}"])
        cam = json.loads(open(res["png"] + ".json").read())
        im = np.asarray(Image.open(res["png"]).convert("RGB")).astype(int)
        line = (np.abs(im - np.array([250, 170, 60])).sum(axis=2) < 60)
        a, b = np.asarray(A, float), np.asarray(B, float)
        errs, n = [], 0
        for s in np.linspace(0.05, 0.95, 24):
            q = a + (b - a) * s
            want = geom.project(cam, [[*q, fx_height(*q)]])[0]
            col = int(round(want[0]))
            rows = np.nonzero(line[:, col])[0]
            n += 1
            got = float(rows.mean()) if len(rows) else None
            if got is None or abs(got - want[1]) > PX + 0.5:   # a drawn line: half its width more
                errs.append((col, None if got is None else round(got - want[1], 1)))
        check("A1 section", f"{name}: the ground line at the row the heights say", n >= 20 and not errs,
              f"{n} columns; off (col, px): {errs[:8]}", png=res["png"])
        if name == "hollow":
            x, y = 1408, 4096 + 11 * 128
            check("A7 land rows add", "the numbers read the two rows' sum at the hollow",
                  abs(sc.ground.height(x, y) - fx_height(x, y)) < 0.5 and abs(fx_height(x, y) + 80) < 0.5,
                  f"numbers {sc.ground.height(x, y)}, the rows' sum {fx_height(x, y)}")
    # the page's land is the sum too: our pool (z -60) shows in the hollow (-80) as the oracle sees it; a page that
    # kept only the last row (-40) would bury it
    cam = geom.frame([1158, 5254, -62], [1658, 5754, -60], "s", "top", 768, 576) | {"far": 2e5}
    img, r = shot(d, cam)
    png = save(img, root, "a7-pool-top")
    ids, table, id0 = gpu_ids(r, cam)
    want, wid = oracle(sc, cam, *ids.shape[::-1])
    g = int(mask_gpu(ids, table, id0, f"{PLACE}.pool").sum())
    o = int((want == wid.index(f"{PLACE}.pool")).sum()) if f"{PLACE}.pool" in wid else 0
    check("A7 land rows add", "the page draws the pool over the rows' sum, as the oracle sees it", o > 0 and abs(g - o) <= 0.03 * o,
          f"page {g} px, oracle {o} px", png=png)
    # the section's scale: units per pixel as stated
    cam, _, _ = verbs.section_setup(sc, *lines["flat"], 96, 768, 576)
    a, b = geom.project(cam, [[1000, 3400, 0], [2000, 3400, 0]])
    check("A1 section", "1000 units span the pixels the scale says", abs(abs(b[0] - a[0]) - 1000 / cam["upp"]) < 0.5,
          f"{abs(b[0] - a[0]):.1f} px for {1000 / cam['upp']:.1f}")


def floor_truth(sc, x, y, below):
    """The highest surface under (x, y) a person could stand on, under `below`: the ground or a box's top."""
    g = sc.ground.height(x, y)
    best = g if g is not None else -1e9
    for pid, m, lo, hi in boxes_of(sc):
        c = m @ np.array([[lo[0], lo[1], hi[2], 1], [hi[0], hi[1], hi[2], 1]]).T
        x0, x1 = sorted(c[0])
        y0, y1 = sorted(c[1])
        top = float(c[2][0])
        if x0 <= x <= x1 and y0 <= y <= y1 and top <= below - 30 and top > best:
            best = top
    return best


def inside_any(sc, pos):
    for pid, m, lo, hi in boxes_of(sc):
        if FX.BASES.get(next((e for e, (k, mo) in FX.BASES.items() if mo == sc.by_id[pid].get("model")), ""), ("", ""))[0] == "tree":
            continue   # a tree's box is mostly air; its trunk and crown boxes are checked as boxes below
        loc = np.linalg.solve(m, np.array([*pos, 1.0]))[:3]
        if np.all(loc > lo + 1) and np.all(loc < hi - 1):
            return pid
    for pid, m, lo, hi in boxes_of(sc, only={f"{PLACE}.tree"}):
        loc = np.linalg.solve(m, np.array([*pos, 1.0]))[:3]
        if np.all(loc > lo + 1) and np.all(loc < hi - 1):
            return pid
    return None


def cameras(d, sc, root, check):
    """A.2: an eye camera stands at eye height over what is under it, out of every piece, never under the ground."""
    W, H = 768, 576
    cases = {
        "on the slope": ("6000,1500", "e"),
        "on the mound": (f"{4096 + 16 * 128},{4096 + 16 * 128}", "s"),
        "by the deck": (f"{PLACE}.post0", "ne"),
        "beside the wall": (f"{PLACE}.wall", "s"),
        "under the crown": (f"{PLACE}.tree", "w"),
        "behind the house": (f"{PLACE}.house", "n"),
    }
    for name, (thing, side) in cases.items():
        th = sc.resolve(thing)
        if name == "under the crown":
            lo, hi = verbs.framing.base_box(th["lo"], th["hi"])
            th = dict(th, lo=lo, hi=hi)
        c = verbs.make_cam(sc, PLACE, th, side, "eye", W, H, {}, False, 1.0, sc.ground_under(th["lo"], th["hi"]))
        if c is None:
            check("A2 cameras", f"{name}: a spot was found", False, "make_cam found none")
            continue
        p = c["pos"]
        fl = floor_truth(sc, p[0], p[1], p[2])
        g = sc.ground.height(p[0], p[1])
        check("A2 cameras", f"{name}: eye height over what is under the camera", abs(p[2] - fl - geom.EYE) <= 3,
              f"camera z {p[2]:.1f}, floor under it {fl:.1f}, ground {g}")
        check("A2 cameras", f"{name}: not under the ground", g is None or p[2] > g, f"camera z {p[2]:.1f}, ground {g}")
        hit = inside_any(sc, p)
        check("A2 cameras", f"{name}: inside no piece", hit is None, f"inside {hit}")
    # a thing no person can stand near says so instead of drawing from a bad spot
    th = {"name": "boxed in", "kind": "point", "pieces": [], "lo": [990, 990, 300], "hi": [1010, 1010, 320], "point": [1000, 1000, 300]}
    c = verbs.make_cam(sc, PLACE, th, "s", "eye", W, H, {}, False, 0.05, 300.0)
    ok = c is None or (inside_any(sc, c["pos"]) is None and abs(c["pos"][2] - floor_truth(sc, *c["pos"]) - geom.EYE) <= 3)
    check("A2 cameras", "inside the house: no spot, or a good one", ok, f"camera {c and c['pos']}")
    # `at --stand x,y`: the eye 120 over the deck under the point, the capture scored; refused inside the wall
    dk = sc.resolve(f"{PLACE}.deck")
    x, y = dk["hi"][0] - 25, (dk["lo"][1] + dk["hi"][1]) / 2   # the deck's strip outside the house on it
    got = verbs.view(d, PLACE, [], "at", [f"{PLACE}.post0", "--stand", f"{x:.0f},{y:.0f}", "--plain"], keep=True)
    p = got["cam"]["pos"]
    fl = floor_truth(sc, p[0], p[1], p[2])
    check("A2 cameras", "--stand: the eye 120 over the deck under the point", abs(p[2] - fl - 120.0) <= 3,
          f"camera z {p[2]:.1f}, floor under it {fl:.1f}")
    hs = sc.resolve(f"{PLACE}.wall")
    try:
        verbs.view(d, PLACE, [], "at", [f"{PLACE}.post0", "--stand",
                                        f"{(hs['lo'][0] + hs['hi'][0]) / 2:.0f},{(hs['lo'][1] + hs['hi'][1]) / 2:.0f},"
                                        f"{(hs['lo'][2] + hs['hi'][2]) / 2:.0f}"], keep=True)
        refused = ""
    except ValueError as e:
        refused = str(e)
    check("A2 cameras", "--stand inside the wall's mesh is refused", "inside the mesh" in refused, refused or "not refused")


def scoring(d, sc, root, check):
    """A.3: seen, fills, occluders and the verdict against the oracle, for views whose answer is known."""
    W, H = 768, 576
    house = sc.resolve(f"{PLACE}.house")
    hs = {f"{PLACE}.house"}
    base = {"up": [0, 0, 1], "fov": 50, "w": W, "h": H, "near": 10, "far": 2e5}
    cases = [
        ("fully seen", geom.frame(house["lo"], house["hi"], "s", "oblique", W, H) | {"far": 2e5}, "good", None),
        ("half behind the wall", base | {"pos": [1000, 3400, 250], "target": [1000, 1000, 380]}, None, f"{PLACE}.wall"),
        ("behind the crown", base | {"pos": [4600, 1000, 1150], "target": [1000, 1000, 400]}, "failed", f"{PLACE}.tree"),
        ("from on its roof", base | {"pos": [1000, 1000, 700], "target": [1000, 1150, 0]}, "failed", None),
        ("small and far, another fills more", base | {"pos": [1000, 8000, 500], "target": [1000, 1000, 400], "fov": 30}, "failed", None),
        ("a leaf 50 u from the lens", base | {"pos": [1000, 250, 160], "target": [1000, 1000, 380]}, "failed", f"{PLACE}.leaf"),
    ]
    for name, cam, verdict, occ in cases:
        img, r = shot(d, cam, subject=hs)
        s, _ = verbs.judge(sc, cam, r, house, False)
        png = save(verbs.mark(img, s), root, f"a3-{name.replace(' ', '-')}")
        w, h = r["ref"]
        want, wid = oracle(sc, cam, w // 2, h // 2)
        k = wid.index(f"{PLACE}.house") if f"{PLACE}.house" in wid else None
        subj = float((want == k).sum()) if k is not None else 0.0
        wide = cam | {"fov": 2 * math.degrees(math.atan(3 * math.tan(math.radians(cam["fov"]) / 2)))}
        alone, _ = oracle(sc, wide, 3 * (w // 2), 3 * (h // 2), only=hs)
        total = float((alone >= 0).sum())
        seen = subj / total if total else 0.0
        n = float(want.size)
        fills = subj / n
        others = {pid: float((want == i).sum()) / n for i, pid in enumerate(wid) if pid not in hs}
        top = max(others, key=others.get) if others else None
        check("A3 scoring", f"{name}: seen as the oracle counts it", abs(s["subject_seen"] - seen) <= 0.04,
              f"tool {s['subject_seen']}, oracle {seen:.3f}", png=png)
        check("A3 scoring", f"{name}: fills as the oracle counts it", abs(s["subject_fills"] - fills) <= 0.01,
              f"tool {s['subject_fills']}, oracle {fills:.3f}", png=png)
        got = (s.get("occluders") or [{}])[0].get("piece")
        if top and others[top] > 0.005:
            check("A3 scoring", f"{name}: names first what the oracle says covers most", got == top, f"tool names {got}; oracle {top}", png=png)
        if occ:
            check("A3 scoring", f"{name}: {occ.split('.')[-1]} is what covers most", top == occ, f"oracle {top}", png=png)
        if verdict:
            check("A3 scoring", f"{name}: capture {verdict}", s["capture"] == verdict, f"tool: {s['capture']} ({s.get('why', '')})", png=png)
    # every threshold is named in one place
    names = ("MIN_SEEN", "MIN_FILL", "LENS", "NEAR", "NEAR_SHARE", "ON_SUBJECT", "SEEN_ERROR")
    check("A3 scoring", "thresholds named in capture.py", all(hasattr(capture, k) for k in names))


def picking(d, sc, root, check, sess):
    """A.4: pick at a pixel returns the piece drawn there."""
    for thing, args in ((f"{PLACE}.house", ["--plain", "--once"]), (f"{PLACE}.pool", ["--top", "--plain", "--once"])):
        res = verbs.run(d, PLACE, sess, "at", [thing, *args])
        npz = np.load(res["png"] + ".ids.npz")
        ids, table = npz["ids0"], json.loads(str(npz["tables"]))[0]
        m = mask_gpu(ids, table, int(npz["id0"]), thing)
        if not m.any():
            check("A4 pick", f"{thing.split('.')[-1]}: drawn to be picked", False, "not in its own view", png=res["png"])
            continue
        ys, xs = np.nonzero(m)
        i = len(xs) // 2
        got = verbs.pick(d, PLACE, [], [res["png"], str(xs[i]), str(ys[i])])
        check("A4 pick", f"{thing.split('.')[-1]}: pick at its pixel returns it", (got.get("drawn") or {}).get("ref") == thing,
              f"pick says {got.get('drawn')}", png=res["png"])


def census(d, sc, root, check):
    """A.5: what was sent, loaded and drawn is counted; a missing model is a listed stand-in; markers hidden."""
    cam = geom.frame([300, 300, 0], [3300, 2800, 1500], "se", "oblique", 768, 576) | {"far": 2e5}
    img, r = shot(d, cam)
    c = r.get("census") or {}
    n = len(sc.pieces)
    check("A5 census", "every piece sent to the page", c.get("sent") == n, f"page {c.get('sent')}, scene {n}")
    check("A5 census", "the missing model drawn as a listed stand-in", c.get("stand_in") == 1 and
          any(f["model"] == "gs/gone.nif" for f in c.get("failed", [])), f"{c.get('stand_in')} {c.get('failed')}")
    ids, table, id0 = gpu_ids(r, cam)
    gone = [row for row in table if row[0] == f"{PLACE}.gone"]
    check("A5 census", "the stand-in is flagged in the id buffer", bool(gone) and gone[0][3] == 1, f"{gone}")
    check("A5 census", "the marker is hidden without --helpers", not mask_gpu(ids, table, id0, f"{PLACE}.marker").any()
          and c.get("helpers_hidden") == 1, f"helpers hidden {c.get('helpers_hidden')}")
    img, r = shot(d, cam, helpers=True)
    ids, table, id0 = gpu_ids(r, cam)
    check("A5 census", "the marker is drawn with --helpers", mask_gpu(ids, table, id0, f"{PLACE}.marker").any())
    drawn = sum((c.get("drawn") or {}).values())
    check("A5 census", "instances drawn in the frame are counted by kind", drawn >= 10, f"{c.get('drawn')}")


def centroid(d, cam, pid):
    img, r = shot(d, cam)
    ids, table, id0 = gpu_ids(r, cam)
    ys, xs = np.nonzero(mask_gpu(ids, table, id0, pid))
    return (float(xs.mean()), float(ys.mean())) if len(xs) else None, r


def freshness(d, root, check, sess):
    """A.6: a change to the place files, a commit, an undo and a restore all show at the next look, no restart."""
    from tools.places.seat import PLACES
    pdir = PLACES / PLACE
    git = lambda *a: subprocess.run(["git", "-C", str(pdir.parent), *a], capture_output=True, text=True)  # noqa: E731
    git("init", "-q")
    git("add", "-A")
    git("-c", "user.name=look truth", "-c", "user.email=truth@localhost", "commit", "-qm", "golden scene")
    cam = geom.frame([0, 0, 0], [3500, 2500, 600], "s", "top", 768, 576) | {"far": 2e5}
    verbs.run(d, PLACE, sess, "at", [f"{PLACE}.house", "--plain", "--once"])
    drew0 = dict(d.drew)
    a, _ = centroid(d, cam, f"{PLACE}.house")
    refs = pdir / "spaces" / "exterior" / "refs.jsonl"
    rows = [json.loads(x) for x in refs.read_text().splitlines()]
    for row in rows:
        if row["id"] in (f"{PLACE}.house",):
            row["pos"][0] += 500
    refs.write_text("".join(json.dumps(r) + "\n" for r in rows))
    d.open(PLACE)
    b, _ = centroid(d, cam, f"{PLACE}.house")
    sc = d.scene(PLACE, [])
    want = geom.project(cam, [[1500, 1000, 600]])[0][:2] - geom.project(cam, [[1000, 1000, 600]])[0][:2]
    moved = None if a is None or b is None else np.subtract(b, a)
    check("A6 freshness", "a row moved in the files is drawn moved at the next look", moved is not None and abs(moved[0] - want[0]) <= 3
          and abs(moved[1] - want[1]) <= 3, f"moved {moved}, should move {want}")
    check("A6 freshness", "the numbers read the same state", abs(sc.by_id[f"{PLACE}.house"]["m"][0][3] - 1500) < 0.01)
    check("A6 freshness", "the answer names the state it drew (working tree)", d.drew["files"] != drew0["files"] and d.drew["working_tree"],
          f"{drew0} -> {d.drew}")
    git("add", "-A")
    git("-c", "user.name=look truth", "-c", "user.email=truth@localhost", "commit", "-qm", "house moved")
    d.open(PLACE)
    check("A6 freshness", "a commit is a new state", d.drew["commit"] != drew0["commit"] and not d.drew["working_tree"], f"{d.drew}")
    # an edit by hand: delete, then undo, then restore a snapshot
    verbs.run(d, PLACE, sess, "snapshot", ["before"])
    verbs.run(d, PLACE, sess, "delete", [f"{PLACE}.house"])
    verbs.view(d, PLACE, sess["strokes"], "at", [f"{PLACE}.deck", "--plain", "--once"], keep=True)
    gone, _ = centroid(d, cam, f"{PLACE}.house")
    verbs.run(d, PLACE, sess, "undo", [])
    verbs.view(d, PLACE, sess["strokes"], "at", [f"{PLACE}.deck", "--plain", "--once"], keep=True)
    back, _ = centroid(d, cam, f"{PLACE}.house")
    verbs.run(d, PLACE, sess, "delete", [f"{PLACE}.house"])
    verbs.view(d, PLACE, sess["strokes"], "at", [f"{PLACE}.deck", "--plain", "--once"], keep=True)
    verbs.run(d, PLACE, sess, "restore", ["before"])
    verbs.view(d, PLACE, sess["strokes"], "at", [f"{PLACE}.deck", "--plain", "--once"], keep=True)
    again, _ = centroid(d, cam, f"{PLACE}.house")
    check("A6 freshness", "a deleted piece is gone, back after undo and after restore", gone is None and back is not None and again is not None,
          f"deleted {gone}, undone {back}, restored {again}")
    # the drafts are this checkout's own; looks written together never share a file
    own = data_out() / "bundles" / f"draft.{PLACE}"
    check("A6 freshness", "the draft bundle is this daemon's own", own.exists() and not (Path(d.shared_out) / "bundles" / f"draft.{PLACE}").exists(),
          f"{own}")
    names = {verbs._out(PLACE, "same") for _ in range(50)}
    check("A6 freshness", "looks in the same second never share a file", len(names) == 50, f"{len(names)} names for 50")
    check("A6 freshness", "every answer says which state it drew", "drew" in d.handle({"place": PLACE, "verb": "status", "args": []}))


def rooms(d, root, check, sess):
    """A.8: a room draws all its pieces."""
    sc = d.scene(PLACE, sess["strokes"], "fx_room")
    res = verbs.run(d, PLACE, sess, "in", ["fx_room", "overview", "--plain"])
    c = res.get("census") or {}
    check("A8 rooms", "a room draws all its pieces", len(sc.pieces) == len(FX.ROOM) and c.get("sent") == len(FX.ROOM)
          and c.get("loaded") == len(FX.ROOM), f"scene {len(sc.pieces)}, page {c}", png=res.get("png"))
