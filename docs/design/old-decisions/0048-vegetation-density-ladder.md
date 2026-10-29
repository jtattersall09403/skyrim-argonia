<!-- imported unchanged from elder-souls-argonia docs/decisions/0048-vegetation-density-ladder.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0048 — The between-region vegetation ladder, and the gates that hold it

**Status** accepted · **Extends** [0036](0036-phase10-placement-decisions.md) ·
**Evidence** the measurements, rejected candidates and rounds are
[archived](../research/archive/vegetation-0048-rounds/0048-as-recorded.md)

Each region's palette was authored on its own ecological terms, never against
its neighbours, so the between-region comparison had nowhere to live and
drifted until the lowlands read as uniform. This record makes the comparison
a typed table and gates it.

## The measure

**Stems per hectare** counts T1-tier instances whose role is not rock or cliff
dressing: giants, emergents, canopy, gallery, waterline and drowned trees,
basin mangrove, the rootland's tree-scale fungi. It excludes understory,
lianas, epiphytes, aquatics and boulders. It is measured **per region pixel**:
each instance is attributed to the region class of the raster cell it stands
in and divided by that class's own area, never by a chunk's dominant class,
which counts a neighbour's forest inside a lake.

## The ladder (tropical jungle = 1.00)

The jungle's density is held fixed (the owner's constraint) and everything is
graded around it.

| class | region | ratio | grounding |
|---|---|---|---|
| 13 | tropical jungle | **1.00** | terra firme; "rainforest leading inland" (`lore/regions/murkmire.md:13`) |
| 14 | mangrove forest | 1.40 | higher stem count, lower roof; the "nigh-impenetrable" wall near Lilmoth (`murkmire.md:23`) |
| 6 | rootland deep marsh | 0.76 | fewer, far bigger buttressed trunks (`middle-argonia.md:11,19`) |
| 7 | interior swamp | 0.67 | flooded forest; flood depth sets the gradient (`middle-argonia.md:85`) |
| 5 | deep river corridor | 0.60 | riparian gallery, abrupt outer edge, nothing midchannel (`waters.md:27,31`) |
| 2 | upland hills | 0.60 | "more temperate grasslands" (`thornmarsh-and-east.md:11`) |
| 11 | firm lowland | 0.55 | the largest lowland class; clearly below the jungle (`blackwood-and-gloommire.md:10-16`) |
| 3 | tidal delta | 0.45 | landward band over mudflat and salt pan (`waters.md:27,31`) |
| 8 | fringe marsh | 0.40 | the ecotone between swampy south and grassland north |
| 4 | coastal lagoon & salt marsh | 0.35 | trees patchy on saline flats (`waters.md:24`) |
| 1 | border mountains | 0.15 | the treeline altitude gates stay |
| 9 | seasonal floodplain | 0.12 | "fields of ferns and flowered grasses" (`fauna-hazards.md:99`) |
| 12 | lake & standing water | 0.02 | open water; drowned snags only |

Class 10 (raised hammock) is retired ([0050](0050-retire-the-raised-hammock-region-class.md)).

## How it is applied

One scalar per region on the stem layers only (`build_palettes.rebase_stems`):
`multiplier = target_ratio × delivered(13) / delivered(region)`, from the
measured attenuation of authored to delivered (`MEASURED_ATTENUATION`).
Understory, aquatics, groundcover, boulders and epiphytes keep their authored
values, and every spatial parameter (patchiness, glade response, the 90 m
glade and 190 m stand wavelengths, clump size) is untouched, so a region that
halves gets half as many clumps of the same size. Delivery is close to linear
in the authored count; the gate's ±0.15 tolerance (±0.35 for the thin classes
3, 4 and 5) absorbs the rest, and a miss is fixed by re-fitting the
attenuation and re-running the generator.

**A shipped asset is not a stem.** The canopy is wide-crown composites, each
standing for about five botanical stems at the jungle roof; the browser, not
botany, is the limit. Canopy closure is not gated, because crown diameter is
not a field `palettes.json` carries (backlog row: vegetation crown
diameters).

## Understory and the ground ring

- **Every region class carries at least two understory species that no class
  it borders carries**, assigned in one place
  (`build_palettes.EXCLUSIVE_UNDERSTORY`). Adjacency is measured
  (`vegetation_ladder.region_adjacency()`: 250 or more shared 4-neighbour
  edges on the shipped raster), never a hand table.
- **Groundcover has a region axis**: `groundcover.json`
  `byRegionClass[region].swaps[cover]` replaces the base list for one cover in
  one region. LTEX.GNAM's three-grass cap is per painted texture, so the swap
  layer fits the shipped-game rule. `regionCovers` records which covers each
  region paints, measured from `ground-control.png` against
  `hydro-regions.png`; a swap for an unpainted cover is dead data and fails.
  The runtime decodes `hydro-regions.png` by the legend
  `hydrology-meta.json` ships, read, never duplicated.
- **The ground-ring kit** is chosen on measured geometry and texture, never
  labels: Skyrim-climate families (juniper, heather, spruce, tundra, volcanic
  ash, snow grass, holarctic bog plants) are wrong-province; a mesh whose
  texture is absent from its pool is left out, never shipped untextured. The
  budget is 2,400 triangles and 3.3 m per mesh, with baked cards for the far
  tier so geometry is paid only near the camera; nothing in the ring is solid
  (`collision: none`).

## The gates

`worldgen/test_vegetation_ladder.py`, in `npm run test:placement`, each
mutation-tested red on its own defect:

1. **Authored ladder**: ratios and ordering on the authored palettes through
   the measured attenuation.
2. **Delivered ladder**: decodes the shipped `chunk_*_vegetation.bin` and
   checks the same table. If it goes red after a palette change, the fix is
   the authoring loop, not the target.
3. **Breadth**: understory species per region, no species over 60 % of a
   region's understory, exclusive understory per border, a real ground layer
   (six species per region, floored at three per painted cover), no ground
   mesh on three land covers, the ring's triangle and size budget read off the
   **built** manifest, nothing solid, and every palette species present in
   the kit that renders it.

`report_flora_variety.py` shows the aquatics in its variety view.
