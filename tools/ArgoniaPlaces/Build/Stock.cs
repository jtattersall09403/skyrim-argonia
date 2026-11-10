// Stock: the containers and outfits a place's stock rows make (tools/places/stock/plan.py decides every item; the
// contract is docs/design/place-studio.md, Stock). A container of ours is a copy of the ref's source base holding
// exactly the plan's items (set dressing kept from the source, the stock row's items and gold), never respawning;
// an outfit of ours is the worn rows plus the base outfit's set dressing. Nothing levelled: every item is fixed.
using System.Text.Json;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using Noggog;

static class Stock
{
    public static ContainerEntry Entry(Write.Ctx ctx, JsonElement e) => new()
    {
        Item = new ContainerItem { Item = new FormLink<IItemGetter>(ctx.Link(e.GetProperty("item").GetString()!)), Count = e.GetProperty("count").GetInt32() },
    };

    public static void Build(Write.Ctx ctx, JsonElement stock)
    {
        foreach (var c in stock.GetProperty("containers").EnumerateArray())
        {
            var from = ctx.Link(c.GetProperty("from").GetString()!);
            IContainerGetter src = from.ModKey == ctx.Mod.ModKey
                ? (ctx.Fc.Copies.TryGetValue(from, out var own) && own is IContainerGetter oc ? oc : throw new InvalidDataException($"stock: {C.Key(from)} is not a container"))
                : People.Cache.Resolve<IContainerGetter>(from);
            var o = (Container)src.Duplicate(C.Fk(c.GetProperty("fk").GetString()!));
            o.EditorID = c.GetProperty("edid").GetString();
            o.Flags &= ~Container.Flag.Respawns;  // an authored container never respawns
            o.Items = new ExtendedList<ContainerEntry>(c.GetProperty("items").EnumerateArray().Select(e => Entry(ctx, e)));
            ctx.Localize(o);
            ctx.Mod.Containers.Add(o);
        }
        foreach (var f in stock.GetProperty("outfits").EnumerateArray())
        {
            var ot = new Outfit(C.Fk(f.GetProperty("fk").GetString()!), C.Rel) { EditorID = f.GetProperty("edid").GetString() };
            ot.Items = new ExtendedList<IFormLinkGetter<IOutfitTargetGetter>>(
                f.GetProperty("items").EnumerateArray().Select(i => (IFormLinkGetter<IOutfitTargetGetter>)new FormLink<IOutfitTargetGetter>(ctx.Link(i.GetString()!))));
            ctx.Mod.Outfits.Add(ot);
        }
    }
}
