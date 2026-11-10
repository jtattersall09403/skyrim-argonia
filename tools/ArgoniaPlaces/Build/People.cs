// People: the plan's actor bases, placed actors, packages, factions and services (tools/places/people.py says how
// and why each is built the way Skyrim.esm's towns do it). Nothing levelled reaches the plugin: an actor base gets a
// fixed level, and every levelled list in its inventory, its outfit or a merchant chest is flattened to fixed items.
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Cache;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;
using Noggog;

static class People
{
    static ILinkCache? cache;
    static ILinkCache Cache => cache ??= C.Cache(Write.Masters);

    static P3Float P(JsonElement e) => new((float)e[0].GetDouble(), (float)e[1].GetDouble(), (float)e[2].GetDouble());
    static string? S(JsonElement e, string k) => e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() : null;

    static T Resolve<T>(Write.Ctx ctx, string key) where T : class, IMajorRecordGetter
    {
        var fk = C.Fk(key);
        if (fk.ModKey == ctx.Mod.ModKey) throw new InvalidDataException($"{key} is ours: not a source");
        if (Cache.TryResolve<T>(fk, out var r)) return r;
        return (T)ctx.Fc.Plugin(fk.ModKey.FileName).EnumerateMajorRecords<T>().First(x => x.FormKey == fk);
    }

    public static void Build(Write.Ctx ctx, string pid, JsonElement people, Dictionary<string, PlacedObject> refs, Dictionary<string, Cell> interiors)
    {
        var mod = ctx.Mod;
        var cf = people.GetProperty("crime_faction");
        var crime = new Faction(C.Fk(cf.GetProperty("fk").GetString()!), C.Rel)
        {
            EditorID = cf.GetProperty("edid").GetString(),
            Name = new TranslatedString(Language.English, cf.GetProperty("name").GetString()),
            Flags = Faction.FactionFlag.TrackCrime,
            CrimeValues = new CrimeValues { Arrest = true, AttackOnSight = true, Murder = 1000, Assault = 40, Trespass = 5, Pickpocket = 25, StealMult = 1f, Escape = 100, Werewolf = 1000 },
        };
        mod.Factions.Add(crime);

        // the merchant chests' cell: an interior no door reaches (vanilla keeps them in such cells or under floors)
        Cell? chests = null;
        if (people.TryGetProperty("chest_cell", out var cc) && cc.ValueKind == JsonValueKind.Object)
        {
            chests = new Cell(C.Fk(cc.GetProperty("fk").GetString()!), C.Rel) { EditorID = cc.GetProperty("edid").GetString(), Flags = Cell.Flag.IsInteriorCell };
            chests.LightingTemplate.SetTo(C.Fk(cc.GetProperty("light").GetString()!));
            Write.AddInterior(mod, chests);
        }
        foreach (var c in people.GetProperty("containers").EnumerateArray())
        {
            var src = Resolve<IContainerGetter>(ctx, c.GetProperty("from").GetString()!);
            var o = (Container)src.Duplicate(C.Fk(c.GetProperty("fk").GetString()!));
            o.EditorID = c.GetProperty("edid").GetString();
            o.VirtualMachineAdapter = null;
            o.Flags |= Container.Flag.Respawns;  // a merchant's stock restocks, as vanilla merchant chests do
            Flatten(ctx, o.Items);
            ctx.Localize(o);
            mod.Containers.Add(o);
        }
        // markers: XMarkerHeadings at routine stops, patrol chains, merchant chests
        foreach (var m in people.GetProperty("markers").EnumerateArray())
        {
            var o = new PlacedObject(C.Fk(m.GetProperty("fk").GetString()!), C.Rel) { MajorRecordFlagsRaw = 0x400 };
            o.Base.SetTo(ctx.Link(m.GetProperty("base").GetString()!));
            o.Placement = new Placement { Position = P(m.GetProperty("pos")), Rotation = P(m.GetProperty("rot")) };
            if (m.TryGetProperty("linked", out var ln))
                foreach (var l in ln.EnumerateArray()) { var lr = new LinkedReferences(); lr.Reference.SetTo(C.Fk(l.GetProperty("ref").GetString()!)); o.LinkedReferences.Add(lr); }
            refs[C.Key(o.FormKey)] = o;
            var space = m.GetProperty("space").GetString()!;
            if (space == "__chests__") chests!.Persistent.Add(o);
            else if (space == "exterior") ((Worldspace)mod.Worldspaces.First()).TopCell!.Persistent.Add(o);
            else interiors[space].Persistent.Add(o);
        }
        foreach (var f in people.GetProperty("factions").EnumerateArray())
        {
            var fa = new Faction(C.Fk(f.GetProperty("fk").GetString()!), C.Rel)
            {
                EditorID = f.GetProperty("edid").GetString(),
                Name = new TranslatedString(Language.English, f.GetProperty("name").GetString()),
            };
            if (f.TryGetProperty("vendor", out var v))
            {
                fa.Flags |= Faction.FactionFlag.Vendor;
                fa.VendorValues = new VendorValues
                {
                    StartHour = (ushort)v.GetProperty("start").GetInt32(), EndHour = (ushort)v.GetProperty("end").GetInt32(), Radius = 0,
                    OnlyBuysStolenItems = v.GetProperty("stolen_only").GetBoolean(), NotSellBuy = false,
                };
                fa.VendorBuySellList.SetTo(C.Fk(v.GetProperty("list").GetString()!));
                fa.MerchantContainer.SetTo(C.Fk(v.GetProperty("chest").GetString()!));
            }
            mod.Factions.Add(fa);
        }
        // packages: copies of the vanilla templated package of each kind, our schedule and place
        foreach (var p in people.GetProperty("packages").EnumerateArray())
        {
            var src = Resolve<IPackageGetter>(ctx, p.GetProperty("from").GetString()!);
            var k = (Package)src.Duplicate(C.Fk(p.GetProperty("fk").GetString()!));
            k.EditorID = p.GetProperty("edid").GetString();
            k.OwnerQuest.Clear(); k.Conditions.Clear();
            k.ScheduleHour = (sbyte)p.GetProperty("hour").GetInt32();
            k.ScheduleDurationInMinutes = p.GetProperty("minutes").GetInt32();
            var kind = p.GetProperty("kind").GetString();
            if (p.TryGetProperty("location", out var loc))
            {
                var at = C.Fk(loc.GetProperty("ref").GetString()!);
                var target = new LocationTarget(); target.Link.SetTo(at);
                foreach (var d in k.Data.Values.OfType<PackageDataLocation>().Take(1))
                    d.Location = new LocationTargetRadius { Target = target, Radius = (uint)loc.GetProperty("radius").GetInt32() };
                if (kind == "sleep")  // the bed: the Sleep template's specific-reference target
                    foreach (var d in k.Data.Values.OfType<PackageDataTarget>())
                        if (d.Target is PackageTargetSpecificReference sr) sr.Reference.SetTo(at);
            }
            if (p.TryGetProperty("target_linked", out var tl) && tl.GetBoolean())  // vanilla patrols: the actor's own linked ref, no keyword
                foreach (var d in k.Data.Values.OfType<PackageDataTarget>().Take(1))
                    d.Target = new PackageTargetLinkedReference();
            else if (S(p, "target") is { } tgt)
                foreach (var d in k.Data.Values.OfType<PackageDataTarget>().Take(1))
                {
                    var sr = new PackageTargetSpecificReference(); sr.Reference.SetTo(C.Fk(tgt));
                    d.Target = sr;
                }
            // nothing of the vanilla town may remain: no link to a vanilla placed ref or cell
            var stale = k.EnumerateFormLinks().Where(l => l.FormKey.ModKey != mod.ModKey && (l.Type == typeof(IPlacedGetter) || l.Type == typeof(ICellGetter) || l.Type == typeof(IPlacedObjectGetter))).ToList();
            if (stale.Count > 0) throw new InvalidDataException($"package {k.EditorID} still links {string.Join(", ", stale.Select(l => C.Key(l.FormKey)))}");
            mod.Packages.Add(k);
        }
        var classes = new Dictionary<string, JsonElement>();
        foreach (var c in people.GetProperty("classes").EnumerateArray()) classes[c.GetProperty("fk").GetString()!] = c;
        // actor bases
        foreach (var n in people.GetProperty("npcs").EnumerateArray())
        {
            var src = Resolve<INpcGetter>(ctx, n.GetProperty("from").GetString()!);
            if (!src.Template.IsNull && Cache.TryResolve<ILeveledNpcGetter>(src.Template.FormKey, out _))
                throw new InvalidDataException($"{n.GetProperty("id")}: base_from {C.Key(src.FormKey)} is templated on a levelled list (decision 0035)");
            var o = (Npc)src.Duplicate(C.Fk(n.GetProperty("fk").GetString()!));
            o.EditorID = n.GetProperty("edid").GetString();
            o.Name = new TranslatedString(Language.English, n.GetProperty("name").GetString());
            o.VirtualMachineAdapter = n.TryGetProperty("scripts", out var scs) && scs.GetArrayLength() > 0 ? C.Vmad(scs) : null;
            if (S(n, "voice") is { } vk) o.Voice.SetTo(C.Fk(vk));
            else if (S(n, "voice_list") is { } vl) o.Voice.SetTo(RentVoice(src, C.Fk(vl)));
            o.Configuration.Flags |= NpcConfiguration.Flag.Unique;
            o.Configuration.Level = new NpcLevel { Level = (short)n.GetProperty("level").GetInt32() };
            o.Packages.Clear();
            foreach (var pk in n.GetProperty("packages").EnumerateArray()) o.Packages.Add(new FormLink<IPackageGetter>(C.Fk(pk.GetString()!)));
            o.Factions.Clear();
            foreach (var f in n.GetProperty("factions").EnumerateArray())
                o.Factions.Add(new RankPlacement { Faction = new FormLink<IFactionGetter>(ctx.Link(f.GetProperty("faction").GetString()!)), Rank = (sbyte)f.GetProperty("rank").GetInt32() });
            o.CrimeFaction.SetTo(crime.FormKey);
            if (S(n, "class") is { } ck)
            {
                var c = classes[ck];
                var baseClass = Resolve<IClassGetter>(ctx, C.Key(src.Class.FormKey));
                var cl = (Class)baseClass.Duplicate(C.Fk(ck));
                cl.EditorID = c.GetProperty("edid").GetString();
                cl.Teaches = Enum.Parse<Skill>(c.GetProperty("teaches").GetString()!);
                cl.MaxTrainingLevel = (byte)c.GetProperty("max_level").GetInt32();
                mod.Classes.Add(cl);
                o.Class.SetTo(cl.FormKey);
            }
            if (o.Items != null) Flatten(ctx, o.Items);
            if (!o.DefaultOutfit.IsNull && Cache.TryResolve<IOutfitGetter>(o.DefaultOutfit.FormKey, out var outfit)
                && outfit.Items?.Any(i => Cache.TryResolve<ILeveledItemGetter>(i.FormKey, out var li) && Levelled(li)) == true)
            {
                var ot = (Outfit)outfit.Duplicate(new FormKey(mod.ModKey, ctx.Fc.NextIdTake()));
                ot.EditorID = $"{o.EditorID}_Outfit";
                var items = new ExtendedList<IFormLinkGetter<IOutfitTargetGetter>>();
                foreach (var i in outfit.Items!)
                    if (Cache.TryResolve<ILeveledItemGetter>(i.FormKey, out var li)) foreach (var f in Fixed(li)) items.Add(new FormLink<IOutfitTargetGetter>(f));
                    else items.Add(i);
                ot.Items = items;
                mod.Outfits.Add(ot);
                o.DefaultOutfit.SetTo(ot.FormKey);
            }
            ctx.Localize(o);
            mod.Npcs.Add(o);
        }
        // placed actors: persistent, as vanilla files town people
        foreach (var a in people.GetProperty("actors").EnumerateArray())
        {
            var o = new PlacedNpc(C.Fk(a.GetProperty("fk").GetString()!), C.Rel) { MajorRecordFlagsRaw = 0x400 };
            o.Base.SetTo(C.Fk(a.GetProperty("base").GetString()!));
            o.Placement = new Placement { Position = P(a.GetProperty("pos")), Rotation = P(a.GetProperty("rot")) };
            if (a.TryGetProperty("linked", out var aln))
                foreach (var l in aln.EnumerateArray()) { var lr = new LinkedReferences(); lr.Reference.SetTo(C.Fk(l.GetProperty("ref").GetString()!)); o.LinkedReferences.Add(lr); }
            var space = a.GetProperty("space").GetString()!;
            if (space == "exterior") ((Worldspace)mod.Worldspaces.First()).TopCell!.Persistent.Add(o);
            else interiors[space].Persistent.Add(o);
        }
    }

    /// A voice type that is a member of the form list: the base's own when it is in the list, else the list's voice of the
    /// base's sex, an Argonian one for an Argonian base, else the Commoner one (the list holds Male/Female Commoner and Argonian).
    static FormKey RentVoice(INpcGetter src, FormKey list)
    {
        var members = Cache.Resolve<IFormListGetter>(list).Items.Select(i => i.FormKey).ToList();
        if (members.Contains(src.Voice.FormKey)) return src.Voice.FormKey;
        var female = src.Configuration.Flags.HasFlag(NpcConfiguration.Flag.Female);
        var argonian = Cache.TryResolve<IRaceGetter>(src.Race.FormKey, out var race) && (race.EditorID ?? "").StartsWith("Argonian");
        var want = (female ? "Female" : "Male") + (argonian ? "Argonian" : "Commoner");
        foreach (var m in members)
            if (Cache.TryResolve<IVoiceTypeGetter>(m, out var v) && v.EditorID == want) return m;
        throw new InvalidDataException($"{src.EditorID}: no voice {want} in {C.Key(list)}");
    }

    /// An LVLI is levelled against the player when any entry needs a level above 1 to drop.
    public static bool Levelled(ILeveledItemGetter li) => li.Entries?.Any(e => (e.Data?.Level ?? 1) > 1) == true;

    /// The fixed items an LVLI stands for: every level-1 entry when it gives all, else its first level-1 entry;
    /// nested lists the same way.
    public static List<FormKey> Fixed(ILeveledItemGetter li, int depth = 0)
    {
        var res = new List<FormKey>();
        if (depth > 8 || li.Entries == null) return res;
        var low = li.Entries.Where(e => (e.Data?.Level ?? 1) <= 1 && e.Data != null).ToList();
        if (low.Count == 0) low = li.Entries.Where(e => e.Data != null).OrderBy(e => e.Data!.Level).Take(1).ToList();
        if (!li.Flags.HasFlag(LeveledItem.Flag.UseAll)) low = low.Take(1).ToList();
        foreach (var e in low)
        {
            var k = e.Data!.Reference.FormKey;
            if (Cache.TryResolve<ILeveledItemGetter>(k, out var inner)) res.AddRange(Fixed(inner, depth + 1));
            else res.Add(k);
        }
        return res;
    }

    static void Flatten(Write.Ctx ctx, ExtendedList<ContainerEntry>? items)
    {
        if (items == null) return;
        var outList = new List<ContainerEntry>();
        foreach (var e in items)
        {
            var k = e.Item.Item.FormKey;
            if (Cache.TryResolve<ILeveledItemGetter>(k, out var li))
                foreach (var f in Fixed(li))
                    outList.Add(new ContainerEntry { Item = new ContainerItem { Item = new FormLink<IItemGetter>(f), Count = e.Item.Count } });
            else outList.Add(e);
        }
        items.Clear();
        items.AddRange(outList);
    }
}
