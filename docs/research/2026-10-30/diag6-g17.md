# diag6: game-17's round-2 reds (read-only diagnosis, 2026-10-31)

Evidence: /home/ubuntu/wt-game17/out/batch/adhoc/20261031T000000/* (reds17, deploy bea4119) and g17/20261030T225900/27-menus-quit.
Code read at a54c614. Stills read by a `reader`, not by this lane.

| red | owner | cause | fix |
|---|---|---|---|
| ui-sweep sleep-wait | **check** | the menu opened | journey match name |
| ui-probe close-dialogue | **our code** (dev probe) | the unfocused probe window gets no Esc | ViewProbe focus arg |
| lf83 mortar-tub | **data** | the tub sits 0.9 m inside the well head; E hits the well | move the tub ref |
| die-and-recover take-pile | **our code** | the player is still in bleedout after the wake, so E does nothing | end bleedout natively |
| grow-at-rest pending-level | **check, plus a log bug** | the re-enabled deserter walks off out of reach | hold him or re-move him |
| fight-archetype its-light-hit | **game AI / check (not proved)** | the deserter is unarmed in the stills | equip the kit, re-probe |
| menus-quit quit-confirmed | **tool (pad route)** | the pad is hot-plugged inside a paused menu and never goes live | open the Journal with the pad |

## 1. ui-sweep sleep-wait: check
- The still 13-sleep-wait.png shows "Wait how long?" open (slider 1, Enter Yes / Tab No). T is bound, and the router does not suppress the menu.
- The engine's menu name is `Sleep/Wait Menu` (~/.argonia/commonlib/include/RE/S/SleepWaitMenu.h:18). The bridge pushes `e->menuName` verbatim (skse/ArgoniaBridge/src/ep_events.cpp:69).
- The journey matches `SleepWaitMenu` (tests/journeys/ui-sweep.yaml:56 and :60).
- **Fix:** ui-sweep.yaml:56 `match: Sleep/Wait Menu`; :60 `match: '"menu": "Sleep/Wait Menu", "opening": false'`.
- **Re-prove:** ui-sweep from sleep-wait.

## 2. ui-probe close-dialogue: our code (the dev probe)
- bea4119 made ViewProbe call `g_api->Unfocus` (skse/ArgoniaCore/src/views.cpp:541-543), so frames-open could tick. Without the focus, both ESCs go to the engine, and the page's Escape (filter clear, then view.close) never runs.
- The still shows the window back on Livia's real state ("Livia Varinius", one topic), still open. The intercept's real talk replaced the probe, and nothing closed the view.
- **Fix (code):** add a second argument to `ViewProbe(topics, focus)`. Unfocus only when the argument is not `focus`. In ui-probe.yaml, step probe-300 calls `[core, ViewProbe, "300", "focus"]`. frames-open keeps the unfocused call. Register the extra argument in skse/core/src/bridge_call.cpp.
- **Interim (check only):** close-dialogue calls `[core, ViewIntent, '{"type":"view.close","v":1,"body":{"view":"dialogue"}}']`. This loses the Esc proof, so the code fix is preferred.
- **Re-prove:** ui-probe from talk-livia.

## 3. lf83-components mortar-tub: data
- In world/db/build_ref.jsonl the tub (`ref.claywater-station.mortar-tub`, x 323.6, y 3061.5) is 0.9 m from the well head (`ref.claywater-station.well`, x 323.0, y 3062.2), "under the windlass cover". The well-head mesh takes the crosshair.
- At the mortar-tub step, ArgoniaCore.log logs `things: thing.lf83.well-head activated` twice (tail lines 192-193) and never logs the tub.
- The still shows the player standing on the well cap with no prompt.
- **Fix (data, through db.py):** place the tub clear of the well-head collision, about 1.5 m off on the cover's open side (for example x_m 325.0, y_m 3061.0, keeping yaw 30). Regenerate the ESM. The journey stays as it is (moveto the tub, 0 -100 0).
- **Re-prove:** lf83-components from well-head (well-head, then mortar-tub).

## 4. die-and-recover take-pile: our code
- The pile is placed where the player fell: (-3381.3, 752.2), 1.2 units from the camp. The player wakes in the same place.
- The take-pile still shows the yellow death tint, an empty health bar and no crosshair. The player is still in the bleedout state.
- ArgoniaCore.log has neither `took the pile back` nor `out of reach`. The perk's Activate entry (ARG_PRKF_RestIntercept.psc Fragment_1 -> TakeVastei, life.cpp:561) never ran, because a bleeding-out player cannot activate.
- Cause: the wake task restores AVs to `GetPermanentActorValue` and sends `NotifyAnimationGraph("BleedoutStop")`, marked UNVERIFIED (skse/ArgoniaCore/src/life.cpp:316-320). The life state stays kBleedout. After `forceav health 5`, the permanent value is also the forced low base.
- **Fix (code, life.cpp wake task, before `ResetActors`):**
  ```cpp
  // restore to full: avo->RestoreActorValue(av, avo->GetPermanentActorValue(av)) stays (after the check fix below)
  if (p->AsActorState()->IsBleedingOut()) { p->SetLifeState(RE::ACTOR_LIFE_STATE::kAlive); p->NotifyAnimationGraph("BleedOutStop"); }
  SKSE::log::info("death: bleedout {}", p->AsActorState()->IsBleedingOut() ? "STILL ON" : "ended");
  ```
  (Actor::SetLifeState: commonlib RE/A/Actor.h:696. IsBleedingOut: RE/A/ActorState.h:163.) The log line turns the UNVERIFIED into a check.
- **Check fix too:** setup forces health with `forceav`, which survives the wake. Use `player.damageav health <hp-5>` instead, so the wake's restore reaches full.
- **Re-prove:** die-and-recover to take-pile. The woke-at-camp expect gains `{log: {name: ArgoniaCore, contains: "death: bleedout ended"}}`.

## 5. grow-at-rest pending-level: check (plus a log bug)
- The rest skips the disabled deserter (`respawn: 1000088C is disabled; not reset`, ArgoniaCore.log:87; life.cpp:155). Then the journey moves him 300 units off and enables him.
- In the 04 still he is alive and walking away at the frame edge. In the 05 still he is gone. Out of combat, his AI walks him back to his placement, out of the loaded or targetable set.
- dev-grow's `find_any` then fails `IsDead()` or the lookup (skse/ArgoniaBridge/src/ep_dev.cpp:93-97). It cannot tell dead from missing.
- Log bug: life.cpp counts `2 actors reset` after skipping both (ArgoniaCore.log:89). Count only the actors reset.
- **Fix (check):** in pending-level `do`, before dev-grow, add `{console: '"{opp}".moveto player 0 150 0'}` and `{console: '"{opp}".startcombat player'}`.
- **Fix (code):** ep_dev.cpp:97 says which failure it is: "no actor" / "dead" / "not loaded (Is3DLoaded false)".
- **Re-prove:** grow-at-rest from rest-no-pending.

## 6. fight-archetype its-light-hit: the deserter is unarmed (not fully proved)
- The record has a steel sword (000840) and a steel shield (00084E) in Items, and no Outfit and no CombatStyle (plugin/Argonia/Npcs/ARG_Npc_AmbushDeserter - 000858_Argonia.esm.yaml:21-27). Template 0551C7 lends Traits only.
- The reader sees him in a loincloth with no weapon, crouched with an arm to his head (02-record-values, 03-its-light-hit). He holds the kit but has nothing equipped and swings at nothing within 12 s.
- In die-and-recover the same actor kills a 5-health player. So he does fight there, but that death may have come from his fists or another source.
- Most likely: an unequipped weapon plus the step's `player.unequipall` (an unarmed target). Not proved: there is no GetCombatTarget or IsWeaponDrawn read.
- **Fix (data):** give the NPC a DefaultOutfit, or equip the sword and shield in the scene: `"{opp}".equipitem ARG_Weap_SteelSword` in the claywater-ambush scene. Our numbers stay the same.
- **Check:** before its-light-hit, read `"{opp}".GetEquippedItemType 1` (expect 1, one-handed sword) and `"{opp}".GetCombatTarget`.
- **Re-prove:** fight-archetype from record-values, with those two reads added.

## 7. menus-quit quit-confirmed: tool (pad route)
- The 05 and 06-pre stills show the Journal on Quests with the **keyboard** footer ("Enter Toggle Active", "M Show on Map"). The UI never switched to the pad, so no pad input reached the menu. It was not focus in our journal view: this is the vanilla Journal Menu.
- infra/gpu-box/pad.ps1:12-19,62 makes a fresh ViGEm hot-plug on every call. Its warm-up nudge is a RightThumbY (camera) touch, which does nothing in a paused menu, and the pad is disconnected after each call.
- A pad plugged in while the Journal pauses the game is not taken up as the active device before the presses end. Favourites UP and B worked because they were sent in play.
- **Fix (journey, tests/journeys/menus-quit.yaml):** open the Journal from the pad in play, in the same pad call as the presses: `pad: "START:80 wait:1500 DOWN:80 wait:120 ... (x8) A:120 wait:1500 A:120"` (START opens the Journal on System). Keep the Esc step as its own check of the Esc route.
- **Fix (tool, optional):** a `-Warm` button in pad.ps1 that works in menus (for example LS click) in place of the RightThumbY nudge.
- **Re-prove:** menus-quit from system-tab, with the system-tab still showing pad glyphs.
