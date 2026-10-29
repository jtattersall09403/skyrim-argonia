# Magic effects and spells (Morrowind)

**Scope.** Every Morrowind spell effect and every Morrowind spell: the vendor spells of the six
school lists, the spells no vendor sells (NPC and creature spells, shrine blessings, the birthsign
spells) from the same pages' second tables, and the powers. Mined for the 2.9 catalogue
(`packages/magic`, decision 0146; world/76 §123).

**Source.** UESP, fetched 2026-10-20 through the MediaWiki API (action=parse, the
rendered page): `Morrowind:Spell_Effects`; `Morrowind:Alteration_Spells`, `Conjuration_Spells`,
`Destruction_Spells`, `Illusion_Spells`, `Mysticism_Spells`, `Restoration_Spells` (the list
`Morrowind:Spells` routes to); `Morrowind:Powers`; `Morrowind:Birthsigns`; the cost formula from
`Morrowind:Spellmaking`. The parsed cache is `packages/magic/scripts/uesp-morrowind-magic.json`;
`packages/magic/scripts/build_catalogue.py --write` regenerates the tables below and the json.

**Era and confidence (decision 0002).** These are game-system facts of *Morrowind* (3E 427), a
mechanics source, not a world-state claim: magic works the same in 4E 201 Black Marsh, and
nothing here says who in the province knows a spell. Confidence: primary for names, schools, base
costs and magnitudes (UESP transcribes the game data); derived for the cost formula (fitted:
with Morrowind's base costs it reproduces 701 of 851 listed prices exactly; the rest
are prices the game's editor set by hand, kept as they are).

## How the catalogue reads it

- **Cost.** Per effect `((max(1,min) + max(1,max)) × max(1,seconds) + areaFeet) × baseCost / 40`,
  × 1.5 on Target, summed and rounded half up. This is Morrowind's cost, the unit of the §123 gate
  (`2 × skill + Willpower/5 ≥ cost`). A spell the game's editor priced by hand keeps Morrowind's
  price (138 spells, `handPriced` in `spells.json`).
- **Tier.** The dearest `magic.json` tier whose `magickaCost` the cost reaches (novice below 8); a power, which costs nothing to cast, takes the tier of its formula cost.
- **Cast style.** By the range of the spell's dearest effect: Target aimed, Touch stream, Self
  self; Shield and the three elemental shields on Self are wards.
- **Parameterised effects.** Morrowind's Fortify, Drain, Damage, Restore and Absorb Attribute and
  Skill are one effect with a parameter; here each attribute and skill is its own row. Armorer is
  Smithing (§118). Luck is dropped (§127): Luck rows and Luck lines in spells are left out.
- **Bound Gloves.** UESP lists a left and a right gauntlet row; the game has one Bound Gloves
  effect, so the catalogue has one.
- **One tuning (0144 item 7).** A fortify on Alchemy, Enchant, Smithing, Intelligence or Strength
  (and absorbing one) is `rareFortify`. Its base cost is Morrowind's × 4.3, the smallest step
  that puts every spell carrying one at 60 or more; those spells are `signature`
  (they reach a seller only through that seller's own list).
- **Left out.** Spells whose every line is a Luck line: Hex (Damage Luck 1-20 pts on Touch); Absorb Luck (Absorb Luck 5-20 pts for 30 secs on Touch); Turn of the Wheel (Fortify Luck 5-20 pts for 30 secs on Self); Jack of Trades (Fortify Luck 10 pts for 60 secs on Self); Ogrul's Lucky-Again (Restore Luck 10 pts on Self); Restore Luck (Restore Luck 5-20 pts for 30 secs on Self); Luck of the Emperor (Fortify Luck 20 pts for 2 mins on Self); Curse Luck (Drain Luck 2-4 pts for 30 secs on Touch); Dread Curse: Luck (Damage Luck 5-12 pts on Touch); Grave Curse: Luck (Drain Luck 2-4 pts for 60 secs on Target); Misfortunate Touch (Drain Luck 5-20 pts for 30 secs on Touch); Misfortune (Drain Luck 5-20 pts for 30 secs on Target); Wild Misfortune (Drain Luck 5-20 pts for 1 min, 30 secs on Target); Absorb Luck [Ranged] (Absorb Luck 5-20 pts for 30 secs on Target); Daedric Luck (Fortify Luck 20 pts for 1 min, 30 secs on Self); Vivec's Mystery (Fortify Luck 10 pts for 48 mins on Touch); Wulfharth's Cups (Fortify Luck 1-8 pts for 12 mins on Self).

## Magnitude fills (derived from the cost formula)

**UESP (fetched 2026-10-21, `Morrowind:Destruction_Spells`)** prints seven spells with no magnitude:
"Weakness to Frost for 5 secs on Target 8" (and Magicka, Poison, Shock), "Weakness to Corprus Disease
for 10 secs on Touch 21" (and Blight, and the record named Corpus). Their siblings carry one:
"Weakness to Fire 10 pts for 5 secs on Target 8", "Weakness to Common Disease 1-20 pts for 10 secs on
Target 16". A weakness of 0 does nothing, so each takes the magnitude its own price implies
(confidence derived, decision 0002): the four elements at baseCost 2, 5 s, Target, cost 8 need
min + max of 20 to 22, `(20 × 5) × 2 / 40 × 1.5 = 7.5`, rounded 8, the same 10 points as Weakness to
Fire; the diseases at baseCost 4, 10 s, Touch, cost 21 need min + max = 21, `(21 × 10) × 4 / 40 = 21`,
the 1-20 of Weakness to Common Disease. `MAGNITUDE_FILLS` in the script holds them and refuses once the
source carries a magnitude of its own.

**What a weakness does (UESP `Morrowind:Weakness_to_Element`).** "M is the percentage of resistance
reduction. At 100% the target will receive double damage": it is taken off the target's resistance,
so it cancels a Resist Element first. A disease weakness makes the target M % more likely to catch
that disease (`Morrowind:Weakness_to_Common_Disease`). Skyrim, for comparison (UESP
`Skyrim:Weakness_to_Fire`, `_Frost`, `_Shock`, `_Magic`, `_Poison`): "Target is M% weaker", base
magnitude 3 for the elements and 2 for Magic and Poison on a poison of 30 s; Skyrim has no disease
weakness. Morrowind's 10 points for 5 s sits on Skyrim's scale for a cheap spell.

## Resistance (by effect, never by school)

**UESP (fetched 2026-10-21).** `Morrowind:Resist_Magicka` resists "Absorb Health, Damage Health,
Drain Health, ... Absorb/Damage/Drain Attribute, Absorb/Damage/Drain Skill, Blind, Burden, Sound,
Silence, Calm, Charm, Command, Demoralize, Frenzy, and any Weakness to Element effects" and "does
not protect against Paralyze". `Morrowind:Resist_Paralysis`: "Reduces the chance of being
Paralyzed by M%", added to the Willpower-based resistance. `Morrowind:Willpower` resists Paralyze and
Silence. No UESP page gives Disintegrate Armor or Weapon a resistance; OpenMW (a reimplementation,
corroborating only) maps them to Sanctuary, which is not a resistance. So `packages/magic/src/apply.ts`
`resistRule`: every harmful effect meets Willpower / 4 + Resist Magicka; the four elements add their
own field (§123 keeps Resist Magicka on them); Paralyze meets Willpower and Resist Paralysis only;
Calm meets Resist Magicka though it is not flagged harmful; Open, Disintegrate Armor and Weapon and
Soul Trap are not resisted (they act on an object or a soul, and are on no resistance list). Morrowind
rolls a flag effect (Paralyze, Silence) as a chance; the cast here is deterministic, so the resisted
share comes off its duration, the same expectation.

## Levitate movement speed (derived, not UESP)

**UESP (fetched 2026-10-20, `Morrowind:Levitate`, `Morrowind:Speed`, `Morrowind:Athletics`)** says only that the
speed of movement through the air is set by the magnitude M and by the Speed attribute, that Athletics
plays no part, and that it is "purely a factor of Speed and Encumbrance". It gives no numbers.

**The numbers come from OpenMW**, which reproduces the game's rule (decision 0002: a mechanics source,
confidence derived; this one entry relaxes the UESP-only rule). Read:
`apps/openmw/mwclass/npc.cpp`, `Npc::getMaxSpeed` (master e34a9e968, 2026-10-20; file last changed c8604bc27)
and the default GMSTs in `apps/opencs/model/world/defaultgmsts.cpp` (fMinFlySpeed 5, fMaxFlySpeed 300,
fEncumberedMoveEffect 0.3).

    t     = 0.01 * (Speed + M)
    speed = (fMinFlySpeed + t * (fMaxFlySpeed - fMinFlySpeed)) * (1 - fEncumberedMoveEffect * load)

`speed` is in Morrowind units per second; `load` is carried weight over capacity, and above 1 the body
cannot move. Carried into `magic.json` `levitate` and `levitateSpeedMps` (`game-core/physics/levitateDrive.ts`).

## Effects (141 UESP rows, 301 catalogue rows)

| Morrowind effect | School | Base cost | Catalogue ids |
|---|---|---|---|
| Burden | Alteration | 1 | `burden` |
| Feather | Alteration | 1 | `feather` |
| Fire Shield | Alteration | 3 | `fire-shield` |
| Frost Shield | Alteration | 3 | `frost-shield` |
| Jump | Alteration | 3 | `jump` |
| Levitate | Alteration | 3 | `levitate` |
| Lightning Shield | Alteration | 3 | `lightning-shield` |
| Lock | Alteration | 2 | `lock` |
| Open | Alteration | 6 | `open` |
| Shield | Alteration | 2 | `shield` |
| Slowfall | Alteration | 3 | `slowfall` |
| Swift Swim | Alteration | 2 | `swift-swim` |
| Water Breathing | Alteration | 3 | `water-breathing` |
| Water Walking | Alteration | 3 | `water-walking` |
| Bound Battle Axe | Conjuration | 2 | `bound-battle-axe` |
| Bound Boots | Conjuration | 2 | `bound-boots` |
| Bound Cuirass | Conjuration | 2 | `bound-cuirass` |
| Bound Dagger | Conjuration | 2 | `bound-dagger` |
| Bound Left Gauntlet | Conjuration | 2 | `bound-gloves` |
| Bound Right Gauntlet | Conjuration | 2 | `bound-gloves` |
| Bound Helm | Conjuration | 2 | `bound-helm` |
| Bound Longbow | Conjuration | 2 | `bound-longbow` |
| Bound Longsword | Conjuration | 2 | `bound-longsword` |
| Bound Mace | Conjuration | 2 | `bound-mace` |
| Bound Shield | Conjuration | 2 | `bound-shield` |
| Bound Spear | Conjuration | 2 | `bound-spear` |
| Command Creature | Conjuration | 15 | `command-creature` |
| Command Humanoid | Conjuration | 15 | `command-humanoid` |
| Summon Ancestral Ghost | Conjuration | 7 | `summon-ancestral-ghost` |
| Summon Bonelord | Conjuration | 25 | `summon-bonelord` |
| Summon Bonewalker | Conjuration | 13 | `summon-bonewalker` |
| Summon Bonewolf (Bloodmoon) | Conjuration | 30 | `summon-bonewolf` |
| Summon Centurion Sphere | Conjuration | 25 | `summon-centurion-sphere` |
| Summon Clannfear | Conjuration | 22 | `summon-clannfear` |
| Summon Daedroth | Conjuration | 32 | `summon-daedroth` |
| Summon Dremora | Conjuration | 28 | `summon-dremora` |
| Summon Fabricant (Tribunal) | Conjuration | 10 | `summon-fabricant` |
| Summon Flame Atronach | Conjuration | 23 | `summon-flame-atronach` |
| Summon Frost Atronach | Conjuration | 27 | `summon-frost-atronach` |
| Summon Golden Saint | Conjuration | 55 | `summon-golden-saint` |
| Summon Greater Bonewalker | Conjuration | 15 | `summon-greater-bonewalker` |
| Summon Grizzly Bear (Bloodmoon) | Conjuration | 30 | `summon-grizzly-bear` |
| Summon Hunger | Conjuration | 29 | `summon-hunger` |
| Summon Scamp | Conjuration | 12 | `summon-scamp` |
| Summon Skeletal Minion | Conjuration | 13 | `summon-skeletal-minion` |
| Summon Storm Atronach | Conjuration | 38 | `summon-storm-atronach` |
| Summon Wolf (Bloodmoon) | Conjuration | 30 | `summon-wolf` |
| Summon Winged Twilight | Conjuration | 52 | `summon-winged-twilight` |
| Turn Undead | Conjuration | 0.2 | `turn-undead` |
| Corprus | Destruction | 2500 | `corprus` |
| Damage Attribute | Destruction | 8 | `damage-strength` … `damage-personality` (7 rows) |
| Damage Fatigue | Destruction | 4 | `damage-fatigue` |
| Damage Health | Destruction | 8 | `damage-health` |
| Damage Magicka | Destruction | 8 | `damage-magicka` |
| Damage Skill | Destruction | 8 | `damage-long-blade` … `damage-restoration` (27 rows) |
| Disintegrate Armor | Destruction | 6 | `disintegrate-armor` |
| Disintegrate Weapon | Destruction | 6 | `disintegrate-weapon` |
| Drain Attribute | Destruction | 1 | `drain-strength` … `drain-personality` (7 rows) |
| Drain Fatigue | Destruction | 2 | `drain-fatigue` |
| Drain Health | Destruction | 4 | `drain-health` |
| Drain Magicka | Destruction | 4 | `drain-magicka` |
| Drain Skill | Destruction | 1 | `drain-long-blade` … `drain-restoration` (27 rows) |
| Fire Damage | Destruction | 5 | `fire-damage` |
| Frost Damage | Destruction | 5 | `frost-damage` |
| Poison | Destruction | 9 | `poison` |
| Shock Damage | Destruction | 7 | `shock-damage` |
| Stunted Magicka | Destruction | 1 | `stunted-magicka` |
| Sun Damage | Destruction | 1 | `sun-damage` |
| Vampirism | Destruction | 5 | `vampirism` |
| Weakness to Blight Disease | Destruction | 4 | `weakness-to-blight-disease` |
| Weakness to Common Disease | Destruction | 2 | `weakness-to-common-disease` |
| Weakness to Corprus Disease | Destruction | 4 | `weakness-to-corprus-disease` |
| Weakness to Fire | Destruction | 2 | `weakness-to-fire` |
| Weakness to Frost | Destruction | 2 | `weakness-to-frost` |
| Weakness to Magicka | Destruction | 2 | `weakness-to-magicka` |
| Weakness to Normal Weapons | Destruction | 2 | `weakness-to-normal-weapons` |
| Weakness to Poison | Destruction | 2 | `weakness-to-poison` |
| Weakness to Shock | Destruction | 2 | `weakness-to-shock` |
| Blind | Illusion | 1 | `blind` |
| Calm Creature | Illusion | 1 | `calm-creature` |
| Calm Humanoid | Illusion | 1 | `calm-humanoid` |
| Chameleon | Illusion | 1 | `chameleon` |
| Charm | Illusion | 5 | `charm` |
| Demoralize Creature | Illusion | 1 | `demoralize-creature` |
| Demoralize Humanoid | Illusion | 1 | `demoralize-humanoid` |
| Frenzy Creature | Illusion | 1 | `frenzy-creature` |
| Frenzy Humanoid | Illusion | 1 | `frenzy-humanoid` |
| Invisibility | Illusion | 20 | `invisibility` |
| Light | Illusion | 0.2 | `light` |
| Night Eye | Illusion | 0.2 | `night-eye` |
| Paralyze | Illusion | 40 | `paralyze` |
| Rally Creature | Illusion | 0.2 | `rally-creature` |
| Rally Humanoid | Illusion | 0.2 | `rally-humanoid` |
| Sanctuary | Illusion | 1 | `sanctuary` |
| Silence | Illusion | 40 | `silence` |
| Sound | Illusion | 3 | `sound` |
| Absorb Attribute | Mysticism | 2 | `absorb-strength` … `absorb-personality` (7 rows) |
| Absorb Fatigue | Mysticism | 4 | `absorb-fatigue` |
| Absorb Health | Mysticism | 8 | `absorb-health` |
| Absorb Magicka | Mysticism | 8 | `absorb-magicka` |
| Absorb Skill | Mysticism | 2 | `absorb-long-blade` … `absorb-restoration` (27 rows) |
| Almsivi Intervention | Mysticism | 150 | `almsivi-intervention` |
| Detect Animal | Mysticism | 0.75 | `detect-animal` |
| Detect Enchantment | Mysticism | 1 | `detect-enchantment` |
| Detect Key | Mysticism | 1 | `detect-key` |
| Dispel | Mysticism | 5 | `dispel` |
| Divine Intervention | Mysticism | 150 | `divine-intervention` |
| Mark | Mysticism | 350 | `mark` |
| Recall | Mysticism | 350 | `recall` |
| Reflect | Mysticism | 10 | `reflect` |
| Soultrap | Mysticism | 2 | `soultrap` |
| Spell Absorption | Mysticism | 10 | `spell-absorption` |
| Telekinesis | Mysticism | 1 | `telekinesis` |
| Cure Blight Disease | Restoration | 2000 | `cure-blight-disease` |
| Cure Common Disease | Restoration | 300 | `cure-common-disease` |
| Cure Corprus Disease | Restoration | 2500 | `cure-corprus-disease` |
| Cure Paralyzation | Restoration | 100 | `cure-paralyzation` |
| Cure Poison | Restoration | 100 | `cure-poison` |
| Fortify Attack | Restoration | 1 | `fortify-attack` |
| Fortify Attribute | Restoration | 1 | `fortify-strength` … `fortify-personality` (7 rows) |
| Fortify Fatigue | Restoration | 0.5 | `fortify-fatigue` |
| Fortify Health | Restoration | 1 | `fortify-health` |
| Fortify Magicka | Restoration | 1 | `fortify-magicka` |
| Fortify Maximum Magicka | Restoration | 4 | `fortify-maximum-magicka` |
| Fortify Skill | Restoration | 1 | `fortify-long-blade` … `fortify-restoration` (27 rows) |
| Remove Curse | Restoration | 15 | `remove-curse` |
| Resist Blight Disease | Restoration | 5 | `resist-blight-disease` |
| Resist Common Disease | Restoration | 2 | `resist-common-disease` |
| Resist Corprus Disease | Restoration | 5 | `resist-corprus-disease` |
| Resist Fire | Restoration | 2 | `resist-fire` |
| Resist Frost | Restoration | 2 | `resist-frost` |
| Resist Magicka | Restoration | 2 | `resist-magicka` |
| Resist Normal Weapons | Restoration | 5 | `resist-normal-weapons` |
| Resist Paralysis | Restoration | 0.2 | `resist-paralysis` |
| Resist Poison | Restoration | 2 | `resist-poison` |
| Resist Shock | Restoration | 2 | `resist-shock` |
| Restore Attribute | Restoration | 1 | `restore-strength` … `restore-personality` (7 rows) |
| Restore Fatigue | Restoration | 1 | `restore-fatigue` |
| Restore Health | Restoration | 5 | `restore-health` |
| Restore Magicka | Restoration | 5 | `restore-magicka` |
| Restore Skill | Restoration | 1 | `restore-long-blade` … `restore-restoration` (27 rows) |

## Spells (874)

Cost is Morrowind's listed price; *ours* is the catalogue's where it differs (a rareFortify
spell, or no listed price).

| Spell | Kind | School | Effects (UESP) | Cost | Id |
|---|---|---|---|---|---|
| Burden | spell | alteration | Burden 20 pts for 10 secs on Target | 15 | `burden` |
| Heavy Burden Touch | spell | alteration | Burden 40 pts for 10 secs on Touch | 20 | `heavy-burden-touch` |
| Crushing Burden Touch | spell | alteration | Burden 60 pts for 10 secs on Touch | 30 | `crushing-burden-touch` |
| Great Burden of Sin | spell | alteration | Burden 40 pts for 10 secs on Target | 30 | `great-burden-of-sin` |
| Heavy Burden | spell | alteration | Burden 40 pts for 10 secs on Target | 30 | `heavy-burden` |
| Weary | spell | alteration | Burden 30-60 pts for 10 secs on Target | 34 | `weary` |
| Cruel Weary | spell | alteration | Burden 50-70 pts for 10 secs on Target | 45 | `cruel-weary` |
| Crushing Burden | spell | alteration | Burden 60 pts for 10 secs on Target | 45 | `crushing-burden` |
| Burden of Sin | spell | alteration | Burden 40-60 pts for 20 secs on Touch | 50 | `burden-of-sin` |
| Dire Weary | spell | alteration | Burden 60-90 pts for 10 secs on Target | 56 | `dire-weary` |
| Crushing Burden of Sin | spell | alteration | Burden 60-80 pts for 30 secs on Target | 158 | `crushing-burden-of-sin` |
| Feather | spell | alteration | Feather 20 pts for 10 secs on Self | 10 | `feather` |
| Strong Feather | spell | alteration | Feather 50 pts for 10 secs on Self | 25 | `strong-feather` |
| Ulms's Juicedaw's Feather | spell | alteration | Feather 50 pts for 10 secs on Self | 25 | `ulmss-juicedaws-feather` |
| Great Feather | spell | alteration | Feather 100 pts for 10 secs on Self | 50 | `great-feather` |
| Fire Barrier | spell | alteration | Fire Shield 1-10 pts for 10 secs on Self | 8 | `fire-barrier` |
| Fire Shield | spell | alteration | Fire Shield 10 pts for 30 secs on Self | 45 | `fire-shield` |
| Strong Fire Shield | spell | alteration | Fire Shield 12 pts for 30 secs on Self | 54 | `strong-fire-shield` |
| Frost Barrier | spell | alteration | Frost Shield 3 pts for 10 secs on Self | 5 | `frost-barrier` |
| Frost Shield | spell | alteration | Frost Shield 6 pts for 30 secs on Self | 27 | `frost-shield` |
| Strong Frost Shield | spell | alteration | Frost Shield 12 pts for 30 secs on Self | 54 | `strong-frost-shield` |
| Tinur's Hoptoad | spell | alteration | Jump 20 pts for 10 secs on Self | 30 | `tinurs-hoptoad` |
| Strong Levitate | spell | alteration | Levitate 20 pts for 10 secs on Self | 30 | `strong-levitate` |
| Levitate | spell | alteration | Levitate 10 pts for 30 secs on Self | 45 | `levitate` |
| Wild Levitate | spell | alteration | Levitate 1-50 pts for 30 secs on Self | 115 | `wild-levitate` |
| Shock Barrier | spell | alteration | Lightning Shield 1-10 pts for 10 secs on Self | 8 | `shock-barrier` |
| Lightning Shield | spell | alteration | Lightning Shield 10 pts for 30 secs on Self | 45 | `lightning-shield` |
| Strong Shock Shield | spell | alteration | Lightning Shield 12 pts for 30 secs on Self | 54 | `strong-shock-shield` |
| Fenrick's Doorjam | spell | alteration | Lock 10 pts on Touch | 1 | `fenricks-doorjam` |
| Ondusi's Open Door | spell | alteration | Open 50 pts on Touch | 15 | `ondusis-open-door` |
| Open | spell | alteration | Open 20 pts on Touch | 6 | `open` |
| Strong Open | spell | alteration | Open 50 pts on Touch | 15 | `strong-open` |
| Wild Open | spell | alteration | Open 1-100 pts on Touch | 15 | `wild-open` |
| Shield | spell | alteration | Shield 5 pts for 30 secs on Self | 15 | `shield` |
| First Barrier | spell | alteration | Shield 10 pts for 30 secs on Self | 30 | `first-barrier` |
| Second Barrier | spell | alteration | Shield 20 pts for 30 secs on Self | 60 | `second-barrier` |
| Third Barrier | spell | alteration | Shield 30 pts for 30 secs on Self | 90 | `third-barrier` |
| Fourth Barrier | spell | alteration | Shield 40 pts for 30 secs on Self | 120 | `fourth-barrier` |
| Fifth Barrier | spell | alteration | Shield 50 pts for 30 secs on Self | 150 | `fifth-barrier` |
| Sixth Barrier | spell | alteration | Shield 60 pts for 30 secs on Self | 180 | `sixth-barrier` |
| Slowfall | spell | alteration | Slowfall 30 pts for 10 secs on Self | 45 | `slowfall` |
| Buoyancy | spell | alteration | Swift Swim 1 pt for 20 secs on Self | 2 | `buoyancy` |
| Swimmer's Blessing | spell | alteration | Swift Swim 5 pts for 30 secs on Self | 15 | `swimmers-blessing` |
| Water Breathing | spell | alteration | Water Breathing for 30 secs on Self | 5 | `water-breathing` |
| Vivec's Kiss | spell | alteration | Water Breathing for 1 min, 40 secs on Self | 15 | `vivecs-kiss` |
| Water Walking | spell | alteration | Water Walking for 60 secs on Self | 9 | `water-walking` |
| Bound Battle-Axe | spell | conjuration | Bound Battle Axe for 60 secs on Self | 6 | `bound-battle-axe` |
| Bound Boots | spell | conjuration | Bound Boots for 60 secs on Self | 6 | `bound-boots` |
| Bound Cuirass | spell | conjuration | Bound Cuirass for 60 secs on Self | 6 | `bound-cuirass` |
| Bound Dagger | spell | conjuration | Bound Dagger for 60 secs on Self | 6 | `bound-dagger` |
| Bound Gauntlets | spell | conjuration | Bound Gloves for 60 secs on Self | 6 | `bound-gauntlets` |
| Bound Helm | spell | conjuration | Bound Helm for 60 secs on Self | 6 | `bound-helm` |
| Bound Longbow | spell | conjuration | Bound Longbow for 60 secs on Self | 6 | `bound-longbow` |
| Bound Longsword | spell | conjuration | Bound Longsword for 60 secs on Self | 6 | `bound-longsword` |
| Bound Mace | spell | conjuration | Bound Mace for 60 secs on Self | 6 | `bound-mace` |
| Bound Shield | spell | conjuration | Bound Shield for 60 secs on Self | 6 | `bound-shield` |
| Bound Spear | spell | conjuration | Bound Spear for 60 secs on Self | 6 | `bound-spear` |
| Command Creature | spell | conjuration | Command Creature 5 pts for 30 secs on Target | 169 | `command-creature` |
| Command of the Third Corner | spell | conjuration | Command Humanoid 5-25 pts for 30 secs on Touch | 30 | `command-of-the-third-corner` |
| Commanding Touch | spell | conjuration | Command Humanoid 5 pts for 10 secs on Touch | 38 | `commanding-touch` |
| Command Humanoid | spell | conjuration | Command Humanoid 5 pts for 30 secs on Target | 169 | `command-humanoid` |
| Summon Ancestral Ghost | spell | conjuration | Summon Ancestral Ghost for 60 secs on Self | 21 | `summon-ancestral-ghost` |
| Summon Bonelord | spell | conjuration | Summon Bonelord for 60 secs on Self | 75 | `summon-bonelord` |
| Summon Least Bonewalker | spell | conjuration | Summon Bonewalker for 60 secs on Self | 39 | `summon-least-bonewalker` |
| Dwemer Animunculi | spell | conjuration | Summon Centurion Sphere for 2 mins on Self | 75 | `dwemer-animunculi` |
| Summon Clannfear | spell | conjuration | Summon Clannfear for 60 secs on Self | 66 | `summon-clannfear` |
| Summon Daedroth | spell | conjuration | Summon Daedroth for 60 secs on Self | 96 | `summon-daedroth` |
| Summon Dremora | spell | conjuration | Summon Dremora for 60 secs on Self | 84 | `summon-dremora` |
| Summon Flame Atronach | spell | conjuration | Summon Flame Atronach for 60 secs on Self | 69 | `summon-flame-atronach` |
| Summon Frost Atronach | spell | conjuration | Summon Frost Atronach for 60 secs on Self | 81 | `summon-frost-atronach` |
| Summon Golden Saint | spell | conjuration | Summon Golden Saint for 60 secs on Self | 165 | `summon-golden-saint` |
| Summon Greater Bonewalker | spell | conjuration | Summon Greater Bonewalker for 60 secs on Self | 45 | `summon-greater-bonewalker` |
| Summon Hunger | spell | conjuration | Summon Hunger for 60 secs on Self | 87 | `summon-hunger` |
| Summon Scamp | spell | conjuration | Summon Scamp for 60 secs on Self | 36 | `summon-scamp` |
| Summon Skeletal Minion | spell | conjuration | Summon Skeletal Minion for 60 secs on Self | 39 | `summon-skeletal-minion` |
| Summon Storm Atronach | spell | conjuration | Summon Storm Atronach for 60 secs on Self | 114 | `summon-storm-atronach` |
| Summon Winged Twilight | spell | conjuration | Summon Winged Twilight for 60 secs on Self | 156 | `summon-winged-twilight` |
| Blessed Touch | spell | conjuration | Turn Undead 100 pts for 30 secs on Touch | 5 | `blessed-touch` |
| Holy Word | spell | conjuration | Turn Undead 5 pts for 60 secs on Target | 5 | `holy-word` |
| Turn Undead | spell | conjuration | Turn Undead 50 pts for 10 secs on Touch | 5 | `turn-undead` |
| Holy Touch | spell | conjuration | Turn Undead 10 pts for 60 secs on Touch | 6 | `holy-touch` |
| Saintly Touch | spell | conjuration | Turn Undead 25 pts for 60 secs on Touch | 15 | `saintly-touch` |
| Saintly Word | spell | conjuration | Turn Undead 25 pts for 60 secs on Target | 23 | `saintly-word` |
| Evil Eye | spell | destruction | Damage Personality 1-10 pts on Touch | 2 | `evil-eye` |
| Clench | spell | destruction | Damage Speed 1-20 pts on Touch | 4 | `clench` |
| Emasculate | spell | destruction | Damage Endurance 1-20 pts on Touch | 4 | `emasculate` |
| Fuddle | spell | destruction | Damage Intelligence 1-20 pts on Touch | 4 | `fuddle` |
| Stumble | spell | destruction | Damage Agility 1-20 pts on Touch | 4 | `stumble` |
| Woe | spell | destruction | Damage Willpower 1-20 pts on Touch | 4 | `woe` |
| Fleabite | spell | destruction | Damage Fatigue 1-10 pts on Touch | 1 | `fleabite` |
| Doze | spell | destruction | Damage Fatigue 1-20 pts on Touch | 2 | `doze` |
| Hornhand | spell | destruction | Damage Fatigue 15-36 pts on Touch | 5 | `hornhand` |
| Spirit Knife | spell | destruction | Damage Health 1-20 pts on Touch | 4 | `spirit-knife` |
| Stormhand | spell | destruction | Damage Health 5-12 pts on Touch; Shock Damage 5-12 pts on Touch | 6 | `stormhand` |
| Black Hand | spell | destruction | Damage Health 5-12 pts on Touch; Poison 5-12 pts on Touch | 7 | `black-hand` |
| Heartbite | spell | destruction | Damage Health 10-50 pts on Touch | 12 | `heartbite` |
| Daedric Bite | spell | destruction | Damage Health 50 pts on Target | 30 | `daedric-bite` |
| Soulpinch | spell | destruction | Damage Magicka 1-20 pts on Touch | 4 | `soulpinch` |
| Armor Eater | spell | destruction | Disintegrate Armor 10-30 pts on Touch | 6 | `armor-eater` |
| Weapon Eater | spell | destruction | Disintegrate Weapon 6-25 pts on Touch | 5 | `weapon-eater` |
| Clumsy Touch | spell | destruction | Drain Agility 5-20 pts for 30 secs on Touch | 19 | `clumsy-touch` |
| Distraction | spell | destruction | Drain Intelligence 5-20 pts for 30 secs on Target | 28 | `distraction` |
| Enervate | spell | destruction | Drain Endurance 5-20 pts for 30 secs on Target | 28 | `enervate` |
| Spite | spell | destruction | Drain Personality 5-20 pts for 30 secs on Target | 28 | `spite` |
| Temptation | spell | destruction | Drain Willpower 5-20 pts for 30 secs on Target | 28 | `temptation` |
| Torpor | spell | destruction | Drain Speed 5-20 pts for 30 secs on Target | 28 | `torpor` |
| Strength Leech | spell | destruction | Drain Strength 20 pts for 30 secs on Touch | 30 | `strength-leech` |
| Distracting Touch | spell | destruction | Drain Intelligence 5-20 pts for 60 secs on Touch | 38 | `distracting-touch` |
| Blood Despair | spell | destruction | Drain Willpower 7-14 pts for 60 secs on Target | 47 | `blood-despair` |
| Wild Distraction | spell | destruction | Drain Intelligence 5-20 pts for 60 secs on Target | 56 | `wild-distraction` |
| Wearying Touch | spell | destruction | Drain Fatigue 5-20 pts for 30 secs on Touch | 38 | `wearying-touch` |
| Sleep | spell | destruction | Drain Fatigue 5-15 pts for 30 secs on Target | 45 | `sleep` |
| Exhausting Touch | spell | destruction | Drain Fatigue 5-20 pts for 60 secs on Touch | 75 | `exhausting-touch` |
| Ordeal of St. Olms | spell | destruction | Drain Fatigue 5-20 pts for 60 secs on Touch | 75 | `ordeal-of-st-olms` |
| Wild Exhaustion | spell | destruction | Drain Fatigue 5-15 pts for 60 secs on Target | 90 | `wild-exhaustion` |
| Drain Blood | spell | destruction | Drain Health 5 pts for 30 secs on Touch; Drain Magicka 5 pts for 30 secs on Touch | 60 | `drain-blood` |
| Wild Flay Spirit | spell | destruction | Drain Magicka 1-20 pts for 3 secs on Target | 9 | `wild-flay-spirit` |
| Gash Spirit | spell | destruction | Drain Magicka 5-20 pts for 30 secs on Touch | 75 | `gash-spirit` |
| Gash Spirit [Ranged] | spell | destruction | Drain Magicka 5-20 pts for 30 secs on Target | 113 | `gash-spirit-ranged` |
| Magicka Leech | spell | destruction | Drain Magicka 6-15 pts for 60 secs on Touch | 126 | `magicka-leech` |
| Flay Spirit | spell | destruction | Drain Magicka 5-20 pts for 60 secs on Touch | 150 | `flay-spirit` |
| Drain Athletics | spell | destruction | Drain Athletics 5-20 pts for 60 secs on Target | 56 | `drain-athletics` |
| Drain Block | spell | destruction | Drain Block 5-20 pts for 60 secs on Target | 56 | `drain-block` |
| Drain Destruction | spell | destruction | Drain Destruction 5-20 pts for 60 secs on Target | 56 | `drain-destruction` |
| Scourge Blade | spell | destruction | Drain Long Blade 5-20 pts for 30 secs on Target; Drain Short Blade 5-20 pts for 30 secs on Target | 56 | `scourge-blade` |
| Fireball | spell | destruction | Fire Damage 2-20 pts in 5ft on Target | 5 | `fireball` |
| Fire Bite | spell | destruction | Fire Damage 15-30 pts on Touch | 6 | `fire-bite` |
| Cruel Firebloom | spell | destruction | Fire Damage 10-16 pts in 10ft on Target | 7 | `cruel-firebloom` |
| Greater Fireball | spell | destruction | Fire Damage 2-40 pts in 10ft on Target | 10 | `greater-fireball` |
| Fire Storm | spell | destruction | Fire Damage 1-10 pts in 10ft for 10 secs on Target | 23 | `fire-storm` |
| God's Fire | spell | destruction | Fire Damage 11-60 pts in 10ft for 10 secs on Target | 135 | `gods-fire` |
| Frostbite | spell | destruction | Frost Damage 15-30 pts on Touch | 6 | `frostbite` |
| Greater Frostball | spell | destruction | Frost Damage 2-40 pts in 10ft on Target | 10 | `greater-frostball` |
| Frost Storm | spell | destruction | Frost Damage 1-10 pts in 10ft for 10 secs on Target | 23 | `frost-storm` |
| God's Frost | spell | destruction | Frost Damage 11-60 pts in 10ft for 10 secs on Target | 135 | `gods-frost` |
| Poison | spell | destruction | Poison 2-20 pts in 5ft on Target | 9 | `poison` |
| Poisonous Touch | spell | destruction | Poison 15-40 pts on Touch | 12 | `poisonous-touch` |
| Poisonbloom | spell | destruction | Poison 1-20 pts in 10ft for 5 secs on Target | 39 | `poisonbloom` |
| Viperbolt | spell | destruction | Poison 10-50 pts in 10ft for 2 secs on Target | 44 | `viperbolt` |
| Deadly Poison | spell | destruction | Poison 1-20 pts for 10 secs on Touch | 47 | `deadly-poison` |
| Toxic Cloud | spell | destruction | Poison 2-15 pts in 10ft for 10 secs on Target | 61 | `toxic-cloud` |
| Potent Poison | spell | destruction | Poison 20-40 pts for 5 secs on Touch | 68 | `potent-poison` |
| Shock | spell | destruction | Shock Damage 1-15 pts on Touch | 3 | `shock` |
| Spark | spell | destruction | Shock Damage 2-20 pts in 5ft on Target | 7 | `spark` |
| Greater Shockball | spell | destruction | Shock Damage 2-40 pts in 10ft on Target | 14 | `greater-shockball` |
| Shockball | spell | destruction | Shock Damage 2-40 pts in 10ft on Target | 14 | `shockball` |
| Lightning Bolt | spell | destruction | Shock Damage 10-50 pts in 10ft for 2 secs on Target | 34 | `lightning-bolt` |
| Lightning Storm | spell | destruction | Shock Damage 2-10 pts in 10ft for 10 secs on Target | 34 | `lightning-storm` |
| Shockbloom | spell | destruction | Shock Damage 1-25 pts in 10ft for 5 secs on Target | 37 | `shockbloom` |
| Weakness to Common Disease | spell | destruction | Weakness to Common Disease 1-20 pts for 10 secs on Target | 16 | `weakness-to-common-disease` |
| Weakness to Fire | spell | destruction | Weakness to Fire 10 pts for 5 secs on Target | 8 | `weakness-to-fire` |
| Dire Weakness to Fire | spell | destruction | Weakness to Fire 2-60 pts for 10 secs on Target | 47 | `dire-weakness-to-fire` |
| Dire Weakness to Frost | spell | destruction | Weakness to Frost 2-60 pts for 10 secs on Target | 47 | `dire-weakness-to-frost` |
| Dire Weakness to Magicka | spell | destruction | Weakness to Magicka 2-60 pts for 10 secs on Target | 47 | `dire-weakness-to-magicka` |
| Dire Weakness to Poison | spell | destruction | Weakness to Poison 2-60 pts for 10 secs on Target | 47 | `dire-weakness-to-poison` |
| Dire Weakness to Shock | spell | destruction | Weakness to Shock 2-60 pts for 10 secs on Target | 47 | `dire-weakness-to-shock` |
| Crying Eye | spell | illusion | Blind 1-10 pts for 5 secs on Target | 2 | `crying-eye` |
| Erelvam's Wild Sty | spell | illusion | Blind 1-40 pts for 10 secs on Touch | 10 | `erelvams-wild-sty` |
| Alad's Caliginy | spell | illusion | Blind 10-30 pts for 30 secs on Touch | 30 | `alads-caliginy` |
| Calm Creature | spell | illusion | Calm Creature 30 pts for 10 secs on Target | 23 | `calm-creature` |
| Calming Touch | spell | illusion | Calm Humanoid 30 pts for 10 secs on Touch | 15 | `calming-touch` |
| Calm Humanoid | spell | illusion | Calm Humanoid 30 pts for 10 secs on Target | 23 | `calm-humanoid` |
| Golanar's Eye-Maze | spell | illusion | Chameleon 10-40 pts for 10 secs on Self | 13 | `golanars-eye-maze` |
| Chameleon | spell | illusion | Chameleon 10 pts for 30 secs on Self | 15 | `chameleon` |
| Shadow Form | spell | illusion | Chameleon 6-15 pts for 30 secs on Self | 16 | `shadow-form` |
| Shadow Weave | spell | illusion | Chameleon 20 pts for 10 secs on Self; Sanctuary 20 pts for 10 secs on Self | 20 | `shadow-weave` |
| Mephala's Skill | spell | illusion | Chameleon 50 pts for 60 secs on Self; Fortify Attack 10 pts for 60 secs on Self | 30 | `mephalas-skill` |
| Shadowmask | spell | illusion | Chameleon 40-70 pts for 30 secs on Self | 83 | `shadowmask` |
| Charming Touch | spell | illusion | Charm 30 pts for 30 secs on Touch | 225 | `charming-touch` |
| Charm Mortal | spell | illusion | Charm 10-30 pts for 30 secs on Target | 225 | `charm-mortal` |
| Demoralize Beast | spell | illusion | Demoralize Creature 5 pts for 10 secs on Target | 4 | `demoralize-beast` |
| Demoralize Creature | spell | illusion | Demoralize Creature 5 pts for 10 secs on Target | 4 | `demoralize-creature` |
| Frenzy Beast | spell | illusion | Frenzy Creature 5 pts for 10 secs on Touch | 3 | `frenzy-beast` |
| Frenzy Creature | spell | illusion | Frenzy Creature 5 pts for 10 secs on Target | 4 | `frenzy-creature` |
| Frenzying Touch | spell | illusion | Frenzy Humanoid 5 pts for 10 secs on Touch | 3 | `frenzying-touch` |
| Brevusa's Averted Eyes | spell | illusion | Invisibility for 10 secs on Self | 10 | `brevusas-averted-eyes` |
| Hide | spell | illusion | Invisibility for 30 secs on Self | 30 | `hide` |
| Invisibility | spell | illusion | Invisibility for 30 secs on Self | 30 | `invisibility` |
| Concealment | spell | illusion | Invisibility for 1 min, 30 secs on Self | 90 | `concealment` |
| Light | spell | illusion | Light 20 pts in 30ft for 30 secs on Target | 9 | `light` |
| Night-Eye | spell | illusion | Night Eye 20 pts for 30 secs on Self | 6 | `night-eye` |
| Paralysis | spell | illusion | Paralyze for 5 secs on Touch | 10 | `paralysis` |
| Medusa's Gaze | spell | illusion | Paralyze for 15 secs on Target | 45 | `medusas-gaze` |
| Rally Beast | spell | illusion | Rally Creature 5 pts for 30 secs on Target | 2 | `rally-beast` |
| Rally Creature | spell | illusion | Rally Creature 5 pts for 30 secs on Target | 2 | `rally-creature` |
| Rally Humanoid | spell | illusion | Rally Humanoid 5 pts for 30 secs on Target | 2 | `rally-humanoid` |
| Rallying Touch | spell | illusion | Rally Humanoid 5 pts for 30 secs on Touch | 2 | `rallying-touch` |
| Sotha's Grace | spell | illusion | Sanctuary 1-20 pts for 5 secs on Self | 3 | `sothas-grace` |
| Father's Hand | spell | illusion | Sanctuary 1-40 pts for 5 secs on Self | 5 | `fathers-hand` |
| Sanctuary | spell | illusion | Sanctuary 10 pts for 30 secs on Self | 15 | `sanctuary` |
| Silence | spell | illusion | Silence for 5 secs on Target | 15 | `silence` |
| Far Silence | spell | illusion | Silence for 10 secs on Target | 30 | `far-silence` |
| Earwig | spell | illusion | Sound 3-8 pts for 5 secs on Target | 6 | `earwig` |
| Cruel Noise | spell | illusion | Sound 10-22 pts for 5 secs on Touch | 12 | `cruel-noise` |
| Dire Earwig | spell | illusion | Sound 8-15 pts for 5 secs on Target | 13 | `dire-earwig` |
| Wild Earwig | spell | illusion | Sound 1-30 pts for 5 secs on Target | 17 | `wild-earwig` |
| Dire Noise | spell | illusion | Sound 2-60 pts for 5 secs on Target | 35 | `dire-noise` |
| Absorb Agility | spell | mysticism | Absorb Agility 5-20 pts for 30 secs on Touch | 38 | `absorb-agility` |
| Absorb Endurance | spell | mysticism | Absorb Endurance 5-20 pts for 30 secs on Touch | 38 | `absorb-endurance` |
| Absorb Intelligence | spell | mysticism | Absorb Intelligence 5-20 pts for 30 secs on Touch | 38 (ours 161) | `absorb-intelligence` |
| Absorb Personality | spell | mysticism | Absorb Personality 5-20 pts for 30 secs on Touch | 38 | `absorb-personality` |
| Absorb Speed | spell | mysticism | Absorb Speed 5-20 pts for 30 secs on Touch | 38 | `absorb-speed` |
| Absorb Strength | spell | mysticism | Absorb Strength 5-20 pts for 30 secs on Touch | 38 (ours 161) | `absorb-strength` |
| Absorb Willpower | spell | mysticism | Absorb Willpower 5-20 pts for 30 secs on Touch | 38 | `absorb-willpower` |
| Absorb Speed [Ranged] | spell | mysticism | Absorb Speed 5-20 pts for 30 secs on Target | 56 | `absorb-speed-ranged` |
| Crimson Despair | spell | mysticism | Absorb Willpower 5-20 pts for 60 secs on Target | 113 | `crimson-despair` |
| Absorb Fatigue | spell | mysticism | Absorb Fatigue 5-20 pts for 30 secs on Touch | 75 | `absorb-fatigue` |
| Energy Leech | spell | mysticism | Absorb Fatigue 5-20 pts for 30 secs on Touch | 75 | `energy-leech` |
| Absorb Fatigue [Ranged] | spell | mysticism | Absorb Fatigue 5-20 pts for 30 secs on Target | 113 | `absorb-fatigue-ranged` |
| Righteousness | spell | mysticism | Absorb Health 10 pts on Touch | 4 | `righteousness` |
| Absorb Health | spell | mysticism | Absorb Health 5-52 pts on Touch | 11 | `absorb-health` |
| Almsivi Intervention | spell | mysticism | Almsivi Intervention on Self | 8 | `almsivi-intervention` |
| Demoralizing Touch | spell | mysticism | Demoralize Humanoid 5 pts for 10 secs on Touch | 3 | `demoralizing-touch` |
| Demoralize Humanoid | spell | mysticism | Demoralize Humanoid 5 pts for 10 secs on Target | 4 | `demoralize-humanoid` |
| Detect Creature | spell | mysticism | Detect Animal 50-150 pts for 5 secs on Self | 19 | `detect-creature` |
| Detect Enchantment | spell | mysticism | Detect Enchantment 10 pts for 10 secs on Self | 5 | `detect-enchantment` |
| Tevral's Hawkshaw | spell | mysticism | Detect Key 10 pts for 10 secs on Self | 5 | `tevrals-hawkshaw` |
| Detect Key | spell | mysticism | Detect Key 50 pts for 5 secs on Self | 13 | `detect-key` |
| Purge Magic | spell | mysticism | Dispel 5 pts on Target | 2 | `purge-magic` |
| Almalexia's Grace | spell | mysticism | Dispel 20 pts on Self | 5 | `almalexias-grace` |
| Dispel | spell | mysticism | Dispel 100 pts on Self | 25 | `dispel` |
| Divine Intervention | spell | mysticism | Divine Intervention on Self | 8 | `divine-intervention` |
| Mark | spell | mysticism | Mark on Self | 18 | `mark` |
| Recall | spell | mysticism | Recall on Self | 18 | `recall` |
| Sotha's Mirror | spell | mysticism | Reflect 10 pts for 5 secs on Self | 25 | `sothas-mirror` |
| Reflect | spell | mysticism | Reflect 10-20 pts for 5 secs on Self | 38 | `reflect` |
| Strong Reflect | spell | mysticism | Reflect 20-30 pts for 5 secs on Self | 63 | `strong-reflect` |
| Shalidor's Mirror | spell | mysticism | Reflect 10-30 pts for 10 secs on Self | 100 | `shalidors-mirror` |
| Wild Reflect | spell | mysticism | Reflect 1-40 pts for 10 secs on Self | 103 | `wild-reflect` |
| Llivam's Reversal | spell | mysticism | Reflect 20-30 pts for 10 secs on Self | 125 | `llivams-reversal` |
| Soul Trap | spell | mysticism | Soultrap for 60 secs on Touch | 6 | `soul-trap` |
| Spell Absorption | spell | mysticism | Spell Absorption 10 pts for 5 secs on Self | 25 | `spell-absorption` |
| Vivec's Feast | spell | mysticism | Spell Absorption 10 pts for 5 secs on Self | 25 | `vivecs-feast` |
| Weak Spelldrinker | spell | mysticism | Spell Absorption 10-20 pts for 5 secs on Self | 38 | `weak-spelldrinker` |
| Wild Spelldrinker | spell | mysticism | Spell Absorption 1-40 pts for 5 secs on Self | 51 | `wild-spelldrinker` |
| Strong Spelldrinker | spell | mysticism | Spell Absorption 20-30 pts for 5 secs on Self | 63 | `strong-spelldrinker` |
| Tranasa's Spelltrap | spell | mysticism | Spell Absorption 20-30 pts for 10 secs on Self | 125 | `tranasas-spelltrap` |
| Telekinesis | spell | mysticism | Telekinesis 25 pts for 5 secs on Self | 6 | `telekinesis` |
| Rilm's Gift | spell | restoration | Cure Common Disease on Touch; Cure Blight Disease on Touch | 30 | `rilms-gift` |
| Cure Blight Disease | spell | restoration | Cure Blight Disease on Self | 100 | `cure-blight-disease` |
| Vivec's Tears | spell | restoration | Cure Blight Disease on Self | 100 | `vivecs-tears` |
| Panacea | spell | restoration | Cure Poison on Self; Cure Common Disease on Self; Cure Blight Disease on Self | 120 | `panacea` |
| Vivec's Touch | spell | restoration | Cure Blight Disease on Touch; Cure Common Disease on Touch | 10 | `vivecs-touch` |
| Aryon's Blight Cure | spell | restoration | Cure Blight Disease in 2ft on Target | 30 | `aryons-blight-cure` |
| Cure Common Disease | spell | restoration | Cure Common Disease on Self | 15 | `cure-common-disease` |
| Cure Common Disease on Other | spell | restoration | Cure Common Disease on Touch | 15 | `cure-common-disease-on-other` |
| Rilm's Cure | spell | restoration | Cure Common Disease on Self | 15 | `rilms-cure` |
| Cure Common Disease Victim | spell | restoration | Cure Common Disease on Target | 23 | `cure-common-disease-victim` |
| Free Action | spell | restoration | Cure Paralyzation on Self | 5 | `free-action` |
| Balyna's Antidote | spell | restoration | Cure Poison on Self | 5 | `balynas-antidote` |
| Cure Poison | spell | restoration | Cure Poison on Self | 5 | `cure-poison` |
| Seryn's Gift | spell | restoration | Cure Poison on Touch | 5 | `seryns-gift` |
| Charisma | spell | restoration | Fortify Personality 10 pts for 60 secs on Self | 30 | `charisma` |
| Fortitude | spell | restoration | Fortify Endurance 10 pts for 60 secs on Self | 30 | `fortitude` |
| Iron Will | spell | restoration | Fortify Willpower 10 pts for 60 secs on Self | 30 | `iron-will` |
| Nimbleness | spell | restoration | Fortify Agility 10 pts for 60 secs on Self | 30 | `nimbleness` |
| Quicksilver | spell | restoration | Fortify Speed 10 pts for 60 secs on Self | 30 | `quicksilver` |
| Troll Strength | spell | restoration | Fortify Strength 10 pts for 60 secs on Self | 30 (ours 129) | `troll-strength` |
| Wisdom | spell | restoration | Fortify Intelligence 10 pts for 60 secs on Self | 30 (ours 129) | `wisdom` |
| Orc Strength | spell | restoration | Fortify Strength 5-20 pts for 60 secs on Self | 38 (ours 161) | `orc-strength` |
| Feet of Notorgo | spell | restoration | Fortify Speed 10 pts for 1 min, 30 secs on Self | 45 | `feet-of-notorgo` |
| Zenithar's Gospel | spell | restoration | Fortify Personality 10 pts for 1 min, 30 secs on Self | 45 | `zenithars-gospel` |
| Divine Aid | spell | restoration | Fortify Willpower 10 pts for 60 secs on Self; Fortify Luck 10 pts for 60 secs on Self (Luck left out: 1) | 60 | `divine-aid` |
| Daedric Willpower | spell | restoration | Fortify Willpower 20 pts for 1 min, 30 secs on Self | 90 | `daedric-willpower` |
| Enrichment | spell | restoration | Fortify Fatigue 5-20 pts for 30 secs on Self | 9 | `enrichment` |
| Vigor | spell | restoration | Fortify Fatigue 5-20 pts for 30 secs on Self | 9 | `vigor` |
| Daedric Fatigue | spell | restoration | Fortify Fatigue 50 pts for 1 min, 30 secs on Self | 113 | `daedric-fatigue` |
| Vitality | spell | restoration | Fortify Health 5-20 pts for 30 secs on Self | 19 | `vitality` |
| Blood Gift | spell | restoration | Fortify Health 10-40 pts for 30 secs on Self | 38 | `blood-gift` |
| Daedric Health | spell | restoration | Fortify Health 25 pts for 60 secs on Self | 75 | `daedric-health` |
| Powerwell | spell | restoration | Fortify Magicka 5-20 pts for 60 secs on Self | 38 | `powerwell` |
| Poet's Whim | spell | restoration | Resist Blight Disease 1-30 pts for 10 secs on Self | 39 | `poets-whim` |
| Vivec's Mercy | spell | restoration | Resist Blight Disease 20 pts for 10 secs on Self | 50 | `vivecs-mercy` |
| Shield of the Armiger | spell | restoration | Resist Blight Disease 30 pts for 10 secs on Self | 75 | `shield-of-the-armiger` |
| Resist Common Disease | spell | restoration | Resist Common Disease 10 pts for 5 secs on Self | 5 | `resist-common-disease` |
| Variable Resist Common Disease | spell | restoration | Resist Common Disease 1-30 pts for 10 secs on Self | 16 | `variable-resist-common-disease` |
| Seryn's Blessing | spell | restoration | Resist Common Disease 20 pts for 10 secs on Self | 20 | `seryns-blessing` |
| Great Resist Common Disease | spell | restoration | Resist Common Disease 30 pts for 10 secs on Self | 30 | `great-resist-common-disease` |
| Variable Resist Corprus Disease | spell | restoration | Resist Corprus Disease 1-30 pts for 10 secs on Self | 39 | `variable-resist-corprus-disease` |
| Strong Resist Corprus Disease | spell | restoration | Resist Corprus Disease 20 pts for 10 secs on Self | 50 | `strong-resist-corprus-disease` |
| Great Resist Corprus Disease | spell | restoration | Resist Corprus Disease 30 pts for 10 secs on Self | 75 | `great-resist-corprus-disease` |
| Resist Fire | spell | restoration | Resist Fire 10 pts for 5 secs on Self | 5 | `resist-fire` |
| Variable Resist Fire | spell | restoration | Resist Fire 1-30 pts for 10 secs on Self | 16 | `variable-resist-fire` |
| Strong Resist Fire | spell | restoration | Resist Fire 20 pts for 10 secs on Self | 20 | `strong-resist-fire` |
| Great Resist Fire | spell | restoration | Resist Fire 30 pts for 10 secs on Self | 30 | `great-resist-fire` |
| Flameguard | spell | restoration | Resist Fire 20-40 pts for 30 secs on Self | 90 | `flameguard` |
| Resist Frost | spell | restoration | Resist Frost 10 pts for 5 secs on Self | 5 | `resist-frost` |
| Variable Resist Frost | spell | restoration | Resist Frost 1-30 pts for 10 secs on Self | 16 | `variable-resist-frost` |
| Strong Resist Frost | spell | restoration | Resist Frost 20 pts for 10 secs on Self | 20 | `strong-resist-frost` |
| Great Resist Frost | spell | restoration | Resist Frost 30 pts for 10 secs on Self | 30 | `great-resist-frost` |
| Frostguard | spell | restoration | Resist Frost 20-40 pts for 30 secs on Self | 90 | `frostguard` |
| Resist Magicka | spell | restoration | Resist Magicka 10 pts for 5 secs on Self | 5 | `resist-magicka` |
| Variable Resist Magicka | spell | restoration | Resist Magicka 1-30 pts for 10 secs on Self | 16 | `variable-resist-magicka` |
| Strong Resist Magicka | spell | restoration | Resist Magicka 20 pts for 10 secs on Self | 20 | `strong-resist-magicka` |
| Great Resist Magicka | spell | restoration | Resist Magicka 30 pts for 10 secs on Self | 30 | `great-resist-magicka` |
| Magickguard | spell | restoration | Resist Magicka 20-40 pts for 10 secs on Self | 30 | `magickguard` |
| Resist Paralysis | spell | restoration | Resist Paralysis 50 pts for 30 secs on Self | 300 | `resist-paralysis` |
| Resist Poison | spell | restoration | Resist Poison 20 pts for 5 secs on Self | 10 | `resist-poison` |
| Variable Resist Poison | spell | restoration | Resist Poison 1-30 pts for 10 secs on Self | 16 | `variable-resist-poison` |
| Strong Resist Poison | spell | restoration | Resist Poison 20 pts for 10 secs on Self | 20 | `strong-resist-poison` |
| Greater Resist Poison | spell | restoration | Resist Poison 30 pts for 10 secs on Self | 30 | `greater-resist-poison` |
| Poisonguard | spell | restoration | Resist Poison 20-40 pts for 30 secs on Self | 90 | `poisonguard` |
| Resist Shock | spell | restoration | Resist Shock 20 pts for 5 secs on Self | 10 | `resist-shock` |
| Variable Resist Shock | spell | restoration | Resist Shock 1-30 pts for 10 secs on Self | 16 | `variable-resist-shock` |
| Strong Resist Shock | spell | restoration | Resist Shock 20 pts for 10 secs on Self | 20 | `strong-resist-shock` |
| Shockguard | spell | restoration | Resist Shock 20-40 pts for 30 secs on Self | 90 | `shockguard` |
| Ogrul's Quick-Again | spell | restoration | Restore Speed 10 pts on Self | 1 | `ogruls-quick-again` |
| Ogrul's Staunch-Again | spell | restoration | Restore Willpower 10 pts on Self | 1 | `ogruls-staunch-again` |
| Ogrul's Strong-Again | spell | restoration | Restore Strength 10 pts on Self | 1 | `ogruls-strong-again` |
| Restore Agility | spell | restoration | Restore Agility 5-20 pts for 30 secs on Self | 19 | `restore-agility` |
| Restore Endurance | spell | restoration | Restore Endurance 5-20 pts for 30 secs on Self | 19 | `restore-endurance` |
| Restore Intelligence | spell | restoration | Restore Intelligence 5-20 pts for 30 secs on Self | 19 | `restore-intelligence` |
| Restore Personality | spell | restoration | Restore Personality 5-20 pts for 30 secs on Self | 19 | `restore-personality` |
| Restore Speed | spell | restoration | Restore Speed 5-20 pts for 30 secs on Self | 19 | `restore-speed` |
| Restore Strength | spell | restoration | Restore Strength 5-20 pts for 30 secs on Self | 19 | `restore-strength` |
| Restore Willpower | spell | restoration | Restore Willpower 5-20 pts for 30 secs on Self | 19 | `restore-willpower` |
| Rest of St. Merris | spell | restoration | Restore Fatigue 1-10 pts for 20 secs on Self | 6 | `rest-of-st-merris` |
| Stamina | spell | restoration | Restore Fatigue 10-30 pts for 30 secs on Self | 30 | `stamina` |
| Balyna's Soothing Balm | spell | restoration | Restore Health 3-12 pts on Self | 2 | `balynas-soothing-balm` |
| Balyna's Efficacious Balm | spell | restoration | Restore Health 3-22 pts on Self | 3 | `balynas-efficacious-balm` |
| Veloth's Benison | spell | restoration | Restore Health 10 pts on Self | 3 | `veloths-benison` |
| Heal Companion | spell | restoration | Restore Health 6-15 pts on Touch | 3 | `heal-companion` |
| Balyna's Perfect Balm | spell | restoration | Restore Health 3-30 pts on Self | 4 | `balynas-perfect-balm` |
| Mother's Kiss | spell | restoration | Restore Health 10-20 pts on Self | 4 | `mothers-kiss` |
| Veloth's Grace | spell | restoration | Restore Health 10 pts for 2 secs on Self | 5 | `veloths-grace` |
| Hearth Heal | spell | restoration | Restore Health 20-80 pts on Self | 13 | `hearth-heal` |
| Regenerate | spell | restoration | Restore Health 1-5 pts for 20 secs on Self | 15 | `regenerate` |
| Rapid Regenerate | spell | restoration | Restore Health 5-10 pts for 20 secs on Self | 38 | `rapid-regenerate` |
| Adrenaline Rush | power | restoration | Fortify Agility 50 pts for 60 secs on Self; Fortify Strength 50 pts for 60 secs on Self; Fortify Speed 50 pts for 60 secs on Self; Fortify Endurance 50 pts for 60 secs on Self; Fortify Health 25 pts for 60 secs on Self | ours 0 | `adrenaline-rush` |
| Almalexia's Light (Tribunal) | power | restoration | Restore Agility 25 pts on Self; Restore Endurance 25 pts on Self; Restore Intelligence 25 pts on Self; Restore Luck 25 pts on Self; Restore Personality 25 pts on Self; Restore Speed 25 pts on Self; Restore Strength 25 pts on Self; Restore Willpower 25 pts on Self (Luck left out: 1) | ours 0 | `almalexias-light` |
| Ancestor Guardian | power | illusion | Sanctuary 50 pts for 60 secs on Self | ours 0 | `ancestor-guardian` |
| Beast Tongue | power | conjuration | Command Creature 5 pts for 10 mins on Target | ours 0 | `beast-tongue` |
| Berserk | power | restoration | Fortify Health 20 pts for 60 secs on Self; Fortify Fatigue 200 pts for 60 secs on Self; Fortify Attack 100 pts for 60 secs on Self; Drain Agility 100 pts for 60 secs on Self | ours 0 | `berserk` |
| Burning Hand | power | destruction | Fire Damage 50 pts on Target | ours 0 | `burning-hand` |
| Dragon Skin | power | alteration | Shield 50 pts for 60 secs on Self | ours 0 | `dragon-skin` |
| Eye of Fear | power | illusion | Demoralize Humanoid 100 pts for 30 secs on Target | ours 0 | `eye-of-fear` |
| Grace of Almsivi (Tribunal) | power | restoration | Restore Health 30-80 pts on Self; Restore Fatigue 60-100 pts on Self; Cure Common Disease on Self | ours 0 | `grace-of-almsivi` |
| Hunter's Wind (Bloodmoon) | power | restoration | Restore Health 1000 pts on Self | ours 0 | `hunters-wind` |
| Lover's Kiss | power | illusion | Paralyze for 60 secs on Target; Damage Fatigue 200 pts on Self | ours 0 | `lovers-kiss` |
| Mara's Gift | power | restoration | Restore Health 100 pts on Self | ours 0 | `maras-gift` |
| Moonshadow | power | illusion | Invisibility for 60 secs on Self | ours 0 | `moonshadow` |
| Star of the West | power | mysticism | Absorb Fatigue 200 pts on Target | ours 0 | `star-of-the-west` |
| Thunder Fist | power | destruction | Frost Damage 25 pts on Touch | ours 0 | `thunder-fist` |
| Tower Key | power | alteration | Open 50 pts on Touch | ours 0 | `tower-key` |
| Voice of the Emperor | power | illusion | Charm 25-50 pts for 15 secs on Target | ours 0 | `voice-of-the-emperor` |
| Wizard's Brand | power | destruction | Shock Damage 50 pts in 12ft on Touch | ours 0 | `wizards-brand` |
| Woad | power | alteration | Shield 30 pts for 60 secs on Self | ours 0 | `woad` |
| Aryon's Rest | spell | alteration | Damage Fatigue 10 pts for 10 secs on Target; Burden 10 pts for 10 secs on Target | 38 | `aryons-rest` |
| Burden Touch | spell | alteration | Burden 20 pts for 10 secs on Touch | 10 | `burden-touch` |
| Fields of Kummu Blessing | spell | alteration | Feather 100 pts for 48 mins on Touch | 0 | `fields-of-kummu-blessing` |
| Fierce Fire Shield | spell | alteration | Fire Shield 5-11 pts for 10 secs on Self | 12 | `fierce-fire-shield` |
| Fierce Frost Shield | spell | alteration | Frost Shield 5-11 pts for 10 secs on Self | 12 | `fierce-frost-shield` |
| Fierce Shock Shield | spell | alteration | Lightning Shield 5-11 pts for 10 secs on Self | 12 | `fierce-shock-shield` |
| Ghostgate Shrine Blessing | spell | alteration | Fortify Magicka 50 pts for 48 mins on Touch; Shield 25 pts for 48 mins on Touch | 14400 | `ghostgate-shrine-blessing` |
| Great Levitate | spell | alteration | Levitate 30 pts for 10 secs on Self | 45 | `great-levitate` |
| Great Open | spell | alteration | Open 50 pts on Touch | 15 | `great-open` |
| Hand of Odros | spell | alteration | Damage Fatigue 60 pts on Touch; Absorb Agility 3-6 pts for 2 mins on Touch; Burden 30-40 pts for 60 secs on Touch | 342 | `hand-of-odros` |
| Jump | spell | alteration | Jump 5 pts for 10 secs on Self | 8 | `jump` |
| Lock | spell | alteration | Lock 5 pts on Touch | 1 | `lock` |
| Puzzle Canal Blessings | spell | alteration | Water Breathing for 48 mins on Touch; Swift Swim 25 pts for 48 mins on Touch | 7632 | `puzzle-canal-blessings` |
| Shock Shield | spell | alteration | Lightning Shield 3 pts for 20 secs on Self | 9 | `shock-shield` |
| Stop the Moon Blessings | spell | alteration | Levitate 100 pts for 24 mins on Touch | 0 | `stop-the-moon-blessings` |
| Vampire Fly | spell | alteration | Levitate 30-70 pts for 15 secs on Self | 25 | `vampire-fly` |
| Warding Touch | spell | alteration | Shield 20-40 pts for 4 mins on Target | 1 | `warding-touch` |
| Water Breathing | spell | alteration | Water Breathing for 2 mins on Self | 5 | `argonian-breathing` |
| Wrath of Odros | spell | alteration | Damage Fatigue 60 pts on Target; Absorb Agility 3 pts for 2 mins on Target; Burden 20-30 pts for 50 secs on Target | 332 | `wrath-of-odros` |
| Blessed Word | spell | conjuration | Turn Undead 100 pts for 30 secs on Target | 10 | `blessed-word` |
| Bone Guard | spell | conjuration | Summon Skeletal Minion for 10 secs on Self | 7 | `bone-guard` |
| Command Beast | spell | conjuration | Command Creature 5 pts for 60 secs on Touch | 225 | `command-beast` |
| Ghost Guard | spell | conjuration | Summon Ancestral Ghost for 30 secs on Self | 11 | `ghost-guard` |
| Hand of Endus | spell | conjuration | Summon Flame Atronach for 1 min, 30 secs on Self; Summon Storm Atronach for 1 min, 30 secs on Self; Disintegrate Armor 30 pts for 3 secs on Touch; Disintegrate Weapon 30 pts for 3 secs on Touch | 468 | `hand-of-endus` |
| Summon Hrelvesuu | spell | conjuration | Summon Daedroth for 10 mins on Self | 3900 | `summon-hrelvesuu` |
| Wrath of Endus | spell | conjuration | Summon Flame Atronach for 1 min, 30 secs on Self; Summon Storm Atronach for 1 min, 30 secs on Self; Disintegrate Armor 10-20 pts for 3 secs on Target; Disintegrate Weapon 20-30 pts for 3 secs on Target | 468 | `wrath-of-endus` |
| Alit Bite | spell | destruction | Poison 1-2 pts for 5 secs on Touch | 3 | `alit-bite` |
| Ash Curse: Fatigue | spell | destruction | Damage Fatigue 10-20 pts on Touch; Corprus on Self | 128 | `ash-curse-fatigue` |
| Ash Curse: Health | spell | destruction | Damage Health 10-20 pts on Touch; Corprus on Self | 131 | `ash-curse-health` |
| Ash Curse: Spell Points | spell | destruction | Damage Magicka 10-20 pts on Touch; Corprus on Self | 131 | `ash-curse-spell-points` |
| Ash Feast | spell | destruction | Drain Health 3 pts for 30 secs on Touch | 18 | `ash-feast` |
| Blessings of the Fourth Corner | spell | destruction | Fortify Intelligence 1-25 pts for 24 mins on Touch; Fortify Luck 1-25 pts for 24 mins on Touch; Fortify Personality 1-25 pts for 24 mins on Touch; Fortify Willpower 1-25 pts for 240 mins on Touch; Drain Intelligence 1-25 pts for 24 mins on Touch; Drain Luck 1-25 pts for 24 mins on Touch; Drain Personality 1-25 pts for 24 mins on Touch; Drain Willpower 1-25 pts for 24 mins on Touch (Luck left out: 2) | 23868 (ours 17129) | `blessings-of-the-fourth-corner` |
| Blood Sacrifice | spell | destruction | Damage Health 10-40 pts on Touch | 10 | `blood-sacrifice` |
| Burning Touch | spell | destruction | Fire Damage 1-25 pts on Touch | 3 | `burning-touch` |
| Clumsiness | spell | destruction | Drain Agility 5-20 pts for 30 secs on Target | 28 | `clumsiness` |
| Curse Agility | spell | destruction | Drain Agility 2-4 pts for 30 secs on Touch | 5 | `curse-agility` |
| Curse Endurance | spell | destruction | Drain Endurance 2-4 pts for 30 secs on Target | 7 | `curse-endurance` |
| Curse Fatigue | spell | destruction | Damage Fatigue 2-4 pts for 5 secs on Touch | 3 | `curse-fatigue` |
| Curse Health | spell | destruction | Drain Health 2-4 pts for 5 secs on Touch | 3 | `curse-health` |
| Curse Intelligence | spell | destruction | Drain Intelligence 2-4 pts for 30 secs on Touch | 5 | `curse-intelligence` |
| Curse Personality | spell | destruction | Drain Personality 2-4 pts for 30 secs on Touch | 5 | `curse-personality` |
| Curse Speed | spell | destruction | Drain Speed 2-4 pts for 30 secs on Touch | 5 | `curse-speed` |
| Curse Spell Points | spell | destruction | Damage Magicka 2-4 pts for 5 secs on Touch | 6 | `curse-spell-points` |
| Curse Strength | spell | destruction | Drain Strength 2-4 pts for 30 secs on Touch | 5 | `curse-strength` |
| Curse Willpower | spell | destruction | Drain Willpower 2-4 pts for 30 secs on Touch | 5 | `curse-willpower` |
| Dagoth's Bosom | spell | destruction | Drain Fatigue 20 pts for 30 secs on Target | 90 | `dagoths-bosom` |
| Deadly Poison [Ranged] | spell | destruction | Poison 1-20 pts for 10 secs on Target | 71 | `deadly-poison-ranged` |
| Dire Viper | spell | destruction | Poison 5-7 pts for 5 secs on Touch | 0 | `dire-viper` |
| Disintegrate Armor | spell | destruction | Disintegrate Armor 6-25 pts on Target | 7 | `disintegrate-armor` |
| Disintegrate Weapon | spell | destruction | Disintegrate Weapon 6-25 pts on Target | 7 | `disintegrate-weapon` |
| Drain Acrobatics | spell | destruction | Drain Acrobatics 5-20 pts for 60 secs on Target | 56 | `drain-acrobatics` |
| Drain Alchemy | spell | destruction | Drain Alchemy 5-20 pts for 60 secs on Target | 56 | `drain-alchemy` |
| Drain Alteration | spell | destruction | Drain Alteration 5-20 pts for 60 secs on Target | 56 | `drain-alteration` |
| Drain Armorer | spell | destruction | Drain Armorer 5-20 pts for 60 secs on Target | 56 | `drain-armorer` |
| Drain Axe | spell | destruction | Drain Axe 5-20 pts for 60 secs on Target | 56 | `drain-axe` |
| Drain Blunt Weapon | spell | destruction | Drain Blunt Weapon 5-20 pts for 60 secs on Target | 56 | `drain-blunt-weapon` |
| Drain Conjuration | spell | destruction | Drain Conjuration 5-20 pts for 60 secs on Target | 56 | `drain-conjuration` |
| Drain Enchant | spell | destruction | Drain Enchant 5-20 pts for 60 secs on Target | 56 | `drain-enchant` |
| Drain Hand-to-Hand | spell | destruction | Drain Hand-to-hand 5-20 pts for 60 secs on Target | 56 | `drain-hand-to-hand` |
| Drain Heavy Armor | spell | destruction | Drain Heavy Armor 5-20 pts for 60 secs on Target | 56 | `drain-heavy-armor` |
| Drain Illusion | spell | destruction | Drain Illusion 5-20 pts for 60 secs on Target | 56 | `drain-illusion` |
| Drain Light Armor | spell | destruction | Drain Light Armor 5-20 pts for 60 secs on Target | 56 | `drain-light-armor` |
| Drain Long Blade | spell | destruction | Drain Long Blade 5-20 pts for 60 secs on Target | 56 | `drain-long-blade` |
| Drain Marksman | spell | destruction | Drain Marksman 5-20 pts for 60 secs on Target | 56 | `drain-marksman` |
| Drain Medium Armor | spell | destruction | Drain Medium Armor 5-20 pts for 60 secs on Target | 56 | `drain-medium-armor` |
| Drain Mercantile | spell | destruction | Drain Mercantile 5-20 pts for 60 secs on Target | 56 | `drain-mercantile` |
| Drain Mysticism | spell | destruction | Drain Mysticism 5-20 pts for 60 secs on Target | 56 | `drain-mysticism` |
| Drain Restoration | spell | destruction | Drain Restoration 5-20 pts for 60 secs on Target | 56 | `drain-restoration` |
| Drain Security | spell | destruction | Drain Security 5-20 pts for 60 secs on Target | 56 | `drain-security` |
| Drain Short Blade | spell | destruction | Drain Short Blade 5-20 pts for 60 secs on Target | 56 | `drain-short-blade` |
| Drain Sneak | spell | destruction | Drain Sneak 5-20 pts for 60 secs on Target | 56 | `drain-sneak` |
| Drain Spear | spell | destruction | Drain Spear 5-20 pts for 60 secs on Target | 56 | `drain-spear` |
| Drain Speechcraft | spell | destruction | Drain Speechcraft 5-20 pts for 60 secs on Target | 56 | `drain-speechcraft` |
| Drain Unarmored | spell | destruction | Drain Unarmored 5-20 pts for 60 secs on Target | 56 | `drain-unarmored` |
| Dratha's Spite | spell | destruction | Damage Agility 2-4 pts for 10 secs on Target; Damage Health 5-10 pts for 10 secs on Target | 63 | `drathas-spite` |
| Dread Curse: Agility | spell | destruction | Damage Agility 5-12 pts on Target | 5 | `dread-curse-agility` |
| Dread Curse: Endurance | spell | destruction | Damage Endurance 5-12 pts on Touch | 3 | `dread-curse-endurance` |
| Dread Curse: Fatigue | spell | destruction | Damage Fatigue 5-12 pts on Touch | 2 | `dread-curse-fatigue` |
| Dread Curse: Health | spell | destruction | Damage Health 5-12 pts on Touch | 3 | `dread-curse-health` |
| Dread Curse: Intelligence | spell | destruction | Damage Intelligence 5-12 pts on Touch | 3 | `dread-curse-intelligence` |
| Dread Curse: Personality | spell | destruction | Damage Personality 5-12 pts on Touch | 3 | `dread-curse-personality` |
| Dread Curse: Speed | spell | destruction | Damage Speed 5-12 pts on Touch | 3 | `dread-curse-speed` |
| Dread Curse: Spell Points | spell | destruction | Damage Magicka 5-12 pts on Touch | 3 | `dread-curse-spell-points` |
| Dread Curse: Strength | spell | destruction | Damage Strength 5-12 pts on Touch | 3 | `dread-curse-strength` |
| Dread Curse: Willpower | spell | destruction | Damage Willpower 5-12 pts on Touch | 3 | `dread-curse-willpower` |
| Electrical Discharge | spell | destruction | Shock Damage 50-150 pts in 5ft on Touch | 108 | `electrical-discharge` |
| Enervating Touch | spell | destruction | Drain Endurance 5-20 pts for 30 secs on Touch | 19 | `enervating-touch` |
| Exhaustion | spell | destruction | Drain Fatigue 5-20 pts for 1 min, 30 secs on Target | 169 | `exhaustion` |
| Fire Trap | spell | destruction | Fire Damage 2-20 pts for 3 secs on Touch | 3 | `fire-trap` |
| Firebloom | spell | destruction | Fire Damage 1-25 pts in 10ft for 5 secs on Target | 26 | `firebloom` |
| Firefist | spell | destruction | Damage Health 10-24 pts on Touch; Fire Damage 10-24 pts on Touch | 11 | `firefist` |
| Five Fingers of Pain | spell | destruction | Damage Health 3-5 pts on Touch; Fire Damage 3-5 pts on Touch; Frost Damage 3-5 pts on Touch; Shock Damage 3-5 pts on Touch; Demoralize Humanoid 3-5 pts on Touch | 5 | `five-fingers-of-pain` |
| Flame | spell | destruction | Fire Damage 1-15 pts on Touch | 2 | `flame` |
| Flamebolt | spell | destruction | Fire Damage 10-50 pts in 10ft for 2 secs on Target | 24 | `flamebolt` |
| Flay Spirit [Ranged] | spell | destruction | Drain Magicka 5-20 pts for 60 secs on Target | 225 | `flay-spirit-ranged` |
| Force Bolt | spell | destruction | Drain Health 5-20 pts for 30 secs on Target; Paralyze for 4 secs on Target | 125 | `force-bolt` |
| Freezing Touch | spell | destruction | Frost Damage 15-30 pts on Touch | 6 | `freezing-touch` |
| Frost Bolt | spell | destruction | Frost Damage 10-50 pts in 10ft for 2 secs on Target | 24 | `frost-bolt` |
| Frost Trap | spell | destruction | Frost Damage 2-20 pts for 3 secs on Touch | 3 | `frost-trap` |
| Frostball | spell | destruction | Frost Damage 2-20 pts in 5ft on Target | 5 | `frostball` |
| Frostbloom | spell | destruction | Frost Damage 1-25 pts in 10ft for 5 secs on Target | 26 | `frostbloom` |
| Frostfist | spell | destruction | Damage Health 10-24 pts on Touch; Frost Damage 10-24 pts on Touch | 11 | `frostfist` |
| Ghost Curse | spell | destruction | Drain Endurance 5 pts for 30 secs on Touch; Drain Fatigue 10 pts for 30 secs on Touch; Damage Health 1-10 pts on Touch | 40 | `ghost-curse` |
| Ghost Snake | spell | destruction | Paralyze for 3 secs on Target; Drain Strength 3-7 pts for 3 secs on Target; Drain Endurance 3-7 pts for 3 secs on Target; Drain Fatigue 9-21 pts for 3 secs on Target | 9 | `ghost-snake` |
| Glyph of Weakness | spell | destruction | Damage Endurance 10-25 pts in 5ft for 2 secs on Touch | 30 | `glyph-of-weakness` |
| God's Spark | spell | destruction | Shock Damage 5-50 pts in 10ft for 10 secs on Target | 147 | `gods-spark` |
| Gothren's Gout | spell | destruction | Paralyze for 5 secs on Touch; Fire Damage 2 pts for 5 secs on Touch; Frost Damage 2 pts for 5 secs on Touch; Shock Damage 2 pts for 5 secs on Touch; Poison 2 pts for 5 secs on Touch | 23 | `gothrens-gout` |
| Grave Curse: Agilitiy | spell | destruction | Drain Agility 2-4 pts for 60 secs on Target | 14 | `grave-curse-agilitiy` |
| Grave Curse: Endurance | spell | destruction | Drain Endurance 2-4 pts for 60 secs on Target | 14 | `grave-curse-endurance` |
| Grave Curse: Fatigue | spell | destruction | Damage Fatigue 2-4 pts for 10 secs on Target | 9 | `grave-curse-fatigue` |
| Grave Curse: Health | spell | destruction | Damage Health 1-4 pts for 10 secs on Target | 15 | `grave-curse-health` |
| Grave Curse: Intelligence | spell | destruction | Drain Intelligence 2-4 pts for 60 secs on Target | 14 | `grave-curse-intelligence` |
| Grave Curse: Magicka | spell | destruction | Damage Magicka 2-4 pts for 10 secs on Target | 18 | `grave-curse-magicka` |
| Grave Curse: Personality | spell | destruction | Drain Personality 2-4 pts for 60 secs on Target | 14 | `grave-curse-personality` |
| Grave Curse: Speed | spell | destruction | Drain Speed 2-4 pts for 60 secs on Target | 14 | `grave-curse-speed` |
| Grave Curse: Strength | spell | destruction | Drain Strength 2-4 pts for 60 secs on Target | 14 | `grave-curse-strength` |
| Grave Curse: Willpower | spell | destruction | Drain Willpower 2-4 pts for 60 secs on Target | 14 | `grave-curse-willpower` |
| Gripes | spell | destruction | Damage Endurance 1-20 pts on Touch | 4 | `gripes` |
| Hand of Araynys | spell | destruction | Damage Health 20-30 pts on Touch; Damage Fatigue 20-30 pts on Touch; Damage Agility 20-30 pts on Touch; Damage Speed 20-30 pts on Touch | 70 | `hand-of-araynys` |
| Hand of Dagoth | spell | destruction | Damage Health 25-75 pts on Touch; Damage Fatigue 25-75 pts on Touch; Damage Agility 5 pts on Touch; Damage Endurance 5 pts on Touch; Damage Speed 5 pts on Touch; Damage Strength 5 pts on Touch; Damage Willpower 5 pts on Touch; Damage Luck 5 pts on Touch (Luck left out: 1) | 39 | `hand-of-dagoth` |
| Hand of Decay | spell | destruction | Drain Health 1-100 pts on Touch | 20 | `hand-of-decay` |
| Hand of Gilvoth | spell | destruction | Damage Health 20-30 pts on Touch; Damage Fatigue 20-30 pts on Touch; Damage Intelligence 20-30 pts on Touch; Damage Willpower 20-30 pts on Touch | 70 | `hand-of-gilvoth` |
| Hand of Sleep | spell | destruction | Drain Fatigue 5-20 pts for 30 secs on Touch | 75 | `hand-of-sleep` |
| Hand of Tureynul | spell | destruction | Damage Fatigue 50 pts on Touch; Damage Strength 20-30 pts on Touch; Damage Endurance 20-30 pts on Touch | 60 | `hand-of-tureynul` |
| Hand of Uthol | spell | destruction | Absorb Agility 2-4 pts for 2 mins on Touch; Damage Fatigue 20-30 pts for 3 secs on Touch | 102 | `hand-of-uthol` |
| Hand of Vemyn | spell | destruction | Damage Health 10-30 pts on Touch; Damage Fatigue 20-30 pts for 3 secs on Touch; Absorb Strength 3-6 pts for 2 mins on Touch | 154 (ours 255) | `hand-of-vemyn` |
| Hand of Vivec | spell | destruction | Damage Health 50 pts for 3 secs on Touch; Fire Damage 50 pts for 3 secs on Touch; Frost Damage 50 pts for 3 secs on Touch; Shock Damage 50 pts for 3 secs on Touch | 188 | `hand-of-vivec` |
| Ironhand | spell | destruction | Damage Fatigue 21-42 pts on Touch | 6 | `ironhand` |
| Knuckle Luck | spell | destruction | Damage Fatigue 3-120 pts on Touch | 12 | `knuckle-luck` |
| Kwama Poison | spell | destruction | Poison 1-3 pts for 40 secs on Touch | 12 | `kwama-poison` |
| Lifeforce Trap | spell | destruction | Damage Health 2-20 pts for 3 secs on Touch | 8 | `lifeforce-trap` |
| Lustidrike Cocktail | spell | destruction | Fortify Strength 5 pts for 30 secs on Target; Drain Intelligence 5 pts for 30 secs on Target | 23 (ours 60) | `lustidrike-cocktail` |
| Poison Trap | spell | destruction | Poison 1-5 pts for 60 secs on Touch | 16 | `poison-trap` |
| Potent Poison [Ranged] | spell | destruction | Poison 20-40 pts for 5 secs on Target | 101 | `potent-poison-ranged` |
| Shalk's Fire Bite | spell | destruction | Fire Damage 3-6 pts in 5ft on Touch | 5 | `shalks-fire-bite` |
| Shard | spell | destruction | Frost Damage 2-20 pts in 5ft on Target | 5 | `shard` |
| Shock Trap | spell | destruction | Shock Damage 2-20 pts for 3 secs on Touch | 5 | `shock-trap` |
| Shockbite | spell | destruction | Shock Damage 35-45 pts for 2 secs on Touch | 28 | `shockbite` |
| Shocking Touch | spell | destruction | Shock Damage 3-30 pts on Touch | 6 | `shocking-touch` |
| Smite the Ungodly | spell | destruction | Shock Damage 1-50 pts on Target | 13 | `smite-the-ungodly` |
| Spell Drain | spell | destruction | Drain Magicka 10-30 pts for 30 secs on Target | 180 | `spell-drain` |
| Sphere of Negation | spell | destruction | Drain Health 15-26 pts in 10ft on Target | 8 | `sphere-of-negation` |
| Spite Touch | spell | destruction | Drain Personality 5-20 pts for 30 secs on Touch | 19 | `spite-touch` |
| Star-Curse | spell | destruction | Poison 3 pts for 30 secs on Touch; Damage Health 1 pt for 30 secs on Self | 5 | `star-curse` |
| Sting | spell | destruction | Poison 1-25 pts on Touch | 6 | `sting` |
| Strain | spell | destruction | Drain Agility 5-20 pts for 30 secs on Target | 28 | `strain` |
| Straining Touch | spell | destruction | Drain Agility 5-20 pts for 30 secs on Touch | 19 | `straining-touch` |
| Tempting Touch | spell | destruction | Drain Willpower 5-20 pts for 30 secs on Touch | 19 | `tempting-touch` |
| Torpor Touch | spell | destruction | Drain Speed 5-20 pts for 30 secs on Touch | 19 | `torpor-touch` |
| TouchDrain Acrobatics | spell | destruction | Drain Acrobatics 5-20 pts for 30 secs on Touch | 19 | `touchdrain-acrobatics` |
| TouchDrain Alchemy | spell | destruction | Drain Alchemy 5-20 pts for 30 secs on Touch | 19 | `touchdrain-alchemy` |
| TouchDrain Alteration | spell | destruction | Drain Alteration 5-20 pts for 30 secs on Touch | 19 | `touchdrain-alteration` |
| TouchDrain Armorer | spell | destruction | Drain Armorer 5-20 pts for 30 secs on Touch | 19 | `touchdrain-armorer` |
| TouchDrain Athletics | spell | destruction | Drain Athletics 5-20 pts for 30 secs on Touch | 19 | `touchdrain-athletics` |
| TouchDrain Axe | spell | destruction | Drain Axe 5-20 pts for 30 secs on Touch | 19 | `touchdrain-axe` |
| TouchDrain Block | spell | destruction | Drain Block 5-20 pts for 30 secs on Touch | 19 | `touchdrain-block` |
| TouchDrain Blunt Weapon | spell | destruction | Drain Blunt Weapon 5-20 pts for 30 secs on Touch | 19 | `touchdrain-blunt-weapon` |
| TouchDrain Conjuration | spell | destruction | Drain Conjuration 5-20 pts for 30 secs on Touch | 19 | `touchdrain-conjuration` |
| TouchDrain Destruction | spell | destruction | Drain Destruction 5-20 pts for 30 secs on Touch | 19 | `touchdrain-destruction` |
| TouchDrain Enchant | spell | destruction | Drain Enchant 5-20 pts for 30 secs on Touch | 19 | `touchdrain-enchant` |
| TouchDrain Hand to Hand | spell | destruction | Drain Hand To Hand 5-20 pts for 30 secs on Touch | 19 | `touchdrain-hand-to-hand` |
| TouchDrain Heavy Armor | spell | destruction | Drain Heavy Armor 5-20 pts for 30 secs on Touch | 19 | `touchdrain-heavy-armor` |
| TouchDrain Illusion | spell | destruction | Drain Illusion 5-20 pts for 30 secs on Touch | 19 | `touchdrain-illusion` |
| TouchDrain Light Armor | spell | destruction | Drain Light Armor 5-20 pts for 30 secs on Touch | 19 | `touchdrain-light-armor` |
| TouchDrain Long Blade | spell | destruction | Drain Long Blade 5-20 pts for 30 secs on Touch | 19 | `touchdrain-long-blade` |
| TouchDrain Marksman | spell | destruction | Drain Marksman 5-20 pts for 30 secs on Touch | 19 | `touchdrain-marksman` |
| TouchDrain Medium Armor | spell | destruction | Drain Medium Armor 5-20 pts for 30 secs on Touch | 19 | `touchdrain-medium-armor` |
| TouchDrain Mercantile | spell | destruction | Drain Mercantile 5-20 pts for 30 secs on Touch | 19 | `touchdrain-mercantile` |
| TouchDrain Mysticism | spell | destruction | Drain Mysticism 5-20 pts for 30 secs on Touch | 19 | `touchdrain-mysticism` |
| TouchDrain Restoration | spell | destruction | Drain Restoration 5-20 pts for 30 secs on Touch | 19 | `touchdrain-restoration` |
| TouchDrain Security | spell | destruction | Drain Security 5-20 pts for 30 secs on Touch | 19 | `touchdrain-security` |
| TouchDrain Short Blade | spell | destruction | Drain Short Blade 5-20 pts for 30 secs on Touch | 19 | `touchdrain-short-blade` |
| TouchDrain Sneak | spell | destruction | Drain Sneak 5-20 pts for 30 secs on Touch | 19 | `touchdrain-sneak` |
| TouchDrain Spear | spell | destruction | Drain Spear 5-20 pts for 30 secs on Touch | 19 | `touchdrain-spear` |
| TouchDrain Speechcraft | spell | destruction | Drain Speechcraft 5-20 pts for 30 secs on Touch | 19 | `touchdrain-speechcraft` |
| TouchDrain Unarmored | spell | destruction | Drain Unarmored 5-20 pts for 30 secs on Touch | 19 | `touchdrain-unarmored` |
| Vampire's Kiss | spell | destruction | Damage Health 1-10 pts on Touch; Restore Health 1-10 pts on Self | 4 | `vampires-kiss` |
| Viper | spell | destruction | Poison 2-8 pts on Touch | 2 | `viper` |
| Viperbite | spell | destruction | Poison 1-30 pts on Touch | 7 | `viperbite` |
| Vivec's Wrath | spell | destruction | Damage Health 10-20 pts on Target; Fire Damage 10-20 pts on Target; Frost Damage 10-20 pts on Target; Shock Damage 10-20 pts on Target | 28 | `vivecs-wrath` |
| Weakening Touch | spell | destruction | Drain Strength 5-20 pts for 30 secs on Touch | 19 | `weakening-touch` |
| Weakness | spell | destruction | Drain Strength 5-20 pts for 30 secs on Target | 28 | `weakness` |
| Weakness to Blight Disease | spell | destruction | Weakness to Blight Disease for 10 secs on Touch | 21 | `weakness-to-blight-disease` |
| Weakness to Corprus Disease | spell | destruction | Weakness to Corprus Disease for 10 secs on Touch | 21 | `weakness-to-corprus-disease` |
| Weakness to Corpus Disease | spell | destruction | Weakness to Corprus Disease for 10 secs on Touch | 21 | `weakness-to-corpus-disease` |
| Weakness to Frost | spell | destruction | Weakness to Frost for 5 secs on Target | 8 | `weakness-to-frost` |
| Weakness to Magicka | spell | destruction | Weakness to Magicka for 5 secs on Target | 8 | `weakness-to-magicka` |
| Weakness to Poison | spell | destruction | Weakness to Poison for 5 secs on Target | 8 | `weakness-to-poison` |
| Weakness to Shock | spell | destruction | Weakness to Shock for 5 secs on Target | 8 | `weakness-to-shock` |
| Weariness | spell | destruction | Drain Fatigue 1-10 pts on Target | 1 | `weariness` |
| Weeping Wound | spell | destruction | Drain Health 1-10 pts for 3 secs on Target | 5 | `weeping-wound` |
| Wild Clumsiness | spell | destruction | Drain Agility 5-20 pts for 60 secs on Target | 56 | `wild-clumsiness` |
| Wild Shockbloom | spell | destruction | Shock Damage 2-40 pts in 10ft on Target | 14 | `wild-shockbloom` |
| Wild Spite | spell | destruction | Drain Personality 5-20 pts for 1 min, 30 secs on Target | 84 | `wild-spite` |
| Wild Strain | spell | destruction | Drain Agility 1-20 pts for 3 secs on Target | 2 | `wild-strain` |
| Wild Temptation | spell | destruction | Drain Willpower 1-20 pts for 3 secs on Target | 2 | `wild-temptation` |
| Wild Torpor | spell | destruction | Drain Speed 5-20 pts for 30 secs on Target | 28 | `wild-torpor` |
| Wild Weakness | spell | destruction | Drain Strength 1-20 pts for 3 secs on Target | 2 | `wild-weakness` |
| Wild Weeping Wound | spell | destruction | Drain Health 1-20 pts on Target | 3 | `wild-weeping-wound` |
| Wizard Rend | spell | destruction | Drain Magicka 10-35 pts for 4 secs on Target; Paralyze for 4 secs on Target | 39 | `wizard-rend` |
| Wizard's Fire | spell | destruction | Drain Health 16-35 pts on Target | 8 | `wizards-fire` |
| Wound | spell | destruction | Drain Health 1-10 pts on Target | 2 | `wound` |
| Wounding Touch | spell | destruction | Drain Health 1-10 pts for 3 secs on Touch | 3 | `wounding-touch` |
| Wrath of Araynys | spell | destruction | Damage Health 10-20 pts on Target; Damage Fatigue 10-20 pts on Target; Damage Agility 10-20 pts on Target; Damage Speed 10-20 pts on Target | 63 | `wrath-of-araynys` |
| Wrath of Dagoth | spell | destruction | Damage Health 5-50 pts for 3 secs on Target; Damage Strength 1-3 pts on Target; Damage Speed 1-3 pts on Target; Damage Endurance 1-3 pts on Target; Damage Agility 1-3 pts on Target; Damage Willpower 1-3 pts on Target; Damage Luck 1-3 pts on Target (Luck left out: 1) | 73 | `wrath-of-dagoth` |
| Wrath of Gilvoth | spell | destruction | Damage Health 10-20 pts on Target; Damage Fatigue 10-20 pts on Target; Damage Intelligence 10-20 pts on Target; Damage Willpower 10-20 pts on Target | 63 | `wrath-of-gilvoth` |
| Wrath of Tureynul | spell | destruction | Damage Fatigue 10-20 pts on Target; Damage Strength 10-20 pts on Target; Damage Endurance 10-20 pts on Target | 45 | `wrath-of-tureynul` |
| Wrath of Uthol | spell | destruction | Damage Health 10-20 pts on Target; Damage Fatigue 10-20 pts on Target; Damage Magicka 10-20 pts on Target; Weakness to Magicka on Target | 50 | `wrath-of-uthol` |
| Wrath of Vemyn | spell | destruction | Damage Health 10-20 pts on Target; Damage Fatigue 10-20 pts for 3 secs on Target; Absorb Strength 1-5 pts for 2 mins on Target | 153 (ours 255) | `wrath-of-vemyn` |
| Wrath of Vivec | spell | destruction | Damage Health 50 pts on Target; Fire Damage 50 pts on Target; Shock Damage 50 pts on Target; Frost Damage 50 pts on Target | 94 | `wrath-of-vivec` |
| Baleful Glower | spell | illusion | Sanctuary 1-8 pts for 12 mins on Self | ours 162 | `baleful-glower` |
| Blind | spell | illusion | Blind 20 pts for 10 secs on Touch | 10 | `blind` |
| Cruel Earwig | spell | illusion | Sound 5-11 pts for 5 secs on Target | 9 | `cruel-earwig` |
| Eye of Night | spell | illusion | Night Eye 50 pts for 30 secs on Self | 0 | `eye-of-night` |
| Father Ahaz | spell | illusion | Chameleon 30 pts for 30 secs on Self | 0 | `father-ahaz` |
| Frenzy Humanoid | spell | illusion | Frenzy Humanoid 5 pts for 10 secs on Target | 4 | `frenzy-humanoid` |
| Maar Gan Blessings | spell | illusion | Restore Health 30-50 pts on Touch; Sanctuary 75 pts for 30 secs on Touch; Fortify Attack 25 pts for 30 secs on Touch | 123 | `maar-gan-blessings` |
| Noise | spell | illusion | Sound 3-8 pts for 5 secs on Touch | 4 | `noise` |
| Paralysis Trap | spell | illusion | Paralyze for 10 secs on Touch | 13 | `paralysis-trap` |
| Paralysis | spell | illusion | Paralyze for 6 secs on Touch | 12 | `scrib-paralysis` |
| Sanil's Murdrum | spell | illusion | Fortify Sneak 10 pts for 30 secs on Self; Invisibility for 30 secs on Self | 45 | `sanils-murdrum` |
| Silence Trap | spell | illusion | Silence for 30 secs on Touch | 37 | `silence-trap` |
| Soothe the Savage Beast | spell | illusion | Calm Creature 30 pts for 10 secs on Touch | 15 | `soothe-the-savage-beast` |
| Spider Touch | spell | illusion | Paralyze for 3 secs on Touch | 12 | `spider-touch` |
| Absorb Agility [Ranged] | spell | mysticism | Absorb Agility 5-20 pts for 30 secs on Target | 56 | `absorb-agility-ranged` |
| Absorb Endurance [Ranged] | spell | mysticism | Absorb Endurance 5-20 pts for 30 secs on Target | 56 | `absorb-endurance-ranged` |
| Absorb Health [Ranged] | spell | mysticism | Absorb Health 5-20 pts on Target | 8 | `absorb-health-ranged` |
| Absorb Intelligence [Ranged] | spell | mysticism | Absorb Intelligence 5-51 pts for 30 secs on Target | 126 (ours 542) | `absorb-intelligence-ranged` |
| Absorb Personality [Ranged] | spell | mysticism | Absorb Personality 5-20 pts for 30 secs on Target | 56 | `absorb-personality-ranged` |
| Absorb Spell Points | spell | mysticism | Absorb Magicka 5-20 pts for 30 secs on Touch | 150 | `absorb-spell-points` |
| Absorb Spell Points [Ranged] | spell | mysticism | Absorb Magicka 5-20 pts for 30 secs on Target | 225 | `absorb-spell-points-ranged` |
| Absorb Strength [Ranged] | spell | mysticism | Absorb Strength 5-20 pts for 30 secs on Target | 56 (ours 242) | `absorb-strength-ranged` |
| Absorb Willpower [Ranged] | spell | mysticism | Absorb Willpower 5-20 pts for 30 secs on Target | 56 | `absorb-willpower-ranged` |
| Beggar's Nose | spell | mysticism | Detect Animal 200 pts for 60 secs on Self; Detect Enchantment 200 pts for 60 secs on Self; Detect Key 200 pts for 60 secs on Self | 5 | `beggars-nose` |
| Life Force | spell | mysticism | Absorb Health 5-30 pts for 30 secs on Touch; Absorb Fatigue 5-30 pts for 30 secs on Touch | 315 | `life-force` |
| Red Despair | spell | mysticism | Absorb Willpower 4-8 pts for 5 secs on Target | 5 | `red-despair` |
| Self Dispel | spell | mysticism | Dispel 5 pts on Self | 1 | `self-dispel` |
| Slave Belt | spell | mysticism | Dispel 5 pts on Self | 1 | `slave-belt` |
| Tap Energy | spell | mysticism | Absorb Fatigue 20 pts for 30 secs on Target | 180 | `tap-energy` |
| The Moth-Wing Mirror | spell | mysticism | Reflect 1-8 pts for 12 mins on Self | 1 | `the-moth-wing-mirror` |
| The Red Diamond | spell | mysticism | Reflect 1-8 pts for 12 mins on Self; Fortify Long Blade 1-8 pts for 12 mins on Self | 1 | `the-red-diamond` |
| Touch Dispel | spell | mysticism | Dispel 5 pts on Touch | 1 | `touch-dispel` |
| Vampire Touch | spell | mysticism | Absorb Health 10-30 pts on Touch | 8 | `vampire-touch` |
| Almsivi Restoration | spell | restoration | Restore Agility 100 pts on Touch; Restore Endurance 100 pts on Touch; Restore Intelligence 100 pts on Touch; Restore Luck 100 pts on Touch; Restore Personality 100 pts on Touch; Restore Speed 100 pts on Touch; Restore Strength 100 pts on Touch; Restore Willpower 100 pts on Touch (Luck left out: 1) | 40 | `almsivi-restoration` |
| Almsivi Restore Fighter | spell | restoration | Restore Block 100 pts on Touch; Restore Armorer 100 pts on Touch; Restore Medium Armor 100 pts on Touch; Restore Heavy Armor 100 pts on Touch; Restore Blunt Weapon 100 pts on Touch; Restore Long Blade 100 pts on Touch; Restore Axe 100 pts on Touch; Restore Spear 100 pts on Touch | ours 40 | `almsivi-restore-fighter` |
| Assured Balanced Armor | spell | restoration | Fortify Medium Armor 10 pts for 60 secs on Self | 30 | `assured-balanced-armor` |
| Assured Deep Biting | spell | restoration | Fortify Axe 10 pts for 60 secs on Self | 30 | `assured-deep-biting` |
| Assured Denial | spell | restoration | Fortify Block 10 pts for 60 secs on Self | 30 | `assured-denial` |
| Assured Enterprise | spell | restoration | Fortify Mercantile 10 pts for 60 secs on Self | 30 | `assured-enterprise` |
| Assured Fleetness | spell | restoration | Fortify Athletics 10 pts for 60 secs on Self | 30 | `assured-fleetness` |
| Assured Fluid Evasion | spell | restoration | Fortify Unarmored 10 pts for 60 secs on Self | 30 | `assured-fluid-evasion` |
| Assured Glib Speech | spell | restoration | Fortify Speechcraft 10 pts for 60 secs on Self | 30 | `assured-glib-speech` |
| Assured Golden Wisdom | spell | restoration | Fortify Alteration 10 pts for 60 secs on Self | 30 | `assured-golden-wisdom` |
| Assured Green Wisdom | spell | restoration | Fortify Restoration 10 pts for 60 secs on Self | 30 | `assured-green-wisdom` |
| Assured Hewing | spell | restoration | Fortify Long Blade 10 pts for 60 secs on Self | 30 | `assured-hewing` |
| Assured Horny Fist | spell | restoration | Fortify Hand To Hand 10 pts for 60 secs on Self | 30 | `assured-horny-fist` |
| Assured Impaling Thrust | spell | restoration | Fortify Spear 10 pts for 60 secs on Self | 30 | `assured-impaling-thrust` |
| Assured Leaping | spell | restoration | Fortify Acrobatics 10 pts for 60 secs on Self | 30 | `assured-leaping` |
| Assured Martial Craft | spell | restoration | Fortify Armorer 10 pts for 60 secs on Self | 30 (ours 129) | `assured-martial-craft` |
| Assured Nimble Armor | spell | restoration | Fortify Light Armor 10 pts for 60 secs on Self | 30 | `assured-nimble-armor` |
| Assured Red Wisdom | spell | restoration | Fortify Destruction 10 pts for 60 secs on Self | 30 | `assured-red-wisdom` |
| Assured Safekeeping | spell | restoration | Fortify Security 10 pts for 60 secs on Self | 30 | `assured-safekeeping` |
| Assured Silver Wisdom | spell | restoration | Fortify Illusion 10 pts for 60 secs on Self | 30 | `assured-silver-wisdom` |
| Assured Smiting | spell | restoration | Fortify Blunt Weapon 10 pts for 60 secs on Self | 30 | `assured-smiting` |
| Assured Stalking | spell | restoration | Fortify Sneak 10 pts for 60 secs on Self | 30 | `assured-stalking` |
| Assured Stolid Armor | spell | restoration | Fortify Heavy Armor 10 pts for 60 secs on Self | 30 | `assured-stolid-armor` |
| Assured Sublime Wisdom | spell | restoration | Fortify Alchemy 10 pts for 60 secs on Self | 30 (ours 129) | `assured-sublime-wisdom` |
| Assured Sureflight | spell | restoration | Fortify Marksman 10 pts for 60 secs on Self | 30 | `assured-sureflight` |
| Assured Swiftblade | spell | restoration | Fortify Short Blade 10 pts for 60 secs on Self | 30 | `assured-swiftblade` |
| Assured Transcendant Wisdom | spell | restoration | Fortify Conjuration 10 pts for 60 secs on Self | 30 | `assured-transcendant-wisdom` |
| Assured Transfiguring Wisdom | spell | restoration | Fortify Enchant 10 pts for 60 secs on Self | 30 (ours 129) | `assured-transfiguring-wisdom` |
| Assured Unseen Wisdom | spell | restoration | Fortify Mysticism 10 pts for 60 secs on Self | 30 | `assured-unseen-wisdom` |
| Blessings of the First Corner | spell | restoration | Fortify Strength 10-20 pts for 48 mins on Touch | 1 (ours 9288) | `blessings-of-the-first-corner` |
| Blessings of the Second Corner | spell | restoration | Fortify Destruction 10 pts for 48 mins on Touch; Fortify Axe 10 pts for 48 mins on Touch; Fortify Attack 10 pts for 48 mins on Touch | 1 | `blessings-of-the-second-corner` |
| Blessings of the Third Corner | spell | restoration | Fortify Speechcraft 5 pts for 24 mins on Touch | 30 | `blessings-of-the-third-corner` |
| Blightguard | spell | restoration | Resist Blight Disease 10 pts for 5 secs on Self | 13 | `blightguard` |
| Blood of the North | spell | restoration | Restore Health 2 pts for 30 secs on Self | 15 | `blood-of-the-north` |
| Blood Rage | spell | restoration | Fortify Attack 20 pts for 60 secs on Self | 20 | `blood-rage` |
| Colovia's Grace | spell | restoration | Fortify Personality 5-15 pts for 12 mins on Self | 1 | `colovias-grace` |
| Cure Blight Disease | spell | restoration | Cure Blight Disease on Touch | 100 | `cure-blight-disease-2` |
| Cure Corprus Disease | spell | restoration | Cure Corprus Disease on Self | 75 | `cure-corprus-disease` |
| Cure Corpus Disease | spell | restoration | Cure Corprus Disease on Self | 75 | `cure-corpus-disease` |
| Cure Poison on Touch | spell | restoration | Cure Poison on Touch | 5 | `cure-poison-on-touch` |
| Daedric Agility | spell | restoration | Fortify Agility 20 pts for 1 min, 30 secs on Self | 90 | `daedric-agility` |
| Daedric Endurance | spell | restoration | Fortify Endurance 20 pts for 1 min, 30 secs on Self | 90 | `daedric-endurance` |
| Daedric Intelligence | spell | restoration | Fortify Intelligence 20 pts for 1 min, 30 secs on Self | 90 (ours 387) | `daedric-intelligence` |
| Daedric Personality | spell | restoration | Fortify Personality 20 pts for 1 min, 30 secs on Self | 90 | `daedric-personality` |
| Daedric Speed | spell | restoration | Fortify Speed 20 pts for 1 min, 30 secs on Self | 90 | `daedric-speed` |
| Daedric Strength | spell | restoration | Fortify Strength 20 pts for 1 min, 30 secs on Self | 90 (ours 387) | `daedric-strength` |
| Emperor's Blessing | spell | restoration | Fortify Willpower 1-8 pts for 12 mins on Self | 1 | `emperors-blessing` |
| Eye of Talos | spell | restoration | Fortify Blunt Weapon 1-8 pts for 12 mins on Self; Shield 1-8 pts for 12 mins on Self | 1 | `eye-of-talos` |
| Felms' Glory | spell | restoration | Fortify Restoration 5 pts for 48 mins on Touch | 1 | `felms-glory` |
| Fortify Acrobatics Skill | spell | restoration | Fortify Acrobatics 10 pts for 60 secs on Self | 30 | `fortify-acrobatics-skill` |
| Fortify Alchemy Skill | spell | restoration | Fortify Alchemy 10 pts for 60 secs on Self | 30 (ours 129) | `fortify-alchemy-skill` |
| Fortify Alteration Skill | spell | restoration | Fortify Alteration 10 pts for 60 secs on Self | 30 | `fortify-alteration-skill` |
| Fortify Armorer Skill | spell | restoration | Fortify Armorer 10 pts for 60 secs on Self | 30 (ours 129) | `fortify-armorer-skill` |
| Fortify Athletics Skill | spell | restoration | Fortify Athletics 10 pts for 60 secs on Self | 30 | `fortify-athletics-skill` |
| Fortify Axe Skill | spell | restoration | Fortify Axe 10 pts for 60 secs on Self | 30 | `fortify-axe-skill` |
| Fortify Block Skill | spell | restoration | Fortify Block 10 pts for 60 secs on Self | 30 | `fortify-block-skill` |
| Fortify Blunt Weapons Skill | spell | restoration | Fortify Blunt Weapon 10 pts for 60 secs on Self | 30 | `fortify-blunt-weapons-skill` |
| Fortify Conjuration Skill | spell | restoration | Fortify Conjuration 10 pts for 60 secs on Self | 30 | `fortify-conjuration-skill` |
| Fortify Destruction Skill | spell | restoration | Fortify Destruction 10 pts for 60 secs on Self | 30 | `fortify-destruction-skill` |
| Fortify Enchant Skill | spell | restoration | Fortify Enchant 10 pts for 60 secs on Self | 30 (ours 129) | `fortify-enchant-skill` |
| Fortify Hand to Hand Skill | spell | restoration | Fortify Hand-to-hand 10 pts for 60 secs on Self | 30 | `fortify-hand-to-hand-skill` |
| Fortify Heavy Armor Skill | spell | restoration | Fortify Heavy Armor 10 pts for 60 secs on Self | 30 | `fortify-heavy-armor-skill` |
| Fortify Illusion Skill | spell | restoration | Fortify Illusion 10 pts for 60 secs on Self | 30 | `fortify-illusion-skill` |
| Fortify Light Armor Skill | spell | restoration | Fortify Light Armor 10 pts for 60 secs on Self | 30 | `fortify-light-armor-skill` |
| Fortify Long Blade Skill | spell | restoration | Fortify Long Blade 10 pts for 60 secs on Self | 30 | `fortify-long-blade-skill` |
| Fortify Marksman Skill | spell | restoration | Fortify Marksman 10 pts for 60 secs on Self | 30 | `fortify-marksman-skill` |
| Fortify Medium Armor Skill | spell | restoration | Fortify Medium Armor 10 pts for 60 secs on Self | 30 | `fortify-medium-armor-skill` |
| Fortify Mercantile Skill | spell | restoration | Fortify Mercantile 10 pts for 60 secs on Self | 30 | `fortify-mercantile-skill` |
| Fortify Mysticism Skill | spell | restoration | Fortify Mysticism 10 pts for 60 secs on Self | 30 | `fortify-mysticism-skill` |
| Fortify Restoration Skill | spell | restoration | Fortify Restoration 10 pts for 60 secs on Self | 30 | `fortify-restoration-skill` |
| Fortify Security Skill | spell | restoration | Fortify Security 10 pts for 60 secs on Self | 30 | `fortify-security-skill` |
| Fortify Short Blade Skill | spell | restoration | Fortify Short Blade 10 pts for 60 secs on Self | 30 | `fortify-short-blade-skill` |
| Fortify Sneak Skill | spell | restoration | Fortify Sneak 10 pts for 60 secs on Self | 30 | `fortify-sneak-skill` |
| Fortify Spear Skill | spell | restoration | Fortify Spear 10 pts for 60 secs on Self | 30 | `fortify-spear-skill` |
| Fortify Speechcraft Skill | spell | restoration | Fortify Speechcraft 10 pts for 60 secs on Self | 30 | `fortify-speechcraft-skill` |
| Fortify Unarmored Skill | spell | restoration | Fortify Unarmored 10 pts for 60 secs on Self | 30 | `fortify-unarmored-skill` |
| Gnisis Shrine Blessing | spell | restoration | Cure Blight Disease on Touch; Cure Common Disease on Touch; Cure Poison on Touch | 1 | `gnisis-shrine-blessing` |
| Great Heal Companion | spell | restoration | Restore Health 4-45 pts on Touch | 6 | `great-heal-companion` |
| Great Resist Corpus Disease | spell | restoration | Resist Corprus Disease 30 pts for 10 secs on Self | 75 | `great-resist-corpus-disease` |
| Great Resist Shock | spell | restoration | Resist Shock 30 pts for 10 secs on Self | 30 | `great-resist-shock` |
| Hand of Azura | spell | restoration | Restore Agility 100 pts on Touch; Restore Endurance 100 pts on Touch; Restore Speed 100 pts on Touch; Restore Strength 100 pts on Touch; Restore Willpower 100 pts on Touch; Restore Luck 100 pts on Touch (Luck left out: 1) | 30 | `hand-of-azura` |
| Hand of the Hart-King | spell | restoration | Fortify Block 1-8 pts for 12 mins on Self | 1 | `hand-of-the-hart-king` |
| Healing Word | spell | restoration | Restore Health 20-30 pts on Target | 19 | `healing-word` |
| Icarian Flight | spell | restoration | Fortify Acrobatics 500 pts for 5 secs on Self | 0 | `icarian-flight` |
| Imperial Acrobatics Skill | spell | restoration | Fortify Acrobatics 1-8 pts for 12 mins on Self | 1 | `imperial-acrobatics-skill` |
| Imperial Alchemy Skill | spell | restoration | Fortify Alchemy 1-8 pts for 12 mins on Self | 1 (ours 697) | `imperial-alchemy-skill` |
| Imperial Alteration Skill | spell | restoration | Fortify Alteration 1-8 pts for 12 mins on Self | 1 | `imperial-alteration-skill` |
| Imperial Armorer Skill | spell | restoration | Fortify Armorer 1-8 pts for 12 mins on Self | 1 (ours 697) | `imperial-armorer-skill` |
| Imperial Athletics Skill | spell | restoration | Fortify Athletics 1-8 pts for 12 mins on Self | 1 | `imperial-athletics-skill` |
| Imperial Axe Skill | spell | restoration | Fortify Axe 1-8 pts for 12 mins on Self | 1 | `imperial-axe-skill` |
| Imperial Block Skill | spell | restoration | Fortify Block 1-8 pts for 12 mins on Self | 1 | `imperial-block-skill` |
| Imperial Blunt Weapon Skill | spell | restoration | Fortify Blunt Weapon 1-8 pts for 12 mins on Self | 1 | `imperial-blunt-weapon-skill` |
| Imperial Conjuration Skill | spell | restoration | Fortify Conjuration 1-8 pts for 12 mins on Self | 1 | `imperial-conjuration-skill` |
| Imperial Destruction Skill | spell | restoration | Fortify Destruction 1-8 pts for 12 mins on Self | 1 | `imperial-destruction-skill` |
| Imperial Enchant Skill | spell | restoration | Fortify Enchant 1-8 pts for 12 mins on Self | 1 (ours 697) | `imperial-enchant-skill` |
| Imperial Hand to Hand Skill | spell | restoration | Fortify Hand To Hand 1-8 pts for 12 mins on Self | 1 | `imperial-hand-to-hand-skill` |
| Imperial Heavy Armor Skill | spell | restoration | Fortify Heavy Armor 1-8 pts for 12 mins on Self | 1 | `imperial-heavy-armor-skill` |
| Imperial Illusion Skill | spell | restoration | Fortify Illusion 1-8 pts for 12 mins on Self | 1 | `imperial-illusion-skill` |
| Imperial Light Armor Skill | spell | restoration | Fortify Light Armor 1-8 pts for 12 mins on Self | 1 | `imperial-light-armor-skill` |
| Imperial Long Blade Skill | spell | restoration | Fortify Long Blade 1-8 pts for 12 mins on Self | 1 | `imperial-long-blade-skill` |
| Imperial Marksman Skill | spell | restoration | Fortify Marksman 1-8 pts for 12 mins on Self | 1 | `imperial-marksman-skill` |
| Imperial Medium Armor Skill | spell | restoration | Fortify Medium Armor 1-8 pts for 12 mins on Self | 1 | `imperial-medium-armor-skill` |
| Imperial Mercantile Skill | spell | restoration | Fortify Mercantile 1-8 pts for 12 mins on Self | 1 | `imperial-mercantile-skill` |
| Imperial Mysticism Skill | spell | restoration | Fortify Mysticism 1-8 pts for 12 mins on Self | 1 | `imperial-mysticism-skill` |
| Imperial Restoration Skill | spell | restoration | Fortify Restoration 1-8 pts for 12 mins on Self | 1 | `imperial-restoration-skill` |
| Imperial Security Skill | spell | restoration | Fortify Security 1-8 pts for 12 mins on Self | 1 | `imperial-security-skill` |
| Imperial Short Blade Skill | spell | restoration | Fortify Short Blade 1-8 pts for 12 mins on Self | 1 | `imperial-short-blade-skill` |
| Imperial Sneak Skill | spell | restoration | Fortify Sneak 1-8 pts for 12 mins on Self | 1 | `imperial-sneak-skill` |
| Imperial Spear Skill | spell | restoration | Fortify Spear 1-8 pts for 12 mins on Self | 1 | `imperial-spear-skill` |
| Imperial Speechcraft Skill | spell | restoration | Fortify Speechcraft 1-8 pts for 12 mins on Self | 1 | `imperial-speechcraft-skill` |
| Imperial Unarmored Skill | spell | restoration | Fortify Unarmored 1-8 pts for 12 mins on Self | 1 | `imperial-unarmored-skill` |
| Koal Cave Blessing | spell | restoration | Fortify Unarmored 10 pts for 48 mins on Touch; Fortify Light Armor 10 pts for 48 mins on Touch; Fortify Medium Armor 10 pts for 48 mins on Touch; Fortify Heavy Armor 10 pts for 48 mins on Touch | 0 | `koal-cave-blessing` |
| Lady's Grace | spell | restoration | Fortify Endurance 5 pts for 48 mins on Touch | 0 | `ladys-grace` |
| Maar Gan Shrine | spell | restoration | Fortify Speechcraft 10 pts for 48 mins on Touch; Fortify Personality 10 pts for 48 mins on Touch | 1440 | `maar-gan-shrine` |
| Masterful Balanced Armor | spell | restoration | Fortify Medium Armor 15 pts for 60 secs on Self | 45 | `masterful-balanced-armor` |
| Masterful Deep Biting | spell | restoration | Fortify Axe 15 pts for 60 secs on Self | 45 | `masterful-deep-biting` |
| Masterful Denial | spell | restoration | Fortify Block 15 pts for 60 secs on Self | 45 | `masterful-denial` |
| Masterful Enterprise | spell | restoration | Fortify Mercantile 15 pts for 60 secs on Self | 45 | `masterful-enterprise` |
| Masterful Fleetness | spell | restoration | Fortify Athletics 15 pts for 60 secs on Self | 45 | `masterful-fleetness` |
| Masterful Fluid Evasion | spell | restoration | Fortify Unarmored 15 pts for 60 secs on Self | 45 | `masterful-fluid-evasion` |
| Masterful Glib Speech | spell | restoration | Fortify Speechcraft 15 pts for 60 secs on Self | 45 | `masterful-glib-speech` |
| Masterful Golden Wisdom | spell | restoration | Fortify Alteration 15 pts for 60 secs on Self | 45 | `masterful-golden-wisdom` |
| Masterful Green Wisdom | spell | restoration | Fortify Restoration 15 pts for 60 secs on Self | 45 | `masterful-green-wisdom` |
| Masterful Hewing | spell | restoration | Fortify Long Blade 15 pts for 60 secs on Self | 45 | `masterful-hewing` |
| Masterful Horny Fist | spell | restoration | Fortify Hand To Hand 15 pts for 60 secs on Self | 45 | `masterful-horny-fist` |
| Masterful Impaling Thrust | spell | restoration | Fortify Spear 15 pts for 60 secs on Self | 45 | `masterful-impaling-thrust` |
| Masterful Leaping | spell | restoration | Fortify Acrobatics 15 pts for 60 secs on Self | 45 | `masterful-leaping` |
| Masterful Martial Craft | spell | restoration | Fortify Armorer 15 pts for 60 secs on Self | 45 (ours 194) | `masterful-martial-craft` |
| Masterful Nimble Armor | spell | restoration | Fortify Light Armor 15 pts for 60 secs on Self | 45 | `masterful-nimble-armor` |
| Masterful Red Wisdom | spell | restoration | Fortify Destruction 15 pts for 60 secs on Self | 45 | `masterful-red-wisdom` |
| Masterful Safekeeping | spell | restoration | Fortify Security 15 pts for 60 secs on Self | 45 | `masterful-safekeeping` |
| Masterful Silver Wisdom | spell | restoration | Fortify Illusion 15 pts for 60 secs on Self | 45 | `masterful-silver-wisdom` |
| Masterful Smiting | spell | restoration | Fortify Blunt Weapon 15 pts for 60 secs on Self | 45 | `masterful-smiting` |
| Masterful Stalking | spell | restoration | Fortify Sneak 15 pts for 60 secs on Self | 45 | `masterful-stalking` |
| Masterful Stolid Armor | spell | restoration | Fortify Heavy Armor 15 pts for 60 secs on Self | 45 | `masterful-stolid-armor` |
| Masterful Sublime Wisdom | spell | restoration | Fortify Alchemy 15 pts for 60 secs on Self | 45 (ours 194) | `masterful-sublime-wisdom` |
| Masterful Sureflight | spell | restoration | Fortify Marksman 15 pts for 60 secs on Self | 45 | `masterful-sureflight` |
| Masterful Swiftblade | spell | restoration | Fortify Short Blade 15 pts for 60 secs on Self | 45 | `masterful-swiftblade` |
| Masterful Transcendant Wisdom | spell | restoration | Fortify Conjuration 15 pts for 60 secs on Self | 45 | `masterful-transcendant-wisdom` |
| Masterful Transfiguring Wisdom | spell | restoration | Fortify Enchant 15 pts for 60 secs on Self | 45 (ours 194) | `masterful-transfiguring-wisdom` |
| Masterful Unseen Wisdom | spell | restoration | Fortify Mysticism 15 pts for 60 secs on Self | 45 | `masterful-unseen-wisdom` |
| Meris' Warding | spell | restoration | Resist Corprus Disease 20 pts for 48 mins on Touch | 1 | `meris-warding` |
| Meris's Warding | spell | restoration | Resist Corprus Disease 20 pts for 24 mins on Self | 1 | `meriss-warding` |
| Mount Kand Shrine | spell | restoration | Fortify Endurance 10 pts for 48 mins on Touch; Fortify Intelligence 10 pts for 48 mins on Touch | 2880 (ours 7632) | `mount-kand-shrine` |
| Nibenay's Wit | spell | restoration | Fortify Health 1-8 pts for 12 mins on Self | 1 | `nibenays-wit` |
| Olms' Benediction | spell | restoration | Resist Common Disease 20 pts for 48 mins on Touch | 1 | `olms-benediction` |
| Palace Blessings | spell | restoration | Fortify Mercantile 10 pts for 48 mins on Touch; Fortify Luck 10 pts for 48 mins on Touch (Luck left out: 1) | 0 | `palace-blessings` |
| Reman's Girdle | spell | restoration | Fortify Fatigue 1-8 pts for 12 mins on Self | 1 | `remans-girdle` |
| Resist Cold | spell | restoration | Resist Frost 10 pts for 5 secs on Self | 5 | `resist-cold` |
| Resist Corprus Disease | spell | restoration | Resist Corprus Disease 10 pts for 5 secs on Self | 25 | `resist-corprus-disease` |
| Resist Corpus Disease | spell | restoration | Resist Corprus Disease 10 pts for 5 secs on Self | 25 | `resist-corpus-disease` |
| Restore Attributes | spell | restoration | Restore Agility 100 pts on Touch; Restore Endurance 100 pts on Touch; Restore Intelligence 100 pts on Touch; Restore Luck 100 pts on Touch; Restore Personality 100 pts on Touch; Restore Speed 100 pts on Touch; Restore Strength 100 pts on Touch; Restore Willpower 100 pts on Touch (Luck left out: 1) | 40 | `restore-attributes` |
| Restore Fighter | spell | restoration | Restore Block 100 pts on Touch; Restore Armorer 100 pts on Touch; Restore Medium Armor 100 pts on Touch; Restore Heavy Armor 100 pts on Touch; Restore Blunt Weapon 100 pts on Touch; Restore Long Blade 100 pts on Touch; Restore Axe 100 pts on Touch; Restore Spear 100 pts on Touch | ours 40 | `restore-fighter` |
| Roris' Bloom | spell | restoration | Fortify Health 5 pts for 48 mins on Touch | 1 | `roris-bloom` |
| Roris's Bloom | spell | restoration | Fortify Health 5 pts for 24 mins on Self | 1 | `roriss-bloom` |
| Saguine Leaping | spell | restoration | Fortify Acrobatics 10 pts for 30 secs on Self | 15 | `saguine-leaping` |
| Sanctus Shrine | spell | restoration | Fortify Endurance 10 pts for 48 mins on Touch; Fortify Willpower 10 pts for 48 mins on Touch | 2880 | `sanctus-shrine` |
| Sanguine Balanced Armor | spell | restoration | Fortify Medium Armor 10 pts for 30 secs on Self | 15 | `sanguine-balanced-armor` |
| Sanguine Deep Biting | spell | restoration | Fortify Axe 10 pts for 30 secs on Self | 15 | `sanguine-deep-biting` |
| Sanguine Denial | spell | restoration | Fortify Block 10 pts for 30 secs on Self | 15 | `sanguine-denial` |
| Sanguine Enterprise | spell | restoration | Fortify Mercantile 10 pts for 30 secs on Self | 15 | `sanguine-enterprise` |
| Sanguine Fleetness | spell | restoration | Fortify Athletics 10 pts for 30 secs on Self | 15 | `sanguine-fleetness` |
| Sanguine Fluid Evasion | spell | restoration | Fortify Unarmored 10 pts for 30 secs on Self | 15 | `sanguine-fluid-evasion` |
| Sanguine Glib Speech | spell | restoration | Fortify Speechcraft 10 pts for 30 secs on Self | 15 | `sanguine-glib-speech` |
| Sanguine Golden Wisdom | spell | restoration | Fortify Alteration 10 pts for 30 secs on Self | 15 | `sanguine-golden-wisdom` |
| Sanguine Green Wisdom | spell | restoration | Fortify Restoration 3 pts for 5 secs on Self | 1 | `sanguine-green-wisdom` |
| Sanguine Hewing | spell | restoration | Fortify Long Blade 10 pts for 30 secs on Self | 15 | `sanguine-hewing` |
| Sanguine Horny Fist | spell | restoration | Fortify Hand To Hand 10 pts for 30 secs on Self | 15 | `sanguine-horny-fist` |
| Sanguine Impaling Thrust | spell | restoration | Fortify Spear 10 pts for 30 secs on Self | 15 | `sanguine-impaling-thrust` |
| Sanguine Martial Craft | spell | restoration | Fortify Armorer 10 pts for 30 secs on Self | 15 (ours 65) | `sanguine-martial-craft` |
| Sanguine Nimble Armor | spell | restoration | Fortify Light Armor 10 pts for 30 secs on Self | 15 | `sanguine-nimble-armor` |
| Sanguine Red Wisdom | spell | restoration | Fortify Destruction 10 pts for 30 secs on Self | 15 | `sanguine-red-wisdom` |
| Sanguine Safekeeping | spell | restoration | Fortify Security 10 pts for 30 secs on Self | 15 | `sanguine-safekeeping` |
| Sanguine Silver Wisdom | spell | restoration | Fortify Illusion 10 pts for 30 secs on Self | 15 | `sanguine-silver-wisdom` |
| Sanguine Smiting | spell | restoration | Fortify Blunt Weapon 10 pts for 30 secs on Self | 15 | `sanguine-smiting` |
| Sanguine Stalking | spell | restoration | Fortify Sneak 10 pts for 30 secs on Self | 15 | `sanguine-stalking` |
| Sanguine Stolid Armor | spell | restoration | Fortify Heavy Armor 10 pts for 30 secs on Self | 15 | `sanguine-stolid-armor` |
| Sanguine Sublime Wisdom | spell | restoration | Fortify Alchemy 10 pts for 30 secs on Self | 15 (ours 65) | `sanguine-sublime-wisdom` |
| Sanguine Sureflight | spell | restoration | Fortify Marksman 10 pts for 30 secs on Self | 15 | `sanguine-sureflight` |
| Sanguine Swiftblade | spell | restoration | Fortify Short Blade 10 pts for 30 secs on Self | 15 | `sanguine-swiftblade` |
| Sanguine Transcendant Wisdom | spell | restoration | Fortify Conjuration 10 pts for 30 secs on Self | 15 | `sanguine-transcendant-wisdom` |
| Sanguine Transfiguring Wisdom | spell | restoration | Fortify Enchant 10 pts for 30 secs on Self | 15 (ours 65) | `sanguine-transfiguring-wisdom` |
| Sanguine Unseen Wisdom | spell | restoration | Fortify Mysticism 10 pts for 30 secs on Self | 15 | `sanguine-unseen-wisdom` |
| Seryn's Shield | spell | restoration | Resist Poison 20 pts for 48 mins on Touch | 5760 | `seryns-shield` |
| Sheogorath's Blessing | spell | restoration | Fortify Agility 20 pts for 240 mins on Target; Fortify Speed 20 pts for 240 mins on Target | 43200 | `sheogoraths-blessing` |
| Shield of St. Delyn | spell | restoration | Resist Blight Disease 10 pts for 48 mins on Touch | 1 | `shield-of-st-delyn` |
| Shrine Acrobatics Skill | spell | restoration | Fortify Acrobatics 5 pts for 24 mins on Self | 1 | `shrine-acrobatics-skill` |
| Shrine Alchemy Skill | spell | restoration | Fortify Alchemy 5 pts for 24 mins on Self | 1 (ours 1548) | `shrine-alchemy-skill` |
| Shrine Alteration Skill | spell | restoration | Fortify Alteration 5 pts for 24 mins on Self | 1 | `shrine-alteration-skill` |
| Shrine Armorer Skill | spell | restoration | Fortify Armorer 5 pts for 24 mins on Self | 1 (ours 1548) | `shrine-armorer-skill` |
| Shrine Athletics Skill | spell | restoration | Fortify Athletics 5 pts for 24 mins on Self | 1 | `shrine-athletics-skill` |
| Shrine Axe Skill | spell | restoration | Fortify Axe 5 pts for 24 mins on Self | 1 | `shrine-axe-skill` |
| Shrine Block Skill | spell | restoration | Fortify Block 5 pts for 24 mins on Self | 1 | `shrine-block-skill` |
| Shrine Blunt Weapon Skill | spell | restoration | Fortify Blunt Weapon 5 pts for 24 mins on Self | 1 | `shrine-blunt-weapon-skill` |
| Shrine Conjuration Skill | spell | restoration | Fortify Conjuration 5 pts for 24 mins on Self | 1 | `shrine-conjuration-skill` |
| Shrine Destruction Skill | spell | restoration | Fortify Destruction 5 pts for 24 mins on Self | 1 | `shrine-destruction-skill` |
| Shrine Enchant Skill | spell | restoration | Fortify Enchant 5 pts for 24 mins on Self | 1 (ours 1548) | `shrine-enchant-skill` |
| Shrine Hand to Hand Skill | spell | restoration | Fortify Hand To Hand 5 pts for 24 mins on Self | 1 | `shrine-hand-to-hand-skill` |
| Shrine Heavy Armor Skill | spell | restoration | Fortify Heavy Armor 5 pts for 24 mins on Self | 1 | `shrine-heavy-armor-skill` |
| Shrine Illusion Skill | spell | restoration | Fortify Illusion 5 pts for 24 mins on Self | 1 | `shrine-illusion-skill` |
| Shrine Light Armor Skill | spell | restoration | Fortify Light Armor 5 pts for 24 mins on Self | 1 | `shrine-light-armor-skill` |
| Shrine Long Blade Skill | spell | restoration | Fortify Long Blade 5 pts for 24 mins on Self | 1 | `shrine-long-blade-skill` |
| Shrine Marksman Skill | spell | restoration | Fortify Marksman 5 pts for 24 mins on Self | 1 | `shrine-marksman-skill` |
| Shrine Medium Armor Skill | spell | restoration | Fortify Medium Armor 5 pts for 24 mins on Self | 1 | `shrine-medium-armor-skill` |
| Shrine Mercantile Skill | spell | restoration | Fortify Mercantile 5 pts for 24 mins on Self | 1 | `shrine-mercantile-skill` |
| Shrine Mysticism Skill | spell | restoration | Fortify Mysticism 5 pts for 24 mins on Self | 1 | `shrine-mysticism-skill` |
| Shrine Restoration Skill | spell | restoration | Fortify Restoration 5 pts for 24 mins on Self | 1 | `shrine-restoration-skill` |
| Shrine Security Skill | spell | restoration | Fortify Security 5 pts for 24 mins on Self | 1 | `shrine-security-skill` |
| Shrine Short Blade Skill | spell | restoration | Fortify Short Blade 5 pts for 24 mins on Self | 1 | `shrine-short-blade-skill` |
| Shrine Sneak Skill | spell | restoration | Fortify Sneak 5 pts for 24 mins on Self | 1 | `shrine-sneak-skill` |
| Shrine Spear Skill | spell | restoration | Fortify Spear 5 pts for 24 mins on Self | 1 | `shrine-spear-skill` |
| Shrine Speechcraft Skill | spell | restoration | Fortify Speechcraft 5 pts for 24 mins on Self | 1 | `shrine-speechcraft-skill` |
| Shrine Unarmored Skill | spell | restoration | Fortify Unarmored 5 pts for 24 mins on Self | 1 | `shrine-unarmored-skill` |
| Skylamp's Shadow | spell | restoration | Fortify Speed 5-20 pts for 30 secs on Self | 19 | `skylamps-shadow` |
| Soul of Sotha Sil | spell | restoration | Fortify Magicka 5 pts for 48 mins on Touch | 1 | `soul-of-sotha-sil` |
| Spirit of Nerevar | spell | restoration | Fortify Fatigue 20 pts for 48 mins on Touch | 1 | `spirit-of-nerevar` |
| Strong Heal Companion | spell | restoration | Restore Health 6-25 pts on Self | 4 | `strong-heal-companion` |
| Strong Resist Corpus Disease | spell | restoration | Resist Corprus Disease 20 pts for 10 secs on Self | 50 | `strong-resist-corpus-disease` |
| Surpassing Balanced Armor | spell | restoration | Fortify Medium Armor 12 pts for 60 secs on Self | 36 | `surpassing-balanced-armor` |
| Surpassing Deep Biting | spell | restoration | Fortify Axe 12 pts for 60 secs on Self | 36 | `surpassing-deep-biting` |
| Surpassing Denial | spell | restoration | Fortify Block 12 pts for 60 secs on Self | 36 | `surpassing-denial` |
| Surpassing Enterprise | spell | restoration | Fortify Mercantile 12 pts for 60 secs on Self | 36 | `surpassing-enterprise` |
| Surpassing Fleetness | spell | restoration | Fortify Athletics 12 pts for 60 secs on Self | 36 | `surpassing-fleetness` |
| Surpassing Fluid Evasion | spell | restoration | Fortify Unarmored 12 pts for 60 secs on Self | 36 | `surpassing-fluid-evasion` |
| Surpassing Glib Speech | spell | restoration | Fortify Speechcraft 12 pts for 60 secs on Self | 36 | `surpassing-glib-speech` |
| Surpassing Golden Wisdom | spell | restoration | Fortify Alteration 12 pts for 60 secs on Self | 36 | `surpassing-golden-wisdom` |
| Surpassing Green Wisdom | spell | restoration | Fortify Restoration 12 pts for 60 secs on Self | 36 | `surpassing-green-wisdom` |
| Surpassing Hewing | spell | restoration | Fortify Long Blade 12 pts for 60 secs on Self | 36 | `surpassing-hewing` |
| Surpassing Horny Fist | spell | restoration | Fortify Hand To Hand 12 pts for 60 secs on Self | 36 | `surpassing-horny-fist` |
| Surpassing Impaling Thrust | spell | restoration | Fortify Spear 12 pts for 60 secs on Self | 36 | `surpassing-impaling-thrust` |
| Surpassing Leaping | spell | restoration | Fortify Acrobatics 12 pts for 60 secs on Self | 36 | `surpassing-leaping` |
| Surpassing Martial Craft | spell | restoration | Fortify Armorer 12 pts for 60 secs on Self | 36 (ours 155) | `surpassing-martial-craft` |
| Surpassing Nimble Armor | spell | restoration | Fortify Light Armor 12 pts for 60 secs on Self | 36 | `surpassing-nimble-armor` |
| Surpassing Red Wisdom | spell | restoration | Fortify Destruction 12 pts for 60 secs on Self | 36 | `surpassing-red-wisdom` |
| Surpassing Safekeeping | spell | restoration | Fortify Security 12 pts for 60 secs on Self | 36 | `surpassing-safekeeping` |
| Surpassing Silver Wisdom | spell | restoration | Fortify Illusion 12 pts for 60 secs on Self | 36 | `surpassing-silver-wisdom` |
| Surpassing Smiting | spell | restoration | Fortify Blunt Weapon 12 pts for 60 secs on Self | 36 | `surpassing-smiting` |
| Surpassing Stalking | spell | restoration | Fortify Sneak 12 pts for 60 secs on Self | 36 | `surpassing-stalking` |
| Surpassing Stolid Armor | spell | restoration | Fortify Heavy Armor 12 pts for 60 secs on Self | 36 | `surpassing-stolid-armor` |
| Surpassing Sublime Wisdom | spell | restoration | Fortify Alchemy 12 pts for 60 secs on Self | 36 (ours 155) | `surpassing-sublime-wisdom` |
| Surpassing Sunlight | spell | restoration | Fortify Marksman 12 pts for 60 secs on Self | 36 | `surpassing-sunlight` |
| Surpassing Swiftblade | spell | restoration | Fortify Short Blade 12 pts for 60 secs on Self | 36 | `surpassing-swiftblade` |
| Surpassing Transcendant Wisdom | spell | restoration | Fortify Conjuration 12 pts for 60 secs on Self | 36 | `surpassing-transcendant-wisdom` |
| Surpassing Transfiguring Wisdom | spell | restoration | Fortify Enchant 12 pts for 60 secs on Self | 36 (ours 155) | `surpassing-transfiguring-wisdom` |
| Surpassing Unseen Wisdom | spell | restoration | Fortify Mysticism 12 pts for 60 secs on Self | 36 | `surpassing-unseen-wisdom` |
| The Dove's Promise | spell | restoration | Resist Common Disease 1-30 pts for 12 mins on Self | 1 | `the-doves-promise` |
| The Eight Gifts | spell | restoration | Fortify Long Blade 1-8 pts for 12 mins on Self; Fortify Heavy Armor 1-8 pts for 12 mins on Self; Fortify Armorer 1-8 pts for 12 mins on Self; Fortify Blunt Weapon 1-8 pts for 12 mins on Self; Fortify Block 1-8 pts for 12 mins on Self; Fortify Athletics 1-8 pts for 12 mins on Self; Fortify Endurance 1-8 pts for 12 mins on Self; Fortify Fatigue 1-8 pts for 12 mins on Self | 1 (ours 1750) | `the-eight-gifts` |
| The Eight Wonders | spell | restoration | Fortify Agility 1-8 pts for 12 mins on Self; Fortify Endurance 1-8 pts for 12 mins on Self; Fortify Intelligence 1-8 pts for 12 mins on Self; Fortify Luck 1-8 pts for 12 mins on Self; Fortify Personality 1-8 pts for 12 mins on Self; Fortify Speed 1-8 pts for 12 mins on Self; Fortify Strength 1-8 pts for 12 mins on Self; Fortify Willpower 1-8 pts for 12 mins on Self (Luck left out: 1) | 1 (ours 2203) | `the-eight-wonders` |
| The Rock of Llothis | spell | restoration | Fortify Willpower 5 pts for 48 mins on Touch | 1 | `the-rock-of-llothis` |
| Troll's Blood | spell | restoration | Restore Health 1-3 pts for 10 secs on Self | 5 | `trolls-blood` |
| Variable Resist Corpus Disease | spell | restoration | Resist Corprus Disease 1-30 pts for 10 secs on Self | 39 | `variable-resist-corpus-disease` |
| Veloth's Gift | spell | restoration | Restore Health 10 pts on Touch | 3 | `veloths-gift` |
| Veloth's Indwelling | spell | restoration | Fortify Magicka 10 pts for 48 mins on Touch | 1440 | `veloths-indwelling` |
| Vivec's Fury | spell | restoration | Fortify Attack 5 pts for 48 mins on Touch | 1 | `vivecs-fury` |
| Vivec's Humility | spell | restoration | Fortify Personality 5 pts for 48 mins on Touch | 720 | `vivecs-humility` |
| Wild Fortify Acrobatics Skill | spell | restoration | Fortify Acrobatics 5-30 pts for 1 min, 30 secs on Self | 79 | `wild-fortify-acrobatics-skill` |
| Wild Fortify Alchemy Skill | spell | restoration | Fortify Alchemy 5-30 pts for 1 min, 30 secs on Self | 79 (ours 339) | `wild-fortify-alchemy-skill` |
| Wild Fortify Alteration Skill | spell | restoration | Fortify Alteration 5-30 pts for 1 min, 30 secs on Self | 79 | `wild-fortify-alteration-skill` |
| Wild Fortify Armorer Skill | spell | restoration | Fortify Armorer 5-30 pts for 1 min, 30 secs on Self | 79 (ours 339) | `wild-fortify-armorer-skill` |
| Wild Fortify Athletics Skill | spell | restoration | Fortify Athletics 5-30 pts for 1 min, 30 secs on Self | 79 | `wild-fortify-athletics-skill` |
| Wild Fortify Axe Skill | spell | restoration | Fortify Axe 5-30 pts for 1 min, 30 secs on Self | 79 | `wild-fortify-axe-skill` |
| Wild Fortify Block Skill | spell | restoration | Fortify Block 5-30 pts for 1 min, 30 secs on Self | 79 | `wild-fortify-block-skill` |
| Wild Fortify Blunt Weapon Skill | spell | restoration | Fortify Blunt Weapon 5-30 pts for 1 min, 30 secs on Self | 79 | `wild-fortify-blunt-weapon-skill` |
| Wild Fortify Conjuration Skill | spell | restoration | Fortify Conjuration 5-30 pts for 1 min, 30 secs on Self | 79 | `wild-fortify-conjuration-skill` |
| Wild Fortify Destruction Skill | spell | restoration | Fortify Destruction 5-30 pts for 1 min, 30 secs on Self | 79 | `wild-fortify-destruction-skill` |
| Wild Fortify Enchant Skill | spell | restoration | Fortify Enchant 5-30 pts for 1 min, 30 secs on Self | 79 (ours 339) | `wild-fortify-enchant-skill` |
| Wild Fortify Hand to Hand Skill | spell | restoration | Fortify Hand To Hand 5-30 pts for 1 min, 30 secs on Self | 79 | `wild-fortify-hand-to-hand-skill` |
| Wild Fortify Heavy Armor Skill | spell | restoration | Fortify Heavy Armor 5-30 pts for 1 min, 30 secs on Self | 79 | `wild-fortify-heavy-armor-skill` |
| Wild Fortify Light Armor Skill | spell | restoration | Fortify Light Armor 5-30 pts for 1 min, 30 secs on Self | 79 | `wild-fortify-light-armor-skill` |
| Wild Fortify Long Blade Skill | spell | restoration | Fortify Long Blade 5-30 pts for 1 min, 30 secs on Self | 79 | `wild-fortify-long-blade-skill` |
| Wild Fortify Marksman Skill | spell | restoration | Fortify Marksman 5-30 pts for 1 min, 30 secs on Self | 79 | `wild-fortify-marksman-skill` |
| Wild Fortify Medium Armor Skill | spell | restoration | Fortify Medium Armor 5-30 pts for 1 min, 30 secs on Self | 79 | `wild-fortify-medium-armor-skill` |
| Wild Fortify Mercantile Skill | spell | restoration | Fortify Mercantile 5-30 pts for 1 min, 30 secs on Self | 79 | `wild-fortify-mercantile-skill` |
| Wild Fortify Mysticism Skill | spell | restoration | Fortify Mysticism 5-30 pts for 1 min, 30 secs on Self | 79 | `wild-fortify-mysticism-skill` |
| Wild Fortify Restoration Skill | spell | restoration | Fortify Restoration 5-30 pts for 1 min, 30 secs on Self | 79 | `wild-fortify-restoration-skill` |
| Wild Fortify Security Skill | spell | restoration | Fortify Security 5-30 pts for 1 min, 30 secs on Self | 79 | `wild-fortify-security-skill` |
| Wild Fortify Short Blade Skill | spell | restoration | Fortify Short Blade 5-30 pts for 1 min, 30 secs on Self | 79 | `wild-fortify-short-blade-skill` |
| Wild Fortify Sneak Skill | spell | restoration | Fortify Sneak 5-30 pts for 1 min, 30 secs on Self | 79 | `wild-fortify-sneak-skill` |
| Wild Fortify Spear Skill | spell | restoration | Fortify Spear 5-30 pts for 1 min, 30 secs on Self | 79 | `wild-fortify-spear-skill` |
| Wild Fortify Speechcraft Skill | spell | restoration | Fortify Speechcraft 5-30 pts for 1 min, 30 secs on Self | 79 | `wild-fortify-speechcraft-skill` |
| Wild Fortify Unarmored Skill | spell | restoration | Fortify Unarmored 5-30 pts for 1 min, 30 secs on Self | 79 | `wild-fortify-unarmored-skill` |
| Ysmir's Cough | spell | restoration | Fortify Health 1-8 pts for 12 mins on Self | 1 | `ysmirs-cough` |
| Zenithar's Blessing | spell | restoration | Fortify Mercantile 5 pts for 1 min, 30 secs on Self | 25 | `zenithars-blessing` |
