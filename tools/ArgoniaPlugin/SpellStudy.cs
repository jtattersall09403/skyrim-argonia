using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;

// spells <plugins in load order...>: what a quest could teach or hand over, counted from the load order's winners
// (docs/research/skyrim/outcome-kinds.md). Prints counts and editor ids only ("section<TAB>key<TAB>count"); no game
// text is read (strings are never loaded) and nothing is written (decision 0003).
static class SpellStudy
{
    public static int Run(string[] paths)
    {
        var mods = Survey.Load(paths);
        var counts = new SortedDictionary<string, int>();
        void Add(string k) => counts[k] = counts.GetValueOrDefault(k) + 1;

        var books = Survey.Winners<IBookGetter>(mods);
        var taught = books.Values.Select(b => b.rec.Teaches).OfType<IBookSpellGetter>().Select(t => t.Spell.FormKey).ToHashSet();
        var given = new HashSet<FormKey>();
        foreach (var (_, (n, _)) in Survey.Winners<INpcGetter>(mods))
            foreach (var s in n.ActorEffect ?? []) given.Add(s.FormKey);
        foreach (var (fk, (s, from)) in Survey.Winners<ISpellGetter>(mods))
        {
            var src = fk.ModKey.FileName.String;
            var how = taught.Contains(fk) ? "tome" : "notome";
            Add($"spell\t{src}\t{s.Type}\t{how}");
            // a power or ability no tome teaches and no person carries: a quest's or a stone's gift
            if (s.Type is SpellType.Power or SpellType.LesserPower or SpellType.Ability && !taught.Contains(fk) && !given.Contains(fk)
                && src is "Magic.esp" or "Skyrim.esm" or "Dawnguard.esm" or "Dragonborn.esm")
                Add($"gift\t{src}\t{s.Type}\t{s.EditorID}");
        }
        foreach (var (fk, (a, _)) in Survey.Winners<IArmorGetter>(mods))
            if (!a.ObjectEffect.IsNull && a.TemplateArmor.IsNull) Add($"enchanted\t{fk.ModKey.FileName}\tarmor");
        foreach (var (fk, (w, _)) in Survey.Winners<IWeaponGetter>(mods))
            if (!w.ObjectEffect.IsNull && w.Template.IsNull) Add($"enchanted\t{fk.ModKey.FileName}\tweapon");
        foreach (var (fk, (p, _)) in Survey.Winners<IPerkGetter>(mods)) Add($"perk\t{fk.ModKey.FileName}\t{(p.Playable ? "playable" : "hidden")}");
        // recipes: what gates a constructible object (its workbench and the functions of its conditions)
        var kw = Survey.Winners<IKeywordGetter>(mods);
        foreach (var (fk, (o, _)) in Survey.Winners<IConstructibleObjectGetter>(mods))
        {
            var bench = kw.TryGetValue(o.WorkbenchKeyword.FormKey, out var b) ? b.rec.EditorID : "none";
            var fns = o.Conditions.Select(c => c.Data.GetType().Name.Replace("ConditionData", "")).Distinct().OrderBy(x => x).ToList();
            Add($"recipe\t{fk.ModKey.FileName}\t{bench}\t{(fns.Count == 0 ? "ungated" : string.Join("+", fns))}");
        }
        foreach (var (k, n) in counts) Console.WriteLine($"{k}\t{n}");
        return 0;
    }
}
