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
