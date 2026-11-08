// ForeignCopy: copy a record from an asset-only plugin (King of the Murkmire, Tropical Skyrim, Depths of Skyrim,
// Black Marsh North, Valenwood...: their assets are installed, their plugins are not active) as a NEW record of ours,
// so the written plugin never masters them nor links into them. Owner ruling 2026-11-08.
// Use (any writer, e.g. the new world's textures, water, and the placement step's TREE/STAT/FLOR bases):
//   var fc = new ForeignCopy(ourMod, allowedMasters, dataDir, nextId);   // nextId: the first free object id
//   FormKey ours = fc.Get("King of the Murkmire.esp", "LALPAMarshGrass");  // by plugin + editor id
//   FormKey ours = fc.Get(someForeignFormKey, "Tropical Skyrim.esp");     // by form key, read from that plugin
// A record found in an allowed master (Skyrim.esm, Update.esm, Black Marsh.esm and its masters) is linked, not
// copied, unless Get(..., forceCopy: true); one named from a non-allowed plugin is always copied as that plugin has it. A copy keeps every field (model and texture paths point at the mod's
// installed assets), gets EditorID "ANW_" + the source's, and each of its own links into a non-allowed plugin is
// copied the same way first (recursively, once each: `Map` holds source -> ours), so the copy is self-contained.
// Plugins are read from the Data folder, else from ~/.argonia/stack/MO2/mods/*/ (asset-only mods are staged there).
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;

sealed class ForeignCopy : IDisposable
{
    readonly SkyrimMod mod;
    readonly HashSet<ModKey> allowed;
    readonly string data;
    readonly Dictionary<string, ISkyrimModDisposableGetter> plugins = new(StringComparer.OrdinalIgnoreCase);
    public readonly Dictionary<FormKey, FormKey> Map = new();
    uint next;
    public uint NextId => next;
    public uint NextIdTake() => next++;  // an id for a record the caller builds itself (shares the copy range)

    public ForeignCopy(SkyrimMod mod, IEnumerable<ModKey> allowed, string data, uint firstId)
    {
        this.mod = mod; this.allowed = allowed.ToHashSet(); this.data = data; next = firstId;
        this.allowed.Add(mod.ModKey);
    }

    public bool IsAllowed(ModKey m) => allowed.Contains(m);

    public ISkyrimModGetter Plugin(string file)
    {
        if (plugins.TryGetValue(file, out var p)) return p;
        var path = Path.Combine(data, file);
        if (!File.Exists(path))
        {
            var mods = Path.Combine(Environment.GetEnvironmentVariable("HOME")!, ".argonia/stack/MO2/mods");
            path = Directory.Exists(mods) ? Directory.EnumerateDirectories(mods).Select(d => Path.Combine(d, file)).FirstOrDefault(File.Exists) ?? "" : "";
            if (path == "") throw new FileNotFoundException($"{file} not in {data} nor the staged mods");
        }
        return plugins[file] = SkyrimMod.CreateFromBinaryOverlay(path, SkyrimRelease.SkyrimSE, Survey.NoStrings);
    }

    readonly Dictionary<string, Dictionary<string, IMajorRecordGetter>> edids = new(StringComparer.OrdinalIgnoreCase);

    public IMajorRecordGetter Find(string file, string edid)
    {
        if (!edids.TryGetValue(file, out var ix))
        {
            ix = new(StringComparer.OrdinalIgnoreCase);
            foreach (var r in Plugin(file).EnumerateMajorRecords()) if (r.EditorID is { } e) ix.TryAdd(e, r);
            edids[file] = ix;
        }
        return ix.TryGetValue(edid, out var rec) ? rec : throw new InvalidDataException($"{edid} not in {file}");
    }

    // A record named from a non-allowed plugin is always copied (that plugin's version, even of a vanilla form).
    public FormKey Get(string file, string edid, bool forceCopy = false) =>
        Get(Find(file, edid), file, forceCopy || !allowed.Contains(ModKey.FromFileName(file)));

    public FormKey Get(FormKey fk, string file, bool forceCopy = false)
    {
        if (Map.TryGetValue(fk, out var m)) return m;
        if (!forceCopy && allowed.Contains(fk.ModKey)) return fk;
        var r = Plugin(file).EnumerateMajorRecords().FirstOrDefault(x => x.FormKey == fk)
                ?? Plugin(fk.ModKey.FileName).EnumerateMajorRecords().First(x => x.FormKey == fk);
        return Get(r, file, forceCopy);
    }

    public FormKey Get(IMajorRecordGetter src, string file, bool forceCopy = false)
    {
        if (Map.TryGetValue(src.FormKey, out var m)) return m;
        if (!forceCopy && allowed.Contains(src.FormKey.ModKey)) return src.FormKey;
        var ours = new FormKey(mod.ModKey, next++);
        Map[src.FormKey] = ours;
        var dup = (IMajorRecord)src.Duplicate(ours);
        dup.EditorID = "ANW_" + (src.EditorID ?? src.FormKey.IDString());
        foreach (var l in src.EnumerateFormLinks().Select(l => l.FormKey).Distinct().ToList())
            if (!l.IsNull && !allowed.Contains(l.ModKey) && !Map.ContainsKey(l)) Get(l, file);
        dup.RemapLinks(Map);
        mod.GetTopLevelGroup(dup.GetType()).AddUntyped(dup);
        return ours;
    }

    public void Dispose() { foreach (var p in plugins.Values) p.Dispose(); }
}
