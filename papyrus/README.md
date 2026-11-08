# papyrus

Our Papyrus scripts: quest-stage fragments, alias and trigger scripts, and the glue a record cannot do
(PLAN Phase 3 settles the shapes). Compiled on the play machine by
`infra/gpu-box/records_jobs.sh papyrus` (the Creation Kit's compiler against its `Scripts.zip`, never committed);
the `.pex` files are build outputs and are sent by `infra/gpu-box/deploy.sh`.

| Script | What it does |
|---|---|
| `ARG_QF_MQ101.psc` | MQ101's fragment script in `Argonia.esp`'s MQ101 override: the engine starts MQ101 on a new game; stage 0 starts `ARG_Opening` and stops MQ101 (no Helgen) |
| `ARG_StartQuestScript.psc` | `ARG_Opening`'s script: the player to `ARG_OpeningMarker` on Lilmoth's dock, the race menu, the roughspun tunic and footwraps, stage 10's journal line (PLAN Phase 1, the start) |
| `ARG_QF_BlockTest.psc` | Phase 3's test quest `ARG_BlockTest`: the stage fragments, every effect block once (docs/phases/3-building-blocks.md); removed after the owner's walk |
| `ARG_QF_BlockTestEnd.psc` | the second test quest `ARG_BlockTestEnd`'s stage 100: `IncSideQuests()` and `Stop()`, as vanilla side quests end |
| `TIF_ARG_BT_20/40/50/90.psc` | the test quest's keeper lines: `GetOwningQuest().SetStage(n)` at the line's end (TR-topic) |
| `SF_ARG_BT_Scene.psc` | the test scene's end fragment: stage 60 (TR-scene) |
| `ARG_QF_TG01.psc`, `ARG_QF_TG02.psc` | the Night-Reed quests TG01 and TG02 (`tools/ArgoniaPlugin/NightReed.cs`): stage fragments and the helpers their lines call (pay, hand-overs, the guarded all-three checks) |
| `generated/TIF_ARG_TG0*.psc` | their lines' end fragments, written by the seed from NightReed.cs (one call each) |
| `ARG_QF_MQ01.psc`, `ARG_QF_MQ03.psc` | the opening act's MQ01 (character creation, then the hold, the march, the strike, the choice) and MQ03 (the dawn camp, the Reed's house, the dream), `tools/ArgoniaPlugin/MainQuest.cs`; MQ101 now starts `ARG_MQ01` |
| `generated/TIF_ARG_MQ0*.psc` | their lines' end fragments, written by the seed from MainQuest.cs |
