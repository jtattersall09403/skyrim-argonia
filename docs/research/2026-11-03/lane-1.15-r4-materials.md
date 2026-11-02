# Lane 1.15-r4-materials: the shiny ground and the flat mossy pebble fields (owner play test 3, findings 16-17)

## Causes (measured 2026-11-02)

1. **The pebble fields are `LRiverbedEdge01` (BM&V `textures\TEXTUREPACK\landscape\riverbededge.dds`).** In the round-3
   build it held 16.9 % of the province's LAND and 28.3 % of dry ground over 34 sampled 1 km windows. 46 % of its area lay
   more than 16 vertices (~29 m) from any water. Cause: `material.EDGE` keys height alone (-384 u to +128 u above local
   water, `material.py` `EDGE = Stop(...)`). That is a one-vertex strip on Skyrim's rising banks, but on our flat
   swamps it covers every flat a metre above water. The owner's stills agree (reader, 7 stills): still 7 is "pebble
   field about 90 % of visible ground, flat, over 100 m across, floodplain near Highwater / Cartwright's Crossing", and
   still 6 shows the same texture beside a river road. The texture has relief, but it tiles into a grid at distance.
2. **The shine comes from the normal map's alpha.** Skyrim's landscape shader reads specular from that alpha. Our
   TXSTs named no normal (TX01 empty, `texture_sets.py`), because BM&V ships none. Skyrim.esm's 50 landscape normals
   carry a mean alpha of 22.0/255 (p90 28.9). Tropical Skyrim's loose copies at the same vanilla paths are DXT1, which
   reads as alpha 255 on 18 of our 19. Naming a TS normal would therefore have been shiny too. Reader on the owner's
   stills: the sheen is on the pale, nearly textureless steep hillside (still 5) and on the road strip (still 6).
   Forest floor and pebbles read matte. The reader notes fog may account for part of the sheen.
3. BM&V's 19 diffuses are 512² DXT3 with **no mipmaps**, so they shimmer and tile at distance. This is not fixed here:
   making mips is a derived file (0014), so it is made on the player's machine by an installer step: installer backlog (P2).

## What changed

- `e396d20`:
  - `Tex.normal`: each TXST names Skyrim.esm's own `landscape\<name>_n.dds` (the player's BSA).
  - `data/dependencies.json`: tropical-skyrim-sse drops its 19 copies of those normals, so the vanilla ones resolve.
  - `material._keys`: dry ground beyond `EDGE_REACH` (2-4 vertices) of water reads at least `LIFT_DH` (beach top
    +0.3 m), so it takes the class's land stops.
  - Six classes gain patch stops on their own noise (litter, moss, beach grass, marsh grass, upland forest). Every
    added stop cites the shoreline research.
  - New `terrain check-materials` (`texcheck.py`, `dds.py`) and new tests: `test_dds.py`, a flat-land-is-not-edge test,
    and a no-single-land-texture class test.
  - `material_gradient` rewritten (81 rows).
- `69b3186`: journey `tests/journeys/ground-materials.yaml` and a ledger row in `docs/phases/1-core-loop/checks.md` (owed).

## Measured

- **L1 `python -m tools.argonia_world.terrain check-materials`: 19 textures, 0 fails.**
  - Every normal resolves from the vanilla BSA, with alpha 16.9-40.7 and tilt 12-60°.
  - The bar is vanilla p90 28.9, or Skyrim's own figure for that same LTEX where higher (riverbottom 33.6, riverbededge 40.7).
  - Before the change, 19 of 19 had no normal. With TS's normals, 18 of 19 would carry alpha 255.
- **Share of dry ground, 34 one-km windows (seed 1), before → after** (after = with the flooded-forest leaf-litter gate
  lowered 0.54 → 0.48, commit below):

  | LTEX | before | after |
  |---|---|---|
  | RiverbedEdge01 | 28.3 % | 2.6 % (100 % of it within 4 vertices of water) |
  | FrozenMarshGrass01 | 12.7 % | 6.3 % |
  | FieldGrass02 | 10.0 % | 7.5 % |
  | FallForestLeaves01 | 5.2 % | 23.8 % |
  | FallForestDirt01 | 5.6 % | 12.9 % |
  | ReachMoss01 | 7.9 % | 12.4 % |
  | PineForest03 | 6.5 % | 11.9 % |
  | PineForest02 | 7.9 % | 11.4 % |

- **Largest single texture in any window:** before 0.75 (edge) and 0.70 (marsh grass). After: **0.38** (PineForest03
  and FallForestLeaves01), then 0.36. Every window is under the 40 % bar.
- **L3 of that window** (cells -19 5 to -2 22, `out/terrain-sample/render-r4-ff/`), judged by a reader: **PASS**. Dark
  green is the largest colour at about 35-40 % of the land, split into many areas. The land is in patches, and the
  shore band is thin (5-15 px).
- The whole-province share from the built LAND is not re-measured: a province rebuild waits for the province lock and
  the planner. The round-3 build in out/terrain stays as the "before". It gives 16.9 % edge province-wide, including water.
- **L3 render** of the sample windows (`out/terrain-sample/render-r4-materials/`), judged by a reader:
  - The water-edge band is thin (a few px) in all four windows, and the land breaks into patches.
  - Over 40 % by eye: the lake-dominated -21_-26_-14_-19 (its little land is shore) and -12_63_-11_64 (bright green
    40-45 %).
  - The reader saw a wide straight brown strip in -12_63, probably the road paint, and a straight edge in -38_25.
    Both go to the roads and water lanes (planner).
  - Verdict: FAIL narrowly.

## Owed in game (planner's batch)

- Journey `ground-materials`: -9 27 (a pebble-field window) and -50 8 (a hillside), at midday. Ledger row owed.
- The next deploy must re-lay three things:
  - tropical-skyrim-sse (the drop list)
  - Argonia.esm (TXST TX01)
  - ArgoniaWorld.esm (land rebuild: `plugin-check` reports "land is stale" until then)

## Gate

- `make check-reach`: green (59 passed).
- The full `make check` reds are not this lane's: ruff in tools/bridge.py (`re`), the CLAUDE.md word budget, and a
  stale INDEX.
