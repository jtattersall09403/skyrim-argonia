# Lane 1.15-creatures: report

Brief: [briefs/1.15-creatures.md](briefs/1.15-creatures.md). Session 1, 2026-11-01.

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
- **Not usable yet.** Distance to a named cell is useless because most Tamriel cells carry an editor ID. Road
  distance and day/night packages are not measured yet (owed).
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
in water. Slope, tree distance and day/night packages per mod are owed.

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

## Counts

| Run | Cells | Refs | Spawn refs | Dens (each with its predator) | Time |
|---|---|---|---|---|---|
| Sample (SAMPLE_1_15) | 352 | 205 | 167 | 19 | 15 s check |
| Province | 15,876 | 6,138 | 4,612 | 763 | 20 s plan, 39 s with checks |

Province refs by medium: land 3,943, shore 1,648, water 547.

## Band → effect

Afflictions are in `creature_affliction` (6 diseases from fauna-hazards "Diseases", plus 5 poisons). The band →
creature → affliction rows are in `danger_band_effect` (21 rows). Their `spell_form` is NULL everywhere: the mods'
own SPEL forms have not been read yet (owed).

## What 1.14 must read

- `encounter_zone.respawn`: `untilCleared` zones get never-resets once their place is cleared.
- `place.hostility_clearable`.
- `core_respawn_class`.

## Starting state (hand-off)

**Done.** These are green:
- the measurement;
- the inventory;
- the schema: 10 tables, seeded;
- the planner;
- `creatures check`: 5 checks green on the sample in 15 s;
- `pytest tools/argonia_world/creatures`: 7 passed;
- `db check`;
- `tests/journeys/creature-walk.yaml`: 14 steps, `--dry` ok. It is generated by
  `python3 -m tools.argonia_world.creatures.journey` from out/creatures/spawns.jsonl.

**Owed.**
1. ArgoniaGen records. This needs NPC_ templates over each LVLN, plus LVLN, ECZN and ACHR (with XEZN) spliced in
   the way VegetationRecords.cs does it, and a pipeline stage. Open question: ArgoniaWorld.esm would need KotM,
   Cipactli, BM and Birds as masters, or a separate ArgoniaCreatures.esp. Rule on that first. `make plugin-check`
   is not yet run.
2. Sourcing register rows for every mod creature form (data/sourcing-register.json).
3. A row in the checks.md ledger for creature-walk.
4. The mod-placement habits not yet measured: slope, tree distance, day/night packages. Also roads and vanilla
   day/night.
5. Bush/open cover from the vegetation density, and ambush points by hostility.
6. Afflictions realised as the mods' SPEL forms where they exist.
7. Thin classes: tidal-delta (19 refs) and deep-river-corridor (9) are few in the province. Check their cells'
   bands and lists.
