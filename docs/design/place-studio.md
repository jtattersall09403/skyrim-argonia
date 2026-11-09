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
  `{source_id, title, plugins:[...], worldspace, cells | location | marker+radius, extra_refs_plugins, notes}`.
- A place's allocation is `newworld/places/<place_id>/place.json`:
  `{place_id, source_id, similar:[source_id...], ...}`. nw-04 fills these for every place; the tools read them
  and nothing else.
- Base forms are keyed `"<Plugin file>:<6-hex local form id>"` (`Black Marsh.esm:0D794B`). Placed refs of a
  source use the same key shape. Our own placed things have ids we mint (`<place_id>.<ulid>`), stable for life.

## Units and axes

Everything on disk and over the API is in Skyrim's own terms: game units, Z up, positions absolute in the
worldspace, rotations as the record's three angles in radians, scale as the record's float. One shared function
pair (Python `tools/places/xform.py`, JavaScript `web/xform.js`, the same test vectors) turns a record's
position, angles and scale into a matrix; nothing else does that maths. The browser converts to its own axes
only at render time.

## Bundles (derived, never committed)

A bundle is one place as data, in `out/places/bundles/<bundle_id>/`; `bundle_id` is `src.<source_id>`,
`ground.<place_id>` or `draft.<place_id>` (the place files resolved for viewing). The studio shows any bundle.

```
bundle.json            {bundle_id, kind: source|ground|draft, title, plugins, worldspace, anchor:[x,y,z],
                        cells:[[cx,cy]...], spaces:[space_id...], stamp:{inputs:{file:sha256}, tool, at}}
bases.jsonl            every base form the bundle's refs use (below)
npcs.jsonl             every actor base the bundle places (below)
spaces/<space_id>/     space_id: "exterior" or an interior cell's editor id
  space.json           {space_id, type: exterior|interior, name, cells, water:{default_height, type}, light, owner}
  terrain.json + terrain.f32   exterior only. Per cell: 33x33 float32 heights (world Z, row-major south to
                        north), water height, the land texture layers (base per quadrant, then alpha layers as
                        17x17 opacity per quadrant), vertex colours
  refs.jsonl           one placed ref per line (below)
  navmesh.jsonl        one navmesh per line: {id, cell, verts:[[x,y,z]], tris:[[a,b,c,flags,cover]],
                        edge_links, door_links}
```

A ref: `{id, base, kind, pos:[x,y,z], rot:[rx,ry,rz], scale, layer, flags:[...], door:{to_space,to_ref,to_pos,
to_rot}?, owner?, linked:[{ref,keyword}]?, enable_parent?, lock?, src?}`.
`kind` is one of `building, static, clutter, tree, plant, groundcover, rock, furniture, door, container, light,
activator, marker, actor, water, other` and is decided once, in the extractor, from the record type and the
model. `layer` is `world` (the generated world's own refs: plants, rocks, scatter) or `place`.

A base: `{key, edid, type, name, model, bounds:[min,max], plugin, keywords:[...], nordic: bool, door:{},
furniture:{markers}, light:{radius,colour}, container:{}, tree:{}, ...}`. `model` is the path under `meshes/`,
lower case.

An actor base: `{key, edid, name, race, sex, template, class, factions:[{faction,rank}], voice, outfit,
services:{vendor, trainer, innkeeper...}, packages:[...as the record has them...]}`.

The ground bundle is the proof of "the real world": it is extracted from `out/newworld/plugin/ArgoniaNewWorld.esm`,
its stamp carries that file's sha256, and `tools.places ground-check` fails unless that sha equals the play
machine's (`out/newworld/verify/play-esm.sha256`). The studio shows the sha and the check's result.

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
paths.jsonl            streets and paths: {id, kind, points:[[x,y]...], width, style}
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
| `ref.add` | `ref` (whole row; `src` set when copied from a source ref, `base` when from search) |
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
                                              stamps:{draft, ground, source}
GET  /api/bundle/<bundle_id>/...              the bundle's files as written
GET  /api/asset/mesh?model=<path>             GLB (converted on demand; 202 + Retry-After while converting)
GET  /api/asset/tex?path=<path>&size=<n>      WebP (the same 202 rule)
GET  /api/asset/thumb?model=<path>            WebP thumbnail of a mesh (the same 202 rule)
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
                                              log (tail), report (markdown, when done)}
GET  /api/place/<id>/seat?x=&y=               ground height, water height, slope at a point (the same code as seat)
POST /api/heartbeat                           an open tab, every 60 s; {held, started, release_after_s}
GET  /api/status                              {ground_sha, deployed_sha, match, error?, versions:{studio, repo_head,
                                              python, aiohttp, search_model, search_rows}, awake:{job_alive}}
```

Errors are `{error}` with a plain-English message. A part not built yet answers 503. Bundle, web and asset files
carry ETags, honour range requests, and are sent brotli- or gzip-compressed when the browser accepts it and no
range is asked.

**The server** (`tools/places/studio`, aiohttp) calls each other part through one function
(`tools/places/studio/links.py`): `tools.places.assets.mesh(model)`, `tex(path, size)` and `thumb(model)` return
the converted file's path, or None once conversion has started; `tools.places.seat.ground_for(place_id).at(x, y)`;
`tools.places.ground_check.status()` returns `{ground_sha, deployed_sha, match}`. Finalise runs under the job
name `places-finalise-<run_id>` with `ARGONIA_RUN_ID` set; the chain writes `out/places/runs/<run_id>/state.json`
`{state, step}` as it goes and `report.md` at the end; the server adds `run.json`.

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

1. **Record**: apply the save to the place files, mark the save final, commit.
2. **Build**: seat, build, navmesh, check.
3. **Learn**: a headless agent runs the skill `place-lessons` on the save's fault ops and rewrites the skill
   `place-build` as a clean recipe, in its own commit. Taste ops are written to `place.json` as that place's
   preferences.
4. **Report**: `out/places/runs/<run_id>/report.md`, shown in the studio.

Each step writes its stamp; a rerun resumes at the first step without one.
