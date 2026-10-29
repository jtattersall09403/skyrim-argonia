<!-- imported unchanged from elder-souls-argonia docs/decisions/0090-arrow-damage-is-calibrated-to-a-masters-warbow-headshot.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0090 — Arrow damage is calibrated to the band ladder; bows take no Strength

**Date:** 2026-09-24. **Status:** accepted (planner ruling for the owner's
round-2 feedback, combat-sandbox lane; supersedes the lane's first cut, which
put Strength on bows). Amended 2026-10-21 (2.9b-c6b, planner ruling on the
owner's "decide for me"): the calibration moved from the master's warbow
headshot on a 150-health opponent to the band ladder (decisions 2 to 4).

## Context

The owner asked that a master archer kill the default opponent with one
daedric warbow headshot. The lane first did it with Strength's `(Str+50)/100`
on bow damage. Module 76 §117 divergence 1 keeps Strength off Marksman, and
the stats model encodes that (`strengthApplies("marksman") === false`), so the
ruling moved the one-hit kill into the arrow's own damage calibration.

## Decisions

1. **Bows take no Strength term.** The sandbox reads `marksmanModifiers` and
   `meleeModifiers` from `game-core/src/stats` (the lane's linear
   `combat/skillScalars.ts` is deleted). Melee blows carry the model's
   `strength` into `resolveHit` beside `damagePosition` (×1.0 at the reference
   Strength 50); the weapon class picks the melee skill
   (`equipment/weaponSkill.ts`, Morrowind's mapping: staves Blunt, halberds
   Spear, claws Short Blade).
2. **One knob: `DAMAGE_PER_JOULE` 0.3** (`combat/ballistics.ts`; it was
   0.57, and 0.5 before that). The head-zone multiplier stays ×2 for every
   weapon; the constant is the physics-to-health conversion, so all arrows (the
   enemy archers' too) move together before armour. It is calibrated to the
   band ladder (world/76 §128.1, the owner's 2.9b ruling): an early iron
   longbow body shot must not one-shot a D1 enemy; a sneak headshot may.
3. **The check** (`combat/arrowCalibration.test.ts`): a level-1 archer
   (Marksman a major skill, 30 to 35), full draw, iron longbow, the iron war
   arrow (the default and starting arrow), against D1's health (18–28) and
   armour (0–18): two to three body shots, every case; the sneak headshot at
   the lowest Sneak band's bow multiplier kills. Measured body shot 14.4–16.7.
   The broadhead (iron hunting arrow, wound severity 1.45) can one-shot an
   unarmoured D1 at the bottom of the band: that is the broadhead's purpose.
4. **The sim follows.** The stats sim's bow stand-ins move by the same ratio
   (0.3 / 0.57: shortbow 18, longbow 27, warbow 38), and a tier-1 bow build
   carries the longbow (`builds.json` `gearTierMaterials.1.bow`). A legend
   marksman still finishes the endgame boss (57 s, inside the ×2.8 spread of
   `every-build-can-finish`); below a warbow stand-in of about 40 at the old
   ratio it could not, which is why the constant is 0.3 and not lower.

## Consequences

- Bows hit harder than a blade per shot only with a sneak opener or a head;
  a plain early shot is a two- or three-shot kill on D1, and the fixed-danger
  scale holds above it.
- 10c's per-weapon bands and real attributes will move these numbers; the
  test is the record to re-run.
