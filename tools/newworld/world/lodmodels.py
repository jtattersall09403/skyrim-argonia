"""Far-off models (static LOD models) for the heavy placed bases that have none: fallen logs, stumps, roots, boulders.

Skyrim draws a static beyond the loaded cells from its LOD model, `<model>_lod_0.nif` (dyndolod.info Mod-Authors:
DynDOLOD finds it by that name anywhere under meshes\\ and merges it into the object LOD of each block, its textures
into the atlas). A base whose full model is too heavy for the block budget (lodplan.py) and has no LOD model gets one
derived here: the same shape with fewer triangles, the same textures, laid out as Skyrim's own LOD models are.

    python -m tools.newworld.world.lodmodels build [--plugin out/newworld/plugin] [--out out/newworld/lodmodels]
        reads <plugin>/map/lodplan.json's "lod_targets" (model -> triangles); writes
        <out>/meshes/lod/<model path>_lod_0.nif and <out>/manifest.json (key; per model: its LOD path, triangles,
        the checks' numbers; "failed": model -> why). A model already made for the same source, target and maker is
        kept (resumable); a model no longer wanted is removed.
    python -m tools.newworld.world.lodmodels check [--out ...]
        every model of the manifest read back from its file again; exit 1 on any fault

How a model is made:
  - the full model is read with nifdump (nifly); its drawn shapes (not hidden, not skinned, lit by a
    BSLightingShaderProperty, textured, with UVs) are baked into the root's space;
  - each shape is simplified by quadric edge collapse (fast-simplification) on its position-welded surface, so UV
    seams stay closed; the triangle target is shared between the shapes by their area;
  - every vertex of the result is one of the full model's own: its position is the source vertex nearest the
    collapsed point, its UV, normal and colour those of a source vertex of the same UV island. So the bounds cannot
    grow and no UV leaves the source's range (DynDOLOD then treats the textures exactly as the full model's);
  - niflod writes the nif as Skyrim's own LOD models are (measured on 28 of Skyrim - Meshes' *_lod_*.nif: BSFadeNode
    root, BSTriShape children each with a BSLightingShaderProperty of type 0 and a BSShaderTextureSet of diffuse and
    normal map, flags 0x80400300 / 0x8001, no collision, no extra data).
The checks every model must pass, or it is not in the manifest and its bases keep no LOD: the written file reads
back (nifdump and niflod --info); it has triangles, no more than the target; root and blocks as above; every UV
inside the source's range; the bounds inside the source's and no side more than SHRINK of that axis's extent (or
SHRINK_UNITS) short of it; every texture resolves in the profile.

The outputs are derived build outputs: never committed (decision 0003), sent to the machine by lod.sh send, archived
with the LOD.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
NIFLOD = Path.home() / ".argonia" / "bin" / "niflod"
MAKER = 3  # raised when a change here or in niflod changes what is written: every model is made again
SHRINK = 0.10  # a side of the bounds may fall short of the source's by this share of the axis's extent ...
SHRINK_UNITS = 8.0  # ... or by this many units, whichever is more
BLOCKS = {"BSFadeNode", "BSTriShape", "BSLightingShaderProperty", "BSShaderTextureSet", "NiAlphaProperty"}


def lod_path(model: str) -> str:
    """Where the LOD model of a full model (path under meshes) goes, under meshes: lod\\<path>_lod_0.nif."""
    m = model.replace("/", "\\").lower()
    return f"lod\\{m[:-4] if m.endswith('.nif') else m}_lod_0.nif"


def parts(head: dict) -> list[dict]:
    """The shapes of a nifdump header a far shape is made of, baked into the root's space."""
    out = []
    for s in head["shapes"]:
        sh = s.get("shader") or {}
        if s.get("hidden") or s.get("skinned") or not s["tris"] or s["UV"] is None or not s["tex"][0]:
            continue
        if sh.get("type") != "BSLightingShaderProperty":
            continue  # an effect shader (glow, mist): no part of the far shape
        m = np.asarray(s["m"], np.float64).reshape(3, 4)
        P = np.asarray(s["P"], np.float64) @ m[:, :3].T + m[:, 3]
        N = None
        if s["N"] is not None:
            N = np.asarray(s["N"], np.float64) @ m[:, :3].T
            N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
        UV = np.asarray(s["UV"], np.float64) * sh.get("uv_scale", [1, 1]) + sh.get("uv_offset", [0, 0])
        C = np.asarray(s["C"], np.float64) if s["C"] is not None and sh.get("vertex_colors") else None
        I = np.asarray(s["I"], np.int64)
        e1, e2 = P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]]
        out.append({"P": P, "N": N, "UV": UV, "C": C, "I": I, "tex": s["tex"], "two_sided": bool(sh.get("two_sided")),
                    "alpha_test": bool((s.get("alpha") or {}).get("flags", 0) & 0x200),
                    "area": float(0.5 * np.linalg.norm(np.cross(e1, e2), axis=1).sum())})
    return out


def _islands(n: int, I: np.ndarray) -> np.ndarray:
    """A label per vertex: the connected piece of the unwelded surface it lies in (a UV island or a part of one)."""
    parent = np.arange(n)

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for a, b, c in I:
        ra = find(a)
        for x in (b, c):
            rx = find(x)
            if rx != ra:
                parent[rx] = ra
    return np.array([find(i) for i in range(n)])


def simplify(p: dict, target: int) -> dict:
    """One shape with at most about `target` triangles, every vertex one of the source's own (module docstring)."""
    import fast_simplification as fs
    P, I = p["P"], p["I"]
    if len(I) <= target:
        return p
    # the position-welded surface: seams closed, so a collapse cannot open one
    _, first, inv = np.unique(np.round(P, 3), axis=0, return_index=True, return_inverse=True)
    inv = inv.reshape(-1)
    Pw, Iw = P[first], inv[I]
    live = (Iw[:, 0] != Iw[:, 1]) & (Iw[:, 1] != Iw[:, 2]) & (Iw[:, 0] != Iw[:, 2])
    src_tri = np.nonzero(live)[0]
    Iw = Iw[live]
    best = None
    for agg in (7, 9, 11):  # a harder collapse only when the gentler one stops far above the target
        _, _, coll = fs.simplify(Pw.astype(np.float32), Iw, target_count=max(target, 4), agg=agg, return_collapses=True)
        P2, _, mp = fs.replay_simplification(Pw.astype(np.float32), Iw, coll)
        F = mp[Iw]
        keep = (F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 0] != F[:, 2])
        if best is None or keep.sum() < best[2].sum():
            best = (np.asarray(P2, np.float64), mp, keep, F)
        if keep.sum() <= target * 1.1:
            break
    P2, mp, keep, F = best
    label = _islands(len(P), I)
    # each new vertex stands on the welded source vertex nearest the collapsed point
    d = np.linalg.norm(Pw - P2[mp], axis=1)
    order = np.lexsort((np.arange(len(mp)), d, mp))
    stand = np.full(len(P2), -1, np.int64)
    stand[mp[order][::-1]] = order[::-1]  # the first of each group in (mp, d) order: the nearest
    new_of = mp[inv]  # source vertex -> new vertex
    members: dict[tuple[int, int], list[int]] = {}
    for o in range(len(P)):
        members.setdefault((int(new_of[o]), int(label[o])), []).append(o)
    chosen: dict[tuple[int, int], int] = {}
    out_of: dict[tuple[int, int], int] = {}
    verts, tris = [], []
    for t in np.nonzero(keep)[0]:
        tri = []
        for c in range(3):
            o = int(I[src_tri[t], c])
            k = (int(new_of[o]), int(label[o]))
            if k not in chosen:  # the source vertex of this island nearest where the new vertex stands
                ms = members[k]
                chosen[k] = ms[int(np.argmin(np.linalg.norm(P[ms] - Pw[stand[k[0]]], axis=1)))]
            if k not in out_of:
                out_of[k] = len(verts)
                verts.append((stand[k[0]], chosen[k]))
            tri.append(out_of[k])
        tris.append(tri)
    at = np.array([v[0] for v in verts])
    src = np.array([v[1] for v in verts])
    q = dict(p)
    q["P"], q["UV"], q["I"] = Pw[at], p["UV"][src], np.array(tris, np.int64)
    q["N"] = p["N"][src] if p["N"] is not None else None
    q["C"] = p["C"][src] if p["C"] is not None else None
    return q


def shapes_file(shapes: list[dict]) -> bytes:
    """niflod's input (niflod.cpp)."""
    b = bytearray(b"NLOD" + struct.pack("<I", len(shapes)))
    for s in shapes:
        flags = (1 if s["N"] is not None else 0) | (2 if s["C"] is not None else 0) | (4 if s["two_sided"] else 0) | (8 if s["alpha_test"] else 0)
        b += struct.pack("<III", len(s["P"]), len(s["I"]), flags)
        for t in s["tex"][:2]:
            raw = t.encode("latin-1")
            b += struct.pack("<H", len(raw)) + raw
        b += np.asarray(s["P"], "<f4").tobytes() + np.asarray(s["UV"], "<f4").tobytes()
        if s["N"] is not None:
            b += np.asarray(s["N"], "<f4").tobytes()
        if s["C"] is not None:
            b += np.asarray(s["C"], "<f4").tobytes()
        b += np.asarray(s["I"], "<u2").tobytes()
    return bytes(b)


def info(path: Path) -> dict:
    r = subprocess.run([str(NIFLOD), "--info", str(path)], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise ValueError((r.stderr or "niflod --info failed").strip()[:200])
    return json.loads(r.stdout)


def _bounds(ps: list[dict]) -> np.ndarray:
    P = np.concatenate([p["P"] for p in ps])
    return np.array([P.min(0), P.max(0)])


def _uv_range(ps: list[dict]) -> dict[str, list[float]]:
    r: dict[str, list[float]] = {}
    for p in ps:
        k = p["tex"][0].lower()
        lo, hi = p["UV"].min(0), p["UV"].max(0)
        a = r.setdefault(k, [float(lo[0]), float(lo[1]), float(hi[0]), float(hi[1])])
        a[:] = [min(a[0], lo[0]), min(a[1], lo[1]), max(a[2], hi[0]), max(a[3], hi[1])]
    return r


def verify(raw: bytes, src: list[dict], target: int, read_tex) -> tuple[dict, list[str]]:
    """The written LOD model read back, against the full model's parts: (numbers, faults)."""
    from tools.places.assets import nifglb
    faults: list[str] = []
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "lod.nif"
        f.write_bytes(raw)
        try:
            inf = info(f)
            got = parts(nifglb.dump(raw))
        except Exception as e:  # noqa: BLE001 - any reader's refusal is the fault
            return {}, [f"does not read back: {e}"[:200]]
    tris = sum(len(p["I"]) for p in got)
    if not got or not tris:
        return {}, ["no drawn shape reads back"]
    if tris != sum(s["tris"] for s in inf["shapes"]):
        faults.append("the two readers count different triangles")
    if tris > target:
        faults.append(f"{tris} triangles, over the target {target}")
    if inf["root"] != "BSFadeNode" or set(inf["blocks"]) - BLOCKS or any(s["parent"] != "BSFadeNode" or s["block"] != "BSTriShape" for s in inf["shapes"]):
        faults.append(f"not laid out as Skyrim's LOD models: root {inf['root']}, blocks {sorted(set(inf['blocks']))}")
    sb, gb = _bounds(src), _bounds(got)
    ext = sb[1] - sb[0]
    grow = max(float((sb[0] - gb[0]).max()), float((gb[1] - sb[1]).max()))
    short = np.maximum(gb[0] - sb[0], sb[1] - gb[1])
    allow = np.maximum(ext * SHRINK, SHRINK_UNITS)
    if grow > 0.01:
        faults.append(f"bounds {grow:.2f} units outside the source's")
    if (short > allow).any():
        faults.append(f"bounds fall short of the source's by {short.round(1).tolist()} units (extent {ext.round(1).tolist()})")
    su, gu = _uv_range(src), _uv_range(got)
    for k, g in gu.items():
        s = su.get(k)
        if s is None:
            faults.append(f"a texture the source does not use: {k}")
        elif g[0] < s[0] - 1e-4 or g[1] < s[1] - 1e-4 or g[2] > s[2] + 1e-4 or g[3] > s[3] + 1e-4:
            faults.append(f"UVs of {k} leave the source's range")
    for p in got:
        for t in p["tex"][:2]:
            if t and read_tex(t) is None:
                faults.append(f"texture not in the profile: {t}")
    uv = [min(g[0] for g in gu.values()), min(g[1] for g in gu.values()), max(g[2] for g in gu.values()), max(g[3] for g in gu.values())]
    return {"triangles": tris, "shapes": len(got), "bounds_short": [round(float(x), 1) for x in short],
            "extent": [round(float(x), 1) for x in ext], "uv": [round(x, 3) for x in uv],
            "textures": sorted({p["tex"][0].lower() for p in got})}, faults


def make(raw: bytes, target: int, read_tex) -> tuple[bytes | None, dict, list[str]]:
    """(the LOD nif, its numbers, faults) of one full model."""
    from tools.places.assets import nifglb
    try:
        src = parts(nifglb.dump(raw))
    except Exception as e:  # noqa: BLE001
        return None, {}, [f"the full model does not read: {e}"[:200]]
    if not src:
        return None, {}, ["the full model has no drawn, textured shape"]
    total = sum(p["area"] for p in src) or 1.0
    full = sum(len(p["I"]) for p in src)
    done = []
    for scale in (1.0, 0.85, 0.7):  # a collapse can stop a little above its target: ask for less, never accept more
        done = [simplify(p, max(4, int(target * scale * p["area"] / total))) for p in src]
        if sum(len(p["I"]) for p in done) <= target:
            break
    done = [p for p in done if len(p["I"])]
    with tempfile.TemporaryDirectory() as d:
        i, o = Path(d) / "shapes.bin", Path(d) / "lod.nif"
        i.write_bytes(shapes_file(done))
        r = subprocess.run([str(NIFLOD), str(i), str(o)], capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            return None, {}, [f"niflod: {(r.stderr or r.stdout).strip()[:200]}"]
        out = o.read_bytes()
    nums, faults = verify(out, src, target, read_tex)
    nums["source_triangles"] = full
    return out, nums, faults


def build(plugin: Path, out: Path, read=None, read_tex=None) -> dict:
    from tools.places.assets import resolve
    if read is None:
        r = resolve.default()
        read = lambda p: r.read(resolve.norm(p, "meshes"))  # noqa: E731
        read_tex = lambda p: r.read(resolve.norm(p, "textures"))  # noqa: E731
    targets = json.loads((plugin / "map" / "lodplan.json").read_text()).get("lod_targets", {})
    mf = out / "manifest.json"
    old = json.loads(mf.read_text())["models"] if mf.exists() else {}
    niflod = hashlib.sha256(NIFLOD.read_bytes()).hexdigest()[:16] if NIFLOD.exists() else ""
    if targets and not niflod:
        raise SystemExit(f"niflod not built: run tools/newworld/niflod/build.sh ({NIFLOD})")
    models, failed = {}, {}
    for model, target in sorted(targets.items()):
        raw = read(model)
        if raw is None:
            failed[model] = ["the full model is not in the profile"]
            continue
        key = hashlib.sha256(raw + f"|{target}|{MAKER}|{niflod}".encode()).hexdigest()[:16]
        dst = out / "meshes" / Path(*lod_path(model).split("\\"))
        was = old.get(model)
        if was and was.get("key") == key and dst.exists() and hashlib.sha256(dst.read_bytes()).hexdigest() == was.get("sha256"):
            models[model] = was
            continue
        nif, nums, faults = make(raw, target, read_tex)
        if faults or nif is None:
            failed[model] = faults
            dst.unlink(missing_ok=True)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(nif)
        models[model] = {"key": key, "lod": lod_path(model), "target": target, "sha256": hashlib.sha256(nif).hexdigest(), **nums}
        mf.parent.mkdir(parents=True, exist_ok=True)  # the manifest after every model: a stopped run resumes
        mf.write_text(json.dumps({"key": "", "models": models, "failed": failed}, indent=1))
    want = {out / "meshes" / Path(*m["lod"].split("\\")) for m in models.values()}
    if (out / "meshes").exists():
        for f in (out / "meshes").rglob("*.nif"):
            if f not in want:
                f.unlink()
    doc = {"key": hashlib.sha256(json.dumps(sorted((m, v["sha256"]) for m, v in models.items())).encode()).hexdigest()[:16],
           "maker": MAKER, "models": models, "failed": failed}
    out.mkdir(parents=True, exist_ok=True)
    mf.write_text(json.dumps(doc, indent=1))
    return doc


def check(out: Path) -> int:
    """Every model of the manifest still the file it names, reading back with triangles."""
    doc = json.loads((out / "manifest.json").read_text())
    bad = 0
    for model, m in doc["models"].items():
        f = out / "meshes" / Path(*m["lod"].split("\\"))
        try:
            ok = hashlib.sha256(f.read_bytes()).hexdigest() == m["sha256"] and sum(s["tris"] for s in info(f)["shapes"]) == m["triangles"]
        except Exception:  # noqa: BLE001
            ok = False
        if not ok:
            bad += 1
            print(f"FAULT lod model of {model}: {f} is not the file the manifest names")
    print(f"lod models: {len(doc['models'])} read back, {bad} faults, {len(doc['failed'])} not made")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("build", "check"))
    ap.add_argument("--plugin", default=str(REPO / "out/newworld/plugin"))
    ap.add_argument("--out", default=str(REPO / "out/newworld/lodmodels"))
    a = ap.parse_args(argv)
    if a.cmd == "check":
        return check(Path(a.out))
    doc = build(Path(a.plugin), Path(a.out))
    ms = doc["models"].values()
    print(f"lod models: {len(doc['models'])} made ({sum(m['source_triangles'] for m in ms)} -> {sum(m['triangles'] for m in ms)} triangles), "
          f"{len(doc['failed'])} not made, key {doc['key']}")
    for m, why in doc["failed"].items():
        print(f"  not made: {m}: {'; '.join(why)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
