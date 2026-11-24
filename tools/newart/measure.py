"""Measure a GLB: the numbers half of measure-and-look. usage: measure.py file.glb [--json]"""
import sys, json, numpy as np, trimesh
def measure(path):
    sc = trimesh.load(path, force='scene')
    geoms = list(sc.geometry.values())
    m = sc.to_geometry() if hasattr(sc,'to_geometry') else trimesh.util.concatenate(sc.dump())
    out = {"file": path.split('/')[-1], "meshes": len(geoms), "vertices": int(len(m.vertices)), "triangles": int(len(m.faces))}
    ext = m.bounds[1]-m.bounds[0]
    out["size_m"] = [round(float(x),3) for x in ext]; out["bounds"] = [[round(float(x),3) for x in b] for b in m.bounds]
    mm = trimesh.Trimesh(m.vertices, m.faces, process=True)   # merged by position, for topology
    mm.merge_vertices()
    comps = mm.split(only_watertight=False)
    areas = sorted([float(c.area) for c in comps], reverse=True)
    out["welded_vertices"] = int(len(mm.vertices)); out["components"] = len(comps)
    out["small_components"] = int(sum(1 for a in areas[1:] if a < 0.01*areas[0])) if areas else 0
    out["largest_component_area_share"] = round(areas[0]/sum(areas),4) if areas else None
    out["watertight"] = bool(mm.is_watertight)
    e = mm.edges_sorted; u, c = np.unique(e, axis=0, return_counts=True)
    out["open_edges"] = int((c==1).sum()); out["non_manifold_edges"] = int((c>2).sum())
    a = mm.area_faces; out["degenerate_faces"] = int((a < 1e-12).sum())
    out["surface_m2"] = round(float(mm.area),3)
    tex = []
    for g in geoms:
        mat = getattr(g.visual,'material',None)
        for k in ('baseColorTexture','metallicRoughnessTexture','normalTexture','emissiveTexture','occlusionTexture','image'):
            im = getattr(mat,k,None) if mat is not None else None
            if im is not None: tex.append({"map":k,"px":list(im.size)})
        out["has_uv"] = bool(getattr(g.visual,'uv',None) is not None)
    out["textures"] = tex
    if tex and out["surface_m2"]>0:
        px = tex[0]["px"][0]; out["texels_per_m_if_uv_full"] = round(px/ (out["surface_m2"]**0.5),1)
    return out
if __name__ == "__main__":
    print(json.dumps(measure(sys.argv[1]), indent=1))
