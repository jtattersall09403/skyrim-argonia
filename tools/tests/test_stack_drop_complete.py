"""The nested-archive completeness check leaves a row's `drop` list out on purpose (stack.left_out_on_purpose)."""
import importlib.util
import pathlib

spec = importlib.util.spec_from_file_location(
    "stack", pathlib.Path(__file__).resolve().parents[2] / "infra" / "gpu-box" / "stack.py")
stack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stack)


def test_drop_list_is_on_purpose():
    m = {"drop": ["meshes/architecture/solitude/SBrylingHouse.nif", "meshes/elfx/*"]}
    assert stack.left_out_on_purpose("meshes/architecture/solitude/sbrylinghouse.nif", m)
    assert stack.left_out_on_purpose("meshes/elfx/a.nif", m)
    assert not stack.left_out_on_purpose("meshes/architecture/solitude/serikurhouse.nif", m)


def test_leftovers_and_no_drop():
    assert stack.left_out_on_purpose("tool.bat", {})
    assert stack.left_out_on_purpose("put your files here.txt", {})
    assert not stack.left_out_on_purpose("meshes/a.nif", {})
