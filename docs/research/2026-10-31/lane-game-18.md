# Lane game-18 (2026-10-31): diag6 checks, three deploys, the reds rounds; hand-off

Deploys (all DEPLOY OK): 7903449 (diag5-fix, ui-review 1-2), c413ce5 (diag6-fix: bleedout, armed outfits, tub,
padhost; disposition), 41b7126+ (trader c745ef3, cliff probe), then the lake-bank probe (deploy 5).
Owner rulings applied: weather and swim checks deleted; crash-prone checks once; fight-archetype keeps only our records.

## Verdicts
| journey | result | evidence / state |
|---|---|---|
| attributes | **PASS** (g18a) | diag5 case-insensitive names |
| quest-board | **PASS** (g18a) | ending fragments Stop() |
| lf83-endings | **PASS** (g18a) | |
| w3-weather-stills, water-swim | PASS (g18a), then deleted (owner: base Skyrim) | no crash after the moveto-marker travel |
| smoke | **PASS** (g18b) | the persistent pad host works (walk by pad) |
| fight-archetype | **PASS** (g18b) | values, steel kit, outfit worn (GetEquippedItemType Right >> 1); swing/hit cut |
| world-sample | no crash in 5 runs; stops 1-6 pass (g18c) | s02 cliff: the probe stood on the limiter's ~83 deg VHGT ramp and slid (z 11019.66 at 0.2 s, then 3-47 m lower); fixed 6a1fe97 (probe on ground under 35 deg). s07 lake-bank slid 14 m: same fix (deploy 5) |
| lf83-components | tub **passes** (diag6-fix + aim square to the well line); CRASH at ledger-read | SkyrimSE+0EDC8C8 `mov rax,[rdi]` null, BookMenu on the stack, Book01.nif "Character Assets" just requested; `ARG_Ref_ClaywaterStationLedger.activate player`. ARG_Book_StationWaterLedger has no InventoryArt. **Real bug: needs a diag lane** |
| die-and-recover | bleedout ends (`death: bleedout ended` logged each wake); the pickup works (`took the pile back`) | g18c red was the check: the deserter killed the player again at the camp and a 1-vastei pile replaced the 51. Fixed: he is disabled at the wake (deploy 5 run) |
| menus-quit | pad live in menus (glyphs) | START opens OUR journal view, not System; back to RB RB from Quests (deploy 5 run) |
| ui-probe | red at close-dialogue | **Real bug:** Esc closes neither the probe nor the REAL Livia dialogue view, engine or os route (zz-esc live, two runs). The page maps Escape to back (ui/views/core/nav.ts:23, dialogue main.ts back()), so the key never reaches the page or back() never sends view.close. Needs a build lane |
| ui-sweep | red at favorites (g18b, g18c) | Q opened nothing; favorite-one (I, D/S/F os keys) passed but the still shows no menu: the favourite likely not set. Sleep/Wait name and Tab close fixed (untested past favorites). Barter steps untested |
| grow-at-rest | red at ten-blows (g18b, g18c) | `talk 1000088C: the crosshair never showed it`: still 02 he stands beside, 03 he is gone from frame. Began after diag6-fix (armed CSTY). setrestrained 1 did not help |

## Fixes this lane (commits)
25a51e6, 782118f, c413ce5, 41b7126 (check fixes from diag6 and the rounds), 6a1fe97 + the lake fix (world_sample.py
probes on standable ground), d06c456 + the lake marker YAML, die-and-recover and menus-quit fixes; ArgoniaCore
ViewProbe "<n> focus" keeps the dialogue focus.

## Owed (not run this lane)
- xLODGen restore and a Claywater still; `stack.py verify` 0 bad (tk-dodge); touch B on the journal.
- Vastei pile still: the take-pile still shows a flat tan slab at the feet, unclear (re-judge after the deploy-5 run).

## Next lane
1. Diag/build: Esc does not close the dialogue view (real play). 2. Diag: BookMenu crash on the ledger.
3. grow-at-rest ten-blows aim with the armed deserter; ui-sweep favourite set. 4. The owed list above.
