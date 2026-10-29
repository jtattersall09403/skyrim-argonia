<!-- imported unchanged from elder-souls-argonia docs/decisions/0093-swimming-is-a-movement-mode-behind-the-controller-boundary.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0093 — Swimming is a movement mode behind the controller boundary, fed by the water query the world already has

**Status:** accepted (owner: "swim in 3D, as Skyrim does"; the shield rides
on the back while swimming; swimming otherwise stays as the studio has it).
Proved in the combat sandbox so the studio and the game adopt it rather than
rebuild it.

## Decisions

1. **The water comes in through the existing contract.** The runtime takes a
   `WaterSampler = Pick<WorldWaterQuery, "sample">` (`@elder-souls/contracts`)
   on its host. The sandbox passes a flat pool (`flatPoolSampler`); the studio
   passes its `WaterWorld` unchanged. No second water model.
2. **Swim is a mode of `PlayerMovementController`** (`setMovementMode`).
   Ecctrl has no buoyancy and rewrites gravity every frame, so in swim mode
   the adapter switches ecctrl off and drives the body itself: no gravity,
   velocity from the stick, a damped spring holding the chest at the surface.
   Grounded mode restores ecctrl untouched.
3. **Entering and leaving** use the sample's immersion with hysteresis, the
   water sampled at the top of the 1.7 m body column (feet + 1.7 m), which is
   what `WaterWorld` means by the query point: swim at 0.62 (water 1.05 m
   deep, chest under), back to grounded under 0.45 (0.77 m) with the feet on
   ground. The adapter keeps driving the body until ecctrl's first enabled
   frame, so the hand-over never leaves it undriven.
4. **Speed is the stats model's** `swimSpeed(athletics)` (1.60 m/s at the
   reference Athletics 50). Sprint-swim is 1.4 × swim speed with the ground
   sprint's stamina drain, and stops at empty stamina until the input is
   released.
5. **Vanilla's rules for the body.** Five in-place vanilla clips (idle,
   forward, back, left, right), forward at the vanilla slow rate and doubled at
   full stick; the weapon is put away on entry, as Skyrim's swim state forces;
   no attacks, guard, dodge or jump in the water; draughts may be drunk; a
   carried torch goes out ([0091](0091-the-off-hand-holds-a-shield-a-weapon-or-a-light.md)'s
   `submerged` hook) without being used up. The body is drawn pitched when
   diving, since vanilla has no dive clip.
6. **The shield rides on the back while swimming.** A held shield moves to
   the `WeaponBack` socket by its `swum` transform, selected by the swim
   state, and returns to the arm on leaving the water; `visual:check swim`
   asserts the parent is `WeaponBack` while swimming.
7. **Underwater and breath.** Dive (crouch held) and rise (jump held), or the
   stick forward with the camera looking steeply up or down, move the swimmer
   vertically (`swimVerticalIntent`, `swimVertical3D`); with no vertical input
   under water the body holds its depth, and near the float line the spring
   takes it back to the surface. The swimmer's yaw rate is set each frame,
   never built from torque impulses: `EcctrlAdapter` caps it at 4 rad/s (gain
   6 per radian of error) and sets it to zero with no facing
   (`EcctrlAdapter.swim.test.ts`). Breath is the stats model's
   `breathSeconds`, infinite for a race whose record carries
   `waterBreathing` (`raceBreathesWater`,
   [0096](0096-one-race-record-keyed-by-the-roster-with-morrowinds-packages.md));
   it drains with the eyes under water and returns four times as fast.
   Drowning damage waits for a health pool outside combat.
8. **One runtime, every host.** The swim law is `swimStroke`
   (`game-core/locomotion/swim.ts`), run under `PlayerMovementController`
   by the world studio and the game alike. The combat sandbox's pool
   drives the same vertical control; the scenario `swim-dive-turn` (group
   `swim`) dives, holds depth, rises, turns a full circle and asserts the yaw
   rate is back under 0.2 rad/s 0.5 s after the stick is released. On touch
   the controls show a dive button and turn jump into rise while swimming.

## Why

Ecctrl cannot float a body, and a second water model would drift from the
one the world renders. A mode behind the controller boundary keeps combat,
input and animation on `PlayerMovementController` and the water on the
world's own query.
