"""The band copies' loot check (tools/newworld/ecology/loot_check.py): a copy is searchable as its source is."""
import struct

from tools.newworld.ecology import loot_check as L


def npc(flags=0, tflags=0, **subs):
    acbs = struct.pack("<IhhhhhhHhH", flags, 0, 0, 1, 0, 0, 100, tflags, 0, 0)
    return {"ACBS": [acbs], **{k: [v] for k, v in subs.items()}}


def test_a_copy_like_its_source_is_clean_and_band_fields_may_differ():
    src = npc(0x18, INAM=b"\x01\0\0\0", RNAM=b"\x02\0\0\0")
    cp = npc(0x08, INAM=b"\x01\0\0\0", RNAM=b"\x02\0\0\0", SPLO=b"\x09\0\0\0", DNAM=b"x")
    assert L.check({"X": src, "ANW_Eco_X_D2": cp}) == ([], 1)


def test_summonable_a_lost_death_item_and_a_new_script_fail():
    src = npc(0x4018, INAM=b"\x01\0\0\0")
    faults, _ = L.check({"X": src, "ANW_Eco_X_D2": npc(0x4008, VMAD=b"s")})
    assert any("summonable" in f for f in faults) and any("INAM" in f for f in faults) and any("script" in f for f in faults)
