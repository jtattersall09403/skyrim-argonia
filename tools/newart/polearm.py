"""Stage: shaping a pole weapon that acts as an existing one. The generator makes only the head; the shaft is made here
from simple shapes, to the DONOR's own measurements (grip at the origin, butt and tip where the donor's are), and takes
its wood colour, measured, from the head's own stub so the two match. Everything is measured on the real vertices.
usage: polearm.py head.glb outdir donor.json head_tris"""
import sys, json, os, numpy as np, trimesh, pymeshlab
from PIL import Image, ImageFilter
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
