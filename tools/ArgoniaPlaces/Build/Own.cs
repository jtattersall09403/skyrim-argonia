// Our own bases (tools/places/own_bases.py says what and why): per place, a water type of ours (a copy of a vanilla
// water as the load order's winner has it, with the plan's values set) and a placed water of ours (an activator with a
// vanilla model and bounds, carrying that water type). The plan's refs already name these records.
using System.Drawing;
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Cache;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Noggog;

static class Own
{
    static ILinkCache? cache;
    static ILinkCache Cache => cache ??= C.Cache(Write.Masters);

    public static void Build(Write.Ctx ctx, JsonElement rows)
    {
        foreach (var r in rows.EnumerateArray())
        {
            var fk = C.Fk(r.GetProperty("fk").GetString()!);
            if (r.GetProperty("kind").GetString() == "water")
            {
                var src = r.GetProperty("copy").GetString()!.Split(':', 2);
                var w = (Water)ctx.Fc.Find(src[0], src[1]).Duplicate(fk);
                w.EditorID = r.GetProperty("edid").GetString();
                foreach (var f in r.GetProperty("set").EnumerateObject()) Set(w, f.Name, f.Value);
                ctx.Mod.Waters.Add(w);
            }
            else
            {
                var from = C.Fk(r.GetProperty("model_from").GetString()!);
                var m = Cache.Resolve<IActivatorGetter>(from);
                ctx.Mod.Activators.Add(new Mutagen.Bethesda.Skyrim.Activator(fk, C.Rel)
                {
                    EditorID = r.GetProperty("edid").GetString(),
                    Model = m.Model?.DeepCopy() ?? throw new InvalidDataException($"{C.Key(from)} has no model"),
                    ObjectBounds = m.ObjectBounds.DeepCopy(),
                    WaterType = new FormLinkNullable<IWaterGetter>(C.Fk(r.GetProperty("water").GetString()!)),
                });
            }
        }
    }

    /// one member of a WATR from JSON: a colour [r, g, b], a vector [x, y, z], or a number
    static void Set(Water w, string name, JsonElement val)
    {
        var p = typeof(Water).GetProperty(name) ?? throw new InvalidDataException($"WATR has no member {name}");
        var t = Nullable.GetUnderlyingType(p.PropertyType) ?? p.PropertyType;
        static int I(JsonElement v) => (int)Math.Round(v.GetDouble());   // a whole-number member written as 0.0 still reads
        object o = t == typeof(Color) ? Color.FromArgb(0, I(val[0]), I(val[1]), I(val[2]))
            : t == typeof(P3Float) ? new P3Float(val[0].GetSingle(), val[1].GetSingle(), val[2].GetSingle())
            : t == typeof(byte) ? (object)(byte)I(val)
            : t == typeof(float) ? (object)val.GetSingle()
            : t == typeof(ushort) ? (object)(ushort)I(val)
            : t == typeof(uint) ? (object)(uint)I(val)
            : t == typeof(int) ? (object)I(val)
            : throw new InvalidDataException($"WATR member {name} is {t.Name}");
        p.SetValue(w, o);
    }
}
