using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;

// World fixes: overrides of BM&V's world that keep form ids and add no art (decision 0006). Each fix copies the load
// order's winner and changes one field.
//
// Window panes (owner walk 2026-11-07, Lilmoth docks): BM&V ships loose copies of vanilla Solitude, Whiterun and
// Riften building meshes edited for Enhanced Lighting (ELFX) at the vanilla paths, so they shadow the vanilla meshes;
// their window shapes name textures\effects\ELFX\windows\... and the cubemap textures\effects\ELFX\cubemaps\tundra_e.dds,
// which no archive or loose file in the staged load order holds, so the panes draw flat pale blue. BM&V also ships
// "gkb" copies of three of those houses that name only vanilla textures (SWindow01/_g, all present); the STAT's model
// moves to that copy. (docs/phases/1-stack-in-bmv.md, BM&V texture gap.)
static class WorldFix
{
    static readonly (string key, string model)[] Models =
    {
        ("037F0E:Skyrim.esm", @"Architecture\Solitude\SBryling HouseGKB.nif"),   // SBrylingHouse, 2 refs in Lilmoth
        ("037F05:Skyrim.esm", @"Architecture\Solitude\SStyrrsHouseGKB.nif"),     // SStyrrsHouse, 2 refs in Lilmoth
        ("037F0F:Skyrim.esm", @"Architecture\Solitude\SHouseForSaleGKB.nif"),    // SHouseForSale, 1 ref in Lilmoth
    };

    public static void Add(SkyrimMod mod, List<ISkyrimModGetter> mods)
    {
        var stats = Survey.Winners<IStaticGetter>(mods);
        foreach (var (key, model) in Models)
        {
            var s = (Static)stats[FormKey.Factory(key)].rec.DeepCopy();
            s.Model ??= new Model();
            s.Model.File.GivenPath = model;
            s.Model.Data = null;  // the old mesh's texture hashes (MODT) would name the ELFX files

            mod.Statics.Add(s);
        }
    }
}
