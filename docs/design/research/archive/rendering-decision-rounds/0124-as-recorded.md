<!-- imported unchanged from elder-souls-argonia docs/research/archive/rendering-decision-rounds/0124-as-recorded.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0124 — Marsh mist, waterfall mist and mountain cap clouds are raymarched volumes

Evidence: decision 0124 as it stood before it was rewritten as one current document; the record itself is [0124](../../../old-decisions/0124-marsh-mist-waterfall-mist-and-cap-clouds-are-raymarched-volumes.md).

Status: accepted (16k walk 11, outdoor-fx lane, 2026-10-04). The marsh mist
reached 25 to 30 % in the studio and 40 to 45 % on the proxy frame against a
90 % bar (see Open). Cap clouds ship, default on, for the owner's judgement.

## Context

Owner, 2026-10-03: soft, low-lying marsh mist below eye level over water
and the wet ground around it, with a very slow morph; thicker after a rainy
night than a dry one, burning off and thinning on sunny days, thicker under
overcast; no sea fog; colour from the sky; a mysterious, slightly spooky,
steamy tropical marsh. The ask named "soft particle mesh fog" in the manner
of composer-suite. The quality bar was the reference image
`docs/research/rendering/volumetric-bars/marsh-mist-reference-nexus-33017.jpg`,
judged at 90 % or better by an image reader, side by side, on a proxy scene
(real vegetation, studio-like terrain, basic water, a lighting proxy). The
owner also asked for cap clouds on the montane belt and for waterfall mist.

## What was measured

All on the fair proxy frame (eye 1.7 m over a 0.4 m bank, backlit far bank
about 130 m away), SwiftShader, scored by image readers against the
reference.

| Technique | Reader score | Cost |
| --- | --- | --- |
| Soft-particle billboards (the owner's wording) | 30 % | 1.2 to 2.3 times the no-fog frame |
| Skyrim-style sheets | 15 % | 2.5 times the frame |
| Thin-slab raymarch | 50 to 55 % | about the no-fog frame |

The shipped slab, scored by two image readers against the reference:

| Frame | Reader score |
| --- | --- |
| Studio, Greenspring water edge, dawn after rain, eye 1.7 m over water, pitch -6.5, FOV 38 | 25 to 30 % |
| Studio, Riverwalk cove, same pose | under 10 %; frame judged unfair (open sea, no backdrop; mist is meant to be near-absent over sea) |
| Proxy harness round 34 | 40 to 45 % (round 33 scored 45 to 55 % and layered better; round 34 reads as a thicker, warmer, flatter wall) |

Cap clouds, raymarched summit deck (reader scores out of 10, v8 shipped):

| Target | Score |
| --- | --- |
| 3D look | 6 |
| Wraps the summit, wider than the ridge | 7 |
| Inside the cloud, near the eye | 5 (still a flat milky grey in the harness) |

Billboard cap clouds scored 50 % at best (25 to 30 % from the ridge camera)
and Skyrim-style sheets 30 to 35 % at +231 % frame time; neither read as a
slope-hugging band. Evidence images:
`docs/research/rendering/volumetric-bars/cap-cloud-trial-billboards-r3.jpg`
and `cap-cloud-trial-sheets-r7.jpg`.

## Decision

### Marsh mist

1. Marsh mist is one full-screen thin-slab raymarch at reduced resolution,
   in `packages/game-core/src/air/marshMist/`. It runs through the pre-bloom
   pass slot of `WaterPipeline`, after the water surface and before bloom.
   Its in-scatter luminance comes from the lighting uniforms and the
   measured floor only, never from the scene colour (a scene term imprinted
   silhouettes standing above the mist). The composite is display-referred
   over the canvas, `toScreen(fog) + canvas * (1 - a)`, so it only ever
   obscures what the canvas holds, water surface included. The march ends
   at `min(scene depth, water surface depth)`: `WaterPipeline` draws the
   water layer depth-only at the mist's resolution (`WaterDepthPass`, one
   shared override material) when a water mesh survived frustum culling, so
   mist over shallow water never reveals the bed or the plants the surface
   hides. It is skipped underwater and when `mistAmount` is about zero;
   `?mist=0` mounts none (A/B).
2. `mistAmount` carries the owner's ordering: dawn after rain, then dry
   dawn, then night, then overcast dusk, far above sunny noon. There is no
   sea fog.
3. The wet mask is water plus 20 m of shore, never sea or coast, rasterised
   over a camera-centred rectangle and rebuilt off the hot path.
4. The 3D noise is procedural and generated in code. Nothing is added to
   the download.
5. Every noise octave is sampled at the world sample point; only the march
   (ray origin, direction, slab interval) is camera-relative. Step length is
   a fixed fraction of the distance along the ray: high tier 0.1 x t clamped
   0.75 to 8 m, at most 44 steps; low tier 0.22 x t clamped 1.5 to 14 m, at
   most 20. Against a dense march the high tier's sampling error is 0.77
   RMS, against 13.2 for 10 uniform steps, so the puffs do not re-form as
   the eye moves. The step jitter is keyed to the world view direction,
   never the screen pixel. The high tier adds a far rung: a world-anchored
   24 m octave on the slab top and coverage, ramping in from 40 to 100 m.
   On steep rays (an adaptive step crossing more than 0.1 m of height) the
   march samples the midpoints between world planes y = k x
   `MIST_PLANE_DY_M` (0.1 m, scaled by the vertical scale through
   `uPlaneDy`), so walking does not drag the pattern; the plane spacing
   doubles while nested when the slab is deeper than the loop bound.
   Shallow rays keep the jittered adaptive steps. Density is one GLSL
   function, `mistRho`.
6. The low-res target is 0.67 per axis on the high tier and 0.35 on the low
   tier, then a 5x5 depth-aware blur and a slope-predicted upsample. The
   blur compares each tap with the depth the surface slope predicts (a
   one-sided depth slope); the upsample weights taps with exp weights on
   the same prediction. The composite adds a +-0.5/255 interleaved-gradient
   dither where alpha is above 0.004. The far view's softness is the slab
   integrated along a grazing ray, not resolution. Harnesses:
   `apps/world-studio/scripts/outdoor-fx-walk.mjs` (`walkCheck` over the
   real shader) and `MistMarch.anchor.test.ts` (CPU model).
7. Distance bands:

   | Range | Behaviour |
   | --- | --- |
   | 0 to 2 m | Clear |
   | 2 to 8 m | Near clear ramps from 0 to full |
   | 120 to 150 m | Fades out |
   | 150 m | March ends |

   The slab top is 1.45 m at full amount and is clamped below 1.6 m, so it
   stays below a 1.7 m eye.

### Waterfall mist

8. Each placed fall carries one analytic raymarched volume
   (`WaterfallMistVolume`, 20 steps), derived from its cascade record and
   traced arc, never placed by hand.
9. It has three shapes: a lip spray 0.5 of the sheet width across; a soft
   sleeve veil along the traced arc, 0.85 of the width at the lip and a
   quarter of the drop at the foot, weighted to the lower part; and a pool
   haze 0.12 of the drop deep over 1.2 times the bowl.
10. Strength comes from the marsh mist's `mistAmount` over the same driver
    inputs, read as "river": spray always shows, and the pool haze is about
    5 times stronger at a wet dawn than at a clear noon.
11. In-scatter is the light's luminance in a cool grey-white, with a
    forward-scatter lobe toward the sun. The density is world-anchored noise
    that drifts.
12. It fades between 120 and 150 m from the nearest point; at most 6 falls
    draw per frame. Proxy loop: `apps/world-studio/scripts/waterfall-fx-loop.mjs`.

### Cap clouds

13. Mountain cap clouds ship, default on, for the owner's judgement. Each
    summit that qualifies on the frozen height raster gets a raymarched soft
    deck: 10 summits in the province, at most 16. The deck wraps the summit,
    is 2.6 times the summit's prominence across, and drapes lower down the
    flanks near the peak. The peak pokes up through it. Code:
    `packages/game-core/src/air/capClouds/`.
14. All decks are one instanced box draw, at 24 steps per pixel and full
    resolution. Each step adds a Beer-powder self-shadow tap toward the sun,
    so the top is lit and the underside is dark. The decks use the marsh
    mist's seeded noise and add nothing to the download. The march stops at
    the terrain.
15. Coverage follows the weather and clock through the marsh mist driver's
    inputs: most when overcast and after rain, none at a clear dry noon.
    `&caps=0` turns it off.
    Colour comes from `capCloudColour` (GLSL twin `capColour`) off the sky
    dome's cloud colours (`uCloudBright`, `uCloudDark` via
    `drawnLightRigOf`), darkened by 0.45 x sunDim, with height and
    overcast shading, self-shadow only under sun, a forward sun glow, and a
    floor at 0.8 x the deck's luma. `capWindStep` drifts the deck with the
    weather's `windDirXZ` x speed x 0.8 (clamped 0.4 to 10 m/s); the morph
    rate is 0.12 + 0.05 per m/s; both are x1.8 in a gust front
    (`windGustEnvelope`); the deck leans downwind up to 0.12 of its radius.
    Inside a deck the near 160 m (`insideSpanM`) is marched, and the
    aerial uniform `uCapFog` carries extinction per metre,
    `capFogExtinction(insideDensity)` = density x 3 / `CAP_FOG_VISIBILITY_M`
    (45 m), applied over the first `CAP_FOG_REACH_M` (600 m) of every
    surface path and the dome march. `insideDensity` is floored at the
    deck's radial core x coverage x (0.25 + large/small noise) before the
    inside-only near octave, so a dense storm cap gives about 45 to 60 m of
    sight and a thin cap a light haze. `WorldSky` caps `wx.visibilityM` at
    3 / `uCapFog` so the published sight distance agrees. Walking into a cap
    is walking into fog.
16. Cost: 1 draw call, 12 triangles per volume (120 in total), 24 march
    steps plus one sun tap per step per pixel, render-target scale 1.0. At
    most 16 volumes, culled beyond 8 km; the draw hides at coverage 0.
17. The wet mask, drivers and noise of the marsh mist are shared; the
    weather-to-mist mapping (`toPoint`) exists in both `StudioMarshMist` and
    `StudioCapClouds` and is hoisted into one helper when the lane that owns
    `StudioMarshMist` frees it.

## Consequences

- Marsh mist, waterfall mist and cap clouds are three raymarched volumes
  on one driver; billboard and sheet code, their textures and the proxy
  variants do not exist.
- `WaterPipeline` has a generic pre-bloom pass slot, usable by other
  full-screen effects.
- The sunny-noon mist pass costs nothing (skipped, zero draws).
- Cost, measured on SwiftShader on the CPU-only VM, not a GPU number: the
  mist pass reads 0.1 to 0.2 ms on the GPU timer. Whole-frame on/off medians
  are load noise, so no frame-cost claim is made. GPU cost: not measured, no
  pod.
- The aerial-perspective shader has no whiteout regime and
  `packages/world-weather` has no whiteout belt: cap clouds are the one
  summit cloud, and the haze and fog field of
  [world 55](../../../world/55-light-sky-time.md) §97 is weather fog, region
  haze, radiation mist and advection fog.

## Open

The owner's bar for marsh mist is 90 % of the reference's. The best studio
score is 25 to 30 %. Remaining reasons, worst first:

- (a) Near water is still mostly clear, and the mist does not layer with
  distance: there is one bright band at the far waterline.
- (b) The far band has a hard flat top edge across the trunk bases.
- (c) The colour is neutral grey-white in the studio, with no warm dawn tint
  or sun glow. The proxy goes too beige. The in-scatter hue follows
  `fogSunLum`, and the sky carries no horizon colour per view bearing.
- (d) There is no visible drift over 30 s.
- (e) A faint smear reaches the near bank, and a faint haze sits over the
  sea at Riverwalk.

Far detail beyond +4 % is a look decision (a stronger top silhouette or
larger banks at 30 to 60 m); more steps or resolution buy nothing
measurable.

Waterfall mist lacks a turbulent plume at the base rising 2 to 3 times
wider than the fall, droplet speckle in the air around it, and lit hollows
in the noon and side views (the proxy has no image-based lighting).

Cap clouds: the inside view is judged in the studio, where `uCapFog` drives
the sight distance; the harness (`apps/world-studio/scripts/capcloud-fx-loop.mjs`,
states overcast-after-rain, clear-noon, storm, fair-humid; inside and
outside, -20 s shots, `sightM`; `src/outdoorFx/capColour.test.ts` beside it)
measures it. A swirl and ring texture sits in the dark core, from the 80 m small-noise
octave at 24 steps.

The next judgement on all three is on the owner's walk. Owner check
(studio): outside `?view=character&x=3.563&z=0.598&t=15&rate=0.5&w=overcast`,
facing west; inside `?view=character&x=1.633&z=0.598&t=15&rate=0.5&w=overcast`;
compare with `&caps=0`.

## Evidence

Lane reports under `tooling/.reports/16k/walk11/outdoor-fx/` and
`tooling/.reports/16k/walk11/mist-2/` (`fix-a.md` noise anchoring, `fix-b.md`
waterfall mist, `fix-c.md` cap clouds; these report paths are gitignored).
