# The block set: the quest form's vocabulary

A quest is data in one fixed form ([quest-form](quest-form.md)); the blocks are the words that form may use. Each
block has one engine shape, made by the one generic builder (`tools/ArgoniaPlugin/QuestForm.cs`) from one of three
things: our generic scripts (`papyrus/ARG_QuestStages.psc`, `ARG_Effects.psc`, `ARG_LineEffects.psc`,
`ARG_AliasEffects.psc`), Skyrim's own default scripts, or the one force-greet package. Each block's Skyrim precedent
is counted in Skyrim.esm where [quest-block-precedent](../research/skyrim/quest-block-precedent.md) or
[quest-form-engine-facts](../research/skyrim/quest-form-engine-facts.md) gives it (decision 0034).

Because every quest is built from the same blocks by the same builder, a block proven once in game is proven for every
quest. The block test (`tools/questform/blocktest/`, two forms that use every trigger, condition and result) is built
by every seed, read back, compared with its forms, and walked once in game by the owner. A quest needing anything
outside these blocks is rewritten (the dramatic jobs table in
[principles/general.md](../../.claude/skills/quest-write/principles/general.md)); a new block is a change to the
form, the builder, the reader, the paper game and the block test together, proven once by an owner check.

## Triggers: what moves a stage

| Block (form) | Engine shape | Skyrim precedent |
|---|---|---|
| a line (`lines[]` with a `set_stage` result): a topic, an answer, a greeting | a topic and its responses with the speaker, the stage window and the form's conditions; `ARG_LineEffects` on each response runs the line's rows as it ends | 5,540 INFOs with a fragment, in 475 quests |
| an answer to a question (`answer`) | a topic in the question's own branch, the question's response linking to it | Skyrim's question-and-answer pairs |
| taking a thing (`take`) | `defaultSetStageOnPlayerAcquire` on the thing's alias; a second take of a placed thing: `defaultSetStageOnPlayerAcquireItem` on the reference; a thing held before the take opens: the prerequisite stage's IfHolds then SetStage | 16 quests |
| using or reading a thing (`use`) | `defaultSetStageOnCloseBook` for a book, else `defaultSetStageAliasScript` (activate) on the alias | 119 quests use the alias set-stage family; 6 read-book set-stage |
| a death (`death`) | `defaultSetStageOnDeathRefAlias` on the person's alias; with `until`, `ARG_AliasEffects` with the window's guards | 20 quests |
| another quest's stage (`quest_stage`) | two rows on that quest's stage: IfStageDone (prerequisite), SetStageIfRunning | 86 quests read another quest's stage; 1,596 INFOs do |
| a person speaking first (`speaks_first`) | the quest's one package, a copy of vanilla's `MS05InductionForcegreet` (template ForceGreet), held while the line's window is open, plus the same line under the quest's Hello | 302 packages use the ForceGreet template, 214 of them alias packages in 124 quests |

## Conditions: what gates a line or a stage

All are conditions on the response (or the start check's rows); `not` inverts the comparison.

| Block (form) | Function | Uses in Skyrim.esm (QUST, INFO, PACK, SCEN) |
|---|---|---|
| `stage_is`, `stage_at_least`, `stage_done` | GetStage, GetStageDone | 8,029 / 4,175 |
| `number_compare` | GetGlobalValue on one of our globals (`ARG_N_<id>`) | 1,579 |
| `in_faction`, `rank_at_least` | GetInFaction, GetFactionRank | 6,904 / 259 |
| `item_count_at_least`, `gold_at_least` | GetItemCount (gold as Gold001) | 678 |
| `skill_at_least` | GetActorValue on the skill | 150 on skills |
| `alive`, `dead` | GetDead | 1,028 |
| `speaker_is` | GetIsReference on the placed person (every line also carries its speaker this way) | GetIsID: 19,169 uses |
| `regard_at_least` | GetRelationshipRank with the player (-4 to 4) | not counted |
| `race_is`, `sex_is` | GetIsRace, GetIsSex on the player | not counted |
| `spoken_before`, `not_spoken_before` | GetTalkedToPC | not counted |

## Results: what a line or a stage does

Every result is a row (`Op`, `What`, `Num`) that `ARG_Effects.Run` carries out; the numbered list is in
[quest-form](quest-form.md) "The operations". Each operation is safe to repeat.

| Block (form) | Operation | Skyrim precedent |
|---|---|---|
| the next stage, its journal entry, its objectives with targets | the stage's log entry; SetStage, ShowObjective, CompleteObjective, SetActive; objectives target a forced-reference alias | 726 log stages in 203 quests; 1,452 objectives in 396 quests, each on an alias |
| an ending | the stage's Complete Quest or Fail Quest flag; CompleteAll or FailAll, IncSideQuests for a completed side or faction quest, Stop last | QF_dunVolunruudQST: SetObjectiveCompleted, IncSideQuests, Stop; 21 of 23 completing side quests count the stat |
| `give_item`, `take_item`, `give_gold`, `take_gold` | AddItem, RemoveItem on the player | every vanilla reward |
| `set_number`, `add_number` | a global's SetValue, Mod | backs the 1,579 GetGlobalValue uses |
| `join_faction`, `set_rank` | AddToFaction, SetFactionRank | 1,215 alias factions in 140 quests |
| `change_regard` | SetRelationshipRank with the player | the favour quests' death scripts (46 quests) |
| `switch_on`, `switch_off` (away from the player) | Enable, Disable on a persistent reference | 4,072 placements start disabled |
| `lock_door`, `unlock_door` | Lock, Unlock on the door | 762 locked door refs, 398 naming a key; 43 quests' scripts take a locked door or key |
| `give_ownership` | the container's owner set to the player | not counted |
| `teach_spell`, `forget_spell` | AddSpell, RemoveSpell on the player, of our copy of a load-order spell under our name | the Nightingale and Black Book powers, the standing stones; Morrowind's AddSpell (the Corprus cure) |
| `make_enemy`, `make_peace` | the faction's SetPlayerEnemy | the civil war's sides; Morrowind's SetPCFacRep and hostile houses |
| `leave_faction` | RemoveFromFaction on the player | expulsion from a guild (Morrowind's PCExpell) |
| `show_message` | a message box of ours, `Show()` | DA06FailMessage from QF_DA06 |
| `start_quest` | Start, then SetStage | a chained quest started at its first stage |
| `speaker_hostile` (a line's only) | the speaker attacks the player | common in Morrowind (the smuggler who draws a blade when refused) |

## World edits: what a quest may place

| Block (form) | Record shape | Skyrim precedent |
|---|---|---|
| a person or creature of ours (`template_person`) | our base templated on a load-order base, with the ref's name and a fixed level; placed persistent at a measured spot; a `hostile` one takes aggressive AI | 3,651 of 5,118 NPC_ have a template; 4,664 are fixed level |
| an existing person, thing or door (`existing`) | made persistent in our plugin with its starting state | forced-reference aliases: 2,687 in 425 quests |
| a thing of ours (`template_item`, `item`) | our item copied from a load-order item whose model reads as the thing; placed on a measured surface, in a container or carried | every vanilla quest item |
| a container's lock, key, owner, contents | the reference's lock level and key, its owner, its items | 762 locked doors; owned containers throughout |
| a door locked or unlocked | the door's lock; a door a result unlocks starts locked | as above |
| who must live; the message | `ARG_MortalWatch`, one always-running quest with an alias per person, running `ARG_AliasEffects` on the death | Morrowind's death message; DA06's failure box |
| nobody unkillable | the seed takes Essential and Protected off every base we or Black Marsh & Valenwood place, and off every alias of ours | the flags live on the base, through Use Base Data templates, and on the alias ([quest-form-engine-facts](../research/skyrim/quest-form-engine-facts.md) §3) |

Every alias is a forced reference to a persistent placed reference, never "find matching". A spot is measured, never
typed: a person on the winning navmesh (`plugin.sh inspect navnear`), a thing on the modelled surface under it
(`plugin.sh surface`, `inspect cellat`); `plugin.sh placecheck` reads every placement back.

## Where the argument could fail, and the guard for each

| Failure | Why it breaks | Guard |
|---|---|---|
| Two triggers racing for one stage | two takes, uses or deaths that set one stage can fire in one frame | stages are by done: setting a done stage does nothing, so a stage's rows run once; a trigger is open only while its prerequisite is done and its stage is not (`until` closes it at a later step), and `late-trigger` refuses one that can fire after the quest has moved past it |
| Forced persistent aliases | a forced alias whose reference is not persistent, or is in an unloaded cell, fails to fill and the quest will not start | every reference a form names is made persistent by the builder; an existing reference on an enable parent is refused; `questcheck` reads every alias back |
| Save and reload | a script running at the save is cut short; a trigger may fire again | every operation is safe to repeat; triggers carry their prerequisite, so a refire on a done stage does nothing; property values bind when the instance is made, so a changed quest needs a new game |
| A death before the quest starts | a person the quest needs, or whose death it waits for, is already dead when it starts | the start stage carries FailIfDead for each who-must-live row whose window holds it, and a death trigger open from the start adds its own start check, so the quest moves at once |
| Arrays past their limit | Papyrus arrays hold 128 entries | `result-limits` refuses a quest whose stage rows or a line's rows pass 128, counted as the builder writes them |

## How record terms map to blocks

The compiler maps every record term to the form's blocks, and refuses each term outside them, in
[quest-form](quest-form.md) "Compiling a quest record". `python3 -m tools.argonia_world.quest_record export <quest id>`
prints a quest's record; `python3 -m tools.questform compile <quest id>` shows the blocks it becomes.
