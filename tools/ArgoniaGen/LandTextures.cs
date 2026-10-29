// LTEX: the landscape textures' grass lists (2.W1; decision 0006: no Nordic grass reaches the marsh).
//   ltex --data <dir> --plugins a.esm,b.esp --out <json>   every LTEX's winning copy (its fields and grass list)
//                                                          and every GRAS with the plugins that define or override it
//   Write: an LTEX override in Argonia.esm, every field resolved by Python from that scan (no lookups here).
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;

namespace ArgoniaGen;

static class LandTextures
{
    public static int Scan(string data, string[] plugins, string outPath)
    {
        var ltex = new Dictionary<FormKey, object>();
        var gras = new Dictionary<FormKey, (string Edid, string Model, List<string> Plugins)>();
        foreach (var plugin in plugins)  // one pass per plugin: the last copy wins, as in the game
        {
            using var mod = Load.Open(data, plugin);
            foreach (var l in mod.LandscapeTextures)
                ltex[l.FormKey] = new
                {
                    formKey = Load.Key(l.FormKey), edid = l.EditorID ?? "", winner = plugin,
                    textureSet = l.TextureSet.FormKeyNullable is { } t ? Load.Key(t) : null,
                    materialType = Load.Key(l.MaterialType.FormKey), friction = l.HavokFriction,
                    restitution = l.HavokRestitution, specular = l.TextureSpecularExponent,
                    flags = l.Flags.HasValue ? (int?)(int)l.Flags.Value : null,
                    grasses = l.Grasses.Select(g => Load.Key(g.FormKey)).ToArray(),
                };
            foreach (var g in mod.Grasses)
            {
                if (!gras.TryGetValue(g.FormKey, out var e)) gras[g.FormKey] = e = (g.EditorID ?? "", "", new List<string>());
                gras[g.FormKey] = (g.EditorID ?? e.Edid, g.Model?.File.DataRelativePath.Path ?? e.Model, e.Plugins);
                e.Plugins.Add(plugin);
            }
        }
        Load.WriteJson(outPath, new
        {
            plugins,
            ltex = Ordered(ltex).Select(kv => kv.Value).ToList(),
            grass = Ordered(gras).Select(kv => (object)new { formKey = Load.Key(kv.Key), edid = kv.Value.Edid, model = kv.Value.Model, plugins = kv.Value.Plugins }).ToList(),
        });
        Console.WriteLine($"ltex: {ltex.Count} LTEX, {gras.Count} GRAS -> {outPath}");
        return 0;
    }

    static IEnumerable<KeyValuePair<FormKey, T>> Ordered<T>(Dictionary<FormKey, T> d) =>
        d.OrderBy(kv => kv.Key.ModKey.FileName.String, StringComparer.Ordinal).ThenBy(kv => kv.Key.ID);

    static string S(JsonElement e, string k) => e.GetProperty(k).GetString() ?? throw new InvalidDataException($"{k} is null");

    public static void Write(SkyrimMod mod, JsonElement r)
    {
        var l = new LandscapeTexture(FormKey.Factory(S(r, "formKey")), SkyrimRelease.SkyrimSE)
        {
            EditorID = S(r, "edid"),
            HavokFriction = (byte)r.GetProperty("friction").GetInt32(),
            HavokRestitution = (byte)r.GetProperty("restitution").GetInt32(),
            TextureSpecularExponent = (byte)r.GetProperty("specular").GetInt32(),
        };
        if (r.TryGetProperty("textureSet", out var t) && t.ValueKind == JsonValueKind.String) l.TextureSet.SetTo(FormKey.Factory(t.GetString()!));
        l.MaterialType.SetTo(FormKey.Factory(S(r, "materialType")));
        if (r.TryGetProperty("flags", out var f) && f.ValueKind == JsonValueKind.Number) l.Flags = (LandscapeTexture.Flag)f.GetInt32();
        foreach (var g in r.GetProperty("grasses").EnumerateArray())
            l.Grasses.Add(new FormLink<IGrassGetter>(FormKey.Factory(g.GetString()!)));
        mod.LandscapeTextures.Add(l);
    }
}
