// PERK: the intermediate's perk records (tools/argonia_world/hooks_records.py) -> Mutagen. Entry-point effects with
// AddActivateChoice, tab-1 conditions, the script flags and the perk fragments. No choices here: every value
// arrives resolved; an unsupported entry point, function or condition is an InvalidDataException.
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;

namespace ArgoniaGen;

static class PerkRecords
{
    const SkyrimRelease Rel = SkyrimRelease.SkyrimSE;

    static string S(JsonElement e, string k) => e.GetProperty(k).GetString() ?? throw new InvalidDataException($"{k} is null");
    static int I(JsonElement e, string k, int d = 0) => e.TryGetProperty(k, out var v) ? v.GetInt32() : d;
    static bool B(JsonElement e, string k) => e.TryGetProperty(k, out var v) && v.GetBoolean();
    static IEnumerable<JsonElement> A(JsonElement e, string k) =>
        e.TryGetProperty(k, out var v) ? v.EnumerateArray() : Enumerable.Empty<JsonElement>();

    public static void Write(SkyrimMod mod, JsonElement r)
    {
        var edid = S(r, "edid");
        var p = new Perk(FormKey.Factory(S(r, "formKey")), Rel)
        {
            EditorID = edid,
            Name = r.TryGetProperty("name", out var n) && n.GetString() is { Length: > 0 } nm ? new TranslatedString(Language.English, nm) : null,
            Description = new TranslatedString(Language.English, r.TryGetProperty("description", out var d) ? d.GetString() ?? "" : ""),
            Hidden = B(r, "hidden"), Playable = B(r, "playable"), Trait = B(r, "trait"),
            Level = (byte)I(r, "level"), NumRanks = (byte)I(r, "ranks", 1),
        };
        foreach (var e in A(r, "effects")) p.Effects.Add(Effect(edid, e));
        if (r.TryGetProperty("fragments", out var frag))
        {
            var name = S(frag, "script");
            var fr = new PerkScriptFragments { FileName = name };
            foreach (var f in A(frag, "entries"))
                fr.Fragments.Add(new IndexedScriptFragment
                {
                    FragmentIndex = (ushort)I(f, "index"), Unknown = 0, Unknown2 = 1,
                    ScriptName = name, FragmentName = S(f, "name"),
                });
            p.VirtualMachineAdapter = new PerkAdapter { ScriptFragments = fr };
        }
        mod.Perks.Add(p);
    }

    static PerkEntryPointAddActivateChoice Effect(string edid, JsonElement e)
    {
        var ep = S(e, "entryPoint");
        var fn = S(e, "function");
        if (ep != "Activate") throw new InvalidDataException($"{edid}: entry point {ep} not supported yet");
        if (fn != "AddActivateChoice") throw new InvalidDataException($"{edid}: perk function {fn} not supported yet");
        long fl = 0;
        foreach (var f in A(e, "flags")) fl |= (long)Enum.Parse<PerkScriptFlag.Flag>(f.GetString()!);
        var eff = new PerkEntryPointAddActivateChoice
        {
            EntryPoint = APerkEntryPointEffect.EntryType.Activate,
            Rank = (byte)I(e, "rank"), Priority = (byte)I(e, "priority"),
            PerkConditionTabCount = (byte)I(e, "tabCount"),
            ButtonLabel = S(e, "buttonLabel"),
            Flags = new PerkScriptFlag { Flags = (PerkScriptFlag.Flag)fl, FragmentIndex = (ushort)I(e, "fragment") },
        };
        foreach (var c in A(e, "conditions"))
        {
            var cf = S(c, "function");
            if (cf != "HasKeyword") throw new InvalidDataException($"{edid}: condition function {cf} not supported yet");
            var data = new HasKeywordConditionData { RunOnType = Condition.RunOnType.Subject };
            data.Keyword.Link.SetTo(FormKey.Factory(S(c, "keyword")));
            eff.Conditions.Add(new PerkCondition
            {
                RunOnTabIndex = (byte)I(c, "tab"),
                Conditions =
                {
                    new ConditionFloat
                    {
                        CompareOperator = Enum.Parse<CompareOperator>(S(c, "op")),
                        ComparisonValue = c.GetProperty("value").GetSingle(),
                        Data = data,
                    },
                },
            });
        }
        return eff;
    }
}
