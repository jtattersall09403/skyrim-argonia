"""Stage: shaping and clean-up of the chosen generation. Aligns to its own axes from the real vertices, scales to the
brief's length, reduces triangles keeping the texture layout, writes GLBs. usage: shape.py in.glb outdir length_m target_tris"""
import sys, json, numpy as np, trimesh, pymeshlab, os
src, outdir, L, target = sys.argv[1], sys.argv[2], float(sys.argv[3]), int(sys.argv[4])
os.makedirs(outdir, exist_ok=True)
sc = trimesh.load(src, force='scene'); g = list(sc.geometry.values())[0]
T = sc.graph.get(list(sc.graph.nodes_geometry)[0])[0]
g = g.copy(); g.apply_transform(T)
V = g.vertices - g.vertices.mean(0)
# principal axes from the actual vertices (area-weighted would be finer; vertices are dense and even here)
w, E = np.linalg.eigh(np.cov(V.T)); order = np.argsort(w)[::-1]; E = E[:, order]      # long, wide, thin
if np.linalg.det(E) < 0: E[:, 2] *= -1
R = np.eye(4); R[:3, :3] = np.stack([E[:, 0], E[:, 2], E[:, 1]])                      # x = length, y = up (thin), z = beam
g.apply_translation(-g.vertices.mean(0)); g.apply_transform(R)
if np.linalg.det(R[:3,:3]) < 0: g.invert()
# which way is up: the hollow opens upward, so vertex normals near the middle of the hull's inside point up; use the
# open side = the side where the mean of vertices lies further from the extreme (the rim is wide, the keel narrow)
ys = g.vertices[:, 1]; top, bot = ys.max(), ys.min()
band = (np.abs(g.vertices[:, 0]) < 0.3 * np.ptp(g.vertices[:, 0]))
wt = np.ptp(g.vertices[band & (ys > top - 0.15 * (top - bot)), 2]); wb = np.ptp(g.vertices[band & (ys < bot + 0.15 * (top - bot)), 2])
flipped = bool(wb > wt)
if flipped:
    F = trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]); g.apply_transform(F)
s = L / np.ptp(g.vertices[:, 0]); g.apply_scale(s)
g.apply_translation([-g.vertices[:, 0].mean() * 0 - (g.vertices[:, 0].max() + g.vertices[:, 0].min()) / 2, -g.vertices[:, 1].min(), -(g.vertices[:, 2].max() + g.vertices[:, 2].min()) / 2])
g.export(f'{outdir}/aligned.glb')
# clean-up: reduce triangles, texture layout kept
tex = g.visual.material.baseColorTexture; tex.convert('RGB').save(f'{outdir}/_base.png')
uv0 = np.asarray(g.visual.uv, dtype=np.float64)
ms = pymeshlab.MeshSet(); ms.add_mesh(pymeshlab.Mesh(vertex_matrix=np.asarray(g.vertices, dtype=np.float64), face_matrix=np.asarray(g.faces, dtype=np.int32), v_tex_coords_matrix=uv0))
before = ms.current_mesh().face_number()
ms.compute_texcoord_transfer_vertex_to_wedge()
ms.meshing_decimation_quadric_edge_collapse_with_texture(targetfacenum=target, qualitythr=0.5, extratcoordw=2.0, preserveboundary=True, optimalplacement=True, preservenormal=True, planarquadric=True)
ms.compute_texcoord_transfer_wedge_to_vertex()
cm = ms.current_mesh()
d = trimesh.Trimesh(cm.vertex_matrix(), cm.face_matrix(), process=False)
d.visual = trimesh.visual.TextureVisuals(uv=cm.vertex_tex_coord_matrix(), material=g.visual.material)
d.export(f'{outdir}/cleaned.glb')
print(json.dumps({"scale_applied": round(float(s), 4), "flipped_upright": flipped, "triangles_before": int(before), "triangles_after": int(len(d.faces)),
                  "size_m": [round(float(x), 3) for x in np.ptp(d.vertices, axis=0)]}))
