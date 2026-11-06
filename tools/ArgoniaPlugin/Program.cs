switch (args.FirstOrDefault())
{
    case "study": Study.Run(args[1]); break;
    case "fixup": Fixup.Run(args[1], args[2..]); break;
    case "probe": Probe.Run(args[1], args[2]); break;
    case "list": return Listing.Run(args[1], args[2], args[3..]);
    case "find": Find.Run(args[1], args[2]); break;
    case "seed": Generate.Run(args[1], args[2..]); break;
    case "cell": CellStudy.Run(args[1], args[2]); break;
    case "survey": Survey.Run(args[1..]); break;
    case "seat": Seat.Run(args[1..]); break;
    case "inspect": Inspect.Run(args[1], args[2..]); break;
    case "quests": Study2.Run(args[1], args[2..]); break;
    default: Console.Error.WriteLine("ArgoniaPlugin seed <out.esp> <plugins...> | list <esp> <md> | survey <plugins...> | study|quests|cell|find ..."); return 2;
}
return 0;
