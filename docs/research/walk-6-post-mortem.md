# Walk 6 post-mortem: why the built opening (MQ01) went wrong

Lane R2 of [walk 6 (quests)](../phases/walk-6-quests.md), deliverable 7 of the
[handover](../phases/walk-6-quests-handover.md). Diagnosed from the files only (2026-11-12): the builder
`tools/ArgoniaPlugin/MainQuest.cs` and `QuestKit.cs`, the quest script `papyrus/ARG_QF_MQ01.psc` (and `ARG_QF_MQ03.psc`),
the built records in `plugin/Argonia` (worldspace `BlackMarsh - 23D689`, `Persistent` refs; quest `ARG_MQ01` 000E2D),
the quest record (`quest_record export quest.main.mq01`), `story/data/quest_lines/mq01.json` and `quest_people.json`,
the owner's two screenshots, and the base records read from `Black Marsh.esm` with a read-only parser.

## The short answer

Two things went wrong, and the checks could not see either of them.

1. **The design was a staged set piece.** The record's stages 30 to 93 are a march, a strike scene, a burning camp,
   a choice made by walking into one of two areas, an escort and a reveal. The build dropped the scenes, as no block
   could do them (MainQuest.cs:16-17), but kept the journal entries and lines written for them. Every stage after 30
   is set by where the player stands (five walk-in areas, MainQuest.cs:207-213). The journal and the lines describe
   the scene that was meant to happen, whether or not it did.
2. **The build added structures at coordinates typed by hand** (MainQuest.cs:36-37, 189-200): a Hearthfire fish dock,
   two Ashlander yurts, two campfires and a Whiterun ruin, at the fixed height z 0. None of them was placed against
   what already stands on BM&V's dock.

Every check passed because each one asks either "is the build what the record says?" (mainquestcheck 554/554 PASS
compares the build with a record that was itself the fault) or "can the engine do it?" (questcheck). None asks what
the player sees, or whether a journal entry is true of what has happened.

## Each fault the owner saw

**a. An extra piece of dock across the original one, its rope fence blocking people; a hut sunk in the water that
later "became a house".**
Cause: three statics placed by MainQuest.cs, each at the hand-typed height z 0.
`ARG_MQ01_Planks` (000E75) is `BYOHFishDock01` (0008CB:HearthFires.esm), a fish dock with a rope rail, at
4900,-5450,0, turned 90 degrees (MainQuest.cs:197, 204). It has no enable parent, so it is there from the start of
the game. The record wanted "plank boards over the deep water at the fire" (5900,-4700); the builder's `Planks` spot
is 1,250 units away, beside the huts (MainQuest.cs:37), and no step reads where BM&V's dock lies.
`ARG_MQ01_Hut1` and `Hut2` (000E72, 000E73) are `001Hut2` and `001hut3` (0AA5F0, 0AA5F2:Black Marsh.esm), whose
models are Morrowind's Ashlander yurts (`vvardenfell\ashlanderhut\exterior\alhut01ext.nif`, `alhut02ext.nif`).
They stand at z 0, the water's surface; the water's edge marker beside them snaps to z 1 (000E64), and the land under
them is about -120 (the fish trap at land + 10 is at -118, 000EA9). They have no stilts, so they look sunk.
They are under `ARG_MQ01_CampAftermath` (000E5C), set to the opposite of its state.
The "house": when an ending enables the aftermath parent (psc:223), both yurts switch off and `ARG_MQ01_HutBurnt`
(000E74) switches on, 200 units south, also at z 0. It is `WRHouseShack01DestroyedDUPLICATE001` (0D8589:Black
Marsh.esm), whose model is `Architecture\WhiteRun\WRBuildings\WRHouseShack01Destroyed.nif`: a ruined Whiterun house.
That is also a Nordic element reaching the player, against decision 0006.
Class: **new structures placed by hand coordinates; a thing switched on in view.**
Why the checks passed: placecheck lets a structure 256 or more across stand sunk "as Bethesda sinks foundations" and
fails it only when it floats (PlaceCheck.cs:17-19). It checks only actors' bodies against statics (PlaceCheck.cs:7-9),
never a static of ours against BM&V's statics. No check reads a base's model path for a Nordic set.
Ruled out by: the ceiling's world-edit row ("nothing built, nothing moved, no structure added"), and the quest form,
which has nowhere to write a structure.

**b. Reaching the camp fire set the next milestone, with a journal entry about events that had not happened; no
burning hut.**
Cause: stage 40 is set by `ARG_MQ01_ZoneFire` (000E7B), a set-stage box 400 units across around the fire, with
prerequisite 32 (MainQuest.cs:207). Stage 32 is set once the five walkers are loaded, or after 60 checks whatever
happens (psc:87-94). So stage 40 fires when the player reaches the fire, wherever the gang is. Its journal is the
record's text for a scene ("a tall Argonian woman... killed the courier... The camp is burning"; screenshot 13). That
scene was never built (MainQuest.cs:16-17); Fragment_40 does it all in one instant instead (psc:165-184).
In that fragment, the "burning huts" are two vanilla campfires (`Campfire01Burning` 035F49) at z 97
(`HutFire1`/`HutFire2`, 000E76, 000E77; MainQuest.cs:198-199), placed at the same x and y as the yurts' centres, so
they are inside the yurt models. No hut model burns. The courier's death did not show either (see c).
The files cannot say whether any flame showed through the yurt; viewing the cell in xEdit's preview or the Creation
Kit would.
Class: **the journal narrates the designed world, not the player's acts; a stage set by position.**
Why the checks passed: mainquestcheck confirms the stage's journal text equals the record's text (MainQuestCheck.cs:7-11).
quest_text_check and echoes check text against the record's facts, not against the world. questcheck's `stages` rule
asks only that a stage has a setter (QuestCheck.cs:13).
Ruled out by: plan rule 4 (a journal entry says only what the player has just done; stages move by talk, take, use,
death or another quest), and the ceiling's cut of walk-in areas and scenes.

**c. The gang walking back to the ship; Mee-Tuja "doing a weird crouching thing"; Deesh-Duun standing at the end of
the dock.**
Cause (the gang): the march package `ARG_MQ01_MarchOff` (000E81) is gated to stages 32 up to (not including) 40
(MainQuest.cs:220). At 40 it stops applying. Every base of the opening is built `Ai.Own`, which leaves out the
template's AI packages (QuestKit.cs:155-166), so the walkers have no package left. They go back to their placed
spots, the plank's foot by the barge (000E56 to 000E59, 5280 to 5405, -7800 to -7900). `AtFire` had first moved any
walker more than 400 units away to the fire, in the player's sight (psc:96-102, 166-170). The editor-location fallback
is the engine's, not a file; the owner's sighting fits it.
Cause (Mee-Tuja): Fragment_40 clears his alias (`Courier`, flagged Essential in the built quest) and calls
`Kill(Leader)` on the next line (psc:176-178). Three candidates: (1) he was still essential when Kill ran, and went
down into bleedout (a kneel), which fits "crouching" and "none of this happened"; (2) with no package left, his
idle by the campfire was a crouched warm-hands idle; (3) Kill worked and the crouch was a death pose (unlikely,
since the owner saw him moving). **The files cannot settle this.** The Papyrus log of the walk, or reading the save
for IsDead and IsBleedingOut on 000E55, would.
Cause (Deesh-Duun): Fragment_40 moves her to `ARG_MQ01_HutsMarker` (000E62, 4803,-5615,-86) (psc:180). Her base has
no package either, so, like the gang, she most likely went back to her placed spot at 5700,-4786. That is 200 units
west of the fire, at the dock's landward end, which matches "standing by the end of the dock". The files cannot tell
which of the two spots it was; e below favours the placed spot.
Class: **people moved by a script and by stage-gated packages; what they do when the package ends is not designed.**
Why the checks passed: questcheck's `route` and `start` rules check that a walker can reach the destination and starts
in the player's reach (QuestCheck.cs:10-11). No rule asks what an actor does after its last package's window closes.
Nothing checks that a scripted Kill is visible or that a killed alias is not essential.
Ruled out by: the ceiling's cut of "any package that makes a person walk, follow, lead or keep a timetable for a
quest" and "moving a person in view". Killing is not a result on the closed list, and plan "Anyone can die" removes
the essential flags.

**d. Deesh-Duun answering "Who are you?" with "The huts are burning and I am under the boards".**
Cause: `quest_people.json` (ARG_MQ01_DeeshDuun, second entry, line 245) gates this line on MQ01 stages 40 to 41.
Talk.cs:169-205 builds it into `ARG_Talk_QuestWhoareyou` (000F01), INFO 000F07, conditioned only on GetIsID and that
stage window. The line was written for where the design puts her (hiding in the huts, under the boards). Its only
condition is the stage, and the stage did not put her there (c).
Class: **a line describes the staged situation, not where the speaker stands.**
Why the checks passed: talk_check and quest_text_check read a line's reachability and its facts. No check compares a
line's claims about the speaker with the speaker's position.
Ruled out by: partly. With nothing moved and no scenes, a person stands in one place throughout, so the claim can be
checked. But no rule checks it: see "Not ruled out", 2.

**e. Talking to her did not count as reaching her.**
Cause: stage 42 ("reached Deesh-Duun") is set only by `ARG_MQ01_ZoneHuts` (000E7D), a box 600 x 600 x 500 centred at
4850,-5700,-100 in the water by the yurts, prerequisite 40 (MainQuest.cs:209; the record's successor 40 to 42 is
`inZone: zone.mq01.huts-first`). None of her lines has a result (Talk.cs builds quest_people INFOs with no
fragment). Standing at her placed spot (5700,-4786), she was 550 units outside the box, so talking to her could not
set 42.
Class: **a stage set by position, while the objective names a person.**
Why the checks passed: questcheck's `stages` rule needs only some setter for 42. The objective's target is Deesh-Duun
(`TargetsFromRecord`, MainQuest.cs:258-263), but nothing checks that the act which completes the objective concerns
that target.
Ruled out by: the ceiling (no walk-in areas; a stage moves on a line the player picks). The link between an
objective's target and its trigger is not a rule yet: see "Not ruled out", 3.

**f. The two cutters stood by the camp fire throughout.**
Cause: `ARG_MQ01_RootCutter1Ref`/`2Ref` (000E69, 000E6A) stand at 6225,-4684 and 6263,-4535, 335 and 390 units from
the fire (5891,-4716). The "shed" they guard is only that far from the fire. They are switched on with
`CellParent` at stage 40 (psc:173; this shows Fragment_40 ran at least that far). By design they have no package
("stays at the shed until the ending", MainQuest.cs:242). The kit's default aggression is Unaggressive, kept on
purpose (QuestKit.cs:153; MainQuest.cs:98-99), so the "cutters" the stage 40 objective tells the player to get past
or fight never act. With no combat, there is no combat music (g).
Class: **a set piece's people with nothing to do; an enemy built unable to fight.**
Why the checks passed: no check reads a person's intended role (an enemy) against their AI data. questcheck's
`people` rule checks only for two enabled people of one name.
Ruled out by: the ceiling (no set pieces; people placed standing where they are needed). A person the quest says to
fight being built unable to fight is not ruled out: see "Not ruled out", 4.

**g. Calm exploration music the whole time.**
Cause: nothing in the build changes the music. There is no music record or call in MainQuest.cs, QuestKit.cs or
ARG_QF_MQ01.psc. The record's drama was in `startScene: scene.mq01.strike`, which was cut (MainQuest.cs:16-17). The
cutters are unaggressive (f), so combat music never starts. The region's ordinary music played, as it would.
Class: **the atmosphere was promised by the text and not made by any record.** This is a symptom of b.
Why the checks passed: nothing checks mood. Nothing should.
Ruled out by: the ceiling cuts music, and rule 4 stops the journal promising a drama the world does not stage.

**h. After swimming round the sunken hut, "Bring Deesh-Duun to the shore west of the camp" appeared late.**
Cause: the yurt `Hut1` (4900,-5800) stands inside `ARG_MQ01_ZoneHuts` (x 4550 to 5150, y -6000 to -5400). Swimming
round it entered the box, which set 42 (e). Fragment_42 kills Sal-Sei out of sight, switches the shed's box off,
starts Deesh-Duun's follow package and shows the objective (psc:188-198, 211-217). The objective is late because the
box, not Deesh-Duun, carries the stage.
Class: **a stage set by position (a walk-in area entered by chance).**
Why the checks passed: questcheck's `zones` rule only refuses two overlapping consecutive zones (QuestCheck.cs:15).
Ruled out by: the ceiling (walking into an area moves no stage), and rule 4.

**i. At the shore people suddenly appeared, the journal jumped to the sunk fish trap and the sap, and the hut became a
house.**
Cause: `ARG_MQ01_ZoneShore91` (000E7F, at the shore marker, prerequisite 42) sets 91. Fragment_91 calls `Ending`
(psc:222-239), which in the same instant:
- turns on `CampAftermath` (the yurts off, the Whiterun ruin on: a);
- turns on `SurvivorsParent`, so Ri'Sakka, Tsanji and Llarvi Maryon (000E6C to 000E6E) appear about 150 units from
  the player;
- turns on Ties-The-Loose-Plank (000E6B);
- moves Deesh-Duun to the shore marker;
- calls `NextQuest.SetStage(10)` on MQ03 (psc:237).

MQ03's Fragment_10 then turns on `ARG_MQ03_JarParent` (the sap, the sunk fish trap, the picks) and
`ARG_MQ03_ReedParent` (the officer and the stranger, 000EAF and 000EB0, about 150 units from the shore marker)
(ARG_QF_MQ03.psc:51-58). It also shows MQ03's journal 10 ("Two strangers on the shore...") and its sap and
fish-trap objectives. The player stands inside the shore box, so every one of these is switched on in view.
Class: **things and people switched on in view; one quest's ending starting the next quest's world at once.**
Why the checks passed: no check measures the distance from an enable or disable to where the player must be. Each
read-back checks that the enable parent exists and is wired as the record says.
Ruled out by: the ceiling's "switch on or off **away from the player** (another cell, or out of sight by distance,
checked from the positions)", and rule 4 for MQ03's journal. How sure that check can be is not settled: see "Not ruled
out", 1.

## Not ruled out by the plan

These are the classes the plan's ceiling and quest form leave open, each with the smallest rule or check that closes it.

1. **"Away from the player" cannot be checked for every trigger.** The player's position at a result is known only when
   a line (the speaker's position), a take or a use (the thing's) moves the stage. For a death or another quest's
   stage, the player can be anywhere, so "out of sight by distance, checked from the positions" has no position to
   check from. Smallest rule: a switch on or off may be the result only of a line, a take or a use, and only for a ref
   in an interior the player is not in at that moment, or in an exterior more than the loaded grid (about 3 cells,
   12,288 units) from the speaker or thing. The form check refuses it on a death or a quest-stage trigger.
2. **A line may say where the speaker is, or what is happening round them, and be false.** Deesh-Duun's line passed every
   check. Smallest check: the quest form holds every person's one standing place. Quest-review reads each line against
   that place and the stage's state. The paper game's "look around" shows who stands where, so a playtester meets the
   contradiction. This is a review step, not a gate rule.
3. **An objective's words and its target can differ from the act that completes it.** "Reach Deesh-Duun" was completed by
   a box in the water. Smallest gate rule (form check): every objective's completing stage is set by a trigger whose
   subject is one of the objective's targets. That subject is the speaker of the line, the thing taken or used, or the
   person who dies.
4. **A person the quest expects the player to fight may be built unable to fight.** The kit's default is Unaggressive.
   Smallest rule: the form marks a person `hostile` when a death trigger or an objective asks the player to fight them.
   The generic builder sets aggression and faction from that mark, and the designed-against-built comparison reads it
   back.
5. **A thing placed "on a read surface" can still sit inside BM&V's own geometry.** placecheck checks an object's
   bottom, not its sides (PlaceCheck.cs:17-19). Smallest check: placecheck fails any thing of ours whose bounds cross a
   static or furniture of the load order by more than a few units, floors excepted. It also fails any base whose model
   path lies under a Nordic set (`WhiteRun`, `Windhelm`, `Nordic`) (decision 0006).

## Appendix: every world edit the built opening makes

Form ids are Argonia.esp unless named. Positions are x, y, z in BlackMarsh (23D689) or the hold (0F9178). "Parent" is
the enable parent (opp = opposite state). The rebuild confirms each is gone or, for the hold, kept on purpose.

| Form id | Editor id / what | Where |
|---|---|---|
| 0F9178:Black Marsh.esm | hold cell override: location 'Dainty Sload' cleared (we.mq01.hold-location) | barge hold |
| 0F92EC:Black Marsh.esm | stair door override: teleport to the pier door 005AB4, locked with no key | hold |
| 0F9399:Black Marsh.esm | far door override: teleport removed | hold |
| 005AB4:Black Marsh.esm | pier door override: teleport to the stair door | 5688,-9382,178 |
| 000E48 | ARG_MQ01_StartMarker | hold 2750,3900,7010 |
| 000E49, 000E4A | ARG_MQ01_HoldParent, ARG_MQ01_CrewParent (markers) | hold |
| 000E4B, 000E4C | ARG_MQ01_WuleenSeiRef, ARG_MQ01_UxXeekRef (parent CrewParent) | hold |
| 000E4D to 000E51 | Dives, Finds, Ri'Sakka, Tsanji, Llarvi Maryon hold refs (parent HoldParent) | hold |
| 000E52, 000E53 | ARG_MQ01_BrokerParent, ARG_MQ01_MarchParent (off at start) | pier, -300 |
| 000E54 | ARG_MQ01_BuysTheMonthsRef (parent BrokerParent) | 5360,-7485 |
| 000E55 | ARG_MQ01_MeeTujaRef (no parent) | 5344,-7330 |
| 000E56 to 000E59 | Wuleen-Sei, Ux-Xeek, Dives, Finds march refs (parent MarchParent) | plank's foot 5280-5405,-7805 to -7901 |
| 000E5A to 000E5F | CampOrderly, CampAttacked, CampAftermath, CellParent, SurvivorsParent (off), Shore93Parent (on) | under the fire, -242 |
| 000E60 to 000E64 | Fire, Shed, Huts, Shore, WaterEdge markers | camp |
| 000E65, 000E66 | ARG_MQ01_SalSeiRef, ARG_MQ01_DeeshDuunRef | 5844,-4483; 5700,-4786 |
| 000E67 | ARG_MQ01_NeshNeelRef (parent CampOrderly) | 6101,-4444 |
| 000E68 | ARG_MQ01_CutsTheOldKnotRef (parent CellParent) | 5628,-4417 |
| 000E69, 000E6A | ARG_MQ01_RootCutter1Ref, 2Ref (parent CellParent) | 6225,-4684; 6263,-4535 |
| 000E6B | ARG_MQ01_TiesTheLoosePlankRef (off at start) | 4429,-4359 |
| 000E6C to 000E6E | Ri'Sakka, Tsanji, Llarvi Maryon shore refs (parent SurvivorsParent) | shore |
| 000E6F | ARG_MQ01_Campfire, Campfire01Burning 035F49 (parent Aftermath, opp) | 5891,-4716,58 |
| 000E70 | ARG_MQ01_Shed, 01shed 0A013F:Black Marsh.esm | 6210,-4390 |
| 000E71 | ARG_MQ01_Cutting, 01swamptreecoolmoss 1B32E5, scale 0.15 | 6100,-4300 |
| 000E72, 000E73 | ARG_MQ01_Hut1, Hut2, Ashlander yurts 0AA5F0, 0AA5F2 (parent Aftermath, opp) | 4900,-5800,0; 4750,-5900,0 |
| 000E74 | ARG_MQ01_HutBurnt, WRHouseShack01Destroyed 0D8589 (parent Aftermath) | 4900,-6000,0 |
| 000E75 | ARG_MQ01_Planks, BYOHFishDock01 0008CB:HearthFires.esm, rotated 90 degrees, no parent | 4900,-5450,0 |
| 000E76, 000E77 | ARG_MQ01_HutFire1, HutFire2, Campfire01Burning (parent CampAttacked) | in the yurts, z 97 |
| 000E78 to 000E7A | ARG_MQ01_Egg9, Egg10, Egg11, 01egg 17BF06 | by the shed |
| 000E7B to 000E80 | zones: Fire (32 to 40), Shed (40 to 41), Huts (40 to 42), Shore90, Shore91, Shore93 (parent Shore93Parent) | camp and shore |
| 03B21E:Black Marsh.esm; 0BCC51, 0F0F3E:Valenwood.esp | quest overrides: Start Game Enabled cleared (01Captain, 0MainQuest1, AANEWQuestM) | records |
| 03372B:Skyrim.esm | MQ101 override: starts ARG_MQ01 | record |

Base and other records of MQ01 (all to go with it): quest ARG_MQ01 000E2D. NPC bases 000E2F to 000E41 (19:
WuleenSei and March, UxXeek and March, BuysTheMonths, MeeTuja, DivesWithoutARope and March, FindsTheOtherBank and
March, RiSakka, Tsanji, LlarviMaryon, NeshNeel, SalSei, DeeshDuun, TiesTheLoosePlank, CutsTheOldKnot, RootCutter).
Faction ARG_UnboundRoot 000E42. Weapon ARG_MQ01_SalReedKnife 000E43. Globals 000E44 to 000E47. Packages 000E81 to
000E84 (MarchOff, LeaderLeaves, SalSeiFollows, DeeshDuunFollows). Topics ARG_MQ01_TheRoll, AnswerName, AnswerSilent,
AnswerDefy, TheHire, TheMarch, Strike (000E86 to 000E95). The MQ01-gated INFOs of `ARG_Talk_Quest*` built from
`quest_people.json` (for example 000F07). MQ03's refs at the same camp (000EA6 to 000EB0: JarParent, ReedParent, the sap,
the fish trap, five lockpicks, the officer and the stranger) stand in the opening's footprint and go with it or move.
The hold's 0F920A (initially disabled) is the slice clean-up's, not MQ01's.
