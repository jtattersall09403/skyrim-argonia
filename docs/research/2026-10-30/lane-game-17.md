# Lane game-17 (2026-10-30/31): code-fix proofs, the all-batch, a reds round; hand-off

Machine: argonia-play, the g4dn. Deploys from a clean worktree (/home/ubuntu/wt-game17): 409f252, then 28a9a5a
(+f4d8056 world-markers), then bea4119 (dev-grow fix, journey fixes, ViewProbe unfocus). Batches: adhoc 223639 (code
fixes), g17 225900 (all.yaml minus world-sample and smoke, 28 items, 16 passed), adhoc 20261031T000000 (reds17, 7
items, 1 passed). Slot released at the end; the machine is left running for the next lane.

## Code-fix proofs (live, interactive)
- **Map close: proven after a fix.** At 1aa3444 the chart closed itself at once: the router's kHide does take, so
  MapMenu's close event (sent while it opens) closed the new chart through 1aa3444's "MapMenu close closes the chart"
  sink. Removed (28a9a5a). Live: M opens the chart (`chart ready open`), and B (pad), Tab, M and the touch Close intent
  each close it (`views: chart closed by Sprint|Tween Menu|Quick Map`). Esc closes it by the os route; by the engine
  route it does not (the engine-route Esc never reaches our input sink). ui-sweep's map-closed now reads
  `chart ready closed` (the chart is the map) and passes.
- **B closes the journal with no roll: proven.** Pad Back opened the journal, B closed it, 0 TKDR_DodgeStart in the
  window; `+LX=0,LY=1:300 B:100` while moving gave 1 TKDR_DodgeStart. Touch B not rerun.
- **Favourites: proven.** The console has no favourite command; the sword was favourited in the inventory (I, D, S,
  F by the os route). Then Q and pad UP (the pad's name is `UP`, not `DUp`) each opened FavoritesMenu. With no
  favourite, Q and UP open nothing: game-16's red was the empty list. ui-sweep now favourites one item first; it passes.
- **lf83 stage 20: proven at the check.** The events ring held all four ArgoniaJournalNotice events (entry 10, clue
  10, clue 11, entry 20). Stage 20 is entered by hear-landing (diag5 §3); the expects moved there and stage-20 passes.
- **grow-at-rest dev-grow crash: fixed at source.** The crash came again after 1aa3444's guard
  (ArgoniaBridge+5E543 `jmp [rax+0x30]`, Deserter in RSI/R14). Cause: `target->DamageActorValue/RestoreActorValue`
  called Actor's inherited ActorValueOwner helpers. CommonLib declares ActorValueOwner at 0xB0 (SE), but on 1.7 it
  is at 0xB8 (`RUNTIME_CAST_ACCESSOR_VERSIONED`). The static base read a null vtable, and slot 6 (+0x30) is
  ModActorValue. Fix: call through `AsActorValueOwner()` (ep_dev.cpp). reds17: no crash. dev-grow now says
  "no player, or no living actor 1000088C" (see reds).

## Batch g17 (28 items): 16 passed
Passed: claywater-look, claywater-walk, combat-trial-a, dialogue-intercept, fight-damage-builds, fight-lock-on,
fight-roll-burden, quarantine, w3-crime, **first-place** (first pass), lf83-endings, livia-sleep, w3-interior-sun,
croc-den, rest-is-the-only-save, cosave. Every red was diagnosed in diag5-g17.md; the split and the fixes are below.

## Round 2 (reds17, deploy bea4119)
| journey | result | state |
|---|---|---|
| suspend-save | **PASS** | the crocodile ignores `startcombat` live (aggression 2, loaded, AI on); the deserter fights; IsInCombat prints "Prisoner is in combat", never ">> 1" |
| ui-probe | frames-open **passes** (ViewProbe drops its focus); fails at close-dialogue (ViewState still holds the dialogue after the probe: the unfocused probe window is not closed by goodbye) | check or code: close the probe view in the step, or ViewProbe closes on goodbye |
| ui-sweep | map-closed and favourites pass; fails at sleep-wait (T opens no SleepWaitMenu) | undiagnosed: read 13-sleep-wait.png and the menus |
| lf83-components | stage-20 passes; fails at mortar-tub (`flag.lf83.tub-seen` false) | undiagnosed |
| grow-at-rest | no crash; pending-level: dev-grow finds 1000088C dead or missing after rest-no-pending (disable, rest, moveto, enable) | the rest's reset or the player's blows killed him: read the step stills and `"{opp}".GetDead` |
| fight-archetype | still 0 hits in 12 s after moveto-then-startcombat | the deserter does not swing at an unarmed player: needs a still and `GetCombatTarget` |
| die-and-recover | the move to the pile ref works; take-pile: GetVastei 0, wanted 50 (E did not take it) | aim or activate: read 06-take-pile.png |

## Taken by diag5-fix (b7393c0, NOT yet deployed)
world-sample and smoke scene travel by moveto markers; w3-weather-stills and water-swim crashed in the same engine
culling signature on their scene's travel (diag4 class 1); quest-board's ending fragments now Stop(); attributes'
case-insensitive attribute names. ui-review round 1 (70943b1) is also undeployed. menus-quit: the still shows the
Journal still on Quests, so the pad's RB/DOWN/A presses never reached the menu. A pad hot-plug in a menu, or keyboard
mode: undiagnosed.

## Fixes this lane (commits)
28a9a5a (chart stays open; ui-sweep map read; grow-at-rest keeps the player alive), 65eef1b (dev-grow
AsActorValueOwner; lf83, fight-archetype, suspend-save, die-and-recover and ui-sweep favourites at the check; the
installer step `installer/steps/terrain-lod.md` names xLODGen), bea4119 (ViewProbe unfocus), 69258ca (deploy.sh
stops the game before the stack push: a running game held argonia-views and the unpack failed twice).

## Still owed (hand-listed)
- The vastei pile still (reader) and pickup: blocked on die-and-recover take-pile.
- xLODGen restore through the stage and a Claywater still: NOT run (about 26 min of `lod.sh run prepare terrain
  collect`, then `lod.sh still`). The installer step is written.
- `stack.py verify` 0 bad (restage tk-dodge.toml): NOT run.
- Respawn flags: L1 read only. The deserter's NPC_ has Respawn and the crocodile's has none (plugin YAML).
  rest-respawn passed (game-16).
- Touch B close (no roll): not rerun.
- Engine Fixes Part 2: NOT tried. Try it only if world-sample and smoke still crash after b7393c0. Two more items,
  weather-stills and water-swim, crashed in the same signature in g17.

## Next lane
One deploy at origin/main (b7393c0, 70943b1 and the above). Then the reds: world-sample and smoke 3x each last, and
the Part 2 trial if they crash.
