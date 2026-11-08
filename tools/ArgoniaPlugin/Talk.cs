using System.Text.Json;
using System.Text.RegularExpressions;
using Noggog;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;

// Talk (docs/design/talk.md, block W-talk): BM&V's people given topics of their own, from the story data's talk tables
// (story/data/db: talk_topic, talker, talk_line). One running quest ARG_Talk holds one top-level player topic per
// topic kind (its prompt is the menu choice); each talker's reply is one INFO under it, gated GetIsReference to the
// talker's placed reference (BM&V bases are shared: one base stands in sixteen places). A talker with no voice type
// gets ours, ARG_TalkSilentVoice (no vanilla line matches it, so no bark of Skyrim's; Fuz Ro D'oh times the
// subtitle). Allocated last in Generate, in sorted order, so earlier form ids never move.
static class Talk
{
    static readonly string Db = Path.Combine("story", "data", "db");

    static IEnumerable<JsonElement> Rows(string table) =>
        File.ReadLines(Path.Combine(Db, table + ".jsonl")).Where(l => l.Trim().Length > 0).Select(l => JsonDocument.Parse(l).RootElement);
    static string S(JsonElement e, string k) => e.GetProperty(k).GetString()!;

    public static void Add(SkyrimMod mod, List<ISkyrimModGetter> mods)
    {
        var lines = Rows("talk_line").ToList();
        if (lines.Count == 0) return;
        var census = Rows("bmv_talker").ToDictionary(r => S(r, "id"));
        var topics = Rows("talk_topic").ToDictionary(r => S(r, "id"));

        var q = mod.Quests.AddNew("ARG_Talk");
        q.Name = "Talk";
        q.Flags = Quest.Flag.StartGameEnabled;
        q.Priority = 20;
        q.Type = Quest.TypeEnum.Misc;
        q.Stages.Add(new QuestStage { Index = 0, Flags = QuestStage.Flag.StartUpStage, LogEntries = { new QuestLogEntry { Flags = 0 } } });

        var silent = mod.VoiceTypes.AddNew("ARG_TalkSilentVoice");
        var npcs = Survey.Winners<INpcGetter>(mods);
        foreach (var who in lines.Select(l => S(l, "talker")).Distinct().OrderBy(x => x))
        {
            var c = census[who];
            if (c.TryGetProperty("voice", out var v) && v.ValueKind != JsonValueKind.Null) continue;
            var baseKey = FormKey.Factory(S(c, "npc"));
            if (mod.Npcs.ContainsKey(baseKey)) continue; // a base two silent talkers share
            var npc = (Npc)npcs[baseKey].rec.DeepCopy();
            npc.Voice.SetTo(silent.FormKey);
            mod.Npcs.Add(npc);
        }

        // Greetings by standing (recipe v2 rule 2), Skyrim's own way: Skyrim.esm's Hello INFOs gate a friend's line on
        // GetRelationshipRank with the player >= 1 (37 of them) and the rest below it. One Hello topic in ARG_Talk; per
        // talker a stranger INFO (rank < 1) and a friend INFO (rank >= 1), each gated GetIsReference too.
        var greet = new Dictionary<string, CompareOperator> { ["talk.greet-stranger"] = CompareOperator.LessThan, ["talk.greet-friend"] = CompareOperator.GreaterThanOrEqualTo };
        var hellos = lines.Where(l => greet.ContainsKey(S(l, "topic"))).ToList();
        if (hellos.Count > 0)
        {
            var hello = mod.DialogTopics.AddNew("ARG_Talk_Hello");
            hello.Quest.SetTo(q.FormKey); hello.Priority = 50;
            hello.Category = DialogTopic.CategoryEnum.Misc; hello.Subtype = DialogTopic.SubtypeEnum.Hello; hello.SubtypeName = new RecordType("HELO");
            foreach (var who in hellos.GroupBy(l => (S(l, "talker"), S(l, "topic"))).OrderBy(w => w.Key.Item1).ThenByDescending(w => w.Key.Item2))
            {
                var info = new DialogResponses(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE) { Flags = new DialogResponseFlags() };
                byte n = 1;
                foreach (var l in who.OrderBy(l => l.GetProperty("ord").GetInt32()))
                    info.Responses.Add(new DialogResponse { Text = S(l, "text"), ResponseNumber = n++, Emotion = Emotion.Neutral });
                var d = new GetIsReferenceConditionData();
                d.Target.Link.SetTo(FormKey.Factory(who.Key.Item1));
                info.Conditions.Add(new ConditionFloat { CompareOperator = CompareOperator.EqualTo, ComparisonValue = 1, Data = d });
                var rank = new GetRelationshipRankConditionData();
                rank.TargetNpc.Link.SetTo(FormKey.Factory("000014:Skyrim.esm"));
                info.Conditions.Add(new ConditionFloat { CompareOperator = greet[who.Key.Item2], ComparisonValue = 1, Data = rank });
                hello.Responses.Add(info);
            }
        }

        var questRumour = QuestRumours();
        foreach (var g in lines.Where(l => !greet.ContainsKey(S(l, "topic")) && !questRumour.ContainsKey((S(l, "talker"), S(l, "topic")))).GroupBy(l => S(l, "topic")).OrderBy(g => g.Key))
        {
            var tp = topics[g.Key];
            var prompt = S(tp, "prompt");
            var id = "ARG_Talk_" + string.Concat(g.Key.Split('.')[1].Split('-').Select(p => char.ToUpper(p[0]) + p[1..]));
            var branch = mod.DialogBranches.AddNew(id + "Branch");
            var t = mod.DialogTopics.AddNew(id);
            branch.Quest.SetTo(q.FormKey); branch.Category = DialogBranch.CategoryType.Player; branch.Flags = DialogBranch.Flag.TopLevel;
            branch.StartingTopic.SetTo(t.FormKey);
            t.Name = prompt; t.Quest.SetTo(q.FormKey); t.Branch.SetTo(branch.FormKey); t.Priority = 50;
            t.Category = DialogTopic.CategoryEnum.Topic; t.Subtype = DialogTopic.SubtypeEnum.Custom; t.SubtypeName = new RecordType("CUST");
            foreach (var who in g.GroupBy(l => S(l, "talker")).OrderBy(w => w.Key))
            {
                var info = new DialogResponses(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE) { Flags = new DialogResponseFlags(), Prompt = prompt };
                byte n = 1;
                foreach (var l in who.OrderBy(l => l.GetProperty("ord").GetInt32()))
                    info.Responses.Add(new DialogResponse { Text = S(l, "text"), ResponseNumber = n++, Emotion = Emotion.Neutral });
                var d = new GetIsReferenceConditionData();
                d.Target.Link.SetTo(FormKey.Factory(who.Key));
                info.Conditions.Add(new ConditionFloat { CompareOperator = CompareOperator.EqualTo, ComparisonValue = 1, Data = d });
                t.Responses.Add(info);
            }
        }
        Console.WriteLine($"talk: {lines.Select(l => S(l, "talker")).Distinct().Count()} talkers, {mod.DialogTopics.Count(x => x.EditorID!.StartsWith("ARG_Talk_"))} topics, {lines.Count} responses");
        Names(mod, mods, census, npcs);
    }

    // Quest rumours (talk.md, talk.rumours: "a QUST that can start (its giver, its stage)"): a talker whose rumours fact
    // cites a quest ("quest ARG_X stage N; giver ...") is left out of Add and built by Rumours at the seed's end, once
    // every quest exists. Keyed (talker, topic) -> (quest editor id, start stage).
    // A source 'quest ARG_X stages A-B; ...' is a line about the quest running, not one to start it (BC02's fire, seen by
    // the talkers near the stone house): its INFO is gated GetStage >= A and <= B. hi is -1 for a start rumour.
    static readonly Regex QuestSource = new(@"^quest (ARG_\w+) stages? (\d+)(?:-(\d+))?;");
    static Dictionary<(string, string), (string quest, int stage, int hi)> QuestRumours()
    {
        var facts = Rows("talk_fact").Where(f => S(f, "topic") == "talk.rumours").Select(f => (id: S(f, "id"), m: QuestSource.Match(S(f, "source"))))
            .Where(f => f.m.Success).ToDictionary(f => f.id, f => (f.m.Groups[1].Value, int.Parse(f.m.Groups[2].Value),
                f.m.Groups[3].Success ? int.Parse(f.m.Groups[3].Value) : -1));
        var by = new Dictionary<(string, string), (string, int, int)>();
        foreach (var tt in Rows("talker_topic").Where(r => S(r, "topic") == "talk.rumours"))
        {
            var all = S(tt, "facts").Split(',').Select(x => x.Trim()).Where(x => x.Length > 0).ToList();
            var cited = all.Where(facts.ContainsKey).ToList();
            if (cited.Count == 0) continue;
            if (cited.Count != all.Count || cited.Count > 1) throw new Exception($"talk rumours: {S(tt, "talker")} must cite one quest rumour alone");
            by[(S(tt, "talker"), "talk.rumours")] = facts[cited[0]];
        }
        return by;
    }

    // Each quest rumour, one INFO under ARG_Talk_Rumours gated to the talker's ref (as Add) and on the quest not yet past
    // its start: the giver's opening INFO in the quest's own topics (GetStage quest == start, the C-stage) gives the gate,
    // and every GetStage condition on it (the quest's, and another quest's, as BC03's BC01 >= 90) is copied.
    public static void Rumours(SkyrimMod mod)
    {
        var want = QuestRumours();
        if (want.Count == 0) return;
        var lines = Rows("talk_line").Where(l => want.ContainsKey((S(l, "talker"), S(l, "topic")))).ToList();
        var t = mod.DialogTopics.First(x => x.EditorID == "ARG_Talk_Rumours");
        foreach (var who in lines.GroupBy(l => S(l, "talker")).OrderBy(w => w.Key))
        {
            var (edid, stage, hi) = want[(who.Key, "talk.rumours")];
            var q = mod.Quests.FirstOrDefault(x => x.EditorID == edid) ?? throw new Exception($"talk rumours: {edid} not in the plugin");
            bool IsStart(IConditionGetter c) => c is IConditionFloatGetter f && f.Data is IGetStageConditionDataGetter g && g.Quest.Link.FormKey == q.FormKey
                && f.CompareOperator == CompareOperator.EqualTo && f.ComparisonValue == stage;
            var opening = hi >= 0 ? null : mod.DialogTopics.Where(d => d.Quest.FormKey == q.FormKey).SelectMany(d => d.Responses)
                .FirstOrDefault(r => r.Conditions.Any(IsStart)) ?? throw new Exception($"talk rumours: {edid} has no opening line at stage {stage}");
            var info = new DialogResponses(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE) { Flags = new DialogResponseFlags(), Prompt = t.Name };
            byte n = 1;
            foreach (var l in who.OrderBy(l => l.GetProperty("ord").GetInt32()))
                info.Responses.Add(new DialogResponse { Text = S(l, "text"), ResponseNumber = n++, Emotion = Emotion.Neutral });
            var d = new GetIsReferenceConditionData();
            d.Target.Link.SetTo(FormKey.Factory(who.Key));
            info.Conditions.Add(new ConditionFloat { CompareOperator = CompareOperator.EqualTo, ComparisonValue = 1, Data = d });
            if (opening != null)
                foreach (var c in opening.Conditions.Where(c => c is IConditionFloatGetter { Data: IGetStageConditionDataGetter }))
                    info.Conditions.Add(c.DeepCopy());
            else
                foreach (var (op, v) in new[] { (CompareOperator.GreaterThanOrEqualTo, stage), (CompareOperator.LessThanOrEqualTo, hi) })
                {
                    var g = new GetStageConditionData();
                    g.Quest.Link.SetTo(q.FormKey);
                    info.Conditions.Add(new ConditionFloat { CompareOperator = op, ComparisonValue = v, Data = g });
                }
            t.Responses.Add(info);
        }
        Console.WriteLine($"talk rumours: {lines.Select(l => S(l, "talker")).Distinct().Count()} talkers rumour {want.Values.Select(v => v.quest).Distinct().Count()} quests");
    }

    // The slice quests' own people with no quest topic (story/data/quest_lines/quest_people.json): one top-level topic per
    // prompt in ARG_Talk, an INFO per person gated GetIsID to their base (a base of ours stands in one or two places) and
    // on a quest's stage window when given. After every quest, at the seed's end.
    public static void QuestPeople(SkyrimMod mod)
    {
        var doc = JsonDocument.Parse(File.ReadAllText(Path.Combine("story", "data", "quest_lines", "quest_people.json"))).RootElement;
        var q = mod.Quests.First(x => x.EditorID == "ARG_Talk");
        var topics = new Dictionary<string, DialogTopic>();
        int n = 0;
        foreach (var who in doc.EnumerateObject().Where(p => !p.Name.StartsWith('_')).OrderBy(p => p.Name))
        {
            var npc = mod.Npcs.FirstOrDefault(x => x.EditorID == who.Name) ?? throw new Exception($"quest people: no base {who.Name}");
            foreach (var v in who.Value.EnumerateArray())
            {
                var prompt = S(v, "prompt");
                if (!topics.TryGetValue(prompt, out var t))
                {
                    var id = "ARG_Talk_Quest" + string.Concat(prompt.Where(char.IsLetter));
                    var branch = mod.DialogBranches.AddNew(id + "Branch");
                    t = mod.DialogTopics.AddNew(id);
                    branch.Quest.SetTo(q.FormKey); branch.Category = DialogBranch.CategoryType.Player; branch.Flags = DialogBranch.Flag.TopLevel;
                    branch.StartingTopic.SetTo(t.FormKey);
                    t.Name = prompt; t.Quest.SetTo(q.FormKey); t.Branch.SetTo(branch.FormKey); t.Priority = 50;
                    t.Category = DialogTopic.CategoryEnum.Topic; t.Subtype = DialogTopic.SubtypeEnum.Custom; t.SubtypeName = new RecordType("CUST");
                    topics[prompt] = t;
                }
                var info = new DialogResponses(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE) { Flags = new DialogResponseFlags(), Prompt = prompt };
                byte r = 1;
                foreach (var l in v.GetProperty("lines").EnumerateArray())
                    info.Responses.Add(new DialogResponse { Text = l.GetString()!, ResponseNumber = r++, Emotion = Emotion.Neutral });
                var d = new GetIsIDConditionData();
                d.Object.Link.SetTo(npc.FormKey);
                info.Conditions.Add(new ConditionFloat { CompareOperator = CompareOperator.EqualTo, ComparisonValue = 1, Data = d });
                if (v.GetProperty("when") is { ValueKind: JsonValueKind.Array } w)
                {
                    var wq = mod.Quests.First(x => x.EditorID == w[0].GetString());
                    foreach (var (op, val) in new[] { (CompareOperator.GreaterThanOrEqualTo, w[1].GetInt32()), (CompareOperator.LessThan, w[2].GetInt32()) })
                    {
                        var g = new GetStageConditionData(); g.Quest.Link.SetTo(wq.FormKey);
                        info.Conditions.Add(new ConditionFloat { CompareOperator = op, ComparisonValue = val, Data = g });
                    }
                }
                t.Responses.Add(info); n++;
            }
        }
        Console.WriteLine($"quest people: {n} replies, {doc.EnumerateObject().Count(p => !p.Name.StartsWith('_'))} people, {topics.Count} topics");
    }

    // Every person we place has a voice: a base of ours drawn through Use Traits speaks with its template's voice, and a
    // voiceless BM&V template (1DE49D, ArgonianMaleTribeLeader1) leaves the person with no dialogue at all. The template at
    // the end of the Traits chain is overridden with ARG_TalkSilentVoice, as Add does for voiceless talkers.
    public static void Voices(SkyrimMod mod, List<ISkyrimModGetter> mods)
    {
        var npcs = Survey.Winners<INpcGetter>(mods);
        foreach (var n in mod.Npcs) npcs[n.FormKey] = (n, mod.ModKey);
        var silent = mod.VoiceTypes.First(v => v.EditorID == "ARG_TalkSilentVoice");
        var races = Survey.Winners<IRaceGetter>(mods);
        var done = new List<string>();
        foreach (var r in mod.EnumerateMajorRecords<IPlacedNpcGetter>().ToList())
        {
            if (!npcs.TryGetValue(r.Base.FormKey, out var b) || b.rec.FormKey.ModKey != mod.ModKey) continue;
            if (!races.TryGetValue(b.rec.Race.FormKey, out var race) || !race.rec.Flags.HasFlag(Race.Flag.Playable)) continue; // people, not creatures
            var v = b.rec;
            for (var i = 0; i < 8 && v.Configuration.TemplateFlags.HasFlag(NpcConfiguration.TemplateFlag.Traits) && npcs.TryGetValue(v.Template.FormKey, out var t); i++) v = t.rec;
            if (!v.Voice.IsNull) continue;
            var own = mod.Npcs.FirstOrDefault(x => x.FormKey == v.FormKey);
            if (own == null) { own = (Npc)v.DeepCopy(); mod.Npcs.Add(own); }
            own.Voice.SetTo(silent.FormKey);
            npcs[own.FormKey] = (own, mod.ModKey);
            done.Add(own.EditorID ?? own.FormKey.ToString());
        }
        Console.WriteLine($"voices: {done.Count} voiceless bases given ARG_TalkSilentVoice ({string.Join(", ", done)})");
    }

    static FormKey K(string k) => FormKey.Factory(k);
    // W-npc's look flags (BlockTest.cs): the face, race, voice, AI, inventory, factions and scripts come from the base
    // BM&V placed, so the person looks and behaves as before. Use Traits carries the face: the engine draws a templated
    // NPC with its template's FaceGen (facegeom/facetint under the template's plugin and form id), as ARG_BT_Keeper shows
    // on the dock. Use Base Data is off, so the name is ours; Use Stats is off, so the level is fixed (decision 0035).
    const NpcConfiguration.TemplateFlag Looks = NpcConfiguration.TemplateFlag.Traits | NpcConfiguration.TemplateFlag.Factions
        | NpcConfiguration.TemplateFlag.SpellList | NpcConfiguration.TemplateFlag.AIData | NpcConfiguration.TemplateFlag.AIPackages
        | NpcConfiguration.TemplateFlag.ModelAnimation | NpcConfiguration.TemplateFlag.Inventory | NpcConfiguration.TemplateFlag.Script
        | NpcConfiguration.TemplateFlag.DefPackList | NpcConfiguration.TemplateFlag.AttackData | NpcConfiguration.TemplateFlag.Keywords;

    // Looks-At-Books (03E418, Black Marsh North's "Looks at books") sold from vanilla's WEServiceMiscMerchant chest, whose
    // levelled lists stock any misc merchant in Skyrim; she gets a vendor faction of her own whose chest holds a book
    // trader's fixed stock: vanilla and BM&V books with no Nordic subject (decision 0006), paper, ink and quills.
    static readonly FormKey LooksAtBooks = K("03E418:Black Marsh North.esp"), MiscMerchant = K("0B5D55:Skyrim.esm");
    static readonly (string item, int count)[] BookStock =
    [
        ("01AFD7:Skyrim.esm", 1), ("01ACE7:Skyrim.esm", 1), ("01AFFC:Skyrim.esm", 1), ("01ACE8:Skyrim.esm", 1), // The Argonian Account 1 to 4
        ("01ACEF:Skyrim.esm", 1), ("0F699D:Skyrim.esm", 1),   // The Lusty Argonian Maid v1, v2
        ("006925:Dawnguard.esm", 1),                          // The Sultry Argonian Bard v1
        ("01B22B:Skyrim.esm", 1),                             // Short History of Morrowind
        ("166BB6:Black Marsh North.esp", 2),                  // Welcome to Black Marsh
        ("033761:Skyrim.esm", 5), ("04C3C6:Skyrim.esm", 2), ("04C3C8:Skyrim.esm", 3), // roll of paper, inkwell, quill
        ("00000F:Skyrim.esm", 300),                           // gold: a small trader's purse
    ];

    // Names (owner walk 2026-11-07): a placed ref's base is shared (02A1EE stands in sixteen places), so each talker whose
    // known_as differs from the base's name gets a base of their own, ARG_Talker_<ref>, templated on the old base for
    // its look, and the ref is overridden to place it. Allocated after the talk records, in sorted order.
    static void Names(SkyrimMod mod, List<ISkyrimModGetter> mods, Dictionary<string, JsonElement> census, Dictionary<FormKey, (INpcGetter rec, ModKey from)> npcs)
    {
        var talkers = Rows("talker").OrderBy(r => S(r, "id")).ToList();
        var placed = Survey.Winners<IPlacedGetter>(mods);
        // each talker's cell names its worldspace (bmv_cell); none means an interior
        var cellWs = Rows("bmv_cell").ToDictionary(r => S(r, "id"),
            r => r.TryGetProperty("worldspace", out var ws) && ws.ValueKind == JsonValueKind.String ? ws.GetString() : null);
        int named = 0, owned = 0;
        foreach (var t in talkers)
        {
            var id = S(t, "id"); var c = census[id];
            var name = S(t, "known_as");
            var oldName = c.TryGetProperty("name", out var nm) && nm.ValueKind == JsonValueKind.String ? nm.GetString() : null;
            if (name == oldName || name.StartsWith("the ")) continue;
            var refKey = K(id);
            if (LocalQuests.OwnsBase.Contains(refKey)) { owned++; continue; } // LQ25 gives this ref its base
            if (Overrides.Placed(mod, refKey) != null) throw new Exception($"talk names: {id} already overridden in the mod");
            var wsKey = cellWs.GetValueOrDefault(S(c, "cell"));
            var world = wsKey == null ? null : Overrides.World(mod, mods, K(wsKey));
            var tpl = npcs[K(S(c, "npc"))].rec;
            var n = mod.Npcs.AddNew("ARG_Talker_" + id.Split(':')[0]);
            n.Name = name;
            n.Template.SetTo(tpl.FormKey);
            n.Race.SetTo(tpl.Race.FormKey);
            n.Class.SetTo(tpl.Class.FormKey);
            n.Configuration.TemplateFlags = Looks;
            // the old base's level when it is fixed, else 5 (a PC-level-mult base would level against the player)
            n.Configuration.Level = new NpcLevel { Level = tpl.Configuration.Level is INpcLevelGetter l ? l.Level : (short)5 };
            var keep = NpcConfiguration.Flag.Female | NpcConfiguration.Flag.Essential | NpcConfiguration.Flag.Protected
                | NpcConfiguration.Flag.Unique | NpcConfiguration.Flag.SimpleActor;
            n.Configuration.Flags = NpcConfiguration.Flag.AutoCalcStats | (tpl.Configuration.Flags & keep);
            if (refKey == LooksAtBooks) Vendor(mod, mods, world, n, tpl, (IPlacedNpcGetter)placed[refKey].rec);

            var r = (PlacedNpc)((IPlacedNpcGetter)placed[refKey].rec).DeepCopy();
            r.Base.SetTo(n.FormKey);
            bool persistent = (r.MajorRecordFlagsRaw & 0x400) != 0;
            if (world != null && persistent) world.TopCell!.Persistent.Add(r);
            else
            {
                var cell = world != null ? Overrides.Exterior(mods, world, K(S(c, "cell"))) : Overrides.Interior(mod, mods, K(S(c, "cell")));
                if (persistent) cell.Persistent.Add(r); else cell.Temporary.Add(r);
            }
            named++;
        }
        Console.WriteLine($"talk names: {named} people given bases of their own, {owned} left to a quest's base");
    }

    // Looks-At-Books' own vendor faction (a copy of WEServiceMiscMerchant: its buy list, hours and ranks) whose chest is
    // ours, a persistent container ref 30 m under her stall holding BookStock; her base takes the old base's factions
    // with WEServiceMiscMerchant swapped for it (the Factions template flag off).
    static void Vendor(SkyrimMod mod, List<ISkyrimModGetter> mods, Worldspace world, Npc n, INpcGetter tpl, IPlacedNpcGetter at)
    {
        var src = Survey.Winners<IFactionGetter>(mods)[MiscMerchant].rec;
        var f = mod.Factions.AddNew("ARG_VendorLooksAtBooks");
        f.DeepCopyIn(src, new Faction.TranslationMask(true) { EditorID = false, FormVersion = false, VersionControl = false });
        var srcChest = Survey.Winners<IPlacedObjectGetter>(mods)[src.MerchantContainer.FormKey].rec;
        var chestBase = Survey.Winners<IContainerGetter>(mods)[srcChest.Base.FormKey].rec;
        var box = mod.Containers.AddNew("ARG_VendorLooksAtBooksChest");
        box.DeepCopyIn(chestBase, new Container.TranslationMask(true) { EditorID = false, FormVersion = false, VersionControl = false, Items = false, Name = false });
        box.Items = BookStock.Select(s => new ContainerEntry { Item = new ContainerItem { Item = new FormLink<IItemGetter>(K(s.item)), Count = s.count } }).ToExtendedList();
        var p = at.Placement!.Position;
        var chest = new PlacedObject(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE)
        {
            EditorID = "ARG_VendorLooksAtBooksChestRef", MajorRecordFlagsRaw = 0x400,
            Placement = new Placement { Position = new P3Float(p.X, p.Y, p.Z - 2100) },
        };
        chest.Base.SetTo(box.FormKey);
        world.TopCell!.Persistent.Add(chest);
        f.MerchantContainer.SetTo(chest.FormKey);
        n.Configuration.TemplateFlags &= ~NpcConfiguration.TemplateFlag.Factions;
        foreach (var r in tpl.Factions)
            n.Factions.Add(new RankPlacement { Faction = new FormLink<IFactionGetter>(r.Faction.FormKey == MiscMerchant ? f.FormKey : r.Faction.FormKey), Rank = r.Rank });
    }
}
