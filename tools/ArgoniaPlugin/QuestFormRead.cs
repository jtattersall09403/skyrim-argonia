using Mutagen.Bethesda.Plugins.Aspects;
using System.Text.Json;
using System.Text.Json.Nodes;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Noggog;

// questform-read <Argonia.esp> <out dir> <plugins in load order...>: every quest of ours built from a quest form (its
// fragment script is ARG_QuestStages) turned back into its quest form, <out dir>/<quest id>.json, from the built plugin
// alone: the quest record, its aliases and their scripts, the stage rows, the lines' responses and their scripts, the
// force-greet package and the mortal watch; positions and text as built (docs/design/quest-form.md, "How a form becomes
// records"). The load order gives only where an existing reference stands and what a base is. A record of a form-built
// quest that the form cannot say (an unknown script, a property it does not know, a package other than the one
// force-greet, a condition outside the vocabulary, a scene, a trigger box) fails the read with one line naming it.
static class QuestFormRead
{
    sealed class Bad(string q, string what) : Exception($"questform-read {q}: {what}");
    static readonly Dictionary<int, string> ResultOf = QuestForm.Op.OfResult.ToDictionary(kv => kv.Value, kv => kv.Key);
    static readonly HashSet<string> StageProps = ["Op", "What", "Num", "Stages", "StageFrom", "StageTo", "QuestId", "Kind", "Labels"];
    static readonly HashSet<string> LineProps = ["Op", "What", "Num", "Owner", "Line", "Written"];
    sealed record Rw(int Op, FormKey What, float Num);

    public static int Run(string esp, string outDir, string[] paths)
    {
        var mods = Survey.Load(paths);
        var mod = SkyrimMod.CreateFromBinaryOverlay(esp, SkyrimRelease.SkyrimSE, Survey.NoStrings);
        var all = mods.Append(mod).ToList();
        Directory.CreateDirectory(outDir);
        var formed = mod.Quests.Where(q => q.FormKey.ModKey == mod.ModKey && q.VirtualMachineAdapter?.FileName == QuestForm.StagesScript).ToList();
        var ctx = new Ctx(mod, all, formed, mods);
        var bad = 0;
        foreach (var q in formed)
        {
            try
            {
                var f = Read(ctx, q);
                var p = Path.Combine(outDir, f["quest"]!["id"]!.GetValue<string>() + ".json");
                File.WriteAllText(p, f.ToJsonString(new JsonSerializerOptions { WriteIndented = true, Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping }) + "\n");
                Console.WriteLine($"questform-read: {q.EditorID} -> {p}");
            }
            catch (Bad e) { bad++; Console.WriteLine("FAIL " + e.Message); }
        }
        // a quest of ours that runs our generic scripts but not as a form-built quest is a record the form cannot say
        foreach (var q in mod.Quests.Where(q => q.FormKey.ModKey == mod.ModKey && !formed.Contains(q) && q.EditorID != QuestForm.WatchId))
            if (q.VirtualMachineAdapter?.Scripts.Any(s => s.Name.StartsWith("ARG_") && s.Name is QuestForm.StagesScript or QuestForm.AliasScript) == true)
            { bad++; Console.WriteLine($"FAIL questform-read {q.EditorID}: runs a generic script without being a form-built quest"); }
        Console.WriteLine($"questform-read: {formed.Count - bad} of {formed.Count} form-built quests read back");
        return bad == 0 ? 0 : 1;
    }

    sealed class Ctx
    {
        public readonly ISkyrimModGetter Mod; public readonly List<ISkyrimModGetter> All; public readonly List<IQuestGetter> Formed;
        public readonly Dictionary<FormKey, (IPlacedGetter rec, ModKey from)> Placed;
        public readonly Dictionary<FormKey, (IPlacedGetter rec, ModKey from)> Orig;     // the load order's winners without our plugin
        public readonly Dictionary<FormKey, (FormKey cell, FormKey world, bool interior)> Where = [];
        public readonly Dictionary<(FormKey, int, int), FormKey> Grid = [];
        public readonly Dictionary<FormKey, (List<Rw> rows, Dictionary<int, (int from, int to)> stages, string qid)> Rows = [];
        public readonly IQuestGetter? Watch;
        public readonly Dictionary<FormKey, IMajorRecordGetter> Recs = [];
        public Ctx(ISkyrimModGetter mod, List<ISkyrimModGetter> all, List<IQuestGetter> formed, List<ISkyrimModGetter> loaded)
        {
            Mod = mod; All = all; Formed = formed;
            Placed = Survey.Winners<IPlacedGetter>(all);
            Orig = Survey.Winners<IPlacedGetter>(loaded);
            foreach (var m in all)
            {
                foreach (var w in m.Worldspaces)
                {
                    foreach (var r in w.TopCell?.Persistent ?? []) Where[r.FormKey] = (FormKey.Null, w.FormKey, false);
                    foreach (var c in w.SubCells.SelectMany(b => b.Items).SelectMany(s => s.Items))
                    {
                        if (c.Grid != null) Grid[(w.FormKey, c.Grid.Point.X, c.Grid.Point.Y)] = c.FormKey;
                        foreach (var r in c.Persistent.Concat(c.Temporary)) Where[r.FormKey] = (c.FormKey, w.FormKey, false);
                    }
                }
                foreach (var c in m.Cells.Records.SelectMany(b => b.SubBlocks).SelectMany(s => s.Cells))
                    foreach (var r in c.Persistent.Concat(c.Temporary)) Where[r.FormKey] = (c.FormKey, FormKey.Null, true);
            }
            Watch = mod.Quests.FirstOrDefault(q => q.EditorID == QuestForm.WatchId);
            foreach (var m in all)
                foreach (var r in m.EnumerateMajorRecords().Where(r => r is not IPlacedGetter and not INavigationMeshGetter and not IDialogResponsesGetter))
                    Recs[r.FormKey] = r;
            foreach (var q in formed)
            {
                var s = q.VirtualMachineAdapter!.Scripts.Single(x => x.Name == QuestForm.StagesScript);
                var rows = Arrays(s.Properties, q.EditorID ?? "");
                var st = Ints(s, "Stages"); var fr = Ints(s, "StageFrom"); var to = Ints(s, "StageTo");
                var map = new Dictionary<int, (int, int)>();
                for (var i = 0; i < st.Count; i++) map[st[i]] = (fr[i], to[i]);
                Rows[q.FormKey] = (rows, map, Str(s, "QuestId"));
            }
        }
    }

    static List<int> Ints(IScriptEntryGetter s, string n) => s.Properties.OfType<IScriptIntListPropertyGetter>().FirstOrDefault(p => p.Name == n)?.Data.ToList() ?? [];
    static string Str(IScriptEntryGetter s, string n) => s.Properties.OfType<IScriptStringPropertyGetter>().FirstOrDefault(p => p.Name == n)?.Data ?? "";
    static List<Rw> Arrays(IEnumerable<IScriptPropertyGetter> props, string where)
    {
        var ps = props.ToList();
        var op = ps.OfType<IScriptIntListPropertyGetter>().FirstOrDefault(p => p.Name == "Op")?.Data.ToList() ?? [];
        var what = ps.OfType<IScriptObjectListPropertyGetter>().FirstOrDefault(p => p.Name == "What")?.Objects.Select(o => o.Object.FormKey).ToList() ?? [];
        var num = ps.OfType<IScriptFloatListPropertyGetter>().FirstOrDefault(p => p.Name == "Num")?.Data.ToList() ?? [];
        if (op.Count != what.Count || op.Count != num.Count) throw new Bad(where, $"the row arrays differ in length ({op.Count}, {what.Count}, {num.Count})");
        return [.. op.Select((o, i) => new Rw(o, what[i], num[i]))];
    }

    static JsonObject Read(Ctx c, IQuestGetter q)
    {
        var e = q.EditorID ?? q.FormKey.ToString();
        Bad No(string what) => new(e, what);
        var vm = q.VirtualMachineAdapter!;
        if (vm.Scripts.Count != 1) throw No($"scripts {string.Join(", ", vm.Scripts.Select(s => s.Name))}: only {QuestForm.StagesScript}");
        var script = vm.Scripts[0];
        foreach (var p in script.Properties) if (!StageProps.Contains(p.Name)) throw No($"{QuestForm.StagesScript} property {p.Name} is unknown");
        foreach (var f in vm.Fragments)
            if (f.ScriptName != QuestForm.StagesScript || f.FragmentName != $"Fragment_{f.Stage}") throw No($"stage {f.Stage}'s fragment {f.ScriptName}.{f.FragmentName}");
        if (c.Mod.Scenes.Any(s => s.Quest.FormKey == q.FormKey)) throw No("owns a scene");
        var labels = script.Properties.OfType<IScriptStringListPropertyGetter>().FirstOrDefault(p => p.Name == "Labels")?.Data.ToList() ?? [];
        var names = labels.Where(l => l.StartsWith("name=")).Select(l => l[5..].Split('|', 3)).ToDictionary(p => (p[0], p[1]), p => p[2]);
        var (rows, stageRows, qid) = c.Rows[q.FormKey];
        var kind = Str(script, "Kind");
        if ((kind == "main") != (q.Type == Quest.TypeEnum.MainQuest)) throw No($"kind {kind} on a quest of type {q.Type}");
        string Name(string k, FormKey key) => names.TryGetValue((k, key.ToString()), out var n) ? n : key.ToString();
        // an item base: a new item of ours copied from a template (template_item, its template's word), else the item's word
        JsonObject ItemBase(FormKey key) => names.TryGetValue(("template", key.ToString()), out var tw)
            ? new JsonObject { ["kind"] = "template_item", ["id"] = tw } : new JsonObject { ["kind"] = "item", ["id"] = Name("item", key) };
        string QuestName(FormKey key) => c.Rows.TryGetValue(key, out var r) ? r.qid : Name("quest", key);

        // ---- refs: one per alias, the alias's name is the ref id
        var aliases = q.Aliases.OrderBy(a => a.ID).ToList();
        var refOf = new Dictionary<FormKey, string>();
        var refs = new JsonArray();
        var aliasName = aliases.ToDictionary(a => a.ID, a => a.Name ?? throw No($"alias {a.ID} has no name"));
        var persons = aliases.Where(x => !x.ForcedReference.IsNull && Placed(c, x.ForcedReference.FormKey) is IPlacedNpcGetter).ToList();
        var personIds = persons.Select(x => x.ID).ToHashSet();
        var personOfBase = persons.GroupBy(x => ((IPlacedNpcGetter)Placed(c, x.ForcedReference.FormKey)!).Base.FormKey).Where(g => g.Count() == 1)
            .ToDictionary(g => g.Key, g => g.First().Name!);
        var refTakes = new List<(string an, int pre, int sets)>();
        var autolocked = labels.Where(l => l.StartsWith("autolock=")).Select(l => l[9..]).ToHashSet();
        foreach (var a in aliases)
        {
            if (a.Type != QuestAlias.TypeEnum.Reference) throw No($"alias {a.Name} is not a reference alias");
            var flags = a.Flags ?? 0;
            if ((flags & ~QuestAlias.Flag.AllowDisabled) != 0) throw No($"alias {a.Name} flags {flags}");
            var j = new JsonObject { ["id"] = a.Name };
            if (a.CreateReferenceToObject is { } cr)
            {
                if (cr.Create != CreateReferenceToObject.CreateEnum.In || !a.ForcedReference.IsNull) throw No($"alias {a.Name}: a created reference not in a container");
                j["kind"] = "thing";
                j["placement"] = new JsonObject { ["base"] = ItemBase(cr.Object.FormKey),
                    [personIds.Contains((uint)cr.AliasID) ? "carried_by" : "container"] = aliasName.TryGetValue((uint)cr.AliasID, out var cn) ? cn : throw No($"alias {a.Name}'s container alias {cr.AliasID}") };
                j["enabled"] = true;
                if (Full(c, cr.Object.FormKey) is { } cnm) j["name"] = cnm;
                if (c.Recs.GetValueOrDefault(cr.Object.FormKey) is IBookGetter cbk && cbk.BookText?.String is { } cbt) j["text"] = cbt;
                refs.Add(j);
                continue;
            }
            if (a.ForcedReference.IsNull) throw No($"alias {a.Name} is not a forced reference");
            var k = a.ForcedReference.FormKey;
            refOf[k] = a.Name!;
            var rec = Placed(c, k) ?? throw No($"alias {a.Name}'s reference {k} is in no plugin");
            if ((rec.MajorRecordFlagsRaw & 0x400) == 0) throw No($"alias {a.Name}'s reference {k} is not persistent");
            var npc = rec is IPlacedNpcGetter;
            var baseKey = rec switch { IPlacedNpcGetter n => n.Base.FormKey, IPlacedObjectGetter o => o.Base.FormKey, _ => FormKey.Null };
            var isNew = k.ModKey == c.Mod.ModKey && k.ID >= 0x800000 && k.ID <= 0x8FFFFF;
            var isDoor = c.All.Any(m => m.Doors.Any(d => d.FormKey == baseKey));
            j["kind"] = npc ? "person" : isDoor ? "door" : baseKey == QuestForm.XMarker ? "marker" : "thing";
            if (!isNew) j["placement"] = new JsonObject { ["existing"] = k.ToString() };
            else
            {
                var w = c.Where.TryGetValue(k, out var ww) ? ww : throw No($"{k} stands nowhere");
                var anchor = new JsonObject { ["place"] = CellOf(c, k, rec).ToString(), ["rule"] = OnNavmesh(c, k, rec) ? "navmesh" : "surface" };
                JsonObject bas;
                if (npc)
                {
                    var b = c.Mod.Npcs.FirstOrDefault(n => n.FormKey == baseKey) ?? throw No($"{a.Name}'s base {baseKey} is not ours");
                    if (b.Template.IsNull) throw No($"{a.Name}'s base has no template");
                    bas = new JsonObject { ["kind"] = "template_person", ["id"] = b.Template.FormKey.ToString() };
                    var hostile = !b.Configuration.TemplateFlags.HasFlag(NpcConfiguration.TemplateFlag.AIData) && b.AIData.Aggression >= Aggression.Aggressive;
                    if (hostile) j["hostile"] = true;
                }
                else
                {
                    var item = c.All.Any(m => m.EnumerateMajorRecords<IItemGetter>().Any(x => x.FormKey == baseKey));
                    bas = item ? ItemBase(baseKey) : new JsonObject { ["kind"] = "existing_base", ["id"] = Name("base", baseKey) };
                }
                j["placement"] = new JsonObject { ["base"] = bas, ["anchor"] = anchor };
            }
            j["enabled"] = (rec.MajorRecordFlagsRaw & 0x800) == 0;
            if (rec is IPlacedObjectGetter pc && pc.ItemCount is int cnt) j["count"] = cnt;
            // a second take of a placed thing rides on the reference (QuestForm.Triggers)
            foreach (var s in (rec as IPlacedObjectGetter)?.VirtualMachineAdapter?.Scripts ?? [])
            {
                if (s.Name != QuestForm.TakeRefScript) continue;
                var si = s.Properties.OfType<IScriptIntPropertyGetter>().ToDictionary(p => p.Name, p => p.Data);
                refTakes.Add((a.Name!, si["preReqStage"], si["StageToSet"]));
            }
            if (npc && labels.Contains($"level={a.Name}") && c.Mod.Npcs.FirstOrDefault(n => n.FormKey == baseKey)?.Configuration.Level is INpcLevelGetter lvl) j["level"] = (int)lvl.Level;
            // what the player sees: a person's or thing's name, a marker's place, a door's name and where it leads, a book's text
            var shown = npc ? PersonName(c, baseKey) : j["kind"]!.GetValue<string>() == "marker" ? Full(c, CellOf(c, k, rec)) : Full(c, baseKey);
            if (shown != null) j["name"] = shown;
            if (rec is IPlacedObjectGetter po && po.TeleportDestination is { } td && !td.Door.IsNull && c.Where.TryGetValue(td.Door.FormKey, out var dw))
            {
                var dest = dw.interior ? Full(c, dw.cell) : Full(c, CellOf(c, td.Door.FormKey, Placed(c, td.Door.FormKey)!)) ?? Full(c, dw.world);
                if (dest != null) j["destination"] = dest;
            }
            if (c.Recs.GetValueOrDefault(baseKey) is IBookGetter bk && bk.BookText?.String is { } bt) j["text"] = bt;
            // a lock, an owner and a new container's contents: what our record says that the load order's winner does not
            if (rec is IPlacedObjectGetter plo)
            {
                var orig = c.Orig.TryGetValue(k, out var ow0) ? ow0.rec as IPlacedObjectGetter : null;
                if (plo.Lock is { } lk && !(orig?.Lock is { } ol && ol.Level == lk.Level && ol.Key.FormKey == lk.Key.FormKey)
                    && !(autolocked.Contains(a.Name!) && RequiresKey(lk.Level) && lk.Key.IsNull))
                {
                    var lj = new JsonObject { ["level"] = LevelWord(lk.Level, w => No($"{a.Name}: {w}")) };
                    if (!lk.Key.IsNull) lj["key"] = ItemWord(Name, lk.Key.FormKey);
                    j["lock"] = lj;
                }
                if (!plo.Owner.IsNull && plo.Owner.FormKey != (orig?.Owner.FormKey ?? default))
                {
                    var ok = plo.Owner.FormKey;
                    j["owner"] = personOfBase.TryGetValue(ok, out var pn) ? pn : c.Recs.GetValueOrDefault(ok) is IFactionGetter ? Name("faction", ok)
                        : throw No($"{a.Name}'s owner {ok} is neither a faction nor one person of the form");
                }
                if (isNew && c.Mod.Containers.FirstOrDefault(x => x.FormKey == baseKey) is { } cont)
                    j["contents"] = new JsonArray([.. cont.Items?.Select(e => (JsonNode)new JsonObject { ["item"] = ItemWord(Name, e.Item.Item.FormKey), ["count"] = e.Item.Count }) ?? []]);
            }
            var pos = rec switch { IPlacedNpcGetter n => n.Placement!.Position, IPlacedObjectGetter o => o.Placement!.Position, _ => default };
            var cell = CellOf(c, k, rec);
            j["at"] = new JsonObject { ["cell"] = cell.ToString(), ["interior"] = c.Where[k].interior, ["x"] = pos.X, ["y"] = pos.Y, ["z"] = pos.Z };
            // a reference's packages: only the speaks-first force-greet (read with the lines)
            foreach (var p in a.PackageData)
            {
                var pk = c.Mod.Packages.FirstOrDefault(x => x.FormKey == p.FormKey) ?? throw No($"alias {a.Name}'s package {p.FormKey} is not ours");
                if (pk.PackageTemplate.FormKey != QuestForm.ForceGreetTemplate || a.PackageData.Count > 1) throw No($"alias {a.Name}'s package {pk.EditorID} is not the one force-greet");
            }
            refs.Add(j);
        }
        string RefName(FormKey k, string what) => refOf.TryGetValue(k, out var n) ? n : throw No($"{what} names {k}, which no alias holds");

        // ---- stages and their rows
        var start = 0; var byGame = q.Flags.HasFlag(Quest.Flag.StartGameEnabled);
        var endings = q.Stages.Where(s => s.LogEntries.Any(l => l.Flags is { } f && f != 0)).Select(s => (int)s.Index).ToHashSet();
        var objs = q.Objectives.OrderBy(o => o.Index).ToList();
        var shownAt = objs.ToDictionary(o => (int)o.Index, _ => new List<int>());
        var doneAt = objs.ToDictionary(o => (int)o.Index, _ => new List<int>());
        var mustLive = new JsonArray();
        var stages = new JsonArray();
        foreach (var s in q.Stages.OrderBy(s => s.Index))
        {
            int n = s.Index;
            if (s.LogEntries.Count != 1) throw No($"stage {n} has {s.LogEntries.Count} log entries");
            var le = s.LogEntries[0];
            if (byGame && s.Flags.HasFlag(QuestStage.Flag.StartUpStage)) start = n;
            var ending = le.Flags is { } lf && lf.HasFlag(QuestLogEntry.Flag.CompleteQuest) ? "completed" : le.Flags is { } lf2 && lf2.HasFlag(QuestLogEntry.Flag.FailQuest) ? "failed" : "none";
            var mine = stageRows.TryGetValue(n, out var range) ? rows.GetRange(range.from, range.to - range.from) : [];
            if (ending != "none")
            {
                // the closing rows: Stop last; before it the side-quest count, before that every objective closed
                if (mine.Count == 0 || mine[^1].Op != QuestForm.Op.StopQuest) throw No($"ending {n} does not stop the quest last");
                mine = mine[..^1];
                if (ending == "completed" && kind != "main") { if (mine.Count == 0 || mine[^1].Op != QuestForm.Op.IncSideQuests) throw No($"ending {n} does not count the side quest"); mine = mine[..^1]; }
                var close = ending == "completed" ? QuestForm.Op.CompleteAll : QuestForm.Op.FailAll;
                if (objs.Count > 0)
                {
                    if (mine.Count == 0 || mine[^1].Op != close || (int)mine[^1].Num != objs.Max(o => (int)o.Index)) throw No($"ending {n} does not close every objective");
                    mine = mine[..^1];
                }
            }
            var results = new JsonArray();
            for (var i = 0; i < mine.Count; i++)
            {
                var r = mine[i];
                switch (r.Op)
                {
                    case QuestForm.Op.FailIfDead: mustLive.Add(new JsonObject { ["ref"] = RefName(r.What, $"stage {n}'s start check"), ["fail_stage"] = (int)r.Num }); break;
                    case QuestForm.Op.ShowObjective: Obj(shownAt, (int)r.Num, n); break;
                    case QuestForm.Op.CompleteObjective: Obj(doneAt, (int)r.Num, n); break;
                    case QuestForm.Op.SetActive: break;
                    case QuestForm.Op.StartOnStage: break;                                  // another quest's start: read there
                    case QuestForm.Op.IfStageDone: i++; break;                              // another quest's trigger: read there
                    case QuestForm.Op.IfHolds:                                              // set_stage if_held
                        if (i + 1 >= mine.Count || mine[i + 1].Op != QuestForm.Op.SetStage) throw No($"stage {n}: a held check guards no set_stage");
                        results.Add(new JsonObject { ["do"] = "set_stage", ["stage"] = (int)mine[i + 1].Num, ["if_held"] = ItemWord(Name, r.What) });
                        i++; break;
                    case QuestForm.Op.FailObjective or QuestForm.Op.StopQuest or QuestForm.Op.IncSideQuests or QuestForm.Op.SetStageIfRunning or QuestForm.Op.IfQuestOpen:
                        throw No($"stage {n}: op {r.Op} out of its place");
                    default: results.Add(Result(c, r, No, Name, QuestName, RefName, $"stage {n}")); break;
                }
            }
            stages.Add(new JsonObject { ["number"] = n, ["shown"] = le.Entry?.String != null, ["journal"] = le.Entry?.String, ["ending"] = ending, ["results"] = results });
        }
        void Obj(Dictionary<int, List<int>> d, int o, int stage) { if (!d.TryGetValue(o, out var l)) throw No($"a row names objective {o}, which the quest has not"); l.Add(stage); }
        JsonObject startJ;
        if (byGame) startJ = new JsonObject { ["by"] = "game", ["stage"] = start };
        else
        {
            var by = c.Rows.SelectMany(kv => kv.Value.stages.SelectMany(st => kv.Value.rows.GetRange(st.Value.from, st.Value.to - st.Value.from)
                .Where(r => r.Op == QuestForm.Op.StartOnStage && r.What == q.FormKey).Select(r => (kv.Value.qid, st.Key, (int)r.Num)))).ToList();
            // started by another quest's start_quest result: every such row starts it at one stage
            var res = c.Rows.SelectMany(kv => kv.Value.rows.Where(r => r.Op == QuestForm.Op.StartQuest && r.What == q.FormKey).Select(r => (int)r.Num)).Distinct().ToList();
            if (by.Count == 0 && res.Count == 1) startJ = new JsonObject { ["by"] = "start_quest", ["stage"] = res[0] };
            else if (by.Count != 1) throw No($"started by {by.Count} other quests' stages, and not from a new game");
            else startJ = new JsonObject { ["by"] = "quest_stage", ["quest"] = by[0].qid, ["quest_stage"] = by[0].Key, ["stage"] = by[0].Item3 };
        }
        start = startJ["stage"]!.GetValue<int>();   // the start stage, however the quest starts
        var objectives = new JsonArray();
        foreach (var o in objs)
            objectives.Add(new JsonObject
            {
                ["number"] = (int)o.Index, ["text"] = o.DisplayText?.String,
                ["shown_at"] = new JsonArray([.. shownAt[o.Index].Select(x => (JsonNode)x)]), ["completed_at"] = new JsonArray([.. doneAt[o.Index].Select(x => (JsonNode)x)]),
                ["targets"] = new JsonArray([.. o.Targets.Select(t => (JsonNode)(aliasName.TryGetValue((uint)t.AliasID, out var an) ? an : throw No($"objective {o.Index} targets alias {t.AliasID}")))]),
            });

        // ---- triggers: vanilla's alias scripts, and rows in other form quests; the labels give their ids
        var trigLabels = labels.Where(l => l.StartsWith("trigger=")).Select(l => l[8..].Split('|')).ToList();
        string TrigId(string kindT, string subject, int pre, int sets, out bool choice)
        {
            var hit = trigLabels.FirstOrDefault(p => p[1] == kindT && p[2] == subject && p[^3] == pre.ToString() && p[^2] == sets.ToString())
                ?? throw No($"a {kindT} trigger on {subject} ({pre} to {sets}) has no label");
            choice = hit[^1] == "choice";
            return hit[0];
        }
        var triggers = new JsonArray();
        var minorDeaths = new Dictionary<string, (int fail, int? from, int? to)>();
        foreach (var fa in vm.Aliases)
        {
            var an = aliasName.TryGetValue((uint)fa.Property.Alias, out var x) ? x : throw No($"alias scripts on alias {fa.Property.Alias}");
            foreach (var s in fa.Scripts)
            {
                var ints = s.Properties.OfType<IScriptIntPropertyGetter>().ToDictionary(p => p.Name, p => p.Data);
                var objsP = s.Properties.OfType<IScriptObjectPropertyGetter>().ToDictionary(p => p.Name, p => p.Object.FormKey);
                void Only(params string[] ok) { foreach (var p in s.Properties) if (!ok.Contains(p.Name)) throw No($"{s.Name} on {an}: property {p.Name} is unknown"); }
                void Mine(string p) { if (objsP.GetValueOrDefault(p) != q.FormKey) throw No($"{s.Name} on {an}: {p} is not this quest"); }
                string kindT; int pre, sets;
                switch (s.Name)
                {
                    case QuestForm.TakeScript: Only("myQST", "preReqStage", "StageToSet"); Mine("myQST"); (kindT, pre, sets) = ("take", ints["preReqStage"], ints["StageToSet"]); break;
                    case QuestForm.UseScript: Only("stage", "prereqStageOPT", "TriggerType"); if (ints["TriggerType"] != 0) throw No($"{an}: TriggerType {ints["TriggerType"]}"); (kindT, pre, sets) = ("use", ints["prereqStageOPT"], ints["stage"]); break;
                    case QuestForm.ReadScript: Only("preReqStage", "StageToSet"); (kindT, pre, sets) = ("use", ints["preReqStage"], ints["StageToSet"]); break;
                    case QuestForm.DeathScript:
                        Only("myQST", "preReqStage", "StageToSet"); Mine("myQST");
                        if (ints["preReqStage"] == -1) { minorDeaths[an] = (ints["StageToSet"], null, null); continue; }
                        (kindT, pre, sets) = ("death", ints["preReqStage"], ints["StageToSet"]); break;
                    case QuestForm.AliasScript:
                        Only("Op", "What", "Num");
                        minorDeaths[an] = Death(Arrays(s.Properties, e), q.FormKey) ?? throw No($"{QuestForm.AliasScript} on {an} is no who-must-live death");
                        continue;
                    default: throw No($"alias {an} carries {s.Name}, which no form says");
                }
                // a take script stands for every take of its thing to its stage from its prerequisite on (QuestForm.Triggers)
                if (kindT == "take")
                    foreach (var p in trigLabels.Where(p => p[1] == "take" && p[2] == an && p[^2] == sets.ToString() && int.Parse(p[^3]) > pre))
                        triggers.Add(new JsonObject { ["id"] = p[0], ["kind"] = "take", ["ref"] = an, ["prerequisite"] = int.Parse(p[^3]), ["sets"] = sets });
                var id = TrigId(kindT, an, pre, sets, out var choice);
                var t = new JsonObject { ["id"] = id, ["kind"] = kindT, ["ref"] = an, ["prerequisite"] = pre, ["sets"] = sets };
                if (choice) t["choice"] = true;
                triggers.Add(t);
            }
        }
        foreach (var (an2, pre2, sets2) in refTakes)
            triggers.Add(new JsonObject { ["id"] = TrigId("take", an2, pre2, sets2, out _), ["kind"] = "take", ["ref"] = an2, ["prerequisite"] = pre2, ["sets"] = sets2 });
        foreach (var (other, (orows, ost, oqid)) in c.Rows)
            foreach (var (st, (from, to)) in ost)
                for (var i = from; i < to; i++)
                    if (orows[i].Op == QuestForm.Op.IfStageDone && orows[i].What == q.FormKey)
                    {
                        if (i + 1 >= to || orows[i + 1].Op != QuestForm.Op.SetStageIfRunning || orows[i + 1].What != q.FormKey) throw No($"{oqid} stage {st}: a guard without its stage");
                        int pre = (int)orows[i].Num, sets = (int)orows[i + 1].Num;
                        triggers.Add(new JsonObject { ["id"] = TrigId("quest_stage", oqid, pre, sets, out _), ["kind"] = "quest_stage", ["quest"] = oqid, ["quest_stage"] = st, ["prerequisite"] = pre, ["sets"] = sets });
                    }
        // order the triggers as the labels list them (the form's order)
        var order = trigLabels.Select(p => p[0]).ToList();
        triggers = new JsonArray([.. triggers.OrderBy(t => order.IndexOf(t!["id"]!.GetValue<string>())).Select(t => t!.DeepClone())]);

        // ---- who must live: the start check, then the mortal watch (main_message) or the quest's own death script
        // a start check is a death trigger's (one open from the start) or a who-must-live row's
        var starts = mustLive.Cast<JsonObject>().Select(m => (who: m["ref"]!.GetValue<string>(), at: m["fail_stage"]!.GetValue<int>()))
            .Where(x => !triggers.Any(t => t!["kind"]!.GetValue<string>() == "death" && t["ref"]!.GetValue<string>() == x.who && t["sets"]!.GetValue<int>() == x.at && t["prerequisite"]!.GetValue<int>() == start)).ToList();
        var deaths = c.Watch?.Aliases.Where(a => a.Name?.StartsWith(qid + "|") == true).Select(a => (who: a.Name![(qid.Length + 1)..], main: true, d: WatchRows(c, q.FormKey, a.Name![(qid.Length + 1)..])))
            .Select(x => (x.who, x.main, d: x.d ?? throw No($"the mortal watch's rows for {x.who} are not a who-must-live death"))).ToList() ?? [];
        deaths.AddRange(minorDeaths.Select(kv => (kv.Key, false, kv.Value)));
        mustLive = [];
        foreach (var (who, main, d) in deaths)
        {
            var m = new JsonObject { ["ref"] = who, ["fail_stage"] = d.fail, ["main_message"] = main };
            if (d.from is { } f) m["from"] = f;
            if (d.to is { } t) m["to"] = t;
            if (main && WatchMessage(c, q.FormKey, who) is { } mt) m["message"] = mt;
            var within = (d.from is not { } f2 || start >= f2) && (d.to is not { } t2 || start <= t2);
            var checkedAt = starts.Where(x => x.who == who).ToList();
            if (within != (checkedAt.Count == 1 && checkedAt[0].at == d.fail)) throw No($"{who}: the start check does not match the death's window");
            starts.RemoveAll(x => x.who == who);
            mustLive.Add(m);
        }
        if (starts.Count > 0) throw No($"a start check on {string.Join(", ", starts.Select(x => x.who))} that nothing else explains");

        // ---- lines: every response of ours whose ARG_LineEffects names this quest as its owner
        var lines = new JsonArray();
        var speaksFirst = new Dictionary<string, (string text, string conds, string rows)>();
        var helloCopies = new List<(string id, string text, string conds, string rows)>();
        var lineOfInfo = new Dictionary<FormKey, string>();
        var answersOf = new List<(JsonObject line, IDialogResponsesGetter info)>();
        foreach (var t in c.Mod.DialogTopics)
        {
            var br = c.Mod.DialogBranches.FirstOrDefault(b => b.FormKey == t.Branch.FormKey);
            foreach (var info in t.Responses)
            {
                var ad = info.VirtualMachineAdapter;
                var ls = ad?.Scripts.FirstOrDefault(s => s.Name == QuestForm.LineScript);
                if (ls == null) continue;
                if (ls.Properties.OfType<IScriptObjectPropertyGetter>().FirstOrDefault(p => p.Name == "Owner")?.Object.FormKey != q.FormKey) continue;
                var id = ls.Properties.OfType<IScriptStringPropertyGetter>().First(p => p.Name == "Line").Data;
                if (ad!.Scripts.Count != 1) throw No($"line {id}: scripts {string.Join(", ", ad.Scripts.Select(s => s.Name))}");
                foreach (var p in ls.Properties) if (!LineProps.Contains(p.Name)) throw No($"line {id}: property {p.Name} is unknown");
                var lrows = Arrays(ls.Properties, e);
                var frag = ad.ScriptFragments;
                var begin = frag?.OnBegin != null;
                if (lrows.Count > 0 && (frag == null || (frag.OnBegin == null) == (frag.OnEnd == null) || frag.FileName != QuestForm.LineScript)) throw No($"line {id}: its rows run from no fragment");
                if (lrows.Count == 0 && frag != null) throw No($"line {id}: a fragment with no rows");
                var text = string.Join(" ", info.Responses.Select(r => r.Text.String));
                var conds = info.Conditions.ToList();
                if (conds.Count < 3 || conds[0].Data is not IGetIsReferenceConditionDataGetter sp || conds[1].Data is not IGetStageConditionDataGetter g1 || conds[2].Data is not IGetStageConditionDataGetter g2
                    || g1.Quest.Link.FormKey != q.FormKey || g2.Quest.Link.FormKey != q.FormKey || conds[1].CompareOperator != CompareOperator.GreaterThanOrEqualTo || conds[2].CompareOperator != CompareOperator.LessThanOrEqualTo)
                    throw No($"line {id}: its first conditions are not the speaker and the stage window");
                var speaker = RefName(sp.Target.Link.FormKey, $"line {id}'s speaker");
                var cj = new JsonArray([.. conds.Skip(3).Select(cd => (JsonNode)Condition(c, cd, No, Name, QuestName, RefName, $"line {id}"))]);
                var rj = new JsonArray([.. lrows.Select(r => (JsonNode)Result(c, r, No, Name, QuestName, RefName, $"line {id}"))]);
                string lkind; string? prompt = null;
                if (t.Subtype == DialogTopic.SubtypeEnum.Hello) lkind = "greeting";
                else if (br != null && ((br.Flags ?? 0) & DialogBranch.Flag.Blocking) != 0) lkind = "speaks_first";
                else if (br != null && br.StartingTopic.FormKey == t.FormKey && ((br.Flags ?? 0) & DialogBranch.Flag.TopLevel) != 0) { lkind = "topic"; prompt = t.Name?.String; }
                else if (br != null && br.StartingTopic.FormKey != t.FormKey) { lkind = "answer"; prompt = t.Name?.String; }
                else throw No($"line {id}: topic {t.EditorID} is neither a greeting, a topic, an answer nor a force-greet");
                if (info.Prompt?.String is { } ip && ip != prompt) throw No($"line {id}: its response's own prompt '{ip}'");
                var condsKey = cj.ToJsonString(); var rowsKey = rj.ToJsonString();
                if (lkind == "speaks_first") speaksFirst[id] = (text, condsKey, rowsKey);
                if (lkind == "greeting" && begin) { helloCopies.Add((id, text, condsKey, rowsKey)); continue; }
                if (begin != (lkind == "speaks_first") && lrows.Count > 0) throw No($"line {id}: a {lkind} runs its rows as it {(begin ? "begins" : "ends")}");
                var j = new JsonObject
                {
                    ["id"] = id, ["speaker"] = speaker, ["kind"] = lkind, ["prompt"] = prompt, ["text"] = text,
                    ["written"] = ls.Properties.OfType<IScriptBoolPropertyGetter>().FirstOrDefault(p => p.Name == "Written")?.Data ?? false,
                    ["conditions"] = cj, ["results"] = rj,
                    ["first_stage"] = (int)((IConditionFloatGetter)conds[1]).ComparisonValue, ["last_stage"] = (int)((IConditionFloatGetter)conds[2]).ComparisonValue,
                    ["answers"] = new JsonArray(),
                };
                lineOfInfo[info.FormKey] = id;
                answersOf.Add((j, info));
                lines.Add(j);
            }
        }
        // a speaks-first line with no rows has no begin fragment: its greeting copy is the greeting of the same line id
        foreach (var g in lines.Where(l => (string?)l!["kind"] == "greeting" && speaksFirst.ContainsKey((string)l!["id"]!)).ToList())
        {
            helloCopies.Add(((string)g!["id"]!, (string)g["text"]!, g["conditions"]!.ToJsonString(), g["results"]!.ToJsonString()));
            lines.Remove(g);
            answersOf.RemoveAll(x => x.line == g);
        }
        foreach (var (id, text, cj, rj) in helloCopies)
            if (!speaksFirst.TryGetValue(id, out var sf) || sf != (text, cj, rj)) throw No($"greeting {id} runs its rows as it begins and is no speaks-first line's copy");
        foreach (var id in speaksFirst.Keys) if (!helloCopies.Any(h => h.id == id)) throw No($"speaks-first {id} has no copy under the greeting");
        foreach (var (j, info) in answersOf)
            foreach (var link in info.LinkTo)
            {
                var at = c.Mod.DialogTopics.FirstOrDefault(t => t.FormKey == link.FormKey) ?? throw No($"line {j["id"]} links to {link.FormKey}");
                foreach (var ai in at.Responses) ((JsonArray)j["answers"]!).Add(lineOfInfo.TryGetValue(ai.FormKey, out var aid) ? aid : throw No($"line {j["id"]}'s answer {ai.FormKey} is no line"));
            }
        // the force-greet: its topic is the speaks-first line's
        foreach (var a in aliases.Where(a => a.PackageData.Count > 0))
        {
            var pk = c.Mod.Packages.First(x => x.FormKey == a.PackageData[0].FormKey);
            var topic = pk.Data.Values.OfType<IPackageDataTopicGetter>().SelectMany(t => t.Topics).OfType<ITopicReferenceGetter>().Select(t => t.Reference.FormKey).FirstOrDefault();
            var sfTopic = c.Mod.DialogTopics.FirstOrDefault(t => t.FormKey == topic);
            if (sfTopic == null || !sfTopic.Responses.Any(r => lineOfInfo.TryGetValue(r.FormKey, out var lid) && speaksFirst.ContainsKey(lid))) throw No($"{a.Name}'s force-greet opens no speaks-first line");
        }
        if (speaksFirst.Count != aliases.Count(a => a.PackageData.Count > 0)) throw No("a speaks-first line without its force-greet");

        // the names of the items the form names, as the player sees them
        var itemNames = new JsonObject();
        foreach (var (kk, given) in names.Where(n => n.Key.Item1 == "item").Select(n => (n.Key.Item2, n.Value)))
            if (Full(c, FormKey.Factory(kk)) is { } inm) itemNames[given] = inm;
        return new JsonObject
        {
            ["version"] = 1,
            ["names"] = itemNames,
            ["quest"] = new JsonObject { ["id"] = qid, ["editor_id"] = q.EditorID, ["name"] = q.Name?.String, ["kind"] = kind, ["start"] = startJ },
            ["stages"] = stages, ["objectives"] = objectives, ["refs"] = refs, ["lines"] = lines, ["triggers"] = triggers, ["must_live"] = mustLive,
        };
    }

    // A record's name as the plugins hold it (none for a localized master's: its strings are never read, decision 0003).
    static string? Full(Ctx c, FormKey k) => c.Recs.GetValueOrDefault(k) switch
    {
        ITranslatedNamedGetter t => string.IsNullOrEmpty(t.Name?.String) ? null : t.Name!.String,
        INamedGetter n => string.IsNullOrEmpty(n.Name) ? null : n.Name,
        _ => null,
    };
    // A person's name: our base's own, or its template's when it takes the base data from it.
    static string? PersonName(Ctx c, FormKey k)
    {
        for (var i = 0; i < 16 && c.Recs.GetValueOrDefault(k) is INpcGetter n; i++)
        {
            if (n.Template.IsNull || !n.Configuration.TemplateFlags.HasFlag(NpcConfiguration.TemplateFlag.BaseData)) return Full(c, k);
            k = n.Template.FormKey;
        }
        return Full(c, k);
    }
    static string? WatchMessage(Ctx c, FormKey q, string who)
    {
        if (c.Watch?.VirtualMachineAdapter is not { } vm) return null;
        var a = c.Watch.Aliases.FirstOrDefault(x => x.Name == $"{c.Rows[q].qid}|{who}");
        var s = a == null ? null : vm.Aliases.FirstOrDefault(x => x.Property.Alias == a.ID)?.Scripts.SingleOrDefault(x => x.Name == QuestForm.AliasScript);
        var rows = s == null ? [] : Arrays(s.Properties, QuestForm.WatchId);
        return rows.Where(r => r.Op == QuestForm.Op.ShowMessage).Select(r => c.Mod.Messages.FirstOrDefault(m => m.FormKey == r.What)?.Description?.String).FirstOrDefault();
    }
    static string LevelWord(LockLevel l, Func<string, Bad> no) => l switch
    {
        LockLevel.Novice => "novice", LockLevel.Apprentice => "apprentice", LockLevel.Adept => "adept", LockLevel.Expert => "expert",
        LockLevel.Master => "master", _ when RequiresKey(l) => "key", _ => throw no($"lock level {l} is none of the form's"),
    };
    // Requires Key is the byte 255; a record read from the plugin file gives it as 255, the enum's member is -1
    static bool RequiresKey(LockLevel l) => ((int)l & 0xFF) == 0xFF;
    // an item a result or condition names: a thing of the form's by its ref id, else the item's own word
    static string ItemWord(Func<string, FormKey, string> name, FormKey k) => name("thing", k) is var t && t != k.ToString() ? t : name("item", k);
    static IPlacedGetter? Placed(Ctx c, FormKey k) =>
        (IPlacedGetter?)c.Mod.EnumerateMajorRecords<IPlacedGetter>().FirstOrDefault(r => r.FormKey == k) ?? (c.Placed.TryGetValue(k, out var w) ? w.rec : null);
    static FormKey CellOf(Ctx c, FormKey k, IPlacedGetter rec)
    {
        var w = c.Where[k];
        if (w.interior || !w.cell.IsNull) return w.cell;
        var p = rec switch { IPlacedNpcGetter n => n.Placement!.Position, IPlacedObjectGetter o => o.Placement!.Position, _ => default };
        return c.Grid.TryGetValue((w.world, (int)MathF.Floor(p.X / 4096), (int)MathF.Floor(p.Y / 4096)), out var cell) ? cell : FormKey.Null;
    }
    // A position stands "on the navmesh" when it is a triangle centre (rounded) of a navmesh of its cell: the Snap rule's spot.
    static bool OnNavmesh(Ctx c, FormKey k, IPlacedGetter rec)
    {
        var cell = CellOf(c, k, rec);
        var p = rec switch { IPlacedNpcGetter n => n.Placement!.Position, IPlacedObjectGetter o => o.Placement!.Position, _ => default };
        var near = QuestForm.Neighbours(c.Grid, cell, c.Where[k].world, c.Where[k].interior, p).ToHashSet();
        var meshes = c.All.SelectMany(m => m.EnumerateMajorRecords<ICellGetter>().Where(x => near.Contains(x.FormKey))).SelectMany(x => x.NavigationMeshes.Select(n => n.FormKey)).ToHashSet();
        foreach (var m in Enumerable.Reverse(c.All))
            foreach (var nav in m.EnumerateMajorRecords<INavigationMeshGetter>().Where(n => meshes.Contains(n.FormKey) && n.Data != null))
            {
                var v = nav.Data!.Vertices;
                foreach (var t in nav.Data.Triangles)
                {
                    var a = v[t.Vertices.X]; var b = v[t.Vertices.Y]; var d = v[t.Vertices.Z];
                    if (MathF.Abs(MathF.Round((a.X + b.X + d.X) / 3) - p.X) < 1 && MathF.Abs(MathF.Round((a.Y + b.Y + d.Y) / 3) - p.Y) < 1) return true;
                }
            }
        return false;
    }
    // The mortal watch's rows for a person: [IfQuestOpen, window, ShowMessage, window, SetStageIfRunning].
    static (int fail, int? from, int? to)? WatchRows(Ctx c, FormKey q, string who)
    {
        if (c.Watch?.VirtualMachineAdapter is not { } vm) return null;
        var a = c.Watch.Aliases.FirstOrDefault(x => x.Name == $"{c.Rows[q].qid}|{who}");
        var s = a == null ? null : vm.Aliases.FirstOrDefault(x => x.Property.Alias == a.ID)?.Scripts.SingleOrDefault(x => x.Name == QuestForm.AliasScript);
        var rows = s == null ? [] : Arrays(s.Properties, QuestForm.WatchId);
        var show = rows.FindIndex(r => r.Op == QuestForm.Op.ShowMessage);
        if (rows.Count == 0 || rows[0].Op != QuestForm.Op.IfQuestOpen || rows[0].What != q || show < 0) return null;
        var before = Death([.. rows.GetRange(1, show - 1), new Rw(QuestForm.Op.SetStageIfRunning, q, rows[^1].Num)], q);
        var after = Death(rows.GetRange(show + 1, rows.Count - show - 1), q);
        return before == after ? after : null;
    }
    // A who-must-live death's rows: the window's guards, then the failed ending set while the quest runs.
    static (int fail, int? from, int? to)? Death(List<Rw> rows, FormKey q)
    {
        if (rows.Count == 0 || rows[^1].Op != QuestForm.Op.SetStageIfRunning || rows[^1].What != q) return null;
        int? from = null, to = null;
        foreach (var r in rows[..^1])
        {
            if (r.What != q) return null;
            if (r.Op == QuestForm.Op.IfStageDone && from == null) from = (int)r.Num;
            else if (r.Op == QuestForm.Op.IfStageAtMost && to == null) to = (int)r.Num;
            else return null;
        }
        return ((int)rows[^1].Num, from, to);
    }

    static JsonObject Result(Ctx c, Rw r, Func<string, Bad> no, Func<string, FormKey, string> name, Func<FormKey, string> quest, Func<FormKey, string, string> refName, string where)
    {
        if (!ResultOf.TryGetValue(r.Op, out var w)) throw no($"{where}: op {r.Op} is no result");
        var j = new JsonObject { ["do"] = w };
        switch (w)
        {
            case "set_stage": j["stage"] = (int)r.Num; break;
            case "give_item" or "take_item": j["item"] = ItemWord(name, r.What); j["count"] = (int)r.Num; break;
            case "give_gold" or "take_gold": if (r.What != QuestForm.Gold) throw no($"{where}: gold that is not Gold001"); j["amount"] = (int)r.Num; break;
            case "set_number" or "add_number": j["number"] = name("number", r.What); j["value"] = r.Num == MathF.Round(r.Num) ? (int)r.Num : r.Num; break;
            case "join_faction": j["faction"] = name("faction", r.What); break;
            case "set_rank": j["faction"] = name("faction", r.What); j["rank"] = (int)r.Num; break;
            case "change_regard": j["ref"] = refName(r.What, where); j["by"] = (int)r.Num; break;
            case "switch_on" or "switch_off" or "lock_door" or "unlock_door": j["ref"] = refName(r.What, where); break;
            case "show_message":
                j["text"] = c.Mod.Messages.FirstOrDefault(m => m.FormKey == r.What)?.Description?.String ?? throw no($"{where}: message {r.What} is not ours"); break;
            case "speaker_hostile": break;
            case "start_quest": j["quest"] = quest(r.What); j["stage"] = (int)r.Num; break;
        }
        return j;
    }

    static JsonObject Condition(Ctx c, IConditionGetter cd, Func<string, Bad> no, Func<string, FormKey, string> name, Func<FormKey, string> quest, Func<FormKey, string, string> refName, string where)
    {
        if (cd is not IConditionFloatGetter f || (cd.Flags & Mutagen.Bethesda.Skyrim.Condition.Flag.OR) != 0) throw no($"{where}: a condition that is not one plain test");
        var op = f.CompareOperator; var v = f.ComparisonValue; var d = cd.Data;
        bool onPlayer = d.RunOnType == Mutagen.Bethesda.Skyrim.Condition.RunOnType.Reference && d.Reference.FormKey == QuestForm.Player;
        FormKey OnRef() => d.RunOnType == Mutagen.Bethesda.Skyrim.Condition.RunOnType.Reference ? d.Reference.FormKey : throw no($"{where}: {d.GetType().Name} not on a reference");
        // (the word, whether it is negated) from the operator against the positive one and its negation
        bool Neg(CompareOperator pos) => op == pos ? false : op == QuestForm.Negate(pos) ? true : throw no($"{where}: {d.GetType().Name} {op} {v}");
        JsonObject J(string w, bool not, params (string k, JsonNode? v)[] kv)
        {
            var j = new JsonObject { ["is"] = w };
            foreach (var (k, x) in kv) j[k] = x;
            if (not) j["not"] = true;
            return j;
        }
        void Player() { if (!onPlayer) throw no($"{where}: {d.GetType().Name} not on the player"); }
        switch (d)
        {
            case IGetStageConditionDataGetter g:
                if (op is CompareOperator.EqualTo or CompareOperator.NotEqualTo) return J("stage_is", op != CompareOperator.EqualTo, ("quest", quest(g.Quest.Link.FormKey)), ("stage", (int)v));
                return J("stage_at_least", Neg(CompareOperator.GreaterThanOrEqualTo), ("quest", quest(g.Quest.Link.FormKey)), ("stage", (int)v));
            case IGetStageDoneConditionDataGetter g:
                if (v != 1) throw no($"{where}: GetStageDone against {v}");
                return J("stage_done", Neg(CompareOperator.EqualTo), ("quest", quest(g.Quest.Link.FormKey)), ("stage", g.Stage));
            case IGetGlobalValueConditionDataGetter g:
                var ops = new Dictionary<CompareOperator, string> { [CompareOperator.EqualTo] = "=", [CompareOperator.NotEqualTo] = "!=", [CompareOperator.LessThan] = "<",
                    [CompareOperator.LessThanOrEqualTo] = "<=", [CompareOperator.GreaterThan] = ">", [CompareOperator.GreaterThanOrEqualTo] = ">=" };
                return J("number_compare", false, ("number", name("number", g.Global.Link.FormKey)), ("op", ops[op]), ("value", v == MathF.Round(v) ? (int)v : v));
            case IGetInFactionConditionDataGetter g:
                Player(); if (v != 1) throw no($"{where}: GetInFaction against {v}");
                return J("in_faction", Neg(CompareOperator.EqualTo), ("faction", name("faction", g.Faction.Link.FormKey)));
            case IGetFactionRankConditionDataGetter g:
                Player(); return J("rank_at_least", Neg(CompareOperator.GreaterThanOrEqualTo), ("faction", name("faction", g.Faction.Link.FormKey)), ("rank", (int)v));
            case IGetItemCountConditionDataGetter g:
                Player();
                if (g.ItemOrList.Link.FormKey == QuestForm.Gold) return J("gold_at_least", Neg(CompareOperator.GreaterThanOrEqualTo), ("gold", (int)v));
                return J("item_count_at_least", Neg(CompareOperator.GreaterThanOrEqualTo), ("item", ItemWord(name, g.ItemOrList.Link.FormKey)), ("count", (int)v));
            case IGetActorValueConditionDataGetter g:
                Player();
                var sk = QuestForm.SkillName(g.ActorValue);
                if (QuestForm.Skill(sk) != g.ActorValue) throw no($"{where}: actor value {g.ActorValue} is no skill");
                return J("skill_at_least", Neg(CompareOperator.GreaterThanOrEqualTo), ("skill", sk), ("value", (int)v));
            case IGetDeadConditionDataGetter:
                var who = refName(OnRef(), where);
                if (v == 0) return J("alive", Neg(CompareOperator.EqualTo), ("ref", who));
                if (v == 1) return J("dead", Neg(CompareOperator.EqualTo), ("ref", who));
                throw no($"{where}: GetDead against {v}");
            case IGetIsReferenceConditionDataGetter g:
                if (v != 1) throw no($"{where}: GetIsReference against {v}");
                return J("speaker_is", Neg(CompareOperator.EqualTo), ("ref", refName(g.Target.Link.FormKey, where)));
            case IGetRelationshipRankConditionDataGetter g:
                if (g.TargetNpc.Link.FormKey != QuestForm.Player) throw no($"{where}: a regard not toward the player");
                return J("regard_at_least", Neg(CompareOperator.GreaterThanOrEqualTo), ("ref", refName(OnRef(), where)), ("value", (int)v));
            case IGetIsRaceConditionDataGetter g:
                Player(); if (v != 1) throw no($"{where}: GetIsRace against {v}");
                return J("race_is", Neg(CompareOperator.EqualTo), ("value", name("race", g.Race.Link.FormKey)));
            case IGetIsSexConditionDataGetter g:
                Player(); if (v != 1) throw no($"{where}: GetIsSex against {v}");
                return J("sex_is", Neg(CompareOperator.EqualTo), ("value", g.MaleFemaleGender == MaleFemaleGender.Female ? "female" : "male"));
            case IGetTalkedToPCConditionDataGetter:
                if (v == 1) return J("spoken_before", Neg(CompareOperator.EqualTo));
                if (v == 0) return J("not_spoken_before", Neg(CompareOperator.EqualTo));
                throw no($"{where}: GetTalkedToPC against {v}");
            default: throw no($"{where}: condition {d.GetType().Name} is outside the form's vocabulary");
        }
    }
}
