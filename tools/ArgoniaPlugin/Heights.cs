using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;

// People at their race's height (W-npc; owner walk 4, 2026-11-08: Mee-Tuja stood about 12 feet tall). A base of ours
// templated with Use Traits draws its template's height, and two of BM&V's Argonian bases are 1.9 (ArgonianMaleTribeLeader
// 02A1E6 'Flaa Heet' and ArgonianMaleTribeLeader1 1DE49D). Every placed person of ours (a playable race) whose drawn height
// is off 1 by 0.1 or more is scaled on the ref to stand at 1 (children, below 1, are left). After every builder.
static class Heights
{
    public static int Fix(SkyrimMod mod, List<ISkyrimModGetter> mods)
    {
        var npcs = Survey.Winners<INpcGetter>(mods);
        foreach (var n in mod.Npcs) npcs[n.FormKey] = (n, mod.ModKey);
        var races = Survey.Winners<IRaceGetter>(mods);
        float H(INpcGetter n, int d = 0) => d < 8 && n.Configuration.TemplateFlags.HasFlag(NpcConfiguration.TemplateFlag.Traits)
            && npcs.TryGetValue(n.Template.FormKey, out var t) ? H(t.rec, d + 1) : n.Height;
        var fixedN = 0;
        foreach (var r in mod.EnumerateMajorRecords<PlacedNpc>())
        {
            if (!npcs.TryGetValue(r.Base.FormKey, out var b)) continue;
            var h = H(b.rec);
            if (h < 1.1f || !races.TryGetValue(b.rec.Race.FormKey, out var race) || !race.rec.Flags.HasFlag(Race.Flag.Playable)) continue;
            r.Scale = MathF.Round(1 / h, 3);
            fixedN++;
            Console.WriteLine($"heights: {r.EditorID ?? r.FormKey.ToString()} ({b.rec.EditorID}) drawn {h}, scale {r.Scale}");
        }
        return fixedN;
    }
}
