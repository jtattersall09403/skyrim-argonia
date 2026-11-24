"""Bring a building-sized generation's texture up to the game's texel density without changing its look.

  densify.py in.glb out_dir px_per_m swatch.jpg swatch_px_per_m [atlas_px=8192] [amount=0.20]

1. New UVs (xatlas) at one even density: px_per_m texture pixels per metre of the real surface, packed into as many
   atlases of atlas_px as it takes. The triangles are the same; vertices split only along the new seams.
2. The generator's own texture re-baked onto them: every new texel finds its triangle and its place on the old UVs
   and takes the old colour there (bilinear). Nothing of the generated look is lost; where the old texture was
   coarser it is only magnified.
3. A grain layer: the fine detail of one of our own material swatches (its blur taken away, so it carries no colour
   and no shading), shown at the swatch's true size, laid per chart of the new atlas with
   - its grain turned to run along the re-bake's own strokes in that chart (the structure tensor of the chart's
     lightness), a chart with no clear direction getting less of it;
   - its own random offset and a scale of 0.85 to 1.15, so no two charts repeat;
   - its strength set per texel by how little fine detail the re-bake has there (the generator's own grain is
     never painted over) and by how wood-like the colour is (low chroma: amber windows, green moss and bright painted
     colour get none);
   It only multiplies lightness by 1 +- amount, so the mean colour of every chart is unchanged.
4. The atlas gutters filled outward from the charts (push-pull), so no filtering level ever pulls in black.

Writes out_dir/densified.glb (one material per atlas, JPEG textures), out_dir/atlas<i>.jpg and out_dir/densify.json:
density, fine detail, mean colour, triangles and seams before and after."""
import json, sys
from pathlib import Path
import numpy as np, trimesh, xatlas
from PIL import Image
from scipy.ndimage import gaussian_filter
Image.MAX_IMAGE_PIXELS = None


def load(src):
    sc = trimesh.load(src, force='scene', process=False); return max(sc.geometry.values(), key=lambda g: len(g.faces))


def density(V, F, UV, px):
    """Texture pixels per metre over the whole surface, from the real triangles and their UVs."""
    T = V[F]; U = UV[F]; e1, e2 = U[:, 1] - U[:, 0], U[:, 2] - U[:, 0]
    a3 = 0.5 * np.linalg.norm(np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]), axis=1).sum()
    return float(np.sqrt(0.5 * np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]).sum() / a3)) * px


def blur(a, r):
    return gaussian_filter(np.asarray(a, np.float32), r, mode='nearest')


def fine(L, r=2):
    """Fine detail per texel: the absolute difference between lightness and its r-pixel blur (0-255 grey levels)."""
    return np.abs(L - blur(L, r))


def lab(rgb):
    """Lightness and chroma (CIE Lab) of an RGB float array."""
    c = rgb / 255.0; c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    xyz = c @ np.array([[0.4124, 0.2126, 0.0193], [0.3576, 0.7152, 0.1192], [0.1805, 0.0722, 0.9505]], np.float32)
    xyz /= np.array([0.9505, 1.0, 1.089], np.float32); f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return 116 * f[..., 1] - 16, np.hypot(500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2]))


def bake(V, F, UVold, UVnew, atlas_of, chart_of, n_atlas, size, tex):
    """Each new texel takes the old texture's colour at the same point of the same triangle; returns the atlases,
    their coverage and the chart index of every texel (-1 in the gutters)."""
    T = np.asarray(tex.convert('RGB'), np.float32); th, tw = T.shape[:2]
    out = [np.zeros((size, size, 3), np.float32) for _ in range(n_atlas)]; ch = [np.full((size, size), -1, np.int32) for _ in range(n_atlas)]
    for f in range(len(F)):
        a = atlas_of[f]; P = UVnew[F[f]] * size; P[:, 1] = size - P[:, 1]
        x0, y0 = np.maximum(np.floor(P.min(0)).astype(int) - 1, 0); x1, y1 = np.minimum(np.ceil(P.max(0)).astype(int) + 1, size - 1)
        if x1 < x0 or y1 < y0: continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        v0, v1, v2 = P; d = (v1[1] - v2[1]) * (v0[0] - v2[0]) + (v2[0] - v1[0]) * (v0[1] - v2[1])
        if abs(d) < 1e-12: continue
        l0 = ((v1[1] - v2[1]) * (xs - v2[0]) + (v2[0] - v1[0]) * (ys - v2[1])) / d; l1 = ((v2[1] - v0[1]) * (xs - v2[0]) + (v0[0] - v2[0]) * (ys - v2[1])) / d; l2 = 1 - l0 - l1
        e = 1.0 / max(abs(d) ** 0.5, 1.0)                        # about one texel over each edge, so seams never show the gutter
        m = (l0 >= -e) & (l1 >= -e) & (l2 >= -e)
        if not m.any(): continue
        uo = UVold[F[f]]; u = l0[m] * uo[0, 0] + l1[m] * uo[1, 0] + l2[m] * uo[2, 0]; v = l0[m] * uo[0, 1] + l1[m] * uo[1, 1] + l2[m] * uo[2, 1]
        px = (u % 1) * (tw - 1); py = (1 - v % 1) * (th - 1); ix, iy = np.floor(px).astype(int), np.floor(py).astype(int); fx, fy = (px - ix)[:, None], (py - iy)[:, None]
        ix1, iy1 = np.minimum(ix + 1, tw - 1), np.minimum(iy + 1, th - 1)
        c = T[iy, ix] * (1 - fx) * (1 - fy) + T[iy, ix1] * fx * (1 - fy) + T[iy1, ix] * (1 - fx) * fy + T[iy1, ix1] * fx * fy
        yy, xx = ys[m].astype(int), xs[m].astype(int); inside = (l0[m] >= 0) & (l1[m] >= 0) & (l2[m] >= 0)
        keep = inside | (ch[a][yy, xx] < 0)                      # a texel inside its own triangle wins over a neighbour's overhang
        out[a][yy[keep], xx[keep]] = c[keep]; ch[a][yy[keep], xx[keep]] = chart_of[f]
    return out, [c >= 0 for c in ch], ch


def grain_swatch(path, swatch_ppm, ppm):
    """The swatch's fine detail at the atlas's scale (one swatch pixel = 1/swatch_ppm m), unit spread, with the
    direction its strokes run (radians, in swatch pixels)."""
    D = Image.open(path).convert('L'); k = ppm / swatch_ppm
    D = D.resize((max(16, round(D.width * k)), max(16, round(D.height * k))), Image.LANCZOS)
    g = np.asarray(D, np.float32); hp = g - blur(g, 4); hp /= max(float(hp.std()), 1e-3)
    gy, gx = np.gradient(blur(g, 1)); ang = 0.5 * np.arctan2(2 * (gx * gy).mean(), ((gx ** 2) - (gy ** 2)).mean())
    return hp, float(ang)                                         # ang: the mean gradient direction; strokes run across it


def chart_grain(L, chart, cov, hp, swatch_ang, rng):
    """The grain field for one atlas: per chart, the swatch turned so its strokes follow the chart's own strokes,
    at its own offset and scale. Returns the field and each chart's coherence (0 no direction, 1 one direction)."""
    out = np.zeros(L.shape, np.float32); coh = np.zeros(L.shape, np.float32); H, W = hp.shape
    gy, gx = np.gradient(blur(L, 1.5)); jxx, jyy, jxy = gx * gx, gy * gy, gx * gy
    ids = np.unique(chart[cov]); ys, xs = np.nonzero(cov); cid = chart[ys, xs]; order = np.argsort(cid, kind='stable')
    ys, xs, cid = ys[order], xs[order], cid[order]; starts = np.searchsorted(cid, ids); ends = np.r_[starts[1:], len(cid)]
    for c, s, e in zip(ids, starts, ends):
        y, x = ys[s:e], xs[s:e]; a, b, d = jxx[y, x].sum(), jyy[y, x].sum(), jxy[y, x].sum()
        ang = 0.5 * np.arctan2(2 * d, a - b); k = float(np.hypot(a - b, 2 * d) / max(a + b, 1e-6))
        t = ang - swatch_ang + (rng.uniform(-np.pi, np.pi) if k < 0.15 else 0.0); sc = rng.uniform(0.85, 1.15)
        ct, st = np.cos(-t), np.sin(-t); x0, y0 = rng.uniform(0, W), rng.uniform(0, H)
        u = (ct * x - st * y) / sc + x0; v = (st * x + ct * y) / sc + y0
        iu, iv = np.floor(u).astype(int), np.floor(v).astype(int); fu, fv = u - iu, v - iv
        a0, a1, b0, b1 = iu % W, (iu + 1) % W, iv % H, (iv + 1) % H
        out[y, x] = hp[b0, a0] * (1 - fu) * (1 - fv) + hp[b0, a1] * fu * (1 - fv) + hp[b1, a0] * (1 - fu) * fv + hp[b1, a1] * fu * fv
        coh[y, x] = k
    return out, coh


def push_pull(img, cov):
    """Fill every uncovered texel from the covered ones around it, coarse to fine, so the gutters carry the charts'
    own colours at every filtering level."""
    levels = [(img * cov[..., None], cov.astype(np.float32))]
    while levels[-1][1].shape[0] > 1:
        c, w = levels[-1]; h = c.shape[0] // 2
        c2 = c[:2 * h, :2 * h].reshape(h, 2, h, 2, 3).sum((1, 3)); w2 = w[:2 * h, :2 * h].reshape(h, 2, h, 2).sum((1, 3))
        levels.append((c2, w2))
    fill = levels[-1][0] / np.maximum(levels[-1][1], 1e-6)[..., None]
    for c, w in reversed(levels[:-1]):
        up = np.repeat(np.repeat(fill, 2, 0), 2, 1)[:c.shape[0], :c.shape[1]]
        fill = np.where((w > 0)[..., None], c / np.maximum(w, 1e-6)[..., None], up)
    return np.where(cov[..., None], img, fill)


def densify(src, outdir, ppm, swatch, swatch_ppm, atlas_px=8192, amount=0.20, seed=1):
    out = Path(outdir); out.mkdir(parents=True, exist_ok=True); g = load(src); tex = g.visual.material.baseColorTexture
    V, F, UVo = np.asarray(g.vertices), np.asarray(g.faces), np.asarray(g.visual.uv, float)
    T0 = np.asarray(tex.convert('RGB'), np.float32); L0, C0 = lab(T0)
    before = {"px_per_m": round(density(V, F, UVo, tex.size[0]), 1), "texture_px": list(tex.size), "triangles": int(len(F)), "vertices": int(len(V)),
              "fine_detail": round(float(fine(T0.mean(-1)).mean()), 2), "mean_L": round(float(L0.mean()), 2), "mean_chroma": round(float(C0.mean()), 2)}
    at = xatlas.Atlas(); at.add_mesh(V.astype(np.float32), F.astype(np.uint32))
    po = xatlas.PackOptions(); po.resolution = atlas_px; po.texels_per_unit = float(ppm); po.padding = 4; po.bilinear = True
    at.generate(xatlas.ChartOptions(), po)
    vmap, F2, UV2 = at[0]; n_atlas, size = at.atlas_count, at.width
    vatl, vch = (np.asarray(x) for x in at.get_mesh_vertex_assignment(0)); atlas_of, chart_of = vatl[F2[:, 0]], vch[F2[:, 0]]
    imgs, cov, charts = bake(V[vmap], F2, UVo[vmap], UV2, atlas_of, chart_of, n_atlas, size, tex)
    hp, sang = grain_swatch(swatch, swatch_ppm, ppm); rng = np.random.default_rng(seed); res, per = [], []
    for a in range(n_atlas):
        im = imgs[a]; L, C = lab(im); have = blur(fine(L), 6)               # the re-bake's own fine detail, in L units
        lack = np.clip(1 - have / 3.0, 0, 1); woody = np.clip((24 - C) / 10, 0, 1)
        gr, coh = chart_grain(L, charts[a], cov[a], hp, sang, rng); w = lack * woody * (0.4 + 0.6 * coh) * cov[a]
        fin = np.clip(im * (1 + amount * np.clip(gr, -3, 3) * w)[..., None], 0, 255)
        L1, C1 = lab(fin); m = cov[a]
        per.append({"atlas": a, "used": round(float(m.mean()), 3), "fine_detail_rebaked": round(float(fine(L)[m].mean()), 2),
                    "fine_detail_after": round(float(fine(L1)[m].mean()), 2), "grain_weight_mean": round(float(w[m].mean()), 3),
                    "mean_L_rebaked": round(float(L[m].mean()), 2), "mean_L_after": round(float(L1[m].mean()), 2),
                    "mean_chroma_rebaked": round(float(C[m].mean()), 2), "mean_chroma_after": round(float(C1[m].mean()), 2)})
        pic = Image.fromarray(push_pull(fin, m).round().astype(np.uint8)); pic.save(out / f'atlas{a}.jpg', quality=90); res.append(Image.open(out / f'atlas{a}.jpg'))
    sc = trimesh.Scene()
    for a in range(n_atlas):
        sel = atlas_of == a
        if not sel.any(): continue
        mat = trimesh.visual.material.PBRMaterial(baseColorTexture=res[a], metallicFactor=0.0, roughnessFactor=0.9)
        m = trimesh.Trimesh(V[vmap], F2[sel], process=False); m.visual = trimesh.visual.TextureVisuals(uv=UV2, material=mat); m.remove_unreferenced_vertices(); sc.add_geometry(m, node_name=f'shell_{a}')
    sc.export(out / 'densified.glb')
    after = {"px_per_m": round(density(V[vmap], F2, UV2, size), 1), "atlases": n_atlas, "atlas_px": size, "charts": int(at.chart_count),
             "triangles": int(len(F2)), "vertices": int(len(vmap)), "seam_vertices_added": int(len(vmap) - len(V)), "per_atlas": per}
    r = {"source": str(src), "target_px_per_m": ppm, "swatch": str(swatch), "swatch_px_per_m": swatch_ppm, "amount": amount, "before": before, "after": after}
    (out / 'densify.json').write_text(json.dumps(r, indent=1)); return r


if __name__ == '__main__':
    a = sys.argv
    if len(a) < 6: raise SystemExit(__doc__)
    print(json.dumps(densify(a[1], a[2], float(a[3]), a[4], float(a[5]), int(a[6]) if len(a) > 6 else 8192, float(a[7]) if len(a) > 7 else 0.20)))
