"""The custom-UI card (owner, 2026-11-02 22:06): stack.py's ui-custom.json sets Wind UI, Dear Diary and Wood and
Paper aside, our retheme of Dear Diary with them, and re-lays a path from the highest remaining mod that places it."""
import importlib.util
import pathlib

HERE = pathlib.Path(__file__).resolve().parents[2] / "infra" / "gpu-box" / "stack.py"
spec = importlib.util.spec_from_file_location("stack", HERE)
stack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stack)


def lay(mo2, mod, *paths):
    for p in paths:
        f = mo2 / "mods" / mod / p
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(b"x")


def test_custom_sets_aside_the_windui_rows_and_their_retheme(tmp_path):
    mo2 = tmp_path
    (mo2 / "profiles" / stack.PROFILE).mkdir(parents=True)
    (mo2 / "profiles" / stack.PROFILE / "modlist.txt").write_text(
        "+argonia-views\r\n+argonia-theme\r\n+wood-and-paper\r\n+dear-diary\r\n+windui\r\n+other\r\n")
    lay(mo2, "dear-diary", "interface/inventorymenu.swf", "interface/console.swf", "DearDiary.esp")
    lay(mo2, "argonia-theme", "interface/inventorymenu.swf", "interface/own.swf")
    lay(mo2, "windui", "SKSE/Plugins/windui.dll")
    lay(mo2, "other", "interface/console.swf")
    lay(mo2, "argonia-views", "PrismaUI/views/x.html")
    v = stack.ui_variant("custom", mo2)
    assert v["paths"]["interface\\inventorymenu.swf"] is None          # the retheme goes with Dear Diary
    assert v["paths"]["interface\\console.swf"] == ["other", "interface\\console.swf"]
    assert v["paths"]["skse\\plugins\\windui.dll"] is None
    assert "interface\\own.swf" not in v["paths"] and "prismaui\\views\\x.html" not in v["paths"]
    assert v["plugins"] == ["DearDiary.esp"]
    assert stack.ui_variant("windui", mo2)["paths"] == {}
