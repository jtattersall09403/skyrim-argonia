"""Write the asset explorer's web copy of a model: one glTF JSON file (.gltf.json) with its buffers and textures as
data URIs (the page host serves no .glb), textures as JPEG no larger than a set size (never enlarged); a model over the triangle cap is refused (cut it with shape.py first).
usage: webcopy.py in.(glb|obj) out.gltf.json [px=1024] [max_triangles=60000]   prints what it did as JSON"""
import sys, io, json, base64, tempfile, os, trimesh
from PIL import Image
import pygltflib

def webcopy(src, out, px=1024, cap=60000):
    sc = trimesh.load(src, force='scene', process=False); note = {"source_triangles": 0, "decimated": False}
    for name, g in list(sc.geometry.items()):
        note["source_triangles"] += len(g.faces)
        mat = getattr(g.visual, 'material', None)
        if isinstance(mat, trimesh.visual.material.SimpleMaterial):   # an OBJ's material: carry its picture as the base colour
            mat = mat.to_pbr(); g.visual.material = mat
        if mat is None: continue
        for k in ('baseColorTexture', 'normalTexture'):
            im = getattr(mat, k, None)
            if im is not None:
                b = io.BytesIO(); im.convert('RGB').resize((min(px, im.width), min(px, im.height)), Image.LANCZOS).save(b, 'JPEG', quality=85); b.seek(0); setattr(mat, k, Image.open(b))
        for k in ('metallicRoughnessTexture', 'occlusionTexture', 'emissiveTexture'):
            if getattr(mat, k, None) is not None: setattr(mat, k, None)
        mat.metallicFactor = 0.0; mat.roughnessFactor = 0.9
        if len(g.faces) > cap:
            raise SystemExit(f"{src}: {len(g.faces)} triangles is over the web cap of {cap}; cut it with shape.py first")
    with tempfile.TemporaryDirectory() as d:
        glb = os.path.join(d, 'w.glb'); sc.export(glb)
        gl = pygltflib.GLTF2().load(glb); blob = gl.binary_blob()
        for im in gl.images or []:                       # each picture becomes its own data URI
            bv = gl.bufferViews[im.bufferView]; data = blob[bv.byteOffset or 0:(bv.byteOffset or 0) + bv.byteLength]
            im.uri = f"data:{im.mimeType or 'image/jpeg'};base64," + base64.b64encode(data).decode(); im.bufferView = None
        gl.buffers[0].uri = "data:application/octet-stream;base64," + base64.b64encode(blob).decode()
        gl.set_binary_blob(None) if hasattr(gl, 'set_binary_blob') else None
        gl._glb_data = None
        txt = gl.gltf_to_json()
    open(out, 'w').write(txt); note.update({"out_kb": round(len(txt) / 1024), "texture_px": px}); return note

if __name__ == '__main__':
    a = sys.argv
    print(json.dumps(webcopy(a[1], a[2], int(a[3]) if len(a) > 3 else 1024, int(a[4]) if len(a) > 4 else 60000)))
