using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using Noggog;
// inspect <what> <plugins...>: read-only questions about the load order.
//   player   who overrides the Player NPC and the playable races, with outfit, skin and default items
//   movt     every plugin's movement types and their speeds
//   ref:<formkey>   a placed object's position in each plugin, and the objects near it there
//   navnear:<x>:<y>:<z>[;...]   per spot, the winning navmeshes near it (NAVNEAR_IN=<text> keeps those whose world or cell
//            names it), with the nearest triangle's centre and height
//   near:<x>:<y>:<z>:<r>   every placed object and actor of the Black Marsh and Valenwood plugins within r of a spot
//   items:<regex>   winning items (misc, armour, key, book, ingredient, potion) whose form key, editor id, name or model match
//   cellrefs:<cell>, cellat:<cell>:<x>,<y>[;...], cellgrid:<cell>:<x>:<y>:<z>:<step>   an interior's references and
//            navmeshes, the surfaces under points, a 13 x 13 map of the surface nearest z and the navmesh's height
//   surroundings:<spot>[;...]   the raw facts round a spot as JSON, put into words by tools/argonia_world/surroundings.py
//   the rest are named at their branch below
static class Inspect
{
    public static void Run(string what, string[] paths)
    {
        var mods = Survey.Load(paths);
        if (what.StartsWith("surroundings:")) { Surroundings.Run(what[13..], mods, paths); return; }  // Surroundings.cs
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
        if (what.StartsWith("navnear:"))  // navnear:<x>:<y>:<z>[;...]: per spot, the winning navmeshes with a triangle within 1500 of it and 1000 of its height, nearest first (the nearest triangle's centre and the navmesh's world or cell)
        {
            var navs = Survey.Winners<INavigationMeshGetter>(mods);
            foreach (var spot in what[8..].Split(';'))
            {
                var p = spot.Split(':').Select(float.Parse).ToArray();
                var near = new List<(float d, float x, float y, float z, FormKey m, string parent)>();
                foreach (var (k, (nv, _)) in navs)
                {
                    if (nv.Data is not { } d || d.Triangles.Count == 0) continue;
                    var v = d.Vertices; var best = (dist: float.MaxValue, z: 0f, x: 0f, y: 0f);
                    foreach (var t in d.Triangles)
                    {
                        P3Float va = v[t.Vertices.X], vb = v[t.Vertices.Y], vc = v[t.Vertices.Z];
                        var r = PlaceCheck.Nearest2D(va, vb, vc, p[0], p[1]);
                        if (MathF.Abs(r.z - p[2]) < 1000 && r.dist < best.dist) best = (r.dist, r.z, (va.X + vb.X + vc.X) / 3, (va.Y + vb.Y + vc.Y) / 3);
                    }
                    var parent = d.Parent switch { IWorldspaceNavmeshParentGetter w => $"world {w.Parent.FormKey} {w.Coordinates.X},{w.Coordinates.Y}", ICellNavmeshParentGetter cp => $"cell {cp.Parent.FormKey}", _ => "?" };
                    if (best.dist < 1500 && (Environment.GetEnvironmentVariable("NAVNEAR_IN") is not { } only || parent.Contains(only))) near.Add((best.dist, best.x, best.y, best.z, k, parent));
                }
                Console.WriteLine($"{spot}:");
                foreach (var n in near.OrderBy(n => n.d).Take(6)) Console.WriteLine($"  NAVNEAR {n.m}: {n.d:F0} off, z {n.z:F0}, triangle centre {n.x:F0},{n.y:F0}, {n.parent}");
            }
            return;
        }
        if (what.StartsWith("cellrefs:"))  // cellrefs:<interior cell>: its placed references (base, position) and its navmeshes' extent
        {
            var ck = FormKey.Factory(what[9..]);
            var bases = mods.SelectMany(m => m.EnumerateMajorRecords()).Where(r => r is not IPlacedGetter && r.EditorID != null).GroupBy(r => r.FormKey).ToDictionary(g => g.Key, g => g.Last().EditorID);
            var cells = mods.SelectMany(m => m.Cells.Records.SelectMany(b => b.SubBlocks).SelectMany(s => s.Cells)).Where(x => x.FormKey == ck).ToList();
            foreach (var r in cells.SelectMany(x => x.Persistent.Concat(x.Temporary)).GroupBy(r => r.FormKey).Select(g => g.Last()))
            {
                var (bk, pos) = r switch { IPlacedObjectGetter o => (o.Base.FormKey, o.Placement?.Position), IPlacedNpcGetter n => (n.Base.FormKey, n.Placement?.Position), _ => (FormKey.Null, null) };
                Console.WriteLine($"CELLREF {r.FormKey} {bases.GetValueOrDefault(bk) ?? bk.ToString()} pos={pos}");
            }
            var navs = Survey.Winners<INavigationMeshGetter>(mods);
            foreach (var nk in cells.SelectMany(x => x.NavigationMeshes.Select(n => n.FormKey)).Distinct())
                if (navs.TryGetValue(nk, out var nv) && nv.rec.Data is { } d && d.Vertices.Count > 0)
                    Console.WriteLine($"CELLNAV {nk} from {nv.from}: {d.Triangles.Count} tris, x {d.Vertices.Min(v => v.X):F0}..{d.Vertices.Max(v => v.X):F0} y {d.Vertices.Min(v => v.Y):F0}..{d.Vertices.Max(v => v.Y):F0} z {d.Vertices.Min(v => v.Z):F0}..{d.Vertices.Max(v => v.Z):F0}");
            return;
        }
        if (what.StartsWith("items:"))  // items:<regex>: every winning misc item, armour, key, book, ingredient and potion whose editor id, name or model matches (case ignored)
        {
            var rx = new System.Text.RegularExpressions.Regex(what[6..], System.Text.RegularExpressions.RegexOptions.IgnoreCase);
            var seen = new Dictionary<FormKey, string>();
            foreach (var m in mods)
                foreach (var r in m.EnumerateMajorRecords().Where(r => r is IMiscItemGetter or IArmorGetter or IKeyGetter or IBookGetter or IIngredientGetter or IIngestibleGetter))
                {
                    var name = (r as Mutagen.Bethesda.Plugins.Aspects.ITranslatedNamedGetter)?.Name?.String ?? "";
                    var model = r switch { IMiscItemGetter it => it.Model?.File.DataRelativePath.Path, IKeyGetter it => it.Model?.File.DataRelativePath.Path, IBookGetter it => it.Model?.File.DataRelativePath.Path,
                        IIngredientGetter it => it.Model?.File.DataRelativePath.Path, IIngestibleGetter it => it.Model?.File.DataRelativePath.Path, IArmorGetter it => it.WorldModel?.Male?.Model?.File.DataRelativePath.Path, _ => null } ?? "";
                    var line = $"{r.GetType().Name.Replace("BinaryOverlay", "")} {r.FormKey} {r.EditorID} '{name}' {model} (from {m.ModKey})";
                    if (rx.IsMatch(r.FormKey.ToString()) || rx.IsMatch(r.EditorID ?? "") || rx.IsMatch(name) || rx.IsMatch(model)) seen[r.FormKey] = line; else seen.Remove(r.FormKey);
                }
            foreach (var l in seen.Values) Console.WriteLine($"ITEM {l}");
            return;
        }
        if (what.StartsWith("near:"))  // near:<x>:<y>:<z>:<r>: every placed object and actor of the Black Marsh and Valenwood plugins within r of the spot (x, y and z), nearest first
        {
            var p = what[5..].Split(':').Select(float.Parse).ToArray();
            var bases = mods.SelectMany(m => m.EnumerateMajorRecords()).Where(r => r is not IPlacedGetter && r.EditorID != null).GroupBy(r => r.FormKey).ToDictionary(g => g.Key, g => g.Last().EditorID);
            var hits = new Dictionary<FormKey, (float d, string what)>();
            foreach (var m in mods.Where(mm => mm.ModKey.FileName.String.StartsWith("Black Marsh") || mm.ModKey.FileName.String.StartsWith("Valenwood")))
                foreach (var r in m.EnumerateMajorRecords<IPlacedGetter>())
                {
                    var (bk, pos) = r switch { IPlacedObjectGetter o => (o.Base.FormKey, o.Placement?.Position), IPlacedNpcGetter n => (n.Base.FormKey, n.Placement?.Position), _ => (FormKey.Null, null) };
                    if (pos is not { } q || MathF.Abs(q.X - p[0]) > p[3] || MathF.Abs(q.Y - p[1]) > p[3] || MathF.Abs(q.Z - p[2]) > p[3]) continue;
                    var d = MathF.Sqrt((q.X - p[0]) * (q.X - p[0]) + (q.Y - p[1]) * (q.Y - p[1]));
                    hits[r.FormKey] = (d, $"{r.FormKey} {bases.GetValueOrDefault(bk) ?? bk.ToString()} pos={q.X:F0},{q.Y:F0},{q.Z:F0}");
                }
            foreach (var h in hits.Values.OrderBy(h => h.d)) Console.WriteLine($"NEAR {h.d,6:F0}  {h.what}");
            return;
        }
        if (what.StartsWith("cellat:"))  // cellat:<interior cell>:<x>,<y>[;<x>,<y>...]: every surface under each point, highest first
        {
            var p = what[7..].Split(':');
            var ck = FormKey.Factory(p[0] + ":" + p[1]);
            var assets = new Surface.Assets(paths); Surface.Bases(mods);
            var refs = mods.SelectMany(m => m.Cells.Records.SelectMany(b => b.SubBlocks).SelectMany(s => s.Cells)).Where(x => x.FormKey == ck)
                .SelectMany(x => x.Persistent.Concat(x.Temporary)).OfType<IPlacedObjectGetter>().GroupBy(o => o.FormKey).Select(g => g.Last()).Where(o => o.Placement != null).ToList();
            foreach (var pt in p[2].Split(';'))
            {
                var xy = pt.Split(',').Select(float.Parse).ToArray();
                Console.WriteLine($"{xy[0]:F0},{xy[1]:F0}:");
                foreach (var h in Surface.UnderRefs(refs, assets, xy[0], xy[1], everyCrossing: true).Where(h => !h.Model.Contains("Effects", StringComparison.OrdinalIgnoreCase)).OrderByDescending(h => h.Top))
                    Console.WriteLine($"  {h.Kind,-6} top z {h.Top,8:F1}  {h.EditorId ?? "-"}  ref {h.Ref.IDString()}");
            }
            return;
        }
        if (what.StartsWith("cellgrid:"))  // cellgrid:<interior cell>:<x>:<y>:<z>:<step>: 13 x 13 map round x,y: the surface nearest z / the navmesh z
        {
            var p = what[9..].Split(':');
            var ck = FormKey.Factory(p[0] + ":" + p[1]);
            float x0 = float.Parse(p[2]), y0 = float.Parse(p[3]), z0 = float.Parse(p[4]), st = float.Parse(p[5]);
            var assets = new Surface.Assets(paths); Surface.Bases(mods);
            var cells = mods.SelectMany(m => m.Cells.Records.SelectMany(b => b.SubBlocks).SelectMany(s => s.Cells)).Where(x => x.FormKey == ck).ToList();
            var refs = cells.SelectMany(x => x.Persistent.Concat(x.Temporary)).OfType<IPlacedObjectGetter>().GroupBy(o => o.FormKey).Select(g => g.Last()).Where(o => o.Placement != null).ToList();
            var navs = Survey.Winners<INavigationMeshGetter>(mods);
            var mine = cells.SelectMany(x => x.NavigationMeshes.Select(n => n.FormKey)).Distinct().Where(navs.ContainsKey).Select(k => navs[k].rec).ToList();
            for (var gy = 6; gy >= -6; gy--)
            {
                var line = new System.Text.StringBuilder($"{y0 + gy * st,7:F0} ");
                for (var gx = -6; gx <= 6; gx++)
                {
                    float px = x0 + gx * st, py = y0 + gy * st;
                    var top = Surface.UnderRefs(refs, assets, px, py, everyCrossing: true).Where(h => !h.Model.Contains("Effects", StringComparison.OrdinalIgnoreCase)).MinBy(h => MathF.Abs(h.Top - z0));
                    var nav = Surface.NavZ(mine, px, py).Where(z => MathF.Abs(z - z0) < 300).DefaultIfEmpty(float.NaN).Max();
                    line.Append($"{(top == null ? "    ." : $"{top.Top,5:F0}")}/{(float.IsNaN(nav) ? "    ." : $"{nav,5:F0}")} ");
                }
                Console.WriteLine(line);
            }
            Console.WriteLine($"        x from {x0 - 6 * st:F0} to {x0 + 6 * st:F0} by {st:F0}");
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
