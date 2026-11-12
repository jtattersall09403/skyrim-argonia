# The quest form

A quest is data only: one JSON file per quest in one fixed form, `tools/questform/schema.json` (version 1). The
form has no place for a scene, a walk, an area to walk into, a timer or a script, so a quest above the ceiling cannot
be written in it. The generic builder turns a form into plugin records; the plugin reader turns the built plugin back
into a form; the paper game plays a form. Every field not listed here is refused (`additionalProperties: false`
throughout). Ids, form keys, editor ids and positions are plain strings and numbers.

## The fields

| Field | Holds |
|---|---|
| `version` | `1` |
| `quest` | `id` (the record's quest id), `editor_id` (`ARG_<code>`), `name`, `kind` (its line: `main`, `faction` for a faction's quest line, `minor` for any other; compiled from the record's group), `start`: `{by: game, stage}` (running from a new game at that stage) or `{by: quest_stage, quest, quest_stage, stage}` (set to `stage` when that quest's stage is set) |
| `stages[]` | `number` (0 to 255); `shown` (it shows in the journal); `journal` (its text, or null when not shown); `ending`: `none`, `completed` or `failed`; `results` (applied as the stage begins) |
| `objectives[]` | `number`, `text`, `shown_at` and `completed_at` (stage numbers), `targets` (one or more ref ids: the marker points at each) |
| `refs[]` | every person, thing, door or marker the quest names: `id`, `kind` (`person`, `thing`, `door`, `marker`), `placement`, `enabled` (on at the start), `hostile` (a person the quest asks the player to fight: the builder sets aggression from it), `at` (where it stands: `cell`, `interior`, `x`, `y`, `z`) |
| `placement` | `{existing: <form key>}`, or a new placement `{base: {kind, id}, anchor}` with `kind` `template_person`, `item` or `existing_base`, and `anchor` `{near: <existing reference's form key>, rule}` or `{place: <census place id>, rule}`, `rule` `surface` or `navmesh` (the builder resolves the exact spot); a thing may instead sit in `container` (another thing's ref id) |
| `lines[]` | `id`, `speaker` (ref id), `kind` (`greeting`, `topic`, `answer`, `speaks_first`), `prompt` (the player's words; null for a greeting or speaks-first), `text` (the spoken words, or the gist when `written` is false), `conditions`, `results`, `first_stage`, `last_stage`, `answers` (for a question: its answer lines' ids). Lines of one speaker are tried in order: the first whose conditions hold is said |
| `triggers[]` | `id`, `kind` (`take`, `use`, `death`: with `ref`; `quest_stage`: with `quest`, `quest_stage`), `prerequisite`, `sets`; a death may carry `choice: true` (killing them is the player's choice) |
| `must_live[]` | `ref`, `fail_stage` (a failed ending), `main_message` (the death also shows the main quest's message once: only on a main or faction quest, where it is true; a minor quest's death only fails it); the builder makes the quest's start check they are alive |

A **speaks-first** line is the one package a quest has: the person stands where `at` says, walks up and says it.
The form says nothing more about it.

**Windows.** A line is open at every stage numbered from its first stage to its last. A trigger is open from its
prerequisite up to, not including, the stage it sets. An objective is active at a stage it is shown at and not
completed at.

## The vocabularies

**Conditions** (`is`; all of a line's conditions must hold, nothing is negated):
`stage_is`, `stage_at_least`, `stage_done` {quest, stage}; `number_compare` {number, op (`=`, `!=`, `<`, `<=`, `>`,
`>=`), value}; `in_faction` {faction}; `rank_at_least` {faction, rank}; `item_count_at_least` {item, count};
`gold_at_least` {gold}; `skill_at_least` {skill, value}; `alive`, `dead`, `speaker_is` {ref}; `regard_at_least`
{ref, value}; `race_is`, `sex_is` {value} (the player's); `spoken_before`, `not_spoken_before` (the speaker to the
player).

**Results** (`do`): `set_stage` {stage} (this quest); `give_item`, `take_item` {item, count}; `give_gold`,
`take_gold` {amount}; `set_number`, `add_number` {number, value} (a stored number: a flag, a counter, a standing, a
quest's own liking); `join_faction` {faction}; `set_rank` {faction, rank}; `change_regard` {ref, by};
`switch_on`, `switch_off` {ref}; `lock_door`, `unlock_door` {ref}; `show_message` {text}; `speaker_hostile` (a
line's only: the speaker attacks); `start_quest` {quest, stage}.

## The rules

`python3 -m tools.questform check <file...>` runs the schema and then each rule (`tools/questform/rules.py`); each
failure is one line naming its rule.

| Rule | Fails when |
|---|---|
| `schema`, `vocabulary` | a field is missing, of the wrong type or not in the form; a condition or result word is not in its vocabulary; `speaker_hostile` is a stage's result |
| `unique-ids` | two stages, objectives, refs, lines, triggers or who-must-live rows share an id |
| `stages-exist`, `refs-exist` | a stage or ref named anywhere is not in the form; an answer is not a line; a locked door is not a door |
| `placement` | a new placement has neither or both of an anchor and a container; a container holds a non-thing |
| `journal-text` | a shown stage has no journal text; an ending does not show |
| `way-out` | a stage that is not an ending has no line, trigger or result that moves the quest on |
| `reachable` | a stage cannot be reached from the start (a who-must-live death reaches its failed ending) |
| `objective-target-on` | a shown stage that is not an ending has no active objective with a target switched on at it |
| `asked-is-target` | a thing to take or use is not a target at its prerequisite stage; a person whose line moves the quest is not a target at that stage |
| `completes-on-target` | the line or trigger that completes an objective concerns none of its targets |
| `hand-in` | a line that takes a thing is not gated on holding it, or is not open from the stage a take trigger of that thing opens to the stage the trigger sets (holding it early still works; the take moves only an in-between stage) |
| `line-window` | a first stage is after the last; a line offered before the first ending stays open into it |
| `switch-cause` | a stage that switches a reference can be set by a death, another quest's stage, the start or another stage (the player could be anywhere) |
| `away` | a switched reference is in the same cell as the speaker or the taken or used thing, or, both outdoors, under `AWAY_UNITS` (18,000) from it; a position is missing (another interior, or across the interior/exterior line, is away) |
| `result-limits` | the stages hold more than `MAX_STAGE_RESULTS` (128) results in all, or a line more than `MAX_LINE_RESULTS` (128) |
| `must-live-fails` | a who-must-live row's stage is not a failed ending |
| `main-message` | a minor quest's who-must-live row shows the message |
| `death-hostile` | a death trigger names a person neither hostile nor who-must-live, and the kill is not marked the player's choice |
| `speaks-first-has-line` | a speaks-first line has no topic or greeting line with the same speaker, words, results and window |

## Compiling a quest record

`python3 -m tools.questform compile <quest id...> [--out dir]` (or `--all`; default `out/questform`) reads the quest
record (`quest_record export`) and writes its form, or prints each refused term with where it stands and a re-author
hint.

| Record | Form |
|---|---|
| `startWhen` a topic or a take | `{by: game, stage: 0}`, a hidden stage 0, and the line or trigger that sets `start` |
| `startWhen` another quest's stage; or no `startWhen` and another quest's `setStage` of it | `{by: quest_stage}` |
| no `startWhen`, a `start`, nothing that starts it | `{by: game, stage: start}` |
| stage `journalText`, `hidden`, `ending`; its `onEnter` and its ending's `world` and `rewards` | stage `journal`, `shown`, `ending`, `results` |
| objective `objectiveText`, `target`; the stage's successors | objective `text`, `targets`, `shown_at`, `completed_at` |
| successor or fail-forward `topicHeardFrom` (with gates under `all`) | a line at that stage that sets the stage |
| `hasItem`; `not npcAlive`; `questStage`/`stageEverReached`; a `flag` a `thing_hook` sets | take, death, quest-stage, use trigger |
| `not npcAlive` to a failed ending | a who-must-live row (`main_message` for the main and faction groups) |
| `objectiveComplete` | the objective's own completion test |
| gates: `questStage`, `stageEverReached`, `flag`, `counterAtLeast`, standings, `factionRankAtLeast`, `hasItem`, `goldAtLeast`, `skillAtLeast`, `npcAlive`, `dispositionAtLeast`, `raceIs`, `sexIs` | the matching condition |
| `setFlag`, `addCounter`, `changeStanding`, `changeSettlementStanding` | `set_number`, `add_number` |
| `changeDisposition`, `enableRef`/`disableRef`, `setDoorAccess`, `give`/`take` `Item`/`Gold`, `setFactionRank`, `setStage` | `change_regard`, `switch_on`/`off`, `lock_door`/`unlock_door`, the item and gold results, `set_rank`, `set_stage` or `start_quest` |
| `grantTopic`, `removeTopic` | dropped: a line's window opens and closes it |
| the record's `topics` (`kind` greeting or speaks-first; an answer is a reply of a written question) | lines; words from `story/data/quest_lines/<code>.json`, else the written `dialogue_line` rows, else the `intent` as a gist |
| the record's `placements` | `refs` (an existing actor's `at` from `bmv_placement`) |

Refused, each with its hint: walking into or standing in a place (`inZone`, `inSettlement`, `inCell`, `inRegion`,
`discovered`); the clock (`timeOfDay`, `daysSince`, dates, seasons, weather, tide, `startTimer`); being seen
(`detectedBy`, `seenBy`, `witnessed`, `recordWitnessed`); scenes (`sceneEnded`, `startScene`); people walked or
moved (`npcAtMark`, `setSchedule`, `moveRef`, the player included); `knowsTopic`; `placeCleared`; local variants;
an `any` or a `not` as a gate; an `all` around a trigger; a flag moving a stage; any other term; and missing data:
`placement` (a named ref without a placements row), `objective target`, `objective text`, `start`, `death both
ways` (a death that both fails and moves the quest).

## The gate

`make check` runs the form's unit tests and `python3 -m tools.questform gate`: the example
(`tools/questform/examples/opening.json`) passes, and every quest record with stages is compiled and checked against
`story/data/questform_owed.json`, which lists each quest that does not fit with its refused terms (a failed rule is
`check:<rule>`). The gate fails on a quest that does not fit and is not listed, on a listed quest that now fits, and
on a listed quest whose terms changed. The list only shrinks: `python3 -m tools.questform owed --write` rewrites the
listed quests' terms and never adds a quest.

To fit a quest: re-author its record to the ceiling (quest-write), add a `placements` row for every person, thing,
door and marker it names, give every objective its words and its target, run `compile`, then `owed --write`.
