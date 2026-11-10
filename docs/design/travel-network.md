# The travel network

How the player gets about Black Marsh without map fast travel: by boat, by coach and by rootworm, as stops and
routes in the new world's database. The place records list each stop, and the build makes it each place's service.
Map fast travel will be turned off later (owner, 2026-11-10); nothing in the game depends on it.

## Sources and tables

- `newworld/sources/travel/network.json`: the modes, the operators, the stops, the routes (authored as pairs) and
  the places left remote on purpose, each with its reason.
- `build_db` loads it through `tools/newworld/travel.py`, which takes its measurements from the database's own
  ground, into `travel_mode`, `travel_mode_water`, `travel_operator`, `travel_stop`, `travel_route` (both ways) and
  `travel_approach`.
- A stop is a give in the place record (`boat-stop`, `coach-stop`, `rootworm-stop`). The record names who serves it
  and where; the network names its operator, whether it is a hub or a spoke, and why. The build fails on a stop with
  no give and on a stop give with no stop.

## Modes

| Mode | Needs | Operators | Fare (fixed, never levelled) |
|---|---|---|---|
| boat | navigable water from landing to landing: sea, bays, estuaries, rivers, lakes, streams and marsh channels at least 8 m wide | sea-coaster (any open sea), raft-master (at most 500 m of open sea) | 10 + 8 a km, in fives, 10 to 60 |
| coach | a major road the whole way | carter | 10 + 6 a km, in fives, 10 to 50 |
| rootworm | a Hist with a root pool at both ends | root-tender | 25 |

The time on the way is the mode's boarding hour plus the distance at its pace, but the game advances the clock
itself: the service line calls Game.FastTravel, as vanilla's carriages do, and they still run when map travel is
turned off, as in Survival. Fares sit in the scale's first two gold bands (newworld/sources/stock/scale.json): a hop costs what a
common thing does, the longest voyage what a sound one does.

## Measuring

- A boat route runs along the water raster (`out/newworld/water_classified.png`) through the bodies of the mode's
  kinds and widths, from the water within a place's reach (its built radius, at most 200 m, plus 80 m of jetty) to
  the other's, by the shortest water path; the metres over ocean or bay are kept apart and held to the operators'
  limits.
- A coach route runs along the road graph, through roads of the mode's class only.
- A rootworm route is the straight line under the ground.
- Each place with no stop gets its approach: of its four nearest stops, the shortest way from one, by road where a
  road joins them no more than a third longer than the straight line, across the marsh on foot otherwise, over the
  water to an island or a place on the water, and diving to the seabed.

## Authoring a network

1. Find where boats and carts can go: `python -m tools.newworld.travel candidates` lists each lived-in place's
   water and major road.
2. Hubs by tier, wealth and trade: the cities and towns whose records already run the traffic (a port, a lake quay,
   a confluence, a Hist the region hatches at). Spokes are the smaller places whose records show a boat, a ferry or
   a cart, each joined to its hub. A place is a stop only when its own record or the lore shows that trade there; a
   ferry crossing a few hundred metres to a neighbour is a walk, not a route.
3. Culture and region choose the mode, as Morrowind's routes were laid out by mode (striders inland between towns,
   ships round the coast, guild guides between halls): sea-coasters at the canon ports (Archon, Lilmoth, Soulrest;
   Thorn, Stormhold), raft-masters on the inland water that drains to Helstrom, carters on the old Imperial roads of
   the west, root-tenders at the Hist trees of the interior and at Gideon, the rootworm's canon stop.
4. Add no route that the ground or the lore does not support: a boat route needs a water path, a coach route a
   major road, a rootworm route a Hist at both ends; open sea needs a sea-going operator.
5. Every place is reachable by a chain of routes and walks between stops, or lies within `walk_max_m` of a stop,
   or is in `remote` with the reason. The `networks` count in the source gives the number of separate networks.
6. Rebuild (`python -m tools.newworld.build_db`) and check: `python -m tools.newworld.travel check` (0 problems)
   and `report` (stops, routes, parts, approaches).

## The service

For each stop, `build.py plan_travel` writes one line per route for the stop's operator (the person whose
`people.jsonl` service is the stop's give). The line carries the route's fare and lands the traveller at the
destination's arrival point, its map marker in the world ESM. A destination with no arrival point yet is not
offered: the build lists it as waiting, and the place record still carries the promise. `check.py` tests that each
route is offered at its fare and lands at its arrival point (docs/design/place-studio.md, Build: travel).
