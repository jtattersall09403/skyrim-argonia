using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using static QuestKit;

// The new game's world: BM&V's barge hold, where character creation runs, and the way from its stair door to Lilmoth's pier.
// Called by Generate after Talk; no quest code (the opening's quests MQ01 and MQ03 are quest forms).
static class Opening
{
    // The hold cell and its navmesh (main deck z 7010), the hold's stair door (BM&V's copy of the ship 01Ship) and its far
    // door, the pier door at the dock's foot, and the top-of-stairs door whose arrival spot the stair door takes.
    public static readonly FormKey HoldCell = K("0F9178:Black Marsh.esm"), HoldNav = K("0F9179:Black Marsh.esm"),
        HoldDoor = K("0F92EC:Black Marsh.esm"), HoldDoorFar = K("0F9399:Black Marsh.esm"), PierDoor = K("005AB4:Black Marsh.esm"),
        StairTop = K("039827:Black Marsh.esm"), Welcome = K("03B21E:Black Marsh.esm");
    public static readonly string[] Valenwood = ["0BCC51:Valenwood.esp", "0F0F3E:Valenwood.esp"];
    public static readonly FormKey Tunic = K("03C9FE:Skyrim.esm"), Footwraps = K("03CA00:Skyrim.esm");
    public static PlacedObject StartMarker = null!;

    public static void Add(SkyrimMod mod, List<ISkyrimModGetter> mods, Worldspace world)
    {
        var kit = new QuestKit(mod, mods, "ARG_Opening_");
        // The start marker, on the hold's main deck; the hold cell's location 'Dainty Sload' cleared.
        StartMarker = kit.Marker("StartMarker", kit.Snap(HoldNav, 2750, 3900, 7010));
        var hold = kit.Interior(HoldCell);
        hold.Location.Clear();
        hold.Persistent.Add(StartMarker);
        // The hold's way out: the stair door 0F92EC paired both ways with the pier door 005AB4 (the arrival in the hold is
        // Black Marsh North's own in front of 0AA6C9; on the pier, the far door 0F9399's old one); the far door loses its
        // teleport and opens onto its room. Nothing locks the stair door.
        var holdTo = ((IPlacedObjectGetter)kit.Placed[HoldDoorFar].rec).TeleportDestination!;
        var stairIn = ((IPlacedObjectGetter)kit.Placed[StairTop].rec).TeleportDestination!;
        var stairDoor = (PlacedObject)((IPlacedObjectGetter)kit.Placed[HoldDoor].rec).DeepCopy();
        stairDoor.MajorRecordFlagsRaw |= 0x400;
        stairDoor.TeleportDestination = new TeleportDestination { Position = holdTo.Position, Rotation = holdTo.Rotation };
        stairDoor.TeleportDestination.Door.SetTo(PierDoor);
        var farDoor = (PlacedObject)((IPlacedObjectGetter)kit.Placed[HoldDoorFar].rec).DeepCopy();
        farDoor.TeleportDestination = null; farDoor.MajorRecordFlagsRaw |= 0x400;
        var pierDoor = (PlacedObject)((IPlacedObjectGetter)kit.Placed[PierDoor].rec).DeepCopy();
        pierDoor.MajorRecordFlagsRaw |= 0x400;
        pierDoor.TeleportDestination = new TeleportDestination { Position = stairIn.Position, Rotation = stairIn.Rotation };
        pierDoor.TeleportDestination.Door.SetTo(HoldDoor);
        hold.Persistent.AddRange([stairDoor, farDoor]);
        world.TopCell!.Persistent.Add(pierDoor);
        // BM&V's own openings (the captain's welcome, Valenwood's two start quests) never start with a new game of ours
        var quests = Survey.Winners<IQuestGetter>(mods);
        foreach (var k in Valenwood.Select(v => FormKey.Factory(v)).Append(Welcome))
        {
            var q = quests[k].rec.DeepCopy();
            q.Flags &= ~Quest.Flag.StartGameEnabled;
            mod.Quests.Add(q);
        }
    }
}
