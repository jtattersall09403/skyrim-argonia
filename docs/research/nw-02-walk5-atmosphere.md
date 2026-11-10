# Walk 5, lane A: a warm, steamy, regional atmosphere and more low mist (research)

The owner's two items (walk 5, 2026-11-10; `docs/phases/new-worldspace-plan/nw-02-walk-5-handover.md`): more and
stronger low-lying mist, "especially to the green marsh and blackwater swamp water areas and surrounds"; and light
and air that read warm and steamy, like Borneo or southern India, different by region and by latitude. The owner's
four steps are the four sections below: the real atmospheres (1), how games make them (2), how Skyrim does it and
what our build did (3), what we built from that (4). The recipe is `docs/design/atmosphere.md`; the numbers live in
`newworld/sources/atmosphere/` and are measured by `python -m tools.newworld.atmosphere study`.

## 1. The real atmospheres

Sources: standard tropical climatology and field-station records (Danum Valley Field Centre, Sabah; the Sebangau peat
swamp, Central Kalimantan; Kerala's Kuttanad and the Western Ghats stations at Munnar and Agumbe), the atmospheric
optics of haze (Koschmieder's visibility law; Hänel's hygroscopic growth of aerosol), and daylight colorimetry (CIE
daylight; measured direct-beam colour temperatures). Where a number is a range, the class takes a point inside it.

### 1.1 Lowland rainforest (Borneo: Danum Valley, Sabah, 5 deg N)

- Air: 22-23 C at dawn, 31-32 C in the afternoon; relative humidity 95-100 % at night and dawn, 60-75 % at 14:00;
  about 2,800 mm of rain on about 200 days, most of it in convective afternoon storms (14:00-18:00).
- Mist: at dawn the canopy steams; low cloud and radiation fog lie in the valleys and over the rivers and lift by
  08:00-09:30 as the sun warms the canopy. Cumulus builds from late morning; storms by mid-afternoon; after rain,
  steam rises off the wet canopy and ground in the sun.
- Light: above the canopy the direct sun is 5,500-5,800 K at high sun, a little lower (5,000-5,500 K) through humid
  haze; the overcast sky is 6,500-7,000 K. Under a closed canopy 1-2 % of the light reaches the floor, filtered
  green (leaves pass green and far red; the red to far-red ratio falls from 1.2 in the open to 0.2-0.6 in shade),
  broken by sunflecks: the ambient is a saturated, dim green.
- Distance: on a fair day 10-20 km; the far ridges lose contrast into a pale, whitish haze, not the blue of dry air.

### 1.2 Morning mist and its burn-off (all the lowland classes)

- Radiation fog forms on still, clear nights when the humid air cools to its dew point over wet ground and water;
  it is thickest just before dawn, a few metres deep, and lies in hollows and over water. Over water warmer than the
  dawn air it rises as steam fog.
- It burns off from the top and edges as the sun heats the ground: in Borneo and Kerala it is gone by 09:00-10:00 on a
  fair day; under cloud it can linger to late morning. It regathers after dusk on clear nights.
- After rain the wet ground and canopy steam in the first sun: a warm, sunlit, close fog.

### 1.3 Peat (blackwater) swamp forest (Sebangau, Central Kalimantan; Belait, Brunei)

- Water: humic and tannic acids stain it tea-brown to black (pH 3-4); its albedo is about 5 %, so little light comes
  back up from it.
- Forest: lower and more open than the dryland forest (pole forest to stunted padang), so more sky and more haze
  are seen, with a dark brown-olive floor.
- Air: the closest of all: humidity near saturation most of the day, ground fog most nights, heavy and still at noon.
  Its haze carries organic aerosol from the swamp (and, in dry years, peat smoke, the yellow-brown haze of the
  2015 fires); the haze reads amber to olive, never blue.

### 1.4 Green marsh and backwaters (Kerala's Kuttanad and Alappuzha; Borneo's open freshwater marsh)

- Ground: rice paddy, reed and water hyacinth on lagoons and canals at and below sea level; coconut palms on the
  bunds; the green is bright and yellow-green.
- Air: humid (75-90 %) and bright; the pre-monsoon sky is a hot white glare; after the monsoon the light is luminous
  and the greens saturated; mist lies over the paddies and canals at dawn.
- Light: high sun on wet paddy and water; the fill light is green, reflected from the crops; sunsets over the
  backwaters are gold and pink.

### 1.5 River corridors (the Kinabatangan and Rajang, Borneo; the Periyar, Kerala)

- Brown, silt-laden rivers in a humid valley; river fog at dawn, often a ribbon following the channel; clear, hot
  late mornings; storms in the afternoon; golden light on brown water in the evening.
- The haze is golden-white (sunlit moisture over warm water); the fill from the riverine forest is green.

### 1.6 Highlands, mesas and karst (the Western Ghats at Munnar and the Nilgiris; Mulu's karst and Kinabalu's lower slopes)

- Cooler (15-24 C by day) and less turbid: the air above the valley fog is crisper and the light whiter (sun
  5,800-6,000 K); ridges recede in layers into blue (the Nilgiris are named the Blue Mountains for it).
- The valleys below fill with fog at dawn, a sea of cloud seen from above; the ridges catch cloud in the afternoon;
  monsoon rain is orographic and heavy on the windward side.

### 1.7 Coasts and islands

- Windward monsoon coast (the Malabar coast in the south-west monsoon; Sabah's east coast in the north-east
  monsoon): wind, long swell, low grey-green overcast and rain off the sea; a silver-grey sea haze of salt aerosol.
- Mist coast (Borneo's south coast; the Sundarbans' creeks): sea mist most mornings over the shallows and mangrove;
  a warm, milky haze; mud and sand bounce the light.
- Sheltered bay coast facing west (Kerala's lagoons at sunset; Kota Kinabalu): sunny mornings, sea breeze by
  afternoon, squalls; the sun sets over the water in gold and red.
- Small islands (Lakshadweep; Sabah's offshore islands): the cleanest air (sea salt only, no land haze), the brightest
  light, turquoise shallows, short passing showers.
- Tropical day: about twelve hours all year at these latitudes; sunrise near 06:10, sunset near 18:20, twilight only
  20-25 minutes.

### 1.8 Humidity and haze distance

Koschmieder: visibility is inversely proportional to the extinction coefficient. Haze aerosol takes up water as the
relative humidity rises (hygroscopic growth): its extinction grows as f(RH) = (1 - RH)^-gamma, gamma about 0.25-0.6
for continental and marine aerosol (Hänel). We take gamma 0.5, and a temperate reference of RH 0.5 (Skyrim's
weathers are tuned for it), so a class's visibility against Skyrim's is sqrt((1 - RH) / 0.5) divided by its aerosol
load (peat swamp 1.15 for its organic haze; highland 0.8 and islands 0.85 for clean air; coasts 0.95; others 1).
Afternoon RH: peat swamp 0.88, rainforest 0.85, south coast 0.85, green marsh 0.82, river 0.80, east coast 0.80,
west coast 0.78, islands 0.75, highland 0.68.

Colour temperature by hour, used for the sun (CIE daylight and direct-beam measures): sun under 5 deg 2,000-2,800 K,
at 10-15 deg 3,000-3,500 K (our dawn and dusk slots, 2,700-3,300 K by class), high sun 5,000-6,000 K (our noon,
5,000 K in the peat swamp's haze to 6,000 K in the highland); moonlight through humid air is warmer than the cold
blue Skyrim draws (our night 6,000-7,500 K instead of Skyrim's saturated blue).

### 1.9 Latitude and season across the province

Black Marsh runs from the Morrowind border (cells y about -95) to the south coast (-242). As in the Indian
peninsula from the Deccan edge to Kerala, the north is the drier edge of the monsoon belt: clearer fair days,
harder storms (the Valley of Storms), less steam; the interior is the class as researched; the south coast belt on
the Sea of Mists is the hottest and most humid, with more mist and steam and fewer clear days. Bands: north above
cell row -135, south below -185, measured on each region's province cells (not its border scenery). The engine has
one climate per worldspace, so the bands shift the region's weather mix and its sun and haze, not the hours.

### 1.10 Our regions mapped to classes

`newworld/sources/atmosphere/regions.json` holds each region's class with the research note it rests on; the
database holds it with the measured band (`region_atmosphere`). Sea regions take the class of the coast they wash.

| Class | Regions (band) | Why |
|---|---|---|
| blackwater-swamp | Banujha Basin, Ultherus Swamp, Tulmek Washes (south); Blackwood (middle) | the most blackwater cells (561, 168, 331, 267); dark water, warm fog, steam after rain |
| green-marsh | Barsaebica (north); Okuwun-Rahei, Lake Ulaish (middle); Nushara Bayou (south) | the most green-marsh water (452, 408), reed and fen, pale lakes |
| river-corridor | Valley of Storms (north); Nha-Enasa (middle) | river plains cut by channels; thunder in the north |
| rainforest | Arnesian Jungle (north); Murkwood (middle) | tall forest, "light comes green and dim, the air thick" |
| highland | Chixathe Mesa, Aunike Ridge (middle) | mesa tops 60-110 m, a ridge above the marsh, drier, windy |
| coast-east | Hatandros Bight, Padomaic Ocean (middle); Benthic Yobesh (south) | the windward ocean coast: overcast, rain, sea mist |
| coast-south | Cape Percar, Sea of Mists (south) | mist most mornings on the Sea of Mists |
| coast-west | Kotherra Mangroves (middle); Topal Bay (south) | the bay coast: sea breezes, squalls, sunsets |
| island | Skeith Isle (middle); Aphon Isle, Althii Archipelago (south) | sea on every side, sea wind, the clearest air |

## 2. How games make warm, humid, tropical air (what transfers)

- Height and distance fog with a warm, bright colour: the single strongest cue. Humid haze scatters all wavelengths
  (Mie), so it is whitish-gold by day, not the blue of Rayleigh-scattered dry air; distant land fades into it.
  Transfers: the weather's fog near and far colours and distances.
- Warm key, cool or green fill: a warm sun against a fill coloured by the sky and the ground (green under canopy,
  brown over dark water, blue-green at sea). Transfers: sunlight colour, ambient and the six directional ambient
  colours (sides, from the sky, from the ground).
- Aerial perspective: far objects take the sky's colour; layered ridges recede into blue in the highland, into
  white-gold in the lowland. Transfers: fog far colour and the sky's horizon.
- God rays through canopy and mist: volumetric light shafts. Transfers: the weather's volumetric lighting records
  (where the engine's volumetric lighting runs).
- Volumetric and particle ground fog: low banks below eye level, drifting. Transfers: placed mist statics
  (Skyrim's own way, section 3.5); a ray-marched height fog exists in Community Shaders but is not in our profile
  (section 3.6).
- Bloom, tone mapping and grading: warm tint, slightly higher saturation for greens, soft bloom on bright haze.
  Transfers: the image space's tint colour and saturation, per weather and hour.
- Weather mixes: tropical games favour fair-humid and cloudy days with frequent short storms and post-rain steam
  over all-day fog. Transfers: the region's weather list.

## 3. Skyrim's way, and what our build did

### 3.1 The levers (records; measured with `ArgoniaPlugin atmos study` over Skyrim.esm, Update.esm, Black Marsh.esm, Black Marsh North.esp, Tropical Skyrim.esp)

- WTHR: colours per time of day (sunrise, day, sunset, night) for the sky (upper, lower, horizon), fog near and far,
  ambient, sunlight, effect lighting, sky statics, water multiplier; directional ambient (six directions per hour:
  the four sides, Z+ the light coming up from the ground, Z- the light coming down from the sky); fog distances
  by day and by night (near, far, power, max); four image spaces and four volumetric lightings, one per hour.
- CLMT: the weather list and the sunrise and sunset windows; the engine lerps night to day colours and fog across
  the sunrise window and back across the sunset one. One climate per worldspace.
- REGN: per region a weather list with chances; a cell's region (XCLR) picks the weather.
- IMGS: HDR, cinematic (saturation, brightness, contrast), tint (colour and amount).
- VOLI: intensity, custom colour and its share, density, phase function.

### 3.2 Bethesda's regional atmosphere

Bethesda gives each kind of country its own copy of the weathers: MA (Hjaalmarch's marsh), FF (the Rift's fall
forest), RE (the Reach), CO (the coast), TU, SN, VT; each region's list draws from its set. Chance-weighted over each
region's list (`newworld/sources/atmosphere/measured.json`):

| Region list | noon sun | noon fog near | noon fog far | noon ambient | dawn sun |
|---|---|---|---|---|---|
| Hjaalmarch (WeatherTundraMarsh) | (192,187,184) 6,176 K | (65,125,148) | (98,141,164) | (129,147,158) | (195,164,135) 4,246 K |
| the Rift (WeatherFallForest) | (196,186,174) 5,590 K | (42,82,111) | (127,174,200) | (134,157,177) | (190,154,129) |
| the Reach (WeatherReach) | (191,190,189) 6,388 K | (33,93,114) | (100,146,176) | (132,147,159) | (205,168,141) |
| the coast (WeatherCoast) | (161,171,174) 7,196 K | (34,88,115) | (109,146,168) | (119,164,192) | (192,162,138) |

The regions differ from each other by dE (CIE76) 10.7 (the Rift against the Reach) to 18.2 (Hjaalmarch against the
Rift) at their largest colour difference over fog near, fog far, ambient and sunlight at dawn and noon. Hjaalmarch's
marsh lists Cloudy 40, Clear 20, Fog 20, OvercastRain 10, Clear_A 5, Cloudy_A 5; its fog weather (SkyrimFogMA) is
0-50000 by day: Morthal's mist is not the weather's fog but placed statics (3.5). Every vanilla region reads cool:
noon fog near and far have warmth (R-B)/mean from -0.4 to -1.0.

### 3.3 BM&V and Tropical Skyrim

- BM&V uses Skyrim's base weathers through BlackMarshClimate (Black Marsh North.esp's winner): SkyrimFog 45,
  OvercastRain 20, StormRain 20, Cloudy 10, Clear 5. King of the Murkmire's regions use the same five (Fog 35-45).
- Tropical Skyrim overrides Skyrim's weathers and image spaces rather than adding its own: its fog near colours at
  noon are yellow-olive (SkyrimFog (182,185,68), SkyrimClear (136,138,68)), its far fog stays blue (SkyrimFog
  (164,180,210)), its image space tints are warm (ISSkyrimClearDAY_TU (224,203,165)) and its saturations high
  (1.3-2.25). Weighted over BM&V's list its noon sun is 7,678 K and far fog 13,454 K: no warmer than BM&V. The owner
  ruled before that our world is not Tropical Skyrim's atmosphere; we take its lesson (warm near fog, warm tints)
  and not its records.

### 3.4 Why the old build read cold and grey (measured on ArgoniaNewWorld.esm, build 20261109T204317Z)

The old build's climate and regions listed Skyrim's base weathers (SkyrimFog 30 to 55 %, ANW_AfterRainFog, the two
rains, and Clear and Cloudy copies with only their night fog changed). Chance-weighted over its climate:

| | noon sun | noon fog near | noon fog far | noon ambient |
|---|---|---|---|---|
| old build | (193,201,212) 7,505 K, warmth -0.10 | (49,89,110) warmth -0.74 | (100,120,136) 10,224 K, warmth -0.30 | (74,85,91) |
| BM&V | (198,207,217) 7,452 K | (49,83,100) | (91,111,128) 10,713 K | (74,85,91) |

Every slot is blue: the sun bluish white, the fog blue-grey, the ambient a dim blue-grey (SkyrimFog's day ambient is
(48,50,58)), and fog was half the weather. That is the cold grey the owner saw.

### 3.5 Hjaalmarch's low mist, measured (`ArgoniaPlugin atmos mist`, Tamriel cells x -22..2, y 8..30)

- 166 mist refs: FXMistLow01LongHalfVis 52, FXMistLow01Long 38, FXMistLow01HalfVis 36, FXMistLow01 29, a few
  street and mill-wheel mists. 43 % of the FXMistLow family is full opacity; within each opacity the long mesh is
  57 % (full) and 59 % (half).
- Over the DefaultMarshWater cells (72 + 19 transition cells): 3.53 refs a hectare (1.21 a cell), at most 5 in a
  cell; 96 over water and 70 over land (58 % over water); none with an enable parent or script (always on).
- Height: centre 1.27 / 1.81 / 2.71 m (p10/p50/p90) over the water, 0.67 / 1.82 / 2.80 m over land; scale 1.0 /
  1.45 / 1.88.
- BM&V's own: FXFog01 scaled 3 to 9, sunk 0.2 to 9 m below the surface, 340 refs over 1,408 BlackMarsh cells.
- The old build: FXMistLow01HalfVis 60 %, LongHalfVis 30 %, Long 10 % (10 % full opacity), centre 0.6-1.0 m,
  scale 1.3-1.6; over blackwater swamp 2.98 refs a hectare, green marsh 2.88, pond 2.94 (10,455 refs). A centre
  below 1.3 m buries much of a mesh 2.5 m tall at scale 1, and a tenth full-opacity is a quarter of Hjaalmarch's:
  that is why the mist the owner likes was thin.

### 3.6 Community Shaders in the NewWorld profile

- Community Shaders 1.9.1 is in both profiles. Its DLL has per-weather settings (a `Weathers` folder of per-weather
  JSON keyed by the weather's editor id) for the features that register weather variables: Exponential Height Fog,
  image-based lighting and wetness.
- Features installed in both profiles (the community-shaders row is `profile: play`, so the NewWorld profile has the
  same files): 26 `Shaders/Features/*.ini`: CSEditor, CloudShadows, DynamicCubemaps, ExtendedMaterials,
  ExtendedTranslucency, GrassCollision, GrassLighting, HorizonFix, ImageBasedLighting, InteriorSun,
  InverseSquareLighting, LODBlending, LightLimitFix, PerformanceOverlay, RemoteControl, RenderDoc,
  ScreenSpaceShadows, Screenshot, SkySync, SubsurfaceScattering, TerrainShadows, TruePBR, UnifiedWater,
  VolumetricLighting, VolumetricShadows, WaterEffects. Our overrides (`mods/dependencies.json`, community-shaders
  `files`) set VolumetricLighting `ExteriorEnabled: false` and lay an ExponentialHeightFog override with density 0.
- Not installed: Exponential Height Fog, the only Community Shaders feature that makes a volumetric ground or
  height fog. Its code is in the 1.9.1 DLL, but its add-on (its `Shaders/Features/ExponentialHeightFog.ini` and its
  shaders) is not laid: the row's `why` says "Its separate Exponential Height Fog add-on is NOT laid: with it the
  2026-11-03 sky went to a grey veil" (commit 0fa53c73, 2026-11-05).
- Where the off came from: not an owner ruling. It is a planner's entry of 2026-11-03 in docs/owner-brief.md (commit
  ea4a3909; that file was retired at the pivot, d269dbf5, and the entry is not in docs/owner-rulings.md): "Community
  Shaders' height fog and volumetric lighting are off for now (planner, from the sky bisect on Paris at 11:44): with
  them on the sky was a flat grey veil with no clouds and dawn a cream wash ... The low mist comes from the weather
  records only until the shader fog is re-authored within measured bounds." Round 6 then found the veil was our
  own sky templates, not Community Shaders (4e304b9b), turned its exterior volumetric lighting back on, and turned it
  off again when the dawn veil came back with no shafts (38c13f55). The owner's own words on Community Shaders are
  the 2026-11-05 row ("at its default features") and walk 5's "using volumetrics from community shaders where
  appropriate".
- What a Community Shaders low ground fog for the new world needs: (1) a mod row for the Exponential Height Fog
  add-on (a separate Community Shaders feature download), laid in the NewWorld profile only (a `profile: newworld`
  row, since the community-shaders row's files are shared by both profiles); (2) its global settings authored near
  the feature's defaults (density 0.005, falloff 0.2, start 0, the earlier measured bounds) with
  `volumetricFogEnabled` on; (3) per-weather files `SKSE/Plugins/CommunityShaders/Weathers/<editor id>.json` for our
  marsh and swamp weathers (fair, cloudy, mist, steam: dense and low at dawn), keyed on our editor ids, which no
  other card loads; (4) for light shafts in it, VolumetricLighting `ExteriorEnabled: true` in a NewWorld-only
  override. It is a call for the owner: the two earlier tries veiled the sky.
- The engine's own volumetric lighting is on in the prefs the stack writes (`bVolumetricLightingEnable=1`, stack.ps1
  line 115) and draws each weather's volumetric lighting records, so our per-class records take effect without it.
- Built in this lane: the native low mist (Skyrim's placed mist; the owner names it "the Skyrim native Hjaalmarch
  way"), denser and stronger, and per-class volumetric lighting records; no Community Shaders change.

## 4. What we built (the recipe is docs/design/atmosphere.md)

- Nine classes x their latitude bands in use = 17 weather sets of six kinds (fair, cloudy, mist, rain, storm,
  steam): 102 weathers, 408 image spaces, 68 volumetric lightings, the climate ANW_Climate and 24 region lists, at
  fixed form ids (weathers 080500-0805D7, image spaces 080000.., volumetric 080400.., climate 080600).
- Read back off a sample ESM written by the world writer's own code (`ArgoniaPlugin atmos sample`): 578/578 records
  at their ids with every field as the spec; 24/24 region lists; climate 05:00-11:00 / 16:30-20:30.
- Warmth, chance-weighted over the sets at noon: sun 5,524 K (warmth +0.12) against the old build's 7,491 K (-0.09),
  BM&V's 7,446 K and Tropical Skyrim's 7,678 K; far fog 6,457 K (warmth 0.00) against 10,211 K (-0.30), 10,824 K
  and 13,454 K.
- Distinct: the closest two classes (rainforest and river corridor) differ by dE 12.0, more than Bethesda's two
  closest regions (10.7); blackwater swamp against green marsh 15.7.
- Mist (all 24 regions, the current terrain build): 18,428 refs (was 10,455); refs a hectare over blackwater swamp
  water 5.93 (was 2.98; Hjaalmarch 3.53), green marsh 5.14 (was 2.88), pond 5.76, river and stream 2.62, sea 0.14
  (land cells of sea-typed cells) with none over sea water; full opacity 55 % in the blackwater swamp and 50 % in the
  green marsh (was 10 %); centre 0.92 / 1.15 / 1.38 m; at most 7 in a cell, natural plus mist at most 123 (cap 162).
