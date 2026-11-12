using System.Text.Json;
using System.Text.RegularExpressions;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Cache;
using Mutagen.Bethesda.Plugins.Order;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Noggog;

// mine <job.json> <out.jsonl>: one row per candidate source place of the job's "mine" plugins, read as the load
// order's winner (the job's plugins in order, masters first; a missing master is skipped and named). A candidate is a
// location record (LCTN) the plugin adds, with the cells that name it, its children that carry no map marker of their
// own, the interiors behind its doors, and its map marker; plus every map marker no such location claims. Each row
// holds the signals the matcher scores (tools/places/sources_mine.py): kind signals, footprint, counts, people, water,
// culture and tileset tags.
static class Miner
{
    sealed class Ext { public string Ws = ""; public (int, int) G; public ICellGetter Cell = null!; public string From = ""; }

    static readonly Regex Enemy = new(@"^enc|bandit|draugr|necro|forsworn|vampire|falmer|warlock|skeleton|spriggan|troll|wolf|bear|spider|chaurus|mudcrab|slaughterfish|skeever|dwarven|sphere|centurion|hagraven|witch|conjurer|mage(?!.*(guild|college))|thalmor(?!.*(embassy))|automat|undead|zombie|ghost|wraith|hostile|boss|sabre|wisp|lurker|riekling|netch|ashhopper|daedra|atronach|dremora|crocodile|lizard|slaughter|hunter_enemy|raider|pirate|smuggler|cultist|lich", RegexOptions.IgnoreCase);
    static readonly (string tag, Regex rx)[] Tags =
    {
        ("ayleid", new(@"ayleid|aylied|welkynd|varla", RegexOptions.IgnoreCase)),
        ("dwemer", new(@"dwemer|dwarven|dwarf", RegexOptions.IgnoreCase)),
        ("imperial", new(@"imperial|impcastle|impfort|/imp", RegexOptions.IgnoreCase)),
        ("nordic", new(@"nordic|/nord|draugr|barrow|whiterun|windhelm|solitude|riften|markarth|farmhouse", RegexOptions.IgnoreCase)),
        ("dunmer", new(@"dunmer|ravenrock|telvanni|redoran|ashland|velothi|daedricshrine|solstheim|dlc02/architecture", RegexOptions.IgnoreCase)),
        ("argonian", new(@"argon|xanmeer|blackmarsh|black ?marsh|/bm|hist|stilt|lilmoth|murkmire|kotm|saxhleel", RegexOptions.IgnoreCase)),
        ("bosmer", new(@"valenwood|bosmer|graht", RegexOptions.IgnoreCase)),
        ("redguard", new(@"redguard|hammerfell", RegexOptions.IgnoreCase)),
        ("khajiit", new(@"khajiit|elsweyr", RegexOptions.IgnoreCase)),
        ("falmer", new(@"falmer", RegexOptions.IgnoreCase)),
        ("daedric", new(@"daedric|oblivion", RegexOptions.IgnoreCase)),
        ("orc", new(@"orcish|/orc", RegexOptions.IgnoreCase)),
        ("mine", new(@"mine|minecart|mineshaft|ore|scaffold", RegexOptions.IgnoreCase)),
        ("cave", new(@"dungeons/caves|/cave|caveg|cavel|cavem|caves/", RegexOptions.IgnoreCase)),
        ("farm", new(@"farm|barn|windmill|crop|plow|haystack|cabbage|wheat|chicken", RegexOptions.IgnoreCase)),
        ("ship", new(@"ship|wreck|boat|hull", RegexOptions.IgnoreCase)),
        ("dock", new(@"dock|pier|jetty", RegexOptions.IgnoreCase)),
        ("camp", new(@"tent|camp|bedroll|lean", RegexOptions.IgnoreCase)),
        ("fort", new(@"fort|castle|battlement|rampart|palisade", RegexOptions.IgnoreCase)),
        ("lighthouse", new(@"lighthouse|beacon", RegexOptions.IgnoreCase)),
        ("lumber", new(@"lumber|sawmill|woodmill|logpile|timber", RegexOptions.IgnoreCase)),
        ("ruin", new(@"ruin|rubble|broken|collapsed", RegexOptions.IgnoreCase)),
        ("shrine", new(@"shrine|altar|statue|temple", RegexOptions.IgnoreCase)),
    };

    public static int Run(string jobPath, string outPath)
    {
        var j = JsonDocument.Parse(File.ReadAllText(jobPath)).RootElement;
        var search = j.GetProperty("search").EnumerateArray().Select(e => e.GetString()!).ToList();
        var mine = j.GetProperty("mine").EnumerateArray().Select(e => e.GetString()!).ToHashSet(StringComparer.OrdinalIgnoreCase);
        var cluster = j.TryGetProperty("cluster", out var ce) && ce.ValueKind == JsonValueKind.True;
        var exclude = j.TryGetProperty("exclude", out var xe) ? xe.EnumerateArray().Select(e => e.GetString()!).ToHashSet(StringComparer.OrdinalIgnoreCase) : new();
        var mods = new List<ISkyrimModGetter>(); var byName = new HashSet<string>(StringComparer.OrdinalIgnoreCase); var missing = new List<string>();
        string? Find(string f)
        {
            foreach (var d in search)
            {
                if (!Directory.Exists(d)) continue;
                var hit = Directory.EnumerateFiles(d).FirstOrDefault(p => string.Equals(Path.GetFileName(p), f, StringComparison.OrdinalIgnoreCase));
                if (hit != null) return hit;
            }
            return null;
        }
        void Add(string f)
        {
            if (!byName.Add(f)) return;
            var p = Find(f);
            if (p == null) { missing.Add(f); return; }
            var m = SkyrimMod.CreateFromBinaryOverlay(p, SkyrimRelease.SkyrimSE, Extractor.NoStrings);
            foreach (var mr in m.ModHeader.MasterReferences) Add(mr.Master.FileName);
            mods.Add(m);
            Console.Error.WriteLine($"loaded {p}");
        }
        foreach (var e in j.GetProperty("plugins").EnumerateArray()) Add(e.GetString()!);
        var cache = new LoadOrder<ISkyrimModGetter>(mods).ToImmutableLinkCache();
        var baseCache = new Dictionary<FormKey, IMajorRecordGetter?>();
        IMajorRecordGetter? Res(FormKey fk)
        {
            if (fk.IsNull) return null;
            if (baseCache.TryGetValue(fk, out var v)) return v;
            return baseCache[fk] = cache.TryResolve(fk, typeof(IMajorRecordGetter), out var r) ? r : null;
        }

        // winning exterior cells, their refs (every plugin's, last wins), and every map marker
        var ext = new Dictionary<(FormKey, (int, int)), Ext>();
        var extRefs = new Dictionary<(FormKey, (int, int)), Dictionary<FormKey, IMajorRecordGetter>>();
        var refAt = new Dictionary<FormKey, (FormKey ws, (int, int) g)>();
        var wsEdid = new Dictionary<FormKey, string>();
        var wsWater = new Dictionary<FormKey, float?>();
        void PutRef(FormKey ws, (int, int) g, IMajorRecordGetter r)
        {
            if (refAt.TryGetValue(r.FormKey, out var was) && extRefs.TryGetValue(was, out var wd)) wd.Remove(r.FormKey);
            if (r.IsDeleted) { refAt.Remove(r.FormKey); return; }
            if (!extRefs.TryGetValue((ws, g), out var d)) extRefs[(ws, g)] = d = new();
            d[r.FormKey] = r; refAt[r.FormKey] = (ws, g);
        }
        foreach (var m in mods)
            foreach (var w in m.Worldspaces)
            {
                wsEdid[w.FormKey] = w.EditorID ?? ""; wsWater[w.FormKey] = w.LandDefaults?.DefaultWaterHeight;
                if (w.TopCell is { } top)
                    foreach (var r in top.Persistent.Concat(top.Temporary))
                        if (Pos(r) is { } p) PutRef(w.FormKey, ((int)Math.Floor(p.X / 4096), (int)Math.Floor(p.Y / 4096)), r);
                foreach (var b in w.SubCells) foreach (var sb in b.Items) foreach (var c in sb.Items)
                {
                    if (c.Grid is not { } g) continue;
                    var gp = (g.Point.X, g.Point.Y);
                    ext[(w.FormKey, gp)] = new Ext { Ws = Extractor.Key(w.FormKey), G = gp, Cell = c, From = m.ModKey.FileName.String };
                    foreach (var r in c.Persistent.Concat(c.Temporary)) PutRef(w.FormKey, gp, r);
                }
            }
        // interiors: winning copy and union of refs
        var intCell = new Dictionary<FormKey, ICellGetter>();
        var intFrom = new Dictionary<FormKey, string>();
        var intRefs = new Dictionary<FormKey, Dictionary<FormKey, IMajorRecordGetter>>();
        var refInt = new Dictionary<FormKey, FormKey>();
        foreach (var m in mods)
            foreach (var b in m.Cells.Records) foreach (var sb in b.SubBlocks) foreach (var c in sb.Cells)
            {
                intCell[c.FormKey] = c; intFrom[c.FormKey] = m.ModKey.FileName.String;
                if (!intRefs.TryGetValue(c.FormKey, out var d)) intRefs[c.FormKey] = d = new();
                foreach (var r in c.Persistent.Concat(c.Temporary))
                {
                    if (r.IsDeleted) d.Remove(r.FormKey); else d[r.FormKey] = r;
                    refInt[r.FormKey] = c.FormKey;
                }
            }

        // winning locations; cells by location
        var locs = new Dictionary<FormKey, ILocationGetter>();
        foreach (var m in mods) foreach (var l in m.Locations) locs[l.FormKey] = l;
        var extByLoc = new Dictionary<FormKey, List<(FormKey, (int, int))>>();
        foreach (var (k, e) in ext)
            if (e.Cell.Location.FormKey is { IsNull: false } lk) { if (!extByLoc.TryGetValue(lk, out var l)) extByLoc[lk] = l = new(); l.Add(k); }
        var intByLoc = new Dictionary<FormKey, List<FormKey>>();
        foreach (var (k, c) in intCell)
            if (c.Location.FormKey is { IsNull: false } lk) { if (!intByLoc.TryGetValue(lk, out var l)) intByLoc[lk] = l = new(); l.Add(k); }
        var children = locs.Values.Where(l => !l.ParentLocation.FormKey.IsNull).GroupBy(l => l.ParentLocation.FormKey).ToDictionary(g => g.Key, g => g.ToList());
        var markers = new Dictionary<FormKey, (IPlacedObjectGetter r, FormKey ws, (int, int) g)>();
        foreach (var (k, d) in extRefs) foreach (var r in d.Values) if (r is IPlacedObjectGetter po && po.MapMarker != null) markers[po.FormKey] = (po, k.Item1, k.Item2);
        var markerOfLoc = new Dictionary<FormKey, FormKey>();
        foreach (var l in locs.Values)
            if (l.WorldLocationMarkerRef.FormKey is { IsNull: false } mk && markers.ContainsKey(mk)) markerOfLoc[l.FormKey] = mk;

        var cellCounts = new Dictionary<object, Dictionary<string, object>>();
        using var o = new StreamWriter(outPath);
        int n = 0;
        var claimedMarkers = new HashSet<FormKey>();
        var usedExt = new HashSet<(FormKey, (int, int))>();

        void Emit(string id, string plugin, ILocationGetter? loc, (IPlacedObjectGetter r, FormKey ws, (int, int) g)? mk,
                  List<(FormKey, (int, int))> cells, List<FormKey> ints0, List<string> keywords, string? parent)
        {
            // interiors: those that name the location, then those behind doors of the gathered spaces (<= 3 hops)
            var ints = new List<FormKey>(ints0); var seen = new HashSet<FormKey>(ints0);
            var frontier = cells.SelectMany(c => extRefs.TryGetValue(c, out var d) ? d.Values : Enumerable.Empty<IMajorRecordGetter>())
                .Concat(ints0.SelectMany(c => intRefs[c].Values)).ToList();
            for (int hop = 0; hop < 3 && frontier.Count > 0; hop++)
            {
                var next = new List<IMajorRecordGetter>();
                foreach (var r in frontier.OfType<IPlacedObjectGetter>())
                    if (r.TeleportDestination is { } t && !t.Door.FormKey.IsNull && refInt.TryGetValue(t.Door.FormKey, out var ck) && seen.Add(ck))
                    {
                        var cl = intCell[ck].Location.FormKey;
                        if (!cl.IsNull && loc != null && cl != loc.FormKey && !(children.TryGetValue(loc.FormKey, out var ch) && ch.Any(x => x.FormKey == cl))
                            && markerOfLoc.ContainsKey(cl)) continue;  // another place's interior
                        ints.Add(ck); next.AddRange(intRefs[ck].Values);
                    }
                frontier = next;
            }
            var counts = new Dictionary<string, int>();
            var tags = new Dictionary<string, int>();
            var npcs = new List<string>();
            int enemies = 0, residents = 0, doorsOut = 0, wetCells = 0, landCells = 0;
            float minx = float.MaxValue, miny = float.MaxValue, maxx = float.MinValue, maxy = float.MinValue;
            void Tally(IMajorRecordGetter r, bool exterior)
            {
                var b = Res(Extractor.BaseOf(r));
                var kind = r is IPlacedNpcGetter ? "actor" : Extractor.KindOfBase(b);
                counts[kind] = counts.GetValueOrDefault(kind) + 1;
                counts["refs"] = counts.GetValueOrDefault("refs") + 1;
                if (r is IPlacedNpcGetter)
                {
                    var e = b?.EditorID ?? "";
                    if (b is ILeveledNpcGetter || Enemy.IsMatch(e)) enemies++; else residents++;
                    return;
                }
                if (r is IPlacedObjectGetter po && po.TeleportDestination is { } t && !t.Door.FormKey.IsNull && exterior) doorsOut++;
                if (kind is "building" or "static" or "door" or "furniture" or "container" or "clutter" or "activator")
                {
                    var mdl = (Extractor.ModelOf(b) ?? "") + " " + (b?.EditorID ?? "");
                    foreach (var (tag, rx) in Tags) if (rx.IsMatch(mdl)) tags[tag] = tags.GetValueOrDefault(tag) + 1;
                }
                if (exterior && kind is "building" or "door" or "furniture" && Pos(r) is { } p)
                { minx = Math.Min(minx, p.X); maxx = Math.Max(maxx, p.X); miny = Math.Min(miny, p.Y); maxy = Math.Max(maxy, p.Y); }
            }
            foreach (var c in cells)
            {
                if (extRefs.TryGetValue(c, out var d)) foreach (var r in d.Values) Tally(r, true);
                var e = ext[c];
                if (e.Cell.Landscape?.VertexHeightMap is { } hm)
                {
                    landCells++;
                    var wh = e.Cell.Flags.HasFlag(Cell.Flag.HasWater) ? e.Cell.WaterHeight ?? wsWater.GetValueOrDefault(c.Item1) : null;
                    if (wh is float w && MinHeight(hm) < w) wetCells++;
                }
            }
            foreach (var ic in ints) foreach (var r in intRefs[ic].Values) Tally(r, false);
            var wsk = mk?.ws ?? (cells.Count > 0 ? cells[0].Item1 : FormKey.Null);
            object? marker = mk is { } m ? new
            {
                key = Extractor.Key(m.r.FormKey), type = m.r.MapMarker!.Type.ToString(), name = m.r.MapMarker.Name?.String,
                x = m.r.Placement?.Position.X, y = m.r.Placement?.Position.Y, cell = new[] { m.g.Item1, m.g.Item2 },
            } : null;
            var row = new Dictionary<string, object?>
            {
                ["candidate_id"] = id, ["plugin"] = plugin,
                ["location"] = loc == null ? null : Extractor.Key(loc.FormKey), ["edid"] = loc?.EditorID ?? m_edid(mk),
                ["name"] = loc?.Name?.String ?? mk?.r.MapMarker?.Name?.String, ["parent"] = parent,
                ["keywords"] = keywords, ["marker"] = marker,
                ["worldspace"] = wsk.IsNull ? null : Extractor.Key(wsk), ["worldspace_edid"] = wsk.IsNull ? null : wsEdid.GetValueOrDefault(wsk),
                ["cells"] = cells.Select(c => new[] { c.Item2.Item1, c.Item2.Item2 }).OrderBy(c => c[1]).ThenBy(c => c[0]).ToList(),
                ["interiors"] = ints.Select(c => intCell[c].EditorID ?? Extractor.Key(c)).ToList(),
                ["interior_names"] = ints.Select(c => intCell[c].Name?.String).Where(s => !string.IsNullOrEmpty(s)).Distinct().Take(12).ToList(),
                ["counts"] = counts, ["doors_out"] = doorsOut, ["interior_count"] = ints.Count,
                ["npcs"] = enemies + residents, ["enemies"] = enemies, ["residents"] = residents,
                ["land_cells"] = landCells, ["wet_cells"] = wetCells,
                ["footprint_m"] = minx <= maxx ? new[] { MathF.Round((maxx - minx) / 70f), MathF.Round((maxy - miny) / 70f) } : null,
                ["centre"] = minx <= maxx ? new[] { (minx + maxx) / 2, (miny + maxy) / 2 } : (marker != null ? new[] { mk!.Value.r.Placement!.Position.X, mk.Value.r.Placement!.Position.Y } : null),
                ["tags"] = tags,
            };
            o.WriteLine(JsonSerializer.Serialize(row));
            foreach (var c in cells) usedExt.Add(c);
            n++;
        }
        static string? m_edid((IPlacedObjectGetter r, FormKey ws, (int, int) g)? mk) => mk?.r.EditorID;

        // 1. locations the mined plugins add
        foreach (var l in locs.Values.OrderBy(l => l.FormKey.ModKey.FileName.String).ThenBy(l => l.FormKey.ID))
        {
            var plugin = l.FormKey.ModKey.FileName.String;
            if (!mine.Contains(plugin) || exclude.Contains(l.EditorID ?? "")) continue;
            // gather the location and its marker-less descendants
            var group = new List<FormKey> { l.FormKey }; var q = new Queue<FormKey>(group);
            while (q.Count > 0)
                foreach (var ch in children.GetValueOrDefault(q.Dequeue()) ?? new())
                    if (!markerOfLoc.ContainsKey(ch.FormKey) && !group.Contains(ch.FormKey)) { group.Add(ch.FormKey); q.Enqueue(ch.FormKey); }
            var cells = group.SelectMany(g => extByLoc.GetValueOrDefault(g) ?? new()).Distinct().ToList();
            var ints = group.SelectMany(g => intByLoc.GetValueOrDefault(g) ?? new()).Distinct().ToList();
            (IPlacedObjectGetter, FormKey, (int, int))? mk = markerOfLoc.TryGetValue(l.FormKey, out var mkk) ? markers[mkk] : null;
            if (cells.Count == 0 && ints.Count == 0 && mk == null) continue;
            if (mk is { } mm) { claimedMarkers.Add(mm.Item1.FormKey); if (cells.Count == 0) cells.Add((mm.Item2, mm.Item3)); }
            if (cells.Count > 40) continue;  // a hold or a region, not a place
            if (cells.Count == 0 && ints.Count > 0 && mk == null && !l.ParentLocation.FormKey.IsNull && markerOfLoc.ContainsKey(l.ParentLocation.FormKey)) continue;  // a room of a marked place
            var kws = l.Keywords?.Select(k => Res(k.FormKey)?.EditorID ?? Extractor.Key(k.FormKey)).ToList() ?? new();
            var parent = l.ParentLocation.FormKey.IsNull ? null : (locs.TryGetValue(l.ParentLocation.FormKey, out var pl) ? pl.EditorID : Extractor.Key(l.ParentLocation.FormKey));
            Emit(Id(plugin, l.EditorID ?? Extractor.Key(l.FormKey)), plugin, l, mk, cells, ints, kws, parent);
        }
        // 2. built-up clusters of the mined plugins' own refs that no location names (a plugin that places towns
        //    by cells alone): 8-connected exterior cells holding >= 6 of its buildings or a door to an interior
        var clusterMarkers = new HashSet<FormKey>();
        if (cluster)
        {
            var dense = new Dictionary<(FormKey, (int, int)), int>();
            foreach (var (k, d) in extRefs)
            {
                if (usedExt.Contains(k)) continue;
                int b = 0;
                foreach (var r in d.Values)
                {
                    if (!mine.Contains(r.FormKey.ModKey.FileName.String) || r is IPlacedNpcGetter) continue;
                    var kind = Extractor.KindOfBase(Res(Extractor.BaseOf(r)));
                    if (kind == "building") b++;
                    else if (r is IPlacedObjectGetter po && po.TeleportDestination is { } t && refInt.ContainsKey(t.Door.FormKey)) b += 6;
                }
                if (b >= 6 && ext.ContainsKey(k)) dense[k] = b;
            }
            var done = new HashSet<(FormKey, (int, int))>();
            foreach (var start in dense.Keys.OrderBy(k => k.Item2.Item1).ThenBy(k => k.Item2.Item2))
            {
                if (!done.Add(start)) continue;
                var comp = new List<(FormKey, (int, int))> { start }; var q = new Queue<(FormKey, (int, int))>(comp);
                while (q.Count > 0)
                {
                    var (ws, (x, y)) = q.Dequeue();
                    for (int dx = -1; dx <= 1; dx++) for (int dy = -1; dy <= 1; dy++)
                    {
                        var nb = (ws, (x + dx, y + dy));
                        if (dense.ContainsKey(nb) && done.Add(nb)) { comp.Add(nb); q.Enqueue(nb); }
                    }
                }
                if (comp.Count > 64) Console.Error.WriteLine($"cluster of {comp.Count} cells at {start.Item2} kept whole");
                // its name: a marker in or beside it, else its interiors' or cells' commonest name
                var compSet = comp.ToHashSet();
                var mk = markers.Values.Where(m => m.ws == start.Item1 && comp.Any(c => Math.Abs(c.Item2.Item1 - m.g.Item1) <= 1 && Math.Abs(c.Item2.Item2 - m.g.Item2) <= 1))
                    .OrderByDescending(m => compSet.Contains((m.ws, m.g)) ? 1 : 0).Cast<(IPlacedObjectGetter, FormKey, (int, int))?>().FirstOrDefault();
                if (mk is { } mm) clusterMarkers.Add(mm.Item1.FormKey);
                var nm = comp.Select(c => ext[c].Cell.Name?.String ?? ext[c].Cell.EditorID).Where(s => !string.IsNullOrEmpty(s))
                    .GroupBy(s => Regex.Replace(s!, @"\d+$|exterior|ext$", "", RegexOptions.IgnoreCase)).OrderByDescending(g => g.Count()).Select(g => g.Key).FirstOrDefault();
                var plugin = comp.SelectMany(c => extRefs[c].Values).Select(r => r.FormKey.ModKey.FileName.String).Where(mine.Contains)
                    .GroupBy(s => s).OrderByDescending(g => g.Count()).First().Key;
                var label = mk?.Item1.MapMarker?.Name?.String ?? nm ?? $"{wsEdid[start.Item1]} {start.Item2.Item1} {start.Item2.Item2}";
                Emit(Id(plugin, "cluster." + label + $".{start.Item2.Item1}.{start.Item2.Item2}"), plugin, null, mk, comp, new(),
                     new() { "cluster", "cell-name:" + (nm ?? "") }, null);
            }
        }
        // 3. map markers no location or cluster claims (a marker's own cell and its neighbours)
        foreach (var (k, (r, ws, g)) in markers)
        {
            var plugin = r.FormKey.ModKey.FileName.String;
            if (!mine.Contains(plugin) || claimedMarkers.Contains(k) || clusterMarkers.Contains(k)) continue;
            var cells = new List<(FormKey, (int, int))>();
            for (int dx = -1; dx <= 1; dx++) for (int dy = -1; dy <= 1; dy++)
            {
                var c = (ws, (g.Item1 + dx, g.Item2 + dy));
                if (!ext.ContainsKey(c)) continue;
                var cl = ext[c].Cell.Location.FormKey;
                if (dx == 0 && dy == 0 || cl.IsNull) cells.Add(c);
            }
            Emit(Id(plugin, "marker." + (r.MapMarker!.Name?.String ?? r.EditorID ?? $"{k.ID:X6}")), plugin, null, (r, ws, g), cells, new(), new(), null);
        }
        Console.Error.WriteLine($"mined {n} candidates; masters not found: {string.Join(", ", missing)}");
        File.WriteAllText(outPath + ".missing", string.Join("\n", missing));
        return 0;
    }

    static string Id(string plugin, string edid)
    {
        var p = Regex.Replace(Path.GetFileNameWithoutExtension(plugin).ToLowerInvariant(), "[^a-z0-9]+", "");
        return p + "." + Regex.Replace(edid.ToLowerInvariant(), "[^a-z0-9.]+", "-").Trim('-');
    }

    static float MinHeight(ILandscapeVertexHeightMapGetter hm)
    {
        float min = float.MaxValue, rowStart = hm.Offset * 8;
        for (var r = 0; r < 33; r++)
        {
            rowStart += hm.HeightMap[0, r] * 8; var v = rowStart; min = Math.Min(min, v);
            for (var c = 1; c < 33; c++) { v += hm.HeightMap[c, r] * 8; min = Math.Min(min, v); }
        }
        return min;
    }

    static P3Float? Pos(IMajorRecordGetter r) => r switch
    {
        IPlacedObjectGetter p => p.Placement?.Position,
        IPlacedNpcGetter n => n.Placement?.Position,
        IPlacedGetter g => (g.GetType().GetProperty("Placement")?.GetValue(g) as IPlacementGetter)?.Position,
        _ => null,
    };
}
