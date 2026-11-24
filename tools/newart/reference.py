"""The reference numbers: what "consistent with Skyrim" measures as, per material, over the meshes we hold (vanilla's
archives and the mods in the stack, BM&V first among them). For each material a sample of meshes is found by the
diffuse texture's path, every shape of it is read (nifdump, the real triangles and UVs), and these are measured:

  px_per_m      texel density: texture pixels per metre of the real surface, from each shape's UV area against its
                world area (tiling counts: a texture repeated four times over a wall is four times as dense)
  L, chroma     the diffuse's CIELAB lightness (10th, 50th and 90th percentile) and chroma (median), over the
                texture's own pixels (alpha-tested holes left out)
  hue           the circular mean hue in degrees, where the chroma is enough to carry one
  normal        normal-map strength: the median tilt of the normal map's normals away from flat, in degrees
  specular      the normal map's alpha (Skyrim's specular mask), median 0 to 1

usage: reference.py out.json [per_material=24]   (run with the project venv: ~/.argonia/venv/bin/python)"""
import json, re, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.places.assets.nifglb import dump
from tools.places.assets.resolve import default
from tools.places.assets.dds import decode

UNITS_PER_M = 70.0
MATERIALS = {   # diffuse path patterns; the first match wins, in this order
    "rope and binding": r"rope|lashing|binding|twine|cord",
    "bone": r"bone(?!r)|skull|antler|ivory|tusk",
    "reed and thatch": r"thatch|reed|straw|hay|wicker|basket",
    "weathered wood": r"wood|plank|boat|dock|\blog|stilt|hut|shack|canoe|raft|barrel|crate",
    "stone": r"stone|rock|cobble|obsidian|flint|slate|ruin",
    "iron and bronze": r"iron|bronze|steel|metal|dwarven|dwemer",
}
MESH_HINT = r"clutter|architecture|weapons|dungeons|furniture|landscape|blackmarsh|bmv|argonian|murkmire|camp|dock|boat|hut"


def lab(rgb):
    c = rgb / 255.0; c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    xyz = c @ np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]).T / [0.95047, 1.0, 1.08883]
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[:, 1] - 16, 500 * (f[:, 0] - f[:, 1]), 200 * (f[:, 1] - f[:, 2])], 1)


def image_stats(img: Image.Image) -> dict:
    a = np.asarray(img.convert("RGBA").resize((128, 128)), np.float32).reshape(-1, 4); a = a[a[:, 3] > 128] if (a[:, 3] < 250).mean() < 0.9 else a
    L = lab(a[:, :3]); ch = np.hypot(L[:, 1], L[:, 2]); h = np.degrees(np.arctan2(L[:, 2], L[:, 1])) % 360; w = ch > 6
    hue = float(np.degrees(np.arctan2(np.sin(np.radians(h[w])).mean(), np.cos(np.radians(h[w])).mean())) % 360) if w.sum() > 20 else None
    return {"L": [round(float(np.percentile(L[:, 0], q)), 1) for q in (10, 50, 90)], "chroma": round(float(np.median(ch)), 1), "hue": None if hue is None else round(hue)}


def normal_stats(img: Image.Image) -> dict:
    a = np.asarray(img.convert("RGBA").resize((128, 128)), np.float32).reshape(-1, 4) / 255.0
    x, y = a[:, 0] * 2 - 1, a[:, 1] * 2 - 1; tilt = np.degrees(np.arcsin(np.clip(np.hypot(x, y), 0, 1)))
    return {"normal": round(float(np.median(tilt)), 1), "specular": round(float(np.median(a[:, 3])), 2)}


def density(s) -> float | None:
    P, I, UV = s.get("P"), s.get("I"), s.get("UV")
    if P is None or I is None or UV is None or len(I) == 0: return None
    R = np.array(s["m"], float).reshape(3, 4)[:, :3]; sc = abs(np.linalg.det(R)) ** (1 / 3) if np.linalg.det(R) else 1.0
    T = np.asarray(P, float)[np.asarray(I)] * sc / UNITS_PER_M; U = np.asarray(UV, float)[np.asarray(I)] * np.asarray(s["shader"].get("uv_scale", [1, 1]), float)
    wa = 0.5 * np.linalg.norm(np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]), axis=1).sum()
    e1, e2 = U[:, 1] - U[:, 0], U[:, 2] - U[:, 0]; ua = 0.5 * np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]).sum()
    return float(np.sqrt(ua / wa)) if wa > 1e-4 and ua > 0 else None


def measure_all(per: int = 24) -> dict:
    r = default(); meshes = []
    for name, arc in r.archives():
        if "meshes" in name.lower() or "bmv" in name.lower() or "patch" in name.lower():
            meshes += [k for k in arc.files if k.endswith(".nif") and re.search(MESH_HINT, k) and not re.search(r"lod|1stperson|_far|marker|fx", k)]
    for root in (Path.home() / ".argonia/stack/MO2/mods").glob("*/[mM]eshes"):
        meshes += [str(p.relative_to(root.parent)).lower().replace("\\", "/") for p in root.rglob("*.nif") if re.search(MESH_HINT, str(p).lower()) and not re.search(r"lod|1stperson|_far|marker|fx", str(p).lower())]
    meshes = sorted(set(meshes)); rng = np.random.default_rng(5); rng.shuffle(meshes)
    got = {m: [] for m in MATERIALS}; seen_tex = set()
    for key in meshes:
        if all(len(v) >= per for v in got.values()): break
        b = r.read(key)
        if not b: continue
        try: d = dump(b)
        except Exception: continue
        for s in d.get("shapes", []):
            if s.get("hidden") or (s.get("shader") or {}).get("type") != "BSLightingShaderProperty" or not s.get("tex") or not s["tex"][0]: continue
            diff = s["tex"][0].lower().replace("\\", "/"); mat = next((m for m, rx in MATERIALS.items() if re.search(rx, diff)), None)
            if not mat or len(got[mat]) >= per or diff in seen_tex: continue
            px = density(s); db = r.read(diff)
            if px is None or not db: continue
            try: img = decode(db)
            except Exception: continue
            row = {"mesh": key, "diffuse": diff, "tex_px": img.size[0], "px_per_m": round(px * img.size[0], 1), **image_stats(img)}
            nb = r.read(s["tex"][1].lower().replace("\\", "/")) if len(s["tex"]) > 1 and s["tex"][1] else None
            if nb:
                try: row.update(normal_stats(decode(nb)))
                except Exception: pass
            got[mat].append(row); seen_tex.add(diff)
    summary = {}
    for m, rows in got.items():
        if not rows: continue
        q = lambda k, f=lambda x: x: [f(x[k]) for x in rows if x.get(k) is not None]
        pct = lambda v: [round(float(np.percentile(v, p)), 1) for p in (25, 50, 75)] if v else None
        hues = [x["hue"] for x in rows if x.get("hue") is not None]
        summary[m] = {"n": len(rows), "px_per_m": pct(q("px_per_m")), "L50": pct(q("L", lambda v: v[1])), "L10": pct(q("L", lambda v: v[0])), "L90": pct(q("L", lambda v: v[2])),
                      "chroma": pct(q("chroma")), "hue": round(float(np.degrees(np.arctan2(np.sin(np.radians(hues)).mean(), np.cos(np.radians(hues)).mean())) % 360)) if hues else None,
                      "normal_deg": pct(q("normal")), "specular": pct(q("specular"))}
    return {"summary": summary, "samples": got}


if __name__ == "__main__":
    out = measure_all(int(sys.argv[2]) if len(sys.argv) > 2 else 24); Path(sys.argv[1]).write_text(json.dumps(out, indent=1))
    for m, s in out["summary"].items(): print(m, json.dumps(s))
