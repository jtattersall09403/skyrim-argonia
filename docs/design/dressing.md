# Regional dressing: ground colour and small signature things

Each region reads as its own place at the player's feet: its own flower colour in the grass, and small things found
there and nowhere next door. Both change records only: no terrain, tree, scatter-placement or LOD rebuild.

## Ground-cover colour

1. **Census.** `python -m tools.newworld.dressing.grass_census` reads every grass (GRAS) the New World load order
   offers (Skyrim, Update, the DLC, Black Marsh, Valenwood, King of the Murkmire, Depths of Skyrim, Tropical
   Skyrim; last wins), resolves its mesh and textures as the game does (the assets audit's resolver) and measures
   its diffuse texture's opaque pixels: the share of each hue family among saturated pixels, and white. A grass is a
   flower grass when one family passes its floor (yellow, white and orange 5%, since dry grass tips are pale and
   warm; violet, blue, pink and red 1.2%). Output: `out/newworld/dressing/grass_census.json`.
2. **The colour.** Each land region's colour is its identity sheet's `ground.family`
   (`newworld/sources/identity/regions.json`, grounded in the region's look notes).
3. **The palette.** In `tools/newworld/world/texture.py`, each region's own grass lists (`REGIONS[...]["grass"]`,
   on `meadow`, `marsh_grass`, `forest_floor`, and `rainforest`, `moss` or `rock_grass` where the region shows
   them) carry its colour's flower grass on every grassy material, beside its own leaf grasses. A flower grass is
   listed in one region only; the province lists carry leaf grasses only. The base lists of the shore, edge and
   underwater materials stay one list everywhere, by water kind and habitat, as Skyrim's do.
4. **What keeps it Skyrim-like.** Only the lists change: the materials, their blend, the swathe and hard-edge
   rules of the ground paint (walk-5 ground research) and each grass record's own density are untouched.
5. **The check.** `python -m tools.newworld.dressing.ground_colour`: no flower grass in two regions; a region's
   flower grasses are of its sheet's family; a sheet family the load order has a free flower grass for is met;
   neighbouring regions (`newworld/sources/identity/adjacency.json`) never show the same flower colour; the share of
   palette grass types two neighbours have in common is at most 0.5. A family no complete land grass carries is
   listed as unmet: the sourcing gap to close with a grass mod.

## Small signature things

1. **The kinds.** `newworld/sources/dressing/kinds.json`: each kind's regions (one or two, never neighbours), its
   bases (`plugin:edid` from the held mods), its dressing habitat, its Skyrim sort and its rate. Each kind cites the
   identity sheet's `signature.thing` it delivers or the lore line it rests on.
2. **Which bases.** A base is in the load order, every mesh and texture resolves, it has no distant LOD, and it is
   small (bounds half-extent at most 160 units) or an effect or spawner (MSTT, ACTI) a player walks through: nothing
   the navmesh must cut round, nothing seen from afar.
3. **How many.** A kind's rate is references per 100 cells where its habitat holds ground, at most Skyrim's own
   outdoor rate for the same sort (`python -m tools.newworld.dressing.measure`, Skyrim.esm's Tamriel cells:
   `newworld/sources/dressing/skyrim_measures.json`); a cell holds at most six. A find, not a carpet.
4. **Where.** By hyperlocal habitat on the ecology stage's cell view: canopy, forest (near placed understorey),
   open, rock, slope (15 to 35 degrees), marsh, reeds (near placed reeds and ferns, or marsh), shore (within 12 m of
   water). Never on a road, in water, in a built place's held cells or a landing's cell.
5. **Ids and bytes.** Each reference's id is the `dressing` idspace row's first id plus the digest of its identity
   (cell, kind, ordinal), probed on a collision; every draw is seeded by cell and kind, so a rerun writes the same
   bytes.
6. **The stage.** `dressing` runs after the navmesh and before `esm`, writes `out/newworld/plugin/dressing/`
   (`cy<+NNN>.jsonl`, `manifest.json`, `check.json`) beside `refs/`, and is read only by `esm` as plain REFR.
   `python -m tools.newworld.dressing.place check` judges the kinds and the placement.
