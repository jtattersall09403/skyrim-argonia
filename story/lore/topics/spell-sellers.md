# Spell sellers in Morrowind and Skyrim: how many spells, chosen how

Why this dossier exists: lane 2.9xi had to size a spell seller's stock
(decision [0148](../../../../docs/decisions/0148-spell-sellers-carry-a-sheet-not-the-catalogue.md))
after the owner found a 244-spell list "crazy long". These are game-system
facts, not province lore. Era policy [0002](../../../../docs/decisions/0002-era-and-source-confidence.md):
Morrowind's and Skyrim's own data, read from UESP. We copy the shape, not the
content.

Sources, read from the UESP MediaWiki API on 2026-10-20 (page, revision):
Morrowind:Spell Merchants 3411339; Tribunal:Spell Merchants 3329228;
Bloodmoon:Spell Merchants 3329227; Morrowind:Spellmakers 3545626;
Morrowind:Spells 3649384; Skyrim:Spells 3595907; Skyrim:Merchants 3654015;
the Standard Merchandise tables on the Skyrim NPC pages for Farengar
Secret-Fire, Wylandriah, Calcelmo, Sybille Stentor, Madena, Wuunferth the
Unliving, Falion, Nelacar, Tolfdir, Phinis Gestor, Colette Marence, Drevis
Neloren, Faralda, Enthir and Urag gro-Shub. Counts were made by script from
the wikitext tables.

## 1. Morrowind: spells per seller

- **CANON_EXPLICIT** (Spell Merchants tables). Base game, 86 sellers: min 5,
  lower quartile 12, median 15, upper quartile 18.75, max 27, mean 15.7.
  Tribunal, 6 sellers: min 12, median 21, max 27. Bloodmoon, 2 sellers: 6
  and 27. All 94 sellers: min 5, quartiles 12 and 19, median 15, max 27.
- Fewest: Melie Frenck 5, Arrille 7, Bratheru Oran 9. Most: Erer Darothril
  and Fanildil 27, Tunila Omavel 24.
- **Schools per seller** (base game): 1 school for 1 seller, 2 for 15, 3 for
  27, 4 for 33, 5 for 9 and 6 for 1. The mean is 3.4. The usual shape is one
  or two heavy schools and one to three thin ones (one to three spells each).
- **Leading school**: Restoration for 42 sellers, Destruction 17, Alteration
  9, Illusion 9, Conjuration 5, Mysticism 4. Mysticism is sold most widely
  (70 of 86 sellers) but is always thin.
- **By kind of seller** (patterns in the tables): temple, cult and healer
  sellers lead with Restoration (5 to 17 spells) and add some Mysticism.
  Mages Guild sellers lead with Destruction, Conjuration or Alteration.
  Telvanni sellers sell Conjuration, Destruction and Illusion. Morag Tong
  sellers sell Illusion and Mysticism. Some sellers deal only with members
  of a faction at a given rank.
- **How the list is chosen.** UESP says sellers are "typically
  spellcasters" and sell a spell whether or not the player can cast it.
  CANON_INFERRED, not stated on UESP and so marked unverified: the
  Construction Set gives an NPC a Spells service flag and a hand-authored
  spell list, and the seller offers that list without the spells the player
  already knows. Nothing is rolled or levelled. The school patterns come
  from how the designers authored each class and faction.

## 2. Skyrim: court wizards and the College

- **CANON_EXPLICIT** (Skyrim:Spells). Tomes sit in the merchant's chest as
  "Complete set of <tier> <school> Spell Tomes", one of each, and restock
  every two days. Adept sets appear only once the player's skill in that
  school is 40, Expert sets at 65. Master tomes are sold only after the
  school's ritual quest. Player level gates only tomes found as loot.
- **Base-game tomes on sale, by tier**: Novice 12, Apprentice 19, Adept 21,
  Expert 21, Master 10.
- **Court wizards** sell the Novice and Apprentice sets in every school (31
  tomes) and the Adept set of one school. That gives 37 for Farengar,
  Madena and Wuunferth (Destruction), 35 for Calcelmo, Falion (Conjuration)
  and Wylandriah (Alteration), and 33 for Sybille (Illusion). Nelacar sells
  a partial list of about 20.
- **College sellers** sell all four tiers of their own school only: Tolfdir
  11 (Alteration), Phinis Gestor 16 (Conjuration), Colette Marence 14
  (Restoration), Drevis Neloren 11 (Illusion), Faralda 21 (Destruction).
  Enthir sells the 21 Destruction tomes. Urag gro-Shub sells no tomes.
- Across these 14 sellers the count runs from 11 to 37, median about 21.

## 3. What we take

- A seller offers about Morrowind's number: our band is 10 to 24, around the
  median of 15. One or two heavy schools and a few thin ones, led by the
  seller's own craft.
- The list is the seller's own, as in Morrowind. We derive it from the
  seller's compiled sheet and role instead of authoring it by hand. Skyrim's
  skill gate is not taken: the seller's sheet decides, not the player's.
