// LSCR: the intermediate's loading screens (tools/argonia_world/intermediate.py) -> Mutagen. An override keeps the
// master's FormKey and EditorID and carries only a never-true condition, so the engine never picks it (0012); ours
// carry the tip text and no model unless one is named.
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;
using Noggog;

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
        {
            l.LoadingScreenNif.SetTo(FormKey.Factory(m.GetString()!));
            // Skyrim's classic layout (owner, 2026-10-31): the model's initial scale, rotation (degrees), the range
            // the player may turn it, and its translation, from data/loading-screens.json.
            if (r.TryGetProperty("scale", out var sc)) l.InitialScale = sc.GetSingle();
            if (r.TryGetProperty("rotation", out var ro))
                l.InitialRotation = new P3Int16(ro[0].GetInt16(), ro[1].GetInt16(), ro[2].GetInt16());
            if (r.TryGetProperty("rotationRange", out var rr))
                l.RotationOffsetConstraints = new Int16MinMax { Min = rr[0].GetInt16(), Max = rr[1].GetInt16() };
            if (r.TryGetProperty("translation", out var tr))
                l.InitialTranslationOffset = new P3Float(tr[0].GetSingle(), tr[1].GetSingle(), tr[2].GetSingle());
        }
        if (r.TryGetProperty("conditions", out var cs))
            foreach (var c in cs.EnumerateArray()) l.Conditions.Add(QuestRecords.Condition(c));
        mod.LoadScreens.Add(l);
    }
}
