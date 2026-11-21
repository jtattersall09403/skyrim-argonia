"""The hand-over line: the built check is current against the place files by the consistency stage's rule (an edit
after the check, in a room's files too, makes it old; the owner's `edits/` do not)."""
import os

from tools.newworld import consistency as C
from tools.places import handover


def place(tmp_path):
    root = tmp_path / "repo"
    d = root / "newworld/places/fen"
    (d / "spaces/hut").mkdir(parents=True)
    (d / "edits").mkdir()
    for f in ("place.json", "spaces/hut/refs.jsonl", "edits/save.json"):
        (d / f).write_text("{}\n")
        os.utime(d / f, (1000, 1000))
    chk = root / "out/places/shards/fen/check.json"
    chk.parent.mkdir(parents=True)
    chk.write_text("{}\n")
    os.utime(chk, (2000, 2000))
    (root / "out/newworld").mkdir(parents=True)
    return root, d


def test_current_then_old_after_a_room_edit_but_not_after_an_owner_save(tmp_path, capsys):
    root, d = place(tmp_path)
    ok, line = C.built_check_current(root, root / "out", "fen")
    assert ok and line.startswith("built check current")
    os.utime(d / "edits/save.json", (3000, 3000))          # the owner's save: not the draft
    assert C.built_check_current(root, root / "out", "fen")[0]
    os.utime(d / "spaces/hut/refs.jsonl", (3000, 3000))     # the agent's last small edit, after the check
    ok, line = C.built_check_current(root, root / "out", "fen")
    assert not ok and "NOT CURRENT" in line and "after the last edit" in line
    assert handover.main(["fen", "--places-dir", str(root / "newworld/places")]) == 1
    assert "NOT CURRENT" in capsys.readouterr().out
