"""L1: the install's derived ground textures (derive_textures.py): mip chain, normal tilt and specular alpha."""
import numpy as np

from tools.argonia_world.terrain import dds
from tools.argonia_world.terrain import derive_textures as D
from tools.argonia_world.terrain import material as M
from tools.argonia_world.terrain.texcheck import normal_stats


def _diffuse(n=64, seed=3):
    rng = np.random.default_rng(seed)
    px = rng.uniform(40, 200, (n, n, 4)).astype(np.float32)
    px[..., 3] = 255
    return px


def test_mips_round_trip():
    px = _diffuse()
    b = D.write_dds(D.mips(px))
    hd = dds.header(b)
    assert (hd["w"], hd["h"], hd["mips"]) == (64, 64, 7)
    assert np.array_equal(dds.mip0(b), np.rint(px))


def test_normal_alpha_and_tilt_hit_vanilla_targets():
    nrm, k = D.normal_from(_diffuse(), 30.0, 22.0)  # vanilla's mean landscape alpha ~22/255 (r4)
    s = normal_stats(D.write_dds(D.mips(nrm, normal=True)))
    assert abs(s["alpha_mean"] - 22.0) < 1.0
    assert abs(s["tilt_deg"] - 30.0) < 1.5
    assert s["mips"] == 7 and k > 0


def test_flat_diffuse_reads_flat_and_matte():
    nrm, _ = D.normal_from(np.full((16, 16, 4), 128.0, np.float32), 0.0, 22.0)
    assert np.allclose(nrm[..., 2], 255.0, atol=0.6) and abs(nrm[..., 3].mean() - 22.0) < 0.5


def test_txst_paths_are_the_derived_ones():
    for t in M.TEXTURES:
        assert t.diffuse == f"argonia\\landscape\\{t.name}.dds" and t.normal == f"argonia\\landscape\\{t.name}_n.dds"
        assert t.vanilla_normal == f"landscape\\{t.name}_n.dds"
