// PERK: the intermediate's perk records (tools/argonia_world/hooks_records.py) -> Mutagen. Entry-point effects with
// AddActivateChoice, tab-1 conditions, the script flags and the perk fragments. No choices here: every value
// arrives resolved; an unsupported entry point, function or condition is an InvalidDataException.
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Binary.Parameters;
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

    static readonly Dictionary<string, ISkyrimModDisposableGetter> masters = new(StringComparer.OrdinalIgnoreCase);

    // The master's string tables, extracted loose into out/strings-cache (found upward from the binary, else
    // $ARGONIA_STRINGS): a copied perk's entry labels are localized strings the overlay must be able to read.
    // Mutagen also asks for a Windows-style plugin listing (%LocalAppData%/Skyrim Special Edition/Plugins.txt) to find
    // archives; on Linux it wants $LocalAppData, so an empty listing is made in a scratch directory and named.
    static BinaryReadParameters StringsParams()
    {
        var dir = Environment.GetEnvironmentVariable("ARGONIA_STRINGS");
        for (var d = new DirectoryInfo(AppContext.BaseDirectory); string.IsNullOrEmpty(dir) && d != null; d = d.Parent)
            if (Directory.Exists(Path.Combine(d.FullName, "out", "strings-cache"))) dir = Path.Combine(d.FullName, "out", "strings-cache");
        if (string.IsNullOrEmpty(dir)) throw new InvalidDataException("no out/strings-cache (extract the official string tables) and no $ARGONIA_STRINGS");
        if (string.IsNullOrEmpty(Environment.GetEnvironmentVariable("LocalAppData")))
        {
            var lad = Path.Combine(Path.GetTempPath(), "argonia-localappdata");
            Directory.CreateDirectory(Path.Combine(lad, "Skyrim Special Edition"));
            File.WriteAllText(Path.Combine(lad, "Skyrim Special Edition", "Plugins.txt"), "");
            Environment.SetEnvironmentVariable("LocalAppData", lad);
        }
        return new BinaryReadParameters { StringsParam = new StringsReadParameters { StringsFolderOverride = new Noggog.DirectoryPath(dir), TargetLanguage = Language.English } };
    }

    // 1.12 §4 (decision 0012): a master's skill-tree perk overridden with our name and description (perk_text), the
    // record otherwise copied whole from the load order. The master's own strings live in its string tables, which are
    // not read here, so the copy leaves Name and Description out and sets ours.
    public static void Override(SkyrimMod mod, JsonElement r, string data) =>
        Override(mod, S(r, "formKey"), S(r, "name"), S(r, "description"), data);

    public static void Override(SkyrimMod mod, string formKey, string name, string description, string data)
    {
        var key = FormKey.Factory(formKey);
        var file = key.ModKey.FileName.String;
        if (!masters.TryGetValue(file, out var master))
            masters[file] = master = SkyrimMod.CreateFromBinaryOverlay(Path.Combine(data, file), Rel, StringsParams());
        if (!master.Perks.TryGetValue(key, out var src)) throw new InvalidDataException($"no PERK {key} in {file}");
        var p = (Perk)src.DeepCopy(new Perk.TranslationMask(true) { Name = false, Description = false });
        p.Name = new TranslatedString(Language.English, name);
        p.Description = new TranslatedString(Language.English, description);
        mod.Perks.Add(p);
    }

    // perks: the perk_text table + the player's masters -> ArgoniaPerks.esp (installer/steps/perk-text.md, 0014).
    // A derived plugin made on the player's machine: it carries the masters' PERK records, so it is never committed.
    public static int Plugin(string jsonl, string data, string outPath)
    {
        var mod = new SkyrimMod(ModKey.FromFileName(Path.GetFileName(outPath)), Rel);
        mod.ModHeader.Author = "Elder Souls: Argonia (derived at install)";
        mod.ModHeader.Description = "The skill-tree perks' names and descriptions in Argonia's words. Made on your machine; do not share.";
        var n = 0;
        foreach (var line in File.ReadLines(jsonl).Where(l => l.Trim().Length > 0))
        {
            using var doc = JsonDocument.Parse(line);
            var r = doc.RootElement;
            Override(mod, S(r, "formkey"), S(r, "name"), S(r, "description"), data);
            n++;
        }
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(outPath))!);
        // masters listed in load order (Skyrim.esm first), as the Creation Kit writes them
        var order = new[] { "Skyrim.esm", "Dawnguard.esm" }.Select(f => ModKey.FromFileName(f)).Append(mod.ModKey);
        mod.BeginWrite.ToPath(outPath).WithLoadOrder(order).WithDataFolder(data).Write();
        Console.WriteLine($"perks: {n} overrides -> {outPath}");
        return 0;
    }

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
            // The fragment script is also the perk's attached script, as the CK writes it: without the Scripts entry
            // the engine binds no ARG_PRKF instance and the entry point's fragment never runs (game-9: E on the camp
            // spot and on a speaker ran nothing with the .pex laid; no bind line in Papyrus.0.log).
            var vm = new PerkAdapter { ScriptFragments = fr };
            var entry = new ScriptEntry { Name = name };
            // Object properties of the fragment script (the closed road's MESG): name -> a record of ours or a master's.
            foreach (var pr in A(frag, "properties"))
                entry.Properties.Add(new ScriptObjectProperty
                {
                    Name = S(pr, "name"), Flags = ScriptProperty.Flag.Edited,
                    Object = new FormLink<ISkyrimMajorRecordGetter>(FormKey.Factory(S(pr, "object"))),
                });
            vm.Scripts.Add(entry);
            p.VirtualMachineAdapter = vm;
        }
        mod.Perks.Add(p);
    }

    static APerkEntryPointEffect Effect(string edid, JsonElement e) => S(e, "function") switch
    {
        "AddActivateChoice" => ActivateChoice(edid, e),
        "MultiplyOnePlusAVMult" or "MultiplyAVMult" => ModifyActorValue(edid, e),
        "MultiplyValue" => ModifyValue(edid, e),
        var fn => throw new InvalidDataException($"{edid}: perk function {fn} not supported yet"),
    };

    // A modify-value entry point (1.6 combat wiring): the entry point, its condition tab count and the value.
    static APerkEntryPointEffect.EntryType Entry(string edid, JsonElement e) =>
        Enum.TryParse<APerkEntryPointEffect.EntryType>(S(e, "entryPoint"), out var t) && t != APerkEntryPointEffect.EntryType.Activate
            ? t : throw new InvalidDataException($"{edid}: entry point {S(e, "entryPoint")} is not a value entry point");

    static PerkEntryPointModifyActorValue ModifyActorValue(string edid, JsonElement e)
    {
        var eff = new PerkEntryPointModifyActorValue
        {
            EntryPoint = Entry(edid, e), Rank = (byte)I(e, "rank"), Priority = (byte)I(e, "priority"),
            PerkConditionTabCount = (byte)I(e, "tabCount"),
            ActorValue = Enum.Parse<ActorValue>(S(e, "actorValue")),
            Modification = Enum.Parse<PerkEntryPointModifyActorValue.ModificationType>(S(e, "function")),
            Value = e.GetProperty("value").GetSingle(),
        };
        foreach (var c in A(e, "conditions")) eff.Conditions.Add(Cond(edid, c));
        return eff;
    }

    static PerkEntryPointModifyValue ModifyValue(string edid, JsonElement e)
    {
        var eff = new PerkEntryPointModifyValue
        {
            EntryPoint = Entry(edid, e), Rank = (byte)I(e, "rank"), Priority = (byte)I(e, "priority"),
            PerkConditionTabCount = (byte)I(e, "tabCount"),
            Modification = PerkEntryPointModifyValue.ModificationType.Multiply,
            Value = e.GetProperty("value").GetSingle(),
        };
        foreach (var c in A(e, "conditions")) eff.Conditions.Add(Cond(edid, c));
        return eff;
    }

    static PerkEntryPointAddActivateChoice ActivateChoice(string edid, JsonElement e)
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
        foreach (var c in A(e, "conditions")) eff.Conditions.Add(Cond(edid, c));
        return eff;
    }

    static PerkCondition Cond(string edid, JsonElement c)
    {
        var cf = S(c, "function");
        if (cf != "HasKeyword") throw new InvalidDataException($"{edid}: condition function {cf} not supported yet");
        var data = new HasKeywordConditionData { RunOnType = Condition.RunOnType.Subject };
        data.Keyword.Link.SetTo(FormKey.Factory(S(c, "keyword")));
        return new PerkCondition
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
        };
    }
}
