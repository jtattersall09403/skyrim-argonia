<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.10-loops/records.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: stealth, crime and lock records (2.10 § Loops, lane 2.10-a)

Rule (world/76 §118, §121.5, §124; decisions 0092, 0151, 0039; contract
lanes/2.10/briefs/rules.md): detection, locks, traps, the Owing and the
pickpocket chance are home tables in `world/sources/registries/`
(`detection.json`, `locks.json`, `traps.json`, `owing.json`,
`pickpocket.json`); `worldgen.stealth_views` validates them and writes the
views under `packages/game-core/src/{perception,interaction,crime}/data/`.
A creature's sense ranges stay in `creatures.json`. Every number names its
passage; a number the design lacks is a named blocker, never a tuned one.
Eyes: none (data and numbers only).

Measures:

- `cd tooling/world-generation && python3 -m worldgen.stealth_views --check`
- `cd tooling/world-generation && python3 -m pytest -q worldgen/test_stealth_views.py`
- `cd packages/game-core && npx vitest run src/perception/data src/interaction/data src/crime/data`
- `cd tooling/world-generation && python3 -m worldgen.item_views --check`

| Measurement | Bar | Result | Elapsed | Capture |
|---|---|---|---|---|
| A whole profile (spot, cone, sight, hearing, scent, alarm radius, search timeout) for the person, every enemy archetype and every creature with `notice` | 1 + 11 + 42 | 54 profiles | 0.2 s | `stealth_views --check`; `detection.test.ts` |
| Noise tables: gait 4, armour class 4, a surface factor for every physical material | 4, 4, 14 | 4, 4, 14 (surface all 1: blocker) | 0.2 s | `test_stealth_views.py` |
| Light rows ascending, sneak-attack bands = world/76 §121.5, one-shot exclusions, eye mapping, searching multiplier | all present | 4 light rows, 6 bands x 7 classes, 4 exclusions, 5 eye keys, ×1 | 0.2 s | `test_stealth_views.py` |
| Locks: class, opens {place, ref}, owner on every row; key names its lock back; world-schema locks.v1 | 3 of 3 | 3 of 3 | 0.2 s | `test_stealth_views.py` |
| Pick and probe quality from Morrowind (apprentice grades) | item.lockpick 1.0, item.probe 0.5 | 1.0, 0.5; `item_views` reds a missing quality | 0.14 s | `item_views --check` |
| Trap kinds: Morrowind's trapped-lock spells, each an effects.json effect with its 2.9 family | ≥ fire, frost, shock, poison, paralysis | 7 (+ lifeforce, silence) | 0.2 s | `locksTraps.test.ts` |
| Owing: one row per catalogue region, assessor a faction, amnesty 72, rates or a named blocker | 8 regions | 8 rows, 0 complete, 8 blocked (§124 carries no rates; the Rose has no assessor faction) | 0.2 s | `crime.test.ts` |
| Pickpocket rows per the contract | base, targetSpot, bands, exclude | present, from Skyrim's GMSTs (§118 and §121.5 carry none) | 0.2 s | `crime.test.ts` |
| Place record zones and watch: world-schema place-crime.v1 and the catalogue check | fixture green, three reds | green; zone id, volume and watch region red | 1.2 s | `test_stealth_views.py` |
| The gate reds a trap with no effect, a lock with a missing key item, a profile with no search timeout, an owing gap with no blocker, and every unresolved reference | 4 + 8 reds | 12 reds, one line each | 1.2 s | `test_stealth_views.py` |
| Generator check green, views current | green | green | 0.2 s | `stealth_views --check` |
