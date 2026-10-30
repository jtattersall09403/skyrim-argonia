// PACK: AI packages built on a vanilla package template, the way the CK writes one. Research (Skyrim.esm, Mutagen 0.54.4,
// `ArgoniaGen packages --edids a,b` dumps the shape of any PACK):
//   * Templates are PACK records of Type PackageTemplate with no template link: Sandbox 01C254:Skyrim.esm, Sleep 019717:Skyrim.esm
//     (also Sit 019715, Eat 019714, SandboxAndGuard 05FAD4, SleepAndGuard 0DD745). They hold the ProcedureTree (ANAM/PTDA branches
//     with condition and data-input indices) and the data inputs with Name/Flags(Public) labels.
//   * A package built from one (e.g. MS08SaadiaSandboxRoom, DefaultSleepEditorLoc17x5) has Type Package, PackageTemplate = the
//     template, an EMPTY ProcedureTree, no input Name/Flags, and only the inputs that carry a value (label-only entries such as
//     Sleep's "Wait Timer" are dropped), in the template's order, with the template's DataInputVersion (10 Sandbox, 6 Sleep),
//     XnamMarker, InterruptFlags and preamble events (empty topic + no idle) copied. PKCU is derived from Data by Mutagen.
//   * Sandbox inputs: 0 Location (PackageDataLocation), 14 Unlock On Arrival, 1 Allow Eating, 3 Sleeping, 4 Conversation, 5 Idle
//     Markers, 6 Sitting, 31 Special Furniture, 7 Wandering, 25 Preferred Path Only, 27 RideHorse, 29 Energy (float 50).
//   * Sleep inputs: 0 Location, 1 Target (PackageDataTarget; vanilla Target = TouchActorEffects object type or a specific bed
//     reference), 15 Lock Doors, 13 Warn Before Locking, 2 Found Bed (object list), 17..22/25 Allow*, 26 MinWanderDistance (300),
//     24 Energy (50). A vanilla sleep package sets Flags WeaponsUnequipped.
//   * Location kinds (Mutagen LocationTarget classes inside LocationTargetRadius): LocationTarget{Link: placed ref} (near reference),
//     LocationCell{Link: cell} (in cell), LocationFallback{Type NearEditorLocation}. Radius is in units.
//   * Schedule: ScheduleHour (-1 any), ScheduleMinute (-1 any), ScheduleDurationInMinutes, ScheduleDayOfWeek (Any), Month -1, Date 0.
// So this writer copies the template's valued inputs and the record fields the CK copies, then applies the intermediate's values.
// Not writable by Mutagen/not verified against the CK: nothing structural found; risk is the CK's own repack of PKDT.Unknown
// (random-looking bytes 32/105/130 in vanilla), which we leave as the template's 0.
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;

namespace ArgoniaGen;

static class PackageRecords
{
    const SkyrimRelease Rel = SkyrimRelease.SkyrimSE;
    static readonly Dictionary<string, ISkyrimModDisposableGetter> Masters = new();

    static string S(JsonElement e, string k) => e.GetProperty(k).GetString() ?? throw new InvalidDataException($"{k} is null");
    static FormKey FK(string s) => FormKey.Factory(s);

    public static void Write(SkyrimMod mod, JsonElement r, string data)
    {
        if (S(r, "type") != "PACK") throw new InvalidDataException($"PackageRecords: {S(r, "type")}");
        var tk = FK(S(r, "template"));
        if (!Masters.TryGetValue(tk.ModKey.FileName, out var m)) Masters[tk.ModKey.FileName] = m = Load.Open(data, tk.ModKey.FileName);
        var t = m.Packages.FirstOrDefault(p => p.FormKey == tk) ?? throw new InvalidDataException($"template {tk} is not a PACK of {tk.ModKey}");
        if (t.Type != Package.Types.PackageTemplate) throw new InvalidDataException($"{tk} is not a package template");

        var p = new Package(FK(S(r, "formKey")), Rel)
        {
            EditorID = S(r, "edid"), Type = Package.Types.Package, InterruptOverride = t.InterruptOverride, PreferredSpeed = t.PreferredSpeed,
            InterruptFlags = t.InterruptFlags, DataInputVersion = t.DataInputVersion, XnamMarker = t.XnamMarker.ToArray(),
            ScheduleMonth = -1, ScheduleDate = 0, ScheduleHour = -1, ScheduleMinute = -1,
            OnBegin = t.OnBegin?.DeepCopy(), OnEnd = t.OnEnd?.DeepCopy(), OnChange = t.OnChange?.DeepCopy(),
        };
        p.PackageTemplate.SetTo(tk);
        if (r.TryGetProperty("flags", out var fl)) foreach (var f in fl.EnumerateArray()) p.Flags |= Enum.Parse<Package.Flag>(f.GetString()!);
        if (r.TryGetProperty("speed", out var sp)) p.PreferredSpeed = Enum.Parse<Package.Speed>(sp.GetString()!);
        var sc = r.GetProperty("schedule");
        p.ScheduleHour = (sbyte)sc.GetProperty("hour").GetInt32();
        if (sc.TryGetProperty("minute", out var mi)) p.ScheduleMinute = (sbyte)mi.GetInt32();
        p.ScheduleDurationInMinutes = (int)Math.Round(sc.GetProperty("durationHours").GetDouble() * 60);
        if (sc.TryGetProperty("dayOfWeek", out var dw)) p.ScheduleDayOfWeek = Enum.Parse<Package.DayOfWeek>(dw.GetString()!);

        foreach (var kv in t.Data)
        {
            if (kv.Value is not (IPackageDataLocationGetter or IPackageDataBoolGetter or IPackageDataIntGetter or IPackageDataFloatGetter
                or IPackageDataTargetGetter or IPackageDataObjectListGetter or IPackageDataTopicGetter)) continue;  // label-only entries
            var c = kv.Value.DeepCopy();
            c.Name = null; c.Flags = 0;
            p.Data[kv.Key] = c;
        }
        if (r.TryGetProperty("location", out var loc)) SetLocation(p, 0, loc);
        if (r.TryGetProperty("target", out var tg))
            ((PackageDataTarget)p.Data[1]).Target = new PackageTargetSpecificReference { Reference = new FormLink<IPlacedGetter>(FK(S(tg, "ref"))), CountOrDistance = 0 };
        if (r.TryGetProperty("inputs", out var ins))
            foreach (var i in ins.EnumerateArray())
            {
                var idx = (sbyte)i.GetProperty("index").GetInt32();
                switch (p.Data[idx])
                {
                    case PackageDataBool b: b.Data = i.GetProperty("value").GetBoolean(); break;
                    case PackageDataInt n2: n2.Data = i.GetProperty("value").GetUInt32(); break;
                    case PackageDataFloat f2: f2.Data = i.GetProperty("value").GetSingle(); break;
                    default: throw new InvalidDataException($"{S(r, "edid")}: input {idx} is not a bool/int/float");
                }
            }
        mod.Packages.Add(p);
    }

    static void SetLocation(Package p, sbyte idx, JsonElement loc)
    {
        var d = (PackageDataLocation)p.Data[idx];
        var radius = loc.TryGetProperty("radius", out var rd) ? rd.GetSingle() : 0f;
        ALocationTarget tgt = loc.TryGetProperty("ref", out var rf) ? new LocationTarget { Link = new FormLink<IPlacedGetter>(FK(rf.GetString()!)) }
            : loc.TryGetProperty("cell", out var ce) ? new LocationCell { Link = new FormLink<ICellGetter>(FK(ce.GetString()!)) }
            : throw new InvalidDataException("location needs ref or cell");
        d.Location = new LocationTargetRadius { Target = tgt, Radius = (uint)Math.Round(radius) };
    }

    // Reflection dump: the vanilla PACK shape, whatever the Mutagen API calls it.
    public static int Dump(string data, string outPath, string[] sample, string plugin = "Skyrim.esm")
    {
        using var mod = Load.Open(data, plugin);
        var list = new List<object?>();
        foreach (var p in mod.Packages)
        {
            var e = p.EditorID ?? "";
            if (sample.Contains(e)) list.Add(Dyn(p, 0));
        }
        // templates: PACK records that are templates (no template link, Template flag set) listed by name
        var tmpl = mod.Packages.Where(p => p.PackageTemplate.IsNull).Select(p => new { p.FormKey, p.EditorID, p.Type, f = p.Flags.ToString() }).ToList();
        var brief = new List<object>();
        foreach (var p in mod.Packages.Where(p => sample.Contains(p.EditorID ?? "")))
        {
            var l = (p.Data.TryGetValue(0, out var d0) ? d0 as IPackageDataLocationGetter : null)?.Location;
            brief.Add(new { edid = p.EditorID, template = p.PackageTemplate.FormKeyNullable?.ToString(), flags = p.Flags.ToString(), hour = (int)p.ScheduleHour,
                durationMinutes = p.ScheduleDurationInMinutes, procedureTree = p.ProcedureTree.Count, inputs = p.Data.Keys.Select(k => (int)k).ToList(),
                locRef = (l?.Target as ILocationTargetGetter)?.Link.FormKeyNullable?.ToString(), radius = l?.Radius });
        }
        foreach (var n in mod.Npcs.Where(n => sample.Contains(n.EditorID ?? "")))
            brief.Add(new { edid = n.EditorID, flags = n.Configuration.Flags.ToString(), keywords = n.Keywords?.Select(k => k.FormKey.ToString()).ToList() ?? new List<string>(), packages = n.Packages.Select(k => k.FormKey.ToString()).ToList() });
        var byT = mod.Packages.Where(p => !p.PackageTemplate.IsNull).GroupBy(p => p.PackageTemplate.FormKeyNullable!.Value.ToString()).Where(g => g.Key is "01C254:Skyrim.esm" or "019717:Skyrim.esm").Select(g => g.Key + " " + string.Join(",", g.Take(12).Select(p => p.EditorID))).ToList();
        Load.WriteJson(outPath, new { brief, byT, tmpl = tmpl.Select(t => $"{t.FormKey} {t.EditorID} {t.Type} {t.f}"), sample = list });
        return 0;
    }

    static object? Dyn(object? o, int depth)
    {
        if (o is null) return null;
        var t = o.GetType();
        if (o is string || t.IsPrimitive || t.IsEnum || o is decimal) return o.ToString();
        if (o is IFormLinkGetter l) return l.FormKeyNullable?.ToString();
        if (depth > 6) return "...";
        if (o is System.Collections.IDictionary d) { var r = new Dictionary<string, object?>(); foreach (System.Collections.DictionaryEntry kv in d) r[kv.Key + ":" + kv.Value?.GetType().Name] = Dyn(kv.Value, depth + 1); return r; }
        if (o is System.Collections.IEnumerable en) return en.Cast<object?>().Select(x => Dyn(x, depth + 1)).ToList();
        var res = new Dictionary<string, object?> { ["$t"] = t.Name };
        foreach (var pr in t.GetProperties().Where(x => x.GetIndexParameters().Length == 0 && x.DeclaringType != typeof(object)))
        {
            if (pr.Name is "StaticRegistration" or "TriggerSpecs" or "Unknown1" or "Registration" or "BinaryWriteTranslator" or "FormVersion" or "VersionControl" or "SkyrimMajorRecordFlags" or "EditorID" or "Version2" or "FormKey" or "Type" && false) continue;
            object? v; try { v = pr.GetValue(o); } catch { continue; }
            if (v is null) continue;
            if (pr.Name is "StaticRegistration" or "TriggerSpecs" or "Unknown1" or "Registration" or "BinaryWriteTranslator" or "FormVersion" or "VersionControl" or "MajorRecordFlagsRaw" or "IsDeleted" or "IsCompressed" or "EditorID" or "FormKey" or "Version2" or "SkyrimMajorRecordFlags") continue;
            res[pr.Name] = Dyn(v, depth + 1);
        }
        return res;
    }
}
