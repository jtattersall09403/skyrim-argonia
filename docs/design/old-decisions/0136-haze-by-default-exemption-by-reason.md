<!-- imported unchanged from elder-souls-argonia docs/decisions/0136-haze-by-default-exemption-by-reason.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0136: Haze by default, exemption by reason

**Status:** accepted.

## Rule

Everything drawn is in the air. WorldSky's draw patcher gives every
material its aerial haze at first draw (`patchSceneMaterial`,
`packages/world-render/src/sky/litMaterialPatch.ts`): lit materials in
the lit chain after CSM, every other material (basic, line, points,
shader: glows, smoke, flames, beams, water FX, rope lines) through the
same `applyAerialPerspective`, in the mode its blending implies
(`aerialModeOf`: surface, additive, premultiplied). A material draws clear
of the haze only with `userData.esAerialExempt = "<reason>"` (the sky
dome and its stars and moons, a medium that is its own haze such as cap
clouds, rain, ambient air and marsh mist, the underwater column, UI,
debug), or `userData.esAerial === false` (the vegetation "noaerial"
switch).

## Why

Haze is the default, so no loader can draw clear by omission. An opt-in
tag leaves every untagged loader crisp against faded terrain (buoyant
hulls and the barrels on them, ropes, characters, glows, smoke and
flames); a default fixes the class.

## Consequences

- `applyAerialPerspective` is idempotent: a second call is a no-op while
  its hook is live, re-wraps after CSM replaced `onBeforeCompile`, appends
  its cache-key suffix once, and the shader carries the term once.
- `hazeCoverage.test.ts` builds the once-clear paths, runs the draw
  patcher and fails on any visible material without the term or a named
  exemption. `npm run look -- far-haze` shows subjects fading against the
  ridge behind them.
- An emissive draw only dims by the transmittance (its background already
  carries the inscatter); a premultiplied flame dims its coverage too, so
  a far flame fades into the hazed scene, never to a dark hole.
- An interior cell is outside the exterior air: `uAerialMask` on the
  shared aerial block (`packages/world-render/src/sky/aerial.ts`) scales
  every optical depth of the surface term and the dome march, and
  `writeAerialCellMask` (WorldSky, from its `hidden` flag, every frame) is
  its only writer, so no hazed material leaks exterior air into a cell.
  Every host that loads interiors passes `hidden` to WorldSky;
  `interiorAerialMask.test.ts` fails on the leak, and
  `tooling/visual-look/interior-haze.mjs` checks a deployed studio (live
  equals noair).
