// newworld: the new world's plugin ArgoniaNewWorld.esm from the land shards (tools/newworld/world/land.py), and its
// off-game read-back. Ported from the old ArgoniaGen/LandWorld.cs (ac983185): same LAND layout, no intermediate JSON.
//   newworld write <land/manifest.json> <Data dir> <out.esm>
//   newworld check <out.esm> <land/manifest.json> <Data dir>      (exit 1 on any failure)
// Facts kept from LandWorld.cs (measured on Skyrim.esm's Tamriel): LAND DATA flags 0x1F, compressed; per quadrant
// BottomLeft, BottomRight, TopLeft, TopRight one base layer (0xFFFF); Array2d indexed [x, y], y north from the south;
// blocks 32 x 32 cells, sub-blocks 8 x 8, floor division. VHGT offset is in 8-unit steps.
// Placeholders the later nw-02 steps replace: the ground texture (BM&V's 01MOSS1 on every quadrant), the water type
// (the BM&V BlackMarsh worldspace's), the climate (BM&V's BlackMarshClimate).
using System.Diagnostics;
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;
using Noggog;

static class NewWorld
{
    const SkyrimRelease Rel = SkyrimRelease.SkyrimSE;
    const int V = 33, CELL = 4096;
    const string Esm = "ArgoniaNewWorld.esm", WorldEdid = "ArgoniaBlackMarsh", WorldName = "Black Marsh (Argonia)";
    const string StartCell = "ArgoniaNWStart", StartMarker = "ArgoniaNWStartMarker";
    static readonly FormKey XMarkerHeading = FormKey.Factory("000034:Skyrim.esm");
    static readonly Quadrant[] Quads = { Quadrant.BottomLeft, Quadrant.BottomRight, Quadrant.TopLeft, Quadrant.TopRight };
    // fixed form ids: the bytes depend only on the shards
    const uint IdWorld = 0x800, IdTopCell = 0x801, IdMarker = 0x802, IdCopies = 0x900, IdRegions = 0x880, IdCells = 0x100000, IdRefs = 0x200000;  // cell k: IdCells + 2k, its LAND +1; 0x900.. copied records

    record Manifest(JsonElement Root)
    {
        public JsonElement Grid => Root.GetProperty("grid");
        public int G(string k) => Grid.GetProperty(k).GetInt32();
        public string Dir = "";
        public string BuildId => Root.GetProperty("build_id").GetString()!;
        public JsonElement Marker => Root.GetProperty("marker");
    }

    static Manifest Load(string path)
    {
        var m = new Manifest(JsonDocument.Parse(File.ReadAllText(path)).RootElement) { Dir = Path.GetDirectoryName(Path.GetFullPath(path))! };
        if (m.Root.GetProperty("cell_bytes").GetInt32() != 4 + V * V * 4) throw new InvalidDataException("cell_bytes");
        return m;
    }

    static T Edid<T>(ISkyrimModGetter mod, string edid) where T : class, IMajorRecordGetter =>
        mod.EnumerateMajorRecords<T>().FirstOrDefault(r => r.EditorID == edid) ?? throw new InvalidDataException($"{edid} not in {mod.ModKey}");

    public static int Run(string[] a) => a[0] switch
    {
        "write" => Write(a[1], a[2], a[3]),
        "check" => Check(a[1], a[2], a[3]),
        "navmesh" => NewWorldNavmesh.Run(a[1..]),
        _ => throw new ArgumentException("newworld write|check"),
    };

    static int Write(string manPath, string data, string outPath)
    {
        var sw = Stopwatch.StartNew();
        var man = Load(manPath);
        int cx0 = man.G("cx0"), cx1 = man.G("cx1"), cyTop = man.G("cy_top"), cyBot = man.G("cy_bottom"), nx = man.G("cells_x");
        float water = (float)man.Grid.GetProperty("water").GetDouble();
        using var bm = SkyrimMod.CreateFromBinaryOverlay(Path.Combine(data, "Black Marsh.esm"), Rel, Survey.NoStrings);
        var climate = Edid<IClimateGetter>(bm, "BlackMarshClimate").FormKey;
        var bmWorld = Edid<IWorldspaceGetter>(bm, "BlackMarsh");
        var watr = bmWorld.Water.FormKey;

        var modKey = ModKey.FromFileName(Esm);
        var mod = new SkyrimMod(modKey, Rel);
        mod.ModHeader.Flags |= SkyrimModHeader.HeaderFlag.Master;
        mod.ModHeader.Author = "Argonia";
        mod.ModHeader.Description = $"The new world's land; terrain build {man.BuildId}";
        FormKey K(uint id) => new(modKey, id);
        var ws = new Worldspace(K(IdWorld), Rel)
        {
            EditorID = WorldEdid,
            Name = new TranslatedString(Language.English, WorldName),
            Climate = new FormLinkNullable<IClimateGetter>(climate),
            Water = new FormLinkNullable<IWaterGetter>(watr),
            LodWater = new FormLinkNullable<IWaterGetter>(watr),
            LodWaterHeight = water,
            LandDefaults = new WorldspaceLandDefaults { DefaultLandHeight = -2048f, DefaultWaterHeight = water },
            ObjectBoundsMin = new P2Float(cx0 * CELL, cyBot * CELL),
            ObjectBoundsMax = new P2Float((cx1 + 1) * CELL, (cyTop + 1) * CELL),
            MapData = new WorldspaceMap
            {
                UsableDimensions = new P2Int(4096, 4096 * (cyTop - cyBot + 1) / nx),
                NorthwestCellCoords = new P2Int16((short)cx0, (short)cyTop),
                SoutheastCellCoords = new P2Int16((short)cx1, (short)cyBot),
                CameraMinHeight = 50000, CameraMaxHeight = 80000, CameraInitialPitch = 50,
            },
            Flags = 0,
            TopCell = new Cell(K(IdTopCell), Rel) { Flags = Cell.Flag.HasWater, Grid = new CellGrid { Point = new P2Int(0, 0) }, MajorFlags = Cell.MajorFlag.Persistent },
        };
        mod.Worldspaces.Add(ws);
        // the ground paint (tools/newworld/world/texture.py): our own LTEX per material, copied from its source
        // (asset-only plugins via ForeignCopy), with our grass list
        var allowed = bm.ModHeader.MasterReferences.Select(m => m.Master).Append(bm.ModKey).ToList();
        using var fc = new ForeignCopy(mod, allowed, data, IdCopies);
        var texDir = Path.Combine(Path.GetDirectoryName(man.Dir)!, "tex");
        var texMan = JsonDocument.Parse(File.ReadAllText(Path.Combine(texDir, "manifest.json"))).RootElement;
        if (texMan.GetProperty("build_id").GetString() != man.BuildId) throw new InvalidDataException("tex shards are another terrain build");
        int qBytes = texMan.GetProperty("quad_bytes").GetInt32(), maxL = texMan.GetProperty("max_layers").GetInt32();
        var matKeys = new List<FormKey>();
        foreach (var m in JsonDocument.Parse(File.ReadAllText(Path.Combine(texDir, "materials.json"))).RootElement.EnumerateArray())
        {
            var spec = m.GetProperty("ltex").GetString()!.Split(':');
            var key = fc.Get(spec[0], spec[1], forceCopy: true);
            var lt = mod.LandscapeTextures[key];
            lt.EditorID = "ANW_Ground_" + m.GetProperty("id").GetString();
            lt.Grasses.Clear();
            foreach (var gs in m.GetProperty("grass").EnumerateArray().Select(x => x.GetString()!.Split(':')))
                lt.Grasses.Add(new FormLink<IGrassGetter>(fc.Get(gs[0], gs[1])));
            matKeys.Add(key);
        }
        // water types, regions and weather, placed refs (tools/newworld/world/cells.py)
        var plugDir = Path.GetDirectoryName(man.Dir)!;
        var cj = JsonDocument.Parse(File.ReadAllText(Path.Combine(plugDir, "cells.json"))).RootElement;
        if (cj.GetProperty("build_id").GetString() != man.BuildId) throw new InvalidDataException("cells.json is another terrain build");
        var watrKey = new Dictionary<string, FormKey>();
        foreach (var p in cj.GetProperty("watr").EnumerateObject())
        {
            var v = p.Value;
            if (v.TryGetProperty("link", out var l)) { var sp = l.GetString()!.Split(':'); watrKey[p.Name] = fc.Get(sp[0], sp[1]); continue; }
            var src = v.GetProperty("copy").GetString()!.Split(':');
            var key = new FormKey(modKey, fc.NextIdTake());
            var w = (Water)fc.Find(src[0], src[1]).Duplicate(key);
            w.EditorID = v.GetProperty("edid").GetString();
            var vel = v.GetProperty("velocity");
            w.LinearVelocity = new P3Float((float)vel[0].GetDouble(), (float)vel[1].GetDouble(), 0);
            mod.Waters.Add(w);
            watrKey[p.Name] = key;
        }
        ws.Water = new FormLinkNullable<IWaterGetter>(watrKey["sea"]);
        ws.LodWater = new FormLinkNullable<IWaterGetter>(watrKey["sea"]);
        var (climKey, regionWeather) = Weather(mod, fc, ws, cj);
        ws.Climate = new FormLinkNullable<IClimateGetter>(climKey);
        var regionKey = new Dictionary<string, FormKey>();
        uint rid = IdRegions;
        foreach (var r in cj.GetProperty("regions").EnumerateObject())
        {
            var reg = new Region(K(rid++), Rel)
            {
                EditorID = "ANW_Region_" + r.Name.Replace("-", "_"),
                Worldspace = new FormLinkNullable<IWorldspaceGetter>(ws.FormKey),
                MapColor = System.Drawing.Color.FromArgb(120, 140, 90),
                Weather = new RegionWeather { Weathers = new ExtendedList<WeatherType>(regionWeather(r.Value.GetProperty("weathers"))) },
                Map = new RegionMap { Name = r.Value.GetProperty("name").GetString() },
            };
            mod.Regions.Add(reg);
            regionKey[r.Name] = reg.FormKey;
        }
        var cellInfo = cj.GetProperty("cells");
        var refsByCell = Refs(plugDir, fc);
        uint refId = IdRefs;
        var mk = man.Marker;
        var mCell = (mk.GetProperty("cell")[0].GetInt32(), mk.GetProperty("cell")[1].GetInt32());

        var blocks = new SortedDictionary<(int, int), SortedDictionary<(int, int), SortedDictionary<(int, int), Cell>>>();
        var buf = new byte[nx * (4 + V * V * 4)];
        var tbuf = new byte[nx * 4 * qBytes];
        uint k = 0;
        foreach (var name in man.Root.GetProperty("shards").EnumerateArray().Select(e => e.GetString()!))
        {
            var cy = int.Parse(name[2..^4]);
            using (var f = File.OpenRead(Path.Combine(man.Dir, name))) f.ReadExactly(buf);
            using (var f = File.OpenRead(Path.Combine(texDir, name))) f.ReadExactly(tbuf);
            for (var i = 0; i < nx; i++, k++)
            {
                int cx = cx0 + i, o = i * (4 + V * V * 4);
                var hm = new Array2d<sbyte>(V, V, 0);
                var nm = new Array2d<P3UInt8>(V, V, new P3UInt8(0, 0, 0));
                var cm = new Array2d<P3UInt8>(V, V, new P3UInt8(255, 255, 255));  // VCLR neutral
                for (var j = 0; j < V; j++)
                    for (var x = 0; x < V; x++)
                    {
                        var p = j * V + x;
                        hm[x, j] = unchecked((sbyte)buf[o + 4 + p]);
                        var q = o + 4 + V * V + 3 * p;
                        nm[x, j] = new P3UInt8(buf[q], buf[q + 1], buf[q + 2]);
                    }
                var land = new Landscape(K(IdCells + 2 * k + 1), Rel)
                {
                    Flags = (Landscape.Flag)0x1F,
                    IsCompressed = true,
                    VertexHeightMap = new LandscapeVertexHeightMap { Offset = BitConverter.ToSingle(buf, o), HeightMap = hm },
                    VertexNormals = nm,
                    VertexColors = cm,
                    Layers = GroundLayers(tbuf, i * 4 * qBytes, qBytes, maxL, matKeys),
                };
                var c = new Cell(K(IdCells + 2 * k), Rel)
                {
                    Flags = Cell.Flag.HasWater,
                    Grid = new CellGrid { Point = new P2Int(cx, cy) },
                    WaterHeight = water,
                    Landscape = land,
                };
                if (cellInfo.TryGetProperty($"{cx},{cy}", out var ci))
                {
                    if (ci.TryGetProperty("water", out var wk) && wk.GetString() != "sea") c.Water = new FormLinkNullable<IWaterGetter>(watrKey[wk.GetString()!]);
                    c.Regions = new ExtendedList<IFormLinkGetter<IRegionGetter>> { new FormLink<IRegionGetter>(regionKey[ci.GetProperty("region").GetString()!]) };
                }
                if (refsByCell.TryGetValue((cx, cy), out var rl))
                    foreach (var (bk, pos, rot, sc) in rl)
                        c.Temporary.Add(new PlacedObject(K(refId++), Rel)
                        {
                            Base = new FormLinkNullable<IPlaceableObjectGetter>(bk),
                            Placement = new Placement { Position = pos, Rotation = rot },
                            Scale = sc == 1f ? null : sc,
                        });
                if ((cx, cy) == mCell)
                {
                    c.EditorID = StartCell;
                    c.Temporary.Add(new PlacedObject(K(IdMarker), Rel)
                    {
                        EditorID = StartMarker,
                        Base = new FormLinkNullable<IPlaceableObjectGetter>(XMarkerHeading),
                        Placement = new Placement
                        {
                            Position = new P3Float((float)mk.GetProperty("x").GetDouble(), (float)mk.GetProperty("y").GetDouble(), (float)mk.GetProperty("z").GetDouble()),
                            Rotation = new P3Float(0, 0, (float)mk.GetProperty("rot_z").GetDouble()),
                        },
                    });
                }
                int bx = cx >> 5, by = cy >> 5, sx = cx >> 3, sy = cy >> 3;
                if (!blocks.TryGetValue((bx, by), out var subs)) blocks[(bx, by)] = subs = new();
                if (!subs.TryGetValue((sx, sy), out var cells)) subs[(sx, sy)] = cells = new();
                cells.Add((cx, cy), c);
            }
        }
        foreach (var ((bx, by), subs) in blocks)
        {
            var b = new WorldspaceBlock { BlockNumberX = (short)bx, BlockNumberY = (short)by, GroupType = GroupTypeEnum.ExteriorCellBlock };
            foreach (var ((sx, sy), cells) in subs)
            {
                var sb = new WorldspaceSubBlock { BlockNumberX = (short)sx, BlockNumberY = (short)sy, GroupType = GroupTypeEnum.ExteriorCellSubBlock };
                sb.Items.AddRange(cells.Values);
                b.Items.Add(sb);
            }
            ws.SubCells.Add(b);
        }
        NewWorldNavmesh.Attach(mod, ws, outPath, man.BuildId);  // nw-02 step 10: the navmesh, when built for this land
        var lo = bm.ModHeader.MasterReferences.Select(m => m.Master).Append(bm.ModKey).Append(modKey).ToList();
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(outPath))!);
        var tmpDir = Path.Combine(Path.GetDirectoryName(Path.GetFullPath(outPath))!, ".writing"); Directory.CreateDirectory(tmpDir);
        var tmp = Path.Combine(tmpDir, Path.GetFileName(outPath));  // same file name: Mutagen matches it to the mod key
        mod.BeginWrite.ToPath(tmp).WithLoadOrder(lo).WithDataFolder(data)
            .WithExtraIncludedMasters(ModKey.FromFileName("Skyrim.esm"), ModKey.FromFileName("Update.esm"))
            .SingleThread().Write();
        File.Move(tmp, outPath, true);
        Console.WriteLine($"newworld write: {outPath}: {k} cells with LAND, build {man.BuildId}, {new FileInfo(outPath).Length} bytes, {sw.Elapsed.TotalSeconds:F1} s");
        return 0;
    }

    // Our climate and weathers: BM&V's BlackMarshClimate copied as ours with a long sunrise/sunset window
    // (05:00-12:00, 17:00-22:00) so the night fog lerps away by noon and back by night; SkyrimClear and SkyrimCloudy
    // copied with a dense Night fog slot (near 0, far 8000, power 0.4, max 0.75): ground mist at dawn and night on
    // fair days; ANW_AfterRainFog (a SkyrimFog copy, day far 15000) listed beside the rain so fog follows it often.
    static (FormKey, Func<JsonElement, IEnumerable<WeatherType>>) Weather(SkyrimMod mod, ForeignCopy fc, Worldspace ws, JsonElement cj)
    {
        FormKey Copy(string edid, string ours, Action<Mutagen.Bethesda.Skyrim.Weather> edit)
        {
            var key = new FormKey(mod.ModKey, fc.NextIdTake());
            var w = (Mutagen.Bethesda.Skyrim.Weather)fc.Find("Skyrim.esm", edid).Duplicate(key);
            w.EditorID = ours; edit(w); mod.Weathers.Add(w); return key;
        }
        void NightFog(Mutagen.Bethesda.Skyrim.Weather w)
        {
            w.FogDistance ??= new WeatherFogDistance();
            w.FogDistance.NightNear = 0; w.FogDistance.NightFar = 8000; w.FogDistance.NightPower = 0.4f; w.FogDistance.NightMax = 0.75f;
        }
        var clear = Copy("SkyrimClear", "ANW_ClearMorningMist", NightFog);
        var cloudy = Copy("SkyrimCloudy", "ANW_CloudyMorningMist", NightFog);
        var after = Copy("SkyrimFog", "ANW_AfterRainFog", w => { w.FogDistance ??= new WeatherFogDistance(); w.FogDistance.DayFar = 15000; });
        var key = new Dictionary<string, FormKey>
        {
            ["SkyrimFog"] = fc.Find("Skyrim.esm", "SkyrimFog").FormKey, ["SkyrimOvercastRain"] = fc.Find("Skyrim.esm", "SkyrimOvercastRain").FormKey,
            ["SkyrimStormRain"] = fc.Find("Skyrim.esm", "SkyrimStormRain").FormKey, ["SkyrimCloudy"] = cloudy, ["SkyrimClear"] = clear,
        };
        IEnumerable<WeatherType> Mix(JsonElement weathers)
        {
            foreach (var p in weathers.EnumerateObject())
            {
                var ch = p.Value.GetInt32();
                if (p.Name == "SkyrimFog") { yield return Wt(key[p.Name], ch - ch / 3); yield return Wt(after, ch / 3); }
                else yield return Wt(key[p.Name], ch);
            }
        }
        static WeatherType Wt(FormKey k, int ch) => new() { Weather = new FormLink<IWeatherGetter>(k), Chance = ch };
        var climKey = fc.Get("Black Marsh.esm", "BlackMarshClimate", forceCopy: true);
        var clim = mod.Climates[climKey];
        clim.EditorID = "ANW_BlackMarshClimate";
        clim.Weathers.Clear();
        clim.Weathers.AddRange(Mix(JsonDocument.Parse("{\"SkyrimFog\":45,\"SkyrimOvercastRain\":20,\"SkyrimStormRain\":20,\"SkyrimCloudy\":10,\"SkyrimClear\":5}").RootElement));
        clim.SunriseBegin = new DateTime(1, 1, 1, 5, 0, 0); clim.SunriseEnd = new DateTime(1, 1, 1, 12, 0, 0);
        clim.SunsetBegin = new DateTime(1, 1, 1, 17, 0, 0); clim.SunsetEnd = new DateTime(1, 1, 1, 22, 0, 0);
        return (climKey, Mix);
    }

    // Placed refs from every producer's shards: <plugin dir>/refs/<producer>/cy<+NNN>.jsonl (format: cells.py).
    static Dictionary<(int, int), List<(FormKey, P3Float, P3Float, float)>> Refs(string plugDir, ForeignCopy fc)
    {
        var res = new Dictionary<(int, int), List<(FormKey, P3Float, P3Float, float)>>();
        var dir = Path.Combine(plugDir, "refs");
        if (!Directory.Exists(dir)) return res;
        var bases = new Dictionary<string, FormKey>();
        foreach (var f in Directory.EnumerateFiles(dir, "*.jsonl", SearchOption.AllDirectories).Order())
            foreach (var line in File.ReadLines(f))
            {
                if (line.Length == 0) continue;
                var o = JsonDocument.Parse(line).RootElement;
                var b = o.GetProperty("base").GetString()!;
                if (!bases.TryGetValue(b, out var bk)) { var sp = b.Split(':', 2); bases[b] = bk = fc.Get(sp[0], sp[1]); }
                float G(string k) => (float)o.GetProperty(k).GetDouble();
                var pos = new P3Float(G("x"), G("y"), G("z"));
                var cell = ((int)Math.Floor(pos.X / CELL), (int)Math.Floor(pos.Y / CELL));
                if (!res.TryGetValue(cell, out var l)) res[cell] = l = new();
                l.Add((bk, pos, new P3Float(G("rx"), G("ry"), G("rz")), G("scale")));
            }
        return res;
    }

    // One cell's LAND layers from its 4 tex quadrants: per quadrant one base (BTXT, layer 0xFFFF) then alpha layers
    // 0..n-2 (ATXT + VTXT, only non-zero points), in the shard's order.
    static ExtendedList<BaseLayer> GroundLayers(byte[] t, int off, int qBytes, int maxL, List<FormKey> mats)
    {
        var layers = new ExtendedList<BaseLayer>();
        for (var q = 0; q < 4; q++)
        {
            int o = off + q * qBytes, n = t[o];
            var quad = Quads[q];
            layers.Add(new BaseLayer { Header = new LayerHeader { Texture = new FormLink<ILandscapeTextureGetter>(mats[t[o + 1]]), Quadrant = quad, LayerNumber = 0xFFFF } });
            for (var k = 1; k < n; k++)
            {
                var ad = new ExtendedList<AlphaLayerData>();
                int a = o + 1 + maxL + (k - 1) * 289;
                for (ushort p = 0; p < 289; p++) if (t[a + p] > 0) ad.Add(new AlphaLayerData { Position = p, Opacity = t[a + p] / 255f });
                layers.Add(new AlphaLayer
                {
                    Header = new LayerHeader { Texture = new FormLink<ILandscapeTextureGetter>(mats[t[o + 1 + k]]), Quadrant = quad, LayerNumber = (ushort)(k - 1) },
                    AlphaLayerData = ad,
                });
            }
        }
        return layers;
    }

    static int Check(string esmPath, string manPath, string data)
    {
        var sw = Stopwatch.StartNew();
        var man = Load(manPath);
        int cx0 = man.G("cx0"), cx1 = man.G("cx1"), cyTop = man.G("cy_top"), cyBot = man.G("cy_bottom");
        int width = man.G("width"), height = man.G("height");
        float water = (float)man.Grid.GetProperty("water").GetDouble();
        var hmap = ReadNpy(man.Root.GetProperty("heightmap").GetString()!, width, height);
        var fails = new List<string>();
        void Fail(string s) { if (fails.Count < 40) fails.Add(s); else if (fails.Count == 40) fails.Add("..."); }
        using var mod = SkyrimMod.CreateFromBinaryOverlay(esmPath, Rel, Survey.NoStrings);
        if (!mod.ModHeader.Flags.HasFlag(SkyrimModHeader.HeaderFlag.Master)) Fail("ESM flag not set");
        var masters = mod.ModHeader.MasterReferences.Select(m => m.Master.FileName.String).ToList();
        foreach (var need in new[] { "Skyrim.esm", "Update.esm", "Black Marsh.esm" }) if (!masters.Contains(need)) Fail($"master {need} missing");
        var wss = mod.Worldspaces.ToList();
        if (wss.Count != 1) Fail($"{wss.Count} worldspaces");
        var ws = wss[0];
        if (ws.EditorID != WorldEdid || ws.Name?.String != WorldName) Fail($"WRLD {ws.EditorID} '{ws.Name?.String}'");
        if (ws.LandDefaults?.DefaultWaterHeight != water) Fail($"WRLD default water {ws.LandDefaults?.DefaultWaterHeight}");
        if (ws.Climate.IsNull || ws.Water.IsNull) Fail("WRLD climate or water missing");
        if (ws.Parent is not null && !ws.Parent.Worldspace.IsNull) Fail("WRLD has a parent");
        var heights = new Dictionary<(int, int), float[]>();
        double maxErr = 0; (int, int) maxAt = default; long over4 = 0, verts = 0, wrongWater = 0, noNormals = 0;
        IPlacedObjectGetter? marker = null; ICellGetter? markerCell = null; int startCells = 0;
        foreach (var b in ws.SubCells) foreach (var sb in b.Items) foreach (var c in sb.Items)
        {
            if (c.Grid is null) { Fail($"cell {c.FormKey} without grid"); continue; }
            var (x, y) = (c.Grid.Point.X, c.Grid.Point.Y);
            if (c.EditorID == StartCell) startCells++;
            foreach (var r in c.Temporary.Concat(c.Persistent))
                if (r.EditorID == StartMarker && r is IPlacedObjectGetter po) { marker = po; markerCell = c; }
            if (c.WaterHeight != water || !c.Flags.HasFlag(Cell.Flag.HasWater)) wrongWater++;
            var l = c.Landscape;
            if (l?.VertexHeightMap is null) { Fail($"cell {x},{y} without VHGT"); continue; }
            if (l.VertexNormals is null) noNormals++;
            var hm = l.VertexHeightMap.HeightMap;
            var dec = new float[V * V];
            double row = l.VertexHeightMap.Offset;
            for (var j = 0; j < V; j++)
            {
                row += hm[0, j];  // [0, 0] is 0 by construction, [0, j] carries north
                double v = row;
                dec[j * V] = (float)(v * 8);
                for (var i = 1; i < V; i++) { v += hm[i, j]; dec[j * V + i] = (float)(v * 8); }
            }
            if (!heights.TryAdd((x, y), dec)) Fail($"cell {x},{y} twice");
            int north = (cyTop - y) * 32, west = (x - cx0) * 32;
            for (var j = 0; j < V; j++)
                for (var i = 0; i < V; i++)
                {
                    var e = Math.Abs(dec[j * V + i] - hmap[(long)(north + 32 - j) * width + west + i]);
                    verts++;
                    if (e > 4.0001) over4++;
                    if (e > maxErr) { maxErr = e; maxAt = (x, y); }
                }
        }
        int expected = (cx1 - cx0 + 1) * (cyTop - cyBot + 1), missing = 0;
        for (var y = cyBot; y <= cyTop; y++) for (var x = cx0; x <= cx1; x++) if (!heights.ContainsKey((x, y))) missing++;
        if (heights.Count != expected || missing > 0) Fail($"{heights.Count} cells, expected {expected}, {missing} missing");
        long seamEdges = 0, seamBad = 0;
        foreach (var ((x, y), d) in heights)
        {
            if (heights.TryGetValue((x + 1, y), out var e)) { seamEdges++; for (var j = 0; j < V; j++) if (d[j * V + 32] != e[j * V]) { seamBad++; break; } }
            if (heights.TryGetValue((x, y + 1), out var n)) { seamEdges++; for (var i = 0; i < V; i++) if (d[32 * V + i] != n[i]) { seamBad++; break; } }
        }
        if (seamBad > 0) Fail($"{seamBad} seam mismatches");
        if (over4 > 0) Fail($"{over4} vertices more than half a step from the heightmap (limited or overflowed)");
        if (wrongWater > 0) Fail($"{wrongWater} cells without water height {water}");
        if (noNormals > 0) Fail($"{noNormals} cells without VNML");
        var mk = man.Marker;
        var mc = (mk.GetProperty("cell")[0].GetInt32(), mk.GetProperty("cell")[1].GetInt32());
        string markerLine = "marker missing";
        if (marker is null || markerCell?.Grid is null) Fail("start marker missing");
        else
        {
            var mcell = (markerCell.Grid.Point.X, markerCell.Grid.Point.Y);
            var pos = marker.Placement!.Position;
            var inCell = ((int)Math.Floor(pos.X / CELL), (int)Math.Floor(pos.Y / CELL));
            var d = heights[mcell];
            int i = (int)Math.Round((pos.X - mcell.Item1 * CELL) / 128.0), j = (int)Math.Round((pos.Y - mcell.Item2 * CELL) / 128.0);
            var ground = d[j * V + i];
            if (mcell != mc || inCell != mc) Fail($"marker in cell {mcell}, position in {inCell}, manifest {mc}");
            if (markerCell.EditorID != StartCell) Fail($"marker cell edid {markerCell.EditorID}");
            if (marker.Base.FormKey != XMarkerHeading) Fail("marker base is not XMarkerHeading");
            if (pos.Z < ground || pos.Z > ground + 64 || ground <= water) Fail($"marker z {pos.Z} vs ground {ground} (water {water})");
            markerLine = $"marker {StartMarker} at {pos.X:F0},{pos.Y:F0},{pos.Z:F0} in cell {mcell} (ground {ground:F0}, dry)";
        }
        if (startCells != 1) Fail($"{startCells} cells named {StartCell}");
        // coc resolves the name to one cell: no other record in the masters carries it
        foreach (var m in new[] { "Skyrim.esm", "Update.esm", "Black Marsh.esm" })
        {
            using var mm = SkyrimMod.CreateFromBinaryOverlay(Path.Combine(data, m), Rel, Survey.NoStrings);
            foreach (var r in mm.EnumerateMajorRecords()) if (r.EditorID is { } ed && (ed.Equals(StartCell, StringComparison.OrdinalIgnoreCase) || ed.Equals(WorldEdid, StringComparison.OrdinalIgnoreCase))) Fail($"{ed} also in {m}");
        }
        var stats = man.Root.GetProperty("stats");
        Console.WriteLine($"newworld check: {esmPath} ({new FileInfo(esmPath).Length} bytes), build {man.BuildId}");
        Console.WriteLine($"  cells {heights.Count}/{expected} with LAND; vertices {verts}; max height error {maxErr:F2} units ({maxErr / 70:F3} m) at {maxAt}; >half-step {over4}");
        Console.WriteLine($"  seams {seamEdges} edges, {seamBad} mismatches; VHGT overflow pairs before/after limiter {stats.GetProperty("overflow_pairs_before")}/{stats.GetProperty("overflow_pairs_after")}, limited vertices {stats.GetProperty("limited_vertices")}");
        Console.WriteLine($"  water: WRLD default {ws.LandDefaults?.DefaultWaterHeight}, cells off {wrongWater}; {markerLine}; coc {StartCell} (unique)");
        Console.WriteLine($"  {(fails.Count == 0 ? "PASS" : "FAIL")} in {sw.Elapsed.TotalSeconds:F1} s");
        foreach (var f in fails) Console.WriteLine($"  FAIL {f}");
        return fails.Count == 0 ? 0 : 1;
    }

    static float[] ReadNpy(string path, int width, int height)
    {
        using var f = File.OpenRead(path);
        using var r = new BinaryReader(f);
        if (r.ReadByte() != 0x93) throw new InvalidDataException("not npy");
        r.ReadBytes(5);
        int major = r.ReadByte(); r.ReadByte();
        int hl = major == 1 ? r.ReadUInt16() : (int)r.ReadUInt32();
        var header = System.Text.Encoding.ASCII.GetString(r.ReadBytes(hl));
        if (!header.Contains("'<f4'") || !header.Contains("'fortran_order': False") || !header.Contains($"({height}, {width})"))
            throw new InvalidDataException($"heightmap npy header {header}");
        var a = new float[(long)width * height];
        var bytes = System.Runtime.InteropServices.MemoryMarshal.AsBytes(a.AsSpan());
        f.ReadExactly(bytes);
        return a;
    }
}
