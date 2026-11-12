# Finding a creature mod for a lore kind

How to find a real actor for a lore creature kind the mods we hold do not cover, or cover only by a nearest fit
(`newworld/sources/ecology/bindings.json`: `dropped`, or a `why` that says nearest).

## Method

1. List the wanted kinds: every kind in the 24 region files (`newworld/sources/ecology/regions/`) whose binding is
   dropped or nearest.
2. Search Nexus Skyrim SE by every name of the kind: the lore name, its ESO name, its Morrowind or Oblivion name,
   the real animal and its family (`python3 tooling/nexus_search.py <term> ...`: GraphQL name search, most endorsed
   first, translations and patches dropped). Web search finds few ids; the API finds them.
3. Sweep the big creature authors by series name: Mihail ("Mihail Monsters and Animals"), Skinwalker21 ("Animal
   Series", "Creature Series", "Prehistoric Content Series"), Pixie, Chakra, Vicn; and the Creation Club plugins
   already in `Data` (`cc*.esm`).
4. Read each candidate (`python3 tooling/nexus_search.py --mod <id>`): SE or AE, standalone (not a replacer, not
   tied to another worldspace or quest), requirements, scripts, file size, and the page's permission text.
5. Take a mod when it is a true fit for a kind not already well met, standalone, and its page allows use as a
   requirement (or states nothing: the player downloads it; nothing is redistributed, decision 0003). A mod the owner
   names is approved. Drop a candidate that duplicates a kind already bound to a true fit.
6. Fetch with the stack's Nexus route, lay it asset-only (assets under `~/games/skyrimse/newworld-assets/<id>`, the
   plugin in `Data` for reading), check every script its records name is shipped, bind, rerun the census.

## The loop

The roster test (`python3 -m tools.newworld.ecology.roster_check`, [ecology](../design/ecology.md)) is the exit.
Each round: list its failures per region; re-author each kind no model fits to a creature that fills the same niche
there (cited, or stated as extrapolation), first from the census's unused creatures; search and source for the rest;
bind; rerun. Stop when it passes, or when two rounds add nothing.

## Result

Taken: Dreughs 139898, Otters 49518, Better Bats 33789 (owner), Kagouti 27521, Giant Leeches 104589,
Blue Whales 47619, LamiaEnemies 50880, Gorgons and Medusa 100485, Nix-Hounds 54358, Giant Spider Crabs 49521,
Goliath Groupers 49523, Tuna 58749, Shroom Beetles 69828, Megalania 109174, Hummingbirds 78759, Anglerfish 87250,
Sabertooth Salmon 60270, Megalodon 59005. Census creatures put to use: King of the Murkmire's snails, Curse of
Cipactli's rootworm, spike-ox and mudrunner, Skinwalker21's small leeches, Dawnguard's Spriggan Earth Mother.

Re-authored, as no SE model exists: sea lion to sea otter, manta ray to goliath grouper, barracuda and sea snake to
anglerfish, moray to megalania, osheeja gar to sabretooth salmon, hoarvor to swamp leech, feather-serpent to
kaj-thux, fleshfly larvae to giant snail, heron to kingfisher, ibis and tern to shorebird, parrot to hummingbird,
mangrove and hermit crab to giant spider crab, glowgill guar to kagouti, fire drake to swamp wyvern, giant wasp to
giant mosquito, dragonfly to meganeura. Searched without an SE actor model: sea lion, seal, manta, stingray,
barracuda, moray, sea snake, mosquito, wasp, hornet, heron, egret, ibis, flamingo, pelican, crane, parrot, macaw,
iguana, gecko, gar, pike, monkey, haj mota, hermit crab (Mihail's terns 90518 are critter activators, not actors).
Found but not taken, as the kind already has a true fit: giant snakes 36548, frogs 120998, sea turtles 122141,
Marsh Leviathans 86261 (a spinosaurus), Giant Gastropods 98488 (King of the Murkmire's snails serve).
