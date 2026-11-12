using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using Noggog;

// placecheck <Argonia.esp> <plugins in load order...>: every actor and object Argonia.esp places (all worlds and
// interiors), read from the built ESP against the load order's winners. Exit 1 on any failure.
//   Actors: the winning navmesh under the feet (fail over 40 above it, below it by more than the 1-unit rounding, or no
//   triangle within 150 horizontally); the body (fail if a static's or furniture's mesh within 200 units,
//   whose bounding box holds the actor, crosses a 40-wide column 30 to 110 above the feet: inside a wall or a table).
//   An actor under the water with no navmesh swims; an actor the builder names as standing (Standing) has no navmesh by
//   the host's making and is checked on its floor instead.
//   WARN (not a failure): no floor (land, a model's mesh, water) within 40 under the feet: a navmesh over nothing. Settle
//   moves such an actor to the nearest triangle of the space's navmeshes (within 1200) whose floor is BM&V's own and proven.
//   A navmesh more than 1000 above or below the feet is another storey and not this actor's.
//   Models: every ref of ours, and every ref whose bounds hold one of ours (the host a quest uses as a place), fails
//   when its base's model resolves in no archive or loose file of the load order (Models).
//   Objects: the bottom of the bounds against the surface nearest it (the land, a static, furniture, a container; fail
//   floating or sunk by more than 10); a structure (256 or more across) may stand sunk in the ground or the water as
//   Bethesda sinks foundations, and fails only floating. Markers, zones, effects, lights and merchant chests are skipped.
//   Inside: an object of ours (the same ones the Objects check covers) fails when its bounds (the base's, under the ref's
//   rotation and scale, shrunk by 4 units on every side so the floor it rests on and a wall it leans on never count) are
//   crossed by a triangle of the mesh of another winning static, moveable static, furniture or activator of the load order
//   (separating-axis triangle-box test on the meshes, never the other's bounding box).
//   Nordic: every object Argonia.esp places (ours and its overrides) fails when its base's model path holds a Nordic
//   fragment (NordicFragments, decision 0006). Actors are not checked.
// Settle (seed, after every builder): each object that fails is moved up or down onto the surface the check measured.
// Game files are read only (decision 0003).
static class PlaceCheck
{
    // Actors placed where the host has no navmesh (the Reed's house: BM&V's sinking cabin has none in its rooms).
    public static readonly HashSet<string> Standing = ["ARG_NeshDeekaRef", "ARG_MQ03_SaltsTheCatchRef", "ARG_BC_NeverSoldRef"];

    sealed record Nav(FormKey Parent, List<(P3Float a, P3Float b, P3Float c)> Tris);
    public sealed record Result(FormKey Ref, string Where, string? EditorId, P3Float At, string? Fail, string Detail, float? FixZ, bool Warn, P3Float? MoveTo = null);

    public static int Run(string esp, string[] paths)
    {
        var mods = Survey.Load(paths); var ours = SkyrimMod.CreateFromBinaryOverlay(esp, SkyrimRelease.SkyrimSE, Survey.NoStrings);
        var results = Check(mods.Append(ours).ToList(), ours.ModKey, new Surface.Assets(paths));
        foreach (var r in results)
            Console.WriteLine($"  {(r.Fail != null ? "FAIL" : r.Warn ? "WARN" : "PASS")} {r.Where} {r.EditorId} ({r.Ref.IDString()}) at {r.At.X:F0},{r.At.Y:F0},{r.At.Z:F0}: {r.Fail ?? r.Detail}");
        var failed = results.Count(r => r.Fail != null);
        Console.WriteLine($"placecheck: {results.Count} checked, {failed} failed, {results.Count(r => r.Warn)} warned (for the walk)");
        var models = Models(mods.Append(ours).ToList(), ours.ModKey, new Surface.Assets(paths));
        foreach (var r in models.Where(r => r.Fail != null)) Console.WriteLine($"  FAIL model {r.Where} {r.EditorId} ({r.Ref.IDString()}:{r.Ref.ModKey}): {r.Fail}");
        var mfailed = models.Count(r => r.Fail != null);
        Console.WriteLine($"placecheck models: {models.Count} checked ({models.Count(r => r.Ref.ModKey == ours.ModKey)} ours, {models.Count(r => r.Ref.ModKey != ours.ModKey)} hosts), {mfailed} failed");
        var inside = Inside(mods.Append(ours).ToList(), ours.ModKey, new Surface.Assets(paths));
        foreach (var r in inside.Where(r => r.Fail != null)) Console.WriteLine($"  FAIL inside {r.Where} {r.EditorId} ({r.Ref.IDString()}): {r.Fail}");
        var ifailed = inside.Count(r => r.Fail != null);
        Console.WriteLine($"placecheck inside: {inside.Count} checked, {ifailed} failed");
        var nordic = NordicCheck(mods.Append(ours).ToList(), ours.ModKey);
        foreach (var r in nordic.Where(r => r.Fail != null)) Console.WriteLine($"  FAIL nordic {r.EditorId} ({r.Ref.IDString()}): {r.Fail}");
        var nfailed = nordic.Count(r => r.Fail != null);
        Console.WriteLine($"placecheck nordic: {nordic.Count} checked, {nfailed} failed");
        return failed + mfailed + ifailed + nfailed == 0 ? 0 : 1;
    }

    // Fragments of Skyrim's Nordic culture in a model path (decision 0006: nothing we add carries a Nordic element); the
    // folders of the hold cities, the Nordic farm and ruin kits and Talos, as tools/places/check.py's NORDIC_MODEL lists them.
    public static readonly string[] NordicFragments = ["WhiteRun", "Windhelm", "Solitude", "Markarth", "Riften", "Winterhold", "Dawnstar",
        "Falkreath", "Morthal", "Riverwood", "Nordic", "Farmhouse", "Talos"];

    // Every object Argonia.esp places (ours and its overrides) whose base's model path holds a Nordic fragment.
    public static List<Result> NordicCheck(List<ISkyrimModGetter> all, ModKey ours)
    {
        var models = new Dictionary<FormKey, (string? EditorID, string? Model)>();
        foreach (var m in all)
            foreach (var r in m.EnumerateMajorRecords())
                if (r is IModeledGetter md && r is not IPlacedGetter) models[r.FormKey] = (r.EditorID, md.Model?.File.DataRelativePath.Path);
        var results = new List<Result>();
        var mod = all.First(m => m.ModKey == ours);
        foreach (var o in mod.EnumerateMajorRecords<IPlacedObjectGetter>())
        {
            if (!models.TryGetValue(o.Base.FormKey, out var b) || string.IsNullOrEmpty(b.Model)) continue;
            var hit = NordicFragments.Any(f => b.Model.Contains(f, StringComparison.OrdinalIgnoreCase));
            results.Add(new Result(o.FormKey, "", b.EditorID ?? o.EditorID, o.Placement?.Position ?? new P3Float(), hit ? b.Model : null, b.Model, null, false));
        }
        return results;
    }

    const float InsideMargin = 4;

    // The inside check: see the header.
    public static List<Result> Inside(List<ISkyrimModGetter> all, ModKey ours, Surface.Assets assets)
    {
        Surface.Bases(all);
        var (types, bounds, containerModels) = BaseTypes(all);
        Surface.AddBases(containerModels);
        var (refsIn, mine) = Winners(all, ours);
        var merchant = all.SelectMany(m => m.Factions).Select(f => f.MerchantContainer.FormKey).Where(k => !k.IsNull).ToHashSet();
        static P3Float[] Corners(IObjectBoundsGetter ob, float[] rot, P3Float at, float s) =>
            [.. new[] { ob.First.X, ob.Second.X }.SelectMany(x => new[] { ob.First.Y, ob.Second.Y }.SelectMany(y => new[] { ob.First.Z, ob.Second.Z }.Select(z => Surface.Add(at, Surface.Mul(rot, new P3Float(x, y, z), s)))))];
        var results = new List<Result>();
        foreach (var (key, (space, where)) in mine.OrderBy(e => e.Value.where).ThenBy(e => refsIn[e.Value.space][e.Key].EditorID))
        {
            if (refsIn[space][key] is not IPlacedObjectGetter o || o.Placement is not { } pl) continue;
            if (merchant.Contains(key) || o.Primitive != null || SkipBase(types, o.Base.FormKey) || bounds.GetValueOrDefault(o.Base.FormKey) is not { } ob) continue;
            var s = o.Scale ?? 1; var rot = Surface.RefRot(pl.Rotation);
            var inv = new[] { rot[0], rot[3], rot[6], rot[1], rot[4], rot[7], rot[2], rot[5], rot[8] };
            var cs = Corners(ob, rot, pl.Position, s);
            var (x0, x1, y0, y1, z0, z1) = (cs.Min(c => c.X) - InsideMargin, cs.Max(c => c.X) + InsideMargin, cs.Min(c => c.Y) - InsideMargin, cs.Max(c => c.Y) + InsideMargin, cs.Min(c => c.Z) - InsideMargin, cs.Max(c => c.Z) + InsideMargin);
            // the box in the ref's own frame, shrunk by the margin (world units) on every side, the floor under it included
            float m = InsideMargin / s;
            P3Float bc = new((ob.First.X + ob.Second.X) / 2, (ob.First.Y + ob.Second.Y) / 2, (ob.First.Z + ob.Second.Z) / 2);
            float[] half = [(ob.Second.X - ob.First.X) / 2 - m, (ob.Second.Y - ob.First.Y) / 2 - m, (ob.Second.Z - ob.First.Z) / 2 - m];
            if (half.Any(h => h <= 0)) continue;
            (float depth, string name, FormKey id)? worst = null;
            foreach (var other in refsIn[space].Values.OfType<IPlacedObjectGetter>())
            {
                if (other.FormKey == key || other.Placement is not { } op || (other.MajorRecordFlagsRaw & 0x800) != 0) continue;
                if (types.GetValueOrDefault(other.Base.FormKey) is not ("STAT" or "MSTT" or "FURN" or "ACTI") || SkipBase(types, other.Base.FormKey)) continue;
                if (Surface.Base(other.Base.FormKey) is not { } bs || bs.Model is not { } model || bs.ObjectBounds is not { } obo) continue;
                var os = other.Scale ?? 1; var orot = Surface.RefRot(op.Rotation);
                var oc = Corners(obo, orot, op.Position, os);
                if (oc.Max(c => c.X) < x0 || oc.Min(c => c.X) > x1 || oc.Max(c => c.Y) < y0 || oc.Min(c => c.Y) > y1 || oc.Max(c => c.Z) < z0 || oc.Min(c => c.Z) > z1) continue;
                if (Surface.Mesh(assets, model) is not { } tris) continue;
                float best = 0;
                foreach (var (a0, b0, c0) in tris)
                {
                    P3Float L(P3Float v) { var w = Surface.Add(op.Position, Surface.Mul(orot, v, os)); var d = Surface.Mul(inv, new P3Float(w.X - pl.Position.X, w.Y - pl.Position.Y, w.Z - pl.Position.Z), 1 / s); return new P3Float(d.X - bc.X, d.Y - bc.Y, d.Z - bc.Z); }
                    var a = L(a0); var b = L(b0); var c = L(c0);
                    if (!TriBox(a, b, c, half)) continue;
                    // how far in: the smallest overlap of the triangle's extent with the unshrunk box over the three axes
                    float Ov(Func<P3Float, float> f, float h) => MathF.Min(MathF.Max(f(a), MathF.Max(f(b), f(c))), h) - MathF.Max(MathF.Min(f(a), MathF.Min(f(b), f(c))), -h);
                    var depth = MathF.Min(Ov(v => v.X, half[0] + m), MathF.Min(Ov(v => v.Y, half[1] + m), Ov(v => v.Z, half[2] + m))) * s;
                    best = MathF.Max(best, depth);
                }
                if (best > 0 && (worst == null || best > worst.Value.depth)) worst = (best, bs.EditorID ?? model, other.FormKey);
            }
            var fail = worst is { } w ? $"inside {w.name} ({w.id.IDString()}:{w.id.ModKey}) by {w.depth:F0} units" : null;
            results.Add(new Result(key, where, o.EditorID, pl.Position, fail, fail ?? "clear", null, false));
        }
        return results;
    }

    // Triangle-box overlap (Akenine-Moller): the box is centred on the origin with the half extents; the triangle is in the same frame.
    static bool TriBox(P3Float a, P3Float b, P3Float c, float[] h)
    {
        static float[] V(P3Float p) => [p.X, p.Y, p.Z];
        float[][] v = [V(a), V(b), V(c)];
        float[][] e = [[b.X - a.X, b.Y - a.Y, b.Z - a.Z], [c.X - b.X, c.Y - b.Y, c.Z - b.Z], [a.X - c.X, a.Y - c.Y, a.Z - c.Z]];
        static float[] Cr(float[] u, float[] w) => [u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0]];
        bool Sep(float[] ax)
        {
            if (MathF.Abs(ax[0]) + MathF.Abs(ax[1]) + MathF.Abs(ax[2]) < 1e-9f) return false;
            float p0 = v[0][0] * ax[0] + v[0][1] * ax[1] + v[0][2] * ax[2], p1 = v[1][0] * ax[0] + v[1][1] * ax[1] + v[1][2] * ax[2], p2 = v[2][0] * ax[0] + v[2][1] * ax[1] + v[2][2] * ax[2];
            var r = h[0] * MathF.Abs(ax[0]) + h[1] * MathF.Abs(ax[1]) + h[2] * MathF.Abs(ax[2]);
            return MathF.Min(p0, MathF.Min(p1, p2)) > r || MathF.Max(p0, MathF.Max(p1, p2)) < -r;
        }
        for (var i = 0; i < 3; i++) if (v.Max(p => p[i]) < -h[i] || v.Min(p => p[i]) > h[i]) return false;
        for (var i = 0; i < 3; i++)
            for (var j = 0; j < 3; j++)
            {
                var u = new float[3]; u[j] = 1;
                if (Sep(Cr(e[i], u))) return false;
            }
        return !Sep(Cr(e[0], e[1]));
    }

    static bool SkipBase(Dictionary<FormKey, string> types, FormKey b) => !types.TryGetValue(b, out var ty) || ty is "LIGH" or "SOUN" or "IDLM" or "DOOR"
        || (Surface.Base(b)?.EditorID ?? "").Contains("Marker", StringComparison.OrdinalIgnoreCase) || (Surface.Base(b)?.Model ?? "").Contains("Effects", StringComparison.OrdinalIgnoreCase);

    // The record type, bounds and model of every base the checks read (the load order's winners).
    static (Dictionary<FormKey, string> types, Dictionary<FormKey, IObjectBoundsGetter> bounds, Dictionary<FormKey, (string? EditorID, string? Model, IObjectBoundsGetter? ObjectBounds)> containerModels) BaseTypes(List<ISkyrimModGetter> all)
    {
        var types = new Dictionary<FormKey, string>(); var bounds = new Dictionary<FormKey, IObjectBoundsGetter>();
        void T<R>(IEnumerable<R> rs, string ty) where R : ISkyrimMajorRecordGetter
        { foreach (var r in rs) { types[r.FormKey] = ty; if (r is IObjectBoundedGetter b && b.ObjectBounds != null) bounds[r.FormKey] = b.ObjectBounds; } }
        var containerModels = new Dictionary<FormKey, (string? EditorID, string? Model, IObjectBoundsGetter? ObjectBounds)>();
        foreach (var m in all)
        {
            T(m.Statics, "STAT"); T(m.MoveableStatics, "MSTT"); T(m.Furniture, "FURN"); T(m.Containers, "CONT");
            T(m.Books, "BOOK"); T(m.MiscItems, "MISC"); T(m.Ingredients, "INGR"); T(m.Activators, "ACTI");
            T(m.Lights, "LIGH"); T(m.Doors, "DOOR"); T(m.Florae, "FLOR"); T(m.Weapons, "WEAP");
            T(m.Armors, "ARMO"); T(m.Ingestibles, "ALCH"); T(m.SoundMarkers, "SOUN"); T(m.IdleMarkers, "IDLM");
            foreach (var c in m.Containers) containerModels[c.FormKey] = (c.EditorID, c.Model?.File.DataRelativePath.Path, c.ObjectBounds);
            T(m.Trees, "TREE");
            foreach (var t in m.Trees) containerModels[t.FormKey] = (t.EditorID, t.Model?.File.DataRelativePath.Path, t.ObjectBounds);
        }
        return (types, bounds, containerModels);
    }

    // The winning refs of every world and interior cell (the last plugin's copy wins), and ours to check.
    static (Dictionary<FormKey, Dictionary<FormKey, IPlacedGetter>> refsIn, Dictionary<FormKey, (FormKey space, string where)> mine) Winners(List<ISkyrimModGetter> all, ModKey ours)
    {
        var refsIn = new Dictionary<FormKey, Dictionary<FormKey, IPlacedGetter>>();
        var mine = new Dictionary<FormKey, (FormKey space, string where)>();
        foreach (var m in all)
        {
            void Add(FormKey space, string where, IEnumerable<IPlacedGetter> rs)
            {
                if (!refsIn.TryGetValue(space, out var d)) refsIn[space] = d = [];
                foreach (var r in rs)
                {
                    if ((r.MajorRecordFlagsRaw & 0x20) != 0) { d.Remove(r.FormKey); continue; } // deleted
                    d[r.FormKey] = r;
                    if (m.ModKey == ours && r.FormKey.ModKey == ours) mine[r.FormKey] = (space, where);
                }
            }
            foreach (var w in m.Worldspaces)
            {
                if (w.TopCell != null) Add(w.FormKey, w.EditorID ?? "", w.TopCell.Persistent.Concat(w.TopCell.Temporary));
                foreach (var c in w.SubCells.SelectMany(b => b.Items).SelectMany(s => s.Items)) Add(w.FormKey, w.EditorID ?? "", c.Persistent.Concat(c.Temporary));
            }
            foreach (var c in m.Cells.Records.SelectMany(b => b.SubBlocks).SelectMany(s => s.Cells)) Add(c.FormKey, c.EditorID ?? c.FormKey.ToString(), c.Persistent.Concat(c.Temporary));
        }
        return (refsIn, mine);
    }

    // Seed's last step: every object of ours that fails rests on the surface the check measured (same x, y; z only).
    public static void Settle(SkyrimMod mod, List<ISkyrimModGetter> mods, string[] paths)
    {
        var fixes = Check([.. mods, mod], mod.ModKey, new Surface.Assets(paths)).Where(r => r.Fail != null && r.FixZ != null).ToDictionary(r => r.Ref, r => r.FixZ!.Value);
        foreach (var o in mod.EnumerateMajorRecords<PlacedObject>())
            if (fixes.TryGetValue(o.FormKey, out var z)) o.Placement!.Position = new P3Float(o.Placement.Position.X, o.Placement.Position.Y, MathF.Round(z));
        Console.WriteLine($"placecheck settle: {fixes.Count} objects rested on their surface");
        // an actor on a navmesh with no floor under it moves to the nearest triangle of that navmesh whose floor is proven
        var moves = Check([.. mods, mod], mod.ModKey, new Surface.Assets(paths)).Where(r => r.Warn && r.MoveTo != null).ToDictionary(r => r.Ref, r => r.MoveTo!.Value);
        foreach (var a in mod.EnumerateMajorRecords<PlacedNpc>())
            if (moves.TryGetValue(a.FormKey, out var to)) a.Placement!.Position = to;
        Console.WriteLine($"placecheck settle: {moves.Count} actors moved off a navmesh with no floor ({string.Join(", ", moves.Keys.Select(k => k.IDString()))})");
    }

    public static List<Result> Check(List<ISkyrimModGetter> all, ModKey ours, Surface.Assets assets)
    {
        Surface.Bases(all);
        var types = new Dictionary<FormKey, string>(); var bounds = new Dictionary<FormKey, IObjectBoundsGetter>();
        void T<R>(IEnumerable<R> rs, string ty) where R : ISkyrimMajorRecordGetter
        { foreach (var r in rs) { types[r.FormKey] = ty; if (r is IObjectBoundedGetter b && b.ObjectBounds != null) bounds[r.FormKey] = b.ObjectBounds; } }
        var containerModels = new Dictionary<FormKey, (string? EditorID, string? Model, IObjectBoundsGetter? ObjectBounds)>();
        foreach (var m in all)
        {
            T(m.Statics, "STAT"); T(m.MoveableStatics, "MSTT"); T(m.Furniture, "FURN"); T(m.Containers, "CONT");
            T(m.Books, "BOOK"); T(m.MiscItems, "MISC"); T(m.Ingredients, "INGR"); T(m.Activators, "ACTI");
            T(m.Lights, "LIGH"); T(m.Doors, "DOOR"); T(m.Florae, "FLOR"); T(m.Weapons, "WEAP");
            T(m.Armors, "ARMO"); T(m.Ingestibles, "ALCH"); T(m.SoundMarkers, "SOUN"); T(m.IdleMarkers, "IDLM");
            foreach (var c in m.Containers) containerModels[c.FormKey] = (c.EditorID, c.Model?.File.DataRelativePath.Path, c.ObjectBounds);
            T(m.Trees, "TREE"); // a giant tree's roots and platforms carry navmesh
            foreach (var t in m.Trees) containerModels[t.FormKey] = (t.EditorID, t.Model?.File.DataRelativePath.Path, t.ObjectBounds);
        }
        Surface.AddBases(containerModels); // a barrel's lid is a surface too

        // The winning navmeshes that carry data, by parent (world or interior cell).
        var navs = all.SelectMany(m => m.EnumerateMajorRecords<INavigationMeshGetter>().Where(r => r.Data != null)).GroupBy(r => r.FormKey).Select(g => g.Last())
            .Select(n =>
            {
                var d = n.Data!; var v = d.Vertices;
                var parent = d.Parent switch { IWorldspaceNavmeshParentGetter w => w.Parent.FormKey, ICellNavmeshParentGetter c => c.Parent.FormKey, _ => FormKey.Null };
                return new Nav(parent, d.Triangles.Select(t => (v[t.Vertices.X], v[t.Vertices.Y], v[t.Vertices.Z])).ToList());
            }).ToLookup(n => n.Parent);

        // The winning refs of every world and interior cell (the last plugin's copy wins), and ours to check.
        var refsIn = new Dictionary<FormKey, Dictionary<FormKey, IPlacedGetter>>();
        var mine = new Dictionary<FormKey, (FormKey space, string where)>();
        foreach (var m in all)
        {
            void Add(FormKey space, string where, IEnumerable<IPlacedGetter> rs)
            {
                if (!refsIn.TryGetValue(space, out var d)) refsIn[space] = d = [];
                foreach (var r in rs)
                {
                    if ((r.MajorRecordFlagsRaw & 0x20) != 0) { d.Remove(r.FormKey); continue; } // deleted
                    d[r.FormKey] = r;
                    if (m.ModKey == ours && r.FormKey.ModKey == ours) mine[r.FormKey] = (space, where);
                }
            }
            foreach (var w in m.Worldspaces)
            {
                if (w.TopCell != null) Add(w.FormKey, w.EditorID ?? "", w.TopCell.Persistent.Concat(w.TopCell.Temporary));
                foreach (var c in w.SubCells.SelectMany(b => b.Items).SelectMany(s => s.Items)) Add(w.FormKey, w.EditorID ?? "", c.Persistent.Concat(c.Temporary));
            }
            foreach (var c in m.Cells.Records.SelectMany(b => b.SubBlocks).SelectMany(s => s.Cells)) Add(c.FormKey, c.EditorID ?? c.FormKey.ToString(), c.Persistent.Concat(c.Temporary));
        }

        // The water height under a point: the exterior cell's own, else the world's default; an interior's if it has water.
        var worlds = all.SelectMany(m => m.Worldspaces).GroupBy(w => w.FormKey).ToDictionary(g => g.Key, g => g.Last());
        var cells = Survey.Winners<ICellGetter>(all);
        var extCells = all.SelectMany(m => m.Worldspaces.SelectMany(w => w.SubCells.SelectMany(b => b.Items).SelectMany(sb => sb.Items).Where(c => c.Grid != null).Select(c => (w.FormKey, c))))
            .GroupBy(e => (e.FormKey, e.c.Grid!.Point)).ToDictionary(g => g.Key, g => g.Last().c);
        float? Water(FormKey space, float x, float y)
        {
            if (worlds.TryGetValue(space, out var w))
                return extCells.TryGetValue((space, new P2Int((int)MathF.Floor(x / 4096), (int)MathF.Floor(y / 4096))), out var ec) && ec.WaterHeight is float eh && eh < 1e6f
                    ? eh : w.LandDefaults?.DefaultWaterHeight;
            return cells.TryGetValue(space, out var c) && c.rec.Flags.HasFlag(Cell.Flag.HasWater) ? c.rec.WaterHeight : null;
        }
        // Merchant chests are hidden under the world by design (Bethesda's vendors): not a placement to rest.
        var merchant = all.SelectMany(m => m.Factions).Select(f => f.MerchantContainer.FormKey).Where(k => !k.IsNull).ToHashSet();
        bool Skip(FormKey b) => !types.TryGetValue(b, out var ty) || ty is "LIGH" or "SOUN" or "IDLM" or "DOOR"
            || (Surface.Base(b)?.EditorID ?? "").Contains("Marker", StringComparison.OrdinalIgnoreCase) || (Surface.Base(b)?.Model ?? "").Contains("Effects", StringComparison.OrdinalIgnoreCase);

        // Every surface under x,y: each crossing of a static, furniture, activator or container mesh (not fires or items),
        // the land, the water.
        List<Surface.Hit> Under(FormKey space, FormKey self, float x, float y)
        {
            var near = refsIn[space].Values.OfType<IPlacedObjectGetter>().Where(o => o.Placement != null && (o.MajorRecordFlagsRaw & 0x800) == 0 && o.FormKey != self
                && types.GetValueOrDefault(o.Base.FormKey) is "STAT" or "FURN" or "ACTI" or "CONT" or "TREE" && !merchant.Contains(o.FormKey) && !(Surface.Base(o.Base.FormKey)?.EditorID ?? "").Contains("Marker", StringComparison.OrdinalIgnoreCase)
                && MathF.Abs(o.Placement.Position.X - x) < 3000 && MathF.Abs(o.Placement.Position.Y - y) < 3000);
            var hits = Surface.UnderRefs(near, assets, x, y, everyCrossing: true);
            float? landZ = worlds.ContainsKey(space) ? Surface.Land(all, space, x, y) : null;
            if (landZ is float lz) hits.Add(new Surface.Hit("land", FormKey.Null, FormKey.Null, null, "", lz, lz));
            if (Water(space, x, y) is float wz && (landZ == null || wz > landZ)) hits.Add(new Surface.Hit("water", FormKey.Null, FormKey.Null, null, "", wz, wz));
            return [.. hits.OrderByDescending(h => h.Top)];
        }
        static string List(List<Surface.Hit> hits) => " [" + string.Join(", ", hits.Take(6).Select(h => $"{h.EditorId ?? h.Kind} {h.Top:F0}")) + "]";

        // The nearest triangle centre of the space's navmeshes (within 1200) with a floor within 40 under it, not water.
        var taken = new List<P3Float>();
        P3Float? Proven(FormKey space, P3Float p)
        {
            foreach (var c in navs[space].SelectMany(n => n.Tris).Select(t => new P3Float((t.a.X + t.b.X + t.c.X) / 3, (t.a.Y + t.b.Y + t.c.Y) / 3, (t.a.Z + t.b.Z + t.c.Z) / 3))
                         .Where(c => Dist2(c, p) < 1200).OrderBy(c => Dist2(c, p) + MathF.Abs(c.Z - p.Z)))
            {
                var hs = Under(space, FormKey.Null, c.X, c.Y);
                var w = Water(space, c.X, c.Y);
                if (w is float wz && c.Z < wz - 1) continue;
                var onWater = w is float wz2 && c.Z - wz2 <= 40;
                // BM&V's own floor (never a prop we placed), and no two moved actors on one spot
                var sup = hs.Where(h => h.Kind != "water" && h.Ref.ModKey != ours).FirstOrDefault(h => h.Top <= c.Z + 10);
                if (!onWater && (sup == null || c.Z - sup.Top > 30) || taken.Any(t => Dist2(t, c) < 80)) continue;
                var to = new P3Float(MathF.Round(c.X), MathF.Round(c.Y), MathF.Round(c.Z)); taken.Add(to);
                return to;
            }
            return null;
        }

        var results = new List<Result>();
        foreach (var (key, (space, where)) in mine.OrderBy(e => e.Value.where).ThenBy(e => refsIn[e.Value.space][e.Key].EditorID))
        {
            var r = refsIn[space][key];
            if (r.Placement is not { } pl) continue;
            var p = pl.Position;
            string? fail = null, warn = null; string detail; float? fixZ = null; P3Float? moveTo = null;
            if (r is IPlacedNpcGetter)
            {
                // the navmesh: the nearest triangle (0 when under the feet), of those the one nearest in height
                var best = (gap: float.NaN, dist: float.MaxValue); var far = (dist: float.MaxValue, at: new P3Float());
                foreach (var n in navs[space])
                    foreach (var (a, b, c) in n.Tris)
                    {
                        var (dist, z) = Nearest2D(a, b, c, p.X, p.Y);
                        if (dist < far.dist) far = (dist, new P3Float((a.X + b.X + c.X) / 3, (a.Y + b.Y + c.Y) / 3, (a.Z + b.Z + c.Z) / 3));
                        if (dist > 150) continue;
                        var gap = p.Z - z;
                        if (MathF.Abs(gap) > 1000) continue; // a navmesh a storey or more away (another room of a shared cell) is not under this actor
                        if (dist < best.dist - 0.5f || (dist <= best.dist + 0.5f && MathF.Abs(gap) < MathF.Abs(best.gap))) best = (gap, dist);
                    }
                var hits = Under(space, key, p.X, p.Y);
                var water = Water(space, p.X, p.Y);
                var support = hits.Where(h => h.Kind != "water").FirstOrDefault(h => h.Top <= p.Z + 10);
                var floor = support == null ? float.NaN : p.Z - support.Top;
                if (float.IsNaN(best.gap) && water is float wz && p.Z < wz - 50) detail = "swimming (under the water, no navmesh)";
                else if (float.IsNaN(best.gap) && Standing.Contains(r.EditorID ?? ""))
                {
                    detail = $"standing (no navmesh in the host), floor {floor:+0;-0;0} on {support?.EditorId ?? support?.Kind}";
                    if (support == null || floor > 40 || floor < -1) fail = detail + List(hits);
                }
                else
                {
                    detail = float.IsNaN(best.gap) ? $"no navmesh within 150 (nearest {far.dist:F0} off, centre {far.at.X:F0},{far.at.Y:F0},{far.at.Z:F0})"
                        : $"navmesh gap {best.gap:F0} at {best.dist:F0} off, ground {(support == null ? "none" : $"{floor:+0;-0;0} on {support.EditorId ?? support.Kind}")}";
                    var onWater = water is float w2 && p.Z >= w2 - 1 && p.Z - w2 <= 40;
                    if (float.IsNaN(best.gap) || best.gap > 40 || best.gap < -1) fail = detail;
                    else if (!onWater && (support == null || floor > 40))
                    {
                        warn = "no floor under the navmesh (land, a model's mesh or its collision, water)" + List(hits);
                        moveTo = Proven(space, p);
                        if (moveTo is { } m) warn += $"; settle moves it to the nearest proven floor {m.X:F0},{m.Y:F0},{m.Z:F0} ({Dist2(m, p):F0} off)";
                    }
                }
                // the body: a static's or furniture's mesh within 200 whose box holds the actor, crossing its column
                foreach (var o in refsIn[space].Values.OfType<IPlacedObjectGetter>())
                {
                    if (o.Placement is not { } op || (o.MajorRecordFlagsRaw & 0x800) != 0 || Dist2(op.Position, p) > 200) continue;
                    if (types.GetValueOrDefault(o.Base.FormKey) is not ("STAT" or "FURN") || Skip(o.Base.FormKey)) continue;
                    if (Surface.Base(o.Base.FormKey) is not { } bs || bs.Model is not { } model || bs.ObjectBounds is not { } ob) continue;
                    var s = o.Scale ?? 1; var rot = Surface.RefRot(op.Rotation);
                    var inv = new[] { rot[0], rot[3], rot[6], rot[1], rot[4], rot[7], rot[2], rot[5], rot[8] };
                    var d = Surface.Mul(inv, new P3Float(p.X - op.Position.X, p.Y - op.Position.Y, p.Z + 60 - op.Position.Z), 1 / s);
                    if (d.X < ob.First.X || d.X > ob.Second.X || d.Y < ob.First.Y || d.Y > ob.Second.Y || d.Z < ob.First.Z || d.Z > ob.Second.Z) continue;
                    if (Surface.Mesh(assets, model) is { } tris && Body(tris, rot, op.Position, s, p))
                        fail = (fail == null ? "" : fail + "; ") + $"body inside {bs.EditorID} ({o.FormKey.IDString()}:{o.FormKey.ModKey})";
                }
            }
            else if (r is IPlacedObjectGetter o)
            {
                if (merchant.Contains(key) || o.Primitive != null || Skip(o.Base.FormKey)) continue;
                var ty = types[o.Base.FormKey];
                var s = o.Scale ?? 1; var rot = Surface.RefRot(pl.Rotation); var bottom = p.Z;
                var ob = bounds.GetValueOrDefault(o.Base.FormKey);
                if (ob != null)
                {
                    bottom = float.MaxValue;
                    foreach (var cx in new[] { ob.First.X, ob.Second.X }) foreach (var cy in new[] { ob.First.Y, ob.Second.Y }) foreach (var cz in new[] { ob.First.Z, ob.Second.Z })
                        bottom = MathF.Min(bottom, Surface.Add(p, Surface.Mul(rot, new P3Float(cx, cy, cz), s)).Z);
                }
                var hits = Under(space, key, p.X, p.Y);
                var big = ob != null && MathF.Max(ob.Second.X - ob.First.X, ob.Second.Y - ob.First.Y) * s >= 256 && ty is "STAT" or "ACTI" or "FLOR" or "MSTT";
                Surface.Hit? near;
                if (big)
                {
                    // the support: the land or water when the bottom is in them, else the highest surface no more than 10 above it
                    near = hits.Where(h => h.Kind is "land" or "water").FirstOrDefault(h => h.Top >= bottom) ?? hits.FirstOrDefault(h => h.Top <= bottom + 10);
                }
                else near = hits.MinBy(h => MathF.Abs(bottom - h.Top));
                var gap = near == null ? float.NaN : big ? MathF.Max(0, bottom - near.Top) : bottom - near.Top;
                detail = near == null ? "no surface" : $"{ty}{(big ? " structure" : "")} bottom {gap:+0;-0;0} on {near.EditorId ?? near.Kind}";
                if (near == null || gap > 10 || gap < -10) { fail = detail + List(hits); if (near != null) fixZ = p.Z - gap; }
            }
            else continue;
            results.Add(new Result(key, where, r.EditorID, p, fail, warn == null ? detail : detail + "; WARN " + warn, fixZ, warn != null, moveTo));
        }
        return results;
    }

    // The model-exists check: every ref of ours, and every load-order ref that hosts one of ours (its rotated, scaled bounds
    // hold our ref's point, z within 200: the building or floor a quest uses as a place), fails when its base names a model
    // that resolves in no archive or loose folder of the load order (matched without case, Surface.Assets). Bases with no
    // model are not checked; a host disabled at start is not a place.
    public static List<Result> Models(List<ISkyrimModGetter> all, ModKey ours, Surface.Assets assets)
    {
        var baseOf = new Dictionary<FormKey, (string? EditorID, string? Model, IObjectBoundsGetter? Bounds)>();
        foreach (var m in all)
            foreach (var r in m.EnumerateMajorRecords())
                if (r is IModeledGetter md && r is not IPlacedGetter)
                    baseOf[r.FormKey] = (r.EditorID, md.Model?.File.DataRelativePath.Path, (r as IObjectBoundedGetter)?.ObjectBounds);
        var spaces = new Dictionary<FormKey, (Dictionary<FormKey, (IPlacedObjectGetter r, string where)> objs, List<P3Float> ourAt)>();
        foreach (var m in all)
        {
            void Add(FormKey space, string where, IEnumerable<IPlacedGetter> rs)
            {
                if (!spaces.TryGetValue(space, out var d)) spaces[space] = d = ([], []);
                foreach (var r in rs)
                {
                    if (r.FormKey.ModKey == ours && m.ModKey == ours && r.Placement != null) d.ourAt.Add(r.Placement.Position);
                    if (r is not IPlacedObjectGetter o) continue;
                    if ((r.MajorRecordFlagsRaw & 0x20) != 0) d.objs.Remove(r.FormKey); else d.objs[r.FormKey] = (o, where);
                }
            }
            foreach (var w in m.Worldspaces)
            {
                if (w.TopCell != null) Add(w.FormKey, w.EditorID ?? "", w.TopCell.Persistent.Concat(w.TopCell.Temporary));
                foreach (var c in w.SubCells.SelectMany(b => b.Items).SelectMany(s => s.Items)) Add(w.FormKey, w.EditorID ?? "", c.Persistent.Concat(c.Temporary));
            }
            foreach (var c in m.Cells.Records.SelectMany(b => b.SubBlocks).SelectMany(s => s.Cells)) Add(c.FormKey, c.EditorID ?? c.FormKey.ToString(), c.Persistent.Concat(c.Temporary));
        }
        var exists = new Dictionary<string, bool>(StringComparer.OrdinalIgnoreCase);
        bool Resolves(string model)
        {
            if (exists.TryGetValue(model, out var e)) return e;
            var rel = model.Replace('/', '\\'); if (!rel.StartsWith("meshes\\", StringComparison.OrdinalIgnoreCase)) rel = "meshes\\" + rel;
            return exists[model] = assets.Read(rel) != null;
        }
        var results = new List<Result>();
        foreach (var (space, (objs, at)) in spaces)
        {
            if (at.Count == 0) continue;
            foreach (var (r, where) in objs.Values)
            {
                if (r.Placement is not { } pl || !baseOf.TryGetValue(r.Base.FormKey, out var b) || string.IsNullOrEmpty(b.Model)) continue;
                if (r.FormKey.ModKey != ours)
                {
                    if ((r.MajorRecordFlagsRaw & 0x800) != 0 || b.Bounds is not { } ob) continue;
                    var s = r.Scale ?? 1; var rot = Surface.RefRot(pl.Rotation);
                    var inv = new[] { rot[0], rot[3], rot[6], rot[1], rot[4], rot[7], rot[2], rot[5], rot[8] };
                    bool Holds(P3Float p)
                    {
                        if (MathF.Abs(p.X - pl.Position.X) > 8000 || MathF.Abs(p.Y - pl.Position.Y) > 8000) return false;
                        var d = Surface.Mul(inv, new P3Float(p.X - pl.Position.X, p.Y - pl.Position.Y, p.Z - pl.Position.Z), 1 / s);
                        return d.X >= ob.First.X && d.X <= ob.Second.X && d.Y >= ob.First.Y && d.Y <= ob.Second.Y && d.Z >= ob.First.Z - 200 / s && d.Z <= ob.Second.Z + 200 / s;
                    }
                    if (!at.Any(Holds)) continue;
                }
                var ok = Resolves(b.Model!);
                results.Add(new Result(r.FormKey, where, b.EditorID ?? r.EditorID, pl.Position, ok ? null : $"model {b.Model} is in no archive or loose folder of the load order", b.Model!, null, false));
            }
        }
        return results;
    }

    static float Dist2(P3Float a, P3Float b) => MathF.Sqrt((a.X - b.X) * (a.X - b.X) + (a.Y - b.Y) * (a.Y - b.Y));

    // The horizontal distance from x,y to a triangle (0 inside) and the triangle's height at the nearest point.
    static (float dist, float z) Nearest2D(P3Float a, P3Float b, P3Float c, float x, float y)
    {
        if (x < MathF.Min(a.X, MathF.Min(b.X, c.X)) - 150 || x > MathF.Max(a.X, MathF.Max(b.X, c.X)) + 150
            || y < MathF.Min(a.Y, MathF.Min(b.Y, c.Y)) - 150 || y > MathF.Max(a.Y, MathF.Max(b.Y, c.Y)) + 150)
            return (MathF.Sqrt((x - a.X) * (x - a.X) + (y - a.Y) * (y - a.Y)), a.Z);
        var den = (b.Y - c.Y) * (a.X - c.X) + (c.X - b.X) * (a.Y - c.Y);
        if (MathF.Abs(den) < 1e-6f) return (float.MaxValue, 0);
        var l1 = ((b.Y - c.Y) * (x - c.X) + (c.X - b.X) * (y - c.Y)) / den; var l2 = ((c.Y - a.Y) * (x - c.X) + (a.X - c.X) * (y - c.Y)) / den; var l3 = 1 - l1 - l2;
        if (l1 >= 0 && l2 >= 0 && l3 >= 0) return (0, l1 * a.Z + l2 * b.Z + l3 * c.Z);
        var best = (dist: float.MaxValue, z: 0f);
        foreach (var (u, v) in new[] { (a, b), (b, c), (c, a) })
        {
            float ex = v.X - u.X, ey = v.Y - u.Y, len = ex * ex + ey * ey;
            var t = len < 1e-6f ? 0 : Math.Clamp(((x - u.X) * ex + (y - u.Y) * ey) / len, 0, 1);
            float px = u.X + t * ex, py = u.Y + t * ey, d = MathF.Sqrt((x - px) * (x - px) + (y - py) * (y - py));
            if (d < best.dist) best = (d, u.Z + t * (v.Z - u.Z));
        }
        return best;
    }

    // Whether a model's triangles cross an actor's body at the feet p: a vertical segment 30..110 up and horizontal
    // segments 40 wide at 40, 80 and 110 up (below 30 is the floor, steps and the slope the actor stands on).
    static bool Body(List<(P3Float a, P3Float b, P3Float c)> tris, float[] rot, P3Float origin, float scale, P3Float p)
    {
        var segs = new List<(P3Float, P3Float)> { (new(p.X, p.Y, p.Z + 30), new(p.X, p.Y, p.Z + 110)) };
        foreach (var h in new[] { 40f, 80f, 110f })
        {
            segs.Add((new(p.X - 20, p.Y, p.Z + h), new(p.X + 20, p.Y, p.Z + h)));
            segs.Add((new(p.X, p.Y - 20, p.Z + h), new(p.X, p.Y + 20, p.Z + h)));
        }
        foreach (var (a0, b0, c0) in tris)
        {
            var a = Surface.Add(origin, Surface.Mul(rot, a0, scale)); var b = Surface.Add(origin, Surface.Mul(rot, b0, scale)); var c = Surface.Add(origin, Surface.Mul(rot, c0, scale));
            if (MathF.Max(a.X, MathF.Max(b.X, c.X)) < p.X - 21 || MathF.Min(a.X, MathF.Min(b.X, c.X)) > p.X + 21
                || MathF.Max(a.Y, MathF.Max(b.Y, c.Y)) < p.Y - 21 || MathF.Min(a.Y, MathF.Min(b.Y, c.Y)) > p.Y + 21
                || MathF.Max(a.Z, MathF.Max(b.Z, c.Z)) < p.Z + 30 || MathF.Min(a.Z, MathF.Min(b.Z, c.Z)) > p.Z + 110) continue;
            foreach (var (s0, s1) in segs) if (Crosses(s0, s1, a, b, c)) return true;
        }
        return false;
    }

    // Segment-triangle intersection (Moller-Trumbore).
    static bool Crosses(P3Float s0, P3Float s1, P3Float a, P3Float b, P3Float c)
    {
        static P3Float Sub(P3Float u, P3Float v) => new(u.X - v.X, u.Y - v.Y, u.Z - v.Z);
        static P3Float Cross(P3Float u, P3Float v) => new(u.Y * v.Z - u.Z * v.Y, u.Z * v.X - u.X * v.Z, u.X * v.Y - u.Y * v.X);
        static float Dot(P3Float u, P3Float v) => u.X * v.X + u.Y * v.Y + u.Z * v.Z;
        var dir = Sub(s1, s0); var e1 = Sub(b, a); var e2 = Sub(c, a); var h = Cross(dir, e2); var det = Dot(e1, h);
        if (MathF.Abs(det) < 1e-7f) return false;
        var f = 1 / det; var sv = Sub(s0, a); var u = f * Dot(sv, h); if (u < 0 || u > 1) return false;
        var q = Cross(sv, e1); var v = f * Dot(dir, q); if (v < 0 || u + v > 1) return false;
        var t = f * Dot(e2, q); return t >= 0 && t <= 1;
    }
}
