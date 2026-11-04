import importlib.util, pathlib
spec = importlib.util.spec_from_file_location("rr", pathlib.Path(__file__).parents[1] / "tooling/round_retro.py")
rr = importlib.util.module_from_spec(spec); spec.loader.exec_module(rr)

def test_parse(tmp_path):
    f = tmp_path / "r.log"
    f.write_text("== launch\nx\n== 91 s\n== terrain: 1097 s\nROUND up OK in 7 s\nup after 3 tries\nno spot capacity\n"
                 "   run 1: PASS in 67.6 s, 1 -> 2 MB\nqueued for argonia-play behind x (up to 7200 s)\nDEPLOY OK in 300 s\n")
    S, W = rr.parse([str(f)])
    assert S["deploy: launch"] == [91.0] and S["lod: terrain"] == [1097.0] and S["round: up"] == [7.0]
    assert S["capacity wait ((tries-1) x 60 s)"] == [120.0] and S["batch: per journey run"] == [67.6]
    assert S["deploy total"] == [300.0] and W["locks: queued behind"] == 1
    assert "| deploy: launch | 1 | 91 |" in rr.table(S, W)
