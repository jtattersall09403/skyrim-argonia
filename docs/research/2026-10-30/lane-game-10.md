# Lane game-10: LF83's components, the native sleep, the crocodile, PrismaUI bound (2026-10-30, 09:00 to ~10:30 UTC)

## 1. Deploys
| Deploy | What | Result |
|---|---|---|
| deploy10 | HEAD 19e4e67 (59a0c3c LF83 stage 0, afdbae4 door links, 9325354 map/suspend/den, f6177a7 ref heights) | DEPLOY OK 354 s |
| deploy2 | + ui-live's PrismaUI wiring; DLLs built from a HEAD worktree (other lanes edit skse/ in the shared checkout) | DEPLOY OK 419 s; PrismaUI.dll laid, 5 view pages |
| deploy3 | + af6c541 crocodile aggro, ui-gaps (HUD hiding, chart revealed, journal text) | DEPLOY OK 242 s |
| deploy4 | + a196939 (HUD entries marked by our own member) | DLLs from a HEAD worktree; ESMs unchanged |

- `stack.py verify` after deploy2: 1 bad, `skse\plugins\tk-dodge.toml (tk-dodge-re-addon)` differs from the record
  (not ours to fix here; the combat lane's roll lock writes it).

## 2. LF83 as component checks (owner ruling bb7395f): green twice
`tests/journeys/lf83-components.yaml` (23 steps, ~61 s) and `tests/journeys/lf83-endings.yaml` (8 steps, ~72 s), each
PASS in 2 of 2 runs (g10-lf83d), from the first-place scene on the base save. No playthrough: each step sets one fact
through its real path and reads state.

| Stage / fact | Real path driven | Read |
|---|---|---|
| 0 -> 10 | E at Takes (intercept perk opens our view); her greeting links two-charges | KnowsTopic, GetStage 10, JournalEntries `lf83 10 0` |
| hear-station (obj 10) | E at Livia, `core ViewIntent dialogue.topic two-charges` | GetObjectiveCompleted 10 |
| 10 -> 20 | E at Signs, two-charges (offers clay-bend: ViewState topics), clay-bend | GetStage 20, journal `20 0`, landing-terms and cracked-well granted |
| why-failing (obj 20) | the well water activated; Takes' cracked-well (tasted) | GetFlag ford-tasted, objective 20 |
| old-mending (obj 31) | cracked-well again (mending) | GetFlag mending-heard; objective 31 once at 30 |
| clear-bend (obj 21) | the crocodile's death (staged `kill`; the fight is §4's check) | objective 21 |
| 20 -> 30 | the clay basket activated | GetStage 30, journal `30 0`, one-charge granted |
| 30 -> 40 | Signs: landing-terms, one-charge (agrees, takes the basket); Livia: one-charge (agree) | flags, GetStage 40, journal `40 1`, terms-settled, GetQuestCompleted 1 |
| 41 | 100 gold staged; Signs: two-charges, ford-charge (bought) | flag, GetStage 41, journal `41 1`, completed |
| 90 | the month set to Last Seed (wet); a gold pickup makes ArgoniaCore re-read its facts | GetStage 90, journal `90 2` |
| 92 / 93 | Livia / Signs killed | GetStage 92 / 93, journal `92 2` / `93 2` |
| families | a rest at the camp, every family digest kept, ArgoniaRest loaded | all 9 digests, journal, SaveCount, stage, flag, topic equal |

Found while cutting them (one fix each, in the journey):
- Livia agrees to one charge only once landing-terms was heard **of Signs**: the first run failed there (flag false);
  the step now asks it first.
- One run lost the E at Livia (the view never opened; objective 10 stayed 0). Each talk is now an `-open` step that
  asserts the speaker before its intents, so a lost key fails where it happens.

Not covered, with reasons:
- **No "journal updated" notice exists.** ArgoniaCore writes the entry (natives.cpp:66-77, one log line) but raises
  no HUD notice, view push or event, at a stage or at a clue (an objective). The router rows `questNotice` and
  `engineMessage` (router_table.h:67,70) have no handler. The checks read the journal family instead. **Owed: a
  build item** (the notice at each stage and clue, observable through `core`).
- Ending 42 (stop charge dropped) needs Livia's disposition >= 70; no real path stages it.
- crack-seen, tub-seen, ledger-read have no real path (the well head and mortar tub carry no script; the ledger
  has no read hook; `item.station-water-ledger` has no forms.h row). The quest does not need them.
- A season that turns while no fact changes is noticed only at the next fact change (FactsChanged runs SeasonCheck;
  plain time passing outside the Sleep/Wait menu does not).

## 3. Livia's bed, the native way
- e7ee9f3: a home's sleep package is Location "in cell" (her station house, 893374 KotM, borrowed) on vanilla's
  Sleep template; the template's Target finds the bed she owns there (the bed ref 8933BE already carries her
  ownership, 000886). L1: `check_package_targets` now also requires the home cell to hold a ref owned by every NPC_
  that runs the package (2 tests, one fails on purpose).
- In game (deploy2, `tests/journeys/livia-sleep.yaml`): at 20:30 she is outside; at 23:00 she is in her house
  (GetInCell 1: she walked to her door and the door link took her in) running ARG_Npc_WellKeeper_Sleep (000885);
  asleep (GetSleeping 3) 39 units from her bed at 23:54. The first runs read her 20 s after the player entered and
  failed (0); the read now waits up to 90 s.
- The hut door still (B4): the first still faced the pod's back (the door-local axis taken the wrong way); re-shot
  facing door-local +y.

## 4. The crocodile
- Placed and alive at its den; **it did not attack** a player 200 or 430 units away (2 of 2 runs failed at
  attacks-near), though it detected him: Aggression 2 and Confidence 4 from KotM's template, but its AIDT has
  AggroRadiusBehavior off and every radius 0 (EncWolf/EncBear: on, 2000/1500), and our NPC_ took AIData from the
  template. Fix af6c541: creatures carry their own AI data (VeryAggressive, Foolhardy, radii 2000/1500 as vanilla's
  predators), CombatRecords.cs writes the radii, L1 `check_creatures` (fails on the old flags).
- **Still no attack after af6c541** (deploy3, 2 of 2 runs red at attacks-near). Our placed one, a fresh `placeatme`
  of our base and of KotM's own base (08000A04) all stay out of combat 185-430 units from the player on the bank,
  while a vanilla EncWolf (shown as "Raptor" by Tropical Skyrim) placed 600 units away fights at once, so the player's
  state is not the cause. Record evidence: KotM's race CrocodileWaterRace 000A01 is a slaughterfish clone, DATA
  flags 0x02504040 = Swims **without Walks**, slaughterfish skeleton and movement types; our NPC_ has no combat
  style (KotM's base carries csSlaughterfish; vanilla predators carry ZNAM and DPLT 095F47). A swim-only creature
  does not start a fight with a target it cannot reach, and fixes-1 moved its den out of the pool onto the bank.
  Factions are cleared (no stack override; no relation to PlayerFaction either way, as for the wolf).
- **Planner's call (the crocodile is the planner's, bb7395f):** (a) the den back in the water, where it hunts (the
  LF83 fight at the water's edge), plus our own combat style; (b) a RACE override with Walks (the slaughterfish
  graph on land is unproven); (c) a walking crocodile race from another mod. The killable and no-respawn checks
  (tests/journeys/croc-den.yaml) wait on it. Cheapest proof of the cause: the KotM crocodile beside a swimming player.

## 5. ui-probe (1.2 §0)
- deploy2: `bound` ok: **PrismaUI binds on 1.7.104** and every page reports DOM ready. `hud` failed: `core Views`
  had no "vanilla-hud hidden" line (ui-gaps' HUD hiding was not in that build).
- deploy3: `hud` red: "vanilla-hud hidden 4/4, 0 out of HudElements" (the clips hidden, none taken out of the list).
- deploy4 (a196939): `hud` red again: "vanilla-hud hidden 4/4, 0 out of HudElements (22 listed)". The runner stops
  at the first red, so frames-closed/open, scroll, journal, Escape, chart and relaunch have not run: decision 0017's
  numbers other than "binds on 1.7.104" are still owed.

## 6. Batch 2 (deploy3)
(pending)
