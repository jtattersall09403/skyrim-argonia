"""Stage: put a generation into true metres before anyone looks at it. Generators return a model in their own unit
(most fit it into a 1-unit box), so an unscaled generation beside a 1.8 m person is meaningless. This turns the model
about the vertical only, so its longest level axis runs along X, scales it uniformly by one measure of the brief, and
stands it on the ground at the middle. Every vertex of the real mesh is measured; nothing else of the model changes.
usage: tobrief.py in.glb out.glb rule metres [beam_m]     rule: length (longest level axis) | height | across (= length)
beam_m (optional): the brief's width across the long axis; when the generation is fatter or thinner than the brief,
the cross-section (width and depth together) is scaled to it, the length kept: a hull keeps its section shape.
prints the scale applied and the size in metres as JSON"""
import sys, json, numpy as np, trimesh


def verts(sc):
    return np.vstack([trimesh.transform_points(sc.geometry[g].vertices, sc.graph.get(n)[0])
                      for n in sc.graph.nodes_geometry for g in [sc.graph.get(n)[1]]])


def to_brief(src, out, rule, metres, beam=None):
    sc = trimesh.load(src, force='scene', process=False)
    V = verts(sc); c = V.mean(0); XZ = V[:, [0, 2]] - c[[0, 2]]
    w, E = np.linalg.eigh(np.cov(XZ.T)); ax = E[:, np.argmax(w)]            # the long level axis, from the real vertices
    a = np.arctan2(ax[1], ax[0])
    R = trimesh.transformations.rotation_matrix(a, [0, 1, 0])                # turns that axis onto +X (about Y only)
    sc.apply_transform(R); V = verts(sc); ext = np.ptp(V, axis=0)
    have = ext[1] if rule == 'height' else max(ext[0], ext[2])
    s = metres / have
    sz = beam / (ext[2] * s) * s if beam else s
    S = np.diag([s, sz, sz, 1.0]); sc.apply_transform(S); V = verts(sc)
    lo, hi = V.min(0), V.max(0)
    sc.apply_translation([-(lo[0] + hi[0]) / 2, -lo[1], -(lo[2] + hi[2]) / 2])
    sc.export(out)
    size = np.ptp(verts(sc), axis=0)
    return {"rule": rule, "target_m": metres, "scale_applied": round(float(s), 4), "beam_scale": round(float(sz / s), 3), "size_m": [round(float(x), 3) for x in size]}


if __name__ == '__main__':
    print(json.dumps(to_brief(sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), float(sys.argv[5]) if len(sys.argv) > 5 else None)))
