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
                        ltex:{key:{edid, plugin, diffuse, normal, grasses:[{key, edid, model}]}}}.
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
land.jsonl             land patches: {cell, verts:[[row,col,dz]...], textures?, why}; the last resort
paths.jsonl            streets and paths: {id, kind: path|street, points:[[x,y]...], width, style}; style is a land
                       texture key (the source place's own road texture) or the draft's style word (dirt, boardwalk)
people.jsonl           one person per line: {id, name, base_from, role, home, bed, work, services, faction_ranks,
                       routine:[{start, hours, kind, at:{space, ref | pos, radius}, days?}], patrol?}
edits/<save_id>.json   a studio save (below); finalised saves stay here as the lessons' evidence
```

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
- `veg.clear` writes `by: owner` unless the item names `by`; `veg.restore` items carry the `by` they had, so the
  inverse restores it.
- Rows are kept in one order (refs, paths and people by id, land by cell, clearance by base and position), so
  independent ops give the same files in any order. Floats match within 0.001.
- An op whose `before` (or the row it names) does not match the files is a conflict: the save is not applied and
  the error names the op. Every op has an inverse; a save then its inverse gives back the files.
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
                                              wrote it, or null: the studio's linked views map through it)
GET  /api/bundle/<bundle_id>/...              the bundle's files as written
GET  /api/asset/mesh?model=<path>&level=0|1   GLB (converted on demand, off the event loop);
                                              level 1 is the light version (trees, plants, far away)
GET  /api/asset/tex?path=<path>&size=<n>      WebP; cached a month (immutable: the GLBs' texture URIs)
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
                                              current:{rev, at, name}} when the save moved on since (another tab)
                                              or is final. save_id: [a-z0-9][a-z0-9._-]*; "autosave" is the autosave
POST /api/place/<id>/finalise {save_id}       starts the chain; 202 {run_id}
GET  /api/place/<id>/runs/<run_id>            {run_id, save_id, state: starting|running|done|failed, step, rc,
                                              log (tail), report (markdown, when done)} plus every
                                              field of finalise.read_run (steps, log_tail, report_md)
GET  /api/place/<id>/seat?x=&y=               ground height, water height, slope at a point (the same code as seat)
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

**Saves.** Writes are atomic. A named save is committed and pushed by path (`tooling/lane_commit.sh`) after each
write, so it survives a stopped machine and a lost disk; the autosave goes to the private bucket at most once a
minute.

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
nothing is dropped.

**Textures.** DDS (BC1 to BC7, uncompressed) to lossy WebP, halved to the largest power of two not over the
requested size (64 to 2048); alpha kept on diffuse textures, dropped on normal maps and land textures.

**Cache.** `out/places/assets/{mesh,tex,thumb}/`, each file keyed by the sha256 of its source bytes and the
converter's version; atomic writes, one conversion per key at a time; least recently used files deleted above
`ARGONIA_ASSET_CAP_MB` (default 4096). `python -m tools.places assets warm <bundle_id>...` converts everything the
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
loaded are copied in as ours (the route `tools/ArgoniaPlugin/ForeignCopy.cs` proves). Never LOD.

`python -m tools.places check <place_id>` reads the built plugin back and fails on any of: a ref not seated as
its `seat` says; a ref inside another's collision that the source did not have; a door without its pair or
facing into a wall; a person without a bed, with a routine stop off the navmesh or unreachable from the one
before; a navmesh island or an unjoined cell edge; a land patch whose built heights differ from `land.jsonl` or
tear at a seam; a cleared plant still enabled, or a plant standing in a building, street or doorway; a service
the place record promises with nobody giving it; a Nordic base; anything levelled.

## Finalise

`POST finalise` runs `python -m tools.places finalise <place_id> <save_id>` under `tooling/job_guard.sh`:

1. **Record**: apply the save to the place files (`apply_save`, which also writes its taste ops to `place.json`
   `preferences`), mark the save final, commit the place by path.
2. **Build**: seat, build, check (a verb not yet built is reported as not available). A failed build or check
   does not undo the record; the report says what failed and what it means.
3. **Learn**: a headless agent (`.claude/agents/place-lessons.md`, `claude -p`, capped at $30 and 60 turns) runs
   the skill `place-lessons` on the save's fault ops and rewrites the skill `place-build` as a clean recipe, which
   finalise commits as its own commit (one `git revert` removes it). Tool changes it finds are rows in
   `docs/skill-fixes.md`, never code edits. If the agent fails or runs over budget the skill is left as it was,
   the chain completes, and the report says to rerun with `--relearn`.
4. **Report**: `out/places/runs/<run_id>/report.md`, plain English, shown in the studio.

`run_id` is `<place_id>.<save_id>`. Each step writes `<step>.done` in the run folder; a rerun resumes at the first
step without one. `state.json` (`{run_id, place_id, save_id, state: running|done|failed, step, steps:{...},
report}`) and `run.log` are what `GET runs/<run_id>` returns, through `tools.places.finalise.read_run(run_dir)`
(adds `log_tail` and `report_md`); `tools.places.finalise.start(place_id, save_id)` launches the chain under
`tooling/job_guard.sh` and returns the `run_id`. A conflicting save stops the chain at record with state `failed`
and a report; nothing is applied.
