# The world rebuild: options for 1.15 (planning record, 2026-11-01)

The owner's question (verbatim in the session): the terrain, water, textures, placed rocks and light are broken in
many ways; consider the options from fresh, including "do nothing"; use the Argonia part of the all-Tamriel
heightmap as a coarse prior, the hydrology graph broadly for the bird's-eye water plan and for classing water,
a terrain that lets Skyrim's native water "just work", and the authored place plot, people and quests on top;
lean on Opus 5.5 as a 3D designer with a clear bar. Nothing is implemented by this record.

## 1. What is actually there (measured this session)

**Terrain.** The "frozen heightfield" is not the all-Tamriel prior. The old project sculpted it: the raw
Tamriel Worldspaces Argonia esp spans -86..+122 m (old 0005); the sculpt chain raised summits to 655 m and carved
every river trench, weir and plunge bowl into it (old 0059, 0060). Measured on `refined-height-f32.npy`:

| Measure (land samples, h > 0) | Value |
|---|---|
| land fraction of the 4033² grid | 0.62 |
| median height / p90 / p99 | 24.9 m / 342 m / 557 m |
| slope median / p90 / share over 45° | 0.18 / 1.00 / 10.0 % |
| land under 2 m / 5 m / 10 m | 12 % / 25 % / 35 % |
| samples where VHGT's int8 overflows (cliffs steeper than 82.9°) | 23,880 pairs, 674 cells |

A tenth of the land is steeper than 45° and the western massif runs to 650 m. That is alpine, not Black Marsh,
and it is where the "large same-texture swathes" come from: MOUNTAIN_ROCK (class 31) is 12 % of all samples and
nothing else can grow there. No texture choice fixes a mountain range.

**Land cover.** `landcover-i16.npy` is the old chain's ground-control red channel: a per-sample class id, 37
classes, median run of 4 samples (7 m) along a row. `paint.py` paints one LTEX per class with a 3×3 box blur
(one vertex of feathering) and keeps at most six layers per quadrant by weight. Hence speckle, hard edges at
class borders, and layer drop-outs at quadrant seams. Both faults are in our painter, not in Tropical Skyrim.

**Water.** The planner (`tools/argonia_world/water`, about 4,000 lines) gives every heightfield sample a water
level, steps each of 615 reaches at ≤ 0.5 m into turned 16 m tiles, lays 20,165 placed `Water1024` activators
and 1,531 vanilla rapids, cascade and falls pieces, and regrades 90,694 vertices to make the ground agree. Its
L1 checks are green. In game the result shows the known faults of placed water activators: planes that end in
the air where the ground falls away ("hovering"), tiles that do not meet ("gaps"), pieces seated by rule on
ground that does not match them, and black rendering where a plane's edge crosses terrain or its own
reflection (the black sawtooth is visible in `out/batch/all/20261030T181841/26-world-sample-1-*/03-s01-probe-east-30m.png`).
The 259 cells the plan could not cover at budget 32 are mapped in `out/water/fallback-causes.png`: steep
reaches, large marshes, junctions and diagonal reaches, i.e. exactly where flat squares cannot follow a
sloping, branching river. Nothing about this is a tuning problem; placed planes "do not know about each other"
(the one firm fact the web research turned up) and every seam has to be hidden by hand.

The inland water is sea-level water: 1,423 bodies are dropped as puddles, 37 are sea, 783 join basins, and the
big northern marsh systems render as the worldspace default water, i.e. the sea WATR at 0. That is why so much
inland water reads as "sea".

**Vegetation and rocks.** Our own placer (470,508 refs) tilts vanilla rocks onto the slope normal and stands
them on the surface. Vanilla rock meshes are open underneath and meant to be sunk; the journal records that the
tilt's sign convention is unproven. Hollow backs are a placer bug, not a design fault.

**Light.** We did change it. Four weathers of ours (mist, tannin haze, squall, storm) derive every colour slot
(sky upper and lower, horizon, fog near and far, ambient, sunlight, sun, clouds) from ONE hex fog tint by a
brightness ladder (`regions/api.py` LADDER), with fog near at 0 m. Our six image spaces add a yellow-green tint
(day `C8BC6A` at 0.12, haze `B89A58` at 0.18) and raise saturation. A one-tint ladder is a monochrome
pea-soup by construction; it reads as the yellow-green fog at Claywater whenever mist or haze is active (5 to
16 % per region per roll), and the day image space yellows the fifteen Tropical Skyrim weathers too.

**What survives any rebuild.** The place plot (830 places, 567 with a position in the province frame; 960
people; 717 quests; 33 factions; the route graph; the hydrology graph's topology and classes) is x, y and
semantics. Only z and the plot facts derived from the ground (landform, distance to water, water level) are
re-derived. The 284 terrain patches, 57 place terrain requests and the old pads are tied to the old ground and
would be dropped.

## 2. The engine facts every option must respect

- One water height per cell (XCLW) is the robust path: it renders, reflects, has LOD (xLODGen writes water
  LOD from it), is swimmable, is seen by the navmesh and by the flora posture, and never gaps. Vanilla rivers
  are cell water stepped at cell boundaries with FXWaterfall and rapids meshes hiding the drops.
- Placed water activators are the fragile path: no LOD, no mutual awareness, seams, black edges, a per-cell
  count that costs frame time. Vanilla uses them sparingly (ponds inside a cell above its water, mill races).
- LAND is 33×33 vertices per cell at 128 units, VHGT int8 deltas (no slope over 82.9°), six alpha layers per
  quadrant, vertex colour (VCLR) for tint.
- Grass is a property of the LTEX record (GNAM), which we already override in Argonia.esm. So "do BM&V's
  textures come with grass?" is the wrong question: any texture file set works with whatever grass list we
  attach; the textures are files the player installs, the grass is our record.

## 3. The options

### A. Do nothing structural: keep the frozen ground and the placed-plane water, and fix the faults

Feather and noise the texture weights, sink the rocks, set XCLW/XCWT on every cell, overlap tiles and bury
their edges, rebuild the weathers with real palettes, hunt each black-water case.

- Pros: no data migration; every L1 check and writer exists; the first fixes (rocks, textures, weather) are
  cheap and needed under every option anyway.
- Cons: the three structural faults stay. The mountains stay alpine. The water stays 20,000 activators that
  must be checked seam by seam in game, in 259 cells that already failed at the plan level. The texture
  speckle comes from the land-cover raster itself, so feathering it gives soft speckle. There is no convergence
  argument: each fix is local and the province has 15,876 cells.
- Biggest risk: months of in-game whack-a-mole, the thing the owner's rulings forbid ("no loads of manual
  testing and tweaking everywhere").
- De-risk: none needed; this is the known path.

### B. Water-first terrain: generate the ground so that cell water fits it by construction (recommended)

Invert the order. Solve the water as **one level per cell** first, then generate the terrain to agree.

1. **Classify the hydrology graph into cell water.** Each body keeps its class from the graph (sea, tidal lagoon,
   sea-level inland marsh, lake at its own level, pond, river reach) and gets a WATR type (sea, brackish,
   blackwater fresh, clear upland). Every province cell gets at most one water height, from a global solve:
   sea cells at 0; lake and marsh cells at the body's level; river cells at a monotone profile **quantised to
   cell boundaries** (a reach is flat inside a cell and drops only at a cell edge, by 0.3 m rapids up to a
   10 m fall). Conflicts (a lake and a river at different levels in one cell) are resolved by moving the step
   to the cell edge before the lake. The sea-level inland marshes stop being "sea": they are cells at 0 with
   a brackish or blackwater WATR and a marsh shore, not the default water.
2. **Generate the terrain from the prior plus the water plan.** The coarse prior (the all-Tamriel Argonia
   block, or the old sculpt low-pass filtered to about 100 m wavelength, with its 650 m massif compressed to a
   Black Marsh profile: border mountains to perhaps 300 m, uplands 60 to 150 m, foothills, a marsh floor under
   10 m) gives the macro shape. Procedural detail (noise by region class, a hydraulic erosion pass, levees
   along rivers, terraces by design not by accident) gives the relief. The water plan is applied as
   constraints: each water cell's ground is carved to its level minus its depth inside the body's footprint;
   a **sill** of ground above the upper level runs along every step boundary so the higher cell's plane ends
   in ground, with the falls or rapids piece seated on the sill where the river crosses; shores rise at a
   designed grade. The int8 limiter is then never needed because no designed slope exceeds it.
3. **Textures by an auto-material**, not by the old raster: per region class a palette of four to six LTEX,
   mixed by slope, height above the nearest water, curvature, a low-frequency noise and a wetness field, with
   soft weights over 10 to 20 m, plus VCLR for wetness and shade. The land-cover raster becomes one input
   (the ecological class), not the paint.
4. **Rocks and flora** keep the region-rule placer with the rock fix (sink by a fraction of bounds, closed-bottom
   forms where visible) and may draw on the old project's tree pool once the dependencies are permitted
   (BM&V's ~700 swamp trees, Tropical Skyrim palms; see §4).
5. **Light** rebuilt from real palettes (§4).

- Pros: the water "just works" with the engine's own system: no planes, no seams, no plane budget, water LOD
  for free, swimming and navmesh exact. The code shrinks (the plane cover, the regrade, the oriented tiles, the
  budget go). Every world fault the owner listed is addressed at its cause. The plot, people and quests carry
  over as x, y. The whole thing is a pure function of the database and two rasters, so it is rebuilt in
  minutes and reviewable at L3 before any game run.
- Cons: throws away about 4,000 lines of water code and the regrade (sunk cost, not a reason). Rivers are
  coarser: no drop inside a cell, so a stream falling 20 m over 300 m becomes five cells with a 4 m fall at
  each edge; meanders inside a cell are flat. Every old terrain patch and place pad is void; the built places
  (Claywater, the slice places' blueprints) are re-seated on new ground, which is a z change and a pad
  regrade per place. 2.W1 to 2.W4's L4 rows reopen.
- Biggest risk: the cell-boundary step reads as "the river staircases every 58 m" in upland reaches; and a
  diagonal river crossing a cell corner needs the sill on two edges. Both are design rules the L3 render can
  show before the game does.
- De-risk on a sample: one river from source to sea plus one marsh system and one lake, about 40 cells,
  generated end to end (terrain, cell water, pieces, auto-material, rocks), rendered at L3 (hillshade, water
  overlay, cross-sections, a Blender render), then one L4 scene list of fixed vantages. The bar is written
  before the sample: no visible plane edge, no black water, every step hidden by a piece, no slope over 45°
  outside designed cliffs, a reader's checklist on the stills.

### C. Keep the frozen ground, re-plan the water as cell water only

Option B's step 1 on today's terrain, with the regrade doing the fitting.

- Pros: smaller change; the terrain data and its checks stay; the place pads survive.
- Cons: the ground was carved for a continuous water field and for 0.5 m steps, so a cell-level plan fights it
  everywhere the 259 fallback cells already show: steep reaches, junctions, large marshes. The regrade grows
  rather than shrinks. The alpine relief and the speckled land cover stay. The look stays.
- Risk: it ends up as A with a different water model.
- De-risk: the same 40-cell sample as B, which would show at once how many cells the regrade cannot fit.

### D. Agent-designed terrain region by region (an execution method, not a separate shape)

The "Opus as 3D designer" path: each of the eight region packets gets a geomorphology brief (what Black Marsh
looks like there: delta, lagoon coast, deep river corridor, flooded forest, upland, border mountain), and an
agent iterates the terrain and the water plan for that region against a written bar, judged first on cheap
L3 renders (hillshade, slope map, water overlay, a Blender flythrough still at the play camera's height) and
then on a fixed set of L4 vantage stills. The code it iterates is option B's generator and its parameters, so
this is how B is run, not an alternative to it. It is the right use of the model: a clear bar, a fast oracle,
one region per lane.

### E. Make the Tamriel Worldspaces Argonia esp a player dependency and build over it

Use the raw prior at 1:1 as the land (it is a free Nexus mod, so the player owns it under 0003) and override
only the cells we change.

- Pros: a real modder's worldspace; the ground exists today; honest to "use the all-Tamriel heightmap".
- Cons: relief of -86..+122 m only (the owner already judged it too flat in 2026-08 and the old project raised
  it); no texture paint, no water design, no regions; a dependency whose permissions and AI clause are
  unchecked; every cell we touch is an override anyway, so we would still be generating the whole thing.
- Verdict: a source of the prior (which we have as an array), not a base.

### F. Use Black Marsh & Valenwood's own Black Marsh worldspace as the land

- Pros: art-directed Black Marsh by a modder, with its textures and trees in place.
- Cons: the old project's rule stands (asset pool, never lift-and-shift their authored world); its Black Marsh
  esps were reportedly pulled and moved; permissions and the AI clause (0006 §7) unknown; it would not follow
  our plot, hydrology or place positions. Rejected as a base; its textures and trees stay candidate assets.

### G. A smaller worldspace first

Build B on the slice's region packets only (the two or three packets with the slice places), the rest left to
the apron and LOD until Part 4.

- Pros: quality per cell, faster loops, fewer cells to judge.
- Cons: the plot spans the province, the route graph crosses it, and the phase plan's "wide load" rule says
  terrain, water, roads and navmesh are filled whole. B's generator is the same whether it runs on 40 cells or
  15,876, so the saving is only in judging, which D handles region by region anyway.
- Verdict: fold into D's region order, not a scope cut.

## 4. The look: textures, plants, light (orthogonal to A to G)

- **Textures.** The "beach" reads come from three things: LCoastBeach and LFieldGrass forms painted over
  large low areas, the sea WATR over inland marsh, and the yellow day tint. Under any option the auto-material
  (B §3) with a darker palette (river mud, peat, fall-forest dirt, marsh grass, moss) does most of it. Whether
  the files are Tropical Skyrim's or BM&V's is a palette choice we can defer: both replace vanilla-named files,
  both work with our grass lists. BM&V's landscape pack is recorded in the old asset strategy as a full
  vanilla-named 512 px repaint, dark, mossy and moody (`90-asset-strategy.md` line 330); its permissions and
  AI clause are unverified (the research agent could not fetch ModDB). An owner-cleared permission check comes
  before any use.
- **Plants and trees.** The old project's pool (BM&V swamp trees, Tropical Skyrim palms, Hoddminir, WOODLAND,
  Project Rainforest) is usable by our placer as mod forms if the mod is a pinned dependency with permission;
  tree LOD then comes from DynDOLOD on the player's machine (0014). Project Rainforest is recorded as
  incompatible with Tropical Skyrim as a whole install, so single forms, not the mod's world edits.
- **Light.** Replace the one-tint ladder with authored palettes per weather and time of day (sky, horizon,
  fog near and far, ambient and sunlight as separate colours, fog near above 0 m except in true mist), and
  cut the image-space tint to a touch. Judge against reference stills (owned games' swamp looks, Morrowind's
  Bitter Coast as mood). This is a data change in `weather` and `image_space` and the LADDER's removal.

## 5. What the research agent found, read critically

Thin (search snippets, one page read). Useful: no community recipe for a generated worldspace exists; no
auto-paint tool exists, so our painter is first of its kind and the Unreal "auto material by slope and
height" is the right model; placed water activators do not join and the community hides seams with banks and
rocks; the black-water causes list (SSR, depth of field, HasWater/XCLW mismatch, missing water LOD) is worth
one controlled reproduction; no evidence anyone has built a Bethesda worldspace with an LLM agent. Not useful:
the layer-limit confusion (we measured six on vanilla) and the BM&V claims (unverified).

## 6. Recommendation

B, executed as D, with the sample first. Order the sample so that each step is judged before the next: the
water plan at L3 (a map), the terrain at L3 (renders), the paint at L3 (a texture-weight render), then one
L4 batch. Keep from today's work the hydrology tables, the region records and their object lists, the placer
(with the rock fix), the navmesh job, the LOD job, the writer and the terrain checks; retire the water planner,
the regrade and the land-cover raster as paint. Fix the light as a data change in the same chunk.

The schedule change the owner asked for (1.15 before 1.14) holds either way: 1.14 is death and the pile and
does not touch the world. 1.15 is rewritten from "close the owed rows" to "the world rebuilt on its sample,
then whole", with a decision record for the water-first terrain, and 2.W1 to 2.W4 reopen under it.

## 7. The two Opus 5.5 perspectives (medium effort; `tmp/opus-a-world-options.md`, `tmp/opus-b-world-options.md`), read critically

Both were given the owner's question verbatim and the same reading list, after this record's §1 to §6 were
drafted. Both recommend the same shape as option B: regenerate the terrain from a smoothed prior so that one
flat water height per cell fits by construction, rivers stepping only at cell edges under one piece, inland
sea-level water held at 0 as its own class, soft slope-and-wetness paint, and a region-by-region agent pass
with a fixed stills panel judged by a reader. That convergence is some corroboration, with the caveat that
the owner's question already points that way, so none of the three answers is an independent discovery.

What they add that this record takes:
- **Two more black-water causes** worth one controlled reproduction: Skyrim computes reflections for one water
  height per frame, so placed planes at other heights can render dark from some angles (Opus B, unconfirmed);
  and placed planes have no distant water at all, so water vanishes at range and the dry bed shows (Opus A).
- **A measured picture of the water** (Opus A): 21 km² of the water is at sea level; 1,085 inland bodies sit
  at 1,085 slightly different levels between 0.5 and 3 m; 37.7 of 62.8 km of river is flat and only 14 km is
  steeper than 5 %. So the cell-level model loses very little: most water is already flat and near 0.
- **An owner call this record missed** (Opus B): whether small upland streams may become dry gullies (bed
  pieces, no water) where one level per cell cannot hold them, rather than a staircase of pools.
- **A reference mood board** of 10 to 20 images, chosen by the owner, as the look oracle for the reader.
- **BM&V is already pinned** (`data/dependencies.json`: Black Marsh.esm, Black Marsh North.esp, Valenwood.esp,
  for buildings, props and creatures), so using its landscape textures and trees is a palette amendment to
  0028, not a new dependency; its permissions and AI clause still need the owner's own check.

What they add that this record does not take:
- Opus A's "use King of the Murkmire's worldspace" and Opus B's "adopt BM&V's worldspace": both lose the plot,
  the hydrology and the place positions, and both contradict 0006 and 0028; a few reference stills of each are
  worth having as mood evidence, nothing more.
- Opus A's "Opus sculpts each region by hand" as a separate option: nothing keeps the water rules or the region
  seams; it is only safe as the agent pass over B's generator (option D here).
- Opus B's "erosion simulation and designed landforms" as a later upgrade: agreed on timing; a light erosion
  pass is already in B's generator for the uplands, and a heavier one is tuning.
- Opus A's "custom water meshes or our own water rendering": ruled out by 0026 and 0028, as it says.

## 8. The owner's reply (2026-11-01) and what it changes

**Rulings** (recorded in the owner brief): B accepted with its costs, executed as D; place seating redone natively
afterwards; the worldspace is built once, whole, then frozen, with patches after and never a rebuild; no smaller
worldspace first; BM&V is the primary look (permissions checked by the owner: ~700 swamp trees, dark landscape
pack); the border ranges are canon and the relief profile is answered from the lore; the golden rule of lore
grounding is decision 0032; fog, haze and mist are authored intentionally with volumetrics from an existing mod or
feature; a mood board of 10–20 images; one water level per cell.

**Corrections to §1.** "Alpine, not Black Marsh" was taste over canon: the Velothi/Valus ranges and the Blackwood
uplands lie inside the province, Shadowfen's dossier says relief lives there (Silyanorn on a mountain flank around
a waterfall, ravines), and the old mountain-synthesis research chose Kinabalu/New Guinea drama on purpose. What
stands is the engine fact: 674 cells overflow the int8 slope limit and must be regraded whatever the profile. And
"the same texture on whole mountainsides" is not a property of mountains: it is the painter mapping one land-cover
class (MOUNTAIN_ROCK) to one LTEX (LRocks01) with no slope, aspect, height or noise variation. Mountainsides in
Skyrim carry four to six textures in bands and patches; the fix is the material rule, not the relief.

**What already exists for D's grounding** (found this turn): the lore dossiers and extrapolation are imported in
full (`world/sources/lore/`, 1.3 MB; `world/IMPORTED_FROM.md` lists no missing path); 48 land regions in the DB
(8 culture regions × eco classes such as coastal-lagoon, deep-sink-basin, interior-swamp, northern-transition),
310 region–weather rows, flora palettes and dressing zones, places in 8 region packets, demographics priors; the
old research record is now imported too (decision 0032): world-terrain (climatology, mountain synthesis, tropical
fluvial geomorphology, rivers on slopes and cascades, shoreline materials, mangrove ecology, beyond-border distant
lands), rendering (ground texture sources, landscape texture granularity, waterfalls, water edges, mist), vegetation
(ecology targets, composition, rock placement rules, regional variety audit), placement-settlements, the lore-facts
audit, the eight per-region reviews (phase16/16g-review) and the archived water, weather and rendering rounds.

**Open questions answered in chat**: what a sill is and why every step needs one; how Skyrim does upland streams;
the most Skyrim-native painting method; volumetric fog options; Blender as an L3 vibe-check renderer.

## 9. Dungeons and caves (owner, 2026-11-01: "an important requirement")

Audit by a research agent of the old plan (`docs/design/world/70-dungeons-interiors.md`, old decisions 0062/0114,
`docs/design/research/placement-settlements/place-purpose-hostility-and-dungeon-balance.md`) against the DB.

**What exists.** Ten families with a spatial grammar each; entrances decoupled from geology (teleport doors in a
mouth mesh: cave-mouth, root-mouth, hollow trunk, sinkhole lip, burrow, stair-throat, well shaft, grave-cut,
underwater entry, trapdoor); typed promises per record (room reveal order, loop type, traversal metres, up to 3
combat spaces, light, lock; two same-family dungeons within 2 km may share at most 3 axes); fixed loot and
enemies, never levelled. In the DB: 327 of 830 places have an interior kind (delve 197, dungeon 95, warren 19,
complex 16); families root-cavern 91, flooded-cave 58, xanmeer-complex 34, sinkhole-ruin 26, burrow-warren 21,
imperial-fort 20, smuggler-den 16, plantation 15, shipwreck 12, ayleid-nedic 11, kothringi 4, hist-sanctum 2;
1,152 room-function rows, 921 sockets, 360 combat spaces; landform requests already typed (ridge-end 60,
flood-high 115, cliff-bench 47, sinkhole 39, ravine 39, gorge 23, box-canyon 17). Two tiers: A = a mod's own
furnished cell reached by that mod's load door; B/C = assembled from kit pieces. Bones and Tools
(`place.saxhleel-coast.jungle-root-hollow`) is tier A: vanilla `rockcaveentrance02` mound (30×32×19.5 m) whose
door loads King of the Murkmire's `MugsumpHollowInt01` root cave. No dungeon interior is linked in the DB yet;
`blueprint_door` and `culture_kit` are empty; 2.W5 §d is the only build proof and is still todo.

**Judgement.** The records and vocabulary are strong and match how Skyrim dungeons are authored. Weak: the plan
is about the record, not the build (nothing turns a record into a navmeshed, lit, looped cell); tier-A supply is
small (KotM: 9 root caves, 8 xanmeer cells, 24 wet cells; BM&V root pieces) against 327 records; the old
"decoupled entrance" rule came from terrain with no rock, and says nothing about the hillside, bank or sinkhole a
mouth needs; 52 underwater entries and 44 stair-throats have no mouth mesh in the pools; vanilla cave kit (981
pieces) is quarantined under 0012; 327 interiors (39 % of places) is a three.js-era count.

**Fold into B/D.** (1) The terrain generator reserves and shapes an entrance site per dungeon record from its
landform request and entrance type (a mound or bank for cave-mouth/burrow/grave-cut, a depression for
sinkhole-lip, flat landmark ground at xanmeer mounds, a cell deep enough for underwater entry under the
one-level rule), as a first-class table, before the freeze. (2) First measure supply: how many records a distinct
mod cell can serve, how many need assembly; re-type the rest as exteriors (0062 §3 allows). (3) The slice proves
one cave (Bones and Tools) and one xanmeer in game with navmesh, light and a loop back. (4) Keep the families,
promises, fixed loot, tier model and the Bones and Tools design as the hillside-mouth template; drop the 327 as a
first-build commitment and the old dungeon-share targets.

## 10. Carry-over features from the old world design, and what Skyrim can do natively (2026-11-01)

Two research agents: an inventory of the old design's world-level features against today's data and schedule, and a
feasibility check of seasons, floods, tides, monthly events and mist in Skyrim SE. Nexus permission pages returned
403, so permissions below are unverified until the 1.16 Nexus audit.

**Cheap and native (do in the rebuild or 2.W3).**
- *Seasons as weather*: region weather entries carry a chance and an optional global; put one ArgoniaCore global per
  season on each entry and set it from the game month (a tiny SKSE or Papyrus check; the Seasonal Weathers Framework,
  Nexus 63562, works this way). The DB already holds 6 weather states, 19 weathers, 310 region–weather rows, a season
  table and 32 chance globals (2.W3). A monsoon set and a dry set need no art. Verify the global-chance behaviour in
  one probe.
- *Monthly events* (the wintertide rootworm migration south, hatching-season hazards): quest or scene conditions on
  GameMonth with enable parents on ref groups; vanilla pattern, rules in a tested table.
- *Mist that burns off*: weather fog near/far per time of day is data; Community Shaders (pinned) has Exponential
  Height Fog and volumetric lighting; placed mist meshes come last, toggled by a weather or hour check if a test shows
  the weather fog is not enough. Mist mods (Volumetric Mists 29273, Cresty's 29003, Mists of Tamriel 78703) are
  Tamriel-placed; reuse method, not placement.
- *Region sound tables with hydrology-derived emitters* (rivers, rapids, shores, night chorus): the old design's
  biggest "Morrowind soul" item; 2.16 holds only generic ambience; data exists to derive it.
- *Fixed danger bands, dens and territories, night multiplier*: data exists (danger_band, creature_region, npc_den);
  the rebuilt terrain must carry the placed dens (4.2).
- *Seasonal grass or landscape swaps*: Seasons of Skyrim (powerof3, 62861; custom worldspaces supported by INI;
  licence README MIT vs API GPL-3, check) swaps forms, land textures and grass by season with no weather handling;
  optional, only with assets Tropical Skyrim or BM&V already ship.

**Approximation only.** *Wet-season floods*: cell water height is static data; no SKSE setter exists and LOD water
would not follow. Vanilla's own quest floods are placed planes toggled by enable parent; at most 3–5 chosen basins as
set pieces, plus wetter textures, pools as swapped statics, more mist and rain. The owner had already dropped
seasonal water in the old repo (50:150); recommendation: keep it dropped, keep the 3–5 set-piece option open.

**Not feasible natively.** *Tides*: no water-height setter; an unread forum thread claims otherwise; leave out, fake
with shoreline FX if wanted (the old owner ruling was "tide only moves water down from the high line", 2.9b).

**Needs a mod first.** Authored night sky (two moons on a 28-night cycle, 13 constellations, the Serpent; the star
catalogue is in the repo): Skyrim's sky is textures; needs a sky replacer we are permitted to use.

**Already cut by the owner in the old repo (inherited rulings 0042 etc.), stay cut**: drifting settlements, fire
spread, river-pirate system (shore ambushes kept), mounts, tide gating, eclipses.

**Not scheduled, worth a line in a chunk**: infrastructure decay states; insect, disease and potable-water tables
driven by season; deep-marsh strangeness (mimic surfaces, vibration ambush); montane haze belt with clear summits;
Argonian season names in the calendar text; waterfall mist and spray pieces (4.6a).

## 11. How vanilla joins a stepped river at a cell edge (measured in Skyrim.esm, 2026-11-01)

The owner challenged the "sill along every step" idea. Measured on all 11,186 Tamriel exterior cells: 556 carry
an explicit water height; 93 adjacent pairs differ (the steps), 80 valid after dropping sentinels; 30 of the 80 drop
more than 1,000 units, 5 less than 100. At the shared edge, in 48 of 80 steps **the river bed crosses the edge
below the upper water surface** (median 224 units, p90 688, about 11 of 33 vertices wide) and **slopes down inside
the lower cell** to below the lower water, in 24 cases within 1–5 vertices (128–640 units), the rest over up to 28;
21 steps are closed banks or lake edges with no channel; 11 have the bed below both levels. There is no lip at the
water surface: the upper cell's water is clipped to its cell, the drop is a sloped bed, and the slope is covered by
a rapids and falls chain (FXrapidsFallsLine01 in 41 of 60 steps, FxRapidsRingHeavy 37, FXWaterfallBodySlope 30,
FXWaterfallSkirtSlope 33, a mist blast at the foot, salmon activators) with rock piles and cliffs on the banks
(897 rock refs against 551 fall refs across 60 steps). Tamriel places no water planes at all: river water is the
cell's own height everywhere.

**So the generator's rule is the vanilla one, not a sill**: hold the banks above the upper water so the channel is
the only crossing; run the bed through the edge about 100–300 units under the upper surface; slope it down inside
the lower cell to below the lower water over 1–5 vertices (longer where the drop is big); lay the rapids or falls
chain on the slope with rocks on the banks; where no river crosses, keep the bank closed at or above the upper
water. §3 B's "sill" wording is withdrawn. The same measurement gives the piece set and spacing to copy.
