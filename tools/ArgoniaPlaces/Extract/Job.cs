using System.Text.Json;

// The job extract.py hands over: everything the extractor needs, nothing it must look up in our tables.
sealed class Job
{
    public string BundleId = "", Kind = "source", Title = "", Out = "", Worldspace = "", Layer = "place", Location = "", Marker = "";
    public float MarkerRadius;
    public List<string> Plugins = new(), Search = new();
    public List<(int x, int y)> Cells = new();
    public List<(float x, float y, float r)> Areas = new();
    public bool FollowDoors = true, Terrain = true, Navmesh = true;

    public static Job Load(string path)
    {
        var j = JsonDocument.Parse(File.ReadAllText(path)).RootElement;
        string S(string k, string d = "") => j.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString()! : d;
        bool B(string k, bool d) => j.TryGetProperty(k, out var v) && v.ValueKind is JsonValueKind.True or JsonValueKind.False ? v.GetBoolean() : d;
        List<JsonElement> A(string k) => j.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.Array ? v.EnumerateArray().ToList() : new();
        return new Job
        {
            BundleId = S("bundle_id"), Kind = S("kind", "source"), Title = S("title"), Out = S("out"),
            Worldspace = S("worldspace"), Layer = S("layer", "place"), Location = S("location"), Marker = S("marker"),
            MarkerRadius = j.TryGetProperty("radius", out var mr) && mr.ValueKind == JsonValueKind.Number ? mr.GetSingle() : 0,
            Plugins = A("plugins").Select(e => e.GetString()!).ToList(),
            Search = A("search").Select(e => e.GetString()!).ToList(),
            Cells = A("cells").Select(e => (e[0].GetInt32(), e[1].GetInt32())).ToList(),
            Areas = A("areas").Select(e => (e.GetProperty("x").GetSingle(), e.GetProperty("y").GetSingle(), e.GetProperty("r").GetSingle())).ToList(),
            FollowDoors = B("follow_doors", true), Terrain = B("terrain", true), Navmesh = B("navmesh", true),
        };
    }

    // The exterior cells of the extent: the listed cells plus every cell whose square meets an area's circle.
    public HashSet<(int, int)> ExtentCells()
    {
        var s = new HashSet<(int, int)>(Cells);
        foreach (var (x, y, r) in Areas)
            for (var cx = (int)Math.Floor((x - r) / 4096); cx <= (int)Math.Floor((x + r) / 4096); cx++)
                for (var cy = (int)Math.Floor((y - r) / 4096); cy <= (int)Math.Floor((y + r) / 4096); cy++)
                {
                    float nx = Math.Clamp(x, cx * 4096f, cx * 4096f + 4096), ny = Math.Clamp(y, cy * 4096f, cy * 4096f + 4096);
                    if ((nx - x) * (nx - x) + (ny - y) * (ny - y) <= r * r) s.Add((cx, cy));
                }
        return s;
    }
}
