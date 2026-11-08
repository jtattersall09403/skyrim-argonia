using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using Noggog;
using static QuestKit;

// MQ04 The Tree That Turned Its Face (quest.main.mq04): Low-Reed Village, BM&V's Village (03978F, BlackMarsh 22,-4)
// and the cell's camp two cells north (039793). Every stage, trigger and effect a copy of a proven block shape
// (docs/design/blocks.md; QuestKit.cs). Started by ARG_MQ03's ending stages (90, 91: ARG_MQ04.SetStage(10)); its
// ending stage 91 starts ARG_MQ05 the same way. Stages, journal and objectives come from the record's rows.
static class MQ04
{
    public const string Id = "quest.main.mq04";
    const string Herald = "npc.mercantile-coast.low-reed-village.root-herald", Minder = "npc.mercantile-coast.low-reed-village.chime-tuner",
        Egg = "npc.mercantile-coast.low-reed-village.egg-tender";
    public static readonly FormKey World = K("23D689:Black Marsh.esm"), VillageCell = K("03978F:Black Marsh.esm");
    // Navmeshes: the village's raised ground (06EF98), its water edge (06EFDD), the north village (06EED1, 039791) and
    // the camp's dry rise (07449F, 039793), read from Black Marsh.esm's cells.
    public static readonly FormKey Raised = K("06EF98:Black Marsh.esm"), Edge = K("06EFDD:Black Marsh.esm"), North = K("06EED1:Black Marsh.esm"), Rise = K("07449F:Black Marsh.esm");
    // Alias ids.
    public const uint AHerald = 0, AMinder = 1, AEgg = 2, AJars = 3, AZone30 = 4, AZone91 = 5, ACell1 = 6, ACell2 = 7;
    public static readonly int[] FragmentStages = [10, 20, 30, 40, 45, 91];

    public static void Add(SkyrimMod mod, List<ISkyrimModGetter> mods, Quest q, Quest next)
    {
        var k = new QuestKit(mod, mods, q, "ARG_MQ04_");
        var world = k.World(World);
        float Land(float x, float y) => Surface.Land(mods, World, x, y) ?? throw new InvalidOperationException($"MQ04: no land at {x},{y}");

        // W-npc: the three village people and the two cell men (band 2, fixed level), templated on BM&V's villagers.
        var herald = k.Base("ARG_MQ04_RootHerald", "Hires-By-The-Season", "02A1EE:Black Marsh.esm", 6);
        // Pays-Late is essential (review F8) and carries his own inventory (the template's Inventory flag dropped): the gum
        // pot, pickpocketed from him (vanilla pickpocket, Sneak against him; caught, it is theft).
        var minder = k.Base("ARG_MQ04_PaysLate", "Pays-Late", "00FF4D:Black Marsh.esm", 6, NpcConfiguration.Flag.Essential);
        minder.Configuration.TemplateFlags &= ~NpcConfiguration.TemplateFlag.Inventory;
        var egg = k.Base("ARG_MQ04_TurnsTheClutch", "Turns-The-Clutch", "02A1EE:Black Marsh.esm", 6, NpcConfiguration.Flag.Protected);
        var cell1 = k.Base("ARG_MQ04_HidesHisWake", "Hides-His-Wake", "084A7A:Black Marsh.esm", 8);
        var cell2 = k.Base("ARG_MQ04_CountsTheJars", "Counts-The-Jars", "084A7A:Black Marsh.esm", 8);
        // W-fixed: BM&V's Leech and Giant Leech at a fixed level (band 2), never levelled (decision 0035).
        var leech = k.Base("ARG_MQ04_Leech", "Leech", "084AD6:Black Marsh.esm", 4);
        var giant = k.Base("ARG_MQ04_GiantLeech", "Giant Leech", "07F934:Black Marsh.esm", 7);

        // Spots: each actor and marker on a navmesh triangle; the cut root on the water edge south of the raised ground.
        var heraldAt = k.Snap(Raised, 92950, -12600);
        var minderAt = k.Snap(Raised, 93650, -12850);
        var eggAt = k.Snap(Raised, 93700, -13400);
        var rootAt = k.Snap(Edge, 92700, -13700);
        var markAt = k.Snap(Edge, rootAt.X + 60, rootAt.Y);
        var histXY = (X: 92750f, Y: -12800f);
        var histAt = new P3Float(histXY.X, histXY.Y, Land(histXY.X, histXY.Y));
        var fireAt = k.Snap(Rise, 91051, -7467);
        var tentAt = k.Snap(Rise, 90837, -6933);
        var boatAt = k.Snap(Rise, 91115, -7787);
        var cell1At = k.Snap(Rise, 91600, -7700); // the sentry, on the trail side (south)
        var cell2At = k.Snap(Rise, 90987, -6869);

        // E-enable parents: the camp (off until stage 40, off again at 91), the leeches of the way back (off until 45), the Hist withdrawn (on) and reconciled (off).
        var camp = k.Marker("CampParent", new P3Float(fireAt.X, fireAt.Y, fireAt.Z - 200), 0xC00);
        var withdrawn = k.Marker("WithdrawnParent", new P3Float(histAt.X, histAt.Y, histAt.Z - 300));
        var reconciled = k.Marker("ReconciledParent", new P3Float(histAt.X + 50, histAt.Y, histAt.Z - 300), 0xC00);
        var mark = k.Marker("CutRootMark", markAt);
        var returnParent = k.Marker("ReturnLeechesParent", new P3Float(rootAt.X, rootAt.Y, rootAt.Z - 300), 0xC00);

        // W-ref: the Hist (BM&V's statics: withdrawn the dead tree, reconciled the living one), the camp's statics.
        var histDark = k.Ref("HistWithdrawn", K("11FE74:Black Marsh.esm"), histAt, withdrawn);
        var histLight = k.Ref("HistReconciled", K("11FE7A:Black Marsh.esm"), histAt, reconciled);
        var fire = k.Ref("CampFire", K("1E44DE:Black Marsh.esm"), fireAt, camp);
        var tent = k.Ref("CampTent", K("0AA5F1:Black Marsh.esm"), tentAt, camp);
        var boat = k.Ref("CampBoat", K("08ABC1:Black Marsh.esm"), boatAt, camp);

        // The gum pot in Pays-Late's inventory; TR-acquire: the jars with the knife in one bundle by the camp's fire
        // (a loose item on the ground: PlaceCheck.Settle rests it).
        var gumPot = k.Item("GumPot", "Pays-Late's Gum Pot", k.ModelOf(K("1C40C2:Black Marsh.esm")), 1);
        minder.Items = [new ContainerEntry { Item = new ContainerItem { Item = gumPot.ToLink<IItemGetter>(), Count = 1 } }];
        var jars = k.Item("SapJars", "Jars of Hist Sap", k.ModelOf(K("08AB9C:Black Marsh.esm")), 4);
        var jarsXY = (X: fireAt.X + 120, Y: fireAt.Y);
        var jarsRef = k.Ref("SapJarsRef", jars.FormKey, new P3Float(jarsXY.X, jarsXY.Y, Land(jarsXY.X, jarsXY.Y) + 30), camp);

        var heraldRef = k.Actor("RootHeraldRef", herald, heraldAt);
        var minderRef = k.Actor("PaysLateRef", minder, minderAt);
        var eggRef = k.Actor("TurnsTheClutchRef", egg, eggAt);
        var cell1Ref = k.Actor("HidesHisWakeRef", cell1, cell1At, camp);
        var cell2Ref = k.Actor("CountsTheJarsRef", cell2, cell2At, camp);
        var leeches = new List<PlacedNpc>
        {
            k.Actor("LeechRoot1", leech, k.Snap(Edge, rootAt.X - 150, rootAt.Y - 100)),
            k.Actor("LeechRoot2", giant, k.Snap(Edge, rootAt.X + 150, rootAt.Y - 100)),
            k.Actor("LeechWater1", leech, k.Snap(North, 92600, -9500)),
            k.Actor("LeechWater2", leech, k.Snap(North, 93100, -9800)),
            k.Actor("LeechWater3", giant, k.Snap(North, 92300, -9200)),
            // The way back (review F2): enabled at stage 45, between the camp and the village.
            k.Actor("LeechBack1", leech, k.Snap(North, 92800, -10400), returnParent),
            k.Actor("LeechBack2", leech, k.Snap(North, 92400, -10800), returnParent),
            k.Actor("LeechBack3", giant, k.Snap(Edge, rootAt.X, rootAt.Y + 250), returnParent),
        };

        // TR-zone: two boxes at the cut root, one per outcome (the way down, prereq 20 sets 30; the return, prereq 45 sets 91).
        var zoneAt = new P3Float(rootAt.X, rootAt.Y, rootAt.Z + 100);
        var zone30 = k.Zone("ZoneRoot30", zoneAt, 20, 30);
        var zone91 = k.Zone("ZoneRoot91", zoneAt, 45, 91);

        // E-global, E-faction.
        var reconciledFlag = k.Global("Reconciled");
        var adoptedFlag = k.Global("Adopted");
        var standing = k.Global("LowReedStanding");
        var village = Faction(mod, "ARG_MQ04_LowReedVillage", "Low-Reed Village");

        // E-package: Pays-Late at the cut root after dark (C-time on the package), from stage 10 until the ending.
        var night = k.Travel("PaysLateNight", mark, Hour(CompareOperator.GreaterThanOrEqualTo, 20, or: true), Hour(CompareOperator.LessThan, 6),
            k.StageIs(10, CompareOperator.GreaterThanOrEqualTo), k.StageIs(91, CompareOperator.LessThan));

        // TR-topic: the record's topics, each INFO gated on its speaker's base (GetIsID), the stage and its check.
        var salt = K("034CDF:Skyrim.esm"); // Salt Pile (item.salt-pile): two placed by Lilmoth's fish barrels (F6, F7)
        k.Topic("Village", Label("topic.mq04-the-village"),
            k.Banded("topic.mq04-the-village", Herald, "speech", "TIF_ARG_MQ04_20", IsId(herald.FormKey), k.StageIs(10), Speech(25)),
            k.Banded("topic.mq04-the-village", Herald, "item", "TIF_ARG_MQ04_20Food", [Obj("Salt", salt)], IsId(herald.FormKey), k.StageIs(10), Has(salt, 2)),
            k.Banded("topic.mq04-the-village", Herald, "default", null, IsId(herald.FormKey), k.StageIs(10)));
        k.Topic("Boat", Label("topic.mq04-the-boat"),
            k.Banded("topic.mq04-the-boat", Egg, "speech", "TIF_ARG_MQ04_40", IsId(egg.FormKey), k.StageIs(30), Speech(25)),
            k.Banded("topic.mq04-the-boat", Egg, "default", null, IsId(egg.FormKey), k.StageIs(30)));
        // The cut (review F1): at 30 only while the player holds the pot, and it sets 40; at 40 and after, freely.
        k.Topic("Cut", Label("topic.mq04-the-cut"),
            k.Banded("topic.mq04-the-cut", Minder, "item", "TIF_ARG_MQ04_40", IsId(minder.FormKey), k.StageIs(30), Has(gumPot.FormKey, 1)),
            k.Banded("topic.mq04-the-cut", Minder, "default", null, IsId(minder.FormKey), k.StageIs(40, CompareOperator.GreaterThanOrEqualTo)));

        // The quest: Main Quest (the act's line), not Start Game Enabled; stages and objectives from the record.
        q.Name = "The Tree That Turned Its Face"; q.Priority = 60; q.Type = Quest.TypeEnum.MainQuest; q.Flags = Quest.Flag.RunOnce;
        k.StagesFromRecord(Id, "ARG_QF_MQ04", FragmentStages);
        k.ObjectivesFromRecord(Id);
        k.Forced(AHerald, "RootHerald", heraldRef);
        k.Forced(AMinder, "PaysLate", minderRef).PackageData.Add(night.ToLink());
        k.Forced(AEgg, "EggTender", eggRef);
        k.Forced(AJars, "Jars", jarsRef, QuestAlias.Flag.AllowDisabled | QuestAlias.Flag.Optional);
        k.Forced(AZone30, "ZoneRoot30", zone30);
        k.Forced(AZone91, "ZoneRoot91", zone91);
        k.Forced(ACell1, "HidesHisWake", cell1Ref, QuestAlias.Flag.AllowDisabled | QuestAlias.Flag.Optional);
        k.Forced(ACell2, "CountsTheJars", cell2Ref, QuestAlias.Flag.AllowDisabled | QuestAlias.Flag.Optional);
        q.VirtualMachineAdapter!.Scripts.Add(Script("ARG_QF_MQ04",
            k.Alias("RootHerald", AHerald), k.Alias("PaysLate", AMinder), Obj("CampParent", camp.FormKey), Obj("WithdrawnParent", withdrawn.FormKey),
            Obj("ReconciledParent", reconciled.FormKey), Obj("ReturnParent", returnParent.FormKey), Obj("SapJars", jars.FormKey), Obj("Reconciled", reconciledFlag.FormKey),
            Obj("Adopted", adoptedFlag.FormKey), Obj("Standing", standing.FormKey), Obj("LowReedVillage", village.FormKey), Obj("NextQuest", next.FormKey)));
        q.VirtualMachineAdapter.Aliases.Add(DeathSets(k, AHerald, 10, 20));   // fail-forward: the root-herald dead
        q.VirtualMachineAdapter.Aliases.Add(AcquireSets(k, AJars, 40, 45));   // the jars taken

        // World edits: everything persistent in the worldspace's persistent cell; the village named (W-name).
        world.TopCell!.Persistent.AddRange([camp, withdrawn, reconciled, mark, returnParent, histDark, histLight, fire, tent, boat, jarsRef, zone30, zone91]);
        world.TopCell.Persistent.AddRange([heraldRef, minderRef, eggRef, cell1Ref, cell2Ref]);
        world.TopCell.Persistent.AddRange(leeches);
        k.Exterior(world, VillageCell).Name = "Low-Reed Village";

        // F7: two Salt Piles on Lilmoth's fish barrel (02A1F6), on its modelled top (Surface.On, BlockTest's token shape).
        var barrel = K("02A1F6:Black Marsh.esm");
        var barrelAt = k.Placed[barrel].rec switch { IPlacedObjectGetter o => o.Placement!.Position, _ => throw new InvalidOperationException("MQ04: 02A1F6 is not a placed object") };
        var barrelWorld = mods.SelectMany(m => m.Worldspaces).First(w => (w.TopCell?.Persistent ?? []).Concat(w.SubCells.SelectMany(b => b.Items).SelectMany(sb => sb.Items)
            .SelectMany(c => c.Persistent.Concat(c.Temporary))).Any(r => r.FormKey == barrel)).FormKey;
        // The barrel is a container (10CD5B:Skyrim.esm), which Surface.Under does not read: its top is its object bounds'
        // top (Surface's own fallback for a model it cannot read), times its scale, over its placed z.
        var barrelRef = (IPlacedObjectGetter)k.Placed[barrel].rec;
        var bounds = Survey.Winners<IContainerGetter>(mods)[barrelRef.Base.FormKey].rec.ObjectBounds;
        var top = barrelAt.Z + bounds.Second.Z * (barrelRef.Scale ?? 1);
        var saltWorld = k.World(barrelWorld);
        saltWorld.TopCell!.Persistent.Add(k.Ref("SaltPile1", salt, new P3Float(barrelAt.X - 10, barrelAt.Y, MathF.Round(top + 3))));
        saltWorld.TopCell.Persistent.Add(k.Ref("SaltPile2", salt, new P3Float(barrelAt.X + 10, barrelAt.Y + 5, MathF.Round(top + 3))));
    }
}
