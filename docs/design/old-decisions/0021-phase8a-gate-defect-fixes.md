<!-- imported unchanged from elder-souls-argonia docs/decisions/0021-phase8a-gate-defect-fixes.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0021 — The light stack: rules learned from its owner gate

**Status** accepted · **Amends** [0020](0020-phase8a-light-implementation-shape.md) ·
**Evidence** the eight owner rounds are
[archived](../research/archive/light-8a-rounds/0021-as-recorded.md); the
research is `docs/research/` light stack §8

The light stack first failed only in character view while every fly-view
probe passed. **Probe the mode the owner actually plays.** The rules below are
classes of bug, each with the fix that now holds it.

## Lifetimes and React

- `CSM.dispose()` does not detach cascade lights; `remove()` does. Cleanup
  calls both; cascade lights are tagged `csm-cascade` and orphans are swept on
  commit. Read an addon's source, not its method names.
- React discards suspended renders without cleanup, so nothing mutates the
  scene from a `useMemo`, and the physics subtree has its own `<Suspense>`.
- The sky probe asserts a **light census** (three cascades, moon, hemisphere)
  and runs character-view scenarios.
- Shadows are set as `shadows="soft"` on the Canvas, since r3f re-applies its
  default over the renderer.

## Physics stepping

The studio runs `<Physics paused>` and `CharacterDriver` steps at most
3 × 1/60 s per frame via `rapier.step()`, dropping excess time: brief slow
motion under load, never a catch-up spiral. Physics unpauses only after
colliders and smooth frames (`RenderWarmup`). The streaming safety net
teleports only when the CPU height claim and a physics ray agree there is no
floor, rate-limited to 1.5 s. The camera rejects non-finite positions and
hard-resets on a jump over 40 m; its body never drops below `minPosPitch`,
and extra look-up raises the look target instead.

## Sky and exposure

- **Dome brightness is pinned by construction.** The rig normalises the
  Preetham dome against a CPU port of the shader (`preethamCpu.ts`) to one
  authored perceptual curve (`skyScreenTarget`); `lightRig.test.ts` walks the
  whole day × humidity asserting screen luminance stays in range.
  `skyScreenModel.ts` is the shader's CPU twin and stays in lockstep with the
  dome patch. Never hand-tune dome scale against exposure: change
  `skyScreenTarget` (sky) or `EXPOSURE_CURVE` (ground) and let the test
  verify.
- Dome Mie is pinned at the addon default (0.005), turbidity capped; the
  humid-lowland glow is the aerial term's job, not the dome's.
- Exposure is an authored log-interpolated curve over sun altitude with a
  mid-day plateau; eye adaptation runs in world time. The PMREM IBL is the one
  sky-ambient authority; the hemisphere light is a ground-bounce supplement.
  The IBL re-bake threshold tightens near the horizon so ambient steps never
  flash.
- The night is an authored gameplay floor, as Skyrim does it: the night dome
  is authored in screen-linear terms and divided by the moon-driven exposure
  (moonlit sky about 1.7× moonless), and the hemisphere floor is
  exposure-anchored so dusk land is never pitch black.
- Directional twilight: per-pixel twilight progress, Earth's shadow with the
  Belt of Venus, stars appearing by magnitude anti-solar first, a tropical
  twilight palette (golden-peach core, coral spread, lavender wash).
- The dome's lower hemisphere is replaced with a CPU-computed ground-bounce
  colour; never gate correctness on `isnan()` in a shader.

## Sun, moons, stars

- Sunlight follows a three-stop colour-temperature ramp (2000 K horizon,
  3400 K golden band, 5500 K by about 35°), with a `warmthBias` default of 1.0.
- Moons are display-referred with a sharpened terminator, are no light source
  while the sun is up, and write depth so stars behind a disc fail the depth
  test. The phase ephemeris is correct; never "fix" phases there.
- About 3,300 background stars share the constellation buffer, so the whole
  sky wheels together.

## Also

CSM shadow bias −6e-5 with normal bias 0.05 keeps shadows on the feet. Only
the LOD-1 ring casts shadows; chunk-decode re-renders coalesce to one per
250 ms. City markers are UI (`toneMapped={false}`). A defect report taken
against a hot-reloading dev server is re-checked after a restart and hard
refresh.
