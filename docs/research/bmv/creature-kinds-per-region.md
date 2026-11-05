# Creature kinds per region: Skyrim.esm, the Black Marsh mod, and ours

Owner question (#37, 2026-11-03 08:55): is "12–21 kinds per region" at least as many kinds per equivalent-sized
region as Skyrim and the Black Marsh & Valenwood mod? The bar: at least as many. Read-only measurement, 2026-11-03.

## Answer

- **Against Skyrim.esm, by region of equal area: four of our nine region classes fall short, five clear it.**
  Skyrim's nine biome regions (600–1,650 cells each) hold 14–22 wild species. Ours of the same size hold 12
  (coastal-lagoon), 13 (northern-transition), 15 (western-frontier) and 25 (flooded-forest); the five smaller wet
  classes hold 15–23 over 45–1,315 cells, above any Skyrim region of their size.
- **Against the Black Marsh mod's main worldspace (26 wild kinds over 1,127 cells) only flooded-forest keeps up.**
  Its second worldspace is thinner (19 kinds over 3,230 cells, almost all of it empty).
- **On dry ground the gap is wider than the headline.** The D2–D3 land lists a walker draws hold 4 kinds on the coast
  (crow, fleshfly swarm, hackwing, marsh rat), 5 in the delta and river corridor, 7–11 elsewhere. Skyrim's land
  species per biome are 12–20. This is what the owner saw: the water and shore lists carry our variety.
- **Province-wide we have more kinds than Skyrim** (34 placeable against Skyrim's 23 wild + 5 domestic), but 15 of
  our 49 creature rows have no actor form (9 hand-authored, 3 domestic, 3 critters), and no domestic animal stands
  in any settlement; Skyrim places 5 domestic kinds in every settled biome.

## Method

- **Kind.** One species, not one form: Skyrim's three bears, two wolves, three spider sizes, spriggan and matron each
  count once (the collapse table is in the scratch script; counting every visual variant adds about 8 across the
  province). Ours: one `creature` row. The mod: one display name. Humanoids, named quest actors and test forms are
  out; domestic kinds are counted apart (`*`).
- **Region.** Skyrim: the `Weather*` REGN each Tamriel cell carries in XCLR (`tools/argonia_world/vanilla/load.py:116`;
  `NoPrecip` variants merged into their parent; the city sub-regions left out). The mod: its own two worldspaces,
  because its cells carry no REGN (scan: 0 XCLR entries in `BlackMarsh` and `BlackMarsh2`). Ours: `land_region`
  (political region × eco class, `cells` column) and the eco class the lists key on.
- **What counts as present.** Skyrim and the mod: every creature NPC_ reachable from an exterior ACHR in the region,
  levelled lists expanded to their leaves (`actors.Scan` from `tools/argonia_world/creatures/actors.py`;
  `is_creature` from `tools/argonia_world/vanilla/creatures.py`). Ours: the kinds in the class's lists
  (`creature_list_entry` → `creature_form` → `creature`) plus the apex kinds placed at dens
  (`creature_region_class` where `creature.kind = 'apex'`), the same union the lane report used
  (`docs/research/2026-11-03/lane-1.15-r4-creatures.md:89-92`).
- **Area blocks.** For "what a walker meets", species per 20×20 (400-cell) and 9×9 block of cells with LAND.
- Scripts (scratch, this session only): `skyrim_kinds.py`, `modregions.py`, `bmv_blocks.py`, `ours2.py`, `ours3.py`
  in `/tmp/claude-1000/-home-ubuntu-skyrim-argonia/7a2a2562-5de7-4599-9044-8aa607daefd9/scratchpad/`. They read the
  caches `~/.cache/argonia-vanilla/{tamriel,actors}.pkl`, the laid mod at `~/.argonia/stack/MO2/mods/bmv/` and
  `out/world.sqlite`; worth folding into `vanilla/creatures.py` and `creatures/checks.py` if the bar becomes a check.

## Skyrim.esm (Tamriel, 11,186 cells)

| Biome region (REGN) | Cells | Creature refs | Wild species | With domestic | Species |
|---|---|---|---|---|---|
| WeatherTundra | 1,286 | 783 | 22 | 27 | atronach, bear, chaurus, deer, dragon, fox, frost troll, frostbite spider, giant, goat, hagraven, hare, horker, ice wraith, mammoth, mudcrab, sabre cat, skeever, slaughterfish, spriggan, troll, wolf |
| WeatherSnow | 1,463 | 657 | 20 | 24 | bear, chaurus, deer, dragon, fox, frost troll, frostbite spider, giant, goat, hare, horker, ice wraith, mammoth, mudcrab, sabre cat, skeever, spriggan, troll, wisp, wolf |
| WeatherPineForest | 1,042 | 599 | 20 | 25 | bear, deer, dragon, fox, frost troll, frostbite spider, giant, goat, hagraven, hare, ice wraith, mammoth, mudcrab, sabre cat, skeever, slaughterfish, spriggan, troll, wisp, wolf |
| WeatherMountains | 1,652 | 209 | 18 | 21 | bear, deer, dragon, fox, frost troll, frostbite spider, giant, goat, hagraven, hare, horker, ice wraith, sabre cat, skeever, spriggan, troll, wisp, wolf |
| WeatherReach | 723 | 277 | 18 | 22 | bear, deer, dragon, fox, frost troll, frostbite spider, giant, goat, hagraven, hare, ice wraith, mudcrab, sabre cat, skeever, slaughterfish, troll, wisp, wolf |
| WeatherFallForest | 606 | 392 | 17 | 22 | bear, deer, dragon, fox, frost troll, frostbite spider, giant, goat, hagraven, hare, ice wraith, sabre cat, skeever, spriggan, troll, wisp, wolf |
| WeatherVolcanicTundra | 187 | 149 | 16 | 19 | bear, deer, dragon, fox, frostbite spider, giant, goat, hagraven, hare, mammoth, mudcrab, sabre cat, skeever, spriggan, troll, wolf |
| WeatherCoast | 1,461 | 367 | 14 | 15 | atronach, bear, fox, frost troll, goat, hare, horker, ice wraith, mudcrab, sabre cat, skeever, slaughterfish, wisp, wolf |
| WeatherTundraMarsh | 171 | 132 | 10 | 13 | chaurus, deer, fox, frostbite spider, goat, hare, horker, mudcrab, slaughterfish, troll |

Province: 23 wild species, 5 domestic (chicken, cow, dog, goat, horse). The regions overlap heavily: bear, deer, fox,
hare, skeever, wolf and troll are in nearly all of them. Per block of land: 20×20 blocks (n = 24) hold 0 / 10 / 13.5 /
16 / 20 wild species at min / p25 / median / p75 / max; 9×9 blocks (n = 129) hold 0 / 0 / 5 / 10 / 17.

## The Black Marsh mod (Black Marsh.esm, laid stack)

| Worldspace | LAND cells | Creature refs | Wild kinds | With domestic | Kinds |
|---|---|---|---|---|---|
| BlackMarsh | 1,127 | 411 | 26 | 31 | alligator, bear, centipede, corpse leech, crocodile, deer, dragling, drake, dreugh, dwarven centurion, forest drake, forest guardian, forest spider, giant leech, goat, hare, leech, lurker shark, mudcrab, restless dead, serpent, shark, slaughterfish, tree mother, viper, zombie (+ chicken, cow, dog, goat, horse) |
| BlackMarsh2 | 3,230 | 137 | 19 | 19 | alligator, ancient tree, crocodile, deer, dragling, forest drake, forest guardian, forest spider, leech, leopard, megalania, panther, red wolf, rhino, selkie, shark, tree mother, turtle, viper |

The mod's own forms are 61 NPC_ (inventory, `lane-1.15-creatures.md`); 12 of its wild kinds are vanilla or named
one-offs. Density is low and clumped: BlackMarsh2's 20×20 blocks hold 3, 4 and 6 kinds; in 10×10 blocks the median is
0 in both worldspaces (18 of 28 BlackMarsh2 blocks and 4 of 6 BlackMarsh blocks hold no creature). 121 of
BlackMarsh's 411 refs are one leech form.

## Ours (out/world.sqlite, the round-4 lists)

Per eco class, province-wide (`land_region.cells` summed; lists from `creature_list_entry`; apex from `creature_region_class`):

| Class | Cells | In lists | Apex dens | Total | Land | Shore | Water | D2/D3 land list |
|---|---|---|---|---|---|---|---|---|
| coastal-lagoon | 5,680 | 12 | 0 | 12 | 4 | 5 | 3 | 4 |
| western-frontier | 2,370 | 15 | 0 | 15 | 11 | 4 | 0 | 11 |
| northern-transition | 2,354 | 13 | 0 | 13 | 11 | 2 | 0 | 11 |
| flooded-forest | 2,545 | 21 | 4 | 25 | 9 | 10 | 2 | 9 |
| interior-swamp | 1,315 | 21 | 2 | 23 | 7 | 11 | 3 | 7 |
| deep-sink-basin | 773 | 19 | 3 | 22 | 7 | 9 | 3 | 7 |
| rootland | 744 | 18 | 4 | 22 | 11 | 6 | 1 | 11 |
| tidal-delta | 50 | 16 | 0 | 16 | 5 | 7 | 4 | 5 |
| deep-river-corridor | 45 | 14 | 1 | 15 | 5 | 7 | 2 | 5 |

Province: 34 placeable kinds (30 in lists + 4 apex), 15 rows without a form (feather-serpent, haynekhtnamet, lamia,
ripper eel, rootworm, shine, swamp leviathan, wispmother, xal-krona hand-authored; guar, lizard-steed, mouth-plover
domestic; osheeja gar, torchbug critters; medusa place-placed). Every political region reaches 31–34 kinds because
each holds several classes.

Per land region of 600 cells or more, the unit comparable with a Skyrim biome:

| Land region (map name) | Cells | Kinds | Nearest Skyrim region by size and ground | Its wild species | Gap |
|---|---|---|---|---|---|
| saxhleel-coast.coastal-lagoon (Archon Coast) | 2,783 | 12 | WeatherCoast 1,461 | 14 | −2 (−8 to −10 against the inland biomes) |
| dunmer-north.northern-transition (Shadowfen) | 2,354 | 13 | WeatherTundra 1,286 / WeatherReach 723 | 22 / 18 | −9 / −5 |
| imperial-fringe.western-frontier (Blackwood) | 2,179 | 15 | WeatherReach 723 / WeatherFallForest 606 | 18 / 17 | −3 / −2 |
| hist-heartland.flooded-forest (Middle Argonia) | 1,435 | 25 | WeatherPineForest 1,042 | 20 | +5 |
| mercantile-coast.coastal-lagoon (Oliis Bay) | 1,084 | 12 | WeatherCoast 1,461 | 14 | −2 |
| dunmer-north.coastal-lagoon (Shadowfen) | 786 | 12 | WeatherReach 723 | 18 | −6 |
| hist-heartland.coastal-lagoon (Middle Argonia) | 703 | 12 | WeatherFallForest 606 | 17 | −5 |

The mid-sized wet land regions (deep-sink-basin 90–145 cells at 22, interior-swamp 51–535 at 23, rootland 85–350 at
22, flooded-forest 68–372 at 25) all exceed WeatherVolcanicTundra (187 cells, 16) and WeatherTundraMarsh (171, 10).
Against the mod's BlackMarsh worldspace (26 over 1,127 cells) only flooded-forest (25) is level; against BlackMarsh2
(19 over 3,230) coastal-lagoon, northern-transition, western-frontier, tidal-delta and deep-river-corridor fall short.

What a walker meets, same block method: the lane's own "possible kinds within ±4 cells of each region shore marker"
(a 9×9 window) measured 15–27 after round 4 (`lane-1.15-r4-creatures.md:77-87`), against Skyrim's 9×9 median 5 and
max 17. On the shore we are rich; the shortfall is the dry-ground lists above and the empty settlements.

## Shortfall per Argonia region, and what could close it

Candidates only: every habitat widening needs its `creature_region_class.why` citation (0032), every new form a
sourcing-register row. "Have" = a form we already join (`roster.R`, `tools/argonia_world/creatures/roster.py:65`);
"mod" = a Black Marsh.esm form we do not use yet.

| Region (map name) | Short where | Candidates we have (widen habitat) | Mod forms, lore status |
|---|---|---|---|
| Archon Coast (saxhleel-coast) | coastal-lagoon 12, land list 4 | land: giant centipede, moon adder, bog dog, giant snail, jassa red slug; shore: singing frog, kotu gava; water: giant leech, swamp jelly | shark + lurker shark (pad-sa sharks, fresh and salt water to Topal Bay, `loading-facts.md:688`, canon); viper (red hooped tree-viper, `loading-facts.md:104`, canon); selkie, dragling, megalania: no dossier hit |
| Shadowfen (dunmer-north) | northern-transition 13 (Tundra 22, Reach 18); its lagoon 12 | marsh turtle, giant snail, jassa red slug, dragon frog, death hopper, haj mota and giant leech on its rivers, burglar crab, kaj-thux den | viper (canon); red wolf: the swamp wolf is extinct since 2E 10s (`loading-facts.md:689`), so no; drake (SoM_00EncDrakess): only sea-drakes in the dossier |
| Blackwood (imperial-fringe) | western-frontier 15 (Reach 18, FallForest 17) | giant snail, jassa red slug, dragon frog, marsh turtle, giant leech, burglar crab, wamasu den | viper (canon); leopard, panther, rhino: no dossier hit (the panther hits are the Panther River); bear-lizard is canon (`loading-facts.md:106`) but no mod ships one |
| Oliis Bay (mercantile-coast) | coastal-lagoon 12 | as Archon Coast | shark, lurker shark (Oliis Bay fish list `loading-facts.md:436` names sea-drakes at the mouth, sharks by the pad-sa fact) |
| Middle Argonia (hist-heartland) | coastal-lagoon 12 | as Archon Coast | as above |
| Blackrose (imperial-penal-south) | coastal-lagoon 12 | as Archon Coast | as above |
| Dead-Water (naga-kur-deeps), Alten Corimont (pirate-freeholds) | none by count; Alten Corimont's frontier 15 | as Blackwood | — |
| every settlement | 0 domestic kinds placed (Skyrim 5, the mod 5) | guar, lizard-steed, mouth-plover rows exist with no form; the mod's chickens, cows, goats, horses, dogs are vanilla (0012 quarantine) | a guar or lizard-steed form from the pinned mods, or an owner call |

Smallest change with the largest effect: the D2–D3 land lists of coastal-lagoon, tidal-delta and deep-river-corridor
(4–5 kinds) are what the owner walks past; widening six land kinds into the coast lifts them to 10, level with the
other classes and with Skyrim's land set, at no new form.

## Notes

- `creature_region` (103 rows, seven legacy region names: murkmire, coasts, middle-argonia, shadowfen,
  blackwood-gloommire, thornmarsh-east, deep-basin) no longer matches `land_region`; `creature_region_class` (163 rows)
  is what the lists read. One of the two should go.
- Skyrim's levelled lists put the same prey and predators in every biome; its variety per region comes from a shared
  pool of 23, not from per-biome authorship. Ours is authored per class, which is why the wet classes exceed Skyrim and
  the dry ones trail it: the dossier gives the swamp more named animals than the uplands.
- The committed plugin YAML (`plugin/Argonia/Worldspaces`) carries no creature spawn refs; the province's placed
  refs exist only in the build on the machine, so per-block counts for ours come from the lane's window measure.
