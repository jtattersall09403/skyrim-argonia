# What we hold, what the province now uses, and what is genuinely missing

Current truth as of 2026-11-24, after track A (use what we hold), the sourcing of extras and the conversion of the 2011 packs were done. Measured
facts only; each "missing" row lists the searches and looks behind it. The cost of each gap is put in what the
player sees. Generators and costs are another document's business ([PROPOSAL.md](PROPOSAL.md)).

## 0. The method

For every thing, in this order, and "not held" only with the searches and looks listed beside it:

1. Name it every way: lore word, plain word, real thing, what a modder would call the file (a grave-stake is
   "roadsign"; a weir is "fence", "fishnet", "trap"; a sap tap is "spigot").
2. Search what we hold: `python -m tools.places search query "<words>" --look` scores the catalogue
   (`out/places/catalogue/bases.jsonl`, 47,673 rows: every plugin we hold, vanilla, DLC and Creation Club included,
   and our own statics for model-only packs) by its text and by a picture of each model.
3. Search what we built: drafted places' plans and refs, place records, source places. A thing may exist only as an
   arrangement of pieces: record the recipe.
4. Look at every candidate: `search sheet "<words>"` draws the top 48 in one picture. A name is never enough
   either way; a magenta or black render is "could not look", never "not held".
5. Check use: our tables (planting, dressing kinds, gear and clothing, stock, travel boats) and placed refs.
6. Only then Nexus, in both Skyrim games, by name, description and the big resource authors; check permissions.
7. One verdict: used, held and idle, compose, get, adapt, make, or could not look.

## 1. What the province now uses, by kind

| Kind | Before | Now | Where it lives |
|---|---|---|---|
| Reeds and cattails | 1 model per region (`bm-v-001reed`) | 5 per region in all 18 regions (BM&V reed kept as the main one, Baan Malur Cattails1-4, Tropical Skyrim CattailGrass01) | `newworld/sources/flora/` (extra_bases.json, families.json) |
| Lilies | 5 per region, one model at 93% | 8 per region in 15 regions (HTBM Lilly1/2/5/6 white and yellow blooms, resource-pack lily clusters) | same |
| Giant fungus | 4 per region in 3 regions | 8 per region (Update.esm ThinMushroomTree01-06, clusters 02/03) | same |
| Cypress knees | 2 per region in 7 regions | 4 per region | same |
| Saltrice | none | grown in the four regions the lore gives paddies (Nushara Bayou, Althii Archipelago, Lake Ulaish, Arnesian Jungle near Thorn), each citing its line | same, `habitats.json` |
| World dressing kinds | 26 | 29: grave-stakes (HTBM GraveStake3) in Valley of Storms and Tulmek Washes; hackwing nests (KotM egg nest) on Skeith Isle; landing totems (00GV totem) in Murkwood | `newworld/sources/dressing/kinds.json` |
| Native boats at boat stops | none (the raft-master had no model) | 22 raft-master stops carry KotM's reed-covered river boats; 7 ferry and cargo stops the 25 m reed-roofed barge (ALPABoat04, placed nowhere before) | `newworld/sources/travel/network.json`, read by `draft/io.stop_boats` |
| Swap table for Argonian places | none | 17 easy swaps (tents, lamp post, braziers, plank and farm doors, the Talos shrine to Dibella), each keeping function, seeded into a new place's `draft.replace` | `newworld/sources/dressing/swaps.json`, place-plan |
| Source places contradicting the lore | 13 undrafted places on Dwemer, Daedric, snowy Nordic or Nordic-stone sources | 8 re-pinned to held sources of their own kind (Lilmothiit Ra'tal Den on Haj-Uxith's domes; Ovezza on Frossel; Imperial ruins on the sunken fort and KotM's old Imperial ruin; Kothringi ruins on Teeth of Sithis and Root Whisper); 5 kept on their matched source, whose note already builds them from held pieces of the right people; every shared source's note says how its place differs | `newworld/sources/source_match/`, the research notes |
| Interiors per house | one interior per source door, repeated | a further door into the same interior takes an unused interior of the same source of like size (new places only) | `tools/places/draft/interiors.py` |
| Bog-iron (T1-T2) weapons | 11 vanilla iron and steel models | 32 marsh and mod models at T2, none vanilla; marsh pieces drawn before Skyrim's at equal rank (KotM's dark-iron Argonian set moved to bog-iron) | `newworld/sources/stock/item_material.json` |
| Tribe gear: gold, pearl, rust | pearl had no wearable; gold and rust fell to saxhleel and hide | pearl and gold wear the saxhleel light harness beside the Naga Shellback shell (heavy, the only shell held); rust the Bone Cultist bone plate beside hide | `kits.json` overlays |
| Town guard cuirass | BMArgBody, no model on the ground | Argonian Scale Armor (altscalearmor) | `scale.json` guard_issue |
| Clothing | 0 of 23 trade kits had a clothing row; 19 clothing items known | 23 of 23 kits and the Dunmer, Imperial, Khajiit and Bosmer overlays; 55 clothing items filed by race fit read from their ARMA records (Argonian pieces first, Telvanni robes for Dunmer, vanilla farm, fine and monk clothes only as the fallback); every non-guard person derives one worn outfit | `item_material.json`, `kits.json`, `tools/places/stock/derive.py`, `fit.py` |
| Hammock | a static with no bed | `ArgoniaHammockBed`, a copy of Baan Malur's hammock furniture (its sleep markers) | `tools/places/own_bases.py`, blocks.md |
| Mossy, silted, algae-grown ruins and rocks | none of ours | four material records (moss as KotM, silt, algae, and a rock moss from Moss Shaders Restored's values) and 102 twins: 20 held ruin pieces in three states, 14 most-planted rocks mossed; built and read back | `own_bases.py`, blocks.md |
| Resource packs without records | not usable | 989 statics of ours (ships, banners, Hlaalu, Velothi, GKB trees, harvestables, the stilt house, war tails, AmA, HistBone, the Ayleid kit) | `newworld/sources/own/pack_statics.json` |

Drafted places keep what they have: nothing above redrafts or re-stocks them. A drafted place takes any of it only
through a narrow change by its own agent.

The moss material's file: the 23 material records that name `Meshes\ShaderTests\ShaderBox.nif` (16 Skyrim.esm,
1 Dawnguard, 5 Dragonborn, 3 KotM) point at the Creation Kit's preview mesh, which ships in no archive of the game
or of any mod; the game draws the material from the record's own colour and falloff values
([ruins-and-weathering](ruins-and-weathering.md)).

## 2. What was sourced

Every pack below is fetched by `infra/gpu-box/stack.py` into the private cache, staged asset-only (its plugins never
active), and searchable by text and look. Packs made for the 2011 game are converted on this machine by
`infra/gpu-box/nifconv` (nifly's own SE optimiser: NiTriShape to BSTriShape, stream 83 to 100, skinning kept), proven
on a skinned tail with a read-back render. A pack that ships models without records gets statics of ours
(`newworld/sources/own/pack_statics.json`, 989 in all).

| Pack (Nexus) | Terms | What it gives Black Marsh |
|---|---|---|
| Tropical Lands Assets (SE 33446) | "use any and all" | kapok trees with buttress roots, palms, a bamboo table and platform, a clipper, green-cave pieces (its bamboo is not placed) |
| Waterplants (SE 6092) | credit | 26 lily clumps in five colours |
| Simple Straw Hats (SE 89962) | credit | 16 straw hats |
| Ships and Boats of Tamriel (SE 41653) | credit, not for profit | 56 statics: Breton, Imperial and Redguard boats, a city ferry, galleons, wrecks, anchors |
| Incaendo's Banner Resource (SE 17604) | modders' resource | 59 banners, for the emblems of track B |
| Morrowind Hlaalu Architecture (SE 157997) | credit | 113 statics: Hlaalu houses, towers, docks, walls |
| Phitt's Velothi Resources (SE 107571) | credit | 17 statics: Velothi towers, walls, bridge, houses |
| GKB Green Trees (2011, 19268) | credit, never renamed | 503 statics: jungle, palm and cypress trees; 14 of the 48 looked at fit Black Marsh (cypress 1-5, date, fan and beach palms) |
| Harvestables (2011, 15108) | free to use | 28 statics: marshmerrow, saltrice, sugarcane, hackle-lo, stoneflower, trama root |
| Stroti's Stilt House (2011, 61824) | free mods only | a raised stilt house and its door |
| Argonian War Tails (2011, 28502) | credit | five tail armour variants |
| AmA Argonian Mercenary Armor (2011, 27676) | none stated: reconfirm with the author before any distribution | Argonian mercenary armour with a tail |
| HistBone and Bonewood Argonian Armors (2011, 99144) | none stated: reconfirm before any distribution | an Argonian hood and bone armour (worn pieces; heavy) |
| Ayleid Ruins Building Kit (2011, 90667) | none stated: reconfirm before any distribution | 189 statics of Ayleid ruin |
| Moss Shaders Restored (SE 55279) | none stated: reconfirm before any distribution | its rock moss values, used for our 14-rock moss twin family |
| Shaders of Solstheim (SE 60144) | none stated: reconfirm before any distribution | ash on basalt: nothing used (no basalt in Black Marsh) |
| Not taken: Saxhleel Sundries (SE 191593) | its author says its sets are taken from another game (ESO) | for the owner: assets lifted from another game are not taken on any footing |

The own records are built by the place layer's writer and read back from the written plugin: the hammock bed equals
Baan Malur's furniture in every subrecord but its editor id; four material records resolve (KotM's moss found by
editor id); 102 weathered twins carry their material and angle; 989 pack statics carry their model paths.

## 3. Held shells against the interior gaps

[interiors-by-kind](interiors-by-kind.md) counted, of 144 places with building interiors, 13 with no fitting domestic
shell (oxblood 7 Kothringi towns, pearl 5 Seafalls, gold 1 Archon harbour), the root-hollow homes of 19 forest-green
places, and no shell for the Hist room (4 rooms), the Argonian cellar (1), the Kothringi greathouse (1) and the
Kothringi and Lilmothiit ruins (17 places). Searched by text and look since (`search query`, `search sheet` for
"kothringi great house", "hist root hall room", "root hollow tree interior", "cellar room earthen", "stilt house";
sheets looked at):

- **Kothringi greathouse and Kothringi towns: held.** HTBM Curse of Cipactli's `CIPHTBMVillKothGreatHouse` with its
  interior `CIPHTBMVillKothGreatHouseInt` (a round thatched greathouse on posts) and KothHut1-3 with interiors. They
  fit the greathouse and the 7 oxblood towns; no cell or place uses them yet.
- **Hist room: compose.** KotM's root-hall kit (`HistRootHall2way`, `3way`, `4way`, `Ramp01`, `Endcap`, `Turn`,
  `Shift01/02`, `HistHallEntrance01`): grown-root halls with mossy floors that snap together. The 4 Hist rooms compose
  from it.
- **Argonian cellar: adapt.** The vanilla farmhouse basement kit (earth and timber, no Nordic sign).
- **Pearl's cliff-and-surf village: held in part.** Stroti's stilt house and the KotM blackwood stilt shells.
- **Lilmothiit ruins (9): held.** Haj-Uxith's mud domes and burrow interior serve as the turf-and-leaf dens (five
  places use it).
- **Root-hollow homes (19 places): not held.** The root halls are tunnels, not homes; no held kit grows a room from roots.

## 4. What is genuinely missing, ranked by what its absence costs the player

| # | Thing | Searched and looked | Where needed, how many | Cost to the player |
|---|---|---|---|---|
| 1 | Root-grown buildings and root-hollow homes (hut, family house, hall, granary, tree-minder's house) | "root grown hut", "living tree house", "root hollow interior", "tree dwelling", across all 54,000 catalogue rows and every pack above: Hist trunks, root pieces and tunnels, no building; Nexus: nothing | the 19 forest-green (Root-Folk) places, Helstrom's 110 people, the Hist rooms' surroundings | The interior culture's whole look: every Root-Folk settlement stands in borrowed reed or mud huts |
| 2 | Dugout, canoe, punt, reed raft | 0 matches for canoe, dugout, raft, kayak, coracle, pirogue, punt, outrigger in every model file and catalogue row, the new packs included; Ships and Boats of Tamriel holds hulls, not canoes; Nexus: Sailboats SSE (40057) holds a canoe but states no terms and bundles another author's resources | 22 raft-master stops; the travel operator promises "a poled raft or a paddled canoe"; rafts named in 216 place notes | Small craft are the marsh's ordinary transport; plank boats stand in at every stop |
| 3 | A modular Argonian room kit (floor, wall, corner, ceiling) | interiors-by-kind section 3; no pack adds one | every Argonian interior of 72 stilt and reed culture places plus the derived homes (about 500) | Every Argonian house is one of 13 whole shells; rooms repeat |
| 4 | Light shell and light bone-plate armour | "bone armour", "shell armour", "turtle shell breastplate", "crab shell armor", "bone breastplate ribs": statics, enchanted pieces, or the heavy Shellback and Bone Cultist only; HistBone's bone armour is heavy too. Bethesda never makes a light and a heavy cuirass of one model (2 shared light/heavy limb groups in 3,675 vanilla ARMO records, no cuirass), so none is minted | tribes gold, pearl, rust (3 of 18 cultures) | Gold and pearl wear the saxhleel light harness beside their heavy shell; their shell harness reads as plain leather |
| 5 | Argonian clothing beyond KotM's few pieces | clothing sheets; 55 items filed, the Argonian ones KotM's robes, hoods and hats and the Naga loincloth; AmA and HistBone are armour | every Argonian commoner of the 252 undrafted places | Commoners wear something native or neutral, from a few designs |
| 6 | Whip, claw, rapier, halberd in a Black Marsh make | name and look ("long polearm blade", "clawed gauntlet weapon"); Nexus: Heavy Armory (6308) and Glaive Danger (89156) are mods, not resources, terms unstated | the signature weapons of six tribes | Those tribes carry generic Animated Armoury models |
| 7 | Toll bar, milestone | "toll", "milestone", "barrier", "waystone": stockade barriers and posts held | Company and Imperial roads | Small: a composed barrier or post stands in |
| 8 | Gourd, reed mat | "gourd", "calabash", "reed mat", "sleeping mat": none (Gourd HD on Nexus is a texture only) | households | Small: jars and bedrolls stand in |

## 5. The six drafted places: what the newly used things call for

Each row is what the place's record or kind calls for and its files lack, for the place's own agent to apply
narrowly; the tables above reach a drafted place only that way.

| Place | Thing | Base | Where | Why |
|---|---|---|---|---|
| helstrom | native boats at the raft-master stop | KotM `ALPABoat02`, `ALPABoat03` (barge `ALPABoat04` if a ferry) | the hub's landing (today ShipRowBoat01, ShipRowBoatAnim01, 01boatracked) | its travel stop; `io.stop_boats` |
| helstrom | door swap | `Skyrim.esm:0453D8` SHouseDoor02 to `CIPHTBMVillageHutDoorLoad` | 15 refs | swaps.json |
| helstrom | sap spigot and sap jar | `dunSleepingTreeCampSpigot` / `Skyrim.esm:0AED90` | the city Hist's pool | promises p014, p021 (sap seller), p032 (tree-minders' hall) |
| helstrom | guard cuirass | argonian-scale issue (altscalearmor) | 14 guards wear BMArgBody, which has no model | scale.json guard_issue |
| helstrom | clothing | the kits' clothing rows | 80 of 110 people wear nothing authored | kits.json |
| jal-veesa | sap spigot and jar | as above | the sick Hist's pool | p02, p03, p04 (tree-minder Weeltul) |
| jal-veesa | clothing | kits' rows | 19 of 22 people | kits.json |
| outpost-m11-m63 | clothing | kits' rows | Heeta-daro, Dee-kai, Nur-daro | kits.json |
| outpost-m13-m65 | hammock bed | `ArgoniaHammockBed` | the gang-master's hut ("beside his hammock") | p06 |
| outpost-m13-m65 | clothing | kits' rows | all 15 people | kits.json |
| outpost-m6-m66 | sap spigot and jar | as above | the Hist's pool | p01, p02, p13 (the minder sells sap) |
| outpost-m6-m66 | clothing | kits' rows | Tsa-tah, Paa-shei, Heem-Jasa | kits.json |
| tribal-camp-m2-m68 | clothing | kits' rows | 6 of 8 people | kits.json |

No drafted place's record names a burial ground, so none owes grave-stakes; only Helstrom is a boat stop.

## 6. The lightest in-game check for each kind (owner's list)

- Plants (once the plant stage has run): stand in a reed marsh: several reed and cattail shapes, lilies in more than one colour; Lake Ulaish's paddies hold rice.
- Dressing kinds: one grave-stake cluster in the Valley of Storms, one hackwing nest on Skeith Isle, one totem on a Murkwood shore.
- Boats: arrive at one raft-master stop (a river boat) and one ferry stop (the reed-roofed barge).
- Clothing: talk to a commoner in the next stocked place: an outfit, not BM&V's default.
- Guard: a town watch guard's cuirass shows on him and on the ground when dropped.
- Hammock: activate a placed hammock: the player lies in the net.
- Weathered pieces: the clean, moss, silt and algae Ayleid arch side by side, and a moss-twin rock, from above by day.
- Converted meshes: one GKB cypress and one war tail on an Argonian: no missing-mesh marker, the tail moves with the body.
- Pack statics: one Hlaalu house and one Breton boat placed in a Dunmer or Imperial place.
