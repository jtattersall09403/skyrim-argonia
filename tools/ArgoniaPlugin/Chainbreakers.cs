using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using Noggog;
using static LocalQuests;

// Phase 4's Chainbreakers line (story data quest.bc.bc01 to bc03), built from Phase 3's proven blocks with LocalQuests'
// kit, all in BM&V's BlackMarsh (23D689). BC01 Four Months for a Boat: Never-Sold in the Chainbreakers' house (BM&V's
// House, 15635D) and the estate landing at 31,-12 (095465, Black Marsh North's navmesh 0ACD06). BC02 Names Scratched Out:
// the heirs' outer post, BM&V's walk-in stone house 01Swamphousestone (1307CF, architecture\Swamp House.nif) on the shore
// at the Rose's east edge, 34,-16 (cell 0AFE4F, Black Marsh North's navmesh 0ACC91 on the land inside), its gate-keepers
// at its west side. (BM&V's keep 01cyKeep, cyrkeep.nif, is in no archive or folder of the load order: an empty hill.) BC03 The Broker's Mercy stands on Soulrest's open dock, BM&V's Dock2 (02F35A, 11,-2),
// whose navmesh is Black Marsh North's 0A7784. The line's standing is ARG_ChainbreakersStanding (E-global). Allocated
// after LocalQuests in Generate, BC01, BC02, BC03.
static class Chainbreakers
{
    public static readonly FormKey BlackMarsh = FormKey.Factory("23D689:Black Marsh.esm");
    const string Dock2 = "02F35A:Black Marsh.esm", Landing = "095465:Black Marsh.esm", HouseExt = "0AFC2C:Black Marsh.esm",
        PostCell = "0AFE4F:Black Marsh.esm";
    static readonly FormKey House = FormKey.Factory("15635D:Black Marsh.esm");
    static readonly FormKey Gold = FormKey.Factory("00000F:Skyrim.esm"), Achievements = FormKey.Factory("0FC85D:Skyrim.esm"),
        PlayerRef = FormKey.Factory("000014:Skyrim.esm"), StrongBox = FormKey.Factory("09424C:Skyrim.esm"), OlavaToken = FormKey.Factory("059654:Skyrim.esm"),
        Journal = FormKey.Factory("10B2CD:Skyrim.esm"), Smoke = FormKey.Factory("0D5E82:Skyrim.esm");
    const string Female = "02A1EE:Black Marsh.esm", Male = "00FF4D:Black Marsh.esm";
    public const uint B3Ussa = 0, B3Rope = 1, B3Chest = 2, B3Tokens = 3;
    public const uint B1Patron = 0, B1Debtor = 1, B1Steward = 2, B1Chest = 3;
    public const uint B2Patron = 0, B2Keeper = 1, B2Speaker = 2, B2Killer = 3, B2Mother = 4;
    // The post's floor: the navmesh triangles nearest these points, all well inside the house's footprint (16 x 20 m round
    // its origin 140731,-63604; bmv_shell: 16 inner triangles, joined to the street); the gate 1100 west, towards the town.
    // Never-Sold's spot in HouseInt's small house (SmallHouseINT 156421): between the shelf (156424) and the hearth
    // (15642B), under its floor level plus a step (the highest floor crossing below Z).
    public static readonly (float X, float Y, float Z) RoomSpot = (520, -120, 1560);
    public static readonly (float X, float Y)[] HeldAt = [(140850, -63800), (140931, -63454), (140731, -63854)];
    public static readonly (float X, float Y) PostCentre = (140731, -63604), GateAt = (139631, -63604);

    static GlobalShort? standing;
    public static void Add(SkyrimMod mod, List<ISkyrimModGetter> mods)
    {
        var kit = new Kit(mod, mods, BlackMarsh);
        standing = mod.Globals.AddNewShort("ARG_ChainbreakersStanding"); standing.Data = 0;
        var patronRef = NeverSold(mod, mods, kit);
        var bc01 = Bc01(mod, mods, kit, patronRef);
        Bc02(mod, mods, kit, patronRef, bc01);
        Bc03(mod, mods, kit, bc01);
    }

    static Npc Person(Kit kit, string id, string name, bool female, short level, NpcConfiguration.Flag extra = 0)
    {
        var n = kit.Base(id, name, female ? Female : Male, level, NpcConfiguration.Flag.Unique | extra);
        if (!female) n.Configuration.Flags &= ~NpcConfiguration.Flag.Female;
        return n;
    }

    // Never-Sold (we.bc01.never-sold), the keeper of the Chainbreakers' house: one placement, in BM&V's House (15635D), on
    // its navmesh; BC01 and BC02 both name her ref.
    static PlacedNpc NeverSold(SkyrimMod mod, List<ISkyrimModGetter> mods, Kit kit)
    {
        var b = Person(kit, "ARG_BC_NeverSold", "Never-Sold", true, 10);
        // BM&V's HouseInt has no navmesh in its rooms (its one navmesh lies at z 7520 over nothing): he stands in the small
        // house by the hearth and the shelf, on the floor its mesh carries (PlaceCheck.Standing).
        var cellRefs = mods.SelectMany(m => m.Cells.Records.SelectMany(b => b.SubBlocks).SelectMany(s => s.Cells)).Where(c => c.FormKey == House)
            .SelectMany(c => c.Persistent.Concat(c.Temporary)).OfType<IPlacedObjectGetter>().Where(o => o.Placement != null).ToList();
        Surface.Bases(mods);
        var hits = Surface.UnderRefs(cellRefs, new Surface.Assets(Surface.Paths), RoomSpot.X, RoomSpot.Y, everyCrossing: true);
        var floor = hits.Where(h => h.Top <= RoomSpot.Z).Select(h => h.Top).DefaultIfEmpty(float.NaN).Max();
        if (float.IsNaN(floor)) throw new InvalidOperationException($"no floor under Never-Sold's spot ({cellRefs.Count} refs; crossings {string.Join(", ", hits.Select(h => $"{h.EditorId} {h.Top:F0}"))})");
        var at = new P3Float(RoomSpot.X, RoomSpot.Y, MathF.Round(floor) + 10);
        var r = kit.Actor("ARG_BC_NeverSoldRef", b, at);
        Interior(mod, mods, House).Persistent.Add(r);
        return r;
    }

    static Cell Interior(SkyrimMod mod, List<ISkyrimModGetter> mods, FormKey k)
    {
        foreach (var bl in mod.Cells.Records) foreach (var sb in bl.SubBlocks) foreach (var c in sb.Cells) if (c.FormKey == k) return c;
        var cells = Survey.Winners<ICellGetter>(mods);
        var noRefs = new Cell.TranslationMask(true) { Persistent = false, Temporary = false, NavigationMeshes = false, Landscape = false };
        var id = k.ID; var bn = (int)(id % 10); var sn = (int)(id / 10 % 10);
        var block = mod.Cells.Records.FirstOrDefault(b => b.BlockNumber == bn);
        if (block == null) { block = new CellBlock { BlockNumber = bn, GroupType = GroupTypeEnum.InteriorCellBlock }; mod.Cells.Records.Add(block); }
        var sub = block.SubBlocks.FirstOrDefault(s => s.BlockNumber == sn);
        if (sub == null) { sub = new CellSubBlock { BlockNumber = sn, GroupType = GroupTypeEnum.InteriorCellSubBlock }; block.SubBlocks.Add(sub); }
        var cell = cells[k].rec.DeepCopy(noRefs); sub.Cells.Add(cell); return cell;
    }

    // A snapped spot inside the post: fail the build if the nearest triangle lies outside the walls.
    static P3Float Inside(Kit kit, float x, float y)
    {
        var p = kit.Snap.At(PostCell, x, y);
        if (MathF.Sqrt((p.X - PostCentre.X) * (p.X - PostCentre.X) + (p.Y - PostCentre.Y) * (p.Y - PostCentre.Y)) > 500)
            throw new InvalidOperationException($"BC02: the post's navmesh near {x},{y} lies outside the house ({p.X},{p.Y})");
        return p;
    }

    // E-package: a copy of a vanilla package, its location (when it has one) set to a marker, gated on the stage.
    static Package Pack(SkyrimMod mod, List<ISkyrimModGetter> mods, string id, string from, Quest q, PlacedObject? at, int radius, params ConditionFloat[] conds)
    {
        var p = mods[0].Packages.First(x => x.EditorID == from).Duplicate(mod.GetNextFormKey());
        p.EditorID = id; p.OwnerQuest.SetTo(q.FormKey); p.Conditions.Clear(); p.Conditions.AddRange(conds);
        p.ScheduleHour = -1; p.ScheduleDurationInMinutes = 0;
        if (at != null)
            foreach (var d in p.Data.Values.OfType<PackageDataLocation>().Take(1))
            {
                d.Location = new LocationTargetRadius { Target = new LocationTarget(), Radius = (uint)radius };
                ((LocationTarget)d.Location.Target).Link.SetTo(at.FormKey);
            }
        mod.Packages.Add(p); return p;
    }
    static ConditionFloat Or(ConditionFloat c) { c.Flags = Condition.Flag.OR; return c; }
    static ConditionFloat Hour(CompareOperator op, float h) => C(new GetCurrentTimeConditionData(), op, h);
    static ConditionFloat Speech(CompareOperator op, float n) { var d = new GetActorValueConditionData { ActorValue = ActorValue.Speech, RunOnType = Condition.RunOnType.Reference }; d.Reference.SetTo(PlayerRef); return C(d, op, n); }
    static ConditionFloat Has(FormKey item, float n) { var d = new GetItemCountConditionData { RunOnType = Condition.RunOnType.Reference }; d.Reference.SetTo(PlayerRef); d.ItemOrList.Link.SetTo(item); return C(d, CompareOperator.GreaterThanOrEqualTo, n); }

    // BC01: Never-Sold's estate topic in her house (0 -> 10, the debt book's parent enabled); she walks to the landing by
    // her alias's sandbox package; the book given to her there (10 -> 90), or Rows-For-Another's channel topic after dark
    // (10 -> 40), whose alias then follows the player to the channel-end zone (40 -> 91). Both women are essential.
    static Quest Bc01(SkyrimMod mod, List<ISkyrimModGetter> mods, Kit kit, PlacedNpc patronRef)
    {
        const string id = "quest.bc.bc01";
        var q = NewQuest(mod, "ARG_BC01", "Four Months for a Boat", id, [10, 40, 90, 91, 94], [90, 91, 94]);
        var debtor = Person(kit, "ARG_BC01_RowsForAnother", "Rows-For-Another", true, 5);
        var steward = Person(kit, "ARG_BC01_HulmTei", "Hulm-Tei", false, 6);
        var man = Person(kit, "ARG_BC01_EstateMan", "Estate Man", false, 5);
        var book = mod.Books.AddNew("ARG_BC01_DebtBook");
        book.Name = "Debt Book of the Estate"; book.Value = 0; book.Weight = 1;
        book.Model = new Model { File = mods[0].Books.First(b => b.FormKey == Journal).Model!.File.DataRelativePath.Path };
        book.BookText = DebtBookText;

        // The landing: the bank of 095465 above the shallows (navmesh 0ACD06, z about 20), the channel north-east of it.
        var chestAt = kit.Snap.At(Landing, 128960, -46420);
        var stewardAt = kit.Snap.At(Landing, 129000, -46640);
        var debtorAt = kit.Snap.At(Landing, 128880, -46230);
        var men = new[] { kit.Snap.At(Landing, 129110, -46950), kit.Snap.At(Landing, 128810, -45910) };
        var waitAt = kit.Snap.At(Landing, 128900, -46500);
        var endAt = kit.Snap.At(Landing, 130900, -45250);
        var homeAt = kit.Snap.At(HouseExt, 134450, -56350);
        var chest = kit.Marker("ARG_BC01_ChestRef", chestAt);
        chest.Base.SetTo(StrongBox); chest.Lock = new LockData { Level = LockLevel.Apprentice };
        chest.Owner.SetTo(steward.FormKey);
        var debtorRef = kit.Actor("ARG_BC01_RowsForAnotherRef", debtor, debtorAt);
        var stewardRef = kit.Actor("ARG_BC01_HulmTeiRef", steward, stewardAt);
        var menRefs = men.Select((p, i) => kit.Actor($"ARG_BC01_EstateMan{i + 1}Ref", man, p)).ToList();
        var wait = kit.Marker("ARG_BC01_LandingMarker", waitAt);
        var home = kit.Marker("ARG_BC01_BlackroseMarker", homeAt);
        var zone = kit.Zone("ARG_BC01_ChannelEndZone", new P3Float(endAt.X, endAt.Y, endAt.Z + 100), new P3Float(500, 500, 400), q, 40, 91);
        kit.World.TopCell!.Persistent.AddRange([chest,debtorRef, stewardRef, .. menRefs, wait, home, zone]);

        Forced(q, B1Patron, "Patron", patronRef.FormKey, QuestAlias.Flag.Essential).PackageData.Add(
            Pack(mod, mods, "ARG_BC01_PatronAtLanding", "GledaSandboxEditorLocation512", q, wait, 400, StageIs(q, CompareOperator.GreaterThanOrEqualTo, 10)).ToLink());
        Forced(q, B1Debtor, "Debtor", debtorRef.FormKey, QuestAlias.Flag.Essential).PackageData.Add(
            Pack(mod, mods, "ARG_BC01_DebtorFollow", "FollowPlayer", q, null, 0, StageIs(q, CompareOperator.EqualTo, 40)).ToLink());
        Forced(q, B1Steward, "Steward", stewardRef.FormKey, QuestAlias.Flag.Protected);
        Forced(q, B1Chest, "Chest", chest.FormKey);
        // The book goes into the chest by stage 10's fragment (E-item: Chest.AddItem), so it is absent before 10.
        q.VirtualMachineAdapter = new QuestAdapter
        {
            FileName = "ARG_QF_BC01",
            Scripts = { Script("ARG_QF_BC01", Alias("Patron", q, B1Patron), Alias("Debtor", q, B1Debtor), Alias("Chest", q, B1Chest),
                Obj("DebtBook", book.FormKey), Obj("BlackroseMarker", home.FormKey), Obj("ChannelEndZone", zone.FormKey),
                Obj("Gold001", Gold), Obj("ChainbreakersStanding", standing!.FormKey), Obj("AchievementsQuest", Achievements)) },
            Aliases = { AliasScript(q, B1Patron, OnDeath(q, 10, 94)), AliasScript(q, B1Debtor, OnDeath(q, 10, 94)) },
        };
        Fragments(q, "ARG_QF_BC01", [10, 40, 90, 91, 94]);

        var lines = Lines("bc01");
        var isPatron = IsId(patronRef.Base.FormKey); var isDebtor = IsId(debtor.FormKey); var isSteward = IsId(steward.FormKey);
        TopicV(mod, q, "BC01", lines, "topic.bc01-the-estate", isPatron, (10, [StageIs(q, CompareOperator.EqualTo, 0)], null),
            (null, [StageIs(q, CompareOperator.GreaterThanOrEqualTo, 10)], null));
        TopicV(mod, q, "BC01", lines, "topic.bc01-the-book", isSteward, (null, [StageIs(q, CompareOperator.EqualTo, 10)], null));
        // C-time and C-detected (review F1): night is 21:00 to 5:00 (GetCurrentTime >= 21 OR < 5), and neither the steward
        // nor an estate man detects the player; otherwise the second info (first match wins): not in daylight, not watched.
        ConditionFloat Unseen(PlacedNpc by) { var d = new GetDetectedConditionData { RunOnType = Condition.RunOnType.Reference }; d.Reference.SetTo(by.FormKey); d.TargetNpc.Link.SetTo(PlayerRef); return C(d, CompareOperator.EqualTo, 0); }
        TopicV(mod, q, "BC01", lines, "topic.bc01-cut-loose", isDebtor,
            (40, [StageIs(q, CompareOperator.EqualTo, 10), Or(Hour(CompareOperator.GreaterThanOrEqualTo, 21)), Hour(CompareOperator.LessThan, 5),
                Unseen(stewardRef), .. menRefs.Select(Unseen)], null),
            (null, [StageIs(q, CompareOperator.EqualTo, 10)], "day"));
        TopicV(mod, q, "BC01", lines, "topic.bc01-bring-down", isPatron, (90, [StageIs(q, CompareOperator.EqualTo, 10), Has(book.FormKey, 1)], null));
        // Rows-For-Another free of the book after either ending (90 the book brought down, 91 out by the channel).
        AfterHello(mod, q, "ARG_BC01_AfterHello", (debtorRef.FormKey, After("bc01", "rows-for-another"), [90, 91]));
        return q;
    }

    // BC02 (after BC01 at 90 or 91): Never-Sold's fire topic (0 -> 20: smoke and the three held enabled); Tsaxi's gate
    // topic at Speech 25 or the zone inside the post (20 -> 30); a 'come with me' topic (30 -> 31, 32 or 33: the other two
    // disabled, the chosen follows); the exit zone at the gate for the chosen (31 -> 91, 32 -> 92, 33 -> 93); the chosen's
    // death (-> 94).
    static void Bc02(SkyrimMod mod, List<ISkyrimModGetter> mods, Kit kit, PlacedNpc patronRef, Quest bc01)
    {
        const string id = "quest.bc.bc02";
        var q = NewQuest(mod, "ARG_BC02", "One Out of the Smoke", id, [20, 30, 31, 32, 33, 91, 92, 93, 94], [91, 92, 93, 94]);
        var keeper = Person(kit, "ARG_BC02_ThirdBornTsaxi", "Third-Born Tsaxi", false, 8);
        var keeper2 = Person(kit, "ARG_BC02_GateKeeper", "Gate-Keeper", false, 6);
        var held = new[]
        {
            Person(kit, "ARG_BC02_SaysItPlain", "Says-It-Plain", false, 4),
            Person(kit, "ARG_BC02_HidesInReeds", "Hides-In-Reeds", true, 5),
            Person(kit, "ARG_BC02_KeepsTheOldCount", "Keeps-The-Old-Count", true, 4),
        };
        string[] key = ["Speaker", "Killer", "Mother"]; string[] topic = ["speaker", "killer", "mother"];
        uint[] alias = [B2Speaker, B2Killer, B2Mother];

        var gateAt = kit.Snap.At(PostCell, GateAt.X, GateAt.Y);
        var gate2At = kit.Snap.At(PostCell, GateAt.X, GateAt.Y + 200);
        var heldAt = HeldAt.Select(p => Inside(kit, p.X, p.Y)).ToArray();
        var keepFloor = Inside(kit, PostCentre.X, PostCentre.Y);
        var smokeParent = kit.Marker("ARG_BC02_SmokeParent", new P3Float(keepFloor.X, keepFloor.Y, keepFloor.Z - 200), 0xC00);
        var smoke = heldAt.Append(keepFloor).Select((p, i) =>
        {
            var s = kit.Marker($"ARG_BC02_Smoke{i + 1}", new P3Float(p.X, p.Y, p.Z + 150));
            s.Base.SetTo(Smoke); s.EnableParent = new EnableParent(); s.EnableParent.Reference.SetTo(smokeParent.FormKey);
            return s;
        }).ToList();
        var parents = heldAt.Select((p, i) => kit.Marker($"ARG_BC02_{key[i]}Parent", new P3Float(p.X, p.Y, p.Z - 200), 0xC00)).ToArray();
        var heldRefs = held.Select((b, i) => kit.Actor($"ARG_BC02_{key[i]}Ref", b, heldAt[i], parents[i])).ToArray();
        var keeperRef = kit.Actor("ARG_BC02_TsaxiRef", keeper, gateAt);
        var keeper2Ref = kit.Actor("ARG_BC02_GateKeeperRef", keeper2, gate2At);
        var inZone = kit.Zone("ARG_BC02_InZone", new P3Float(keepFloor.X, keepFloor.Y, keepFloor.Z + 100), new P3Float(450, 450, 300), q, 20, 30);
        var outZones = Enumerable.Range(0, 3).Select(i =>
            kit.Zone($"ARG_BC02_Out{key[i]}Zone", new P3Float(gateAt.X, gateAt.Y, gateAt.Z + 100), new P3Float(600, 600, 400), q, 31 + i, 91 + i)).ToArray();
        kit.World.TopCell!.Persistent.AddRange([smokeParent, .. smoke, .. parents, .. heldRefs, keeperRef, keeper2Ref, inZone, .. outZones]);

        Forced(q, B2Patron, "Patron", patronRef.FormKey, QuestAlias.Flag.Essential);
        Forced(q, B2Keeper, "GateKeeper", keeperRef.FormKey, QuestAlias.Flag.Essential);
        for (var i = 0; i < 3; i++)
            Forced(q, alias[i], key[i], heldRefs[i].FormKey, QuestAlias.Flag.Protected | QuestAlias.Flag.AllowDisabled).PackageData.Add(
                Pack(mod, mods, $"ARG_BC02_{key[i]}Follow", "FollowPlayer", q, null, 0, StageIs(q, CompareOperator.EqualTo, 31 + i)).ToLink());
        q.VirtualMachineAdapter = new QuestAdapter
        {
            FileName = "ARG_QF_BC02",
            Scripts = { Script("ARG_QF_BC02", Obj("SmokeParent", smokeParent.FormKey), Obj("SpeakerParent", parents[0].FormKey),
                Obj("KillerParent", parents[1].FormKey), Obj("MotherParent", parents[2].FormKey),
                Obj("ChainbreakersStanding", standing!.FormKey), Obj("AchievementsQuest", Achievements)) },
        };
        for (var i = 0; i < 3; i++) q.VirtualMachineAdapter.Aliases.Add(AliasScript(q, alias[i], OnDeath(q, 30, 94)));
        q.VirtualMachineAdapter.Aliases.Add(AliasScript(q, B2Keeper, OnDeath(q, 20, 94)));
        q.VirtualMachineAdapter.Aliases.Add(AliasScript(q, B2Patron, OnDeath(q, 20, 94)));
        Fragments(q, "ARG_QF_BC02", [20, 30, 31, 32, 33, 91, 92, 93, 94]);

        var lines = Lines("bc02");
        TopicV(mod, q, "BC02", lines, "topic.bc02-the-fire", IsId(patronRef.Base.FormKey),
            (20, [StageIs(q, CompareOperator.EqualTo, 0), StageIs(bc01, CompareOperator.GreaterThanOrEqualTo, 90)], null),
            (null, [StageIs(q, CompareOperator.GreaterThanOrEqualTo, 20)], null));
        TopicV(mod, q, "BC02", lines, "topic.bc02-the-gate", IsId(keeper.FormKey),
            (30, [StageIs(q, CompareOperator.EqualTo, 20), Speech(CompareOperator.GreaterThanOrEqualTo, 25)], null),
            (null, [StageIs(q, CompareOperator.EqualTo, 20), Speech(CompareOperator.LessThan, 25)], "fail"));
        for (var i = 0; i < 3; i++)
            TopicV(mod, q, "BC02", lines, $"topic.bc02-come-{topic[i]}", IsId(held[i].FormKey), (31 + i, [StageIs(q, CompareOperator.EqualTo, 30)], null));
        // Review F1: the way out past Tsaxi at Speech 25 (31, 32, 33 -> 91, 92, 93), or below it a plain refusal.
        TopicV(mod, q, "BC02", lines, "topic.bc02-let-by", IsId(keeper.FormKey),
            (91, [StageIs(q, CompareOperator.EqualTo, 31), Speech(CompareOperator.GreaterThanOrEqualTo, 25)], null),
            (92, [StageIs(q, CompareOperator.EqualTo, 32), Speech(CompareOperator.GreaterThanOrEqualTo, 25)], null),
            (93, [StageIs(q, CompareOperator.EqualTo, 33), Speech(CompareOperator.GreaterThanOrEqualTo, 25)], null),
            (null, [StageIs(q, CompareOperator.GreaterThanOrEqualTo, 31), StageIs(q, CompareOperator.LessThanOrEqualTo, 33), Speech(CompareOperator.LessThan, 25)], "fail"));
        // The one brought out of the smoke greets the player after their own ending (91, 92 or 93).
        string[] writer = ["says-it-plain", "hides-in-reeds", "keeps-the-old-count"];
        AfterHello(mod, q, "ARG_BC02_AfterHello", [.. Enumerable.Range(0, 3).Select(i => (heldRefs[i].FormKey, After("bc02", writer[i]), new[] { 91 + i }))]);
    }

    // BC03: Heavy-Rope's last-season topic (0 -> 10, once BC01 is at 90 or more); Ussa-Rekh's season topic opens the sides;
    // the tokens topic (10 -> 20) or the refusal topic (10 -> 30); the tokens given back (20 -> 90, standing +10); Heavy-Rope
    // talked down with Speechcraft 30 (30 -> 91) or paid 50 gold (30 -> 92); either man's death (10, 20, 30 -> 94).
    static void Bc03(SkyrimMod mod, List<ISkyrimModGetter> mods, Kit kit, Quest bc01)
    {
        const string id = "quest.bc.bc03";
        var q = NewQuest(mod, "ARG_BC03", "The Broker's Mercy", id, [10, 20, 30, 90, 91, 92, 94], [90, 91, 92, 94]);
        var ussa = Person(kit, "ARG_BC03_UssaRekh", "Ussa-Rekh", false, 10);
        var rope = Person(kit, "ARG_BC03_HeavyRope", "Heavy-Rope", false, 8);
        var tokens = mod.MiscItems.AddNew("ARG_BC03_Tokens");
        tokens.Name = "Carved Tokens"; tokens.Value = 0; tokens.Weight = 0.1f;
        tokens.Model = new Model { File = mods[0].MiscItems.First(m => m.FormKey == OlavaToken).Model!.File.DataRelativePath.Path };
        var heard = mod.Globals.AddNewShort("ARG_BC03_SeasonHeard"); heard.Data = 0;

        // On the dock among the crews (navmesh 0A7784): Ussa-Rekh with his chest beside him, Heavy-Rope a few steps off.
        var ussaAt = kit.Snap.At(Dock2, 48450, -5900);
        var chestAt = kit.Snap.At(Dock2, 48520, -5880);
        var ropeAt = kit.Snap.At(Dock2, 48700, -6100);
        var ussaRef = kit.Actor("ARG_BC03_UssaRekhRef", ussa, ussaAt);
        var ropeRef = kit.Actor("ARG_BC03_HeavyRopeRef", rope, ropeAt);
        var chest = kit.Marker("ARG_BC03_ChestRef", chestAt);
        chest.Base.SetTo(StrongBox);
        chest.Lock = new LockData { Level = LockLevel.Novice };
        chest.Owner.SetTo(ussa.FormKey);
        kit.World.TopCell!.Persistent.AddRange([ussaRef, ropeRef, chest]);

        Forced(q, B3Ussa, "Broker", ussaRef.FormKey, QuestAlias.Flag.Essential);
        Forced(q, B3Rope, "CrewBoss", ropeRef.FormKey, QuestAlias.Flag.Essential);
        Forced(q, B3Chest, "Chest", chest.FormKey);
        // F1: the tokens a Quest Object from stage 0, created in the chest by the alias (Bethesda's quest-item shape).
        q.Aliases.Add(new QuestAlias
        {
            ID = B3Tokens, Type = QuestAlias.TypeEnum.Reference, Name = "Tokens", Flags = QuestAlias.Flag.QuestObject,
            CreateReferenceToObject = new CreateReferenceToObject { Object = tokens.ToLink<ISkyrimMajorRecordGetter>(), AliasID = (short)B3Chest, Create = CreateReferenceToObject.CreateEnum.In, Level = Level.Easy },
        });
        q.VirtualMachineAdapter = new QuestAdapter
        {
            FileName = "ARG_QF_BC03",
            Scripts = { Script("ARG_QF_BC03", Alias("Broker", q, B3Ussa), Alias("CrewBoss", q, B3Rope), Obj("Tokens", tokens.FormKey),
                Obj("Gold001", Gold), Obj("ChainbreakersStanding", standing!.FormKey), Obj("AchievementsQuest", Achievements)) },
            Aliases = { AliasScript(q, B3Ussa, OnDeath(q, 10, 94)), AliasScript(q, B3Rope, OnDeath(q, 10, 94)) },
        };
        Fragments(q, "ARG_QF_BC03", [10, 20, 30, 90, 91, 92, 94]);

        ConditionFloat[] open = [StageIs(q, CompareOperator.EqualTo, 0), StageIs(bc01, CompareOperator.GreaterThanOrEqualTo, 90)];
        ConditionFloat Heard() { var d = new GetGlobalValueConditionData(); d.Global.Link.SetTo(heard.FormKey); return C(d, CompareOperator.EqualTo, 1); }
        var lines = Lines("bc03");
        var isRope = IsId(rope.FormKey); var isUssa = IsId(ussa.FormKey);
        TopicV(mod, q, "BC03", lines, "topic.bc03-last-season", isRope, (10, open, null), (null, [StageIs(q, CompareOperator.GreaterThanOrEqualTo, 10)], null));
        TopicV(mod, q, "BC03", lines, "topic.bc03-the-season", isUssa, (null, [StageIs(q, CompareOperator.GreaterThanOrEqualTo, 10)], null));
        // F4: hearing the season opens the sides; each of its infos' (every band's) fragment sets ARG_BC03_SeasonHeard (E-global).
        foreach (var season in mod.DialogTopics.First(t => t.EditorID == "ARG_BC03_TheSeason").Responses)
        season.VirtualMachineAdapter = new DialogResponsesAdapter
        {
            Scripts = { Script("TIF_ARG_BC03_Season", Obj("SeasonHeard", heard.FormKey)) },
            ScriptFragments = new ScriptFragments { FileName = "TIF_ARG_BC03_Season", OnEnd = new ScriptFragment { ScriptName = "TIF_ARG_BC03_Season", FragmentName = "Fragment_0" } },
        };
        TopicV(mod, q, "BC03", lines, "topic.bc03-the-tokens", isRope, (20, [StageIs(q, CompareOperator.EqualTo, 10), Heard()], null));
        TopicV(mod, q, "BC03", lines, "topic.bc03-brawl", isRope, (30, [StageIs(q, CompareOperator.EqualTo, 10), Heard()], null));
        TopicV(mod, q, "BC03", lines, "topic.bc03-break", isRope, (90, [StageIs(q, CompareOperator.EqualTo, 20), Has(tokens.FormKey, 1)], null));
        TopicV(mod, q, "BC03", lines, "topic.bc03-yield-talk", isRope,
            (91, [StageIs(q, CompareOperator.EqualTo, 30), Speech(CompareOperator.GreaterThanOrEqualTo, 30)], null),
            (null, [StageIs(q, CompareOperator.EqualTo, 30), Speech(CompareOperator.LessThan, 30)], "fail"));
        TopicV(mod, q, "BC03", lines, "topic.bc03-yield-pay", isRope, (92, [StageIs(q, CompareOperator.EqualTo, 30), Has(Gold, 50)], null));
    }

    // The steward's book (item.bc01.debt-book, clue k2): every line true (fact.bc01.book-true, fact.bc01.boat-owing).
    const string DebtBookText = "<font face='$HandwrittenFont'>Rows-For-Another. One boat from the stores. Owing: four months' work.<br><br>"
        + "First season: her food, one month. The boat's upkeep, one month. Sick, nine days.<br><br>"
        + "Every season since, the same lines again.<br><br>"
        + "Owing this season: nineteen months.</font>";
}
