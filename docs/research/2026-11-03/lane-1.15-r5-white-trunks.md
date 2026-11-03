# Lane 1.15-r5-white-trunks: the cream-white glowing trunks and the stretched bark, named and dropped

L1 only (placement shards, NIFs of the laid stack, textures of the laid stack and the retail BSAs read in place; numbers only). The L4 check is owed (below). No game machine touched.

## 1. Census (placement shards rebuilt for the two vantages' cells; 150 m; frustum +-50 deg of the journey yaw)
Shore (-69632, -29056) yaw 141: 11,133 refs in 150 m, 2,799 in the frustum. High (-163560, 218624) yaw 135: 11,556 and 3,186. Every tree/shrub form in view, with shader flags and bark numbers, was read per shape (scratch parser: BSLightingShaderProperty flags, emissive, gloss, texture slots; BSTriShape vertex colour and UV-to-surface stretch).

- All bark diffuses in view are dark: weepingwillowbark01_d lum 62 sat 0.20, baldcypressbark01_d 52, cypressbark3/4 61/67, trunk2 38, gkbbark27 81 (placed median 59). Only the dropped kapok (138) was bright. So a bright diffuse is not the cause here. Own_Emit colours are black on every trunk shape; no trunk has Glow_Map, Rim or Back lighting.
- Bloom is not the cause: the deep-sink weathers (clear-dry, cloudy-ma, mist) take Tropical's IMGS (day bloom 0.2 / 0.95, sky 0.12, lane sky-2). In the same noon frame a trunk of the same bark texture (SwampBroken01, 15 m, vertex colour 137) draws dark (mean RGB 38,53,41) while the white trunk reads (209,230,182), brighter than the sunlit leaf litter (91,91,32).
- The white trunk in 12-deep-sink-basin-high-noon.png (bearing +1 to +14 deg, 102-112 m, four refs) is **ArgoniaTreeErut07 (155FEC, ErutTree03Tall.nif)**: its 3436-vertex bark shape is the only placed bark with an empty normal slot (snowgumbark01_n sits in slot 2), no Specular, gloss 1, and a vertex colour mean of (242, 245, 242) (kapok was 255). Its sibling Erut08 (04Tall) has (197, 204, 196) and a normal; it stands at 138-142 m and is kept.
- The pale tree at left of the same still (bearing -35, 102-105 m, three refs; also 27-40 m left in the shore stills) is **01skydead (04E139, BM&V 11skykahl1.nif)**: its trunk2 shape is Own_Emit + Soft_Lighting + Double_Sided with a slot-2 map, the signature of the rainforest trunks dropped by trees-2. Its wrap value is 0.3, so this is by shape signature, not by a number.
- The cause of the extra brightness is not provable from bytes: the diffuse is dark and the flags are plain. It is an L4 question; the drops are by named form with the measured anomalies above.

## 2. Stretched UV
Per bark shape, the median singular-value ratio of the UV-to-surface Jacobian (3:1 to 6:1 is the placed band; global median 1.7:1, 252 shapes):
| form | mesh | shape | stretch |
|---|---|---|---|
| ArgoniaTreeMega04 15B1E2 (11 rows) | MegaTree04 | 3240 verts, UV 0-1 over 2050 units | 104:1 (texel density 7x the siblings) |
| ArgoniaTreeMega05 15B1E3 (6) | MegaTree05 | 3720 verts | 91:1 |
| ArgoniaTreeSwamp04 15B1E7 (6) | SwampTreeTall04 | 8082 verts | 44:1 |
| ArgoniaTreeJungle08/04/09/10 (8/6/3/2) | JungleTree01/02/05/06 | trunk2 | 24/24/23/27:1 (JungleTree03/04 draw the same texture at 5:1) |
The streaked swirl at top right of 11-deep-sink-basin-shore-dawn.png (Mega04 stands 101-102 m off at bearing -54 to -57, the swirl sits at the frame's right edge: bearing not exact, the shape is the only one placed with this stretch at that scale) is the MegaTree04 shape. All seven are dropped.

## 3. Fix
No install-time NIF patcher exists (0014), so per 0010 the data route drops the forms: `lists.LOOK_DROP` gains 9 forms (155FEC, 04E139, 15B1E2, 15B1E3, 15B1E7, 0EB922, 0EB923, 155FE0, 155FE2), each with its measured reason. Lists rebuilt (`vegetation forms --lists-only`): land_region_object 1399 -> 1352 rows, placed forms 204 -> 195. data/dependencies.json loses 11skykahl1.nif from the keep list. Province vegetation check (`build` + `check` against out/terrain/land): **18 green, 0 red, 647,618 refs** (was 647,783). Lore: Black Marsh's trunks are dark river-stained bark under moss (0032: topics/loading-facts.md:301 for the marsh; no source calls for pale trunks).

## Owed
Row `tree-look` (checks.md): the same two panel stops (deep-sink-basin shore dawn/noon and high noon), after the next terrain/vegetation build and ESM. A reader asks: is any trunk cream-white or brighter than the sunlit litter; is any bark streaked or twisted. If a white trunk remains, name its form by the bearing/distance method above and look at the vertex colour and the normal slot first.
