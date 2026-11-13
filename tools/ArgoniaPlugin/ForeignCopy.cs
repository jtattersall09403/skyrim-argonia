// ForeignCopy: copy a record from an asset-only plugin (King of the Murkmire, Tropical Skyrim, Depths of Skyrim,
// Black Marsh North, Valenwood...: their assets are installed, their plugins are not active) as a NEW record of ours,
// so the written plugin never masters them nor links into them. Owner ruling 2026-11-08.
// Use (any writer, e.g. the new world's textures, water, and the placement step's TREE/STAT/FLOR bases):
//   var fc = new ForeignCopy(ourMod, allowedMasters, dataDir, ids);      // ids: the plugin's registry (FormIds.cs):
//                                    // a copy's id is its source's for life ("copy:<source form key>"), in fc.Kind's block
//   var fc = new ForeignCopy(ourMod, allowedMasters, dataDir, nextId);   // a plugin with no registry: ids count up from nextId
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
    readonly FormIds? ids;
    readonly Dictionary<FormKey, FormKey> sourceOf = new();  // ours -> the record it copies
    uint next;
    public uint NextId => next;
    public uint NextIdTake() => ids is null ? next++ : throw new InvalidOperationException("this plugin's ids are registered: Take(kind, name)");
    /// The kind whose block a copy first asked for now takes its id from (a registered plugin).
    public string Kind = "";
    /// An id for a record the caller builds itself, by its registered name; counted up where the plugin has no registry.
    public uint Take(string kind, string name) => ids is null ? next++ : ids.Take(kind, name);

    public ForeignCopy(SkyrimMod mod, IEnumerable<ModKey> allowed, string data, uint firstId)
    {
        this.mod = mod; this.allowed = allowed.ToHashSet(); this.data = data; next = firstId;
        this.allowed.Add(mod.ModKey);
    }

    public ForeignCopy(SkyrimMod mod, IEnumerable<ModKey> allowed, string data, FormIds ids) : this(mod, allowed, data, 0) { this.ids = ids; }

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
        var ours = new FormKey(mod.ModKey, Take(Kind, $"copy:{src.FormKey}"));
        Map[src.FormKey] = ours;
        return Copy(src, file, ours);
    }

    /// A copy of `src` at an id the caller holds, made as Get makes one but not the source's one copy: a second copy
    /// of one source (a land texture per material) is its own record, and nothing that links to the source is led to it.
    public FormKey CopyAs(IMajorRecordGetter src, string file, uint id) => Copy(src, file, new FormKey(mod.ModKey, id));

    FormKey Copy(IMajorRecordGetter src, string file, FormKey ours)
    {
        sourceOf[ours] = src.FormKey;
        var dup = (IMajorRecord)src.Duplicate(ours);
        DropUnshowable(dup, file);
        dup.EditorID = $"ANW_{Initials(file)}_{src.EditorID ?? src.FormKey.IDString()}";
        var placed = new Dictionary<FormKey, FormKey>();
        foreach (var l in src.EnumerateFormLinks().Select(l => l.FormKey).Distinct().ToList())
            if (!l.IsNull && !allowed.Contains(l.ModKey) && !Map.ContainsKey(l))
            {
                if (WorldBound(Find(l, file))) { placed[l] = FormKey.Null; continue; }
                Get(l, file);
            }
        dup.RemapLinks(Map);
        if (placed.Count > 0)
        {
            dup.RemapLinks(placed);
            Console.WriteLine($"foreign copy: {dup.EditorID}: {placed.Count} link(s) into the source's world (placed refs, cells, quests, dialogue) nulled");
        }
        DropDangling(dup);
        // nothing in our file is levelled against the player (decision 0035): a copied actor keeps a fixed level, the
        // lowest its multiplier allowed (a band copy sets its own; a template copy is never placed)
        if (dup is Npc npc)
        {
            if (npc.Configuration.Level is PcLevelMult)
                npc.Configuration.Level = new NpcLevel { Level = (short)Math.Max(1, (int)npc.Configuration.CalcMinLevel) };
            npc.Configuration.TemplateFlags &= ~NpcConfiguration.TemplateFlag.Stats;   // its own fixed level, not a template's
        }
        mod.GetTopLevelGroup(dup.GetType()).AddUntyped(dup);
        Copies[ours] = dup;
        return ours;
    }

    // Items whose model names a texture their own mod does not ship (the mod's own world draws them untextured too):
    // a copy never carries them, so the closure never reaches them (plugin file, editor id, why).
    public static readonly (string File, string EditorId, string Why)[] Unshowable =
    {
        ("Here There Be Monsters - Curse of Cipactli.esp", "CIPHTBMBambooStaff2",
         "bamboostaffgreen.nif names textures\\weapons\\bamboostaff\\bamboostaffyellow.dds; the mod ships that texture only under its own folder"),
    };

    // A levelled list, a container or an actor in `dup` stops listing an unshowable item.
    void DropUnshowable(IMajorRecord dup, string file)
    {
        var bad = Unshowable.Where(u => string.Equals(u.File, file, StringComparison.OrdinalIgnoreCase))
            .Select(u => Find(u.File, u.EditorId).FormKey).ToHashSet();
        if (bad.Count == 0) return;
        int n = 0;
        switch (dup)
        {
            case LeveledItem li when li.Entries is { } es: n = es.RemoveAll(e => e.Data?.Reference.FormKey is { } k && bad.Contains(k)); break;
            case Npc np when np.Items is { } its: n = its.RemoveAll(e => e.Item is { } ci && bad.Contains(ci.Item.FormKey)); break;
            case Container c when c.Items is { } cis: n = cis.RemoveAll(e => e.Item is { } ci && bad.Contains(ci.Item.FormKey)); break;
        }
        if (n > 0) Console.WriteLine($"foreign copy: {dup.EditorID}: {n} unshowable item(s) not carried");
    }

    public readonly Dictionary<FormKey, IMajorRecord> Copies = new();

    // A record that belongs to its plugin's world or story (a placed reference, a cell, a worldspace, a quest, its
    // dialogue, a navmesh, a story-manager node): a copy never carries one over; its link to it is nulled.
    static bool WorldBound(IMajorRecordGetter? r) => r is IPlacedGetter or ICellGetter or IWorldspaceGetter or IQuestGetter
        or IDialogTopicGetter or IDialogResponsesGetter or INavigationMeshGetter or ILandscapeGetter or IAStoryManagerNodeGetter;

    IMajorRecordGetter? Find(FormKey fk, string file) =>
        Plugin(file).EnumerateMajorRecords().FirstOrDefault(x => x.FormKey == fk)
        ?? (Exists(fk) ? Plugin(fk.ModKey.FileName).EnumerateMajorRecords().FirstOrDefault(x => x.FormKey == fk) : null);

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
            var ts = new TextureSet(new FormKey(mod.ModKey, Take(Kind, $"alttex:{sourceOf[ours]}:{index}")), SkyrimRelease.SkyrimSE)
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
