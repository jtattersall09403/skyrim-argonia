// `sound study <out.json> <Data dir> <plugin names...>`: every REGN with Sounds data (Override/priority, music, each
// sound with flags and chance) and every SNDR those regions name (category, conditions, output model, files count),
// as the load order's last winner. Read only; feeds newworld/sources/identity/sound_measured.json.
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Cache;
using Mutagen.Bethesda.Skyrim;

static class SoundStudy
{
    public static int Run(string[] a)
    {
        var data = a[2];
        var mods = a[3..].Select(p => SkyrimMod.CreateFromBinaryOverlay(Path.Combine(data, p), SkyrimRelease.SkyrimSE, Survey.NoStrings)).ToList();
        var cache = mods.Cast<ISkyrimModGetter>().ToImmutableLinkCache<ISkyrimMod, ISkyrimModGetter>();
        var regions = new List<object>();
        var sndr = new Dictionary<string, object>();
        foreach (var m in mods)
            foreach (var r in m.Regions)
            {
                if (r.Sounds is null) continue;
                var s = r.Sounds;
                var l = new List<object>();
                foreach (var x in s.Sounds ?? (IReadOnlyList<IRegionSoundGetter>)Array.Empty<IRegionSoundGetter>())
                {
                    var key = x.Sound.FormKey;
                    l.Add(new { sound = Id(cache, key), flags = x.Flags.ToString(), chance = x.Chance });
                    if (!sndr.ContainsKey(key.ToString()) && cache.TryResolve<ISoundDescriptorGetter>(key, out var dd)) sndr[key.ToString()] = Desc(dd);
                }
                regions.Add(new { plugin = m.ModKey.FileName.String, formkey = r.FormKey.ToString(), edid = r.EditorID, flags = s.Flags.ToString(),
                    priority = s.Priority, music = s.Music.IsNull ? null : Id(cache, s.Music.FormKey), sounds = l });
            }
        var all = new List<object>();
        foreach (var m in mods)
            foreach (var d in m.SoundDescriptors)
                all.Add(new { plugin = m.ModKey.FileName.String, formkey = d.FormKey.ToString(), edid = d.EditorID, files = d.SoundFiles.Count,
                    time = string.Join(" ", d.Conditions.Where(c => c.Data is IGetCurrentTimeConditionDataGetter).Select(c => c.CompareOperator + ((c as IConditionFloatGetter)?.ComparisonValue.ToString() ?? "?"))),
                    loop = d.LoopAndRumble?.Loop.ToString() });
        File.WriteAllText(a[1], JsonSerializer.Serialize(new { regions, descriptors = sndr, all }));
        Console.WriteLine($"sound study: {regions.Count} regions with sounds, {sndr.Count} descriptors -> {a[1]}");
        return 0;
    }

    static string Id(ILinkCache c, FormKey k) => c.TryResolveIdentifier(k, out var e) && e is not null ? $"{k.ModKey.FileName}:{e}" : k.ToString();

    static object Desc(ISoundDescriptorGetter d) => new
    {
        edid = d.EditorID, type = d.Type.ToString(), category = d.Category.IsNull ? null : d.Category.FormKey.ToString(),
        output = d.OutputModel.IsNull ? null : d.OutputModel.FormKey.ToString(), files = d.SoundFiles.Count, firstFile = d.SoundFiles.FirstOrDefault(),
        conditions = d.Conditions.Select(c => c.Data?.ToString() + " " + (c.CompareOperator) + " " + (c is IConditionFloatGetter f ? f.ComparisonValue : 0)).ToList(),
        loop = d.LoopAndRumble?.Loop.ToString(),
    };
}
