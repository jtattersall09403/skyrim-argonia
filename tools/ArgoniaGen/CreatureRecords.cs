// creatures: the province's wild creatures (1.15 §g.3) the Skyrim way (tools/argonia_world/creatures/records.py).
//   Add(mod, world.json's "creatures"): one LVLN per list (LVLF 3, every entry at its band's level), one NPC_ per
//     list templated on it (TPLT, every template flag, RNAM the placeholder race: Skyrim.esm's own shape for its
//     451 levelled encounter NPC_), one ECZN per zone (min = max: the band's fixed level).
//   creatures --in <ArgoniaWorld.esm> --refs <dir> --out <esm>: the spawn ACHRs (NAME, XEZN, DATA) and den REFRs
//     (NAME, DATA) spliced at the end of each cell's Temporary group as VegetationRecords.cs does (the same layout
//     for a REFR; an ACHR's XEZN sits between NAME and DATA as Skyrim.esm's do). No unit maths and no choices.
using System.IO.Compression;
using System.Text;
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;
using Noggog;

namespace ArgoniaGen;

static class CreatureRecords
{
    const SkyrimRelease Rel = SkyrimRelease.SkyrimSE;
    static string S(JsonElement e, string k) => e.GetProperty(k).GetString() ?? throw new InvalidDataException($"{k} is null");
    static FormKey FK(string s) => FormKey.Factory(s);

    public static void Add(SkyrimMod mod, JsonElement c)
    {
        foreach (var l in c.GetProperty("lists").EnumerateArray())
        {
            var lv = new LeveledNpc(FK(S(l, "formKey")), Rel)
            {
                EditorID = S(l, "edid"),
                Flags = LeveledNpc.Flag.CalculateFromAllLevelsLessThanOrEqualPlayer | LeveledNpc.Flag.CalculateForEachItemInCount,
                Entries = new ExtendedList<LeveledNpcEntry>(),
            };
            foreach (var e in l.GetProperty("entries").EnumerateArray())
                lv.Entries.Add(new LeveledNpcEntry
                {
                    Data = new LeveledNpcEntryData
                    {
                        Reference = new FormLink<INpcSpawnGetter>(FK(e[0].GetString()!)),
                        Level = (short)e[1].GetInt32(), Count = (short)e[2].GetInt32(),
                    },
                });
            mod.LeveledNpcs.Add(lv);
        }
        foreach (var t in c.GetProperty("templates").EnumerateArray())
        {
            var n = new Npc(FK(S(t, "formKey")), Rel)
            {
                EditorID = S(t, "edid"),
                Configuration = new NpcConfiguration
                {
                    TemplateFlags = (NpcConfiguration.TemplateFlag)0x1FFF,  // every part from the template (40 vanilla)
                    Level = new NpcLevel { Level = 1 }, CalcMinLevel = 1, CalcMaxLevel = 1, SpeedMultiplier = 100,
                },
                PlayerSkills = new PlayerSkills(),
                AIData = new AIData(),
            };
            n.Race.SetTo(FK(S(t, "race")));
            n.Template.SetTo(FK(S(t, "list")));
            mod.Npcs.Add(n);
        }
        foreach (var z in c.GetProperty("zones").EnumerateArray())
            mod.EncounterZones.Add(new EncounterZone(FK(S(z, "formKey")), Rel)
            {
                EditorID = S(z, "edid"), MinLevel = (byte)z.GetProperty("minLevel").GetInt32(),
                MaxLevel = (byte)z.GetProperty("maxLevel").GetInt32(),
                Flags = z.GetProperty("neverResets").GetBoolean() ? EncounterZone.Flag.NeverResets : 0,
            });
        Afflictions(mod, c);
    }

    // Our afflictions where no mod ships one (records.py OUR_EFFECTS: Skyrim.esm's own disease and poison shapes):
    // a disease is a constant-effect contact SPEL of type Disease, a poison a fire-and-forget contact one of type
    // Poison; each effect its own hostile, detrimental MGEF on one actor value.
    static void Afflictions(SkyrimMod mod, JsonElement c)
    {
        if (!c.TryGetProperty("afflictions", out var aa)) return;
        foreach (var a in aa.EnumerateArray())
        {
            var disease = S(a, "kind") == "disease";
            var effects = a.GetProperty("effects").EnumerateArray().ToList();
            var cast = disease ? CastType.ConstantEffect : CastType.FireAndForget;
            var mgef = FK(S(a, "mgef"));
            var e0 = effects[0];
            mod.MagicEffects.Add(new MagicEffect(mgef, Rel)
            {
                EditorID = S(a, "edid") + "Effect",
                Name = new TranslatedString(Language.English, S(a, "name")),
                Flags = MagicEffect.Flag.Hostile | MagicEffect.Flag.Detrimental | MagicEffect.Flag.Recover,
                Archetype = new MagicEffectArchetype(Enum.Parse<MagicEffectArchetype.TypeEnum>(S(e0, "archetype")))
                {
                    ActorValue = Enum.Parse<ActorValue>(S(e0, "av")),
                },
                CastType = cast, TargetType = TargetType.Touch,
            });
            var sp = new Spell(FK(S(a, "spel")), Rel)
            {
                EditorID = S(a, "edid"),
                Name = new TranslatedString(Language.English, S(a, "name")),
                Description = new TranslatedString(Language.English, ""),
                Type = disease ? SpellType.Disease : SpellType.Poison,
                CastType = cast, TargetType = TargetType.Touch,
            };
            for (var i = 0; i < effects.Count; i++)
            {
                var e = effects[i];
                var fk = mgef;
                if (i > 0)  // a further actor value: its own MGEF beside the first (id + 0x800 x i, records.py)
                {
                    fk = new FormKey(mgef.ModKey, mgef.ID + 0x800u * (uint)i);
                    mod.MagicEffects.Add(new MagicEffect(fk, Rel)
                    {
                        EditorID = S(a, "edid") + "Effect" + i,
                        Name = new TranslatedString(Language.English, S(a, "name")),
                        Flags = MagicEffect.Flag.Hostile | MagicEffect.Flag.Detrimental | MagicEffect.Flag.Recover,
                        Archetype = new MagicEffectArchetype(Enum.Parse<MagicEffectArchetype.TypeEnum>(S(e, "archetype")))
                        {
                            ActorValue = Enum.Parse<ActorValue>(S(e, "av")),
                        },
                        CastType = cast, TargetType = TargetType.Touch,
                    });
                }
                var eff = new Effect
                {
                    Data = new EffectData { Magnitude = e.GetProperty("magnitude").GetSingle(), Area = 0,
                                            Duration = e.GetProperty("duration").GetInt32() },
                };
                eff.BaseEffect.SetTo(fk);
                sp.Effects.Add(eff);
            }
            mod.Spells.Add(sp);
        }
    }

    public static int Run(string inPath, string refsDir, string outPath) =>
        VegetationRecords.Splice(inPath, outPath, "creatures", (masters, own) => Load(refsDir, masters, own));

    static (Dictionary<(int, int), byte[]>, long) Load(string dir, IReadOnlyList<string> masters, uint own)
    {
        var mi = masters.Select((m, i) => (m, i)).ToDictionary(t => t.m, t => (uint)t.i, StringComparer.OrdinalIgnoreCase);
        mi.TryAdd("ArgoniaWorld.esm", (uint)masters.Count);
        uint Id(string fk)
        {
            var s = fk.Split(':');
            if (!mi.TryGetValue(s[1], out var k)) throw new InvalidDataException($"creatures: {s[1]} is not a master of the plugin");
            return (k << 24) | Convert.ToUInt32(s[0], 16);
        }
        var outp = new Dictionary<(int, int), byte[]>();
        long n = 0;
        foreach (var path in Directory.GetFiles(dir, "cy*.jsonl.gz").Order(StringComparer.Ordinal))
        {
            using var f = File.OpenRead(path);
            using var z = new GZipStream(f, CompressionMode.Decompress);
            using var rd = new StreamReader(z);
            while (rd.ReadLine() is { } line)
            {
                if (line.Length == 0) continue;
                using var doc = JsonDocument.Parse(line);
                var e = doc.RootElement;
                var key = (e.GetProperty("x").GetInt32(), e.GetProperty("y").GetInt32());
                using var ms = new MemoryStream();
                var w = new BinaryWriter(ms);
                foreach (var r in e.GetProperty("refs").EnumerateArray())
                {
                    var sig = r[1].GetString()!;
                    var achr = sig == "ACHR";
                    w.Write(Encoding.ASCII.GetBytes(sig));
                    w.Write((uint)(10 + (achr ? 10 : 0) + 30));
                    w.Write(0u);
                    w.Write(own | r[0].GetUInt32());
                    w.Write(0u);
                    w.Write((ushort)44);
                    w.Write((ushort)0);
                    w.Write(Encoding.ASCII.GetBytes("NAME")); w.Write((ushort)4); w.Write(Id(r[2].GetString()!));
                    if (achr) { w.Write(Encoding.ASCII.GetBytes("XEZN")); w.Write((ushort)4); w.Write(Id(r[3].GetString()!)); }
                    w.Write(Encoding.ASCII.GetBytes("DATA")); w.Write((ushort)24);
                    for (var k = 4; k <= 9; k++) w.Write(r[k].GetSingle());
                    n++;
                }
                if (!outp.TryAdd(key, ms.ToArray())) throw new InvalidDataException($"creatures: cell {key} twice");
            }
        }
        return (outp, n);
    }
}
