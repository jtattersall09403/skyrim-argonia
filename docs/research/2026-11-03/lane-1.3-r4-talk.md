# Lane 1.3-r4-talk (round 4): Claywater people talk; no Talk on a corpse or a fighter

Owner play test 3, findings 24, 27 and 28. Proven at L1, L2 and L3. The L4 check is owed: journey `claywater-talk` and its row in the 1.3 ledger.

## Causes

1. **Topics hidden until learned (24, "Livia only has Barter").** `skse/core/src/topics.cpp:189` (`offered`) listed a topic only if the player already knew it or it was a service. A topic is learned from a keyword the player has heard. So a first meeting whose greeting taught no keyword showed Barter alone. Measured on the store at a first meeting: Livia offered 2 topics, Takes-The-Short-Weight 1, Signs-For-The-Cargo 1. A log from 2026-10-30 (g15-reds2 first-place) shows the same: 1 to 2 topics.
2. **Gaius Vibius silent (24).** He is built as a speaker: `place_build.py:325` gives him the ARG_Speaker keyword. But he had only imported reference lines. `topic_tables.py` keeps only written lines, so `talk::speaks` refused him. The perk had already replaced his vanilla Talk (`dialogue.cpp` OpenDialogue, then "not an Argonia speaker"), so nothing opened. The other Claywater people (Keeps-The-Second-Ledger, Abhuki, Mee-Seesh) are not built by any place, so they are not in the plugin.
3. **Talk on a corpse or a fighter (27, 28).** The intercept perk's only condition was HasKeyword (`hooks_records.py:23`). The perk uses Replace Default, so its "Speak" replaced the engine's Search on a dead speaker. The HUD prompt (`ArgoniaCore/src/views.cpp` SetPrompt) showed the engine's activate text for any actor, the deserter in combat included.

## Changes (pushed to origin/main)

- **3bf65d4.** The perk's tab 1 now also requires GetDead == 0 and IsInCombat == 0. Skyrim.esm's DA11Cannibalism gates its corpse choice with GetDead on the same tab. `PerkRecords.cs` groups conditions by tab and supports both functions.
  - New core rule `offers_talk` / `actor_prompt` in `skse/core/views`: a corpse's prompt is Search; an actor fighting the player gets no prompt.
  - ArgoniaCore's prompt and `OpenDialogue` both apply it. ActorAtOf (engine.cpp) reads dead, and in combat and hostile to the player.
  - The perk YAML is regenerated.
- **d73657f.** Topics of class service, newcomer and local are offered from a first meeting, unlearned. Morrowind's starting topics work the same way. Uses `topics::Topic::open` and `topic_tables.OPEN_CLASSES`.
- **12b9678.** Journey `tests/journeys/claywater-talk.yaml` (`--dry` ok) and an owed row in the 1.3 ledger of checks.md.
- **c315f19.** Ten written lines for Gaius (dialogue-writer, lint clean): 4 greetings, a goodbye and 5 answers.
  - New L1 test `test_speakers_talk.py`: every built speaker at the place has written lines in the store. It failed on n1 before this commit and passes after.

## Evidence

- `skse/check.sh`: 36/36 pass. This includes core.views actor_rule, core.talk every_speaker_greets_with_topics and core.topics.
- Topics offered at a first meeting: Livia 14, Takes 12, Signs 12 (measured before Gaius was added). Gaius answers 5.
- `test_hooks_records.py`: 3 pass.
- Built perk (out/Argonia.esm, worktree): one condition tab holding HasKeyword, GetDead and IsInCombat.
- L3: `ui/fixtures/dialogue.json` already shows a greeting with 6 topics (Signs-For-The-Cargo). It is exercised by the ui_harness stills.
- `make check-reach`: 342 pass, 3 red, none reached by this lane:
  - two in `tools/tests/test_world_sample.py`: stale weather names in the sample;
  - `test_unit_facts_live_only_in_the_units_module` on `vegetation/seat.py`.
- ArgoniaCore (the Windows DLL) is built only on the game machine. Its compile is checked at the planner's deploy.

## Owed and open

- **L4:** the `claywater-talk` journey. It talks to each of the four people and reads `topics` through the bridge, one still each, then kills Livia and expects a ContainerMenu, never our window. Needs the new ESM and DLL deployed.
- **Gaius's facts:** his brief has no facts for the road, Gideon, Onkobra, prison-road, danger or directions, so he stays silent on those topics.
- **Unanswered reference:** n1-3's line "Ask Gaius Vibius" (about-imperial-legion-remnant) has no answer from Gaius.
- **Conflicting records on his hut:** `fact.claywater-station.people-household` puts it on the landing bank; his stance puts him in the station half.
- **Prose review:** `text-review` has not yet been run on Gaius's lines.
