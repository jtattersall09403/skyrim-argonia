<!-- imported unchanged from elder-souls-argonia docs/decisions/0033-workstream-s-design-and-numbers.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0033 — The stat design, its numbers, and the balance harness

**Status** accepted · **Scope** [module 76](../world/76-stats-progression.md)
§116–129, `tooling/stats-sim/`, `packages/game-core/src/stats/data/`

Decision [0031](0031-workstream-s-round1-shape.md) settled the shape; this
record holds the calls behind the detailed design. Module 76 §116–129 is the
design: seven attributes, 27 skills, one skill curve with an attribute assist,
*vastei* levelling, combat and defence maths, movement, burden and breath,
magic, crafting and the economy, speech, rest, death and respawn, races, one
effects stack, the D0–D5 ladder and semantic NPC authoring. The worked
derivation and the owner rounds are archived for provenance:
[numbers packet](../research/archive/workstream-s/stats-progression-numbers-packet.md),
[owner round 2](../research/archive/workstream-s/stats-progression-owner-round2.md),
[simulation findings](../research/archive/workstream-s/stats-sim-findings.md).

## The balance harness

`tooling/stats-sim/` is a standalone, data-only harness (no workspace entry,
no game package imported: the one code exception
[0019](0019-stats-system-workstream-and-placement.md) allows). It sweeps
builds × stages × gear × archetypes × danger bands plus progression,
encumbrance, breath, climbing, economy, exploit hunts and a whole-playthrough
campaign (`src/campaign.mjs`: six builds over about 150 hours), and asserts 16
invariants. The game's tables in `packages/game-core/src/stats/data/` are the
canonical numbers. **The simulation is evidence, not law**: where it and a
playtest disagree, the playtest wins.

## The non-obvious calls

1. **One curve, one assist.** Every skill effect is `k(s) = 1 − (1 − s/100)^1.6`
   over an effective skill of `skill + clamp((governingAttribute − 50)/5, ±10)`.
   Attributes matter everywhere without buying anything twice, and the curve
   is the soft cap. The assist is ours, not Morrowind's (§117.1); the canon
   trainer cap is kept.
2. **Armour** is `AR / (AR + 135.6 + 0.6 × incomingDamage)`: 25 % at the
   reference loadout, and big hits punch through, as a fixed-danger world
   needs. Armour has its own material ladder (Morrowind's 8× spread) with
   light, medium and heavy scaling: light dies in 2–3 blows, heavy in 4–5,
   best plate in 5–6.
3. **Getting hit matters.** Blows-to-kill is the danger ladder's design input
   (10 / 5 / 4 / 3.5 / 3 / 3 by band, on the character each band is for) and
   enemy damage is solved from it. One difficulty multiplier scales incoming
   damage only, so [0004](0004-fixed-difficulty-constraint.md) holds.
4. **Health is a formula over Endurance and level**, retroactive by
   construction.
5. **Vastei** is the levelling currency: canon Argonian for *change*, earned
   by acting, dropped where you die, taught diegetically by a Nisswo in the
   opening hours. Hoarding it is strictly worse than spending it. Grounding:
   [magic-practice](../../../world/sources/lore/topics/magic-practice.md), which
   also records why Mysticism survives here as a folk school.
6. **Requirements never block**: an over-heavy find is usable at level one at
   a stamina penalty.
7. **A variant may not invent a tier**: compiled enemy fields clamp to ±25 %
   of their band edge.
8. **Spell-cost reduction caps at 75 %** across all sources.
9. **Crafting reads base stats and nothing fortifies a crafting skill**,
   which closes every documented Elder Scrolls crafting loop.
10. **Stats stay off the feel constants**: weapon skill does not touch
    recovery timing. Poise is the combat system's
    ([0040](0040-animation-packs-and-combat-parallel-pass.md)), and stats
    reach it only through `PoiseModifiers`.
11. **Roll tiers vary i-frames** (Dark Souls 1's 13 / 11 / 9): equip load is a
    visible choice.
12. **Sneak attacks** multiply by Sneak-skill band, Skyrim-shaped (dagger ×3
    to ×15, bow ×2 to ×4), melee above ranged.
13. **Acrobatics governs climbing**: about 12 m of wall in hour one, 160 m at
    mastery; burden multiplies the drain.
14. **Training is priced as Morrowind prices it**: 10 × the current skill
    level in gold per rank (`iTrainingMod`), then through the barter formula,
    so disposition and Mercantile move it (`economy.json`
    `training.costPerRank` 10, exponent 1.0). A skill is never trained above
    its governing attribute's base value. Settled.
15. Birthsign is chosen directly; constant-effect enchantments are tiered by
    soul size; barter is a visible price band (about 3× end to end, no
    minigame); no followers; 18 preset classes (11 canonical, 7 from canon
    province offices).

## What the simulation forced

Burden thresholds 0.20 / 0.35, so the reference kit is mid; enemy armour
bands down and D5 trimmed; magicka pool and regen up with capped cost
reduction; spell tier damage down; arrow material as its own damage axis with
armour penetration. Confirmed by simulation: a D5 beats a beginner; every
build style can finish the final boss; no achievable armour approaches
immunity.

Reported, not fixed, as forward work for the economy and progression
systems: nobody dies after Act III, gold outgrows its sinks, and non-social
builds finish with Speechcraft under 20.

## Owned elsewhere

Loot and trap semantic schemas are module 76 §128.2; the weapon keep-list
sourcing evidence is module 90 §74.3.
