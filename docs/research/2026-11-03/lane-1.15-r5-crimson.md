# Lane 1.15-r5-crimson: the crimson and pink canopy was a vertex colour, not a diffuse

Owner finding, round 5 stills (sky A/B, shaders on and off): a saturated crimson tree top-left at the coastal-lagoon shore noon vantage; red/pink trees at the left and right edge at the western-frontier high noon vantage; olive-yellow reeds at the shore. L1 only; L4 owed.

## Reader on the two stills (a reader agent, not me)
- Lagoon: one near foreground branch, top-left, 12-15 % of frame, long narrow drooping lanceolate leaves, crimson/maroon with brighter red edge, a few green leaves mixed in; real 3D, not a billboard. Reeds: tall olive to sage, standing in open water, hazy.
- Frontier high: three pink-crimson/rose leafy groups (lower-left, centre-left, far-right edge), canopy trees, 1.5-4 % of frame each, 3D, colour on leaves not trunks.

## Frustum census (placement shards out/terrain/vegetation, 250 u ~ 3.5 m was empty, so 3000 u; yaw 94 and 180, +-50 deg)
Lagoon (35 refs): seaweed06 cluster 9, 01TROPICAL11 5, Erut07 4, SwampBroken01 4, Cypress06 3, Jungle03 2, seaweed01 2, 01BIRCH 2, Erut02 2, others 1. Frontier (102 refs): Undergrowth01 29, SwampPlant02A 17, Groundplant10 16, FernCluster02B 15, braken 9, Swamp03 3, Shrub03 3, 01BIGUSHTREE 3, Erut08 2, Mega05 2, rocks 2, branchpile 1.

## Cause (measured)
No placed diffuse is red: all 180 slot-0 diffuses measured, including the 44 unmeasured vanilla ones (hangingmoss01 hue 63, fern01 102, nightshade01 low-saturation mauve, goldkanet 52, hackleloleaf 62: none red). 0 placed forms have a texture with no source (`textures check` fails on any, waive off; 30 absent from every row, all non-diffuse maps or unplaced). Missing-texture pink is ruled out.

The cause is the NIF vertex colour, which the engine multiplies into the leaf diffuse. Read from each mesh's BSTriShape vertex-colour attribute (`hue build-nif`, new): the leaf shape of these meshes has every vertex crimson or pink:
- King of the Murkmire Erut trees eruttree01-04, 01tall, 03tall, 04tall: mean RGB (209,48,113) .. (255,74,168), red share 1.0. Forms ArgoniaTreeErut01-08 (155FE5, 155FE7-155FEA, 155FEC, 155FED); their diffuse leaves27.dds is green (hue 72). In the frustums: Erut07 and Erut02 at the lagoon (the top-left branch), Erut08 at the frontier.
- SwampPlant08/08a: (225,59,91), (226,85,85). Forms ArgoniaTreeSwampPlant02A/B (3A3FA3, 3A3FA4); 17 refs at the frontier.
Other vertex-coloured trees carry green or grey means (swamptreetall, megatree: fine). Also red but not placed or not flora: histflower01/02 (the Hist's red, lore hist-and-sap.md:23, kept allowed) and rockl01 (a rock, exempt).

## Fix
- leaf_hue.py: `nif_shapes` / `build_nif` / `red_shape` / `red_vertex`; data/leaf-hue.json holds per-shape vertex colour means for 336 meshes (13 with a red shape). `lists.usable` drops a non-rock form with a red shape; `textures check` (make check) fails on any placed one. histflower and water lilies allowed with a why (lore 0032: ferns and flowered grasses under blue moss; red only for Hist flowers).
- Lists rebuilt (`forms --lists-only`): land_region_object rows 1493 -> 1399 (the 9 forms had 53 rows, replaced by other forms where the region's list drew); placed forms 220 -> 211; red-vertex rows 53 -> 0; `textures check` 9 problems before the lists, 0 after. 45 vegetation tests pass (new test_vertex_colour).

## Reeds
The lagoon "reeds" are aquatic: Depths of Skyrim TBPSeaweed06Cluster (seaweed02.dds, rgb 40,43,14, hue 66) and TBP_seaweed01 (seaweed01, hue 81), standing in open water, plus cypress branches (hue 61). Olive-yellow is their measured diffuse (saturation 0.46-0.68) under the sky's yellow cast; not a fault, not changed. The sky lane owns the cast.

## Owed
The placement shards and the ESM still hold the old forms until the planner's next terrain/vegetation build. Then in the round-5 batch: sky-ab coastal-lagoon-shore-noon and western-frontier-high-noon, a reader on "no crimson, pink or rose canopy or shrub"; the reeds read against the sky cast. Remaining, unrun here: the machine-local `hue build-nif` needs Pillow-free numpy-free code only (it is), `hue build` needs Pillow, numpy and lz4.
