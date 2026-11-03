# Lane 1.15-r4-red-trees: crimson, pink and rose foliage; the teal cypress

Owner play test 3, finding 5; batch two's readers (red foliage in 12 of 19 world stills). L1 only; L4 owed (checks.md row after "Trees stand on their trunk bases").

## Names, from the placement shards (refs within 60 m of each vantage)
- Coastal lagoon high (-238080, -65536): ArgoniaFernCluster01B 34, ArgoniaTreeSwampPlant03B 28, ArgoniaFern01 27, ArgoniaFernCluster01C 13 (all King of the Murkmire).
- Blackwood flat 46 / slope 57 / 20: ArgoniaFern01 33/16/19, FernCluster01B 26/21/18, SwampPlant03B 22/16/12.
- Upland (creature-spots day/night): FernCluster01B 14/16, SwampPlant03B -/10, Fern01 2/8.
- Lagoon shore (108800, -66048): SwampPlant03A 3, FernCluster01A 1.

## Reader on the batch-two stills (evidence)
Red in 6 of 7 (all but marsh-day). Heaviest: blackwood-flat-46 and upland-day, feathery frond foliage 25-30 % of frame, waist-to-head height (the meadowsweet clusters at KotM's scale); lagoon-high: crimson low leafy clumps (SwampPlant06a); lagoon-shore-dawn: maroon fronds. No neon teal foliage in any still: teal only in water or a fog cast.

## Cause per form (measured diffuse: mean RGB, hue, share of saturated red/magenta pixels)
- ArgoniaFern01, ArgoniaFernCluster01A/B/C (KotM 768248, 768240, 768242, 768243): mesh HoddminirGrassFlowers/ESpMeadowsweet04*St.nif, diffuse textures/landscape/grass/espmeadowsweet04.dds, (77,53,45), hue 14, 66 % red. No vertex-colour or texture fault: the asset's own red variant (Hoddminir's ornamental meadowsweet). Out of place: dropped.
- ArgoniaTreeSwampPlant03A/B (KotM 3A3FA5, 3A3FA6): greguire/SwampPlant06(a).nif, diffuse ewplake10_rose.dds, hue 68 but 48 % red pixels (rose-edged leaves). The mod's rose variant; dropped.
- 01fortFlower (Black Marsh.esm 0AA5F4): vvardenfell/stronghold/fort00.nif, a fort mesh in the shrub role (moulding.dds, 31 % red). Not flora at all; dropped.
- Lore: Black Marsh undergrowth is "ferns and flowered grasses ... under canopies of blue moss" (world/sources/lore/topics/loading-facts.md:301; fauna-hazards.md:95-101); red belongs to Hist flowers (topics/hist-and-sap.md:23), not a fern's or a shrub's leaf. The same family's green meadowsweet 05 (hue 58, 3 % red; ArgoniaFernCluster02A-C) stands instead and stays in the lists.
- Allowed with a why (leaf_hue.ALLOWED): the water-lily flowers (lily1, lily2, lily1_violet; Path of the Lily, :465) and the cupling fungus cap.

## The teal cypress
Answer: keep. The bald cypresses (KotM cypress1/3/4/5.nif) draw vanilla `_resourcepack` baldcypressbranches01_d.dds. That texture is not on this machine (owner-owned; 44 vanilla diffuses unmeasured), so its hue is not measured at L1. No reader saw neon teal foliage in batch two's seven stills: teal shows only in water and fog casts. This supports the trees lane's lighting cause, not a texture fault. Owed: `vegetation hue build vanilla=<Data/_ResourcePack.bsa>` on the game machine during the planner's pass. If that measures it as teal, re-tint it through a texture set.

## What changed
- tools/argonia_world/vegetation/leaf_hue.py (new): `hue build <row>=<bsa|dir>` measures each manifest diffuse from the row that supplies it (numbers only), and writes data/leaf-hue.json (136 diffuses). `red()`: mean hue <20 or >290 deg at sat >= 0.2, or >= 25 % saturated red pixels. Bark, trunk and stump names are exempt.
- lists.usable drops a red-leaf form. `textures check` (make check, world step) fails on any placed flora form with one; tests in test_leaf_hue.py.
- Lists rebuilt (`vegetation forms --lists-only`). land_region_object went from 1577 to 1493 rows. Red-form rows went from 59 to 0. Before, per class: western-frontier 16, flooded-forest 12, deep-sink-basin 8, rootland 7, interior-swamp 6, tidal-delta 6, coastal-lagoon 2, northern-transition 2. After: 0 in every class. Placed forms went from 227 to 220. `textures check` now reports 0 problems (it reported 7 before).

## Owed
The placement (shards) still holds the old forms until the planner's next build. Then, in game, the tree-seat class stills and the world panel's coastal-lagoon stills, with a reader on "no crimson, pink or neon canopy". On the game machine: the vanilla hue pass above.
