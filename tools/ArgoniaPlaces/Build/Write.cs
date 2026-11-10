// write <out.esp> <world.esm> <plan.json...>: the place layer plugin from the shards tools/places/build.py plans.
// Every decision is in the plan; this only turns rows into records:
//   - the world's WRLD, its persistent cell and each touched CELL as overrides that carry only their header (the
//     world's own refs, LAND and NAVM stay the world's) plus what the plan adds: our refs, the cleared refs (the
//     world's ref with Initially Disabled set), LAND (the world's record with our VHGT/VNML and added alpha layers),
//     NAVM (the plan's bytes);
//   - interiors: new cells whose header is the source cell's (links out of our masters copied by ForeignCopy, its
//     location and encounter zone dropped), holding our refs and navmesh;
//   - people (People.cs); the NAVI override with every NVMI of ours.
// A base or any link in a plugin that is not one of our masters is copied in as ours (ForeignCopy.cs).
using System.Diagnostics;
using System.Text;
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Binary.Streams;
using Mutagen.Bethesda.Plugins.Masters;
using Mutagen.Bethesda.Plugins.Meta;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;
using Noggog;

static class Write
{
    public static readonly string[] Masters = { "Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm", "Black Marsh.esm" };
    public const uint CopyFirst = 0x001000;  // ForeignCopy's range: below every place block (0x10000 on)

    public static ParsingMeta Meta(IEnumerable<string> masters, string self)
    {
        var key = ModKey.FromFileName(self);
        var refs = new MasterReferenceCollection(key, masters.Select(m => new MasterReference { Master = ModKey.FromFileName(m) }));
        var pkg = SeparatedMasterPackage.Factory(GameRelease.SkyrimSE, key, MasterStyle.Full, refs, null);
        return new ParsingMeta(GameConstants.Get(GameRelease.SkyrimSE), key, pkg);
    }

    public static MutagenFrame Frame(byte[] b, ParsingMeta meta) => new(new MutagenMemoryReadStream(b, meta, 0));

    static P3Float P(JsonElement e) => new((float)e[0].GetDouble(), (float)e[1].GetDouble(), (float)e[2].GetDouble());
    static string? S(JsonElement e, string k) => e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() : null;
    static bool B(JsonElement e, string k) => e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.True;
    static bool Has(JsonElement e, string k) => e.TryGetProperty(k, out var v) && v.ValueKind != JsonValueKind.Null;

    public sealed class Ctx
    {
        public required SkyrimMod Mod;
        public required ForeignCopy Fc;
        public required ISkyrimModGetter World;
        public HashSet<ModKey> Allowed = new();
        public Dictionary<FormKey, FormKey> Remap = new();
        /// A key of a base or link: ours or a master's as it is; any other plugin's copied in as ours.
        public FormKey Link(string key)
        {
            var fk = C.Fk(key);
            if (fk.ModKey == Mod.ModKey || Allowed.Contains(fk.ModKey)) return fk;
            if (!Remap.TryGetValue(fk, out var ours)) Remap[fk] = ours = Fc.Get(fk, fk.ModKey.FileName);
            return ours;
        }
        /// Every link of a record into a plugin that is not a master: copied in and remapped.
        public void Localize(IMajorRecord r)
        {
            var map = new Dictionary<FormKey, FormKey>();
            foreach (var l in r.EnumerateFormLinks())
            {
                var k = l.FormKey;
                if (k.IsNull || k.ModKey == Mod.ModKey || Allowed.Contains(k.ModKey)) continue;
                map[k] = Link(C.Key(k));
            }
            if (map.Count > 0) r.RemapLinks(map);
        }
    }

    public static int Run(string esp, string worldEsm, string[] shards)
    {
        var sw = Stopwatch.StartNew();
        var world = C.Open(worldEsm);
        var ws = world.Worldspaces.Single();
        var mod = new SkyrimMod(ModKey.FromFileName(Path.GetFileName(esp)), C.Rel);
        mod.ModHeader.Author = "Argonia";
        mod.ModHeader.Description = "The new world's places: built by tools/places/build.py";
        var fc = new ForeignCopy(mod, Masters.Select(m => ModKey.FromFileName(m)).Append(world.ModKey), C.Data, CopyFirst);
        var ctx = new Ctx { Mod = mod, Fc = fc, World = world };
        ctx.Allowed.UnionWith(Masters.Select(m => ModKey.FromFileName(m)));
        ctx.Allowed.Add(world.ModKey);

        // the WRLD override: its header only; its persistent cell's header; the touched cells' headers
        var noChildren = new Cell.TranslationMask(true) { Persistent = false, Temporary = false, NavigationMeshes = false, Landscape = false };
        var wso = ws.DeepCopy(new Worldspace.TranslationMask(true) { SubCells = false, TopCell = false });
        mod.Worldspaces.Add(wso);
        wso.TopCell = ws.TopCell!.DeepCopy(noChildren);
        var worldCells = new Dictionary<(int, int), ICellGetter>();
        var want = new HashSet<(int, int)>();
        var plans = shards.Select(p => JsonDocument.Parse(File.ReadAllText(p))).ToList();
        foreach (var d in plans) foreach (var c in d.RootElement.GetProperty("cells").EnumerateArray()) want.Add((c.GetProperty("x").GetInt32(), c.GetProperty("y").GetInt32()));
        foreach (var c in C.Cells(ws)) if (c.Grid is { } g && want.Contains((g.Point.X, g.Point.Y))) worldCells[(g.Point.X, g.Point.Y)] = c;
        var cells = new Dictionary<(int, int), Cell>();
        Cell Ext(int x, int y)
        {
            if (cells.TryGetValue((x, y), out var c)) return c;
            if (!worldCells.TryGetValue((x, y), out var wc)) throw new InvalidDataException($"cell {x},{y} is not in the world (or not in the plan's cells)");
            return cells[(x, y)] = wc.DeepCopy(noChildren);
        }
        var interiors = new Dictionary<string, Cell>();
        var nvmi = new List<byte[]>();
        int nRefs = 0, nClear = 0, nLand = 0, nNavm = 0;
        var refByKey = new Dictionary<string, PlacedObject>();

        foreach (var doc in plans)
        {
            var plan = doc.RootElement;
            var pid = plan.GetProperty("place_id").GetString()!;
            // interiors
            foreach (var I in plan.GetProperty("interiors").EnumerateArray())
            {
                var fk = C.Fk(I.GetProperty("fk").GetString()!);
                Cell cell;
                if (I.TryGetProperty("copy", out var cp) && cp.ValueKind == JsonValueKind.Object)
                {
                    var src = C.Open(cp.GetProperty("plugin").GetString()!).EnumerateMajorRecords<ICellGetter>().First(x => x.FormKey == C.Fk(cp.GetProperty("cell").GetString()!));
                    cell = (Cell)src.Duplicate(fk, noChildren);
                    cell.Location.Clear(); cell.EncounterZone.Clear(); cell.Owner.Clear(); cell.Regions = null;
                    ctx.Localize(cell);
                }
                else cell = new Cell(fk, C.Rel) { Flags = Cell.Flag.IsInteriorCell };
                cell.EditorID = I.GetProperty("edid").GetString();
                cell.Name = new TranslatedString(Language.English, I.GetProperty("name").GetString() ?? cell.EditorID);
                if (S(I, "owner") is { } ow) cell.Owner.SetTo(ctx.Link(ow));
                interiors[I.GetProperty("space").GetString()!] = cell;
                AddInterior(mod, cell);
            }
            // refs
            foreach (var r in plan.GetProperty("refs").EnumerateArray())
            {
                var o = MakeRef(ctx, r);
                refByKey[C.Key(o.FormKey)] = o;
                var space = r.GetProperty("space").GetString()!;
                var persistent = B(r, "persistent");
                if (space == "exterior")
                {
                    var c = r.GetProperty("cell");
                    var cell = Ext(c[0].GetInt32(), c[1].GetInt32());
                    if (persistent) wso.TopCell.Persistent.Add(o); else cell.Temporary.Add(o);
                }
                else
                {
                    var cell = interiors[space];
                    if (persistent) cell.Persistent.Add(o); else cell.Temporary.Add(o);
                }
                nRefs++;
            }
            // cleared world refs: the world's ref, Initially Disabled
            foreach (var r in plan.GetProperty("clear").EnumerateArray())
            {
                var fk = C.Fk(r.GetProperty("fk").GetString()!);
                var c = r.GetProperty("cell");
                var (x, y) = (c[0].GetInt32(), c[1].GetInt32());
                var wc = worldCells[(x, y)];
                var src = wc.Temporary.FirstOrDefault(q => q.FormKey == fk);
                if (src != null)
                {
                    var copy = (IPlaced)src.DeepCopy();
                    copy.MajorRecordFlagsRaw |= 0x800;
                    Ext(x, y).Temporary.Add(copy);
                }
                else
                {
                    var p = ws.TopCell!.Persistent.FirstOrDefault(q => q.FormKey == fk) ?? throw new InvalidDataException($"cleared ref {C.Key(fk)} not in cell {x},{y}");
                    var copy = (IPlaced)p.DeepCopy();
                    copy.MajorRecordFlagsRaw |= 0x800;
                    wso.TopCell.Persistent.Add(copy);
                }
                nClear++;
            }
            // land
            foreach (var L in plan.GetProperty("land").EnumerateArray())
            {
                int x = L.GetProperty("x").GetInt32(), y = L.GetProperty("y").GetInt32();
                var cell = Ext(x, y);
                var land = worldCells[(x, y)].Landscape!.DeepCopy();
                if (L.TryGetProperty("heights", out var h) && h.ValueKind == JsonValueKind.Object)
                {
                    var d = Convert.FromBase64String(h.GetProperty("deltas").GetString()!);
                    var n = Convert.FromBase64String(h.GetProperty("normals").GetString()!);
                    var hm = new Array2d<sbyte>(33, 33, 0);
                    var nm = new Array2d<P3UInt8>(33, 33, new P3UInt8(0, 0, 0));
                    for (var j = 0; j < 33; j++)
                        for (var i = 0; i < 33; i++)
                        {
                            var p = j * 33 + i;
                            hm[i, j] = unchecked((sbyte)d[p]);
                            nm[i, j] = new P3UInt8(n[3 * p], n[3 * p + 1], n[3 * p + 2]);
                        }
                    land.VertexHeightMap = new LandscapeVertexHeightMap { Offset = (float)h.GetProperty("offset").GetDouble(), HeightMap = hm };
                    land.VertexNormals = nm;
                }
                if (L.TryGetProperty("layers", out var ls) && ls.ValueKind == JsonValueKind.Array)
                {
                    if (land.Layers is null) throw new InvalidDataException($"cell {x},{y}: the world LAND has no layers");
                    foreach (var a in ls.EnumerateArray())
                    {
                        var q = (Quadrant)a.GetProperty("quadrant").GetInt32();
                        var next = land.Layers.Where(z => z.Header!.Quadrant == q && z is AlphaLayer).Select(z => (int)z.Header!.LayerNumber).DefaultIfEmpty(-1).Max() + 1;
                        var ad = new ExtendedList<AlphaLayerData>();
                        foreach (var pv in a.GetProperty("alpha").EnumerateArray())
                            ad.Add(new AlphaLayerData { Position = (ushort)pv[0].GetInt32(), Opacity = (float)pv[1].GetDouble() });
                        land.Layers.Add(new AlphaLayer
                        {
                            Header = new LayerHeader { Texture = new FormLink<ILandscapeTextureGetter>(ctx.Link(a.GetProperty("texture").GetString()!)), Quadrant = q, LayerNumber = (ushort)next },
                            AlphaLayerData = ad,
                        });
                    }
                }
                cell.Landscape = land;
                nLand++;
            }
            // navmesh: the plan's records, written against its masters
            var nav = plan.GetProperty("navmesh");
            var meta = Meta(nav.GetProperty("masters").EnumerateArray().Select(e => e.GetString()!), nav.GetProperty("self").GetString()!);
            foreach (var n in nav.GetProperty("navm").EnumerateArray())
            {
                var rec = NavigationMesh.CreateFromBinary(Frame(Convert.FromBase64String(n.GetProperty("record").GetString()!), meta));
                rec.IsCompressed = true;
                var space = n.GetProperty("space").GetString()!;
                if (space == "exterior") { var c = n.GetProperty("cell"); Ext(c[0].GetInt32(), c[1].GetInt32()).NavigationMeshes.Add(rec); }
                else interiors[space].NavigationMeshes.Add(rec);
                nvmi.Add(Convert.FromBase64String(n.GetProperty("nvmi").GetString()!));
                nNavm++;
            }
            // people
            if (plan.TryGetProperty("people", out var people) && people.ValueKind == JsonValueKind.Object)
                People.Build(ctx, pid, people, refByKey, interiors);
            if (plan.TryGetProperty("boats", out var boats) && boats.ValueKind == JsonValueKind.Array)
                Boat.Build(ctx, boats);
            if (plan.TryGetProperty("shrines", out var shrines) && shrines.ValueKind == JsonValueKind.Array)
                Shrine.Build(ctx, shrines);
            Console.WriteLine($"write: {pid}");
        }

        // the cells into the WRLD override's blocks
        foreach (var g in cells.GroupBy(kv => (kv.Key.Item1 >> 5, kv.Key.Item2 >> 5)))
        {
            var b = new WorldspaceBlock { BlockNumberX = (short)g.Key.Item1, BlockNumberY = (short)g.Key.Item2, GroupType = GroupTypeEnum.ExteriorCellBlock };
            foreach (var sg in g.GroupBy(kv => (kv.Key.Item1 >> 3, kv.Key.Item2 >> 3)))
            {
                var sb = new WorldspaceSubBlock { BlockNumberX = (short)sg.Key.Item1, BlockNumberY = (short)sg.Key.Item2, GroupType = GroupTypeEnum.ExteriorCellSubBlock };
                sb.Items.AddRange(sg.OrderBy(kv => kv.Key).Select(kv => kv.Value));
                b.Items.Add(sb);
            }
            wso.SubCells.Add(b);
        }
        // the NAVI override: our NVMI only (Bethesda's plugins carry only their own and overridden navmeshes' NVMI)
        if (nvmi.Count > 0)
        {
            var meta = Meta(new[] { "Skyrim.esm", world.ModKey.FileName.String }, mod.ModKey.FileName);
            mod.NavigationMeshInfoMaps.Add(NavigationMeshInfoMap.CreateFromBinary(Frame(Navi(nvmi), meta)));
        }
        WriteMod(mod, esp, world);
        Console.WriteLine($"write: {esp}: {nRefs} refs, {interiors.Count} interiors, {nClear} cleared, {nLand} LAND, {nNavm} NAVM, {cells.Count} cell overrides, {sw.Elapsed.TotalSeconds:F1} s");
        return 0;
    }

    public static void AddInterior(SkyrimMod mod, Cell cell)
    {
        var id = (int)cell.FormKey.ID;
        int blk = id % 10, sub = id / 10 % 10;
        var b = mod.Cells.Records.FirstOrDefault(x => x.BlockNumber == blk);
        if (b == null) { b = new CellBlock { BlockNumber = blk, GroupType = GroupTypeEnum.InteriorCellBlock }; mod.Cells.Records.Add(b); }
        var s = b.SubBlocks.FirstOrDefault(x => x.BlockNumber == sub);
        if (s == null) { s = new CellSubBlock { BlockNumber = sub, GroupType = GroupTypeEnum.InteriorCellSubBlock }; b.SubBlocks.Add(s); }
        s.Cells.Add(cell);
    }

    static PlacedObject MakeRef(Ctx ctx, JsonElement r)
    {
        var o = new PlacedObject(C.Fk(r.GetProperty("fk").GetString()!), C.Rel);
        o.Base.SetTo(ctx.Link(r.GetProperty("base").GetString()!));
        o.Placement = new Placement { Position = P(r.GetProperty("pos")), Rotation = P(r.GetProperty("rot")) };
        var sc = r.TryGetProperty("scale", out var s) && s.ValueKind == JsonValueKind.Number ? s.GetSingle() : 1f;
        if (Math.Abs(sc - 1f) > 1e-6) o.Scale = sc;
        uint flags = 0;
        if (B(r, "persistent")) flags |= 0x400;
        if (B(r, "disabled")) flags |= 0x800;
        o.MajorRecordFlagsRaw = (int)flags;
        if (S(r, "edid") is { } ed) o.EditorID = ed;
        if (r.TryGetProperty("teleport", out var t) && t.ValueKind == JsonValueKind.Object)
        {
            o.TeleportDestination = new TeleportDestination { Position = P(t.GetProperty("pos")), Rotation = P(t.GetProperty("rot")) };
            o.TeleportDestination.Door.SetTo(C.Fk(t.GetProperty("to").GetString()!));
        }
        if (S(r, "owner") is { } owner) o.Owner.SetTo(ctx.Link(owner));
        if (r.TryGetProperty("lock", out var lk) && lk.ValueKind == JsonValueKind.Number)
            o.Lock = new LockData { Level = (LockLevel)lk.GetInt32() };
        if (r.TryGetProperty("linked", out var ln) && ln.ValueKind == JsonValueKind.Array)
            foreach (var l in ln.EnumerateArray())
            {
                var lr = new LinkedReferences();
                lr.Reference.SetTo(ctx.Link(l.GetProperty("ref").GetString()!));
                if (S(l, "keyword") is { Length: > 0 } kw) lr.KeywordOrReference.SetTo(ctx.Link(kw));
                o.LinkedReferences.Add(lr);
            }
        if (S(r, "enable_parent") is { } ep)
        {
            o.EnableParent = new EnableParent(); o.EnableParent.Reference.SetTo(ctx.Link(ep));
            if (S(r, "enable_parent_flags") is { Length: > 0 } epf) o.EnableParent.Flags = Enum.Parse<EnableParent.Flag>(epf);
        }
        return o;
    }

    static byte[] Navi(List<byte[]> nvmi)
    {
        using var subs = new MemoryStream();
        void Sub(string sig, byte[] p)
        {
            if (p.Length > 0xFFFF) { subs.Write(Encoding.ASCII.GetBytes("XXXX")); subs.Write(BitConverter.GetBytes((ushort)4)); subs.Write(BitConverter.GetBytes((uint)p.Length)); subs.Write(Encoding.ASCII.GetBytes(sig)); subs.Write(BitConverter.GetBytes((ushort)0)); }
            else { subs.Write(Encoding.ASCII.GetBytes(sig)); subs.Write(BitConverter.GetBytes((ushort)p.Length)); }
            subs.Write(p);
        }
        Sub("NVER", BitConverter.GetBytes(12u));
        foreach (var m in nvmi) Sub("NVMI", m);
        Sub("NVPP", new byte[8]);
        var body = subs.ToArray();
        using var rec = new MemoryStream();
        rec.Write(Encoding.ASCII.GetBytes("NAVI"));
        rec.Write(BitConverter.GetBytes((uint)body.Length));
        rec.Write(BitConverter.GetBytes(0u));
        rec.Write(BitConverter.GetBytes(0x012FB4u));  // Skyrim.esm (index 0)'s NAVI
        rec.Write(BitConverter.GetBytes(0u));
        rec.Write(BitConverter.GetBytes((ushort)44));
        rec.Write(BitConverter.GetBytes((ushort)0));
        rec.Write(body);
        return rec.ToArray();
    }

    static void WriteMod(SkyrimMod mod, string esp, ISkyrimModGetter world)
    {
        var lo = Masters.Select(m => ModKey.FromFileName(m)).Append(world.ModKey).Append(mod.ModKey).ToList();
        var known = Masters.Select(m => (IModMasterStyledGetter)C.Open(m)).Append(world).ToArray();
        var dir = Path.GetDirectoryName(Path.GetFullPath(esp))!;
        var tmpDir = Path.Combine(dir, ".writing"); Directory.CreateDirectory(tmpDir);
        var tmp = Path.Combine(tmpDir, Path.GetFileName(esp));  // same file name: Mutagen matches it to the mod key
        mod.BeginWrite.ToPath(tmp).WithLoadOrder(lo).WithKnownMasters(known).SingleThread().Write();
        File.Move(tmp, esp, true);
        Directory.Delete(tmpDir);
    }
}
