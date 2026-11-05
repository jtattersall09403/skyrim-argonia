<!-- imported unchanged from elder-souls-argonia docs/world/74-ecology.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 74 — Ecology: the province's creatures

The province ecology table and the rules that place creatures. Every
creature in Black Marsh has one row here. The same row lives as data
in [creatures.json](../../../world/sources/registries/creatures.json) (the
home table; this doc is its design and its readable view). The table is
province-wide; 2.4 places only the slice's places, routes and the wild
between them. Every other wilderness is a Part 4 packet that reads the
same table. Decisions [0004](../old-decisions/0004-fixed-difficulty-constraint.md)
(fixed danger) and [0138](../old-decisions/0138-people-and-creatures-live-by-the-place-record-and-the-lamp-clock.md)
(creatures live on the same shape, clock and loops as people) bind it.

## Sources

Every row stands on a lore dossier:
[fauna and hazards](../../../world/sources/lore/topics/fauna-hazards.md) and
[ecology, encounters and loot](../../../world/sources/lore/topics/ecology-encounters-loot.md),
both UESP extracts under the era policy (0002). The UESP pages a row
names are the ones those dossiers record. What can be shown is bounded by
[creature asset availability](../research/lore/creature-asset-availability.md)
and the [Murkmire adoption plan](../research/placement-settlements/king-of-the-murkmire-adoption-plan.md)
§3.7 keep list. Counts, notice ranges, day patterns and the
Fight/Flee/Alarm values are design numbers set from the dossiers'
behaviour lines (`EXTRAPOLATED`); presence, region and behaviour come from the dossiers.

## Three rules from the lore

1. **Flies, leeches, water and rot make the baseline danger.** Set-piece
   hunters are rare and fixed. Adding more creatures does not raise the
   danger (ecology § P2).
2. **Nothing scales to the player.** A row's band is fixed (world/76
   §128). D1 managed marsh is mostly harmless and skittish: fish, birds,
   torchbugs, slugs, a leech. D2 adds what bites. D3 and D4 hold the hunters. D5 rows are hand-authored set pieces, never ambient.
3. **Creatures yield materials.** Every row names what comes off it and its use
   (ecology § P3); 2.7 turns that into drops.

## Regions

The catalogue's culture regions map onto the lore regions of ecology §2
by the cities they hold:

| Catalogue region | Lore region(s) | Why |
|---|---|---|
| `dunmer-north` | Shadowfen, Thornmarsh and the east | Stormhold and Thorn |
| `hist-heartland` | Middle Argonia | the Hist forest interior |
| `imperial-fringe` | Blackwood and Gloommire | Gideon |
| `imperial-penal-south` | Blackwood and Gloommire, Murkmire | Blackrose between them |
| `mercantile-coast` | the coasts, Murkmire | Lilmoth and Soulrest |
| `naga-kur-deeps` | Murkmire | the inner Naga-Kur country |
| `pirate-freeholds` | the coasts, Middle Argonia | Alten Corimont and the rivers above it |
| `saxhleel-coast` | the coasts, Murkmire | Archon and the coastal jungle |

**Variety.** Each region has a signature, a staple and an apex (ecology
§2), so two crossings of one band differ: a D2 stretch in the Blackwood
fringe holds bog dogs, death hoppers and crows; a D2 stretch on the
Murkmire coast holds swamp jellies, hackwings and slaughterfish in the
shallows; D2 in the Hist heartland is wasps, adders and kotu gava. The
per-region, per-band row lists are in `wild` of
`lanes/2.4/c1-slice-creatures.json`, derived from this table.

## The row

Each row in `creatures.json` carries: `statblock` (the contract's
`Statblock`, class `creature`, band and position on the D-ladder,
variants, respawn), `hostility`, `fightFleeAlarm` (Morrowind's 0–100
triple), `reaction` (on notice: fight, flee, alarm, lure or ignore),
`notice` (sight range and cone, hearing, scent, the senses it uses; the scent it smells is the player's own, lowered by being submerged, a mud wallow, eel slime and a carried pahnjee, `perception/scent.ts`, rows in `detection.json` `tables.scent`),
`den` (type, the reason it is there, the rest activity), `territory`
(radius, path or swim network, group size, groups per km), `day` (the
contract's day blocks; `home` is the den, `work:0` the territory),
`habitat`, `diet`, `eatenBy`, `harvest`, `whyHere`, `sourcing` (the
asset that delivers it and any redesign), `look.modelSet` (2.4c2 fills
it), `domestic`, `handAuthoredOnly` and `tableRow` (its anchor here). A
placed creature is a `creature-at.` living-thing record that copies
these from its species row.

**The hunt.** Every predator row (kind `predator`) names `hunt` in its
active block; the roster generator copies the species' blocks into each
placed creature's day and the species' territory radius into its
territory. `hunt` is a composed routine on the creature's existing walk
and idle clips (no new art, no combat; attacks are 2.7's): from the den
the hunter goes to two or three prey points inside the territory radius,
on its own nav class (the species' "what it eats" decides only that it
hunts; where the prey stands is the nearest mesh point on a ring of the
territory), pauses and notices at each, then returns to the den. The
routine fills the active block; the rest block is the den.

## The table

42 rows. Columns: what it is; the ground or water it lives on (and its
network); regions; bands; how many per km of matching network and how
they group; day and night; what it eats and what eats it; how it notices
and reacts; its den; why it is here in the lore; how it is shown; its
dossier.

| Creature | What it is | Ground and water | Regions | Bands | Per stretch, group | Day and night | Eats; eaten by | Notices and reacts | Den | Why here | Model | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| <a id="bog-blight"></a>**Bog Blight** (`creature.bog-blight`) | A drowned Argonian corpse that walks once its grave-stake works loose. | grave mounds, flooded burial ground; shallow standing water (path) | shadowfen, murkmire, blackwood-gloommire | D2–D3 | 0–2/km; loose pack 2–5 | nocturnal | the living, Naga whole; no predator; rats pick its leavings | scent, hearing, sight 14 m; hostile, fight 90 flee 0 alarm 0; closes on any living scent; a pahnjee rack masks the scent and turns it aside | grave field (ruin) | Argonian dead whose stake came loose, dangerous in numbers; the marsh floods every wet season, so old grave fields are where they walk. | vanilla: vanilla draugr (meshes/actors/draugr) + BM&V troll/ghoul.nif re-material | fauna-hazards.md; ecology-encounters-loot.md |
| <a id="crocodile"></a>**Crocodile** (`creature.crocodile`) | A marsh crocodile two men long that lies still at the bank and lunges fast. | mud banks, reed edges; slow rivers, ravine pools, canals (swim) | shadowfen, murkmire, coasts, blackwood-gloommire | D2–D3 | 1–3/km; solitary or loose bask 1–3 | crepuscular | fish, guar, waders, anything at the water's edge; wamasu; sea-drakes offshore | sight, water-vibration, sight 18 m; hostile, fight 70 flee 20 alarm 0; ambush from the water at a bank; breaks off and sinks if badly hurt | bank wallow (water) | Two men long, fast, attacks inside town limits at Bogmother; Shadowfen ravines are crocodile-infested. | sourced: BM&V vault slaughterfish/character assets/mihailcrocodile.nif (+ mihailcrocodileSALT) | fauna-hazards.md; ecology-encounters-loot.md |
| <a id="death-hopper"></a>**Death Hopper** (`creature.death-hopper`) | A frog the size of a dog that waits under the water and spits poison. | pond margins, peat pools; still ponds and seeps (swim) | blackwood-gloommire, murkmire, shadowfen | D2–D3 | 1–4/km; pack 3–6 | crepuscular | birds, rats, large prey swallowed whole; crocodiles, hackwings take the young | water-vibration, sight, sight 12 m; hostile, fight 80 flee 30 alarm 10; ambush from under the surface; spits toxic globs at range, then closes as a pack | pond bed (water) | A notably large population around Gideon; lurk under the water, poisonous, spit over great distances, found in packs. | sourced: HTBM vault pool htbm FrogSkeleton.nif with PoisonFrogBlue/Green/Red.nif, plus Toad.nif | UESP:Lore:Death Hopper; fauna-hazards.md; ecology-encounters-loot.md |
| <a id="feather-serpent"></a>**Feather-Serpent** (`creature.feather-serpent`) | A great serpent of the deep meres. Argonian stories give it feathers. | Hist forest floor; deep interior meres (swim) | middle-argonia, deep-basin | D5 | hand-placed only; solitary 1–1 | day and night | giant snakes, haj mota, crocodiles; no predator | sight, scent, water-vibration, sight 30 m; hostile, fight 60 flee 0 alarm 0; territorial; strikes anything that enters its mere and does not follow out of it | deep mere (water) | The sources say only that feather-serpents inhabit the depths of Black Marsh; ecology-encounters-loot names it Middle Argonia's free apex. Placed by hand only. | none: Shown as a colossal great serpent on the kaj-thux build; the feathers live in rumour and text only. | fauna-hazards.md; ecology-encounters-loot.md |
| <a id="fellrunner"></a>**Fellrunner** (`creature.fellrunner`) | A pale, quick ground bird whose down hides a hunter's scent. | fern floor, field edges; none (path) | murkmire, coasts, middle-argonia | D1–D2 | 2–6/km; flock 3–8 | diurnal | seed, insects; hackwings, bog dogs, moon adders | sight, hearing, sight 25 m; neutral, fight 0 flee 90 alarm 30; runs at once and calls; a fleeing flock warns the birds and beasts nearby | fern scrape (cover) | Their pale down lets a hunter move through Murkwood undetected. Argonian farmers trade the feathers, so the birds live by the fields. | sourced: BM&V dodo on the vanilla chicken rig. It never fights, so its attack slot is the peck; it dies by settling into the sit-down clip. | fauna-hazards.md; ecology-encounters-loot.md |
| <a id="fleshfly"></a>**Fleshfly Swarm** (`creature.fleshfly`) | A red cloud of sand-grain flies that eat flesh. | carrion, rot; stagnant pools (path) | shadowfen, murkmire, blackwood-gloommire, middle-argonia, deep-basin | D1–D3 | 1–5/km; cloud 1–3 | diurnal | flesh; birds at the cloud edge | scent, sight 6 m; hostile, fight 100 flee 0 alarm 0; a cloud that follows a warm body; the vile emollient repels it | carrion pool (prey) | Red, sand-grain sized, in obscuring clouds; the Slough Point garrison lost ears and noses to them; they give mounts sloughskin. | none: A particle cloud with a damage volume, part of the attrition field rather than a creature with a body. | fauna-hazards.md; ecology-encounters-loot.md |
| <a id="giant-leech"></a>**Giant Leech** (`creature.giant-leech`) | A leech as long as an arm that waits in dark water for a swimmer. | none; seeps, dark pools, flooded halls (swim) | shadowfen, murkmire, blackwood-gloommire, middle-argonia | D1–D3 | 1–6/km; cluster 2–8 | day and night | blood; osheeja gars, death hoppers | water-vibration, scent, sight 4 m; hostile, fight 80 flee 10 alarm 0; latches on and drains; slow on land | seep edge (water) | The sources name giant leeches among Black Marsh's everyday hazards; they feed where scraps fall into still water. | sourced: BM&V vault slaughterfish/character assets leech build | fauna-hazards.md |
| <a id="giant-wasp"></a>**Giant Wasp** (`creature.giant-wasp`) | A wasp the size of a pony that hunts from the canopy edge. | canopy edge, clearings; none (path) | murkmire, middle-argonia, blackwood-gloommire | D2–D3 | 0–2/km; nest group 2–4 | diurnal | insects, fellrunners, carrion; hackwings | sight, hearing, sight 20 m; hostile, fight 85 flee 15 alarm 40; defends its nest hard; others join on the alarm buzz | paper nest (cover) | Giant wasps 'the size of ponies' are among Black Marsh's everyday hazards. | vanilla: A ground-hunting giant insect on the vanilla chaurus body, tinted wasp-amber: it hunts from the clearing edge on foot rather than from the air. The wasp bodies are Dawnguard and Dragonborn ones we do not hold, so it stands on the base chaurus rig. | fauna-hazards.md |
| <a id="guar"></a>**Guar** (`creature.guar`) | A placid two-legged reptile kept in pens; its body warms a hatchery. | pens, field edges, coast meadows; shallows (the Glowgill breed swims under) (path) | coasts, middle-argonia, murkmire | D1 | kept by people; herd 2–6 | diurnal | reed, fern, fodder; crocodiles, wamasu | sight, scent, sight 15 m; neutral, fight 5 flee 70 alarm 10; kept animals stay in their pen; a struck one bolts | pen or awning (cover) | The Glowgill Guar of the Archon coast breathes underwater; the Ambergill is the Gideon and Murkmire golden variant. | sourced: BM&V vault guars/guar.nif, histguar.nif, pond variants | fauna-hazards.md; ecology-encounters-loot.md |
| <a id="hackwing"></a>**Hackwing** (`creature.hackwing`) | A big bird with a saw-edged beak. It wounds its prey, flies off and returns. | open marsh, grassland edge; none (path) | murkmire, thornmarsh-east, blackwood-gloommire | D2–D3 | 1–3/km; flock 2–5 | diurnal | fellrunners, young death hoppers, wounded travellers; no predator when grown; eggs to moon adders | sight, sight 35 m; hostile, fight 75 flee 40 alarm 30; bleed and withdraw: strikes, leaves, returns when the victim is weak | snag roost (cover) | Flocks that strike, fly off and return when the victim is mostly dead from blood loss; Murkmire and the grassland edge. | vanilla: A dun winged reptile on the vanilla dragon body at a three-metre wingspan; it still dives, strikes and climbs away. The BM&V cliff racer ships no skeleton or clips. | UESP:Lore:Hackwing; fauna-hazards.md; ecology-encounters-loot.md |
| <a id="haj-mota"></a>**Haj Mota** (`creature.haj-mota`) | A great armoured swamp turtle with a crushing bite. | mudflats, bank sand; slow shallows (both) | murkmire, shadowfen, coasts | D2–D3 | 0–2/km; solitary or pair 1–2 | diurnal | reed, carrion, shellfish; geels-ha butcher eels in Kothringi folklore | sight, tremor, sight 10 m; guarded, fight 40 flee 10 alarm 0; ignores the distant; charges anyone who comes close or near its eggs | egg bank (water) | A large armoured swamp turtle-beast; its shells make the province's platters and shields. | sourced: BM&V vault cow/Glyptodon and mudcrab character assets | UESP:Lore:Haj Mota; fauna-hazards.md; ecology-encounters-loot.md |
| <a id="haynekhtnamet"></a>**Haynekhtnamet** (`creature.haynekhtnamet`) | The old wamasu of Shadowfen that villagers fed to hold back the floods. | flood channels; deep black water of Shadowfen (swim) | shadowfen | D5 | hand-placed only; unique 1–1 | crepuscular | crocodiles, haj mota, offerings; no predator | sight, water-vibration, sight 30 m; hostile, fight 70 flee 0 alarm 0; electrifies its water; does not touch the offerings | flood-channel lair (water) | The legendary wamasu of Shadowfen, given offerings to stop the seasonal flooding. Placed by hand, once. | sourced: creature.wamasu build (HTBM Wamasu.nif/WamasuALT.nif), uniquely scaled and re-materialled | UESP:Lore:Haynekhtnamet; fauna-hazards.md |
| <a id="hoarvor"></a>**Hoarvor** (`creature.hoarvor`) | A swollen tick as big as a dog that feeds on carcasses and on any traveller close to its nest. | bone scatter, cave mouths; none (path) | murkmire, coasts, blackwood-gloommire | D1–D2 | 0–3/km; cluster 2–5 | day and night | blood, carrion; hackwings, bog dogs | scent, tremor, sight 8 m; hostile, fight 70 flee 30 alarm 0; scuttles at any warm body close by and gives up the chase quickly | bone scatter (prey) | The sources name hoarvor among Black Marsh's everyday hazards; they gather where a predator leaves carcasses. | sourced: BM&V vault mudcrab/character assets/parasite build | UESP:Lore:Hoarvor; fauna-hazards.md |
| <a id="jassa-red-slug"></a>**Jassa Red Slug** (`creature.jassa-red-slug`) | A red acid slug that slug-shapers use to carve wood and stone. | wet stone, rotting wood; none (path) | murkmire, middle-argonia, coasts | D1 | 0–4/km; scatter 1–4 | nocturnal | rot, moss; fellrunners, moon adders | touch, sight 2 m; neutral, fight 0 flee 40 alarm 0; harmless unless handled bare; burns skin on touch | wet wood (cover) | The acid-secreting slugs used in slug shaping. | sourced: BM&V vault snail/slug.nif (+ slugskeleton) | fauna-hazards.md; ecology-encounters-loot.md |
| <a id="kaj-thux"></a>**Giant Snake** (`creature.kaj-thux`) | A giant snake, long as a dozen cattle, that swallows its prey whole. | reedbeds, forest floor; rivers and meres (both) | shadowfen, middle-argonia | D3–D4 | 0–1/km; solitary 1–1 | crepuscular | guar, crocodiles, travellers; the feather-serpent only | scent, tremor, sight 20 m; hostile, fight 65 flee 10 alarm 0; strikes and swallows; ignores what is too big or too far | reedbed coil (cover) | Abundant prey and no competent predators have grown snakes 'a dozen cattle laid end to end'; Shadowfen's signature. | sourced: BM&V vault snake.nif on the BM&V snake skeleton, eight metres | UESP:Lore:Giant Snake; fauna-hazards.md; ecology-encounters-loot.md |
| <a id="kotu-gava"></a>**Kotu Gava** (`creature.kotu-gava`) | A whirring swarm of biting marsh insects. | reeds, standing water; surface (path) | murkmire, coasts, middle-argonia | D1–D2 | 0–4/km; swarm 1–2 | crepuscular | blood, nectar; fellrunners, death hoppers | scent, sight, sight 8 m; hostile, fight 80 flee 30 alarm 0; a swarm that harries and thins with distance from water | reed swarm (water) | The sources name kotu gava among the everyday insect hazards; KotM placed 23 of them in its exterior. | none: A particle swarm with a damage volume in the attrition field, like fleshflies. | UESP:Lore:Kotu Gava; fauna-hazards.md; king-of-the-murkmire-adoption-plan.md |
| <a id="lamia"></a>**Lamia** (`creature.lamia`) | A serpent-tailed hunter that lives in the caverns under ruins. | caverns, flooded halls; cave pools (both) | shadowfen | D3 | hand-placed only; warren 2–4 | day and night | cave fish, intruders; no predator | hearing, sight, sight 16 m; hostile, fight 85 flee 10 alarm 40; hunts in the dark; calls others in the warren | cavern warren (ruin) | Lamias infest the caverns beneath Loriasel. It lives only in interiors. | sourced: BM&V vault slaughterfish/rivnaga.nif | UESP:Lore:Lamia; fauna-hazards.md; ecology-encounters-loot.md |
| <a id="lizard-steed"></a>**Lizard-Steed** (`creature.lizard-steed`) | A riding lizard that the Hist shaped to cross the marsh. | stables, roads; wades (path) | coasts, middle-argonia, shadowfen, murkmire | D1 | kept by people; kept 1–3 | diurnal | fodder; safe while kept | sight, scent, sight 18 m; neutral, fight 10 flee 60 alarm 20; kept and ridden; bolts if struck | stable (cover) | The Hist shaped lizards into other races' mounts because ordinary mounts bog down or catch sloughskin. | sourced: BM&V vault guars/ variants (albino guar and others) | fauna-hazards.md |
| <a id="marsh-giant"></a>**Marsh Giant** (`creature.marsh-giant`) | A woodland spirit the size of a giant that fells dead trees and turns the soil. | old forest, deadfall; wades (path) | blackwood-gloommire, middle-argonia | D4 | 0–1/km; solitary 1–1 | diurnal | none recorded (a spirit); no predator | sight, hearing, sight 25 m; neutral, fight 20 flee 0 alarm 20; goes about its work; fights only if struck or if loggers cut nearby | deadfall clearing (cover) | Cousins to spriggans that keep the forest; the Hist urge Argonians to avoid them; it is the apex of Blackwood. | sourced: vanilla giant (meshes/actors/giant) + BM&V vault bark re-material | UESP:Lore:Giant (Black Marsh); fauna-hazards.md; ecology-encounters-loot.md |
| <a id="medusa"></a>**Medusa** (`creature.medusa`) | A serpent-bodied hunter of the Murkwood whose gaze stuns. | Murkwood floor, ruins; pools (path) | murkmire | D3 | 0–1/km; solitary or pair 1–2 | nocturnal | intruders, swamp jellies; no predator | sight, sight 22 m; hostile, fight 85 flee 10 alarm 20; holds ground in its ruin | Murkwood ruin (ruin) | Medusas are in Murkwood. | sourced: Shown on the BM&V serpent body at three metres, tinted moss-green. The rivnaga mesh is a feathered Quetzalcoatl that reads as a sea dragon. | fauna-hazards.md |
| <a id="miregaunt"></a>**Miregaunt** (`creature.miregaunt`) | A walking mound of root, mud and old stone that rises again after it falls. | ruins, Hist groves; wades (path) | murkmire | D4 | 0–1/km; solitary 1–1 | day and night | none (part of the land); no predator | tremor, hearing, sight 15 m; hostile, fight 90 flee 0 alarm 0; guards a set ground; never leaves it; returns after it falls | guarded ground (ruin) | Murkmire's signature; tied to the Hist and part of the land; it returns after it is struck down. | sourced: BM&V vault giant/character assets/treant.nif | UESP:Lore:Miregaunt; fauna-hazards.md; ecology-encounters-loot.md |
| <a id="mouth-plover"></a>**Mouth-Plover** (`creature.mouth-plover`) | A small bird kept by rich Argonians to clean their teeth. | perches in wealthy houses; none (path) | coasts, murkmire | D1 | kept by people; kept 1–2 | diurnal | scraps from teeth, insects; moon adders | sight, sight 10 m; neutral, fight 0 flee 90 alarm 10; flits away | household perch (cover) | Corimont mouth-plovers are kept by high-status Argonians to clean their fangs. | sourced: BM&V goose on the vanilla chicken rig; its attack slot is the peck and it dies by settling into the sit-down clip. | fauna-hazards.md |
| <a id="osheeja-gar"></a>**Osheeja Gar** (`creature.osheeja-gar`) | A long-jawed fish that Naka-Desh fishers train to drive other fish. | none; rivers, estuaries (swim) | coasts, murkmire, middle-argonia | D1 | 2–8/km; school 2–6 | day and night | small fish, leeches; crocodiles, ripper eels | water-vibration, sight 6 m; neutral, fight 0 flee 80 alarm 0; darts away from swimmers | river pool (water) | Osheeja gars are used by the Naka-Desh to catch other fish. | vanilla: vanilla fish (meshes/actors/ambient) and slaughterfish family | fauna-hazards.md |
| <a id="rootworm"></a>**Rootworm** (`creature.rootworm`) | A translucent eight-foot worm that carries travellers through the deep roots. | under the Hist roots; none (path) | middle-argonia | D1 | hand-placed only; none shown 0–0 | day and night | slow digestion of what it swallows; no predator | none, sight 0 m; friendly, fight 0 flee 0 alarm 0; not an enemy; a transport | rootworm station (cover) | The Underground Express; eight feet, translucent, swallows travellers whole and digests very slowly; wintertide migration to Gideon. | none: Never placed as an actor: shown as its station mound, sound and the travel screen. | fauna-hazards.md; middle-argonia.md |
| <a id="sea-drake"></a>**Sea-Drake** (`creature.sea-drake`) | A crocodile-like sea beast with paddles for legs that hunts deep water. | none; deep bay water (swim) | coasts | D4 | 0–1/km; solitary 1–2 | day and night | slaughterfish, swimmers; no predator | water-vibration, sight, sight 25 m; hostile, fight 80 flee 10 alarm 0; takes swimmers in deep water; never comes ashore | deep channel (water) | In the deep water off Lilmoth, making Oliis Bay incredibly dangerous for swimmers. | sourced: HTBM vault pool htbm SeaDrake mesh | UESP:Lore:Sea Drake; fauna-hazards.md; ecology-encounters-loot.md |
| <a id="swamp-leviathan"></a>**Swamp Leviathan** (`creature.swamp-leviathan`) | A spined beast the size of a hill, with long claws and blind white eyes. | deep marsh; wades (both) | murkmire, middle-argonia, deep-basin | D4–D5 | hand-placed only; solitary 1–1 | day and night | anything; no predator; rats hollow out its carcass | tremor, hearing, sight 0 m; hostile, fight 95 flee 0 alarm 0; blind; hunts by tremor and sound | leviathan wallow (water) | Very, very dangerous; their skeletons litter Deepmire. It is placed by hand only. | sourced: BM&V vault gehenoth/gehenoth.nif | UESP:Lore:Swamp Leviathan; fauna-hazards.md; ecology-encounters-loot.md |
| <a id="voriplasm"></a>**Voriplasm** (`creature.voriplasm`) | A creeping pool of green slime that strips a body to the bone. | flooded floors, sunken halls; stagnant pools (path) | murkmire, blackwood-gloommire | D3–D4 | 0–0/km; solitary 1–1 | day and night | anything living; no predator | tremor, scent, sight 0 m; hostile, fight 100 flee 0 alarm 0; lies still as a pool and rises when anyone comes close | sunken hall (ruin) | A moving pool of green slime; leaves small bones; KotM placed voriplasms in its xanmeers. It is placed in interiors first. | sourced: BM&V vault snail/slug.nif (+ slugskeleton) re-material; KotM voriplasm on horker rig is the dedicated-mesh candidate | UESP:Lore:Voriplasm; fauna-hazards.md; ecology-encounters-loot.md; king-of-the-murkmire-adoption-plan.md |
| <a id="wamasu"></a>**Wamasu** (`creature.wamasu`) | A great lightning-charged swamp reptile that makes its water deadly. | jungle floor, root hollows; black pools and channels (both) | shadowfen, thornmarsh-east, coasts | D3–D4 | 0–1/km; solitary 1–1 | crepuscular | crocodiles, guar, juvenile wamasu; no predator when grown | sight, water-vibration, sight 25 m; hostile, fight 85 flee 5 alarm 0; electrifies the water round it; adult males eat juveniles | root-hollow den (cover) | Lightning-powered, electrifies its water; Shadowfen's apex, drawn down to the marsh edge in the east. | sourced: HTBM vault pool htbm Wamasu.nif / WamasuALT.nif | UESP:Lore:Wamasu; fauna-hazards.md; ecology-encounters-loot.md |
| <a id="wisp"></a>**Wisp** (`creature.wisp`) | A drifting light that leads travellers into deep water. | none (floats); over deep pools (path) | shadowfen, murkmire, blackwood-gloommire | D2–D3 | 0–2/km; drift 1–3 | nocturnal | none (a spirit); no predator | sight, sight 30 m; hostile, fight 60 flee 30 alarm 0; drifts ahead toward deep water; strikes when the traveller is in it | drowning pool (water) | Wisps lure travellers to drown, with an intelligence behind them. | vanilla: vanilla witchlight (meshes/actors/witchlight), 0.3 m, blue-white glow, hanging 1.4 m up | fauna-hazards.md |
| <a id="wispmother"></a>**Wispmother** (`creature.wispmother`) | A pale spirit that drives the wisps of a drowning pool. | mist over water; deep pools (path) | shadowfen, murkmire | D4 | hand-placed only; unique 1–1 | nocturnal | none; no predator | sight, sight 30 m; hostile, fight 80 flee 0 alarm 0; calls its wisps; splits into shades | anchor pool (water) | Something intelligent behind an anchor drives the wisps; it is placed by hand. | vanilla: vanilla wispmother (meshes/actors/wisp) | UESP:Lore:Wispmother; fauna-hazards.md |
| <a id="xal-krona"></a>**Xal-Krona** (`creature.xal-krona`) | A hulking Hist-made Argonian that speaks in few words and spits sludge. | tribal ground, Hist roots; wades (path) | murkmire, middle-argonia | D4–D5 | hand-placed only; unique 1–1 | day and night | as an Argonian; no predator | sight, hearing, sight 25 m; guarded, fight 50 flee 0 alarm 30; tests those who come; respects tribal tradition; will talk | Hist ground (ruin) | Created by the Hist through sap for a reason, as the Dead-Water Hist made one to test warriors; it is placed by hand. | sourced: vanilla werewolfbeast rig + BM&V vault armour; KotM Argonian behemoth on werewolf rig | UESP:Lore:Argonian Behemoth; fauna-hazards.md |
| <a id="bog-dog"></a>**Bog Dog** (`creature.bog-dog`) | A pack hunter that grows marsh plants in the fur of its back. | fern and reed thickets; wades (path) | blackwood-gloommire, murkmire | D2 | 1–3/km; pack 3–5 | crepuscular | fellrunners, rats, guar calves; crocodiles, kaj-thux | scent, hearing, sight 20 m; hostile, fight 70 flee 40 alarm 50; circles as a pack; howls bring the rest; breaks if two fall | thicket burrow (cover) | Pack hunters with camouflaging vegetation growing in their back fur; a Blackwood staple; tameable and loyal. | vanilla: A dark vanilla wolf; the back-growth is carried by where it lies (fern thickets) and its description, not by the model. | UESP:Lore:Bog Dog; ecology-encounters-loot.md |
| <a id="swamp-jelly"></a>**Swamp Jelly** (`creature.swamp-jelly`) | A floating jelly that drifts over the marsh, mostly harmless. | none (floats); over still water (path) | murkmire, coasts | D1–D3 | 1–5/km; drift 2–6 | day and night | insects, spores; medusas, hackwings | touch, sight 5 m; neutral, fight 5 flee 30 alarm 0; drifts and ignores; the Deepmire breed stings on contact (D3) | still-water drift (water) | Mostly docile, named by flavour; the plum is rare good fortune; Deepmire breeds kill on brief contact. It is a staple of Murkmire. | vanilla: Shown as the vanilla witchlight grown to jelly size, plum-tinted with a faint glow, drifting just over the water. The netch is a Dragonborn body we do not hold. | UESP:Lore:Swamp Jelly; ecology-encounters-loot.md |
| <a id="ripper-eel"></a>**Ripper Eel** (`creature.ripper-eel`) | A canal eel trained to hunt anyone who swims the canals without leave. | none; Lilmoth canals and harbour (swim) | coasts | D2 | hand-placed only; school 2–4 | day and night | fish, intruders; sea-drakes | scent, water-vibration, sight 10 m; hostile, fight 85 flee 20 alarm 0; attacks swimmers in its canal; ignores anyone rubbed with eel-slime | canal stretch (water) | Trained to hunt Argonians crossing Lilmoth's canals illegally; eel-slime turns them aside. | vanilla: Shown on the vanilla slaughterfish build, scaled long. | UESP:Lore:Ripper Eel; ecology-encounters-loot.md |
| <a id="slaughterfish"></a>**Slaughterfish** (`creature.slaughterfish`) | A toothed fish that bites anything in its water. | none; coast shallows, estuaries (swim) | coasts | D1–D2 | 1–4/km; school 2–4 | day and night | fish, swimmers; sea-drakes, crocodiles | water-vibration, scent, sight 8 m; hostile, fight 75 flee 30 alarm 0; swarms a swimmer briefly, loses interest at the shore | weed bed (water) | Slaughterfish are the coast's staple swimmer threat. | vanilla: vanilla slaughterfish (meshes/actors/slaughterfish) | ecology-encounters-loot.md |
| <a id="dreugh"></a>**Dreugh** (`creature.dreugh`) | A many-legged shelled sea creature that walks the seabed. | seabed, tidal flats; bay deeps (swim) | coasts | D3 | 0–1/km; pair 1–2 | day and night | shellfish, carrion; sea-drakes | water-vibration, sight 12 m; hostile, fight 70 flee 10 alarm 0; guards its seabed; follows into the shallows | seabed hollow (water) | Dreugh are among the coast's swimmer threats. | sourceable: Sea of Spirits, Nexus SSE 4781 (sharks, dreugh, whales); not in the vault | ecology-encounters-loot.md |
| <a id="alit"></a>**Alit** (`creature.alit`) | A big-jawed two-legged hunter of the open eastern ground. | grassland, dry edges; none (path) | thornmarsh-east | D2 | 1–2/km; pair 1–3 | diurnal | guar, fellrunners; wamasu at the marsh edge | sight, scent, sight 25 m; hostile, fight 75 flee 30 alarm 20; charges in pairs on open ground | grass hollow (prey) | Alit are native to Morrowind and Black Marsh; the eastern grassland staple. | sourced: KotM alit mesh on the vanilla dog rig (plan §3.7 keepable) | UESP:Lore:Alit; ecology-encounters-loot.md; king-of-the-murkmire-adoption-plan.md |
| <a id="marsh-rat"></a>**Marsh Rat** (`creature.marsh-rat`) | A large rat that nests in carcasses and rubbish. | carcasses, rubbish, ruins; wades (path) | shadowfen, murkmire, blackwood-gloommire, coasts, middle-argonia | D1 | 0–3/km; nest 2–5 | nocturnal | carrion, scraps; moon adders, bog dogs, hackwings | scent, hearing, sight 8 m; hostile, fight 40 flee 60 alarm 30; nips when cornered, else scatters | carcass nest (prey) | Rats hollow out a swamp leviathan's carcass from the inside. | vanilla: vanilla skeever (meshes/actors/skeever) | fauna-hazards.md |
| <a id="crow"></a>**Crow** (`creature.crow`) | A black carrion bird that roosts by roads. | road verges, dead trees; none (path) | blackwood-gloommire, thornmarsh-east | D1 | 1–4/km; flock 3–8 | diurnal | carrion, scraps; hackwings | sight, sight 25 m; neutral, fight 0 flee 90 alarm 40; takes off calling and warns the road | dead-tree roost (cover) | Crows are part of Blackwood's staple fauna. | vanilla: vanilla crow (ambient critter) | ecology-encounters-loot.md |
| <a id="moon-adder"></a>**Moon Adder** (`creature.moon-adder`) | A small venomous marsh snake whose venom makes daril. | reed roots, stone; wades (path) | murkmire, middle-argonia, coasts | D1–D2 | 0–3/km; solitary 1–1 | nocturnal | rats, eggs, plovers; hackwings, bog dogs | tremor, scent, sight 4 m; guarded, fight 50 flee 40 alarm 0; strikes at a foot that comes close, then slips off | stone crevice (cover) | Moon adder venom makes daril, fatal to non-Argonians. | sourced: BM&V vault snake.nif on the BM&V snake skeleton, one metre, pale tint | ecology-encounters-loot.md |
| <a id="shine"></a>**Shine** (`creature.shine`) | A harmless drifting light that hangs about old Imperial ruins. | ruins; none (path) | coasts | D1 | hand-placed only; drift 1–4 | nocturnal | none; no predator | sight, sight 10 m; neutral, fight 0 flee 50 alarm 0; drifts; never harms | ruin glow (ruin) | Shines, a harmless cousin of wisps, loom around the Imperial ruins of Lilmoth. | vanilla: vanilla witchlight (meshes/actors/witchlight) | fauna-hazards.md |
| <a id="torchbug"></a>**Torchbug** (`creature.torchbug`) | A small glowing insect that hovers over marsh flowers at dusk. | flowering fern, reeds; none (path) | shadowfen, murkmire, middle-argonia, coasts, blackwood-gloommire | D1–D2 | 2–10/km; drift 3–10 | nocturnal | nectar; fellrunners, death hoppers | sight, sight 3 m; neutral, fight 0 flee 100 alarm 0; drifts away; catchable | flower bed (cover) | The sources list torchbugs in Black Marsh's flora and fauna. | vanilla: vanilla firefly critter, clips in the NIF, amber glow | fauna-hazards.md |

### Redesigns

Rows that no model can show as a body are redesigned around what exists,
so each one can still be placed:

- **Feather-serpent**: shown as a colossal great serpent on the
  kaj-thux build; its feathers live in rumour only.
- **Fleshflies** and **kotu gava**: particle clouds with a damage
  volume, part of the attrition field.
- **Rootworm**: never an actor; its station mound, its sound and the
  travel screen carry it.
- **Bog dog**: a dark vanilla wolf; the plants in its fur are carried
  by its den in fern thickets and by its description.
- **Swamp jelly**: the vanilla netch build.
- **Ripper eel**: the vanilla slaughterfish, scaled long.
- **Dreugh**: sourceable only (Sea of Spirits, SSE 4781); sourced
  before any placement; none is placed in the slice.

Dropped with reasons: kagouti (no model; the alit carries the eastern
grassland staple); the Helstrom crocodile (extinct since the Great Burn);
geels-ha butcher eels (Kothringi folklore; they appear only in stories).

## Placement rules

Written so a placer can run them mechanically; 2.4c2 places the slice from
them and `lanes/2.4/c1-slice-creatures.json`.

1. **Band.** A place's or stretch's band (the place record's
   `dangerTier`; a route takes its region band) caps everything in it. A
   placed creature's band is one of its row's `bands` and never above the
   place's. A row's typical band is `statblock.band`; a place may hold it
   lower only when that lower band is in its `bands`.
2. **Region.** Only rows whose `regions` include one of the place's lore
   regions (table above). A place record that names a species overrides
   this only with a written reason.
3. **No ambient life in D0.** A settlement's inside is D0: no wild
   creature stands inside its boundary. Wild creatures in a settlement's
   list stand outside the boundary. Kept animals (`domestic`) stand in
   their pen or awning and never fight.
4. **Every den has a reason.** Each den is one of: water (a pool,
   bank, channel or seep), cover (reeds, fern, a roost, a nest), prey (a
   carcass, a bone scatter, grazing), or ruin (a hall, a warren, a grave
   field). The den sits on the place's or stretch's path or swim network,
   matching the row's `habitat.network` (`path`, `swim` or `both`).
5. **Territory.** A creature lives its day between its den (`home`) and
   its territory (`work:0`) within `territory.radiusM` of the den, on the
   network its row names, on the village clock.
6. **How many.** A wild stretch takes `perStretch` groups per km of
   matching network, each group within `group.min`–`group.max`. A place
   record's `contents.creatures` and its `fauna` and `encounter` sockets
   set exact counts and win over the density.
7. **Hand-authored rows** (`handAuthoredOnly`: the D5 set pieces, the
   wispmother, the Xal-Krona, lamias, the rootworm, trained ripper eels,
   the Lilmoth shines) are placed only where a place record names them.
8. **Never scaled.** No count, band or stat reads player state.

## Packs

An authored group spawns as a group and moves as one. Every roster row of a
den is one member, and the members of one den are one pack. The pack's id is
the den socket (`CastMember.packId`), and each member has its place in the
pack (`packIndex`, 0 the leader). How a pack moves is set by its species'
`territory.group.kind`, looked up in `packages/game-core/src/people/packs.json`.
Each kind has a row, and a test fails on a kind with none:

- `formation`: `file` (a pair trails its mate), `spread` (a pack fans out
  behind the leader), `cluster` (a flock, a school or a drift keeps close),
  or `none` (solitary, unique and kept animals walk alone).
- `cohesionM`: the ring a follower keeps round the leader. A follower is never
  further than 1.4 times this from the leader.
- `followLagS` and `pauseJitterS`: each follower walks the leader's round
  behind it by its place in the pack, plus a pause of its own, so no two move
  in step.
- `alarm`, `rallyM` and `breakAtFallen`: `rally` brings the pack to an alarm
  (a bog dog's howl, a wasp's buzz). `scatter` sends each one off (a fleeing
  flock). A hostile answers alarms of its own pack only (`alarmGroupOf`), so a
  second pack 15 m away stays calm. `breakAtFallen` is the count of fallen
  members that breaks the pack (the bog dog's two).

The leader walks the hunt round ([72](72-navigation-ai.md) § The day), and
its followers walk the same round lagged on their ring, each snapped to its
own nav class. At the den, the members stand round it on the spread rings.
The people layer draws creatures on their species' model set, the nearest 24
within the people draw distance. Combat pack tactics (circling, flanking,
breaking off) are 2.7's enemy AI.

## The slice

The sixteen places and two routes, with every creature's row, count, den
and band, are in `lanes/2.4/c1-slice-creatures.json`; the build check that
wrote it reports no creature above its place's band and none inside a D0
settlement. Socket-bound entries name their `fauna` or `encounter`
socket.
