using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;

// fixup <Argonia.esp> <plugins in load order...>: the nodes in shutdown.json's conditions_from_winner get the gate plus
// the winner's conditions again, which Spriggit's YAML cannot carry (see shutdown.json's _about).
static class Fixup
{
    public static void Run(string esp, string[] paths)
    {
        var plan = JsonDocument.Parse(File.ReadAllText(Path.Combine(AppContext.BaseDirectory, "shutdown.json"))).RootElement;
        var ids = plan.GetProperty("conditions_from_winner").EnumerateArray().Select(e => e.GetString()!).ToHashSet();
        var winners = Survey.Winners<IAStoryManagerNodeGetter>(Survey.Load(paths));
        var mod = SkyrimMod.CreateFromBinary(esp, SkyrimRelease.SkyrimSE, Survey.NoStrings);
        var n = 0;
        foreach (var node in mod.EnumerateMajorRecords<IAStoryManagerNode>().Where(x => ids.Contains(x.EditorID ?? "")).ToList())
        {
            var gate = node.Conditions[0].DeepCopy();
            node.Conditions.Clear();
            node.Conditions.Add(gate);
            node.Conditions.AddRange(winners[node.FormKey].rec.Conditions.Select(c => c.DeepCopy()));
            n++;
        }
        if (n != ids.Count) throw new Exception($"conditions_from_winner: {n} of {ids.Count} nodes found");
        var tmp = Path.Combine(Path.GetDirectoryName(Path.GetFullPath(esp))!, "fixup");
        Directory.CreateDirectory(tmp);
        var outp = Path.Combine(tmp, Path.GetFileName(esp));
        mod.BeginWrite.ToPath(outp).WithLoadOrder(paths.Select(p => ModKey.FromFileName(Path.GetFileName(p))).Append(mod.ModKey)).WithNoDataFolder()
            .WithExtraIncludedMasters(mod.ModHeader.MasterReferences.Select(m => m.Master).ToArray()).Write();  // keep the seeded masters
        File.Move(outp, esp, true); Directory.Delete(tmp);
        Console.WriteLine($"fixup: {n} nodes' conditions from the winners");
    }
}
