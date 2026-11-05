using Mutagen.Bethesda;
using Mutagen.Bethesda.Skyrim;
static class Study2
{
    public static void Run(string path, string[] names)
    {
        using var mod = SkyrimMod.CreateFromBinaryOverlay(path, SkyrimRelease.SkyrimSE);
        foreach (var q in mod.Quests.Where(q => names.Length == 0 || names.Contains(q.EditorID)))
        {
            Console.WriteLine($"{q.EditorID} {q.FormKey} flags={q.Flags} pri={q.Priority} event={q.Event} type={q.Type} name={q.Name?.String} stages={string.Join(",", q.Stages.Select(s => s.Index))} aliases={string.Join(",", q.Aliases.Select(a => a.Name))} objectives={q.Objectives.Count} topics={mod.DialogTopics.Count(t => t.Quest.FormKey == q.FormKey)} scenes={mod.Scenes.Count(sc => sc.Quest.FormKey == q.FormKey)}");
            foreach (var t in mod.DialogTopics.Where(t => t.Quest.FormKey == q.FormKey).Take(8)) Console.WriteLine($"  topic {t.EditorID} {t.Name?.String} subtype={t.Subtype} responses={t.Responses.Count}");
            foreach (var s in q.VirtualMachineAdapter?.Scripts ?? []) Console.WriteLine($"  script {s.Name} props={string.Join(",", s.Properties.Select(p => p.Name))}");
            if (q.VirtualMachineAdapter is IQuestAdapterGetter a)
                foreach (var f in a.Fragments) Console.WriteLine($"  frag stage={f.Stage} {f.ScriptName}.{f.FragmentName}");
        }
    }
}
