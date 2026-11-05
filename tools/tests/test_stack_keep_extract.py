"""L2: a keep-listed nested row (BM&V) lays only its keep list from the rars, so need_bytes is the archive plus a small
headroom (not x3), and a keep entry that matches no member is a red."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "infra" / "gpu-box"))
import stack  # noqa: E402

M = {"id": "bmv", "nested": ["Data1.rar", "Data2.rar"], "drop": ["valenwood.esp"],
     "keep": ["meshes/a/b.nif", "textures/hana/signs/*"]}
LIST = {"Data1.rar": ["Valenwood.esp", "Black Marsh.esm", "meshes/A/B.nif", "meshes/other.nif"],
        "Data2.rar": ["Textures/Hana/Signs/x.dds", "textures/big/y.dds"]}


def test_select_is_built_from_keep_case_insensitive_and_drop():
    sel = stack.keep_select(LIST, M)
    assert sel == {"Data1.rar": ["Black Marsh.esm", "meshes/A/B.nif"], "Data2.rar": ["Textures/Hana/Signs/x.dds"]}


def test_keep_entry_matching_nothing_is_red():
    with pytest.raises(SystemExit, match="matching nothing.*meshes/gone.nif"):
        stack.keep_select(LIST, {**M, "keep": M["keep"] + ["meshes/gone.nif"]})


def test_need_bytes_from_keep_list():
    assert stack.stage_need(M, 9 << 30) == (9 << 30) + stack.KEPT_HEADROOM
    assert stack.stage_need({"id": "x", "nested": ["a.rar"]}, 9 << 30) == 27 << 30  # no keep: the old x3
    assert stack.stage_need({"id": "x"}, 1 << 30) == 3 << 30


def test_stage_lays_only_selection_then_the_meshes_textures(tmp_path):
    laid = []

    def unpack_fn(archive, dest):
        (dest / "x").mkdir(parents=True)
        for n in M["nested"]:
            (dest / "x" / n).write_text(n)

    def unrar(inner, data, names=None):
        laid.append((inner.name, names))
        for n in names or []:
            (data / n).parent.mkdir(parents=True, exist_ok=True)
            (data / n).write_bytes(b"\x08textures\\big\\y.dds" if n.endswith(".nif") else b"d")

    stack.stage_nested(M, "k", tmp_path / "a.tar", tmp_path / "src", tmp_path / "data", tmp_path / "p.json",
                       unpack_fn, unrar, list_fn=lambda inner: LIST[inner.name])
    assert laid[0] == ("Data1.rar", ["Black Marsh.esm", "meshes/A/B.nif"])
    assert laid[1] == ("Data2.rar", ["Textures/Hana/Signs/x.dds"])
    assert laid[2] == ("Data2.rar", ["textures/big/y.dds"])  # named by the kept nif
    assert len(laid) == 3
