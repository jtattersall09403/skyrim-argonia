# Mine similar places

Mine BM&Valenwood mod (for Blackrose, Thorn, and all of its minor places and POIs), King of the Murkmire (for all of its minor places and dungeons, plus any major places it has that we also have in our map), the other mods in our assets source list, and Skyrim itself (for any places not covered by the mods, or not covered enough - e.g. we need to have enough 'mines' and caves and ruins and so on to match up to all of the ones in our map) for places that are semantically similar to those in our game. Record a selection of similar places for each, ranked by similarity. (note we will be using the Tropical SKyrim version of all Skyrim assets if there is one).

After all collected, use an optimisation/matching algorithm to match up places in our new game/map to mined places. I want to end up with a matched 'source place' for each place in our map, such that no two of our places share the same source place. Factor into the optimisation:
* I didn't like Lilmoth in BM&V so don't use that
* Prioritise more major places getting a more similar match recorded as their top match. Weight the matching by this - the more major a place, the more weight is given in the optimisation to matching it a source place that is as similar as possible.

Record results in the database in whatever way will make it very fast and easy to load up any place's source place (including its full 3D layout and build and its local terrain in the game/mod where it was placed and all assets etc). Also record in the database 3 more other 'most similar places' for each of our places in the same way (it's OK for these other ones to be shared between our places, unlike with the optimised/allocated top 'source place').


Do not rebuild LOD at this point.
