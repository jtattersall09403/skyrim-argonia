# Ecology: creatures, hostile people and harvestables between places

The recipe for what lives in the new world between its places, and how the rebuild puts it there. The phase is
[nw-03b](../phases/new-worldspace-plan/nw-03b-ecology-creatures.md); danger bands are [danger](danger.md).

## Sources

- `newworld/sources/ecology/regions/<region>.json`: each region's creature rows (kind, size class insect, small,
  game, predator or giant; hostility; habitat; group range; signature; the lore it is cited from) and its lore
  harvestables. A kind is a signature in at most two regions.
- `newworld/sources/ecology/bindings.json`: each kind bound to real NPC_ records of the plugins we hold, weakest
  first (`levels` gives their census levels, a relative order only), or dropped with its reason; each lore-backed
  hostile group of `npc_encounters.json` bound the same way. Never an invented record. Measured: 68 of 96 kinds
  bound to 167 records, 28 dropped (effect-only swarms; critters that are activators, not actors, such as torch bugs;
  kinds no mod models, such as dreugh and lamia); 38 of 39 people groups bound: the Naga, the tribal
  Argonians and the undead to King of the Murkmire and Curse of Cipactli records, every bandit, raider, deserter,
  smuggler, pirate, salvager and slaver group to whole bandit-faction records of the Argonian, Dunmer, Imperial,
  Khajiit, Redguard, Orc, Breton and Bosmer of Skyrim, Dawnguard and Dragonborn (`tools/newworld/ecology/people.py`;
  Skyrim's templated bandit lists are never used, they resolve to Nords). The one left out is the Velothi undead of
  Chixathe Mesa: the held plugins' Dunmer dead are unique ghosts, none a generic actor.
- `newworld/sources/ecology/skyrim_measures.json`: Skyrim's own numbers (decision 0034): creatures per 100 cells
  shore 77, forest 60, mountain 14, open 12, water 8; 38% hostile; mean group 1.56.
- `tools/newworld/ecology/census.py` lists every creature, race, LVLN and harvestable per plugin
  (out/newworld/ecology/census.json); bindings are checked against it.

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
where 20 or more are expected. The readback (`verify.py`, part `ecology`) proves each actor is in the written file
at its id, place and cell, and each band actor's level is fixed and its band's.

Measured on the small world (16 x 16 cells; arnesian-jungle, chixathe-mesa, valley-of-storms): 106 actors (D1 6,
D2 44, D3 56), 68 band actors, Dunmer slavers among the people; hostile blows by band, mean D1 6.6, D2 20.4, D3 28.7,
peak 11, 35, 91;  forest 28 against 32 expected, shore 37 against 40,
open 10 against 13, mountain 10 against 7; largest overlap of two regions' kinds 0.08. The province, at the same
rates over its cells, holds about 25 per 100 land cells at D2, twice that at D5.

## Harvestables

The flora stage already places 31 King of the Murkmire FLOR bases with ingredients, 35,343 refs. Per 100 cells of
each region (all its cells, water included): swamp and forest regions 104 to 377 (Murkwood 327, Nushara Bayou 355,
Ultherus Swamp 377, Barsaebica 241), within Skyrim's forest 386 and shore 460; drier and island regions lower
(Valley of Storms 50, Chixathe Mesa 66, Althii 61, Aphon and Skeith 13 to 14); the sea regions 4 to 18, against
Skyrim's water 75. Each land region grows 12 to 22 harvestable kinds, more than its lore list of 5 to 7. No new
harvestable is added: the lore lists name ingredients by lore name, and binding them to existing FLOR and INGR
records region by region is the open step, with sea harvestables the first gap.
