# Research records

Research is written here as JSON and built into the database by `tools/newworld/build_db.py`, so parallel
researchers never write the same table. Each file holds `{"records": [ ... ]}`; each record fills the row its `id`
names. Rebuild after writing: `/home/ubuntu/.argonia/venv/bin/python -m tools.newworld.build_db`.

## Grounding

- Read the repo's lore first: `story/lore/README.md` (the router and sourcing rules),
  `story/lore/black-marsh-province.md`, `story/lore/extrapolation/argonia-4e201-state.md` (what the province is like in
  4E 201), `story/lore/tribes.md`, `story/lore/topics/lost-peoples.md`, the city dossiers (`story/lore/<city>.md`), the
  region dossiers (`story/lore/regions/`), and `story/lore/extrapolation/settlement-register.md`.
- UESP: the MediaWiki API with the User-Agent `ElderSoulsArgonia-research/1.0` (plain page fetches are refused):
  `https://en.uesp.net/w/api.php?action=query&prop=extracts&explaintext=1&redirects=1&format=json&titles=Lore:<Name>`;
  to find a page, `action=query&list=search&srsearch=<name>&srnamespace=130&format=json`. Look up every place and
  region name; most Project Tamriel names have no page, and saying so is a finding.
- Era: 4E 201. Earlier facts are history; never present a 2E (ESO) political state as current.
- Tier every statement: `CANON_EXPLICIT` (stated by a source), `CANON_DERIVED` (follows directly), `EXTRAPOLATED`
  (reasoned from canon, the region, comparable places and the 4E 201 state), `AGENT_INVENTED` (made up to fill a gap,
  consistent with all of the above). Where canon is silent, extrapolate: what would this place logically be in 4E
  201, given its kind, its culture, its region, its neighbours on the map and what similar places are like.
- Cite: every note lists its sources (`kind` one of `uesp`, `dossier`, `extrapolation`, `map`, `reasoning`).
  `reasoning` names the facts it reasons from in `title`.
- No Nordic element reaches the player through what we add (decision 0006). Nothing is levelled to the player
  (decision 0035): danger is fixed by place.
- Prose: plain, concrete, present tense for 4E 201, for a reader who knows nothing of the setting. No filler.

## Place record (`places/<batch>.json`)

```json
{"id": "<place id from the database>",
 "name": "<the map's name; for an unlabelled or bracketed place, a name: AGENT_INVENTED, in the culture's naming style>",
 "place_kind_id": "<only if the research changes the kind, e.g. an unlabelled triangle that is a fort>",
 "status": "inhabited | garrisoned | abandoned | ruined | occupied | sunken | seasonal",
 "held_by": "<who holds or haunts it now>",
 "population": 0,
 "footprint_radius_m": 0,
 "siting": "riverbank | coast | island | lakeshore | inland | hilltop | swamp | seabed",
 "danger_band_id": "D0..D5 (the strength of what lives inside: docs/design/danger.md)",
 "importance": "5 shapes the province, 4 major, 3 regional, 2 local, 1 local colour",
 "summary": "<two or three sentences>",
 "lore_page": "Lore:<Name> or null",
 "statement_tier_id": "<the tier of the place's identity as a whole>",
 "aliases": [{"alias": "...", "source": {"kind": "uesp", "title": "Lore:X", "locator": "Lore:X"}}],
 "notes": [{"aspect": "overview", "text": "...", "tier": "EXTRAPOLATED",
            "sources": [{"kind": "uesp", "title": "Lore:Helstrom", "locator": "Lore:Helstrom",
                         "url": "https://en.uesp.net/wiki/Lore:Helstrom", "section": "History"}]}],
 "terrain_needs": [{"id": "flat-pad", "radius_m": 200, "why": "the city's built area"}],
 "gives": [{"kind": "trainer", "detail": "Expert Alteration trainer", "count": 1},
           {"kind": "combat-boss", "detail": "the smugglers' captain", "count": 1, "reward": "boss-chest"},
           {"kind": "boss-chest", "detail": "the captain's chest in the stern cabin", "count": 1}]}
```

Every place carries every field above (aliases and terrain needs may be empty lists), and one note for each of
these aspects: `overview`, `history`, `present`, `people`, `economy`, `faith`, `look`, `dangers`, `hooks`
(1-3 sentences each; a ruin's `economy` says what it once was and what draws people now).

Terrain needs (`id`): `flat-pad` (level built ground), `entrance-in-slope` (a bank or rise the entrance is cut into;
give `facing_deg`, 0 north, clockwise), `shore-access`, `island`, `rise` (stands on a mound above the land),
`seabed` (on the floor under the water). Settlements need a `flat-pad` of their footprint; caves, mines and dungeon
ruins with an entrance into the ground need `entrance-in-slope`; places on the water need `shore-access`.

Population (people living there in 4E 201, at Skyrim's scale: Solitude has about 70 named residents): use the
tier's range in `settlement_tier` unless the research says otherwise; 0 for a ruin or wild place.

## Gives

`gives` lists what the place gives the player as gameplay. Leave out local colour, quests and factions. A place can
list several kinds, and several of one kind.

- `kind` is an id from `give_kinds.json`. Its groups are travel, trade, craft, train, rest, blessing, resource, loot
  and combat.
- `detail` is specific: name the skill and tier of a trainer, the schools a spell vendor sells, the ore of a vein,
  the plant of a harvest and the foes of a fight.
- `count` is how many, 1 or more.
- A travel give (`boat-stop`, `coach-stop`, `rootworm-stop`) is a stop of the travel network: its detail says who
  serves it and where; the stop and its routes are in `newworld/sources/travel/network.json`, and the build rejects
  a stop give the network does not hold, or a stop with no give (docs/design/travel-network.md). No place promises
  map fast travel.
- A combat give (`combat-foes`, `combat-boss`, `combat-creature`) needs a `reward`. The reward is the id of a loot
  give that the same place also lists: `boss-chest`, `treasure`, `gold-hoard` or `unique-item`. A boss needs a
  boss-chest, a gold-hoard or a unique-item.
- A combat give at a settlement (city, town, village, hamlet, outpost) names its `setting`: `interior` (it lives in
  a dungeon-like interior of the place) or `provoked` (the place's own people, who fight only when provoked). A
  creature fight in its waters needs none; a fight outside it is the ground's, not the settlement's.
- A loot give's detail says where and what kind of store it is ("the captain's chest in the stern cabin"), never
  its tier.
- The build rejects an unknown kind, an empty detail, a combat give without its reward and a setting on any other
  give.

The reward's tier is the place's reward band (the higher of the way in and what lives inside; docs/design/danger.md),
never the player's level; the scale (`newworld/sources/stock/scale.json`, `danger_tier`) turns a band into a tier:

| Band | Combat | Reward tier |
|---|---|---|
| D0 | none, or in an interior | T1 Common |
| D1 | foes, creatures | T1 Common (iron, steel, hide) |
| D2 | + a boss | T2 Sound (steel, imperial, orcish weapons) |
| D3 | as D2 | T3 Fine (dwarven, elven, scaled) |
| D4 | as D2; a gold-hoard fits | T4 Rare (glass weapons, ebony armour) |
| D5 | as D2; a unique-item fits | T5 Precious (ebony weapons, glass armour) |

## Deliverable in Skyrim

A note promises only what Skyrim's own systems deliver: records, AI packages, scripts on activators and triggers,
and weather, light and sound records. The engine does not have these, so no note promises them:

- Water: no currents or flow that push the player or boats, no tides, no waves that rise or fall, no rising water
  or floods, no swimming hazard beyond drowning when the breath runs out.
- Terrain: no collapsing ground, sinking mud, quicksand or terrain that changes during play.
- Weather: no storm that comes when the story calls for it, only weather records chosen by region and chance. No
  seasons.
- Fire and plants: no fire that spreads and no plants that grow or die during play.
- People: no routine beyond AI packages (rest, eat, work, sandbox, patrol at set hours). No crowds that trade with
  each other and no prices that move with supply.
- Creatures: no herds that migrate and no breeding. Foes respawn only when a cell resets.
- Building: nothing is built or destroyed during play except by enabling and disabling placed references.

## Region record (`regions/<batch>.json`)

```json
{"id": "<region id>", "summary": "...", "landform": "...",
 "elevation_floor_m": 1.0, "elevation_summit_m": 20.0, "roughness_m": 1.0, "cliff_share": 0.05, "wetness": 0.8,
 "biome": "...", "climate": "...", "culture_id": "<the culture most of its places share, or null>",
 "danger_band_id": "D1..D5 (its baseline away from roads and towns)", "statement_tier_id": "...",
 "notes": [ ... one note for each aspect: overview, history, present, people, economy, faith, look, dangers,
            landscape, ecology, climate ... ]}
```

The relief numbers drive the terrain (heights above the one water level, metres): `elevation_floor_m` the typical
lowest dry ground, `elevation_summit_m` the typical highest, `roughness_m` the local relief of hummocks and banks,
`cliff_share` the share of slopes steep enough to be cliffs, `wetness` 0 dry upland to 1 standing swamp. Black Marsh
is mostly low and wet, but not flat everywhere: the north rises toward Morrowind and Cyrodiil, a mesa is flat-topped
with cliff sides, a ridge is a long high spine. Calibration from the earlier terrain work: swamp and lagoon floor
5 m, summit 13-24 m, roughness 0.75-1.2 m; rolling upland floor 7 m, summit 96 m, roughness 4.5 m; the northern
transition floor 10 m, summit 144 m, roughness 7.5 m, cliff share 0.25. Sea regions: give the sea floor depth as a
negative `elevation_floor_m` and the island or coast height as `elevation_summit_m`.

## Culture record (`cultures.json`)

```json
{"id": "<culture id>", "name": "...", "people": "<race, tribe, faction>", "about": "<way of life, building, belief,
 politics in 4E 201: 3-6 sentences>", "why": "<the reasoning that names them: where their places lie, which canon
 places are among them, what the lore says, with sources>", "statement_tier_id": "..."}
```
