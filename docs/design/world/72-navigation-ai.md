<!-- imported unchanged from elder-souls-argonia docs/world/72-navigation-ai.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Part VII-b — Navigation data and ambient movement (§113–115 and the day)

> Module of the world-generation master plan — see [README](README.md) for the router
> and [00-core.md](00-core.md) for the universal principles. Sections §113–115 are
> newly allocated (decision 0022). Companions: technique + library verdicts —
> [research/combat-and-systems/navmesh-ambient-ai-threejs.md](../research/combat-and-systems/navmesh-ambient-ai-threejs.md);
> encounter sockets — [70-dungeons-interiors.md](70-dungeons-interiors.md) §50;
> NPC/creature capability — [75-combat-compatibility.md](75-combat-compatibility.md) §57;
> people and creatures — [0138](../old-decisions/0138-people-and-creatures-live-by-the-place-record-and-the-lamp-clock.md)
> and [2.4](../phases/2-slice/2.4-people.md); the quest plan's deliberate AI ceiling —
> [../quests/20-world-provisions.md](../quests/20-world-provisions.md) (no free-roaming
> escort or chase AI, no followers).

## 113. Scope: what the world build owes, and the deliberate ceiling

The world build **bakes a path network per place and proves each place's
people can walk it**; rich game AI is later work, and the quest plan caps it.

**People walk when seen and are swapped when not** (0138): a person walks
their route between spots on the path network while a player can see them,
and is placed at the next spot when nobody can, in two to four coarse blocks
a day on the village clock. The wait, sleep, ferry and door screens are
catch-up moments. Around that: work and idle spots with sourced animation
loops, small wander radii, patrol chains, creature territories with leashes,
all of them points on the baked network, so the compiler can prove them.
Skyrim's own scheduler is the ceiling we stay below: no needs simulation and
no off-screen timetable.

## 114. The path network: bake, classes, runtime

**Library.** `recast-navigation` (Recast and Detour as WASM; MIT), pinned to
the exact version in `packages/game-core/package.json` and in
`RECAST_NAVIGATION_VERSION` (`packages/game-core/src/nav/navClasses.ts`). The
bake and the runtime load the same package; the index records the version
and `NAV_BAKE_VERSION`, and the runtime refuses a bake of another. Only
`navBake.ts`, `navBoarding.ts` and `NavService.ts` import the library, so a
successor (navcat) is a swap of those files.

**Classes.** One tiled Recast bake per class; the agent radius is eroded
into the mesh, so a class answers whether a body that size stands and
passes. Units are metres:

| Class | radius | height | climb | slope | cell / cell height | tile | water |
|---|---|---|---|---|---|---|---|
| `humanoid` | 0.35 | 1.85 | 0.6 | 47° | 0.15 / 0.1 | 96 voxels | wades to 0.8 m |
| `large` | 1.1 | 2.6 | 0.9 | 40° | 0.4 / 0.2 | 64 voxels | wades to 1.2 m |
| `swim` | 0.5 | 1.0 | 0.2 | 10° | 0.5 / 0.2 | 64 voxels | swims from 1.0 m deep |

Measured on a test yard: a humanoid passes a 1.2 m doorway (the research's
0.25 m cell needed 1.5 m, so the cell is 0.15 m); a large creature is
refused at 2 m and passes at 3 m.

**Inputs.** Per slice place (the sixteen places and the two route places;
not Helstrom, not the fixtures), over the place's boundary, sockets and
door thresholds plus 12 m:

- the frozen chunk ground on the lod1 lattice (1.83 m; the heights the
  Rapier heightfield and `chunkWorld.groundHeight` read), dropping every
  triangle under more water than the class wades;
- the place's runtime solids (`publishedPlaceSolids`, the set the studio's
  physics holds: LOD0 trimeshes and measured boxes), plus moored hulls,
  rafts and lighters at their published rest pose so their decks are
  walkable. Every collider is carved: a low clutter piece keeps its lid
  wound face down (no floor, but its ground is covered) and a box keeps
  face-down inner layers every 1.5 m (no floor inside a trunk or a crown).
  A low piece is a step (its lid floor) only where it joins ground or a
  walkable top within the climb, and never when it is narrower than a body
  (two radii) both ways: a basket, an urn or a bucket is in the way, a tread
  or a plank is a way up. Outdoors a lid keeps its own area in the bake
  (`bakeClass`'s `lidsKeepArea`: rasterisation merges spans one voxel apart,
  and Recast's low-hanging filter is off), so no lid lower than the climb
  turns back into floor; interiors keep the library's reading, their floors
  being stacked meshes a climb apart;
- the place's roads and walk proofs (`navRoutes.ts`): each compiled route
  (`pointsM`, `widthM`) and each walk proof (1.0 m wide) is marked as the
  `route` area after erosion, so polygons split along its edges;
  `nav/nav_carve.mjs --place <id>` tests a standing column of each class on
  every mesh sample against the solids; `worldgen/spot_solids.mjs --place
  <id>` names every home, bed and work spot whose body or first step out
  lies in a solid, with the nearest clear point on the mesh;
- the compiled high-water line (`water/water-surface.png`) for the swim
  class.

**The surface-swim network** is its own class: the water plane at the
high-water line over every lattice cell at least 1.0 m deep, minus every
cell a solid crosses within 0.4 m below to 0.6 m above the line (piles,
hulls, decks, rocks). Divers and water creatures path on it; under the
surface they steer directly inside the open water (no voxel navigation).

**Boarding links.** A moored hull is an island of deck. After a first bake
the bake groups the walkable surface on and beside each hull into islands;
an island that does not walk to one of the place's ways in (the first point
of each of the compiler's walk proofs, `settlement.walkRoutes`) is joined,
closest first, to the connected set by a bidirectional off-mesh link of at
most 3.5 m across and 1.8 m up or down; the second bake carries the links.

**The generator.** `navBake.ts` is the library's tiled generator with two
changes: the route areas are marked on the compact heightfield after erosion
(every walkable polygon keeps flag 1), and the chunk list a tile reads grows
to hold every chunk (the library's stops at 512 and silently drops triangles
in a dense soup: a fence wall a walk ran through, a cave's stairs). The bake
version is `NAV_BAKE_VERSION` 3. `bake_nav.py` and `nav_gate.mjs` read
`NAV_OUT_DIR` to bake and gate a scratch copy without touching the published
one.

**Assets.** `apps/world-studio/public/nav/<place-id>.<class>.bin.gz` (Detour's
binary, gzip) and `nav/index.json` (per place: bake bounds, the input
digest, per-class file, sha256, sizes, polygon and tile counts, boarding
links, and the ground height under each door). The bake for the eighteen
places runs in about 40 s under the job guard; the published total is
1.42 MB gzip (4.0 MB raw), the border-road route place the largest at
0.4 MB. The game reads the studio's copy.

**Runtime.** `NavService` (`packages/game-core/src/nav/NavService.ts`), built
by the composition, never a module singleton (0038): `init()` reads the
index; `loadPlace` and `loadAround(x, z)` load a place's classes on demand;
`findPath(from, to, class)` returns the string-pulled corridor with its
corners cut where the mesh allows and says whether it reaches the goal
(`{ preferRoutes }`, a routine's walk only, costs ground off the routes
`OFF_ROUTE_COST` 2 per metre against a route's 1, so people keep to the roads;
combat and reactions take the plain filter);
`nearest`, `randomPointAround` (the wander query) and `raycast` (the
stuck-people loop) answer per class; `unloadPlace` frees a place streamed
out. The studio's dev HUD layer "path network" (`?nav=1`, `NavOverlay`)
draws the loaded meshes and a sample walk near the camera.

## 115. The gate: every person's walk is proved

`tooling/world-generation/nav/nav_gate.mjs` (rules in `navGate.ts`), run by
`regen.py --check` as the `nav-bake` gate under `npm run check`, and per
place by `derived_fresh.py`:

- **Fresh bake.** Each place's bake digest (`navInputDigest`: placements,
  boundary, socket and door positions, the ways in; never text, so a label
  edit leaves a bake fresh) matches its bundle, and the bake version matches
  the runtime's. Stale: `bake_nav.py --place <id>`.
- **Work and home.** Every `npc` socket's spot reaches each spot its
  schedule names on the humanoid class. A walk arrives within 1.5 m of the
  spot, or within 1.2 m of the edge of the furniture or station the spot is
  on (a bed, a well), at most 4 m. A spot in an interior cell stands in as
  the doorstep of the door into that cell.
- **Doors.** Every interior door's doorstep (found by walking the mesh back
  from 4 m out along the door's outward bearing to where a closed shell's
  wall stops it, over the lowest walkable surface above the door's ground)
  reaches the way in of its own walk proof, else the place's hub.
- **Water work.** A fisher's, poler's or diver's work is proved on the swim
  class: swim water within 8 m of the spot (40 m for a diver's bed), a
  walkable edge beside it that the person's home walks to, and a swim path
  from that edge to the spot.

It prints the counts per place and every unroutable pair with coordinates,
and exits 1 on any red. `nav_view.py --place <id>` draws a place's class
mesh with every pair, so a red is read from a picture.

**Later, on the same network.** Patrol chains and wander areas, creature
territories and dens (2.4 c), encounter access per class (2.7), and the
streamed province-wide bake when Part 4 builds the wilderness.

## The day: the village clock and the people service

One village clock, pinned to the lamps and the sleeping hours
(`game-core/src/people/clock.ts`; its constants are tested against
`settlement/lighting.ts` and `interior/interiorLighting.ts`): rise 05:30,
work 06:30, a midday meal 12:00-13:00, home at 17:30 when the lamps come on,
the evening at home, bed at 22:00. That is the common day. Each person keeps
their own version of it (`jitterDay`): every edge between two blocks moves by
up to 10 game minutes either way, by up to 3 next to sleep. The offset is
fixed per id and edge, so the blocks still tile the day and a save restores
the same day, and nobody stops for the meal at the same instant. A shop's, an
inn's and a watch's people keep the exact hours, because trading, the door
locks and the handover read them. A living thing's blocks come from its record (`LivingThingRecord.day`);
**role exceptions** change them by role id, never per person
(`people/roles.json`: the innkeeper up late with the door open, the
shopkeeper, the watch in day and night shifts so someone is always out,
fishers and divers on the light, posted guards, a crew sleeping `aboard` its
hull and a tended `camp`'s sleepers, both on an outdoor bed with a written
`roleReason`, and dens). A predator's active block is `hunt`: from the den
to two or three prey points inside its territory radius on its own nav
class, and back. A pack's leader walks the round and the rest follow it on a
ring, lagged ([74](74-ecology.md) § Packs). The roles are the
place record's (`life.groups[].roleExceptions`); the cast reads them only from
the roster row whose home socket the socket is (`generated/living.json`).

**The cast** (`people/cast.ts`) is a place's living things, built from its
sockets, doors and roster, each with its home, bed, work, leisure and evening
spots. A spot in an interior cell is reached at the step 1 m outside its
door; it also carries its position in the cell's own frame and the door's
arrival marker there (`cellPosition`, `cellArrival`). Every creature row of
a den is a member, carrying its pack (`packId`, `packIndex`, `packKind`).

**Seats for the meal and the evening.** A person whose day has the midday
meal and no seat of its own takes the nearest free `sit` socket: in its
work's cell indoors, else outdoors within 60 m, its own parcel first. The
same holds for an evening spent outdoors. Each seat is claimed by one body,
so a family of four with two chairs seats two and the rest eat standing. Sit
sockets on chairs and benches are a layer on the built place (0140):
`tooling/placement-workbench/workbench/seat_sockets.py --place <id>` picks
seats by the mesh's seat top and footprint, never by name; indoors, from the
chairs the cell's plugin marks as sit furniture, routed on the cell's own
nav. Each socket
carries `seatHeightM`, the seat top above the floor
(`people/seat.ts`, read by the player's sit as well), so a chair too small
for the bake still seats its sitter.

**Walk when seen, swap when not** (`people/service.ts`, `PeopleService`, one
per walk, built by the composition):

- At a block change, a thing a player can see walks its route on the path
  network to its next spot; a thing nobody sees is swapped there at once.
- A seen thing sets off early by the length of its walk, so it arrives on
  time; a thing stays late only while a player never takes their eyes off it.
- A walker nobody sees any longer is swapped to its goal.
- **Inside a cell.** While a player stands in a cell, its people are seen
  there, and a walk gains a leg on the cell's own mesh: from the spot out to
  the door's arrival marker, from the marker in to the spot, or across the
  room. Outdoors and indoors are separate frames: a player inside sees
  nobody outdoors, and the reverse. `bake_nav.py --interiors` bakes the
  cells' meshes into `nav/interiors/` (one per cell, in its own frame);
  `people/interiorNav.ts` loads them per cell.
- **One nav for both worlds.** Combat, search, crime reaction and the
  custody walk take their mesh from `navFor(frame)` (`createNavFor`,
  `people/interiorNav.ts`): outdoors (`null`) the world mesh; a shown cell
  its bake shifted by the cell's `originM` both ways, so points go in and
  come out in world feet; null for a cell with no loaded bake. The result
  goes to `reactionNavOf` and `steerTarget` unchanged.
- **Interiors are humanoid only.** A cell hostile of any size walks the
  humanoid mesh: a `large` (1.1 m) bake of the cells with large hostiles
  costs 0.5–19 s and 2–19 KB, but no arrival reaches any of their 14
  hostile spots on it, because the doorways are narrower than the body.
  `swim` in a cell answers null. A Teeth crypt query costs 0.1–0.3 ms.
- **The interior gate.** `nav_gate.mjs` reds a stale cell bake (index
  `inputDigest` against `interiorNavInput`) and, on each cell's humanoid
  mesh (`gateCell`, `nav/navGate.ts`), any cast spot in the cell its
  door's arrival does not reach, hostile spots counted apart, and any
  linked load door the cell's arrival marker does not reach. A linked door
  is the exit or a door into another baked cell; any other door is listed
  as unlinked. Every idle socket of the plugin's, cast or not, must also be
  reached from the arrival marker (itself or a point within 1.5 m of it, as
  a bed is walked up to from a side), so a sealed room reds. A cell whose
  gaps fit a body but not the 0.45 m erosion the 0.15 m voxel rounds the
  0.35 m radius up to bakes at 0.0875 m (`FINE_CELLS`,
  `interiorBake.node.ts`); the rest read worse finer.
- **On the ground.** A socket's height is the origin of what it was placed
  on (a rune circle, a dug-in stone), never the floor. Every outdoor body
  seated off a host stands on the mesh under it (`floorAt`: the nearest
  floor within 1 m up or down, in widening squares), or on the floor beside
  it when the spot is inside a rack's cut-out. A body seated before its mesh
  loads is mesh-pending: it is not drawn, and it is re-seated once a second
  until the mesh lands. The layer asks for the mesh before it adds a place.
- **Apart.** The things at one spot stand on rings round it, on the floor
  at the spot, never where another body already stands. A pot, a station,
  a pole or a dig takes one body (`single`); the rest of its group stand by
  facing it.
- **Solid bodies.** A walker's body is swept against the frame's solids
  and the player, and a person on its feet stands on the ground under it
  (`personGround`), outdoors and in a cell alike, so it climbs a stair's
  treads instead of meeting its risers. A ground ray that starts inside a
  solid reads that solid's top, never its own origin.
- **The stuck guard.** A walker held 0.6 s steps 0.9 m aside onto its mesh
  and re-plans, first away from another walker within a body's width (a
  dead heat by id), then the other side. A walker off the mesh, or making
  less than 0.5 m in 2 s (`stuckAfterS`), is re-seated at the nearest mesh
  point and reported, never silently.
- **Catch-up moments.** The wait, sleep, ferry and door screens call
  `catchUp(epochMinutes)`: everyone goes to the spot of the block at the new
  time. A clock jump of more than 20 game minutes between frames (the
  studio's time control) is caught up the same way.
- **Activities.** Each spot names an activity (`people/activities.ts`): a
  rig clip, or a routine composed of existing moves (the diver dives, swims
  about, surfaces, repeats). A fallback always carries its reason.
- **Doors and windows.** Doors lock as Morrowind and Skyrim do, by house and
  person; each rule is a role's `doorLock {when, level, keyHolder}` in
  `roles.json` (`doorKinds` for a door whose people carry none). A house
  locks while everyone in it sleeps, at 15 (hut), 30 or 45 (prosperous) by
  wealth, the occupant holding the key; a shop locks at 30 once its keeper
  stops work (17:30-06:30) and stays open through the midday break; an inn, a
  watch post, a camp, a public temple and a guild hall's public room never
  lock (a sleeping innkeeper only refuses trade); a priest's quarters lock
  asleep at 30, a leader's chambers at 50. A shut door hands the door runtime
  its level and key holder (`dayLocks.lock`): the occupant's key or a pick
  opens it; leaving a cell never reads the day lock (`people/doors.ts`).
  Street windows go dark from bed to rise (`windowGlowFactor`).
- **Save.** The `people` save slot holds the minute and each thing's block
  and spot; a restore is a catch-up.

The scene side (`packages/scene/src/people`): `usePeople` builds the service
over the walk's clock, path network and interior meshes; `PeopleLayer` steps
it against the camera's sight each frame and draws each person on the rig
and the nearest 24 creatures on their model sets (`drawn.ts`);
`PeopleHudLine` is the dev HUD's line (time, in view, walking, swapped,
indoors).

**The clock loop** (`tooling/stats-sim/clock-loop`, under `npm run check`)
runs the slice's living things through a day unseen and a day watched on the
real baked networks, and proves every indoor spot reachable both ways from
its door on the cell's mesh. It fails on anyone stuck, routeless, late or in
the open at a block change. It also fails on a body floating or sunk more
than 0.15 m, one spawned with no mesh, two people within 0.6 m, and any
minute of the noon edge that turns more than a quarter of the slice. It runs the scenarios: the wait screen, a loiter
in each shop until night, the watch handover, each hostile camp at noon and
at night, each keeper watched from inside, and everyone leaving an indoor
spot watched from inside. The bodies day walks the watched day again in
0.25 s steps with every walker a solid body among its frame's solids
(`bodiesDay.ts`); every stuck is a red naming the solid that holds it, and
its table prints per place the walks, stuck, route-joined walks kept on the
route and steps held by a solid. The loop runs in about 11 s.
