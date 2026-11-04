"""The install-time mesh patcher (lane 1.15-r6-mesh-patcher; decisions 0014, 0034, 0003).

Some placed forms draw the wrong colours because of their own NIF, not our data (owner #37, 2026-11-04 07:36: find
the cause and fix it, never drop): a soft-lit leaf with no soft-light map, Own_Emit on a leaf or bark, a bark normal in
the wrong slot, a bark UV stretched tens of times along one axis. A modder fixes these in NifSkope; we write the same
edits as data (data/mesh-patches.yaml: per mesh and shape, the measured before, the ops, the reason) and this tool
applies them to the source mod's mesh on the player's machine side of the build (the deploy's lay step), writing
copies into a derived mod folder that wins over the source mods. Nothing patched is ever committed.

Ops (per shape): clear_flags / set_flags [names of nif.F1/F2]; emissive {rgb, mult}; texture_slot {slot: path};
uv_scale {axis: u|v, factor: <number> | fit} (fit: per UV island, the factor from FIT_STEPS that minimises the
island's median stretch; the island is scaled about its own minimum so the half floats stay small).
Bars, every shape of a patched mesh, after: a soft-lit shape has a slot-2 map; no shape is Own_Emit unless the entry
names the lore (`lore_emit`); a shape of kind bark has a normal (slot 1) and a median UV stretch <= STRETCH_BAR.

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
DERIVED = "argonia-mesh-patches"  # the derived mod folder's name on the machine (stack.ps1 lays it last)
OUT = ROOT / "out" / "mesh_patches" / DERIVED
STRETCH_BAR = 6.0  # the placed bark band's top (lane 1.15-r5-white-trunks: 3:1 to 6:1; global median 1.7:1)
FIT_STEPS = np.geomspace(1 / 128, 128, 57)


def load(path: Path = TABLE) -> list[dict]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))["meshes"]


def measure(sh: N.Shape) -> dict:
    p = sh.prop
    m = {"name": sh.name}
    if p is not None:
        f1, f2 = p.flags
        sl = p.slots() + [""] * 3
        m.update(flags=N.flag_names(f1, f2), emissive=list(p.emissive), soft=p.soft, slot1=sl[1], slot2=sl[2])
    st = sh.stretch() if sh.has_uv() else None
    m["stretch"] = None if st is None else round(st, 1)
    return m


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
        r0, _ = N.ratios(pos, uv, tt)
        if not len(r0):
            continue
        best, bf = float(np.median(r0)), 1.0
        for f in FIT_STEPS:
            trial = uv.copy()
            trial[vs, k] = lo + (uv[vs, k] - lo) * f
            r, _ = N.ratios(pos, trial, tt)
            if len(r) and (m := float(np.median(r))) < best - 1e-6:
                best, bf = m, f
        uv[vs, k] = lo + (uv[vs, k] - lo) * bf
    sh.set_uv(uv)


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
        if "uv_scale" in ops:
            _uv_scale(sh, ops["uv_scale"]["axis"], ops["uv_scale"]["factor"])
    return bad


def bars(n: N.Nif, entry: dict) -> list[str]:
    kinds = {se["shape"]: se.get("kind") for se in entry["shapes"]}
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
            if m["stretch"] is not None and m["stretch"] > STRETCH_BAR:
                out.append(f"{tag}: UV stretch {m['stretch']}:1 > {STRETCH_BAR}:1")
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
            if s.i in {x["shape"] for x in e["shapes"]}:
                a, b = before[s.i], measure(s)
                say(f"    shape {s.i} {s.name}:")
                for k in ("flags", "emissive", "soft", "slot1", "slot2", "stretch"):
                    if k in a:
                        say(f"      {k:8} {a[k]!s:60} -> {b.get(k)}" if a[k] != b.get(k) else f"      {k:8} {a[k]}")
        for p in problems:
            say(f"    BAR {p}")
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
    say(f"lay: {out} -> C:\\argonia\\MO2\\mods\\{DERIVED} (stack.ps1 on: laid after every profile mod, so it wins)")
    return 0
