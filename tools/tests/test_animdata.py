"""infra/gpu-box/animdata.py: the missing TK Dodge clips get the vanilla dodge's triggers and motion (0.2 §c)."""
import importlib.util
import pathlib

import pytest

spec = importlib.util.spec_from_file_location(
    "animdata", pathlib.Path(__file__).resolve().parents[2] / "infra" / "gpu-box" / "animdata.py")
animdata = importlib.util.module_from_spec(spec)
spec.loader.exec_module(animdata)

# two projects: a creature without clips, and DefaultMale with DodgeBack (id 2) and one other clip (id 1)
CLIPS = ["1", "1", "Behaviors\\0_Master.hkx", "1",
         "Walk", "1", "1", "0", "0", "0", "",
         "DodgeBack", "2", "1", "0", "0", "1", "SprintStop:0.9", ""]
MOTION = ["1", "0.5", "1", "0.5 0 10 0", "1", "0.5 0 0 0 1", "",
          "2", "0.9", "2", "0.1 0 -3.9 0", "0.9 0 -207.07 0", "1", "0.9 0 0 0 1", ""]
CREATURE = ["1", "1", "Behaviors\\Wolf.hkx", "0"]
TEXT = "\r\n".join(["2", "WolfProject.txt", "DefaultMale.txt", str(len(CREATURE)), *CREATURE,
                    str(len(CLIPS)), *CLIPS, str(len(MOTION)), *MOTION]) + "\r\n"


def test_round_trip_is_exact():
    assert animdata.render(animdata.parse(TEXT)) == TEXT


def test_missing_clip_gets_the_vanilla_motion_under_a_free_id():
    out, added = animdata.patch(TEXT)
    assert added == ["DefaultMale.txt TKDodgeBack = DodgeBack (clip 2) as 3"]
    p = {name: (block, motion) for name, block, motion in animdata.parse(out)}
    block, motion = p["DefaultMale.txt"]
    c, m = animdata.clips(block), animdata.motions(motion)
    assert c["TKDodgeBack"][2] == "3"
    a, b, _ = c["TKDodgeBack"]
    assert block[a:b] == ["TKDodgeBack", "3", "1", "0", "0", "1", "SprintStop:0.9", ""]
    ma, mb = m["3"]
    assert motion[ma:mb] == ["3", "0.9", "2", "0.1 0 -3.9 0", "0.9 0 -207.07 0", "1", "0.9 0 0 0 1", ""]
    assert p["WolfProject.txt"] == (CREATURE, None)


def test_patch_is_idempotent():
    once, _ = animdata.patch(TEXT)
    twice, added = animdata.patch(once)
    assert twice == once and added == []


def test_a_truncated_file_is_refused():
    with pytest.raises((ValueError, IndexError)):
        animdata.parse(TEXT.rsplit("\r\n", 4)[0] + "\r\n")
