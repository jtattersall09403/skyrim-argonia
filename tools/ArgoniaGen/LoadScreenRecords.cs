// LSCR: the intermediate's loading screens (tools/argonia_world/intermediate.py) -> Mutagen. An override keeps the
// master's FormKey and EditorID and carries only a never-true condition, so the engine never picks it (0012); ours
// carry the tip text and no model unless one is named.
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;

namespace ArgoniaGen;

static class LoadScreenRecords
{
    const SkyrimRelease Rel = SkyrimRelease.SkyrimSE;

    static string S(JsonElement e, string k) => e.GetProperty(k).GetString() ?? throw new InvalidDataException($"{k} is null");

    public static void Write(SkyrimMod mod, JsonElement r)
    {
        var l = new LoadScreen(FormKey.Factory(S(r, "formKey")), Rel)
        {
            EditorID = S(r, "edid"),
            Description = new TranslatedString(Language.English, r.TryGetProperty("text", out var t) ? t.GetString() ?? "" : ""),
        };
        if (r.TryGetProperty("model", out var m) && m.ValueKind == JsonValueKind.String)
            l.LoadingScreenNif.SetTo(FormKey.Factory(m.GetString()!));
        if (r.TryGetProperty("conditions", out var cs))
            foreach (var c in cs.EnumerateArray()) l.Conditions.Add(QuestRecords.Condition(c));
        mod.LoadScreens.Add(l);
    }
}
