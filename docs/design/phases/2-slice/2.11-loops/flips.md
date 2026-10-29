<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.11-loops/flips.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Stance flips (2.11 narrative)

Generated from the catalogue `hostility` blocks (`world/sources/catalogue/places-*.json`) by the stance view (`packages/narrative/src/stance/stance.ts`). Reading rule: baseline first, then each `place`-scope flip whose `when` holds in authored order; the last holding flip wins. Flips of scope `occupantGroup` and `namedRole` change no place stance (`heldFlips` lists them for the greeting and the watch). Respawn is the block's class (`none` stays cleared; any other class is refilled by `StanceView.refill` from the system that owns it); no timings are stated by the catalogue, so none are invented.

A flip is reachable when its condition is a quests/85 term in the exact vocabulary shape (operator `≥`; `deedCountAtLeast` takes faction, deed, count), which `worldgen.quests --check` enforces over every catalogue flip, and every flag it reads is set by some quest data under `world/sources/quests` (a `flag` term with no setter is marked **no setter**).

## Slice places

| place | baseline | owner | clearable | respawn | flips (to, scope: condition) |
|---|---|---|---|---|---|
| place.dunmer-north.riverwalk | wary | none | no | none | none |
| place.dunmer-north.the-wamasu-shrine | sanctuary | none | no | none | none |
| place.hist-heartland.greenspring | friendly | none | no | none | none |
| place.hist-heartland.helstrom | friendly | faction.many-root-conclave | no | none | guarded, place: notorietyTier "region.helstrom", "known"<br>hostile, place: notorietyTier "region.helstrom", "hunted" |
| place.imperial-fringe.bog-iron-workings | guarded | none | no | none | none |
| place.imperial-fringe.claywater-station | guarded | none | no | none | none |
| place.imperial-fringe.the-broke-column | hostile | faction.imperial-legion-remnant | yes | slow | wary, place: flag "flag.broke-column.pardon-offered", true **no setter** |
| place.imperial-penal-south.rose-bone-waystation | neutral | none | no | none | none |
| place.imperial-penal-south.voriplasm-vault | hostile | none | yes | none | none |
| place.mercantile-coast.chasepoint | guarded | faction.unclaimed | no | none | hostile, occupantGroup: flag "flag.coast.long-bar-exposed", true **no setter** |
| place.mercantile-coast.lighter-flotilla | wary | faction.reed-sail-compact | no | none | friendly, place: factionRankAtLeast "faction.reed-sail-compact", 1 |
| place.mercantile-coast.teeth-of-sithis | hostile | faction.nisswo | yes | faction-refills | sanctuary, place: factionRankAtLeast "faction.nisswo", 1<br>hostile, place: deedCountAtLeast "faction.nisswo", "deed.nisswo.rite-broken", 1 |
| place.naga-kur-deeps.naga-highway-camp-active-north | hostile | faction.tribeless-naga | yes | faction-refills | guarded, place: goldAtLeast 200<br>neutral, place: factionRankAtLeast "faction.tribeless-naga", 1 |
| place.pirate-freeholds.opening-work-camp | wary | faction.dres-remnant | no | none | friendly, place: questStage "quest.main.mq01", "\u2265", 60 |
| place.pirate-freeholds.upriver-hist-village | wary | none | no | none | friendly, place: questStage "quest.main.mq01", "\u2265", 40 |
| place.route.archon-gideon-mere-neck | none in catalogue | | | | |
| place.route.border-road-greenspring-crossings | none in catalogue | | | | |
| place.saxhleel-coast.jungle-root-hollow | hostile | none | yes | slow | none |
| place.saxhleel-coast.pearl-lots | neutral | none | no | none | none |

Slice places: 19 (17 with a catalogue block, 2 route places with none); flips on them: 11 (10 place scope, 1 other scope); flips whose flag has no setter yet: 2.

## Whole catalogue

- Places: 827; with 0 flips 643, 1 flip 133, 2 flips 51.
- Flips by scope: namedRole 1, occupantGroup 31, place 203 (total 235).
- Respawn classes: faction-refills 88, none 542, seasonal 16, slow 181.
