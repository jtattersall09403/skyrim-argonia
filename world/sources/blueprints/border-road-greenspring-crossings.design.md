# The Border road crossings below Greenspring: design

The place is `place.route.border-road-greenspring-crossings`. It is type 10, a road structure or crossing, built in 16k walk 9. Its record is its row in `world/sources/routes/route-structure-exemplars.json`. Its layout is `border-road-greenspring-crossings.layout.json`.

## Site

- **Way:** `route.road.stormhold-thorn` (trunk, condition `worn`, registry
  note "long timber bridges patched"), chainage 3940 to 4815 m. The stretch runs from the
  Greenspring track head (4801, 1785) west to the river marsh (4444, 1516).
- **Water** (dossier `world/sources/sites/dossiers/border-road-greenspring-crossings.json`):
  `crossing.major.009` (span band, 36.3 m, 1.32 m deep) and
  `crossing.major.012` (26.4 m, up to 1.07 m deep; the owner's 2026-09-16
  "short boardwalk" at the inlet mouth). The painted road stops at both
  marsh reaches and on the bank top (z 1638 to 1695).
- **Stair:** the place builds `structure.road-stormhold-thorn.12` (rise 7.6 m)
  (0115 item 4: `builtBy`; the parcel `bank-stair` claims it by
  `routeStructureId`). The bank is a 7.85 m face over 2 m of ground
  (z 1628.6 to 1630.5). The lip stands at 7.8 m.
- **Neighbours:** Greenspring (built) lies up its track. No other place's ground
  lies on the stretch. The ferry crossing of the exemplar set belongs to Claywater
  (built).
- **Lore:** the route registry row; the junction pins
  `junction.pin.stormhold-thorn.river-crossing` and `.inlet-mouth` (owner
  steers 2026-09-16); `docs/research/placement-settlements/road-dressing.md`
  and the mine `world/sources/placement/vanilla-roadside-dressing.json`.

## Brief

| Thing | Purpose | Kit piece | Rule or pointer |
|---|---|---|---|
| River crossing | carries the road over 1.3 m of marsh to the stair foot | 9 x `vanilla:architecture/docks/dockstrent02` (docks-v1), pick 3 | modular-runs 23; `crossing.major.009` |
| Inlet deck | carries the road over the inlet mouth | 8 x `dockstrent02` (docks-v1), pick 3 | `crossing.major.012`, owner 2026-09-16 |
| Stair | climbs the river bank | 3 x `kotm:argonia/mudhuts/stairs02` (settlement-mud-v1), mined run pair, top tread on the lip, foot sunk in the marsh 0.36 m past the plank end | modular-runs 29b; walkwayRule |
| Track-head marks (maintained band) | shows where the Greenspring track leaves the road | `cairns/rockcairn02` shell, `rockm02`, `rockl01`, `rockm01`, `rocks02` (route-dressing-v1) | road-dressing.md rule 3 (a step better near a place) |
| Bank road (worn band) | rocks at both bends, a cold fire ring on the only flat ground of the bank road (above the inlet; no cell at the bends is under 1.8 deg across the ring's 4.8 m), a cairn at the inlet deck's west head | `campfire01landoff` shell, `rockm04`, `rockl04`, `rockm03`, `rockpiles01-03`, `rocks01-03`, `cairns/rockcairn03` | mine: bends 3.5x, campfires 47% at bends, cairns singletons |
| River-crossing head (worn, far end) | marks the planks for a walker from Stormhold; a grave mound on the flat beside it | `cairns/rockcairn01` shell, `burialcairn03`, `wetrocks/rockm02wet` x2, `rockpiles01`, `rocks03` | mine: rocks 4.9 m median off the edge |
| Footpaths | a trodden stub from the road to the mark of each band | 3 footpaths, 1.5 m | pathReachRule |
| Signposts | none: no junction of three or more roads on the stretch | - | road-dressing.md rule 4 |
| Walls | none: hist-heartland roads carry no walls | - | road-dressing.md rule 1 |
| Lights | none: the road is unlit between places | - | 97 C16 applies to places with doors |

The record's `structures[]` is promised. The place builds the bridge, deck and stair. The lip-step is pending with the Two-Gate Bridge. Claywater builds the ferry crossing. The record's `why` is carried by the blueprint `causalModel`. The record's `culture` is the district.

## Creative register

1. The dressing reads the road's condition as a gradient. Kept marks stand near
   Greenspring, rubble and a cold fire ring stand in the middle and wet rocks mark the
   far crossing head.
2. A grave mound stands by the road at the head of the river crossing. A traveller died on this stretch.
3. The crossings are bare plank runs with no rails or lamps. The people of Greenspring
   keep them in repair.

## Lessons this slice

- A missing kit piece is a kit job (build-and-publish row).
- A route place's `culture` is a kit culture (build-and-publish row).
- Crossings are laid with `boardwalk --pick 3` (runs-and-built-ways row).
- A climb's top tread is measured onto the lip and its flight stands in
  front of the bank face. The plank run is moved to end short of its foot
  (runs-and-built-ways row, audit10 c6).
