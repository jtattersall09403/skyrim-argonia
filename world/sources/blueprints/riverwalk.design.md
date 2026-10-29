# Riverwalk — design (16k slice 3, type 3 water village)

The builder was the place-new lane, in walk 5, on 2026-09-29. The layout file `riverwalk.layout.json` is the source (0105 R59). Round folders are `tooling/.reports/16k/place.dunmer-north.riverwalk/round-N/`.

## Site

### The choice

Slice 3 was chosen by the contrast rule: type 3 (water village), region dunmer-north. The contrast was against Claywater (type 1, imperial-fringe). The contrast was also against Greenspring (type 2, hist-heartland). Riverwalk is the smallest water-village record with sockets. The record's `culture` is `argonian`. Its `sitingNote` says the culture raster reads hist-heartland there. The `sitingNote` places Riverwalk on the Argonian marsh side.

### The record (`world/sources/catalogue/places-dunmer-north.json`)

- **why:** Riverwalk is the mid-point of the northern trunk. It is strung along a channel because the
  channel is the street. The villagers earn their living from the ferry and the toll and by feeding boat crews.
  The captain of Alten Corimont and the field-owners of Thorn both claim the toll.
- **vibe:** one boardwalk with houses down both sides and "no land under any
  of them". The planks are silver, the water is black and the roofs are reed. The boardwalk is constantly re-planked.
- **services:** ferry, lodging, shrine, trader. **occupants:** D1 households,
  D2 crews overnighting, D2 toll hands. **notable slots:** toll-holder,
  stage-mistress. **sockets:** scene `the-long-walk`, evidence
  `the-plank-ages`, posts `toll-holder` and `stage-mistress`.
  **travelStation:** boat, canoe, ferry to seven dunmer-north places.
- Promise ledger: `world/sources/placement/promises/place.dunmer-north.riverwalk.json`, 15 rows.

### The ground (`world/sources/sites/dossiers/riverwalk.{json,md}`, workbench grids)

- A cove of `body.ocean` (level 0.0 m) holds water 0.4–0.9 m deep over flat mud
  (x 7170–7215, z 532–615). A dry spit lies to the north (x 7185–7220,
  z 496–530, 0 to +2 m). A dry islet lies to the south (x 7205–7245,
  z 618–640, 0 to +1 m). A cliff stands to the west. North of
  the islet the water is deeper than 1 m (x 7230–7245, z 595–610) and then a terraced drop falls to 3.8 m.
- The tracks from Riverwalk, Hissmir and Murkwater all end at (7186.1, 573.0),
  in the middle of the cove.

### Quest rows (`world/sources/quests/local-dunmer-north.json`)

LV38 Two Cities Claim the Halt is a skeleton quest row. LV39 Argued Nightly is a skeleton quest row. LV40 The Channel Silted Overnight is a skeleton quest row. `20-world-provisions.md` contains no provision that names Riverwalk.

### Lore read

- `world/sources/lore/alten-corimont.md`:54,70: Riverwalk lies east of Alten
  Corimont on the Stormhold, Tenmar Wall, Alten Corimont, Riverwalk, Thorn line.
- `world/sources/lore/topics/roads-and-routes-4e201.md`:33–34: the
  Stormhold–Thorn trunk is extrapolated with Riverwalk on it.
- UESP has no Lore article for Riverwalk (the name belongs to an Arena location and a novel).

## Brief

### The calls the ground and the kits force

1. **No Argonian dwelling that we hold may stand in the water.** The stilt shells
   (`composite:stilt/stilthouse-with-door`, HTBM `stilthouseplatform`) are
   ground-class. The plugins give no evidence of either shell standing in water (mounts miner:
   `anchorClassEvidence` policy for the composite, unplaced for the HTBM shell). BMV places
   `stilthouseext` twice and both placements are on ground. `submergedRule` fails the shells in the
   cove. On dry ground the stilt house fails `slopeRule` (9–11°) even on a pad.
2. **Only the KotM plank house is enterable for dunmer-north** (walk 11).
   `culture-kits.json` lists it as a visiting family (a timber stand-in for
   the Dagon Fel shacks, which have no load door). Every Seekhat thatch cell
   and every RootWhisper cell fails the interior acceptance gate on CC-only
   flora. The KotM pod is Claywater's shell. house3-with-door claims
   AltenDockmasterHouse and house1-with-door claims LilmothApothecaryHouse.
3. **The plank houses stand on posts.** King of the Murkmire raises them
   about 3 m over flood water on boardwalks. On the dry bank of the spit each house is
   seated by its door (reviewed sink 1.2 m, posts buried), so the door is
   walked into from the ground.
4. The long walk carries the tracks. It starts on the spit and passes through
   the end of the tracks.

### Rows (as built)

| Thing | Purpose | Kit piece (measured) | Rule or pointer |
|---|---|---|---|
| The long walk, 12 spans | the street; scene socket; the toll is called at its head | `vanilla:architecture/docks/dockstrent02` (docks-v1, 176 plugin placements, evidence snaps `pick 3`; deck 0.35 m over the water) | R67; docks-v1 is slope-exempt |
| The islet walk, 5 spans | joins the foot of the long walk to the islet | `dockstrsol01` (evidence snaps with `allow_terminal`); the first span is snapped square to span 11 by geometry | R67 |
| Ferry landing, 3 spans | islet shore to deep water | `dockstrent02`, deck lowered 0.16 m to 0.19 m over the water | R67, berthReachRule |
| Ferry raft | the ferry to seven stations | `ferryraft:snt/ferry/ferryraft01` in 1.3 m of water on a 1.6° bed | hullWater, slopeRule |
| Long house | the stilt house over the cove edge, reached by its own landing | `composite:stilt/swamp-house-with-landing` | landingRule |
| Crews' house | lodging and trader for the boat crews; its door looks out south-west to the cove, onto nine laid boards that run from the sill to the crews path, which starts off their outer edge | `composite:plank/thatchhouse06-with-door` on a pad at (7206.5, 505) yaw 0, cell SeekhatEldersHut (tier A); Kothringi plank boards bound as its `landing` | R52 fit rule; 97 C8 front to the water; doorFrontRule |
| Family house | the herb-gatherers' home on posts, its porch facing the cove to the south; eight laid boards cross the porch's front and a ninth runs out to the long walk's head. A short spur joins them to the hut path. The back yard to the north is the work yard | `composite:plank/house1-with-door` on its posts at (7209.4, 516) yaw 180, no pad, cell AltenGeneralStore (tier A); Kothringi plank boards bound as its `landing` | R52 fit rule; stiltRule; 97 C8; doorFrontRule |
| Stage shelter | the stage-mistress's post by the landing | `mudmother:gv_meshes/argoniannest/argoniantent02`, open front, no door | R18, R58 |
| Shrine | shrine service | two `argoniantotem01` beside the long house yard | — |
| Canoes | the crews' craft for Hissmir and Murkwater | two `canoe:actors/sfss/canoe/canoe1`, both afloat: one moored alongside the stage pier south of the raft, one off the islet's south shore | hullWater |
| Dressing | 38 single pieces sited with `wb.py site --free --clear 0.7` on flat padded ground, around the plank houses. The crews' work yard lies behind and east of the crews' house (rain barrel, stores, a seat, a wash line on its own small pad). The family yard lies around its door (a candle within 2 m, firewood, baskets, a seat). 20 and 21 pieces stand within 12 m of the two houses against the bar of 20. The spit is its own plan unit, `argonian-plank` (97 C1), beside the cove's mud-and-boards unit and the long house's stilt unit | Argonian urns, baskets, chairs, pots, nets, an oar | slopeRule, propSeatRule |
| Walk-9 dressing | the crews-house's trade at a market stall on the crews path, on its own small pad; the islet's catch drying on a fish rack north of the islet path, where the long walk lands, on its own small pad. The shrine parcel keeps its totems. The Sithis shrine is licensed indoors only (R1) | `rtmarketstall01`, `fishrack01` | `references/dressing.md` § 4 (water village row set); pads scanned, `tooling/.reports/16k/place.dunmer-north.riverwalk/walk9-dressing/` |

Lights: `argoniancandle01` stands at the long house door, 1.9 m from the threshold. A second `argoniancandle01` stands at the stage shelter. The raft carries two mined flames of its own. The fire module draws every flame from the kit's mined `flames[]`. The candle preset supplies the candles. No flame is placed by hand. The cell has four plugin lights that light the long house interior. Their radii are hearth 4.6 m, 3.5 m, 3.6 m and 0.7 m.

The place is built under no breadth column, with 2 counted buildings. The 0098 and breadth gates report 'below every column'.

## Record corrections (REQUEST rows in `tooling/.reports/16k/place.dunmer-north.riverwalk/requests.jsonl`)

- `vibe.silhouette` claims a kilometre of boardwalk with houses on both sides
  and no land under them. The built boards are about 125 m long. A single house
  stands on the spit. The record is to be rewritten to what is built.

## Lessons this slice (candidate rows, REQUEST)

- Water village: read the shell's manifest `anchorClass` and
  `anchorClassEvidence` before choosing it. A `ground` shell in water fails
  `submergedRule`. A policy or unplaced class is a mining job that is filed before
  design.
- A dwelling shell needs a cell that passes the fit rule
  (`blueprint_interiors --claim`) before it is sited. Run the claim on a
  one-parcel skeleton first. The HTBM bamboo huts have no such cell.
- Yard sets on sloped ground: members at pad edges fail `slopeRule`. A
  `remove` of a member leaves its yard socket behind (walkRule then fails on
  a missing host). Site single pieces with `wb.py site --free --clear 0.7`.
- A route that carries a track in over water must be a `track` with at most
  20 m of it wet. The rest of the way over water is the walkable run parcels,
  with footpaths only on dry ground.
