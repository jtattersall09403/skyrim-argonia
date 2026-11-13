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
    case "waterblend": return args[1] == "flows" ? WaterBlend.Flows(args[2]) : WaterBlend.Study(args[2]);
    case "waterstudy": return WaterStudy.Run(args[1..]);
    case "survey":Survey.Run(args[1..]); break;
    case "gives": GiveStudy.Run(args[1..]); break;
    case "spells": return SpellStudy.Run(args[1..]);
    case "seat": Seat.Run(args[1..]); break;
    case "cleancheck": return CleanUp.Check(args[1], args[2..]);
    case "mapprobe": MapFix.Probe(args[1..]); break;
    case "musicprobe": Music.Probe(args[1..]); break;
    case "blockstudy": BlockTestStudy.Run(args[1]); break;
    case "surface": Surface.Run(args[1..]); break;
    case "asset": File.WriteAllBytes(args[2], new Surface.Assets(args[3..]).Read(args[1]) ?? throw new FileNotFoundException(args[1])); break; // read only, to a scratch path
    case "inspect": Inspect.Run(args[1], args[2..]); break;
    case "quests": Study2.Run(args[1], args[2..]); break;
    case "newworld": return NewWorld.Run(args[1..]);
    case "formids": return FormIds.Run(args[1..]);
    case "atmos": return NewWorldAtmosphere.Run(args[1..]);
    case "sound": return SoundStudy.Run(args[1..]);
    case "nwmap": return NewWorldMap.Run(args[1..]);
    case "placecheck": return PlaceCheck.Run(args[1], args[2..]);
    case "questcheck": return args.Length > 1 && args[1] == "--selftest" ? QuestCheck.SelfTest() : QuestCheck.Run(args[1], args[2], args[3..]);
    case "questform": return QuestFormTest.Run(args[1..]);
    case "questform-read": return QuestFormRead.Run(args[1], args[2], args[3..]);
    default: Console.Error.WriteLine("ArgoniaPlugin seed <out.esp> <plugins...> | list <esp> <md> | survey <plugins...> | study|quests|cell|find ..."); return 2;
}
return 0;
