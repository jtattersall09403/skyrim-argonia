// ForeignCopy: copy a record from an asset-only plugin (King of the Murkmire, Tropical Skyrim, Depths of Skyrim,
// Black Marsh North, Valenwood...: their assets are installed, their plugins are not active) as a NEW record of ours,
// so the written plugin never masters them nor links into them. Owner ruling 2026-11-08.
// Use (any writer, e.g. the new world's textures, water, and the placement step's TREE/STAT/FLOR bases):
//   var fc = new ForeignCopy(ourMod, allowedMasters, dataDir, nextId);   // nextId: the first free object id
//   FormKey ours = fc.Get("King of the Murkmire.esp", "LALPAMarshGrass");  // by plugin + editor id
//   FormKey ours = fc.Get(someForeignFormKey, "Tropical Skyrim.esp");     // by form key, read from that plugin
// A record found in an allowed master (Skyrim.esm, Update.esm, Black Marsh.esm and its masters) is linked, not
// copied, unless Get(..., forceCopy: true); one named from a non-allowed plugin is always copied as that plugin has it. A copy keeps every field (model and texture paths point at the mod's
// installed assets), gets EditorID "ANW_<plugin initials>_" + the source's (BM&V North and Valenwood share editor ids;
// the plugin it was read from keeps them apart, the same every build), and each of its own links into a non-allowed plugin is
// copied the same way first (recursively, once each: `Map` holds source -> ours), so the copy is self-contained.
// A copy's link into an allowed master that names no record there (King of the Murkmire's alternate textures pointing
// at 000028:Skyrim.esm) is dropped: the alternate-texture entry is removed, any other such link is nulled; each logged.
// AltTextures(ours, [(shape, 3D index, 8 nif slot paths)]) puts a texture repair on a copy's model: a new TXST of
// ours with the corrected paths, listed in the model's MODS (Skyrim's alternate textures; the mesh is untouched).
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
        dup.EditorID = $"ANW_{Initials(file)}_{src.EditorID ?? src.FormKey.IDString()}";
        foreach (var l in src.EnumerateFormLinks().Select(l => l.FormKey).Distinct().ToList())
            if (!l.IsNull && !allowed.Contains(l.ModKey) && !Map.ContainsKey(l)) Get(l, file);
        dup.RemapLinks(Map);
        DropDangling(dup);
        mod.GetTopLevelGroup(dup.GetType()).AddUntyped(dup);
        Copies[ours] = dup;
        return ours;
    }

    public readonly Dictionary<FormKey, IMajorRecord> Copies = new();

    // "Black Marsh North.esp" -> BMN, "King of the Murkmire.esp" -> KotM, "DepthsOfSkyrim.esp" -> DOS
    public static string Initials(string file) =>
        string.Concat(System.Text.RegularExpressions.Regex.Matches(Path.GetFileNameWithoutExtension(file), "[A-Z][a-z]*|[a-z]+|[0-9]+").Select(m => m.Value[0]));

    readonly Dictionary<ModKey, HashSet<FormKey>> masterKeys = new();
    bool Exists(FormKey fk)
    {
        if (fk.ModKey == mod.ModKey) return true;
        if (!masterKeys.TryGetValue(fk.ModKey, out var ks))
            masterKeys[fk.ModKey] = ks = Plugin(fk.ModKey.FileName).EnumerateMajorRecords().Select(r => r.FormKey).ToHashSet();
        return ks.Contains(fk);
    }

    void DropDangling(IMajorRecord dup)
    {
        var bad = dup.EnumerateFormLinks().Select(l => l.FormKey).Where(k => !k.IsNull && allowed.Contains(k.ModKey) && !Exists(k)).ToHashSet();
        if (bad.Count == 0) return;
        if (dup is IModeled { Model.AlternateTextures: { } alts })
        {
            var n = alts.RemoveAll(a => bad.Contains(a.NewTexture.FormKey));
            if (n > 0) Console.WriteLine($"foreign copy: {dup.EditorID}: {n} alternate texture(s) into a missing record dropped ({string.Join(", ", bad)})");
        }
        var left = dup.EnumerateFormLinks().Select(l => l.FormKey).Where(bad.Contains).ToHashSet();
        if (left.Count == 0) return;
        dup.RemapLinks(left.ToDictionary(k => k, _ => FormKey.Null));
        Console.WriteLine($"foreign copy: {dup.EditorID}: links into missing records nulled ({string.Join(", ", left)})");
    }

    public void AltTextures(FormKey ours, IEnumerable<(string Shape, int Index, string[] Slots)> alts)
    {
        if (!Copies.TryGetValue(ours, out var rec) || rec is not IModeled { Model: { } model })
            throw new InvalidDataException($"{ours}: not a copied record with a model; alternate textures need our copy");
        model.AlternateTextures ??= new();
        foreach (var (shape, index, s) in alts)
        {
            var ts = new TextureSet(new FormKey(mod.ModKey, next++), SkyrimRelease.SkyrimSE)
            {
                EditorID = $"{rec.EditorID}_Tex{index}",
                ObjectBounds = new ObjectBounds(),
            };
            string? P(int i) => i < s.Length && s[i] != "" ? s[i] : null;
            // nif slots -> TXST: 0 diffuse, 1 normal, 2 glow, 3 height, 4 environment, 5 environment mask, 6 multilayer, 7 backlight
            if (P(0) is { } d) ts.Diffuse = d;
            if (P(1) is { } nrm) ts.NormalOrGloss = nrm;
            if (P(2) is { } g) ts.GlowOrDetailMap = g;
            if (P(3) is { } h) ts.Height = h;
            if (P(4) is { } e) ts.Environment = e;
            if (P(5) is { } em) ts.EnvironmentMaskOrSubsurfaceTint = em;
            if (P(6) is { } ml) ts.Multilayer = ml;
            if (P(7) is { } bl) ts.BacklightMaskOrSpecular = bl;
            mod.TextureSets.Add(ts);
            model.AlternateTextures.RemoveAll(a => a.Name == shape);
            model.AlternateTextures.Add(new AlternateTexture { Name = shape, Index = index, NewTexture = ts.ToLink<ITextureSetGetter>() });
            Console.WriteLine($"alt texture: {rec.EditorID} shape '{shape}' #{index} -> {ts.EditorID} ({P(0)})");
        }
    }

    public void Dispose() { foreach (var p in plugins.Values) p.Dispose(); }
}
