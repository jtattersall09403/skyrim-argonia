"""Canopy radii (lane 1.15-r6-water-stands-4): a placed plant form's OBND is not always the mesh's visible reach (a
ground plant or cattail whose fronds hang past the bounds). `python -m tools.journeys.canopy` measures each plant form's
mesh in the laid stack (tools/navmesh/nif_bounds: the box round the shapes' vertices) and writes the forms whose
horizontal reach from the pivot exceeds the OBND's by CANOPY_RATIO into data/canopy-radius.json (form key -> radius in
units). Build.shapes takes the larger of the two, so clearance and frustum cover reject a stand under those fronds.
Forms whose mesh the stack here cannot read keep their OBND."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TABLE = ROOT / "data" / "canopy-radius.json"
CANOPY_RATIO = 1.15   # a mesh reaching 15 % past its OBND is listed


def load(path: Path = TABLE) -> dict[str, float]:
    """form key -> canopy radius (units); empty when the table is absent."""
    try:
        return {k: float(v) for k, v in json.loads(path.read_text())["radius_u"].items()}
    except (OSError, ValueError, KeyError):
        return {}


def reach(shapes: dict, canopy: dict[str, float]) -> dict:
    """shapes (form key -> (radius, height, bushy, z0)) with each listed form's radius raised to its canopy radius."""
    return {k: ((max(v[0], canopy[k]), *v[1:]) if k in canopy else v) for k, v in shapes.items()}


def measure() -> dict[str, float]:
    import numpy as np  # noqa: F401  (nif_bounds needs it)
    from tools.argonia_world import db
    from tools.navmesh import nif_bounds
    from tools.navmesh.meshes import STACK, Resolver
    res = Resolver(STACK / ".." / "root" / "data")
    out = {}
    for r in db.open().query("SELECT form_key, role_id, model, bound_x0, bound_x1, bound_y0, bound_y1 FROM object_form "
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
    return out


if __name__ == "__main__":
    t = measure()
    TABLE.write_text(json.dumps({"note": "mesh reach past the OBND, units; made by python -m tools.journeys.canopy", "radius_u": t},
                                indent=1, sort_keys=True) + "\n")
    print(f"{len(t)} forms listed in {TABLE}")
