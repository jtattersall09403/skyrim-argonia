import importlib.util
import pathlib

spec = importlib.util.spec_from_file_location("controlmap", pathlib.Path(__file__).parents[2] / "infra/gpu-box/controlmap.py")
cm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cm)

VANILLA = (
    "// Main Gameplay\t\t\n"
    "Left Attack/Block\t0xff\t0x1\t0x0100\t1\t1\t1\t0x841\n"
    "Right Attack/Block\t0xff\t0x0\t0x0200,0x000a\t1\t1\t1\t0x841\n"
    "Activate\t0x12\t0xff\t0x1000\t1\t1\t1\t0x804\n"
    "Ready Weapon\t0x13\t0xff\t0x4000\t1\t1\t1\t0x840\n"
    "Tween Menu\t0x0f\t0xff\t0x0004,0x0008\t1\t1\t1\t0x908\n"
    "Jump\t\t0x39\t0xff\t0x8000\t1\t1\t1\t0xC01\n"
    "Sprint\t\t0x38\t0xff\t0x2000\t1\t1\t1\t0x801\n"
    "Shout\t0x2c\t0xff\t0x0009\t1\t1\t1\t0x840\n"
    "Sneak\t0x1d\t0xff\t0x0040\t1\t1\t1\t0x881\n"
    "Run\t\t0x2a\t0xff\t0xff\t1\t1\t0\t0x801\n"
    "Favorites\t0x10\t0xff\t0x0001,0x0002\t1\t1\t0\t0x908\n"
    "Hotkey1\t0x02,0x4f\t0xff\t0xff\t0\t0\t0\t0x908\n"
    "Hotkey2\t0x03,0x50\t0xff\t0xff\t0\t0\t0\t0x908\n"
    "Wait\t0x14\t0xff\t0x0020\t1\t1\t1\t0x808\n"
    "Journal\t0x24\t0xff\t0x0010\t1\t1\t1\t0x808\n"
    "Toggle POV\t0x21\t0xff\t0x0080\t1\t1\t1\t0x820\n"
)


def rows():
    out = {}
    for line in cm.remap(VANILLA).splitlines():
        f = [v for v in line.split("\t") if v.strip()]
        out[f[0]] = f
    return out


def test_space_sprint_dodge_shift_jump():
    r = rows()
    assert r["Sprint"][1] == "0x39"
    assert r["Jump"][1] == "0x2a"


def test_no_keyboard_clash_in_gameplay():
    keys = {}
    for name, f in rows().items():
        if name.startswith("//"):
            continue
        for k in f[1].split(","):
            if k.startswith("0x") and k != "0xff":
                assert k not in keys, f"{k} on {name} and {keys[k]}"
                keys[k] = name
    assert "0x38" in keys and keys["0x38"] == "Run"


def test_gamepad_unchanged():
    r = rows()
    assert r["Sprint"][3] == "0x2000"   # B
    assert r["Jump"][3] == "0x8000"     # Y


def test_remap_is_idempotent():
    once = cm.remap(VANILLA)
    assert cm.remap(once.replace("\r\n", "\n")) == once
