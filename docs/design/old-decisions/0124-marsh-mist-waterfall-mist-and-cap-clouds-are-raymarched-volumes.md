<!-- imported unchanged from elder-souls-argonia docs/decisions/0124-marsh-mist-waterfall-mist-and-cap-clouds-are-raymarched-volumes.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0124 — Marsh mist, waterfall mist and mountain cap clouds are raymarched volumes

**Status:** accepted. Cap clouds ship on by default for the owner's
judgement; the marsh mist is below its bar (§ Open).

## Context

The owner asked for soft, low-lying marsh mist below eye level over water
and the wet ground around it, with a very slow morph; thicker after a rainy
night, burning off on sunny days, thicker under overcast; no sea fog;
colour from the sky; a mysterious, slightly spooky, steamy tropical marsh.
The bar is the reference image
`docs/research/rendering/volumetric-bars/marsh-mist-reference-nexus-33017.jpg`,
judged at 90 percent or better by an image reader, side by side. The owner
also asked for cap clouds on the montane belt and for waterfall mist.
On the proxy frame soft-particle billboards (the owner's wording) scored
about 30 percent at up to twice the frame cost and Skyrim-style sheets 15
percent at 2.5 times, against 50 to 55 percent for a thin-slab raymarch at
about the no-fog cost; for cap clouds billboards and sheets never read as a
slope-hugging band. So all three are raymarched volumes.

## Decision

### Marsh mist

1. One full-screen thin-slab raymarch at reduced resolution
   (`packages/game-core/src/air/marshMist/`), run through the pre-bloom pass
   slot of `WaterPipeline`. In-scatter comes from the lighting uniforms and
   the measured floor only, never the scene colour. The composite is
   display-referred, `toScreen(fog) + canvas * (1 - a)`, so it only obscures.
   The march ends at `min(scene depth, water surface depth)` (`WaterDepthPass`
   draws each water surface with its own material, depth-only, at the mist's
   resolution when a water mesh is in view, so the surface's own height and
   coverage stop the march). Skipped under water and when `mistAmount` is
   about zero; `?mist=0` mounts none.
2. `mistAmount` orders: dawn after rain, then dry dawn, then night, then
   overcast dusk, far above sunny noon. There is no floor: a clear sunny noon
   burns the mist off; by day only cloud, rain and recent rain keep it. There
   is no sea fog.
3. The wet mask is water plus 20 m of shore, never sea or coast, rasterised
   over a camera-centred rectangle and rebuilt off the hot path.
4. The 3D noise is procedural, generated in code; nothing is downloaded.
5. Every noise octave is sampled at the world point; only the march is
   camera-relative. Step length is a fixed fraction of the distance along
   the ray (high tier 0.1 × t clamped 0.75 to 8 m, at most 44 steps; low
   0.22 × t clamped 1.5 to 14 m, at most 20); the jitter is keyed to the
   world view direction, never the screen pixel; steep rays sample between
   world planes `MIST_PLANE_DY_M` apart, so walking does not drag the
   pattern. The high tier adds a world-anchored 24 m octave from 40 to 100 m.
   Density is one GLSL function, `mistRho`.
6. The target is 0.67 per axis (high) or 0.35 (low), then a 5×5 depth-aware
   blur and a slope-predicted upsample, with a ±0.5/255 dither. Harnesses:
   `apps/world-studio/scripts/outdoor-fx-walk.mjs` and
   `MistMarch.anchor.test.ts`.
7. Distance bands: clear to 2 m, ramping to full by 8 m, fading 120 to
   150 m, march ends at 150 m. The slab top is 1.45 m at full amount and is
   clamped below 1.6 m, under a 1.7 m eye.

### Waterfall mist

8. Each placed fall carries one analytic raymarched volume
   (`WaterfallMistVolume`, 20 steps), derived from its cascade record and
   traced arc, never placed by hand: a lip spray, a sleeve veil along the
   arc weighted to the lower part, and a pool haze over 1.2 times the bowl.
9. Strength follows `mistAmount` read as "river": spray always shows; the
   pool haze is about five times stronger at a wet dawn than at a clear noon.
   In-scatter is a cool grey-white with a forward lobe toward the sun, on
   world-anchored drifting noise. Faded 120 to 150 m; at most 6 falls a
   frame. Proxy loop: `apps/world-studio/scripts/waterfall-fx-loop.mjs`.

### Cap clouds

10. Each summit that qualifies on the frozen height raster (at most 16; 10 in
    the province) gets a raymarched soft deck 2.6 times the summit's
    prominence across, wrapping it and draping lower near the peak, which pokes
    through (`packages/game-core/src/air/capClouds/`).
11. All decks are one instanced box draw at 24 steps per pixel and full
    resolution, each step with a Beer-powder self-shadow tap toward the sun;
    the march stops at the terrain; culled beyond 8 km, hidden at coverage 0.
12. Coverage follows the weather and clock through the mist driver: most
    when overcast and after rain, none at a clear dry noon; `&caps=0` turns
    it off. Colour is `capCloudColour` (GLSL `capColour`) off the sky dome's
    cloud colours, darkened by the weather's sun dim. The deck drifts with the
    weather's wind (`capWindStep`) and leans downwind.
13. **Walking into a cap is walking into fog.** Inside a deck the near 160 m
    is marched and the aerial uniform `uCapFog` carries extinction per metre
    (`capFogExtinction`, `CAP_FOG_VISIBILITY_M`), applied over the first
    `CAP_FOG_REACH_M` of every surface path and the dome march; `WorldSky`
    caps the published sight distance to match.
14. The wet mask, drivers and noise are shared by all three volumes.

## Consequences

- Billboard and sheet mist code, their textures and the proxy variants do
  not exist. `WaterPipeline`'s pre-bloom pass slot serves other full-screen
  effects. The sunny-noon mist pass costs nothing.
- Cap clouds are the one summit cloud; the haze and fog field of
  [world 55](../world/55-light-sky-time.md) is weather fog, region haze,
  radiation mist and advection fog.
- The GPU cost is unmeasured; it is read on a pod boot.

## Open

The marsh mist reads well below the 90 percent bar in the studio. What is
missing, worst first: near water is still mostly clear and the mist does not
layer with distance; the far band has a hard flat top; the colour is
neutral, with no warm dawn tint or sun glow; no drift is visible over 30 s;
a faint smear reaches the near bank. Waterfall mist lacks a turbulent plume
at the base, droplet speckle and lit hollows. Cap clouds keep a swirl in the
dark core from the 80 m octave; their inside view is measured by
`apps/world-studio/scripts/capcloud-fx-loop.mjs`. The next judgement on all
three is the owner's walk. Scores and the measured rounds:
[rendering-decision-rounds/0124](../research/archive/rendering-decision-rounds/0124-as-recorded.md).
