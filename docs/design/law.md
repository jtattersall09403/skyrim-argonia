# Law

Whose law holds at each place, and what the player meets when caught breaking it. A native Argonian place has no
cell: its sentence is the Owing, and whoever resists arrest is fought to the death. Places kept by an office
inherited from the Empire keep the Imperial cells. The owner ruled this on 2026-11-10 (`docs/owner-rulings.md`). The
lore is in `story/lore/topics/labour-and-bondage.md` §6 and `prisons.md`. This note is the brief for the lane that
builds it; the place builder builds it (`draft jail`, Build step 6 of `place-studio.md`).

## Sources and tables

- `tools/newworld/place_law.py` derives each place's law with its reason; `build_db` runs it after the danger facts.
- `law` is the lookup (native, foreign, none; `newworld/sources/key.json`). `place_law` holds one row per place:
  `law_id`, `jail_place_id` (foreign law only: the place whose cell holds the sentence) and `why`.
- `python3 -m tools.newworld.place_law list` prints every place by law, `counts` the totals, and `check` the
  invariants (`make check` runs them in `tools/tests/test_newworld_law.py`).

## Which law a place keeps

Read from the place's `held_by`, its disposition and its kind:

1. **None**: a hostile or abandoned place, or one with no people. It has no guards to arrest anyone, and the player
   meets its fight.
2. **Foreign**: `held_by` names an office inherited from the Empire. That is either the Archwardens, who hold the
   old Imperial forts, keeps, posts and lights in their own name, or a city governed from an Imperial building
   still standing (Gideon's Governor's Mansion and courthouse, Archon's East Empire Company halls, Soulrest's
   ex-Imperial civil office). A fort, keep or city serves its sentences in its own cell. The keeper of a post or
   light without one sends the prisoner to the same keeper's nearest fort or keep.
3. **Native**: every other place where people live, whatever its culture: a city such as Helstrom and a camp alike.

Of the 258 places, 143 keep native law, 16 foreign law and 99 none.

| Law | Places |
|---|---|
| Foreign (16) | Archon, Gideon and Soulrest (each its own cell); Fort Chalkmoth, Fort Gysilla, Fort Reedmoth, Fort Rustmoth, Fort Shellmoth, Fort Silvermoth, Fort Thornmoth, Fort Willowmoth and Southwatch Keep (each its own cell); Aphon Belvedere (to Fort Silvermoth), Marshgate Watch and Thornway Watch (to Fort Thornmoth), Mistfall Light (to Southwatch Keep) |
| Native (143) | Acra-Tiin, Amalaja, Armanias, Arorha, Aroxhu, Ashgate Post, Ayiin, Badal, Banu-Veeth Post, Bell Station, Blackrose, Brineflat Farm, Causeway-Head Post, Chalkmoth Pit, Chasepoint, Coldbrine Mine, Cutbank Camp, Delta Ferry, Deshaa Post, Dunhallow Plantation, Gaweja, Gaxu-Reet, Giovesse, Gul-Tej, Guxal, Helstrom, Hirecan, Hixinoag, Hokal-Ush, Hutan-Aru, Hutan-Ketu, Hutan-Veel, Icalca, Inoio, Inoja, Ixa-Ruu Farm, Ixha-Neeth Camp, Ixu-Maan, Jal-Resh Post, Jal-Veesa, Jarecai, Joxhi, Julo, Ka-Asei, Kalaxo Cut, Karketa, Kharaxos, Khiar, Korydon, Lilmoth, Lujei, Lujei Ferry, Luntoc, Marzai, Mereweather Estate, Mir-Xal, Myroleon, Nacydes, Nacydes Watch, Nahk-Zeel Station, Natai, Naxan, Neexa-Lul, Nemeon, Noota Nara, Nul-Sakeesh Camp, Nundi, Nuxhal, Oeneas, Oju, Olaxa Station, Olvani, Orji-Hael, Oxayo, Ranvos Landing, Redclay Watch, Redgum Camp, Redtimber Camp, Reed-Sill Weir, Reedfall Farm, Reek-Anu, Reeka-Veesa, Renhu, Sakeepa Station, Sal-Axan, Salaxul, Saltmeadow Farm, Sarth-Hul Station, Seafalls, Seafalls Lighthouse, Sedge-Kal Camp, Sedgeweir, Seeku Farm, Shalaia, Silt-Orrel Estate, Siluo, Slough Point, Stormhold, Surkina, Tal-Neesh Farm, Tapauo, Tazhul, Teel-Fen Weir, Tei-Kur, Tenmal, Tenmal Pits, Teth-Kasa Station, Thorn, Tidewatch Homestead, Toklea, Truowa, Tselan, Tseli-Oon, Tsonac, Tumnatu Cattail Camp, Tumnatu Reed Camp, Tydeos, Tzel-Haar, Ukeel Station, Uluo, Umpholo, Urvyn Farm, Uzu-Tegh, Vandrel Farm, Vel-Sapha Stand, Vesh-Aneel, Veshu-Taal Camp, Vicrium, Wattle-Pool Farm, Xal-Tarek, Xanuc Diggings, Xi-Inou, Xibcan, Xul-Banu Post, Xuvagol, Yalugo, Yina, Ysan, Yulca, Yuva-Goli, Yuvexa, Zeeraxun Roost, Zul-Meeka Station |
| None (99) | Agia Nero, Aithros, Aldanus Watchtower, Anutasil, Anvadas, Aphon Signal Tower, Ashfall Cut, Ashiit Den, Aunike Crown, Bala Karag, Balormaak, Blackdrift, Blackrose Prison, Brackwater Waystation, Brushmound, Bucalos, Calvian Waystation, Calyphe, Dorianth, Dry-Fang Camp, Echo Deep, Eurydike, Fort Lowmoth, Fort Sallowmoth, Fort Swiftmoth, Gandranen, Gemin, Gideon South Watch, Hanaxi Roost, Haxtil-Meht Spire, Hiss-Bank Camp, Hollow Tide Camp, Kaochalit, Karsh-Naal Camp, Kelp-Mouth Cave, Khariton, Kharraluhl, Kit Mounds, Kitsa Burrow, Kornakim, Kyrenos, Loriasel, Marque Landing, Mazurath, Meliton, Meris-Keth, Mirasel, Mistwatch, Mnemosa, Mud-Croak Camp, Mudmoth, Naxiil-Ru Spire, Nenria, Nine Reeds Waystation, Ninth Shaft, Okhu-Thteel Spire, Old Goldseam, Orimel, Oru-Neel, Ovezza, Pelaxis, Percar Scar, Ra'tal Den, Rainbreaker Keep, Redbank Quarry, Reknaa-iit Mound, Ruined Velothi Shrine of Nyrath-Ven, Rushiit Den, Sahlpesh Cave, Salt-Tooth Camp, Seth-Alaxh Roost, Sethiral, Sheh-Ara, Stonecut Quarry, Tailfall Mound, Tailhollow, Tarak Shan, Teku-Sul Spire, The Grey Heron, The Grey Tooth, The Kelp Lantern, The Sallow Anne, Thul-Kesh Spire, Ushaan Camp, Va-Seeth Spire, Virtluush, Vorannuhl, Wrackmoth, Wreck of the Brindle Gull, Wreck of the Brine Gull, Wreck of the Pale Harvest, Wreck of the Resolute Crest, Wreck of the Salt Heron, Wreck of the Silt Bride, Wreck of the Stormwidow, Wreck of the Tidewarden, Zeh-Orun, Zeshul-Tha Spire, Zul-Etha |

## What the player meets when caught

The guard's challenge is vanilla Skyrim's arrest dialogue, with the answers changed by the law:

| | Native law | Foreign law |
|---|---|---|
| Pay | The bounty in gold, as in vanilla | The fine, as in vanilla |
| Serve | **The Owing**: a season of work in the place, no cell | Vanilla jail: the cell, the bed or a lock to pick |
| Resist | The guards fight to the death and take no surrender | Vanilla: the guards attack, and a yield is taken |

## The Owing: the game's jail with no cell

The Owing is vanilla's jail sentence played without a cell. The player chooses it in the arrest dialogue. The sentence's days pass at
once with the screen dark while the player works it off, and the player is then set free at a named spot in the
place and wakes there the next morning. It uses the crime faction's own jail data, so the bounty, the days owed,
the stolen goods and the release are the engine's:

- The send is vanilla's real jail call, sent to a jail marker that stands outside. Measured on the arrest
  dialogue's compiled fragments: vanilla's "go to jail" runs the guard's crime faction's
  `SendPlayerToJail(true, true)`, and Winterhold's own line `SendPlayerToJail(false, true)`, which keeps the player's
  belongings; no vanilla line sends with `abRealJail` false, so the Owing does not rely on it. The Owing's line is an
  INFO of ours in vanilla's "go to jail" topic that carries Winterhold's fragment: no script of ours.
- **What it needs from a place**: a **work spot** (a marker where the sentence is shown being served: a channel
  being dredged, a boardwalk under repair, a field, a kiln) and a **return spot** (the faction's exterior jail
  marker: where the player stands when it ends, in the open near the elder's house or the landing). It also needs
  the faction's stolen-goods container, which is out of reach and belongs to the council, and a follower wait marker. No cell, no jail
  outfit and no player-inventory container are needed, because the player's belongings are not taken.
- **What vanilla takes, and whether it fits**: the bounty is cleared (fits); stolen goods stay with the faction and
  go back to their owners (fits: the sentence repays the harm); days pass by the size of the bounty (fits: a season
  of work); progress toward the next rank is lost in some skills (fits loosely: weeks of hauling are weeks not
  spent practising; the owner may prefer to keep progress). Vanilla's taking and returning of the player's
  inventory is skipped (`abRemoveInventory` false).
- **Resisting at a native place**: the guards take no yield. In vanilla the guards re-offer the arrest when a resisting
  player sheathes their weapon; at a native place they do not, and the fight runs to its end. The resist line is an
  INFO of ours first in vanilla's resist topic (DGCrimeResistArrest), said only by the place's guards, which runs
  our one fragment `TIF_ARG_NoSurrender` (papyrus/): the guard's `SetPlayerResistingArrest()`, as vanilla's resist
  lines run, then the place's guard faction made the player's enemy (`Faction.SetPlayerEnemy`, as vanilla's civil
  war makes a side's soldiers the player's enemies). An enemy fights on and takes no yield; the townsfolk, in the
  crime faction but not the guard faction, are not made enemies, and the guards stay enemies after the fight.
  Why a script: the guards' taking of a yield is the engine's, tied to the crime faction arresting at all, which pay
  and the Owing need. Measured on Skyrim.esm and Update.esm: no faction flag, crime value, combat style flag, actor
  value or game setting names a surrender or yield; the Yield and AcceptYield dialogue subtypes are an actor's own
  surrender (the Dark Brotherhood's, DialogueGeneric's), not the player's.
- **Crime factions**: no central authority keeps native law (the lore: the state holds no power beyond the water's edge), so
  each native place has its own bounty. A foreign post shares its jail place's crime faction, as vanilla's
  holds share one jail.

The place builder reads each place's law from `place_law`, the one source of this fact. Helstrom keeps native law:
its work spot is the landing where the boatman works, its return spot the walkway beside it.
