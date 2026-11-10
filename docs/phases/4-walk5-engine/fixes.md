# Engine lane fix checklist (hand-off state)

Done (uncommitted until the fixes pass): papyrus/*.psc endings (Zones + DisarmZones + Stop), guards (MQ03 20/40,
MQ05, TG01, TG02), MQ01 march (30 enables march/disables hold, StartMarch 3D loop -> 32, Fragment_32 evaluates,
AtFire at the strike, started guard), MQ03 HouseDoor unlock at 20 + Ending, taste completes objective 10.
CleanUp.cs: cell of a non-person placement read from the load order.

Kit (after the port): RunOnce always; Zones registry -> quest script property `Zones` (ObjectReference[]); Target(obj, aliases)
and Finish() refusing objectives without targets and overlapping consecutive zones; DeathSets refuses Essential alias
or base; Travel/Follow/Schedule owner quest set; Snap throws on a deleted winning navmesh; drop bandsFirst param.

MainQuest MQ01: rehost on 079823 (fire 5900,-4700; shed 6150,-4450; cutting 6100,-4300; shore 4350,-4450; water edge
4500,-5150; huts 4900,-5800 / 4750,-5900; planks ~4900,-5450; Deesh's huts marker ON the island at Snap(4850,-5600));
stages 10,20,30,32(hidden),40,41,42,90,91,93; delete 35, camp zone, WaitAtFire, DockEndMarker; march to fire marker
radius 200 gated 32..<40; fire zone half 200 prereq 32 -> 40; shed zone centre 6250,-4300 half 175; huts zone
4850,-5700 half 300x300x250 z -100; shore zones 4350,-4450 half 300; cutters Unaggressive (no combat at the strike:
the talkers Hard-Scale and Rakhee-Tul stay out of it); HouseDoor property for MQ03; targets 10 Wuleen, 20 door,
30 fire, 40 Sal+Deesh, 41/42 shore marker alias; Zones property. MQ03 camp things moved to the new spots; officer
Essential, death trigger removed; targets 10 sap, 11 trap, 12 officer, 20 Nesh, 21 Ties, 22 Nesh, 40 hold door;
oath topics lose NightTold; TheBoat 'where' split exclusive of 'ready'.
MQ04: meshes from the winner (0C7102 BMN for the raised ground/edge); Cut topic < 91; targets.
MQ05: delete KaskaGoPost/EiTujaGoPost + markers; Word = one ungated INFO (speech gate's lines) sets 20; Quarrel/Watch
< 91; Basin < 91 and not while LQ30 == 30; Kaska + Ei Protected, DeathSets(Ei,10,91), Kaska (10,92); targets.
LQ25: MQ05 >= 40 gate in a finish step (throws if missing). LQ30: targets.
BC01: Patron package deleted (she stays home); Debtor follow via kit Follow; Never-Sold Essential no death; Debtor
Protected + death -> 94; TheEstate < 90; CutLoose fallback split day / seen; AfterHello 91 only (+ after90 when written);
ChannelEnd alias; targets. BC02: follows via kit Follow; Never-Sold no death; Tsaxi Protected + death; TheFire < 91; targets.
BC03: Broker, CrewBoss Protected (deaths kept); LastSeason/TheSeason < 90; targets.
TG01: trapdoor alias; targets; TG02: pledges as created-in-box QuestObject aliases; targets.
