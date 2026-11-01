# Lane 1.15-creatures: report

Brief: [briefs/1.15-creatures.md](briefs/1.15-creatures.md). Sessions 1 and 2, 2026-11-01.

## The vanilla measurement

`python3 -m tools.argonia_world.vanilla.creatures --json out/creatures/vanilla.json` takes 7 s (Skyrim.esm actors
are cached at ~/.cache/argonia-vanilla/actors.pkl; the Tamriel cache is load.py's).

- **Refs.** Tamriel holds 4,362 exterior creature ACHRs. 45.5% have a levelled-list template; the rest are single
  creatures.
- **Density per 100 cells, by terrain class.** Shore 105, forest 96, open 26, mountain 21, water 8.7. An occupied
  cell holds 1 ref at the median and 3 at p90.
- **Levelled lists.** There are 72 creature lists, and every one has chance none 0. Entries run 2 / 4 / 13 at
  p10 / p50 / p90. Prey lists use a single level (1). Predator lists use 7–17 levels, from 1 to 35, with flags 3
  (levels at or below the player's, all entries). Example: LCharAnimalForestPredator has 26 entries over 15 levels.
- **Encounter zones.** There are 280 ECZN records. 61 never reset, 270 carry a location, 98% have max level 0, and
  min levels are mostly 6 or 8. Only 4 exterior cells and 291 interiors carry an XEZN. Zones belong to places;
  the wild is unzoned.
- **Dens.** 32% of creature refs stand within 60 m of a door, and the door distance runs 15 / 93 / 185 m at
  p10 / p50 / p90.
- **Hostility.** 25% of refs are hostile overall: open 19%, forest 22%, shore 29%, water 57%.
- **Not usable.** Distance to a named cell is useless because most Tamriel cells carry an editor ID.
- **Roads and day/night** (`python3 -m tools.argonia_world.vanilla.creature_habits`, 28 s uncached). Of 2,925
  creature ACHRs, 7.8% stand within 512 units (7 m) of a road vertex; the distance runs 10.6 / 84.7 / 117 m at
  p10 / p50 / p90, and 42% have no road in their 3 x 3 cells. Roads are LTEX LDirtPath01, LDirtSnowPath01 and
  LSnowCobble01 at opacity 0.5 or more. All 206 creature NPC_ behind the refs are all-day: 10 have a sleep package
  beside unscheduled ones, 2 have a scheduled package, and 114 have none. **Rule:** no day/night split and no road
  attraction. Our no-spawn radii already keep spawns off settled ground.
- **Verdict.** We use the same method. We differ deliberately in one way: our levels are fixed per band, never
  scaled to the player (76 §128).

## Inventory

`python3 -m tools.argonia_world.creatures inventory` takes 3 s. It writes out/creatures/inventory.json, which is
not committed.

| Plugin | Creature NPC_ (new) | Exterior refs | In water | Grouped within 15 m |
|---|---|---|---|---|
| Black Marsh.esm | 61 (55) | 458 | 169 | 223 |
| King of the Murkmire | 106 (106) | 529 | 139 | 217 |
| HTBM | 38 (38) | 310 | 85 | 163 |
| HTBM Curse of Cipactli | 87 (87) | 639 | 53 | 469 |
| Depths of Skyrim | 2 | 3 | 3 | 3 |
| Tropical Skyrim Birds | 42 (42) | 495 | 0 | 261 |

The modders group their creatures heavily: Cipactli places 73% of its exterior refs grouped. Water creatures sit
in water. Habits per mod, measured in each mod's own worldspace (creature_habits.py):

| Plugin | Refs | Slope p50 / p90 / max (deg) | Tree distance p10 / p50 / p90 (m) | Day/night |
|---|---|---|---|---|
| King of the Murkmire | 589 | 5.1 / 10.6 / 39.1 | 3.4 / 6.5 / 30.2 | all-day |
| Black Marsh.esm | 750 | 0.0 / 10.3 / 78.9 | 1.5 / 6.8 / 20.9 | all-day |
| HTBM Curse of Cipactli | 565 | 3.6 / 17.4 / 65.0 | 3.3 / 9.9 / 39.6 | all-day |

The modders stand creatures near trees (6.5–9.9 m at the median) and on gentle ground (p90 10–17 degrees). Both
habits support the cover rule below: 8 m is their median tree distance. The slope caps in creature_spawn_rule
(30–90 degrees) are not tightened, because the mods' maxima reach 39–79 degrees.

74 mod forms are joined to 34 creature kinds (`creature_form`). Seven new kinds come from the lore, each with a
fact id in its `why_here`: singing frog, dragon frog, burglar crab, marsh turtle, giant centipede, giant snail and
marsh bird.

Kinds per region class: coastal-lagoon 12, northern-transition 13, deep-river-corridor 15, western-frontier 15,
tidal-delta 16, rootland 22, deep-sink-basin 22, interior-swamp 23, flooded-forest 25.

Three kinds have no actor form and are left out of the lists (roster.NO_FORM): osheeja-gar and torchbug are
critters, and medusa is placed by its place record.

## Placement rules (creatures/place.py; each source in its docstring)

- **Lists.** Each list is `lvln.<class>.<band>.<medium>`, with every entry at the band's level and chance none 0.
  There are 81 lists and 639 entries.
- **Spawn count.** A cell's expected spawns are the band's value (D1 1.0 down to D5 0.2) × 0.09 on a cell more
  than half under water (vanilla's water/shore ratio).
- **Medium.** The medium is chosen by eligible vertices, with water weighted 0.1. A list ref must suit the
  strictest of its entries.
- **No-spawn radius.** Each place class has one (place_no_spawn, 25–150 m).
- **Band.** A cell's band is the most common tier among its 5 nearest places, capped at D4. The first cut used
  the nearest place alone, which made whole dungeon surrounds D5 and empty.
- **Dens.** A den marker carries its creature (the first mod form) within 6 m.
- **Zones.** Each band has a wild zone (onRest) and a clearable zone (untilCleared).
- **Water classes** (session 2). On tidal-delta and deep-river-corridor cells, water is the creatures' home. Skyrim's
  open-water cut (×0.09 count, 0.1 medium weight) does not apply there. Before this change those classes had 19
  refs in 50 cells and 9 in 45.
- **Cover and ambush** (session 2). A vertex is bush when 3 or more vegetation stems lie within 8 m. That is 60% of
  a vanilla forested cell's p95 stem density, and 8 m is the mods' median tree distance. A list whose entries are
  mostly hostile spawns in the bush; this is the ambush point, after 74-ecology's ambushers. Other lists spawn in
  the open. On the 1.15 sample: 99 bush, 4 open, and 21 untagged where the medium has no such vertex.

## Counts

| Run | Cells | Refs | Spawn refs | Dens (each with its predator) | Time |
|---|---|---|---|---|---|
| Sample (SAMPLE_1_15) | 352 | 205 | 167 | 19 | 15 s check |
| Province | 15,876 | 6,138 | 4,612 | 763 | 20 s plan, 39 s with checks |

Province refs by medium: land 3,943, shore 1,648, water 547.

## Band → effect

Afflictions are in `creature_affliction` (6 diseases from fauna-hazards "Diseases", plus 5 poisons). The band →
creature → affliction rows are in `danger_band_effect` (21 rows). Their `spell_form` is NULL everywhere: the mods'
`spell_form` is now set on every row (records.spell_form). Four afflictions use the mods' own SPEL: Swamp Rot and
Swamp Fever (KotM DiseaseSwampRot / DiseaseSwampFever), Adder Venom (Cipactli mihailsnakepoisonVIPER) and
Centipede Numbing (KotM mihailgiantcentipede_poisonspit_spell). The other seven are ours, in ArgoniaWorld.esm at
0x0D3000+. Each is one MGEF per actor value plus a SPEL, copying Skyrim.esm's own shapes. Diseases are SPIT 1,
constant, contact, PeakValueModifier 25 or a regen ×2.5 (Rattles). Poisons are SPIT 5, contact, ValueModifier
5–7 points over 5–7 s (crChaurusPoisonBite). Why: no mod ships these afflictions.

## The records (session 2)

ArgoniaWorld.esm holds the creature records, with KotM, Cipactli, Black Marsh.esm and TS Birds as masters (the
planner's ruling). records.py turns the rows into world.json's "creatures" section and into the splice shards:
- LandWorld.cs → CreatureRecords.Add writes 81 LVLN (LVLF 3, entries at the band level), 81 NPC_ templated on them
  (template flags 0x1FFF, RNAM FoxRace: Skyrim.esm's shape for all 451 of its LVLN-templated NPC_) and 10 ECZN
  (min = max).
- `ArgoniaGen creatures` splices spawn and predator ACHRs (NAME, XEZN, DATA) and den REFRs (XMarkerHeading) into
  each cell's Temporary group, through VegetationRecords.Splice.
- `creatures readback` compares the count per cell through Mutagen with the planner's.

Ids are computed, never allocated: lists at 0x0D0000, templates 0x0D1000, zones 0x0D2000, refs 0xE00000 +
cell × 64.

## What 1.14 must read

- `encounter_zone.respawn`: `untilCleared` zones get never-resets once their place is cleared.
- `place.hostility_clearable`.
- `core_respawn_class`.

## Starting state (hand-off)

**Done (session 2).**
- The records: ArgoniaGen and the pipeline stage are built, `dotnet build` has 0 errors, and readback is wired.
- Sourcing register rows exist for the 4 mods' 74 forms.
- The checks.md 1.15 §g row's evidence is journey:creature-walk.
- Habits are measured (creature_habits.py). The rules: no day/night split, no road rule, slope caps kept.
- Cover and ambush points are built.
- Afflictions are realised (spell_form set; 7 MGEF/SPEL of ours).
- Water classes have a full density rule.
- `pytest tools/argonia_world/creatures` passes 9 tests. `creatures check` is 5 green on the sample in 8.9 s.

**Owed.**
1. `make plugin-check` with the creature stage: see the return line. Re-pin
   tools/argonia_world/terrain/sample-manifest.json deliberately once the sample hash changes for the creature
   records.
2. (Done.) Province after the water-class rule took 22 s: 6,115 refs. Tidal-delta now has 36 refs in 50 cells and
   deep-river-corridor 33 in 45, about 0.7 per cell, which is their D2–D3 band's value. Cover: 1,501 bush and 679
   open. The rest are untagged, because the province vegetation shards are partial while terrain rebuilds.
3. The L4 checks are owed to the round's batch: creature-walk, and the first load with the ESP masters.
4. 1.14 applies the afflictions on hit (the spell_form is data). The creatures carry no spell yet.
