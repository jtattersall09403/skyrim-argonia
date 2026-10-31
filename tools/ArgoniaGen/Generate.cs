// generate: intermediate JSON (tools/argonia_world/intermediate.py) -> Argonia.esm. No unit maths and no
// choices here: every number, id and link arrives resolved; this only maps fields onto Mutagen's records.
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Strings;
using Mutagen.Bethesda.Skyrim;
using Noggog;

namespace ArgoniaGen;

static class Generate
{
    const SkyrimRelease Rel = SkyrimRelease.SkyrimSE;

    public static int Run(string inPath, string data, string outPath)
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(inPath));
        var root = doc.RootElement;
        if (root.GetProperty("schema").GetInt32() != 1) throw new InvalidDataException("intermediate schema must be 1");
        var modKey = ModKey.FromFileName(root.GetProperty("mod").GetString()!);
        var mod = new SkyrimMod(modKey, Rel);
        using var places = new PlaceCells(data);
        mod.ModHeader.Flags |= SkyrimModHeader.HeaderFlag.Master;
        mod.ModHeader.Author = root.GetProperty("author").GetString();
        mod.ModHeader.Description = root.GetProperty("description").GetString();
        var loadOrder = root.GetProperty("loadOrder").EnumerateArray().Select(e => ModKey.FromFileName(e.GetString()!)).ToList();

        foreach (var r in root.GetProperty("records").EnumerateArray())
        {
            var type = S(r, "type");
            switch (type)
            {
                case "GLOB": Glob(mod, r); break;
                case "MUSC": Music(mod, r); break;
                case "STAT": Static(mod, r); break;
                case "CELL" when r.TryGetProperty("override", out var ov) && ov.GetBoolean(): places.Add(r); break;
                case "CELL": Cell(mod, r); break;
                case "QUST": QuestRecords.Write(mod, r); break;
                case "CLAS": Class(mod, r); break;
                case "SPEL": Spell(mod, r); break;
                case "LVLI": LevItem(mod, r); break;
                case "LTEX": LandTextures.Write(mod, r); break;
                case "KYWD": ItemWriters.Write(mod, r); break;
                case "WEAP": ItemWriters.Write(mod, r); break;
                case "ARMO": ItemWriters.Write(mod, r); break;
                case "ARMA": ItemWriters.Write(mod, r); break;
                case "CONT": ItemWriters.Write(mod, r); break;
                case "BOOK": ItemWriters.Write(mod, r); break;
                case "MISC": ItemWriters.Write(mod, r); break;
                case "ALCH": ItemWriters.Write(mod, r); break;
                case "PERK": PerkRecords.Write(mod, r); break;
                case "LSCR": LoadScreenRecords.Write(mod, r); break;
                case "PACK": PackageRecords.Write(mod, r, data); break;
                case "NPC_" or "ECZN" or "OTFT": CombatRecords.Write(mod, r); break;
                case "ACTI" or "GMST" or "LCTN": ActivatorRecords.Write(mod, r); break;
                case "RACE" or "CSTY": RaceRecords.Write(mod, r, data); break;
                case "FACT" or "MESG" or "FLST": SocialRecords.Write(mod, r); break;
                case "REGN" or "CLMT" or "WTHR" or "IMGS" or "WRLD": RegionWriters.Write(mod, r, data); break;
                default: throw new InvalidDataException($"record type {type} has no writer ({S(r, "edid")})");
            }
        }

        places.Finish(mod);  // the place layers' cell overrides, after the WRLD override exists
        // Interior cell blocks and sub-blocks in number order (the canonical order the round trip compares).
        var blocks = mod.Cells.Records.OrderBy(b => b.BlockNumber).ToList();
        mod.Cells.Records.Clear();
        foreach (var b in blocks)
        {
            var subs = b.SubBlocks.OrderBy(x => x.BlockNumber).ToList();
            b.SubBlocks.Clear(); b.SubBlocks.AddRange(subs);
            mod.Cells.Records.Add(b);
        }
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(outPath))!);
        mod.BeginWrite
            .ToPath(outPath)
            .WithLoadOrder(loadOrder.Append(modKey))
            .WithDataFolder(data)
            .Write();
        // A master's own masters are listed too (as the Creation Kit does), or the engine hoists an ESP master above
        // this ESM but leaves that ESP's master below it (Cipactli above HTBM, game-6). Mutagen's WithAllParentMasters
        // reads every master from Data, and ArgoniaWorld.esm is not there, so the parents are read here (PlaceCells'
        // resolution) and the file written once more with them.
        var listed = ReadMasters(outPath, data);
        var parents = listed.SelectMany(m => ReadMasters(MasterPath(m, data), data)).Distinct().Where(m => !listed.Contains(m)).ToList();
        if (parents.Count > 0)
            mod.BeginWrite
                .ToPath(outPath)
                .WithLoadOrder(loadOrder.Append(modKey))
                .WithDataFolder(data)
                .WithExtraIncludedMasters(parents)
                .Write();
        Console.WriteLine($"generate: {mod.EnumerateMajorRecords().Count()} records -> {outPath}");
        return 0;
    }

    static string MasterPath(ModKey m, string data) =>
        m.FileName.String.Equals("ArgoniaWorld.esm", StringComparison.OrdinalIgnoreCase)
            ? Environment.GetEnvironmentVariable("ARGONIA_WORLD_ESM") ?? throw new InvalidDataException("ARGONIA_WORLD_ESM is not set (pipeline.py sets it)")
            : Path.Combine(data, m.FileName.String);

    static List<ModKey> ReadMasters(string path, string data)
    {
        using var m = SkyrimMod.CreateFromBinaryOverlay(path, Rel);
        return m.ModHeader.MasterReferences.Select(r => r.Master).ToList();
    }

    // ---- field helpers -------------------------------------------------------------------------------------
    static string S(JsonElement e, string k) => e.GetProperty(k).GetString() ?? throw new InvalidDataException($"{k} is null");
    static string? Os(JsonElement e, string k) => e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() : null;
    static float F(JsonElement e, string k, float d = 0) => e.TryGetProperty(k, out var v) ? v.GetSingle() : d;
    static int I(JsonElement e, string k, int d = 0) => e.TryGetProperty(k, out var v) ? v.GetInt32() : d;
    static IEnumerable<JsonElement> A(JsonElement e, string k) =>
        e.TryGetProperty(k, out var v) ? v.EnumerateArray() : Enumerable.Empty<JsonElement>();
    static FormKey FK(string s) => FormKey.Factory(s);
    static FormKey Key(JsonElement r) => FK(S(r, "formKey"));
    static P3Float P3(JsonElement e, string k)
    {
        var a = e.GetProperty(k).EnumerateArray().Select(x => x.GetSingle()).ToArray();
        return new P3Float(a[0], a[1], a[2]);
    }
    static T Flags<T>(JsonElement r, string k) where T : struct, Enum
    {
        long v = 0;
        foreach (var f in A(r, k)) v |= Convert.ToInt64(Enum.Parse<T>(f.GetString()!));
        return (T)Enum.ToObject(typeof(T), v);
    }
    static TranslatedString? Text(JsonElement r, string k) => Os(r, k) is { } s ? new TranslatedString(Language.English, s) : null;

    // ---- writers -----------------------------------------------------------------------------------------
    static void Glob(SkyrimMod mod, JsonElement r)
    {
        var g = new GlobalShort(Key(r), Rel) { EditorID = S(r, "edid"), Data = (short)I(r, "value") };
        mod.Globals.Add(g);
    }

    static void Music(SkyrimMod mod, JsonElement r)
    {
        var m = new MusicType(Key(r), Rel) { EditorID = S(r, "edid"), Flags = Flags<MusicType.Flag>(r, "flags") };
        // An empty track list is an access violation when the engine picks a track (game-6): never written.
        var tracks = A(r, "tracks").Select(t => FK(t.GetString()!)).ToList();
        if (tracks.Count == 0) throw new InvalidDataException($"MUSC {m.EditorID} has no track: the engine crashes on it");
        m.Tracks = tracks.Select(t => (IFormLinkGetter<IMusicTrackGetter>)t.ToLink<IMusicTrackGetter>()).ToExtendedList();
        mod.MusicTypes.Add(m);
    }

    static void Static(SkyrimMod mod, JsonElement r)
    {
        var s = new Static(Key(r), Rel) { EditorID = S(r, "edid"), Model = new Model { File = S(r, "model") } };
        mod.Statics.Add(s);
    }

    static void Cell(SkyrimMod mod, JsonElement r)
    {
        var key = Key(r);
        var c = new Cell(key, Rel)
        {
            EditorID = S(r, "edid"),
            Name = Text(r, "name"),
            Flags = Flags<Cell.Flag>(r, "flags"),
        };
        if (Os(r, "music") is { } mus) c.Music.SetTo(FK(mus));
        if (Os(r, "water") is { } wat) c.Water.SetTo(FK(wat));  // interior water (fixtures): optional
        if (r.TryGetProperty("waterHeight", out var wh)) c.WaterHeight = wh.GetSingle();
        if (r.TryGetProperty("lighting", out var l))
            c.Lighting = new CellLighting
            {
                AmbientColor = Color(l, "ambient"),
                DirectionalColor = Color(l, "directional"),
                FogNearColor = Color(l, "fogNear"),
                FogFarColor = Color(l, "fogFar"),
                FogNear = F(l, "fogNearDistance"),
                FogFar = F(l, "fogFarDistance"),
                FogClipDistance = F(l, "fogClipDistance"),
                FogPower = F(l, "fogPower", 1),
                LightFadeBegin = F(l, "fadeBegin"),
                LightFadeEnd = F(l, "fadeEnd"),
                DirectionalFade = F(l, "directionalFade", 1),
                FogMax = F(l, "fogMax", 1),
            };
        foreach (var p in A(r, "refs")) PlacedRefs.File(c, p);
        if (!c.Flags.HasFlag(Mutagen.Bethesda.Skyrim.Cell.Flag.IsInteriorCell))
            throw new InvalidDataException($"{c.EditorID}: exterior cells go through the worldspace writer (0.4 §d)");
        // Interior cells live in block id%10, sub-block (id/10)%10 (the engine's grouping).
        int block = (int)(key.ID % 10), sub = (int)(key.ID / 10 % 10);
        var b = mod.Cells.Records.FirstOrDefault(x => x.BlockNumber == block);
        if (b == null) { b = new CellBlock { BlockNumber = block, GroupType = GroupTypeEnum.InteriorCellBlock }; mod.Cells.Records.Add(b); }
        var sb = b.SubBlocks.FirstOrDefault(x => x.BlockNumber == sub);
        if (sb == null) { sb = new CellSubBlock { BlockNumber = sub, GroupType = GroupTypeEnum.InteriorCellSubBlock }; b.SubBlocks.Add(sb); }
        sb.Cells.Add(c);
    }

    static System.Drawing.Color Color(JsonElement l, string k)
    {
        if (!l.TryGetProperty(k, out var v)) return System.Drawing.Color.FromArgb(0, 0, 0, 0);
        var a = v.EnumerateArray().Select(x => x.GetInt32()).ToArray();
        return System.Drawing.Color.FromArgb(0, a[0], a[1], a[2]);
    }

    static void Class(SkyrimMod mod, JsonElement r)
    {
        var c = new Class(Key(r), Rel)
        {
            EditorID = S(r, "edid"),
            Name = Text(r, "name") ?? new TranslatedString(Language.English, ""),
            Description = Text(r, "description") ?? new TranslatedString(Language.English, ""),
            Teaches = Enum.Parse<Skill>(S(r, "teaches")),
            MaxTrainingLevel = (byte)I(r, "maxTrainingLevel"),
            BleedoutDefault = F(r, "bleedoutDefault"),
            VoicePoints = (uint)I(r, "voicePoints"),
        };
        foreach (var w in r.GetProperty("skillWeights").EnumerateObject()) c.SkillWeights[Enum.Parse<Skill>(w.Name)] = (byte)w.Value.GetInt32();
        foreach (var w in r.GetProperty("statWeights").EnumerateObject()) c.StatWeights[Enum.Parse<BasicStat>(w.Name)] = (byte)w.Value.GetInt32();
        mod.Classes.Add(c);
    }

    static void Spell(SkyrimMod mod, JsonElement r)
    {
        var s = new Spell(Key(r), Rel)
        {
            EditorID = S(r, "edid"),
            Name = Text(r, "name"),
            Description = Text(r, "description") ?? new TranslatedString(Language.English, ""),
            Type = Enum.Parse<SpellType>(S(r, "spellType")),
            CastType = Enum.Parse<CastType>(S(r, "castType")),
            TargetType = Enum.Parse<TargetType>(S(r, "targetType")),
            Flags = Flags<SpellDataFlag>(r, "flags"),
        };
        foreach (var e in A(r, "effects"))
        {
            var eff = new Effect
            {
                Data = new EffectData { Magnitude = F(e, "magnitude"), Area = I(e, "area"), Duration = I(e, "duration") },
            };
            eff.BaseEffect.SetTo(FK(S(e, "effect")));
            s.Effects.Add(eff);
        }
        mod.Spells.Add(s);
    }

    static void LevItem(SkyrimMod mod, JsonElement r)
    {
        var l = new LeveledItem(Key(r), Rel)
        {
            EditorID = S(r, "edid"),
            Flags = Flags<LeveledItem.Flag>(r, "flags"),
            ChanceNone = new Percent(F(r, "chanceNone") / 100.0),
            Entries = new ExtendedList<LeveledItemEntry>(),
        };
        foreach (var e in A(r, "entries"))
        {
            var d = new LeveledItemEntryData { Level = (short)I(e, "level", 1), Count = (short)I(e, "count", 1) };
            d.Reference.SetTo(FK(S(e, "item")));
            l.Entries.Add(new LeveledItemEntry { Data = d });
        }
        mod.LeveledItems.Add(l);
    }
}
