"""Stage: surface. (a) make a generated swatch into a repeating material (its edges cross-faded into its own middle, so they always meet with no mirror symmetry) with a
normal map from its own relief; (b) wrap a mesh in it by box projection in metres from the real face normals, so pixels
per metre are constant whatever the size; (c) write web copies of GLBs with lighter textures.
usage: surface.py material src.png outdir | wrap mesh.glb material_dir out.glb metres_per_tile | web in.glb out.glb px"""
import sys, io, json, numpy as np, trimesh
from PIL import Image, ImageFilter
def material(src, outdir, px=2048):
    im = Image.open(src).convert('RGB').resize((px, px), Image.LANCZOS)
    A = np.asarray(im, dtype=np.float32); B = np.roll(A, (px // 2, px // 2), axis=(0, 1))      # B's edges are A's middle: they meet
    y, x = np.mgrid[0:px, 0:px]; d = np.minimum(np.minimum(x, px - 1 - x), np.minimum(y, px - 1 - y)) / (px * 0.5)
    m = np.clip((d - 0.08) / 0.30, 0, 1); m = (m * m * (3 - 2 * m))[..., None]                 # A in the middle, B towards the edges
    t = Image.fromarray(np.clip(A * m + B * (1 - m), 0, 255).astype(np.uint8))
    t.save(f'{outdir}/base.png')
    g = np.asarray(t.convert('L').filter(ImageFilter.GaussianBlur(1.2)), dtype=np.float32) / 255.0
    dx = np.roll(g, -1, 1) - np.roll(g, 1, 1); dy = np.roll(g, -1, 0) - np.roll(g, 1, 0); k = 4.0
    n = np.dstack([-dx * k, dy * k, np.ones_like(g)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    Image.fromarray(((n * 0.5 + 0.5) * 255).astype(np.uint8)).save(f'{outdir}/normal.png')
    a = np.asarray(t, dtype=np.float32) / 255.0; lum = a @ [0.2126, 0.7152, 0.0722]
    mx, mn = a.max(2), a.min(2); sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    print(json.dumps({"px": px, "mean_brightness": round(float(lum.mean()), 3), "brightness_5_95": [round(float(np.percentile(lum, 5)), 3), round(float(np.percentile(lum, 95)), 3)], "mean_saturation": round(float(sat.mean()), 3)}))
def wrap(mesh, matdir, out, mpt, shade=False, web=0):
    g = trimesh.load(mesh, force='mesh', process=False); V, F = np.asarray(g.vertices), np.asarray(g.faces)
    fn = g.face_normals; ax = np.abs(fn).argmax(1)                         # the real face normals choose the projection
    P = V[F].reshape(-1, 3); A = np.repeat(ax, 3)
    u = np.where(A == 0, P[:, 2], P[:, 0]); v = np.where(A == 1, P[:, 2], P[:, 1])     # grain (U) runs along the hull
    uv = np.stack([u, v], 1) / mpt
    m = trimesh.Trimesh(P, np.arange(len(P)).reshape(-1, 3), process=False)
    m.vertex_normals = np.repeat(fn, 3, axis=0) if False else g.vertex_normals[F].reshape(-1, 3)
    def tex(name):
        im = Image.open(f'{matdir}/{name}.png').convert('RGB')
        if web: buf = io.BytesIO(); im.resize((web, web), Image.LANCZOS).save(buf, 'JPEG', quality=88); buf.seek(0); im = Image.open(buf)
        return im
    mat = trimesh.visual.material.PBRMaterial(baseColorTexture=tex('base'), normalTexture=tex('normal'), metallicFactor=0.0, roughnessFactor=0.9)
    vc = None
    if shade:   # shading and wear carried as vertex colour, sampled from the generation's own texture at each real vertex (Skyrim's own way to darken and tint)
        src = g.visual.material.baseColorTexture.convert('RGB').resize((512, 512), Image.LANCZOS).filter(ImageFilter.GaussianBlur(6))
        a = np.asarray(src, dtype=np.float32) / 255.0; guv = np.asarray(g.visual.uv)
        px = np.clip((guv[:, 0] % 1.0) * 511, 0, 511).astype(int); py = np.clip((1 - guv[:, 1] % 1.0) * 511, 0, 511).astype(int)
        c = a[py, px]; lum = c @ [0.2126, 0.7152, 0.0722]; ref = np.percentile(lum, 92)
        c = np.clip(c / ref, 0.30, 1.0); c = 0.25 + 0.75 * c                               # never brighter than the material, never black
        vc = (np.c_[c[F].reshape(-1, 3), np.ones(len(P))] * 255).astype(np.uint8)
    m.visual = trimesh.visual.TextureVisuals(uv=uv, material=mat)
    m.export(out)
    if vc is not None:   # trimesh writes texture visuals without colours: add COLOR_0 to the GLB ourselves
        import pygltflib
        gl = pygltflib.GLTF2().load(out); blob = gl.binary_blob(); data = (vc.astype(np.float32) / 255.0).tobytes()
        off = len(blob); pad = (-off) % 4; blob = blob + b'\0' * pad + data; off += pad
        gl.bufferViews.append(pygltflib.BufferView(buffer=0, byteOffset=off, byteLength=len(data), target=34962))
        gl.accessors.append(pygltflib.Accessor(bufferView=len(gl.bufferViews) - 1, componentType=5126, count=len(vc), type='VEC4'))
        gl.meshes[0].primitives[0].attributes.COLOR_0 = len(gl.accessors) - 1
        gl.buffers[0].byteLength = len(blob); gl.set_binary_blob(blob); gl.save(out)
    area = float(g.area); print(json.dumps({"metres_per_tile": mpt, "pixels_per_metre": round(Image.open(f'{matdir}/base.png').size[0] / mpt), "surface_m2": round(area, 2), "triangles": int(len(F))}))
def web(src, out, px):
    sc = trimesh.load(src, force='scene', process=False)
    for g in sc.geometry.values():
        mat = g.visual.material
        for k in ('baseColorTexture', 'normalTexture'):
            im = getattr(mat, k, None)
            if im is not None:
                b = io.BytesIO(); im.convert('RGB').resize((px, px), Image.LANCZOS).save(b, 'JPEG', quality=88); b.seek(0); setattr(mat, k, Image.open(b))
        for k in ('metallicRoughnessTexture', 'occlusionTexture', 'emissiveTexture'):
            if getattr(mat, k, None) is not None: setattr(mat, k, None)
        mat.metallicFactor = 0.0; mat.roughnessFactor = 0.9
    sc.export(out)
if __name__ == '__main__':
    c = sys.argv[1]
    if c == 'material': material(sys.argv[2], sys.argv[3])
    if c == 'wrap': wrap(sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5]), shade=len(sys.argv) > 6 and sys.argv[6] == 'shade', web=int(sys.argv[7]) if len(sys.argv) > 7 else 0)
    if c == 'web': web(sys.argv[2], sys.argv[3], int(sys.argv[4]))
