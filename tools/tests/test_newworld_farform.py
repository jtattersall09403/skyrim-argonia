"""The leaf recolour (recolour.py) and the far-form audit of the LOD's read-back (lodplan.far_form)."""
import io

import numpy as np
from PIL import Image

from tools.newworld.world import lodplan, recolour


def test_recolour_moves_teal_to_green_and_keeps_alpha():
    a = np.zeros((4, 4, 4), np.uint8)
    a[..., :3] = (32, 68, 53)  # the bamboo's teal, hue 136
    a[..., 3] = 200
    out = recolour.recolour(a, -58, 0.9, 0.8)
    h, s, v = recolour.rgb_to_hsv(out[..., :3].astype(float) / 255)
    assert 70 <= h[0, 0] * 360 <= 103
    assert (out[..., 3] == 200).all()


def test_dds_reads_back_with_its_mips():
    a = np.random.default_rng(1).integers(0, 255, (8, 16, 4), dtype=np.uint8)
    raw = recolour.dds_bgra(a)
    im = Image.open(io.BytesIO(raw))
    assert np.array_equal(np.asarray(im.convert("RGBA")), a)
    assert len(raw) == 128 + 4 * (16 * 8 + 8 * 4 + 4 * 2 + 2 * 1 + 1 * 1)


def _logs(tmp_path, lines):
    (tmp_path / "DynDOLOD_SSE_BillboardsUsed_ArgoniaSmallWorld.txt").write_text("\n".join(lines))
    return tmp_path


def test_far_form_names_stale_and_unlike_billboards(tmp_path):
    plan = {"bases": [
        {"edid": "Good", "mech": "tree", "refs": 5, "model": "trees\\good.nif"},
        {"edid": "Squat", "mech": "tree", "refs": 5, "model": "trees\\squat.nif"},
        {"edid": "Other", "mech": "tree", "refs": 5, "model": "trees\\other.nif"},
        {"edid": "Dropped", "mech": "none", "refs": 0, "model": "trees\\moss.nif"},
    ]}
    logs = _logs(tmp_path, [
        "Good [TREE:0A000001] Billboard found textures\\terrain\\lodgen\\x.esm\\good_00000001.dds AB 800x1000 1",
        "Squat [TREE:0A000002] Billboard found textures\\terrain\\lodgen\\x.esm\\squat_00000002.dds AB 800x300 1",
        "Other [TREE:0A000003] Billboard found textures\\terrain\\lodgen\\x.esm\\good_00000003.dds AB 800x1000 1",
        "Dropped [TREE:0A000004] Billboard found textures\\terrain\\lodgen\\x.esm\\moss_00000004.dds AB 800x1000 1",
        "Gone [TREE:0A000005] Billboard found textures\\terrain\\lodgen\\x.esm\\gone_00000005.dds AB 800x1000 1",
    ])
    stale, faults = lodplan.far_form(plan, logs, read=lambda p: b"", extent=lambda m, r: (1000.0, 1000.0))
    assert [s.split(":")[0] for s in stale] == ["Dropped", "Gone"]
    assert [f.split(":")[0] for f in faults] == ["Squat", "Other"]


def test_far_form_is_clean_when_every_billboard_is_its_own(tmp_path):
    plan = {"bases": [{"edid": "Good", "mech": "tree", "refs": 5, "model": "trees\\good.nif"}]}
    logs = _logs(tmp_path, ["Good [TREE:0A000001] Billboard found textures\\terrain\\lodgen\\x.esm\\good_00000001.dds AB 800x1000 1"])
    assert lodplan.far_form(plan, logs, read=lambda p: b"", extent=lambda m, r: (1000.0, 1000.0)) == ([], [])
