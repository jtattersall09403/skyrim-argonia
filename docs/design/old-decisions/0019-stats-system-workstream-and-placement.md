<!-- imported unchanged from elder-souls-argonia docs/decisions/0019-stats-system-workstream-and-placement.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0019 — The stats system: designed in parallel, authored semantically, implemented in the game

**Status** accepted · **Design** [module 76](../world/76-stats-progression.md)
§116–129 · **Numbers** [0033](0033-workstream-s-design-and-numbers.md)

## Decision

The stat system was designed as a docs-and-decisions workstream beside the
world build, then implemented in `packages/game-core`, where it generates the
capability profiles and restates enemy archetypes on its scale.

- **The world build is not blocked on stats.** Capability profiles (module 75
  §52) are the world-to-character contract: the world compiler validates
  traversal against named profiles generated from gameplay data and never
  hard-codes speeds. When the stats generate the profiles, no world data
  changes.
- **Content is authored semantically and compiled to absolutes.** Enemy,
  trap and loot stats are references to the power ladder (band, relative
  position, variant modifiers), so a curve retune rebalances all content
  without re-authoring; literal overrides remain for uniques. Fixed danger
  ([0004](0004-fixed-difficulty-constraint.md)) holds: derivation reads world
  data only, never player state.

## The shape: a Morrowind chassis with a Souls combat layer

The design works out what that means: the seams between chassis and layer,
the mapping of Skyrim-taxonomy items and rig onto Morrowind categories,
keeping a Morrowind-only category only where sourceable assets and movesets
exist, which Skyrim innovations merit keeping (smithing), one stat schema for
every NPC and enemy, and marsh hooks (Athletics governs swim speed and breath
for non-Argonians; Argonians breathe underwater). Morrowind's documented
formulas on UESP are the reference, and a data-only balance harness
(`tooling/stats-sim/`, the one standalone-code exception) proves the numbers.

## Constraints the design satisfies

- **No hidden to-hit roll.** A swing that visibly connects registers; skill
  modifies damage, stagger, stamina cost, recovery and reach, never whether a
  connecting attack lands.
- **An uncapped power ceiling is wanted.** Morrowind's "overpowered because
  you put the work in" is the payoff of fixed danger. Power is earned through
  system mastery, not handed out by the levelling curve; the critical path
  assumes a competent, ordinarily equipped character; the early curve is
  gradual as intent, not an enforced invariant, so an accidental early gem is
  an easter egg, not a defect. The world degrades into skipped challenge,
  never an unfinishable state.
- **A documented absolute power ladder**, so the D0–D5 danger bands and the
  access progression ([0007](0007-access-progression.md))
  mean something numerically.
- **Sandbox values are calibration data, not the baseline.** What is anchored
  is the feel at a reference loadout: one named default character reproduces
  the sandbox timing and weight, asserted by test. Around it, stat- and
  load-linked timing variation is design space (Souls equip-load roll tiers).
- **Argonian physiology** (breath, swimming, disease) is expressible as race
  modifiers.
- **Birthsigns are calendar-shaped**: thirteen constellations, one per month,
  from the world clock (module 55 §95).

## What is protected

The sandbox's systems are not finished or unchangeable; later work may
refactor and extend them. What is protected is the calibrated feel, the
controller boundary and the package rule (module 75 §51.1).
