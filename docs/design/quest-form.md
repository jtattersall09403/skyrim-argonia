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
| `names` | optional: the name the player sees for each item id the form names that is not a ref (a given page, a stock item), and ids the records cannot carry (a number's id, a faction's id); the reader writes them back |
| `texts` | optional: a readable item's words, by item id, for an item the form names that is not a ref (a page a line gives) |
| `places` | optional: every cell a ref stands in or a door leads to, as the player knows it: `{cell: {name, interior, entrance}}`, `entrance` an interior's outside door position. The paper game needs no other source of names |
| `quest` | `id` (the record's quest id), `editor_id` (`ARG_<code>`), `name`, `kind` (its line: `main`, `faction` for a faction's quest line, `minor` for any other; compiled from the record's group), `start`: `{by: game, stage}` (running from a new game at that stage), `{by: quest_stage, quest, quest_stage, stage}` (set to `stage` when that quest's stage is set) or `{by: start_quest, stage}` (started by another form's `start_quest` result) |
| `stages[]` | `number` (0 to 255); `shown` (it shows in the journal); `journal` (its text, or null when not shown); `ending`: `none`, `completed` or `failed`; `results` (applied as the stage begins) |
| `objectives[]` | `number`, `text`, `shown_at` and `completed_at` (stage numbers), `targets` (one or more ref ids: the marker points at each; the compiler reads a comma-separated record target as several) |
| `refs[]` | every person, thing, door or marker of the record's placements: `id`, `kind` (`person`, `thing`, `door`, `marker`), `placement`, `enabled` (on at the start), `hostile` (a person the quest asks the player to fight: the builder sets aggression from it), `lock` (`{level: novice, apprentice, adept, expert, master or key, key: <item id>}` on a container or door), `owner` (a container's: a person ref or a faction id), `contents` (a new container's exact contents, each `{item, count}`), `count` (a stock item's count in one placed reference), `level` (a new person's or creature's fixed level), `name`, `destination` and `text` (what the player sees: the ref's name, a door's destination, a readable's words; the reader writes back what is built), `at` (where it stands: `cell`, `interior`, `x`, `y`, `z`) |
| `placement` | `{existing: <form key>}`, or a new placement `{base: {kind, id}, anchor}` with `kind` `template_person` (a person or creature of ours on a template), `template_item` (a new item of ours on a template item, called by the ref's `name`), `item` (a stock item, or an item whose id is the ref's own) or `existing_base`, and `anchor` `{near: <existing reference's form key>, rule}` or `{place: <census place id>, rule}`, `rule` `surface` or `navmesh` (the builder resolves the exact spot); a thing may instead sit in `container` (another thing's ref id) or be `carried_by` a person ref |
| item ids | a condition, a result, an `if_held` and a lock's key name a unique thing (a `template_item`, or an item whose id is the ref's own) by its ref id, and a stock item by its item id; never a unique thing's base |
| `lines[]` | `id`, `speaker` (ref id), `kind` (`greeting`, `topic`, `answer`, `speaks_first`), `prompt` (the player's words; null for a greeting or speaks-first), `text` (the spoken words, or the gist when `written` is false), `conditions`, `results`, `first_stage`, `last_stage`, `answers` (for a question: its answer lines' ids). Lines of one speaker are tried in order: the first whose conditions hold is said |
| `triggers[]` | `id`, `kind` (`take`, `use`, `death`: with `ref`; `quest_stage`: with `quest`, `quest_stage`), `prerequisite`, `sets`; a death may carry `choice: true` (killing them is the player's choice) |
| `must_live[]` | `ref`, `fail_stage` (a failed ending), `main_message` (the death also shows the kind's message once: only on a main or faction quest, where it is true; a minor quest's death only fails it), optional `message` (must be the kind's own words), optional `from` and `to` (stages: the row holds only while the quest's stage is from `from` up to `to`; either may be left out; `from` is never before the quest's first shown stage); the builder makes the quest's start check they are alive when its window holds the start stage |

A **speaks-first** line is the one package a quest has: the person stands where `at` says, walks up and says it.
The form says nothing more about it.

**Windows.** A line is open at every stage numbered from its first stage to its last. A trigger is open from its
prerequisite up to, not including, the stage it sets. An objective is active at a stage it is shown at and not
completed at.

## The vocabularies

**Conditions** (`is`; all of a line's conditions must hold; any condition but `number_compare` may carry `not: true`, which turns it round: its comparison is inverted, and `number_compare` says it with its `op`):
`stage_is`, `stage_at_least`, `stage_done` {quest, stage}; `number_compare` {number, op (`=`, `!=`, `<`, `<=`, `>`,
`>=`), value}; `in_faction` {faction}; `rank_at_least` {faction, rank}; `item_count_at_least` {item, count};
`gold_at_least` {gold}; `skill_at_least` {skill, value}; `alive`, `dead`, `speaker_is` {ref}; `regard_at_least`
{ref, value}; `race_is`, `sex_is` {value} (the player's); `spoken_before`, `not_spoken_before` (the speaker to the
player).

**Results** (`do`): `set_stage` {stage} (this quest), with optional `if_held` {item} (a stage's result only: set
the stage as this stage begins if the player already holds the item); `give_item`, `take_item` {item, count}; `give_gold`,
`take_gold` {amount}; `set_number`, `add_number` {number, value} (a stored number: a flag, a counter, a standing, a
quest's own liking); `join_faction` {faction}; `set_rank` {faction, rank}; `change_regard` {ref, by};
`switch_on`, `switch_off` {ref}; `lock_door`, `unlock_door` {ref}; `show_message` {text}; `speaker_hostile` (a
line's only: the speaker attacks); `start_quest` {quest, stage}.

## The rules

`python3 -m tools.questform check <file...>` runs the schema and then each rule (`tools/questform/rules.py`); each
failure is one line naming its rule.

| Rule | Fails when |
|---|---|
| `schema`, `vocabulary` | a field is missing, of the wrong type or not in the form; a condition or result word is not in its vocabulary; `speaker_hostile` is a stage's result; `if_held` is a line's; `not` is on `number_compare` |
| `unique-ids` | two stages, objectives, refs, lines, triggers or who-must-live rows share an id |
| `stages-exist`, `refs-exist` | a stage or ref named anywhere is not in the form; an answer is not a line; a locked door is not a door |
| `placement` | a new placement has not exactly one of an anchor, a container and a carrier; a container holds a non-thing; a carried thing is not an item or its carrier not a person; a `template_item` has no `name`; a `level` is on anything but a new person; a `count` on anything but a stock item placed by an anchor |
| `lock`, `owner`, `contents` | a lock on anything but a door or a thing, or its key not an item; an owner on anything but a thing, or not a person or faction; contents on anything but a new container, or naming a ref |
| `item-id` | an item is named by a unique thing's base, or a stock thing by its ref, or a ref that is no item thing |
| `journal-text` | a shown stage has no journal text; an ending does not show |
| `way-out` | a stage that is not an ending has no line, trigger or result that moves the quest on |
| `reachable` | a stage cannot be reached from the start (a who-must-live death reaches its failed ending) |
| `objective-target-on` | a shown stage that is not an ending has no active objective with a target switched on at it |
| `asked-is-target` | a thing to take or use is not a target at its prerequisite stage; a person whose line moves the quest is not a target at that stage |
| `completes-on-target` | the line or trigger that completes an objective concerns none of its targets |
| `hand-in` | a line that takes a thing is not gated on holding it, or is not open from the stage a take trigger of that thing opens to the stage the trigger sets (holding it early still works; the take moves only an in-between stage) |
| `held-take` | a take trigger's prerequisite stage does not set the trigger's stage `if_held` its item (a thing taken before the stage began would move nothing) |
| `line-window` | a first stage is after the last; a line offered before the first ending stays open into it |
| `switch-cause` | a stage that switches a reference can be set by a death, another quest's stage, the start or another stage (the player could be anywhere) |
| `away` | a switched reference is in the same cell as the speaker or the taken or used thing, or, both outdoors, under `AWAY_UNITS` (18,000) from it; a position is missing (another interior, or across the interior/exterior line, is away) |
| `result-limits` | the stages hold more than `MAX_STAGE_RESULTS` (128) results in all, or a line more than `MAX_LINE_RESULTS` (128) |
| `must-live-fails` | a who-must-live row's stage is not a failed ending |
| `must-live-window` | a who-must-live row holds before the quest's first shown stage (its death would fail a quest the player has not begun), or its `from` is after its `to` |
| `main-message` | a minor quest's who-must-live row shows the message |
| `death-hostile` | a death trigger names a person neither hostile nor who-must-live, and the kill is not marked the player's choice |
| `speaks-first-has-line` | a speaks-first line has no topic or greeting line with the same speaker, words, results and window |

**The set.** `python3 -m tools.questform check --set <dir or forms...>` also checks the forms as the quests one game
holds (`rules.check_set`):

| Rule | Fails when |
|---|---|
| `set-start` | a quest is started more than one way (its `quest_stage` start and a `start_quest` result, or a new game and a result); a `start_quest` quest has no result that starts it, or results that can both fire in one play (more than one stage, unless each is an ending of one quest); a result starts a quest at another stage than its start |
| `set-stages` | a form names a quest that is not in the set, or a stage that quest does not have (its start, a quest-stage trigger, a stage condition, a `start_quest` result) |

## How a form becomes records

`tools/ArgoniaPlugin/QuestForm.cs` is the one builder: every form becomes the same shape of records, and no quest has
code of its own. Anything it cannot build exactly fails the build with one line naming the quest and the rule
(`questform <quest>: <rule>: <what>`); it never approximates.

**The quest.** One quest record: Run Once; type Main Quest for kind `main`, Side Quest otherwise; Start Game Enabled
when the form starts `by: game`, and that start stage carries the Start Up Stage flag; priority 50. Each stage is one log
entry: its journal text when shown, and the flag Complete Quest or Fail Quest for an ending. A form started by another
quest's stage adds a start row to that quest's stage (below), so that quest must be built from a form too.

**The aliases.** One alias per ref, named by the ref's id, in the order the form lists them. An existing or a placed ref
is a forced reference (allowed disabled when it starts off); a thing whose placement is a container is a
create-in-container alias into the container thing's alias (an item thing only, on from the start). A ref two forms name
by one id is one placement: both must state it alike, and a thing made in a container belongs to one quest. A made thing
has no reference, so no result switches or locks it and no trigger watches it.

**The placements.** An existing ref is made persistent in our plugin with its starting state (on or off); it is refused
when it hangs on an enable parent or is the wrong kind (a person must be an actor, a door a door). A new ref is a
persistent placed reference (flagged disabled when it starts off) at the spot its anchor gives:
- the spot is the form's `at` when it has one, else the anchor ref's own position (`near`); a `place` anchor needs `at`;
- a load door as the anchor of the person who speaks first (or of a ref with no `at`) means where the player comes out
  of it, a step (100 units) further on, so the spot is in
  front of the door and clear of the arrival point;
- then the rule: `navmesh` takes the centre of the nearest free triangle of the cell's navmeshes (an exterior spot also
  looks in the eight cells round it) and is refused when that is over 300 units from the spot; `surface` takes the
  modelled surface or land under the spot nearest its height;
- where there is no navmesh within 300 units, a person the player does not fight stands at the form's exact `at` and
  will not walk (the build log says so); a person the player fights, a person placed by a load door, or one with no `at`
  is refused;
- a person placed by a load door faces where the player comes out of it.

**The persons.** A new person is a base of ours (`ARG_R_<ref>_Base`) templated on the form's base with everything taken
from the template but the stats (the template's own level, automatic stats, its sex). A person the player is asked to
fight (`hostile`) takes its AI data from ours instead: very aggressive, brave, no crime, helps allies. An existing
person cannot be hostile.

**The stage rows.** The quest carries `ARG_QuestStages` (`papyrus/ARG_QuestStages.psc`), one script for every form. Its
properties:
- `Op` (ints), `What` (forms), `Num` (floats): the rows, three parallel arrays, at most 128 in all;
- `Stages` the stage numbers that have rows; `StageFrom[k]` and `StageTo[k]` the slice of rows of `Stages[k]` (from, up
  to but not including to); each such stage has a fragment that runs its slice through `ARG_Effects.Run`;
- `QuestId` and `Kind` the form's quest id and kind; `Labels` what the records cannot carry, for the reader:
  `quest=<id>`, `kind=<kind>`, `name=<kind>|<what it became>|<the form's word>` (a number, story item, faction, race,
  skill or quest id the records hold under another form), and `trigger=<id>|<kind>|<ref or quest>|...` for each
  trigger (with `choice` for a death the player chose).

A stage's rows run in this order: the who-must-live start check (the start stage only); the stage's own results; the
objectives it completes, then those it shows (the stage that shows the first objective then sets the quest active);
the rows other forms added to this stage (a quest it starts, a trigger of another form's quest on it); the ending's
closing rows (every objective completed, or failed for a failed ending; Side Quests Completed counted for a completed
minor or faction quest); and Stop, always last, on an ending.

**The operations** (`papyrus/ARG_Effects.psc` carries them out; the numbers are the script's):

| No. | Name | What | Num |
|---|---|---|---|
| 1 | SetStage | | a stage of this quest |
| 2, 3, 4 | ShowObjective, CompleteObjective, FailObjective | | an objective |
| 5, 6 | SetActive, StopQuest | | |
| 7 | IncSideQuests | Skyrim.esm's AchievementsQuest | |
| 8 | FailIfDead | a person | the failed ending (set when dead; the rest of the rows are skipped) |
| 9 | SetStageIfRunning | a quest | its stage |
| 10, 13 | IfStageDone, IfStageAtMost | a quest | a stage: guard the next row |
| 14 | IfHolds | an item | how many the player must hold: guards the next row |
| 11 | IfQuestOpen | a quest | guards the next row |
| 12, 35 | StartOnStage, StartQuest | a quest | the stage it is set to |
| 20, 21 | GiveItem, TakeItem | the item | how many |
| 22, 23 | GiveGold, TakeGold | Gold001 | how much |
| 24, 25 | SetNumber, AddNumber | the number's global | the value |
| 26, 27 | JoinFaction, SetRank | the faction | (27) the rank |
| 28 | ChangeRegard | the person | by how much |
| 29, 30 | SwitchOn, SwitchOff | the reference | |
| 31, 32 | LockDoor, UnlockDoor | the door | |
| 33 | ShowMessage | the message box | |
| 34 | SpeakerHostile | | the line's speaker attacks the player |

A `set_stage` result is row 1; the other form results are rows 20 to 35 by their word. A number is a global
(`ARG_N_<id>`), a faction (when the form gives no form key) a faction record of ours, a message a message box named by
the quest and a hash of its words. An item is a form key, a thing of the form (its base), or a story item whose first
Skyrim record (`item_asset_record`) is an item of the load order. A door that a result unlocks starts locked.

**The lines.** A line's words are split at sentence ends into responses of about 150 characters (one subtitle each).
Every response carries `ARG_LineEffects` with the line's rows (`Op`, `What`, `Num`), `Owner` (the form's quest),
`Line` (the line id) and `Written`; a line with rows runs them as it ends, except the speaks-first line, which runs
them as it begins. Every line's conditions, in this order: the speaker is the person; the quest's stage is at least the
first stage; at most the last stage; then the form's conditions (`not` inverts the comparison).
- A `topic` is a topic under its own top-level branch; lines with the same prompt share one topic and are tried in
  order. An `answer` is a topic in its question's branch, and the question's response links to it.
- A `greeting` is a Hello response of the quest.
- A `speaks_first` line is a topic in a blocking branch, plus the same line under the quest's Hello topic (so he
  also says it when spoken to), plus the quest's one force-greet package on the speaker: a copy of vanilla's
  `MS05InductionForcegreet` (template ForceGreet), held while the line's window is open, never in combat or while the
  player moves into a new space. He waits at his reference, greets a player within 500 units and walks up to 300. A quest
  has one such package, so one person speaks first. He must stand on navmesh (one standing where there is none is
  refused); placed by a load door, he must stand within the 500 units of where the player comes out of it with a walk
  over navmesh between them, and the build log prints his spot and that distance.
- A line open only after the quest ends (its window holds an ending stage) lives on `ARG_Talk`, the always-running
  quest, because a stopped quest's topics are never offered; such a line may not be open before the first ending and
  into it, and cannot speak first.

**The triggers.** Each is a vanilla script on the ref's alias, never ours:
- `take` (a thing): `defaultSetStageOnPlayerAcquire` with the prerequisite and the stage to set; and, since a thing
  already held is never acquired again, two rows at the prerequisite stage: IfHolds (the thing's base, 1), then
  SetStage (the stage the take sets);
- `use`: `defaultSetStageOnCloseBook` for a book, else `defaultSetStageAliasScript` (activation) for the thing or
  door; a made thing is taken, not used;
- `death` (a person): `defaultSetStageOnDeathRefAlias`; one open from the start also adds the start check, so a death
  before the quest began moves it as it starts;
- `quest_stage` (another form's quest): two guarded rows on that quest's stage, IfStageDone(prerequisite) then
  SetStageIfRunning(sets).

A ref carries one trigger script of a kind.

**Who must live.** Every row adds the start check (FailIfDead) while its window holds the start stage. A row without
`main_message` sets the failed ending on the person's death: with vanilla's death script from any stage, or, with a
`from` or `to`, through `ARG_AliasEffects` with the window's guards. A row with `main_message` (main or faction quest
only; a minor quest's is refused) is held by the mortal watch: `ARG_MortalWatch`, one always-running quest with an
alias per person, named `<quest>|<ref>`, running `ARG_AliasEffects` on the death: if the quest has not ended, the window
guards, the message box, the window guards again, then the failed ending if the quest runs. There are two messages, by
kind: the main quest's ("... the main story can no longer be finished ...") and a faction's ("... this faction's story
can no longer be finished ..."); a row's `message`, when given, must be its kind's own.

**Nobody essential or protected.** At the end of the seed `Mortality.Clear` takes Essential and Protected off the base
of every person placed by us or by Black Marsh & Valenwood (through Use Base Data templates) and off every alias of our
quests. `questcheck` reads it back.

**Form ids** come from `plugin/questform-formids.json` (block `questform`, `0x800000-0x8FFFFF`), by name, so adding a
quest never moves another's id: `quest:<quest>`, `ref:<ref>`, `npc:<ref>`, `dial:<quest>:<key>`,
`branch:<quest>:<key>`, `info:<quest>:<line>` (and `hello:` for the Hello copy of a speaks-first line),
`pack:<quest>:<line>`, `msg:<quest>:<hash>`, `glob:<number>`, `fac:<faction>`, `watch`, `watchmsg:<kind>`.

**How the seed gets the forms.** `plugin.sh seed` compiles every quest record that fits to `out/questform`
(`compile --all --owed-ok`) and builds those forms and `tools/questform/blocktest/*.json` (`QUESTFORM_DIRS` overrides
the directories). Every quest of ours is built from its form; no quest has a builder of its own. The first refusal
stops the seed; `plugin.sh seed --refused-ok` instead leaves each refused form out (found by a trial build on a copy of
the plugin, so a form that fails for want of it is left out too), lists them, and seeds the rest.

**Talk that points at a quest.** A talker's rumour of a quest that can start (`Talk.Rumours`, after the forms are built)
holds while the form's start window does: the quest's stage at its start (a quest started by another's stage: not past
its start, and that stage done), and every other quest's stage that each opening line (open at the start, setting a
stage) asks for. A quest's people answer "Who are you?" from the form's own lines.

**The reader and the tests.** `plugin.sh questform-read <dir>` turns every form-built quest of the built plugin back
into its form from the records alone (a record the form cannot say fails the read). `plugin.sh questform-test` seeds the
block test and the example into a scratch plugin, reads it back, compares it with the forms and runs the gate's quest
rules on it. `ArgoniaPlugin questform --selftest` (`tools/tests/test_questform_build.py`) proves each refusal on
hand-made forms with no game data.

**The refusals** (the rule named in the line): `unique`, `unique-ids` (two forms of a quest, or two refs, lines or
triggers of one id); `editor-id` (a quest of that editor id is already in the plugin); `start` (a start stage that is not a stage, or started by a quest with no form);
`vocabulary` (no such result, condition, trigger kind, line kind, op, sex or skill; `speaker_hostile` as a stage's
result; `not` on `number_compare`); `refs-exist`, `stages-exist` (a ref or a stage the form does not hold);
`placement` (wrong kind, neither or both of an anchor and a container, a spot with no navmesh within 300 units for a
person the player fights or one placed by a door, no surface, an existing ref with an enable parent); `hostile` (a hostile ref that is not a new person); `person`,
`created`, `speaker` (a person's act on a thing, or a made thing's reference used); `form-key`, `item`, `race`, `quest`
(a word that resolves to no record); `shared-ref`; `trigger`; `must-live`, `main-message`, `message`; `line-window`,
`owner`, `speaks-first` (two, after the ending, standing with no navmesh, or out of reach of the door), `answer`, `schema`; `result-limits` (over 128 rows).

## Compiling a quest record

`python3 -m tools.questform compile <quest id...> [--out dir]` (or `--all`; default `out/questform`) reads the quest
record (`quest_record export`) and writes its form, or prints each refused term with where it stands and a re-author
hint.

| Record | Form |
|---|---|
| `startWhen` a topic or a take | `{by: game, stage: 0}`, a hidden stage 0, and the line or trigger that sets `start` |
| `startWhen` another quest's stage | `{by: quest_stage}` |
| no `startWhen` and another quest's `setStage` of it | `{by: start_quest}` (that quest's stage carries the `start_quest` result) |
| no `startWhen`, a `start`, nothing that starts it | `{by: game, stage: start}` |
| stage `journalText`, `hidden`, `ending`; its `onEnter` and its ending's `world` and `rewards` | stage `journal`, `shown`, `ending`, `results` |
| objective `objectiveText`, `target` (one ref, or several separated by commas); the stage's successors | objective `text`, `targets`, `shown_at`, `completed_at` |
| successor or fail-forward `topicHeardFrom` (with gates under `all`) | a line at that stage that sets the stage, with those gates; when every line of the stage is gated and one checks skill or gold that no other line catches, the fallback line (the topic's written `fail` info, else its `fallback` gist; refused as `fallback` without one), gated on the rest of the gates; never an ungated copy |
| a topic's `when` | a gate on every line of the topic |
| `hasItem`; `not npcAlive`; `questStage`/`stageEverReached`; a `flag` a `thing_hook` sets | take, death, quest-stage, use trigger; a take also gives its prerequisite stage the result `set_stage` to the trigger's stage `if_held` the item |
| `not npcAlive` to a failed ending | a who-must-live row (`main_message` for the main and faction groups), its `from` and `to` the first and last stage whose fail-forwards name the person, `from` raised to the first shown stage; while the quest waits at a hidden start stage, every line that moves it on is gated on that person alive (a death before the quest is shown leaves it unable to start, saying nothing) |
| `hasItem`, `giveItem`, `takeItem` of a ref | the ref's item id (a unique thing's ref id, a stock thing's base); naming a unique thing's base is refused (`item id`) |
| `objectiveComplete` | the objective's own completion test |
| gates: `questStage`, `stageEverReached`, `flag`, `counterAtLeast`, standings, `factionRankAtLeast`, `hasItem`, `goldAtLeast`, `skillAtLeast`, `npcAlive`, `dispositionAtLeast`, `raceIs`, `sexIs` | the matching condition |
| `setFlag`, `addCounter`, `changeStanding`, `changeSettlementStanding` | `set_number`, `add_number` |
| `changeDisposition`, `enableRef`/`disableRef`, `setDoorAccess`, `give`/`take` `Item`/`Gold`, `setFactionRank`, `setStage` | `change_regard`, `switch_on`/`off`, `lock_door`/`unlock_door`, the item and gold results, `set_rank`, `set_stage` or `start_quest` |
| `grantTopic`, `removeTopic` | dropped: a line's window opens and closes it |
| the record's `topics` (`kind` greeting or speaks-first; an answer is a reply of a written question) | lines; words from `story/data/quest_lines/<code>.json` (a topic's `infos`, or one info written as `prompt` and `lines`; variant `main` for the line, `fail` for its fallback), else the written `dialogue_line` rows, else the `intent` as a gist |
| every row of the record's `placements` | `refs`, with its `lock`, `owner`, `count`, `level`, `carriedBy`; an existing actor's or door's `at` from the census; the `name` the player sees (the row's, else the thing's, else the cast's, else the census's) |
| the record's things' `name` and `text` for items that are not refs | `names`, `texts` |
| the cells the refs stand in and the doors lead to | `places`: the census's name (a cell's own, else its settlement's: the designed place it lands as, else BM&V's map marker, else the settlement), a row's `placeName` over it; a door into a worldspace's persistent cell is named by the grid square it opens on; refused as `place name` when nothing names it |

Refused, each with its hint: walking into or standing in a place (`inZone`, `inSettlement`, `inCell`, `inRegion`,
`discovered`); the clock (`timeOfDay`, `daysSince`, dates, seasons, weather, tide, `startTimer`); being seen
(`detectedBy`, `seenBy`, `witnessed`, `recordWitnessed`); scenes (`sceneEnded`, `startScene`); people walked or
moved (`npcAtMark`, `setSchedule`, `moveRef`, the player included); `knowsTopic`; `placeCleared`; local variants;
an `any` or a `not` as a gate; an `all` around a trigger; a flag moving a stage; any other term; and missing data:
`placement` (a named ref without a placements row), `objective target`, `objective text`, `start`, `death both
ways` (a death that both fails and moves the quest), `fallback`, `item id`, `place name`.

## The gate

`make check` runs the form's unit tests and `python3 -m tools.questform gate`: the example
(`tools/questform/examples/opening.json`) and the block test (`tools/questform/blocktest/`, also as a set) pass, the
forms of every record that fits pass as a set, and every quest record with stages is compiled and checked against
`story/data/questform_owed.json`, which lists each quest that does not fit with its refused terms (a failed rule is
`check:<rule>`). The gate fails on a quest that does not fit and is not listed, on a listed quest that now fits, and
on a listed quest whose terms changed. The list only shrinks: `python3 -m tools.questform owed --write` rewrites the
listed quests' terms and never adds a quest.

To fit a quest: re-author its record to the ceiling (quest-write), add a `placements` row for every person, thing,
door and marker it names, give every objective its words and its target, run `compile`, then `owed --write`.
