# Lane 1.15-r3-mods: the MODS-dropped overrides and the L1 check that sees alternate textures

Follows [the shader lane](lane-1.15-r3-shader.md) §4 under the planner's ruling: the Skyrim-native fix, no new
dependency. Files only; no game machine.

## 1. The check now follows MODS

- ArgoniaGen `alttex` (tools/ArgoniaGen/AltTextures.cs) reads each candidate form's alternate texture sets from the
  plugin that owns it, and their TXSTs' TX00/TX01. Candidates are the non-vanilla object_forms, the build cells' bases
  (Claywater's block) and the creature forms. A creature form is followed through its skin (WNAM, else the race's)
  to the ARMAs' world models.
- `textures build` stores the sets in `data/mesh-textures.json` ("forms", paths only). `textures check` reads each set
  like a mesh slot: a missing diffuse is always red, and a missing normal is red unless WAIVED.
- 86 candidate forms carry MODS. Before the fix, the check listed exactly the shader lane's 14 bases, plus 4 King of
  the Murkmire giant snakes whose skin TXSTs name Mihail's `body2/3/4.dds`. Only `body.dds` is laid. 27 problems.
- After the fix: `246 placed forms, ... 86 forms with MODS (17 overridden without it), 0 problems`.

## 2. The fix

- `mesh_textures.ALT_DROPPED` lists 17 forms: the 13 Black Marsh.esm bases and the 4 snakes. `terrain/world.py`
  passes the list as `dropAltTextures`. LandWorld.cs writes an override of each in ArgoniaWorld.esm with the
  model's MODS dropped (`GetOrAddAsOverride`, nothing else changed), so the NIF's own textures draw. For a snake,
  the override is of its skin ARMAs, with both world models' MODS dropped. The NIF slots of all 13 bases resolve.
- The moss 17BD15 is not overridden. Its blue is the NIF's BSLightingShaderProperty (Own_Emit, emissive (0, 0.73, 1)
  × 1.5), not a field of the STAT or of the TXST, so an override cannot clear it. It is in `ALT_UNFIXABLE`, and
  `lists.usable` drops it (`untextured_forms`). `forms --lists-only` rebuilt the lists, and no
  land_region_object row names it now. The pools' rotation also moved other picks: esalixshrub03 and the two
  stinging nettles left BM&V's keep list. The check is red if the moss is ever placed.
- Read-back: after the vegetation splice, the world build runs `textures overrides`. It reads ALT_DROPPED back from
  the built plugin (ours first, else the owner's), and any remaining MODS set is red.

## 3. Tests and measures

- `tools/ArgoniaGen/test_alttex.py` runs `alttex-selftest`. It builds a synthetic master with a MODS-carrying STAT,
  TREE and FLOR, writes the overrides, and reads both plugins back. Result: `3 overrides written, 0 wrong`.
- `vegetation/tests/test_mesh_textures.py` covers these cases: a MODS gap is red until the form is overridden, an
  unwaived TXST normal is red, an unfixable form is dropped and is red when placed, and the read-back finds problems.
- The sample world build (pipeline.world with sample=True under job_guard, as plugin-check runs it) prints
  `textures overrides: 17 bases to override without MODS in ArgoniaWorld.esm, 0 problems` and
  `vegetation readback: 10 cells, 696 refs`. The same read-back on main's 04:49 out/ArgoniaWorld.esm gives
  17 problems, so the check can fail.
- `make plugin-check` as a whole stops before the world step on origin/main's own red:
  `ARG_WChance_coastal_clear_dry: no FormID yet` (weather commit 411a2c4 did not commit its formid table). That red
  is not from this lane.

## 4. Owed

- L4: re-shoot round 2's stills 04, 16 and 20 on the next deploy of main. Expect green trunks, plants and ruin walls,
  and no blue moss.
- The snake ARMA override is proved by the read-back in the province build, not by the selftest, which covers
  STAT/TREE/FLOR only.
