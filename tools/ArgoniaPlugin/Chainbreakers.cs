using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using Noggog;
using static LocalQuests;

// Phase 4's Chainbreakers line (story data quest.bc.bc01 to bc03), built from Phase 3's proven blocks with LocalQuests'
// kit. BC03 The Broker's Mercy stands on Soulrest's open dock, BM&V's Dock2 (02F35A, 11,-2) in BlackMarsh, whose
// navmesh is Black Marsh North's 0A7784. Allocated after LocalQuests in Generate.
static class Chainbreakers
{
    public static readonly FormKey BlackMarsh = FormKey.Factory("23D689:Black Marsh.esm");
    const string Dock2 = "02F35A:Black Marsh.esm";
    static readonly FormKey Gold = FormKey.Factory("00000F:Skyrim.esm"), Achievements = FormKey.Factory("0FC85D:Skyrim.esm"),
        PlayerRef = FormKey.Factory("000014:Skyrim.esm"), StrongBox = FormKey.Factory("09424C:Skyrim.esm"), OlavaToken = FormKey.Factory("059654:Skyrim.esm");
    public const uint B3Ussa = 0, B3Rope = 1, B3Chest = 2, B3Tokens = 3;

    public static void Add(SkyrimMod mod, List<ISkyrimModGetter> mods)
    {
        var kit = new Kit(mod, mods, BlackMarsh);
        Bc03(mod, mods, kit);
    }

    // BC03: Heavy-Rope's last-season topic (0 -> 10, once BC01 is at 90); Ussa-Rekh's season topic opens the sides; the
    // tokens topic (10 -> 20) or the refusal topic (10 -> 30); the tokens given back (20 -> 90); Heavy-Rope talked down
    // with Speechcraft 30 (30 -> 91) or paid 50 gold (30 -> 92); either man's death (10, 20, 30 -> 94; both essential).
    static void Bc03(SkyrimMod mod, List<ISkyrimModGetter> mods, Kit kit)
    {
        const string id = "quest.bc.bc03";
        var q = NewQuest(mod, "ARG_BC03", "The Broker's Mercy", id, [10, 20, 30, 90, 91, 92, 94], [90, 91, 92, 94]);
        var ussa = kit.Base("ARG_BC03_UssaRekh", "Ussa-Rekh", "02A1EE:Black Marsh.esm", 10, NpcConfiguration.Flag.Unique);
        var rope = kit.Base("ARG_BC03_HeavyRope", "Heavy-Rope", "00FF4D:Black Marsh.esm", 8, NpcConfiguration.Flag.Unique);
        ussa.Configuration.Flags &= ~NpcConfiguration.Flag.Female; rope.Configuration.Flags &= ~NpcConfiguration.Flag.Female;
        var tokens = mod.MiscItems.AddNew("ARG_BC03_Tokens");
        tokens.Name = "Carved Tokens"; tokens.Value = 0; tokens.Weight = 0.1f;
        tokens.Model = new Model { File = mods[0].MiscItems.First(m => m.FormKey == OlavaToken).Model!.File.DataRelativePath.Path };
        var heard = mod.Globals.AddNewShort("ARG_BC03_SeasonHeard"); heard.Data = 0;

        // On the dock among the crews (navmesh 0A7784): Ussa-Rekh with his chest beside him, Heavy-Rope a few steps off.
        var ussaAt = kit.Snap.At(Dock2, 48450, -5900);
        var chestAt = kit.Snap.At(Dock2, 48520, -5880);
        var ropeAt = kit.Snap.At(Dock2, 48700, -6100);
        var ussaRef = kit.Actor("ARG_BC03_UssaRekhRef", ussa, ussaAt);
        var ropeRef = kit.Actor("ARG_BC03_HeavyRopeRef", rope, ropeAt);
        var chest = kit.Marker("ARG_BC03_ChestRef", chestAt);
        chest.Base.SetTo(StrongBox);
        chest.Lock = new LockData { Level = LockLevel.Novice };
        chest.Owner.SetTo(ussa.FormKey);
        kit.World.TopCell!.Persistent.AddRange([ussaRef, ropeRef, chest]);

        Forced(q, B3Ussa, "Broker", ussaRef.FormKey, QuestAlias.Flag.Essential);
        Forced(q, B3Rope, "CrewBoss", ropeRef.FormKey, QuestAlias.Flag.Essential);
        Forced(q, B3Chest, "Chest", chest.FormKey);
        // F1: the tokens a Quest Object from stage 0, created in the chest by the alias (Bethesda's quest-item shape).
        q.Aliases.Add(new QuestAlias
        {
            ID = B3Tokens, Type = QuestAlias.TypeEnum.Reference, Name = "Tokens", Flags = QuestAlias.Flag.QuestObject,
            CreateReferenceToObject = new CreateReferenceToObject { Object = tokens.ToLink<ISkyrimMajorRecordGetter>(), AliasID = (short)B3Chest, Create = CreateReferenceToObject.CreateEnum.In, Level = Level.Easy },
        });
        q.VirtualMachineAdapter = new QuestAdapter
        {
            FileName = "ARG_QF_BC03",
            Scripts = { Script("ARG_QF_BC03", Alias("Broker", q, B3Ussa), Alias("CrewBoss", q, B3Rope), Obj("Tokens", tokens.FormKey),
                Obj("Gold001", Gold), Obj("AchievementsQuest", Achievements)) },
            Aliases = { AliasScript(q, B3Ussa, OnDeath(q, 10, 94)), AliasScript(q, B3Rope, OnDeath(q, 10, 94)) },
        };
        Fragments(q, "ARG_QF_BC03", [10, 20, 30, 90, 91, 92, 94]);

        // C-stage on BC01 (ARG_BC01): gated when it is built in this plugin.
        var bc01 = mod.Quests.FirstOrDefault(x => x.EditorID == "ARG_BC01");
        if (bc01 == null) Console.WriteLine("BC03: ARG_BC01 not in the plugin; the opening topic's BC01 >= 90 gate is left out until it is");
        ConditionFloat[] open = bc01 == null ? [StageIs(q, CompareOperator.EqualTo, 0)] : [StageIs(q, CompareOperator.EqualTo, 0), StageIs(bc01, CompareOperator.GreaterThanOrEqualTo, 90)];
        ConditionFloat Heard() { var d = new GetGlobalValueConditionData(); d.Global.Link.SetTo(heard.FormKey); return C(d, CompareOperator.EqualTo, 1); }
        ConditionFloat Speech(CompareOperator op) { var d = new GetActorValueConditionData { ActorValue = ActorValue.Speech, RunOnType = Condition.RunOnType.Reference }; d.Reference.SetTo(PlayerRef); return C(d, op, 30); }
        ConditionFloat Has(FormKey item, float n) { var d = new GetItemCountConditionData { RunOnType = Condition.RunOnType.Reference }; d.Reference.SetTo(PlayerRef); d.ItemOrList.Link.SetTo(item); return C(d, CompareOperator.GreaterThanOrEqualTo, n); }
        var lines = Lines("bc03");
        var isRope = IsId(rope.FormKey); var isUssa = IsId(ussa.FormKey);
        TopicV(mod, q, "BC03", lines, "topic.bc03-last-season", isRope, (10, open, null), (null, [StageIs(q, CompareOperator.GreaterThanOrEqualTo, 10)], null));
        TopicV(mod, q, "BC03", lines, "topic.bc03-the-season", isUssa, (null, [StageIs(q, CompareOperator.GreaterThanOrEqualTo, 10)], null));
        // F4: hearing the season opens the sides; its info's fragment sets ARG_BC03_SeasonHeard (E-global).
        var season = mod.DialogTopics.First(t => t.EditorID == "ARG_BC03_TheSeason").Responses[0];
        season.VirtualMachineAdapter = new DialogResponsesAdapter
        {
            Scripts = { Script("TIF_ARG_BC03_Season", Obj("SeasonHeard", heard.FormKey)) },
            ScriptFragments = new ScriptFragments { FileName = "TIF_ARG_BC03_Season", OnEnd = new ScriptFragment { ScriptName = "TIF_ARG_BC03_Season", FragmentName = "Fragment_0" } },
        };
        TopicV(mod, q, "BC03", lines, "topic.bc03-the-tokens", isRope, (20, [StageIs(q, CompareOperator.EqualTo, 10), Heard()], null));
        TopicV(mod, q, "BC03", lines, "topic.bc03-brawl", isRope, (30, [StageIs(q, CompareOperator.EqualTo, 10), Heard()], null));
        TopicV(mod, q, "BC03", lines, "topic.bc03-break", isRope, (90, [StageIs(q, CompareOperator.EqualTo, 20), Has(tokens.FormKey, 1)], null));
        TopicV(mod, q, "BC03", lines, "topic.bc03-yield-talk", isRope,
            (91, [StageIs(q, CompareOperator.EqualTo, 30), Speech(CompareOperator.GreaterThanOrEqualTo)], null),
            (null, [StageIs(q, CompareOperator.EqualTo, 30), Speech(CompareOperator.LessThan)], "fail"));
        TopicV(mod, q, "BC03", lines, "topic.bc03-yield-pay", isRope, (92, [StageIs(q, CompareOperator.EqualTo, 30), Has(Gold, 50)], null));
    }
}
