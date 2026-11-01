// The item family's writers (1.3 §c; tools/argonia_world/items_records.py writes their intermediate): KYWD (the
// weapon class keywords), WEAP, AMMO, ARMO, ARMA, CONT, BOOK, ALCH. A record with a `template` (a base-game
// record, "Skyrim.esm:<EditorID>") wears that record's look: its meshes, first-person model, armatures and sounds,
// read from the master in Data (1.12: an invented mesh path left the sword and its inventory icon invisible). As Generate.cs: no unit maths and no choices; every
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

    static readonly Dictionary<string, ISkyrimModDisposableGetter> masters = new(StringComparer.OrdinalIgnoreCase);
    static string data = "";

    // The base-game record a `template` names, by EditorID (the masters are read as overlays, once).
    static T Template<T>(JsonElement r, Func<ISkyrimModGetter, IEnumerable<T>> group) where T : IMajorRecordGetter
    {
        var t = S(r, "template");
        var i = t.IndexOf(':');
        var file = t[..i];
        if (!masters.TryGetValue(file, out var m))
            masters[file] = m = SkyrimMod.CreateFromBinaryOverlay(Path.Combine(data, file), Rel);
        return group(m).FirstOrDefault(x => x.EditorID == t[(i + 1)..])
            ?? throw new InvalidDataException($"{S(r, "edid")}: no {typeof(T).Name} {t}");
    }

    static bool Has(JsonElement r, string k) => r.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.String;

    public static void Write(SkyrimMod mod, JsonElement r, string dataDir)
    {
        data = dataDir;
        switch (S(r, "type"))
        {
            case "KYWD": mod.Keywords.Add(new Keyword(Key(r), Rel) { EditorID = S(r, "edid") }); break;
            case "WEAP": mod.Weapons.Add(Weapon(r)); break;
            case "AMMO": mod.Ammunitions.Add(Ammo(r)); break;
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
            Model = Has(r, "model") ? M(r, "model") : null,
            BasicStats = new WeaponBasicStats { Value = (uint)I(r, "value"), Weight = F(r, "weight"), Damage = r.TryGetProperty("damage", out var d) ? (ushort)d.GetInt32() : (ushort)0 },
            Data = new WeaponData
            {
                AnimationType = Enum.Parse<WeaponAnimationType>(S(r, "animation")),
                Speed = F(r, "speed"),
                Reach = F(r, "reach"),
            },
            Keywords = new ExtendedList<IFormLinkGetter<IKeywordGetter>>(),
        };
        foreach (var k in A(r, "keywords")) w.Keywords.Add(new FormLink<IKeywordGetter>(FK(k.GetString()!)));
        w.EquipmentType.SetTo(FK(S(r, "equipSlot")));  // none crashed the Container Menu (game-8)
        if (Has(r, "template"))
        {
            var t = Template(r, m => m.Weapons);
            w.Model = t.Model?.DeepCopy();
            w.FirstPersonModel.SetTo(t.FirstPersonModel.FormKeyNullable);  // the 1st-person static; none shows nothing in hand
            w.PickUpSound.SetTo(t.PickUpSound.FormKeyNullable);
            w.PutDownSound.SetTo(t.PutDownSound.FormKeyNullable);
            w.ImpactDataSet.SetTo(t.ImpactDataSet.FormKeyNullable);
            w.AttackSound.SetTo(t.AttackSound.FormKeyNullable);
            w.AttackSound2D.SetTo(t.AttackSound2D.FormKeyNullable);
            w.AttackLoopSound.SetTo(t.AttackLoopSound.FormKeyNullable);
            w.AttackFailSound.SetTo(t.AttackFailSound.FormKeyNullable);
            w.IdleSound.SetTo(t.IdleSound.FormKeyNullable);
            w.EquipSound.SetTo(t.EquipSound.FormKeyNullable);
            w.UnequipSound.SetTo(t.UnequipSound.FormKeyNullable);
            w.BlockBashImpact.SetTo(t.BlockBashImpact.FormKeyNullable);
            w.AlternateBlockMaterial.SetTo(t.AlternateBlockMaterial.FormKeyNullable);
            w.DetectionSoundLevel = t.DetectionSoundLevel;
            if (!r.TryGetProperty("damage", out _)) w.BasicStats!.Damage = t.BasicStats?.Damage ?? 0;  // the class's numbers are owed
        }
        if (w.Model is null) throw new InvalidDataException($"WEAP {w.EditorID}: no model");
        return w;
    }

    // An arrow: its base-game record's look, projectile, damage and flags; our name, weight and value.
    static Ammunition Ammo(JsonElement r)
    {
        var t = Template(r, m => m.Ammunitions);
        var a = new Ammunition(Key(r), Rel)
        {
            EditorID = S(r, "edid"),
            Name = T(r, "name"),
            Model = t.Model?.DeepCopy(),
            Value = (uint)I(r, "value"),
            Weight = F(r, "weight"),
            Damage = t.Damage,
            Flags = t.Flags,
        };
        a.Projectile.SetTo(t.Projectile.FormKey);
        a.PickUpSound.SetTo(t.PickUpSound.FormKeyNullable);
        a.PutDownSound.SetTo(t.PutDownSound.FormKeyNullable);
        return a;
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
                ArmorType = Has(r, "armorType") ? Enum.Parse<ArmorType>(S(r, "armorType")) : ArmorType.Clothing,
            },
        };
        foreach (var x in A(r, "armatures")) a.Armature.Add(new FormLink<IArmorAddonGetter>(FK(x.GetString()!)));
        if (Has(r, "template"))
        {
            var t = Template(r, m => m.Armors);
            foreach (var x in t.Armature) a.Armature.Add(new FormLink<IArmorAddonGetter>(x.FormKey));
            a.WorldModel = t.WorldModel is { } wm ? new GenderedItem<ArmorModel?>(wm.Male?.DeepCopy(), wm.Female?.DeepCopy()) : null;
            a.PickUpSound.SetTo(t.PickUpSound.FormKeyNullable);
            a.PutDownSound.SetTo(t.PutDownSound.FormKeyNullable);
            if (!Has(r, "armorType") && t.BodyTemplate is { } bt) a.BodyTemplate!.ArmorType = bt.ArmorType;  // Morrowind's medium: the engine has none
        }
        else if (!Has(r, "armorType")) throw new InvalidDataException($"ARMO {S(r, "edid")}: no armour type");
        return a;
    }

    static Container Container(JsonElement r)
    {
        var c = new Container(Key(r), Rel) { EditorID = S(r, "edid"), Name = T(r, "name"), Weight = F(r, "weight") };
        if (r.TryGetProperty("items", out var its))  // a merchant chest's stock (place_build._traders)
        {
            c.Items = new Noggog.ExtendedList<ContainerEntry>();
            foreach (var i in its.EnumerateArray())
                c.Items.Add(new ContainerEntry { Item = new ContainerItem { Item = new FormLink<IItemGetter>(FK(S(i, "item"))), Count = i.GetProperty("count").GetInt32() } });
        }
        return c;
    }

    static Book Book(JsonElement r)
    {
        var b = new Book(Key(r), Rel)
        {
            EditorID = S(r, "edid"),
            Name = T(r, "name"),
            BookText = T(r, "text"),
            Model = M(r, "model"),
            Value = (uint)I(r, "value"),
            Weight = F(r, "weight"),
        };
        // BookMenu draws the inventory art's 3D book: a BOOK with none crashes the menu on read (game-18).
        if (!r.TryGetProperty("inventoryArt", out _) || string.IsNullOrEmpty(b.Model?.File))
            throw new InvalidDataException($"BOOK {b.EditorID} has no inventory art or model: BookMenu crashes on it");
        b.InventoryArt.SetTo(FK(S(r, "inventoryArt")));
        return b;
    }

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
