// The place studio's catalogue reader (docs/design/place-studio.md, tools/places/assets/catalogue.py).
// Usage: Catalogue <out dir> <plugin path>... (load order, earliest first). Writes:
//   bases.raw.jsonl  every base with a model, the last plugin's version winning: key (origin plugin:6-hex id),
//                    edid, type, name, model, bounds, plugin (the winner), keywords (editor ids)
//   ltex.jsonl       every land texture: key, edid, plugin, txst, diffuse, normal
// Plugins are read as overlays; names come from the plugin's strings when it is localized.
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Plugins.Aspects;
using Mutagen.Bethesda.Skyrim;

var outDir = args[0];
var paths = args.Skip(1).ToList();
var mods = new List<ISkyrimModGetter>();
var Strings = StringsFor();
foreach (var p in paths)
{
    try { mods.Add(SkyrimMod.CreateFromBinaryOverlay(p, SkyrimRelease.SkyrimSE, Strings)); }
    catch (Exception e) { Console.Error.WriteLine($"skip {p}: {e.Message}"); }
}
var cache = mods.ToImmutableLinkCache();
// a localized plugin's names: the string files catalogue.py unpacked from the game's archives (ARGONIA_STRINGS)
static Mutagen.Bethesda.Plugins.Binary.Parameters.BinaryReadParameters StringsFor()
{
    var dir = Environment.GetEnvironmentVariable("ARGONIA_STRINGS") ?? Directory.CreateTempSubdirectory("places-strings").FullName;
    return new() { StringsParam = new Mutagen.Bethesda.Strings.StringsReadParameters { StringsFolderOverride = dir, BsaFolderOverride = dir } };
}
string Key(FormKey k) => $"{k.ModKey.FileName}:{k.ID:X6}";

var kinds = new (string code, Func<ISkyrimModGetter, IEnumerable<IMajorRecordGetter>> get)[] {
    ("STAT", m => m.Statics), ("MSTT", m => m.MoveableStatics), ("FURN", m => m.Furniture), ("DOOR", m => m.Doors),
    ("CONT", m => m.Containers), ("LIGH", m => m.Lights), ("ACTI", m => m.Activators), ("TACT", m => m.TalkingActivators),
    ("TREE", m => m.Trees), ("FLOR", m => m.Florae), ("GRAS", m => m.Grasses), ("MISC", m => m.MiscItems),
    ("BOOK", m => m.Books), ("INGR", m => m.Ingredients), ("ALCH", m => m.Ingestibles), ("KEYM", m => m.Keys),
    ("SCRL", m => m.Scrolls), ("SLGM", m => m.SoulGems), ("WEAP", m => m.Weapons), ("AMMO", m => m.Ammunitions),
    ("APPA", m => m.AlchemicalApparatuses), ("IDLM", m => m.IdleMarkers), ("ARMO", m => m.Armors),
};
var nameErrors = 0;
var rows = new Dictionary<string, Dictionary<string, object?>>();
var order = new List<string>();
foreach (var m in mods)
{
    foreach (var (code, get) in kinds)
    {
        IEnumerable<IMajorRecordGetter> recs;
        try { recs = get(m).ToList(); } catch (Exception e) { Console.Error.WriteLine($"{m.ModKey} {code}: {e.Message}"); continue; }
        foreach (var r in recs)
        {
            try
            {
                string? model = r switch
                {
                    IArmorGetter a => a.WorldModel?.Male?.Model?.File.DataRelativePath.Path ?? a.WorldModel?.Female?.Model?.File.DataRelativePath.Path,
                    IModeledGetter md => md.Model?.File.DataRelativePath.Path,
                    _ => null,
                };
                if (string.IsNullOrWhiteSpace(model)) continue;
                model = model.Replace('\\', '/').ToLowerInvariant();
                if (model.StartsWith("meshes/")) model = model[7..];
                List<int[]>? bounds = null;
                if (r is IObjectBoundedGetter ob && ob.ObjectBounds is { } b)
                    bounds = new() { new[] { (int)b.First.X, b.First.Y, b.First.Z }, new[] { (int)b.Second.X, b.Second.Y, b.Second.Z } };
                string? name = null;
                if (r is INamedGetter nm) { try { name = nm.Name; } catch (Exception e) { if (nameErrors++ < 3) Console.Error.WriteLine($"name {r.FormKey}: {e.Message}"); } }
                var kw = new List<string>();
                if (r is IKeywordedGetter<IKeywordGetter> kd && kd.Keywords != null)
                    foreach (var l in kd.Keywords) kw.Add(cache.TryResolve<IKeywordGetter>(l.FormKey, out var k) ? (k.EditorID ?? Key(l.FormKey)) : Key(l.FormKey));
                var key = Key(r.FormKey);
                if (!rows.ContainsKey(key)) order.Add(key);
                rows[key] = new() { ["key"] = key, ["edid"] = r.EditorID, ["type"] = code, ["name"] = name, ["model"] = model,
                                    ["bounds"] = bounds, ["plugin"] = m.ModKey.FileName.String, ["keywords"] = kw };
            }
            catch (Exception e) { Console.Error.WriteLine($"{m.ModKey} {code} {r.FormKey}: {e.Message}"); }
        }
    }
}
Directory.CreateDirectory(outDir);
var opt = new JsonSerializerOptions { Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping };
using (var w = new StreamWriter(Path.Combine(outDir, "bases.raw.jsonl")))
    foreach (var k in order) w.WriteLine(JsonSerializer.Serialize(rows[k], opt));
var lt = new Dictionary<string, Dictionary<string, object?>>();
foreach (var m in mods)
    foreach (var l in m.LandscapeTextures)
    {
        string? dif = null, nrm = null, ts = null;
        if (cache.TryResolve<ITextureSetGetter>(l.TextureSet.FormKey, out var t))
        {
            ts = Key(t.FormKey);
            dif = t.Diffuse?.DataRelativePath.Path; nrm = t.NormalOrGloss?.DataRelativePath.Path;
        }
        lt[Key(l.FormKey)] = new() { ["key"] = Key(l.FormKey), ["edid"] = l.EditorID, ["plugin"] = m.ModKey.FileName.String,
                                      ["txst"] = ts, ["diffuse"] = dif?.Replace('\\', '/').ToLowerInvariant(), ["normal"] = nrm?.Replace('\\', '/').ToLowerInvariant() };
    }
using (var w = new StreamWriter(Path.Combine(outDir, "ltex.jsonl")))
    foreach (var v in lt.Values) w.WriteLine(JsonSerializer.Serialize(v, opt));
Console.WriteLine($"{rows.Count} bases, {lt.Count} land textures from {mods.Count} plugins");
