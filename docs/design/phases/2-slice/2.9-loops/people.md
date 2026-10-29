<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.9-loops/people.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 2.9 people loop survey (lane 2.9d)

Written before the first measure. Each row: harness command, number, bar,
capture, reader checklist, elapsed.

| # | Measure | Harness | Bar | Capture | Reader checklist | Elapsed | State |
|---|---|---|---|---|---|---|---|
| 1 | Tree-minder stock | `npx vitest run packages/economy/src/spellStock.test.ts` | both sellers stock spells, blessing, cure; every stocked spell castable by §123 from the seller's sheet or in signatureSpells; a planted rareFortify row reds | none | none | 1 s | green: 7/7; Vees-Wai 244 spells, Swims-The-Channel-Twice 311, both with cure-common-disease; a planted rareFortify row reds through `stockProblems` |
| 2 | Purchase writes known spells | `npx vitest run packages/economy/src/services.test.ts packages/magic/src/purchase.test.ts` | bought id in known spells with source `bought`; purchase row applied true; blessing and cure effects applied through 2.9a2 | none | none | 2 s | green: 15/15 (blessing `sanctus-shrine`; the cure clears swamp fever) |
| 3 | Scrolls | `npx vitest run packages/economy/src/stock.test.ts packages/economy/src/restock.test.ts packages/magic/src/scroll.test.ts` | scrolls in general traders' restock and loot; one cast, no skill bound, consumed, known spells unchanged | none | none | 3 s | green: 18/18 |
| 4 | Teach topic | `npx vitest run packages/dialogue/src/services` | one non-seller teaches one spell at a 0141 price; known spells written once | none | text-review pass | 2 s | green: 14/14; Im-Moro teaches `hearth-heal` (`topic.hearth-heal`, the `offerTeach` action); text review applied, lint_prose clean |
| 5 | Caster seam | `npx vitest run packages/game-core/src/ai/casterSeam.test.ts` | Nisswo and priest choose casts; distance kept for aimed; interrupt on poise break | `lanes/2.9/d-shots/teeth-casters-strip.png` (from the drive traces beside it) | casts visible, range held, interrupt visible | 6 s | green: 5/5; Ohl-Nakka 5 fires, Zaxi-Rekh 21, one interrupt each, every fire beyond 4.5 m (nearest 6.55 m and 6.10 m); reader: all four checks met, it holds about 6.5 m rather than the 9 m standoff |
