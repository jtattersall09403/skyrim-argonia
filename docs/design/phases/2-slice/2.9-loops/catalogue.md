<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.9-loops/catalogue.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: the catalogue (2.9 § Loops, lane 2.9a1)

Rule (world/76 §123, §127; decisions 0144 item 7, 0146): every Morrowind
effect and spell is a row in `packages/magic/src/data/effects.json` and
`spells.json`, written by `packages/magic/scripts/build_catalogue.py` from
the UESP dossier `world/sources/lore/topics/magic-effects.md`. Cost is
Morrowind's formula (a hand-priced spell keeps Morrowind's price), tier is
the `magic.json` cost band, cast style follows the dearest effect's range.
A fortify on a crafting skill or its input attribute is `rareFortify`: never
under cost 60, `signature` only, never in a non-signature stock or under a
`common` tag. Eyes: none (data and numbers only).

Measures:

- `cd packages/magic && npx vitest run src/catalogue.test.ts`
- `python3 -I packages/magic/scripts/build_catalogue.py --check` (the json and the dossier are current)
- `cd tooling/world-generation && python3 -m worldgen.item_views --check` (gem and scroll rows)

| Measurement | Bar | Result | Elapsed | Capture |
|---|---|---|---|---|
| Every effect and spell row validates (ids, schools, ops, families, colours, ranges, cost, tier, cast style), every effectId resolves | 0 problems | 0 problems; 300 effects, 876 spells (857 spells, 19 powers) | 1.0 s (one run, all rows) | `catalogue.test.ts` |
| Every UESP effect mined | 141 UESP rows | 141 rows, each mapped (dossier § Effects) | 0.1 s | `build_catalogue.py --check` |
| Stack-op fields: an `EFFECT_FIELDS` name, a current pool, or a listed non-stat field | exact partition | pass | 1.0 s (one run) | `catalogue.test.ts` |
| Fire, frost and shock resist are separate fields | three fields | pass | 1.0 s (one run) | `catalogue.test.ts` |
| rareFortify = fortify or absorb on alchemy, enchant, smithing, intelligence, strength; matches `magic.json` `bannedEffects` | exact | pass | 1.0 s (one run) | `catalogue.test.ts` |
| No rareFortify spell under 60; every one `signature` | 0 under | pass (base cost ×4.3, the one tuning) | 1.0 s (one run) | `catalogue.test.ts` |
| Water walking and levitate flagged traversal | both | pass | 1.0 s (one run) | `catalogue.test.ts` |
| §123 worked examples: novice (10, 30) holds 26; master (100, 100) 220; reliability line 50 inside (170) | exact | pass | 1.0 s (one run) | `catalogue.test.ts` |
| The formula reproduces Morrowind's listed prices | every autocalc price | 696 of 854 listed prices with Morrowind's base costs; the rest are the 146 `handPriced` spells and 12 rareFortify spells Morrowind priced by hand, priced here by the tuned formula | 0.1 s | dossier § Spells |
| Slice set present with the README's school, range and cast style | 9 of 9 | pass | 1.0 s (one run) | `catalogue.test.ts` |
| Birthsign powers and spells: the nine `birthsigns.json` ids authored, powers as powers | 9 of 9 | pass; `birthsigns.json` ids confirmed unchanged | 1.0 s (one run) | `catalogue.test.ts` |
| The gate reds a dangling effectId | red | red, one exact line | 1.0 s (one run) | `catalogue.test.ts` |
| The gate reds a rareFortify spell in a non-signature seller stock (`stockProblems`, for 2.9d) | red | red; green when the same spell is on `signatureSpells` | 1.0 s (one run) | `catalogue.test.ts` |
| Soul-gem and slice-scroll item rows | 10 gems with `soulGem`, 9 scrolls with `spellId` resolving | pass | 0.06 s | `item_views --check`; `catalogue.test.ts` (shipped item view) |
