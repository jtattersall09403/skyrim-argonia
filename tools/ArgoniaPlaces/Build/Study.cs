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
    /// crime <Data dir>: the guards' arrest dialogue (the evidence for a native law's Owing and its resist): every topic of
    /// the quest DialogueCrimeGuards with its INFOs (prompt, first line, the topics a choice leads to, conditions, fragment
    /// script), and the game settings whose names speak of surrender, yield or arrest.
    public static int Crime(string data)
    {
        var mods = new[] { "Skyrim.esm", "Update.esm" }.Select(f => SkyrimMod.CreateFromBinaryOverlay(Path.Combine(data, f), SkyrimRelease.SkyrimSE)).ToList();
        var cache = mods.ToImmutableLinkCache();
        var sky = mods[0];
        string Name(FormKey k) => cache.TryResolve<IMajorRecordGetter>(k, out var r) ? $"{r.EditorID ?? ""}[{k.ID:X6}]" : $"?{k.ID:X6}";
        string Txt(Func<string?> f) { try { return f() ?? ""; } catch { return "?"; } }
        var q = sky.Quests.First(x => x.EditorID == "DialogueCrimeGuards");
        Console.WriteLine($"quest {q.EditorID} {q.FormKey.ID:X6} scripts [{string.Join(",", q.VirtualMachineAdapter?.Scripts.Select(s => s.Name) ?? [])}]");
        foreach (var t in sky.DialogTopics.Where(t => t.Quest.FormKey == q.FormKey))
        {
            Console.WriteLine($"topic {t.EditorID} {t.FormKey.ID:X6} '{Txt(() => t.Name?.String)}' sub {t.Subtype} cat {t.Category} branch {Name(t.Branch.FormKey)}");
            foreach (var i in t.Responses)
            {
                var vm = i.VirtualMachineAdapter as IDialogResponsesAdapterGetter;
                Console.WriteLine($"  info {i.FormKey.ID:X6} prompt '{Txt(() => i.Prompt?.String)}' says '{Txt(() => i.Responses.FirstOrDefault()?.Text.String)}' flags {i.Flags?.Flags} "
                    + $"links [{string.Join(", ", i.LinkTo.Select(l => Name(l.FormKey)))}] frag {vm?.ScriptFragments?.FileName} start {vm?.ScriptFragments?.OnBegin?.ScriptName}.{vm?.ScriptFragments?.OnBegin?.FragmentName} end {vm?.ScriptFragments?.OnEnd?.ScriptName}.{vm?.ScriptFragments?.OnEnd?.FragmentName} "
                    + $"scripts [{string.Join(",", vm?.Scripts.Select(s => s.Name) ?? [])}]");
                foreach (var c in i.Conditions)
                {
                    var d = c.Data;
                    var arg = string.Join(",", d.GetType().GetProperties().Where(p => p.Name is not ("RunOnType" or "Reference" or "Unknown3" or "UseAliases" or "UsePackageData" or "Function")).Select(p => p.GetValue(d)).OfType<IFormLinkContainerGetter>().SelectMany(x => x.EnumerateFormLinks()).Select(l => Name(l.FormKey)));
                    var v = c is IConditionFloatGetter cf ? cf.ComparisonValue.ToString() : c is IConditionGlobalGetter cg ? Name(cg.ComparisonValue.FormKey) : "?";
                    Console.WriteLine($"    {d.GetType().Name.Replace("BinaryOverlay", "").Replace("ConditionData", "")}({arg}) {d.RunOnType} {c.CompareOperator} {v} {c.Flags}");
                }
            }
        }
        // a yield and its acceptance: every topic of those subtypes, its quest, and its INFOs' conditions
        foreach (var t in sky.DialogTopics.Where(t => t.Subtype is DialogTopic.SubtypeEnum.Yield or DialogTopic.SubtypeEnum.AcceptYield))
        {
            Console.WriteLine($"yield topic {t.EditorID} {t.FormKey.ID:X6} sub {t.Subtype} quest {Name(t.Quest.FormKey)} infos {t.Responses.Count}");
            foreach (var i in t.Responses.Take(6))
                Console.WriteLine($"  info {i.FormKey.ID:X6} [{string.Join("; ", i.Conditions.Select(c => $"{c.Data.GetType().Name.Replace("BinaryOverlay", "").Replace("ConditionData", "")}({string.Join(",", c.Data.GetType().GetProperties().Select(p => p.GetValue(c.Data)).OfType<IFormLinkContainerGetter>().SelectMany(x => x.EnumerateFormLinks()).Select(l => Name(l.FormKey)))}) {c.CompareOperator} {(c as IConditionFloatGetter)?.ComparisonValue}"))}]");
        }
        foreach (var g in mods.SelectMany(m => m.GameSettings).Where(g => System.Text.RegularExpressions.Regex.IsMatch(g.EditorID ?? "", "Surrender|Yield|Arrest|Jail|Prison", System.Text.RegularExpressions.RegexOptions.IgnoreCase)))
            Console.WriteLine($"gmst {g.EditorID} = {g switch { IGameSettingFloatGetter f => f.Data?.ToString(), IGameSettingIntGetter n => n.Data?.ToString(), IGameSettingBoolGetter b => b.Data?.ToString(), IGameSettingStringGetter s => Txt(() => s.Data?.String), _ => "?" }}");
        foreach (var g in sky.Globals.Where(g => (g.EditorID ?? "").StartsWith("Crime")))
            Console.WriteLine($"global {g.EditorID} = {(g as IGlobalFloatGetter)?.Data ?? (g as IGlobalShortGetter)?.Data ?? (g as IGlobalIntGetter)?.Data}");
        return 0;
    }
    /// jail <Data dir> <faction edid...>: how Skyrim.esm gives a hold's crime faction its jail (the evidence for a place's
    /// jail): the faction's crime fields and values; each marker and container ref it names (base, cell, position,
    /// flags, owner, linked refs, the base's contents and respawn flag); the jail cell's beds, doors and owner; and the
    /// placed refs in Skyrim.esm whose base is the prison marker or that a jail's door links to.
    public static int Jail(string data, string[] edids)
    {
        var files = new[] { "Skyrim.esm", "Update.esm" };
        var mods = files.Select(f => SkyrimMod.CreateFromBinaryOverlay(Path.Combine(data, f), SkyrimRelease.SkyrimSE, Survey.NoStrings)).ToList();
        var cache = mods.ToImmutableLinkCache();
        var sky = mods[0];
        var cellOf = new Dictionary<FormKey, ICellGetter>();
        void Index(ICellGetter c) { foreach (var r in c.Persistent.Concat(c.Temporary)) cellOf[r.FormKey] = c; }
        foreach (var c in C.Interiors(sky)) Index(c);
        foreach (var ws in sky.Worldspaces) { if (ws.TopCell is { } tc) Index(tc); foreach (var c in C.Cells(ws)) Index(c); }
        string Name(FormKey k) => cache.TryResolve<IMajorRecordGetter>(k, out var r) ? $"{r.EditorID ?? ""}[{C.Sig(r)} {k.ID:X6}]" : $"?{k.ID:X6}";
        void Ref(string what, FormKey k, bool follow = true)
        {
            if (k.IsNull) { Console.WriteLine($"  {what}: none"); return; }
            if (!cache.TryResolve<IPlacedObjectGetter>(k, out var r)) { Console.WriteLine($"  {what}: {Name(k)} (not a placed object)"); return; }
            var c = cellOf.GetValueOrDefault(k);
            Console.WriteLine($"  {what}: {k.ID:X6} base {Name(r.Base.FormKey)} cell {c?.EditorID}{(c?.Grid is { } g ? $" ({g.Point.X},{g.Point.Y})" : "")} interior={c?.Flags.HasFlag(Cell.Flag.IsInteriorCell)} pos {r.Placement?.Position} flags 0x{r.MajorRecordFlagsRaw:X} owner {Name(r.Owner.FormKey)} linked [{string.Join(", ", r.LinkedReferences.Select(l => Name(l.Reference.FormKey) + "/" + Name(l.KeywordOrReference.FormKey)))}] loctypes [{string.Join(",", r.LocationRefTypes?.Select(x => Name(x.FormKey)) ?? [])}]");
            if (follow && r.TeleportDestination is { } tp && cache.TryResolve<IPlacedObjectGetter>(tp.Door.FormKey, out var into))
            {
                Console.WriteLine($"    teleport -> {tp.Door.FormKey.ID:X6} base {Name(into.Base.FormKey)} pos {tp.Position} (the marker's own {into.Placement?.Position}); its teleport back -> {(into.TeleportDestination is { } bk ? $"{bk.Door.FormKey.ID:X6} at {bk.Position}" : "none")}");
                Ref("  the jail marker inside", tp.Door.FormKey, false);
            }
            if (cache.TryResolve<IContainerGetter>(r.Base.FormKey, out var cb))
                Console.WriteLine($"    container flags {cb.Flags} items {cb.Items?.Count ?? 0} scripts [{string.Join(",", cb.VirtualMachineAdapter?.Scripts.Select(s => s.Name) ?? [])}] ref scripts [{string.Join(",", r.VirtualMachineAdapter?.Scripts.Select(s => s.Name) ?? [])}]");
            if (c != null && c.Flags.HasFlag(Cell.Flag.IsInteriorCell))
            {
                var all = c.Persistent.Concat(c.Temporary).OfType<IPlacedObjectGetter>().ToList();
                var beds = all.Where(x => cache.TryResolve<IFurnitureGetter>(x.Base.FormKey, out var f) && (f.EditorID ?? "").Contains("Bed", StringComparison.OrdinalIgnoreCase)).ToList();
                var doors = all.Where(x => cache.TryResolve<IDoorGetter>(x.Base.FormKey, out _)).ToList();
                Console.WriteLine($"    cell {c.EditorID} owner {Name(c.Owner.FormKey)} loc {Name(c.Location.FormKey)} refs {all.Count} beds {beds.Count} doors {doors.Count}");
                foreach (var b in beds) Console.WriteLine($"      bed {b.FormKey.ID:X6} {Name(b.Base.FormKey)} pos {b.Placement?.Position} owner {Name(b.Owner.FormKey)} dist {Dist(b, r):F0}");
                foreach (var d in doors) Console.WriteLine($"      door {d.FormKey.ID:X6} {Name(d.Base.FormKey)} pos {d.Placement?.Position} lock {(d.Lock is { } l ? $"{l.Level} key {Name(l.Key.FormKey)}" : "none")} owner {Name(d.Owner.FormKey)} load {(d.TeleportDestination is { } t ? Name(t.Door.FormKey) : "-")} dist {Dist(d, r):F0}");
            }
        }
        static float Dist(IPlacedObjectGetter a, IPlacedObjectGetter b) => a.Placement is { } p && b.Placement is { } q ? (p.Position - q.Position).Magnitude : -1;
        // every crime-tracking faction: does it arrest, and has it a jail (the evidence for a jail-less faction)
        if (edids.Length == 1 && edids[0] == "all")
        {
            foreach (var m in mods.AsEnumerable().Reverse().Concat(new[] { "Dawnguard.esm", "Dragonborn.esm" }.Select(f => SkyrimMod.CreateFromBinaryOverlay(Path.Combine(data, f), SkyrimRelease.SkyrimSE, Survey.NoStrings))))
                foreach (var f in m.Factions.Where(x => x.Flags.HasFlag(Faction.FactionFlag.TrackCrime)))
                    Console.WriteLine($"crime {m.ModKey.FileName} {f.EditorID} arrest {f.CrimeValues?.Arrest} aos {f.CrimeValues?.AttackOnSight} jail {(f.ExteriorJailMarker.IsNull ? "none" : "set")} stol {(f.StolenGoodsContainer.IsNull ? "none" : "set")} flags {f.Flags}");
            edids = Array.Empty<string>();
        }
        foreach (var e in edids)
        {
            var f = mods.AsEnumerable().Reverse().SelectMany(m => m.Factions).FirstOrDefault(x => x.EditorID == e);
            if (f == null) { Console.WriteLine($"{e}: no faction"); continue; }
            var cv = f.CrimeValues;
            Console.WriteLine($"faction {e} {f.FormKey.ID:X6} flags {f.Flags} jail outfit {Name(f.JailOutfit.FormKey)} shared crime list {Name(f.SharedCrimeFactionList.FormKey)}");
            if (cv != null) Console.WriteLine($"  crime: arrest {cv.Arrest} aos {cv.AttackOnSight} murder {cv.Murder} assault {cv.Assault} trespass {cv.Trespass} pickpocket {cv.Pickpocket} steal {cv.StealMult} escape {cv.Escape} werewolf {cv.Werewolf}");
            Ref("JAIL exterior jail marker", f.ExteriorJailMarker.FormKey);
            Ref("WAIT follower wait marker", f.FollowerWaitMarker.FormKey);
            Ref("STOL stolen goods container", f.StolenGoodsContainer.FormKey);
            Ref("PLCN player inventory container", f.PlayerInventoryContainer.FormKey);
        }
        // the in-jail marker: refs whose base names a prison marker, and any ref with a jail location ref type
        foreach (var r in cellOf.Keys.Select(k => cache.TryResolve<IPlacedObjectGetter>(k, out var x) ? x : null).OfType<IPlacedObjectGetter>())
        {
            var bn = cache.TryResolve<IMajorRecordGetter>(r.Base.FormKey, out var b) ? b.EditorID ?? "" : "";
            var lt = r.LocationRefTypes?.Select(x => Name(x.FormKey)).ToList() ?? new();
            if (bn.Contains("Prison", StringComparison.OrdinalIgnoreCase) || lt.Any(x => x.Contains("Jail", StringComparison.OrdinalIgnoreCase) || x.Contains("Prison", StringComparison.OrdinalIgnoreCase)))
                Console.WriteLine($"marker {r.FormKey.ID:X6} base {Name(r.Base.FormKey)} cell {cellOf[r.FormKey].EditorID} pos {r.Placement?.Position} flags 0x{r.MajorRecordFlagsRaw:X} loctypes [{string.Join(",", lt)}] linked [{string.Join(", ", r.LinkedReferences.Select(l => Name(l.Reference.FormKey)))}]");
        }
        // what the guards' arrest lines need: the distinct conditions over the INFOs of the crime dialogue quests
        foreach (var qn in new[] { "DialogueCrimeGuards", "DialogueGuardsCrime", "DGIntimidateQuest" })
        {
            var q = sky.Quests.FirstOrDefault(x => x.EditorID == qn);
            if (q == null) continue;
            Console.WriteLine($"quest {qn} {q.FormKey.ID:X6} flags {q.Flags} conditions [{string.Join("; ", q.DialogConditions.Select(Cond))}]");
            var seen = new Dictionary<string, int>();
            foreach (var t in sky.DialogTopics.Where(t => t.Quest.FormKey == q.FormKey))
                foreach (var i in t.Responses)
                    foreach (var c in i.Conditions) { var k = $"{t.Subtype}: {Cond(c)}"; seen[k] = seen.GetValueOrDefault(k) + 1; }
            foreach (var kv in seen.OrderByDescending(kv => kv.Value).Take(40)) Console.WriteLine($"  {kv.Value} x {kv.Key}");
            // the lines that send the player to jail: their topic, prompt, conditions and fragment script
            foreach (var t in sky.DialogTopics.Where(t => t.Quest.FormKey == q.FormKey))
                foreach (var i in t.Responses.Where(i => (i.Prompt?.String ?? "").Contains("jail", StringComparison.OrdinalIgnoreCase)
                    || (i.VirtualMachineAdapter as IDialogResponsesAdapterGetter)?.ScriptFragments?.FileName is { } fn && fn.Length > 0 && t.EditorID?.Contains("Jail", StringComparison.OrdinalIgnoreCase) == true))
                    Console.WriteLine($"  jail line: topic {t.EditorID} '{t.Name?.String}' info {i.FormKey.ID:X6} prompt '{i.Prompt?.String}' frag {(i.VirtualMachineAdapter as IDialogResponsesAdapterGetter)?.ScriptFragments?.FileName} conditions [{string.Join("; ", i.Conditions.Select(Cond))}]");
        }
        string Cond(IConditionGetter c)
        {
            var d = c.Data;
            var arg = string.Join(",", d.GetType().GetProperties().Where(p => p.Name is not ("RunOnType" or "Reference" or "Unknown3" or "UseAliases" or "UsePackageData" or "Function")).Select(p => p.GetValue(d)).OfType<IFormLinkContainerGetter>().SelectMany(x => x.EnumerateFormLinks()).Select(l => Name(l.FormKey)));
            var v = c is IConditionFloatGetter cf ? cf.ComparisonValue.ToString() : c is IConditionGlobalGetter cg ? Name(cg.ComparisonValue.FormKey) : "?";
            return $"{d.GetType().Name.Replace("BinaryOverlay", "").Replace("ConditionData", "")}({arg}) {d.RunOnType} {c.CompareOperator} {v}";
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
