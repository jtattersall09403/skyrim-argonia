# New art for Argonia: what we could do, and what I recommend

Written 2026-11-24 for owner call #93; the choice is owner call #94. Nothing has been created or bought. This
page is the proposal; the seven research reports behind it sit beside it in this folder:

- [tooling.md](tooling.md): the tools, prices and policies for making 3D models with an agent.
- [skyrim-asset-pipeline.md](skyrim-asset-pipeline.md): what it takes to turn a generated model into a working Skyrim asset.
- [visual-consistency.md](visual-consistency.md): how sets of AI-made assets are kept looking like one game.
- [gear-and-clothing.md](gear-and-clothing.md): weapons, armour and clothing.
- [places-and-pieces.md](places-and-pieces.md): places against their source places, and the most Skyrim-looking pieces.
- [identity-vs-lore.md](identity-vs-lore.md): every region, culture and faction against the lore.
- [nature-and-vessels.md](nature-and-vessels.md): trees, plants, boats, ships and wrecks.

## 1. The short answer

**I recommend relaxing the rule, narrowly, in three steps, and stopping after any step that disappoints.**

1. **Do the "least" option now.** Most of the cheapest gains need no new art at all: models we hold and do not
   use, and mods on Nexus we had not found. The rest of that option needs only flat images on banner models
   that already exist.
2. **Run a five-model pilot** (about $15 of Fal fees), taken all the way into the game for you to look at. It
   proves two things nobody seems to have published: the route from a generated model to a Skyrim model file,
   and that our way of keeping the models consistent actually works.
3. **If the pilot looks right in game, do the "more" option**: about 49 small solid models, every one made by
   your "acts like an existing thing" route. Treat the "most" list as a menu to pick from afterwards, never as a block.

The reason is what the audits found. The province is not short of models in number. It is short in a few
specific, very visible spots, and after a proper search of Nexus the spots that remain are mostly small, solid
things:

- The commonest weapons in Black Marsh are Skyrim's own iron and steel swords under a new name.
- Six tribes' signature weapons (pike, halberd, quarterstaff, rapier, whip, claw) are generic medieval models.
- No dugout or raft exists, though 22 of the 31 boat stops are worked by raft-masters.
- The lore's best repeatable object, the carved grave-stake, was not found anywhere.
- No tribe has a standard and no story line has a sign.

The largest gap is still **what people wear**. The proper search found more Argonian clothing and armour than I
first reported, which helps; making skinned clothing ourselves stays out of reach (section 7).

## 2. What the audits found

### Where we are thin (measured)

| Area | What we hold | Where it is thin |
|---|---|---|
| Weapons and armour | 767 records on 638 distinct models | The 11 lowest-tier "bog iron" weapons are vanilla iron and steel models. Two heavy sets use Nordic plate and Nordic carved models. Every Argonian village guard wears one set (Stormhold Warrior); every town watch wears one other. Three tribes are specified in light shell or bone-plate armour we do not hold. Six tribes' signature weapon types have no Black Marsh model. |
| Clothing | About 30 non-armour clothing models in all | 12 of the 23 trade kits have no clothing row. In the six stocked places 126 of 165 people have no authored clothing, and half of the rest wear vanilla farm, monk or beggar clothes. The jewellery is 32 vanilla silver rings. The other 252 places are not stocked yet. |
| Places | 258 places, each with its own first-choice source place (246 distinct) | 77 places take an Argonian-kit source. 126 take a source built from vanilla Skyrim pieces (110 from Skyrim itself, the rest from border and trading-post mods). The places that should feel most Argonian lean hardest on those: Murkwood 10 of 13, Banujha Basin 11 of 15, Cape Percar 12 of 17, the Root-Folk 13 of 19. Every farm, mine, estate and keep, 8 of 11 shipwrecks and 5 of 8 forts have no Argonian-kit candidate among their four choices. |
| Pieces in places | About 3,500 placed objects in the six drafts | 47% of doors are Nordic-ruin or Solitude doors (nearly all in Helstrom). The vanilla candle lantern is placed 173 times. The fur bedroll is 27 of 97 furniture pieces. In a wider sample of 54 source places, barrels, crates, sacks, baskets and hay are about 8% of everything placed. Tropical Skyrim swaps none of these: it changes trees and grass only. |
| Lore objects | Totems (about 8), bone chimes, a drum, a Sithis shrine, frog instruments, 12 Argonian banner types, the Dunmer house banners, four hammock models with no bed record | Not found in any mod we hold or on Nexus: grave-stake, sap jar and sap tap, a proper egg clutch (ours are vanilla dragon eggs), Hist stele and tablets, fish weir and net rack, dugout or raft, an emblem for any of the 18 cultures, a sign for any of the nine story lines. |
| Trees and plants | 193 tree models over the 20 land regions; no two regions share more than about a third | One fern model is 11% of all plant placements. There is one reed model (7%). One lily model is 93% of lilies. Eleven wet regions come out near-identical. A handful of mangrove models carry the whole coast. The Hist has no sick or dying look, though your rulings want the endings to show trees dying. |
| Boats and wrecks | Black Marsh & Valenwood's Imperial ship; King of the Murkmire's three boats and docks; vanilla rowboats | 31 boat stops and 11 wreck places. No native craft. Four wrecks stand on a vanilla Nordic ship. No boat mod is among our 193 dependencies. |

Limits on these numbers:

- Nothing was judged by eye. The lanes worked from model names, counts and tables, so "reads as Nordic" is by
  name, and how good the held Argonian models look is unchecked. You judge look.
- Only six places are stocked and drafted, so province-wide shares of clothing and pieces are projections.

### What Nexus can fill without any art

**How it was searched, and what was wrong the first time.** My first pass searched only the Special Edition's
Nexus and only mod names, and I told you Nexus had no mangroves, canoes, jade weapons or Argonian bone armour.
You showed that was wrong with GKB Green Trees. The search tool now covers both the Special Edition and the
2011 game, and matches description text as well as names; the four audit lanes re-ran about 220 terms and read
about 140 descriptions. Two limits remain: nothing was downloaded, so the contents of the big resource packs
are known only from their descriptions; and permissions were read from the description text only.

A mod of the 2011 game needs its model files converted before the Special Edition can load them. That is a new
kind of step for us (a conversion at staging, nothing committed) and would be proved once like any other.

| Gap | Found (2011 = the 2011 game's Nexus, needs converting) | To check |
|---|---|---|
| Trees | GKB Green Trees (2011, 19268): free to use with credit. We already hold 40 of its models through Black Marsh & Valenwood, mangroves included; its numbering has gaps, so it probably holds unused jungle trees and mangroves. | open the pack and list what we do not hold |
| Tropical plants and props | Tropical Lands Assets from the Cathnoquey project (33446): a 440 MB set, free with credit, contents unlisted. The strongest unopened lead. Also Tamira's New Plants (2011, 22018) and Waterplants (6092), the only lead for more reeds. | open and list |
| Lore ingredient plants | Harvestables (2011, 15108): saltrice, marshmerrow, hackle-lo, sugarcane, stoneflower, trama root, ash yam, bamboo trees. | no permission line: ask the author |
| Ships and wrecks | Ships and Boats of Tamriel (41653) and three 2011 ship packs: Nord, Breton, Imperial and East Empire hulls. Two sailing mods mention canoes and rowboats (2011, 67727; 40057). | one author's packs say "only with my permission": ask |
| Banners | Incaendo's Banner Resource (17604, 59 banners) and Banner Resource 2 (94919, 163 banners), and Flags Resource (56152). The banner models exist; only our emblems are missing. | |
| Argonian armour and dress | Argonian Mercenary Armor with Armored Tail (2011, 27676), Argonian Raptor Feet (2011, 19283), HistBone and Bonewood Argonian Armors (2011, 99144: the light bone plate three tribes are specified in), Edhildil's Argonian War Tails (2011, 28502, "use at will, credit"), Shifts-Sand's Saxhleel Sundries (191593: tribal wear, wraps, shell armour, robes, a death mask; a demo ported from Elder Scrolls Online with known faults), Simple Straw Hats (89962, says it fits Argonians), frog and lizard hats (2011, 88009). | Argonian fit of each; I would look at Saxhleel Sundries and not lean on it |
| Jewellery and rigid tribal pieces | Gemling Queen Resources (2011, 54483, blanket permission with credit), a bone shield, skull helmets and a tribal staff (2011, 43293, free to use), a feather ornament, the I'noh-Ssu-Keh war mask (82282). | |
| Weapons | Argonian (Saxhleel) Weapon Pack (67137, seven melee weapons), Saxhleel War Club (35555), one jade blade (2011, 110218). | |
| Sleeping | Four hammock models are already held (Black Marsh & Valenwood, Baan Malur) but have no bed record, so nobody can sleep in them. | a record and a sleep marker, no modelling |
| Buildings and clutter | Stroti's Stilt House Resource (2011, 61824: stilt house, hut, platform, shutter door, credit), a wicker furniture set, tiki torches, skull ropes and offering bowls, pots and baskets from three resource authors, tombstones, several statue resources, a Hawaiian deity statue that could base an idol. | one building-kit pack forbids porting without permission: leave it |
| Bones and lily pads | Whale Bones on Coasts (91958), a bones pack and a lily pad resource (2011). | |
| A map of Argonian mods | Katie's Beast Race Aesthetics Compendium (45654), a curated list worth reading end to end. | |

**Still not found by any term in either game:** Argonian grave-stakes; totems beyond the eight we hold; sap
vessels and tapping gear; egg nests; Hist steles; dugouts, reed rafts and houseboats; fish weirs, fish traps
and drying racks; cattails and rice-field plants beyond the saltrice we hold; tree ferns; turtle-shell or reed
shields; Black Marsh versions of the lowest-tier weapons and of the six signature weapon types. That is the
own-model list, and I hold it more loosely than before: the unopened packs above may yet shorten it.

## 3. What the tools can and cannot do

**The pipeline you described works in pieces, and nobody seems to have joined them for Skyrim.** Each step is
documented; the join from a generated model to a Skyrim model file is the unproven part.

- **Images:** Fal's image models make a clean reference of one object on a plain background. One of them takes
  up to 14 reference pictures at once, which is the tool for consistency (section 5).
- **3D:** Fal already hosts Tripo (four versions) and Hunyuan 3D, on the same account we use for music. No
  separate Tripo account is needed. They can return a textured model or the bare shape.
- **Clean-up:** generated models come out with 19,000 to 52,000 triangles, poor texture layouts and stray
  faces. A Skyrim weapon wants 2,000 to 8,000. Blender, run without a screen on the build machine, does the
  reduction, re-layout and scaling by script.
- **Into Skyrim:** we already own tools that read every Skyrim model and write simple static ones. They do not
  yet write collision, markers or anything worn. The standard Blender exporter for Skyrim is officially
  Windows-only.
- **What generators are good at:** solid, closed shapes with a strong outline: clubs, blades, pots, posts,
  stumps, hulls, shells.
- **What they are bad at:** thin parts (shafts, hafts, reeds), leaves and fronds (flat cut-out cards in a game,
  which a generator cannot make), symmetry, and anything that must bend with a body.

**Your size instinct is right, with numbers.** One 2K texture gives 2,048 pixels per metre on a 1 m object, 683
on a 3 m one, 256 on an 8 m one and 102 on a 20 m one. A surface two metres from the player fills about 480
screen pixels per metre. So one texture stays sharp up to roughly 4 m of object and is visibly soft past 8 m.
A 4K texture doubles those sizes. Big things stay possible only if seen from a distance, split into parts, or
dressed in repeating materials instead of one stretched picture.

**Prices** (Fal's model pages, 24 November; they move often):

| Step | Price |
|---|---|
| One reference image, with up to 14 references fed in | $0.06 to $0.16 |
| One bare shape, no texture (Tripo H3.1 to Tripo P2) | $0.20 to $1.00 |
| One textured model (Hunyuan 3D, Tripo H3.1, Tripo P2) | $0.38 to $1.30 |
| **One kept model, allowing three image tries and two model tries** | **$1.00 to $2.70** |

**Agent cost: I cannot estimate it reliably, and the pilot is where it gets measured.** The one outside figure
is a vendor's write-up of five weapons cleaned up with an agent in about 2.7 hours in total, to an ordinary
game engine and not to Skyrim. For scale, all of today's research lanes together used about 1.3 million tokens.

**Policies:**

- **Nexus** announced on 3 November 2026 that AI-made content is allowed but must be labelled, with existing
  mods to comply by 2 January 2027, and that using a mod to train an AI needs its author's written consent.
  The label only bites if we publish there; our Fal music already counts.
- **Bethesda's paid Creations programme** bans generative AI. It is not our channel.
- **Fal's output terms** are already recorded for our music as owned by us with commercial use allowed. Before
  bulk spend I would read the same terms for the 3D models and record them the same way.
- **King of the Murkmire** is the one mod of ours whose page says add-ons should "not make use of AI". Our
  record says your permission from its author, held since 24 September, covers our use. See section 8.

## 4. The route: "acts like an existing thing"

Your suggestion is the centre of the whole plan, and it reaches further than weapons. I call it the **template
swap**: take a copy of an existing model file and its record, replace only the visible shape with the new one,
and keep everything else.

I read the vanilla files on the build machine to check this. The steel sword's file holds the visible blade,
a blood-edge shape, a tag naming the bone it hangs from, and its drop collision. The warhammer is the same,
hung from the back. The iron shield carries its own tag and collision. The bedroll carries its sleep markers
and collision inside the file. None of that needs remaking: a new shape placed at the same grip point and
along the same axis swings, sheathes, blocks, drops and sounds exactly like the donor, and a sleeper lies on a
new mat exactly as on the old bedroll.

**Your ruling on weapon types** (24 November): where a type exists in Animated Armoury or another of our
sources, its animations are taken as good, and our own version copies that record and swaps the model. Our
items page already records how each swings:

| Our own version of | Copies the record from | Swings as |
|---|---|---|
| Sword, dagger, war axe, mace, greatsword, battleaxe, warhammer | vanilla | itself |
| Pike | Animated Armoury | greatsword |
| Spear, trident, harpoon | Heavy Armory, Here There Be Monsters or New Armory | greatsword (short spear: sword) |
| Halberd, quarterstaff | Animated Armoury | battleaxe |
| Whip | Animated Armoury | mace |
| Rapier | the collection's rapier animation pack | sword |
| Claw | the collection's claw animation pack | dagger |

Long shafts are the generators' weak side, so for every long weapon only the head is generated; the shaft is a
plain cylinder made by script and dressed in a shared wood material. Bows, crossbows, blowguns and thrown
weapons stay out: their parts are animated.

How far the swap reaches in other kinds (the research lane's estimates, to be confirmed by the pilot):

| Kind | How much the swap covers | The catch |
|---|---|---|
| Melee weapons | about 95% | Keep the length within about 20% of the donor's. Two-handed shafts must be as long as the donor's or the second hand floats. |
| Shields, rigid masks and helmets, jewellery | about 90% | Masks and helmets must clear the Argonian snout; that needs a fitting step. |
| Movable clutter (bowls, jars, baskets) | about 85% | The collision is re-fitted if the size differs much. |
| Furniture (mats, hammocks, stools) | about 80% | The lying or sitting surface must be within about 5 cm of the donor's height. |
| Lanterns and other lights | about 80% | The flame must sit at the new wick. |
| Harvestable plants; containers with fixed lids | about 60% | The picked and unpicked states must keep their names. |
| Doors and things with moving parts | about 40% | The moving part must keep its pivot. |
| Bows and crossbows; full outfits | about 10% | Animated limbs; cloth that must bend with the body. |

**Two more routes need even less:**

- **Texture only.** A banner or a door sign is a flat image on a model that already exists. The record can
  point an existing model at a new texture without touching the model.
- **Replace the file for the whole province.** A new model saved over the vanilla bedroll's path changes every
  bedroll in every source place at once, with no record work and no place edits. It would also change Imperial
  and Dunmer camps; a record-level swap by culture is the finer tool where that matters.

## 5. Keeping it all one game: the consistency method

You asked for a hierarchy: everything looks like the same game; within that, each culture, region or faction is
distinct from the others and consistent within itself; and there may be levels below. This section is the plan
for that.

**What the research is worth.** Every source describes the same process, and almost every source is a vendor
selling a tool. I found no independent account of a shipped AI-made 3D set that reports how consistent it came
out, and no published recipe for matching an existing game's look. So the process below is well supported; the
parts about matching Skyrim are my own reasoning, and the pilot is built to test them.

**The main idea: fix the look at the material, not at the picture.** If every model gets its own generated
texture, consistency depends on forty separate generations agreeing. If the generator supplies only the shape,
and the surface comes from a small shared set of materials, then two models of the same wood are the same wood
by construction. Skyrim itself is built this way.

So each surface takes one of two routes:

1. **Shared material (the default).** The new shape is dressed in materials from a library: first the game's
   own wood, bone, rope, straw, stone and metal textures, which match Skyrim perfectly because they are
   Skyrim's; then a few of our own repeating marsh materials where the game has none (reed weave, wet clay,
   jade, scale), each made once and approved once.
2. **Unique texture (only where the surface carries meaning).** A grave-stake's carving, an emblem, a painted
   mask. These are generated, then passed through one fixed script that pulls colour, brightness and sharpness
   into ranges measured from the game's own textures, removes baked-in light, and converts to Skyrim's texture
   layout. Measuring the game's colour ranges is arithmetic on files the player owns, not training a model.

**The hierarchy, and what is fixed once at each level:**

| Level | What it is | Fixed once | Who approves |
|---|---|---|---|
| 0. The game | one sheet for everything we make | ranges of colour, brightness and sharpness measured from Skyrim's and our mods' textures; pixels per metre; triangle limits per kind; the fixed conversion script; the shared material library; one lighting set-up for all review pictures; a size chart; a "never" list (clean, glossy, saturated, glowing, ornate fantasy) | you, once, on a line-up beside vanilla pieces |
| 1. Material | the items ladder's materials, which already exist as data: bog iron, bone, flint, jade, obsidian, reed, shell, clay | one library material each, so bone is the same bone on every tribe's weapons | you, once per material |
| 2. Culture, region or faction | the 18 cultures, the nine story lines, the foreign enclaves | a one-page sheet: the culture's identity colour (already in our data) and five to seven more; which two or three materials it favours; one sentence of shape (for example "hooked and toothed" against "smooth and leaf-shaped"); its emblem, which is the standard from part B and recurs carved or painted on its things; three reference pictures; one approved hero piece | you, on the sheet and the hero |
| 3. Family | one tribe's weapon set, the grave-stake set, the boat kit | one anchor model, taken into the game. Every sibling is made from the anchor and the culture sheet, never from another sibling, because picture-to-picture copying drifts after a few steps. One thing changes per batch. | you, on the anchor in game |
| 4. Object | the single model | a short brief: what it is for, its size, the record it copies, and the one feature that makes its outline its own | automatic checks; you see the finished family as a line-up |

Material and culture cross each other: a Naga-Kur club is the ladder's bone and wood, in the Naga-Kur's shape,
carrying the Naga-Kur mark. That gives "same game" from level 0 and 1, "this tribe" from level 2, and "this
set" from level 3, without any model needing to be consistent by luck.

**How it is held in practice:**

- The sheets are data files, like the music's shared palette. A script builds every image request from them
  (game block, material block, culture block, family block, object brief), so no request is written freehand.
- Every reference image is made with the approved hero and anchor fed in as references.
- An automatic gate checks numbers only: colour and brightness inside the measured ranges, pixels per metre,
  triangle count, size against the donor, materials from the library. An AI image judge may list suspected
  faults for a person to look at, but never approves: such judges are known to invent details and pass them.
- You judge look at three points only: the level sheets and their hero pieces, each family's anchor in game,
  and one line-up picture per finished family beside its vanilla neighbours.
- Sheets are written only for the cultures a batch touches, starting with the Act I places, not all 18 up front.
- No style training. Fal's own guide says it pays only at hundreds of images, and we would never train on the
  game's or a mod's textures.

## 6. The four options

Each option includes the one before it. Fees are Fal's; agent work is extra and unmeasured.

### Do nothing

The rule stays. The audits' free findings still stand as ordinary work (below, "least, part A"), but nothing
new is made.

- **Benefit:** no risk, no policy question, no time off the story.
- **Cost:** the tells in section 1 stay. The tribes keep differing by tint only.

### Do least: no new models

**Part A needs no rule change and no art.** I would do this whatever you decide.

1. **Open the packs the search found** and list what they hold that we do not: GKB Green Trees' unused trees,
   the Cathnoquey tropical set, Waterplants, Harvestables, the banner packs, the stilt house, and the Argonian
   armour, footwear, tail and jewellery mods in section 2. Add what is good as dependencies; ask the two
   authors whose terms need it. This is the step most likely to shrink everything below it.
2. **A swap table for Argonian places**, using Argonian models we already hold: the vanilla candle lantern
   (173 placements in six drafts) to the Argonian lanterns; Nordic-ruin and Solitude doors (56 of 119 doors)
   to King of the Murkmire's mud, thatch and bamboo doors where the frame fits; hide tents to the scale tents;
   shrines of the Nine to the Hist shrine; generic banners to the Argonian banners. This is your ruling of 20
   November ("an easy swap is taken where there is one") made into one table, and it matters most for the 126
   places built from vanilla pieces.
3. **Give the held hammocks a bed record**, so camps can sleep in hammocks instead of on fur bedrolls.
4. **Place what we hold and never placed:** King of the Murkmire's saltrice (the "saltrice marsh" regions show
   none), five giant cypress knees, two bamboo models, and the Dragonborn giant mushroom trees for the fungus
   floors. These appear at the next world rebuild you ask for.
5. **Fix the holes the audit found in our own tables:** the three tribes pointed at armour we do not hold; the
   12 trade kits with no clothing row; the town guard's cuirass with no dropped model; two reward outfits with
   no item rows.

**Part B is flat images only**, and needs a small change to the rule (today a Fal image is allowed only as one
small piece you ask for):

6. **An emblem for each of the 18 cultures and a sign for each of the nine story lines**, plus the Company
   standard and a pirate flag: about 30 images on banner models that already exist, and as door signs. The
   emblems are new lore, so each cites the tribe's lore and you judge them on one sheet. They are also the
   first half of each culture's level 2 sheet in section 5, so this work is not thrown away if you stop here.
7. **Recolours by code, not by image model**, as we already do for bamboo leaves: a sick and a dying Hist, marsh
   dyes for the six vanilla commoner outfits, a colourway per tribe for the totems.
8. **A wet-wood retexture of the vanilla barrels, crates and sacks**, the largest family of generic pieces.

- **Fal fees:** under $30.
- **Benefit:** every culture and story line gets a mark the player can learn; the most-placed Nordic pieces in
  Argonian places go; the marsh gains rice, knees, fungus and whatever the opened packs hold; dress improves
  from mods made for Argonians. Low risk, because nothing new has to work in the engine.
- **Cost:** the commonest weapons, the native boats and the lore objects stay as they are.

### Do more: about 49 small solid models (recommended, after the pilot)

**First a pilot of five**, each taken into the game for your check, about $15 of fees:

| Pilot model | Proves |
|---|---|
| Crocodile-tooth club, acting as a mace, in shared wood and bone | the weapon swap; the shared-material route; a family's anchor |
| Crocodile-tooth maul, acting as a warhammer, made from the club | that a sibling made from an anchor looks like its family |
| Carved grave-stake, with its own generated texture | a new static prop; the unique-texture route and the grading script beside Skyrim's textures |
| Reed sleeping mat, in the bedroll's file | the furniture swap: a person lies on it correctly |
| A tribal pike: generated head, scripted shaft, copying Animated Armoury's pike | your weapon-type ruling and the shaft method |

The pilot also builds everything once: Blender on the build machine, the swap step in our own model tool,
texture conversion, the level 0 sheet with its measured ranges and first library materials, one culture sheet,
and a record template per kind. It measures the agent cost per model, which I cannot estimate today.

**Then the batch**, every item small, solid and without moving parts. Anything the opened packs turn out to
hold comes off this list first.

| Group | Models | Count | Acts as, or route |
|---|---|---|---|
| Bog-iron weapons, replacing the relabelled vanilla ones | sword, dagger, war axe, mace, greatsword | 5 | the same vanilla type |
| Tribal weapons | jade dagger, flint war axe, crocodile-tooth club, crocodile-tooth maul, toothed sword, Naga-Kur bone sword and dagger, eel gaff, obsidian-edged heavy club | 9 | dagger, war axe, mace, warhammer, sword, sword and dagger, dagger, battleaxe |
| The six signature types | pike, halberd, skull-topped quarterstaff, rapier, whip, claw | 6 | the existing record of each type |
| Shields | turtle shell, reed wicker | 2 | shield |
| Grave-stakes | skull, glyph, serpent, twinned, small | 5 | new static |
| Hist tending | sap jar, sap tap, gourd, Hist seed pod | 4 | movable clutter and static |
| Eggs | egg clutch in a shell cup, two sizes | 2 | static, replacing the dragon eggs |
| Sleeping | reed mat, two weaves | 2 | the bedroll's file |
| Fishing | weir section, fish trap, net drying rack | 3 | new static |
| Boats | dugout canoe, bundled-reed raft, moored | 2 | new static, not rideable |
| Shore and swamp | hollow log, snag, stump, half-sunk trunk, two driftwood piles | 6 | new static |
| Mounds | clay, mud and termite mound | 3 | new static |

- **Fal fees:** 49 models at $1.00 to $2.70 is $50 to $135. I would cap it at $200 to allow for more retries
  than the estimate assumes.
- **Benefit:** the commonest weapons, six tribes' signature weapons, the boats at 22 raft stops, the
  grave-stake in 137 lived-in places, the two Act I weirs and the Hist's own gear all become Black Marsh's,
  and each tribe's things carry its mark.
- **Cost and risk:** the tooling is new and one link is unproven (the pilot settles it). The consistency
  method's Skyrim-matching part is my own reasoning (the pilot tests it). Each new prop still has to be placed
  by the place and stock skills, and scattered props reach undrafted places only at a world rebuild.

### Do most: about 55 more, harder

Everything above, plus the medium and hard kinds. Fal fees about $150 to $250 more. I would not approve this as
a block; pick from it once the "more" batch has shown what the pipeline does well.

| Group | Models | Why it is harder |
|---|---|---|
| Head ornaments and masks | feather crests, horn caps, frill clips, two masks | each must be fitted to the Argonian head |
| Necklaces and rings | tooth, jasper and pearl necklaces; shell and jade rings | the necklace bends with the chest; try the jewellery resource first |
| Faith and memory | three Sithis shrines, a Hist stele, three tablets, a chime tree, four new totems | larger carved shapes |
| Mangrove roots and tree ferns | root clusters, three fern trunks | a generated trunk joined to an existing tree's leaves so it still sways; needs distant-view models; only after the GKB pack is opened |
| Marsh plants | reeds, cattails, sedge, rice, hanging moss | flat cut-out cards built by hand from a Fal image; no 3D generator involved |
| Native houseboats and wrecks | twin-hull canoe, houseboat, a houseboat wreck | size: walkable decks, repeating materials instead of one texture |
| Fungus, coral | four each | narrow regions |
| Working pieces | kiln, clay wall, reed tent, woven screens | hut-sized |

### What I would not do at any level

- **Houses and hut kits.** King of the Murkmire holds about 200 hut, stockade and house pieces, and a stilt
  house resource exists; size is the generator's weakest point; and buildings need walkable collision and
  walking meshes.
- **The root-grown house.** It is a real gap for the 19 Root-Folk places, but it is a whole building kit.
- **Full outfits and anything cloth.** See section 7.
- **Bows, crossbows, blowguns and thrown weapons.** All need animation work.
- **The ball court and the banyan.** Rare, or not in our lore.

## 7. The honest gap: clothing

Clothing is the largest hole the audit found and the one this pipeline helps least. A loincloth, wrap or robe
has to bend with the body and tail, which means weight-painting to the skeleton and a second fit for Argonian
heads and tails. Generated cloth wrapped on a body is the hardest case there is.

What can be done, in order of value for effort:

1. Fill the 12 trade kits that have no clothing row from what we hold (part A).
2. Try the Argonian-made mods the proper search found: the mercenary armour with a tail piece, the raptor
   feet, the bone-plate armours, the war tails, the straw hats, and Saxhleel Sundries with caution (part A).
3. Marsh-dye recolours of the vanilla commoner clothes, by code (part B).
4. Rigid ornaments on top of plain clothes: feather crests, horn caps, masks, necklaces (the "most" list). A
   villager in a dyed tunic with a tooth necklace and a feather crest reads as Black Marsh far more cheaply
   than a new outfit would.

Dress will still be the weakest part of the province's look. If it matters most to you, the answer beyond
these is a human-made clothing mod or a commission, not this pipeline.

## 8. Risks and what would have to change

- **King of the Murkmire's terms.** Its author asks that add-ons not use AI, and your permission of 24
  September is what covers us today. Putting AI-made models beside its buildings in 40-odd places is a step
  beyond what that permission was given for. I would never use its files as donors, as references or as the
  base of a retexture, and I think it is worth one plain question to the author before the "more" batch. That
  is your call and your relationship.
- **Other authors' terms.** Two finds need asking before use (Harvestables, one ship author); one building-kit
  pack forbids porting. Every new dependency gets its permission read in full, as now.
- **Look.** A generated texture can read as pasted in beside Skyrim's. The guards are the shared-material
  route, the measured ranges, and your three look points in section 5.
- **The unproven link.** If the pilot fails on the build machine, the fallback is the Windows play machine
  with the standard Blender exporter, which costs machine time.
- **My search can still be wrong.** It was once already. The big packs are unopened, and Nexus's search matches
  whole words in descriptions, so a pack that never names a thing will not be found by it. Part A's first step
  is there for that reason, and the own-model list is cut down before any model is made.
- **Placement is separate work.** A model in the pool changes nothing until the stock ladder, the dressing
  rules and the drafted places use it. Drafted places take it by a narrow change; the rest of the province
  takes it at a world rebuild, which runs only when you ask.
- **Labelling.** If the mod is ever published on Nexus it carries the AI-generated label. It already would,
  for the music.
- **Where the files live.** Like the soundtrack: built, stored outside the repository, one row in the mod
  list, with every request recorded. The style sheets are committed as data. Nothing binary is committed.
- **The rule.** Decision 0006 point 5 and the "Never make art" line in CLAUDE.md would be amended to name
  exactly what is allowed (flat images on existing models; small solid models by template swap or as static
  props, made under the style sheets), and what stays banned (section 6's last list).

## 9. The ten best returns, in order

1. Open the packs the search found. It costs nothing and may shrink everything else.
2. The swap table for lanterns, doors, tents, shrines and banners, and a bed record for the hammocks. No art.
3. Emblems for the 18 cultures and signs for the nine story lines. Flat images on existing banners.
4. Bog-iron and tribal weapons by swap. The commonest things in every hand.
5. The six signature weapon types, each tribe's own, on existing records.
6. Grave-stakes. The lore's best repeatable object, in 137 places.
7. The dugout and the reed raft. Twenty-two raft stops with no native boat.
8. Clothing rows, the Argonian-made mods and dye recolours. The biggest hole, the cheapest partial fix.
9. The fish weir kit. Two Act I places are named for weirs.
10. Sap jar, sap tap and a real egg clutch, with saltrice, cypress knees and mushroom trees placed.

## 10. What I need from you

One choice, on owner call #94: **nothing, least (part A only, or A and B), more, or most**. My recommendation
is part A now, part B with the small rule change, and the five-model pilot as the gate to "more". And one yes
or no: whether to ask King of the Murkmire's author before AI-made models go in beside its buildings.
