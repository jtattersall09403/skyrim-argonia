"""B14 to B17 and B19 in the dialogue linter: place-occupying hold, fighting a place, bare passive, bare sale."""
import importlib.util
import pathlib
import re

import yaml

SKILL = pathlib.Path(__file__).resolve().parents[2] / ".claude" / "skills" / "dialogue-write"
spec = importlib.util.spec_from_file_location("dialogue_lint", SKILL / "lint.py")
lint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lint)
BANS = {b["id"]: b for b in yaml.safe_load((SKILL / "bans.yaml").read_text())}


def rx(ban_id):
    return re.compile(lint.pattern(BANS[ban_id]))


CASES = {
    "B14-hold-place": (
        ["Unbound scouts hold the cave.", "The Collector's men held the old tower.", "They keep the vault.",
         "whose garrisons keep the old Imperial forts", "Legionaries kept the river crossing."],
        ["They hold the line.", "She held a grudge.", "They keep the peace.", "Keep the old coin."],
    ),
    "B19-im-to": (
        ["I'm to go to Vosh-Leera.", "Now i’m to wait.", "I am to go."],
        ["I should go to Vosh-Leera.", "Dralin told me that I should wait.", "Tim to go."],
    ),
    "B15-fight-place": (
        ["The player fights the yard and the hall.", "She kills the gate.", "You sneak past the camp."],
        ["The player fights the guards in the yard.", "He cleared the road of bandits."],
    ),
    "B16-passive-actor": (
        ["They are fought, or passed.", "The guard was killed by the player."],
        ["The player fights them.", "The ship was built in Lilmoth."],
    ),
    "B17-sold-bare": (
        ["The company sold the course of the best ship.", "He sold them.", "I would sell that."],
        ["He sold the privateers the ship's course for gold.", "She sells it at market for ten drakes."],
    ),
}


def test_flags_and_leaves():
    for ban_id, (flagged, clean) in CASES.items():
        r = rx(ban_id)
        assert not [s for s in flagged if not r.search(s)], (ban_id, "missed")
        assert not [s for s in clean if r.search(s)], (ban_id, "noisy")


def test_hold_place_has_a_cap_and_others_are_warn_or_hard():
    assert BANS["B14-hold-place"]["max_per_file"] == 2
    assert BANS["B16-passive-actor"]["severity"] == "warn"
    assert BANS["B17-sold-bare"]["severity"] == "warn"
    assert "severity" not in BANS["B15-fight-place"]


def test_im_to_warns_above_one_per_record(tmp_path, capsys, monkeypatch):
    assert BANS["B19-im-to"]["max_per_file"] == 1 and BANS["B19-im-to"]["severity"] == "warn"
    f = tmp_path / "journal.txt"
    f.write_text("I'm to go east.\nI was told to wait.\n")
    monkeypatch.setattr("sys.argv", ["lint.py", str(f), "--race", "imperial"])
    assert lint.main() == 0 and "B19" not in capsys.readouterr().out.split("review by hand")[0]
    f.write_text("I'm to go east.\nI'm to wait.\n")
    assert lint.main() == 0 and "warn B19-im-to: 2 in the file" in capsys.readouterr().out
