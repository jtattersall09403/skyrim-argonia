// Shrines: the vanilla temple shrine (tools/places/build.py plan_shrines says how and why): an activator of ours with the
// old base's model and TempleBlessingScript, its blessing spell (a copy of a vanilla blessing whose fortify effect is ours),
// the magic effect (a copy of vanilla's Fire and Forget fortify effect, on another actor value) and a message.
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Cache;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;
using Noggog;

static class Shrine
{
    static ILinkCache? cache;
    static ILinkCache Cache => cache ??= C.Cache(Write.Masters);

    static TranslatedString T(string s) => new(Language.English, s);

    public static void Build(Write.Ctx ctx, JsonElement rows)
    {
        var mod = ctx.Mod;
        foreach (var s in rows.EnumerateArray())
        {
            var mg = s.GetProperty("mgef");
            var m = (MagicEffect)Cache.Resolve<IMagicEffectGetter>(C.Fk(mg.GetProperty("from").GetString()!)).Duplicate(C.Fk(mg.GetProperty("fk").GetString()!));
            m.EditorID = mg.GetProperty("edid").GetString();
            m.Name = T(mg.GetProperty("name").GetString()!);
            m.Description = T(mg.GetProperty("description").GetString()!);
            m.Archetype.ActorValue = Enum.Parse<ActorValue>(mg.GetProperty("actor_value").GetString()!);
            mod.MagicEffects.Add(m);

            var sp = s.GetProperty("spell");
            var spell = (Spell)Cache.Resolve<ISpellGetter>(C.Fk(sp.GetProperty("from").GetString()!)).Duplicate(C.Fk(sp.GetProperty("fk").GetString()!));
            spell.EditorID = sp.GetProperty("edid").GetString();
            spell.Name = T(sp.GetProperty("name").GetString()!);
            var swap = C.Fk(sp.GetProperty("swap_effect").GetString()!);
            var swapped = 0;
            foreach (var e in spell.Effects.Where(e => e.BaseEffect.FormKey == swap))
            {
                e.BaseEffect.SetTo(m.FormKey);
                e.Data!.Magnitude = (float)sp.GetProperty("magnitude").GetDouble();
                e.Data.Duration = sp.GetProperty("duration").GetInt32();
                swapped++;
            }
            if (swapped != 1) throw new InvalidDataException($"{spell.EditorID}: {swapped} effects of {C.Key(swap)} in the vanilla blessing (want 1)");
            mod.Spells.Add(spell);

            var ms = s.GetProperty("message");
            mod.Messages.Add(new Message(C.Fk(ms.GetProperty("fk").GetString()!), C.Rel)
            {
                EditorID = ms.GetProperty("edid").GetString(), Description = T(ms.GetProperty("text").GetString()!), DisplayTime = 2u,
            });

            var ac = s.GetProperty("activator");
            var from = C.Fk(ac.GetProperty("model_from").GetString()!);
            var src = Cache.TryResolve<IMajorRecordGetter>(from, out var r) ? r
                : ctx.Fc.Plugin(from.ModKey.FileName).EnumerateMajorRecords().First(x => x.FormKey == from);
            var a = new Mutagen.Bethesda.Skyrim.Activator(C.Fk(ac.GetProperty("fk").GetString()!), C.Rel)
            {
                EditorID = ac.GetProperty("edid").GetString(), Name = T(ac.GetProperty("name").GetString()!),
                Model = (src as IModeledGetter)?.Model?.DeepCopy() ?? throw new InvalidDataException($"{C.Key(from)} has no model"),
                ObjectBounds = (src as IObjectBoundedGetter)?.ObjectBounds.DeepCopy() ?? new ObjectBounds(),
                VirtualMachineAdapter = C.Vmad(ac.GetProperty("scripts")),
            };
            ctx.Localize(a);
            mod.Activators.Add(a);
        }
    }
}
