// nwverify: the facts tools/newworld/verify.py judges, read back from ArgoniaNewWorld.esm as the game reads it (nw-02
// step 12). Judges nothing itself; every number is written for the Python side.
//   nwverify dump <ArgoniaNewWorld.esm> <Data dir> <out dir>
// Writes <out>/header.json (masters, load errors, links, worldspace, climate, regions, waters, textures, the coc cell),
// <out>/cells.tsv (one row per exterior cell) and <out>/refs.tsv.gz (one row per placed object, with the LAND's ground
// height and slope under it, bilinear on the cell's VHGT).
using System.IO.Compression;
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;

static class NewWorldVerify
{
    const SkyrimRelease Rel = SkyrimRelease.SkyrimSE;
    const int V = 33, CELL = 4096;
    static readonly string[] Masters = { "Skyrim.esm", "Update.esm", "Black Marsh.esm" };

    public static int Run(string[] a) => a[0] switch
    {
        "dump" => Dump(a[1], a[2], a[3]),
        _ => throw new ArgumentException("nwverify dump <esm> <Data> <out>"),
    };

    record Base(string Sig, string Edid, string Model, string From);

    static string Sig(IMajorRecordGetter r) => r.GetType().Name.Replace("BinaryOverlay", "");

    static int Dump(string esmPath, string data, string outDir)
    {
        Directory.CreateDirectory(outDir);
        var errors = new List<string>();
        void Err(string s) { if (errors.Count < 50) errors.Add(s); }
        using var mod = SkyrimMod.CreateFromBinaryOverlay(esmPath, Rel, Survey.NoStrings);
        var mods = new List<ISkyrimModGetter>();
        foreach (var m in Masters)
        {
            var p = Path.Combine(data, m);
            if (File.Exists(p)) mods.Add(SkyrimMod.CreateFromBinaryOverlay(p, Rel, Survey.NoStrings));
            else Err($"master file {p} not found");
        }
        mods.Add(mod);
        // every record of the masters and ours: what a link resolves to (later wins)
        var recs = new Dictionary<FormKey, Base>();
        foreach (var m in mods)
            foreach (var r in m.EnumerateMajorRecords())
            {
                try { recs[r.FormKey] = new Base(Sig(r), r.EditorID ?? "", (r as IModeledGetter)?.Model?.File.ToString() ?? "", m.ModKey.FileName); }
                catch (Exception e) { Err($"{m.ModKey}: {e.GetType().Name} {e.Message}"); }
            }
        var allowed = Masters.Select(m => ModKey.FromFileName(m)).Append(mod.ModKey).ToHashSet();
        var masterList = mod.ModHeader.MasterReferences.Select(m => m.Master.FileName.String).ToList();
        long links = 0, foreignLinks = 0, unresolved = 0, records = 0;
        var foreignEx = new List<string>(); var unresEx = new List<string>();
        var counts = new Dictionary<string, int>();
        foreach (var r in mod.EnumerateMajorRecords())
        {
            try
            {
                records++;
                var s = Sig(r); counts[s] = counts.GetValueOrDefault(s) + 1;
                foreach (var l in r.EnumerateFormLinks())
                {
                    if (l.IsNull) continue;
                    links++;
                    if (!allowed.Contains(l.FormKey.ModKey)) { foreignLinks++; if (foreignEx.Count < 10) foreignEx.Add($"{r.FormKey} -> {l.FormKey}"); }
                    else if (!recs.ContainsKey(l.FormKey)) { unresolved++; if (unresEx.Count < 10) unresEx.Add($"{r.FormKey} -> {l.FormKey}"); }
                }
            }
            catch (Exception e) { Err($"{r.FormKey}: {e.GetType().Name} {e.Message}"); }
        }
        string Ed(FormKey k) => recs.TryGetValue(k, out var b) ? b.Edid : k.ToString();
        var ltex = mod.LandscapeTextures.ToDictionary(t => t.FormKey);
        var txst = mod.TextureSets.ToDictionary(t => t.FormKey);
        foreach (var m in mods.Take(mods.Count - 1)) foreach (var t in m.TextureSets) txst.TryAdd(t.FormKey, t);
        var grassy = ltex.Values.Where(t => t.Grasses?.Count > 0).Select(t => t.FormKey).ToHashSet();
        var wss = mod.Worldspaces.ToList();
        var header = new Dictionary<string, object?>
        {
            ["esm"] = esmPath, ["bytes"] = new FileInfo(esmPath).Length,
            ["esm_flag"] = mod.ModHeader.Flags.HasFlag(SkyrimModHeader.HeaderFlag.Master),
            ["masters"] = masterList, ["records"] = records, ["record_counts"] = counts,
            ["links"] = links, ["foreign_links"] = foreignLinks, ["foreign_examples"] = foreignEx,
            ["unresolved_links"] = unresolved, ["unresolved_examples"] = unresEx,
            ["worldspaces"] = wss.Select(w => w.EditorID).ToList(),
            ["ltex"] = ltex.Values.Select(t => new
            {
                edid = t.EditorID, grasses = t.Grasses?.Count ?? 0,
                diffuse = txst.TryGetValue(t.TextureSet.FormKey, out var ts) ? ts.Diffuse?.ToString() : null,
            }).ToList(),
            ["grass_density"] = mod.Grasses.GroupBy(g => g.EditorID ?? g.FormKey.ToString()).ToDictionary(g => g.Key, g => (int)g.Max(x => x.Density)),
            ["regions"] = mod.Regions.Select(r => new
            {
                edid = r.EditorID, weathers = r.Weather?.Weathers?.Select(w => Ed(w.Weather.FormKey)).ToList(),
                map_name = r.Map?.Name?.ToString(),
            }).ToList(),
            ["waters"] = mod.Waters.Select(w => new { edid = w.EditorID }).ToList(),
            ["navi"] = mod.NavigationMeshInfoMaps.Sum(n => n.MapInfos.Count),
            ["errors"] = errors,
        };
        if (wss.Count == 0) { File.WriteAllText(Path.Combine(outDir, "header.json"), JsonSerializer.Serialize(header)); Console.WriteLine("nwverify: no worldspace"); return 0; }
        var ws = wss[0];
        var clim = ws.Climate.IsNull ? null : mods.SelectMany(m => m.Climates).LastOrDefault(c => c.FormKey == ws.Climate.FormKey);
        header["world"] = new
        {
            edid = ws.EditorID, name = ws.Name?.String, climate = ws.Climate.IsNull ? null : Ed(ws.Climate.FormKey),
            climate_weathers = clim?.WeatherTypes.Select(w => new { weather = Ed(w.Weather.FormKey), chance = w.Chance }).ToList(),
            water = ws.Water.IsNull ? null : Ed(ws.Water.FormKey), default_water = ws.LandDefaults?.DefaultWaterHeight,
            map_usable = ws.MapData is { } md ? new[] { md.UsableDimensions.X, md.UsableDimensions.Y } : null,
            map_nw = ws.MapData is { } m1 ? new[] { m1.NorthwestCellCoords.X, m1.NorthwestCellCoords.Y } : null,
            map_se = ws.MapData is { } m2 ? new[] { m2.SoutheastCellCoords.X, m2.SoutheastCellCoords.Y } : null,
            // map markers live in the world's persistent cell (NewWorldMap.cs), which the cell walk below never reads
            map_markers = ws.TopCell?.Persistent.OfType<IPlacedObjectGetter>().Count(r => r.MapMarker is not null) ?? 0,
        };
        object? marker = null; int startCells = 0;
        using var cw = new StreamWriter(Path.Combine(outDir, "cells.tsv"));
        cw.WriteLine("x\ty\tedid\tland\twater\twater_h\tregion\trefs\tnavm\tnavm_tris\tland_quads\tgrass_quads\th_min\th_max\th_mean");
        using var gz = new GZipStream(File.Create(Path.Combine(outDir, "refs.tsv.gz")), CompressionLevel.Fastest);
        using var rw = new StreamWriter(gz);
        // placed actors (ecology): one row each, and every NPC_ record of our file with the level it carries
        using var ew = new StreamWriter(Path.Combine(outDir, "ecology.tsv"));
        ew.WriteLine("cx\tcy\tfid\tx\ty\tz\trz\tbase\tbase_edid\tsig");
        using (var nw = new StreamWriter(Path.Combine(outDir, "eco_npcs.tsv")))
        {
            nw.WriteLine("edid\tkey\tlevel_kind\tlevel\tstats_template\tautocalc");
            foreach (var n in mod.Npcs)
            {
                var lv = n.Configuration.Level;
                var (kind, val) = lv switch { INpcLevelGetter l when l is NpcLevel nl => ("fixed", (double)nl.Level), PcLevelMult pm => ("pc_mult", (double)pm.LevelMult), _ => ("other", 0d) };
                nw.WriteLine($"{n.EditorID}\t{n.FormKey}\t{kind}\t{val}\t{n.Configuration.TemplateFlags.HasFlag(NpcConfiguration.TemplateFlag.Stats)}\t{n.Configuration.Flags.HasFlag(NpcConfiguration.Flag.AutoCalcStats)}");
            }
        }
        rw.WriteLine("cx\tcy\tbase\tsig\tedid\tmodel\tfrom\tx\ty\tz\trx\try\trz\tscale\tground\tgx\tgy\tfid");
        float water = ws.LandDefaults?.DefaultWaterHeight ?? 0;
        foreach (var b in ws.SubCells) foreach (var sb in b.Items) foreach (var c in sb.Items)
        {
            try
            {
                if (c.Grid is null) continue;
                var (x, y) = (c.Grid.Point.X, c.Grid.Point.Y);
                if (c.EditorID == "ArgoniaNWStart") startCells++;
                float[]? dec = null;
                var l = c.Landscape;
                if (l?.VertexHeightMap is { } vh)
                {
                    dec = new float[V * V]; var hm = vh.HeightMap; double row = vh.Offset;
                    for (var j = 0; j < V; j++) { row += hm[0, j]; double v = row; dec[j * V] = (float)(v * 8); for (var i = 1; i < V; i++) { v += hm[i, j]; dec[j * V + i] = (float)(v * 8); } }
                }
                (float g, float gx, float gy) Ground(float px, float py)
                {
                    if (dec is null) return (float.NaN, 0, 0);
                    double u = Math.Clamp((px - x * CELL) / 128.0, 0, 32), w = Math.Clamp((py - y * CELL) / 128.0, 0, 32);
                    int i = Math.Min((int)u, 31), j = Math.Min((int)w, 31); double fu = u - i, fw = w - j;
                    float h00 = dec[j * V + i], h10 = dec[j * V + i + 1], h01 = dec[(j + 1) * V + i], h11 = dec[(j + 1) * V + i + 1];
                    var h = (h00 * (1 - fu) + h10 * fu) * (1 - fw) + (h01 * (1 - fu) + h11 * fu) * fw;
                    var dx = ((h10 - h00) * (1 - fw) + (h11 - h01) * fw) / 128.0; var dy = ((h01 - h00) * (1 - fu) + (h11 - h10) * fu) / 128.0;
                    return ((float)h, (float)dx, (float)dy);
                }
                int landQ = 0, grassQ = 0;
                if (dec is not null && l?.Layers is { } layers)
                    foreach (var g in layers.GroupBy(q => q.Header!.Quadrant))
                    {
                        int qi = g.Key switch { Quadrant.BottomLeft => 0, Quadrant.BottomRight => 1, Quadrant.TopLeft => 2, _ => 3 };
                        int i0 = (qi % 2) * 16, j0 = (qi / 2) * 16; double sum = 0;
                        for (var j = j0; j <= j0 + 16; j++) for (var i = i0; i <= i0 + 16; i++) sum += dec[j * V + i];
                        if (sum / 289 <= water) continue;
                        landQ++;
                        if (g.Any(q => grassy.Contains(q.Header!.Texture.FormKey))) grassQ++;
                    }
                int nref = 0;
                foreach (var r in c.Temporary.Concat(c.Persistent))
                {
                    if (r is IPlacedNpcGetter pn && pn.Placement is { } pp)
                    {
                        recs.TryGetValue(pn.Base.FormKey, out var nb);
                        ew.WriteLine($"{x}\t{y}\t{pn.FormKey.ID:X6}\t{pp.Position.X:F2}\t{pp.Position.Y:F2}\t{pp.Position.Z:F2}\t{pp.Rotation.Z:F5}\t{pn.Base.FormKey}\t{nb?.Edid}\t{nb?.Sig}");
                        continue;
                    }
                    if (r is not IPlacedObjectGetter po || po.Placement is null) continue;
                    var pos = po.Placement.Position; var rot = po.Placement.Rotation;
                    if (po.EditorID == "ArgoniaNWStartMarker")
                    {
                        var gm = Ground(pos.X, pos.Y);
                        marker = new { cell = new[] { x, y }, cell_edid = c.EditorID, pos = new[] { pos.X, pos.Y, pos.Z }, ground = gm.g, water };
                        continue;
                    }
                    if (po.FormKey.ID is >= 0xF00000 and <= 0xFDFFFF)    // an ecology critter: with the actors, not the placed refs
                    {
                        recs.TryGetValue(po.Base.FormKey, out var cb);
                        ew.WriteLine($"{x}\t{y}\t{po.FormKey.ID:X6}\t{pos.X:F2}\t{pos.Y:F2}\t{pos.Z:F2}\t{rot.Z:F5}\t{po.Base.FormKey}\t{cb?.Edid}\t{cb?.Sig}");
                        continue;
                    }
                    nref++;
                    var bk = po.Base.FormKey; recs.TryGetValue(bk, out var bs);
                    var (gh, gx, gy) = Ground(pos.X, pos.Y);
                    rw.WriteLine($"{x}\t{y}\t{bk}\t{bs?.Sig}\t{bs?.Edid}\t{bs?.Model}\t{bs?.From}\t{pos.X:F1}\t{pos.Y:F1}\t{pos.Z:F1}\t{rot.X:F5}\t{rot.Y:F5}\t{rot.Z:F5}\t{po.Scale ?? 1f:F4}\t{gh:F1}\t{gx:F4}\t{gy:F4}\t{po.FormKey.ID:X6}");
                }
                var navs = c.NavigationMeshes.ToList();
                long tris = 0;
                foreach (var n in navs) try { tris += n.Data?.Triangles.Count ?? 0; } catch (Exception e) { Err($"navm {x},{y}: {e.Message}"); }
                var wn = c.Water.IsNull ? "" : Ed(c.Water.FormKey);
                var reg = c.Regions?.FirstOrDefault(); var rn = reg is null ? "" : Ed(reg.FormKey);
                string hs = dec is null ? "\t\t" : $"{dec.Min():F0}\t{dec.Max():F0}\t{dec.Average():F0}";
                cw.WriteLine($"{x}\t{y}\t{c.EditorID}\t{(dec is null ? 0 : 1)}\t{wn}\t{(c.Flags.HasFlag(Cell.Flag.HasWater) ? c.WaterHeight : null)}\t{rn}\t{nref}\t{navs.Count}\t{tris}\t{landQ}\t{grassQ}\t{hs}");
            }
            catch (Exception e) { Err($"cell {c.FormKey}: {e.GetType().Name} {e.Message}"); }
        }
        header["start_cells"] = startCells;
        header["marker"] = marker;
        header["errors"] = errors;
        File.WriteAllText(Path.Combine(outDir, "header.json"), JsonSerializer.Serialize(header, new JsonSerializerOptions { WriteIndented = true }));
        Console.WriteLine($"nwverify dump: {records} records, {links} links, {errors.Count} errors -> {outDir}");
        return 0;
    }
}
