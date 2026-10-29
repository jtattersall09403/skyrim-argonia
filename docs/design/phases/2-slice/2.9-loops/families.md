<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.9-loops/families.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Visual families (2.9c1)

The loop for [2.9 § Loops](../2.9-magic.md#loops) "each visual family":
the seven families of 0146 item 3 drawn by one config-driven system,
`packages/magic/src/fx/` (`families.json`, `FamilySystem.ts`, one file per
family in `families/`, the mined atlas in `sprites/`). Written before the
first measure; the re-measure runs the same rows.

## The phone budget (standard 16, 0084)

Per family, one cast live, at its busiest frame (the projectile counts its
hit flash's first frame beside its own last frame). The numbers are
`families.json` `budget`; the measure fails a row over them.

| Band | Draw calls | Triangles | Texture bytes (download) | Point lights |
|---|---|---|---|---|
| phone | 1 | 64 | 65 536 | 1 (light orb only) |
| desktop | 1 | 128 | 65 536 | 1 |

Every family shares one instanced draw and one atlas, so draw calls do not
grow with the number of casts. The atlas is 512 x 256 grey, about 0.7 MB in
VRAM as RGBA with mips (named here, not gated).

## Rows

| # | Row | Harness | Bar | Elapsed |
|---|---|---|---|---|
| 1 | config | `npx vitest run src/fx` in packages/magic | every family has a row, a renderer and a sprite in the atlas; every param a renderer reads exists; colour parsed from the effect row | |
| 2 | budget | `node apps/combat-sandbox/scripts/magic-families.mjs` (headless Chromium, SwiftShader; renderer.info) | every family x band within the table above; zero GL errors | |
| 3 | sprites | `sprites.json` hashes re-read by the vitest row; README § Credits and the register row | every sprite's source path and sha256 recorded; atlas sha256 matches the file | |
| 4 | stills | the same script writes `lanes/2.9/c1-shots/families.png` (every family at its moment of effect, day and night, both bands) | a `reader` child passes every family's checklist below | |
| 5 | recipe | `fx/recipe.test.ts` plays Burden (an effect outside the slice set) from its effects.json row; the still sheet carries a Burden column | one data row, zero code: no family file or system change names Burden | |

## Checklists for the reader (one per family, judged on the still)

- **projectile** (Fireball, orange): a bright round core with a hot white
  centre and a fading wisp trail behind it along the line of flight; reads
  as a thrown ball of fire, not a smear or a square.
- **hitFlash** (Fireball's landing): a burst larger than the projectile
  with sparks thrown outward; centred where the projectile ended.
- **selfGlow** (Hearth Heal, Cure Common Disease, Levitate): a soft halo
  on the body and wisps spiralling up around it, inside about half a metre
  of the body; the figure stays readable through it.
- **areaRing** (Shield's ward, Soul Trap): a ring lying flat on the ground
  around the target, open to its radius, with motes rising from the rim; it
  must not stand upright or float clear of the ground.
- **stream** (Frostbite): a continuous flowing ribbon from the hand toward
  the target with a glow at its tip; no gaps between segments, no square
  ends.
- **lightOrb** (Light): an orb at shoulder height off the caster, a bright
  core, and the ground under it lit in the orb's colour.
- **summonFlash** (Bound Dagger): a flash and swirl at the hand with a
  column of sparks rising; brief and bright.
- **every family**: tinted by its effect's colour (fire orange, frost pale
  blue, restoration gold-green, and so on); visible by day against the sky
  and the ground, not clipped to white at night; no black box or hard
  sprite edge; dual (both hands) visibly larger, same shape.
- **Burden** (the recipe row): drawn by its row's family and colour with
  no other change.

## Results

2026-10-20, all green.

| # | Result | Elapsed |
|---|---|---|
| 1 | 27 vitest tests pass (config, renderers, colour, seam, budget per family x band, sprites, recipe) | 0.5 s |
| 2 | every family x band: 1 draw call; peak triangles desktop 36, dual 36, phone 20 (bars 128, 64); lights 1 desktop, 0 phone (1 for the light orb); atlas 34 583 bytes (bar 65 536); GL error 0 | 2.6 s |
| 3 | six sprites, each with vault path and source sha256; atlas sha256 matches | in row 1 |
| 4 | reader: first pass FAIL on projectile (small, broken trail) and area ring (filled centre); fixed (bigger core, dense glow trail; annulus on the ring sprite); second pass PASS on all | 2 reads |
| 5 | Burden plays from its effects.json row (projectile, #6fa8dc); no fx file names it | in row 1 |

Queued as polish: the phone band's projectile trail reads as beads (half the
trail sprites); the light orb's ground light is faint at night.
