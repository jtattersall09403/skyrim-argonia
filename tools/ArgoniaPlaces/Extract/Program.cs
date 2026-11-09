// ArgoniaPlacesExtract: a place out of any plugin into a bundle (docs/design/place-studio.md, "Bundles").
//   extract <job.json>          the job extract.py writes: plugins, worldspace, cells or areas, doors to follow, out dir
//   survey <job.json> <out.tsv> per exterior cell of the worldspace: placed refs by kind and plugin (to measure a source)
//   types <Interface...>        the Mutagen getter's properties (a probe for whoever extends this tool)
switch (args.FirstOrDefault())
{
    case "extract": return Extractor.Run(Job.Load(args[1]));
    case "survey": return Extractor.Survey(Job.Load(args[1]), args[2]);
    case "types":
        foreach (var n in args[1..])
        {
            var t = typeof(Mutagen.Bethesda.Skyrim.ISkyrimModGetter).Assembly.GetType("Mutagen.Bethesda.Skyrim." + n);
            Console.WriteLine(t == null ? $"{n}: ?" : $"{n}: " + string.Join(" ",
                t.GetInterfaces().Append(t).SelectMany(i => i.GetProperties()).Select(p => $"{p.Name}:{p.PropertyType.Name}").Distinct()));
        }
        return 0;
    default:
        Console.Error.WriteLine("ArgoniaPlacesExtract extract <job.json> | survey <job.json> <out.tsv> | types <I...Getter>");
        return 2;
}
