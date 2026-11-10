using System.Text.RegularExpressions;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;

// questcheck <Argonia.esp> <papyrus dir> <plugins in load order...>: one read-back over every quest of ours (ARG_*, bar
// ARG_BlockTest* and ARG_Opening) in the built plugin, asking not "is it what the builder meant" but "can it happen".
// The loader builds a plain model (quests, stages, objectives, aliases, packages, zones, refs, navmeshes, INFOs and the
// Papyrus SOURCE of every script: papyrus/*.psc and papyrus/generated/*.psc, since the .pex are compiled elsewhere);
// each rule is one pure function over that model, unit-tested on hand-made models by `questcheck --selftest`.
//   route    a package's walker reaches its destination over one navmesh walk (never a deleted mesh, never off mesh)
//   start    a travel package gated on stage S is not started while its walker is out of the player's reach
//   shape    every alias package is a Package with a template link, never a PackageTemplate
//   stages   every stage has a reachable setter, objectives and targets, and a way out
//   endings  RunOnce, Stop(), every zone disabled
//   zones    no two zones overlap when one sets the other's prerequisite
//   people   no two enabled people of one name stand in reach of each other during a simulated run
//   offers   a topic gated on a stage has an upper bound below the first ending
//   doors    a key-locked door of ours is opened or its key given on every ending
// Prints one `FAIL <quest> <rule>: <what>` line per fault and a summary; exit 1 on any failure.
sealed record Spot(string Cell, bool Interior, string World, float X, float Y, float Z)
{
    public string CellId => Interior ? Cell : $"E:{World}:{(int)Math.Floor(X / 4096)}:{(int)Math.Floor(Y / 4096)}";
    public float Dist(Spot o) => MathF.Sqrt((X - o.X) * (X - o.X) + (Y - o.Y) * (Y - o.Y));
    public bool Near(Spot o, float r) => Interior || o.Interior ? Cell == o.Cell : World == o.World && Dist(o) <= r;
}
enum Op { Eq, Ne, Lt, Le, Gt, Ge }
sealed record Cond(string Quest, Op Op, float V);
sealed class St { public int Index; public bool HasText, Ending, StartUp; }
sealed class Ob { public int Index, Targets; }
sealed class AS { public string Name = ""; public Dictionary<string, int> Ints = new(StringComparer.OrdinalIgnoreCase); public Dictionary<string, string> Objs = new(StringComparer.OrdinalIgnoreCase); }
sealed class Al { public int Id; public string Name = ""; public bool Essential; public string? Forced; public List<string> Packs = []; public List<AS> Scripts = []; }
sealed class Pr { public string Obj = ""; public int Alias = -1; public string[]? Arr; }
sealed class Info { public string Topic = ""; public bool Hello; public List<Cond> Conds = []; public string? Frag; public string FragFn = "Fragment_0"; public List<string> Bases = []; public List<string> Refs = []; public bool Clock; }
sealed class Q
{
    public string Key = "", Edid = ""; public bool Check, RunOnce, StartGame; public string? Script;
    public List<St> Stages = []; public List<Ob> Objs = []; public List<Al> Aliases = []; public List<Info> Infos = [];
    public Dictionary<string, Pr> Props = new(StringComparer.OrdinalIgnoreCase); public Dictionary<int, (string script, string fn)> Frags = [];
    public St? Stage(int i) => Stages.FirstOrDefault(s => s.Index == i);
    public int? FirstEnding => Stages.Where(s => s.Ending).Select(s => (int?)s.Index).Min();
}
sealed class R
{
    public string Key = "", Edid = ""; public Spot Spot = new("", false, "", 0, 0, 0); public bool Npc, Ours, InMod, Disabled, Opp, Essential, Locked, Unique;
    public string Base = "", Name = "", Parent = "", Tele = "", LockKey = "";
}
sealed class Trig { public R Ref = new(); public string Quest = ""; public int Prereq = -1, Stage; public bool Zone; public float Hx, Hy, Hz; }
sealed class Pk
{
    public string Key = "", Edid = ""; public bool IsPackage = true, HasTemplate = true, Clock; public int Hour = -1;
    public List<Cond> Stages = []; public string? Location, Follow;
}
sealed class Fn { public string Name = ""; public List<string> Params = []; public List<Stmt> Body = []; }
sealed record Stmt(string Kind, string Target, string[] Args);
sealed class Script { public string Name = ""; public Dictionary<string, Fn> Fns = new(StringComparer.OrdinalIgnoreCase); }
sealed record Eff(string Kind, string Target, int? N, bool G3, string Via);
sealed class Mesh
{
    public string Id = "", Region = "", Plugin = ""; public bool Deleted; public string DeletedBy = "";
    public float[][] V = []; public int[][] T = []; public (string mesh, int tri)?[][] Nb = [];
}
sealed class Nav
{
    public Dictionary<string, List<Mesh>> ByRegion = []; public Dictionary<string, Mesh> ById = [];
    public void Add(Mesh m) { ById[m.Id] = m; if (!ByRegion.TryGetValue(m.Region, out var l)) ByRegion[m.Region] = l = []; l.Add(m); }
    static string Reg(Spot s, int dx, int dy) => s.Interior ? "I:" + s.Cell : $"W:{s.World}:{(int)Math.Floor(s.X / 4096) + dx}:{(int)Math.Floor(s.Y / 4096) + dy}";
    IEnumerable<Mesh> Around(Spot s) => (s.Interior ? new[] { (0, 0) } : [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)])
        .SelectMany(d => ByRegion.GetValueOrDefault(Reg(s, d.Item1, d.Item2)) ?? []);
    public IEnumerable<Mesh> DeletedNear(Spot s) => Around(s).Where(m => m.Deleted && Dist(m, s, out _) <= 150);
    // The nearest triangle of a live (winning, undeleted) mesh within 150 in x,y and 200 in z of the spot.
    public (Mesh m, int tri)? Snap(Spot s)
    {
        (Mesh, int)? best = null; var bd = float.MaxValue;
        foreach (var m in Around(s).Where(m => !m.Deleted))
        {
            var d = Dist(m, s, out var tri);
            if (d <= 150 && d < bd) { bd = d; best = (m, tri); }
        }
        return best;
    }
    // Distance in x,y from the spot to the nearest triangle of m that is within 200 in z; the triangle index.
    static float Dist(Mesh m, Spot s, out int tri)
    {
        var best = float.MaxValue; tri = -1;
        for (var i = 0; i < m.T.Length; i++)
        {
            var a = m.V[m.T[i][0]]; var b = m.V[m.T[i][1]]; var c = m.V[m.T[i][2]];
            if (s.Z < Math.Min(a[2], Math.Min(b[2], c[2])) - 200 || s.Z > Math.Max(a[2], Math.Max(b[2], c[2])) + 200) continue;
            var d = TriDist(s.X, s.Y, a, b, c);
            if (d < best) { best = d; tri = i; }
        }
        return best;
    }
    static float TriDist(float x, float y, float[] a, float[] b, float[] c)
    {
        float Cr(float[] p, float[] q) => (q[0] - p[0]) * (y - p[1]) - (q[1] - p[1]) * (x - p[0]);
        float d1 = Cr(a, b), d2 = Cr(b, c), d3 = Cr(c, a);
        if ((d1 >= 0 && d2 >= 0 && d3 >= 0) || (d1 <= 0 && d2 <= 0 && d3 <= 0)) return 0;
        return Math.Min(Seg(x, y, a, b), Math.Min(Seg(x, y, b, c), Seg(x, y, c, a)));
    }
    static float Seg(float x, float y, float[] p, float[] q)
    {
        float dx = q[0] - p[0], dy = q[1] - p[1], l = dx * dx + dy * dy;
        var t = l == 0 ? 0 : Math.Clamp(((x - p[0]) * dx + (y - p[1]) * dy) / l, 0, 1);
        float ex = p[0] + t * dx - x, ey = p[1] + t * dy - y; return MathF.Sqrt(ex * ex + ey * ey);
    }
    // Breadth-first over triangle adjacency and edge links (Inspect's navpath walk).
    public bool Connected((Mesh m, int tri) a, (Mesh m, int tri) b)
    {
        var from = (a.m.Id, a.tri); var to = (b.m.Id, b.tri);
        var seen = new HashSet<(string, int)> { from }; var queue = new Queue<(string, int)>([from]);
        while (queue.Count > 0)
        {
            var (m, i) = queue.Dequeue();
            if ((m, i) == to) return true;
            if (!ById.TryGetValue(m, out var mesh) || i >= mesh.Nb.Length) continue;
            foreach (var n in mesh.Nb[i]) if (n is { } nn && seen.Add(nn)) queue.Enqueue(nn);
        }
        return seen.Contains(to);
    }
}
sealed class QModel
{
    public List<Q> Quests = []; public Dictionary<string, R> Refs = []; public List<Trig> Trigs = []; public Dictionary<string, Pk> Packs = [];
    public Dictionary<string, Script> Scripts = new(StringComparer.OrdinalIgnoreCase); public Nav Nav = new();
    public HashSet<string> DoorPairs = []; // "cellA|cellB" both ways
    public Q? Quest(string key) => Quests.FirstOrDefault(q => q.Key == key);
    public IEnumerable<Q> Checked => Quests.Where(q => q.Check);
    public Dictionary<string, List<Spot>> DoorSpots = []; // cell id -> where the doors of that cell come out
    public bool Joined(Spot a, Spot b) =>
        (a.CellId != b.CellId && DoorPairs.Contains(a.CellId + "|" + b.CellId)) || (DoorSpots.GetValueOrDefault(a.CellId)?.Any(s => s.Near(b, 8192)) ?? false) || (DoorSpots.GetValueOrDefault(b.CellId)?.Any(s => s.Near(a, 8192)) ?? false);
    public IEnumerable<Trig> ZonesOf(Q q) => Trigs.Where(t => t.Zone && t.Quest == q.Key);
    public R? AliasRef(Q q, int id) => q.Aliases.FirstOrDefault(a => a.Id == id)?.Forced is { } f && Refs.TryGetValue(f, out var r) ? r : null;
}

static partial class QuestCheck
{
    static string Fail(Q q, string rule, string what) => $"FAIL {q.Edid} {rule}: {what}";
    static string Nm(QModel m, string key) => m.Refs.TryGetValue(key, out var r) && r.Edid != "" ? $"{r.Edid} ({key})" : key;

    // ---- Papyrus: enough to see what a function does, not a compiler.
    static readonly Regex RFn = new(@"^\s*(?:\w+(?:\[\])?\s+)?(Function|Event)\s+(\w+)\s*\((.*?)\)", RegexOptions.IgnoreCase);
    static readonly Regex RCast = new(@"\(\s*(?:\w+(?:\(\))?)\s+as\s+(\w+)\s*\)\s*\.\s*(\w+)\s*\(([^)]*)\)", RegexOptions.IgnoreCase);
    static readonly Regex ROwn = new(@"GetOwningQuest\(\)\s*\.\s*(\w+)\s*\(([^)]*)\)", RegexOptions.IgnoreCase);
    static readonly Regex RDot = new(@"(?<![\w)\.])(\w+)(?:\[[^\]]*\])?(?:\s*\.\s*(?:GetRef|GetActorRef)\(\))?\s*\.\s*(\w+)\s*\(([^)]*)\)", RegexOptions.IgnoreCase);
    static readonly Regex RBare = new(@"(?<![\w.])(\w+)\s*\(([^)]*)\)");
    static readonly Regex RAdd = new(@"\.\s*AddItem\(\s*(\w+)", RegexOptions.IgnoreCase);
    static readonly HashSet<string> Words = new(StringComparer.OrdinalIgnoreCase) { "function", "event", "if", "elseif", "while", "return", "endif", "endwhile", "int", "float", "bool", "string" };
    static string[] Args(string s) => s.Split(',', StringSplitOptions.TrimEntries | StringSplitOptions.RemoveEmptyEntries);

    public static Script Parse(string name, string src)
    {
        var sc = new Script { Name = name }; Fn? cur = null;
        foreach (var raw in src.Split('\n'))
        {
            var line = raw.Split(';')[0].TrimEnd('\r');
            var h = RFn.Match(line);
            if (h.Success && cur == null && !line.TrimStart().StartsWith("End", StringComparison.OrdinalIgnoreCase))
            {
                cur = new Fn { Name = h.Groups[2].Value, Params = Args(h.Groups[3].Value).Select(p => p.Split(' ', StringSplitOptions.RemoveEmptyEntries).Last()).ToList() };
                sc.Fns[cur.Name] = cur; continue;
            }
            if (cur == null) continue;
            if (Regex.IsMatch(line, @"^\s*End(Function|Event)\b", RegexOptions.IgnoreCase)) { cur = null; continue; }
            Statements(line, cur.Body);
        }
        return sc;
    }
    static void Statements(string line, List<Stmt> body)
    {
        var hits = new List<(int at, Stmt s)>();
        foreach (Match c in RCast.Matches(line)) hits.Add((c.Index, new Stmt("call", c.Groups[2].Value, [c.Groups[1].Value, .. Args(c.Groups[3].Value)])));
        foreach (Match c in ROwn.Matches(line))
            if (c.Groups[1].Value.Equals("SetStage", StringComparison.OrdinalIgnoreCase)) hits.Add((c.Index, new Stmt("set", "(owner)", Args(c.Groups[2].Value))));
        foreach (Match c in RDot.Matches(line))
        {
            string t = c.Groups[1].Value, meth = c.Groups[2].Value.ToLowerInvariant(); var a = Args(c.Groups[3].Value);
            switch (meth)
            {
                case "setstage": hits.Add((c.Index, new Stmt("set", t, a))); break;
                case "enable": hits.Add((c.Index, new Stmt("enable", t, a))); break;
                case "disable": hits.Add((c.Index, new Stmt("disable", t, a))); break;
                case "lock": if (a.Length > 0 && a[0].Equals("False", StringComparison.OrdinalIgnoreCase)) hits.Add((c.Index, new Stmt("unlock", t, a))); break;
                case "start": hits.Add((c.Index, new Stmt("start", t, a))); break;
                case "stop": hits.Add((c.Index, new Stmt("stop", t, a))); break;
                case "is3dloaded": hits.Add((c.Index, new Stmt("is3d", t, a))); break;
            }
        }
        foreach (Match c in RAdd.Matches(line)) hits.Add((c.Index, new Stmt("give", c.Groups[1].Value, [])));
        foreach (Match c in RBare.Matches(line))
        {
            var n = c.Groups[1].Value; var a = Args(c.Groups[2].Value);
            if (Words.Contains(n)) continue;
            if (n.Equals("SetStage", StringComparison.OrdinalIgnoreCase)) hits.Add((c.Index, new Stmt("set", "", a)));
            else if (n.Equals("Stop", StringComparison.OrdinalIgnoreCase)) hits.Add((c.Index, new Stmt("stop", "", a)));
            else if (n.Equals("SetObjectiveDisplayed", StringComparison.OrdinalIgnoreCase)) hits.Add((c.Index, new Stmt("obj", "", a)));
            else hits.Add((c.Index, new Stmt("call", n, ["", .. a])));
        }
        foreach (var (_, s) in hits.OrderBy(h => h.at)) body.Add(s);
    }

    // What a function does, calls followed: own functions and `(GetOwningQuest() as Script).Fn()`, int and name arguments bound.
    public static List<Eff> Effects(QModel m, Script? sc, string fn, Dictionary<string, string>? bind = null, int depth = 0, bool g3 = false, string via = "")
    {
        var res = new List<Eff>();
        if (sc == null || depth > 6 || !sc.Fns.TryGetValue(fn, out var f)) return res;
        bind ??= [];
        string B(string s) => bind.TryGetValue(s, out var v) ? v : s;
        int? N(string[] a, int i) => a.Length > i && int.TryParse(B(a[i]), out var n) ? n : null;
        var seen3 = g3; via = via == "" ? sc.Name + "." + fn : via;
        foreach (var s in f.Body)
        {
            switch (s.Kind)
            {
                case "is3d": seen3 = true; break;
                case "set": res.Add(new Eff("set", B(s.Target), N(s.Args, 0), seen3, via)); break;
                case "obj": res.Add(new Eff("obj", "", N(s.Args, 0), seen3, via)); break;
                case "enable": case "disable": case "unlock": case "start": case "stop": res.Add(new Eff(s.Kind, B(s.Target), null, seen3, via)); break;
                case "give": res.Add(new Eff("give", B(s.Target), null, seen3, via)); break;
                case "call":
                    var target = s.Args.Length > 0 && s.Args[0] != "" ? m.Scripts.GetValueOrDefault(s.Args[0]) : sc;
                    if (target == null || !target.Fns.TryGetValue(s.Target, out var callee) || (target == sc && s.Target.Equals(fn, StringComparison.OrdinalIgnoreCase))) break;
                    var nb = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
                    for (var i = 0; i < callee.Params.Count && i + 1 < s.Args.Length; i++) nb[callee.Params[i]] = B(s.Args[i + 1]);
                    res.AddRange(Effects(m, target, s.Target, nb, depth + 1, seen3, via));
                    if (res.Any(e => e.Kind == "is3d")) seen3 = true;
                    break;
            }
        }
        return res;
    }

    // ---- model helpers shared by the rules
    public static List<Eff> FragEffects(QModel m, Q q, int stage) =>
        q.Frags.TryGetValue(stage, out var f) ? Effects(m, m.Scripts.GetValueOrDefault(f.script), f.fn) : [];
    public static List<Eff> EventEffects(QModel m, Q q) =>
        q.Script == null || !m.Scripts.TryGetValue(q.Script, out var sc) ? [] : sc.Fns.Keys.Where(k => k.StartsWith("On", StringComparison.OrdinalIgnoreCase)).SelectMany(k => Effects(m, sc, k)).ToList();
    // The quest a `SetStage` effect addresses.
    static Q? SetQuest(QModel m, Q ctx, string target) =>
        target is "" or "(owner)" ? ctx : ctx.Props.TryGetValue(target, out var p) ? m.Quest(p.Obj) : null;
    // The refs a property or alias name stands for in a quest's script.
    public static List<string> RefsOf(QModel m, Q ctx, string name)
    {
        if (!ctx.Props.TryGetValue(name, out var p)) return [];
        if (p.Arr != null) return [.. p.Arr];
        if (p.Alias >= 0) { var q = m.Quest(p.Obj) ?? ctx; var al = q.Aliases.FirstOrDefault(a => a.Id == p.Alias); return al?.Forced != null ? [al.Forced] : []; }
        return [p.Obj];
    }
    static Cond? StageCond(Pk p) => p.Stages.FirstOrDefault(c => c.Op is Op.Ge or Op.Eq or Op.Gt);

    // ---- setters: who can set a stage, with where they stand (for rules 2 and 4).
    sealed record Setter(string Kind, string Desc, Spot? Spot, bool G3, string SrcQuest, int[] Prereq, bool GePrereq, bool Death = false, bool OnEssential = false, string? FromQuest = null, int FromStage = -1);
    static List<Setter> SettersOf(QModel m, Q q, int stage)
    {
        var res = new List<Setter>();
        foreach (var t in m.Trigs.Where(t => t.Quest == q.Key && t.Stage == stage))
            res.Add(new Setter(t.Zone ? "zone" : "trigger", $"{(t.Zone ? "zone" : "trigger")} {t.Ref.Edid}", t.Ref.Spot, false, q.Key, t.Prereq > 0 ? [t.Prereq] : [], true));
        foreach (var oq in m.Quests)
            foreach (var a in oq.Aliases)
                foreach (var s in a.Scripts)
                {
                    var st = AliasStage(s); if (st != stage) continue;
                    var target = s.Objs.Values.FirstOrDefault() is { } ok && m.Quest(ok) != null ? ok : oq.Key; if (target != q.Key) continue;
                    var pre = s.Ints.Where(kv => kv.Key.Contains("prereq", StringComparison.OrdinalIgnoreCase)).Select(kv => kv.Value).Where(v => v > 0).ToArray();
                    var death = s.Name.Contains("death", StringComparison.OrdinalIgnoreCase);
                    var fr = a.Forced != null && m.Refs.TryGetValue(a.Forced, out var rr) ? rr : null;
                    var acquire = s.Name.Contains("acquire", StringComparison.OrdinalIgnoreCase);
                    res.Add(new Setter("alias", $"alias {oq.Edid}.{a.Name} ({s.Name})", acquire ? null : fr?.Spot, false, q.Key, pre, true, death, death && (a.Essential || fr?.Essential == true)));
                }
        foreach (var oq in m.Quests)
            foreach (var i in oq.Infos)
            {
                if (i.Frag == null || !m.Scripts.TryGetValue(i.Frag, out var sc)) continue;
                foreach (var e in Effects(m, sc, i.FragFn).Where(e => e.Kind == "set" && e.N == stage && SetQuest(m, oq, e.Target) == q))
                {
                    var lo = i.Conds.Where(c => c.Quest == oq.Key && c.Op is Op.Ge or Op.Eq).Select(c => (int)c.V).ToArray();
                    var spots = i.Bases.SelectMany(b => m.Refs.Values.Where(r => r.Npc && r.Base == b)).Concat(i.Refs.Where(k => m.Refs.ContainsKey(k)).Select(k => m.Refs[k])).Select(r => r.Spot).ToList();
                    res.Add(new Setter("info", $"line {i.Topic}", spots.FirstOrDefault(), e.G3, oq.Key, lo, lo.Length == 0 ? true : i.Conds.Any(c => c.Op == Op.Ge)));
                }
            }
        foreach (var oq in m.Quests)
        {
            foreach (var (fs, _) in oq.Frags)
                foreach (var e in FragEffects(m, oq, fs).Where(e => e.Kind == "set" && e.N == stage && SetQuest(m, oq, e.Target) == q))
                    res.Add(new Setter("fragment", $"{oq.Edid} stage {fs} ({e.Via})", null, e.G3, q.Key, [fs], false, FromQuest: oq.Key, FromStage: fs));
            foreach (var e in EventEffects(m, oq).Where(e => e.Kind == "set" && e.N == stage && SetQuest(m, oq, e.Target) == q))
                res.Add(new Setter("event", $"{oq.Edid} {e.Via}", null, e.G3, q.Key, [], true, FromQuest: oq.Key, FromStage: -2));
        }
        return res;
    }
    static int AliasStage(AS s)
    {
        foreach (var k in new[] { "StageToSet", "stage" }) if (s.Ints.TryGetValue(k, out var v) && s.Name.StartsWith("defaultSetStage", StringComparison.OrdinalIgnoreCase)) return v;
        return -1;
    }
}

// ---- the rules: one pure function each over the model.
static partial class QuestCheck
{
    // 1. route: a walk over one navmesh from the walker's start to the destination.
    public static IEnumerable<string> Route(QModel m)
    {
        foreach (var q in m.Checked)
            foreach (var a in q.Aliases.Where(a => a.Forced != null && m.Refs.ContainsKey(a.Forced)))
            {
                var start = m.Refs[a.Forced!];
                foreach (var pk in a.Packs.Select(k => m.Packs.GetValueOrDefault(k)).Where(p => p != null).Select(p => p!))
                {
                    var dests = new List<(string what, Spot spot)>();
                    if (pk.Location != null && m.Refs.TryGetValue(pk.Location, out var lr)) dests.Add((Nm(m, pk.Location), lr.Spot));
                    else if (pk.Follow != null)
                    {
                        var gate = StageCond(pk)?.V ?? 0; var upper = pk.Stages.Where(c => c.Op is Op.Lt or Op.Le or Op.Eq).Select(c => c.Op == Op.Lt ? c.V - 1 : c.V).DefaultIfEmpty(float.MaxValue).Min();
                        foreach (var z in m.ZonesOf(q).Where(z => z.Prereq >= gate && z.Prereq <= upper)) dests.Add(($"zone {z.Ref.Edid} (stage {z.Prereq})", z.Ref.Spot));
                    }
                    foreach (var (what, spot) in dests)
                    {
                        var why = Walk(m, start.Spot, spot, $"{a.Name} start {Nm(m, start.Key)}", what);
                        if (why != null) yield return Fail(q, "route", $"package {pk.Edid} ({pk.Key}) of alias {a.Name}: {why}");
                    }
                }
            }
    }
    static string? Walk(QModel m, Spot from, Spot to, string fromName, string toName)
    {
        string? Off(Spot s, string name)
        {
            if (m.Nav.Snap(s) != null) return null;
            var del = m.Nav.DeletedNear(s).Select(d => $"{d.Id} ({d.Plugin}) is DELETED by {d.DeletedBy}").FirstOrDefault();
            return $"{name} at {s.X:F0},{s.Y:F0},{s.Z:F0} ({s.CellId}) {(s.Interior ? "is in an interior " + s.Cell + " with no navmesh under it" : "is more than 150 off any navmesh")}{(del != null ? "; navmesh " + del : "")}";
        }
        var why = Off(from, fromName) ?? Off(to, toName);
        if (why != null) return why;
        var a = m.Nav.Snap(from)!.Value; var b = m.Nav.Snap(to)!.Value;
        return m.Nav.Connected(a, b) ? null : $"no walk from {fromName} (navmesh {a.m.Id}) to {toName} (navmesh {b.m.Id}): not connected";
    }

    // 2. start: a travel package gated on stage S must not turn eligible while its walker is out of the player's reach.
    public static IEnumerable<string> Start(QModel m)
    {
        foreach (var q in m.Checked)
            foreach (var a in q.Aliases.Where(a => a.Forced != null && m.Refs.ContainsKey(a.Forced)))
            {
                var walker = m.Refs[a.Forced!];
                foreach (var pk in a.Packs.Select(k => m.Packs.GetValueOrDefault(k)).Where(p => p is { Location: not null, Hour: < 0, Clock: false }).Select(p => p!))
                {
                    var gate = StageCond(pk); if (gate == null) continue;
                    var s = (int)gate.V + (gate.Op == Op.Gt ? 1 : 0);
                    var bad = new List<string>();
                    foreach (var st in SettersOf(m, q, s)) Unseen(m, st, walker.Spot, bad, 0);
                    if (bad.Count > 0)
                        yield return Fail(q, "start", $"package {pk.Edid} ({pk.Key}) of alias {a.Name} starts at stage {s}, but {Nm(m, walker.Key)} (at {walker.Spot.X:F0},{walker.Spot.Y:F0} in {walker.Spot.CellId}) is out of reach when it is set by {string.Join("; ", bad)} (no Is3DLoaded test)");
                }
            }
    }
    static void Unseen(QModel m, Setter st, Spot walker, List<string> bad, int depth)
    {
        if (st.G3 || depth > 4) return;
        if (st.Kind == "fragment")
        {
            var from = m.Quest(st.FromQuest!); if (from == null) return;
            foreach (var up in SettersOf(m, from, st.FromStage)) Unseen(m, up, walker, bad, depth + 1);
            return;
        }
        if (st.Spot == null) return;
        if (!st.Spot.Near(walker, 4096)) bad.Add($"{st.Desc} at {st.Spot.X:F0},{st.Spot.Y:F0} in {st.Spot.CellId}");
    }

    // 3. shape: an alias package is a Package with a template link.
    public static IEnumerable<string> Shape(QModel m)
    {
        foreach (var q in m.Checked)
            foreach (var a in q.Aliases)
                foreach (var k in a.Packs)
                    if (m.Packs.GetValueOrDefault(k) is { } p && (!p.IsPackage || !p.HasTemplate))
                        yield return Fail(q, "shape", $"package {p.Edid} ({p.Key}) of alias {a.Name} is {(p.IsPackage ? "a Package without a template link" : "a PackageTemplate")}");
    }

    // 4. stages (and 10, objectives): reachable setters, objective display and targets, a way out.
    sealed record Reached(HashSet<(string, int)> Set, Dictionary<(string, int), List<Setter>> Setters);
    static Reached Reach(QModel m)
    {
        var set = new HashSet<(string, int)>(); var setters = new Dictionary<(string, int), List<Setter>>();
        foreach (var q in m.Quests) foreach (var s in q.Stages) setters[(q.Key, s.Index)] = SettersOf(m, q, s.Index);
        foreach (var q in m.Quests.Where(q => !q.Check)) foreach (var s in q.Stages) set.Add((q.Key, s.Index));
        foreach (var q in m.Quests.Where(q => !q.Check)) foreach (var f in q.Frags.Keys) set.Add((q.Key, f));
        var started = new HashSet<string>();
        bool Running(string k) => m.Quest(k) is { } q && (q.StartGame || started.Contains(k) || set.Any(x => x.Item1 == k));
        for (var changed = true; changed;)
        {
            changed = false;
            // a quest another reachable fragment starts is running (MQ101's stage 0 starts ARG_MQ01)
            foreach (var (oq, s) in set.ToList())
                if (m.Quest(oq) is { } fq)
                    foreach (var e in FragEffects(m, fq, s).Where(e => e.Kind == "start"))
                        if (SetQuest(m, fq, e.Target) is { } sq && started.Add(sq.Key)) changed = true;
            foreach (var ((qk, s), list) in setters)
            {
                if (set.Contains((qk, s))) continue;
                foreach (var st in list)
                {
                    if (st.Death && st.OnEssential) continue;
                    var ok = st.FromStage == -2 ? Running(st.FromQuest!) : st.Kind == "fragment" ? set.Contains((st.FromQuest!, st.FromStage)) : st.Prereq.All(p => p <= 0 || set.Contains((st.SrcQuest, p)));
                    if (ok) { set.Add((qk, s)); changed = true; break; }
                }
            }
        }
        return new Reached(set, setters);
    }
    public static IEnumerable<string> Stages(QModel m)
    {
        var rc = Reach(m);
        foreach (var q in m.Checked)
        {
            foreach (var st in q.Stages.OrderBy(s => s.Index))
            {
                var setters = rc.Setters[(q.Key, st.Index)];
                if (!st.StartUp && !rc.Set.Contains((q.Key, st.Index)))
                    yield return Fail(q, "stages", $"stage {st.Index} has no reachable setter ({(setters.Count == 0 ? "nothing sets it" : string.Join("; ", setters.Select(s => s.Desc + (s.Death && s.OnEssential ? " [Essential]" : "")).Distinct()))})");
                if (st.HasText && !st.Ending && !FragEffects(m, q, st.Index).Any(e => e.Kind == "obj"))
                    yield return Fail(q, "stages", $"stage {st.Index} has journal text but its fragment displays no objective");
                if (!st.Ending && !st.StartUp && !q.Stages.Where(t => t.Index > st.Index).Any(t => rc.Setters[(q.Key, t.Index)].Any(x => From(x, q, st.Index))))
                    yield return Fail(q, "stages", $"stage {st.Index} is not an ending and nothing sets a stage above it from there (no way out)");
            }
            foreach (var o in q.Objs.Where(o => o.Targets == 0))
                yield return Fail(q, "objectives", $"objective {o.Index} has no target");
            foreach (var (st, desc) in rc.Setters.Where(kv => kv.Key.Item1 == q.Key).SelectMany(kv => kv.Value.Where(s => s.Death && s.OnEssential).Select(s => (kv.Key.Item2, s.Desc))))
                yield return Fail(q, "stages", $"stage {st} is set by a death on an Essential person ({desc}): it can never be reached");
        }
    }
    // Can setter x of a stage fire while the quest stands at stage s?
    static bool From(Setter x, Q q, int s)
    {
        if (x.Death && x.OnEssential) return false;
        if (x.Kind == "fragment") return x.FromQuest == q.Key && x.FromStage == s;
        if (x.Prereq.Length == 0) return true;
        return x.GePrereq ? s >= x.Prereq.Max() : x.Prereq.Contains(s);
    }

    // 5. endings: RunOnce, Stop(), every zone disabled.
    public static IEnumerable<string> Endings(QModel m)
    {
        foreach (var q in m.Checked)
        {
            if (!q.RunOnce) yield return Fail(q, "endings", "the quest does not have the RunOnce flag");
            var zones = m.ZonesOf(q).ToList();
            foreach (var e in q.Stages.Where(s => s.Ending))
            {
                if (!q.Frags.ContainsKey(e.Index)) { yield return Fail(q, "endings", $"ending {e.Index} has no fragment: nothing calls Stop() or disables the zones"); continue; }
                var eff = FragEffects(m, q, e.Index);
                if (!eff.Any(x => x.Kind == "stop" && x.Target == "")) yield return Fail(q, "endings", $"ending {e.Index} never calls Stop()");
                var off = new HashSet<string>();
                foreach (var d in eff.Where(x => x.Kind == "disable"))
                {
                    foreach (var r in RefsOf(m, q, d.Target)) off.Add(r);
                    if (d.Target.Equals("Zones", StringComparison.OrdinalIgnoreCase) && q.Props.TryGetValue("Zones", out var zp) && zp.Arr != null && !zp.Arr.OrderBy(x => x).SequenceEqual(zones.Select(z => z.Ref.Key).OrderBy(x => x)))
                        yield return Fail(q, "endings", $"the Zones property holds {string.Join(",", zp.Arr)} but the quest's zones are {string.Join(",", zones.Select(z => z.Ref.Key))}");
                }
                var left = zones.Where(z => !off.Contains(z.Ref.Key)).ToList();
                if (left.Count > 0) yield return Fail(q, "endings", $"ending {e.Index} leaves zone(s) enabled: {string.Join(", ", left.Select(z => $"{z.Ref.Edid} ({z.Ref.Key}, prereq {z.Prereq} -> {z.Stage})"))}");
            }
        }
    }

    // 6. zones: no two overlap when one sets the other's prerequisite.
    public static IEnumerable<string> Zones(QModel m)
    {
        foreach (var q in m.Checked)
        {
            var zs = m.ZonesOf(q).ToList();
            for (var i = 0; i < zs.Count; i++)
                for (var j = i + 1; j < zs.Count; j++)
                {
                    var a = zs[i]; var b = zs[j];
                    if (a.Stage != b.Prereq && b.Stage != a.Prereq) continue;
                    if (a.Ref.Spot.CellId != b.Ref.Spot.CellId && a.Ref.Spot.World != b.Ref.Spot.World) continue;
                    if (MathF.Abs(a.Ref.Spot.X - b.Ref.Spot.X) < a.Hx + b.Hx && MathF.Abs(a.Ref.Spot.Y - b.Ref.Spot.Y) < a.Hy + b.Hy && MathF.Abs(a.Ref.Spot.Z - b.Ref.Spot.Z) < a.Hz + b.Hz)
                        yield return Fail(q, "zones", $"zone {a.Ref.Edid} (prereq {a.Prereq} -> {a.Stage}) overlaps {b.Ref.Edid} (prereq {b.Prereq} -> {b.Stage}), and one sets the other's prerequisite");
                }
        }
    }

    // 7. people: two enabled people of one name within reach of each other in a simulated run.
    public static IEnumerable<string> People(QModel m)
    {
        foreach (var q in m.Checked)
        {
            var state = m.Refs.Values.ToDictionary(r => r.Key, r => !r.Disabled);
            var owned = new HashSet<string>(q.Aliases.Where(a => a.Forced != null).Select(a => a.Forced!));
            var steps = new List<(string label, List<Eff> eff)> { ("the start", []) };
            foreach (var s in q.Frags.Keys.OrderBy(k => k)) steps.Add(($"stage {s}", FragEffects(m, q, s)));
            var seen = new HashSet<string>();
            foreach (var (label, eff) in steps)
            {
                foreach (var e in eff.Where(e => e.Kind is "enable" or "disable"))
                    foreach (var k in RefsOf(m, q, e.Target)) { if (state.ContainsKey(k)) state[k] = e.Kind == "enable"; owned.Add(k); }
                var on = m.Refs.Values.Where(r => r.Npc && r.Ours && r.Name != "" && Enabled(m, state, r.Key, 0)).ToList();
                foreach (var g in on.GroupBy(r => r.Name).Where(g => g.Count() > 1))
                {
                    var l = g.ToList();
                    for (var i = 0; i < l.Count; i++)
                        for (var j = i + 1; j < l.Count; j++)
                        {
                            var a = l[i]; var b = l[j];
                            if (!a.Unique || !b.Unique) continue; // only named persons (Unique bases) can stand twice; crowds of one kind may share a name
                            if (!Owns(m, owned, a) && !Owns(m, owned, b)) continue;
                            var how = a.Spot.CellId == b.Spot.CellId ? "in one cell" : m.Joined(a.Spot, b.Spot) ? "in two cells joined by a door pair"
                                : !a.Spot.Interior && !b.Spot.Interior && a.Spot.World == b.Spot.World && a.Spot.Dist(b.Spot) <= 8192 ? $"{a.Spot.Dist(b.Spot):F0} units apart" : null;
                            if (how != null && seen.Add(a.Key + b.Key))
                                yield return Fail(q, "people", $"'{g.Key}' stands twice at {label}: {Nm(m, a.Key)} and {Nm(m, b.Key)}, {how}");
                        }
                }
            }
        }
    }
    static bool Owns(QModel m, HashSet<string> owned, R r)
    {
        for (var k = r.Key; k != "" && m.Refs.TryGetValue(k, out var x); k = x.Parent) if (owned.Contains(k)) return true;
        return false;
    }
    static bool Enabled(QModel m, Dictionary<string, bool> state, string key, int depth)
    {
        if (!m.Refs.TryGetValue(key, out var r) || depth > 8) return false;
        if (r.Parent != "" && m.Refs.ContainsKey(r.Parent)) return Enabled(m, state, r.Parent, depth + 1) ^ r.Opp;
        return state.GetValueOrDefault(key, !r.Disabled);
    }

    // 8. offers: a topic line gated on the quest's own stage has an upper bound below the first ending.
    public static IEnumerable<string> Offers(QModel m)
    {
        foreach (var q in m.Checked)
        {
            var end = q.FirstEnding;
            foreach (var i in q.Infos.Where(i => !i.Hello))
            {
                var own = i.Conds.Where(c => c.Quest == q.Key).ToList();
                if (own.Count == 0) continue;
                var upper = own.Where(c => c.Op is Op.Eq or Op.Lt or Op.Le).Select(c => c.Op == Op.Lt ? c.V - 1 : c.V).DefaultIfEmpty(float.MaxValue).Min();
                if (upper == float.MaxValue || (end != null && upper >= end))
                    yield return Fail(q, "offers", $"a line of topic {i.Topic} is gated {string.Join(" and ", own.Select(c => $"stage {Sym(c.Op)} {c.V:F0}"))} with no upper bound below the first ending ({end?.ToString() ?? "none"}): it is still offered after the quest ends");
            }
        }
    }
    static string Sym(Op o) => o switch { Op.Eq => "==", Op.Ne => "!=", Op.Lt => "<", Op.Le => "<=", Op.Gt => ">", _ => ">=" };

    // 9. doors: a key-locked ref of ours is opened (or its key given) on every ending of a quest whose script holds it.
    public static IEnumerable<string> Doors(QModel m)
    {
        foreach (var d in m.Refs.Values.Where(r => r.InMod && r.Locked))
            foreach (var q in m.Checked.Where(q => q.Props.Values.Any(p => p.Obj == d.Key || p.Obj == d.LockKey)))
                foreach (var e in q.Stages.Where(s => s.Ending))
                {
                    var eff = FragEffects(m, q, e.Index);
                    var given = eff.Any(x => x.Kind == "give" && RefsOf(m, q, x.Target).Contains(d.LockKey)) || eff.Any(x => x.Kind == "unlock" && RefsOf(m, q, x.Target).Contains(d.Key));
                    if (!given) yield return Fail(q, "doors", $"{Nm(m, d.Key)} is locked with key {d.LockKey} and the player is locked out on ending {e.Index} (the key is not given, the door not unlocked)");
                }
    }

    public static List<string> All(QModel m) =>
        [.. new[] { Route(m), Start(m), Shape(m), Stages(m), Endings(m), Zones(m), People(m), Offers(m), Doors(m) }.SelectMany(x => x).Distinct()];
}

// ---- the loader: Argonia.esp, the load order and the Papyrus source into the plain model.
static partial class QuestCheck
{
    public static int Run(string esp, string papyrusDir, string[] paths)
    {
        var mods = Survey.Load(paths.Append(esp));
        var m = Load(mods, papyrusDir);
        var fails = All(m);
        foreach (var f in fails) Console.WriteLine(f);
        var n = m.Checked.Count();
        Console.WriteLine($"questcheck: {n} quests, {fails.Count} failed checks");
        return fails.Count == 0 ? 0 : 1;
    }

    static Op ToOp(CompareOperator o) => o switch
    {
        CompareOperator.EqualTo => Op.Eq, CompareOperator.NotEqualTo => Op.Ne, CompareOperator.LessThan => Op.Lt,
        CompareOperator.LessThanOrEqualTo => Op.Le, CompareOperator.GreaterThan => Op.Gt, _ => Op.Ge,
    };

    static QModel Load(List<ISkyrimModGetter> mods, string papyrusDir)
    {
        var m = new QModel(); var mine = mods[^1];
        foreach (var dir in new[] { papyrusDir, Path.Combine(papyrusDir, "generated") })
            if (Directory.Exists(dir))
                foreach (var f in Directory.GetFiles(dir, "*.psc")) m.Scripts[Path.GetFileNameWithoutExtension(f)] = Parse(Path.GetFileNameWithoutExtension(f), File.ReadAllText(f));

        // refs: ours first, then whichever referenced refs live in the other plugins that carry them
        Ingest(m, mine, null, true);
        var need = new HashSet<FormKey>();
        void Need(FormKey k) { if (!k.IsNull && !m.Refs.ContainsKey(k.ToString())) need.Add(k); }
        foreach (var q in mine.Quests)
        {
            foreach (var a in q.Aliases) Need(a.ForcedReference.FormKey);
            foreach (var s in q.VirtualMachineAdapter?.Scripts ?? []) foreach (var p in s.Properties.OfType<IScriptObjectPropertyGetter>()) Need(p.Object.FormKey);
        }
        foreach (var r in m.Refs.Values.ToList()) { if (r.Tele != "") Need(FormKey.Factory(r.Tele)); if (r.Parent != "") Need(FormKey.Factory(r.Parent)); }
        foreach (var p in mine.Packages) foreach (var d in p.Data.Values.OfType<IPackageDataLocationGetter>()) if (d.Location.Target is ILocationTargetGetter lt) Need(lt.Link.FormKey);
        if (need.Count > 0)
            foreach (var other in mods.Take(mods.Count - 1).Where(o => !IsVanilla(o.ModKey)))
                Ingest(m, other, need, false);

        foreach (var (a, b) in m.Refs.Values.Where(r => r.Tele != "").Select(r => (r, m.Refs.GetValueOrDefault(r.Tele))).Where(x => x.Item2 != null))
        {
            m.DoorPairs.Add(a.Spot.CellId + "|" + b!.Spot.CellId); m.DoorPairs.Add(b.Spot.CellId + "|" + a.Spot.CellId);
            if (!m.DoorSpots.TryGetValue(a.Spot.CellId, out var la)) m.DoorSpots[a.Spot.CellId] = la = []; la.Add(b.Spot);
            if (!m.DoorSpots.TryGetValue(b.Spot.CellId, out var lb)) m.DoorSpots[b.Spot.CellId] = lb = []; lb.Add(a.Spot);
        }

        var npcs = new Dictionary<FormKey, INpcGetter>();
        foreach (var mod in mods) foreach (var n in mod.Npcs) npcs[n.FormKey] = n;
        foreach (var r in m.Refs.Values.Where(r => r.Npc))
        {
            if (!npcs.TryGetValue(FormKey.Factory(r.Base), out var n)) continue;
            r.Essential = n.Configuration.Flags.HasFlag(NpcConfiguration.Flag.Essential); r.Unique = n.Configuration.Flags.HasFlag(NpcConfiguration.Flag.Unique);
            var v = n; for (var i = 0; i < 8 && string.IsNullOrEmpty(v.Name?.String) && v.Configuration.TemplateFlags.HasFlag(NpcConfiguration.TemplateFlag.Traits) && npcs.TryGetValue(v.Template.FormKey, out var t); i++) v = t;
            r.Name = v.Name?.String ?? "";
        }

        foreach (var p in mine.Packages) m.Packs[p.FormKey.ToString()] = ToPack(p);
        foreach (var q in mine.Quests) m.Quests.Add(ToQuest(m, mine, q));
        LoadNav(m, mods);
        return m;
    }
    static bool IsVanilla(ModKey k) => k.FileName.String is "Skyrim.esm" or "Update.esm" or "Dawnguard.esm" or "HearthFires.esm" or "Dragonborn.esm" || k.FileName.String.StartsWith("cc", StringComparison.OrdinalIgnoreCase);

    static void Ingest(QModel m, ISkyrimModGetter mod, HashSet<FormKey>? want, bool ours)
    {
        var world = new Dictionary<FormKey, string>();
        foreach (var ws in mod.Worldspaces)
        {
            foreach (var c in ws.SubCells.SelectMany(b => b.Items).SelectMany(sb => sb.Items)) world[c.FormKey] = ws.FormKey.ToString();
            if (ws.TopCell != null) world[ws.TopCell.FormKey] = ws.FormKey.ToString();
        }
        foreach (var c in mod.EnumerateMajorRecords<ICellGetter>())
        {
            var interior = c.Flags.HasFlag(Cell.Flag.IsInteriorCell); var w = world.GetValueOrDefault(c.FormKey) ?? "";
            foreach (var r in c.Persistent.Concat(c.Temporary))
            {
                if (want != null && !want.Contains(r.FormKey)) continue;
                var key = r.FormKey.ToString(); if (m.Refs.ContainsKey(key) && !ours) continue;
                var x = new R { Key = key, InMod = ours, Ours = ours && r.FormKey.ModKey == mod.ModKey, Edid = r.EditorID ?? "" };
                IReadOnlyList<IScriptEntryGetter>? scripts = null; IEnableParentGetter? ep;
                switch (r)
                {
                    case IPlacedObjectGetter o:
                        if (o.Placement == null) continue;
                        x.Base = o.Base.FormKey.ToString(); Pos(x, o.Placement.Position, c, interior, w);
                        x.Disabled = (o.MajorRecordFlagsRaw & 0x800) != 0; ep = o.EnableParent; x.Tele = o.TeleportDestination?.Door.FormKey.IsNull == false ? o.TeleportDestination.Door.FormKey.ToString() : "";
                        if (o.Lock is { } lk && (lk.Level == LockLevel.RequiresKey || (int)lk.Level >= 254) && !lk.Key.IsNull) { x.Locked = true; x.LockKey = lk.Key.FormKey.ToString(); } // 255 is how the game stores "requires key"
                        scripts = o.VirtualMachineAdapter?.Scripts;
                        foreach (var sc in scripts ?? [])
                        {
                            if (!sc.Name.StartsWith("defaultSetStage", StringComparison.OrdinalIgnoreCase)) continue;
                            var ints = sc.Properties.OfType<IScriptIntPropertyGetter>().ToDictionary(p => p.Name, p => p.Data, StringComparer.OrdinalIgnoreCase);
                            var qk = sc.Properties.OfType<IScriptObjectPropertyGetter>().FirstOrDefault(p => p.Name.Equals("myQuest", StringComparison.OrdinalIgnoreCase))?.Object.FormKey.ToString() ?? "";
                            var bd = o.Primitive?.Bounds ?? default;
                            m.Trigs.Add(new Trig { Ref = x, Quest = qk, Prereq = ints.Where(kv => kv.Key.Contains("prereq", StringComparison.OrdinalIgnoreCase)).Select(kv => kv.Value).FirstOrDefault(-1), Stage = ints.GetValueOrDefault("stage", -1),
                                Zone = sc.Name.Equals("defaultSetStageTrigScript", StringComparison.OrdinalIgnoreCase), Hx = bd.X, Hy = bd.Y, Hz = bd.Z });
                        }
                        break;
                    case IPlacedNpcGetter n:
                        if (n.Placement == null) continue;
                        x.Npc = true; x.Base = n.Base.FormKey.ToString(); Pos(x, n.Placement.Position, c, interior, w);
                        x.Disabled = (n.MajorRecordFlagsRaw & 0x800) != 0; ep = n.EnableParent;
                        break;
                    default: continue;
                }
                if (ep != null && !ep.Reference.IsNull) { x.Parent = ep.Reference.FormKey.ToString(); x.Opp = ep.Flags.HasFlag(EnableParent.Flag.SetEnableStateToOppositeOfParent); }
                m.Refs[key] = x;
            }
        }
    }
    static void Pos(R x, Noggog.P3Float p, ICellGetter c, bool interior, string world) =>
        x.Spot = new Spot(interior ? c.FormKey.ToString() : "", interior, world, p.X, p.Y, p.Z);

    static Pk ToPack(IPackageGetter p)
    {
        var pk = new Pk { Key = p.FormKey.ToString(), Edid = p.EditorID ?? "", IsPackage = p.Type == Package.Types.Package, HasTemplate = !p.PackageTemplate.IsNull, Hour = p.ScheduleHour };
        foreach (var c in p.Conditions.OfType<IConditionFloatGetter>())
        {
            if (c.Data is IGetStageConditionDataGetter g) pk.Stages.Add(new Cond(g.Quest.Link.FormKey.ToString(), ToOp(c.CompareOperator), c.ComparisonValue));
            else if (c.Data is IGetCurrentTimeConditionDataGetter) pk.Clock = true;
        }
        foreach (var d in p.Data.Values)
        {
            if (d is IPackageDataLocationGetter l && l.Location.Target is ILocationTargetGetter lt && !lt.Link.FormKey.IsNull) pk.Location ??= lt.Link.FormKey.ToString();
            if (d is IPackageDataTargetGetter t && t.Target is IPackageTargetSpecificReferenceGetter sr && !sr.Reference.FormKey.IsNull) pk.Follow ??= sr.Reference.FormKey.ToString();
        }
        if (pk.Location != null) pk.Follow = null;
        return pk;
    }

    static Q ToQuest(QModel m, ISkyrimModGetter mine, IQuestGetter q)
    {
        var e = q.EditorID ?? "";
        var res = new Q { Key = q.FormKey.ToString(), Edid = e, RunOnce = q.Flags.HasFlag(Quest.Flag.RunOnce), StartGame = q.Flags.HasFlag(Quest.Flag.StartGameEnabled),
            Check = e.StartsWith("ARG_") && !e.StartsWith("ARG_BlockTest") && e != "ARG_Opening"
                && q.Stages.Any(s => s.Index > 0) }; // a story quest; a dialogue-only quest (ARG_Talk) has no stage but 0
        foreach (var s in q.Stages)
            res.Stages.Add(new St { Index = s.Index, StartUp = s.Flags.HasFlag(QuestStage.Flag.StartUpStage),
                HasText = s.LogEntries.Any(l => !string.IsNullOrWhiteSpace(l.Entry?.String)),
                Ending = s.LogEntries.Any(l => l.Flags.HasValue && (l.Flags.Value.HasFlag(QuestLogEntry.Flag.CompleteQuest) || l.Flags.Value.HasFlag(QuestLogEntry.Flag.FailQuest))) });
        foreach (var o in q.Objectives) res.Objs.Add(new Ob { Index = (int)o.Index, Targets = o.Targets.Count });
        foreach (var a in q.Aliases)
            res.Aliases.Add(new Al { Id = (int)a.ID, Name = a.Name ?? "", Essential = a.Flags?.HasFlag(QuestAlias.Flag.Essential) == true, Forced = a.ForcedReference.IsNull ? null : a.ForcedReference.FormKey.ToString(),
                Packs = a.PackageData.Select(p => p.FormKey.ToString()).ToList() });
        var vm = q.VirtualMachineAdapter;
        if (vm != null)
        {
            foreach (var s in vm.Scripts)
                foreach (var p in s.Properties)
                    switch (p)
                    {
                        case IScriptObjectPropertyGetter o: res.Props[o.Name] = new Pr { Obj = o.Object.FormKey.ToString(), Alias = o.Alias }; break;
                        case IScriptObjectListPropertyGetter l: res.Props[l.Name] = new Pr { Arr = l.Objects.Select(x => x.Object.FormKey.ToString()).ToArray() }; break;
                    }
            res.Script = vm.Fragments.Select(f => f.ScriptName).FirstOrDefault() ?? vm.Scripts.Select(s => s.Name).FirstOrDefault();
            foreach (var f in vm.Fragments) res.Frags.TryAdd(f.Stage, (f.ScriptName, f.FragmentName));
            foreach (var a in vm.Aliases)
            {
                var al = res.Aliases.FirstOrDefault(x => x.Id == a.Property.Alias); if (al == null) continue;
                foreach (var s in a.Scripts)
                {
                    var sc = new AS { Name = s.Name };
                    foreach (var p in s.Properties.OfType<IScriptIntPropertyGetter>()) sc.Ints[p.Name] = p.Data;
                    foreach (var p in s.Properties.OfType<IScriptObjectPropertyGetter>()) sc.Objs[p.Name] = p.Object.FormKey.ToString();
                    al.Scripts.Add(sc);
                }
            }
        }
        foreach (var t in mine.DialogTopics.Where(t => t.Quest.FormKey == q.FormKey))
            foreach (var r in t.Responses)
            {
                var i = new Info { Topic = t.EditorID ?? t.FormKey.ToString(), Hello = t.Subtype == DialogTopic.SubtypeEnum.Hello };
                foreach (var c in r.Conditions.OfType<IConditionFloatGetter>())
                    switch (c.Data)
                    {
                        case IGetStageConditionDataGetter g: i.Conds.Add(new Cond(g.Quest.Link.FormKey.ToString(), ToOp(c.CompareOperator), c.ComparisonValue)); break;
                        case IGetIsIDConditionDataGetter d: i.Bases.Add(d.Object.Link.FormKey.ToString()); break;
                        case IGetIsReferenceConditionDataGetter rf: i.Refs.Add(rf.Target.Link.FormKey.ToString()); break;
                    }
                var fr = r.VirtualMachineAdapter?.ScriptFragments;
                var end = fr?.OnEnd ?? fr?.OnBegin;
                if (end != null) { i.Frag = end.ScriptName; i.FragFn = end.FragmentName; }
                res.Infos.Add(i);
            }
        return res;
    }

    static void LoadNav(QModel m, List<ISkyrimModGetter> mods)
    {
        var versions = new Dictionary<FormKey, List<(INavigationMeshGetter rec, ModKey from)>>();
        foreach (var mod in mods) foreach (var n in mod.EnumerateMajorRecords<INavigationMeshGetter>()) { if (!versions.TryGetValue(n.FormKey, out var l)) versions[n.FormKey] = l = []; l.Add((n, mod.ModKey)); }
        var regions = new HashSet<string>();
        foreach (var s in m.Refs.Values.Where(r => r.Ours).Select(r => r.Spot).Concat(m.Refs.Values.Select(r => r.Spot)))
            foreach (var (dx, dy) in s.Interior ? [(0, 0)] : new[] { (0, 0), (-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1) })
                regions.Add(s.Interior ? "I:" + s.Cell : $"W:{s.World}:{(int)Math.Floor(s.X / 4096) + dx}:{(int)Math.Floor(s.Y / 4096) + dy}");
        static string Region(INavigationMeshDataGetter d) => d.Parent switch
        {
            IWorldspaceNavmeshParentGetter w => $"W:{w.Parent.FormKey}:{w.Coordinates.Y}:{w.Coordinates.X}",
            ICellNavmeshParentGetter c => "I:" + c.Parent.FormKey,
            _ => "?",
        };
        foreach (var (fk, list) in versions)
        {
            var win = list[^1];
            var live = list.LastOrDefault(v => v.rec.Data is { } dd && dd.Vertices.Count > 0);
            if (live.rec == null) continue;
            var region = Region(live.rec.Data!);
            if (!regions.Contains(region)) continue;
            var deleted = win.rec.Data == null || win.rec.Data.Vertices.Count == 0;
            var d = live.rec.Data!; var mesh = new Mesh { Id = fk.ToString(), Region = region, Plugin = live.from.FileName.String, Deleted = deleted, DeletedBy = deleted ? win.from.FileName.String : "" };
            mesh.V = d.Vertices.Select(v => new[] { v.X, v.Y, v.Z }).ToArray();
            mesh.T = d.Triangles.Select(t => new[] { (int)t.Vertices.X, (int)t.Vertices.Y, (int)t.Vertices.Z }).ToArray();
            mesh.Nb = d.Triangles.Select(t =>
            {
                var res = new List<(string, int)?>(); var e = new[] { (int)t.EdgeLink_0_1, (int)t.EdgeLink_1_2, (int)t.EdgeLink_2_0 };
                for (var k = 0; k < 3; k++)
                {
                    if (e[k] < 0) continue;
                    if (((int)t.Flags & (1 << k)) != 0) { if (e[k] < d.EdgeLinks.Count) res.Add((d.EdgeLinks[e[k]].Mesh.FormKey.ToString(), (int)d.EdgeLinks[e[k]].TriangleIndex)); }
                    else res.Add((mesh.Id, e[k]));
                }
                return res.ToArray();
            }).ToArray();
            m.Nav.Add(mesh);
        }
    }
}

// ---- questcheck --selftest: each rule judged on a hand-made model, one passing and one failing case.
static partial class QuestCheck
{
    static Spot S(float x, float y = 50) => new("", false, "W", x, y, 0);
    static Mesh Sq(string id, float x0, float x1) => new()
    {
        Id = id, Region = "W:W:0:0", Plugin = "T.esp", V = [[x0, 0, 0], [x1, 0, 0], [x1, 100, 0], [x0, 100, 0]], T = [[0, 1, 2], [0, 2, 3]],
        Nb = [[(id, 1)], [(id, 0)]],
    };
    static R Rf(string key, Spot s, bool npc = false) => new() { Key = key, Edid = key, Spot = s, Npc = npc, Ours = true };

    // A model every rule passes: quest ARG_T (RunOnce, stages 10 and 90 set by zones, Stop and both zones disabled at 90),
    // a walker whose package walks to a marker on one navmesh and starts at a stage a zone beside him sets.
    static QModel Fx()
    {
        var m = new QModel();
        foreach (var r in new[] { Rf("z10", S(50)), Rf("z90", S(3000)), Rf("w", S(50), true), Rf("d", S(60)) }) m.Refs[r.Key] = r;
        m.Trigs.Add(new Trig { Ref = m.Refs["z10"], Quest = "q1", Prereq = -1, Stage = 10, Zone = true, Hx = 50, Hy = 50, Hz = 50 });
        m.Trigs.Add(new Trig { Ref = m.Refs["z90"], Quest = "q1", Prereq = 10, Stage = 90, Zone = true, Hx = 50, Hy = 50, Hz = 50 });
        m.Nav.Add(Sq("a", 0, 100)); m.Nav.Add(Sq("b", 1000, 1100));
        m.Scripts["QF"] = Parse("QF", "Function Fragment_10()\n SetObjectiveDisplayed(10)\nEndFunction\nFunction Fragment_90()\n Z10.Disable()\n Z90.Disable()\n Stop()\nEndFunction\n");
        m.Packs["p"] = new Pk { Key = "p", Edid = "P", Location = "d", Stages = [new Cond("q1", Op.Ge, 10)] };
        var q = new Q { Key = "q1", Edid = "ARG_T", Check = true, RunOnce = true, StartGame = true, Script = "QF" };
        q.Stages = [new St { Index = 0, StartUp = true }, new St { Index = 10, HasText = true }, new St { Index = 90, HasText = true, Ending = true }];
        q.Objs = [new Ob { Index = 10, Targets = 1 }];
        q.Frags[10] = ("QF", "Fragment_10"); q.Frags[90] = ("QF", "Fragment_90");
        q.Props["Z10"] = new Pr { Obj = "z10" }; q.Props["Z90"] = new Pr { Obj = "z90" };
        q.Aliases = [new Al { Id = 1, Name = "Walker", Forced = "w", Packs = ["p"] }];
        m.Quests.Add(q);
        return m;
    }

    public static int SelfTest()
    {
        var bad = 0;
        void T(string name, bool fails, Func<QModel, IEnumerable<string>> rule, Action<QModel>? tweak = null)
        {
            var m = Fx(); tweak?.Invoke(m); var n = rule(m).Count();
            if ((n > 0) != fails) { bad++; Console.WriteLine($"SELFTEST FAIL {name}: expected {(fails ? "a finding" : "none")}, got {n}"); }
        }
        var q = (QModel m) => m.Quests[0];
        T("route pass", false, Route);
        T("route fail: not connected", true, Route, m => m.Refs["d"].Spot = S(1050));
        T("route fail: off mesh", true, Route, m => m.Refs["d"].Spot = S(2500));
        T("start pass", false, Start);
        T("start fail: setter out of reach", true, Start, m => m.Refs["z10"].Spot = S(9000));
        T("start pass: Is3DLoaded before the set", false, Start, m =>
        {
            m.Refs["z10"].Spot = S(9000); m.Trigs.RemoveAll(t => t.Stage == 10);
            m.Scripts["QF"] = Parse("QF", "Function OnUpdate()\n If w.GetRef().Is3DLoaded()\n SetStage(10)\n EndIf\nEndFunction\nFunction Fragment_10()\n SetObjectiveDisplayed(10)\nEndFunction\nFunction Fragment_90()\n Z10.Disable()\n Z90.Disable()\n Stop()\nEndFunction\n");
        });
        T("shape pass", false, Shape);
        T("shape fail: template type", true, Shape, m => m.Packs["p"].IsPackage = false);
        T("shape fail: no template link", true, Shape, m => m.Packs["p"].HasTemplate = false);
        T("stages pass", false, Stages);
        T("stages fail: no setter", true, Stages, m => m.Trigs.RemoveAll(t => t.Stage == 90));
        T("stages fail: death on an Essential", true, Stages, m =>
        {
            m.Trigs.RemoveAll(t => t.Stage == 90);
            var al = q(m).Aliases[0]; al.Essential = true; al.Scripts.Add(new AS { Name = "defaultSetStageOnDeathRefAlias", Ints = { ["StageToSet"] = 90 }, Objs = { ["myQST"] = "q1" } });
        });
        T("stages fail: objective without target", true, Stages, m => q(m).Objs[0].Targets = 0);
        T("stages fail: journal text but no objective", true, Stages, m => m.Scripts["QF"].Fns["Fragment_10"].Body.Clear());
        T("stages fail: no way out", true, Stages, m => m.Trigs.RemoveAll(t => t.Stage == 90));
        T("endings pass", false, Endings);
        T("endings fail: no Stop", true, Endings, m => m.Scripts["QF"].Fns["Fragment_90"].Body.RemoveAll(s => s.Kind == "stop"));
        T("endings fail: zone left", true, Endings, m => m.Scripts["QF"].Fns["Fragment_90"].Body.RemoveAll(s => s.Target == "Z90"));
        T("endings fail: not RunOnce", true, Endings, m => q(m).RunOnce = false);
        T("zones pass", false, Zones);
        T("zones fail: overlap", true, Zones, m => m.Trigs.Add(new Trig { Ref = m.Refs["z90"], Quest = "q1", Prereq = 90, Stage = 91, Zone = true, Hx = 50, Hy = 50, Hz = 50 }));
        T("people pass", false, People, m => { m.Refs["w"].Name = "Same"; m.Refs["w"].Unique = true; var o = Rf("o", S(70), true); o.Name = "Same"; o.Unique = true; o.Base = "b2"; o.Disabled = true; m.Refs["o"] = o; });
        T("people fail: one person twice", true, People, m => { m.Refs["w"].Name = "Same"; m.Refs["w"].Unique = true; var o = Rf("o", S(70), true); o.Name = "Same"; o.Unique = true; o.Base = "b2"; m.Refs["o"] = o; });
        T("offers pass", false, Offers, m => q(m).Infos.Add(new Info { Topic = "T", Conds = [new Cond("q1", Op.Ge, 10), new Cond("q1", Op.Lt, 90)] }));
        T("offers fail: no upper bound", true, Offers, m => q(m).Infos.Add(new Info { Topic = "T", Conds = [new Cond("q1", Op.Ge, 10)] }));
        T("doors pass", false, Doors, m => { Door(m); m.Scripts["QF"].Fns["Fragment_90"].Body.Add(new Stmt("give", "Key", [])); });
        T("doors fail: locked out", true, Doors, Door);
        Console.WriteLine(bad == 0 ? "questcheck selftest: all rules judge their fixtures" : $"questcheck selftest: {bad} misjudged");
        return bad == 0 ? 0 : 1;
    }
    static void Door(QModel m)
    {
        m.Refs["door"] = new R { Key = "door", Edid = "door", Spot = S(0), Ours = true, InMod = true, Locked = true, LockKey = "key" };
        m.Quests[0].Props["Key"] = new Pr { Obj = "key" };
    }
}
