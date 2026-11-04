"""L2: the journey linter (lane journey-lint) on game-13's three authoring errors, and the client's plugin-form
resolution against a fake bridge. Each rule is proved by a line it must fail and a line it must pass."""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from tools import journey_lint as L  # noqa: E402
from test_bridge import FakeMachine, make, no_cache, serve  # noqa: E402,F401 (no_cache: the fixture)

VOCAB = {"functions": [{"name": "GetLevel", "short": "", "params": 0}, {"name": "HasPerk", "short": "", "params": 1},
                       {"name": "GetBaseActorValue", "short": "GetBaseAV", "params": 1},
                       {"name": "StartCombat", "short": "", "params": 1}, {"name": "MoveTo", "short": "", "params": 4}],
         "actor_values": ["Health", "One-Handed"], "refs": ["ARG_Ref_Known"]}


def journey(*expect, do=()):
    return {"id": "t", "runner": 1, "steps": [{"name": "s", "do": list(do), "expect": list(expect)}]}


def vocab(tmp_path):
    p = tmp_path / "vocab.json"
    p.write_text(json.dumps(VOCAB))
    return L.load_vocab(p)


def test_an_unquoted_calling_id_fails_and_a_quoted_one_passes():
    bad = L.lint(journey({"console": "{opp}.GetLevel", "contains": ">> 10"}, {"console": "1000088C.GetLevel"}), None)
    assert len(bad) == 2 and "quote the calling ref" in bad[0]
    assert L.lint(journey({"console": '"{opp}".GetLevel', "contains": ">> 10"}), None) == []
    assert L.lint(journey(do=[{"console": "player.moveto {opp} 0 -150 0"}]), None) == []


def test_a_malformed_plugin_form_fails_and_a_well_formed_one_passes():
    assert L.lint(journey({"console": "player.hasperk TKDodgeAddon.esp|809", "contains": ">> 1"}), None)
    assert L.lint(journey({"console": "player.hasperk TKDodgeAddon.esp|0x809", "contains": ">> 1"}), None) == []


def test_the_vocab_catches_an_unknown_av_function_and_ref(tmp_path):
    v = vocab(tmp_path)
    errs = L.lint(journey({"read": ["av", "OneHanded", "player"], "path": "base", "eq": 0},
                          {"console": "player.GetLvl"}, {"console": "player.moveto ARG_Ref_Gone"},
                          {"console": "player.GetLevel 3"}), v)
    assert len(errs) == 4, errs
    assert L.lint(journey({"read": ["av", "one-handed", "player"], "path": "base", "eq": 0},
                          {"console": '"{opp}".GetLevel'}, {"console": "player.getbaseav Health"},
                          {"console": "set ARG_Global to 1"}, {"console": "player.moveto ARG_Ref_Known"},
                          {"console": "player.hasperk TKDodgeAddon.esp|0x809"}), v) == []


def test_no_cache_is_static_only(tmp_path):
    assert L.load_vocab(tmp_path / "none.json") is None
    assert L.lint(journey({"console": "player.GetLvl"}), None) == []


def test_the_client_writes_a_plugin_form_as_its_runtime_id():
    seen = []

    def reply(line):
        seen.append(line)
        if " plugin " in line:
            light = "TKDodgeAddon" in line
            return {"ok": True, "result": {"prefix": "FE002" if light else "0A"}}
        return {"ok": True, "result": {"output": ">> 1"}}

    ls, port = serve(reply)
    b = make(port, FakeMachine())
    b.call("console", "player.hasperk TKDodgeAddon.esp|0x809")
    b.call("console", "Other.esm|0x12.GetLevel")
    assert seen[1].endswith(" console player.hasperk FE002809")
    assert seen[3].endswith(' console "0A000012".GetLevel')
    ls.close()


def test_talk_names_one_placed_ref():
    j = {"steps": [{"name": "a", "do": [{"talk": "ARG_Ref_ClaywaterStationLivia"}, {"talk": "{opp}"}]},
                   {"name": "b", "do": [{"talk": "Livia 0 110"}]}]}
    errs = L.lint(j, None)
    assert len(errs) == 1 and errs[0].startswith("step b: talk")


def test_reach_and_needs():
    from tools import journey_lint as jl
    ok = {"reach": ["ui/**", "esm", "skse"], "steps": [{"name": "a"}, {"name": "b", "needs": ["a"], "reach": ["data/dependencies.json"]}]}
    assert jl.lint(ok, None) == []
    bad = {"reach": "ui", "independent_steps": 1,
           "steps": [{"name": "a", "needs": ["b"], "reach": ["no/such/path/**"]}, {"name": "b"}]}
    errs = jl.lint(bad, None)
    assert any("reach: a list" in e for e in errs) and any("independent_steps" in e for e in errs)
    assert any("matches no tracked file" in e for e in errs) and any("not an earlier step" in e for e in errs)


def test_a_look_journey_needs_first_person_hud_off_and_forced_weather_per_stop():
    stop = {"name": "s", "do": [{"console": {"line": "cow ARG_Province -9 27", "settle": 60}}], "expect": []}
    j = {"id": "j", "look": "world", "independent_steps": True, "steps": [stop]}
    errs = L.look(j)
    assert any("camera: first" in e for e in errs) and any("hud: off" in e for e in errs)
    assert any("form id" in e for e in errs) and any("read the weather back" in e for e in errs)
    good = {"name": "s", "do": [{"hud": "off"}, {"console": "cow ARG_Province -9 27"},
                                {"console": "fw Argonia.esm|0x000E9B"}],
            "expect": [{"read": ["weather"], "path": "current.editor_id", "eq": "ARG_Weather_clear_dry", "within": 20}],
            "scan": 6}
    assert L.look({**j, "camera": "first", "steps": [good]}) == []
    by_edid = {**good, "do": [{"hud": "off"}, {"console": "cow ARG_Province -9 27"}, {"console": "fw ARG_Weather_clear_dry"}]}
    assert any("form id" in e for e in L.look({**j, "camera": "first", "steps": [by_edid]}))
    anyw = {"name": "s", "do": [{"hud": "off"}, {"console": "player.setpos x 1"}], "weather": "any", "scan": 6}
    assert L.look({**j, "camera": "first", "steps": [anyw]}) == []
    assert L.look({"id": "j", "steps": [stop]}) == []   # unmarked: not a look journey


def test_a_look_stop_without_a_scan_fails_naming_the_step():
    stop = {"name": "pebbles", "do": [{"hud": "off"}, {"console": "player.setpos x 1"}], "weather": "any"}
    j = {"id": "j", "look": "world", "camera": "first", "steps": [stop]}
    assert L.look(j) == ["step pebbles: look: world: a scan of headings at each stop (`scan: 6`; owner 19:05 #41)"]
    assert L.look({**j, "steps": [{**stop, "scan": 1}]}) != []
    assert L.look({**j, "steps": [{**stop, "scan": 6}]}) == []


def test_the_five_look_journeys_meet_the_standard():
    import yaml
    for n in ("ground-materials", "road-look", "rock-booth", "tree-seat", "claywater-look"):
        j = yaml.safe_load((pathlib.Path(__file__).resolve().parents[2] / "tests" / "journeys" / f"{n}.yaml").read_text())
        assert j.get("look") == "world", n
        errs = [e for e in L.look(j) if "a scan of headings" not in e]  # scans land at the planner's refresh (look.py)
        assert errs == [], (n, errs[:3])
