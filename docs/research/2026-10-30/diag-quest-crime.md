# Diagnosis: lf83-components stage-10 notice, w3-crime GetCrimeGold (batch game-12 20261030T133637)

Mode: diagnose, read-only. Evidence comes from the batch's report.json and failure.json files, the stills (read by a `reader` agent) and the tree. No game log was kept for the batch, so the timing in red 1 is inferred from the code and the lane map. Re-proving it settles it.

## 1. lf83-components: no ArgoniaJournalNotice in step stage-10. Cause: the journey

**Root cause.** The notice is sent and the bridge's sink works. What is wrong is the step the journey checks it in.
- Send path: the fragment calls `ArgoniaCore.AddJournalEntry` (skse/ArgoniaCore/src/natives.cpp:80-91). That calls `JournalNotice` (views.cpp:411, a main-thread task), which calls `JournalNoticeNow` (views.cpp:297-312). `JournalNoticeNow` shows the engine's `ShowHUDMessage`, updates our HUD stack, and sends `SKSE::ModCallbackEvent{"ArgoniaJournalNotice", "<quest> entry|clue", mark}`. Clues go through the same path (engine.cpp:177).
- Sink: `Sinks::ProcessEvent(ModCallbackEvent)` pushes kind `mod` (skse/ArgoniaBridge/src/ep_events.cpp:76-80).
- The sink is proven in the same batch: lf83-endings passed, including the notice expectation at step f41-buy (05-.../report.json; lf83-endings.yaml:38).
- Stage 10 is set in the step **talk-takes**, not in stage-10. lane-game-10.md:21 maps it: "0 -> 10 | E at Takes ...; her greeting links two-charges". Knowing the topic is stage 10's fact, so the greeting sets the stage, writes the entry and sends the notice while talk-takes is running.
- The runner counts only events since the step began (tools/run_journey.py:305-310, `events ctx["since"]`). So in step stage-10 the notice has already passed: 5 other mod events were seen. The step's GetStage and JournalEntries checks pass only because they read state that already holds.
- The merge window (journal.cpp:53, 2 s per quest) does not matter here: the first notice is never merged.

**Fix (journey).** tests/journeys/lf83-components.yaml:
```diff
   - name: talk-takes
     ...
     expect:
       - {read: [core, ViewState, dialogue], path: value.body.speaker.id, eq: ...n1-3}
       - {read: [core, KnowsTopic, topic.claywater-two-charges], path: value, eq: true}
+      - {console: "GetStage ARG_Q_LF83", contains: ">> 10", within: 8}
+      - {read: [core, JournalEntries], path: value, contains: "quest.local.lf83 10 0 ", within: 5}
+      - {event: {kind: mod, match: ArgoniaJournalNotice}, within: 5}
   - name: stage-10
     do: [{call: [core, ViewIntent, '{"type":"dialogue.goodbye","v":1,"body":{}}']}]
-    expect:
-      - {console: "GetStage ARG_Q_LF83", contains: ">> 10", within: 8}
-      - {read: [core, JournalEntries], ...}
-      - {event: {kind: mod, match: ArgoniaJournalNotice}, within: 5}
+    expect: [{console: "GetStage ARG_Q_LF83", contains: ">> 10"}]
```
Check the later notice steps the same way: each one must expect its notice in the step whose `do` sets the fact. hear-station, ford-tasted, clear-bend, get-clay and livia-agrees all appear to do so.

**Re-prove.** Run lf83-components once. Expected: talk-takes holds the notice event, with str `quest.local.lf83 entry` and num 10. If talk-takes does not see it either, read ArgoniaCore.log for `journal notice` / `merged into the last` (views.cpp:303, 312).

## 2. w3-crime: `Livia.GetCrimeGold` = 0. Cause: the journey's read (the game data is right)

**Evidence.**
- The crime data is in place. The faction is plugin/Argonia/Factions/ARG_Faction_ClaywaterStation - 0009C2_Argonia.esm.yaml, with flags TrackCrime (and HiddenFromPC) and Assault 40. Livia (ARG_Npc_WellKeeper - 000886) has Factions 0009C2 and `CrimeFaction: 0009C2` (line 115). Her template uses only Traits, so the crime faction is not overridden.
- Step face-livia passed `GetInFaction ... >> 1`.
- The hit landed. The strike expectation's hit event passed. The reader saw Livia's target bar with her health about 3/4, blood on screen, a boss-style red bar, and a partly hidden "Yo... ...inue fighting." line, so she is in combat.
- The read itself is wrong. The console `GetCrimeGold` run on a ref prints "Actor Crime Gold": the **calling actor's own** bounty (an NPC's bounty), not the player's bounty with that actor's crime faction. The journey header (w3-crime.yaml:4) assumes the Papyrus `Actor.GetCrimeGold` meaning. On Livia the console value is always 0. The w3-infra lane proposed `player.GetCrimeGold` or `GetCrimeGoldNonviolent ARG_Faction_ClaywaterStation` (lane-w3-infra.md:91-92). An assault is violent crime, so the matching read is `GetCrimeGoldViolent`.

**Fix (journey; no bridge change needed).** tests/journeys/w3-crime.yaml:
```diff
-      - {console: "ARG_Ref_ClaywaterStationLivia.GetCrimeGold", keep: gold_before}
+      - {console: "player.GetCrimeGoldViolent ARG_Faction_ClaywaterStation", keep: gold_before}
 ...
-      - {console: "ARG_Ref_ClaywaterStationLivia.GetCrimeGold", ne: {kept: gold_before}, within: 8}
-      - {console: "ARG_Ref_ClaywaterStationLivia.GetCrimeGold", not_contains: ">> 0.00"}
+      - {console: "player.GetCrimeGoldViolent ARG_Faction_ClaywaterStation", ne: {kept: gold_before}, within: 8}
+      - {console: "player.GetCrimeGoldViolent ARG_Faction_ClaywaterStation", not_contains: ">> 0"}
```
I have not checked whether the console accepts a faction argument for that function. If it does not, change the target, not the meaning: either add a bridge read that calls `PlayerCharacter::GetCrimeGoldValue(faction)` / `TESFaction::GetCrimeGold` (ep_state.cpp), or call the Papyrus `ARG_Faction_ClaywaterStation.GetCrimeGold()` through ArgoniaCore.

Also tighten the hit expectation: `match: "*"` accepts any hit. Livia's ref form ID should be the match. Side note: still 02-draw shows no sword and a "Controller Disconnected" toast, yet IsWeaponOut passed. Because the pad dropped out, the draw may have come from a later input.

**Re-prove.** Before editing anything, at the console on the game machine after the strike, compare `ARG_Ref_ClaywaterStationLivia.GetCrimeGold` (expect 0) with `player.GetCrimeGoldViolent ARG_Faction_ClaywaterStation` (expect 40). Then run w3-crime once with the new read.
