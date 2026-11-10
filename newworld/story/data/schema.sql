-- The new world's database: Project Tamriel's Black Marsh, read from its map and researched (nw-01).
-- Loaded by tools/argonia_world/db.py with this folder's parent as the root:  db.open("newworld").
-- One row per line in db/<table>.jsonl, columns in this order, rows sorted by primary key. Third normal form:
-- every fact is stored once, in the table its key names; anything derivable (a cell's region from its own
-- row, a place's metres from its pixels) is either stored as measured input or recomputed, never both by hand.
-- Coordinates: px/py are pixels on the source map (x right, y down); world_x/world_y are game units (x east,
-- y north), 8192 a Morrowind cell, 70 a metre (tools/newworld/frame.py).

-- ---------------------------------------------------------------------------------------------------------
-- Lookups
-- ---------------------------------------------------------------------------------------------------------

-- How sure a statement is (story/lore/README.md): CANON_EXPLICIT, CANON_DERIVED, EXTRAPOLATED, AGENT_INVENTED.
CREATE TABLE "statement_tier" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT NOT NULL
);

-- Where a statement comes from: a UESP page, a lore dossier, the extrapolation, the map itself.
CREATE TABLE "source" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "kind" TEXT NOT NULL CHECK ("kind" IN ('uesp', 'dossier', 'extrapolation', 'map', 'game', 'reasoning')),
  "title" TEXT NOT NULL,
  "locator" TEXT,            -- the page name, file path or file:line
  "url" TEXT
);

-- The settlement tiers of the map key, largest first (the glyph's shape gives the tier).
CREATE TABLE "settlement_tier" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "rank" INTEGER NOT NULL UNIQUE,      -- 1 the largest
  "label" TEXT NOT NULL,
  "glyph" TEXT NOT NULL,               -- the shape on the map
  "about" TEXT NOT NULL,
  "population_lo" INTEGER NOT NULL,    -- people living there in 4E 201 (Skyrim-scale: the named residents and guards)
  "population_hi" INTEGER NOT NULL,
  "footprint_radius_m" REAL NOT NULL   -- the built area's typical radius, from Skyrim's comparable places
);

-- What kind of place a thing is in our world: city, fort, camp, cave, Ayleid ruin... The map's symbol says it
-- for icons; for settlement glyphs the tier and the label say it.
CREATE TABLE "place_kind" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "label" TEXT NOT NULL,
  "family" TEXT NOT NULL CHECK ("family" IN ('settlement', 'military', 'work', 'camp', 'ruin', 'cave', 'landmark',
                                            'wreck', 'sunken')),
  "interior" TEXT NOT NULL CHECK ("interior" IN ('none', 'buildings', 'dungeon', 'cave', 'underwater')),
  "about" TEXT NOT NULL
);

-- The map key: every symbol the Black Marsh map uses, what Project Tamriel's key calls the same glyph, and what
-- it means in our world, with the reason.
CREATE TABLE "symbol" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "label" TEXT NOT NULL,                 -- our name for the symbol
  "glyph" TEXT NOT NULL,                 -- what it looks like
  "pt_key_name" TEXT,                    -- the Hammerfell / High Rock key's name for this glyph, if it has one
  "place_kind_id" TEXT REFERENCES "place_kind"("id"),   -- null for settlement glyphs (the place decides)
  "settlement_tier_id" TEXT REFERENCES "settlement_tier"("id"),
  "meaning" TEXT NOT NULL,               -- what it means in Black Marsh, 4E 201
  "why" TEXT NOT NULL,                   -- the reasoning and its sources
  "statement_tier_id" TEXT NOT NULL REFERENCES "statement_tier"("id")
);

-- The cultures: places sharing a shaded square colour (and glyph fill) on the map share a culture.
CREATE TABLE "culture" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "name" TEXT NOT NULL,
  "tint_hex" TEXT NOT NULL,              -- the square's colour on the map
  "glyph_hex" TEXT NOT NULL,             -- the glyph's fill
  "people" TEXT NOT NULL,                -- who they are (race, tribe, faction)
  "about" TEXT NOT NULL,                 -- way of life, building, belief, politics in 4E 201
  "why" TEXT NOT NULL,                   -- the reasoning that names them, with sources
  "statement_tier_id" TEXT NOT NULL REFERENCES "statement_tier"("id")
);

CREATE TABLE "road_class" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "label" TEXT NOT NULL,
  "map_style" TEXT NOT NULL,             -- how the map draws it
  "width_m" REAL NOT NULL,               -- the walked surface
  "paint_full_m" REAL NOT NULL,          -- road texture at full weight from the centreline
  "paint_fade_m" REAL NOT NULL,          -- road texture gone by this distance
  "grade_max" REAL NOT NULL,             -- the steepest rise over run along it
  "about" TEXT NOT NULL
);

-- Danger bands (nw-01 step 3c): fixed in the world, never levelled to the player (decision 0035).
CREATE TABLE "danger_band" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "rank" INTEGER NOT NULL UNIQUE,
  "label" TEXT NOT NULL,
  "foe_level" INTEGER NOT NULL,          -- the level of the foes met there
  "about" TEXT NOT NULL
);

-- What a place needs of the ground under it (terrain step 4).
CREATE TABLE "terrain_need" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT NOT NULL
);

-- What a place gives the player (newworld/sources/research/give_kinds.json; docs/research/new-world-place-gives.md).
CREATE TABLE "give_kind" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "group" TEXT NOT NULL CHECK ("group" IN ('travel', 'trade', 'craft', 'train', 'rest', 'blessing', 'resource', 'loot', 'combat')),
  "name" TEXT NOT NULL,
  "delivers" TEXT NOT NULL,              -- what it does in the game
  "evidence" TEXT NOT NULL               -- how Skyrim does it, counted from Skyrim.esm and the DLC
);

-- The aspects a place's or region's research prose is filed under.
CREATE TABLE "note_aspect" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "applies_to" TEXT NOT NULL CHECK ("applies_to" IN ('place', 'region', 'both', 'person')),
  "about" TEXT NOT NULL
);

-- Each kind's water type in the game (a WATR record we reuse; the world plugin sets it per cell as XCWT).
CREATE TABLE "water_kind" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "flows" BOOLEAN NOT NULL CHECK ("flows" IN (0, 1)),
  "about" TEXT NOT NULL,
  "watr_editor_id" TEXT,                 -- the WATR's editor id (the flowing kinds name the family; see flow_handling)
  "watr_form_key" TEXT,                  -- Mutagen form key, local id:defining plugin (the load order's winner sets its look)
  "flow_handling" TEXT                   -- how the flow reaches the game
);

-- ---------------------------------------------------------------------------------------------------------
-- The source maps and their frame
-- ---------------------------------------------------------------------------------------------------------

CREATE TABLE "map_source" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "title" TEXT NOT NULL,
  "file" TEXT NOT NULL,                  -- path in the repo
  "url" TEXT NOT NULL,
  "licence" TEXT NOT NULL,
  "width_px" INTEGER NOT NULL,
  "height_px" INTEGER NOT NULL,
  "about" TEXT NOT NULL
);

-- The one frame both maps share: pixels to cells to game units.
CREATE TABLE "map_frame" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "px_per_cell" INTEGER NOT NULL,
  "cell_x0_px" INTEGER NOT NULL,         -- west edge of cell column x = 0
  "cell_y0_px" INTEGER NOT NULL,         -- where the line y = 0 falls (rows grow southward)
  "cell_units" INTEGER NOT NULL,         -- a Morrowind cell's side in units
  "units_per_metre" REAL NOT NULL,
  "about" TEXT NOT NULL
);

-- ---------------------------------------------------------------------------------------------------------
-- Regions and cells
-- ---------------------------------------------------------------------------------------------------------

CREATE TABLE "region" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "name" TEXT NOT NULL,
  "map_label" TEXT NOT NULL,             -- as printed on the regions map
  "kind" TEXT NOT NULL CHECK ("kind" IN ('land', 'sea')),
  "map_hex" TEXT NOT NULL,               -- its colour on the regions map (over land)
  "label_px" REAL NOT NULL,
  "label_py" REAL NOT NULL,
  "summary" TEXT,                        -- two or three sentences for the reader who knows nothing
  "landform" TEXT,                       -- the ground's character: floodplain, mesa, ridge, mangrove...
  "elevation_floor_m" REAL,              -- typical lowest dry ground above the water
  "elevation_summit_m" REAL,             -- typical highest ground
  "roughness_m" REAL,                    -- local relief of hummocks and banks
  "cliff_share" REAL,                    -- share of slopes steep enough to be cliffs
  "wetness" REAL,                        -- 0 dry upland .. 1 standing swamp
  "biome" TEXT,                          -- the vegetation it carries
  "climate" TEXT,
  "culture_id" TEXT REFERENCES "culture"("id"),   -- the culture most of its places share
  "danger_band_id" TEXT REFERENCES "danger_band"("id"),  -- its baseline band away from roads and towns
  "statement_tier_id" TEXT REFERENCES "statement_tier"("id")
);

-- Every cell the world is built over: the province and its seas, and the margin round them.
CREATE TABLE "cell" (
  "x" INTEGER NOT NULL,
  "y" INTEGER NOT NULL,
  "region_id" TEXT NOT NULL REFERENCES "region"("id"),
  "land_share" REAL NOT NULL,            -- share of the cell that is dry land on the map
  "margin" INTEGER NOT NULL CHECK ("margin" IN (0, 1)),  -- 1: border scenery past the province (no navmesh, flora detail or danger)
  "danger_band_id" TEXT REFERENCES "danger_band"("id"),
  "danger_why" TEXT,                     -- the rule that set the band
  PRIMARY KEY ("x", "y")
);

-- ---------------------------------------------------------------------------------------------------------
-- Places
-- ---------------------------------------------------------------------------------------------------------

-- Every symbol on the map is a place. Every place carries the same fields.
CREATE TABLE "place" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "name" TEXT NOT NULL,                  -- its name in our world (the map's label, or an extrapolated name)
  "map_label" TEXT,                      -- exactly as printed on the map; null when unlabelled
  "symbol_id" TEXT NOT NULL REFERENCES "symbol"("id"),
  "place_kind_id" TEXT NOT NULL REFERENCES "place_kind"("id"),
  "culture_id" TEXT REFERENCES "culture"("id"),
  "region_id" TEXT NOT NULL REFERENCES "region"("id"),
  "cell_x" INTEGER NOT NULL,
  "cell_y" INTEGER NOT NULL,
  "px" REAL NOT NULL,                    -- the glyph's centre on the map
  "py" REAL NOT NULL,
  "world_x" REAL NOT NULL,
  "world_y" REAL NOT NULL,
  "on_water" BOOLEAN NOT NULL CHECK ("on_water" IN (0, 1)),   -- the glyph sits on water (island, wreck, sunken)
  "read_sure" BOOLEAN NOT NULL CHECK ("read_sure" IN (0, 1)),  -- the map read had no doubt
  "status" TEXT,                         -- in 4E 201: inhabited, garrisoned, abandoned, ruined, occupied, sunken
  "held_by" TEXT,                        -- who holds or haunts it now
  "population" INTEGER,                  -- people living there in 4E 201 (0 for a ruin or wild place)
  "footprint_radius_m" REAL,
  "siting" TEXT,                         -- its ground: riverbank, coast, island, lakeshore, inland, hilltop, seabed
  "danger_band_id" TEXT REFERENCES "danger_band"("id"),
  "importance" INTEGER,                  -- 5 shapes the province .. 1 local colour
  "summary" TEXT,                        -- two or three sentences for the reader who knows nothing
  "lore_page" TEXT,                      -- the UESP page, when canon names it
  "statement_tier_id" TEXT REFERENCES "statement_tier"("id")   -- the tier of the place's identity as a whole
);

-- Other names a place goes by (an older name, a tribal name, a misspelling on the map).
CREATE TABLE "place_alias" (
  "place_id" TEXT NOT NULL REFERENCES "place"("id"),
  "alias" TEXT NOT NULL,
  "source_id" TEXT REFERENCES "source"("id"),
  PRIMARY KEY ("place_id", "alias")
);

-- Researched prose about a place, one row per aspect.
CREATE TABLE "place_note" (
  "place_id" TEXT NOT NULL REFERENCES "place"("id"),
  "aspect_id" TEXT NOT NULL REFERENCES "note_aspect"("id"),
  "text" TEXT NOT NULL,
  "statement_tier_id" TEXT NOT NULL REFERENCES "statement_tier"("id"),
  PRIMARY KEY ("place_id", "aspect_id")
);

CREATE TABLE "place_note_source" (
  "place_id" TEXT NOT NULL,
  "aspect_id" TEXT NOT NULL,
  "source_id" TEXT NOT NULL REFERENCES "source"("id"),
  "locator" TEXT,                        -- the section or line within the source
  PRIMARY KEY ("place_id", "aspect_id", "source_id"),
  FOREIGN KEY ("place_id", "aspect_id") REFERENCES "place_note"("place_id", "aspect_id")
);

-- What the place needs of the terrain, so the land is built for it in one pass.
CREATE TABLE "place_terrain_need" (
  "place_id" TEXT NOT NULL REFERENCES "place"("id"),
  "terrain_need_id" TEXT NOT NULL REFERENCES "terrain_need"("id"),
  "radius_m" REAL NOT NULL,              -- the ground it shapes
  "facing_deg" REAL,                     -- for an entrance: the way the opening faces (0 north, clockwise)
  "why" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "terrain_need_id")
);

-- What each place gives (a place record's gives list, in order); a combat give names the loot give that rewards it.
CREATE TABLE "place_give" (
  "place_id" TEXT NOT NULL REFERENCES "place"("id"),
  "seq" INTEGER NOT NULL,                -- its order in the record
  "give_kind_id" TEXT NOT NULL REFERENCES "give_kind"("id"),
  "detail" TEXT NOT NULL,                -- specific: 'Expert Alteration trainer', 'iron and corundum veins'
  "count" INTEGER NOT NULL CHECK ("count" >= 1),
  "reward_kind_id" TEXT REFERENCES "give_kind"("id"),   -- combat only: the loot give at this place that pays for it
  PRIMARY KEY ("place_id", "seq")
);

-- ---------------------------------------------------------------------------------------------------------
-- Stocking (newworld/sources/stock/; tools/newworld/wealth.py; docs/design/place-studio.md "Stock")
-- ---------------------------------------------------------------------------------------------------------

-- A lock's level as the game stores it (REFR XLOC).
CREATE TABLE "lock_level" (
  "id" TEXT NOT NULL PRIMARY KEY,        -- Novice, Apprentice, Adept, Expert, Master, Requires key
  "level" INTEGER NOT NULL UNIQUE        -- 1, 25, 50, 75, 100, 255
);

-- The one fixed scale of quality for the whole game: material, enchantment grade, gold, lock (decision 0035).
CREATE TABLE "stock_tier" (
  "id" TEXT NOT NULL PRIMARY KEY,        -- T1..T6
  "rank" INTEGER NOT NULL UNIQUE,
  "label" TEXT NOT NULL,
  "ref_level" INTEGER NOT NULL,          -- the vanilla list level whose gates it matches (a check, not a scaling)
  "enchant_grade" INTEGER NOT NULL,      -- vanilla's enchantment grade 1..6
  "lock_level_id" TEXT NOT NULL REFERENCES "lock_level"("id"),   -- the lock the best thing of this tier sits behind
  "gold_lo" INTEGER NOT NULL,            -- a store's gold at this tier
  "gold_hi" INTEGER NOT NULL,
  "value_max" INTEGER NOT NULL,          -- a container's significant things together, at most
  "about" TEXT NOT NULL
);

-- How well off a place is (P1 poor .. P5 rich): its ceiling tier, its traders' gold, its people's bands.
CREATE TABLE "place_wealth_band" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "rank" INTEGER NOT NULL UNIQUE,
  "label" TEXT NOT NULL,
  "min_score" INTEGER NOT NULL,
  "ceiling_tier_id" TEXT NOT NULL REFERENCES "stock_tier"("id"),
  "trader_gold_mult" REAL NOT NULL,
  "people" TEXT NOT NULL,                -- the spread of person wealth bands it holds
  "about" TEXT NOT NULL
);

-- How well off a person is (W1 destitute .. W5 wealthy): the gold they carry and keep, the best tier they own.
CREATE TABLE "person_wealth_band" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "rank" INTEGER NOT NULL UNIQUE,
  "label" TEXT NOT NULL,
  "carried_lo" INTEGER NOT NULL,
  "carried_hi" INTEGER NOT NULL,
  "home_lo" INTEGER NOT NULL,
  "home_hi" INTEGER NOT NULL,
  "top_tier" TEXT NOT NULL,              -- a tier id, or 'ceiling' (the place's)
  "about" TEXT NOT NULL
);

-- Each place's wealth and its band on the scale, derived with its reason; `by` says whether the owner overruled it.
CREATE TABLE "place_wealth" (
  "place_id" TEXT NOT NULL PRIMARY KEY REFERENCES "place"("id"),
  "wealth_score" REAL,                   -- null: nobody lives there; the ground alone sets its band
  "place_wealth_band_id" TEXT REFERENCES "place_wealth_band"("id"),
  "open_tier_id" TEXT NOT NULL REFERENCES "stock_tier"("id"),     -- what lies open, or along the way
  "ceiling_tier_id" TEXT NOT NULL REFERENCES "stock_tier"("id"),  -- the best it holds without the ledger
  "why" TEXT NOT NULL,
  "by" TEXT NOT NULL CHECK ("by" IN ('derived', 'owner'))
);

-- What a tier is made of: its weapon and armour materials, by the game's material keyword, best first.
CREATE TABLE "tier_material" (
  "stock_tier_id" TEXT NOT NULL REFERENCES "stock_tier"("id"),
  "slot" TEXT NOT NULL CHECK ("slot" IN ('weapon', 'armour')),
  "keyword" TEXT NOT NULL,               -- the KYWD editor id (WeapMaterialSteel)
  "ord" INTEGER NOT NULL,
  PRIMARY KEY ("stock_tier_id", "slot", "keyword")
);

-- The other things a tier names: its soul gem, gems and jewellery (rows of the item catalogue).
CREATE TABLE "tier_item" (
  "stock_tier_id" TEXT NOT NULL REFERENCES "stock_tier"("id"),
  "item_id" TEXT NOT NULL REFERENCES "item"("id"),
  "use" TEXT NOT NULL CHECK ("use" IN ('soul-gem', 'gem', 'jewellery')),
  PRIMARY KEY ("stock_tier_id", "item_id")
);

-- Materials and kits that never reach the player (decision 0006): Skyrim's own peoples' and orders' gear.
CREATE TABLE "never_material" (
  "keyword" TEXT NOT NULL PRIMARY KEY,
  "why" TEXT NOT NULL
);

-- How well a thing is kept (S0 open .. S5 vault); each tier above the open tier needs one more step.
CREATE TABLE "security_level" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "rank" INTEGER NOT NULL UNIQUE,
  "label" TEXT NOT NULL,
  "means" TEXT NOT NULL
);

-- How hard a thing is to reach on wild ground (E0 in plain sight .. E4 beside the boss).
CREATE TABLE "effort_level" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "rank" INTEGER NOT NULL UNIQUE,
  "means" TEXT NOT NULL,
  "tier" TEXT NOT NULL CHECK ("tier" IN ('below', 'band'))   -- the ground's tier below its band, or the band's own
);

-- Kinds of container, read from a container base's editor id, name and model (the split).
CREATE TABLE "container_kind" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "always_significant" BOOLEAN NOT NULL CHECK ("always_significant" IN (0, 1)),
  "words" TEXT NOT NULL                  -- the patterns that name it, in the split's order
);

-- Kinds of item (weapon, armour, clothing, jewellery, gem, gold, potion, food, clutter...).
CREATE TABLE "item_kind" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "always_significant" BOOLEAN NOT NULL CHECK ("always_significant" IN (0, 1)),
  "about" TEXT NOT NULL
);

-- A catalogue of game item forms that stocking uses (the flora_base pattern): generated by
-- `python -m tools.newworld.stockdb items` from the plugins for every item a stock source or the scale names.
CREATE TABLE "item" (
  "id" TEXT NOT NULL PRIMARY KEY,        -- "<plugin>:<6 hex>", the places' key shape
  "form_key" TEXT NOT NULL UNIQUE,       -- Mutagen's "<6 hex>:<plugin>"
  "plugin" TEXT NOT NULL,
  "edid" TEXT,
  "name" TEXT,
  "record" TEXT NOT NULL,                -- WEAP, ARMO, MISC, BOOK, ALCH, INGR, AMMO, SLGM, KEYM, SCRL
  "item_kind_id" TEXT NOT NULL REFERENCES "item_kind"("id"),
  "value" INTEGER NOT NULL,
  "material" TEXT,                       -- its material keyword, if any
  "stock_tier_id" TEXT REFERENCES "stock_tier"("id"),   -- by material, else by value against the tiers' value_max
  "enchanted" BOOLEAN NOT NULL CHECK ("enchanted" IN (0, 1)),
  "significant" BOOLEAN NOT NULL CHECK ("significant" IN (0, 1)),
  "never" BOOLEAN NOT NULL CHECK ("never" IN (0, 1))    -- a never_material or a Skyrim-only kit (decision 0006)
);

-- Goods: what places make, trade and need (from the economy notes), so provenance is computable on the roads.
CREATE TABLE "good" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "name" TEXT NOT NULL,
  "kind" TEXT NOT NULL CHECK ("kind" IN ('food', 'material', 'craft', 'luxury', 'service')),
  "about" TEXT NOT NULL
);

CREATE TABLE "place_good" (
  "place_id" TEXT NOT NULL REFERENCES "place"("id"),
  "good_id" TEXT NOT NULL REFERENCES "good"("id"),
  "relation" TEXT NOT NULL CHECK ("relation" IN ('makes', 'trades', 'needs')),
  "why" TEXT NOT NULL,
  "statement_tier_id" TEXT NOT NULL REFERENCES "statement_tier"("id"),
  PRIMARY KEY ("place_id", "good_id", "relation")
);

-- What an item kind is made from, so a place that makes the good makes the thing (made here is common and cheap).
CREATE TABLE "good_material" (
  "good_id" TEXT NOT NULL REFERENCES "good"("id"),
  "keyword" TEXT NOT NULL,               -- a material keyword the good yields (ArmorMaterialHide), or an item kind id
  PRIMARY KEY ("good_id", "keyword")
);

-- ---------------------------------------------------------------------------------------------------------
-- People (newworld/sources/people/<place_id>.json; tools/newworld/stockdb.py). nw-05 fills every place's;
-- the place folder keeps only placement (bed, work, routine) in people.jsonl, keyed by the same person id.
-- ---------------------------------------------------------------------------------------------------------

CREATE TABLE "race" (
  "id" TEXT NOT NULL PRIMARY KEY,        -- the RACE editor id (ArgonianRace)
  "form_key" TEXT NOT NULL,
  "name" TEXT NOT NULL
);

-- A person's part in the place (the placement's role: guard, resident, merchant, smith...).
CREATE TABLE "person_role" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT NOT NULL
);

-- A person's place in their household (head, partner, grown child, elder, sibling, cousin, lodger, levy...).
CREATE TABLE "household_role" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "about" TEXT NOT NULL
);

-- Ties between people across or within households.
CREATE TABLE "relation_kind" (
  "id" TEXT NOT NULL PRIMARY KEY,        -- parent-of, partner-of, sibling-of, kin-of, friend-of, rival-of, works-for
  "symmetric" BOOLEAN NOT NULL CHECK ("symmetric" IN (0, 1)),
  "about" TEXT NOT NULL
);

-- One roof's people: who lives together in one home.
CREATE TABLE "household" (
  "id" TEXT NOT NULL PRIMARY KEY,        -- <place_id>.household.<home space>
  "place_id" TEXT NOT NULL REFERENCES "place"("id"),
  "home_space" TEXT NOT NULL,            -- the place file's space id of the home
  "name" TEXT                            -- what the place calls it, when it has a name
);

CREATE TABLE "person" (
  "id" TEXT NOT NULL PRIMARY KEY,        -- the place files' person id (<place_id>.<ulid>), stable for life
  "name" TEXT NOT NULL,
  "sex" TEXT NOT NULL CHECK ("sex" IN ('male', 'female')),
  "race_id" TEXT NOT NULL REFERENCES "race"("id"),
  "culture_id" TEXT REFERENCES "culture"("id"),
  "place_id" TEXT NOT NULL REFERENCES "place"("id"),      -- home place
  "household_id" TEXT REFERENCES "household"("id"),
  "household_role_id" TEXT REFERENCES "household_role"("id"),
  "person_role_id" TEXT NOT NULL REFERENCES "person_role"("id"),
  "trade" TEXT NOT NULL,                 -- what they do, in a few words
  "person_wealth_band_id" TEXT NOT NULL REFERENCES "person_wealth_band"("id"),
  "level" INTEGER,                       -- fixed (decision 0035); null until set
  "status" TEXT NOT NULL CHECK ("status" IN ('alive', 'dead', 'missing')),
  "statement_tier_id" TEXT NOT NULL REFERENCES "statement_tier"("id")
);

-- Researched prose about a person, one row per aspect (backstory now; personality, secrets, relationships later).
CREATE TABLE "person_note" (
  "person_id" TEXT NOT NULL REFERENCES "person"("id"),
  "aspect_id" TEXT NOT NULL REFERENCES "note_aspect"("id"),
  "text" TEXT NOT NULL,
  "statement_tier_id" TEXT NOT NULL REFERENCES "statement_tier"("id"),
  PRIMARY KEY ("person_id", "aspect_id")
);

CREATE TABLE "person_note_source" (
  "person_id" TEXT NOT NULL,
  "aspect_id" TEXT NOT NULL,
  "source_id" TEXT NOT NULL REFERENCES "source"("id"),
  "locator" TEXT,
  PRIMARY KEY ("person_id", "aspect_id", "source_id"),
  FOREIGN KEY ("person_id", "aspect_id") REFERENCES "person_note"("person_id", "aspect_id")
);

CREATE TABLE "person_relation" (
  "person_id" TEXT NOT NULL REFERENCES "person"("id"),
  "other_id" TEXT NOT NULL REFERENCES "person"("id"),
  "relation_kind_id" TEXT NOT NULL REFERENCES "relation_kind"("id"),
  PRIMARY KEY ("person_id", "other_id", "relation_kind_id")
);

-- Faction membership: a game faction's form key, or a place faction the build makes (<place_id>.guard).
CREATE TABLE "person_faction" (
  "person_id" TEXT NOT NULL REFERENCES "person"("id"),
  "faction" TEXT NOT NULL,
  "rank" INTEGER NOT NULL,
  PRIMARY KEY ("person_id", "faction")
);

-- ---------------------------------------------------------------------------------------------------------
-- Stock: what holds what and why (newworld/sources/stock/places/<place_id>.json). Each holder is its own table;
-- a container or a loose thing is the place file's ref id within its place. Nothing here is levelled.
-- ---------------------------------------------------------------------------------------------------------

-- A container the place authors: its kind, owner, lock and the tier it holds, with the reason.
CREATE TABLE "stock_container" (
  "place_id" TEXT NOT NULL REFERENCES "place"("id"),
  "ref_id" TEXT NOT NULL,                -- the place files' ref id (our id, or a copied room's source key)
  "space_id" TEXT NOT NULL,
  "container_kind_id" TEXT NOT NULL REFERENCES "container_kind"("id"),
  "owner_person_id" TEXT REFERENCES "person"("id"),
  "owner_household_id" TEXT REFERENCES "household"("id"),
  "owner_faction" TEXT,                  -- a game faction key or a place faction (<place_id>.guard)
  "lock_level_id" TEXT REFERENCES "lock_level"("id"),     -- null: unlocked
  "security_level_id" TEXT NOT NULL REFERENCES "security_level"("id"),
  "effort_level_id" TEXT REFERENCES "effort_level"("id"), -- wild ground only
  "stock_tier_id" TEXT NOT NULL REFERENCES "stock_tier"("id"),
  "gold" INTEGER NOT NULL CHECK ("gold" >= 0),
  "why" TEXT NOT NULL,
  CHECK (("owner_person_id" IS NOT NULL) + ("owner_household_id" IS NOT NULL) + ("owner_faction" IS NOT NULL) <= 1),
  PRIMARY KEY ("place_id", "ref_id")
);

CREATE TABLE "stock_container_item" (
  "place_id" TEXT NOT NULL,
  "ref_id" TEXT NOT NULL,
  "item_id" TEXT NOT NULL REFERENCES "item"("id"),
  "count" INTEGER NOT NULL CHECK ("count" >= 1),
  "why" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "ref_id", "item_id"),
  FOREIGN KEY ("place_id", "ref_id") REFERENCES "stock_container"("place_id", "ref_id")
);

-- A significant thing lying loose: on a ref of the place files (a table, a shelf) or at a position in a space.
CREATE TABLE "stock_loose" (
  "place_id" TEXT NOT NULL REFERENCES "place"("id"),
  "id" TEXT NOT NULL,                    -- a new thing's ref id (<place_id>.<ulid>), or a ref of the place kept where it stands
  "space_id" TEXT NOT NULL,
  "on_ref_id" TEXT,                      -- a new thing: the ref it lies on, or null with a position
  "x" REAL, "y" REAL, "z" REAL,        -- a kept ref (id is the place's own ref): none of these; the place files place it
  "item_id" TEXT NOT NULL REFERENCES "item"("id"),
  "count" INTEGER NOT NULL CHECK ("count" >= 1),
  "owner_person_id" TEXT REFERENCES "person"("id"),
  "owner_faction" TEXT,
  "effort_level_id" TEXT REFERENCES "effort_level"("id"),
  "why" TEXT NOT NULL,
  CHECK ("on_ref_id" IS NULL OR "x" IS NULL),
  CHECK (("x" IS NULL) = ("y" IS NULL) AND ("x" IS NULL) = ("z" IS NULL)),
  PRIMARY KEY ("place_id", "id")
);

-- What a person carries and wears: their inventory on our NPC record (outfit and carried items alike).
CREATE TABLE "person_item" (
  "person_id" TEXT NOT NULL REFERENCES "person"("id"),
  "item_id" TEXT NOT NULL REFERENCES "item"("id"),
  "count" INTEGER NOT NULL CHECK ("count" >= 1),
  "worn" BOOLEAN NOT NULL CHECK ("worn" IN (0, 1)),
  "why" TEXT NOT NULL,
  PRIMARY KEY ("person_id", "item_id")
);

-- A trader's fixed list: what their merchant chest restocks to every 48 hours, and their gold.
CREATE TABLE "trader" (
  "person_id" TEXT NOT NULL PRIMARY KEY REFERENCES "person"("id"),
  "gold" INTEGER NOT NULL CHECK ("gold" >= 0),
  "why" TEXT NOT NULL
);

CREATE TABLE "trader_item" (
  "person_id" TEXT NOT NULL REFERENCES "trader"("person_id"),
  "item_id" TEXT NOT NULL REFERENCES "item"("id"),
  "count" INTEGER NOT NULL CHECK ("count" >= 1),
  "why" TEXT NOT NULL,
  PRIMARY KEY ("person_id", "item_id")
);

-- The facts a stock holder's reason cites (the place_note_source pattern), one table per holder kind.
CREATE TABLE "stock_container_source" (
  "place_id" TEXT NOT NULL,
  "ref_id" TEXT NOT NULL,
  "source_id" TEXT NOT NULL REFERENCES "source"("id"),
  "locator" TEXT,
  PRIMARY KEY ("place_id", "ref_id", "source_id"),
  FOREIGN KEY ("place_id", "ref_id") REFERENCES "stock_container"("place_id", "ref_id")
);

CREATE TABLE "trader_source" (
  "person_id" TEXT NOT NULL REFERENCES "trader"("person_id"),
  "source_id" TEXT NOT NULL REFERENCES "source"("id"),
  "locator" TEXT,
  PRIMARY KEY ("person_id", "source_id")
);

-- The world ledger: the exceptional (uniques, the best gear), authored by story and counted game-wide.
CREATE TABLE "unique_item" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "item_id" TEXT NOT NULL REFERENCES "item"("id"),
  "place_id" TEXT NOT NULL REFERENCES "place"("id"),
  "held_by" TEXT NOT NULL,               -- where: a container ref id, a person id, or a loose id of that place
  "story" TEXT NOT NULL,                 -- the quest or story that puts it there
  "why" TEXT NOT NULL
);

-- Each promise of a place (place_give) and what delivers it, so 'every promise delivered' is a query.
CREATE TABLE "give_delivery" (
  "place_id" TEXT NOT NULL,
  "give_seq" INTEGER NOT NULL,
  "seq" INTEGER NOT NULL,
  "by" TEXT NOT NULL CHECK ("by" IN ('person', 'container', 'loose', 'ref', 'record')),
  "person_id" TEXT REFERENCES "person"("id"),
  "ref_id" TEXT,                         -- a stock container, loose thing or built ref (station, marker) of the place
  "status" TEXT NOT NULL CHECK ("status" IN ('delivered', 'open', 'dropped')),
  "why" TEXT NOT NULL,
  CHECK (("by" = 'person') = ("person_id" IS NOT NULL)),
  CHECK (("by" IN ('container', 'loose', 'ref')) = ("ref_id" IS NOT NULL)),
  PRIMARY KEY ("place_id", "give_seq", "seq"),
  FOREIGN KEY ("place_id", "give_seq") REFERENCES "place_give"("place_id", "seq")
);

CREATE TABLE "region_note" (
  "region_id" TEXT NOT NULL REFERENCES "region"("id"),
  "aspect_id" TEXT NOT NULL REFERENCES "note_aspect"("id"),
  "text" TEXT NOT NULL,
  "statement_tier_id" TEXT NOT NULL REFERENCES "statement_tier"("id"),
  PRIMARY KEY ("region_id", "aspect_id")
);

CREATE TABLE "region_note_source" (
  "region_id" TEXT NOT NULL,
  "aspect_id" TEXT NOT NULL,
  "source_id" TEXT NOT NULL REFERENCES "source"("id"),
  "locator" TEXT,
  PRIMARY KEY ("region_id", "aspect_id", "source_id"),
  FOREIGN KEY ("region_id", "aspect_id") REFERENCES "region_note"("region_id", "aspect_id")
);

-- ---------------------------------------------------------------------------------------------------------
-- Roads, borders, water
-- ---------------------------------------------------------------------------------------------------------

-- The road network as a graph: nodes are places, junctions and ends; each road runs node to node.
CREATE TABLE "road_node" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "kind" TEXT NOT NULL CHECK ("kind" IN ('place', 'junction', 'end', 'ferry')),
  "place_id" TEXT REFERENCES "place"("id"),
  "px" REAL NOT NULL,
  "py" REAL NOT NULL,
  "world_x" REAL NOT NULL,
  "world_y" REAL NOT NULL
);

CREATE TABLE "road" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "road_class_id" TEXT NOT NULL REFERENCES "road_class"("id"),
  "from_node_id" TEXT NOT NULL REFERENCES "road_node"("id"),
  "to_node_id" TEXT NOT NULL REFERENCES "road_node"("id"),
  "length_m" REAL NOT NULL,
  "crosses_water_m" REAL NOT NULL        -- how much of it the map draws over water (bridges, causeways, fords)
);

-- A road's centreline, node to node, in order (about one vertex every 3 map pixels, 17 m).
CREATE TABLE "road_vertex" (
  "road_id" TEXT NOT NULL REFERENCES "road"("id"),
  "seq" INTEGER NOT NULL,
  "px" REAL NOT NULL,
  "py" REAL NOT NULL,
  "world_x" REAL NOT NULL,
  "world_y" REAL NOT NULL,
  "on_water" BOOLEAN NOT NULL CHECK ("on_water" IN (0, 1)),
  PRIMARY KEY ("road_id", "seq")
);

-- Lines drawn on the map: the province border and the region borders.
CREATE TABLE "border" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "kind" TEXT NOT NULL CHECK ("kind" IN ('province', 'region')),
  "about" TEXT NOT NULL
);

CREATE TABLE "border_vertex" (
  "border_id" TEXT NOT NULL REFERENCES "border"("id"),
  "part" INTEGER NOT NULL,               -- a border may be drawn in several pieces
  "seq" INTEGER NOT NULL,
  "px" REAL NOT NULL,
  "py" REAL NOT NULL,
  "world_x" REAL NOT NULL,
  "world_y" REAL NOT NULL,
  PRIMARY KEY ("border_id", "part", "seq")
);

-- Each body of water on the map, classified by tools/newworld/water_kinds.py (shape, place, region research), with the
-- owner's edits from the atlas's water editor applied last.
CREATE TABLE "water_body" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "water_kind_id" TEXT NOT NULL REFERENCES "water_kind"("id"),
  "name" TEXT,
  "area_m2" REAL NOT NULL,
  "label_px" REAL NOT NULL,              -- a point inside it
  "label_py" REAL NOT NULL,
  "flows" BOOLEAN NOT NULL CHECK ("flows" IN (0, 1)),
  "flow_toward_deg" REAL,                -- the way it flows (0 north, clockwise), when it flows
  "speed" TEXT CHECK ("speed" IN ('still', 'slow', 'moderate', 'fast')),
  "downstream_id" TEXT,                  -- the body it runs into (a water_body id)
  "width_m" REAL,                        -- mean width
  "region_id" TEXT,
  "flow_note" TEXT,
  "set_by" TEXT NOT NULL CHECK ("set_by" IN ('derived', 'owner')),
  "why" TEXT NOT NULL
);

-- ---------------------------------------------------------------------------------------------------------
-- Travel: the boat, coach and rootworm network (newworld/sources/travel/network.json; tools/newworld/travel.py;
-- docs/design/travel-network.md). No place promises map fast travel; a stop is a place's promise on the network.
-- ---------------------------------------------------------------------------------------------------------

-- A way of travelling: what it needs of the ground, who runs it, its fixed fare rule and pace (decision 0035).
CREATE TABLE "travel_mode" (
  "id" TEXT NOT NULL PRIMARY KEY,        -- boat, coach, rootworm
  "name" TEXT NOT NULL,
  "give_kind_id" TEXT NOT NULL UNIQUE REFERENCES "give_kind"("id"),   -- the place record's give for a stop of it
  "needs" TEXT NOT NULL,                 -- what the ground must offer from stop to stop
  "road_class_id" TEXT REFERENCES "road_class"("id"),                 -- a coach's road, the whole way
  "operated_by" TEXT NOT NULL,
  "fare_base" INTEGER NOT NULL,          -- fare = base + per_km x km, rounded to step, held in [min, max]
  "fare_per_km" REAL NOT NULL,
  "fare_step" INTEGER NOT NULL,
  "fare_min" INTEGER NOT NULL,
  "fare_max" INTEGER NOT NULL,
  "speed_kmh" REAL NOT NULL,             -- hours = board_h + km / speed, whole, at least 1
  "board_h" REAL NOT NULL,
  "evidence" TEXT NOT NULL,              -- how Bethesda did it
  "why" TEXT NOT NULL                    -- the lore it stands on
);

-- The water a boat mode runs on: a water kind, and the narrowest of it that carries a boat.
CREATE TABLE "travel_mode_water" (
  "travel_mode_id" TEXT NOT NULL REFERENCES "travel_mode"("id"),
  "water_kind_id" TEXT NOT NULL REFERENCES "water_kind"("id"),
  "min_width_m" REAL,                    -- null: any width
  PRIMARY KEY ("travel_mode_id", "water_kind_id")
);

-- Who runs a stop: the operator's kind, its craft and how much open sea it crosses.
CREATE TABLE "travel_operator" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "travel_mode_id" TEXT NOT NULL REFERENCES "travel_mode"("id"),
  "name" TEXT NOT NULL,
  "craft" TEXT NOT NULL,
  "open_sea_max_m" REAL,                 -- the most open sea (ocean, bay) one passage may cross; null: any
  "who" TEXT NOT NULL,
  "why" TEXT NOT NULL
);

-- A stop: a place's promise of a mode (its place_give of the mode's kind), its operator and its part in the network.
CREATE TABLE "travel_stop" (
  "place_id" TEXT NOT NULL REFERENCES "place"("id"),
  "travel_mode_id" TEXT NOT NULL REFERENCES "travel_mode"("id"),
  "give_seq" INTEGER NOT NULL,
  "travel_operator_id" TEXT NOT NULL REFERENCES "travel_operator"("id"),
  "rank" TEXT NOT NULL CHECK ("rank" IN ('hub', 'spoke')),
  "why" TEXT NOT NULL,
  PRIMARY KEY ("place_id", "travel_mode_id"),
  FOREIGN KEY ("place_id", "give_seq") REFERENCES "place_give"("place_id", "seq")
);

-- A route from one stop to another of the same mode (authored as a pair, built both ways), measured on the ground.
CREATE TABLE "travel_route" (
  "from_place_id" TEXT NOT NULL,
  "to_place_id" TEXT NOT NULL,
  "travel_mode_id" TEXT NOT NULL REFERENCES "travel_mode"("id"),
  "distance_m" INTEGER NOT NULL,         -- boat: along the water; coach: along the road; rootworm: straight
  "open_sea_m" INTEGER NOT NULL,         -- of it, over ocean or bay
  "fare" INTEGER NOT NULL CHECK ("fare" > 0),   -- the mode's rule over the distance
  "hours" INTEGER NOT NULL,
  "why" TEXT NOT NULL,
  PRIMARY KEY ("from_place_id", "to_place_id", "travel_mode_id"),
  FOREIGN KEY ("from_place_id", "travel_mode_id") REFERENCES "travel_stop"("place_id", "travel_mode_id"),
  FOREIGN KEY ("to_place_id", "travel_mode_id") REFERENCES "travel_stop"("place_id", "travel_mode_id")
);

-- How one reaches a place that is no stop: from the nearest stop, and how (derived), or why it is remote (authored).
CREATE TABLE "travel_approach" (
  "place_id" TEXT NOT NULL PRIMARY KEY REFERENCES "place"("id"),
  "stop_place_id" TEXT NOT NULL,
  "travel_mode_id" TEXT NOT NULL,
  "foot_m" INTEGER NOT NULL,             -- by road when a road joins them, else straight
  "way" TEXT NOT NULL CHECK ("way" IN ('road', 'marsh', 'water', 'dive')),
  "remote" INTEGER NOT NULL CHECK ("remote" IN (0, 1)),   -- 1: off the network on purpose, `why` says so
  "why" TEXT NOT NULL,
  FOREIGN KEY ("stop_place_id", "travel_mode_id") REFERENCES "travel_stop"("place_id", "travel_mode_id")
);

-- ---------------------------------------------------------------------------------------------------------
-- Terrain (step 4): the built rasters are outputs, rebuilt by tools/newworld/terrain.py; this records each build.
-- ---------------------------------------------------------------------------------------------------------

CREATE TABLE "terrain_build" (
  "id" TEXT NOT NULL PRIMARY KEY,        -- the build's stamp
  "water_level_units" REAL NOT NULL,     -- the one water height
  "sample_units" REAL NOT NULL,          -- heightmap spacing (Skyrim's LAND vertex: 128 units)
  "width" INTEGER NOT NULL,
  "height" INTEGER NOT NULL,
  "origin_world_x" REAL NOT NULL,        -- the world position of sample (0, 0), the north-west corner
  "origin_world_y" REAL NOT NULL,
  "files" TEXT NOT NULL,                 -- where the rasters are (out/newworld/terrain/ and the bucket)
  "sha256" TEXT NOT NULL,                -- of the heightmap file
  "about" TEXT NOT NULL
);

-- ---------------------------------------------------------------------------------------------------------
-- Flora: plant, tree and rock sets per region (nw-02 step 6; tools/newworld/flora.py from newworld/sources/flora/)
-- ---------------------------------------------------------------------------------------------------------

-- A placement class: how bases of the class tilt with the ground and sink when no measured seating exists.
CREATE TABLE "flora_class" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "tilt_factor" REAL NOT NULL,           -- tilt = factor x ground slope
  "tilt_max_deg" REAL NOT NULL,
  "sink_m" REAL,                         -- fallback pivot sink below ground (trees, plants)
  "sink_ratio" REAL,                     -- fallback sink as a share of the base's height (rocks, cliffs)
  "about" TEXT NOT NULL
);

-- A family of bases that look and behave alike (bald cypress, coconut palm, reed, coral...).
CREATE TABLE "flora_family" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "flora_class_id" TEXT NOT NULL REFERENCES "flora_class"("id"),
  "standing_water_max_m" REAL,           -- deepest still water a base may stand in; NULL = never in water
  "water_only" INTEGER NOT NULL CHECK ("water_only" IN (0, 1)),  -- 1: only on a water surface (lilies)
  "seabed_min_m" REAL,                   -- for seabed families: the depth band measured in Depths of Skyrim
  "seabed_max_m" REAL,
  "cluster_size" INTEGER NOT NULL,       -- typical refs per clump (from nearest-neighbour clumping)
  "about" TEXT NOT NULL                  -- with the study's measured evidence
);

-- One base object from a mod, as the flora study catalogued it.
CREATE TABLE "flora_base" (
  "id" TEXT NOT NULL PRIMARY KEY,        -- our id: mod and editor id, slugged
  "form_key" TEXT NOT NULL,              -- FormID:plugin, as in the catalogue
  "plugin" TEXT NOT NULL,
  "mod" TEXT NOT NULL,                   -- BM&V, KoTM, TS, Depths
  "edid" TEXT NOT NULL,
  "model" TEXT NOT NULL,                 -- mesh path under meshes\
  "flora_family_id" TEXT NOT NULL REFERENCES "flora_family"("id"),
  "size" TEXT NOT NULL CHECK ("size" IN ('small', 'medium', 'large', 'huge')),
  "height_m" REAL NOT NULL,              -- OBND height
  "sink_m" REAL NOT NULL,                -- pivot Z = ground Z - sink_m (measured median, or the class fallback)
  "sink_lo_m" REAL,                      -- measured IQR, for jitter
  "sink_hi_m" REAL,
  "sink_measured_in" TEXT,               -- the worldspace the median comes from; NULL = class fallback
  "scale_med" REAL,                      -- the authors' median scale where measured
  "placed_refs" INTEGER NOT NULL,        -- refs the authors placed (all worlds)
  "nordic_override" TEXT                 -- why a base the study's name flag marked Nordic is not Nordic
);

-- Where flora stands: dry ground, still water (never flowing), or a seabed depth band.
CREATE TABLE "habitat" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "name" TEXT NOT NULL,
  "water" TEXT NOT NULL CHECK ("water" IN ('dry', 'standing', 'seabed')),
  "depth_min_m" REAL,
  "depth_max_m" REAL,                    -- standing: the deepest still water; seabed: the band's floor
  "density_per_ha" REAL NOT NULL,        -- all flora refs per hectare
  "about" TEXT NOT NULL
);

-- The share of a habitat's refs each family takes.
CREATE TABLE "habitat_family" (
  "habitat_id" TEXT NOT NULL REFERENCES "habitat"("id"),
  "flora_family_id" TEXT NOT NULL REFERENCES "flora_family"("id"),
  "share" REAL NOT NULL,
  PRIMARY KEY ("habitat_id", "flora_family_id")
);

-- Companion groups: families the authors stamp together (co-occurrence lifts within 10 m).
CREATE TABLE "flora_guild" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "lift" REAL NOT NULL,
  "evidence" TEXT NOT NULL
);

CREATE TABLE "flora_guild_member" (
  "flora_guild_id" TEXT NOT NULL REFERENCES "flora_guild"("id"),
  "flora_family_id" TEXT NOT NULL REFERENCES "flora_family"("id"),
  "role" TEXT NOT NULL CHECK ("role" IN ('anchor', 'partner')),
  PRIMARY KEY ("flora_guild_id", "flora_family_id")
);

-- A region's habitats and the research they rest on. Standing-water habitats here are the only places a base
-- may stand in water, to the lesser of the habitat's and the family's depth.
CREATE TABLE "region_habitat" (
  "region_id" TEXT NOT NULL REFERENCES "region"("id"),
  "habitat_id" TEXT NOT NULL REFERENCES "habitat"("id"),
  "share" REAL NOT NULL,                 -- of the region's flora-bearing ground
  "note_aspect_id" TEXT REFERENCES "note_aspect"("id"),  -- the region_note it cites; NULL = the region row
  "why" TEXT NOT NULL,
  PRIMARY KEY ("region_id", "habitat_id")
);

-- A region's own leaning toward or away from a family, from its research.
CREATE TABLE "region_family" (
  "region_id" TEXT NOT NULL REFERENCES "region"("id"),
  "flora_family_id" TEXT NOT NULL REFERENCES "flora_family"("id"),
  "boost" REAL NOT NULL,                 -- multiplier on the habitat share; 0 = left out
  "note_aspect_id" TEXT REFERENCES "note_aspect"("id"),
  "why" TEXT NOT NULL,
  PRIMARY KEY ("region_id", "flora_family_id")
);

-- The set: each base a region grows, in which habitat and how much. Its reason is the research it rests on:
-- region_habitat.why for (region, habitat) and region_family.why for (region, the base's family), each citing its
-- region_note; clump size is the family's cluster_size.
CREATE TABLE "region_flora" (
  "region_id" TEXT NOT NULL REFERENCES "region"("id"),
  "habitat_id" TEXT NOT NULL REFERENCES "habitat"("id"),
  "flora_base_id" TEXT NOT NULL REFERENCES "flora_base"("id"),
  "weight" REAL NOT NULL,                -- share of the region's flora refs (sums to 1 per region)
  "density_per_ha" REAL NOT NULL,        -- refs per hectare of this habitat
  "water_max_m" REAL,                    -- still water it may stand in here (habitat and family allow); NULL = dry
  PRIMARY KEY ("region_id", "habitat_id", "flora_base_id"),
  FOREIGN KEY ("region_id", "habitat_id") REFERENCES "region_habitat"("region_id", "habitat_id")
);
