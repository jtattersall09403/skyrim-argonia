// ArgoniaGen: the Mutagen side of the pipeline (decision 0009). Python plans and resolves; this writes records.
//   counts     --data <dir>                                      records per major type in Skyrim.esm (0.1)
//   index      --data <dir> --plugins a.esm,b.esm --out <json>  every modelled base record and archive mesh (pieces.py)
//   quests     --data <dir> --plugins a.esm,b.esm --out <json>  vanilla quests: start-game-enabled and story-manager-started
//   generate   --in <json> --data <dir> --out <Argonia.esm>     the records, written deterministically
//   world      --in <json> --land <dir> --data <dir> --out <ArgoniaWorld.esm>   the generated ground (LandWorld.cs)
using ArgoniaGen;

static int Fail(string m) { Console.Error.WriteLine(m); return 1; }

string? Opt(string name)
{
    var i = Array.IndexOf(args, name);
    return i >= 0 && i + 1 < args.Length ? args[i + 1] : null;
}

string Dir(string? p) => Path.GetFullPath((p ?? "").Replace("~", Environment.GetEnvironmentVariable("HOME") ?? "~"));
string[] Plugins() => (Opt("--plugins") ?? "Skyrim.esm").Split(',', StringSplitOptions.RemoveEmptyEntries);

if (args.Length == 0) return Fail("usage: ArgoniaGen counts|index|quests|generate|world ... (see Program.cs header)");
try
{
    switch (args[0])
    {
        case "counts":
            return Counts.Run(Dir(Opt("--data")));
        case "index":
            return PieceIndex.Run(Dir(Opt("--data")), Plugins(), Opt("--out") ?? throw new ArgumentException("missing --out"));
        case "quests":
            return QuestScan.Run(Dir(Opt("--data")), Plugins(), Opt("--out") ?? throw new ArgumentException("missing --out"));
        case "generate":
            return Generate.Run(Opt("--in") ?? throw new ArgumentException("missing --in"), Dir(Opt("--data")),
                                Opt("--out") ?? throw new ArgumentException("missing --out"));
        case "world":
            return LandWorld.Run(Opt("--in") ?? throw new ArgumentException("missing --in"),
                                 Opt("--land") ?? throw new ArgumentException("missing --land"), Dir(Opt("--data")),
                                 Opt("--out") ?? throw new ArgumentException("missing --out"));
        default:
            return Fail($"unknown command {args[0]}");
    }
}
catch (Exception e) when (e is ArgumentException or FileNotFoundException or InvalidDataException)
{
    return Fail(e.Message);
}
