// MODS: a base record's alternate texture sets (lane 1.15-r3-mods). A STAT/TREE/FLOR/ACTI/MSTT model's MODS maps a
// NIF shape to a TXST whose TX00/TX01 replace the shape's own diffuse and normal; Black Marsh.esm names TXST diffuses
// no source ships, drawn as Skyrim's missing-texture lavender (docs/research/2026-11-02/lane-1.15-r3-shader.md).
//   alttex --data <dir> --forms <txt: one FormKey a line> --out <json>   read only: each form's sets (an NPC_'s through
//          its skin's ARMA world models), {formKey: {"sig", "sets": [{"shape", "txst", "diffuse", "normal"}]}};
//          [--in <esm>]: read each form from that plugin first, else its owner (the overrides' read-back), listing each one
//   Write: the world step's override of a base with its MODS dropped, so the NIF's own texture set draws (LandWorld.cs); for a
//          creature NPC_, of its skin's ARMAs (their world models' MODS dropped).
// Records are read from the plugin that owns the FormKey, as overlays (the memory guidance; CreatureRecords.cs).
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;

namespace ArgoniaGen;

static class AltTextures
{
    static readonly Dictionary<string, Dictionary<FormKey, IMajorRecordGetter>> byPlugin = new(StringComparer.OrdinalIgnoreCase);

    static readonly SortedSet<string> missing = new(StringComparer.OrdinalIgnoreCase);

    static string? only;  // --in: every form read from this one plugin (the read-back of ArgoniaWorld.esm's overrides)

    static IMajorRecordGetter? Find(string data, FormKey fk)
    {
        if (only is not null)
        {
            if (!byPlugin.TryGetValue("", out var o))
            {
                o = new Dictionary<FormKey, IMajorRecordGetter>();
                foreach (var r in SkyrimMod.CreateFromBinaryOverlay(only, SkyrimRelease.SkyrimSE).EnumerateMajorRecords()) o.TryAdd(r.FormKey, r);
                byPlugin[""] = o;
            }
            if (o.TryGetValue(fk, out var hit)) return hit;  // else the owner's record (an NPC_ whose skin ARMA we override)
        }
        if (!byPlugin.TryGetValue(fk.ModKey.FileName, out var d))
        {
            var path = Path.Combine(data, fk.ModKey.FileName);
            d = new Dictionary<FormKey, IMajorRecordGetter>();
            byPlugin[fk.ModKey.FileName] = d;
            if (!File.Exists(path)) { missing.Add(fk.ModKey.FileName); return null; }  // our own plugins: no MODS
            var m = SkyrimMod.CreateFromBinaryOverlay(path, SkyrimRelease.SkyrimSE);
            foreach (var r in m.EnumerateMajorRecords()) d.TryAdd(r.FormKey, r);
        }
        return d.GetValueOrDefault(fk);
    }

    static IEnumerable<IAlternateTextureGetter> Alts(IMajorRecordGetter r) => r switch
    {
        IStaticGetter s => s.Model?.AlternateTextures ?? [],
        ITreeGetter t => t.Model?.AlternateTextures ?? [],
        IFloraGetter f => f.Model?.AlternateTextures ?? [],
        IActivatorGetter a => a.Model?.AlternateTextures ?? [],
        IMoveableStaticGetter m => m.Model?.AlternateTextures ?? [],
        IArmorAddonGetter aa => (aa.WorldModel?.Male?.AlternateTextures ?? []).Concat(aa.WorldModel?.Female?.AlternateTextures ?? []),
        _ => [],
    };

    static IEnumerable<IAlternateTextureGetter> NpcAlts(string data, INpcGetter n) => SkinArmatures(data, n).SelectMany(Alts);

    static IEnumerable<IArmorAddonGetter> SkinArmatures(string data, INpcGetter n)
    {
        for (var i = 0; i < 8 && n.Configuration.TemplateFlags.HasFlag(NpcConfiguration.TemplateFlag.Traits) && !n.Template.IsNull; i++)
            if (Find(data, n.Template.FormKey) is INpcGetter t) n = t; else break;  // a levelled template: its entries are records of their own
        var skin = n.WornArmor.FormKey;
        if (skin.IsNull && Find(data, n.Race.FormKey) is IRaceGetter race) skin = race.Skin.FormKey;
        if (skin.IsNull || Find(data, skin) is not IArmorGetter armo) yield break;
        foreach (var aa in armo.Armature)
            if (Find(data, aa.FormKey) is IArmorAddonGetter a && Alts(a).Any()) yield return a;
    }

    public static int Scan(string data, string formsPath, string outPath, string? inPlugin = null)
    {
        only = inPlugin;
        var outp = new SortedDictionary<string, object>(StringComparer.Ordinal);
        foreach (var line in File.ReadAllLines(formsPath).Select(l => l.Trim()).Where(l => l.Length > 0).Distinct())
        {
            var r = Find(data, FormKey.Factory(line));
            if (r is null) continue;
            var alts = (r is INpcGetter n ? NpcAlts(data, n) : Alts(r)).ToList();
            if (alts.Count == 0 && only is null) continue;  // a read-back lists every record found, sets or none
            outp[line] = new
            {
                sig = r.Registration.ClassType.Name,
                sets = alts.Select(a =>
                {
                    var t = Find(data, a.NewTexture.FormKey) as ITextureSetGetter;
                    return new { shape = a.Name, txst = a.NewTexture.FormKey.ToString(), diffuse = t?.Diffuse?.ToString(), normal = t?.NormalOrGloss?.ToString() };
                }).ToList(),
            };
        }
        Load.WriteJson(outPath, outp);
        Console.WriteLine($"alttex: {outp.Count} forms with alternate texture sets; plugins not in the data folder: {string.Join(", ", missing)}");
        return 0;
    }

    /// The override of each base in ArgoniaWorld.esm, its model's MODS dropped (nothing else changed).
    public static int Write(SkyrimMod mod, string data, IEnumerable<string> keys)
    {
        var n = 0;
        foreach (var k in keys)
        {
            var fk = FormKey.Factory(k);
            switch (Find(data, fk))
            {
                case IStaticGetter s: { var o = mod.Statics.GetOrAddAsOverride(s); if (o.Model is { } m) m.AlternateTextures = null; break; }
                case ITreeGetter t: { var o = mod.Trees.GetOrAddAsOverride(t); if (o.Model is { } m) m.AlternateTextures = null; break; }
                case IFloraGetter f: { var o = mod.Florae.GetOrAddAsOverride(f); if (o.Model is { } m) m.AlternateTextures = null; break; }
                case IActivatorGetter a: { var o = mod.Activators.GetOrAddAsOverride(a); if (o.Model is { } m) m.AlternateTextures = null; break; }
                case IMoveableStaticGetter ms: { var o = mod.MoveableStatics.GetOrAddAsOverride(ms); if (o.Model is { } m) m.AlternateTextures = null; break; }
                case INpcGetter npc:  // a creature: its skin's ARMA world models, both sexes (the NPC_ itself is untouched)
                    foreach (var aa in SkinArmatures(data, npc))
                    {
                        var o = mod.ArmorAddons.GetOrAddAsOverride(aa);
                        if (o.WorldModel?.Male is { } ml) ml.AlternateTextures = null;
                        if (o.WorldModel?.Female is { } fm) fm.AlternateTextures = null;
                    }
                    break;
                case null when missing.Contains(fk.ModKey.FileName): continue;  // a data folder without that plugin (the unit tests); the read-back is red in a real build
                case null: throw new InvalidDataException($"alttex: no record {fk}");
                case var r: throw new InvalidDataException($"alttex: {fk} is a {r.Registration.Name}, not a STAT/TREE/FLOR/ACTI/MSTT/NPC_");
            }
            n++;
        }
        return n;
    }

    /// The writer's unit test (test_alttex.py): a synthetic master with a MODS-carrying STAT, TREE and FLOR, their
    /// overrides written into a second plugin and read back. Exit 0 when every override exists and carries no MODS
    /// while the master's still do.
    public static int SelfTest(string dir)
    {
        Directory.CreateDirectory(dir);
        var mk = ModKey.FromFileName("AltMaster.esm");
        var master = new SkyrimMod(mk, SkyrimRelease.SkyrimSE);
        var txst = new TextureSet(master) { EditorID = "T", Diffuse = "landscape\\plants\\absent.dds" };
        master.TextureSets.Add(txst);
        Model M() => new() { File = "a.nif", AlternateTextures = [new AlternateTexture { Name = "Leaf", NewTexture = txst.ToLink(), Index = 0 }] };
        var st = new Static(master) { EditorID = "S", Model = M() };
        var tr = new Tree(master) { EditorID = "R", Model = M() };
        var fl = new Flora(master) { EditorID = "F", Model = M() };
        master.Statics.Add(st); master.Trees.Add(tr); master.Florae.Add(fl);
        var mp = Path.Combine(dir, mk.FileName);
        master.WriteToBinary(mp);
        var ours = new SkyrimMod(ModKey.FromFileName("AltOurs.esm"), SkyrimRelease.SkyrimSE);
        var keys = new[] { st.FormKey, tr.FormKey, fl.FormKey }.Select(k => k.ToString()).ToArray();
        var n = Write(ours, dir, keys);
        var op = Path.Combine(dir, "AltOurs.esm");
        ours.BeginWrite.ToPath(op).WithLoadOrder(mk, ours.ModKey).WithDataFolder(dir).Write();
        byPlugin.Clear();
        only = op;
        var bad = keys.Where(k => Find(dir, FormKey.Factory(k)) is not { } r || Alts(r).Any()).ToList();
        only = mp; byPlugin.Clear();
        bad.AddRange(keys.Where(k => Find(dir, FormKey.Factory(k)) is not { } r || !Alts(r).Any()).Select(k => "master " + k));
        only = null; byPlugin.Clear();
        Console.WriteLine($"alttex selftest: {n} overrides written, {bad.Count} wrong {string.Join(" ", bad)}");
        return n == 3 && bad.Count == 0 ? 0 : 1;
    }
}
