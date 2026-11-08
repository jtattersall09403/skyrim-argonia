using Mutagen.Bethesda.Strings;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Noggog;

// The Night-Reed line's first two quests (Phase 4 part C): TG01 "A Dry Hand in a Wet City" at Soulrest (BM&V's Docks,
// bmv.dock2) and Lilmoth, and TG02 "The Drowned Lockbox" at Lilmoth, from the records quest.tg.tg01 and quest.tg.tg02.
// Every stage, trigger, condition and effect is a proven block's shape (docs/design/blocks.md); the re-authored parts
// are named where they are built and in the records' review sections. Called from Generate after Combat, so earlier
// form ids never move. Places are measured (NightReedStudy) and every actor and marker is snapped to a navmesh
// triangle centre of the host cell's own navmesh at build; NightReedCheck reads them back.
static class NightReed
{
    static FormKey K(string k) => FormKey.Factory(k);
    static FormLink<ISkyrimMajorRecordGetter> L(FormKey k) => new(k);
    static readonly FormKey World = K("23D689:Black Marsh.esm"), PlayerRef = K("000014:Skyrim.esm"), Gold = K("00000F:Skyrim.esm"),
        Lockpick = K("00000A:Skyrim.esm"), XMarker = K("00003B:Skyrim.esm"), Achievements = K("0FC85D:Skyrim.esm");
    // Hosts (measured 2026-11-08, NightReedStudy): Soulrest's house interior and its room's navmesh; Soulrest's exterior
    // navmesh (cell 12,-2); the Chapter's dungeon and its inner room and ladder corridor; the deep channel north of
    // Pusbottom by the trapdoor (cell 5,0: land -700 under water 0) and its south bank's navmesh.
    public static readonly FormKey HouseCell = K("0E96A9:Black Marsh.esm"), HouseNav = K("0E96AA:Black Marsh.esm"),
        SoulrestNav = K("0A7785:Black Marsh North.esp"), ChapterCell = K("16BF81:Black Marsh North.esp"),
        ChapterRoom = K("16C06E:Black Marsh North.esp"), BankNav = K("07EDF2:Black Marsh.esm");
    public static readonly FormKey Trapdoor = K("16BF7F:Black Marsh North.esp");
    // we.tg01.doors: Soulrest's room has three door pairs; two are locked with no key on both sides.
    public static readonly string[] LockedDoors = ["11ACD3:Black Marsh North.esp", "120E95:Black Marsh.esm", "11ACA1:Black Marsh North.esp", "11ABF3:Black Marsh North.esp"];
    public const uint T1Tilts = 0, T1STabi = 1, T1Thief = 2, T1Friend = 3, T1Bent = 4, T1Zone = 5;
    public const uint T2Bent = 0, T2Neeta = 1, T2Okan = 2, T2Dar = 3, T2Box = 4;
    // The lockbox and fallen house on the channel floor (land measured at build), the eels between them and the bank.
    public static readonly (float X, float Y) BoxXY = (22400, 1024), HouseXY = (22784, 1408);
    public static readonly (float X, float Y)[] EelXY = [(22560, 1200), (22300, 1350)];

    internal sealed class Snapper(List<ISkyrimModGetter> mods)
    {
        readonly Dictionary<FormKey, (INavigationMeshGetter rec, ModKey from)> nav = Survey.Winners<INavigationMeshGetter>(mods);
        readonly HashSet<(FormKey, int)> used = [];
        public P3Float At(FormKey mesh, float x, float y)
        {
            var d = nav[mesh].rec.Data!; var v = d.Vertices;
            var best = Enumerable.Range(0, d.Triangles.Count).Where(i => !used.Contains((mesh, i))).Select(i =>
            {
                var t = d.Triangles[i].Vertices; var a = v[t.X]; var b = v[t.Y]; var c = v[t.Z];
                return (i, p: new P3Float((a.X + b.X + c.X) / 3, (a.Y + b.Y + c.Y) / 3, (a.Z + b.Z + c.Z) / 3));
            }).MinBy(e => (e.p.X - x) * (e.p.X - x) + (e.p.Y - y) * (e.p.Y - y));
            used.Add((mesh, best.i));
            return new P3Float(MathF.Round(best.p.X), MathF.Round(best.p.Y), MathF.Round(best.p.Z));
        }
        // The same, nearest in three dimensions: a deck above a deck (MainQuest's barge hold) keeps to the named level.
        public P3Float At(FormKey mesh, float x, float y, float z)
        {
            var d = nav[mesh].rec.Data!; var v = d.Vertices;
            var best = Enumerable.Range(0, d.Triangles.Count).Where(i => !used.Contains((mesh, i))).Select(i =>
            {
                var t = d.Triangles[i].Vertices; var a = v[t.X]; var b = v[t.Y]; var c = v[t.Z];
                return (i, p: new P3Float((a.X + b.X + c.X) / 3, (a.Y + b.Y + c.Y) / 3, (a.Z + b.Z + c.Z) / 3));
            }).MinBy(e => (e.p.X - x) * (e.p.X - x) + (e.p.Y - y) * (e.p.Y - y) + 16 * (e.p.Z - z) * (e.p.Z - z));
            used.Add((mesh, best.i));
            return new P3Float(MathF.Round(best.p.X), MathF.Round(best.p.Y), MathF.Round(best.p.Z));
        }
    }

    internal static ConditionFloat C(ConditionData d, CompareOperator op, float v, bool or = false) =>
        new() { CompareOperator = op, ComparisonValue = v, Data = d, Flags = or ? Condition.Flag.OR : 0 };
    internal static T OnPlayer<T>(T d) where T : ConditionData { d.RunOnType = Condition.RunOnType.Reference; d.Reference.SetTo(PlayerRef); return d; }
    internal static ConditionFloat StageLt(Quest q, int s) { var d = new GetStageConditionData(); d.Quest.Link.SetTo(q.FormKey); return C(d, CompareOperator.LessThan, s); }
    internal static ConditionFloat StageIs(Quest q, int s) { var d = new GetStageConditionData(); d.Quest.Link.SetTo(q.FormKey); return C(d, CompareOperator.EqualTo, s); }
    internal static ConditionFloat Speech(float v) => C(OnPlayer(new GetActorValueConditionData { ActorValue = ActorValue.Speech }), CompareOperator.GreaterThanOrEqualTo, v);
    internal static ConditionFloat Has(FormKey item, float n) { var d = new GetItemCountConditionData(); d.ItemOrList.Link.SetTo(item); OnPlayer(d); return C(d, CompareOperator.GreaterThanOrEqualTo, n); }
    internal static ConditionFloat IsId(Npc n) { var d = new GetIsIDConditionData(); d.Object.Link.SetTo(n.FormKey); return C(d, CompareOperator.EqualTo, 1); }
    internal static ConditionFloat Dead(uint alias, bool dead) => C(new GetDeadConditionData { RunOnType = Condition.RunOnType.QuestAlias, RunOnTypeIndex = (int)alias }, CompareOperator.EqualTo, dead ? 1 : 0);
    internal static ScriptEntry Script(string name, params ScriptProperty[] ps) { var e = new ScriptEntry { Name = name }; e.Properties.AddRange(ps); return e; }
    internal static ScriptObjectProperty Obj(string n, FormKey k) => new() { Name = n, Object = L(k) };
    internal static ScriptObjectProperty Alias(string n, Quest q, uint id) => new() { Name = n, Object = L(q.FormKey), Alias = (short)id };
    internal static ScriptIntProperty Int(string n, int v) => new() { Name = n, Data = v };

    // The written lines, one per INFO, by its TIF id; NightReedCheck and the dialogue pass read them from here.
    public sealed record Line(string Topic, string Prompt, string Text, string? Fragment);

    public static void Add(SkyrimMod mod, List<ISkyrimModGetter> mods)
    {
        var world = mod.Worldspaces.First(w => w.FormKey == World);
        var snap = new Snapper(mods);
        var npcs = Survey.Winners<INpcGetter>(mods);
        var placed = Survey.Winners<IPlacedGetter>(mods);
        var cells = Survey.Winners<ICellGetter>(mods);
        var noRefs = new Cell.TranslationMask(true) { Persistent = false, Temporary = false, NavigationMeshes = false, Landscape = false };

        var t1 = mod.Quests.AddNew("ARG_TG01");
        var t2 = mod.Quests.AddNew("ARG_TG02");
        var chapter = mod.Factions.AddNew("ARG_NightReedChapter");
        chapter.Name = "Night-Reed Chapter";
        chapter.Flags = Faction.FactionFlag.HiddenFromPC;
        foreach (var (i, title) in new[] { (0, "Lookout") })
            chapter.Ranks.Add(new Rank { Number = (uint)i, Title = new GenderedItem<TranslatedString?>(new TranslatedString(Language.English, title), new TranslatedString(Language.English, title)) });

        // W-npc: our bases templated on BM&V's (Ri'saad, vanilla, for the Khajiit) for looks; fixed level (0035).
        const NpcConfiguration.TemplateFlag looks = NpcConfiguration.TemplateFlag.Traits | NpcConfiguration.TemplateFlag.SpellList
            | NpcConfiguration.TemplateFlag.ModelAnimation | NpcConfiguration.TemplateFlag.AttackData | NpcConfiguration.TemplateFlag.Keywords
            | NpcConfiguration.TemplateFlag.Inventory;
        Npc Base(string id, string name, string tpl, short level, bool female, NpcConfiguration.Flag extra)
        {
            var t = npcs[K(tpl)].rec;
            var n = mod.Npcs.AddNew(id);
            n.Name = name;
            n.Template.SetTo(t.FormKey);
            n.Race.SetTo(t.Race.FormKey);
            n.Class.SetTo(t.Class.FormKey);
            n.Configuration.TemplateFlags = looks;
            n.Configuration.Level = new NpcLevel { Level = level };
            n.Configuration.Flags = NpcConfiguration.Flag.AutoCalcStats | NpcConfiguration.Flag.Unique | (female ? NpcConfiguration.Flag.Female : 0) | extra;
            n.AIData = new AIData { Aggression = Aggression.Unaggressive, Confidence = Confidence.Average, Responsibility = Responsibility.NoCrime, Assistance = Assistance.HelpsNobody };
            n.Voice.SetTo(t.Voice.FormKey);
            return n;
        }
        // Sex and face come with Traits, so each template is of the person's sex (Black Marsh.esm's winners of the presets).
        var tilts = Base("ARG_TG_Tilts", "Tilts-The-Jug", "0B2E11:Skyrim.esm", 10, true, NpcConfiguration.Flag.Essential);
        var stabi = Base("ARG_TG_STabi", "S'Tabi", "01B1DB:Skyrim.esm", 8, false, NpcConfiguration.Flag.Protected);
        var thief = Base("ARG_TG_KeepsWhatFloats", "Keeps-What-Floats", "043E58:Skyrim.esm", 5, false, NpcConfiguration.Flag.Protected);
        thief.AIData!.Confidence = Confidence.Cowardly; // we.tg01.thief: he runs when caught (no script)
        var friend = Base("ARG_TG_SitsByTheWater", "Sits-By-The-Water", "0B2E12:Skyrim.esm", 5, true, NpcConfiguration.Flag.Protected);
        var bent = Base("ARG_TG_BentSpine", "Bent-Spine", "02A1E6:Black Marsh.esm", 15, false, NpcConfiguration.Flag.Essential);
        var look1 = Base("ARG_TG_ChapterLookout1", "Night-Reed Lookout", "00FF4D:Black Marsh.esm", 8, false, 0);
        var look2 = Base("ARG_TG_ChapterLookout2", "Night-Reed Lookout", "02A1EE:Black Marsh.esm", 8, true, 0);
        var neeta = Base("ARG_TG_NeetaHaj", "Neeta-Haj", "160E6A:Black Marsh.esm", 5, true, NpcConfiguration.Flag.Protected);
        var okan = Base("ARG_TG_OkanTei", "Okan-Tei", "045E50:Black Marsh.esm", 5, false, NpcConfiguration.Flag.Protected);
        var dar = Base("ARG_TG_DarZeel", "Dar-Zeel", "1DE49D:Black Marsh.esm", 5, false, NpcConfiguration.Flag.Protected);
        foreach (var n in new[] { tilts, bent, look1, look2 })
            n.Factions.Add(new RankPlacement { Faction = chapter.ToLink<IFactionGetter>(), Rank = 0 });
        // we.tg02.eels: ripper eels, our base on vanilla's slaughterfish (a fixed level, no respawn).
        var eel = mod.Npcs.AddNew("ARG_TG_RipperEel");
        {
            var t = npcs[K("023AB8:Skyrim.esm")].rec;
            eel.Name = "Ripper Eel"; eel.Template.SetTo(t.FormKey); eel.Race.SetTo(t.Race.FormKey); eel.Class.SetTo(t.Class.FormKey);
            eel.Configuration.TemplateFlags = NpcConfiguration.TemplateFlag.Traits | NpcConfiguration.TemplateFlag.ModelAnimation | NpcConfiguration.TemplateFlag.AIData
                | NpcConfiguration.TemplateFlag.AIPackages | NpcConfiguration.TemplateFlag.AttackData | NpcConfiguration.TemplateFlag.SpellList | NpcConfiguration.TemplateFlag.Keywords | NpcConfiguration.TemplateFlag.Factions;
            eel.Configuration.Level = new NpcLevel { Level = 4 };
            eel.Configuration.Flags = NpcConfiguration.Flag.AutoCalcStats;
        }

        // Items (we.tg01.thief, we.tg02.house): our copies of vanilla jewellery and a misc carving, names carrying the tell.
        var armors = Survey.Winners<IArmorGetter>(mods);
        Armor Jewel(string id, string name, string from, uint value)
        {
            var a = armors[K(from)].rec.Duplicate(mod.GetNextFormKey());
            a.EditorID = id; a.Name = name; a.Value = value;
            mod.Armors.Add(a); return a;
        }
        var necklace = Jewel("ARG_TG01_JasperNecklace", "Blue Jasper Necklace", "087832:Skyrim.esm", 120);
        var charm = Jewel("ARG_TG02_NeesakCharm", "Newly Mounted Neesak Charm", "087833:Skyrim.esm", 90);
        var beads = Jewel("ARG_TG02_GlassBeads", "Kothringi Glass Beads", "09171B:Skyrim.esm", 90);
        // the figurine: vanilla HorkerTusk's ivory (Clutter\HorkerTusk), worn bone with no culture's mark; CRTotem2 (a Companions
        // totem) was Nordic (decision 0006)
        var figurine = Survey.Winners<IMiscItemGetter>(mods)[K("03AD68:Skyrim.esm")].rec.Duplicate(mod.GetNextFormKey());
        figurine.EditorID = "ARG_TG02_BoneFigurine"; figurine.Name = "Worn Bone Figurine"; figurine.Value = 60;
        figurine.Keywords?.Clear(); figurine.VirtualMachineAdapter = null;
        mod.MiscItems.Add(figurine);
        // the necklace goes on him at stage 20 (his inventory stays his template's, so he is dressed)
        var box = Survey.Winners<IContainerGetter>(mods)[K("09424C:Skyrim.esm")].rec.Duplicate(mod.GetNextFormKey());
        box.EditorID = "ARG_TG02_Lockbox"; box.Name = "Merchant's Lockbox";
        box.Items = [];
        foreach (var it in new IItemGetter[] { figurine, charm, beads })
            box.Items.Add(new ContainerEntry { Item = new ContainerItem { Item = new FormLink<IItemGetter>(it.FormKey), Count = 1 } });
        box.Flags &= ~Container.Flag.Respawns;
        mod.Containers.Add(box);

        // Places: snapped to the host navmeshes (measured), never two on one triangle.
        PlacedObject Marker(string id, P3Float p, FormKey? baseKey = null, int flags = 0x400) => new(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE)
        { EditorID = id, Base = new FormLinkNullable<IPlaceableObjectGetter>(baseKey ?? XMarker), MajorRecordFlagsRaw = flags, Placement = new Placement { Position = p } };
        PlacedNpc Actor(string id, Npc b, P3Float p, PlacedObject? parent)
        {
            var r = new PlacedNpc(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE) { EditorID = id, MajorRecordFlagsRaw = 0x400, Placement = new Placement { Position = p } };
            r.Base.SetTo(b.FormKey);
            if (parent != null) { r.EnableParent = new EnableParent(); r.EnableParent.Reference.SetTo(parent.FormKey); }
            return r;
        }
        var doorOut = placed[K("120E93:Black Marsh.esm")].rec.Placement!.Position;    // Soulrest's house, outside
        var doorIn = placed[K("0E971F:Black Marsh.esm")].rec.Placement!.Position;     // inside
        var trapIn = placed[K("16C05B:Black Marsh North.esp")].rec.Placement!.Position; // the ladder's foot
        // TG01's people and the thief's round, all on Soulrest's navmesh 0A7785 unless named.
        var tiltsAt = snap.At(HouseNav, 2300, 1150);                 // the room's far side, by its table and chest
        var stabiAt = snap.At(SoulrestNav, doorOut.X + 220, doorOut.Y - 150); // on the dock beside the house door
        var dayAt = snap.At(SoulrestNav, 50069, -7317);              // the dock west of the house
        var drinkAt = snap.At(SoulrestNav, 50964, -6408);            // the bench by the water (BM&V's 145424)
        var friendAt = snap.At(SoulrestNav, 51060, -6450);
        var sleepAt = snap.At(SoulrestNav, 49856, -6784);            // under the shacks' eaves north-west of the house
        var bentAt = snap.At(ChapterRoom, 1500, 2000);              // the inner room, past the ladder's corridor
        var look1At = snap.At(ChapterRoom, 1900, 2600);
        var look2At = snap.At(ChapterRoom, 1300, 2300);
        var bankAt = snap.At(BankNav, 23050, 650);                  // TG02's clients on the channel's south bank
        var neetaAt = snap.At(BankNav, 23100, 500);
        var okanAt = snap.At(BankNav, 23300, 700);
        var darAt = snap.At(BankNav, 23500, 520);
        _ = trapIn; _ = bankAt; _ = doorIn;

        var p1 = Marker("ARG_TG01_Parent", new P3Float(dayAt.X, dayAt.Y, dayAt.Z - 300), null, 0xC00);
        var p2 = Marker("ARG_TG02_Parent", new P3Float(bankAt.X, bankAt.Y, bankAt.Z - 300), null, 0xC00);
        var tiltsRef = Actor("ARG_TG_TiltsRef", tilts, tiltsAt, null);
        var stabiRef = Actor("ARG_TG_STabiRef", stabi, stabiAt, null);
        var thiefRef = Actor("ARG_TG_KeepsWhatFloatsRef", thief, dayAt, p1);
        var friendRef = Actor("ARG_TG_SitsByTheWaterRef", friend, friendAt, p1);
        var bentRef = Actor("ARG_TG_BentSpineRef", bent, bentAt, p1);
        var look1Ref = Actor("ARG_TG_ChapterLookout1Ref", look1, look1At, p1);
        var look2Ref = Actor("ARG_TG_ChapterLookout2Ref", look2, look2At, p1);
        var neetaRef = Actor("ARG_TG_NeetaHajRef", neeta, neetaAt, p2);
        var okanRef = Actor("ARG_TG_OkanTeiRef", okan, okanAt, p2);
        var darRef = Actor("ARG_TG_DarZeelRef", dar, darAt, p2);
        var dayMarker = Marker("ARG_TG01_DayMarker", dayAt);
        var drinkMarker = Marker("ARG_TG01_DrinkMarker", drinkAt);
        var sleepMarker = Marker("ARG_TG01_SleepMarker", sleepAt);
        // we.tg01.round: a vanilla ground bedroll where he sleeps (the sleep package's bed); no Nordic mark on it.
        var bedroll = Marker("ARG_TG01_Bedroll", new P3Float(sleepAt.X + 60, sleepAt.Y, sleepAt.Z), K("0B8371:Skyrim.esm"), 0x400);
        bedroll.EnableParent = new EnableParent(); bedroll.EnableParent.Reference.SetTo(p1.FormKey);
        // TR-zone, unconditioned with a prereq stage only (re-authored from zone + night + unseen: the follow is the
        // walk to his bed, which he keeps at night; the journal and objective say so).
        var trigTemplate = mods[0].EnumerateMajorRecords<IPlacedObjectGetter>().First(r => r.Base.FormKey == K("099312:Skyrim.esm") && r.Primitive != null);
        var zone = new PlacedObject(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE)
        {
            EditorID = "ARG_TG01_ZoneBed", MajorRecordFlagsRaw = 0x400, Placement = new Placement { Position = new P3Float(sleepAt.X, sleepAt.Y, sleepAt.Z + 100) },
            Primitive = trigTemplate.Primitive!.DeepCopy(),
            VirtualMachineAdapter = new VirtualMachineAdapter { Scripts = { Script("defaultSetStageTrigScript", Obj("myQuest", t1.FormKey), Int("prereqStageOPT", 20), Int("stage", 30)) } },
        };
        zone.Primitive.Bounds = new P3Float(200, 200, 100);
        zone.Base.SetTo(K("099312:Skyrim.esm"));

        // TG02's channel: the lockbox on the floor (Apprentice), the fallen house beside it, the eels above. Heights from
        // the land (measured: about -700 under water at 0); the box 10 units up so it settles, never inside the floor.
        float Floor((float X, float Y) p) => Surface.Land(mods, World, p.X, p.Y) ?? throw new InvalidOperationException($"no land at {p}");
        var boxRef = Marker("ARG_TG02_LockboxRef", new P3Float(BoxXY.X, BoxXY.Y, MathF.Round(Floor(BoxXY) + 10)), box.FormKey, 0x400);
        boxRef.Lock = new LockData { Level = LockLevel.Apprentice };
        boxRef.EnableParent = new EnableParent(); boxRef.EnableParent.Reference.SetTo(p2.FormKey);
        var houseBase = ((IPlacedObjectGetter)placed[K("0396C2:Black Marsh.esm")].rec).Base.FormKey; // BM&V's 001House at Soulrest
        var houseRef = Marker("ARG_TG02_FallenHouse", new P3Float(HouseXY.X, HouseXY.Y, MathF.Round(Floor(HouseXY))), houseBase, 0);
        houseRef.Placement!.Rotation = new P3Float(1.35f, 0, 0.6f); // on its side on the floor
        houseRef.EnableParent = new EnableParent(); houseRef.EnableParent.Reference.SetTo(p2.FormKey);
        var eelRefs = EelXY.Select((p, i) => Actor($"ARG_TG02_Eel{i + 1}", eel, new P3Float(p.X, p.Y, MathF.Round(Floor(p) / 2)), p2)).ToList();

        // Packages: the thief's round on his alias (E-package by alias list), copies of vanilla's Gleda sandbox and sleep
        // with their schedules; the friend at the bench always.
        var packs = mods[0].Packages.ToDictionary(p => p.EditorID ?? "", p => p);
        Package Pack(string id, string from, PlacedObject at, int radius, sbyte hour, int minutes)
        {
            var p = packs[from].Duplicate(mod.GetNextFormKey());
            p.EditorID = id; p.OwnerQuest.Clear(); p.Conditions.Clear();
            p.ScheduleHour = hour; p.ScheduleDurationInMinutes = minutes;
            foreach (var d in p.Data.Values.OfType<PackageDataLocation>().Take(1))
            {
                d.Location = new LocationTargetRadius { Target = new LocationTarget(), Radius = (uint)radius };
                ((LocationTarget)d.Location.Target).Link.SetTo(at.FormKey);
            }
            mod.Packages.Add(p); return p;
        }
        var dayPack = Pack("ARG_TG01_ThiefDay", "GledaSandboxEditorLocation512", dayMarker, 600, 6, 12 * 60);
        var drinkPack = Pack("ARG_TG01_ThiefEvening", "GledaSandboxEditorLocation512", drinkMarker, 250, 18, 5 * 60);
        var sleepPack = Pack("ARG_TG01_ThiefSleep", "GledaSleepEditorLoc24x8", sleepMarker, 300, 23, 7 * 60);
        var friendPack = Pack("ARG_TG01_FriendBench", "GledaSandboxEditorLocation512", drinkMarker, 250, -1, 0);

        // The quest records, their topics and lines.
        Build1(mod, t1, t2, chapter, tilts, stabi, thief, friend, bent, necklace, tiltsRef, stabiRef, thiefRef, friendRef, bentRef, zone, p1, dayPack, drinkPack, sleepPack, friendPack);
        Build2(mod, t2, chapter, bent, neeta, okan, dar, figurine, charm, beads, bentRef, neetaRef, okanRef, darRef, boxRef, p2);

        // World edits. Exterior persistent refs in the worldspace's persistent cell; interiors in their cell overrides.
        world.TopCell!.Persistent.AddRange([p1, p2, stabiRef, thiefRef, friendRef, neetaRef, okanRef, darRef, dayMarker, drinkMarker, sleepMarker, bedroll, zone, boxRef, houseRef]);
        world.TopCell.Persistent.AddRange(eelRefs);
        houseRef.MajorRecordFlagsRaw = 0x400;
        Cell Interior(FormKey k)
        {
            foreach (var b in mod.Cells.Records) foreach (var sb in b.SubBlocks) foreach (var c in sb.Cells) if (c.FormKey == k) return c;
            var id = k.ID; var bn = (int)(id % 10); var sn = (int)(id / 10 % 10);
            var block = mod.Cells.Records.FirstOrDefault(b => b.BlockNumber == bn);
            if (block == null) { block = new CellBlock { BlockNumber = bn, GroupType = GroupTypeEnum.InteriorCellBlock }; mod.Cells.Records.Add(block); }
            var sub = block.SubBlocks.FirstOrDefault(s => s.BlockNumber == sn);
            if (sub == null) { sub = new CellSubBlock { BlockNumber = sn, GroupType = GroupTypeEnum.InteriorCellSubBlock }; block.SubBlocks.Add(sub); }
            var cell = cells[k].rec.DeepCopy(noRefs); sub.Cells.Add(cell); return cell;
        }
        Interior(HouseCell).Persistent.Add(tiltsRef);
        Interior(ChapterCell).Persistent.AddRange([bentRef, look1Ref, look2Ref]);
        // W-override: two of the house's door pairs locked with no key (both sides); the Chapter's trapdoor at Novice.
        void Lock(FormKey k, LockLevel level)
        {
            var r = (PlacedObject)((IPlacedObjectGetter)placed[k].rec).DeepCopy();
            r.Lock = new LockData { Level = level };
            r.MajorRecordFlagsRaw |= 0x400;
            if (r.Placement!.Position.Z > 7000) Interior(HouseCell).Persistent.Add(r); // the house's inner doors
            else world.TopCell.Persistent.Add(r);
        }
        foreach (var d in LockedDoors) Lock(K(d), LockLevel.RequiresKey);
        Lock(Trapdoor, LockLevel.Novice);
        Console.WriteLine($"night-reed: TG01 {t1.FormKey}, TG02 {t2.FormKey}, {Lines.Count} lines");
    }

    public static readonly List<Line> Lines = [];
    static readonly List<(string script, string body)> TifBodies = [];

    // One top-level player topic per line set (TR-topic): its INFOs, each with its conditions and a TIF fragment whose
    // body calls the quest script (properties stay on the quest script; Papyrus in papyrus/generated is written by
    // `nightreed-psc`).
    // The written lines (dialogue-write pass, text-reviewed), one per INFO keyed "<topic>_<n>"; the inline texts below are
    // the records' intents the lines were written to, and every INFO must have its written line.
    const string WrittenPath = "story/data/dialogue-writer/quest/tg/nightreed.lines.tsv";
    static readonly Dictionary<string, string> Written = File.ReadLines(WrittenPath).Where(l => l.Length > 0 && l[0] != '#')
        .Select(l => l.Split('\t', 2)).ToDictionary(x => x[0], x => x[1]);
    static void Topic(SkyrimMod mod, Quest q, string id, string prompt, params (string text, string? body, ConditionFloat[] conds)[] infos)
    {
        var branch = mod.DialogBranches.AddNew(id + "Branch");
        var t = mod.DialogTopics.AddNew(id);
        branch.Quest.SetTo(q.FormKey); branch.Category = DialogBranch.CategoryType.Player; branch.Flags = DialogBranch.Flag.TopLevel;
        branch.StartingTopic.SetTo(t.FormKey);
        t.Name = prompt; t.Quest.SetTo(q.FormKey); t.Branch.SetTo(branch.FormKey); t.Priority = 50;
        t.Category = DialogTopic.CategoryEnum.Topic; t.Subtype = DialogTopic.SubtypeEnum.Custom; t.SubtypeName = new RecordType("CUST");
        var n = 0;
        foreach (var (text, body, conds) in infos)
        {
            var info = new DialogResponses(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE) { Flags = new DialogResponseFlags(), Prompt = prompt };
            var said = Written.TryGetValue($"{id}_{n}", out var w) ? w : throw new InvalidDataException($"no written line {id}_{n} in {WrittenPath}");
            info.Responses.Add(new DialogResponse { Text = said, ResponseNumber = 1, Emotion = Emotion.Neutral });
            info.Conditions.AddRange(conds);
            string? script = null;
            if (body != null)
            {
                script = $"TIF_{id}_{n}";
                info.VirtualMachineAdapter = new DialogResponsesAdapter
                {
                    Scripts = { Script(script) },
                    ScriptFragments = new ScriptFragments { FileName = script, OnEnd = new ScriptFragment { ScriptName = script, FragmentName = "Fragment_0" } },
                };
                TifBodies.Add((script, body));
            }
            Lines.Add(new Line(id, prompt, said, script));
            t.Responses.Add(info);
            n++;
        }
    }

    static void Stages(Quest q, (int s, string? log, QuestLogEntry.Flag flag)[] stages, (ushort i, string text)[] objectives, string script)
    {
        foreach (var (s, log, flag) in stages)
            q.Stages.Add(new QuestStage { Index = (ushort)s, Flags = s == 0 ? QuestStage.Flag.StartUpStage : 0, LogEntries = { new QuestLogEntry { Flags = flag, Entry = log } } });
        foreach (var (i, text) in objectives) q.Objectives.Add(new QuestObjective { Index = i, DisplayText = text });
        foreach (var (s, _, _) in stages.Where(x => x.s != 0))
            q.VirtualMachineAdapter!.Fragments.Add(new QuestScriptFragment { Stage = (ushort)s, StageIndex = 0, ScriptName = script, FragmentName = $"Fragment_{s}" });
    }
    internal static QuestAlias Forced(Quest q, uint id, string name, FormKey r, QuestAlias.Flag flags = 0)
    {
        var a = new QuestAlias { ID = id, Type = QuestAlias.TypeEnum.Reference, Name = name, Flags = flags };
        a.ForcedReference.SetTo(r); q.Aliases.Add(a); return a;
    }
    internal static QuestFragmentAlias AliasScript(Quest q, uint id, ScriptEntry s) { var f = new QuestFragmentAlias { Property = Alias("", q, id) }; f.Scripts.Add(s); return f; }
    internal static ScriptEntry OnDeath(Quest q, int pre, int set) => Script("defaultSetStageOnDeathRefAlias", Obj("myQST", q.FormKey), Int("preReqStage", pre), Int("StageToSet", set));

    static void Build1(SkyrimMod mod, Quest q, Quest next, Faction chapter, Npc tilts, Npc stabi, Npc thief, Npc friend, Npc bent, Armor necklace,
        PlacedNpc tiltsRef, PlacedNpc stabiRef, PlacedNpc thiefRef, PlacedNpc friendRef, PlacedNpc bentRef, PlacedObject zone, PlacedObject parent,
        Package day, Package evening, Package sleep, Package friendPack)
    {
        // Start Game Enabled with an empty start-up stage 0; Tilts-The-Jug's opening topic, gated on stage 0, sets 20
        // (re-authored from a dialogue start: the proven shape).
        q.Name = "A Dry Hand in a Wet City"; q.Priority = 50; q.Type = Quest.TypeEnum.SideQuest; q.Flags = Quest.Flag.StartGameEnabled;
        q.VirtualMachineAdapter = new QuestAdapter
        {
            FileName = "ARG_QF_TG01",
            Scripts = { Script("ARG_QF_TG01", Alias("Tilts", q, T1Tilts), Alias("Thief", q, T1Thief), Obj("RoundParent", parent.FormKey),
                Obj("Necklace", necklace.FormKey), Obj("Gold001", Gold), Obj("Lockpick", Lockpick), Obj("Chapter", chapter.FormKey),
                Obj("NextQuest", next.FormKey), Obj("AchievementsQuest", Achievements)) },
        };
        Stages(q, [
            (0, null, 0),
            (20, "Tilts-The-Jug, inside the house on Soulrest's dock, keeps the Chapter's desk at Soulrest and wants to see how I work. Keeps-What-Floats, a dock thief, took a necklace of polished blue jaspers from another thief, and it must come back with no harm done to him. I'm to follow him on the dock until he goes to his bed for the night, or get out of Sits-By-The-Water, who drinks with him, where he sleeps.", 0),
            (30, "Keeps-What-Floats, who took the necklace of blue jaspers, keeps it on him on the dock by day, at the bench by the water in the evening, and on his bedroll north-west of the house at night. I'm to get the necklace back without hurting him, by lifting it off him by day or while he sleeps, or by talking him out of it, and bring it to Tilts-The-Jug inside Soulrest's house.", 0),
            (40, "I brought the necklace of blue jaspers back to Tilts-The-Jug at Soulrest, and Keeps-What-Floats came to no harm. She paid me and gave me three lockpicks. The Chapter's way down is a locked trapdoor two squares north of Pusbottom in Lilmoth. I'm to take the coast ship from Soulrest's dock to Lilmoth, open the trapdoor, go down to the Chapter and speak to whoever waits below.", 0),
            (41, "I brought the necklace of blue jaspers back to Tilts-The-Jug at Soulrest, but Keeps-What-Floats is dead. She paid me nothing, and said the Chapter wanted the necklace without a body, but she gave me three lockpicks and sent me on. The Chapter's way down is a locked trapdoor two squares north of Pusbottom in Lilmoth. I'm to take the coast ship from Soulrest's dock to Lilmoth, open the trapdoor, go down to the Chapter and speak to whoever waits below.", 0),
            (90, "I got the necklace of blue jaspers back from Keeps-What-Floats at Soulrest without hurting him, and Tilts-The-Jug paid me. I opened the trapdoor north of Pusbottom with my own hand and went down to the Chapter, and Bent-Spine took me in as a Lookout.", QuestLogEntry.Flag.CompleteQuest),
            (91, "I got the necklace of blue jaspers back at Soulrest, but Keeps-What-Floats died for it, and Tilts-The-Jug paid me nothing. I opened the trapdoor north of Pusbottom with my own hand and went down to the Chapter, and Bent-Spine took me in as a Lookout.", QuestLogEntry.Flag.CompleteQuest),
        ], [
            (20, "Follow Keeps-What-Floats on Soulrest's dock to his bed, or get it out of his drinking friend"),
            (30, "Get the Blue Jasper Necklace from Keeps-What-Floats without harming him"),
            (31, "Bring the necklace to Tilts-The-Jug inside Soulrest's house"),
            (40, "Pick the lock of the trapdoor north of Pusbottom in Lilmoth and speak to whoever waits below"),
        ], "ARG_QF_TG01");
        Forced(q, T1Tilts, "Tilts", tiltsRef.FormKey);
        Forced(q, T1STabi, "STabi", stabiRef.FormKey);
        var th = Forced(q, T1Thief, "Thief", thiefRef.FormKey, QuestAlias.Flag.AllowDisabled);
        th.PackageData.Add(day.ToLink()); th.PackageData.Add(evening.ToLink()); th.PackageData.Add(sleep.ToLink());
        Forced(q, T1Friend, "Friend", friendRef.FormKey, QuestAlias.Flag.AllowDisabled).PackageData.Add(friendPack.ToLink());
        Forced(q, T1Bent, "BentSpine", bentRef.FormKey, QuestAlias.Flag.AllowDisabled);
        Forced(q, T1Zone, "BedZone", zone.FormKey);
        // TR-death: either the thief or his friend dead before the follow moves the quest on to 30 (two aliases, one stage).
        q.VirtualMachineAdapter.Aliases.Add(AliasScript(q, T1Thief, OnDeath(q, 20, 30)));
        q.VirtualMachineAdapter.Aliases.Add(AliasScript(q, T1Friend, OnDeath(q, 20, 30)));

        const string Q = "(GetOwningQuest() as ARG_QF_TG01)";
        Topic(mod, q, "ARG_TG01_TopicDoor", "Is there quiet work at Soulrest?",
            ("Quiet work is not sold on this dock, friend. But Tilts-The-Jug, inside the house behind me, sometimes has a use for a careful pair of hands.", null, [IsId(stabi), StageLt(q, 20)]));
        Topic(mod, q, "ARG_TG01_TopicTest", "S'Tabi sent me about the Chapter.",
            ("Then let us see how you work. Keeps-What-Floats, a dock thief, took a necklace of blue jaspers from another thief while he slept. I want it back, and I want him unharmed. Watch his round; he keeps it on him.", "GetOwningQuest().SetStage(20)", [IsId(tilts), StageIs(q, 0)]));
        Topic(mod, q, "ARG_TG01_TopicBed", "Where does Keeps-What-Floats sleep?",
            ("He drinks here with me till the lamps are low, then sleeps on a bedroll north-west of the house. If anyone shouts at him, he runs.", "GetOwningQuest().SetStage(30)", [IsId(friend), StageIs(q, 20), Speech(25)]),
            ("Buy me a drink and I'll tell you. Ten gold. ... He sleeps on a bedroll north-west of the house, and he runs from any shout.", $"{Q}.PayFriend()", [IsId(friend), StageIs(q, 20), Has(Gold, 10)]));
        Topic(mod, q, "ARG_TG01_TopicGiveBack", "Give me the jasper necklace.",
            ("You talk like someone who knows who it belongs to. Take it, then. I never could sell it.", $"{Q}.NecklaceFrom(akSpeakerRef, 0)", [IsId(thief), StageIs(q, 30), Speech(35), HasOn(necklace.FormKey)]),
            ("Sixty gold, and it is yours. I have a buyer, I swear.", $"{Q}.NecklaceFrom(akSpeakerRef, 60)", [IsId(thief), StageIs(q, 30), Has(Gold, 60), HasOn(necklace.FormKey)]));
        Topic(mod, q, "ARG_TG01_TopicReturn", "I have the necklace.",
            ("And he is still breathing. Good hands. Here is your pay, and three picks. The Chapter's door is a trapdoor two squares north of Pusbottom in Lilmoth. Take the coast ship, open it yourself, and speak to whoever waits below.", "GetOwningQuest().SetStage(40)", [IsId(tilts), StageIs(q, 30), Has(necklace.FormKey, 1), Dead(T1Thief, false)]),
            ("The Chapter wanted the necklace without a body. No pay. Take three picks all the same: the trapdoor two squares north of Pusbottom in Lilmoth. Open it yourself.", "GetOwningQuest().SetStage(41)", [IsId(tilts), StageIs(q, 30), Has(necklace.FormKey, 1), Dead(T1Thief, true)]));
        Topic(mod, q, "ARG_TG01_TopicWelcome", "Tilts-The-Jug sent me down.",
            ("You opened the trapdoor with your own hand. Then you are a Lookout of the Night-Reed Chapter. Stay; I have work.", "GetOwningQuest().SetStage(90)", [IsId(bent), StageIs(q, 40)]),
            ("You opened the trapdoor with your own hand, though I hear the dock thief is dead. You are a Lookout of the Night-Reed Chapter all the same. Stay; I have work.", "GetOwningQuest().SetStage(91)", [IsId(bent), StageIs(q, 41)]));
    }

    // C-item on the speaker (the condition's default subject): the thief still has the necklace.
    static ConditionFloat HasOn(FormKey item) { var d = new GetItemCountConditionData(); d.ItemOrList.Link.SetTo(item); return C(d, CompareOperator.GreaterThanOrEqualTo, 1); }

    static void Build2(SkyrimMod mod, Quest q, Faction chapter, Npc bent, Npc neeta, Npc okan, Npc dar, MiscItem figurine, Armor charm, Armor beads,
        PlacedNpc bentRef, PlacedNpc neetaRef, PlacedNpc okanRef, PlacedNpc darRef, PlacedObject boxRef, PlacedObject parent)
    {
        // TR-chain: started by TG01's 90 or 91 with SetStage(20); an empty start-up stage 0.
        q.Name = "The Drowned Lockbox"; q.Priority = 50; q.Type = Quest.TypeEnum.SideQuest; q.Flags = 0;
        q.VirtualMachineAdapter = new QuestAdapter
        {
            FileName = "ARG_QF_TG02",
            Scripts = { Script("ARG_QF_TG02", Alias("BentSpine", q, T2Bent), Alias("Neeta", q, T2Neeta), Alias("Okan", q, T2Okan), Alias("Dar", q, T2Dar),
                Obj("ClientsParent", parent.FormKey), Obj("Figurine", figurine.FormKey), Obj("Charm", charm.FormKey), Obj("Beads", beads.FormKey),
                Obj("Gold001", Gold), Obj("AchievementsQuest", Achievements)) },
        };
        // Re-authored: "all three claims heard" is three hidden stages (21, 22, 23), each fragment checking the other two
        // (the race-guard shape); "each sold back" likewise (43, 44, 45 to 91); any client's death before the end is the
        // failed ending 92 (TR-death, three aliases on one stage), replacing the 20-to-40 fail-forward.
        Stages(q, [
            (0, null, 0),
            (20, "I'm in the Night-Reed Chapter now, under Pusbottom in Lilmoth. Bent-Spine, the Chapter's fence, wants the lockbox of a merchant whose stilt house fell into the deep water two squares north of Pusbottom, by the Chapter's trapdoor; it lies locked on the floor beside the house, and ripper eels hunt the water. Three clients on the bank want it. I'm to talk to each of them, Neeta-Haj, Okan-Tei and Dar-Zeel, and get out of each what they claim the box holds for them.", 0),
            (21, null, 0), (22, null, 0), (23, null, 0),
            (40, "Neeta-Haj says the bone figurine in the lockbox was carved for her clutch, Okan-Tei that the charm was only pledged and never sold, and Dar-Zeel that the beads are old family work. The box lies locked on the floor of the deep water north of Pusbottom beside the fallen stilt house, and ripper eels hunt the water. I'm to swim down to it, slip past the eels, pick its lock and take the figurine, the charm and the beads, then settle it on the bank, by handing all three things to one client or by selling each client the thing they claimed.", 0),
            (43, null, 0), (44, null, 0), (45, null, 0),
            (90, "I brought up the lockbox's figurine, charm and beads from the deep water north of Pusbottom, past the ripper eels, and gave all three to one of the clients on the bank, who paid me for them. The other two will not forget it.", QuestLogEntry.Flag.CompleteQuest),
            (91, "I brought up the lockbox's figurine, charm and beads from the deep water north of Pusbottom, past the ripper eels, and sold each client the thing they claimed. Neeta-Haj, Okan-Tei and Dar-Zeel paid, and none of them will greet me kindly again.", QuestLogEntry.Flag.CompleteQuest),
            (92, "With one of Neeta-Haj, Okan-Tei or Dar-Zeel dead before I had settled with them, the lockbox's pledges cannot be settled, and the job for Bent-Spine has come to nothing.", QuestLogEntry.Flag.FailQuest),
        ], [
            (20, "Get each of the three clients on the bank north of Pusbottom to say what they claim from the box"),
            (41, "Dive to the lockbox beside the fallen house, pick its lock and take the three things in it"),
            (42, "On the bank, give the three things to one client, or sell each client the thing they claimed"),
        ], "ARG_QF_TG02");
        Forced(q, T2Bent, "BentSpine", bentRef.FormKey, QuestAlias.Flag.AllowDisabled);
        Forced(q, T2Neeta, "Neeta", neetaRef.FormKey, QuestAlias.Flag.AllowDisabled);
        Forced(q, T2Okan, "Okan", okanRef.FormKey, QuestAlias.Flag.AllowDisabled);
        Forced(q, T2Dar, "Dar", darRef.FormKey, QuestAlias.Flag.AllowDisabled);
        Forced(q, T2Box, "Lockbox", boxRef.FormKey, QuestAlias.Flag.AllowDisabled);
        foreach (var a in new[] { T2Neeta, T2Okan, T2Dar }) q.VirtualMachineAdapter.Aliases.Add(AliasScript(q, a, OnDeath(q, 20, 92)));

        const string Q = "(GetOwningQuest() as ARG_QF_TG02)";
        Topic(mod, q, "ARG_TG02_TopicJob", "You said you have work.",
            ("A merchant's stilt house fell into the deep water two squares south of here, by our trapdoor. His lockbox lies beside it on the floor, locked, and ripper eels hunt that water. Three of his clients wait on the bank. Bring the box up before they find a diver. What becomes of what is in it, I leave to you.", null, [IsId(bent), StageIs(q, 20)]));
        Topic(mod, q, "ARG_TG02_TopicClaimFigurine", "What do you claim from the lockbox?",
            ("The bone figurine. It was carved for my clutch, and it should come back to me.", "GetOwningQuest().SetStage(21)", [IsId(neeta), StageIs(q, 20)]));
        Topic(mod, q, "ARG_TG02_TopicClaimCharm", "What do you claim from the lockbox?",
            ("The Neesak charm. I only pledged it to him. It was never sold.", "GetOwningQuest().SetStage(22)", [IsId(okan), StageIs(q, 20), Speech(30)]),
            ("Twenty gold loosens the tongue. The charm is mine. I only pledged it; it was never sold.", $"{Q}.PayOkan()", [IsId(okan), StageIs(q, 20), Has(Gold, 20)]));
        Topic(mod, q, "ARG_TG02_TopicClaimBeads", "What do you claim from the lockbox?",
            ("The beads. Old family work, handed down. They are worth nothing to anyone but us.", "GetOwningQuest().SetStage(23)", [IsId(dar), StageIs(q, 20)]));
        foreach (var (n, id) in new[] { (neeta, "Neeta"), (okan, "Okan"), (dar, "Dar") })
            Topic(mod, q, $"ARG_TG02_TopicHandOver{id}", "Take all three pledges.",
                ("All three? Then here is eighty gold, and I will not ask where you found them.", $"{Q}.HandOver(akSpeakerRef)", [IsId(n), StageIs(q, 40), Has(figurine.FormKey, 1), Has(charm.FormKey, 1), Has(beads.FormKey, 1)]));
        Topic(mod, q, "ARG_TG02_TopicSellFigurine", "This figurine is older than any clutch of yours.",
            ("Worn smooth, yes. Fifty gold, then, and we say no more of clutches.", $"{Q}.SellBack(akSpeakerRef, 43)", [IsId(neeta), StageIs(q, 40), Has(figurine.FormKey, 1), Speech(30)]));
        Topic(mod, q, "ARG_TG02_TopicSellCharm", "No one remounts a charm that was only pledged.",
            ("A new silver mount. He bought it outright, then. Fifty gold, and it comes home.", $"{Q}.SellBack(akSpeakerRef, 44)", [IsId(okan), StageIs(q, 40), Has(charm.FormKey, 1), Speech(30)]));
        Topic(mod, q, "ARG_TG02_TopicSellBeads", "These beads are Kothringi glass from the old cairns.",
            ("Keep your voice down. Fifty gold, and you never saw them.", $"{Q}.SellBack(akSpeakerRef, 45)", [IsId(dar), StageIs(q, 40), Has(beads.FormKey, 1), Speech(30)]));
    }

    // nightreed-psc <dir>: writes the TIF fragment scripts the topics above use (Papyrus source, generated).
    public static void WritePsc(string dir)
    {
        Directory.CreateDirectory(dir);
        foreach (var (script, body) in TifBodies)
            File.WriteAllText(Path.Combine(dir, script + ".psc"),
                $"Scriptname {script} extends TopicInfo Hidden\n{{Generated by tools/ArgoniaPlugin/NightReed.cs: one Night-Reed line's end fragment (TR-topic).}}\n\n;BEGIN FRAGMENT Fragment_0\nFunction Fragment_0(ObjectReference akSpeakerRef)\n\t{body}\nEndFunction\n;END FRAGMENT\n");
    }
}
