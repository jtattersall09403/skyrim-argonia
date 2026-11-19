using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;

// Items of ours that a place's stock gives by editor id (newworld/sources/stock; place-stock skill). Called by Generate
// after the quests and Talk, so no earlier form id moves.
static class Items
{
    public const string VoshLeerasRing = "ANW_VoshLeerasRing", VoshLeerasRingEnch = "ANW_VoshLeerasRingEnch";
    const float VoshLeerasMagnitude = 15f;

    public static void Add(SkyrimMod mod, List<ISkyrimModGetter> mods)
    {
        // Vosh-Leera's Ring: Skyrim's Ring of Minor Health (EnchRingHealth01, whose Fortify Health is 20) with its own
        // enchantment, a copy of the vanilla one at 15, so the vanilla ring's enchantment is untouched.
        var ring = Survey.Winners<IArmorGetter>(mods)[FormKey.Factory("0FCEFD:Skyrim.esm")].rec;
        var ench = (ObjectEffect)Survey.Winners<IObjectEffectGetter>(mods)[ring.ObjectEffect.FormKey].rec.Duplicate(mod.GetNextFormKey());
        ench.EditorID = VoshLeerasRingEnch;
        foreach (var e in ench.Effects) e.Data!.Magnitude = VoshLeerasMagnitude;
        mod.ObjectEffects.Add(ench);
        var armo = (Armor)ring.Duplicate(mod.GetNextFormKey());
        armo.EditorID = VoshLeerasRing;
        armo.Name = "Vosh-Leera's Ring";
        armo.ObjectEffect.SetTo(ench.FormKey);
        mod.Armors.Add(armo);
    }
}
