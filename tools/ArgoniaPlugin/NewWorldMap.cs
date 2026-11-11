// The new world's native map (nw-02 step 11): the WRLD's map fields and one map marker per settlement, applied to
// ArgoniaNewWorld.esm in place after `newworld write` (rerunnable: our markers are replaced, never added twice).
// Inputs from `python -m tools.newworld.world.mapdata build` (<plugin>/map/map.json, markers.json). The vanilla way:
// a marker is a persistent ref of MapMarker (Skyrim.esm 000010) in the world's persistent cell with XMRK/FNAM/FULL/TNAM;
// flags Visible|CanTravelTo only on the start place (discovered), 0 on the rest (found by walking near them). The
// map itself is the world's terrain LOD seen by the map camera inside the NW/SE pan box (MNAM).
//   nwmap apply <esm> <mapdir> <data>    set MNAM, add the markers, write the ESM back
//   nwmap check <esm> <mapdir>           the WRLD's map fields and every marker against markers.json
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;
using Noggog;

static class NewWorldMap
{
    const SkyrimRelease Rel = SkyrimRelease.SkyrimSE;
    const string World = "ArgoniaBlackMarsh";
    const uint IdMarkers = 0xFF0000;  // marker k: IdMarkers + k (NewWorld.cs: cells 0x100000.., refs 0x200000..)
    const uint IdCoc = 0xFE0000;  // teleport marker k: IdCoc + k
    static readonly FormKey MapMarkerBase = FormKey.Factory("000010:Skyrim.esm");
    static readonly FormKey CocMarkerBase = FormKey.Factory("000032:Skyrim.esm");  // COCMarkerHeading

    public static int Run(string[] a) => a[0] switch
    {
        "apply" => Apply(a[1], a[2], a[3]),
        "check" => Check(a[1], a[2]),
        _ => throw new ArgumentException("nwmap apply <esm> <mapdir> <data> | check <esm> <mapdir>"),
    };

    static JsonElement Json(string p) => JsonDocument.Parse(File.ReadAllText(p)).RootElement;
    static P2Int16 P(JsonElement e) => new((short)e[0].GetInt32(), (short)e[1].GetInt32());

    static int Apply(string esm, string mapDir, string data)
    {
        var mp = Json(Path.Combine(mapDir, "map.json"));
        var mk = Json(Path.Combine(mapDir, "markers.json")).GetProperty("markers");
        var mod = SkyrimMod.CreateFromBinary(esm, Rel);
        var ws = mod.Worldspaces.Single(w => w.EditorID == World);
        ws.MapData ??= new WorldspaceMap();
        ws.MapData.UsableDimensions = new P2Int(mp.GetProperty("usable")[0].GetInt32(), mp.GetProperty("usable")[1].GetInt32());
        ws.MapData.NorthwestCellCoords = P(mp.GetProperty("nw"));
        ws.MapData.SoutheastCellCoords = P(mp.GetProperty("se"));
        if (mp.TryGetProperty("camera", out var cam))
        {
            ws.MapData.CameraMinHeight = (float)cam.GetProperty("min_height").GetDouble();
            ws.MapData.CameraMaxHeight = (float)cam.GetProperty("max_height").GetDouble();
            ws.MapData.CameraInitialPitch = (float)cam.GetProperty("pitch").GetDouble();
        }
        var bd = mp.GetProperty("bounds");  // NAM0/NAM9: DynDOLOD's Worldspace-Bounds check reads them
        ws.ObjectBoundsMin = new P2Float(bd[0].GetInt32(), bd[1].GetInt32());
        ws.ObjectBoundsMax = new P2Float(bd[2].GetInt32(), bd[3].GetInt32());
        ws.WorldMapOffsetScale = 1f;  // ONAM as Tamriel's (Skyrim.esm: scale 1, offset 0,0,0); 0 is no map
        ws.WorldMapCellOffset = new P3Float(0, 0, 0);
        var top = ws.TopCell ?? throw new InvalidDataException("WRLD has no persistent cell");
        top.Persistent.RemoveAll(r => r.FormKey.ModKey == mod.ModKey && r.FormKey.ID >= IdMarkers);
        uint k = 0;
        foreach (var m in mk.EnumerateArray())
        {
            var disc = m.GetProperty("discovered").GetBoolean();
            top.Persistent.Add(new PlacedObject(new FormKey(mod.ModKey, IdMarkers + k++), Rel)
            {
                EditorID = "ANW_MapMarker_" + m.GetProperty("place").GetString()!.Replace("-", "_"),
                Base = new FormLinkNullable<IPlaceableObjectGetter>(MapMarkerBase),
                Placement = new Placement { Position = new P3Float((float)m.GetProperty("x").GetDouble(), (float)m.GetProperty("y").GetDouble(), (float)m.GetProperty("z").GetDouble()) },
                MapMarker = new MapMarker
                {
                    Flags = disc ? MapMarker.Flag.Visible | MapMarker.Flag.CanTravelTo : 0,
                    Name = new TranslatedString(Language.English, m.GetProperty("name").GetString()),
                    Type = Enum.Parse<MapMarker.MarkerType>(m.GetProperty("type").GetString()!),
                },
            });
        }
        var nCoc = Teleports(mod, ws, mapDir);
        var (nFlag, nBill, nRule) = LodPlan(mod, mapDir, data);
        var lo = mod.ModHeader.MasterReferences.Select(r => r.Master).Append(mod.ModKey).ToList();
        var dir = Path.GetDirectoryName(Path.GetFullPath(esm))!;
        var tmpDir = Path.Combine(dir, ".writing-map"); Directory.CreateDirectory(tmpDir);
        var tmp = Path.Combine(tmpDir, Path.GetFileName(esm));
        mod.BeginWrite.ToPath(tmp).WithLoadOrder(lo).WithDataFolder(data).SingleThread().Write();
        File.Move(tmp, esm, true);
        Directory.Delete(tmpDir);
        Console.WriteLine($"nwmap apply: {k} map markers, MNAM NW{ws.MapData.NorthwestCellCoords} SE{ws.MapData.SoutheastCellCoords} usable {ws.MapData.UsableDimensions} cam {ws.MapData.CameraMinHeight}/{ws.MapData.CameraMaxHeight}/{ws.MapData.CameraInitialPitch}");
        Console.WriteLine($"  {nCoc} named teleport cells with a COCMarkerHeading; LOD plan: Has Tree LOD set on {nFlag} statics, {nBill} billboards forced, {nRule} object LOD rules");
        return 0;
    }

    static IEnumerable<Cell> Cells(IWorldspaceGetter ws) =>
        ws.SubCells.SelectMany(b => b.Items).SelectMany(sb => sb.Items).Cast<Cell>();

    static JsonElement? JsonIf(string p) => File.Exists(p) ? Json(p) : null;

    // The teleports (tools/newworld/teleports.py -> teleports.json): each named cell gets its editor id, as Skyrim names
    // its own exterior cells for `coc` (Riverwood), and one COCMarkerHeading (Skyrim.esm 000032) where the player lands,
    // the first teleport naming the cell. Ours are replaced on a rerun: our markers in IdCoc.., our ANW cell names.
    static int Teleports(SkyrimMod mod, Worldspace ws, string mapDir)
    {
        var doc = JsonIf(Path.Combine(mapDir, "teleports.json"));
        if (doc is not { } d) { Console.WriteLine("  no teleports.json: no teleport cells"); return 0; }
        var byGrid = Cells(ws).ToDictionary(c => (c.Grid!.Point.X, c.Grid.Point.Y));
        foreach (var c in byGrid.Values)
        {
            c.Temporary.RemoveAll(r => r.FormKey.ModKey == mod.ModKey && r.FormKey.ID >= IdCoc && r.FormKey.ID < IdMarkers);
            if (c.EditorID is { } e && e.StartsWith("ANW")) c.EditorID = null;
        }
        var clash = mod.EnumerateMajorRecords().FirstOrDefault(r => r.FormKey.ModKey == mod.ModKey && r.FormKey.ID >= IdCoc && r.FormKey.ID < IdMarkers);
        if (clash != null) throw new InvalidDataException($"form id {clash.FormKey} is in the teleport markers' range");
        uint k = 0;
        var done = new HashSet<string>();
        foreach (var t in d.GetProperty("teleports").EnumerateArray())
        {
            var name = t.GetProperty("coc").GetString()!;
            if (!done.Add(name) || name == "ArgoniaNWStart") continue;  // the start cell keeps NewWorld.cs's marker
            var g = t.GetProperty("cell");
            var cell = byGrid[(g[0].GetInt32(), g[1].GetInt32())];
            cell.EditorID = name;
            cell.Temporary.Add(new PlacedObject(new FormKey(mod.ModKey, IdCoc + k++), Rel)
            {
                EditorID = name + "Marker",
                Base = new FormLinkNullable<IPlaceableObjectGetter>(CocMarkerBase),
                Placement = new Placement
                {
                    Position = new P3Float((float)t.GetProperty("x").GetDouble(), (float)t.GetProperty("y").GetDouble(), (float)t.GetProperty("z").GetDouble()),
                    Rotation = new P3Float(0, 0, (float)t.GetProperty("rot_z").GetDouble()),
                },
            });
        }
        return (int)k;
    }

    // The LOD plan (tools/newworld/world/lodplan.py -> lodplan.json): "Has Tree LOD" on our STAT trees (DynDOLOD draws
    // a STAT in tree LOD only with it), and the files DynDOLOD reads from Data\DynDOLOD\ (dyndolod.info Mod-Authors,
    // TexGen-Configuration; lod.ps1 lays them), with this ESM's form ids:
    //   DynDOLOD_SSE_TexGen_Billboards_<plugin>.txt  "<plugin>;<form id>;<editor id>,True" per base whose billboard
    //       TexGen must make (its own filter wants "tree" in the model path), as its TexGen_SSE_Tree_Billboards.txt
    //   DynDOLOD_SSE_argonianewworldesm.ini  a plugin's rule file ([Skyrim LODGen], LODGen1..n), whose rules DynDOLOD
    //       lists ahead of the preset's catch-all: one mesh-mask rule per large static model without LOD models, its
    //       full model at LOD4 (and LOD8), "\<model>,Full,Full|None,None,None,FarLOD,Unchanged,0" (a plugin;form id
    //       mask is a reference's, never a base's); and one per heavy model with a derived LOD model
    //       (lodmodels.py), that model at LOD4: "<model>,Level0,None,None,None,FarLOD,Unchanged,0"
    static string Squash(string file) => new string(file.ToLowerInvariant().Where(char.IsLetterOrDigit).ToArray());

    static (int, int, int) LodPlan(SkyrimMod mod, string mapDir, string data)
    {
        var doc = JsonIf(Path.Combine(mapDir, "lodplan.json"));
        if (doc is not { } d) { Console.WriteLine("  no lodplan.json: no LOD plan"); return (0, 0, 0); }
        var ours = mod.EnumerateMajorRecords().Where(r => r.EditorID != null && (r is IStatic || r is ITree))
            .GroupBy(r => r.EditorID!).ToDictionary(g => g.Key, g => g.First());
        foreach (var s in mod.Statics) s.MajorFlags &= ~Static.MajorFlag.HasTreeLOD;
        // our overrides of masters' statics exist only for the flag: dropped, then made again from the plan
        foreach (var fk in mod.Statics.Where(s => s.FormKey.ModKey != mod.ModKey).Select(s => s.FormKey).ToList()) mod.Statics.Remove(fk);
        var masters = new Dictionary<ModKey, ISkyrimModDisposableGetter>();
        var bill = new Dictionary<string, List<string>>();
        var rules = new List<string>();
        int flags = 0;
        foreach (var b in d.GetProperty("bases").EnumerateArray())
        {
            var mech = b.GetProperty("mech").GetString();
            if (mech != "tree" && mech != "object" && mech != "lodmodel") continue;
            var edid = b.GetProperty("edid").GetString()!;
            string plugin; uint id;
            if (b.GetProperty("key").ValueKind == JsonValueKind.String)
            {
                var fk = FormKey.Factory(b.GetProperty("key").GetString()!);
                plugin = fk.ModKey.FileName; id = fk.ID;
                if (mech == "tree" && b.GetProperty("sig").GetString() == "STAT")
                {
                    // a master's static tree: an override of ours carries the flag (the master's record, flag added)
                    if (!mod.ModHeader.MasterReferences.Any(m => m.Master == fk.ModKey)) throw new InvalidDataException($"lodplan: {fk} is not of a master");
                    if (!masters.TryGetValue(fk.ModKey, out var m)) masters[fk.ModKey] = m = SkyrimMod.CreateFromBinaryOverlay(Path.Combine(data, fk.ModKey.FileName), Rel);
                    var src = m.Statics.FirstOrDefault(s => s.FormKey == fk) ?? throw new InvalidDataException($"lodplan: {fk} is no STAT in {fk.ModKey}");
                    var ov = (Static)src.DeepCopy();
                    ov.MajorFlags |= Static.MajorFlag.HasTreeLOD;
                    mod.Statics.Set(ov);
                    flags++;
                }
            }
            else
            {
                if (!ours.TryGetValue(edid, out var r)) throw new InvalidDataException($"lodplan: {edid} not in {mod.ModKey}");
                plugin = mod.ModKey.FileName; id = r.FormKey.ID;
                if (mech == "tree" && r is Static st) { st.MajorFlags |= Static.MajorFlag.HasTreeLOD; flags++; }
            }
            var key = $"{plugin.ToLowerInvariant()};{id:X8}";
            if (mech == "tree")
            {
                if (!bill.TryGetValue(plugin, out var l)) bill[plugin] = l = new();
                l.Add($"{key};{edid},True");
            }
            else
            {
                var mask = b.GetProperty("model").GetString()!.Replace('/', '\\').ToLowerInvariant();
                var lod8 = b.GetProperty("lod8").GetBoolean() ? "Full" : "None";
                var rule = mech == "lodmodel" ? $"{mask},Level0,None,None,None,FarLOD,Unchanged,0" : $"{mask},Full,{lod8},None,None,FarLOD,Unchanged,0";
                if (!rules.Any(r => r.StartsWith(mask + ","))) rules.Add(rule);
            }
        }
        foreach (var f in Directory.GetFiles(mapDir, "DynDOLOD_SSE_*")) File.Delete(f);
        foreach (var (plugin, lines) in bill)
            File.WriteAllLines(Path.Combine(mapDir, $"DynDOLOD_SSE_TexGen_Billboards_{Squash(plugin)}.txt"), lines);
        File.WriteAllLines(Path.Combine(mapDir, $"DynDOLOD_SSE_{Squash(mod.ModKey.FileName)}.ini"),
            rules.Select((r, i) => $"LODGen{i + 1}={r}").Prepend("[Skyrim LODGen]"));
        return (flags, bill.Values.Sum(l => l.Count), rules.Count);
    }

    static int Check(string esm, string mapDir)
    {
        var mp = Json(Path.Combine(mapDir, "map.json"));
        var mk = Json(Path.Combine(mapDir, "markers.json")).GetProperty("markers").EnumerateArray().ToList();
        using var mod = SkyrimMod.CreateFromBinaryOverlay(esm, Rel);
        var ws = mod.Worldspaces.Single(w => w.EditorID == World);
        var md = ws.MapData!;
        var fails = new List<string>();
        if (!md.NorthwestCellCoords.Equals(P(mp.GetProperty("nw"))) || !md.SoutheastCellCoords.Equals(P(mp.GetProperty("se")))) fails.Add("MNAM box differs from map.json");
        var bd = mp.GetProperty("bounds");
        if (ws.ObjectBoundsMin.X != bd[0].GetInt32() || ws.ObjectBoundsMin.Y != bd[1].GetInt32() || ws.ObjectBoundsMax.X != bd[2].GetInt32() || ws.ObjectBoundsMax.Y != bd[3].GetInt32()) fails.Add($"bounds {ws.ObjectBoundsMin}..{ws.ObjectBoundsMax}");
        if (ws.WorldMapOffsetScale != 1f) fails.Add($"bounds {ws.ObjectBoundsMin}..{ws.ObjectBoundsMax}; ONAM scale {ws.WorldMapOffsetScale}, not 1");
        var refs = (ws.TopCell?.Persistent ?? []).OfType<IPlacedObjectGetter>().Where(r => r.MapMarker != null).ToDictionary(r => r.EditorID ?? "", r => r);
        int disc = 0;
        foreach (var m in mk)
        {
            var id = "ANW_MapMarker_" + m.GetProperty("place").GetString()!.Replace("-", "_");
            if (!refs.TryGetValue(id, out var r)) { fails.Add($"{id} missing"); continue; }
            var p = r.Placement!.Position;
            if (Math.Abs(p.X - m.GetProperty("x").GetDouble()) > 1 || Math.Abs(p.Y - m.GetProperty("y").GetDouble()) > 1 || Math.Abs(p.Z - m.GetProperty("z").GetDouble()) > 1) fails.Add($"{id} at {p}");
            if (r.MapMarker!.Name?.String != m.GetProperty("name").GetString()) fails.Add($"{id} name {r.MapMarker.Name?.String}");
            if (r.Base.FormKey != MapMarkerBase) fails.Add($"{id} base {r.Base.FormKey}");
            var d = r.MapMarker.Flags.HasFlag(MapMarker.Flag.CanTravelTo);
            if (d != m.GetProperty("discovered").GetBoolean()) fails.Add($"{id} discovered={d}");
            if (d) disc++;
        }
        if (mp.TryGetProperty("camera", out var cam) && (md.CameraMaxHeight != (float)cam.GetProperty("max_height").GetDouble() || md.CameraMinHeight != (float)cam.GetProperty("min_height").GetDouble()))
            fails.Add($"camera {md.CameraMinHeight}/{md.CameraMaxHeight}, map.json {cam}");
        // teleports: every named cell has its name and one COCMarkerHeading at the landing
        int named = 0;
        if (JsonIf(Path.Combine(mapDir, "teleports.json")) is { } tp)
        {
            var byGrid = ws.SubCells.SelectMany(b => b.Items).SelectMany(sb => sb.Items).ToDictionary(c => (c.Grid!.Point.X, c.Grid.Point.Y));
            var seen = new HashSet<string>();
            foreach (var t in tp.GetProperty("teleports").EnumerateArray())
            {
                var name = t.GetProperty("coc").GetString()!;
                if (!seen.Add(name) || name == "ArgoniaNWStart") continue;
                var g = t.GetProperty("cell");
                var c = byGrid[(g[0].GetInt32(), g[1].GetInt32())];
                if (c.EditorID != name) { fails.Add($"cell {g} named {c.EditorID}, not {name}"); continue; }
                var m = c.Temporary.OfType<IPlacedObjectGetter>().Where(r => r.Base.FormKey == CocMarkerBase).ToList();
                if (m.Count != 1) { fails.Add($"{name}: {m.Count} COC markers"); continue; }
                var p = m[0].Placement!.Position;
                if (Math.Abs(p.X - t.GetProperty("x").GetDouble()) > 1 || Math.Abs(p.Y - t.GetProperty("y").GetDouble()) > 1) fails.Add($"{name} marker at {p}");
                named++;
            }
        }
        // the LOD plan: Has Tree LOD on exactly the statics planned as trees
        int flagged = 0;
        if (JsonIf(Path.Combine(mapDir, "lodplan.json")) is { } lp)
        {
            var plan = lp.GetProperty("bases").EnumerateArray().ToList();
            string Mech(JsonElement b) => b.GetProperty("mech").GetString()!;
            bool Keyed(JsonElement b) => b.GetProperty("key").ValueKind == JsonValueKind.String;
            // Has Tree LOD on exactly the statics planned as trees: ours by editor id, a master's on our override
            var want = plan.Where(b => Mech(b) == "tree" && !Keyed(b)).Select(b => b.GetProperty("edid").GetString()!).ToHashSet();
            var wantOv = plan.Where(b => Mech(b) == "tree" && Keyed(b) && b.GetProperty("sig").GetString() == "STAT")
                .Select(b => FormKey.Factory(b.GetProperty("key").GetString()!)).ToHashSet();
            foreach (var s in mod.Statics)
            {
                var has = s.MajorFlags.HasFlag(Static.MajorFlag.HasTreeLOD);
                if (has) flagged++;
                var should = s.FormKey.ModKey == mod.ModKey ? want.Contains(s.EditorID ?? "") : wantOv.Contains(s.FormKey);
                if (has != should) fails.Add($"{s.EditorID} {s.FormKey} Has Tree LOD {has}");
            }
            foreach (var fk in wantOv.Where(k => !mod.Statics.ContainsKey(k))) fails.Add($"no override of {fk} with Has Tree LOD");
            // each billboard line: <plugin>;<form id>;<edid>,True resolving to a planned tree that is a TREE or a flagged STAT here
            var trees = mod.Trees.ToDictionary(t => t.FormKey);
            var statics = mod.Statics.ToDictionary(s => s.FormKey);
            var planTrees = plan.Where(b => Mech(b) == "tree").ToDictionary(b => b.GetProperty("edid").GetString()!);
            int nb = 0;
            foreach (var f in Directory.GetFiles(mapDir, "DynDOLOD_SSE_TexGen_Billboards_*.txt"))
                foreach (var ln in File.ReadAllLines(f))
                {
                    nb++;
                    var m = System.Text.RegularExpressions.Regex.Match(ln, @"^([^;]+);([0-9A-F]{8});([^,]+),True$");
                    if (!m.Success) { fails.Add($"billboard line '{ln}'"); continue; }
                    if (!planTrees.TryGetValue(m.Groups[3].Value, out var pb)) { fails.Add($"billboard {m.Groups[3].Value} not planned as a tree"); continue; }
                    var plugin = mod.ModHeader.MasterReferences.Select(x => x.Master).Append(mod.ModKey).FirstOrDefault(k => k.FileName.String.Equals(m.Groups[1].Value, StringComparison.OrdinalIgnoreCase));
                    if (plugin.IsNull) { fails.Add($"billboard {ln}: {m.Groups[1].Value} is neither ours nor a master"); continue; }
                    var fk = new FormKey(plugin, Convert.ToUInt32(m.Groups[2].Value, 16) & 0xFFFFFF);
                    var ok = trees.ContainsKey(fk) || (statics.TryGetValue(fk, out var st) && st.MajorFlags.HasFlag(Static.MajorFlag.HasTreeLOD))
                             || (plugin != mod.ModKey && pb.GetProperty("sig").GetString() == "TREE" && Keyed(pb) && FormKey.Factory(pb.GetProperty("key").GetString()!) == fk);
                    if (!ok) fails.Add($"billboard {ln}: no TREE or Has-Tree-LOD STAT {fk} here");
                }
            var nt = planTrees.Count;
            if (nb != nt) fails.Add($"TexGen billboard files list {nb} bases, lodplan.json {nt}: nwmap apply owed");
            if (nt > 256) fails.Add($"{nt} tree billboards: past DynDOLOD's 256 a world");
            // the rule file: [Skyrim LODGen], LODGen1..n, 8 fields, the mask a planned object model, LOD8 as planned
            var rf = Path.Combine(mapDir, $"DynDOLOD_SSE_{Squash(mod.ModKey.FileName)}.ini");
            var objs = plan.Where(b => Mech(b) == "object" || Mech(b) == "lodmodel").GroupBy(b => b.GetProperty("model").GetString()!.Replace('/', '\\').ToLowerInvariant())
                .ToDictionary(g => g.Key, g => Mech(g.First()) == "lodmodel" ? "Level0,None" : g.First().GetProperty("lod8").GetBoolean() ? "Full,Full" : "Full,None");
            if (!File.Exists(rf)) fails.Add("no DynDOLOD rule file: nwmap apply owed");
            else
            {
                var lines = File.ReadAllLines(rf).Where(l => l.Trim() != "").ToList();
                if (lines.FirstOrDefault() != "[Skyrim LODGen]") fails.Add("rule file does not open with [Skyrim LODGen]");
                var seenMasks = new HashSet<string>();
                for (var i = 1; i < lines.Count; i++)
                {
                    var m = System.Text.RegularExpressions.Regex.Match(lines[i], @"^LODGen(\d+)=(.*)$");
                    var f = m.Success ? m.Groups[2].Value.Split(',') : [];
                    if (!m.Success || int.Parse(m.Groups[1].Value) != i) { fails.Add($"rule line {i} '{lines[i]}' not LODGen{i}"); continue; }
                    if (f.Length != 8) { fails.Add($"rule {i}: {f.Length} fields, not 8"); continue; }
                    if (f[0].StartsWith('\\') || !objs.TryGetValue(f[0], out var l8)) { fails.Add($"rule {i}: mask {f[0]} is no planned object model"); continue; }
                    seenMasks.Add(f[0]);
                    if ($"{f[1]},{f[2]}" != l8 || f[3] != "None" || f[4] != "None") fails.Add($"rule {i}: levels {string.Join(",", f[1..5])}, plan {l8}");
                }
                foreach (var miss in objs.Keys.Where(k => !seenMasks.Contains(k))) fails.Add($"planned object model {miss} has no rule");
            }
        }
        Console.WriteLine($"  teleport cells named with their marker {named}; statics with Has Tree LOD {flagged}");
        Console.WriteLine($"nwmap check: WRLD {World} MNAM usable {md.UsableDimensions} NW{md.NorthwestCellCoords} SE{md.SoutheastCellCoords} cam {md.CameraMinHeight}/{md.CameraMaxHeight}/{md.CameraInitialPitch}; ONAM scale {ws.WorldMapOffsetScale} offset {ws.WorldMapCellOffset}");
        Console.WriteLine($"  map markers {refs.Count} in the persistent cell (expected {mk.Count}), discovered {disc}");
        foreach (var f in fails.Take(20)) Console.WriteLine("  FAIL " + f);
        Console.WriteLine(fails.Count == 0 && refs.Count == mk.Count ? "  PASS" : $"  FAIL ({fails.Count})");
        return fails.Count == 0 && refs.Count == mk.Count ? 0 : 1;
    }
}
