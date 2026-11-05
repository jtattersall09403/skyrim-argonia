using Mutagen.Bethesda;
using Mutagen.Bethesda.Skyrim;
static class Study2
{
    public static void Run(string path, string[] names)
    {
        using var mod = SkyrimMod.CreateFromBinaryOverlay(path, SkyrimRelease.SkyrimSE);
        foreach (var q in mod.Quests.Where(q => names.Length == 0 || names.Contains(q.EditorID)))
        {
            Console.WriteLine($"{q.EditorID} {q.FormKey} flags={q.Flags} pri={q.Priority} event={q.Event}");
            foreach (var s in q.VirtualMachineAdapter?.Scripts ?? []) Console.WriteLine($"  script {s.Name} props={string.Join(",", s.Properties.Select(p => p.Name))}");
            if (q.VirtualMachineAdapter is IQuestAdapterGetter a)
                foreach (var f in a.Fragments) Console.WriteLine($"  frag stage={f.Stage} {f.ScriptName}.{f.FragmentName}");
        }
    }
}
