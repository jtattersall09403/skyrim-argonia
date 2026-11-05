# Lane 1.15-r6-bridges: the step crossings bridged, the junction out of the Blue Hole

Code: `routes/infra.py` (bridges), `routes/build.py` (keep-out re-route), `routes/tests/test_bridges.py`. Route rows re-routed through db.py
(`road_point`, `road`, `route_edge`). No game, no generate, no regenerate.

## How Skyrim does it (0034), measured
Probe: Skyrim.esm Tamriel. For every placed bridge STAT, its OBND, its position and yaw, the cell's XCLW and the LAND under its two ends.
- Bridge01 is the road bridge (Riverwood, Whiterun plain; 35 refs). Length 42.3 m (p50).
- Crown over the water: p50 4.94 m, min 2.38 m (n 25).
- Crown over the land at the mesh's ends: p50 2.97 m, p10 2.3 m. The stone ramps run down into the banks, so the road climbs about 3 m to the deck.
- StockadeBridge* and StockadeScaffoldBridge* are wooden spans, 9.3-9.5 m p50. They are laid across gaps and stand on their posts, not on the banks.
- Bethesda's method: a static laid across the water along the road, its ends on the banks, the approaches graded up to it.

## The asset
King of the Murkmire's cypress scaffold bridge `stockadescaffoldbridge04.nif`. It resolves to `CypressStockadeBridgeB04` 10A58B:King of the Murkmire.esp (also `MurkmirePlatformBridge04`).
- OBND (-613, -136, -80, 616, 130, 47) u: 17.56 m long, 3.80 m wide, deck top 0.67 m over the origin.
- Why: it is the longest and widest wooden span in the permitted stack (a scan of KotM and Black Marsh.esm STATs, wood/plank/dock/bridge meshes at least 8.6 m by 3.6 m).
- Lore: Stormhold's "long wooden bridges" (world/sources/lore/stormhold.md 43). Murkmire's own kit is the source, so no Nordic stone (0006).
- Black Marsh.esm's `01hut2bridge` is a 5 m hut walk. `0bridge` has no bounds and its mesh is not on the VM.
- The register row is updated: data/sourcing-register.json, King of the Murkmire.

## The crossings (`python3 -m tools.argonia_world.routes.infra check`, on the current GameGround)
Rule: the deck is level on the mean line of the roads it carries. It is centred where the earthwork at the two seats (each end's last 0.3 m and 4 m beyond) is least. Its top is the higher bank, and the lower bank is the terrain's seat.

| bridge | roads | centre (x, y south) m | yaw | deck top | banks | lift | over the lower water |
|---|---|---|---|---|---|---|---|
| gideon-step (reach.878-1669) | gideon-soulrest, gideon-stormhold | (1604.44, 3039.16) | 345.08 | 69.11 | 69.11 / 67.34 | 0 / 1.77 | 13.4 m |
| glenbridge-step (reach.1015-1489) | gideon-stormhold, glenbridge, north-shadowfen-rootworm-line | (1871.41, 2723.45) | 302.51 | 18.02 | 18.02 / 17.88 | 0 / 0.14 | 5.25 m |
| thorn-step (reach.3043-787) | stormhold-thorn, dres-slave-road | (5580.37, 1460.95) | 327.43 | 31.26 | 31.26 / 31.11 | 0 / 0.15 | 6.4 m |

- Each step is a gorge: the banks stand level on both sides, 4-16 m over the channel. So a level deck spans it and both ends rest on ground.
- The L1 check passes for all three (0 errors): every road carried crosses inside the deck's width and between its seats, the top is at the higher bank, and the ground under the deck lies below it.
- Ends (m): gideon (1595.96, 3041.42)-(1612.92, 3036.9); glenbridge (1866.7, 2730.85)-(1876.13, 2716.05); thorn (5572.98, 1465.68)-(5587.77, 1456.23).
- The pieces are persistent REFRs in the WRLD's persistent cell, the same path as the gates (`infra.refs` via regions/api.py).

## The seat the terrain pass must give (not built here: terrain/generate.py and routes/shape.py are not this lane's)
`infra.seats(w, z)`: per bridge end, from 0.3 m under the deck to 4 m beyond it, the corridor is held at the deck top, 5.8 m wide (the deck plus 2 m). It is then eased into the road's own profile at GRADE_MAX.
- Between the seats the step channel is left as it is: the deck stands over it.
- The lifts are 1.77 m at gideon's east end, 0.14 m and 0.15 m at the others.
- The census (`wet_main`) should take `infra.census_bridges(w, z)` as its `bridges` entry: the form, the roads, the deck and its banks, and `seated` once each bank is within 0.3 m of the deck. It should drop the step crossings that entry covers from `bridge_candidates`.
- Navmesh: tools/navmesh/placed.py reads only `place:` layer CELL refs, not the persistent infra refs. The deck gets no navmesh until placed.py also reads the infra refs (gates, landings and bridges) from the intermediate's WRLD persistent cell. Planner to route.

## The junction (a place call)
The Blue Hole (place.imperial-penal-south.natural-dive-shaft, 30 m site, entrance underwater-entry).
- Its row reads "a vertical hole nine metres wide in a flat lake bottom", with traversal_fallback boat and underwater_access deep-dive. Its approach is the water, not a road.
- `build.KEEP_OUT` names it. Each road keeps out of the site's radius x SITE_BLEND (45 m, the bowl's easing) plus half its flat width plus the dry corridor's 6 m shoulder: 52.25 m for these tracks.
- The line goes round the disc on its drier side (fewer wet search cells), and each road's two ends are kept.
- `build()` applies this after every trace. `routes.build reroute` applied it to the stored lines with no re-trace:
  - blackrose-cordon-line: +63.1 m from 367 m
  - coast-road: +63.7 m from 3003 m
  - rose-causeway: +63.1 m from 251 m
- New line: the three tracks share one arc of radius 52.25 m round (2475.8, 6226.5), on its south side (mid-arc bearing 217°). It runs from (2522.0, 6250.9) to (2436.9, 6191.6), and the tracks meet the arc at those two points. The nearest road point to the shaft is now 52.24 m away (it was 3.8 m).
- `routes.build check`: 1 component, worst terrain deviation 2.02 %. The old chain's reference-length reds are as before: major roads only, untouched.
- The same class of conflict: place.saxhleel-coast.archon-glowgill-byre (45 m site) lies 26.6 m from route.road.archon-gideon. It is not named, since no ford was measured there. It is the planner's call.

## Tests and the gate
- `pytest tools/argonia_world/routes/tests`: 27 passed (5 new: seat on a level and an off-centre gorge, the arc round a disc, the six crossings on their decks, no road in the shaft's site).
- ruff clean.
- `make plugin PLAN=1`: ground, terrain, vegetation, creatures, world-esm and the whole build run; water skips.
- The census stays red until the planner's regenerate (r6-land3) takes the seats and the shape.py `bridges` entry.

## Checks owed (rows for checks.md; the planner adds them to the batch)
1. The six step crossings are walkable on their bridges. Journey `bridge-look`: a stop at each of the three decks (the centres above, standing on the deck at the deck top), scan 6. The player walks end to end on each road's line with no wall at either seat. A state read gives the player's z within 0.3 m of the deck top at both ends.
2. The junction is dry. Journey `junction-dry`: a stop at (2444.7, 6268.5) on the arc, scan 6. The three tracks meet outside the Blue Hole's bowl with no water on the line. A state read: the player is not swimming along the arc.

## Round 2 (planner): the keep-out made general
- `build.keep_out_discs` now takes every placed site whose entrance is underwater-entry (`KEEP_OUT_ENTRANCES`; generate's deep_water shape): 42 sites.
  - A site that is one of a road's own ends is not kept out (`route_ends`).
  - When it picks a side, an arc weighs another site's disc at 1000 and water at 1, so it never swaps one site for the next.
  - `around` is idempotent: a point already on the arc counts as outside.
- `build.site_conflicts` is the census line, printed by `routes.build check`.
  - `red`: a road corridor inside a keep-out disc. It fails the check, so the next one is a red.
  - `served`: a built place's eased footprint that a road runs through and that is not one of its ends. These are listed only, because the road is the place's street.
  - Today: 0 red; served: claywater-station on gideon-blackwood-road.
- `routes.build reroute` (no re-trace):
  - archon-gideon goes round archon-glowgill-byre (67.5 m eased site + 8.5 m corridor = 76 m; it was 26.6 m away): +54.2 m from chain 727 m, ends kept.
  - stormhold-thorn goes round reach-wreck (it passed 63.1 m away, keep 76.5 m): 880 -> 895 points, +0.0 m (a graze).
  - The Blue Hole's three tracks are unchanged.
- `routes.build check`: 1 component, worst terrain deviation 2.02 %, site_conflicts 0 red.
- Tests: routes tests pass, 30 (no road enters a water-entered site; a planted road into a disc is red). Ruff is clean.

## Round 3: the deck at the corridor's height, and what the piece looks like
- The r6-chain23 bridge-look stills (gideon-step 01 and 02) show the deck at the bottom of a trench 3-5 m under the raised road.
  - Cause: the ref's z came from the pre-causeway ground, and the seats cut the causeway down to it.
- `infra.bridge_placements` now reads generate's `out/terrain/bridge-decks.json` (`load_decks`; a list or `{"decks": [...]}`, with `deck_top_m` and `ends_m`).
  - A file deck whose centre lies within 20 m of a crossing's census point sets that bridge's ends, heading and top.
  - The piece's z is the top less 0.67 m (BRIDGE_TOP_M), and `deck_source` is `decks-file`.
  - Without the file it prints a warning and falls back to GameGround (`deck_source` `ground`).
  - `seats` and `census_bridges` read the same file.
- Test `test_a_deck_file_sets_the_top_and_the_ends_and_the_census_reads_it` uses a synthetic deck file. Routes tests pass: 32.
- The form placed is CypressStockadeBridgeB04, 10A58B:King of the Murkmire.esp (`stockadescaffoldbridge04.nif`). Its name says cypress stockade, but the mesh is a bamboo-pole deck with rope rails on short posts, as the still shows.
  - That is a long wooden footbridge, which meets the lore's "long wooden bridges" (stormhold.md 43).
  - It is not a plank road bridge: whether bamboo reads as Argonian is the owner's look, at the next check.
