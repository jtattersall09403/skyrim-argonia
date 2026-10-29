# The quest record

One YAML file per quest is the only source of truth for that quest (decision 0024 §1). It is **the imported
quest object plus the record's sections**: the object's fields are exactly those of
`world/sources/quests/README.md` (the rows in `quests-*.json` and `local-<region>.json`), and the record adds
the sections below them. There is no second quest format: when the record is `reviewed`, its quest-object
fields replace the row in the quest data file (same `id`), and the added sections stay in the record.
Conditions and actions are written only in the condition vocabulary
(`docs/design/quests/85-condition-vocabulary.md`); a term it lacks is added there first, never written in prose.
Worked examples: [examples/lh38.yaml](examples/lh38.yaml) (local), [examples/mr01.yaml](examples/mr01.yaml)
(faction).

## 1. The imported quest object (field names as in the import)

| Field | Rule (from `world/sources/quests/README.md`) |
|---|---|
| `id`, `code`, `title` | `quest.<line-slug>.<code-lower>`, never reused; two capitals two digits; working title |
| `line`, `group`, `tier` | a `quest.line.*` id from `lines.json`; its group (`main`, `faction`, `line`, `local`, `daedric`, `proposed`); 0–3, a quest may not write what a lower tier owns (40-factions §30b) |
| `status` | the import's `live`, `concept`, `skeleton`, `proposed`. The record's own progress is `recordStatus` (§2) |
| `shapes` | primary first, up to two secondary, from the 16 (docs/design/quests/index/README.md §47b) |
| `region`, `settlement`, `anchorPlaces` | catalogue region; a live settlement `place.` id, also in `anchorPlaces` |
| `premise` | one clause the player could say back afterwards |
| `costTier`, `milestone` | `S`/`M`/`L` (00-overview, cost tiers); 1 or 2 |
| `touches`, `sockets`, `essentialTopics`, `sources` | shared ids read or written; placed sockets; topics never gated on disposition (old 0145); the docs the row came from |
| `startWhen`, `start` | optional: a condition that enters the quest at `start` (85 §D) |
| `stages` | the stage graph below |

**A stage** keeps the import's fields and adds the record's (marked +):

| Field | What it holds |
|---|---|
| `id` | 10, 20…; 90+ for endings and fail-forward |
| `place` | the `place.` id the stage happens at |
| `journal` | the text key `text.journal.<code>.<id>`; + `journalText`: the entry's draft, in the style guide's `journal` register (§4 below) |
| `onEnter` | actions (85 §B), e.g. `{grantTopic: topic.x}`, `{setFlag: [flag.x, true]}` |
| `objectives` | `{id, text: text.objective.<code>.<id>, completeWhen: <condition>}`; + `objectiveText`: the draft |
| `successors`, `failForward` | `{to, when: <condition>}`; every stage that names a person has a fail-forward for that person's death (old 0138) |
| `ending` | `complete` or `failed` on an end stage; + `endingId`: the `endings` row it plays |
| `outside` | `{packet}` when the stage is built in a later packet (import field) |
| + `actions` / `approaches` | `{skill, use, target, setting, note}` from `skill-uses.yaml`; approaches are `{id, actions}` (principles/actions.md). Supporting acts as `{system, use}` |
| + `learns` | fact ids the player learns here (player knowledge is computed from these) |
| + `directions` | how the player finds the next place: landmark, direction, distance, against the real route network; no markers (old 0137) |

## 2. The record's sections (added to the object, written in this order)

| # | Section | What it holds | Built from |
|---|---|---|---|
| 1 | `recordStatus`, `foundation` | `design`, `reviewed`, `briefed`, `written`; which imported design it rebuilds (the row, its 40-factions or 50-side-quests entry) and what changed | the import |
| 2 | `recordSources` | the place facts file, culture sheets, stance file, roster section read, by path or id | world data |
| 3 | `actionPlan`, `centrepiece` | the skill uses the quest is built round (`skill`, `use`, reason), from `action_plan.py`; `centrepiece`: one verb tag (`skill-uses.yaml` verbTags; 00-overview §4) | profile, place, shapes |
| 4 | `truth` | numbered physical events: `id`, `when`, `who`, `where`, `what` (and why) | premise + cast motives |
| 5 | `playerStart`, `facts` | facts any player has on arrival; the quest's new facts `{id, claim, from}`, `from` a truth event, a place fact or `culture.*#field` | truth |
| 6 | `cast` | each person by registry id (`npcs.json`) with `wants`, `fears`, `knowledge` per fact (`knows`, `believes: <false version>`, `suspects`, `hides: <reason>`; absent = ignorant), `changes` per stage; `persona` only for what the registry and stance file lack, marked `invented` | npcs.json, stance, culture sheets, 36-cast-roster |
| 7 | `things` | every physical thing: `{id, kind, source: existing <id> | new, where, states}` | truth + clues |
| 8 | `conclusions`, `clues` | each conclusion with three clues or more; each clue's `form` (line, thing, place, behaviour), `carrier`, `gives`, `supports` | cast knowledge + things |
| 9 | `shapeData` | the sections each shape requires (`shapes.yaml`) | truth + clues |
| 10 | `stages` | as §1, with actions, learns and directions | conclusions + clues |
| 11 | `endings` | `{id, when, world (actions), seen, rewards (actions)}`: two or more with real costs | stages |
| 12 | `topics` | `{id: topic.<slug>, label, person, stages, essential, intent, uses, hides, grants}`; the id is an existing `world/sources/dialogue/topics.json` row or `new` (2.5 adds it) | cast + stages |
| 13 | `review` | the `quest-review` findings and how each was answered | quest-review |

A **line record** (faction, main, Daedric) comes before its quests: `principles/questlines.md` lists its sections.

## 3. The engine-mapping table: every machine field and its consumer

| Field | Consumer (chunk) | How |
|---|---|---|
| `id`, `code`, `stages[].id` | quest generator (1.4 first rung, 2.12 §a) | one QUST per quest, EDID from `code`; stage indices from ids |
| `stages[].objectives` | generator → QUST objectives (no target markers) | `completeWhen` → begin-fragment stage advance via the evaluator |
| `stages[].successors`, `failForward`, `ending` | generator → Papyrus begin-fragments calling ArgoniaCore (1.4, 2.12 §a) | `when` evaluated by ArgoniaCore; begin fragments only (2.5 engine facts) |
| `stages[].onEnter`, `endings[].world`, `endings[].rewards` | ArgoniaCore action applier (1.4 first actions, 2.12 §a) | 85 §B actions; native where Skyrim has one (SetStage, AddItem) |
| any condition (`completeWhen`, `when`, `startWhen`, topic gates) | ArgoniaCore evaluator (1.3 first predicates, 2.5 whole) | 85 §A; native conditions where they exist |
| `journal`, `journalText`, `objectiveText` | the journal (1.2 view, 1.4 entries, 2.12 §b) and the text catalogue (2.5 §b) | QUST log entries and our journal store by text key |
| `stages[].directions` | the journal's directions (1.4 by hand, 2.12 §a generator and validator over 2.W3 routes) | `directionsId` on the entry |
| `topics[]` (`id`, `label`, `person`, `stages`, `essential`) | topic store (1.3 first rung, 2.5 §a) | topic row in `topics.json` (`keys.quest`); availability = questStage condition |
| topic lines (written by `dialogue-write`) | topic store (1.3, 2.5 §b) | lines by person and band, citing fact ids |
| `facts[]` (`id`, `claim`) | dialogue facts (`world/sources/dialogue/facts.json`, 2.5 §b) | `says` from `claim`; cues added by 2.5 |
| `cast[].persona`, `wants`, `fears` (invented rows) | people records (2.4) | written back to `npcs.json` / stance before generation |
| `cast[].changes` | topic store conditions (2.5) | a per-stage variant of the person's topic |
| `things[]` with `source: new` | the world-builder (2.W5 slice, 4.2 packets, 4.4 interiors); by hand in 1.4 | a provision row placed at `where`; `states` → `enableRef`/`disableRef`/local variants |
| `things[].states` | generator + local-state overlay (2.12 §a) | `applyLocalVariant` per stage |
| `touches`, `sockets`, `tier` | quest validator (2.12 §a) and tier protection (old 0030) | |
| `actionPlan`, `actions`, `approaches` | design only: the reviewer and the ledger (`action_plan.py --ledger`); their `world` needs become `things` rows | not generated |
| `truth`, `conclusions`, `clues`, `shapeData`, `playerStart`, `learns`, `review` | design only: `brief.py` and `quest-review` | not generated |
| `centrepiece` | the old validator's per-line verb-tag ratios (00-overview §4); `brief.py` checks it | not generated |

**Needs a decision** (fields or terms the planned engine cannot yet express; each must get a chunk or a ruling
before a quest that uses it is generated):

| Field or term | Why |
|---|---|
| `present-evidence`, `accuse` actions | 85 has `hasEvidence` and `topicHeardFrom` but no "show item X to person Y" or "accuse Y with exhibits" verb, and no dialogue-view affordance; 2.5 §a and 2.12 §a name the need (0025) but no row defines it |
| rival factions' reactions to a solved case | no action or predicate for a faction reacting to the player's accusation or exposure beyond `changeStanding`; needs a term or a rule (0025) |
| `witnessed(event)` / `recordWitnessed` | no chunk builds the event ledger that sets them |
| `custody`, `evidenceState` | listed in 2.5's evaluator, but nothing sets an item's state (copied, altered) or custody in any chunk |
| `setSchedule(npc, schedule)` for "spy" stages | the people's day (2.4) exists; no chunk lets a stage swap it |
| `disguisedAs`, `wearing` as disguise; `grantHistStep`/`histStepAtLeast` | no chunk (skill-uses.yaml systems marked DECISION) |
| `lockIs`, `seenBy`, `inZone` | marked `planned: 2.10` in 85; the plan builds them in 2.11: re-point the vocabulary |
| `timeOfDay` as a stage gate for night-only clues | evaluator has it (2.5); the generator must re-check on the clock, not only on dialogue: say which |

## 4. Journal rules (imported design)

Journal text follows `docs/design/standards/text/style-guide.md` § `journal`: first person, past tense for events,
"I'm to…" or "I must…" for the outstanding objective; full names and place names every entry; each entry
re-summarises the chain from its start; directions in landmark prose, never a marker for an undiscovered place
(old 0137); a failure state has its own flat entry with its consequence. One entry per stage (`journal`), written
as `journalText` in the record and moved to the text catalogue by 2.5.

## 5. Investigation support (decision 0025): what the import already covers

| Need | Covered by the import | 2.5 and 2.12 must add |
|---|---|---|
| Evidence-gated topics | `knowsTopic`, `topicHeardFrom`, `hasEvidence`, `grantTopic`, `not` (85 §A3, §D); `essentialTopics` | the topic store's per-topic availability conditions (2.5 §a) |
| Catching a lie | `topicHeardFrom` (who told you) | a topic variant that changes when the player holds the refuting fact or item |
| Presenting evidence | `hasEvidence` only (possession) | a "show" act in the dialogue view: item or learned topic → person → response; a vocabulary term for it |
| Accusation | nothing | an "accuse" act naming suspect and exhibits, a threshold (`needed`), outcomes as stages; a term |
| Tampering and custody | `evidenceState`, `custody` predicates | the actions and state that set them |
| Rival reactions | `changeStanding`, `changeDisposition`, `seedRumour` | a rule for which rival faction reacts and how (Shadowscales, Night-Reed) |
| Witnessing a scene | `witnessed`, `recordWitnessed`, `startScene` | the event ledger and scene runtime |

## Rules that make it consistent by construction

- **Truth before trail.** Every clue is a trace a truth event left; no truth event the player needs is left without clues.
- **Nobody knows what they could not know.** Knowledge comes from truth events the person took part in or was told of.
- **People come from the registry.** Race, sex, role and home are `npcs.json`'s; voice is the stance file's. A record
  that needs a different value proposes it as `invented` for 2.4 to write back; it never silently differs.
- **Motives cite the sheets.** Each `wants`, `fears` and hidden reason cites a culture-sheet or registry entry, or is flagged `invented`.
- **The world is built from the record.** A `new` thing is a provision row; dialogue names a thing only by its id here.
- **Player knowledge is computed** from `playerStart` and each earlier stage's `learns`.
- **New facts flow up, not sideways.** A writer who needs a fact asks; it is added here and the briefs are rebuilt.
