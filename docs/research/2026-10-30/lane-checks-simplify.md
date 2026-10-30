# Lane checks-simplify (2026-10-30)

Owner rulings of 2026-10-30 (owner brief): test our integration, not other modders' work; in-game checks are simple
and in real places (no proving ground, no arena, no road walk); every in-game check runs in one batch, crash-prone
last. Build-VM lane: nothing deployed or run in game; every touched journey passes `run_journey.py --dry`.

## What changed

- `tools/run_batch.py`: journeys carry `crash_risk: low|medium|high` (unset: medium; any other value refuses).
  `--write-owed` orders by it, save-changing (relaunch or `batch_last`) last within each tier; `--all` adds passed
  journeys; a journey with `stack: <set>` (another combat set) is left out. Fake-bridge test
  `test_write_owed_orders_by_crash_risk_save_changing_last` (tools/tests/test_run_batch.py).
- `tools/bridge.py`: `actors` requests resolve ref editor ids (as `console` and `refs` already did), so a journey can
  read a named ref's position, dist, dead and disabled.
- `tests/journeys/batches/all.yaml` (written by `run_batch.py --write-owed --all`, 30 items) replaces game-12 and
  game-13 (removed). Scenes `duel-ring` and `proving-ground` removed; no journey uses ARG_ProvingGround or ARG_Booth.
- w3-road-hops was already deleted by the world-fixes lane (with world_sample.py's generator output).

## Journeys

| Journey | crash_risk | Now proves | Cut, and why |
|---|---|---|---|
| combat-trial-a | low | On the Blackwood Road (claywater-ambush): Precision.esp and TKDodgeAddon.esp loaded; ArgoniaCore read TK Dodge's perk lock (log); unburdened player holds the perk; sheet up (strength >= 1) and carriers logged; TKDR_DodgeStart fires from the pad; TDM lock-on reports a lock < 2000 u | 12 roll-distance steps x 3 loads (TK Dodge's motion), poise naked/heavy, backstab, parry-riposte (Elden/Rim Parry), Papyrus queue under a 5-deserter brawl: all modders' behaviour; the duel ring |
| combat-trial-b / b2 | low, `stack: B`/`B2` | DSC's plugin loaded, our staged globals (crits on/off, debug trace), our Pandora output plays DSC's roll (moved > 150), TDM lock-on | DSC's poise, roll bands, backstab, killmove, parry, Papyrus load (DSC's own; trial numbers belong in combat.md); out of all.yaml since they need another stack |
| croc-den | high | Present, alive, enabled; IsSwimming in its pool; the bridge's named-ref read: not dead, within 7 m of the wading player, position kept; killed by console, away 11 days, still dead (our no-respawn flag) | It attacks / its hit lands; dies to blows (KotM's ambusher as built) |
| fight-archetype | low | The deserter's record values: level 10, max health 44, steel kit; its light hit on 0 AR is our 32 (31-33) | Aggro range (Skyrim AI), the player's blow, parry-riposte (mods), kill and rest-respawn (rest is covered by grow-at-rest); a weak owed level-20 step |
| fight-damage-builds | low | Pinned vanilla skills 0; carriers move on equip and back; novice (Str/Agi 40, LB 5) blow = 10.8 +-0.5, god (100/100/100) = 36.0 +-0.5 via dev-set at the step's start | Power-attack stamina (kept, never judged); the duel ring |
| fight-lock-on | low | R3 at 6 m locks (TDM API), within 2000 u; at 30 m R3 locks nothing (our lock distance) | Flick target switching (TDM's own); three placed hostiles in the arena |
| fight-roll-burden | low | Overloaded: our tier logs "roll locked" and the perk is gone; unloaded: "roll unlocked" and the perk is back | Roll distance, stamina per roll, i-frame trace (TK Dodge, i-frame generator) |
| die-and-recover | high | Unchanged checks (ours: wake point, vastei, pile); moved from the proving ground to the Blackwood Road | Proving ground |
| grow-at-rest | medium | Unchanged checks (ours: vastei, no vanilla XP, level waits for rest, sitting); on the Blackwood Road, deserter calmed so a rest is allowed | Proving ground |
| attributes, claywater-look, claywater-walk, dialogue-intercept, quarantine, quest-board, smoke, w3-crime | low | Unchanged (reads in one place) | none |
| first-place, lf83-components, lf83-endings, livia-sleep, w3-interior-sun, w3-weather-stills, water-swim, ui-sweep | medium | Unchanged | none |
| cosave, menus-quit, rest-is-the-only-save, suspend-save, ui-probe | high | Unchanged (relaunch, quit, save counts) | none |
| world-sample | unset (medium) | Generated; not edited here | Owed to the world-fixes lane: world_sample.py should emit `crash_risk: high`, then rewrite all.yaml |
| w3-road-hops | — | Deleted (owner: not necessary, too long) | whole journey |

Drafts (not runnable, untouched): nav-npc-walk, nav-sandbox-20, water-budget, water-npc-swim, w4-veg-densest; soak and
the `broken` must_fail fixture stay out of the batch.

## Not audited deeply

The unchanged journeys were sorted by risk only; their individual expectations were not re-audited against "could a
broken version of our work fail it". first-place, lf83-components and ui-probe are the long ones worth that pass next.

## Unproved until the next game slot

- `read: [plugin, X]` on an absent plugin replies an error; assumed to fail the step (the wanted outcome).
- The ambush deserter is assumed to be `actors 4000`'s first listed actor from the ambush marker (as fight-archetype
  already assumed).
- `hasperk` replies `>> 1.00` / `>> 0.00`.
