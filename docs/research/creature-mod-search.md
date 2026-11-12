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

## Result (2026-11-12)

Taken: Dreughs 139898, Otters 49518, Better Bats 33789 (owner), Kagouti 27521, Giant Leeches 104589,
Blue Whales 47619, LamiaEnemies 50880, Gorgons and Medusa 100485, Nix-Hounds 54358.

No SE mod found for: sea-lion (Mihail's seals are not on SE; 49700 is a patch for them), manta-ray (88505's rays
fly), flying-fish, mudskipper, osheeja-gar, death-hopper, feather-serpent, hoarvor, kaj-thux, barracuda, moray,
sea-snake, mosquito, ibis, heron, parrot, wild monkeys. Found but not taken, as the kind already has a true fit:
giant snakes 36548, frogs 120998, sea turtles 122141, Marsh Leviathans 86261 (a spinosaurus).
