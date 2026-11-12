using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;

// The new world's music (docs/design/music.md "In game"; data newworld/sources/music/records.json), made Bethesda's
// way (decision 0034), measured on Skyrim.esm 2026-11-12:
//   - a region carries its exploration music type in its sound data (REGN RDMO: WeatherFallForest -> MUSExploreForestPine);
//     a separate world names a fallback type on the worldspace (DLC2SolstheimWorld ZNAM DLC2MUSExploreSolstheimGeneral);
//   - an explore type cycles single tracks with silent spacers between (MUSExploreMarsh: flags CycleTracks, priority
//     49, fade 12 s; _MUSExploreSILENT30TypeSpacer); day tracks carry GetCurrentTime >= 6 AND <= 20, night tracks
//     GetCurrentTime >= 22 OR <= 5 (MUSExploreDay01, MUSExploreNight01); ours use 6..20 and 20..6, so no hour is silent;
//   - combat, death and level-up music are the default object types (DOBJ SMTB MUSCombat, SMTD MUSSpecialDeath,
//     SMCS/SMUL MUSSpecialSuccess) and discovery the four MUSDiscovery* types; none can be set per world, so our
//     tracks are added to them with GetInWorldspace == ours, and each of Skyrim's tracks in them is overridden with
//     GetInWorldspace != ours put first (an AND ahead of its own conditions). No plugin of the NewWorld profile
//     (Update.esm, the DLCs, USSEP and the rest) overrides any of these records (measured 2026-11-12), so Skyrim.esm's
//     record is the load order's winner and the template.
// Ids by formula in the idspace row `music` (tools/newworld/idspace.py): track slot i day 0x090100 + i, night
// 0x090140 + i, explore type of class j 0x090180 + j.
static class NewWorldMusic
{
    public const uint IdTrack = 0x090100, IdNight = 0x090140, IdType = 0x090180, IdEnd = 0x0901FF;
    static readonly FormKey Spacer = FormKey.Factory("0C7027:Skyrim.esm");        // _MUSExploreSILENT30TypeSpacer
    static readonly FormKey ExploreTemplate = FormKey.Factory("0C76D3:Skyrim.esm"); // MUSExploreMarsh
    // Skyrim's default music types our pieces join, by records.json key
    static readonly (string key, string type)[] Defaults =
    [
        ("combat", "03418E"), ("boss", "0D777A"), ("death", "013686"), ("levelup", "03B565"),
        ("discovery", "0AC13D"), ("discovery", "0ABDA3"), ("discovery", "0ABDA4"), ("discovery", "0ABDA5"),
    ];

    // Slots in pieces.json order: a slot's index is its id's offset, so a slot keeps its ids for life.
    public static void Attach(SkyrimMod mod, Worldspace ws, string sourcesDir, string dataDir)
    {
        // the world's registry sits in newworld/sources; a test world's beside its ESM: then the repo's sources serve
        for (var d = new DirectoryInfo(Environment.CurrentDirectory); !File.Exists(Path.Combine(sourcesDir, "music", "records.json")) && d != null; d = d.Parent)
            sourcesDir = Path.Combine(d.FullName, "newworld", "sources");
        var musicDir = Path.Combine(sourcesDir, "music");
        var rec = JsonDocument.Parse(File.ReadAllText(Path.Combine(musicDir, "records.json"))).RootElement;
        var slots = JsonDocument.Parse(File.ReadAllText(Path.Combine(musicDir, "pieces.json"))).RootElement
            .GetProperty("pieces").EnumerateArray().Select(p => p.GetProperty("id").GetString()!).ToList();
        var regionClass = JsonDocument.Parse(File.ReadAllText(Path.Combine(sourcesDir, "atmosphere", "regions.json"))).RootElement
            .GetProperty("regions").EnumerateObject().ToDictionary(r => r.Name, r => r.Value[0].GetString()!);
        string Pattern = rec.GetProperty("files").GetString()!;
        List<string> L(JsonElement e) => e.EnumerateArray().Select(x => x.GetString()!).ToList();
        FormKey K(uint id) => new(mod.ModKey, id);
        using var sky = SkyrimMod.CreateFromBinaryOverlay(Path.Combine(dataDir, "Skyrim.esm"), SkyrimRelease.SkyrimSE);

        var made = new Dictionary<(string, bool), FormKey>();
        FormKey Track(string slot, bool? night)
        {
            int i = slots.IndexOf(slot);
            if (i < 0) throw new InvalidDataException($"music: no slot {slot} in pieces.json");
            if (made.TryGetValue((slot, night == true), out var have)) return have;
            var t = new MusicTrack(K((night == true ? IdNight : IdTrack) + (uint)i), SkyrimRelease.SkyrimSE)
            {
                EditorID = "ANW_MUS_" + slot.Replace("-", "_") + (night == true ? "_Night" : ""),
                Type = MusicTrack.TypeEnum.SingleTrack,
                TrackFilename = Pattern.Replace("{slot}", slot),
                Conditions = new(),
            };
            if (night == false) { t.Conditions.Add(Hour(CompareOperator.GreaterThanOrEqualTo, 6)); t.Conditions.Add(Hour(CompareOperator.LessThan, 20)); }
            if (night == true) { t.Conditions.Add(Hour(CompareOperator.GreaterThanOrEqualTo, 20, or: true)); t.Conditions.Add(Hour(CompareOperator.LessThan, 6)); }
            if (night is null) t.Conditions.Add(InWorld(ws.FormKey, true));
            mod.MusicTracks.Add(t);
            return made[(slot, night == true)] = t.FormKey;
        }

        // exploration: one type per class, Skyrim's explore type as the template
        var template = sky.MusicTypes.First(m => m.FormKey == ExploreTemplate);
        var night = L(rec.GetProperty("night"));
        var typeOf = new Dictionary<string, FormKey>();
        int j = 0;
        foreach (var cls in rec.GetProperty("day").EnumerateObject())
        {
            var mt = (MusicType)template.Duplicate(K(IdType + (uint)j++));
            mt.EditorID = "ANW_MUSExplore_" + cls.Name.Replace("-", "_");
            mt.Tracks = new();
            foreach (var s in L(cls.Value)) { mt.Tracks.Add(Track(s, false)); mt.Tracks.Add(Spacer); }
            foreach (var s in night) { mt.Tracks.Add(Track(s, true)); mt.Tracks.Add(Spacer); }
            mod.MusicTypes.Add(mt);
            typeOf[cls.Name] = mt.FormKey;
        }
        if (IdType + (uint)j - 1 > IdEnd) throw new InvalidDataException("music: types run out of their range");

        int regions = 0;
        foreach (var r in mod.Regions.Where(r => r.EditorID?.StartsWith("ANW_Region_") == true))
        {
            var name = r.EditorID!["ANW_Region_".Length..].Replace("_", "-");
            if (!regionClass.TryGetValue(name, out var cls) || !typeOf.TryGetValue(cls, out var mk))
                throw new InvalidDataException($"music: region {name} has no atmosphere class with music");
            r.Sounds ??= new RegionSounds { Flags = RegionData.RegionDataFlag.Override, Priority = (byte)NewWorldAtmosphere.RegionPriority };
            r.Sounds.Music.SetTo(mk);
            regions++;
        }
        ws.Music.SetTo(typeOf[rec.GetProperty("world").GetString()!]);

        // combat, death, level-up, discovery: ours joined to Skyrim's types, Skyrim's tracks kept out of our world
        var guarded = new HashSet<FormKey>();
        int joined = 0;
        foreach (var (key, id) in Defaults)
        {
            var fk = new FormKey(sky.ModKey, Convert.ToUInt32(id, 16));
            var src = sky.MusicTypes.First(m => m.FormKey == fk);
            var o = src.DeepCopy();
            foreach (var t in src.Tracks ?? []) if (guarded.Add(t.FormKey)) Guard(mod, sky, t.FormKey, ws.FormKey);
            o.Tracks ??= new();
            foreach (var s in L(rec.GetProperty(key))) { o.Tracks.Add(Track(s, null)); joined++; }
            mod.MusicTypes.Add(o);
        }
        Console.WriteLine($"  music: {mod.MusicTracks.Count(t => t.FormKey.ModKey == mod.ModKey)} tracks, {typeOf.Count} explore types, {regions} regions, {Defaults.Length} of Skyrim's types joined ({joined} tracks), {guarded.Count} of Skyrim's tracks kept out of the world");
    }

    // A vanilla track of a default type (and a palette's sub-tracks) gets GetInWorldspace(ours) == 0 first.
    static void Guard(SkyrimMod mod, ISkyrimModGetter sky, FormKey fk, FormKey world)
    {
        if (mod.MusicTracks.Any(t => t.FormKey == fk)) return;
        var src = sky.MusicTracks.FirstOrDefault(t => t.FormKey == fk) ?? throw new InvalidDataException($"music: {fk} not in Skyrim.esm");
        var t = src.DeepCopy();
        t.Conditions ??= new();
        t.Conditions.Insert(0, InWorld(world, false));
        mod.MusicTracks.Add(t);
        foreach (var s in src.Tracks ?? []) Guard(mod, sky, s.FormKey, world);
    }

    static ConditionFloat Hour(CompareOperator op, float h, bool or = false) =>
        new() { Data = new GetCurrentTimeConditionData(), CompareOperator = op, ComparisonValue = h, Flags = or ? Condition.Flag.OR : 0 };

    static ConditionFloat InWorld(FormKey world, bool inside)
    {
        var d = new GetInWorldspaceConditionData();
        d.WorldspaceOrList.Link.SetTo(world);
        return new() { Data = d, CompareOperator = CompareOperator.EqualTo, ComparisonValue = inside ? 1 : 0 };
    }
}
