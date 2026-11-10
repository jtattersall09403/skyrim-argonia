// dump <esp> <world.esm> <out.json>: the built place layer read back for tools/places/check.py, the way xEdit would
// show it: masters, record counts by type, every link that resolves nowhere, and the rows the checks read (refs
// with their bases and a container's contents, overrides of the world's refs, LAND, actors, packages, factions,
// classes, levelled lists reachable from ours, each actor base's inventory, outfit items and death item). Navmesh is read by check.py from the plugin's bytes (tools/navmesh/esm.py).
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Aspects;
using Mutagen.Bethesda.Plugins.Cache;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;

static class Dump
{
    public static int Run(string esp, string worldEsm, string outPath)
    {
        var mod = SkyrimMod.CreateFromBinaryOverlay(esp, C.Rel, Survey.NoStrings);
        var world = C.Open(worldEsm);
        var lo = Write.Masters.Select(m => C.Open(m)).Append(world).Append(mod).ToList();
        var cache = lo.ToImmutableLinkCache();
        var me = mod.ModKey;
        var counts = new SortedDictionary<string, int>();
        void Count(string k) => counts[k] = counts.GetValueOrDefault(k) + 1;
        var unresolved = new List<string>();
        var PlayerRef = new FormKey(ModKey.FromFileName("Skyrim.esm"), 0x14);
        foreach (var r in mod.EnumerateMajorRecords())
        {
            Count(r.GetType().Name.Replace("BinaryOverlay", "") + (r.FormKey.ModKey == me ? "" : " (override)"));
            foreach (var l in r.EnumerateFormLinks())
                // PlayerRef (Skyrim.esm:000014) is made by the engine, not a record: vanilla enable parents name it
                if (!l.FormKey.IsNull && l.FormKey != PlayerRef && !cache.TryResolve(l.FormKey, l.Type, out _))
                    if (unresolved.Count < 200) unresolved.Add($"{C.Key(r.FormKey)} -> {C.Key(l.FormKey)} <{l.Type.Name}>");
        }
        var refs = new List<object>();
        var overrides = new List<object>();
        var land = new List<object>();
        var actors = new List<object>();
        var cellsOut = new List<object>();
        void Walk(ICellGetter c, string space, int[]? grid)
        {
            foreach (var (r, persistent) in c.Persistent.Select(x => (x, true)).Concat(c.Temporary.Select(x => (x, false))))
            {
                var d = C.Ref(r, cache);
                d["space"] = space; d["grid"] = grid; d["persistent"] = persistent;
                // a container's contents and respawn flag, as the game reads its base (the stock check reads them)
                if (r is IPlacedObjectGetter po && cache.TryResolve<IContainerGetter>(po.Base.FormKey, out var cb))
                {
                    d["contents"] = (cb.Items ?? Array.Empty<IContainerEntryGetter>()).Select(i => new object[] { C.Key(i.Item.Item.FormKey), i.Item.Count }).ToList();
                    d["respawns"] = cb.Flags.HasFlag(Container.Flag.Respawns);
                }
                if (d["base"] is string { Length: > 0 } bk && cache.TryResolve<IMajorRecordGetter>(C.Fk(bk), out var b))
                    d["keywords"] = (b as IKeywordedGetter<IKeywordGetter>)?.Keywords?.Select(k => cache.TryResolve<IKeywordGetter>(k.FormKey, out var kw) ? kw.EditorID : C.Key(k.FormKey)).ToList();
                if (r is IPlacedNpcGetter) actors.Add(d);
                else if (r.FormKey.ModKey == me) refs.Add(d);
                else overrides.Add(d);
            }
            if (c.Landscape is { } l && l.VertexHeightMap is { } h)
            {
                var bytes = Enumerable.Range(0, 33 * 33).Select(i => unchecked((byte)h.HeightMap[i % 33, i / 33])).ToArray();
                land.Add(new Dictionary<string, object?>
                {
                    ["x"] = grid?[0], ["y"] = grid?[1], ["fk"] = C.Key(l.FormKey), ["offset"] = h.Offset, ["deltas"] = Convert.ToBase64String(bytes),
                    ["layers"] = l.Layers?.Count ?? 0,
                    ["alpha"] = l.Layers?.OfType<IAlphaLayerGetter>().Select(a => new Dictionary<string, object?> { ["quadrant"] = (int)a.Header!.Quadrant, ["texture"] = C.Key(a.Header.Texture.FormKey), ["n"] = a.AlphaLayerData?.Count ?? 0 }).ToList(),
                });
            }
            cellsOut.Add(new Dictionary<string, object?> { ["fk"] = C.Key(c.FormKey), ["edid"] = c.EditorID, ["space"] = space, ["grid"] = grid, ["override"] = c.FormKey.ModKey != me, ["navm"] = c.NavigationMeshes.Select(n => C.Key(n.FormKey)).ToList() });
        }
        foreach (var ws in mod.Worldspaces)
        {
            if (ws.TopCell is { } tc) Walk(tc, "exterior", null);
            foreach (var c in C.Cells(ws)) Walk(c, "exterior", c.Grid is { } g ? new[] { g.Point.X, g.Point.Y } : null);
        }
        foreach (var c in C.Interiors(mod).Where(c => c.FormKey.ModKey == me)) Walk(c, c.EditorID ?? C.Key(c.FormKey), null);

        var npcs = mod.Npcs.Select(n => new Dictionary<string, object?>
        {
            ["fk"] = C.Key(n.FormKey), ["edid"] = n.EditorID, ["name"] = n.Name?.String, ["race"] = C.Key(n.Race.FormKey),
            ["level"] = n.Configuration.Level is INpcLevelGetter nl ? nl.Level : -1, ["pc_level_mult"] = n.Configuration.Level is IPcLevelMultGetter,
            ["template"] = C.Key(n.Template.FormKey), ["crime_faction"] = C.Key(n.CrimeFaction.FormKey), ["class"] = C.Key(n.Class.FormKey),
            ["packages"] = n.Packages.Select(p => C.Key(p.FormKey)).ToList(),
            ["factions"] = n.Factions.Select(f => cache.TryResolve<IFactionGetter>(f.Faction.FormKey, out var fa) ? fa.EditorID : C.Key(f.Faction.FormKey)).ToList(),
            ["faction_keys"] = n.Factions.Select(f => C.Key(f.Faction.FormKey)).ToList(),
            ["faction_ranks"] = n.Factions.Select(f => new Dictionary<string, object?> { ["faction"] = C.Key(f.Faction.FormKey), ["rank"] = (int)f.Rank }).ToList(),
            ["voice"] = C.Key(n.Voice.FormKey),
            ["scripts"] = n.VirtualMachineAdapter?.Scripts.Select(sc => new Dictionary<string, object?>
            {
                ["name"] = sc.Name,
                ["props"] = sc.Properties.Select(pr => new Dictionary<string, object?> { ["name"] = pr.Name, ["type"] = pr.GetType().Name.Replace("BinaryOverlay", "").Replace("Script", "").Replace("Property", "").ToLowerInvariant(),
                    ["value"] = pr is IScriptObjectPropertyGetter op ? C.Key(op.Object.FormKey) : null }).ToList(),
            }).ToList() ?? new List<Dictionary<string, object?>>(),
            ["items"] = n.Items?.Select(i => C.Key(i.Item.Item.FormKey)).ToList(), ["outfit"] = C.Key(n.DefaultOutfit.FormKey),
            ["inventory"] = (n.Items ?? Array.Empty<IContainerEntryGetter>()).Select(i => new object[] { C.Key(i.Item.Item.FormKey), i.Item.Count }).ToList(),
            ["outfit_items"] = cache.TryResolve<IOutfitGetter>(n.DefaultOutfit.FormKey, out var dof) ? dof.Items?.Select(i => C.Key(i.FormKey)).ToList() : null,
            ["death_item"] = C.Key(n.DeathItem.FormKey),
        }).ToList();
        List<Dictionary<string, object?>> Scripts(IVirtualMachineAdapterGetter? v) => v?.Scripts.Select(sc => new Dictionary<string, object?>
        {
            ["name"] = sc.Name,
            ["props"] = sc.Properties.Select(pr => new Dictionary<string, object?> { ["name"] = pr.Name, ["type"] = pr.GetType().Name.Replace("BinaryOverlay", "").Replace("Script", "").Replace("Property", "").ToLowerInvariant(),
                ["value"] = pr is IScriptObjectPropertyGetter op ? C.Key(op.Object.FormKey) : null }).ToList(),
        }).ToList() ?? new List<Dictionary<string, object?>>();
        var activators = mod.Activators.Select(a => new Dictionary<string, object?>
        {
            ["fk"] = C.Key(a.FormKey), ["edid"] = a.EditorID, ["name"] = a.Name?.String, ["model"] = a.Model?.File.DataRelativePath.Path.ToLowerInvariant(), ["scripts"] = Scripts(a.VirtualMachineAdapter),
        }).ToList();
        // quests, topics and their INFOs, the travel lines' read-back: conditions, links, script properties (object keys, ints) and the fragment
        object? Val(IScriptPropertyGetter pr) => pr switch { IScriptObjectPropertyGetter op => C.Key(op.Object.FormKey), IScriptIntPropertyGetter ip => ip.Data, _ => null };
        var quests = mod.Quests.Select(qq => new Dictionary<string, object?>
        {
            ["fk"] = C.Key(qq.FormKey), ["edid"] = qq.EditorID, ["name"] = qq.Name?.String, ["start_game_enabled"] = qq.Flags.HasFlag(Quest.Flag.StartGameEnabled),
        }).ToList();
        var topics = mod.DialogTopics.Select(t => new Dictionary<string, object?>
        {
            ["fk"] = C.Key(t.FormKey), ["edid"] = t.EditorID, ["name"] = t.Name?.String, ["quest"] = C.Key(t.Quest.FormKey), ["branch"] = C.Key(t.Branch.FormKey),
            ["infos"] = t.Responses.Select(i =>
            {
                var ad = i.VirtualMachineAdapter as IDialogResponsesAdapterGetter;
                return new Dictionary<string, object?>
                {
                    ["fk"] = C.Key(i.FormKey), ["prompt"] = i.Prompt?.String, ["text"] = i.Responses.Select(r => r.Text.String).ToList(),
                    ["link_to"] = i.LinkTo.Select(l => C.Key(l.FormKey)).ToList(),
                    ["conditions"] = i.Conditions.Select(c =>
                    {
                        var cd = c.Data;
                        var row = new Dictionary<string, object?> { ["fn"] = cd.GetType().Name.Replace("BinaryOverlay", "").Replace("ConditionData", ""), ["run_on"] = cd.RunOnType.ToString(),
                            ["op"] = c.CompareOperator.ToString(), ["value"] = c is IConditionFloatGetter cf ? cf.ComparisonValue : null };
                        switch (cd)
                        {
                            case IGetInFactionConditionDataGetter gf: row["faction"] = C.Key(gf.Faction.Link.FormKey); break;
                            case IGetItemCountConditionDataGetter gi: row["item"] = C.Key(gi.ItemOrList.Link.FormKey); break;
                        }
                        return row;
                    }).ToList(),
                    ["scripts"] = ad?.Scripts.Select(sc => new Dictionary<string, object?> { ["name"] = sc.Name,
                        ["props"] = sc.Properties.Select(pr => new Dictionary<string, object?> { ["name"] = pr.Name, ["value"] = Val(pr) }).ToList() }).ToList(),
                    ["fragment"] = ad?.ScriptFragments is { } sf ? new Dictionary<string, object?> { ["file"] = sf.FileName, ["on_end"] = sf.OnEnd?.FragmentName } : null,
                };
            }).ToList(),
        }).ToList();
        var worldMarkers = Read.MapMarkers(world.Worldspaces.Single()).ToDictionary(kv => kv.Value, kv => kv.Key); // form key -> editor id
        var spells = mod.Spells.Select(sp => new Dictionary<string, object?>
        {
            ["fk"] = C.Key(sp.FormKey), ["edid"] = sp.EditorID, ["name"] = sp.Name?.String, ["type"] = sp.Type.ToString(), ["cast"] = sp.CastType.ToString(), ["target"] = sp.TargetType.ToString(),
            ["effects"] = sp.Effects.Select(e =>
            {
                var has = cache.TryResolve<IMagicEffectGetter>(e.BaseEffect.FormKey, out var me);
                return new Dictionary<string, object?> { ["mgef"] = C.Key(e.BaseEffect.FormKey), ["mgef_edid"] = has ? me!.EditorID : null,
                    ["actor_value"] = has ? me!.Archetype.ActorValue.ToString() : null, ["magnitude"] = e.Data?.Magnitude, ["duration"] = e.Data?.Duration, ["area"] = e.Data?.Area };
            }).ToList(),
        }).ToList();
        var messages = mod.Messages.Select(ms => new Dictionary<string, object?> { ["fk"] = C.Key(ms.FormKey), ["edid"] = ms.EditorID, ["text"] = ms.Description.String }).ToList();
        var packages = mod.Packages.Select(p => new Dictionary<string, object?>
        {
            ["fk"] = C.Key(p.FormKey), ["edid"] = p.EditorID, ["template"] = C.Key(p.PackageTemplate.FormKey), ["hour"] = p.ScheduleHour, ["minutes"] = p.ScheduleDurationInMinutes,
            ["location"] = p.Data.Values.OfType<IPackageDataLocationGetter>().Select(d => d.Location.Target is ILocationTargetGetter t ? C.Key(t.Link.FormKey) : null).FirstOrDefault(),
            ["radius"] = p.Data.Values.OfType<IPackageDataLocationGetter>().Select(d => (int?)d.Location.Radius).FirstOrDefault(),
            ["target"] = p.Data.Values.OfType<IPackageDataTargetGetter>().Select(d => d.Target is IPackageTargetSpecificReferenceGetter s ? C.Key(s.Reference.FormKey) : null).FirstOrDefault(x => x != null),
            ["target_linked"] = p.Data.Values.OfType<IPackageDataTargetGetter>().Take(1).Any(d => d.Target is IPackageTargetLinkedReferenceGetter),
        }).ToList();
        var factions = mod.Factions.Select(f => new Dictionary<string, object?>
        {
            ["fk"] = C.Key(f.FormKey), ["edid"] = f.EditorID, ["flags"] = (int)f.Flags, ["vendor"] = f.Flags.HasFlag(Faction.FactionFlag.Vendor),
            ["chest"] = C.Key(f.MerchantContainer.FormKey), ["list"] = C.Key(f.VendorBuySellList.FormKey), ["crime"] = f.Flags.HasFlag(Faction.FactionFlag.TrackCrime),
        }).ToList();
        var classes = mod.Classes.Select(c => new Dictionary<string, object?> { ["fk"] = C.Key(c.FormKey), ["edid"] = c.EditorID, ["teaches"] = c.Teaches?.ToString(), ["max_level"] = c.MaxTrainingLevel }).ToList();
        // anything levelled against the player that our records reach (decision 0035): levelled lists in an inventory, an
        // outfit, a death item, a spell list or a placed container; a level that follows the player; a template that scales
        var levelled = new List<string>();
        void Item(string from, FormKey k)
        {
            if (cache.TryResolve<ILeveledItemGetter>(k, out var li) && People.Levelled(li, cache)) levelled.Add($"{from} -> {C.Key(k)} {li.EditorID}");
        }
        void Outfit(string from, FormKey k)
        {
            if (cache.TryResolve<IOutfitGetter>(k, out var o)) foreach (var i in o.Items ?? Array.Empty<IFormLinkGetter<IOutfitTargetGetter>>()) Item(from, i.FormKey);
        }
        foreach (var n in mod.Npcs)
        {
            foreach (var i in n.Items ?? Array.Empty<IContainerEntryGetter>()) Item(n.EditorID ?? "", i.Item.Item.FormKey);
            Outfit(n.EditorID + " outfit", n.DefaultOutfit.FormKey);
            Outfit(n.EditorID + " sleep outfit", n.SleepingOutfit.FormKey);
            Item(n.EditorID + " death item", n.DeathItem.FormKey);
            foreach (var sp in n.ActorEffect ?? Array.Empty<IFormLinkGetter<ISpellRecordGetter>>())
                if (cache.TryResolve<ILeveledSpellGetter>(sp.FormKey, out var ls) && People.Levelled(ls, cache)) levelled.Add($"{n.EditorID} spells -> {C.Key(sp.FormKey)} {ls.EditorID}");
            if (n.Configuration.Level is IPcLevelMultGetter) levelled.Add($"{n.EditorID}: PC level mult");
            if (People.LevelledByTemplate(n, cache) is { } why) levelled.Add($"{n.EditorID}: {why}");
        }
        foreach (var c in mod.Containers) foreach (var i in c.Items ?? Array.Empty<IContainerEntryGetter>()) Item(c.EditorID ?? "", i.Item.Item.FormKey);
        foreach (var a in actors.Cast<Dictionary<string, object?>>()) if (cache.TryResolve<ILeveledNpcGetter>(C.Fk((string)a["base"]!), out _)) levelled.Add($"actor {a["fk"]} is a LVLN");
        // placed things: a levelled item list as a base, and a master's container that holds one (one line per base)
        var held = new Dictionary<string, (int n, string first)>();
        foreach (var r in refs.Cast<Dictionary<string, object?>>())
        {
            if (r["base"] is not string { Length: > 0 } bk) continue;
            if (cache.TryResolve<ILeveledItemGetter>(C.Fk(bk), out var li) && People.Levelled(li, cache)) levelled.Add($"ref {r["fk"]} -> {li.EditorID}");
            else if (cache.TryResolve<IContainerGetter>(C.Fk(bk), out var co)
                && co.Items?.Any(i => cache.TryResolve<ILeveledItemGetter>(i.Item.Item.FormKey, out var x) && People.Levelled(x, cache)) == true)
                held[bk] = (held.GetValueOrDefault(bk).n + 1, held.GetValueOrDefault(bk).first ?? (string)r["fk"]!);
        }
        foreach (var (bk, (n, first)) in held.OrderBy(kv => kv.Key, StringComparer.Ordinal))
            levelled.Add($"container {bk} {(cache.TryResolve<IContainerGetter>(C.Fk(bk), out var co) ? co.EditorID : "")} holds a levelled list: {n} placed (first {first})");

        // vanilla's innkeeper rent: the voices of form list 03B4A5 and the conditions of the rent offer INFO 079B1A
        var rentVoices = cache.TryResolve<IFormListGetter>(C.Fk("Skyrim.esm:03B4A5"), out var rvl) ? rvl.Items.Select(i => C.Key(i.FormKey)).ToList() : new List<string>();
        var rentOffer = new List<Dictionary<string, object?>>();
        if (cache.TryResolve<IDialogResponsesGetter>(C.Fk("Skyrim.esm:079B1A"), out var offer))
            foreach (var c in offer.Conditions)
            {
                var cd = c.Data;
                var row = new Dictionary<string, object?> { ["fn"] = cd.GetType().Name.Replace("BinaryOverlay", "").Replace("ConditionData", ""), ["run_on"] = cd.RunOnType.ToString(),
                    ["op"] = c.CompareOperator.ToString(), ["or"] = c.Flags.HasFlag(Condition.Flag.OR) };
                row["value"] = c is IConditionFloatGetter cf ? (object)cf.ComparisonValue : c is IConditionGlobalGetter cg ? C.Key(cg.ComparisonValue.FormKey) : null;
                switch (cd)
                {
                    case IGetInFactionConditionDataGetter gf: row["faction"] = C.Key(gf.Faction.Link.FormKey); break;
                    case IGetFactionRankConditionDataGetter gr: row["faction"] = C.Key(gr.Faction.Link.FormKey); break;
                    case IGetActorValueConditionDataGetter ga: row["actor_value"] = ga.ActorValue.ToString(); break;
                    case IGetItemCountConditionDataGetter gi: row["item"] = C.Key(gi.ItemOrList.Link.FormKey); break;
                    case IGetIsIDConditionDataGetter gid: row["object"] = C.Key(gid.Object.Link.FormKey); break;
                }
                rentOffer.Add(row);
            }
        C.WriteJson(outPath, new Dictionary<string, object?>
        {
            ["rent_voices"] = rentVoices, ["rent_offer"] = rentOffer,
            ["esp"] = esp, ["masters"] = mod.ModHeader.MasterReferences.Select(m => m.Master.FileName.String).ToList(),
            ["flags"] = (int)mod.ModHeader.Flags, ["counts"] = counts, ["unresolved"] = unresolved,
            ["refs"] = refs, ["overrides"] = overrides, ["land"] = land, ["actors"] = actors, ["cells"] = cellsOut,
            ["npcs"] = npcs, ["packages"] = packages, ["factions"] = factions, ["classes"] = classes, ["levelled"] = levelled,
            ["activators"] = activators, ["quests"] = quests, ["topics"] = topics, ["world_markers"] = worldMarkers, ["spells"] = spells, ["messages"] = messages,
        });
        Console.WriteLine($"dump: {esp}: {string.Join(", ", counts.Select(kv => $"{kv.Key} {kv.Value}"))}; unresolved {unresolved.Count}");
        return 0;
    }
}
