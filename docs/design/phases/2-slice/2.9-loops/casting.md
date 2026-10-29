<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.9-loops/casting.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Casting: the verb, the hands and the belt (2.9b1)

Written before the first measure. One row per measurement: the command,
the number, its bar, the capture beside it and the reader's checklist.
Elapsed is wall time for the row's command.

## Rows

| # | Measure | Command | Bar | Result | Elapsed |
|---|---|---|---|---|---|
| 1 | hands: a spell in either hand beside weapon, torch, shield; dual; belt spell slot; swaps carry spells; save round trip | `npx vitest run src/inventory/hands.test.ts src/inventory/serialiser.test.ts src/inventory/rules.test.ts` (game-core) | all pass | 9/9 hands tests; inventory dir 83/83 | ~5 s |
| 2 | bindings: each hand's cast control on keyboard and mouse, pad and touch, held as a hold | `npx vitest run src/io/input.cast.test.ts` (game-core) | all pass | 6/6 input.cast; io + intent 42/42 | ~1 s |
| 3 | the verb: charge for the tier's cast time, release fires, early release refunds, stream and ward drain per second, dual ratios from magic.json, the §123 gate refuses with a reason, magicka read from the pool, a poise-breaking hit interrupts and a soaked one does not | `npx vitest run src/combat/castCycle.test.ts` (game-core) | all pass | 15/15 castCycle | ~3 s |
| 4 | the upper-body layer: style to clip by castStyle, upper-body bone filter, phase to layer weight and time, missing clip logs once and the cycle still runs | `npx vitest run src/combat/castLayer.test.ts` (character) | all pass | 9/9 castLayer; character combat dir green | ~5 s |
| 5 | typecheck of the touched packages | `npm run typecheck -w @elder-souls/game-core -w @elder-souls/character` | 0 errors | 0 errors (game-core, character, combat-sandbox) | ~10-15 s each |
| 6 | strip of one cast (the sandbox `mage` preset, Fireball charged and released) | `npm run visual:check -w @elder-souls/combat-sandbox -- cast` | reader checklist below all yes | GREEN (2.9b4, round 3). The pose was never the fault. Rounds 1-2 shot from the default rear camera (`lanes/2.9/b4-shots/r1-*`, `r2-*`): legs still yes, off arm still yes/partly, no throw visible, because an aimed throw goes straight into the screen. Measured offline in the rig-root frame: the layer moves the hand 36 units forward between clip 0.167 and 0.2 s (the full clip moves it 40). A look-stick orbit cannot frame a profile, because a readied spell turns the body with the camera. Round 3 is a side close-up (`--closeup` with `VISUAL_STILLS`), strip `lanes/2.9/b4-shots/r3-cast-aimed-strip.png`. Reader: "three distinct poses YES ... c reads as the throw, the hand pushed furthest forward ... the sequence does read as casting an aimed spell ... nothing is broken". Polish: the torso does not lean into the throw, and the charge pose looks close to the release. Side close-up: `VISUAL_STILLS=... node scripts/capture-visual-scenarios.mjs --prebuilt --no-video --closeup cast-aimed`. All five styles re-shot the same way (strips `lanes/2.9/b4-shots/styles/`, reader `lanes/2.9/b4-reader.md`): aimed and stream green, self, ward and dual partly (see clips.md) | ~3 min per shot |
| 7 | still of the HUD hands and the cast meter from the sandbox (mage loadout, live state through `scene/ui` `castingViewOf` and `handSpellViews`, `MagicHud`) | `VISUAL_STILLS="d-early:0.45,e-mid:0.7,a-charge:1.0" node scripts/capture-visual-scenarios.mjs --prebuilt --no-video cast-aimed` | reader checklist all yes | GREEN (2.9e2): stills `lanes/2.9/e2-shots/`, reader `lanes/2.9/e2-reader.md`: the ring fills d to a with the flame inside, "Charging" and "Ready" legible, two hand tiles (flame, eye), no raw ids, no overlap. Polish: no empty track at low charge on the light floor; the ring is magicka-blue, not school-tinted; stills lag sim time on software GL | ~1 min per shot |

## Reader checklist: the cast strip (row 6)

1. The upper body raises the casting hand while the legs keep the stance (no slide, no pop at the blend).
2. The charge, the hold and the release read as three distinct poses.
3. The other hand is unchanged by the cast.

## Reader checklist: the HUD hands and belt (row 7)

1. Each hand shows what it holds: a spell name or icon in a spell hand.
2. A belt slot holding a spell reads as a spell, not an item.
3. Nothing overlaps or is cut off at desktop and phone.
