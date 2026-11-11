# Walk 5, lane R: relief character, the land past the map, held ground, clearance from the water plane

Measured 2026-11-10/11 on terrain build 20261109T204317Z (before) and a trial build from this lane's code
(20261111T003111Z, in the lane's worktree).

## Region relief character (tools/newworld/terrain_character.py)
Eleven features per region (height p50 and span, slope p50/p90, flat share, band roughness at 20/100/500 m, landform
scale, slope grain, skew), each divided by a fixed pooled spread (Skyrim's sample regions and ours before); distance
is Euclidean. Ground held for a built place is left out.
- Skyrim (Tamriel, seven sample boxes): mean distance 2.56; nearest-neighbour distances 0.84 to 3.42, mean about 1.55.
  Hjaalmarch's marsh has 0.40 m of relief at 20 m and 1.8 m at 100 m; our marshes had 0.04 to 0.11 and 0.17 to 0.83:
  Bethesda's marsh is pools and hummocks, ours was a flat sheet.
- Ours before: mean distance 3.34, mean nearest 1.50, mean between neighbouring regions 3.02; the low regions
  (nha-enasa, nushara, banujha, ultherus, okuwun) within 0.95 to 1.14 of each other.
- Ours after: mean distance 3.52, mean nearest 1.61, mean between neighbours 3.42. Nearest per region, before > after:
  althii 1.32>1.48, aphon 2.22>2.45, arnesian 1.65>1.81, aunike 2.04>1.81, banujha 0.96>1.07, barsaebica 1.42>1.18,
  blackwood 1.90>2.50, cape-percar 1.58>1.51, chixathe 1.42>2.30, hatandros 1.25>0.92, kotherra 1.50>1.42,
  lake-ulaish 1.95>1.68, murkwood 1.11>2.03, nha-enasa 0.95>1.56, nushara 0.95>1.10, okuwun 1.14>0.92,
  skeith 2.53>2.69, tulmek 1.36>1.46, ultherus 0.96>1.07, valley-of-storms 1.72>1.18.
  Thirteen regions moved apart, seven closer: the global statistics read landform type (rings, ridges, ravines,
  mounds) weakly; the hillshade crops show the types plainly.

## The land past the map (tools/newworld/terrain_beyond.py, tiles.BEYOND_CELLS = 8)
The picture's ruler band and frame strip are 88 px deep (water share by column steps at 75 to 80 px). The map's last
true pixels are carried outward, blurred by 1 + 0.35 px per px of distance. World cells: map cells x -50..56,
y -129..-40 (Skyrim cells x -100..113, y -258..-79), 107 x 90 map cells, 38,520 Skyrim cells (was 26,936).

## Clearance from the water plane (tools/newworld/terrain_clearance.py)
Skyrim (height against each cell's own water): points within 32 units of the plane 0.0137, within 64 0.0253, the
same at LOD4 to LOD32 spacings. By distance from the waterline, within 32 units: 2-8 m inland 0.16 to 0.34, 8-20 m
0.014 to 0.027, 20-50 m 0.000 to 0.001; 2-8 m out 0.08 to 0.23, 8-20 m 0.002 to 0.008.
Ours before: 0.049 / 0.108 at full resolution, 0.072 / 0.132 at LOD32 (8-20 m inland 0.070, 20-50 m 0.008 within 32).
Ours after (land 1.1 m clear by 6 m inland, beds 1.1 m deep by 4 m out): 0.0146 / 0.0334 full, 0.0143-0.0151 /
0.0334-0.0345 at LOD4 to LOD32. Helstrom's held zone is lifted 72 units (1.03 m) as one constant.
