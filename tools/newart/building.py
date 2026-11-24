"""Stage: shaping a generated building shell, with its door marked by hand. Three steps:

  building.py shell  gen.glb  outdir tris          loose pieces off, triangles cut (texture layout kept), stood on the
                                                    ground; writes outdir/shell_raw.glb, still in the generator's unit
  building.py view   outdir [side]                 draws the four elevations (sides 0-3, looking in at the shell along
                                                    -X after turning it by side x 90 degrees) as flat surfaced pictures
                                                    with a grid, on the shell's real triangles; the agent looks and
                                                    chooses the side with the painted door
  building.py door   outdir side door_h_m  "z,y z,y ..."
                                                    the door as the agent marked it on that side's elevation (points in
                                                    the elevation's own unit, z across, y up, from the picture's grid);
                                                    turns the shell so that side faces +X, scales it so the marked door
                                                    is door_h_m high, lays the door plate on the real surface there (a
                                                    hair in front of the proudest part inside the outline, so a bar or
                                                    sill never stands in front of it) with the arrival point 1.3 m out,
                                                    and draws the side view that checks it

Nothing finds the door automatically: the agent marks it by eye. Every height and depth is measured on the real
triangles by casting rays, never from a bounding box."""
import sys, json, os, numpy as np, trimesh, pymeshlab
from PIL import Image, ImageDraw


def load_one(src):
    sc = trimesh.load(src, force='scene'); g = list(sc.geometry.values())[0].copy()
    g.apply_transform(sc.graph.get(list(sc.graph.nodes_geometry)[0])[0]); return g


def shell(src, out, tris):
    os.makedirs(out, exist_ok=True); g = load_one(src); mat = g.visual.material
    w = trimesh.Trimesh(g.vertices, g.faces, process=False); w.merge_vertices(merge_tex=True, merge_norm=True)
    lab = trimesh.graph.connected_component_labels(w.face_adjacency, node_count=len(w.faces))
    area = np.bincount(lab, weights=w.area_faces); keep = np.isin(lab, np.where(area >= 0.01 * area.max())[0])
    removed = int(len(area) - (area >= 0.01 * area.max()).sum()); g.update_faces(keep); g.remove_unreferenced_vertices()
    ms = pymeshlab.MeshSet(); ms.add_mesh(pymeshlab.Mesh(vertex_matrix=np.asarray(g.vertices, float), face_matrix=np.asarray(g.faces, np.int32), v_tex_coords_matrix=np.asarray(g.visual.uv, float)))
    before = ms.current_mesh().face_number(); ms.compute_texcoord_transfer_vertex_to_wedge()
    ms.meshing_decimation_quadric_edge_collapse_with_texture(targetfacenum=tris, qualitythr=0.5, extratcoordw=2.0, preserveboundary=True, optimalplacement=True, preservenormal=True)
    ms.compute_texcoord_transfer_wedge_to_vertex(); cm = ms.current_mesh()
    s = trimesh.Trimesh(cm.vertex_matrix(), cm.face_matrix(), process=False); s.visual = trimesh.visual.TextureVisuals(uv=cm.vertex_tex_coord_matrix(), material=mat)
    b = s.bounds; s.apply_translation([-(b[0][0] + b[1][0]) / 2, -b[0][1], -(b[0][2] + b[1][2]) / 2])
    s.export(f'{out}/shell_raw.glb')
    return {"loose_pieces_removed": removed, "triangles_before": int(before), "triangles": int(len(s.faces))}


def turned(g, side):
    g = g.copy(); g.apply_transform(trimesh.transformations.rotation_matrix(side * np.pi / 2, [0, 1, 0])); return g


def elevation(g, px=420):
    """Flat surfaced picture of the +X face, looking along -X: one ray per pixel onto the real triangles."""
    b = g.bounds; z0, z1, y0, y1 = b[0][2], b[1][2], b[0][1], b[1][1]; pad = 0.04 * max(z1 - z0, y1 - y0)
    z0, z1, y0, y1 = z0 - pad, z1 + pad, y0 - pad, y1 + pad; W = px; H = int(px * (y1 - y0) / (z1 - z0))
    zz, yy = np.meshgrid(np.linspace(z0, z1, W), np.linspace(y1, y0, H))
    O = np.stack([np.full(zz.size, b[1][0] + 1.0), yy.ravel(), zz.ravel()], 1); D = np.tile([-1.0, 0, 0], (len(O), 1))
    loc, ri, ti = g.ray.intersects_location(O, D, multiple_hits=False)
    img = np.full((H * W, 3), 90, np.uint8); depth = np.full(H * W, np.nan)
    tex = np.asarray(g.visual.material.baseColorTexture.convert('RGB')); th, tw = tex.shape[:2]
    bc = trimesh.triangles.points_to_barycentric(g.triangles[ti], loc); uv = np.einsum('ij,ijk->ik', bc, g.visual.uv[g.faces[ti]])
    img[ri] = tex[np.clip(((1 - uv[:, 1] % 1) * (th - 1)).astype(int), 0, th - 1), np.clip((uv[:, 0] % 1 * (tw - 1)).astype(int), 0, tw - 1)]
    depth[ri] = loc[:, 0]
    return img.reshape(H, W, 3), depth.reshape(H, W), (z0, z1, y0, y1)


def gridded(img, frame, step):
    z0, z1, y0, y1 = frame; H, W = img.shape[:2]; im = Image.fromarray(img).resize((W * 2, H * 2)); d = ImageDraw.Draw(im)
    X = lambda z: (z - z0) / (z1 - z0) * W * 2; Y = lambda y: (y1 - y) / (y1 - y0) * H * 2
    for z in np.arange(np.ceil(z0 / step) * step, z1, step): d.line([(X(z), 0), (X(z), H * 2)], fill=(255, 255, 0), width=1); d.text((X(z) + 2, 2), f'{z:.2f}', fill=(255, 255, 0))
    for y in np.arange(np.ceil(y0 / step) * step, y1, step): d.line([(0, Y(y)), (W * 2, Y(y))], fill=(0, 255, 255), width=1); d.text((2, Y(y) + 2), f'{y:.2f}', fill=(0, 255, 255))
    return im, X, Y, d


def view(out, sides):
    g = load_one(f'{out}/shell_raw.glb'); step = round(float(np.ptp(g.vertices[:, 1])) / 10, 3)
    for s in sides:
        img, _, frame = elevation(turned(g, s)); im, *_ = gridded(img, frame, step); im.save(f'{out}/elevation_{s}.png')
    return {"elevations": [f'{out}/elevation_{s}.png' for s in sides], "grid_step": step}


def door(out, side, door_h, pts):
    from shapely.geometry import Polygon, Point
    g = turned(load_one(f'{out}/shell_raw.glb'), side); P = np.array(pts, float)                   # (z, y) in the raw unit
    poly = Polygon(P).buffer(0); zmin, ymin, zmax, ymax = poly.bounds
    # the marked door's own surface: one ray per 1/200 of its height inside the outline, onto the real triangles
    n = 200; zz, yy = np.meshgrid(np.linspace(zmin, zmax, n), np.linspace(ymin, ymax, n)); inside = np.array([poly.contains(Point(z, y)) for z, y in zip(zz.ravel(), yy.ravel())])
    O = np.stack([np.full(inside.sum(), g.bounds[1][0] + 1.0), yy.ravel()[inside], zz.ravel()[inside]], 1)
    loc, ri, _ = g.ray.intersects_location(O, np.tile([-1.0, 0, 0], (len(O), 1)), multiple_hits=False)
    assert len(loc) > 0.8 * len(O), f'only {len(loc)} of {len(O)} rays inside the outline met the shell: the mark is off the building'
    s = door_h / (ymax - g.bounds[0][1])                   # the doorway runs from the ground to the top of the mark
    g.apply_scale(s); b = g.bounds; shift = np.array([-(b[0][0] + b[1][0]) / 2, -b[0][1], -(b[0][2] + b[1][2]) / 2]); g.apply_translation(shift)
    hx = loc[:, 0] * s + shift[0]; face = float(np.median(hx))
    inner = poly.buffer(-0.08 * (zmax - zmin)); leaf = np.array([inner.contains(Point(z, y)) and y > ymin + 0.10 * (ymax - ymin) for z, y in zip(O[ri, 2], O[ri, 1])])
    hy = loc[:, 1] * s + shift[1]; kb, ka = np.polyfit(hy[leaf], hx[leaf], 1)          # the leaf's own lean: x = ka + kb * y
    off = float(np.percentile(hx[leaf] - (ka + kb * hy[leaf]), 99.5)) + 0.02             # in front of its proudest part (bars, sill), not the frame's roots
    xat = lambda y: ka + kb * y + off
    outline = np.column_stack([P[:, 0] * s + shift[2], np.maximum(P[:, 1] * s + shift[1], 0.0)])
    plate = trimesh.creation.extrude_polygon(Polygon(outline).buffer(0), 0.02)
    plate.apply_transform(np.array([[0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1]], float))
    v = plate.vertices.copy(); v[:, 0] += xat(v[:, 1]); plate.vertices = v                 # the plate leans with the door
    plate.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(baseColorFactor=[255, 150, 40, 110], alphaMode='BLEND', metallicFactor=0.0, roughnessFactor=1.0))
    zc = float(outline[:, 0].mean()); proud = float(xat(0.0)); arrive = [round(proud + 1.3, 3), 0.0, round(zc, 3)]
    gap = hx[leaf] - xat(hy[leaf])                                                       # every leaf ray: how far behind the plate the painted door is
    mk = trimesh.creation.cylinder(radius=0.18, height=0.03, sections=20); mk.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])); mk.apply_translation([arrive[0], 0.02, arrive[2]])
    mk.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(baseColorFactor=[255, 150, 40, 255], metallicFactor=0.0, roughnessFactor=1.0))
    S = trimesh.Scene(); S.add_geometry(g, node_name='shell'); S.export(f'{out}/shell.glb')
    S.add_geometry(plate, node_name='door_plate'); S.add_geometry(mk, node_name='arrival'); S.export(f'{out}/shell_with_door.glb')
    # the check from the side: a section through the door's middle, the shell's real surface and the plate in front of it
    img, depth, frame = elevation(turned(g, 1)); im, X, Y, d = gridded(img, frame, 0.5)
    yl = np.linspace(0, outline[:, 1].max(), 60); O = np.stack([np.full(60, g.bounds[1][0] + 1.0), yl, np.full(60, zc)], 1)
    hit, ri, _ = g.ray.intersects_location(O, np.tile([-1.0, 0, 0], (60, 1)), multiple_hits=False)
    sec = Image.new('RGB', (600, 600), (40, 40, 40)); sd = ImageDraw.Draw(sec); R = max(3.0, outline[:, 1].max() * 1.2)
    SX = lambda x: 300 + (x - face) / R * 560; SY = lambda y: 580 - y / R * 560
    for p in hit: sd.ellipse([SX(p[0]) - 2, SY(p[1]) - 2, SX(p[0]) + 2, SY(p[1]) + 2], fill=(200, 200, 200))
    ytop = float(outline[:, 1].max()); sd.polygon([(SX(xat(0)), SY(0)), (SX(xat(ytop)), SY(ytop)), (SX(xat(ytop) + 0.02), SY(ytop)), (SX(xat(0) + 0.02), SY(0))], fill=(255, 150, 40)); sd.ellipse([SX(arrive[0]) - 6, SY(0) - 6, SX(arrive[0]) + 6, SY(0) + 6], fill=(255, 150, 40))
    sd.text((8, 8), 'section through the door, seen from the side: grey = the shell surface, orange = plate and arrival', fill=(255, 255, 255)); sec.save(f'{out}/door_section.png')
    fr, _, ffr = elevation(g); fim, FX, FY, fd = gridded(fr, ffr, 0.5); fd.polygon([(FX(z), FY(y)) for z, y in outline], outline=(255, 150, 40), width=3); fim.save(f'{out}/door_front.png')
    sz = np.ptp(g.vertices, axis=0)
    return {"side": side, "scale_applied": round(float(s), 3), "size_m": {"across_the_door": round(float(sz[2]), 2), "front_to_back": round(float(sz[0]), 2), "high": round(float(sz[1]), 2)},
            "door": {"width_m": round(float(np.ptp(outline[:, 0])), 2), "height_m": round(float(outline[:, 1].max()), 2), "outline_points": int(len(outline)), "rays_on_door": int(len(loc)),
                     "door_surface_depth_spread_m": round(float(np.ptp(hx)), 3), "door_lean_m_per_m": round(float(kb), 3), "plate_in_front_of_leaf_m": {"min": round(float(-gap.max()), 3), "median": round(float(np.median(-gap)), 3), "max": round(float(-gap.min()), 3)}, "arrival_point": arrive},
            "pixels_per_metre": round(float(g.visual.material.baseColorTexture.size[0] / np.sqrt(g.area)), 0)}


if __name__ == '__main__':
    a = sys.argv
    if a[1] == 'shell': r = shell(a[2], a[3], int(a[4]))
    elif a[1] == 'view': r = view(a[2], [int(a[3])] if len(a) > 3 else [0, 1, 2, 3])
    elif a[1] == 'door': r = door(a[2], int(a[3]), float(a[4]), [tuple(map(float, p.split(','))) for p in a[5].split()])
    print(json.dumps(r))
