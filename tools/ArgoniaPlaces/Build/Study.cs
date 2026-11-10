// study <Data dir> <plugin...>: the evidence for how a plugin lays land, navmesh and refs over a master's worldspace
// (place-studio.md, Build): per plugin, its NAVI (entries, and how many name navmeshes of its own vs a master's), its
// NAVM, LAND and CELL overrides of a master, and its placed-ref overrides of a master by how they are switched off.
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;

static class Study
{
    /// carriage <Skyrim.esm path>: the topics and INFOs of the quest DialogueCarriageSystem (name, conditions, fragment script),
    /// the evidence for a boatman's travel lines.
    public static int Carriage(string esm)
    {
        using var m = SkyrimMod.CreateFromBinaryOverlay(esm, SkyrimRelease.SkyrimSE, Survey.NoStrings);
        foreach (var g in m.Globals.Where(g => g.EditorID?.StartsWith("CarriageCost") == true || g.FormKey.ID == 0x050765)) Console.WriteLine($"global {g.EditorID} {g.FormKey.ID:X6} {(g as IGlobalFloatGetter)?.Data ?? (g as IGlobalShortGetter)?.Data}");
        var q = m.Quests.First(x => x.EditorID == "DialogueCarriageSystem");
        Console.WriteLine($"quest {q.EditorID} {q.FormKey} flags {q.Flags} scripts {string.Join(",", q.VirtualMachineAdapter?.Scripts.Select(s => s.Name) ?? [])}");
        foreach (var t in m.DialogTopics.Where(t => t.Quest.FormKey == q.FormKey))
        {
            Console.WriteLine($"topic {t.EditorID} '{t.Name?.String}' branch {t.Branch.FormKey} cat {t.Category} sub {t.Subtype} prio {t.Priority}");
            foreach (var i in t.Responses)
            {
                Console.WriteLine($"  info {i.FormKey.ID:X6} '{i.Prompt?.String}' resp '{string.Join(" / ", i.Responses.Select(r => r.Text.String))}' frag {(i.VirtualMachineAdapter as IDialogResponsesAdapterGetter)?.ScriptFragments?.FileName}");
                foreach (var c in i.Conditions)
                {
                    var d = c.Data;
                    var v = c is IConditionFloatGetter cf ? cf.ComparisonValue.ToString() : c is IConditionGlobalGetter cg ? "GLOB " + cg.ComparisonValue.FormKey : "?";
                    var arg = d switch
                    {
                        IGetInFactionConditionDataGetter gf => gf.Faction.Link.FormKey.ToString(),
                        IGetItemCountConditionDataGetter gi => gi.ItemOrList.Link.FormKey.ToString(),
                        _ => "",
                    };
                    Console.WriteLine($"    {d.GetType().Name.Replace("BinaryOverlay", "")} {arg} {d.RunOnType} {c.CompareOperator} {v} flags {c.Flags}");
                }
            }
        }
        return 0;
    }
    public static int Run(string[] a)
    {
        var data = a[0];
        foreach (var f in a[1..])
        {
            using var m = SkyrimMod.CreateFromBinaryOverlay(Path.Combine(data, f), SkyrimRelease.SkyrimSE, Survey.NoStrings);
            var me = m.ModKey;
            int naviEntries = 0, naviOwn = 0;
            foreach (var n in m.NavigationMeshInfoMaps)
                foreach (var e in n.MapInfos) { naviEntries++; if (e.NavigationMesh.FormKey.ModKey == me) naviOwn++; }
            int navmOver = 0, navmNew = 0, landOver = 0, cellOver = 0, refOver = 0, refDel = 0, refDis = 0, refLow = 0, refNew = 0, refNewPersist = 0;
            foreach (var c in m.EnumerateMajorRecords<ICellGetter>())
            {
                if (c.FormKey.ModKey != me) cellOver++;
                foreach (var n in c.NavigationMeshes) { if (n.FormKey.ModKey != me) navmOver++; else navmNew++; }
                if (c.Landscape is { } l && l.FormKey.ModKey != me) landOver++;
                foreach (var (r, persistent) in c.Temporary.Select(x => (x, false)).Concat(c.Persistent.Select(x => (x, true))))
                {
                    if (r.FormKey.ModKey == me) { refNew++; if (persistent) refNewPersist++; continue; }
                    refOver++;
                    if (r.IsDeleted) refDel++;
                    else if ((r.MajorRecordFlagsRaw & 0x800) != 0) { refDis++; if (r is IPlacedObjectGetter p && p.Placement?.Position.Z < -29000) refLow++; }
                }
            }
            Console.WriteLine($"{f}: NAVI {m.NavigationMeshInfoMaps.Count} rec, {naviEntries} NVMI ({naviOwn} own navmeshes, {naviEntries - naviOwn} a master's); NAVM {navmNew} new, {navmOver} overrides; LAND overrides {landOver}; CELL overrides {cellOver}; refs new {refNew} (persistent {refNewPersist}), overrides {refOver}: deleted {refDel}, initially disabled {refDis} (of them at z<-29000: {refLow})");
        }
        return 0;
    }
}
