"""Labels on a look: structure ids where they stand (set-of-mark), a person's height at the subject, a north arrow
and the side seen from, the ground grid and its spacing, red outlines on faulted pieces; for a section, the ground
profile, the water, a height scale and each crossed piece's height over the ground. Contact sheets."""
from __future__ import annotations

import io
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from tools.places.look import geom

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
RED = (230, 30, 30, 255)


def _grid_z(scene, x, y) -> float:
    """The grid's height: the ground's outside, a room's floor level inside (flat, so it reads as a plan)."""
    if hasattr(scene.ground, "floor"):
        return scene.ground.floor
    return scene.ground.height(x, y) or 0.0


def font(size: int, bold: bool = False):
    try:
        return ImageFont.truetype(BOLD if bold else FONT, size)
    except OSError:
        return ImageFont.load_default()


def from_data_url(u: str) -> Image.Image:
    import base64
    return Image.open(io.BytesIO(base64.b64decode(u.split(",", 1)[1]))).convert("RGBA")


BASE_W = 768   # the width every pixel size below was drawn for; a drawing scales by width / BASE_W


def unit(w: float) -> float:
    """How much to scale a size written for a 768-wide image to one `w` wide."""
    return w / BASE_W


def tag(d: ImageDraw.ImageDraw, xy, text: str, fill=(255, 255, 255, 235), ink=(0, 0, 0, 255), size: int = 13, bold=True,
        k: float | None = None):
    """A label; its text, padding and outline scale with the image's width (`k`: the panel's, for a sheet of panels)."""
    k = unit(d.im.size[0]) if k is None else k
    f = font(max(8, round(size * k)), bold)
    x, y = xy
    b = d.textbbox((0, 0), text, font=f)
    px, py = round(3 * k), round(2 * k)
    w, h = b[2] - b[0] + 2 * px, b[3] - b[1] + 2 * py
    m = max(2, round(2 * k))
    x = min(max(m, x - w / 2), d.im.size[0] - w - m)
    y = min(max(m, y - h), d.im.size[1] - h - m)
    d.rectangle([x, y, x + w, y + h], fill=fill, outline=(0, 0, 0, 255), width=max(1, round(k)))
    d.text((x + px, y + py - b[1]), text, font=f, fill=ink)
    return [x, y, x + w, y + h]


def _inside(p, w, h, pad=0):
    return p[2] > 0 and -pad <= p[0] <= w + pad and -pad <= p[1] <= h + pad


RING = (255, 140, 0, 235)


def ring_points(ring: dict, n: int = 96) -> list[tuple[float, float]]:
    """The footprint ring of a source view (place.json look_ring: centre, radius_m) as n+1 points round it, closed."""
    cx, cy = ring["centre"]
    r = float(ring["radius_m"]) * geom.UNITS_PER_M
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n + 1)]


def ring_crossings(ring: dict, a, b) -> list[float]:
    """Where a section line a->b (plan points) crosses the ring: distances along it from a."""
    a, b = np.asarray(a[:2], float), np.asarray(b[:2], float)
    c, r = np.asarray(ring["centre"], float), float(ring["radius_m"]) * geom.UNITS_PER_M
    L = float(np.linalg.norm(b - a))
    if L == 0:
        return []
    t = (b - a) / L
    f = a - c
    p, q = float(f @ t), float(f @ f) - r * r
    disc = p * p - q
    if disc < 0:
        return []
    return [s for s in (-p - math.sqrt(disc), -p + math.sqrt(disc)) if 0 <= s <= L]


def draw_ring(d: ImageDraw.ImageDraw, cam: dict, scene, w: int, h: int, k: float) -> None:
    """The footprint ring on the ground, in pieces wherever it is in front of the camera, with its radius."""
    ring = getattr(scene, "ring", None)
    if not ring:
        return
    pts = ring_points(ring)
    zs = [scene.ground.height(x, y) for x, y in pts]
    known = [z for z in zs if z is not None]
    z0 = scene.ground.height(*ring["centre"]) or (sorted(known)[len(known) // 2] if known else 0.0)
    world = [(x, y, (z if z is not None else z0) + 4) for (x, y), z in zip(pts, zs)]   # past the bundle's land: level
    pp = geom.project(cam, world)
    seg, best = [], None
    for q in pp:
        if q[2] > 0:
            seg.append((float(q[0]), float(q[1])))
            if _inside(q, w, h) and (best is None or q[1] > best[1]):
                best = q
        else:
            if len(seg) > 1:
                d.line(seg, fill=RING, width=max(2, round(3 * k)))
            seg = []
    if len(seg) > 1:
        d.line(seg, fill=RING, width=max(2, round(3 * k)))
    if best is not None:
        tag(d, (float(best[0]), float(best[1]) - 10 * k), f"ring {ring['radius_m']:g} m", fill=(255, 220, 170, 235), size=11)


def annotate(img: Image.Image, cam: dict, scene, subject: dict | None, fault_ids: set[str], side_text: str,
             grid: bool = False) -> tuple[Image.Image, list[dict]]:
    """A perspective look's labels. Returns the image and the labels drawn [{text, at}]."""
    w, h = img.size
    k = unit(w)
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    labels = []
    tgt = np.asarray(cam["target"], float)
    dist = float(np.linalg.norm(np.asarray(cam["pos"]) - tgt))
    # the ground grid around the subject: lines every `step` units, on the ground
    step = None
    if grid and subject is not None:
        lo, hi = np.asarray(subject["lo"]), np.asarray(subject["hi"])
        span = max(hi[0] - lo[0], hi[1] - lo[1], 600.0)
        step = min((128, 256, 512, 1024, 2048, 4096), key=lambda s: abs(span * 1.6 / s - 8))
        x0, x1 = math.floor((lo[0] - span * 0.3) / step) * step, math.ceil((hi[0] + span * 0.3) / step) * step
        y0, y1 = math.floor((lo[1] - span * 0.3) / step) * step, math.ceil((hi[1] + span * 0.3) / step) * step
        for fixed_x in (True, False):
            for v in np.arange(x0 if fixed_x else y0, (x1 if fixed_x else y1) + 1, step):
                ts = np.linspace(y0, y1, 24) if fixed_x else np.linspace(x0, x1, 24)
                pts = [(v, t) if fixed_x else (t, v) for t in ts]
                world = [(x, y, (_grid_z(scene, x, y)) + 2) for x, y in pts]
                pp = geom.project(cam, world)
                seg = [(float(p[0]), float(p[1])) for p in pp if p[2] > 0]
                if len(seg) > 1:
                    d.line(seg, fill=(255, 255, 255, 70), width=max(1, round(k)))
    draw_ring(d, cam, scene, w, h, k)
    # red outlines on faulted pieces in frame
    for p in scene.pieces:
        if p["id"] not in fault_ids:
            continue
        pp = geom.project(cam, geom.corners(p))
        if (pp[:, 2] <= 0).any() or not any(_inside(q, w, h) for q in pp):
            continue
        hl = geom.hull(pp[:, :2])
        if len(hl) > 2:
            d.polygon(hl, outline=RED, width=max(2, round(3 * k)))
    # structure ids where they stand
    seen = []
    cl = scene.clusters()
    for cid, ps in sorted(cl.items()):
        bx = [geom.aabb(p) for p in ps]   # the label stands over the middle of the structure's pieces
        c = np.array([float(np.median([(b[0][0] + b[1][0]) / 2 for b in bx])), float(np.median([(b[0][1] + b[1][1]) / 2 for b in bx])),
                      float(np.median([b[1][2] for b in bx]))])
        if np.linalg.norm(c - tgt) > dist * 2.5:
            continue
        q = geom.project(cam, [c])[0]
        if not _inside(q, w, h, -10):
            continue
        if any(abs(q[0] - s[0]) < 40 * k and abs(q[1] - s[1]) < 16 * k for s in seen):
            continue
        seen.append(q)
        bad = any(p["id"] in fault_ids for p in ps)
        tag(d, (q[0], q[1]), cid, fill=(255, 220, 220, 235) if bad else (255, 255, 255, 225), size=12)
        labels.append({"text": cid, "at": [round(float(q[0])), round(float(q[1]))]})
    # a person's height at the subject, on the ground
    if subject is not None:
        lo, hi = subject["lo"], subject["hi"]
        gx, gy = lo[0], (lo[1] + hi[1]) / 2
        g = scene.ground.height(gx, gy) or lo[2]
        a, b = geom.project(cam, [[gx, gy, g], [gx, gy, g + geom.PERSON]])
        if a[2] > 0 and b[2] > 0 and _inside(a, w, h):
            ph = math.hypot(b[0] - a[0], b[1] - a[1])
            if ph >= 4 * k:
                x, y = float(a[0]), float(a[1])
                r = max(1.5 * k, ph * 0.09)
                d.line([(x, y), (x, y - ph + 2 * r)], fill=(255, 210, 0, 255), width=max(round(2 * k), int(ph / 14)))
                d.ellipse([x - r, y - ph, x + r, y - ph + 2 * r], fill=(255, 210, 0, 255))
                tag(d, (x, y - ph - 4 * k), "1.8 m", fill=(255, 240, 160, 230), size=11)
    # north arrow and the side seen from
    c0, c1 = geom.project(cam, [tgt, tgt + np.array([0, max(dist * 0.05, 50), 0])])
    ang = math.atan2(c1[1] - c0[1], c1[0] - c0[0]) if c0[2] > 0 and c1[2] > 0 else -math.pi / 2
    ox, oy, L = w - 34 * k, 38 * k, 22 * k
    d.ellipse([ox - 26 * k, oy - 26 * k, ox + 26 * k, oy + 26 * k], fill=(255, 255, 255, 200), outline=(0, 0, 0, 255), width=max(1, round(k)))
    tip = (ox + L * math.cos(ang), oy + L * math.sin(ang))
    tail = (ox - L * 0.6 * math.cos(ang), oy - L * 0.6 * math.sin(ang))
    d.line([tail, tip], fill=(200, 0, 0, 255), width=round(4 * k))
    d.text((tip[0] + 4 * k * math.cos(ang) - 5 * k, tip[1] + 4 * k * math.sin(ang) - 8 * k), "N", font=font(round(13 * k), True), fill=(0, 0, 0, 255))
    txt = side_text + (f"   grid {step} u = {step / geom.UNITS_PER_M:.1f} m" if step else "")
    tag(d, (8 * k + len(txt) * 3.6 * k, 24 * k), txt, size=13)
    return Image.alpha_composite(img, over), labels


def annotate_section(img: Image.Image, cam: dict, scene, prof, crossed: list[dict], fault_ids: set[str],
                     title: str) -> Image.Image:
    """A section's labels: ground line, water line, a height scale, each crossed piece's height over the ground."""
    w, h = img.size
    k = unit(w)
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    a, b = np.asarray(cam.get("prof_line", cam["line"])[0]), np.asarray(cam.get("prof_line", cam["line"])[1])
    t = (b - a) / np.linalg.norm(b - a)

    def px(s, z):
        q = geom.project(cam, [[*(a + t * s), z]])[0]
        return float(q[0]), float(q[1])
    pts = [px(s, g) for s, g, _ in prof if g is not None]
    if len(pts) > 1:
        d.line(pts, fill=(120, 60, 10, 255), width=round(4 * k))
        d.line(pts, fill=(250, 170, 60, 255), width=round(2 * k))
    wl = [(s, wz) for s, g, wz in prof if wz is not None and g is not None and wz > g]
    if wl:
        runs, cur = [], [wl[0]]
        for q in wl[1:]:
            if q[0] - cur[-1][0] > 40:
                runs.append(cur)
                cur = []
            cur.append(q)
        runs.append(cur)
        for r in runs:
            if len(r) > 1:
                d.line([px(s, wz) for s, wz in r], fill=(20, 110, 255, 255), width=round(4 * k))
        tag(d, (max(px(wl[0][0], wl[0][1])[0], 0) + 110 * k, px(wl[0][0], wl[0][1])[1] - 3 * k), f"water {wl[0][1]:.0f}", fill=(200, 225, 255, 235), size=11)
    ring = getattr(scene, "ring", None)
    for s_ in ring_crossings(ring, a, b) if ring else []:   # the footprint ring where the section crosses it
        x_, _ = px(s_, cam["target"][2])
        d.line([(x_, 0), (x_, h)], fill=RING, width=max(2, round(3 * k)))
        tag(d, (x_, 40 * k), f"ring {ring['radius_m']:g} m", fill=(255, 220, 170, 235), size=11)
    # height scale at the left
    upp = cam["upp"]
    zc = cam["target"][2]
    ztop, zbot = zc + upp * h / 2, zc - upp * h / 2
    stepz = geom.nice((ztop - zbot) / 6)
    d.rectangle([0, 0, 62 * k, h], fill=(255, 255, 255, 170))
    for z in np.arange(math.ceil(zbot / stepz) * stepz, ztop, stepz):
        _, y = px(0, z)
        d.line([(0, y), (w, y)], fill=(0, 0, 0, 40), width=max(1, round(k)))
        d.line([(52 * k, y), (62 * k, y)], fill=(0, 0, 0, 255), width=round(2 * k))
        d.text((2 * k, y - 7 * k), f"{z:.0f}", font=font(round(11 * k)), fill=(0, 0, 0, 255))
    # distance scale at the bottom
    L = float(np.linalg.norm(np.subtract(cam["line"][1], cam["line"][0])))
    sd = geom.nice(L / 5)
    x0, _ = px(0, zc)
    x1, _ = px(sd, zc)
    d.line([(x0 + 70 * k, h - 14 * k), (x1 + 70 * k, h - 14 * k)], fill=(0, 0, 0, 255), width=round(4 * k))
    tag(d, ((x0 + x1) / 2 + 70 * k, h - 18 * k), f"{sd:.0f} u = {sd / geom.UNITS_PER_M:.1f} m", size=11)
    # crossed pieces: outline (red when faulted) and their lowest point over the ground
    placed = []
    from tools.places.look import outline
    for c in crossed:   # every crossed piece by its mesh's own outline in the slab (its box only when it has no mesh)
        p = scene.by_id[c["id"]]
        pp = geom.project(cam, geom.corners(p))
        bad = p["id"] in fault_ids
        ol = outline.piece_outline(cam, p, (w, h), float(cam.get("slab", 96.0)))
        if ol is not None:
            ink = Image.new("RGBA", (w, h), RED if bad else (255, 255, 255, 200))
            over.paste(ink, (0, 0), ol.point(lambda v: 255 if v else 0))
            if bad:
                over.paste(ink, (0, 0), outline.edge(ol.filter(outline.ImageFilter.MaxFilter(2 * max(1, round(k)) + 1))).point(lambda v: 255 if v else 0))
        else:
            hl = geom.hull(pp[:, :2])
            if len(hl) > 2:
                d.polygon(hl, outline=RED if bad else (255, 255, 255, 150), width=round((3 if bad else 1) * k))
        if bad or c.get("label"):
            xm, ym = float(pp[:, 0].mean()), float(pp[:, 1].min())
            txt = f"{c['id'].split('.')[-1][:6]} {c.get('edid') or ''} {'+' if (c['over'] or 0) >= 0 else ''}{c['over']:.0f}" if c["over"] is not None else c["id"][-6:]
            yy = ym - 4 * k
            while any(abs(yy - q[1]) < 17 * k and abs(xm - q[0]) < 140 * k for q in placed):
                yy -= 17 * k
            placed.append((xm, yy))
            tag(d, (xm, yy), txt, fill=(255, 220, 220, 235) if bad else (255, 255, 255, 220), size=11)
    tag(d, (w / 2, 22 * k), title, size=13)
    for name, q in zip("AB", cam["line"]):   # the line's ends, at the foot of the frame
        x = float(geom.project(cam, [[q[0], q[1], cam["target"][2]]])[0][0])
        d.line([(x, h - 30 * k), (x, h)], fill=(0, 0, 0, 255), width=round(2 * k))
        d.text((x + 3 * k, h - 30 * k), name, font=font(round(16 * k), True), fill=(0, 0, 0, 255))
    return Image.alpha_composite(img, over)


def sheet(images: list[Image.Image], cols: int, captions: list[str] | None = None) -> Image.Image:
    w, h = images[0].size
    rows = math.ceil(len(images) / cols)
    out = Image.new("RGBA", (w * cols, h * rows), (40, 40, 40, 255))
    d = ImageDraw.Draw(out)
    for i, im in enumerate(images):
        x, y = (i % cols) * w, (i // cols) * h
        out.paste(im, (x, y))
        if captions:
            tag(d, (x + (60 + len(captions[i]) * 3) * unit(w), y + h - 6 * unit(w)), captions[i], size=12, k=unit(w))
        d.rectangle([x, y, x + w - 1, y + h - 1], outline=(0, 0, 0, 255), width=max(1, round(unit(w))))
    return out


def pair(a: Image.Image, b: Image.Image, la: str, lb: str) -> Image.Image:
    out = sheet([a, b], 2)
    d = ImageDraw.Draw(out)
    tag(d, (a.size[0] / 2, a.size[1] - 8 * unit(a.size[0])), la, size=15, fill=(255, 255, 160, 240), k=unit(a.size[0]))
    tag(d, (a.size[0] * 1.5, a.size[1] - 8 * unit(a.size[0])), lb, size=15, fill=(255, 255, 160, 240), k=unit(a.size[0]))
    return out


def mesh_overlay(img: Image.Image, cam: dict, M, doors: list[tuple[str, list, bool]], points: list[tuple[list, bool]],
                 keep=None) -> Image.Image:
    """The built walkable mesh over a look: each island translucent in its own colour (the main network green) with
    its id at its middle, door arrivals as squares and street points as dots (white on the mesh, red off it).
    `keep`: a mask of the triangles to draw (a section's slab); else those in front of the camera and in the frame."""
    from tools.places.look import mesh as mesh_
    w, h = img.size
    k = unit(w)
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    if len(M.T):
        P = geom.project(cam, M.V)
        tri = P[M.T]                                   # (n, 3, 3)
        front = (tri[:, :, 2] > 0).all(axis=1)
        inside = (tri[:, :, 0].max(1) >= 0) & (tri[:, :, 0].min(1) <= w) & (tri[:, :, 1].max(1) >= 0) & (tri[:, :, 1].min(1) <= h)
        e1, e2 = tri[:, 1, :2] - tri[:, 0, :2], tri[:, 2, :2] - tri[:, 0, :2]
        small = np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]) / 2 < w * h / 6   # one right by the eye hides the rest
        m = front & inside & small & (np.ones(len(M.T), bool) if keep is None else keep)
        idx = np.where(m)[0]
        idx = idx[np.argsort(-tri[idx, :, 2].mean(1))]
        for i in idx:
            c = mesh_.colour(int(M.lab[i]), M.main)
            d.polygon([(float(x), float(y)) for x, y, _ in tri[i]], fill=c + (70,), outline=c + (170,), width=max(1, round(k)))
        for isl in sorted(set(M.lab[idx].tolist())):
            s = idx[M.lab[idx] == isl]
            cx, cy = float(tri[s, :, 0].mean()), float(tri[s, :, 1].mean())
            if 0 <= cx < w and 0 <= cy < h:
                tag(d, (cx, cy), f"#{isl}" + (" main" if isl == M.main else f" {int(M.count[isl])}t"),
                    fill=mesh_.colour(int(isl), M.main) + (230,), size=11)
    for name, at, on in doors:
        p = geom.project(cam, [at])[0]
        if p[2] > 0 and _inside(p, w, h):
            col = (255, 255, 255, 255) if on else (230, 20, 20, 255)
            d.rectangle([p[0] - 5 * k, p[1] - 5 * k, p[0] + 5 * k, p[1] + 5 * k], fill=col, outline=(0, 0, 0, 255), width=max(1, round(k)))
            tag(d, (p[0] + 4 * k, p[1] - 14 * k), name, size=10, bold=False)
    if points:
        pp = geom.project(cam, [q for q, _ in points])
        for p, (_, on) in zip(pp, points):
            if p[2] > 0 and _inside(p, w, h):
                col = (255, 255, 255, 255) if on else (230, 20, 20, 255)
                d.ellipse([p[0] - 3 * k, p[1] - 3 * k, p[0] + 3 * k, p[1] + 3 * k], fill=col, outline=(0, 0, 0, 255), width=max(1, round(k)))
    return Image.alpha_composite(img.convert("RGBA"), over)
