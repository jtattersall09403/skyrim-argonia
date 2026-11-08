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

-- The aspects a place's or region's research prose is filed under.
CREATE TABLE "note_aspect" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "applies_to" TEXT NOT NULL CHECK ("applies_to" IN ('place', 'region', 'both')),
  "about" TEXT NOT NULL
);

CREATE TABLE "water_kind" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "flows" BOOLEAN NOT NULL CHECK ("flows" IN (0, 1)),
  "about" TEXT NOT NULL
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

-- Every cell inside the regions (the province and its seas).
CREATE TABLE "cell" (
  "x" INTEGER NOT NULL,
  "y" INTEGER NOT NULL,
  "region_id" TEXT NOT NULL REFERENCES "region"("id"),
  "land_share" REAL NOT NULL,            -- share of the cell that is dry land on the map
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

-- Each connected body of water on the map, with its default kind (the owner may set kind and flow later).
CREATE TABLE "water_body" (
  "id" TEXT NOT NULL PRIMARY KEY,
  "water_kind_id" TEXT NOT NULL REFERENCES "water_kind"("id"),
  "name" TEXT,
  "area_m2" REAL NOT NULL,
  "label_px" REAL NOT NULL,              -- a point inside it
  "label_py" REAL NOT NULL,
  "flows" BOOLEAN NOT NULL CHECK ("flows" IN (0, 1)),
  "flow_toward_deg" REAL,                -- the way it flows (0 north, clockwise), when it flows
  "flow_note" TEXT,
  "set_by" TEXT NOT NULL CHECK ("set_by" IN ('derived', 'owner')),
  "why" TEXT NOT NULL
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
