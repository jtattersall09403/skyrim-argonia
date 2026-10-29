<!-- imported unchanged from elder-souls-argonia docs/quests/87-written-quest-recipe.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Writing a quest: the recipe

The reference every slice quest is written against (2.11 deliverable e,
decision 0153). Worked example: LF83, the two charges at Claywater
Station (`quest.local.lf83`). Logic, words and facts live in separate
files; nothing in one is restated by hand in another.

## 1. Read first

- The quest's row and prose in [50-side-quests](50-side-quests.md) (or its line file), and
  [60-writing-and-lore](60-writing-and-lore.md) §49-50.
- The place's facts record, `world/sources/placement/facts/<place>.json`: `facts[]` (the claims you may
  state, each with an id), `world.people[]` (who is there and the topics they carry), `world.landmarks`,
  `world.sockets`. A claim the quest needs and the record lacks is a request to lane 2.11-facts (or the
  facts owner) in your report. Never edit a facts record by hand.
- The lore dossiers under `world/sources/lore/` for the place and people.
- [85-condition-vocabulary](85-condition-vocabulary.md): every condition and action is written in it.

## 2. The stages (logic): `world/sources/quests/<packet>.json`

One record per quest (schema `quests.v2`). Per stage:

| Field | Shape | LF83 |
|---|---|---|
| `id` | 10, 20, 30... ; endings 90+ | 10, 20, 30, 90 |
| `place` | the place id the stage happens at | Claywater Station |
| `person` (optional) | the npc the stage is with; the validator wants their facts `people[].topics` to carry the topic | unset: the objective names the npc |
| `journal` | `text.journal.<code>.<stage>` | `text.journal.lf83.10` |
| `onEnter` | actions from 85 § B | `grantTopic` the stage's topic; `setFlag` on the ending |
| `objectives[]` | `{id, text: text.objective.<code>.<id>, completeWhen: <condition>}` | `topicHeardFrom(topic, npc)` |
| `successors[]` | `{to, when}`; first holding wins | the objective's condition |
| `failForward[]` | `{to, when}`; every live stage has one | `any` of `not npcAlive(npc)` for each keeper, to 90 |
| `ending` | `complete` or `failed` on terminal stages | 30 complete, 90 failed |

Quest-level: `touches` (every flag written, every npc and place read; the validator checks them against
the stages), `essentialTopics` (the topics the quest cannot finish without; never gated on disposition).

Rules carried: no quest markers (a marker only from a deliberate in-world act, an action in `onEnter`); no
radiant quests; every live stage fails forward to an ending when a person it needs dies.

**Advancing on a conversation.** There is no "spoke to X" flag. The objective is
`topicHeardFrom(<topic>, <npc>)`, which reads the `heardFrom` the dialogue session records on every line
it delivers. The quest's topics are offered by the person who carries them:
- the opening topic by its giver's role (`topics.json` `requiredFor.roles`, a role unique to the giver), or
  by `requiredFor.places`;
- later topics by `grantTopic` in the stage's `onEnter` (known to the player, so any speaker offers it;
  only the stage's person has an override, so only they answer it in their own words).

Once the stages are written, `python3 -m worldgen.quest_topics --place <place> --write` adds every
`topicHeardFrom` topic to the asked person's `people[].topics` in that place's lines file (idempotent;
`--check` reds a lack). Then `dialogue_lines --write --place <place>`, and the place's facts
`people[].topics` carry it after `place_facts --write --id <place>` (the facts owner runs it).

**Starting.** The giver's start line is a pool line `available: questState(<quest>, unstarted)` with
`onDelivered: setStage(<quest>, 10)`; the giver's override derives from it (`derivedFrom.poolLineId`) and
repeats its `available`. A `.default` pool line on the same topic answers once the quest runs. The start
line's topic and giver never make the stage it sets: stage 10 asks another topic or another person, or
advances on something else (`stage.opening` reds a start line that already meets its stage).

## 3. Directions (route graph, never prose)

A stage that sends the player elsewhere carries `directions: [{to, from?, landmarks?}]`. The validator walks
the shipped route graph from `from` (else the stage's place) and checks the walk ends inside `to`'s facts
extent and that each landmark is in sight of the route. The words ("north along the causeway, past the
shrine") are generated from that walk by `packages/dialogue/src/directions`; the journal and lines only
restate what the walk says. A quest inside one place (LF83: "across the ford") needs no directions entry.

## 4. The words (text): catalogue units, written through the dialogue-write skill

- **Dialogue.** Topics in `world/sources/dialogue/topics.json` (class `quest`, `keys.quest`); facts the
  lines state in `world/sources/dialogue/facts.json`, each grounded on the place's facts claim ids;
  pool lines through `python3 -m worldgen.dialogue_pool add`; per-person overrides through the
  dialogue-write skill's writer packets (`dialogue_rewrite packet`, a `deliver-small` writer per person,
  `check`, `freeze`, `apply`, `dialogue_lines --stamp`, then `--write --place` and `--write --pool`). No
  rounds, panels or corpus reads for a quest (0153 item 5).
- **Journal and objectives.** `world/sources/text/journal/<packet>.json`: one unit per key a stage names,
  `{id, questId, surface: journal, text, factIds, groundedIn}`. `factIds` are the dialogue facts the words
  state; `groundedIn` the place facts claim ids. Journal: first person, past tense, names in full, says
  only what the player saw or was told. Objectives: imperative, no full stop.
  `python3 -m worldgen.place_text --emit-text --whole-province --reason "<why>"` compiles them into
  `packages/text-catalogue/src/generated/journal-text.ts`.
- **Review.** A `reader` child text-reviews the journal and the quest's overrides against the style guide
  and against the facts (it catches personified things, stray facts and ambiguous pronouns the linter
  does not). Fix through `dialogue_rewrite reopen --reds text-review`, `check`, `freeze`, `apply`.
  `python3 -m worldgen.lint_prose --file <file>` is green on every file touched.

## 5. Gates

- `python3 -m worldgen.quests --check --whole-province --reason "<quest>"`: graph, world-ref and every
  `stage.*` rule 0 red.
- The headless driver plays it through dialogue (below), from a new game and from every save point.
- Tests beside the change: `packages/narrative` vitest and tsc, `packages/text-catalogue` vitest.

## 6. The driver script: `packages/narrative/src/data/scripts/<code>.json`

Data only; no TypeScript per quest. The file is `{quest, scripts: [{name, expectEnding, expectStage,
opening?, steps: [{atStage, facts?, actions?, reads?, asks?}]}]}`, one script per ending; `opening` is the
asks that start the quest instead of `start`; a record with `startWhen` needs `startFacts` (the outside facts of the
event that makes it hold, e.g. `discovered.<socket>`), never `start`; `reads` names document items read, each granting the
topics its `documents.json` row `teaches`. The one host (`driver/worldHost.ts`) finds the record in
any `world/sources/quests` file, loads the pool and the published bundle and facts world block of
every place the record names (anchors, settlement, stage places, touched places), and asks through a
real `DialogueSession` committed into the narrative. Outside facts it answers from: `alive.<npc>`,
`items.<item>`, `gold`, `cleared.<place>`, `stance.<place>` (default the facts' hostility baseline),
`discovered.<poi>`. `cli.ts` drives every scripts file from every save point
(`npx tsx packages/narrative/src/driver/cli.ts [quest-id]`); `worldHost.test.ts` holds LF83's
expectations. A world term the host does not answer is a host change for every quest, never a
per-quest host. See `scripts/lf83.json`.
