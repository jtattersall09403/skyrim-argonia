# The new world's atmosphere: weather, light and low mist by region

How the new world's air is made: warm, steamy and tropical, different by region and by latitude, with low mist
drifting below eye level over the marsh and swamp water. Research and every measured number:
`docs/research/nw-02-walk5-atmosphere.md`. Code: `tools/newworld/atmosphere.py`, `tools/newworld/world/mist.py`,
`tools/ArgoniaPlugin/NewWorldAtmosphere.cs`, `tools/newworld/atmosphere_cs.py` (Community Shaders' height fog).
Sources: `newworld/sources/atmosphere/`.

## The model

- **A class per region.** Each region has an atmosphere class: a real tropical atmosphere (peat swamp, green marsh
  and backwater, river corridor, lowland rainforest, highland, the east, south and west coasts, islands).
  `regions.json` names it with the region research it rests on; a sea region takes the class of the coast it washes.
- **A band per region.** North (by the Morrowind border), middle or south (the south coast belt), measured from the
  mean cell row of the region's province cells (not its border scenery). The band shifts the class's sun, humidity
  and weather chances (`classes.json` `bands`).
- **A weather set per class and band.** Six kinds: fair, cloudy, mist, rain, storm, steam (the air after rain). Each
  is our own copy of the vanilla weather of the same kind in the Bethesda regional set the class's family names
  (marsh: Hjaalmarch's MA; forest: the Rift's FF; upland: the Reach's RE; coast: CO), the load order's winner, with
  its own four image spaces; the set has four volumetric lightings shared by its non-rain kinds.
- **One climate.** The worldspace's climate (one per worldspace in the engine) carries the tropical day and the
  default list (the green marsh's middle set).

## The records

1. **Colours.** For each colour slot and hour, keep the source weather's luminance (Bethesda's level for that
   weather and hour) and take the class's hue (`recolour`):
   - sunlight and effect lighting: the black body at the class's colour temperature for the hour plus the band's
     offset (`sun_k`);
   - fog near: the class's haze for the hour; fog far: the haze a quarter of the way to the sky;
   - ambient and the four side directions of the directional ambient: the class's fill;
   - directional ambient from the ground (Z+): the class's ground colour; from the sky (Z-): sky and fill halved;
   - sky upper: the class's sky; sky lower and horizon: sky toward haze (0.6); both mixed over the source by the
     class's `sky_mix`.
   By day the fog's luminance is multiplied by the class's fog gain (steam 1.1 more), the ambient by its ambient
   gain and the sun by its sun gain. Rain and storm take the class's hue at 0.7 and 0.6 strength so they keep their
   overcast character.
2. **Fog distances.** Start from Skyrim's base weathers of the same kind (`reference_fog`: Clear, Cloudy, Fog,
   OvercastRain, StormRain) and multiply by the class's visibility, sqrt((1 - RH) / 0.5) / aerosol, RH being the
   class's afternoon humidity plus the band's offset. Day near is 0. Steam's day far is the mist's times
   `steam_scale`.
3. **The dawn mist.** Fair and cloudy weathers get a dense night slot (near 0, far `night_mist.far`, power 0.4, max
   `night_mist.max`). The climate's sunrise window (05:00-11:00) lerps it to the day slot: thick at dawn, gone
   before noon; the sunset window (16:30-20:30, centred on the tropical sunset at about 18:30) brings it back.
4. **Image spaces.** Copy each source weather's image space per hour; set the tint colour to the hour's sun mixed
   0.3 toward the haze (at the kind's strength) and the saturation to the source's times the class's `saturation`.
5. **Volumetric lighting.** Copy the class family's fair weather's volumetric lighting per hour; set its custom
   colour to the haze, its colour share and density from the class (`voli`).
6. **Region lists.** Each region lists its set's six weathers with the class's chances plus the band's shifts
   (at least 1 each, summing to 100), with the Override flag and priority 50 as Bethesda's regional sets carry them
   (50 to 55), so the region's list replaces the climate's. The climate lists the default set.
7. **Form ids are fixed** (`atmosphere.py` `BASE`): image spaces 0x80000 + set x 24 + kind x 4 + hour, volumetric
   0x80400 + set x 4 + hour, weathers 0x80500 + set x 8 + kind, climate 0x80600, where set = class index x 3 + band
   index in `classes.json` order. A weather's console id is the new world file's load index followed by its id
   (`fw <index>0805XX`).

## The low mist

Skyrim's own way (Morthal's): always-on `FXMistLow01` statics, no script.

- A jittered 25 m lattice; a site is kept with the chance density x 3.53 / 16, where 3.53 is Hjaalmarch's mist refs
  a hectare over its marsh water and the density is the region class's (`classes.json` `mist.density`, a multiple
  of Hjaalmarch's) times the site's weight, raised over still water and its 20 m banks to the water kind's floor
  (blackwater swamp 2.0, green marsh 1.8, pond 1.2; banks 0.8 of it), so those waters carry their mist in any region.
- Weights: still water and marsh or swamp habitats 1; banks of still water 0.8; mangrove 0.7, Hist grove 0.5,
  hummock 0.45; flowing water 0.25; the sea, bays and lakes 0, nor within three samples of a sea cell's water.
- Opacity: the class's full-opacity share (`mist.full_vis`, at least Hjaalmarch's 43 %) of `FXMistLow01Long` and
  `FXMistLow01` (57 : 43), the rest `FXMistLow01LongHalfVis` and `FXMistLow01HalfVis` (59 : 41).
- Height: centre 0.9 to 1.4 m over the water or the ground under the ref (bilinear on the heightmap, as the game
  reads its LAND); below eye level; scale from the class; random yaw.
- At most 8 in a cell, and never more than the placer's 162 refs a cell leave after the cell's flora refs
  (`refs/flora`), so `world/mist.py` runs after the placer.

## The pipeline (tools/newworld/world/world.sh)

`world/cells.py` (water and regions) -> `world/mist.py` (refs/mist) -> `atmosphere.py spec` (reads the vanilla
records through `ArgoniaPlugin atmos study`, writes `atmosphere.json`) -> the ESM write (`NewWorldAtmosphere.Build`
makes every record from `atmosphere.json`; the regions take their lists) -> `atmosphere_cs.py write` (the height
fog's files into the `cs-height-fog` row; then `stack.py stage`) -> the read-back. The database's
`atmosphere_class` and `region_atmosphere` come from `build_db` (`atmosphere.load`).

## Proof off game

- `python -m tools.newworld.atmosphere check --plugin <dir>`: every record at its id with every field and every
  hour's image space and volumetric lighting link as the spec; every region's list, with the Override flag and
  priority at least 50; the climate's list, chances and four sun times; the classes at least as distinct as
  Bethesda's two closest regions (`measured.json`, from `atmosphere study`); warm: noon sun at most 6,000 K with
  warmth at least +0.05 and far fog warmth at least -0.10.
- `python -m tools.newworld.atmosphere swatch`: per set, the fair weather's sky, horizon, fog near and far, ambient
  and sun at dawn, noon, dusk and night, beside Skyrim's base weathers (BM&V's) and Tropical Skyrim's.
- `ArgoniaPlugin atmos sample <dir> <Data> <out.esm>` writes only the atmosphere's records through the writer's own
  `Build`, for a proof without the world.
- `tools/newworld/verify.py`: the same atmosphere rows on the built world, and the mist rows (at least 1.4 x
  Hjaalmarch's density over blackwater swamp and green marsh water, graded by class, opacity, every centre 0.5 to
  2.0 m over its surface, budget, none at sea).

## Community Shaders: the low height fog (NewWorld profile only)

Over the placed mist, Community Shaders' Exponential Height Fog draws a low, warm fog layer per weather, with light
shafts in it. Code: `tools/newworld/atmosphere_cs.py`. Everything below is laid in the NewWorld profile only; the
Argonia profile (Black Marsh & Valenwood) keeps the community-shaders row's files.

1. **The add-on.** The `cs-height-fog` row (`mods/dependencies.json`, `profile: newworld`) is the feature's release
   asset built with the Community Shaders the stack lays (v1.9.1; its DLL requires the feature at 1-3-2, which this
   asset is). `pick: ["Shaders"]` lays its feature ini and shaders. When Community Shaders moves, the row moves to the
   same release's asset.
2. **The two global overrides** sit at the community-shaders row's paths
   (`SKSE/Plugins/CommunityShaders/Overrides/Argonia_ExponentialHeightFog.json`, `..._VolumetricLighting.json`), so in
   the NewWorld profile the newworld row's copies win:
   - height fog on, replacing the vanilla fog (`disableVanillaFog`); no sky cubemap and no added colour; any weather
     not ours takes the feature's shipped values (density 0.005, falloff 0.2);
   - volumetric lighting on outdoors (`ExteriorEnabled`, medium quality). Community Shaders sets the engine's
     `bEnableVolumetricLighting` from it every time the player goes outdoors, so this switch is what lets our
     weathers' volumetric lighting records draw.
3. **One file per weather of ours**, `SKSE/Plugins/CommunityShaders/Weathers/0x<local form id>~ArgoniaNewWorld.esm.json`
   (Community Shaders keys a weather by its local form id, hex upper case, and the plugin that defines it), holding
   `{"featureSettings": {"ExponentialHeightFog": {"__enabled": true, ...}}}` with the names the feature registers:
   - **Fog Density**: the fog 90 % thick along its floor at the weather's own day fog far (the record's visibility
     for its class and band; the shader's level ray fades as 2^(-d L ln 2), d = density / 1000), times the class's
     strength (blackwater swamp and green marsh 1.4, river corridor 1.2, rainforest 1.1, south coast 1.0, east and
     west coasts 0.7, islands and highland 0.5) and the kind's (fair 0.7, cloudy 0.9, mist and steam 1.0, rain and
     storm 0.5), at most 1;
   - **Fog Height**: the class's floor, the 75th percentile of the surface (water at 0) over its still and flowing
     water and its marsh habitats on the current terrain, rounded to 10 units; below the floor the fog is full;
   - **Fog Height Falloff** 2.0, the feature's maximum: the fog halves every 500 units (7 m) above the floor, so it
     fills the hollows and lies over the water, and the mesa tops and the sky stay clear;
   - **Directional Inscattering Multiplier**: the sun scattered forward in the fog (anisotropy 0.6, global): fair and
     steam 1.0, cloudy 0.8, mist 0.4, rain and storm 0.2;
   - **volumetricFogEnabled** in the sunlit kinds (fair, cloudy, steam), out to 20,000 units, its **Volumetric
     Albedo** the weather's day fog near colour scaled to a top channel of 1: the fog is lit and shadowed, so the sun
     falls through canopy gaps in shafts;
   - **the veil guard**, also global but stated in each file: `disableVanillaFog` true, **Original Fog Color Amount**
     1 (the fog's colour is the weather's own fog colour at the hour), the added colour's and the cubemap tint's
     alphas 0. With the vanilla fog kept, Community Shaders' composite paints every sky pixel with the weather's far
     fog colour at its fog maximum: a flat veil with no clouds.
   The feature has no time of day: a weather's values hold at every hour; the dawn mist of the records' night fog
   slot shows in the fog's colour only.
4. **Generated, then staged.** `python -m tools.newworld.atmosphere_cs write` writes the row's `files` (the two
   overrides and the 102 weather files) into the manifest from `atmosphere.json` and the terrain; `stack.py stage`
   lays them like any row's files (a changed file re-stages the row alone).

Pipeline place: after `atmosphere.py spec` and the terrain, before `stack.py stage` and the deploy.

Proof (`python -m tools.newworld.atmosphere_cs check`, and the "height fog" rows of `tools/newworld/verify.py`): one
file per weather, parsed back, each value inside the range the feature registers; every block enabled; the veil
guard in every file; the sky through the fog from the floor (the shader's integral): at least 0.7 of the sky's own
colour at the zenith in every weather and 0.8 at 15 degrees in fair and cloudy weather; the peat swamp and green
marsh thicker than the highland, coasts and islands; mist and steam thicker than fair and cloudy; the manifest's
files equal the generator's; the add-on and the files laid in NewWorld by the row and in Argonia not at all; the two
overrides from this row in NewWorld and from community-shaders in Argonia; the staged add-on's version 1-3-2.

If the sky looks veiled in game, the one switch is the Community Shaders menu's Exponential Height Fog, "Enable
Exponential Height Fog": off, the weathers' own fog returns as built.
