"""L1: the sky's records (RegionWeather.cs) written from the world and read back from the bytes against each template
as the game resolves it (Tropical Skyrim.esp's restyle first; lane 1.15-r5-sky-2), the sky paint equal field by field
(lane 1.15-r5-sky): every WTHR draws its cloud layers where its template does and a clear sky keeps its template's
layer colours; every IMGS carries its template's HDR and its template is a vanilla image space of the time of day it
is used at. Skipped where ArgoniaGen is not built or there is no game data. The checks' own catches on synthetic
records run everywhere."""
import json
import os
import struct
import subprocess
from pathlib import Path

import pytest

from tools.argonia_world import checks, db
from tools.argonia_world.formids import Allocator
from tools.argonia_world.regions import api
from tools.argonia_world.terrain import esm

ROOT = Path(__file__).resolve().parents[4]
GEN = ROOT / "tools" / "ArgoniaGen" / "bin" / "Release" / "net10.0" / "ArgoniaGen"
GAME = Path(os.environ.get("ARGONIA_GAME_ROOT", Path.home() / "games/skyrimse")) / "Data"


def _rec(sig, fid, **subs):
    return esm.Record(sig, 0, fid, [(k, v) for k, v in subs.items()])


def _fid(key: str) -> int:
    return int(key.split(":")[0], 16)


def test_sky_clouds_catches_layers_drawn_and_cream_fill():
    tex = {"L0TX": b"Sky\\SkyrimCloudsFill.dds\0", "00TX": b"Sky\\Upper.dds\0"}
    tpl = _rec("WTHR", 1, **tex, NAM1=struct.pack("<I", 1), PNAM=b"\x11" * 16 * 29)
    bad = _rec("WTHR", 2, **tex, NAM1=struct.pack("<I", 0), PNAM=b"\xee" * 16 * 29)
    errs = checks.sky_clouds(bad, tpl, pleasant=True)
    assert any("layer 0 on" in e for e in errs) and any("layer 28 colours" in e for e in errs)
    good = _rec("WTHR", 3, **tex, NAM1=struct.pack("<I", 1), PNAM=b"\x11" * 16 * 29)
    assert checks.sky_clouds(good, tpl, pleasant=True) == []
    assert checks.sky_clouds(bad, tpl, pleasant=False) == ["cloud layer 0 on where the template has it off"]


def test_sky_paint_catches_a_pale_zenith_and_an_authored_cloud_tint():
    nam0 = bytearray(17 * 16)
    nam0[16 * 0 + 4:16 * 0 + 7] = bytes.fromhex("001E64")  # Tropical's SkyrimClearFF noon zenith
    tex = {"00TX": b"Sky\\Upper.dds\0"}
    tpl = _rec("WTHR", 1, **tex, NAM0=bytes(nam0), PNAM=b"\x11" * 16 * 29)
    pale = bytearray(nam0)
    pale[4:7] = bytes.fromhex("4B86C8")
    bad = _rec("WTHR", 2, **tex, NAM0=bytes(pale), PNAM=b"\xee" * 16 * 29)
    assert checks.sky_paint(bad, tpl) == ["sky upper at day 4B86C8 not the template's 001E64",
                                          "cloud layer 0 colours not the template's"]
    assert checks.sky_paint(tpl, tpl) == []


def test_sky_image_catches_our_hdr_and_a_dawn_template_at_noon():
    tpl = _rec("IMGS", 1, HNAM=struct.pack("<9f", 45, 7, 0.6, 3.5, 0.5, 1.02, 2.55, 0.3, 7))
    ours = _rec("IMGS", 2, HNAM=struct.pack("<9f", 1, 4, 0.7, 0.4, 0.6, 4.0, 1.6, 1.6, 0.3))
    assert checks.sky_image(ours, tpl, "day", "ISSkyrimClearDAWN_MA") == [
        "HDR not the template's", "used at day but its template ISSkyrimClearDAWN_MA is not a DAY image space"]
    assert checks.sky_image(tpl, tpl, "day", "ISSkyrimClearDAY_FF") == []
    assert checks.sky_image(tpl, tpl, "sunset", "ISSkyrimClearDAWN_FF") == []


@pytest.mark.skipif(not GEN.exists() or not (GAME / "Skyrim.esm").exists(),
                    reason="ArgoniaGen not built or no game data (the templates are Skyrim.esm's)")
def test_written_sky_follows_its_templates(tmp_path):
    world = db.open()
    alloc = Allocator(world=world, frozen=True)
    images, by_id = api._image_records(alloc, world)
    weathers = api._weather_records(alloc, world, by_id)
    order = ["Skyrim.esm", "Update.esm", "Tropical Skyrim.esp"]
    for m in order:
        (tmp_path / m).symlink_to(GAME / m)
    (tmp_path / "in.json").write_text(json.dumps({"schema": 1, "mod": "Argonia.esm", "author": "test",
                                                  "description": "test", "loadOrder": order,
                                                  "records": images + weathers}))
    out = tmp_path / "o" / "Argonia.esm"
    env = dict(os.environ, DOTNET_ROOT=str(Path.home() / ".dotnet"), DOTNET_gcServer="0")
    r = subprocess.run([str(GEN), "generate", "--in", str(tmp_path / "in.json"), "--data", str(tmp_path),
                        "--out", str(out)], capture_output=True, text=True, env=env, check=False)
    assert r.returncode == 0, r.stdout + r.stderr
    ours = {x.formid & 0xFFFFFF: x for x in esm.records(out.read_bytes()) if x.sig in ("WTHR", "IMGS")}
    # each template as the game resolves it: the load order's last plugin carrying it (Tropical Skyrim's restyle
    # first; lane 1.15-r5-sky-2), every one of ours named by the record
    plugin = {r["template"]: r["templatePlugin"] for r in images + weathers}
    assert plugin["00081A:Skyrim.esm"] == plugin["10A1EE:Skyrim.esm"] == "Tropical Skyrim.esp"
    van = {}
    for p in dict.fromkeys(plugin.values()):
        byid = {x.formid & 0xFFFFFF: x for x in esm.records((GAME / p).read_bytes()) if x.sig in ("WTHR", "IMGS")}
        van.update({_fid(k): byid[_fid(k)] for k, q in plugin.items() if q == p})
    edid = {k: (v.first("EDID") or b"").rstrip(b"\0").decode() for k, v in van.items()}
    errs = []
    for w in weathers:
        errs += [f"{w['edid']}: {e}" for e in checks.sky_clouds(ours[_fid(w["formKey"])], van[_fid(w["template"])],
                                                                "Pleasant" in w["flags"])]
        errs += [f"{w['edid']}: {e}" for e in checks.sky_paint(ours[_fid(w["formKey"])], van[_fid(w["template"])])]
        t = van[_fid(w["template"])]
        clear_tpl = bool(struct.unpack_from("<B", t.first("DATA"), 11)[0] & 1)  # DATA flags: Pleasant
        errs += [f"{w['edid']}: {e}" for e in checks.sky_fill_and_ambient(
            ours[_fid(w["formKey"])], t, clear_tpl, "Pleasant" in w["flags"])]
        for tod, key in w["images"].items():
            if tod in ("sunrise", "sunset") and key == w["images"]["day"]:
                continue  # one image all day (mist, overcast, rain, storm): judged as the day's
            i = next(x for x in images if x["formKey"] == key)
            errs += [f"{w['edid']} {i['edid']}: {e}" for e in checks.sky_image(
                ours[_fid(key)], van[_fid(i["template"])], tod, edid[_fid(i["template"])])]
    assert errs == []
