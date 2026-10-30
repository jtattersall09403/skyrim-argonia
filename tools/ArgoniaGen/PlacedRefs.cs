// Placed references (REFR and ACHR), one mapping for every cell writer: interior CELLs (Generate.cs), the place
// layers' exterior CELL overrides and the worldspace's persistent cell (PlaceCells.cs). As Generate.cs: no unit
// maths and no choices; every number and link arrives resolved.
//   ref: {formKey, edid?, base, pos, rot, scale?, persistent?, actor? (true: an ACHR of an NPC_ base),
//         disabled? (initially disabled), teleport? {door: the partner door ref, pos, rot},
//         owner? (NPC_ or FACT), persistentLocation? (ACHR XLCN), lock? {level: LockLevel name, key?}, encounterZone?, ignoredBySandbox?,
//         linked? [{ref, keyword?}], enableParent? {ref, opposite?}}
using System.Text.Json;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Noggog;

namespace ArgoniaGen;

static class PlacedRefs
{
    const SkyrimRelease Rel = SkyrimRelease.SkyrimSE;

    static string S(JsonElement e, string k) => e.GetProperty(k).GetString() ?? throw new InvalidDataException($"{k} is null");
    static string? Os(JsonElement e, string k) => e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() : null;
    static bool B(JsonElement e, string k) => e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.True;
    static FormKey FK(string s) => FormKey.Factory(s);
    static P3Float P3(JsonElement e, string k)
    {
        var a = e.GetProperty(k).EnumerateArray().Select(x => x.GetSingle()).ToArray();
        return new P3Float(a[0], a[1], a[2]);
    }

    public static bool Persistent(JsonElement p) => B(p, "persistent");

    /// One placed reference; persistent ones carry the record flag (the caller files it in the persistent list).
    public static IPlaced Build(JsonElement p)
    {
        var place = new Placement { Position = P3(p, "pos"), Rotation = P3(p, "rot") };
        float? scale = p.TryGetProperty("scale", out var sc) && Math.Abs(sc.GetSingle() - 1f) > 1e-6 ? sc.GetSingle() : null;
        if (B(p, "actor"))
        {
            var a = new PlacedNpc(FK(S(p, "formKey")), Rel) { EditorID = Os(p, "edid"), Placement = place, Scale = scale };
            a.Base.SetTo(FK(S(p, "base")));
            if (Os(p, "encounterZone") is { } ez) a.EncounterZone.SetTo(FK(ez));
            if (Os(p, "persistentLocation") is { } pl) a.PersistentLocation.SetTo(FK(pl));  // XLCN: its editor location
            if (Persistent(p)) a.MajorRecordFlagsRaw |= (int)PlacedNpc.MajorFlag.Persistent;
            if (B(p, "disabled")) a.MajorRecordFlagsRaw |= (int)SkyrimMajorRecord.SkyrimMajorRecordFlag.InitiallyDisabled;
            Linked(p, a.LinkedReferences);
            return a;
        }
        var o = new PlacedObject(FK(S(p, "formKey")), Rel) { EditorID = Os(p, "edid"), Placement = place, Scale = scale };
        o.Base.SetTo(FK(S(p, "base")));
        if (p.TryGetProperty("teleport", out var t))
        {
            o.TeleportDestination = new TeleportDestination { Position = P3(t, "pos"), Rotation = P3(t, "rot") };
            o.TeleportDestination.Door.SetTo(FK(S(t, "door")));
        }
        if (Os(p, "owner") is { } ow) o.Owner.SetTo(FK(ow));
        if (p.TryGetProperty("lock", out var l))
        {
            o.Lock = new LockData { Level = Enum.Parse<LockLevel>(S(l, "level")) };
            if (Os(l, "key") is { } key) o.Lock.Key.SetTo(FK(key));
        }
        if (Os(p, "encounterZone") is { } z) o.EncounterZone.SetTo(FK(z));
        if (B(p, "ignoredBySandbox")) o.IsIgnoredBySandbox = true;
        if (p.TryGetProperty("enableParent", out var ep))
        {
            o.EnableParent = new EnableParent { Flags = B(ep, "opposite") ? EnableParent.Flag.SetEnableStateToOppositeOfParent : 0 };
            o.EnableParent.Reference.SetTo(FK(S(ep, "ref")));
        }
        Linked(p, o.LinkedReferences);
        if (Persistent(p)) o.MajorRecordFlagsRaw |= (int)PlacedObject.DefaultMajorFlag.Persistent;
        if (B(p, "disabled")) o.MajorRecordFlagsRaw |= (int)SkyrimMajorRecord.SkyrimMajorRecordFlag.InitiallyDisabled;
        return o;
    }

    static void Linked(JsonElement p, ExtendedList<LinkedReferences> into)
    {
        if (!p.TryGetProperty("linked", out var ls)) return;
        foreach (var l in ls.EnumerateArray())
        {
            var lr = new LinkedReferences();
            lr.Reference.SetTo(FK(S(l, "ref")));
            if (Os(l, "keyword") is { } kw) lr.KeywordOrReference.SetTo(FK(kw));
            into.Add(lr);
        }
    }

    /// Into a cell's persistent or temporary list by the ref's own flag.
    public static void File(Cell c, JsonElement p)
    {
        var r = Build(p);
        if (Persistent(p)) c.Persistent.Add(r); else c.Temporary.Add(r);
    }
}
