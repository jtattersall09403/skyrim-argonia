# Foreign and remnant peoples of Argonia: what we hold, what is thin, what to make (owner calls #93/#94)

Written 2026-11-24. Nothing generated, bought or downloaded. No model was opened and no look was judged: all
"reads as" statements are by model name, record, tag and lore text. Method for making anything below: an agent
models, places, edits and dresses by hand and inspects with the place studio `look` verbs (docs/design/agent-view.md:
`at <thing> --from`, `section`, `survey`, `overview`, `playwalk`), camera tied to coordinates, distance and framing;
a blind script is used only for steps already proved. Owner steer 24 Nov: do not shrink proposals to what a script can do.

## 0. Live docs and the one to edit
Cover this: docs/research/new-art/PROPOSAL.md (s2 table, s4 routes), identity-vs-lore.md (rows 30, 71, 80-103, 127),
gear-and-clothing.md (s2 foreign kits, s4), places-and-pieces.md, nature-and-vessels.md (hulls), docs/design/items.md
(l.252-263 faction look table), story/lore/extrapolation/argonia-4e201-state.md (s4-5, 607-613, 870-893),
story/design/world/92-demographics.md. CONFIRMED: foreign gear has the widest variety (Imperial 73 records on ~68
models; gear-and-clothing.md:63); Company and pirate marks are not held (identity-vs-lore.md:30). CONTRADICTED/QUALIFIED:
PROPOSAL s2 treats the gap as "Argonian"; for foreign groups the gap is architecture and marks, not gear. NEW: Stormhold
is sourced on Markarth, which is not Dunmer (see s2). One doc to edit: PROPOSAL.md (add a "foreign and remnant" row to
s2 and the building-kit list to the "more" option); this file is the backing report.

## 1. Census (world.sqlite, 258 places; query by place_kind/status/held_by/place_note)
No culture of the 18 is foreign: all foreign people are minorities or occupiers inside Argonian places. Status: inhabited
152, ruined 49, garrisoned 17, abandoned 16, sunken 17, occupied 7. Persons stocked: 165, of whom 164 Argonian and 1
Dark Elf (person.race_id), so the six stocked places say nothing about foreigners.

| Group | Places (data) | Kinds / status | Lore look in 4E 201 (cited) |
|---|---|---|---|
| Warden forts (Imperial forts held by Archwardens) | 11 fort/keep: 9 garrisoned (Chalkmoth, Gysilla, Reedmoth, Rustmoth, Shellmoth, Silvermoth, Thornmoth, Willowmoth, Southwatch), Swiftmoth abandoned, Rainbreaker occupied by pirates; 21 places in the crimson-red culture | grey stone, gatehouse, tower, toll bar/chain, Imperial eagle over gate, Argonian reed-cord pennants, Xeech-Leel flag, moat now reed pond (place_note look: Thornmoth, Rustmoth, Silvermoth, Gysilla) | Legion "-moth" forts; moss, reed re-roof |
| Imperial ruins and posts | 12 imperial-ruin (9 ruined, 2 abandoned, 1 occupied by Brethren), 2 lighthouses, 2 Imperial mines abandoned + Ninth Shaft, Blackrose Prison (Blackguards), Giovesse castle | broken wall, arch, plinth with worn eagle, rusted lamp bracket, rails and broken sluice | empty since the secession 4E 5-10 (extrapolation 885) |
| Gideon frontier (Nibenese-descended + Lukiul) | Gideon, Slough Point, Gul-Tej, Olvani, Giovesse; 8 pale-green places | "Imperial brick and timber along Blackwood Way, wet red clay, Ayleid white-stone stumps"; Slough Point: long white bridge broken mid-span, stone customs house with weathered eagles, mud huts, a few Cyrodiilic gables | UESP Lore:Gideon "built majorly in the Imperial architectural style" |
| Imperial-descended households elsewhere | Soulrest (stone Imperial quarter at the neck, half empty), Archon (Company brick at the waterfront), Lilmoth (drowned Imperial villas under stilts), 3 planter estates reoccupied (Dunhallow, Silt-Orrel, Mereweather) | long plank house on posts with tiled roof; "layers, never blends: Imperial ashlar below, Argonian above" (material-culture.md:344) | |
| Topal Bay Company / East Empire Company | 16 places mention (Archon, Gideon house, 3 wrecks, Bramman's Watch, mines) | warehouses, bonded stores, marines; no marks held | foreign-powers.md EEC section |
| Dunmer civic | Stormhold (~a fifth Dunmer), Thorn, Archon (families), Alten Corimont outbuildings | "stone, ornate Dunmer architecture + stone roads, light posts, long wooden bridges + large Argonian mud huts" (Lore:Stormhold); Thorn "Ayleid stone under Dunmer and Imperial rebuilding" | |
| Dunmer rural and slaver legacy | Julo (House Ulvarys hall, 12 bound workers), Ashgate Landing (gang-master, 12 cutters), Vandrel Farm, Urvyn Farm, Hlaalu-named farms none (3 hits are farms named in notes) | "low stone footings with reed-and-mud walls, causeway of laid stone"; hide tents; stone barn + mud-plaster house on a mound | Dres walled plantations (Lore:Tear) |
| Dunmer sacred and Velothi tombs "in use" | 12 velothi-ruin; one niche tended by Archon Dunmer families; 5 notes name Redoran | stepped dome, ash-bowls, carved ash-grey doors under vine | ruins lane covers era/weathering |
| Telvanni, Indoril/Temple, Ashlanders | 0 places name them (0 hits "Telvanni", "Indoril", "Ashlander"); gear is held for them anyway (telvanni-robes, indoril-ordinator, redoran-tombwarden) | | items.md:255 says none holds a place |
| Khajiit | 0 own places; 35 hits: smugglers (Meris-Keth, Hollow Tide, Kitsa Burrow), crews (Kelp-Mouth cave, Marque Landing), wrecks Salt Heron, Tidewarden, Sallow Anne, traders at Gideon/Slough Point/Soulrest | moon charm of shell in cave mouth; offering cup for Jone and Jode; Soulrest is ~18% Khajiit (demographics Table A) | |
| Bosmer | 0 own places; 5 note hits (Gideon, Soulrest, Truowa, a wreck, Redtimber) | pilots, coasters | Valenwood.esp 788 refs held via BM&V |
| Pirates and Brethren | 6 places (Bramman's Watch, Kelp-Mouth cave, Aphon Signal Tower, Marque Landing, Rainbreaker Keep, Skeith), 22 text hits, 2 outlaw camps, 11 wrecks | hulks and hide tents on cypress walkways among broken Imperial arches; white-washed verandah house on stone tower; nets and ship lanterns | Alten Corimont: beached ship hall |
| Slavers' legacy | Silt Bride wreck (shackles), Ulvarys, Owing places | rusted shackles trailing from hatch | Owing system |
| Nord, Breton, Redguard, Orc, Altmer | people only: priors 0.3-4.4% by zone (92-demographics Table A); 0 places; one Breton planter house hit | | nothing to build |
| Blackguards | Blackrose Prison, Khariton watch post | grey fortress of Lilmothiit rubble, part flooded, banners and fires | |

## 2. What we hold, and fit (0-3; D = distinct from the others, F = fit to the marsh; judged by names, not by eye)
Rank-0 sources (place_source): Warden forts draw on 8 distinct Skyrim/mod forts (Fort Neugrad, Fort Tulis, Kintyra's Wall,
Ashfallow, Whiterun Watchtower, Cracked Tusk, Perilous Pass, Dawnguard Valley01); Gideon on Riften (Nordic city; notes say
Nordic pieces swapped for brick and timber, "still to add" courthouse, arena, Company house, east gate); Soulrest on
Solitude; Stormhold on Markarth (Reach stone, culture_tags dwemer,nordic,imperial: the Dunmer look is NOT what the
source gives); Thorn on BM&V Thorn; Archon on Baan Malur (dunmer,imperial,nordic: good); Ashgate Landing on Military
Camp Hjaalmarch Imperial; Julo on Honningbrew Meadery; Pirates on Waylayer's Watch, Fort Tulis, Bonestrewn Grove.
Held gear by records (material table, item.plugin): Imperial 73 (10 plugins), bonemold 47, netch 29, moonstone 26,
Khajiit caravan steel 55 (Apex 49 records on 8+4+1 models), Bosmer greenwood 26 (15 models), corsair 13 (Pirate Armor 10),
chitin 24. Held props (places-and-pieces.md): smallimperialtent 59, imperial candles 583, imperial braziers 86, Dunmer urn
dlc2darkelfurn01 x853, Raven Rock Redoran tent 36 and wells 9, Baan Malur signposts 44 and overhangs 55, Dunmer and
Imperial banners (BM&V). Not held: Company or pirate marks, toll bars, milestones, Argonian-over-Imperial marks.

| Group | D | F | Reason |
|---|---|---|---|
| Warden forts | 1 | 2 | eight Skyrim fort bodies with no Argonian mark; pale stone and moss fit; snow-fort frames and Nordic residue (nightcaller 13, identity-vs-lore.md:31) |
| Imperial ruins/posts | 1 | 2 | same kit broken; ruins lane |
| Gideon / Nibenese | 2 | 2 | brick and timber is lore; Riften frame is Nordic timber, Tropical Skyrim helps |
| Soulrest Imperial quarter | 2 | 3 | Solitude stone is the right Imperial register |
| Company/EEC | 1 | 2 | armour held, nothing else |
| Dunmer civic (Stormhold) | 3 | 1 | Markarth source; Dunmer ash-stone/chitin/bonemold style reads ash; a swamp wants Hlaalu plaster-and-timber or Telvanni fungus |
| Dunmer at Archon/rural | 3 | 2 | Baan Malur mud-brick and Solstheim additions |
| Khajiit | 2 | 2 | gear is distinct; no camp or boat kit |
| Bosmer | 1 | 3 | little visible; nothing needed beyond items |
| Pirates | 1 | 2 | cutlasses and coats; no flag, no hull |
| Slavers | 2 | 2 | Dres Slavemaster outfit held; shackle and work-roll props are vanilla |
Held-mod licences: dunmer-settlements-solstheim, project-aho, grey-quarter-overhaul, moonpath-to-elsweyr and the other Dunmer
and Khajiit rows read "none stated: placing its meshes in our plugin needs the author's permission" (mods/dependencies.json);
this limits using their pieces in a shipped plugin, not as a player's own dependency.

## 3. Nexus (searched both Skyrim games, names and descriptions; held mods excluded)
Searched: Nibenese, Colovian, Leyawiin, Bravil, "imperial fort", "imperial architecture", cyrodiil, Beyond Skyrim Bruma,
colonial, plantation, villa, lighthouse, aqueduct, milestone, stone/wooden bridge, "architecture resource", "modders
resource", Hlaalu, Telvanni, Redoran, Indoril, Dunmer architecture, morrowind architecture, ashlander, yurt, Dres, Narsis,
Khajiit, Elsweyr, caravan, Bosmer, Valenwood, pirate, galleon, East Empire, warehouse, Hawaiian, Rochebere, Stroti, Phitt,
Tamira, Oaristys, mathy79, Den of Fen, legion, road sign, signpost, notice board, slave, shackles, pillory, cage, dock,
wharf, pier, crane, cargo crates, trade goods, tabard, heraldry, shanty, Imperial Fort Resource, Beyond Skyrim Assets,
Roman, Telvanni tower, mushroom, Imperial City, silt strider, Dunmer ship, Vvardenfell, Balmora, Tribunal, Almsivi,
ancestral tomb, Ordinator, Dunmer shrine, Imperial Cult. Permissions are from description text only; nothing opened.
"2011" = 2011 game, meshes need conversion at staging.

| Fills | Candidate (id, author, endorsements, format) | Permission line |
|---|---|---|
| Dunmer swamp-fit architecture (Hlaalu: plaster, timber, stilted shacks) | Morrowind Hlaalu Architecture 157997 (Angelio, 17, SE; v2 29 MB); Den of Fen Assorted Asset pack 167214 (Fenruss, 1, SE, 1.3 GB, remeshed Vvardenfell buildings); Silgrad Hlaalu Overhaul 168071 (Angelio, 67, SE) uses it with MAL permission | 157997 "all with proper credit"; 167214 none read |
| Velothi, shack and trama kit remapped to vanilla textures | Phitt's Morrowind Resources Remapped 107571 (pancake, 5, SE, Velothi Resources 32 MB, alternate shack kit) | "freely use if you credit pancake, phitt, tamira, mihail" |
| Morrowind-style stilted and mushroom pieces, lanterns | Phitt's Sheogorad Resource Parts One/Two (skyrim:59632, 60125; Phitt+Tamira, 466/435, 2011); Phitt's Morrowind Style Lanterns 4736 (104, SE) | lanterns: free to use with credit, no money; Sheogorad: "none in paid mods", read the Terms of Use |
| Telvanni fungus towers | Telvanni Tower Resources skyrim:34882 (Earrindo, 134, 2011, 5.8 MB) | "freely used if credited" |
| Redoran rooms | Redoran architecture resource skyrim:81475 (anothersunday, 31, 2011) | resource only, needs Dragonborn |
| Dunmer furniture | Redoran Reverie furniture replacer 132695 (sothasimp, 1,865) and beds 132997 (6,680) | not read |
| Dunmer houses' identity | Dunmer Great House Capes 105159 (TheSilverSpoonhead, 30; House symbols from Bethesda banners) ; Armors of the Velothi Pt I 62752 (Pulcharmsolis, 11,931; 8 sets incl. Hlaalu Remnant, Narsis Watchman, Indoril Wayfarer, Redoran Exile) ; Tribunal Robes and Masks 4937 (7,426); Kanjs Dunmer Plinths Shrine 130009 (730) | capes credit only; others not read; Velothi needs FSMP |
| Dunmer lighthouse | Solstheim Lighthouse 14329 (fadingsignal, 3,252; Redoran-style, ESP 204 KB) + interior 27887 | not read |
| Imperial colonial, Nibenese, Colovian | Beyond Skyrim Bruma SE 10917 (68,075; 3.5 GB; needs Beyond Skyrim Assets 198585, 1.9 GB): Cyrodiilic/Nibenese/Colovian architecture, clothes, clutter; Bruma Clutter BOS 74178 (MelwenMods, 576) and Bruma Outfits for Imperials 48783 (773) show what it holds; Colovian Prince Set 79894 (Pulcharmsolis, 10,003); SKYBLIVION Cyrodiilic Steel 31206 (1,318) | assets-repository terms not read: ask the authors |
| Imperial fort bodies and walls | Imperial Stone redone 6481 (MrMcGee, 1,608; "permissions completely open"); Imperial Castles of Skyrim 129327 (2,160); Fortified Imperial Fort Battlements 66831 (1,129); Strotis Castle Wall Resource 3152 (175); Pirates of The North 28985 credits an "Imperial Fort Resource by whatever" (name searched; its own page not found) | 6481 open |
| Docks, cranes, bridges | Skyrim 3D Docks and Boardwalks 28781 (mathy79, 6,400); Cargo Cranes 126552 (Andyross1962, 39); Unique Wooden Bridges BOS 114971 (2,267) and More Wooden Bridges 42201 | not read |
| Company marks | East Empire Strongbox Logo SSE 70396 (UlithiumDragon+Gamwich, 759): logo on strongboxes; East Empire Shipping 20976 (crates); Environs Riften Warehouse 88024 (Siberpunk, 4,094; "use resources with credit") | 70396 ported with permission |
| Khajiit camps | Khajiit Has Wares 73500 (SassiestAssassin, 4,994): exotic objects round caravan camps; "to use a resource ask the original author" | ask |
| Pirates | Pirates of Skyrim (skyrim:62844, BigBizkit, 12,789, 2011; SE port 105542: ship + gear, "permission granted to package"); Pirates of The North SSE 28985 (agerweb, 736: pirate base, 4 villages); Flags Resource 56152 (held in PROPOSAL list) | read before use |
| Bondage props | Detailed NPCs Chain and Shackles 63932 (BecomingNplus1, 629) | permission cited from two authors |
| Silt striders (Dunmer transport at Thorn?) | Silt Strider models are vanilla Dragonborn; Striding Silt Strider 109619 | not needed |
Not found by any term above: an Imperial milestone or toll bar; a Khajiit dhow or moon-shrine; a Company logo of our own
name; a bayou-ready Dunmer plantation house; Imperial colonial pieces drowned or stilted. That is a statement about the terms
searched, not about Nexus.
Two cautions: Beyond Skyrim assets are Cyrodiil-in-Bruma (cold north Nibenese/Colovian stone) and may read as Skyrim
Imperial; unjudged. Hlaalu fits best because Vvardenfell's Hlaalu is itself a swamp-and-plaster style.

## 4. What to make: building kits and hero buildings (hand modelled and dressed by an agent by default)
Default method for every item: a generator or a donor model gives the mass; an agent then edits, scales, snaps and
dresses it by hand in the place studio, looks from several named angles (`at <thing> --from n..nw --eye/--high`,
`section`, `survey`, `playwalk`) and iterates; interiors are hand-dressed shells with matching door, window and floor
positions. Scripted shared-material geometry is the filler for plain pieces (walls, beams, posts), not the ceiling.
Sizes assume a 2K texture is crisp to about 4 m (PROPOSAL s3), so large buildings are kits of 2-4 m pieces plus tiling materials.

### 4.1 Imperial-colonial kit ("Nibenese in a swamp") and its hero buildings
Seen: Gideon (8 pale-green places, ~90 residents), Slough Point, Soulrest quarter, Archon waterfront, 3 estates, Fort Rustmoth kitchens.
- Pieces (about 30): ashlar plinth course (drowned-brick variant with waterline stain), red-brick wall panel, timber-frame
  infill panel, tiled hip roof and gable ends (reed-patched variant, moss variant), colonnade bay with arch, shuttered
  window, double-leaf door with fanlight, raised stoop and steps, jetty and quay edge, brick chimney, gate arch with eagle
  boss, causeway slab, bridge pier and a span that can be broken mid-way, drain grating, eave lamp bracket, lamp post.
- Materials: red-clay brick, whitewashed plaster, dark timber, tile, patches of local reed and cypress plank; a shared mould
  and tide-line overlay; key rule "Imperial below, Argonian above" (material-culture.md:344): each piece has a stone base
  and a stilt or reed upper variant.
- Hero buildings: Governor's Mansion and courthouse (Gideon; "still to add" in the Gideon note), Temple of Dibella, Topal Bay
  Company house with strong room, Slough Point customs house with its broken white bridge, Soulrest government block
  (half empty, repurposed), Company warehouse row at Archon (stone wharf, timber loft, brick gable).
- Reads as that people because: brick-and-tile gables, fanlights and columns are Cyrodiilic; the swamp shows in the moss,
  the stilted annex, reed patches and the tide-line. Gap now: Riften's frame is Nordic timber (notes).
- Difficulty: high for a full kit; start with 8 pieces and the courthouse. Candidates to hand-finish from: Beyond Skyrim
  Bruma / Skyland-class forts (s3) or generator masses. Interiors: courthouse hall with bench and dock, mansion hall,
  Company counting room: dress by hand from held Imperial furniture (Solitude/Imperial sets).

### 4.2 Warden fort kit (the Empire's forts under Argonian flags; 9 garrisoned, 2 others, 12 ruins share it)
- Pieces: curtain wall (whole, breached, vine-eaten), square corner tower, gatehouse with portcullis and eagle relief
  (original and defaced), toll bar and counterweight, toll chain post and windlass, jetty and watch boat berth, moat as reed
  pond, barracks bunk row, quartermaster store, yard grindstone, reed-cord pennant pole, signal lantern mast, prison stair
  door (Chalkmoth).
- Materials: grey limestone (chalk-dusted for Chalkmoth, moss for Willowmoth), reed-cord and reed thatch repairs, timber toll gear.
- Reads as: Imperial plan with Argonian repairs and flags layered on top. Today: 8 different Skyrim fort bodies without any
  Argonian mark (s2). The mark set (pennants, Xeech-Leel flag, reed-thatch roofs over stone) is the cheap high-impact part.
- Difficulty: medium; the kit is mostly existing fort meshes edited by hand plus about 12 new pieces.

### 4.3 Dunmer-in-the-marsh kit (Stormhold, Thorn, Archon, Julo, Ashgate)
Dunmer built in wood and mud and local stone, not ash-stone and chitin (the owner's point; lore: Julo "reed-and-mud walls on
low stone footings", Vandrel "stone barn, mud-plaster house on a mound", Stormhold "stone roads, light posts, long wooden bridges").
- Pieces (about 25): rounded plaster-and-timber wall (Hlaalu), stone footing course, curved tiled or reed roof with
  upturned ridge, shutter and round-arched door, stilted Hlaalu house variant, covered walkway, long timber bridge with posts,
  stone light post, ornate stone arch for Stormhold's Dunmer quarter, plantation hall (Dres-style walled yard, gate, tower
  for overseers), saltrice drying shed, slave pen fence (Ulvarys: work-roll board, coffle post), canal steps, Dunmer shrine niche
  and ash bowl, clan banner post, Telvanni-style fungal tower as a hero piece if any holdout exists (none in data).
- Materials: whitewashed plaster, chalky red mud brick, dark wood, glazed or terracotta tile, a little polished stone;
  house colours from the Great House capes and banners.
- Hero buildings: Dunmer hall at Julo (Aldyne Ulvarys: hall, great roll room), Stormhold Dunmer quarter and Vicecanon court,
  Ashgate gang-master's hut, an Archon Dunmer chandler's house, a tomb shrine tended by Archon families.
- Difficulty: medium; Hlaalu resources (157997, 107571, s3) give a donor base, hand work removes ash-stone reading.
  Today's risk: Markarth as the Stormhold source (F1).

### 4.4 Khajiit and Bosmer (people without places)
- Khajiit: a coaster/dhow and a smugglers' sloop hull (2 wreck places, Salt Heron and Sallow Anne, plus Tidewarden cog), a
  caravan/coaster camp set (awning, crate stack with moon marks, rug, lantern, moon charm), a moon-shell charm and an
  offering cup as hand-modelled hero props. Seen at about 8 places; Soulrest quay if built.
- Bosmer: a Valenwood coaster (shared hull donor), and nothing else; the held greenwood kit and Valenwood.esp cover it.

### 4.5 Pirates (Brethren) and Company
- Pirate: Bramman's Watch white verandah house and stone tower (hero), Marque Landing hulks-and-walkways (a hulk is a beached
  hull, hand-dressed as a house), Alten Corimont beached-ship hall, Rainbreaker keep with sea wall, nets and ship lanterns,
  Kelp-Mouth cave prize store. Pieces: hulk hull sections (3-4), cypress walkway, plank gangway, net rack, black-sail
  hanging, prize-crate set, flag pole.
- Company: warehouse (stone wharf, timber loft, hoist beam, bonded-store cage), crate and bale set with Company stencil,
  strongbox with logo, standard and notice board. Reads as: stencilled crate marks and a repeated livery.

### 4.6 Infrastructure (roads, bridges, towers; 381 road segments, 78 major)
Pieces: milestone, boundary stone, toll bar, road marker post, waystation shed with signal bracket, rail section and sluice
gate (Old Goldseam, Ninth Shaft), lighthouse lamp room (2 lighthouses; Seafalls white-lime tower), signal tower stair (outside
wall, Aphon), broken-span bridge. Difficulty: low to medium; mostly blocky shapes.

### 4.7 Flat images on existing models (no 3D)
Company standard and crate stencil, Brethren flag, Xeech-Leel flag and Warden reed-cord pennant, Vicecanon office sign,
Soulrest council seal, Gideon courthouse notice board, road-sign boards with Argonian names, Khajiit moon-charm retexture on a
held chime, and an alternate-texture Warden tabard on a held Imperial cuirass (record-level alternate texture on the armour
addon, no model edit: unverified, needs one test). The Imperial eagle, Dunmer house banners and capes already exist.

### 4.8 Weapons by "acts as"
Imperial short sword and crossbow, Khajiit scimitar/khukuri, Bosmer greenwood bow, Dunmer bonemold/moonstone, pirate cutlass
are all held (items.md:262-263); nothing new except a rapier for the Lilmoth docks (tribal-weapon lane).

## 5. Ranking (player impact per unit of difficulty) and what is already served
1. Warden-fort mark set (pennants, flag, thatch repairs, tabards, toll bar): 9 garrisons + roads, every Argonian soldier; low-medium.
2. Company and Brethren marks (flags, crate stencils, sign): 16 + 6 places; low (texture on held models, Nexus logo base).
3. Dunmer-in-the-marsh kit, starting at Stormhold and Julo: most distinctive, worst fit now (Stormhold on Markarth); medium.
4. Gideon Imperial-colonial kit and the courthouse: the province's one Cyrodiilic city; high effort, high payoff.
5. Infrastructure props (toll bar, milestones, sluice): low.
6. Pirate hulks and the Khajiit coaster (shared hull donor with the vessel lane): medium.
7. Hero props (moon charm, offering cup, chain/work-roll): low.
Already well served, need nothing: foreign gear (Imperial, Dunmer, Khajiit, Bosmer, pirate), Nord/Breton/Redguard/Orc/Altmer
(no places), Soulrest's Imperial quarter on Solitude, Archon on Baan Malur, Telvanni/Indoril/Ashlander (no places, gear held).

## Unverified
No model, texture or plugin was opened. Fit scores are from names, tags and notes; no look was judged. Nexus permissions are
from description snippets only. UESP read by API: Lore:Gideon, Stormhold, Thorn, Blackwood, Tear, Kothringi, Blackrose Prison,
Alten Corimont, Online:Blackwood (Lore:Slough Point and Fort Swampmoth returned empty).

Covered: world.sqlite (place, place_note, place_source, source_place, culture, material, guard_issue, trade_kit, person, road), PROPOSAL and the new-art reports, story/lore topics and extrapolation (foreign-powers, material-culture, roads, 4e201 state), design/world 92-demographics, quest lines (owing-house, house-cardruhn, merchants, pirates), docs/design/items.md, mods/dependencies.json, 90 Nexus terms, UESP. Skipped: drafted place files (only Ashgate Landing is foreign; not opened), out/places/catalogue (absent), mesh registries (not located).
