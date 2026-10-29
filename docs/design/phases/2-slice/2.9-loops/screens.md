<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.9-loops/screens.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: screens (2.9 § Loops, lane 2.9e)

Rule (2.9 § e; decision 0146 item 7): every screen magic implies stands on
2.2's system on every device and input: a spell in a belt slot and in a
hand (its school's symbol), the cast meter on the reticle, the spell
seller, the disease line and notice, the known spells on the sheet, the
three service buttons and the teach topic, the active-effects strip fed
by the timed stack.

Code: `packages/ui/src/screens/Magic.tsx` (the magic window on the
four-slot quick belt and the hands), `Services.tsx` `SpellSellerScreen`,
`Stats.tsx` (`diseases`, `knownSpells`), `hud/Hud.tsx` `CastMeter`
(`HudView.casting`), `hud/effects.ts` `effectsFromStack` (2.9a2's timed
entry to `EffectView`), `hud/Belt.tsx` (an `ItemView` with `school`
draws the school symbol). Fixtures: `apps/ui-lab/src/screens/magic.tsx`
(built to the 2.9 contract; the live state binds as 2.9a2, b1 and d land).

Harness: `bash tooling/repo-standards/job_guard.sh 2.9e --mem 4 -- node
tooling/ui/ui_lab_check.mjs --screens <ids>` while iterating; the green
record from the five-part batch (`--part K/5`, tooling/ui/README.md). The
lab shoots desktop (mouse and keyboard), phone and fold-inner (touch and
the pad focus walk). Shots copied to `lanes/2.9/e-shots/`. The lab has
one colour scheme (no dark scheme in `packages/ui/src/tokens`), so light
and dark is one pass.

| Screen id | Bar | Result | Elapsed (last shoot) | Capture | Live (2.9e2 views, `scene/ui/session.ts`, test `magicViews.test.ts`; 2.9e4 hosts: studio lift `liftMagicViews` (`magicLink.test.ts`), dialogue `magicServices.tsx` (`magicServices.test.tsx`)) |
|---|---|---|---|---|---|
| magic-window | bars green; reader clear | PASS; reader: belt slots read by tip only, phone/fold panels below the scroll (P2) | ~20 s | e-shots/magic-window__* | `magicViewOf` through `pauseViewOf({ magic })`: known spells, belt spell slots, hand spells; studio pause deck live from the walk's session |
| hud-cast-charging | bars green; reader clear | PASS; reader clear after the word moved above the ring on touch | ~15 s | e-shots/hud-cast-charging__* | `castingViewOf` over `castHudState` (`magicHudOf`); sandbox `MagicHud`, still `lanes/2.9/e2-shots/`; studio HUD from the runtime's published `cast` |
| hud-cast-held | bars green; reader clear | PASS; reader clear (glow, Ready) | ~15 s | e-shots/hud-cast-held__* | `castingViewOf`: charged and sustaining read held |
| hud-cast-interrupted | bars green; reader clear | PASS; reader clear (red ring, Interrupted in bone for contrast) | ~15 s | e-shots/hud-cast-interrupted__* | `castingViewOf({ interrupted })`: the host holds the poise break, the cycle is idle |
| hud-magic-effects | bars green; reader clear | PASS; reader: notices right, Shield expired and absent | ~15 s | e-shots/hud-magic-effects__* | `activeEffectsOf` over the session's timed stack via `effectsFromStack`; studio HUD live |
| spell-seller | bars green; reader clear | PASS; grouped by school chip (stocks of 244 and 311); reader: side title wraps on fold windows (P3) | ~15 s | e-shots/spell-seller__* | `spellSellerViewOf` over 2.9d stock and `spellPrice`, `blessingPrice`, `curePrice`; dialogue host: Vees-Wai's stock, buy through `buySpell` and `applyPurchase`, blessing and cure rows |
| character-sheet-magic | bars green; reader clear | PASS; reader clear on desktop (Diseases, Spells Known at the top of column two); fold shows them after scrolling (P3) | ~15 s | e-shots/character-sheet-magic__* | `sheetMagicOf` through `pauseViewOf({ magic })`: diseases (stage of stages), known spells by source; studio sheet live |
| dialogue-tree-minder | bars green; reader clear | PASS; reader: Spells, Blessing, Cure present | ~13 s | e-shots/dialogue-tree-minder__* | the roster's services; `magicServicesOf` keeps teach only while unknown |
| dialogue-teach | bars green; reader clear | PASS; reader: the topic and the lesson answer present; teach is also a service button (`teach`, lane d) | ~13 s | e-shots/dialogue-teach__* | `teachOfferOf` (`teachPrice`) and `magicServicesOf`; dialogue host: Im-Moro's Teach while Hearth Heal is unknown, `teachSpell` then `learnTaught` |
| the whole grid (stale rule) | five parts PASS; screen-green.json newer than every source | PASS twice (670 shots, 73 screens, 933 s); restaled by another lane's lab edits after the run | 933 s | tooling/.reports/ui-lab/report.json | - |

## Reader checklist

Magic window: the slice spells under Powers and Spells with cost, Soultrap
marked beyond the skill; the chosen spell's school with its symbol, cost,
effect, and the Right Hand and Left Hand buttons; the hands panel showing
Fireball in both hands with the destruction symbol and the doubled-cast
line; the quick belt with Light and Hearth Heal on the item slots as
school symbols and Frost Bite in hand swap 1; nothing cut or overlapping.

Cast meter (three screens): a ring round the reticle's dot with the
destruction symbol inside; charging about half full with "Charging";
held full and glowing with "Ready"; interrupted in red with
"Interrupted"; the hands and the belt bottom left show the spells by
school symbol; the state reads in words, not colour alone.

Effects strip and notices: four effect symbols bottom right (Fortify
Willpower, Levitate, Light with time rings; Swamp Fever plain in the
disease tint), Shield absent (expired); the notices "You have caught a
disease" with Swamp Fever and "Spell learned" with Light.

Spell seller: the tree-minder's spells as rows, each with its school
symbol, name, magicka cost and price; Hearth Heal marked Known;
Soultrap's price beyond the purse dimmed; Levitate chosen, its effect and
"Within your skill" shown; beside it the Blessing (Fortify Willpower) and
Cure (Swamp Fever) rows with prices, the gold, Close reachable.

Sheet: the Diseases panel with Swamp Fever "Stage 2 of 3" in the disease
tint; the Spells Known panel under the skills: Mara's Gift under Powers
(once a day), the spells with school symbols and costs.

Dialogue: the tree-minder with Spells, Blessing and Cure buttons; the
fisher's topic "a light for the boats" asked, its answer offering the
lesson.

## Reader verdicts

Two readers (lanes/2.9/e-reader.md): the first pass found the cast word under the touch hand button, the sheet's magic panels off the desktop window and the seller's side title wrapping one word per line; all three are fixed and the re-read is clear. Left as P2/P3: belt slots name their contents only by tip, and phone/fold panels sit below the scroll.
