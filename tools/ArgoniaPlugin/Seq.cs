using Mutagen.Bethesda;
using Mutagen.Bethesda.Skyrim;

// seq <esp> <out.seq>: the plugin's SEQ file, Data\SEQ\<plugin>.seq. The engine starts the quests a SEQ lists before
// the game runs, so a Start Game Enabled quest's dialogue is there from a new game's first frame; one missing from it
// has no dialogue until a save is loaded (owner walk 4, 2026-11-08: every ARG_Talk talker silent on a new game).
// Bethesda ships one per master (skyrim.seq, update.seq, dawnguard.seq ... in Skyrim - Misc.bsa): a flat list of
// little-endian form ids, file-relative (Update.esm's read 01xxxxxx, Dawnguard.esm's 02xxxxxx). Ours lists every Start
// Game Enabled quest the plugin defines.
static class Seq
{
    public static int Run(string esp, string outPath)
    {
        var mod = SkyrimMod.CreateFromBinaryOverlay(esp, SkyrimRelease.SkyrimSE, Survey.NoStrings);
        uint index = (uint)mod.ModHeader.MasterReferences.Count;
        var quests = mod.Quests.Where(q => q.FormKey.ModKey == mod.ModKey && q.Flags.HasFlag(Quest.Flag.StartGameEnabled)).OrderBy(q => q.FormKey.ID).ToList();
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(outPath))!);
        using (var w = new BinaryWriter(File.Create(outPath)))
            foreach (var q in quests) w.Write((index << 24) | q.FormKey.ID);
        Console.WriteLine($"seq: {outPath}, {quests.Count} start-game quests ({string.Join(", ", quests.Select(q => q.EditorID))})");
        return quests.Count > 0 ? 0 : 1;
    }
}
