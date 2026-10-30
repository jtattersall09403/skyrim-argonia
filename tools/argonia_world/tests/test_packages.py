"""L1/L2: the native AI packages (packages.py; PackageRecords.cs; NPC_ keywords and packages)."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from tools.argonia_world import packages as pk
from tools.argonia_world import skyrim_units as su

ROOT = Path(__file__).resolve().parents[3]
GEN = ROOT / "tools/ArgoniaGen/bin/Release/net10.0/ArgoniaGen.dll"
DATA = Path(os.environ.get("ARGONIA_GAME_ROOT", Path.home() / "games/skyrimse")) / "Data"
DOTNET = Path.home() / ".dotnet/dotnet"
REF = "000A00:Argonia.esm"


class FakeAlloc:
    def __init__(self):
        self.ids: dict[str, int] = {}

    def form_key(self, edid, record_type=None, entity_key=None):
        return f"{self.ids.setdefault(edid, 0x800 + len(self.ids)):06X}:Argonia.esm"


def test_shape_and_units():
    a = FakeAlloc()
    s = pk.sandbox(a, "ARG_Pack_A", "k", REF, 12.0, 8, 10)
    z = pk.sleep(a, "ARG_Pack_B", "k", REF, 3.0, 22, 8)
    assert s["type"] == z["type"] == "PACK"
    assert s["template"] == "01C254:Skyrim.esm" and z["template"] == "019717:Skyrim.esm"
    assert s["location"] == {"ref": REF, "radius": su.rounded(su.metres_to_units(12.0), 2)}
    assert z["location"]["radius"] == su.rounded(su.metres_to_units(3.0), 2)
    assert s["schedule"] == {"hour": 8, "minute": 0, "durationHours": 10, "dayOfWeek": "Any"}
    assert z["flags"] == ["WeaponsUnequipped"] and s["flags"] == []
    assert s["formKey"] != z["formKey"]
    with pytest.raises(ValueError):
        pk.sleep(a, "ARG_Pack_C", "k", REF, 3.0, 25, 8)


@pytest.mark.skipif(not (DATA / "Skyrim.esm").exists() or not GEN.exists() or not DOTNET.exists(),
                    reason="needs Skyrim.esm and the built ArgoniaGen")
def test_generate_and_read_back(tmp_path):
    a = FakeAlloc()
    sand = pk.sandbox(a, "ARG_Pack_Sand", "k", REF, 12.0, 8, 10)
    slp = pk.sleep(a, "ARG_Pack_Sleep", "k", REF, 3.0, 22, 8)
    kw = "013794:Skyrim.esm"  # a vanilla keyword (ActorTypeNPC)
    npc = {"type": "NPC_", "formKey": a.form_key("ARG_Npc_T"), "edid": "ARG_Npc_T", "name": "Test", "race": "013746:Skyrim.esm",
           "class": "0013BB:Skyrim.esm", "female": False, "level": 5, "healthOffset": 0, "aggression": "Unaggressive",
           "confidence": "Average", "height": 1.0, "weight": 50.0, "templateFlags": [],
           "keywords": [kw], "packages": [slp["formKey"], sand["formKey"]], "flags": ["Unique"]}
    doc = {"schema": 1, "mod": "Argonia.esm", "author": "t", "description": "t", "loadOrder": ["Skyrim.esm"],
           "records": [sand, slp, npc]}
    inp, out = tmp_path / "in.json", tmp_path / "Argonia.esm"
    inp.write_text(json.dumps(doc))
    env = dict(os.environ, PATH=f"{Path.home()}/.dotnet:{os.environ['PATH']}", DOTNET_gcServer="0", DOTNET_GCHeapHardLimit="0xC0000000")
    subprocess.run([str(DOTNET), str(GEN), "generate", "--in", str(inp), "--data", str(DATA), "--out", str(out)], check=True, env=env)
    dump = tmp_path / "dump.json"
    subprocess.run([str(DOTNET), str(GEN), "packages", "--data", str(tmp_path), "--plugin", "Argonia.esm", "--out", str(dump),
                    "--edids", "ARG_Pack_Sand,ARG_Pack_Sleep,ARG_Npc_T"], check=True, env=env)
    by = {x["edid"]: x for x in json.loads(dump.read_text())["brief"]}
    for rec in (sand, slp):
        x = by[rec["edid"]]
        assert x["template"] == rec["template"] and x["procedureTree"] == 0
        assert x["locRef"] == REF and x["radius"] == round(rec["location"]["radius"])
        assert x["hour"] == rec["schedule"]["hour"] and x["durationMinutes"] == rec["schedule"]["durationHours"] * 60
    assert by["ARG_Pack_Sleep"]["flags"] == "WeaponsUnequipped"
    assert 0 in by["ARG_Pack_Sand"]["inputs"] and 29 in by["ARG_Pack_Sand"]["inputs"] and 2 not in by["ARG_Pack_Sand"]["inputs"]
    n = by["ARG_Npc_T"]
    assert n["packages"] == [slp["formKey"], sand["formKey"]] and n["keywords"] == [kw] and "Unique" in n["flags"]
