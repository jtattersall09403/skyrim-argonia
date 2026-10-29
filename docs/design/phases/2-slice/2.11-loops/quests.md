<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.11-loops/quests.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 2.11 loop: the slice quests by packet

The quests touching a slice place are written by region packet against the
[recipe](../../../quests/87-written-quest-recipe.md). A quest is data: its
record, its text, its lines and one `packages/narrative/src/data/scripts/<code>.json`
the one world host drives. LF83 is done (the exemplar); MQ01 is 3.4's and is
in the validator set only.

## Packets

`*` marks a quest wholly inside the slice; the rest stop cleanly at their
first stage past it (recipe § partial).

| Packet | Anchor slice places | Quests |
|---|---|---|
| P1 | Greenspring, the wamasu shrine | MR01, LH07, LH37, LH38*, LH51, LD65, the Hist Trial stand-in |
| P2 | upriver Hist village, jungle root hollow | LP13, LP14*, LP19, SX08 |
| P3 | Riverwalk, Teeth of Sithis, the Broke Column, the Naga camp, the bog-iron workings | LV38*, LV39, LV40*, NI05*, FG07*, LQ15, LF21, LN07, LF67 |
| P4 | Chasepoint, the lighter flotilla | LQ29, LM38, LM56, LM57, LM62, TG04*, LM08, LM23 |
| P5 | Rose-Bone waystation, Pearl Lots, the voriplasm vault, the opening work camp | BC05, LR03, LR24, LR39, SX05, SX06, LR52, MQ32 |

The Hist Trial stand-in (0157): a Root Steward of Hissmir gives the Trial of
the Burnished Scales at Greenspring and grants `heard`. P1 authors two
records: the canon Trials quest anchored on `place.dunmer-north.hissmir`
(stages left to the packet that builds Hissmir), and the stand-in with
`standInFor` naming it. The validator reds once Hissmir passes its gates
while the stand-in still grants.

## Coverage

Each row is carried by a quest whose premise already holds it. The packet
writes the row into that quest; it does not bend another quest to fill it.

| Row | Quest (packet) | Why it fits |
|---|---|---|
| favour paid by labour where coin is worth nothing (0141) | LD65 (P1) | The wamasu shrine is interior tier (no purse). Pilgrims pay in offerings, not coin; the work against the worsening flood is the favour. 0157 rules floods out as a mechanic, so the labour is the offerings and the shrine's upkeep, not a flood system. **P1: done** (LD65: river salt laid on the shelf keeps the village turn; no coin. The headwoman Hassk-Kaya gives the shrine blessing on a favour hooked to quest.local.ld65, paid at completion: 374fe9abe, test in magicServices.test.tsx. scripts/ld65.json drives green: complete and two fail paths). |
| consequence is a local-state variant | LV40 (P3) | The silted cove at Riverwalk: the sounded way silts or is cleared, an overlay variant on the place. **P3: done** (LV40 stage 10 `applyLocalVariant` [riverwalk, `variant.riverwalk.cove-silted`], stage 30 `clearLocalVariant`; scripts/lv40.json: complete on 30, four death paths failed on 90, every save point; the variant's overlay record is the place-builder's, planner-ruled). |
| hostile entry by flip | NI05 (P3) | The offering at the last bend grants Nisswo rank 1, which flips the Teeth of Sithis to sanctuary; the priest is met inside. **P3: done** (NI05 stage 10 outside at `socket.teeth-of-sithis.q-post-last-bend`, onEnter `setFactionRank` [faction.nisswo, 1]; stage 20 inside; scripts/ni05.json: complete on 30, both deaths failed on 90). LF21 stays partial: parley outside, stops at Gideon (4.2.imperial-fringe). |
| hostile entry by clear | SX08 (P2) | The jungle root hollow is hostile and clearable; the thing taking foragers is cleared. **P2: done** (SX08 stage 10 objective placeCleared on the hollow; scripts/sx08.json ends outside 4.2.saxhleel-coast on 20). |
| hostile entry from outside | LQ15 (P3) | The bandits who count boats are watched from the toll road, a socket outside the Broke Column's hostile scope. **P3: done** (LQ15 stage 10 `entry: outside` at `socket.the-broke-column.q-watch-toll-road`; scripts/lq15.json ends outside 4.2.imperial-fringe on 20; LF21 and LN07 use the same shape). |
| the Hist Trial stand-in (0157) | the stand-in (P1) | See above. **P1: done** (LH63 standInFor quest.local.ht01, grants `heard`; scripts/lh63.json drives complete and both fail paths; HT01 anchored on Hissmir, outside 4.2.dunmer-north). |
| verb: talk | LH37 (P1) | Two delegations want the use of the spring written down: talk on both sides. **P1: done** (LH37 verb talk; scripts/lh37.json ends outside 4.2.hist-heartland at Nine-Trunks from every save point). |
| verb: collect | SX06 (P5) | Four families dive the heirless lot to make a claim; the player collects from the lot. **P5: done** (SX06 stage 10 hasItem item.deep-lot-pearl at `socket.pearl-lots.cache-deep-lot`, an unowned drowned diver's basket 8 m down; stage 20 shown to the tender; scripts/sx06.json ends outside 4.2.saxhleel-coast on 30, both tender deaths failed on 90, every save point). |
| verb: deliver | LR03 (P5) | A bone-tag comes back for a woman said to have walked out; it goes to her family. **P5: done** (LR03 stage 10 onEnter giveItem item.bone-tag, objective hasItem + topicHeardFrom Vees-Kai; stage 20 takeItem, outside 4.2.imperial-penal-south; scripts/lr03.json, both endings, every save point). |
| verb: clear | SX08 (P2) | As the clear entry above. **P2: done** (scripts/sx08.json). |
| verb: steal | TG04 (P4) | The burglary of the house that floats. **P4: done** (TG04 stage 10 hasItem item.flotilla-hull-tally; successor to 40 failed on `worstCrimeIs` [mercantile-coast, theft], the crime ledger the game wires in scene/interact/crime.ts; the driver host answers `crime.<region>` and `owing.<region>` (worldHost.test.ts); scripts/tg04.json: unseen complete on 30, seen failed on 40, purser deaths failed on 90, every save point; the owned container on hull h-n02 is a place-builder job). |
| verb: enter a hostile place | NI05 (P3) | The Teeth of Sithis is hostile at baseline (Nisswo); the sect's claim is met inside. **P3: done** (NI05 stage 20 asks Zaxi-Rekh inside after the rank flip; FG07 enters the Broke Column by clear, stage 10 placeCleared). |
| verb: pay a favour | LD65 (P1) | As the favour row above. **P1: done** (as the favour row). |
| verb: walk a direction | LM56 (P4) | The coast road survey went east of Soulrest; the player follows it by directions from Chasepoint. **P4: done** (LM56 stage 10 `directions` [rose-bone-waystation from chasepoint], objective discovered(rose-bone-waystation); stage.direction 0 red; scripts/lm56.json ends outside 4.2.mercantile-coast on 20, keeper death failed on 90, every save point). |
| verb: discover | LP14 (P2) | The cut mark at the waterline on nine bends, found bend by bend. **P2: done** (LP14 objective discovered(socket.upriver-hist-village.marker-waterline-cut); scripts/lp14.json completes on 30 from 3 save points, both fail paths end on 90). |
| verb: read | LR24 (P5) | The trafficker moves the living on the paperwork of the dead; the papers are read. **P5: done** (documents.json `teaches` (item_views gate, tests/test_document_teaches.py, world/98); the driver's `reads` step and the host's `read`; LR24 stage 10 knowsTopic(topic.tag-seventeen) at `socket.rose-bone-waystation.item-charge-ledger`; scripts/lr24.json ends outside on 30, three death paths failed on 90). |

No row lacks a fitting quest.

## Gates per quest

The recipe § 5: `worldgen.quests --check` 0 red on every `stage.*` rule; the
driver plays each ending from a new game and every save point
(`npx tsx packages/narrative/src/driver/cli.ts <quest-id>`); `lint_prose`
green on every text file touched; vitest and tsc in `packages/narrative`
and `packages/text-catalogue`. Nothing is filmed (0156 level 4).
