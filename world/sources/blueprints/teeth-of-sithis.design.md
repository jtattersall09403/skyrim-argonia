# The Teeth of Sithis (`place.mercantile-coast.teeth-of-sithis`): design

The Teeth of Sithis is Type 6, a shrine. Its family is `sithis`, its type `sithis-temple`, its variant tended. Its scale is M1. It is in mercantile-coast. It is Argonian. It was built in walk 11, wave 3, parts A to C. Its layout is `teeth-of-sithis.layout.json`.

## Site

- Record: `world/sources/catalogue/places-mercantile-coast.json` (id above); site packet
  `tooling/.reports/16k/place.mercantile-coast.teeth-of-sithis/site-packet.json`; promise ledger
  `world/sources/placement/promises/place.mercantile-coast.teeth-of-sithis.json` (25 rows).
- Why: this is the largest Sithis temple in Murkmire. The Clutch of Nisswo keep it and scrub it to the
  waterline and no further. Its first purpose is lost and one faction says that it has found the purpose out
  (`why.*`). The temple was built to frame a natural rock formation at the end of a pilgrim water.
- Vibe: a colonnade of black stone teeth rises out of standing water. The stone is wet and black, a white
  scrub line marks each tooth and the water is brown. The work is exact and unexplained.
  The colonnade is seen only from the last bend of the pilgrim water.
- Contents: a named priest (Nisswo of the Teeth) and a band of the Clutch (`faction.nisswo`);
  "the one who scrubs to the waterline"; a D3 guardian in the deep rooms; tier-4 offerings.
- Sockets: `scene.teeth.colonnade-rite`, `evidence.teeth.scrub-line-rule`,
  `post.teeth.pilgrim-landing`, `marks.teeth.rite-witnessed`; interior anchor sockets boss,
  boss-chest, escape, shrine.
- Interior: `kind` dungeon, family `hist-sanctum`, S3, 2 entrances, loop `second-entrance`,
  `verticalRelationship` below, swim 14 m, climb 8 m.
- Quest: NI05 "Teeth of Sithis" (`world/sources/quests/quests-factions.json`, `quest.ni.ni05`;
  `docs/quests/25-quest-place-map.md`:92, :109, :158).
- Ground (`world/sources/sites/dossiers/teeth-of-sithis.md`): centre 4.8 m, slope 9.7 deg facing
  215 deg; shore 31 m (ocean, level 0); 5.8 m over the water table; buildable 7.76 ha of the
  400 m disc; relief p5 -40 m to p95 5 m (the formation drops to the sea on the south-west).
- Seams (site packet `routeSeams`): the footpath `track.track.mercantile-coast.nisswo-line` ends here
  (from Lilmoth, 0.35 km N). It is the pilgrim way, so the place stands on its own way and the way ends at the
  temple. The boat route lilmoth-archon passes 144 m N. Neighbours within 200 m: High Junction 91 m, Cold Light
  105 m, Lights-From-Under 151 m, Bramman's Screen 170 m, Fourth Stage 182 m.
- Lore: `world/sources/lore/topics/sithis-nisswo-shadowscales.md` (record source);
  `world/sources/lore/extrapolation/quest-plan-deltas.md`:141 ("the Teeth of Sithis is a real
  place"). King of the Murkmire ships its own Teeth of Sithis dungeon (cells TeethofSithisInt01,
  Int02, Int03), which is the plugin source for the interiors of this place.
- Must not repeat: the Tag House (bamboo hut and half pavilion, the-dead) and the Wamasu Shrine
  (open offering shelf). The Emptying House (`place.naga-kur-deeps.sithis-temple-mass-sacrifice`,
  1.7 km) is the other Sithis temple and is unbuilt.

## Intent

- A pilgrim comes down the track from Lilmoth through scrub and sees nothing until the
  last bend. Then six black teeth stand in a row in brown water, with a white band scrubbed on each to
  the waterline and never below. The work is exact and unexplained. A keeper tends the place with care.
  The reason for that care is not stated anywhere.
- The Clutch are few and quiet. A priest stands at the water's edge, a scrubber works at the stone and a band waits on
  the east scaffold. Their work is the place. The place has no market, no smoke and no shelter for guests.
- The temple itself lies under the bank. The two scaffolds are the scrubbing frames of the Clutch and each
  stands over a door down into the drowned rooms (KotM's own Teeth of Sithis cells).

## Walk-through

1. Approach (north, the footpath `nisswo-line`): the track runs south down a 9.7 deg slope. The
   bank hides the teeth until about 30 m out.
2. Reveal (z ~6760): the way opens between the two scaffolds. The colonnade fills the view and the gap
   between teeth 3 and 4 lies dead ahead.
3. Arrival (z ~6776): the track runs out at the water. Candles on dug-in stands mark the last dry
   ground. The priest stands here (post socket) and the scrubber works the waterline to the west.
4. The rite water: the visitor wades knee-deep to the gap between the middle teeth (scene socket).
5. Going in: the load door of either scaffold leads down into the temple (Int01 west, Int02 east). The
   second entrance makes the loop of the dungeon.
- Approach answers (97 §5): the place is seen from the last bend only (record vibe). Wayfinding follows the single
  track and the landmark is the colonnade. Nothing is signposted, because the place is a shrine at the end of its own way.

## Quest beats

| Quest id | Tier | Beat | Need | Decision | Evidence |
|---|---|---|---|---|---|
| quest.ni.ni05 | medium (faction tier 2) | Arrive and meet the Clutch's priest | NPC spot at the end of the way | build | `socket.teeth-of-sithis.npc-nisswo`, `q-post-pilgrim-landing` |
| quest.ni.ni05 | medium | Witness the rite in the water between the teeth | open water framed by two teeth | build | `q-scene-colonnade-rite`, `q-mark-rite-witnessed` |
| quest.ni.ni05 | medium | Read the scrub line, which the splinter sect would break | a tooth with its waterline band, reachable | build | `q-evidence-scrub-line-rule` on `t-tooth3` |
| quest.ni.ni05 | medium | Face the splinter sect with the band of the Clutch | the band's spot by the east door | build | `socket.teeth-of-sithis.npc-band` |
| quest.ni.ni05 | medium | Reckoning in the deep rooms (guardian, boss chest, escape) | the dungeon's rooms | build | the two load doors to Int01/Int02 (tier A claims); room anchors are Phase 12 dungeon population |

All six sockets are in the quest row's `sockets[]`. The quest row is in `world/sources/quests/quests-factions.json`.

## Brief

| Thing | Purpose | Kit piece | Rule or lore pointer |
|---|---|---|---|
| Six teeth (`t-tooth1..6`), wet | the colonnade, the signature; gap 3-4 frames the way's end | `kotm:argonia/xanmeer/exterior/obelisk` (6.9 m) | record vibe; R86 wet by design |
| West scaffold + load door | Clutch's scrubbing frame; door to Int01 | `kotm:argonia/stockades/stockadescaffoldbase1sided01` | plugin link (R83) |
| East scaffold + load door | second entrance; door to Int02, the band's post | same shell | interior loop `second-entrance` |
| Four dug-in candles | light the last dry ground and the two doors | `mudmother:.../argoniancandle01` | lights.density; lit entrances |
| The street + two spurs | the pilgrim way to the water, branches to each door | path | seams: ends the footpath |
| Stone stair | not built: the way ends at the water on the bank's own slope, which the design uses, so no stair is needed | - | owner no-gap rule (R113): redesigned, not a gap |

## Interiors

| Door | Shell | Tier | Why |
|---|---|---|---|
| door .1 (west scaffold) | stockade scaffold | A, TeethofSithisInt01 | KotM's own door to its Teeth of Sithis cell (free-standing load door, `doorOffsetInShell`) |
| door .2 (east scaffold) | stockade scaffold | A, TeethofSithisInt02 | the second KotM door; homes for priest, scrubber and band are its beds |

Cells export without their water pieces (`water-surface`). Water in interiors is Phase 12 work. Decision 0102 gives the later-phase reason. These two cells exist nowhere else in the pool.

## Doors (the plugin's evidence)

Evidence: `tooling/.reports/16k/place.mercantile-coast.teeth-of-sithis/feasibility-doors.md`.

- Doors. The only shells in `world/sources/placement/exterior-interior-links.json` that load into a
  Sithis or xanmeer dungeon with two doors are KotM's own Teeth doors: shell
  `kotm:argonia/stockades/stockadescaffoldbase1sided01` (a 3.7 m scaffold beside the door), door
  model `kotm:architecture/xanmeer/furniture/xanmeer_murkmire_door2load`, two rows: TeethofSithisInt01
  (236 x 153 x 77 m) and TeethofSithisInt02 (182 x 156 x 107 m). Placing the shell twice claims
  Int01 then Int02. The scaffold beside the door fits the record, because it is the scrubbing scaffold of the Clutch.
- Blocker. Neither cell passes the fit rule (`bundle_sourcing`). Int01 lacks 878 architecture
  references and Int02 lacks 1239 (KotM `architecture/xanmeer/interior/*`, `argonia/xanmeer/interior/*`,
  the door2load itself). No published kit carries any KotM xanmeer piece, interior or exterior.
  The stockade shell is in the config of `interior-kotm-v1` but in no published kit. With no passing
  cell, `blueprint_interiors --claim` reserves the door and exits 3 (0114 rule 4, R83). A
  reserved dungeon door has no legal path in 16k (0103 decision 7 keeps dungeon interiors for
  Phase 12, but `interiors.reserved` and `--claim` give no tier B/C pass).
- Exterior pieces. Published: HTBM xanmeer pyramids and walls, pillar02 (9.3 m) and pillar05
  (3.1 m) in `ruin-monumental-v1`. KotM's black xanmeer exterior set (`argonia/xanmeer/exterior/*`
  pyramid, obelisk, towers, stairs01-04, wallpiece01-05; `architecture/xanmeer/exterior/*`) is in
  the vault only (`king-of-the-murkmire-190459/extracted/meshes`) and in no kit config.
- Kit the place needs: a KotM xanmeer kit lane, interior and exterior together (they share the
  door2load and the room pieces). The interior part is a batch pre-pass by rule
  (`references/builder-practice.md`, "a builder never builds one"), so it belongs to the planner.

## Record defects (step 0 item 5; REQUEST rows in `tooling/.reports/16k/place.mercantile-coast.teeth-of-sithis/requests.jsonl`)

1. `world/sources/catalogue/interior-recipes.json` `hist-sanctum` and `xanmeer-complex` name kit
   `xanmeer-interior-v1`, which is the Creation Club Ayleid set (`ayleidcc:sarthesarai`) and not a
   xanmeer grammar. The KotM xanmeer kit is to be named once it exists.
2. The record's `assetPlan` carries `cc-ayleid-interior` (Creation Club content; owner walk 2
   "no CC/DLC"). It is to be replaced with the KotM xanmeer kit slug.
