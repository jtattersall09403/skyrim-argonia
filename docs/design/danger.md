# Danger

How dangerous each part of Black Marsh is, and what each place holds for it, as four facts in the new world's
database. Danger is fixed geography. The player grows into a band, but no band grows with the player (decision
0035). Each fact is derived with its reason, and the owner overrules any place's facts in one file.

## Sources and tables

- `tools/newworld/danger.py` sets each cell's bands (`cell.natural_band_id`, `cell.danger_band_id`, `danger_why`).
- `tools/newworld/place_danger.py` sets each place's facts (`place_danger`: disposition, strength, reach, reward,
  each with its reason). `build_db` runs both after the roads and the travel network are in.
- `newworld/sources/danger/owner.json` holds the owner's overrules, `{place_id: {disposition?, strength?, reward?,
  why}}`. `build_db` keeps them and marks the row `by: owner`.
- The place record's `danger_band_id` is the researched strength inside; a combat give at a settlement names its
  `setting` (`newworld/sources/research/FORMAT.md`).
- The bands are `danger_band` D0 Safe .. D5 Lethal, each with its foes' level; the dispositions are `disposition`.

## Ground: what roams a cell

1. The natural band is the country before anyone tames it: the depth into the province from its outer edge (under
   4 cells D2, under 10 D3, under 16 D4, deeper D5), moved one band toward the region's researched baseline when
   two or more from it. Sea cells take their region's baseline near a coast and one band more (at most D3) beyond.
2. Only a city or town makes ground Safe (D0): its cell, and a metropolis's or large city's eight neighbours.
3. Elsewhere one thing lowers a cell, the strongest of: a major road through it, two bands; a minor road, one band;
   a village, or a garrisoned fort or keep, one band. Never below D1, and the lowerings do not add up.
4. Hamlets, outposts, farms, mines, stations, ferries and camps change nothing: their people live with the
   country round them.

## The four facts of a place

1. **Ground**: its cell's band.
2. **Disposition**: friendly, wary, hostile or abandoned. Occupied places, outlaw camps and ruins held by people
   are hostile; a ruin, wreck or empty village whose fight is beasts or the dead is abandoned (or empty, with no
   fight). A lived place whose people fight only when provoked (a give with `setting: provoked`, or notes that turn
   strangers away) is wary; a tribal camp is wary unless its own people attack. Everyone else is friendly.
3. **Strength inside**: a city or town is safe inside, whatever surrounds it. A friendly or wary place takes its
   cell's natural band: people who live in lethal land are formidable. A hostile or abandoned place with a fight is
   at least its natural band, and one worse when the fight ends at a boss or its foes hold a dungeon, cave or
   wreck (at most D5). An empty place is its natural band. Any of these is raised to the researched band when that is higher, and never lowered to it.
4. **Reward**: the higher of the way in and the strength inside. The way in is the worst ground on the calmest way
   from the network: a travel stop or a road, the place's own cell included (a bottleneck path over the cells).

A place is stocked from its reward band: the band's tier (`scale.json` `danger_tier`, D0 and D1 T1 up to D5 T5) is the best a
place's ground and fight hold, and a lived place's ceiling is the higher of that and its wealth's
(`tools/newworld/wealth.py`; `place_wealth.json` is re-derived whenever a band changes).

## A settlement holds no hostile occupants

A settlement holds no hostile occupants. Its own fight lives in a dungeon-like interior of it (a cellar, a sewer,
a vault, as Riften keeps its thieves in the Ratway) or is a fight of its own people, who fight only when provoked;
either names its `setting`. Wildlife in its waters (Riften's canal) is a creature fight and needs none. Raiders on the road and
beasts in the country beyond belong to the ground round it, and an outpost whose people attack on sight is a
hostile place, not a settlement with foes.

## Checks

`python3 -m tools.newworld.place_danger check` tests that every cell's ground is its natural band, lowered only by
the rules under Ground; every hostile or abandoned place with a fight is at least its natural band; a settlement's own fight has its
setting, and a provoked fight belongs to a wary place; the reward is never below the strength or the way in; and
every value has its reason. `make check` runs it (tools/tests/test_newworld_danger.py) and also tests that
`place_wealth.json` matches a fresh derive. `counts` prints places by each fact, `show <place>` one place's facts
and reasons, and `reconcile` the places whose researched band is two or more from the rules (each is decided from its record and the lore, and the
record or the rule fixed).

## The Atlas

`python3 -m tools.newworld.map_page` colours each cell by its ground on the Danger layer, rings each place by its
disposition (hostile a solid red ring with spikes, wary amber dashes, abandoned grey dots) and lists the four facts
with their reasons in its card.
