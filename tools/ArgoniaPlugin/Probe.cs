using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
// probe <plugin> <node formkey>: a node's conditions as Mutagen reads them.
static class Probe
{
    public static void Run(string path, string key)
    {
        using var mod = SkyrimMod.CreateFromBinaryOverlay(path, SkyrimRelease.SkyrimSE, Survey.NoStrings);
        var n = mod.EnumerateMajorRecords<IAStoryManagerNodeGetter>().First(x => x.FormKey == FormKey.Factory(key));
        foreach (var c in n.Conditions) Console.WriteLine($"{c.GetType().Name} {c.Flags} {c.Data.GetType().Name} {(c.Data as IGetVMQuestVariableConditionDataGetter)?.VariableName}");
        var full = SkyrimMod.CreateFromBinary(path, SkyrimRelease.SkyrimSE, Survey.NoStrings);
        var m = full.EnumerateMajorRecords<IAStoryManagerNodeGetter>().First(x => x.FormKey == FormKey.Factory(key));
        Console.WriteLine($"full read: {m.Conditions.Count} conditions; deep copy of overlay: {((IAStoryManagerNode)n.DeepCopy()).Conditions.Count}");
    }
}
