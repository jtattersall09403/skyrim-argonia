"""Canopy radii (lane 1.15-r6-water-stands-4): a placed plant form's OBND is not always the mesh's visible reach (a
ground plant or cattail whose fronds hang past the bounds). `python -m tools.journeys.canopy` measures each plant form's
mesh in the laid stack (tools/navmesh/nif_bounds: the box round the shapes' vertices) and writes the forms whose
horizontal reach from the pivot exceeds the OBND's by CANOPY_RATIO into data/canopy-radius.json (form key -> radius in
units). Build.shapes takes the larger of the two, so clearance and frustum cover reject a stand under those fronds.
Forms whose mesh the stack here cannot read keep their OBND. Lane 1.15-r6-water-stands-5: the fronds also stand past the
OBND's height (King of the Murkmire's Bush01: OBND -16..113 units, its fronds -185..438), so a form whose mesh top
reaches CANOPY_RATIO past the OBND's is listed too, with its mesh z extent (z_u: form key -> [z0, z1] units), and
Build.shapes takes the taller span: the clearance's eye line meets fronds standing over the eye.""" 
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TABLE = ROOT / "data" / "canopy-radius.json"
CANOPY_RATIO = 1.15   # a mesh reaching 15 % past its OBND is listed


def load(path: Path = TABLE) -> dict[str, tuple]:
    """form key -> (canopy radius, mesh z0, mesh z1 or None) units; empty when the table is absent."""
    try:
        t = json.loads(path.read_text())
        z = t.get("z_u", {})
        return {k: (float(t["radius_u"].get(k, 0.0)), *(map(float, z[k]) if k in z else (None, None)))
                for k in set(t["radius_u"]) | set(z)}
    except (OSError, ValueError, KeyError, AttributeError):
        return {}


def widen(v: tuple, c) -> tuple:
    """One shape (radius, height, bushy, z0) widened to its canopy entry: the larger radius, and the span from the
    lower bottom to the higher top."""
    r, h, bushy, z0 = v
    c = c if isinstance(c, tuple) else (float(c), None, None)
    r = max(r, c[0])
    if c[1] is not None:
        lo, hi = min(z0, c[1]), max(z0 + h, c[2])
        z0, h = lo, hi - lo
    return r, h, bushy, z0


def reach(shapes: dict, canopy: dict) -> dict:
    """shapes (form key -> (radius, height, bushy, z0)) with each listed form widened to its canopy entry."""
    return {k: (widen(v, canopy[k]) if k in canopy else v) for k, v in shapes.items()}


def measure() -> tuple[dict[str, float], dict[str, list]]:
    import numpy as np  # noqa: F401  (nif_bounds needs it)
    from tools.argonia_world import db
    from tools.navmesh import nif_bounds
    from tools.navmesh.meshes import STACK, Resolver
    res = Resolver(STACK / ".." / "root" / "data")
    out, zs = {}, {}
    for r in db.open().query("SELECT form_key, role_id, model, bound_x0, bound_x1, bound_y0, bound_y1, bound_z1 FROM object_form "
                             "WHERE role_id != 'rock'"):
        data = res.read(r["model"]) if r["model"] else None
        if data is None:
            continue
        try:
            nb = nif_bounds.bounds(data)
        except Exception:   # an unreadable mesh keeps its OBND
            continue
        obnd = max(1.0, abs(r["bound_x0"] or 0), abs(r["bound_x1"] or 0), abs(r["bound_y0"] or 0), abs(r["bound_y1"] or 0))
        mesh = max(abs(nb["lo"][0]), abs(nb["hi"][0]), abs(nb["lo"][1]), abs(nb["hi"][1]))
        if mesh > obnd * CANOPY_RATIO:
            out[r["form_key"]] = round(mesh, 1)
        top = max(1.0, r["bound_z1"] or 0)
        if nb["hi"][2] > top * CANOPY_RATIO:
            zs[r["form_key"]] = [round(nb["lo"][2], 1), round(nb["hi"][2], 1)]
    return out, zs


if __name__ == "__main__":
    t, z = measure()
    TABLE.write_text(json.dumps({"note": "mesh reach past the OBND, units; made by python -m tools.journeys.canopy",
                                 "radius_u": t, "z_u": z}, indent=1, sort_keys=True) + "\n")
    print(f"{len(t)} radii, {len(z)} heights listed in {TABLE}")
