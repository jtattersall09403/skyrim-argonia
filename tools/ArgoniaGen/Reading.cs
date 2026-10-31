// The read-only commands: counts (0.1), the piece index and the vanilla quest scan. Outputs land in out/,
// never in git: they are derived from the player's game files (decision 0003).
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Archives;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Aspects;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;

namespace ArgoniaGen;

static class Load
{
    public static ISkyrimModDisposableGetter Open(string data, string plugin)
    {
        var path = Path.Combine(data, plugin);
        if (!File.Exists(path)) throw new FileNotFoundException($"not found: {path}");
        return SkyrimMod.CreateFromBinaryOverlay(path, SkyrimRelease.SkyrimSE);
    }

    public static readonly JsonSerializerOptions Json = new() { WriteIndented = true };

    public static void WriteJson(string path, object value)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(path))!);
        File.WriteAllText(path, JsonSerializer.Serialize(value, Json) + "\n");
    }

    public static string Key(FormKey k) => k.ToString();
}

static class Counts
{
    public static int Run(string data)
    {
        using var mod = Load.Open(data, "Skyrim.esm");
        var counts = mod.EnumerateMajorRecords()
            .GroupBy(r => r.Registration.Name)
            .Select(g => (Type: g.Key, Count: g.Count()))
            .OrderByDescending(t => t.Count)
            .Take(10);
        Console.WriteLine($"Skyrim.esm: {mod.EnumerateMajorRecords().Count()} major records");
        foreach (var (type, count) in counts) Console.WriteLine($"{type,-28}{count,8}");
        return 0;
    }
}

static class PieceIndex
{
    // Every base record with a model, by normalised mesh path, and every mesh in the plugins' archives.
    public static int Run(string data, string[] plugins, string outPath)
    {
        // The winning record per FormKey: an override later in the load order replaces its master's model.
        var won = new Dictionary<FormKey, Dictionary<string, string>>();
        var meshes = new SortedSet<string>(StringComparer.Ordinal);
        foreach (var plugin in plugins)
        {
            using var mod = Load.Open(data, plugin);
            foreach (var r in mod.EnumerateMajorRecords())
            {
                if (r is not IModeledGetter m || string.IsNullOrEmpty(m.Model?.File.DataRelativePath.Path)) continue;
                won[r.FormKey] = new()
                {
                    ["mesh"] = Norm(m.Model!.File.DataRelativePath.Path),
                    ["plugin"] = plugin, // the plugin whose copy wins
                    ["formKey"] = Load.Key(r.FormKey),
                    ["type"] = r.Registration.ClassType.Name,
                    ["edid"] = r.EditorID ?? "",
                };
            }
            // Only mesh-bearing archives: "<plugin>.bsa" and "<plugin> - Meshes*.bsa" (the vanilla split).
            var stem = Path.GetFileNameWithoutExtension(plugin);
            foreach (var bsa in Directory.EnumerateFiles(data, stem + "*.bsa"))
            {
                var n = Path.GetFileNameWithoutExtension(bsa);
                if (n.Equals(stem, StringComparison.OrdinalIgnoreCase) || n.Contains("Meshes", StringComparison.OrdinalIgnoreCase))
                    AddArchive(bsa, meshes);
            }
        }
        var loose = Path.Combine(data, "meshes");
        if (Directory.Exists(loose))
            foreach (var f in Directory.EnumerateFiles(loose, "*.nif", SearchOption.AllDirectories))
                meshes.Add(Norm(Path.GetRelativePath(data, f)));
        // Meshes laid on the game machine by mods the build VM does not hold: one path per line.
        var lists = Path.Combine(data, "argonia-mesh-lists");
        if (Directory.Exists(lists))
            foreach (var f in Directory.EnumerateFiles(lists, "*.txt"))
                foreach (var line in File.ReadLines(f))
                    if (line.Trim() is { Length: > 0 } l && l.EndsWith(".nif", StringComparison.OrdinalIgnoreCase)) meshes.Add(Norm(l));
        var records = won.Values.ToList();
        records.Sort((a, b) => string.CompareOrdinal(a["mesh"] + a["formKey"], b["mesh"] + b["formKey"]));
        Load.WriteJson(outPath, new { plugins, records, meshes });
        Console.WriteLine($"index: {records.Count} modelled base records, {meshes.Count} meshes -> {outPath}");
        return 0;
    }

    static void AddArchive(string bsa, SortedSet<string> meshes)
    {
        var reader = Archive.CreateReader(GameRelease.SkyrimSE, bsa);
        foreach (var f in reader.Files)
            if (f.Path.EndsWith(".nif", StringComparison.OrdinalIgnoreCase)) meshes.Add(Norm(f.Path));
    }

    // meshes/ prefixed, forward slashes, lower case: the one spelling pieces.py compares.
    public static string Norm(string p)
    {
        var s = p.Replace('\\', '/').TrimStart('/').ToLowerInvariant();
        return s.StartsWith("meshes/") ? s : "meshes/" + s;
    }
}

static class QuestScan
{
    // The quarantine's input: every quest the masters start by themselves and every music type, so the
    // generator can shell them (decision 0012).
    public static int Run(string data, string[] plugins, string outPath)
    {
        // One pass per plugin; the winning copy of each quest, story-manager node and music type decides.
        var quests = new Dictionary<FormKey, (string Edid, int Flags)>();
        var nodes = new Dictionary<FormKey, FormKey[]>();
        var musics = new Dictionary<FormKey, (string Edid, string[] Flags, int Tracks)>();
        // Every game setting of the masters (winning copy): the FormKey and kind the GMST overrides are written with.
        var settings = new SortedDictionary<string, object>(StringComparer.Ordinal);
        // Every loading screen of the masters (winning copy): each is shelled with a never-true condition (0012).
        var screens = new Dictionary<FormKey, string>();
        foreach (var plugin in plugins)
        {
            using var mod = Load.Open(data, plugin);
            foreach (var g in mod.GameSettings)
                if (g.EditorID is { Length: > 0 } id)
                    settings[id] = new { formKey = Load.Key(g.FormKey),
                                         kind = g switch { IGameSettingFloatGetter => "float", IGameSettingIntGetter => "int",
                                                           IGameSettingBoolGetter => "bool", _ => "string" } };
            foreach (var l in mod.LoadScreens) screens[l.FormKey] = l.EditorID ?? "";
            foreach (var q in mod.Quests) quests[q.FormKey] = (q.EditorID ?? "", (int)q.Flags);
            foreach (var node in mod.StoryManagerQuestNodes) nodes[node.FormKey] = node.Quests.Select(n => n.Quest.FormKey).ToArray();
            foreach (var m in mod.MusicTypes)
                musics[m.FormKey] = (m.EditorID ?? "", m.Flags.ToString().Split(", ", StringSplitOptions.RemoveEmptyEntries)
                                                         .Where(f => f != "0").ToArray(), m.Tracks?.Count ?? 0);
        }
        var started = new Dictionary<FormKey, SortedSet<string>>();
        foreach (var (k, q) in quests)
            if (((Quest.Flag)q.Flags).HasFlag(Quest.Flag.StartGameEnabled)) Mark(started, k, "start-game-enabled");
        foreach (var list in nodes.Values) foreach (var k in list) Mark(started, k, "story-manager");
        var rows = started.Keys
            .Where(quests.ContainsKey)
            .OrderBy(k => k.ModKey.FileName.String, StringComparer.Ordinal).ThenBy(k => k.ID)
            .Select(k => new { formKey = Load.Key(k), edid = quests[k].Edid, plugin = k.ModKey.FileName.String,
                               flags = quests[k].Flags, why = started[k].ToArray() })
            .ToList();
        var music = musics.OrderBy(kv => kv.Key.ModKey.FileName.String, StringComparer.Ordinal).ThenBy(kv => kv.Key.ID)
            .Select(kv => (object)new { formKey = Load.Key(kv.Key), edid = kv.Value.Edid, plugin = kv.Key.ModKey.FileName.String,
                                        flags = kv.Value.Flags, tracks = kv.Value.Tracks })
            .ToList();
        var lscr = screens.OrderBy(kv => kv.Key.ModKey.FileName.String, StringComparer.Ordinal).ThenBy(kv => kv.Key.ID)
            .Select(kv => (object)new { formKey = Load.Key(kv.Key), edid = kv.Value, plugin = kv.Key.ModKey.FileName.String })
            .ToList();
        Load.WriteJson(outPath, new { plugins, quests = rows, musicTypes = music, gameSettings = settings, loadScreens = lscr });
        Console.WriteLine($"quests: {rows.Count} self-starting vanilla quests, {music.Count} music types -> {outPath}");
        return 0;
    }

    static void Mark(Dictionary<FormKey, SortedSet<string>> d, FormKey k, string why)
    {
        if (!d.TryGetValue(k, out var s)) d[k] = s = new SortedSet<string>(StringComparer.Ordinal);
        s.Add(why);
    }
}
