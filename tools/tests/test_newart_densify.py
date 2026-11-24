"""densify.py on a small textured box: the density reaches its target, the triangles are the same, the mean colour
is unchanged, the grain stays off strongly coloured texels, and the gutters hold no black. Runs in the workshop's
scratch environment (out/newart/.venv); skipped where its libraries are missing."""
import json, sys
from pathlib import Path
import pytest
np = pytest.importorskip("numpy"); trimesh = pytest.importorskip("trimesh"); pytest.importorskip("xatlas"); pytest.importorskip("scipy")
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "newart"))
import densify  # noqa: E402


def test_densify_box(tmp_path):
    rng = np.random.default_rng(0)
    tex = np.clip(rng.normal(110, 6, (256, 256, 3)), 0, 255).astype(np.uint8); tex[:, 128:] = [200, 120, 20]   # half grey wood, half amber
    box = trimesh.creation.box((2.0, 1.0, 1.0)); box = box.unwrap() if hasattr(box, 'unwrap') else box
    uv = np.c_[(box.vertices[:, 0] + 1) / 2, (box.vertices[:, 1] + box.vertices[:, 2] + 1) / 3]
    box.visual = trimesh.visual.TextureVisuals(uv=uv, material=trimesh.visual.material.PBRMaterial(baseColorTexture=Image.fromarray(tex)))
    src = tmp_path / "box.glb"; box.export(src)
    sw = tmp_path / "sw.jpg"; Image.fromarray(np.tile((np.sin(np.arange(256) / 3) * 60 + 128).astype(np.uint8), (256, 1))).save(sw)
    r = densify.densify(src, tmp_path / "out", 100, sw, 400, atlas_px=1024)
    assert abs(r["after"]["px_per_m"] / 100 - 1) < 0.05
    assert r["after"]["triangles"] == r["before"]["triangles"] == len(box.faces)
    for a in r["after"]["per_atlas"]:
        assert abs(a["mean_L_after"] - a["mean_L_rebaked"]) < 0.5 and abs(a["mean_chroma_after"] - a["mean_chroma_rebaked"]) < 0.5
        assert a["fine_detail_after"] > a["fine_detail_rebaked"]
    sc = trimesh.load(tmp_path / "out/densified.glb", force='scene')
    im = np.asarray(next(iter(sc.geometry.values())).visual.material.baseColorTexture.convert('RGB'))
    assert im.reshape(-1, 3).sum(1).min() > 60                          # gutters filled from the charts, never black
    amber = im[np.abs(im.astype(int) - [200, 120, 20]).max(-1) < 12]
    assert len(amber) > 1000 and amber.std(0).max() < 3                  # no grain on the amber
    assert json.loads((tmp_path / "out/densify.json").read_text())["after"]["atlases"] == 1
