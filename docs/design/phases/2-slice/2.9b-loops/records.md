<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.9b-loops/records.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: crafting records (2.9b § Loops, lane 2.9b-a)

Rule (world/76 §124; decisions 0144 items 4 and 7, 0146, 0070): stations,
smithing recipes and material tiers are rows in `packages/crafting/src/data/`;
ingredient and potion effects ride the item home table
(`world/sources/registries/items.json`); resource-node kinds live in
`world/sources/registries/resource-nodes.json` (derived view
`packages/crafting/src/data/resource-nodes.json`, written by
`worldgen.item_views`). Every reference resolves by id; a rareFortify
ingredient has one placed or looted source, never a shelf. Eyes: none (data
and numbers only).

Measures:

- `cd packages/crafting && npx vitest run`
- `cd tooling/world-generation && python3 -m worldgen.item_views --check`

| Measurement | Bar | Result | Elapsed | Capture |
|---|---|---|---|---|
| Every ingredient row carries four effect ids that resolve in packages/magic effects.json | 39 of 39 | 39 of 39; effects resolve | 0.4 s (one run) | `item_views --check`; `catalogue.test.ts` |
| rareFortify on exactly the rows with a rareFortify effect; at most 3; each sourced from one placed node or looted container | ≤ 3, 0 shelf | 1 (item.spriggan-sap: fortify enchant + smithing; source socket.KeebaHouseElder.0801AABE) | 0.4 s | `catalogue.test.ts` |
| No rareFortify item reaches a trade shelf | 0 | 0 (trade_tables drops rareFortify; spriggan-sap left the shelf) | 0.4 s | `trade_tables` view |
| Every potion row carries effects with §124 magnitude and duration (journeyman, Alchemy 30, Int 40) | 9 of 9, exact | 9 of 9 (restore health 2.3 for 6.8 s) | 0.4 s | `catalogue.test.ts` |
| Stations: five kinds, alchemy by three qualities, stationClass in a published kit or named for sourcing | 7 rows | 7 rows; stationClass a vocabulary key, piece in works-v1 or xanmeer-kotm-v1 | 0.4 s | `catalogue.test.ts` |
| One recipe per weapon and armour row with a material; inputs resolve to items | every gear row with a material | 154 recipes; 18 rows with no material (akaviri 1, obsidian 1, falmer 5, daedric 11) | 0.05 s | `catalogue.test.ts` |
| Material tiers from `sets` | one row per tier | 8 tiers (5 and 8 empty) | 0.05 s | `catalogue.test.ts` |
| Tier gate `1 + floor(effSkill/14)` at 0, 14, 27, 28, 84 | 1, 2, 2, 3, 7 | 1, 2, 2, 3, 7 | 0.4 s | `catalogue.test.ts` |
| Resource-node kinds: yields are ingredients, stationClass a kit piece | every node | 6 node kinds, all green | 0.4 s | `catalogue.test.ts` |
| The gate reds a shelf-sourced rareFortify ingredient, a recipe with a missing material, a node yielding a non-ingredient | 3 reds | 3 reds, one exact line each (plus piece and stationClass reds) | 0.4 s | `catalogue.test.ts` |
| Generator check green, views current | green | green (424 items, 154 recipes) | 0.05 s | `item_views --check` |
