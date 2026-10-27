# 0016: Weapon classes follow Morrowind, including crossbows and thrown weapons (provisional)

**Status:** provisional 2026-10-27; owner call **O-15** confirms or reverts before P4-WP4.11.

## Context

The old project cut whips, crossbows and throwing weapons ("Marksman = bows"; old decision 0031 items, old
`76-stats-progression.md` lines ~96 and ~327). On 2026-10-27 the owner listed "weapon and item classes matching
Morrowind" as a must-have of Morrowind's soul. Morrowind's Marksman covers bows, crossbows and thrown weapons
(darts, throwing stars, throwing knives). The newer, more specific owner statement points the other way from the
old cut, but it is an owner ruling either way.

## Decision (provisional)

1. Marksman covers **bows, crossbows and thrown weapons**, as in Morrowind. Crossbows are vanilla (Dawnguard);
   thrown weapons come from Throwable Weapons SKSE (GPL-3) plus its NPC add-on, as dependencies.
2. Whips stay cut (not a Morrowind class).
3. Old decision 0031's crossbow/thrown cut moves from Carry to **Adapt** in inherited-rulings.
4. If the owner reverts (O-15), Marksman = bows only, and crossbows/thrown are hidden by the immersion inventory.
