// QUST: the intermediate's quest records (tools/argonia_world/quest_gen.py; the quarantine's start quest in
// intermediate.py) -> Mutagen. Stages with their log entries, objectives with their text and no targets (no
// markers: target data is never written, and a target in the input is an error), reference aliases, the attached
// scripts and the begin fragments bound to their stages. No choices here: every value arrives resolved.
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Strings;
using Mutagen.Bethesda.Skyrim;

namespace ArgoniaGen;

static class QuestRecords
{
    const SkyrimRelease Rel = SkyrimRelease.SkyrimSE;

    static string S(JsonElement e, string k) => e.GetProperty(k).GetString() ?? throw new InvalidDataException($"{k} is null");
    static string? Os(JsonElement e, string k) => e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() : null;
    static int I(JsonElement e, string k, int d = 0) => e.TryGetProperty(k, out var v) ? v.GetInt32() : d;
    static IEnumerable<JsonElement> A(JsonElement e, string k) =>
        e.TryGetProperty(k, out var v) ? v.EnumerateArray() : Enumerable.Empty<JsonElement>();
    static T Flags<T>(JsonElement r, string k) where T : struct, Enum
    {
        long v = 0;
        foreach (var f in A(r, k)) v |= Convert.ToInt64(Enum.Parse<T>(f.GetString()!));
        return (T)Enum.ToObject(typeof(T), v);
    }
    static TranslatedString Text(string s) => new(Language.English, s);

    public static void Write(SkyrimMod mod, JsonElement r)
    {
        var edid = S(r, "edid");
        var q = new Quest(FormKey.Factory(S(r, "formKey")), Rel)
        {
            EditorID = edid,
            Name = Os(r, "name") is { } n ? Text(n) : null,
            Flags = Flags<Quest.Flag>(r, "flags"),
            Priority = (byte)I(r, "priority"),
            Type = Enum.Parse<Quest.TypeEnum>(Os(r, "questType") ?? "None"),
        };
        foreach (var c in A(r, "eventConditions")) q.EventConditions.Add(Condition(c));
        var fragStages = r.TryGetProperty("fragments", out var fs0) ? A(fs0, "stages").Select(i => (ushort)i.GetInt32()).ToHashSet() : new HashSet<ushort>();
        foreach (var st in A(r, "stages"))
        {
            var stage = new QuestStage { Index = (ushort)I(st, "index"), Flags = Flags<QuestStage.Flag>(st, "flags") };
            foreach (var e in A(st, "log"))
                stage.LogEntries.Add(new QuestLogEntry { Flags = Flags<QuestLogEntry.Flag>(e, "flags"), Entry = Text(S(e, "text")) });
            // A stage's fragment hangs on one of its log entries (StageIndex), as the CK writes every stage: a stage with
            // none runs no fragment (game-9: LF83's stage-0 WatchQuest never ran, so nothing stepped the quest).
            if (stage.LogEntries.Count == 0 && fragStages.Contains(stage.Index)) stage.LogEntries.Add(new QuestLogEntry { Flags = 0, Entry = Text("") });
            q.Stages.Add(stage);
        }
        foreach (var o in A(r, "objectives"))
        {
            if (o.TryGetProperty("targets", out _))
                throw new InvalidDataException($"{edid} objective {I(o, "index")}: target data (no markers, old 0137)");
            q.Objectives.Add(new QuestObjective { Index = (ushort)I(o, "index"), DisplayText = Text(S(o, "text")) });
        }
        foreach (var a in A(r, "aliases"))
        {
            var al = new QuestAlias
            {
                ID = (uint)I(a, "id"), Type = QuestAlias.TypeEnum.Reference, Name = S(a, "name"),
                Flags = Flags<QuestAlias.Flag>(a, "flags"),
            };
            if (a.TryGetProperty("forcedRef", out var fr))  // the reference a built place lays (place_build.placed)
                al.ForcedReference.SetTo(FormKey.Factory(fr.GetString()!));
            q.Aliases.Add(al);
        }
        if (q.Aliases.Count > 0) q.NextAliasID = (uint)q.Aliases.Count;

        var scripts = A(r, "scripts").ToList();
        var hasFragments = r.TryGetProperty("fragments", out var frag);
        if (scripts.Count > 0 || hasFragments)
        {
            var vm = new QuestAdapter();
            foreach (var s in scripts) vm.Scripts.Add(Script(s));
            if (hasFragments)
            {
                var name = S(frag, "script");
                vm.FileName = name;
                foreach (var i in A(frag, "stages"))
                    vm.Fragments.Add(new QuestScriptFragment
                    {
                        Stage = (ushort)i.GetInt32(), StageIndex = 0, Unknown2 = 1,
                        ScriptName = name, FragmentName = $"Fragment_{i.GetInt32()}",
                    });
            }
            q.VirtualMachineAdapter = vm;
        }
        mod.Quests.Add(q);
    }

    static ScriptEntry Script(JsonElement s)
    {
        var e = new ScriptEntry { Name = S(s, "name") };
        foreach (var p in A(s, "properties"))
        {
            if (Os(p, "object") is { } obj)
                e.Properties.Add(new ScriptObjectProperty
                {
                    Name = S(p, "name"), Flags = ScriptProperty.Flag.Edited,
                    Object = new FormLink<ISkyrimMajorRecordGetter>(FormKey.Factory(obj)),
                });
            else throw new InvalidDataException($"script {e.Name}: property {S(p, "name")} kind not supported yet");
        }
        return e;
    }

    static Condition Condition(JsonElement c)
    {
        var fn = S(c, "function");
        ConditionData data = fn switch
        {
            "GetGlobalValue" => Global(c),
            _ => throw new InvalidDataException($"condition function {fn} not supported yet"),
        };
        return new ConditionFloat
        {
            CompareOperator = Enum.Parse<CompareOperator>(S(c, "op")),
            ComparisonValue = c.TryGetProperty("value", out var v) ? v.GetSingle() : 0,
            Data = data,
        };
    }

    static ConditionData Global(JsonElement c)
    {
        var d = new GetGlobalValueConditionData();
        d.Global.Link.SetTo(FormKey.Factory(S(c, "global")));
        return d;
    }
}
