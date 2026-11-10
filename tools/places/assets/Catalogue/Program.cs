// The place studio's catalogue reader (docs/design/place-studio.md, tools/places/assets/catalogue.py).
// Usage: Catalogue <out dir> <plugin path>... (load order, earliest first). Writes:
//   bases.raw.jsonl  every base with a model, the last plugin's version winning: key (origin plugin:6-hex id),
//                    edid, type, name, model, bounds, plugin (the winner), keywords (editor ids)
//   lights.jsonl     every light base, with or without a model: key, edid, model, plugin, light {radius, colour,
//                    flags, fov}
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
// every light base, with or without a model (a bare light has none), the last plugin's version winning: what a
// place's own lights are chosen from (a shadow caster's no-shadow twin, a forge's fire light)
var lights = new Dictionary<string, Dictionary<string, object?>>();
foreach (var m in mods)
    foreach (var li in m.Lights)
        try
        {
            lights[Key(li.FormKey)] = new() { ["key"] = Key(li.FormKey), ["edid"] = li.EditorID, ["type"] = "Light", ["kind"] = "light",
                ["model"] = li.Model?.File.DataRelativePath.Path, ["plugin"] = m.ModKey.FileName.String,
                ["light"] = new { radius = li.Radius, colour = new[] { li.Color.R, li.Color.G, li.Color.B }, flags = li.Flags.ToString(), fov = li.FOV } };
        }
        catch (Exception e) { Console.Error.WriteLine($"{m.ModKey} LIGH {li.FormKey}: {e.Message}"); }
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
                // an item form's value and enchantment (the record's own, as the stocking extractor reads it), so its
                // tier on the stocking scale is right before stockdb measures it
                (long? value, FormKey ench) = r switch
                {
                    IWeaponGetter x => ((long?)x.BasicStats?.Value, x.ObjectEffect.FormKey),
                    IArmorGetter x => (x.Value, x.ObjectEffect.FormKey),
                    IBookGetter x => (x.Value, FormKey.Null),
                    IIngestibleGetter x => (x.Value, FormKey.Null),
                    IIngredientGetter x => (x.Value, FormKey.Null),
                    IMiscItemGetter x => (x.Value, FormKey.Null),
                    ISoulGemGetter x => (x.Value, FormKey.Null),
                    IAmmunitionGetter x => (x.Value, FormKey.Null),
                    IKeyGetter x => (x.Value, FormKey.Null),
                    IScrollGetter x => (x.Value, FormKey.Null),
                    ILightGetter x => (x.Value, FormKey.Null),
                    _ => ((long?)null, FormKey.Null),
                };
                if (value != null)
                {
                    rows[key]["value"] = value;
                    rows[key]["ench"] = ench.IsNull ? null : Key(ench);
                    // the enchantment's grade, by vanilla's naming of its enchantments (EnchWeaponShockDamage03 is grade 3)
                    if (!ench.IsNull && cache.TryResolve<IObjectEffectGetter>(ench, out var en)
                        && System.Text.RegularExpressions.Regex.Match(en.EditorID ?? "", @"(\d\d)$") is { Success: true } g)
                        rows[key]["ench_grade"] = int.Parse(g.Groups[1].Value);
                }
            }
            catch (Exception e) { Console.Error.WriteLine($"{m.ModKey} {code} {r.FormKey}: {e.Message}"); }
        }
    }
}
Directory.CreateDirectory(outDir);
var opt = new JsonSerializerOptions { Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping };
using (var w = new StreamWriter(Path.Combine(outDir, "bases.raw.jsonl")))
    foreach (var k in order) w.WriteLine(JsonSerializer.Serialize(rows[k], opt));
using (var w = new StreamWriter(Path.Combine(outDir, "lights.jsonl")))
    foreach (var k in lights.Keys.OrderBy(k => k, StringComparer.Ordinal)) w.WriteLine(JsonSerializer.Serialize(lights[k], opt));
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
