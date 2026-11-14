import re
from pathlib import Path

import pytest

from tools.newworld.ecology import bodies_repro as B

FOUND = {"bandit": (0xF75D5A, (-270000.0, -766000.0, 0.0), "x"), "crab": (0xF52138, (-270100.0, -766100.0, 0.0), "y")}


def test_a_ref_is_read_only_in_a_batch_after_the_one_that_loads_or_moves_it():
    b = B.batches(FOUND, "06")
    assert b["a"] == "cow ArgoniaBlackMarsh -66 -188\n"            # the bandit's own cell, and nothing else
    assert "getpos" not in b["a"] + b["b"] + b["e"]                 # the console runs a file before the game moves
    assert b["b"].count("moveto player") == 3 and "prid 06F75D5A" in b["b"] and f"prid {B.NAZEEM}" in b["b"]
    assert b["e"] == f"player.moveto {B.BRENUIN}\n"
    for letter in "cdfg":
        lines = b[letter].splitlines()
        assert lines[0] == f"scof bodies_repro_{letter}.txt" and lines[-1] == "scof 0"
    assert b["c"].count("kill") == 3 and b["f"].count("kill") == 1 and "kill" not in b["d"] + b["g"]
    assert b["c"].index("kill") > b["c"].rindex("isswimming")      # every reading is taken before anything dies


def test_the_pair_is_within_a_cell_so_one_arrival_loads_both():
    far = (1, (50000.0, 50000.0, 0.0), "crabFar")
    near = (2, (4100.0, 100.0, 0.0), "crabNear")
    got = B.nearest_pair([(9, (4000.0, 0.0, 0.0), "b")], [far, near])
    assert got["crab"] == near
    with pytest.raises(SystemExit):
        B.nearest_pair([(9, (4000.0, 0.0, 0.0), "b")], [far])


def log(letter, values):
    return "\n".join(f"GetPos: Z >> {v:.2f}" for v in values)


def logs(bandit_z, nazeem_z, brenuin_z):
    c = B.parse("c", log("c", [0, 0, 100, 0, 0, bandit_z, 0, 0, 0, 0, 100, 0, 0, 0, 0, nazeem_z, 0, 0]))
    f = B.parse("f", log("f", [0, 0, 50, 0, 0, brenuin_z, 0, 0]))
    return c, f


@pytest.mark.parametrize("zs, word", [((78, 100, 50), "copy"), ((78, 78, 50), "our world"), ((78, 78, 28), "mod stack"),
                                      ((100, 100, 50), "nobody")])
def test_the_three_arms_name_one_cause(zs, word):
    c, f = logs(*zs)
    d, why = B.verdict(c, f, {"bandit": 100.0, "crab": 100.0, "nazeem": 100.0})
    assert word in why
    assert d["bandit"] == zs[0] - 100


def test_a_short_log_is_refused():
    with pytest.raises(SystemExit):
        B.parse("c", log("c", [1, 2, 3]))


def test_the_stack_keeps_the_logs_plugins_write_in_data():
    # FreeClimb writes Data\SKSE\FreeClimb.log; laying the stack must not delete the log of the walk before
    ps = (Path(__file__).resolve().parents[2] / "infra/gpu-box/stack.ps1").read_text()
    lay = ps[ps.index("what goes and what is laid are listed first"):]
    assert re.search(r"\$gone = .*\n.*\n.*skse\\\\\[\^\\\\\]\+\\\.log", lay[:900])
