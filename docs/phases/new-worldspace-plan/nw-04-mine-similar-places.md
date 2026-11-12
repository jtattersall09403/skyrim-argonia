# Mine similar places

Mine BM&Valenwood mod (for Blackrose, Thorn, and all of its minor places and POIs), King of the Murkmire (for all of its minor places and dungeons, plus any major places it has that we also have in our map), the other mods in our assets source list, and Skyrim itself (for any places not covered by the mods, or not covered enough - e.g. we need to have enough 'mines' and caves and ruins and so on to match up to all of the ones in our map) for places that are semantically similar to those in our game. Record a selection of similar places for each, ranked by similarity. (note we will be using the Tropical SKyrim version of all Skyrim assets if there is one).

After all collected, use an optimisation/matching algorithm to match up places in our new game/map to mined places. I want to end up with a matched 'source place' for each place in our map, such that no two of our places share the same source place. Factor into the optimisation:
* I didn't like Lilmoth in BM&V so don't use that
* Prioritise more major places getting a more similar match recorded as their top match. Weight the matching by this - the more major a place, the more weight is given in the optimisation to matching it a source place that is as similar as possible.

Record results in the database in whatever way will make it very fast and easy to load up any place's source place (including its full 3D layout and build and its local terrain in the game/mod where it was placed and all assets etc). Also record in the database 3 more other 'most similar places' for each of our places in the same way (it's OK for these other ones to be shared between our places, unlike with the optimised/allocated top 'source place').

Also update the place records in the DB for population: should be baselined on population of the source place, and adjusted up or down depending on what the place record promises (overwriting its original estimated population field).

Think of a sensible way to present the results to me so I can sense check in a useful way that doesn't require me to go through and check every match individually.

Do not rebuild LOD at this point.

## Delivered (2026-11-12, agent)

- Mined: `python -m tools.places sources-mine` (the extractor's `mine` mode, tools/ArgoniaPlaces/Extract/Mine.cs):
  locations, map markers and, for mods that place towns by cells alone (BM&V), built-up clusters; 1216 candidates
  from 18 plugin groups into out/newworld/sources/mined/, 821 usable (an exterior and 15+ refs). BM&V's Lilmoth left out.
- Matched: `python -m tools.places sources-match`: score = kind 0.38, text (bge-small) 0.14, size 0.14, status 0.10,
  culture 0.10, water 0.08, interior 0.06, plus 0.3 for the same name in a Black Marsh mod; one linear assignment
  with cost weighted by importance (1, 1.5, 2.5, 4, 6). Helstrom kept on bmv.helstrom.
- Stored: newworld/sources/source_match/ into the database tables `source_place` and `place_source` (rank 0
  allocated, 1-3 alternates, each score part); `place.population` from the allocated source, why in `place_source`.
- Loading: `python -m tools.places source <place_id> [--rank N]` writes the bundle (layout, interiors, bases, actors,
  navmesh, the source's terrain heights and land textures); importance 4-5 pre-extracted.
- Sense check: `python -m tools.places sources-page` -> out/newworld/sources/index.html; the atlas shows "Source place".
