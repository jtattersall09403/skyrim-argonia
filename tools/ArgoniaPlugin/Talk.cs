using System.Text.Json;
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
            var npc = (Npc)npcs[baseKey].rec.DeepCopy();
            npc.Voice.SetTo(silent.FormKey);
            mod.Npcs.Add(npc);
        }

        foreach (var g in lines.GroupBy(l => S(l, "topic")).OrderBy(g => g.Key))
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
    }
}
