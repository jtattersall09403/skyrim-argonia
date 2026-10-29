<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.10-loops/zones.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: zones and owners (2.10 § Loops, lane 2.10-z)

Rule (decision 0151 item 3; contract lanes/2.10/briefs/rules.md; world/98
Lock, Zone and Watch rows): every door and lid of a slice place has a
locks.json row (class `none` for an open thing) naming its owner and
`opens {place, ref}` on a ref the place's bundle carries; every home, store
and counting house is a zone with its owner and hours from the people's day
(2.4); every slice place carries `watch` (a row, or null with
`watchReason`); every key item is carried (`carriedBy`) or placed (a socket's
lootTable); every day-lock door's key has its row. Eyes: none.

Measures:

- `cd tooling/world-generation && python3 -m worldgen.stealth_views --check` (the integrity gate)
- `cd packages/game-core && npx vitest run src/people/dayLockKeys.test.ts`

| Place | Doors / lids | Zones | Watch | Keys | Result | Elapsed |
|---|---|---|---|---|---|---|
| place.dunmer-north.riverwalk | 2 / 11, 13 rows (none, simple) | 2 | faction.an-xileel | 3 | green | 0.2 s (one gate run) |
| place.dunmer-north.the-wamasu-shrine | 0 / 2, 2 rows (none, unpickable-key) | 0 | null (reason) | 0 | green | 0.2 s (one gate run) |
| place.hist-heartland.greenspring | 6 / 35, 41 rows (none, simple) | 5 | null (reason) | 4 | green | 0.2 s (one gate run) |
| place.imperial-fringe.bog-iron-workings | 1 / 8, 9 rows (none, simple) | 1 | null (reason) | 1 | green | 0.2 s (one gate run) |
| place.imperial-fringe.claywater-station | 4 / 13, 17 rows (none, simple) | 3 | null (reason) | 2 | green | 0.2 s (one gate run) |
| place.imperial-fringe.the-broke-column | 0 / 2, 2 rows (none) | 0 | faction.imperial-legion-remnant | 0 | green | 0.2 s (one gate run) |
| place.imperial-penal-south.rose-bone-waystation | 1 / 9, 10 rows (none, simple) | 1 | null (reason) | 1 | green | 0.2 s (one gate run) |
| place.imperial-penal-south.voriplasm-vault | 1 / 0, 1 rows (none) | 0 | null (reason) | 0 | green | 0.2 s (one gate run) |
| place.mercantile-coast.chasepoint | 5 / 25, 30 rows (hard, none, simple) | 5 | null (reason) | 4 | green | 0.2 s (one gate run) |
| place.mercantile-coast.lighter-flotilla | 1 / 0, 1 rows (none) | 0 | faction.reed-sail-compact | 0 | green | 0.2 s (one gate run) |
| place.mercantile-coast.teeth-of-sithis | 2 / 0, 2 rows (none) | 0 | faction.nisswo | 0 | green | 0.2 s (one gate run) |
| place.naga-kur-deeps.naga-highway-camp-active-north | 0 / 9, 9 rows (hard, none) | 0 | null (reason) | 0 | green | 0.2 s (one gate run) |
| place.pirate-freeholds.opening-work-camp | 2 / 11, 13 rows (none, simple) | 1 | faction.dres-remnant | 2 | green | 0.2 s (one gate run) |
| place.pirate-freeholds.upriver-hist-village | 11 / 16, 27 rows (none, simple) | 10 | null (reason) | 5 | green | 0.2 s (one gate run) |
| place.saxhleel-coast.jungle-root-hollow | 1 / 0, 1 rows (none) | 0 | null (reason) | 0 | green | 0.2 s (one gate run) |
| place.saxhleel-coast.pearl-lots | 0 / 5, 5 rows (none) | 0 | null (reason) | 0 | green | 0.2 s (one gate run) |
| place.route.archon-gideon-mere-neck | route corridor: no catalogue record, no doors or lids | - | - | - | out of scope (no record) | - |
| place.route.border-road-greenspring-crossings | route corridor: no catalogue record, no doors or lids | - | - | - | out of scope (no record) | - |
