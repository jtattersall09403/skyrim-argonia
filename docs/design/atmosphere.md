# The new world's atmosphere: weather, light and low mist by region

How the new world's air is made: warm, steamy and tropical, different by region and by latitude, with low mist
drifting below eye level over the marsh and swamp water. Research and every measured number:
`docs/research/nw-02-walk5-atmosphere.md`. Code: `tools/newworld/atmosphere.py`, `tools/newworld/world/mist.py`,
`tools/ArgoniaPlugin/NewWorldAtmosphere.cs`. Sources: `newworld/sources/atmosphere/`.

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
   (at least 1 each, summing to 100). The climate lists the default set.
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
- Height: centre 0.9 to 1.4 m over the water or ground (below eye level); scale from the class; random yaw.
- At most 8 in a cell; natural plus mist refs within the placer's 162 a cell.

## The pipeline (tools/newworld/world/world.sh)

`world/cells.py` (water and regions) -> `world/mist.py` (refs/mist) -> `atmosphere.py spec` (reads the vanilla
records through `ArgoniaPlugin atmos study`, writes `atmosphere.json`) -> the ESM write (`NewWorldAtmosphere.Build`
makes every record from `atmosphere.json`; the regions take their lists) -> the read-back. The database's
`atmosphere_class` and `region_atmosphere` come from `build_db` (`atmosphere.load`).

## Proof off game

- `python -m tools.newworld.atmosphere check --plugin <dir>`: every record at its id with every field as the spec,
  every region's list, the climate, the classes at least as distinct as Bethesda's two closest regions, and warmer
  than the build before walk 5 and BM&V (`measured.json`, from `atmosphere study`).
- `python -m tools.newworld.atmosphere swatch`: per set, the fair weather's sky, horizon, fog near and far, ambient
  and sun at dawn, noon, dusk and night, beside the old build's and Tropical Skyrim's.
- `ArgoniaPlugin atmos sample <dir> <Data> <out.esm>` writes only the atmosphere's records through the writer's own
  `Build`, for a proof without the world.
- `tools/newworld/verify.py`: the same atmosphere rows on the built world, and the mist rows (density by water kind
  against Hjaalmarch and the old build, graded by class, opacity, height, budget, none at sea).

## Community Shaders

Its exponential height fog is not in the profile and its exterior volumetric lighting is off by the owner's round-5
ruling (both veiled the sky grey). The engine's volumetric lighting uses our per-class records. Turning Community
Shaders' fog on for the new world is an owner call; its per-weather settings would key on our weathers' editor ids.
