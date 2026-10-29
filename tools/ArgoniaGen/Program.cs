// ArgoniaGen: Mutagen-based data tool. Command so far: counts (records per major type, ten largest).
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;

static int Fail(string m) { Console.Error.WriteLine(m); return 1; }

if (args.Length == 0 || args[0] != "counts")
    return Fail("usage: ArgoniaGen counts --data <Skyrim Data dir>");
var i = Array.IndexOf(args, "--data");
if (i < 0 || i + 1 >= args.Length) return Fail("missing --data <dir>");
var path = Path.Combine(Path.GetFullPath(args[i + 1].Replace("~", Environment.GetEnvironmentVariable("HOME") ?? "~")), "Skyrim.esm");
if (!File.Exists(path)) return Fail($"not found: {path}");

using var mod = SkyrimMod.CreateFromBinaryOverlay(path, SkyrimRelease.SkyrimSE);
var counts = mod.EnumerateMajorRecords()
    .GroupBy(r => r.Registration.Name)
    .Select(g => (Type: g.Key, Count: g.Count()))
    .OrderByDescending(t => t.Count)
    .Take(10);
Console.WriteLine($"{Path.GetFileName(path)}: {mod.EnumerateMajorRecords().Count()} major records");
foreach (var (type, count) in counts) Console.WriteLine($"{type,-28}{count,8}");
return 0;
