# Walk 5, lane R: relief character, the land past the map, held ground, clearance from the water plane

Measured 2026-11-11 on terrain build 20261109T204317Z (before) and trial build 20261111T023933Z from this lane's code.

## Why a wider scope once moved every hill (and no longer does)
Every noise lattice, the drainage routing's jitter, the rain's droplets, the rounding pattern and each pad's outline
were laid from the grid's corner. Widening the scope moved the corner, so the whole province was laid afresh: old
against new land heights correlated 0.36 and four places failed their terrain need (Tsonac's pad rose 9 m). All of
them are now anchored to the base window (terrain_relief.anchor: the scope without the cells past the picture).
Old against new land heights correlate 0.91 (what differs is the landforms, the clearance and the ruler band);
terrain_needs: 6 failures (blackrose-prison, fort-chalkmoth, mine-28-m65, vicrium pads; seafalls rise; blackrose
island), all among the old build's 12; the five shore-access failures and outpost-7-m69's pad now pass.

## Region relief character (tools/newworld/terrain_character.py)
Thirteen features per region: four of amount (median height, height span, slope p90, roughness at 100 m) and nine of
shape (flat share, step, landform scale, fine and broad roughness ratios, grain, line, skew and tail width by
quantiles), each divided by a fixed pooled spread; distance is Euclidean. Ground held for a built place is left out.
Moment skew and kurtosis read the mounds of a handful of places (four flat regions sat on the clip at 3.0), so both
are by quantiles. Tested on synthetic ground: two landforms of one amplitude lie further apart than one landform at
1.5 times the amplitude.
- Skyrim (Tamriel, seven sample boxes): nearest distances 1.04 to 3.60; its eleven pairs of neighbouring sample
  regions lie 2.10 to 3.93 apart, mean 3.16 (pale-snowfield and eastmarch-springs the closest).
- Ours before: mean nearest 2.47; neighbouring regions 1.71 at the closest, mean 3.99.
- Ours after: mean nearest 2.70; neighbouring regions 2.19 at the closest
  (Skyrim 2.10), mean 4.23 (Skyrim 3.16). Nearest per region, before > after:
  althii 2.17>2.19, aphon 3.31>3.39, arnesian 2.72>2.72, aunike 2.73>2.83, banujha 2.04>2.07, barsaebica 1.95>2.06, blackwood 2.35>4.01, cape-percar 1.95>2.32, chixathe 2.29>2.82, hatandros 1.98>2.30, kotherra 1.77>2.07, lake-ulaish 3.89>3.98, murkwood 2.74>2.92, nha-enasa 3.79>2.92, nushara 2.87>2.30, okuwun 1.98>2.09, skeith 3.17>3.94, tulmek 1.71>2.19, ultherus 1.71>2.06, valley-of-storms 2.29>2.75.
  Eighteen regions lie as far or further from their most alike; two lie nearer: nha-enasa (to murkwood: the root
  hummocks bring murkwood's fine roughness ratio to nha-enasa's) and nushara-bayou (to hatandros-bight: its ridges
  roughen what was the calmest ground of the province, slope p90 1.8 to 3.1 degrees). Both stay above Skyrim's
  closest neighbouring pair.
- What a landform does to the measure: a share (`base`) of the shared relief under 1 draws flat regions together;
  a form on a region whose mark was its calm (lake-ulaish, nushara-bayou, the two rock isles) draws it toward the
  others. The two isles take no form (as-laid); the lake's strandlines are faint (0.3 m).
- Hjaalmarch's marsh has 0.40 m of relief at 20 m; murkwood's root hummocks are 0.7 to 1.8 m high for that reason.

## The land past the map (tools/newworld/terrain_beyond.py, tiles.BEYOND_CELLS = 8)
The picture's ruler band and frame strip are 88 px deep. The map's last true pixels are carried outward, blurred by
1 + 0.35 px per px of distance. Map cells x -50..56, y -129..-40 (Skyrim cells x -100..113, y -258..-79), 107 x 90
map cells, 38,520 Skyrim cells (was 26,936); the grid is 6849 x 5761 samples. The cells past the picture are margin
(no places, no navmesh, the pan box unchanged); regions.py gives each its nearest region (weather and flora rows
continue across the edge), and their land is foreign land in the terrain build.

## Clearance from the water plane (tools/newworld/terrain_clearance.py)
Skyrim (height against each cell's own water): points within 32 units of the plane 0.0137, within 64 0.0253, the
same at LOD4 to LOD32 spacings. Ours before: 0.049 / 0.108 at full resolution, 0.072 / 0.132 at LOD32. Ours after
(land 1.1 m clear by 6 m inland, beds 1.1 m deep by 4 m out): 0.0155 / 0.0351 full, 0.0152-0.0164 / 0.0352-0.0360
at LOD4 to LOD32. Helstrom's held zone: 865,322 samples, every land sample the old build's plus 72 units, no water
sample higher, waterline unmoved.

## Memory
The build's peak resident set was 12.4 GB (the relief's whole-grid float64 temporaries, then the weathering's
working fields held to its end). The relief is worked 256 rows at a time in float32 and the weathering frees each
field after its last reader: peak 5.6 GB (/usr/bin/time -v: 5,612,644 kB), written into build.json (peak_rss_mb).
The character measure works a region's window at a time: 0.6 GB.
