// `cells`: every interior CELL's placed references with their bases and load-door partners, read from the load
// order's winning copies. Read-only; the output lands in out/ (decision 0003). One plugin at a time through the
// binary overlay, keeping only ids and small structs (the memory guidance), never a whole-environment LinkCache.
using System.Text;
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Archives;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Binary.Parameters;
using Mutagen.Bethesda.Strings;
using Mutagen.Bethesda.Plugins.Aspects;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Noggog;

namespace ArgoniaGen;

static class CellScan
{
    record Tele(FormKey Door, float[] Pos, float[] Rot);
    record Ref(FormKey Key, FormKey Base, float[] Pos, float[] Rot, float Scale, bool Persistent, bool Disabled, Tele? Tele);
    record CellRow(FormKey Key, string Edid, string Name, string Plugin, Dictionary<FormKey, Ref> Refs);
    record Base(string Type, string Edid, string Model);
    record Where(string Worldspace, string WorldspaceEdid, string Cell, int X, int Y, float[] Pos);

    static float[] V(P3Float p) => new[] { p.X, p.Y, p.Z };

    static Ref? ToRef(IPlacedGetter p)
    {
        if ((p.MajorRecordFlagsRaw & 0x20) != 0) return null; // deleted
        FormKey b; IPlacementGetter? pl; float scale = 1f; Tele? t = null;
        switch (p)
        {
            case IPlacedObjectGetter o:
                b = o.Base.FormKey; pl = o.Placement; scale = o.Scale ?? 1f;
                if (o.TeleportDestination is { } td && !td.Door.FormKey.IsNull)
                    t = new Tele(td.Door.FormKey, V(td.Position), V(td.Rotation));
                break;
            case IPlacedNpcGetter n: b = n.Base.FormKey; pl = n.Placement; break;
            default: return null;
        }
        if (pl is null || b.IsNull) return null;
        return new Ref(p.FormKey, b, V(pl.Position), V(pl.Rotation), scale,
                       (p.MajorRecordFlagsRaw & 0x400) != 0, (p.MajorRecordFlagsRaw & 0x800) != 0, t);
    }

    static IEnumerable<IPlacedGetter> Placed(ICellGetter c) => c.Persistent.Concat(c.Temporary);

    // Skyrim's string tables sit in its archives; Mutagen finds them through a Windows listings path that does not
    // exist here, so the English tables are extracted once beside the output and passed to the overlay.
    static string Strings(string data, string[] plugins, string outPath)
    {
        var stems = plugins.ToDictionary(p => Path.GetFileNameWithoutExtension(p).ToLowerInvariant(), p => Path.GetFileNameWithoutExtension(p));
        var dir = Path.Combine(Path.GetDirectoryName(Path.GetFullPath(outPath))!, "strings-cache");
        Directory.CreateDirectory(dir);
        foreach (var bsa in Directory.EnumerateFiles(data, "*.bsa"))
        {
            if (bsa.Contains("Textures") || bsa.Contains("Sounds") || bsa.Contains("Voices") || bsa.Contains("Meshes")) continue;
            foreach (var f in Archive.CreateReader(GameRelease.SkyrimSE, bsa).Files)
            {
                var n = f.Path.Replace('\\', '/');
                if (!n.StartsWith("strings/", StringComparison.OrdinalIgnoreCase) || !n.Contains("english", StringComparison.OrdinalIgnoreCase)) continue;
                var low = Path.GetFileName(n); var us = low.IndexOf("_english", StringComparison.Ordinal);
                if (us < 0 || !stems.TryGetValue(low[..us], out var stem)) continue;
                var dest = Path.Combine(dir, stem + "_English." + low[(low.LastIndexOf('.') + 1)..].ToUpperInvariant());
                if (!File.Exists(dest)) File.WriteAllBytes(dest, f.GetBytes().ToArray());
            }
        }
        return dir;
    }

    public static int Run(string data, string[] plugins, string outPath)
    {
        var strings = Strings(data, plugins, outPath);
        var rp = new BinaryReadParameters { StringsParam = new StringsReadParameters { StringsFolderOverride = strings,
                                                                                         BsaFolderOverride = Directory.CreateDirectory(Path.Combine(strings, "no-bsa")).FullName,
                                                                                         TargetLanguage = Language.English } };
        ISkyrimModDisposableGetter Open(string plugin) => SkyrimMod.CreateFromBinaryOverlay(Path.Combine(data, plugin), SkyrimRelease.SkyrimSE, rp);
        // Pass A: interior cells, merged per CELL FormKey across plugins (a later plugin's ref replaces by FormKey).
        var cells = new Dictionary<FormKey, CellRow>();
        foreach (var plugin in plugins)
        {
            using var mod = Open(plugin);
            foreach (var block in mod.Cells.Records)
                foreach (var sub in block.SubBlocks)
                    foreach (var c in sub.Cells)
                    {
                        if (!c.Flags.HasFlag(Mutagen.Bethesda.Skyrim.Cell.Flag.IsInteriorCell)) continue;
                        if (!cells.TryGetValue(c.FormKey, out var cell))
                            cells[c.FormKey] = cell = new CellRow(c.FormKey, "", "", plugin, new());
                        cells[c.FormKey] = cell = cell with { Edid = c.EditorID ?? cell.Edid, Name = c.Name?.String ?? cell.Name };
                        // the origin mod is the cell's own FormKey plugin, not the last override
                        foreach (var p in Placed(c))
                            if (ToRef(p) is { } r) cell.Refs[r.Key] = r;
                            else cell.Refs.Remove(p.FormKey);
                    }
        }
        var cellOf = new Dictionary<FormKey, FormKey>();
        foreach (var c in cells.Values) foreach (var r in c.Refs.Keys) cellOf[r] = c.Key;
        var bases = cells.Values.SelectMany(c => c.Refs.Values).Select(r => r.Base).ToHashSet();
        var partners = cells.Values.SelectMany(c => c.Refs.Values).Where(r => r.Tele is not null).Select(r => r.Tele!.Door)
            .Where(d => !cellOf.ContainsKey(d)).ToHashSet();

        // Pass B: the bases' winning type, EditorID and model; the exterior cells that hold a wanted partner door.
        var baseInfo = new Dictionary<FormKey, Base>();
        var outside = new Dictionary<FormKey, Where>();
        foreach (var plugin in plugins)
        {
            using var mod = Open(plugin);
            foreach (var r in mod.EnumerateMajorRecords())
                if (bases.Contains(r.FormKey))
                    baseInfo[r.FormKey] = new Base(r.Registration.ClassType.Name, r.EditorID ?? "",
                        r is IModeledGetter m && m.Model is { } mm ? PieceIndex.Norm(mm.File.DataRelativePath.Path) : "");
            if (partners.Count == 0) continue;
            foreach (var ws in mod.Worldspaces)
            {
                void Scan(ICellGetter c)
                {
                    foreach (var p in Placed(c))
                        if (partners.Contains(p.FormKey))
                            outside[p.FormKey] = new Where(Load.Key(ws.FormKey), ws.EditorID ?? "", Load.Key(c.FormKey),
                                                           c.Grid?.Point.X ?? 0, c.Grid?.Point.Y ?? 0,
                                                           p is IPlacedObjectGetter po && po.Placement is { } pp ? V(pp.Position) : new float[3]);
                }
                if (ws.TopCell is { } top) Scan(top);
                foreach (var block in ws.SubCells)
                    foreach (var sub in block.Items)
                        foreach (var c in sub.Items) Scan(c);
            }
        }

        // Output, streamed: cells by FormKey, refs by FormKey.
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(outPath))!);
        using var fs = File.Create(outPath);
        fs.Write(Encoding.UTF8.GetBytes("[\n"));
        var first = true;
        foreach (var c in cells.Values.OrderBy(c => Load.Key(c.Key), StringComparer.Ordinal))
        {
            using var buf = new MemoryStream();
            using (var w = new Utf8JsonWriter(buf))
            {
                w.WriteStartObject();
                w.WriteString("formKey", Load.Key(c.Key)); w.WriteString("edid", c.Edid); w.WriteString("name", c.Name);
                w.WriteString("plugin", c.Key.ModKey.FileName.String);
                w.WriteStartArray("refs");
                foreach (var r in c.Refs.Values.OrderBy(r => Load.Key(r.Key), StringComparer.Ordinal))
                {
                    baseInfo.TryGetValue(r.Base, out var bi);
                    w.WriteStartObject();
                    w.WriteString("formKey", Load.Key(r.Key)); w.WriteString("base", Load.Key(r.Base));
                    w.WriteString("baseType", bi?.Type ?? ""); w.WriteString("baseEdid", bi?.Edid ?? "");
                    w.WriteString("model", bi?.Model ?? "");
                    Vec(w, "pos", r.Pos); Vec(w, "rot", r.Rot); w.WriteNumber("scale", r.Scale);
                    w.WriteBoolean("persistent", r.Persistent); w.WriteBoolean("disabled", r.Disabled);
                    if (r.Tele is { } t)
                    {
                        w.WriteStartObject("teleport");
                        w.WriteString("door", Load.Key(t.Door));
                        if (cellOf.TryGetValue(t.Door, out var dc)) { w.WriteString("cell", Load.Key(dc)); w.WriteBoolean("interior", true); }
                        else if (outside.TryGetValue(t.Door, out var o))
                        {
                            w.WriteString("cell", o.Cell); w.WriteBoolean("interior", false);
                            w.WriteStartObject("exterior"); w.WriteString("worldspace", o.Worldspace);
                            w.WriteString("worldspaceEdid", o.WorldspaceEdid); w.WriteNumber("x", o.X); w.WriteNumber("y", o.Y); Vec(w, "doorPos", o.Pos);
                            w.WriteEndObject();
                        }
                        else w.WriteNull("cell");
                        Vec(w, "pos", t.Pos); Vec(w, "rot", t.Rot);
                        w.WriteEndObject();
                    }
                    else w.WriteNull("teleport");
                    w.WriteEndObject();
                }
                w.WriteEndArray(); w.WriteEndObject();
            }
            if (!first) fs.Write(Encoding.UTF8.GetBytes(",\n"));
            first = false;
            fs.Write(buf.ToArray());
        }
        fs.Write(Encoding.UTF8.GetBytes("\n]\n"));
        Console.WriteLine($"cells: {cells.Count} interior cells, {cells.Values.Sum(c => c.Refs.Count)} refs, {outside.Count}/{partners.Count} exterior partner doors found -> {outPath}");
        return 0;
    }

    static void Vec(Utf8JsonWriter w, string name, float[] v)
    {
        w.WriteStartArray(name); foreach (var x in v) w.WriteNumberValue(x); w.WriteEndArray();
    }
}
