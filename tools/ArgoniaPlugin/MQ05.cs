using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Noggog;
using static QuestKit;

// MQ05 The Word Carried Inland (quest.main.mq05): from Nesh-Deeka at Lilmoth, the coast ship (01Ship, 0AA665) to
// Helstrom's river landing (BlackMarsh2 -10,12), the marsh way to the gate (08D5E9) and the grove behind the Hall of
// the Scalded Throne (0D78C1, hall 2076BB). Started by ARG_MQ04's stage 91 (SetStage(10)). Every stage, trigger and
// effect a copy of a proven block shape (QuestKit.cs); the one new block is the ship's inner door pair (W-ref load
// doors with XTEL both ways, we.mq05.ship-door): no existing door joins the ship's two sections (bmv_door: Lilmoth's
// 0AA837 and 0AA6C9 open on navmesh 0AA666's section, the landing's 23D496 and 23D688 on the other, nothing between).
static class MQ05
{
    public const string Id = "quest.main.mq05";
    const string Nesh = "npc.nesh-deeka", Kaska = "npc.hist-heartland.helstrom.grove-s-senior-tree",
        EiTuja = "npc.hist-heartland.helstrom.nisswo-interpreter-debating-house", Warden = "npc.hist-heartland.helstrom.levy-warden-01";
    public static readonly FormKey World2 = K("0D6960:Black Marsh.esm"), Ship = K("0AA665:Black Marsh.esm"), ShipNav = K("0AA666:Black Marsh.esm"),
        Hall = K("2076BB:Black Marsh.esm"), WardenRef = K("08D5E9:Black Marsh North.esp"), Grove = K("1FAE2D:Black Marsh.esm"), WayNav = K("1FAE21:Black Marsh.esm"),
        ArgDoor = K("1DE5DF:Black Marsh.esm");
    public const string NeshRefId = "ARG_NeshDeekaRef"; // agreed with the MQ01/MQ03 lane: her placed ref's editor id
    public const uint AKaska = 0, AEiTuja = 1, AZone = 2, ANesh = 3;
    public static readonly int[] FragmentStages = [10, 20, 40, 91, 92];

    public static void Add(SkyrimMod mod, List<ISkyrimModGetter> mods, Quest q)
    {
        var k = new QuestKit(mod, mods, q, "ARG_MQ05_");
        Kit = k; Q = q;
        var world = k.World(World2);

        // W-npc: Kaska-Meen and Ei-Tuja (band 0), templated on BM&V's villagers.
        var kaska = k.Base("ARG_MQ05_KaskaMeen", "Kaska-Meen", "02A1EE:Black Marsh.esm", 3);
        var ei = k.Base("ARG_MQ05_EiTuja", "Ei-Tuja", "00FF4D:Black Marsh.esm", 3);
        // W-fixed: two of BM&V's Giant Wasps (166381) at band 1, under the way's enable parent.
        var wasp = k.Base("ARG_MQ05_Wasp", "Giant Wasp", "166381:Black Marsh.esm", 5);

        // The grove behind the hall, on the platform's navmesh 1FAE2D (0D78C1).
        var kaskaAt = k.Snap(Grove, -29700, 79100);
        var eiAt = k.Snap(Grove, -29300, 78400);
        var histAt = k.Snap(Grove, -30000, 79350);
        var kaskaPost = k.Marker("KaskaPost", kaskaAt);
        var eiPost = k.Marker("EiTujaPost", eiAt);
        var hist = k.Ref("YoungHist", K("11FE7A:Black Marsh.esm"), histAt, scale: 0.4f);
        var zone = k.Zone("ZoneGrove", new P3Float(-29500, 78800, kaskaAt.Z + 100), 20, 40, new P3Float(600, 600, 250));
        var kaskaRef = k.Actor("KaskaMeenRef", kaska, kaskaAt);
        var eiRef = k.Actor("EiTujaRef", ei, eiAt);

        // The way's far bend (navmesh 1FAE21, -7,18, short of the gate): the wasps under ref.mq05.way.
        var w1 = k.Snap(WayNav, -27800, 74200); var w2 = k.Snap(WayNav, -27400, 74000);
        var way = k.Marker("WayParent", new P3Float(w1.X, w1.Y, w1.Z - 200), 0xC00);
        var wasp1 = k.Actor("Wasp1", wasp, w1, way);
        var wasp2 = k.Actor("Wasp2", wasp, w2, way);

        // The levy warden: BM&V North's gate soldier, made persistent by LQ30 (LocalQuests.cs, kit.Persist): not copied here.

        // The ship's inner door pair (the new block, owed an owner check): door A at navmesh 0AA666's east end, door B
        // beside the landing door 23D496, each teleporting to a spot in front of the other.
        var aAt = k.Snap(ShipNav, 3295, 5343);
        var bAt = new P3Float(5990, 5825, 8054);
        var doorA = k.Ref("ShipDoorA", ArgDoor, aAt);
        var doorB = k.Ref("ShipDoorB", ArgDoor, bAt);
        doorA.TeleportDestination = new TeleportDestination { Position = new P3Float(bAt.X - 120, bAt.Y, bAt.Z), Rotation = new P3Float() };
        doorA.TeleportDestination.Door.SetTo(doorB.FormKey);
        doorB.TeleportDestination = new TeleportDestination { Position = new P3Float(aAt.X - 120, aAt.Y, aAt.Z), Rotation = new P3Float() };
        doorB.TeleportDestination.Door.SetTo(doorA.FormKey);
        k.Interior(Ship).Persistent.AddRange([doorA, doorB]);

        // The hall: named (W-name), a seat at its far end from its door (2076D0), a broom by it (W-ref).
        var hall = k.Interior(Hall);
        hall.Name = "Hall of the Scalded Throne";
        var hallMesh = k.Meshes(Hall).Select(k.Mesh).First(m => m.Data != null);
        var dv = hallMesh.Data!.Vertices;
        var far = hallMesh.Data.Triangles.Select(t => new P3Float((dv[t.Vertices.X].X + dv[t.Vertices.Y].X + dv[t.Vertices.Z].X) / 3,
            (dv[t.Vertices.X].Y + dv[t.Vertices.Y].Y + dv[t.Vertices.Z].Y) / 3, (dv[t.Vertices.X].Z + dv[t.Vertices.Y].Z + dv[t.Vertices.Z].Z) / 3))
            .MaxBy(p => (p.X - 9) * (p.X - 9) + (p.Y - 1709.7f) * (p.Y - 1709.7f));
        var seat = k.Ref("Seat", K("1E44EC:Black Marsh.esm"), new P3Float(MathF.Round(far.X), MathF.Round(far.Y), MathF.Round(far.Z)));
        var broom = k.Ref("Broom", K("06717F:Skyrim.esm"), new P3Float(MathF.Round(far.X) + 80, MathF.Round(far.Y), MathF.Round(far.Z) + 30));
        hall.Persistent.AddRange([seat, broom]);

        // E-global (the endings' flags), E-package (each at their post).
        var minders = k.Global("MindersHold");
        var nisswo = k.Global("NisswoRead");
        var kaskaPkg = k.Travel("KaskaGoPost", kaskaPost, 64, true);
        var eiPkg = k.Travel("EiTujaGoPost", eiPost, 64, true);

        // TR-topic. Nesh-Deeka is the MQ01/MQ03 lane's person: her lines gate on her placed ref (GetIsReference).
        k.Topic("Basin", Label("topic.mq05-the-basin"),
            k.Banded("topic.mq05-the-basin", Warden, "default", null, IsRef(WardenRef), k.StageIs(20, CompareOperator.GreaterThanOrEqualTo)));
        k.Topic("Quarrel", Label("topic.mq05-the-quarrel"),
            k.Banded("topic.mq05-the-quarrel", EiTuja, "default", null, IsId(ei.FormKey), k.StageIs(40, CompareOperator.GreaterThanOrEqualTo)));
        k.Topic("Watch", Label("topic.mq05-the-watch"),
            k.Banded("topic.mq05-the-watch", Kaska, "default", null, IsId(kaska.FormKey), k.StageIs(40, CompareOperator.GreaterThanOrEqualTo)));
        k.Topic("TellMinder", Label("topic.mq05-tell-minder"),
            k.Banded("topic.mq05-tell-minder", Kaska, "default", "TIF_ARG_MQ05_91", IsId(kaska.FormKey), k.StageIs(40)));
        k.Topic("TellNisswo", Label("topic.mq05-tell-nisswo"),
            k.Banded("topic.mq05-tell-nisswo", EiTuja, "default", "TIF_ARG_MQ05_92", IsId(ei.FormKey), k.StageIs(40)));

        k.Header("The Word Carried Inland", 60, Quest.TypeEnum.MainQuest, Quest.Flag.RunOnce);
        k.FromRecord(Id, "ARG_QF_MQ05", fragments: FragmentStages);
        k.Forced(AKaska, "KaskaMeen", kaskaRef).PackageData.Add(kaskaPkg.ToLink());
        k.Forced(AEiTuja, "EiTuja", eiRef).PackageData.Add(eiPkg.ToLink());
        k.Forced(AZone, "ZoneGrove", zone);
        q.VirtualMachineAdapter!.Scripts.Add(Script("ARG_QF_MQ05", k.Alias("KaskaMeen", AKaska), k.Alias("EiTuja", AEiTuja),
            Obj("WayParent", way.FormKey), Obj("MindersHold", minders.FormKey), Obj("NisswoRead", nisswo.FormKey)));
        q.VirtualMachineAdapter.Aliases.Add(DeathSets(k, AKaska, 40, 92)); // fail-forward: Kaska-Meen dead

        world.TopCell!.Persistent.AddRange([kaskaPost, eiPost, hist, zone, way, kaskaRef, eiRef, wasp1, wasp2]);
    }

    static QuestKit? Kit; static Quest? Q;
    // Nesh-Deeka's part of MQ05: called from Generate.cs after MainQuest.Add, which places ARG_NeshDeekaRef.
    public static void AddNesh(SkyrimMod mod)
    {
        var k = Kit!; var q = Q!;
        var neshRef = mod.EnumerateMajorRecords<IPlacedNpcGetter>().FirstOrDefault(r => r.EditorID == NeshRefId);
        if (neshRef != null)
            k.Topic("Word", Label("topic.mq05-the-word"),
                k.Banded("topic.mq05-the-word", Nesh, "speech", "TIF_ARG_MQ05_20", IsRef(neshRef.FormKey), k.StageIs(10), Speech(25)),
                k.Banded("topic.mq05-the-word", Nesh, "item", "TIF_ARG_MQ05_20Gold", [Obj("Gold001", Gold)], IsRef(neshRef.FormKey), k.StageIs(10), Has(Gold, 40)),
                k.Banded("topic.mq05-the-word", Nesh, "default", null, IsRef(neshRef.FormKey), k.StageIs(10)));
        else Console.WriteLine($"MQ05: WARN no {NeshRefId} in the plugin (the MQ01/MQ03 lane's); stage 10's topic and fail-forward left out");
        if (neshRef != null) k.Forced(ANesh, "NeshDeeka", neshRef, QuestAlias.Flag.Optional);
        if (neshRef != null) q.VirtualMachineAdapter!.Aliases.Add(DeathSets(k, ANesh, 10, 20)); // fail-forward: Nesh-Deeka dead
    }
}
