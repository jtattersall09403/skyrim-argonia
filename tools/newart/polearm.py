"""Stage: shaping a pole weapon that acts as an existing one. The generator makes only the head; the shaft is made here
from simple shapes, to the DONOR's own measurements (grip at the origin, butt and tip where the donor's are), and takes
its wood colour, measured, from the head's own stub so the two match. Everything is measured on the real vertices.
usage: polearm.py head.glb outdir donor.json head_tris      (assemble: the generated head on a plain hand-made pole)
       polearm.py finish assembled_dir donor.json buttcap.glb gripband.glb outdir   (the finished weapon, below)"""
import sys, json, os, numpy as np, trimesh, pymeshlab
from PIL import Image, ImageFilter


def assemble():
    src, out, donor, head_tris = sys.argv[1], sys.argv[2], json.load(open(sys.argv[3])), int(sys.argv[4])
    os.makedirs(out, exist_ok=True)
    sc = trimesh.load(src, force='scene'); g = list(sc.geometry.values())[0].copy(); g.apply_transform(sc.graph.get(list(sc.graph.nodes_geometry)[0])[0])
    V = g.vertices
    # 1. the head's own frame: long axis up (Y); the blade's flat faces turned to face Z, as the donor's blade lies in X
    ext = np.ptp(V, axis=0); assert ext.argmax() == 1, 'head is not upright'
    if ext[2] > ext[0]: g.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    V = g.vertices; top_w = np.ptp(V[V[:, 1] > np.percentile(V[:, 1], 60), 0]); bot_w = np.ptp(V[V[:, 1] < np.percentile(V[:, 1], 15), 0])
    if bot_w > top_w: g.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [0, 0, 1]))       # blade must be the upper end
    # 2. scale: the head (blade, socket and stub) to the brief's height
    s = donor['head_height_m'] / np.ptp(g.vertices[:, 1]); g.apply_scale(s)
    V = g.vertices; y0 = V[:, 1].min(); stub = V[V[:, 1] < y0 + 0.06]                                   # the lowest 6 cm: the cut stub
    cx, cz = stub[:, 0].mean(), stub[:, 2].mean(); r = float(np.percentile(np.hypot(stub[:, 0] - cx, stub[:, 2] - cz), 90))
    tip_y, butt_y = donor['tip_y_m'], donor['butt_y_m']
    g.apply_translation([-cx, tip_y - V[:, 1].max(), -cz])                                              # tip where the donor's tip is, stub on the axis
    head_bottom = float(g.vertices[:, 1].min())
    # 3. clean-up of the head: fewer triangles, texture layout kept
    ms = pymeshlab.MeshSet(); ms.add_mesh(pymeshlab.Mesh(vertex_matrix=np.asarray(g.vertices, float), face_matrix=np.asarray(g.faces, np.int32), v_tex_coords_matrix=np.asarray(g.visual.uv, float)))
    before = ms.current_mesh().face_number(); ms.compute_texcoord_transfer_vertex_to_wedge()
    ms.meshing_decimation_quadric_edge_collapse_with_texture(targetfacenum=head_tris, qualitythr=0.5, extratcoordw=2.0, preserveboundary=True, optimalplacement=True, preservenormal=True)
    ms.compute_texcoord_transfer_wedge_to_vertex(); cm = ms.current_mesh()
    head = trimesh.Trimesh(cm.vertex_matrix(), cm.face_matrix(), process=False); head.visual = trimesh.visual.TextureVisuals(uv=cm.vertex_tex_coord_matrix(), material=g.visual.material)
    # 4. the shaft's wood: sampled from the stub's own patch of the head's texture, made to repeat
    tex = g.visual.material.baseColorTexture.convert('RGB'); W = tex.size[0]; T = np.asarray(tex, np.float32)
    low = g.vertices[:, 1] < head_bottom + 0.10; uv = np.asarray(g.visual.uv)[low]                    # the stub's own vertices
    col = T[np.clip(((1 - uv[:, 1]) * (W - 1)).astype(int), 0, W - 1), np.clip((uv[:, 0] * (W - 1)).astype(int), 0, W - 1)]
    lum = col @ [0.2126, 0.7152, 0.0722]; keep = (lum > np.percentile(lum, 20)) & (lum < np.percentile(lum, 80)); base = np.median(col[keep], axis=0); spread = float(lum[keep].std())
    rngw = np.random.default_rng(11); grain = np.asarray(Image.fromarray((rngw.random((512, 64)) * 255).astype(np.uint8)).resize((512, 512), Image.BICUBIC).filter(ImageFilter.GaussianBlur(1.5)), np.float32) / 255.0
    grain = (grain - grain.mean()) / (grain.std() + 1e-6); fine = (rngw.random((512, 512)) - 0.5) * 0.05                # streaks running along the pole
    A = np.clip(base[None, None, :] * (1 + (grain * min(spread / max(float(lum[keep].mean()), 1), 0.25) + fine))[..., None], 0, 255)
    B = np.roll(A, (256, 256), axis=(0, 1)); yy, xx = np.mgrid[0:512, 0:512]; d = np.minimum(np.minimum(xx, 511 - xx), np.minimum(yy, 511 - yy)) / 256.0
    m = np.clip((d - 0.08) / 0.3, 0, 1)[..., None]; wood = Image.fromarray(np.clip(A * m + B * (1 - m), 0, 255).astype(np.uint8))
    wood.save(f'{out}/shaft_wood.png')
    # 5. the shaft: a slightly uneven round pole from the donor's butt up into the stub, with a rounded butt and a sinew grip wrap
    n, rings = 14, 26; ys = np.linspace(butt_y, head_bottom + 0.04, rings); rng = np.random.default_rng(7)
    rad = r * 0.97 * (1 + 0.035 * np.sin(ys * 9.0) + 0.02 * rng.standard_normal(rings)); rad[0] *= 0.82
    bow = 0.006 * np.sin((ys - butt_y) / (ys[-1] - butt_y) * np.pi)                                    # a pole is never dead straight
    P, UV = [], []
    for i, y in enumerate(ys):
        for k in range(n + 1):
            a = 2 * np.pi * k / n; P.append([rad[i] * np.cos(a) + bow[i], y, rad[i] * np.sin(a)]); UV.append([k / n * 1.0, (y - butt_y) / (2 * np.pi * r) / 1.0])
    F = []
    for i in range(rings - 1):
        for k in range(n):
            a, b = i * (n + 1) + k, (i + 1) * (n + 1) + k; F += [[a, b + 1, b], [a, a + 1, b + 1]]
    c = len(P); P.append([bow[0], butt_y - r * 0.25, 0]); UV.append([0.5, 0]); F += [[c, k + 1, k] for k in range(n)]                    # the butt
    shaft = trimesh.Trimesh(np.array(P), np.array(F), process=False)
    shaft.visual = trimesh.visual.TextureVisuals(uv=np.array(UV), material=trimesh.visual.material.PBRMaterial(baseColorTexture=wood, metallicFactor=0.0, roughnessFactor=0.9))
    whole = trimesh.Scene(); whole.add_geometry(head, node_name='head'); whole.add_geometry(shaft, node_name='shaft'); whole.export(f'{out}/assembled.glb')
    allv = np.vstack([head.vertices, shaft.vertices])
    print(json.dumps({"scale_applied": round(float(s), 3), "stub_radius_m": round(r, 4), "shaft_radius_m": round(float(rad.mean()), 4), "head_triangles_before": int(before), "head_triangles": int(len(head.faces)), "shaft_triangles": int(len(shaft.faces)),
      "length_m": round(float(np.ptp(allv[:, 1])), 3), "donor_length_m": round(tip_y - butt_y, 3), "tip_y_m": round(float(allv[:, 1].max()), 3), "butt_y_m": round(float(allv[:, 1].min()), 3), "grip_at_origin": True,
      "shaft_wood_rgb": [int(x) for x in base], "blade_width_m": round(float(np.ptp(head.vertices[:, 0])), 3), "donor_blade_width_m": donor['blade_width_m'], "thickness_m": round(float(np.ptp(head.vertices[:, 2])), 3), "donor_thickness_m": donor['thickness_m']}))


# ---------------------------------------------------------------------------------------------------------------
# finish: the hybrid of the proposal's "Long-weapon shafts". The assembled weapon's generated head is kept as it is;
# the hand-made shaft is remade with a raised cord grip, a binding collar over the joint where it seats into the head's
# socket, wear painted along its own length, and two short generated end pieces (a bone butt cap and a carved grip band)
# seated by measurement on the shaft's real radius. Every piece is closed onto the shaft: nothing hangs.
# The triangle budget (default 3,200) is shared out so the whole stays inside what Skyrim's polearms carry: Animated
# Armoury's sixteen halberds measure 749 to 2,971 triangles, BM&V's staves and spears 180 to 3,909.
# usage: polearm.py finish assembled_dir donor.json buttcap.glb gripband.glb outdir [budget]

def tube(path, radius, sides=6):
    """A closed tube of `radius` along a polyline (a cord), its ends capped."""
    P = np.asarray(path, float); n = len(P); T = np.gradient(P, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
    up = np.where(np.abs(T[:, 1:2]) > 0.9, [[1.0, 0, 0]], [[0, 1.0, 0]]); N = np.cross(T, up); N /= np.linalg.norm(N, axis=1)[:, None]; B = np.cross(T, N)
    a = np.linspace(0, 2 * np.pi, sides, endpoint=False)
    V = (P[:, None, :] + radius * (np.cos(a)[None, :, None] * N[:, None, :] + np.sin(a)[None, :, None] * B[:, None, :])).reshape(-1, 3)
    F = []
    for i in range(n - 1):
        for k in range(sides):
            p, q = i * sides + k, i * sides + (k + 1) % sides; F += [[p, q, q + sides], [p, q + sides, p + sides]]
    c0, c1 = len(V), len(V) + 1; V = np.vstack([V, P[0], P[-1]])
    F += [[c0, (k + 1) % sides, k] for k in range(sides)] + [[c1, (n - 1) * sides + k, (n - 1) * sides + (k + 1) % sides] for k in range(sides)]
    return trimesh.Trimesh(V, np.array(F), process=False)


def helix(r, y0, y1, pitch, cord, sides=3, phase=0.0, per_turn=6):
    turns = (y1 - y0) / pitch; t = np.linspace(0, turns * 2 * np.pi, max(int(turns * per_turn), 8))
    return tube(np.column_stack([r * np.cos(t + phase), y0 + (y1 - y0) * t / t[-1], r * np.sin(t + phase)]), cord, sides)


def coloured(m, rgb, rough=0.95):
    m.visual = trimesh.visual.TextureVisuals(uv=np.zeros((len(m.vertices), 2)), material=trimesh.visual.material.PBRMaterial(
        baseColorTexture=Image.new('RGB', (4, 4), tuple(int(x) for x in rgb)), metallicFactor=0.0, roughnessFactor=rough)); return m


def end_piece(src, tris, fit):
    """A short generated piece, cut to `tris`, scaled so `fit(vertices)` (its measured size) becomes 1, socket axis on Y."""
    sc = trimesh.load(src, force='scene'); g = list(sc.geometry.values())[0].copy(); g.apply_transform(sc.graph.get(list(sc.graph.nodes_geometry)[0])[0])
    w = trimesh.Trimesh(g.vertices, g.faces, process=False); w.merge_vertices(merge_tex=True, merge_norm=True)
    lab = trimesh.graph.connected_component_labels(w.face_adjacency, node_count=len(w.faces)); area = np.bincount(lab, weights=w.area_faces)
    g.update_faces(np.isin(lab, np.where(area >= 0.01 * area.max())[0])); g.remove_unreferenced_vertices()
    m = cut(g, tris); c = m.vertices.mean(0); m.apply_translation([-c[0], 0, -c[2]]); m.apply_scale(1.0 / fit(m)); return m


def inner_radius(m, y):
    """The hole's radius at height y, from rays cast outward from the axis onto the piece's real triangles."""
    a = np.linspace(0, 2 * np.pi, 36, endpoint=False); O = np.column_stack([np.zeros(36), np.full(36, y), np.zeros(36)]); D = np.column_stack([np.cos(a), np.zeros(36), np.sin(a)])
    loc, ri, _ = m.ray.intersects_location(O, D, multiple_hits=False); d = np.hypot(loc[:, 0], loc[:, 2]); return float(np.median(d)) if len(d) > 18 else None


def cut(m, tris):
    """Fewer triangles, the texture layout kept, the surface whole: the mesh is welded by position first (its texture
    seams carried per corner), cut, then split again only where a corner's texture place differs, so a seam never
    opens into a crack."""
    w = trimesh.Trimesh(m.vertices, m.faces, process=False); uvw = np.asarray(m.visual.uv, float)[m.faces].reshape(-1, 2)
    w.merge_vertices(merge_tex=True, merge_norm=True)
    import tempfile
    with tempfile.TemporaryDirectory() as t:                           # an OBJ carries per-corner texture places and one texture, which MeshLab reads as wedges
        Image.new('RGB', (4, 4)).save(f'{t}/t.png'); open(f'{t}/m.mtl', 'w').write('newmtl m\nmap_Kd t.png\n')
        with open(f'{t}/m.obj', 'w') as f:
            f.write('mtllib m.mtl\nusemtl m\n'); f.writelines(f'v {x:.7f} {y:.7f} {z:.7f}\n' for x, y, z in w.vertices); f.writelines(f'vt {u:.7f} {v:.7f}\n' for u, v in uvw)
            f.writelines(f'f {a + 1}/{3 * i + 1} {b + 1}/{3 * i + 2} {c + 1}/{3 * i + 3}\n' for i, (a, b, c) in enumerate(w.faces))
        ms = pymeshlab.MeshSet(); ms.load_new_mesh(f'{t}/m.obj')
        ms.meshing_decimation_quadric_edge_collapse_with_texture(targetfacenum=tris, qualitythr=0.5, extratcoordw=2.0, preserveboundary=False, optimalplacement=True, preservenormal=True)
        cm = ms.current_mesh(); F = cm.face_matrix(); V = cm.vertex_matrix()[F].reshape(-1, 3); UV = cm.wedge_tex_coord_matrix()
    d = trimesh.Trimesh(V, np.arange(len(V)).reshape(-1, 3), process=False); d.visual = trimesh.visual.TextureVisuals(uv=UV, material=m.visual.material)
    d.merge_vertices(merge_tex=False, merge_norm=True); return d


def finish(adir, donor, cap_src, band_src, out, budget=3200):
    os.makedirs(out, exist_ok=True); sc = trimesh.load(f'{adir}/assembled.glb', force='scene')
    geo = {n: sc.geometry[sc.graph.get(n)[1]].copy() for n in sc.graph.nodes_geometry}
    for n in geo: geo[n].apply_transform(sc.graph.get(n)[0])
    head = geo['head']; asm = json.load(open(f'{adir}/assembly.json'))
    r = float(asm['shaft_radius_m']); butt_y = donor['butt_y_m']; hb = float(head.vertices[:, 1].min()); top = hb + 0.04
    # the head's own colours, measured: the sinew of its bindings is the middle of the socket band's texture (its darkest quarter is shadow)
    tex = np.asarray(head.visual.material.baseColorTexture.convert('RGB'), np.float32); W = tex.shape[0]; uv = np.asarray(head.visual.uv)
    band = (head.vertices[:, 1] > hb + 0.04) & (head.vertices[:, 1] < hb + 0.22)
    col = tex[np.clip(((1 - uv[band, 1]) * (W - 1)).astype(int), 0, W - 1), np.clip((uv[band, 0] * (W - 1)).astype(int), 0, W - 1)]
    lum = col @ [0.2126, 0.7152, 0.0722]; sinew = np.median(col[(lum > np.percentile(lum, 30)) & (lum < np.percentile(lum, 60))], axis=0)
    # 1. the butt cap: its socket's measured inner radius made the shaft's, its bottom at the donor's butt
    head = cut(head, int(budget * 0.55)) if len(head.faces) > budget * 0.55 else head
    cap = end_piece(cap_src, int(budget * 0.07), lambda m: 1.0)
    ys = np.linspace(cap.vertices[:, 1].max() - 0.02 * np.ptp(cap.vertices[:, 1]), cap.vertices[:, 1].max() - 0.25 * np.ptp(cap.vertices[:, 1]), 6)
    ir = [x for x in (inner_radius(cap, y) for y in ys) if x]; k = (r * 1.03) / float(np.median(ir)); cap.apply_scale(k)
    cap.apply_translation([0, butt_y - cap.vertices[:, 1].min(), 0]); cap_top = float(cap.vertices[:, 1].max())
    # 2. the shaft, from inside the cap up into the head's stub, wood unique along its length so wear can be painted where it falls
    L = top - (cap_top - 0.05); n, rings = 10, 24; ys = np.linspace(cap_top - 0.05, top, rings); rng = np.random.default_rng(7)
    rad = r * (1 + 0.03 * np.sin(ys * 9.0) + 0.015 * rng.standard_normal(rings)); bow = 0.006 * np.sin((ys - ys[0]) / L * np.pi)
    P, UV = [], []
    for i, y in enumerate(ys):
        for kk in range(n + 1):
            a = 2 * np.pi * kk / n; P.append([rad[i] * np.cos(a) + bow[i], y, rad[i] * np.sin(a)]); UV.append([kk / n, 1 - (y - ys[0]) / L])
    F = [[i * (n + 1) + kk, (i + 1) * (n + 1) + kk + 1, (i + 1) * (n + 1) + kk] for i in range(rings - 1) for kk in range(n)] + [[i * (n + 1) + kk, i * (n + 1) + kk + 1, (i + 1) * (n + 1) + kk + 1] for i in range(rings - 1) for kk in range(n)]
    shaft = trimesh.Trimesh(np.array(P), np.array(F), process=False)
    grain = np.asarray(Image.open(f'{adir}/shaft_wood.png').convert('RGB'), np.float32)               # the assembled shaft's own wood
    H = 2048; strip = np.vstack([grain[:, :64]] * (H // grain.shape[0])); wood = np.asarray(Image.fromarray(strip.astype(np.uint8)).resize((256, H), Image.BICUBIC), np.float32)
    yy = ys[0] + (1 - (np.arange(H) + 0.5) / H) * L                                                  # each texture row's height on the weapon
    g0, g1 = -0.17, 0.36                                                                               # the grip: the hands' span about the origin
    polish = np.exp(-((yy - (g0 + g1) / 2) / ((g1 - g0) * 0.8)) ** 4)[:, None, None]                  # handled wood: smoother and a shade lighter
    dirt = np.clip(1 - (yy - butt_y) / 0.35, 0, 1)[:, None, None] ** 1.5                               # the butt end: grounded, dark with mud
    sweat = np.exp(-((yy - 0.0) / 0.25) ** 2)[:, None, None]                                           # under the hands: darkened by use
    w = wood * (1 + 0.10 * polish) * (1 - 0.35 * dirt) * (1 - 0.15 * sweat)
    blur = np.asarray(Image.fromarray(np.clip(w, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)), np.float32); w = w * (1 - 0.5 * polish) + blur * 0.5 * polish
    nick = np.random.default_rng(3)
    for _ in range(70):                                                                                # knocks and scrapes: short dark gouges with a pale edge
        x0, y0 = int(nick.integers(0, 256)), int(nick.integers(0, H)); l = int(nick.integers(4, 18)); t = nick.uniform(-0.6, 0.6)
        for j in range(l):
            xx, yv = (x0 + j) % 256, int(np.clip(y0 + j * t, 0, H - 1)); w[yv, xx] *= 0.55; w[max(yv - 1, 0), xx] = np.minimum(w[max(yv - 1, 0), xx] * 1.25, 255)
    shaft.visual = trimesh.visual.TextureVisuals(uv=np.array(UV), material=trimesh.visual.material.PBRMaterial(baseColorTexture=Image.fromarray(np.clip(w, 0, 255).astype(np.uint8)), metallicFactor=0.0, roughnessFactor=0.85))
    # 3. the raised cord grip: two cords wound tight over the grip span, real geometry, sinew-coloured, ends tucked under the turns
    cord = 0.0042; grip = helix(r + cord * 0.7, g0, g1, cord * 5.0, cord); coloured(grip, sinew * 0.92)
    # 4. the binding collar: a dense wrap over the joint where the shaft seats into the head's socket
    sr = float(np.percentile(np.hypot(head.vertices[np.abs(head.vertices[:, 1] - hb) < 0.03, 0], head.vertices[np.abs(head.vertices[:, 1] - hb) < 0.03, 2]), 90))
    collar = helix(max(sr, r) + cord * 0.8, hb - 0.035, hb + 0.03, cord * 3.0, cord); coloured(collar, sinew)
    # 5. the grip band: its hole's measured radius made the shaft's (over the cord), seated at the top of the grip
    band_m = end_piece(band_src, int(budget * 0.07), lambda m: 1.0); hr = inner_radius(band_m, float(band_m.vertices[:, 1].mean())); band_m.apply_scale((r + 2 * cord) * 1.02 / hr)
    band_m.apply_translation([0, g1 + 0.005 - band_m.vertices[:, 1].min(), 0])
    whole = trimesh.Scene()
    for nm, m in (('head', head), ('shaft', shaft), ('grip_cord', grip), ('collar', collar), ('butt_cap', cap), ('grip_band', band_m)): whole.add_geometry(m, node_name=nm)
    whole.export(f'{out}/finished.glb')
    allv = np.vstack([m.vertices for m in (head, shaft, grip, collar, cap, band_m)])
    res = {"length_m": round(float(np.ptp(allv[:, 1])), 3), "donor_length_m": round(donor['tip_y_m'] - donor['butt_y_m'], 3), "tip_y_m": round(float(allv[:, 1].max()), 3), "butt_y_m": round(float(allv[:, 1].min()), 3),
           "shaft_radius_m": r, "socket_radius_at_joint_m": round(sr, 4), "grip_m": [g0, g1], "cord_radius_m": cord, "sinew_rgb": [int(x) for x in sinew],
           "butt_cap": {"height_m": round(float(np.ptp(cap.vertices[:, 1])), 3), "across_m": round(float(np.ptp(cap.vertices[:, 0])), 3), "socket_inner_radius_m": round(float(np.median(ir)) * k, 4)},
           "grip_band": {"height_m": round(float(np.ptp(band_m.vertices[:, 1])), 3), "across_m": round(float(np.ptp(band_m.vertices[:, 0])), 3), "hole_radius_m": round(hr * (r + 2 * cord) * 1.02 / hr, 4)},
           "triangles": {"head": len(head.faces), "shaft": len(shaft.faces), "grip_cord": len(grip.faces), "collar": len(collar.faces), "butt_cap": len(cap.faces), "grip_band": len(band_m.faces), "total": int(sum(len(m.faces) for m in (head, shaft, grip, collar, cap, band_m)))}}
    json.dump(res, open(f'{out}/finish.json', 'w'), indent=1); return res


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'finish':
    print(json.dumps(finish(sys.argv[2], json.load(open(sys.argv[3])), sys.argv[4], sys.argv[5], sys.argv[6], int(sys.argv[7]) if len(sys.argv) > 7 else 3200)))


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] != 'finish':
    assemble()
