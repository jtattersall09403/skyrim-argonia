# 0009: The world content is imported from elder-souls-argonia, owned here, and generated into Skyrim plugins

**Status:** decided 2026-10-27.

## Context

elder-souls-argonia holds the authored world as engine-neutral JSON with schemas (decision 0104 there: one
normalised record set modelled on Bethesda FormID records): 827 places, 959 NPC/creature rows, 733 quest rows
(38 with stages), ~2,000 dialogue lines, 32 factions, 508 items, 42 creature species, hydrology (101 rivers,
615 reaches, 2,280 bodies), routes and travel services, the frozen 4033² heightfield at 1.828 m (= Skyrim's
128-unit vertex spacing: 126×126 Skyrim cells), climate, flora rules, lore dossiers, the stats design, a text
style guide and a Morrowind exemplar corpus. The owner may keep developing the three.js version separately.

## Decision

1. **Import, then own.** Chunk 0.1 copies the engine-neutral sources (list in [source-map.md](../source-map.md))
   into `world/` here, with the source commit recorded. From then on this repo's copy is the source of truth
   for skyrim-argonia; later changes in the old repo are pulled only deliberately (a dated re-import note).
2. **Pipeline:** `world/` JSON → generators (Python for planning and checks, C# Mutagen for records) →
   **Spriggit** YAML (one file per record, committed, reviewable) → `Argonia.esm` (+ BSAs of our own files)
   as build outputs. Hand edits in the Creation Kit are not the workflow; the CK is installed and used as a
   scripted tool (Papyrus compiler, load checks, navmesh, FaceGen, flowmaps; decision 0018), and anything it
   produces is captured back into Spriggit.
3. **Record identity:** every world id maps to a stable EditorID (`ARG_` prefix plus the id) and a FormID
   allocated by a committed allocator table, so regenerating never renumbers.
4. **Skyrim-specific facts** (units ×70.03 per metre, ZYX Euler, cell 4096 units = 58.5 m, LAND 33×33 per
   cell, ≤6 texture layers per quadrant, one water plane per cell, placed water for rivers) live in one module
   `tools/argonia_world/skyrim_units.py` (and its C# twin) and nowhere else.
5. **The heightfield and other big binaries** (frozen `.npy` arrays, nav bakes) are not committed (size, and
   the heightfield's origin is a Skyrim mod worldspace, "Tamriel Worldspaces – Argonia", Nexus 118678): they
   are fetched into `$ARGONIA_DATA` from the old project's R2 vault snapshot by a script, verified by the
   committed hashes in `world/sources/terrain/freeze.json`.

## Consequences

- Places are rebuilt natively from their design notes, with the old layouts as a guide (decision 0026). Every piece
  the old places used is already Skyrim's or a Skyrim mod's, so each resolves to a base record.
- Morrowind-style dialogue and quest conditions beyond Skyrim's condition functions are evaluated by
  ArgoniaCore (S2), fed by the same JSON.
