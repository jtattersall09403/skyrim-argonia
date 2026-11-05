using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
// find <plugin> <editor-id regex>: records whose editor id matches, with type.
static class Find
{
    public static void Run(string path, string rx)
    {
        using var mod = SkyrimMod.CreateFromBinaryOverlay(path, SkyrimRelease.SkyrimSE, Survey.NoStrings);
        var re = new System.Text.RegularExpressions.Regex(rx);
        foreach (var r in mod.EnumerateMajorRecords())
            if (r.EditorID != null && re.IsMatch(r.EditorID))
                Console.WriteLine($"{r.FormKey} {r.GetType().Name.Replace("BinaryOverlay", "")} {r.EditorID}");
    }
}
