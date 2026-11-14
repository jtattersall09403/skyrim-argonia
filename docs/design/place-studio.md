# Places: source, draft, studio, build

How a place of the new world is built: seeded on a source place, drafted by an agent, edited by the owner in the
studio, and built into the place layer. One pipeline for every place; a place is a row, never a special case.
The phase is [nw-03](../phases/new-worldspace-plan/nw-03-build-helstrom.md); the rulings are in
[owner-rulings](../owner-rulings.md) (2026-11-09).

## The pipeline

```
source plugin ──extract──▶ source bundle ─┐
world ESM ─────extract──▶ ground bundle ──┼─draft──▶ place files ──build──▶ place layer ESP + checks
                                          │            ▲
                              studio (browser) ──edits─┘  save / load / finalise ──▶ lessons into the skill
```

| Part | Where | Does |
|---|---|---|
| Extract | `tools/ArgoniaPlaces/Extract` (C#, Mutagen), `python -m tools.places extract` | Reads a place out of any plugin into a bundle; reads our own ground the same way |
| Assets | `tools/places/assets` | Mesh and texture conversion for the browser, on demand, cached; the asset catalogue |
| Search | `tools/places/search` | Embedding index over the catalogue |
| Draft | `tools/places/draft`, skill `place-build` | Source bundle + our ground → place files |
| People | `tools/places/identities.py`, skill `place-people` | Who each placed person is: the people source (Stock, below) |
| Stock | `tools/places/stock`, `tools/newworld/stockdb.py`, skill `place-stock` | The split, the derive; people, goods and contents as database sources (Stock, below) |
| Build | `tools/ArgoniaPlaces/Build` (C#, Mutagen), `python -m tools.places build` | Place files and the database's stock → `out/places/plugin/ArgoniaNWPlaces.esp`, navmesh, checks |
| Studio | `tools/places/studio` (server, Python), `tools/places/studio/web` (front end) | The owner's editor |
| Finalise | `python -m tools.places finalise`, skill `place-lessons` | Edits → place files → build → lessons → report |

`python -m tools.places <verb> <place_id>` is the one entry point; every verb is rerunnable and skips work whose
key (inputs' hashes) matches a stamp it wrote itself.

## Identity

- `place_id`: the id in `newworld/story/data/db/place.jsonl` (`helstrom`).
- `source_id`: `<mod>.<name>` (`bmv.helstrom`). A source is declared in `newworld/places/sources.jsonl`:
  `{source_id, title, plugins:[...], extra_refs_plugins:[...], worldspace: "<Plugin>:<hex>" | editor id,
  cells:[[cx,cy]...] | areas:[{x,y,r}] | location: editor id or key | marker: ref key + radius, follow_doors,
  extent_m:[east-west, north-south], parts:[{name, cells, size_m, centre, notes}], notes}`. The extent is any union of
  cells, circles (game units), a location's cells and a marker's radius; `extent_m` and `parts` are measured from the
  plugin (the built area: buildings, doors, furniture, containers, actors). Plugins are found in the game's Data,
  the staged mods (MO2 priority order), the asset mods and `out/newworld/plugin`; their masters load with them. A new
  source in any plugin is a row, never a code change.
- A place's allocation is `newworld/places/<place_id>/place.json`:
  `{place_id, source_id, similar:[source_id...], ...}`. nw-04 fills these for every place; the tools read them
  and nothing else.
- Base forms are keyed `"<Plugin file>:<6-hex local form id>"` (`Black Marsh.esm:0D794B`). Placed refs of a
  source use the same key shape. Our own placed things have ids we mint (`<place_id>.<ulid>`), stable for life.

## Units and axes

Everything on disk and over the API is in Skyrim's own terms: game units (70 to the metre), Z up, +Y north,
positions absolute in the worldspace, rotations as the record's three angles in radians, scale as the record's
float. Each angle is a clockwise turn about its axis seen from the axis' positive end (a Z angle is a compass
heading: 0 faces +Y, pi/2 faces +X), and the rotation is `R = Rx(-x) . Ry(-y) . Rz(-z)` (Rk the usual
counter-clockwise rotations, column vectors): world = pos + scale * R . model. One shared function pair (Python
`tools/places/xform.py`, JavaScript `web/xform.js`, the same test vectors `tools/places/xform_vectors.json`) turns a
record's position, angles and scale into a matrix and back; nothing else does that maths. `python -m tools.places
xform prove <bundle_id>` proves the convention on a bundle's real data (slope-conformed refs against the land's
normal; door teleport markers against their doors). The browser converts to its own axes only at render time.

## Bundles (derived, never committed)

A bundle is one place as data, in `out/places/bundles/<bundle_id>/`; `bundle_id` is `src.<source_id>`,
`ground.<place_id>` or `draft.<place_id>` (the place files resolved for viewing). The studio shows any bundle.

The draft bundle is written by `python -m tools.places draft_bundle <place_id>` (`tools/places/draft_bundle.py`):
the exterior's refs as written; each interior the source cell's refs without actors, cut to the room the build keeps
(`tools.places.build.room_partition`, the one copy of the room rule), with our rows over them; people, paths, clear and land files as written;
every base a ref uses, from the source bundle (then the ground's), else the catalogue, and any in neither listed
as `stamp.missing_bases`; actor bases from the source. It is built from the place as committed (a
snapshot of `HEAD:newworld/places/<id>` in `out/places/snapshots/`), never the working tree, and swapped in by
one atomic rename of the `draft.<id>` symlink. Its `stamp.key` is a sha256 over that path's git tree id and the source and ground bundles' `bundle.json`. The studio rebuilds it whenever that key
is stale (a commit to the place, or a new source or ground bundle), on `GET /api/places` and on a request for the draft's `bundle.json`, so a redraft, a re-seat or a
finalise shows without a command. Unknown fields pass through.

```
bundle.json            {bundle_id, kind: source|ground|draft, title, plugins (every plugin loaded, masters first),
                        source_plugins, worldspace, worldspace_edid, anchor:[x,y,z], cells:[[cx,cy]...],
                        spaces:[space_id...], not_followed:[{space, reached_from, exits}], counts:{...},
                        stamp:{key, inputs:{plugin file:sha256}, tool, at}}; a ground bundle adds
                        esm:{file, sha256}, place:{id, world_x, world_y}, radius_m
bases.jsonl            every base form the bundle's refs use (below)
npcs.jsonl             every actor base the bundle places (below)
spaces/<space_id>/     space_id: "exterior" or an interior cell's editor id
  space.json           {space_id, type: exterior|interior, name, cells, water:{default_height, type}, light, owner,
                        refs, doors}; an exterior adds groundcover:{placed_refs, generated_from_land_textures, note}
                        (Skyrim grows grass from the land textures' grass lists; it is not placed as refs) and
                        sky:{climate, edid, SunriseBegin, SunriseEnd, SunsetBegin, SunsetEnd, weathers:[{key, edid,
                        plugin, chance, SkyUpperColor, SkyLowerColor, HorizonColor, FogNearColor, FogFarColor,
                        AmbientColor, SunlightColor, SunColor, EffectLightingColor (each {Sunrise, Day, Sunset,
                        Night}), DirectionalAmbientLightingColors ({Sunrise, Day, Sunset, Night} of the six
                        directional ambient colours), FogDistanceDay|NightNear|Far|Power|Max, Flags}]} (the
                        worldspace's climate and the lighting fields of each of its weathers, for the night views);
                        an interior adds key, plugin, lighting_template, lighting_template_light (the template's
                        lighting: the fields `light.Inherits` names come from it), flags. A colour the extractor
                        writes from a record is its three bytes in base64
  terrain.json + terrain.f32   exterior only. terrain.json: {cells:[{cell:[cx,cy], key, edid, plugin,
                        water:{height, type} | null, regions, heights_index, layers, vertex_colours}],
                        ltex:{key:{edid, plugin, diffuse, normal, grasses:[{key, edid, model, density, min_slope, max_slope,
                        units_from_water, units_from_water_type, position_range, height_range, color_range,
                        wave_period, vertex_lighting, uniform_scaling, fit_to_slope}]}}} (each GRAS record's own fields).
                        terrain.f32: per cell at heights_index, 33x33 float32 world Z, row-major south to north,
                        west to east, 128 units apart. layers: per quadrant its base {quad, layer:-1, tex}, then alpha
                        layers {quad, layer:n, tex, alpha: base64 of 17x17 opacity bytes, row-major south to north}.
                        vertex_colours: base64 of 33x33 RGB bytes, same order
  refs.jsonl           one placed ref per line (below)
  navmesh.jsonl        one navmesh per line: {id, cell, verts:[[x,y,z]], tris:[[a,b,c,flags,cover]],
                        tri_edges:[[e01,e12,e20]] (an index into edge_links when the edge's flag is set, else the
                        neighbouring triangle), edge_links:[{mesh, tri}], door_links:[{tri, door}]}
```

Files are plain JSON and JSONL; a reader takes `<name>.gz` in place of any `.jsonl` (`tools/places/bundle.py`, the
reader every lane imports: `Bundle(id).space("exterior").terrain.height_at(x, y)`). The studio serves them
compressed over HTTP.

A ref: `{id, edid?, base, kind, pos:[x,y,z], rot:[rx,ry,rz], scale, layer, flags:[...], door:{to_space,to_ref,to_pos,
to_rot,flags}?, owner:{owner,rank}?, linked:[{ref,keyword}]?, enable_parent:{ref,flags}?, lock:{level,key,flags}?,
src?, cell?, map_marker?, primitive?, radius?, light_data:{fov,fade,end_cap,shadow_bias}?, emittance?,
loc_ref_types?, count?, patrol?, persistent_location?, merchant_container?, scripts?, activate_parents?, name?}`. A
place row's `name` is the name the game shows on looking at the thing, where the place names it (a container only:
the build's stock copy of its base carries the name, below). `primitive` is
the ref's XPRM, the shape a collision marker, a trigger, a room marker or an acoustic space has: `{type: Box | Sphere |
Plane | Line | Ellipsoid, bounds: [x, y, z] half extents round the ref's origin in its own frame (xEdit shows them
doubled), color: [r, g, b], unknown}`; `scripts` the names of the ref's own scripts (VMAD) and `activate_parents` the
refs whose activation it follows (XAPD). `light_data` is a light ref's own
offsets to its base (XLIG) and `emittance` the region or light whose colour a ref glows with (XEMI: a window that
follows the time of day). In a bundle `src` is the plugin whose version of the ref wins and `cell` the exterior cell;
flags are `persistent, initially_disabled, visible_when_distant, high_priority_lod, multibound, no_respawn,
open_by_default, ignored_by_sandbox`.
`kind` is one of `building, static, clutter, tree, plant, groundcover, rock, furniture, door, container, light,
activator, marker, actor, water, other` and is decided once, in the extractor, from the record type and the
model. `layer` is `world` (the generated world's own refs: plants, rocks, scatter) or `place`.

A base: `{key, edid, type, kind, name, model, bounds:[min,max], plugin, keywords:[...], nordic: bool, door:{},
furniture:{markers}, light:{radius, colour, flags, fov, fade, falloff}, container:{}, tree:{}, flora:{}, water?}`. `model` is the path under
`meshes/`, lower case; `plugin` is the plugin whose version of the base wins. `nordic` (decision 0006) is true when
the model path or editor id names a Nordic culture, hold town or Nordic dungeon kit (nord, draugr, barrow,
Whiterun, Windhelm, Riften, Solitude, Markarth, farmhouse and the like) and not a non-Nordic kit (Dwemer, Dunmer,
Imperial, Ayleid, Falmer), whatever plugin carries it, or when it is architecture from Skyrim's own masters outside
those kits.

`nordic` judges only what we add from elsewhere. A piece the source place itself uses, from its own mods, Tropical
Skyrim or the base game, is accepted as it comes. The drafter reads `nordic` false on every base of the source
bundle (`io.place_bases`). The build's `nordic` check passes a ref whose base the source bundle holds. For a
base we add (a station, a replacement, a laid piece) the folder rule is a first sort, not a look: a pile of leaves
from Riften's folder is not a Nordic element. The verdict, once such a base has been looked at, is
`newworld/places/nordic_review.jsonl`, one row per base: `{base (key), edid, model, verdict: "nordic"|"neutral",
why (one line: what it looks like)}`. A reviewed verdict outranks the folder rule in the drafter, `draft check` and
the build's check; an unreviewed base keeps the folder rule. The wide search marks Nordic bases by the same rule.

The catalogue's `lights.jsonl` holds every light base of the load order, with or without a model: `{key, edid,
model, plugin, light:{radius, colour, flags, fov}}`. The drafter reads it for the lights of added stations.

## Place files (ours, committed): `newworld/places/<place_id>/`

The source of truth for a built place. Rows carry our own decisions (where, which way, who) and point at the
source for everything copied; no record or asset content of a mod is written here.

```
place.json             allocation, the fit (how the source's frame maps onto ours, per cluster), the ground stamp
                       the draft was seated on, the build key
spaces/<space_id>/refs.jsonl     the place layer's refs, same row shape as a bundle ref, plus
                       seat:{mode, dz, on?} (how it sits: on ground, on a ref, at source's height above ground,
                       in water, free) and src (the source ref it came from, if any). A light is seated `on` its
                       fixture (the lantern, sconce, window or fire within 128 units of it in the source) and
                       stands at its source offset from it. A copied room's lights stand on the bases the source
                       placed, shadow casters among them (no cap on shadow-casting lights in a room)
spaces/<space_id>/space.json     interiors: {copy_of: "<source_id>/<space_id>", name}; the refs file holds only our
                       changes to the copy (moved, removed, added). `name` is what the game shows on the room's door
                       and inside it (the cell's name); the stage `names` gives it (Room names, below)
clear.jsonl            world plants and scatter switched off: {base, pos, by: draft|owner}; matched to the world's
                       ref at build by base and nearest position, so a world rebuild re-applies it
land.jsonl             land patches: {cell, verts:[[row,col,dz]...], textures?, why}; the last resort, only to ease
                       the ground under a building: |dz| <= place.json fit.patch_max (1.5 m), never across the waterline
paths.jsonl            streets, paths and walkways: {id, kind: path|street|walkway, points:[[x,y]...], width, style,
                       from?, to?, laid?}; style is a land texture key (the source place's own road texture) or the
                       draft's style word (dirt, boardwalk). The points are the line as walked: routed on our ground
                       and decks and eased into a curve, so a walkway's line runs along its decks, and every point of
                       the line on the built place's main walkable network, at its own level (over a walkway piece
                       the deck's own triangles; the drafter re-lays a stretch off it along the built navmesh; `laid`
                       then says so); a guard's patrol points lie on it too; `from` and `to`
                       name the doors (source ids), `landing` or `camp.<cluster>` a drafted link joins. The studio
                       draws a person's way between two stops outside by the same rules (round buildings, never
                       through open water, along these lines where one leads the right way)
people.jsonl           one person per line: {id, name, base_from, role, home, bed, work, services, faction_ranks,
                       routine:[{start, hours, kind, at, days?}], patrol?: {points:[[x,y] | stop...], loop}}.
                       A stop (`at`, `bed`, `work`, a patrol point) is {space, ref | pos, radius}: `ref` our id or a
                       source key of that space; `pos` [x,y] (outside only: seated on the built land) or [x,y,z]; neither: the
                       space's arrival point (where its load door lands one), else its first furniture. `bed` a stop or null; `kind` sleep|work|wander|sandbox|eat|patrol (a
                       patrol stop's route is `patrol`). services: [{seq, kind | give_kind_id, detail, destinations?,
                       skill?, level?, room_bed?}]: kind and detail the record's give at seq, destinations (a travel
                       stop) the network's places by that mode, nearest first; `draft people` re-reads them and the
                       `services` check compares them; a travel stop's operator is the mode's role (boatman for a
                       boat stop, carter for a coach stop, a resident for a rootworm stop); faction_ranks: [{faction: a form key or <place_id>.<name>, rank}]. Any other
                       shape is a problem `build --plan` lists, never a crash
                       Who each person is (name, household, trade, wealth, notes) is not placement: it lives in the
                       database's people source under the same id (Stock, below); the drafter writes each person's
                       name from it onto this row
ledger.jsonl           one row per source ref: {src, space, status: placed|adapted|replaced|dropped, as?, why?,
                       cluster?, patch?}; every source ref has one
edits/<save_id>.json   a studio save (below); finalised saves stay here as the lessons' evidence
```

Seat rule `seat:{mode, dz, on?, carrier?, foot?}` (one function, `tools/places/seat.py`): `ground` z = lowest ground under
the footprint + dz; `clear` z = highest ground under the footprint + dz (a raised thing whose underside cleared the
ground everywhere); `above` z = ground at the origin + dz; `water` z = water surface + dz; `stilts` z = lowest of
max(ground, water) under the footprint + dz; `on` z = the ref `on`'s z + dz; `free` z kept (interiors). `foot` is
the true footprint `[x0, y0, x1, y1]` in the ref's own frame (not centred on the origin), from the model's own
geometry (`seat.model_bounds`, cached in `out/places/footprints.json`); every footprint test calls it. dz is
measured in the source the same way. A ref rests on what its seat names: the ref it stands `on` (a barrel on a
deck, a flight of steps hung on its pier, a walkway piece on the one it continues) and its `carrier` (the ship
whose gangway a laid walkway piece is; the seat's mode is then `free`). A flight of steps is seated `on` the deck
piece it leaves, its top tread at the deck's height.

`place.json` also holds: `draft` (the agent's calls: `anchor`, `rot_deg`, `search`, `replace`, `drop`, `add`,
`roles`, `keep_patches`, `room_names`; skill `place-build`), `fit` (global and per-cluster transforms, `clusters_info`,
`relief_norm`, `patch_max`),
`clearance` (the source's measured clearance), `factions` (`<place_id>.crime`, `.guard`, `.town`, and one
`.vendor.NN` per trader with hours and `chest`; the crime row's `law` is the place's law (native, foreign or
none, from the database's `place_law`) and `law_why` its reason; its `jail` (foreign law) is null where there is none,
else `{space, known, cell, bed, door, marker, exterior, stolen, inventory}`: the jail room, how it was known, how the
cell was chosen, the prisoner's bed and the cell's locking door (a source key or our id; null where it has none), and
our ids of the jail marker, the exterior prison marker and the two evidence chests; its `owing` (native law) is null
where there is none, else `{work, return, bed, stolen, work_at}`: our ids of the work spot's and the return spot's
prison markers, the worker's bedroll and the stolen goods chest, and where the work is done; both written by `draft
jail`), `stations` (needed, found, missing, added: {station, id, base,
space, by}), `ground`, `source`,
`radius_m`, `counts`, `draft_key`.

An interior copy brings every ref of the source space except actors. Its `space.json` adds `door_from` (our door
that leads in), `parent` and `room`: when the source packs several rooms into one cell, the source door of this
copy's own room (its beds are the ones nearer that door than any other way out). Its `refs.jsonl` rows carry `src`
(the source ref they override, by its source id); refs not listed are copied unchanged. A person's `bed` and
routine `at` name a copied ref by its source id with the copy's `space`; a row with no `src` in a copy is an
addition (a station). `clear.jsonl` rows add `why` and `ref`. A ref the draft added (station, bridge) has `src`
null and a `why`; a replaced door or directional piece carries `align: {turn_deg, shift, of}` (already applied
to its pos and rot; the record of how its plane was matched to the original's; a replaced load door is also
turned so its front, read from its mesh, faces its arrival). A walkway piece (dock, boardwalk, bridge, steps)
carries `walk`, the height of its deck over its origin (the top of its collision at its centre): one standing at
that height stands on it, not in it, for the drafter and for `check`. A person in an innkeeper's role
has `bed` null and one 24-hour work stop (Skyrim's innkeepers keep no bed). An exterior door into a copy
carries `door.arrival` [x, y, z], where one stands outside it on our ground, clear of collision; the copy's way
out (its `door_back` row) has `to_pos` that arrival and `to_rot` facing away from the door. A copy of a shared
cell overrides only its own way out and removes the other rooms' ways out that fall in its kept room.

**Things added by hand** (`draft.add`, `tools/places/draft/adds.py`): `[{base, pos: [x, y] | [x, y, z], space?, rot_z?,
scale?, kind?, dz?, name?, need?, tier?, why}]`. Outside (no `space`) a thing is seated `ground` on its true
footprint; in a room (`space` a room's id) it stands `free` where `pos` puts it, its height measured off the
floor-standing piece beside it. Its row carries `name`, `need` (the seq of the story need it meets) and `tier` as
given; its id is minted from its place in the list and its base. The whole draft places them; `draft add <place>`
places them again on a drafted place.

**Room names** (`tools/places/draft/names.py`, stage `names`). A room's `name` says what it is, from what the place
data holds, first rule that gives one: the agent's call in `draft.room_names` `{space: {name, why}}`; the place a
promise of the record names (a detail beginning "the ..."), where that promise is kept in the room (a station of it
stands there, or its giver works there): "the tree-minders' hall" names the room its enchanter stands in
"Tree-Minders' Hall"; the household that lives there, by its head, as Skyrim names its homes ("Ixtul-Bei's House");
the source's own name unless it is a builder's leftover (a test cell, an editor id). A room an owner's save created
keeps the owner's name. `draft check` fails a room with no name or a leftover name and, once the place's people have
identities, two rooms with one name.

Seating is data, never baked: `pos[2]` is what the last seating wrote, and `python -m tools.places seat` rewrites
it from `seat` and the ground bundle. A ground rebuild is followed by `seat`, `build`, nothing else.

## Stock: people, goods and what a place holds

Building a place includes what is in it (nw-03, Stocking). Nothing is random and nothing is levelled (decision 0035).
Set dressing (food, crockery, cheap clutter, furniture) stays as the source has it. Everything significant is
authored, each thing with its reason; what the source held of that kind is taken out. The order of work on a place
is the one the skill `place-build` states at its top: research (`place-research`), the draft (`place-build`), who
each person is (`place-people`), what the place holds (`place-stock`), build and check (`place-build`), the owner's
studio edits, and finalise (`place-lessons`). Stocking runs after `place-people` has given every placed person an
identity.

**Where each fact lives.** World facts live in the new world's database, built from source files the way places and
regions are. Placement lives in the place files. Each fact has one home:

| Fact | Its home (source of truth) | Tables |
|---|---|---|
| The scale: tiers, materials, gold, locks, security, effort, wealth bands, budgets, traders' gold, the split | `newworld/sources/stock/scale.json` | `stock_tier`, `tier_material`, `tier_item`, `lock_level`, `security_level`, `effort_level`, `place_wealth_band`, `person_wealth_band`, `container_kind`, `item_kind`, `never_material` |
| A place's wealth: derived figure, band, ceiling, reason, the owner's overrule | `newworld/sources/stock/place_wealth.json` (`python3 -m tools.newworld.wealth derive` rewrites the derived part; `owner` is kept) | `place_wealth` |
| The item forms stocking names | `newworld/sources/stock/items.json` (generated: `python3 -m tools.newworld.stockdb items`) | `item` |
| Goods, and what each place makes, trades and needs | `newworld/sources/stock/goods.json`; a place's own in its stock source `goods` | `good`, `good_material`, `place_good` |
| Who each person is: name, sex, race, culture, household, role, trade, wealth, level, status, notes, ties, factions | `newworld/sources/people/<place_id>.json` (lookups in `people/lookups.json`) | `race`, `person_role`, `household_role`, `relation_kind`, `household`, `person`, `person_note`, `person_note_source`, `person_relation`, `person_faction` |
| What holds what: containers, loose things, possessions, traders' lists; the deliveries stocking owns | `newworld/sources/stock/places/<place_id>.json` | `stock_container`, `stock_container_item`, `stock_container_source`, `stock_loose`, `person_item`, `trader`, `trader_item`, `trader_source`, `give_delivery` |
| The exceptional: uniques and every T6 thing, counted game-wide | `newworld/sources/stock/unique.json` | `unique_item` |
| Where a person sleeps, works and walks; the refs, rooms, stations | the place files (`people.jsonl`, `spaces/`, `place.json`) | none: the build reads them |

`python3 -m tools.newworld.build_db` loads everything. `python3 -m tools.newworld.stockdb load` rewrites these tables
alone from their sources (a whole build needs the map's extraction). Every column is described in
`newworld/story/data/schema.sql`. A person id and a ref id are the place files' own (`<place_id>.<ulid>`, or a copied room's source key), so a
row in the database and a row in the place files name the same thing. A person's `role` is held in both: the
people source is its home. `people.jsonl` holds the drafter's copy, and `identities check` confirms the two are equal.

**The people source** `newworld/sources/people/<place_id>.json`: `{place_id, households: [{id, home_space, name}],
people: [{id, name, sex, race (RACE editor id), culture_id, household: {id, role}, role, trade, wealth: W1..W5, level
(fixed, or null until set), status: alive|dead|missing, tier (statement tier), notes: [{aspect: backstory|personality|
secrets|relationships, text, tier, cites: [...]}], relations: [{to, kind}], factions: [{faction, rank}]}]}`. A cite
is a repo path or a database row: `place_note:<place>/<aspect>`, `place_give:<place>/<seq>`, `culture:<id>`,
`region:<id>`; each becomes a `source` row (`cite-...`). `guard_body` is the place's own name for its watch, one of
the lookups' `guard_body` ids, chosen from the record's `held_by` ("levy" where a tribal levy keeps the guard).
`python -m tools.places identities check <place>` proves a person per placed person, names unique in the new world
(never a name another place's people source, the story's roster or a BM&V talker gives) and by the naming rules, one
household per roof with one head, every guard's trade naming the place's guard body, every cite existing and roles
equal to `people.jsonl`'s. `tools.places.identities.read` gives the drafter
each person's name.

**The stock source** `newworld/sources/stock/places/<place_id>.json`:

```
{place_id,
 goods:       [{good, relation: makes|trades|needs, why, tier, cites}],
 containers:  [{ref, space, kind (container_kind), owner_person? | owner_household? | owner_faction?, lock? (lock_level),
                security (S0..S5), effort? (E0..E4, wild ground), tier (T1..T6), gold, items: [{item, count, why}],
                why, cites}],
 loose:       [{id, space, on? (the ref it lies on) | pos: [x, y, z], item, count, owner_person? | owner_faction?,
                effort?, why}],
 possessions: [{person, items: [{item, count, worn, why}], why}],
 traders:     [{person, give_seq, gold, items: [{item, count, why}], why, cites}],
 deliveries:  [{give_seq, by: person|container|loose|ref|record, person? | ref?, status: delivered|open|dropped, why}],
 removed:     [{space, ref, edid, why}]}
```

`item` is an item id, `"<plugin>:<6 hex>"` (an `item` row: run `stockdb items` after naming a new one). At most one
owner per holder. A `ref` names a container the way the place files do: our id outside, the source key in a copied
room. A loose row whose `id` is a ref of the place keeps that ref where the place files stand it (no `on`, no `pos`);
any other `id` is a new thing (`<place_id>.<ulid>`, minted once) at `pos` or on the top of the container `on`.
`owner_faction` is a household id (that household's faction), `<place_id>.<name>` (the place's faction of that name,
as `people.jsonl` names it: `town`, `guard`) or a faction's form key. `removed` records each significant loose ref of
the source the stocker decided not to keep, with the reason; the build leaves out every significant loose ref with no
row whether or not it is listed. `respawn` is never stored: an authored container never respawns, and a trader's merchant chest
restocks every 48 hours to its list (vanilla's own timing; the list is fixed and nothing in it is levelled).
`deliveries` holds only what stocking owns (loot, a treasure, a record edit); the loader adds the rest:
a person whose `people.jsonl` services name the give (a travel stop's operator among them), a station of
`place.json` `stations.found`. Anything else stays `open`; a stop whose operator is known but not yet placed is an
`open` row `by: person` naming them, so the place files' owner knows whom to give the service. `python3 -m tools.newworld.stockdb promises <place>` lists
each promise and what delivers it, and exits 1 while any is open. A promise is dropped only by editing the place
record, with the reason (`status: dropped`, `why` naming the edit), never to avoid the work.

**The scale** (`scale.json`, with its reasons): one fixed ladder T1 Common .. T5 Precious, and T6 Exceptional, which
is entered only in the ledger. Each tier lists its weapon and armour materials, enchantment grade, soul gem, gems, jewellery,
potion grade, gold range, lock and the most its container may hold (`value_max`). The tiers are checked against
vanilla's level gates (`docs/research/skyrim/stocking-yields.md`). How a place's band is set:
- Wild ground: the place's reward band (`place_danger`, docs/design/danger.md) sets the tier (`danger_tier`: D0
  and D1 T1 .. D5 T5). The hardest spot holds the band's tier and the way to it the tier below (`effort`).
- A peopled place: its wealth (`place_wealth`) sets a ceiling (P1 T1 .. P5 T5). A friendly or wary place holds its
  people's own goods, so its wealth alone sets it, as a city's does; a hostile lived place's ceiling is never below
  its reward band's tier (`scale.json` `ceiling_why`).
  What lies open is T1. Each tier above the open tier needs one more step of `security`, and a container's lock is
  its best tier's `lock`.
- A person: their wealth band W1..W5 sets the gold they carry and keep, their clothes, their jewellery and their best
  tier (W5 reaches the place's ceiling). A guard carries the guard faction's issue whatever their band
  (`guard_issue`): their own culture's guard set where the place's mods provide one (the set's plugin is one of the
  source's plugins) and the place's ceiling reaches the set's tier (BM&V's Argonian guard armour, T3, for a
  Black Marsh place of ceiling T3 or more), with the set's weapon where the source's guards carried one; else the
  plain issue at the `owner` faction's `issue_tier` (sound gear, T2). Every guard also carries one plain torch
  (`guard_issue.torch`, Skyrim.esm 01D4EC, never a levelled list), as Skyrim's guards do; the guard packages
  (copies of vanilla guard packages, their flags unchanged) let them carry it lit at night.
- An owner sets a container: a person or household by their band, a faction (guard, town, temple) by the place's
  band, nobody by the ground.
- Provenance: a thing made here (the place `makes` a good whose `good_material` covers it) is common and costs its
  value. Carried in, it costs `cost` times its value against the holder's budget and comes in `count` times the
  number, by road distance to the nearest maker or import gate.
- Budget: a container's significant things together stay within its tier's `value_max` times its owner's share.
- Never: a `never_material` or a Skyrim-only kit (decision 0006).

**The split.** `python -m tools.places stock classify <place>` sorts every container, loose item and person's item
of the draft bundle into set dressing or significant, from record data only (scale.json `split`), and prints what it
catches before anything is taken out. A container is significant when its kind always is (chest, strongbox, safe,
corpse, boss or merchant chest), when it is locked, or when it holds a significant thing. A container's and a
person's levelled contents are read at level 1, as the build flattens them.

**The derive.** `python -m tools.places stock derive <place> --to <path>` writes a first stock source with a reason
on every row: a store per household (its best-kept container) by the head's band and the household's size, a
body's few things, each person's tool or weapon, the levy's gear, jewellery and carried gold by band, each trader's
gold and a list from T1 to the ceiling within the band's list value. It also writes what is taken out and what it
leaves open. The stocker reads it, corrects it and completes it by hand into the stock source.

**What the build makes of it** (`tools/places/stock/plan.py`, called by `build.py` after the people and before the
navmesh; the records by `ArgoniaPlaces/Build` `Stock.cs` and `People.cs`). A place with no stock source is built as
before. Every list is read at level 1 the way the writer flattens one (`Records.fixed`: the level-1 entries, every
one when the list gives all, else the first).
A placed container whose row carries a `name` is always copied, under that name, holding its stock row's items and
gold alone (a new thing keeps none of its base's contents); a `name` on any other ref is a problem.
1. A `stock_container` row: the placed ref's base becomes a container of ours (a copy of its base, `ANP_<place>_StockNNN`)
   holding the base's own set dressing plus exactly the row's items and gold, never respawning. The ref gets the row's
   lock (its level, no key) or none, and its owner: the person's actor base, a household faction of ours (`<household
   id> household`, every member at rank 0), or the named faction. A container the split calls significant with no
   row becomes a copy holding its set dressing alone. A row that names no container of the place is a problem.
2. A `stock_loose` row: a kept ref keeps its place with the row's owner and count; a new one is a placed ref of the item
   at `pos`, or on the named container's top (its record bounds). A significant loose ref of the place with no row is
   not built.
3. `person_item` rows: our actor base carries exactly the non-worn rows plus the base's own set dressing, and wears an
   outfit of ours (`<npc>_StockOutfit`): the worn rows, then the base outfit's set dressing in the biped slots the
   worn rows leave free. A death item that would give a significant thing is cleared; an inventory template flag is
   cleared so the base's own list is the one the game reads. Nothing of the base's significant inventory or outfit
   stays. When a person's source outfit loses its only body piece (armour, or an enchanted garment), the stocker gives
   a worn garment of set dressing in its place.
4. A `trader` row: the vendor's merchant chest of ours holds exactly `trader_item` and `gold`, restocking to it. A
   trader with no row keeps vanilla's chest at level 1 (a note); a row whose person has no trader service is a problem.
5. `unique_item` rows stand in their holder's stock row, like any other item.
6. Nothing levelled anywhere (decision 0035).
Beside the plugin the writer leaves `<esp>.copies.json` (each record of ours copied from a plugin that is not a
master, and its source key), so the check reads a copied item as its source record.

**What the build check proves** (`tools/places/stock/verify.py`, run by `check` as its checks `stock` and
`promises` on a stocked place), on the built plugin read back (`dump` gives each container ref's contents and respawn
flag and each actor base's inventory, outfit items and death item):
1. Nothing levelled: a container, an actor's inventory, outfit or death item, a placed item (check `levelled`).
2. Every significant thing traces to a row. Each container ref, loose item ref, actor base and merchant chest of the
   place is split again, and its significant things must equal its holder's stock row (counts and gold included):
   a container with no row holds nothing significant. Any other significant item fails, by holder and item.
3. Every row is built: a container, loose, possession or trader row whose holder or items are missing fails.
4. Every promise delivered (`promises`): `give_delivery` has no `open` row for the place, each delivered row's person
   or ref exists in the build (a travel stop is proved by `services`: each route offered at its fare to its
   arrival point).
5. Quest things untouched: a ref or item a quest record names is in no stock row and stands as the quest has it (the
   quest tables of nw-05; none yet).
6. Ownership set: every row's built owner is its row's; only S0 rows and wild ground are nobody's.
7. Locks and value agree: the built lock equals the row's; a container's tier is at most its security's reach
   (`open tier + rank of security`); its significant value is within its budget (`value_max` of its tier times its
   owner's share: a person's band, a household's richest member's band, a faction or nobody 1.0); no item above its
   container's tier.
8. No respawn, except a trader's merchant chest, which must restock.
9. The ledger: a T6 or unique item has its `unique_item` row, and the game-wide counts are within `scale.json`
   `ledger.caps`.
10. Never: no item of a `never_material` or Skyrim-only kit.
11. Each person within their band: carried gold at most the band's `carried` top, jewellery at most its `jewellery`,
   no item above the band's `top_tier` (capped at the place's ceiling; a guard reaches the tier of the place's
   guard issue, `guard_issue`).
   Nothing anywhere above the place's ceiling but a ledger row.
`python -m tools.places stock report <place> [--out DIR]` prints the built place in numbers: containers authored,
items placed, the containers' value against their budgets, people's and loose value, gold, and the ten most valuable
things with who or what holds them.

**The studio** (lane S3; `tools/places/studio/stock.py`, the panels in `web/js/contents.js`, the pure part in
`web/js/stock.js`). It reads the database's sources, not the tables, so what it shows is the shape its ops carry:
- `GET /api/place/<id>/stock` returns `{place_id, facts, identities, stock, items, scale, lookups}`: `facts` the
  place's wealth as the database loads it (the owner's overrule first: `band`, `band_label`, `open_tier`,
  `ceiling_tier`, `why`, `by`); `identities` the people source whole; `stock` the stock source whole; `items`
  `{id: {edid, name, kind, record, value, tier, significant, never, measured, why_tier}}` for every item the stock
  names; `scale` the tiers, wealth bands, security, lock levels, effort and container kinds; `lookups` race, roles
  and relation kinds. An item `stockdb items` measured has its value and tier; one it has not (added in the studio)
  has its tier from its material keyword or the scale's tier lists, its value unknown until finalise measures it.
  Names come from the asset catalogue (`out/places/catalogue/bases.jsonl`, its item records).
- `GET /api/place/<id>/items?q=&kind=&limit=` (at most 60) finds items by name or editor id, best first. Each result
  is an item's facts plus `allowed` and `why`: an item on the never list or above the place's ceiling tier is
  listed with the reason it is refused, never hidden.

Selecting a container shows its kind, owner, lock, security, best tier, gold and reason, and each thing in it (count,
name, kind, value, tier, reason); a container with no stock row says whether it is set dressing or significant but
not stocked, and can be stocked. A thing laid out (`stock.loose`, its `id` or the ref it lies `on`) shows its
reason. A person (People panel) shows their household and role in it, race, wealth band with its meaning, trade and
backstory, what they carry and, for a trader, the gold and wares. Each can be changed: add a thing found by the item
search (with an optional reason; the default is "The owner added it in the studio."), one more, one fewer, remove,
the lock, the gold, the name, trade, wealth band and backstory. A new name changes the identity and `people.jsonl`'s
row together (one `identity.edit` and one `person.edit`, undone together). Nothing prompts the owner to do any of it.

The ops (Edits, below) carry the whole row after and `before`, like a path or person op, so each has an inverse and
conflicts are found the same way: `identity.edit` a people-source person; `stock.container.set` a container row
(no `before`: added) and `.remove`; `stock.loose.add`/`.remove`/`.edit`; `stock.possessions.set`,
`stock.trader.set` and `stock.delivery.set` a row or null with its `before` or null (null after: removed; null
before: added). A row is named by `id` (people, loose), `space` and `ref` (containers), `person` (possessions,
traders), or its whole self (deliveries).

**Finalise** applies these ops to the source files, never to the tables, through the same `edits.apply` as the place
files: `edits.load_place` reads the place's people and stock sources beside the place files (`newworld/sources`,
under `identities` and `stock`), and `write_place` writes back only a source whose rows changed: the people source
as indented JSON, the stock source one row per line, as they are kept. The record step commits the sources by path
with the place; when the save holds a content op it then runs `stockdb items` (only when an op names an item
`items.json` lacks) and `stockdb load`, and commits `items.json` and the tables by path. A failure there stops the
chain at record; a rerun finds the save recorded and reloads again. The build that follows reads the database.

**The owner's own words.** A reason (`why`) or note text (`text`) that a content op's row holds and its before did not
is the owner's, written in the studio: it is recorded at the statement tier `OWNER_STATED` (a note's `tier`, `why_tier`
beside a reason); a word the row keeps keeps the tier it had. `js/stock.js` `ownerMarks` marks a row as the studio
makes its op, and `edits.apply_save` marks a save again (`edits.mark_owner`, so a later op's before names the marked
row), so a save from any client goes in at the owner's tier; an op's inverse is never marked. `OWNER_STATED` ranks
first among the statement tiers (`newworld/sources/key.json`, highest first), above canon: the owner rules what the
game says, and a departure from canon is the owner's to make. No agent or tool overwrites an owner-tier row: `stock
derive` keeps every such row of the stock source as it stands and lists the difference in `owner_kept`.

## Edits

The studio never writes place files. It keeps an ordered list of operations; undo and redo move a cursor in it; a
save is the list up to the cursor.

`edits/<save_id>.json`: `{save_id, place_id, name, at, rev, final: bool, base:{draft_key, ground_sha}, ops:[...],
notes:[{id, text, at}]}`.
`rev` is raised by the server on every write. The autosave is the same shape at `out/places/autosave/<place_id>.json`
(on disk and in the private bucket, never committed).
An op: `{n, at, op, space, call: "fault"|"taste", note_group?, stroke?, ...payload with before and after}`.

| op | payload |
|---|---|
| `ref.add` | `ref` (whole row; `src` set when copied from a source ref, `base` when from search); the first op into a space the place does not have yet carries `space_copy_of: "<source_id>/<space_id>"` and `space_name`, which become that interior's `space.json` |
| `ref.remove` | `id`, `before` |
| `ref.move` | `id`, `before:{pos,rot,scale,seat,primitive}` (the fields it changes), `after:{...}` |
| `veg.clear` / `veg.restore` | `items:[{base,pos}]` |
| `land.patch` | `cell`, `verts:[[row,col,before_z,after_z]]`, `tool:{kind: raise|lower|level|smooth, radius, strength}` |
| `path.add` / `path.remove` / `path.edit` | `path`, `before?` |
| `person.add` / `person.remove` / `person.edit` | `person`, `before?` (placement, routine stops, patrol points) |
| `identity.edit` | `person` (the people source's row: name, sex, race, household, role, trade, wealth, level, notes), `before` |
| `stock.container.set` / `stock.container.remove` | `container` (the stock source's whole container row with its items); `.set` with `before` replaces it, without adds it |
| `stock.loose.add` / `stock.loose.remove` / `stock.loose.edit` | `loose` (whole row), `before` on `.edit` |
| `stock.possessions.set` | `possessions` ({person, items, why} or null: removed), `before` (null: added) |
| `stock.trader.set` | `trader` ({person, give_seq, gold, items, why, cites} or null), `before` (or null) |
| `stock.delivery.set` | `delivery` ({give_seq, by, person?, ref?, status, why} or null), `before?` (found by the whole row) |

- `land.patch` heights are the patch's `dz` at that vertex, as `land.jsonl` holds it (0 is the world's own ground).
- `path.add` and `person.add` carry the new row; `.remove` carries the removed row; `.edit` carries the row after
  and `before` the row before.
- `veg.clear` writes the item as the row (`by: owner` unless the item names `by`); `veg.restore` items carry the
  whole cleared row (`by`, and a draft row's `why` and `ref`), so the inverse puts it back as it was. Plants are
  keyed by base and position rounded half up to a tenth of a unit (JavaScript's `Math.round(v * 10) / 10`).
- A `ref.add` with `space_copy_of` creates the room: `space.json` is `{space_id, copy_of, name: space_name,
  door_from, parent}`, where `door_from` and `parent` are the door (and its space) whose `door.to_space` is this
  room, whichever op adds it first. Into a space that already exists it is a conflict. Its inverse is a
  `ref.remove` with `space_drop: true`, which deletes the room when its last ref goes.
- Doors are paired: after a save is applied, every door it added that leads into one of the place's own rooms
  must find its `to_ref` there, leading back to it; otherwise the save is a conflict.
- Rows are kept in one order (refs, paths and people by id, land by cell, clearance by base and position; in the
  people source households and people by id; in the stock source containers by space and ref, loose by id,
  possessions and traders by person, deliveries by give, by, person, ref), so independent ops give the same files in
  any order. Floats match within 0.001. The content ops' cases are `tools/tests/places_edits/stock/` (a `base.json`
  people and stock source, then per case `ops` with `expected` sources or an `error`).
- An op whose `before` (or the row it names) does not match the files is a conflict: the save is not applied and
  the error names the op. Every op has an inverse; a save then its inverse gives back the files.
- A copied room's refs that `refs.jsonl` does not list exist as copied, under their source id (the draft bundle's
  reading of the source cell and the build's room rule, `tools/places/draft_bundle.py: copy_space`). A `ref.move`
  or `ref.remove` on one checks `before` (`base`, `pos`, `rot`, `scale`) against that source row and writes an
  override row with `id` and `src` both the source id: the whole source row with `after` over it, or
  `{id, src, removed: true}`. An override moved back to its source pose is dropped; a `ref.add` of a removed
  override's id drops the marker (and adds nothing when the row is the source's own). Removing a listed row that
  has a `src` in the copied room leaves `{id, src, removed: true}`, so the source ref does not return. A ref in
  neither the files nor the copied room is a conflict. These cases are `tools/tests/places_edits/copy_refs/`, with
  the copied room's rows given as `source: {space_id: [row...]}`.
- `place.json` lists `saves_applied`; a save already listed is rejected. Applying a save also appends each `taste`
  op to `place.json` `preferences` as `{save, n, op, what, note}`.

**Notes on changes.** The owner's words for the agent travel with the changes they are about. A note is
`{id, text, at}` in the save's `notes`, listed once; every op it covers carries its `id` in `note_group`, and an op
naming a note the save does not list is a schema error (`check_save`). A change is one op, or the ops of one
`stroke`; a note covers whole changes. An older save's per-op `note` reads as a note on that op and on the ops
beside it with the same words (`tools/places/change_notes.py: groups`, `js/note_groups.js: groupsOf`). In the
studio the note bar sits under the views in the page's flow, never over the panel or a view's controls: it counts
the changes since the last note (the applied changes after the last noted one), a stepper trims the count to the
last few, a Fault/Taste switch sets their call, and one ordinary text field (typed, handwritten or spoken) takes
the note; confirming gives those changes one new note and the count starts again. Changes never noted stay
unnoted. History picks any changes and gives them one note; tapping a change's note picks its changes and offers
its words to edit or take away. The Notes panel lists the notes on the applied changes ("about 3 changes"), and
Select picks the things they touched. Undo and redo leave each op's `note_group` as it is, so a note covers what is
applied and comes back with its changes; a save writes the notes its applied ops name. A taste op's preference row
takes its note's words. The agent reads each note with exactly the changes it covers, each said as what changed,
from what to what, and where (`change_notes.present`): finalise's lessons step (`notes.json`), and
`python -m tools.places notes --changes`, which lists them for every save not yet finalised. They are read at
finalise and never before.

`call` defaults to `fault`. Applying a save to the place files is one function (`tools/places/edits.py: apply`,
`apply_save` for a whole save), used by load (in memory) and by finalise (to disk). The fixtures in
`tools/tests/places_edits/` (`place.json`, and per case `ops` with `expected` or an `error` pattern) are the
semantics; the front end's JavaScript mirror is tested against the same files.

## Studio API (`/api`, JSON; the front end uses nothing else)

```
GET  /api/places                              places with a draft; each: place_id, title, source_id, similar,
                                              stamps:{draft, ground, source}, fit (place.json's fit as the draft
                                              wrote it, or null: the studio's linked views map through it),
                                              draft_error: [{error} when the draft bundle
                                              could not be rebuilt (the last good one is served), {missing_base, refs}
                                              for a base in neither the source bundle nor the catalogue]
GET  /api/bundle/<bundle_id>/...              the bundle's files as written
GET  /api/asset/mesh?model=<path>&level=0|1   GLB (converted on demand, off the event loop);
                                              level 1 is the light version (trees, plants, far away)
GET  /api/asset/tex?path=<path>&size=<n>      WebP; cached a month (immutable: the GLBs' texture URIs); a texture
                                              the profile lacks: 200, a 4x4 grey WebP, X-Argonia-Missing: 1
GET  /api/asset/thumb?model=<path>            256 px WebP thumbnail of a mesh
GET  /api/asset/land                          land.json: the land textures for the terrain splat (Assets, below)
GET  /api/asset/land/<file>                   one land texture, WebP
GET  /api/search?q=&scope=source|all&source_id=&kind=&limit=
                                              {q, scope, results:[{key, edid, name, model, type, kind, nordic,
                                              plugin, score, thumb}]}; kind may be a comma list
GET  /api/place/<id>/saves                    [{save_id, name, at, rev, final, ops, kept: committed|pending|
                                              disk+bucket}], newest first, the autosave among them
GET  /api/place/<id>/saves/<save_id>          a save
PUT  /api/place/<id>/saves/<save_id>          write a save {name, base, ops, rev}: rev is the rev the tab last read
                                              (0 for a new save); 200 {save_id, rev, at, kept}; 409 {error,
                                              current:{rev, at, name}} when the save moved on since (another tab),
                                              is final, or is being finalised (from the POST below until its chain
                                              ends; a chain that failed leaves it open to change). save_id: [a-z0-9][a-z0-9._-]*; "autosave" is the autosave
POST /api/place/<id>/finalise {save_id}       starts the chain; 202 {run_id}
GET  /api/place/<id>/runs/<run_id>            {run_id, save_id, state: starting|running|done|failed, step, rc,
                                              log (tail), report (markdown, when done)} plus every
                                              field of finalise.read_run (steps, log_tail, report_md)
GET  /api/place/<id>/seat?x=&y=               ground height, water height, slope at a point (the same code as seat)
GET  /api/place/<id>/nav                      the built place's walking mesh (tools/places/navexport.py): the built
                                              plugin's navmesh, outside (with the world's round it) and per room.
                                              The studio finds people's routes on it (navroute.js), so a drawn
                                              route is the way taken in the game: every point lies on the mesh,
                                              and a stop that stands off it (a chair by a wall) is joined to the
                                              mesh's nearest point; 404 before the first build
GET  /api/place/<id>/notes                    the owner's notes for the agent, oldest first: [{id, at, text, things:
                                              [{id, space, base, name, kind, pos, src}], view: {space, at}, sent,
                                              sent_at, batch, done, done_at, reply}] (Notes for the agent, below)
POST /api/place/<id>/notes                    {text, things, view} keeps a new note, unsent; {id, text} changes the
                                              words of an unsent one, {id, delete: true} deletes it (400 once sent);
                                              {id, done} closes or reopens a sent one. Notes on changes are in the
                                              saves (Edits: notes on changes)
POST /api/place/<id>/notes/send               sends every unsent note as one batch and starts its agent: 202
                                              {batch, sent: [notes], job}; 400 when none is unsent
GET  /api/place/<id>/stock                    who the place's people are and what it holds, from the database's
                                              sources (Stock: the studio)
GET  /api/place/<id>/items?q=&kind=&limit=    item search for a holder: each result allowed or refused, with why
GET  /api/place/<id>/needs                    what the stories need of the place, made from the stories at each
                                              request (What the stories need of a place, below): {needs: [{seq,
                                              key, thing, line, quests, does, rewrite, sources: [{story, line,
                                              rewrite, url}], judged, know, signs, rests, met, why, fit, narrow,
                                              sight, changed}], people: {person id: {who, name, uses: [{for, line,
                                              rewrite, sources}]}}, changed_story: [{seq, was_for, line, placed}]}
POST /api/place/<id>/needs/changed            the owner carried on past a need's warning: {need | person, change:
                                              removed|moved|renamed, what, save}; appended at OWNER_STATED to
                                              newworld/sources/needs/<id>.changed.jsonl and committed by path
POST /api/heartbeat                           an open tab, every 60 s; {held, started, release_after_s}
GET  /api/status                              {ground_sha, deployed_sha, match, error?, versions:{studio, repo_head,
                                              python, aiohttp, search_model, search_rows}, awake:{job_alive}}
```

Errors are `{error}` with a plain-English message; a missing source is 404. Bundle, web and asset files
carry ETags, honour range requests, and are sent brotli- or gzip-compressed when the browser accepts it and no
range is asked.

**The server** (`tools/places/studio`, aiohttp) calls each other part through one function
(`tools/places/studio/links.py`): `tools.places.assets.mesh(model, level)`, `tex(path, size)` and `thumb(model)`
return the converted file's path (synchronous, run off the event loop); `land_table()` returns land.json's path; `tools.places.seat.ground_for(place_id).at(x, y)`;
`tools.places.ground_check.status()` returns `{ground_sha, deployed_sha, match}`. Finalise calls `tools.places.finalise.start` and runs
are read with `read_run` (Finalise, below); `rc` is the job_guard job `finalise.<run_id>`'s exit code.

**What the views draw** (the front end, `tools/places/studio/web`): exactly what the game will show. Every placed
thing is drawn whole at any zoom, its placed ground cover too. Geometry the game never shows is left out: effects
(models under `effects\` or named `fx*`, records named `FX*`: the game's shader tricks, wherever a mod keeps
them, as Dragonborn's Apocrypha mist in `dlc02\dungeons`), things with no model (markers, triggers, sounds; a light is drawn as a bulb, below) and any part of a
model under a node named `EditorMarker` (the Creation Kit's own marker shapes, as on mist, fog and trap gas). Grass
is grown as the game grows it, from each land texture's grass list (`grass.js`, rules in `grass_rules.js`): a ring
round where the view looks, out to the view's distance (at most 16,000 units), every spot near the eye and, beyond
4,500 units, a spot kept with chance (4500 / d)^2 and drawn up to twice the size, so the ground keeps its cover for at
most 6,000 blades; none once the view stands back past 30,000 units, and none from a model the converter could not
read. Drawn paths are painted as the build paints them, by the world's road rule (`path_paint.js`; node tests it
against `test/road_rule.json`, numbers the Python rule wrote and a Python test keeps current): three alpha layers over
the ground (verge, second track, first track) whose composite is the build's weights: full on the path, a straight ramp
from its edge (0 by 8.55 m out for a road or a street, 6.8 m for a path, a dirt track or a boardwalk), the track core
falling away over 6.5 m with the verge holding the rest; a style word takes the road set of the ground (the set whose
track the world's land here carries, else the forest set; the build takes the ground province's), a one-texture style
(`mud`, `sand`, `stone`, `skirt`) or a picked key its own texture, a material found by its whole name
(`ANW_Ground_<id>`); tiled and lit like the ground; a boardwalk only ashore. Each view has a compass at its lower left (the needle points north on
screen; a tap turns the view to face north), and the Selected panel gives the position in game units, the cell
(floor of position / 4096, outside) and the turn in degrees, or the middle of several things, kept current as they
move.

**Lights** (`objects.js`, `lights.js`). A light record has no model in the game, so the views draw each light as a
small bulb of its own colour (a few pixels across at any distance), every bulb of a layer in one instanced mesh, with
a faint ring at its radius for a selected light, the lights of a selected fixture, and any light within 1,500 units
of where the view looks (a second instanced mesh). Bulbs are drawn and picked while the Select or Add tool is in use, or with the Selected panel's toggle
"Lights and invisible walls: always show them", so other tools' views stay uncluttered. A light belongs to the nearest fixture within 128
units: a thing whose record names a lantern, sconce, candle, torch, brazier, fire, chandelier, lamp, window, glow,
ember or hearth. The Selected panel gives a light's radius, colour (with a swatch), whether it casts shadows and the
fixture it belongs to, and a fixture's lights. Moving, turning, resizing, seating, duplicating or removing a fixture
takes its lights with it in the same undo step, each keeping its place in the fixture's frame and its height through
its own seat. A light selected by itself moves or goes alone.

**Invisible walls** (`objects.js`, `prims.js`). A ref with a primitive (a kept collision box, or a trigger, room or
sound volume) has no model either. With the lights, and only then, each is drawn as a faint box of its real size (its
half extents round the ref's origin, turned with the ref) with its edges outlined a pixel or two wide, or a faint wire
sphere, every one of a layer in one instanced mesh filled when the layer changes (nothing is worked out per frame),
and picked by its box. The Selected panel says what it is (a collision marker's box: "an invisible wall: people and
the player cannot pass"; anything else: an invisible volume the game uses, nothing solid), the piece it belongs to
(the piece its seat stands `on`) and its size in units and metres. It follows that piece as a light follows its
fixture: moving, turning, resizing, seating, duplicating or removing the piece takes its invisible walls with it in
the same undo step, each keeping its place in the piece's frame and its height through its own seat, a resize
growing its box by the same factor, a copy seated on the piece's copy. The tie is the wall's seat `on` the piece,
as the drafter's `primitives` stage writes it; a box seated on nothing goes alone. The Selected panel of a piece
says what comes with it: how many invisible walls and lights. A wall selected by itself moves, turns and is removed
alone, and the panel's size fields (long, wide, high in units; a sphere's radius) change its extents as one `ref.move`
of its `primitive`. The plain view never shows it.

**Day and night** (`js/lighting.js`). Each view's bar has a Day and a Night switch; with the People tool on, the
time of day drives both (night from the end of the climate's sunset to the start of its sunrise), and a view's switch
moves the time. By day the studio's own light, as it always was. By night the game's: outside, the climate's weather
(the likeliest, or the one chosen under Detail) at night: the six directional ambient colours as a hemisphere that
gives a level face the side colours exactly, the sunlight colour as moonlight, the upper sky colour as the sky, and
fog from its night distances, power and maximum, measured from where the view looks; inside, the cell's own
lighting (ambient, directional colour and rotation, fog), each field the cell inherits taken from its lighting
template; a room the game keeps the same at any hour. A bundle without this data shows a plain night and says so.
Every placed light (its base's radius, colour and fade, the ref's own radius and fade offset; a negative light is
left out) lights its surroundings with Skyrim's falloff, 1 - (d / r)^2 in the game's gamma space. The six lights
nearest where the view looks are real unshadowed point lights (six in every view at all times, by day at nothing, so
no shader is rebuilt); every other light is a pool: one instanced draw of additive discs into a light map seen from
above (1,024 texels a side, three times the view's distance across, drawn again when a light changes or the view
moves a quarter of the map away), the disc where the light's sphere meets the ground under it, weighted by the
ground's angle to the light (never under a third, so walls keep some), which every lit surface adds in by its
position, times its own colour. Each light glows where it hangs. What is approximate, as the studio's help says: no
shadows; no ENB or Community Shaders effects; windows do not glow; the game's eye adjusting to the dark is not
copied; a pool lights everything at its spot whatever its height.

**The world map.** The top bar's World map button opens the Atlas (the page `python3 -m tools.newworld.map_page`
builds into `out/newworld/map/`) over the studio in a frame, loaded the first time it is opened, at
`/atlas/index.html#place=<place_id>`: the Atlas reads `#place=` at load to centre, zoom and open that place. The
server serves the built directory read-only at `/atlas/` (`STUDIO_ATLAS` overrides the directory) and answers 404
when it has not been built, which the button then says. Nothing of the Atlas is copied into the studio.

**Saves.** Writes are atomic. A named save is committed and pushed by path (`tooling/lane_commit.sh`) after each
write, so it survives a stopped machine and a lost disk; the autosave goes to the private bucket at most once a
minute. Saves and notes are committed one at a time; a commit that fails (another commit in the tree at that
moment, the network) is tried again after a wait, six times in all, and the finalise chain does the same with its
own commits, so the server and the chain never fail each other. Notes are changed under a lock on the place's
`edits/` folder, so the server and an agent's `notes done` never lose each other's change. Request bodies are
capped by kind: a save 64 MB, a note 512 KB, a finalise 4 KB; the page's log line keeps its first 4,000 bytes.

**Search** (`tools/places/search`): `python -m tools.places search build` embeds each catalogue base
(`out/places/catalogue/bases.jsonl`) with bge-small-en-v1.5 (MIT; int8 ONNX on CPU, 34 MB in
`~/.argonia/models`) into `out/places/search/`, re-embedding only keys whose text changed. The text is the base's
name, editor id and model path split into words, its record type, and a short gloss of modders' words
(boardwalk: wooden walkway). A query scores cosine similarity plus exact (editor id or name equal to the query)
and prefix boosts, so a typed name always comes first. `scope=source` keeps the bases of
`bundles/src.<source_id>/bases.jsonl`; a base's `kind` is its catalogue `kind`, else one derived from its type.

**Awake.** Each heartbeat touches `~/.argonia/state/studio-heartbeat` and starts the job_guard job
`studio-awake` if it is not alive; the job ends five minutes after the last heartbeat (and every four hours, the
next heartbeat starting a fresh one). While it lives the idle-stop sees a job and keep-busy holds the CPU above the
owner's alarm, which then stops the machine about 30 minutes after the last tab closes. The alarm is never touched.

**Notes for the agent.** Besides the notes on changes, the owner writes plain notes in the Notes panel, about the
place or about the things selected, as many as he likes. One JSON line each in the place's `edits/notes.jsonl`
(outside the draft's and the build's identity), written under the edits folder's lock and committed by path as the
saves are, so a note survives a closed tab and a stopped machine. A note is in one of three states:
- **unsent** (`sent: false`): the owner's; he may change its words or delete it, and no agent sees it;
- **sent**: the panel's "Send notes to the agent (n)" sends every unsent note of the place as one batch (`batch`,
  `sent_at`), after one confirmation in plain words ("An agent will read these three notes and make the changes. You
  can keep editing."); it can no longer change;
- **done**: the agent closed it with its reply, shown under the note.

A row without `sent` predates batches and counts as sent. Sending starts the batch's agent at once
(`tools/places/notes_batch.py: start`): a headless `claude -p` under `tooling/job_guard.sh`, as the finalise chain
runs its lessons agent (budget $10, 80 turns, edits accepted, its shell limited to `python -m tools.places`, the lane
commit and git reads). One notes agent runs at a time: each run holds `out/places/notes-runs/agent.lock` for its
whole length, so a batch sent meanwhile waits and then takes every sent note still open. The prompt names the place
and the notes and says: read them with `python -m tools.places notes <place>`; answer each with a narrow change to
the place by the place-build skill's stage for it, never redrafting the whole place nor regenerating over the
owner's studio edits; close each with `notes done <place> <id> --reply "..."` in plain English; a question for the
owner, or a change larger than a narrow one, is closed with a reply that says so and what it would take, and not
done; commit the changed files and the notes file by path. Each run's prompt, cost, turns and the notes it left open
are kept in `out/places/notes-runs/`.

`python -m tools.places notes` lists the sent, open notes of every place (what a session start answers);
`--unsent` adds the owner's unsent ones, `--changes` the notes on changes in saves not yet finalised, `--all`
everything. `notes done` refuses an unsent note.

**Hosting.** `https://studio.<domain>` (the Moonlight gate's zone): the named tunnel `argonia-build` to
`localhost:8765`, behind Cloudflare Access for the owner's email only; the VM opens no port.
`infra/build-vm/studio-install.sh` installs the pinned cloudflared and the user units `argonia-studio` and
`argonia-studio-tunnel` (started at boot, restarted on failure); `infra/build-vm/studio_gate.py apply` makes the
tunnel, DNS and Access app and `prove` checks both sides of the gate and the switch below.

**The address starts the machine.** The play switch Worker (`infra/cloudflare/play-switch.js`, deployed by
`infra/gpu-box/cloudflare_gate.py worker`) is routed on the studio's page and `/argonia/*` (`studio.<domain>/` and
`studio.<domain>/argonia/*`); the studio's own requests (assets, the API) go straight to the tunnel. With the build
machine running, the page's request goes on to the tunnel unchanged (marked `x-argonia-switch: studio`), so the
owner sees no difference. With it stopped, the Worker checks the owner: the Access sign-in's token (its header, else
its cookie) verified against the team's signing keys, for the studio app's audience, unexpired, with the owner's
email; anyone else gets "Only the owner can start the build machine" and nothing starts. For the owner it writes the
tag `argonia-studio-start=<time>` on the instance, starts it, and shows "Starting the build machine. This takes
about a minute.", a page that reloads every 4 seconds and so becomes the studio once it answers; a start AWS
refuses while the machine settles after a stop retries for two minutes, and any other refusal says what AWS said and
what to do. The Worker's AWS user may describe instances and start, and tag with that one key, only
`argonia-build` (infra/OWNER-SETUP.md). At boot `infra/build-vm/resume.sh` reads the tag: a boot within 10 minutes
of it is a studio start, which resumes no agent (Claude waits at its prompt), so opening the studio spends no Claude
usage; work a resume was owed is kept in `state/resume-owed` for the next start that is not the studio's. The
machine stops itself as before: the Awake job ends five minutes after the last tab closes and the owner's alarm
stops it about 30 minutes later.

## What the stories need of a place

A line story lists, per place, the physical things its quests rely on (skill `story-line`, "What each quest needs
of its places"). Those rows are the place's **needs**, beside its record's promises (`place_give`, `give_delivery`).
A place is built to both, and a need is **met only from the player's side**: the thing exists in the place files
and a player who has been told nothing would know it for what it is, by its look, by the game's own label (the name
its door shows, which is its room's name; a map marker's name; a named thing), by what stands in or by it, or
because a named person tells them. A house the story calls the hatching shed is "not met: a house stands at X that
could become it". The stories are fitted to the place, never the place redrafted for a story: every unmet need
says what the place has that the story could use instead (`fit`) and whether a small narrow addition closes the
gap (`narrow`: a name on a room, a lock, a thing placed, a person's spot).

| What | Where |
|---|---|
| What a place's stories need of it, and the people they name | the line stories' needs tables and text (`story/design/quests/lines/`) and the cast roster, read each time (`tools/places/needs.py`) |
| The place's judgement of each need, keyed to the story rows it judges | `newworld/sources/needs/<place_id>.json` (`needs`, `dismissed`) |
| The story lines, named for a reader who knows none of them | `newworld/sources/needs/lines.json` |
| The owner's changes to what a need rests on | `newworld/sources/needs/<place_id>.changed.jsonl` (the studio writes it) |
| The tables | `story_line`, `need_sign`, `place_need`, `place_need_sign`, `place_need_story`, `need_change` (`tools/newworld/needsdb.py`) |

The panel is made from the stories each time it is asked for, so it never falls behind them. A **need** is a row
of a story's needs table naming this place (its name or an alias in the database), shown in the story's own words
with a link to the story in the story explorer; a story whose head says `**Status: to be rewritten.**` marks its
rows so, and one whose status begins "replaced" is not read. A **judgement** is the place's side, kept by hand:
`{seq, from: [the story rows' keys], thing (the row it judged), line, rests: {space, ref?} | {person} | null,
signs: [{sign: look|label|beside|person, detail, person?}], placed?: [{person}], near?: {space, pos}, met, why,
fit?, narrow?, sight?: {result: recognised|not recognised, said}, tier}`. A row no judgement covers shows as not yet
judged. A judgement whose rows no story still has shows under **Placed for a story that has changed**, with every
thing placed for it (a ref whose `need` is its seq) and every person it names; nothing is removed, and the owner
decides. **People the stories name** are the place's people found by name in the line stories and the cast roster,
each with the sentence or table row that names them and its link. Who each person is to a player (their trade and
household) is derived from the people source, never stored.

    python -m tools.places needs open <place>           the story rows no judgement covers yet, with their keys
    python -m tools.places needs dismiss <place> <key> --why "..."    a row that names the place by mistake
    python -m tools.places needs check <place>          every rest exists; every need judged; every unmet one fitted
    python -m tools.places needs show <place>
    python -m tools.places needs changed [<place>]      the owner's changes: the stories to change to fit
    python -m tools.places needs load                   the tables from the sources
    python -m tools.places sight <place>                the sight test's input

**The sight test.** `sight` writes, for each need's spot, only what a player would meet there: what stands within
about 30 metres in plain kinds (`tools/argonia_world/surroundings.py`'s table over each base's model and editor id),
the names the game shows (doors by their room's name, map markers, named things: a base's name or a row's own
`name`, with the lock the stock source gives it), the people there as a player
sees them (name, race, a guard's kit, what they offer when spoken to), and through a door the room's name and what
it holds; never our names for things, ids or the story. One fresh `reader` is asked first what each spot is, and
only then which spot each needed thing is; the need's `sight` records whether the reader said it unprompted.

**The studio.** The rail's **Story** opens "What the story needs of this place": one row per need in its plain
sentence, grouped not met, not yet judged, then met, each linked to the story it comes from and marked when that
story is to be rewritten, saying how the player would know it, what is there now, what the story could use
instead and whether a small change closes the gap; "Show it" (or "Show what could serve") selects and frames the
thing or person; a not-met row offers a note for the agent (the place's ordinary notes). Below them come the
people the stories name, and what stands placed for a story that has changed, each with "Show". Selecting a thing or
person a need rests on, or any of the place's people, adds a line to the Selected or People panel: who this is to
a player, and "A quest needs this: ...". Removing, moving more than 10 metres or into another cell, re-homing or
renaming something a need rests on shows a plain warning at that moment ("A quest needs this: ... If you change
it, that quest will be changed to fit. Carry on?"), never a block: the change has already been made like any
other; "Undo this change" undoes it, and "Carry on" records the change at `OWNER_STATED` for `needs changed`. The
view bar's **As the player sees it** shows over the view the names the game shows: door names (the room each
leads to), the room's own name inside, map markers, and named things near where the view looks; people's names
show as always.

## Assets (`tools/places/assets`)

**Resolution.** A model or texture path resolves as the game does in the NewWorld profile: the loose winner from
`~/.argonia/stack/installed-NewWorld.json` (Tropical Skyrim's file wins over vanilla where it has one), found in
`~/.argonia/stack/MO2/mods/<mod>` or `~/games/skyrimse/newworld-assets/<mod>`, then the profile mods' BSAs in
priority order, then the game's `Data/*.bsa`.

**Meshes.** `nifdump` (C++, built from ousnius/nifly by `tools/places/assets/nifdump/build.sh`) reads the NIF;
`nifglb.py` writes a GLB in the mesh's own units and axes: one node per drawable shape carrying its transform to
the root, positions, normals, UVs (shader UV scale and offset applied), vertex colours (a tree's vertex alpha is
its wind weight, never opacity), alpha test as MASK at the NIF's threshold, alpha blend as BLEND, two-sided as
doubleSided. Textures are referenced by URI, never embedded: `/api/asset/tex?path=<data path>&size=512` (256 for
a normal map), so a texture shared by many meshes is fetched once; the front end may rewrite `size`. Level 1 is
the light version: a mesh over 1,500 triangles simplified to the larger of 1,500 and a quarter. The GLB's
`extras.argonia` holds `{level, tris, tris_full, shapes, textures, bounds, placeholder?, why?}`. A mesh that
cannot be read is a magenta half-transparent box of the base's bounds with `placeholder: true` and the reason;
nothing is dropped. When the fault is not the mesh's (the reader not built, out of time on a busy machine, the
disk) the box also has `retry: true`, is served `no-store` and is not kept: the next request converts again.

**Textures.** DDS (BC1 to BC7, uncompressed) to lossy WebP, halved to the largest power of two not over the
requested size (64 to 2048); alpha kept on diffuse textures, dropped on normal maps and land textures.

**Cache.** `out/places/assets/{mesh,tex,thumb}/`, each file keyed by the sha256 of its source bytes and the
converter's version (the hash is worked out once per source file as it stands, so a request for something already
converted reads no source); atomic writes, one conversion per key at a time; least recently used files deleted
above `ARGONIA_ASSET_CAP_MB` (default 4096), the land set never. `python -m tools.places assets warm <bundle_id>...` converts everything the
bundles use in parallel and writes `out/places/assets/reports/warm-<ids>.json` (placeholders and missing
textures, each with its reason and users; counts, bytes, seconds).

**Land.** `out/places/assets/land/land.json`: `{<LTEX key>: {edid, plugin, diffuse, file, avg, w, h}}` for every
land texture the bundles' terrains use and every land texture record of the catalogue's sources; `file` is the
WebP (512, no alpha) under `land/`, `avg` its average colour (the splat at a distance and while loading); a
texture the profile lacks has `file: null` and `why`.

**Catalogue.** `python -m tools.places assets catalogue` writes `out/places/catalogue/bases.jsonl`: every base
with a model across the game's masters and Creation Club files, USSEP, Tropical Skyrim, BM&V and every new-world
source and asset mod in `mods/dependencies.json` (a plugin not on disk is unpacked from the mod's archive), the
last plugin's version winning. A row is the bundle base shape plus `kind`, `source` (mod id), `has_model` (the
model resolves, so the converter can show it), `nordic` (decision 0006: Skyrim's architecture sets and
cold-climate flora by editor id and model words) and `text`, a plain-English descriptor (name, editor id in words,
record type, model path words, source mod, size in metres). `ltex.jsonl` beside it lists every land texture record.

## Build

`python -m tools.places build <place_id>` writes the place layer: one plugin for all places,
`out/places/plugin/ArgoniaNWPlaces.esp`, assembled from one shard per place, mastered on `ArgoniaNewWorld.esm`.
It holds each place's refs, interiors with paired doors, people with their packages, guards, the crime faction,
service factions and chests, land overrides for patched cells, the cleared world refs, the path textures, and
the navmesh of every touched cell, joined to its untouched neighbours. Base records of plugins that are not
loaded are copied in as ours (the route `tools/ArgoniaPlugin/ForeignCopy.cs` proves). Nothing placed is levelled
(decision 0035): a container whose base holds a levelled list stands on a copy of ours with the fixed items (as a
merchant chest is made; these copies take ids from 0x00FFFF down), and a placed levelled item list is the item it
gives at level 1. Never LOD.

**Override, not merge.** The place layer is an ESP that overrides the world ESM's WRLD, CELL headers, LAND and
NAVM and adds refs; nothing is merged into the ESM, so a place build never waits on a world rebuild. Measured on
Bethesda's own plugins (`ArgoniaPlacesBuild study`): Update.esm overrides 267 NAVM and 1,659 LAND of Skyrim.esm,
and its NAVI holds 313 NVMI (42 of its own navmeshes, 271 of overridden ones) beside Skyrim.esm's 15,462;
Dawnguard 407 NAVM overrides and 1,873 NVMI, HearthFires 88 and 132, Dragonborn 26 and 1,732. A NAVI override
carries only its own and its overridden navmeshes' NVMI and the engine keeps every other plugin's; ours does the
same. An ESP's form ids run 0x000800 to 0xFFFFFF; each place has a block of 0x8000
(`newworld/places/formid_blocks.json`; the ids of its keys in `newworld/places/<place_id>/formids.json`, both
committed so a save game's refs stay the same for life); copied foreign bases take 0x001000 on. Load doors,
actors, beds, package targets and merchant chests are persistent: in the world's persistent cell (exterior) or
their own cell (interior), as vanilla files them.

**The recipe.**
0. `build <place_id> --plan` plans without navmesh or plugin and lists every problem (a fault of the place
   files: file, row id, what is wrong), exiting 1 if any; a full build stops on the same list. The drafter runs it
   in its loop (seconds once the source cells and rooms are cached).
1. Plan each place into `out/places/shards/<place_id>/plan.json` (`tools/places/build.py`), keyed on its place
   files, the world ESM's sha256 and the code; an unchanged key is not planned again. The world ESM must be of the
   land build its navmesh inputs hold (`out/newworld/plugin/land/manifest.json`), else the build stops.
2. Interiors: `space.json` `copy_of` names the source cell, copied as the game shows it with the source's load order
   (the bundle's `plugins`, masters first): every plugin that can hold the cell (the one it originates in and each
   plugin mastering that one) is read, in load order, and the last holder's version of each ref, navmesh and the
   header wins; a ref its winner deletes is gone. A cell BM&V overrides from Dawnguard.esm is Dawnguard's refs with
   BM&V's changes over them, never BM&V's alone. Each holder is read once and cached under `out/places/srccells`;
   the plan's `src_plugins` lists the holders in load order and the writer reads the source refs the same way.
   `room` (one of the cell's load doors that lead out)
   keeps only that room of a cell the source shares between houses, by the room rule: the whole cell's collision
   (doors open) is meshed by the world's own Recast run; the room is the walkable island reached from its door;
   every source ref belongs to the door island its position is nearest, islands of every door of the cell
   competing, so refs behind a door that leads nowhere fall in no room. No hand numbers; cached under
   `out/places/rooms` by the source refs' hash. Measured on BM&V's `01ArgonianHouseinside` (nine houses in one
   cell, no source navmesh joining door to floor): nine islands of 206 to 278 triangles, 6 beds in each room,
   every ref at least 2,093 units nearer its own room than the next. A row with `src` changes that copied ref
   (`removed: true` drops it; `base`, `pos`, `rot`, `scale`, `owner`, `door` replace the source's); a row with a
   `src` outside the kept room is not in the copy; a row without `src` is added. A copied ref whose base is still
   the source's keeps what the source ref itself says of it: a light's radius and light data, its emittance, an item
   count, a charge, open by default, ignored by sandbox, its lock's key, its primitive. An exterior row whose base is still the
   source's takes its source ref's `light_data` and `emittance` from the source bundle. Any row's own `radius`,
   `light_data`, `emittance`, `count` and `primitive` (the ref shape's) are built as given, in a room or outside. An emittance
   is built only where its target is in our load order: a master's region or light as it is, another plugin's light
   copied in as ours; any other is left off and named in the write's notes. Source actors are never copied: people
   are ours.
3. Doors: a door pair is one row on each side (the exterior door, and the copy's override of the source door it
   leads to) whose `door.to_space` and `to_ref` (our id, or a source key in a copied space) name each other; one row
   naming its partner is enough, and both get teleports. One using door x lands at x's `door.to_pos` and `to_rot`
   (a point in the partner's space beside the partner) when the place files give it; else at the source pair's
   marker (a copied door), the source's marker moved rigidly from the source door to ours (our door whose partner
   is a copy), or 128 units in front of the partner. A source load door of a copy with no partner row is built as
   a plain door.
4. Land: each `land.jsonl` vertex (`row` from the south, `col` from the west, `dz` in units, rounded to 8-unit
   steps) is applied to the world's own heights; every cell whose heights or normals change gets a LAND override
   (the world's record with new VHGT and VNML, the normals computed as the world computes them). Paths are painted
   by the world's road rule (`tools/newworld/world/roadpaint.py`): a style word (`road`, `street`, `path`, `dirt`,
   `track`, `boardwalk`) takes the road set of the ground province at the path (two track materials varying along
   it, a verge), a one-texture style (`mud`, `sand`, `stone`, `skirt`) or a picked key its texture; full on the
   path, a straight ramp beyond its edge. Each quadrant a path reaches is repainted whole (the world's composite
   with the path blended over it, at most six textures: the heaviest at each corner, the path's, then the heaviest)
   and its base and alpha layers replace the world's in that quadrant (`quads` in the plan; Write.cs). A texture a
   quadrant cannot keep fades out over 4 vertices toward it, in it and in its eight neighbours (repainted too, with
   what the world paints there), all on one shared lattice of vertices, so a vertex two quadrants share reads the
   same from both; what the cut takes from a path goes to the path's other textures. Only the cells a path itself
   crosses (96 units beyond its half width) count as touched for the navmesh.
5. Clearance: each `clear.jsonl` row matches the world's ref of its base nearest it within 64 units, overridden
   **Initially Disabled**. Bethesda also deletes (Update.esm: 59 deleted, 7 disabled), but a deleted master ref
   breaks any save or link that names it and cannot come back when the owner un-clears; BM&V disables (40 refs).
   Disabled is reversible and save-safe.
6. People (`tools/places/people.py`): an actor base of ours per person (a copy of `base_from` at a fixed level;
   levelled lists in its inventory, outfits, death item, spells or merchant chest flattened to their level-1
   items), placed once and
   persistent; packages copied from vanilla templated ones (rest: WhiterunBraithSleep21x12; work and wander:
   SolitudeTempleMinister0x8; eat: GuardRiftenEatDayShift20x4; patrol: GuardRiftenBarracksPatrol, the vanilla way: its target
   input is PackageTargetLinkedReference with no keyword, and the actor's own linked ref names the first of a chain
   of linked XMarkerHeadings, closed when `patrol.loop`) with our schedule and place, then an unscheduled sandbox at home; the person's bed
   owned by them; everyone in the place's crime faction (vanilla's hold flags TrackCrime, CrimeGoldUseDefaults and
   CanBeOwner, and its crime values), guards also in IsGuardFaction, and where the place has a sentence (a jail, or
   the Owing) in GuardDialogueFaction (vanilla's DialogueCrimeGuards speaks its arrest lines, pay, resist and "go to
   jail", to an actor that IsGuard and is in GuardDialogueFaction; its "go to jail" line, DGCrimeGoToJail 0267E1, has
   no condition, so the guards of a faction with no sentence are kept out of it, as Skyrim's Orc strongholds' and the
   Skaal village's crime factions have no such guards). The sentence follows the place's law (`place_law`;
   `docs/design/law.md`). The arrest lines, measured (`ArgoniaPlacesBuild crime`, their compiled fragments read):
   pay runs the guard's crime faction's PlayerPayCrimeGold(true, true); "go to jail" SendPlayerToJail(true, true),
   and Winterhold's own line (020F99) SendPlayerToJail(false, true), the player keeping their belongings; resist the
   guard's SetPlayerResistingArrest(); no vanilla line sends with abRealJail false.
   The jail (foreign law), as Skyrim.esm's hold factions have one (measured by `ArgoniaPlacesBuild jail` on Riften, Whiterun,
   Falkreath and Winterhold): the faction's JAIL and WAIT are a persistent PrisonMarker (Skyrim.esm 000004, a
   door-type marker) at the release point outside the jail's town door, whose teleport leads to a second PrisonMarker
   beside the prisoner's bed in the jail and back; STOL and PLCN are an EvidenceChestStolenGoods (0267E7) and an
   EvidenceChestPlayerInventory (108D36) in the jail's room, persistent, empty, never respawning, owned by the crime
   faction; JOUT is BeggarOutfit (028B60); the shared crime faction list (CRGR) is left empty, so the place's bounty
   is its own. The Owing (native law), the same jail served outside with no cell: JAIL and WAIT the return spot's
   PrisonMarker, whose teleport leads to the work spot's PrisonMarker and back; a Bedroll01 beside the work spot;
   STOL an EvidenceChestStolenGoods under the ground; no PLCN and no JOUT. Its line is an INFO of ours first in
   DGCrimeGoToJail (no previous INFO), conditioned on GetInFaction(the place's crime faction) on the speaker, its
   prompt "I'll work off the Owing." and its reply a subtitle, carrying the script fragment of vanilla's 020F99
   (records only). Its resist line, so the guards take no surrender, is an INFO of ours first in DGCrimeResistArrest
   (0267DC), conditioned the same, Goodbye as vanilla's resist lines, its reply a subtitle, running our
   `TIF_ARG_NoSurrender` (papyrus/) at its start with `Guards` the place's guard faction: the guard's
   SetPlayerResistingArrest(), then that faction's SetPlayerEnemy(true), so its guards fight on as enemies and take
   no yield; the townsfolk, in the crime faction only, are not made enemies. No record can do it: the engine takes a
   yield from any guard of a faction that arrests, and no faction flag, crime value, combat style, actor value or
   game setting refuses one (the Yield and AcceptYield subtypes are an actor's own surrender). A foreign law's faction
   has no resist line of ours: vanilla's yield stands. A ref owned `<place>.crime` is owned by the crime faction. A place with neither fines only.
   `draft jail` (tools/places/draft/jail.py) chooses the jail's room (the copied room holding the jail kit: bars, jail
   walls, jail doors; never a name alone), the cell, the Owing's spots and where each thing stands. the cell and where each thing stands. A stop names a ref (our id or a source key in its space), a position (2D, outside only, is
   seated on the built land: the world's heights with the place's land patches, between the cell's vertices), or
   only a space (where one arrives in it by a load door, else its first furniture). A person whose day starts on
   patrol stands at the patrol's first point and keeps home there; every patrol stop of a day walks the one chain,
   and each marker of a chain leads on to one marker only (a patrol point that names a ref another route already
   leads on from is a problem). Services by give (the place record's give at the service's `seq`; `give_kind_id` or `kind` is a copy): `trader-*` a
   vendor faction of ours (hours from the work stop, the vanilla vendor list, a merchant chest in the place's
   chest cell) and the vanilla Job faction; `trainer` a class of ours that teaches (Journeyman 50, Expert 75,
   Master 90; skill and level from `skill`/`level` or the give's detail) with JobTrainerFaction and
   JobTrainer<Skill>Faction; `inn-room` JobInnkeeperFaction and the rented bed (`room_bed`, else a bed of the
   innkeeper's house, else of where they work, that no resident sleeps in) owned by the innkeeper's vendor
   faction. `faction_ranks` `<place>.crime` and `<place>.vendor.*` are made by the build; `<place>.town` is
   the place's town faction.
   Renting the bed is vanilla's, records only: the innkeeper is in JobRentRoomFaction (09CC97) at rank -1 and in
   05091B and 051596, speaks with a voice of form list 03B4A5 (the base's if it is in the list, else the list's
   Male/Female Argonian or Commoner), and carries RentRoomScript (Bed = the rented bed, WI = 035D64); vanilla's
   rent offer (INFO 079B1A) then serves our innkeeper, and check evaluates that INFO's conditions on our records.
   Travel (`boat-stop`, `coach-stop`, `rootworm-stop`): a place's stops and routes are the travel network's
   (`travel_stop`, `travel_route`; docs/design/travel-network.md); nothing about travel is read from a give's
   `detail`. The operator of a stop is the person whose `people.jsonl` service names the stop's give (its seq);
   `people.py` gives them a travel faction of ours per mode (`ANP_<place>_Boatman_`, `_Carter_` or `_RootTender_`
   in its editor id). `build.py plan_travel` and `ArgoniaPlaces/Build/Boat.cs` build it as vanilla's
   DialogueCarriageSystem is (measured: a start-game-enabled quest holding the topics; each destination INFO gates
   on GetGold >= the fare, run on the target): per place a quest of ours; per operator a top-level topic in the
   mode's words ("I need passage.", "I need a ride.", "I would ride the rootworm.") whose line links one topic per
   route of the stop; a route's INFO needs the faction and the gold and carries `TIF_ARG_BoatTravel`
   (`Destination` = the destination's arrival point, its `ANW_MapMarker_<place>` ref in the world ESM; `Fare` = the
   route's fare; `Gold001` = Skyrim.esm 00000F) with fragment `Fragment_0` on OnEnd, which takes the fare and calls
   Game.FastTravel (it works with map travel turned off, as vanilla's carriages do in Survival). A route whose
   destination has no arrival point in the world ESM is not offered: the build lists it as waiting on that place
   (`travel_waiting`) and the record keeps the promise. A stop nobody serves is a problem. check reads quests,
   topics, INFOs, conditions and script properties back (`dump`) and fails a stop unless one operator offers every
   route that has an arrival point, at the route's fare, to that arrival point, and unless the place has its own
   arrival point; the compiled `out/gpu/papyrus/TIF_ARG_BoatTravel.pex` is warned about when absent.
   Shrines (`build.py plan_shrines`, `ArgoniaPlaces/Build/Shrine.cs`): each `shrine` row of `stations.added` is built
   as vanilla's temple shrines are (measured on Skyrim.esm's ten TempleBlessingScript activators): the ref keeps its id
   and form key; its base becomes an activator of ours with the old base's model and `TempleBlessingScript`
   (`TempleBlessing`, `BlessingMessage`, `AltarRemoveMsg` = vanilla's 10E4F9). The blessing is a copy of vanilla's
   Stendarr blessing (Self, Fire and Forget, 28800 s; magnitude 10, as every blessing that is not Health, Magicka or
   Stamina) whose fortify effect is ours: a copy of vanilla's FortifyBlockFFSelf on Resist Disease (vanilla has no
   Resist Disease effect with a duration; the copy keeps its keyword and DispelWithKeywords, so blessings replace
   each other), then vanilla's Cure Disease. The message is ours.
7. Navmesh: the touched exterior cells (placed collision, changed land, path cells) are rebuilt by
   `tools.navmesh` over the patched land and the place's collision (each base read from its plugin where the game
   loads it, the game's Data or the laid stack's mod, so a mod's ship or pier is solid; a collision marker's
   primitive is the box it gives, `build.collision_box`, outside and in a generated room alike; a ref flagged
   `initially_disabled` is built Initially Disabled and is no collision) in a window that grows from three rings until
   its last ring inside the cut comes out byte-equal to the world's own NAVM; the touched cells, ring 1 and every
   cell inside that came out different are ours, so every link out lands on a mesh the world already holds; a
   window still unlike the world six rings out, or a cell whose walkable ground is gone altogether, is a problem. The
   window's stitch runs with `tools.navmesh.stitch.STACKED` on: where a deck or step stands over ground on a cell
   line, seam edges are split and linked by height as well as plan (a neighbour's seam point never snaps to a
   vertex of another surface at the same spot, and two edges with the same ends at different heights both link);
   the world's own build runs with it off, so its bytes stay as deployed. Between our own cells, a link the other
   side does not answer is opened (its row leaves the mesh's link table, so the NVMI lists only meshes it is joined
   to), and every open seam edge is paired with the
   open edge across it that shares the longest stretch of seam at a like height: a portal link both ways.
   An interior keeps its source cell's navmeshes when they make one walkable island (each read from the plugin of
   the source whose version of it wins, the links between them kept, links out of the cell opened); a `room` copy
   takes its room's island from the room rule; an interior whose source has none, or has one in pieces that do not
   join, is generated by the same Recast run over its collision (the plan's notes say which), and one that still
   has no floor is a problem. Door triangles on both sides follow vanilla's rule: the triangle nearest the
   partner's arrival marker in plan and height names the door, on whichever mesh of the space holds it (outside,
   the arrival's cell or one beside it); a prison marker's teleport is an arrest's, never a way people walk, and
   names no triangle. The NAVI override carries our NVMI only.
8. Assemble every shard into the plugin (`ArgoniaPlacesBuild write`); the world ESM is read, never written.

**Deploy** (run by the lead after the owner's walk; the build never deploys): `infra/gpu-box/places_deploy.sh`
(`--dry-run` checks and stages only). It refuses a place whose world records (tools/places/worldparts.py) are no longer those of
`out/newworld/plugin/ArgoniaNewWorld.esm` or a place whose check read another build, prints each place's checks,
builds the plugin's SEQ file (`ArgoniaPlugin seq`: the travel dialogue quest is Start Game Enabled, and the
engine starts a SEQ's quests before a new game's first frame, as `Argonia.seq` does for Argonia.esp), then sends
the plugin to `C:\argonia\ours\newworld\`, the SEQ to `C:\argonia\ours\newworld\SEQ\` and the compiled scripts
(`TIF_ARG_BoatTravel.pex`, compiled with the rest of `papyrus/` by `records_jobs.sh papyrus`) to
`C:\argonia\ours\scripts\`, and runs `stack.ps1 -World NewWorld on`. `stack.ps1` lays `ArgoniaNWPlaces.esp` last
among the NewWorld profile's own plugins (after the world ESM) and the place SEQ in that profile only. Then
`stack.py verify --profile NewWorld`.

`python -m tools.places check <place_id>` reads the built plugin back and fails on any of: a ref not seated as
its `seat` says; a ref inside another's collision that neither rests on the other (`seat.on`, `seat.carrier`: the
one carrier rule, `check.rests`, which the drafter lays joins and flights by) nor stood so in the source; a door without its pair or
facing into a wall; a person without a bed, with a routine stop off the navmesh or unreachable from the one
before, or with a patrol marker off the navmesh or unreachable from the marker before it (a loop's first from its
last); a navmesh island or an unjoined cell edge; a street, path or walkway point (each line sampled every 64
units) or a guard's patrol point off the town's main network. A point stands on a dry triangle of it within 48
units in plan at a level one may stand at there: a walkway piece's own surface (within 48 units of it: the upward
faces of its collision under its `walk` top that join into a surface a person can stand on, 1024 square units or
more, so a post's or a rail's cap is not a deck; a gap in those faces narrower than 48 units, as between a
flight's treads, is a seam of the same surface), the ground or a ford, or, over water too deep to wade with no
deck, a dry triangle right over it. A line's point is taken at the level one reaches it by from the point before
(the nearest in height of those it may stand on), and is off the network when that takes a drop or a climb steeper
than 45 degrees plus a 32-unit step, as off a deck's edge; a line's first point, and a patrol point, is found as a
stop is, the deck first; a land patch whose
built heights differ from `land.jsonl` or tear at a seam; a cleared plant still enabled, or a plant standing in a
building, street or doorway; a service the place record promises with nobody giving it; a Nordic base added from
outside the source place; a copied
room built short of its source (check `rooms`: per room, its built refs and lights against the bundle's cell, the
kept room where a `room` is copied, less the rows the place removes and the loose things the stock takes out, naming
what is missing by plugin); anything levelled (a levelled list in a person's
inventory, outfits, death item or spells, or in a placed container; a level that follows the player; a base whose
template chain reaches a levelled actor list or takes stats or an inventory from a template that scales); a sentence
not as Build step 6 has it (check `jail`: for a jail, the crime faction's JAIL, WAIT, STOL and PLCN not set to our
refs, the jail marker off its room's navmesh, the release point off the town's main network, an evidence chest not in
the jail; for the Owing, JAIL, WAIT and STOL not set to our refs or PLCN set, the work or return spot off the town's
main network, the two markers not leading to each other, the bedroll more than 256 units from the work spot, the
chest within reach, the Owing's line missing from DGCrimeGoToJail, not first, not limited to the faction's guards,
not reading its prompt or not running 020F99's fragment, the resist line missing from DGCrimeResistArrest, not
first, not limited to the faction's guards, not running TIF_ARG_NoSurrender at its start or its Guards not the
place's guard faction (an uncompiled TIF_ARG_NoSurrender.pex is a warning); for a jail, a resist line of ours for
the faction; for both, an evidence chest not empty, respawning or not
the faction's, a guard not in IsGuardFaction and GuardDialogueFaction; a place with neither passes with a note saying
why, unless its law is native, and fails a guard of it in GuardDialogueFaction, whose lines would offer a sentence
it lacks); a copied ref whose source has a primitive neither built with it identical
(type, half extents, colour) nor in the ledger as dropped with its reason (check `primitives`). It also
fails on a link that
resolves nowhere or a plugin not mastered on the world ESM. The promises are the place's rows of
`newworld/story/data/db/place_give.jsonl` (combat, loot and resource gives are not a place's to give). Nordic is,
for a base the source bundle does not hold, the Nordic review's verdict where it lists the base, else a base whose
model lies in Skyrim's hold-city, Nordic farm or Nordic ruin folders, or whose editor id carries their kit prefixes
(decision 0006). Results go to `out/places/shards/<place_id>/check.json`, which the new world's
read-back (`tools/newworld/verify.py`, area `places`) reports. Water triangles join the network as Skyrim.esm's do (in Tamriel 16,729 water-dry shared edges and 1,670 water-dry
edge links, measured: actors wade and swim them); a street or a patrol is never laid along water deeper than a ford
(`WADE`, 64 units, half the agent's height). The geometry is one: a ref is inside another
when its origin is within 0.8 of the other's record box in plan under the other's full three-axis rotation and
within its height; a standing point (arrival, stop) is inside a body only below its top by more than 16 units.
`python -m tools.places draft <stage> <place_id>` runs one stage of the draft alone on the place files as they
stand (`tools/places/draft/stages.py`): `fit` (each piece in its source cluster, a light in its fixture's, standing
where that cluster stands now), `pieces` (`draft.replace` and `draft.drop`), `seating` (seat rules and heights),
`clearance` (`clear.jsonl`), `streets` or `join` (the source's steps hung on their decks, residents' promises,
names, then the built network: flights, joins, arrivals, work stops, streets and patrols), `people` (promises and
names), `lights` (added stations' lights, each room's lights on the source's own bases, `place.json` `lights`:
`{added:[{id, base, on}]}`), `stations` (a promised station the files lack), `jail` (by the place's
law, the jail room's cell, prison markers, bedroll and evidence chests, or the Owing's spots, prison markers,
bedroll and chest, and the crime row's `law`, `jail` and `owing`: Build step 6), `primitives` (each
copied ref's primitive by its class, `tools/places/draft/primitives.py`: a collision marker is kept when its box touches
or holds the record box of a kept building, static, furniture, door, activator or container, and then stands at its source offset from the nearest such piece, turned with that piece's cluster and
seated `on` it (as a light with its fixture; `fit` and `seating` leave it to this stage); one that met only the
source's ground, trees and rocks is dropped with that reason, our ground not being the source's; room, portal and
plane markers, multibounds, acoustic spaces and other volumes are written; a trap's trigger stays with its trap; a trigger
with a script whose activation reaches nothing the place keeps, no ref following it and no link, is dropped with its
reason in the ledger, a copied room's as a `removed` row). A whole draft runs `primitives`, the join, then `jail`. A stage writes only the
rows and fields it owns. After a stage runs the tool checks that; if the stage wrote anything else, the tool
restores the files and fails. A row a
finalised save under `edits/` touched is kept as it stands. The run prints `{file: {changed, added, removed}}`. The
whole `draft <place_id>` refuses a place with finalised saves unless `--force "<why>"` is given.
`draft check <place_id>` runs this same check (the build into `out/places/draft_check/`, then these functions on
that plugin), so a draft that passes it passes `check` on the build; it also mends every street again on that
built mesh and fails if a stretch is re-laid (the streets are settled).

## Finalise

`POST finalise` runs `python -m tools.places finalise <place_id> <save_id>` under `tooling/job_guard.sh`:

1. **Record**: apply the save to the place files and the place's people and stock sources (`apply_save`, which
   also writes its taste ops to `place.json` `preferences`), mark the save final, commit the place and the sources
   by path; with content ops, reload the stock tables and commit them (Stock: Finalise). The applied files are kept
   as `after.json` before they are written, so a run stopped while writing writes the same files again.
2. **Build**: against the current world: `worldparts` decides whether the world moved under the place; if so the
   ground is taken again (`extract --ground`, `ground-check`); then seat, build, check, navexport, and the place layer
   onto the New World card (`infra/gpu-box/places_deploy.sh`, which waits out a live stream); `finalise --plan`
   prints the order. A failed build or check does not undo the record and skips the deploy; the report says what
   failed and what it means.
3. **Learn**: a headless agent (`.claude/agents/place-lessons.md`, `claude -p`, capped at $30 and 60 turns) runs
   the skill `place-lessons` on the save's fault ops and rewrites the skill `place-build` as a clean recipe, which
   the agent writes whole to `out/places/runs/<run_id>/place-build.SKILL.md` (it reads only `faults.jsonl`, the
   save's fault ops, each with its note's words as `note`, and `notes.json`, each of the owner's notes with
   exactly the ops it covers said in plain words) and finalise puts in place and commits as its own commit (one `git revert` removes it). Fault
   content ops are lessons for their own recipes: `identity.edit` for the skill `place-people`, `stock.*` for the
   skill `place-stock`. The prompt names each with its count, and a rewrite the agent writes to
   `place-people.SKILL.md` or `place-stock.SKILL.md` in the run folder is put in place in the same commit; each is
   kept before the agent runs and put back with `place-build` when the agent does not finish. Tool changes it finds are rows in
   `docs/skill-fixes.md`, never code edits. If the agent fails or runs over budget the skill is left as it was,
   the chain completes, and the report says to rerun with `--relearn`.
4. **Report**: `out/places/runs/<run_id>/report.md`, plain English, shown in the studio.

`run_id` is `<place_id>.<save_id>`. Each step writes `<step>.done` in the run folder; a rerun resumes at the first
step without one. `state.json` (`{run_id, place_id, save_id, state: running|done|failed, step, steps:{...},
report}`) and `run.log` are what `GET runs/<run_id>` returns, through `tools.places.finalise.read_run(run_dir)`
(adds `log_tail` and `report_md`); `tools.places.finalise.start(place_id, save_id)` launches the chain under
`tooling/job_guard.sh` and returns the `run_id`. A conflicting save stops the chain at record with state `failed`
and a report; nothing is applied.
