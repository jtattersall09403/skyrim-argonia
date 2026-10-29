<!-- imported unchanged from elder-souls-argonia docs/decisions/0123-interiors-are-lit-by-their-sources-windows-and-beams.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0123 — Interiors are lit by their own sources and, by day, their windows and beams

**Status:** accepted. **Supersedes:** the window-daylight rule of
[0109](0109-interior-additions-add-kit-pieces-to-a-tier-a-cell.md), which
keeps the additions and the fixture design rule.

## Context

The owner's bar: a room is lit almost entirely by its local sources
(hearth, candles, lanterns) plus its windows in daylight; windows read as
sources by day; the room changes visibly with the time of day; the look is
close to the saved references
(`docs/research/rendering/volumetric-bars/god-rays-*.png`). One point light
per window primitive over a flat ambient that rose with the sun whatever the
window faced was too bright and the same at every hour.

## Decision

One module, `packages/game-core/src/interior/interiorLighting.ts`
(`InteriorLighting`, pure functions first), lights every interior; the
loader builds it for every cell (`interiorLoader.ts` `instantiateInterior`).
Inputs are a plain struct built from the drawn sky rig (sun, moons,
weather), so the package imports nothing from an app. Lights are created
once at load and only their intensities and aims change, when the inputs
move past an epsilon (`DIR_EPS` 1e-6 for the sun and moon directions, so a
running clock is followed every frame and a paused one costs nothing);
nothing allocates per frame. Constants are named here, never valued: the
loop tunes them.

0. **Record falloff.** A plugin light's falloff exponent
   (`raw.recordFalloffExponent`) is the bundle's `falloffExponent`, never a
   constant. Irradiance = intensity × clamp(1 − d/R, 0, 1)^exponent
   (`falloffWindow` in `interiorLightClasses.json`), zero at the radius; the
   exporter (`worldgen/interior_light.py` `skyrim_curve`) fits `fade` to
   Skyrim's `1 − (d/r)^2`. One form, four evaluators: the runtime
   (`interiorLightFalloff`; the fixture shader reads the exponent from its
   decay slot), the render (`interior_render.py`, `render_interior.py`) and
   the exporter. There is no decay mapping (a decay of twice the exponent put
   lights out far inside their radius). `test_interior_light.py` holds the
   calibration.
1. **Window record and light plan.** `interiorWindows.json`
   (`INTERIOR_WINDOWS_SCHEMA`), written by `tooling/volumetrics/interior_light.py`
   at every interior publish: per cell its kind, dust class and windows
   (centre, outward normal, width, height, up, `opening` kind). Openings are
   found by geometry and material, never a texture name: `pane` (a glow-mapped
   or glass material kept only as an upright flat plate), `node` (a mesh under
   a NIF node named a window or porthole), `shell` (a light-ray shaft static).
   Each row carries a `lightPlan`: rooms clustered from the floor reached from
   the doors, each zone's `daylight` share and `dark` flag, the cell's
   `darkFraction` and `entranceDark`, cached by the bundle's hash
   (`--rule-change` re-measures all). Gate `interiors.dark`
   (`place_gates.dark_gate`) fails a claimed cell over 30 percent dark or dark
   at the entrance.
2. **Ambient is a floor.** The applied ambient is the cell's cube times
   `AMBIENT_FLOOR`. At night a moon hemisphere (`MOON_HEMI`, both moons'
   fraction and size summed over a starlight floor) enters only through the
   windows, scaled by window area (`apertureFactor`, zero in a windowless
   cell). A constant neutral night fill (`interiorNightLight.json`
   `nightFillE`, below `DARK_E`, so the fill alone never passes a cell) lights
   every cell; the runtime, the dark gate and the night render add the same
   value. A cell's exposure is its measured row in `interiorExposure.json`
   (from the loop's noon-clear tiles) when it has one, else the
   ambient-derived exposure (`interiorEnvironment.ts`), so the ambient cut
   darkens the room instead of being undone by eye adaptation.
3. **Windows.** Each window's world bearing is the cell's world yaw
   (`cellWorldYaw`: door bearing against the arrival marker) plus its normal.
   One `RectAreaLight` per window (at most `WINDOW_LIGHTS_MAX`, ranked by
   facing then area), seated `PANE_SEAT_M` inside the pane and inset
   `RECT_EDGE_INSET_M` off every edge at the same flux (`insetRect`). Its light
   is the sky share only (`skyShare`: rises from civil twilight, dimmed and
   greyed by the weather, warmed by a low clear sun). The direct share
   (`directShare`: sun up, times facing, times the rig's `directFactor`)
   drives the beam and the shadowed sun. After sunset the brightest moon
   (`brightestMoon`) adds to the rect, tinted `MOON_TINT`; the moon is the
   outdoor sky rig's own and never lights a window by day.
4. **One shadowed sun per cell.** A `DirectionalLight` far outside along the
   dominant direct source (sun, else moon) carries its energy, elevation
   clamped, shadow box fitted over the cell, `autoUpdate` off; it is re-aimed
   once it has turned a quarter of a shadow texel across the cell
   (`SHADOW_STEP_TEXELS`), and a large turn asks for the next frame's pass.
   Interior meshes cast and receive shadows, so the sun lands as a patch.
5. **Panes glow** with the light's hue, capped by luminance (`capColour`,
   `PANE_MAX`), masked by the pane's own glow map so only the glass glows;
   the pane's diffuse is `PANE_DIFFUSE`, so the glass shows the sky.
6. **Volumetric beams.** `packages/game-core/src/render/volumetricBeam/`
   draws one beam per sun-facing window: a ray-marched frustum with a soft
   luminance knee, thickness from the cell's dust class, faded near the
   camera (`beamProximityFade`). A shaft runs until the room's geometry stops
   it (`geometryReach`, cast on the CPU only when the beam re-aims, eased in
   over `REACH_EASE_TAU_S`), and its scattering is scaled by reach so a small
   hut's shaft is not a slab. Its dust motes move on the air's motion chunk
   (`packages/game-core/src/air/airMotion.ts`, shared with pollen and
   fireflies). The module has no interior assumptions.
7. **Sources.** Each record light is classed by the nearest fixture or flame
   within `FIXTURE_NEAR_M` (hearth, candle, lantern, other; none is fill);
   its reach is the smaller of the authored radius and `FIXTURE_REACH_M`;
   fill lights run at `FILL_SHARE`.
8. **Fixture schedule** (`fixturePhase`). In an inhabited cell a candle or
   lantern whose zone has daylight at least `ZONE_DAYLIT_MIN` is out while the
   sun stands at or above `CANDLES_LIT_BELOW_SUN_RAD` and lit below it; the
   hearth, other and fill lights burn; a fixture in a zone the windows do not
   reach stays lit through waking hours. In sleeping hours (`SLEEP_START_MIN`
   to `SLEEP_END_MIN`) candles, lanterns, other and fill lights go out; the
   hearth stays; a cell with no hearth keeps its smallest one or two. Flames
   follow their light's level; lights ease over `LIGHT_EASE_TAU_S`. Exterior
   window glow follows the same bedtime
   ([0138](0138-people-and-creatures-live-by-the-place-record-and-the-lamp-clock.md)).
9. **Shadow cadence.** Shadow maps redraw every other frame; a light owner
   asks for the next frame's pass through `shadowRefresh.ts`
   (`requestShadowRefresh`, `shadowFrameDue`), and the sun's map is requested
   at creation, since an empty shadow texture without a compare mode drops
   every standard draw with GL_INVALID_OPERATION.

**Verification** is the loop, `tooling/visual-look/interior-light-loop.mjs`:
the real runtime in headless Chromium over 09:00, noon clear, noon
overcast, 16:30, dusk, 20:30 and 23:30 under a full and a new moon, one
contact sheet per cell, faulting a tile (`interiorLightArgs.mjs`
`tileFaults`) on too few draws, a GL error, window light too weak, too much
clipping, or a framed sunlit beam that adds too little.

## Consequences

- Every published cell gets its row and light plan in `interiorWindows.json`
  from the exporter; a new interior with windows also needs its exposure row.
- `tooling/volumetrics/interior_light.py` and its window-mesh reader write
  the live window record and stay with the interior tooling.
- Place builders do nothing per cell: the model applies to every interior.
- Evidence, frame costs and judged scores:
  [rendering-decision-rounds/0123](../research/archive/rendering-decision-rounds/0123-as-recorded.md).
