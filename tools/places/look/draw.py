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


def tag(d: ImageDraw.ImageDraw, xy, text: str, fill=(255, 255, 255, 235), ink=(0, 0, 0, 255), size: int = 13, bold=True):
    f = font(size, bold)
    x, y = xy
    b = d.textbbox((0, 0), text, font=f)
    w, h = b[2] - b[0] + 6, b[3] - b[1] + 4
    x = min(max(2, x - w / 2), d.im.size[0] - w - 2)
    y = min(max(2, y - h), d.im.size[1] - h - 2)
    d.rectangle([x, y, x + w, y + h], fill=fill, outline=(0, 0, 0, 255))
    d.text((x + 3, y + 1 - b[1]), text, font=f, fill=ink)
    return [x, y, x + w, y + h]


def _inside(p, w, h, pad=0):
    return p[2] > 0 and -pad <= p[0] <= w + pad and -pad <= p[1] <= h + pad


def annotate(img: Image.Image, cam: dict, scene, subject: dict | None, fault_ids: set[str], side_text: str,
             grid: bool = True) -> tuple[Image.Image, list[dict]]:
    """A perspective look's labels. Returns the image and the labels drawn [{text, at}]."""
    w, h = img.size
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
                    d.line(seg, fill=(255, 255, 255, 70), width=1)
    # red outlines on faulted pieces in frame
    for p in scene.pieces:
        if p["id"] not in fault_ids:
            continue
        pp = geom.project(cam, geom.corners(p))
        if (pp[:, 2] <= 0).any() or not any(_inside(q, w, h) for q in pp):
            continue
        hl = geom.hull(pp[:, :2])
        if len(hl) > 2:
            d.polygon(hl, outline=RED, width=3)
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
        if any(abs(q[0] - s[0]) < 40 and abs(q[1] - s[1]) < 16 for s in seen):
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
            if ph >= 4:
                x, y = float(a[0]), float(a[1])
                r = max(1.5, ph * 0.09)
                d.line([(x, y), (x, y - ph + 2 * r)], fill=(255, 210, 0, 255), width=max(2, int(ph / 14)))
                d.ellipse([x - r, y - ph, x + r, y - ph + 2 * r], fill=(255, 210, 0, 255))
                tag(d, (x, y - ph - 4), "1.8 m", fill=(255, 240, 160, 230), size=11)
    # north arrow and the side seen from
    c0, c1 = geom.project(cam, [tgt, tgt + np.array([0, max(dist * 0.05, 50), 0])])
    ang = math.atan2(c1[1] - c0[1], c1[0] - c0[0]) if c0[2] > 0 and c1[2] > 0 else -math.pi / 2
    ox, oy, L = w - 34, 38, 22
    d.ellipse([ox - 26, oy - 26, ox + 26, oy + 26], fill=(255, 255, 255, 200), outline=(0, 0, 0, 255))
    tip = (ox + L * math.cos(ang), oy + L * math.sin(ang))
    tail = (ox - L * 0.6 * math.cos(ang), oy - L * 0.6 * math.sin(ang))
    d.line([tail, tip], fill=(200, 0, 0, 255), width=4)
    d.text((tip[0] + 4 * math.cos(ang) - 5, tip[1] + 4 * math.sin(ang) - 8), "N", font=font(13, True), fill=(0, 0, 0, 255))
    txt = side_text + (f"   grid {step} u = {step / geom.UNITS_PER_M:.1f} m" if step else "")
    tag(d, (8 + len(txt) * 3.6, 24), txt, size=13)
    return Image.alpha_composite(img, over), labels


def annotate_section(img: Image.Image, cam: dict, scene, prof, crossed: list[dict], fault_ids: set[str],
                     title: str) -> Image.Image:
    """A section's labels: ground line, water line, a height scale, each crossed piece's height over the ground."""
    w, h = img.size
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    a, b = np.asarray(cam.get("prof_line", cam["line"])[0]), np.asarray(cam.get("prof_line", cam["line"])[1])
    t = (b - a) / np.linalg.norm(b - a)

    def px(s, z):
        q = geom.project(cam, [[*(a + t * s), z]])[0]
        return float(q[0]), float(q[1])
    pts = [px(s, g) for s, g, _ in prof if g is not None]
    if len(pts) > 1:
        d.line(pts, fill=(120, 60, 10, 255), width=4)
        d.line(pts, fill=(250, 170, 60, 255), width=2)
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
                d.line([px(s, wz) for s, wz in r], fill=(20, 110, 255, 255), width=4)
        tag(d, (max(px(wl[0][0], wl[0][1])[0], 0) + 110, px(wl[0][0], wl[0][1])[1] - 3), f"water {wl[0][1]:.0f}", fill=(200, 225, 255, 235), size=11)
    # height scale at the left
    upp = cam["upp"]
    zc = cam["target"][2]
    ztop, zbot = zc + upp * h / 2, zc - upp * h / 2
    stepz = geom.nice((ztop - zbot) / 6)
    d.rectangle([0, 0, 62, h], fill=(255, 255, 255, 170))
    for z in np.arange(math.ceil(zbot / stepz) * stepz, ztop, stepz):
        _, y = px(0, z)
        d.line([(0, y), (w, y)], fill=(0, 0, 0, 40), width=1)
        d.line([(52, y), (62, y)], fill=(0, 0, 0, 255), width=2)
        d.text((2, y - 7), f"{z:.0f}", font=font(11), fill=(0, 0, 0, 255))
    # distance scale at the bottom
    L = float(np.linalg.norm(np.subtract(cam["line"][1], cam["line"][0])))
    sd = geom.nice(L / 5)
    x0, _ = px(0, zc)
    x1, _ = px(sd, zc)
    d.line([(x0 + 70, h - 14), (x1 + 70, h - 14)], fill=(0, 0, 0, 255), width=4)
    tag(d, ((x0 + x1) / 2 + 70, h - 18), f"{sd:.0f} u = {sd / geom.UNITS_PER_M:.1f} m", size=11)
    # crossed pieces: outline (red when faulted) and their lowest point over the ground
    placed = []
    for c in crossed:
        p = scene.by_id[c["id"]]
        pp = geom.project(cam, geom.corners(p))
        hl = geom.hull(pp[:, :2])
        bad = p["id"] in fault_ids
        if len(hl) > 2 and (bad or c.get("label")):
            d.polygon(hl, outline=RED if bad else (255, 255, 255, 150), width=3 if bad else 1)
        if bad or c.get("label"):
            xm, ym = float(pp[:, 0].mean()), float(pp[:, 1].min())
            txt = f"{c['id'].split('.')[-1][:6]} {c.get('edid') or ''} {'+' if (c['over'] or 0) >= 0 else ''}{c['over']:.0f}" if c["over"] is not None else c["id"][-6:]
            yy = ym - 4
            while any(abs(yy - q[1]) < 17 and abs(xm - q[0]) < 140 for q in placed):
                yy -= 17
            placed.append((xm, yy))
            tag(d, (xm, yy), txt, fill=(255, 220, 220, 235) if bad else (255, 255, 255, 220), size=11)
    tag(d, (w / 2, 22), title, size=13)
    for name, q in zip("AB", cam["line"]):   # the line's ends, at the foot of the frame
        x = float(geom.project(cam, [[q[0], q[1], cam["target"][2]]])[0][0])
        d.line([(x, h - 30), (x, h)], fill=(0, 0, 0, 255), width=2)
        d.text((x + 3, h - 30), name, font=font(16, True), fill=(0, 0, 0, 255))
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
            tag(d, (x + 60 + len(captions[i]) * 3, y + h - 6), captions[i], size=12)
        d.rectangle([x, y, x + w - 1, y + h - 1], outline=(0, 0, 0, 255))
    return out


def pair(a: Image.Image, b: Image.Image, la: str, lb: str) -> Image.Image:
    out = sheet([a, b], 2)
    d = ImageDraw.Draw(out)
    tag(d, (a.size[0] / 2, a.size[1] - 8), la, size=15, fill=(255, 255, 160, 240))
    tag(d, (a.size[0] * 1.5, a.size[1] - 8), lb, size=15, fill=(255, 255, 160, 240))
    return out


def mesh_overlay(img: Image.Image, cam: dict, M, doors: list[tuple[str, list, bool]], points: list[tuple[list, bool]],
                 keep=None) -> Image.Image:
    """The built walkable mesh over a look: each island translucent in its own colour (the main network green) with
    its id at its middle, door arrivals as squares and street points as dots (white on the mesh, red off it).
    `keep`: a mask of the triangles to draw (a section's slab); else those in front of the camera and in the frame."""
    from tools.places.look import mesh as mesh_
    w, h = img.size
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
            d.polygon([(float(x), float(y)) for x, y, _ in tri[i]], fill=c + (70,), outline=c + (170,))
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
            d.rectangle([p[0] - 5, p[1] - 5, p[0] + 5, p[1] + 5], fill=col, outline=(0, 0, 0, 255))
            tag(d, (p[0] + 4, p[1] - 14), name, size=10, bold=False)
    if points:
        pp = geom.project(cam, [q for q, _ in points])
        for p, (_, on) in zip(pp, points):
            if p[2] > 0 and _inside(p, w, h):
                col = (255, 255, 255, 255) if on else (230, 20, 20, 255)
                d.ellipse([p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3], fill=col, outline=(0, 0, 0, 255))
    return Image.alpha_composite(img.convert("RGBA"), over)
