# Ecology: creatures, hostile people and harvestables between places

The recipe for what lives in the new world between its places, and how the rebuild puts it there. The phase is
[nw-03b](../phases/new-worldspace-plan/nw-03b-ecology-creatures.md); danger bands are [danger](danger.md).

## Sources

- `newworld/sources/ecology/regions/<region>.json`: each region's creature rows (kind, size class insect, small,
  game, predator or giant; hostility; habitat; group range; signature; the lore it is cited from) and its lore
  harvestables. A kind is a signature in at most two regions.
- `newworld/sources/ecology/bindings.json`: each kind bound to real NPC_ records of the plugins we hold, weakest
  first (`levels` gives their census levels, a relative order only), or dropped with its reason; each lore-backed
  hostile group of `npc_encounters.json` bound the same way. Never an invented record. Measured: 85 of 97 kinds
  bound to 209 records, 11 bound to critter spawners and swarms (below), the cave bat waiting on its spawner
  (Skyrim's bat activator); no binding is a nearest fit (the roster test below); 38 of 39 people groups bound: the Naga, the tribal
  Argonians and the undead to King of the Murkmire and Curse of Cipactli records, every bandit, raider, deserter,
  smuggler, pirate, salvager and slaver group to whole bandit-faction records of the Argonian, Dunmer, Imperial,
  Khajiit, Redguard, Orc, Breton and Bosmer of Skyrim, Dawnguard and Dragonborn (`tools/newworld/ecology/people.py`;
  Skyrim's templated bandit lists are never used, they resolve to Nords). The one left out is the Velothi undead of
  Chixathe Mesa: the held plugins' Dunmer dead are unique ghosts, none a generic actor.
- `newworld/sources/ecology/skyrim_measures.json`: Skyrim's own numbers (decision 0034): creatures per 100 cells
  shore 77, forest 60, mountain 14, open 12, water 8; 38% hostile; mean group 1.56.
  Its `critters` section: per critter spawner base Skyrim places (insects, pond fish, dragonflies, birds) the refs
  per 100 cells of each class, where they stand against water and harvestable plants, and the hours its spawn
  script runs; and how many times denser King of the Murkmire places spawners than Skyrim (`black_marsh.factor`).
- `tools/newworld/ecology/census.py` lists every creature, race, LVLN and harvestable per plugin
  (out/newworld/ecology/census.json); bindings are checked against it.

## The roster test

`tools/newworld/ecology/roster_check.py` holds every region's roster to the owner's "full range, as wide as
possible, rich and alive", and exits 1 on any failure. Per region:

- a. Kinds per size class at least: land tiny (insects and critters) 2, small 3, game 2, predator 3, giant 1; sea
  tiny 1, small 3, game 1, predator 2, giant 1.
- b. On land, a benign and a hostile kind among the tiny, the small and the game (defensive counts as hostile: it
  fights back); predators and monsters are hostile by the lore.
- c. At least 4 kinds no bordering region has (borders: 3 or more shared cell edges in `cell_region.json`), and no
  two regions sharing more than half their kinds (Jaccard, the stage's own bound).
- d. Each water kind of the region (fresh, brackish, salt; 20,000 m2 or more in `water_classified.json`) has a
  swimmer of that water.
- e. Every kind bound to a true model: records or a critter base; never dropped, never a `why` that says nearest or
  stand-in. A lore name may bind to the same animal under another name (kaj-thux to the giant snakes, haj mota to
  the armoured turtles, death hoppers to large frogs).
- f. Province-wide, distinct actor kinds placed at least the 38 creature races Skyrim.esm places in Tamriel (every
  ACHR resolved through its lists).

A kind no mod models is re-authored: another creature that fills its niche in that region, from the lore or stated
as extrapolation, first from the census's unused creatures, then searched and sourced
([creature-mod-search](../research/creature-mod-search.md)). Measured: 97 kinds over 24 regions, 85 actor kinds
against Skyrim's 38; largest overlap of two regions 0.5. The cave bat is Skyrim's own bat colony activator
(`FXbatGroupACT`) bound as a critter (`bindings.json` `critter_kinds`, function `bats`): it carries no spawn hours, so
the bat is always out, and it stands on the kind's rock ground at Skyrim's rate for it (two refs in Tamriel, in
forest and mountain cells).

### Kinds no model exists for

Each lore kind with no Skyrim Special Edition actor model is either bound to the nearest honest fit, said so and why,
or left out. Searches that found no actor model are listed in the search record's Result section.

| Lore kind | Fit | Why |
|---|---|---|
| sea lion | sea otter (Otters) | a swimming fur-coated shore hunter of the same size class; no sea lion or seal model |
| manta ray | goliath grouper | the lore's big, slow, harmless filter swimmer of the shallows; no ray model |
| barracuda | anglerfish | a fish predator that ambushes from the water; no barracuda model |
| sea snake | anglerfish | the same niche, a fish-shaped predator of the sea; no sea snake or eel model |
| moray | megalania (Megalania) | a lurking ambusher at the water's edge; no eel model |
| osheeja gar | sabretooth salmon | the lore's long-toothed river fish; no gar or pike model |
| hoarvor | swamp leech | a bloodsucker of the standing water; the leech is Giant Leeches' |
| feather-serpent | kaj-thux (giant snakes) | the same snake under another name in the lore |
| death hopper | large frogs | the lore's death hoppers are large frogs: the frog mod models them true |
| mosquito | giant mosquito | the big biting insect; a critter swarm stands for the small ones |
| ibis, heron | shorebird, kingfisher | the nearest wading and fishing birds the load order carries |
| parrot | hummingbird | the nearest small bright bird; no parrot model |

Flying fish and mudskipper are critters (shallow-water fish school, and the nearest the water spawner gives).
A kind with no honest fit in its region is left out of that region's roster: the roster test then holds the region to
its size-class floors with the kinds that remain.

## The stage

`ecology` (tools/newworld/ecology/place.py) runs after `navmesh` and `map`, and only `esm` reads it. It writes
`out/newworld/plugin/ecology/`, beside `refs/` and never in it: everything under `refs/` feeds the navmesh and its
key, and an actor is no obstacle; nothing of it reaches the LOD.

A cell (never a margin cell, a held cell of a built place, or a teleport landing's cell) is filled so:

1. Its class as Skyrim classed its cells: water (most samples water), shore (some water), mountain (rock habitats
   most), forest (canopy), open. It takes a Poisson draw of Skyrim's creatures for that class, times its band's
   density: D0 0.5, D1 0.8, D2 1, D3 1.25, D4 1.6, D5 2.
2. Groups are drawn until that number is met. A group is hostile with its band's share (D0 none, D1 0.15, D2 0.38 as
   Skyrim, D3 0.5, D4 0.65, D5 0.8). Its kind is drawn from the region's rows of that temper whose ground the cell
   holds, signature rows twice as likely, weighted by the band's size weights: low bands mostly insects and small
   animals, giants only from D3, predators and giants most of D5. Group size from the row's range, larger in high
   bands. A cell holds at most 4 (D0) to 18 (D5) actors.
3. Ground by habitat: walkers on dry ground under 35 degrees, off road surfaces and place pads; marsh kinds on marsh
   habitats and shallow fresh water; bush kinds within 4 m of a placed understorey, fern or reed; canopy kinds under
   canopy; rock kinds on rock habitats; shore kinds on beach and mangrove or within 15 m of water; swimmers in fresh,
   brackish or salt water of their kind at least 1.5 m deep, at mid-depth; insects of the water over its surface.
   Hostiles keep 30 m off roads, and the cell's band is already lower near roads and towns.
4. The record by band from the kind's list, weakest in D0 and strongest in D5. Its band copy (one NPC_ per record
   and band, `ANW_Eco_<source>_<band>`) has a fixed level, the band's foe level times the size class's share
   (insect 0.4, small 0.6, game 0.8, predator 1, giant 1.25), never the player's (decision 0035; no PC level
   multiplier, no stats template, no levelled list), health times the band's (0.6 to 2.8), and the mod's own AI.
   Variety comes by chance in direct placement, as Skyrim's fixed placements do.
5. Hostile people: in D2 and over, a land cell holds a roaming group of its region's bound lore groups with chance
   1% (D2) to 4% (D5), 2 to 6 strong by band, on open dry ground, at the band's foe level.
   Each member's look is a flat draw from its people's looks (at least 4 existing NPC_ records of the lore's race
   and both sexes, their own faces; no FaceGen work), and its kit a flat draw from its band's gear tier (low D2,
   mid D3, high D4 and D5; at least 2 sets each): a flat outfit of a plugin we hold, or our own outfit of listed
   armour (the world writer wears it) and weapons and ammunition (it gives them, replacing the record's own items:
   outfits cannot hold weapons), never a levelled list. A look is never Nord: no unique person, no Nord voice type,
   no record whose face comes from a template list. Kit is what that people would own, its value rising with the band:
   Naga from Naga hide to Naga elite (mean value 18, 392, 940); tribal Argonians from Saxhleel leather to An-Xileel
   reel armour (162, 538, 949); Veeskhleel and Hist zealots their robes, mage kit and masks; undead their own bones.
   Outlaws, raiders and prospectors hide, leather and iron, then steel and banded, then steel plate and scale with
   two-handed steel; deserters worn Imperial issue, the officers' plate last; pirates and wreckers leather, scale and
   a captain's elven blade; smugglers light, quick kit and elven at the top; Orc raiders iron then orcish; Dunmer
   slavers leather and bonemold, then chitin, then heavy chitin and improved bonemold. Nothing Nordic. The check
   holds each group to 4 looks and 2 sets a tier, its mean value rising tier on tier, no Nord voice among its looks
   and no Nordic piece in its kit.

6. Critters, the tiny life: Skyrim places insects, fish and birds as refs of critter spawner activators (ACTI with
   the `critterspawn` script: up to a few critters inside a leash, within the hours of its script), not as actors.
   A lore kind that is such a creature binds to one base (`bindings.json`, `critter_kinds`: `critter`, its `function`, its `time`; the kind stays dropped as an actor in `kinds`):
   night kinds (torchbugs, moths, fire beetles) to a night-only insect spawner (20 to 23 h), day kinds to the bee,
   dragonfly or shallow-fish spawner (hours as the base runs), kinds of no hours to the swarm record that exists
   (Black Marsh's Flesh Flies, for gnat clouds, midges and flies; a fixed critter, so its kind's time is dropped).
   A kind's `time` is honoured only by choosing the base whose hours fit; a row never takes a spawner of the other
   time. Only bases of Skyrim.esm and Black Marsh.esm, linked as masters with their own script and hours, never
   copied. A cell draws per function (`critter_functions`: insects, dragonflies, pond fish) a Poisson count at
   Skyrim's spawners per cell of its class for that function's bases, times the King of the Murkmire factor, each
   of one of the region's kinds of that function whose ground the cell holds (signature rows twice as likely) on that
   ground: insects over their habitat or the water's surface, fish on water of their kind at the surface. No band
   thins them; at most 8 a cell. Every region whose lore lists such a kind has its spawners.
   They are written to `ecology/critters/cy<+NNN>.jsonl` (one REFR a line) and the world writer places each as a
   REFR of its base, id in the ecology range.

Every draw is seeded by the cell, so a rerun writes the same bytes. Each actor's id is in the `ecology` range of
tools/newworld/idspace.py (0xF00000..0xFDFFFF), its identity's digest (cell, kind, ordinal), probed on a collision.
The world writer (NewWorld.cs `Ecology`) copies each band actor's record whole into the world file (ForeignCopy:
race, skin, armour addons, spells, factions and sounds follow; a link into the source plugin's world or story,
placed references, cells, quests or dialogue, is nulled) and writes each actor as an ACHR.

## Toughness by band

Damage rises with the band as health and level do, as Skyrim scales its fixed-level variants. Skyrim's creatures hit
by their race's unarmed damage (`toughness.json`, measured from Skyrim.esm: skeever, wolf, fox, mudcrab and spider 5;
goat 7.5; horker 15; brown and black bear 30 and 35; troll and sabre cat 35; snowy sabre cat 45; giant 60; frost troll
and mammoth 65; by size class insect 5, small 5, game 11.25, predator 35, giant 65), and a stronger variant of a kind
is its own record carrying an ability that adds to that damage (`AbFortifyUnarmedDamage`: the dragons' tiers +25,
+75, +125, +175, werewolves +5 to +25, vampires +5 to +20, the large and giant mudcrabs +15 and +20). Each band copy
of a creature carries our ability of that kind (`ANW_Eco_UnarmedDamage<magnitude>`, one per magnitude, written by the
world writer) adding size class base times (band factor - 1), factors D0 to D2 1, D3 1.4, D4 2, D5 2.8: a predator's
blow 35, 35, 35, 49, 70, 98 and a giant's 65, 65, 65, 91, 130, 182. D0 to D2 take no ability: their weakness is the
low level, the low health and the weakest record of the kind first. Bands D0 and D1 hold no predator or giant (size
weights), and a D1 hostile never lands more than 15 in one blow, so nothing of the first band can kill an early
character; a D5 predator or giant lands 98 to 182, lethal to an early character's 100 health, trivial to a
strong one. People hit with the weapons of their kit tier (iron or hide, steel, steel two-handed, elven or orcish), so
their damage rises with the band through the kit's weapon value. Nothing reads the player's level: a creature's
damage is a function of its band and size class alone, its level fixed, no level multiplier, template or list.
The check asserts all of it (`toughness.py check`): each actor's bonus is its band's, no D1 hostile over 15, the peak
and mean blow rise with the band, the table's D5 blow is lethal to 100 health and at least twice D2's, the people's
weapon value rises, and no actor carries a player-level multiplier, template or list.

## Checks

The stage's check (fails the stage): every actor on ground or water of its kind; none in a held, landing or margin
cell; no cell over its band's cap; no hostile in D0; levels as the band's; ids in range and once; no two regions
sharing more than half their kinds; creatures per class within 0.5 to 1.6 of Skyrim's measure times band density
where 20 or more are expected. For critters: every spawner on ground or water of its kind, on the base its kind
binds, a night or day kind on a spawner of that time, outside held cells, ids once and in range, at most 8 a cell,
no class over 1.6 times its rate, every region expected to hold critters holding some. The readback (`verify.py`, part `ecology`) proves each actor is in the written file
at its id, place and cell, and each band actor's level is fixed and its band's; and each critter a REFR of its base
at its id, place and cell.

Measured on the small world (16 x 16 cells; arnesian-jungle, chixathe-mesa, valley-of-storms): 106 actors (D1 6,
D2 44, D3 56), 68 band actors, Dunmer slavers among the people; hostile blows by band, mean D1 6.6, D2 20.4, D3 28.7,
peak 11, 35, 91; forest 28 against 32 expected, shore 37 against 40,
open 10 against 13, mountain 10 against 7; largest overlap of two regions' kinds 0.08. The province, at the same
rates over its cells, holds about 25 per 100 land cells at D2, twice that at D5.

## Harvestables

Skyrim counts as harvestable every placed FLOR or TREE that yields an ingredient (17,307 refs). Per 100 cells of each
habitat class it holds: shore 460, forest 386, mountain 79, water 75, open 12.5 (`skyrim_measures.json`). The flora stage
places King of the Murkmire FLOR bases and ingredient-bearing trees with the plants of each region's habitats;
`tools/newworld/ecology/harvest.py` (the second command of the `ecology` stage) binds each region's lore plants to records
and brings every region to Skyrim's density for its classes. It writes `ecology/harvest/`, never `refs/`: the flora stage,
the LOD plan and the navmesh are not touched.

- `newworld/sources/ecology/harvestables.json`: the kinds (each a list of real FLOR, TREE or ACTI records of Skyrim and its
  DLC, King of the Murkmire and the Cipactli jungle; never a Nordic name), the lore map (each lore ingredient of the regions'
  tables is a kind, or a creature's drop with the reason), the class pools (Skyrim's own variety per class,
  `skyrim_bases_by_class_top`: barnacles, fish-egg nests and clams in the water; fungi, moss and roots on shore and in
  forest) and the new records. `harvest_bases.json` lists every ingredient-bearing FLOR and TREE of the plugins we hold and
  the two Nirnroot activators (`harvest.py catalogue` rewrites it from the game files); the check holds every kind to it.
- New records, where no record of ours had the plant: Marshweed, Flower Buds yielding Dried Flower Buds, Rootland Mushroom,
  and a Sugar Cane plant yielding Skyrim's Moon Sugar. Each is a FLOR or TREE copied from a mesh we hold under a Black Marsh
  name, yielding a new INGR (or Skyrim's) whose effects are existing ingredients' effects nearest the lore's
  (ingredients-alchemy.md); the world writer makes them (`NewWorld.cs` `Harvest`). Of the lore's 53 harvestables 18 are
  plants, fungi, eggs or shells and are bound; the other 35 are creature or daedra drops, taken from the creature, not placed.
  Kelp yields no ingredient in Skyrim, so none is placed.
- Placement: a region's target is Skyrim's rate for each of its cells' classes (classed as the creatures are); what the flora
  stage placed counts toward it. Each bound lore plant gets at least 2 per 100 cells (never under 6), net of the flora
  stage's, on the ground its lore row names, spread by that ground's area in each cell. The rest of the target is Skyrim's
  variety for the cell's class, the region's lore plants twice as likely, in the cells short of their class's rate. Grounds:
  the stage's masks (marsh, shore, canopy, bush, open, rock) and: a bank (dry within 6 m of water: Nirnroot), and a bed
  0.5 to 10 m under fresh, salt or brackish water of its kind (clams, oysters, barnacles, pearl oysters, fish-egg nests; the
  bed stands at the ground height). No two within 128 units; at most 60 a cell; never a margin, held or landing cell.
- The stage's check: every ref on ground of its habitat, in its region and cell, its base a record of the catalogue or ours,
  its id in the ecology range and given once; every region at or over Skyrim's class density; every bound lore plant of the
  region present at its quota; every lore ingredient bound or a drop. The readback (`verify.py`, part `ecology`) proves each
  ref stands in the written file at its id, place, cell and base.

Per region over the province's cells (`harvest.py run`): the flora stage's refs per 100 cells, the refs this stage adds,
the total per 100 cells, Skyrim's density for the region's classes, and its bound lore plants.

| region | cells | flora per 100 | added | total per 100 | Skyrim's | lore plants |
|---|---|---|---|---|---|---|
| althii-archipelago | 481 | 98.1 | 719 | 247.6 | 228.8 | small-pearl, dried-flower-buds, marshweed |
| aphon-isle | 143 | 21.0 | 234 | 184.6 | 164.1 | small-pearl |
| arnesian-jungle | 889 | 252.3 | 276 | 283.4 | 279.8 | hanging-moss, somnalius-frond, fly-amanita |
| aunike-ridge | 456 | 236.0 | 34 | 243.4 | 109.0 | giant-lichen, thistle-branch, birds-nest, white-cap, imp-stool, lavender |
| banujha-basin | 912 | 190.5 | 989 | 298.9 | 285.6 | nirnroot, marshweed, swamp-fungal-pod |
| barsaebica | 517 | 668.9 | 22 | 673.1 | 221.2 | swamp-fungal-pod, hanging-moss |
| benthic-yobesh | 400 | 32.5 | 186 | 79.0 | 75.5 | small-pearl |
| blackwood | 213 | 306.1 | 12 | 311.7 | 310.7 | - |
| cape-percar | 567 | 148.7 | 256 | 193.8 | 188.1 | thistle-branch |
| chixathe-mesa | 556 | 106.1 | 341 | 167.4 | 160.1 | giant-lichen, birds-nest, white-cap, imp-stool |
| hatandros-bight | 377 | 139.5 | 362 | 235.5 | 224.9 | lavender, moon-sugar, thistle-branch |
| kotherra-mangroves | 195 | 154.4 | 415 | 367.2 | 339.6 | marshweed |
| lake-ulaish | 391 | 204.1 | 16 | 208.2 | 184.3 | nirnroot, marshweed |
| murkwood | 1234 | 363.9 | 100 | 372.0 | 297.0 | rootland-mushroom, swamp-fungal-pod, hanging-moss, somnalius-frond |
| nha-enasa | 505 | 328.5 | 33 | 335.0 | 202.9 | nirnroot, marshweed, dried-flower-buds |
| nushara-bayou | 765 | 466.4 | 16 | 468.5 | 268.4 | marshweed |
| okuwun-rahei | 1081 | 255.5 | 66 | 261.6 | 253.2 | dried-flower-buds, nirnroot, marshweed, thistle-branch |
| padomaic-ocean | 588 | 115.1 | 12 | 117.2 | 78.1 | small-pearl |
| sea-of-mists | 526 | 109.9 | 11 | 112.0 | 79.8 | small-pearl |
| skeith-isle | 149 | 65.8 | 130 | 153.0 | 142.2 | small-pearl, giant-lichen |
| topal-bay | 491 | 2.0 | 388 | 81.1 | 76.3 | small-pearl |
| tulmek-washes | 1279 | 96.6 | 2528 | 294.2 | 269.5 | nirnroot, slaughterfish-egg, marshweed |
| ultherus-swamp | 304 | 484.5 | 28 | 493.8 | 314.2 | dragons-tongue, swamp-fungal-pod, somnalius-frond, marshweed |
| valley-of-storms | 666 | 142.5 | 56 | 150.9 | 135.6 | nirnroot, marshweed, dried-flower-buds, swamp-fungal-pod |

Small world (arnesian-jungle, chixathe-mesa, valley-of-storms): 66 added, all three regions over Skyrim's density (243, 195
and 220 per 100 cells against 166, 97 and 219), every lore plant present, check and readback green.
