using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;
using Noggog;

// The "Argonia Travel" lesser power (owner: reach the new world on a gamepad, no console). One start-game-enabled quest
// gives the power (a new game, and any save the plugin is added to); casting it runs ANW_TravelEffect, which opens the
// root page; each page is a message box (<= 10 buttons) held by a quest holding ANW_TravelPage, whose buttons open
// another page or move the player to a named cell as `coc` does (Debug.CenterOnCell). The pages are
// newworld/sources/travel/menu.json (tools/newworld/travel_menu.py): a new spot is a data row. Every record's id is its
// name's in the registry (kind "base"). Scripts: papyrus/ANW_Travel*.psc.
static class NewWorldTravel
{
    const int MaxButtons = 10;

    public static void Attach(SkyrimMod mod, FormIds ids, string menuPath)
    {
        var doc = JsonDocument.Parse(File.ReadAllText(menuPath)).RootElement;
        var root = doc.GetProperty("root").GetString()!;
        var pages = doc.GetProperty("pages").EnumerateObject().OrderBy(p => p.Name, StringComparer.Ordinal).ToList();
        FormKey K(string name) => new(mod.ModKey, ids.Take("base", "travel:" + name));
        foreach (var p in pages)
        {
            var n = p.Value.GetProperty("buttons").GetArrayLength();
            if (n is < 1 or > MaxButtons) throw new InvalidDataException($"travel menu page {p.Name}: {n} buttons (1 to {MaxButtons})");
        }
        // pages first: a quest and a message each
        var quest = new Dictionary<string, Quest>();
        var msg = new Dictionary<string, Message>();
        foreach (var p in pages)
        {
            var m = new Message(K("msg:" + p.Name), SkyrimRelease.SkyrimSE)
            {
                EditorID = "ANW_TravelMsg_" + Edid(p.Name),
                Description = new TranslatedString(Language.English, p.Value.GetProperty("title").GetString()!),
                Flags = Message.Flag.MessageBox,
                DisplayTime = 0,
            };
            foreach (var b in p.Value.GetProperty("buttons").EnumerateArray())
                m.MenuButtons.Add(new MessageButton { Text = new TranslatedString(Language.English, b.GetProperty("label").GetString()!) });
            mod.Messages.Add(m);
            msg[p.Name] = m;
            quest[p.Name] = new Quest(K("page:" + p.Name), SkyrimRelease.SkyrimSE) { EditorID = "ANW_TravelPage_" + Edid(p.Name), Priority = 0 };
        }
        foreach (var p in pages)
        {
            var btn = p.Value.GetProperty("buttons").EnumerateArray().ToList();
            var cells = btn.Select(b => b.TryGetProperty("cell", out var c) ? c.GetString()! : "").ToList();
            var next = btn.Select(b => b.TryGetProperty("page", out var t) ? quest[t.GetString() ?? throw new InvalidDataException("page")].ToLink() : null).ToList();
            var props = new ExtendedList<ScriptProperty>
            {
                new ScriptObjectProperty { Name = "Msg", Object = msg[p.Name].ToLink() },
                new ScriptStringListProperty { Name = "Cells", Data = cells.ToExtendedList() },
                new ScriptObjectListProperty { Name = "Pages", Objects = next.Select(l => new ScriptObjectProperty { Object = new FormLink<ISkyrimMajorRecordGetter>(l is null ? FormKey.Null : l.FormKey) }).ToExtendedList() },
            };
            var q = quest[p.Name];
            q.VirtualMachineAdapter = new QuestAdapter { Scripts = { new ScriptEntry { Name = "ANW_TravelPage", Properties = props } } };
            mod.Quests.Add(q);
        }
        // the power: a script effect whose script opens the root page
        var mgef = new MagicEffect(K("mgef"), SkyrimRelease.SkyrimSE)
        {
            EditorID = "ANW_TravelEffect",
            Name = new TranslatedString(Language.English, "Argonia Travel"),
            Flags = MagicEffect.Flag.NoArea | MagicEffect.Flag.NoDuration | MagicEffect.Flag.NoHitEvent,
            Archetype = new MagicEffectArchetype(MagicEffectArchetype.TypeEnum.Script),
            CastType = CastType.FireAndForget,
            TargetType = TargetType.Self,
            MagicSkill = ActorValue.None,
            ResistValue = ActorValue.None,
            SecondActorValue = ActorValue.None,
            VirtualMachineAdapter = new VirtualMachineAdapter
            {
                Scripts = { new ScriptEntry { Name = "ANW_TravelEffect", Properties = { new ScriptObjectProperty { Name = "Root", Object = quest[root].ToLink() } } } },
            },
        };
        mod.MagicEffects.Add(mgef);
        var spel = new Spell(K("spell"), SkyrimRelease.SkyrimSE)
        {
            EditorID = "ANW_Travel",
            Name = new TranslatedString(Language.English, "Argonia Travel"),
            Description = new TranslatedString(Language.English, "Opens a menu of the new world's places and walk checks: choose one to be there."),
            Type = SpellType.LesserPower,
            CastType = CastType.FireAndForget,
            TargetType = TargetType.Self,
            ChargeTime = 0,
            Effects = { new Effect { BaseEffect = mgef.ToNullableLink(), Data = new EffectData { Magnitude = 0, Area = 0, Duration = 0 } } },
        };
        spel.EquipmentType.SetTo(FormKey.Factory("013F45:Skyrim.esm")); // EitherHand, as Skyrim's lesser powers
        mod.Spells.Add(spel);
        // the quest that hands the power over: start game enabled, so a new game has it and so does any save the file joins
        var give = new Quest(K("give"), SkyrimRelease.SkyrimSE)
        {
            EditorID = "ANW_TravelGive", Flags = Quest.Flag.StartGameEnabled | Quest.Flag.RunOnce, Priority = 0,
            VirtualMachineAdapter = new QuestAdapter { Scripts = { new ScriptEntry { Name = "ANW_TravelGive", Properties = { new ScriptObjectProperty { Name = "Power", Object = spel.ToLink() } } } } },
        };
        mod.Quests.Add(give);
        Console.WriteLine($"  travel menu: {pages.Count} pages, the power {spel.EditorID}, root {root}");
    }

    // `newworld travel <menu.json> <scratch.esm>`: the records written to a scratch file and read back (the menu's own proof).
    public static int Try(string menuPath, string outPath)
    {
        var key = ModKey.FromFileName("ArgoniaNewWorld.esm");
        var mod = new SkyrimMod(key, SkyrimRelease.SkyrimSE);
        mod.ModHeader.Flags |= SkyrimModHeader.HeaderFlag.Master;
        Attach(mod, FormIds.Load(null), menuPath);
        mod.BeginWrite.ToPath(outPath).WithLoadOrder(new[] { ModKey.FromFileName("Skyrim.esm"), key }).WithNoDataFolder().Write();
        using var back = SkyrimMod.CreateFromBinaryOverlay(outPath, SkyrimRelease.SkyrimSE);
        var pages = back.Quests.Count(q => q.EditorID!.StartsWith("ANW_TravelPage_"));
        var btn = back.Messages.Sum(m => m.MenuButtons.Count);
        var bad = back.Messages.Count != pages || back.Spells.Count != 1 || back.MagicEffects.Count != 1 || back.Quests.Count != pages + 1
            || back.Quests.Any(q => q.VirtualMachineAdapter is null) || back.MagicEffects.First().VirtualMachineAdapter is null;
        Console.WriteLine($"newworld travel: {pages} pages, {btn} buttons, {back.Quests.Count} quests, {back.Spells.Count} spell: " + (bad ? "FAIL" : "ok"));
        return bad ? 1 : 0;
    }

    static string Edid(string page) => new string(page.Select(c => char.IsLetterOrDigit(c) ? c : '_').ToArray());
}
