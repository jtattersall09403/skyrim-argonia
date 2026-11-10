// The new world's atmosphere (walk 5, lane A): our own weathers, image spaces, volumetric lighting, climate and the
// regions' weather lists, all from <plugin dir>/atmosphere.json (tools/newworld/atmosphere.py; the numbers and their
// reasons are in docs/design/atmosphere.md). Called by NewWorld.cs's writer; also a study tool.
//   atmos study <out.json> <plugin paths...>   every WTHR, CLMT, IMGS, VOLI and REGN weather list, as JSON (read only)
// Records are copies of vanilla forms (the load order's winner), re-coloured and re-timed (never edits of vanilla
// forms), at the fixed form ids the spec gives (atmosphere.py BASE: IMGS 0x80000.., VOLI 0x80400.., WTHR 0x80500..,
// CLMT 0x80600), so the owner's `fw` commands stay the same from build to build (the ForeignCopy range starts at
// 0x900 and ends near 0x3000; cells are 0x100000..).
// A field in the spec is a dotted property path on the Mutagen record ("SkyUpper.Day", "FogDistanceDayFar",
// "DirectionalAmbientLightingColors.Sunrise.DirectionalXPlus", "Cinematic.Saturation"); a colour is [r, g, b].
using System.Collections;
using System.Reflection;
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Noggog;

static class NewWorldAtmosphere
{
    public static int Run(string[] a) => a[0] switch
    {
        "study" => Study(a[1], a[2..]),
        "mist" => MistStudy(a[1], a[2], a[3], int.Parse(a[4]), int.Parse(a[5]), int.Parse(a[6]), int.Parse(a[7])),
        "sample" => Sample(a[1], a[2], a[3]),
        _ => throw new ArgumentException("atmos study <out.json> <plugins...> | atmos mist <out.json> <plugin> <world edid> x0 x1 y0 y1 | atmos sample <plugin dir> <Data> <out.esm>"),
    };

    // A small ArgoniaNewWorld.esm holding only what the atmosphere writes (the worldspace with its climate, the 24
    // regions with their weather lists, our weathers, image spaces and volumetric lightings), built by the same
    // Build() the world writer calls: the off-game proof of the records without writing the 2.6 GB world.
    static int Sample(string plugDir, string data, string outPath)
    {
        var modKey = ModKey.FromFileName("ArgoniaNewWorld.esm");
        var mod = new SkyrimMod(modKey, SkyrimRelease.SkyrimSE);
        mod.ModHeader.Flags |= SkyrimModHeader.HeaderFlag.Master;
        var allowed = new[] { "Skyrim.esm", "Update.esm", "Black Marsh.esm" }.Select(f => ModKey.FromFileName(f)).ToList();
        using var fc = new ForeignCopy(mod, allowed, data, 0x900);
        var (clim, lists) = Build(mod, fc, plugDir);
        var ws = new Worldspace(new FormKey(modKey, 0x800), SkyrimRelease.SkyrimSE)
        {
            EditorID = "ArgoniaBlackMarsh", Climate = new FormLinkNullable<IClimateGetter>(clim),
        };
        mod.Worldspaces.Add(ws);
        var spec = JsonDocument.Parse(File.ReadAllText(Path.Combine(plugDir, "atmosphere.json"))).RootElement;
        uint rid = 0x880;
        foreach (var r in spec.GetProperty("regions").EnumerateObject())
            mod.Regions.Add(new Region(new FormKey(modKey, rid++), SkyrimRelease.SkyrimSE)
            {
                EditorID = "ANW_Region_" + r.Name.Replace("-", "_"), Worldspace = new FormLinkNullable<IWorldspaceGetter>(ws.FormKey),
                Weather = new RegionWeather { Weathers = new ExtendedList<WeatherType>(lists(r.Name)) },
            });
        var dir = Path.Combine(Path.GetDirectoryName(Path.GetFullPath(outPath))!, ".writing"); Directory.CreateDirectory(dir);
        var tmp = Path.Combine(dir, Path.GetFileName(outPath));
        mod.BeginWrite.ToPath(tmp).WithLoadOrder(allowed.Append(modKey).ToList()).WithDataFolder(data)
            .WithExtraIncludedMasters(allowed[0], allowed[1]).SingleThread().Write();
        File.Move(tmp, outPath, true);
        Console.WriteLine($"atmos sample: {outPath}: {mod.Weathers.Count} WTHR, {mod.ImageSpaces.Count} IMGS, {mod.VolumetricLightings.Count} VOLI, {mod.Climates.Count} CLMT, {mod.Regions.Count} REGN");
        return 0;
    }

    // Every FXMist*/FXFog* ref of a worldspace's cells in a box, with the cell's water height, the LAND height under
    // the ref (bilinear on VHGT) and each cell's share of LAND vertices under its water: the mist density over water
    // against land, measured (Hjaalmarch: Tamriel x -20..0, y 10..30).
    static int MistStudy(string outPath, string plugin, string world, int x0, int x1, int y0, int y1)
    {
        using var m = SkyrimMod.CreateFromBinaryOverlay(plugin, SkyrimRelease.SkyrimSE, Survey.NoStrings);
        using var sky = SkyrimMod.CreateFromBinaryOverlay(Path.Combine(Path.GetDirectoryName(Path.GetFullPath(plugin))!, "Skyrim.esm"), SkyrimRelease.SkyrimSE, Survey.NoStrings);
        var stat = new Dictionary<FormKey, string>();
        foreach (var src in new ISkyrimModGetter[] { sky, m })
            foreach (var s in src.EnumerateMajorRecords())
                if (s.EditorID is { } e && (e.StartsWith("FXMist", StringComparison.OrdinalIgnoreCase) || e.StartsWith("FXFog", StringComparison.OrdinalIgnoreCase) || e.StartsWith("FXAmbBlowingFog", StringComparison.OrdinalIgnoreCase)))
                    stat[s.FormKey] = e;
        var ws = m.Worldspaces.First(w => w.EditorID == world);
        float defWater = ws.LandDefaults?.DefaultWaterHeight ?? 0;
        var cells = new List<object>(); var refs = new List<object>();
        foreach (var b in ws.SubCells) foreach (var sb in b.Items) foreach (var c in sb.Items)
        {
            if (c.Grid is null) continue;
            int cx = c.Grid.Point.X, cy = c.Grid.Point.Y;
            if (cx < x0 || cx > x1 || cy < y0 || cy > y1) continue;
            float wl = c.Flags.HasFlag(Cell.Flag.HasWater) ? (c.WaterHeight is float f && f < 1e9 ? f : defWater) : float.NegativeInfinity;
            float[]? h = null;
            if (c.Landscape?.VertexHeightMap is { } vh)
            {
                h = new float[33 * 33]; double row = vh.Offset;
                for (var j = 0; j < 33; j++) { row += vh.HeightMap[0, j]; double v = row; h[j * 33] = (float)(v * 8); for (var i = 1; i < 33; i++) { v += vh.HeightMap[i, j]; h[j * 33 + i] = (float)(v * 8); } }
            }
            int under = h is null ? 0 : h.Count(z => z < wl);
            cells.Add(new { cx, cy, water = float.IsNegativeInfinity(wl) ? (float?)null : wl, water_share = h is null ? (double?)null : under / 1089.0,
                water_type = c.Water.IsNull ? null : c.Water.FormKey.ToString() });
            foreach (var r in c.Temporary.Concat(c.Persistent).OfType<IPlacedObjectGetter>())
            {
                if (!stat.TryGetValue(r.Base.FormKey, out var ed) || r.Placement is null) continue;
                var p = r.Placement.Position;
                float? g = null;
                if (h is not null)
                {
                    double fx = (p.X - cx * 4096.0) / 128, fy = (p.Y - cy * 4096.0) / 128;
                    int i = Math.Clamp((int)fx, 0, 31), j = Math.Clamp((int)fy, 0, 31); double ax = fx - i, ay = fy - j;
                    g = (float)((h[j * 33 + i] * (1 - ax) + h[j * 33 + i + 1] * ax) * (1 - ay) + (h[(j + 1) * 33 + i] * (1 - ax) + h[(j + 1) * 33 + i + 1] * ax) * ay);
                }
                refs.Add(new { cx, cy, edid = ed, x = p.X, y = p.Y, z = p.Z, ground = g, water = float.IsNegativeInfinity(wl) ? (float?)null : wl, scale = r.Scale ?? 1f,
                    enable_parent = r.EnableParent is not null });
            }
        }
        File.WriteAllText(outPath, JsonSerializer.Serialize(new { plugin = Path.GetFileName(plugin), world, box = new[] { x0, x1, y0, y1 }, cells, refs }));
        Console.WriteLine($"atmos mist: {refs.Count} mist refs in {cells.Count} cells -> {outPath}");
        return 0;
    }

    // ---- the writer's hook --------------------------------------------------------------------------------------
    // Builds every record of atmosphere.json into `mod`; returns the climate and each region's weather list.
    public static (FormKey Climate, Func<string, IEnumerable<WeatherType>> RegionWeathers) Build(SkyrimMod mod, ForeignCopy fc, string plugDir)
    {
        var spec = JsonDocument.Parse(File.ReadAllText(Path.Combine(plugDir, "atmosphere.json"))).RootElement;
        FormKey K(uint id) => new(mod.ModKey, id);
        var keys = new Dictionary<string, FormKey>();  // our editor id -> form key
        FormKey Src(string s) { var sp = s.Split(':'); return keys.TryGetValue(s, out var k) ? k : fc.Find(sp[0], sp[1]).FormKey; }
        foreach (var e in spec.GetProperty("imagespaces").EnumerateArray())
        {
            var sp = e.GetProperty("copy").GetString()!.Split(':');
            var r = (ImageSpace)fc.Find(sp[0], sp[1]).Duplicate(K(e.GetProperty("formid").GetUInt32()));
            r.EditorID = e.GetProperty("edid").GetString();
            Apply(r, e.GetProperty("set"));
            mod.ImageSpaces.Add(r); keys[r.EditorID!] = r.FormKey;
        }
        foreach (var e in spec.GetProperty("volumetric").EnumerateArray())
        {
            var sp = e.GetProperty("copy").GetString()!.Split(':');
            var r = (VolumetricLighting)fc.Find(sp[0], sp[1]).Duplicate(K(e.GetProperty("formid").GetUInt32()));
            r.EditorID = e.GetProperty("edid").GetString();
            Apply(r, e.GetProperty("set"));
            mod.VolumetricLightings.Add(r); keys[r.EditorID!] = r.FormKey;
        }
        foreach (var e in spec.GetProperty("weathers").EnumerateArray())
        {
            var sp = e.GetProperty("copy").GetString()!.Split(':');
            var w = (Weather)fc.Find(sp[0], sp[1]).Duplicate(K(e.GetProperty("formid").GetUInt32()));
            w.EditorID = e.GetProperty("edid").GetString();
            Apply(w, e.GetProperty("set"));
            if (e.TryGetProperty("imagespaces", out var isp))
            {
                w.ImageSpaces ??= new WeatherImageSpaces();
                w.ImageSpaces.Sunrise.SetTo(keys[isp.GetProperty("Sunrise").GetString()!]);
                w.ImageSpaces.Day.SetTo(keys[isp.GetProperty("Day").GetString()!]);
                w.ImageSpaces.Sunset.SetTo(keys[isp.GetProperty("Sunset").GetString()!]);
                w.ImageSpaces.Night.SetTo(keys[isp.GetProperty("Night").GetString()!]);
            }
            if (e.TryGetProperty("volumetric", out var vl))
            {
                w.VolumetricLighting ??= new WeatherVolumetricLighting();
                w.VolumetricLighting.Sunrise.SetTo(keys[vl.GetProperty("Sunrise").GetString()!]);
                w.VolumetricLighting.Day.SetTo(keys[vl.GetProperty("Day").GetString()!]);
                w.VolumetricLighting.Sunset.SetTo(keys[vl.GetProperty("Sunset").GetString()!]);
                w.VolumetricLighting.Night.SetTo(keys[vl.GetProperty("Night").GetString()!]);
            }
            mod.Weathers.Add(w); keys[w.EditorID!] = w.FormKey;
        }
        IEnumerable<WeatherType> List(JsonElement l) => l.EnumerateArray().Select(x => new WeatherType
        {
            Weather = new FormLink<IWeatherGetter>(Src(x[0].GetString()!)), Chance = x[1].GetInt32(),
        }).ToList();
        var c = spec.GetProperty("climate");
        var csp = c.GetProperty("copy").GetString()!.Split(':');
        var clim = (Climate)fc.Find(csp[0], csp[1]).Duplicate(K(c.GetProperty("formid").GetUInt32()));
        clim.EditorID = c.GetProperty("edid").GetString();
        clim.WeatherTypes = new ExtendedList<WeatherType>(List(c.GetProperty("weathers")));
        TimeOnly T(string k) => TimeOnly.Parse(c.GetProperty(k).GetString()!);
        clim.SunriseBegin = T("sunrise_begin"); clim.SunriseEnd = T("sunrise_end");
        clim.SunsetBegin = T("sunset_begin"); clim.SunsetEnd = T("sunset_end");
        mod.Climates.Add(clim);
        var regions = spec.GetProperty("regions");
        return (clim.FormKey, rid => List(regions.GetProperty(rid)));
    }

    // Sets each "path": value of `set` on the record by reflection; a missing path or a wrong type throws.
    static void Apply(object rec, JsonElement set)
    {
        foreach (var p in set.EnumerateObject())
        {
            var parts = p.Name.Split('.');
            object cur = rec;
            for (var i = 0; i < parts.Length - 1; i++)
            {
                var pi = cur.GetType().GetProperty(parts[i]) ?? throw new InvalidDataException($"{rec.GetType().Name}: no {p.Name}");
                var next = pi.GetValue(cur);
                if (next is null)
                {
                    next = System.Activator.CreateInstance(pi.PropertyType.IsInterface ? pi.PropertyType.Assembly.GetType(pi.PropertyType.Namespace + "." + pi.PropertyType.Name[1..].Replace("Getter", ""))! : pi.PropertyType)!;
                    pi.SetValue(cur, next);
                }
                cur = next;
            }
            var leaf = cur.GetType().GetProperty(parts[^1]) ?? throw new InvalidDataException($"{rec.GetType().Name}: no {p.Name}");
            leaf.SetValue(cur, Convert(p.Value, leaf.PropertyType, p.Name));
        }
    }

    static object Convert(JsonElement v, Type t, string name)
    {
        var u = Nullable.GetUnderlyingType(t) ?? t;
        if (u == typeof(System.Drawing.Color)) return System.Drawing.Color.FromArgb(v[0].GetInt32(), v[1].GetInt32(), v[2].GetInt32());
        if (u == typeof(float)) return v.GetSingle();
        if (u == typeof(byte)) return v.GetByte();
        if (u == typeof(sbyte)) return v.GetSByte();
        if (u == typeof(int)) return v.GetInt32();
        if (u == typeof(ushort)) return v.GetUInt16();
        if (u == typeof(bool)) return v.GetBoolean();
        if (u == typeof(Percent)) return new Percent(v.GetDouble());
        throw new InvalidDataException($"{name}: cannot set a {t.Name}");
    }

    // ---- study --------------------------------------------------------------------------------------------------
    static int Study(string outPath, string[] plugins)
    {
        var res = new Dictionary<string, object>();
        foreach (var p in plugins)
        {
            using var m = SkyrimMod.CreateFromBinaryOverlay(p, SkyrimRelease.SkyrimSE, Survey.NoStrings);
            var edid = new Dictionary<FormKey, string>();
            var recs = new Dictionary<string, List<object>>();
            void Add(string sig, IEnumerable<IMajorRecordGetter> rs)
            {
                var l = recs[sig] = new List<object>();
                foreach (var r in rs) l.Add(Dump(r, 0));
            }
            Add("WTHR", m.Weathers); Add("CLMT", m.Climates); Add("IMGS", m.ImageSpaces); Add("VOLI", m.VolumetricLightings);
            Add("REGN", m.Regions.Where(r => r.Weather is not null));
            Add("WRLD", m.Worldspaces);
            res[Path.GetFileName(p)] = recs;
        }
        File.WriteAllText(outPath, JsonSerializer.Serialize(res, new JsonSerializerOptions { WriteIndented = false }));
        Console.WriteLine($"atmos study: {outPath}");
        return 0;
    }

    static readonly HashSet<string> Skip = new() { "SubCells", "TopCell", "Version2", "VersionControl", "FormVersion", "MajorRecordFlagsRaw",
        "Registration", "StaticRegistration", "Map", "Objects", "Grasses", "Sounds", "Land", "Landscape", "OffsetData", "LargeReferences",
        "MaxHeight", "Regions", "RegionAreas", "Cloud", "Clouds", "CloudTextures", "LandDefaults" };

    static object? Dump(object? o, int depth)
    {
        if (o is null) return null;
        if (depth > 5) return o.ToString();
        switch (o)
        {
            case System.Drawing.Color c: return new[] { (int)c.R, (int)c.G, (int)c.B };
            case string or bool or float or double or int or uint or short or ushort or byte or sbyte or long: return o;
            case Enum e: return e.ToString();
            case Percent pc: return pc.Value;
            case TimeOnly t: return t.ToString("HH:mm");
            case FormKey fk: return fk.ToString();
            case IFormLinkGetter fl: return fl.IsNull ? null : fl.FormKey.ToString();
            case P2Float p2: return new[] { p2.X, p2.Y };
            case P3Float p3: return new[] { p3.X, p3.Y, p3.Z };
            case ReadOnlyMemorySlice<byte> b: return $"{b.Length} bytes";
            case byte[] b2: return $"{b2.Length} bytes";
        }
        var type = o.GetType();
        if (o is IEnumerable en && type.Name != "String")
        {
            var l = new List<object?>();
            foreach (var x in en) { l.Add(Dump(x, depth + 1)); if (l.Count > 40) break; }
            return l;
        }
        var d = new Dictionary<string, object?>();
        foreach (var pi in type.GetProperties(BindingFlags.Public | BindingFlags.Instance))
        {
            if (pi.GetIndexParameters().Length > 0 || Skip.Contains(pi.Name)) continue;
            object? v;
            try { v = pi.GetValue(o); } catch { continue; }
            if (v is null) continue;
            d[pi.Name] = Dump(v, depth + 1);
        }
        return d;
    }
}
