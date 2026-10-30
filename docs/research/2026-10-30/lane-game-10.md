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
- In game (`tests/journeys/livia-sleep.yaml`):
  - **Home by 23:00: green** (4 of 4 runs): at 20:30 she is outside; at 23:00 she is in her house (GetInCell 1), so
    she walked to her door and the door link took her in, running ARG_Npc_WellKeeper_Sleep (000885).
  - **Asleep: red with the player in the room.** With the player in the interior from 23:00, GetSleeping read 0 after
    90 s (deploy3, 1 run) and after one more game hour (deploy4, 2 of 2 runs). Once, with the player gone outside,
    she was read asleep (GetSleeping 3) 39 units from her bed at 23:54. The bed is reached from its side (the nav
    journal: KotM's interior navmesh, nearest centroid 101 units from the bed's centre). **Next:** read her distance
    to the bed and her position over a minute in the loaded interior (moving, stuck at the side, or standing); the
    bed's furniture markers against the navmesh.
- The hut door still (B4, for nav-walk-2), read by a `reader`: the first still faced the pod's back (door-local axis
  taken the wrong way). The second, from door-local -y facing the door: live render; the door sits in a recessed,
  rounded alcove with a mud rim all round, not floating or buried; no gap, cliff or water at the sill (its base hid
  by the player and grass); nothing Nordic. "The pod and its recessed door read as Black Marsh and look correctly
  placed."

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

## 6. The combat trial (bdd9282, ba5e33d)
- pad.ps1 now holds a trigger or button across steps (`+LT=1:600 RB:120 wait:1500 -:100`; `-` releases them), so
  parry-riposte is a run step in combat-trial-a/b/b2 (99bd4d5).
- **B2: dead at Pandora.** `stack.py combat B2` installed and ran Pandora; `pandora-check` read every DSC FNIS event
  MISSING from the behaviours (BB_DSC_ForwardRoll_Fast, BB_DSC_Backstep_Med, BB_DSC_RightRoll_Fat_MAG,
  BB_DSC_pa_1HMKillMoveBleedOutKill, BB_DSC_pa_KillMoveH2HComboA, ...): "DSC's FNIS animations did not reach the
  behaviours (B is dead)". combat-trial-b2 failed at its first check, pandora-wired (moved 0 units, wanted > 150).
  Papyrus.0.log fetched to out/combat-trial/papyrus-b2.log.
- **B:** the same pandora-check (every DSC event MISSING, animdata 0 DSC clip lines); combat-trial-b then failed at
  its scene: "the game reported a failed load of argoniabase" (the base save is A's).
- **A (restore):** installed, main menu with 29 DLLs, 0 not loaded; combat-trial-a failed at pandora-wired (moved 0
  units, wanted > 150: the roll did not move the player). **`stack.py verify` after A: 20 bad** (was 1 bad,
  tk-dodge.toml, before the trial): the switch back to A is not exact on the machine. The next lane must read the
  20 names (`stack.py verify`) and restore A before any other check (a full `make deploy` relays the profile).

| Group | Pandora (DSC events) | Journey | Verdict |
|---|---|---|---|
| A (0.0 stack) | n/a | failed at pandora-wired (roll moved 0) after the restore | not measured; restore not exact (20 bad) |
| B (DSC) | all MISSING | scene load failed | dead at Pandora |
| B2 (DSC, crits off) | all MISSING | failed at pandora-wired | dead at Pandora |

- **The gate:** `make check` red in plugin-check: "order: Dark Souls Combat.esp is listed but not found in
  /home/ubuntu/games/skyrimse/Data" (links: 1 problem). Cause: combat-trial-prep's DSC rows (bdd9282) put DSC in
  the load order the links check reads, and the build VM's Data mirror lacks it. Not w3-infra's 002dca4.

## 7. Not done (hand-off to the next game lane)
1. **ui-probe** past `hud`: ui-gaps' a196939 still reads "0 out of HudElements (22 listed)" (deploy4). Either the
   next ui-gaps fix, or run the remaining steps with that one expectation relaxed to get decision 0017's numbers
   (frames closed/open p50/p99, scroll, journal key, Escape keeps System, chart, relaunch).
2. **The crocodile:** the planner's call in §4, then croc-den.yaml twice.
3. **Livia asleep with the player in the room** (§3 next step).
4. **w3-infra (002dca4)** asks for a deploy (Argonia.esm, the DLL with hook.road-closed, ARG_PRKF_RoadClosed.pex)
   and three checks: world-sample s09-gate-message (notice "The road beyond is closed.", crosshair "Open Border
   Gate", HasPerk ARG_Perk_RoadClosed 1, push-north stops), s10-sign-text (Gideon arm 0 reads "To Archon"; board
   direction and height; does a script-less named ACTI prompt), and crime (a theft in Livia's sight gives
   GetCrimeGoldNonviolent on ARG_Faction_ClaywaterStation > 0). Report docs/research/2026-10-30/lane-w3-infra.md.
5. **The world sample** (tests/journeys/world-sample.yaml, 79 steps, 13 scenes; deploy sends every scene, 30 sent).
6. **LOD** (lane-2.W4-lod.md's sequence; lod.ps1 not parsed yet), then the map check (FWMF needs the terrain LOD).
7. **The memory climb:** a load-only loop is written (scratch memclimb.py: A base-save loads, B exterior to the
   holding cell and back, C the holding cell reloaded; private MB after each). Seen in passing: 5,608 MB private
   after ~10 min of journeys on a fresh launch.
8. **The soak**, last, once, never a gate.
9. **Closing chunks:** none closes yet. 1.4 closes when the planner rules the three thing hooks (well head, mortar
   tub, ledger) and the missing "journal updated" notice (§2) dropped or deferred; 0.3 needs only recording
   (scene-to-scene time and the 238.3 s edit-to-verdict into journals/bridge.md); 0.2 §b needs verify clean
   (tk-dodge.toml differs), §c lock-on/climb/swim/menus, §d latency; 0.4 §d needs the other people's day and night
   reads and the stills.

## Commits
e7ee9f3 native sleep; 99bd4d5 LF83 component checks and pad.ps1; af6c541 (child) crocodile AI data; 4cc88c9 lint;
fdd620f croc-den and livia-sleep journeys, this report.
