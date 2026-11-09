# Town life in Skyrim.esm: how Bethesda sets up a town's people (decision 0034)

Measured 2026-11-09 from Skyrim.esm with Update.esm's overrides (880,130 records, 713,023 placed refs). Towns: Riverwood
(TownRiverwoodFaction, 14 NPCs), Ivarstead (TownIvarsteadFaction, 10), Whiterun (TownWhiterunFaction). Spriggit `serialize`
of Skyrim.esm stops on Linux at the localized-string step, so a throw-away raw record reader was used (not kept). Every
figure names its record by editor id. Hours are game hours; `h8 dur12` = starts 8:00, lasts 12 h. Bethesda names a PACK
`<Who><What><start>x<hours>` (AlvorWork8x12). "Linked ref" is an XLKR with no keyword. Not decoded: PKDT flags, Papyrus bodies.

## 1. The shape of a day

PACK = PSDT (hour, minute, duration in minutes) + PKCU (template) + PLDT (location). A town NPC_ lists 3-6 PACKs in PKID.
Template mix (PACKs on town NPCs): Riverwood Sandbox 27, Eat 18, Sleep 14, SandboxWorking 6, Travel 6, Patrol 3.
Ivarstead Eat 19, Sleep 9, Sandbox 5, SandboxMultiLocation 4, SandboxWorking 2. Whiterun Sandbox 118, Sleep 51, Eat 22,
Travel 18, Patrol 15, Sit 10, SitTarget 4. Also seen once or twice: SandboxAndKeepEyeOn, CarryAndDropItem, Activate,
ActivateSpecialFurniture, UseIdleMarker, ForceGreet.
- Sleep starts: Riverwood 0:00 x9, 22:00 x3, 23:00, 2:00; lasts 5-9 h (mode 7). Ivarstead 0:00 x7, 4:00 (Narfi), 22:00
  (BassianusAxius); lasts 4-8 h (mode 5-6). Whiterun 0:00 x17, 22:00 x7, 20:00-21:00 x5; 8 h x26 (DefaultSleepEditorLoc24x8).
- Eat is always 60 min. Riverwood starts 6 (x6), 7, 12, 18, 20 (x4). Ivarstead 4-6 (breakfast), 11-13, 15-18 (dinner), 20.
- Sleep location: either `NearEditorLoc r500/r2000` (DefaultSleepEditorLoc22x7 r2000, AlvorSleepPackage r500), or `InCell`
  home (GerdurSleepHome22x9, FaendalSleepHome23x5), or `NearRef <the owned bed> r0` (all nine Ivarstead sleepers,
  e.g. IvarsteadBotiSleepPackage on bed 0658AD CommonBed01L). Eat: `NearEditorLoc r500` (DefaultEatEditorLoc6x1), `InCell` home
  (IvarsteadBotiEatBreakfastPackage), or a table XMarker r100-512 (IvarsteadGwilinEatDinnerPackage r100, EmbryEat7x1 r512).
- Work/wander location: `NearRef <XMarker or XMarkerHeading> r128-800` (AlvorWork8x12 r600, HildeLoiter8x12 r128,
  EmbryLoiter8x9 r700); multi-spot work uses SandboxMultiLocation / SandboxWorkingMultiLocation with 3-4 XMarkers r200-800
  plus empty NearEditorLoc r0 slots (GerdurWorkPackage7x12, IvarsteadBotiFarmingPackage r200). Default fallback with no hours:
  DefaultSandboxEditorLocation512 (NearEditorLoc r512), DefaultSandboxHomeowner (r1500).
- Per role (editor ids):
  - Smith Alvor: Sleep 0 dur6 (AlvorSleepPackage); AlvorWork8x12 SandboxWorking at forge marker 02C308; Eat 20 dur1
    (AlvorSigridDortheEat20x1); AlvorTavernPackage21x2 Sandbox at the inn marker 08AFC4 r768.
  - Merchant Lucan (LucanValerius): LucanSleep0x6 in shop cell; LucanBreakfast6x1; LucanValeriusTraderServices7x13
    (SandboxAndKeepEyeOn at 0801F9 r128, 7-20); LucanRiverwoodEatInn20x4 (Eat at a bench r500). Belethor: 8-20
    WhiterunBelethorGeneralGoodsSellPackage (SandboxAndKeepEyeOn); 20 dur4 WhiterunBelethorPatrolCityPackage (Patrol).
  - Innkeepers: Orgnar has one PACK, OrgnarWorkInn0x24 (SandboxWorking, 24 h, marker 0BD056 r256) and no Sleep. Hulda one
    (WhiterunInnkeeperPackage Sandbox r100). Wilhelm one (SitTarget at IvarsteadInnkeeperMarker). Lynly sleeps 0 dur5, else Sit
    at CounterBarLeanMarker or SandboxAndKeepEyeOn InCell the inn (barmaid).
  - Farmers (Ivarstead Boti, Fastred, Jofthor): sleep 0 (6-8 h), meals 6 / 11 / 15 in the farm cell, farming default pack
    (no hours) SandboxMultiLocation. Boti housework 16 dur7; Jofthor drinks at the inn 18 dur4 (IvarsteadJofthorDrinkInnPackage).
  - Residents: Hilde loiters 8 dur12, eats 18, sleeps 22 dur7. Citizens Gwilin / Temba visit the inn 17 dur7 / 20 dur4.
    Narfi (beggar): sleeps bedroll 4 dur5, eats 10 and 20, wanders 4 markers r128-256.
  - Lumberjack Hod: sleep 0 dur8, eat 6, sawmill 8 dur11 (HodSawmillSawLog8x11 Activate lever, ...LoadLog ActivateSpecialFurniture,
    ...Sandbox), inn 19 dur3 (SandboxMultiLocation, 2 inn markers). Child Frodnar: play 7 dur12, eat 6, sleep 0 dur8.
  - Priest Heimskr: shrine 5 dur15 (Travel to PrayerIdleMarker), home 20 dur4. Trainer Amren: sit and repair 8 dur3, home 19
    dur4, tavern 23 dur3. Smith Adrianne: forge 6 dur11, home 17 dur3, city walk 20 dur4.
- Gaps between PACKs (Alvor 23-0 and 6-8) fall to the last or default package: engine behaviour not measured.

## 2. Guards and patrols (Whiterun only; Riverwood and Ivarstead have none)

- No NPC of TownRiverwoodFaction or TownIvarsteadFaction is in a guard faction. Their crimes go to the hold's CrimeFaction.
- Whiterun guard NPC_ (GuardWhiterunSonsPatrolDayExterior) is templated on GuardWhiterunSonsTemplate (-> LvlGuardSons). Factions:
  CrimeFactionSons, CrimeFactionWhiterun, CWSonsFaction, GuardFactionWhiterun, IsGuardFaction, GuardDialogueFaction, TownWhiterunFaction.
- Two shifts of 12 h, each with its own sleep PACK in cell WhiterunGuardHouse (4 beds, owner GuardFactionWhiterun):
  day = GuardWhiterunPatrolExteriorDayA (Patrol, 9:30 dur12) + GuardWhiterunDaySleepGuardTowerA (Sleep 21:30 dur12);
  night = GuardWhiterunPatrolNightPatrol (Patrol 21:00 dur12) + GuardWhiterunNightSleepGuardTower (Sleep 9:00 dur12).
- Patrol PACK target is the placed ref's own linked ref (PTDA type 3 = linked ref). The ref links to a PatrolIdleMarker that links to the next
  (a chain): marker 02C934 chain 21 markers, 02C935 chain 8 (XPRD wait 6 s, then 0), 0370A3 chain 6, 0370C7 chain 12.
  Placed groups per shift: PatrolDay1/2 (2 guards each), PatrolNight1/2 (2 each), PostDay2/PostNight1/2 (single XMarkerHeading).
- Fixed posts: GuardWhiterunSonsGate x2 (WhiterunGateGuardTravel, linked XMarkerHeading), GuardWhiterunSonsDragonsreach x6
  (linked XMarkerHeading or SoldierWallIdle), PorchPatrol x2 (two links), watchtower patrol x3 (WhiterunWatchtowerExterior), jail x3
  (WhiterunDragonsreachBasement, markers PatrolIdleMarker / NobleChair02R). Total 39 ACHR for the Sons side, a parallel set for the Imperial
  side (civil war swaps them). Hold-outer guards: farms (PelagiaFarmExterior) link CWLinkGuardContested1 for the contested-hold PACK.
- Guard AIDT: aggression 0, confidence 2, energy 50, responsibility 3 (GuardWhiterunSonsPatrolDayExterior).

## 3. Merchants

A vendor is a FACT `Services<Town><Shop>` with: VEND (FLST of keywords), VENC (ref of the vendor chest), VENV (start hour, end hour, radius,
flags) and PLVD (the shop area). Seller NPCs hold the Services faction, JobMerchantFaction, a Job<Trade>Faction, the town and crime factions.
| Vendor faction | VEND list (keywords) | hours | area (PLVD) | chest (CONT) owner |
|---|---|---|---|---|
| ServicesRiverwoodAlvor | VendorItemsBlacksmith (6) | 0-24 r256 | NearRef 02C308 forge marker | MerchantRiverwoodAlvorBlacksmithChest, persistent exterior ref; RiverwoodAlvorsHouseFaction |
| ServicesRiverwoodRiverwoodTrader | VendorItemsMiscLucan (3) | 7-20 r0 | InCell RiverwoodRiverwoodTrader | MerchantRiverwoodTraderChest in shop; RiverwoodRiverwoodTraderFaction |
| ServicesRiverwoodSleepingGiantInn | VendorItemsInnkeeperOrgnar (3) | 0-23 r256 | InCell the inn | MerchantRiverwoodSleepingGiantChest; RiverwoodSleepingGiantInnFaction |
| ServicesIvarsteadVilemyrInn | VendorItemsInnkeeper (2) | 0-24 r0 | InCell the inn | MerchantIvarsteadVilemyrInnChest; the Services faction itself |
| ServicesWhiterunBelethorsGoods | VendorItemsMisc (2) | 8-20 r0 | InCell shop | MerchantWhiterunBelethorsGoodsChest; no owner |
| ServicesWhiterunArcadiasCauldtron | VendorItemsApothecary (7) | 8-20 | InCell shop | ...ArcadiasCauldronChest; WhiterunArcadiasCauldronFaction |
| ServicesWhiterunWarmaidens / ...Forge | VendorItemsBlacksmith (6) | 8-20 / 6-20 r600 | InCell / tanning rack marker | MerchantWhiterunWarmaidensBlacksmithChest |
| ServicesWhiterunEorlund | VendorItemsBlacksmith (6) | 0-23 r700 | skyforge ref | MerchantWhiterunEorlundChest (shared exterior cell) |
- VENV byte 9 = 1 on the two general-goods vendors (Lucan, Belethor): they buy and sell everything except their list.
- Stock lists (FLST): VendorItemsBlacksmith = AnimalHide, Arrow, Weapon, OreIngot, Tool, Armor; VendorItemsInnkeeper = FoodRaw, Food;
  VendorItemsMisc = VendorNoSale, Key. Gold in the chest is a LVLI: VendorGoldInn 100, VendorGoldMisc 750, VendorGoldBlacksmith 1000.
- Chest contents are mostly levelled lists (LItem..., VendorBlacksmithEnchWeaponsLevel20): our chests must be fixed lists (0035).
  Chest sizes: Alvor 22 entries, Lucan 26, Orgnar 12, Ivarstead inn 4 (SaltPile, VendorGoldInn, LItemInnRuralDrink x7, LItemFoodInnCommon x10).
- Ownership in the shop cell (RiverwoodRiverwoodTrader): goods (ALCH 28, WEAP 5, AMMO 3, MISC 2, ARMO 1) owned by the Services faction
  (taking = theft); CONT x4 and DOOR x2 by RiverwoodRiverwoodTraderFaction; the person's own CONT / FURN by LucanValerius.

## 4. Beds and houses

- Bed refs (FURN CommonBed01, 01L, 01R, Bedroll01, NobleBedSingle01) carry XOWN: a person (single occupant), a one-person faction
  (IvarsteadTembaFaction, IvarsteadKlimmekFaction), or the house faction (RiverwoodAlvorsHouseFaction etc.). CommonBedDouble01 and
  NobleBedDouble01 have 2 FNPR sleep markers; the rest 1.
- Riverwood: Alvor's House 3 spots (CommonBed01R + CommonBedDouble01, both house faction) for Alvor, Sigrid, Dorthe; Gerdur's 3 (double + 01L)
  for Gerdur, Hod, Frodnar; Faendal 1; Sven's House 2 (owners Sven, Hilde); Trader 2 (Camilla faction, LucanValerius); inn 3 (2 owned by
  RiverwoodSleepingGiantInnFaction, NobleBedSingle01 owned by Delphine; Embry sleeps in the inn).
- Ivarstead: farm 3 (owners Fastred, Boti, Jofthor); Klimmek's House 2 (BassianusAxius, IvarsteadKlimmekFaction); inn 5 (Gwilin, Lynly, IvarsteadTembaFaction,
  IvarsteadVilemyrInnFaction CommonBed01L, Bedroll01L); Narfi's Bedroll01 outdoors. Whiterun: 54 sleepers with a Sleep PACK, house beds 1-6 per house (WhiterunHouseBattleBorn 6).
- Spots versus sleepers (a double counts 2): Riverwood 14 spots, 13 NPCs with a Sleep PACK (Orgnar none): 1 spare. Ivarstead 11 spots, 9 sleepers
  (Wilhelm none): 2 spare, both inn-faction beds (the rentable ones).
- House doors are owned by the house faction (RiverwoodAlvorsHouse DOOR), idle markers inside by the person (4 IDLM owned by Sigrid).

## 5. Crime factions

- Every Riverwood NPC is in CrimeFactionWhiterun, every Ivarstead NPC in CrimeFactionRift (165 and 193 members), plus the town faction and a house faction.
  TownRiverwoodFaction / TownWhiterunFaction / GuardFactionWhiterun carry only DATA 0x8000 (can be owner); no crime fields.
- CrimeFactionWhiterun: DATA 0x9040 (track crime, gold defaults, can be owner); JAIL PrisonMarker 0267E5, WAIT XMarkerHeading 0267E6 (both in cell 0001A270);
  STOL EvidenceChestStolenGoods 09DC64 and PLCN EvidenceChestPlayerInventory 0267E8 (WhiterunDragonsreachBasement); JOUT BeggarOutfit; CRGR CrimeFactionsList (FLST).
  CRVA: arrest yes, attack on sight yes, murder 1000, assault 40, trespass 5, pickpocket 25, steal x0.5, escape 100, werewolf 1000. XNAM: PlayerWerewolfFaction, VampirePCFaction.
- CrimeFactionRift: same CRVA; JAIL = WAIT = PrisonMarker 03EF58 (Riften), STOL 0A9069 and PLCN 0A8F33 in RiftenJail01. The two small towns have no jail of their own.

## 6. Innkeepers, trainers, carriages, shrines

- Rent: innkeepers hold JobRentRoomFaction (rank 255) with JobInnkeeperFaction (Orgnar, Lynly, Wilhelm, Saadia). RentRoomTopic (DIAL 0009CC92, quest DialogueGeneric)
  INFO 0009CC94 needs the speaker in JobRentRoomFaction and Gold001; cost GLOB RoomCost = 10; fragment TIF__0009CC94 sets the rental (compiled Papyrus: how the rented
  bed is assigned is not measured). Beds to rent are the inn-faction-owned ones (section 4). Delphine has her own DelphineRentRoomBranch.
- Trainers: the class record teaches one skill to a maximum level (CLAS DATA): TrainerMarksmanJourneyman (Faendal) Archery 50; TrainerOneHandedJourneyman (Amren)
  OneHanded 50; TrainerAlchemyExpert (Arcadia) Alchemy 75; TrainerSmithingMaster (Eorlund) Smithing 90; TrainerRestorationMaster (Danica) Restoration 90.
  Plus JobTrainerFaction and Job Trainer<Skill>Faction. GMST fTrainingMultCost 10, iTrainingExpertCost 3, iTrainingMasterCost 5.
- Carriage (Skyrim.esm has no boats; Solstheim ferries are in Dragonborn.esm: not measured): NPC_ CarriageDriverWhiterun (CarriageSystemFaction + the hold crime
  faction) with two PACKs, CartDriverOnCart (SitTarget) and CartDriverOnCartForcegreet (ForceGreetFromSitting, r325). ACHR 013698 links: no-keyword -> CartFurnitureDriver
  1070F1, LinkCarriageSeat -> CartFurniturePassenger 1070F0, LinkCarriageHorse -> HorseForCarriageNew 09B7A9. Quest DialogueCarriageSystem (script CarriageSystemScript) holds
  one driver property per town and one stop per destination; fares are GLOB CarriageCost 20 and CarriageCostSmall 50.
- Shrines: ACTI ShrineofAkatosh, ...ofTalos, ...ofKynareth etc. carry TempleBlessingScript (TempleBlessing = SPEL AltarAkatoshSpell / AltarTalosSpell ..., BlessingMessage,
  AltarRemoveMsg). Placed only inside temples: WhiterunTempleofKynareth 1, WhiterunHalloftheDead 2, Solitude 18. None in Riverwood or Ivarstead.

## Rules our drafter follows

1. Every named townsperson gets 3-6 PACKs on templates, named `<Who><What><start>x<hours>`, ordered eat, work, social, sleep.
2. Sleep (Sleep template) starts 0:00 (22:00 for children's households and elders), lasts 6-8 h, target the owned bed `NearRef r0`, else `NearEditorLoc r500-2000`.
3. Meals are Eat, 60 min: breakfast 6-7, midday 12-13, dinner 18-20, in the home cell or at a table marker r100-512.
4. Workers use SandboxWorking, start 7-8, last 11-13 h, `NearRef` a work XMarker r512-800; forge, mill and saw use Activate / ActivateSpecialFurniture PACKs.
5. A shopkeeper's shop hours are VENV 8-20 (0-24 with a marker radius 256 for smiths and inns); sleeps 0 dur6 in the shop cell; eats dinner at the inn 20 dur4.
6. Innkeepers have one 24 h Sandbox / SandboxWorking PACK at a counter marker r100-256 and no Sleep PACK; vendor 0-23; JobRentRoomFaction 255; rent 10 gold.
7. Every vendor is one `Services<Town><Shop>` FACT: a VEND FLST of 2-7 keywords, a VENC chest CONT of its own, VENV hours and a PLVD area; chests hold fixed items (no levelled lists).
8. Shop goods are owned by the Services faction, the chest, doors and containers by the shop faction, personal items by the person.
9. Beds: one per sleeper (a double counts 2), owned by the person or a one-person faction, else the house faction; every inn has at least 2 inn-faction beds to rent.
10. Spare beds per town: 1-2, all in the inn; the drafter fails a town with fewer beds than sleepers.
11. Every NPC joins CrimeFaction<Hold>, the town faction and a house or shop faction; a town without guards uses the hold's jail.
12. A crime faction sets JAIL, WAIT, STOL, PLCN, JOUT, CRGR and CRVA (arrest, attack on sight, murder 1000, assault 40, trespass 5, pickpocket 25, steal x0.5, escape 100).
13. Guards exist only in hold capitals: two 12 h shifts (patrol 9:30 / 21:00, sleep the other half in the guardhouse), patrol = Patrol PACK on a linked PatrolIdleMarker chain of 6-21 markers.
14. Posts and gates are one guard linked to one XMarkerHeading; a hold capital's guards number about 39 per allegiance.
15. Trainers' class names the skill and cap (Journeyman 50, Expert 75, Master 90); the trainer has an 8-20 work PACK and a job faction for that skill.
16. A carriage driver is an NPC with CarriageSystemFaction, 2 PACKs, a linked seat, horse and passenger seat; fares 20 / 50 gold.
17. Shrines are ACTI with TempleBlessingScript and an altar SPEL, placed inside temples only.
18. Children play 7 dur12 near a sibling, eat 6, sleep 0 dur8.
19. Beggars and wanderers use SandboxMultiLocation over 3-4 XMarkers r128-256 and sleep on a bedroll 4 dur5.
20. Leave no gap that matters at night: not measured how Bethesda fills gaps, so the drafter never relies on one.
