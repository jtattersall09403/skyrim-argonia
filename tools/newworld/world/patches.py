"""The world's local patches of ground, laid over the fixed base: each patch changes the heights of the vertices it
names, and only the cells whose heights or normals that changes are written, in rows of their own beside the base's.

    python3 -m tools.newworld.world.patches apply --plugin out/newworld/plugin --patches newworld/sources/ground_patches.jsonl
    python3 -m tools.newworld.world.patches check --plugin out/newworld/plugin --patches newworld/sources/ground_patches.jsonl

The base (`<plugin>/land/`: the limited heights `limited.npy` and one shard per cell row) is the province's ground,
pinned and never rewritten (the skill world-build). A patch row is a place's `land.jsonl` row with an id and a reason:

    {"id": "patch.0001", "by": "agent" | "owner", "why": "...", "cell": [cx, cy], "verts": [[row, col, dz], ...]}

`row` counts vertices from the cell's south edge and `col` from its west edge (0..32), `dz` is game units, added to
the base's height there (the rows' changes to one vertex are summed; a vertex two cells share takes one height).
Every patch is applied to the base each time, never to an earlier patch's output, so the same rows write the same
bytes and a removed row leaves the base as it was.

Out: `<plugin>/patch/land/<shard>` for each row of cells a patch changes: the base's row, byte for byte, with the
changed cells' heights and normals rewritten; and `<plugin>/patch/land/manifest.json` (the base's key, the patches'
digest, the cells changed and the rows written). The world file's writer reads a patched row in place of the base's
(tools/ArgoniaPlugin/NewWorld.cs), and its check holds a patched cell to the patch and every other cell to the base.
A row no patch reaches any longer is removed. `check` proves every written row is the base's outside the cells a
patch reaches, and that applying the rows again writes the same bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np

from tools.newworld.world import land as nwland, quantize
from tools.newworld.world import units as su

V = su.LAND_VERTS
CELL_BYTES = nwland.CELL_BYTES


class PatchError(ValueError):
    """A patch row that cannot be applied."""


def read_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    for r in rows:
        if not isinstance(r.get("id"), str) or not r["id"]:
            raise PatchError("a patch row needs an id")
        if not r.get("why"):
            raise PatchError(f"{r['id']}: a patch row says why")
        c = r.get("cell")
        if not (isinstance(c, list) and len(c) == 2 and all(isinstance(v, int) for v in c)):
            raise PatchError(f"{r['id']}: cell must be [cx, cy]")
        for v in r.get("verts") or []:
            if not (len(v) == 3 and 0 <= int(v[0]) < V and 0 <= int(v[1]) < V):
                raise PatchError(f"{r['id']}: vertex {v} lies outside the cell (0..{V - 1})")
    return rows


def _grid(plugin: Path) -> tuple[su.Grid, dict]:
    man = json.loads((plugin / "land/manifest.json").read_text())
    return su.Grid(**{k: man["grid"][k] for k in ("build_id", "width", "height", "origin_x", "origin_y", "water")}), man


def reach(rows: list[dict]) -> set[tuple[int, int]]:
    """The cells a patch may change: each patched cell and the ring round it (a height on an edge is its neighbour's
    too, and a normal reads the vertex beyond)."""
    return {(cx + dx, cy + dy) for r in rows for cx, cy in [r["cell"]] for dx in (-1, 0, 1) for dy in (-1, 0, 1)}


def patched_cells(plugin: Path, rows: list[dict]) -> dict[tuple[int, int], bytes]:
    """{cell: its new bytes in a shard (offset, VHGT deltas, VNML)} for every cell whose heights or normals the rows
    change, computed from the base alone."""
    if not rows:
        return {}
    g, _ = _grid(plugin)
    lim = np.load(plugin / "land/limited.npy", mmap_mode="r")         # [row from the north, col from the west], steps
    target: dict[tuple[int, int], int] = {}
    summed: dict[tuple[int, int], dict[tuple[int, int], float]] = {}
    for r in rows:
        c = summed.setdefault(tuple(r["cell"]), {})
        for row, col, dz in r.get("verts") or []:
            c[(int(row), int(col))] = c.get((int(row), int(col)), 0.0) + float(dz)
    for (cx, cy), d in summed.items():
        if not (g.cx0 <= cx < g.cx0 + g.cells_x and g.cy_bottom <= cy <= g.cy_top):
            raise PatchError(f"cell {cx},{cy} lies outside the world's grid")
        north, south = g.cell_rows(cy)
        west, _ = g.cell_cols(cx)
        for (row, col), dz in d.items():
            gi, gj = south - row, west + col
            v = int(round(float(lim[gi, gj]) + dz / su.VHGT_STEP_UNITS))
            if target.get((gi, gj), v) != v:
                raise PatchError(f"vertex {gi},{gj} (cell {cx},{cy}) patched to two heights")
            target[(gi, gj)] = v
    ii = [k[0] for k in target]
    jj = [k[1] for k in target]
    # a window two vertices wider than the cells' ring: its normals inside are the whole grid's
    r0, r1 = max(min(ii) - 2 * (V - 1), 0), min(max(ii) + 2 * (V - 1), lim.shape[0] - 1)
    c0, c1 = max(min(jj) - 2 * (V - 1), 0), min(max(jj) + 2 * (V - 1), lim.shape[1] - 1)
    before = np.array(lim[r0:r1 + 1, c0:c1 + 1], np.int64)
    after = before.copy()
    for (gi, gj), v in target.items():
        after[gi - r0, gj - c0] = v
    nb, na = nwland.normals(before), nwland.normals(after)
    out: dict[tuple[int, int], bytes] = {}
    for cx, cy in sorted(reach(rows)):
        if not (g.cx0 <= cx < g.cx0 + g.cells_x and g.cy_bottom <= cy <= g.cy_top):
            continue
        north, south = g.cell_rows(cy)
        a, b = g.cell_cols(cx)
        sl = (slice(north - r0, south - r0 + 1), slice(a - c0, b - c0 + 1))
        if np.array_equal(before[sl], after[sl]) and np.array_equal(nb[sl], na[sl]):
            continue
        offset, d = quantize.encode(after[sl][::-1])
        out[(cx, cy)] = np.float32(offset).tobytes() + d.tobytes() + np.ascontiguousarray(na[sl][::-1]).tobytes()
    return out


def rows_of(plugin: Path, cells: dict[tuple[int, int], bytes]) -> dict[str, bytes]:
    """{shard name: the base's row with the changed cells' bytes in place}."""
    g, _ = _grid(plugin)
    out: dict[str, bytes] = {}
    for cy in sorted({c[1] for c in cells}):
        name = nwland.shard_name(cy)
        data = bytearray((plugin / "land" / name).read_bytes())
        for (cx, y), b in cells.items():
            if y == cy:
                o = (cx - g.cx0) * CELL_BYTES
                data[o:o + CELL_BYTES] = b
        out[name] = bytes(data)
    return out


def _atomic(p: Path, data: bytes) -> None:
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, p)


def apply(plugin: Path, patches: Path) -> dict:
    rows = read_rows(patches)
    _, man = _grid(plugin)
    cells = patched_cells(plugin, rows)
    shards = rows_of(plugin, cells)
    out = plugin / "patch/land"
    out.mkdir(parents=True, exist_ok=True)
    for name, data in shards.items():
        p = out / name
        if not p.exists() or p.read_bytes() != data:
            _atomic(p, data)
    for p in out.glob("cy*.bin"):
        if p.name not in shards:
            p.unlink()
    doc = {"base_key": man["key"], "patches": [r["id"] for r in rows],
           "patches_sha256": hashlib.sha256(patches.read_bytes()).hexdigest() if patches.exists() else None,
           "cells": [list(c) for c in sorted(cells)], "shards": sorted(shards)}
    _atomic(out / "manifest.json", json.dumps(doc, indent=1).encode())
    print(f"ground patches: {len(rows)} rows, {len(cells)} cells changed in {len(shards)} rows of cells "
          f"({', '.join(f'{c[0]},{c[1]}' for c in sorted(cells)[:8])}{' ...' if len(cells) > 8 else ''})")
    return doc


def check(plugin: Path, patches: Path) -> list[str]:
    """Faults: a written row that differs from the base outside the cells the patches reach, a cell changed outside
    their reach, a row on disk the patches do not write, or a second application that writes other bytes."""
    rows = read_rows(patches)
    g, man = _grid(plugin)
    out = plugin / "patch/land"
    faults = []
    doc = json.loads((out / "manifest.json").read_text())
    if doc["base_key"] != man["key"]:
        faults.append(f"the patches were laid on base {doc['base_key']}, the base is {man['key']}")
    near = reach(rows)
    for c in doc["cells"]:
        if tuple(c) not in near:
            faults.append(f"cell {c[0]},{c[1]} changed, outside every patch's reach")
    want = rows_of(plugin, patched_cells(plugin, rows))
    on_disk = {p.name for p in out.glob("cy*.bin")}
    if on_disk != set(want):
        faults.append(f"rows on disk {sorted(on_disk ^ set(want))[:4]} are not the patches' rows")
    for name in sorted(on_disk & set(want)):
        data, base = (out / name).read_bytes(), (plugin / "land" / name).read_bytes()
        if data != want[name]:
            faults.append(f"{name}: applying the patches again writes other bytes")
        cy = int(name[2:-4])
        for i in range(g.cells_x):
            o = i * CELL_BYTES
            if (g.cx0 + i, cy) not in near and data[o:o + CELL_BYTES] != base[o:o + CELL_BYTES]:
                faults.append(f"{name}: cell {g.cx0 + i},{cy} differs from the base outside the patches' reach")
    print(f"ground patches check: {len(rows)} rows, {len(doc['cells'])} cells, {len(on_disk)} rows of cells: "
          + ("PASS" if not faults else "FAIL"))
    for f in faults[:20]:
        print(f"  FAIL {f}")
    return faults


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=("apply", "check"))
    ap.add_argument("--plugin", type=Path, default=Path("out/newworld/plugin"))
    ap.add_argument("--patches", type=Path, default=Path("newworld/sources/ground_patches.jsonl"))
    a = ap.parse_args(argv)
    try:
        if a.cmd == "apply":
            apply(a.plugin, a.patches)
            return 0
        return 1 if check(a.plugin, a.patches) else 0
    except PatchError as e:
        print(f"FAIL {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
