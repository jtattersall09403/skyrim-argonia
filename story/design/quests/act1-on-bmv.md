# Act I on BM&V: the opening act moved onto Black Marsh & Valenwood's world

Phase 2 ([brief](../../../docs/phases/2-first-act-on-paper.md)). The main quest's spirit and act shape are kept
([30-main-quest](30-main-quest.md) §16-21); the detail moves onto BM&V's world with minor edits only. Every place,
person and door below is a census row (`bmv_*` tables, [census](../../../docs/research/bmv/census.md)). The quest
records are rows in the story data: `quest.main.mq01`, `mq03`, `mq04`, `mq05` (`quest_record export <id>`).

## The act's spirit, kept

A nameless debtor on an Owing gang sees the cult cut a Hist from its eggs, is made useful to the Veiled Reed because
the law thinks them dead, finds the same wound on a second tree, and is carried upriver to the capital where the
throne stands empty and the priests argue what the closings mean. The stakes (dead eggs) are shown in the first hour;
the endgame's third option (the empty throne) is in a room by the end of the act.

## Which BM&V settlement hosts which beat

| Quest | Old place (no BM&V cell) | BM&V host | Why |
|---|---|---|---|
| MQ01 processing | work barge near Alten Corimont | Dock1 `00591F` | Argonia.esp already wakes the player there (ARG_OpeningMarker, ARG_Opening stage 10) |
| MQ01 camp, clutch | work camp | Pussbottom `005A0B` | the lore's Pusbottom district; navmesh; 138 refs of dressing |
| MQ01 the Hist | upriver Hist village | LilmothHist `005A0D` | Lilmoth's own Hist (lore: it once went rogue and was purged, `story/lore/lilmoth.md`:52,76) |
| MQ01 escape end, MQ03 | Stormhold river station | Hereguard Plantation `005919` | one square west of Lilmoth; manor servants `015193`, `015195`, boat captain `00AC8E` (Black Marsh North.esp deletes the merchants `0AA64F`, `0AA650`) |
| MQ03 the hiding overseer | none | cabin `01CabinIntsining1` `0FE7F7` (door `0FE832`) | a BM&V interior at Lilmoth |
| MQ03 the first sap-dream | fog-dressed reuse | orphan cave `01Cavebig` (no door; 723 refs) | reached by moving the player while asleep, so no door is needed |
| MQ04 hatching pools | Hatching Pools, north | Village `03978F` (22,-4) | tribal chief `084A7F`, tribe `084A7B`-`084A91`; its 72 leeches are the disease the village blames |
| MQ04 the cult camp | none | swamplandsrose by SPOT (29,-7) | a wild rise with alligators and leeches, three squares from the Village |
| MQ05 the convoy | Alten Corimont-Helstrom boat | ship `01Ship` Lilmoth (7,-1) to dock5 (BM2 -11,13), then an escorted walk north | BM&V's only crossing; the census's ship exits |
| MQ05 the city | Helstrom inner city | Helstrom `0D794B` (BM2 -7,21); houses interior `01ArgonianHouseinside` `1DE4A1` (nine doors) | mapped high in `place_bmv` |
| MQ05 the Scalded Throne | its own hall | `01cellDUPLICATE002` `2076BB` (door `2076D0`) | Helstrom's second interior with its own door |

## The minor world edits each needs (nothing major)

- **MQ01:** six new NPCs (the gang's named people) on Dock1 navmesh from BM&V Argonian templates; Cuts-the-Old-Knot and
  three cultists at a fixed level, enable-parented to one attack marker; fire FX statics on the same parent; a hatching
  shed and clutch statics in Pussbottom; a light on LilmothHist's tree under its own parent (turned off when the tree
  closes); a locked chest of the player's fixed starting gear. BM&V's WE adventurers and thieves at LilmothHist
  (`02A204`-`02A206`, `02A208`, `02A209`, vanilla levelled bases), Old Salty (`015184`, a levelled crab boss) and the
  Megalanian `155C92` get an enable parent that stays off (decisions 0035, 0006); the Daedroth pack by the grove
  (`1453EF`-`1453F3`) is deleted by Black Marsh North.esp.
- **MQ03:** Nesh-Deeka and two Lilmoth dock wardens placed; the courier's body and strap left at Dock1; the overseer
  hidden in BM&V's cabin `01CabinIntsiningDUPLICATE002` (`0FE8B7`, door `0FE95B` by Pusbottom), its door locked and its
  Maiden Spider removed; the Restless Dead `0AA660` and levelled Bonemen
  (`02A228`-`02A22A`) by the cabin removed (Black Marsh North.esp deletes `0AA65F` and the crocodile `1453FD`); a strongbox and three books; a lean-to and an alchemy table by Hereguard's
  landing (the census gives Hereguard no interior); `01Cavebig`'s ten actors removed and fog added.
- **MQ04:** Nurwul-Neel and Mee-Vei placed in the Village from BM&V's tribal template; a Hist tree reference (the base
  BM&V uses in LilmothHist) placed above the pools; the six draugr-race and dragon-priest-race placements (`07F92F`, `07F931`-`07F933`, `120E0A`, `120E0B`) removed
  (Black Marsh North.esp already deletes the eight `SoM_00EncDraugrzombiez1`, `084AF9` first, and `120E0A`, `120E0B`)
  under a parent that stays off (decision 0006); four fixed-level leeches placed on the cut root; a camp of three cultists at a fixed level, a
  chest of jars and a trail of gum spots at swamplandsrose; an An-Xileel officer, disabled until one ending calls him.
- **MQ05:** three raiders at a fixed level by dock5; two Reed escorts; two Megalanians and a Leopard on the walk; the
  four doors into Helstrom's house interior that open outside the city (`1E42B7`-`1E42B9` at dock5, `1E44AE`) locked;
  a young Hist for the Tree-Minders' grove and markers for the Reed's rooms and the debating house; six people at Helstrom (Ei-Tuja, Kaska-Meen,
  Never-Writes-Twice, the hall keeper, two gate guards) on its navmesh and in its house interior; a throne static
  and a broom in the hall. Black Marsh.esm's Helstrom had no actors; Black Marsh North.esp places 13 in its cells (a boatman, soldiers, villagers) and two merchants and a soldier in the hall `01cellDUPLICATE002` (census), so these six are the city's named people among BM&V's
  (below).

Every enemy is at a fixed level (decision 0035); no levelled list is used.

## What changed from the authored design, and why

- **MQ01:** the barge and camp become Lilmoth's Dock1 and Pussbottom; the rowboat escape becomes a swim to
  Hereguard. The Hist that turns its face is Lilmoth's own, which raises the stakes and is grounded in its lore.
- **MQ03:** Stormhold has no BM&V cell, so the survivors gather at Hereguard, one square from the attack. The
  "evidence table" becomes the real dock: the player goes back and reads the traces, which turns a talking quest
  into a search, a sample test and a forced lock.
- **MQ04:** the first affected Hist community is BM&V's tribal Village; its leeches, already there in numbers, become
  the misdiagnosis. A camp the player finds by following a gum trail adds the hunt (MISSING secondary).
- **MQ05:** the convoy is BM&V's ship and an escorted walk, and the ambush comes from a leak in the Reed's own office.
  The theological quarrel became a bargain (Helstrom answers to no outsider, and the Nisswo hold many readings): the
  player wins the Tree-Minders' leave for Reed watchers at the wounded trees. Helstrom is a census-empty city; six people and one
  reused interior give the arrival, the Reed office, the dispute and the empty throne. Act II's council and archive
  will need more of Helstrom and are a later phase's call.

## Open, recorded

- The coast road and Longmont need a decision 0006/0035 audit before Phase 4 builds MQ04 (Longmont has vanilla Imperial
  soldier bases; the road has hagravens renamed "Tree Mother", and levelled boar and Soul Cairn bases).
- The quest vocabulary's skills are Morrowind's; the block C-skill maps them to Skyrim's for now. Phase 4 owes the
  vocabulary itself.

- BM&V's Helstrom has nine house doors into one interior: the house quarter reads as one building inside. Kept;
  retargeting doors is a later edit if the owner finds it odd.
- MQ04's Village is east of Lilmoth where the lore's hatching pools are north; `place_bmv` maps
  `place.dunmer-north.hatching-pools` to `bmv.village` at medium confidence for this reason.
