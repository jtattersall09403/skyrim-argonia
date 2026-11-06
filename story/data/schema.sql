


-- Lookup: the allowed values of value band.
CREATE TABLE "value_band" (
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

-- Lookup: the allowed values of item kind.
CREATE TABLE "item_kind" (
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
  -- A person's own starting regard for a stranger, 0-100 (76 §125; Morrowind's neutral is 50). Persons carry one
  -- (check person-disposition); creatures none. ArgoniaCore adds the player's Personality and the priors to it.
  "base_disposition" INTEGER CHECK ("base_disposition" BETWEEN 0 AND 100),
  PRIMARY KEY ("id")
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

-- Home of one row per element of `services` of each npc row (ordered by `ord` where it has one).
CREATE TABLE "npc_service" (
  "npc_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "value" TEXT NOT NULL,
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
  "pocket" TEXT NOT NULL,
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
  "lock" TEXT,
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

-- Home of every creature kind: region classes (creature_region_class), bands, habitat, stat block, senses, reaction.
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

-- == quest_line ==

-- Home of every questline: its code prefix, name, group, faction, tier, home region and target count.
CREATE TABLE "quest_line" (
  "id" TEXT NOT NULL,
  "code" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "group" TEXT NOT NULL REFERENCES "quest_group"("id"),
  "faction" TEXT REFERENCES "faction"("id"),
  "tier" INTEGER NOT NULL,
  "home_region" TEXT,
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
  "region" TEXT NOT NULL,
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
-- `text` is the objective's text key; `objective_text` its words (the record's `objectiveText`).
CREATE TABLE "quest_objective" (
  "quest_id" TEXT NOT NULL,
  "stages_ord" INTEGER NOT NULL,
  "ord" INTEGER NOT NULL,
  "id" TEXT NOT NULL,
  "text" TEXT NOT NULL,
  "complete_when" TEXT NOT NULL REFERENCES "condition"("id"),
  "where_ref" TEXT,
  "objective_text" TEXT,
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

-- One native hook on a quest thing (1.4): activating the thing's activator, or reading its book, sets one flag of
-- the quest. ArgoniaCore's thing table (skse/core generated things.h, tools/argonia_world/thing_hooks.py) is keyed by
-- the world id of the record the thing is placed as (its build_ref base). Not part of the quest record: a quest
-- rewrite keeps these rows, and thing_hooks' check refuses one whose thing or flag the quest no longer has.
CREATE TABLE "thing_hook" (
  "quest_id" TEXT NOT NULL REFERENCES "quest"("id"),
  "thing_id" TEXT NOT NULL,
  "hook" TEXT NOT NULL CHECK ("hook" IN ('activate', 'read')),
  "sets_flag" TEXT NOT NULL,
  PRIMARY KEY ("quest_id", "thing_id")
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
-- `kind`: a `concept` clue says what happened, a `lead` where to go next (quest-write principles/general.md §6).
CREATE TABLE "quest_clue" (
  "quest_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "id" TEXT NOT NULL,
  "form" TEXT NOT NULL,
  "carrier" TEXT NOT NULL,
  "kind" TEXT CHECK ("kind" IN ('concept', 'lead')),
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

-- Home of one row per element of `people` of each place_build row (ordered by `ord` where it has one).
CREATE TABLE "place_person" (
  "place_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  "id" TEXT NOT NULL REFERENCES "npc"("id"),
  "name" TEXT NOT NULL,
  "role" TEXT NOT NULL,
  "post" TEXT NOT NULL,
  "hostility" TEXT NOT NULL REFERENCES "hostility_stance"("id"),
  PRIMARY KEY ("place_id", "ord")
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
-- delivered. The imported lines are reference only (0024 §7): `status` says so (`imported` reference, `written` ours).
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
  "status" TEXT NOT NULL CHECK ("status" IN ('imported', 'written')),
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
  "region_id" TEXT,
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

-- == attribute ==

-- Home of the seven attributes (no Luck; 76 §117) and each one's reference value.
CREATE TABLE "attribute" (
  "id" TEXT NOT NULL,
  "reference" INTEGER NOT NULL,
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

-- Home of a form of a dependency mod (a player's own download, data/dependencies.json) that Argonia restates at data
-- load without editing or mastering its plugin (1.12; decisions 0003, 0012): a reviewed name or description in our
-- words where the mod's own carries a Skyrim tell, and for a magic effect the Morrowind school it belongs to. The id
-- is the immersion inventory's row id ("<local FormID, 6 hex>:<plugin>"). ArgoniaCore applies the rows at data load
-- (skse/core magic, from tables_magic.h); a school whose skill has no Skyrim actor value (Mysticism) is recorded but
-- the effect stays under the school its mod gave it (docs/research/2026-10-31/lane-1.12-magic.md).
CREATE TABLE "mod_form" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "dependency" TEXT NOT NULL,
  "form_type" TEXT NOT NULL CHECK ("form_type" IN ('SPEL', 'MGEF', 'BOOK', 'SCRL', 'WEAP', 'ARMO', 'MESG')),
  "name" TEXT,
  "description" TEXT,
  "school" TEXT REFERENCES "skill"("id"),
  "why" TEXT NOT NULL,
  CHECK ("school" IS NULL OR "form_type" = 'MGEF'),
  CHECK ("description" IS NULL OR "form_type" IN ('MGEF', 'MESG')),
  CHECK ("name" IS NOT NULL OR "description" IS NOT NULL OR "school" IS NOT NULL)
);

-- Home of a merchant's trade class and its stock. Migrated by 2.10 from world/sources/economy/trade-classes.json; until then a key only.
CREATE TABLE "trade_class" (
  "id" TEXT NOT NULL PRIMARY KEY
);

-- Home of a trade class's stock (2.10 migrates the rest of trade-classes.json): what a trader of the class keeps in
-- their merchant chest, as item rows (our record, or the reviewed base record the item names, decision 0012).
CREATE TABLE "trade_class_stock" (
  "trade_class_id" TEXT NOT NULL REFERENCES "trade_class"("id") ON DELETE CASCADE,
  "ord" INTEGER NOT NULL,
  "item_id" TEXT NOT NULL REFERENCES "item"("id"),
  "count" INTEGER NOT NULL CHECK ("count" > 0),
  PRIMARY KEY ("trade_class_id", "ord")
);

-- Home of a trade class's stock from a dependency mod (1.12, lane-1.12-magicpane): a form of the player's own copy of
-- the mod (data/dependencies.json), named as the immersion inventory names it ("<local FormID, 6 hex>:<plugin>",
-- reviewed there, decision 0012), added to each trader's merchant chest of the class at data load by ArgoniaCore
-- (skse/core magic, from tables_magic.h), so our plugin never masters the mod's (0003). A form whose plugin is not
-- loaded is skipped. The engine prices it.
CREATE TABLE "trade_class_mod_stock" (
  "trade_class_id" TEXT NOT NULL REFERENCES "trade_class"("id") ON DELETE CASCADE,
  "ord" INTEGER NOT NULL,
  "form" TEXT NOT NULL CHECK ("form" GLOB '[0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F]:?*'),
  "dependency" TEXT NOT NULL,
  "count" INTEGER NOT NULL CHECK ("count" > 0),
  "why" TEXT NOT NULL,
  PRIMARY KEY ("trade_class_id", "ord")
);

-- Home of a person's barter terms (Morrowind's barter gold; Skyrim's vendor faction): the gold in their merchant
-- chest and the hours they trade (HH:MM, game time). Their stock is their trade class's (npc.trade_class).
CREATE TABLE "npc_trade" (
  "npc_id" TEXT NOT NULL PRIMARY KEY REFERENCES "npc"("id") ON DELETE CASCADE,
  "barter_gold" INTEGER NOT NULL CHECK ("barter_gold" >= 0),
  "opens" TEXT NOT NULL,
  "closes" TEXT NOT NULL
);

-- Home of a culture's kit of pieces. Migrated by the place builds from world/sources/placement/culture-kits.json; until then a key only.
CREATE TABLE "culture_kit" (
  "id" TEXT NOT NULL PRIMARY KEY
);

-- The seasons an enum argument of a condition term takes (85 §A6 calendarIs), in rank order; the season table is
-- their home, so a season named in a condition is always one the weather rule knows.
CREATE TABLE "condition_shape_season" (
  "term" TEXT NOT NULL REFERENCES "condition_shape"("term"),
  "season_id" TEXT NOT NULL,
  "ord" INTEGER NOT NULL,
  PRIMARY KEY ("term", "season_id"),
  UNIQUE ("term", "ord")
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

-- Home of the master record an item effect id names (alchemy's ENIT effects link to a magic effect record).
CREATE TABLE "effect_skyrim_mgef" (
  "effect_id" TEXT NOT NULL PRIMARY KEY,
  "plugin" TEXT NOT NULL,
  "form_id" INTEGER NOT NULL,
  "editor_id" TEXT NOT NULL
);

-- == The action vocabulary's shapes (lane 1.3-rules; 85 §B as data, read by skse/core `actions`) ==

-- Home of an action verb's arguments in order (85 §B): the kind of each and whether it may be left out
-- (a left-out count is one; a left-out flag is true).
CREATE TABLE "action_shape_arg" (
  "term" TEXT NOT NULL REFERENCES "condition_term"("id"),
  "ord" INTEGER NOT NULL,
  "kind" TEXT NOT NULL CHECK ("kind" IN ('id', 'int', 'bool')),
  "optional" BOOLEAN NOT NULL CHECK ("optional" IN (0, 1)),
  PRIMARY KEY ("term", "ord")
);

-- How a placed creature hunts (game-10 §4, the planner's call): `walk` (b) overrides its race in Argonia.esm to walk
-- (the race's Walks flag; its walk and run movement types are kept) so it fights on the bank at its den; `shallows`
-- (a) leaves the race as it is and stands the creature at `den_ref_id` in the water's edge, where it attacks a player
-- wading in. Either way the creature's NPC_ carries our own combat style (`combat_style`, place_build.COMBAT_STYLES).
-- The switch from (b) to (a) is this one row: `way` and `den_ref_id`.
CREATE TABLE "creature_hunt" (
  "npc_id" TEXT NOT NULL PRIMARY KEY,
  "way" TEXT NOT NULL CHECK ("way" IN ('walk', 'shallows')),
  "den_ref_id" TEXT NOT NULL,
  "combat_style" TEXT NOT NULL CHECK ("combat_style" IN ('melee-ambush')),
  "why" TEXT NOT NULL
);

-- == Perk text (1.12 §4; decision 0012: no vanilla perk text reaches the player) ==

-- Home of our wording for a vanilla perk that can reach the player (a record of a skill's tree in Skyrim.esm or a
-- DLC, with its rank chain): same meaning and every number unchanged, nothing Nordic. `formkey` is the master's
-- FormKey (`0BEE97:Skyrim.esm`); Argonia.esm overrides that PERK with this name and description (the record
-- otherwise a copy of the master's). `tree` is the skill's actor value editor ID, for grouping only.
CREATE TABLE "perk_text" (
  "formkey" TEXT NOT NULL PRIMARY KEY CHECK ("formkey" GLOB '[0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F]:*.es[mp]'),
  "tree" TEXT NOT NULL CHECK ("tree" GLOB 'AV*'),
  "name" TEXT NOT NULL CHECK (length("name") > 0),
  "description" TEXT NOT NULL CHECK (length("description") > 0)
);

-- == Creature encounters (1.15 §g; decision 0034: Skyrim.esm's own method, measured in
-- tools/argonia_world/vanilla/creatures.py and docs/research/2026-11-01/lane-1.15-creatures.md) ==

-- Home of a dependency mod's creature form (NPC_) that stands for one of our creature kinds: the mod's own record,
-- race and behaviour (route 1 data), joined to its `creature` row. form_key is "<local FormID 6 hex>:<plugin>".
-- Written by `python -m tools.argonia_world.creatures seed` from creatures/roster.py's FORMS. pc_level_mult: the
-- mod's stats scale with the player; death_item_levelled: its death item reaches a levelled entry above 1. Either
-- way our plugin carries its own fixed-level copy (decision 0035, creatures/levelled.py).
CREATE TABLE "creature_form" (
  "form_key" TEXT NOT NULL PRIMARY KEY,
  "creature_id" TEXT NOT NULL REFERENCES "creature"("id"),
  "mod" TEXT NOT NULL,
  "edid" TEXT NOT NULL,
  "race" TEXT NOT NULL,
  "aggression" INTEGER NOT NULL CHECK ("aggression" BETWEEN 0 AND 3),
  "pc_level_mult" BOOLEAN NOT NULL CHECK ("pc_level_mult" IN (0, 1)),
  "death_item_levelled" BOOLEAN NOT NULL CHECK ("death_item_levelled" IN (0, 1)),
  "why" TEXT NOT NULL
);

-- Home of a disease or poison a creature's bite, sting or touch carries (fauna-hazards.md "Diseases").
CREATE TABLE "creature_affliction" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "kind" TEXT NOT NULL CHECK ("kind" IN ('disease', 'poison')),
  "name" TEXT NOT NULL,
  "effect" TEXT NOT NULL,
  "source" TEXT NOT NULL
);

-- Home of one of our levelled actor lists (LVLN): one per region class, band and medium, every entry at the band's
-- level (fixed; chance none 0, as every one of Skyrim.esm's 72 creature lists). Derived by `creatures seed`.
CREATE TABLE "creature_list" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "region_class" TEXT NOT NULL,
  "band" TEXT NOT NULL,
  "medium" TEXT NOT NULL CHECK ("medium" IN ('water', 'shore', 'land')),
  "level" INTEGER NOT NULL,
  "chance_none" INTEGER NOT NULL CHECK ("chance_none" BETWEEN 0 AND 100)
);

-- Home of one entry of a creature list: a mod form at the list's level.
CREATE TABLE "creature_list_entry" (
  "list_id" TEXT NOT NULL REFERENCES "creature_list"("id"),
  "form_key" TEXT NOT NULL REFERENCES "creature_form"("form_key"),
  "level" INTEGER NOT NULL,
  "count" INTEGER NOT NULL CHECK ("count" >= 1),
  PRIMARY KEY ("list_id", "form_key")
);

-- ---------------------------------------------------------------------------------------------------------------------
-- The BM&V census (phase 1): our data about BM&V's four plugins in load order (BosmerArmorMATY743.esm, Black Marsh.esm,
-- Black Marsh North.esp, Valenwood.esp), read from the files by `tools/argonia_world/bmv_census.py` (never copied from
-- them: keys, editor ids, names, coordinates, counts and links only). Every id is a form key "XXXXXX:Plugin" of the
-- defining master, as mod_form writes them; `defined_in` is that master. A record's values are the load order's
-- winner (a later plugin's version wins; a winner flagged deleted removes it). `plugin` is the first BM&V file that
-- carries the record (its defining file for BM&V's own forms; null for a master form no BM&V file carries) and
-- `overridden_by` the later BM&V files that override it, space-separated (null: none). Designed rows are linked to it
-- by place_bmv, npc_bmv and faction_bmv, never copied.
-- ---------------------------------------------------------------------------------------------------------------------

-- Home of a worldspace BM&V adds or edits (WRLD); `parent` its parent worldspace (WNAM); `land_cells` its exterior
-- cells with LAND in the load order.
CREATE TABLE "bmv_worldspace" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "plugin" TEXT,
  "overridden_by" TEXT,
  "editor_id" TEXT NOT NULL,
  "name" TEXT,
  "defined_in" TEXT NOT NULL,
  "parent" TEXT,
  "land_cells" INTEGER NOT NULL CHECK ("land_cells" >= 0)
);

-- Home of a location (LCTN) BM&V defines, overrides, or names on one of its cells.
CREATE TABLE "bmv_location" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "plugin" TEXT,
  "overridden_by" TEXT,
  "editor_id" TEXT,
  "name" TEXT,
  "parent" TEXT,
  "defined_in" TEXT NOT NULL,
  "in_bmv" BOOLEAN NOT NULL CHECK ("in_bmv" IN (0, 1))
);

-- Home of a cell (CELL) in BM&V's plugins: an interior, or an exterior of a worldspace at a grid square; the
-- persistent cell of a worldspace (flag 0x400, directly under its WRLD) has no grid. `refs` counts the placed references (REFR, ACHR, PGRE) the load order's winners put in it.
CREATE TABLE "bmv_cell" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "plugin" TEXT,
  "overridden_by" TEXT,
  "editor_id" TEXT,
  "name" TEXT,
  "interior" BOOLEAN NOT NULL CHECK ("interior" IN (0, 1)),
  "worldspace" TEXT REFERENCES "bmv_worldspace"("id"),
  "grid_x" INTEGER,
  "grid_y" INTEGER,
  "persistent" BOOLEAN NOT NULL CHECK ("persistent" IN (0, 1)),
  "location" TEXT REFERENCES "bmv_location"("id"),
  "has_navmesh" BOOLEAN NOT NULL CHECK ("has_navmesh" IN (0, 1)),
  "refs" INTEGER NOT NULL CHECK ("refs" >= 0),
  "defined_in" TEXT NOT NULL,
  CHECK (("interior" = 1) = ("worldspace" IS NULL)),
  CHECK (("grid_x" IS NULL) = ("grid_y" IS NULL)),
  CHECK ("interior" = 0 OR "grid_x" IS NULL),
  CHECK ("persistent" = 0 OR "grid_x" IS NULL)
);

-- Home of a race a BM&V actor uses (RACE).
CREATE TABLE "bmv_race" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "plugin" TEXT,
  "overridden_by" TEXT,
  "editor_id" TEXT,
  "name" TEXT,
  "defined_in" TEXT NOT NULL
);

-- Home of a class a BM&V actor uses (CLAS).
CREATE TABLE "bmv_class" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "plugin" TEXT,
  "overridden_by" TEXT,
  "editor_id" TEXT,
  "name" TEXT,
  "defined_in" TEXT NOT NULL
);

-- Home of a faction (FACT) BM&V defines or overrides, or that one of its actors belongs to.
CREATE TABLE "bmv_faction" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "plugin" TEXT,
  "overridden_by" TEXT,
  "editor_id" TEXT,
  "name" TEXT,
  "defined_in" TEXT NOT NULL,
  "in_bmv" BOOLEAN NOT NULL CHECK ("in_bmv" IN (0, 1))
);

-- Home of an actor base BM&V defines or places: an NPC_ record, or a levelled actor list (LVLN) one of its
-- references places. Race, class and sex are the NPC_'s own: a templated actor's (template_flags, ACBS, non-zero) may
-- come from its template. `person` is whether its own race carries ActorTypeNPC (false: a creature).
CREATE TABLE "bmv_npc" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "plugin" TEXT,
  "overridden_by" TEXT,
  "record" TEXT NOT NULL CHECK ("record" IN ('NPC_', 'LVLN')),
  "editor_id" TEXT,
  "name" TEXT,
  "race" TEXT REFERENCES "bmv_race"("id"),
  "class" TEXT REFERENCES "bmv_class"("id"),
  "sex" TEXT CHECK ("sex" IN ('male', 'female')),
  "template" TEXT,
  "template_flags" INTEGER,
  "person" BOOLEAN,
  "defined_in" TEXT NOT NULL,
  "in_bmv" BOOLEAN NOT NULL CHECK ("in_bmv" IN (0, 1)),
  CHECK ("record" = 'NPC_' OR ("race" IS NULL AND "sex" IS NULL))
);

-- Home of one faction membership of a BM&V NPC_ (SNAM).
CREATE TABLE "bmv_npc_faction" (
  "npc" TEXT NOT NULL REFERENCES "bmv_npc"("id"),
  "faction" TEXT NOT NULL REFERENCES "bmv_faction"("id"),
  "rank" INTEGER NOT NULL,
  PRIMARY KEY ("npc", "faction")
);

-- Home of a placed actor (ACHR) in BM&V's plugins: its base, its cell, its position; grid is the exterior square
-- the position falls in (for a reference in a worldspace's persistent cell too), null in an interior.
CREATE TABLE "bmv_placement" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "plugin" TEXT,
  "overridden_by" TEXT,
  "npc" TEXT NOT NULL REFERENCES "bmv_npc"("id"),
  "cell" TEXT NOT NULL REFERENCES "bmv_cell"("id"),
  "x" REAL NOT NULL,
  "y" REAL NOT NULL,
  "z" REAL NOT NULL,
  "grid_x" INTEGER,
  "grid_y" INTEGER,
  "disabled" BOOLEAN NOT NULL CHECK ("disabled" IN (0, 1)),
  "enable_parent" TEXT
);

-- Home of a quest (QUST) BM&V defines or overrides.
CREATE TABLE "bmv_quest" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "plugin" TEXT,
  "overridden_by" TEXT,
  "editor_id" TEXT,
  "name" TEXT,
  "start_game_enabled" BOOLEAN NOT NULL CHECK ("start_game_enabled" IN (0, 1)),
  "priority" INTEGER NOT NULL,
  "defined_in" TEXT NOT NULL
);

-- Home of a load door (a REFR with XTEL) in BM&V's plugins (`base` its DOOR: a book-shaped base is a book portal): where it stands and the door it leads to. An exterior
-- door sits in its worldspace's persistent cell; `ext_cell` is the exterior square it stands on.
-- `target` is the paired door when BM&V holds it; `target_elsewhere` the paired door's key when only a master holds it.
CREATE TABLE "bmv_door" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "plugin" TEXT,
  "overridden_by" TEXT,
  "cell" TEXT NOT NULL REFERENCES "bmv_cell"("id"),
  "x" REAL NOT NULL,
  "y" REAL NOT NULL,
  "z" REAL NOT NULL,
  "grid_x" INTEGER,
  "grid_y" INTEGER,
  "worldspace" TEXT REFERENCES "bmv_worldspace"("id"),
  "ext_cell" TEXT REFERENCES "bmv_cell"("id"),
  "target" TEXT REFERENCES "bmv_door"("id"),
  "target_elsewhere" TEXT,
  "base" TEXT NOT NULL,
  "base_editor_id" TEXT,
  "base_name" TEXT,
  CHECK (("target" IS NULL) <> ("target_elsewhere" IS NULL))
);

-- Home of a settlement or site the census groups BM&V's cells into (BM&V has no LCTN of its own): a named exterior
-- cell cluster ('settlement'), or interiors reached by load doors from one exterior spot ('site'). Derived, with why;
-- `marker_name` is the world-map name of the BM&V map marker that stands in its cells, if any.
CREATE TABLE "bmv_settlement" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "name" TEXT NOT NULL,
  "kind" TEXT NOT NULL CHECK ("kind" IN ('settlement', 'site')),
  "worldspace" TEXT REFERENCES "bmv_worldspace"("id"),
  "grid_x" INTEGER,
  "grid_y" INTEGER,
  "why" TEXT NOT NULL,
  "marker_name" TEXT
);

-- Home of a map marker BM&V places (a REFR with XMRK): its worldspace, square, position and the name the world map shows.
CREATE TABLE "bmv_map_marker" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "plugin" TEXT,
  "overridden_by" TEXT,
  "name" TEXT,
  "worldspace" TEXT NOT NULL REFERENCES "bmv_worldspace"("id"),
  "x" REAL NOT NULL,
  "y" REAL NOT NULL,
  "grid_x" INTEGER NOT NULL,
  "grid_y" INTEGER NOT NULL,
  "settlement" TEXT REFERENCES "bmv_settlement"("id")
);

-- Home of a book (BOOK) a BM&V file defines or overrides, with how often and where the load order places it.
CREATE TABLE "bmv_book" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "plugin" TEXT,
  "overridden_by" TEXT,
  "editor_id" TEXT,
  "name" TEXT,
  "placed" INTEGER NOT NULL CHECK ("placed" >= 0),
  "first_cell" TEXT REFERENCES "bmv_cell"("id")
);

-- Home of a cell's membership of a settlement: an anchor (a named exterior cell), a neighbour square (within one), an
-- area square (a square with content, nearest this settlement's anchors within eight), or an interior reached through
-- load doors (its main settlement; every exit is in bmv_interior_exit).
CREATE TABLE "bmv_settlement_cell" (
  "settlement" TEXT NOT NULL REFERENCES "bmv_settlement"("id"),
  "cell" TEXT NOT NULL UNIQUE REFERENCES "bmv_cell"("id"),
  "role" TEXT NOT NULL CHECK ("role" IN ('anchor', 'neighbour', 'area', 'interior')),
  PRIMARY KEY ("settlement", "cell")
);

-- Home of one way out of an interior: an exterior load door its door graph reaches, and the settlement there if any.
-- A ship has one per port, a shared house interior one per house door; an interior with none has no load door in,
-- or is a vanilla interior BM&V edits (Skyrim's, left out of the settlements).
CREATE TABLE "bmv_interior_exit" (
  "interior" TEXT NOT NULL REFERENCES "bmv_cell"("id"),
  "door" TEXT NOT NULL REFERENCES "bmv_door"("id"),
  "settlement" TEXT REFERENCES "bmv_settlement"("id"),
  PRIMARY KEY ("interior", "door")
);

-- Home of a designed place's landing in BM&V: a settlement or a cell, or waiting when BM&V has nothing for it.
CREATE TABLE "place_bmv" (
  "place" TEXT NOT NULL PRIMARY KEY REFERENCES "place"("id"),
  "settlement" TEXT REFERENCES "bmv_settlement"("id"),
  "cell" TEXT REFERENCES "bmv_cell"("id"),
  "status" TEXT NOT NULL CHECK ("status" IN ('mapped', 'waiting')),
  "confidence" TEXT CHECK ("confidence" IN ('high', 'medium', 'low')),
  "reason" TEXT NOT NULL,
  "source" TEXT NOT NULL,
  CHECK (("status" = 'waiting') = ("settlement" IS NULL AND "cell" IS NULL)),
  CHECK (("status" = 'waiting') = ("confidence" IS NULL))
);

-- Home of a designed person who clearly is a BM&V actor.
CREATE TABLE "npc_bmv" (
  "npc" TEXT NOT NULL PRIMARY KEY REFERENCES "npc"("id"),
  "bmv_npc" TEXT NOT NULL REFERENCES "bmv_npc"("id"),
  "confidence" TEXT NOT NULL CHECK ("confidence" IN ('high', 'medium', 'low')),
  "reason" TEXT NOT NULL,
  "source" TEXT NOT NULL
);

-- Home of a designed faction's landing on a BM&V faction.
CREATE TABLE "faction_bmv" (
  "faction" TEXT NOT NULL PRIMARY KEY REFERENCES "faction"("id"),
  "bmv_faction" TEXT NOT NULL REFERENCES "bmv_faction"("id"),
  "confidence" TEXT NOT NULL CHECK ("confidence" IN ('high', 'medium', 'low')),
  "reason" TEXT NOT NULL,
  "source" TEXT NOT NULL
);

-- ---------------------------------------------------------------------------------------------------------------------
-- The adaptation ledger (phase 2, "the whole quest system on BM&V"): every line's spirit and hubs, every quest's
-- verdict, premise and hosts in BM&V's world, and one ledger of world edits linked to the quests that need them.
-- Checked as a whole by `tools/argonia_world/adaptation_check.py` (make check). The plan: story/design/quests/adaptation.md.
-- ---------------------------------------------------------------------------------------------------------------------

-- Home of a line's spirit: the promise, the core and the identity any adaptation keeps, and what is free.
CREATE TABLE "line_spirit" (
  "line" TEXT NOT NULL PRIMARY KEY REFERENCES "quest_line"("id"),
  "promise" TEXT NOT NULL,
  "core" TEXT NOT NULL,
  "identity" TEXT,
  "free" TEXT NOT NULL,
  "source" TEXT NOT NULL
);

-- Home of one signature beat of a line (ordered), which must survive the adaptation.
CREATE TABLE "line_spirit_beat" (
  "line" TEXT NOT NULL REFERENCES "line_spirit"("line") ON DELETE CASCADE,
  "ord" INTEGER NOT NULL,
  "beat" TEXT NOT NULL,
  PRIMARY KEY ("line", "ord")
);

-- Home of a line's seat and hubs in BM&V: a settlement, or an interior cell, with its role.
CREATE TABLE "line_hub" (
  "line" TEXT NOT NULL REFERENCES "quest_line"("id"),
  "ord" INTEGER NOT NULL,
  "settlement" TEXT NOT NULL REFERENCES "bmv_settlement"("id"),
  "cell" TEXT REFERENCES "bmv_cell"("id"),
  "role" TEXT NOT NULL CHECK ("role" IN ('seat', 'hub', 'field')),
  "why" TEXT NOT NULL,
  PRIMARY KEY ("line", "ord")
);

-- Home of the senior exclusions between lines (40-factions): no two exclusive lines share a seat or a prerequisite.
CREATE TABLE "line_exclusion" (
  "line" TEXT NOT NULL REFERENCES "quest_line"("id"),
  "other" TEXT NOT NULL REFERENCES "quest_line"("id"),
  "what" TEXT NOT NULL,
  PRIMARY KEY ("line", "other"),
  CHECK ("line" < "other")
);

-- Home of a quest's verdict and adapted premise. `band` is its peak danger (0-5, fixed by place: decision 0035).
CREATE TABLE "quest_adaptation" (
  "quest" TEXT NOT NULL PRIMARY KEY REFERENCES "quest"("id"),
  "verdict" TEXT NOT NULL CHECK ("verdict" IN ('keep', 'adapt', 'merge', 'drop')),
  "merged_into" TEXT REFERENCES "quest"("id"),
  "spirit" TEXT NOT NULL,
  "premise" TEXT,
  "changed" TEXT,
  "why" TEXT NOT NULL,
  "band" INTEGER CHECK ("band" BETWEEN 0 AND 5),
  "lore" TEXT,
  CHECK (("verdict" = 'merge') = ("merged_into" IS NOT NULL)),
  CHECK ("verdict" IN ('merge', 'drop') OR ("premise" IS NOT NULL AND "band" IS NOT NULL AND "lore" IS NOT NULL))
);

-- Home of the BM&V places a kept quest is played in: a settlement, or one of its interiors, with the place's role.
CREATE TABLE "quest_host" (
  "quest" TEXT NOT NULL REFERENCES "quest_adaptation"("quest") ON DELETE CASCADE,
  "ord" INTEGER NOT NULL,
  "settlement" TEXT NOT NULL REFERENCES "bmv_settlement"("id"),
  "cell" TEXT REFERENCES "bmv_cell"("id"),
  "role" TEXT NOT NULL CHECK ("role" IN ('start', 'main', 'stage', 'end')),
  "what" TEXT NOT NULL,
  PRIMARY KEY ("quest", "ord")
);

-- Home of a quest's prerequisite beyond its line's order: it starts only after `needs` (another quest) ends.
CREATE TABLE "quest_prereq" (
  "quest" TEXT NOT NULL REFERENCES "quest_adaptation"("quest") ON DELETE CASCADE,
  "needs" TEXT NOT NULL REFERENCES "quest_adaptation"("quest"),
  "why" TEXT NOT NULL,
  PRIMARY KEY ("quest", "needs"),
  CHECK ("quest" <> "needs")
);

-- Home of one minor world edit, ledgered once. `target` is the BM&V form key it changes (null for a new thing);
-- `band` the fixed danger of an actor it adds (decision 0035: never levelled).
CREATE TABLE "world_edit" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "kind" TEXT NOT NULL CHECK ("kind" IN ('npc_add', 'npc_move', 'npc_remove', 'npc_change', 'creature_add',
    'creature_remove', 'ref_place', 'ref_disable', 'door_add', 'interior_copy', 'record_change', 'name_place')),
  "settlement" TEXT REFERENCES "bmv_settlement"("id"),
  "cell" TEXT REFERENCES "bmv_cell"("id"),
  "target" TEXT,
  "description" TEXT NOT NULL,
  "race" TEXT,
  "band" INTEGER CHECK ("band" BETWEEN 0 AND 5),
  "lore" TEXT NOT NULL,
  CHECK ("kind" NOT IN ('npc_add', 'creature_add') OR "band" IS NOT NULL),
  CHECK ("kind" NOT IN ('npc_move', 'npc_remove', 'npc_change', 'creature_remove', 'ref_disable', 'record_change')
    OR "target" IS NOT NULL)
);

-- Home of a quest's need of a world edit, or of a BM&V thing as it stands (`target`, a form key, no edit).
CREATE TABLE "quest_world_edit" (
  "quest" TEXT NOT NULL REFERENCES "quest_adaptation"("quest") ON DELETE CASCADE,
  "edit" TEXT NOT NULL REFERENCES "world_edit"("id"),
  PRIMARY KEY ("quest", "edit")
);

CREATE TABLE "quest_bmv_need" (
  "quest" TEXT NOT NULL REFERENCES "quest_adaptation"("quest") ON DELETE CASCADE,
  "target" TEXT NOT NULL,
  "what" TEXT NOT NULL,
  PRIMARY KEY ("quest", "target")
);
