using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Aspects;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Noggog;

// inspect surroundings:<spot>[;<spot>...]: the raw facts round each spot as one JSON line (SURR {...}), for
// tools/argonia_world/surroundings.py to put into words. A spot is <cell form key>@<x>,<y>,<z>@<radius> or
// <placed ref form key>@<radius>. Facts: the cell (name, interior, world, water height), every surface under the spot
// (Surface.cs), the land's height, every placed thing within the radius (base sig, editor id, name, model, size,
// position, a door's destination cell), every person or creature within it (name, race, sex, class, aggression and the
// packages its AI uses, through the template chain), and the map markers within 12,000 units outdoors. Derived values
// only: form keys, editor ids, names, model paths, numbers.
static class Surroundings
{
    const float MarkerRange = 12000;

    public static void Run(string spec, List<ISkyrimModGetter> mods, string[] paths)
    {
        var assets = new Surface.Assets(paths); Surface.Bases(mods);
        var cells = new Dictionary<FormKey, ICellGetter>();
        var cellWorld = new Dictionary<FormKey, IWorldspaceGetter>();
        var refCell = new Dictionary<FormKey, FormKey>();
        var placed = new Dictionary<FormKey, IPlacedGetter>();
        var worlds = Survey.Winners<IWorldspaceGetter>(mods);
        foreach (var m in mods)
        {
            void Take(ICellGetter c, IWorldspaceGetter? w)
            {
                cells[c.FormKey] = c; if (w != null) cellWorld[c.FormKey] = w;
                foreach (var r in c.Persistent.Concat(c.Temporary)) { placed[r.FormKey] = r; refCell[r.FormKey] = c.FormKey; }
            }
            foreach (var c in m.Cells.Records.SelectMany(b => b.SubBlocks).SelectMany(s => s.Cells)) Take(c, null);
            foreach (var w in m.Worldspaces)
            {
                if (w.TopCell is { } tc) Take(tc, w);
                foreach (var c in w.SubCells.SelectMany(b => b.Items).SelectMany(s => s.Items)) Take(c, w);
            }
        }
        var npcs = Survey.Winners<INpcGetter>(mods); var races = Survey.Winners<IRaceGetter>(mods);
        var classes = Survey.Winners<IClassGetter>(mods); var packs = Survey.Winners<IPackageGetter>(mods);
        var factions = Survey.Winners<IFactionGetter>(mods);
        // every base a placed object may stand for, with what it reads as
        var bases = new Dictionary<FormKey, (string sig, string? edid, string? name, string? model, float size)>();
        foreach (var m in mods)
            foreach (var r in m.EnumerateMajorRecords())
            {
                if (r is IPlacedGetter or ICellGetter or IWorldspaceGetter or IDialogResponsesGetter or INavigationMeshGetter or ILandscapeGetter) continue;
                var model = (r as IModeledGetter)?.Model?.File.DataRelativePath.Path;
                if (model == null && r is not ISoundMarkerGetter) continue;
                var ob = (r as IObjectBoundedGetter)?.ObjectBounds;
                var size = ob == null ? 0 : Math.Max(ob.Second.X - ob.First.X, Math.Max(ob.Second.Y - ob.First.Y, ob.Second.Z - ob.First.Z));
                var sig = r.GetType().Name.Replace("BinaryOverlay", "").Replace("Getter", "");
                bases[r.FormKey] = (sig, r.EditorID, (r as ITranslatedNamedGetter)?.Name?.String, model, size);
            }
        var o = new JsonSerializerOptions { WriteIndented = false };
        foreach (var s in spec.Split(';', StringSplitOptions.RemoveEmptyEntries))
        {
            var part = s.Split('@');
            FormKey ck; P3Float at; float radius;
            if (part.Length == 3)
            {
                ck = FormKey.Factory(part[0]); var xyz = part[1].Split(',').Select(float.Parse).ToArray();
                at = new P3Float(xyz[0], xyz[1], xyz[2]); radius = float.Parse(part[2]);
            }
            else
            {
                var rk = FormKey.Factory(part[0]); radius = float.Parse(part[1]);
                if (!placed.TryGetValue(rk, out var pr)) { Console.WriteLine($"SURR {JsonSerializer.Serialize(new { spot = s, error = "no such placed reference" })}"); continue; }
                ck = refCell[rk]; at = Pos(pr) ?? new P3Float(0, 0, 0);
            }
            if (!cells.TryGetValue(ck, out var cell)) { Console.WriteLine($"SURR {JsonSerializer.Serialize(new { spot = s, error = "no such cell" })}"); continue; }
            var interior = cell.Flags.HasFlag(Cell.Flag.IsInteriorCell);
            var world = interior ? null : cellWorld.GetValueOrDefault(ck);
            float? water = interior ? (cell.Flags.HasFlag(Cell.Flag.HasWater) ? cell.WaterHeight : null)
                : (cell.WaterHeight is float wh && MathF.Abs(wh) < 1e9 ? wh : world?.LandDefaults?.DefaultWaterHeight);
            // the refs to look at: the interior's own, or the world's within the radius
            var near = placed.Where(kv => (kv.Value.MajorRecordFlagsRaw & 0x800) == 0 && Pos(kv.Value) is { } p
                && (interior ? refCell[kv.Key] == ck : !cells[refCell[kv.Key]].Flags.HasFlag(Cell.Flag.IsInteriorCell) && cellWorld.GetValueOrDefault(refCell[kv.Key])?.FormKey == world?.FormKey)
                && MathF.Abs(p.X - at.X) <= (interior ? 1e9 : Math.Max(radius, MarkerRange)) && MathF.Abs(p.Y - at.Y) <= (interior ? 1e9 : Math.Max(radius, MarkerRange)))
                .Select(kv => kv.Value).ToList();
            var surfaces = interior
                ? Surface.UnderRefs(near.OfType<IPlacedObjectGetter>().Where(r => r.Placement != null), assets, at.X, at.Y, everyCrossing: true)
                : Surface.Under(mods, assets, world!.FormKey, at.X, at.Y, 3000);
            float? land = interior ? null : Surface.Land(mods, world!.FormKey, at.X, at.Y);
            // the land round the spot: eight compass points at three distances (where the water lies)
            var ring = interior ? [] : (from a in Enumerable.Range(0, 8) from r in new[] { 400f, 1200f, 3000f }
                select new float?[] { a * 45, r, Surface.Land(mods, world!.FormKey, at.X + r * MathF.Cos(a * MathF.PI / 4), at.Y + r * MathF.Sin(a * MathF.PI / 4)) }).ToList();
            var things = new List<object>(); var people = new List<object>(); var markers = new List<object>();
            foreach (var r in near)
            {
                var p = Pos(r)!.Value; var d = MathF.Sqrt((p.X - at.X) * (p.X - at.X) + (p.Y - at.Y) * (p.Y - at.Y));
                if (r is IPlacedObjectGetter po && po.MapMarker is { } mm)
                {
                    if (!interior && d <= MarkerRange) markers.Add(new { name = mm.Name?.String, x = p.X, y = p.Y, z = p.Z, d });
                    continue;
                }
                if (d > radius || (interior && MathF.Abs(p.Z - at.Z) > radius)) continue;
                if (r is IPlacedNpcGetter pn)
                {
                    people.Add(Person(pn, p, d, npcs, races, classes, packs, factions, bases));
                    continue;
                }
                if (r is not IPlacedObjectGetter ob || !bases.TryGetValue(ob.Base.FormKey, out var b)) continue;
                string? dest = null;
                if (ob.TeleportDestination is { } td && refCell.TryGetValue(td.Door.FormKey, out var dc) && cells.TryGetValue(dc, out var dcell))
                    dest = dcell.Name?.String ?? dcell.EditorID ?? (cellWorld.GetValueOrDefault(dc) is { } dw ? dw.Name?.String ?? dw.EditorID : null);
                things.Add(new { key = ob.FormKey.ToString(), sig = b.sig, edid = b.edid, name = b.name, model = b.model, size = b.size * (ob.Scale ?? 1),
                    x = p.X, y = p.Y, z = p.Z, d, door = dest, locked = ob.Lock?.Level.ToString(), plugin = ob.FormKey.ModKey.FileName.String });
            }
            var surf = surfaces.Where(h => !h.Model.Contains("Effects", StringComparison.OrdinalIgnoreCase))
                .Select(h => new { kind = h.Kind, edid = h.EditorId, model = h.Model, top = h.Top }).ToList();
            Console.WriteLine("SURR " + JsonSerializer.Serialize(new
            {
                spot = s, cell = new { key = ck.ToString(), edid = cell.EditorID, name = cell.Name?.String, interior,
                    grid = cell.Grid?.Point is { } g ? new[] { g.X, g.Y } : null, location = cell.Location.FormKey.IsNull ? null : cell.Location.FormKey.ToString() },
                world = world == null ? null : new { key = world.FormKey.ToString(), edid = world.EditorID, name = world.Name?.String },
                at = new[] { at.X, at.Y, at.Z }, radius, water, land, ring, surfaces = surf, things, people, markers,
            }, o));
        }
    }

    static P3Float? Pos(IPlacedGetter r) => r switch { IPlacedObjectGetter o => o.Placement?.Position, IPlacedNpcGetter n => n.Placement?.Position, _ => null };

    static object Person(IPlacedNpcGetter pn, P3Float p, float d, Dictionary<FormKey, (INpcGetter rec, ModKey from)> npcs,
        Dictionary<FormKey, (IRaceGetter rec, ModKey from)> races, Dictionary<FormKey, (IClassGetter rec, ModKey from)> classes,
        Dictionary<FormKey, (IPackageGetter rec, ModKey from)> packs, Dictionary<FormKey, (IFactionGetter rec, ModKey from)> factions,
        Dictionary<FormKey, (string sig, string? edid, string? name, string? model, float size)> bases)
    {
        INpcGetter? b = npcs.GetValueOrDefault(pn.Base.FormKey).rec;
        // the record that supplies each part, through the template chain (a levelled list ends the chain)
        INpcGetter? Via(NpcConfiguration.TemplateFlag f)
        {
            var v = b;
            for (var i = 0; i < 8 && v != null && v.Configuration.TemplateFlags.HasFlag(f) && npcs.TryGetValue(v.Template.FormKey, out var t); i++) v = t.rec;
            return v;
        }
        var traits = Via(NpcConfiguration.TemplateFlag.Traits); var basic = Via(NpcConfiguration.TemplateFlag.BaseData);
        var ai = Via(NpcConfiguration.TemplateFlag.AIPackages); var aid = Via(NpcConfiguration.TemplateFlag.AIData);
        var fac = Via(NpcConfiguration.TemplateFlag.Factions);
        var pk = (ai?.Packages ?? []).Select(l => packs.GetValueOrDefault(l.FormKey).rec).Where(x => x != null).Select(x => new
        {
            edid = x!.EditorID, template = packs.GetValueOrDefault(x.PackageTemplate.FormKey).rec?.EditorID,
            hour = x.ScheduleHour, minutes = x.ScheduleDurationInMinutes,
            where = x.Data.Values.OfType<IPackageDataLocationGetter>().Select(l => l.Location.Target switch
            {
                ILocationTargetGetter lt => $"{lt.Link.FormKey} {bases.GetValueOrDefault(lt.Link.FormKey).edid ?? ""}".Trim(),
                ILocationFallbackGetter f => f.Type.ToString(), var t => t?.GetType().Name.Replace("BinaryOverlay", ""),
            } + $" r{l.Location.Radius}").ToList(),
        }).ToList();
        return new
        {
            key = pn.FormKey.ToString(), base_key = pn.Base.FormKey.ToString(), edid = b?.EditorID, name = basic?.Name?.String ?? b?.Name?.String,
            race = races.GetValueOrDefault((traits ?? b)?.Race.FormKey ?? FormKey.Null).rec?.EditorID,
            female = (traits ?? b)?.Configuration.Flags.HasFlag(NpcConfiguration.Flag.Female) ?? false,
            @class = classes.GetValueOrDefault((traits ?? b)?.Class.FormKey ?? FormKey.Null).rec?.EditorID,
            aggression = aid?.AIData?.Aggression.ToString(),
            factions = (fac?.Factions ?? []).Select(f => factions.GetValueOrDefault(f.Faction.FormKey).rec?.EditorID).Where(e => e != null).ToList(),
            packages = pk, x = p.X, y = p.Y, z = p.Z, d, plugin = pn.FormKey.ModKey.FileName.String,
        };
    }
}
