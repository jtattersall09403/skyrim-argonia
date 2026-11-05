"""The region shells and the border's cell runs: what the terrain stage needs of the regions (ArgoniaWorld.esm's REGN
shells, the cells' region runs, the border polygon's cells). Kept apart from api.py so the terrain's stamp walk does not
reach the weather tables (api imports regions.classify's weather lists): a weather colour change re-keys no land pass.
api.py re-exports every name here."""
from __future__ import annotations

from tools.argonia_world import skyrim_units as su

LAND_PLUGIN = "ArgoniaWorld.esm"
REGION_SHELL_BASE = 0x080000  # ArgoniaWorld.esm: past the terrain's CELL/LAND range (to 0x22A30), below the water's


# --- the shells (ArgoniaWorld.esm) ---------------------------------------------------------------------------
def shell_keys(world, frozen: bool = True) -> dict[str, str]:
    """{land_region id: shell FormKey}, allocating new regions append-only unless frozen."""
    have = {r.editor_id: r.form_id for r in world.rows("formid", plugin=LAND_PLUGIN) if r.record_type == "REGN"}
    out = {}
    for r in world.query("SELECT id, edid, border FROM land_region ORDER BY id"):
        # the border's EditorID already names its Argonia.esm id (before it had a shell); its shell row takes a suffix
        key = f"{r['edid']}Shell" if r["border"] else r["edid"]
        if key not in have:
            if frozen:
                raise KeyError(f"{r['edid']}: no shell id yet; run `make plugin` and commit the formid table")
            fid = max(have.values(), default=REGION_SHELL_BASE - 1) + 1
            world.insert("formid", editor_id=key, plugin=LAND_PLUGIN, form_id=fid, record_type="REGN",
                         entity_key=f"land_region.{r['id']}" + (".shell" if r["border"] else ""))
            have[key] = fid
        out[r["id"]] = f"{have[key]:06X}:{LAND_PLUGIN}"
    return out


def shell_records(world) -> list[dict]:
    keys = shell_keys(world)
    edid = dict(world.query("SELECT id, edid FROM land_region"))
    return [{"type": "REGN", "formKey": keys[k], "edid": edid[k]} for k in sorted(keys, key=keys.get)]


def cell_region_runs(world) -> list[dict]:
    keys = shell_keys(world)
    return [{"cy": r["cy"], "cx0": r["cx0"], "cx1": r["cx1"], "region": keys[r["land_region_id"]]}
            for r in world.query("SELECT * FROM cell_region_run ORDER BY cy, cx0")]


def border_shell_key(world) -> str | None:
    keys = shell_keys(world)
    row = world.query("SELECT id FROM land_region WHERE border = 1 ORDER BY id")
    return keys[row[0]["id"]] if row else None


def _inside(px: float, py: float, poly) -> bool:
    c = False
    for k in range(len(poly)):
        (x1, y1), (x2, y2) = poly[k], poly[k - 1]
        if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
            c = not c
    return c


def border_cell_runs(poly=None) -> list[dict]:
    """The cells whose square overlaps the border polygon, as row runs: vanilla's rule (a cell lists the border
    when a corner lies inside it). Corners are tested 1 unit inside the cell, so a cell that only touches the edge
    from outside is not listed."""
    poly = poly if poly is not None else border_polygon()
    c = su.CELL_UNITS
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    out = []
    for cy in range(int(min(ys) // c) - 1, int(max(ys) // c) + 1):
        row = []
        for cx in range(int(min(xs) // c) - 1, int(max(xs) // c) + 1):
            x0, y0 = cx * c, cy * c
            pts = [(x0 + 1, y0 + 1), (x0 + c - 1, y0 + 1), (x0 + 1, y0 + c - 1), (x0 + c - 1, y0 + c - 1),
                   (x0 + c / 2, y0 + c / 2)]
            if any(_inside(px, py, poly) for px, py in pts):
                row.append(cx)
        for cx in row:
            if out and out[-1]["cy"] == cy and out[-1]["cx1"] == cx - 1:
                out[-1]["cx1"] = cx
            else:
                out.append({"cy": cy, "cx0": cx, "cx1": cx})
    return out


def border_polygon() -> list[list[float]]:
    from tools.argonia_world.terrain.edges import border_polygon as bp
    return bp()
