// ArgoniaPlacesBuild: the place layer plugin (docs/design/place-studio.md, Build). Driven by tools/places/build.py.
//   write <out.esp> <world.esm> <plan.json...>    the plugin from the places' resolved plans (Write.cs)
//   dump <esp> <world.esm> <out.json>             the read-back the checks read (Dump.cs)
//   world <world.esm> <request.json> <out.json>   facts of the world ESM the plan needs (Read.cs)
//   source <plugin> <cell> <out.json> | doors <plugin> <worldspace> <out.json> | list <plugin> <kind> <out.json> |
//   links <key...>                                what a source plugin holds (Read.cs)
//   study <Data dir> <plugin...> | carriage <Skyrim.esm>   override and travel-line evidence (Study.cs)
var need = args.FirstOrDefault() switch { "write" or "dump" or "world" or "source" or "doors" or "list" => 4, "study" or "carriage" or "links" => 2, _ => 0 };
if (args.Length < need) return Usage();
return (args.FirstOrDefault()) switch
{
    "carriage" => Study.Carriage(args[1]),
    "study" => Study.Run(args[1..]),
    "source" => Read.Source(args[1], args[2], args[3]),
    "doors" => Read.Doors(args[1], args[2], args[3]),
    "list" => Read.List(args[1], args[2], args[3]),
    "links" => Read.Links(args[1..]),
    "dump" => Dump.Run(args[1], args[2], args[3]),
    "write" => Write.Run(args[1], args[2], args[3..]),
    "world" => Read.World(args[1], args[2], args[3]),
    _ => Usage(),
};

static int Usage()
{
    Console.Error.WriteLine("ArgoniaPlacesBuild write <out.esp> <world.esm> <plan.json...> | dump <esp> <world.esm> <out.json> | world <world.esm> <request.json> <out.json> | "
        + "source <plugin> <cell> <out.json> | doors <plugin> <worldspace> <out.json> | list <plugin> <kind> <out.json> | links <key...> | study <Data dir> <plugin...> | carriage <Skyrim.esm>");
    return 2;
}
