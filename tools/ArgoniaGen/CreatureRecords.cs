// creatures: the province's wild creatures (1.15 §g.3) the Skyrim way (tools/argonia_world/creatures/records.py).
//   Add(mod, world.json's "creatures", data): decision 0035, nothing levelled against the player. One LVLN per list
//     (LVLF 2, every entry at level 1: the band picks the list, never the player's level), one NPC_ per list
//     templated on it (TPLT, every template flag, RNAM the placeholder race: Skyrim.esm's own shape for its 451
//     levelled encounter NPC_; ACBS at the band's level, CalcMin = CalcMax, no PC-level multiplier), one ECZN per
//     zone (min = max), and our fixed copy of every scaling mod creature the lists name (`actors`: the mod's record
//     duplicated with its AI, model, sounds and spells, ACBS fixed at the band's level, stats our own where it took
//     them from a template, and a levelled death item swapped for our level-1 copy of its list tree).
//   creatures --in <ArgoniaWorld.esm> --refs <dir> --out <esm>: the spawn ACHRs (NAME, XEZN, DATA) and den REFRs
//     (NAME, DATA) spliced at the end of each cell's Temporary group as VegetationRecords.cs does (the same layout
//     for a REFR; an ACHR's XEZN sits between NAME and DATA as Skyrim.esm's do). No unit maths and no choices.
using System.IO.Compression;
using System.Text;
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;
using Noggog;

namespace ArgoniaGen;

static class CreatureRecords
{
    const SkyrimRelease Rel = SkyrimRelease.SkyrimSE;
    static string S(JsonElement e, string k) => e.GetProperty(k).GetString() ?? throw new InvalidDataException($"{k} is null");
    static FormKey FK(string s) => FormKey.Factory(s);

    public static void Add(SkyrimMod mod, JsonElement c, string data)
    {
        Actors(mod, c, data);
        foreach (var l in c.GetProperty("lists").EnumerateArray())
        {
            var lv = new LeveledNpc(FK(S(l, "formKey")), Rel)
            {
                EditorID = S(l, "edid"),
                Flags = LeveledNpc.Flag.CalculateForEachItemInCount,
                Entries = new ExtendedList<LeveledNpcEntry>(),
            };
            foreach (var e in l.GetProperty("entries").EnumerateArray())
                lv.Entries.Add(new LeveledNpcEntry
                {
                    Data = new LeveledNpcEntryData
                    {
                        Reference = new FormLink<INpcSpawnGetter>(FK(e[0].GetString()!)),
                        Level = (short)One(e[1].GetInt32(), S(l, "edid")), Count = (short)e[2].GetInt32(),
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
                    Level = new NpcLevel { Level = (short)t.GetProperty("level").GetInt32() },
                    CalcMinLevel = (short)t.GetProperty("level").GetInt32(), CalcMaxLevel = (short)t.GetProperty("level").GetInt32(),
                    SpeedMultiplier = 100,
                },
                PlayerSkills = new PlayerSkills(),
                AIData = new AIData(),
            };
            n.Race.SetTo(FK(S(t, "race")));
            n.Template.SetTo(FK(S(t, "list")));
            mod.Npcs.Add(n);
        }
        foreach (var z in c.GetProperty("zones").EnumerateArray())
            if (z.GetProperty("minLevel").GetInt32() != z.GetProperty("maxLevel").GetInt32())
                throw new InvalidDataException($"{S(z, "edid")}: zone min <> max (decision 0035)");
        foreach (var z in c.GetProperty("zones").EnumerateArray())
            mod.EncounterZones.Add(new EncounterZone(FK(S(z, "formKey")), Rel)
            {
                EditorID = S(z, "edid"), MinLevel = (byte)z.GetProperty("minLevel").GetInt32(),
                MaxLevel = (byte)z.GetProperty("maxLevel").GetInt32(),
                Flags = z.GetProperty("neverResets").GetBoolean() ? EncounterZone.Flag.NeverResets : 0,
            });
        Afflictions(mod, c);
    }

    static int One(int level, string where) =>
        level == 1 ? 1 : throw new InvalidDataException($"{where}: a levelled entry at {level} (decision 0035)");

    // Decision 0035's copies. The masters are read as overlays, one at a time by owner (never a whole-environment
    // LinkCache: the memory guidance); a record is looked up in the plugin that owns its FormKey.
    static readonly Dictionary<string, ISkyrimModDisposableGetter> plugins = new(StringComparer.OrdinalIgnoreCase);

    static ISkyrimModGetter Plugin(JsonElement c, string data, ModKey mk)
    {
        if (plugins.TryGetValue(mk.FileName, out var m)) return m;
        var path = c.TryGetProperty("plugins", out var pp) && pp.TryGetProperty(mk.FileName, out var p)
            ? p.GetString()! : Path.Combine(data, mk.FileName);
        return plugins[mk.FileName] = SkyrimMod.CreateFromBinaryOverlay(path, Rel);
    }

    static T Get<T>(JsonElement c, string data, FormKey fk) where T : class, IMajorRecordGetter
    {
        var m = Plugin(c, data, fk.ModKey);
        return m.EnumerateMajorRecords<T>().FirstOrDefault(r => r.FormKey == fk)
            ?? throw new InvalidDataException($"creatures: no {typeof(T).Name} {fk}");
    }

    // The NPC_ whose part (Use Stats, Use Traits) a form takes, through its template chain.
    static INpcGetter Resolve(JsonElement c, string data, INpcGetter n, NpcConfiguration.TemplateFlag part)
    {
        for (var i = 0; i < 8 && n.Configuration.TemplateFlags.HasFlag(part) && !n.Template.IsNull; i++)
        {
            var t = Plugin(c, data, n.Template.FormKey.ModKey).EnumerateMajorRecords<INpcGetter>()
                .FirstOrDefault(r => r.FormKey == n.Template.FormKey);
            if (t is null) break;  // a levelled template: its entries are their own records
            n = t;
        }
        return n;
    }

    static readonly Dictionary<FormKey, FormKey> fixedLists = new();
    static uint nextList;

    // A levelled item list reaches an entry above level 1 (the player's level gates it).
    static bool Levelled(JsonElement c, string data, FormKey fk, int depth = 0)
    {
        if (depth > 10) return false;
        var l = Plugin(c, data, fk.ModKey).EnumerateMajorRecords<ILeveledItemGetter>().FirstOrDefault(r => r.FormKey == fk);
        if (l?.Entries is null) return false;
        return l.Entries.Any(e => e.Data is { } d && (d.Level > 1 || Levelled(c, data, d.Reference.FormKey, depth + 1)));
    }

    // Our copy of a levelled item list at level 1: its level-1 entries, each sublist that is itself levelled
    // swapped for its own copy; the list's other flags (use all, each in count) and chance none kept.
    static FormKey FixList(SkyrimMod mod, JsonElement c, string data, FormKey fk)
    {
        if (fixedLists.TryGetValue(fk, out var done)) return done;
        if (!Levelled(c, data, fk)) return fk;
        var src = Get<ILeveledItemGetter>(c, data, fk);
        var key = new FormKey(mod.ModKey, 0x0D6000u + nextList++);
        fixedLists[fk] = key;
        var lv = new LeveledItem(key, Rel)
        {
            EditorID = "ARG_Fixed_" + (src.EditorID ?? fk.ID.ToString("X6")),
            ChanceNone = src.ChanceNone,
            Flags = src.Flags & ~LeveledItem.Flag.CalculateFromAllLevelsLessThanOrEqualPlayer,
            Entries = new ExtendedList<LeveledItemEntry>(),
        };
        foreach (var e in src.Entries ?? (IReadOnlyList<ILeveledItemEntryGetter>)Array.Empty<ILeveledItemEntryGetter>())
            if (e.Data is { Level: <= 1 } d)
                lv.Entries.Add(new LeveledItemEntry
                {
                    Data = new LeveledItemEntryData
                    {
                        Reference = new FormLink<IItemGetter>(FixList(mod, c, data, d.Reference.FormKey)),
                        Level = 1, Count = d.Count,
                    },
                });
        mod.LeveledItems.Add(lv);
        return key;
    }

    static void Actors(SkyrimMod mod, JsonElement c, string data)
    {
        if (!c.TryGetProperty("actors", out var aa)) return;
        foreach (var a in aa.EnumerateArray())
        {
            var src = Get<INpcGetter>(c, data, FK(S(a, "source")));
            var n = (Npc)src.Duplicate(FK(S(a, "formKey")));
            n.EditorID = S(a, "edid");
            var lvl = (short)a.GetProperty("level").GetInt32();
            var cf = n.Configuration;
            if (cf.TemplateFlags.HasFlag(NpcConfiguration.TemplateFlag.Stats))
            {  // the stats came from a template: ours now, copied from the record that held them
                var st = Resolve(c, data, src, NpcConfiguration.TemplateFlag.Stats);
                var keep = cf.TemplateFlags & ~NpcConfiguration.TemplateFlag.Stats;
                n.Configuration = st.Configuration.DeepCopy();
                n.Configuration.TemplateFlags = keep;
                n.Class.SetTo(st.Class.FormKey);
                n.PlayerSkills = st.PlayerSkills?.DeepCopy();
                cf = n.Configuration;
            }
            cf.Level = new NpcLevel { Level = lvl };  // an NpcLevel, not a PcLevelMult: Mutagen writes the ACBS flag off
            cf.CalcMinLevel = lvl;
            cf.CalcMaxLevel = lvl;
            if (a.GetProperty("deathItem").GetBoolean())
            {
                if (cf.TemplateFlags.HasFlag(NpcConfiguration.TemplateFlag.Traits))
                    throw new InvalidDataException($"{n.EditorID}: its death item comes from a template (not handled)");
                n.DeathItem.SetTo(FixList(mod, c, data, src.DeathItem.FormKey));
            }
            mod.Npcs.Add(n);
        }
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
