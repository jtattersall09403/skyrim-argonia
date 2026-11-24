# What we hold, what the province now uses, and what is genuinely missing

Current truth as of 2026-11-24, after track A (use what we hold) and the sourcing of extras were done. Measured
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
| Source places contradicting the lore | 13 undrafted places on Dwemer, Daedric, snowy Nordic or Nordic-stone sources | re-pinned to held sources of their own kind (Lilmothiit on Haj-Uxith's mud domes; Velothi on Redeyn, Frossel, Bossarena Koemia; Imperial ruins on the sunken fort and KotM's old Imperial ruin; Kothringi on Teeth of Sithis and Root Whisper) | `newworld/sources/source_match/` |
| Interiors per house | one interior per source door, repeated | a further door into the same interior takes an unused interior of the same source of like size (new places only) | `tools/places/draft/interiors.py` |
| Bog-iron (T1-T2) weapons | 11 vanilla iron and steel models | 32 marsh and mod models at T2, none vanilla; marsh pieces drawn before Skyrim's at equal rank (KotM's dark-iron Argonian set moved to bog-iron) | `newworld/sources/stock/item_material.json` |
| Tribe gear: gold, pearl, rust | pearl had no wearable; gold and rust fell to saxhleel and hide | pearl wears the Naga Shellback shell (heavy, the only shell held), rust the Bone Cultist bone plate; gold, who never wear heavy armour, keep the saxhleel harness | `kits.json` overlays |
| Town guard cuirass | BMArgBody, no model on the ground | Argonian Scale Armor (altscalearmor) | `scale.json` guard_issue |
| Clothing | 0 of 23 trade kits had a clothing row; 19 clothing items known | 23 of 23 kits and the Dunmer, Imperial, Khajiit and Bosmer overlays; 55 clothing items filed by race fit read from their ARMA records (Argonian pieces first, Telvanni robes for Dunmer, vanilla farm, fine and monk clothes only as the fallback); every non-guard person derives one worn outfit | `item_material.json`, `kits.json`, `tools/places/stock/derive.py`, `fit.py` |
| Hammock | a static with no bed | `ArgoniaHammockBed`, a copy of Baan Malur's hammock furniture (its sleep markers) | `tools/places/own_bases.py`, blocks.md |
| Mossy, silted, algae-grown ruins | none of ours | three material records (moss as KotM, silt pale grey-brown, algae green) and a twin of each for 20 held ruin pieces (Ayleid, old Imperial, Xanmeer rubble): 60 statics | `own_bases.py`, blocks.md |
| Model-only resource packs | not usable | 245 statics of ours: 56 ships, ferries and wrecks; 59 banners; 113 Hlaalu pieces; 17 Velothi pieces | `newworld/sources/own/pack_statics.json` |

Drafted places keep what they have: nothing above redrafts or re-stocks them. A drafted place takes any of it only
through a narrow change by its own agent.

The moss material's file: the 23 material records that name `Meshes\ShaderTests\ShaderBox.nif` (16 Skyrim.esm,
1 Dawnguard, 5 Dragonborn, 3 KotM) point at the Creation Kit's preview mesh, which ships in no archive of the game
or of any mod; the game draws the material from the record's own colour and falloff values
([ruins-and-weathering](ruins-and-weathering.md)).

## 2. What was sourced

| Pack (Nexus) | Permission | State | What it gives Black Marsh |
|---|---|---|---|
| Tropical Lands Assets (SE 33446) | "use any and all" | staged, indexed | kapok trees with buttress roots, palms, a bamboo table and platform, a clipper, green-cave pieces (its bamboo is not placed) |
| Waterplants (SE 6092) | credit | staged, indexed | 26 lily clumps in five colours |
| Simple Straw Hats (SE 89962) | credit | staged, indexed | 16 straw hats for workers and stalls |
| Ships and Boats of Tamriel (SE 41653) | credit, not for profit | staged, 56 statics | Breton, Imperial and Redguard boats, a city ferry, galleons, wrecks, anchors |
| Incaendo's Banner Resource (SE 17604) | modders' resource | staged, 59 statics | banners for the emblems of track B |
| Morrowind Hlaalu Architecture (SE 157997) | credit | staged, 113 statics | Hlaalu houses, towers, docks, walls for the Dunmer places |
| Phitt's Velothi Resources (SE 107571) | credit | staged, 17 statics | Velothi towers, walls, a bridge, Aldredanyia houses |
| GKB Green Trees, Harvestables, Stroti's Stilt House, Argonian War Tails (2011 game) | credit / free mods only | in the private cache, profile `held`, never laid | need an LE-to-SE mesh converter, which the pipeline lacks (stack.py only unpacks; nifglb and nif.py only read) |
| Not taken: Argonian Mercenary Armor (27676), HistBone armours (99144), Ayleid kit (90667), the two moss-shader plugins | no permission stated: the author must be asked | | |
| Not taken: Saxhleel Sundries (191593) | its author says its sets come from ESO | | |
| Not taken: Banner Resource 2 (94919, 197 MB), Flags Resource (real-world flags) | disk, or not lore | | |

## 3. Held shells against the interior gaps

[interiors-by-kind](interiors-by-kind.md) counts 72 places with only whole-hut or whole-house shells and 13 with no
fitting shell, and names four shells nothing held provides. Searched by text and look (`search query` and
`search sheet` for "kothringi great house", "hist root hall room", "root hollow tree interior", "cellar room
earthen"; sheets looked at):

- **Kothringi greathouse: held.** HTBM Curse of Cipactli `CIPHTBMVillKothGreatHouse` and its interior
  `CIPHTBMVillKothGreatHouseInt` (a round thatched greathouse on posts), with KothHut1-3 and KothHutFP. Used by no
  cell or place.
- **Hist room: held as a kit.** KotM's root halls (`HistRootHall2way`, `3way`, `4way`, `Ramp01`, `Endcap`, `Turn`,
  `Shift01/02`, `HistHallEntrance01`): a grown-root hall kit, mossy floor, snapping pieces. A Hist room composes from
  it; it is a dungeon kit, so a domestic root-hollow home is not.
- **Argonian cellar: adapt.** The vanilla farmhouse basement kit (FarmBWall, FarmBCorner, FarmBWallEntrance) is
  earth and timber with no Nordic sign; it serves a cellar.
- **Root-hollow home: not held.** No domestic room grown from roots in any held kit; the root halls are tunnels.

## 4. What is genuinely missing, ranked by what its absence costs the player

| # | Thing | Searched and looked | Where needed | Cost to the player |
|---|---|---|---|---|
| 1 | Root-grown buildings and a root-hollow home (huts, family houses, hall, granary, tree-minder's house) | "root grown hut", "living tree house", "root hollow interior", "tree dwelling": sheets show Hist trunks, root pieces and halls, no building; Nexus: nothing (interiors-by-kind section 3) | Helstrom (110 people), two hamlets, sixteen outposts of the Root-Folk, the Middle Argonia and Helstrom basin places | The interior culture's whole look: every Root-Folk settlement stands in borrowed reed or mud huts, so the lore's signature people look like everyone else |
| 2 | Dugout, canoe, punt, reed raft | 0 of 28,880 mesh files and of 47,673 catalogue rows match canoe, dugout, raft, kayak, coracle, pirogue, punt, outrigger; looked at the nearest (rotted logs, KotM boats); Nexus: Sailboats SSE (40057) holds a canoe but states no permission; no resource pack | 22 raft-master stops (the travel operator promises "a poled raft or a paddled canoe"); place notes name rafts 216 times | Small craft are the marsh's ordinary transport; their absence is seen at every fishing hamlet and every waterside stop. Plank boats stand in at the stops now |
| 3 | Argonian clothing beyond KotM's few pieces | clothing sheets looked at; 55 items filed, of which the Argonian ones are KotM's robes, hoods, hats and the Naga loincloth; three Masu and Saxhleel robes are typed armour | every Argonian commoner of 252 unstocked places | Commoners now wear something native or neutral, but a few designs repeat across the province |
| 4 | Light shell and light bone-plate armour | "shell armour", "turtle", "bone plate", "chitin light": Shellback and Bone Cultist are heavy; the Kothringi light set is enchanted; Nexus: HistBone (99144) needs the author's permission | tribes gold, pearl, rust (three of 18 cultures) | Gold keep the generic saxhleel harness; pearl and rust wear heavy pieces their lore calls light |
| 5 | Whip, claw, rapier, halberd in a Black Marsh make | name search (whip, claw, rapier, halberd, glaive) and look ("long polearm blade", "clawed gauntlet weapon"); Nexus: Heavy Armory (6308) and Glaive Danger (89156) are mods, not resources, permission not stated | six tribes' signature weapon types (crimson, forest-green, lime, plum, rose, sky-blue) | Those six tribes carry the generic Animated Armoury models; the tribes read alike in a fight |
| 6 | 2011-game packs (GKB trees, harvestables, Stroti's stilt house, war tails) | fetched and held | trees for variety; a stilt house for the swamp towns | Waiting only on a mesh converter |
| 7 | Toll bar, milestone | "toll", "milestone", "barrier", "waystone": stockade barriers and posts held; Nexus: the community barrier resource (16225) is a script, not a model | Company and Imperial roads | Small: a composed barrier or post stands in |
| 8 | Gourd, reed mat | "gourd", "calabash", "reed mat", "sleeping mat": none; bedroll and rug retextures are the adapt | households | Small: jars and bedrolls stand in |

## 5. The lightest in-game check for each kind (owner's list)

- Plants: stand in a reed marsh of one region and look round: several reed and cattail shapes, lilies in more than one colour.
- Saltrice: stand in Lake Ulaish's paddies: rice beds among the reeds.
- Dressing kinds: one grave-stake cluster in the Valley of Storms, one hackwing nest on Skeith Isle, one totem on a Murkwood shore.
- Boats: arrive at one raft-master stop (a river boat at the landing) and one ferry stop (the reed-roofed barge).
- Clothing: talk to a commoner in the next stocked place: an outfit, not BM&V's default.
- Guard: a town watch guard's cuirass shows on him and on the ground when dropped.
- Hammock: activate a placed hammock: the player lies in the net.
- Weathered ruins: the clean, moss, silt and algae Ayleid arch side by side, from above, by day.
- Pack statics: one Hlaalu house and one Breton boat placed in a Dunmer or Imperial place.
