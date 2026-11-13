// newworld: the new world's plugin ArgoniaNewWorld.esm from the land shards (tools/newworld/world/land.py), and its
// off-game read-back. Ported from the old ArgoniaGen/LandWorld.cs (ac983185): same LAND layout, no intermediate JSON.
//   newworld write <land/manifest.json> <Data dir> <out.esm> [form ids registry]
//       the registry (FormIds.cs) holds the id of every record that is not placed by formula; the world's is
//       newworld/sources/world_formids.json, another world's defaults to formids.json beside its ESM
//   newworld check <out.esm> <land/manifest.json> <Data dir>      (exit 1 on any failure)
// Facts kept from LandWorld.cs (measured on Skyrim.esm's Tamriel): LAND DATA flags 0x1F, compressed; per quadrant
// BottomLeft, BottomRight, TopLeft, TopRight one base layer (0xFFFF); Array2d indexed [x, y], y north from the south;
// blocks 32 x 32 cells, sub-blocks 8 x 8, floor division. VHGT offset is in 8-unit steps.
// The ground is painted from the tex shards (world/texture.py), the water typed per cell (world/cells.py, WaterBlend.cs),
// the climate, weathers and region weather lists made by NewWorldAtmosphere.cs from atmosphere.json.
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
    // form ids by formula: the world, its persistent cell, the start marker; cell k of the grid IdCells + 2k, its LAND
    // +1. A placed reference whose shard line carries its form id ("fid": the placer's, by formula from the
    // reference's identity, IdRefs..; an added thing's, given once by its edit row, up to IdRefsCounted - 1) takes
    // that id, so an edit of one reference moves no other's: a save names a reference by its id. A producer's line
    // without one (the mist) counts up from IdRefsCounted in the shards' order. The navmesh's records hold
    // IdNavmesh..IdNavmeshEnd inside the references' range (navmesh/stitch.py): no reference may carry one.
    // Every other record's id is its name's in the registry (FormIds.cs), in its kind's block.
    // Every allocator's range is one table, tools/newworld/idspace.py; these are its numbers.
    const uint IdWorld = 0x800, IdTopCell = 0x801, IdMarker = 0x802, IdCells = 0x100000, IdRefs = 0x200000, IdRefsCounted = 0x740000, IdRefsEnd = 0x7FFFFF;
    const byte FlowerGrassDensity = 40;   // verify.py FLOWER_GRASS_DENSITY
    const uint IdNavmesh = 0x600000, IdNavmeshEnd = 0x609677;
    const uint IdDressing = 0x0A0000, IdDressingEnd = 0x0FFFFF;   // tools/newworld/idspace.py row `dressing`
    const uint IdEcology = 0xF00000, IdEcologyEnd = 0xFDFFFF;   // tools/newworld/idspace.py row `ecology`
    static readonly string[] Allowed = { "Skyrim.esm", "Update.esm", "Black Marsh.esm" };  // the only masters (verify.py MASTERS)

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
        "write" => Write(a[1], a[2], a[3], a.Length > 4 ? a[4] : Path.Combine(Path.GetDirectoryName(Path.GetFullPath(a[3]))!, "formids.json")),
        "check" => Check(a[1], a[2], a[3]),
        "navmesh" => NewWorldNavmesh.Run(a[1..]),
        "travel" => NewWorldTravel.Try(a[1], a[2], a.Length > 3 ? a[3] : null),
        _ => throw new ArgumentException("newworld write|check"),
    };

    static int Write(string manPath, string data, string outPath, string idsPath)
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
        var allowed = Allowed.Select(f => ModKey.FromFileName(f)).ToList();  // a DLC record (Black Marsh's own masters) is copied too
        var ids = FormIds.Load(idsPath);
        using var fc = new ForeignCopy(mod, allowed, data, ids) { Kind = "ground" };
        var texDir = Path.Combine(Path.GetDirectoryName(man.Dir)!, "tex");
        var texMan = JsonDocument.Parse(File.ReadAllText(Path.Combine(texDir, "manifest.json"))).RootElement;
        if (texMan.GetProperty("build_id").GetString() != man.BuildId) throw new InvalidDataException("tex shards are another terrain build");
        int qBytes = texMan.GetProperty("quad_bytes").GetInt32(), maxL = texMan.GetProperty("max_layers").GetInt32();
        var matKeys = new List<FormKey>();
        foreach (var m in JsonDocument.Parse(File.ReadAllText(Path.Combine(texDir, "materials.json"))).RootElement.EnumerateArray())
        {
            var spec = m.GetProperty("ltex").GetString()!.Split(':');
            // each material its own LTEX (two materials of one source differ by their grass), its id the material's
            var key = fc.CopyAs(fc.Find(spec[0], spec[1]), spec[0], ids.Take("ground", "ltex:" + m.GetProperty("id").GetString()));
            var lt = mod.LandscapeTextures[key];
            lt.EditorID = "ANW_Ground_" + m.GetProperty("id").GetString();
            var ts = lt.TextureSet.FormKey;  // our own TXST too, so the ground's diffuse paths read from this plugin alone
            if (!ts.IsNull && ts.ModKey != modKey) lt.TextureSet.SetTo(fc.Get(ts, ts.ModKey.FileName, forceCopy: true));
            lt.Grasses.Clear();
            foreach (var gs in m.GetProperty("grass").EnumerateArray().Select(x => x.GetString()!.Split(':')))
            {
                var gk = fc.Get(gs[0], gs[1]);
                // Flower Fields' grasses come at density 100; King of the Murkmire's flower grasses and the middle of
                // Skyrim's are 40 (docs/design/dressing.md): our copy is thinned to that, so a patch is not a carpet
                if (gs[0] == "FlowerFields.esp" && mod.Grasses.TryGetValue(gk, out var gr) && gr.Density > FlowerGrassDensity) gr.Density = FlowerGrassDensity;
                lt.Grasses.Add(new FormLink<IGrassGetter>(gk));
            }
            matKeys.Add(key);
        }
        // water types, regions and weather, placed refs (tools/newworld/world/cells.py)
        var plugDir = Path.GetDirectoryName(man.Dir)!;
        var cj = JsonDocument.Parse(File.ReadAllText(Path.Combine(plugDir, "cells.json"))).RootElement;
        if (cj.GetProperty("build_id").GetString() != man.BuildId) throw new InvalidDataException("cells.json is another terrain build");
        var (watrKey, watrRec) = WaterBlend.Records(mod, fc, cj.GetProperty("watr"));   // our WATR per kind and heading
        ws.Water = new FormLinkNullable<IWaterGetter>(watrKey["sea"]);
        ws.LodWater = new FormLinkNullable<IWaterGetter>(watrKey["sea"]);
        var (climKey, regionWeather) = NewWorldAtmosphere.Build(mod, fc, plugDir);  // atmosphere.json (tools/newworld/atmosphere.py)
        ws.Climate = new FormLinkNullable<IClimateGetter>(climKey);
        var regionKey = new Dictionary<string, FormKey>();
        // Where the player is, Skyrim's way: a location (LCTN) named for the place, its parent the larger area (Skyrim.esm
        // WhiteRunLocation -> WhiterunHoldLocation "Whiterun Hold" -> TamrielLocation), set on the cell (XLCN); the
        // location's name is what the map menu, the save list and the journal show for "here". One location per region,
        // its parent the world's location, set on every exterior cell of the region.
        var worldLoc = new Location(K(ids.Take("region", "location:world")), Rel) { EditorID = "ANW_Loc_World", Name = ws.Name?.String?.Split(" (")[0] ?? "Black Marsh" };
        mod.Locations.Add(worldLoc);
        var regionLoc = new Dictionary<FormKey, FormKey>();
        foreach (var r in cj.GetProperty("regions").EnumerateObject())
        {
            var reg = new Region(K(ids.Take("region", "region:" + r.Name)), Rel)
            {
                EditorID = "ANW_Region_" + r.Name.Replace("-", "_"),
                Worldspace = new FormLinkNullable<IWorldspaceGetter>(ws.FormKey),
                MapColor = System.Drawing.Color.FromArgb(120, 140, 90),
                Weather = NewWorldAtmosphere.RegionWeatherOf(regionWeather(r.Name)),
                Sounds = NewWorldAtmosphere.RegionSoundsOf(r.Name),
                Map = new RegionMap { Name = r.Value.GetProperty("name").GetString() },
            };
            mod.Regions.Add(reg);
            regionKey[r.Name] = reg.FormKey;
            var loc = new Location(K(ids.Take("region", "location:" + r.Name)), Rel)
            {
                EditorID = "ANW_Loc_" + r.Name.Replace("-", "_"),
                Name = r.Value.GetProperty("name").GetString(),
                ParentLocation = new FormLinkNullable<ILocationGetter>(worldLoc.FormKey),
            };
            mod.Locations.Add(loc);
            regionLoc[reg.FormKey] = loc.FormKey;
        }
        var cellInfo = cj.GetProperty("cells");
        // seams between water types graded over a band of cells (WaterBlend.cs)
        var cellKind = new Dictionary<(int, int), string>();
        foreach (var e in cellInfo.EnumerateObject())
            if (e.Value.TryGetProperty("water", out var wv))
            {
                var xy = e.Name.Split(',');
                cellKind[(int.Parse(xy[0]), int.Parse(xy[1]))] = wv.GetString()!;
            }
        var (cellWater, blendReport) = WaterBlend.Blend(mod, n => ids.Take("water", n), cellKind, watrKey, watrRec);
        File.WriteAllText(Path.Combine(plugDir, "water_blend.json"), JsonSerializer.Serialize(blendReport));
        Console.WriteLine("  water seams: " + string.Join(", ", blendReport.Select(kv => $"{kv.Key} {kv.Value}")));
        fc.Kind = "base";
        var refsByCell = Refs(plugDir, fc);
        var actorsByCell = Ecology(plugDir, fc, ids, mod);
        var crittersByCell = Critters(plugDir, fc);
        var harvestByCell = Harvest(plugDir, fc, ids, mod);
        var dressingByCell = Dressing(plugDir, fc);
        uint refId = IdRefsCounted;
        var given = new HashSet<uint>();
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
                    if (cellWater.TryGetValue((cx, cy), out var wfk)) c.Water = new FormLinkNullable<IWaterGetter>(wfk);
                    var rk = regionKey[ci.GetProperty("region").GetString()!];
                    c.Regions = new ExtendedList<IFormLinkGetter<IRegionGetter>> { new FormLink<IRegionGetter>(rk) };
                    c.Location = new FormLinkNullable<ILocationGetter>(regionLoc[rk]);
                }
                if (refsByCell.TryGetValue((cx, cy), out var rl))
                    foreach (var (bk, pos, rot, sc, fid) in rl)
                    {
                        if (fid is { } id && (id < IdRefs || id >= IdRefsCounted || (id >= IdNavmesh && id <= IdNavmeshEnd) || !given.Add(id)))
                            throw new InvalidDataException($"a placed reference's form id {id:X6} is given twice, lies outside {IdRefs:X6}..{IdRefsCounted - 1:X6} or is one of the navmesh's ({IdNavmesh:X6}..{IdNavmeshEnd:X6})");
                        c.Temporary.Add(new PlacedObject(K(fid ?? refId++), Rel)
                        {
                            Base = new FormLinkNullable<IPlaceableObjectGetter>(bk),
                            Placement = new Placement { Position = pos, Rotation = rot },
                            Scale = sc == 1f ? null : sc,
                        });
                    }
                if (actorsByCell.TryGetValue((cx, cy), out var al))
                    foreach (var (nk, pos, rz, fid) in al)
                    {
                        if (fid < IdEcology || fid > IdEcologyEnd || !given.Add(fid))
                            throw new InvalidDataException($"an ecology actor's form id {fid:X6} is given twice or lies outside {IdEcology:X6}..{IdEcologyEnd:X6}");
                        c.Temporary.Add(new PlacedNpc(K(fid), Rel)
                        {
                            Base = new FormLinkNullable<INpcGetter>(nk),
                            Placement = new Placement { Position = pos, Rotation = new P3Float(0, 0, rz) },
                        });
                    }
                if (crittersByCell.TryGetValue((cx, cy), out var cl))
                    foreach (var (bk, pos, rz, fid) in cl)
                    {
                        if (fid < IdEcology || fid > IdEcologyEnd || !given.Add(fid))
                            throw new InvalidDataException($"an ecology critter's form id {fid:X6} is given twice or lies outside {IdEcology:X6}..{IdEcologyEnd:X6}");
                        c.Temporary.Add(new PlacedObject(K(fid), Rel)
                        {
                            Base = new FormLinkNullable<IPlaceableObjectGetter>(bk),
                            Placement = new Placement { Position = pos, Rotation = new P3Float(0, 0, rz) },
                        });
                    }
                if (harvestByCell.TryGetValue((cx, cy), out var hl))
                    foreach (var (bk, pos, rz, sc, fid) in hl)
                    {
                        if (fid < IdEcology || fid > IdEcologyEnd || !given.Add(fid))
                            throw new InvalidDataException($"an ecology harvestable's form id {fid:X6} is given twice or lies outside {IdEcology:X6}..{IdEcologyEnd:X6}");
                        c.Temporary.Add(new PlacedObject(K(fid), Rel)
                        {
                            Base = new FormLinkNullable<IPlaceableObjectGetter>(bk),
                            Placement = new Placement { Position = pos, Rotation = new P3Float(0, 0, rz) },
                            Scale = sc == 1f ? null : sc,
                        });
                    }
                if (dressingByCell.TryGetValue((cx, cy), out var dl))
                    foreach (var (bk, pos, rz, sc, fid) in dl)
                    {
                        if (fid < IdDressing || fid > IdDressingEnd || !given.Add(fid))
                            throw new InvalidDataException($"a dressing reference's form id {fid:X6} is given twice or lies outside {IdDressing:X6}..{IdDressingEnd:X6}");
                        c.Temporary.Add(new PlacedObject(K(fid), Rel)
                        {
                            Base = new FormLinkNullable<IPlaceableObjectGetter>(bk),
                            Placement = new Placement { Position = pos, Rotation = new P3Float(0, 0, rz) },
                            Scale = sc == 1f ? null : sc,
                        });
                    }
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
        // the travel menu (newworld/sources/travel/menu.json, beside the registry): the gamepad's way in, no console
        var menu = Path.Combine(Path.GetDirectoryName(Path.GetFullPath(idsPath))!, "travel", "menu.json");
        if (File.Exists(menu)) NewWorldTravel.Attach(mod, ids, menu);
        NewWorldMusic.Attach(mod, ws, Path.GetDirectoryName(Path.GetFullPath(idsPath))!, data);  // music records (newworld/sources/music/records.json)
        NewWorldNavmesh.Attach(mod, ws, outPath, man.BuildId);  // nw-02 step 10: the navmesh, when built for this land
        if (IdCells + 2 * k > IdRefs || refId > IdRefsEnd + 1 || k > IdNavmeshEnd - IdNavmesh + 1) throw new InvalidDataException($"cells ran to {IdCells + 2 * k:X6} or counted references to {refId:X6}, out of their ranges");
        InIdOrder(mod);
        ids.Save();
        Console.WriteLine($"  form ids: {ids.Count} registered names, {ids.Added.Count} new; references: {given.Count} under their own ids, {refId - IdRefsCounted} counted from {IdRefsCounted:X6}");
        var lo = bm.ModHeader.MasterReferences.Select(m => m.Master).Append(bm.ModKey).Append(modKey).ToList();
        var upd = ModKey.FromFileName("Update.esm");  // a master always (its WATR/WTHR records win), placed after Skyrim.esm
        if (!lo.Contains(upd)) lo.Insert(lo.IndexOf(ModKey.FromFileName("Skyrim.esm")) + 1, upd);
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(outPath))!);
        var tmpDir = Path.Combine(Path.GetDirectoryName(Path.GetFullPath(outPath))!, ".writing"); Directory.CreateDirectory(tmpDir);
        var tmp = Path.Combine(tmpDir, Path.GetFileName(outPath));  // same file name: Mutagen matches it to the mod key
        mod.BeginWrite.ToPath(tmp).WithLoadOrder(lo).WithDataFolder(data)
            .WithExtraIncludedMasters(ModKey.FromFileName("Skyrim.esm"), upd)
            .SingleThread().Write();
        File.Move(tmp, outPath, true);
        Console.WriteLine($"newworld write: {outPath}: {k} cells with LAND, build {man.BuildId}, {new FileInfo(outPath).Length} bytes, {sw.Elapsed.TotalSeconds:F1} s");
        return 0;
    }

    // Each top group's records in the order of their ids, a record after the records of its own group it links to (a
    // levelled list after the lists inside it): the file's order follows from the records, never from the order the
    // build met them in.
    static void InIdOrder(SkyrimMod mod)
    {
        foreach (var g in mod.EnumerateMajorRecords().Where(r => r is not (ICellGetter or IPlacedGetter or ILandscapeGetter or INavigationMeshGetter or IWorldspaceGetter))
                     .GroupBy(r => r.GetType()).Select(t => mod.GetTopLevelGroup(t.Key)).ToList())
        {
            var byKey = g.Records.ToDictionary(r => r.FormKey);
            var done = new HashSet<FormKey>();
            var order = new List<IMajorRecord>();
            void Put(IMajorRecord r)
            {
                if (!done.Add(r.FormKey)) return;
                foreach (var l in r.EnumerateFormLinks().Select(l => l.FormKey).Where(byKey.ContainsKey).Distinct().OrderBy(l => l.ID)) Put(byKey[l]);
                order.Add(r);
            }
            foreach (var r in byKey.Values.OrderBy(r => r.FormKey.ID)) Put(r);
            ((dynamic)g).Clear();  // the typed group's own Clear: a group emptied record by record does not keep the order it is filled in
            foreach (var r in order) g.AddUntyped(r);
        }
    }

    // The ecology stage's actors (tools/newworld/ecology/place.py): <plugin dir>/ecology/actors.json names each band
    // actor (the record it copies, its band's fixed level and health), copied whole by ForeignCopy and then given the
    // band: a fixed level (never the player's: decision 0035), its stats its own (no template's), not unique,
    // essential or protected, health times the band's. cy<+NNN>.jsonl places them, one ACHR a line.
    static Dictionary<(int, int), List<(FormKey, P3Float, float, uint)>> Ecology(string plugDir, ForeignCopy fc, FormIds ids, SkyrimMod mod)
    {
        var res = new Dictionary<(int, int), List<(FormKey, P3Float, float, uint)>>();
        var dir = Path.Combine(plugDir, "ecology");
        var aj = Path.Combine(dir, "actors.json");
        if (!File.Exists(aj)) return res;
        var actor = new Dictionary<string, FormKey>();
        var dmg = new Dictionary<int, FormKey>();
        foreach (var a in JsonDocument.Parse(File.ReadAllText(aj)).RootElement.GetProperty("actors").EnumerateArray())
        {
            var name = a.GetProperty("name").GetString()!;
            var sp = a.GetProperty("src").GetString()!.Split(':', 2);
            var src = mod.Npcs[fc.Get(sp[0], sp[1], forceCopy: true)];
            // the source's own copy is never placed, yet it stands in our file: it keeps no player-level multiplier either
            // (decision 0035), so it takes the lowest band level any of its band copies has
            var lv0 = (short)a.GetProperty("level").GetInt32();
            if (src.Configuration.Level is not NpcLevel sl || sl.Level > lv0) src.Configuration.Level = new NpcLevel { Level = lv0 };
            src.Configuration.TemplateFlags &= ~NpcConfiguration.TemplateFlag.Stats;
            var n = (Npc)src.Duplicate(new FormKey(mod.ModKey, ids.Take("base", "eco:" + name)));
            var kit = name.Contains('~') ? "_" + name.Split('~')[1].Split('@')[0] : "";
            var sized = name.Contains('/') ? "_" + name.Split('/')[1] : "";   // one record at a second size (ecology/place.py)
            n.EditorID = $"ANW_Eco_{src.EditorID}_{a.GetProperty("band").GetString()}{kit}{sized}";
            var cfg = n.Configuration;
            cfg.Level = new NpcLevel { Level = (short)a.GetProperty("level").GetInt32() };
            cfg.TemplateFlags &= ~NpcConfiguration.TemplateFlag.Stats;
            cfg.Flags &= ~(NpcConfiguration.Flag.Unique | NpcConfiguration.Flag.Essential | NpcConfiguration.Flag.Protected | NpcConfiguration.Flag.AutoCalcStats);
            var hm = a.GetProperty("health_mult").GetDouble();
            if (n.PlayerSkills is { } ps) ps.Health = (ushort)Math.Clamp(Math.Max((int)ps.Health, 20) * hm, 1, 65535);
            cfg.HealthOffset = (short)Math.Clamp(cfg.HealthOffset * hm, short.MinValue, short.MaxValue);
            // a people's kit for the band (place.py GEAR_TIER): an outfit of a plugin we hold, or our own flat outfit
            // of the listed armour and weapons; never a levelled list
            if (a.TryGetProperty("gear", out var gear))
            {
                FormKey G(string r) { var q = r.Split(':', 2); return fc.Get(q[0], q[1]); }
                if (gear.TryGetProperty("outfit", out var ot)) n.DefaultOutfit = new FormLinkNullable<IOutfitGetter>(G(ot.GetString()!));
                else
                {
                    var o = new Outfit(new FormKey(mod.ModKey, ids.Take("base", "eco-outfit:" + name)), Rel) { EditorID = n.EditorID + "_Outfit",
                        Items = new ExtendedList<IFormLinkGetter<IOutfitTargetGetter>>(gear.GetProperty("items").EnumerateArray()
                            .Select(i => (IFormLinkGetter<IOutfitTargetGetter>)new FormLink<IOutfitTargetGetter>(G(i.GetString()!)))) };
                    mod.Outfits.Add(o);
                    n.DefaultOutfit = new FormLinkNullable<IOutfitGetter>(o.FormKey);
                }
            }
            // the kit's hands: weapons (and ammunition) are items, not outfit targets, so the record's own items go and the
            // band tier's weapons come in; Skyrim's NPCs wield the best weapon they carry
            if (a.TryGetProperty("gear", out var hands) && hands.TryGetProperty("weapons", out var ws))
            {
                FormKey W(string r) { var q = r.Split(':', 2); return fc.Get(q[0], q[1]); }
                n.Items = new ExtendedList<ContainerEntry>();
                foreach (var w in ws.EnumerateArray())
                    n.Items.Add(new ContainerEntry { Item = new ContainerItem { Item = new FormLink<IItemGetter>(W(w.GetString()!)), Count = 1 } });
                if (hands.TryGetProperty("ammo", out var am))
                    n.Items.Add(new ContainerEntry { Item = new ContainerItem { Item = new FormLink<IItemGetter>(W(am.GetString()!)), Count = 40 } });
            }
            // the band's blow, as Skyrim scales a stronger variant of a creature (the dragons' and werewolves' tiers): an
            // ability that adds to the unarmed damage its race gives (AbFortifyUnarmedDamage), one per magnitude
            if (a.TryGetProperty("damage_bonus", out var db) && db.GetInt32() > 0)
            {
                var mag = db.GetInt32();
                if (!dmg.TryGetValue(mag, out var sk))
                {
                    var ab = new Spell(new FormKey(mod.ModKey, ids.Take("base", "eco-damage:" + mag)), Rel)
                    {
                        EditorID = $"ANW_Eco_UnarmedDamage{mag:D3}", Name = new TranslatedString(Language.English, "Band blow"),
                        Type = SpellType.Ability, CastType = CastType.ConstantEffect, TargetType = TargetType.Self,
                    };
                    ab.EquipmentType.SetTo(FormKey.Factory("013F44:Skyrim.esm"));   // EitherHand, as vanilla abilities
                    ab.Effects.Add(new Effect { BaseEffect = new FormLinkNullable<IMagicEffectGetter>(FormKey.Factory("0424E2:Skyrim.esm")),
                                                Data = new EffectData { Magnitude = mag, Area = 0, Duration = 0 } });
                    mod.Spells.Add(ab);
                    dmg[mag] = sk = ab.FormKey;
                }
                n.ActorEffect ??= new();
                n.ActorEffect.Add(new FormLink<ISpellRecordGetter>(sk));
            }
            mod.Npcs.Add(n);
            actor[name] = n.FormKey;
        }
        foreach (var f in Directory.EnumerateFiles(dir, "cy*.jsonl").Order())
            foreach (var line in File.ReadAllLines(f))
            {
                if (line.Length == 0) continue;
                var o = JsonDocument.Parse(line).RootElement;
                float G(string k) => (float)o.GetProperty(k).GetDouble();
                var pos = new P3Float(G("x"), G("y"), G("z"));
                var cell = ((int)Math.Floor(pos.X / CELL), (int)Math.Floor(pos.Y / CELL));
                if (!res.TryGetValue(cell, out var l)) res[cell] = l = new();
                l.Add((actor[o.GetProperty("actor").GetString()!], pos, G("rz"), uint.Parse(o.GetProperty("fid").GetString()!, System.Globalization.NumberStyles.HexNumber)));
            }
        return res;
    }

    // The ecology stage's critters (insects, fish, swarms): <plugin dir>/ecology/critters/cy<+NNN>.jsonl, one REFR a line
    // of the base a line names (a critter spawner of Skyrim.esm or a swarm of Black Marsh.esm: masters, linked as they
    // are, with their own spawn script and hours).
    static Dictionary<(int, int), List<(FormKey, P3Float, float, uint)>> Critters(string plugDir, ForeignCopy fc)
    {
        var res = new Dictionary<(int, int), List<(FormKey, P3Float, float, uint)>>();
        var dir = Path.Combine(plugDir, "ecology", "critters");
        if (!Directory.Exists(dir)) return res;
        var bases = new Dictionary<string, FormKey>();
        foreach (var f in Directory.EnumerateFiles(dir, "cy*.jsonl").Order())
            foreach (var line in File.ReadAllLines(f))
            {
                if (line.Length == 0) continue;
                var o = JsonDocument.Parse(line).RootElement;
                float G(string k) => (float)o.GetProperty(k).GetDouble();
                var src = o.GetProperty("base").GetString()!;
                if (!bases.TryGetValue(src, out var bk))
                {
                    var sp = src.Split(':', 2);
                    bases[src] = bk = fc.Get(sp[0], sp[1]);
                    if (!fc.IsAllowed(bk.ModKey)) throw new InvalidDataException($"critter base {src} is not a record of a master");
                }
                var pos = new P3Float(G("x"), G("y"), G("z"));
                var cell = ((int)Math.Floor(pos.X / CELL), (int)Math.Floor(pos.Y / CELL));
                if (!res.TryGetValue(cell, out var l)) res[cell] = l = new();
                l.Add((bk, pos, G("rz"), uint.Parse(o.GetProperty("fid").GetString()!, System.Globalization.NumberStyles.HexNumber)));
            }
        return res;
    }

    // The ecology stage's harvestables (tools/newworld/ecology/harvest.py): <plugin dir>/ecology/harvest/records.json names
    // the new FLOR records (a copy of a mesh's FLOR under a new name, yielding an existing or a new INGR whose effects are
    // taken from existing ingredients' effects), cy<+NNN>.jsonl one REFR a line of a record of a plugin we hold or of those.
    static Dictionary<(int, int), List<(FormKey, P3Float, float, float, uint)>> Harvest(string plugDir, ForeignCopy fc, FormIds ids, SkyrimMod mod)
    {
        var res = new Dictionary<(int, int), List<(FormKey, P3Float, float, float, uint)>>();
        var dir = Path.Combine(plugDir, "ecology", "harvest");
        if (!Directory.Exists(dir)) return res;
        var bases = new Dictionary<string, FormKey>();
        FormKey Of(string r) { var q = r.Split(':', 2); return fc.Get(q[0], q[1]); }
        var rj = Path.Combine(dir, "records.json");
        if (File.Exists(rj))
            foreach (var r in JsonDocument.Parse(File.ReadAllText(rj)).RootElement.GetProperty("records").EnumerateArray())
            {
                var edid = r.GetProperty("edid").GetString()!;
                var ing = r.GetProperty("ingr");
                var yields = Of(ing.GetProperty("from").GetString()!);
                if (ing.TryGetProperty("edid", out var ie))
                {
                    var sp = ing.GetProperty("from").GetString()!.Split(':', 2);
                    var srcI = mod.Ingredients[fc.Get(sp[0], sp[1], forceCopy: true)];
                    var ni = (Ingredient)srcI.Duplicate(new FormKey(mod.ModKey, ids.Take("base", "harvest-ingr:" + edid)));
                    ni.EditorID = ie.GetString();
                    ni.Name = new TranslatedString(Language.English, ing.GetProperty("name").GetString()!);
                    ni.Effects.Clear();
                    foreach (var ef in ing.GetProperty("effects").EnumerateArray())
                    {
                        var ep = ef[0].GetString()!.Split(':', 2);
                        var src = (IIngredientGetter)fc.Find(ep[0], ep[1]);
                        ni.Effects.Add(src.Effects[ef[1].GetInt32()].DeepCopy());
                    }
                    mod.Ingredients.Add(ni);
                    yields = ni.FormKey;
                }
                var fp = r.GetProperty("flor_from").GetString()!.Split(':', 2);
                var fkey = new FormKey(mod.ModKey, ids.Take("base", "harvest:" + edid));
                var fname = new TranslatedString(Language.English, r.GetProperty("flor_name").GetString()!);
                var copied = fc.Get(fp[0], fp[1], forceCopy: true);
                FormKey nfk;
                if (fc.Find(fp[0], fp[1]) is ITreeGetter)
                {
                    var nt = (Tree)mod.Trees[copied].Duplicate(fkey);
                    nt.EditorID = edid; nt.Name = fname; nt.Ingredient = new FormLinkNullable<IHarvestTargetGetter>(yields);
                    mod.Trees.Add(nt); nfk = nt.FormKey;
                }
                else
                {
                    var nf = (Flora)mod.Florae[copied].Duplicate(fkey);
                    nf.EditorID = edid; nf.Name = fname; nf.Ingredient = new FormLinkNullable<IHarvestTargetGetter>(yields);
                    mod.Florae.Add(nf); nfk = nf.FormKey;
                }
                bases["new:" + edid] = nfk;
            }
        foreach (var f in Directory.EnumerateFiles(dir, "cy*.jsonl").Order())
            foreach (var line in File.ReadAllLines(f))
            {
                if (line.Length == 0) continue;
                var o = JsonDocument.Parse(line).RootElement;
                float G(string k) => (float)o.GetProperty(k).GetDouble();
                var src = o.GetProperty("base").GetString()!;
                if (!bases.TryGetValue(src, out var bk)) bases[src] = bk = Of(src);
                var pos = new P3Float(G("x"), G("y"), G("z"));
                var cell = ((int)Math.Floor(pos.X / CELL), (int)Math.Floor(pos.Y / CELL));
                if (!res.TryGetValue(cell, out var l)) res[cell] = l = new();
                l.Add((bk, pos, G("rz"), G("scale"), uint.Parse(o.GetProperty("fid").GetString()!, System.Globalization.NumberStyles.HexNumber)));
            }
        return res;
    }

    // The small signature things (<plugin dir>/dressing/cy*.jsonl, tools/newworld/dressing/place.py): one reference a line,
    // its base from a master plugin (fc.Get), position, yaw, scale and form id.
    static Dictionary<(int, int), List<(FormKey, P3Float, float, float, uint)>> Dressing(string plugDir, ForeignCopy fc)
    {
        var res = new Dictionary<(int, int), List<(FormKey, P3Float, float, float, uint)>>();
        var dir = Path.Combine(plugDir, "dressing");
        if (!Directory.Exists(dir)) return res;
        var bases = new Dictionary<string, FormKey>();
        foreach (var f in Directory.EnumerateFiles(dir, "cy*.jsonl").Order())
            foreach (var line in File.ReadAllLines(f))
            {
                if (line.Length == 0) continue;
                var o = JsonDocument.Parse(line).RootElement;
                float G(string k) => (float)o.GetProperty(k).GetDouble();
                var src = o.GetProperty("base").GetString()!;
                if (!bases.TryGetValue(src, out var bk)) { var q = src.Split(':', 2); bases[src] = bk = fc.Get(q[0], q[1]); }
                var pos = new P3Float(G("x"), G("y"), G("z"));
                var cell = ((int)Math.Floor(pos.X / CELL), (int)Math.Floor(pos.Y / CELL));
                if (!res.TryGetValue(cell, out var l)) res[cell] = l = new();
                var fid = uint.Parse(o.GetProperty("fid").GetString()!, System.Globalization.NumberStyles.HexNumber);
                if (fid < IdDressing || fid > IdDressingEnd) throw new InvalidDataException($"dressing form id {fid:X6} lies outside {IdDressing:X6}..{IdDressingEnd:X6}");
                l.Add((bk, pos, G("rz"), G("scale"), fid));
            }
        return res;
    }

    // Placed refs from every producer's shards: <plugin dir>/refs/<producer>/cy<+NNN>.jsonl (format: cells.py).
    static Dictionary<(int, int), List<(FormKey, P3Float, P3Float, float, uint?)>> Refs(string plugDir, ForeignCopy fc)
    {
        var res = new Dictionary<(int, int), List<(FormKey, P3Float, P3Float, float, uint?)>>();
        var dir = Path.Combine(plugDir, "refs");
        if (!Directory.Exists(dir)) return res;
        var bases = new Dictionary<string, FormKey>();
        // NW_REF_PRODUCERS (comma list, e.g. "mist") limits the producers read; a shard a producer is replacing is skipped
        var only = Environment.GetEnvironmentVariable("NW_REF_PRODUCERS")?.Split(',', StringSplitOptions.RemoveEmptyEntries).ToHashSet();
        // a producer's bases.json may carry alternate textures for a base ("alt_textures": [{shape, index, slots[8]}],
        // tools/newworld/place/texsets.py): that base is always copied and the repair put on our copy's model
        var alts = new Dictionary<string, List<(string, int, string[])>>();
        foreach (var bj in Directory.EnumerateFiles(dir, "bases.json", SearchOption.AllDirectories).Order())
        {
            if (only is not null && !only.Contains(Path.GetFileName(Path.GetDirectoryName(bj)!))) continue;
            foreach (var e in JsonDocument.Parse(File.ReadAllText(bj)).RootElement.GetProperty("bases").EnumerateArray())
                if (e.TryGetProperty("alt_textures", out var at))
                    alts[e.GetProperty("ref").GetString()!] = at.EnumerateArray().Select(a => (a.GetProperty("shape").GetString()!,
                        a.GetProperty("index").GetInt32(), a.GetProperty("slots").EnumerateArray().Select(x => x.GetString() ?? "").ToArray())).ToList();
        }
        foreach (var f in Directory.EnumerateFiles(dir, "*.jsonl", SearchOption.AllDirectories).Order())
        {
            if (only is not null && !only.Contains(Path.GetFileName(Path.GetDirectoryName(f)!))) continue;
            string[] lines;
            try { lines = File.ReadAllLines(f); } catch (FileNotFoundException) { Console.WriteLine($"refs: {f} vanished while read, skipped"); continue; }
            foreach (var line in lines)
            {
                if (line.Length == 0) continue;
                var o = JsonDocument.Parse(line).RootElement;
                var b = o.GetProperty("base").GetString()!;
                if (!bases.TryGetValue(b, out var bk))
                {
                    var sp = b.Split(':', 2);
                    if (alts.TryGetValue(b, out var alt)) { bk = fc.Get(sp[0], sp[1], forceCopy: true); fc.AltTextures(bk, alt); }
                    else bk = fc.Get(sp[0], sp[1]);
                    bases[b] = bk;
                }
                float G(string k) => (float)o.GetProperty(k).GetDouble();
                var pos = new P3Float(G("x"), G("y"), G("z"));
                var cell = ((int)Math.Floor(pos.X / CELL), (int)Math.Floor(pos.Y / CELL));
                if (!res.TryGetValue(cell, out var l)) res[cell] = l = new();
                uint? fid = o.TryGetProperty("fid", out var fe) ? uint.Parse(fe.GetString()!, System.Globalization.NumberStyles.HexNumber) : null;
                l.Add((bk, pos, new P3Float(G("rx"), G("ry"), G("rz")), G("scale"), fid));
            }
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
        foreach (var need in new[] { "Skyrim.esm", "Update.esm" }) if (!masters.Contains(need)) Fail($"master {need} missing");
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
        // asset-only plugins: never a master, never a link target (owner ruling 2026-11-08)
        using var bmc = SkyrimMod.CreateFromBinaryOverlay(Path.Combine(data, "Black Marsh.esm"), Rel, Survey.NoStrings);
        var allowed = Allowed.Select(f => ModKey.FromFileName(f)).Append(mod.ModKey).ToHashSet();
        foreach (var m in masters) if (!allowed.Contains(ModKey.FromFileName(m))) Fail($"master {m} is not allowed");
        long links = 0, badLinks = 0;
        foreach (var r in mod.EnumerateMajorRecords())
            foreach (var l in r.EnumerateFormLinks())
            {
                links++;
                if (!l.IsNull && !allowed.Contains(l.FormKey.ModKey)) { badLinks++; Fail($"{r.FormKey} links into {l.FormKey.ModKey}"); }
            }
        // ground layers, water types, regions, refs
        var ours = mod.LandscapeTextures.ToDictionary(t => t.FormKey);
        var layerHist = new long[8]; long quads = 0, badLayers = 0;
        // the written layers against the painted shards texcheck measured: the same textures in the same order, every
        // opacity the shard's byte (so texcheck's rows hold for the ESM itself)
        var texDirC = Path.Combine(Path.GetDirectoryName(man.Dir)!, "tex");
        var texManC = JsonDocument.Parse(File.ReadAllText(Path.Combine(texDirC, "manifest.json"))).RootElement;
        int qBytesC = texManC.GetProperty("quad_bytes").GetInt32(), maxLC = texManC.GetProperty("max_layers").GetInt32();
        var matEdid = JsonDocument.Parse(File.ReadAllText(Path.Combine(texDirC, "materials.json"))).RootElement.EnumerateArray()
            .Select(m => "ANW_Ground_" + m.GetProperty("id").GetString()).ToList();
        var shardRow = new Dictionary<int, byte[]>(); long texDiff = 0, texQuads = 0;
        var watrCells = new Dictionary<string, int>(); long regionCells = 0, cellsAll = 0;
        var regionName = mod.Regions.ToDictionary(r => r.FormKey, r => r.EditorID ?? "");
        var refsByRegion = new Dictionary<string, int>(); var refsByBase = new Dictionary<FormKey, int>();
        using var sky = SkyrimMod.CreateFromBinaryOverlay(Path.Combine(data, "Skyrim.esm"), Rel, Survey.NoStrings);
        var watrName = sky.Waters.ToDictionary(w => w.FormKey, w => w.EditorID ?? "");
        foreach (var w in mod.Waters) watrName[w.FormKey] = w.EditorID ?? "";
        foreach (var b in ws.SubCells) foreach (var sb in b.Items) foreach (var c in sb.Items)
        {
            cellsAll++;
            var wn = c.Water.IsNull ? "(world) " + watrName.GetValueOrDefault(ws.Water.FormKey, ws.Water.FormKey.ToString()) : watrName.GetValueOrDefault(c.Water.FormKey, c.Water.FormKey.ToString());
            watrCells[wn] = watrCells.GetValueOrDefault(wn) + 1;
            var reg = c.Regions?.FirstOrDefault();
            if (reg is not null) regionCells++;
            foreach (var r in c.Temporary.OfType<IPlacedObjectGetter>())
            {
                if (r.EditorID == StartMarker) continue;
                refsByBase[r.Base.FormKey] = refsByBase.GetValueOrDefault(r.Base.FormKey) + 1;
                var rn = reg is null ? "(none)" : regionName.GetValueOrDefault(reg.FormKey, "?");
                refsByRegion[rn] = refsByRegion.GetValueOrDefault(rn) + 1;
            }
            var l = c.Landscape;
            if (l?.Layers is null) continue;
            foreach (var g in l.Layers.GroupBy(x => x.Header!.Quadrant))
            {
                quads++;
                var bases = g.Where(x => x is not IAlphaLayerGetter).ToList();
                var alphas = g.OfType<IAlphaLayerGetter>().ToList();
                layerHist[Math.Min(alphas.Count + bases.Count, 7)]++;
                bool ok = bases.Count == 1 && alphas.Count <= 5 &&  // six textures a quadrant: the shader's six slots
                           alphas.Select(x => (int)x.Header!.LayerNumber).SequenceEqual(Enumerable.Range(0, alphas.Count))
                          && g.All(x => ours.ContainsKey(x.Header!.Texture.FormKey))
                          && alphas.All(x => x.AlphaLayerData is { } d && d.All(p => p.Opacity > 0 && p.Opacity <= 1.0001f && p.Position < 289));
                if (!ok && badLayers++ < 5) Fail($"cell {c.Grid?.Point} quadrant {g.Key}: bad layers ({bases.Count} base, {alphas.Count} alpha)");
                if (ok && c.Grid is { } cg)
                {
                    int gx = cg.Point.X, gy = cg.Point.Y;
                    if (!shardRow.TryGetValue(gy, out var t))
                        shardRow[gy] = t = File.ReadAllBytes(Path.Combine(texDirC, $"cy{(gy < 0 ? "-" : "+")}{Math.Abs(gy):000}.bin"));
                    int o = (gx - cx0) * 4 * qBytesC + Array.IndexOf(Quads, g.Key) * qBytesC, n = t[o];
                    bool same = n == 1 + alphas.Count && ours[bases[0].Header!.Texture.FormKey].EditorID == matEdid[t[o + 1]];
                    for (var k = 1; same && k < n; k++)
                    {
                        var al = alphas[k - 1];
                        var op = new byte[289];
                        foreach (var pnt in al.AlphaLayerData!) op[pnt.Position] = (byte)Math.Round(pnt.Opacity * 255f);
                        same = ours[al.Header!.Texture.FormKey].EditorID == matEdid[t[o + 1 + k]]
                               && op.AsSpan().SequenceEqual(t.AsSpan(o + 1 + maxLC + (k - 1) * 289, 289));
                    }
                    texQuads++;
                    if (!same && texDiff++ < 5) Fail($"cell {gx},{gy} quadrant {g.Key}: the written layers are not the painted shard's");
                }
            }
        }
        if (quads != 4L * expected) Fail($"{quads} painted quadrants, expected {4L * expected}");
        if (regionCells != cellsAll) Fail($"{cellsAll - regionCells} cells without a region");
        var grassy = mod.LandscapeTextures.Count(t => t.Grasses?.Count > 0);
        var stats = man.Root.GetProperty("stats");
        Console.WriteLine($"newworld check: {esmPath} ({new FileInfo(esmPath).Length} bytes), build {man.BuildId}");
        Console.WriteLine($"  cells {heights.Count}/{expected} with LAND; vertices {verts}; max height error {maxErr:F2} units ({maxErr / 70:F3} m) at {maxAt}; >half-step {over4}");
        Console.WriteLine($"  seams {seamEdges} edges, {seamBad} mismatches; VHGT overflow pairs before/after limiter {stats.GetProperty("overflow_pairs_before")}/{stats.GetProperty("overflow_pairs_after")}, limited vertices {stats.GetProperty("limited_vertices")}");
        Console.WriteLine($"  water: WRLD default {ws.LandDefaults?.DefaultWaterHeight}, cells off {wrongWater}; {markerLine}; coc {StartCell} (unique)");
        Console.WriteLine($"  masters {string.Join(", ", masters)}; {links} links, {badLinks} into asset-only plugins");
        Console.WriteLine($"  ground: {quads} quadrants, layers per quadrant (base + alpha) {string.Join(" ", layerHist.Select((n, i) => $"{i}:{n}").Skip(1))}, bad {badLayers}; {texQuads - texDiff}/{texQuads} equal to the painted shards; our LTEX {ours.Count} ({grassy} with grass)");
        Console.WriteLine($"  water types by cell: {string.Join(", ", watrCells.OrderByDescending(x => x.Value).Take(12).Select(x => $"{x.Key} {x.Value}"))}");
        Console.WriteLine($"  regions: {mod.Regions.Count} REGN, cells with a region {regionCells}/{cellsAll}; climate {ws.Climate.FormKey}");
        Console.WriteLine($"  refs by region: {string.Join(", ", refsByRegion.OrderByDescending(x => x.Value).Select(x => $"{x.Key} {x.Value}"))}");
        Console.WriteLine($"  refs by base: {string.Join(", ", refsByBase.OrderByDescending(x => x.Value).Select(x => $"{x.Key} {x.Value}"))}");
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
