using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using Noggog;
// inspect <what> <plugins...>: read-only questions about the load order.
//   player   who overrides the Player NPC and the playable races, with outfit, skin and default items
//   movt     every plugin's movement types and their speeds
//   ref:<formkey>   a placed object's position in each plugin, and the objects near it there
//   navnear:<x>:<y>:<r>   winning navmesh triangle centres within r units of x,y (worldspace cell grid shown)
static class Inspect
{
    public static void Run(string what, string[] paths)
    {
        var mods = Survey.Load(paths);
        if (what == "player")
        {
            foreach (var m in mods)
            {
                foreach (var n in m.Npcs.Where(n => n.FormKey == FormKey.Factory("000007:Skyrim.esm")))
                    Console.WriteLine($"PLAYER in {m.ModKey}: outfit={n.DefaultOutfit.FormKey} skin={n.WornArmor.FormKey} race={n.Race.FormKey} items={string.Join(",", (n.Items ?? []).Select(i => i.Item.Item.FormKey))}");
                foreach (var r in m.Races.Where(r => r.Flags.HasFlag(Race.Flag.Playable)))
                    Console.WriteLine($"RACE {r.EditorID} in {m.ModKey}: skin={r.Skin.FormKey}");
                foreach (var o in m.Outfits) if (o.EditorID != null && o.EditorID.Contains("Player", StringComparison.OrdinalIgnoreCase)) Console.WriteLine($"OUTFIT {o.EditorID} in {m.ModKey}");
            }
            return;
        }
        if (what == "movt")
        {
            foreach (var m in mods)
                foreach (var t in m.MovementTypes)
                {
                    Console.WriteLine($"MOVT {t.EditorID} in {m.ModKey}: " + string.Join(" ", typeof(IMovementTypeGetter).GetProperties().Where(pp => pp.PropertyType == typeof(float)).Select(pp => $"{pp.Name}={pp.GetValue(t)}")));
                }
            return;
        }
        if (what.StartsWith("ref:"))
        {
            var k = FormKey.Factory(what[4..]);
            var bases = mods.SelectMany(m => m.EnumerateMajorRecords()).Where(r => r is not IPlacedGetter && r.EditorID != null).GroupBy(r => r.FormKey).ToDictionary(g => g.Key, g => g.Last().EditorID);
            foreach (var m in mods) foreach (var r in m.EnumerateMajorRecords<IPlacedObjectGetter>().Where(r => r.FormKey == k))
            {
                var pos = r.Placement!.Position;
                Console.WriteLine($"REF {k} in {m.ModKey}: base={bases.GetValueOrDefault(r.Base.FormKey)} pos={pos}");
                if (r.TeleportDestination is { } td) Console.WriteLine($"  teleport: door {td.Door.FormKey} arrival {td.Position}");
                foreach (var o in mods.Where(mm => mm.ModKey.FileName.String.StartsWith("Black Marsh")).SelectMany(mm => mm.EnumerateMajorRecords<IPlacedObjectGetter>()))
                    if (o.Placement is { } op && Math.Abs(op.Position.X - pos.X) < 600 && Math.Abs(op.Position.Y - pos.Y) < 600 && Math.Abs(op.Position.Z - pos.Z) < 600)
                        Console.WriteLine($"  near: {o.FormKey} {bases.GetValueOrDefault(o.Base.FormKey)} pos={op.Position}");
            }
            return;
        }
        if (what.StartsWith("dial:"))  // dial:<quest formkey>: the quest's topics, their INFO counts and condition kinds
        {
            var qk = FormKey.Factory(what[5..]);
            foreach (var m in mods) foreach (var t in m.EnumerateMajorRecords<IDialogTopicGetter>().Where(t => t.Quest.FormKey == qk))
                Console.WriteLine($"DIAL {t.FormKey} in {m.ModKey} {t.EditorID} '{t.Name?.String}' {t.Subtype} infos={t.Responses.Count} conds={string.Join(",", t.Responses.SelectMany(r => r.Conditions).Select(c => c.Data.GetType().Name.Replace("ConditionData", "")).Distinct())}");
            return;
        }
        if (what.StartsWith("npc:"))  // npc:<base formkey>[,...]: height, weight, race and its heights, template chain, from each plugin
        {
            var races = Survey.Winners<IRaceGetter>(mods);
            foreach (var key in what[4..].Split(','))
                foreach (var m in mods) foreach (var n in m.Npcs.Where(n => n.FormKey == FormKey.Factory(key)))
                {
                    var r = races.GetValueOrDefault(n.Race.FormKey).rec;
                    Console.WriteLine($"NPC {key} {n.EditorID} in {m.ModKey}: height={n.Height} weight={n.Weight} race={r?.EditorID} raceHeight={r?.Height} tpl={n.Template.FormKey} tflags={n.Configuration.TemplateFlags}");
                }
            return;
        }
        if (what.StartsWith("xtel:"))  // xtel:<ref>[,...]: a placed door's position, rotation and teleport (destination door, arrival spot)
        {
            foreach (var key in what[5..].Split(','))
                foreach (var m in mods) foreach (var r in m.EnumerateMajorRecords<IPlacedObjectGetter>().Where(r => r.FormKey == FormKey.Factory(key)))
                    Console.WriteLine($"XTEL {key} in {m.ModKey}: pos={r.Placement?.Position} rot={r.Placement?.Rotation} -> {r.TeleportDestination?.Door.FormKey} at {r.TeleportDestination?.Position} rot {r.TeleportDestination?.Rotation}");
            return;
        }
        if (what == "aliaspack")  // per plugin: the packages its quests' aliases carry, by owner quest, template kind and where the base's own packages are
        {
            var packs = Survey.Winners<IPackageGetter>(mods);
            foreach (var m in mods)
            {
                int n = 0, own = 0, none = 0, other = 0, tpl = 0;
                foreach (var q in m.Quests)
                    foreach (var al in q.Aliases)
                        foreach (var l in al.PackageData)
                        {
                            if (!packs.TryGetValue(l.FormKey, out var p)) continue;
                            n++;
                            if (p.rec.OwnerQuest.IsNull) none++; else if (p.rec.OwnerQuest.FormKey == q.FormKey) own++; else other++;
                            if (p.rec.Type == Package.Types.PackageTemplate) tpl++;
                            if (m.ModKey == mods[^1].ModKey && (p.rec.OwnerQuest.FormKey != q.FormKey || p.rec.Type == Package.Types.PackageTemplate))
                                Console.WriteLine($"ALIASPACK {q.EditorID} alias {al.Name}: {p.rec.EditorID} owner={(p.rec.OwnerQuest.IsNull ? "none" : p.rec.OwnerQuest.FormKey.ToString())} type={p.rec.Type}");
                        }
                if (n > 0) Console.WriteLine($"ALIASPACK {m.ModKey}: {n} alias packages; owner is the alias's quest {own}, another quest {other}, none {none}; template-type {tpl}");
            }
            return;
        }
        if (what == "navstat")  // per plugin: winning navmeshes, and how many carry edge links to another navmesh
        {
            foreach (var g in Survey.Winners<INavigationMeshGetter>(mods).GroupBy(w => w.Key.ModKey))
                Console.WriteLine($"NAVSTAT {g.Key}: {g.Count()} navmeshes, {g.Count(w => w.Value.rec.Data?.EdgeLinks.Count > 0)} with edge links");
            return;
        }
        if (what.StartsWith("navpath:"))  // navpath:<navmesh>:<x>:<y>:<navmesh>:<x>:<y>: is there a walk over winning navmesh between two spots
        {
            var p = what[8..].Split(':');
            FormKey NK(int i) => FormKey.Factory(p[i] + ":" + p[i + 1]);
            var navs = Survey.Winners<INavigationMeshGetter>(mods);
            (FormKey, int) Near(FormKey m, float x0, float y0)
            {
                var d = navs[m].rec.Data!; var v = d.Vertices;
                var i = Enumerable.Range(0, d.Triangles.Count).MinBy(i => { var t = d.Triangles[i].Vertices; var cx = (v[t.X].X + v[t.Y].X + v[t.Z].X) / 3 - x0; var cy = (v[t.X].Y + v[t.Y].Y + v[t.Z].Y) / 3 - y0; return cx * cx + cy * cy; });
                return (m, i);
            }
            foreach (var mk in new[] { NK(0), NK(4) })
            {
                var dd = navs[mk].rec.Data!;
                Console.WriteLine($"NAVM {mk}: {dd.Triangles.Count} tris, {dd.EdgeLinks.Count} edge links, {dd.Triangles.Count(t => ((int)t.Flags & 7) != 0)} linked tris, to {string.Join(",", dd.EdgeLinks.Select(l => l.Mesh.FormKey).Distinct())}");
            }
            var from = Near(NK(0), float.Parse(p[2]), float.Parse(p[3])); var to = Near(NK(4), float.Parse(p[6]), float.Parse(p[7]));
            var seen = new HashSet<(FormKey, int)> { from }; var queue = new Queue<(FormKey, int)>([from]); var meshes = new HashSet<FormKey>();
            while (queue.Count > 0)
            {
                var (m, i) = queue.Dequeue(); meshes.Add(m);
                if ((m, i) == to) break;
                if (!navs.TryGetValue(m, out var nv) || nv.rec.Data is not { } d || i >= d.Triangles.Count) continue;
                var t = d.Triangles[i];
                var e = new[] { (int)t.EdgeLink_0_1, (int)t.EdgeLink_1_2, (int)t.EdgeLink_2_0 };  // NVNM flag bits 0-2: that edge is a link
                for (var k = 0; k < 3; k++)
                {
                    if (e[k] < 0) continue;
                    (FormKey, int) n = ((int)t.Flags & (1 << k)) != 0
                        ? (e[k] < d.EdgeLinks.Count ? (d.EdgeLinks[e[k]].Mesh.FormKey, (int)d.EdgeLinks[e[k]].TriangleIndex) : default)
                        : (m, e[k]);
                    if (n != default && seen.Add(n)) queue.Enqueue(n);
                }
            }
            Console.WriteLine($"NAVPATH {from} -> {to}: {(seen.Contains(to) ? "CONNECTED" : "NOT CONNECTED")}; reached {seen.Count} triangles in {meshes.Count} navmeshes");
            return;
        }
        if (what == "silent")  // every person Argonia.esp places (a playable race, not aggressive) that no INFO of ours names
        {
            var mine = mods[^1];
            var npcs = Survey.Winners<INpcGetter>(mods); var races = Survey.Winners<IRaceGetter>(mods);
            var named = mine.EnumerateMajorRecords<IDialogResponsesGetter>().SelectMany(i => i.Conditions).Select(c => c.Data switch
            {
                IGetIsIDConditionDataGetter d => d.Object.Link.FormKey, IGetIsReferenceConditionDataGetter r => r.Target.Link.FormKey, _ => FormKey.Null,
            }).ToHashSet();
            int n = 0, quiet = 0;
            foreach (var c in mine.EnumerateMajorRecords<ICellGetter>())
                foreach (var r in c.Persistent.Concat(c.Temporary).OfType<IPlacedNpcGetter>().Where(r => r.FormKey.ModKey == mine.ModKey))
                {
                    var b = npcs.GetValueOrDefault(r.Base.FormKey).rec;
                    if (b == null || !races.TryGetValue(b.Race.FormKey, out var race) || !race.rec.Flags.HasFlag(Race.Flag.Playable) || b.AIData?.Aggression >= Aggression.Aggressive) continue;
                    n++;
                    INpcGetter v = b; for (var i = 0; i < 8 && v.Configuration.TemplateFlags.HasFlag(NpcConfiguration.TemplateFlag.Traits) && npcs.TryGetValue(v.Template.FormKey, out var tv); i++) v = tv.rec;
                    if (v.Voice.IsNull) Console.WriteLine($"NOVOICE {r.EditorID} base={b.EditorID}");
                    if (named.Contains(r.FormKey) || named.Contains(b.FormKey)) continue;
                    quiet++;
                    Console.WriteLine($"SILENT {r.EditorID} base={b.EditorID} '{b.Name?.String}' cell={c.EditorID ?? c.FormKey.ToString()}");
                }
            Console.WriteLine($"silent: {quiet} of {n} people we place have no line");
            return;
        }
        if (what == "heights")  // every NPC base Argonia.esp adds or overrides whose drawn height (Traits template chain) is off 1 by 0.1+
        {
            var npcs = Survey.Winners<INpcGetter>(mods);
            float H(INpcGetter n, int d = 0) => d < 8 && n.Configuration.TemplateFlags.HasFlag(NpcConfiguration.TemplateFlag.Traits)
                && npcs.TryGetValue(n.Template.FormKey, out var t) ? H(t.rec, d + 1) : n.Height;
            foreach (var n in mods[^1].Npcs)
                if (Math.Abs(H(n) - 1) >= 0.1f)
                {
                    var refs = mods[^1].EnumerateMajorRecords<IPlacedNpcGetter>().Where(r => r.Base.FormKey == n.FormKey).Select(r => $"{r.EditorID} scale {r.Scale?.ToString() ?? "1"} -> drawn {H(n) * (r.Scale ?? 1):F2}");
                    Console.WriteLine($"TALL {n.FormKey} {n.EditorID} '{n.Name?.String}' height={H(n)} tpl={n.Template.FormKey}; {string.Join("; ", refs)}");
                }
            foreach (var (k, (n, from)) in npcs.Where(w => w.Key.ModKey.FileName.String.StartsWith("Black Marsh") && w.Value.rec.Height is > 0.95f and < 1.05f
                && w.Value.rec.EditorID?.StartsWith("ArgonianMale") == true && w.Value.rec.Template.IsNull).Take(30))
                Console.WriteLine($"MALE1 {k} {n.EditorID}");
            return;
        }
        if (what == "doors")  // every door ref Argonia.esp adds or overrides, and every door in the interiors it touches
        {
            var mine = mods[^1];
            var doorBases = Survey.Winners<IDoorGetter>(mods);
            var refs = new Dictionary<FormKey, (IPlacedObjectGetter r, ModKey from, FormKey cell)>();
            foreach (var m in mods)
                foreach (var c in m.EnumerateMajorRecords<ICellGetter>())
                    foreach (var r in c.Persistent.Concat(c.Temporary).OfType<IPlacedObjectGetter>())
                    {
                        refs[r.FormKey] = (r, m.ModKey, c.FormKey);
                    }
            var cells = Survey.Winners<ICellGetter>(mods);
            var touched = mine.EnumerateMajorRecords<ICellGetter>().Where(c => c.Flags.HasFlag(Cell.Flag.IsInteriorCell)).Select(c => c.FormKey).ToHashSet();
            var ourRefs = mine.EnumerateMajorRecords<ICellGetter>().SelectMany(c => c.Persistent.Concat(c.Temporary)).Select(r => r.FormKey).ToHashSet();
            foreach (var (k, (r, from, cell)) in refs.Where(kv => doorBases.ContainsKey(kv.Value.r.Base.FormKey) && (ourRefs.Contains(kv.Key) || touched.Contains(kv.Value.cell))).OrderBy(kv => kv.Value.cell.ToString()).ThenBy(kv => kv.Key.ToString()))
            {
                var b = doorBases[r.Base.FormKey].rec;
                var t = r.TeleportDestination;
                string dest = "none";
                if (t != null)
                {
                    var dk = t.Door.FormKey;
                    dest = refs.TryGetValue(dk, out var d)
                        ? $"{dk} in {cells.GetValueOrDefault(d.cell).rec?.EditorID ?? d.cell.ToString()} back={(d.r.TeleportDestination?.Door.FormKey == k ? "yes" : d.r.TeleportDestination?.Door.FormKey.ToString() ?? "none")} disabled={(d.r.MajorRecordFlagsRaw & 0x800) != 0} parent={d.r.EnableParent?.Reference.FormKey.ToString() ?? "-"} by={d.from}"
                        : $"{dk} MISSING";
                }
                Console.WriteLine($"DOOR {k} cell={cells.GetValueOrDefault(cell).rec?.EditorID ?? cell.ToString()} base={b.EditorID} model={b.Model?.File} flags={b.Flags} ours={ourRefs.Contains(k)} winner={from} disabled={(r.MajorRecordFlagsRaw & 0x800) != 0} parent={r.EnableParent?.Reference.FormKey.ToString() ?? "-"} lock={(r.Lock == null ? "-" : r.Lock.Level + (r.Lock.Key.IsNull ? "" : " key")) } pos={r.Placement?.Position} xtel={dest}");
            }
            return;
        }
        var a = what.Split(':'); float x = float.Parse(a[1]), y = float.Parse(a[2]), rr = float.Parse(a[3]);
        foreach (var (fk, (n, from)) in Survey.Winners<INavigationMeshGetter>(mods))
        {
            if (n.Data is not { } d || d.Vertices.Count == 0) continue;
            if (d.Parent is not IWorldspaceNavmeshParentGetter wp || wp.Parent.FormKey != FormKey.Factory("23D689:Black Marsh.esm")) continue;
            var v = d.Vertices;
            for (var i = 0; i < d.Triangles.Count; i++)
            {
                var t = d.Triangles[i].Vertices; var p = v[t.X]; var q = v[t.Y]; var s = v[t.Z];
                float cx = (p.X + q.X + s.X) / 3, cy = (p.Y + q.Y + s.Y) / 3, cz = (p.Z + q.Z + s.Z) / 3;
                if (Math.Abs(cx - x) > rr || Math.Abs(cy - y) > rr) continue;
                Console.WriteLine($"NAVM {fk} {from} tri={i} centre={cx:F0},{cy:F0},{cz:F0} cell={(int)Math.Floor(cx / 4096)},{(int)Math.Floor(cy / 4096)}");
            }
        }
    }
}
