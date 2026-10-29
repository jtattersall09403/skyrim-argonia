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
        var records = new List<Dictionary<string, string>>();
        var meshes = new SortedSet<string>(StringComparer.Ordinal);
        foreach (var plugin in plugins)
        {
            using var mod = Load.Open(data, plugin);
            foreach (var r in mod.EnumerateMajorRecords())
            {
                if (r.FormKey.ModKey != mod.ModKey) continue; // overrides of a master's record are the master's
                if (r is not IModeledGetter m || string.IsNullOrEmpty(m.Model?.File.DataRelativePath.Path)) continue;
                records.Add(new()
                {
                    ["mesh"] = Norm(m.Model!.File.DataRelativePath.Path),
                    ["plugin"] = plugin,
                    ["formKey"] = Load.Key(r.FormKey),
                    ["type"] = r.Registration.ClassType.Name,
                    ["edid"] = r.EditorID ?? "",
                });
            }
            foreach (var bsa in Directory.EnumerateFiles(data, Path.GetFileNameWithoutExtension(plugin) + "*.bsa"))
                AddArchive(bsa, meshes);
        }
        foreach (var bsa in Directory.EnumerateFiles(data, "Skyrim - Meshes*.bsa")) AddArchive(bsa, meshes);
        foreach (var f in Directory.EnumerateFiles(Path.Combine(data), "*.nif", SearchOption.AllDirectories))
            meshes.Add(Norm(Path.GetRelativePath(data, f)));
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
        var started = new Dictionary<FormKey, SortedSet<string>>();
        var info = new Dictionary<FormKey, (string Edid, string Plugin, int Flags)>();
        foreach (var plugin in plugins)
        {
            using var mod = Load.Open(data, plugin);
            foreach (var q in mod.Quests)
            {
                info[q.FormKey] = (q.EditorID ?? "", q.FormKey.ModKey.FileName, (int)q.Flags);
                if (q.Flags.HasFlag(Quest.Flag.StartGameEnabled)) Mark(started, q.FormKey, "start-game-enabled");
            }
            foreach (var node in mod.StoryManagerQuestNodes)
                foreach (var nq in node.Quests)
                    Mark(started, nq.Quest.FormKey, "story-manager");
        }
        var rows = started.Keys
            .Where(info.ContainsKey)
            .OrderBy(k => k.ModKey.FileName.String, StringComparer.Ordinal).ThenBy(k => k.ID)
            .Select(k => new { formKey = Load.Key(k), edid = info[k].Edid, plugin = info[k].Plugin,
                               flags = info[k].Flags, why = started[k].ToArray() })
            .ToList();
        var music = new List<object>();
        foreach (var plugin in plugins)
        {
            using var mod = Load.Open(data, plugin);
            foreach (var m in mod.MusicTypes.Where(m => m.FormKey.ModKey == mod.ModKey).OrderBy(m => m.FormKey.ID))
                music.Add(new { formKey = Load.Key(m.FormKey), edid = m.EditorID ?? "", plugin,
                                flags = m.Flags.ToString().Split(", ", StringSplitOptions.RemoveEmptyEntries)
                                         .Where(f => f != "0").ToArray(),
                                tracks = m.Tracks?.Count ?? 0 });
        }
        Load.WriteJson(outPath, new { plugins, quests = rows, musicTypes = music });
        Console.WriteLine($"quests: {rows.Count} self-starting vanilla quests, {music.Count} music types -> {outPath}");
        return 0;
    }

    static void Mark(Dictionary<FormKey, SortedSet<string>> d, FormKey k, string why)
    {
        if (!d.TryGetValue(k, out var s)) d[k] = s = new SortedSet<string>(StringComparer.Ordinal);
        s.Add(why);
    }
}
