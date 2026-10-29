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

## Data homes added after the migration

Tables below the end-of-migration marker in `world/schema.sql`, and the two JSON files beside the schema that
are the homes of what SQL does not hold. Each is written by the tool named.

| Home | Of what | Written by |
|---|---|---|
| `data/router/surfaces.json` | the router registry: every vanilla surface Argonia takes over (1.1 §d) | by hand; `tools/schema_gen` (`router.ts`) generates `gen::kSurfaces` |
| `skse/core/schema/families.json` | the co-save family layouts: id, version, payload fields (1.1 §b) | by hand; `tools/schema_gen` (`families.ts`) generates `family_layouts.h` |
| `core_module`, `core_constant`, `core_burden_tier`, `core_armour_skill`, `core_skill_class`, `core_use`, `core_use_skill_points`, `core_ranks_per_level`, `core_bed_tier`, `core_disposition_band`, `core_respawn_class`, `core_wear_kind`, `core_effect_op`, `core_stat_field` | the core rules' constant tables (curve, use, vastei, rest, disposition, wear, effects) | `tools/argonia_world/core_tables.py`, which generates `skse/core/generated` |
| `condition_shape`, `condition_shape_arg`, `condition_shape_value`, `condition_op` | each condition term's evaluation shape, argument kinds and operators for the C++ evaluator | `core_tables.py` |
| `season`, `condition_shape_season`, `season_factor` | the one season vocabulary (share of year, order), the seasons `calendarIs` takes, and a season's factor on a weather state's weight | `tools/argonia_world/regions/migrate.py`; read by `regions/season.py` |
| `hydrology_river`, `hydrology_junction`, `hydrology_reach`, `hydrology_body`, `hydrology_edge`, `hydrology_setting` and their children | the river graph, bodies of water and the graph's settings | `tools/argonia_world/water/migrate.py`, `water/` |
| `water_budget_cell`, `water_loss`, `water_regrade` | the water plan's plane budget, each reduction, and each regraded ground vertex | `python -m tools.argonia_world.water plan --write-db`; `terrain/water_regrade.py` |
| `eco_class`, `region_class_profile`, `region_class_override` (`_point`, `_applies`, `_eco_override`), `region_class_role`, `object_role`, `object_form` | ecological classes, old raster classes, owner macro overrides, placement roles and the vanilla forms an object list may name | `tools/argonia_world/regions/migrate.py`, `regions/classify.py` |
| `weather_group`, `weather_state_profile`, `weather_group_weight`, `weather`, `weather_realisation`, `image_space` | weather groups, states, the weathers (WTHR) that realise them, and our image spaces | `regions/migrate.py`, `regions/classify.py` |
| `land_region`, `cell_region_run`, `land_region_class_share`, `land_region_weather`, `land_region_object` | region records (REGN), their cell runs, class mix, weather list and object list | `regions/classify.py`, `regions/api.py` |
| `road`, `road_point`, `road_structure`, `route_node`, `route_edge`, `route_edge_landmark`, `signpost`, `signpost_arm` | road legs and their paint, the route graph and the signposts | `tools/argonia_world/routes/infra.py`, `routes/build.py` |
| `terrain_input`, `terrain_patch_outcome`, `land_cover`, `land_cover_ltex` | terrain inputs, each patch's outcome, and the land-cover painting | `tools/argonia_world/terrain/migrate.py`, `terrain/landcover.py` |
| `grass_source`, `ltex_grass_plan`, `ltex_grass` | the grass sources and the land-texture grass plan | `tools/argonia_world/terrain/grass.py` |

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

## Every table, by parent

The children and lookups of the families above, listed so the guide names every table; the schema comment on each says what it holds.

- `faction`: `faction_kind`, `faction_source`, `faction_standing_join_sources`, `faction_standing_expel_causes`, `faction_standing_expel_cost`, `faction_standing_expel_return`, `faction_standing_expel_unstated`, `faction_standing_expel_sources`, `faction_standing_join_requires_quest_state`
- `npc`: `npc_kind`, `npc_depth`, `npc_statblock`, `npc_fight_flee_alarm`, `npc_home_bed`, `npc_work`, `npc_role_exception`, `npc_day_block`, `npc_service`, `npc_quest_hook`, `npc_source`, `npc_den`, `npc_territory`, `npc_notice`, `npc_loot`, `npc_signature_spell`
- `asset`: `asset_status`
- `item`: `item_kind`, `item_condition`, `item_source`, `item_asset_record`, `item_effect`, `item_incendiary`, `item_recipe`, `item_soul_gem`, `item_tag`, `item_enchantment`
- `lock`: `lock_kind`, `lock_class`, `lock_source`
- `deed`: `deed_kind`, `deed_source`
- `rumour_pool`: `rumour_pool_kind`, `rumour_pool_source`
- `document`: `document_kind`, `document_leaf`, `document_source`, `document_teaches`
- `creature`: `creature_kind`, `creature_source`, `creature_region`, `creature_band`, `creature_statblock`, `creature_fight_flee_alarm`, `creature_notice`, `creature_day_role_exceptions`, `creature_day_blocks`
- `quest`: `quest_group`, `quest_status`, `quest_shape`, `quest_anchor_place`, `quest_touch`, `quest_source`, `quest_essential_topic`, `quest_record_source`, `quest_player_start`, `quest_socket`
- `topic`: `topic_class`, `topic_required_for_places`, `topic_required_for_glossary_terms`, `topic_required_for_factions`, `topic_required_for_roles`, `topic_required_for_people`
- `route`: `route_mode`, `route_class`, `route_alias`, `route_source`, `route_stages`
- `skill`: `skill_family`, `skill_bands`, `skill_effect_visibility_at`
- `rank_ladder`: `rank_ladder_rank`
- `faction_rules`: `faction_rules_member_disposition`, `faction_rules_crime_against_member`, `faction_rules_doom_tier`, `faction_rules_doom_by_role`
- `npc_statblock`: `npc_statblock_variants`
- `npc_territory`: `npc_territory_socket_ids`
- `npc_notice`: `npc_notice_senses`
- `npc_loot`: `npc_loot_items`, `npc_loot_frozen_from`
- `item_recipe`: `item_recipe_inputs`
- `item_set`: `item_set_source`, `item_set_requirement_bonus`, `item_set_materials`, `item_set_bonus_damage`
- `creature_statblock`: `creature_statblock_variants`
- `creature_notice`: `creature_notice_senses`
- `owing_region`: `owing_region_source`
- `place`: `place_alias`, `place_era_layers`, `place_source`, `place_siting_prefs_region_classes`, `place_siting_prefs_landform_classes`, `place_siting_prefs_hard_constraints`, `place_siting_prefs_preferences`, `place_siting_prefs_scour_site_ids`, `place_relations_depends_on`, `place_relations_supplies`, `place_relations_rivals`, `place_relations_patrols`, `place_relations_tolls`, `place_relations_visible_from`, `place_relations_reached_via`, `place_relations_travel_service_edges`, `place_occupants`, `place_notable_npc_slots`, `place_traversal_modes`, `place_loot_table_kinds`, `place_asset_plan`, `place_quest_hooks_provisions`, `place_quest_hooks_tags`, `place_deed_counter_keys`, `place_sockets_scene`, `place_sockets_evidence`, `place_sockets_post`, `place_sockets_marks`, `place_local_state_variants`, `place_candidates_considered`, `place_hostility_flips`, `place_player_purpose_secondary`, `place_interior_room_functions`, `place_interior_traversal`, `place_interior_combat_spaces`, `place_interior_anchor_sockets`, `place_contents_creatures`, `place_contents_npcs`, `place_contents_loot`, `place_siting_prefs_bound_to`, `place_siting_prefs_sightline_to`, `place_local_groups`, `place_prose_refs`, `place_services`, `place_travel_station_modes`, `place_travel_station_destinations`, `place_siting_prefs_near_point`, `place_relations_reserved_reached_via`, `place_relations_reserved_supplies`, `place_interior_facts_varied_for_variety`, `place_underwater_access_detail`, `place_relations_reserved_depends_on`, `place_terrain_requests`, `place_hero_hist`, `place_relations_reserved_rivals`, `place_plot_override`, `place_life`, `place_zones`, `place_watch`, `place_city_layout`, `place_footprint_polygon`, `place_relations_relations_reserved`, `place_relations_reserved_visible_from`, `place_asset_gaps`, `place_authored_danger_property`, `place_secondary_cultures`, `place_faction_presence`, `place_relations_reserved_travel_service_edges`, `place_relations_reserved_patrols`, `place_relations_reserved_tolls`, `place_siting_prefs_scour_site_candidates`, `place_hostility_trespass_zones`
- `place_siting_prefs_preferences`: `place_siting_prefs_preferences_landform_classes`
- `place_life`: `place_life_groups`, `place_life_creatures`
- `place_life_groups`: `place_life_groups_lines`, `place_life_groups_services`, `place_life_groups_role_exceptions`, `place_life_groups_spots`, `place_life_groups_signature_spells`, `place_life_groups_races`, `place_life_groups_post_roles_socket_opening_work_camp_encounter_camp_guards`
- `place_life_creatures`: `place_life_creatures_territory`, `place_life_creatures_lines`, `place_life_creatures_role_exceptions`
- `place_city_layout`: `place_city_layout_way`
- `place_life_groups_spots`: `place_life_groups_spots_work`, `place_life_groups_spots_add_work`
- `item_class`: `item_class_kind`
- `container_class`: `container_class_name_family`
- `furniture_activity`: `furniture_activity_family`
- `fill_rule`: `fill_rule_loot_table_fields`
- `plant_class`: `plant_class_species`
- `station_class`: `station_class_dressing`
- `sign_purpose`: `sign_purpose_needs`
- `socket_vocabulary`: `socket_vocabulary_decision`, `socket_vocabulary_common_fields`, `socket_vocabulary_interactables_classes`, `socket_vocabulary_interactables_cook_hosts`, `socket_vocabulary_interactables_cook_stations`, `socket_vocabulary_interactables_soft_sets`, `socket_vocabulary_service_surfaces_name_families`, `socket_vocabulary_sign`
- `layout`: `layout_place`, `layout_bind`, `layout_path`, `layout_note`, `layout_mount`, `layout_move`, `layout_group`, `layout_remove`, `layout_pool`, `layout_mound`, `layout_settle`, `layout_snap`, `layout_swap`, `layout_cliff_ways`
- `layout_path`: `layout_path_points`
- `layout_place`: `layout_place_pad`, `layout_place_fills`, `layout_place_states`
- `socket`: `socket_loot_table`, `socket_fills`, `socket_schedule`, `socket_accepts`, `socket_points_to`, `socket_states`
- `socket_loot_table`: `socket_loot_table_items`
- `layout_pool`: `layout_pool_sources`
- `layout_mound`: `layout_mound_polygon_m`, `layout_mound_sources`, `layout_mound_ramp_m`, `layout_mound_faced_by`
- `layout_place_pad`: `layout_place_pad_apron_by_side`
- `layout_bind`: `layout_bind_fills`
- `layout_cliff_ways`: `layout_cliff_ways_pieces`
- `quest_line`: `quest_line_source`
- `quest_shape`: `quest_shape_of`
- `quest_record_source`: `quest_record_source_items`
- `quest_action`: `quest_action_plan`
- `quest_truth`: `quest_truth_who`
- `quest_cast`: `quest_cast_change`, `quest_cast_persona_invented`
- `quest_thing`: `quest_thing_state`
- `quest_conclusion`: `quest_conclusion_clue`
- `quest_clue`: `quest_clue_gives`, `quest_clue_supports`
- `quest_shape_data`: `quest_shape_data_items`, `quest_shape_data_exhibits`, `quest_shape_data_closed_run`
- `quest_stage`: `quest_stage_learns`, `quest_stage_directions`
- `quest_approach`: `quest_approach_action`
- `quest_topic`: `quest_topic_stage`, `quest_topic_uses`, `quest_topic_hides`, `quest_topic_grants`
- `quest_review_finding`: `quest_review_finding_ids`
- `quest_shape_data_items`: `quest_shape_data_items_to`
- `journal_entry`: `journal_entry_fact`, `journal_entry_grounding`
- `place_build`: `place_build_position_m`, `place_build_boundary_m`, `place_build_extent_m`, `place_build_route`, `place_build_stands`, `place_build_sockets`, `place_build_landmarks`, `place_build_services`, `place_build_hostility`
- `place_build_sockets`: `place_build_sockets_fills`
- `place_build_landmarks`: `place_build_landmarks_in_sight_places`, `place_build_landmarks_in_sight_here`
- `place_person`: `place_person_services`, `place_person_topics`
- `place_build_services`: `place_build_services_by`, `place_build_services_filled_by`
- `place_build_hostility`: `place_build_hostility_flips`
- `dialogue_line`: `dialogue_line_fact`, `dialogue_line_link`
- `stance`: `stance_chain`, `stance_topic`, `stance_answer_length`, `stance_never_mentions`, `stance_explainer_of`
- `authored_track`: `authored_track_point`, `authored_track_settings`
- `minor_waterway_settings`: `minor_waterway_settings_waterways`
- `junction`: `junction_road`
- `route_structure_exemplar`: `route_structure_exemplar_structures`, `route_structure_exemplar_life_creatures`
- `route_structure_exemplar_life_creatures`: `route_structure_exemplar_life_creatures_territory`, `route_structure_exemplar_life_creatures_lines`
- `route_structure_exemplar_structures`: `route_structure_exemplar_structures_crossing_ids`
- `route_structure`: `route_structure_settings`
- `route_structure_settings`: `route_structure_settings_ferry_crossings`
- `travel_service`: `travel_service_fare_free_if`, `travel_service_hops`, `travel_service_refused_if`, `travel_service_stations`, `travel_service_crossing`, `travel_service_landings`, `travel_service_measured`, `travel_service_severs`, `travel_service_warnings`
- `travel_service_hops`: `travel_service_hops_follows_lanes`, `travel_service_hops_jetty_m`, `travel_service_hops_follows_bodies`, `travel_service_hops_lane_depth_m`
- `travel_station`: `travel_station_berth`, `travel_station_operator`
- `travel_settings`: `travel_settings_operator_model_canon`, `travel_settings_operator_model_extrapolated`, `travel_settings_policy`, `travel_settings_vocabulary`
- `travel_settings_vocabulary`: `travel_settings_vocabulary_items`
- `water_crossing`: `water_crossing_banks`, `water_crossing_serves_routes`, `water_crossing_settings`
- `race`: `race_skill_bonus`, `race_effect`, `race_power`, `race_base_attribute`
- `class`: `class_favoured_attributes`, `class_majors`, `class_minors`
- `birthsign`: `birthsign_effects`, `birthsign_powers`, `birthsign_spells`
- `hydrology_river`: `hydrology_river_reach`
- `hydrology_reach`: `hydrology_reach_upstream`, `hydrology_reach_point`
- `hydrology_junction`: `hydrology_junction_inflow`
- `hydrology_body`: `hydrology_body_inflow`, `hydrology_body_approved_merged`, `hydrology_body_radius`
- `region_class`: `region_class_eco_override`
- `region_class_override`: `region_class_override_point`, `region_class_override_applies`
- Also `region`, `marker` and `climate` (the region lookup, the map markers, the province climate row).
- Lookups with no parent: `value_band`, `danger_band`, `day_phase`, `schedule_purpose`, `activity`, `interact_kind`, `sex`, `record_status`, `doom_tier`, `hostility_stance`, `sense`, `pocket`, `owing_kind`, `cost_tier`, `verb_tag`, `touch_access`, `line_type`, `culture_level`, `formality`, `opinion_class`, `specialisation`, `glossary_form`, `minor_waterway_settings`, `travel_craft`, `travel_harbour_station`, `travel_road_edge`, `travel_rootway`, `travel_transfer_edge`, `travel_settings`.
