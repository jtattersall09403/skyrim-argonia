// InventoryDump: the Mutagen half of the immersion inventory (decision 0006 §1). Read-only over the load order.
//   dump     --data DIR --load-order a.esm,b.esm,... [--root PATH] [--block WRLD:x0,y0,x1,y1] [--block-cells fk,...] --out FILE.jsonl
//            --block adds `block`: the walk depth from the block's cells (that worldspace's grid box plus the named
//            interiors) by what the player meets there: a cell its refs, a ref its base, a base its parts, five hops,
//            never through a faction, quest, topic, location, package, keyword or another cell (Dump.Stop)
//   archives --data DIR --archives "x.bsa,y.bsa" --out FILE.json   (paths in each archive + UI translate keys)
//   fixture  --out DIR                                             (two tiny plugins, no game data, for the reachability test)
// Rows carry identifiers only (type, FormKey, editor id, plugins); never names, text or file data (decision 0003).
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Archives;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Binary.Parameters;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;

static int Fail(string m) { Console.Error.WriteLine(m); return 2; }
string? Arg(string name) { var i = Array.IndexOf(args, name); return i >= 0 && i + 1 < args.Length ? args[i + 1] : null; }
if (args.Length == 0) return Fail("usage: InventoryDump dump|archives|fixture ...");
var data = Arg("--data") ?? Path.Combine(Environment.GetEnvironmentVariable("HOME") ?? "", "games/skyrimse/Data");
var outPath = Arg("--out") ?? throw new ArgumentException("--out required");
var json = new JsonSerializerOptions { WriteIndented = false };

switch (args[0])
{
    case "dump": return Dump.Run(data, (Arg("--load-order") ?? "Skyrim.esm").Split(',', StringSplitOptions.RemoveEmptyEntries), Arg("--root"), outPath,
        Arg("--block"), (Arg("--block-cells") ?? "").Split(',', StringSplitOptions.RemoveEmptyEntries));
    case "archives":
    {
        var result = new Dictionary<string, object>();
        foreach (var name in (Arg("--archives") ?? "").Split(',', StringSplitOptions.RemoveEmptyEntries))
        {
            var reader = Archive.CreateReader(GameRelease.SkyrimSE, Path.Combine(data, name));
            var files = reader.Files.ToList();
            var keys = new SortedSet<string>(StringComparer.Ordinal);
            foreach (var f in files.Where(f => f.Path.Replace('\\', '/').ToLowerInvariant() == "interface/translate_english.txt"))
            {
                var text = System.Text.Encoding.Unicode.GetString(f.GetBytes());  // UTF-16LE: "$KEY<TAB>text"
                foreach (var line in text.Split('\n'))
                {
                    var key = line.Split('\t')[0].Trim().TrimStart('﻿');
                    if (key.StartsWith('$')) keys.Add(key);
                }
            }
            result[name] = new { files = files.Select(f => f.Path.Replace('\\', '/').ToLowerInvariant()).OrderBy(p => p, StringComparer.Ordinal).ToList(), translate_keys = keys };
        }
        File.WriteAllText(outPath, JsonSerializer.Serialize(result, json));
        return 0;
    }
    case "fixture": return Fixture.Write(outPath);
    default: return Fail($"unknown command {args[0]}");
}

static class Sig
{
    static readonly Dictionary<Type, string> Cache = new();
    // The four-letter record signature of a major record: the static TriggeringRecordType of its registration.
    public static string Of(IMajorRecordGetter r)
    {
        var reg = r.Registration;
        var t = reg.GetType();
        lock (Cache)
        {
            if (Cache.TryGetValue(t, out var s)) return s;
            var f = t.GetField("TriggeringRecordType") ?? throw new InvalidOperationException($"no signature on {t}");
            s = f.GetValue(null)!.ToString()!;
            Cache[t] = s;
            return s;
        }
    }
}

static class Dump
{
    // 0006 §1's list, plus the item types it implies and the containers places are made of.
    public static readonly HashSet<string> Types = new()
    {
        "WEAP","ARMO","MISC","BOOK","NPC_","STAT","FURN","ACTI","DOOR","CONT","LIGH","FLOR","TREE","GRAS","LTEX","TXST",
        "WTHR","CLMT","IMGS","SOUN","SNDR","MUSC","MUST","MESG","GMST","LSCR","SPEL","MGEF","PERK","RACE","CLAS","FACT",
        "QUST","DIAL","INFO","WOOP","SHOU","LCTN","REGN","VTYP",
        // implied by "every record the player can be shown": items, ammo, ingredients, scrolls, soul gems, keys,
        // enchantments, ambience (acoustic spaces), sound categories, movable statics, worldspaces and cells
        "AMMO","ALCH","INGR","SCRL","SLGM","KEYM","ENCH","ASPC","SNCT","MSTT","WRLD","CELL",
    };

    // The graph is ids and edges only, built in one streaming pass per plugin (no link cache, no record kept):
    // each record's own links (nested records excluded; the winning override's replace earlier ones), plus the
    // structural edges a plugin's layout implies, unioned across plugins: a cell reaches its contents and its
    // worldspace, a placed reference its cell, a topic its lines, a quest its topics.
    sealed class Graph
    {
        readonly Dictionary<FormKey, int> idx = new();
        public readonly List<FormKey> Keys = new();
        public readonly List<int[]> Own = new();
        public readonly List<List<int>?> Extra = new();
        public int Id(FormKey k)
        {
            if (idx.TryGetValue(k, out var i)) return i;
            idx[k] = i = Keys.Count; Keys.Add(k); Own.Add(Array.Empty<int>()); Extra.Add(null);
            return i;
        }
        public bool TryId(FormKey k, out int i) => idx.TryGetValue(k, out i);
        public void Link(FormKey from, FormKey to)
        {
            if (to.IsNull) return;
            var f = Id(from);
            (Extra[f] ??= new()).Add(Id(to));
        }
    }

    static IEnumerable<ICellGetter> CellsOf(ISkyrimModGetter mod)
    {
        foreach (var b in mod.Cells.Records) foreach (var s in b.SubBlocks) foreach (var c in s.Cells) yield return c;
        foreach (var w in mod.Worldspaces)
        {
            if (w.TopCell != null) yield return w.TopCell;
            foreach (var b in w.SubCells) foreach (var s in b.Items) foreach (var c in s.Items) yield return c;
        }
    }

    // The block walk labels these but never walks out of them: each is a hub that would reach the whole load order.
    public static readonly HashSet<string> Stop = new() { "RACE", "VTYP", "FACT", "QUST", "DIAL", "INFO", "LCTN", "CELL", "WRLD", "PACK", "KYWD", "PERK", "IDLE", "CLAS", "SMQN", "SMBN", "SMEN", "SCEN", "DLBR", "DLVW" };
    public const int BlockDepth = 5;

    public static int Run(string data, string[] order, string? root, string outPath, string? blockBox = null, string[]? blockCells = null)
    {
        string? blockWorld = null; int bx0 = 0, by0 = 0, bx1 = -1, by1 = -1;
        if (blockBox != null)
        {
            var parts = blockBox.Split(':');
            var n = parts[1].Split(',').Select(int.Parse).ToArray();
            (blockWorld, bx0, by0, bx1, by1) = (parts[0], n[0], n[1], n[2], n[3]);
        }
        var interiorSeeds = new HashSet<FormKey>((blockCells ?? Array.Empty<string>()).Select(s => FormKey.Factory(s)));
        var blockSeeds = new HashSet<int>();
        var sigOf = new Dictionary<int, string>();
        var disabled = new HashSet<int>();
        var paths = order.Select(n => n.Contains('/') ? n : Path.Combine(data, n)).ToList();
        if (root != null) paths.Add(root);
        // No text is read (rows hold identifiers only), so point Mutagen's strings lookup at an empty folder:
        // it then never needs plugins.txt, which Linux does not have.
        var noStrings = Directory.CreateTempSubdirectory("argonia-inventory-").FullName;
        var read = new BinaryReadParameters { StringsParam = new Mutagen.Bethesda.Strings.StringsReadParameters { StringsFolderOverride = noStrings, BsaFolderOverride = noStrings } };

        var g = new Graph();
        var rows = new Dictionary<FormKey, Row>();
        var rootSeeds = new List<int>();
        foreach (var path in paths)
        {
            if (!File.Exists(path)) { Console.Error.WriteLine($"missing plugin: {path}"); return 2; }
            using var mod = SkyrimMod.CreateFromBinaryOverlay(path, SkyrimRelease.SkyrimSE, read);
            var isRoot = root != null && path == root;
            foreach (var r in mod.EnumerateMajorRecords())
            {
                var id = g.Id(r.FormKey);
                g.Own[id] = r.EnumerateFormLinks(false).Select(l => l.FormKey).Where(k => !k.IsNull).Distinct().Select(g.Id).ToArray();
                // seeds are our own new records; an override of a vanilla record (the quarantine's quest
                // overrides) counts only if something reaches it
                if (isRoot && r.FormKey.ModKey == mod.ModKey) rootSeeds.Add(id);
                var sig = Sig.Of(r);
                sigOf[id] = sig;
                if (r is IPlacedGetter)  // the winning override decides: Initially Disabled (0x800) is never met
                {
                    if ((r.MajorRecordFlagsRaw & 0x800) != 0) disabled.Add(id); else disabled.Remove(id);
                }
                if (r is IDialogTopicGetter d)
                {
                    foreach (var info in d.Responses) g.Link(d.FormKey, info.FormKey);
                    if (!d.Quest.IsNull) g.Link(d.Quest.FormKey, d.FormKey);
                }
                if (!Types.Contains(sig)) continue;
                if (!rows.TryGetValue(r.FormKey, out var row))
                    rows[r.FormKey] = row = new Row { type = sig, formkey = r.FormKey.ToString(), origin = r.FormKey.ModKey.FileName };
                row.edid = r.EditorID ?? row.edid;
                row.plugins.Add(mod.ModKey.FileName);
                if (r is IQuestGetter q) row.start_enabled = q.Flags.HasFlag(Quest.Flag.StartGameEnabled);
            }
            foreach (var c in CellsOf(mod))
            {
                foreach (var child in c.Persistent.Concat(c.Temporary).Select(x => x.FormKey)
                             .Concat(c.NavigationMeshes.Select(n => n.FormKey))
                             .Concat(c.Landscape != null ? new[] { c.Landscape.FormKey } : Array.Empty<FormKey>()))
                {
                    g.Link(c.FormKey, child);
                    g.Link(child, c.FormKey);
                }
            }
            foreach (var c in CellsOf(mod)) if (interiorSeeds.Contains(c.FormKey)) blockSeeds.Add(g.Id(c.FormKey));
            foreach (var w in mod.Worldspaces)
            {
                if (blockWorld != null && w.EditorID == blockWorld)
                {
                    blockSeeds.Add(g.Id(w.FormKey));
                    if (w.TopCell != null) blockSeeds.Add(g.Id(w.TopCell.FormKey));  // persistent refs live here
                    foreach (var b in w.SubCells) foreach (var s in b.Items) foreach (var c in s.Items)
                        if (c.Grid is { } gr && gr.Point.X >= bx0 && gr.Point.X <= bx1 && gr.Point.Y >= by0 && gr.Point.Y <= by1)
                            blockSeeds.Add(g.Id(c.FormKey));
                }
                if (w.TopCell != null) g.Link(w.TopCell.FormKey, w.FormKey);
                foreach (var b in w.SubCells) foreach (var s in b.Items) foreach (var c in s.Items) g.Link(c.FormKey, w.FormKey);
            }
            GC.Collect(2, GCCollectionMode.Aggressive, true, true);  // each plugin's bytes go before the next is read
        }

        // Reachability: first from every new record of our plugin ("world"), then from the quests that start with the
        // game as their winning override says ("start-quest"), so the quarantine's override drops them.
        var reach = new byte[g.Keys.Count];  // 0 unreached, 1 world, 2 start-quest
        void Walk(IEnumerable<int> seeds, byte label)
        {
            var stack = new Stack<int>();
            foreach (var s in seeds) if (reach[s] == 0) { reach[s] = label; stack.Push(s); }
            while (stack.Count > 0)
            {
                var n = stack.Pop();
                foreach (var m in g.Own[n].Concat(g.Extra[n] ?? Enumerable.Empty<int>()))
                    if (reach[m] == 0) { reach[m] = label; stack.Push(m); }
            }
        }
        Walk(rootSeeds, 1);
        // The block walk: breadth first, so `block` is the fewest hops from the block's cells. Seeds expand (a cell its
        // refs, the worldspace its climate and water); a Stop type or a disabled ref is labelled and not walked out of.
        var depth = new int[g.Keys.Count];
        Array.Fill(depth, -1);
        var via = new int[g.Keys.Count];
        var queue = new Queue<int>();
        foreach (var s in blockSeeds) { depth[s] = 0; queue.Enqueue(s); }
        while (queue.Count > 0)
        {
            var n = queue.Dequeue();
            if (depth[n] >= BlockDepth || disabled.Contains(n)) continue;
            if (depth[n] > 0 && sigOf.TryGetValue(n, out var ns) && Stop.Contains(ns)) continue;
            foreach (var m in g.Own[n].Concat(g.Extra[n] ?? Enumerable.Empty<int>()))
                if (depth[m] < 0 && !disabled.Contains(m)) { depth[m] = depth[n] + 1; via[m] = n; queue.Enqueue(m); }
        }
        Walk(rows.Values.Where(x => x.start_enabled == true).Select(x => g.Id(FormKey.Factory(x.formkey))), 2);

        using var w2 = new StreamWriter(outPath);
        int reached = 0;
        foreach (var (fk, row) in rows.OrderBy(r => r.Value.origin, StringComparer.Ordinal).ThenBy(r => r.Value.type, StringComparer.Ordinal).ThenBy(r => r.Value.formkey, StringComparer.Ordinal))
        {
            row.reach = g.TryId(fk, out var i) ? reach[i] switch { 1 => "world", 2 => "start-quest", _ => null } : null;
            if (row.reach != null) reached++;
            if ((blockBox != null || blockSeeds.Count > 0) && g.TryId(fk, out var j) && depth[j] >= 0)
            {
                row.block = depth[j];
                var path = new List<string>();  // the hops it was met through, nearest first: SIG:formkey
                for (var k = j; depth[k] > 0; k = via[k]) path.Add($"{sigOf.GetValueOrDefault(via[k], "?")}:{g.Keys[via[k]]}");
                if (path.Count > 0) row.block_via = string.Join(" < ", path);
            }
            w2.WriteLine(JsonSerializer.Serialize(row));
        }
        Console.Error.WriteLine($"rows {rows.Count}, graph nodes {g.Keys.Count}, listed rows reached {reached}, peak MB {Environment.WorkingSet / 1048576}");
        return 0;
    }

    public sealed class Row
    {
        public string type { get; set; } = "";
        public string formkey { get; set; } = "";
        public string? edid { get; set; }
        public string origin { get; set; } = "";
        public List<string> plugins { get; set; } = new();
        public bool? start_enabled { get; set; }
        public string? reach { get; set; }
        [System.Text.Json.Serialization.JsonIgnore(Condition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull)]
        public int? block { get; set; }
        [System.Text.Json.Serialization.JsonIgnore(Condition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull)]
        public string? block_via { get; set; }
    }
}

static class Fixture
{
    // Two tiny plugins, no game data: FixtureBase.esm stands in for a vanilla master (a static, a container, a race,
    // a voice type, a static nothing uses, and a start-enabled quest whose alias-free topic is its own); the block
    // FixtureBlock.esp masters it: one interior cell holding the static, the container and an NPC of the race and
    // voice type, one quest, one weapon. Prints the FormKeys the test expects.
    public static int Write(string dir)
    {
        Directory.CreateDirectory(dir);
        var basePath = Path.Combine(dir, "FixtureBase.esm");
        var bm = new SkyrimMod(ModKey.FromFileName("FixtureBase.esm"), SkyrimRelease.SkyrimSE);
        bm.ModHeader.Flags |= SkyrimModHeader.HeaderFlag.Master;
        var rock = bm.Statics.AddNew("BaseRock");
        var unused = bm.Statics.AddNew("BaseUnusedRock");
        var barrel = bm.Containers.AddNew("BaseBarrel");
        var race = bm.Races.AddNew("BaseRace");
        var voice = bm.VoiceTypes.AddNew("BaseVoice");
        var startQuest = bm.Quests.AddNew("BaseStartQuest");
        startQuest.Flags = Quest.Flag.StartGameEnabled;
        var startTopic = bm.DialogTopics.AddNew("BaseStartTopic");
        startTopic.Quest.SetTo(startQuest);
        bm.WriteToBinary(basePath);

        var blockPath = Path.Combine(dir, "FixtureBlock.esp");
        var mod = new SkyrimMod(ModKey.FromFileName("FixtureBlock.esp"), SkyrimRelease.SkyrimSE);
        var cell = new Cell(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE) { EditorID = "FixtureCell", Flags = Cell.Flag.IsInteriorCell };
        cell.Temporary.Add(new PlacedObject(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE) { EditorID = "FixtureRock", Base = new FormLinkNullable<IPlaceableObjectGetter>(rock.FormKey) });
        cell.Temporary.Add(new PlacedObject(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE) { EditorID = "FixtureBarrel", Base = new FormLinkNullable<IPlaceableObjectGetter>(barrel.FormKey) });
        var npc = mod.Npcs.AddNew("FixtureNpc");
        npc.Race.SetTo(race);
        npc.Voice.SetTo(voice);
        cell.Temporary.Add(new PlacedNpc(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE) { EditorID = "FixtureNpcRef", Base = new FormLinkNullable<INpcGetter>(npc.FormKey) });
        var block = new CellBlock { BlockNumber = 0, GroupType = GroupTypeEnum.InteriorCellBlock };
        var sub = new CellSubBlock { BlockNumber = 0, GroupType = GroupTypeEnum.InteriorCellSubBlock };
        sub.Cells.Add(cell); block.SubBlocks.Add(sub); mod.Cells.Records.Add(block);
        var q = mod.Quests.AddNew("FixtureQuest");
        var weap = mod.Weapons.AddNew("FixtureBlade");
        mod.WriteToBinary(blockPath, new BinaryWriteParameters { MastersListOrdering = new MastersListOrderingByLoadOrder(new[] { bm.ModKey }.ToList()) });
        Console.WriteLine(JsonSerializer.Serialize(new
        {
            base_plugin = basePath, block = blockPath,
            world = new[] { cell.FormKey, npc.FormKey, q.FormKey, weap.FormKey, rock.FormKey, barrel.FormKey, race.FormKey, voice.FormKey }.Select(k => k.ToString()),
            start_quest = new[] { startQuest.FormKey, startTopic.FormKey }.Select(k => k.ToString()),
            unreached = new[] { unused.FormKey.ToString() },
        }));
        return 0;
    }
}
