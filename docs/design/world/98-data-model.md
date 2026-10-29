# 98: The data model, a guide to the world database

Read this before you read or write any world data. It is the guide to `world/schema.sql`, the single
description of the world's data (decision 0030). It tells you which table is the home of what, and how to read
and write those tables. It never restates a column: the schema's comment on each table says what that table is
the home of, and its DDL gives the columns, keys and checks.

## The rule

- **One schema.** `world/schema.sql` is in third normal form. There is one table per entity and one per
  relationship. Every row has a stable primary key (the old id strings: `npc.<place>.<slug>`,
  `fact.<place>.<slug>`). Every reference is a foreign key, every enumeration is a lookup table, and prose sits
  in text columns on the row it belongs to.
- **One committed form.** Each table is committed as `world/db/<table>.jsonl`: one row per line, columns in
  schema order, rows sorted by primary key, null columns left out. A git diff is a row diff.
- **One door.** `tools/argonia_world/db.py` is the only reader and writer of `world/`. A tool, skill or agent
  that opens a world file itself is a defect, and the gate's `world` part refuses it
  (`tools/argonia_world/check_world_reads.py`).
- **Everything else is derived.** That covers intermediate JSON, `plugin/`, `Argonia.esm`, the briefs for the
  writing skills, the exported quest views and reports. A derived file is regenerated, never edited. When one
  is wrong, fix its rows and run its step again.

## Reading and writing

```
python3 -m tools.argonia_world.db query "SELECT id, name FROM npc WHERE home_place_id = 'place.hist-heartland.greenspring'"
python3 -m tools.argonia_world.db show npc npc.hist-heartland.greenspring.tree-minder
python3 -m tools.argonia_world.db counts           # rows per table
python3 -m tools.argonia_world.db check            # the gate: the load with every constraint, then the named checks
make db                                            # out/world.sqlite, for DuckDB, pandas or the sqlite3 shell
```

In code, `w = db.open()` gives the loaded world, with foreign keys on.
- **Reads:** `w.get(table, *key)` returns one typed row, `w.rows(table, **eq)` returns typed rows in key order,
  and `w.query(sql, *params)` returns `sqlite3.Row`s.
- **Writes:** `w.insert`, `w.upsert`, `w.update` and `w.delete`, then `w.save()`. The writes run in one
  transaction, with foreign keys deferred until `save()`.
- **Saving:** `save()` runs the foreign-key check and the named checks. Only then does it write the changed
  tables back, sorted. While any check fails it writes nothing and raises `db.LoadError` with every error.

A quest record has an authoring view, `tools/argonia_world/quest_record.py`, described below under Quests.
`tools/argonia_world/records.py` holds the readers the briefs share: a person, a stance, a culture sheet, a
place's facts and condition trees.

## Conventions

- **Child tables.** A child table is keyed by its parent's key plus `ord` (a list position) or the map key, and
  it is deleted with its parent (`ON DELETE CASCADE`). The table name says where it belongs:
  `quest_stage`, `quest_objective` (`quest_id`, `stages_ord`, `ord`).
- **Lookups.** A lookup table (`id`, `about`) lists the allowed values of one enumeration. A new value is a new
  row, added on purpose.
- **Types.** BOOLEAN columns hold 0 or 1 and are read back as `bool`. REAL columns are floats. An untyped
  `value` column (a condition's or action's argument) holds a scalar, and a `bool` there is typed by the term's
  argument shape.
- **Conditions and actions.** These are the vocabulary as data. `condition_term` holds every predicate,
  combinator and action verb with its argument shape (`docs/design/quests/85-condition-vocabulary.md` explains
  each term). A condition is a tree of `condition` rows: a combinator over its children, or a predicate with its
  `condition_arg`s. An action list is an `action_list` row with its ordered `action` and `action_arg` rows.
  - **Ids:** the column that holds a condition's or list's id is its owner. The id is
    `<table>:<owner key joined by |>:<column>`, and a child's id adds `.<n>`.
- **Order.** A fact has an `ord`: its position in its place's or quest's list, the order they state it in.
- **Ownership.** Lanes own tables. The 0030 migrator writes only the tables it migrated, so every other table
  is its writer's: `formid` belongs to the FormID allocator, and the world track's tables belong to their
  lanes. A chunk that adds a table appends its DDL below the end marker of `schema.sql` and writes its rows
  through `db.py`.

## The integrity gate

The integrity gate is the load itself plus four named checks:
- **The load:** types, NOT NULL, CHECK, UNIQUE and every foreign key. A dangling key is refused.
- **The named checks**, in `tools/argonia_world/checks.py`, for the rules SQL cannot state:
  - `lock-owner`: a lock's owner names a row of the table its `owner_kind` says.
  - `journal-grounding`: `groundedIn` is a fact or a promise.
  - `quest-topic`: a quest's topic is a topic row or is marked `new`, and an essential topic is one of those.
  - `term-arity`: every condition and action has the argument count its term's shape allows. A trailing `bool`
    or count may be left out (`flag(x)` is `flag(x, true)`, `hasItem(x)` is `hasItem(x, 1)`).

Some id columns still have no key: sockets by id, water bodies, sites, slots, magic effects, assets and a
stage's `ending_id`. They point at families that are not tables yet, and their chunks add the key along with
the table.

## Which table is the home of what

| Family | Home tables (each with its child tables) |
|---|---|
| Factions | `faction`, `faction_reaction`, `faction_rules`, `rank_ladder`, `deed` |
| People and creatures | `npc` (look, home, schedule, notice, loot, statblock), `npc_faction`, `creature` |
| Stance and culture | `stance` (keyed by `person_id`: chain, per-class lean, voice), `culture_sheet` (`culture_entry` by kind, `culture_opinion`, `culture_view`, `culture_member`, `culture_dissent`) |
| Items and locks | `item`, `item_set`, `item_class`, `container_class`, `lock`, `document` |
| Places | `place` (the catalogue row: siting, relations, contents, life, zones, watch, travel), `place_build` (the old project's last build: stands, sockets, landmarks, `place_person` with topics and services, hostility) |
| Layouts and sockets | `layout` (the ordered workbench program) and `socket`; `socket_vocabulary`, `fill_rule`, `plant_class`, `station_class`, `sign_purpose`, `furniture_activity`, `door_type` |
| Facts | `fact`: one table for place facts (`claim`, carrier, `place_id`), dialogue facts (`says`, `fact_cue`) and quest facts (`quest_id`, `from_ref`) |
| Quests | `quest_line`, `quest` with the record as child tables (`quest_truth`, `quest_cast` and `quest_cast_knowledge`, `quest_thing`, `quest_clue`, `quest_conclusion`, `quest_shape_data`, `quest_stage` with `quest_objective`, `quest_successor`, `quest_fail_forward`, `quest_action`, `quest_approach`; `quest_ending`, `quest_topic`, `quest_review_finding`), `quest_budget_exception`, `journal_entry` |
| Topics and lines | `topic`, `glossary_term`, `dialogue_line` (the imported lines, reference only), `rumour_pool`, `owing_region` |
| Routes and travel | `route`, `authored_track`, `junction`, `harbour`, `lane_terminal`, `water_crossing`, `route_structure`, `route_structure_exemplar`, `travel_service`, `travel_station`, `travel_*` edges and settings, `rootworm_station`, `rootworm_rootway` |
| The character sheet | `attribute`, `skill`, `race`, `class`, `birthsign`, `sheet_rules`, `class_rules` |
| Terrain freeze | `frozen_array` (the frozen heightfield arrays and their hashes; `tools/fetch_vault.py` checks them), `freeze_rules` |
| Conditions and actions | `condition_term`, `condition`, `condition_arg`, `action_list`, `action`, `action_arg` |
| FormIDs | `formid` (entity key to FormID, append-only; written by `tools/argonia_world/formids.py`) |
| Keyed tables, later chunks | `terrain_patch`, `anchor` (2.W1), `hydrology_body`, `hydrology_edge` (2.W2), `region_class`, `weather_state` (2.W3), `flora_rule`, `star` (2.W4), `magic_effect`, `spell` (2.9), `recipe`, `trade_class` (2.10), `loot_rule` (2.3), `trap`, `hazard_volume`, `detection_rule` (2.11), `physical_material` (2.6), `boat_class`, `boat` (2.8), `blueprint_parcel`, `blueprint_door`, `promise` (its keys are already in), `asset`, `culture_kit` (the place builds) |

## Quests: the record as rows

The quest record (`.claude/skills/quest-write/quest-record.md`) is made of rows:
- the `quest` row and its `quest_*` tables;
- its facts, as `fact` rows;
- its conditions and actions.

A writer edits its YAML view. `python3 -m tools.argonia_world.quest_record import QUEST.yaml` replaces the
quest's record rows with the view's and writes nothing on any error. `quest_record export <quest id>` rebuilds
the view from the rows; the skill's worked examples are such exports. `tools/argonia_world/quest_view.json` maps
every YAML path to its column or child table. The briefs (`quest-write/brief.py <quest id>`,
`dialogue-write/place_brief.py --person <id>`) read the rows through `db.py`.

## What is still in world/sources

`world/sources/` is the import (`world/IMPORTED_FROM.md` is its provenance). Its files are read-only and are
deleted family by family as each migrates. What remains belongs to the families in the keyed-tables row above:
- terrain patches, anchors, hydrology, regions, flora, climate and sky;
- the blueprints and promise ledgers;
- the asset registries and the economy;
- the lore dossiers.

A chunk that first reads one of these families migrates it first: it adds the table's columns and rows, and
deletes its files from `world/sources/`.
