using System.Text.Json;
using Noggog;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using static QuestKit;

// Phase 4's two local quests at Helstrom (story data quest.local.lq30, quest.local.lq25), built from Phase 3's proven
// blocks only (docs/design/blocks.md; each record's review finding B1 says what was re-authored). Both stand in BM&V's
// BlackMarsh2 (0D6960). Journal and objective text come from the story data rows; the dialogue from
// story/data/quest_lines/<code>.json (dialogue-write, text-review). Allocated after Combat in Generate, LQ30 then LQ25.
static class LocalQuests
{
    public static readonly FormKey BlackMarsh2 = FormKey.Factory("0D6960:Black Marsh.esm");
    static readonly FormKey Achievements = K("0FC85D:Skyrim.esm");
    // The ref BM&V placed at Helstrom's gate (the levy warden; MQ05 cites him too).
    public static readonly FormKey Warden = K("08D5E9:Black Marsh North.esp");
    public static readonly FormKey Poler = K("08D5EE:Black Marsh North.esp"), Steerer = K("08D5EF:Black Marsh North.esp"), Captain = K("08D5F1:Black Marsh North.esp");
    public const uint L30Kin = 0, L30Youth = 1, L30Viper = 2, L30Warden = 3, L30Zone = 4;
    public const uint L25Poler = 0, L25Steerer = 1, L25Captain = 2, L25Croc = 3;
    public static readonly List<ModKey> Masters = [];

    // What the checks read (LocalQuestsCheck, ChainbreakersCheck): the record's rows and lines, through the kit.
    public static Dictionary<int, string> Journal(string quest) => QuestKit.Stages(quest).ToDictionary(s => s.id, s => s.journal);
    public static Dictionary<int, string> Objectives(string quest) => QuestKit.Objectives(quest).ToDictionary(o => o.stage, o => o.text);
    public static JsonElement Lines(string code) => QuestKit.QuestLines(code);
    public static List<string> After(string code, string who, string variant = "after") => QuestKit.After(code, who, variant);

    // Placed refs whose base a quest here owns (LQ25's poler and steerer): Talk gates their lines but leaves the base to LQ25.
    public static readonly FormKey[] OwnsBase = [Poler, Steerer];

    public static void Add(SkyrimMod mod, List<ISkyrimModGetter> mods)
    {
        var world = new QuestKit(mod, mods).World(BlackMarsh2);
        Lq30(mod, mods, world);
        Lq25(mod, mods, world);
    }

    /// After MQ05 is in the plugin: Okan-Zish's opening topic (every INFO of ARG_LQ25_TheBeast gated on LQ25's stage 0) opens only
    /// once MQ05 is at 40.
    public static void Finish(SkyrimMod mod)
    {
        var mq05 = mod.Quests.FirstOrDefault(x => x.EditorID == "ARG_MQ05") ?? throw new InvalidOperationException("LQ25: ARG_MQ05 is not in the plugin; its opening topic's MQ05 >= 40 gate cannot be built");
        var lq25 = mod.Quests.First(x => x.EditorID == "ARG_LQ25");
        var opening = mod.DialogTopics.First(t => t.EditorID == "ARG_LQ25_TheBeast").Responses
            .Where(r => r.Conditions.OfType<IConditionFloatGetter>().Any(c => c.Data is IGetStageConditionDataGetter g && g.Quest.Link.FormKey == lq25.FormKey && c.CompareOperator == CompareOperator.EqualTo && c.ComparisonValue == 0)).ToList();
        if (opening.Count == 0) throw new InvalidOperationException("LQ25: no INFO of ARG_LQ25_TheBeast is gated on stage 0");
        foreach (var r in opening) r.Conditions.Add(StageIs(mq05, CompareOperator.GreaterThanOrEqualTo, 40));
    }

    // LQ30 The Gates of Helstrom: Haj-Wan's topic (0 -> 30), the viper's death (30 -> 40), the gate zone (40 -> 91) or
    // Sei-Wan's topic (40 -> 92); Sei-Wan's death (30, 40 -> 93).
    static void Lq30(SkyrimMod mod, List<ISkyrimModGetter> mods, Worldspace world)
    {
        const string id = "quest.local.lq30";
        var q = mod.Quests.AddNew("ARG_LQ30");
        var kit = new QuestKit(mod, mods, q);
        kit.Header("The Gates of Helstrom", 50, Quest.TypeEnum.SideQuest, Quest.Flag.StartGameEnabled);
        kit.FromRecord(id, "ARG_QF_LQ30", [30, 40, 91, 92, 93], ends: [91, 92, 93]);
        var kin = kit.Base("ARG_LQ30_HajWan", "Haj-Wan", "02A1EE:Black Marsh.esm", 5, NpcConfiguration.Flag.Protected | NpcConfiguration.Flag.Unique);
        var youth = kit.Base("ARG_LQ30_SeiWan", "Sei-Wan", "00FF4D:Black Marsh.esm", 3, NpcConfiguration.Flag.Protected | NpcConfiguration.Flag.Unique);
        var viper = kit.Base("ARG_LQ30_Viper", "Viper", "17BC83:Black Marsh.esm", 12, 0); // band 3, fixed

        var gate = kit.Pos(Warden);                                   // (-27858, 77815): BM&V's gate soldier
        var kinAt = kit.Snap("0D787F:Black Marsh.esm", gate.X + 150, gate.Y - 100);
        var markAt = kit.Snap("0D787F:Black Marsh.esm", gate.X - 600, gate.Y - 250); // inside the city, out of sight of the zone
        var youthAt = kit.Snap("0D7883:Black Marsh.esm", -18324, 77678); // the roots in the shallows, navmesh 1FAE4C
        var viperAt = kit.Snap("0D7883:Black Marsh.esm", -18093, 77568);
        var viperParent = kit.Marker("ARG_LQ30_ViperParent", new P3Float(viperAt.X, viperAt.Y, viperAt.Z - 200), 0xC00);
        var kinRef = kit.Actor("ARG_LQ30_HajWanRef", kin, kinAt);
        var youthRef = kit.Actor("ARG_LQ30_SeiWanRef", youth, youthAt, viperParent); // absent before 30 (quest review)
        var viperRef = kit.Actor("ARG_LQ30_ViperRef", viper, viperAt, viperParent);
        var mark = kit.Marker("ARG_LQ30_GateMarker", markAt);
        var zone = kit.Zone("ARG_LQ30_GateZone", new P3Float(gate.X, gate.Y, gate.Z + 100), 40, 91, new P3Float(400, 400, 300));
        world.TopCell!.Persistent.AddRange([viperParent, kinRef, youthRef, viperRef, mark, zone]);
        kit.Persist(world, Warden);

        kit.Forced(L30Kin, "Kin", kinRef.FormKey);
        kit.Forced(L30Youth, "Youth", youthRef.FormKey, QuestAlias.Flag.Protected);
        kit.Forced(L30Viper, "Viper", viperRef.FormKey, QuestAlias.Flag.AllowDisabled);
        kit.Forced(L30Warden, "Warden", Warden);
        kit.Forced(L30Zone, "GateZone", zone);
        q.VirtualMachineAdapter!.Scripts.Add(Script("ARG_QF_LQ30", Alias("Kin", q, L30Kin), Alias("Youth", q, L30Youth), Obj("ViperParent", viperParent.FormKey),
            Obj("GateMarker", mark.FormKey), Obj("GateZone", zone.FormKey), Obj("Gold001", Gold), Obj("AchievementsQuest", Achievements)));
        q.VirtualMachineAdapter.Aliases.Add(DeathSets(kit, L30Viper, 30, 40));
        q.VirtualMachineAdapter.Aliases.Add(DeathSets(kit, L30Youth, 30, 93));

        var lines = QuestLines("lq30");
        kit.RecordV("LQ30", lines, "topic.lq30-walked-out", IsId(kin.FormKey),
            (30, [StageIs(q, CompareOperator.EqualTo, 0)], null), (null, [StageIs(q, CompareOperator.EqualTo, 30)], null));
        kit.RecordV("LQ30", lines, "topic.lq30-the-basin", IsRef(Warden), (null, [StageIs(q, CompareOperator.EqualTo, 30)], null));
        kit.RecordV("LQ30", lines, "topic.lq30-come-back", IsId(youth.FormKey), (92, [StageIs(q, CompareOperator.EqualTo, 40)], null));
        // Sei-Wan at the gate after the quest (the record's after-90 state): his greeting by ending, 91 or 92.
        // and Haj-Wan's, by the ending (91, 92, 93).
        kit.AfterHellos("ARG_LQ30_AfterHello", "lq30", (youthRef.FormKey, "sei-wan", []), (kinRef.FormKey, "lq30-kin", []));
        // Objective targets, from the record's target column: Sei-Wan (30, 40) and the gate zone (40).
        kit.TargetsFromRecord(id, new()
        {
            ["npc.hist-heartland.helstrom.lq30-youth"] = [L30Youth], ["thing.lq30.zones"] = [L30Zone],
        });
        kit.Finish();
    }

    // LQ25 The River Monster: Okan-Zish's topic once MQ05 is at 40 (0 -> 20), the crocodile's death (20 -> 40), the
    // captain's topic with the bucket (40 -> 91) or Wuleen-Taza's (40 -> 92); the captain's death (40 -> 93).
    static void Lq25(SkyrimMod mod, List<ISkyrimModGetter> mods, Worldspace world)
    {
        const string id = "quest.local.lq25";
        var q = mod.Quests.AddNew("ARG_LQ25");
        var kit = new QuestKit(mod, mods, q);
        kit.Header("The River Monster", 50, Quest.TypeEnum.SideQuest, Quest.Flag.StartGameEnabled);
        // stage 93 (the captain dead) is not built: Sells-Dear's base is vanilla Essential, nothing can set it
        kit.FromRecord(id, "ARG_QF_LQ25", [20, 40, 91, 92], ends: [91, 92]);
        var poler = kit.Base("ARG_LQ25_OkanZish", "Okan-Zish", "00FF4D:Black Marsh.esm", 5, NpcConfiguration.Flag.Protected | NpcConfiguration.Flag.Unique);
        var steerer = kit.Base("ARG_LQ25_WuleenTaza", "Wuleen-Taza", "02A1EE:Black Marsh.esm", 5, NpcConfiguration.Flag.Protected | NpcConfiguration.Flag.Unique);
        var croc = kit.Base("ARG_LQ25_Crocodile", "Crocodile", "0BCB00:Black Marsh.esm", 4, 0); // band 1, fixed
        var bucket = mod.MiscItems.AddNew("ARG_LQ25_BaitBucket");
        bucket.Name = "Bait Bucket"; bucket.Value = 0; bucket.Weight = 2;
        bucket.Model = new Model { File = mods[0].MiscItems.First(m => m.FormKey == K("012FDF:Skyrim.esm")).Model!.File.DataRelativePath.Path }; // Bucket01

        // The lair: the shallows under the crew's plank walk (BM&V's 05A835 planks), navmesh 1FAEB6 in 0D77AF.
        var crocAt = kit.Snap("0D77AF:Black Marsh.esm", -36450, 64100);
        var bucketNav = kit.Snap("0D77AF:Black Marsh.esm", -36600, 64150);
        var bucketAt = new P3Float(bucketNav.X, bucketNav.Y, bucketNav.Z + 30);
        var crocParent = kit.Marker("ARG_LQ25_CrocParent", new P3Float(crocAt.X, crocAt.Y, crocAt.Z - 200), 0xC00);
        var crocRef = kit.Actor("ARG_LQ25_CrocodileRef", croc, crocAt, crocParent);
        var bucketRef = kit.Marker("ARG_LQ25_BaitBucketRef", bucketAt);
        bucketRef.Base.SetTo(bucket.FormKey);
        bucketRef.EnableParent = new EnableParent(); bucketRef.EnableParent.Reference.SetTo(crocParent.FormKey);
        world.TopCell!.Persistent.AddRange([crocParent, crocRef, bucketRef]);
        kit.Persist(world, Poler, poler); kit.Persist(world, Steerer, steerer); kit.Persist(world, Captain);

        kit.Forced(L25Poler, "Poler", Poler);
        kit.Forced(L25Steerer, "Steerer", Steerer);
        kit.Forced(L25Captain, "Captain", Captain);
        kit.Forced(L25Croc, "Crocodile", crocRef.FormKey, QuestAlias.Flag.AllowDisabled);
        q.VirtualMachineAdapter!.Scripts.Add(Script("ARG_QF_LQ25", Alias("Steerer", q, L25Steerer), Alias("Captain", q, L25Captain), Obj("CrocParent", crocParent.FormKey),
            Obj("BaitBucket", bucket.FormKey), Obj("Gold001", Gold), Obj("AchievementsQuest", Achievements)));
        q.VirtualMachineAdapter.Aliases.Add(DeathSets(kit, L25Croc, 20, 40));
        // the captain is vanilla's Essential base: he cannot die, so no death trigger (the kit refuses one)

        // The opening topic's MQ05 >= 40 gate is added by Finish(mod) once ARG_MQ05 exists.
        var hasBucket = new GetItemCountConditionData { RunOnType = Condition.RunOnType.Reference }; hasBucket.Reference.SetTo(PlayerRef); hasBucket.ItemOrList.Link.SetTo(bucket.FormKey);
        var lines = QuestLines("lq25");
        kit.RecordV("LQ25", lines, "topic.lq25-the-beast", IsId(poler.FormKey), (20, [StageIs(q, CompareOperator.EqualTo, 0)], null), (null, [StageIs(q, CompareOperator.EqualTo, 20)], null));
        kit.RecordV("LQ25", lines, "topic.lq25-tell-captain", IsRef(Captain), (91, [StageIs(q, CompareOperator.EqualTo, 40), C(hasBucket, CompareOperator.GreaterThanOrEqualTo, 1)], null));
        kit.RecordV("LQ25", lines, "topic.lq25-keep-quiet", IsId(steerer.FormKey), (92, [StageIs(q, CompareOperator.EqualTo, 40)], null));
        // Sells-Dear's and Wuleen-Taza's greetings by the ending (91, 92; the record's 93 is not built).
        kit.AfterHellos("ARG_LQ25_AfterHello", "lq25", (Captain, "boat-captain", []), (Steerer, "lq25-crew-steerer", []));
        // Objective targets, from the record's target column: the crocodile (20), Sells-Dear and Wuleen-Taza (40).
        kit.TargetsFromRecord(id, new()
        {
            ["thing.lq25.beast"] = [L25Croc], ["npc.hist-heartland.helstrom.boat-captain"] = [L25Captain], ["npc.hist-heartland.helstrom.lq25-crew-steerer"] = [L25Steerer],
        });
        kit.Finish();
    }
}
