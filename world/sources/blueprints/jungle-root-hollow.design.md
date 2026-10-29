# Takes-The-Tools (`place.saxhleel-coast.jungle-root-hollow`): design

The place is type 5, a dungeon entrance. Its type sheet is `references/types/05-dungeon-entrance.md`, which this slice wrote. The build is 16k walk 9, slice 4 of the loop. It is the first type-5 place.

## Why this place (the type-5 pick)

The 16k brief (§ From 16i item 1) asks for a dungeon-kind record. The entrance piece of the record must exist in a kit. The record needs complete promises and a contrasting region. The brief prefers a root cavern. The lane brief prefers a tier A interior. A tier A interior lets the entrance link to a real cell (0109, 0114).

The pick was measured over the 61 active lair records. These records have `classification.class` lair.

| Record | Region | Interior family | Entrance | Quest refs | Linked shell with a cell we can build |
|---|---|---|---|---|---|
| **Takes-The-Tools** (`saxhleel-coast.jungle-root-hollow`) | saxhleel-coast (unbuilt) | root-cavern S2, 1 entrance | sinkhole-lip | SX08 | `rockcaveentrance02` -> `MugsumpHollowInt01` (King of the Murkmire's 32 x 57 m root cave, bones, a behemoth's den): the record's "bone scatter", "something breathing" and "root-walled rock" are what the cell holds |
| Under-Root (`mercantile-coast.root-gallery-murkmire`) | mercantile-coast | root-cavern S2, 4 entrances | hollow-trunk | LM30, 3 sockets | none fits: "200 m of passage, three entrances, hearth-scars at three heights" matches no linked cell that we hold |
| The Hollow Under the Figs (`imperial-fringe...`) | imperial-fringe (Claywater's region) | root-cavern S2 | hollow-trunk | LF34, LF41 | fails the contrast rule (same region as slice 1) |

Takes-The-Tools wins the pick. Its linked cell can keep the record true, which the other two records cannot. It lies in a region that no slice has built. Its record has the fewest sockets. This build fills the sockets from the cell and the mouth.

## § Site

The record is `world/sources/catalogue/places-saxhleel-coast.json`. The record is a lair of class root-system, type root-hollow-gallery, variant inhabited, magnitude M1. Danger is D4, hostility is hostile, the place is clearable and respawn is slow. `discovery` is none and `effortToReach` is 4. The why: a dry void under the root layer has root walls and one defensible mouth. The record says rock-floored, but the site audit finds no rock in the ground, so the floor is not stated as rock. An occupant has taken the void over and drags its kills there. The record said that a nearby village keeps its hunters clear of the valley. The change set names the hiring camp as the source of the warning, because there is no village nearby. The vibe: a cave mouth in a bank, collared with Hist root, with bones outside it. The colours are black, bone white and root brown. The bone scatter outside holds three generations of other people's tools. The mood is unwelcoming. The smell carries before the mouth shows. Something breathes in a hollow space. Contents c1 is `creature.wamasu`, D4, an apex ambusher, deep. Contents c2 is `creature.hoarvor`, D2, scavengers at the threshold, ticks in the bone scatter. Contents l1 is a unique item, deep. Contents l2 is a hidden cache. The interior is a delve of family root-cavern, size band S2, with a single entrance. The interior is dry and dark (0.8), with lock hard. The interior rooms are collapse, gallery and cache. The anchor socket is `cache` (hidden). The record names no sockets and no occupants, because it is a beast's lair. The quest is SX08 Takes The Tools (skeleton, PREDATOR). The hiring camp is Sells-Their-Hours, `saxhleel-coast.owing-hiring-camp`. The hiring camp cannot forage because a creature in a root hollow has been taking foragers.

The ground dossier is `world/sources/sites/dossiers/jungle-root-hollow.md`. The centre lies at 3682, 4554 m at 38.3 m, with slope 0.7 deg. The setting is tropical jungle on firm upland soil, danger band 4. Canopy closure is 0.98 and plant density is 375 plants/ha. The plants are bracken, esloe bush, tropical plant and fern. The site lies 3.0 m above the local water table. The swamp body `body.2047-2456` lies 70 m off, at level 39.71 m. A headwater channel lies 262 m W. The floor is hummocky, +-1.5 m over 50 m (workbench samples), with no rock. Concealment is 0.85. The archon-gideon road is 888 m away. Archon is 1.48 km away.

The site is off the road. No route, track or terminal reaches the site (`routeSeams` empty). The way in leads through the jungle from the east. The hiring camp lies 895 m away at bearing 79 deg. No internal way is built. A lair has no path. A path would also need a terminal. No terminal exists here.

The neighbours within 500 m come from the site packet. The Interrupted Flight lies 209 m NE (fallen flier). The Horwalli Cut lies 225 m W (ruin). The Licensed Stage lies 257 m WNW (sap-tapping camp). The Bled Tree lies 309 m NNE. The Warren lies 338 m SE (another root gallery). Root-Sakka lies 340 m SSW (abandoned root gallery). The Quiet Camp lies 429 m N. None of the neighbours is built. This place must not repeat the signature of The Warren, which is unbuilt. This place sets the root-mouth signature first.

Lore, one line each. `world/sources/lore/topics/fauna-hazards.md:14` says that the wamasu is a lightning-powered swamp beast. Wamasu bones are black and hold a charge. `world/sources/lore/topics/fauna-hazards.md:28` says that the Argonian behemoth (Xal-Krona) is made by the Hist. The plugin places the behemoth as the occupant of this cell. `world/sources/lore/topics/hist-and-sap.md` says that Hist roots run under the ground of the whole province. A root gallery is a void under the roots. `world/sources/lore/topics/fauna-hazards.md:46` says that hoarvor are ticks that live on what a predator leaves.

No place is built within 2 km. Claywater, Greenspring and Riverwalk are in other regions.

Record defects were found at step 0 and fixed in the step 5b change set. The premise of SX08 says that the camp "cannot forage east". The camp lies 895 m east of the lair (bearing 79 deg), so the lair is WEST of the camp. The premise reads "west" after the change set. The `entrance` of the record was `sinkhole-lip`. The built mouth is a cave mouth in a rock bank at ground level (`cave-mouth`). The 5b change set changed the record to match the built mouth. The same set adds the tool scatter to `sockets.evidence`. The same set names the hiring camp of the quest in `why.pressures` and `wouldChangeIf`. The same set drops "D4" from `why.founding`.

## § Brief

| Thing | Purpose | Kit piece (measured) | Rule or lore |
|---|---|---|---|
| The mouth and its bank (`b-mouth`, parcel `parcel.jungle-root-hollow.the-cave-mouth`) | the single entrance of the lair: a 30 x 32 x 19.5 m mossy rock mound with the tunnel in its east face; the mound is the record's bank | `vanilla:landscape/rocks/rockcaveentrance02` (settlement-root-v1), seated so its lip meets the ground (reviewed `assetPlacement` row, designed sink -0.02 m: pivot 0.02 m under the lip); its AutoLoadDoor01 on the tunnel axis | 0114 (linked shell), R83; L25, L26; mined with `worldgen.link_neighbourhood` |
| The collar (`r-vines`) | the Hist root that the record says collars the mouth | `kotm:argonia/trees/hist trees/hist_vines01` (settlement-root-v1), assembly member at the right-hand side of the mouth, outside the rock (the plugin's own offset buries it in this rock on level ground) | vibe.silhouette; KotM refs round the door |
| Bone scatter (`s1-lb-*`, yard set `lair-bone-scatter`) | what the occupant dragged out and left | the bones that `MugsumpHollowInt01` itself scatters (humanribcage, humanarmleft, humanlegleft, humanspine, bloodyribs, bloodybone) and its Argonian skull (`kotm:issgard/clutter/bones/issgard_boneargonianskullfull`), all settlement-root-v1 | vibe.signatureFeature |
| Tools in the scatter (`s1-lt-*`, yard set `lair-tool-scatter`) | other people's tools | `vanilla:clutter/common/shovel01`, `vanilla:clutter/basket01`, `shores:shoresofskyrim/fishnet01` (settlement-root-v1) | vibe.signatureFeature; item classes `tool`, `fishing-gear` |
| Warding at the mouth (`l-candle-n`, `l-candle-s`, `d-totem`, `d-chime`; audit10 C5) | the searchers from the hiring camp mark the den. Two candle stands flank the way in (1.85 m from the threshold, each a flame at night). A totem stands 9 m out on the approach. A bone chime hangs on the Hist vine and anything coming out rings it | `mudmother:gv_meshes/argoniannest/argoniancandle01` (settlement-mud-v1, lit, mined light and flame), `argoniantotem01` (plugin sink n 3), `argonianbonechime01` hung by `mount --hang` (unmined, reader-approved r29) | material-culture.md:30 (totems), :300 (chimes at every threshold); no made light goes inside. The den is lit by fungus, sap and the sky (§ Interior light) |
| Forager's basket (`d-basket`) | a second dropped basket in the tool scatter | `mudmother:gv_meshes/argoniannest/basketsmall01` | vibe.materials "dragged belongings" |
| Ways | none (off the road, no terminal) | — | step 0.3b |

Type 5 has no breadth-bars object yet. The type sheet records it. The place is a single shell, so the 0098 within-place variety bar does not apply. Planned dressing kinds are rock 3, bones 7 and tools 5.

### § Interiors

| Door | Building | Shell | Tier | Cell (expected) | Why |
|---|---|---|---|---|---|
| `door.saxhleel-coast.jungle-root-hollow.1` | the mouth | `vanilla:landscape/rocks/rockcaveentrance02` | A | `MugsumpHollowInt01` (King of the Murkmire) | This is the cell that the AutoLoadDoor01 of King of the Murkmire inside this rock loads. The slice re-mined the links: the miner had given the door to the Hist vines 5.85 m off because rocks were never shells and a rock whose box holds an invisible load door now counts as a shell. The cell is a root cave with a beast in it. Shell-choice checklist: (a) doored; (b) linked; (c) the cell is a lair (bones, a behemoth, a single chest) and serves the parcel; (d) not held anywhere in the province |

The 162 references of the cell were added to interior-kotm-v1. The references are cave walls, pillars, vine floors, stalactites, Hist roots, plants and bones. The place also lays the bones live in settlement-root-v1. Each bone exists once. 21 references ship as listed gaps (R51, `kit-interiors/substitutions/MugsumpHollowInt01.json`), each with its search. Four gaps are Creation Club hanging root clusters. Four gaps are resource-pack cliff boulders. Thirteen gaps are undergrowth clumps whose leaf texture exists only in the resource pack. None of the gaps is architecture. The root clusters sit in the clutter folder of their kit.

#### § Interior light

A beast lives here, so the den has no lantern or fire. Its light comes from glow fungus, Hist sap blooms and daylight through the roof (place skill § Intent; `worldgen.lair_light_lint` checks it).

| Light | Purpose | Kit piece | Rule or record |
|---|---|---|---|
| Glow fungus (28: clusters on the floor and the roof roots, singles up the tunnel) | the way in is visible; the den floor lies in pools of cold blue light, with the bones in the middle left dark | `vanilla:plants/glowingmushroomcluster01`, `glowingmushroomsingle01` (interior-kotm-v1) | Skyrim lights them with FalmerBlueLightSuperSaturate01NS (159 of 700 cluster refs, `mine_kit_lights`); seated by `wb.py seat-interior`; the den spots were chosen where the night light plan read dark |
| Hist sap blooms (3) | red sap light beside the cell's own Hist roots, south-east and at the back | `kotm:argonia/trees/hist trees/histflower01`, `histflower02` | the bloom glows by its own shader; its light is the nearest steady Skyrim hue (`mine_kit_lights --emissive-fallback`); hist-and-sap.md (the roots run under the province) |
| Daylight through the roof (4 holes) | by day, green-gold sun shafts fall into the den in patches, as if through leaves | the cell's own roof gaps, under the plugin's four DefaultSunlight01Omni lights | `interior_light.py` shell holes with leaf mullions (interiorWindows.json); the runtime's canopy tint |

Measured: the night light plan reads 29.8% of the walked floor dark (bar 30%), median E 0.167 (dark below 0.12).

### § Containers and items

- The rustic chest of the cell (container socket from the cell) is the
  record's hidden cache l2.
- The three tools at the mouth carry `item` sockets (classes `tool` and `fishing-gear`, value
  low). They are the foragers' belongings, for the evidence of SX08.
- l1 (the unique item, deep) is an `item` socket in the cell.

### § Creative register (three calls unlike Claywater, Greenspring, Riverwalk)

1. The searchers keep two candles at the door of the beast's den as a warning.
   Inside, the den is lit by fungus, sap and the sky (§ Interior light).
2. The signature is the threshold scatter: bones and tools lie in a single fan
   in front of the mouth, thickest at the door and thinning outwards.
3. The bank is rock, the rarest material in the province, set against living
   root. The mouth reads from 30 m as a dark gap between rock and root.

### § Sockets

| Socket | Kind | Host | Data | Why |
|---|---|---|---|---|
| `socket.jungle-root-hollow.ticks` | fauna | ground at the scatter | D2, zone threshold, `creature.hoarvor` | contents c2 |
| `socket.jungle-root-hollow.occupant` | encounter | cell `MugsumpHollowInt01`, the den (host: its rib cage, ref 08570749, 44 m in) | D4, zone deep, `creature.wamasu` | contents c1 |
| `socket.jungle-root-hollow.unique-item` | item | cell, deep (host: hist_root04, ref 08570742, the far end) | class misc-household, value high | contents l1 |
| `socket.jungle-root-hollow.tool-*` (3) | item | the spade, the basket, the net | class tool or fishing-gear, value low | vibe; SX08 evidence |

### § Quests

The quest is SX08 Takes The Tools (PREDATOR, tier 3, skeleton). Foragers from the hiring camp do not come back. Their trail ends at the hollow. Their tools lie at the mouth. The creature that took them is inside, to be killed or driven off. The provisions are the mouth (door to the cell), the tool scatter (evidence, item sockets) and the occupant (encounter socket). All three provisions are built here.

### § Seams

The site is off the road and has no internal way. The approach is on foot through the jungle from the east, from the hiring camp. The place has no road sign. The totem of the camp on the approach is the sole marker.

### § Approach (openworld-approach §5, the answers that matter)

A walker sees the place first from 30-40 m through the trees (concealment 0.85). The rock bank and the root mass come into view. The mouth is the dark gap between them, facing east toward the hiring camp. The place has no path. At night the two warding candles show the mouth from the trees.

## § Lessons this slice

The lessons are recorded in the place-build skill.

- The links record gave the door of the cave to the vines beside it, because rocks were
  never shells. A rock whose box holds an invisible load door is now the
  shell and `link_neighbourhood` lists what the plugin set round a door.
- The AutoLoadDoor01 of a cave cell is its load door and never a missing piece.
- The door of a cave mouth stands on the axis that the door yaws in its plugins give. Its
  sill is judged where the way in meets the ground and its lip is seated on
  the ground (designed sink = the measured sill).
- Lit density applies where people live. A cave mouth is not a building
  and needs no entrance light. An off-network lair is walked from its
  approach.
- Miner merges from two lanes lost a row, so merges now hold the lock of the record.
- A piece in two kits resolves to the first kit by name, so each piece keeps a single home.
