using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;
using Noggog;
using static QuestKit;

// The opening act's first two main quests (Phase 4 part C): MQ01 "No Name on the Work Roll" (the new game: the barge hold
// at Lilmoth's dock, the march, the camp on the shore beside the dock and the strike) and MQ03 "A Dead Prisoner's
// Use" (the camp at dawn, the Reed's house in Lilmoth, the dream in the empty hold), from quest.main.mq01 and
// quest.main.mq03. Journal and objective text from the story data rows; the lines from story/data/quest_lines/mq01.json
// and mq03.json. Every stage, trigger, condition and effect is a proven block's shape (docs/design/blocks.md); where the
// record names a shape with no proven block, the re-authoring is named where it is built (and in Phase 4's Measured):
// the three scenes (opening, strike, dream) have no written lines, so the march ends at a fire zone (32 -> 40), the strike
// is stage 40's fragment, and the dream ends at a door zone (40 -> 45 -> 90/91 on the oath global).
// MQ101's override starts ARG_MQ01 (Generate); ARG_Opening keeps its forms and never starts. Called after NightReed.
static class MainQuest
{
    static readonly FormKey World = K("23D689:Black Marsh.esm"), Lockpick = K("00000A:Skyrim.esm");
    // Hosts (measured with `plugin.sh inspect navpath` / `navnear`): the barge hold and its navmesh (main deck z 7010);
    // Lilmoth's Dock1 (1,-2) navmesh 079823, the plank's foot at 5350,-7800 and, on the one mesh, the whole camp (the owner's
    // ruling: the camp stands beside the dock, so the march and every route of the strike lie on one island); the Reed's
    // house (BM&V's sinking cabin: no navmesh where the rooms are, a floor tilted 0.4 rad, top z = 7409 + (1301 - y) * 0.4228,
    // read from its floor pieces).
    public static readonly FormKey HoldCell = K("0F9178:Black Marsh.esm"), HoldNav = K("0F9179:Black Marsh.esm"),
        DockNav = K("079823:Black Marsh.esm"), HouseCell = K("0FE7F7:Black Marsh.esm"),
        HoldDoor = K("0F92EC:Black Marsh.esm"), HoldDoorFar = K("0F9399:Black Marsh.esm"), PierDoor = K("005AB4:Black Marsh.esm"), HouseDoorOut = K("0FE95A:Black Marsh.esm"), DaintySload = K("07B91A:Skyrim.esm"),
        Welcome = K("03B21E:Black Marsh.esm");
    public static readonly string[] Valenwood = ["0BCC51:Valenwood.esp", "0F0F3E:Valenwood.esp"];
    public static float HouseFloor(float y) => MathF.Round(7409 + (1301 - y) * 0.4228f);
    // The camp's spots (x, y): the fire, the shed and the cutting at the far (east) end, the huts over the water to the south
    // west under the plank boards (Deesh-Duun's marker on the island at the huts' end), the shore end (the endings) to the
    // west, the water's edge where the leader goes.
    public static readonly (float X, float Y) Fire = (5900, -4700), Shed = (6150, -4450), Cutting = (6100, -4300), Huts1 = (4900, -5800),
        Huts2 = (4750, -5900), HutsEnd = (4850, -5600), Planks = (4900, -5450), Trap = (4850, -5650), Shore = (4350, -4450), WaterEdge = (4500, -5150);

    // MQ01 alias ids.
    public const uint A1WuleenHold = 0, A1UxHold = 1, A1Buys = 2, A1Courier = 3, A1WuleenMarch = 4, A1UxMarch = 5, A1DivesMarch = 6,
        A1FindsMarch = 7, A1Sal = 8, A1Deesh = 9, A1Leader = 10, A1Cutter1 = 11, A1Cutter2 = 12, A1Ties = 13, A1ZoneFire = 14,
        A1ZoneShed = 15, A1ZoneHuts = 16, A1Shore90 = 17, A1Shore91 = 18, A1Shore93 = 19, A1HoldDoor = 20, A1FireMark = 21, A1ShoreMark = 22;
    // MQ03 alias ids.
    public const uint A3Officer = 0, A3Stranger = 1, A3Sap = 2, A3Nesh = 3, A3Salts = 4, A3Ties = 5, A3DoorZone = 6, A3Trap = 7, A3HoldDoor = 8;

    public static Quest Mq01 = null!, Mq03 = null!;
    public static PlacedObject StartMarker = null!;
    static P3Float HoldInside;  // the arrival spot inside the hold, in front of its stair door
    // record person id -> our base editor ids that speak for it (the read-back's speaker check)
    public static readonly Dictionary<string, string[]> Speakers = [];
    public sealed record Line(string Quest, string Topic, string Variant, string Edid, string Prompt, string[] Text, string? Script, string? Body);
    public static readonly List<Line> Lines = [];

    // What MainQuestCheck reads: the record's lines and objectives (stage, index = stage + order within the stage, text).
    public static JsonElement LinesOf(string code) => QuestKit.QuestLines(code);
    public static List<(int stage, int index, string text)> Objectives(string quest) =>
        [.. QuestKit.Objectives(quest).GroupBy(o => o.stage).SelectMany(g => g.Select((o, i) => (g.Key, g.Key + i, o.text)))];

    public static void Add(SkyrimMod mod, List<ISkyrimModGetter> mods)
    {
        Mq01 = mod.Quests.AddNew("ARG_MQ01");
        Mq03 = mod.Quests.AddNew("ARG_MQ03");
        var mq01Parts = BuildMq01(mod, mods);
        BuildMq03(mod, mods, mq01Parts);
        Console.WriteLine($"main quest: MQ01 {Mq01.FormKey}, MQ03 {Mq03.FormKey}, {Lines.Count} lines");
    }

    sealed record Mq01Parts(PlacedNpc Ties, PlacedObject Survivors, PlacedObject Broker, PlacedObject Aftermath);

    static Mq01Parts BuildMq01(SkyrimMod mod, List<ISkyrimModGetter> mods)
    {
        var q = Mq01;
        var kit = new QuestKit(mod, mods, q) { TifNote = "Generated by tools/ArgoniaPlugin/MainQuest.cs: one main-quest line's end fragment (TR-topic)." };
        kit.OnLine = l => Lines.Add(new Line("MQ01", l.Key, l.Variant!, l.Id, l.Prompt, l.Text, l.Script, l.Body));
        var world = kit.World(World);
        const NpcConfiguration.Flag P = NpcConfiguration.Flag.Protected, U = NpcConfiguration.Flag.Unique, E = NpcConfiguration.Flag.Essential;
        // Templates: BM&V's Argonians (female 160E6A, 02A1EE; male 00FF4D, 045E50, 1DE49D, 02A1E6), vanilla Khajiit (Ri'saad,
        // Atahba) and a Dunmer woman (Brelyna Maryon) for looks.
        var wuleen = kit.Base("ARG_MQ01_WuleenSei", "Wuleen-Sei", "160E6A:Black Marsh.esm", 10, P | U, Ai.Own);
        var wuleenM = kit.Base("ARG_MQ01_WuleenSeiMarch", "Wuleen-Sei", "160E6A:Black Marsh.esm", 10, P | U, Ai.Own);
        var ux = kit.Base("ARG_MQ01_UxXeek", "Ux-Xeek", "02A1EE:Black Marsh.esm", 5, P | U, Ai.Own);
        var uxM = kit.Base("ARG_MQ01_UxXeekMarch", "Ux-Xeek", "02A1EE:Black Marsh.esm", 5, P | U, Ai.Own);
        var buys = kit.Base("ARG_MQ01_BuysTheMonths", "Buys-The-Months", "045E50:Black Marsh.esm", 10, P | U, Ai.Own);
        var courier = kit.Base("ARG_MQ01_MeeTuja", "Mee-Tuja", "1DE49D:Black Marsh.esm", 8, U, Ai.Own);
        var dives = kit.Base("ARG_MQ01_DivesWithoutARope", "Dives-Without-A-Rope", "160E6A:Black Marsh.esm", 4, P | U, Ai.Own);
        var divesM = kit.Base("ARG_MQ01_DivesWithoutARopeMarch", "Dives-Without-A-Rope", "160E6A:Black Marsh.esm", 4, P | U, Ai.Own);
        var finds = kit.Base("ARG_MQ01_FindsTheOtherBank", "Finds-The-Other-Bank", "02A1EE:Black Marsh.esm", 4, P | U, Ai.Own);
        var findsM = kit.Base("ARG_MQ01_FindsTheOtherBankMarch", "Finds-The-Other-Bank", "02A1EE:Black Marsh.esm", 4, P | U, Ai.Own);
        // the rest of the gang: two refs each (the hold, and the shore's survivors), never both enabled, so not Unique
        var risakka = kit.Base("ARG_MQ01_RiSakka", "Ri'Sakka", "01B1DB:Skyrim.esm", 4, P, Ai.Own);
        var tsanji = kit.Base("ARG_MQ01_Tsanji", "Tsanji", "01B1DA:Skyrim.esm", 4, P, Ai.Own);
        var llarvi = kit.Base("ARG_MQ01_LlarviMaryon", "Llarvi Maryon", "01C196:Skyrim.esm", 4, P, Ai.Own);
        var neshNeel = kit.Base("ARG_MQ01_NeshNeel", "Nesh-Neel", "160E6A:Black Marsh.esm", 4, P | U, Ai.Own);
        var sal = kit.Base("ARG_MQ01_SalSei", "Sal-Sei", "00FF4D:Black Marsh.esm", 5, U, Ai.Own);
        var deesh = kit.Base("ARG_MQ01_DeeshDuun", "Deesh-Duun", "02A1EE:Black Marsh.esm", 5, U, Ai.Own);
        var ties = kit.Base("ARG_MQ01_TiesTheLoosePlank", "Ties-The-Loose-Plank", "02A1E6:Black Marsh.esm", 5, E | U, Ai.Own);
        var leader = kit.Base("ARG_MQ01_CutsTheOldKnot", "Cuts-the-Old-Knot", "160E6A:Black Marsh.esm", 20, U, Ai.Own);
        // unaggressive: no combat at the strike, so BM&V's talkers Hard-Scale and Rakhee-Tul to the north are neither attacked nor drawn in
        var cutter = kit.Base("ARG_MQ01_RootCutter", "Root-Cutter", "00FF4D:Black Marsh.esm", 3, 0, Ai.Own);
        var root = kit.Faction("ARG_UnboundRoot", "Unbound Root", true);
        foreach (var n in new[] { leader, cutter }) n.Factions.Add(new RankPlacement { Faction = root.ToLink<IFactionGetter>(), Rank = 0 });
        foreach (var (rec, ids) in new (string, string[])[] {
            ("npc.pirate-freeholds.opening-work-barge.npc-opening-overseer", ["ARG_MQ01_WuleenSei", "ARG_MQ01_WuleenSeiMarch"]),
            ("npc.pirate-freeholds.opening-work-barge.npc-opening-roll-reader", ["ARG_MQ01_UxXeek", "ARG_MQ01_UxXeekMarch"]),
            ("npc.mercantile-coast.lilmoth.broker-buys-the-months", ["ARG_MQ01_BuysTheMonths"]),
            ("npc.pirate-freeholds.opening-work-camp.n1-2", ["ARG_MQ01_DivesWithoutARope", "ARG_MQ01_DivesWithoutARopeMarch"]),
            ("npc.pirate-freeholds.opening-work-camp.n1", ["ARG_MQ01_TiesTheLoosePlank"]) })
            Speakers[rec] = ids;

        // Items: Sal-Sei's reed-knife (e-sal's reward; our copy of the iron dagger, renamed).
        var knife = Survey.Winners<IWeaponGetter>(mods)[K("01397E:Skyrim.esm")].rec.Duplicate(mod.GetNextFormKey());
        knife.EditorID = "ARG_MQ01_SalReedKnife"; knife.Name = "Sal-Sei's Reed-Knife"; knife.VirtualMachineAdapter = null;
        mod.Weapons.Add(knife);
        var rollRead = kit.Global("ARG_MQ01_RollRead");
        var answered = kit.Global("ARG_MQ01_Answered");
        var savedSal = kit.Global("ARG_MQ01_SavedSal");     // flag.mq01.saved-sal (E-global)
        var savedDeesh = kit.Global("ARG_MQ01_SavedDeesh"); // flag.mq01.saved-deesh

        // Places. The hold (we.mq01.start, .barge-crew, .gang): the main deck, away from the door 0F9399 at the far end.
        StartMarker = kit.Marker("ARG_MQ01_StartMarker", kit.Snap(HoldNav, 2750, 3900, 7010));
        var holdParent = kit.Marker("ARG_MQ01_HoldParent", new P3Float(2750, 3700, 6700), null, 0x400);   // on until 40
        var crewParent = kit.Marker("ARG_MQ01_CrewParent", new P3Float(2750, 3750, 6700), null, 0x400);   // on until the end
        var wuleenRef = kit.Actor("ARG_MQ01_WuleenSeiRef", wuleen, kit.Snap(HoldNav, 2850, 4300, 7010), crewParent);
        var uxRef = kit.Actor("ARG_MQ01_UxXeekRef", ux, kit.Snap(HoldNav, 2950, 4150, 7010), crewParent);
        var gangHold = new[] { (dives, 2650f, 4000f), (finds, 2700f, 3800f), (risakka, 3000f, 3900f), (tsanji, 3100f, 4400f), (llarvi, 2600f, 4450f) }
            .Select(g => kit.Actor($"ARG_MQ01_{g.Item1.EditorID![9..]}HoldRef", g.Item1, kit.Snap(HoldNav, g.Item2, g.Item3, 7010), holdParent)).ToList();
        // The hold cell: the vanilla location 'Dainty Sload' cleared (we.mq01.hold-location).
        var hold = kit.Interior(HoldCell);
        hold.Location.Clear();
        hold.Persistent.AddRange([StartMarker, holdParent, crewParent, wuleenRef, uxRef, .. gangHold]);
        // we.mq01.hold-door (W-override, the door audit of walk 4): the hold is BM&V's copy of the ship 01Ship, whose way out
        // Black Marsh North moved to the door at the top of the stairs (0AA6C9); the copy's stair door 0F92EC has a load
        // door's model and no teleport (it did nothing), and its far door 0F9399, an opening door with a room behind it,
        // teleported to the pier. The stair door becomes the way out, paired with the pier door 005AB4 both ways (the
        // arrival in the hold is BMN's own in front of 0AA6C9; on the pier, 0F9399's old one), locked with no key until
        // the answer (stage 20's fragment unlocks it); 0F9399 loses its teleport and opens onto its room.
        var holdTo = ((IPlacedObjectGetter)kit.Placed[HoldDoorFar].rec).TeleportDestination!;
        var stairIn = ((IPlacedObjectGetter)kit.Placed[K("039827:Black Marsh.esm")].rec).TeleportDestination!;
        var stairDoor = (PlacedObject)((IPlacedObjectGetter)kit.Placed[HoldDoor].rec).DeepCopy();
        stairDoor.MajorRecordFlagsRaw |= 0x400;
        stairDoor.TeleportDestination = new TeleportDestination { Position = holdTo.Position, Rotation = holdTo.Rotation };
        stairDoor.TeleportDestination.Door.SetTo(PierDoor);
        stairDoor.Lock = new LockData { Level = LockLevel.RequiresKey };
        var farDoor = (PlacedObject)((IPlacedObjectGetter)kit.Placed[HoldDoorFar].rec).DeepCopy();
        farDoor.TeleportDestination = null; farDoor.MajorRecordFlagsRaw |= 0x400;
        var pierDoor = (PlacedObject)((IPlacedObjectGetter)kit.Placed[PierDoor].rec).DeepCopy();
        pierDoor.MajorRecordFlagsRaw |= 0x400;
        pierDoor.TeleportDestination = new TeleportDestination { Position = stairIn.Position, Rotation = stairIn.Rotation };
        pierDoor.TeleportDestination.Door.SetTo(HoldDoor);
        hold.Persistent.AddRange([stairDoor, farDoor]);
        world.TopCell!.Persistent.Add(pierDoor);
        HoldInside = stairIn.Position;

        // The pier (we.mq01.broker) and the march copies at the plank's foot (we.mq01.march), Dock1's navmesh 079823.
        var brokerParent = kit.Marker("ARG_MQ01_BrokerParent", new P3Float(5380, -7500, -300), null, 0x400);
        var marchParent = kit.Marker("ARG_MQ01_MarchParent", new P3Float(5350, -7800, -300), null, 0xC00);
        var buysRef = kit.Actor("ARG_MQ01_BuysTheMonthsRef", buys, kit.Snap(DockNav, 5380, -7500), brokerParent);
        var courierRef = kit.Actor("ARG_MQ01_MeeTujaRef", courier, kit.Snap(DockNav, 5300, -7350));
        var wuleenMRef = kit.Actor("ARG_MQ01_WuleenSeiMarchRef", wuleenM, kit.Snap(DockNav, 5350, -7800), marchParent);
        var uxMRef = kit.Actor("ARG_MQ01_UxXeekMarchRef", uxM, kit.Snap(DockNav, 5300, -7850), marchParent);
        var divesMRef = kit.Actor("ARG_MQ01_DivesWithoutARopeMarchRef", divesM, kit.Snap(DockNav, 5400, -7880), marchParent);
        var findsMRef = kit.Actor("ARG_MQ01_FindsTheOtherBankMarchRef", findsM, kit.Snap(DockNav, 5250, -7900), marchParent);

        // The camp (we.mq01.camp, .families, .cell), on the dock's navmesh 079823; the dressing from BM&V's and vanilla
        // statics under three enable parents (orderly, attacked, aftermath; "standing" things are the opposite of aftermath).
        var fireAt = kit.Snap(DockNav, Fire.X, Fire.Y);
        var orderly = kit.Marker("ARG_MQ01_CampOrderly", new P3Float(fireAt.X, fireAt.Y, fireAt.Z - 300), null, 0xC00);
        var attacked = kit.Marker("ARG_MQ01_CampAttacked", new P3Float(fireAt.X + 20, fireAt.Y, fireAt.Z - 300), null, 0xC00);
        var aftermath = kit.Marker("ARG_MQ01_CampAftermath", new P3Float(fireAt.X + 40, fireAt.Y, fireAt.Z - 300), null, 0xC00);
        var cellParent = kit.Marker("ARG_MQ01_CellParent", new P3Float(fireAt.X + 60, fireAt.Y, fireAt.Z - 300), null, 0xC00);
        var survivors = kit.Marker("ARG_MQ01_SurvivorsParent", new P3Float(fireAt.X + 80, fireAt.Y, fireAt.Z - 300), null, 0xC00);
        var shore93Parent = kit.Marker("ARG_MQ01_Shore93Parent", new P3Float(fireAt.X + 100, fireAt.Y, fireAt.Z - 300), null, 0x400);
        var fireMark = kit.Marker("ARG_MQ01_FireMarker", kit.Snap(DockNav, Fire.X + 100, Fire.Y - 50));
        var shedMark = kit.Marker("ARG_MQ01_ShedMarker", kit.Snap(DockNav, Shed.X, Shed.Y));
        var hutsMark = kit.Marker("ARG_MQ01_HutsMarker", kit.Snap(DockNav, HutsEnd.X, HutsEnd.Y)); // on the island at the huts' end, so Deesh-Duun's follow starts on one mesh
        var shoreMark = kit.Marker("ARG_MQ01_ShoreMarker", kit.Snap(DockNav, Shore.X, Shore.Y));
        var waterMark = kit.Marker("ARG_MQ01_WaterEdgeMarker", kit.Snap(DockNav, WaterEdge.X, WaterEdge.Y));
        var salRef = kit.Actor("ARG_MQ01_SalSeiRef", sal, kit.Snap(DockNav, Fire.X + 60, Fire.Y + 150));
        var deeshRef = kit.Actor("ARG_MQ01_DeeshDuunRef", deesh, kit.Snap(DockNav, Fire.X - 60, Fire.Y - 150));
        var neshNeelRef = kit.Actor("ARG_MQ01_NeshNeelRef", neshNeel, kit.Snap(DockNav, Fire.X + 150, Fire.Y + 100), orderly);
        var leaderRef = kit.Actor("ARG_MQ01_CutsTheOldKnotRef", leader, kit.Snap(DockNav, Fire.X - 150, Fire.Y + 120), cellParent);
        var cutter1Ref = kit.Actor("ARG_MQ01_RootCutter1Ref", cutter, kit.Snap(DockNav, Shed.X + 50, Shed.Y - 200), cellParent);
        var cutter2Ref = kit.Actor("ARG_MQ01_RootCutter2Ref", cutter, kit.Snap(DockNav, Shed.X - 80, Shed.Y - 220), cellParent);
        var tiesRef = kit.Actor("ARG_MQ01_TiesTheLoosePlankRef", ties, kit.Snap(DockNav, Shore.X + 120, Shore.Y + 60));
        tiesRef.MajorRecordFlagsRaw = 0xC00; // off until MQ01's endings (his own ref, outside the survivors parent)
        var survivorRefs = new[] { (risakka, 80f, -60f), (tsanji, -100f, 90f), (llarvi, 200f, 120f) }
            .Select(g => kit.Actor($"ARG_MQ01_{g.Item1.EditorID![9..]}ShoreRef", g.Item1, kit.Snap(DockNav, Shore.X + g.Item2, Shore.Y + g.Item3), survivors)).ToList();
        P3Float OnLand((float X, float Y) p, float dz = 0) => new(p.X, p.Y, MathF.Round(kit.Land(World, p.X, p.Y) + dz));
        var dressing = new List<PlacedObject>
        {
            kit.Marker("ARG_MQ01_Campfire", new P3Float(fireAt.X, fireAt.Y, fireAt.Z), K("035F49:Skyrim.esm"), 0x400, aftermath, opposite: true), // Campfire01Burning
            kit.Marker("ARG_MQ01_Shed", OnLand((Shed.X + 60, Shed.Y + 60)), K("0A013F:Black Marsh.esm"), 0x400),                       // 01shed, the hatching shed (uxith); 01strawhut's HutExterior.nif is in no archive
            kit.Marker("ARG_MQ01_Cutting", OnLand(Cutting), K("1B32E5:Black Marsh.esm"), 0x400),                // 01swamptreecoolmoss, scaled down below
            kit.Marker("ARG_MQ01_Hut1", new P3Float(Huts1.X, Huts1.Y, 0), K("0AA5F0:Black Marsh.esm"), 0x400, aftermath, opposite: true), // 001Hut2
            kit.Marker("ARG_MQ01_Hut2", new P3Float(Huts2.X, Huts2.Y, 0), K("0AA5F2:Black Marsh.esm"), 0x400, aftermath, opposite: true), // 001hut3
            kit.Marker("ARG_MQ01_HutBurnt", new P3Float(Huts1.X, Huts1.Y - 200, 0), K("0D8589:Black Marsh.esm"), 0x400, aftermath),    // a destroyed shack
            kit.Marker("ARG_MQ01_Planks", new P3Float(Planks.X, Planks.Y, 0), K("0008CB:HearthFires.esm"), 0x400),                      // BYOHFishDock01
            kit.Marker("ARG_MQ01_HutFire1", new P3Float(Huts1.X, Huts1.Y, 120), K("035F49:Skyrim.esm"), 0x400, attacked),
            kit.Marker("ARG_MQ01_HutFire2", new P3Float(Huts2.X, Huts2.Y, 120), K("035F49:Skyrim.esm"), 0x400, attacked),
        };
        foreach (var (dx, dy) in new[] { (-40f, 0f), (30f, 30f), (10f, -40f) })
            dressing.Add(kit.Marker($"ARG_MQ01_Egg{dressing.Count}", OnLand((Shed.X + 60 + dx, Shed.Y + 60 + dy), 5), K("17BF06:Black Marsh.esm"), 0x400)); // 01egg, the clutch
        dressing.Single(d => d.EditorID == "ARG_MQ01_Cutting").Scale = 0.15f;
        dressing.Single(d => d.EditorID == "ARG_MQ01_Planks").Placement!.Rotation = new P3Float(0, 0, MathF.PI / 2);
        // Zones: the fire (the march's end, 32 -> 40), the shed (40 -> 41), the huts' water (40 -> 42), the shore's three boxes
        // (41 -> 90, 42 -> 91, 40 -> 93). No two consecutive zones overlap (the kit refuses it).
        var fireZone = kit.Zone("ARG_MQ01_ZoneFire", new P3Float(fireAt.X, fireAt.Y, fireAt.Z + 100), 32, 40, new P3Float(200, 200, 200));
        var shedZone = kit.Zone("ARG_MQ01_ZoneShed", new P3Float(6250, -4300, kit.Land(World, 6250, -4300) + 100), 40, 41, new P3Float(175, 175, 200));
        var hutsZone = kit.Zone("ARG_MQ01_ZoneHuts", new P3Float(4850, -5700, -100), 40, 42, new P3Float(300, 300, 250));
        var shoreAt = new P3Float(shoreMark.Placement!.Position.X, shoreMark.Placement.Position.Y, shoreMark.Placement.Position.Z + 100);
        var shore90 = kit.Zone("ARG_MQ01_ZoneShore90", shoreAt, 41, 90, new P3Float(300, 300, 250));
        var shore91 = kit.Zone("ARG_MQ01_ZoneShore91", shoreAt, 42, 91, new P3Float(300, 300, 250));
        var shore93 = kit.Zone("ARG_MQ01_ZoneShore93", shoreAt, 40, 93, new P3Float(300, 300, 250), shore93Parent);

        // Packages on the aliases (E-package). BM&V's navmeshes carry no edge links (0 of 17,589 in Black Marsh.esm and
        // Black Marsh North.esp; `plugin.sh inspect navstat`), so no one walks from one navmesh to another: the camp stands on
        // the dock's own mesh, and the gang walks from the plank's foot to the fire along it once the player has come out on
        // the pier (stage 32, set when the five walkers are loaded). The leader to the water's edge from 40, the cutters stay at the shed
        // until the ending disables them; the saved one follows the player on 41 or 42.
        var march = kit.Travel("ARG_MQ01_MarchOff", fireMark, 200, StageIs(q, CompareOperator.GreaterThanOrEqualTo, 32), StageIs(q, CompareOperator.LessThan, 40));
        var leave = kit.Travel("ARG_MQ01_LeaderLeaves", waterMark, 128, StageIs(q, CompareOperator.GreaterThanOrEqualTo, 40));
        var salFollow = kit.Follow("ARG_MQ01_SalSeiFollows", StageIs(q, CompareOperator.EqualTo, 41));
        var deeshFollow = kit.Follow("ARG_MQ01_DeeshDuunFollows", StageIs(q, CompareOperator.EqualTo, 42));

        kit.Header("No Name on the Work Roll", 60, Quest.TypeEnum.MainQuest, 0);
        kit.FromRecord("quest.main.mq01", "ARG_QF_MQ01", ends: [90, 91, 93]);
        const QuestAlias.Flag AD = QuestAlias.Flag.AllowDisabled;
        kit.Forced(A1WuleenHold, "WuleenSei", wuleenRef.FormKey, AD | QuestAlias.Flag.Essential);
        kit.Forced(A1UxHold, "UxXeek", uxRef.FormKey, AD);
        kit.Forced(A1Buys, "BuysTheMonths", buysRef.FormKey, AD);
        var courierA = kit.Forced(A1Courier, "Courier", courierRef.FormKey, QuestAlias.Flag.Essential);
        courierA.PackageData.Add(march.ToLink());
        foreach (var (id, name, r, f) in new[] { (A1WuleenMarch, "WuleenSeiMarch", wuleenMRef, AD | QuestAlias.Flag.Essential), (A1UxMarch, "UxXeekMarch", uxMRef, AD),
                     (A1DivesMarch, "DivesMarch", divesMRef, AD), (A1FindsMarch, "FindsMarch", findsMRef, AD) })
        {
            var a = kit.Forced(id, name, r.FormKey, f);
            a.PackageData.Add(march.ToLink());
        }
        kit.Forced(A1Sal, "SalSei", salRef.FormKey, QuestAlias.Flag.Essential).PackageData.Add(salFollow.ToLink());
        kit.Forced(A1Deesh, "DeeshDuun", deeshRef.FormKey, QuestAlias.Flag.Essential).PackageData.Add(deeshFollow.ToLink());
        kit.Forced(A1Leader, "CutsTheOldKnot", leaderRef.FormKey, AD | QuestAlias.Flag.Protected).PackageData.Add(leave.ToLink());
        kit.Forced(A1Cutter1, "RootCutter1", cutter1Ref.FormKey, AD); // stays at the shed until the ending disables it
        kit.Forced(A1Cutter2, "RootCutter2", cutter2Ref.FormKey, AD);
        kit.Forced(A1Ties, "TiesTheLoosePlank", tiesRef.FormKey, AD);
        kit.Forced(A1ZoneFire, "ZoneFire", fireZone.FormKey);
        kit.Forced(A1ZoneShed, "ZoneShed", shedZone.FormKey, AD);
        kit.Forced(A1ZoneHuts, "ZoneHuts", hutsZone.FormKey, AD);
        kit.Forced(A1Shore90, "ZoneShore90", shore90.FormKey);
        kit.Forced(A1Shore91, "ZoneShore91", shore91.FormKey);
        kit.Forced(A1Shore93, "ZoneShore93", shore93.FormKey, AD);
        // TR-activate on the hold's stair door (BlockTest's door shape): opening it once the answer is given sets 30.
        kit.Forced(A1HoldDoor, "HoldDoor", HoldDoor);
        kit.Forced(A1FireMark, "FireMarker", fireMark.FormKey);
        kit.Forced(A1ShoreMark, "ShoreMarker", shoreMark.FormKey);
        q.VirtualMachineAdapter!.Aliases.Add(ActivateSets(kit, A1HoldDoor, 20, 30));
        // Objective targets (the compass marker), from the record's target column: Wuleen-Sei at 10, the stair door at 20, the
        // camp's fire at 30, the two at the strike (Sal-Sei, Deesh-Duun) at 40, the shore end at 41 and 42.
        kit.TargetsFromRecord("quest.main.mq01", new()
        {
            ["npc.pirate-freeholds.opening-work-barge.npc-opening-overseer"] = [A1WuleenHold], ["ref.mq01.hold-door"] = [A1HoldDoor], ["ref.mq01.fire"] = [A1FireMark],
            ["npc.pirate-freeholds.opening-work-camp.npc-opening-clutch-keeper"] = [A1Sal], ["npc.pirate-freeholds.opening-work-camp.npc-opening-witness"] = [A1Deesh],
            ["mark.mq01.shore"] = [A1ShoreMark],
        });
        q.VirtualMachineAdapter!.Scripts.Add(Script("ARG_QF_MQ01",
            Obj("StartMarker", StartMarker.FormKey), Obj("Tunic", K("03C9FE:Skyrim.esm")), Obj("Footwraps", K("03CA00:Skyrim.esm")),
            Obj("RollRead", rollRead.FormKey), Obj("Answered", answered.FormKey), Obj("SavedSal", savedSal.FormKey), Obj("SavedDeesh", savedDeesh.FormKey),
            Obj("CampOrderly", orderly.FormKey), Obj("CampAttacked", attacked.FormKey), Obj("CampAftermath", aftermath.FormKey),
            Obj("MarchParent", marchParent.FormKey), Obj("HoldParent", holdParent.FormKey), Obj("CrewParent", crewParent.FormKey),
            Obj("BrokerParent", brokerParent.FormKey), Obj("CellParent", cellParent.FormKey), Obj("SurvivorsParent", survivors.FormKey),
            Obj("Shore93Parent", shore93Parent.FormKey), Obj("ShedZone", shedZone.FormKey), Obj("HutsZone", hutsZone.FormKey),
            Obj("ShedMark", shedMark.FormKey), Obj("HutsMark", hutsMark.FormKey), Obj("ShoreMark", shoreMark.FormKey),
            Obj("FireMark", fireMark.FormKey), Obj("HoldDoor", HoldDoor),
            Alias("Courier", q, A1Courier), Alias("Leader", q, A1Leader), Alias("SalSei", q, A1Sal), Alias("DeeshDuun", q, A1Deesh),
            Alias("WuleenMarch", q, A1WuleenMarch), Alias("UxMarch", q, A1UxMarch), Alias("Ties", q, A1Ties),
            Alias("Cutter1", q, A1Cutter1), Alias("Cutter2", q, A1Cutter2), Alias("DivesMarch", q, A1DivesMarch), Alias("FindsMarch", q, A1FindsMarch),
            Obj("ReedKnife", knife.FormKey), Obj("NextQuest", Mq03.FormKey)));

        // Lines (TR-topic). The roll at 10 is a question: its INFO links to the three answers (choices in its branch, as
        // Skyrim's question-and-answer pairs), so they follow it at once and come back with it if the player walks off.
        // Each answer sets Answered (the broker's line) and stage 20; the broker, the port hand and Dives-Without-A-Rope
        // from 10 until the strike.
        var lines = LinesOf("mq01");
        const string Q = "(GetOwningQuest() as ARG_QF_MQ01)";
        ConditionFloat[] Who(params Npc[] ns) => ns.Select((n, i) => i < ns.Length - 1 ? Or(IsId(n)) : IsId(n)).ToArray();
        var at10 = StageIs(q, CompareOperator.EqualTo, 10);
        ConditionFloat[] Before40() => [StageIs(q, CompareOperator.GreaterThanOrEqualTo, 10), StageIs(q, CompareOperator.LessThan, 40)];
        var roll = kit.Record("MQ01", lines, "topic.mq01-the-roll", null, Who(wuleen), ("main", $"{Q}.ReadRoll()", [at10.DeepCopy()]));
        var rollBranch = mod.DialogBranches.Single(b => b.FormKey == roll.Branch.FormKey);
        foreach (var t in new[] { "topic.mq01-answer-name", "topic.mq01-answer-silent", "topic.mq01-answer-defy" })
        {
            var answer = kit.Record("MQ01", lines, t, rollBranch, Who(wuleen), ("main", $"{Q}.Answer()", [at10.DeepCopy()]));
            foreach (var r in roll.Responses) r.LinkTo.Add(answer.ToLink<IDialogTopicGetter>());
        }
        kit.Record("MQ01", lines, "topic.mq01-the-hire", null, Who(buys), ("after-answer", null, [.. Before40(), Glob(answered, 1)]), ("before-answer", null, [at10.DeepCopy()]));
        kit.Record("MQ01", lines, "topic.mq01-the-march", null, Who(dives, divesM), ("main", null, Before40()));
        // The strike's shout (stage 40): Dives-Without-A-Rope, at the fire with the gang, says where Sal-Sei ran and where Deesh-Duun
        // is; Fragment_40 has her Say it (a line heard without talking, a Misc quest topic).
        var strike = kit.Shout("MQ01", lines, "topic.mq01-strike", IsId(divesM));
        q.VirtualMachineAdapter!.Scripts.Single(x => x.Name == "ARG_QF_MQ01").Properties.Add(Obj("StrikeShout", strike.FormKey));

        // World edits: exterior persistent refs in the worldspace's persistent cell.
        world.TopCell!.Persistent.AddRange([brokerParent, marchParent, buysRef, courierRef, wuleenMRef, uxMRef, divesMRef, findsMRef,
            orderly, attacked, aftermath, cellParent, survivors, shore93Parent, fireMark, shedMark, hutsMark, shoreMark, waterMark,
            salRef, deeshRef, neshNeelRef, leaderRef, cutter1Ref, cutter2Ref, tiesRef, .. survivorRefs, .. dressing,
            fireZone, shedZone, hutsZone, shore90, shore91, shore93]);
        // we.mq01.no-valenwood, we.mq01.no-welcome: Valenwood.esp's start-game quests and BM&V's greeting quest off at
        // the start; MQ03's ending starts them (Valenwood's two deferred there too: no first-entry trigger is a block).
        foreach (var k in Valenwood.Append(Welcome.ToString()))
        {
            var key = K(k);
            if (!Survey.Winners<IQuestGetter>(mods).TryGetValue(key, out var w)) { Console.WriteLine($"MQ01: no quest {k} in the load order"); continue; }
            var copy = mod.Quests.FirstOrDefault(z => z.FormKey == key) ?? (Quest)w.rec.DeepCopy();
            copy.Flags &= ~Quest.Flag.StartGameEnabled;
            if (!mod.Quests.Any(z => z.FormKey == key)) mod.Quests.Add(copy);
        }
        kit.Finish();
        return new Mq01Parts(tiesRef, survivors, brokerParent, aftermath);
    }

    static void BuildMq03(SkyrimMod mod, List<ISkyrimModGetter> mods, Mq01Parts m1)
    {
        var q = Mq03;
        var kit = new QuestKit(mod, mods, q) { TifNote = "Generated by tools/ArgoniaPlugin/MainQuest.cs: one main-quest line's end fragment (TR-topic)." };
        kit.OnLine = l => Lines.Add(new Line("MQ03", l.Key, l.Variant!, l.Id, l.Prompt, l.Text, l.Script, l.Body));
        var world = kit.World(World);
        const NpcConfiguration.Flag P = NpcConfiguration.Flag.Protected, U = NpcConfiguration.Flag.Unique;
        var nesh = kit.Base("ARG_MQ03_NeshDeeka", "Nesh-Deeka", "160E6A:Black Marsh.esm", 15, U, Ai.Own);
        var salts = kit.Base("ARG_MQ03_SaltsTheCatch", "Salts-The-Catch", "02A1EE:Black Marsh.esm", 6, P | U, Ai.Own);
        var officer = kit.Base("ARG_MQ03_NeverWritesTwice", "Never-Writes-Twice", "160E6A:Black Marsh.esm", 12, U, Ai.Own);
        var stranger = kit.Base("ARG_MQ03_ReedStranger", "Stranger", "1DE49D:Black Marsh.esm", 12, U, Ai.Own);
        Speakers["npc.nesh-deeka"] = ["ARG_MQ03_NeshDeeka"];
        Speakers["npc.dunmer-north.stormhold.reed-officer"] = ["ARG_MQ03_NeverWritesTwice"];
        var reed = kit.Faction("ARG_VeiledReed", "Veiled Reed", true, "Sworn Hand");

        // Items (we.mq03.jar-marks): the phial on vanilla's potion bottle, the courier's tag on a key's model, the sunk fish-trap
        // (our copy of vanilla's lockbox, Novice), the spilled sap (our copy of vanilla's inert oil pool activator), the key.
        var phial = mod.MiscItems.AddNew("ARG_MQ03_SapPhial");
        phial.Name = "Phial of Spilled Sap"; phial.Value = 0; phial.Weight = 0.2f;
        phial.Model = new Model { File = mods[0].Ingestibles.First(i => i.FormKey == K("03EADD:Skyrim.esm")).Model!.File.DataRelativePath.Path };
        var tag = mod.MiscItems.AddNew("ARG_MQ03_CourierTag");
        tag.Name = "Courier's Brass Tag"; tag.Value = 0; tag.Weight = 0.1f;
        tag.Model = new Model { File = mods[0].Keys.First(k => k.Model != null).Model!.File.DataRelativePath.Path };
        var trap = Survey.Winners<IContainerGetter>(mods)[K("09424C:Skyrim.esm")].rec.Duplicate(mod.GetNextFormKey());
        trap.EditorID = "ARG_MQ03_FishTrap"; trap.Name = "Sunk Fish-Trap"; trap.VirtualMachineAdapter = null;
        trap.Items = [new ContainerEntry { Item = new ContainerItem { Item = new FormLink<IItemGetter>(tag.FormKey), Count = 1 } }];
        trap.Flags &= ~Container.Flag.Respawns;
        mod.Containers.Add(trap);
        var sap = Survey.Winners<IActivatorGetter>(mods)[K("0F02E1:Skyrim.esm")].rec.Duplicate(mod.GetNextFormKey());
        sap.EditorID = "ARG_MQ03_SpilledSap"; sap.Name = "Spilled Sap"; sap.VirtualMachineAdapter = null; sap.ActivateTextOverride = "Taste";
        mod.Activators.Add(sap);
        var key = mod.Keys.AddNew("ARG_MQ03_HouseKey");
        key.Name = "Key to the House in Lilmoth"; key.Value = 0; key.Weight = 0;
        key.Model = new Model { File = mods[0].Keys.First(k => k.Model != null).Model!.File.DataRelativePath.Path };
        var attackTold = kit.Global("ARG_MQ03_AttackTold");
        var nightTold = kit.Global("ARG_MQ03_NightTold");
        var sworn = kit.Global("ARG_MQ03_ReedSworn");       // flag.mq03.reed-sworn
        var declined = kit.Global("ARG_MQ03_ReedDeclined"); // flag.mq03.reed-declined
        var hist = mod.Globals.FirstOrDefault(g => g.EditorID == "ARG_HistHearing") as Global ?? kit.Global("ARG_HistHearing"); // grantHistStep (E-global)

        // The camp at dawn, at MQ01's camp: the jar-marks parent (sap at the shed, the sunk fish-trap under the plank boards, the
        // picks by the fire) and the Reed's strangers at the shore end, all on the dock's navmesh.
        var jarParent = kit.Marker("ARG_MQ03_JarParent", new P3Float(Shed.X, Shed.Y, kit.Land(World, Shed.X, Shed.Y) - 300), null, 0xC00);
        var reedParent = kit.Marker("ARG_MQ03_ReedParent", new P3Float(Shore.X, Shore.Y, kit.Land(World, Shore.X, Shore.Y) - 300), null, 0xC00);
        var sapRef = kit.Marker("ARG_MQ03_SpilledSapRef", new P3Float(Shed.X + 20, Shed.Y - 60, MathF.Round(kit.Land(World, Shed.X + 20, Shed.Y - 60) + 2)), sap.FormKey, 0x400, jarParent);
        var trapRef = kit.Marker("ARG_MQ03_FishTrapRef", new P3Float(Trap.X, Trap.Y, MathF.Round(kit.Land(World, Trap.X, Trap.Y) + 10)), trap.FormKey, 0x400, jarParent);
        trapRef.Lock = new LockData { Level = LockLevel.Novice };
        var fireAt = kit.Snap(DockNav, Fire.X + 120, Fire.Y + 60);
        var picks = Enumerable.Range(0, 5).Select(i => kit.Marker($"ARG_MQ03_Lockpick{i + 1}", new P3Float(fireAt.X + 15 * i, fireAt.Y, MathF.Round(kit.Land(World, fireAt.X + 15 * i, fireAt.Y) + 30)), Lockpick, 0x400, jarParent)).ToList();
        var officerRef = kit.Actor("ARG_MQ03_NeverWritesTwiceRef", officer, kit.Snap(DockNav, Shore.X + 100, Shore.Y - 50), reedParent);
        var strangerRef = kit.Actor("ARG_MQ03_ReedStrangerRef", stranger, kit.Snap(DockNav, Shore.X + 160, Shore.Y - 10), reedParent);

        // The house (we.mq03.house, .rooms): Nesh-Deeka and the mats in the back room, Salts-The-Catch at the outer door; on
        // the tilted floor (no navmesh where the rooms are: the actors are placed 10 units over the floor and settle).
        P3Float H(float hx, float hy) => new(hx, hy, HouseFloor(hy) + 10);
        var neshRef = kit.Actor("ARG_NeshDeekaRef", nesh, H(1620, 1250));
        var saltsRef = kit.Actor("ARG_MQ03_SaltsTheCatchRef", salts, H(1850, 800));
        var houseMark = kit.Marker("ARG_MQ03_HouseMarker", H(1750, 950));
        var matMark = kit.Marker("ARG_MQ03_MatMarker", H(1550, 1150));
        var mats = new[] { kit.Marker("ARG_MQ03_Mat1", new P3Float(1540, 1180, HouseFloor(1180)), K("0B8371:Skyrim.esm"), 0x400),
                           kit.Marker("ARG_MQ03_Mat2", new P3Float(1540, 1060, HouseFloor(1060)), K("0B8371:Skyrim.esm"), 0x400) };
        var house = kit.Interior(HouseCell);
        house.Persistent.AddRange([neshRef, saltsRef, houseMark, matMark, .. mats]);

        // The dream (we.mq03.dream) in the empty hold: a ring of BM&V's thorn roots on the walk from the mark to the door,
        // under the dream parent; the door-gap's zone at the hold door (40 -> 45; 45 splits 90/91 on the oath global).
        var dreamParent = kit.Marker("ARG_MQ03_DreamParent", new P3Float(2850, 3300, 6700), null, 0xC00);
        var dreamMark = kit.Marker("ARG_MQ03_DreamMarker", kit.Snap(HoldNav, 2850, 3300, 7010));
        var roots = new[] { (2650f, 3700f), (3100f, 3700f), (2600f, 4300f), (3150f, 4300f), (2700f, 4850f), (3100f, 4850f) }
            .Select((p, i) => kit.Marker($"ARG_MQ03_DreamRoot{i + 1}", new P3Float(p.Item1, p.Item2, 7010), K("1B331F:Black Marsh.esm"), 0x400, dreamParent)).ToList();
        var doorPos = HoldInside; // in front of the hold's stair door, its way out (MQ01)
        var doorZone = kit.Zone("ARG_MQ03_ZoneDoor", doorPos, 40, 45, new P3Float(150, 150, 150));
        kit.Interior(HoldCell).Persistent.AddRange([dreamParent, dreamMark, .. roots, doorZone]);

        // we.mq03.door: the outer door locked to the house key (setDoorAccess: the key handed at e-sworn).
        var door = (PlacedObject)((IPlacedObjectGetter)kit.Placed[HouseDoorOut].rec).DeepCopy();
        door.MajorRecordFlagsRaw |= 0x400;
        door.Lock = new LockData { Level = LockLevel.RequiresKey };
        door.Lock.Key.SetTo(key.FormKey);

        kit.Header("A Dead Prisoner's Use", 60, Quest.TypeEnum.MainQuest, 0);
        kit.FromRecord("quest.main.mq03", "ARG_QF_MQ03", ends: [90, 91]);
        const QuestAlias.Flag AD = QuestAlias.Flag.AllowDisabled;
        kit.Forced(A3Officer, "NeverWritesTwice", officerRef.FormKey, AD | QuestAlias.Flag.Essential);
        kit.Forced(A3Stranger, "Stranger", strangerRef.FormKey, AD | QuestAlias.Flag.Essential);
        kit.Forced(A3Sap, "SpilledSap", sapRef.FormKey, AD);
        kit.Forced(A3Nesh, "NeshDeeka", neshRef.FormKey);
        kit.Forced(A3Salts, "SaltsTheCatch", saltsRef.FormKey);
        kit.Forced(A3Ties, "TiesTheLoosePlank", m1.Ties.FormKey, AD);
        kit.Forced(A3DoorZone, "ZoneDoor", doorZone.FormKey);
        kit.Forced(A3Trap, "FishTrap", trapRef.FormKey, AD);
        kit.Forced(A3HoldDoor, "HoldDoor", HoldDoor);
        var vm = q.VirtualMachineAdapter!;
        // TR-activate: the taste (the alias set-stage script on activate, prereq 10) sets the hidden stage 11; TR-death:
        // Nesh-Deeka's moves 20 to 40 (the record's fail-forward); the officer is Essential and cannot die.
        vm.Aliases.Add(ActivateSets(kit, A3Sap, 10, 11));
        vm.Aliases.Add(DeathSets(kit, A3Nesh, 20, 40));
        vm.Scripts.Add(Script("ARG_QF_MQ03",
            Obj("JarParent", jarParent.FormKey), Obj("ReedParent", reedParent.FormKey), Obj("SurvivorsParent", m1.Survivors.FormKey),
            Obj("DreamParent", dreamParent.FormKey), Obj("BrokerParent", m1.Broker.FormKey), Obj("HouseMark", houseMark.FormKey),
            Obj("MatMark", matMark.FormKey), Obj("DreamMark", dreamMark.FormKey), Obj("HoldDoor", HoldDoor), Obj("HouseKey", key.FormKey),
            Obj("Phial", phial.FormKey), Obj("Gold001", Gold), Obj("VeiledReed", reed.FormKey), Obj("ReedSworn", sworn.FormKey),
            Obj("ReedDeclined", declined.FormKey), Obj("AttackTold", attackTold.FormKey), Obj("NightTold", nightTold.FormKey),
            Obj("HistHearing", hist.FormKey), Obj("HouseDoor", HouseDoorOut), Alias("Ties", q, A3Ties),
            new ScriptObjectListProperty { Name = "Deferred", Objects = Valenwood.Append(Welcome.ToString()).Where(k => mod.Quests.Any(z => z.FormKey == K(k)))
                .Select(k => new ScriptObjectProperty { Object = new FormLink<ISkyrimMajorRecordGetter>(K(k)) }).ToExtendedList() }));

        // Lines.
        var lines = LinesOf("mq03");
        const string Q = "(GetOwningQuest() as ARG_QF_MQ03)";
        var before20 = StageIs(q, CompareOperator.LessThan, 20);
        var at20 = StageIs(q, CompareOperator.EqualTo, 20);
        // "where" is two INFOs, each exclusive of "ready" (a speaker's INFOs are tried in order, so all must not pass at once):
        // the player has not tasted the sap, or holds neither the phial nor the tag.
        var from10 = StageIs(q, CompareOperator.GreaterThanOrEqualTo, 10);
        kit.Record("MQ03", lines, "topic.mq03-the-boat", null, [IsId(officer)],
            ("ready", "GetOwningQuest().SetStage(20)", [before20.DeepCopy(), Done(q, 11), Or(Has(phial.FormKey, 1)), Has(tag.FormKey, 1)]),
            ("where", null, [before20.DeepCopy(), from10.DeepCopy(), Not(Done(q, 11))]),
            ("where", null, [before20.DeepCopy(), from10.DeepCopy(), Not(Has(phial.FormKey, 1)), Not(Has(tag.FormKey, 1))]));
        kit.Record("MQ03", lines, "topic.mq03-the-attack", null, [IsId(nesh)],
            ("phial-carried", $"{Q}.TellAttack(akSpeakerRef, True)", [at20.DeepCopy(), Has(phial.FormKey, 1)]),
            ("phial-none", $"{Q}.TellAttack(akSpeakerRef, False)", [at20.DeepCopy()]));
        kit.Record("MQ03", lines, "topic.mq03-the-night", null, [IsId(mod.Npcs.Single(n => n.EditorID == "ARG_MQ01_TiesTheLoosePlank"))],
            ("tag", $"{Q}.TellNight()", [at20.DeepCopy(), Has(tag.FormKey, 1)]),
            ("words", $"{Q}.TellNight()", [at20.DeepCopy(), Speech(25)]),
            ("low", null, [at20.DeepCopy(), Speech(CompareOperator.LessThan, 25)]));
        kit.Record("MQ03", lines, "topic.mq03-the-offer", null, [IsId(nesh)], ("main", null, [at20.DeepCopy()]));
        kit.Record("MQ03", lines, "topic.mq03-take-oath", null, [IsId(nesh)], ("main", $"{Q}.TakeOath()", [at20.DeepCopy(), Glob(attackTold, 1)]));
        kit.Record("MQ03", lines, "topic.mq03-refuse-oath", null, [IsId(nesh)], ("main", "GetOwningQuest().SetStage(40)", [at20.DeepCopy(), Glob(attackTold, 1)]));

        world.TopCell!.Persistent.AddRange([jarParent, reedParent, sapRef, trapRef, .. picks, officerRef, strangerRef, door]);
        // Nesh-Deeka's greeting after the oath (90) or the refusal (91).
        kit.AfterHellos("ARG_MQ03_AfterHello", "mq03", (neshRef.FormKey, "nesh-deeka", []));
        // Objective targets, from the record's target column: the sap (10 and the phial), the fish-trap's tag, the officer,
        // Nesh-Deeka, Ties, the hold's door.
        kit.TargetsFromRecord("quest.main.mq03", new()
        {
            ["thing.mq03.jar-marks"] = [A3Sap], ["thing.mq03.courier-token"] = [A3Trap], ["npc.dunmer-north.stormhold.reed-officer"] = [A3Officer],
            ["npc.nesh-deeka"] = [A3Nesh], ["npc.pirate-freeholds.opening-work-camp.n1"] = [A3Ties], ["thing.mq03.dream"] = [A3HoldDoor],
        });
        kit.Finish();
    }

    // After every quest is allocated (Generate's end): MQ03's endings start ARG_MQ04 at 10 when it is in the plugin.
    public static void Finish(SkyrimMod mod)
    {
        var mq04 = mod.Quests.FirstOrDefault(q => q.EditorID == "ARG_MQ04");
        var props = Mq03.VirtualMachineAdapter!.Scripts.Single(s => s.Name == "ARG_QF_MQ03").Properties;
        props.RemoveAll(p => p.Name == "NextQuest");
        if (mq04 != null) props.Add(Obj("NextQuest", mq04.FormKey));
        else Console.WriteLine("MQ03: ARG_MQ04 not in the plugin; its endings start nothing until it is");
    }

    // The TIF fragment scripts the lines above use (Papyrus source, generated into papyrus/generated by the seed): the kit's.
    public static void WritePsc(string dir) => QuestKit.WritePsc(dir);
}
