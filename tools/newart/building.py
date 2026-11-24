"""Stage: shaping a generated building shell. Removes loose pieces, finds the painted door on the REAL geometry (the
largest flat patch facing out at ground level), scales the whole shell so that door is door-sized, stands it on the
ground, cuts triangles keeping the texture layout, and makes the invisible door plate to the door's own outline, a
hair in front of it, with the point a visitor arrives at. usage: building.py shell.glb outdir door_height_m tris"""
import sys, json, os, numpy as np, trimesh, pymeshlab
from scipy.spatial import ConvexHull
src, out, door_h, tris = sys.argv[1], sys.argv[2], float(sys.argv[3]), int(sys.argv[4]); os.makedirs(out, exist_ok=True)
sc = trimesh.load(src, force='scene'); g = list(sc.geometry.values())[0].copy(); g.apply_transform(sc.graph.get(list(sc.graph.nodes_geometry)[0])[0])
mat = g.visual.material
# 1. loose pieces: keep the main body (pieces under 1% of its area go)
w = trimesh.Trimesh(g.vertices, g.faces, process=False); w.merge_vertices(merge_tex=True, merge_norm=True)          # joined by position, so texture seams do not count as breaks
assert len(w.faces) == len(g.faces); lab = trimesh.graph.connected_component_labels(w.face_adjacency, node_count=len(w.faces))
area = np.bincount(lab, weights=w.area_faces); keep = np.isin(lab, np.where(area >= 0.01 * area.max())[0]); removed = int(len(area) - (area >= 0.01 * area.max()).sum())
g.update_faces(keep); g.remove_unreferenced_vertices(); w.update_faces(keep)
adj = w.face_adjacency
# 2. the door: faces that are near-vertical, in the lower half, and flat together; candidates on every side, the largest flat patch wins
V, F, n, a = g.vertices, g.faces, g.face_normals, g.area_faces; c = g.triangles_center; H = np.ptp(V[:, 1]); y0 = V[:, 1].min(); ctr = V.mean(0)
best = None
for ang in np.linspace(0, 2 * np.pi, 72, endpoint=False):
    d = np.array([np.cos(ang), 0, np.sin(ang)]); m = (n @ d > 0.93) & (c[:, 1] < y0 + 0.5 * H)
    if m.sum() < 20: continue
    depth = c[m] @ d; hist, edges = np.histogram(depth, bins=40, weights=a[m]); k = hist.argmax(); sel = m.copy(); sel[m] = np.abs(depth - (edges[k] + edges[k + 1]) / 2) < H * 0.02
    idx = np.where(sel)[0]; pos = -np.ones(len(sel), int); pos[idx] = np.arange(len(idx)); e = adj[sel[adj[:, 0]] & sel[adj[:, 1]]]
    if len(e) == 0: continue
    cl = trimesh.graph.connected_component_labels(pos[e], node_count=len(idx)); big = np.bincount(cl, weights=a[idx]).argmax(); sel = np.zeros(len(sel), bool); sel[idx[cl == big]] = True   # one joined flat patch
    score = a[sel].sum()
    if best is None or score > best[0]: best = (score, ang, d, sel)
score, ang, d, sel = best
# the strict patch is one plank; grow it over the neighbouring faces that face the same way at the same depth: the whole door, planks and grooves
dm = float(np.median(c[sel] @ d)); cand = (n @ d > 0.55) & (np.abs(c @ d - dm) < H * 0.035) & (c[:, 1] < y0 + 0.55 * H)
grown = sel.copy()
for _ in range(60):
    e = adj[(grown[adj[:, 0]] ^ grown[adj[:, 1]])]; new = np.unique(e[cand[e] & ~grown[e]])
    if len(new) == 0: break
    grown[new] = True
strict_area = float(a[sel].sum()); sel = grown; score = float(a[sel].sum())
side = np.cross([0, 1, 0], d); P = V[np.unique(F[sel])]; u, v = P @ side, P[:, 1]
u0, u1 = np.percentile(u, 2), np.percentile(u, 98); v0, v1 = np.percentile(v, 2), np.percentile(v, 98); depth_face = float(np.median(P @ d))
# 3. scale by the door, turn the door to face +X, stand the shell on the ground at the middle
s = door_h / (v1 - y0)                                                     # the doorway runs from the ground to the top of the plank patch
R = trimesh.transformations.rotation_matrix(ang, [0, 1, 0]); g.apply_transform(R); g.apply_scale(s)
b = g.bounds; g.apply_translation([-(b[0][0] + b[1][0]) / 2, -b[0][1], -(b[0][2] + b[1][2]) / 2])
# recompute the door patch on the transformed mesh (same faces)
selk = sel
Pd = g.vertices[np.unique(g.faces[selk])]; xf = float(np.percentile(Pd[:, 0], 90)); zy = Pd[:, [2, 1]]
zy = np.vstack([zy, [[np.percentile(zy[:, 0], 3), 0.0], [np.percentile(zy[:, 0], 97), 0.0]]])       # a doorway reaches the ground
hull = ConvexHull(zy); outline = zy[hull.vertices]
zc = float(outline[:, 0].mean()); outline[:, 1] = np.maximum(outline[:, 1], 0.0)
# 4. clean-up: fewer triangles, texture layout kept
ms = pymeshlab.MeshSet(); ms.add_mesh(pymeshlab.Mesh(vertex_matrix=np.asarray(g.vertices, float), face_matrix=np.asarray(g.faces, np.int32), v_tex_coords_matrix=np.asarray(g.visual.uv, float)))
before = ms.current_mesh().face_number(); ms.compute_texcoord_transfer_vertex_to_wedge()
ms.meshing_decimation_quadric_edge_collapse_with_texture(targetfacenum=tris, qualitythr=0.5, extratcoordw=2.0, preserveboundary=True, optimalplacement=True, preservenormal=True)
ms.compute_texcoord_transfer_wedge_to_vertex(); cm = ms.current_mesh()
shell = trimesh.Trimesh(cm.vertex_matrix(), cm.face_matrix(), process=False); shell.visual = trimesh.visual.TextureVisuals(uv=cm.vertex_tex_coord_matrix(), material=mat)
# 5. the door plate: the door's own outline, 2 cm thick, 4 cm in front of the painted door; shown here in orange, invisible in the game
from shapely.geometry import Polygon
poly = Polygon(outline).buffer(0); plate = trimesh.creation.extrude_polygon(poly, 0.02)
T = np.array([[0, 0, 1, xf + 0.04], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1]], float)        # polygon (z, y) -> world; extrusion along +X
plate.apply_transform(T); plate.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(baseColorFactor=[255, 150, 40, 110], alphaMode='BLEND', metallicFactor=0.0, roughnessFactor=1.0))
arrive = [round(xf + 1.3, 3), 0.0, round(zc, 3)]
S = trimesh.Scene(); S.add_geometry(shell, node_name='shell'); S.export(f'{out}/shell.glb')
S2 = trimesh.Scene(); S2.add_geometry(shell, node_name='shell'); S2.add_geometry(plate, node_name='door_plate')
mk = trimesh.creation.cylinder(radius=0.18, height=0.03, sections=20); mk.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])); mk.apply_translation(arrive[:1] + [0.02] + arrive[2:])
mk.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(baseColorFactor=[255, 150, 40, 255], metallicFactor=0.0, roughnessFactor=1.0)); S2.add_geometry(mk, node_name='arrival'); S2.export(f'{out}/shell_with_door.glb')
sz = np.ptp(shell.vertices, axis=0)
print(json.dumps({"loose_pieces_removed": removed, "scale_applied": round(float(s), 3), "triangles_before": int(before), "triangles": int(len(shell.faces)), "size_m": {"across_the_door": round(float(sz[2]), 2), "front_to_back": round(float(sz[0]), 2), "high": round(float(sz[1]), 2)},
  "door": {"strict_patch_m2": round(strict_area * s * s, 2), "faces_in_patch": int(selk.sum()), "patch_area_m2": round(float(score * s * s), 2), "width_m": round(float(np.ptp(outline[:, 0])), 2), "height_m": round(float(outline[:, 1].max()), 2), "outline_points": int(len(outline)), "plate_in_front_m": 0.04, "arrival_point": arrive},
  "pixels_per_metre": round(float(mat.baseColorTexture.size[0] / np.sqrt(shell.area)), 0)}))
