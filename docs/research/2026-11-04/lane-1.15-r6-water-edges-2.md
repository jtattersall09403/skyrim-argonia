# Lane 1.15-r6-water-edges-2: the lower water at a step's foot

Status: the second census and its gate item are shipped, along with Skyrim.esm's numbers. The root fix is not shipped: three trials were measured and none moved the step class, so all three were reverted. The diagnosis below corrects lane water-edges' account.

## The second census (water/edges_census.py; `edges-census` in `make check`, about 3 s, cached by a stamp of what it reads)
- foot: for each kept step, the number of vertices from the line, down the channel's middle, to the first 3 vertices in a row under the lower level. A one-vertex pit does not count. Bar 12.
- wet: each held cell's share of vertices under its level, against its raster footprint. Bar 80 %.
- Gate: red on any hanging line. The two new measures are red only above their ceilings on today's ground (FOOT_FAR_MAX 183, BURIED_MAX 1654), so the fix lane ratchets them down.
- out/terrain ground (2026-11-05 05:04): 4876 lines, 0 red, 2370.7 m hanging only in channels. 183 of 203 kept steps have no lower water within 12 vertices (foot p10/50/90 13/33/33). 1654 of 2449 held cells are buried.

## Skyrim.esm (terrain/probes/vanilla_hanging_edges.py, extended)
- 77 level steps. Drop p10/50/90/max: 2.5, 10.7, 41.4 and 394 m.
- Foot (first under-level vertex): 0/8/33. Foot by the 3-in-a-row rule: 0/9/33, with 41 of 77 within 12. The lower cell's wet share is 0/19/35 %.
- 13 of 77 lower cells step again.
- The face at the channel stands 6.2, 5.4, 4.0, 3.5, 3.4, 1.6 and 0.3 m over the lower water by vertex (2.0 m per vertex).
- The p90 foot is 33, so "vanilla's p90" gives no bar. The gate uses 12 instead.

## The mechanism (measured on a scratch generate dump with water_field run on it)
1. The centreline ground under each reach falls steadily: the ground over the thalweg is p90 0.4 m, and only 1 of 582 reaches exceeds 10 m. The real cause is the fall within one cell. The solve allows a cell's thalweg to fall up to MAX_DROP_M (21 m) inside it, and takes the lowest point as the cell's level. So the reach's raster footprint stands 15-29 m (-50,46, p10/90) and 8-26 m (-59,-13) over the flat level.
2. The carve cuts that footprint with a cone at 0.6 m per sample. The cone digs the cell lines (the bank sources) under the level. The bank lift, a gentler cone, then fills the trench back in and spreads further. At (-50,46), lift from bank sources p50 is 41 m, while the largest shortfall on the pre-carve ground is 15 m.
3. Province-wide, held cells counted as buried after each stage: the carve leaves 430, the lift brings it to 1111 and the shore floor to 1650. Most are blackwater body cells (lift +681: 301 blackwater bodies and 184 reach cells; floor +539: 444 blackwater bodies). The hillside step class is the smaller share.

## Trials (none shipped)
- Solve bank cap: a reach cell whose line pre-ground falls more than 4.8 m short is lowered to what its banks hold, and the reach stays monotone. This lowered 94 cells and dried 2 more reaches. Buried cells went from 1654 to 1651, and the three named cells stayed 0.0 % wet. Reverted.
- Carve cap at banks: the cut stops at a source's need and rises from it at 2.0 m per sample (vanilla's face). After the carve, the footprint over the level at p50 dropped from 17 to 5.9 m (-50,46) and to -1.2 m (-59,-13). The lift on the pre-existing shortfalls then raised them to 12.9 and 7.0 m. Province buried cells 1585, kept-step lower cells buried 164 of 185. Reverted.
- Plus a steep lift inside the carve: it created iso hollows (sources 53 to 275), and the lift p50 rose to 14.5 m. Reverted.

## Owed, at source
1. The solve: a cell's fall inside itself needs a bar measured from Skyrim.esm (the ground fall along a vanilla river inside a level cell), not the 21 m piece height. A reach whose cell falls past that bar needs a step inside the run (the cell split in two at its own edge) or a dry gully.
2. The field, after (1): the carve cap at banks at FACE_GRADE (the second trial), once the footprint no longer stands 20 m over its level.
3. The blackwater burial by the shore floor and the carve, which is a separate lane.
