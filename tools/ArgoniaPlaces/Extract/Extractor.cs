using System.Collections;
using System.Text.Json;
using System.Text.RegularExpressions;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Cache;
using Mutagen.Bethesda.Plugins.Order;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Plugins.Aspects;
using Mutagen.Bethesda.Strings;
using Noggog;

// One place out of its plugins into a bundle directory (the contract: docs/design/place-studio.md, "Bundles").
// Every record is read as the load order's winner; refs are the union of every loaded plugin's refs in the extent.
static class Extractor
{
    const int V = 33;
    static readonly JsonSerializerOptions Js = new() { WriteIndented = false };
    static readonly string[] Vanilla = { "skyrim.esm", "update.esm", "dawnguard.esm", "hearthfires.esm", "dragonborn.esm" };

    public static string Key(FormKey fk) => $"{fk.ModKey.FileName}:{fk.ID:X6}";
    static string? KeyN(FormKey fk) => fk.IsNull ? null : Key(fk);

    // ---- loading ------------------------------------------------------------------------------------------------

    sealed class Loaded
    {
        public List<(ISkyrimModGetter mod, string path)> Mods = new();
        public ILinkCache Cache = null!;
        public FormKey World;
        public IWorldspaceGetter? WorldRec;
    }

    static Loaded Load(Job job)
    {
        var L = new Loaded();
        var byName = new Dictionary<string, ISkyrimModGetter>(StringComparer.OrdinalIgnoreCase);
        string Find(string file)
        {
            foreach (var d in job.Search)
            {
                var p = Path.Combine(d, file);
                if (File.Exists(p)) return p;
            }
            throw new FileNotFoundException($"plugin {file} is in none of the search directories");
        }
        void Add(string file)
        {
            if (byName.ContainsKey(file)) return;
            var path = Find(file);
            var m = SkyrimMod.CreateFromBinaryOverlay(path, SkyrimRelease.SkyrimSE, NoStrings);
            byName[file] = m;  // before the masters: a cycle cannot recurse forever
            foreach (var mr in m.ModHeader.MasterReferences) Add(mr.Master.FileName);
            L.Mods.Add((m, path));
            Console.Error.WriteLine($"loaded {path}");
        }
        foreach (var p in job.Plugins) Add(p);
        L.Cache = new LoadOrder<ISkyrimModGetter>(L.Mods.Select(m => m.mod)).ToImmutableLinkCache();
        if (job.Worldspace.Contains(':'))
        {
            var parts = job.Worldspace.Split(':');
            L.World = new FormKey(ModKey.FromFileName(parts[0]), Convert.ToUInt32(parts[1], 16));
        }
        else if (job.Worldspace != "")
            L.World = L.Mods.SelectMany(m => m.mod.Worldspaces).First(w => string.Equals(w.EditorID, job.Worldspace, StringComparison.OrdinalIgnoreCase)).FormKey;
        if (!L.World.IsNull) L.Cache.TryResolve<IWorldspaceGetter>(L.World, out L.WorldRec);
        return L;
    }

    // Localized plugins' strings are never read (decision 0003): names come only from plugins that carry them inline.
    static readonly string NoStr = Directory.CreateTempSubdirectory("argonia-nostrings").FullName;
    static readonly Mutagen.Bethesda.Plugins.Binary.Parameters.BinaryReadParameters NoStrings = new()
    {
        StringsParam = new Mutagen.Bethesda.Strings.StringsReadParameters { StringsFolderOverride = NoStr, BsaFolderOverride = NoStr },
    };

    // ---- gathering ----------------------------------------------------------------------------------------------

    sealed class Space
    {
        public string Id = "", Type = "exterior";
        public ICellGetter? Cell;                      // interior: the winning CELL record
        public string From = "";
        public Dictionary<FormKey, (IMajorRecordGetter rec, string from, (int, int)? cell)> Refs = new();
        public Dictionary<FormKey, (INavigationMeshGetter rec, (int, int)? cell)> Navs = new();
    }

    sealed class Exterior
    {
        public Dictionary<(int, int), (ICellGetter cell, string from)> Cells = new();
        public Dictionary<(int, int), ILandscapeGetter> Land = new();
    }

    static (int, int) GridOf(float x, float y) => ((int)Math.Floor(x / 4096), (int)Math.Floor(y / 4096));

    static void GatherExterior(Loaded L, Func<(int, int), bool> want, Space sp, Exterior ex)
    {
        foreach (var (mod, _) in L.Mods)
            foreach (var w in mod.Worldspaces)
            {
                if (w.FormKey != L.World) continue;
                var from = mod.ModKey.FileName.String;
                if (w.TopCell is { } top)  // persistent refs live in the world's persistent cell; placed by position
                    foreach (var r in top.Persistent.Concat(top.Temporary))
                        if (Pos(r) is { } p && want(GridOf(p.X, p.Y))) AddRef(sp, r, from, GridOf(p.X, p.Y));
                foreach (var b in w.SubCells) foreach (var sb in b.Items) foreach (var c in sb.Items)
                {
                    if (c.Grid is not { } g) continue;
                    var gp = (g.Point.X, g.Point.Y);
                    if (!want(gp)) continue;
                    ex.Cells[gp] = (c, from);
                    if (c.Landscape is { } land) ex.Land[gp] = land;
                    foreach (var r in c.Persistent.Concat(c.Temporary)) AddRef(sp, r, from, gp);
                    foreach (var n in c.NavigationMeshes) sp.Navs[n.FormKey] = (n, gp);
                }
            }
    }

    // the exterior cells of the worldspace whose winning CELL record names the location (editor id or key)
    static HashSet<(int, int)> LocationCells(Loaded L, string loc)
    {
        FormKey lk;
        if (loc.Contains(':')) { var p = loc.Split(':'); lk = new FormKey(ModKey.FromFileName(p[0]), Convert.ToUInt32(p[1], 16)); }
        else lk = L.Mods.SelectMany(m => m.mod.Locations).First(x => string.Equals(x.EditorID, loc, StringComparison.OrdinalIgnoreCase)).FormKey;
        var win = new Dictionary<(int, int), FormKey>();
        foreach (var (mod, _) in L.Mods)
            foreach (var w in mod.Worldspaces.Where(w => w.FormKey == L.World))
                foreach (var b in w.SubCells) foreach (var sb in b.Items) foreach (var c in sb.Items)
                    if (c.Grid is { } g) win[(g.Point.X, g.Point.Y)] = c.Location.FormKey;
        var s = win.Where(kv => kv.Value == lk).Select(kv => kv.Key).ToHashSet();
        Console.Error.WriteLine($"location {loc}: {s.Count} cells");
        return s;
    }

    static void AddRef(Space sp, IMajorRecordGetter r, string from, (int, int)? cell)
    {
        if (r.IsDeleted) sp.Refs.Remove(r.FormKey);
        else sp.Refs[r.FormKey] = (r, from, cell);
    }

    sealed class InteriorIndex
    {
        public Dictionary<FormKey, FormKey> RefCell = new();                       // placed ref -> interior cell
        public Dictionary<FormKey, List<(ICellGetter cell, string from)>> Cells = new();  // every plugin's copy, load order
    }

    static InteriorIndex IndexInteriors(Loaded L)
    {
        var ix = new InteriorIndex();
        foreach (var (mod, _) in L.Mods)
            foreach (var b in mod.Cells.Records) foreach (var sb in b.SubBlocks) foreach (var c in sb.Cells)
            {
                if (!ix.Cells.TryGetValue(c.FormKey, out var l)) ix.Cells[c.FormKey] = l = new();
                l.Add((c, mod.ModKey.FileName.String));
                foreach (var r in c.Persistent.Concat(c.Temporary)) ix.RefCell[r.FormKey] = c.FormKey;
            }
        return ix;
    }

    static Space InteriorSpace(InteriorIndex ix, FormKey cellKey)
    {
        var copies = ix.Cells[cellKey];
        var (cell, from) = copies[^1];
        var sp = new Space { Id = SpaceId(cell), Type = "interior", Cell = cell, From = from };
        foreach (var (c, f) in copies)
        {
            foreach (var r in c.Persistent.Concat(c.Temporary)) AddRef(sp, r, f, null);
            foreach (var n in c.NavigationMeshes) sp.Navs[n.FormKey] = (n, null);
        }
        return sp;
    }

    static string SpaceId(ICellGetter c) => c.EditorID is { Length: > 0 } e ? e : Key(c.FormKey).Replace(':', '_');

    static IEnumerable<(FormKey door, FormKey target)> Doors(Space sp) =>
        sp.Refs.Values.Select(v => v.rec).OfType<IPlacedObjectGetter>()
            .Where(r => r.TeleportDestination is { } t && !t.Door.FormKey.IsNull)
            .Select(r => (r.FormKey, r.TeleportDestination!.Door.FormKey));

    // ---- the run ------------------------------------------------------------------------------------------------

    public static int Run(Job job)
    {
        var sw = System.Diagnostics.Stopwatch.StartNew();
        var L = Load(job);
        Directory.CreateDirectory(job.Out);
        var extent = job.ExtentCells();
        if (job.Location != "") extent.UnionWith(LocationCells(L, job.Location));
        if (job.Marker != "")  // a placed ref (key) and a radius in game units
        {
            var p = job.Marker.Split(':');
            var mk = new FormKey(ModKey.FromFileName(p[0]), Convert.ToUInt32(p[1], 16));
            var pos = Resolve(L, mk).rec is { } mrec ? Pos(mrec) : null;
            if (pos == null) throw new InvalidOperationException($"marker {job.Marker} not found");
            job.Areas.Add((pos.Value.X, pos.Value.Y, job.MarkerRadius));
            extent.UnionWith(job.ExtentCells());
        }
        if (extent.Count == 0 && !L.World.IsNull) throw new InvalidOperationException("the extent has no cells: give cells, areas or a location");
        var ext = new Space { Id = "exterior", Type = "exterior" };
        var ex = new Exterior();
        if (!L.World.IsNull) GatherExterior(L, extent.Contains, ext, ex);
        var spaces = new List<Space> { ext };
        var outside = new List<object>();
        if (job.FollowDoors)
        {
            var ix = IndexInteriors(L);
            var seen = new HashSet<FormKey>();
            var queue = new Queue<Space>(); queue.Enqueue(ext);
            while (queue.Count > 0)
            {
                var sp = queue.Dequeue();
                foreach (var (door, target) in Doors(sp))
                {
                    if (!ix.RefCell.TryGetValue(target, out var ck) || !seen.Add(ck)) continue;
                    var isp = InteriorSpace(ix, ck);
                    // an interior that opens onto exterior ground outside the extent belongs to another place: not followed
                    var exits = Doors(isp).Where(d => !ix.RefCell.ContainsKey(d.target) && !ext.Refs.ContainsKey(d.target)).ToList();
                    if (exits.Count > 0 && sp.Type == "interior")
                    {
                        outside.Add(new { space = isp.Id, reached_from = sp.Id, exits = exits.Select(e => Key(e.target)).ToList() });
                        continue;
                    }
                    spaces.Add(isp); queue.Enqueue(isp);
                }
            }
        }
        var w = new Writer(L, job);
        foreach (var sp in spaces) w.WriteSpace(sp, sp == ext ? ex : null, spaces);
        w.WriteBases(); w.WriteNpcs();
        var bundle = new Dictionary<string, object?>
        {
            ["bundle_id"] = job.BundleId, ["kind"] = job.Kind, ["title"] = job.Title,
            ["plugins"] = L.Mods.Select(m => m.mod.ModKey.FileName.String).ToList(),
            ["source_plugins"] = job.Plugins,
            ["worldspace"] = L.World.IsNull ? null : Key(L.World),
            ["worldspace_edid"] = L.WorldRec?.EditorID,
            ["anchor"] = w.Anchor(ext),
            ["cells"] = extent.OrderBy(c => c.Item2).ThenBy(c => c.Item1).Select(c => new[] { c.Item1, c.Item2 }).ToList(),
            ["spaces"] = spaces.Select(s => s.Id).ToList(),
            ["not_followed"] = outside,
            ["counts"] = w.Counts,
        };
        File.WriteAllText(Path.Combine(job.Out, "bundle.json"), JsonSerializer.Serialize(bundle, new JsonSerializerOptions { WriteIndented = true }));
        Console.Error.WriteLine($"extracted {job.BundleId}: {spaces.Count} spaces, {w.Counts["refs"]} refs, {w.Counts["bases"]} bases in {sw.Elapsed.TotalSeconds:F0}s");
        return 0;
    }

    // survey: per exterior cell, refs by kind and plugin, and doors with where they lead (to measure a source's extent)
    public static int Survey(Job job, string outPath)
    {
        var L = Load(job);
        var sp = new Space(); var ex = new Exterior();
        GatherExterior(L, _ => true, sp, ex);
        var ix = IndexInteriors(L);
        using var o = new StreamWriter(outPath);
        o.WriteLine("cx\tcy\tplugin\tkind\tcount\tdoors_to");
        foreach (var g in sp.Refs.Values.GroupBy(v => (v.cell, v.from, Kind(L, v.rec))))
        {
            var doors = g.Select(v => v.rec).OfType<IPlacedObjectGetter>().Where(r => r.TeleportDestination is { } t && !t.Door.FormKey.IsNull)
                .Select(r => ix.RefCell.TryGetValue(r.TeleportDestination!.Door.FormKey, out var ck) ? SpaceId(ix.Cells[ck][^1].cell) : "ext");
            o.WriteLine($"{g.Key.cell!.Value.Item1}\t{g.Key.cell!.Value.Item2}\t{g.Key.from}\t{g.Key.Item3}\t{g.Count()}\t{string.Join(",", doors)}");
        }
        foreach (var (gp, (c, from)) in ex.Cells.Where(c => c.Value.cell.EditorID != null))
            o.WriteLine($"{gp.Item1}\t{gp.Item2}\t{from}\tcell_edid\t0\t{c.EditorID}");
        return 0;
    }

    // ---- kinds and the Nordic flag ------------------------------------------------------------------------------

    static P3Float? Pos(IMajorRecordGetter r) => r switch
    {
        IPlacedObjectGetter p => p.Placement?.Position,
        IPlacedNpcGetter n => n.Placement?.Position,
        IPlacedGetter g => (g.GetType().GetProperty("Placement")?.GetValue(g) as IPlacementGetter)?.Position,
        _ => null,
    };

    public static FormKey BaseOf(IMajorRecordGetter r) => r switch
    {
        IPlacedObjectGetter p => p.Base.FormKey,
        IPlacedNpcGetter n => n.Base.FormKey,
        _ => (r.GetType().GetProperty("Base")?.GetValue(r) as IFormLinkGetter)?.FormKey ?? FormKey.Null,
    };

    static readonly Dictionary<FormKey, (IMajorRecordGetter? rec, string from)> BaseCache = new();
    static (IMajorRecordGetter? rec, string from) Resolve(Loaded L, FormKey fk)
    {
        if (fk.IsNull) return (null, "");
        if (BaseCache.TryGetValue(fk, out var v)) return v;
        v = L.Cache.TryResolveSimpleContext(fk, out var ctx) ? (ctx.Record, ctx.ModKey.FileName.String) : (null, "");
        return BaseCache[fk] = v;
    }

    public static string? ModelOf(IMajorRecordGetter? b)
    {
        var f = (b as IModeledGetter)?.Model?.File.DataRelativePath.Path;
        if (string.IsNullOrEmpty(f)) return null;
        f = f.Replace('\\', '/').ToLowerInvariant();
        return f.StartsWith("meshes/") ? f[7..] : f;
    }

    static readonly Regex Marker = new(@"marker|xmarker|^cow$|navcut|collision|trigger|fxlight", RegexOptions.IgnoreCase);
    static string Kind(Loaded L, IMajorRecordGetter r)
    {
        if (r is IPlacedNpcGetter) return "actor";
        var b = Resolve(L, BaseOf(r)).rec;
        return KindOfBase(b);
    }

    // kind from the record type, then for statics from the model path (decided once, here)
    public static string KindOfBase(IMajorRecordGetter? b)
    {
        var m = ModelOf(b) ?? ""; var e = (b?.EditorID ?? "").ToLowerInvariant();
        switch (b)
        {
            case null: return "other";
            case INpcGetter or ILeveledNpcGetter: return "actor";
            case IDoorGetter: return "door";
            case IContainerGetter: return "container";
            case ILightGetter: return "light";
            case IFurnitureGetter: return "furniture";
            case ITreeGetter: return "tree";
            case IFloraGetter: return "plant";
            case IGrassGetter: return "groundcover";
            case IIdleMarkerGetter or ITextureSetGetter or ISoundMarkerGetter: return "marker";
            case IMiscItemGetter or IWeaponGetter or IArmorGetter or IBookGetter or IIngredientGetter or IIngestibleGetter
                or IAmmunitionGetter or IKeyGetter or IScrollGetter or ISoulGemGetter or ILeveledItemGetter: return "clutter";
            case IActivatorGetter:
                return m.Contains("water") || e.Contains("water") ? "water" : "activator";
        }
        if (b is IStaticGetter or IMoveableStaticGetter)
        {
            if (m == "" || Marker.IsMatch(m) || Marker.IsMatch(e)) return "marker";
            var fn = m[(m.LastIndexOf('/') + 1)..];
            if (m.StartsWith("effects/") || fn.StartsWith("fx")) return "other";
            if (m.Contains("groundcover") || fn.Contains("grass") || fn.Contains("moss") && !fn.Contains("rock")) return "groundcover";
            if (m.Contains("/plants/") || m.Contains("plant") || fn.Contains("fern") || fn.Contains("shrub") || fn.Contains("bush") || fn.Contains("reed")
                || fn.Contains("flower") || fn.Contains("vine") || fn.Contains("ivy") || fn.Contains("tramaroot") || fn.Contains("mushroom") || fn.Contains("lily")
                || m.Contains("/flora/") || m.Contains("/mushrooms/") || fn.Contains("flora")) return "plant";
            if (m.Contains("water") && !m.Contains("waterfall")) return "water";
            if (m.Contains("/trees/") || fn.Contains("tree") || fn.Contains("stump") || fn.StartsWith("log") || fn.Contains("mangrove") || fn.Contains("roots")) return "tree";
            if (m.Contains("/rocks/") || fn.Contains("rock") || fn.Contains("boulder") || fn.Contains("cliff") || fn.Contains("mountain") || fn.Contains("stone")) return "rock";
            if (m.StartsWith("clutter/") || m.Contains("/clutter/") || m.Contains("clutter")) return "clutter";
            if (m.StartsWith("architecture/") || m.Contains("/architecture/") || m.StartsWith("dungeons/") || m.Contains("house") || m.Contains("building") || m.Contains("hut")
                || m.Contains("tower") || m.Contains("wall") || m.Contains("dock") || m.Contains("bridge") || m.Contains("stair") || m.Contains("roof")
                || m.Contains("temple") || m.Contains("pyramid") || m.Contains("ship")) return "building";
            return "static";
        }
        return "other";
    }

    // Nordic (decision 0006): a base is Nordic when its model path or editor id names a Nordic culture, hold town or
    // Nordic dungeon kit, whatever plugin carries it; or when it is one of Skyrim's own masters' architecture pieces
    // (Skyrim's towns are Nordic) outside the non-Nordic kits (Dwemer, Dunmer, Imperial, Ayleid, Falmer).
    static readonly Regex NordicTok = new(@"nord|draugr|dragonclaw|dragonpriest|sovngarde|skaal|barrow|whiterun|windhelm|riften|solitude|markarth|falkreath|winterhold|dawnstar|morthal|riverwood|rorikstead|ivarstead|helgen|dragonsreach|highhrothgar|throat ?of ?the ?world|jarl|stormcloak|farmhouse|skyrimhouse|wrcastle|wrhouse|whhouse|solhouse|rifhouse|mrkhouse", RegexOptions.IgnoreCase);
    static readonly Regex NotNordicKit = new(@"dwemer|dwarven|dunmer|ravenrock|telvanni|imperial|impcastle|ayleid|falmer|daedric|redguard|argonian|khajiit", RegexOptions.IgnoreCase);
    public static bool Nordic(FormKey fk, string? model, string? edid)
    {
        var m = model ?? ""; var e = edid ?? "";
        if (NordicTok.IsMatch(m) || NordicTok.IsMatch(e)) return !NotNordicKit.IsMatch(m) || NordicTok.IsMatch(e) && !NotNordicKit.IsMatch(e);
        return Vanilla.Contains(fk.ModKey.FileName.String.ToLowerInvariant()) && m.StartsWith("architecture/") && !NotNordicKit.IsMatch(m);
    }

    // ---- writing --------------------------------------------------------------------------------------------------

    sealed class Writer
    {
        readonly Loaded L; readonly Job job;
        public readonly HashSet<FormKey> Bases = new(), Npcs = new();
        public readonly Dictionary<string, object> Counts = new() { ["refs"] = 0 };
        readonly Dictionary<string, int> kinds = new(), perSpace = new();
        public Writer(Loaded l, Job j) { L = l; job = j; Counts["refs_by_kind"] = kinds; Counts["refs_by_space"] = perSpace; }

        public float[]? Anchor(Space ext)
        {
            var ps = ext.Refs.Values.Select(v => Pos(v.rec)).Where(p => p != null).Select(p => p!.Value).ToList();
            if (job.Areas.Count > 0) return new[] { job.Areas[0].x, job.Areas[0].y, 0f };
            if (ps.Count == 0) return null;
            return new[] { ps.Average(p => p.X), ps.Average(p => p.Y), ps.Average(p => p.Z) }.Select(f => (float)f).ToArray();
        }

        public void WriteSpace(Space sp, Exterior? ex, List<Space> all)
        {
            var dir = Path.Combine(job.Out, "spaces", sp.Id);
            Directory.CreateDirectory(dir);
            var spaceOf = new Dictionary<FormKey, string>();
            foreach (var s in all) foreach (var k in s.Refs.Keys) spaceOf[k] = s.Id;
            int n = 0, doors = 0;
            using (var o = new StreamWriter(Path.Combine(dir, "refs.jsonl")))
                foreach (var (fk, (r, from, cell)) in sp.Refs.OrderBy(k => k.Key.ModKey.FileName.String).ThenBy(k => k.Key.ID))
                {
                    var row = RefRow(fk, r, from, cell, spaceOf);
                    if (row == null) continue;
                    if (row.ContainsKey("door")) doors++;
                    o.WriteLine(JsonSerializer.Serialize(row, Js)); n++;
                }
            Counts["refs"] = (int)Counts["refs"] + n; perSpace[sp.Id] = n;
            Counts[$"doors.{sp.Id}"] = doors;
            if (job.Navmesh)
                using (var o = new StreamWriter(Path.Combine(dir, "navmesh.jsonl")))
                    foreach (var (fk, (nm, cell)) in sp.Navs.OrderBy(k => k.Key.ID))
                        if (nm.Data is { } d)
                        {
                            o.WriteLine(JsonSerializer.Serialize(new Dictionary<string, object?>
                            {
                                ["id"] = Key(fk), ["cell"] = cell is { } c ? new[] { c.Item1, c.Item2 } : null,
                                ["verts"] = d.Vertices.Select(v => new[] { v.X, v.Y, v.Z }).ToList(),
                                ["tris"] = d.Triangles.Select(t => new[] { t.Vertices.X, t.Vertices.Y, t.Vertices.Z, (int)t.Flags, t.CoverFlags }).ToList(),
                                ["tri_edges"] = d.Triangles.Select(t => new[] { t.EdgeLink_0_1, t.EdgeLink_1_2, t.EdgeLink_2_0 }).ToList(),
                                ["edge_links"] = d.EdgeLinks.Select(e => new { mesh = KeyN(e.Mesh.FormKey), tri = e.TriangleIndex }).ToList(),
                                ["door_links"] = d.DoorTriangles.Select(e => new { tri = e.TriangleBeforeDoor, door = KeyN(e.Door.FormKey) }).ToList(),
                            }, Js));
                            Counts["navmeshes"] = (Counts.TryGetValue("navmeshes", out var c0) ? (int)c0 : 0) + 1;
                        }
            var space = new Dictionary<string, object?> { ["space_id"] = sp.Id, ["type"] = sp.Type, ["refs"] = n, ["doors"] = doors };
            if (sp.Cell is { } ic)
            {
                space["key"] = Key(ic.FormKey); space["name"] = ic.Name?.String; space["plugin"] = sp.From;
                space["cells"] = new[] { Key(ic.FormKey) };
                space["water"] = ic.Flags.HasFlag(Cell.Flag.HasWater) ? new { default_height = ic.WaterHeight, type = KeyN(ic.Water.FormKey) } : null;
                space["light"] = Dump(ic.Lighting); space["lighting_template"] = KeyN(ic.LightingTemplate.FormKey);
                space["owner"] = KeyN(ic.Owner.FormKey); space["flags"] = ic.Flags.ToString();
            }
            else if (ex != null)
            {
                space["name"] = L.WorldRec?.Name?.String;
                space["cells"] = ex.Cells.Keys.OrderBy(c => c.Item2).ThenBy(c => c.Item1).Select(c => new[] { c.Item1, c.Item2 }).ToList();
                space["water"] = new { default_height = L.WorldRec?.LandDefaults?.DefaultWaterHeight, type = KeyN(L.WorldRec?.Water.FormKey ?? FormKey.Null) };
                if (job.Terrain) space["terrain"] = WriteTerrain(dir, ex, space);
            }
            File.WriteAllText(Path.Combine(dir, "space.json"), JsonSerializer.Serialize(space, new JsonSerializerOptions { WriteIndented = true }));
        }

        Dictionary<string, object?>? RefRow(FormKey fk, IMajorRecordGetter r, string from, (int, int)? cell, Dictionary<FormKey, string> spaceOf)
        {
            var bk = BaseOf(r);
            var (b, _) = Resolve(L, bk);
            IPlacementGetter? pl = r switch { IPlacedObjectGetter p => p.Placement, IPlacedNpcGetter p => p.Placement, _ => r.GetType().GetProperty("Placement")?.GetValue(r) as IPlacementGetter };
            if (pl == null) return null;
            var kind = r is IPlacedNpcGetter ? "actor" : KindOfBase(b);
            if (!bk.IsNull) Bases.Add(bk);
            if (r is IPlacedNpcGetter && b is INpcGetter) Npcs.Add(bk);
            kinds[kind] = kinds.GetValueOrDefault(kind) + 1;
            var flags = new List<string>();
            var raw = r.MajorRecordFlagsRaw;
            if ((raw & 0x400) != 0) flags.Add("persistent");
            if ((raw & 0x800) != 0) flags.Add("initially_disabled");
            if ((raw & 0x8000) != 0) flags.Add("visible_when_distant");
            if ((raw & 0x10000) != 0) flags.Add("high_priority_lod");
            if ((raw & 0x40000000) != 0) flags.Add("no_respawn");
            if ((raw & 0x20000000) != 0) flags.Add("multibound");
            var row = new Dictionary<string, object?>
            {
                ["id"] = Key(fk), ["edid"] = r.EditorID, ["base"] = KeyN(bk), ["kind"] = kind,
                ["pos"] = new[] { pl.Position.X, pl.Position.Y, pl.Position.Z },
                ["rot"] = new[] { pl.Rotation.X, pl.Rotation.Y, pl.Rotation.Z },
                ["scale"] = (r.GetType().GetProperty("Scale")?.GetValue(r) as float?) ?? 1f,
                ["layer"] = job.Layer, ["flags"] = flags, ["src"] = from,
            };
            if (cell is { } c) row["cell"] = new[] { c.Item1, c.Item2 };
            if (r is IPlacedObjectGetter po)
            {
                if (po.IsOpenByDefault) flags.Add("open_by_default");
                if (po.IsIgnoredBySandbox) flags.Add("ignored_by_sandbox");
                if (po.TeleportDestination is { } t)
                    row["door"] = new Dictionary<string, object?>
                    {
                        ["to_space"] = spaceOf.GetValueOrDefault(t.Door.FormKey), ["to_ref"] = KeyN(t.Door.FormKey),
                        ["to_pos"] = new[] { t.Position.X, t.Position.Y, t.Position.Z }, ["to_rot"] = new[] { t.Rotation.X, t.Rotation.Y, t.Rotation.Z },
                        ["flags"] = t.Flags.ToString(),
                    };
                if (po.Owner.FormKey is { IsNull: false } ow) row["owner"] = new { owner = Key(ow), rank = po.FactionRank };
                if (po.Lock is { } lk) row["lock"] = new { level = lk.Level.ToString(), key = KeyN(lk.Key.FormKey), flags = lk.Flags.ToString() };
                if (po.LinkedReferences.Count > 0) row["linked"] = po.LinkedReferences.Select(x => new { @ref = KeyN(x.Reference.FormKey), keyword = KeyN(x.KeywordOrReference.FormKey) }).ToList();
                if (po.EnableParent is { } ep) row["enable_parent"] = new { @ref = KeyN(ep.Reference.FormKey), flags = ep.Flags.ToString() };
                if (po.MapMarker is { } mm) row["map_marker"] = Dump(mm);
                if (po.Primitive is { } prim) row["primitive"] = Dump(prim);
                if (po.Radius is { } rad) row["radius"] = rad;
                if (po.LocationRefTypes is { Count: > 0 } lr) row["loc_ref_types"] = lr.Select(x => KeyN(x.FormKey)).ToList();
                if (po.ItemCount is { } ic) row["count"] = ic;
            }
            else if (r is IPlacedNpcGetter pn)
            {
                if (pn.IsIgnoredBySandbox) flags.Add("ignored_by_sandbox");
                if (pn.Owner.FormKey is { IsNull: false } ow) row["owner"] = new { owner = Key(ow), rank = pn.FactionRank };
                if (pn.LinkedReferences.Count > 0) row["linked"] = pn.LinkedReferences.Select(x => new { @ref = KeyN(x.Reference.FormKey), keyword = KeyN(x.KeywordOrReference.FormKey) }).ToList();
                if (pn.EnableParent is { } ep) row["enable_parent"] = new { @ref = KeyN(ep.Reference.FormKey), flags = ep.Flags.ToString() };
                if (pn.Patrol is { } pat) row["patrol"] = Dump(pat);
                if (pn.PersistentLocation.FormKey is { IsNull: false } plc) row["persistent_location"] = Key(plc);
                if (pn.MerchantContainer.FormKey is { IsNull: false } mc) row["merchant_container"] = Key(mc);
            }
            return row;
        }

        // terrain.f32: per cell in terrain.json's order, 33x33 float32 world Z, row-major south to north, west to east
        object WriteTerrain(string dir, Exterior ex, Dictionary<string, object?> space)
        {
            var cells = new List<object>();
            var ltex = new Dictionary<FormKey, object?>();
            var grassBased = new HashSet<string>();
            using var f = new BinaryWriter(File.Create(Path.Combine(dir, "terrain.f32")));
            int i = 0;
            var defW = L.WorldRec?.LandDefaults?.DefaultWaterHeight;
            foreach (var gp in ex.Cells.Keys.OrderBy(c => c.Item2).ThenBy(c => c.Item1))
            {
                var (cell, from) = ex.Cells[gp];
                ex.Land.TryGetValue(gp, out var land);
                var row = new Dictionary<string, object?> { ["cell"] = new[] { gp.Item1, gp.Item2 }, ["key"] = Key(cell.FormKey), ["edid"] = cell.EditorID, ["plugin"] = from };
                var hasWater = cell.Flags.HasFlag(Cell.Flag.HasWater);
                row["water"] = hasWater ? new { height = cell.WaterHeight ?? defW, type = KeyN(cell.Water.FormKey.IsNull ? (L.WorldRec?.Water.FormKey ?? FormKey.Null) : cell.Water.FormKey) } : null;
                row["regions"] = cell.Regions?.Select(x => KeyN(x.FormKey)).ToList();
                if (land?.VertexHeightMap is { } hm)
                {
                    row["heights_index"] = i++;
                    float rowStart = hm.Offset * 8;
                    for (var r = 0; r < V; r++)
                    {
                        rowStart += hm.HeightMap[0, r] * 8;
                        var v = rowStart;
                        f.Write(v);
                        for (var c = 1; c < V; c++) { v += hm.HeightMap[c, r] * 8; f.Write(v); }
                    }
                    var layers = new List<object>();
                    foreach (var l in land.Layers ?? (IReadOnlyList<IBaseLayerGetter>)Array.Empty<IBaseLayerGetter>())
                    {
                        var tk = l.Header?.Texture.FormKey ?? FormKey.Null;
                        if (!tk.IsNull && !ltex.ContainsKey(tk)) ltex[tk] = LtexRow(tk, grassBased);
                        if (l is IAlphaLayerGetter al)
                        {
                            var a = new byte[289];
                            foreach (var p in al.AlphaLayerData ?? Array.Empty<IAlphaLayerDataGetter>())
                                if (p.Position < 289) a[p.Position] = (byte)Math.Clamp(Math.Round(p.Opacity * 255), 0, 255);
                            layers.Add(new { quad = l.Header!.Quadrant.ToString(), layer = (int)l.Header.LayerNumber, tex = KeyN(tk), alpha = Convert.ToBase64String(a) });
                        }
                        else layers.Add(new { quad = l.Header?.Quadrant.ToString(), layer = -1, tex = KeyN(tk) });
                    }
                    row["layers"] = layers;
                    if (land.VertexColors is { } vc)
                    {
                        var b = new byte[V * V * 3];
                        for (var r = 0; r < V; r++) for (var c = 0; c < V; c++) { var p = vc[c, r]; var o = (r * V + c) * 3; b[o] = p.X; b[o + 1] = p.Y; b[o + 2] = p.Z; }
                        row["vertex_colours"] = Convert.ToBase64String(b);
                    }
                }
                cells.Add(row);
            }
            var placedGrass = kinds.GetValueOrDefault("groundcover");
            space["groundcover"] = new
            {
                placed_refs = placedGrass,
                generated_from_land_textures = grassBased.Count > 0,
                note = grassBased.Count > 0
                    ? "Grass is generated by the game from the land textures' grass lists (ltex[].grasses), not placed as refs; show it from the texture layers."
                    : "No land texture in these cells carries grass: ground cover is only what is placed as refs.",
            };
            var terrain = new Dictionary<string, object?> { ["cells"] = cells, ["ltex"] = ltex.ToDictionary(k => Key(k.Key), k => k.Value) };
            File.WriteAllText(Path.Combine(dir, "terrain.json"), JsonSerializer.Serialize(terrain, Js));
            Counts["terrain_cells"] = i;
            return new { file = "terrain.json", heights = "terrain.f32", cells_with_land = i };
        }

        object? LtexRow(FormKey tk, HashSet<string> grassBased)
        {
            var (r, from) = Resolve(L, tk);
            if (r is not ILandscapeTextureGetter lt) return null;
            var (ts, _) = Resolve(L, lt.TextureSet.FormKey);
            var grasses = lt.Grasses.Select(g =>
            {
                var (gr, _) = Resolve(L, g.FormKey);
                return new { key = Key(g.FormKey), edid = gr?.EditorID, model = ModelOf(gr) };
            }).ToList();
            if (grasses.Count > 0) grassBased.Add(Key(tk));
            return new
            {
                edid = lt.EditorID, plugin = from,
                diffuse = (ts as ITextureSetGetter)?.Diffuse?.DataRelativePath.Path.Replace('\\', '/').ToLowerInvariant(),
                normal = (ts as ITextureSetGetter)?.NormalOrGloss?.DataRelativePath.Path.Replace('\\', '/').ToLowerInvariant(),
                grasses,
            };
        }

        public void WriteBases()
        {
            using var o = new StreamWriter(Path.Combine(job.Out, "bases.jsonl"));
            var nordic = 0;
            foreach (var fk in Bases.OrderBy(k => k.ModKey.FileName.String).ThenBy(k => k.ID))
            {
                var (b, from) = Resolve(L, fk);
                var model = ModelOf(b);
                var row = new Dictionary<string, object?>
                {
                    ["key"] = Key(fk), ["edid"] = b?.EditorID, ["type"] = b?.GetType().Name.Replace("BinaryOverlay", ""),
                    ["kind"] = KindOfBase(b), ["name"] = (b as INamedGetter)?.Name, ["model"] = model, ["plugin"] = from,
                };
                if ((b as IObjectBoundedGetter)?.ObjectBounds is { } ob)
                    row["bounds"] = new[] { new[] { ob.First.X, ob.First.Y, ob.First.Z }, new[] { ob.Second.X, ob.Second.Y, ob.Second.Z } };
                if (b is IKeywordedGetter<IKeywordGetter> kw && kw.Keywords is { } ks)
                    row["keywords"] = ks.Select(k => Resolve(L, k.FormKey).rec?.EditorID ?? Key(k.FormKey)).ToList();
                var nd = Nordic(fk, model, b?.EditorID);
                row["nordic"] = nd; if (nd) nordic++;
                switch (b)
                {
                    case IDoorGetter d: row["door"] = new { flags = d.Flags.ToString() }; break;
                    case IFurnitureGetter fu: row["furniture"] = new { markers = Dump(fu.Markers), flags = fu.Flags?.ToString(), keyword = KeyN(fu.InteractionKeyword.FormKey) }; break;
                    case ILightGetter li: row["light"] = new { radius = li.Radius, colour = new[] { li.Color.R, li.Color.G, li.Color.B }, flags = li.Flags.ToString(), fov = li.FOV }; break;
                    case IContainerGetter co: row["container"] = new { flags = co.Flags.ToString(), items = co.Items?.Count ?? 0 }; break;
                    case ITreeGetter tr: row["tree"] = new { ingredient = KeyN(tr.Ingredient.FormKey) }; break;
                    case IFloraGetter fl: row["flora"] = new { ingredient = KeyN(fl.Ingredient.FormKey) }; break;
                    case IActivatorGetter ac when ac.WaterType.FormKey is { IsNull: false } wt: row["water"] = Key(wt); break;
                }
                o.WriteLine(JsonSerializer.Serialize(row, Js));
            }
            Counts["bases"] = Bases.Count; Counts["bases_nordic"] = nordic;
        }

        public void WriteNpcs()
        {
            using var o = new StreamWriter(Path.Combine(job.Out, "npcs.jsonl"));
            foreach (var fk in Npcs.OrderBy(k => k.ModKey.FileName.String).ThenBy(k => k.ID))
            {
                if (Resolve(L, fk).rec is not INpcGetter n) continue;
                var cls = Resolve(L, n.Class.FormKey).rec as IClassGetter;
                var factions = n.Factions.Select(f => (f, rec: Resolve(L, f.Faction.FormKey).rec as IFactionGetter)).ToList();
                var services = new Dictionary<string, object?>();
                foreach (var (f, fr) in factions)
                {
                    if (fr == null) continue;
                    if (fr.Flags.HasFlag(Faction.FactionFlag.Vendor))
                        services["vendor"] = new { faction = Key(fr.FormKey), edid = fr.EditorID, buy_sell_list = KeyN(fr.VendorBuySellList.FormKey), container = KeyN(fr.MerchantContainer.FormKey), values = Dump(fr.VendorValues), location = Dump(fr.VendorLocation) };
                    if ((fr.EditorID ?? "").Contains("Innkeeper", StringComparison.OrdinalIgnoreCase)) services["innkeeper"] = Key(fr.FormKey);
                    if ((fr.EditorID ?? "").Contains("Guard", StringComparison.OrdinalIgnoreCase)) services["guard"] = Key(fr.FormKey);
                }
                if (cls?.Teaches is { } t && cls.MaxTrainingLevel > 0) services["trainer"] = new { skill = t.ToString(), max = cls.MaxTrainingLevel };
                var pkgs = new List<object?>();
                void AddPkg(FormKey pk, string via)
                {
                    var (p, pf) = Resolve(L, pk);
                    if (p is IPackageGetter pg) pkgs.Add(PackageRow(pg, pf, via));
                    else if (p is IFormListGetter fl) foreach (var x in fl.Items) AddPkg(x.FormKey, via + ":" + (fl.EditorID ?? Key(fl.FormKey)));
                    else pkgs.Add(new { key = KeyN(pk), via, unresolved = true });
                }
                foreach (var pk in n.Packages) AddPkg(pk.FormKey, "npc");
                if (!n.DefaultPackageList.FormKey.IsNull) AddPkg(n.DefaultPackageList.FormKey, "default_list");
                var row = new Dictionary<string, object?>
                {
                    ["key"] = Key(fk), ["edid"] = n.EditorID, ["name"] = n.Name?.String, ["short_name"] = n.ShortName?.String,
                    ["race"] = KeyN(n.Race.FormKey), ["race_edid"] = Resolve(L, n.Race.FormKey).rec?.EditorID,
                    ["sex"] = n.Configuration.Flags.HasFlag(NpcConfiguration.Flag.Female) ? "female" : "male",
                    ["flags"] = n.Configuration.Flags.ToString(), ["level"] = Dump(n.Configuration.Level),
                    ["template"] = KeyN(n.Template.FormKey), ["template_flags"] = n.Configuration.TemplateFlags.ToString(),
                    ["class"] = KeyN(n.Class.FormKey), ["class_edid"] = cls?.EditorID,
                    ["factions"] = factions.Select(x => new { faction = Key(x.f.Faction.FormKey), edid = x.rec?.EditorID, rank = x.f.Rank }).ToList(),
                    ["crime_faction"] = KeyN(n.CrimeFaction.FormKey),
                    ["voice"] = KeyN(n.Voice.FormKey), ["outfit"] = KeyN(n.DefaultOutfit.FormKey), ["sleep_outfit"] = KeyN(n.SleepingOutfit.FormKey),
                    ["ai"] = Dump(n.AIData), ["keywords"] = n.Keywords?.Select(k => Resolve(L, k.FormKey).rec?.EditorID ?? Key(k.FormKey)).ToList(),
                    ["services"] = services, ["packages"] = pkgs,
                    ["plugin"] = Resolve(L, fk).from,
                };
                o.WriteLine(JsonSerializer.Serialize(row, Js));
            }
            Counts["actors"] = Npcs.Count;
        }

        object PackageRow(IPackageGetter p, string from, string via) => new Dictionary<string, object?>
        {
            ["key"] = Key(p.FormKey), ["edid"] = p.EditorID, ["plugin"] = from, ["via"] = via,
            ["template"] = KeyN(p.PackageTemplate.FormKey), ["template_edid"] = Resolve(L, p.PackageTemplate.FormKey).rec?.EditorID,
            ["type"] = p.Type.ToString(), ["flags"] = p.Flags.ToString(), ["interrupt"] = p.InterruptOverride.ToString(),
            ["interrupt_flags"] = p.InterruptFlags.ToString(), ["speed"] = p.PreferredSpeed.ToString(),
            ["schedule"] = new { month = p.ScheduleMonth, day_of_week = p.ScheduleDayOfWeek.ToString(), date = p.ScheduleDate, hour = p.ScheduleHour, minute = p.ScheduleMinute, duration_minutes = p.ScheduleDurationInMinutes },
            ["data"] = Dump(p.Data), ["procedure_tree"] = Dump(p.ProcedureTree), ["idles"] = Dump(p.IdleAnimations),
            ["conditions"] = Dump(p.Conditions), ["owner_quest"] = KeyN(p.OwnerQuest.FormKey), ["combat_style"] = KeyN(p.CombatStyle.FormKey),
            ["on_begin"] = Dump(p.OnBegin), ["on_end"] = Dump(p.OnEnd), ["on_change"] = Dump(p.OnChange),
        };
    }

    // A record's sub-object as plain JSON: links as keys, enums as names, vectors as arrays; Mutagen's plumbing skipped.
    static readonly HashSet<string> Skip = new() { "Registration", "StaticRegistration", "BinaryWriteTranslator", "Versioning", "VirtualMachineAdapter", "FormVersion", "Version2", "VersionControl", "MajorRecordFlagsRaw", "IsCompressed", "IsDeleted", "Type" };
    public static object? Dump(object? o, int depth = 0)
    {
        switch (o)
        {
            case null: return null;
            case string or bool or byte or sbyte or short or ushort or int or uint or long or ulong or float or double: return o;
            case Enum e: return e.ToString();
            case FormKey fk: return KeyN(fk);
            case IFormLinkGetter l: return KeyN(l.FormKey);
            case P3Float p: return new[] { p.X, p.Y, p.Z };
            case P3Int16 p: return new[] { p.X, p.Y, p.Z };
            case P2Float p: return new[] { p.X, p.Y };
            case System.Drawing.Color c: return new[] { c.R, c.G, c.B };
            case ITranslatedStringGetter ts: return ts.String;
        }
        if (depth > 8) return o.ToString();
        var t = o.GetType();
        if (t.IsGenericType && t.Name.StartsWith("ReadOnlyMemorySlice")) return null;
        if (o is IDictionary d)
        {
            var r = new Dictionary<string, object?>();
            foreach (DictionaryEntry kv in d) r[kv.Key.ToString()!] = Dump(kv.Value, depth + 1);
            return r;
        }
        var ifaces = t.GetInterfaces();
        var roDict = ifaces.FirstOrDefault(i => i.IsGenericType && i.GetGenericTypeDefinition() == typeof(IReadOnlyDictionary<,>));
        if (roDict != null)
        {
            var r = new Dictionary<string, object?>();
            foreach (var kv in (IEnumerable)o)
            {
                var kt = kv.GetType();
                r[kt.GetProperty("Key")!.GetValue(kv)!.ToString()!] = Dump(kt.GetProperty("Value")!.GetValue(kv), depth + 1);
            }
            return r;
        }
        if (o is IEnumerable en) return en.Cast<object?>().Select(x => Dump(x, depth + 1)).ToList();
        var res = new Dictionary<string, object?> { ["$type"] = t.Name.Replace("BinaryOverlay", "") };
        foreach (var p in t.GetProperties())
        {
            if (Skip.Contains(p.Name) || p.Name.StartsWith("Unknown") || p.Name.StartsWith("Unused") || p.GetIndexParameters().Length > 0) continue;
            object? v;
            try { v = p.GetValue(o); } catch { continue; }
            if (v is null) continue;
            res[p.Name] = Dump(v, depth + 1);
        }
        return res;
    }
}
