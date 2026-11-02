# Lane 1.15-r4-trees: tree seating, tree colours, variety between region classes

Owner play test 3, findings 4, 5 and 32. L1 and L3 only; the in-game check is owed (row in docs/phases/1-core-loop/checks.md, journey tree-seat).

## 1. Seating (finding 4)
**Cause.** `vegetation/place.py:306` set every non-rock pivot on the ground: `sink_m` was 0 because `Rule.sink_of` returned 0 unless `sink_frac` was set, and `lists.sink_frac` set it only for rocks. The mods sink their trees by an amount each mesh needs, measured in the mods' own worldspaces (decision 0034, `vegetation/seat.py`: REFR z against that cell's LAND VHGT, divided by the ref's scale). Measured medians, in units:
- KotM erut trees: 340 (Erut02) and 390 (Erut06). The mesh's lowest point is its root tips at the pivot, so with no sink the trunk stood about 5 m up on its roots.
- Palmoke palms: 415.
- Thick palm: 71.5. Fan palm: 34.5.
- Swamp cypresses: about 0. These were fine.
- Hanging-moss "gallery" forms: OBND z0 of +456 to +543 over the pivot. These hang from a tree and were being placed standing on their own.
The lists also held 61 non-flora rows: KotM stockades, walkways, bridges and a giant snail shell, all taken in by the role words.

**Change.**
- `seat.py` measures 1,417 forms and 1,098 meshes into `data/tree-seat.json`. Each tree is seated by its form's median, or its mesh's median, over at least 5 refs.
- `vegetation_form.seat_units` (new column in `world/schema.sql`) feeds `Rule.sink_m` in `build.load_rules`.
- `lists.usable` now drops trees with no measured seat and forms that hang more than 10 units above the ground at their seat.
- `lists.NOT_FLORA` drops the structures.
- In `place.place_cell`, a tree's base is held within 10 units over and 40 units under both triangulations of its quad; quads twisted more than 50 units are refused.
- `checks.run` reports `seat` failures and `tree_seat` (worst hover, worst sink).

## 2. Colours (finding 5)
- **L1 change.** `mesh_textures.incomplete` is new. `lists.usable` and the check (`waive=False` for the region lists) now place no flora mesh with any missing slot. That removes, among others: the waived missing normals on the Vurt mushrooms, flatpalm1, fanpalm1, gorse and the coral or kelp grass; and gkbjungletreenew1, which has a broken normal string and a missing glow slot. `textures check`: 227 placed forms, 0 problems.
- **Owner's evidence: 7 stills, judged by a reader.** The fault is a saturated neon teal on the foliage of "slender, bamboo-trunked cypress or conifer-like trees with feathery leaves" (stills 1, 3 and 4), and pink or maroon on a fern-leaved tree (still 5). It reads as a wrong diffuse or tint, not a missing normal; there is no glossy specular in any still. The buttress-root jungle trunks look pale grey-green and washed out. Still 3 may show a hovering base.
- **So the missing-normal cause is not confirmed for the teal trees.** The likely models are the bald cypresses: KotM ArgoniaTreeSwampCypress03, 05 and 07 (cypress1, 3 and 5.nif), whose bark and branches resolve to vanilla `textures/_resourcepack/.../baldcypress*` from the runtime's resource pack. The cause is unproven. Owed: one still of the same model in KotM's own worldspace against ours, the 0034 reference. If KotM's own copy is teal, it is the asset; if not, it is our resolution of `_resourcepack` or a MODS set.

## 3. Variety (finding 32)
**Cause.** `lists.pick` took every class's forms from one pool in one order (BM&V first, then most placed). The first CORE forms were in every region, and packets rotated over the whole pool, so the classes' lists overlapped 86 to 100 % (min share differing 0.00 to 0.14, except western-frontier at 0.50).

**Change.**
- `lists.FAMILY` groups tree kinds by name into families, each tied to the classes whose ground it is and cited to the audit rows or dossiers (written into each row's `why`).
- `lists.ranked` orders each class's pool by its own families first.
- `lists.draft` splits each role's pool between the classes, each drawing the least-shared form.
- Packets rotate only inside their class's draft.

Per-class kinds, before (union over the class's regions):

| class | kinds | aquatic | canopy | deadwood | emergent | gallery | mushroom | palm | rock | shrub | min share differing |
|---|---|---|---|---|---|---|---|---|---|---|---|
| coastal-lagoon | 120 | 17 | 58 | 15 | 0 | 0 | 0 | 13 | 0 | 17 | 0.07 |
| deep-river-corridor | 76 | 9 | 21 | 7 | 0 | 7 | 5 | 0 | 10 | 17 | 0.13 |
| deep-sink-basin | 167 | 13 | 60 | 16 | 26 | 11 | 13 | 0 | 0 | 28 | 0.10 |
| flooded-forest | 150 | 13 | 51 | 14 | 20 | 11 | 13 | 0 | 0 | 28 | 0.00 |
| interior-swamp | 136 | 13 | 42 | 15 | 14 | 11 | 13 | 0 | 0 | 28 | 0.00 |
| northern-transition | 52 | 0 | 12 | 5 | 3 | 2 | 0 | 8 | 10 | 12 | 0.12 |
| rootland | 149 | 13 | 57 | 14 | 24 | 0 | 13 | 0 | 0 | 28 | 0.00 |
| tidal-delta | 129 | 17 | 49 | 15 | 0 | 0 | 0 | 25 | 0 | 23 | 0.14 |
| western-frontier | 101 | 0 | 28 | 11 | 3 | 2 | 0 | 8 | 21 | 28 | 0.50 |

After:

| class | kinds | aquatic | canopy | deadwood | emergent | gallery | mushroom | palm | rock | shrub | min share differing |
|---|---|---|---|---|---|---|---|---|---|---|---|
| coastal-lagoon | 35 | 3 | 10 | 7 | 0 | 0 | 0 | 8 | 0 | 7 | 0.89 |
| deep-river-corridor | 38 | 3 | 10 | 6 | 0 | 3 | 2 | 0 | 7 | 7 | 0.84 |
| deep-sink-basin | 39 | 3 | 10 | 7 | 6 | 3 | 3 | 0 | 0 | 7 | 0.77 |
| flooded-forest | 39 | 3 | 10 | 7 | 6 | 3 | 3 | 0 | 0 | 7 | 0.82 |
| interior-swamp | 39 | 3 | 10 | 7 | 6 | 3 | 3 | 0 | 0 | 7 | 0.77 |
| northern-transition | 42 | 0 | 10 | 5 | 3 | 0 | 0 | 8 | 9 | 7 | 0.79 |
| rootland | 36 | 3 | 10 | 7 | 6 | 0 | 3 | 0 | 0 | 7 | 0.83 |
| tidal-delta | 35 | 3 | 10 | 7 | 0 | 0 | 0 | 8 | 0 | 7 | 0.89 |
| western-frontier | 48 | 0 | 10 | 7 | 3 | 0 | 0 | 8 | 13 | 7 | 0.81 |

The trade-off: each class now has fewer kinds (3 aquatic kinds per class) in exchange for identity.

## L3
`terrain/render.py`'s registry named `vegetation.render`, which did not exist, so no render ever drew a placement. That module now exists and colours trees by family. The four-window render and the reader are listed under the run state below.
