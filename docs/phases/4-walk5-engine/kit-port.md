# Brief: port every quest builder onto one QuestKit (zero-diff refactor)

Repo: /home/ubuntu/skyrim-argonia (main tree; read CLAUDE.md). Never run the game. Other lanes edit story/data,
.claude/skills and docs at the same time: touch only tools/ArgoniaPlugin/*.cs listed below.

## Goal
One quest kit: every helper the quest builders use lives in tools/ArgoniaPlugin/QuestKit.cs, with one implementation
each; the builders MainQuest.cs, LocalQuests.cs, Chainbreakers.cs, NightReed.cs, MQ04.cs, MQ05.cs call the kit and
define no helper of their own. This pass is a PURE REFACTOR: the seeded plugin must be byte-identical.

Delete from the builders (move the one surviving behaviour into QuestKit.cs):
- MainQuest.cs: `Ctx` (Base, Marker, Parent, Actor, Zone, Interior, Travel, Follow, Land), `Glob/Stage/Done/Or/Not/SpeechBelow`,
  `NewQuest`, `Topic` (with `Under`), `Objectives`, `LinesOf`, `NewShort`, `WritePsc`'s body (one kit WritePsc for every
  builder's TIF bodies), the `using static NightReed`.
- LocalQuests.cs: `Snapper`, `Kit` (Base, Marker, Actor, Persist, Pos, Zone, World), `Script/Obj/Alias/Int/C/StageIs/IsId/IsRef/Rank/Bands`,
  `Journal`, `Objectives`, `Lines`, `Rows`, `S`, `NewQuest`, `Forced`, `AliasScript`, `OnDeath`, `AfterHello`, `After`,
  `Topic/TopicV`, `Fragments`.
- Chainbreakers.cs: `Interior`, `Pack`, `Or/Hour/Speech/Has`, `Person` may stay only as a one-line call into the kit
  (better: inline), the `using static LocalQuests`.
- NightReed.cs: `Snapper`, `C/OnPlayer/StageLt/StageIs/Speech/Has/HasOn/IsId/Dead/Script/Obj/Alias/Int`, the local
  `Base/Marker/Actor/Pack/Interior/Lock` functions, `Topic`, `Stages`, `Forced`, `AliasScript`, `OnDeath`, `Written/Band`
  readers (move to the kit as line-store readers), `WritePsc`.
- MQ04.cs, MQ05.cs: already on the kit; keep them compiling against the merged kit.
Every builder constructs a `QuestKit` per quest (MQ01 and MQ03 may share one instance's snap state: see below).

## One behaviour each (how to merge without changing output)
- Navmesh snapping: one `Snap(FormKey mesh, x, y)`, `Snap(mesh, x, y, z)` (the 3-D nearest, MainQuest's hold) and
  `Snap(string cell, x, y)` (LocalQuests' cell form), all over "the last copy of each navmesh that carries data"
  (QuestKit's current rule; for every mesh the other builders name it equals the winner). The used-triangle set is
  ONE static set shared by every kit instance (today MainQuest's MQ01 and MQ03 share one Snapper; other builders snap
  on distinct meshes, so a shared set changes nothing; the diff proves it).
- Base: one `Base(id, name, tpl, level, flags, Ai ai = Ai.Template, Aggression aggression = Unaggressive)`:
  `Ai.Template` = QuestKit's current flag set (looks + AI data + packages + factions + script + def pack list);
  `Ai.Own` = MainQuest's/NightReed's (looks only: Traits, SpellList, ModelAnimation, AttackData, Keywords, Inventory;
  own AIData {aggression, Average, NoCrime, HelpsNobody}; Voice from the template). Female flag from the template
  unless a caller overrides (NightReed passes female explicitly; Chainbreakers clears it for men): keep each caller's
  output identical.
- Marker/Ref/Actor/Zone: one each, with the optional parameters the callers need (base, flags, enable parent,
  opposite, scale, rotation; Zone takes a half-size P3Float and an optional parent). Editor-id prefix: the kit's
  `prefix` (may be "" for builders that pass full ids).
- Packages: `Travel(id, to, radius, owner, conds)`, `Follow(id, owner, conds)`, `Schedule(id, fromVanillaEdid, at, radius, hour, minutes, owner, conds)`
  for NightReed's and Chainbreakers' `Pack`. Today owner-quest handling differs (MainQuest and NightReed clear it,
  QuestKit and Chainbreakers set it): keep each caller's output with an explicit parameter in this pass; the next
  pass sets it everywhere.
- Quest setup: one `Stages(...)`/`Objectives(...)` path reading story/data/db (quest_stage, quest_objective) with the
  parameters needed to reproduce each builder's output (explicit stage list or all record stages; hidden stages;
  ending stages explicit or from the record; fragments for all stages or a named list; objective index = stage +
  order within the stage). NightReed's in-code stage texts stay in NightReed.cs as data passed to the same helper.
- Topics: one Topic(id, prompt, branch-under?, infos) and one Info/Banded builder (wording bands on
  GetRelationshipRank >= 1 / < 0, default the complement, every band copying gates and fragment). The four line
  sources (quest_lines JSON, the db rows, NightReed's TSV, the after.tsv files) become kit readers. INFO form ids are
  allocated in two orders today (MainQuest and NightReed: default first, then bands; QuestKit and LocalQuests: bands
  first): keep an explicit `bandsFirst` parameter in this pass so ids do not move.
- Conditions: one static each in the kit: C, OnPlayer, StageIs(Quest q, op, s) (+ the instance shorthand), Done, Glob,
  Or, Not, Speech(op, v), Has, HasOn, IsId(FormKey), IsRef, Hour, Dead, Rank, Unseen(detected by ref).
- Scripts: Script, Obj, Alias(name, quest, id), Int, AliasScript, DeathSets/OnDeath (one), AcquireSets, ActivateSets
  (defaultSetStageAliasScript: stage, prereq, TriggerType 0), Forced (FormKey and IPlaced overloads), Persist (the
  LocalQuests Kit's), Interior/Exterior/World (Overrides.cs), Item, Global, Faction.
- Psc writing: one kit `WritePsc(dir)` writing every TIF body any builder registered, with the header line naming the
  builder file as today (the generated files must stay byte-identical).
Keep allocation order exactly (the order of every GetNextFormKey/AddNew call). Public members other files use
(MainQuest.Mq01/Mq03/StartMarker/Speakers/Lines, NightReed.Lines/Written, LocalQuests.Warden/OwnsBase/Masters/BlackMarsh2,
Chainbreakers constants, the alias-id consts, the *Check.cs readers' needs) stay reachable: grep the *Check.cs, Talk.cs,
PlaceCheck.cs, Generate.cs for what they use and keep it (as forwarding members if needed).

## Build and prove
- `tools/ArgoniaPlugin/plugin.sh seed` under `tooling/job_guard.sh run <name> -- ...` then `tooling/job_guard.sh wait <name>`
  (a seed takes a few minutes; never sleep or poll). The baseline: plugin/Argonia and papyrus/generated as committed.
- Iterate one builder at a time if that helps; the oracle is `git status --short plugin/Argonia papyrus/generated`
  (and `git diff --stat`) after each seed.

Acceptance: after a final seed, `git status --short plugin/Argonia papyrus/generated` prints nothing; `dotnet build -c Release
tools/ArgoniaPlugin` 0 errors; `grep -nE "static (ConditionFloat|ScriptEntry|ScriptObjectProperty|ScriptIntProperty|QuestAlias|QuestFragmentAlias|Quest|Package|PlacedObject|PlacedNpc|Npc|DialogTopic|DialogResponses\[?\]?|P3Float|Cell) [A-Z]" tools/ArgoniaPlugin/{MainQuest,LocalQuests,Chainbreakers,NightReed,MQ04,MQ05}.cs`
and a grep for `class Snapper|class Kit|class Ctx` there show no helper definitions (builder-specific Build/Add functions
that make that builder's records are fine). Commit with `tooling/lane_commit.sh -m "<msg>" -- tools/ArgoniaPlugin/<files>`
(also keep and commit the uncommitted `inspect aliaspack` block already in tools/ArgoniaPlugin/Inspect.cs: it is ours).
Do not commit plugin/ or papyrus/ (nothing should change there). Return at most 15 lines: the commit, the seed diff
result, the kit's public helper list (one line per group), and anything you could not merge with zero diff and why.
