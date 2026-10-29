<!-- imported unchanged from elder-souls-argonia docs/decisions/0108-performance-architecture-fixture-light-field-ready-materials-view-gated-streaming-fading-tiers.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0108 — Performance architecture: fixture light field, material ready before first draw, view-gated streaming, tiers that fade

**Status:** accepted. **Supersedes:** 0105 R3 (the 16-light cap) and R11
(stepped lit counts). **Extends:**
[0075](0075-lod-is-a-ladder-stepped-from-the-camera.md) and
[0082](0082-vegetation-cells-are-built-once-and-the-gpu-picks-the-rung.md);
[0084](0084-the-frame-is-a-triangle-budget.md) is the frame budget every
rule below is sized against; [0120](0120-kits-stream-per-piece-spawn-ring-first.md)
is the kit streaming. **Standing rules for agents:**
[engineering.md § Performance checklists](../standards/engineering.md#performance-checklists).

## 1. Fixture lights leave three's light list

three bakes the point-light count into every lit program and shades every
light per fragment: lamps as PointLights cost and relink on any count change.

- **`FixtureLightField`** (`packages/game-core/src/render/fixtureLights/`):
  a 100-slot float texture (position + radius, colour × intensity) with a
  runtime count, one field per scene (`fixtureLightFieldOf(scene)`). A
  texture, not a uniform array, which would take most of WebGL2's
  guaranteed fragment vectors.
- `install(material)` injects one loop after `lights_fragment_begin` using
  three's attenuation and `RE_Direct`; `attach(object)` gives each object
  its nearest 8 lamps that reach its bounding sphere
  (`FIXTURE_LIGHTS_PER_OBJECT`; terrain 16). One program for any count.
- **`LIGHTS_CAP` = 100** (`settlement/lighting.ts`), `LIGHTS_ACTIVE_M`
  200 m, a 20 m fade at the band edge; `place_gates` reads the cap.
- **Fixture glow is anchored to exposure and knee-limited**:
  `FIXTURE_SCREEN_GAIN` over `toneMappingExposure` with a per-light tanh
  knee (`esFxScreen`, `esFxKnee`), so a night exposure cannot blow a wall.
- **The carried torch is the one real PointLight**, at a constant count
  (`fx/carriedLightRig.ts`), so lighting a torch relinks nothing.

## 2. A program is linked before its first visible draw

- Materials are patched at draw time (`sky/drawPatcher.ts`, plus a 1 Hz
  sweep); streamed builds go through the sky's lit preparer
  (`setLitPreparer`) and are warmed before they swap in.
- **A program is linked and its uniform blocks bound before its first
  visible draw** through `drawTargetLinker` (`runFirstUse`); late-shown
  meshes are hidden until linked; kit program classes are baked at publish
  (`program_classes.py`) and linked at boot (`kitProgramWarm.ts`). A raw
  `compileAsync` outside `drawTargetLinker` or `RippleSim` fails
  `check_raw_compile.mjs`.
- **Ready waits for warm** (`WarmGate`): per-frame work stable 60 frames.
- Settlement materials are shared per kit and merge per material identity
  (texture tuple + parameters), never per uuid; flame gain and the aerial
  scalars are uniforms (one std140 `EsAerial` block), never program keys;
  every layer render sees the lights (`lightEveryLayer`), so no layer bumps
  the light-state version; water is on its layer at creation.

## 3. Streaming is view-gated and builds once

- A vegetation cell builds once, at the settled LOD (0082); ground-cover
  tiles wait for terrain LOD 1 under all four corners.
- Build order is in view and near first (`viewPriority`).
- Startup budget: 24 ms a frame for the first 6 s, then less
  (`FrameWorkQueue`); ground cover has one 2.5 ms budget for all its work,
  a stable slot per tile, pooled meshes and changed-range uploads.
- **Scene complete** (`sceneCompleteS`, `gpu-lane/measure.mjs`: the last
  resource, load mark or program link): under 10 s where cheap, 15-18 s
  accepted, no long effort below it. The settlement warm links every caster's
  shadow-depth twin with its colour pass, and the fixture fire and glow
  sprites before their textures land (`settlement/warmMaterials.ts`).
  Measured (d6945d26, RTX 5080, cold Riverwalk x3): 17.4 s median, gate 5.5 s
  (1ef89171, same host: 19.9 s); above 10 s: the Limpet twin, the 20 s build wave. Creature models load when a creature enters the 70 m draw ring,
  never at boot (up to 2 MB each, the phone's download), so a late creature
  fetch is not scene arrival.

## 4. Culling works on bounds that can leave the view

- Vegetation tiles: the widened view frustum with hysteresis, casters kept
  by a sweep along the sun (0082 decision 8).
- Ground cover: a 24 m core disc plus 8 wedges, each drawn when a tile box
  meets the frustum (`SectorCuller`, `?gcsec=1|4|8`).
- Settlement buckets split per 48 m square (`SETTLEMENT_CHUNK_M`), each
  with its own bounding sphere; a merged batch's key never reads the
  camera: every LOD level is built and linked before ready, and walking
  only swaps visibility.
- An instanced mesh with 0 instances is never submitted (`drawCount.ts`).

## 5. Vegetation tiers fade, never decimate

- **Part-aware tiers** (`pipeline/tree_tiers.py`): leaves thinned by
  keeping whole source cards per cluster, bark by keeping whole islands.
  The bar is silhouette IoU at least 0.90 in each of 8 views on masks
  closed by a disc of 1.5 percent of the tree's pixel height, no view
  losing more than 5 percent coverage, at the hand-over distance; and the
  image judge is a hard gate beside it (`--record` refuses a level with no
  judge PASS). The share cap is a setting (`treeTiers.maxShare`).
- **Leaf cutoff is the NIF's**: every foliage material ships glTF MASK at
  its NiAlphaProperty threshold / 255; the card bake clips at the same
  cutoff.
- **Octahedral impostors replace the card** for the trees that pass their
  own bar (`pipeline/impostor_bake.py`, game-core `vegetation/impostor.ts`):
  a hemi-octahedral atlas of the tree's own mesh, one quad per instance,
  three frames blended with a depth walk, split on the axis diagonals per
  quadrant. An impostor ships when its silhouette IoU beats the card in
  every view and two image judges pass it. Impostors load after the
  startup window; those species' last mesh level runs to the draw distance
  until they arrive (`withholdCards`).
- The ladder, its screen-size hand-over and its 0.4 s fade are 0075.
- Ground-cover thinning is a per-plant roll against a per-tile,
  distance-ramped threshold (near band never thinned), so walking closer
  never removes a plant shown further out (`groundcoverThin.test.ts`).

## 6. Quality defaults are never lowered to win frames

A frame is won by doing less invisible work (lights nobody sees, copies off
screen, rebuilds, relinks, allocations), never by lowering a visible
default. Canvas MSAA stays on (`?aa=0` is the A/B); `shadowMapSize` is a quality field (low/medium 2048, high 4096).

## 7. Post-processing is bloom only

`packages/game-core/src/render/post/BloomPass.ts`, drawn by `WaterPipeline`
above water after the overlay pass: a half-resolution prefilter of the
linear HDR target plus the flame layer (`BLOOM_SOURCE_LAYER` 7, ×
`flameGain` from `bloom.config.json`), a dual-filter mip chain composited
additively. `BloomPass.gl.test.ts` fails unless a torch's halo reads. No
colour grade (ACES runs in the blit), no `alphaToCoverage`; not drawn under
water, with `?water=0`, or in Fly3D; `?post=0` is the A/B.

## 8. Frame-path rules

- No per-texel, per-cell or per-call allocation in clock- or frame-driven
  paths; `scene.environment` keeps one persistent texture; static meshes
  carry `matrixAutoUpdate={false}`.
- Periodic background passes run under a per-frame budget, keep their
  caches, apply only changed results under a cap, and never start two
  cadences on one frame.
- Water inputs that vary non-linearly (depth, shore distance, exposure,
  crest) are computed per pixel; Gerstner bands shorter than 2.2 grid cells
  go to the fragment normal.
- Data rasters are never decoded through ImageBitmap or canvas
  (`decodePng`); React state set from timers changes only on a new value.
- Emissive glow on kit materials is divided by `toneMappingExposure`.
- Tiled lighting and GPU-driven culling are not built: they need compute,
  and WebGPU is retired ([0122](0122-webgpu-retired-webgl-studio-is-canonical.md)).

## 9. How performance is measured

No full-studio headless probes on the VM (SwiftShader milliseconds are not
frame times); node harnesses over the real code give counts and ratios. GPU
measurements run on the RunPod lane ([0119](0119-runpod-is-the-gpu-lane.md))
with `tooling/gpu-lane/measure.mjs`: the game clock at game speed, HUD-free
frames at the settled camera, and `shader-compile-check.mjs` after any
shader or material commit. The owner's device gives the fps verdict.
Evidence, walk rows and pod tables: [rendering-decision-rounds/0108](../research/archive/rendering-decision-rounds/0108-as-recorded.md).
