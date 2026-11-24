// Our own bases (tools/places/own_bases.py says what and why): per place, a furniture and weathered statics with materials of ours, a water type of ours (a copy of a vanilla
// water as the load order's winner has it, with the plan's values set) and a placed water of ours (an activator with a
// vanilla model and bounds, carrying that water type), and a clear texture set with the copies of the mod statics whose
// alternate textures point at no texture set, those rows pointed at the clear set. The plan's refs already name these records.
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
            var kind = r.GetProperty("kind").GetString();
            if (kind == "txst")   // a texture set naming one diffuse (our clear set: an existing texture, no art of ours)
            {
                ctx.Mod.TextureSets.Add(new TextureSet(fk, C.Rel)
                {
                    EditorID = r.GetProperty("edid").GetString(),
                    Diffuse = r.GetProperty("diffuse").GetString()!.Replace('/', '\\').Replace("textures\\", ""),
                });
                continue;
            }
            if (kind == "static")   // a copy of a static whose alternate textures that resolve to nothing take `clear`
            {
                var src = C.Fk(r.GetProperty("copy").GetString()!);   // a mod's static, read from its own plugin
                var st = (Static)ctx.Fc.Plugin(src.ModKey.FileName).Statics.First(x => x.FormKey == src).Duplicate(fk);
                st.EditorID = r.GetProperty("edid").GetString();
                if (r.TryGetProperty("clear", out var cl))
                {
                    var clear = C.Fk(cl.GetString()!);
                    foreach (var a in st.Model?.AlternateTextures ?? new())
                        if (a.NewTexture.IsNull || !Cache.TryResolve<ITextureSetGetter>(a.NewTexture.FormKey, out _))
                            a.NewTexture.SetTo(clear);
                }
                if (r.TryGetProperty("material", out var mt))   // a weathered twin: the directional material, at its angle
                {
                    st.Material.SetTo(C.Fk(mt.GetString()!));
                    st.MaxAngle = r.GetProperty("angle").GetSingle();
                }
                ctx.Mod.Statics.Add(st);
                continue;
            }
            if (kind == "modelstatic")   // a plain static of a model-only resource pack's mesh (no record to copy)
            {
                var b = r.GetProperty("bounds").EnumerateArray().SelectMany(c => c.EnumerateArray()).Select(v => (short)Math.Round(v.GetDouble())).ToArray();
                ctx.Mod.Statics.Add(new Static(fk, C.Rel)
                {
                    EditorID = r.GetProperty("edid").GetString(),
                    Model = new Model { File = r.GetProperty("model").GetString()!.Replace('/', '\\').Replace("meshes\\", "") },
                    ObjectBounds = new ObjectBounds { First = new P3Int16(b[0], b[1], b[2]), Second = new P3Int16(b[3], b[4], b[5]) },
                });
                continue;
            }
            if (kind == "furniture")   // a copy of a mod's furniture (the hammock bed: its sleep markers kept)
            {
                var src = C.Fk(r.GetProperty("copy").GetString()!);
                var f = (Furniture)ctx.Fc.Plugin(src.ModKey.FileName).Furniture.First(x => x.FormKey == src).Duplicate(fk);
                f.EditorID = r.GetProperty("edid").GetString();
                ctx.Mod.Furniture.Add(f);
                continue;
            }
            if (kind == "material")   // a copy of a mod's directional material (by editor id) with members set
            {
                var src = r.GetProperty("copy").GetString()!.Split(':', 2);
                var m = (MaterialObject)ctx.Fc.Find(src[0], src[1]).Duplicate(fk);
                m.EditorID = r.GetProperty("edid").GetString();
                foreach (var f in r.GetProperty("set").EnumerateObject()) SetMember(m, f.Name, f.Value);
                ctx.Mod.MaterialObjects.Add(m);
                continue;
            }
            if (kind == "water")
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

    /// one member of a MATO from JSON: a colour or vector [x, y, z] (single-pass colour is three floats), or a number
    static void SetMember(MaterialObject m, string name, JsonElement val)
    {
        var p = typeof(MaterialObject).GetProperty(name) ?? throw new InvalidDataException($"MATO has no member {name}");
        var ty = Nullable.GetUnderlyingType(p.PropertyType) ?? p.PropertyType;
        object o = ty == typeof(P3Float) ? new P3Float(val[0].GetSingle(), val[1].GetSingle(), val[2].GetSingle())
            : ty == typeof(float) ? (object)val.GetSingle()
            : throw new InvalidDataException($"MATO member {name} is {ty.Name}");
        p.SetValue(m, o);
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
