-- The world's relational schema (decision 0030). The single description of the world's data; the
-- guide is docs/design/world/98-data-model.md. Committed form: world/db/<table>.jsonl, one row per
-- line, columns in schema order, sorted by primary key; read and written only through
-- tools/argonia_world/db.py. Conventions: ids are the old stable id strings; a child table's key
-- is its parent's key plus `ord` (list position) or the map key; BOOLEAN is 0/1.

-- == Lookups: one row per allowed value of an enumeration ==

-- Lookup: the kinds of place socket (old 0103 §5): The vocabulary in which every place socket is written (0103
-- decision 5). compile_settlement refuses a socket kind, activity, day phase, schedule purpose, item class, container
-- class or fill rule that is not listed here. Each item class names the vanilla mesh folder or file that supplies its
-- meshes. A socket therefore cannot promise an item that has no asset.
CREATE TABLE "socket_kind" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of value band.
CREATE TABLE "value_band" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of danger band.
CREATE TABLE "danger_band" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the day phases a schedule names (packages/world-time/src/clock.ts DayPhase (world 8a dayPhase())).
CREATE TABLE "day_phase" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of schedule purpose.
CREATE TABLE "schedule_purpose" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of activity.
CREATE TABLE "activity" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of interact kind.
CREATE TABLE "interact_kind" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of sex.
CREATE TABLE "sex" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of faction kind.
CREATE TABLE "faction_kind" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of record status.
CREATE TABLE "record_status" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of doom tier.
CREATE TABLE "doom_tier" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of npc kind.
CREATE TABLE "npc_kind" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of hostility stance.
CREATE TABLE "hostility_stance" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of npc depth.
CREATE TABLE "npc_depth" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of asset status.
CREATE TABLE "asset_status" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of sense.
CREATE TABLE "sense" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of item kind.
CREATE TABLE "item_kind" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of pocket.
CREATE TABLE "pocket" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of lock kind.
CREATE TABLE "lock_kind" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of lock class.
CREATE TABLE "lock_class" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of owner kind.
CREATE TABLE "owner_kind" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of deed kind.
CREATE TABLE "deed_kind" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of rumour pool kind.
CREATE TABLE "rumour_pool_kind" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of document kind.
CREATE TABLE "document_kind" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of creature kind.
CREATE TABLE "creature_kind" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of owing kind.
CREATE TABLE "owing_kind" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of quest group.
CREATE TABLE "quest_group" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of region.
CREATE TABLE "region" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of quest status.
CREATE TABLE "quest_status" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of cost tier.
CREATE TABLE "cost_tier" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of verb tag.
CREATE TABLE "verb_tag" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of quest shape.
CREATE TABLE "quest_shape" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of touch access.
CREATE TABLE "touch_access" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of topic class.
CREATE TABLE "topic_class" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of line type.
CREATE TABLE "line_type" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of culture level.
CREATE TABLE "culture_level" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of formality.
CREATE TABLE "formality" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of opinion class.
CREATE TABLE "opinion_class" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of route mode.
CREATE TABLE "route_mode" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of route class.
CREATE TABLE "route_class" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of specialisation.
CREATE TABLE "specialisation" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- Lookup: the allowed values of skill family.
CREATE TABLE "skill_family" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT
);

-- == faction ==

-- Home of every faction: name, kind, status, how it is joined and left, its doom tier.
CREATE TABLE "faction" (
  "id" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "kind" TEXT NOT NULL REFERENCES "faction_kind"("id"),
  "status" TEXT NOT NULL REFERENCES "record_status"("id"),
  "notes" TEXT NOT NULL,
  "standing_joinable" BOOLEAN CHECK ("standing_joinable" IN (0, 1)),
  "standing_rank_ladder" TEXT,
  "standing_doom_default" TEXT REFERENCES "doom_tier"("id"),
  "standing_doom_by_rank_senior" TEXT REFERENCES "doom_tier"("id"),
  "standing_join_how" TEXT,
  "standing_join_entry_quest" TEXT REFERENCES "quest"("id"),
  "standing_join_refusal" TEXT,
  "standing_expel_applies" BOOLEAN CHECK ("standing_expel_applies" IN (0, 1)),
  "standing_join_sponsor_role" TEXT,
  "standing_join_sponsor_npc" TEXT REFERENCES "npc"("id"),
  PRIMARY KEY ("id")
);

-- Home of one row per element of `sources` of each faction row (ordered by `ord` where it has one).
CREATE TABLE "faction_source" (
  "faction_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("faction_id", "ord"),
  FOREIGN KEY ("faction_id") REFERENCES "faction" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `standing.join.sources` of each faction row (ordered by `ord` where it has one).
CREATE TABLE "faction_standing_join_sources" (
  "faction_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("faction_id", "ord"),
  FOREIGN KEY ("faction_id") REFERENCES "faction" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `standing.expel.causes` of each faction row (ordered by `ord` where it has one).
CREATE TABLE "faction_standing_expel_causes" (
  "faction_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("faction_id", "ord"),
  FOREIGN KEY ("faction_id") REFERENCES "faction" ("id") ON DELETE CASCADE
);

-- Home of the optional block `standing.expel.cost` of each faction row (ordered by `ord` where it has one).
CREATE TABLE "faction_standing_expel_cost" (
  "faction_id" TEXT NOT NULL,
  "rank" TEXT NOT NULL,
  "disposition" TEXT NOT NULL,
  PRIMARY KEY ("faction_id"),
  FOREIGN KEY ("faction_id") REFERENCES "faction" ("id") ON DELETE CASCADE
);

-- Home of the optional block `standing.expel.return` of each faction row (ordered by `ord` where it has one).
CREATE TABLE "faction_standing_expel_return" (
  "faction_id" TEXT NOT NULL,
  "allowed" BOOLEAN NOT NULL CHECK ("allowed" IN (0, 1)),
  PRIMARY KEY ("faction_id"),
  FOREIGN KEY ("faction_id") REFERENCES "faction" ("id") ON DELETE CASCADE
);

-- Home of one row per key of `standing.expel.unstated` of each faction row (ordered by `ord` where it has one).
CREATE TABLE "faction_standing_expel_unstated" (
  "faction_id" TEXT NOT NULL,
  "field" TEXT NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("faction_id", "field"),
  FOREIGN KEY ("faction_id") REFERENCES "faction" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `standing.expel.sources` of each faction row (ordered by `ord` where it has one).
CREATE TABLE "faction_standing_expel_sources" (
  "faction_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("faction_id", "ord"),
  FOREIGN KEY ("faction_id") REFERENCES "faction" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `standing.join.requires.questState` of each faction row (ordered by `ord` where it
-- has one).
CREATE TABLE "faction_standing_join_requires_quest_state" (
  "faction_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("faction_id", "ord"),
  FOREIGN KEY ("faction_id") REFERENCES "faction" ("id") ON DELETE CASCADE
);

-- == faction_reaction ==

-- Home of how one faction's members regard another's (disposition), symmetric or not.
CREATE TABLE "faction_reaction" (
  "a" TEXT NOT NULL,
  "b" TEXT NOT NULL,
  "disposition" INTEGER NOT NULL,
  "symmetric" BOOLEAN NOT NULL CHECK ("symmetric" IN (0, 1)),
  "why" TEXT NOT NULL,
  PRIMARY KEY ("a", "b")
);

-- == rank_ladder ==

-- Home of each rank ladder: its ranks in order and the reputation each needs.
CREATE TABLE "rank_ladder" (
  "id" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- Home of one row per element of `ranks` of each rank_ladder row (ordered by `ord` where it has one).
CREATE TABLE "rank_ladder_rank" (
  "rank_ladder_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "rank" TEXT NOT NULL,
  "reputation_at_least" INTEGER NOT NULL,
  PRIMARY KEY ("rank_ladder_id", "ord"),
  FOREIGN KEY ("rank_ladder_id") REFERENCES "rank_ladder" ("id") ON DELETE CASCADE
);

-- == faction_rules ==

-- Home of the faction system's single set of numbers (one row): ranges, member dispositions, crime weights against
-- members, doom by role.
CREATE TABLE "faction_rules" (
  "id" TEXT NOT NULL,
  "reputation_range_x" INTEGER NOT NULL,
  "reputation_range_y" INTEGER NOT NULL,
  "disposition_range_x" INTEGER NOT NULL,
  "disposition_range_y" INTEGER NOT NULL,
  "expelled_disposition" INTEGER NOT NULL,
  "reputation_weight" REAL NOT NULL,
  "crime_witnessed_multiplier" INTEGER NOT NULL,
  "killable" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- Home of one row per key of `memberDisposition` of each faction_rules row (ordered by `ord` where it has one).
CREATE TABLE "faction_rules_member_disposition" (
  "faction_rules_id" TEXT NOT NULL,
  "rank" TEXT NOT NULL,
  "value" INTEGER NOT NULL,
  PRIMARY KEY ("faction_rules_id", "rank"),
  FOREIGN KEY ("faction_rules_id") REFERENCES "faction_rules" ("id") ON DELETE CASCADE
);

-- Home of one row per key of `crimeAgainstMember` of each faction_rules row (ordered by `ord` where it has one).
CREATE TABLE "faction_rules_crime_against_member" (
  "faction_rules_id" TEXT NOT NULL,
  "crime" TEXT NOT NULL,
  "value" INTEGER NOT NULL,
  PRIMARY KEY ("faction_rules_id", "crime"),
  FOREIGN KEY ("faction_rules_id") REFERENCES "faction_rules" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `doomTiers` of each faction_rules row (ordered by `ord` where it has one).
CREATE TABLE "faction_rules_doom_tier" (
  "faction_rules_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL REFERENCES "doom_tier"("id"),
  PRIMARY KEY ("faction_rules_id", "ord"),
  FOREIGN KEY ("faction_rules_id") REFERENCES "faction_rules" ("id") ON DELETE CASCADE
);

-- Home of one row per key of `doomByRole` of each faction_rules row (ordered by `ord` where it has one).
CREATE TABLE "faction_rules_doom_by_role" (
  "faction_rules_id" TEXT NOT NULL,
  "role" TEXT NOT NULL,
  "value" TEXT NOT NULL REFERENCES "doom_tier"("id"),
  PRIMARY KEY ("faction_rules_id", "role"),
  FOREIGN KEY ("faction_rules_id") REFERENCES "faction_rules" ("id") ON DELETE CASCADE
);

-- == npc ==

-- Home of every person and creature placed in the world (decision 0030: people): who they are, where they live and
-- work, their day, senses, loot, look and asset status.
CREATE TABLE "npc" (
  "id" TEXT NOT NULL,
  "kind" TEXT NOT NULL REFERENCES "npc_kind"("id"),
  "name" TEXT NOT NULL,
  "role" TEXT NOT NULL,
  "archetype" TEXT,
  "hostility" TEXT NOT NULL REFERENCES "hostility_stance"("id"),
  "home_place_id" TEXT NOT NULL REFERENCES "place"("id"),
  "home_slot_index" INTEGER,
  "home_home_socket_id" TEXT,
  "home_home_activity" TEXT,
  "home_post" TEXT,
  "dialogue_set_id" TEXT REFERENCES "npc"("id"),
  "doom_tier" TEXT NOT NULL REFERENCES "doom_tier"("id"),
  "status" TEXT NOT NULL REFERENCES "record_status"("id"),
  "notes" TEXT NOT NULL,
  "species" TEXT,
  "nav" TEXT,
  "look_model_set" TEXT,
  "table_row" TEXT,
  "race" TEXT REFERENCES "race"("id"),
  "sex" TEXT REFERENCES "sex"("id"),
  "depth" TEXT REFERENCES "npc_depth"("id"),
  "name_form" TEXT,
  "look_body" TEXT,
  "look_face_donor" TEXT,
  "look_skin_tint_donor" TEXT,
  "look_hair_tint_donor" TEXT,
  "look_body_weight" REAL,
  "look_outfit" TEXT,
  "asset_availability_status" TEXT REFERENCES "asset_status"("id"),
  "asset_availability_via" TEXT,
  "asset_availability_notes" TEXT,
  "trade_class" TEXT,
  "caster" BOOLEAN CHECK ("caster" IN (0, 1)),
  PRIMARY KEY ("id")
);

-- Home of the optional block `statblock` of each npc row (ordered by `ord` where it has one).
CREATE TABLE "npc_statblock" (
  "npc_id" TEXT NOT NULL,
  "class" TEXT NOT NULL,
  "band" TEXT NOT NULL,
  "position" REAL NOT NULL,
  "loadout" TEXT,
  "respawn" TEXT NOT NULL,
  "soul_trappable" BOOLEAN NOT NULL CHECK ("soul_trappable" IN (0, 1)),
  "class_id" TEXT REFERENCES "class"("id"),
  PRIMARY KEY ("npc_id"),
  FOREIGN KEY ("npc_id") REFERENCES "npc" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `statblock.variants` of each npc_statblock row (ordered by `ord` where it has one).
CREATE TABLE "npc_statblock_variants" (
  "npc_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  PRIMARY KEY ("npc_id", "ord"),
  FOREIGN KEY ("npc_id") REFERENCES "npc_statblock" ("npc_id") ON DELETE CASCADE
);

-- Home of one row per element of `factions` of each npc row (ordered by `ord` where it has one).
CREATE TABLE "npc_faction" (
  "npc_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "faction_id" TEXT NOT NULL REFERENCES "faction"("id"),
  PRIMARY KEY ("npc_id", "ord"),
  FOREIGN KEY ("npc_id") REFERENCES "npc" ("id") ON DELETE CASCADE
);

-- Home of the optional block `fightFleeAlarm` of each npc row (ordered by `ord` where it has one).
CREATE TABLE "npc_fight_flee_alarm" (
  "npc_id" TEXT NOT NULL,
  "fight" INTEGER NOT NULL CHECK ("fight" BETWEEN 0 AND 100),
  "flee" INTEGER NOT NULL CHECK ("flee" BETWEEN 0 AND 100),
  "alarm" INTEGER NOT NULL CHECK ("alarm" BETWEEN 0 AND 100),
  PRIMARY KEY ("npc_id"),
  FOREIGN KEY ("npc_id") REFERENCES "npc" ("id") ON DELETE CASCADE
);

-- Home of the optional block `home.bed` of each npc row (ordered by `ord` where it has one).
CREATE TABLE "npc_home_bed" (
  "npc_id" TEXT NOT NULL,
  "socket_id" TEXT,
  "activity" TEXT NOT NULL,
  "place_id" TEXT REFERENCES "place"("id"),
  PRIMARY KEY ("npc_id"),
  FOREIGN KEY ("npc_id") REFERENCES "npc" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `home.work` of each npc row (ordered by `ord` where it has one).
CREATE TABLE "npc_work" (
  "npc_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "socket_id" TEXT NOT NULL,
  "activity" TEXT NOT NULL,
  PRIMARY KEY ("npc_id", "ord"),
  FOREIGN KEY ("npc_id") REFERENCES "npc" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `day.roleExceptions` of each npc row (ordered by `ord` where it has one).
CREATE TABLE "npc_role_exception" (
  "npc_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("npc_id", "ord"),
  FOREIGN KEY ("npc_id") REFERENCES "npc" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `day.blocks` of each npc row (ordered by `ord` where it has one).
CREATE TABLE "npc_day_block" (
  "npc_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "from" TEXT NOT NULL,
  "to" TEXT NOT NULL,
  "spot" TEXT NOT NULL,
  "activity" TEXT NOT NULL,
  PRIMARY KEY ("npc_id", "ord"),
  FOREIGN KEY ("npc_id") REFERENCES "npc" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `services` of each npc row (ordered by `ord` where it has one).
CREATE TABLE "npc_service" (
  "npc_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("npc_id", "ord"),
  FOREIGN KEY ("npc_id") REFERENCES "npc" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `questHooks` of each npc row (ordered by `ord` where it has one).
CREATE TABLE "npc_quest_hook" (
  "npc_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  PRIMARY KEY ("npc_id", "ord"),
  FOREIGN KEY ("npc_id") REFERENCES "npc" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `sources` of each npc row (ordered by `ord` where it has one).
CREATE TABLE "npc_source" (
  "npc_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("npc_id", "ord"),
  FOREIGN KEY ("npc_id") REFERENCES "npc" ("id") ON DELETE CASCADE
);

-- Home of the optional block `den` of each npc row (ordered by `ord` where it has one).
CREATE TABLE "npc_den" (
  "npc_id" TEXT NOT NULL,
  "socket_id" TEXT NOT NULL,
  "activity" TEXT NOT NULL,
  PRIMARY KEY ("npc_id"),
  FOREIGN KEY ("npc_id") REFERENCES "npc" ("id") ON DELETE CASCADE
);

-- Home of the optional block `territory` of each npc row (ordered by `ord` where it has one).
CREATE TABLE "npc_territory" (
  "npc_id" TEXT NOT NULL,
  "area_id" TEXT NOT NULL REFERENCES "place"("id"),
  "radius_m" INTEGER NOT NULL,
  PRIMARY KEY ("npc_id"),
  FOREIGN KEY ("npc_id") REFERENCES "npc" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `territory.socketIds` of each npc_territory row (ordered by `ord` where it has one).
CREATE TABLE "npc_territory_socket_ids" (
  "npc_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("npc_id", "ord"),
  FOREIGN KEY ("npc_id") REFERENCES "npc_territory" ("npc_id") ON DELETE CASCADE
);

-- Home of the optional block `notice` of each npc row (ordered by `ord` where it has one).
CREATE TABLE "npc_notice" (
  "npc_id" TEXT NOT NULL,
  "sight_m" INTEGER NOT NULL,
  "cone_deg" INTEGER NOT NULL,
  "hearing_m" INTEGER NOT NULL,
  "scent_m" INTEGER NOT NULL,
  PRIMARY KEY ("npc_id"),
  FOREIGN KEY ("npc_id") REFERENCES "npc" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `notice.senses` of each npc_notice row (ordered by `ord` where it has one).
CREATE TABLE "npc_notice_senses" (
  "npc_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL REFERENCES "sense"("id"),
  PRIMARY KEY ("npc_id", "ord"),
  FOREIGN KEY ("npc_id") REFERENCES "npc_notice" ("npc_id") ON DELETE CASCADE
);

-- Home of the optional block `loot` of each npc row (ordered by `ord` where it has one).
CREATE TABLE "npc_loot" (
  "npc_id" TEXT NOT NULL,
  PRIMARY KEY ("npc_id"),
  FOREIGN KEY ("npc_id") REFERENCES "npc" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `loot.items` of each npc_loot row (ordered by `ord` where it has one).
CREATE TABLE "npc_loot_items" (
  "npc_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "item" TEXT NOT NULL REFERENCES "item"("id"),
  "count" INTEGER NOT NULL,
  "condition" REAL,
  PRIMARY KEY ("npc_id", "ord"),
  FOREIGN KEY ("npc_id") REFERENCES "npc_loot" ("npc_id") ON DELETE CASCADE
);

-- Home of one row per element of `loot.frozenFrom` of each npc_loot row (ordered by `ord` where it has one).
CREATE TABLE "npc_loot_frozen_from" (
  "npc_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("npc_id", "ord"),
  FOREIGN KEY ("npc_id") REFERENCES "npc_loot" ("npc_id") ON DELETE CASCADE
);

-- Home of one row per element of `signatureSpells` of each npc row (ordered by `ord` where it has one).
CREATE TABLE "npc_signature_spell" (
  "npc_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("npc_id", "ord"),
  FOREIGN KEY ("npc_id") REFERENCES "npc" ("id") ON DELETE CASCADE
);

-- == item ==

-- Home of every item: name, kind, pocket, weight, value, ladder band, model, effects, the set it belongs to and what
-- it does.
CREATE TABLE "item" (
  "id" TEXT NOT NULL,
  "status" TEXT NOT NULL REFERENCES "record_status"("id"),
  "name" TEXT NOT NULL,
  "kind" TEXT NOT NULL REFERENCES "item_kind"("id"),
  "pocket" TEXT NOT NULL REFERENCES "pocket"("id"),
  "unique" BOOLEAN NOT NULL CHECK ("unique" IN (0, 1)),
  "verb" TEXT NOT NULL,
  "stackable" BOOLEAN NOT NULL CHECK ("stackable" IN (0, 1)),
  "weight_kg" REAL NOT NULL,
  "value" INTEGER NOT NULL,
  "ladder_band" TEXT NOT NULL,
  "ladder_position" REAL NOT NULL,
  "model" TEXT,
  "icon" TEXT NOT NULL,
  "subkind" TEXT,
  "description" TEXT NOT NULL,
  "why_here" TEXT,
  "notes" TEXT NOT NULL,
  "asset_availability_status" TEXT NOT NULL REFERENCES "asset_status"("id"),
  "asset_availability_via" TEXT NOT NULL,
  "asset_availability_notes" TEXT NOT NULL,
  "set" TEXT REFERENCES "item_set"("id"),
  "value_from" TEXT,
  "asset_availability_model" TEXT,
  "text_ref" TEXT,
  "premise" TEXT,
  "teaches" TEXT,
  "quest" TEXT REFERENCES "quest"("id"),
  "shaft" TEXT,
  "model_male" TEXT,
  "model_female" TEXT,
  "harvested_from" TEXT,
  "cooks_into" TEXT REFERENCES "item"("id"),
  "asset_availability_plugin" TEXT,
  "lock" TEXT REFERENCES "lock"("id"),
  "bound" BOOLEAN CHECK ("bound" IN (0, 1)),
  "quality" REAL,
  "material_from" TEXT,
  "spell_id" TEXT,
  "rare_fortify" BOOLEAN CHECK ("rare_fortify" IN (0, 1)),
  "carried_by" TEXT REFERENCES "npc"("id"),
  "worn" TEXT,
  PRIMARY KEY ("id")
);

-- Home of the optional block `condition` of each item row (ordered by `ord` where it has one).
CREATE TABLE "item_condition" (
  "item_id" TEXT NOT NULL,
  "max" INTEGER NOT NULL,
  "wear" TEXT NOT NULL,
  "wear_per_use" INTEGER,
  PRIMARY KEY ("item_id"),
  FOREIGN KEY ("item_id") REFERENCES "item" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `sources` of each item row (ordered by `ord` where it has one).
CREATE TABLE "item_source" (
  "item_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("item_id", "ord"),
  FOREIGN KEY ("item_id") REFERENCES "item" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `assetAvailability.records` of each item row (ordered by `ord` where it has one).
CREATE TABLE "item_asset_record" (
  "item_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("item_id", "ord"),
  FOREIGN KEY ("item_id") REFERENCES "item" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `effects` of each item row (ordered by `ord` where it has one).
CREATE TABLE "item_effect" (
  "item_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT,
  "effect_id" TEXT,
  "magnitude" REAL,
  "duration_seconds" REAL,
  PRIMARY KEY ("item_id", "ord"),
  FOREIGN KEY ("item_id") REFERENCES "item" ("id") ON DELETE CASCADE
);

-- Home of the optional block `incendiary` of each item row (ordered by `ord` where it has one).
CREATE TABLE "item_incendiary" (
  "item_id" TEXT NOT NULL,
  "effect_id" TEXT NOT NULL,
  "magnitude" INTEGER NOT NULL,
  "duration_seconds" INTEGER NOT NULL,
  "area_metres" INTEGER NOT NULL,
  "source" TEXT NOT NULL,
  PRIMARY KEY ("item_id"),
  FOREIGN KEY ("item_id") REFERENCES "item" ("id") ON DELETE CASCADE
);

-- Home of the optional block `recipe` of each item row (ordered by `ord` where it has one).
CREATE TABLE "item_recipe" (
  "item_id" TEXT NOT NULL,
  "station" TEXT NOT NULL,
  "tier" INTEGER NOT NULL,
  PRIMARY KEY ("item_id"),
  FOREIGN KEY ("item_id") REFERENCES "item" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `recipe.inputs` of each item_recipe row (ordered by `ord` where it has one).
CREATE TABLE "item_recipe_inputs" (
  "item_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "input_item_id" TEXT NOT NULL REFERENCES "item"("id"),
  "count" INTEGER NOT NULL,
  PRIMARY KEY ("item_id", "ord"),
  FOREIGN KEY ("item_id") REFERENCES "item_recipe" ("item_id") ON DELETE CASCADE
);

-- Home of the optional block `soulGem` of each item row (ordered by `ord` where it has one).
CREATE TABLE "item_soul_gem" (
  "item_id" TEXT NOT NULL,
  "size" TEXT NOT NULL,
  "capacity" INTEGER NOT NULL,
  "filled" BOOLEAN NOT NULL CHECK ("filled" IN (0, 1)),
  "holds" TEXT,
  PRIMARY KEY ("item_id"),
  FOREIGN KEY ("item_id") REFERENCES "item" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `tags` of each item row (ordered by `ord` where it has one).
CREATE TABLE "item_tag" (
  "item_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("item_id", "ord"),
  FOREIGN KEY ("item_id") REFERENCES "item" ("id") ON DELETE CASCADE
);

-- Home of the optional block `enchantment` of each item row (ordered by `ord` where it has one).
CREATE TABLE "item_enchantment" (
  "item_id" TEXT NOT NULL,
  "effect_id" TEXT NOT NULL,
  "magnitude" INTEGER NOT NULL,
  "duration" INTEGER NOT NULL,
  "charge_max" INTEGER NOT NULL,
  PRIMARY KEY ("item_id"),
  FOREIGN KEY ("item_id") REFERENCES "item" ("id") ON DELETE CASCADE
);

-- == item_set ==

-- Home of each material set (wood, iron, ebony...): tier, scales, value per kg, requirement bonus and its materials.
CREATE TABLE "item_set" (
  "id" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "description" TEXT NOT NULL,
  "why_here" TEXT NOT NULL,
  "tier" INTEGER NOT NULL,
  "damage_scale" REAL NOT NULL,
  "weight_scale" REAL NOT NULL,
  "guard_scale" REAL NOT NULL,
  "value_per_kg" INTEGER NOT NULL,
  "armour_class" TEXT,
  PRIMARY KEY ("id")
);

-- Home of one row per element of `sources` of each item_set row (ordered by `ord` where it has one).
CREATE TABLE "item_set_source" (
  "item_set_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("item_set_id", "ord"),
  FOREIGN KEY ("item_set_id") REFERENCES "item_set" ("id") ON DELETE CASCADE
);

-- Home of one row per key of `requirementBonus` of each item_set row (ordered by `ord` where it has one).
CREATE TABLE "item_set_requirement_bonus" (
  "item_set_id" TEXT NOT NULL,
  "attribute" TEXT NOT NULL REFERENCES "attribute"("id"),
  "value" INTEGER NOT NULL,
  PRIMARY KEY ("item_set_id", "attribute"),
  FOREIGN KEY ("item_set_id") REFERENCES "item_set" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `materials` of each item_set row (ordered by `ord` where it has one).
CREATE TABLE "item_set_materials" (
  "item_set_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL REFERENCES "item"("id"),
  PRIMARY KEY ("item_set_id", "ord"),
  FOREIGN KEY ("item_set_id") REFERENCES "item_set" ("id") ON DELETE CASCADE
);

-- Home of one row per key of `bonusDamage` of each item_set row (ordered by `ord` where it has one).
CREATE TABLE "item_set_bonus_damage" (
  "item_set_id" TEXT NOT NULL,
  "element" TEXT NOT NULL,
  "value" INTEGER NOT NULL,
  PRIMARY KEY ("item_set_id", "element"),
  FOREIGN KEY ("item_set_id") REFERENCES "item_set" ("id") ON DELETE CASCADE
);

-- == lock ==

-- Home of every lock: level, key, what it opens, its class and owner.
CREATE TABLE "lock" (
  "id" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "kind" TEXT NOT NULL REFERENCES "lock_kind"("id"),
  "status" TEXT NOT NULL REFERENCES "record_status"("id"),
  "notes" TEXT NOT NULL,
  "level" INTEGER NOT NULL CHECK ("level" BETWEEN 0 AND 100),
  "key" TEXT REFERENCES "item"("id"),
  "opens_place" TEXT NOT NULL,
  "opens_ref" TEXT NOT NULL,
  "class" TEXT NOT NULL REFERENCES "lock_class"("id"),
  "owner_kind" TEXT NOT NULL REFERENCES "owner_kind"("id"),
  "owner_id" TEXT NOT NULL,
  "trap" TEXT,
  "spell_key" TEXT,
  PRIMARY KEY ("id")
);

-- Home of one row per element of `sources` of each lock row (ordered by `ord` where it has one).
CREATE TABLE "lock_source" (
  "lock_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("lock_id", "ord"),
  FOREIGN KEY ("lock_id") REFERENCES "lock" ("id") ON DELETE CASCADE
);

-- == deed ==

-- Home of every deed counter (the silent-unlock counters, old 0039).
CREATE TABLE "deed" (
  "id" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "kind" TEXT NOT NULL REFERENCES "deed_kind"("id"),
  "status" TEXT NOT NULL REFERENCES "record_status"("id"),
  "notes" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- Home of one row per element of `sources` of each deed row (ordered by `ord` where it has one).
CREATE TABLE "deed_source" (
  "deed_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("deed_id", "ord"),
  FOREIGN KEY ("deed_id") REFERENCES "deed" ("id") ON DELETE CASCADE
);

-- == rumour_pool ==

-- Home of every rumour pool a place draws on.
CREATE TABLE "rumour_pool" (
  "id" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "kind" TEXT NOT NULL REFERENCES "rumour_pool_kind"("id"),
  "status" TEXT NOT NULL REFERENCES "record_status"("id"),
  "notes" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- Home of one row per element of `sources` of each rumour_pool row (ordered by `ord` where it has one).
CREATE TABLE "rumour_pool_source" (
  "rumour_pool_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("rumour_pool_id", "ord"),
  FOREIGN KEY ("rumour_pool_id") REFERENCES "rumour_pool" ("id") ON DELETE CASCADE
);

-- == document ==

-- Home of every readable document: its text reference, the item that carries it, its leaves and what it teaches.
CREATE TABLE "document" (
  "id" TEXT NOT NULL,
  "text_ref" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "kind" TEXT NOT NULL REFERENCES "document_kind"("id"),
  "status" TEXT NOT NULL REFERENCES "record_status"("id"),
  "item" TEXT NOT NULL REFERENCES "item"("id"),
  "notes" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- Home of one row per element of `leaves` of each document row (ordered by `ord` where it has one).
CREATE TABLE "document_leaf" (
  "document_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("document_id", "ord"),
  FOREIGN KEY ("document_id") REFERENCES "document" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `sources` of each document row (ordered by `ord` where it has one).
CREATE TABLE "document_source" (
  "document_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("document_id", "ord"),
  FOREIGN KEY ("document_id") REFERENCES "document" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `teaches` of each document row (ordered by `ord` where it has one).
CREATE TABLE "document_teaches" (
  "document_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("document_id", "ord"),
  FOREIGN KEY ("document_id") REFERENCES "document" ("id") ON DELETE CASCADE
);

-- == creature ==

-- Home of every creature kind: regions, bands, habitat, stat block, senses, reaction.
CREATE TABLE "creature" (
  "id" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "kind" TEXT NOT NULL REFERENCES "creature_kind"("id"),
  "status" TEXT NOT NULL REFERENCES "record_status"("id"),
  "notes" TEXT NOT NULL,
  "habitat_ground" TEXT NOT NULL,
  "habitat_water" TEXT NOT NULL,
  "habitat_network" TEXT NOT NULL,
  "hostility" TEXT NOT NULL REFERENCES "hostility_stance"("id"),
  "reaction_on_notice" TEXT NOT NULL,
  "reaction_note" TEXT NOT NULL,
  "den_type" TEXT NOT NULL,
  "den_why" TEXT NOT NULL,
  "den_note" TEXT NOT NULL,
  "den_activity" TEXT NOT NULL,
  "territory_radius_m" INTEGER NOT NULL,
  "territory_network" TEXT NOT NULL,
  "territory_group_kind" TEXT NOT NULL,
  "territory_group_min" INTEGER NOT NULL,
  "territory_group_max" INTEGER NOT NULL,
  "territory_per_stretch_min" INTEGER NOT NULL,
  "territory_per_stretch_max" INTEGER NOT NULL,
  "territory_per_stretch_unit" TEXT NOT NULL,
  "day_active" TEXT NOT NULL,
  "diet" TEXT NOT NULL,
  "eaten_by" TEXT NOT NULL,
  "harvest" TEXT NOT NULL,
  "why_here" TEXT NOT NULL,
  "domestic" BOOLEAN NOT NULL CHECK ("domestic" IN (0, 1)),
  "hand_authored_only" BOOLEAN NOT NULL CHECK ("hand_authored_only" IN (0, 1)),
  "look_model_set" TEXT,
  "sourcing_status" TEXT NOT NULL,
  "sourcing_via" TEXT NOT NULL,
  "sourcing_notes" TEXT NOT NULL,
  "sourcing_redesign" TEXT,
  "table_row" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- Home of one row per element of `sources` of each creature row (ordered by `ord` where it has one).
CREATE TABLE "creature_source" (
  "creature_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("creature_id", "ord"),
  FOREIGN KEY ("creature_id") REFERENCES "creature" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `regions` of each creature row (ordered by `ord` where it has one).
CREATE TABLE "creature_region" (
  "creature_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("creature_id", "ord"),
  FOREIGN KEY ("creature_id") REFERENCES "creature" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `bands` of each creature row (ordered by `ord` where it has one).
CREATE TABLE "creature_band" (
  "creature_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("creature_id", "ord"),
  FOREIGN KEY ("creature_id") REFERENCES "creature" ("id") ON DELETE CASCADE
);

-- Home of the optional block `statblock` of each creature row (ordered by `ord` where it has one).
CREATE TABLE "creature_statblock" (
  "creature_id" TEXT NOT NULL,
  "class" TEXT NOT NULL,
  "band" TEXT NOT NULL,
  "position" REAL NOT NULL,
  "respawn" TEXT NOT NULL,
  "soul_trappable" BOOLEAN NOT NULL CHECK ("soul_trappable" IN (0, 1)),
  PRIMARY KEY ("creature_id"),
  FOREIGN KEY ("creature_id") REFERENCES "creature" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `statblock.variants` of each creature_statblock row (ordered by `ord` where it has
-- one).
CREATE TABLE "creature_statblock_variants" (
  "creature_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("creature_id", "ord"),
  FOREIGN KEY ("creature_id") REFERENCES "creature_statblock" ("creature_id") ON DELETE CASCADE
);

-- Home of the optional block `fightFleeAlarm` of each creature row (ordered by `ord` where it has one).
CREATE TABLE "creature_fight_flee_alarm" (
  "creature_id" TEXT NOT NULL,
  "fight" INTEGER NOT NULL,
  "flee" INTEGER NOT NULL,
  "alarm" INTEGER NOT NULL,
  PRIMARY KEY ("creature_id"),
  FOREIGN KEY ("creature_id") REFERENCES "creature" ("id") ON DELETE CASCADE
);

-- Home of the optional block `notice` of each creature row (ordered by `ord` where it has one).
CREATE TABLE "creature_notice" (
  "creature_id" TEXT NOT NULL,
  "sight_m" INTEGER NOT NULL,
  "cone_deg" INTEGER NOT NULL,
  "hearing_m" INTEGER NOT NULL,
  "scent_m" INTEGER NOT NULL,
  PRIMARY KEY ("creature_id"),
  FOREIGN KEY ("creature_id") REFERENCES "creature" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `notice.senses` of each creature_notice row (ordered by `ord` where it has one).
CREATE TABLE "creature_notice_senses" (
  "creature_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL REFERENCES "sense"("id"),
  PRIMARY KEY ("creature_id", "ord"),
  FOREIGN KEY ("creature_id") REFERENCES "creature_notice" ("creature_id") ON DELETE CASCADE
);

-- Home of one row per element of `day.roleExceptions` of each creature row (ordered by `ord` where it has one).
CREATE TABLE "creature_day_role_exceptions" (
  "creature_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  PRIMARY KEY ("creature_id", "ord"),
  FOREIGN KEY ("creature_id") REFERENCES "creature" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `day.blocks` of each creature row (ordered by `ord` where it has one).
CREATE TABLE "creature_day_blocks" (
  "creature_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "from" TEXT NOT NULL,
  "to" TEXT NOT NULL,
  "spot" TEXT NOT NULL,
  "activity" TEXT NOT NULL,
  PRIMARY KEY ("creature_id", "ord"),
  FOREIGN KEY ("creature_id") REFERENCES "creature" ("id") ON DELETE CASCADE
);

-- == owing_region ==

-- Home of each region's Owing ledger: assessor, crime rates, custody and amnesty hours (old 0039, 0151).
CREATE TABLE "owing_region" (
  "id" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "kind" TEXT NOT NULL REFERENCES "owing_kind"("id"),
  "status" TEXT NOT NULL REFERENCES "record_status"("id"),
  "notes" TEXT NOT NULL,
  "region" TEXT NOT NULL,
  "region_name" TEXT NOT NULL,
  "region_name_source" TEXT NOT NULL,
  "assessor" TEXT,
  "rates_trespass" INTEGER NOT NULL,
  "rates_theft_per_value" INTEGER NOT NULL,
  "rates_theft_min" INTEGER NOT NULL,
  "rates_pickpocket" INTEGER NOT NULL,
  "rates_assault" INTEGER NOT NULL,
  "rates_murder" INTEGER NOT NULL,
  "custody_hours_per_nushmeeko" REAL NOT NULL,
  "amnesty_hours" INTEGER NOT NULL,
  "rate_note" TEXT NOT NULL,
  "assessor_reason" TEXT,
  PRIMARY KEY ("id")
);

-- Home of one row per element of `sources` of each owing_region row (ordered by `ord` where it has one).
CREATE TABLE "owing_region_source" (
  "owing_region_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("owing_region_id", "ord"),
  FOREIGN KEY ("owing_region_id") REFERENCES "owing_region" ("id") ON DELETE CASCADE
);

-- == marker ==

-- Home of every map marker id.
CREATE TABLE "marker" (
  "id" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- == place ==

-- Home of every place of the catalogue (decision 0030: places): what it is, why it exists, its siting, culture,
-- danger, vibe, contents, interior, hostility and quest hooks; one row per place, its region a column, never a file.
CREATE TABLE "place" (
  "id" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "classification_class" TEXT,
  "classification_family" TEXT,
  "classification_type" TEXT,
  "classification_variant" TEXT,
  "classification_magnitude" TEXT,
  "status" TEXT REFERENCES "record_status"("id"),
  "season" TEXT,
  "provenance" TEXT,
  "confidence" TEXT,
  "why_founding" TEXT,
  "why_site_advantages" TEXT,
  "why_occupants_motive" TEXT,
  "why_pressures" TEXT,
  "why_would_change_if" TEXT,
  "siting_prefs_water_relation" TEXT,
  "siting_prefs_neighbour_relation" TEXT,
  "culture" TEXT,
  "owner_faction" TEXT,
  "danger_tier" TEXT,
  "approach_danger" TEXT,
  "traversal_fallback" TEXT,
  "effort_to_reach" INTEGER,
  "loot_table_value_tier" TEXT,
  "vibe_silhouette" TEXT,
  "vibe_palette" TEXT,
  "vibe_materials" TEXT,
  "vibe_signature_feature" TEXT,
  "vibe_condition" TEXT,
  "vibe_mood" TEXT,
  "vibe_approach" TEXT,
  "vibe_senses" TEXT,
  "discovery" TEXT,
  "quest_hooks_opportunity" TEXT,
  "quest_hooks_tier_ownership" TEXT,
  "rumour_pool_key" TEXT,
  "complexity_budget" TEXT,
  "importance_tier" INTEGER,
  "place_tier" TEXT,
  "workflow" TEXT,
  "density_layer" TEXT,
  "entrance" TEXT,
  "underwater_access" TEXT,
  "position_u" REAL,
  "position_v" REAL,
  "position_m_x" REAL,
  "position_m_y" REAL,
  "footprint_radius_m" REAL,
  "footprint_source" TEXT,
  "why_site_won" TEXT,
  "plot_facts_landform" TEXT,
  "plot_facts_region_class" TEXT,
  "plot_facts_danger_band" INTEGER,
  "plot_facts_distance_to_route_m" REAL,
  "plot_facts_distance_to_water_m" REAL,
  "plot_facts_water_entity_id" TEXT,
  "plot_facts_water_kind" TEXT,
  "plot_facts_water_level_m" REAL,
  "plot_facts_water_season" TEXT,
  "plot_facts_water_distance_m" REAL,
  "plot_facts_score" REAL,
  "hostility_baseline" TEXT,
  "hostility_owner" TEXT,
  "hostility_clearable" BOOLEAN CHECK ("hostility_clearable" IN (0, 1)),
  "hostility_respawn" TEXT,
  "player_purpose_primary" TEXT,
  "player_purpose_impact" TEXT,
  "player_purpose_hook" TEXT,
  "player_purpose_reviewed" BOOLEAN CHECK ("player_purpose_reviewed" IN (0, 1)),
  "interior_kind" TEXT,
  "interior_family" TEXT,
  "interior_size_band" TEXT,
  "interior_wet_fraction" REAL,
  "interior_entrance_count" INTEGER,
  "interior_exterior_shell",
  "interior_vertical_relationship" TEXT,
  "interior_loop" TEXT,
  "interior_light" TEXT,
  "interior_lock" TEXT,
  "region" TEXT,
  "scour_site_id" TEXT,
  "siting_note" TEXT,
  "siting_prefs_min_depth_m" REAL,
  "design_group" TEXT,
  "singular_claim" TEXT,
  "watch_reason" TEXT,
  "complexity_justification" TEXT,
  "owner_guided" BOOLEAN CHECK ("owner_guided" IN (0, 1)),
  "deferred_why" TEXT,
  "siting_prefs_near_water_entity_id" TEXT,
  "siting_prefs_near_water_max_m" INTEGER,
  "hostility_environmental_danger" BOOLEAN CHECK ("hostility_environmental_danger" IN (0, 1)),
  "reconciliation" TEXT,
  "stronghold_candidate" BOOLEAN CHECK ("stronghold_candidate" IN (0, 1)),
  "reconciliation_note" TEXT,
  "interior_schema_version" INTEGER,
  "reserved_for" TEXT,
  "siting_prefs_preferences_neighbour_relation" TEXT,
  "siting_prefs_preferences_density_gradient" TEXT,
  "deferred_from_status" TEXT,
  "footprint_why" TEXT,
  "deferral_note" TEXT,
  "promoted_why" TEXT,
  "vastei_tutorial_scene" BOOLEAN CHECK ("vastei_tutorial_scene" IN (0, 1)),
  PRIMARY KEY ("id")
);

-- Home of one row per element of `aliases` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_alias" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `eraLayers` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_era_layers" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `sources` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_source" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `sitingPrefs.regionClasses` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_siting_prefs_region_classes" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `sitingPrefs.landformClasses` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_siting_prefs_landform_classes" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `sitingPrefs.hardConstraints` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_siting_prefs_hard_constraints" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `sitingPrefs.preferences` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_siting_prefs_preferences" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `sitingPrefs.scourSiteIds` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_siting_prefs_scour_site_ids" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `relations.dependsOn` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_relations_depends_on" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `relations.supplies` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_relations_supplies" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `relations.rivals` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_relations_rivals" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `relations.patrols` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_relations_patrols" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `relations.tolls` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_relations_tolls" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `relations.visibleFrom` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_relations_visible_from" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `relations.reachedVia` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_relations_reached_via" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `relations.travelServiceEdges` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_relations_travel_service_edges" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `occupants` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_occupants" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `notableNpcSlots` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_notable_npc_slots" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "slot_id" TEXT NOT NULL,
  "role" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `traversalModes` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_traversal_modes" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `lootTable.kinds` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_loot_table_kinds" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `assetPlan` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_asset_plan" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `questHooks.provisions` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_quest_hooks_provisions" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `questHooks.tags` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_quest_hooks_tags" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `deedCounterKeys` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_deed_counter_keys" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `sockets.scene` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_sockets_scene" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `sockets.evidence` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_sockets_evidence" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `sockets.post` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_sockets_post" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `sockets.marks` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_sockets_marks" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `localStateVariants` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_local_state_variants" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT,
  "id" TEXT,
  "when" TEXT,
  "what_changes" TEXT,
  "description" TEXT,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `candidatesConsidered` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_candidates_considered" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "site_id" TEXT NOT NULL,
  "score" REAL NOT NULL,
  "why_lost" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `hostility.flips` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_hostility_flips" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "to" TEXT NOT NULL,
  "when" TEXT NOT NULL REFERENCES "condition"("id"),
  "scope" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `playerPurpose.secondary` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_player_purpose_secondary" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `interior.roomFunctions` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_interior_room_functions" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of the optional block `interior.traversal` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_interior_traversal" (
  "place_id" TEXT NOT NULL,
  "swim_m" INTEGER NOT NULL,
  "dive_m" INTEGER NOT NULL,
  "climb_m" INTEGER NOT NULL,
  "breath_gated" BOOLEAN NOT NULL CHECK ("breath_gated" IN (0, 1)),
  "current" TEXT NOT NULL,
  "dark_fraction" REAL NOT NULL,
  PRIMARY KEY ("place_id"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `interior.combatSpaces` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_interior_combat_spaces" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "scale" TEXT NOT NULL,
  "footing" TEXT NOT NULL,
  "clearance" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `interior.anchorSockets` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_interior_anchor_sockets" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "id" TEXT NOT NULL,
  "kind" TEXT NOT NULL,
  "where_in_interior" TEXT NOT NULL,
  "provision" TEXT,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `contents.creatures` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_contents_creatures" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "slot_id" TEXT NOT NULL,
  "role" TEXT NOT NULL,
  "register_ref" TEXT,
  "count" TEXT NOT NULL,
  "danger" TEXT NOT NULL,
  "where_in_interior" TEXT,
  "note" TEXT,
  "trigger" TEXT,
  "provenance" TEXT,
  "named" BOOLEAN CHECK ("named" IN (0, 1)),
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `contents.npcs` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_contents_npcs" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "slot_id" TEXT NOT NULL,
  "role" TEXT NOT NULL,
  "danger" TEXT,
  "count" TEXT NOT NULL,
  "named" BOOLEAN CHECK ("named" IN (0, 1)),
  "note" TEXT,
  "where_in_interior" TEXT,
  "faction" TEXT,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `contents.loot` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_contents_loot" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "slot_id" TEXT NOT NULL,
  "role" TEXT NOT NULL,
  "payoff" TEXT NOT NULL,
  "value_tier" TEXT NOT NULL,
  "provenance" TEXT,
  "where_in_interior" TEXT,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of the optional block `sitingPrefs.boundTo` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_siting_prefs_bound_to" (
  "place_id" TEXT NOT NULL,
  "place" TEXT NOT NULL,
  "max_m" REAL NOT NULL,
  "why" TEXT,
  PRIMARY KEY ("place_id"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `sitingPrefs.sightlineTo` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_siting_prefs_sightline_to" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `localGroups` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_local_groups" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "name" TEXT NOT NULL,
  "answers_to" TEXT NOT NULL,
  "reason" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `proseRefs` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_prose_refs" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "source_path" TEXT NOT NULL,
  "place_ref" TEXT,
  "faction_ref" TEXT,
  "route_ref" TEXT,
  "service_ref" TEXT,
  "quest_ref" TEXT,
  "item_ref" TEXT,
  "occupant_ref" TEXT,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `services` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_services" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `travelStation.modes` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_travel_station_modes" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `travelStation.destinations` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_travel_station_destinations" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of the optional block `sitingPrefs.nearPoint` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_siting_prefs_near_point" (
  "place_id" TEXT NOT NULL,
  "x" REAL NOT NULL,
  "z" REAL NOT NULL,
  "max_m" REAL NOT NULL,
  PRIMARY KEY ("place_id"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `relationsReserved.reachedVia` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_relations_reserved_reached_via" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `relationsReserved.supplies` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_relations_reserved_supplies" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `interior.factsVariedForVariety` of each place row (ordered by `ord` where it has
-- one).
CREATE TABLE "place_interior_facts_varied_for_variety" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of the optional block `underwaterAccessDetail` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_underwater_access_detail" (
  "place_id" TEXT NOT NULL,
  "gating" TEXT NOT NULL,
  "depth_m" REAL NOT NULL,
  "entity_id" TEXT NOT NULL,
  "air_pockets" BOOLEAN NOT NULL CHECK ("air_pockets" IN (0, 1)),
  "submerged_portal" BOOLEAN NOT NULL CHECK ("submerged_portal" IN (0, 1)),
  "surface_access_nodes" INTEGER NOT NULL,
  PRIMARY KEY ("place_id"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `relationsReserved.dependsOn` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_relations_reserved_depends_on" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `terrainRequests` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_terrain_requests" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "kind" TEXT NOT NULL,
  "radius_m" REAL NOT NULL,
  "delivery_feature" TEXT NOT NULL,
  "delivery_ledge_count" INTEGER,
  "delivery_orientation" TEXT,
  "delivery_water_relation" TEXT,
  "delivery_height_class" TEXT,
  "note" TEXT NOT NULL,
  "delivery_crossings_min" INTEGER,
  "delivery_access" TEXT,
  "delivery_depth_m" REAL,
  "delivery_current" TEXT,
  "delivery_capacity" TEXT,
  "delivery_islet_count" INTEGER,
  "delivery_sides" INTEGER,
  "delivery_feature_count" INTEGER,
  "delivery_bank" TEXT,
  "delivery_depth_class" TEXT,
  "delivery_height_m" INTEGER,
  "delivery_width_m" INTEGER,
  "delivery_connection_count" INTEGER,
  "delivery_length_m" INTEGER,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `sitingPrefs.preferences.landformClasses` of each place row (ordered by `ord` where
-- it has one).
CREATE TABLE "place_siting_prefs_preferences_landform_classes" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of the optional block `heroHist` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_hero_hist" (
  "place_id" TEXT NOT NULL,
  "id" TEXT NOT NULL,
  "kind" TEXT NOT NULL,
  "power_slot" TEXT,
  "status" TEXT NOT NULL,
  "note" TEXT NOT NULL,
  PRIMARY KEY ("place_id"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `relationsReserved.rivals` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_relations_reserved_rivals" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of the optional block `plotOverride` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_plot_override" (
  "place_id" TEXT NOT NULL,
  "source" TEXT NOT NULL,
  "why" TEXT NOT NULL,
  "candidate_id" TEXT,
  "kind" TEXT,
  PRIMARY KEY ("place_id"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of the optional block `life` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_life" (
  "place_id" TEXT NOT NULL,
  "reviewed_on" TEXT NOT NULL,
  "provides" TEXT NOT NULL,
  PRIMARY KEY ("place_id"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `life.groups` of each place_life row (ordered by `ord` where it has one).
CREATE TABLE "place_life_groups" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "slot_id" TEXT NOT NULL,
  "headcount" INTEGER NOT NULL,
  "faction" TEXT,
  "faction_reason" TEXT NOT NULL,
  "depth" TEXT NOT NULL,
  "role" TEXT,
  "trade_class" TEXT,
  "doom_tier" TEXT,
  "outfit" TEXT,
  "outfit_reason" TEXT,
  "race_reason" TEXT,
  "role_reason" TEXT,
  "caster" BOOLEAN CHECK ("caster" IN (0, 1)),
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place_life" ("place_id") ON DELETE CASCADE
);

-- Home of one row per element of `life.groups[].lines` of each place_life_groups row (ordered by `ord` where it has
-- one).
CREATE TABLE "place_life_groups_lines" (
  "place_id" TEXT NOT NULL,
  "groups_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "groups_ord", "ord"),
  FOREIGN KEY ("place_id", "groups_ord") REFERENCES "place_life_groups" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `life.groups[].services` of each place_life_groups row (ordered by `ord` where it has
-- one).
CREATE TABLE "place_life_groups_services" (
  "place_id" TEXT NOT NULL,
  "groups_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "groups_ord", "ord"),
  FOREIGN KEY ("place_id", "groups_ord") REFERENCES "place_life_groups" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `life.groups[].roleExceptions` of each place_life_groups row (ordered by `ord` where
-- it has one).
CREATE TABLE "place_life_groups_role_exceptions" (
  "place_id" TEXT NOT NULL,
  "groups_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "groups_ord", "ord"),
  FOREIGN KEY ("place_id", "groups_ord") REFERENCES "place_life_groups" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `life.creatures` of each place_life row (ordered by `ord` where it has one).
CREATE TABLE "place_life_creatures" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "slot_id" TEXT NOT NULL,
  "species" TEXT NOT NULL,
  "headcount" INTEGER NOT NULL,
  "band" TEXT NOT NULL,
  "den" TEXT NOT NULL,
  "network" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place_life" ("place_id") ON DELETE CASCADE
);

-- Home of one row per element of `life.creatures[].territory` of each place_life_creatures row (ordered by `ord` where
-- it has one).
CREATE TABLE "place_life_creatures_territory" (
  "place_id" TEXT NOT NULL,
  "creatures_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "creatures_ord", "ord"),
  FOREIGN KEY ("place_id", "creatures_ord") REFERENCES "place_life_creatures" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `life.creatures[].lines` of each place_life_creatures row (ordered by `ord` where it
-- has one).
CREATE TABLE "place_life_creatures_lines" (
  "place_id" TEXT NOT NULL,
  "creatures_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "creatures_ord", "ord"),
  FOREIGN KEY ("place_id", "creatures_ord") REFERENCES "place_life_creatures" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `zones` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_zones" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "id" TEXT NOT NULL,
  "owner_kind" TEXT NOT NULL,
  "owner_id" TEXT NOT NULL REFERENCES "npc"("id"),
  "hours_x" REAL NOT NULL,
  "hours_y" REAL NOT NULL,
  "volume_kind" TEXT NOT NULL,
  "volume_cell" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of the optional block `watch` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_watch" (
  "place_id" TEXT NOT NULL,
  "answers_kind" TEXT NOT NULL,
  "answers_id" TEXT NOT NULL REFERENCES "faction"("id"),
  "radius_m" REAL NOT NULL,
  "custody_post" TEXT NOT NULL,
  "custody_light_fixture" TEXT,
  "custody_light_at_x" REAL,
  "custody_light_at_y" REAL,
  "region" TEXT NOT NULL,
  PRIMARY KEY ("place_id"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of the optional block `cityLayout` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_city_layout" (
  "place_id" TEXT NOT NULL,
  "gate_x" REAL NOT NULL,
  "gate_y" REAL NOT NULL,
  "centre_x" REAL NOT NULL,
  "centre_y" REAL NOT NULL,
  "source" TEXT NOT NULL,
  PRIMARY KEY ("place_id"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `cityLayout.way` of each place_city_layout row (ordered by `ord` where it has one).
CREATE TABLE "place_city_layout_way" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "x" REAL NOT NULL,
  "y" REAL NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place_city_layout" ("place_id") ON DELETE CASCADE
);

-- Home of one row per element of `footprintPolygon` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_footprint_polygon" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "x" REAL NOT NULL,
  "y" REAL NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `relations.relationsReserved` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_relations_relations_reserved" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `relationsReserved.visibleFrom` of each place row (ordered by `ord` where it has
-- one).
CREATE TABLE "place_relations_reserved_visible_from" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of the optional block `life.groups[].spots` of each place_life_groups row (ordered by `ord` where it has one).
CREATE TABLE "place_life_groups_spots" (
  "place_id" TEXT NOT NULL,
  "groups_ord" INTEGER NOT NULL,
  "home_socket_id" TEXT NOT NULL,
  "home_activity" TEXT NOT NULL,
  "bed_socket_id" TEXT,
  "bed_activity" TEXT NOT NULL,
  "bed_place_id" TEXT REFERENCES "place"("id"),
  PRIMARY KEY ("place_id", "groups_ord"),
  FOREIGN KEY ("place_id", "groups_ord") REFERENCES "place_life_groups" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `life.groups[].spots.work` of each place_life_groups_spots row (ordered by `ord`
-- where it has one).
CREATE TABLE "place_life_groups_spots_work" (
  "place_id" TEXT NOT NULL,
  "groups_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "socket_id" TEXT NOT NULL,
  "activity" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "groups_ord", "ord"),
  FOREIGN KEY ("place_id", "groups_ord") REFERENCES "place_life_groups_spots" ("place_id", "groups_ord") ON DELETE CASCADE
);

-- Home of one row per element of `life.creatures[].roleExceptions` of each place_life_creatures row (ordered by `ord`
-- where it has one).
CREATE TABLE "place_life_creatures_role_exceptions" (
  "place_id" TEXT NOT NULL,
  "creatures_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "creatures_ord", "ord"),
  FOREIGN KEY ("place_id", "creatures_ord") REFERENCES "place_life_creatures" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `assetGaps` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_asset_gaps" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `life.groups[].signatureSpells` of each place_life_groups row (ordered by `ord` where
-- it has one).
CREATE TABLE "place_life_groups_signature_spells" (
  "place_id" TEXT NOT NULL,
  "groups_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "groups_ord", "ord"),
  FOREIGN KEY ("place_id", "groups_ord") REFERENCES "place_life_groups" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of the optional block `authoredDangerProperty` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_authored_danger_property" (
  "place_id" TEXT NOT NULL,
  "interior" TEXT NOT NULL,
  "field" TEXT NOT NULL,
  "note" TEXT NOT NULL,
  PRIMARY KEY ("place_id"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `secondaryCultures` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_secondary_cultures" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `life.groups[].races` of each place_life_groups row (ordered by `ord` where it has
-- one).
CREATE TABLE "place_life_groups_races" (
  "place_id" TEXT NOT NULL,
  "groups_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT,
  PRIMARY KEY ("place_id", "groups_ord", "ord"),
  FOREIGN KEY ("place_id", "groups_ord") REFERENCES "place_life_groups" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `factionPresence` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_faction_presence" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "faction_ref" TEXT NOT NULL,
  "role" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `relationsReserved.travelServiceEdges` of each place row (ordered by `ord` where it
-- has one).
CREATE TABLE "place_relations_reserved_travel_service_edges" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `relationsReserved.patrols` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_relations_reserved_patrols" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `relationsReserved.tolls` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_relations_reserved_tolls" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `sitingPrefs.scourSiteCandidates` of each place row (ordered by `ord` where it has
-- one).
CREATE TABLE "place_siting_prefs_scour_site_candidates" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `life.groups[].spotsAdd.work` of each place_life_groups row (ordered by `ord` where
-- it has one).
CREATE TABLE "place_life_groups_spots_add_work" (
  "place_id" TEXT NOT NULL,
  "groups_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "socket_id" TEXT NOT NULL,
  "activity" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "groups_ord", "ord"),
  FOREIGN KEY ("place_id", "groups_ord") REFERENCES "place_life_groups" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `life.groups[].postRoles.socket.opening-work-camp.encounter-camp-guards` of each
-- place_life_groups row (ordered by `ord` where it has one).
CREATE TABLE "place_life_groups_post_roles_socket_opening_work_camp_encounter_camp_guards" (
  "place_id" TEXT NOT NULL,
  "groups_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "groups_ord", "ord"),
  FOREIGN KEY ("place_id", "groups_ord") REFERENCES "place_life_groups" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `hostility.trespassZones` of each place row (ordered by `ord` where it has one).
CREATE TABLE "place_hostility_trespass_zones" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "zone" TEXT NOT NULL,
  "stance" TEXT NOT NULL,
  "warning" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place" ("id") ON DELETE CASCADE
);

-- == item_class ==

-- Home of each item class a socket may name, its asset source, value band and kinds (each with the mesh that shows
-- it). Each item class lists the kinds an item socket names in itemKind (16k walk 12: the item system must know a mace
-- is a mace), each with the vanilla mesh that shows it. A kind no mesh shows is never added; a stack is one socket
-- over several placements of the kind's mesh.
CREATE TABLE "item_class" (
  "id" TEXT NOT NULL,
  "asset_source" TEXT NOT NULL,
  "value_band" TEXT NOT NULL REFERENCES "value_band"("id"),
  "text_bearing" BOOLEAN CHECK ("text_bearing" IN (0, 1)),
  PRIMARY KEY ("id")
);

-- Home of one row per key of `kinds` of each item_class row (ordered by `ord` where it has one).
CREATE TABLE "item_class_kind" (
  "item_class_id" TEXT NOT NULL,
  "kind" TEXT NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("item_class_id", "kind"),
  FOREIGN KEY ("item_class_id") REFERENCES "item_class" ("id") ON DELETE CASCADE
);

-- == container_class ==

-- Home of each container class: its name families and default fill rule.
CREATE TABLE "container_class" (
  "id" TEXT NOT NULL,
  "default_fill_rule" TEXT,
  "about" TEXT,
  PRIMARY KEY ("id")
);

-- Home of one row per element of `nameFamilies` of each container_class row (ordered by `ord` where it has one).
CREATE TABLE "container_class_name_family" (
  "container_class_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("container_class_id", "ord"),
  FOREIGN KEY ("container_class_id") REFERENCES "container_class" ("id") ON DELETE CASCADE
);

-- == furniture_activity ==

-- Home of which furniture families host each activity.
CREATE TABLE "furniture_activity" (
  "id" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- Home of one row per element of `value` of each furniture_activity row (ordered by `ord` where it has one).
CREATE TABLE "furniture_activity_family" (
  "furniture_activity_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("furniture_activity_id", "ord"),
  FOREIGN KEY ("furniture_activity_id") REFERENCES "furniture_activity" ("id") ON DELETE CASCADE
);

-- == fill_rule ==

-- Home of the authored fill rule's needs. A container socket's `fillRule` is a blanket rule id of the loot-rules table
-- (worldgen.sockets.load_vocabulary reads its ids) or `authored`. A blanket socket's list is frozen at authoring time
-- by `python3 -m worldgen.loot_fill --place <id> --apply` into `lootTable {items, frozenFrom}`; an authored socket's
-- `lootTable` carries `storyNote` and, once 2.3c fills it, `items` (00-core rule 9: nothing rolls at play time).
CREATE TABLE "fill_rule" (
  "id" TEXT NOT NULL,
  "needs" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- Home of one row per element of `lootTableFields` of each fill_rule row (ordered by `ord` where it has one).
CREATE TABLE "fill_rule_loot_table_fields" (
  "fill_rule_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("fill_rule_id", "ord"),
  FOREIGN KEY ("fill_rule_id") REFERENCES "fill_rule" ("id") ON DELETE CASCADE
);

-- == plant_class ==

-- Home of each harvestable plant class. The harvestable plant socket (2.3a, decision 6): an already-placed flora piece
-- of one of these species is a one-slot container holding its linked ingredient, which regrows `regrowDays` in-game
-- days after harvest. No new plant models, no new placement.
CREATE TABLE "plant_class" (
  "id" TEXT NOT NULL,
  "ingredient" TEXT NOT NULL,
  "regrow_days" INTEGER NOT NULL,
  "note" TEXT,
  PRIMARY KEY ("id")
);

-- Home of one row per element of `species` of each plant_class row (ordered by `ord` where it has one).
CREATE TABLE "plant_class_species" (
  "plant_class_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("plant_class_id", "ord"),
  FOREIGN KEY ("plant_class_id") REFERENCES "plant_class" ("id") ON DELETE CASCADE
);

-- == station_class ==

-- Home of each crafting or service station class: kit, asset, dressing.
CREATE TABLE "station_class" (
  "id" TEXT NOT NULL,
  "kit" TEXT NOT NULL,
  "asset_source" TEXT NOT NULL,
  "dressing_note" TEXT,
  "note" TEXT,
  PRIMARY KEY ("id")
);

-- Home of one row per element of `dressing` of each station_class row (ordered by `ord` where it has one).
CREATE TABLE "station_class_dressing" (
  "station_class_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("station_class_id", "ord"),
  FOREIGN KEY ("station_class_id") REFERENCES "station_class" ("id") ON DELETE CASCADE
);

-- == sign_purpose ==

-- Home of each sign purpose and the fields it needs.
CREATE TABLE "sign_purpose" (
  "id" TEXT NOT NULL,
  "about" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- Home of one row per element of `needs` of each sign_purpose row (ordered by `ord` where it has one).
CREATE TABLE "sign_purpose_needs" (
  "sign_purpose_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("sign_purpose_id", "ord"),
  FOREIGN KEY ("sign_purpose_id") REFERENCES "sign_purpose" ("id") ON DELETE CASCADE
);

-- == door_type ==

-- Home of each door type.
CREATE TABLE "door_type" (
  "id" TEXT NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- == socket_vocabulary ==

-- Home of the socket vocabulary's rules in prose (one row): its decisions, the common fields, interactables, service
-- surfaces and the sign fields.
CREATE TABLE "socket_vocabulary" (
  "id" TEXT NOT NULL,
  "about" TEXT NOT NULL,
  "interactables_about" TEXT NOT NULL,
  "interactables_verbs_read" TEXT NOT NULL,
  "interactables_verbs_sleep" TEXT NOT NULL,
  "interactables_verbs_sit" TEXT NOT NULL,
  "interactables_verbs_cook" TEXT NOT NULL,
  "interactables_verbs_use" TEXT NOT NULL,
  "interactables_verbs_pray" TEXT NOT NULL,
  "interactables_verbs_gather" TEXT NOT NULL,
  "interactables_station_hosts_blacksmithforge" TEXT NOT NULL,
  "interactables_station_hosts_smelter" TEXT NOT NULL,
  "interactables_station_hosts_tanningrack" TEXT NOT NULL,
  "interactables_station_hosts_sharpeningwheel" TEXT NOT NULL,
  "interactables_station_hosts_blacksmithworkbench" TEXT NOT NULL,
  "interactables_station_hosts_alchemyworkbench" TEXT NOT NULL,
  "interactables_station_hosts_enchantingworkbench" TEXT NOT NULL,
  "interactables_station_repairs_forge" TEXT NOT NULL,
  "interactables_station_repairs_smelter" TEXT NOT NULL,
  "interactables_station_repairs_grindstone" TEXT NOT NULL,
  "interactables_station_repairs_workbench" TEXT NOT NULL,
  "interactables_station_repairs_tanning_rack" TEXT NOT NULL,
  "interactables_station_repairs_alchemy" TEXT NOT NULL,
  "interactables_station_repairs_enchanting" TEXT NOT NULL,
  "interactables_repairs_about" TEXT NOT NULL,
  "interactables_shrine_class" TEXT NOT NULL,
  "interactables_prayer_text" TEXT NOT NULL,
  "service_surfaces_about" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- Home of one row per element of `decision` of each socket_vocabulary row (ordered by `ord` where it has one).
CREATE TABLE "socket_vocabulary_decision" (
  "socket_vocabulary_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("socket_vocabulary_id", "ord"),
  FOREIGN KEY ("socket_vocabulary_id") REFERENCES "socket_vocabulary" ("id") ON DELETE CASCADE
);

-- Home of one row per key of `commonFields` of each socket_vocabulary row (ordered by `ord` where it has one).
CREATE TABLE "socket_vocabulary_common_fields" (
  "socket_vocabulary_id" TEXT NOT NULL,
  "field" TEXT NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("socket_vocabulary_id", "field"),
  FOREIGN KEY ("socket_vocabulary_id") REFERENCES "socket_vocabulary" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `interactables.classes` of each socket_vocabulary row (ordered by `ord` where it has
-- one).
CREATE TABLE "socket_vocabulary_interactables_classes" (
  "socket_vocabulary_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("socket_vocabulary_id", "ord"),
  FOREIGN KEY ("socket_vocabulary_id") REFERENCES "socket_vocabulary" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `interactables.cookHosts` of each socket_vocabulary row (ordered by `ord` where it
-- has one).
CREATE TABLE "socket_vocabulary_interactables_cook_hosts" (
  "socket_vocabulary_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("socket_vocabulary_id", "ord"),
  FOREIGN KEY ("socket_vocabulary_id") REFERENCES "socket_vocabulary" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `interactables.cookStations` of each socket_vocabulary row (ordered by `ord` where it
-- has one).
CREATE TABLE "socket_vocabulary_interactables_cook_stations" (
  "socket_vocabulary_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("socket_vocabulary_id", "ord"),
  FOREIGN KEY ("socket_vocabulary_id") REFERENCES "socket_vocabulary" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `interactables.softSets` of each socket_vocabulary row (ordered by `ord` where it has
-- one).
CREATE TABLE "socket_vocabulary_interactables_soft_sets" (
  "socket_vocabulary_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("socket_vocabulary_id", "ord"),
  FOREIGN KEY ("socket_vocabulary_id") REFERENCES "socket_vocabulary" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `serviceSurfaces.nameFamilies` of each socket_vocabulary row (ordered by `ord` where
-- it has one).
CREATE TABLE "socket_vocabulary_service_surfaces_name_families" (
  "socket_vocabulary_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("socket_vocabulary_id", "ord"),
  FOREIGN KEY ("socket_vocabulary_id") REFERENCES "socket_vocabulary" ("id") ON DELETE CASCADE
);

-- Home of one row per key of `sign` of each socket_vocabulary row (ordered by `ord` where it has one).
CREATE TABLE "socket_vocabulary_sign" (
  "socket_vocabulary_id" TEXT NOT NULL,
  "field" TEXT NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("socket_vocabulary_id", "field"),
  FOREIGN KEY ("socket_vocabulary_id") REFERENCES "socket_vocabulary" ("id") ON DELETE CASCADE
);

-- == layout ==

-- Home of each place's layout: the authored pose of every placed thing as an ordered program of ops (old 0140); `ord`
-- is the op's position across all the op tables, so the program replays in order. Sockets are the `socket` table.
CREATE TABLE "layout" (
  "place_id" TEXT NOT NULL,
  "window_centre_km_x" REAL NOT NULL,
  "window_centre_km_y" REAL NOT NULL,
  "window_half_m" REAL NOT NULL,
  "state_key" TEXT,
  "owner_go_ahead" TEXT,
  PRIMARY KEY ("place_id")
);

-- Home of the elements of `ops` of each layout row (ordered by `ord` where it has one).
CREATE TABLE "layout_place" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "op" TEXT NOT NULL,
  "uid" TEXT NOT NULL,
  "asset" TEXT NOT NULL,
  "at_x" REAL NOT NULL,
  "at_y" REAL NOT NULL,
  "yaw" REAL,
  "settle" BOOLEAN CHECK ("settle" IN (0, 1)),
  "wet" BOOLEAN CHECK ("wet" IN (0, 1)),
  "y" REAL,
  "walkable" BOOLEAN CHECK ("walkable" IN (0, 1)),
  "tether" TEXT,
  "beached" BOOLEAN CHECK ("beached" IN (0, 1)),
  "scale" REAL,
  "collision" TEXT,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "layout" ("place_id") ON DELETE CASCADE
);

-- Home of the elements of `ops` of each layout row (ordered by `ord` where it has one).
CREATE TABLE "layout_bind" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "op" TEXT NOT NULL,
  "uid" TEXT NOT NULL,
  "kind" TEXT NOT NULL,
  "id" TEXT NOT NULL,
  "layer" TEXT,
  "on" TEXT,
  "evidence" TEXT,
  "fit" TEXT,
  "index" INTEGER,
  "host" TEXT,
  "grows_from" TEXT,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "layout" ("place_id") ON DELETE CASCADE
);

-- Home of the elements of `ops` of each layout row (ordered by `ord` where it has one).
CREATE TABLE "layout_path" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "op" TEXT NOT NULL,
  "action" TEXT NOT NULL,
  "id" TEXT NOT NULL,
  "width" REAL,
  "kind" TEXT,
  "why" TEXT,
  "variant_ref" TEXT,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "layout" ("place_id") ON DELETE CASCADE
);

-- Home of one row per element of `ops[].points` of each layout_path row (ordered by `ord` where it has one).
CREATE TABLE "layout_path_points" (
  "place_id" TEXT NOT NULL,
  "ops_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "x" REAL NOT NULL,
  "y" REAL NOT NULL,
  PRIMARY KEY ("place_id", "ops_ord", "ord"),
  FOREIGN KEY ("place_id", "ops_ord") REFERENCES "layout_path" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of every place socket (decision 0030: sockets; old 0103): an NPC post, idle spot, item, container, station,
-- sign, plant, mooring or marker, with its owner, value tier, fill rule and loot; `ord` is its position in the place's
-- layout program.
CREATE TABLE "socket" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "op" TEXT NOT NULL,
  "id" TEXT NOT NULL,
  "kind" TEXT NOT NULL,
  "at_x" REAL,
  "at_y" REAL,
  "zone" TEXT,
  "species" TEXT,
  "headcount" INTEGER,
  "why" TEXT,
  "danger_band" TEXT,
  "host" TEXT,
  "container_class" TEXT REFERENCES "container_class"("id"),
  "fill_rule" TEXT,
  "parcel" TEXT,
  "value_tier" TEXT,
  "owner" TEXT,
  "activity" TEXT,
  "interior_cell" TEXT,
  "roster_slot_id" TEXT,
  "role" TEXT,
  "plant_class" TEXT REFERENCES "plant_class"("id"),
  "station_class" TEXT REFERENCES "station_class"("id"),
  "seat_height_m" REAL,
  "mooring_kind" TEXT,
  "capacity" INTEGER,
  "service_link" TEXT,
  "min_depth_dry_m" REAL,
  "water_id" TEXT,
  "lock" TEXT REFERENCES "lock"("id"),
  "sign_purpose" TEXT REFERENCES "sign_purpose"("id"),
  "text_key" TEXT,
  "item_class" TEXT REFERENCES "item_class"("id"),
  "item_kind" TEXT,
  "item" TEXT REFERENCES "item"("id"),
  "station_id" TEXT,
  "reach" TEXT,
  "effort" INTEGER,
  "reach_via" TEXT,
  "cue_placement" TEXT,
  "cue_text" TEXT,
  "yaw_deg" REAL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "layout" ("place_id") ON DELETE CASCADE
);

-- Home of the optional block `ops[].pad` of each layout_place row (ordered by `ord` where it has one).
CREATE TABLE "layout_place_pad" (
  "place_id" TEXT NOT NULL,
  "ops_ord" INTEGER NOT NULL,
  "apron_m" REAL NOT NULL,
  "batter" BOOLEAN CHECK ("batter" IN (0, 1)),
  "datum_m" REAL,
  "blend_m" REAL,
  "floor_min_m" REAL,
  PRIMARY KEY ("place_id", "ops_ord"),
  FOREIGN KEY ("place_id", "ops_ord") REFERENCES "layout_place" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of the elements of `ops` of each layout row (ordered by `ord` where it has one).
CREATE TABLE "layout_note" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "op" TEXT NOT NULL,
  "uid" TEXT NOT NULL,
  "text" TEXT NOT NULL,
  "district" TEXT,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "layout" ("place_id") ON DELETE CASCADE
);

-- Home of the elements of `ops` of each layout row (ordered by `ord` where it has one).
CREATE TABLE "layout_mount" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "op" TEXT NOT NULL,
  "child" TEXT NOT NULL,
  "parent" TEXT NOT NULL,
  "unmined" TEXT,
  "inside" BOOLEAN CHECK ("inside" IN (0, 1)),
  "hang" BOOLEAN CHECK ("hang" IN (0, 1)),
  "max_h" REAL,
  "bearing" REAL,
  "along" REAL,
  "wall" BOOLEAN CHECK ("wall" IN (0, 1)),
  "height" REAL,
  "min_h" REAL,
  "like" TEXT,
  "yaw" REAL,
  "bracket" BOOLEAN CHECK ("bracket" IN (0, 1)),
  "moor" TEXT,
  "rope" TEXT,
  "plank_to" TEXT,
  "ladder" BOOLEAN CHECK ("ladder" IN (0, 1)),
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "layout" ("place_id") ON DELETE CASCADE
);

-- Home of the elements of `ops` of each layout row (ordered by `ord` where it has one).
CREATE TABLE "layout_move" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "op" TEXT NOT NULL,
  "uid" TEXT NOT NULL,
  "dy" REAL,
  "turn" REAL,
  "yaw" REAL,
  "resettle" BOOLEAN CHECK ("resettle" IN (0, 1)),
  "dx" REAL,
  "dz" REAL,
  "pitch" REAL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "layout" ("place_id") ON DELETE CASCADE
);

-- Home of the elements of `ops` of each layout row (ordered by `ord` where it has one).
CREATE TABLE "layout_group" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "op" TEXT NOT NULL,
  "action" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "at_x" REAL NOT NULL,
  "at_y" REAL NOT NULL,
  "yaw" REAL NOT NULL,
  "prefix" TEXT,
  "parcel" TEXT,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "layout" ("place_id") ON DELETE CASCADE
);

-- Home of the elements of `ops` of each layout row (ordered by `ord` where it has one).
CREATE TABLE "layout_remove" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "op" TEXT NOT NULL,
  "uid" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "layout" ("place_id") ON DELETE CASCADE
);

-- Home of the optional block `ops[].lootTable` of each socket row (ordered by `ord` where it has one).
CREATE TABLE "socket_loot_table" (
  "place_id" TEXT NOT NULL,
  "ops_ord" INTEGER NOT NULL,
  "story_note" TEXT,
  "frozen_from" TEXT,
  "band" TEXT,
  PRIMARY KEY ("place_id", "ops_ord"),
  FOREIGN KEY ("place_id", "ops_ord") REFERENCES "socket" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `ops[].lootTable.items` of each socket_loot_table row (ordered by `ord` where it has
-- one).
CREATE TABLE "socket_loot_table_items" (
  "place_id" TEXT NOT NULL,
  "ops_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "item" TEXT NOT NULL REFERENCES "item"("id"),
  "count" INTEGER NOT NULL,
  PRIMARY KEY ("place_id", "ops_ord", "ord"),
  FOREIGN KEY ("place_id", "ops_ord") REFERENCES "socket_loot_table" ("place_id", "ops_ord") ON DELETE CASCADE
);

-- Home of one row per element of `ops[].fills` of each layout_place row (ordered by `ord` where it has one).
CREATE TABLE "layout_place_fills" (
  "place_id" TEXT NOT NULL,
  "ops_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ops_ord", "ord"),
  FOREIGN KEY ("place_id", "ops_ord") REFERENCES "layout_place" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of the elements of `ops` of each layout row (ordered by `ord` where it has one).
CREATE TABLE "layout_pool" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "op" TEXT NOT NULL,
  "uid" TEXT NOT NULL,
  "centre_m_x" REAL NOT NULL,
  "centre_m_y" REAL NOT NULL,
  "radius_m" REAL NOT NULL,
  "depth_m" REAL NOT NULL,
  "rim_m" REAL NOT NULL,
  "why" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "layout" ("place_id") ON DELETE CASCADE
);

-- Home of one row per element of `ops[].sources` of each layout_pool row (ordered by `ord` where it has one).
CREATE TABLE "layout_pool_sources" (
  "place_id" TEXT NOT NULL,
  "ops_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ops_ord", "ord"),
  FOREIGN KEY ("place_id", "ops_ord") REFERENCES "layout_pool" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of the elements of `ops` of each layout row (ordered by `ord` where it has one).
CREATE TABLE "layout_mound" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "op" TEXT NOT NULL,
  "uid" TEXT NOT NULL,
  "datum_m" REAL,
  "blend_m" REAL NOT NULL,
  "why" TEXT NOT NULL,
  "profile" TEXT,
  "variant_ref" TEXT,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "layout" ("place_id") ON DELETE CASCADE
);

-- Home of one row per element of `ops[].polygonM` of each layout_mound row (ordered by `ord` where it has one).
CREATE TABLE "layout_mound_polygon_m" (
  "place_id" TEXT NOT NULL,
  "ops_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "x" REAL NOT NULL,
  "y" REAL NOT NULL,
  PRIMARY KEY ("place_id", "ops_ord", "ord"),
  FOREIGN KEY ("place_id", "ops_ord") REFERENCES "layout_mound" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `ops[].sources` of each layout_mound row (ordered by `ord` where it has one).
CREATE TABLE "layout_mound_sources" (
  "place_id" TEXT NOT NULL,
  "ops_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ops_ord", "ord"),
  FOREIGN KEY ("place_id", "ops_ord") REFERENCES "layout_mound" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `ops[].fills` of each socket row (ordered by `ord` where it has one).
CREATE TABLE "socket_fills" (
  "place_id" TEXT NOT NULL,
  "ops_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ops_ord", "ord"),
  FOREIGN KEY ("place_id", "ops_ord") REFERENCES "socket" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `ops[].schedule` of each socket row (ordered by `ord` where it has one).
CREATE TABLE "socket_schedule" (
  "place_id" TEXT NOT NULL,
  "ops_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "day_phase" TEXT NOT NULL,
  "socket_id" TEXT NOT NULL,
  "purpose" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ops_ord", "ord"),
  FOREIGN KEY ("place_id", "ops_ord") REFERENCES "socket" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of the elements of `ops` of each layout row (ordered by `ord` where it has one).
CREATE TABLE "layout_settle" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "op" TEXT NOT NULL,
  "uid" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "layout" ("place_id") ON DELETE CASCADE
);

-- Home of one row per element of `ops[].accepts` of each socket row (ordered by `ord` where it has one).
CREATE TABLE "socket_accepts" (
  "place_id" TEXT NOT NULL,
  "ops_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ops_ord", "ord"),
  FOREIGN KEY ("place_id", "ops_ord") REFERENCES "socket" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of the elements of `ops` of each layout row (ordered by `ord` where it has one).
CREATE TABLE "layout_snap" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "op" TEXT NOT NULL,
  "child" TEXT NOT NULL,
  "child_face" TEXT NOT NULL,
  "parent" TEXT NOT NULL,
  "parent_face" TEXT NOT NULL,
  "by" TEXT,
  "settle" BOOLEAN CHECK ("settle" IN (0, 1)),
  "pick" INTEGER,
  "allow_terminal" BOOLEAN CHECK ("allow_terminal" IN (0, 1)),
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "layout" ("place_id") ON DELETE CASCADE
);

-- Home of the optional block `ops[].pad.apronBySide` of each layout_place_pad row (ordered by `ord` where it has one).
CREATE TABLE "layout_place_pad_apron_by_side" (
  "place_id" TEXT NOT NULL,
  "ops_ord" INTEGER NOT NULL,
  "w" REAL,
  "e" REAL,
  "n" REAL,
  "s" REAL,
  PRIMARY KEY ("place_id", "ops_ord"),
  FOREIGN KEY ("place_id", "ops_ord") REFERENCES "layout_place_pad" ("place_id", "ops_ord") ON DELETE CASCADE
);

-- Home of the elements of `ops` of each layout row (ordered by `ord` where it has one).
CREATE TABLE "layout_swap" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "op" TEXT NOT NULL,
  "uid" TEXT NOT NULL,
  "asset" TEXT NOT NULL,
  "resettle" BOOLEAN NOT NULL CHECK ("resettle" IN (0, 1)),
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "layout" ("place_id") ON DELETE CASCADE
);

-- Home of one row per element of `ops[].pointsTo` of each socket row (ordered by `ord` where it has one).
CREATE TABLE "socket_points_to" (
  "place_id" TEXT NOT NULL,
  "ops_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ops_ord", "ord"),
  FOREIGN KEY ("place_id", "ops_ord") REFERENCES "socket" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `ops[].fills` of each layout_bind row (ordered by `ord` where it has one).
CREATE TABLE "layout_bind_fills" (
  "place_id" TEXT NOT NULL,
  "ops_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ops_ord", "ord"),
  FOREIGN KEY ("place_id", "ops_ord") REFERENCES "layout_bind" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `ops[].rampM` of each layout_mound row (ordered by `ord` where it has one).
CREATE TABLE "layout_mound_ramp_m" (
  "place_id" TEXT NOT NULL,
  "ops_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "x" REAL NOT NULL,
  "y" REAL NOT NULL,
  "z" REAL NOT NULL,
  PRIMARY KEY ("place_id", "ops_ord", "ord"),
  FOREIGN KEY ("place_id", "ops_ord") REFERENCES "layout_mound" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `ops[].states` of each socket row (ordered by `ord` where it has one).
CREATE TABLE "socket_states" (
  "place_id" TEXT NOT NULL,
  "ops_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ops_ord", "ord"),
  FOREIGN KEY ("place_id", "ops_ord") REFERENCES "socket" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `ops[].states` of each layout_place row (ordered by `ord` where it has one).
CREATE TABLE "layout_place_states" (
  "place_id" TEXT NOT NULL,
  "ops_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ops_ord", "ord"),
  FOREIGN KEY ("place_id", "ops_ord") REFERENCES "layout_place" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `cliffWays` of each layout row (ordered by `ord` where it has one).
CREATE TABLE "layout_cliff_ways" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "uid" TEXT NOT NULL,
  "route" TEXT NOT NULL,
  "path_zm" REAL NOT NULL,
  "water_zm" REAL NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "layout" ("place_id") ON DELETE CASCADE
);

-- Home of one row per element of `cliffWays[].pieces` of each layout_cliff_ways row (ordered by `ord` where it has
-- one).
CREATE TABLE "layout_cliff_ways_pieces" (
  "place_id" TEXT NOT NULL,
  "cliff_ways_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "cliff_ways_ord", "ord"),
  FOREIGN KEY ("place_id", "cliff_ways_ord") REFERENCES "layout_cliff_ways" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `ops[].facedBy` of each layout_mound row (ordered by `ord` where it has one).
CREATE TABLE "layout_mound_faced_by" (
  "place_id" TEXT NOT NULL,
  "ops_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ops_ord", "ord"),
  FOREIGN KEY ("place_id", "ops_ord") REFERENCES "layout_mound" ("place_id", "ord") ON DELETE CASCADE
);

-- == quest_line ==

-- Home of every questline: its code prefix, name, group, faction, tier, home region and target count.
CREATE TABLE "quest_line" (
  "id" TEXT NOT NULL,
  "code" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "group" TEXT NOT NULL REFERENCES "quest_group"("id"),
  "faction" TEXT REFERENCES "faction"("id"),
  "tier" INTEGER NOT NULL,
  "home_region" TEXT REFERENCES "region"("id"),
  "target_count_min" INTEGER NOT NULL,
  "target_count_max" INTEGER NOT NULL,
  "notes" TEXT NOT NULL,
  "registry_status" TEXT NOT NULL,
  "registry_note" TEXT NOT NULL,
  "depth" TEXT,
  PRIMARY KEY ("id")
);

-- Home of one row per element of `sources` of each quest_line row (ordered by `ord` where it has one).
CREATE TABLE "quest_line_source" (
  "quest_line_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("quest_line_id", "ord"),
  FOREIGN KEY ("quest_line_id") REFERENCES "quest_line" ("id") ON DELETE CASCADE
);

-- == quest ==

-- Home of every quest (decision 0030: quests): the quest object (code, title, line, group, tier, shapes, region,
-- settlement, anchor places, premise) and, once a quest is written, its record (quest-write/quest-record.md) as child
-- tables: truth, cast and what each knows, things, clues, conclusions, shape data, stages with objectives and edges,
-- endings, topics, review.
CREATE TABLE "quest" (
  "id" TEXT NOT NULL,
  "code" TEXT NOT NULL,
  "title" TEXT NOT NULL,
  "line" TEXT NOT NULL REFERENCES "quest_line"("id"),
  "group" TEXT NOT NULL REFERENCES "quest_group"("id"),
  "tier" INTEGER NOT NULL,
  "status" TEXT NOT NULL REFERENCES "quest_status"("id"),
  "region" TEXT NOT NULL REFERENCES "region"("id"),
  "settlement" TEXT REFERENCES "place"("id"),
  "premise" TEXT NOT NULL,
  "cost_tier" TEXT REFERENCES "cost_tier"("id"),
  "milestone" INTEGER NOT NULL,
  "packet" TEXT NOT NULL,
  "registry_status" TEXT NOT NULL,
  "registry_note" TEXT NOT NULL,
  "start_when" TEXT REFERENCES "condition"("id"),
  "start" INTEGER,
  "record_status" TEXT,
  "foundation" TEXT,
  "centrepiece" TEXT REFERENCES "verb_tag"("id"),
  "review_reviewer" TEXT,
  "review_checklist" TEXT,
  "notes" TEXT,
  "stand_in_for" TEXT REFERENCES "quest"("id"),
  PRIMARY KEY ("id")
);

-- Home of one row per element of `shapes` of each quest row (ordered by `ord` where it has one).
CREATE TABLE "quest_shape_of" (
  "quest_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL REFERENCES "quest_shape"("id"),
  PRIMARY KEY ("quest_id", "ord"),
  FOREIGN KEY ("quest_id") REFERENCES "quest" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `anchorPlaces` of each quest row (ordered by `ord` where it has one).
CREATE TABLE "quest_anchor_place" (
  "quest_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL REFERENCES "place"("id"),
  PRIMARY KEY ("quest_id", "ord"),
  FOREIGN KEY ("quest_id") REFERENCES "quest" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `touches` of each quest row (ordered by `ord` where it has one).
CREATE TABLE "quest_touch" (
  "quest_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "id" TEXT NOT NULL,
  "access" TEXT NOT NULL REFERENCES "touch_access"("id"),
  PRIMARY KEY ("quest_id", "ord"),
  FOREIGN KEY ("quest_id") REFERENCES "quest" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `sources` of each quest row (ordered by `ord` where it has one).
CREATE TABLE "quest_source" (
  "quest_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("quest_id", "ord"),
  FOREIGN KEY ("quest_id") REFERENCES "quest" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `stages` of each quest row (ordered by `ord` where it has one).
CREATE TABLE "quest_stage" (
  "quest_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "id" INTEGER NOT NULL,
  "place" TEXT NOT NULL REFERENCES "place"("id"),
  "journal" TEXT,
  "on_enter" TEXT REFERENCES "action_list"("id"),
  "outside_packet" TEXT,
  "ending" TEXT,
  "entry" TEXT,
  "journal_text" TEXT,
  "directions" TEXT,
  "ending_id" TEXT,
  PRIMARY KEY ("quest_id", "ord"),
  UNIQUE ("quest_id", "id"),
  FOREIGN KEY ("quest_id") REFERENCES "quest" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `stages[].objectives` of each quest_stage row (ordered by `ord` where it has one).
CREATE TABLE "quest_objective" (
  "quest_id" TEXT NOT NULL,
  "stages_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "id" TEXT NOT NULL,
  "text" TEXT NOT NULL,
  "complete_when" TEXT NOT NULL REFERENCES "condition"("id"),
  "where_ref" TEXT,
  PRIMARY KEY ("quest_id", "stages_ord", "ord"),
  FOREIGN KEY ("quest_id", "stages_ord") REFERENCES "quest_stage" ("quest_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `stages[].successors` of each quest_stage row (ordered by `ord` where it has one).
CREATE TABLE "quest_successor" (
  "quest_id" TEXT NOT NULL,
  "stages_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "to" INTEGER NOT NULL,
  "when" TEXT NOT NULL REFERENCES "condition"("id"),
  PRIMARY KEY ("quest_id", "stages_ord", "ord"),
  FOREIGN KEY ("quest_id", "stages_ord") REFERENCES "quest_stage" ("quest_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `stages[].failForward` of each quest_stage row (ordered by `ord` where it has one).
CREATE TABLE "quest_fail_forward" (
  "quest_id" TEXT NOT NULL,
  "stages_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "to" INTEGER NOT NULL,
  "when" TEXT NOT NULL REFERENCES "condition"("id"),
  PRIMARY KEY ("quest_id", "stages_ord", "ord"),
  FOREIGN KEY ("quest_id", "stages_ord") REFERENCES "quest_stage" ("quest_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `essentialTopics` of each quest row (ordered by `ord` where it has one).
CREATE TABLE "quest_essential_topic" (
  "quest_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("quest_id", "ord"),
  FOREIGN KEY ("quest_id") REFERENCES "quest" ("id") ON DELETE CASCADE
);

-- Home of one row per key of `recordSources` of each quest row (ordered by `ord` where it has one).
CREATE TABLE "quest_record_source" (
  "quest_id" TEXT NOT NULL,
  "source" TEXT NOT NULL,
  "value" TEXT,
  PRIMARY KEY ("quest_id", "source"),
  FOREIGN KEY ("quest_id") REFERENCES "quest" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `recordSources{*}` of each quest_record_source row (ordered by `ord` where it has
-- one).
CREATE TABLE "quest_record_source_items" (
  "quest_id" TEXT NOT NULL,
  "source" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("quest_id", "source", "ord"),
  FOREIGN KEY ("quest_id", "source") REFERENCES "quest_record_source" ("quest_id", "source") ON DELETE CASCADE
);

-- Home of one row per element of `actionPlan` of each quest row (ordered by `ord` where it has one).
CREATE TABLE "quest_action_plan" (
  "quest_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "skill" TEXT NOT NULL,
  "use" TEXT NOT NULL,
  "reason" TEXT NOT NULL,
  PRIMARY KEY ("quest_id", "ord"),
  FOREIGN KEY ("quest_id") REFERENCES "quest" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `truth` of each quest row (ordered by `ord` where it has one).
CREATE TABLE "quest_truth" (
  "quest_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "id" TEXT NOT NULL,
  "when" TEXT NOT NULL,
  "where" TEXT NOT NULL,
  "what" TEXT NOT NULL,
  PRIMARY KEY ("quest_id", "ord"),
  FOREIGN KEY ("quest_id") REFERENCES "quest" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `truth[].who` of each quest_truth row (ordered by `ord` where it has one).
CREATE TABLE "quest_truth_who" (
  "quest_id" TEXT NOT NULL,
  "truth_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("quest_id", "truth_ord", "ord"),
  FOREIGN KEY ("quest_id", "truth_ord") REFERENCES "quest_truth" ("quest_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `playerStart` of each quest row (ordered by `ord` where it has one).
CREATE TABLE "quest_player_start" (
  "quest_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL REFERENCES "fact"("id"),
  PRIMARY KEY ("quest_id", "ord"),
  FOREIGN KEY ("quest_id") REFERENCES "quest" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `cast` of each quest row (ordered by `ord` where it has one).
CREATE TABLE "quest_cast" (
  "quest_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "id" TEXT NOT NULL REFERENCES "npc"("id"),
  "wants" TEXT NOT NULL,
  "fears" TEXT NOT NULL,
  "persona_backstory" TEXT,
  PRIMARY KEY ("quest_id", "ord"),
  FOREIGN KEY ("quest_id") REFERENCES "quest" ("id") ON DELETE CASCADE
);

-- Home of one row per key of `cast[].knowledge` of each quest_cast row (ordered by `ord` where it has one).
CREATE TABLE "quest_cast_knowledge" (
  "quest_id" TEXT NOT NULL,
  "cast_ord" INTEGER NOT NULL,
  "fact_id" TEXT NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("quest_id", "cast_ord", "fact_id"),
  FOREIGN KEY ("quest_id", "cast_ord") REFERENCES "quest_cast" ("quest_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `cast[].changes` of each quest_cast row (ordered by `ord` where it has one).
CREATE TABLE "quest_cast_change" (
  "quest_id" TEXT NOT NULL,
  "cast_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "at_stage" INTEGER NOT NULL,
  "fact" TEXT NOT NULL REFERENCES "fact"("id"),
  "to" TEXT NOT NULL,
  PRIMARY KEY ("quest_id", "cast_ord", "ord"),
  FOREIGN KEY ("quest_id", "cast_ord") REFERENCES "quest_cast" ("quest_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `things` of each quest row (ordered by `ord` where it has one).
CREATE TABLE "quest_thing" (
  "quest_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "id" TEXT NOT NULL,
  "kind" TEXT NOT NULL,
  "source" TEXT NOT NULL,
  "where" TEXT,
  PRIMARY KEY ("quest_id", "ord"),
  FOREIGN KEY ("quest_id") REFERENCES "quest" ("id") ON DELETE CASCADE
);

-- Home of one row per key of `things[].states` of each quest_thing row (ordered by `ord` where it has one).
CREATE TABLE "quest_thing_state" (
  "quest_id" TEXT NOT NULL,
  "things_ord" INTEGER NOT NULL,
  "state" TEXT NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("quest_id", "things_ord", "state"),
  FOREIGN KEY ("quest_id", "things_ord") REFERENCES "quest_thing" ("quest_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `conclusions` of each quest row (ordered by `ord` where it has one).
CREATE TABLE "quest_conclusion" (
  "quest_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "id" TEXT NOT NULL,
  "statement" TEXT NOT NULL,
  PRIMARY KEY ("quest_id", "ord"),
  FOREIGN KEY ("quest_id") REFERENCES "quest" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `conclusions[].clues` of each quest_conclusion row (ordered by `ord` where it has
-- one).
CREATE TABLE "quest_conclusion_clue" (
  "quest_id" TEXT NOT NULL,
  "conclusions_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("quest_id", "conclusions_ord", "ord"),
  FOREIGN KEY ("quest_id", "conclusions_ord") REFERENCES "quest_conclusion" ("quest_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `clues` of each quest row (ordered by `ord` where it has one).
CREATE TABLE "quest_clue" (
  "quest_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "id" TEXT NOT NULL,
  "form" TEXT NOT NULL,
  "carrier" TEXT NOT NULL,
  PRIMARY KEY ("quest_id", "ord"),
  FOREIGN KEY ("quest_id") REFERENCES "quest" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `clues[].gives` of each quest_clue row (ordered by `ord` where it has one).
CREATE TABLE "quest_clue_gives" (
  "quest_id" TEXT NOT NULL,
  "clues_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL REFERENCES "fact"("id"),
  PRIMARY KEY ("quest_id", "clues_ord", "ord"),
  FOREIGN KEY ("quest_id", "clues_ord") REFERENCES "quest_clue" ("quest_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `clues[].supports` of each quest_clue row (ordered by `ord` where it has one).
CREATE TABLE "quest_clue_supports" (
  "quest_id" TEXT NOT NULL,
  "clues_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("quest_id", "clues_ord", "ord"),
  FOREIGN KEY ("quest_id", "clues_ord") REFERENCES "quest_clue" ("quest_id", "ord") ON DELETE CASCADE
);

-- Home of one row per key of `shapeData` of each quest row (ordered by `ord` where it has one).
CREATE TABLE "quest_shape_data" (
  "quest_id" TEXT NOT NULL,
  "section" TEXT NOT NULL,
  "value" TEXT,
  "wrong" TEXT,
  "test" TEXT,
  "needed" INTEGER,
  "too_few" TEXT,
  "right" TEXT,
  "partial" TEXT,
  "unsolved" TEXT,
  PRIMARY KEY ("quest_id", "section"),
  FOREIGN KEY ("quest_id") REFERENCES "quest" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `shapeData{*}` of each quest_shape_data row (ordered by `ord` where it has one).
CREATE TABLE "quest_shape_data_items" (
  "quest_id" TEXT NOT NULL,
  "section" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT,
  "speaker" TEXT,
  "says" TEXT,
  "refuted_by" TEXT,
  "from" TEXT,
  "suspect" TEXT,
  PRIMARY KEY ("quest_id", "section", "ord"),
  FOREIGN KEY ("quest_id", "section") REFERENCES "quest_shape_data" ("quest_id", "section") ON DELETE CASCADE
);

-- Home of one row per element of `stages[].actions` of each quest_stage row (ordered by `ord` where it has one).
CREATE TABLE "quest_action" (
  "quest_id" TEXT NOT NULL,
  "stages_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "skill" TEXT,
  "use" TEXT NOT NULL,
  "setting" TEXT,
  "note" TEXT,
  "system" TEXT,
  "target" TEXT,
  PRIMARY KEY ("quest_id", "stages_ord", "ord"),
  FOREIGN KEY ("quest_id", "stages_ord") REFERENCES "quest_stage" ("quest_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `stages[].learns` of each quest_stage row (ordered by `ord` where it has one).
CREATE TABLE "quest_stage_learns" (
  "quest_id" TEXT NOT NULL,
  "stages_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL REFERENCES "fact"("id"),
  PRIMARY KEY ("quest_id", "stages_ord", "ord"),
  FOREIGN KEY ("quest_id", "stages_ord") REFERENCES "quest_stage" ("quest_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `stages[].approaches` of each quest_stage row (ordered by `ord` where it has one).
CREATE TABLE "quest_approach" (
  "quest_id" TEXT NOT NULL,
  "stages_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "id" TEXT NOT NULL,
  PRIMARY KEY ("quest_id", "stages_ord", "ord"),
  FOREIGN KEY ("quest_id", "stages_ord") REFERENCES "quest_stage" ("quest_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `stages[].approaches[].actions` of each quest_approach row (ordered by `ord` where it
-- has one).
CREATE TABLE "quest_approach_action" (
  "quest_id" TEXT NOT NULL,
  "stages_ord" INTEGER NOT NULL,
  "approaches_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "skill" TEXT NOT NULL,
  "use" TEXT NOT NULL,
  "setting" TEXT,
  "target" TEXT,
  "note" TEXT,
  PRIMARY KEY ("quest_id", "stages_ord", "approaches_ord", "ord"),
  FOREIGN KEY ("quest_id", "stages_ord", "approaches_ord") REFERENCES "quest_approach" ("quest_id", "stages_ord", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `endings` of each quest row (ordered by `ord` where it has one).
CREATE TABLE "quest_ending" (
  "quest_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "id" TEXT NOT NULL,
  "when" TEXT NOT NULL,
  "world" TEXT NOT NULL REFERENCES "action_list"("id"),
  "seen" TEXT NOT NULL,
  "rewards" TEXT REFERENCES "action_list"("id"),
  PRIMARY KEY ("quest_id", "ord"),
  FOREIGN KEY ("quest_id") REFERENCES "quest" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `topics` of each quest row (ordered by `ord` where it has one).
CREATE TABLE "quest_topic" (
  "quest_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "id" TEXT NOT NULL,
  "new" BOOLEAN CHECK ("new" IN (0, 1)),
  "label" TEXT NOT NULL,
  "person" TEXT NOT NULL REFERENCES "npc"("id"),
  "essential" BOOLEAN NOT NULL CHECK ("essential" IN (0, 1)),
  "intent" TEXT NOT NULL,
  PRIMARY KEY ("quest_id", "ord"),
  FOREIGN KEY ("quest_id") REFERENCES "quest" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `topics[].stages` of each quest_topic row (ordered by `ord` where it has one).
CREATE TABLE "quest_topic_stage" (
  "quest_id" TEXT NOT NULL,
  "topics_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" INTEGER NOT NULL,
  PRIMARY KEY ("quest_id", "topics_ord", "ord"),
  FOREIGN KEY ("quest_id", "topics_ord") REFERENCES "quest_topic" ("quest_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `topics[].uses` of each quest_topic row (ordered by `ord` where it has one).
CREATE TABLE "quest_topic_uses" (
  "quest_id" TEXT NOT NULL,
  "topics_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL REFERENCES "fact"("id"),
  PRIMARY KEY ("quest_id", "topics_ord", "ord"),
  FOREIGN KEY ("quest_id", "topics_ord") REFERENCES "quest_topic" ("quest_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `topics[].hides` of each quest_topic row (ordered by `ord` where it has one).
CREATE TABLE "quest_topic_hides" (
  "quest_id" TEXT NOT NULL,
  "topics_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL REFERENCES "fact"("id"),
  PRIMARY KEY ("quest_id", "topics_ord", "ord"),
  FOREIGN KEY ("quest_id", "topics_ord") REFERENCES "quest_topic" ("quest_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `review.findings` of each quest row (ordered by `ord` where it has one).
CREATE TABLE "quest_review_finding" (
  "quest_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "id" TEXT NOT NULL,
  "severity" TEXT NOT NULL,
  "finding" TEXT NOT NULL,
  "answer" TEXT NOT NULL,
  PRIMARY KEY ("quest_id", "ord"),
  FOREIGN KEY ("quest_id") REFERENCES "quest" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `review.findings[].ids` of each quest_review_finding row (ordered by `ord` where it
-- has one).
CREATE TABLE "quest_review_finding_ids" (
  "quest_id" TEXT NOT NULL,
  "review_findings_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("quest_id", "review_findings_ord", "ord"),
  FOREIGN KEY ("quest_id", "review_findings_ord") REFERENCES "quest_review_finding" ("quest_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `sockets` of each quest row (ordered by `ord` where it has one).
CREATE TABLE "quest_socket" (
  "quest_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("quest_id", "ord"),
  FOREIGN KEY ("quest_id") REFERENCES "quest" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `cast[].persona.invented` of each quest_cast row (ordered by `ord` where it has one).
CREATE TABLE "quest_cast_persona_invented" (
  "quest_id" TEXT NOT NULL,
  "cast_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("quest_id", "cast_ord", "ord"),
  FOREIGN KEY ("quest_id", "cast_ord") REFERENCES "quest_cast" ("quest_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `shapeData{*}[].to` of each quest_shape_data_items row (ordered by `ord` where it has
-- one).
CREATE TABLE "quest_shape_data_items_to" (
  "quest_id" TEXT NOT NULL,
  "section" TEXT NOT NULL,
  "items_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("quest_id", "section", "items_ord", "ord"),
  FOREIGN KEY ("quest_id", "section", "items_ord") REFERENCES "quest_shape_data_items" ("quest_id", "section", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `shapeData{*}.exhibits` of each quest_shape_data row (ordered by `ord` where it has
-- one).
CREATE TABLE "quest_shape_data_exhibits" (
  "quest_id" TEXT NOT NULL,
  "section" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("quest_id", "section", "ord"),
  FOREIGN KEY ("quest_id", "section") REFERENCES "quest_shape_data" ("quest_id", "section") ON DELETE CASCADE
);

-- Home of one row per element of `shapeData{*}.closedRun` of each quest_shape_data row (ordered by `ord` where it has
-- one).
CREATE TABLE "quest_shape_data_closed_run" (
  "quest_id" TEXT NOT NULL,
  "section" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("quest_id", "section", "ord"),
  FOREIGN KEY ("quest_id", "section") REFERENCES "quest_shape_data" ("quest_id", "section") ON DELETE CASCADE
);

-- Home of one row per element of `topics[].grants` of each quest_topic row (ordered by `ord` where it has one).
CREATE TABLE "quest_topic_grants" (
  "quest_id" TEXT NOT NULL,
  "topics_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("quest_id", "topics_ord", "ord"),
  FOREIGN KEY ("quest_id", "topics_ord") REFERENCES "quest_topic" ("quest_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `stages[].directions` of each quest_stage row (ordered by `ord` where it has one).
CREATE TABLE "quest_stage_directions" (
  "quest_id" TEXT NOT NULL,
  "stages_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "to" TEXT NOT NULL,
  "from" TEXT NOT NULL,
  PRIMARY KEY ("quest_id", "stages_ord", "ord"),
  FOREIGN KEY ("quest_id", "stages_ord") REFERENCES "quest_stage" ("quest_id", "ord") ON DELETE CASCADE
);

-- == quest_budget_exception ==

-- Home of each recorded departure from the shape budget (old 55 §47c step 5): the packet, the line, the shape and the
-- one-line reason.
CREATE TABLE "quest_budget_exception" (
  "packet" TEXT NOT NULL,
  "line" TEXT NOT NULL,
  "shape" TEXT NOT NULL,
  "reason" TEXT NOT NULL,
  PRIMARY KEY ("packet", "line", "shape")
);

-- == journal_entry ==

-- Home of every journal entry's text: its quest, surface, the facts it states and those it is grounded in.
CREATE TABLE "journal_entry" (
  "id" TEXT NOT NULL,
  "quest_id" TEXT NOT NULL REFERENCES "quest"("id"),
  "surface" TEXT NOT NULL,
  "text" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- Home of one row per element of `factIds` of each journal_entry row (ordered by `ord` where it has one).
CREATE TABLE "journal_entry_fact" (
  "journal_entry_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL REFERENCES "fact"("id"),
  PRIMARY KEY ("journal_entry_id", "ord"),
  FOREIGN KEY ("journal_entry_id") REFERENCES "journal_entry" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `groundedIn` of each journal_entry row (ordered by `ord` where it has one).
CREATE TABLE "journal_entry_grounding" (
  "journal_entry_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("journal_entry_id", "ord"),
  FOREIGN KEY ("journal_entry_id") REFERENCES "journal_entry" ("id") ON DELETE CASCADE
);

-- == fact ==

-- Home of every fact (decision 0030: facts): what is true, as the place states it (`claim`) and as a person says it
-- (`says`), with the cues that name it; a place fact carries its place and carrier, a quest fact its quest and where
-- it comes from (`from_ref`: a truth event, a place fact or a culture-sheet entry); `ord` is its position in its
-- place's or quest's list (the order they state it in).
CREATE TABLE "fact" (
  "id" TEXT NOT NULL,
  "says" TEXT,
  "claim" TEXT,
  "source_field" TEXT,
  "kind" TEXT,
  "carrier_built_uid" TEXT,
  "carrier_built_type" TEXT,
  "place_id" TEXT REFERENCES "place"("id"),
  "ord" INTEGER,
  "carrier_queued_type" TEXT,
  "carrier_queued_ref" TEXT,
  "tag" TEXT,
  "provision" TEXT,
  "from_ref" TEXT,
  "quest_id" TEXT REFERENCES "quest"("id"),
  PRIMARY KEY ("id"),
  UNIQUE ("place_id", "ord"),
  UNIQUE ("quest_id", "ord")
);

-- Home of one row per element of `cues` of each fact row (ordered by `ord` where it has one).
CREATE TABLE "fact_cue" (
  "fact_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("fact_id", "ord"),
  FOREIGN KEY ("fact_id") REFERENCES "fact" ("id") ON DELETE CASCADE
);

-- == place_build ==

-- Home of the old project's last build of each place, kept as the guide for 0.4 §d and the place briefs: its name,
-- position, extent, route, stands, built sockets, landmarks, the people and their topics, services and hostility (the
-- counts are derived and dropped).
CREATE TABLE "place_build" (
  "place_id" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "footprint_radius_m" REAL NOT NULL,
  "extent_radius_m" REAL NOT NULL,
  PRIMARY KEY ("place_id")
);

-- Home of one row per element of `positionM` of each place_build row (ordered by `ord` where it has one).
CREATE TABLE "place_build_position_m" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" REAL NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place_build" ("place_id") ON DELETE CASCADE
);

-- Home of one row per element of `boundaryM` of each place_build row (ordered by `ord` where it has one).
CREATE TABLE "place_build_boundary_m" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "x" REAL NOT NULL,
  "y" REAL NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place_build" ("place_id") ON DELETE CASCADE
);

-- Home of one row per element of `extentM` of each place_build row (ordered by `ord` where it has one).
CREATE TABLE "place_build_extent_m" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "x" REAL NOT NULL,
  "y" REAL NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place_build" ("place_id") ON DELETE CASCADE
);

-- Home of the optional block `route` of each place_build row (ordered by `ord` where it has one).
CREATE TABLE "place_build_route" (
  "place_id" TEXT NOT NULL,
  "line_id" TEXT NOT NULL,
  "kind" TEXT NOT NULL,
  "name" TEXT,
  "from" TEXT NOT NULL,
  "to" TEXT NOT NULL,
  "vertex_m_x" REAL NOT NULL,
  "vertex_m_y" REAL NOT NULL,
  "off_extent_m" REAL NOT NULL,
  "along_m" REAL NOT NULL,
  "length_m" REAL NOT NULL,
  PRIMARY KEY ("place_id"),
  FOREIGN KEY ("place_id") REFERENCES "place_build" ("place_id") ON DELETE CASCADE
);

-- Home of one row per element of `stands` of each place_build row (ordered by `ord` where it has one).
CREATE TABLE "place_build_stands" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "id" TEXT NOT NULL,
  "asset_id" TEXT NOT NULL,
  "kind" TEXT NOT NULL,
  "layer" TEXT,
  "position_m_x" REAL NOT NULL,
  "position_m_y" REAL NOT NULL,
  "position_m_z" REAL NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place_build" ("place_id") ON DELETE CASCADE
);

-- Home of one row per element of `sockets` of each place_build row (ordered by `ord` where it has one).
CREATE TABLE "place_build_sockets" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "id" TEXT NOT NULL,
  "kind" TEXT NOT NULL,
  "area" TEXT NOT NULL,
  "position_m_x" REAL NOT NULL,
  "position_m_y" REAL NOT NULL,
  "position_m_z" REAL NOT NULL,
  "slot" TEXT,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place_build" ("place_id") ON DELETE CASCADE
);

-- Home of one row per element of `sockets[].fills` of each place_build_sockets row (ordered by `ord` where it has
-- one).
CREATE TABLE "place_build_sockets_fills" (
  "place_id" TEXT NOT NULL,
  "sockets_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "sockets_ord", "ord"),
  FOREIGN KEY ("place_id", "sockets_ord") REFERENCES "place_build_sockets" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `landmarks` of each place_build row (ordered by `ord` where it has one).
CREATE TABLE "place_build_landmarks" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "id" TEXT NOT NULL,
  "what" TEXT NOT NULL,
  "via" TEXT NOT NULL,
  "position_m_x" REAL NOT NULL,
  "position_m_y" REAL NOT NULL,
  "position_m_z" REAL NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place_build" ("place_id") ON DELETE CASCADE
);

-- Home of one row per element of `landmarks[].inSight.places` of each place_build_landmarks row (ordered by `ord`
-- where it has one).
CREATE TABLE "place_build_landmarks_in_sight_places" (
  "place_id" TEXT NOT NULL,
  "landmarks_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "landmarks_ord", "ord"),
  FOREIGN KEY ("place_id", "landmarks_ord") REFERENCES "place_build_landmarks" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `landmarks[].inSight.here` of each place_build_landmarks row (ordered by `ord` where
-- it has one).
CREATE TABLE "place_build_landmarks_in_sight_here" (
  "place_id" TEXT NOT NULL,
  "landmarks_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "landmarks_ord", "ord"),
  FOREIGN KEY ("place_id", "landmarks_ord") REFERENCES "place_build_landmarks" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `people` of each place_build row (ordered by `ord` where it has one).
CREATE TABLE "place_person" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "id" TEXT NOT NULL REFERENCES "npc"("id"),
  "name" TEXT NOT NULL,
  "role" TEXT NOT NULL,
  "post" TEXT NOT NULL,
  "hostility" TEXT NOT NULL REFERENCES "hostility_stance"("id"),
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place_build" ("place_id") ON DELETE CASCADE
);

-- Home of one row per element of `people[].services` of each place_person row (ordered by `ord` where it has one).
CREATE TABLE "place_person_services" (
  "place_id" TEXT NOT NULL,
  "people_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "people_ord", "ord"),
  FOREIGN KEY ("place_id", "people_ord") REFERENCES "place_person" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `people[].topics` of each place_person row (ordered by `ord` where it has one).
CREATE TABLE "place_person_topics" (
  "place_id" TEXT NOT NULL,
  "people_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL REFERENCES "topic"("id"),
  PRIMARY KEY ("place_id", "people_ord", "ord"),
  FOREIGN KEY ("place_id", "people_ord") REFERENCES "place_person" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `services` of each place_build row (ordered by `ord` where it has one).
CREATE TABLE "place_build_services" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "kind" TEXT NOT NULL,
  "promised" BOOLEAN NOT NULL CHECK ("promised" IN (0, 1)),
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place_build" ("place_id") ON DELETE CASCADE
);

-- Home of one row per element of `services[].by` of each place_build_services row (ordered by `ord` where it has one).
CREATE TABLE "place_build_services_by" (
  "place_id" TEXT NOT NULL,
  "services_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL REFERENCES "npc"("id"),
  PRIMARY KEY ("place_id", "services_ord", "ord"),
  FOREIGN KEY ("place_id", "services_ord") REFERENCES "place_build_services" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `services[].filledBy` of each place_build_services row (ordered by `ord` where it has
-- one).
CREATE TABLE "place_build_services_filled_by" (
  "place_id" TEXT NOT NULL,
  "services_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "services_ord", "ord"),
  FOREIGN KEY ("place_id", "services_ord") REFERENCES "place_build_services" ("place_id", "ord") ON DELETE CASCADE
);

-- Home of the optional block `hostility` of each place_build row (ordered by `ord` where it has one).
CREATE TABLE "place_build_hostility" (
  "place_id" TEXT NOT NULL,
  "baseline" TEXT NOT NULL REFERENCES "hostility_stance"("id"),
  "owner" TEXT REFERENCES "faction"("id"),
  "clearable" BOOLEAN NOT NULL CHECK ("clearable" IN (0, 1)),
  "respawn" TEXT NOT NULL,
  PRIMARY KEY ("place_id"),
  FOREIGN KEY ("place_id") REFERENCES "place_build" ("place_id") ON DELETE CASCADE
);

-- Home of one row per element of `hostility.flips` of each place_build_hostility row (ordered by `ord` where it has
-- one).
CREATE TABLE "place_build_hostility_flips" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "to" TEXT NOT NULL REFERENCES "hostility_stance"("id"),
  "when" TEXT NOT NULL REFERENCES "condition"("id"),
  "scope" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ord"),
  FOREIGN KEY ("place_id") REFERENCES "place_build_hostility" ("place_id") ON DELETE CASCADE
);

-- == topic ==

-- Home of every dialogue topic of the topic web: class, label, glossary term, what it is keyed to and what requires
-- it.
CREATE TABLE "topic" (
  "id" TEXT NOT NULL,
  "topic_class" TEXT NOT NULL REFERENCES "topic_class"("id"),
  "label" TEXT NOT NULL,
  "glossary_term" TEXT REFERENCES "glossary_term"("id"),
  "keys_place" TEXT REFERENCES "place"("id"),
  "keys_aspect" TEXT,
  "keys_faction" TEXT REFERENCES "faction"("id"),
  "keys_quest" TEXT REFERENCES "quest"("id"),
  PRIMARY KEY ("id")
);

-- Home of one row per element of `requiredFor.places` of each topic row (ordered by `ord` where it has one).
CREATE TABLE "topic_required_for_places" (
  "topic_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL REFERENCES "place"("id"),
  PRIMARY KEY ("topic_id", "ord"),
  FOREIGN KEY ("topic_id") REFERENCES "topic" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `requiredFor.glossaryTerms` of each topic row (ordered by `ord` where it has one).
CREATE TABLE "topic_required_for_glossary_terms" (
  "topic_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL REFERENCES "glossary_term"("id"),
  PRIMARY KEY ("topic_id", "ord"),
  FOREIGN KEY ("topic_id") REFERENCES "topic" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `requiredFor.factions` of each topic row (ordered by `ord` where it has one).
CREATE TABLE "topic_required_for_factions" (
  "topic_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL REFERENCES "faction"("id"),
  PRIMARY KEY ("topic_id", "ord"),
  FOREIGN KEY ("topic_id") REFERENCES "topic" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `requiredFor.roles` of each topic row (ordered by `ord` where it has one).
CREATE TABLE "topic_required_for_roles" (
  "topic_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("topic_id", "ord"),
  FOREIGN KEY ("topic_id") REFERENCES "topic" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `requiredFor.people` of each topic row (ordered by `ord` where it has one).
CREATE TABLE "topic_required_for_people" (
  "topic_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL REFERENCES "npc"("id"),
  PRIMARY KEY ("topic_id", "ord"),
  FOREIGN KEY ("topic_id") REFERENCES "topic" ("id") ON DELETE CASCADE
);

-- == glossary_term ==

-- Home of every glossary term: its forms, its topic, whether it is act-one and opaque, its gloss and section.
-- `load_bearing` marks the forms the old glossary listed as load-bearing.
CREATE TABLE "glossary_term" (
  "id" TEXT NOT NULL,
  "topic_id" TEXT NOT NULL REFERENCES "topic"("id"),
  "act_one" BOOLEAN NOT NULL CHECK ("act_one" IN (0, 1)),
  "opaque" BOOLEAN NOT NULL CHECK ("opaque" IN (0, 1)),
  "gloss" TEXT NOT NULL,
  "section" TEXT NOT NULL,
  "load_bearing" TEXT,
  PRIMARY KEY ("id")
);

-- Home of one row per element of `forms` of each glossary_term row (ordered by `ord` where it has one).
CREATE TABLE "glossary_form" (
  "glossary_term_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("glossary_term_id", "ord"),
  FOREIGN KEY ("glossary_term_id") REFERENCES "glossary_term" ("id") ON DELETE CASCADE
);

-- == dialogue_line ==

-- Home of every dialogue line (decision 0030: lines): greeting, topic answer, override or pool line; its speaker (or
-- its pool), topic, words and variants, conditions (`available`), the facts it states, links and what it does when
-- delivered. The imported lines are reference only (0024 §7): `status` says so.
CREATE TABLE "dialogue_line" (
  "id" TEXT NOT NULL,
  "type" TEXT NOT NULL REFERENCES "line_type"("id"),
  "speaker" TEXT REFERENCES "npc"("id"),
  "words" TEXT NOT NULL,
  "available" TEXT REFERENCES "condition"("id"),
  "variants_low" TEXT,
  "variants_high" TEXT,
  "place_id" TEXT REFERENCES "place"("id"),
  "pool" TEXT,
  "slot" TEXT,
  "keys_topic" TEXT REFERENCES "topic"("id"),
  "derived_from_pool_line_id" TEXT REFERENCES "dialogue_line"("id"),
  "derived_from_hash" TEXT,
  "fallback_for" TEXT,
  "on_delivered" TEXT REFERENCES "action_list"("id"),
  "fallback" BOOLEAN CHECK ("fallback" IN (0, 1)),
  PRIMARY KEY ("id")
);

-- Home of one row per element of `factIds` of each dialogue_line row (ordered by `ord` where it has one).
CREATE TABLE "dialogue_line_fact" (
  "dialogue_line_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL REFERENCES "fact"("id"),
  PRIMARY KEY ("dialogue_line_id", "ord"),
  FOREIGN KEY ("dialogue_line_id") REFERENCES "dialogue_line" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `links` of each dialogue_line row (ordered by `ord` where it has one).
CREATE TABLE "dialogue_line_link" (
  "dialogue_line_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL REFERENCES "topic"("id"),
  PRIMARY KEY ("dialogue_line_id", "ord"),
  FOREIGN KEY ("dialogue_line_id") REFERENCES "dialogue_line" ("id") ON DELETE CASCADE
);

-- == culture_sheet ==

-- Home of every culture sheet (decision 0030: culture): one node of the culture chain (province, region, people,
-- faction, settlement, group, household) with its parent, speech, opinions per topic class, views and dissent; its
-- entries are `culture_entry`.
CREATE TABLE "culture_sheet" (
  "id" TEXT NOT NULL,
  "level" TEXT NOT NULL REFERENCES "culture_level"("id"),
  "name" TEXT NOT NULL,
  "parent" TEXT REFERENCES "culture_sheet"("id"),
  "faction_id" TEXT REFERENCES "faction"("id"),
  "speech_formality" TEXT NOT NULL REFERENCES "formality"("id"),
  "speech_register_ref" TEXT,
  "deviation_rate" REAL NOT NULL CHECK ("deviation_rate" BETWEEN 0 AND 0.5),
  "file" TEXT NOT NULL,
  "rank" TEXT,
  "race" TEXT REFERENCES "race"("id"),
  "upbringing" TEXT,
  "region_id" TEXT REFERENCES "region"("id"),
  "place_id" TEXT REFERENCES "place"("id"),
  PRIMARY KEY ("id")
);

-- Home of every culture-sheet entry, by kind (norm, taboo, value, contempt, address term, oath, never-said, grievance,
-- rumour), in order, with its source.
CREATE TABLE "culture_entry" (
  "culture_sheet_id" TEXT NOT NULL,
  "kind" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "text" TEXT NOT NULL,
  "source" TEXT NOT NULL,
  PRIMARY KEY ("culture_sheet_id", "kind", "ord"),
  FOREIGN KEY ("culture_sheet_id") REFERENCES "culture_sheet" ("id") ON DELETE CASCADE
);

-- Home of one row per key of `opinions` of each culture_sheet row (ordered by `ord` where it has one).
CREATE TABLE "culture_opinion" (
  "culture_sheet_id" TEXT NOT NULL,
  "opinion_class" TEXT NOT NULL REFERENCES "opinion_class"("id"),
  "lean" INTEGER NOT NULL CHECK ("lean" BETWEEN -2 AND 2),
  "text" TEXT NOT NULL,
  "source" TEXT NOT NULL,
  PRIMARY KEY ("culture_sheet_id", "opinion_class"),
  FOREIGN KEY ("culture_sheet_id") REFERENCES "culture_sheet" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `views` of each culture_sheet row (ordered by `ord` where it has one).
CREATE TABLE "culture_view" (
  "culture_sheet_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "node" TEXT NOT NULL REFERENCES "culture_sheet"("id"),
  "lean" INTEGER NOT NULL CHECK ("lean" BETWEEN -2 AND 2),
  "text" TEXT NOT NULL,
  "source" TEXT NOT NULL,
  PRIMARY KEY ("culture_sheet_id", "ord"),
  FOREIGN KEY ("culture_sheet_id") REFERENCES "culture_sheet" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `members` of each culture_sheet row (ordered by `ord` where it has one).
CREATE TABLE "culture_member" (
  "culture_sheet_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL REFERENCES "npc"("id"),
  PRIMARY KEY ("culture_sheet_id", "ord"),
  FOREIGN KEY ("culture_sheet_id") REFERENCES "culture_sheet" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `dissent` of each culture_sheet row (ordered by `ord` where it has one).
CREATE TABLE "culture_dissent" (
  "culture_sheet_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "person_id" TEXT NOT NULL REFERENCES "npc"("id"),
  "topic" TEXT NOT NULL,
  "lean" INTEGER NOT NULL CHECK ("lean" BETWEEN -2 AND 2),
  "text" TEXT NOT NULL,
  "source" TEXT NOT NULL,
  PRIMARY KEY ("culture_sheet_id", "ord"),
  FOREIGN KEY ("culture_sheet_id") REFERENCES "culture_sheet" ("id") ON DELETE CASCADE
);

-- == stance ==

-- Home of each person's stance and voice (decision 0030: culture): the culture chain they speak from, per topic class
-- their lean and where it comes from and any deviation, and their voice.
CREATE TABLE "stance" (
  "person_id" TEXT NOT NULL REFERENCES "npc"("id"),
  "voice_quirk" TEXT NOT NULL,
  "voice_chatter" TEXT NOT NULL CHECK ("voice_chatter" IN ('terse', 'plain', 'chatty', 'rambling')),
  "voice_contraction_rate" REAL NOT NULL CHECK ("voice_contraction_rate" BETWEEN 0 AND 1),
  "voice_address_term" TEXT NOT NULL,
  "voice_favourite_subject" TEXT NOT NULL,
  "reviewed" BOOLEAN NOT NULL CHECK ("reviewed" IN (0, 1)),
  "place_id" TEXT NOT NULL REFERENCES "place"("id"),
  PRIMARY KEY ("person_id")
);

-- Home of one row per element of `chain` of each stance row (ordered by `ord` where it has one).
CREATE TABLE "stance_chain" (
  "person_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL REFERENCES "culture_sheet"("id"),
  PRIMARY KEY ("person_id", "ord"),
  FOREIGN KEY ("person_id") REFERENCES "stance" ("person_id") ON DELETE CASCADE
);

-- Home of one row per key of `topics` of each stance row (ordered by `ord` where it has one).
CREATE TABLE "stance_topic" (
  "person_id" TEXT NOT NULL,
  "opinion_class" TEXT NOT NULL REFERENCES "opinion_class"("id"),
  "lean" INTEGER NOT NULL CHECK ("lean" BETWEEN -2 AND 2),
  "from" TEXT NOT NULL REFERENCES "culture_sheet"("id"),
  "deviation_lean" INTEGER CHECK ("deviation_lean" BETWEEN -2 AND 2),
  "deviation_reason" TEXT,
  PRIMARY KEY ("person_id", "opinion_class"),
  FOREIGN KEY ("person_id") REFERENCES "stance" ("person_id") ON DELETE CASCADE
);

-- Home of one row per key of `voice.answerLength` of each stance row (ordered by `ord` where it has one).
CREATE TABLE "stance_answer_length" (
  "person_id" TEXT NOT NULL,
  "length_class" TEXT NOT NULL,
  "min" INTEGER NOT NULL CHECK ("min" BETWEEN 6 AND 60),
  "max" INTEGER NOT NULL CHECK ("max" BETWEEN 10 AND 80),
  PRIMARY KEY ("person_id", "length_class"),
  FOREIGN KEY ("person_id") REFERENCES "stance" ("person_id") ON DELETE CASCADE
);

-- Home of one row per element of `voice.neverMentions` of each stance row (ordered by `ord` where it has one).
CREATE TABLE "stance_never_mentions" (
  "person_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("person_id", "ord"),
  FOREIGN KEY ("person_id") REFERENCES "stance" ("person_id") ON DELETE CASCADE
);

-- Home of one row per element of `voice.explainerOf` of each stance row (ordered by `ord` where it has one).
CREATE TABLE "stance_explainer_of" (
  "person_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL REFERENCES "topic"("id"),
  PRIMARY KEY ("person_id", "ord"),
  FOREIGN KEY ("person_id") REFERENCES "stance" ("person_id") ON DELETE CASCADE
);

-- == route ==

-- Home of every named route (road, track, boat lane, ferry, rootway): its mode, class, ends, aliases, confidence and
-- sources (decision 0030: routes).
CREATE TABLE "route" (
  "id" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "mode" TEXT NOT NULL REFERENCES "route_mode"("id"),
  "class" TEXT NOT NULL REFERENCES "route_class"("id"),
  "from" TEXT NOT NULL,
  "to" TEXT NOT NULL,
  "confidence" TEXT NOT NULL,
  "notes" TEXT,
  "solved" BOOLEAN CHECK ("solved" IN (0, 1)),
  "geometry_id" TEXT,
  "reason" TEXT,
  "condition" TEXT,
  "condition_why" TEXT,
  "kind" TEXT,
  "note" TEXT,
  "joins_route_id" TEXT REFERENCES "route"("id"),
  PRIMARY KEY ("id")
);

-- Home of one row per element of `aliases` of each route row (ordered by `ord` where it has one).
CREATE TABLE "route_alias" (
  "route_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("route_id", "ord"),
  FOREIGN KEY ("route_id") REFERENCES "route" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `sources` of each route row (ordered by `ord` where it has one).
CREATE TABLE "route_source" (
  "route_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("route_id", "ord"),
  FOREIGN KEY ("route_id") REFERENCES "route" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `stages` of each route row (ordered by `ord` where it has one).
CREATE TABLE "route_stages" (
  "route_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("route_id", "ord"),
  FOREIGN KEY ("route_id") REFERENCES "route" ("id") ON DELETE CASCADE
);

-- == authored_track ==

-- Home of each hand-authored track's polyline (metres).
CREATE TABLE "authored_track" (
  "id" TEXT NOT NULL,
  "why" TEXT NOT NULL,
  "source" TEXT,
  PRIMARY KEY ("id")
);

-- Home of one row per element of `pointsM` of each authored_track row (ordered by `ord` where it has one).
CREATE TABLE "authored_track_point" (
  "authored_track_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "x" REAL NOT NULL,
  "y" REAL NOT NULL,
  PRIMARY KEY ("authored_track_id", "ord"),
  FOREIGN KEY ("authored_track_id") REFERENCES "authored_track" ("id") ON DELETE CASCADE
);

-- == authored_track_settings ==

-- Home of routes/authored-routes.json's single set of rules and notes (one row).
CREATE TABLE "authored_track_settings" (
  "id" TEXT NOT NULL,
  "kind" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- == minor_waterway_settings ==

-- Home of routes/authored-minor-waterways.json's single set of rules and notes (one row).
CREATE TABLE "minor_waterway_settings" (
  "id" TEXT NOT NULL,
  "kind" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- Home of one row per element of `waterways` of each minor_waterway_settings row (ordered by `ord` where it has one).
CREATE TABLE "minor_waterway_settings_waterways" (
  "minor_waterway_settings_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  PRIMARY KEY ("minor_waterway_settings_id", "ord"),
  FOREIGN KEY ("minor_waterway_settings_id") REFERENCES "minor_waterway_settings" ("id") ON DELETE CASCADE
);

-- == harbour ==

-- Home of each city's harbour station: the place that serves as its quay and why.
CREATE TABLE "harbour" (
  "id" TEXT NOT NULL,
  "place_id" TEXT NOT NULL REFERENCES "place"("id"),
  "why" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- == junction ==

-- Home of each road junction or pin: position, roads and why.
CREATE TABLE "junction" (
  "id" TEXT NOT NULL,
  "kind" TEXT NOT NULL,
  "position_m_x" REAL NOT NULL,
  "position_m_y" REAL NOT NULL,
  "why" TEXT NOT NULL,
  "confidence" TEXT NOT NULL,
  "approach" BOOLEAN CHECK ("approach" IN (0, 1)),
  PRIMARY KEY ("id")
);

-- Home of one row per element of `roads` of each junction row (ordered by `ord` where it has one).
CREATE TABLE "junction_road" (
  "junction_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL REFERENCES "route"("id"),
  PRIMARY KEY ("junction_id", "ord"),
  FOREIGN KEY ("junction_id") REFERENCES "junction" ("id") ON DELETE CASCADE
);

-- == lane_terminal ==

-- Home of each boat lane's terminal where the city anchor is inland.
CREATE TABLE "lane_terminal" (
  "id" TEXT NOT NULL,
  "terminal_uv_x" REAL NOT NULL,
  "terminal_uv_y" REAL NOT NULL,
  "dock_id" TEXT NOT NULL,
  "why" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- == rootworm_station ==

-- Home of each rootworm station (root node): its place and kind.
CREATE TABLE "rootworm_station" (
  "id" TEXT NOT NULL,
  "place_id" TEXT NOT NULL REFERENCES "place"("id"),
  "kind" TEXT NOT NULL,
  "why" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- == rootworm_rootway ==

-- Home of each rootway between two root nodes.
CREATE TABLE "rootworm_rootway" (
  "ord" INTEGER NOT NULL,
  "from" TEXT NOT NULL REFERENCES "rootworm_station"("id"),
  "to" TEXT NOT NULL REFERENCES "rootworm_station"("id"),
  PRIMARY KEY ("ord")
);

-- == route_structure_exemplar ==

-- Home of each exemplar route-structure place (old 2.W): its way, chainage and position.
CREATE TABLE "route_structure_exemplar" (
  "id" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "classification_type" TEXT NOT NULL,
  "way_id" TEXT NOT NULL REFERENCES "route"("id"),
  "chainage_m_x" INTEGER NOT NULL,
  "chainage_m_y" INTEGER NOT NULL,
  "position_m_x" REAL NOT NULL,
  "position_m_y" REAL NOT NULL,
  "footprint_radius_m" INTEGER NOT NULL,
  "region" TEXT NOT NULL,
  "culture" TEXT NOT NULL,
  "setting_class" TEXT NOT NULL,
  "condition" TEXT NOT NULL,
  "why_founding" TEXT NOT NULL,
  "why_site_advantages" TEXT NOT NULL,
  "why_occupants_motive" TEXT NOT NULL,
  "why_pressures" TEXT NOT NULL,
  "why_would_change_if" TEXT NOT NULL,
  "ends_east_place_id" TEXT REFERENCES "place"("id"),
  "ends_east_via" TEXT,
  "ends_east_at_m_x" REAL,
  "ends_east_at_m_y" REAL,
  "ends_west_way_id" TEXT REFERENCES "route"("id"),
  "ends_west_towards" TEXT,
  "ends_west_at_m_x" REAL,
  "ends_west_at_m_y" REAL,
  "dressing_rules" TEXT NOT NULL,
  "dressing_evidence" TEXT NOT NULL,
  "ends_southeast_way_id" TEXT REFERENCES "route"("id"),
  "ends_southeast_towards" TEXT,
  "ends_southeast_at_m_x" REAL,
  "ends_southeast_at_m_y" REAL,
  "ends_northwest_way_id" TEXT REFERENCES "route"("id"),
  "ends_northwest_towards" TEXT,
  "ends_northwest_at_m_x" REAL,
  "ends_northwest_at_m_y" REAL,
  "ends_southwest_way_id" TEXT,
  "ends_southwest_towards" TEXT,
  "ends_southwest_at_m_x" REAL,
  "ends_southwest_at_m_y" REAL,
  PRIMARY KEY ("id")
);

-- Home of one row per element of `structures` of each route_structure_exemplar row (ordered by `ord` where it has
-- one).
CREATE TABLE "route_structure_exemplar_structures" (
  "route_structure_exemplar_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "kind" TEXT NOT NULL,
  "id" TEXT NOT NULL,
  "crossing_id" TEXT REFERENCES "water_crossing"("id"),
  "built_by" TEXT NOT NULL,
  "junction_id" TEXT REFERENCES "junction"("id"),
  "status" TEXT,
  "pending_why" TEXT,
  PRIMARY KEY ("route_structure_exemplar_id", "ord"),
  FOREIGN KEY ("route_structure_exemplar_id") REFERENCES "route_structure_exemplar" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `life.creatures` of each route_structure_exemplar row (ordered by `ord` where it has
-- one).
CREATE TABLE "route_structure_exemplar_life_creatures" (
  "route_structure_exemplar_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "slot_id" TEXT NOT NULL,
  "species" TEXT NOT NULL,
  "headcount" INTEGER NOT NULL,
  "band" TEXT NOT NULL,
  "den" TEXT NOT NULL,
  "network" TEXT NOT NULL,
  PRIMARY KEY ("route_structure_exemplar_id", "ord"),
  FOREIGN KEY ("route_structure_exemplar_id") REFERENCES "route_structure_exemplar" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `life.creatures[].territory` of each route_structure_exemplar_life_creatures row
-- (ordered by `ord` where it has one).
CREATE TABLE "route_structure_exemplar_life_creatures_territory" (
  "route_structure_exemplar_id" TEXT NOT NULL,
  "life_creatures_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("route_structure_exemplar_id", "life_creatures_ord", "ord"),
  FOREIGN KEY ("route_structure_exemplar_id", "life_creatures_ord") REFERENCES "route_structure_exemplar_life_creatures" ("route_structure_exemplar_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `life.creatures[].lines` of each route_structure_exemplar_life_creatures row (ordered
-- by `ord` where it has one).
CREATE TABLE "route_structure_exemplar_life_creatures_lines" (
  "route_structure_exemplar_id" TEXT NOT NULL,
  "life_creatures_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  PRIMARY KEY ("route_structure_exemplar_id", "life_creatures_ord", "ord"),
  FOREIGN KEY ("route_structure_exemplar_id", "life_creatures_ord") REFERENCES "route_structure_exemplar_life_creatures" ("route_structure_exemplar_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `structures[].crossingIds` of each route_structure_exemplar_structures row (ordered
-- by `ord` where it has one).
CREATE TABLE "route_structure_exemplar_structures_crossing_ids" (
  "route_structure_exemplar_id" TEXT NOT NULL,
  "structures_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("route_structure_exemplar_id", "structures_ord", "ord"),
  FOREIGN KEY ("route_structure_exemplar_id", "structures_ord") REFERENCES "route_structure_exemplar_structures" ("route_structure_exemplar_id", "ord") ON DELETE CASCADE
);

-- == route_structure ==

-- Home of each structure on a route (stair, bridge, causeway...): its piece, span and rise.
CREATE TABLE "route_structure" (
  "id" TEXT NOT NULL,
  "cap_deg" REAL NOT NULL,
  "family" TEXT NOT NULL,
  "from_m" REAL NOT NULL,
  "gap_m" REAL NOT NULL,
  "kind" TEXT NOT NULL,
  "piece_ref" TEXT NOT NULL,
  "rise_m" REAL NOT NULL,
  "sourcing" TEXT NOT NULL,
  "to_m" REAL NOT NULL,
  "way_id" TEXT NOT NULL REFERENCES "route"("id"),
  "why" TEXT NOT NULL,
  "window_from_m" REAL NOT NULL,
  "window_to_m" REAL NOT NULL,
  "worst_deg" REAL NOT NULL,
  "built_by" TEXT,
  PRIMARY KEY ("id")
);

-- == route_structure_settings ==

-- Home of routes/route-structures.json's single set of rules and notes (one row).
CREATE TABLE "route_structure_settings" (
  "id" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- Home of one row per element of `ferryCrossings` of each route_structure_settings row (ordered by `ord` where it has
-- one).
CREATE TABLE "route_structure_settings_ferry_crossings" (
  "route_structure_settings_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  PRIMARY KEY ("route_structure_settings_id", "ord"),
  FOREIGN KEY ("route_structure_settings_id") REFERENCES "route_structure_settings" ("id") ON DELETE CASCADE
);

-- == travel_craft ==

-- Home of each craft and landing piece a travel service uses. Verified against the built kits on 2026-09-09, not
-- chosen from filenames. `watercraft-v1` is built (45/45) and its GLB is deployed to apps/world-studio/public/kits.
-- Sizes are metres from the built kit manifests. Nothing was sourced for this work; every credit is already in
-- README.md.
CREATE TABLE "travel_craft" (
  "id" TEXT NOT NULL,
  "kit" TEXT NOT NULL,
  "piece_ref" TEXT NOT NULL,
  "size_m_x" REAL NOT NULL,
  "size_m_y" REAL NOT NULL,
  "size_m_z" REAL NOT NULL,
  "mooring_post" TEXT,
  "gangplank" TEXT,
  PRIMARY KEY ("id")
);

-- == travel_harbour_station ==

-- Home of each city's harbour station id.
CREATE TABLE "travel_harbour_station" (
  "id" TEXT NOT NULL,
  "place_id" TEXT NOT NULL REFERENCES "place"("id"),
  "station_id" TEXT NOT NULL REFERENCES "travel_station"("id"),
  "why" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- == travel_road_edge ==

-- Home of each road edge between travel stations.
CREATE TABLE "travel_road_edge" (
  "ord" INTEGER NOT NULL,
  "from" TEXT NOT NULL,
  "road_id" TEXT NOT NULL REFERENCES "route"("id"),
  "to" TEXT NOT NULL,
  "why" TEXT NOT NULL,
  PRIMARY KEY ("ord")
);

-- == travel_rootway ==

-- Home of each rootway as a travel edge.
CREATE TABLE "travel_rootway" (
  "id" TEXT NOT NULL,
  "from" TEXT NOT NULL,
  "status" TEXT NOT NULL,
  "to" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- == travel_service ==

-- Home of every travel service: its form, fare, hops and operator.
CREATE TABLE "travel_service" (
  "id" TEXT NOT NULL,
  "available" TEXT REFERENCES "condition"("id"),
  "fare_gold" INTEGER NOT NULL,
  "form" TEXT NOT NULL,
  "operator_nearest_place_id" TEXT REFERENCES "place"("id"),
  "operator_role" TEXT NOT NULL,
  "operator_slot_id" TEXT NOT NULL,
  "operator_socket_station_id" TEXT NOT NULL REFERENCES "travel_station"("id"),
  "quest_use" TEXT,
  "service_kind" TEXT NOT NULL,
  "status" TEXT NOT NULL,
  "text_hail" TEXT NOT NULL,
  "text_name" TEXT NOT NULL,
  "why" TEXT NOT NULL,
  "craft" TEXT,
  "hull_class" TEXT,
  "operator_socket_ref" TEXT,
  "text_refusal" TEXT,
  "water_class" TEXT,
  "water_name" TEXT,
  "retired_why" TEXT,
  PRIMARY KEY ("id")
);

-- Home of one row per element of `fare.freeIf` of each travel_service row (ordered by `ord` where it has one).
CREATE TABLE "travel_service_fare_free_if" (
  "travel_service_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  PRIMARY KEY ("travel_service_id", "ord"),
  FOREIGN KEY ("travel_service_id") REFERENCES "travel_service" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `hops` of each travel_service row (ordered by `ord` where it has one).
CREATE TABLE "travel_service_hops" (
  "travel_service_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "follows_lane" TEXT,
  "from" TEXT NOT NULL REFERENCES "travel_station"("id"),
  "length_m" REAL NOT NULL,
  "to" TEXT NOT NULL REFERENCES "travel_station"("id"),
  "follows_road" TEXT,
  "unresolved" BOOLEAN CHECK ("unresolved" IN (0, 1)),
  "follows_rootway" TEXT,
  PRIMARY KEY ("travel_service_id", "ord"),
  FOREIGN KEY ("travel_service_id") REFERENCES "travel_service" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `refusedIf` of each travel_service row (ordered by `ord` where it has one).
CREATE TABLE "travel_service_refused_if" (
  "travel_service_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "predicate" TEXT NOT NULL,
  "region" TEXT,
  "value" INTEGER,
  "is" TEXT,
  PRIMARY KEY ("travel_service_id", "ord"),
  FOREIGN KEY ("travel_service_id") REFERENCES "travel_service" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `stations` of each travel_service row (ordered by `ord` where it has one).
CREATE TABLE "travel_service_stations" (
  "travel_service_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("travel_service_id", "ord"),
  FOREIGN KEY ("travel_service_id") REFERENCES "travel_service" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `hops[].follows.lanes` of each travel_service_hops row (ordered by `ord` where it has
-- one).
CREATE TABLE "travel_service_hops_follows_lanes" (
  "travel_service_id" TEXT NOT NULL,
  "hops_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("travel_service_id", "hops_ord", "ord"),
  FOREIGN KEY ("travel_service_id", "hops_ord") REFERENCES "travel_service_hops" ("travel_service_id", "ord") ON DELETE CASCADE
);

-- Home of the optional block `hops[].jettyM` of each travel_service_hops row (ordered by `ord` where it has one).
CREATE TABLE "travel_service_hops_jetty_m" (
  "travel_service_id" TEXT NOT NULL,
  "hops_ord" INTEGER NOT NULL,
  "station_dunmer_north_hutan_tzel" REAL,
  "station_dunmer_north_the_black_stage" REAL,
  "station_dunmer_north_hissmir" REAL,
  "station_dunmer_north_riverwalk" REAL,
  "station_dunmer_north_murkwater" REAL,
  "station_dunmer_north_the_tide_fair" REAL,
  "station_hist_heartland_treasure_hunters_live_camp" REAL,
  "station_saxhleel_coast_portdun_mont" REAL,
  "station_imperial_fringe_slough_point" REAL,
  "station_mercantile_coast_moonmarch" REAL,
  "station_mercantile_coast_mudfoot" REAL,
  "station_mercantile_coast_quinrawl_anchorage" REAL,
  "station_imperial_penal_south_lake_divers_yard" REAL,
  "station_imperial_penal_south_lake_ferry_stage" REAL,
  "station_mercantile_coast_bright_throat_village" REAL,
  "station_mercantile_coast_screen_watch" REAL,
  "station_mercantile_coast_oliis_ferry_stage" REAL,
  "station_imperial_penal_south_bramman_head" REAL,
  "station_imperial_penal_south_manned_toll_tower" REAL,
  "station_mercantile_coast_bramman_river_ferry" REAL,
  PRIMARY KEY ("travel_service_id", "hops_ord"),
  FOREIGN KEY ("travel_service_id", "hops_ord") REFERENCES "travel_service_hops" ("travel_service_id", "ord") ON DELETE CASCADE
);

-- Home of the optional block `crossing` of each travel_service row (ordered by `ord` where it has one).
CREATE TABLE "travel_service_crossing" (
  "travel_service_id" TEXT NOT NULL,
  "entity_id" TEXT NOT NULL,
  "entity_kind" TEXT NOT NULL,
  "id" TEXT NOT NULL,
  "max_depth_m" REAL NOT NULL,
  "span_m" REAL NOT NULL,
  PRIMARY KEY ("travel_service_id"),
  FOREIGN KEY ("travel_service_id") REFERENCES "travel_service" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `landings` of each travel_service row (ordered by `ord` where it has one).
CREATE TABLE "travel_service_landings" (
  "travel_service_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("travel_service_id", "ord"),
  FOREIGN KEY ("travel_service_id") REFERENCES "travel_service" ("id") ON DELETE CASCADE
);

-- Home of the optional block `measured` of each travel_service row (ordered by `ord` where it has one).
CREATE TABLE "travel_service_measured" (
  "travel_service_id" TEXT NOT NULL,
  "max_depth_m" REAL NOT NULL,
  "source" TEXT NOT NULL,
  "span_m" REAL NOT NULL,
  PRIMARY KEY ("travel_service_id"),
  FOREIGN KEY ("travel_service_id") REFERENCES "travel_service" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `severs` of each travel_service row (ordered by `ord` where it has one).
CREATE TABLE "travel_service_severs" (
  "travel_service_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("travel_service_id", "ord"),
  FOREIGN KEY ("travel_service_id") REFERENCES "travel_service" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `hops[].follows.bodies` of each travel_service_hops row (ordered by `ord` where it
-- has one).
CREATE TABLE "travel_service_hops_follows_bodies" (
  "travel_service_id" TEXT NOT NULL,
  "hops_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("travel_service_id", "hops_ord", "ord"),
  FOREIGN KEY ("travel_service_id", "hops_ord") REFERENCES "travel_service_hops" ("travel_service_id", "ord") ON DELETE CASCADE
);

-- Home of the optional block `hops[].laneDepthM` of each travel_service_hops row (ordered by `ord` where it has one).
CREATE TABLE "travel_service_hops_lane_depth_m" (
  "travel_service_id" TEXT NOT NULL,
  "hops_ord" INTEGER NOT NULL,
  "station_imperial_penal_south_bramman_head" REAL,
  "station_imperial_penal_south_lake_ferry_stage" REAL,
  "station_imperial_penal_south_lake_divers_yard" REAL,
  "station_imperial_penal_south_manned_toll_tower" REAL,
  "station_mercantile_coast_bramman_river_ferry" REAL,
  "station_mercantile_coast_oliis_ferry_stage" REAL,
  PRIMARY KEY ("travel_service_id", "hops_ord"),
  FOREIGN KEY ("travel_service_id", "hops_ord") REFERENCES "travel_service_hops" ("travel_service_id", "ord") ON DELETE CASCADE
);

-- Home of one row per element of `warnings` of each travel_service row (ordered by `ord` where it has one).
CREATE TABLE "travel_service_warnings" (
  "travel_service_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "at" TEXT NOT NULL,
  "depth_m" REAL NOT NULL,
  "kind" TEXT NOT NULL,
  "need_m" REAL NOT NULL,
  PRIMARY KEY ("travel_service_id", "ord"),
  FOREIGN KEY ("travel_service_id") REFERENCES "travel_service" ("id") ON DELETE CASCADE
);

-- == travel_station ==

-- Home of every travel station (ferry landing, place station, root node): its kind, place, berth and piece.
CREATE TABLE "travel_station" (
  "id" TEXT NOT NULL,
  "kind" TEXT NOT NULL,
  "piece" TEXT,
  "position_m_x" REAL NOT NULL,
  "position_m_y" REAL NOT NULL,
  "status" TEXT NOT NULL,
  "notes" TEXT,
  "place_id" TEXT REFERENCES "place"("id"),
  "root_kind" TEXT,
  "why" TEXT,
  PRIMARY KEY ("id")
);

-- Home of the optional block `berth` of each travel_station row (ordered by `ord` where it has one).
CREATE TABLE "travel_station_berth" (
  "travel_station_id" TEXT NOT NULL,
  "depth_m" REAL NOT NULL,
  "entity_id" TEXT NOT NULL,
  "entity_kind" TEXT NOT NULL,
  "floats" BOOLEAN NOT NULL CHECK ("floats" IN (0, 1)),
  "hull_class" TEXT NOT NULL,
  "jetty_m" REAL NOT NULL,
  "position_m_x" REAL NOT NULL,
  "position_m_y" REAL NOT NULL,
  PRIMARY KEY ("travel_station_id"),
  FOREIGN KEY ("travel_station_id") REFERENCES "travel_station" ("id") ON DELETE CASCADE
);

-- Home of the optional block `operator` of each travel_station row (ordered by `ord` where it has one).
CREATE TABLE "travel_station_operator" (
  "travel_station_id" TEXT NOT NULL,
  "role" TEXT NOT NULL,
  "slot_id" TEXT NOT NULL,
  "socket_station_id" TEXT NOT NULL REFERENCES "rootworm_station"("id"),
  PRIMARY KEY ("travel_station_id"),
  FOREIGN KEY ("travel_station_id") REFERENCES "travel_station" ("id") ON DELETE CASCADE
);

-- == travel_transfer_edge ==

-- Home of each walking transfer between stations.
CREATE TABLE "travel_transfer_edge" (
  "ord" INTEGER NOT NULL,
  "from" TEXT NOT NULL,
  "to" TEXT NOT NULL,
  "why" TEXT NOT NULL,
  PRIMARY KEY ("ord")
);

-- == travel_settings ==

-- Home of routes/travel-services.json's single set of rules and notes (one row).
CREATE TABLE "travel_settings" (
  "id" TEXT NOT NULL,
  "operator_model_x" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- Home of one row per element of `operatorModel.canon` of each travel_settings row (ordered by `ord` where it has
-- one).
CREATE TABLE "travel_settings_operator_model_canon" (
  "travel_settings_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("travel_settings_id", "ord"),
  FOREIGN KEY ("travel_settings_id") REFERENCES "travel_settings" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `operatorModel.extrapolated` of each travel_settings row (ordered by `ord` where it
-- has one).
CREATE TABLE "travel_settings_operator_model_extrapolated" (
  "travel_settings_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("travel_settings_id", "ord"),
  FOREIGN KEY ("travel_settings_id") REFERENCES "travel_settings" ("id") ON DELETE CASCADE
);

-- Home of one row per key of `policy` of each travel_settings row (ordered by `ord` where it has one).
CREATE TABLE "travel_settings_policy" (
  "travel_settings_id" TEXT NOT NULL,
  "key" TEXT NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("travel_settings_id", "key"),
  FOREIGN KEY ("travel_settings_id") REFERENCES "travel_settings" ("id") ON DELETE CASCADE
);

-- Home of one row per key of `vocabulary` of each travel_settings row (ordered by `ord` where it has one).
CREATE TABLE "travel_settings_vocabulary" (
  "travel_settings_id" TEXT NOT NULL,
  "key" TEXT NOT NULL,
  PRIMARY KEY ("travel_settings_id", "key"),
  FOREIGN KEY ("travel_settings_id") REFERENCES "travel_settings" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `vocabulary{*}` of each travel_settings_vocabulary row (ordered by `ord` where it has
-- one).
CREATE TABLE "travel_settings_vocabulary_items" (
  "travel_settings_id" TEXT NOT NULL,
  "vocabulary_key" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("travel_settings_id", "vocabulary_key", "ord"),
  FOREIGN KEY ("travel_settings_id", "vocabulary_key") REFERENCES "travel_settings_vocabulary" ("travel_settings_id", "key") ON DELETE CASCADE
);

-- == water_crossing ==

-- Home of each place a way crosses water: the way, the water body, banks, span, depth and band.
CREATE TABLE "water_crossing" (
  "id" TEXT NOT NULL,
  "way_name" TEXT NOT NULL,
  "way_class" TEXT NOT NULL,
  "network" TEXT NOT NULL,
  "water" TEXT NOT NULL,
  "entity_id" TEXT NOT NULL,
  "entity_kind" TEXT NOT NULL,
  "position_m_x" REAL NOT NULL,
  "position_m_y" REAL NOT NULL,
  "span_m" REAL NOT NULL,
  "max_depth_m" REAL NOT NULL,
  "nearest_place_id" TEXT NOT NULL REFERENCES "place"("id"),
  "nearest_place_name" TEXT NOT NULL,
  "nearest_place_m" REAL NOT NULL,
  "band" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- Home of one row per element of `banks` of each water_crossing row (ordered by `ord` where it has one).
CREATE TABLE "water_crossing_banks" (
  "water_crossing_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "x" REAL NOT NULL,
  "y" REAL NOT NULL,
  PRIMARY KEY ("water_crossing_id", "ord"),
  FOREIGN KEY ("water_crossing_id") REFERENCES "water_crossing" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `servesRoutes` of each water_crossing row (ordered by `ord` where it has one).
CREATE TABLE "water_crossing_serves_routes" (
  "water_crossing_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("water_crossing_id", "ord"),
  FOREIGN KEY ("water_crossing_id") REFERENCES "water_crossing" ("id") ON DELETE CASCADE
);

-- == water_crossing_settings ==

-- Home of routes/water-crossings.json's single set of rules and notes (one row).
CREATE TABLE "water_crossing_settings" (
  "id" TEXT NOT NULL,
  "thresholds_deep_m" REAL NOT NULL,
  "thresholds_ford_max_m" REAL NOT NULL,
  "thresholds_ford_max_depth_m" REAL NOT NULL,
  "thresholds_ferry_min_m" REAL NOT NULL,
  "thresholds_dedupe_grid_m" REAL NOT NULL,
  PRIMARY KEY ("id")
);

-- == attribute ==

-- Home of the seven attributes (no Luck; 76 §117) and each one's reference value.
CREATE TABLE "attribute" (
  "id" TEXT NOT NULL,
  "reference" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

-- == sheet_rules ==

-- Home of the sheet's single set of attribute rules (one row; 76 §117): the start range, the favoured bonus, the
-- purchase cap.
CREATE TABLE "sheet_rules" (
  "id" TEXT NOT NULL,
  "start_range_min" INTEGER NOT NULL,
  "start_range_max" INTEGER NOT NULL,
  "favoured_bonus" INTEGER NOT NULL,
  "purchase_cap" INTEGER NOT NULL,
  "design_ref" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- == skill ==

-- Home of the 27 skills (76 §118): governing attribute, specialisation, family, the bands that scale with skill and
-- the attribute its score uses.
CREATE TABLE "skill" (
  "id" TEXT NOT NULL,
  "gov" TEXT NOT NULL REFERENCES "attribute"("id"),
  "spec" TEXT NOT NULL REFERENCES "specialisation"("id"),
  "family" TEXT NOT NULL REFERENCES "skill_family"("id"),
  "score" TEXT REFERENCES "attribute"("id"),
  "armour_class" TEXT,
  "temper_grades_x" INTEGER,
  "temper_grades_y" INTEGER,
  "temper_grades_z" INTEGER,
  "temper_per_grade" REAL,
  "score_divisor" INTEGER,
  "constant_effect_at" INTEGER,
  PRIMARY KEY ("id")
);

-- Home of one row per key of `bands` of each skill row (ordered by `ord` where it has one).
CREATE TABLE "skill_bands" (
  "skill_id" TEXT NOT NULL,
  "band" TEXT NOT NULL,
  "x" REAL NOT NULL,
  "y" REAL NOT NULL,
  PRIMARY KEY ("skill_id", "band"),
  FOREIGN KEY ("skill_id") REFERENCES "skill" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `effectVisibilityAt` of each skill row (ordered by `ord` where it has one).
CREATE TABLE "skill_effect_visibility_at" (
  "skill_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" INTEGER NOT NULL,
  PRIMARY KEY ("skill_id", "ord"),
  FOREIGN KEY ("skill_id") REFERENCES "skill" ("id") ON DELETE CASCADE
);

-- == race ==

-- Home of every race (76 §127, UESP Morrowind:Races, old 0089, 0096): base attributes by sex, skill bonuses, permanent
-- effects and powers.
CREATE TABLE "race" (
  "id" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- Home of one row per key of `skillBonuses` of each race row (ordered by `ord` where it has one).
CREATE TABLE "race_skill_bonus" (
  "race_id" TEXT NOT NULL,
  "skill" TEXT NOT NULL REFERENCES "skill"("id"),
  "value" INTEGER NOT NULL,
  PRIMARY KEY ("race_id", "skill"),
  FOREIGN KEY ("race_id") REFERENCES "race" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `effects` of each race row (ordered by `ord` where it has one).
CREATE TABLE "race_effect" (
  "race_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "field" TEXT NOT NULL,
  "op" TEXT NOT NULL,
  "magnitude" REAL NOT NULL,
  "permanent" BOOLEAN NOT NULL CHECK ("permanent" IN (0, 1)),
  PRIMARY KEY ("race_id", "ord"),
  FOREIGN KEY ("race_id") REFERENCES "race" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `powers` of each race row (ordered by `ord` where it has one).
CREATE TABLE "race_power" (
  "race_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  PRIMARY KEY ("race_id", "ord"),
  FOREIGN KEY ("race_id") REFERENCES "race" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `baseAttributes` of each race row (ordered by `ord` where it has one).
CREATE TABLE "race_base_attribute" (
  "race_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "sex" TEXT NOT NULL REFERENCES "sex"("id"),
  "attribute" TEXT NOT NULL REFERENCES "attribute"("id"),
  "value" INTEGER NOT NULL,
  PRIMARY KEY ("race_id", "ord"),
  FOREIGN KEY ("race_id") REFERENCES "race" ("id") ON DELETE CASCADE
);

-- == class ==

-- Home of every class (76): specialisation, favoured attributes, major and minor skills.
CREATE TABLE "class" (
  "id" TEXT NOT NULL,
  "specialization" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- Home of one row per element of `favouredAttributes` of each class row (ordered by `ord` where it has one).
CREATE TABLE "class_favoured_attributes" (
  "class_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("class_id", "ord"),
  FOREIGN KEY ("class_id") REFERENCES "class" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `majors` of each class row (ordered by `ord` where it has one).
CREATE TABLE "class_majors" (
  "class_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("class_id", "ord"),
  FOREIGN KEY ("class_id") REFERENCES "class" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `minors` of each class row (ordered by `ord` where it has one).
CREATE TABLE "class_minors" (
  "class_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("class_id", "ord"),
  FOREIGN KEY ("class_id") REFERENCES "class" ("id") ON DELETE CASCADE
);

-- == class_rules ==

-- Home of the class file's single set of rules (one row).
CREATE TABLE "class_rules" (
  "id" TEXT NOT NULL,
  "starting_skill" INTEGER NOT NULL,
  "major_bonus" INTEGER NOT NULL,
  "minor_bonus" INTEGER NOT NULL,
  "specialization_bonus" INTEGER NOT NULL,
  "favoured_attribute_bonus" INTEGER NOT NULL,
  PRIMARY KEY ("id")
);

-- == birthsign ==

-- Home of every birthsign (76): its effects, abilities and powers.
CREATE TABLE "birthsign" (
  "id" TEXT NOT NULL,
  "guardian" TEXT,
  "month" INTEGER,
  PRIMARY KEY ("id")
);

-- Home of one row per element of `effects` of each birthsign row (ordered by `ord` where it has one).
CREATE TABLE "birthsign_effects" (
  "birthsign_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "field" TEXT NOT NULL,
  "op" TEXT NOT NULL,
  "magnitude" REAL NOT NULL,
  "permanent" BOOLEAN NOT NULL CHECK ("permanent" IN (0, 1)),
  PRIMARY KEY ("birthsign_id", "ord"),
  FOREIGN KEY ("birthsign_id") REFERENCES "birthsign" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `powers` of each birthsign row (ordered by `ord` where it has one).
CREATE TABLE "birthsign_powers" (
  "birthsign_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("birthsign_id", "ord"),
  FOREIGN KEY ("birthsign_id") REFERENCES "birthsign" ("id") ON DELETE CASCADE
);

-- Home of one row per element of `spells` of each birthsign row (ordered by `ord` where it has one).
CREATE TABLE "birthsign_spells" (
  "birthsign_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("birthsign_id", "ord"),
  FOREIGN KEY ("birthsign_id") REFERENCES "birthsign" ("id") ON DELETE CASCADE
);

-- == frozen_array ==

-- Home of every frozen terrain and hydrology array's identity (the vault fetcher's manifest): file name, SHA-256 over
-- its contents, the day it froze and why.
CREATE TABLE "frozen_array" (
  "id" TEXT NOT NULL,
  "sha256" TEXT NOT NULL CHECK (length("sha256") = 64),
  "frozen_on" TEXT NOT NULL,
  "why" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- == freeze_rules ==

-- Home of the freeze record's rules (one row).
CREATE TABLE "freeze_rules" (
  "id" TEXT NOT NULL,
  "about" TEXT NOT NULL,
  PRIMARY KEY ("id")
);

-- == Conditions and actions (docs/design/quests/85-condition-vocabulary.md as data) ==

-- Home of the condition and action vocabulary: every predicate (§A), combinator (all, any, not) and action verb
-- (§B) a quest, line, place or topic may use, with its argument shape and what it reads or does.
CREATE TABLE "condition_term" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "kind" TEXT NOT NULL CHECK ("kind" IN ('predicate', 'combinator', 'action')),
  "section" TEXT,
  "args" TEXT,
  "reads" TEXT,
  "planned" TEXT
);

-- Home of every condition: a tree of nodes; a root is named by the column that holds its id; a node is a
-- combinator over its children (ordered by `ord`) or a predicate over its arguments.
CREATE TABLE "condition" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "parent_id" TEXT REFERENCES "condition"("id") ON DELETE CASCADE,
  "ord" INTEGER,
  "term" TEXT NOT NULL REFERENCES "condition_term"("id"),
  CHECK (("parent_id" IS NULL) = ("ord" IS NULL))
);

-- Home of a predicate's arguments, in order (an id, a number, a flag or an enumeration value).
CREATE TABLE "condition_arg" (
  "condition_id" TEXT NOT NULL REFERENCES "condition"("id") ON DELETE CASCADE,
  "ord" INTEGER NOT NULL,
  "value" NOT NULL,
  PRIMARY KEY ("condition_id", "ord")
);

-- Home of every action list (a stage's onEnter, an ending's world changes, a line's onDelivered); the column
-- that holds the id is its owner.
CREATE TABLE "action_list" (
  "id" TEXT NOT NULL PRIMARY KEY
);

-- Home of each action of a list, in order: one verb of the vocabulary.
CREATE TABLE "action" (
  "list_id" TEXT NOT NULL REFERENCES "action_list"("id") ON DELETE CASCADE,
  "ord" INTEGER NOT NULL,
  "term" TEXT NOT NULL REFERENCES "condition_term"("id"),
  PRIMARY KEY ("list_id", "ord")
);

-- Home of an action's arguments, in order.
CREATE TABLE "action_arg" (
  "list_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "arg_ord" INTEGER NOT NULL,
  "value" NOT NULL,
  PRIMARY KEY ("list_id", "ord", "arg_ord"),
  FOREIGN KEY ("list_id", "ord") REFERENCES "action" ("list_id", "ord") ON DELETE CASCADE
);

-- == The FormID table (decision 0009 §3, 0030 §4) ==

-- Home of every FormID of ours: an EditorID (`ARG_` plus the world id) to the object id it was first given in its
-- plugin; append-only (an entry never changes and is never removed; the next id is past the highest ever given).
-- `entity_key` is the world row the record is generated from, when it has one. Written only by the allocator
-- (tools/argonia_world/formids.py) through db.py.
CREATE TABLE "formid" (
  "editor_id" TEXT NOT NULL PRIMARY KEY CHECK ("editor_id" GLOB 'ARG_*' AND length("editor_id") <= 99),
  "plugin" TEXT NOT NULL,
  "form_id" INTEGER NOT NULL CHECK ("form_id" BETWEEN 2048 AND 16777215),
  "record_type" TEXT,
  "entity_key" TEXT,
  UNIQUE ("plugin", "form_id")
);

-- == Keyed tables for the families later chunks migrate (decision 0030 §6) ==

-- Home of a terrain patch over the frozen heightfield. Migrated by the world track (2.W1) from world/sources/terrain/terrain-patches.json, route-grade-patches.json; until then a key only.
CREATE TABLE "terrain_patch" (
  "id" TEXT NOT NULL PRIMARY KEY
);

-- Migrated by 2.W2 (tools/argonia_world/water/migrate.py); the rest of the family is below the 0030 marker.
-- Home of a standing water body of the graph (ocean, lagoon, lake, tarn, pond, pool, plunge pool, marsh family); levelM is the high-water line (old 0063); its extent is the connected water of the frozen body-level raster around deepest_x/y (full-res samples, y south).
CREATE TABLE "hydrology_body" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "kind" TEXT,
  "origin" TEXT,
  "level_m" REAL,
  "altitude_band" TEXT,
  "area_m2" REAL,
  "max_depth_m" REAL,
  "sheet" BOOLEAN,
  "season" TEXT,
  "season_response" REAL,
  "wet_season_level_m" REAL,
  "dry_season_level_m" REAL,
  "deepest_x" INTEGER,
  "deepest_y" INTEGER,
  "bbox_x0" INTEGER,
  "bbox_y0" INTEGER,
  "bbox_x1" INTEGER,
  "bbox_y1" INTEGER,
  "region" INTEGER,
  "mean_depth_m" REAL,
  "outflow_reach_id" TEXT REFERENCES "hydrology_reach"("id"),
  "terrain_precondition_kind" TEXT,
  "terrain_precondition_level_m" REAL,
  "terrain_precondition_floor_max_m" REAL,
  "terrain_precondition_spill_m" REAL,
  "approved_id" TEXT,
  "approved_kind" TEXT,
  "approved_level_m" REAL,
  "approved_area_m2" REAL,
  "approved_measured_kind" TEXT,
  "approved_overlap_of_approved" REAL,
  "approved_part" INTEGER,
  "sink" BOOLEAN,
  "approved_unreviewed" BOOLEAN,
  "terrain_precondition_channel_level_m" REAL,
  "captured" BOOLEAN,
  "pre_carve_level_m" REAL,
  "pre_carve_area_m2" REAL,
  "pre_carve_spill_m" REAL,
  "lost_at_carve" BOOLEAN,
  "caused_by_fall_reach_id" TEXT REFERENCES "hydrology_reach"("id"),
  "joined_sea" BOOLEAN,
  "declared_by" TEXT,
  "terrain_precondition_depth_m" REAL,
  "terrain_precondition_radius_m" REAL,
  "terrain_precondition_throw_m" REAL,
  "terrain_precondition_hold_m" REAL,
  "terrain_precondition_law" TEXT,
  "name" TEXT,
  "lore" TEXT,
  "terrain_precondition_bed_m" REAL,
  "terrain_precondition_shoreline" TEXT,
  "terrain_precondition_island_radius_m" REAL,
  "terrain_precondition_island_top_m" REAL,
  "terrain_precondition_island_note" TEXT,
  "realised_by" TEXT,
  "caused_by_stage" TEXT,
  "caused_by_why" TEXT
);

-- Home of a flow edge between two bodies. Migrated by 2.W2 from world/sources/hydrology/hydrology-graph.json; until then a key only.
CREATE TABLE "hydrology_edge" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "from_body_id" TEXT REFERENCES "hydrology_body"("id"),
  "to_body_id" TEXT REFERENCES "hydrology_body"("id")
);

-- Home of an ecological region class and its polygons. Migrated by 2.W3 from world/sources/regions/authored-overrides.json; until then a key only.
CREATE TABLE "region_class" (
  "id" TEXT NOT NULL PRIMARY KEY
);

-- Home of a flora placement rule (species, density, slope, water). Migrated by 2.W4 from world/sources/flora/*.json; until then a key only.
CREATE TABLE "flora_rule" (
  "id" TEXT NOT NULL PRIMARY KEY
);

-- Home of a settlement anchor over the heightfield. Migrated by 2.W1 from world/sources/anchors/settlement-anchors.json; until then a key only.
CREATE TABLE "anchor" (
  "id" TEXT NOT NULL PRIMARY KEY
);

-- Home of a weather state of the calendar. Migrated by 2.W3 from world/sources/climate/weather-states.json; until then a key only.
CREATE TABLE "weather_state" (
  "id" TEXT NOT NULL PRIMARY KEY
);

-- Home of a star or patron constellation of the night sky. Migrated by 2.W4 from world/sources/sky/star-catalogue.json; until then a key only.
CREATE TABLE "star" (
  "id" TEXT NOT NULL PRIMARY KEY
);

-- Home of a magic effect. Migrated by 2.9 from the magic dossier; until then a key only.
CREATE TABLE "magic_effect" (
  "id" TEXT NOT NULL PRIMARY KEY
);

-- Home of a spell or power. Migrated by 2.9 from the magic dossier; until then a key only.
CREATE TABLE "spell" (
  "id" TEXT NOT NULL PRIMARY KEY
);

-- Home of a crafting recipe. Migrated by 2.10 from world/sources/economy/, registries/resource-nodes.json; until then a key only.
CREATE TABLE "recipe" (
  "id" TEXT NOT NULL PRIMARY KEY
);

-- Home of a merchant's trade class and its stock. Migrated by 2.10 from world/sources/economy/trade-classes.json; until then a key only.
CREATE TABLE "trade_class" (
  "id" TEXT NOT NULL PRIMARY KEY
);

-- Home of a blanket loot rule a container fills from. Migrated by 2.3 from world/sources/registries/loot-rules.json; until then a key only.
CREATE TABLE "loot_rule" (
  "id" TEXT NOT NULL PRIMARY KEY
);

-- Home of a trap. Migrated by 2.11 from world/sources/registries/traps.json; until then a key only.
CREATE TABLE "trap" (
  "id" TEXT NOT NULL PRIMARY KEY
);

-- Home of a hazard volume. Migrated by 2.11 from world/sources/registries/hazard-volumes.json; until then a key only.
CREATE TABLE "hazard_volume" (
  "id" TEXT NOT NULL PRIMARY KEY
);

-- Home of a physical material. Migrated by 2.6 from world/sources/registries/physical-materials.json; until then a key only.
CREATE TABLE "physical_material" (
  "id" TEXT NOT NULL PRIMARY KEY
);

-- Home of a detection rule of the notice service. Migrated by 2.11 from world/sources/registries/detection.json; until then a key only.
CREATE TABLE "detection_rule" (
  "id" TEXT NOT NULL PRIMARY KEY
);

-- Home of a boat class. Migrated by 2.8 from world/sources/vocab/boat-classes.json; until then a key only.
CREATE TABLE "boat_class" (
  "id" TEXT NOT NULL PRIMARY KEY
);

-- Home of a placed boat. Migrated by 2.8 from world/sources/placement/boats.json; until then a key only.
CREATE TABLE "boat" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "class_id" TEXT REFERENCES "boat_class"("id")
);

-- Home of a parcel of a place's blueprint. Migrated by 2.W/place builds from world/sources/blueprints/place.*.json; until then a key only.
CREATE TABLE "blueprint_parcel" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "place_id" TEXT REFERENCES "place"("id")
);

-- Home of a door of a place's blueprint. Migrated by 2.W/place builds from world/sources/blueprints/place.*.json; until then a key only.
CREATE TABLE "blueprint_door" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "place_id" TEXT REFERENCES "place"("id")
);

-- Home of one claim a place's build must keep. Migrated by the place builds from world/sources/placement/promises/*.json; until then a key only.
CREATE TABLE "promise" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "place_id" TEXT REFERENCES "place"("id")
);

-- Home of a mesh of a dependency the world may place. Migrated by the place builds from world/sources/assets/registry-*.jsonl; until then a key only.
CREATE TABLE "asset" (
  "id" TEXT NOT NULL PRIMARY KEY
);

-- Home of a culture's kit of pieces. Migrated by the place builds from world/sources/placement/culture-kits.json; until then a key only.
CREATE TABLE "culture_kit" (
  "id" TEXT NOT NULL PRIMARY KEY
);

-- == End of the 0030 migration's tables. A later chunk appends its own tables below this line. ==

-- == The hydrology family (2.W2; migrated from the old hydrology graph, decision 0030 §6) ==
-- Read through db.py by tools/argonia_world/water; the migration is tools/argonia_world/water/migrate.py.
-- Frame: east/south metres from the province's north-west corner; x = column (east), y = row (south)
-- of the 4033^2 full-res samples; levels in metres above sea.

-- Home of a river: one stem from headwater to mouth (old 0058; the graph's README).
CREATE TABLE "hydrology_river" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "name" TEXT,
  "strahler" INTEGER,
  "mouth_kind" TEXT,
  "mouth_body_id" TEXT REFERENCES "hydrology_body"("id"),
  "mouth_form" TEXT,
  "water" TEXT,
  "accum_km2" REAL,
  "length_m" REAL,
  "source_east_m" REAL,
  "source_south_m" REAL,
  "mouth_east_m" REAL,
  "mouth_south_m" REAL,
  "mouth_through_body_id" TEXT REFERENCES "hydrology_body"("id"),
  "tributary_of_river_id" TEXT REFERENCES "hydrology_river"("id"),
  "tributary_of_junction_id" TEXT REFERENCES "hydrology_junction"("id"),
  "mouth_river_id" TEXT REFERENCES "hydrology_river"("id"),
  "mouth_junction_id" TEXT REFERENCES "hydrology_junction"("id")
);

-- Home of a junction: a source, confluence or mouth of the river network.
CREATE TABLE "hydrology_junction" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "east_m" REAL,
  "south_m" REAL,
  "level_m" REAL,
  "kind" TEXT,
  "outflow_reach_id" TEXT REFERENCES "hydrology_reach"("id")
);

-- Home of a reach: a stretch of one river with one kind and one surface; levels in metres above sea.
CREATE TABLE "hydrology_reach" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "river_id" TEXT REFERENCES "hydrology_river"("id"),
  "kind" TEXT,
  "surface" TEXT,
  "band" INTEGER,
  "plunge_pool" BOOLEAN,
  "downstream_reach_id" TEXT REFERENCES "hydrology_reach"("id"),
  "from_junction_id" TEXT REFERENCES "hydrology_junction"("id"),
  "to_junction_id" TEXT REFERENCES "hydrology_junction"("id"),
  "accum_km2" REAL,
  "slope" REAL,
  "slope_max" REAL,
  "width_m" REAL,
  "depth_m" REAL,
  "length_m" REAL,
  "level_from_m" REAL,
  "level_to_m" REAL,
  "speed_ms" REAL,
  "season" TEXT,
  "tidal" BOOLEAN,
  "terrain_precondition_kind" TEXT,
  "terrain_precondition_bed_level_from_m" REAL,
  "terrain_precondition_bed_level_to_m" REAL,
  "terrain_precondition_bed_max_m" REAL,
  "terrain_precondition_width_m" REAL,
  "terrain_precondition_width_max_m" REAL,
  "terrain_precondition_shoulder_crest_m" REAL,
  "terrain_precondition_seal_cap_m" REAL,
  "water" TEXT,
  "body_id" TEXT REFERENCES "hydrology_body"("id"),
  "terrain_precondition_body_id" TEXT REFERENCES "hydrology_body"("id"),
  "terrain_precondition_level_m" REAL,
  "fall_drop_m" REAL,
  "fall_lip_level_m" REAL,
  "fall_plunge_level_m" REAL,
  "fall_plunge_body_id" TEXT REFERENCES "hydrology_body"("id"),
  "fall_lip_speed_ms" REAL,
  "fall_origin" TEXT,
  "terrain_precondition_lip_level_m" REAL,
  "terrain_precondition_plunge_level_m" REAL,
  "terrain_precondition_drop_m" REAL,
  "terrain_precondition_face_min_slope" REAL,
  "terrain_precondition_lip_notch" BOOLEAN,
  "origin" TEXT,
  "feeder" TEXT
);

-- Home of a river's reaches, headwater (ord 0) to mouth.
CREATE TABLE "hydrology_river_reach" (
  "river_id" TEXT NOT NULL REFERENCES "hydrology_river"("id"),
  "ord" INTEGER NOT NULL,
  "reach_id" TEXT NOT NULL REFERENCES "hydrology_reach"("id"),
  PRIMARY KEY ("river_id", "ord")
);

-- Home of a reach's upstream reaches.
CREATE TABLE "hydrology_reach_upstream" (
  "reach_id" TEXT NOT NULL REFERENCES "hydrology_reach"("id"),
  "ord" INTEGER NOT NULL,
  "upstream_reach_id" TEXT NOT NULL REFERENCES "hydrology_reach"("id"),
  PRIMARY KEY ("reach_id", "ord")
);

-- Home of a reach's centreline, [east, south] metres from the province's north-west corner every ~5.5 m, headwater
-- first.
CREATE TABLE "hydrology_reach_point" (
  "reach_id" TEXT NOT NULL REFERENCES "hydrology_reach"("id"),
  "ord" INTEGER NOT NULL,
  "east_m" REAL NOT NULL,
  "south_m" REAL NOT NULL,
  PRIMARY KEY ("reach_id", "ord")
);

-- Home of a junction's inflowing reaches.
CREATE TABLE "hydrology_junction_inflow" (
  "junction_id" TEXT NOT NULL REFERENCES "hydrology_junction"("id"),
  "ord" INTEGER NOT NULL,
  "reach_id" TEXT NOT NULL REFERENCES "hydrology_reach"("id"),
  PRIMARY KEY ("junction_id", "ord")
);

-- Home of a body's inflowing reaches.
CREATE TABLE "hydrology_body_inflow" (
  "body_id" TEXT NOT NULL REFERENCES "hydrology_body"("id"),
  "ord" INTEGER NOT NULL,
  "reach_id" TEXT NOT NULL REFERENCES "hydrology_reach"("id"),
  PRIMARY KEY ("body_id", "ord")
);

-- Home of the approved (16a) bodies merged into a body's approved match.
CREATE TABLE "hydrology_body_approved_merged" (
  "body_id" TEXT NOT NULL REFERENCES "hydrology_body"("id"),
  "ord" INTEGER NOT NULL,
  "merged_body_id" TEXT NOT NULL,
  PRIMARY KEY ("body_id", "ord")
);

-- Home of an authored bowl's radii (the Blackrose lake).
CREATE TABLE "hydrology_body_radius" (
  "body_id" TEXT NOT NULL REFERENCES "hydrology_body"("id"),
  "ord" INTEGER NOT NULL,
  "radius_m" REAL NOT NULL,
  PRIMARY KEY ("body_id", "ord")
);

-- Home of one setting of the hydrology graph (thresholds, grid, vocabulary, source hashes), its value as JSON text.
CREATE TABLE "hydrology_setting" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "value" TEXT NOT NULL
);

-- The water plan's plane budget (2.W2; the planner's ruling of 2026-10-29), written by
-- `python -m tools.argonia_world.water plan --write-db` (budget.py) and checked equal to the plan by every plan run.
-- Home of a cell that was over the plane budget: what it held, what it holds, and how it was brought under.
CREATE TABLE "water_budget_cell" (
  "cx" INTEGER NOT NULL,
  "cy" INTEGER NOT NULL,
  "budget" INTEGER NOT NULL,
  "planes_before" INTEGER NOT NULL,
  "planes_after" INTEGER NOT NULL,
  "outcome" TEXT NOT NULL CHECK ("outcome" IN ('merged', 'fallback')),
  "level_m" REAL,
  "ring_cut_vertices" INTEGER,
  PRIMARY KEY ("cx", "cy")
);

-- Home of one loss of the budget: an entity's water in one cell moved, dried or flooded by a kind of reduction.
-- entity_id is a hydrology_body or hydrology_reach id, or `source:<raster|sea|shore|hollow>` for water no body
-- owns; kind is snap, step-merge, dried, flooded, fallback-raised, fallback-lowered, fallback-dried,
-- fallback-flooded, or buried (a body whose patched ground stands above its level everywhere).
CREATE TABLE "water_loss" (
  "entity_id" TEXT NOT NULL,
  "cx" INTEGER NOT NULL,
  "cy" INTEGER NOT NULL,
  "kind" TEXT NOT NULL CHECK ("kind" IN ('snap', 'step-merge', 'dried', 'flooded', 'fallback-raised',
    'fallback-lowered', 'fallback-dried', 'fallback-flooded', 'buried')),
  "samples" INTEGER NOT NULL,
  "max_cm" INTEGER NOT NULL,
  "mean_cm" REAL NOT NULL,
  PRIMARY KEY ("entity_id", "cx", "cy", "kind")
);

-- Home of one regraded ground vertex: the floor a fallback cell's border stands at (terrain/water_regrade.py).
CREATE TABLE "water_regrade" (
  "x" INTEGER NOT NULL,
  "y" INTEGER NOT NULL,
  "floor_m" REAL NOT NULL,
  "cx" INTEGER NOT NULL,
  "cy" INTEGER NOT NULL,
  PRIMARY KEY ("x", "y")
);

-- == Regions, weather, light, roads and the route graph (2.W3; decision 0028: regions are the unit of authorship) ==
-- Read and written through db.py by tools/argonia_world/regions and tools/argonia_world/routes; the migration of
-- climate/weather-states.json, regions/authored-overrides.json and the per-class role totals of flora/palettes.json is
-- tools/argonia_world/regions/migrate.py (flora/palettes.json stays for 2.W4's flora_rule). Positions: metres east and
-- SOUTH from the province's north-west corner (the imported frame); cells are Skyrim grid coordinates.

-- Home of an ecological class of 20-province-design §16 (the 11 classes): what weather group and mist it carries.
CREATE TABLE "eco_class" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "name" TEXT NOT NULL,
  "weather_group_id" TEXT NOT NULL REFERENCES "weather_group"("id"),
  "misty" BOOLEAN NOT NULL CHECK ("misty" IN (0, 1)),
  "exterior" BOOLEAN NOT NULL CHECK ("exterior" IN (0, 1)),
  "about" TEXT
);

-- Home of an old region-raster class (region_class's detail): its raster id and the ecological class it belongs to.
CREATE TABLE "region_class_profile" (
  "region_class_id" TEXT NOT NULL PRIMARY KEY REFERENCES "region_class"("id"),
  "raster_id" INTEGER NOT NULL UNIQUE,
  "name" TEXT NOT NULL,
  "eco_class_id" TEXT NOT NULL REFERENCES "eco_class"("id"),
  "about" TEXT
);

-- Home of a packet's exception to region_class_profile.eco_class_id (firm ground in the north is northern transition).
CREATE TABLE "region_class_eco_override" (
  "region_class_id" TEXT NOT NULL REFERENCES "region_class"("id"),
  "region_id" TEXT NOT NULL REFERENCES "region"("id"),
  "eco_class_id" TEXT NOT NULL REFERENCES "eco_class"("id"),
  PRIMARY KEY ("region_class_id", "region_id")
);

-- Home of an owner-authored macro override polygon (u, v fractions of the province) over listed source classes.
CREATE TABLE "region_class_override" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "region_class_id" TEXT NOT NULL REFERENCES "region_class"("id"),
  "confidence" TEXT NOT NULL,
  "notes" TEXT
);
CREATE TABLE "region_class_override_point" (
  "override_id" TEXT NOT NULL REFERENCES "region_class_override"("id") ON DELETE CASCADE,
  "ord" INTEGER NOT NULL,
  "u" REAL NOT NULL,
  "v" REAL NOT NULL,
  PRIMARY KEY ("override_id", "ord")
);
CREATE TABLE "region_class_override_applies" (
  "override_id" TEXT NOT NULL REFERENCES "region_class_override"("id") ON DELETE CASCADE,
  "region_class_id" TEXT NOT NULL REFERENCES "region_class"("id"),
  PRIMARY KEY ("override_id", "region_class_id")
);

-- Home of a placement role (canopy, understorey, rock...) the region object lists fill from.
CREATE TABLE "object_role" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT NOT NULL
);

-- Home of a region class's total per role from the imported flora palette (stems per hectare, banding, clumping).
CREATE TABLE "region_class_role" (
  "region_class_id" TEXT NOT NULL REFERENCES "region_class"("id"),
  "role_id" TEXT NOT NULL REFERENCES "object_role"("id"),
  "per_ha" REAL NOT NULL CHECK ("per_ha" >= 0),
  "clump_median" REAL,
  "clump_radius_m" REAL,
  "slope_max_deg" REAL,
  "water_min_m" REAL,
  "water_max_m" REAL,
  "layers" INTEGER NOT NULL,
  PRIMARY KEY ("region_class_id", "role_id")
);

-- Home of a vanilla base form an object list may name: the vanilla record Tropical Skyrim (SSE 78044) replaces in
-- place, what it becomes there, and its quarantine review (decision 0012).
CREATE TABLE "object_form" (
  "form_key" TEXT NOT NULL PRIMARY KEY,
  "edid" TEXT NOT NULL,
  "record_type" TEXT NOT NULL CHECK ("record_type" IN ('TREE', 'STAT')),
  "role_id" TEXT NOT NULL REFERENCES "object_role"("id"),
  "ts_model" TEXT,
  "review" TEXT NOT NULL
);

-- Home of a weather group of the imported regionFrequencies (coastal, marsh, jungle, uplands, firm lowland).
CREATE TABLE "weather_group" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "label" TEXT NOT NULL
);

-- Home of a weather state's detail (weather_state holds the key).
CREATE TABLE "weather_state_profile" (
  "weather_state_id" TEXT NOT NULL PRIMARY KEY REFERENCES "weather_state"("id"),
  "name" TEXT NOT NULL,
  "visibility_factor" REAL NOT NULL,
  "wetness" REAL NOT NULL,
  "notes" TEXT
);

-- Home of a group's relative weight for a state (the imported regionFrequencies).
CREATE TABLE "weather_group_weight" (
  "weather_group_id" TEXT NOT NULL REFERENCES "weather_group"("id"),
  "weather_state_id" TEXT NOT NULL REFERENCES "weather_state"("id"),
  "weight" INTEGER NOT NULL CHECK ("weight" > 0),
  PRIMARY KEY ("weather_group_id", "weather_state_id")
);

-- Home of a season of the calendar: the one season vocabulary (the weather rule, regions/season.py, and the
-- condition vocabulary's calendarIs both read it), its share of the year and its place in the year from day 0.
-- The imported climate design (climate/weather-states.json) has these three; 85's finer five (rain-onset, monsoon,
-- flood-peak, recession) have no shares or factors in any imported climate data, so they are not seasons here.
CREATE TABLE "season" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "name" TEXT NOT NULL,
  "share" REAL NOT NULL CHECK ("share" > 0 AND "share" <= 1),
  "effects" TEXT,
  "year_ord" INTEGER NOT NULL UNIQUE
);

-- The seasons an enum argument of a condition term takes (85 §A6 calendarIs), in rank order; the season table is
-- their home, so a season named in a condition is always one the weather rule knows.
CREATE TABLE "condition_shape_season" (
  "term" TEXT NOT NULL REFERENCES "condition_shape"("term"),
  "season_id" TEXT NOT NULL REFERENCES "season"("id"),
  "ord" INTEGER NOT NULL,
  PRIMARY KEY ("term", "season_id"),
  UNIQUE ("term", "ord")
);

-- Home of a season's factor on a state's weight (wet: monsoon and storm x2; dry haze only in the dry season).
CREATE TABLE "season_factor" (
  "season_id" TEXT NOT NULL REFERENCES "season"("id"),
  "weather_state_id" TEXT NOT NULL REFERENCES "weather_state"("id"),
  "factor" REAL NOT NULL CHECK ("factor" >= 0),
  PRIMARY KEY ("season_id", "weather_state_id")
);

-- Home of an image space of ours (IMGS): the humid green-gold marsh light, as cinematic and tint values.
CREATE TABLE "image_space" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "edid" TEXT NOT NULL UNIQUE,
  "template_form_key" TEXT NOT NULL,
  "saturation" REAL NOT NULL,
  "brightness" REAL NOT NULL,
  "contrast" REAL NOT NULL,
  "tint" TEXT NOT NULL CHECK (length("tint") = 6),
  "tint_amount" REAL NOT NULL CHECK ("tint_amount" BETWEEN 0 AND 1),
  "why" TEXT NOT NULL
);

-- Home of a weather a region may draw: a vanilla WTHR that Tropical Skyrim restyles (form_key), or one of ours
-- (template_form_key duplicated, then fog and image spaces set here).
CREATE TABLE "weather" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "edid" TEXT NOT NULL UNIQUE,
  "form_key" TEXT,
  "template_form_key" TEXT,
  "weather_state_id" TEXT NOT NULL REFERENCES "weather_state"("id"),
  "fog_day_near_m" REAL,
  "fog_day_far_m" REAL,
  "fog_night_near_m" REAL,
  "fog_night_far_m" REAL,
  "fog_tint" TEXT CHECK ("fog_tint" IS NULL OR length("fog_tint") = 6),
  "image_day_id" TEXT REFERENCES "image_space"("id"),
  "image_dawn_id" TEXT REFERENCES "image_space"("id"),
  "image_night_id" TEXT REFERENCES "image_space"("id"),
  "why" TEXT NOT NULL,
  CHECK (("form_key" IS NULL) <> ("template_form_key" IS NULL))
);

-- Home of which weathers realise a state in a group, and each one's share of the state's weight.
CREATE TABLE "weather_realisation" (
  "weather_group_id" TEXT NOT NULL REFERENCES "weather_group"("id"),
  "weather_state_id" TEXT NOT NULL REFERENCES "weather_state"("id"),
  "weather_id" TEXT NOT NULL REFERENCES "weather"("id"),
  "share" REAL NOT NULL CHECK ("share" > 0),
  PRIMARY KEY ("weather_group_id", "weather_state_id", "weather_id")
);

-- Home of the province's climate (CLMT): sun times in minutes after midnight, volatility, moon phase, time scale.
CREATE TABLE "climate" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "edid" TEXT NOT NULL UNIQUE,
  "template_form_key" TEXT NOT NULL,
  "sunrise_begin_min" INTEGER NOT NULL,
  "sunrise_end_min" INTEGER NOT NULL,
  "sunset_begin_min" INTEGER NOT NULL,
  "sunset_end_min" INTEGER NOT NULL,
  "volatility" INTEGER NOT NULL CHECK ("volatility" BETWEEN 0 AND 255),
  "moon_phase_days" INTEGER NOT NULL,
  "timescale" INTEGER NOT NULL CHECK ("timescale" > 0),
  "weather_group_id" TEXT NOT NULL REFERENCES "weather_group"("id"),
  "why" TEXT NOT NULL,
  CHECK ("sunrise_begin_min" < "sunrise_end_min" AND "sunrise_end_min" < "sunset_begin_min"
         AND "sunset_begin_min" < "sunset_end_min")
);

-- Home of a region record (REGN): one per catalogue packet and ecological class present, plus the closed border.
CREATE TABLE "land_region" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "edid" TEXT NOT NULL UNIQUE,
  "region_id" TEXT REFERENCES "region"("id"),
  "eco_class_id" TEXT REFERENCES "eco_class"("id"),
  "map_name" TEXT,
  "border" BOOLEAN NOT NULL CHECK ("border" IN (0, 1)),
  "cells" INTEGER NOT NULL CHECK ("cells" >= 0),
  UNIQUE ("region_id", "eco_class_id"),
  CHECK ("border" = 1 OR ("region_id" IS NOT NULL AND "eco_class_id" IS NOT NULL))
);

-- Home of the cells of a region as runs along a cell row (cy, cx0..cx1 inclusive); the runs tile the province once.
CREATE TABLE "cell_region_run" (
  "cy" INTEGER NOT NULL,
  "cx0" INTEGER NOT NULL,
  "cx1" INTEGER NOT NULL,
  "land_region_id" TEXT NOT NULL REFERENCES "land_region"("id"),
  PRIMARY KEY ("cy", "cx0"),
  CHECK ("cx0" <= "cx1")
);

-- Home of how many of a region's cells each old raster class makes up (reconstructed; the object list's mix).
CREATE TABLE "land_region_class_share" (
  "land_region_id" TEXT NOT NULL REFERENCES "land_region"("id"),
  "region_class_id" TEXT NOT NULL REFERENCES "region_class"("id"),
  "cells" INTEGER NOT NULL CHECK ("cells" > 0),
  PRIMARY KEY ("land_region_id", "region_class_id")
);

-- Home of a region's weather list entry (RDWT): the weather, its chance, and the global a season sets.
CREATE TABLE "land_region_weather" (
  "land_region_id" TEXT NOT NULL REFERENCES "land_region"("id"),
  "weather_id" TEXT NOT NULL REFERENCES "weather"("id"),
  "chance" INTEGER NOT NULL CHECK ("chance" BETWEEN 1 AND 100),
  "season_global" TEXT,
  PRIMARY KEY ("land_region_id", "weather_id")
);

-- Home of a region's object list entry (RDOT) for the CK region generator (2.W4 runs it): density per hectare,
-- clustering, slope and height bands; water_min/max_m keep the imported water posture the CK cannot express.
CREATE TABLE "land_region_object" (
  "land_region_id" TEXT NOT NULL REFERENCES "land_region"("id"),
  "form_key" TEXT NOT NULL REFERENCES "object_form"("form_key"),
  "density_per_ha" REAL NOT NULL CHECK ("density_per_ha" > 0),
  "clustering" INTEGER NOT NULL CHECK ("clustering" BETWEEN 1 AND 255),
  "min_slope_deg" INTEGER NOT NULL,
  "max_slope_deg" INTEGER NOT NULL,
  "min_height_m" REAL,
  "max_height_m" REAL,
  "radius_m" REAL NOT NULL,
  "water_min_m" REAL,
  "water_max_m" REAL,
  "conform" BOOLEAN NOT NULL CHECK ("conform" IN (0, 1)),
  PRIMARY KEY ("land_region_id", "form_key"),
  CHECK ("min_slope_deg" <= "max_slope_deg")
);

-- Home of a road leg's surface (old 0069's six legs and two exits): the land cover it paints and its width.
CREATE TABLE "road" (
  "route_id" TEXT NOT NULL PRIMARY KEY REFERENCES "route"("id"),
  "surface_cover" INTEGER NOT NULL,
  "flat_width_m" REAL NOT NULL CHECK ("flat_width_m" > 0),
  "shoulder_m" REAL NOT NULL CHECK ("shoulder_m" >= 0),
  "length_m" REAL NOT NULL,
  "length_3d_m" REAL NOT NULL,
  "reference_length_m" REAL,
  "why" TEXT NOT NULL
);
CREATE TABLE "road_point" (
  "route_id" TEXT NOT NULL REFERENCES "road"("route_id") ON DELETE CASCADE,
  "ord" INTEGER NOT NULL,
  "x_m" REAL NOT NULL,
  "y_m" REAL NOT NULL,
  PRIMARY KEY ("route_id", "ord")
);

-- Home of a structure window on a road (bridge, boardwalk, steps, landing) from the old route-structure compile; the
-- kit piece is chosen at review (the old pieces were vanilla Whiterun stone, a Nordic tell, decision 0012).
CREATE TABLE "road_structure" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "route_id" TEXT NOT NULL REFERENCES "road"("route_id"),
  "role" TEXT NOT NULL,
  "from_m" REAL NOT NULL,
  "to_m" REAL NOT NULL,
  "x_m" REAL NOT NULL,
  "y_m" REAL NOT NULL,
  "z_m" REAL NOT NULL,
  "yaw_deg" REAL NOT NULL,
  "old_piece" TEXT NOT NULL
);

-- Home of a node of the route graph the directions generator reads (2.12): a place, junction, station or exit.
CREATE TABLE "route_node" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "kind" TEXT NOT NULL CHECK ("kind" IN ('place', 'junction', 'station', 'exit')),
  "place_id" TEXT REFERENCES "place"("id"),
  "station_id" TEXT REFERENCES "travel_station"("id"),
  "x_m" REAL NOT NULL,
  "y_m" REAL NOT NULL,
  "name" TEXT,
  CHECK (("kind" = 'exit') = ("name" IS NOT NULL))
);
-- name: what a signpost arm to an exit reads (the city its road leads to beyond the closed border); a place's arm
-- reads the place's own name.

-- Home of an edge of the route graph: one leg of a route between two nodes, its length on the ground (3D over the
-- 2.W1 heights for land legs, straight for water and root legs).
CREATE TABLE "route_edge" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "route_id" TEXT NOT NULL REFERENCES "route"("id"),
  "from_node_id" TEXT NOT NULL REFERENCES "route_node"("id"),
  "to_node_id" TEXT NOT NULL REFERENCES "route_node"("id"),
  "mode" TEXT NOT NULL REFERENCES "route_mode"("id"),
  "length_m" REAL NOT NULL CHECK ("length_m" > 0),
  "from_chain_m" REAL,
  "to_chain_m" REAL,
  CHECK ("from_node_id" <> "to_node_id")
);

-- Home of a landmark along an edge: a place within sight of the leg, at its chainage.
CREATE TABLE "route_edge_landmark" (
  "edge_id" TEXT NOT NULL REFERENCES "route_edge"("id") ON DELETE CASCADE,
  "place_id" TEXT NOT NULL REFERENCES "place"("id"),
  "at_m" REAL NOT NULL,
  PRIMARY KEY ("edge_id", "place_id")
);

-- Home of a signpost at a road node; each arm names a destination node (the arm reads that place's name, so a sign
-- carries no text of its own: sign_purpose 'waymark').
CREATE TABLE "signpost" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "node_id" TEXT NOT NULL REFERENCES "route_node"("id"),
  "x_m" REAL NOT NULL,
  "y_m" REAL NOT NULL,
  "yaw_deg" REAL NOT NULL
);
CREATE TABLE "signpost_arm" (
  "signpost_id" TEXT NOT NULL REFERENCES "signpost"("id") ON DELETE CASCADE,
  "ord" INTEGER NOT NULL,
  "to_node_id" TEXT NOT NULL REFERENCES "route_node"("id"),
  "bearing_deg" REAL NOT NULL,
  PRIMARY KEY ("signpost_id", "ord")
);

-- == The terrain family (2.W1; tools/argonia_world/terrain, rows by tools/argonia_world/terrain/migrate.py) ==
-- The generated ground is ArgoniaWorld.esm (decision 0031); these rows are what the generator reads or proves
-- against. The arrays themselves live in $ARGONIA_DATA/terrain/, identified here by sha256, never in git.

-- Home of a terrain input file: an array or receipt the generator reads, pinned by the sha256 of its bytes.
CREATE TABLE "terrain_input" (
  "name" TEXT NOT NULL PRIMARY KEY,
  "sha256" TEXT NOT NULL,
  "role" TEXT NOT NULL,
  "source" TEXT NOT NULL
);

-- Home of a land-cover class: the id the land-cover raster stores per sample (old 0011's micro layer).
CREATE TABLE "land_cover" (
  "id" INTEGER NOT NULL PRIMARY KEY,
  "name" TEXT NOT NULL UNIQUE,
  "bare" BOOLEAN NOT NULL
);

-- The vanilla LTEX a class paints (decision 0028): a Skyrim.esm form Tropical Skyrim replaces in place.
CREATE TABLE "land_cover_ltex" (
  "land_cover_id" INTEGER NOT NULL PRIMARY KEY REFERENCES "land_cover"("id"),
  "ltex_form_key" TEXT NOT NULL,
  "ltex_edid" TEXT NOT NULL,
  "tropical_skyrim_replaces" BOOLEAN NOT NULL,
  "why" TEXT NOT NULL
);

-- What the old chain did with a terrain patch (its receipts): applied or refused, and how much ground it moved.
CREATE TABLE "terrain_patch_outcome" (
  "terrain_patch_id" TEXT NOT NULL PRIMARY KEY REFERENCES "terrain_patch"("id"),
  "chain" TEXT NOT NULL CHECK ("chain" IN ('terrain', 'route-grade')),
  "kind" TEXT,
  "status" TEXT NOT NULL CHECK ("status" IN ('applied', 'refused')),
  "reason" TEXT,
  "samples_changed" INTEGER,
  "max_abs_delta_m" REAL,
  "receipt" TEXT NOT NULL REFERENCES "terrain_input"("name")
);

-- == The core rules' numbers (lane 1.1-core-rules; 76 §116–§127, 85 §A, goal G11.2) ==
-- Every number a skse/core rule reads, so none is typed into C++. tools/argonia_world/core_tables.py reads these
-- (and attribute, skill, skill_bands, sheet_rules, class_rules, condition_term) and writes skse/core/generated/.

-- Lookup: the skse/core module a constant belongs to (its C++ namespace in the generated header).
CREATE TABLE "core_module" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "header" TEXT NOT NULL CHECK ("header" IN ('sheet', 'progression', 'conditions'))
);

-- Home of every scalar constant of the core rules: its module, value and the design section it comes from.
CREATE TABLE "core_constant" (
  "id" TEXT NOT NULL PRIMARY KEY CHECK ("id" GLOB '[a-z]*' AND "id" NOT GLOB '*[^a-z0-9_]*'),
  "module" TEXT NOT NULL REFERENCES "core_module"("id"),
  "value" REAL NOT NULL,
  "design_ref" TEXT NOT NULL
);

-- Home of the burden tiers (76 §122, §121.2, §122.1), lightest first: the ratio a tier ends below (NULL for the last),
-- the stamina cost multiplier, the climbing drain multiplier (NULL: cannot climb) and the roll (NULL: no roll).
CREATE TABLE "core_burden_tier" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "ord" INTEGER NOT NULL UNIQUE,
  "below_ratio" REAL,
  "stamina_mult" REAL NOT NULL,
  "climb_drain_mult" REAL,
  "roll_distance" REAL,
  "roll_recovery" REAL,
  "iframe_scale" REAL,
  "can_run" BOOLEAN NOT NULL CHECK ("can_run" IN (0, 1)),
  "design_ref" TEXT NOT NULL
);

-- Home of each armour skill's class numbers (76 §121.4, §120.2): the class rating multiplier (NULL for Unarmored,
-- which rates by its own formula) and the kill and hit weights of armour accrual.
CREATE TABLE "core_armour_skill" (
  "skill" TEXT NOT NULL PRIMARY KEY REFERENCES "skill"("id"),
  "rating_mult" REAL,
  "win_weight" REAL NOT NULL,
  "hit_weight" REAL NOT NULL
);

-- Home of the skill classes of a character's class (76 §120.1, §120.4): the rank cost factor and how many ranks of
-- the class make one counted rank toward a level (1 counts in full; 3 is the 1 : 3 credit).
CREATE TABLE "core_skill_class" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "ord" INTEGER NOT NULL UNIQUE,
  "xp_factor" REAL NOT NULL,
  "ranks_per_credit" INTEGER NOT NULL CHECK ("ranks_per_credit" >= 1)
);

-- Home of every qualifying use (76 §120.1): its canon points, what one unit is, and whether worthiness scales it.
CREATE TABLE "core_use" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "points" REAL NOT NULL,
  "unit" TEXT NOT NULL CHECK ("unit" IN ('use', 'second', 'metre', 'percent')),
  "scaled" BOOLEAN NOT NULL CHECK ("scaled" IN (0, 1))
);

-- Home of a skill's own points for a use where they differ from the use's (76 §120.1: axe 1.2, short blade 0.75).
CREATE TABLE "core_use_skill_points" (
  "use" TEXT NOT NULL REFERENCES "core_use"("id"),
  "skill" TEXT NOT NULL REFERENCES "skill"("id"),
  "points" REAL NOT NULL,
  PRIMARY KEY ("use", "skill")
);

-- Home of the ranks-per-level curve (76 §120.5, old 0147): entry `level` takes that level to the next; every level
-- past the last row asks the last row's ranks.
CREATE TABLE "core_ranks_per_level" (
  "level" INTEGER NOT NULL PRIMARY KEY CHECK ("level" >= 1),
  "ranks" INTEGER NOT NULL CHECK ("ranks" >= 1)
);

-- Home of the rest tiers (76 §126, decision 0144): camp < rented bed < owned bed, the skill experience multiplier of
-- the rested entry and its game hours (0: no entry).
CREATE TABLE "core_bed_tier" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "ord" INTEGER NOT NULL UNIQUE,
  "xp_mult" REAL NOT NULL,
  "hours" REAL NOT NULL
);

-- Home of the disposition bands (76 §125, 1.3 §b): each band starts at `min` and runs to the next band's.
CREATE TABLE "core_disposition_band" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "ord" INTEGER NOT NULL UNIQUE,
  "min" INTEGER NOT NULL
);

-- Home of the respawn classes (76 §126, decision 0031): whether a rest resets the actor, and whether a cleared place
-- stops it.
CREATE TABLE "core_respawn_class" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "on_rest" BOOLEAN NOT NULL CHECK ("on_rest" IN (0, 1)),
  "until_cleared" BOOLEAN NOT NULL CHECK ("until_cleared" IN (0, 1))
);

-- Home of the ways an item wears (item_condition.wear's values; 76 §121.6): what one unit of wear is measured in.
CREATE TABLE "core_wear_kind" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "per" TEXT NOT NULL CHECK ("per" IN ('damage', 'use', 'second'))
);

-- Home of the effect stack's operations (76 §127).
CREATE TABLE "core_effect_op" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "ord" INTEGER NOT NULL UNIQUE
);

-- Home of the effect stack's fields beyond the attributes and skills (76 §127, §121.3, §121.6, §123), and how
-- entries on each combine: pool (added), resist (added, capped at the resist cap), factor (multiplied),
-- per_int (added to the magicka-per-Intelligence coefficient), flag (on when any entry is).
CREATE TABLE "core_stat_field" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "kind" TEXT NOT NULL CHECK ("kind" IN ('pool', 'resist', 'factor', 'per_int', 'flag'))
);

-- Home of each predicate's and combinator's evaluation shape (85 §A, §D): how skse/core/conditions evaluates it
-- over the Facts ArgoniaCore supplies, and the Skyrim condition function that carries it natively (P2 of the
-- native map; NULL: evaluated in the core and mirrored into a global).
CREATE TABLE "condition_shape" (
  "term" TEXT NOT NULL PRIMARY KEY REFERENCES "condition_term"("id"),
  "shape" TEXT NOT NULL CHECK ("shape" IN ('all', 'any', 'not', 'truth', 'flag', 'at_least', 'compare', 'is',
                                           'rank_at_least', 'after', 'before', 'calendar', 'time_of_day')),
  "native" TEXT
);

-- Home of a predicate's arguments in order (85 §A): the kind of each and whether it may be left out.
CREATE TABLE "condition_shape_arg" (
  "term" TEXT NOT NULL REFERENCES "condition_shape"("term"),
  "ord" INTEGER NOT NULL,
  "kind" TEXT NOT NULL CHECK ("kind" IN ('id', 'int', 'op', 'enum', 'bool')),
  "optional" BOOLEAN NOT NULL CHECK ("optional" IN (0, 1)),
  PRIMARY KEY ("term", "ord")
);

-- Home of the closed value set of a predicate's enum argument where 85 lists one, in its order (the order is the
-- rank for rank_at_least).
CREATE TABLE "condition_shape_value" (
  "term" TEXT NOT NULL REFERENCES "condition_shape"("term"),
  "value" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  PRIMARY KEY ("term", "value"),
  UNIQUE ("term", "ord")
);

-- Home of the comparison operators an `op` argument takes (85 §A1: questStage), with a C++ name for each.
CREATE TABLE "condition_op" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "name" TEXT NOT NULL UNIQUE,
  "ord" INTEGER NOT NULL UNIQUE
);

-- == The ground's grass (2.W1; tools/argonia_world/terrain/grass.py; decision 0006: no Nordic grass in the marsh) ==
-- Home of a plugin a painted LTEX's grass may come from: the form must be defined or overridden there.
CREATE TABLE "grass_source" (
  "plugin" TEXT NOT NULL PRIMARY KEY,
  "why" TEXT NOT NULL
);

-- Home of a painted LTEX's grass plan: every LTEX `land_cover_ltex` paints has one; no `ltex_grass` rows = bare.
CREATE TABLE "ltex_grass_plan" (
  "ltex_form_key" TEXT NOT NULL PRIMARY KEY,
  "ltex_edid" TEXT NOT NULL,
  "why" TEXT NOT NULL
);

-- The grass a painted LTEX grows, in list order (Argonia.esm overrides the LTEX where the winning list differs).
CREATE TABLE "ltex_grass" (
  "ltex_form_key" TEXT NOT NULL REFERENCES "ltex_grass_plan"("ltex_form_key"),
  "ord" INTEGER NOT NULL,
  "grass_form_key" TEXT NOT NULL,
  PRIMARY KEY ("ltex_form_key", "ord")
);
