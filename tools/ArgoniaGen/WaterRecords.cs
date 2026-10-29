// The water (2.W2) in ArgoniaWorld.esm (decision 0031 §1): the WATR types and water-plane activators from
// <water>/records.json, and on each exterior CELL its water height, water type, HasWater and the plane and piece
// references from <water>/cells.jsonl (tools/argonia_world/water: `python -m tools.argonia_world.water plan`).
// As Generate.cs: no unit maths and no choices; every number, id and link arrives resolved. The WRLD's default
// water links the sea type (the first WATR).
//   records.json: {"schema": 1, "records": [WATR {formKey, edid, name, opacity, shallowColor, deepColor,
//                  reflectionColor: [r,g,b], fogAbove, fogUnder: [near, far, amount]}, ACTI {formKey, edid, model,
//                  bounds: [[x,y,z],[x,y,z]], waterType}]}
//   cells.jsonl:  {"x", "y", "waterHeight"?, "waterType"?, "refs": [{formKey, base, pos, rot, scale}]}
using System.Text.Json;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;
using Noggog;

namespace ArgoniaGen;

sealed class WaterRecords
{
    const SkyrimRelease Rel = SkyrimRelease.SkyrimSE;
    readonly Dictionary<(int, int), string> lines = new();
    readonly HashSet<(int, int)> applied = new();

    static string S(JsonElement e, string k) => e.GetProperty(k).GetString() ?? throw new InvalidDataException($"{k} is null");
    static FormKey FK(string s) => FormKey.Factory(s);
    static float F(JsonElement e, int i) => e[i].GetSingle();
    static System.Drawing.Color Rgb(JsonElement e, string k)
    {
        var c = e.GetProperty(k);
        return System.Drawing.Color.FromArgb(c[0].GetInt32(), c[1].GetInt32(), c[2].GetInt32());
    }

    /// The types and activators into the mod, the WRLD's default water, and the cell lines indexed by grid.
    public static WaterRecords Load(SkyrimMod mod, Worldspace ws, string dir)
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(Path.Combine(dir, "records.json")));
        if (doc.RootElement.GetProperty("schema").GetInt32() != 1) throw new InvalidDataException("water records schema must be 1");
        FormKey? sea = null;
        foreach (var r in doc.RootElement.GetProperty("records").EnumerateArray())
        {
            switch (S(r, "type"))
            {
                case "WATR": { var k = Type(mod, r); sea ??= k; break; }  // the first type is the sea
                case "ACTI": Plane(mod, r); break;
                default: throw new InvalidDataException($"water records: no writer for {S(r, "type")}");
            }
        }
        if (sea is { } s) ws.Water.SetTo(s);
        var w = new WaterRecords();
        foreach (var line in File.ReadLines(Path.Combine(dir, "cells.jsonl")))
        {
            if (line.Length == 0) continue;
            using var cd = JsonDocument.Parse(line);
            var key = (cd.RootElement.GetProperty("x").GetInt32(), cd.RootElement.GetProperty("y").GetInt32());
            if (!w.lines.TryAdd(key, line)) throw new InvalidDataException($"water: cell {key} twice");
        }
        return w;
    }

    static FormKey Type(SkyrimMod mod, JsonElement r)
    {
        var fa = r.GetProperty("fogAbove");
        var fu = r.GetProperty("fogUnder");
        var t = new Water(FK(S(r, "formKey")), Rel)
        {
            EditorID = S(r, "edid"),
            Name = new TranslatedString(Language.English, S(r, "name")),
            Opacity = (byte)r.GetProperty("opacity").GetInt32(),
            ShallowColor = Rgb(r, "shallowColor"),
            DeepColor = Rgb(r, "deepColor"),
            ReflectionColor = Rgb(r, "reflectionColor"),
            FogAboveWaterDistanceNearPlane = F(fa, 0),
            FogAboveWaterDistanceFarPlane = F(fa, 1),
            FogAboveWaterAmount = F(fa, 2),
            FogUnderWaterDistanceNearPlane = F(fu, 0),
            FogUnderWaterDistanceFarPlane = F(fu, 1),
            FogUnderWaterAmount = F(fu, 2),
        };
        mod.Waters.Add(t);
        return t.FormKey;
    }

    static void Plane(SkyrimMod mod, JsonElement r)
    {
        var b = r.GetProperty("bounds");
        P3Int16 P(JsonElement v) => new((short)v[0].GetInt32(), (short)v[1].GetInt32(), (short)v[2].GetInt32());
        var a = new Mutagen.Bethesda.Skyrim.Activator(FK(S(r, "formKey")), Rel)
        {
            EditorID = S(r, "edid"),
            ObjectBounds = new ObjectBounds { First = P(b[0]), Second = P(b[1]) },
            Model = new Model { File = S(r, "model") },
        };
        a.WaterType.SetTo(FK(S(r, "waterType")));
        mod.Activators.Add(a);
    }

    /// The cell's water height, type, HasWater and references, if the plan has a line for it.
    public void ApplyCell(Cell c, int x, int y)
    {
        if (!lines.TryGetValue((x, y), out var line)) return;
        using var doc = JsonDocument.Parse(line);
        var e = doc.RootElement;
        c.Flags |= Cell.Flag.HasWater;
        if (e.TryGetProperty("waterHeight", out var h))
        {
            c.WaterHeight = h.GetSingle();
            c.Water.SetTo(FK(S(e, "waterType")));
        }
        foreach (var p in e.GetProperty("refs").EnumerateArray())
        {
            var pos = p.GetProperty("pos");
            var rot = p.GetProperty("rot");
            var o = new PlacedObject(FK(S(p, "formKey")), Rel)
            {
                Placement = new Placement
                {
                    Position = new P3Float(F(pos, 0), F(pos, 1), F(pos, 2)),
                    Rotation = new P3Float(F(rot, 0), F(rot, 1), F(rot, 2)),
                },
            };
            o.Base.SetTo(FK(S(p, "base")));
            var sc = p.GetProperty("scale").GetSingle();
            if (Math.Abs(sc - 1f) > 1e-6) o.Scale = sc;
            c.Temporary.Add(o);
        }
        applied.Add((x, y));
    }

    /// Every water line found its cell (a line without a LAND cell is a plan error, never skipped).
    public void CheckAllApplied()
    {
        var missing = lines.Keys.Where(k => !applied.Contains(k)).Order().Take(5).ToList();
        if (missing.Count > 0)
            throw new InvalidDataException($"water: {lines.Count - applied.Count} cell lines have no exterior cell, first {string.Join(", ", missing)}");
    }

    public int Cells => applied.Count;
}
