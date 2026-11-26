# Stack inventory: the magic the player has today, and the building material (owner issue #104)

Measured 2026-11-26 by serialising the plugins to YAML in a scratch dir (Spriggit 0.41, since deleted) and reading Skyrim.esm, Update,
the DLCs, Creation Club, Magic.esp, BM&V, KoTM, HTBM and the mihail creature mods; the soulslike plugins by a GRUP walker over the
binary (record counts and SPIT types). Numbers are for the load-order winners. Not read: Magistrate Levitate.esp (read by `strings`
only, Spriggit refused it), Tropical Skyrim (races only), Shroom Beetles/Medusa/Depths (no spells of use). Siblings: `how-magic-mods-are-built.md`
(technique and costs), `lore-of-marsh-magic.md` (lore).

## 0. Live docs, and the one to edit
- `docs/research/mods/lane-1.12-magic.md` and `lane-1.12-magicpane.md` (2026-10-31): their Magic.esp counts are CONFIRMED (152 SPEL, 191 MGEF,
  19 hidden, 140 BOOK, 55 SCRL, 40 WEAP, 10 ARMO, 4 PERK, 1 QUST, 23 scripts; MGEF skills Alt 39, Con 25, Des 43, Ill 25, Res 46, none 13).
  Their WIRING is SUPERSEDED: the pivot of 2026-11-05 deleted ArgoniaCore, the PrismaUI magic pane and `trade_class_mod_stock`
  (`git ls-files skse` holds only ArgoniaDodgeBuffer; no `ui/views/magic`). Today no vendor sells Magic Expanded tomes (section 3).
  `story/data/db/mod_form.jsonl` and `trade_class_mod_stock.jsonl` are dead data of that build.
- `story/lore/topics/magic-effects.md` (1,122 lines, Morrowind catalogue for `packages/magic`) and `spell-sellers.md` are pre-pivot design;
  `magic-practice.md` (six schools, Mysticism a folk school) is still the lore stance. `morrowind-level-scripting.md` is about quests, not spells.
- The doc to edit for the proposal: `docs/design/blocks.md` (`teach_spell`, `add_perk` are the delivery blocks) plus this file for facts.

## 1. Player-castable spells

"Castable" = a SPEL of type Spell with a school tier (HalfCostPerk Novice..Master) taught by a BOOK. Counts of tome-taught spells:

| source | Alteration | Conjuration | Destruction | Illusion | Restoration | total |
|---|---|---|---|---|---|---|
| Vanilla (Skyrim+Update) N/A/Ad/Ex/Ma | 2/2/5/3/2 = 14 | 3/5/4/5/4 = 21 | 3/6/6/6/3 = 24 | 3/3/2/3/4 = 15 | 2/4/5/4/2 = 17 | 91 (+2 untiered) |
| DLC + CC | 0/0/1/1/0 = 2 | 1/1/11/2/2 = 17 | 0/0/1/0/0 = 1 | 0/0/1/0/0 = 1 | 0/2/4/0/0 = 6 | 27 |
| Magic Expanded | 2/9/12/14/6 = 43 | 2/3/5/2/1 = 13 | 0/13/8/15/5 = 41 | 2/5/7/4/0 = 18 | 2/2/7/8/5 = 24 | 139 (140 tomes) |
| Magistrate Levitate | 1 (Expert, per dependency row; not measured) | | | | | 1 |

Vanilla+DLC+CC per tier N/A/Ad/Ex/Ma: Alt 2/2/6/4/2, Con 4/6/15/7/6, Des 3/6/7/6/3, Ill 3/3/3/3/4, Res 2/6/9/4/2. DLC Conjuration Adept 11 is
Seeker, Ash Spawn, Dark Seducer/Golden Saint (CC Saints & Seducers duplicates the DLC ones: 4 + Staada). Spells with a school but no tome (NPC-only):
vanilla 39, DLC+CC 18 school spells; a further 276 + 235 creature spells have no school.
Other spell-type SPELs in the stack, none with a tome unless noted (types by GRUP walk): KoTM 44 + 9 diseases + 6 poisons; HTBM 16 + Cipactli 8;
Lamia 25; mihail dreughs 19 (the Water school, below); NewArmoury 13; Ultimate Dodge 5; Rim Parry 61 (+ EREP patch 14, mechanism casts:
Exe*/Elden*/OverKill*); TK Dodge 2; sweep attacks 1; USSEP 3; Sirenroot 1; Nix 1; Valenwood 1 (Griffin Whirlwind, type Voice, taught by one
placed tome "Whirlwind", ref in Valenwood Dock7). Mods that change spells/powers/abilities for the player: Magic.esp (7 abilities), Magistrate
Levitate, ours (`ARG_NoHealthRegen`), Elden Counter (2 abilities + 1 lesser power), Keytrace 4 abilities, TDM 1, NASC 1, TK Dodge, UDM 11 abilities:
all combat mechanism, no menu spell. Perks: Magic.esp 4 (Silence, Grip Time, Slowfall x2), NewArmoury 1, Rim Parry 9, sweep 2, TK Dodge 5.
Staves/scrolls/enchants: ME 32 enchanted staves (+ 8 bound weapons), 55 scrolls, 43 object effects (11 + 32 staff); vanilla 63 staves, 74 scrolls,
605 object effects; DLC+CC 21 staves, 35 scrolls, 152 object effects; mods (HTBM 7+11, KoTM 6, NewArmoury 26) 28 staves, 10 scrolls.

Morrowind-style effects present (ME unless named): mark, recall (Alteration Expert), teleportation x4 (to a placed portal activator), water walking x2
(+Water Strider on target), swift swim, jump x4 (Hoptoad), slowfall x3, burden x2, ease burden/pack mule/beast of burden (feather), slow/speed time
and clocks, telekinetic grip, resist fire/frost/shock/poison/magic x2 tiers, shields (flame/frost/shock), weakness to fire/frost/shock/poison/magic x3 tiers,
corrode/disintegrate armor, disintegrate weapon, drain magicka/stamina, absorb health/magicka/stamina, damage health bolts, viperbolt x3, poison cloak/
spray/touch/toxic cloud, silence, blind x2, command creature/humanoid/undead x3 tiers, calm/fear runes, paralysis rune, night-eye, phantom form,
sanctuary, reflect damage, spelldrinker x2, dispel x4, soul trap (mass), cure disease/poison, disease immunity, resurrection, 11 bound items,
analyze, throw noise, fortify health/magicka/stamina, regeneration. Levitate: Magistrate Levitate only. Vanilla adds waterbreathing (Alt Adept),
detect life/dead, telekinesis, invisibility, light, armour spells, atronach/familiar/dremora/thrall summons, turn undead, wards.
Missing: open/lock, fortify attributes/skills, restore/damage other attributes, charm, chameleon as such, divine/almsivi intervention, summon creatures
of the marsh (ME summons only Conjure Ghost), water breathing as a cast spell beside the vanilla one, any Mysticism school (see 2).
Duplicates: ME resist/weakness/hoptoad/slowfall ladders are 3-4 near-identical tiers; vanilla armour (oakflesh..ebonyflesh) overlaps ME shields/resists;
Command (9 spells) and Weakness (17) are the bloat. Gaps: ME Novice 10, Master 17 only; Conjuration thin (13) beside vanilla's 38; Illusion has no Master;
Destruction has no Novice (vanilla supplies it); no ME spell is Argonian in flavour (cold "Whiteout", "Stormcell", dragon-storm effects were renamed pre-pivot).

### Full Magic Expanded list (EDID-less: name [local id: effect magnitude / seconds]; Aimed/Self/Touch not shown; 145 SPEL of type Spell)

#### Alteration
- Novi (2): Slow Clock [000A4E: Slow Clock 1], Speed Clock [000A37: Speed Clock 1]
- Appr (9): Ease Burden [00082A: Fortify Carry Weight 50 / 300s; Damage Magicka 10 / 300s], Resist Fire [000865: Resist Fire 25 / 60s], Resist Frost [0008AB: Resist Frost 25 / 60s], Resist Poison [0008BC: Resist Poison 25 / 60s], Resist Shock [0008BE: Resist Shock 25 / 60s], Slow Time [000836: Slow Time 0.7 / 8s], Slowfall [00095C: Slowfall 0.5 / 20s], Swift Swim [00095D: Swift Swim / 60s], Tinur's Hoptoad [0009EE: Jump 100 / 10s]
- Adep (12): Burden [0009FB: Burden 75 / 20s], Disarm [00093E: Disarm 30], Flame Shield [000807: Flame Shield 5 / 30s; Resist Fire 25 / 30s], Frost Shield [000806: Frost Shield 5 / 30s; Resist Frost 25 / 30s], Greater Hoptoad [000A06: Jump 200 / 10s], Greater Slow Time [000AF5: Slow Time 0.5 / 12s], Paralysis Rune [000A7B: Paralysis Rune 20 / 10s], Resist Magic [0009F4: Resist Magic 25 / 60s], Shock Shield [000A84: Shock Shield 5 / 30s; Resist Shock 25 / 30s], Teleportation [0009F2: Teleportation], Water Strider [000A9E: Water Walking / 60s], Water Walking [000A9B: Water Walking / 60s]
- Expe (14): Cyclone [000858: Cyclone 75], Greater Resist Fire [000866: Resist Fire 50 / 60s], Greater Resist Frost [0009F3: Resist Frost 50 / 60s], Greater Resist Poison [0008BD: Resist Poison 50 / 60s], Greater Resist Shock [0008BF: Resist Shock 50 / 60s], Greater Slowfall [00099D: Slowfall 0.9 / 20s], Greater Teleportation [000A01: Teleportation], Grip Time [000827: Grip Time 0.1 / 5s], Mark [000A8C: Mark], Mass Burden [0009FC: Burden 75 / 20s], Pack Mule [0008DA: Fortify Carry Weight 150 / 300s; Damage Magicka 25 / 300s], Recall [000A8E: Recall], Superior Hoptoad [000A07: Jump 320 / 10s], Superior Slow Time [000AF6: Slow Time 0.3 / 16s]
- Mast (6): Beast of Burden [0008E4: Fortify Carry Weight 250 / 300s; Damage Magicka 50 / 300s], Greater Resist Magic [0009F5: Resist Magic 50 / 60s], Greater Slow Clock [000A4F: Greater Slow Clock 20], Greater Speed Clock [000A4D: Greater Speed Clock 20], Superior Teleportation [000A02: Teleportation], Telekinetic Grip [000A65: Telekinetic Grip 1]

#### Conjuration
- Novi (2): Bound Mace [0008EF: Bound Mace / 120s; Mystic Mace / 120s], Bound War Axe [0008FB: Bound War Axe / 120s; Mystic War Axe / 120s]
- Appr (3): Bound Greatsword [0008FD: Bound Greatsword / 120s; Mystic Greatsword / 120s], Bound Warhammer [0008FC: Bound Warhammer / 120s; Mystic Warhammer / 120s], Conjure Ghost [00081E: Conjure Ghost / 60s]
- Adep (5): Bound Boots [000946: Bound Boots / 120s; Mystic Boots / 120s], Bound Cuirass [000930: Bound Cuirass / 120s; Mystic Cuirass / 120s], Bound Gauntlets [000945: Bound Gauntlets / 120s; Mystic Gauntlets / 120s], Bound Helmet [000944: Bound Helmet / 120s; Mystic Helmet / 120s], Bound Shield [0009D3: Bound Shield / 120s; Mystic Shield / 120s]
- Expe (2): Bound Armor [0009EC: Bound Cuirass / 120s; Mystic Cuirass / 120s; Bound Helmet / 120s], Mass Soul Trap [000823: Soul Trap / 60s]
- Mast (1): Command Greater Humanoid [000A95: Command Humanoid 150 / 60s]

#### Destruction
- Appr (13): Cold Touch [000A17: Cold Touch 30; Perk Impact Stagger 0.3; Deep Freeze Paralyze / 3s], Drain Stamina [000A1F: Drain Stamina 250 / 30s], Entropic Bolt [0009BE: Damage Health 30; Perk Impact Stagger 0.1], Fire Bite [000A0A: Fire Bite 30; Perk Impact Stagger 0.3; Intense Flames Fear 99 / 15s], Poison Spray [00096C: Poison Spray 10 / 3s], Shock [000A1A: Shock 30; Perk Impact Stagger 0.3; Disintegrate 200 / 1s], Slight Force [000AA5: Unrelenting Force Weak 0.75; Generic Damage 2], Twister [000856: Twister 25], Viperbolt [00091F: Viperbolt 15], Weakness to Fire [000845: Weakness to Fire 25 / 30s], Weakness to Frost [000847: Weakness to Frost 25 / 30s], Weakness to Poison [000849: Weakness to Poison 25 / 30s], Weakness to Shock [00084B: Weakness to Shock 25 / 30s]
- Adep (8): Corrode Armor [000915: Corrode Armor 25 / 30s], Drain Magicka [000A1E: Drain Magicka 250 / 30s], Force [000AA6: Unrelenting Force Middle 1.25; Generic Damage 5], Poison Cloak [000950: Poison Cloak 10 / 60s], Poisonous Touch [000A16: Perk Impact Stagger 0.3; Poisonous Touch 10 / 6s], Potent Viperbolt [00093A: Potent Viperbolt 35], Weakness to Magic [00084F: Weakness to Magic 25 / 30s], Whirlwind [000857: Whirlwind 50]
- Expe (15): Arctic Blow [000A19: Arctic Blow 60; Perk Impact Stagger 0.3; Deep Freeze Paralyze / 3s], Deadly Viperbolt [00093B: Deadly Viperbolt 60], Dire Weakness to Fire [000846: Weakness to Fire 50 / 30s], Dire Weakness to Frost [000848: Weakness to Frost 50 / 30s], Dire Weakness to Poison [00084A: Weakness to Poison 50 / 30s], Dire Weakness to Shock [00084C: Weakness to Shock 50 / 30s], Disintegrate Armor [000916: Disintegrate Armor 50 / 30s], Disintegrate Weapon [000908: Disintegrate Weapon 25 / 30s], Mass Weakness to Fire [000AB5: Weakness to Fire 25 / 30s], Mass Weakness to Frost [000AB7: Weakness to Frost 25 / 30s], Mass Weakness to Shock [000AB9: Weakness to Shock 25 / 30s], Powerful Force [0009EF: Unrelenting Force Strong 1.5; Generic Damage 10; Unrelenting Force Middle 1.5], Scorching Blow [000A14: Scorching Blow 60; Perk Impact Stagger 0.3; Intense Flames Fear 99 / 15s], Stormhand [000A1B: Stormhand 60; Perk Impact Stagger 0.3; Disintegrate 200 / 1s], Withering Bolt [0009C0: Damage Health 70; Perk Impact Stagger 0.2]
- Mast (5): Conflagration [0009C4: CG Dragon Storm Call Self 10 / 60s; Conflagration 120 / 60s; It Burns Hysteria 20 / 60s], Dire Weakness to Magic [000850: Weakness to Magic 50 / 30s], Stormcell [0009C2: Storm Call Effect 2 10 / 60s; Stormcell 120 / 60s], Toxic Cloud [000A75: Toxic Cloud 10 / 10s], Whiteout [000972: CG Dragon Storm Call Self 10 / 60s; On Ice Paralyze / 60s; Whiteout 120 / 60s]

#### Illusion
- Novi (2): Command Lesser Creature [000A5D: Command Creature 50 / 60s], Void Gazer [000928: Night-Eye]
- Appr (5): Blind [000A55: Blind 100 / 60s], Command Creature [000AA9: Command Creature 100 / 60s], Command Lesser Undead [000A53: Command Undead 50 / 60s], Night-Eye [0009F7: Night-Eye / 60s], Throw Noise [000A00: Throw Noise]
- Adep (7): Calm Rune [000A6B: Calm Rune 20 / 30s], Command Greater Creature [000AAA: Command Creature 150 / 60s], Command Lesser Humanoid [000A5E: Command Humanoid 50 / 60s], Command Undead [000AAB: Command Undead 100 / 60s], Enduring Night-Eye [0009C8: Night-Eye / 300s], Fear Rune [000A71: Fear Rune 20 / 30s], Phantom Form [000A51: Phantom Form / 10s]
- Expe (5): Command Greater Undead [000AAC: Command Undead 150 / 60s], Command Humanoid [000A44: Command Humanoid 100 / 60s], Mass Blind [000A58: Blind 100 / 60s], Sanctuary [000A35: Sanctuary], Silence [000995: Silence 1000 / 20s]

#### Restoration
- Novi (2): Analyze [000ACD: Analyze / 1s], Invigoration [000809: Fortify Stamina Rate 25 / 300s]
- Appr (2): Absorb Stamina [00099B: Absorb Stamina 25 / 1s], Fortify Stamina [0009B0: Fortify Stamina 35 / 60s]
- Adep (7): Absorb Magicka [00099A: Absorb Magicka 20 / 1s], Cure Poison [000A9D: Cure Poison], Disease Immunity [0009EB: Resist Disease 100 / 300s], Fortify Health [0009AC: Fortify Health 35 / 60s], Greater Fortify Stamina [0009B1: Fortify Stamina 70 / 60s], Rapid Invigoration [000838: Fortify Stamina Rate 50 / 300s], Regeneration [000808: Fortify Healing Rate 25 / 300s]
- Expe (8): Absorb Health [000999: Absorb Health 15 / 1s], Cure Disease [000A9C: Cure Disease], Dispel [000991: Dispel 100], Dispel Other [000992: Dispel Other 100], Fortify Magicka [0009AE: Fortify Magicka 35 / 60s], Greater Fortify Health [0009AD: Fortify Health 70 / 60s], Reflect Damage [000968: Reflect Damage 20 / 25s], Spelldrinker [000966: Spell Absorption 25 / 25s]
- Mast (5): Greater Fortify Magicka [0009AF: Fortify Magicka 70 / 60s], Greater Spelldrinker [000B04: Spell Absorption 50 / 25s], Mass Dispel [000ABF: Mass Dispel 100], Rapid Regeneration [000837: Fortify Healing Rate 50 / 300s], Resurrection [0009A2: Resurrect Animation 100 / 6s; Resurrection]

#### Helper sub-spells (no tome, no tier)
- - (5): Conflagration [000952: Flames 50 / 1s], Etherialize [0009F0: Phantom Form / 10s], Poison Cloak [000951: Poison Cloak Damage 5 / 1s], Stormcell [0009C3: Stormcell 50 / 1s], Whiteout [000975: Whiteout 50 / 1s]

## 2. What Magic Expanded does structurally (scripting ceiling)
- Keeps the five Skyrim schools; no Mysticism. Mysticism effects (mark, recall, absorb, dispel, soul trap, telekinesis, reflect, teleport) sit in Alteration,
  Restoration or Conjuration (MGEF MagicSkill counts above). Poison spells are filed Destruction (Poison Spray/Cloak/Touch/Viperbolt) but Cure Poison is
  Restoration and Resist Poison Alteration.
- 145 spells: 84 use only stock archetypes (value modifier, cloak, bound, summon, light, spawn hazard, stagger, calm, demoralize, paralysis...) no script;
  25 reuse Skyrim's own FX scripts (magicAbsorbFXScript, DLC2CycloneEffectScript, magicNightEyeScript, magicSetActorAlphaScript, ImodScripts...);
  36 depend on the mod's own Papyrus (23 scripts in Magic.bsa, 45 of 191 MGEFs carry one): Mark/Recall, Teleportation x4, Bound armour x10 effects, Command x9,
  Jump x3, Slowfall, Swift Swim, Blind, Analyze, Resurrection, Phantom Form, Weather x3 (Weather.ForceActive), Timescale/Clocks x4, Damage Weapon.
  SKSE/PO3 Papyrus Extender (in our stack) is called by 3 scripts: Blind (PreventActorDetecting), Slowfall (local gravity, falls back to an ini float),
  LoadDetection. SPID distributes 37 spells to vanilla NPC classes/factions (assassins, priests, elemental mages, vampires...), the config quest
  `aaaMagicConfigQuest` (SkyUI MCM + tome/scroll/staff distribution into vanilla leveled lists at runtime, 25 tome lists) is in our allow-list.
- Most complex types: Mark/Recall (a placed marker ability, exclusion FLSTs of worldspaces and locations (ours would need adding), scene check, XP via
  AdvanceSkill); Teleportation (caster script scans for a placed activator within the spell radius and MoveTo); Command (level-ratio roll vs magnitude,
  faction + teammate flags, refund); Magistrate Levitate (Papyrus loop every 0.05 s moves two keyframed collision platforms under the caster and sets
  `fInAirFallingCharGravityMult`); Slowfall (gravity). Everything else is data. Our rule (CLAUDE.md): record first, Papyrus only for the generic
  scripts, own SKSE plugin where nothing does it. Proven pattern for a constant change: `ARG_NoHealthRegen` (Combat.cs:27-40, an Ability with a
  Value Modifier on HealRateMult added to the player base 000007, no script).

## 3. How the player gets spells today
- Starting: player base 000007 carries Healing, Flames, PCHealRateCombat, plus ours `ARG_NoHealthRegen`. The opening quest's TEST KIT
  (Generate.cs:21, 96; "removed with the authored opening, Phase 3") gives 14 ME spells (Mark, Recall, Hoptoad, Slowfall, Water Walking, Fire Bite, Entropic
  Bolt, Slight Force, Burden, Teleportation, Analyze, Dispel, Mass Soul Trap, Bound Shield) and Levitate. Owner ruling 2026-11-22: MN01 Dralin offers a
  pick of weapon kits or "an offensive spell tome". Owner 2026-10-30: reuse ME, do not build magic.
- Vendors: none. All 10 BM&V vendor factions use VendorItemsBlacksmith (8) or Apothecary (2), none the SpellTome keyword list; the only vendor of ours
  (ARG_VendorLooksAtBooks, list VendorItemsMisc) stocks books/items, no tome. The pre-pivot tome stock is gone. Loot: ME script adds tomes to
  vanilla LItemSpellTomes lists (reaches BM&V chests only if BM&V/our containers use those lists: not measured). SPID class/faction gifts: whether any
  BM&V NPC has those classes is not measured. Quest delivery exists: block `teach_spell` (AddSpell of our copy of a load-order spell), `add_perk`.
- Racial: ArgonianRace 013740 has RaceArgonianWaterbreathing (AbWaterbreathing), PowerArgonianHistskin (Power: Fortify HealRate 10 for 60 s,
  "recover health ten times faster"; CC Survival Mode adds a second effect if loaded), RaceArgonianResistDisease (50). BM&V does not change them: Black Marsh.esm's
  `ArgonianRaceDUPLICATE001` and Black Marsh North's `BMNagaRace` carry the same three; Loathial tribe has crSprigganPoisonClaw. The collection's
  Dark Souls Movement plugin changes race stamina regen only (5 -> 17 on all ten races). FLAG (formula, not tested in game): Histskin raises HealRate
  but our ability sets HealRateMult to 0, so natural regen is nil and Histskin may do nothing.
- Birthsigns: 13 Doomstone activators + DLC standing stones; BM&V places none (0 refs in its cells). Shouts/word walls/dragons: 75 vanilla + 42
  DLC/CC Shout records, 81+26 words; decision 0012 point 3 says shouts, word walls, standing stones and dragons do not exist for the player and the
  main-quest/dragon story nodes are shut off (shutdown.json); BM&V places 0 word walls. Only exception found: Valenwood's one "Whirlwind" tome. LT is
  bound to shout in the control scheme (owner-rulings 439). The voice/power slot can carry Hist powers (0012). Dragon souls: not obtainable.
- Collection: Rim Parry etc. give mechanism spells only (above).

## 4. Reusable look-and-sound material (record-only unless said)
EFSH recolour: colour keys in the record (fill/edge/particle) recolour with a new EFSH record; 74 vanilla + 32 DLC/CC + 2 mod shaders are colour-keys-only
(record-only), 95 + 79 + 12 use a palette gradient texture (MembranePaletteTexture / ParticlePaletteTexture): colour then lives in a dds (texture edit,
install-time per decision 0003). LIGH colour/radius, MGEF CastingLight, IMPS, SNDR picks: record-only. PROJ/EXPL/ARTO/VFX models: nif (or reference
shaders). Sound: 2,453 vanilla SNDR (147 MAG*), KoTM 75, dreughs 12: reuse by reference; we make no SFX.
- Poison/acid: ChaurusPoisonFXShader 10CC64 (green already, palette GradPoisonForm); Dragonborn spider poison family (DLC2ExpSpiderPoison*: 19 explosions,
  hazard, casting art, projectiles); KoTM Arachas acid sap/poison bomb, centipede venom spit, voriplasm acid, Kotu Gava "Acid" spit; vanilla DA13 Vile Vapor
  (DA13PoisonSprayProjectile), TrapPoisonGas/BloomGas explosions; ME's own poison cloak/spray.
- Spores/roots/sap/amber: Spriggan family (SprigganConcProjectile, SprigganBugDamageConcAimed bug spray, AbFXSpriggan, FXSprigganSwarm/Attachments art,
  Earth Mother variants, Spriggan summon SprigganCallEffect); KynesPeaceFXS 084B39 and ArgonianHistHealFXS 10F4A9 (Histskin's shader; both colour-only, particle
  FXGlowySparks); KoTM Spore Cloak (mihailarachascloak_spell + its EFSH), HistGhostFXShader 4A0F99 (VaporTile + GradGhostShader), Hist light set
  (ArgoniaHistFlowerLilacLight Color #B13EFF r256, HistGland, Marshroom blue/green), CC ccBGSSSE025 amber arrow projectile.
- Water/mist/rain: mihaildreughbundle is a finished Water school: 20 spells (Waterball, Torrent, Tidal Wave, Wall of Water, Rapids, Geyser, Rain Cloak, Water
  Rune, Water Cloak, atronach cloak) with 66 MGEF, 7 PROJ, 4 EXPL, 2 HAZD, 3 EFSH, 4 ARTO, 4 IMPS, 12 SNDR; vanilla fog/mist camera FX (FXCameraAttach
  FineMist/Fog/WispyFog/TurbulentFog), Dawnguard Vampire Mistform shaders, MQClearSkyFog hazard, WaterBreathingFXS, SteamFXShader, KoTM RainHistRainParticles (SPGD).
- Insects: HTBM Cipactli "Summon Fleshfly Swarm", Histgaunt, Miregaunt, Alux summons; Spriggan swarm; chaurus (ChaurusSpitProjectile, AbFXChaurus); KoTM
  giant centipede (call spells, 3 NPCs); no bee effect found (AmberBee is a misc item); wisp/will-o-wisp (mihailwillothewisp*, wispDeathExplosion).
- Disease/rot: KoTM 9 diseases (Swamp Rot, Swamp Fever, Naga Flu, Hist Fever, Sloughskin, Yellow Tick, Brain Fever, Ostraekeratic Fever, Chanthrax Blight) with
  effects DisDrain*/DisDamage*; BogBlightExplosion + Claws abilities; vanilla vampire plague effects.
- Mud/earth/ash: Dragonborn Ash (AshSpawn/AshShell/AshGuardian explosions, DLC02 ash particles), Havok rocks explosions, Dragonborn standing-stone FX, Crystal absorb.
- Shadow/Sithis: vanilla NightEyeFXHand, InvisFX, DLC1ShadowShieldFX, ExplosionIllusionDark, Nightingale Strife/Subterfuge projectiles, Soul Cairn shaders (26 shadow-like EFSH).
- Soul/ghost: ME Conjure Ghost/Soul Trap; vanilla Ghost*FXShader (19), MAGMysticismSoulTrap sounds; DLC1 Soul Tear (reanimate), Soul Cairn keeper/ghost shaders;
  HTBM Sea Ghost; KoTM AbHistGhost, HistGhostDeathFXShader, voriplasm ghost shaders.
- Lightning/wamasu: BM&V itself has NO wamasu (its races are vanilla + Naga/Loathial). KoTM/mihail wamasu: SummonSpectralWamasu, ConjureSpectralWamasu spell,
  mihailwamasu_spell1 Lightning Cloak, mihailwamasu_spell2 Chain Lightning (projectile + exp + 2 EFSH), NPCs Wamasu01/WamasuSpectral(Summonable); Cipactli Wamasu/Alpha;
  vanilla Shock set (ShockFXShaderNew, ChainLightning explosions, shock cloak art).
- Blood: DLC1 Drain Vitality/vampire drain (art, EFSH x18, projectiles), BloodSpray impact sets, CIPHTBMCipactliBlood.
- BM&V creatures/effects: Black Marsh.esm holds 0 spells/MGEF/perks (races, books, 3 ingredients only); Valenwood 1 spell + 1 MGEF (Whirlwind). Its creatures are vanilla
  races (spriggan, chaurus, slaughterfish, werebear, hagraven, Naga, Loathial), so all effects above come from vanilla/DLC or the new-world mods.
- Status of the creature mods: KoTM, HTBM(+Cipactli), dreughs, Lamia, Nix are `newworld` group in dependencies.json (records read for places); they are NOT in the
  NewWorld/Argonia MO2 plugins.txt (30 plugins) and not masters in the committed Argonia.esp; using their spells means adding them as masters (not verified).

## 5. Systems a flavour layer can hang on with records only
- Alchemy: vanilla 97 ingredients + DLC 142 (+ Update 4); BM&V Poison Bloom x2; KoTM 9 (Hist Sap Shiner, Snail Mucus...), Cipactli 37 (Bloatspore, Stinkhorn Cap, Muck, Bog Beacon
  Cap, Swamp Pad, Rootworm Jelly, Grey Sithis' Beard, Somnalius Frond), Shroom Beetles 9. Potions: vanilla 363 ingestibles; poisons: 11 vanilla + 6 KoTM + 3 Cipactli (Poison-type SPEL).
- Hist Sap EXISTS as items: KoTM Ingestible `HistSap` 394B35 (Slow 55% 45 s, Fortify Health 200 for 45 s, Drugged 45 s; value 100); Cipactli `CIPHTBMJungleHistSap`
  (Slow 30, Fortify Health 125, Drugged 60), Hist Bloom (Fortify Illusion 50 +100 s, Damage Stamina), Hist Fruit (Fortify Illusion 200); KoTM Bog Brew (cure poison, fortify magicka 20),
  Jeel-Sa/Tee-Lel (weakness), Kotu Gava Nectar (cure disease, paralysis 15 s). Dragonborn's Sleeping Tree sap effects are what they reuse.
- Enchantments: ObjectEffect records above; powers: 28 vanilla Power + 3 lesser (racial powers incl. Histskin, Redguard, Dunmer flame cloak..., Nightingale, vampire, werewolf)
  + DLC 21 + 18; abilities 253 + 213; Voice 115 + 60. Standing-stone/blessing analogues: 13 vanilla Doomstone activators with ability spells, 6 Dragonborn stone Powers, Black Book
  powers x8, Blades/shrine blessing abilities (3), Dragonborn "MorasGrasp".
- SPID 7.3.3 installed (po3_SpellPerkItemDistributor.dll); two INIs exist (Magic_DISTR 37 spells, RimParryPerk_DISTR); it can give spells/perks/items to NPCs by faction/class/keyword
  with no script. Quest-delivered: `teach_spell`, `add_perk`, `learn_ingredient`, `open_recipe` (blocks.md:62-69).
- Leftover, not loaded: ArgoniaPerks.esp in Data (273 perk renames, pre-pivot install-time file; not in plugins.txt).

## Recommendations
- Fix the Histskin/HealRateMult interaction check before building on Histskin (evidence: PowerArgonianHistskin effect HealRate +10; Combat.cs:27-40 HealRateMult 0): one owner check.
- Treat the mihail dreugh Water school and KoTM wamasu/arachas/spore spells as the cheapest Argonian-flavour spells: complete records, no script, only need master additions
  (spell + tome records of ours can reference them; recolour only EFSH/LIGH).
- Extend Mark/Recall's `aaaMagicExclusionWorldSpaces` and Locations FLSTs with our worldspaces by an override record (data only).
- Any vendor selling tomes needs the faction's VendorBuySellList to include VendorItemSpellTome (0937A5); BM&V's 10 vendor factions have none.

Covered: Skyrim, Update, Dawnguard, Dragonborn, HearthFires, ccFish/AdvDSGS/Curios/Survival, Magic.esp (+bsa scripts), BM&V (3 plugins), KoTM, HTBM x2, mihail dreugh/nix, Lamia, USSEP, ArgoniaPerks, our plugin (Spells, Npcs, Combat.cs, Generate.cs), soulslike plugins by GRUP walk, repo docs · Skipped: Magistrate Levitate record fields (parser refused; strings only), Tropical Skyrim/Depths/Shroom/Medusa spells (none or irrelevant), in-game behaviour (nothing run).
