// RACE and CSTY: a creature's race override and our combat styles (tools/argonia_world/place_build.py, creature_hunt;
// game-10 §4) -> Mutagen. The RACE override copies the master's record whole (from Data) and adds the named flags
// (the crocodile's race: Walks), so nothing else of the race changes. A CSTY's numbers arrive resolved.
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;

namespace ArgoniaGen;

static class RaceRecords
{
    const SkyrimRelease Rel = SkyrimRelease.SkyrimSE;
    static readonly Dictionary<string, ISkyrimModDisposableGetter> masters = new(StringComparer.OrdinalIgnoreCase);

    static string S(JsonElement e, string k) => e.GetProperty(k).GetString() ?? throw new InvalidDataException($"{k} is null");
    static float F(JsonElement e, string k) => e.GetProperty(k).GetSingle();
    static IEnumerable<JsonElement> A(JsonElement e, string k) =>
        e.TryGetProperty(k, out var v) ? v.EnumerateArray() : Enumerable.Empty<JsonElement>();
    static FormKey FK(string s) => FormKey.Factory(s);

    public static void Write(SkyrimMod mod, JsonElement r, string data)
    {
        switch (S(r, "type"))
        {
            case "RACE": Race(mod, r, data); break;
            case "CSTY": Style(mod, r); break;
            default: throw new InvalidDataException($"RaceRecords: {S(r, "type")}");
        }
    }

    static void Race(SkyrimMod mod, JsonElement r, string data)
    {
        var key = FK(S(r, "formKey"));
        var file = key.ModKey.FileName.String;
        if (!masters.TryGetValue(file, out var master))
            masters[file] = master = SkyrimMod.CreateFromBinaryOverlay(Path.Combine(data, file), Rel);
        if (!master.Races.TryGetValue(key, out var src)) throw new InvalidDataException($"no RACE {key} in {file}");
        var race = mod.Races.GetOrAddAsOverride(src);
        foreach (var f in A(r, "flagsAdd")) race.Flags |= Enum.Parse<Race.Flag>(f.GetString()!);
    }

    // The player (1.10): Skyrim.esm's Player overridden with the race and one race preset's face, copied whole (head
    // parts, feather colour, morphs, face parts, tints, texture lighting), as the race menu does when a preset is
    // picked. The head texture stays the race default so the head's scales match the body's (no neck seam).
    public static void Player(SkyrimMod mod, JsonElement r, string data)
    {
        var key = FK(S(r, "formKey"));
        var file = key.ModKey.FileName.String;
        if (!masters.TryGetValue(file, out var master))
            masters[file] = master = SkyrimMod.CreateFromBinaryOverlay(Path.Combine(data, file), Rel);
        if (!master.Npcs.TryGetValue(key, out var src)) throw new InvalidDataException($"no NPC_ {key} in {file}");
        var pk = FK(S(r, "preset"));
        if (!master.Npcs.TryGetValue(pk, out var preset) || preset.EditorID != S(r, "presetEdid"))
            throw new InvalidDataException($"the player's preset {pk} is not {S(r, "presetEdid")} in {file}");
        var race = FK(S(r, "race"));
        if (preset.Race.FormKey != race) throw new InvalidDataException($"{preset.EditorID} is not of race {race}");
        // Copied without its localized names (their strings live in the master's BSA, which Mutagen does not read
        // here): the override carries no FULL, so the save's own player name stands.
        var p = (Npc)src.DeepCopy(new Npc.TranslationMask(true) { Name = false, ShortName = false });
        // Factions, spells and items in FormKey order, as Spriggit writes them back (the round trip is byte-identical).
        var fac = p.Factions.OrderBy(f => f.Faction.FormKey.ModKey.FileName.String).ThenBy(f => f.Faction.FormKey.ID).ToList();
        p.Factions.Clear(); p.Factions.AddRange(fac);
        if (p.ActorEffect is { } sp) { var s = sp.OrderBy(k => k.FormKey.ModKey.FileName.String).ThenBy(k => k.FormKey.ID).ToList(); sp.Clear(); sp.AddRange(s); }
        // The inventory is the starting kit (start.json `player.kit`, 1.12), not the master's engine test kit.
        if (r.TryGetProperty("items", out var kit) && kit.ValueKind == JsonValueKind.Array)
        {
            p.Items = new Noggog.ExtendedList<ContainerEntry>();
            foreach (var e in kit.EnumerateArray())
                p.Items.Add(new ContainerEntry { Item = new ContainerItem { Item = new FormLink<IItemGetter>(FK(S(e, "item"))), Count = e.GetProperty("count").GetInt32() } });
        }
        if (p.Items is { } it) { var s = it.OrderBy(e => e.Item.Item.FormKey.ModKey.FileName.String).ThenBy(e => e.Item.Item.FormKey.ID).ToList(); it.Clear(); it.AddRange(s); }
        if (p.PlayerSkills is { } ps) ps.Unused2 = new byte[ps.Unused2.Length];  // the pad byte Spriggit writes as 0
        mod.Npcs.Add(p);
        p.Race.SetTo(race);
        p.HeadParts.Clear();
        p.HeadParts.AddRange(preset.HeadParts.Select(h => h.FormKey));
        p.HairColor.SetTo(preset.HairColor.FormKeyNullable);
        p.HeadTexture.Clear();
        p.TextureLighting = preset.TextureLighting;
        p.FaceMorph = preset.FaceMorph?.DeepCopy();
        p.FaceParts = preset.FaceParts?.DeepCopy();
        p.TintLayers.Clear();
        p.TintLayers.AddRange(preset.TintLayers.Select(t => t.DeepCopy()));
        p.Weight = preset.Weight;
    }

    static void Style(SkyrimMod mod, JsonElement r)
    {
        var cs = new CombatStyle(FK(S(r, "formKey")), Rel)
        {
            EditorID = S(r, "edid"),
            OffensiveMult = F(r, "offensive"), DefensiveMult = F(r, "defensive"), GroupOffensiveMult = F(r, "groupOffensive"),
            EquipmentScoreMultMelee = 1, EquipmentScoreMultMagic = 1, EquipmentScoreMultRanged = 1,
            EquipmentScoreMultShout = 1, EquipmentScoreMultUnarmed = 1, EquipmentScoreMultStaff = 1,
            AvoidThreatChance = F(r, "avoidThreat"),
            Melee = new CombatStyleMelee
            {
                AttackStaggeredMult = F(r, "attackStaggered"), PowerAttackStaggeredMult = F(r, "powerAttackStaggered"),
                PowerAttackBlockingMult = F(r, "powerAttackBlocking"),
            },
            CloseRange = new CombatStyleCloseRange
            {
                CircleMult = F(r, "circle"), FallbackMult = F(r, "fallback"), FlankDistance = F(r, "flankDistance"),
                StalkTime = F(r, "stalkTime"),
            },
            LongRangeStrafeMult = F(r, "longRangeStrafe"),
        };
        foreach (var f in A(r, "flags")) cs.Flags |= Enum.Parse<CombatStyle.Flag>(f.GetString()!);
        mod.CombatStyles.Add(cs);
    }
}
