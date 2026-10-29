<!-- imported unchanged from elder-souls-argonia docs/decisions/0150-crafting-ships-whole-the-slice-climbs-its-first-rungs.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0150 Crafting ships whole; the slice climbs its first rungs

**Decision (owner, 2.9b plan review).**

1. **The whole engine, thin content.** Every recipe, material tier,
   ingredient effect and enchant tier ships in 2.9b (the wide loads);
   the slice exercises only the early rungs: common materials on sale
   from the one village smith, high-tier metals loot and purchase only, sold at the import points (daedric and
   falmer gear is forged from daedra hearts and chaurus chitin, found
   rather than sold; only 2 gear rows stay loot-only), one rare
   fortify-crafting ingredient with one placed source. Stations stand
   wherever the lore gives a place a works or an inn; the one
   enchanting table is the Wamasu Shrine's. Material tier is a crafting
   gate, not a danger band: a grade-3 cheap weapon may out-hit a plain better
   metal, because the better metal's tempered version still beats the cheaper
   one's, so forging and tempering the better one stays worth it (owner,
   2026-10-20).
2. **A soul caps the size of a permanent effect, not the points.** Each
   soul tier allows a constant effect up to a share of the effect's full
   range (capacity/600: petty 0.05 … grand 1), and the skill point budget
   applies on top (world/76 §123; `magic.json`
   `enchanting.constantEffectMagnitudeShareBySoul`).
3. **Brewing is Morrowind's picking with a by-effect filter.** The player
   picks two to four ingredients; effects show by skill (15/30/45/60); the
   screen also filters the bag by an effect the player can already see.
4. **Loops with eyes.** 2.9b runs one loop per station kind and per seam,
   and three player journeys as data (gather → brew → drink → coat → hit;
   buy → forge → temper; soul trap → enchant → use → recharge →
   disenchant) through the headless scene and game runners and one pod
   strip read by a reader, developed until each step is green.
5. **Out of the slice.** Cooking, spellmaking, the paid enchanting
   service (4.5); recipes whose ingredient rows do not exist yet are
   added when the rows are.

**Why.** The owner wants the Morrowind climb as a hard-won thing proved
end to end, without the slice pretending to be the top of it; a soul tier
that only ever bites at petty made bigger souls meaningless; the filter
is a screen convenience that leaves the rule intact; journeys are the
only harness that sees the systems joined as a player meets them.
