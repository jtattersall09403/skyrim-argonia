"""Grade a generated model's own texture toward Skyrim's measured materials, keeping its detail and wear.

  grade.py regions in.glb outdir k        splits the base colour into k colour regions (k-means in CIELAB over the
                                          texture pixels the model really uses) and writes outdir/regions.png: each
                                          region's swatch and where it lies on the texture, for the agent to name
  grade.py apply in.glb outdir reference.json "0=weathered wood,1=rope and binding,..." [strength=0.7]
                                          moves each named region toward its material's reference (reference.py):
                                          lightness percentiles mapped onto the material's 10th/50th/90th, chroma
                                          scaled to its median, hue turned toward its mean; normal-map strength
                                          brought to the material's median tilt. The change is blended by each
                                          pixel's soft membership, so region edges never show; `strength` (0 to 1)
                                          is how far toward the reference it goes. Writes outdir/graded.glb and
                                          outdir/grade.json: every measure before and after, against the reference.

The geometry and UVs are untouched. Texel density is measured and reported, not changed (that needs new UVs)."""
import json, sys
from pathlib import Path
import numpy as np, trimesh
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference import lab

M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])


def unlab(L):
    fy = (L[:, 0] + 16) / 116; fx = fy + L[:, 1] / 500; fz = fy - L[:, 2] / 200
    f = np.stack([fx, fy, fz], 1); xyz = np.where(f ** 3 > 0.008856, f ** 3, (f - 16 / 116) / 7.787) * [0.95047, 1.0, 1.08883]
    c = xyz @ np.linalg.inv(M).T; c = np.where(c > 0.0031308, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055, 12.92 * c)
    return np.clip(c * 255, 0, 255)


def load(src):
    sc = trimesh.load(src, force='scene', process=False); geos = [(n, sc.geometry[sc.graph.get(n)[1]]) for n in sc.graph.nodes_geometry]
    main = max(geos, key=lambda t: len(t[1].faces))[1]; return sc, main


def used_mask(g, size):
    """The texture pixels the model's triangles cover, drawn from its real UVs."""
    m = Image.new('L', size, 0); d = ImageDraw.Draw(m); W, H = size
    for t in np.asarray(g.visual.uv)[g.faces]:
        d.polygon([(u % 1 * W, (1 - v % 1) * H) for u, v in t], fill=255)
    return np.asarray(m) > 0


def kmeans(X, k, it=25, seed=3):
    rng = np.random.default_rng(seed); C = X[rng.choice(len(X), k, replace=False)]
    for _ in range(it):
        lab_ = np.argmin(((X[:, None] - C[None]) ** 2).sum(-1), 1); C = np.array([X[lab_ == j].mean(0) if (lab_ == j).any() else C[j] for j in range(k)])
    return C


def soft(Lab, C, temp=6.0):
    d = np.sqrt(((Lab[:, None] - C[None]) ** 2).sum(-1)); w = np.exp(-(d - d.min(1, keepdims=True)) / temp); return w / w.sum(1, keepdims=True)


def stats(L, w=None):
    w = np.ones(len(L)) if w is None else w; ch = np.hypot(L[:, 1], L[:, 2]); h = np.arctan2(L[:, 2], L[:, 1])
    def wp(x, q): o = np.argsort(x); c = np.cumsum(w[o]); return float(x[o][np.searchsorted(c, q / 100 * c[-1])])
    s = (ch > 6) * w
    return {"L": [round(wp(L[:, 0], q), 1) for q in (10, 50, 90)], "chroma": round(wp(ch, 50), 1),
            "hue": round(float(np.degrees(np.arctan2((np.sin(h) * s).sum(), (np.cos(h) * s).sum())) % 360)) if s.sum() > 20 else None}


def density(g, px):
    U = np.asarray(g.visual.uv)[g.faces]; e1, e2 = U[:, 1] - U[:, 0], U[:, 2] - U[:, 0]
    return round(float(np.sqrt(0.5 * np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]).sum() / g.area)) * px, 1)


def regions(src, out, k):
    out = Path(out); out.mkdir(parents=True, exist_ok=True); _, g = load(src); tex = g.visual.material.baseColorTexture.convert('RGB')
    small = tex.resize((512, 512)); mask = used_mask(g, (512, 512)); px = np.asarray(small, np.float32).reshape(-1, 3); Lb = lab(px)
    C = kmeans(Lb[mask.ravel()][::3], k); lab_ = np.argmin(((Lb[:, None] - C[None]) ** 2).sum(-1), 1)
    sheet = Image.new('RGB', (512 * 2, 512 + 60), (40, 40, 40)); sheet.paste(small, (0, 0)); pal = [(230, 25, 75), (60, 180, 75), (255, 225, 25), (0, 130, 200), (245, 130, 48), (145, 30, 180), (70, 240, 240), (240, 50, 230)]
    vis = np.array([pal[j % 8] for j in lab_], np.uint8).reshape(512, 512, 3); vis[~mask] = 30; sheet.paste(Image.fromarray(vis), (512, 0)); d = ImageDraw.Draw(sheet)
    for j in range(k):
        rgb = tuple(int(x) for x in unlab(C[j:j + 1])[0]); share = float((lab_[mask.ravel()] == j).mean())
        d.rectangle([8 + j * 120, 520, 48 + j * 120, 556], fill=rgb, outline=pal[j % 8], width=4); d.text((54 + j * 120, 528), f"{j}: {share:.0%}", fill=(255, 255, 255))
    sheet.save(out / 'regions.png'); np.save(out / 'centres.npy', C)
    return {"regions": k, "shares": [round(float((lab_[mask.ravel()] == j).mean()), 3) for j in range(k)], "sheet": str(out / 'regions.png')}


def apply(src, out, refpath, names, strength=0.7):
    out = Path(out); sc, g = load(src); ref = json.loads(Path(refpath).read_text())["summary"]; C = np.load(out / 'centres.npy')
    name = {int(a): b.strip() for a, b in (p.split('=') for p in names.split(','))}
    mat = g.visual.material; tex = mat.baseColorTexture.convert('RGB'); W, H = tex.size
    A = np.asarray(tex, np.float32).reshape(-1, 3); Lb = lab(A); P = soft(Lb, C); mask = used_mask(g, (W, H)).ravel()
    before, after, Ln = {}, {}, Lb.copy()
    for j, m in name.items():
        r = ref[m]; w = P[:, j] * mask; s0 = stats(Lb[mask], P[mask, j]); before[f"{j} {m}"] = s0
        lo, mid, hi = s0["L"]; tlo, tmid, thi = r["L10"][1], r["L50"][1], r["L90"][1]
        L = Lb[:, 0]; tgt = np.where(L < mid, tmid + (L - mid) * (tmid - tlo) / max(mid - lo, 1e-3), tmid + (L - mid) * (thi - tmid) / max(hi - mid, 1e-3))
        ch = np.hypot(Lb[:, 1], Lb[:, 2]); h = np.arctan2(Lb[:, 2], Lb[:, 1]); k = r["chroma"][1] / max(s0["chroma"], 1e-3)
        dh = 0.0 if r["hue"] is None or s0["hue"] is None else np.radians(((r["hue"] - s0["hue"] + 180) % 360) - 180) * 0.5
        a2, b2 = ch * k * np.cos(h + dh), ch * k * np.sin(h + dh)
        f = (w * strength)[:, None]; Ln = Ln + f * (np.stack([tgt, a2, b2], 1) - Lb)
    for j, m in name.items():
        after[f"{j} {m}"] = stats(Ln[mask], P[mask, j])
    graded = Image.fromarray(unlab(Ln).reshape(H, W, 3).astype(np.uint8)); out.mkdir(parents=True, exist_ok=True)
    nrm = getattr(mat, 'normalTexture', None); nb = na = None
    if nrm is not None:     # normal strength toward the area-weighted reference tilt of the named materials
        N = np.asarray(nrm.convert('RGB'), np.float32) / 127.5 - 1; tilt = np.degrees(np.arcsin(np.clip(np.hypot(N[..., 0], N[..., 1]), 0, 1)))
        shares = {j: float(P[mask, j].mean()) for j in name}; want = sum(shares[j] * ref[m]["normal_deg"][1] for j, m in name.items()) / sum(shares.values())
        nb = round(float(np.median(tilt)), 1); s = np.tan(np.radians(want)) / max(np.tan(np.radians(nb)), 1e-3); s = 1 + (s - 1) * strength
        xy = N[..., :2] * s; z = np.sqrt(np.clip(1 - (xy ** 2).sum(-1), 0, 1)); N2 = np.dstack([xy, z])
        mat.normalTexture = Image.fromarray(((N2 + 1) * 127.5).clip(0, 255).astype(np.uint8)); na = round(float(np.median(np.degrees(np.arcsin(np.clip(np.hypot(*N2[..., :2].transpose(2, 0, 1)), 0, 1))))), 1)
    mat.baseColorTexture = graded; sc.export(out / 'graded.glb')
    res = {"strength": strength, "regions": name, "before": before, "after": after, "reference": {m: {k: ref[m][k] for k in ("L10", "L50", "L90", "chroma", "hue", "normal_deg", "px_per_m")} for m in set(name.values())},
           "normal_tilt_deg": {"before": nb, "after": na}, "px_per_m": density(g, W)}
    (out / 'grade.json').write_text(json.dumps(res, indent=1)); return res


if __name__ == '__main__':
    a = sys.argv
    if a[1] == 'regions': print(json.dumps(regions(a[2], a[3], int(a[4]))))
    else: print(json.dumps(apply(a[2], a[3], a[4], a[5], float(a[6]) if len(a) > 6 else 0.7)))
