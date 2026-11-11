"""Community Shaders' height fog for the new world (tools/newworld/atmosphere_cs.py): the per-weather file names and
blocks, the ranges, the veil guard, the sky through the fog, the manifest row and the profile split."""
from __future__ import annotations

import json
import math

import pytest

from tools.newworld import atmosphere as A
from tools.newworld import atmosphere_cs as C

# ExponentialHeightFog::Settings' JSON names in Community Shaders 1.9.1 (NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE_WITH_DEFAULT)
SETTINGS = {"enabled", "useDynamicCubemaps", "startDistance", "fogHeight", "fogHeightFalloff", "fogDensity",
            "directionalInscatteringMultiplier", "directionalInscatteringAnisotropy", "inscatteringTint",
            "cubemapMipLevel", "sunlightAttenuationAmount", "respectVanillaFogFade", "disableVanillaFog",
            "fogInscatteringColor", "originalFogColorAmount", "volumetricFogEnabled", "volumetricGridPixelSize",
            "volumetricGridSizeZ", "volumetricFogDistance", "volumetricFogStartDistance",
            "volumetricFogNearFadeInDistance", "volumetricFogExtinctionScale", "volumetricFogScatteringDistribution",
            "volumetricFogAlbedo", "volumetricFogEmissive", "volumetricDirectionalScatteringIntensity",
            "volumetricShadowBias", "volumetricDepthDistributionScale", "volumetricSkyLightingIntensity",
            "volumetricHistoryWeight", "volumetricHistoryMissSampleCount", "volumetricSampleJitterMultiplier",
            "volumetricUpsampleJitterMultiplier", "volumetricLocalLightScatteringIntensity"}


def weather(formid, cls, kind, far, band="middle"):
    return {"formid": formid, "edid": f"ANW_W_{A.camel(cls)}_{band.capitalize()}_{kind.capitalize()}", "kind": kind,
            "class": cls, "band": band, "set": {"FogDistanceDayFar": far, "FogNearColor.Day": [143, 153, 118]}}


SPEC = {"weathers": [weather(0x80520 + k, "green-marsh", kind, far)
                     for k, (kind, far) in enumerate([("fair", 48000), ("cloudy", 60000), ("mist", 15000),
                                                      ("rain", 9000), ("storm", 15000), ("steam", 12750)])]
        + [weather(0x80568 + k, "highland", kind, far)
           for k, (kind, far) in enumerate([("fair", 80000), ("cloudy", 100000), ("mist", 25000),
                                            ("rain", 15000), ("storm", 25000), ("steam", 21250)])]}
FLOORS = {"build_id": "t", "floors": {"green-marsh": 210, "highland": 1220}}


def test_the_weather_file_is_named_as_community_shaders_keys_it():
    # Util::GetFormFileKey: "0x" + local form id (hex, upper, unpadded) + "~" + the defining plugin
    assert C.weather_file(0x080508) == "SKSE/Plugins/CommunityShaders/Weathers/0x80508~ArgoniaNewWorld.esm.json"
    assert C.weather_file(0x0B0805DA) == "SKSE/Plugins/CommunityShaders/Weathers/0x805DA~ArgoniaNewWorld.esm.json"


def test_generate_is_deterministic_and_reads_back_green():
    files = C.generate(SPEC, FLOORS)
    assert files == C.generate(SPEC, FLOORS)
    assert [f["path"] for f in files] == sorted(f["path"] for f in files)
    assert len(files) == 2 + len(SPEC["weathers"])
    rows = C.file_rows(SPEC, {f["path"]: f["text"] for f in files})
    assert all(ok for _, _, ok, _ in rows), [r for r in rows if not r[2]]


def test_each_block_is_the_features_own_names_and_ranges():
    for f in C.generate(SPEC, FLOORS)[2:]:
        doc = json.loads(f["text"])
        s = doc["featureSettings"]["ExponentialHeightFog"]
        assert s["__enabled"] is True and s["disableVanillaFog"] is True
        assert all(C.in_range(k, v) for k, v in s.items()), s
        assert s["Fog Height Falloff"] == 2.0 and s["Fog Height"] in (210.0, 1220.0)
        assert s["volumetricFogEnabled"] == (doc["_argonia"]["kind"] in ("fair", "cloudy", "steam"))


def test_ranges_reject_out_of_range_and_unknown_values():
    assert not C.in_range("Fog Density", 1.5)
    assert not C.in_range("Fog Height Falloff", 30.0)   # round 4's falloff, 15x the documented cap
    assert not C.in_range("Fog Density", True)
    assert not C.in_range("Made Up", 1.0)
    assert C.in_range("volumetricFogEnabled", False)


def shader_transmittance(s, cam_over_floor, length, dz):
    """ExponentialHeightFog.hlsli GetExponentialHeightFogInternal (no start distance, no volumetric): exp2(-integral)."""
    f, d = s["Fog Height Falloff"] * 1e-3, s["Fog Density"] * 1e-3
    origin = d * 2 ** (-f * max(cam_over_floor, 0))
    fall = f * dz
    li = (1 - 2 ** -fall) / fall if abs(fall) > 0.01 else 0.69314718056 - 0.24022650695 * fall
    return 2 ** -(origin * li * length)


def test_density_follows_the_weathers_own_visibility_class_and_kind():
    s = {w["edid"]: C.weather_settings(w, 0) for w in SPEC["weathers"]}
    gm, hl = "ANW_W_GreenMarsh_Middle_", "ANW_W_Highland_Middle_"
    # 90 % fogged along the floor at the record's day fog far, before the class and kind strengths
    base = dict(s[gm + "Mist"], **{"Fog Density": s[gm + "Mist"]["Fog Density"]
                                   / (C.CLASS_STRENGTH["green-marsh"] * C.KIND["mist"][0])})
    assert 1 - shader_transmittance(base, 0, 15000, 0) == pytest.approx(0.9, abs=2e-3)
    assert s[gm + "Mist"]["Fog Density"] > s[gm + "Fair"]["Fog Density"]
    assert s[gm + "Steam"]["Fog Density"] > s[gm + "Cloudy"]["Fog Density"]
    for k in ("Fair", "Mist", "Steam"):
        assert s[gm + k]["Fog Density"] > 2 * s[hl + k]["Fog Density"]


def test_sky_transmittance_is_the_shaders_line_integral():
    s = {"Fog Density": 0.3, "Fog Height Falloff": 2.0}
    e, L = math.radians(15), 400000.0   # a sky pixel: a ray to the far plane
    for over in (0.0, 500.0):
        want = shader_transmittance(s, over, L, L * math.sin(e))
        assert C.sky_transmittance(s, 15, above_floor=over) == pytest.approx(want, rel=1e-6)
    assert C.sky_transmittance(s, 90) > C.sky_transmittance(s, 15)
    assert C.sky_transmittance(s, 15, above_floor=500) > C.sky_transmittance(s, 15)


def test_the_global_overrides_are_the_features_settings_and_replace_the_play_rows():
    g = {f["path"]: json.loads(f["text"]) for f in C.global_files()}
    ehf = g["SKSE/Plugins/CommunityShaders/Overrides/Argonia_ExponentialHeightFog.json"]
    assert set(ehf) - {"_metadata"} <= SETTINGS
    assert ehf["enabled"] == 1 and ehf["disableVanillaFog"] == 1 and ehf["useDynamicCubemaps"] == 0
    assert ehf["inscatteringTint"][3] == 0 and ehf["fogInscatteringColor"][3] == 0
    vl = g["SKSE/Plugins/CommunityShaders/Overrides/Argonia_VolumetricLighting.json"]
    assert vl["ExteriorEnabled"] is True
    doc = json.loads(C.MANIFEST.read_text())
    play = {f["path"] for f in next(m for m in doc["mods"] if m["id"] == "community-shaders")["files"]}
    assert set(g) <= play   # the same paths, so the newworld row's copies win in its profile only


def test_the_manifest_row_is_newworld_only_and_whole():
    doc = json.loads(C.MANIFEST.read_text())
    ids = [m["id"] for m in doc["mods"]]
    row = C.manifest_row(doc)
    assert row["profile"] == "newworld" and row["source"]["tag"] == "v1.9.1" and row["pick"] == ["Shaders"]
    assert ids.index(C.ROW) > ids.index("community-shaders")
    cs = next(m for m in doc["mods"] if m["id"] == "community-shaders")
    assert cs["version"] == "1.9.1"
    cls = json.loads((A.SRC / "classes.json").read_text())
    names = list(cls["classes"])
    weathers = [f for f in row["files"] if "/Weathers/" in f["path"]]
    assert len(weathers) == 102
    for f in weathers:
        meta = json.loads(f["text"])["_argonia"]
        s = names.index(meta["class"]) * 3 + A.BANDS.index(meta["band"])
        formid = A.BASE["WTHR"] + s * 8 + cls["kinds"].index(meta["kind"])   # atmosphere.py's fixed ids
        assert f["path"] == C.weather_file(formid)
        assert meta["weather"] == f"ANW_W_{A.camel(meta['class'])}_{meta['band'].capitalize()}_{meta['kind'].capitalize()}"
        block = json.loads(f["text"])["featureSettings"]["ExponentialHeightFog"]
        assert all(C.in_range(k, v) for k, v in block.items())


def test_stack_rows_split_the_profiles(tmp_path):
    ini = C.ADDON_INI.replace("/", "\\").lower()
    ov = [f"{C.CS}/Overrides/{n}".replace("/", "\\").lower()
          for n in ("Argonia_ExponentialHeightFog.json", "Argonia_VolumetricLighting.json")]
    wf = {C.weather_file(w["formid"]).replace("/", "\\").lower(): [C.ROW, "h"] for w in SPEC["weathers"]}
    nw = {ini: [C.ROW, "h"], **{k: [C.ROW, "h"] for k in ov}, **wf}
    ar = {k: ["community-shaders", "h"] for k in ov}
    (tmp_path / "installed-NewWorld.json").write_text(json.dumps({"files": nw}))
    (tmp_path / "installed.json").write_text(json.dumps({"files": ar}))
    p = tmp_path / "MO2/mods" / C.ROW / C.ADDON_INI
    p.parent.mkdir(parents=True)
    p.write_text("[Info]\nVersion = 1-3-2\nUnreleased = True\n")
    rows = C.stack_rows(tmp_path, SPEC)
    assert all(ok for _, _, ok, _ in rows), [r for r in rows if not r[2]]
    (tmp_path / "installed.json").write_text(json.dumps({"files": {**ar, ini: [C.ROW, "h"]}}))
    assert not all(ok for _, _, ok, _ in C.stack_rows(tmp_path, SPEC))
