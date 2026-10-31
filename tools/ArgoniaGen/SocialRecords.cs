// FACT, FLST and MESG: a settlement's crime faction (tools/argonia_world/place_build.py) and a message of ours shown by a
// hook (tools/argonia_world/routes/infra.py: the closed road) -> Mutagen. No choices here: the flags, the crime
// values and the text arrive resolved.
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;

namespace ArgoniaGen;

static class SocialRecords
{
    const SkyrimRelease Rel = SkyrimRelease.SkyrimSE;

    static string S(JsonElement e, string k) => e.GetProperty(k).GetString() ?? throw new InvalidDataException($"{k} is null");
    static ushort U(JsonElement e, string k) => (ushort)e.GetProperty(k).GetInt32();
    static FormKey FK(string s) => FormKey.Factory(s);

    public static void Write(SkyrimMod mod, JsonElement r)
    {
        switch (S(r, "type"))
        {
            case "FACT": Faction(mod, r); break;
            case "MESG": Msg(mod, r); break;
            case "FLST": List(mod, r); break;
            default: throw new InvalidDataException($"SocialRecords: {S(r, "type")}");
        }
    }

    static void Faction(SkyrimMod mod, JsonElement r)
    {
        var f = new Faction(FK(S(r, "formKey")), Rel)
        {
            EditorID = S(r, "edid"),
            Name = new TranslatedString(Language.English, S(r, "name")),
        };
        foreach (var fl in r.GetProperty("flags").EnumerateArray())
            f.Flags |= Enum.Parse<Faction.FactionFlag>(fl.GetString()!);
        if (r.TryGetProperty("crime", out var c))
            f.CrimeValues = new CrimeValues
            {
                Arrest = c.GetProperty("arrest").GetBoolean(),
                AttackOnSight = c.GetProperty("attackOnSight").GetBoolean(),
                Murder = U(c, "murder"),
                Assault = U(c, "assault"),
                Trespass = U(c, "trespass"),
                Pickpocket = U(c, "pickpocket"),
                StealMult = c.GetProperty("stealMult").GetSingle(),
                Escape = U(c, "escape"),
                Werewolf = U(c, "werewolf"),
            };
        foreach (var k in r.GetProperty("ranks").EnumerateArray())
            f.Ranks.Add(new Rank
            {
                Number = (uint)k.GetProperty("number").GetInt32(),
                Title = new Mutagen.Bethesda.Plugins.Records.GenderedItem<TranslatedString?>(new TranslatedString(Language.English, S(k, "title")), null),
            });
        if (r.TryGetProperty("vendor", out var v))  // a trader's vendor data (place_build._traders)
        {
            f.VendorValues = new VendorValues
            {
                StartHour = (ushort)v.GetProperty("startHour").GetInt32(),
                EndHour = (ushort)v.GetProperty("endHour").GetInt32(),
                Radius = (ushort)v.GetProperty("radius").GetInt32(),
                OnlyBuysStolenItems = v.GetProperty("onlyBuysStolen").GetBoolean(),
                NotSellBuy = v.GetProperty("notSellBuy").GetBoolean(),
            };
            f.VendorBuySellList.SetTo(FK(S(v, "buySellList")));
            f.MerchantContainer.SetTo(FK(S(v, "chest")));
            var near = new LocationTarget();  // "near reference": the trader's own placed actor
            near.Link.SetTo(FK(S(v, "nearRef")));
            f.VendorLocation = new LocationTargetRadius { Target = near, Radius = (uint)v.GetProperty("radius").GetInt32() };
        }
        mod.Factions.Add(f);
    }

    static void List(SkyrimMod mod, JsonElement r)
    {
        var l = new FormList(FK(S(r, "formKey")), Rel) { EditorID = S(r, "edid") };
        foreach (var x in r.GetProperty("items").EnumerateArray())
            l.Items.Add(new FormLink<ISkyrimMajorRecordGetter>(FK(x.GetString()!)));
        mod.FormLists.Add(l);
    }

    static void Msg(SkyrimMod mod, JsonElement r)
    {
        var m = new Mutagen.Bethesda.Skyrim.Message(FK(S(r, "formKey")), Rel)
        {
            EditorID = S(r, "edid"),
            Description = new TranslatedString(Language.English, S(r, "text")),
            Flags = r.GetProperty("messageBox").GetBoolean() ? Mutagen.Bethesda.Skyrim.Message.Flag.MessageBox : 0,
        };
        mod.Messages.Add(m);
    }
}
