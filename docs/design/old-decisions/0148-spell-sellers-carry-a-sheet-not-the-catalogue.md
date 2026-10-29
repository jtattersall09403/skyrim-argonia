<!-- imported unchanged from elder-souls-argonia docs/decisions/0148-spell-sellers-carry-a-sheet-not-the-catalogue.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0148 Spell sellers carry a sheet-sized stock, not the catalogue

**Decision (owner, 2.9x owner calls).** The owner's words, verbatim:
"that's crazy long. Refine the rules that derive what spells a spell seller
sells. What's the distribution of numbers of spells sold by sellers in
Morrowind and Skyrim? Ours should roughly follow that. What system do those
games use?"

1. **What the games do** (dossier
   [spell-sellers](../../../world/sources/lore/topics/spell-sellers.md)).
   Morrowind: 86 base-game sellers sell between 5 and 27 spells each, with a
   median of 15 and quartiles of 12 and 19. Each covers 3.4 schools on
   average, led by one or two. Each seller's list is hand-authored on the
   NPC. Skyrim: court wizards sell 31 to 37 tomes (every school's Novice and
   Apprentice sets plus one school's Adept set) and College sellers 11 to 21
   (all tiers of their own school), median about 21. Tiers open at the
   player's school skill of 40 and 65.
2. **The rule** (`packages/economy/src/spellStock.ts` `sellerStock`, data
   `packages/economy/src/data/seller-stock.json`). The candidates are the
   spells the seller's own compiled sheet could cast (the §123 castability
   gate, as before). The rule drops:
   - signature and `namedFor` (Tribunal-named) rows;
   - spells named for a person ("Veloth's Benison"; a common-noun owner
     such as "Troll's Blood" stays);
   - shrine, Imperial-cult, Daedric and Dwemer rows;
   - birthsign spells and zero-cost powers;
   - the role's shunned effects.

   From the rest the rule picks a stock:
   - **Size**: 10 to 24 spells, rising with the seller's best school skill
     from 20 to 80. A 40-skill tree-minder gets 15, Morrowind's median.
   - **Spread**: each school's share is the role's school weight times the
     seller's skill in it.
   - **Within a school**: role-favoured effects come first, one spell per
     lead effect before any second, and the rest follow an order seeded by
     the seller's id. The pick is deterministic per seller.
   - **Signature spells** are always kept.
3. **Roles.** The class picks the role: `tree-minder` → tree-minder
   (Restoration, Mysticism, Illusion and Alteration; healing, cures,
   water-breathing, calming beasts), `healer` → priest (Restoration-led),
   any other class → hedge-caster (even weights).
4. **Unchanged.** Cure and blessing services, prices, the castability gate,
   and the caster repertoire (`spellStock`, which enemy casters read).
5. **Slice result.** Vees-Wai 15 spells, Swims-The-Channel-Twice 15 (they
   were 244 and 311). The seller window needs no paging.
