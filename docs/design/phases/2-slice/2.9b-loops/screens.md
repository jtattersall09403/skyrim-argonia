<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.9b-loops/screens.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: crafting screens (2.9b § Loops, lane 2.9b-f)

Rule (2.9b-crafting.md; decision 0150 item 3): the three crafting windows
stand on 2.2's system on every device and input, opened from a station's
prompt by its verbs: Alchemy (Morrowind's picking with a by-effect
filter), Smithing (forge, temper, mend) and Enchanting (enchant,
disenchant, recharge).

Code: `packages/ui/src/screens/Alchemy.tsx`, `Smithing.tsx`,
`Enchanting.tsx` (views in each file); the live views and the station
mount in `packages/scene/src/interact/craftingScreens.tsx`
(`useWalkInteract` opens the screen by the activation's verbs). Fixtures:
`apps/ui-lab/src/screens/crafting.tsx` on the real records
(`@elder-souls/crafting` catalogue, items.json, effects.json).

Harness: `bash tooling/repo-standards/job_guard.sh 2.9b-f --mem 4 -- node
tooling/ui/ui_lab_check.mjs --screens <ids>`. The lab shoots desktop (mouse
and keyboard), phone 844×390 and fold-inner 905×835 (touch and the pad
focus walk), all landscape. The lab has one colour scheme, so light and
dark is one pass. A `reader` child judges every shot (lanes/2.9b/f-reader.md).

| Screen id | Viewports | Result | Elapsed | Capture |
|---|---|---|---|---|
| crafting-alchemy | desktop, phone, fold | pass 1: PASS every automatic bar (72 shots); reader 8 P2, 4 P3 (lanes/2.9b/f-reader.md); fix batch in 09bfd7a94; re-shoot blocked: the ui-lab build fails on `settleDeal` (screens/index.ts vs a live Barter.tsx edit, not this lane) | 101 s (pass 1, all six) | tooling/.reports/ui-lab/shots/crafting-alchemy__*; lanes/2.9b/f-shots/ |
| crafting-alchemy-novice | desktop, phone, fold | pass 1: PASS every automatic bar (72 shots); reader 8 P2, 4 P3 (lanes/2.9b/f-reader.md); fix batch in 09bfd7a94; re-shoot blocked: the ui-lab build fails on `settleDeal` (screens/index.ts vs a live Barter.tsx edit, not this lane) | 101 s (pass 1, all six) | tooling/.reports/ui-lab/shots/crafting-alchemy-novice__*; lanes/2.9b/f-shots/ |
| crafting-smithing | desktop, phone, fold | pass 1: PASS every automatic bar (72 shots); reader 8 P2, 4 P3 (lanes/2.9b/f-reader.md); fix batch in 09bfd7a94; re-shoot blocked: the ui-lab build fails on `settleDeal` (screens/index.ts vs a live Barter.tsx edit, not this lane) | 101 s (pass 1, all six) | tooling/.reports/ui-lab/shots/crafting-smithing__*; lanes/2.9b/f-shots/ |
| crafting-smithing-temper | desktop, phone, fold | pass 1: PASS every automatic bar (72 shots); reader 8 P2, 4 P3 (lanes/2.9b/f-reader.md); fix batch in 09bfd7a94; re-shoot blocked: the ui-lab build fails on `settleDeal` (screens/index.ts vs a live Barter.tsx edit, not this lane) | 101 s (pass 1, all six) | tooling/.reports/ui-lab/shots/crafting-smithing-temper__*; lanes/2.9b/f-shots/ |
| crafting-enchanting | desktop, phone, fold | pass 1: PASS every automatic bar (72 shots); reader 8 P2, 4 P3 (lanes/2.9b/f-reader.md); fix batch in 09bfd7a94; re-shoot blocked: the ui-lab build fails on `settleDeal` (screens/index.ts vs a live Barter.tsx edit, not this lane) | 101 s (pass 1, all six) | tooling/.reports/ui-lab/shots/crafting-enchanting__*; lanes/2.9b/f-shots/ |
| crafting-enchanting-recharge | desktop, phone, fold | pass 1: PASS every automatic bar (72 shots); reader 8 P2, 4 P3 (lanes/2.9b/f-reader.md); fix batch in 09bfd7a94; re-shoot blocked: the ui-lab build fails on `settleDeal` (screens/index.ts vs a live Barter.tsx edit, not this lane) | 101 s (pass 1, all six) | tooling/.reports/ui-lab/shots/crafting-enchanting-recharge__*; lanes/2.9b/f-shots/ |
| dialogue-long-talk (lane w4: speech left page, topics, persuade and services right, nothing across the hinge) | desktop, phone, fold | bar 5 green after one fix (title off the hinge); reader lanes/2.9b/w4-reader.md | 52 s, 81 s, 69 s (3 runs) | tooling/.reports/ui-lab/shots/dialogue-long-talk__* |
| map-faithful (lane w4: still one page at fold-inner) | desktop, phone, fold | bar 5 green once the spread was scoped to the dialogue | same runs | tooling/.reports/ui-lab/shots/map-faithful__* |
| dialogue-trader, -trader-topics, -non-trader, -non-trader-topics, -long-talk (lane w10: services lead the list, universal topics in order, phone pages) | desktop, phone, fold | bars green but shared findings (crafting.css:13 lint, js/css budget); reader: trader obvious PASS; phone log 45% FAIL; trader-topics phone first topic clipped, long-talk fold chip row clipped (lanes/2.9b/w10-reader.md) | 111 s, 83 s | tooling/.reports/ui-lab/shots/dialogue-*trader* |

## Reader checklist

Alchemy: the bag's ingredients as rows with count and the effects the
skill sees (unseen slots as "?"); the by-effect chips filter the list; two
to four picked, the shared effects listed; Brew reachable; the brewed
potion named by its effects; the potions panel with Drink or Coat. The
novice shot (Alchemy under 15): the filter reads "No effects known yet".

Smithing: Forge, Temper and Mend tabs; the tier line; recipes grouped by
material tier with inputs owned against needed; recipes over the tier
greyed with the reason; Temper rows with grade and the next gate.

Enchanting: Enchant, Disenchant and Recharge tabs; item, learned effect,
gem choices; magnitude and duration sliders; the cost line against the
budget and the soul's share; disenchant rows with the warning; recharge
rows with charge and the gem.

Every shot: nothing cut or overlapping, Close reachable, pad focus visible,
text legible on the phone.
