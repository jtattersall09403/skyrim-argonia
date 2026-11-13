from tools.newworld.ecology.bodies_repro import batches


def test_batches_select_each_ref_kill_then_read():
    a, b = batches({"bandit": (0xF75D5A, (0, 0, 0), "x"), "crab": (0xF52138, (0, 0, 0), "y")}, "0A")
    la, lb = a.splitlines(), b.splitlines()
    assert la[0].startswith("scof ") and la[-1] == "scof 0" and lb[-1] == "scof 0"
    assert la[1] == "cow ArgoniaBlackMarsh -67 -188"
    assert la.count("kill") == 2 and "prid 0AF75D5A" in la and "prid 0AF52138" in lb
    assert lb.count("getdead") == 2 and lb.count("isswimming") == 2
