"""The install-time mesh patcher (lane 1.15-r6-mesh-patcher; decisions 0014, 0034, 0003).

Some placed forms draw the wrong colours because of their own NIF, not our data (owner #37, 2026-11-04 07:36: find
the cause and fix it, never drop): a soft-lit leaf with no soft-light map, Own_Emit on a leaf or bark, a bark normal in
the wrong slot, a bark UV stretched tens of times along one axis. A modder fixes these in NifSkope; we write the same
edits as data (data/mesh-patches.yaml: per mesh and shape, the measured before, the ops, the reason) and this tool
applies them to the source mod's mesh on the player's machine side of the build (the deploy's lay step), writing
copies into ours\\derived\\argonia-meshes, laid over every mod. Nothing patched is ever committed.

Ops (per shape): shader_from <shape> (draw with that shape's shader and texture set); clear_flags / set_flags [names of nif.F1/F2]; emissive {rgb, mult}; texture_slot {slot: path};
vertex_colour {lum_to: n | sat_to: s} (the drawn diffuse x vertex colour; the shared texture is never touched);
alpha {threshold: n} (the NiAlphaProperty's test threshold, 0-255; Bethesda's own value for the
same texture, e.g. its weeping willow's 127);
uv_scale {axis: u|v, factor: <number> | fit} (fit: per UV island, the factor from FIT_STEPS that minimises the
island's area-weighted 90th-percentile stretch; the island is scaled about its own minimum so the half floats stay small).
Bars, every shape of a patched mesh, after: a soft-lit shape has a slot-2 map; no shape is Own_Emit unless the entry
names the lore (`lore_emit`); a shape of kind bark has a normal (slot 1), a median UV stretch <= STRETCH_BAR, an area-weighted 90th-percentile stretch <= STRETCH_P90_BAR
unless the entry's `p90_owed` names the measure and why no op reaches it (the streaked tail: a buttress or a fold stretched while the median passes; lane 1.15-r6-veg-forms-3) and a drawn
luminance <= BARK_LUM_BAR; a leaf with a sat_to op draws at saturation <= LEAF_SAT_BAR.

    python3 -m tools.argonia_world.meshes patch --check [--mods DIR ...]   before/after per entry; exit 1 on any bar
    python3 -m tools.argonia_world.meshes patch --out DIR [--mods DIR ...] write the patched copies, re-read, verify
    python3 -m tools.argonia_world.meshes patch --list                    the files the lay step writes, and from where
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml

from tools.argonia_world.meshes import nif as N
from tools.argonia_world.meshes import source

ROOT = Path(__file__).resolve().parents[3]
TABLE = ROOT / "data" / "mesh-patches.yaml"
MODS = Path.home() / ".argonia" / "stack" / "MO2" / "mods"
DERIVED = "argonia-meshes"  # the derived folder: ours\\derived\\<this> on the machine, laid over every mod (stack.ps1)
OUT = ROOT / "out" / "derived" / DERIVED
STRETCH_BAR = 6.0
STRETCH_P90_BAR = 6.0
BARK_LUM_BAR = 81.0  # the brightest kept placed bark (gkbbark27, lane 1.15-r5-white-trunks); placed median 59
BARK_LUM_TARGET = 59.0
LEAF_SAT_BAR = 0.71  # the stack's leaf diffuses' p90 saturation (179 measured; median 0.39)
HUE = ROOT / "data" / "leaf-hue.json"  # the placed bark band's top (lane 1.15-r5-white-trunks: 3:1 to 6:1; global median 1.7:1)
FIT_STEPS = np.geomspace(1 / 128, 128, 57)


def load(path: Path = TABLE) -> list[dict]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))["meshes"]


_HUES: dict = {}


def _diffuse_rgb(path: str) -> list | None:
    if not _HUES and HUE.exists():
        import json
        _HUES.update(json.loads(HUE.read_text(encoding="utf-8")).get("textures", {}))
    from tools.argonia_world.vegetation.mesh_textures import norm
    t = _HUES.get(norm(path)) if path else None
    return t.get("rgb") if t else None


def _lum(c) -> float:
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def _sat(c) -> float:
    return 0.0 if max(c) <= 0 else (max(c) - min(c)) / max(c)


def measure(sh: N.Shape) -> dict:
    """The shape's shader and UV numbers, and what the engine draws: the diffuse mean (data/leaf-hue.json) times the
    vertex colour mean when Vertex_Colors is set (lum = Rec.601 luminance, sat = HSV saturation of that mean)."""
    p = sh.prop
    m = {"name": sh.name}
    if p is not None:
        f1, f2 = p.flags
        sl = p.slots() + [""] * 3
        m.update(flags=N.flag_names(f1, f2), emissive=list(p.emissive), soft=p.soft, slot1=sl[1], slot2=sl[2])
        if sh.alpha is not None:
            m["alpha"] = list(sh.alpha)  # [flags, threshold]: bit 0 blend, bit 9 test
        d = _diffuse_rgb(sl[0])
        if d is not None:
            c = sh.colours()
            vc = c.mean(0)[:3] / 255 if c is not None and "Vertex_Colors" in m["flags"] else np.ones(3)
            e = [float(x) for x in np.asarray(d) * vc]
            m.update(lum=round(_lum(e), 1), sat=round(_sat(e), 2))
    st = sh.stretch() if sh.has_uv() else None
    m["stretch"] = None if st is None else round(st, 1)
    if st is not None:
        r, t = sh.ratios()
        m["stretch90"] = round(_area_q(r, _areas(sh.positions(), t), 0.9), 1)
    return m


def _areas(p: np.ndarray, t: np.ndarray) -> np.ndarray:
    return np.linalg.norm(np.cross(p[t[:, 1]] - p[t[:, 0]], p[t[:, 2]] - p[t[:, 0]]), axis=1)


def _area_q(r: np.ndarray, a: np.ndarray, q: float) -> float:
    """The area-weighted quantile of the per-triangle stretch: what share of the drawn surface is stretched (a count
    quantile is ruled by a branch tip's thousand slivers)."""
    o = np.argsort(r)
    c = np.cumsum(a[o]) / max(a.sum(), 1e-12)
    return float(r[o][min(int(np.searchsorted(c, q)), len(r) - 1)])


def _flags(names: list[str]) -> tuple[int, int]:
    a = b = 0
    for n in names:
        if n in N.F1:
            a |= 1 << N.F1[n]
        elif n in N.F2:
            b |= 1 << N.F2[n]
        else:
            raise ValueError(f"unknown shader flag {n}")
    return a, b


def _uv_scale(sh: N.Shape, axis: str, factor) -> None:
    uv = sh.uv()
    k = 0 if axis == "u" else 1
    if factor != "fit":
        lo = uv[:, k].min()
        uv[:, k] = lo + (uv[:, k] - lo) * float(factor)
        sh.set_uv(uv)
        return
    isl, pos = sh.islands(), sh.positions()
    t = sh.triangles().astype(int)
    t = t[(t < sh.nv).all(1)]
    by = {}
    for j, r in enumerate(isl[t[:, 0]]):
        by.setdefault(r, []).append(j)
    for root, js in by.items():
        tt = t[js]
        vs = np.unique(tt)
        lo = uv[vs, k].min()
        r0, k0 = N.ratios(pos, uv, tt)
        if not len(r0):
            continue
        best, bf = _area_q(r0, _areas(pos, k0), 0.9), 1.0
        for f in FIT_STEPS:
            trial = uv.copy()
            trial[vs, k] = lo + (uv[vs, k] - lo) * f
            r, kk = N.ratios(pos, trial, tt)
            if len(r) and (m := _area_q(r, _areas(pos, kk), 0.9)) < best - 1e-6:
                best, bf = m, f
        uv[vs, k] = lo + (uv[vs, k] - lo) * bf
    sh.set_uv(uv)


def _vertex_colour(sh: N.Shape, op: dict) -> None:
    """lum_to: scale every vertex colour uniformly so the drawn luminance reaches the number (saturation kept);
    sat_to: a per-channel factor (a white balance) that takes the drawn mean colour to that saturation at the same
    luminance. Vertex_Colors is set on the property either way."""
    d = np.asarray(_diffuse_rgb(sh.prop.slots()[0]), float)
    c = sh.colours()
    f1, f2 = sh.prop.flags
    vc = c[:, :3] if c is not None and f2 >> N.F2["Vertex_Colors"] & 1 else np.full((sh.nv, 3), 255.0)
    eff = d * vc.mean(0) / 255
    if "lum_to" in op:
        k = op["lum_to"] / _lum(eff)
        new = vc * k
    else:
        L, lo, hi = _lum(eff), 0.0, 1.0
        for _ in range(40):
            s = (lo + hi) / 2
            lo, hi = (s, hi) if _sat(L + (eff - L) * s) < op["sat_to"] else (lo, s)
        tgt = L + (eff - L) * lo
        f = tgt / np.maximum(eff, 1e-6)
        new = vc * (f / max(1.0, float((vc.max(0) * f / 255).max())))  # no channel past 255: darker, same saturation
    sh.set_colours(new)
    sh.prop.set_flags(f1, f2 | 1 << N.F2["Vertex_Colors"])


def apply(n: N.Nif, entry: dict) -> list[str]:
    """Apply the entry's ops in place; return mismatches between the table's `before` and the bytes."""
    shapes = {s.i: s for s in n.shapes()}
    bad = []
    for se in entry["shapes"]:
        sh = shapes.get(se["shape"])
        if sh is None or sh.name != se["name"]:
            bad.append(f"shape {se['shape']} {se['name']}: not in the mesh")
            continue
        now = measure(sh)
        for k, v in (se.get("before") or {}).items():
            if now.get(k) != v:
                bad.append(f"shape {se['shape']} {k}: table {v}, bytes {now.get(k)}")
        ops = se.get("ops") or {}
        if "shader_from" in ops:  # a shape sharing a texture set it should not (a retexture's atlas strip)
            sh.set_shader(shapes[int(ops["shader_from"])].shader)
        p = sh.prop
        if "clear_flags" in ops or "set_flags" in ops:
            f1, f2 = p.flags
            c1, c2 = _flags(ops.get("clear_flags", []))
            s1, s2 = _flags(ops.get("set_flags", []))
            p.set_flags((f1 & ~c1) | s1, (f2 & ~c2) | s2)
        if "emissive" in ops:
            p.set_emissive(ops["emissive"]["rgb"], ops["emissive"]["mult"])
        for slot, path in (ops.get("texture_slot") or {}).items():
            p.set_slot(int(slot), path)
        if "vertex_colour" in ops:
            _vertex_colour(sh, ops["vertex_colour"])
        if "alpha" in ops:
            if sh.alpha is None:
                bad.append(f"shape {se['shape']}: alpha op on a shape with no NiAlphaProperty")
            else:
                sh.set_alpha(sh.alpha[0], int(ops["alpha"]["threshold"]))
        if "uv_scale" in ops:
            _uv_scale(sh, ops["uv_scale"]["axis"], ops["uv_scale"]["factor"])
    return bad


def bars(n: N.Nif, entry: dict) -> list[str]:
    kinds = {se["shape"]: se.get("kind") for se in entry["shapes"]}
    sat_op = {se["shape"] for se in entry["shapes"] if "sat_to" in ((se.get("ops") or {}).get("vertex_colour") or {})}
    out = []
    for sh in n.shapes():
        m = measure(sh)
        if sh.prop is None:
            continue
        tag = f"shape {sh.i} {sh.name}"
        if "Soft_Lighting" in m["flags"] and not m["slot2"]:
            out.append(f"{tag}: soft-lit with no soft-light map")
        if "Own_Emit" in m["flags"] and not entry.get("lore_emit"):
            out.append(f"{tag}: Own_Emit {m['emissive']} with no lore naming a glow")
        if kinds.get(sh.i) == "bark":
            if not m["slot1"]:
                out.append(f"{tag}: bark with no normal map")
            if m.get("lum") is not None and m["lum"] > BARK_LUM_BAR:
                out.append(f"{tag}: bark draws at luminance {m['lum']} > {BARK_LUM_BAR}")
            if m["stretch"] is not None and m["stretch"] > STRETCH_BAR:
                out.append(f"{tag}: UV stretch {m['stretch']}:1 > {STRETCH_BAR}:1")
            if m.get("stretch90") is not None and m["stretch90"] > STRETCH_P90_BAR and not entry.get("p90_owed"):
                out.append(f"{tag}: UV stretch p90 {m['stretch90']}:1 > {STRETCH_P90_BAR}:1")
        if sh.i in sat_op and m.get("sat") is not None and m["sat"] > LEAF_SAT_BAR + 0.005:
            out.append(f"{tag}: leaf draws at saturation {m['sat']} > {LEAF_SAT_BAR}")
    return out


def find(mods: list[Path], entry: dict) -> bytes:
    for root in mods:
        d = root / entry["mod"]
        if d.is_dir():
            try:
                return source.read(d, entry["mesh"])
            except FileNotFoundError:
                continue
    raise FileNotFoundError(f"{entry['mod']}/{entry['mesh']} in none of {', '.join(map(str, mods))}")


def run(mods: list[Path], out: Path | None = None, table: Path = TABLE, say=print) -> int:
    bad = 0
    for e in load(table):
        try:
            d = find(mods, e)
        except FileNotFoundError as x:
            say(f"FAIL {e['mesh']}: source not found ({x})")
            bad += 1
            continue
        n = N.Nif(d)
        before = {s.i: measure(s) for s in n.shapes()}
        problems = apply(n, e)
        data = n.to_bytes()
        n2 = N.Nif(data)  # verify by re-reading the written bytes
        problems += bars(n2, e)
        say(f"{'FAIL' if problems else 'ok  '} {e['mod']}/{e['mesh']} ({', '.join(e['forms'])})")
        for s in n2.shapes():
            if s.i in {x["shape"] for x in e["shapes"] if x.get("ops")}:
                a, b = before[s.i], measure(s)
                say(f"    shape {s.i} {s.name}:")
                for k in ("flags", "emissive", "alpha", "slot1", "slot2", "stretch", "stretch90", "lum", "sat"):
                    if k in a:
                        say(f"      {k:8} {a[k]} -> {b.get(k)}" if a[k] != b.get(k) else f"      {k:8} {a[k]} (kept)")
        for p in problems:
            say(f"    BAR {p}")
        if e.get("p90_owed"):
            say(f"    OWED p90: {e['p90_owed']}")
        bad += bool(problems)
        if out is not None and not problems:
            dst = out / e["mesh"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(data)
            if N.Nif(dst.read_bytes()).to_bytes() != data:
                say(f"FAIL {dst}: read-back differs")
                bad += 1
    say(f"{len(load(table))} meshes, {bad} failing")
    return 1 if bad else 0


def listing(out: Path = OUT, table: Path = TABLE, say=print) -> int:
    for e in load(table):
        say(f"{DERIVED}/{e['mesh']}  <- {e['mod']}/{e['mesh']}  ({', '.join(e['forms'])})")
    say(f"lay: {out} -> C:\\argonia\\ours\\derived\\{DERIVED} (stack.ps1 on: laid over every mod, so it wins)")
    return 0
