using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;

static class Study
{
    // study <plugin>: every record the plugin overrides from another master, with its type and editor id.
    public static void Run(string path)
    {
        using var mod = SkyrimMod.CreateFromBinaryOverlay(path, SkyrimRelease.SkyrimSE);
        Console.WriteLine($"masters: {string.Join(", ", mod.ModHeader.MasterReferences.Select(m => m.Master))}");
        foreach (var r in mod.EnumerateMajorRecords())
        {
            if (r.FormKey.ModKey == mod.ModKey) continue;
            var extra = r is IQuestGetter q ? $" flags={q.Flags} stages={q.Stages.Count} vmad={(q.VirtualMachineAdapter?.Scripts.Count ?? 0)}" : "";
            Console.WriteLine($"{r.FormKey} {r.GetType().Name.Replace("BinaryOverlay", "")} {r.EditorID}{extra}");
        }
        foreach (var q in mod.Quests.Where(q => q.FormKey.ModKey == mod.ModKey && q.Flags.HasFlag(Quest.Flag.StartGameEnabled)))
            Console.WriteLine($"own SGE quest: {q.EditorID} {q.FormKey}");
    }
}
