# 0031: The generated ground is its own master, ArgoniaWorld.esm, built and hashed, never serialised to YAML

**Status:** decided 2026-10-29 by the planner (a method choice inside decision 0009; reversible: the records are
generated either way). Raised by the 2.W1 terrain lane.

## Context

Decision 0009 makes every record generated, and 0.4 §a serialises `Argonia.esm` to Spriggit YAML under `plugin/`
so each change is a reviewable diff. The whole worldspace is 15,876 province cells and 17,654 apron cells, each
with a CELL and a LAND record (about 67,000 records, most of them heights, normals, colours and texture weights).
As YAML that is hundreds of megabytes of numbers no reviewer reads; it would swamp git and the 3-minute gate.

## Decision

1. **`ArgoniaWorld.esm`** holds the generated ground: the `ARG_Province` WRLD, every exterior CELL and its LAND,
   and later the other bulk outputs of the world track that are pure functions of the world database and the frozen
   arrays (water heights on cells, the region generator's placements if they prove bulky, generated navmesh). It is
   a master of `Argonia.esm`.
2. **`Argonia.esm`** stays the authored, reviewable layer: places, people, quests, regions, weathers, the
   quarantine; serialised to `plugin/` and round-tripped as 0.4 §a built it. Place edits to the ground are layers
   in `Argonia.esm` over the generated cells (old 0140), never edits of `ArgoniaWorld.esm`.
3. `ArgoniaWorld.esm` is **built by `make plugin`** from the database and `$ARGONIA_DATA`, deterministically, with
   its FormIDs computed from a reserved range (cell grid position → id), so a rebuild never renumbers. It is not
   committed and not serialised. The gate checks it by **hash**: a fixed sample of cells rebuilt and hashed against
   a committed manifest; the full rebuild's hash is recorded at each world-track close.
4. It is our own data (the heightfield and patches are the project's; the apron is Transbot9's map, CC BY-NC 4.0,
   credited), so it ships like `Argonia.esm` (0003); it is not a derived file in 0014's sense (nothing in it comes
   from the player's install).

## Consequences

- Reviewers see the ground through the L1 checks and stills, not through YAML.
- The terrain, water and region writers in `tools/ArgoniaGen` target the right plugin by record kind.
- A generated record that must point at an authored one cannot (the master cannot reference its dependant): the
  master carries a **shell** of the authored record (EditorID and owner only, ids from a reserved append-only range in
  the `formid` table) and the authored plugin overrides the shell with its content. First case: each cell's region list
  (XCLR) points at REGN shells in `ArgoniaWorld.esm`; `Argonia.esm` overrides each with its weathers, objects, map name
  and areas (2.W3). The border region needs no XCLR and lives wholly in `Argonia.esm`.
