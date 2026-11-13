# Walk 2, lane eco: creatures, birds, toughness, animations, looting

Measured on the main tree's build 20261111T100156Z (before) and on the lane's sources: the ecology stage run on the
full province into a scratch folder, and `rebuild.sh small` (after). Recipe: [ecology](../../../design/ecology.md).

| L# | cause (measured) | change | proof |
|---|---|---|---|
| L28 | Three causes. (1) Density measured over all 11,186 Tamriel LAND cells, half of them past Skyrim's border with nothing in them: 25.5 per 100 cells. Where the player walks (5,585 navmeshed cells) Skyrim holds 50.9 (benign 31.5, hostile 19.4). Open, mountain and water were a third of Skyrim's, and D0 and D1 were cut further, to 0.5 and 0.8. (2) The spot's own cell (the teleport landing) is kept empty. Most promised kinds were simply not near the spots: before, within 2 cells, D1 had 0 actors; Lake Ulaish had 2 (no otter); the province held 1 river otter. (3) The Barsaebica and Kotherra spots land in margin cells (no band), where the stage places nothing: 0 actors within 2 cells. | Density is Skyrim's per navmeshed cell (`measure.py` `wild`). Benign creatures are at Skyrim's rate in every band. Hostile ones are Skyrim's rate times the band: D0 0, D1 0.5, D2 1, D3 1.5, D4 2, D5 2.5. `walk_spots.json` lists what each spot promises. The stage places what the draw left short within 200 m, and its check fails a spot that is short. The two spots are moved into banded cells of their regions (`teleports.py`: Barsaebica (-26,-117), Kotherra (-50,-160)). | Full province: 7,663 actors against 5,979. Density against Skyrim per class is 0.89 to 0.97. Every promised kind of 13 spots is within 200 m (nearest distances in the stage's `check.json` `walk_spots`). The 10 faults left are the two old landings, which clear when `map` rebuilds the moved spots. Test: `test_newworld_ecology_walk_spots.py`. |
| L10 (creatures, birds) | No creatures at D1: see L28 (2). Birds: every bird kind (crow, sea-gull, shorebird, kingfisher, marsh-bird) was a Tropical Skyrim -- Birds actor. Their race uses a chicken's skeleton and behaviour, its flags are Walks with no Flies, and its package is a creature sandbox. 295 were placed at ground +16. They flutter through the land when they flee. | Flying birds become critters, as Skyrim's are. Crow, sea-gull, shorebird and kingfisher bind to `Skyrim.esm:FXbirdOPreyNoNestACT`, whose `FXfakeCritterScript` flies a path above the ground (function `birds`, at Skyrim's rates). Marsh birds stay walkers. | The roster check is green (96 kinds). The D1 spot now has burglar crab 42 m, marsh rat 59 m, guar 145 m, mudcrab 196 m and torchbug 105 m from the landing. |
| L13 | The ability added damage on top of the mod's own blow and never measured that blow. The check read a table, not the record. The hackwing's own blow is 60 (unarmed 40 × attack multiplier 1.5); the otter's 33, the dreugh's 67.5, the megalodon's 300. Skyrim's first animals (wolf, skeever, mudcrab) land 7.5 on a level 1 player's 100 health. | `toughness.py measure` writes each bound record's own blow to `blows.json` (race unarmed damage plus its fortify abilities, times its largest attack multiplier), and Skyrim's the same way. Each band copy's ability (negative to weaken) brings its blow to its band's target: D0 and D1 7.5; above that, the size class's Skyrim blow (insect and small 7.5, game 18.75, predator 52.5, giant 97.5) times 1, 1.4, 2 or 2.8. A promise never puts a size class where its band has none. The world writer writes negative magnitudes (`NewWorld.cs`). | Every kind is audited. Full province peak blow by band: D0 8, D1 8, D2 53, D3 137, D4 196, D5 273. Mean blow: D1 7.5, D5 130.7. The check fails any record not measured or off its band. Test: `test_a_hard_hitting_record_is_brought_down_to_its_band`. |
| L17 | The flying serpent was King of the Murkmire's giant snake (kinds giant-snake and kaj-thux). Its race `mihailgiantsnakerace` names a snake skeleton but the ice wraith's behaviour project; the skeleton's bones match 3% of that rig and 87% of the dragon's. The files resolve, but no clip drives its bones, so it moved rigid. The audit found 3 more: Black Marsh's swamp wyvern (`FatDragonBlack.nif` on no laid mod: invisible); Black Marsh's centipede (`siligonder.nif` missing); Curse of Cipactli's shine (an unskinned body). | `anim_audit.py` (in the stage's check) follows each placed record to its race. On the New World card it checks skeleton, behaviour project and clips, a skinned body whose bones the skeleton names, the rig's bones, and the plugins laid. Giant snake and kaj-thux are rebound to Curse of Cipactli's serpent (dragon behaviour, 92% bone match). Wisp is rebound to Skyrim's. The wyvern is dropped from its regions and the centipede record dropped. | Before: 4 failing kinds (`anim_before.json` run on the main build). After: full province 286 records, 0 failing; small world 181 records, 0 failing. Test: `test_ecology_anim_audit.py`. |
| L22 | Measured at the Aphon coast (cells -67..-69, -184..-188): actors stand at LAND +16 exactly. The navmesh lies 3 to 4 units under the LAND on average (5th to 95th percentile -10 to +8, max 21). The LAND is rough: a 352-unit drop between neighbouring vertices, and 12% of one flat cell has no navmesh. The walker follows the navmesh, so it dips in and out of the bumpy LAND. | Unchanged in this lane: the cause is the navmesh's fit to rough coastal LAND (`tools/navmesh/`), which needs a navmesh rebuild and a Skyrim comparison I did not take. | Numbers from `out/newworld/plugin/land/cy-184.bin` against the cells' NAVM. |
| L23 | Swimmers near the Aphon coast spot: before, within 2 cells, 2 dreugh and 1 sea otter, with no fish actors. Salt water got 8 per 100 cells (all-LAND measure). | Water is now Skyrim's walked rate (benign 7.9 plus hostile 12.3 per 100 cells × band). The Aphon spot promises dreugh, sea otter, reef slaughterfish, sea turtle and giant spider crab. | After, from the landing: dreugh 78 m, spider crab 94 m, reef slaughterfish 170 m, sea turtle 168 m, sea otter 151 m. |
| L25 | Not found in the records. The band bandit keeps vanilla's death item (`DeathItemBandit`) and its template inventory. The spider crabs carry legs and chitin, and the mudcrabs keep `DeathItemMudCrab02`. No script or race flag blocks activation. Found instead: bandits take their inventory from Skyrim's template (flag 0x100), so the band's kit was never what they carried. 31 copied creatures (e.g. Black Marsh's crocodile) carry nothing, and Skyrim shows no Search on an empty body. | The world writer clears the inventory template flag on any copy given a kit (`NewWorld.cs`), so a bandit carries and drops its band's armour and weapons plus its death item's loot. | Needs the owner's check (below). If bodies still cannot be searched, the cause is outside the records. |
| L26 | Torchbugs bind to Skyrim's night spawner `critterSpawnInsects_ManyNocturnalOnly`, whose script runs 20:00 to 23:00 only. Before, within 2 cells of the Nushara spot, there were 4 torchbug and 3 gnat spawners. | The Dusk spot promises torchbugs and gnat clouds within 200 m. The walk check names the hours. | After: torchbug 63 m, gnat cloud 43 m. |

## Walk checks

Use the "Argonia Travel" power (shout button), page "Walk-check spots". Reply to each bullet with "ok" or "fault",
plus a few words for a fault. Every creature named below is placed within 200 metres (about a minute's walk) of
where you land.

- "D1, the lowest danger: Cape Percar open coast": look around for mudcrabs, burglar crabs (crabs with a pot on their
  back), guar and marsh rats. Let a crab hit you: each hit should cost about 7 or 8 of a new character's 100 health.
- "D5, the highest danger: Murkwood cypress swamp": find a medusa, a bog blight or a stalker cat and let it hit you.
  A new character should die in one or two blows.
- Hackwing: wherever you meet one in a D1 or D2 place, a hit should cost a new character well under half its health.
- "Fresh black water creatures: Banujha Basin": look in and by the water for giant leeches, a crocodile, swamp
  jellies and sabretooth salmon, with frogs and turtles on the bank.
- "Salt water creatures: Aphon Isle coast": look for dreugh and giant spider crabs on the shore, and swim out to find
  sea otters, reef slaughterfish and sea turtles.
- "Under the canopy: Arnesian Jungle": hummingbirds, giant spiders, tree vipers and deer.
- "In the open: Arnesian Jungle grassland": deer, wild boar, an alit and mudcrabs.
- "Night insects at dusk: Nushara Bayou reeds": wait (wait menu) until 21:00. Glowing torchbugs fly over the reeds
  between 20:00 and 23:00, and clouds of flies are there at any hour. Turtles and frogs are nearby too.
- "A hostile people band: Chixathe Mesa": a band of hostile people, lamia, kagouti, netch and mountain goats.
- "A lake shore: Lake Ulaish": river otters, a megalania (giant lizard), a medusa, giant leeches and kingfishers.
- "A cool fen: Barsaebica" (the spot has moved into the fen): lamia, a medusa, turtles and giant snails.
- "Red mud mangroves: Kotherra Mangroves" (the spot has moved into the mangroves): a megalania, giant spider crabs and
  mudcrabs.
- Birds: anywhere on a coast or in open country, birds should fly above the ground and scatter as you come near. Reply
  fault if any bird flies into or through the land.
- Moving creatures: watch the giant serpents (Banujha Basin, Valley of Storms), the wisps (Valley of Storms at night)
  and any other creature. Reply fault, with its name, if one slides about without moving its body.
- Looting: kill one bandit of a hostile band (Chixathe Mesa) and one orange spider crab (Aphon Isle). Reply ok if both
  bodies can be searched, and say what the bandit carried. Reply fault if either cannot be searched.

## For the lead

- changes.md rows: "Creatures, hostile people or their rules" (stale: `ecology`, then `dressing`, which reads
  `ecology/place.py`, then `esm`, `readback`, `upload`). Also "The world writer" for `NewWorld.cs` (`esm`), and
  `teleports.py` (the two moved spots: `landings`, `map` and every stage after them that reads `map/teleports.json`).
  `rebuild.py`: the ecology stage's reads and its new check `anim_audit`.
- Files outside the lane's table, named: `tools/ArgoniaPlugin/NewWorld.cs` (negative band-blow magnitudes; inventory
  template cleared on a kitted copy), `tools/newworld/teleports.py` (two spots' `near`), `tools/newworld/rebuild.py`.
- After the full rebuild, the ecology check must show no `walk spot` fault. The two old landings' faults clear once
  `map` has rebuilt the moved spots. Then deploy as usual; no LOD step.
- L22 is owed to the navmesh: fit the triangles to rough coastal LAND, after measuring Skyrim's own navmesh-to-LAND
  gap.
