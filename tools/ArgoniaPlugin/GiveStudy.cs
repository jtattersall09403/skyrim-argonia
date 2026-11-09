using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;

// gives <plugins in load order...>: what Skyrim's places give the player, counted from the load order's winners
// (docs/research/new-world-place-gives.md). Prints aggregate counts only ("section<TAB>key<TAB>count"); no game text
// is read (strings are never loaded) and nothing is written (decision 0003).
static class GiveStudy
{
    static readonly Dictionary<(string, string), int> Counts = new();
    static void Add(string section, string key, int n = 1) =>
        Counts[(section, key)] = Counts.GetValueOrDefault((section, key)) + n;

    public static void Run(string[] paths)
    {
        var mods = Survey.Load(paths);
        var eid = new Dictionary<FormKey, string>();
        foreach (var m in mods) foreach (var r in m.EnumerateMajorRecords())
            if (r is not IPlacedGetter && r is not ICellGetter && r is not INavigationMeshGetter && r.EditorID is { } e) eid[r.FormKey] = e;
        string E(FormKey k) => eid.GetValueOrDefault(k) ?? k.ToString();

        var kw = Survey.Winners<IKeywordGetter>(mods);
        var furn = Survey.Winners<IFurnitureGetter>(mods);
        var acti = Survey.Winners<IActivatorGetter>(mods);
        var flora = Survey.Winners<IFloraGetter>(mods);
        var tree = Survey.Winners<ITreeGetter>(mods);
        var cont = Survey.Winners<IContainerGetter>(mods);
        var lvli = Survey.Winners<ILeveledItemGetter>(mods);
        var loc = Survey.Winners<ILocationGetter>(mods);
        var ecz = Survey.Winners<IEncounterZoneGetter>(mods);
        var npcs = Survey.Winners<INpcGetter>(mods);
        var cls = Survey.Winners<IClassGetter>(mods);
        var fac = Survey.Winners<IFactionGetter>(mods);
        var flst = Survey.Winners<IFormListGetter>(mods);
        var books = Survey.Winners<IBookGetter>(mods);
        var spells = Survey.Winners<ISpellGetter>(mods);
        var mgef = Survey.Winners<IMagicEffectGetter>(mods);

        // cells and their placed refs (the winner of each)
        var cells = new Dictionary<FormKey, (ICellGetter c, bool interior)>();
        var refs = new Dictionary<FormKey, (IPlacedObjectGetter r, FormKey cell)>();
        foreach (var m in mods)
        {
            void Cell(ICellGetter c, bool interior)
            {
                cells[c.FormKey] = (c, interior);
                foreach (var r in c.Temporary.Concat(c.Persistent)) if (r is IPlacedObjectGetter po) refs[po.FormKey] = (po, c.FormKey);
            }
            foreach (var b in m.Cells.Records) foreach (var sb in b.SubBlocks) foreach (var c in sb.Cells) Cell(c, true);
            foreach (var w in m.Worldspaces)
            {
                if (w.TopCell is { } top) Cell(top, false);
                foreach (var b in w.SubCells) foreach (var sb in b.Items) foreach (var c in sb.Items) Cell(c, false);
            }
        }
        // a cell's location: its own, else (exterior) none
        string LocType(FormKey cell)
        {
            if (!cells.TryGetValue(cell, out var c) || c.c.Location.IsNull || !loc.TryGetValue(c.c.Location.FormKey, out var l)) return "none";
            var types = (l.rec.Keywords ?? []).Select(k => E(k.FormKey)).Where(s => s.StartsWith("LocType")).ToList();
            var pick = new[] { "LocTypeDragonPriestLair", "LocTypeDraugrCrypt", "LocTypeDwarvenAutomatons", "LocTypeFalmerHive",
                "LocTypeVampireLair", "LocTypeWarlockLair", "LocTypeForswornCamp", "LocTypeBanditCamp", "LocTypeGiantCamp",
                "LocTypeDragonLair", "LocTypeAnimalDen", "LocTypeSprigganGrove", "LocTypeHagravenNest", "LocTypeMilitaryFort",
                "LocTypeShipwreck", "LocTypeMine", "LocTypeInn", "LocTypeStore", "LocTypePlayerHouse", "LocTypeTemple",
                "LocTypeCastle", "LocTypeJail", "LocTypeHouse", "LocTypeCity", "LocTypeTown", "LocTypeSettlement",
                "LocTypeDungeon", "LocTypeClearable" };
            return pick.FirstOrDefault(types.Contains) ?? (types.FirstOrDefault() ?? "untyped");
        }
        int? ZoneMin(FormKey cell, out string zflags)
        {
            zflags = "";
            if (!cells.TryGetValue(cell, out var c)) return null;
            var zk = c.c.EncounterZone.FormKey;
            if (c.c.EncounterZone.IsNull || !ecz.TryGetValue(zk, out var z)) return null;
            zflags = $"{z.rec.MinLevel}-{z.rec.MaxLevel}";
            return z.rec.MinLevel;
        }

        // 1 map markers by type, and by the location type of the cell they stand in
        foreach (var (_, (r, cell)) in refs)
            if (r.MapMarker is { } mm) { Add("mapmarker.type", mm.Type.ToString()); Add("mapmarker.total", "all"); }

        // 2 vendors: faction -> buy/sell keyword list
        foreach (var (_, (f, _)) in fac)
        {
            if (!f.Flags.HasFlag(Faction.FactionFlag.Vendor)) continue;
            var list = f.VendorBuySellList.IsNull || !flst.TryGetValue(f.VendorBuySellList.FormKey, out var fl) ? "(none)"
                : string.Join(",", fl.rec.Items.Select(i => E(i.FormKey)).Select(s => s.Replace("VendorItem", "")).OrderBy(s => s));
            var v = f.VendorValues;
            var mode = v == null ? "" : (v.NotSellBuy ? "buys-all-but-list" : "buys-list") + (v.OnlyBuysStolenItems ? "+stolen-only" : "");
            var members = npcs.Values.Count(n => n.rec.Factions.Any(x => x.Faction.FormKey == f.FormKey));
            Add("vendor.faction", $"{f.EditorID}\t{mode}\t{list}", members);
        }
        // spell tomes by school
        foreach (var (_, (b, _)) in books)
            if (b.Teaches is IBookSpellGetter bs && spells.TryGetValue(bs.Spell.FormKey, out var sp))
            {
                var fx = sp.rec.Effects.FirstOrDefault();
                var school = fx != null && mgef.TryGetValue(fx.BaseEffect.FormKey, out var me) ? me.rec.MagicSkill.ToString() : "?";
                var lvl = sp.rec.HalfCostPerk.IsNull ? "?" : E(sp.rec.HalfCostPerk.FormKey);
                Add("spelltome.school", school); Add("spelltome.tier", lvl.Replace("Cost", ""));
            }
            else if (b.Teaches is IBookSkillGetter sk && sk.Skill is { } s) Add("skillbook.skill", s.ToString());

        // 3 crafting furniture by keyword: base forms and placed refs
        string[] Craft(IFurnitureGetter f) => (f.Keywords ?? []).Select(k => E(k.FormKey))
            .Where(s => s.Contains("Craft") || s.Contains("Cook") || s.Contains("Enchant") || s.Contains("Alchemy") || s.Contains("Oven")
                        || s.Contains("Staff") || s.Contains("Sharpen") || s.Contains("Smelter") || s.Contains("Tanning") || s.Contains("isBed") || s.Contains("Bed")).ToArray();
        string? Sleep(IFurnitureGetter f) => f.EditorID is { } e && (e.Contains("Bed") || e.Contains("bedroll", StringComparison.OrdinalIgnoreCase)) && !e.Contains("Marker") ? (e.Contains("Child") ? "bed-child" : e.Contains("Roll", StringComparison.OrdinalIgnoreCase) ? "bedroll" : "bed") : null;
        foreach (var (_, (r, cell)) in refs)
        {
            var bk = r.Base.FormKey;
            if (furn.TryGetValue(bk, out var f))
            {
                foreach (var k in Craft(f.rec)) { Add("craft.placed", k); Add("craft.placed.where", $"{k}\t{LocType(cell)}"); }
                if (Sleep(f.rec) is { } s) { Add("sleep.placed", s); if (s == "bed") Add("bed.where", LocType(cell)); }
            }
            if (acti.TryGetValue(bk, out var a))
            {
                foreach (var sc in a.rec.VirtualMachineAdapter?.Scripts ?? [])
                {
                    var n = sc.Name;
                    if (n.Equals("MineOreScript", StringComparison.OrdinalIgnoreCase))
                    {
                        var ore = sc.Properties.OfType<IScriptObjectPropertyGetter>().FirstOrDefault(p => p.Name.Equals("ore", StringComparison.OrdinalIgnoreCase));
                        Add("ore.placed", ore == null ? "?" : E(ore.Object.FormKey));
                    }
                    else if (n.Contains("Blessing", StringComparison.OrdinalIgnoreCase) || n.Contains("StandingStone", StringComparison.OrdinalIgnoreCase)
                             || n.Contains("WordWall", StringComparison.OrdinalIgnoreCase) || n.Contains("Shrine", StringComparison.OrdinalIgnoreCase)
                             || n.Contains("AtronachForge", StringComparison.OrdinalIgnoreCase) || n.Contains("BlackStar", StringComparison.OrdinalIgnoreCase))
                    {
                        var spell = sc.Properties.OfType<IScriptObjectPropertyGetter>().FirstOrDefault(p => p.Name.Contains("Blessing") || p.Name.Contains("Spell") || p.Name.Contains("Power"));
                        Add("script.placed", $"{n}\t{(spell == null ? "" : E(spell.Object.FormKey))}");
                    }
                }
                if (a.rec.EditorID is { } ae && (ae.Contains("WordWall") || ae.Contains("doomstone", StringComparison.OrdinalIgnoreCase) || ae.Contains("StandingStone")))
                    Add("acti.placed", ae);
            }
            if (flora.TryGetValue(bk, out var fl2) && !fl2.rec.Ingredient.IsNull) Add("harvest.placed", $"{E(fl2.rec.Ingredient.FormKey)}");
            if (tree.TryGetValue(bk, out var tr) && !tr.rec.Ingredient.IsNull) Add("harvest.placed", $"{E(tr.rec.Ingredient.FormKey)}");
            if (cont.TryGetValue(bk, out var c) && c.rec.EditorID is { } ce)
            {
                var boss = ce.Contains("Boss", StringComparison.OrdinalIgnoreCase);
                if (boss)
                {
                    var lt = LocType(cell); var zm = ZoneMin(cell, out var zr);
                    Add("bosschest.placed", ce); Add("bosschest.where", lt);
                    Add("bosschest.zonemin", zm == null ? "nozone" : zm.Value.ToString());
                }
                else if (ce.StartsWith("Treas")) Add("chest.placed", "non-boss Treas*");
            }
        }
        // boss chest contents: their levelled lists and the levels inside them
        foreach (var (_, (c, _)) in cont)
            if (c.EditorID is { } ce && ce.Contains("Boss", StringComparison.OrdinalIgnoreCase))
                foreach (var it in c.Items ?? [])
                {
                    var ik = it.Item.Item.FormKey;
                    var detail = lvli.TryGetValue(ik, out var l)
                        ? $"LVLI levels {string.Join("/", (l.rec.Entries?.Select(e => (int)(e.Data?.Level ?? 0)) ?? Enumerable.Empty<int>()).Distinct().OrderBy(x => x))} flags {l.rec.Flags}"
                        : "fixed item";
                    Add("bosschest.content", $"{ce}\t{E(ik)} x{it.Item.Count}\t{detail}");
                }

        // the material ladder Bethesda's levelled lists climb (level -> item)
        foreach (var (_, (l, _)) in lvli)
            if (l.EditorID is "LItemWeaponSwordBest" or "LItemArmorCuirassHeavyBest" or "LItemArmorCuirassLightBest" or "LootDraugrGoldBoss01" or "LootBanditGold")
                foreach (var e in l.Entries ?? [])
                    if (e.Data is { } d) Add("ladder", $"{l.EditorID}\t{d.Level}\t{E(d.Reference.FormKey)} x{d.Count}");
        // 4 trainers: unique NPCs whose class teaches, by skill and cap
        foreach (var (_, (n, _)) in npcs)
            if (!n.Class.IsNull && cls.TryGetValue(n.Class.FormKey, out var c) && c.rec.MaxTrainingLevel > 0)
            {
                var tier = c.rec.MaxTrainingLevel switch { <= 50 => "Journeyman", <= 75 => "Expert", _ => "Master" };
                Add("trainer", $"{c.rec.Teaches}\t{tier}({c.rec.MaxTrainingLevel})");
                Add("trainer.tier", tier);
            }
        // trainers as the game finds them: the JobTrainer<Skill>Faction members (the class sets the cap)
        foreach (var (_, (n, _)) in npcs)
            foreach (var x in n.Factions.Select(x => E(x.Faction.FormKey)).Where(s => s.StartsWith("JobTrainer") && s != "JobTrainerFaction"))
            {
                var cap = !n.Class.IsNull && cls.TryGetValue(n.Class.FormKey, out var c2) ? c2.rec.MaxTrainingLevel : 0;
                var tier = cap switch { 0 => "?", <= 50 => "Journeyman", <= 75 => "Expert", _ => "Master" };
                Add("trainer.faction", $"{x.Replace("JobTrainer", "").Replace("Faction", "")}\t{tier}");
            }
        // followers, housing
        foreach (var (_, (n, _)) in npcs)
            if (n.Factions.Any(x => E(x.Faction.FormKey) == "PotentialFollowerFaction")) Add("follower", "PotentialFollowerFaction");
        foreach (var (_, (l, _)) in loc)
            foreach (var k in (l.Keywords ?? []).Select(k => E(k.FormKey)).Where(s => s.StartsWith("LocType"))) Add("location.type", k);

        // 5 encounter zones: level ranges and flags
        foreach (var (_, (z, _)) in ecz)
        {
            var fixedz = z.MaxLevel != 0 && z.MaxLevel == z.MinLevel ? "fixed" : z.MaxLevel == 0 ? "open-top" : "capped";
            Add("zone.kind", fixedz); Add("zone.min", z.MinLevel.ToString());
            Add("zone.flags", z.Flags.ToString());
        }
        foreach (var (_, (_, _)) in Survey.Winners<IShoutGetter>(mods)) Add("shout", "SHOU");
        foreach (var (_, (_, _)) in Survey.Winners<IWordOfPowerGetter>(mods)) Add("shout", "WOOP");

        foreach (var ((s, k), n) in Counts.OrderBy(x => x.Key.Item1).ThenByDescending(x => x.Value))
            Console.WriteLine($"{s}\t{k}\t{n}");
    }
}
