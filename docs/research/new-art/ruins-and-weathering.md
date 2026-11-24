# Ruins by builder, and the Black Marsh treatment (owner calls #93/#94, written 2026-11-24)

Nothing was generated, bought or downloaded. Measured = a count or file read in this pass; inference = my reading.
Counts of "reads as X" are by source-place name and culture tag, not by eye. You (the owner) judge look.

## 0. What already covers this, and the one doc to edit
- PROPOSAL.md section 5 (hierarchy game > material > culture > family > object): CONFIRMED as the frame; it has no
  axis for buildings and ruins. Edit THAT section (add the BUILDER x STATE x LOCATION axes of section 6 below); no new file.
- places-and-pieces.md A2 (kind table): confirmed against world.sqlite (imperial-ruin 12, velothi 12, kothringi 8,
  lilmothiit 9, ayleid 7, sunken 7, abandoned-village 8, wrecks 11). Its "7 sources for 7 Ayleid places" confirmed.
- PROPOSAL section 2 / places-and-pieces: "Tropical Skyrim swaps none of these: it changes trees and grass only".
  PARTLY SUPERSEDED: Tropical Skyrim.esp also overrides 12 snow material objects (MATO) with its own colour and
  scale (one STAT only). It does not touch ruins, so the finding stands for pieces, not for materials.
- place-studio.md line 1340 and agent-view.md ("Hands": move, turn, sink, duplicate, place, land, compare, snapshot):
  CONFIRMED present; the studio already draws a base's alternate textures (MODS) in `look`, so the hand-dressing
  method below needs only small additions (section 9).

## 1. Findings first
1. Bethesda's own answer to "the same wall, two states" is a SECOND STAT RECORD per variant (same model, own
   directional material, own alternate-texture set). Measured: in the load order 15,804 winning statics; 2,691 carry
   a directional material (snow 1,286, ice 840, falmer 211, moss 188, ash 110, sulfur 56). Skyrim.esm has 1,467 models
   with a material variant, 1,167 of them also having a clean twin (names like `_HeavySN`, `_LightSN`, `_Snow`).
2. King of the Murkmire (KotM) ALREADY DOES THE MOSS VERSION. It defines 3 moss material objects
   (MossMaterialArgonia01-03) and 176 "...Moss" statics, EVERY one with a clean twin on the same model (176 of 176),
   across Ayleid ruins (48 exterior CC Ayleid-style, 27 interior), Imperial rubble (13 tesak1243 MW-Imperial pieces,
   5 `argonia/imperialruins`), xanmeer rubble, rocks, mud huts, Hist trees. Its moss colour (0.200, 0.235, 0.149) is
   identical to Dragonborn's MossMaterialSolstheim01: it cloned Bethesda's moss and changed projection values.
   So a "mossy Murkwood / clean Gideon" wall is one extra STAT per model in OUR plugin, copying that pattern.
3. Vanilla moss materials: MarkarthMoss (texture mosstile), TundraMossMaterialObject (TundraMoss01.dds),
   MossMaterialSolstheim01, DirtCliffs03Moss. Vanilla uses almost none (Skyrim.esm winners: 2 moss statics); the
   Nexus mod "Moss Shaders Restored" (55279) says vanilla has "very few rocks with moss" and adds them to hundreds.
   Material data layout (MATO DATA, 13 values): falloff scale, falloff bias, noise UV scale, material UV scale,
   projection vector (z -1 = from above), normal dampener, single-pass RGB, flags (1 = single pass).
   Static DNAM = 8 bytes (max angle, material) in 11,915 statics, 12 bytes in 4,088; angle observed 0 to 120,
   90 in 13,592 of 16,003. Hoddminir's 2012 note: falloff bias sets thickness; CK does not show the shader, only the game.
4. BM&V (Black Marsh.esm) defines NO material objects; 2 of its statics carry the vanilla SNOW material (leak; Tropical's
   override tones it). It leans on alternate textures instead: 226 of 384 statics (59%) use MODS; its texture sets
   include `01mossstoneruin` (Ayleid arstone05), MOSS (vurt_spmoss021), MOSSBARK. KotM: 836 of 2,129 (39%) use MODS,
   with sets OldImpMossTexture (Markarth moss-dirt), AYLDWetStone01, AYLDWallDirty01, OldImpPlaster: one Ayleid or
   Imperial model already comes clean, dirty, wet or mossy by record alone. Cipactli: 0 of 312.
5. No tool or plugin of ours reads or writes a directional material: grep for DirectionalMaterial/MaterialObject in
   tools/ and plugin/ finds only a signature list in tools/newworld/assets_audit.py:37; the catalogue
   (out/places/catalogue/bases.jsonl) has model, keywords, `alt_tex`, but no material or angle. A small gap to close.
6. Lore vs kits, the real misfits: (a) 4 places on DWEMER sources although canon has no Dwemer in Black Marsh
   (Zeh-Orun on Irkngthand, Zul-Etha on Kagrumez, Ra'tal Den on Project AHO Dwarfsphere, Tailhollow on Avanchnzel);
   (b) Kothringi ruins (8) mostly on Nordic or Imperial stone sources; (c) 6 of 12 Imperial ruins on snowy Nordic-Imperial
   fort sources (Hraggstad, Kastav, Bloodlet Throne, Morvunskar, Highpoint Tower, Abandoned Prison); (d) 3 Velothi ruins on
   DAEDRIC ruin sources (Ashimmidarum x2, Dunnashammipuri); (e) 4 wrecks on one Nordic ship (Icerunner x2, Winter War, Katariah-
   type); (f) no place row of kind xanmeer: the oldest Argonian stone has only the 7 sunken spires; (g) Umbriel's wake
   (4E 48): 0 places mention it; lore leaves interior waypoints to us (umbriel.md).

## 2. HALF A: ruin kinds (world.sqlite, 258 places; rank-0 source)
| Kind (n) | Regions | Era, builder, holder now | Lore look | Kit today | Dist | Fit |
|---|---|---|---|---|---|---|
| Barsaebic Ayleid ruin (7) | Barsaebica 5, Valley of Storms, Blackwood | 1E 198+, exiled Ayleids; wild, Fenlord undead, Veesa-Teeleel watch | white stone in reed beds; keystones | KotM `ayleidruins` 141, CC Ayleid resources (59 statics), all KotM/BM&V/Nyhus Ayleid sources | 2 | 3 |
| Imperial ruin (12) + forts (8) + keeps (3) + prison (1) | Althii, Cape Percar, Valley, Tulmek... | Reman to 3E; forts now Archwardens/Bramman's Brethren; 12 ruins empty | grey stone, tropical decay | vanilla Imperial forts, KotM `imperialruins` + MW-Imperial rubble, Nyhus | 2 | 2 (6 snowy Nordic-fort sources) |
| Kothringi ruin (8) | Nha-Enasa 3, Kotherra 2, Blackwood 2, Banujha | Flu dead 2E 560; none/diggers/Naka-Desh chimes | cairns, glass beads, silver folk, chimes, stilt | Cipactli `kothringi` 33 models; sources Nordic/Imperial stone | 1 | 1 |
| Lilmothiit ruin (9) | Althii 5, Tulmek 3, Banujha | nomad turf-and-leaf domed dens; empty | light, low, overbuilt | KotM mounds (7 of 9); 2 Dwemer sources | 2 | 2 |
| Cantemiric Velothi ruin (12) | Okuwun 3, Hatandros 3, Chixathe 3, Arnesia 2, Nushara | Dunmer dissidents, dead of Flu; ghosts | Dunmer tomb/shrine | Baan Malur 7, Solstheim 3, DepthsOfSkyrim; 3 Daedric sources | 3 | 2 |
| Sunken ruin (7) + landmark Echo Deep | Benthic Yobesh | old Argonian xanmeer spires, drowned | stepped xanmeer | KotM spires 7 (+ Depths of Skyrim, SIRENROOT held) | 2 | 3 |
| Abandoned stilt village (8) | Tulmek 6, Cape Percar, Banujha | Argonian, left; scavengers | tiered timber halls | KotM Root Whisper/Khariton (2); Dwemer 2, Nordic/Nyhus hamlets 4 | 2 | 1 |
| Shipwreck (11) | seas, Tulmek, shores | Imperial/Dunmer hulls; salvagers | rotted timbers | vanilla Nordic ship (4), HTBM, Wyrmstooth, Northwatch | 1 | 2 |
| Xanmeer (interior) | none as a row | Merethic Argonian; Hist chamber; Naga-Kur reuse block | stepped pyramid | KotM 210, Cipactli 113, Xanmeer Resources 79, tileset | 3 | 3 (not placed) |
| Dwemer | none in lore | n/a | n/a | 4 misplaced sources | - | 0 |
| Daedric | only as Velothi stand-in | Boethiah-type dissidents (Ten-Maur-Wolk) | | 3 Daedric sources | 2 | 1 |
| Umbriel wake | none | 4E 48, undead "wormies", water-capable | | nothing | 0 | - |
Dres plantations: no ruin kind; the 3 estates are Argonian families in EMPTY planter houses (reclaimed, section 6).
Thin after Nexus: sunken/wreck dressing beyond Depths of Skyrim; a Kothringi look; tropical Imperial stone; Velothi in jungle.

## 3. Nexus (searched both games, name and description): moss, mossy, overgrown, ivy, vines, creeper, jungle ruins,
ruined, weathered, swamp retexture, tropical retexture, material object, moss rocks, mossy ruins, algae, decay,
tropical architecture, jungle overhaul, overgrown ruins, vines ruins, hanging vines, Vurt, Hoddminir, Imperial fort
retexture, Ayleid, xanmeer, Enderal, Beyond Skyrim Cyrodiil, sunken ruins, underwater ruins, ruins resource, Dunmer
ruins, Velothi, silt, mud, reclaimed, Black Marsh, Gray Cowl, Stroti, Tamira, Oaristys, InsanitySorrow, Rochebere,
Beyond Reach, Vigilant, Ruins Clutter Improved, jungle ruin, crumbling. Not searched: Elinen beyond "Hoddminir"; Mari beyond ivy/hanging moss.
No hit, so no mod found for: algae/silt/water-line architecture, tropical retexture of Imperial or Nordic stone (only rocks),
a drowned-ruin kit other than held ones. (That is a search result, not a claim Nexus lacks it.)
Permission lines: the API descriptions carried none for the SSE mods below; read each page before use. "Enderal"
(skyrim:77868, 18,089) asset terms NOT checked.
| id | mod, author, endorsements | what for us |
|---|---|---|
| 60144 | Shaders of Solstheim - Ash and Moss, wankingSkeever, 7,717 | moss material shader plugin; "uses your own moss textures", 0 worldspace edits: the pattern to copy |
| 55279 | Moss Shaders Restored, Exalderan, 1,355 | moss material on hundreds of rock statics (5 KB): a list of exactly what we would make |
| 192910 | Simplicity of Snow Sulfur Ash Moss, wSkeever, 1,030 | blended moss, XPMF |
| 83199 / 84706 | Markarth Mossy AF / Lite, GGUNIT, 860 / 500 | mossy retexture of a stone city; optional custom moss shader file |
| 33225, 34772, 150002 | Rally's / Mari / Skyking hanging moss, 6,740 / 3,091 / 905 | textures for the existing hanging-moss pieces (Murkwood "hanging moss") |
| 10305, 113578, 37112, 82048 | HD Ivy 16,590; HQ Ivy Replacer 5,843; Ivy by Mari 4,826; Animated Ivy 1,758 | ivy sheets on ruins |
| 40196, 101926 | 4K Tendril Vines 1,649; Subdivide and Smooth Vines 850 | the Only-Cure vine masses (Dawnguard) retextured/remeshed |
| skyrim:90667 | Ayleid Ruins Building Kit -Resources-, Imperial Society, 259 (2011: convert) | complete Ayleid kit; page cites the original author's permission |
| 5870 (+71127) | Ruins Clutter Improved, raiserfx, 59,729 | rubble/clutter textures and meshes |
| 118028 / skyrim:71234 | Exist's Imperial Forts PBR 260 / Castle wall kit 38 | Imperial fort retextures |
| skyrim:34317 | MSFoxhound Tropical Based Rock Retexture, 140 | tropical rocks (2011, convert) |
| 20636 / skyrim:93800 / skyrim:83982 | Project Rainforest SE 858 / LE 515 / Tropical Skyrim Enhanced 389 | whole-land tropical conversions; ruins not the point |
| 133104, 38544 | Tomato's Markarth and Dwemer Ruins parallax 936; Temples of the Ancients 4,493 | stone retexture leads (content not read) |
| 185420 / 181193 | Desert Ruins Tileset 11; Xanmeer Tileset 23 (held) | DarthVitrial tilesets |
| 23062, 57446 | The Marshlands (Tesfiend) 2,209; Snow Elf Ruins Resource Pack (Step) 87 | marsh environment lead; resource pack |
Held and relevant: KotM, Cipactli, CC Ayleid, Xanmeer Resources/Tileset, Depths of Skyrim, SIRENROOT, Baan Malur, Caves of Morrowind, Project AHO.

## 4. HALF B: the Black Marsh treatment, one kit made many ways (the method is hand work)
Default method (owner steer): an agent dresses each place by hand in the studio, looking from several framed angles,
judging, undoing. Records and shaders only make the dressing cheap to repeat.

**Record level (measured precedent above)**
- R1 Moss twin: one extra STAT per model with a moss material (KotM pattern, 176 precedents). Angle 90 default; use
  30 for ledges only, 70 to 80 for rubble. Cost: one record per model.
- R2 Texture-set twins: `Clean`, `Dirty`, `Wet`, `Mossy`, `Silted`, `Drowned` TXST per kit, chosen per shape by MODS
  (KotM does clean/dirty/wet/moss on Ayleid already). Cost: one TXST per kit state, no mesh.
- R3 New material objects of our own (silt, algae, tide-line, soot): copy KotM's MossMaterialArgonia values, change
  colour and falloff. Colour-only (single pass), no texture file needed (inference: the ShaderBox.nif these point to is in
  no archive held, so the look rests on the record's colour; only a game look settles it).
- R4 Decals (TXST decal data): vanilla has 52 such sets in Skyrim, 7 in the DLCs, none in BM&V, KotM or Cipactli; what
  places them was not measured. Treat as trial.
- R5 Variant naming: "MossLight/MossHeavy" copies Bethesda's `LightSN/HeavySN` ladder: one model, three amounts.
**Engine limits.** One directional material per static (single DNAM field: measured). Cannot be changed by Papyrus at
runtime (Nexus forum topic 956433, repeated reply). Only upward-facing-by-angle surfaces. Vanilla has LOD-specific
materials for snow and ash (SnowLODMaterial, SnowLODMaterialHD, AshLODMaterialMtns1P) and none for moss: so far
LOD would show clean stone (measured absence; consequence inferred; DynDOLOD textures settle it). Performance: single-pass
shader on ~2,700 vanilla uses; inference that it is cheap. Do BM&V/Tropical define moss, mud or algae materials? No (0 and 0).
**Placement level (agent's hands)**: hang ivy/vine/root masses on walls, rubble and fallen masonry at the base,
silt mounds and `land` patches around thresholds, water level and tide-lines as placement, reed or timber patches over
stone, birds and bats, webs (75 in the catalogue), lily and duckweed (55). Catalogue stock, name-matched:
ivy/vine/creeper 112 (Skyrim 46, Dawnguard 23, KotM 17), moss-named 449, root-named 332, rubble/debris 1,042
(Skyrim 379, KotM 205, Baan Malur 130), mud/silt 413, algae/kelp 34 (22 Depths of Skyrim), puddle/stain 24,
leaf litter 18, hanging moss 24 (Cipactli 8). Roots and rubble are plentiful; vines, algae, litter and stains are thin.
**Art level (agent's eyes and hands, Blender while looking at renders)**: hand-modelled vine and root masses, collapse
pieces, repair pieces, a drowned version of a piece (broken, tilted, half-buried), vine/moss cards from a Fal alpha
image, silt and rubble mounds, water-line decals. Tools the eyes and hands need: (a) `look` of an own model beside the
donor with the studio's id-buffer judgement; (b) a `dress` verb: place a named dressing set (vine, root, rubble) on a
structure's face by rule, with an undo; (c) a surface-aware `place` (snap to the wall face and point along the normal;
today `place` takes x,y,z and `sink` buries); (d) a `variant` verb to compare Clean/Mossy/Drowned twins side by side
(`compare` exists); (e) catalogue fields `dir_mat` and `dir_angle` so the studio can draw moss as the game does;
(f) a `waterline` look: a horizontal section at the place's water level, which `section` nearly gives.
Derivative caution: code-blending moss into a vanilla or mod texture is a derivative of that texture (fine for a private
build under rule 0003 so long as nothing is shipped; mods whose terms bar derivatives, and KotM's AI clause for
anything resembling AI use, need reading before use). A code blend is not AI. Nothing is blended here.

## 5. Own art, cheap, by route (the hand method as default)
| Set | Route | Difficulty | Seen, how often |
|---|---|---|---|
| Vine and root masses (4 to 6) | generated solid shape, hand-cleaned in Blender, shared bark/moss material | medium | every Argonian ruin, abandoned village, Imperial ruin |
| Vine/moss cards | Fal alpha image on a card model, hand-built | medium | walls and eaves, hundreds |
| Rubble, silt, fallen masonry (6 to 8) | hand-built from simple shapes plus vanilla rubble textures | easy | every ruin and wreck |
| Water-line and stain decals (4) | TXST decal set from a hand-painted/generated image | easy to medium (decal path unproven) | drowned places, 20+ |
| Bird/bat mess, webs | records over held models | easy | caves and towers |
| Collapsed-roof patch in reed | hand-built over a held wall | medium | Imperial ruins reclaimed by Argonians |
| Repairs in local materials: reed-and-timber over Imperial wall, mud-brick infill in a Dunmer arch | hand-built patch piece | medium | forts held by Warden, Dunmer estates (about 25 places) |
| Drowned variants of held kit pieces | hand tilt, sink, sediment, TXST | medium | sunken 7, wrecks 11, drowned quarters |

## 6. Axes extending the hierarchy (PROPOSAL section 5, level 2 and 3 for buildings)
BUILDER (culture/era): Argonian xanmeer-era, Argonian living, Barsaebic Ayleid, Kothringi, Lilmothiit, Velothi/Dunmer
(Dres era too), Imperial (Reman/Second/Third), Warden-held Imperial, pirate/Company, Daedric stand-in.
STATE: 1 maintained and lived in; 2 used but neglected; 3 abandoned; 4 ruined; 5 drowned; 6 reclaimed (by Argonians
or by the marsh). LOCATION: mangrove coast / deep swamp / jungle upland / dry south (region wetness 0.2 to 0.9, measured).
Measured counts (builder x state; status field):
| Builder | inhabited/maintained | garrisoned/occupied | abandoned | ruined | sunken |
|---|---|---|---|---|---|
| Argonian living (settlements, camps) | 119 | 8 | - | 1 | - |
| Argonian abandoned villages | - | - | 8 | - | - |
| Argonian xanmeer-era sunken | - | - | - | - | 7 |
| Imperial/Warden forts, keeps, prison | - | 11 occupied or garrisoned | 1 | - | - |
| Imperial ruins | - | 1 | 2 | 9 | - |
| Imperial/Dres estates and mines | 9 | - | 3 | 1 | - |
| Ayleid | - | - | - | 7 | - |
| Kothringi | - | - | - | 8 | - |
| Lilmothiit | - | - | - | 9 | - |
| Velothi | - | - | - | 12 | - |
| Wrecks (Imperial/Dunmer hulls) | - | - | - | 2 | 9 |
| Other (Gideon, mixed, caves, camps) | 24 | 4 | 2 | - | 1 |
So 45 of 258 are plain ruined; 119 are living Argonian; non-Argonian BUILDERS stand in about 85 places (ruins 56, forts,
keeps and prison 12, estates 3, wrecks 11, plus mines and mixed).
Treatments by STATE (apply by rule, any kit; LOCATION sets the amount):
| State | Record | Placement (hand) | Art |
|---|---|---|---|
| Maintained | clean twin, Clean TXST | no growth; fresh repairs; banners; swept silt line | repair patches in local material |
| Neglected | Dirty TXST, light moss twin | ivy on shady walls, silt at thresholds | vine cards |
| Abandoned | Mossy TXST, moss twin heavy, no clean | roots in cracks, litter, roof holes | collapsed-roof patch in reed |
| Ruined | moss twin, wet TXST, rubble variants | collapse, rubble piles, trees through walls, vine masses | collapse pieces |
| Drowned | Silted/Wet TXST, algae material | `land` down to the water line; sediment mounds; kelp (Depths of Skyrim) | drowned variants, water-line decals |
| Reclaimed (Argonians) | clean twin kept + Argonian infill | reed/timber patches, totems and chimes over Imperial/Dunmer stone | repair pieces |
| Reclaimed (marsh) | heaviest moss, root TXST | roots through floors, Hist-root pieces from KotM/Cipactli | root masses |
LOCATION scales it: mangrove coast and deep swamp (wetness 0.8 to 0.9) take algae, silt, tide-lines and heavy moss;
jungle upland (Arnesia 0.55, Chixathe 0.3 to 0.55) takes vines and roots with less water; dry south (Skeith 0.2, Chixathe
mesa tops) takes dust and lichen, almost no moss. Four rules a drafter can apply: a kit is dressed by state first,
location second; Argonian reuse of foreign stone is shown by repair in local material, never by retexturing the stone;
xanmeer stone is never repaired or quarried (material-culture.md line 302); Dwemer is not a builder here.

## 7. Ranked by player impact per difficulty
1. R2 texture-set twins for the ruin kits (KotM already ships sets; BM&V 59%): cheap, shows state at once. (Measured precedent.)
2. R1 moss twins for our ruin models, copying KotM's 3 materials: cheap, visible from outside. Needs a look in game.
3. Fix the misfit sources: 4 Dwemer, 3 Daedric, 6 snowy Imperial, Kothringi on Nordic: records only; biggest "wrong place" gain.
4. Hand dressing in the studio with held vines, roots, rubble (stock counts above): no new art.
5. Repair-in-local-material pieces and reed roof patches: the new idea that tells the story of who holds what.
6. Hand-built vine/root/rubble set and drowned variants: medium, large visible gain in ruins and wrecks.
7. Decals: unproven path, trial first. 8. LOD moss: only if distance shots show clean stone.
Only a trial in game settles: whether KotM's colour-only moss reads green on our walls; whether Tropical's snow
override leaves white; whether moss is missing in LOD; decal draw; vertex-colour tinting (not measured at all).

## 8. Recommendations
- Add `dir_mat`, `dir_angle` to the catalogue and carry them in own_bases (evidence: finding 5).
- Pilot one ruin: Gemin (Ayleid) with moss twin + wet TXST + hand-dressed vines, shown beside the clean version.
- Edit PROPOSAL section 5 with the building axes; re-source the 4 Dwemer places (place-plan, no art).
- Read the permission text on 60144 and 55279 pages before borrowing material values (they are only a pattern).

Covered: world.sqlite (place, place_source, source_place, region, culture), lost-peoples, umbriel, material-culture, history-timeline,
hist-placement, places-and-pieces, identity-vs-lore, PROPOSAL 1-6, place-studio, agent-view, catalogue bases.jsonl,
all load-order plugins for MATO/STAT/TXST (own parser), UESP CK, Hoddminir blog, Nexus API, mods/dependencies.json.
Skipped: out/places/catalogue/plugins (per-mod lists), foreign-powers.md and extrapolation files (not needed), nif contents, in-game looks (none possible).
