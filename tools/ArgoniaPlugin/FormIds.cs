// FormIds: the registry of a written plugin's form ids, so that a record keeps its id for life whatever else the
// build writes and in whatever order. The world's is newworld/sources/world_formids.json (committed):
//   {"blocks": {kind: "0xFIRST-0xLAST"}, "ids": {kind: {name: "0xID"}}, "seeded": "0xFIRST-0xLAST"}
// A name is the record's own identity, never a count:
//   copy:<source form key>           a record copied from another plugin (ForeignCopy)
//   alttex:<source form key>:<n>     the texture set of a copy's texture repair, 3D index n
//   ltex:<material id>               the land texture of one material of tex/materials.json
//   watr:<key>                       one water type of cells.json
//   blend:<own type>|<mix>|<look>    one graded water record (WaterBlend.Blend)
//   region:<region id>               one region of cells.json
//   var ids = FormIds.Load(path);  uint id = ids.Take("ground", "ltex:moss");  ...  ids.Save();
// Take: a known name returns its id, whatever kind asks; a new name takes the next free id of its kind's block and is
// added. An entry is never removed and an id never given twice: a name no longer asked for keeps its entry. A full
// block, a kind with no block, two names on one id or an id outside its block stops the build. "seeded" is the range
// the ids made before the registry lie in; nothing new is given there. Save writes the file only when a name was
// added (sorted, one entry a line: the bytes follow from the entries alone) and says how many: commit it.
// `formids selftest` proves the rules on a registry in memory and on a scratch file (no game data).
using System.Globalization;
using System.Text;
using System.Text.Json;

sealed class FormIds
{
    // The world plugin's blocks. Beside them, by formula: 0x800..0x802 the world, its persistent cell and the start
    // marker; 0x80000..0x80FFF the atmosphere (atmosphere.py); 0x100000.. the cells and their LAND; the placed
    // references: 0x200000..0x6FFFFF those placed by rule (each by its identity, place.py form_ids), 0x700000..0x73FFFF
    // those an edit added (given once by its row, edits.py), 0x740000..0x7FFFFF the rest, counted (NewWorld.cs); 0x600000..0x609677
    // inside the references' range the navmesh's (navmesh/stitch.py), never a reference's; 0xFE0000.. the teleport markers,
    // 0xFF0000.. the map markers (NewWorldMap.cs). Every range is a row of one table, tools/newworld/idspace.py.
    public static readonly (string Kind, uint First, uint Last)[] WorldBlocks =
    {
        ("region", 0x000880, 0x0008FF),
        ("ground", 0x010000, 0x01FFFF),   // land textures, their texture sets, grass
        ("base", 0x020000, 0x07FFFF),     // placed bases and what they link to
        ("water", 0x800000, 0xEFFFFF),    // water types and their graded blends
    };
    public static readonly (uint First, uint Last) WorldSeeded = (0x000900, 0x00FFFF);

    readonly string? path;
    readonly SortedDictionary<string, (uint First, uint Last)> blocks = new(StringComparer.Ordinal);
    readonly SortedDictionary<string, SortedDictionary<string, uint>> ids = new(StringComparer.Ordinal);
    readonly Dictionary<string, uint> byName = new(StringComparer.Ordinal);
    readonly Dictionary<uint, string> byId = new();
    readonly Dictionary<string, uint> next = new();
    (uint First, uint Last)? seeded;
    public readonly List<string> Added = new();

    FormIds(string? path) { this.path = path; }

    /// The registry at `path`; a file not there yet starts empty with the world's blocks. `path` null: in memory only.
    public static FormIds Load(string? path)
    {
        var r = new FormIds(path);
        if (path is null || !File.Exists(path))
        {
            foreach (var (k, a, b) in WorldBlocks) r.blocks[k] = (a, b);
            r.seeded = WorldSeeded;
        }
        else
        {
            using var doc = JsonDocument.Parse(File.ReadAllText(path));
            var root = doc.RootElement;
            foreach (var b in root.GetProperty("blocks").EnumerateObject()) r.blocks[b.Name] = Range(b.Value.GetString()!);
            if (root.TryGetProperty("seeded", out var sd)) r.seeded = Range(sd.GetString()!);
            foreach (var k in root.GetProperty("ids").EnumerateObject())
                foreach (var e in k.Value.EnumerateObject())
                    r.Put(k.Name, e.Name, Hex(e.Value.GetString()!));
        }
        var all = r.blocks.OrderBy(b => b.Value.First).ToList();
        for (var i = 1; i < all.Count; i++)
            if (all[i].Value.First <= all[i - 1].Value.Last) throw new InvalidDataException($"form ids: blocks {all[i - 1].Key} and {all[i].Key} overlap");
        foreach (var (kind, (first, _)) in r.blocks)
            r.next[kind] = r.ids.TryGetValue(kind, out var m) ? m.Values.Where(v => r.In(kind, v)).Select(v => v + 1).DefaultIfEmpty(first).Max() : first;
        return r;
    }

    static uint Hex(string s) => s.StartsWith("0x") ? uint.Parse(s[2..], NumberStyles.HexNumber, CultureInfo.InvariantCulture) : throw new InvalidDataException($"form ids: '{s}' is no 0x id");
    static (uint, uint) Range(string s) { var p = s.Split('-'); return p.Length == 2 ? (Hex(p[0]), Hex(p[1])) : throw new InvalidDataException($"form ids: '{s}' is no range"); }
    bool In(string kind, uint id) => blocks.TryGetValue(kind, out var b) && id >= b.First && id <= b.Last;

    void Put(string kind, string name, uint id)
    {
        if (!blocks.ContainsKey(kind)) throw new InvalidDataException($"form ids: kind '{kind}' has no block ({path})");
        if (!In(kind, id) && !(seeded is { } s && id >= s.First && id <= s.Last))
            throw new InvalidDataException($"form ids: {name} holds {id:X6}, outside the block of '{kind}'");
        if (byName.ContainsKey(name)) throw new InvalidDataException($"form ids: {name} is registered twice");
        if (byId.TryGetValue(id, out var other)) throw new InvalidDataException($"form ids: {id:X6} is held by both {other} and {name}");
        if (name.Any(c => c < ' ')) throw new InvalidDataException($"form ids: a name with a control character ({kind})");
        byName[name] = id; byId[id] = name;
        if (!ids.TryGetValue(kind, out var m)) ids[kind] = m = new(StringComparer.Ordinal);
        m[name] = id;
    }

    public uint Take(string kind, string name)
    {
        if (byName.TryGetValue(name, out var id)) return id;
        if (!blocks.TryGetValue(kind, out var b)) throw new InvalidDataException($"form ids: kind '{kind}' has no block; {name} cannot be given an id");
        id = next[kind];
        if (id > b.Last)
            throw new InvalidDataException($"form ids: the block of '{kind}' ({b.First:X6}..{b.Last:X6}) is full; {name} cannot be given an id. Give the kind a second block; never reuse an id");
        next[kind] = id + 1;
        Put(kind, name, id);
        Added.Add(name);
        return id;
    }

    public bool Knows(string name) => byName.ContainsKey(name);
    public int Count => byName.Count;

    public string Text()
    {
        static string Q(string s) => "\"" + s.Replace("\\", "\\\\").Replace("\"", "\\\"") + "\"";
        var sb = new StringBuilder("{\n \"blocks\": {\n");
        sb.Append(string.Join(",\n", blocks.Select(b => $"  {Q(b.Key)}: \"0x{b.Value.First:X6}-0x{b.Value.Last:X6}\""))).Append("\n },\n \"ids\": {\n");
        sb.Append(string.Join(",\n", ids.Select(k => $"  {Q(k.Key)}: {{\n" + string.Join(",\n", k.Value.Select(e => $"   {Q(e.Key)}: \"0x{e.Value:X6}\"")) + "\n  }")));
        sb.Append("\n }");
        if (seeded is { } s) sb.Append($",\n \"seeded\": \"0x{s.First:X6}-0x{s.Last:X6}\"");
        return sb.Append("\n}\n").ToString();
    }

    /// Writes the file when a name was added since Load (whole, then moved into place); returns how many were.
    public int Save()
    {
        if (path is null || (Added.Count == 0 && File.Exists(path))) return 0;
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(path))!);
        File.WriteAllText(path + ".tmp", Text(), new UTF8Encoding(false));
        File.Move(path + ".tmp", path, true);
        Console.WriteLine($"form ids: {Added.Count} added to {path} ({Count} held): commit it");
        return Added.Count;
    }

    public static int Run(string[] a)
    {
        if (a.Length < 1 || a[0] != "selftest") throw new ArgumentException("formids selftest [scratch dir]");
        var fails = new List<string>();
        void Ok(bool c, string what) { if (!c) fails.Add(what); }
        bool Throws(Action f) { try { f(); return false; } catch (InvalidDataException) { return true; } }
        // one placement, then another: other bases, another order, a land texture and a blend more
        string[] ground = { "ltex:moss", "ltex:mud", "copy:000A01:Tex.esp", "copy:000A02:Tex.esp" }, water = { "watr:sea", "blend:sea|river:4|1,2,3" };
        string[] basesA = { "copy:000001:Trees.esp", "copy:000002:Trees.esp", "copy:000003:Trees.esp" }, basesB = { "copy:000004:Trees.esp", "copy:000003:Trees.esp", "copy:000001:Trees.esp" };
        var one = Load(null);
        var a1 = ground.Concat(water).ToDictionary(n => n, n => one.Take(n.StartsWith("watr") || n.StartsWith("blend") ? "water" : "ground", n));
        var b1 = basesA.ToDictionary(n => n, n => one.Take("base", n));
        var again = Load(null);
        foreach (var n in basesB) again.Take("base", n);                       // the bases first this time, others, in another order
        foreach (var n in water) again.Take("water", n);
        foreach (var n in ground) again.Take("ground", n);
        Ok(a1.All(e => again.Take("ground", e.Key) == e.Value), "a kind's ids follow the other kinds' order or count");
        Ok(one.Take("base", "copy:000001:Trees.esp") == b1["copy:000001:Trees.esp"] && one.Added.Count == 9, "a known name was given a new id");
        // a re-place on the kept registry: every known name keeps its id, the new base takes the next of its block
        var n0 = one.Added.Count;
        foreach (var n in basesB) one.Take("base", n);
        Ok(basesA.All(n => one.Take("base", n) == b1[n]) && one.Added.Count == n0 + 1 && one.Take("base", "copy:000004:Trees.esp") == 0x020003, "a re-place moved a base's id");
        Ok(a1.All(e => one.Take("ground", e.Key) == e.Value), "a re-place moved a ground or water id");
        // one land texture more, one blend more: one id more each, nothing else moves
        Ok(one.Take("ground", "ltex:reeds") == 0x010004 && one.Take("water", "blend:sea|river:5|1,2,3") == 0x800002, "a new name did not take its block's next id");
        Ok(a1.All(e => one.Take("ground", e.Key) == e.Value) && basesA.All(n => one.Take("base", n) == b1[n]), "a new land texture or blend moved another id");
        // a name keeps its id whatever kind asks later; a kind with no block and a full block stop the build
        Ok(one.Take("base", "copy:000A01:Tex.esp") == a1["copy:000A01:Tex.esp"], "a name known under another kind was given a second id");
        Ok(Throws(() => one.Take("sky", "x")), "a kind with no block was given an id");
        var full = Load(null);
        for (var i = 0; i < 0x80; i++) full.Take("region", "region:" + i);
        Ok(Throws(() => full.Take("region", "region:over")), "a full block gave an id");
        Ok(full.Take("region", "region:5") == 0x885, "a full block lost a known name");
        // the file: the same bytes from the same entries in any order; read back whole; nothing rewritten when nothing is added
        var dir = a.Length > 1 ? a[1] : Path.Combine(Path.GetTempPath(), "formids-selftest-" + Environment.ProcessId);
        Directory.CreateDirectory(dir);
        string p1 = Path.Combine(dir, "one.json"), p2 = Path.Combine(dir, "two.json");
        var f1 = Load(p1); var f2 = Load(p2);
        foreach (var n in ground) f1.Take("ground", n);
        foreach (var n in basesA) f1.Take("base", n);
        f1.Save();
        var seed = Load(p1);                                                    // two.json: the same entries, asked for in another order
        foreach (var n in basesA.Reverse()) f2.Put("base", n, seed.Take("base", n));
        foreach (var n in ground.Reverse()) f2.Put("ground", n, seed.Take("ground", n));
        f2.Added.Add("x"); f2.Save();
        Ok(File.ReadAllText(p1) == File.ReadAllText(p2), "the file's bytes follow the order names were asked in");
        var stamp = File.GetLastWriteTimeUtc(p1);
        var back = Load(p1);
        Ok(ground.Concat(basesA).All(n => back.Take("base", n) == f1.Take("base", n)) && back.Save() == 0 && File.GetLastWriteTimeUtc(p1) == stamp, "a run that added nothing rewrote the file");
        Ok(back.Take("base", "copy:000009:Trees.esp") == 0x020003 && back.Save() == 1 && Load(p1).Count == 8, "an added name was not saved");
        File.WriteAllText(p2, File.ReadAllText(p1).Replace("\"0x020001\"", "\"0x020000\""));
        Ok(Throws(() => Load(p2)), "two names on one id were read");
        File.WriteAllText(p2, File.ReadAllText(p1).Replace("\"0x020001\"", "\"0x090000\""));
        Ok(Throws(() => Load(p2)), "an id outside its block was read");
        if (a.Length < 2) Directory.Delete(dir, true);
        foreach (var f in fails) Console.WriteLine("FAIL " + f);
        Console.WriteLine(fails.Count == 0 ? "formids selftest: PASS" : $"formids selftest: {fails.Count} FAIL");
        return fails.Count == 0 ? 0 : 1;
    }
}
