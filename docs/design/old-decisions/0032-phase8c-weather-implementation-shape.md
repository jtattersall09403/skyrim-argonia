<!-- imported unchanged from elder-souls-argonia docs/decisions/0032-phase8c-weather-implementation-shape.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0032 — Weather and atmosphere: one synoptic timeline, expressed regionally

**Status** accepted · **Research**
[weather-clouds-rain-threejs](../research/rendering/weather-clouds-rain-threejs.md),
[black-marsh-climatology](../research/world-terrain/black-marsh-climatology.md) ·
**Spec** [module 55](../world/55-light-sky-time.md) §97–98 · **History** the
[round log](../research/archive/weather-8c-rounds/0032-round-log.md) and the
[closing run-book](../research/archive/weather-8c-rounds/0032-runbook.md),
which maps each kind of feedback to the table or constant that owns it

## Decisions

1. **One synoptic timeline, regional expression.** The province is one real
   weather cell, so one seeded state machine (`packages/world-weather`)
   drives the map: multi-day monsoon active and break spells, then 90-minute
   slots rolled from weights by spell, season and time of day. Regions differ
   through local expression of the same state via the climate fields (rain
   amplitude, storm exposure, sea fog, mist propensity, canopy, elevation): a
   squall is violence on the open coast and gusty overcast inland. Weather
   never pops at a region border.
2. **Everything is a pure function of epoch minutes.** Spells and slots are
   hash-seeded; wetness is a closed-form trailing integral of rain; radiation
   mist derives from whether last night was clear and calm; lightning times
   are hashed per slot. Fully scrubbable; a URL reproduces the frame; saves
   need no weather record. No `Math.random` or `Date.now` in world systems.
3. **Ground mist is a computed condition, not a rolled state**: radiation
   mist (basin dawn after a clear calm night), advection sea fog (coast and
   estuary mornings), cloud-forest whiteout (an elevation belt, asymmetric so
   summits clear it). Weather supplies only the fourth fog source (rain veil,
   dry haze). All four feed the one aerial-perspective authority.
4. **Tropical rhythms are structural**: an afternoon-peaked convection factor
   builds inland storms through midday; squall lines live in monsoon break
   spells with the one fast transition; dry-season haze is a real state.
5. **Clouds are procedural layers in the envelope-pinned dome**
   ([0021](0021-phase8a-gate-defect-fixes.md)), so weather cannot break the
   luminance gates; one shared GPU and CPU cloud field
   (`sky/cloudField.ts`). Volumetric clouds are a high-tier polish item.
6. **Rain** is GPU-instanced streaks in a camera-following volume, density ×
   local rain × (1 − canopy), on its own real-time clock, never the game
   clock; splashes stamp the ripple simulation.
7. **Wet surfaces**: one global wetness scalar into the ground-wetness path,
   scaled by 1 − canopy.
8. **Weather owns the wind**: direction wandering about the prevailing wind,
   speed and gusts; renderer and CPU water query read the same wind scale, so
   what you see is what you float on.
9. **Published to gameplay**: `EnvironmentContact` carries a weather block
   (state, rain, wind, visibility, wetness, grip) and
   `TimeLightSample.visibilityM` is real, so AI perception, encounters and
   traction read the authority the renderer draws. One call feeds both the
   renderer's region haze and the published visibility.
10. **The light rig takes a weather modifier** (sun dim, ambient lift, sky
    grey, turbidity) inside the envelope model; overcast kills shadows. The
    studio has a force-state override and `w=` parameter for preview; the
    game ships only the automatic calendar.

## Hard rules

- Fog colours are derived from the real light, never authored per state;
  there is no camera-altitude sky veil.
- Every authored sky, cloud or rain luminance is a screen value divided by
  `exposureTarget`, never a raw HDR constant; the dome's Mie coefficient is
  never raised.
- Any change to the dome shader, cloud colours or exposure keeps
  `WorldSky.createSkyDome`, `sky/skyScreenModel.ts` and `sky/lightRig.test.ts`
  in agreement.
- Real-world climate scale lengths are compressed about 10× for the province,
  or the fields come out flat.
- `GAME_TIME_SCALE` (30, Morrowind's) is calendar only; physical motion never
  scales by it.
- The climate rasters are baked from the raw vault `heightfield-f32.npy`,
  never `province-refined/`.
