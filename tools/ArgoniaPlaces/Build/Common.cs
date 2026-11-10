// Shared helpers: the load order, base types, JSON rows of refs (one shape for source, world and read-back).
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Cache;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Noggog;

static class C
{
    public const SkyrimRelease Rel = SkyrimRelease.SkyrimSE;
    public static readonly JsonSerializerOptions Js = new() { WriteIndented = false };

    /// Data dir: $ARGONIA_GAME_ROOT/Data or ~/games/skyrimse/Data; a plugin not there is found in the staged mods.
    public static string Data => Environment.GetEnvironmentVariable("ARGONIA_DATA")
        ?? Path.Combine(Environment.GetEnvironmentVariable("ARGONIA_GAME_ROOT") ?? Path.Combine(Environment.GetEnvironmentVariable("HOME")!, "games/skyrimse"), "Data");

    public static string PluginPath(string file)
    {
        if (File.Exists(file)) return file;
        var p = Path.Combine(Data, file);
        if (File.Exists(p)) return p;
        var mods = Path.Combine(Environment.GetEnvironmentVariable("HOME")!, ".argonia/stack/MO2/mods");
        return (Directory.Exists(mods) ? Directory.EnumerateDirectories(mods).Select(d => Path.Combine(d, file)).FirstOrDefault(File.Exists) : null)
            ?? throw new FileNotFoundException($"{file} not in {Data} nor the staged mods");
    }

    static readonly Dictionary<string, ISkyrimModDisposableGetter> open = new(StringComparer.OrdinalIgnoreCase);
    public static ISkyrimModGetter Open(string fileOrPath)
    {
        var path = PluginPath(fileOrPath);
        if (!open.TryGetValue(path, out var m)) open[path] = m = SkyrimMod.CreateFromBinaryOverlay(path, Rel, Survey.NoStrings);
        return m;
    }

    public static ILinkCache Cache(IEnumerable<string> files) => files.Select(Open).ToImmutableLinkCache();

    public static string Key(FormKey k) => k.IsNull ? "" : $"{k.ModKey.FileName}:{k.ID:X6}";
    public static FormKey Fk(string key)
    {
        var i = key.LastIndexOf(':');
        return new FormKey(ModKey.FromFileName(key[..i]), Convert.ToUInt32(key[(i + 1)..], 16));
    }

    /// A VMAD from plan rows [{"name": "Script", "props": [{"name": "P", "type": "object|int|float|bool|string", "value": ...}]}]:
    /// vanilla's shape (version 5, object format 2, local script, edited properties, no alias). Object values are form keys.
    public static VirtualMachineAdapter Vmad(JsonElement scripts)
    {
        var vm = new VirtualMachineAdapter { Version = 5, ObjectFormat = 2 };
        foreach (var sc in scripts.EnumerateArray())
        {
            var e = new ScriptEntry { Name = sc.GetProperty("name").GetString()!, Flags = ScriptEntry.Flag.Local };
            if (sc.TryGetProperty("props", out var props))
                foreach (var p in props.EnumerateArray())
                {
                    var name = p.GetProperty("name").GetString()!;
                    var v = p.GetProperty("value");
                    ScriptProperty sp = p.GetProperty("type").GetString() switch
                    {
                        "object" => new ScriptObjectProperty { Object = new FormLink<ISkyrimMajorRecordGetter>(Fk(v.GetString()!)), Alias = -1 },
                        "int" => new ScriptIntProperty { Data = v.GetInt32() },
                        "float" => new ScriptFloatProperty { Data = (float)v.GetDouble() },
                        "bool" => new ScriptBoolProperty { Data = v.GetBoolean() },
                        "string" => new ScriptStringProperty { Data = v.GetString()! },
                        var t => throw new InvalidDataException($"script {e.Name}.{name}: property type {t} (object, int, float, bool, string)"),
                    };
                    sp.Name = name; sp.Flags = ScriptProperty.Flag.Edited;
                    e.Properties.Add(sp);
                }
            vm.Scripts.Add(e);
        }
        return vm;
    }

    public static string Sig(IMajorRecordGetter? r) => r switch
    {
        null => "",
        IStaticGetter => "STAT", IDoorGetter => "DOOR", IFurnitureGetter => "FURN", IContainerGetter => "CONT",
        ILightGetter => "LIGH", IActivatorGetter => "ACTI", IFloraGetter => "FLOR", ITreeGetter => "TREE",
        IMoveableStaticGetter => "MSTT", INpcGetter => "NPC_", ILeveledNpcGetter => "LVLN", IMiscItemGetter => "MISC",
        IGrassGetter => "GRAS", IIdleMarkerGetter => "IDLM", ISoundMarkerGetter => "SOUN",
        ITextureSetGetter => "TXST", IBookGetter => "BOOK", IIngestibleGetter => "ALCH", IIngredientGetter => "INGR",
        IWeaponGetter => "WEAP", IArmorGetter => "ARMO", ILeveledItemGetter => "LVLI", IKeyGetter => "KEYM",
        IHazardGetter => "HAZD", IAddonNodeGetter => "ADDN", IScrollGetter => "SCRL", ISoulGemGetter => "SLGM",
        IAmmunitionGetter => "AMMO", ITalkingActivatorGetter => "TACT",
        _ => r.GetType().Name.Replace("BinaryOverlay", ""),
    };

    public static string? Model(IMajorRecordGetter r) => (r as IModeledGetter)?.Model?.File.DataRelativePath.Path.ToLowerInvariant();

    public static float[] V(P3Float p) => new[] { p.X, p.Y, p.Z };

    public static Dictionary<string, object?> Ref(IPlacedGetter r, ILinkCache? cache)
    {
        var d = new Dictionary<string, object?> { ["fk"] = Key(r.FormKey), ["flags"] = r.MajorRecordFlagsRaw, ["deleted"] = r.IsDeleted };
        switch (r)
        {
            case IPlacedObjectGetter o:
                d["base"] = Key(o.Base.FormKey);
                if (o.Placement is { } p) { d["pos"] = V(p.Position); d["rot"] = V(p.Rotation); }
                d["scale"] = o.Scale ?? 1f;
                if (o.TeleportDestination is { } t)
                {
                    var dd = new Dictionary<string, object?> { ["to_ref"] = Key(t.Door.FormKey), ["to_pos"] = V(t.Position), ["to_rot"] = V(t.Rotation) };
                    // the partner door's placement and its own marker: where a copy's pair stands and lands
                    if (cache != null && cache.TryResolve<IPlacedObjectGetter>(t.Door.FormKey, out var pd) && pd.Placement is { } pp)
                    {
                        dd["partner_pos"] = V(pp.Position); dd["partner_rot"] = V(pp.Rotation);
                        if (pd.TeleportDestination is { } pt) { dd["partner_to_pos"] = V(pt.Position); dd["partner_to_rot"] = V(pt.Rotation); }
                    }
                    d["door"] = dd;
                }
                if (!o.Owner.IsNull) d["owner"] = Key(o.Owner.FormKey);
                if (o.LinkedReferences.Count > 0) d["linked"] = o.LinkedReferences.Select(l => new Dictionary<string, object?> { ["ref"] = Key(l.Reference.FormKey), ["keyword"] = Key(l.KeywordOrReference.FormKey) }).ToList();
                if (o.EnableParent is { } ep) d["enable_parent"] = Key(ep.Reference.FormKey);
                if (o.Lock is { } lk) d["lock"] = (int)lk.Level;
                if (o.LocationRefTypes is { Count: > 0 } lrt) d["loc_ref_types"] = lrt.Select(x => Key(x.FormKey)).ToList();
                break;
            case IPlacedNpcGetter n:
                d["base"] = Key(n.Base.FormKey);
                if (n.Placement is { } q) { d["pos"] = V(q.Position); d["rot"] = V(q.Rotation); }
                d["scale"] = n.Scale ?? 1f;
                if (n.LinkedReferences.Count > 0) d["linked"] = n.LinkedReferences.Select(l => new Dictionary<string, object?> { ["ref"] = Key(l.Reference.FormKey), ["keyword"] = Key(l.KeywordOrReference.FormKey) }).ToList();
                if (n.EnableParent is { } ep2) d["enable_parent"] = Key(ep2.Reference.FormKey);
                break;
            default:
                d["base"] = ""; break;
        }
        if (cache != null && d["base"] is string bk && bk != "" && cache.TryResolve<IMajorRecordGetter>(Fk(bk), out var b))
        {
            d["base_type"] = Sig(b); d["base_edid"] = b.EditorID; d["model"] = Model(b);
            if (b is IObjectBoundedGetter ob && ob.ObjectBounds is { } bb) d["bounds"] = new[] { bb.First.X, bb.First.Y, bb.First.Z, bb.Second.X, bb.Second.Y, bb.Second.Z };
        }
        return d;
    }

    public static void WriteJson(string path, object o)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(path))!);
        File.WriteAllText(path, JsonSerializer.Serialize(o, Js));
    }

    public static IEnumerable<ICellGetter> Cells(IWorldspaceGetter ws)
    {
        foreach (var b in ws.SubCells) foreach (var sb in b.Items) foreach (var c in sb.Items) yield return c;
    }
}
