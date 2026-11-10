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
| Build | `tools/ArgoniaPlaces/Build` (C#, Mutagen), `python -m tools.places build` | Place files → `out/places/plugin/ArgoniaNWPlaces.esp`, navmesh, checks |
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
                        (Skyrim grows grass from the land textures' grass lists; it is not placed as refs); an
                        interior adds key, plugin, lighting_template, flags
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
src?, cell?, map_marker?, primitive?, radius?, loc_ref_types?, count?, patrol?, persistent_location?,
merchant_container?}`. In a bundle `src` is the plugin whose version of the ref wins and `cell` the exterior cell;
flags are `persistent, initially_disabled, visible_when_distant, high_priority_lod, multibound, no_respawn,
open_by_default, ignored_by_sandbox`.
`kind` is one of `building, static, clutter, tree, plant, groundcover, rock, furniture, door, container, light,
activator, marker, actor, water, other` and is decided once, in the extractor, from the record type and the
model. `layer` is `world` (the generated world's own refs: plants, rocks, scatter) or `place`.

A base: `{key, edid, type, kind, name, model, bounds:[min,max], plugin, keywords:[...], nordic: bool, door:{},
furniture:{markers}, light:{radius,colour}, container:{}, tree:{}, flora:{}, water?}`. `model` is the path under
`meshes/`, lower case; `plugin` is the plugin whose version of the base wins. `nordic` (decision 0006) is true when
the model path or editor id names a Nordic culture, hold town or Nordic dungeon kit (nord, draugr, barrow,
Whiterun, Windhelm, Riften, Solitude, Markarth, farmhouse and the like) and not a non-Nordic kit (Dwemer, Dunmer,
Imperial, Ayleid, Falmer), whatever plugin carries it, or when it is architecture from Skyrim's own masters outside
those kits.

The folder rule is a first sort, not a look: a pile of leaves from Riften's folder is not a Nordic element. The
verdict, once a base has been looked at, is `newworld/places/nordic_review.jsonl`, one row per base: `{base (key),
edid, model, verdict: "nordic"|"neutral", why (one line: what it looks like), replace?: {base, turn_deg?}}` (the
standard non-Nordic piece that stands in for it). A reviewed verdict outranks the folder rule everywhere: the
drafter (`io.place_bases`), `draft check` and the build's read-back check all read it, and an unreviewed base keeps
the folder rule. The draft replaces a Nordic base by its `replace` (a place's own `draft.replace` over it), in the
exterior and inside every interior copy alike, or drops it with a ledger reason. The table grows as sources are
drafted: look at each newly flagged base's thumbnail and add its row.

An actor base: `{key, edid, name, short_name, race, race_edid, sex, flags, level, template, template_flags, class,
class_edid, factions:[{faction,edid,rank}], crime_faction, voice, outfit, sleep_outfit, ai, keywords,
services:{vendor:{faction, buy_sell_list, container, values, location}, trainer:{skill,max}, innkeeper, guard},
packages:[{key, edid, plugin, via: npc | default_list:<list>, template, template_edid, type, flags, interrupt,
speed, schedule:{month, day_of_week, date, hour, minute, duration_minutes}, data:{index:{$type, ...}},
procedure_tree, idles, conditions, owner_quest, combat_style, on_begin, on_end, on_change}]}`: the packages as the
records have them, every link a key.

`python -m tools.places extract <source_id>` writes `src.<source_id>`: every ref of every loaded plugin in the
extent's cells (the world's persistent refs placed by position), the land of each cell, the navmeshes, and every
interior reached through the extent's doors, followed door to door but never into an interior that opens onto
exterior ground outside the extent (listed in `not_followed`). `extract --ground <place_id>` writes
`ground.<place_id>` from the place table alone: our world file's cells within 500 m plus half the allocated
source's `extent_m` (300 m when none is allocated) plus 50 m of the place's `world_x, world_y`, every ref with layer
`world`. A rerun whose key (the plugins' sha256, the extractor's own hash, the job) is unchanged does nothing; a
changed one writes beside the old bundle and replaces it in one rename.

The ground bundle is the proof of "the real world": it is extracted from `out/newworld/plugin/ArgoniaNewWorld.esm`,
its stamp carries that file's sha256, and `python -m tools.places ground-check <place_id>` fails unless that sha
equals the play machine's (`out/newworld/verify/play-esm.sha256`, the machine's copy hashed back by
`infra/gpu-box/lod.sh send`). An absent, malformed or stale record fails with what to run, never a silent pass; a
bundle behind the ESM built here fails with the re-extract to run. `ground_check.check(place_id)` returns
`{ok, reason, ground_sha, built_sha, play_sha, play_recorded_at, built_at}`; the studio shows it.

## Place files (ours, committed): `newworld/places/<place_id>/`

The source of truth for a built place. Rows carry our own decisions (where, which way, who) and point at the
source for everything copied; no record or asset content of a mod is written here.

```
place.json             allocation, the fit (how the source's frame maps onto ours, per cluster), the ground stamp
                       the draft was seated on, the build key
spaces/<space_id>/refs.jsonl     the place layer's refs, same row shape as a bundle ref, plus
                       seat:{mode, dz, on?} (how it sits: on ground, on a ref, at source's height above ground,
                       in water, free) and src (the source ref it came from, if any)
spaces/<space_id>/space.json     interiors: {copy_of: "<source_id>/<space_id>"}; the refs file holds only our
                       changes to the copy (moved, removed, added)
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
                       patrol stop's route is `patrol`). services: [{kind | give_kind_id, detail, skill?, level?,
                       room_bed?}]; faction_ranks: [{faction: a form key or <place_id>.<name>, rank}]. Any other
                       shape is a problem `build --plan` lists, never a crash
identities.jsonl       the people's light identities, one row per person id of people.jsonl: {id, name, household:
                       {id, role: head|partner|elder|sibling|grown child|cousin|lodger|levy}, trade, wealth: W1..W5,
                       backstory (one or two sentences), cites: [a repo path | place_note:<place>/<aspect> |
                       place_give:<place>/<seq> | culture:<id> | region:<id>]}. Written by an agent from the lore and
                       the place record; the drafter writes each row's name onto its person (a person without a row
                       keeps the drafter's placeholder). `python -m tools.places identities check <place>` proves it:
                       a row per person, names unique and by the naming rules, a household under one roof with one
                       head and the drafter's head and partner, guards in the levy, every cite existing
ledger.jsonl           one row per source ref: {src, space, status: placed|adapted|replaced|dropped, as?, why?,
                       cluster?, patch?}; every source ref has one
edits/<save_id>.json   a studio save (below); finalised saves stay here as the lessons' evidence
```

Seat rule `seat:{mode, dz, on?, foot?}` (one function, `tools/places/seat.py`): `ground` z = lowest ground under
the footprint + dz; `clear` z = highest ground under the footprint + dz (a raised thing whose underside cleared the
ground everywhere); `above` z = ground at the origin + dz; `water` z = water surface + dz; `stilts` z = lowest of
max(ground, water) under the footprint + dz; `on` z = the ref `on`'s z + dz; `free` z kept (interiors). `foot` is
the true footprint `[x0, y0, x1, y1]` in the ref's own frame (not centred on the origin), from the model's own
geometry (`seat.model_bounds`, cached in `out/places/footprints.json`); every footprint test calls it. dz is
measured in the source the same way.

`place.json` also holds: `draft` (the agent's calls: `anchor`, `rot_deg`, `search`, `replace`, `drop`, `add`,
`roles`, `keep_patches`; skill `place-build`), `fit` (global and per-cluster transforms, `clusters_info`,
`relief_norm`, `patch_max`),
`clearance` (the source's measured clearance), `factions` (`<place_id>.crime`, `.guard`, `.town`, and one
`.vendor.NN` per trader with hours and `chest`), `stations` (needed, found, missing, added: {station, id, base,
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

Seating is data, never baked: `pos[2]` is what the last seating wrote, and `python -m tools.places seat` rewrites
it from `seat` and the ground bundle. A ground rebuild is followed by `seat`, `build`, nothing else.

## Edits

The studio never writes place files. It keeps an ordered list of operations; undo and redo move a cursor in it; a
save is the list up to the cursor.

`edits/<save_id>.json`: `{save_id, place_id, name, at, rev, final: bool, base:{draft_key, ground_sha}, ops:[...]}`.
`rev` is raised by the server on every write. The autosave is the same shape at `out/places/autosave/<place_id>.json`
(on disk and in the private bucket, never committed).
An op: `{n, at, op, space, call: "fault"|"taste", note?, stroke?, ...payload with before and after}`.

| op | payload |
|---|---|
| `ref.add` | `ref` (whole row; `src` set when copied from a source ref, `base` when from search); the first op into a space the place does not have yet carries `space_copy_of: "<source_id>/<space_id>"` and `space_name`, which become that interior's `space.json` |
| `ref.remove` | `id`, `before` |
| `ref.move` | `id`, `before:{pos,rot,scale,seat}`, `after:{...}` |
| `veg.clear` / `veg.restore` | `items:[{base,pos}]` |
| `land.patch` | `cell`, `verts:[[row,col,before_z,after_z]]`, `tool:{kind: raise|lower|level|smooth, radius, strength}` |
| `path.add` / `path.remove` / `path.edit` | `path`, `before?` |
| `person.add` / `person.remove` / `person.edit` | `person`, `before?` (placement, routine stops, patrol points) |

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
- Rows are kept in one order (refs, paths and people by id, land by cell, clearance by base and position), so
  independent ops give the same files in any order. Floats match within 0.001.
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
                                              [{id, space, base, name, kind, pos, src}], view: {space, at}, done,
                                              done_at, reply}]
POST /api/place/<id>/notes                    {text, things, view} adds a note; {id, done} closes or reopens one.
                                              Kept in the place's edits/notes.jsonl (outside the draft's and the
                                              build's identity) and committed by path. An agent lists the open
                                              notes with `python -m tools.places notes`, makes the change, and
                                              closes each with `notes done <place> <id> --reply "..."`
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
them, as Dragonborn's Apocrypha mist in `dlc02\dungeons`), things with no model (markers, triggers, sounds) and any part of a
model under a node named `EditorMarker` (the Creation Kit's own marker shapes, as on mist, fog and trap gas). Grass
is grown as the game grows it, from each land texture's grass list (`grass.js`, rules in `grass_rules.js`): a ring
round where the view looks, out to the view's distance (at most 16,000 units), every spot near the eye and, beyond
4,500 units, a spot kept with chance (4500 / d)^2 and drawn up to twice the size, so the ground keeps its cover for at
most 6,000 blades; none once the view stands back past 30,000 units, and none from a model the converter could not
read. Drawn paths are painted as the build paints them (`path_paint.js`, numbers tested against `build.py`): one
more alpha layer of the style's land texture (a style word picks the land texture whose editor id ends with the
build's word for it), opacity 1 within the half width feathered to 0 over 96 units at each land grid point, tiled and
lit like the ground; a boardwalk only ashore. Each view has a compass at its lower left (the needle points north on
screen; a tap turns the view to face north), and the Selected panel gives the position in game units, the cell
(floor of position / 4096, outside) and the turn in degrees, or the middle of several things, kept current as they
move.

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

**Hosting.** `https://studio.<domain>` (the Moonlight gate's zone): the named tunnel `argonia-build` to
`localhost:8765`, behind Cloudflare Access for the owner's email only; the VM opens no port.
`infra/build-vm/studio-install.sh` installs the pinned cloudflared and the user units `argonia-studio` and
`argonia-studio-tunnel` (started at boot, restarted on failure); `infra/build-vm/studio_gate.py apply` makes the
tunnel, DNS and Access app and `prove` checks both sides of the gate.

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
2. Interiors: `space.json` `copy_of` names the source cell (each of the source's plugins that holds it adds its
   refs; read once and cached under `out/places/srccells`). `room` (one of the cell's load doors that lead out)
   keeps only that room of a cell the source shares between houses, by the room rule: the whole cell's collision
   (doors open) is meshed by the world's own Recast run; the room is the walkable island reached from its door;
   every source ref belongs to the door island its position is nearest, islands of every door of the cell
   competing, so refs behind a door that leads nowhere fall in no room. No hand numbers; cached under
   `out/places/rooms` by the source refs' hash. Measured on BM&V's `01ArgonianHouseinside` (nine houses in one
   cell, no source navmesh joining door to floor): nine islands of 206 to 278 triangles, 6 beds in each room,
   every ref at least 2,093 units nearer its own room than the next. A row with `src` changes that copied ref
   (`removed: true` drops it; `base`, `pos`, `rot`, `scale`, `owner`, `door` replace the source's); a row with a
   `src` outside the kept room is not in the copy; a row without `src` is added. A copied ref whose base is still
   the source's keeps what the source ref itself says of it: a light's radius and light data, an item count, a
   charge, open by default, ignored by sandbox, its lock's key. Any row's own `radius` and `count` (the ref
   shape's) are built as given, in a room or outside. Source actors are never copied: people are ours.
3. Doors: a door pair is one row on each side (the exterior door, and the copy's override of the source door it
   leads to) whose `door.to_space` and `to_ref` (our id, or a source key in a copied space) name each other; one row
   naming its partner is enough, and both get teleports. One using door x lands at x's `door.to_pos` and `to_rot`
   (a point in the partner's space beside the partner) when the place files give it; else at the source pair's
   marker (a copied door), the source's marker moved rigidly from the source door to ours (our door whose partner
   is a copy), or 128 units in front of the partner. A source load door of a copy with no partner row is built as
   a plain door.
4. Land: each `land.jsonl` vertex (`row` from the south, `col` from the west, `dz` in units, rounded to 8-unit
   steps) is applied to the world's own heights; every cell whose heights or normals change gets a LAND override
   (the world's record with new VHGT and VNML, the normals computed as the world computes them). Paths paint one
   alpha layer per quadrant of the world's own LTEX for their `style` (`road`, `street`, `path`: dirt_road;
   `track`: dirt_grass; `mud`, `sand`, `stone`, `skirt`), opacity 1 within the half width, feathered over 96 units.
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
   owned by them; everyone in the place's crime faction (TrackCrime, vanilla's crime values), guards also in
   IsGuardFaction. A stop names a ref (our id or a source key in its space), a position (2D, outside only, is
   seated on the built land: the world's heights with the place's land patches, between the cell's vertices), or
   only a space (where one arrives in it by a load door, else its first furniture). A person whose day starts on
   patrol stands at the patrol's first point and keeps home there; every patrol stop of a day walks the one chain,
   and each marker of a chain leads on to one marker only (a patrol point that names a ref another route already
   leads on from is a problem). Services by give (`give_kind_id` or `kind`): `trader-*` a
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
   Boat travel (`carriage-or-boat`): one Papyrus script of ours, `papyrus/TIF_ARG_BoatTravel.psc`, serves every
   boatman's line by its properties (`Destination` marker, `Fare`): each destination is an INFO whose script data
   names that one script, conditioned on the boatman's faction and the player's gold; fares as vanilla's
   carriages (20 gold to a city, 50 to anywhere smaller); a destination not built yet arrives at its map marker.
   Built by `build.py plan_boats` and `ArgoniaPlaces/Build/Boat.cs` as vanilla's DialogueCarriageSystem is (measured:
   a start-game-enabled quest holding the topics; each destination INFO gates on GetGold >= the fare, run on the target,
   and CarriageCost is 20, CarriageCostSmall 50): the boatman (role `boatman`, give `carriage-or-boat`) gets a boatman
   faction of ours from `people.py`; per place a quest of ours; per boatman a top-level topic "I need passage." (his
   faction on the subject) whose line links one topic per destination; a destination INFO needs the faction and the
   gold and carries `TIF_ARG_BoatTravel` (`Destination` = the destination's `ANW_MapMarker_<place>` ref in the world
   ESM, read from it; `Fare`; `Gold001` = Skyrim.esm 00000F) with fragment `Fragment_0` on OnEnd. The destinations are
   the names in the give's `detail` after its last "to" (place_give has no destination column), matched to
   place.jsonl by name or map label; fare by the place's kind. check reads quests, topics, INFOs, conditions and
   script properties back (`dump`) and fails a boatman that lacks any of it; the compiled
   `out/gpu/papyrus/TIF_ARG_BoatTravel.pex` is warned about when absent.
   Shrines (`build.py plan_shrines`, `ArgoniaPlaces/Build/Shrine.cs`): each `shrine` row of `stations.added` is built
   as vanilla's temple shrines are (measured on Skyrim.esm's ten TempleBlessingScript activators): the ref keeps its id
   and form key; its base becomes an activator of ours with the old base's model and `TempleBlessingScript`
   (`TempleBlessing`, `BlessingMessage`, `AltarRemoveMsg` = vanilla's 10E4F9). The blessing is a copy of vanilla's
   Stendarr blessing (Self, Fire and Forget, 28800 s; magnitude 10, as every blessing that is not Health, Magicka or
   Stamina) whose fortify effect is ours: a copy of vanilla's FortifyBlockFFSelf on Resist Disease (vanilla has no
   Resist Disease effect with a duration; the copy keeps its keyword and DispelWithKeywords, so blessings replace
   each other), then vanilla's Cure Disease. The message is ours.
7. Navmesh: the touched exterior cells (placed collision, changed land, path cells) are rebuilt by
   `tools.navmesh` over the patched land and the place's collision (a ref flagged `initially_disabled` is built
   Initially Disabled and is no collision) in a window that grows from three rings until
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
   the arrival's cell or one beside it). The NAVI override carries our NVMI only.
8. Assemble every shard into the plugin (`ArgoniaPlacesBuild write`); the world ESM is read, never written.

**Deploy** (run by the lead after the owner's walk; the build never deploys): `infra/gpu-box/places_deploy.sh`
(`--dry-run` checks and stages only). It refuses a plugin built over another world ESM than
`out/newworld/plugin/ArgoniaNewWorld.esm` or a place whose check read another build, prints each place's checks,
builds the plugin's SEQ file (`ArgoniaPlugin seq`: the boatman's dialogue quest is Start Game Enabled, and the
engine starts a SEQ's quests before a new game's first frame, as `Argonia.seq` does for Argonia.esp), then sends
the plugin to `C:\argonia\ours\newworld\`, the SEQ to `C:\argonia\ours\newworld\SEQ\` and the compiled scripts
(`TIF_ARG_BoatTravel.pex`, compiled with the rest of `papyrus/` by `records_jobs.sh papyrus`) to
`C:\argonia\ours\scripts\`, and runs `stack.ps1 -World NewWorld on`. `stack.ps1` lays `ArgoniaNWPlaces.esp` last
among the NewWorld profile's own plugins (after the world ESM) and the place SEQ in that profile only. Then
`stack.py verify --profile NewWorld`.

`python -m tools.places check <place_id>` reads the built plugin back and fails on any of: a ref not seated as
its `seat` says; a ref inside another's collision that the source did not have; a door without its pair or
facing into a wall; a person without a bed, with a routine stop off the navmesh or unreachable from the one
before, or with a patrol marker off the navmesh or unreachable from the marker before it (a loop's first from its
last); a navmesh island or an unjoined cell edge; a street, path or walkway point (each line sampled every 64
units) or a guard's patrol point off the town's main network (over a walkway piece, on no dry triangle within 48
units of the deck's own surface: the upward faces of its collision under its `walk` top that join into a surface a
person can stand on, 1024 square units or more, so a post's or a rail's cap is not a deck; over water too deep to
wade with no deck, on no dry triangle right over it; on land or in a ford, as a stop is found); a land patch whose
built heights differ from `land.jsonl` or tear at a seam; a cleared plant still enabled, or a plant standing in a
building, street or doorway; a service the place record promises with nobody giving it; a Nordic base; anything levelled (a levelled list in a person's
inventory, outfits, death item or spells, or in a placed container; a level that follows the player; a base whose
template chain reaches a levelled actor list or takes stats or an inventory from a template that scales). It also
fails on a link that
resolves nowhere or a plugin not mastered on the world ESM. The promises are the place's rows of
`newworld/story/data/db/place_give.jsonl` (combat, loot and resource gives are not a place's to give). Nordic is
the Nordic review's verdict for a base it lists, else a base whose model lies in Skyrim's hold-city, Nordic farm
or Nordic ruin folders, or whose editor id carries their kit prefixes (decision 0006). Results go to `out/places/shards/<place_id>/check.json`, which the new world's
read-back (`tools/newworld/verify.py`, area `places`) reports. Water triangles join the network as Skyrim.esm's do (in Tamriel 16,729 water-dry shared edges and 1,670 water-dry
edge links, measured: actors wade and swim them); a street or a patrol is never laid along water deeper than a ford
(`WADE`, 64 units, half the agent's height). The geometry is one: a ref is inside another
when its origin is within 0.8 of the other's record box in plan under the other's full three-axis rotation and
within its height; a standing point (arrival, stop) is inside a body only below its top by more than 16 units.
`draft check <place_id>` runs this same check (the build into `out/places/draft_check/`, then these functions on
that plugin), so a draft that passes it passes `check` on the build.

## Finalise

`POST finalise` runs `python -m tools.places finalise <place_id> <save_id>` under `tooling/job_guard.sh`:

1. **Record**: apply the save to the place files (`apply_save`, which also writes its taste ops to `place.json`
   `preferences`), mark the save final, commit the place by path.
2. **Build**: seat, build, check (a verb not yet built is reported as not available). A failed build or check
   does not undo the record; the report says what failed and what it means.
3. **Learn**: a headless agent (`.claude/agents/place-lessons.md`, `claude -p`, capped at $30 and 60 turns) runs
   the skill `place-lessons` on the save's fault ops and rewrites the skill `place-build` as a clean recipe, which
   the agent writes whole to `out/places/runs/<run_id>/place-build.SKILL.md` (it reads only `faults.jsonl`, the
   save's fault ops) and finalise puts in place and commits as its own commit (one `git revert` removes it). Tool changes it finds are rows in
   `docs/skill-fixes.md`, never code edits. If the agent fails or runs over budget the skill is left as it was,
   the chain completes, and the report says to rerun with `--relearn`.
4. **Report**: `out/places/runs/<run_id>/report.md`, plain English, shown in the studio.

`run_id` is `<place_id>.<save_id>`. Each step writes `<step>.done` in the run folder; a rerun resumes at the first
step without one. `state.json` (`{run_id, place_id, save_id, state: running|done|failed, step, steps:{...},
report}`) and `run.log` are what `GET runs/<run_id>` returns, through `tools.places.finalise.read_run(run_dir)`
(adds `log_tail` and `report_md`); `tools.places.finalise.start(place_id, save_id)` launches the chain under
`tooling/job_guard.sh` and returns the `run_id`. A conflicting save stops the chain at record with state `failed`
and a report; nothing is applied.
