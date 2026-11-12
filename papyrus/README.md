# papyrus

Our Papyrus scripts: quest-stage fragments, alias and trigger scripts, and the glue a record cannot do
(PLAN Phase 3 settles the shapes). Compiled on the play machine by
`infra/gpu-box/records_jobs.sh papyrus` (the Creation Kit's compiler against its `Scripts.zip`, never committed);
the `.pex` files are build outputs and are sent by `infra/gpu-box/deploy.sh`.

| Script | What it does |
|---|---|
| `ARG_QF_MQ101.psc` | MQ101's fragment script in `Argonia.esp`'s MQ101 override: the engine starts MQ101 on a new game; stage 0 starts `ARG_Opening` and stops MQ101 (no Helgen); with `ArgoniaNewWorld.esm` loaded (the New World card) it instead puts the player on `ArgoniaNWStartMarker` (0x802) and calls `ANW_TravelGive.BeginNewGame()` (0x090000) |
| `ARG_StartQuestScript.psc` | `ARG_Opening`'s script: the player to `ARG_OpeningMarker` on Lilmoth's dock, the race menu, the roughspun tunic and footwraps, stage 10's journal line (PLAN Phase 1, the start) |
| `ARG_Effects.psc` | the quest form's results carried out, row by row: `Run(Op, What, Num, From, To, Quest, Speaker)`, a global function with one numbered operation per result (docs/design/quest-form.md, "How a form becomes records"); every operation is safe to repeat |
| `ARG_QuestStages.psc` | the one stage script of every form-built quest: the rows (`Op`, `What`, `Num`), `Stages`, `StageFrom`, `StageTo`, and `QuestId`, `Kind`, `Labels` for the plugin reader; a fragment per stage (0 to 255, written by a generator) runs that stage's rows |
| `ARG_LineEffects.psc` | the one response script of every form-built quest's lines: the line's rows, `Owner`, `Line`, `Written`; runs the rows as the line ends (as it begins for a speaks-first line) |
| `ARG_AliasEffects.psc` | the mortal watch's script on each person a main or faction quest cannot go on without, and on a who-must-live row with a window: on death it runs its rows once |
| `ARG_QF_TG01.psc`, `ARG_QF_TG02.psc` | the Night-Reed quests TG01 and TG02 (`tools/ArgoniaPlugin/NightReed.cs`): stage fragments and the helpers their lines call (pay, hand-overs, the guarded all-three checks) |
| `generated/TIF_ARG_TG0*.psc` | their lines' end fragments, written by the seed from NightReed.cs (one call each) |
| `ARG_QF_MQ01.psc`, `ARG_QF_MQ03.psc` | the opening act's MQ01 (character creation, then the hold, the march, the strike, the choice) and MQ03 (the dawn camp, the Reed's house, the dream), `tools/ArgoniaPlugin/MainQuest.cs`; MQ101 now starts `ARG_MQ01` |
| `generated/TIF_ARG_MQ0*.psc` | their lines' end fragments, written by the seed from MainQuest.cs |
| `ANW_TravelGive.psc`, `ANW_TravelEffect.psc`, `ANW_TravelPage.psc` | the "Argonia Travel" lesser power of `ArgoniaNewWorld.esm` (`tools/ArgoniaPlugin/NewWorldTravel.cs`): a start-game-enabled quest gives it, and on a New World new game also runs character creation and puts it on the shout button; casting it opens a message-box menu whose pages are `newworld/sources/travel/menu.json` and whose buttons open a page or `Debug.CenterOnCell` a place (a gamepad's way into the new world) |
| `TIF_ARG_BoatTravel.psc` | every boatman's travel line in the place layer (`tools/ArgoniaPlaces/Build`): one script for every boatman and destination, set by the line's properties (`Destination` marker, `Fare`); takes the fare and fast-travels, as vanilla's carriage does |
| `TIF_ARG_NoSurrender.psc` | every native-law place's resist line (`tools/ArgoniaPlaces/Build`, People.cs): the guard's `SetPlayerResistingArrest()`, then the place's guard faction (`Guards`) made the player's enemy, so its guards take no surrender (`docs/design/law.md`) |
