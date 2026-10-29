<!-- imported unchanged from elder-souls-argonia docs/world/60-water-traversal.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Part VI — Water rendering, swimming, boats and climbing (§38–46)

> Module of the world-generation master plan — see [README](README.md) for the router
> and [00-core.md](00-core.md) for the universal principles. Section numbers (§NN)
> preserved from the original plan; cross-doc references resolve via the README map.
>
> **Water rendering depends on the light stack** (module
> [55](55-light-sky-time.md), Phase 8a — decision 0016): sun direction and
> colour, sky IBL, exposure and the aerial-perspective term drive reflection,
> specular, refraction and underwater scattering, and moon phase drives tidal
> amplitude. Build water (8b) against that system, not against placeholder
> lights.

## 38. One authoritative water model

The project should expose one gameplay-facing water query:

```ts
interface WaterSample {
  waterBodyId: WaterBodyId | null;
  surfaceHeight: number;
  surfaceNormal: Vec3;
  flowVelocity: Vec3;
  depth: number;
  immersion: number;
  turbidity: number;
  salinity: number;
  temperature: number;
  hazardIds: HazardId[];
}

interface WorldWaterQuery {
  sample(position: Vec3, time: number): WaterSample;
  emitInteraction(event: WaterInteractionEvent): void;
}
```

Rapier and gameplay systems use this CPU-accessible query. The renderer consumes the same hydrology, wave and interaction data.

The advanced water repositories already contain valuable buoyancy, wake, interaction and underwater techniques. Those algorithms can be adapted while Rapier remains the authoritative rigid-body system. This prevents duplicate object simulation and GPU-readback coupling.

> **Current water architecture (decisions [0046](../old-decisions/0046-water-overhaul-retired.md), [0047](../old-decisions/0047-water-one-physical-model.md), [0057](../old-decisions/0057-phase16-terrain-once-water-once-places-on-a-frozen-world.md), [0058](../old-decisions/0058-the-hydrology-graph-is-the-water-record.md); the 0045 terrain-constrained overhaul is retired and its documents are archive):**
> the runtime is the **field water** of 0047: one signed-depth raster contract
> (`water-surface.png` schema 3, wet ⇔ `signedDepth + lift > 0`), one physical
> model for every water level. **Levels come from the hydrology graph**
> (`world/sources/hydrology/hydrology-graph.json`, 0058): the flood solver
> runs once inside `hydrology_graph derive`; the compile
> (`worldgen/compile_water.py`, rewritten in 16c, decision
> [0063](../old-decisions/0063-water-once-the-line-is-high-water.md)) REALISES
> the graph on the frozen ground — each body flooded from its deepest cell to
> its recorded level, each reach at its profile, a river through a body IS
> the body — and never re-solves or re-floods the province; `patch_water`
> proves a typed patch moved no water. **The compiled level is the
> high-water line** (owner): the season and the tide only draw the
> water DOWN from it. The sea's energy comes from the weather's wind and the
> compiled directional fetch (`waves.ts` `seaRmsHeightM`, ruling 7); every
> wet texel names its graph entity (`water-id.png`). `WorldWaterQuery` + `WaterSample`
> live in `packages/contracts`; the CPU model and the renderer in
> `packages/game-core/src/water/` — that folder's README is the file-by-file
> map of the renderer and the interaction stack. Terrain never moves for
> water after the 16b freeze. The 16c brief and
> [research/phase16/audit-water-runtime.md](../research/phase16/audit-water-runtime.md)
> carry the defect ledger and the sea/edge/falls targets; the round-2
> numeric baselines are in
> [research/archive/water-round-2-2026-09/water-round2-evidence.md](../research/archive/water-round-2-2026-09/water-round2-evidence.md)
> (kept as the keep-list reference, not as a rule set). Deferred to later
> phases: swimming and boat controllers (Phase 9).

## 39. Rendering stack

### 39.1 WaterThreeJS base techniques

WaterThreeJS is MIT-licensed, WebGL2-based Three.js code with analytic Gerstner waves, screen-space reflections, depth-based refraction and absorption, shoreline/contact foam, underwater fog, god rays, caustics and CPU-mirrored wave sampling for buoyancy.[^W1]

Useful components:

- analytic surface function and normal;
- SSR with sky fallback;
- Beer–Lambert colour and underwater absorption;
- Fresnel/GGX surface shading;
- detail-normal cascades;
- contact foam and wakes;
- immersion detection;
- CPU wave sampling and buoyancy concepts;
- underwater post-processing.

### 39.2 SeedOcean reference architecture

SeedOcean is MIT-licensed and provides river, lake, pool, coast and open-ocean modes, a `FlowMap` contract, persistent foam, wake textures, buoyancy currents, underwater effects, quality modes and a WebGL2 fallback.[^W2]

Useful components:

- directional river flow and spline/ribbon approach;
- shared flow-map data for surface movement and shore foam;
- bounded-water abstractions;
- wake and buoyancy interfaces;
- headless design API ideas;
- quality-tier structure.

Its WebGPU-first path does not define the game baseline. The WebGL2 path and data contracts remain directly relevant.

### 39.3 Local interactive simulation

`jeantimex/threejs-water` ports Evan Wallace's bounded water simulation to Three.js. It uses a GPU wave equation, caustics, reflections/refractions, buoyancy and object displacement.[^W3]

Use pooled local patches for:

- hero temple pools;
- flooded dungeon chambers;
- close-range splash interaction;
- falling bodies or objects;
- ritual pools;
- highly visible small water surfaces.

### 39.4 Open-water high tier

ABYSSAL provides a WebGL2 spectral FFT ocean with JONSWAP/TMA spectra, multiple cascades, persistent foam, caustics, underwater rendering and buoyancy.[^W4]

Use it as a high-quality reference for Topal Bay and exposed coasts. Mobile and mid-tier settings should use fewer cascades or analytic waves.

## 40. Water-body semantics

Since Phase 16a the ids, kinds, levels and seasons come from the hydrology
graph (decision 0058); this contract is the runtime view of a graph body.

```ts
interface WaterBody {
  id: WaterBodyId;
  kind: HydrologyBodyKind; // the graph's vocabulary (world/sources/hydrology/README.md):
                           // ocean | lagoon | lake-lowland | tarn-upland | pond | pool |
                           // plunge-pool | marsh-fringe | marsh-deep | swamp | backswamp | mudflat;
                           // rivers are Reach entities (horizontal-* | sloped-* | vertical-fall)
  surfaceBase: number;
  depthField: FieldRef;
  flowField: FieldRef;
  discharge: number;
  turbidity: number;
  sedimentColour: ColourId;
  salinity: number;
  waveExposure: number;
  floodBasinId?: FloodBasinId;
  navigability: NavigabilityProfile;
  ecologyId: EcologyProfileId;
  rendererProfile: WaterRendererProfileId;
}
```

Visual profiles:

| Water class | Surface and underwater character |
|---|---|
| Fast river | Directional advection, coherent downstream ripples, bank/rock foam, suspended sediment |
| Deep swamp pool | Low bulk velocity, small ripples, dark absorption, debris, algae and insects |
| Shallow marsh | Visible mud or vegetation bed, tiny wind waves, wakes from wading and creatures |
| Estuary | Current plus tide, broader wind waves, brackish colour, boat wakes and mudflats |
| Coast/Topal Bay | Long swell, local chop, foam, horizon handling, full underwater optics |
| Hist pool | Site-specific clarity, particles, sap or ritual visual effects driven by lore state |

## 41. Shared render-pass architecture

Large numbers of separate reflector/refractor objects would be expensive. The runtime should capture scene colour and depth through shared passes, then render all visible water using shared buffers and per-water-body data.

Recommended frame structure:

1. opaque scene colour/depth;
2. optional reduced-resolution reflection data or SSR source;
3. all visible water surfaces with shared shader variants;
4. underwater composite when immersed;
5. particles, foam decals, splashes and post-processing.

Rivers use ribbon meshes. Marshes and lakes use connected polygon surfaces. Coasts use camera-centred meshes or clipmaps. Local ripple patches allocate from a small pool near the player.

## 42. Water quality tiers

| Feature | High | Medium | Mobile/performance |
|---|---|---|---|
| Reflections | half-resolution SSR with more steps | reduced-step SSR | short SSR plus environment fallback |
| Refraction | depth-aware scene refraction | simplified depth refraction | absorption and shallow-bed approximation |
| Waves | spectral or dense analytic field | analytic multi-band waves | compact Gerstner field |
| River detail | multi-scale flow normals and foam | flow normals and bank foam | one flow layer and sparse foam |
| Local ripples | several pooled patches | one or two patches | nearest hero surface |
| Caustics | dynamic projected pattern | reduced resolution | selected hero sites |
| Underwater | volumetrics, particles, Snell window | reduced steps | fog, absorption and light shafts |
| Foam | persistent/contact/shore | simplified contact/shore | bank and wake masks |

The semantic water model remains identical across tiers.

## 43. Swimming modes and player capability

The current `PlayerMovementController` handles grounded movement, position, velocity, facing and jumping. Argonia needs a broader locomotion contract while preserving ecctrl as the current grounded adapter.[^R4]

```ts
type LocomotionMode =
  | "grounded"
  | "airborne"
  | "surfaceSwim"
  | "submergedSwim"
  | "climb"
  | "boat"
  | "rootwormTransit";

interface AvatarLocomotion {
  mode(): LocomotionMode;
  position(out: Vec3): Vec3;
  velocity(out: Vec3): Vec3;
  setIntent(intent: LocomotionIntent): void;
  setFacing(direction: Vec3, locked: boolean): void;
  teleport(target: SpawnTarget): void;
  capabilities(): TraversalCapabilityProfile;
}
```

Capability fields include:

- surface and submerged swim speed;
- acceleration and turning;
- breath capacity;
- water-current resistance;
- dive depth tolerance;
- stamina cost;
- equipment drag and buoyancy;
- climb stamina;
- climb speed;
- grip and material modifiers;
- jump and gap capability;
- racial and spell effects.

Argonian racial physiology can set underwater breathing independently of other swimming statistics. Spells can modify breathing, speed, current resistance and visibility.

**Owner steer (module 76 §103):** athletics (or its equivalent in
the decided stat design) governs **swim speed** (Morrowind canon) **and breath
capacity for non-Argonians**; Argonians breathe underwater outright. Phase 9
should wire swim speed and breath through the capability profile so the stat
system can drive them at 10c without rework.

**Swim depths are a real body's (lane swim).** The enter (1.4 m), leave
(1.016 m) and wade (0.5 m) depths in `locomotion/swim` are water at the feet
of a 1.8 m walker, in real metres. A display that exaggerates heights (the
studio's vertical scale) reads the water through `datumScaledWaterQuery`,
which moves only the still datum, and the swim takes the sample's real depth
(`swimWaterAt`); the surface it floats on is the drawn one. The body that
swims is mounted by `PlayerBody` with its one `EcctrlAdapter` as
`movementModes` (required): ecctrl is off while swimming, and the adapter's
handover back to it ends when PlayerBody reports it on.

**The camera in water holds its land pose (lanes swim2, swim5).** As in
Skyrim's third person, the `FollowCamera` follows a swimmer with the same
arm, yaw and pitch range as a walker, crossing the water plane freely, with
no water ceiling. The one difference: while swimming (`update(..., {
swimming })`) the camera BODY stays inside the swim band of orbit pitch
(`swimMinPosPitch` to `swimMaxPosPitch`, 0.22 to 0.46 around the resting
0.34), so it holds its land height and distance above and behind the
swimmer, about 2.4 m over the shoulder and 5.5 m back. Orbit pitch past the
band only tilts the view, and only as far as keeps the drawn body's far end
(`swimmerExtent`: soles hanging and trailing, head leaned by the stroke
blend, both pitched) within `swimFrameShare` (0.4) of the half frame, so a
prone stroker may look further up than a hanging climber. Without the band the steering pitch moved the body: a dive held
at the 0.78 clamp put the camera 5 m above a swimmer 4 m down, and a climb
looking up dropped it to the pivot under water, looking up from below.
Both runtimes draw the swim pitch about the stroking shoulder
(`swimPitchPivot`, `camera/swimmerFrame.ts`) and pass it to the camera
(`swimPitch`, with `strokeBlend`); the view aims at the middle of the drawn
body's extent (`swimmerAimPoint`), not at the land look height, so a body
tipped into a dive or climb or hanging in a tread is not cropped at the
frame's top or bottom (lane swim7: head and soles from 1.16 to 0.52 of the
half frame). The
arm's collision sweep and the studio's terrain backstop still pull it in.
A swimmer dipped at most `swimSweepMaxLift` (1.5 m) under its floating
height (a plunge) has the arm swept from that floating height (`surfaceY`
passed in), so the 0.42 m sweep ball does not graze a quay lip the floating
sweep clears; the water itself never blocks the arm (it is no collider).
The orbit pitch steers
the swim (`swimStroke`) along the camera ray: tilted below the resting view the stroke dives,
tilted up it climbs, and at the surface (`swimAtSurface`, where the float
spring owns the height) an upward intent is dropped, so a swimmer looking
up swims at full speed along the heading. On touch the swim is steered by
the camera drag alone: there are no dive or rise buttons, and the jump
button hides while swimming. The headless swim loop
(`packages/character/src/swimLoop.rapier.test.ts`) drives the real camera
through tread, a 6 m dive, the climb, a surface swim looking up and a
submerged orbit, and holds every frame's camera step under 0.25 m and
0.05 rad, with the swimmer's body centre and its drawn head and soles
(`swimmerExtent`) inside 0.9 of the frame from centre and the
camera within 1 m of its land height and 0.6 m of its land distance on
every script but the tread; a wall-plunge script (a jump off a quay beside
deep water) holds the arm at 0.85 of its length. The sandbox's swim windows hold the drawn
camera's height and distance (`minCameraAbove`, `minCameraBehind`).

The swim pose: the vanilla SWIM_FORWARD clip leans the spine about 57
degrees from vertical from an upright pelvis, so its legs hang and the
stroke reads standing from behind; the treading SWIM_IDLE leans about 6.
`swimBodyPitch` draws the root pitched head-down while stroking: level
(`SWIM_STROKE_PRONE_PITCH`, 33 degrees, which lays the clip at about 90
from vertical, legs trailing behind) at the surface, and further along a
dive or climb under water (0.8 of its angle). It eases in and out with the
stroke blend (`SWIM_STROKE_BLEND_RATE`), stands the body upright while
treading or with the feet on the floor, and pivots at the stroking
shoulder (`SWIM_STROKE_SHOULDER_DROP`, `SWIM_STROKE_SHOULDER_FORWARD`) so
the shoulder stays on the surface. The combat runtime draws it, the one
driver in the studio and the game; the physics body stays upright.
The sandbox's swim windows gate it on telemetry (`minRootPitchDeg`,
`maxRootPitchDeg` on the drawn root pitch; `minBodyLeanDeg`,
`maxBodyLeanDeg` on the drawn pelvis-to-head line), and
`minForwardSpineTiltDeg` holds a surface stroke prone.

Looking up past the body floor tilts the view only as far as keeps the
player's look point within `lookUpFrameShare` of the half frame below
centre, on land and in water, also when a wall shortens the arm: the player
sits low in frame and never leaves it. Further pitch still steers a swimmer
upwards. The combat sandbox draws its free orbit with this same
`FollowCamera` and the same arm collision (`rapierCameraObstruction`), and
its pool has a 6.4 m dive well, so its swim strips show the real camera.

## 44. Underwater is a complete exploration layer

Underwater content should have its own graph:

- surface access nodes;
- air pockets;
- submerged entrances;
- currents;
- vertical shafts;
- hazards;
- creatures;
- loot and containers;
- interior portals;
- return routes;
- visibility and light fields.

POI families include:

- submerged Xanmeer waterworks;
- flooded cave systems;
- riverbed smuggler hatches;
- sunken Imperial villas and customs posts;
- shipwrecks and wreck fields;
- wells and cisterns connected to larger interiors;
- root tunnels;
- drowned Lilmothiit or Kothringi remains;
- ritual pools;
- predator nests;
- air-filled caves behind siphons;
- collapsed prison drains;
- undercut banks and hidden caches.

Access metadata can distinguish:

- immediately Argonian-accessible;
- accessible to other races with breath skill or preparation;
- spell- or equipment-gated;
- high-current or deep-water expert routes;
- quest-state or Hist-state routes.

## 45. Boats as primary world vehicles

Black Marsh supports boats as the main player vehicle family. Horses can appear in selected firm-ground fringe zones where culture, routes and assets support them.

Boat classes:

| Class | Use |
|---|---|
| Dugout/canoe | narrow channels, low draft, easy portage, local travel |
| Skiff/rowboat | fishing, ferrying, cargo and exploration |
| Raft/platform | village links, cargo, improvised transport |
| River trader | storage, passengers, longer routes |
| Sailboat | estuary and coast travel |
| Ritual/Hist craft | culturally specific transport and quests |

**Boat records (2.15, decision 0159).** The slice builds two classes to ride,
the dugout and the sea hull; the skiff and river boat are typed and priced
only (`world/sources/vocab/boat-classes.json`). A Boat record names its class,
owner and last mooring (`world/sources/placement/boats.json`, save family
`walk.boats`). Ownership follows the item model: taking a boat that is not
yours files theft on the Owing ledger, with no stolen flag. A lost or adrift
boat returns to its last tied mooring after a rest, or a boat seller fetches
it for ceil(10% of its price), never under 5 gold. Boats are bought and
fetched through the `boat` person service. A mooring is a socket
(`kind: mooring`) authored in the place's layout and published by the layer
path. `worldgen/moorings.py --seat` writes its dry-season depth and water,
and `--check` refuses one that floats nothing it accepts (depth under the
deepest draught plus 0.05 m), has nothing to tie to (a jetty piece within
6 m, a bank within 7 m, or open anchorage for the sea hull only), has no lore
reason, or sits on water its classes may not enter. Where a class may go is
the derived navigable reach (`worldgen/boat_views.py`).

**Placed craft float (decision 0129).** Every hull, raft and moored ship in a
place is a buoyant body on its tether (`water-motion-classes.json`), unless its
geometry puts it aground (draught over the water depth), where it is placed
`beached` and static. A rigid gangplank may rest on a floating hull only
when the hull's motion envelope fits the plank's seat: the water's fall from
the high-water line (tide on coast and estuary classes, season by draw-down),
the class's measured wave travel and its pitch and roll lever must stay
within the plank's thickness plus its length times sin 5 degrees, and its
tether swing within the plank's overlap on the hull (gate `water.motion`,
`worldgen/water_motion.py`). Tidal water fails every plank, so a hull there
abuts its dock with no plank. Cargo rides its hull: a piece mounted on a
floating hull (`parentPlacementId`) is drawn and collided on the hull's own
body, posed in its frame, with no mass of its own (the class mass is the
craft laden; game-core `BuoyantPlacements` riders). The runtime draws a
floating hull's tether line, so it carries no static rope mesh (gate
`water.motion`). A seabed tether's slack is the measured need, the wave
crest over the rest (2 sqrt 2 times the class's wave RMS, up to 5 cm): the
tether is sized at the high-water line and the water only falls from it,
so the fall needs none and more slack only widens the swing. A ferry raft
lies against its landing stage: the plan gap is at most 0.1 m and the step
from stage to deck at most 0.3 m (`wb.py <layout> measure raft <stage>`);
Riverwalk's ferry raft meets its stage at 0.09 m.

**Boats are sourced assets like everything else — we never design our own**
(owner): a boat type enters the roster only when **both its model
(candidate pool: module 90 §77) and its required player/NPC clips (module 90
§74.3 — no vanilla rowing clips exist) are sourced**. Selection favours craft
needing only seated poses plus procedural oar/tiller drive.

Gameplay components, **tiered** (owner, decision 0034 — the flat
wishlist here was being read as scope):

*Core (Phase 9 — the player's own craft):*

- multi-point Rapier buoyancy;
- water-current sampling;
- rotational and linear drag;
- shallow grounding;
- hull collision;
- boarding and disembarking;
- docking and mooring;
- wake and foam events;
- rain and flooding interaction.

*Travel services (world content, Phase 11+ — never vessel simulation):*

- **ferries and boat fast travel are Morrowind-style**: speak to the
  ferryman/boat owner, pay, arrive — instant travel over a defined,
  geographically sensible service graph: the one travel-service record
  (`world/sources/routes/travel-services.json`, 16e/16g) whose hops follow
  the recorded lanes, reach chains and rootways, with a harbour station per
  major city and connectedness as the gate (depth is reported, never gated;
  owner);
  the service kinds are ferry, boat, canoe and rootworm (guide, cart and
  porter wait for Phase 15); `canoe` is the minor-waterway run between the
  smaller places (decision 0068 §4);
  NPC passengers are set dressing (parented props at most).

*Deferred until a quest brief or playtest demands them (none currently does):*

- cargo/inventory integration on the player's boat;
- passenger carrying on the player's boat;
- hull damage and repair;
- free-roaming AI boats;
- boat combat hooks.

Boat navigation uses depth, channel width, bend radius, current, tide, bridge clearance, submerged obstacles, docking space and vessel capability.

The Phase 4 macro graphs (roads, boat lanes, rootways) connect only the anchor
cities and are deliberately sparse. As settlements populate (Phases 11/15) the
transport network **densifies**: minor roads, jungle paths, boardwalks, levee
tracks, ferry hops, canoe channels and additional fast-travel services grow
around every placed settlement, always as least-cost responses to the same
terrain fields (owner direction). Where a macro boat lane crosses
land (portage hops, drawn amber in the studio), watershed refinement must
resolve the hop explicitly: re-line the lane, move its station, or make it a
real portage/boardwalk feature. (Mechanism exists since Phase 6 pass 2:
compile_society persists lane paths in `waterways.json` — ending at the berths
declared in `world/sources/routes/lane-terminals.json`, with the
anchor-to-anchor solve kept beside it as `waterways-natural.json` for siting
(decision 0025);
`refine_watershed.resolve_portages` (retired with the frozen base, 0059; portages are re-derived from the hydrology graph in 16e's waterway re-lining) applied decision 0012 and recorded
outcomes in the basin's `portages.json` for Phase 11 feature placement.)

## 46. Climbing and world generation

Large logical surfaces should be climbable by default. The asset registry and generated terrain need climb semantics:

```ts
interface ClimbSurfaceProfile {
  material: PhysicalMaterialId;
  climbable: boolean;
  grip: number;
  wetGripMultiplier: number;
  requiredAbility?: AbilityId;
  exclusionReason?: string;
}
```

The world compiler should generate and validate:

- continuous climb corridors;
- ledges and rest points;
- transitions between water, ground and climb;
- tree branch routes;
- building roof access;
- cliff top-out clearance;
- camera clearance;
- stamina-appropriate route lengths;
- intentional blockers with explicit metadata;
- alternate routes for low-capability characters.

Rain, wetness, equipment load, skill and spells can modify grip and stamina.

---
