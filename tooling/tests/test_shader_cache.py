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
