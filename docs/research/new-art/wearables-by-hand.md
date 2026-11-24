# Wearables by hand: clothing, light armour, masks, horns, bows (owner calls #93/#94, re-plan of PROPOSAL sections 7 and 8)

Research only; nothing generated, bought or downloaded. Method: vanilla meshes read with a throwaway nifly probe built
against the pinned nifly (`~/.argonia/src/nifly`, scratchpad `p/sp.cpp`: blocks, shapes, skin instance, partitions,
per-bone weight counts, node tree, controllers, extra data); ARMO/ARMA/RACE/HDPT read from Skyrim.esm with
`tools/navmesh/esm.py`; 2,291 vanilla armour/clothes NIFs and 574 character-asset NIFs read through
`tools/places/assets/resolve.py` into the scratchpad (not the repo). Tags: [M] measured here, [W] from a cited page
(pages read by search summary; ck.uesp.net and Nexus return 403 to fetch, so quotes are second hand), [I] inference,
[T] only a trial settles.

## Live docs and the one to edit

PROPOSAL.md section 7 "would not do" (full outfits, bows, thrown) and section 8 "the honest gap: clothing" are what this
supersedes. `skyrim-asset-pipeline.md` (tool chain, PyNifly Linux PARTIAL) and `gear-and-clothing.md` (audit counts) I
confirm. The doc to edit: PROPOSAL.md sections 7 and 8 (rewrite whole, per the owner's overrule); add an "authored
meshes / worn" row to `docs/research/skyrim/skyrim-tooling.md`. No new file.

## FINDINGS FIRST

1. The reluctance has no technical basis for the editable-outfit route. Every vanilla outfit is already one set of skinned
   shapes with weights, 3 or fewer partitions and a _0/_1 pair of identical topology [M]; reshaping by deleting or moving
   vertices keeps those weights, and only new vertices need transfer. That is hand work an agent can look at.
2. One ARMO serves every race through ARMA records, not through one mesh [M]: body items (cuirass, boots, gauntlets,
   robes, farm clothes) carry ONE ARMA, primary race DefaultRace plus an Additional Races list that names all ten playable
   races (and vampire, Elder, Manakin variants). Head items carry THREE to FOUR ARMAs (default / Argonian / Khajiit / sometimes Orc).
   So body clothing is one mesh set for 10 races x 2 sexes; only headgear multiplies.
3. Eight human races share one skeleton, one body and one skin set; Khajiit and Argonian share `skeletonBeast` and a beast skin set [M]. The
   Argonian "body" is the human body mesh (`MaleBody_1.NIF`) with an Argonian skin texture set; only hands, feet are not
   in the cuirass ARMAs: Argonian has its own hands mesh (`MaleHandsArgonian_1.nif`) and a separate tail mesh (slot 40).
4. Horns are single-bone head parts [M]: all 21 Argonian horn files are one skinned shape, ONE bone, one influence, partition 131.
   Circlets, rings and helmets are the same: 1 bone, 1 influence. Rigid-on-a-bone is how Bethesda builds every
   head ornament, so a new horn, crest or mask is "rigid mesh, weight 1.0 to the head bone": no weight painting at all.
5. Bows are not hard geometry: the limbs and string are ONE shape skinned to 7 named bones, max 2 influences [M]; draw
   animation is NOT in the NIF but in `Weapons\Bow\BowProject.hkx` shared by elven, steel, orcish, nord hero bows [M].
   A new bow needs the same bone names and chain, and nothing else is animated per bow.
6. The real obstacle is one: writing a skinned NIF (skin instance, partitions, bone list) on a Linux box. PyNifly is
   Windows-only per its README [W]; our nifly C++ has the calls to do it (below) [M]. Everything else (looking, posing,
   weighting) works in headless Blender, which we do not yet have installed [pipeline report].
7. Our stack has no body mod (no CBBE/UNP/HIMBO/BodySlide row in `mods/dependencies.json`; grep) [M]. One row,
   "DX Necromancer Robes - UNP" (dependencies.json:6756), is UNP-fitted and unproven on the vanilla body [I].
8. Argonian head parts in vanilla: 91 HDPTs mention Argonian (horns 10 male + 12 female "hair" entries over 21 files, 9 hairline pieces, brows, 5 scar files each
   sex, eyes, mouth, 2 heads) [M]; Black Marsh.esm and the asset mods we hold add no Argonian/horn/feather/frill/crest head part [M]. Tint layers: Argonian
   RACE holds 37 tint entries, 18 mask files (SkinTone, Forehead, EyeSocket, EyeLiner, Nostrils, Laughline, Cheeks, Lips, Chin, Neck,
   6 Stripes, Dirt) [M]. The only tribe-by-head levers are therefore ours to add.

## A. Clothing and light armour by editing existing outfits

### What a vanilla outfit is [M]
`farmclothes01/torsom_0.nif`: shape `upperbody` BSTriShape 1378 v / 2041 t, 36 bones, max 4 influences, 0 verts over 4,
BSDismemberSkinInstance partitions {32 body:1807 tris, 34 forearms:106, 38 calves:128}, plus a second shape
`MaleUnderwearBodyOutfit` 141 v, shader type 5 (skin tint), texture `MaleBody_1.dds`, partitions {32,34}: the body skin that shows
where the cloth stops. `_0` and `_1`: both 1378 v / 2041 t, same shapes, bytes differ (positions only) [M]. A ground model
`torsogo.nif` is a separate unskinned single shape (1278 v), first-person `1stpersontorsom_0/1` separate (88 + 264 v).
Female `torsof`: 1148 v + `ClothSkin` 292 v type 5. Argonian handling for body clothes: none (ARMA lists Argonian) [M].
Argonian skin on type-5 shapes: a skin texture set from the race's naked-body ARMA (`NakedTorsoArgonian` NAM0/NAM1
texture sets 0x4e86f / 0x58db9) is applied to any worn body-part shape with the skin shader [W: Nexus thread 13152894
summary; I: not reproduced here] [T: view an edited outfit on an Argonian before trusting].

### Candidate bases (vertex counts from the files) [M]
Loincloth and wrap territory (little cloth, skin shows, tail free): `beggarclothes/torsom` rags 572 v + underwear body 982
(rags are a shape of their own: `rags` 572 v, partitions 32+38, 5 bones; delete the top and it is a wrap);
`prisoner/prisonerrags` 1303 v (+ skin 1137); `forswornarmor/forswornarmor` torso 1414 v + 1091 skin (fur and hide, bare arms, the nearest light-armour
base for hide and bone-plate: reshape the fur into scale, 38 calves partition kept); `minerclothes` 1691 v; `nocturnal/outfitf`
1861 v (bare-midriff cut, partitions 32,34,35,36,38: shows how Bethesda splits a cut-out); `jester`, `wench`
(WenchTorso 1604 v). Light armour: `hide/m/cuirasslight` 1922 v 28 bones, `studded`, `thievesguild`, `nightingale` torso 2903 v
(32 bones). Robes (kilts and long wraps from the skirt of a robe): `monkrobes` 905 v (the lightest robe, 28 bones, one shape + 86 v skin),
`mageapprenticerobes` 3440 v, `psiijicrobes` 1740 v, `graybeardrobe` 2306 v, `mdrobe` (mythic dawn) 1200 v single partition 32, `thalmorrobes` 1145 v.
Rank for Black Marsh dress, my judgement [I]: (1) beggar rags and prisoner rags for wraps and loincloths (fewest verts, most skin),
(2) monk robes for long cloth, hooded variants exist, (3) Forsworn torso for hide and bone plate, (4) farmclothes01/02 for tunics, (5) nightingale
or hide cuirass for scale and shell.
Head items, Argonian handling [M]: `monkhood_arg_0` (702 v) has the SAME vertex and triangle counts as `monkhood_0`,
the Argonian hat `hatargm` 157 v is a different mesh, `redguardhoodmarg` 432 v same as default, `executionhoodargonian` 789 v vs 790.
Iron helmet: human 786 v/1198 t, Argonian 786/1198, Khajiit 786/1198, female human 809/1252 [M]. So beast variants are usually
the same topology reshaped to the snout; that is exactly what makes a conform or shrinkwrap pass automatable.

### What the agent does by hand (Blender, one body, one skeleton) [I]
Import the donor _0 and _1 with the skeleton; select cloth verts in a named camera view; delete the sleeves or trousers; move boundary
verts to a hem; extrude a sash strip and let the new verts take weights by Data Transfer from the nearest body face
(Blender manual Data Transfer modifier, vertex groups "nearest face interpolated"; Weight Paint "smooth"); limit total
to 4 and normalise; build _1 as a shape key on _0 (PyNifly: "_0 and _1 body/armor weights can be represented as shape
keys with those names"; "Export _0 and _1 armor weights for Skyrim from a single mesh" [W README/Home]); retexture on the existing
UVs. Cut cloth requires trimming the underlying type-5 skin shape: it stays as is (it is the body), only its partitions must keep slot 32
so the engine hides the default body [M partitions].

### What must stay in step [M unless marked]
- _0/_1: identical vertex count and order, per shape. Measured on farm clothes, iron, hide and nightingale cuirass: equal counts. Rigid
  items have NO pair: `silverring_1.nif` is the only ring file and the ARMA still names `_1`; helmets and circlets have one file.
- Partitions: BSDismemberSkinInstance with ids 32/34/38 (body/forearms/calves), 33 hands, 37 feet, 131 hair+head (31+100), 130 head, 142 circlet slot 42, 40 tail.
  Triangles must be assigned to a partition; deleting triangles leaves empty partitions (nifly `RemoveEmptyPartitions`, NifFile.hpp:624).
- Bones: one skinned shape carries only the bones it uses (22 to 36 for torsos); the export keeps them by name.
- First-person `1stperson*` meshes and the `*gnd` ground model are separate files; the ARMA names first-person MOD4/MOD5.
  A kitbash needs three outputs: world (_0/_1), first person (_0/_1), ground (static). For a wrap the first-person shape is the cut-down arms [I].
- ARMA: new ARMA with models, race lists, footstep, and the ARMO model pointing at it. These are records, our usual path.
- Argonian heads: separate ARMAs and meshes, section "All ten races". Tails: separate slot 40 ARMA, shown by default when
  body armour does not claim slot 40 [M slots: cuirasses use [32] only]; a wrap leaves the tail free naturally.

## B. Rigid plates, masks, horns

Plates on cloth: plates are rigid solid meshes joined into the outfit shape (one more shape in the same NIF with a BSDismemberSkinInstance
on the same partition), weights 1.0 to one bone (pauldron: upper arm, breastplate: Spine2, bracer: forearm) or copied from the nearest cuirass
vertex (Data Transfer). Single-bone is how Bethesda does rigid parts (rings, circlets, helmets: 1 bone, 1 influence) [M]. Clipping is judged in poses (section C).
Masks, crests, horn caps: model as a circlet-type (slot 42) or helmet-type (slot 31/130) item. The vanilla circlet is 1-bone, 201-252 v per shape, partition 142; the Argonian circlet is its own 201 v mesh vs the human 234 v [M]. See "All ten races" for the variants.
Head-part route for permanent horns: HDPT record + one rigid skinned file: fits the same recipe as the 21 vanilla horn files [M].

## C. Weights by hand and testing by posing

- Transfer: Blender Data Transfer / nearest-face-interpolated, then smooth; cap at 4 influences, normalise [W Blender manual Weight Paint, Data Transfer; PyNifly export enforces the 4 cap per the pipeline report].
- Poses: PyNifly imports and exports Skyrim/FO4 HKX natively in Python ("complete HKX animation import/export in pure Python", skeleton from the game's skeleton.hkx; animation needs Blender 4.4+; limits: no root-motion export, no float tracks) [W wiki HKX page, Character-Animations page, README]. Vanilla HKX files are on this machine inside `Skyrim - Animations.bsa` (bow draw/release/idle HKX listed [M]), so an agent can import real idle, run, sneak and sit clips onto the skeleton: VERIFIED that the files exist, PARTIAL that the importer works headless on Linux [T]. Fallback: hand-key six poses on the skeleton (arms up, deep crouch, sit, stride, sneak, idle), which is a script of rotations on named bones, no tool risk [I].
- Look verbs, proposed on the agent-view contract (named cameras tied to coordinates, probe, section, orbit, hands; `docs/design/agent-view.md`): `fit <outfit> --race R --sex S --weight 0|1 --pose P --from side` (one framed view, `subject_seen` and clipping score), `fit --sheet` (pose x angle x sex contact sheet), `probe fit`: per pose, count of cloth vertices inside the body mesh (negative offset) and body vertices poking through, number of vertices with 5+ influences, triangles stretched over 3x rest area, a tear check; `section` through the thigh, shoulder; `compare` before/after a weight edit; `pick` on a pixel gives the shape and nearest vertex. All numbers like `probe --all`; look is judgement. These do not exist: they are the build.

## D. Bows, crossbows, blowguns

Bow (iron, steel, elven, forsworn, falmer read) [M]: one BSTriShape, skinned, 7 bones (Bow_MidBone > Bow_LoBone1 > Bow_LoBone2 > Bow_StringBone1; Bow_UpBone1 > Bow_UpBone2 > Bow_StringBone2), max 2 influences per
vertex, partition 32; iron bow 1510 v: weights by bone verts mid 429, lo1 418, lo2 506, string1 67, up1 409, up2 391, string2 67; the string is the same shape as the limbs, ~134 verts. Root: BSFadeNode,
extra data BSBehaviorGraphExtraData `Weapons\Bow\BowProject.hkx` (shared by elven, steel, orcish, nord hero; iron and wooden point at their own `Weapons\Iron\IronBow.hkx`, `Weapons\Wooden\Woodenbow.hkx`),
NiStringExtraData Prn=WeaponBow, BSX flags 66 or 202, BSInvMarker, collision bhkRigidBody. No NiTransformController in a bow NIF: the claim "limbs and string are skinned and animated" is TRUE for the first part and the animation lives in the HKX, not in the mesh, which is the good news: a new bow shares it [M].
Hand route: copy donor nif; replace the shape with new limb geometry; weights by nearest-vertex copy from the donor's limb (limb verts to Lo/Up chains, string verts to String bones, 2 influences); keep the string geometry from the donor; test draw by moving Lo2/Up2 and the string bones (rotate Bow_Lo/UpBone1 about their rest pivot) in Blender and view side and front: VERDICT bow: feasible, easy-medium, the most mechanical of the skinned items. Risk [T]: bone rest transforms must match the HKX, so keep donor bone nodes untouched and only reshape the mesh.
Crossbow (Dawnguard) [M]: 1480 v, ONE shape, 10 bones (CrossbowRoot 728 v, R01/R02, StringR/L, L01/L02, CockingMechanismCtrl 218 v, RollerNutTriggerCtrl 130 v, TriggerCtrl 64 v), 7 NiTransformControllers
(with interpolators) on the node tree, BehaviorGraph `DLC01\Weapons\Crossbow\CrossbowProject.hkx`; dwarven crossbow 18 controllers. VERDICT crossbow: harder than a bow
because the mechanism parts are skinned rigid, controllers must be kept intact, but a reskin of the donor's mesh keeping every node, controller and bone name is a texture-and-shape swap; a new mechanism is medium-hard [T].
Blowgun (Blowgun_by_Ruddy88, mod 12910): ESP read [M]: WEAP `R88_DartGun` animation type 9 (= crossbow), speed 1.3, model `Weapons\Blowgun\Blowgun.nif`, AMMO `DartQuiver.nif`, PROJ `DartProjectile.nif`, a spell `R88_BlowGunSPELL` ("Blow Gun Script"). Its NIF is NOT on this machine
(no staged or asset copy; Nexus preview link 404) so the structure is UNMEASURED; type 9 implies it rides the Dawnguard crossbow graph [I]. Verdict: use as is; to reskin, copy as a crossbow donor after the first read.

## E. Moving parts

Vanilla chest `clutter/containers/chest01/chest01.nif` [M]: BSFadeNode `Chest01` with an NiControllerManager (controller on the root), 2 NiControllerSequence ("Open"/"Close" style: NiTextKeyExtraData x2 for the sound/state keys), 1 NiMultiTargetTransformController, 4 NiTransformInterpolators + NiTransformData, an NiDefaultAVObjectPalette; nodes `Lid` > `Latch` (shapes Lid:0 210 v, Latch:0 60 v) and `Chest` (236 v), bhkRigidBodyT collision on both Chest and Lid nodes, BSXFlags 11.
`upperchest01` has the same tree, Chest > Lid > Latch (Chest 226 v). "Keep the donor's controller and node names" means: the node names `Lid`, `Latch`, `Chest` and the sequences'
target node names stay exactly; replace only the three shapes' geometry (same pivot at the hinge, since the animation rotates the Lid node); keep collision bodies attached to the same nodes. `basketclosed01` is a static single shape (355 v) with a convex collision hull: it does NOT open; a lidded basket is a chest reskin [M]. Doors: `nordoorsm01` nodes LeftDoor01 / RightDoor01 / Object02, 5 shapes, NiControllerManager. VERDICT: chests and doors are the easiest "moving parts": no skin, no weights; the work is geometry on the donor's pivots. Check by open/close frames in Blender (set the controller sequence frames or rotate the Lid node) and probe the pivot.

## F. Tools (see pipeline report for the chain)

- Skinned write: PyNifly is "Windows only" [W README]; Blender 4.0+ and 4.4+ for animation. Run on the Windows play machine (argonia-play, on demand), the agent drives Blender by command line (Blender's `--background --python` on Windows works); costs machine time. Linux build of its C++ DLL unproven [pipeline report].
- Extending `tools/newworld/niflod/niflod.cpp` [M]: it today writes only static LOD shapes (`CreateShapeFromData`, `SetTextureSlot`, shader flags; 135 lines, no skin code). nifly already exposes the calls needed: `GetShapeBoneList/SetShapeBoneList` (NifFile.hpp:373,385), `GetShapeBoneWeights/SetShapeBoneWeights` (390,451), `GetShapePartitions/SetShapePartitions/SetDefaultPartition/RemoveEmptyPartitions` (479-493,624), `CalcShapeTransformGlobalToSkin`. A "donor graft" command: load donor NIF, load a shapes file (verts, tris, uvs, normals, plus per-vertex bone indices and weights and a tri-to-partition list), replace the donor shape's geometry in place (keeping its skin instance, bone list, shader, texture set), write. Estimate 250 to 400 lines plus a Python writer for the weights file; its partition list reuses the donor's ids. Risks [T]: nifly's geometry replacement vs BSDismemberSkinInstance bookkeeping, tangents, and the bone-bound `NiSkinData` transforms. This is "proven once as a block, then copied": it should be a pilot, because it removes the Windows dependency and gives a verifiable `fit` round trip (write, read back with `nifdump`, view).
- Outfit Studio / BodySlide: Outfit Studio has an automation script run `OutfitStudio --automation "<Script>" [inputs]` ("-a"), headless prompts answered by default, 71 step types, exit codes 0/10 [W wiki Automation Dialog]; whether a display is still needed is not stated. It exists as Windows software; use as a conform/weight-transfer worker on the play machine only if Blender plus PyNifly fall short [T].
- Textures: retexture on existing UVs: the image model paints new diffuse (weave, dye, motifs) on the UV layout; `tools/places/assets/dds.py` reads; BC7 write needs texconv build (pipeline report). View on body in Blender and in the agent-view contract.

## G. Argonian texture-only and head-part ideas

Tint layers: `ArgonianRace` RACE has 37 tint entries over 18 masks (SkinTone, Forehead, EyeSocketUpper/Lower, EyeLiner, Nostrils01, Laughline, Cheeks, CheeksLower, Lips, Chin, Neck, Stripes01-06, Dirt) listed twice (male/female) [M]. Tint layers are applied by the engine as colour masks over the head and, for body paint, over the body skin; an NPC record can carry layers (TINI/TINC/TINV/TIAS) without generating them live, but FaceGen head textures are baked, so adding paint to named NPCs means regenerating FaceGen for them with the Creation Kit [W: modding practice; I; T]. Per-tribe skin tones need a new skin texture set (TXST) and a new race skin ARMA or per-NPC `skin` override: record work, no mesh [I]. New paint mask files: Beast-race paint packs add 54 face and 101 body paints for Argonian/Khajiit through RaceMenu [W Nexus search result]: RaceMenu is not in our stack, so for us the layers must be in RACE or NPC records.
Head parts: horns/feathers are HDPT hair-type records with one rigid single-bone file [M]; 21 vanilla files, 9 hairline pieces, so a tribe's horn is a new HDPT (+ a hairline piece if the horn shifts the hairline) and a rigid mesh fitted to the head by hand: the same recipe as masks. Available to NPCs by record (HDPT in the NPC); available to the player only through RaceMenu or by being added to the race's head-part list, so only NPC-side for us [I].

## ALL TEN RACES (owner correction of the coordinator)

### 1. How one ARMO serves every race [M, Skyrim.esm]
ARMO lists ARMAs; each ARMA has a primary race (RNAM) and an Additional Races list; the engine uses the ARMA whose lists contain the wearer's race [W CK ArmorAddon page, second hand].
Samples, ARMAs per item and playable-race coverage (of 10):
| Item (slot) | ARMAs | Coverage |
|---|---|---|
| Iron cuirass (32), hide cuirass, farm clothes, nightingale cuirass | 1 (Default; additional races 23-24 incl. Argonian, Khajiit, Elder, vampires, Manakin) | 10/10 (the Default list holds both beast races) |
| Iron boots (37), hide boots, thieves guild boots | 1 | 10/10: same boots on every foot [M] |
| Iron gauntlets (33) | 1 | 10/10 |
| Iron helmet (31+42), hide helmet | 3: Default (8 races: all but Khajiit, Argonian), Argonian, Khajiit | 10/10 with 3 meshes: iron male 786 v/1198 t for each; female human 809/1252 |
| Glass helmet, Draugr helmet | 4: Default (7), Argonian, Khajiit, Orc | 10/10, Orc own mesh |
| Circlet 01 (42) | 3: Default (8), Argonian, Khajiit: `CircletM1` 234 v, Argonian 201 v | 10/10 |
| Silver ring (36) | 1: primary Argonian, additional all other nine; no female mesh (male mesh used for both) | 10/10 |
| Mourner/farm hat (31+42) | 3: Default (excludes Argonian and Khajiit), `HatArg` 157 v, `HatKha` | 10/10 |
Races in each beast ARMA: `Argonian` ARMA lists ArgonianVampire; `Khajiit` lists KhajiitVampire. Races that share: the eight human races (Nord, Imperial, Breton, Redguard, Altmer, Bosmer, Dunmer, Orc) share the Default head items except Orc on glass and draugr helmets (and a few others: the "Orc" ARMA appears on 2 of 4 helmets sampled). Hoods/hats: 3 variants as above; the Argonian monk hood (`monkhood_arg`) reshapes the human hood. Kinds with a separate Argonian-only mesh: hats, hoods, helmets, circlets, masks, Argonian hands (`MaleHandsArgonian_1`), tails. Bodies: ONE body mesh (all 10); the skin differs by texture set: human 0xd64, beast 0x69ce3 [M]. Heads: heads are head parts per race, not armour; the eight human races share the human head topology with morph files; Argonian and Khajiit have their own heads (Argonian head 1219 v both sexes, `BSDynamicTriShape`, 2 bones) [M]. Feet and claws: the cuirass pipeline does not handle them; boots are one mesh for all (no beast-feet variant in the vanilla boot ARMAs sampled), skin feet = `MaleFeet_1.nif` [M]; Khajiit/Argonian feet clip into boots in vanilla: vanilla accepts it [I]. Tails: separate ARMA slot 40, `NakedTailArgonian`, 480 v, 9 bones; cuirass ARMAs use slot 32 only, so the tail always shows [M]; armour that hides it needs slot 40 in its bipeds [I; W: tail mods summaries].

### 2. Sex and weight [M]
Body items carry a male file and a female file, each named `_1` in the ARMA and held as `_0` and `_1` on disk, identical topology. Rigid single-bone items need no pair (ring: `_1` only; helmets, circlets: one file). Female model may be absent (ring) and the male is used. First-person: separate `1stperson` meshes for body items only; head items have none. Race and height: race height multiplies the skeleton (Nord 1.03, Altmer 1.08, Orc 1.045, Breton and Khajiit female 0.95, Argonian male 1.01) [M], so every skinned and bone-attached piece scales with it.

### 3. Character-creation variation
Head sliders morph the head (tri/egm/egt files, `UpperBodyHuman*.egt` is in every race record [M]) and not the headgear: vanilla helmets are fixed meshes, one per race group, and clip at the extremes; circlets and masks sit on the head bone [M: one bone] and ride the skeleton only. This is how Bethesda does it; we do the same [I]. Elder and child races, vampires: NPC races and vampire variants appear in the Additional Races lists (Elder, ElderVampire, XVampire, Manakin) [M]; our new ARMAs must list them or the same item will not show on them. Argonian NPCs are most seen; the player is any of ten: the Argonian mesh is the one most seen, the Default mesh is the one most worn.

### 4. Hair and horns under headgear [M]
Helmets and hoods claim biped slots [31, 42] (BOD2 flags 0x1002 helmets; hair slot 31 hides hair and Argonian horn HDPTs, which are `hair`-type parts; hairline pieces are separate Misc parts). Circlets claim slot 42 only (flags 0x1000) and leave horns, so a circlet-type crest or mask keeps the horns visible and may intersect them: the agent checks it against all 21 horn files per sex. Slots 41 (long hair) and 43 (ears) are used where the item hides them [I]. A horn cap must be slot 31 (hides horns, which is the lore: it covers the horn) or a slot-42 item that clears the horns by design.

### 5. How humans fit one piece to every race [W]
Search results: reshape per race pack ("reshapes most of the helmets so that they fit the Argonian and Khajiit ... without changing the originals"), or "3 versions of the helmet and cuirass; 1 for the Khajiit, 1 for the Argonian and 1 for all non-beast races", race-list patching in the CK for full-coverage helmets ("add the Argonian, Khajiit and their vampire variants"), duplicating NIFs and new ARMAs [Nexus 71940, 63056, forum 876000, 512396, Steam CK group thread]. Outfit Studio's reference/conform workflow credited by the author of 71940; I found no step-by-step page [W]. In Blender: Shrinkwrap (nearest surface / project) onto each beast head, Lattice for the snout; since our measurement shows the beast variants share topology with the human mesh (iron helmet 786 v three times) the cheap path is shrinkwrap then hand sculpt, and keep vertex order so weights survive [I].
Minimum variant set [I]: body items: 1 mesh set (both sexes, _0/_1) for all ten. Rigid head items: human (8 races) + Argonian + Khajiit (+ Orc where the brow/jaw clips, vanilla gives Orc its own on 2 of 4 sampled helmets). Rings, necklaces, bracelets, tail bands: 1 mesh. Gauntlets/bracers: Argonian hands are a separate mesh in naked-hands; the vanilla gauntlet ARMA is shared, plus `HideBracersArgonianAA` (RNAM Argonian; shared with Khajiit via additional list) as an exception [M].

### Every wearable in the plan: meshes, ARMAs, eye checks, cost multiplier [I unless marked]
| Wearable | Meshes and ARMAs | Checked by eye | Multiplier on one item |
|---|---|---|---|
| Mask (snout) | Default (8 human races: usually a face plate sized to a human face) + Argonian + Khajiit (3 ARMAs; Orc maybe) x male/female if the donor differs (helmets: Argonian shared, human M/F differ: 809 v vs 786) | each race head, front/side/3-4, male and female, at the extreme sliders once | 3 to 4x geometry, one texture |
| Crest, horn cap | slot 31 on Argonian; Khajiit and human variants only if those races may wear it; otherwise vanilla's answer (default mesh shows) | on all 21 horn files per sex | 1 to 3x |
| Helmet, hood | as vanilla: 3 or 4 ARMAs, 786 v topology x3 | all ten races x two sexes: 20 looks | 3 to 4x (shrinkwrap-assisted) |
| Circlet-type | Default + Argonian + Khajiit (vanilla pattern) | head bone, horns | 3x |
| Necklace, ring, bracelet | 1 ARMA, all races listed, 1 mesh (ring: male mesh for both sexes) | on body at 2 weights | 1x |
| Shield | 1 ARMA (arm attach) | not race specific | 1x |
| Kitbashed outfit | 1 ARMA, M and F, _0/_1, first-person, ground: 10 races | on human body and on Argonian body (the same mesh, different skin), 6 poses, weights 0/1, M and F | 2x for sexes, plus _1 and first-person; not races |
| Plate add-on | on the outfit (same ARMA) or as separate slot (pauldron 33 or 34) | clipping in poses | 1 to 2x |
| Boots, gauntlets | 1 ARMA for boots (10/10); gauntlets one mesh for 8 races plus Argonian hands | claws and feet clip vs human | 1x, beast variants only if clipping |
| Tail ornament | slot 40 ARMA for Argonian/Khajiit; no ARMA for humans (the item does not show: vanilla's behaviour for a tail piece) | tail bone chain, bells | 1x, Argonian and Khajiit only |
Items that cannot sensibly fit a race (snout mask on a human): vanilla gives each race its own mesh (helmets) or the default simply shows; the recommendation is the same: do not draw a human version of a snout mask; list the human races to the default (a plain plate or hood) and keep the snout piece Argonian/Khajiit, as the Argonian circlet, hat and helmets do [M].

### 6. Bodies
No CBBE/UNP/HIMBO/BodySlide/RaceMenu row in `mods/dependencies.json` [M], so vanilla bodies are the sole target; "DX Necromancer Robes - UNP" at line 6756 is the one UNP-fitted item and its fit to the vanilla body is unproven [T].

## H. The staged plan (honest odds; evidence vs inference vs trial)

Stage 0 (precondition, 1 to 3 days of agent time): Blender headless on the build VM or Windows play machine; PyNifly installed on the Windows side; the `fit` view verbs; a six-pose set (HKX import of vanilla idle, run, sneak and sit [T] or hand-keys). Proves: donor round trip (import farm clothes _0/_1, export unchanged, diff in nifdump).
Stage 1: one wrap outfit from `beggarclothes/torsom` (rags 572 v) on male and female, Argonian and human, 6 poses, both weights. Needs: the donor graft (PyNifly on Windows or the niflod extension), new TXST. Closes: the 12 trade kits with no clothing row, the commoner baseline of 126/165 persons on BM&V's outfit [audit] if three colourways on one wrap (tribe dye) are retextures only: perhaps 40 percent of "commoner dress" for 5 to 10 percent of the effort. Odds: high [T].
Stage 2: bone-plate set over it (rigid plates + Forsworn torso base). Needs: rigid plate generation, single-bone weights. Closes: rust (light bone-plate) and gold/pearl (light shell) which have no model [audit], 3 of 18 cultures. Odds: medium-high.
Stage 3: one fitted mask (Argonian + Khajiit + human variants, 3 ARMAs). Needs: shrinkwrap pass and a head-view check on all ten races. Closes: the missing masks/crests row of the audit; template for all head items. Odds: high.
Stage 4: one tribe horn or feather HDPT, rigid single-bone. Closes: "tribes differ in the heads themselves" for NPCs; zero weight painting. Odds: high (21 vanilla files are the donors).
Stage 5: one bow (donor 7 bones, shared hkx). Closes: "no BM bow T5/T6" (audit) and the bow rows; crossbow after. Odds: medium; the skinned write is the gate.
Gate for every stage: the first skinned NIF written and viewed in the engine by the owner, [T].
Not solved by this plan: the 23 trade kits all differing, body shape for players with modded bodies, heavy armour reshaping.

## Obstacles, precisely
1. Skinned write (Windows PyNifly or our nifly extension): biggest unknown [T].
2. Poses: HKX import on Linux Blender unproven; hand-keyed poses are the fallback [T].
3. Headgear multiplier of 3 to 4 per item for ten races [M].
4. FaceGen regeneration for tinted named NPCs [I].
5. Blowgun NIF not here [M].
6. Whether skin-tint shapes in an edited outfit take the Argonian skin by race [T].

## Recommendations
- Replace PROPOSAL section 8 with this staged plan and drop "Full outfits" and "Bows" from section 7's "would not do" (evidence: findings 1, 5).
- Build the donor-graft command in niflod before buying any Windows time (NifFile.hpp:373-493 offers every call).
- Make every head item a three-ARMA set from day one (Default, Argonian, Khajiit) and list vampire/Elder/Manakin additional races as vanilla does.
- Stage the blowgun archive on this machine and read it once with the probe (scratchpad `p/sp`).
- Re-run the ARMA audit over mod plugins (Shifts-Sand, AmA) before adopting: vanilla shows 10/10 coverage is by list, not by fit.

Sources: Blender manual (Data Transfer, Shrinkwrap, Weight Paint; docs.blender.org, not fetched); github.com/BadDogSkyrim/PyNifly (README, wiki Home, HKX Animation Format, Character Animations); github.com/ousnius/BodySlide-and-Outfit-Studio wiki (Automation Dialog); Nexus mods 71940, 63056, 31745, 13152894 thread, forum topics 876000 and 512396; wiki.beyondskyrim.org Rigging with Blender 2.79; ck.uesp.net User:DavidJCobb/Tutorials/Editing NIFs (found by search, not read).

Covered: vanilla clothes/armor NIFs (2,291), character assets (574), bows/crossbows/chests/doors, Skyrim.esm ARMO/ARMA/RACE/HDPT, held plugin HDPT scan, blowgun ESP, mods/dependencies.json · Skipped: Dawnguard/Dragonborn ARMA lists (Skyrim.esm only), Tropical Skyrim/BM&V mesh overrides of outfits, DP mask ARMO (EDID not found), KF import, any Blender/PyNifly run.
