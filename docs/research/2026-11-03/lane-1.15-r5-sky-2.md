# Lane 1.15-r5-sky-2: the sky's paint from Tropical Skyrim's restyle; the neon mint and lime leaves

L1, from the bytes (`tools/argonia_world/terrain/esm.py`, `regions/api.py sky_winners`). The inputs were Skyrim.esm,
Update.esm and Tropical Skyrim.esp in `~/games/skyrimse/Data` (byte-equal to the MO2 copy), and the round-5 sky-ab
stills 02-05. L4 is owed (below).

## 1. What the game draws for our templates
Tropical Skyrim.esp overrides 38 vanilla WTHR, 111 IMGS and the SkyrimClimate **in place** (the same Skyrim.esm form ids).
Round 5 read every template from Skyrim.esm. The game never draws that copy where Update.esm or Tropical Skyrim
override the record (the same fault water had: layer.py `winners`). Measured at noon; sunrise is the first of each pair.

| template | plugin | skyUpper sr/day | skyLower sr/day | horizon sr/day | IMGS day HDR (bloom thr, bloom scale, sky scale) |
|---|---|---|---|---|---|
| SkyrimClear 00081A | Tropical | 425A79/**00204F** | 9DA1B5/**004693** | BA8167/**59B5E6** | ISSkyrimClearDAY 12F88: 0.23, 1.0, 0.235 (ESM 0.65, 4.0) |
| SkyrimClearFF 10A23B | Tropical | 425A79/**001E64** | 9DA1B5/**005CCE** | BA8167/6499B5 | ClearDAY_FF 10A1EE: **0.2, 0.95, 0.12** (ESM 0.6, 3.5, 0.3) |
| SkyrimClearFF 10A23B | Skyrim.esm (round 5) | 425A79/0C5A86 | 9DA1B5/5894B8 | BA8167/6499B5 | |
| SkyrimCloudyFF 10A23F | Tropical | 224044/**00188A** | 8B7755/**0B59A8** | 604522/**5CBCEB** | CloudyDAY_FF 10A1FE: 0.2, 0.9, 0.095 |
| SkyrimCloudyMA 10A233 | Tropical | 07242C/1E5162 | 658B86/5A7C8D | 60A0AC/B1CADC | CloudyDAY_MA 10A1CE: 0.175, 1.0, 0.05 |
| SkyrimClearMA 10A230 | Tropical | 466380/**00309F** | A9ADC3/**065EE1** | DD817A/6592A3 | ClearDAY_MA 10A1C2: 0.125, 0.8, 0.15 |
| SkyrimFogMA 10A232 | Tropical | A0ADA7/6F7386 | FFBEA8/697C96 | 847360/3B4B65 | FogDAY_MA 10A1CA: = ESM |
| SkyrimFog 0C821E | Tropical | A0ADA7/6F7386 | FFBEA8/697C96 | 7A685A/3C4965 | |
| SkyrimOvercastRainFF 10A23D | Tropical | 546565/8BA3A3 | 71713C/708C8D | 35321A/21353D | |
| SkyrimStormRain 0C8220 | Update (no Tropical) | 434950/677C83 | 8D6754/475A6D | 151515/112023 | StormRainDAY 0C8217: Tropical = ESM |

**Ours, authored, before this lane (noon / sunrise):**
- clear-dry: upper 4B86C8/577FAC, lower 91B5CD/C99A6A, horizon C7D6CB/E4B174.
- montane-haze: upper 6994C1, lower A6BABA, horizon BDC4BE.
- monsoon-overcast: upper 879695, lower AFAFA6, horizon B9BCAC.
- mist: upper B1C0BF, lower D1D9C3, horizon DBDFC8.
- sea-fog: upper A3B2B7, horizon CDD0CD.
- Every cloud layer of every non-clear weather was painted one cream-grey (its `cloudLodDiffuse`).

**Paler or greyer than Tropical's at noon:** clear-dry, tannin-haze, montane-haze and monsoon-overcast. Our zenith is
2-4x as bright and about half as saturated as Tropical's navy (001E64 to 00309F), and our horizon is near white.
Mist and sea-fog are greyer by design, but they still drew lighter than FogMA's 6F7386. Our day bloom (vanilla
scale 3.5-4) and sky scale (0.3) were Skyrim.esm's. Tropical cuts bloom to about 1 and sky scale to 0.05-0.235, so
its sky draws darker and more saturated.

**At sunrise:** Tropical leaves the dawn fields as vanilla's: upper 425A79 blue-slate, lower 9DA1B5 lavender,
horizon BA8167 rose-orange. Ours were close in hue (577FAC/C99A6A/E4B174). The grey-cream dawn came from the cream
cloud layers and the HDR, not from the sky slots. The dawn IMGS (ClearDAWN_FF 10A1EB) has no Tropical override, so
it is Update.esm's.

## 2. Re-templated (commit 93f39e30)
- `api.sky_winners` resolves each WTHR/IMGS template to the load order's last plugin carrying it. That plugin goes
  into the record as `templatePlugin`, and `RegionWeather.cs Winner()` opens it.
- Every weather takes from it the sky upper, sky lower, horizon and sun colours (`skyFromTemplate`) and every cloud
  layer's colours (`coloursFromTemplate`, now on all classes). Every IMGS takes its HDR and bloom from it.
- Kept as ours: fog near/far distances, curve and colours, sunlight, ambient (Pleasant: the template's), the cinematic
  grade, and the mist bank (CS height fog). Cloud alphas are unchanged.
- Templates moved, through db.py, to Tropical's class match:

| weather | old template | new template |
|---|---|---|
| clear-dry | SkyrimClearFF 10A23B | SkyrimClear 00081A (Tropical's most-restyled clear: navy zenith, blue horizon) |
| sea-fog | SkyrimFogCO 10A235 (no Tropical override) | SkyrimFog 0C821E |
| wet-rain | SkyrimOvercastRainMA 10A231 (no Tropical override) | SkyrimOvercastRainFF 10A23D |

  storm and squall stay on SkyrimStormRain, now resolved to Update.esm. Tropical's only storm, StormRainTU, is a
  yellow-brown tundra sky.
- `checks.weather_slots` now judges the sky paint that is written (`api.template_sky`). With the new horizons,
  horizon_line went red on 5 slots. Those fogFar slots were darkened through db.py to 0.85-0.86 of the horizon luma:
  - clear-dry sunrise: A08667 -> 8C755A
  - monsoon-overcast sunrise: 8D8B7B -> 807E6F
  - monsoon-overcast sunset: 8E7D66 -> 706250
  - montane-haze and montane-haze-68m day: A3AFAB -> 8A9490

  After the change, weather_slots (horizon_line, mist_fog_cast, derived) shows 0 errors.
- Proof: `test_sky_writer.py` writes the plugin and asserts, field by field per time of day, that the sky paint and
  the cloud layers equal the resolved template's (`checks.sky_paint`). It also asserts that SkyrimClear and
  ClearDAY_FF resolve to Tropical. Result: 234 passed, 5 skipped (regions and world tests).

## 3. The neon leaves at the western-frontier high vantage (commit 74654661)
Frustum census: the placement shards (out/terrain/vegetation) at vantage pos (-208896, 143616), yaw 180, +-50 deg,
10,000 u.

| form | refs | nearest (u) |
|---|---|---|
| Undergrowth01 | 80 | 3097 |
| SwampPlant02A | 75 | |
| FernCluster02B | 70 | |
| Groundplant10 (Tamira bush01) | 47 | 1255 |
| braken | 39 | |
| Erut08/03/01 | 21 | |
| **ShrubTree03** | 7 | 2660 |
| SwampTree03 | 4 | |
| deadwood | 4 | |

Shader flags were read from each NIF (new `leaf_hue.soft_lit`: BSLightingShaderProperty with SLSF2 Soft_Lighting,
Lighting Effect 1 = wrap). Across the stack's 123 soft-lit shapes the wrap counts are:

| wrap | shapes |
|---|---|
| 0.3 | 41 |
| 2.0-2.3 | 10 |
| 5.0 | 64 |
| **10.0** | **8** |

The 10.0 shapes all sit on King of the Murkmire's shrubtree01-04, shrubtreestump01 and cypress branchpile01/02 leaf
cards (snowgumbranches01_d, olive hue 62, sat 0.47; vertex colour pale grey 200-212). No emissive (0) and no glow
map on any of them. An olive card wrapped at twice the stack's ceiling is lit through by the blue sky, which gives
the mint "ghost trees": the left tall tree and the right group are ShrubTree03.

The lime palm is Groundplant10. Its anvilleafpalm02 diffuse has sat 0.86, the highest leaf saturation bar a dark oak
card, at a soft wrap of 0.3. Lore: the undergrowth is natural ferns and grasses under blue moss
(topics/loading-facts.md:301; 0032).

Dropped: `lists.usable` and the make-check `textures check` now drop or fail any form whose wrap exceeds
`SOFT_WRAP_MAX` 5.0. That takes out ShrubTree03, ShrubStump/B and CypressBranchpile01/02. Groundplant10 went to
LOOK_DROP with its numbers. Lists rebuilt (`forms --lists-only`):

| measure | before | after |
|---|---|---|
| placed forms | 210 | 204 |
| the 6 forms' list rows | 39 | 0 (re-drawn; land_region_object stays 1399) |
| textures check problems | | 0 |
| vegetation tests | | 47 pass, incl. the new test_leaf_hue_soft.py |

Still placed: SwampPlant02A's red vertex colour is a report only (the owner allows red leaves, #37).

## Owed in game (checks.md row; planner's batch, needs a rebuild of Argonia.esm, ArgoniaWorld.esm and the vegetation)
sky-ab again, shaders on: coastal-lagoon-shore and western-frontier-high, noon and dawn. A reader checks for:
- a deep blue zenith at noon (no pale grey-blue);
- a coloured dawn (a blue-slate zenith over a rose or orange horizon, not a grey-cream wash);
- no neon mint or lime leaves at the western-frontier high vantage.
