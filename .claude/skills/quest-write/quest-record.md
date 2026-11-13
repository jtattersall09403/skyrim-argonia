# The quest record

A quest's record is rows in the story data (`story/data`), the only source of truth for that quest: the `quest` row and its `quest_*` child tables, its facts as `fact` rows (`quest_id`, in `ord`
order), its conditions and actions as `condition*` and `action*` rows. This file describes its **YAML view**,
the form a writer edits: **the imported quest object plus the record's sections**. The object's fields are the
`quest` row's (the import's names), and the record adds the sections below them. There is no second quest
format and no second copy: `python3 -m tools.argonia_world.quest_record import QUEST.yaml` replaces the quest's
record rows with the view's (refusing the whole record on any unknown field, wrong type, dangling key, unknown
lookup value or failing named check), and `quest_record export <quest id>` rebuilds the view from the rows.
Every YAML path maps to one column or child table (`tools/argonia_world/quest_view.json`). Conditions and actions
are written only in the condition vocabulary (`condition_term` rows with their argument shapes;
`story/design/quests/85-condition-vocabulary.md` explains each); a term it lacks is added first, never written
in prose. Worked examples, exported from the rows: [examples/lh38.yaml](examples/lh38.yaml) (local),
[examples/mr01.yaml](examples/mr01.yaml) (faction).

## 1. The imported quest object (field names as in the import)

| Field | Rule (the `quest` row and its child tables) |
|---|---|
| `id`, `code`, `title` | `quest.<line-slug>.<code-lower>`, never reused; two capitals two digits; working title |
| `line`, `group`, `tier` | a `quest_line` id; its group (`main`, `faction`, `line`, `local`, `daedric`, `proposed`); 0–3, a quest may not write what a lower tier owns |
| `status` | the import's `live`, `concept`, `skeleton`, `proposed`. The record's own progress is `recordStatus` (§2) |
| `shapes` | primary first, up to two secondary, from the 16 (story/design/quests/index/README.md §47b) |
| `region`, `settlement`, `anchorPlaces` | catalogue region; a live settlement `place.` id, also in `anchorPlaces` |
| `premise` | one clause the player could say back afterwards |
| `costTier`, `milestone` | `S`/`M`/`L` (00-overview, cost tiers); 1 or 2 |
| `touches`, `sockets`, `essentialTopics`, `sources` | shared ids read or written; placed sockets; topics never gated on disposition; the docs the row came from |
| `startWhen`, `start` | optional: a condition that enters the quest at `start` (85 §D) |
| `stages` | the stage graph below |

**A stage** keeps the import's fields and adds the record's (marked +):

| Field | What it holds |
|---|---|
| `id` | 10, 20…; 90+ for endings and fail-forward |
| `place` | the `place.` id the stage happens at |
| `journal` | the text key `text.journal.<code>.<id>`; + `journalText`: the entry's draft, in the style guide's `journal` register (§4 below) |
| `onEnter` | actions (85 §B), e.g. `{grantTopic: topic.x}`, `{setFlag: [flag.x, true]}` |
| `objectives` | `{id, text: text.objective.<code>.<id>, target, completeWhen: <condition>}`; + `objectiveText`: an imperative with a full stop; `target`: the cast, thing or ref id the compass marker points at (`none` only for a choice between several) |
| + `hidden` | `1` for a stage the build needs and the player never reads (the stage 0 a quest waits at for its opening line); it has no journal or objective |
| `successors`, `failForward` | `{to, when: <condition>}`. A fail-forward on a person's death to a failed ending names someone the quest cannot go on without (who must live): it holds over the stages that carry it, never before the quest's first shown stage, and a person dead before then leaves the quest unable to start. A main-quest record names at least one |
| `ending` | `complete` or `failed` on an end stage; + `endingId`: the `endings` row it plays |
| `outside` | `{packet}` when the stage is built in a later packet (import field) |
| + `actions` / `approaches` | `{skill, use, target, setting, note}` from `skill-uses.yaml`; approaches are `{id, actions}` (principles/actions.md). Supporting acts as `{system, use}` |
| + `learns` | fact ids the player learns here (player knowledge is computed from these) |
| + `directions` | how the player finds the place in words (landmarks, the way, compass points and a word for how far, never a count; against the real route network), written into the journal entry beside the objective's target |

## 2. The record's sections (added to the object, written in this order)

| # | Section | What it holds | Built from |
|---|---|---|---|
| 1 | `recordStatus`, `foundation` | `design`, `reviewed`, `briefed`, `written`; which imported design it rebuilds (the row, its 40-factions or 50-side-quests entry) and what changed | the import |
| 2 | `recordSources` | the place facts file, culture sheets, stance file, roster section read, by path or id; `lore`: each lore file and section checked (quest-write §6b) | world data |
| 3 | `actionPlan`, `centrepiece` | the skill uses the quest is built round (`skill`, `use`, reason), from `action_plan.py`; `centrepiece`: one verb tag (`skill-uses.yaml` verbTags; 00-overview §4) | profile, place, shapes |
| 4 | `truth` | numbered physical events: `id`, `when`, `who`, `where`, `what` (and why) | premise + cast motives |
| 5 | `playerStart`, `facts` | facts any player has on arrival; the quest's new facts `{id, claim, from}`, `from` a truth event, a place fact or `culture.*#field` | truth |
| 6 | `cast` | each person by `npc` id with `wants`, `fears`, `knowledge` per fact (`knows`, `believes: <false version>`, `suspects`, `hides: <reason>`; absent = ignorant), `changes` per stage; `persona` only for what the registry and stance file lack, marked `invented` | `npc`, `stance`, culture sheets, 36-cast-roster |
| 7 | `things` | every physical thing: `{id, kind, name, source: existing <id> | new, where, states, text}`; `name` is what the player sees for a thing of ours (a new item, a container, a page), `text` a readable thing's words | truth + clues |
| 7b | `placements` | where every person, thing, door and marker of the quest stands; every row is in the quest's form. See "Placements" below | things + cast |
| 8 | `conclusions`, `clues` | each conclusion with three clues or more; each clue's `form` (line, thing, place, behaviour), `carrier`, `gives`, `supports` | cast knowledge + things |
| 9 | `shapeData` | the sections each shape requires (`shapes.yaml`) | truth + clues |
| 10 | `stages` | as §1, with actions, learns and directions | conclusions + clues |
| 11 | `endings` | `{id, when, world (actions, may be left out), seen, rewards (actions)}`: two or more with real costs | stages |
| 12 | `topics` | `{id: topic.<slug>, label, person, kind, stages, essential, when, intent, fallback, uses, hides, grants}`; the id is an existing `topic` row or `new`; `kind` is left out for a topic the player picks, `greeting`, or `speaks-first` (the person walks up and says it; it stays open as a topic too). `when` gates every line of the topic (a hand-in that moves no stage: `hasItem`); `fallback` is what the person says when the line's check fails, its gist until the lines are written. See "Checks and their fallbacks" below | cast + stages |
| 13 | `review` | the `quest-review` findings and how each was answered; first the writer's lore-check entries (`id: L<n>`, `severity: lore`, quest-write §6b), then the reviewer's (`severity: blocking` for a quest-review §0 blocking item, otherwise `high`, `medium`, `low`) | quest-write §6b, quest-review |

A **line record** (faction, main, Daedric) comes before its quests: `principles/questlines.md` lists its sections.

### Placements

One row per person, thing, door and marker, keyed by `ref` (the id the record uses everywhere):

| Field | What it holds |
|---|---|
| `ref`, `kind` | the id; `person` (a creature too), `thing`, `door` or `marker` |
| `formKey` | an existing reference; or else `base` and one of `anchor`, `container`, `carriedBy` for a new one |
| `base` | `{kind, id}`: `template_person` (a person or creature of ours on a template), `template_item` (a new item of ours on a template item: it needs a `name`), `item` (a stock item such as gold or lockpicks, or an item whose id is the thing's own), `existing_base` (a container, a static) |
| `anchor` | `{near: <form key>, rule}` or `{place: <census place>, rule}`, `rule` `surface` or `navmesh` |
| `container`, `carriedBy` | a thing's ref it lies in; a person's ref whose pocket it is in (the key on its owner) |
| `name`, `level` | what the player sees for a new person, creature or item when the cast or the thing has no name; a new person's or creature's fixed level (decision 0035) |
| `count` | how many of a stock item lie in one placed reference (five lockpicks) |
| `lock`, `owner` | `{level: novice to master or key, key: <a thing's ref or an item id>}` on a container or door; the container's owner, a person's ref or a faction |
| `enabled`, `hostile`, `killChoice` | on at the start; the player is to fight them; killing them is the player's choice |
| `text` | a readable thing's words (a placed note) |
| `at`, `placeName` | `{cell, interior, x, y, z}` (read from the census for an existing actor or door); the name the player knows the cell by where the census gives none (on a door: the place it leads to) |

**One id for one thing.** A condition or action names a unique quest thing by its `ref` (`hasItem: [thing.mq03.sap-jar, 1]`),
and a stock item by its item id (`item.lockpick`); never a unique thing's template, which would count every item of that
base. A thing two quests place (MQ01 puts out the lockbox MQ03 uses) is stated alike in both.

### Checks and their fallbacks

A line that moves a stage carries its successor's gates. A check the player can fail in front of the speaker (a skill,
an amount of gold) has a fallback: the written line's `fail` info, or until then the topic's `fallback` gist. Without
one the quest does not compile. A line whose failure another line already catches (the haggle when the persuasion fails)
needs none. A gated line never gets an ungated copy: a start topic gated on another quest's stage is simply not offered
before it.

## 3. The engine mapping: the built shapes

A record is built through its quest form (`python3 -m tools.questform compile <quest id>`;
[quest-form](../../../docs/design/quest-form.md) maps each record term to the form and lists the terms it refuses).

| Record field | Built as |
|---|---|
| `id`, `code`, `stages[].id` | one QUST per quest, its editor id from `code`; stage indices from the ids |
| `journal`, `journalText` | the stage's QUST log entry |
| `objectives`, `target` | a QOBJ with a QSTA on a forced-ref alias of the target |
| `successors`, `failForward`, `ending`, `onEnter`, `endings[].world`, `endings[].rewards` | begin fragments that set stages and apply actions (85 §B), native where Skyrim has one (SetStage, AddItem) |
| any condition (`completeWhen`, `when`, `startWhen`, topic gates) | a native condition (85 §A) |
| topic lines | a DIAL and INFO with GetIsID or GetIsReference, the stage window and the check as conditions |
| `sets` of a line | the INFO's fragment |
| a choice | linked topics in the question's branch |
| a greeting after an ending | a Hello topic gated on the ending stage |
| `facts[]` | `fact` rows (`quest_id`) |
| `things[]` with `source: new` | a provision row the world-builder places at `where`; `states` become enable and disable references or local variants per stage |
| `cast[].changes` | a per-stage variant of the person's topic |
| `touches`, `sockets`, `tier` | the validator's checks and tier protection |
| `actionPlan`, `actions`, `approaches`, `truth`, `conclusions`, `clues`, `shapeData`, `playerStart`, `learns`, `centrepiece`, `review` | design only: read by `brief.py`, `quest-review` and the ledger; not built |

## 4. Journal rules

Journal text follows `story/design/text/style-guide.md` § `journal`: first person, past tense for what happened,
"I'm to ..." for the one step now owed; full names and place names as the game shows them (a person by the name their
base carries, with the role beside it at first mention). One entry per stage (`journal`), written as `journalText`
in the record, this step only, two to four sentences. An ending's entry may sum up the quest. A failure has its own
flat entry with its consequence. Directions are landmark prose in the entry beside the objective's target.

## Rules that make it consistent by construction

- **Truth before trail.** Every clue is a trace a truth event left; no truth event the player needs is left without clues.
- **Nobody knows what they could not know.** Knowledge comes from truth events the person took part in or was told of.
- **People come from the registry.** Race, sex, role and home are the `npc` row's; voice is the `stance` row's. A record
  that needs a different value marks it `invented` and adds it to the `npc` or `stance` row; it never silently differs.
- **Motives cite the sheets.** Each `wants`, `fears` and hidden reason cites a culture-sheet or registry entry, or is flagged `invented`.
- **The world is built from the record.** A `new` thing is a provision row; dialogue names a thing only by its id here.
- **Player knowledge is computed** from `playerStart` and each earlier stage's `learns`.
- **New facts flow up, not sideways.** A writer who needs a fact asks; it is added here and the briefs are rebuilt.
