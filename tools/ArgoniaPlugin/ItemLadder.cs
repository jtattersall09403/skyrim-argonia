// ItemLadder: the items ladder's records (docs/design/items.md; records.json from tools/newworld/world/smithing.py):
// every ladder item copied as ours (ForeignCopy), the overrides of its damage or rating and value to its tier's Skyrim
// base, the new MISC records an ingredient needs, and one COBJ per forge or tempering recipe (bench keyword and perk
// from Skyrim.esm by editor id). Shared by the places' build (tools/ArgoniaPlaces, which writes them into the places
// plugin until the world file carries them) and the world file's writer (NewWorld.cs).
//   var copies = ItemLadder.Write(mod, fc, name => id, recordsJsonPath);   // source key ("Plugin:XXXXXX") -> ours
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;

static class ItemLadder
{
    public static string PK(FormKey k) => $"{k.ModKey.FileName}:{k.ID:X6}";
    public static FormKey Src(string key) { var i = key.LastIndexOf(':'); return FormKey.Factory($"{key[(i + 1)..]}:{key[..i]}"); }

    /// Writes the records of `recordsJson` into `mod`; `newId(name)` gives a record of ours its id. Returns the copies
    /// (source key -> our key, and "new:<edid>" for a new item) and a line saying what was written.
    public static (SortedDictionary<string, string> copies, string line) Write(SkyrimMod mod, ForeignCopy fc, Func<string, uint> newId, string recordsJson)
    {
        var doc = JsonDocument.Parse(File.ReadAllText(recordsJson)).RootElement;
        var copies = new SortedDictionary<string, string>(StringComparer.Ordinal);
        FormKey Of(string key)
        {
            if (copies.TryGetValue(key, out var c)) return Src(c);
            var s = Src(key);
            var ours = fc.Get(s, s.ModKey.FileName);
            if (ours != s) copies[key] = PK(ours);
            return ours;
        }
        foreach (var it in doc.GetProperty("items").EnumerateArray()) Of(it.GetProperty("item").GetString()!);
        foreach (var o in doc.GetProperty("overrides").EnumerateArray())
        {
            var k = Of(o.GetProperty("item").GetString()!);
            var pw = o.GetProperty("power").GetDouble();
            var val = (uint)o.GetProperty("value").GetInt32();
            if (mod.Weapons.TryGetValue(k, out var w)) { w.BasicStats ??= new WeaponBasicStats(); w.BasicStats.Damage = (ushort)Math.Round(pw); w.BasicStats.Value = val; }
            else if (mod.Armors.TryGetValue(k, out var a)) { a.ArmorRating = (float)pw; a.Value = val; }
            else throw new InvalidDataException($"ladder override {o.GetProperty("item").GetString()}: {k} is no weapon or armour of ours");
        }
        foreach (var n in doc.GetProperty("new_items").EnumerateArray())
        {
            var edid = n.GetProperty("edid").GetString()!;
            var from = Src(n.GetProperty("model_from").GetString()!);
            var srcRec = fc.Plugin(from.ModKey.FileName).EnumerateMajorRecords().First(x => x.FormKey == from);
            var key = fc.CopyAs(srcRec, from.ModKey.FileName, newId("smithing-new:" + edid));
            var m = mod.MiscItems[key];
            m.EditorID = edid;
            m.Name = new TranslatedString(Language.English, n.GetProperty("name").GetString()!);
            m.Value = (uint)n.GetProperty("value").GetInt32();
            m.Weight = (float)n.GetProperty("weight").GetDouble();
            copies["new:" + edid] = PK(key);
        }
        var skyrim = new Dictionary<string, FormKey>();
        FormKey Vanilla(string edid) => skyrim.TryGetValue(edid, out var f) ? f : skyrim[edid] = fc.Find("Skyrim.esm", edid).FormKey;
        int made = 0;
        foreach (var r in doc.GetProperty("recipes").EnumerateArray())
        {
            var item = r.GetProperty("item").GetString()!;
            var rk = r.GetProperty("kind").GetString()!;
            var co = new ConstructibleObject(new FormKey(mod.ModKey, newId($"smithing:{rk}:{item}")), SkyrimRelease.SkyrimSE)
            { CreatedObjectCount = 1, Items = [] };
            co.EditorID = $"ANW_Smith_{(rk == "forge" ? "Forge" : "Temper")}_{item.Replace(' ', '_').Replace(':', '_').Replace('.', '_').Replace('-', '_')}";
            co.CreatedObject.SetTo(Of(item));
            co.WorkbenchKeyword.SetTo(Vanilla(r.GetProperty("bench").GetString()!));
            foreach (var ing in r.GetProperty("ingredients").EnumerateArray())
            {
                var key = ing[0].GetString()!;
                var ik = key.StartsWith("new:") ? Src(copies[key]) : Of(key);
                co.Items.Add(new ContainerEntry { Item = new ContainerItem { Item = new FormLink<IItemGetter>(ik), Count = ing[1].GetInt32() } });
            }
            foreach (var p in r.GetProperty("perks").EnumerateArray())
                co.Conditions.Add(new ConditionFloat { CompareOperator = CompareOperator.EqualTo, ComparisonValue = 1,
                    Data = new HasPerkConditionData { Perk = { Link = { FormKey = Vanilla(p.GetString()!) } } } });
            mod.ConstructibleObjects.Add(co);
            made++;
        }
        return (copies, $"{copies.Count} copies, {doc.GetProperty("overrides").GetArrayLength()} overrides, {made} recipes");
    }
}
