// ArgoniaGen: the Mutagen side of the pipeline (decision 0009). Python plans and resolves; this writes records.
//   counts     --data <dir>                                      records per major type in Skyrim.esm (0.1)
//   index      --data <dir> --plugins a.esm,b.esm --out <json>  every modelled base record and archive mesh (pieces.py)
//   cells      --data <dir> --plugins a.esm,b.esp --out <json>   every interior cell's refs, bases and door partners (CellScan.cs)
//   quests     --data <dir> --plugins a.esm,b.esm --out <json>  vanilla quests: start-game-enabled and story-manager-started
//   generate   --in <json> --data <dir> --out <Argonia.esm>     the records, written deterministically
//   ltex       --data <dir> --plugins a.esm,b.esp --out <json>   every LTEX's winning copy and every GRAS (LandTextures.cs)
//   world      --in <json> --land <dir> --data <dir> --out <ArgoniaWorld.esm> [--water <dir>] [--navmesh <dir>]   the generated ground (LandWorld.cs), its water (WaterRecords.cs) and navmesh (NavmeshRecords.cs)
//   vegetation --in <ArgoniaWorld.esm> --veg <dir> --out <esm>   the vegetation REFRs spliced into each cell's Temporary group (VegetationRecords.cs)
//   vegcheck   --in <esm> --first <hex> --last <hex> --out <jsonl>   its Mutagen read-back: vegetation REFRs per cell
//   links      --data <dir> --order <file> --check a.esm,b.esm [--ours <dir>]   every FormLink and master resolved in the game's order (LinkCheck.cs)
//   navmesh    roundtrip --in <jsonl.gz> --data <dir> --out <esm>   the vanilla NAVM round trip (NavmeshRecords.cs)
using ArgoniaGen;

static int Fail(string m) { Console.Error.WriteLine(m); return 1; }

string? Opt(string name)
{
    var i = Array.IndexOf(args, name);
    return i >= 0 && i + 1 < args.Length ? args[i + 1] : null;
}

string Dir(string? p) => Path.GetFullPath((p ?? "").Replace("~", Environment.GetEnvironmentVariable("HOME") ?? "~"));
string[] Plugins() => (Opt("--plugins") ?? "Skyrim.esm").Split(',', StringSplitOptions.RemoveEmptyEntries);

if (args.Length == 0) return Fail("usage: ArgoniaGen counts|index|quests|generate|ltex|world ... (see Program.cs header)");
try
{
    switch (args[0])
    {
        case "counts":
            return Counts.Run(Dir(Opt("--data")));
        case "index":
            return PieceIndex.Run(Dir(Opt("--data")), Plugins(), Opt("--out") ?? throw new ArgumentException("missing --out"));
        case "cells":
            return CellScan.Run(Dir(Opt("--data")), Plugins(), Opt("--out") ?? throw new ArgumentException("missing --out"));
        case "quests":
            return QuestScan.Run(Dir(Opt("--data")), Plugins(), Opt("--out") ?? throw new ArgumentException("missing --out"));
        case "generate":
            return Generate.Run(Opt("--in") ?? throw new ArgumentException("missing --in"), Dir(Opt("--data")),
                                Opt("--out") ?? throw new ArgumentException("missing --out"));
        case "ltex":
            return LandTextures.Scan(Dir(Opt("--data")), Plugins(), Opt("--out") ?? throw new ArgumentException("missing --out"));
        case "world":
            return LandWorld.Run(Opt("--in") ?? throw new ArgumentException("missing --in"),
                                 Opt("--land") ?? throw new ArgumentException("missing --land"), Dir(Opt("--data")),
                                 Opt("--out") ?? throw new ArgumentException("missing --out"), Opt("--water"), Opt("--navmesh"));
        case "vegetation":
            return VegetationRecords.Run(Opt("--in") ?? throw new ArgumentException("missing --in"),
                                         Opt("--veg") ?? throw new ArgumentException("missing --veg"),
                                         Opt("--out") ?? throw new ArgumentException("missing --out"));
        case "vegcheck":
            return VegetationRecords.Check(Opt("--in") ?? throw new ArgumentException("missing --in"),
                                           Convert.ToUInt32(Opt("--first") ?? "0", 16), Convert.ToUInt32(Opt("--last") ?? "FFFFFF", 16),
                                           Opt("--out") ?? throw new ArgumentException("missing --out"));
        case "packages":
            return PackageRecords.Dump(Dir(Opt("--data")), Opt("--out") ?? throw new ArgumentException("missing --out"), (Opt("--edids") ?? "").Split(','), Opt("--plugin") ?? "Skyrim.esm");
        case "navmesh":
            return NavmeshRecords.Run(args, Opt, Dir);
        case "links":
            return LinkCheck.Run(Dir(Opt("--data")), Opt("--order") ?? throw new ArgumentException("missing --order"), (Opt("--check") ?? "Argonia.esm,ArgoniaWorld.esm").Split(','), Opt("--ours") is { } o ? string.Join(',', o.Split(',').Select(Dir)) : null);
        default:
            return Fail($"unknown command {args[0]}");
    }
}
catch (Exception e) when (e is ArgumentException or FileNotFoundException or InvalidDataException)
{
    return Fail(e.Message);
}
