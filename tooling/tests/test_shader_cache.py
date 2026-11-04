import importlib.util
import pathlib

import pytest

spec = importlib.util.spec_from_file_location(
    "shader_cache", pathlib.Path(__file__).resolve().parents[2] / "infra" / "gpu-box" / "shader_cache.py")
sc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sc)

FILES = {"shaders\\lighting.hlsl": ["community-shaders", "a"],
         "skse\\plugins\\communityshaders.dll": ["community-shaders", "b"],
         "skse\\plugins\\communityshaders\\overrides\\argonia_fog.json": ["argonia", "c"],
         "textures\\x.dds": ["tropical", "d"], "argonia.esm": ["ours", "e"]}


def test_key_ignores_what_cs_does_not_compile_from():
    k = sc.key(FILES)
    assert len(k) == 12
    other = dict(FILES, **{"textures\\x.dds": ["tropical", "z"], "argonia.esm": ["ours", "y"]})
    assert sc.key(other) == k  # a world or texture change keeps the cache


@pytest.mark.parametrize("path", ["shaders\\lighting.hlsl", "skse\\plugins\\communityshaders.dll",
                                  "skse\\plugins\\communityshaders\\overrides\\argonia_fog.json"])
def test_key_changes_with_a_shader_dll_or_setting(path):
    assert sc.key(dict(FILES, **{path: ["x", "changed"]})) != sc.key(FILES)


def test_no_cs_files_refuses():
    with pytest.raises(SystemExit):
        sc.key({"argonia.esm": ["ours", "e"]})


def test_key_carries_the_gpu_and_driver():
    base = sc.full_key(FILES)
    assert base == sc.key(FILES)  # no GPU read: the shaders only
    l4 = sc.full_key(FILES, "NVIDIA L4, 551.61")
    t4 = sc.full_key(FILES, "Tesla T4, 551.61")
    assert l4 != t4 and l4 != base and l4.startswith(base + "-")
    assert sc.full_key(FILES, "NVIDIA L4, 552.00") != l4  # a driver change
    assert sc.full_key(FILES, " nvidia  l4, 551.61 ") == l4


def test_lay_or_skip_decision():
    assert sc.decide("k", "k", True) == "current"
    assert sc.decide("k-aaaaaa", "k-bbbbbb", True) == "lay"  # the clone: same shaders, other GPU
    assert sc.decide("", "k", False) == "compile"
