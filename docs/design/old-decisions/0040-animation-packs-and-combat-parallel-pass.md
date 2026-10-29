<!-- imported unchanged from elder-souls-argonia docs/decisions/0040-animation-packs-and-combat-parallel-pass.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0040 — Animation packs, and the combat rules they carry

**Status** accepted · **Feeds** combat, animation, archery, character build

How animation ships, how a hit is timed and placed, how feet drive motion,
how the bow works and how faces assemble. The measurements and playtest lists
are in the [round log](../research/archive/combat-0040-rounds/0040-rounds.md).

## Animation packs

The rig ships as several GLBs from one deterministic build: `core` (what a
body does without knowing what it holds), `criticals` (paired ripostes and
backstabs) and one per weapon family. Each pack repeats the skeleton and
carries only its clips; packs declare `requires`, `resolveAnimationPacks`
takes the closure and an actor loads `loadoutAnimationPacks(loadout)`. A new
family is clips with a `pack`, a pack entry, a `MovesetDefinition` and the
class table; nothing in loading, binding or the combat FSM changes.

- A mixer asked for a missing action silently keeps the previous one, so
  `equipment/animationPacks.test.ts` proves every weapon and shield can play
  every clip its profile names.
- The build is byte-for-byte deterministic; an unchanged config reproduces the
  previous packs exactly, which is how a pack change is proved non-regressive.
- Movesets stay at vanilla granularity (`1hm`, `2hm`, `2hw`, `h2h`, `dw`);
  parries and executions are as granular as Rim Parry allows.
- Stationary loops are recentred (`recentreRootMotion`): sway kept, the
  constant planar offset removed, so entering a swing does not slide the mesh.
- Backward runs are the sourced forward run reversed (`reverseSource`) before
  foot measurement; no suitable sourced standing backward run was found.

## Poise

Module 76 §121.3 on DS1's model: hidden pool, class poise damage, timed
refill, one system for all, filled through `PoiseModifiers`. A starting steel
kit sits near 47 (sword three hits, greatsword two, warhammer one);
`poise-break` proves it.

## Timing and contact

- **Anything measured as a fraction of a clip is valid only while clip and
  action share a clock.** `AttackSpec.timeScale` plays the clip at the class
  speed factor; `equipment/attackTiming.test.ts` holds it for every class, and
  every critical's `damageProgress` falls inside its own active window.
- `scripts/measure-contact-windows.mjs` is trusted exactly as far as it
  reproduces the hand-audited one-handed answers
  (`critical-known-answer.test.mjs`). It selects the phase of peak tip speed,
  measures parries across the intro and parry clip pair, and uses the runtime
  volumes: the weapon capsule from measured extents against the victim's
  skeleton-fitted hurtbox. The tool proposes; the visual scenario disposes.
- Executions are trimmed to put contact 0.400 s in, so the victim timeline
  carries across families untouched.
- Parry windows are per family (`ParryProfile.active`): shield 0.26 s,
  one-handed 0.20 s, two-handers 0.16 s, opening where the family's clip
  sweeps the guard. A parry catches by timing: while the catch is active a
  blade reaching the defender's body is parried, both directions.
- A swing has one outcome: a parry counts only if the swing has not already
  hit.
- A held item's hit volume is re-measured when the item id changes.
- Ordinary attack range is measured: `npm run weapons:reach` bakes every melee
  attack at 240 Hz against the production rig into
  `equipment/generated/weapon-reach.json` (hash-stamped, rebuilt in check mode
  by `npm test`; a missing measurement is an error). Inventory shows weapon
  length and maximum reach; AI threat reads the equipped attack's range. Class
  offsets apply only to paired-critical entry limits.

## Criticals

- The choreography belongs to the attacker's weapon: the attacker's pair and
  attack are pinned on the victim for the duration.
- `WeaponClassProfile.criticalStyle`: a thrust class uses its authored
  execution; a swing class plays its own opening light attack from behind.
  Vanilla's back-facing paired clips are all one-handed, so two-handed
  backstabs are assembled from the weapon's execution and a sourced victim
  stagger.
- The dagger class ripostes with `RIPOSTE_STAB` (Rim's dagger execution); the
  one-handed sword keeps the authored lunge.

## Feet drive motion

While a foot is planted it does not slide, so its motion relative to the root
is body motion. The pipeline integrates each clip's `groundTrack` at build
time; the anchor moves at the other foot's touchdown (heel or toe within 2 cm
of its floor). Attacks apply the whole track, forward and lateral, for player
and enemy: the body pivots round its planted foot and an attack does not
track its target. An enemy chooses feet or lunge once, when the swing starts.
Locked-on back and lateral strides and the crouch play clip, clock and track
together (`footAnchoredLoopVelocity`, never against the loop's net direction)
at `LOCKED_STRIDE_RATE` 1.55, scaled by stick magnitude; forward under lock-on
is the ordinary run. Grounded crossfades correct each penetrating leg
(`anim/footContact`) before pelvis support, keeping the sourced knee plane.

## Ownership rules

- A value two systems write has one owner: a mesh is visible iff nobody hides
  it (`actors/meshVisibility`); coverage hides a body mesh by its primary
  (lowest) biped slot.
- The off-hand and main-hand nodes each take a half turn
  (`OFF_HAND_NODE_HALF_TURN`, `MAIN_HAND_NODE_HALF_TURN`), facts about the
  nodes, not the items.
- An orientation is anatomical, never a world axis: the shaft in hand lies in
  the quiver's plane in the body's frame.
- State the AI can choose must exist in the FSM; `shoot` and `withdraw` have
  handlers, and guarding is read from whatever is between the fighter and the
  blow; death interrupts the bow cycle.
- A modal suppresses any action held while it is up until the device releases
  it (`InputController.suppressHeld`); `[data-ui-capture]` chrome owns its
  clicks.
- Full-screen UI is sized by `hud/visualViewport`, never by a CSS unit.

## Enemy tactics

A combat style carries disposition; `ai/weaponTactics` reads ranges,
aggression and circling off the equipped weapon (fallback: the sword's). A
bow has its own intent set: keep range, no guard or parry, the shared solver.

## The bow

- Bows are rigged (`pipeline.build_bow_rigs`) on the vanilla seven-bone bow
  skeleton with their own draw clips; one driver (`riggedBow.ts`) serves main
  hand, off hand and first-person arms. The nock is on the animated string; a
  two-joint constraint brings the drawing hand to it only during the pull.
- A shot starts with an empty string; a press fetches from the quiver
  (`QuiverAttachment`, vanilla quivers) and nocks. Drawn strides are vanilla
  `bowdrawn_walk*`; a raised bow walks.
- The arrow is a centred, sensor-only body under gravity and calibrated drag
  (`½ ρ Cd A v²`), attitude set from velocity each step, swept tip-first
  between steps: world geometry stops it, actor capsules only shortlist posed
  skin for triangle contact, no near-miss attachment. Gameplay gravity is 2×
  (19.62 m/s²); the 1× reference and drag calibration stay in the tests.
  Arrows strike only hurtboxes, the shooter excluded, and the player takes
  them through the melee rules.
- Aim: `camera/bowCamera` owns the shoulder default; the crosshair ray uses
  the rendered camera and `solveBowAim` compensates drag and gravity from the
  nock, for player and archer. Full-draw sight calibration holds through the
  pull; body yaw follows camera or target from the actor centre. Views are
  `shoulder`, `firstPerson` (Skyrim's first-person bow rig per body, skin
  tinted) and `eye`.
- An archer carries a nocked shaft, leans to the solved elevation and looses
  from the nock once facing within 3.4°.

## Faces

FaceGen assembly fits the whole head topology to the body's open neck loop,
snaps and copies skin weights; a race build rejects an open seam or missing
FaceTint. Defaults are whole vanilla `Skyrim.esm` NPC appearances, never
recoloured; hair cards are 0.5-threshold alpha cutouts.

Open, in the [polish backlog](../phases/P-polish/backlog.md): the bow's melee
fallback, a non-pivoting heavy clip, AI planning for track displacement.
