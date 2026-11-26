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

## Held ground at the waterline (tools/newworld/terrain_held.py; build 20261111T094531Z)
A uniform lift of a held zone's land stood whole on the first land sample from the water and its beds were deepened:
inside Helstrom's zone and blend the waterline triangles steeper than the navmesh walks (45 degrees) went from 5.3%
to 38.8% (median slope 20.6 to 43.2 degrees). The rule: beds are the held build's exactly; land is the held build's
plus a lift that is 0 at the old waterline and whole 24.9 m from it (a smoothstep on LAND's 8-unit step; the shortest
ramp whose rise from one sample to the next stays under one step, so no triangle gains more than 5.05 degrees;
islets and spits narrower than about 50 m never take the whole 72 units). Helstrom's zone (865,322 samples): water
difference 0, land difference from old + ramp 0, waterline moved 0, waterline triangles over 45 degrees 1.81% in
the held build and 1.81% now (median 20.6 degrees in both), the most any land triangle steepened 5.05 degrees.
Points within 32 / 64 units of the plane: outside held zones 0.0182 / 0.0403 at full resolution, 0.0183 / 0.0409
at LOD8, 0.0189 / 0.0412 at LOD16, 0.0186 / 0.0418 at LOD32 (the check's 0.03 / 0.05 is judged there, one
threshold for the province; Hjaalmarch itself reads 0.178 / 0.320 at LOD8 spacing: a marsh lies near the plane and
Bethesda leaves it so); inside held zones 0.060 / 0.128 (0.068 / 0.135 at LOD32: a built place's banks stay as
built); over all 0.0198 / 0.0437.

## The banks beside the water (tools/newworld/terrain_clearance.py BANK, place_banks; terrain_needs.py)
Skyrim.esm, land height over its own water by distance from the waterline (terrain_ref/tamriel_h.npy), and the share
of waterline triangles steeper than the navmesh walks (45 degrees):
- Hjaalmarch's marsh: 0.9% over 45 degrees; the rise across a shore edge 8 / 24 / 48 units (p10 / median / p90);
  p90 height 48 units at 1 m, 98 at 3 m, 160 at 5 m, 224 at 7 m, 328 at 10 m, 480 at 14 m, 696 at 20 m.
- Lake Ilinalta: 8.2%; rise 8 / 40 / 88; p90 height 88 at 1 m, 202 at 3 m, 321 at 5 m, 400 at 7 m, 1104 at 10 m.
- The north coast: 2.7%; rise 8 / 32 / 72; p90 height 64 at 1 m, 144 at 3 m, 232 at 5 m, 336 at 7 m, 560 at 10 m,
  992 at 14 m, 1880 at 20 m.
- Rivers: the White River 13.4% (rise 16 / 36 / 120), the Karth 20.8%, the Rift 8.6%: steeper than ours, so ours are
  left.
Ours were far steeper than Hjaalmarch where people, creatures and the player walk in and out of still water (the
relief reached over a 7 m shore ramp where high ground met the water, and pads and rises were laid level to the
water's edge). The rule:
1. The land beside still water (green-marsh, blackwater-swamp, pond), lakes and the sea (ocean, bay, shallow-coast)
   rises no faster than the p90 profile above for its kind (terrain_shape.compose; again after the places are
   shaped, for ground a skirt raised past a place's need). Past the profile's last point the bound runs on at its
   last grade and soon stands over any relief.
2. Ground a place shaped (its needs' discs plus 20 m: pads, rises, islet mounds) is not level to the water's edge at
   such water. The bank is the bank: within the bank band, BANK_BAND_M = two samples = 3.66 m from the waterline
   (every corner of a waterline triangle lies within it), the ground rises from the shore height at 0.6 (31
   degrees) at most; behind the band the place's ground is as shaped. Ground standing more than 2.2 m over the
   water at its waterfront ends in a scarp behind its strand. A road's bed is the road solver's.
3. terrain_needs judges each need on the ground it is about, with the same BANK_BAND_M (imported): a flat pad's
   slope p90 on its land behind the band, the band read as the level of the ground behind it; a rise's top behind
   the band against the land round it; a pad or a top with under a quarter (MIN_BEHIND) of its land behind the band
   fails as "no room behind the bank"; a shore-access on the band's row at the waterline (its gentlest sample no
   steeper than 15 degrees: the band's crest reads the lip of the ground behind it, which is no landing). The build
   judges every landing on the finished ground by that test and cuts again, 1 in 8 into the pad, any that a pad
   laid after it buried (a rise keeps its body, a road its bed).
Why the band and not the whole of a need's disc: easing the whole disc to 31 degrees was measured on build
20261111T053723Z. Half of the eased samples lie more than 3.7 m from the water and 27% more than 7.3 m (pads and
rises stand up to tens of metres over the water at their waterfront), so judged behind a band of 3.7, 5.5, 7.3 or
9.2 m the needs showed 17, 20, 20 and 21 failures (tydeos's pad at 23 to 30 degrees, southwatch-keep, aphon-belvedere
and estate-15-m110 near 30). The shore measure reads only the first two samples from the water, so the band alone
gives the same shares.
Build 20261111T094531Z, waterline triangles over 45 degrees outside held zones, before (build 20261111T081946Z) >
now, against Skyrim's and the check's threshold (terrain_clearance.MAX_OVER_WALK):
| water kind | before | now | Skyrim | threshold |
|---|---|---|---|---|
| green-marsh | 9.2% | 0.30% | 0.9% (Hjaalmarch) | 2% |
| blackwater-swamp | 3.5% | 0.33% | 0.9% | 2% |
| pond | 7.3% | 0.61% | 0.9% | 2% |
| lake | 9.1% | 1.13% | 8.2% (Ilinalta) | 9% |
| ocean | 13.2% | 2.20% | 2.7% (north coast) | 5.5% |
| bay | 20% | 1.76% | 2.7% | 5.5% |
| shallow-coast | | 1.71% | 2.7% | 5.5% |
| river | 5.0% | 4.95% | 13.4% (White River) | 13.4% |
| stream | 6.1% | 6.08% | 13.4% | 13.4% |
| estuary | | 7.63% | 13.4% | 13.4% |
Rise across a shore edge now (p10 / median / p90 units): green-marsh 24 / 32 / 56, blackwater-swamp 24 / 40 / 56,
pond 24 / 40 / 64 (Hjaalmarch 8 / 24 / 48); lake 32 / 48 / 64 (Ilinalta 8 / 40 / 88); ocean 32 / 48 / 72 (north
coast 8 / 32 / 72). 38,567 land samples were lowered by the step after the places, 14,060 of them in places' bands;
no waterline sample changed side against build 20261111T053723Z (0 of 39.5 million).
terrain_needs: 6 failures of 368, the six known (blackrose-prison 13.4, fort-chalkmoth 14.1, mine-28-m65 25.9 and
vicrium 28.2 degrees; seafalls's rise: the place stands on water, there is no land at its top; blackrose's island
joined to the mainland). No pad or top lacks room behind the bank. Two faults of the trial that eased a pad's first
3.7 m by the smooth distance while the test read a two-sample strip by sample steps:
- tydeos's pad read 10.0 degrees: its pad stands about 10 m over the water and the central-difference slope of its
  first row behind the bank read the bank. It is not the tilted pad of the old build's list; behind the band it
  reads 9.1 degrees, as before the banks.
- fort-shellmoth's shore-access read 15.8 degrees: its pad, laid after its landing, buried it; the pad stands 2.1
  to 2.6 m over the water along the whole waterfront, so the bank there is 31 degrees from the water to the pad
  (23.9 degrees at its gentlest on the waterline row; the 8.9 a whole-band reading gives is the pad's lip). It is
  the one place of 97 whose waterline row has no gentle bank. Its landing is cut again into the pad (637 samples
  lowered, by 2.2 m at most): shore-access 8.0 degrees, pad 7.3 degrees (3.6 before the cut). The largest of the 97
  shore-access readings is 9.6 degrees.
Roads: 0 of 86,822 points over grade. Entrances: 49, 0 bad. Peak memory 5.65 GB (/usr/bin/time: 5,652,068 kB).
