"""Our own rock forms (1.15 §e.2, the planner's ruling of 2026-11-01): Black Marsh & Valenwood ships 312 rock meshes
with no record (only 2 boulder forms exist), so ArgoniaWorld.esm carries one STAT per chosen BM&V mesh (route 1,
data: the player installs BM&V; the record only names the mesh). Each form's OBND is the NIF's own vertex box
(tools/navmesh/nif_bounds.py), read once from the archive into object_form; the sink is lists.SINK_BOULDER of it.

    python3 -m tools.argonia_world.vegetation rocks --nifs <dir>     (<dir>/meshes/<path> unpacked from BM&V)

Families, so the rocks vary by region (lists.admits): Morrowind's region rock sets in BM&V, each where its look fits
- az: Azura's Coast, the province over Black Marsh's north-east border: the northern transition
- gl: the Grazelands' grassy boulders: the uplands (northern transition, western frontier)
- al: the Ascadian Isles' green temperate rock: the western frontier's hills and the river walls
- bm: BM&V's own landscaping boulders: every rock-bearing eco class
(lore regions/blackwood-and-gloommire.md:13-14; regional-variety-audit row 1; rock-placement-rules.md rules 1, 6).
"""
from __future__ import annotations

from pathlib import Path

PLUGIN = "ArgoniaWorld.esm"
BASE = 0x0C0000  # ArgoniaWorld.esm: past the REGN shells (0x080000), below the water (0x100000)
# (index, BM&V mesh under meshes/, family): the index fixes the FormID, so a row is only ever appended
ROCKS = (
    (0, r"landscape\rocks\azrocks\coast\az_rock02.nif", "az"),
    (1, r"landscape\rocks\azrocks\coast\az_rock03.nif", "az"),
    (2, r"landscape\rocks\azrocks\coast\az_rock05.nif", "az"),
    (3, r"landscape\rocks\azrocks\coast\az_rock07.nif", "az"),
    (4, r"landscape\rocks\azrocks\coast\az_rock09.nif", "az"),
    (5, r"landscape\rocks\glrocks\gl_rock03.nif", "gl"),
    (6, r"landscape\rocks\glrocks\gl_rock04.nif", "gl"),
    (7, r"landscape\rocks\glrocks\gl_rock06.nif", "gl"),
    (8, r"landscape\rocks\glrocks\gl_rock09.nif", "gl"),
    (9, r"landscape\rocks\glrocks\gl_rock11.nif", "gl"),
    (10, r"landscape\rocks\alrocks\al_rock11.nif", "al"),
    (11, r"landscape\rocks\alrocks\al_rock12.nif", "al"),
    (12, r"landscape\rocks\alrocks\al_rock13.nif", "al"),
    (13, r"landscape\rocks\alrocks\al_rock14.nif", "al"),
    (14, r"landscape\rocks\alrocks\al_rock15.nif", "al"),
    (15, r"landscaping\rocks\from_online_resource\rock_28.nif", "bm"),
    (16, r"landscaping\rocks\from_online_resource\rock_30.nif", "bm"),
    (17, r"landscaping\rocks\from_online_resource\rock_32.nif", "bm"),
    (18, r"landscaping\rocks\from_online_resource\rock_33.nif", "bm"),
    (19, r"landscaping\rocks\from_online_resource\rock_35.nif", "bm"),
)
FAMILY_ECO = {"az": ("northern-transition",), "gl": ("northern-transition", "western-frontier"),
              "al": ("western-frontier", "deep-river-corridor"),
              "bm": ("northern-transition", "western-frontier", "deep-river-corridor")}


def form_key(i: int) -> str:
    return f"{BASE + i:06X}:{PLUGIN}"


def edid(model: str) -> str:
    return "ARG_Rock_" + Path(model.replace("\\", "/")).stem


def family(model: str | None) -> str | None:
    m = (model or "").lower()
    return next((fam for _, p, fam in ROCKS if p.lower() == m), None)


def write(w, nifs: Path) -> int:
    """object_form rows for ROCKS, their OBND from each NIF's vertex box (units, rounded outward)."""
    import math

    from tools.navmesh import nif_bounds
    files = {str(p.relative_to(nifs)).lower(): p for p in nifs.rglob("*.nif")}  # the archive's paths keep their case
    for i, model, fam in ROCKS:
        b = nif_bounds.bounds(files["meshes/" + model.replace("\\", "/").lower()].read_bytes())
        lo = [math.floor(v) for v in b["lo"]]
        hi = [math.ceil(v) for v in b["hi"]]
        w.upsert("object_form", form_key=form_key(i), edid=edid(model), record_type="STAT", role_id="rock",
                 ts_model=None, review=(f"our STAT in {PLUGIN} naming BM&V's own rock mesh ({fam} family; "
                                        "the player's BM&V supplies it, 1.15 ruling); nothing Nordic (0006)"),
                 mod="bmv", model=model, mesh_source="bmv", bound_x0=lo[0], bound_y0=lo[1], bound_z0=lo[2],
                 bound_x1=hi[0], bound_y1=hi[1], bound_z1=hi[2], placed_by_mod=0)
    return len(ROCKS)


def records(w) -> list[dict]:
    """The STAT records for world.json (LandWorld.cs writes them into ArgoniaWorld.esm)."""
    rows = w.query("SELECT * FROM object_form WHERE form_key LIKE ? ORDER BY form_key", f"%:{PLUGIN}")
    return [{"type": "STAT", "formKey": r["form_key"], "edid": r["edid"], "model": r["model"],
             "bounds": [[r["bound_x0"], r["bound_y0"], r["bound_z0"]], [r["bound_x1"], r["bound_y1"], r["bound_z1"]]]}
            for r in rows]


def masters(w) -> list[str]:
    """The plugins whose forms the region lists place, in the stack's plugin order: ArgoniaWorld.esm's REFRs are
    spliced in after Mutagen writes it (VegetationRecords.cs), so it names them as masters up front."""
    import json
    deps = json.loads((Path(__file__).resolve().parents[3] / "data" / "dependencies.json").read_text(encoding="utf-8"))
    order = [p if isinstance(p, str) else p["file"] for p in deps["plugins"]]
    used = {r["p"] for r in w.query("SELECT DISTINCT substr(form_key, 8) AS p FROM land_region_object")} - {PLUGIN}
    return [p for p in order if p in used] + sorted(used - set(order))
