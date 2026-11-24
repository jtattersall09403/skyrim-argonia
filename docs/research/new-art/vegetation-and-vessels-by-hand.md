# Vegetation and vessels made by hand (owner call #93/#94, re-plan)

Written 2026-11-24. Research only: nothing generated, bought or downloaded; no tracked file edited. The owner's steer:
an agent working by hand in Blender (commands, then renders from fixed named cameras) is the default method, and
generators supply only what they are good at. This replaces the back-of-the-queue rating that
[PROPOSAL.md](PROPOSAL.md) section 7 ("most") and [skyrim-asset-pipeline.md](skyrim-asset-pipeline.md) (trees "NOT
WORTH IT", boats "HARD") gave plants, trees, boats and wrecks. Where I measured a file, the number is mine; where I
reason, it says INFERENCE; what only a trial settles is in section 10.

**Live docs that cover this, and the one to edit.** [nature-and-vessels.md](nature-and-vessels.md) (the audit: what
is thin) is confirmed on every number I re-measured (section 1). [skyrim-asset-pipeline.md](skyrim-asset-pipeline.md)
section 5 says trees' wind needs "BSTreeNode (bone list) or BSLeafAnimNode root"; I CONFIRM that and SUPERSEDE its
rating: of the six held tree-like files I opened, five use BSLeafAnimNode (no bones), only the vanilla pine uses
BSTreeNode (section 2). So the "hybrid trunk swap onto donor bones" is not needed. The one doc to edit if the owner
takes this plan is PROPOSAL.md section 7 (move "Mangrove roots and tree ferns", "Marsh plants", "Native houseboats and
wrecks" out of "most" into a staged by-hand track); nothing new file-wise except this report.

## 0. Findings first

1. **The real obstacle to plants is not the generator; it is the writer and the texture pipeline.** Everything a
   plant needs is a handful of simple blocks, all measured below: a BSLeafAnimNode root, one to ten BSTriShapes with
   an alpha-tested two-sided shader flagged tree-anim, vertex alpha as wind weight, vertex colour as baked
   shading, a convex collision for trunks and none for reeds. nifly (which our `nifdump` and `niflod` are built
   on) already has the classes (`/home/ubuntu/.argonia/src/nifly/include/Nodes.hpp:78` BSLeafAnimNode, `:84`
   BSTreeNode; `bhk.hpp:546,560,620` convex, box, capsule). `niflod` writes only BSFadeNode static shapes today
   (`tools/newworld/niflod/niflod.cpp:1-12`). Wiring it, or swapping geometry into a donor file, is the build.
2. **Blender is not installed here** (`which blender` empty; `~/.argonia/nwvenv` has numpy 2.5, scipy, scikit-image,
   Pillow 13, no bpy, Python 3.12). PyPI's `bpy` wheels are CPython 3.11 (4.2.21 has a Linux manylinux_2_28 wheel;
   [pypi.org/project/bpy](https://pypi.org/project/bpy/4.2.21/)), so either a Blender 4.2 LTS tarball (own Python) or a
   separate 3.11 venv. Cycles on CPU renders with no display; EEVEE crashes without one
   ([manual: command-line rendering](https://docs.blender.org/manual/en/4.0/advanced/command_line/render.html),
   [bug 85336](https://projects.blender.org/blender/blender/issues/85336)).
3. **The agent's eyes already exist and are better than a Blender render for this.** The studio's agent view
   (`docs/design/agent-view.md`, `at <thing> --stand x,y,z --distance k`, id-buffer metrics `subject_seen`,
   `subject_fills`, capture faults) loads any model the resolver can find, draws alpha-tested cards as MASK at
   the NIF's threshold, and keeps tree vertex alpha out of colour (`tools/places/assets/nifglb.py:6-14,205`). A new
   NIF in a staged asset folder (the pattern of `argonia-recolours` in the profile) is therefore seen at named
   coordinates and distances without Blender's renderer. It draws no wind and no game lighting (agent-view.md:
   "Light is not judged from the viewer"), so shape, silhouette, repetition, scale and alpha are judged by the
   agent; wind amplitude and light are a donor TREE record's numbers, and the first copy is the owner's in-game check.
4. **Far-off views need almost nothing for plants and one billboard slot for each new tree.** Plants (reeds, ferns,
   lilies, herbs) get no LOD in Skyrim by rule (`tools/newworld/world/lodplan.py:30-33`; the plan's 245 "none" bases
   carry 336,768 refs). Trees get one billboard each that TexGen renders itself from the model. The hard number is the
   cap: **169 of 256 billboard slots are used** (`out/newworld/plugin/map/lodplan.json` counts, build 20261111), 87 free.
5. **Boats are easier than the proposal rated them.** Vanilla and held boats are static, built from three to seven
   shapes in shared tiling materials (the Imperial ship is 7 shapes, 12,324 triangles, five 1024 textures, 29 m
   long, no unique texture), with one MOPP mesh collision. A boat is boarded by talking to a raft-master
   (`docs/design/travel-network.md`, "The service"): no seat marker, no activator. A hull lofted by script gets a
   world-metre UV, so size cannot blur it.
6. **The held mangrove already has thin prop roots** (I drew its triangles from the file, section 2.3); what is
   missing is the tall stilt-root mangrove and variety, not the idea. One mangrove file (gkb8) is 2,380 of the
   3,223 mangrove source refs.
7. **Hist terms differ by file.** The Hist tree meshes (`histtree01-03`) are Skyfall's geometry (identical 38,018
   triangles to `skyfall/sleeping tree overhaul/ancient sleeping tree.nif`); KotM's own Hist pieces are the glands,
   roots and dead variants. Section 6 gives what each allows.

## 1. What the audit gets right, re-measured

From `newworld/sources/flora/bases.json` (534 bases, 119,447 placed source refs, the audit's visual-weight proxy):

| family | refs | share | bases | dominant model |
|---|---|---|---|---|
| fern | 31,126 | 26.1% | 16 | ManFern 13,126 (11.0%), braken 7,779, FernLarge03 5,792 |
| undergrowth | 15,574 | 13.0% | 22 | |
| reed | 8,850 | 7.4% | **1** | `vurt_reeds.nif` |
| marsh_herb | 7,559 | 6.3% | 47 | |
| lily | 4,826 | 4.0% | 11 | `gkblillipad2` 4,482 (93%) |
| bald_cypress | 4,797 | 4.0% | 12 | |
| mangrove | 3,223 | 2.7% | 5 | gkb8 2,380 (74%) |

The ground layer the eleven wet regions are seen through (fern + undergrowth + reed + lily + marsh_herb) is **56.8%** of
all source refs. Vegetation fills the screen; the fix with the biggest weight is plants, then mangroves.
`out/newworld/world.sqlite` is a 0-byte file in this checkout, so I used the committed JSON; the audit's sqlite
figures match it for these rows.

## 2. A. How a Skyrim SE tree and plant is really built (read from the files)

Method: `~/skyrim-argonia/tools/places/assets/resolve.py` (the load-order winner), a header parser for block types, `niflod
--info` for shader flags and alpha, `nifdump` arrays for vertex colour and alpha; DDS headers for size, format,
mips. Flags: shader flags 2 bit 29 = tree anim (`nifglb.py:40`); alpha flags 4844 = test, func GREATER, no blend.
Units are game units, 70 per metre. All textures are DXT (BC1/2/3), none BC7.

| file (winner) | root | shapes / triangles | leaf textures | alpha thr | tree-anim | vertex colour / alpha | collision |
|---|---|---|---|---|---|---|---|
| vanilla `landscape\trees\treepineforest01.nif` (USSEP BSA) | **BSTreeNode** (1 child, 1 + **8 bones**), BSMultiBoundNode, NiSwitchNode (2 LOD levels) | 4 / 3,269 (leaf shape 940 tris, trunk 1,201, LOD pair 632 + 496) | one atlas "BranchComp" 2048x1024 DXT3, 8 mips, normal 1024x512 | 112 | leaf shapes only | rgb baked shade (mean 0.82, sd 0.23); alpha 0..1 mean 0.43 on leaves, constant 1 on trunk | capsule list (2 capsules) + rigid body |
| TS `trees\tropical\palmtree4.nif` | **BSLeafAnimNode** | 5 / 760 (trunk 768 v / 256 t; 3 frond shapes 128+128+176 t; top 72) | one 512x512 DXT3 (`gkbpalmleaf2`) shared by all frond shapes, **header mip count 0** | 55 | **all five shapes, trunk too** | leaves: rgb baked, alpha 0 to 0.59 rising to the tips (r = 0.81 with distance from centre); trunk none | one convex-hull rigid body |
| BM&V `trees\mangrovereachtree0gkb2.nif` (also gkb3/8/9; TS has copies) | BSLeafAnimNode | 10 / 6,392: trunk 1,929 t, **7 root pieces 235-458 t each**, 2 crown shapes of 164 and 176 t (about 170 quads) | `gkbbranch1` 1024x1024 DXT5, and vanilla `TundraDriftWoodBranches01` 2048x1024 used as leaves | 70 / 45 | crown shapes only; trunk and roots rigid | trunk baked shade; crown alpha mean 0.13-0.30, r 0.4-0.5 with height | trunk MOPP + compressed mesh; **each root piece its own convex hull** (7) |
| BM&V `grass\vurt_reeds.nif` (the only reed) | BSLeafAnimNode | **1 / 52 tris (26 quads)**, 907 x 452 x 703 units | `v_reeds` 1024x2048 DXT3, 8 mips | 122 (test only, flags 4608) | yes, two-sided | rgb white (sd 0), alpha constant 1 (the whole clump moves uniformly) | **none, no BSXFlags** |
| BM&V `trees\gkblillipad2.nif` (93% of lilies) | BSLeafAnimNode | 2 / **6 tris** (a 0.9 m flat quad and a 4-tri reed bit) | `lillipads3` 1024x1024 DXT3, **mips 0**; `lillipadreed` 256x512 | 80 | yes | white / constant 1 | none |
| TS `plants\tropical\manfern.nif` (11% of all refs) | **plain NiNode** | 3 / 560 (fronds 378 t, dead fronds 72, trunk tube 110) | `frond` **256x512 DXT5**, 10 mips | 127 | **no: does not sway** | rgb baked AO (mean 0.63-0.70), alpha 1 | none |
| BM&V `plants\fernlarge03.nif` | BSFadeNode | 1 / 236 | `ferny3` 2048x1024 DXT5 | 100 | no | alpha used as vertex alpha, no colour | none |
| vanilla harvestable `plants\nirnroot01.nif` | BSFadeNode + BSXFlags + BSInvMarker | 1 / 136 | 1024x1024 DXT5 | 128 | no | rgb baked | convex hull rigid body (so it can be picked up as an item) |
| KotM `argonia\trees\hist trees\histtree01.nif` | BSLeafAnimNode | 6 / **38,018** (trunk 19,214; 9,721; crowns 982 + 5,253; vines 1,939) | Skyfall's `cluste_col` 1024x1024, `vinesb_col`; bark `CrackedBark` 2048x2048 | 128 | **none: static** | none | MOPP compressed mesh |
| KotM `hist trees\histgland01dead.nif` | BSFadeNode | 2 / 4,490 | vanilla Telvanni `telinsideblob01` 1024x1024 and Skyfall bark | n/a | no | partial | MOPP |
| KotM `greguire\swamptreetalldead01.nif` | BSLeafAnimNode | 3 / 914 (trunk 862 t, moss and vine cards 24 + 28) | `spanishmoss11` 256x512 DXT3, `rainforestvine5` 512 | 128 | moss card only | rgb dark (0.4-0.5), alpha 1 | MOPP |

What this says for the template an agent reproduces:

- **Two wind routes exist and we hold five of one, one of the other.** Skinned (BSTreeNode + 8 bones + skin data,
  the pine) is Bethesda's. Everything else we hold, palms, mangroves, reeds, lilies, dead trees, is BSLeafAnimNode with
  the tree-anim flag and vertex alpha: no skeleton. That is the route to copy. A new tree's trunk can be rigid (the
  mangrove's is) and only its cards flutter, or all shapes flutter (the palm's trunk does).
- **Wind weights are painted, not a formula.** The palm's weights rise to the tips (alpha 0 at the card root, 0.59 at
  the tip); the pine's are patchy (r = 0.06 with height); reeds and lilies are constant 1 (whole object moves). A hand
  rule, INFERENCE: alpha = smoothstep of distance along the card from its stem, times a per-card 0.7 to 1.0.
- **Vertex colour carries baked shade, not tint**: rgb standard deviation 0.2-0.3 on trees, 0 on reeds and lilies.
  Hand rule: darken toward the crown's inside and low on the card, by script.
- **Texture sizes are small**: leaves 256x512 (fern) to 2048x1024 (pine atlas), bark 512x2048 or 1024x2048 strips
  that run the trunk's length. DXT3 is as common as DXT5. Three of the held leaf textures carry **no mip chain**
  (header count 0: palm leaf, mangrove normal, lily). Alpha thresholds run from 45 to 128.
- **Budgets measured**: whole palm 760 triangles; reed clump 52; lily 6; fern 236 to 560; mangrove 6,392; pine
  3,269; the Hist tree 38,018 (an outlier, and static).
- **Collision**: trunk = one capsule or convex hull (pine, palm), roots = one convex hull each (mangrove), plants =
  none, pickable harvestables = convex hull with a rigid body and an inventory marker.

### 2.3 Seeing the held mangrove

I projected gkb8's triangles flat (script in the lane's scratchpad; not committed). Seen from the side: a short forked
trunk, a **dense low crown of about 170 large flat cards** and a tangle of fine rootlets under it that reach roughly
as far down as the trunk is long. So the held mangrove has prop roots in the sense of fine tangled ones, not arches
that lift a trunk clear of the water. Its cards are huge and few; its repetition across 3,223 refs rests on four
files. UNVERIFIED in game; the owner judges look.

## 3. B. Foliage cards by hand

**What is built.** An atlas image plus card geometry plus two vertex channels. Everything below is scriptable in
Blender's Python and numpy; no step needs a 3D generator.

1. **Atlas.** One sheet per plant family, 2048x1024 or 1024x2048 (the sizes the held files use), a grid of frond,
   blade or leaf cells ([Valve's vegetation page](https://developer.valvesoftware.com/wiki/Vegetation) describes the
   same: a grid of evenly spaced sections). Sources, easiest first: (a) **procedural by script** (numpy/PIL: a
   blade or frond with a midrib, a tint gradient, noise; no AI, fully reproducible, matches the held plants' low
   detail); (b) a Fal image of one frond or reed on a plain background, keyed out to alpha (Fal image models do not
   return true alpha; INFERENCE, test once); (c) cut from photographs we generate. Cell padding of 2 to the power of
   the number of mips you want kept clean (32 px for five mips): neighbours must not bleed into a card
   ([three.js thread on atlas bleed](https://discourse.threejs.org/t/uv-padding-question/9986)).
2. **Edge colour (the halo fix).** For every transparent pixel, fill RGB with the nearest opaque pixel's colour
   (`scipy.ndimage.distance_transform_edt(..., return_indices=True)`, already on the VM) before compression, so the
   filtered edge is leaf-coloured, not black or white. Pre-multiplied alpha is not what Skyrim samples (alpha test, not
   blend), so straight alpha with dilated colour is the rule; texconv's `-pmalpha` is for the other route and
   is not used.
3. **Alpha-test thresholds and mips.** Skyrim tests alpha at a per-file threshold (45 to 128 held). Mip alpha
   shrinks and cards thin out with distance unless coverage is preserved: texconv `-keepcoverage <ref>` "preserves
   alpha coverage in generated mipmaps for the alpha test reference value"
   ([texconv wiki](https://github.com/microsoft/DirectXTex/wiki/Texconv)). Use ref = threshold/255 and a full mip
   chain, which three held leaf textures lack. Use BC3 (DXT5) where the edge is soft, since BC2's 4-bit alpha bands.
   Pillow writes BC1/BC3 only and single-mip in my earlier test; **a Linux texconv build is needed** (supported;
   `skyrim-asset-pipeline.md` finding 5). Alpha-to-coverage (MSAA) is a render option the game does not expose per
   file; the ways to soften edges are the threshold and the mips.
4. **Cards in Blender.** Each card is a grid of 1 x 3 to 2 x 5 quads (three to five segments along the frond),
   cut to the frond's outline by moving vertices, so the alpha does less work and overdraw falls (the held reed's 26
   quads for a 13 m patch are crude). Bend each card along its spine by rotating segments, droop tips with a
   gravity curve, fan three to nine cards from a stem point (ferns, crowns) or cross two to three (reeds, sedge);
   clumps of 12 to 30 cards give 100 to 400 triangles, matching the held 52 to 560. Hanging moss and liana curtains are
   vertical strips of 8 to 16 quads with the gentlest tip weights.
5. **Soft light on clumps: edit normals to a dome.** Blender's *Normal Edit* modifier (target object or radial) and
   *Data Transfer* from a low sphere or ellipsoid ([manual](https://docs.blender.org/manual/en/latest/modeling/modifiers/normals/normal_edit.html))
   point every card's normals outward from the clump's centre; this is the standard trick
   ([Polycount thread](https://polycount.com/discussion/comment/2720547), [Unreal forum on card normals](https://forums.unrealengine.com/t/any-tips-for-hiding-sharp-corners-in-leaf-planes/650483),
   [SpeedTree card generator](https://docs.unity3d.com/speedtree-modeler/manual/card-generator-properties.html)).
   Skyrim stores per-vertex normals and tangents (all dumped shapes report both), so the edit survives; the
   writer must recompute tangents after it.
6. **Wind and shading channels** by script: vertex alpha = distance-along-card weight (section 2 hand rule); vertex
   rgb = baked shade; shader flags 1 = `0x82400308` (the palm's value) and flags 2 with bit 29 (tree anim) and the
   two-sided bit; the alpha property copied from a donor (4844, thr from the atlas). Copying the donor's whole shader
   block is safer than building one.
7. **Density and budgets (measured basis in section 2).** Reed clump 80 to 200 triangles in a set of 6 to 10
   distinct clumps from one atlas; fern 150 to 400; tree-fern crown 300 to 600; mangrove crown 300 to 900 over 40 to
   80 smaller cards in place of 170 big ones. Overdraw of alpha-tested layers is the real cost on 8,850 reed refs;
   INFERENCE, a trial measures it.
8. **How the agent judges by eye** (agent-view verbs, all named, nothing flown): `look <place> at <clump>
   --stand x,y,z --distance k` at player eye height (about 160 units over the ground) at 2 m, 10 m and 40 m, once with
   the water behind (low sun side) and once against sky (`--stand` low, `--eye`); a **ring test**: 12 copies at random
   yaw and scale on a 6 m circle by `place edit add` in a scratch place, then `survey` for repetition; the id-buffer
   metrics catch a card filling the lens or a capture inside the subject. A flat 90-degree-crossed pair reads as
   two sheets at 2 m: the check is whether any single card edge is readable.

Plants to build, with a one-line method each: **reed** (tall blades, 6 clump variants from one atlas), **cattail**
(blades plus a brown seed head as a small solid cylinder, 3 variants), **sedge** (low arching blades, wide fans),
**rice / saltrice paddy** (regular seedling rows as fans on a flat sheet; saltrice itself is held and unplaced),
**lily mat** (the 6-triangle lily is already the cheapest thing in the game: draw 8 variants with flowers and
overlapping pads from one 1024 atlas, mips included), **water hyacinth** (EXTRAPOLATION: not in the lore; a rosette
of 8 cards, only if the owner wants a pest plant), **hanging moss and liana curtains** (vertical strips), **fern and
tree-fern crowns** (9 to 14 fronds fanned on a 110-triangle trunk tube like ManFern's `Tri Tube`), **mangrove crowns**
(section 4).

## 4. C. Whole trees by hand

**Trunk and roots.** Three ways, cheapest first. (1) Script them: a trunk is a tapered cylinder along a Bezier
curve with a bevel (Blender curve to mesh, 8 to 10 sides, 6 to 12 rings); mangrove prop roots are 8 to 16 such
curves arching from the trunk at 1 to 3 m up to the ground, each 6 sides by 8 rings (about 100 triangles), about 1,000
triangles for a stilt mangrove's whole root skirt; knees and buttresses are cones with noise displacement. (2)
Blender's **Sapling Tree Gen**: GPL-2.0-or-later, v0.3.6, no longer bundled since 4.1, on
[extensions.blender.org](https://extensions.blender.org/add-ons/sapling-tree-gen/); the
[manual](https://docs.blender.org/manual/en/4.1/addons/add_curve/sapling.html) says it can export its settings as a
preset; its reviews report it **broken on Blender 5.0.1 and 5.1** and its animation failing on 4.4 and 4.5, so pin
4.2 LTS if it is used. (3) **Modular Tree**: GPL-3.0-or-later add-on (core MIT), Blender 4.3+, maintained fork
[GoodPie/modular_tree](https://github.com/GoodPie/modular_tree), original by Maxime Herpin
([extension page](https://extensions.blender.org/add-ons/modular-tree/)); whether either runs headless from
`blender -b --python` is not documented, and a trial settles it (section 10). A generator (Tripo/Hunyuan) is useful for
one thing: a *solid, gnarled* trunk or buttress mass as a reference or a base mesh, not the crown.

**Bark as a tiling shared material, no texel-density limit.** Map U around the trunk (2 to 3 repeats) and V in
**metres along the length** (one bark tile per 1.5 to 2 m); a 2048 bark then gives the same density on a 3 m or a 30 m
trunk. That is how the held bark strips (512x2048, 1024x2048) work. Reuse paths already in the profile (no new art):
`gkbbark` 512x1024, KotM's `weepingwillowbark01` 2048x2048 (a `_resourcepack` path; check whose), `TundraDriftWoodBark01`.
Roots take the same texture at the same metre scale, so no seam shows between trunk and roots.

**Crown cards in layers.** Three layers by hand: an inner dark layer of large cards (shade 0.5), a middle layer, an
outer layer of small bright cards; 40 to 120 cards per crown at 2 triangles each, plus hanging strips. Place in
rings by script, then fix by eye from the three distances. The held mangrove is 170 cards; the aim is more, smaller
cards in the same budget so edges read as leaves.

**Wind.** Use the BSLeafAnimNode route (section 2): trunk and roots rigid, crown cards flagged and weighted. Copying a
donor's whole shape-property block (flags 1 `0x82400309`, flags 2 `0x22008031` for card shapes; the mangrove's values)
is the safe path. The TREE record's flexibility and amplitude numbers are copied from the donor TREE record (the
[Nexus thread](https://forums.nexusmods.com/topic/10905408-some-way-to-make-a-custom-tree-sway-in-the-wind) confirms
the root-node-plus-flag recipe; the CK page, ck.uesp.net/wiki/Tree, returned 403 here, so field names are from the
thread and the CK). A TREE record copied from the donor (TS `TreeCoastPalm01` is an example in our lodplan) with the
model path changed is the whole record job (`docs/design/ecology.md`; harvestables are FLOR records copied the same way).
Our trees are placed as TREE bases or STATs with "Has Tree LOD".

**Collision.** A tree needs only one capsule or convex hull on the trunk (pine and palm do exactly that) plus a
convex hull per root arch (mangrove does 7): PyNifly exports capsule, box and convex hull from Blender objects named
or typed for it (`skyrim-asset-pipeline.md` finding 4); nifly can write them directly (`bhk.hpp:546,560,620`). Prefer
the donor route: swap geometry into a donor NIF and keep its collision node, resizing the shape to the trunk.

**Species plan.**

| species | what makes it | budget | gap it fills (measured) |
|---|---|---|---|
| **Stilt-root mangrove** (3 variants + a seedling stand of 5 small ones) | scripted trunk + 10 to 14 arched root curves + 60 small crown cards; BSLeafAnimNode; one capsule + convex per big root | 1,500 to 2,500 t | mangrove 2.7% of refs, 74% one file; Kotherra is 19% mangrove |
| **Tree fern and cycad** | trunk tube (as ManFern) + fanned 10 to 14 fronds; cycad: stout scaled trunk, stiffer fronds | 300 to 600 t | fern family 26.1%, 3 meshes carry 22% of all refs; no trunked fern |
| **Swamp-cypress variants** | held KotM trunks are fine (12 held, 5 giant knees unplaced, nature audit 2.3); add leaning, buttressed, hollow (a boolean-cut trunk) with the held bark | 1,000 to 2,500 | cypress 4.0%: two to three variants beyond the held 12 |
| **Strangler / aerial-root tree** | trunk with a lattice of root curves wrapping it; LORE: not named (nature audit 2.2: only creatures are "stranglers"), so EXTRAPOLATION, only if the owner wants | 2,000 | none in lore |
| **Drowned and dead trees** | held: 13 swamp_dead + 34 logs; build snags by breaking a trunk (boolean + noise) and half-sinking it | 500 to 1,200 | served; low priority |
| **Giant fungus** | stalk + cap lathe, gill cards under the cap; vanilla Dragonborn mushroom trees exist unplaced (nature audit 2.2) so try those first | 400 to 900 | "giant_mushroom" family holds only small ones |
| **Sick and dying Hist** | section 6 | n/a | owner rulings (docs/owner-rulings.md around 889-912): endings show trees dying |

## 5. D. Far-off views

From `docs/design/lod.md` and `.claude/skills/world-lod/SKILL.md` (lines 37, 82, 86, 90) and `tools/newworld/world/lodplan.py:1-33`:

- **Plants (reed, cattail, sedge, fern, lily, hanging moss, herbs): no LOD**, by Skyrim's rule for things under 512 units
  and ground cover; nothing to make. They end with the loaded cells and the fade-out distance, as vanilla's do.
- **Each new tree: one billboard, made by TexGen from the model itself.** TexGen only makes a billboard for a base whose
  bounds reach magnitude 512 and height 256 and whose model path contains "tree"; our override file
  `DynDOLOD_SSE_TexGen_Billboards_argonianewworldesm.txt` forces listed bases (lodplan.py:7-13), so a new tree is listed
  there and, if a STAT, carries "Has Tree LOD". The billboard is the front view, drawn on two crossed double-sided
  planes, no normals, upright only ([DynDOLOD Tree LOD](https://dyndolod.info/Help/Tree-LOD)). So we do **not** have to render
  billboards from Blender; the pipeline does it from our model and our leaf texture. If the result is poor, the
  documented override is a DDS and TXT pair in `Textures\Terrain\LODGen\` (same page), which a Blender or studio
  render can supply.
- **The cap is the obstacle:** at most 256 billboards in the world's tree atlas; the plan of 2026-11-11 uses 169
  (`lodplan.json` counts: tree 169 bases, 136,064 refs). 87 slots remain. Each new species needs one slot per mesh
  variant, so a stilt mangrove with 3 variants, a tree fern with 3 and two cypress is about 10. Beyond the cap,
  "ultra tree LOD" (billboard in object LOD, no cap, 3D or hybrid LOD models) is DynDOLOD's own answer (same page) and
  would be a new block for us. BM&V's mangroves also ship `*_lod_flat.nif` (8 vertices, 4 triangles, on
  `TamrielTreeLOD`) that our `own` mechanism (44 bases) draws as object LOD.
- **Object LOD for big hand-made statics (boats, wrecks, mangrove root masses):** large statics over 512 units take
  object LOD from the full model at LOD4 when the block budget allows (9,327 triangles per LOD4 block), or a derived
  LOD model (`lodmodels.py` quadric collapse, vertices taken from the source, bounds preserved) with a target; a rule line names
  it. Boats are one or a few hulls per stop, so they fit; a thin-rooted mangrove collapses badly (the doc says
  where refs are dense "no faithful shape exists"), so use the billboard for trees and the root mass as part of it.
- **What a new base reaches:** "A new or changed tree base, or the billboard plan" reruns `texgen`, `dyndolod`, `collect`
  (about 22 minutes; changes.md and world-lod table). A new static base reruns `texgen` too. Textures that are
  shared vanilla paths are already in TexGen's object atlas; new ones are included automatically.

## 6. Hist: whose models, and what a sick one can be

| piece | whose (measured) | terms |
|---|---|---|
| `histtree01`, `02a-c`, `03` geometry | **Skyfall's Sleeping Tree Overhaul** (same 38,018 triangles and per-shape counts as `skyfall/sleeping tree overhaul/ancient sleeping tree.nif`; its textures `cluste_col`, `vinesb_col`, `CrackedBark`) | register `mods/sourcing-register.json:813`, `dependencies.json` row `sleeping-hist-tree`: "none stated", `permission_ask: true`; the author's one grant is a LE backport; `ai_clause` "not stated: ask the author" |
| glands, roots, vines, dead glands (`histgland*`, `hist_root*`, `deadroot*`) | **King of the Murkmire** (the dead gland uses a vanilla DLC2 Telvanni texture and Skyfall's bark) | KotM page: free for use "if they do not make use of AI"; the owner's own permission is on record for our use (PROPOSAL section 9); PROPOSAL says never use its files as donors, references or retexture bases |

What a hand-made sick Hist can be without touching either mod's files:

1. **A state by alternate textures only (no mesh edit, cheapest).** `nifglb.swapped` already models record-level
   alternate texture sets; a STAT base for the sick Hist points the same model at grey, dry bark and leaf textures. Make
   the textures from **vanilla** bark (not a grade of Skyfall's `CrackedBark`, which would be a derivative image)
   and sap-streak decals of our own. Mesh unchanged, so nobody's geometry is edited. Whether a record
   pointing at their model and our textures needs Skyfall's permission is a question for the owner (the row already
   asks).
2. **A bare-branch variant** = the same NIF without its three leaf and vine shapes (`cedartree1:1,:2,:5`): an edit of
   Skyfall's file, so it needs Skyfall's answer.
3. **A Hist of our own** (recommended if the answer is no): a hand-built tree from the scripted trunk of section 4 (a
   broad buttressed trunk, 8 to 12 root arches, a crown of weeping strips), the same in four states: *healthy* (full
   crown, bright), *sick* (half the cards, drooping tips = weights at 0, grey bark), *dying* (bare branches, sap-weeping
   bark by a second shape of stain decal cards hugging the trunk), *dead* (the held dead gland as reference only). One
   skeleton, four card sets, shared bark. Built wholly from our scripts and shared textures: no third-party file.
   That is also the only version that avoids both the AI clause and the permission row.

## 7. E. Regional distinctiveness by planting

What the data already has (`newworld/sources/identity/regions.json`, per region: haze colour, brightness, ground family,
water look, signature; `newworld/sources/flora/regions.json`: habitat shares, family `boost` multipliers, and "bases
inside a family are chosen per region (a deterministic, region-seeded subset)"). The eleven near-identical wet regions
differ already in light and water but **not in plants**:

| region | haze rgb, brightness | water | ground | what the lore note says (region_note) | signature planting to add |
|---|---|---|---|---|---|
| Ultherus Swamp | 118,140,105 / 0.8 | black | red | "a maze of cattails, reed and black water"; lilies; dragon's-tongue | **cattail maze** (new cattail set boosted 1.6 and 40% of the reed habitat) |
| Lake Ulaish | 175,185,190 / 1.1 | pale silt-grey | blue | reed beds, lily; water-bird eggs | **wide reed beds + lily mats** (pale tall reed variant) |
| Barsaebica | 150,165,160 / 0.95 | black tidal | white | fen and sedge | **sedge fen** (the new sedge set; low, wide) |
| Nha Enasa | 135,140,150 / 0.8 | black river | yellow | reed banks, dragonflies | **bundled tall reed banks** with cypress knees |
| Banujha Basin | 185,145,90 / 0.9 | tea-brown | rust | reed, lily, gar eggs | **lily mats on tea water**, short reed |
| Nushara Bayou | 165,175,130 / 0.85 | tea-brown sheets | white | **saltrice marsh** | **saltrice (held, unplaced)** + pollen |
| Althii Archipelago | 190,195,150 / 1.1 | turquoise | orange | **paddy and mangrove** | **rice paddy cards + stilt mangrove** |
| Kotherra Mangroves | 120,110,70 / 0.75 | black | red-ochre | black water between the roots | **stilt-root mangrove thicket** (arches, seedling stands) |
| Tulmek Washes | 150,150,138 / 0.75 | brown standing | yellow | cypress and mangrove mix | cypress variants + tree fern edges |
| Okuwun Rahei | 205,150,120 / 1.05 | silt-brown | red-ochre | clay mounds, hist-frog spawn | low scrub + mound statics |
| Valley of Storms | 115,110,145 / 0.8 | brown over causeways | violet | flooded causeways, wisps | drowned dead trees + moss curtains |

All of this is INFERENCE built on cited region notes; each pairing is a small lore call the lane may make and report, not an
owner call. Colour grade per region is **not** a plant property today (haze, light, ground family are
atmosphere data); a leaf recolour (`newworld/sources/flora/recolour.json`) is per **texture path**, so it is
global. A region-tinted plant therefore needs a second texture path (a variant file), which a new hand-made
clump set gives for free (a pale-reed variant and a dark-reed variant are two atlases or two atlas cells).

**What the world-build rules say** (`.claude/skills/world-build/changes.md:57-76`, `SKILL.md` section 5 and line 195): a flora
set change (`newworld/sources/flora/`) runs `db`, then `place`, `navmesh`, `mist`, `map`, `esm`, `upload` and LOD; **a
world rebuild runs only when the owner has asked**, and the province's ground is never regenerated. New bases and new
boosts therefore reach the undrafted province only at the next rebuild the owner asks for. Two routes do not wait:
(a) drafted places take dressing by narrow change; (b) `place edit swap` changes one placed thing, or every placed thing of a
base, in `newworld/sources/placed_edits.jsonl` and runs only `edits`, `navmesh` (cells in reach), `map`, `esm`,
`readback`, `upload`, with `dyndolod` and `texgen` for a base new to the world. A swap of the 8,850 `vurt_reeds` refs to
the new reed bases is route (b). Whether running `rebuild.sh` for edits counts as "a world rebuild" under the owner-asks
rule is the owner's reading; I would ask it as one plain call.

## 8. F. Boats, ships and wrecks by hand

**What exists** (measured): BM&V `architecture\boats\rowboat01.nif` 3 shapes 3,634 t, 195 x 544 x 107 units
(2.8 x 7.8 x 1.5 m), textures `shipwoodside01` and `shipwood01` 1024², `shiprope01` 1024² and a MOPP mesh collision;
KotM's `shiprowboat01` 5,484 t; BM&V `imperialship01base` 7 shapes 12,324 t, 2,017 units (29 m) long with five tiling
1024 materials and one MOPP; Baan Malur `shipwreck.nif` 6,303 t in 11 pieces; KotM `wooddockbroken01` 1,802 t. There is
no native craft (nature audit 2.4). Held tiling materials a native kit can reuse by path (loose, from the resolver):
`dungeons\ships\shipwood01`, `shipwoodside01`, `shiprope01`, `architecture\wicker01`, Dagon Fel `thatchroof01`,
`wicker`, `rope01`, `netwicker`, Insanity `roofthatched`, `rope01`. (Whose and under which terms: read each mod's
row before a dependency is added.)

**How a player boards today** (`docs/design/travel-network.md`, "The service"): boat travel is a service line of a
raft-master or sea-coaster NPC; it takes the fare and calls `Game.FastTravel`, landing at the destination's arrival
point. The boat is scenery. **No seat marker and no activator is needed.** A seat marker (a `BSFurnitureMarkerNode`
that PyNifly exports) is optional polish if the owner wants the player to sit on the raft during the line.

**Native craft kit** (all statics, moored by the place skills at the 31 boat stops: 22 raft-masters, 9 sea-coasters):

| craft | by hand | tris | collision |
|---|---|---|---|
| dugout canoe (the 22 raft stops' commonest craft) | hollowed log: a 7 m tapered cylinder with a boolean-carved trough, thwart sticks, a paddle; bark outside, adzed wood inside | 700 to 1,500 | one box for the hull rim + boxes for the floor |
| bundled-reed raft | 9 to 15 parallel tapered reed bundles of 8 sides, lashed with rope torus rings every 0.5 m, a poling rest | 1,200 to 2,000 | one slab box for the deck |
| twin-hull platform canoe | two dugouts, a lashed plank platform, a mast stub; lore (`material-culture.md:84-128`) | 2,500 to 4,000 | slab + two hull boxes |
| houseboat with a reed cabin | a platform raft + a hut of woven wall panels and a thatched roof (shared thatch) | 3,000 to 6,000 | floor slab + wall boxes + MOPP optional |
| poled ferry raft with rail | plank deck, post rail, a bow rope, rope loops | 1,500 to 2,500 | deck slab + rail boxes |

Method that avoids blur: **loft the hull by script** (10 to 14 cross-section curves joined by Blender's surface or
`bmesh` skin; a dugout from one tapered cylinder), then UV by **world metres** (U along the length in metres, V around
the section in metres) with a 1 m tile of the shared plank or bark texture. A 2048 plank at 1 m tile is 2,048 px/m on
a 3 m beam and still 2,048 px/m on a 29 m hull. Separate shapes per material (hull, planks, rope, reed) as the Imperial
ship does, so each shape has one tiling texture and one shader.
Walkable decks: boxes (`bhkBoxShape`, static layer) under the visible deck, 3 to 8 per craft; a ramp-free deck 20 to
40 cm over the water is the boarding height. Vanilla puts the MOPP mesh collision on the hull; for hand-made craft
boxes are cheaper and robust (INFERENCE).

**Wrecks by hand (breaking a hull).** Build the hull as separate **planks** (40 to 120 strips each side) and **ribs**
(8 to 14), so the break is a deletion, not a sculpt: delete a random 20 to 40% of planks over a 2 to 4 m patch, break each
rib to a random length with a jagged end (a cut by plane plus noise), tilt the whole hull 6 to 22 degrees on its axis
(list), sink it 40 to 70% below the water plane (the water is a plane; the placement sets Z), add weed (reuse the
section 3 hanging-strip cards), barnacle and rust as a second texture layer or alpha decal cards, and scatter
planks and a broken mast as statics. 3,000 to 8,000 triangles, so a wreck fits the 9,327-triangle LOD4 block.
The four Nordic Icerunner wrecks (nature audit) and the Ink Lagoon ones (unlooked) are the replacement target.

## 9. G. Tools worth having

| tool | what for | headless on Linux | licence / cost |
|---|---|---|---|
| **Blender 4.2 LTS** (tarball, or `bpy` 4.2.21 wheel in a 3.11 venv) | meshes, curves, bmesh, modifiers, Normal Edit, Data Transfer, UV pack, Cycles CPU turntables | yes (`-b --python`; EEVEE no) | GPL, free |
| Blender **geometry nodes** (built in) | scatter, clump variation, root skirts; node groups built from Python | yes | GPL, free |
| **Sapling Tree Gen** 0.3.6 | trunk and branches reference | probably (a Python operator; untested); broken on 5.0.1 and 5.1 per reviews | GPL-2.0+, free |
| **Modular Tree** (GoodPie fork) | trunk and branches, node-based | unknown | GPL-3.0+ add-on, MIT core, free |
| **PyNifly** | Blender to NIF incl. collision, furniture markers | no: Windows DLL; Linux build plausible, unproven (asset pipeline finding 3) | GPL, free |
| **nifly via niflod** (ours) | write NIF with BSLeafAnimNode, shapes, collision; swap geometry into a donor | yes, builds here | MIT (nifly), ours |
| **numpy + scipy + scikit-image + Pillow** (on the VM) | atlas procedural drawing, edge-colour dilation, packing, normal/spec maps | yes | free, present |
| **texconv** (DirectXTex) | BC1/2/3 DDS with a full mip chain and `-keepcoverage` | Linux build supported; not built here | MIT, free |
| rectpack (Python) or Blender `uv.pack_islands` | pack frond cells | yes | MIT/GPL, free |
| **BlenderMCP** | an interactive agent session in a live Blender | needs a GUI Blender | MIT; not needed for scripted work |

Not found worth having: a paid foliage pack (Botaniq-class) or SpeedTree; the plan needs neither.

## 10. H. The plan, staged

**Stage 0, building blocks (once; the first proof of "hands").** Install Blender 4.2 on the build VM; a small
`lib` of scripts: `cards.py` (grid card, bend, fan, cross, droop), `weights.py` (the section 2 rules), `atlas.py`
(procedural cell drawing, edge-colour dilation, packing), `loft.py` (curve to tube, hull), `uvm.py` (world-metre
UV); a Linux texconv; `niflod` extended with a **donor-geometry swap** (take a donor NIF, replace shapes' vertices,
UV, colour and triangles via nifly, keep root, shader blocks, collision and flags) as the first writer, then a
from-scratch BSLeafAnimNode writer. A scratch staged asset folder in the profile so the studio sees new NIFs. Proof:
a donor round trip (read vurt_reeds, write it back, `nifdump` and `niflod --info` agree; studio shows the same).

**Stage 1, one reed clump set (the proof stage).** 6 reed variants, 3 cattails, 3 sedges from one 2048x1024 atlas, built
in the section 3 order, as the donor-shelled `vurt_reeds` swap. Seen at 2, 10 and 40 m in the studio, with the ring
test, then **from a boat** (a rowboat placed on the water, `--stand` on its deck) and at the water's edge against sky.
In game: an owner check at one marsh. LOD: none needed (plants). Gain (measured basis): the reed family is **7.4% of source
refs on one model**; 11 regions read it (nature audit table).

**Stage 2, one stilt-root mangrove with seedling stand, with LOD.** Scripted trunk and arched roots, crown of 60 small
cards, collision (capsule + convex per big root), a TREE record copied from the mangrove donor, a billboard slot (one of the
87), seen at three distances and from a boat, then through TexGen/DynDOLOD on the small world (`rebuild.sh small`, the
skill's selftest) to prove it does not pop. Gain: mangrove is 2.7% of refs, 74% one file, 19% of Kotherra.

**Stage 3, ferns and lilies.** Tree fern with trunk (3 variants), sword and stag fern clumps, lily mats (8 variants).
Fern family 26.1% of refs, three models carry 22%; lily 4.0%, one model 93% of it. Highest screen weight per hour of
work: the fern is already 560 triangles and a 256x512 texture with no wind; ours can sway.

**Stage 4, planting.** Flora tables: new families (cattail, sedge, rice, stilt mangrove), region boosts per section 7,
`place edit swap` of the monocultures; one owner-asked rebuild reaches the rest.

**Stage 5, one dugout** (the proposal's boat pilot, by hand): loft, carve, UV by metre, deck boxes, moored at one raft
stop, boarded by the existing raft-master line; seen from the bank and on the deck. Then the reed raft, the platform
canoe, the ferry raft; at 22 raft stops, the commonest craft.

**Stage 6, wrecks and the houseboat; sick Hist states and cypress variants.** Wrecks from the plank-built hull; the Hist
by alternate textures first, a Hist of our own only on the owner's word about Skyfall and KotM.

What each stage gives the province, in the audit's own shares: Stage 1 retires the single reed model (7.4%); Stage 2
the thin mangrove coast; Stage 3 the 26.1% fern layer and 4.0% lily layer; with Stage 4 the ground layer that is
56.8% of source refs stops being one kit in eleven regions.

### Evidence and inference

Well evidenced (a file, command or page): every table value in section 2; the shares in section 1; the 169 of
256 billboard slots; the nifly classes; Blender's licence and Cycles-only headless rendering; texconv `-keepcoverage`;
Sapling's and Modular Tree's licences and compatibility reports; vanilla and held boats being static and boarded
by dialogue; the Hist tree's identity with Skyfall's file; the regional data columns.

INFERENCE (reasoned, not measured): the wind-weight rule; the world-metre UV making hulls crisp (sound texel
arithmetic, unseen in game); deck boxes being enough; the triangle budgets for new species; Fal giving usable keyed
fronds; that dome normals survive our writer with right tangents; that the studio's views suffice to judge shape
before the owner sees it in game; the regional pairings.

**Only a trial settles:** (1) niflod/donor-swap output loads and sways in game; (2) Blender 4.2 on the VM runs a
bpy script and Sapling or Modular Tree headless; (3) a texconv Linux build writes a coverage-preserving DXT5 chain
that reads right in game; (4) overdraw cost of dense alpha cards at 8,850+ placements on the play machine; (5) the
studio ring test predicting what the owner sees; (6) TexGen's billboard of our crown looks right; (7) agent hours per
asset, which I cannot estimate; (8) the owner's reading of the "world rebuild" rule for `edits`; (9) Skyfall's and KotM's
answers.

## Recommendations

1. **Proposal edit:** move marsh plants, mangrove roots, tree ferns, native craft and wrecks from "most" into this staged
   by-hand track and make Stage 0 plus Stage 1 the next pilot beside the five-model one; evidence: the reed is one
   26-quad model on 7.4% of refs (section 2) and every block it needs is held.
2. **Ask the owner two plain calls:** whether `place edit swap` of a whole base is a world rebuild (section 7); and whether
   to ask Skyfall about the Hist tree (row `sleeping-hist-tree`, `permission_ask: true`) and KotM's author about AI-made
   plants beside its huts, or build our own Hist.
3. **Build the Linux texconv and a Blender 4.2 install in the same stage as the writer**, since all of A to H wait on
   them; `skyrim-asset-pipeline.md` finding 2 shows neither is present.
4. **Reserve the 87 free billboard slots** for trees we make (about 10), before adding any more held trees.

Sources: [Blender command-line rendering](https://docs.blender.org/manual/en/4.0/advanced/command_line/render.html);
[bpy on PyPI](https://pypi.org/project/bpy/4.2.21/); [Sapling manual](https://docs.blender.org/manual/en/4.1/addons/add_curve/sapling.html);
[Sapling extension](https://extensions.blender.org/add-ons/sapling-tree-gen/);
[Modular Tree extension](https://extensions.blender.org/add-ons/modular-tree/);
[Normal Edit modifier](https://docs.blender.org/manual/en/latest/modeling/modifiers/normals/normal_edit.html);
[texconv](https://github.com/microsoft/DirectXTex/wiki/Texconv);
[DynDOLOD Tree LOD](https://dyndolod.info/Help/Tree-LOD);
[Nexus: tree sway](https://forums.nexusmods.com/topic/10905408-some-way-to-make-a-custom-tree-sway-in-the-wind);
[Nexus: custom trees](https://forums.nexusmods.com/topic/5427787-need-a-little-help-with-custom-trees);
[Valve vegetation](https://developer.valvesoftware.com/wiki/Vegetation);
[Polycount foliage normals](https://polycount.com/discussion/comment/2720547);
[SpeedTree card generator](https://docs.unity3d.com/speedtree-modeler/manual/card-generator-properties.html).

Covered: PROPOSAL.md, nature-and-vessels.md, skyrim-asset-pipeline.md, agent-view.md, lod.md, world-lod and world-build skills (changes.md), travel-network.md, flora and identity JSON, lodplan.json, 20 game and mod NIFs · Skipped: Blender trial (not installed, nothing downloaded), ck.uesp.net Tree page (403), in-game look of any model (owner's), Modular Tree headless behaviour (no docs found).
