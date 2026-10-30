// ACTI and GMST: the intermediate's activators (tools/argonia_world/life_records.py) and game-setting overrides -> Mutagen.
// No choices here: the name, mesh path, keyword links and verb arrive resolved; a GMST is an override of a
// master's setting (its FormKey is the master's) or, for a setting no master record carries, a new record of ours.
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;

namespace ArgoniaGen;

static class ActivatorRecords
{
    const SkyrimRelease Rel = SkyrimRelease.SkyrimSE;

    static string S(JsonElement e, string k) => e.GetProperty(k).GetString() ?? throw new InvalidDataException($"{k} is null");
    static FormKey FK(string s) => FormKey.Factory(s);

    public static void Write(SkyrimMod mod, JsonElement r)
    {
        switch (S(r, "type"))
        {
            case "ACTI": Acti(mod, r); break;
            case "GMST": Setting(mod, r); break;
            default: throw new InvalidDataException($"ActivatorRecords: {S(r, "type")}");
        }
    }

    static void Acti(SkyrimMod mod, JsonElement r)
    {
        var a = new Mutagen.Bethesda.Skyrim.Activator(FK(S(r, "formKey")), Rel)
        {
            EditorID = S(r, "edid"),
            Name = new TranslatedString(Language.English, S(r, "name")),
            Model = new Model { File = S(r, "model") },
            ActivateTextOverride = new TranslatedString(Language.English, S(r, "activateTextOverride")),
        };
        if (r.TryGetProperty("keywords", out var kws))
        {
            a.Keywords = new Noggog.ExtendedList<IFormLinkGetter<IKeywordGetter>>();
            foreach (var k in kws.EnumerateArray()) a.Keywords.Add(new FormLink<IKeywordGetter>(FK(k.GetString()!)));
        }
        mod.Activators.Add(a);
    }

    static void Setting(SkyrimMod mod, JsonElement r)
    {
        var key = FK(S(r, "formKey"));
        var edid = S(r, "edid");
        var v = r.GetProperty("value");
        switch (S(r, "kind"))
        {
            case "float": mod.GameSettings.Add(new GameSettingFloat(key, Rel) { EditorID = edid, Data = v.GetSingle() }); break;
            case "int": mod.GameSettings.Add(new GameSettingInt(key, Rel) { EditorID = edid, Data = v.GetInt32() }); break;
            case "bool": mod.GameSettings.Add(new GameSettingBool(key, Rel) { EditorID = edid, Data = v.GetInt32() != 0 }); break;
            default: throw new InvalidDataException($"{edid}: game setting kind {S(r, "kind")}");
        }
    }
}
