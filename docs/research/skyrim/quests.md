# Journal: quests as data (chunks 1.4, 2.12 §a)

How a quest record becomes a playing quest, what each generated piece does, and where it fails on purpose, so a
later quest lane starts from the shape LF83 proved.

## 2026-10-30: the generator's first rung (lane 1.4-generator)

**The pipeline.** `tools/argonia_world/quest_gen.py` reads a quest's rows through `quest_record.export` and derives
three outputs, all regenerated and never edited. The quests in the game are listed in `quest_gen.QUESTS`; 1.4 has
only LF83 there.
- **The QUST** is an intermediate record (layer `quest:<code>`), written by `tools/ArgoniaGen/QuestRecords.cs`. It
  holds stage 0 (`StartUpStage`, the generator's own) and one stage per record stage, each with one log entry: the
  stage's `journal_text`. Ending stages carry `CompleteQuest` or `FailQuest`. Objectives get index stage + ord and
  their `objective_text`, and never any target data; QuestRecords.cs refuses a `targets` key. There is one Optional
  reference alias per cast member and thing, never Essential or Protected (old 0138). The quest is
  `StartGameEnabled, RunOnce`, its priority comes from the tier (`PRIORITY_BY_TIER`), and `ARG_QF_<code>` is
  attached with a fragment per stage.
- **The begin fragments** (`papyrus/generated/ARG_QF_<code>.psc`) do only engine work and action calls. Stage 0
  calls `ArgoniaCore.WatchQuest(self)`. Every other stage calls `ArgoniaCore.AddJournalEntry(self, stage, kind)`,
  `SetObjectiveDisplayed` for its own objectives, and one native per onEnter action. An ending stage also runs its
  ending's world and reward actions, then `CompleteAllObjectives`/`FailAllObjectives` and `UnwatchQuest`.
  There are no If statements (the records check refuses one). Compiled later on the game machine by the CK's compiler.
- **The stage graph** (`skse/core/generated/argonia/core/quests.h`) lists each stage's edges, fail-forwards first,
  as `conditions::Pred` trees. It also holds the objectives' completion trees and `startWhen`.
  `quest_runtime::step(graph, {stage, done}, facts)` returns the objectives to complete, then the stage to set.
  It answers the quest's own `objectiveComplete` from what is done, and an unanswered fact never holds. ArgoniaCore
  calls SetObjectiveCompleted and SetStage. Planner ruling: no stage-graph logic in Papyrus.

**Native rule.** Action `fooBar` maps to `ArgoniaCore.FooBar`: ids are String, counts Int, flags Bool. The quest's
own setStage is Papyrus's SetStage. LF83 calls these: WatchQuest(Quest), UnwatchQuest(Quest),
AddJournalEntry(Quest, Int, Int), GrantTopic(String), SetFlag(String, Bool), ApplyLocalVariant(String, String),
SetPrice(String, Int), GiveItem(String, Int), ChangeDisposition(String, Int), ChangeSettlementStanding(String, Int).
None is declared in `skse/ArgoniaCore/papyrus/ArgoniaCore.psc` yet, so the fragments do not compile until they are.

**QSTA** (`quest_state`): flags, counters, and deeds per faction and class. Each key is a world id hashed with FNV-1a
32, so no table order is needed; `quest_gen.check_state_keys` refuses a collision among the ids in use.

**Checks.** `quest_gen --check` (and `test_quest_gen.py`) covers these: outputs current; no objective target and no
visible map marker, in the intermediate and in the Spriggit YAML; no placeholder text; no protected alias; tier
protection (a breaking action must write an id in `touches`, and no quest of a higher tier may touch or cast that
id); the generated graph walks as the record does. Each rule is made to fail once in the tests.

**Gotchas.** `quests.h` needs fully qualified `::argonia::core::...` names because it sits in namespace `gen`.
Stage indices must be at least ten apart, and a stage may hold at most nine objectives (index = stage + ord).
Unfilled aliases must be Optional, or the start-enabled quest will not start.
