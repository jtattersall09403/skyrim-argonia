# Diagnosis 2: dialogue opens, w3-crime gold (batch 20261030T151243)

Evidence: the batch folder's tail-ArgoniaCore.log per item, report.json, stills read by a reader agent.
The perk, router and dialogue view work in game. Each of the three dialogue items fails for a different journey reason.

## 05 dialogue-intercept, step `closed`: journey
- The cause is the expectation `eq: ""` (tests/journeys/dialogue-intercept.yaml:11, and again at :31). When no dialogue is open, ViewState dialogue reads `null`. first-place.yaml:53 expects `eq: null` and passes.
- No game fault: in item 14 the perk opens our view for Takes and Livia (Core log 15:40:15, 15:40:55 `view dialogue <- ... speaker`).
- Fix: change `eq: ""` to `eq: null` at :11 and :31.
- Re-prove: run dialogue-intercept and check that step `closed` passes.

## 16 lf83-components, step `hear-station-open`: journey (approach)
- After the moveto, the Core log shows the cell change at 15:42:49, then nothing. No activation reached the perk: there is no `view dialogue` line.
- The still shows no NPC in front, no Talk prompt and no fade. Only a dark shape sits behind the player's hip.
- Cause: the speaker walks under AI. The 3 s wait (lf83-components.yaml:45) lets her move out of the crosshair before `E`. In item 14 the same steps worked (prompt shown), so the result depends on timing.
- Fix:
  - Have the step check its own target before the key: an expect or a guard on the crosshair ref (e.g. bridge read of the crosshair target = Livia), retried within 2 s.
  - Or issue the second `moveto player 0 110 0` after the wait, just before `E`.
  - Apply the same change to dialogue-intercept.yaml:15-19 and first-place.yaml:55-61.
- Re-prove: run lf83-components and check that `hear-station-open` passes.

## 14 first-place, step `livia-landing-terms`: journey (data is right)
- Our view was open on Livia. Core 15:41:19.889: `dialogue: ...well-keeper has no line for topic.claywater-landing-terms now`.
- At stage 10, Livia has no landing-terms answer by design. tools/argonia_world/tests/test_stage_walk.py:163 gives her that topic only after the endings (40+).
- The step asks too early (first-place.yaml:69-73).
- Fix: delete the step. The landing terms are learned of Signs in `ask-signs` (:74-83). Alternatively, move the step after an ending.
- Re-prove: run first-place and check that `ask-signs` passes, with KnowsTopic landing-terms true.

## 13 w3-crime, step `strike`: journey read; the blow landed
- The blow landed and Livia fought back:
  - Core 15:39:13 `grow: hit handToHand`.
  - Then nine `struck unarmored` lines, and the player died at 15:39:23.
  - The still shows her target bar drained and blood on screen.
- The faction is right: ARG_Faction_ClaywaterStation has `TrackCrime` (plugin/Argonia/Factions/...0009C2...yaml:8), and Livia is a member (step 1 passed).
- Cause: the console `GetCrimeGoldViolent` takes no faction argument. It ignores `ARG_Faction_ClaywaterStation` and prints the calling actor's own value ("Actor violent Crime Gold"), which is 0 on the player. Nothing in this batch reads the faction-scoped gold (Papyrus `Faction.GetCrimeGoldViolent`).
- Secondary faults:
  - The hit was unarmed (`handToHand`, no weapon in the still), so `equipitem 00012EB7` did not arm the player.
  - The player died mid-step. Our death/wake can confound the read.
- Fix:
  - Read the faction-scoped value through the bridge: a Papyrus/SKSE read of `ARG_Faction_ClaywaterStation.GetCrimeGoldViolent()`. Or use the console `GetPCFactionAttack ARG_Faction_ClaywaterStation`, which is faction-scoped (>> 1).
  - Make the expectation `within: 3` after the first hit.
  - Give the player an Argonia sword by editor id.
- Re-prove: run w3-crime and check that `strike` shows faction violent gold > 0 before any death line.
