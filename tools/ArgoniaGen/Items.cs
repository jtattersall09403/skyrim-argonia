// The item family's writers (1.3 §c; tools/argonia_world/items_records.py writes their intermediate): KYWD (the
// weapon class keywords), WEAP, ARMO, ARMA, CONT, BOOK, ALCH. As Generate.cs: no unit maths and no choices; every
// number, mask, path and link arrives resolved. Combat numbers (damage, armour rating) are not written: they are
// ArgoniaCore's, from the sets' scales.
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;
using Noggog;

namespace ArgoniaGen;

static class ItemWriters
{
    const SkyrimRelease Rel = SkyrimRelease.SkyrimSE;

    public static void Write(SkyrimMod mod, JsonElement r)
    {
        switch (S(r, "type"))
        {
            case "KYWD": mod.Keywords.Add(new Keyword(Key(r), Rel) { EditorID = S(r, "edid") }); break;
            case "WEAP": mod.Weapons.Add(Weapon(r)); break;
            case "ARMA": mod.ArmorAddons.Add(Addon(r)); break;
            case "ARMO": mod.Armors.Add(Armour(r)); break;
            case "CONT": mod.Containers.Add(Container(r)); break;
            case "BOOK": mod.Books.Add(Book(r)); break;
            case "MISC": mod.MiscItems.Add(new MiscItem(Key(r), Rel) { EditorID = S(r, "edid"), Name = T(r, "name"), Model = M(r, "model"), Value = (uint)I(r, "value"), Weight = F(r, "weight") }); break;
            case "ALCH": mod.Ingestibles.Add(Potion(r)); break;
            default: throw new InvalidDataException($"ItemWriters: {S(r, "type")}");
        }
    }

    static string S(JsonElement e, string k) => e.GetProperty(k).GetString() ?? throw new InvalidDataException($"{k} is null");
    static float F(JsonElement e, string k) => e.GetProperty(k).GetSingle();
    static int I(JsonElement e, string k) => e.GetProperty(k).GetInt32();
    static FormKey FK(string s) => FormKey.Factory(s);
    static FormKey Key(JsonElement r) => FK(S(r, "formKey"));
    static IEnumerable<JsonElement> A(JsonElement e, string k) =>
        e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.Array ? v.EnumerateArray() : Enumerable.Empty<JsonElement>();
    static TranslatedString T(JsonElement r, string k) => new TranslatedString(Language.English, S(r, k));
    static Model M(JsonElement r, string k) => new Model { File = S(r, k) };

    static Weapon Weapon(JsonElement r)
    {
        var w = new Weapon(Key(r), Rel)
        {
            EditorID = S(r, "edid"),
            Name = T(r, "name"),
            Model = M(r, "model"),
            BasicStats = new WeaponBasicStats { Value = (uint)I(r, "value"), Weight = F(r, "weight"), Damage = (ushort)I(r, "damage") },
            Data = new WeaponData
            {
                AnimationType = Enum.Parse<WeaponAnimationType>(S(r, "animation")),
                Speed = F(r, "speed"),
                Reach = F(r, "reach"),
            },
            Keywords = new ExtendedList<IFormLinkGetter<IKeywordGetter>>(),
        };
        foreach (var k in A(r, "keywords")) w.Keywords.Add(new FormLink<IKeywordGetter>(FK(k.GetString()!)));
        return w;
    }

    static ArmorAddon Addon(JsonElement r)
    {
        var a = new ArmorAddon(Key(r), Rel)
        {
            EditorID = S(r, "edid"),
            BodyTemplate = new BodyTemplate { FirstPersonFlags = (BipedObjectFlag)I(r, "biped") },
            WorldModel = new GenderedItem<Model?>(M(r, "maleModel"), null),
        };
        a.Race.SetTo(FK(S(r, "race")));
        return a;
    }

    static Armor Armour(JsonElement r)
    {
        var a = new Armor(Key(r), Rel)
        {
            EditorID = S(r, "edid"),
            Name = T(r, "name"),
            Value = (uint)I(r, "value"),
            Weight = F(r, "weight"),
            BodyTemplate = new BodyTemplate
            {
                FirstPersonFlags = (BipedObjectFlag)I(r, "biped"),
                ArmorType = Enum.Parse<ArmorType>(S(r, "armorType")),
            },
        };
        foreach (var x in A(r, "armatures")) a.Armature.Add(new FormLink<IArmorAddonGetter>(FK(x.GetString()!)));
        return a;
    }

    static Container Container(JsonElement r) => new Container(Key(r), Rel)
    {
        EditorID = S(r, "edid"),
        Name = T(r, "name"),
        Weight = F(r, "weight"),
    };

    static Book Book(JsonElement r) => new Book(Key(r), Rel)
    {
        EditorID = S(r, "edid"),
        Name = T(r, "name"),
        BookText = T(r, "text"),
        Model = M(r, "model"),
        Value = (uint)I(r, "value"),
        Weight = F(r, "weight"),
    };

    static Ingestible Potion(JsonElement r)
    {
        var p = new Ingestible(Key(r), Rel)
        {
            EditorID = S(r, "edid"),
            Name = T(r, "name"),
            Model = M(r, "model"),
            Value = (uint)I(r, "value"),
            Weight = F(r, "weight"),
        };
        foreach (var e in A(r, "effects"))
        {
            var eff = new Effect { Data = new EffectData { Magnitude = F(e, "magnitude"), Area = I(e, "area"), Duration = I(e, "duration") } };
            eff.BaseEffect.SetTo(FK(S(e, "effect")));
            p.Effects.Add(eff);
        }
        return p;
    }
}
