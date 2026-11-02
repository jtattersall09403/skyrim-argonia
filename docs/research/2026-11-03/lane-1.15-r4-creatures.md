# Lane 1.15-r4-creatures: report

Brief: [briefs/1.15-r4-creatures.md](briefs/1.15-r4-creatures.md). Owner play test 3, finding 13: "very sparse, only
hackwings and giant centipedes". One session, 2026-11-03.

## Vanilla, measured (0034)

`python3 -m tools.argonia_world.vanilla.creatures` (10 s, cached). Skyrim.esm's Tamriel holds 4,362 exterior creature refs (45.5% levelled lists).
Refs per 100 cells by terrain class: shore 105.16, forest 95.87, open 25.90, mountain 20.78, water 8.72. An occupied
cell holds 1 / 1 / 3 refs at p10 / p50 / p90. The 72 creature lists hold 2 / 4 / 12.8 entries at p10 / p50 / p90, and all
have chance none 0. Prey and predators mix in one list: LCharAmbientCreatures has 5 entries and 367 refs, and
LCharAnimalForestPredator has 26. Of the creature refs, 32% stand within 60 m of a door. Road distance is 10.6 / 84.7 /
117 m at p10 / p50 / p90 (creature_habits, earlier lane). Hostile refs: 25% overall, 57% in water.
The mods' own worldspaces (inventory, earlier lane, unchanged):

| Plugin | Exterior refs | In water | Grouped within 15 m |
|---|---|---|---|
| Black Marsh.esm | 458 | 169 | 223 |
| King of the Murkmire | 529 | 139 | 217 |
| HTBM | 310 | 85 | 163 |
| HTBM Curse of Cipactli | 639 | 53 | 469 |
| TS Birds | 495 | 0 | 261 |

In those worldspaces, refs stand 6.5–9.9 m from a tree at the median and on slopes of 10–17 degrees at p90.

## Causes

1. **Thin lists.** seed.py (before, the list loop at old lines 98–109) put a kind only in the lists of the
   bands it names exactly. A D2 or D3 land list of the coast, delta and interior swamp was hackwing plus fleshfly.
   The D3 land list of deep-sink, flooded-forest and rootland was giant centipede, giant wasp and fleshfly. Of the
   81 lists, 30 held 1 or 2 kinds. The walked shores are D2–D4, so the owner met exactly those land lists.
2. **Low density.** roster.BANDS (before, roster.py:160) set the spawns per cell at D1 1.0, D2 0.8, D3 0.6,
   D4 0.4 and D5 0.2. The sample measured 0.35 spawn refs per cell. Per 100 cells: shore 54.1 (vanilla 105.16),
   forest 73.3 (95.87), water 6.0 (8.72).
3. **Shore under-drawn.** place.py plan_cell weighted media by their count of eligible vertices. A cell's shore band
   is thin, so most spawns drew the thin land list, not the shore lists (crocodile, frogs, turtles, birds).
4. **Apex in the lists.** Wamasu, kaj-thux, miregaunt and marsh giant (creature.kind 'apex') were in the D3/D4 spawn
   lists as well as at their dens. Near the rootland and deep-sink shores, every reachable kind was an apex kind
   (5 and 6 kinds).

No habitat filter failed and no ref sat inside a no-spawn radius: `creatures check` habitat and no_spawn were green before.

## What changed

- `seed.derive_lists` (seed.py) rebuilds the lists from the database rows. A list (class, band, medium) holds every kind of
  its class and medium whose lowest band is at or below the list's band (Skyrim.esm's mixed prey and predator
  lists). No apex kind is in any list: apex kinds appear only at their dens, at 1.5 dens per 100 cells. The result is
  125 lists and 1,647 entries, all at level 1 (0035). The old count was 81 lists and 639 entries.
  `python3 -m tools.argonia_world.creatures lists` rewrites the lists without the laid stack.
- roster.BANDS: every band now has 1.2 spawns per cell, vanilla's densest class (shore 1.05) plus a margin. Danger
  comes from the list, never from the count. The water-cell cut (×0.09) stays, giving 0.108 against vanilla's 0.087.
- place.SHORE_WEIGHT = 105.16 / 25.90 (4.06): a shore vertex is weighted as Skyrim's shore cells weigh against its
  open ones.
- checks.py gains `lists` (each class's lists hold 12 or more kinds, and no list holds an apex kind) and `density`
  (spawn refs per 100 sampled cells by vanilla's own terrain cut, at or above vanilla where a class has 20 or
  more cells). tests/test_lists.py adds L1 and L2 tests.
- tests/journeys/creature-spots.yaml was regenerated on the new plan, and a checks.md row was added under 1.15.

## Before / after

Sample (SAMPLE_1_15, 352 cells), spawn refs per 100 cells (vanilla in brackets):

| Terrain | Cells | Before | After |
|---|---|---|---|
| shore | 109 | 54.1 | 111.9 (105.16) |
| forest | 30 | 73.3 | 130.0 (95.87) |
| water | 116 | 6.0 | 10.3 (8.72) |
| mountain | 82 | 62.2 | 97.6 (20.78) |
| open | 10 | 20.0 | 90.0 (25.90) |

Refs went from 162 to 279. `creatures check`: 8 green in 20 s (it was 6 checks; the 2 new ones are red on the old data).

Kinds within 200 m of each region-save shore marker (`ARG_Ref_Panel<Region>Shore`, panel.vantages). The planner ran
over ±4 cells around each marker. "Possible" counts every kind a ref there can spawn. "Met" is the mean count of
distinct kinds over 50 draws of one entry per ref.

| Region shore | Refs before → after | Possible before → after | Met before → after |
|---|---|---|---|
| coastal-lagoon | 10 → 13 | 18 → 23 | 8.1 → 9.1 |
| deep-river-corridor | 21 → 35 | 17 → 23 | 12.3 → 16.4 |
| deep-sink-basin | 15 → 34 | 6 → 21 | 4.9 → 13.2 |
| flooded-forest | 22 → 39 | 11 → 21 | 9.6 → 15.9 |
| interior-swamp | 16 → 28 | 12 → 27 | 9.2 → 16.1 |
| northern-transition | 22 → 31 | 16 → 24 | 10.4 → 16.1 |
| rootland | 13 → 47 | 5 → 22 | 4.1 → 17.6 |
| tidal-delta | 15 → 19 | 17 → 25 | 10.1 → 13.3 |
| western-frontier | 17 → 22 | 15 → 15 | 10.2 → 10.8 |

Kinds in each class's lists after the change: coastal-lagoon 12, northern-transition 13, deep-river-corridor 14,
western-frontier 15, tidal-delta 16, rootland 18, deep-sink-basin 19, flooded-forest 21, interior-swamp 21. All are
cited through creature_region_class.why (74-ecology or a dossier fact id). The apex kinds are now den-only, so these
counts sit below the earlier totals (12 to 25).

## Owed

- In game: `creature-spots` (tests/journeys/creature-spots.yaml) in the planner's batch on the round-4 build. A
  checks.md row is added under 1.15 ("Creature variety and density after round 4").
- Plugin: lists 0x0D0000+ and templates 0x0D1000+ grow from 81 to 125. The next province plugin build carries this
  change. The sample-manifest hash moves with `make plugin-check` (see the return).
- Not done: group sizes. A spawn ref is one actor; the roster's group_min and group_max are unused, and vanilla's
  occupied-cell p90 is 3. Owed as P2.
