<!-- imported unchanged from elder-souls-argonia docs/research/archive/rendering-decision-rounds/0123-as-recorded.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0123 — Interiors are lit by their own sources and, by day, their windows and beams

Evidence: decision 0123 as it stood before it was rewritten as one current document; the record itself is [0123](../../../old-decisions/0123-interiors-are-lit-by-their-sources-windows-and-beams.md).

Status: accepted (16k walk 11, interior-light lane; commits 9332242a,
2ae5777d, da70c92e, a4fe9321). Supersedes the daylight addendum of
[0109](../../../old-decisions/0109-interior-additions-add-kit-pieces-to-a-tier-a-cell.md).

## Context

Owner, 2026-10-03: interiors with windows were too bright, looked the same
at every hour, and their windows did not read as light sources. The bar:
a room is lit almost entirely by its local sources (hearth, candles,
lanterns) plus its windows in daylight; windows read as sources by day; the
room changes visibly with the time of day; the look is close to the saved
god-ray references (`docs/research/rendering/volumetric-bars/god-rays-*.png`).

The model this replaces lit one point light per window primitive at its
bounding-box centre (two lights for twelve panes in the Claywater station
house), over a flat ambient that rose with the sun the same way whatever
the window faced.

## Decision

One module, `packages/game-core/src/interior/interiorLighting.ts`
(`InteriorLighting`, pure functions first), lights every interior. The
loader builds it for every cell (`interiorLoader.ts` `instantiateInterior`);
a cell with no window row gets no window lights. Inputs are a plain struct
built from the drawn sky rig (sun, moons, weather), so the package imports
nothing from an app. Lights are created once at load and only their
intensities and aims change, when the inputs move past an epsilon; nothing
allocates per frame. The sun and moon directions use `DIR_EPS` (1e-6), so
while the clock runs (the sun moves about 2e-5 per frame at rate 0.5) the
lights, the shadowed sun and the shafts follow it every frame, and a paused
clock costs nothing. Constants are named here, never valued: the loop tunes them.

0. **Record falloff.** A plugin light's falloff exponent (`raw.recordFalloffExponent`:
   1.0 lanterns, 5.0 the sun omni) is the bundle's `falloffExponent`, never a
   constant; the exporter (`worldgen/interior_light.py` `skyrim_curve`) fits `fade`
   to Skyrim's `1 - (d/r)^2` at 0.5 r and 0.75 r under that exponent. The exponent
   shapes intensity inside the light's radius and the light is 0 at the radius:
   irradiance = intensity x clamp(1 - d/R, 0, 1)^exponent (`falloffWindow` in
   `packages/game-core/src/interior/interiorLightClasses.json`). One form, four
   evaluators: the runtime (`interiorLoader.ts` `interiorLightFalloff`; the fixture
   shader `fixtureLightField.ts` reads the exponent from its decay slot as
   `-exponent`, outdoor lamps keep three's decay), the render (`interior_render.py`
   `light_list`, `render_interior.py`) and the exporter (`interior_light.py`
   `falloff`, which also fits `fade`). There is no decay mapping: a decay of
   2 x exponent put the light out far inside its radius (IxtaxhXanmeerInterior
   re-exported 100 % dark with 28 lights). Calibration test
   (`test_interior_light.py`): a plugin lantern (R 3.64, exp 1.0) lights the
   walk node 2.5 m under it above `DARK_E` with no ambient.

1. **Window record and light plan.** `packages/game-core/src/interior/interiorWindows.json`
   (`INTERIOR_WINDOWS_SCHEMA`), written by `tooling/volumetrics/interior_light.py`
   at every interior publish: per cell its kind, dust class and windows
   (`apertures`: centre, outward normal, width, height, up, `opening` kind).
   Openings are found by geometry and material, never a texture name: `pane`
   (a glow-mapped or glass material, kept only as an upright flat plate, so
   bottles and fires drop out), `node` (a mesh under a NIF node named a
   window or porthole, or a whole window piece), `shell` (a light-ray shaft
   static). Each row carries `lightPlan` `{schemaVersion 1, openings[{kind,
   centre, normal, size}], zones[{id, centre, radius, daylight, dark}],
   darkFraction, entranceDark, bundleHash}`: zones are the rooms clustered
   from the floor reached from the doors (per floor level, farthest-point
   seeds 3.5 m apart), `daylight` the openings' share of a zone's light
   (each opening a sky patch, no occlusion), `dark` over half its nodes
   under E 0.12 from sources and ambient; `entranceDark` the floor within
   3 m of a door's arrival marker reads dark. The plan is cached by the
   bundle's hash; `--rule-change` re-measures all. Gate `interiors.dark`
   (`place_gates.dark_gate`) fails a claimed cell over 30 % dark or dark at
   the entrance. The runtime puts candles out by day only in zones whose
   daylight is at least `ZONE_DAYLIT_MIN` (§8).
2. **Ambient is a floor.** The applied ambient is the cell's cube times
   `AMBIENT_FLOOR`; at night a moon hemisphere (`MOON_HEMI`, moon-tinted,
   both moons' fraction and size summed over a starlight floor
   `NEW_MOON_HEMI_FLOOR` .75, so a new moon is .4 of a full Masser) that enters only through the windows: times
   `apertureFactor` (window area over `MOON_APERTURE_FULL_M2`, capped at 1;
   0 in a windowless cell). A constant neutral night fill, `NIGHT_FILL_E` 0.06
   irradiance (`interiorNightLight.json` `nightFillE`, below `DARK_E`, so the fill
   alone never passes a cell), lights every cell, windowless ones included; the
   runtime (`nightFill` ambient light), the dark gate (`interior_light.irradiance`)
   and the night render add the same value. A cell's exposure is its measured record in
   `packages/game-core/src/interior/interiorExposure.json` when it has one
   (exposure = clamp(.0449 / the cell's noon-clear pre-exposure mean over the
   loop's three poses, 1, `INTERIOR_EXPOSURE_MAX` 6); .0449 is the station
   house's noon display mean, so DawnstarBrinasHouse keeps 1.652), else the
   ambient-derived exposure (`interiorEnvironment.ts`); either way the
   ambient cut darkens the room instead of being undone by eye adaptation. A
   newly measured cell gets its row from the loop's noon-clear tiles.
3. **Windows.** Each window's world bearing is the cell's world yaw
   (`cellWorldYaw`: door bearing against the arrival marker) plus its
   outward normal. One `RectAreaLight` per window (at most
   `WINDOW_LIGHTS_MAX`, ranked by facing then area; the rest glow only),
   seated `PANE_SEAT_M` inside the pane and inset `RECT_EDGE_INSET_M` off
   every aperture edge with its intensity raised by the area ratio
   (`insetRect`: same flux, but the header's underside and the sill's top,
   millimetres from a full-size rect's edges, no longer light up as a
   bright line along the window strip's lip). Its light is the sky share only
   (`skyShare`: rises from civil twilight, dimmed by `OVERCAST_SKY_DIM` and
   greyed by the weather's `sunDim`/`skyGrey`, warmed by a low clear sun):
   a RectAreaLight casts no shadow, so sun in it lights every wall evenly.
   The direct share (`directShare`: sun up, times cosine facing
   `windowFacing` from `FACING_MIN` to `FACING_FULL` 1, times the rig's
   `directFactor`) drives the beam and the shadowed sun. After sunset the
   brightest moon (`brightestMoon`: illuminated fraction times apparent
   size) adds to the rect at `MOON_SHARE` x `WINDOW_MOON_INTENSITY`, tinted
   `MOON_TINT`; the moon never lights a window by day. The moon is the
   outdoor sky rig's own (phase and position from `lightRig`, no second
   ephemeris) and lights the windows in sleeping hours too.
4. **One shadowed sun per cell.** A `DirectionalLight` far outside along
   the dominant direct source (sun, else moon), carrying all the sun's
   energy (`WINDOW_SHADOW_SUN_INTENSITY`, at least twice a sky-lit rect),
   or by night the moon's at `WINDOW_SHADOW_MOON_INTENSITY` per unit of moon
   level (a facing full Masser lands a faint patch beside the sleeping-hours
   hearth; at the sun's gain it was never seen), its elevation clamped to
   `LIGHT_ELEVATION_MAX_RAD`, shadow box fitted over the cell,
   `SHADOW_MAP_SIZE`, `autoUpdate` off. It is re-aimed and its map marked
   for the loop's shadow cadence once it has turned `SHADOW_STEP_TEXELS`
   (a quarter) of a shadow texel across the cell, so the patch moves in
   sub-texel steps the PCF filter hides without a pass every frame; a turn
   past `SHADOW_JUMP_SQ` (cell entry, sun to moon) asks for the next
   frame's pass (§9). Interior
   meshes cast and receive shadows, so the sun lands as a patch through the
   openings.
5. **Panes glow.** The pane emissive carries the light's hue, capped by
   luminance at `PANE_MAX` (`capColour`) against `PANE_REF_INTENSITY` (the
   clear-noon rect), so a dusk pane reads warm, an
   overcast one grey, a night one a faint moon glow. The pane's diffuse
   colour is `PANE_DIFFUSE`, so the glass shows the sky, not the room's light.
   The emissive is masked by the pane's own glow map (the NIF's Glow_Map,
   carried as the glTF emissive texture, e.g. `FarmWindowInterior01_m`), so
   only the glass glows; the diffuse, which carries the frame and mullions,
   masks it only on a pane with no glow map.
6. **Volumetric beams.** `packages/game-core/src/render/volumetricBeam/`
   draws one beam per sun-facing window from `BEAM_START_OUT_M` outside the
   pane: a ray-marched frustum with a soft luminance knee (`KNEE_L` to
   `KNEE_MAX_L`, hue kept), thickness from the cell's dust class
   (`DUST_PER_M`), streak contrast falling on long shafts, faded near the
   camera by its distance to the shaft (`beamProximityFade`). A shaft
   runs until the room's geometry stops it (`geometryReach`, cast on the
   CPU only when the beam re-aims: the axis ray's first hit past
   `REACH_SKIP_M`, beyond the window's own reveal, frame and mullions, sets
   the length; an axis that reaches the floor landing keeps it, else the
   four hull-corner rays clip it with hits past `REACH_CORNER_MIN_M`; a
   re-cast length is eased in over `REACH_EASE_TAU_S`, a first cast snaps;
   the beam pass draws into the scene target whose
   depth it would need, so no depth clip), and its scattering is scaled
   by min(1, reach / `BEAM_ROOM_SCALE_M` 2 m) so a small hut's shaft is not a
   slab. Its dust motes move on the air's own motion chunk
   (`packages/game-core/src/air/airMotion.ts`, shared with the pollen and
   fireflies): the mote field sways at pollen's rate by
   `MOTE_SWAY_OF_POLLEN` of its wander, each mote wanders inside its cell
   (`MOTE_WANDER_CELL`, `MOTE_WANDER_HZ`) and fades on the firefly envelope
   over `MOTE_FADE_S` above `MOTE_FADE_FLOOR`, with `MOTE_FADE_GAIN`
   holding the mean mote brightness. The module
   has no interior assumptions, so outdoor canopy shafts can use it.
7. **Sources.** Each record light is classed by the nearest fixture or
   flame within `FIXTURE_NEAR_M` (hearth, candle, lantern, other; none is
   fill). Its reach is a physical pool per class, `fixtureReach` = the
   smaller of the authored radius and `FIXTURE_REACH_M`; fill lights run at
   `FILL_SHARE`.
8. **Fixture schedule** (`fixturePhase`, walk 11 planner ruling, per zone
   since walk 12). In an inhabited (`INHABITED_KINDS`) cell a candle or
   lantern whose light-plan zone (`zoneOf`) has daylight at least
   `ZONE_DAYLIT_MIN` 0.12 is out while the sun stands at or above
   `CANDLES_LIT_BELOW_SUN_RAD` (5 deg) and lit below it, so dusk warms as
   they come on; the hearth, other and fill lights burn. A fixture in a
   zone the windows do not reach (a basement, a windowless cell, a cell
   with no plan) stays lit through waking hours. In every cell's sleeping hours
   (`SLEEP_START_MIN` to `SLEEP_END_MIN`) candles, lanterns, other and fill
   lights go out; the hearth stays; a cell with no hearth keeps its smallest
   one or two. Flames follow their light's level; lights toggle intensity
   only and ease over `LIGHT_EASE_TAU_S`.
9. **Shadow cadence.** The render loops redraw shadow maps every other
   frame. `shadowRefresh.ts` lets a light owner ask for the next frame's
   shadow pass (`requestShadowRefresh`, a flag on the scene root's
   userData, read by `shadowFrameDue`), so a cell entered on an odd frame
   never draws from an unrendered map. The sun's map is requested at
   creation: with no map, three r184 binds its empty shadow texture without
   a compare mode and every standard draw raises GL_INVALID_OPERATION and
   is dropped.

**Verification** is the loop, `tooling/visual-look/interior-light-loop.mjs`
(header gives the job_guard and `HARNESS_PORT` line): the real package
runtime in headless Chromium over the states 09:00, noon clear, noon
overcast, 16:30, dusk, 20:30, 23:30 full moon and 23:30 new moon, one
contact sheet per cell. A tile faults (`interiorLightArgs.mjs`
`tileFaults`) on too few draws or triangles, a GL error in the main pass,
window lights adding too little, too much of the frame clipping, or a
framed sunlit beam that lights no pixel or adds too little against the
window light on the pixels it lights.

## Consequences

- Frame time (SwiftShader, 640x360, DawnstarBrinasHouse, run-perf and
  run-perf2 under machine load 13-20): window rects and the shadowed sun are
  the bulk of the lighting cost (switching either off cut the frame by
  ~70-80 % in the load-contaminated run); the beam's cost is below the
  measurement noise: interleaved none/nobeam pairs gave +60/+20/+170 ms by
  mean and -270/+10/-100 ms by per-frame median (+20 ms and +10 ms on the
  steadiest pair, against the +20 ms bar), so the bar is neither confirmed
  nor refuted on this machine; a quiet-machine or GPU re-measure decides it.
- Judged result after round 15 (two readers per sheet, mean, 0-10
  against the owner bar): station house (DawnstarBrinasHouse) 7.0; with
  measured exposure the Keeba houses Crafter 5.5, Fisher 5.5, SnailMinder 5.5
  (before it 3.75 / 5.25 / 4.5). Open rows: overcast panes stay warm in the
  Keeba cells (not grey); new moon crushed away from the hearth; panes and
  the Crafter 16:30 beam clip and read as hard-edged slabs; Keeba doorway
  views stay under the station house by day; 09:00 shaft absent in the
  station house.
- `tooling/volumetrics/` is WebGPU-era, but `interior_light.py` and its
  window-mesh reader write the live window record: any WebGPU retirement
  keeps them (or moves them to one home with the other interior tooling).
- Every published cell gets its row and light plan in `interiorWindows.json`
  from the exporter's run; gate `interiors.dark` reads it.
- A new interior with windows also needs its exposure row
  (`interiorExposure.json`) from a loop noon-clear capture.
- Place-builders do nothing per cell: the model applies to every interior
  (place-build reference `doors-interiors-sockets.md` § 3 and § 7, reader
  row 48).
