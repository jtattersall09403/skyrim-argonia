<!-- imported unchanged from elder-souls-argonia docs/decisions/0037-workstream-s-round4-qa-rulings.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0037 — Stat design QA rulings: practice, armour accrual, damping, lockpicks, poise, pace, criticals, poisons

**Status** accepted · **Spec** [module 76](../world/76-stats-progression.md)
§116–129 · **Revises** [0031](0031-workstream-s-round1-shape.md) and
[0033](0033-workstream-s-design-and-numbers.md) where stated

The owner's QA review of the stat design ruled on the weaknesses it surfaced.
The balance harness holds all its invariants after them, including the
Morrowind known-answer test.

1. **No practice discount** (§120.4). Discounting attribute prices by recently
   ranked skills recreates Morrowind's pre-level grind spreadsheet. Vastei is
   spent freely at list price.
2. **Armour skills accrue from kills and hits, class-weighted** (§120.2). A
   kill award keyed to the corpse (never to an encounter ending, so
   aggro-and-flee farms nothing; worth scales with the victim's health
   against yours) plus a hit bonus, weighted light {win 1.0, hit 0.25},
   medium {0.6, 0.6}, heavy {0.35, 1.0}; unarmoured follows light; blocked
   hits feed Block only. Constants in `rules-argonia.json` `armourAccrual`;
   `rules-morrowind.json` keeps pure hit accrual for the known-answer test.
3. **No repeat-target damping.** No reference game diminishes repeat use, and
   grinding respawned enemies after a rest is chosen play. Chip-damage
   worthiness stays.
4. **Lockpicks wear** (§118): condition lost per lock scales with
   `lockLevel / score`, so hard locks eat picks; no dice.
5. **Poise** (§121.3) on the DS1 model: passive pool, instant refill about
   5 s after the last hit, attacker poise damage = weapon-class base ×
   attack-type factor, a break plays the heavy reaction. Base poise is
   Agility / 2, replacing a separate damage-threshold stagger rule; armour
   carries skill-banded poise (heavy over medium over light); poise and block
   stability are effect-stack fields. Player and enemies share it; bosses may
   be `staggerable: false`. Implemented in
   [0040](0040-animation-packs-and-combat-parallel-pass.md); research:
   [dark-souls-poise-mechanics](../research/combat-and-systems/dark-souls-poise-mechanics.md).
6. **Pace** (§120.5): the 150-hour level target is 50–70, with no hard level
   ceiling, by design; the early checkpoints (hours 2, 20, 40) keep
   Morrowind's own pace.
7. **Ripostes and backstabs** (§121.5): the critical multiplier is
   per-weapon-class data, dagger-topped (DS1's shape); skill enters only
   through the normal damage pipeline; the sneak-opener table never stacks
   with it (an undetected target uses the sneak table, an aware one the class
   multiplier). A poise break does not open a riposte; a parry or guard break
   does.
8. **Weapon poisons and oils** (§124): a harmful or elemental brew applied to
   an equipped weapon or arrow is delivered by the next successful hit
   through the effect stack, potency from the alchemy formula; one hit, as
   Skyrim does it.

Birthsign contents land when a system needs them; the slot ships with the
stat system. The harness's open watch-items are in its
[findings](../research/archive/workstream-s/stats-sim-findings.md).
