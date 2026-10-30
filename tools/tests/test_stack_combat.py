"""The combat sets A, B and B2 (stack.py combat; docs/research/2026-10-29/combat-mod-28567.md §5): which rows each
lays, and the plugin values stage writes into a mod's plugin (B2's crits global, the roll key)."""
import json
import struct
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "infra" / "gpu-box"))
import stack  # noqa: E402


def sub(t, v):
    return t + struct.pack("<H", len(v)) + v


def rec(t, fid, body):
    return t + struct.pack("<IIIII", len(body), 0, fid, 0, 0) + body


def grup(label, recs):
    inner = b"".join(recs)
    return b"GRUP" + struct.pack("<I", 24 + len(inner)) + label + b"\0" * 12 + inner


def wstr(s):
    return struct.pack("<H", len(s)) + s.encode()


def plugin():
    glob = rec(b"GLOB", 0x800, sub(b"EDID", b"BB_Poise_VarCritsAllowed\0") + sub(b"FNAM", b"f")
               + sub(b"FLTV", struct.pack("<f", 1.0)))
    vmad = struct.pack("<hhH", 5, 2, 1) + wstr("BB_RollCameraQuestScript") + b"\0" + struct.pack("<H", 0)
    qust = rec(b"QUST", 0x801, sub(b"EDID", b"BB_RollCameraQuest\0") + sub(b"VMAD", vmad) + sub(b"DNAM", b"\x11\0" + b"\0" * 10))
    return rec(b"TES4", 0, sub(b"HEDR", b"\0" * 12)) + grup(b"GLOB", [glob]) + grup(b"QUST", [qust])


def fields(buf):
    out, i = {}, 0
    while i < len(buf):
        t, n = buf[i:i + 4], struct.unpack_from("<I", buf, i + 4)[0]
        if t == b"GRUP":
            assert i + n <= len(buf)
            out.update(fields(buf[i + 24:i + n]))
            i += n
            continue
        body, j = buf[i + 24:i + 24 + n], 0
        while j < len(body):
            st, sn = body[j:j + 4], struct.unpack_from("<H", body, j + 4)[0]
            out[(t, st)] = body[j + 6:j + 6 + sn]
            j += 6 + sn
        assert j == len(body)
        i += 24 + n
    return out


def test_b2_values_are_written_and_sizes_follow():
    out = stack.edit_plugin(plugin(), {"BB_Poise_VarCritsAllowed": 0}, "BB_RollCameraQuest",
                            "BB_RollCameraQuestScript", {"RollKey": 0})
    f = fields(out)
    assert struct.unpack("<f", f[(b"GLOB", b"FLTV")])[0] == 0.0
    assert f[(b"QUST", b"VMAD")].endswith(wstr("RollKey") + bytes([3, 1]) + struct.pack("<i", 0))
    assert stack.edit_plugin(out, {"BB_Poise_VarCritsAllowed": 0}, "BB_RollCameraQuest",
                             "BB_RollCameraQuestScript", {"RollKey": 0}) == out  # a restage changes nothing more


def test_an_edit_the_plugin_lacks_is_refused():
    with pytest.raises(SystemExit):
        stack.edit_plugin(plugin(), {"BB_Poise_NoSuchGlobal": 0})


def test_each_combat_set_lays_its_rows():
    doc = stack.manifest()
    ids = {k: {m["id"] for m in stack.chosen(doc, {"combat": v}, False) if m["group"] == "combat"}
           for k, v in stack.COMBAT.items()}
    assert "dark-souls-combat" not in ids["A"] and "modern-stagger-lock" in ids["A"]
    assert "dark-souls-combat" in ids["B"] and not ids["B"] & {"tk-dodge-re", "elden-parry", "rim-parry", "modern-stagger-lock"}
    # the DSC sets' behaviour engine: Nemesis runs in place of Pandora for B and B2 only (game-11)
    assert "nemesis" in ids["B"] and "nemesis" in ids["B2"] and "nemesis" not in ids["A"]
    assert ids["B2"] == ids["A"] - {"modern-stagger-lock"} | {"dark-souls-combat", "nemesis"}


def test_b2_and_b_values_and_the_rips_drop_are_data():
    dsc = next(m for m in stack.manifest()["mods"] if m["id"] == "dark-souls-combat")
    by_set = {e["set"]: e for e in dsc["plugin_values"]}
    assert by_set["dsc-b2"]["glob"]["BB_Poise_VarCritsAllowed"] == 0
    assert by_set["dsc-b2"]["quest_script_int"]["values"]["RollKey"] == 0
    assert "sound/fx/bb_dsc*" in dsc["drop"]


def test_an_unknown_set_is_refused():
    with pytest.raises(SystemExit):
        stack.picks(stack.manifest(), {"combat": "dsc-c"})


def test_masters_lays_only_the_staged_sets_plugins(tmp_path, monkeypatch):
    """game-10's gate red: combat B staged Dark Souls Combat.esp into the profile the gate reads while the build VM's
    Data lacked it. masters lays the staged set's plugins into Data and takes out those an earlier set laid."""
    st, game = tmp_path / "stack", tmp_path / "game"
    (game / "Data").mkdir(parents=True)
    (st / "staged").mkdir(parents=True)
    monkeypatch.setattr(stack, "STACK", st)
    monkeypatch.setattr(stack, "MO2", st / "MO2")
    monkeypatch.setenv("ARGONIA_GAME_ROOT", str(game))

    def stage(mods):
        import shutil
        shutil.rmtree(st / "MO2", ignore_errors=True)
        files = {}
        for mod, plugs in mods.items():
            (st / "MO2" / "mods" / mod).mkdir(parents=True)
            for p in plugs:
                (st / "MO2" / "mods" / mod / p).write_bytes(b"TES4")
            files[f"meshes\\{mod}\\a.nif"] = [mod, "h"]
        (st / "installed.json").write_text(json.dumps({"plugins": [p for ps in mods.values() for p in ps], "files": files}))

    data = game / "Data"
    stage({"precision": ["Precision.esp"], "dark-souls-combat": ["Dark Souls Combat.esp"]})  # set B
    stack.cmd_masters(None)
    assert (data / "Dark Souls Combat.esp").exists() and (data / "argonia-mesh-lists" / "dark-souls-combat.txt").exists()
    stage({"precision": ["Precision.esp"]})  # back to A
    stack.cmd_masters(None)
    assert not (data / "Dark Souls Combat.esp").exists()
    assert not (data / "argonia-mesh-lists" / "dark-souls-combat.txt").exists()
    assert (data / "Precision.esp").exists()
    assert (data / "argonia-plugins.txt").read_text().split() == ["Precision.esp"]


def test_install_syncs_masters_after_the_stage():
    """Every install (combat A, B, B2 included) lays the staged set's plugins into the build VM's Data."""
    import inspect
    src = inspect.getsource(stack.cmd_install)
    assert src.index("cmd_stage(a)") < src.index("cmd_masters(a)") < src.index("cmd_push(a)")


def test_stage_prunes_a_tool_of_another_set():
    """game-12: back to A after B2, the staged MO2/tools still held Nemesis, push sent it, and A's Pandora step ran
    Nemesis (hung). The stage takes out every tool folder whose row is not in the staged set."""
    import inspect
    src = inspect.getsource(stack.cmd_stage)
    loop = src.index("for d in list(tools.iterdir())")
    assert "d.name not in ids" in src[loop:loop + 200] and "shutil.rmtree(d)" in src[loop:loop + 200]
    assert loop < src.index("for m in rows:")
