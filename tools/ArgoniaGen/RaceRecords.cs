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
