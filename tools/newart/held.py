"""A held game model as a line-up neighbour: a vanilla NIF read from the owner's own archives (nifdump, the real
triangles, UVs and the diffuse and normal maps it names), turned to Y up and put in metres (70 game units to the
metre), written as a GLB beside our models so both stand in one scene under one light. Only vanilla goes on the page;
a mod's model (given as a file path in its mod folder, its textures found in the same mod) is for our own looking and
measuring, never published. Nothing it writes is committed (out/newart/ only).
usage: held.py data/path.nif|/path/to/mod/meshes/x.nif out.glb [max_texture_px=1024]"""
import json, sys
from pathlib import Path
import numpy as np, trimesh
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.places.assets.nifglb import dump
from tools.places.assets.resolve import default
from tools.places.assets.dds import decode

UNITS_PER_M = 70.0
ZUP_TO_YUP = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], float)


def reader(key: str):
    """Reads data paths: the owner's archives and enabled mods, else (a file path given) that file's own mod folder."""
    r = default(); f = Path(key)
    if not f.is_file(): return key, r.read
    mod = next(p for p in f.parents if p.name.lower() == "meshes").parent; idx = {}
    for q in mod.rglob("*"):
        if q.is_file(): idx[str(q.relative_to(mod)).lower().replace("\\", "/")] = q
    def read(k):
        q = idx.get(k.lower().replace("\\", "/")); return q.read_bytes() if q else r.read(k)
    return str(f.relative_to(mod)).lower(), read


def held(key: str, out: str, px: int = 1024) -> dict:
    key, read = reader(key); d = dump(read(key)); sc = trimesh.Scene(); tris = 0
    for i, s in enumerate(d["shapes"]):
        if s.get("hidden") or (s.get("shader") or {}).get("type") != "BSLightingShaderProperty" or s.get("P") is None: continue
        T = np.eye(4); T[:3, :] = np.array(s["m"], float).reshape(3, 4)          # the shape's transform to the root, rows of rotation and scale with the translation last
        mesh = trimesh.Trimesh(np.asarray(s["P"], float), np.asarray(s["I"]), process=False)
        uv = np.asarray(s["UV"], float) * np.asarray(s["shader"].get("uv_scale", [1, 1])) + np.asarray(s["shader"].get("uv_offset", [0, 0]))
        tex = [t.lower().replace("\\", "/") for t in s.get("tex") or []]
        img = decode(read(tex[0])) if tex and tex[0] and read(tex[0]) else None
        nrm = decode(read(tex[1])) if len(tex) > 1 and tex[1] and read(tex[1]) else None
        if img is not None: img = img.convert("RGB"); img.thumbnail((px, px))
        if nrm is not None: nrm = nrm.convert("RGB"); nrm.thumbnail((px // 2, px // 2))
        uv[:, 1] = 1 - uv[:, 1]
        mesh.visual = trimesh.visual.TextureVisuals(uv=uv, material=trimesh.visual.material.PBRMaterial(baseColorTexture=img, normalTexture=nrm, metallicFactor=0.0, roughnessFactor=0.85, doubleSided=bool(s["shader"].get("two_sided"))))
        mesh.apply_transform(T); sc.add_geometry(mesh, node_name=f"shape{i}"); tris += len(mesh.faces)
    sc.apply_transform(ZUP_TO_YUP @ np.diag([1 / UNITS_PER_M] * 3 + [1]))
    b = sc.bounds; sc.apply_translation([-(b[0][0] + b[1][0]) / 2, -b[0][1], -(b[0][2] + b[1][2]) / 2]); sc.export(out)
    return {"model": key, "triangles": tris, "size_m": [round(float(x), 2) for x in sc.extents]}


if __name__ == "__main__":
    print(json.dumps(held(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 1024)))
