"""L1: a leaf card soft-lit past the stack's wrap ceiling is dropped (lane 1.15-r5-sky-2: neon mint ghost trees)."""
from tools.argonia_world.vegetation import leaf_hue


def test_glowing_flags_a_wrap_above_the_stack_ceiling():
    soft = {"meshes/argonia/trees/shrubtree03.nif": [
        {"soft": 5.0, "diffuse": "textures/_resourcepack/landscape/trees/snowgumbranches01_d.dds"},
        {"soft": 10.0, "diffuse": "textures/_resourcepack/landscape/trees/snowgumbranches01_d.dds"}],
        "meshes/argonia/trees/cypress1.nif": [{"soft": 5.0, "diffuse": "textures/x/baldcypressbranches01_d.dds"}]}
    assert leaf_hue.glowing("argonia\\trees\\shrubtree03.nif", soft) == ["soft-light wrap 10.0 on snowgumbranches01_d.dds"]
    assert leaf_hue.glowing("argonia\\trees\\cypress1.nif", soft) == []
    placed = [{"form_key": "0F0AC9:King of the Murkmire.esp", "model": "argonia\\trees\\shrubtree03.nif"}]
    assert leaf_hue.glow_problems(placed, soft) == [
        "0F0AC9:King of the Murkmire.esp argonia\\trees\\shrubtree03.nif: soft-light wrap 10.0 on snowgumbranches01_d.dds"]


def test_soft_lit_reads_wrap_and_diffuse_from_the_measured_stack():
    soft = leaf_hue.load_soft()
    assert {x["soft"] for x in soft["meshes/argonia/trees/shrubtree03.nif"]} == {5.0, 10.0}
    assert max(x["soft"] for v in soft.values() for x in v if "cypress1" not in x["diffuse"]) == 10.0
