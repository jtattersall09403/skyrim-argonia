# Lane 1.15-r6-journeys-harness: stands clear of canopy and fronds; the pass ledger that shrinks

Status: delivered except the corridor shore, which reads 2/1, not 0/0 (below). L4 owed to the planner's batch.

## The clearance measure (tools/journeys/__init__.py `clearance`)
From the placement shards and each form's OBND (object_form bounds; the shard's pivot already carries the seat, the
mesh's own z0 is now added): every plant is its whole OBND cylinder (widest half-extent, z0 to z0 + height, scaled),
no trunk exemption. `line`: volumes crossing the level eye line along the heading to 60 m. `canopy`: volumes whose
footprint covers the eye and which reach from under eye + 10 m to over the eye. The first reading (any crown footprint
within 10 m of the eye) was measured unsatisfiable: no dry stand within 200 m of any of the three water stops read 0
(every swamp tree's crown is 25-40 m round), so canopy is the volume over the eye within 10 m above it.

Measured at the round-5 stands (old model read all "clear"): sea 0/22 (first canopy reading), river 16/22, corridor
shore 10/17 then 13/1 (overhead reading).

## Refreshed stands (`python3 -m tools.journeys refresh`, both numbers printed per stand)
| stand | x y (units) | heading | water share | clearance |
|---|---|---|---|---|
| water-types sea | -227328 -88066 | at subject -227328 -116078, pitch 0 | 78% | 0/0 |
| water-types river | -105959 163763 | at subject -101844 159749 | 42% | 0/0 |
| water-types brackish-rim | -76273 243474 | at subject -75776 224773 | 50% | 0/0 |
| world-panel deep-river-corridor-shore (noon, dawn) | -126452 -144896 (marker unmoved) | 73 (was 13) | >= authored | 2/1 |

The water stops try every shore strict (0/0) first, then the old fit with a warning. green-marsh 10/16, black-swamp
1/12, stream 1/3 (outside this brief) fall back with warnings.

Corridor: no stand in the vantage's own land region (imperial-penal-south.deep-river-corridor) within 600 m (8 m grid,
every 15 deg yaw) reads 0/0 while keeping its water share; the nearest 0/0 at 542 m lies in deep-sink-basin. The
fallback (`gen.panel_clear`) takes the least canopy then fewest hits within 60 m: the same stand turned to yaw 73, 2/1.
Closing it needs the vantage chosen elsewhere on the corridor (tools/argonia_world/panel.py `vantages`, not this lane's
path) or a ruling that a one-crown overhead is acceptable. The other panel vantages' numbers are in the refresh log
(e.g. rootland-shore 24/19, flooded-forest-shore 12/25): only the corridor was in scope.

## The pass ledger
world-panel and sky-ab carry `"reach": ["esm", "tests/scenes/world-panel.txt", "data/dependencies.json"]` (the panel
refs and the weathers they force are ESM forms; the journey's own settings and each step are already in every key, so
the file itself is not listed: a refresh moving one vantage reruns only its steps). Refresh now keeps a JSON journey's
reach line. Test `test_panel_and_sky_reach_ignores_other_journeys_and_follows_placement`: another journey's edit leaves
every key, an ESM change moves every key.

## Gates
tools/tests test_journeys, test_journey_lint, test_pass_ledger, test_run_journey: 79 pass, 1 fail:
`test_the_derived_journeys_stand_on_the_current_build` on rock-booth only (six stands +1.7 m), from another lane's
uncommitted rock-booth.yaml / vegetation_form edits in the tree, not this lane's. `journeys check` likewise: 6 stale, all
rock-booth. Paths touched outside the brief's list: tools/journeys/__main__.py (the panel hook, the reach line) and
world/db/build_ref.jsonl (the corridor marker's yaw, written by the refresh).
