// ArgoniaPlacesBuild: the place layer plugin (docs/design/place-studio.md, Build). Driven by tools/places/build.py.
//   write <plan.json> <out.esp>          the plugin from the resolved plan (Write.cs)
//   dump <esp> <world.esm> <out.json>    the read-back the checks read (Dump.cs)
//   world <world.esm> <request.json> <out.json>   facts of the world ESM the plan needs (World.cs)
//   study <Data dir> <plugin...>         override evidence (Study.cs)
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

static int Usage() { Console.Error.WriteLine("ArgoniaPlacesBuild write|dump|world|study ..."); return 2; }
