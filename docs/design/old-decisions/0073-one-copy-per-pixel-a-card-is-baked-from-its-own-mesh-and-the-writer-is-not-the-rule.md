<!-- imported unchanged from elder-souls-argonia docs/decisions/0073-one-copy-per-pixel-a-card-is-baked-from-its-own-mesh-and-the-writer-is-not-the-rule.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0073 — One copy per pixel; a card is baked from its own mesh; the writer is not the rule

**Status:** accepted. **Extends:** [0071](0071-every-placed-thing-steps-down-through-bands-and-collides-as-itself.md).
The level ladder these rules serve is
[0075](0075-lod-is-a-ladder-stepped-from-the-camera.md).

## Decisions

1. **A hand-over between two copies is a partition, not a blend.** Wherever
   two copies of one instance are drawn at once (a rung edge in its 0.4 s
   fade, a ground-cover tier edge), the two test complementary halves of
   the same dither: the incoming copy keeps `{bayer < s}`, the outgoing
   `{bayer >= s}`, from the bit-identical factor `s`, in the colour, depth
   and shadow passes alike. If two copies do not provably sum to one copy
   per pixel, the gap is a hole. The gates (`lodFadeTemporal.test.ts`,
   `ladderCoverage.test.ts`) walk every ladder against all 16 Bayer
   thresholds.
2. **A tree changes quality; it never fades to nothing inside the loaded
   ring.** A land tree is drawn wherever it is loaded and unoccluded, as its
   card or impostor at range (0075 decision 7); terrain occlusion still
   culls. The cost is paid in the card tier, never in mesh instances.
   `lodRings` is the one source of the ladder and holds it in order.
3. **A far card is baked from its own mesh; an authored card is never
   trusted because its filename matches.** Mod-authored `_lod_flat` quads
   pick a rect of a shared atlas by the vanilla tree slot, bound to the mesh
   by name with nothing proving the picture is that tree; measured, several
   wore another species' card or a plane three times the tree's height.
   Under `bakeCards` every asset outside the skip categories bakes from its
   own mesh and the authored NIF is never extracted; `bakeCard: false` is the
   only opt-out. The gate reads the shipped GLB and requires every billboard
   node to carry its asset's node hash.
4. **A rule that runs correctly in memory is worth nothing if the writer
   destroys it.** Prove the gate on the shipped artefact, not on the rule in
   memory. For rocks: the yaw wraps before the quantiser (it once clamped
   negative yaws to zero and turned thousands of open-backed shells
   outward); `align_to_slope = tiltDeg.p50 / slopeDeg.p50` per species from
   the mine (the mined tilt is the total off-vertical angle, never added on
   top of slope-following); the base plane is measured at the base, not the
   pivot; and a rock that cannot be seated is refused, never shipped
   floating. `rock_census.py` reads the published bundles.
5. **A landing follows the surface the controller stands on, not the
   terrain under the body.** `PlayerMovementController.supportHeight()`,
   implemented in `EcctrlAdapter` from the grounding shape-cast's own
   witness point, feeds the whole-clip `floor-contact` landing; the visual
   support falls back to terrain, then to the body's feet.
6. **The sea bed is dressed for a swimmer's sight line.** The density ramp
   runs 900 m from shore, the near bands are about three times denser than
   the first cut, and the low seagrass species are placed at sea.
7. **The site carries only what the shipped ladder can display, and the
   payload has a budget that is a gate.** `tooling/pages-site/compose.mjs`
   (`npm run site:compose`) derives its exclusions at build time: a record
   that only feeds a hidden layer is dark; a kit ships if the built code or a
   shown layer's record names it; chain-only rasters stay off the site. The
   build fails on an unknown ladder layer, a named kit missing from the
   build, a surviving reference to an excluded file or a site over its
   budget. Standard 16 in `docs/standards/engineering.md` states the budget
   and names the gates.
8. **Every kit ships GPU-compressed; the raw build is not what ships.** The
   raw Blender build stays under `output/kits/` as the measurement product;
   `public/kits/` holds that file run through gltfpack by
   `pipeline/kit_compress.py`. Textures are UASTC/KTX2 for every role (ETC1S
   loses the alpha-tested foliage edges the owner inspects; it stays
   available per kit with its price recorded). Geometry is meshopt with
   float positions and UVs, because quantised positions add a
   dequantisation node that moves the mesh off the node whose extras the
   runtime reads. Decoded through `game-core/assets/kitLoader.ts` with the
   transcoder at `<base>/basis/`, gated by `test_kit_compress.py`. The
   character files ship once: the studio's production build resolves them
   against the sandbox's copy. Measured in
   `docs/research/rendering/gpu-texture-and-mesh-compression.md`.
9. **The dev server validates rather than re-sends.** It answers
   `Cache-Control: no-cache` with a weak size+mtime ETag and a 304 on a
   match, so nothing stale is shown and a reload re-downloads only what
   changed ([0072](0072-the-ring-fades-in-the-shader-and-the-studio-serves-files-from-disk.md)).
10. **The shadow type is PCFShadowMap, said once.** `<Canvas shadows="soft">`
    made three rewrite the type each render, force full shadow passes and
    compile some materials with a plain sampler bound to comparison-mode
    depth textures (`GL_INVALID_OPERATION`). We declare PCF.
11. **A render target's depth image is resized with its colour image**
    (`resizeTarget`), and every pass that reads scene depth reads it at the
    target's resolution, not the canvas's.
12. **A startup fetch is gated on whether the view can use it.** The
    underwater kit loads when a bed species stands within 400 m of the focus;
    data for a hidden layer is not fetched.
13. **`ready` means the thing exists.** `EcctrlAdapter.ready` is true only
    once the rigid body exists, and every body accessor is null-safe.

## Why

Each of these defects passed a test that checked the rule rather than what
shipped: a fade whose two copies nested, a card bound by filename, a rock
rule the quantiser clamped, a ready flag ahead of its body. The common cure
is to gate the shipped artefact.

## Consequences

- Kit bytes, the site's size and the cold start are standard 16's budgets;
  a kit change runs `kit_compress --check`.
- Evidence and the measured numbers:
  [rendering-decision-rounds/0073](../research/archive/rendering-decision-rounds/0073-as-recorded.md)
  and the [16f ledger](../research/archive/phase16-evidence/16f-ledger.md).
