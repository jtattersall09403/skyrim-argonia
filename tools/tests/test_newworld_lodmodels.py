"""Derived far-off models (tools/newworld/world/lodmodels.py): every vertex of a simplified shape is the source's own,
and a model that fails a check is never handed on."""
import collections
import struct

import numpy as np
import pytest

from tools.newworld.world import lodmodels, lodplan


def tube(n=24, rings=12, length=600.0, radius=40.0):
    """A log: a tube with a UV seam (the seam column's vertices doubled) and UVs tiling along it."""
    P, UV, I = [], [], []
    for r in range(rings + 1):
        for c in range(n + 1):  # column n repeats column 0's position with u = 1
            a = 2 * np.pi * (c % n) / n
            P.append([radius * np.cos(a), length * r / rings, radius * np.sin(a)])
            UV.append([c / n, 3.0 * r / rings])
    for r in range(rings):
        for c in range(n):
            a, b = r * (n + 1) + c, (r + 1) * (n + 1) + c
            I += [[a, b, a + 1], [a + 1, b, b + 1]]
    P = np.array(P)
    return {"P": P, "N": P / np.maximum(np.linalg.norm(P, axis=1, keepdims=True), 1e-9), "UV": np.array(UV), "C": None,
            "I": np.array(I), "tex": ["textures\\bark.dds", "textures\\bark_n.dds"], "two_sided": False, "alpha_test": False,
            "area": 1.0}


def test_a_simplified_shape_keeps_only_the_sources_own_vertices():
    src = tube()
    out = lodmodels.simplify(src, 120)
    assert 0 < len(out["I"]) <= 140 < len(src["I"])
    have = {tuple(np.round(p, 3)) for p in src["P"]}
    assert all(tuple(np.round(p, 3)) in have for p in out["P"])  # positions: the bounds cannot grow
    uvs = {tuple(np.round(u, 5)) for u in src["UV"]}
    assert all(tuple(np.round(u, 5)) in uvs for u in out["UV"])  # UVs: none leaves the source's range
    assert out["I"].max() < len(out["P"]) and len(out["N"]) == len(out["P"])
    # the seam stays closed: every edge of the welded surface is still shared by two triangles, bar the two open ends
    w = {tuple(np.round(p, 3)): i for i, p in enumerate(out["P"])}
    weld = np.array([w[tuple(np.round(p, 3))] for p in out["P"]])
    edges = collections.Counter()
    for t in weld[out["I"]]:
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            edges[(min(a, b), max(a, b))] += 1
    open_edges = [e for e, k in edges.items() if k == 1]
    ys = {round(float(out["P"][np.nonzero(weld == v)[0][0]][1])) for e in open_edges for v in e}
    assert ys <= {0, 600}


def test_a_shape_under_its_target_is_left_as_it_is():
    src = tube(n=6, rings=2)
    assert lodmodels.simplify(src, 500) is src


def test_the_shapes_file_is_what_niflod_reads():
    s = tube(n=4, rings=1)
    raw = lodmodels.shapes_file([s])
    assert raw[:4] == b"NLOD" and struct.unpack_from("<I", raw, 4)[0] == 1
    nv, nt, flags = struct.unpack_from("<III", raw, 8)
    assert (nv, nt, flags) == (len(s["P"]), len(s["I"]), 1)
    tex0 = struct.unpack_from("<H", raw, 20)[0]
    assert raw[22:22 + tex0] == b"textures\\bark.dds"
    assert len(raw) == 20 + 2 + tex0 + 2 + len(s["tex"][1]) + nv * 4 * (3 + 2 + 3) + nt * 3 * 2


def test_the_lod_model_goes_where_dyndolod_and_the_plan_look():
    assert lodmodels.lod_path("Argonia\\Trees\\LogLarge01.nif") == "lod\\argonia\\trees\\loglarge01_lod_0.nif"
    have = {"lod\\argonia\\trees\\loglarge01_lod_0.nif"}
    assert lodplan.lod_model("argonia\\trees\\loglarge01.nif", lambda p: b"x" if p in have else None) == "lod\\argonia\\trees\\loglarge01_lod_0.nif"


@pytest.mark.skipif(not lodmodels.NIFLOD.exists(), reason="niflod not built (tools/newworld/niflod/build.sh)")
def test_a_written_model_reads_back_as_skyrims_lod_models_are_laid_out(tmp_path):
    import subprocess
    s = lodmodels.simplify(tube(), 100)
    (tmp_path / "s.bin").write_bytes(lodmodels.shapes_file([s]))
    subprocess.run([str(lodmodels.NIFLOD), str(tmp_path / "s.bin"), str(tmp_path / "o.nif")], check=True, capture_output=True)
    inf = lodmodels.info(tmp_path / "o.nif")
    assert inf["root"] == "BSFadeNode" and set(inf["blocks"]) == {"BSFadeNode", "BSTriShape", "BSLightingShaderProperty", "BSShaderTextureSet"}
    sh = inf["shapes"][0]
    assert sh["tris"] == len(s["I"]) and sh["parent"] == "BSFadeNode" and sh["shader_type"] == 0
    assert (sh["flags1"], sh["flags2"]) == (0x80400300, 0x8001) and sh["tex"][:2] == s["tex"] and sh["normals"] and sh["tangents"]
    # and the checks refuse a model that is not the source's shape
    nums, faults = lodmodels.verify((tmp_path / "o.nif").read_bytes(), [tube(length=2000.0)], 100, lambda t: b"x")
    assert any("fall short" in f for f in faults)
    nums, faults = lodmodels.verify((tmp_path / "o.nif").read_bytes(), [tube()], 100, lambda t: None)
    assert nums["triangles"] == len(s["I"]) and all("texture not in the profile" in f for f in faults) and faults


def test_targets_keep_every_block_within_the_budget_or_give_none():
    def row(src, model, tris):
        return {"mech": "none", "heavy": True, "source": src, "model": model, "triangles": tris}
    rows = [row("a", "log.nif", 4000), row("b", "stump.nif", 3000), row("c", "root.nif", 2000)]
    blocks = {"a": {4: collections.Counter({(0, 0): 5})}, "b": {4: collections.Counter({(0, 0): 10, (1, 0): 40})},
              "c": {4: collections.Counter({(5, 5): 5000})}}
    load = {4: collections.Counter({(1, 0): 1327}), 8: collections.Counter()}
    t = lodplan.lod_targets(rows, blocks, load)
    assert t["log.nif"] == round(4000 * lodplan.LOD_RATIO)  # Skyrim's own share where there is room
    assert t["stump.nif"] == (lodplan.BUDGET[4] - 1327) // 40  # lowered to fit its densest block beside the full-model rules
    assert "root.nif" not in t  # 5,000 refs in a block: under LOD_MIN triangles each, so none
    for k in ((0, 0), (1, 0)):
        assert load[4][k] + sum(blocks[r["source"]][4][k] * t.get(r["model"], 0) for r in rows) <= lodplan.BUDGET[4]
