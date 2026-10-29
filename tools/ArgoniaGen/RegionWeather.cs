// The region family's writers (2.W3; tools/argonia_world/regions/api.py writes their intermediate): REGN, CLMT,
// WTHR, IMGS, the WRLD override of ArgoniaWorld.esm's worldspace, and (LandWorld.cs) the REGN shells.
// As Generate.cs: no unit maths and no choices. Every number is ours and arrives resolved. From a weather's or the
// climate's template only references are taken: cloud texture paths, precipitation, the visual effect, sounds,
// sky statics, volumetric lighting, the aurora, the lens flare, the sun textures and the cloud layer count. They are
// read from the master (decision 0003: links to the player's files, never their values).
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;
using Noggog;

namespace ArgoniaGen;

static class RegionWriters
{
    const SkyrimRelease Rel = SkyrimRelease.SkyrimSE;
    static ISkyrimModDisposableGetter? master;
    static readonly string[] Tod = { "sunrise", "day", "sunset", "night" };

    public static void Write(SkyrimMod mod, JsonElement r, string data)
    {
        switch (S(r, "type"))
        {
            case "REGN": mod.Regions.Add(Region(r)); break;
            case "CLMT": mod.Climates.Add(Climate(r, data)); break;
            case "WTHR": mod.Weathers.Add(Weather(r, data)); break;
            case "IMGS": mod.ImageSpaces.Add(ImageSpace(r)); break;
            case "WRLD": mod.Worldspaces.Add(WorldOverride(r)); break;
            default: throw new InvalidDataException($"RegionWriters: {S(r, "type")}");
        }
    }

    static string S(JsonElement e, string k) => e.GetProperty(k).GetString() ?? throw new InvalidDataException($"{k} is null");
    static string? Os(JsonElement e, string k) => e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() : null;
    static float F(JsonElement e, string k) => e.GetProperty(k).GetSingle();
    static FormKey FK(string s) => FormKey.Factory(s);
    static IEnumerable<JsonElement> A(JsonElement e, string k) =>
        e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.Array ? v.EnumerateArray() : Enumerable.Empty<JsonElement>();
    static System.Drawing.Color C(JsonElement a) =>
        System.Drawing.Color.FromArgb(0, a[0].GetInt32(), a[1].GetInt32(), a[2].GetInt32());
    static T Flags<T>(JsonElement r, string k) where T : struct, Enum
    {
        long v = 0;
        foreach (var f in A(r, k)) v |= Convert.ToInt64(Enum.Parse<T>(f.GetString()!));
        return (T)Enum.ToObject(typeof(T), v);
    }

    static ISkyrimModDisposableGetter Master(string data, FormKey template)
    {
        if (template.ModKey.FileName != "Skyrim.esm") throw new InvalidDataException($"template {template}: Skyrim.esm only");
        return master ??= SkyrimMod.CreateFromBinaryOverlay(Path.Combine(data, "Skyrim.esm"), Rel);
    }

    // ---- REGN ----------------------------------------------------------------------------------------------
    public static Region Shell(JsonElement r, FormKey worldspace)
    {
        var g = new Region(FK(S(r, "formKey")), Rel) { EditorID = S(r, "edid") };
        g.Worldspace.SetTo(worldspace);
        return g;
    }

    static Region Region(JsonElement r)
    {
        var g = new Region(FK(S(r, "formKey")), Rel) { EditorID = S(r, "edid") };
        g.Worldspace.SetTo(FK(S(r, "worldspace")));
        if (r.GetProperty("border").GetBoolean()) g.MajorFlags |= Mutagen.Bethesda.Skyrim.Region.MajorFlag.BorderRegion;
        var prio = (byte)r.GetProperty("priority").GetInt32();
        foreach (var a in A(r, "areas"))
        {
            var ar = new RegionArea { EdgeFallOff = (uint)a.GetProperty("falloff").GetInt32(), RegionPointListData = new ExtendedList<P2Float>() };
            foreach (var p in a.GetProperty("points").EnumerateArray()) ar.RegionPointListData.Add(new P2Float(p[0].GetSingle(), p[1].GetSingle()));
            g.RegionAreas.Add(ar);
        }
        var objs = A(r, "objects").ToList();
        if (objs.Count > 0)
        {
            g.Objects = new RegionObjects { Priority = prio, Objects = new ExtendedList<RegionObject>() };
            foreach (var o in objs)
                g.Objects.Objects.Add(new RegionObject
                {
                    Object = new FormLink<IRegionTargetGetter>(FK(S(o, "object"))),
                    Density = F(o, "density"),
                    Clustering = (byte)o.GetProperty("clustering").GetInt32(),
                    MinSlope = (byte)o.GetProperty("minSlope").GetInt32(),
                    MaxSlope = (byte)o.GetProperty("maxSlope").GetInt32(),
                    Flags = Flags<RegionObject.Flag>(o, "flags"),
                    Radius = (ushort)o.GetProperty("radius").GetInt32(),
                    MinHeight = F(o, "minHeight"),
                    MaxHeight = F(o, "maxHeight"),
                    AngleVariance = new P3UInt16(0, 0, 0),
                    Unknown2 = new byte[6],  // RDOT entries are 52 bytes; the last six are unknown and zero
                });
        }
        var ws = A(r, "weathers").ToList();
        if (ws.Count > 0)
        {
            g.Weather = new Mutagen.Bethesda.Skyrim.RegionWeather { Priority = prio, Weathers = new ExtendedList<WeatherType>() };
            foreach (var w in ws) g.Weather.Weathers.Add(WType(w));
        }
        if (Os(r, "mapName") is { } name)
            g.Map = new RegionMap { Priority = prio, Name = new TranslatedString(Language.English, name) };
        return g;
    }

    static WeatherType WType(JsonElement w)
    {
        var t = new WeatherType { Chance = w.GetProperty("chance").GetInt32() };
        t.Weather.SetTo(FK(S(w, "weather")));
        if (Os(w, "global") is { } gl) t.Global.SetTo(FK(gl));
        return t;
    }

    // ---- CLMT ----------------------------------------------------------------------------------------------
    static Climate Climate(JsonElement r, string data)
    {
        var tk = FK(S(r, "template"));
        var tpl = Master(data, tk).Climates.TryGetValue(tk, out var t) ? t : throw new InvalidDataException($"no CLMT {tk}");
        static TimeOnly M(JsonElement r, string k) => TimeOnly.FromTimeSpan(TimeSpan.FromMinutes(r.GetProperty(k).GetInt32()));
        var c = new Climate(FK(S(r, "formKey")), Rel)
        {
            EditorID = S(r, "edid"),
            SunriseBegin = M(r, "sunriseBegin"), SunriseEnd = M(r, "sunriseEnd"),
            SunsetBegin = M(r, "sunsetBegin"), SunsetEnd = M(r, "sunsetEnd"),
            Volatility = (byte)r.GetProperty("volatility").GetInt32(),
            Moons = Flags<Climate.Moon>(r, "moons"),
            PhaseLength = (byte)r.GetProperty("phaseLength").GetInt32(),
            WeatherTypes = new ExtendedList<WeatherType>(A(r, "weathers").Select(WType)),
        };
        if (tpl.SunTexture is { } st) c.SunTexture = new(st.GivenPath);
        if (tpl.SunGlareTexture is { } sg) c.SunGlareTexture = new(sg.GivenPath);
        if (tpl.Model is { } m) c.Model = new Model { File = m.File.GivenPath };
        return c;
    }

    // ---- WTHR ----------------------------------------------------------------------------------------------
    static WeatherColor WC(JsonElement c) => new()
    {
        Sunrise = C(c.GetProperty("sunrise")), Day = C(c.GetProperty("day")),
        Sunset = C(c.GetProperty("sunset")), Night = C(c.GetProperty("night")),
    };

    static AmbientColors Amb(JsonElement a) => new()
    {
        DirectionalXPlus = C(a.GetProperty("xPlus")), DirectionalXMinus = C(a.GetProperty("xMinus")),
        DirectionalYPlus = C(a.GetProperty("yPlus")), DirectionalYMinus = C(a.GetProperty("yMinus")),
        DirectionalZPlus = C(a.GetProperty("zPlus")), DirectionalZMinus = C(a.GetProperty("zMinus")),
        Specular = C(a.GetProperty("specular")), Scale = F(a, "scale"),
    };

    static Weather Weather(JsonElement r, string data)
    {
        var tk = FK(S(r, "template"));
        var tpl = Master(data, tk).Weathers.TryGetValue(tk, out var t) ? t : throw new InvalidDataException($"no WTHR {tk}");
        var col = r.GetProperty("colours");
        var fog = r.GetProperty("fog");
        var img = r.GetProperty("images");
        var amb = r.GetProperty("ambient");
        var w = new Weather(FK(S(r, "formKey")), Rel)
        {
            EditorID = S(r, "edid"),
            SkyUpperColor = WC(col.GetProperty("skyUpper")), FogNearColor = WC(col.GetProperty("fogNear")),
            UnknownColor = WC(col.GetProperty("unknown")), AmbientColor = WC(col.GetProperty("ambient")),
            SunlightColor = WC(col.GetProperty("sunlight")), SunColor = WC(col.GetProperty("sun")),
            StarsColor = WC(col.GetProperty("stars")), SkyLowerColor = WC(col.GetProperty("skyLower")),
            HorizonColor = WC(col.GetProperty("horizon")), EffectLightingColor = WC(col.GetProperty("effectLighting")),
            CloudLodDiffuseColor = WC(col.GetProperty("cloudLodDiffuse")), CloudLodAmbientColor = WC(col.GetProperty("cloudLodAmbient")),
            FogFarColor = WC(col.GetProperty("fogFar")), SkyStaticsColor = WC(col.GetProperty("skyStatics")),
            WaterMultiplierColor = WC(col.GetProperty("waterMultiplier")), SunGlareColor = WC(col.GetProperty("sunGlare")),
            MoonGlareColor = WC(col.GetProperty("moonGlare")),
            FogDistanceDayNear = F(fog, "dayNear"), FogDistanceDayFar = F(fog, "dayFar"),
            FogDistanceNightNear = F(fog, "nightNear"), FogDistanceNightFar = F(fog, "nightFar"),
            FogDistanceDayPower = F(fog, "dayPower"), FogDistanceNightPower = F(fog, "nightPower"),
            FogDistanceDayMax = F(fog, "dayMax"), FogDistanceNightMax = F(fog, "nightMax"),
            WindSpeed = new Percent(F(r, "windSpeed")), TransDelta = F(r, "transDelta"),
            SunGlare = new Percent(F(r, "sunGlare")), SunDamage = new Percent(F(r, "sunDamage")),
            PrecipitationBeginFadeIn = new Percent(F(r, "precipitationFadeIn")),
            PrecipitationEndFadeOut = new Percent(F(r, "precipitationFadeOut")),
            ThunderLightningBeginFadeIn = new Percent(F(r, "thunderFadeIn")),
            ThunderLightningEndFadeOut = new Percent(F(r, "thunderFadeOut")),
            ThunderLightningFrequency = new Percent(F(r, "thunderFrequency")),
            Flags = Flags<Weather.Flag>(r, "flags"),
            LightningColor = C(r.GetProperty("lightning")),
            WindDirection = F(r, "windDirection"), WindDirectionRange = F(r, "windDirectionRange"),
            ImageSpaces = new WeatherImageSpaces(),
            DirectionalAmbientLightingColors = new WeatherAmbientColorSet
            {
                Sunrise = Amb(amb.GetProperty("sunrise")), Day = Amb(amb.GetProperty("day")),
                Sunset = Amb(amb.GetProperty("sunset")), Night = Amb(amb.GetProperty("night")),
            },
        };
        w.ImageSpaces.Sunrise.SetTo(FK(S(img, "sunrise")));
        w.ImageSpaces.Day.SetTo(FK(S(img, "day")));
        w.ImageSpaces.Sunset.SetTo(FK(S(img, "sunset")));
        w.ImageSpaces.Night.SetTo(FK(S(img, "night")));
        // references from the template, never its values
        for (var i = 0; i < w.CloudTextures.Length && i < tpl.CloudTextures.Count; i++)
            if (tpl.CloudTextures[i] is { } ct) w.CloudTextures[i] = new Mutagen.Bethesda.Plugins.Assets.AssetLink<Mutagen.Bethesda.Skyrim.Assets.SkyrimTextureAssetType>(ct.GivenPath);
        var cl = r.GetProperty("clouds");
        for (var i = 0; i < w.Clouds.Length && i < tpl.CloudTextures.Count; i++)
        {
            if (tpl.CloudTextures[i] is null) continue;
            w.Clouds[i] = new CloudLayer
            {
                Enabled = true, XSpeed = F(cl, "speed"), YSpeed = 0f, Colors = WC(cl.GetProperty("colours")),
                Alphas = new WeatherAlpha
                {
                    Sunrise = F(cl.GetProperty("alpha"), "sunrise"), Day = F(cl.GetProperty("alpha"), "day"),
                    Sunset = F(cl.GetProperty("alpha"), "sunset"), Night = F(cl.GetProperty("alpha"), "night"),
                },
            };
        }
        if (tpl.LNAM is { } lnam) w.LNAM = lnam.ToArray();  // the cloud layer count
        w.Precipitation.SetTo(tpl.Precipitation.FormKeyNullable);
        w.VisualEffect.SetTo(tpl.VisualEffect.FormKey);
        foreach (var s in tpl.Sounds) { var ws = new WeatherSound { Type = s.Type }; ws.Sound.SetTo(s.Sound.FormKey); w.Sounds.Add(ws); }
        w.SkyStatics.AddRange(tpl.SkyStatics.Select(x => (IFormLinkGetter<IStaticGetter>)new FormLink<IStaticGetter>(x.FormKey)));
        if (tpl.VolumetricLighting is { } vl)
        {
            w.VolumetricLighting = new WeatherVolumetricLighting();
            w.VolumetricLighting.Sunrise.SetTo(vl.Sunrise.FormKey);
            w.VolumetricLighting.Day.SetTo(vl.Day.FormKey);
            w.VolumetricLighting.Sunset.SetTo(vl.Sunset.FormKey);
            w.VolumetricLighting.Night.SetTo(vl.Night.FormKey);
        }
        if (tpl.Aurora is { } au) w.Aurora = new Model { File = au.File.GivenPath };
        w.SunGlareLensFlare.SetTo(tpl.SunGlareLensFlare.FormKeyNullable);
        return w;
    }

    // ---- IMGS ----------------------------------------------------------------------------------------------
    static ImageSpace ImageSpace(JsonElement r)
    {
        var h = r.GetProperty("hdr");
        var c = r.GetProperty("cinematic");
        var t = r.GetProperty("tint");
        return new ImageSpace(FK(S(r, "formKey")), Rel)
        {
            EditorID = S(r, "edid"),
            Hdr = new ImageSpaceHdr
            {
                EyeAdaptSpeed = F(h, "eyeAdaptSpeed"), EyeAdaptStrength = F(h, "eyeAdaptStrength"),
                BloomBlurRadius = F(h, "bloomBlurRadius"), BloomThreshold = F(h, "bloomThreshold"),
                BloomScale = F(h, "bloomScale"), ReceiveBloomThreshold = F(h, "receiveBloomThreshold"),
                White = F(h, "white"), SunlightScale = F(h, "sunlightScale"), SkyScale = F(h, "skyScale"),
            },
            Cinematic = new ImageSpaceCinematic { Saturation = F(c, "saturation"), Brightness = F(c, "brightness"), Contrast = F(c, "contrast") },
            Tint = new ImageSpaceTint { Amount = F(t, "amount"), Color = C(t.GetProperty("color")) },
            DepthOfField = new ImageSpaceDepthOfField(),
        };
    }

    // ---- WRLD override ---------------------------------------------------------------------------------------
    static Worldspace WorldOverride(JsonElement r)
    {
        var ws = LandWorld.World(r);  // the same mapping as the master's record, so only the links differ
        if (Os(r, "climate") is { } cl) ws.Climate.SetTo(FK(cl));
        if (Os(r, "music") is { } mu) ws.Music.SetTo(FK(mu));
        foreach (var p in A(r, "persistentRefs"))  // the gates and landings (routes/infra.py), placed by position
        {
            var a = p.GetProperty("pos").EnumerateArray().Select(x => x.GetSingle()).ToArray();
            var o = p.GetProperty("rot").EnumerateArray().Select(x => x.GetSingle()).ToArray();
            var refr = new PlacedObject(FK(S(p, "formKey")), Rel)
            {
                EditorID = Os(p, "edid"),
                Placement = new Placement { Position = new P3Float(a[0], a[1], a[2]), Rotation = new P3Float(o[0], o[1], o[2]) },
            };
            refr.Base.SetTo(FK(S(p, "base")));
            refr.MajorRecordFlagsRaw |= (int)PlacedObject.DefaultMajorFlag.Persistent;
            ws.TopCell!.Persistent.Add(refr);
        }
        return ws;
    }
}
