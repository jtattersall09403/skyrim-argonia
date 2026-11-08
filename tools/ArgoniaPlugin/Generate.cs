using Noggog;
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;

// seed <out.esp> <plugin paths in load order...>: Argonia.esp from shutdown.json and the opening's records.
static class Generate
{
    static readonly ModKey Ours = ModKey.FromFileName("Argonia.esp");
    // The opening's spot: a navmesh triangle's centre on Lilmoth's dock, BM&V cell 005A21 (7,-1), NAVM 07EEF8 triangle 14,
    // on the fishing dock (BYOHFishDock01 005A21's 02A20A) beside Black Marsh North's "Lilmoth Dock" map marker 082193
    // (30909,-2852). Cell Dock1 (1,-2) was Hereguard Plantation's dock (owner's walk, 2026-11-06). The read-back checks it.
    static readonly P3Float Spot = new(30901f, -2903f, 3f);

    static FormLink<ISkyrimMajorRecordGetter> Fk(string k) => new(FormKey.Factory(k));
    // Magic Expanded (Magic.esp 5.1) spells in the test kit, by editor id: Mark, Recall (aaaMarkRecallSpell), Jump (it has
    // no Levitate), Slowfall, Water Walking, Fire Touch, Damage Health (Entropic Bolt), Force, Burden, Teleport, Analyze,
    // Dispel Self, Soul Trap Mass, Bound Shield.
    static readonly string[] TestSpells = ["000A8C", "000A8E", "0009EE", "00095C", "000A9B", "000A0A", "0009BE", "000AA5", "0009FB", "0009F2", "000ACD", "000991", "000823", "0009D3"];

    public static void Run(string outPath, string[] paths)
    {
        var plan = JsonDocument.Parse(File.ReadAllText(Path.Combine(AppContext.BaseDirectory, "shutdown.json"))).RootElement;
        var mods = Survey.Load(paths);
        var quests = Survey.Winners<IQuestGetter>(mods);
        var nodes = Survey.Winners<IAStoryManagerNodeGetter>(mods);
        var byEdid = quests.Values.Where(v => v.rec.EditorID != null).GroupBy(v => v.rec.EditorID!).ToDictionary(g => g.Key, g => g.Last().rec);
        var nodeByEdid = nodes.Values.Where(v => v.rec.EditorID != null).GroupBy(v => v.rec.EditorID!).ToDictionary(g => g.Key, g => g.Last().rec);

        var mod = new SkyrimMod(Ours, SkyrimRelease.SkyrimSE);
        mod.ModHeader.Author = "Elder Souls: Argonia";
        mod.ModHeader.Description = "Built from plugin/Argonia (Spriggit YAML); seeded by tools/ArgoniaPlugin.";

        // Our records: allocate in a fixed order so form ids are stable.
        var global = mod.Globals.AddNewShort("ARG_VanillaStoryManager");
        global.Data = 0;
        var opening = mod.Quests.AddNew("ARG_Opening");
        var world = new Worldspace(FormKey.Factory("23D689:Black Marsh.esm"), SkyrimRelease.SkyrimSE);
        // The load order's winning BlackMarsh (Black Marsh North.esp overrides BM&V's): our override starts from it.
        var (bmWorld, worldFrom) = Survey.Winners<IWorldspaceGetter>(mods)[world.FormKey];
        var marker = new PlacedObject(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE)
        {
            EditorID = "ARG_OpeningMarker",
            Base = new FormLinkNullable<IPlaceableObjectGetter>(FormKey.Factory("00003B:Skyrim.esm")), // XMarker
            MajorRecordFlagsRaw = 0x400, // persistent: MoveTo needs it loaded from anywhere
            Placement = new Placement { Position = Spot, Rotation = new P3Float(0, 0, 0) },
        };
        world = bmWorld.DeepCopy(new Worldspace.TranslationMask(true) { SubCells = false, TopCell = false });
        world.TopCell = bmWorld.TopCell!.DeepCopy(new Cell.TranslationMask(true) { Persistent = false, Temporary = false, NavigationMeshes = false, Landscape = false });
        world.TopCell.Persistent.Add(marker);
        mod.Worldspaces.Add(world);
        // Phase 3's test quest (BlockTest.cs): allocated next, removed after the owner's walk.
        BlockTest.Add(mod, mods, world, Spot);

        // The opening quest: started by MQ101's stage 0 (below), its script moves the player and sets stage 10.
        opening.Flags = Quest.Flag.RunOnce;
        opening.Priority = 90;
        opening.Type = Quest.TypeEnum.SideQuest;
        opening.Name = "The Work Detail";
        // A stage's fragment binds to one of its log entries (VMAD: stage, log entry index), so a startup stage holds one
        // empty entry, as every vanilla stage does; with none the fragment never ran and New Game stayed on the menu.
        opening.Stages.Add(new QuestStage { Index = 0, Flags = QuestStage.Flag.StartUpStage, LogEntries = { new QuestLogEntry { Flags = 0 } } });
        opening.Stages.Add(new QuestStage
        {
            Index = 10,
            LogEntries = { new QuestLogEntry { Flags = 0, Entry = "I woke as a prisoner on the work detail at Lilmoth. I own nothing but the roughspun I wear." } },
        });
        // Skyrim lists an active quest in the Quests menu only once one of its objectives is shown (owner's walk
        // 2026-11-07: the log entry alone left the menu empty); the script shows it with stage 10, as vanilla stages do.
        opening.Objectives.Add(new QuestObjective { Index = 10, DisplayText = "Stay with the work detail on Lilmoth's dock" });
        opening.VirtualMachineAdapter = new QuestAdapter
        {
            Scripts =
            {
                new ScriptEntry
                {
                    Name = "ARG_StartQuestScript",
                    Properties =
                    {
                        new ScriptObjectProperty { Name = "StartMarker", Object = marker.ToLink() },
                        new ScriptObjectProperty { Name = "Tunic", Object = new FormLink<ISkyrimMajorRecordGetter>(FormKey.Factory("03C9FE:Skyrim.esm")) },
                        new ScriptObjectProperty { Name = "Footwraps", Object = new FormLink<ISkyrimMajorRecordGetter>(FormKey.Factory("03CA00:Skyrim.esm")) },
                        // TEST KIT for the walk phases (owner, 2026-11-06), removed with the authored opening (Phase 3):
                        // an Imperial sword and light shield (decision 0006: no Nordic item) and a set of Magic Expanded spells.
                        new ScriptObjectProperty { Name = "TestWeapon", Object = Fk("0135B8:Skyrim.esm") }, // Imperialsword
                        new ScriptObjectProperty { Name = "TestShield", Object = Fk("013AB2:Skyrim.esm") }, // ArmorImperialLightShield
                        // and Magistrate Levitate's Levitate (owner walk 2026-11-07), last
                        new ScriptObjectListProperty { Name = "TestSpells", Objects = TestSpells.Select(k => new ScriptObjectProperty { Object = Fk(k + ":Magic.esp") })
                            .Append(new ScriptObjectProperty { Object = Fk("0083EB:Magistrate Levitate.esp") }).ToExtendedList() },
                    },
                },
            },
        };

        // MQ101, the engine's new-game quest: the Helgen intro replaced by one stage-0 fragment that starts ours
        // (LAL's method: MQ101's stage-0 fragment moves the player to the start marker and starts the next quest; here
        // nothing of Helgen is kept).
        var mq101 = new Quest(FormKey.Factory("03372B:Skyrim.esm"), SkyrimRelease.SkyrimSE)
        {
            EditorID = "MQ101", Flags = Quest.Flag.RunOnce, Priority = 80, Type = Quest.TypeEnum.MainQuest,
            Stages = { new QuestStage { Index = 0, Flags = QuestStage.Flag.StartUpStage, LogEntries = { new QuestLogEntry { Flags = 0 } } } },
            VirtualMachineAdapter = new QuestAdapter
            {
                FileName = "ARG_QF_MQ101",
                Scripts =
                {
                    new ScriptEntry
                    {
                        Name = "ARG_QF_MQ101",
                        Properties =
                        {
                            new ScriptObjectProperty { Name = "ARGOpening", Object = opening.ToLink() },
                            new ScriptObjectProperty { Name = "StartMarker", Object = marker.ToLink() },
                        },
                    },
                },
                Fragments = { new QuestScriptFragment { Stage = 0, StageIndex = 0, ScriptName = "ARG_QF_MQ101", FragmentName = "Fragment_0" } },
            },
        };
        mod.Quests.Add(mq101);

        // The shutdown: Start Game Enabled off, text stripped (these quests never run).
        var strip = new Quest.TranslationMask(true)
        {
            Name = false, Description = false, Objectives = false,
            Stages = new QuestStage.TranslationMask(true) { LogEntries = new QuestLogEntry.TranslationMask(true) { Entry = false } },
        };
        foreach (var group in plan.GetProperty("quests_sge_off").EnumerateObject())
            foreach (var e in group.Value.EnumerateArray())
            {
                var id = e.GetString()!;
                if (!byEdid.TryGetValue(id, out var q)) throw new Exception($"no quest {id}");
                if (!q.Flags.HasFlag(Quest.Flag.StartGameEnabled)) throw new Exception($"{id} is not Start Game Enabled");
                var copy = q.DeepCopy(strip);
                copy.Flags &= ~Quest.Flag.StartGameEnabled;
                copy.Name = null; copy.Description = null;
                foreach (var st in copy.Stages) foreach (var le in st.LogEntries) le.Entry = null;
                foreach (var o in copy.Objectives) o.DisplayText = null;
                mod.Quests.Add(copy);
            }
        var cond = new ConditionFloat
        {
            CompareOperator = CompareOperator.EqualTo, ComparisonValue = 1,
            Data = new GetGlobalValueConditionData { Global = { Link = { FormKey = global.FormKey } } },
        };
        foreach (var group in plan.GetProperty("story_nodes_off").EnumerateObject())
            foreach (var e in group.Value.EnumerateArray())
            {
                var id = e.GetString()!;
                var n = id.Contains(':') ? nodes[FormKey.Factory(id)].rec : nodeByEdid.TryGetValue(id, out var x) ? x : throw new Exception($"no node {id}");
                var copy = (IAStoryManagerNode)n.DeepCopy();
                copy.Conditions.Insert(0, cond.DeepCopy());
                switch (copy)
                {
                    case StoryManagerQuestNode qn: mod.StoryManagerQuestNodes.Add(qn); break;
                    case StoryManagerBranchNode bn: mod.StoryManagerBranchNodes.Add(bn); break;
                    default: throw new Exception($"{id}: not a quest or branch node");
                }
            }
        // Talk (Talk.cs): BM&V's people's own topics, from the story data; allocated last so earlier ids never move.
        Talk.Add(mod, mods);
        // Name fix: BM&V's villager base 02A1EE (sixteen placements) is spelt "Aragonian Vliiager"; an override of its name
        // only, copied from the last plugin in the load order that defines it (not the master alone).
        {
            var key = FormKey.Factory("02A1EE:Black Marsh.esm");
            var villager = mod.Npcs.FirstOrDefault(n => n.FormKey == key) ?? (Npc)Survey.Winners<INpcGetter>(mods)[key].rec.DeepCopy();
            villager.Name = "Argonian Villager";
            if (!mod.Npcs.Any(n => n.FormKey == key)) mod.Npcs.Add(villager);
        }
        // Combat (Combat.cs): drawn-weapon run speeds and no player health regen; allocated after Talk.
        Combat.Add(mod, mods);
        var order = mods.Select(m => m.ModKey).Append(Ours).ToList();
        // The plugin whose worldspace record we override is a master even when no form of it is referenced, so ours
        // always loads after it.
        mod.BeginWrite.ToPath(outPath).WithLoadOrder(order).WithNoDataFolder().WithExtraIncludedMasters(worldFrom).Write();
        Console.WriteLine($"wrote {outPath}: {mod.EnumerateMajorRecords().Count()} records");
    }
}
