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
    static readonly FormKey MapMarkerBase = FormKey.Factory("000010:Skyrim.esm");

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
        var lo = mod.ModHeader.MasterReferences.Select(r => r.Master).Append(mod.ModKey).ToList();
        var dir = Path.GetDirectoryName(Path.GetFullPath(esm))!;
        var tmpDir = Path.Combine(dir, ".writing-map"); Directory.CreateDirectory(tmpDir);
        var tmp = Path.Combine(tmpDir, Path.GetFileName(esm));
        mod.BeginWrite.ToPath(tmp).WithLoadOrder(lo).WithDataFolder(data).SingleThread().Write();
        File.Move(tmp, esm, true);
        Directory.Delete(tmpDir);
        Console.WriteLine($"nwmap apply: {k} map markers, MNAM NW{ws.MapData.NorthwestCellCoords} SE{ws.MapData.SoutheastCellCoords} usable {ws.MapData.UsableDimensions}");
        return 0;
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
        if (ws.WorldMapOffsetScale != 1f) fails.Add($"ONAM scale {ws.WorldMapOffsetScale}, not 1");
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
        Console.WriteLine($"nwmap check: WRLD {World} MNAM usable {md.UsableDimensions} NW{md.NorthwestCellCoords} SE{md.SoutheastCellCoords} cam {md.CameraMinHeight}/{md.CameraMaxHeight}/{md.CameraInitialPitch}; ONAM scale {ws.WorldMapOffsetScale} offset {ws.WorldMapCellOffset}");
        Console.WriteLine($"  map markers {refs.Count} in the persistent cell (expected {mk.Count}), discovered {disc}");
        foreach (var f in fails.Take(20)) Console.WriteLine("  FAIL " + f);
        Console.WriteLine(fails.Count == 0 && refs.Count == mk.Count ? "  PASS" : $"  FAIL ({fails.Count})");
        return fails.Count == 0 && refs.Count == mk.Count ? 0 : 1;
    }
}
