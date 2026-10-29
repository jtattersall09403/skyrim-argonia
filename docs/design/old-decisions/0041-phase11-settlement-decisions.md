<!-- imported unchanged from elder-souls-argonia docs/decisions/0041-phase11-settlement-decisions.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0041 — Settlements and places: the cross-cutting rules, extent and isolation

**Status** accepted · **Feeds** the place catalogue, the macro plot, the
`place` skill, [world/96](../world/96-placement-playbook.md) and
[world/97](../world/97-placement-principles.md)

The settlement system's delivery plan now lives in the foundation-and-places
phase; this record holds the rules that outlived it. The run-book, the
round-by-round working and the homeless-record diagnosis are in
[the archive](../research/archive/phase11-rounds/0041-siting-rounds.md).

## The catalogue is the permanent registry

Place ids are what quests, journal, map, saves, letters, deed counters and
rumour pools reference forever: never deleted or renamed; a cut place flips
`status`. Every record carries, from the start, the discovery pointer, the
letter and rumour pool key, deed-counter keys and typed socket lists (SCENE,
EVIDENCE, STATION, marks) even when empty. A compiled place bundle expresses
variants and overlays (quests 20 §14). Every enterable structure carries a
door id, facing, threshold transform and an interior claim, and a validator
proves each door reachable on every compile. The compiler emits a static
per-place budget (instances, draw calls after merge, materials, texture MB,
colliders) checked against the declared packet budget.

## Quests fold in at three points

At derivation, quest provisions (quests 20, §12b) generate catalogue rows
with tier ownership, tier-0 untouchable; after the macro plot, a quest-side
reader names unused offers, unplotted needs and dots to move, both sides
updated in one change; per packet, the quest-brief set and density budget are
a completion gate. World feasibility and the packet budget win ties.

## Distinctiveness is designed in the catalogue

Five rungs, each varying against the one above: province (one house style,
one material logic), region (distinguishable from one screenshot), named
place (a written signature of architecture, palette, silhouette, a landmark
and a layout-shaping economy, checked pairwise against neighbours), within a
place (districts differ) and instance (seeded variation). Small places get a
signature sentence and an asset plan too. A distinctiveness check flags
neighbours or same-family places that are too alike.

## The breadth rule

Example lists in these docs are illustrative, never exhaustive: enumerate
across independent axes (economy, faction, ecology, era, traversal, danger,
social function, condition, season, scale), set a per-region family target,
run a completeness reader, prefer the unfamiliar when options tie.

## Slopes and uneven ground

From [the siting research](../research/placement-settlements/openworld-place-distribution-and-siting.md):
the building snaps to the grid and the ground moves to meet it, driven by the
height delta Δ across the footprint: under 0.15 m place direct; 0.15–0.6 m a
plinth course; 0.6–2.0 m grade a pad with a 2–3× falloff ring and a softened
rim (≤ 30°); 2.0 m or more never grade, use a stilted or dug-in variant or
re-site. Pad height is the footprint's maximum, the base buried ≥ 0.25 m.
Verticals are geometry, never terrain edits. Water-edge structures sit
against the highest water and pile to the bed. Floating corners, buried
doorways and unsteppable thresholds fail the validator. Footprints and doors
are constraints to the road compiler. Each settlement effect is a falloff
field with its own radius per channel (material about 8 m, vegetation 15 m,
terrain 25 m). One LOD authority per building, baked from post-grade
transforms. Compile order: suitability, siting, layout, grade, roads, navmesh,
vegetation, materials, LOD. Pads keep 0.5–1° of residual tilt against shadow
acne.

## Taste ledger

| Steer | Evidence / where it bites |
|---|---|
| **Climbing is free on piles and house sides in every settlement.** Module 00-core makes large logical surfaces climbable by default; no quest gate may assume a stair is the only way up a tier | Lilmoth question 4; quests 85 condition vocabulary must not carry a "reached by the stair" gate |
| **A safe city still declares its combat spaces**, each tied to a quest or a hostility flip (97 D9) | Lilmoth's four; the owner asked and confirmed |
| **Argonian places promise a shrine, not a temple**; Imperial- or Dunmer-founded places keep their chapel or temple under their own culture | promise ledger R3; Stormhold, Thorn, Helstrom, Archon changed |
| **Solid masses stay masses.** A piece with no opening and no door anywhere in its source stands as a mass; a guard post that must be entered uses a piece with a baked leaf | Imperial guard tower, Ayleid stair block |
| **The hostile-or-clearable share: 55 % is the target (warn), 50 % the hard floor** | `test_catalogue.HOSTILE_SHARE_HARD_FLOOR` |
| **A gate is named for the road it faces**, never for a compass point the road does not use | Lilmoth: the north gate faces the Blackrose road from the west-north-west |
| **A capital's drowned or ruined quarter is under the player's own walkway** (1–15 m); the expeditionary dive is a wreck place, not the city | Lilmoth question 2 |
| **Interiors come from the mod's own door links, never a filename guess**; a shell the plugin links to an interior gets that interior and its door offset as the entrance | `exterior-interior-links.json`; supersedes the stilt-hall "hut dressing" holding position |
| **Beast lairs on water are swimmable fights** (pond ≥ 2.5 m), hazards are heavy damage over time not instant death, and clearing one changes the map loudly (detour abandoned, travel times drop) | the Standing Charge; sets the pattern for the 38 lairs |
| **A licensed camp is a landmark, not a hide** (the hero tree, the licence readable from the water); permanent dwelling (mud hut) over canvas | the Licensed Stage |
| **Villages grown into trunks are accepted**; ring spacing 22.6 m is the tribal-village default; delegations camp in canvas outside the gate | Nine-Trunks |
| **A stone place on a slope is shown as a building site of rising courses** where the finished static would swallow the shelf; pens behind the rise (a reveal); haul road as a switchback; the Hist stays where it grew with conduits climbing | Mazzatun |
| **No lane is a ruled line and no huts stand in columns.** Two parallel ways of one width, or three or more buildings on one bearing at one spacing, read as a grid even in a stilt quarter; boardwalks run straight only from pile to pile between bends, footpaths are routed on the ground, and each dwelling takes its own offset (5.5–6.5 m off its lane) and its own spacing (12–19 m) | owner-eye review: Pusbottom's two parallel lanes and three hut columns at 15 m; the shore quarter's ruler row |
| **A ring that grew is not a polygon.** Trunk rings, hut rings and pole rings carry a seeded jitter (up to about 6° and 2 m per member) about the culture's default spacing; the default (22.6 m) is an average, never an exact chord | Nine-Trunks' exact nonagon; applies to all 27 tribal villages |
| **Props are not buildings.** Every parcel derives a `kind` — `building` (encloses a room or has an entrance), `structure` (deck, scaffold, gate, wall, tower), `prop` (rack, oven, cart, board). Props are exempt from the C5 8 m floor, the C6 density band and the C7 use histogram, and are counted as C12 dressing; structures count for C6 and not C7; a stacked piece adds nothing to any count | audit §7.1 (a works yard judged as a village); `worldgen.parcel_kinds`, 97 C5b |
| **Kit purity is held over what a place is built of.** The `works-v1` props and a neutral dressing pool are admitted to every kit set; only structures and buildings are tied to one kit per district. A district drawn round a single prop is deleted | audit §7.2; Lilmoth's dues-board district removed, the board moved into the lighter quay; `blueprint.DRESSING_KITS`, 97 C1a |
| **Where C2 and C4 want the same ground, the Hist wins.** Commerce sits on the spine at the first junction inside the threshold ON THE WAY to the sacred or authority node, not at a fixed distance from the gate | audit §7.3; Lilmoth, where the high ground is the ground nearest the gate; 97 C4 |
| **Argonians build no fence or wall piece except where the lore cites one** (Lilmoth's estuary pole wall); a closed ring of dwellings, trunks and woven panels between them IS the place's edge and counts as one | audit §7.4; Nine-Trunks; 97 C10 |
| **`abuts` covers kit snap pairs only.** A trade contact (a hoist against the rock it works, an oven beside its rack) is `worksWith` + `worksWithWhy`: exempt from the 8 m floor, and it must keep 0.5 m clear, because nobody authored those two pieces to touch | audit §7.5; validator + `parcel-gap` `WORKS_WITH_CLEAR_M`, 97 C5a |
| **The Morrowind ratio is the rule for structure counts** (Balmora ≈ 40, so an M5 is 50–80 buildings and structures); the settlement register's 150–400 band counts total placed objects including props and dressing | audit §7.6; 97 D7, module 92 §83b |
| **The gate piece sets the width through it.** A spine may narrow to the opening for the gate's length and widen again beyond it | audit §7.8; Mazzatun's 3 m roads through a 3 m gate; 97 C3 |
| **The Mazzatun raiders' back way is a climb, not a cut.** One way onto the shelf by the road; the raiders come down a climbable rock face (climbing by default, 00-core), and no terrain is cut for it | audit; the design record, gap plan B8 line removed |
| **A gate that can be walked round is not a gate.** No way of any class enters a place past a `spans` gate; a lore-grounded back way (a raiders' path, a smugglers' cut) is allowed only if it is walkable (≤30° in any 3 m), is not the line any `approaches[]` entry uses, and says on the way why it exists | Mazzatun's shoulder footpath skirted the shelf gate at 42–58°; removed, terrain request in gap plan B8 |
| **What the eye wants gets a path.** Where a walker at a node can see a quarter below within 150 m, a footpath joins them unless the ground forbids it; a 500 m detour to reach what is in plain view reads as fake | Lilmoth: the fishers' path from the gate yard to the shore quarter (120 m for a 500 m loop) |
| **Accepted answers are written into the record the same day.** A design record's open question is closed in place with the ruling and where it now lives; prose that still describes the rejected option (a tent for a hut) is a defect | the Licensed Stage still described the tent; the Standing Charge lacked its four rulings |
| **The committed plot is the seed of the solve.** A record keeps its committed cell unless that cell is no longer valid (water depth at the dot, a moved danger/region raster, a blocked sightline); a province-wide re-plot is the owner's deliberate step behind `--resolve-all` | terrain edits moved 342 of 579 records in a from-scratch solve; `macro_plot`, playbook §1 "The seed rule" |

## Places have extent: a footprint, never a point

1. **`footprintRadiusM` on every type**, derived from the place's **built
   ground** where a blueprint exists: parcel hulls measured off the asset
   geometry, the boundary of every district that holds a parcel, and the
   landmarks inside those districts. Approach water, marker poles and empty
   districts do not count; every test is geometric (97 E2). Otherwise banded:
   by magnitude (M5 230, M4 140, M3 115, M2 65, M1 45 m) else
   `complexityBudget` (25 / 38 / 60 / 95 m) × a class factor × a
   `countBand` nudge, floor 20 m. `worldgen.author_type_siting` derives it
   and is drift-checked.
2. **The pairwise floor** is `max(COLLISION_MIN_M, r_a + r_b)`, immutable
   across relaxation stages. A related pair (`proximity.mayAbut` or
   `boundTo`) clears only the smaller radius.
3. **`proximity` on types**, authored from and quoting the type's own
   `neighbourRelation`: `minFromClassM`, `maxFromM`, `outOfSightOf`,
   `mayAbut`, judged in both directions. An absent block means no constraint.
   `outOfSightOf` binds within the paired `maxFromM` range.
4. **Gates and repairs.** `check_type_proximity` fails a record that
   contradicts its type prose; `typed_siting_violations` re-checks the finished
   plot; `whyHomeless` reports each gate alone (`soleBlocker`); `scourSiteIds`
   are reservations. Repair passes only reduce homeless records or violations
   and roll back otherwise; a seeded solve never moves a committed cell.
5. **Fix the record, never the radii.** A place that cannot be sited under its
   own semantics is a finding about its typed fields, a derivation or the
   solver; the derived radii and `physical_need` are not relaxed to fit.
   Count bands are authored (`stilt-village` 5–9, `reef` 2–6), not re-derived.

## Isolation is effort

Isolation floors are measured as walking effort, not plan distance: Tobler's
hiking function `W = 6·exp(−3.5·|S + 0.05|)` km/h on the survey's 5.48 m
grid over the natural height raster, symmetrised over the pair and clamped
at a 100 % gradient (`worldgen/travel_cost.py`; sources and rejected
alternatives in [travel-cost-isolation](../research/phase11/travel-cost-isolation.md)).
The unit is **equivalent flat metres**, so on flat ground it equals plan
distance and the authored floors keep their numbers; effort is never below
plan distance. Each recipe states `proximity.minFromClassMeasure =
"equivalent-flat-metres"`. Floors are calibrated on measured supply (6.8 % of
land is 800 m or more from any settlement), so isolation floors are 600 m.

Under this measure every live record sites with zero typed-siting
violations, the snowline hermitages included; the hermitage records stand.

## The hostile share

The hostile-or-clearable share of places has two levels: **55 % is the target
and warns** (`HOSTILE_SHARE_FLOOR = 0.55`); **50 % is the hard floor and
fails** (`test_catalogue.HOSTILE_SHARE_HARD_FLOOR = 0.50`). Settled.
