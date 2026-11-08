"""Roads and border lines traced off the base map into centreline polylines, in map px (sub-pixel).

What the map draws: a medium solid red-orange line is a major road, the same line dashed is a minor road or path,
a thick bright-red dash-dot line is the province border (it runs out over the sea around Aphon Isle), thick navy
dash-dot lines are region borders. Roads run under water (rivers, bays: bridges, causeways, fords), under the
culture squares (which tint them), under glyphs and labels.

How it works:
1. Ink. The local background is an 11 px median of the map. A pixel is road ink when it is the road colour
   (204,108,107) laid over its background at some opacity: the opacity of the fit is >= 0.35 and the residual
   off that blend line is small. That reads a road on plain land, on the pale grid bands and under a tinted
   square alike. Border ink is read by colour: bright red with no green (province), navy (region). Road ink
   is dropped within 2 px of border ink, inside glyph discs (symbols.json), next to dark label text, and on
   steps of the background (square edges, shores), where the median fit is unreliable.
2. Lines. The ink is dilated by 3 px, which closes a dash's gap, and thinned to a one-pixel skeleton; short
   spurs are pruned.
3. Bridges. Each loose end looks ahead along its own direction (within 30 degrees) for the nearest other line
   or loose end; it is joined by a straight bridge when the gap is short (<= 22 px) or mostly crosses what
   hides a road (water, a glyph disc, a label, a square's edge), up to 90 px. Ends then join again.
4. Graph. The skeleton is cut into edges between nodes (junctions and ends). Every end or junction within a
   place glyph's snap radius (14 px, or the glyph's half-size + 6) becomes that place's node, and the edge runs
   on to the glyph centre.
5. Class. Along each edge the ink is sampled on the skeleton: a solid road has no breaks; a dashed one breaks
   every ~11 px. A 40 px window's break count sets major or minor per pixel; an edge whose class changes part
   way is split there at a junction. Breaks inside bridges do not count.
6. Points. Each edge's pixel path is smoothed (Gaussian, sigma 1.5 px along the path) and resampled every 3 px.
7. Borders. Province and region ink are dilated by 4 px (closing dash-dot gaps), thinned, pruned, end-joined
   along their direction up to 40 px, and written as polylines.

Outputs: `out/newworld/roads.json` (nodes, edges), `out/newworld/borders.json` (province, region parts),
`out/newworld/roads_check/` (overlay crops and `stats.json`: coverage, dead ends, lengths).

    python3 -m tools.newworld.roads
"""
from __future__ import annotations

import json
import math

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

from tools.newworld import frame as f

ROAD_RGB = (204, 108, 107)
LAND_RGB = (222, 199, 176)
CHECK = f.OUT / "roads_check"
SNAP_PX = 14
BRIDGE_SHORT = 22
BRIDGE_LONG = 90
BRIDGE_ANGLE = 30.0
SPUR_PX = 8
STEP_PX = 3.0
MARGIN_PX = 75          # the frame's rulers
END_TO_GLYPH = 22
TOUCH_PX = 10           # a loose end this close to another line joins it whatever its direction
GLYPH_REACH = 60        # a loose end reaches on to a glyph this far ahead
M_PER_PX = f.UNITS_PER_PX / f.UNITS_PER_METRE

N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


# ---------------------------------------------------------------- ink

def background(a: np.ndarray, size: int = 11) -> np.ndarray:
    return np.stack([ndi.median_filter(a[..., c], size=size) for c in range(3)], -1)


def blend_fit(a: np.ndarray, bg: np.ndarray, rgb=ROAD_RGB, under=LAND_RGB) -> tuple[np.ndarray, np.ndarray]:
    """Each pixel's step off its background read as the line colour `rgb` drawn on `under` (plain land) and
    then dimmed by whatever lies over both (a culture square, a pale band): (strength 0..1, residual)."""
    v = np.asarray(rgb, np.float32) - np.asarray(under, np.float32)
    d = a - bg
    al = (d * v).sum(-1) / float((v * v).sum())
    res = np.linalg.norm(d - al[..., None] * v, axis=-1)
    return al, res


def border_cores(a: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    province = (g < 75) & (r > 140) & (b < 70) & (r - g > 100)
    region = (r < 60) & (g < 60) & (b > 80)
    return province, region


def disc_mask(shape, centres) -> np.ndarray:
    m = np.zeros(shape, bool)
    yy, xx = np.ogrid[:shape[0], :shape[1]]
    for x, y, rad in centres:
        x0, x1 = int(max(0, x - rad - 1)), int(min(shape[1], x + rad + 2))
        y0, y1 = int(max(0, y - rad - 1)), int(min(shape[0], y + rad + 2))
        m[y0:y1, x0:x1] |= (xx[:, x0:x1] - x) ** 2 + (yy[y0:y1] - y) ** 2 <= rad * rad
    return m


def ruler_labels(shape) -> np.ndarray:
    """The red coordinate labels printed where a 10-cell band crosses another ("10.60"), and the frame margin."""
    m = np.zeros(shape, bool)
    xs, ys = f.cell_range()
    for cx in xs:
        for cy in ys:
            if cx % 10 == 0 and cy % 10 == 0:
                left, top, right, bottom = f.cell_px_box(cx, cy)
                m[max(0, top + 10):max(0, bottom - 10), max(0, left - 1):max(0, right + 1)] = True
    e = MARGIN_PX
    m[:e], m[-e:], m[:, :e], m[:, -e:] = True, True, True, True
    return m


def square_mask(shape, symbols, unlike_road: bool = False) -> np.ndarray:
    """The culture squares behind settlements (1 or 2 cells a side, centred on the glyph), edges included;
    with `unlike_road`, only the squares whose tint is far from the road colour (a road reads on them)."""
    m = np.zeros(shape, bool)
    for s in symbols:
        tint = s.get("tint_rgb")
        if unlike_road and (not tint or math.dist(tint, ROAD_RGB) < 50):
            continue
        if s.get("square_cells"):
            h = 20 * s["square_cells"] + 2
            x, y = int(round(s["px"])), int(round(s["py"]))
            m[max(0, y - h):y + h, max(0, x - h):x + h] = True
    return m


def glyph_radius(s: dict) -> float:
    return (s.get("glyph_px") or 16) / 2 + 2


def snap_radius(s: dict) -> float:
    return max(SNAP_PX, (s.get("glyph_px") or 16) / 2 + 6)


def road_ink(a, bg, province, region, glyphs, water, squares):
    """(ink, hidden): road-coloured pixels, and the pixels where a road may be hidden (unreadable)."""
    al, res = blend_fit(a, bg)
    step_len = np.linalg.norm(a - bg, axis=-1)
    along = np.sqrt(np.maximum(step_len ** 2 - res ** 2, 0)) / np.maximum(step_len, 1e-3)
    ink = (al > 0.15) & (along >= 0.95) & (res < 10)
    lum = a.mean(-1)
    text = ndi.binary_dilation(lum < 90, iterations=2) & ~region
    gy = ndi.sobel(bg.mean(-1), 0)
    gx = ndi.sobel(bg.mean(-1), 1)
    step = ndi.binary_dilation(np.hypot(gx, gy) > 60, iterations=1)
    lines = ndi.binary_dilation(province | region, iterations=2)
    ink &= ~(lines | glyphs | text | step | water)
    # over a culture square (and on a bridge over water) the road is drawn on top, in its own colour
    on_top = (np.linalg.norm(a - np.asarray(ROAD_RGB, np.float32), axis=-1) < 40) & (np.linalg.norm(a - bg, axis=-1) > 25)
    ink |= on_top & (squares | water) & ~(lines | glyphs | step | text)

    lab, n_ = ndi.label(ink, np.ones((3, 3)))
    sizes = ndi.sum(ink, lab, range(1, n_ + 1))
    ink &= np.isin(lab, np.nonzero(sizes >= 4)[0] + 1)
    return ink, text | step | glyphs | water


# ---------------------------------------------------------------- skeleton graph

def skeleton(mask: np.ndarray) -> np.ndarray:
    from skimage.morphology import skeletonize
    return skeletonize(mask)


def nbr_count(sk: np.ndarray) -> np.ndarray:
    k = np.ones((3, 3), int)
    k[1, 1] = 0
    return ndi.convolve(sk.astype(int), k, mode="constant") * sk


def trace(sk: np.ndarray) -> tuple[list, list]:
    """Cut a skeleton into nodes and pixel paths. Returns (nodes [(y, x)], edges [(n0, n1, [(y, x), ...])])."""
    sk = sk.copy()
    h, w = sk.shape
    cnt = nbr_count(sk)
    nodepix = sk & (cnt != 2)
    lab, nn = ndi.label(nodepix, np.ones((3, 3)))
    nodes = [tuple(map(float, c)) for c in ndi.center_of_mass(nodepix, lab, range(1, nn + 1))] if nn else []
    edges = []
    visited = np.zeros_like(sk)

    def nbrs(y, x):
        for dy, dx in N8:
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w and sk[yy, xx]:
                yield yy, xx

    def walk(start_node, y0, x0, y, x):
        path = [(y0, x0), (y, x)]
        py, px_ = y0, x0
        while True:
            if lab[y, x]:
                return lab[y, x] - 1, path
            visited[y, x] = True
            nxt = [p for p in nbrs(y, x) if p != (py, px_) and not (visited[p] and not lab[p])
                   and p not in path[-3:]]
            # prefer 4-neighbours to avoid corner shortcuts skipping a node
            nodes_n = [p for p in nxt if lab[p] and lab[p] - 1 != start_node or (lab[p] and len(path) > 2)]
            if nodes_n:
                p = nodes_n[0]
            elif nxt:
                p = min(nxt, key=lambda q: abs(q[0] - y) + abs(q[1] - x))
            else:
                return None, path
            py, px_ = y, x
            y, x = p
            path.append((y, x))

    for ys, xs in zip(*np.nonzero(nodepix)):
        ni = lab[ys, xs] - 1
        for y, x in nbrs(ys, xs):
            if lab[y, x]:
                continue
            if visited[y, x]:
                continue
            end, path = walk(ni, ys, xs, y, x)
            if end is None:
                end = len(nodes)
                nodes.append(tuple(map(float, path[-1])))
            edges.append((ni, end, path))
    # loops with no node
    rest = sk & ~visited & ~nodepix
    while rest.any():
        y, x = map(int, np.argwhere(rest)[0])
        ni = len(nodes)
        nodes.append((float(y), float(x)))
        lab[y, x] = ni + 1
        nb = list(nbrs(y, x))
        visited[y, x] = True
        if nb:
            _, path = walk(ni, y, x, *nb[0])
            edges.append((ni, ni, path))
        rest = sk & ~visited & ~(lab > 0)
    return nodes, edges


def prune(sk: np.ndarray, spur: int = SPUR_PX, rounds: int = 3) -> np.ndarray:
    """Remove side spurs shorter than `spur` px (an end edge whose other node is a junction)."""
    sk = sk.copy()
    for _ in range(rounds):
        nodes, edges = trace(sk)
        deg = np.zeros(len(nodes), int)
        for a_, b_, _ in edges:
            deg[a_] += 1
            deg[b_] += 1
        changed = False
        for a_, b_, path in edges:
            if len(path) < spur and ((deg[a_] == 1) != (deg[b_] == 1)):
                end_first = deg[a_] == 1
                pts = path[:-1] if end_first else path[1:]
                for y, x in pts:
                    sk[y, x] = False
                changed = True
        if not changed:
            break
        from skimage.morphology import skeletonize
        sk = skeletonize(sk)
    return sk


def end_tangents(sk: np.ndarray, back: int = 10) -> list[tuple[int, int, float, float]]:
    """Loose ends of a skeleton with the unit direction pointing out of the line: (y, x, dy, dx)."""
    nodes, edges = trace(sk)
    deg = np.zeros(len(nodes), int)
    for a_, b_, _ in edges:
        deg[a_] += 1
        deg[b_] += 1
    out = []
    for a_, b_, path in edges:
        for ni, p in ((a_, path), (b_, path[::-1])):
            if deg[ni] == 1 and len(p) >= 3:
                y0, x0 = p[0]
                y1, x1 = p[min(back, len(p) - 1)]
                d = math.hypot(y0 - y1, x0 - x1)
                if d > 0:
                    out.append((y0, x0, (y0 - y1) / d, (x0 - x1) / d))
    return out


def along_skeleton(sk: np.ndarray, y: int, x: int, steps: int) -> np.ndarray:
    """Skeleton pixels within `steps` 8-connected steps of (y, x), as a full-size mask."""
    seen = np.zeros(sk.shape, bool)
    seen[y, x] = True
    front = [(y, x)]
    h, w = sk.shape
    for _ in range(steps):
        nxt = []
        for cy, cx in front:
            for dy, dx in N8:
                yy, xx = cy + dy, cx + dx
                if 0 <= yy < h and 0 <= xx < w and sk[yy, xx] and not seen[yy, xx]:
                    seen[yy, xx] = True
                    nxt.append((yy, xx))
        front = nxt
    return seen


def line_px(y0, x0, y1, x1) -> list[tuple[int, int]]:
    n = int(max(abs(y1 - y0), abs(x1 - x0))) + 1
    return [(int(round(y0 + (y1 - y0) * t / max(n - 1, 1))), int(round(x0 + (x1 - x0) * t / max(n - 1, 1))))
            for t in range(n)]


def bridge(sk: np.ndarray, hidden: np.ndarray, short: float = BRIDGE_SHORT, long: float = BRIDGE_LONG,
           angle: float = BRIDGE_ANGLE, keep_out: np.ndarray | None = None,
           places: list | None = None, settlements: list | None = None) -> tuple[np.ndarray, list]:
    """Join loose ends across gaps: a touching gap (TOUCH_PX) to any line, a short gap to any line ahead, a long
    one only to a loose end facing back and only when at least 40% of it crosses hidden ground.
    A loose end within GLYPH_REACH px of a settlement glyph centre ahead of it (within 35 degrees, over mostly hidden
    ground) runs on to it.
    Returns (skeleton with bridges drawn, bridges [(y0, x0, y1, x1)])."""
    sk = sk.copy()
    ends = end_tangents(sk)
    pts = np.argwhere(sk)
    cos_max = math.cos(math.radians(angle))
    bridges = []
    used = set()
    endset = {(y, x) for y, x, _, _ in ends}
    enddir = {(int(y), int(x)): (dy, dx) for y, x, dy, dx in ends}
    placeset = {(int(gy), int(gx)) for gy, gx in settlements or ()}
    cands = []
    for y, x, dy, dx in ends:
        if any(math.hypot(gy - y, gx - x) <= 3 for gy, gx in places or ()):
            continue          # an end that has reached a glyph centre is home
        v = pts - (y, x)
        dist = np.hypot(v[:, 0], v[:, 1])
        ok = (dist > 2) & (dist <= long)
        if not ok.any():
            continue
        cosang = (v[:, 0] * dy + v[:, 1] * dx) / np.maximum(dist, 1e-6)
        # two loose ends facing each other across a short gap may each be off line by up to 60 degrees
        facing = np.zeros(len(pts), bool)
        for j in np.nonzero((dist <= short) & (cosang >= 0.5))[0]:
            od = enddir.get((int(pts[j][0]), int(pts[j][1])))
            if od is not None and -(v[j, 0] * od[0] + v[j, 1] * od[1]) / dist[j] >= 0.5:
                facing[j] = True
        ok &= (cosang >= cos_max) | facing | (dist <= TOUCH_PX)
        # never back into its own line: nothing within 40 px of the end along the skeleton
        near = along_skeleton(sk, y, x, 40)
        ok &= ~near[pts[:, 0], pts[:, 1]]
        for i in np.nonzero(ok)[0]:
            ty, tx = pts[i]
            seg = line_px(y, x, ty, tx)[1:-1]
            if dist[i] > short:
                # a long gap only joins two loose ends that face each other
                od = enddir.get((int(ty), int(tx)))
                back = -(v[i, 0] * od[0] + v[i, 1] * od[1]) / dist[i] if od is not None else -1
                lo, tot = (0.3, 1.1) if dist[i] <= 45 else (0.8, 1.7)   # wide water: nearly straight on
                if min(back, cosang[i]) < lo or back + cosang[i] < tot:
                    continue
                if not seg:
                    continue
                hid = np.mean([hidden[p] for p in seg])
                if hid < 0.4:
                    continue
            if keep_out is not None and any(keep_out[p] for p in seg):
                continue
            # a target that is a loose end facing back is better than a mid-line point
            bonus = 0.6 if (ty, tx) in endset else 1.0
            cands.append((dist[i] * (2 - cosang[i]) * bonus, y, x, int(ty), int(tx)))
        for gy, gx in settlements or ():
            d = math.hypot(gy - y, gx - x)
            cg = ((gy - y) * dy + (gx - x) * dx) / d if d else 0
            if (0 < d <= GLYPH_REACH and cg >= math.cos(math.radians(35))
                    and hidden_share(hidden, y, x, gy, gx) >= 0.6):
                seg = line_px(y, x, gy, gx)[1:-1]
                if keep_out is None or not any(keep_out[p] for p in seg):
                    cands.append((d * (2 - cg) * 0.8, y, x, int(gy), int(gx)))
    cands.sort()
    for _, y, x, ty, tx in cands:
        if (y, x) in used:
            continue
        if (ty, tx) in endset and (ty, tx) in used and (ty, tx) not in placeset:
            continue
        used.add((y, x))
        if (ty, tx) in endset:
            used.add((ty, tx))
        for p in line_px(y, x, ty, tx):
            sk[p] = True
        bridges.append((y, x, ty, tx))
    return sk, bridges


def hidden_share(hidden: np.ndarray, y, x, ty, tx) -> float:
    seg = line_px(y, x, ty, tx)[1:-1]
    return float(np.mean([hidden[p] for p in seg])) if seg else 1.0


def reach_glyphs(sk: np.ndarray, places: list, hidden: np.ndarray,
                 reach: float = END_TO_GLYPH) -> tuple[np.ndarray, list]:
    """A loose end left within `reach` px of a place glyph centre (any direction) runs on to it, when the way
    there is mostly hidden ground (the glyph, its square, water, a label)."""
    sk = sk.copy()
    out = []
    for y, x, _, _ in end_tangents(sk):
        best = min(places, key=lambda g: math.hypot(g[0] - y, g[1] - x), default=None)
        if (best is not None and 0 < math.hypot(best[0] - y, best[1] - x) <= reach
                and hidden_share(hidden, y, x, *best) >= 0.6):
            for p in line_px(y, x, *best):
                sk[p] = True
            out.append((y, x, *best))
    return sk, out


# ---------------------------------------------------------------- class and points

def break_count(ink_on_path: np.ndarray, skip: np.ndarray, win: int = 40) -> np.ndarray:
    """Per path pixel: number of ink breaks (an inked pixel followed by an un-inked one) in a window,
    not counting pixels marked `skip` (bridges, hidden ground)."""
    n = len(ink_on_path)
    starts = np.zeros(n)
    for i in range(1, n):
        if ink_on_path[i - 1] and not ink_on_path[i] and not skip[i] and not skip[i - 1]:
            starts[i] = 1
    valid = (~skip).astype(float)
    k = np.ones(win)
    br = np.convolve(starts, k, "same")
    cov = np.convolve(valid, k, "same")
    return br * win / np.maximum(cov, 1)


def classify(ink_on_path: np.ndarray, skip: np.ndarray, win: int = 40, minrun: int = 25) -> np.ndarray:
    """Per path pixel True = minor (dashed). A solid road has no breaks; a dashed one ~3.5 per 40 px."""
    br = break_count(ink_on_path, skip, win)
    minor = br >= 1.5
    # pixels with no readable ink around take the nearest readable class
    valid = np.convolve((~skip).astype(float), np.ones(win), "same") >= win / 4
    if valid.any() and not valid.all():
        idx = np.nonzero(valid)[0]
        near = idx[np.abs(np.arange(len(minor))[:, None] - idx[None, :]).argmin(1)]
        minor = minor[near]
    elif not valid.any():
        minor[:] = minor.mean() >= 0.5 if len(minor) else False
    # merge short runs into neighbours
    for _ in range(3):
        runs = []
        s = 0
        for i in range(1, len(minor) + 1):
            if i == len(minor) or minor[i] != minor[s]:
                runs.append((s, i))
                s = i
        if len(runs) <= 1:
            break
        changed = False
        for s, e in runs:
            if e - s < minrun:
                minor[s:e] = ~minor[s]
                changed = True
                break
        if not changed:
            break
    return minor


def smooth_resample(path_yx: list, sigma: float = 1.5, step: float = STEP_PX,
                    keep_ends: bool = True) -> list[list[float]]:
    """A pixel path (y, x) to [[px, py], ...] in map px (pixel centres at +0.5), smoothed, every `step` px."""
    p = np.asarray(path_yx, float)[:, ::-1] + 0.5
    if len(p) >= 5:
        q = np.stack([ndi.gaussian_filter1d(p[:, i], sigma, mode="nearest") for i in range(2)], -1)
        if keep_ends:
            q[0], q[-1] = p[0], p[-1]
    else:
        q = p
    seg = np.hypot(*(np.diff(q, axis=0).T))
    s = np.concatenate([[0], np.cumsum(seg)])
    if s[-1] == 0:
        return [[round(q[0, 0], 2), round(q[0, 1], 2)]]
    n = max(1, int(round(s[-1] / step)))
    t = np.linspace(0, s[-1], n + 1)
    out = np.stack([np.interp(t, s, q[:, 0]), np.interp(t, s, q[:, 1])], -1)
    return [[round(float(x), 2), round(float(y), 2)] for x, y in out]


def refine(pts: list, weight: np.ndarray, reach: float = 4.0, passes: int = 2) -> list:
    """Move each inner point across the line onto the ink's weighted centre (sub-pixel), where there is ink."""
    p = np.asarray(pts, float)
    if len(p) < 3:
        return pts
    offs = np.arange(-reach, reach + 0.01, 0.5)
    for _ in range(passes):
        t = np.gradient(p, axis=0)
        t /= np.maximum(np.hypot(t[:, 0], t[:, 1]), 1e-6)[:, None]
        nrm = np.stack([-t[:, 1], t[:, 0]], -1)
        xs = p[:, 0, None] + nrm[:, 0, None] * offs[None] - 0.5
        ys = p[:, 1, None] + nrm[:, 1, None] * offs[None] - 0.5
        w = ndi.map_coordinates(weight, [ys.ravel(), xs.ravel()], order=1, mode="constant").reshape(xs.shape)
        tot = w.sum(1)
        shift = np.where(tot > 1.0, (w * offs[None]).sum(1) / np.maximum(tot, 1e-6), 0.0)
        shift[0] = shift[-1] = 0
        p = p + nrm * shift[:, None]
        if len(p) >= 5:
            q = np.stack([ndi.gaussian_filter1d(p[:, i], 0.8, mode="nearest") for i in range(2)], -1)
            q[0], q[-1] = p[0], p[-1]
            p = q
    return [[round(float(x), 2), round(float(y), 2)] for x, y in p]


def polyline_length(pts) -> float:
    p = np.asarray(pts, float)
    return float(np.hypot(*(np.diff(p, axis=0).T)).sum()) if len(p) > 1 else 0.0


# ---------------------------------------------------------------- road graph

def snap_places(nodes_xy: list, symbols: list, degrees=None) -> list:
    """For each node (px, py): the index of the place glyph it snaps to, or None. An end snaps within the
    glyph's snap radius or on (or within 10 px of) its culture square (the road has reached the settlement); a junction
    only inside the glyph itself (a road passing beside a glyph is not pulled)."""
    out = []
    for k, (x, y) in enumerate(nodes_xy):
        best, bd = None, 1e9
        end = degrees is None or degrees[k] <= 1
        for i, s in enumerate(symbols):
            d = math.hypot(s["px"] - x, s["py"] - y)
            in_square = end and s.get("square_cells") and max(abs(s["px"] - x), abs(s["py"] - y)) <= (
                20 * s["square_cells"] + 12)
            if (d <= (snap_radius(s) if end else glyph_radius(s)) or in_square) and d < bd:
                best, bd = i, d
        out.append(best)
    return out


def inherit_class(pieces: list, readable: list) -> list:
    """A piece with no readable ink (a bridge, a run under a glyph) takes the class most of its neighbours
    at either end have; a minor road reaching a major one keeps its own class."""
    pieces = [list(p) for p in pieces]
    known = list(readable)
    for _ in range(10):
        changed = False
        for i, p in enumerate(pieces):
            if known[i]:
                continue
            votes = [pieces[j][3] for j in range(len(pieces)) if j != i and known[j]
                     and ({pieces[j][0], pieces[j][1]} & {p[0], p[1]})]
            if votes:
                p[3] = sum(votes) * 2 >= len(votes)
                known[i] = True
                changed = True
        if not changed:
            break
    return [tuple(p) for p in pieces]


def split_at_places(nodes: list, edges: list, symbols: list) -> tuple[list, list]:
    """Cut an edge where it passes over a place glyph (through the glyph itself) that is not one of its ends."""
    nodes = list(nodes)
    out = []
    todo = list(edges)
    while todo:
        a_, b_, path = todo.pop()
        p = np.asarray(path, float)
        cut = None
        for s in symbols:
            d = np.hypot(p[:, 1] + 0.5 - s["px"], p[:, 0] + 0.5 - s["py"])
            i = int(d.argmin())
            if d[i] > glyph_radius(s) or i < 3 or i > len(path) - 4:
                continue
            if any(math.hypot(nodes[n][1] + 0.5 - s["px"], nodes[n][0] + 0.5 - s["py"]) <= snap_radius(s)
                   for n in (a_, b_)):
                continue
            cut = i
            break
        if cut is None:
            out.append((a_, b_, path))
            continue
        nid = len(nodes)
        nodes.append(tuple(map(float, path[cut])))
        todo += [(a_, nid, path[:cut + 1]), (nid, b_, path[cut:])]
    return nodes, out


def build_roads(sk, ink, skipmask, symbols, weight=None):
    nodes, edges = trace(sk)
    nodes, edges = split_at_places(nodes, edges, symbols)
    # split each edge by class
    pieces = []          # (node_a, node_b, path, minor)
    readable = []        # whether the piece's class was read off ink (else it is taken from its neighbours)
    extra_nodes = list(nodes)
    for a_, b_, path in edges:
        ys = np.array([p[0] for p in path])
        xs = np.array([p[1] for p in path])
        skip = skipmask[ys, xs]
        cls = classify(ink[ys, xs], skip)
        s = 0
        cur_a = a_
        for i in range(1, len(path) + 1):
            if i == len(path) or cls[i] != cls[s]:
                readable.append(float((~skip[s:i]).mean()) >= 0.3 and i - s >= 12 or (~skip[s:i]).sum() >= 30)
                if i == len(path):
                    pieces.append((cur_a, b_, path[s:], bool(cls[s])))
                else:
                    nid = len(extra_nodes)
                    extra_nodes.append(tuple(map(float, path[i])))
                    pieces.append((cur_a, nid, path[s:i + 1], bool(cls[s])))
                    cur_a = nid
                    s = i
    pieces = inherit_class(pieces, readable)
    deg = np.zeros(len(extra_nodes), int)
    for a_, b_, _, _ in pieces:
        deg[a_] += 1
        deg[b_] += 1
    xy = [(x + 0.5, y + 0.5) for y, x in extra_nodes]
    place = snap_places(xy, symbols, deg)
    # node ids: places merge by glyph
    out_nodes = []
    key_to_id = {}
    for i, (x, y) in enumerate(xy):
        if deg[i] == 0:
            continue
        if place[i] is not None:
            k = ("p", place[i])
            if k not in key_to_id:
                s = symbols[place[i]]
                key_to_id[k] = len(out_nodes)
                out_nodes.append({"id": len(out_nodes), "kind": "place", "place_index": place[i],
                                  "px": round(s["px"], 2), "py": round(s["py"], 2)})
        else:
            k = ("n", i)
            key_to_id[k] = len(out_nodes)
            out_nodes.append({"id": len(out_nodes), "kind": "junction" if deg[i] >= 2 else "end",
                              "place_index": None, "px": round(x, 2), "py": round(y, 2)})
    nid = [key_to_id.get(("p", place[i])) if place[i] is not None else key_to_id.get(("n", i))
           for i in range(len(xy))]
    out_edges = []
    for a_, b_, path, minor in pieces:
        na, nb = nid[a_], nid[b_]
        pts = smooth_resample(path)
        if weight is not None:
            pts = refine(pts, weight)
        if na == nb and polyline_length(pts) < 2 * SNAP_PX:
            continue          # a stub inside one glyph
        for ni, at in ((na, 0), (nb, -1)):
            n = out_nodes[ni]
            if n["kind"] == "place":
                # trim the points inside the glyph and run on to its centre
                c = np.array([n["px"], n["py"]])
                r = snap_radius(symbols[n["place_index"]])
                arr = pts if at == 0 else pts[::-1]
                while len(arr) > 2 and math.hypot(arr[1][0] - c[0], arr[1][1] - c[1]) < r * 0.6:
                    arr = arr[1:]
                arr = [[n["px"], n["py"]]] + arr[1:] if len(arr) > 1 else [[n["px"], n["py"]]] + arr
                arr = densify(arr)
                pts = arr if at == 0 else arr[::-1]
            else:
                if at == 0:
                    pts[0] = [n["px"], n["py"]]
                else:
                    pts[-1] = [n["px"], n["py"]]
        out_edges.append({"id": len(out_edges), "class": "minor" if minor else "major",
                          "from": na, "to": nb, "points": pts})
    # degree recount: a junction whose edges all went to one glyph etc.
    deg2 = np.zeros(len(out_nodes), int)
    for e in out_edges:
        deg2[e["from"]] += 1
        deg2[e["to"]] += 1
    for n in out_nodes:
        if n["kind"] != "place":
            n["kind"] = "junction" if deg2[n["id"]] >= 2 else "end"
    return out_nodes, out_edges


def densify(pts, step: float = STEP_PX):
    """Insert points so that no two consecutive points are more than `step` px apart."""
    out = [list(pts[0])]
    for p in pts[1:]:
        q = out[-1]
        d = math.hypot(p[0] - q[0], p[1] - q[1])
        k = int(math.ceil(d / step))
        for j in range(1, k):
            t = j / k
            out.append([round(q[0] + (p[0] - q[0]) * t, 2), round(q[1] + (p[1] - q[1]) * t, 2)])
        out.append(list(p))
    return out


# ---------------------------------------------------------------- borders

def border_lines(core: np.ndarray, glyphs: np.ndarray, dil: int = 4, min_len: int = 30) -> list:
    m = ndi.binary_dilation(core & ~glyphs, iterations=dil)
    sk = prune(skeleton(m), spur=12)
    sk, _ = bridge(sk, np.ones_like(sk), short=40, long=40, angle=35)
    sk = prune(skeleton(ndi.binary_dilation(sk, iterations=1)), spur=12)
    nodes, edges = trace(sk)
    out = []
    for _, _, path in edges:
        if len(path) >= min_len:
            out.append(smooth_resample(path, sigma=2.0))
    return out


# ---------------------------------------------------------------- run

def main() -> None:
    CHECK.mkdir(parents=True, exist_ok=True)
    a = np.asarray(Image.open(f.BASE_MAP).convert("RGB")).astype(np.float32)
    symbols = json.loads((f.OUT / "symbols.json").read_text())
    water = np.asarray(Image.open(f.OUT / "raster" / "water.png").convert("L")) > 127
    bg = background(a)
    province, region = border_cores(a)
    glyphs = disc_mask(a.shape[:2], [(s["px"], s["py"], glyph_radius(s)) for s in symbols])
    ruler = ruler_labels(a.shape[:2])
    province &= ~(ruler | glyphs)
    region &= ~ruler
    squares = square_mask(a.shape[:2], symbols)
    ink, hidden = road_ink(a, bg, province, region, glyphs, water, square_mask(a.shape[:2], symbols, True))
    ink &= ~ruler
    hidden = hidden | water | ruler | squares
    places = [(int(s["py"]), int(s["px"])) for s in symbols]
    settlements = [(int(s["py"]), int(s["px"])) for s in symbols if s["glyph"] == "settlement"]

    sk = prune(skeleton(ndi.binary_dilation(ink, iterations=3)))
    sk, br1 = bridge(sk, hidden, places=places, settlements=settlements)
    sk = prune(skeleton(ndi.binary_dilation(sk, iterations=1)))
    sk, br2 = bridge(sk, hidden, places=places, settlements=settlements)
    sk = prune(skeleton(ndi.binary_dilation(sk, iterations=1)))
    sk, br3 = reach_glyphs(sk, places, hidden)
    (CHECK / "bridges.json").write_text(json.dumps([[int(v) for v in b] for b in br1 + br2 + br3]))
    bridged = np.zeros_like(sk)
    for y0, x0, y1, x1 in br1 + br2 + br3:
        for p in line_px(y0, x0, y1, x1):
            bridged[p] = True
    bridged = ndi.binary_dilation(bridged, iterations=1)
    ink_near = ndi.binary_dilation(ink, iterations=1)
    skip = bridged | (hidden & ~ink_near)
    al, _ = blend_fit(a, bg)
    weight = np.clip(al, 0, 1) * ink_near
    nodes, edges = build_roads(sk, ink_near, skip, symbols, weight)
    (f.OUT / "roads.json").write_text(json.dumps({"nodes": nodes, "edges": edges}))

    borders = {"province": border_lines(province, glyphs), "region": border_lines(region, glyphs)}
    (f.OUT / "borders.json").write_text(json.dumps(borders))

    core = ink & ((al >= 0.35) | (np.linalg.norm(a - np.asarray(ROAD_RGB, np.float32), axis=-1) < 40))
    stats = check(a, ink, core, bridged | hidden, nodes, edges, borders, symbols)
    (CHECK / "stats.json").write_text(json.dumps(stats, indent=1))
    print(json.dumps({k: v for k, v in stats.items() if k != "dead_ends"}, indent=1))
    print("dead ends:", len(stats["dead_ends"]))


def raster_lines(shape, polylines) -> np.ndarray:
    im = Image.new("L", (shape[1], shape[0]), 0)
    d = ImageDraw.Draw(im)
    for pts in polylines:
        d.line([tuple(p) for p in pts], fill=255, width=1)
    return np.asarray(im) > 0


def check(a, ink, core, gapok, nodes, edges, borders, symbols) -> dict:
    """Coverage both ways, per class. `ink`: every road-ink pixel, faint fringes included; `core`: pixels at
    least 35% road colour (the line itself)."""
    shape = a.shape[:2]
    st = {"nodes": len(nodes), "edges": len(edges),
          "node_kinds": {k: sum(n["kind"] == k for n in nodes) for k in ("place", "junction", "end")}}
    for cls in ("major", "minor"):
        es = [e for e in edges if e["class"] == cls]
        st[f"{cls}_edges"] = len(es)
        st[f"{cls}_km"] = round(sum(polyline_length(e["points"]) for e in es) * M_PER_PX / 1000, 1)
    allline = raster_lines(shape, [e["points"] for e in edges])
    near = ndi.distance_transform_edt(~allline) <= 2.0
    st["ink_px"] = int(ink.sum())
    st["ink_covered"] = round(float((ink & near).sum() / max(ink.sum(), 1)), 4)
    # per class: ink pixels nearest to that class's lines
    for cls in ("major", "minor"):
        lc = raster_lines(shape, [e["points"] for e in edges if e["class"] == cls])
        lo = raster_lines(shape, [e["points"] for e in edges if e["class"] != cls])
        dc = ndi.distance_transform_edt(~lc)
        do = ndi.distance_transform_edt(~lo)
        mine = ink & (dc <= do)
        st[f"ink_covered_{cls}"] = round(float((mine & (dc <= 2)).sum() / max(mine.sum(), 1)), 4)
        mine = core & (dc <= do)
        st[f"core_covered_{cls}"] = round(float((mine & (dc <= 2)).sum() / max(mine.sum(), 1)), 4)
    inkd = ndi.distance_transform_edt(~ink) <= 2.0
    okd = inkd | ndi.binary_dilation(gapok, iterations=1)
    for cls in ("major", "minor"):
        pts = np.array([p for e in edges if e["class"] == cls for p in e["points"]])
        if len(pts):
            ix = np.clip(pts[:, 0].astype(int), 0, shape[1] - 1)
            iy = np.clip(pts[:, 1].astype(int), 0, shape[0] - 1)
            st[f"line_on_ink_{cls}"] = round(float(okd[iy, ix].mean()), 4)
            st[f"line_on_ink_only_{cls}"] = round(float(inkd[iy, ix].mean()), 4)
    st["dead_ends"] = [[n["px"], n["py"]] for n in nodes if n["kind"] == "end"]
    st["province_parts"] = len(borders["province"])
    st["region_parts"] = len(borders["region"])
    st["province_km"] = round(sum(polyline_length(p) for p in borders["province"]) * M_PER_PX / 1000, 1)
    st["region_km"] = round(sum(polyline_length(p) for p in borders["region"]) * M_PER_PX / 1000, 1)
    overlays(a, edges, nodes, borders)
    return st


def overlays(a, edges, nodes, borders, tile: int = 900) -> None:
    im = Image.fromarray(a.astype(np.uint8)).convert("RGB")
    im = Image.blend(im, Image.new("RGB", im.size, (255, 255, 255)), 0.35)
    d = ImageDraw.Draw(im)
    for pts in borders["province"]:
        d.line([tuple(p) for p in pts], fill=(255, 0, 255), width=1)
    for pts in borders["region"]:
        d.line([tuple(p) for p in pts], fill=(0, 200, 255), width=1)
    for e in edges:
        d.line([tuple(p) for p in e["points"]], fill=(0, 0, 0) if e["class"] == "major" else (0, 150, 0), width=1)
    for n in nodes:
        c = {"place": (0, 0, 255), "junction": (255, 160, 0), "end": (255, 0, 0)}[n["kind"]]
        r = 3 if n["kind"] != "end" else 5
        d.ellipse((n["px"] - r, n["py"] - r, n["px"] + r, n["py"] + r), outline=c, width=2)
    for old in CHECK.glob("crop_*.png"):
        old.unlink()
    W, H = im.size
    for y in range(0, H, tile):
        for x in range(0, W, tile):
            im.crop((x, y, min(W, x + tile), min(H, y + tile))).save(CHECK / f"crop_{x:04d}_{y:04d}.png")
    im.resize((W // 3, H // 3)).save(CHECK / "overview.png")


if __name__ == "__main__":
    main()
