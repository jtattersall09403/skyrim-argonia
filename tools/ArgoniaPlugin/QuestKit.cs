using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using Noggog;

// The small kit the generic builder (QuestForm.cs) and the new game's world (Opening.cs) share:
//   story data  Rows (a table of story/data/db)
//   scripts     Script, Obj, Int, OnDeath (vanilla's defaultSetStageOnDeathRefAlias)
//   world       Placed (the load order's winning references), Snap (the nearest unused navmesh triangle), Marker, Interior;
//               Taken, the triangles snapped so far, saved and put back round a trial build
sealed class QuestKit(SkyrimMod mod, List<ISkyrimModGetter> mods, string prefix = "")
{
    public static FormKey K(string k) => FormKey.Factory(k);
    public static FormLink<ISkyrimMajorRecordGetter> L(FormKey k) => new(k);
    public static readonly FormKey XMarker = K("00003B:Skyrim.esm");

    // ---- what the load order holds, read once for every kit
    sealed class Data(List<ISkyrimModGetter> mods)
    {
        public readonly List<ISkyrimModGetter> Mods = mods;
        public readonly Dictionary<FormKey, (IPlacedGetter rec, ModKey from)> Placed = Survey.Winners<IPlacedGetter>(mods);
        // The winning navmesh of each id: the last plugin in the load order that has it (one that deleted it carries no data).
        public readonly Dictionary<FormKey, (INavigationMeshGetter rec, ModKey from)> Nav = mods.SelectMany(m => m.EnumerateMajorRecords<INavigationMeshGetter>()
            .Select(r => (r, m.ModKey))).GroupBy(e => e.r.FormKey).ToDictionary(g => g.Key, g => g.Last());
    }
    static Data? loaded;
    Data D => loaded != null && ReferenceEquals(loaded.Mods, mods) ? loaded : loaded = new Data(mods);
    public Dictionary<FormKey, (IPlacedGetter rec, ModKey from)> Placed => D.Placed;
    // The triangles every kit has taken, so no two places stand on one triangle.
    static readonly HashSet<(FormKey, int)> used = [];
    /// The triangles taken so far, to put back after a trial build (Taken(saved)).
    public static HashSet<(FormKey, int)> Taken() => [.. used];
    public static void Taken(HashSet<(FormKey, int)> saved) { used.Clear(); used.UnionWith(saved); }

    // ---- story data (story/data/db, the one source)
    static readonly string Db = Path.Combine("story", "data", "db");
    public static IEnumerable<JsonElement> Rows(string table) =>
        File.ReadLines(Path.Combine(Db, table + ".jsonl")).Where(l => l.Trim().Length > 0).Select(l => JsonDocument.Parse(l).RootElement);

    // ---- scripts
    public static ScriptEntry Script(string name, params ScriptProperty[] ps) { var e = new ScriptEntry { Name = name }; e.Properties.AddRange(ps); return e; }
    public static ScriptObjectProperty Obj(string n, FormKey k) => new() { Name = n, Object = L(k) };
    public static ScriptIntProperty Int(string n, int v) => new() { Name = n, Data = v };
    public static ScriptEntry OnDeath(Quest q, int prereq, int set) =>
        Script("defaultSetStageOnDeathRefAlias", Obj("myQST", q.FormKey), Int("preReqStage", prereq), Int("StageToSet", set));

    // ---- the world
    /// The nearest unused triangle centre of a navmesh to a spot, nearest in three dimensions (a deck above a deck keeps to
    /// the named level), over the last copy of the navmesh that carries data; no two places in the plugin take one triangle.
    public P3Float Snap(FormKey mesh, float x, float y, float z)
    {
        var (rec, from) = D.Nav.TryGetValue(mesh, out var w) ? w : throw new InvalidOperationException($"navmesh {mesh} is in no plugin of the load order");
        var d = rec.Data ?? throw new InvalidOperationException($"navmesh {mesh}: the winner, {from.FileName}, carries no data (deleted)");
        var v = d.Vertices;
        var best = Enumerable.Range(0, d.Triangles.Count).Where(i => !used.Contains((mesh, i))).Select(i =>
        {
            var t = d.Triangles[i].Vertices; var a = v[t.X]; var b = v[t.Y]; var c = v[t.Z];
            return (i, p: new P3Float((a.X + b.X + c.X) / 3, (a.Y + b.Y + c.Y) / 3, (a.Z + b.Z + c.Z) / 3));
        }).MinBy(e => (e.p.X - x) * (e.p.X - x) + (e.p.Y - y) * (e.p.Y - y) + 16 * (e.p.Z - z) * (e.p.Z - z));
        used.Add((mesh, best.i));
        return new P3Float(MathF.Round(best.p.X), MathF.Round(best.p.Y), MathF.Round(best.p.Z));
    }
    /// A persistent marker (the vanilla X marker) of ours at a spot.
    public PlacedObject Marker(string id, P3Float p) => new(mod.GetNextFormKey(), SkyrimRelease.SkyrimSE)
        { EditorID = prefix + id, Base = new FormLinkNullable<IPlaceableObjectGetter>(XMarker), MajorRecordFlagsRaw = 0x400, Placement = new Placement { Position = p } };
    /// Our override of an interior cell's record, merged with one already in the mod.
    public Cell Interior(FormKey cellKey) => Overrides.Interior(mod, mods, cellKey);
}
