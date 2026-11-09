switch (args.FirstOrDefault())
{
    case "study": Study.Run(args[1]); break;
    case "fixup": Fixup.Run(args[1], args[2..]); break;
    case "seq": return Seq.Run(args[1], args[2]);
    case "nwverify": return NewWorldVerify.Run(args[1..]);
    case "probe": Probe.Run(args[1], args[2]); break;
    case "list": return Listing.Run(args[1], args[2], args[3..]);
    case "find": Find.Run(args[1], args[2]); break;
    case "seed": Surface.Paths = args[2..]; Generate.Run(args[1], args[2..]); break;
    case "cell": CellStudy.Run(args[1], args[2]); break;
    case "waterblend": return WaterBlend.Study(args[2]);
    case "survey": Survey.Run(args[1..]); break;
    case "gives": GiveStudy.Run(args[1..]); break;
    case "seat": Seat.Run(args[1..]); break;
    case "cleancheck": return CleanUp.Check(args[1], args[2..]);
    case "localcheck": return LocalQuestsCheck.Run(args[1], args[2], args[3..]);
    case "bccheck": return ChainbreakersCheck.Run(args[1], args[2], args[3..]);
    case "blocktest": return BlockTestCheck.Run(args[1], args[2], args[3..]);
    case "mqcheck": return MQCheck.Run(args[1], args[2], args[3..]);
    case "mapprobe": MapFix.Probe(args[1..]); break;
    case "musicprobe": Music.Probe(args[1..]); break;
    case "blockstudy": BlockTestStudy.Run(args[1]); break;
    case "surface": Surface.Run(args[1..]); break;
    case "asset": File.WriteAllBytes(args[2], new Surface.Assets(args[3..]).Read(args[1]) ?? throw new FileNotFoundException(args[1])); break; // read only, to a scratch path
    case "inspect": Inspect.Run(args[1], args[2..]); break;
    case "quests": Study2.Run(args[1], args[2..]); break;
    case "nightreed": NightReedStudy.Run(args[1..]); break;
    case "mainquestcheck": return MainQuestCheck.Run(args[1], args[2], args[3..]);
    case "newworld": return NewWorld.Run(args[1..]);
    case "nwmap": return NewWorldMap.Run(args[1..]);
    case "placecheck": return PlaceCheck.Run(args[1], args[2..]);
    case "nightreedcheck": return NightReedCheck.Run(args[1], args[2], args[3..]);
    default: Console.Error.WriteLine("ArgoniaPlugin seed <out.esp> <plugins...> | blocktest <esp> <pexdir> <plugins...> | list <esp> <md> | survey <plugins...> | study|quests|cell|find ..."); return 2;
}
return 0;
