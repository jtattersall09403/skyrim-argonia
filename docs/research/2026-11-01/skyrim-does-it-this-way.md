# Skyrim does it this way: the 1.15 audit against Skyrim.esm (decision 0034)

Measured 2026-11-01 on Tamriel in Skyrim.esm with Update.esm's cell overrides (11,186 cells, 250,830 refs; Update
re-states 510 water heights). Scripts: `tools/argonia_world/vanilla/` (`load.py` caches, `measure.py qN` prints
each answer as JSON; README there). Units are Skyrim units (70.03 u = 1 m; a vertex is 128 u = 1.83 m). Every
Tamriel cell has the has-water flag; the world's default water is −14,000 u (the sea), so a cell without XCLW
still has sea water under its ground.

## Most consequential changes

1. **Ground (shores, q1):** our marsh and sea grades are 3–8× flatter than any vanilla shore. Vanilla's flattest,
   Morthal's marsh, rises 0.06 at the first vertex and ~0.25 by the fifth; its bed falls 0.19 then lies flat at
   ~80 u (1.1 m). Set `SHORE_GRADE`/`BED_GRADE` from the table below.
2. **Water (q2):** vanilla carries a lake's level into every cell the water touches, padding cells with no wet
   vertex at all. There are no dry cells inside a footprint. Drop the 'dry cell' class inside a body.
3. **Materials (q4):** vanilla blends are short, 1 vertex median and 5 at p90, against our 6–17. VCLR is mostly
   white, with darkening only at the water and never by slope. Shorten the blends and drop slope/aspect shading.

## 1. Shores

*Aim:* a believable ground profile from bed to bank. *Bethesda faced it:* yes, at every lake, sea and marsh.

| median, u | Lake Ilinalta (level 600) | Solitude sea (−14,000) | Morthal marsh (−14,000 / −12,350) |
|---|---|---|---|
| depth 1 / 2 / 3 / 5 / 8 vertices in | 32 / 96 / 152 / 272 / 432 | 32 / 96 / 184 / 336 / 528 | 24 / 48 / 64 / 80 / 80 |
| cell-centre depth p10/p50/p90 | 288 / 600 / 712 | 264 / 440 / 856 | 24 / 48 / 51 |
| rise 1 / 2 / 3 / 5 / 8 / 10 vertices out | 24 / 80 / 128 / 240 / 480 / 648 | 24 / 88 / 152 / 304 / 508 / 728 | 8 / 40 / 72 / 160 / 264 / 326 |
| slope over the first 10 vertices above, p50 (p90) | 17° (39°) | 21° (61°) | 12° (25°) |
| slope over the first 3 vertices below, p50 | 20° | 21° | 8° |

The grade (rise per run) at the line: lake and sea 0.19 for the first vertex, then 0.375–0.47 over 5 vertices.
The marsh is 0.06, then 0.25 over 5 vertices. Its bed is 0.19 for one vertex, then flat at 64–80 u. Banks keep
rising past 10 vertices: 330 u in the marsh, 650–730 u at the lake and sea.

*Ours:* `generate.SHORE_GRADE` sea 0.03, brackish 0.04, blackwater 0.08, fresh 0.35; `BED_GRADE` 0.03 / 0.05 / 0.1 / 0.4;
the grade runs out 40 samples.
**Verdict: differs. Change (ground):** fresh 0.35 matches Ilinalta, so keep it. Brackish, blackwater and sea take
the Morthal profile: 0.06 at the first vertex, easing to 0.25 by 5 vertices, then ~0.1 to +330 u at 10 vertices.
Their beds take 0.19 for 1–2 vertices to a flat at 64–80 u, which is the marsh depth (cell centre 48 u). The
open sea (not the mangrove marsh) takes the Solitude column.

## 2. Partly-wet cells and holes

*Aim:* no square cuts where water meets a cell edge. *Faced:* yes, at every multi-cell lake and marsh.
- 510 cells carry an explicit level. The wet share of their vertices is p25 0.1, p50 0.2 and p75 0.4. 119 cells
  (23 %) are under 10 % wet, and **23 have no wet vertex at all**: the level is carried into a padding ring.
- 188 default-level cells sit between two or more explicit-level cells. In 141 the ground stands wholly above the
  neighbours' level. Only 8 dip more than 25 % below it, and Update.esm re-states 6 of those.
- The sea needs no record: every cell has water, so marsh ground below −14,000 is wet wherever it lies.

*Ours:* `cell_water` leaves 'dry cells' inside marshes, so the neighbour's water stops on the cell edge (ground
lane, reader on 96e7247). **Verdict: differs. Change (water):** a body's level goes into every cell the body's
footprint touches, plus a one-cell ring where the ground stands above it (vanilla's padding). Never leave a dry
cell inside or between cells of one level. The edge-bank workaround (`edge_bank`) then only applies at true
level steps (§11).

## 3. Cliffs and steep ground

*Aim:* how steep the ground gets, and how steep ground is dressed. *Faced:* yes.
- Slope over 12.18 M vertices: 0–10° 17 %, 10–20° 23 %, 20–30° 20 %, 30–40° 15 %, 40–45° 6.5 %, 45–60° 14 %,
  60–75° 4.7 %, 75–83° 0.35 %. The maximum is 86.5°, and 19.2 % of vertices are over 45°.
- The LAND itself is steep. Cliff and mountain STATs are sparse: cells with ≥ 20 % of vertices over 45° average
  1.6 such refs, and only 52 % have any. Flat cells average 0.4. The top forms are MountainTrimSlab, RockCliff03,
  MountainCliff02, RockCliff06 and RockCliff04. Half of all steep ground is bare, textured LAND.

*Ours:* a 75° limit, and a cliff mask over 60° that is dressed with KotM rock-wall shells at slope ≥ 25°.
**Verdict: same in kind. Change (ground, vegetation):** keep the 75° limit (vanilla has 0.35 % above it).
Expect ~5 % of vertices over 60°. Do not dress every cliff-mask cell: about half of vanilla's steep cells carry
1–2 shells and the rest are bare.

## 4. Materials

*Aim:* textures per cell, blend width, VCLR, and the bed-to-land sequence. *Faced:* yes.
- Layers per quadrant, counting the base: 1: 2,550; 2: 5,805; 3: 5,518; 4: 5,492; 5: 5,291; 6: 7,276; 7: 335.
  So the cap in practice is base + 6, and 6 is the most common count.
- Distinct LTEX per cell: p50 4, p90 8, p99 10. Per region: p50 13, p90 24.
- **Alpha ramp:** a run of vertices strictly between 0.02 and 0.98 is 1 vertex at p10 and p50 and 5 at p90.
  The median step between neighbours is 0.2. Vanilla's blends are painted brush strokes, a vertex or a few wide.
- **VCLR** is in 5,644 cells (half). Luminance is p50 255 (untouched) and p10 185, and only 13.9 % is under 200.
  Steep ground (>40°) is not darker: its p10 is 198, against 165 on flat ground. The darkest band is within 256 u
  of water (p10 149).
- **Sequence** (the dominant LTEX by height above the local water, all cells with a shoreline):
  - Rivers and lakes: LRiverBottom01 below −384; LRiverMud01(NoGrass) and LRiverbedEdge01 from −384 to 0;
    **LRiverbedEdge01 carries on 0 to +128** (one vertex above); land textures (LFallForestDirt01, LRocks01NoRocks,
    LReachDirt01) from +128.
  - Sea: LCoastOceanFloor01 and LCoastBeach01 below; **LCoastBeach01 from 0 to +256** (42 %, then 30 %); then land
    (snow on the north coast).

*Ours:* base + up to 5; 19 LTEX with 4–6 per class; class blend ~30–45 m; material blend 6–17 vertices; VCLR as
slope/aspect shade × wet; the edge reads bed → waterline → mud → land.
**Verdict: differs. Change (materials):**
- Material blend: 1–5 vertices (p50 1).
- Keep the class blend only where classes change.
- Allow base + 6.
- VCLR: white by default. Darken only within ~2 vertices of water and on wet flats (to ~150/255), and drop the
  slope and aspect terms.
- Sequence: river bed, then mud and edge from −384 u to the line, then **the edge texture to +128 u**, then
  land. There is no mud band above the water. Sea shores take the beach band from below the line to +256 u.

## 5. Rocks

*Aim:* rock seating. *Faced:* yes (43,000 rock refs).

| class (n) | sunk share of OBND height p10/p50/p90 | sunk u p50 | tilt − ground slope p10/p50/p90 | upright (< 2°) |
|---|---|---|---|---|
| boulders RockL/M/S (17,199) | 0.1 / **0.5** / 0.8 | 84 | −29° / −2° / +18° | 26 % |
| rock piles (14,392) | 0.3 / **0.5** / 0.8 | 52 | −21° / −2° / +6° | 14 % |
| cliff/mountain shells (11,586) | 0.4 / **0.7** / 0.9 | 677 | −45° / −11° / +16° | 24 % |

*Ours:* boulders sink 0.38 and shells 0.25; rocks conform to slope.
**Verdict: differs. Change (vegetation):** boulders and piles sink 0.5 (jitter 0.1–0.8), and cliff shells 0.7
(0.4–0.9). Conforming to the slope is the same as vanilla, which tilts with the ground (median 2° under it),
but about a quarter of vanilla's rocks stand upright. Shells tilt ~11° less than the slope.

## 6. Vegetation density

*Aim:* stems per cell, and distance from water. *Faced:* yes.
- TREE refs (excluding shrubs and plants) per cell, by the cell's dominant ground:

  | ground | trees per cell, mean (p90) | flora per cell |
  |---|---|---|
  | forest | 31 (53) | 24 |
  | pine | 28 (44) | 16 |
  | marsh | 18 (36) | 9 |
  | tundra | 15 | 12 |
  | rock | 12.5 | 9 |
  | field | 10 | 11 |
  | shore | 2 | 2 |
  | snow | 6.6 | 2 |

  A cell is 0.342 ha, so forest is ~90 trees/ha and marsh ~52.
- In 12,413 trees in cells with surface water, 5.8 % stand below the waterline. Distance to the nearest wet
  vertex is p5 98 u, p10 198 u and p50 996 u, and 13.9 % stand within 256 u (3.7 m).

*Ours:* the cap is already calibrated to vanilla's forested cells (`VANILLA_P95` 83 and `VANILLA_MAX` 162 refs per
cell, trees plus rocks), with water posture per form. **Verdict: same. Change (vegetation):** add a check that a
dry-land canopy region's trees per cell sits in the band above (marsh ~18, forest ~30). Dry-land trees keep
≥ ~200 u (3 m) from the waterline for 90 % of stems; only water-posture forms (mangrove, gallery) stand in water.

## 7. Weather

*Aim:* authored palettes inside vanilla's ranges. *Faced:* yes (84 WTHR, 53 region weather lists).
- Fog distances (FNAM, u), p10/p50/p90:

  | class (n) | day near | day far | night far |
  |---|---|---|---|
  | pleasant (36) | 0 / 0 / 1,200 | 50k / 85k / 100k | 40k / 50k / 50k |
  | cloudy and fog (16) | 0 | 9k / 30k / 50k | — |
  | rain (12) | — | 15k / 20k / 39k | 10k / 15k / 31k |

  Named weathers, day far / night far: SkyrimFog 25,000 / 15,000; SkyrimFogMA, CO and FF 50,000 / 35,000;
  SkyrimStormRain 25,000 / 10,000; OvercastRain 15,000 / 15,000 with near 1,000–1,200. Fog power is 0.35–0.45 and
  max 0.9–0.95.
- Ambient over sunlight luminance: pleasant 1.2–1.3 at every time of day; cloudy ~0.5; rain 0.4 by day and 0.1 at
  night.
- Region lists: 1–6 entries (p50 3), chances sum to 100 in every list, and **0 of 175 entries use a global**.
  Marsh: WeatherTundraMarshNoPrecip is CloudyMA 44, FogMA 28, ClearMA 18 and two 5 % variants. Coast:
  WeatherCoastFog is FogCO 100. Falkreath: OvercastRain 35, Fog 35, StormRain 20, Clear 5, Cloudy 5.

*Ours:* mist 0/180 m day far (12,600 u) and 120 m night (8,400 u); storm 350/250 m (24,500/17,500 u); squall 500 m;
tannin haze 900/500 m; mist entries driven by `ARG_WMist_<regime>` globals gated by hour.
**Verdict: differs. Change (weather):**
- Mist's day far goes to ≥ 25,000 u (357 m) and its night far to ≥ 15,000 u (214 m). Vanilla's thickest fog is
  SkyrimFog's; ours sits below vanilla's p10.
- Storm, squall and haze are inside the ranges: same.
- Lists hold fixed chances summing to 100, with fog weathers at 28–35 % in marsh lists.
- Drop the hour-gated globals. Vanilla never uses a global and has no hour gate, because a fog weather carries
  its own time-of-day fog.
- The seasonal shift is a problem Bethesda never faced, so a global may carry it.

## 8. Mist

*Aim:* confirm 'weather fog first, placed mist last'. *Faced:* yes.
- 472 low-mist MSTT refs (FXMistLow01HalfVis 190, LongHalfVis 81, Long 76, FXMistLow01 62, FXMistStreet01 37)
  in **296 of 11,186 cells (2.6 %)**, a median of 1 per cell and 3 at p90.
- They lie on flat ground (median 7°). 54 % are in cells with surface water, but they are placed at named sites:
  Witchmist Grove, Bthardamz, Falkreath, Riverwood and Rkund, 4–5 each.
- They are spread across ground types (field 58, tundra 55, marsh 50), not laid as a marsh blanket.

**Verdict: same: confirmed.** Weather fog carries the air everywhere. Placed mist is a site dressing (1–3 per
cell at places), never a regional layer.

## 9. Worldspace edges

*Aim:* how Tamriel's border and far ground are built. *Faced:* yes.
- BorderRegionSkyrim is one 173-point polygon. Inside are **5,411 cells**; outside, **5,775 cells of LAND** run to
  the world bounds (cells −57..61 × −43..50; NAM0/NAM9 −233,472…253,952 × −176,128…208,896).
- Outside the border, cells have p50 0 refs (19 % have any), 0 trees, p50 0 alpha layers (base texture only,
  8 at p90) and VCLR in 15 %. Relief is larger than inside (p50 2,896 u against 2,072): a mountain wall of
  plain LAND.

*Ours:* an apron from All-Tamriel heights blended to the province, painted with the nearest province class and
its full blend. **Verdict: same in kind. Change (ground, materials):** the far ground outside the border is plain
LAND: base texture per quadrant (no ATXT), no refs, no VCLR. Stop running the province's material blend into the
apron. The border is one region polygon. Vanilla's far ground is as large as the playable area.

## 10. Dungeon entrances

*Aim:* the ground around entrances. *Faced:* yes (136 teleport doors of cave, Nordic, Dwemer and mine kinds; 24
sampled across them).
- The ground 1,024 u around stands **above the door's ground by p50 553 u** (p10 46, p90 917). Slope at the door
  is p50 35° (p10 10°, p90 59°).
- Doors sit p50 96 u above the ground: the mouth static covers the gap.
- The pieces within 1,500 u: RockCaveEntrance with RockCliff, RockL/M and RockPileS/L, sometimes MountainTrim or
  MountainCliffSm. The mouth is **cut into a rise**, not raised on a mound. The two exceptions on flat ground
  are a ship and a Dwemer facade.

*Ours:* `generate.SHAPES` gives cave-mouth, burrow, grave-cut and root-mouth a 6 m 'mound', or a bank cut near
water. **Verdict: differs. Change (ground):** a mouth is set at the foot of a rise. If the ground does not rise
≥ ~550 u (8 m) within 1,024 u (15 m) on the mouth's back side, raise a one-sided hill behind it. Dress it with a
cave-mouth piece, 2–6 cliff shells and rock piles. No ring mound.
