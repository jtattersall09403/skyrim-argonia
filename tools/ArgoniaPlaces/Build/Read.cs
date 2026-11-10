// Read verbs (JSON out, one object):
//   source <plugin> <cell edid> <out.json>      an interior cell of a source plugin: header, refs, navmeshes
//   doors <plugin> <worldspace edid> <out.json> the worldspace's load doors: ref, base, pos, the interior they lead to
//   world <world.esm> <request.json> <out.json> facts of the world ESM a build needs: the worldspace, each asked
//        cell's CELL, LAND, NAVM keys, its refs (for clear matching) and its land texture layers; request:
//        {"cells": [[x, y]...]}
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Cache;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using System.Text.Json;

static class Read
{
    static readonly string[] Base = { "Skyrim.esm", "Update.esm", "Black Marsh.esm" };

    /// The plugin, its masters and ours' base masters, in load order.
    public static ILinkCache CacheWith(string plugin)
    {
        var masters = C.Open(plugin).ModHeader.MasterReferences.Select(x => x.Master.FileName.String);
        var files = Base.Concat(masters).Append(Path.GetFileName(plugin)).Distinct(StringComparer.OrdinalIgnoreCase)
            .OrderBy(f => Array.FindIndex(Order, o => o.Equals(f, StringComparison.OrdinalIgnoreCase)) is var i && i < 0 ? 99 : i);
        return C.Cache(files.Select(f => f.Equals(Path.GetFileName(plugin), StringComparison.OrdinalIgnoreCase) ? plugin : f));
    }
    static readonly string[] Order = { "Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm", "Black Marsh.esm" };

    public static Dictionary<string, object?> CellRow(ICellGetter c, ILinkCache cache)
    {
        var refs = c.Persistent.Select(r => { var d = C.Ref(r, cache); d["persistent"] = true; return d; })
            .Concat(c.Temporary.Select(r => C.Ref(r, cache))).ToList();
        var navs = c.NavigationMeshes.Select(n => new Dictionary<string, object?>
        {
            ["fk"] = C.Key(n.FormKey),
            ["verts"] = n.Data?.Vertices.Count ?? 0,
            ["tris"] = n.Data?.Triangles.Count ?? 0,
            ["doors"] = n.Data?.DoorTriangles.Select(t => C.Key(t.Door.FormKey)).ToList(),
        }).ToList();
        return new()
        {
            ["fk"] = C.Key(c.FormKey), ["edid"] = c.EditorID, ["name"] = c.Name?.String, ["flags"] = (int)c.Flags,
            ["lighting_template"] = C.Key(c.LightingTemplate.FormKey), ["owner"] = C.Key(c.Owner.FormKey),
            ["refs"] = refs, ["navmesh"] = navs,
        };
    }

    public static int Source(string plugin, string edid, string outPath)
    {
        var m = C.Open(plugin);
        var cache = CacheWith(plugin);
        var c = m.EnumerateMajorRecords<ICellGetter>().FirstOrDefault(x => (edid.Contains(':') ? C.Key(x.FormKey) == edid : x.EditorID == edid) && x.Grid == null)
            ?? throw new InvalidDataException($"no interior cell {edid} in {plugin}");
        C.WriteJson(outPath, CellRow(c, cache));
        return 0;
    }

    public static int Doors(string plugin, string wsEdid, string outPath)
    {
        var m = C.Open(plugin);
        var cache = CacheWith(plugin);
        var ws = m.Worldspaces.First(w => w.EditorID == wsEdid);
        var where = new Dictionary<FormKey, string>();
        foreach (var c in m.EnumerateMajorRecords<ICellGetter>())
            if (c.Grid == null) foreach (var r in c.Persistent.Concat(c.Temporary)) where[r.FormKey] = c.EditorID ?? C.Key(c.FormKey);
        var rows = new List<object>();
        IEnumerable<ICellGetter> all = ws.TopCell is { } tc ? C.Cells(ws).Prepend(tc) : C.Cells(ws);
        foreach (var c in all)
            foreach (var r in c.Persistent.Concat(c.Temporary).OfType<IPlacedObjectGetter>())
                if (r.TeleportDestination is { } t && where.TryGetValue(t.Door.FormKey, out var into))
                {
                    var d = C.Ref(r, cache); d["into"] = into; rows.Add(d);
                }
        C.WriteJson(outPath, rows);
        return 0;
    }

    /// list <plugin> <npc|door|furn|cont|acti|stat> <out.json>: a plugin's own records of a kind (for authoring fixtures).
    public static int List(string plugin, string kind, string outPath)
    {
        var m = C.Open(plugin);
        IEnumerable<IMajorRecordGetter> recs = kind switch
        {
            "npc" => m.Npcs, "door" => m.Doors, "furn" => m.Furniture, "cont" => m.Containers, "acti" => m.Activators,
            "stat" => m.Statics, "pack" => m.Packages, "fact" => m.Factions, "flst" => m.FormLists, "clas" => m.Classes,
            _ => throw new ArgumentException(kind),
        };
        var rows = recs.Where(r => r.FormKey.ModKey == m.ModKey).Select(r =>
        {
            var d = new Dictionary<string, object?> { ["fk"] = C.Key(r.FormKey), ["edid"] = r.EditorID, ["model"] = C.Model(r) };
            if (r is INpcGetter n)
            {
                d["race"] = C.Key(n.Race.FormKey); d["template"] = C.Key(n.Template.FormKey); d["flags"] = (int)n.Configuration.Flags;
                d["template_flags"] = (int)n.Configuration.TemplateFlags; d["packages"] = n.Packages.Count; d["factions"] = n.Factions.Select(f => C.Key(f.Faction.FormKey)).ToList();
                d["level"] = n.Configuration.Level is INpcLevelGetter l ? l.Level : -1;
            }
            if (r is IPackageGetter pk)
            {
                d["template"] = C.Key(pk.PackageTemplate.FormKey); d["hour"] = pk.ScheduleHour; d["minutes"] = pk.ScheduleDurationInMinutes;
                d["inputs"] = pk.Data.Select(kv => $"{kv.Key}:{kv.Value.GetType().Name.Replace("BinaryOverlay", "")}").ToList();
                d["conditions"] = pk.Conditions.Count; d["owner_quest"] = C.Key(pk.OwnerQuest.FormKey);
            }
            if (r is IFurnitureGetter f) d["keywords"] = f.Keywords?.Select(k => C.Key(k.FormKey)).ToList();
            return d;
        }).ToList();
        C.WriteJson(outPath, rows);
        return 0;
    }

    /// links <key...>: each record's form links (to see what a vanilla record copied as ours would still point at).
    public static int Links(string[] keys)
    {
        var cache = C.Cache(Write.Masters);
        foreach (var k in keys)
        {
            var r = cache.Resolve<IMajorRecordGetter>(C.Fk(k));
            Console.WriteLine($"{k} {r.EditorID}: " + string.Join(", ", r.EnumerateFormLinks().Select(l => $"{C.Key(l.FormKey)}<{l.Type.Name.Replace("Getter", "")}>")));
            if (r is IPackageGetter p)
                foreach (var kv in p.Data) Console.WriteLine($"   data {kv.Key}: {kv.Value.GetType().Name.Replace("BinaryOverlay", "")} {Describe(kv.Value)}");
        }
        return 0;
    }
    static string Describe(object v) => v switch
    {
        IPackageDataLocationGetter l => $"loc {l.Location.Target.GetType().Name} r={l.Location.Radius}",
        IPackageDataTargetGetter t => $"target {t.Target?.GetType().Name} {t.Type}",
        IPackageDataObjectListGetter o => $"objlist {o.Data}",
        IPackageDataBoolGetter b => $"bool {b.Data}",
        IPackageDataFloatGetter f => $"float {f.Data}",
        IPackageDataIntGetter i => $"int {i.Data}",
        _ => "",
    };

    /// The world's map markers (nwmap, ArgoniaNewWorld.esm's persistent cell): editor id -> form key, so a travel line can name one.
    public static Dictionary<string, string> MapMarkers(IWorldspaceGetter ws) =>
        (ws.TopCell?.Persistent ?? []).OfType<IPlacedObjectGetter>().Where(r => r.MapMarker != null && r.EditorID != null)
            .ToDictionary(r => r.EditorID!, r => C.Key(r.FormKey));

    public static int World(string esm, string reqPath, string outPath)
    {
        var m = C.Open(esm);
        using var req = JsonDocument.Parse(File.ReadAllText(reqPath));
        var want = req.RootElement.GetProperty("cells").EnumerateArray().Select(e => (e[0].GetInt32(), e[1].GetInt32())).ToHashSet();
        var ws = m.Worldspaces.Single();
        var cells = new List<object>();
        foreach (var c in C.Cells(ws))
        {
            if (c.Grid is not { } g || !want.Contains((g.Point.X, g.Point.Y))) continue;
            var l = c.Landscape;
            var layers = l?.Layers?.Select(x => new Dictionary<string, object?>
            {
                ["quadrant"] = (int)x.Header!.Quadrant, ["layer"] = x.Header.LayerNumber, ["texture"] = C.Key(x.Header.Texture.FormKey),
                ["alpha"] = x is IAlphaLayerGetter a ? a.AlphaLayerData?.Select(p => new object[] { p.Position, p.Opacity }).ToList() : null,
            }).ToList();
            cells.Add(new Dictionary<string, object?>
            {
                ["x"] = g.Point.X, ["y"] = g.Point.Y, ["fk"] = C.Key(c.FormKey), ["land"] = l == null ? null : C.Key(l.FormKey),
                ["offset"] = l?.VertexHeightMap?.Offset,
                ["deltas"] = l?.VertexHeightMap is { } h ? Convert.ToBase64String(Enumerable.Range(0, 33 * 33).Select(i => unchecked((byte)h.HeightMap[i % 33, i / 33])).ToArray()) : null,
                ["layers"] = layers,
                ["navm"] = c.NavigationMeshes.Select(n => C.Key(n.FormKey)).ToList(),
                ["refs"] = c.Temporary.Concat(c.Persistent).Select(r => C.Ref(r, null)).ToList(),
            });
        }
        var ltex = m.LandscapeTextures.Select(t => new Dictionary<string, object?> { ["fk"] = C.Key(t.FormKey), ["edid"] = t.EditorID }).ToList();
        C.WriteJson(outPath, new Dictionary<string, object?>
        {
            ["worldspace"] = C.Key(ws.FormKey), ["world_edid"] = ws.EditorID, ["top_cell"] = ws.TopCell == null ? null : C.Key(ws.TopCell.FormKey),
            ["description"] = m.ModHeader.Description, ["masters"] = m.ModHeader.MasterReferences.Select(x => x.Master.FileName.String).ToList(),
            ["ltex"] = ltex, ["cells"] = cells, ["map_markers"] = MapMarkers(ws),
        });
        return 0;
    }
}
