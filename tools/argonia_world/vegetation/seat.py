"""How BM&V seats its own trees (lane 1.15-r4-trees; decision 0034: measure the mod's answer, do the same).

Owner play test 3, finding 4: "many have bases hovering in mid air (trailing roots touch ground)". The placer set a
tree's pivot on the ground (place.Rule.sink_m = 0 for every non-rock form), but a tree's pivot is not its trunk base:
the mesh author puts it where the author's own placement wanted it, and BM&V sinks its trees by its own amount. So
per landscape form we measure, over every REFR the Black Marsh mods place of it (forms.PLUGINS), the pivot's depth under
BM&V's own ground at the ref (the LAND's VHGT, bilinear in the quad), divided by the ref's scale: the model's seat
(units at scale 1, positive below the ground). The median is the seat; the placer sinks the pivot by it.

    python3 -m tools.argonia_world.vegetation seat [--stack <MO2>] [--out data/tree-seat.json]
        (machine-local: reads the laid plugin; writes numbers only, never a record's content: decision 0003)
"""
from __future__ import annotations

import json
import struct
from collections import defaultdict
from pathlib import Path

import numpy as np

from tools.argonia_world.terrain.esm import records
from tools.navmesh.meshes import STACK

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data" / "tree-seat.json"
MIN_REFS = 5  # fewer refs: no measured seat (the form is not listed as a tree)
HANG_MAX = 10.0  # units: a mesh whose lowest point stands higher above the ground at its seat hangs
CELL = 4096.0
STEP = 128.0


def vhgt(b: bytes) -> np.ndarray:
    off = struct.unpack_from("<f", b, 0)[0]
    d = np.frombuffer(b, np.int8, 33 * 33, 4).reshape(33, 33).astype(np.float64)
    col = np.cumsum(d[:, 0])
    return (off + col[:, None] + np.cumsum(np.c_[np.zeros(33), d[:, 1:]], axis=1)) * 8.0


def ground(h: np.ndarray, x: float, y: float, cell: tuple[int, int]) -> float:
    """BM&V's ground at (x, y) in the cell's LAND: rows run south to north, columns west to east."""
    fx = (x - cell[0] * CELL) / STEP
    fy = (y - cell[1] * CELL) / STEP
    i, j = min(max(int(fy), 0), 31), min(max(int(fx), 0), 31)
    ty, tx = min(max(fy - i, 0.0), 1.0), min(max(fx - j, 0.0), 1.0)
    a = h[i, j] * (1 - tx) + h[i, j + 1] * tx
    b = h[i + 1, j] * (1 - tx) + h[i + 1, j + 1] * tx
    return float(a * (1 - ty) + b * ty)


def _key(fid: int, masters: list[str], name: str) -> str:
    i = fid >> 24
    return f"{fid & 0xFFFFFF:06X}:{masters[i] if i < len(masters) else name}"


def measure(stack: Path = STACK) -> dict[str, dict]:
    """{forms: form_key -> {seat: median units under the ground at scale 1, p10, p90, refs}, models: the same by mesh},
    over every REFR the Black Marsh
    mods (forms.PLUGINS, load order) place of their landscape forms, on the ground the stack lays at that cell (a
    later plugin's LAND over an earlier one's)."""
    from tools.argonia_world.vegetation import forms
    land: dict[tuple, np.ndarray] = {}
    refs, model = [], {}
    for mod, name in forms.PLUGINS:
        p = stack / "mods" / mod / name
        if not p.exists():
            raise FileNotFoundError(f"{p}: the laid stack is not on this machine")
        masters, wrld, cell = [], None, None
        for r in records(p.read_bytes()):
            if r.sig == "TES4":
                masters = [b.split(b"\0", 1)[0].decode("latin-1") for s, b in r.subs if s == "MAST"]
            elif r.sig in ("TREE", "STAT", "FLOR") and (r.formid >> 24) == len(masters):
                m = r.first("MODL")
                if m:
                    model[_key(r.formid, masters, name)] = mkey(m.split(b"\0", 1)[0].decode("latin-1"))
            elif r.sig == "WRLD":
                wrld = _key(r.formid, masters, name)
            elif r.sig == "CELL":
                xc = r.first("XCLC")
                cell = (wrld, *struct.unpack_from("<ii", xc)) if xc and wrld else None
            elif r.sig == "LAND" and cell is not None:
                v = r.first("VHGT")
                if v:
                    land[cell] = vhgt(v)
            elif r.sig == "REFR" and cell is not None:
                nm, data = r.first("NAME"), r.first("DATA")
                if not nm or not data:
                    continue
                x, y, z = struct.unpack_from("<3f", data)
                s = r.first("XSCL")
                refs.append((_key(struct.unpack_from("<I", nm)[0], masters, name), cell, x, y, z,
                             struct.unpack_from("<f", s)[0] if s else 1.0))
    by, bym = defaultdict(list), defaultdict(list)
    for fk, c, x, y, z, s in refs:
        if c in land and s > 0 and fk in model:
            d = (ground(land[c], x, y, c[1:]) - z) / s
            by[fk].append(d)
            bym[model[fk]].append(d)

    def stat(v):
        a = np.asarray(v)
        return {"seat": round(float(np.median(a)), 1), "p10": round(float(np.percentile(a, 10)), 1),
                "p90": round(float(np.percentile(a, 90)), 1), "refs": int(a.size)}
    return {"forms": {k: stat(v) for k, v in sorted(by.items())},
            "models": {k: stat(v) for k, v in sorted(bym.items())}}


def load(path: Path = OUT) -> dict[str, dict]:
    return json.loads(path.read_text()) if path.exists() else {}


def _measured(form_key: str, model: str | None, table: dict) -> dict | None:
    t = table.get("forms", {}).get(form_key)
    if t and t["refs"] >= MIN_REFS:
        return t
    t = table.get("models", {}).get(mkey(model))  # another base of the same mesh, placed by its mod
    return t if t and t["refs"] >= MIN_REFS else None


def seat_of(form_key: str, model: str | None, table: dict) -> float:
    """A tree form's pivot depth under the ground (units at scale 1): its mod's own median seat for the form, else
    for its mesh under another base (MIN_REFS refs or more); 0 when never measured (standing() keeps those out)."""
    t = _measured(form_key, model, table)
    return float(t["seat"]) if t else 0.0


def standing(form_key: str, model: str | None, bound_z0: int | None, table: dict) -> bool:
    """True when the form has a measured seat and its lowest point (OBND z0) is at or under the ground there: a
    form whose mesh starts HANG_MAX above the ground at its own mod's seat hangs from something (moss, a branch)."""
    t = _measured(form_key, model, table)
    return t is not None and (bound_z0 or 0) - t["seat"] <= HANG_MAX


def mkey(model: str | None) -> str:
    return (model or "").lower().replace("/", "\\")


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="vegetation seat")
    ap.add_argument("--stack", type=Path, default=STACK)
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args(argv)
    t = measure(a.stack)
    a.out.write_text(json.dumps(t, indent=1, sort_keys=True) + "\n")
    print(f"{len(t['forms'])} forms, {len(t['models'])} meshes measured -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
