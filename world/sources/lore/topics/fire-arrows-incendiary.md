# Fire arrows and the incendiary: Fire Salts

Status: `CANON_EXPLICIT` for the Morrowind and Skyrim ingredient records and the Dawnguard recipe; `CANON_DERIVED` for the slice choice (Fire Salts as the incendiary of crafted fire arrows). Era policy: [0002](../../../../docs/decisions/0002-era-and-source-confidence.md); Morrowind (3E 427) supplies the effect vocabulary, Skyrim (4E 201) the record our row comes from.

Sources, all fetched 2026-10-24 through the UESP API (`action=parse`, wikitext): Morrowind:Fire Salts; Skyrim:Fire Salts; Skyrim:Ammunition; Skyrim:Steel (Steel Smithing table); Skyrim:Dwarven (Dwarven Smithing table); Skyrim:Ancient Technology; searched with no hit for fire salts, fire arrows or atronach: Lore:Argonian, Lore:Black Marsh, Lore:Hist.

## The ingredient

| Game | Record | Value | Weight | Effects |
|---|---|---|---|---|
| Morrowind | `ingred_fire_salts_01` | 100 | 0.1 | Drain Health, Fortify Agility, Resist Frost, Fire Shield |
| Skyrim | Skyrim.esm INGR FireSalts, form 0003ad5e | 50 | 0.25 | Weakness to Frost, Resist Fire, Restore Magicka, Regenerate Magicka |

- Both games drop it from flame atronachs: Morrowind's in-game text calls it "the crystalline compound that precipitates from elemental fire in solution", collected from atronachs "banished from the mortal plane".
- Skyrim.esm INGR FireSalts read directly: model `Clutter\Ingredients\FireSaltPile.nif`, value 50, weight 0.25.
- Our row keeps the Morrowind four effects (the vocabulary the magic catalogue carries), the Skyrim mesh and the Skyrim value and weight, as `item.frost-salts` does.

## The incendiary in Skyrim (Dawnguard)

- Exploding Steel Bolt of Fire (xx00f1a0): 10 Steel Bolts + 1 Fire Salts makes 10 bolts. Explodes for 10 points of fire damage (UESP Skyrim:Ammunition).
- Exploding Dwarven Bolt of Fire (xx00f1b1): 10 Dwarven Bolts + 1 Fire Salts makes 10 bolts. Explodes for 15 points of fire damage.
- The ice twins take 1 Frost Salts instead, so salts are the elemental charge by design. Crafting needs Gunmar's forge at Fort Dawnguard, and the recipe is taught through Sorine's Ancient Technology errand.
- The explosion radius in units is not on UESP and Dawnguard.esm is not in the vault Data folder (Skyrim.esm and Update.esm only), so it is unrecorded here. Set it from the game's own scale, not from this dossier.

## Argonians and Black Marsh

No UESP lore page searched (Argonian, Black Marsh, Hist) mentions fire salts or fire on arrows. The reasons the item is here are the traders' route (as frost salts) and flame atronachs as the source; the whyHere stays at that.
