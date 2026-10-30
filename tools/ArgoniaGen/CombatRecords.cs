// NPC_ and ECZN: the intermediate's combat archetypes (tools/argonia_world/combat_records.py) -> Mutagen. Fixed level
// (no PC level multiplier), stats not auto-calculated, the health offset, a face template's traits (decision 0014 §3),
// the compiled perk and the inventory. No choices here: every number and link arrives resolved.
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;
using Noggog;

namespace ArgoniaGen;

static class CombatRecords
{
    const SkyrimRelease Rel = SkyrimRelease.SkyrimSE;

    static string S(JsonElement e, string k) => e.GetProperty(k).GetString() ?? throw new InvalidDataException($"{k} is null");
    static int I(JsonElement e, string k) => e.GetProperty(k).GetInt32();
    static bool B(JsonElement e, string k) => e.TryGetProperty(k, out var v) && v.GetBoolean();
    static IEnumerable<JsonElement> A(JsonElement e, string k) =>
        e.TryGetProperty(k, out var v) ? v.EnumerateArray() : Enumerable.Empty<JsonElement>();
    static FormKey FK(string s) => FormKey.Factory(s);

    public static void Write(SkyrimMod mod, JsonElement r)
    {
        switch (S(r, "type"))
        {
            case "NPC_": Npc(mod, r); break;
            case "ECZN": Zone(mod, r); break;
            default: throw new InvalidDataException($"CombatRecords: {S(r, "type")}");
        }
    }

    static void Zone(SkyrimMod mod, JsonElement r)
    {
        var flags = (EncounterZone.Flag)0;  // optional "flags": EncounterZone.Flag names (NeverResets: a clearable place)
        foreach (var f in A(r, "flags")) flags |= Enum.Parse<EncounterZone.Flag>(f.GetString()!);
        mod.EncounterZones.Add(new EncounterZone(FK(S(r, "formKey")), Rel)
        {
            EditorID = S(r, "edid"), MinLevel = (byte)I(r, "minLevel"), MaxLevel = (byte)I(r, "maxLevel"), Flags = flags,
        });
    }

    static void Npc(SkyrimMod mod, JsonElement r)
    {
        var flags = B(r, "female") ? NpcConfiguration.Flag.Female : 0;
        TemplateFlags(r, out var tf);
        var n = new Npc(FK(S(r, "formKey")), Rel)
        {
            EditorID = S(r, "edid"),
            Name = new TranslatedString(Language.English, S(r, "name")),
            Configuration = new NpcConfiguration
            {
                Flags = flags, Level = new NpcLevel { Level = (short)I(r, "level") },
                CalcMinLevel = (short)I(r, "level"), CalcMaxLevel = (short)I(r, "level"),
                HealthOffset = (short)I(r, "healthOffset"), TemplateFlags = tf, SpeedMultiplier = 100,
            },
            PlayerSkills = new PlayerSkills(),
            AIData = new AIData
            {
                Aggression = Enum.Parse<Aggression>(S(r, "aggression")),
                Confidence = Enum.Parse<Confidence>(S(r, "confidence")),
            },
            Perks = new ExtendedList<PerkPlacement>(),
            Items = new ExtendedList<ContainerEntry>(),
            Height = r.GetProperty("height").GetSingle(), Weight = r.GetProperty("weight").GetSingle(),
        };
        n.Race.SetTo(FK(S(r, "race")));
        n.Class.SetTo(FK(S(r, "class")));
        if (r.TryGetProperty("template", out var t)) n.Template.SetTo(FK(t.GetString()!));
        foreach (var p in A(r, "perks"))
            n.Perks.Add(new PerkPlacement { Perk = new FormLink<IPerkGetter>(FK(p.GetString()!)), Rank = 1 });
        foreach (var i in A(r, "items"))
            n.Items.Add(new ContainerEntry { Item = new ContainerItem { Item = new FormLink<IItemGetter>(FK(S(i, "item"))), Count = I(i, "count") } });
        // Optional people fields (the block's residents): absent means the record writes exactly as before.
        foreach (var f in A(r, "flags")) n.Configuration.Flags |= Enum.Parse<NpcConfiguration.Flag>(f.GetString()!);
        if (r.TryGetProperty("keywords", out var kws))
        {
            n.Keywords = new ExtendedList<IFormLinkGetter<IKeywordGetter>>();
            foreach (var k in kws.EnumerateArray()) n.Keywords.Add(new FormLink<IKeywordGetter>(FK(k.GetString()!)));
        }
        if (r.TryGetProperty("packages", out var pks))
            foreach (var k in pks.EnumerateArray()) n.Packages.Add(new FormLink<IPackageGetter>(FK(k.GetString()!)));
        if (r.TryGetProperty("voice", out var vo)) n.Voice.SetTo(FK(vo.GetString()!));
        if (r.TryGetProperty("outfit", out var of)) n.DefaultOutfit.SetTo(FK(of.GetString()!));
        if (r.TryGetProperty("energy", out var en)) n.AIData.EnergyLevel = (byte)en.GetInt32();
        if (r.TryGetProperty("aggro", out var ag))
        {
            n.AIData.AggroRadiusBehavior = ag.GetProperty("behavior").GetBoolean();
            n.AIData.Warn = (uint)ag.GetProperty("warn").GetInt32();
            n.AIData.WarnOrAttack = (uint)ag.GetProperty("warnOrAttack").GetInt32();
            n.AIData.Attack = (uint)ag.GetProperty("attack").GetInt32();
        }
        if (r.TryGetProperty("responsibility", out var rs)) n.AIData.Responsibility = Enum.Parse<Responsibility>(rs.GetString()!);
        if (r.TryGetProperty("mood", out var md)) n.AIData.Mood = Enum.Parse<Mood>(md.GetString()!);
        if (r.TryGetProperty("assistance", out var asst)) n.AIData.Assistance = Enum.Parse<Assistance>(asst.GetString()!);
        if (r.TryGetProperty("soundLevel", out var sl)) n.SoundLevel = Enum.Parse<SoundLevel>(sl.GetString()!);
        if (r.TryGetProperty("combatStyle", out var cs)) n.CombatStyle.SetTo(FK(cs.GetString()!));
        foreach (var f in A(r, "factions"))
            n.Factions.Add(new RankPlacement { Faction = new FormLink<IFactionGetter>(FK(S(f, "faction"))), Rank = (sbyte)I(f, "rank") });
        if (r.TryGetProperty("crimeFaction", out var cf)) n.CrimeFaction.SetTo(FK(cf.GetString()!));
        mod.Npcs.Add(n);
    }

    static void TemplateFlags(JsonElement r, out NpcConfiguration.TemplateFlag tf)
    {
        tf = 0;
        foreach (var f in A(r, "templateFlags")) tf |= Enum.Parse<NpcConfiguration.TemplateFlag>(f.GetString()!);
    }
}
