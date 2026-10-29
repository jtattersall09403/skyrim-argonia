"""The terrain family's rows (2.W1), written through db.py: the inputs by sha256, the land-cover classes and their
LTEX, and each old terrain or route-grade patch's outcome from the old chain's receipts in `$ARGONIA_DATA/terrain/`.

    python3 -m tools.argonia_world.terrain.migrate      write (or update) the rows; idempotent
    python3 -m tools.argonia_world.terrain.migrate grass   seed the grass plan from out/ltex-scan.json (ArgoniaGen ltex)

The patch definitions themselves (the old `terrain-patches.json` and `route-grade-patches.json`, still among the
unmigrated sources) stay unmigrated: the generator reads the old chain's post-patch array, which the receipts tie to the frozen base by
sha256 (grid.py). They move into the database when a lane first re-applies or edits a patch.
"""
from __future__ import annotations

import json
import sys

from tools.argonia_world import db
from tools.argonia_world.terrain import vault
from tools.argonia_world.terrain.landcover import seed_rows

INPUTS = {  # local name -> (role, source and licence)
    "refined-height-f32.npy": ("province ground after every applied patch", "the old project's chain (ours)"),
    "landcover-i16.npy": ("land-cover class per sample", "the old project's ground control (ours)"),
    "apron-source-near.npy": ("the near apron's heights", "Transbot9 All-Tamriel heightmap, CC BY-NC 4.0, credited"),
    "ground-tint.png": ("vertex colour tint", "the old project's studio (ours)"),
    "terrain-patches-applied.json": ("terrain patch receipts", "the old project's chain (ours)"),
    "route-grade-applied.json": ("route-grade patch receipts", "the old project's chain (ours)"),
}
RECEIPTS = (("terrain-patches-applied.json", "terrain"), ("route-grade-applied.json", "route-grade"))


def rows():
    covers, maps = seed_rows()
    inputs = [{"name": n, "sha256": vault.FILES[n][2], "role": r, "source": s} for n, (r, s) in INPUTS.items()]
    patches, outcomes = [], []
    for name, chain in RECEIPTS:
        rec = json.loads((vault.data_dir() / name).read_text())
        for p in rec["patches"]:
            patches.append({"id": p["id"]})
            outcomes.append({"terrain_patch_id": p["id"], "chain": chain, "kind": p.get("kind"),
                             "status": p["status"], "reason": p.get("reason"),
                             "samples_changed": p.get("samplesChanged"), "max_abs_delta_m": p.get("maxAbsDeltaM"),
                             "receipt": name})
    return {"terrain_input": inputs, "land_cover": covers, "land_cover_ltex": maps,
            "terrain_patch": patches, "terrain_patch_outcome": outcomes}


def main() -> int:
    w = db.open()
    if sys.argv[1:] == ["grass"]:
        from tools.argonia_world.terrain import grass
        painted = {r[0]: r[1] for r in w.query("SELECT ltex_form_key, ltex_edid FROM land_cover_ltex")}
        src, plans, lists = grass.seed_plan(grass.load_scan(), painted)
        for r in w.rows("ltex_grass"):
            w.delete("ltex_grass", r.ltex_form_key, r.ord)
        for t, rs in (("grass_source", src), ("ltex_grass_plan", plans), ("ltex_grass", lists)):
            for r in rs:
                w.upsert(t, r)
        print(w.save())
        return 0
    data = rows()
    for t in ("terrain_input", "land_cover", "land_cover_ltex", "terrain_patch", "terrain_patch_outcome"):
        for r in data[t]:
            w.upsert(t, r)
    print(w.save())
    return 0


if __name__ == "__main__":
    sys.exit(main())
