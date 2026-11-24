# New art for Argonia: what we could do, and what I recommend

Written 2026-11-24 for owner call #93. Nothing has been created or bought. This page is the proposal; the six
research reports behind it sit beside it in this folder:

- [tooling.md](tooling.md): the tools, prices and policies for making 3D models with an agent.
- [skyrim-asset-pipeline.md](skyrim-asset-pipeline.md): what it takes to turn a generated model into a working Skyrim asset.
- [gear-and-clothing.md](gear-and-clothing.md): weapons, armour and clothing.
- [places-and-pieces.md](places-and-pieces.md): places against their source places, and the most Skyrim-looking pieces.
- [identity-vs-lore.md](identity-vs-lore.md): every region, culture and faction against the lore.
- [nature-and-vessels.md](nature-and-vessels.md): trees, plants, boats, ships and wrecks.

## 1. The short answer

**I recommend relaxing the rule, narrowly, in three steps, and stopping after any step that disappoints.**

1. **Do the "least" option now.** Most of the cheapest gains need no new art at all, and the rest of that option
   needs only flat images on models we already hold.
2. **Run a three-model pilot** (about $10 of Fal fees): one weapon, one prop, one piece of furniture, taken all
   the way into the game for you to look at. No one appears to have published a working route from a generated
   model to a Skyrim model file, so this is the one link that has to be proven before any money is spent in bulk.
3. **If the pilot looks right in game, do the "more" option**: about 48 small solid models, almost all made by
   your "acts like an existing thing" route. Treat the "most" list as a menu to pick from afterwards, never as a block.

The reason is what the audits found. The province is not short of models in number. It is short in a few
specific, very visible spots, and those spots are mostly small, solid things:

- The commonest weapons in Black Marsh are Skyrim's own iron and steel swords under a new name.
- Every camp and outpost sleeps on Skyrim's fur bedroll.
- No Argonian boat exists at all, though the travel network has 31 boat stops.
- The lore's best repeatable object, the carved grave-stake, has no model anywhere.
- No tribe has a standard and no story line has a sign.

The one large gap that this pipeline cannot fix cheaply is **what people wear**. Skinned clothing is the hardest
thing to generate, and I say so plainly in section 6.

## 2. What the audits found

### Where we are thin (measured)

| Area | What we hold | Where it is thin |
|---|---|---|
| Weapons and armour | 767 records on 638 distinct models | The 11 lowest-tier "bog iron" weapons are vanilla iron and steel models. Two heavy sets use Nordic plate and Nordic carved models. Every Argonian village guard wears one set (Stormhold Warrior); every town watch wears one other. Three tribes are specified in light shell or bone-plate armour that does not exist. Six tribes' signature weapon types (pike, halberd, quarterstaff, rapier, whip, claw) have no Black Marsh model. |
| Clothing | About 30 non-armour clothing models in all | 12 of the 23 trade kits have no clothing row. In the six stocked places 126 of 165 people have no authored clothing, and half of the rest wear vanilla farm, monk or beggar clothes. The jewellery is 32 vanilla silver rings. The other 252 places are not stocked yet. |
| Places | 258 places, each with its own first-choice source place (246 distinct) | 110 places (43%) take a vanilla Skyrim source and 77 (30%) an Argonian-kit source. 61 places have no Argonian-kit candidate in any of their four choices: every farm, mine, estate and keep, 8 of 11 shipwrecks, 5 of 8 forts. Tribal camps mostly sit on vanilla orc strongholds and giant camps. |
| Pieces in places | About 3,500 placed objects in the six drafts | 47% of doors are Nordic-ruin or Solitude doors (all but a few in Helstrom). The vanilla candle lantern is placed 173 times. The fur bedroll is 27 of 97 furniture pieces. In a wider sample of 54 source places, barrels, crates, sacks, baskets and hay are about 8% of everything placed. Tropical Skyrim swaps none of these: it changes trees and grass only. |
| Lore objects | Totems (about 8), bone chimes, a drum, a Sithis shrine, frog instruments, 12 Argonian banner types, the Dunmer house banners | No model in any mod we hold, and none found on Nexus: grave-stake, sap jar and sap tap, a proper egg clutch (ours are vanilla dragon eggs), Hist stele and tablets, fish weir and net rack, reed sleeping mat, dugout canoe or raft, a standard for any of the 18 cultures, a sign for any of the nine story lines, the Company standard, a pirate flag. |
| Trees and plants | 193 tree models over the 20 land regions; no two regions share more than about a third | One fern model is 11% of all plant placements. There is one reed model (7%). One lily model is 93% of lilies. Eleven wet regions come out near-identical. Five mangrove models carry the whole coast. The Hist has no sick or dying look, though your rulings want the endings to show trees dying. |
| Boats and wrecks | Black Marsh & Valenwood's Imperial ship; King of the Murkmire's three boats and docks; vanilla rowboats | 31 boat stops (22 worked by raft-masters) and 11 wreck places. No canoe, dugout or raft. Four wrecks stand on a vanilla Nordic ship. No boat mod is among our 193 dependencies. |

Three limits on these numbers:

- Nothing was judged by eye. The lanes worked from model names, counts and tables, so "reads as Nordic" is by
  name, and how good the held Argonian models look is unchecked. You judge look.
- Only six places are stocked and drafted, so province-wide shares of clothing and pieces are projections.
- Two lane findings were wrong and are corrected in their reports. One lane read each place's second-choice
  source and concluded that 62 places share one source; at first choice the places are well spread. Another
  said the build machine holds no game files; it does, and I read the vanilla sword, warhammer, shield and
  bedroll files there to confirm the swap route (section 4).

### What Nexus can fill without any art

About 500 searches across the four audit lanes. Worth adding as dependencies, each after its permission page
and contents are read properly (the lanes could only read summaries):

| Mod (Nexus id) | Fills |
|---|---|
| Argonian (Saxhleel) Weapon Pack (67137) | seven Argonian melee weapons for the higher tiers |
| Saxhleel War Club (35555) | a tribal two-handed club |
| Simple Straw Hats (89962) | straw hats that say they fit Argonians |
| Ships and Boats of Tamriel (41653) | ships and wrecks as a modder's resource, to replace the Nordic wrecks |
| Waterplants (6092) | more water plants beside our one lily and one reed |
| Whale Bones on Coasts (91958) | large bones for the coasts |
| Flags Resource (56152) | pirate and national flag textures |
| I'noh-Ssu-Keh War Mask (82282) | one rigid tribal war mask |
| Shifts-Sand's Saxhleel Sundries (191593) | tribal wear, wraps, shell armour, robes, a death mask: the best match to the clothing gap. It is a demo with 6 endorsements, ported from Elder Scrolls Online, with known weight-painting faults. I would look at it and not lean on it. |

Nexus has nothing for: Argonian totems or idols beyond what we hold, grave-stakes, reed mats or hammocks in an
Argonian style, canoes, dugouts, rafts, fish weirs, mangroves, tree ferns, cattails, jade weapons, turtle-shell
shields, reed armour, or any Aztec, Maya or Polynesian dress. What Nexus does have for bedrolls, barrels, pelts
and lanterns are better-looking versions of the same Nordic shapes.

## 3. What the tools can and cannot do

**The pipeline you described works in pieces, and nobody seems to have joined them for Skyrim.** Each step is
documented; the join from a generated model to a Skyrim model file is the unproven part.

- **Images:** Fal's image models make a clean reference of one object on a plain background. Three views
  (front, side, back) cure the commonest fault, an invented back side.
- **3D:** Fal already hosts Tripo (four versions) and Hunyuan 3D, on the same account we use for music. No
  separate Tripo account is needed. Tripo's P2 version removes baked-in lighting and caps the face count,
  which are the two things a game model most needs.
- **Clean-up:** generated models come out with 19,000 to 52,000 triangles, poor texture layouts and stray
  faces. A Skyrim weapon wants 2,000 to 8,000. Blender, run without a screen on the build machine, does the
  reduction, re-layout and scaling by script.
- **Into Skyrim:** we already own tools that read every Skyrim model and write simple static ones. They do not
  yet write collision, markers or anything worn. The standard Blender exporter for Skyrim is officially
  Windows-only.
- **What generators are good at:** solid, closed shapes with a strong outline: clubs, blades, pots, posts,
  stumps, hulls, shells.
- **What they are bad at:** thin parts (staff shafts, spear hafts, reeds), leaves and fronds (these are flat
  cut-out cards in a game, which a generator cannot make), symmetry, and anything that must bend with a body.

**Your size instinct is right, with numbers.** One 2K texture gives 2,048 pixels per metre on a 1 m object, 683
on a 3 m one, 256 on an 8 m one and 102 on a 20 m one. A surface two metres from the player fills about 480
screen pixels per metre. So one texture stays sharp up to roughly 4 m of object and is visibly soft past 8 m.
A 4K texture doubles those sizes. Big things stay possible only if seen from a distance or split into parts.

**Prices** (Fal's model pages, 24 November; they move often):

| Step | Price |
|---|---|
| One reference image | $0.08 to $0.15 |
| One 3D model, Hunyuan 3D with full materials | about $0.38 |
| One 3D model, Tripo H3.1 | $0.30 to $0.40 |
| One 3D model, Tripo P2 (cleanest shape) | $1.10 to $1.30 |
| **One kept model, allowing three image tries and two model tries** | **$1.00 to $2.70** |
| The same with three views per try | about $3.40 |

**Agent cost: I cannot estimate it reliably, and the pilot is where it gets measured.** The one outside figure
is a vendor's write-up of five weapons cleaned up with an agent in about 2.7 hours in total, to an ordinary
game engine and not to Skyrim. For scale, today's six research lanes used about one million tokens between them.

**Policies:**

- **Nexus** announced on 3 November 2026 that AI-made content is allowed but must be labelled, with existing
  mods to comply by 2 January 2027. It only bites if we publish there; our Fal music already counts.
- **Bethesda's paid Creations programme** bans generative AI. It is not our channel.
- **Fal's output terms** are already recorded for our music as owned by us with commercial use allowed. Before
  bulk spend I would read the same terms for the 3D models and record them the same way.
- **King of the Murkmire** is the one mod of ours whose page says add-ons should "not make use of AI". Our
  record says your permission from its author, held since 24 September, covers our use. See section 7.

## 4. The route I would use: "acts like an existing thing"

Your suggestion is the right centre for the whole plan, and it reaches further than weapons. I call it the
**template swap**: take a copy of an existing vanilla model file and its record, replace only the visible shape
with the new one, and keep everything else.

I read the vanilla files on the build machine to check this. The steel sword's file holds the visible blade,
a blood-edge shape, a tag naming the bone it hangs from (`WeaponSword`), and its drop collision. The warhammer
is the same with `WeaponBack`. The iron shield carries a `SHIELD` tag and its collision. The bedroll carries
its sleep markers and collision inside the file. None of that needs remaking: a new shape placed at the same
grip point and along the same axis swings, sheathes, blocks, drops and sounds exactly like the donor, and a
sleeper lies on a new mat exactly as on the old bedroll.

How far it reaches, by kind (the research lane's estimates, to be confirmed by the pilot):

| Kind | How much the swap covers | The catch |
|---|---|---|
| Swords, daggers, war axes, maces, greatswords, battleaxes, warhammers | about 95% | Keep the length within about 20% of the donor's, or hits look wrong. Two-handed shafts must be as long as the donor's or the second hand floats. |
| Shields, rigid masks and helmets, jewellery | about 90% | Masks and helmets must clear the Argonian snout; that needs a fitting step. |
| Movable clutter (bowls, jars, baskets) | about 85% | The collision is re-fitted if the size differs much. |
| Furniture (mats, beds, stools) | about 80% | The new lying or sitting surface must be within about 5 cm of the donor's height. |
| Lanterns and other lights | about 80% | The flame must sit at the new wick. |
| Harvestable plants; containers with fixed lids | about 60% | The picked and unpicked states must keep their names. |
| Doors and things with moving parts | about 40% | The moving part must keep its pivot. |
| Bows and crossbows | about 10% | The limbs and string are animated. |
| Full outfits | about 10% | The cloth must bend with the body. |

**Spears confirm your instinct.** Our spear mods already treat a spear as a greatsword and a short spear as a
sword. A new spear would "act as a greatsword": easy to make, but it sweeps and never thrusts, and long thin
hafts are a known generator weakness. I would leave spears out.

**Two more routes need even less:**

- **Texture only.** A banner, a standard or a door sign is a flat image on a model we already hold. The record
  can point an existing model at a new texture without touching the model.
- **Replace the file for the whole province.** A new model saved over the vanilla bedroll's path changes every
  bedroll in every source place at once, with no record work and no place edits. It would also change Imperial
  and Dunmer camps; a record-level swap by culture is the finer tool where that matters.

## 5. The four options

Each option includes the one before it. Fees are Fal's; agent work is extra and unmeasured.

### Do nothing

The rule stays. The audits' free findings still stand as ordinary work (below, "least, part A"), but nothing
new is made.

- **Benefit:** no risk, no policy question, no time off the story.
- **Cost:** the tells in section 1 stay. The tribes keep differing by tint only.

### Do least: no new models

**Part A needs no rule change and no art.** I would do this whatever you decide.

1. **A swap table for Argonian places**, using Argonian models we already hold: the vanilla candle lantern
   (173 placements in six drafts) to the Argonian lanterns; Nordic-ruin and Solitude doors (56 of 119 doors)
   to King of the Murkmire's mud, thatch and bamboo doors where the frame fits; hide tents to the scale tents;
   shrines of the Nine to the Hist shrine; generic banners to the Argonian banners. This is your ruling of 20
   November ("an easy swap is taken where there is one") made into one table.
2. **Place what we hold and never placed:** King of the Murkmire's saltrice (the "saltrice marsh" regions show
   none), five giant cypress knees, two bamboo models, and the Dragonborn giant mushroom trees for the fungus
   floors. These appear at the next world rebuild you ask for.
3. **Add the Nexus mods in section 2** after reading their pages.
4. **Fix the holes the audit found in our own tables:** the three tribes pointed at armour that does not exist;
   the 12 trade kits with no clothing row; the town guard's cuirass with no dropped model; two reward outfits
   with no item rows.

**Part B is flat images only**, and needs a small change to the rule (today a Fal image is allowed only as one
small piece you ask for):

5. **A standard for each of the 18 cultures and a sign for each of the nine story lines**, plus the Company
   standard and a pirate flag: about 30 emblems on the vanilla banner model and as door signs. The 18 emblems
   are new lore, so each would cite the tribe's lore and you would judge them on one sheet before any is used.
6. **Recolours by code, not by image model**, as we already do for bamboo leaves: a sick and a dying Hist, marsh
   dyes for the six vanilla commoner outfits, a colourway per tribe for the totems.
7. **A wet-wood retexture of the vanilla barrels, crates and sacks**, the largest family of generic pieces.

- **Fal fees:** under $30.
- **Benefit:** every culture and story line gets a mark the player can learn; the most-placed Nordic pieces in
  Argonian places go; the marsh regions gain rice, knees and fungus. Low risk, because nothing new has to
  work in the engine.
- **Cost:** weapons, bedrolls, boats and the lore objects stay as they are.

### Do more: about 48 small solid models (recommended, after the pilot)

**First a pilot of three**, each taken into the game for your check, about $10 of fees:

| Pilot model | Proves |
|---|---|
| Crocodile-tooth club, acting as a mace | the weapon swap: grip, swing, sheath, drop |
| Carved grave-stake | a new static prop with collision, and how a generated texture looks beside Skyrim's |
| Reed sleeping mat, in the bedroll's file | the furniture swap: a person lies on it correctly |

The pilot also builds the tooling once: Blender on the build machine, the swap step in our own model tool,
texture conversion, and a record template per kind. It measures the agent cost per model, which I cannot
estimate today.

**Then the batch**, every item small, solid and without moving parts:

| Group | Models | Count | Acts as, or route |
|---|---|---|---|
| Bog-iron weapons, replacing the relabelled vanilla ones | sword, dagger, war axe, mace, greatsword | 5 | the same vanilla type |
| Tribal weapons | jade sword, jade dagger, flint war axe, crocodile-tooth club, crocodile-tooth maul, toothed sword, Naga-Kur bone sword and dagger, eel gaff, obsidian-edged heavy club | 10 | sword, dagger, war axe, mace, warhammer, sword, sword and dagger, dagger, battleaxe |
| Shields | turtle shell, reed wicker, bone boss | 3 | shield |
| Grave-stakes | skull, glyph, serpent, twinned, small | 5 | new static |
| Hist tending | sap jar, sap tap, gourd, Hist seed pod | 4 | movable clutter and static |
| Eggs | egg clutch in a shell cup, two sizes | 2 | static, replacing the dragon eggs |
| Sleeping | reed mat, two weaves | 2 | the bedroll's file |
| Household | clay pot, gourd jar, wicker fish basket | 3 | clutter and container |
| Fishing | weir section, fish trap, net drying rack | 3 | new static |
| Boats | dugout canoe, bundled-reed raft, moored | 2 | new static, not rideable |
| Shore and swamp | hollow log, snag, stump, half-sunk trunk, two driftwood piles | 6 | new static |
| Mounds | clay, mud and termite mound | 3 | new static |

- **Fal fees:** 48 models at $1.00 to $2.70 is $50 to $130. I would cap it at $200 to allow for more retries
  than the estimate assumes.
- **Benefit:** the commonest weapons, the bed every camp sleeps on, the boats at 22 raft stops, the grave-stake
  in 137 lived-in places, the two Act I weirs and the Hist's own gear all become Black Marsh's. Tribal camps
  get weapons of their own.
- **Cost and risk:** the tooling is new and one link is unproven (the pilot settles it). Generated textures
  may not sit well beside Skyrim's (the pilot shows it). Each new prop still has to be placed by the place and
  stock skills, and scattered props reach undrafted places only at a world rebuild.

### Do most: about 60 more, harder

Everything above, plus the medium and hard kinds. Fal fees about $150 to $250 more. I would not approve this as
a block; pick from it once the "more" batch has shown what the pipeline does well.

| Group | Models | Why it is harder |
|---|---|---|
| Head ornaments and masks | feather crests, horn caps, frill clips, two masks | each must be fitted to the Argonian head |
| Necklaces and rings | tooth, jasper and pearl necklaces; shell and jade rings | the necklace bends with the chest |
| Faith and memory | three Sithis shrines, a Hist stele, three tablets, a chime tree, four new totems | larger carved shapes |
| Mangrove roots and tree ferns | four root clusters, three fern trunks | a generated trunk joined to an existing tree's leaves so it still sways; needs distant-view models |
| Marsh plants | reeds, cattails, sedge, lily mats, hanging moss | flat cut-out cards built by hand from a Fal image; no 3D generator involved |
| Bigger boats and wrecks | twin-hull canoe, houseboat, four wreck hull sections | size: one texture stretched thin, walkable decks |
| Fungus, coral, bones | four each | narrow regions |
| Working pieces | hammock, kiln, clay wall, reed tent | hut-sized or needs a raised sleep marker |

### What I would not do at any level

- **Houses and hut kits.** King of the Murkmire holds about 200 hut, stockade and house pieces; size is the
  generator's weakest point; and buildings need walkable collision and walking meshes.
- **The root-grown house.** It is a real gap for the 19 Root-Folk places, but it is a whole building kit.
- **Full outfits and anything cloth.** See section 6.
- **Bows, crossbows, blowguns, and spears with a thrust.** All need animation work.
- **The ball court and the banyan.** Rare, or not in our lore.

## 6. The honest gap: clothing

Clothing is the largest hole the audit found and the one this pipeline helps least. A loincloth, wrap or robe
has to bend with the body and tail, which means weight-painting to the skeleton and a second fit for Argonian
heads and tails. Generated cloth wrapped on a body is the hardest case there is.

What can be done, in order of value for effort:

1. Fill the 12 trade kits that have no clothing row from what we hold (part A).
2. Try Saxhleel Sundries and the straw hats in game before trusting them.
3. Marsh-dye recolours of the vanilla commoner clothes, by code (part B).
4. Rigid ornaments on top of plain clothes: feather crests, horn caps, masks, necklaces (the "most" list). A
   villager in a dyed tunic with a tooth necklace and a feather crest reads as Black Marsh far more cheaply
   than a new outfit would.

Even with all four, dress will be the weakest part of the province's look. If it matters most to you, the
answer is a human-made clothing mod or a commission, not this pipeline.

## 7. Risks and what would have to change

- **King of the Murkmire's terms.** Its author asks that add-ons not use AI, and your permission of 24
  September is what covers us today. Putting AI-made models beside its buildings in 40-odd places is a step
  beyond what that permission was given for. I would never use its files as donors or as the base of a
  retexture (vanilla donors only), and I think it is worth one plain question to the author before the "more"
  batch. That is your call and your relationship.
- **Look.** A generated texture can read as pasted in beside Skyrim's. The guard is that you see every
  reference image on a sheet before a model is made (a few cents each), and every model on a card before it
  is placed.
- **The unproven link.** If the pilot fails on the build machine, the fallback is the Windows play machine
  with the standard Blender exporter, which costs machine time.
- **Thin shapes.** Stakes, staffs and gaffs sit near the generator's weak side. Stakes are thick enough to be
  fine; I would drop any model that fails twice instead of fighting it.
- **Placement is separate work.** A model in the pool changes nothing until the stock ladder, the dressing
  rules and the drafted places use it. Drafted places take it by a narrow change; the rest of the province
  takes it at a world rebuild, which runs only when you ask.
- **Labelling.** If the mod is ever published on Nexus it carries the AI-generated label. It already would,
  for the music.
- **Where the files live.** Like the soundtrack: built, stored outside the repository, one row in the mod
  list, with every prompt and request recorded. Nothing binary is committed.
- **The rule.** Decision 0006 point 5 and the "Never make art" line in CLAUDE.md would be amended to name
  exactly what is allowed (flat images on existing models; small solid models by template swap or as static
  props), and what stays banned (section 5's last list).

## 8. The ten best returns, in order

1. The swap table for lanterns, doors, tents, shrines and banners. No art.
2. Standards for the 18 cultures and signs for the nine story lines. Flat images.
3. The reed sleeping mat in the bedroll's file. One model changes every camp.
4. Bog-iron and tribal weapons by swap. The commonest things in every hand.
5. Grave-stakes. The lore's best repeatable object, in 137 places.
6. The dugout and the reed raft. Twenty-two raft stops with no native boat.
7. Clothing rows, the two clothing mods and dye recolours. The biggest hole, the cheapest partial fix.
8. Shields of turtle shell and reed.
9. The fish weir kit. Two Act I places are named for weirs.
10. Sap jar, sap tap and a real egg clutch, with saltrice, cypress knees and mushroom trees placed.

## 9. What I need from you

One choice: **nothing, least (part A only, or A and B), more, or most**. My recommendation is part A now, part
B with the small rule change, and the three-model pilot as the gate to "more". And one yes or no: whether to
ask King of the Murkmire's author before AI-made models go in beside its buildings.
