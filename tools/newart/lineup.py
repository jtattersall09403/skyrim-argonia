"""One line-up scene: our models standing beside held neighbours on one ground, in metres, left to right in the order
given, a gap between each. The explorer draws it under its one light with the 1.8 m person.
usage: lineup.py out.glb gap_m a.glb[:x|:up] [b.glb ...]
  each GLB already in metres, Y up; `:x` turns a part about the vertical so its long level axis runs along the line
  (a boat beside a boat), `:up` stands a part's long axis upright (a weapon the game stores lying down); both from
  the part's real vertices."""
import json, sys
import numpy as np, trimesh


def verts(s):
    return np.vstack([trimesh.transform_points(s.geometry[g].vertices, T) for n in s.graph.nodes_geometry for T, g in [s.graph.get(n)]])


def lineup(out: str, gap: float, parts: list[str]) -> dict:
    sc = trimesh.Scene(); x = 0.0; placed = []
    for i, spec in enumerate(parts):
        p, _, how = spec.partition(':'); s = trimesh.load(p, force='scene', process=False); V = verts(s)
        if how == 'x':
            w, E = np.linalg.eigh(np.cov((V[:, [0, 2]] - V[:, [0, 2]].mean(0)).T)); ax = E[:, np.argmax(w)]
            s.apply_transform(trimesh.transformations.rotation_matrix(np.arctan2(ax[1], ax[0]), [0, 1, 0]))
        elif how == 'up':
            w, E = np.linalg.eigh(np.cov((V - V.mean(0)).T)); ax = E[:, np.argmax(w)]
            s.apply_transform(trimesh.geometry.align_vectors(ax, [0, 1, 0]))
        V = verts(s); lo, hi = V.min(0), V.max(0)
        s.apply_translation([x - lo[0], -lo[1], -(lo[2] + hi[2]) / 2])
        for n in s.graph.nodes_geometry:
            T, g = s.graph.get(n); sc.add_geometry(s.geometry[g].copy(), node_name=f"p{i}_{n}", transform=T)
        placed.append({"model": p, "from_x": round(x, 2), "size_m": [round(float(v), 2) for v in hi - lo]}); x += float(hi[0] - lo[0]) + gap
    sc.export(out); return {"out": out, "length_m": round(x - gap, 2), "parts": placed}


if __name__ == "__main__":
    print(json.dumps(lineup(sys.argv[1], float(sys.argv[2]), sys.argv[3:])))
