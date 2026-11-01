// TXST: the ground's texture sets (1.15 materials). Our vanilla-named LTEX are re-pointed at Black Marsh & Valenwood's
// landscape pack (textures\TEXTUREPACK\landscape\, laid by the player's own BM&V download): one new TXST per LTEX,
// every field resolved by Python (terrain/texture_sets.py); the LTEX override's textureSet names it.
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;

namespace ArgoniaGen;

static class TextureSets
{
    static string S(JsonElement e, string k) => e.GetProperty(k).GetString() ?? throw new InvalidDataException($"{k} is null");

    public static void Write(SkyrimMod mod, JsonElement r)
    {
        var t = new TextureSet(FormKey.Factory(S(r, "formKey")), SkyrimRelease.SkyrimSE)
        {
            EditorID = S(r, "edid"),
            Diffuse = S(r, "diffuse"),
        };
        if (r.TryGetProperty("normal", out var n) && n.ValueKind == JsonValueKind.String) t.NormalOrGloss = n.GetString();
        mod.TextureSets.Add(t);
    }
}
