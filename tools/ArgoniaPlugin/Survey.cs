using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;

// survey <plugin paths in load order...>: the Start Game Enabled quests (load-order winners) and the story-manager tree.
static class Survey
{
    public static List<ISkyrimModGetter> Load(IEnumerable<string> paths) =>
        paths.Select(p => (ISkyrimModGetter)SkyrimMod.CreateFromBinaryOverlay(p, SkyrimRelease.SkyrimSE, NoStrings)).ToList();

    // Localized masters' strings are never read: no game text reaches our plugin (decision 0003).
    static readonly string Empty = Directory.CreateTempSubdirectory("argonia-nostrings").FullName;
    public static readonly Mutagen.Bethesda.Plugins.Binary.Parameters.BinaryReadParameters NoStrings = new()
    {
        StringsParam = new Mutagen.Bethesda.Strings.StringsReadParameters { StringsFolderOverride = Empty, BsaFolderOverride = Empty },
    };

    public static Dictionary<FormKey, (T rec, ModKey from)> Winners<T>(List<ISkyrimModGetter> mods) where T : class, IMajorRecordGetter
    {
        var w = new Dictionary<FormKey, (T, ModKey)>();
        foreach (var m in mods) foreach (var r in m.EnumerateMajorRecords<T>()) w[r.FormKey] = (r, m.ModKey);
        return w;
    }

    public static void Run(string[] paths)
    {
        var mods = Load(paths);
        var quests = Winners<IQuestGetter>(mods);
        foreach (var (fk, (q, from)) in quests.OrderBy(k => k.Key.ModKey.Name).ThenBy(k => k.Key.ID))
            if (q.Flags.HasFlag(Quest.Flag.StartGameEnabled))
                Console.WriteLine($"SGE\t{fk}\t{q.EditorID}\twinner={from}\tpri={q.Priority}");
        var nodes = Winners<IAStoryManagerNodeGetter>(mods);
        foreach (var (fk, (n, from)) in nodes.OrderBy(k => k.Key.ModKey.Name).ThenBy(k => k.Key.ID))
        {
            var parent = n.Parent.FormKey;
            var ptype = nodes.TryGetValue(parent, out var p) ? p.rec.GetType().Name.Replace("BinaryOverlay", "") : "none";
            var quest = n is IStoryManagerQuestNodeGetter qn ? string.Join(",", qn.Quests.Select(x => quests.TryGetValue(x.Quest.FormKey, out var qq) ? qq.rec.EditorID : x.Quest.FormKey.ToString())) : "";
            var ev = n is IStoryManagerEventNodeGetter en ? en.Type.ToString() : "";
            Console.WriteLine($"SMN\t{fk}\t{n.GetType().Name.Replace("BinaryOverlay", "")}\t{n.EditorID}\twinner={from}\tparent={parent}({ptype})\tconds={n.Conditions.Count}\t{ev}\t{quest}");
        }
    }
}
