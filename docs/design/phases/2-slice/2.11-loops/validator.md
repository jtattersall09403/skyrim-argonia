<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.11-loops/validator.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# The quest graph and world-reference validator

Part of [2.11](../2.11-quests-journal-map.md) (deliverable b). Code:
`tooling/world-generation/worldgen/quest_graph.py`, run by
`python3 -m worldgen.quests --check`, tests in `worldgen/test_quest_graph.py`.
`--check` prints every rule with its red count, the reds under each, and exits 1
on any red.

## Rules

Graph rules run over records that carry `stages`. The start stage is `start`, or
the lowest stage id.

| Rule | Red when |
|---|---|
| `graph.reachable` | a stage cannot be reached from the start through `successors` and `failForward` |
| `graph.target-exists` | a successor or failForward `to`, or the start stage, names no stage; or stage ids repeat |
| `graph.objective` | objective ids repeat within a stage; or a stage has objectives but no successor and no ending |
| `graph.ending` | a stage has no successor, no failForward and no `ending` |
| `graph.condition` | a `completeWhen` / `when` condition (including `all`, `any`, `not` parts) names no quests/85 predicate, or its arguments do not fit |
| `graph.action` | an `onEnter` / `onComplete` action names no quests/85 action, or its arguments do not fit |

World-reference rules run over all records.

| Rule | Red when |
|---|---|
| `world.touch` | a `touches` id with a home table is not in it: `place.` the live catalogue, `npc.` registries/npcs.json, `item.` registries/items.json, `faction.` registries/factions.json, `quest.` the quest records. Other prefixes (flag, topic) have no home table and are not checked here |
| `world.flag-read` | a `read` touch of a `flag.` id that nothing writes. A flag is written when any record has a `write` touch of it or any stage action is `setFlag` on it |
| `world.stage-place` | a stage `place` is not a live catalogue place |
| `world.stand-in` | `standInFor` is not a quest record |
| `world.action-id` | an id in a stage action with a home table (the five prefixes above) does not resolve |

Not covered, by the brief's scope: ids inside conditions are checked for name
and arity only, not resolved against home tables.

## Vocabulary

Terms and arities are read at run time from the runtime's own source
(`packages/dialogue/src/conditions.ts` PREDICATES, `actions.ts` ACTIONS, enum
constants from `world.ts`), so there is no copy to drift. A predicate the
quests/85 doc marks `planned:` has no evaluator and is rejected, as the runtime
rejects it. Tests pin it: the parsed names equal a second, cruder reading of the
source; shapes of the awkward terms (`flag`, `timeOfDay`, `worstCrimeIs`,
`questStage`) are asserted; the parsed names equal quests/85's tables, with
`planned:` rows excluded.

## Survey (real data)

715 records, none yet with `stages` and none with `touches`, so every rule is at
0 reds, and the graph and flag rules have had nothing real to read yet.

| Rule | Reds |
|---|---|
| graph.reachable | 0 |
| graph.target-exists | 0 |
| graph.objective | 0 |
| graph.ending | 0 |
| graph.condition | 0 |
| graph.action | 0 |
| world.touch | 0 |
| world.flag-read | 0 |
| world.stage-place | 0 |
| world.stand-in | 0 |
| world.action-id | 0 |

## Fail on purpose

`test_every_rule_is_red_on_its_planted_fixture` plants one defect per rule into
a clean fixture (which itself passes) and asserts that rule fires;
`test_each_planted_fixture_trips_only_its_own_rule_or_a_consequence` asserts no
other rule fires. Further tests cover start-stage handling, an objective with no
way on, the flag rule satisfied by an action or a write touch, and records
without stages skipping the graph rules. 19 tests pass with `worldgen/test_quests.py`.

## Stage rules (deliverable c)

`worldgen/quest_stages.py` appends seven rules to `quest_graph.STAGE_RULES`;
`quests.graph_reds` gives them `ctx.world`, a `World` read from the place facts
record (`world/sources/placement/facts/*.json`, key `world`), the build ledger's
`gatesOk` rows (the slice) and the shipped route graph through the walker's
`routes` command (one call for every direction pair). Never catalogue prose.
The fields they read are in quests.v2: stage `directions[]` (`from`, `to`,
`landmarks`, `claims[]` of `subject`, `bearing`, `of`), stage `outside.packet`,
objective `where` (`place`, `ref`, `area`, `kind`). Extent is the facts
`boundaryM` polygon together with the `footprintRadiusM` circle.

| Rule | Red when |
|---|---|
| `stage.direction` | a direction has no way on the route graph from where it is given (`from`, else the stage's place), or its last node lies outside `to`'s extent, or `to` has no facts block; a named landmark is no facts landmark, or neither its place nor its `inSight.places` is a place on the walked route |
| `stage.claim` | a compass bearing (8 points) from `of` to `subject`, or inside/outside `of`'s extent, disagrees with the facts positions |
| `stage.count` | `hasItem` with n of 2 or more, or `counterAtLeast`, names no `where` area and kind, or the facts `counts[area][kind]` is below n |
| `stage.person` | `topicHeardFrom(topic, npc)`: the npc is not in the place's facts `people` or does not carry the topic; `where.ref` is not a socket, stand or landmark of the place |
| `stage.stance` | the start stage, or a stage with a `place`, enters a place that is hostile at that moment (baseline, then each place-scope flip whose `when` an earlier stage of this quest or a stage of another staged quest can make hold; last wins), and is neither `entry: clear` on a clearable place nor `entry: outside` with every objective `where.ref` a socket outside the extent |
| `stage.stand-in` | a `standInFor` record still grants (a `grant*`/`give*`, `offerTeach`, `setFactionRank` or `promoteSuccessor` action) while an anchor of the quest it stands in for is `gatesOk` (0157) |
| `stage.partial` | a stage's place is past the slice and the stage is not `outside`; an `outside` stage is on a built place, names no Part 4 phase file, names a region other than its place's (`4.2.<region>`), or carries objectives, successors, failForward or an ending |

Tests: `tests/test_quest_stages.py` (a clean fixture green on every rule; each
rule red on its planted fixture and on no other; further reds per rule; one
real direction over the shipped graph and facts both ways). An `outside` stage
satisfies `graph.ending`.

## Seam for deliverable c

`quest_graph.STAGE_RULES` holds the stage rules above. A stage-level consistency rule is
`rule(quest, stage, ctx) -> list[Red]`; append it and `validate` runs it once per
stage of every record with stages, its reds grouped under its own rule id (add
the id to `RULES` so `--check` prints its count). A test asserts the list runs per stage.
