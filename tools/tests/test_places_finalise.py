"""The finalise chain in a scratch git repository: a clean run, a run killed (SIGKILL) inside each step and
resumed, a failed lessons agent, and a conflicting save. The lessons agent is a stand-in script."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tools.places import edits
from tools.places.finalise import STEPS, read_run

ROOT = Path(__file__).resolve().parents[2]
FIX = Path(__file__).parent / "places_edits"

FAKE_AGENT = r'''
import json, sys
from pathlib import Path
run, skill = Path(sys.argv[1]), Path(sys.argv[2])
if "FAIL" in skill.read_text():
    skill.write_text("half written")
    print(json.dumps({"is_error": True, "subtype": "error_max_budget_usd", "total_cost_usd": 3.1}))
    sys.exit(1)
(run / "place-build.SKILL.md").write_text(skill.read_text().replace("by its centre point", "by its whole footprint"))
(run / "place-people.SKILL.md").write_text("# Place people\n\nName each person from the place's own culture.\n")
(run / "lessons.json").write_text(json.dumps({"lessons": [{"where": "recipe", "ops": [1],
    "lesson": "Fit a building by its whole footprint.", "why": "The recipe fitted it by its centre point.",
    "change": "It now fits the footprint."}], "one_offs": [{"ops": [10], "what": "A chair moved in a house."}],
    "taste_candidates": []}))
print(json.dumps({"is_error": False, "subtype": "success", "total_cost_usd": 0.0, "num_turns": 1}))
'''


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    place = r / "newworld/places/fixture"
    files = json.loads((FIX / "place.json").read_text())
    edits.write_place(place, files)
    ops = json.loads((FIX / "all_ops.json").read_text())["ops"]
    (place / "edits").mkdir()
    (place / "edits/s1.json").write_text(json.dumps({"save_id": "s1", "place_id": "fixture", "name": "first",
                                                     "at": "x", "final": False, "base": {}, "ops": ops}))
    skill = r / "skill/SKILL.md"
    skill.parent.mkdir()
    skill.write_text("# Place build\n\nFit each building by its centre point.\n")
    for c in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"], ["add", "."],
              ["commit", "-q", "-m", "init"]):
        subprocess.run(["git", "-C", str(r), *c], check=True)
    agent = tmp_path / "agent.py"
    agent.write_text(FAKE_AGENT)
    return r, f"{sys.executable} {agent}"


def run_chain(repo, agent, crash=None, extra=()):
    env = dict(os.environ, FINALISE_AGENT_CMD=agent, FINALISE_PLAIN_COMMIT="1", PYTHONPATH=str(ROOT))
    env.pop("FINALISE_CRASH_IN", None)
    if crash:
        env["FINALISE_CRASH_IN"] = crash
    return subprocess.run([sys.executable, "-m", "tools.places", "finalise", "fixture", "s1", "--repo", str(repo),
                           "--skill", str(repo / "skill/SKILL.md"), "--skip-build", *extra],
                          cwd=ROOT, env=env, capture_output=True, text=True)


def check_done(repo):
    run = repo / "out/places/runs/fixture.s1"
    st = read_run(run)
    assert st["state"] == "done", st
    assert all((run / f"{s}.done").exists() for s in STEPS)
    files = edits.load_place(repo / "newworld/places/fixture")
    assert files["place"]["saves_applied"] == ["s1"]
    assert json.loads((repo / "newworld/places/fixture/edits/s1.json").read_text())["final"] is True
    assert "whole footprint" in (repo / "skill/SKILL.md").read_text()
    log = subprocess.run(["git", "-C", str(repo), "log", "--format=%s"], capture_output=True, text=True).stdout
    assert log.count("place-build: lessons") == 1 and log.count("edits recorded") == 1
    assert not subprocess.run(["git", "-C", str(repo), "status", "--porcelain", "newworld", "skill"],
                              capture_output=True, text=True).stdout
    return st


def test_clean_run(repo):
    r, agent = repo
    p = run_chain(r, agent)
    assert p.returncode == 0, p.stderr
    st = check_done(r)
    assert "git revert" in st["report_md"] and "chair" in st["report_md"]


@pytest.mark.parametrize("step", STEPS)
def test_killed_in_each_step_resumes(repo, step):
    r, agent = repo
    p = run_chain(r, agent, crash=step)
    assert p.returncode == -9, (p.returncode, p.stderr)
    assert not (r / f"out/places/runs/fixture.s1/{step}.done").exists()
    p = run_chain(r, agent)
    assert p.returncode == 0, p.stderr
    check_done(r)


def test_agent_fails_chain_completes(repo):
    r, agent = repo
    skill = r / "skill/SKILL.md"
    skill.write_text(skill.read_text() + "FAIL\n")
    subprocess.run(["git", "-C", str(r), "commit", "-qam", "fail marker"], check=True)
    before = skill.read_text()
    p = run_chain(r, agent)
    assert p.returncode == 0, p.stderr
    st = read_run(r / "out/places/runs/fixture.s1")
    assert st["steps"]["learn"]["status"] == "did not run"
    assert skill.read_text() == before
    assert "--relearn" in st["report_md"] and "over its budget" in st["report_md"]


def test_conflicting_save_stops_at_record(repo):
    r, agent = repo
    save = r / "newworld/places/fixture/edits/s1.json"
    s = json.loads(save.read_text())
    s["ops"][0]["before"]["pos"] = [1, 2, 3]
    save.write_text(json.dumps(s))
    p = run_chain(r, agent)
    assert p.returncode == 1
    st = read_run(r / "out/places/runs/fixture.s1")
    assert st["state"] == "failed" and "not applied" in st["report_md"]
    assert "saves_applied" not in json.loads((r / "newworld/places/fixture/place.json").read_text())


FAKE_STOCKDB = r'''
import json, sys
from pathlib import Path
verb, repo = sys.argv[1], Path(sys.argv[2])
with open(repo / "out" / "stockdb-calls.txt", "a") as f:
    f.write(verb + "\n")
if verb == "items":
    p = repo / "newworld/sources/stock/items.json"
    d = json.loads(p.read_text())
    d["items"].append({"id": "Skyrim.esm:01397E", "edid": "WarHammer"})
    p.write_text(json.dumps(d))
if verb == "load":
    people = json.loads((repo / "newworld/sources/people/fixture.json").read_text())["people"]
    db = repo / "newworld/story/data/db"
    db.mkdir(parents=True, exist_ok=True)
    (db / "person.jsonl").write_text("".join(json.dumps({"id": p["id"], "name": p["name"]}) + "\n" for p in people))
'''


@pytest.mark.parametrize("crash", [None, "record"])
def test_content_edits_reach_the_sources_and_the_tables(repo, tmp_path, crash):
    """A save with identity and stock edits: finalise writes the people and stock sources, measures the new item,
    reloads the tables and commits all of it by path; killed inside record, a rerun does the same once."""
    r, agent = repo
    base = json.loads((FIX / "stock/base.json").read_text())
    src = r / "newworld/sources"
    (src / "people").mkdir(parents=True)
    (src / "stock/places").mkdir(parents=True)
    (src / "people/fixture.json").write_text(json.dumps(base["identities"], indent=1) + "\n")
    (src / "stock/places/fixture.json").write_text(edits.dump_stock(base["stock"]))
    (src / "stock/items.json").write_text(json.dumps({"items": [{"id": "Skyrim.esm:013989"}]}))
    people_skill = r / ".claude/skills/place-people/SKILL.md"
    people_skill.parent.mkdir(parents=True)
    people_skill.write_text("# Place people\n")
    save = r / "newworld/places/fixture/edits/s1.json"
    s = json.loads(save.read_text())
    content = json.loads((FIX / "stock/content_all.json").read_text())["ops"][:2]
    s["ops"] += [dict(op, n=len(s["ops"]) + i + 1) for i, op in enumerate(content)]
    save.write_text(json.dumps(s))
    (r / "out").mkdir(exist_ok=True)
    subprocess.run(["git", "-C", str(r), "add", "."], check=True)
    subprocess.run(["git", "-C", str(r), "commit", "-qm", "sources"], check=True)
    fake = tmp_path / "stockdb.py"
    fake.write_text(FAKE_STOCKDB)
    os.environ["FINALISE_STOCK_CMD"] = f"{sys.executable} {fake}"
    try:
        if crash:
            assert run_chain(r, agent, crash=crash).returncode == -9
        p = run_chain(r, agent)
    finally:
        os.environ.pop("FINALISE_STOCK_CMD")
    assert p.returncode == 0, p.stderr
    st = check_done(r)
    assert json.loads((src / "people/fixture.json").read_text())["people"][0]["name"] == "Ada Hot-Hand"
    assert "Apprentice" in (src / "stock/places/fixture.json").read_text()
    assert "Ada Hot-Hand" in (r / "newworld/story/data/db/person.jsonl").read_text()
    calls = (r / "out/stockdb-calls.txt").read_text().split()
    assert calls[-2:] == ["items", "load"], calls   # the hammer was not measured yet
    assert st["steps"]["record"]["stock"]["status"] == "ok" and st["steps"]["record"]["content"] == 2
    assert "world database was reloaded" in st["report_md"]
    assert "own culture" in people_skill.read_text(), "the identity lesson's recipe put in place"
    assert not subprocess.run(["git", "-C", str(r), "status", "--porcelain"], capture_output=True, text=True).stdout.strip(
        ).replace("?? out/", ""), "sources and tables committed"


def test_content_faults_are_passed_to_the_lessons_agent(tmp_path):
    """An identity fault is a lesson for place-people, a stock fault for place-stock: each recipe is named with its
    own count, its own rewrite path, and is kept, put back and installed by the chain like place-build."""
    from tools.places.finalise import Run, agent_cmd, agent_prompt, content_skills, _kept
    for name in ("place-stock", "place-people"):
        skill = tmp_path / f".claude/skills/{name}/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text(f"# {name}\n")
    run = Run(tmp_path, "fixture", "s1")
    ops = [{"n": 1, "op": "identity.edit"}, {"n": 2, "op": "identity.edit"}, {"n": 3, "op": "stock.loose.add"},
           {"n": 4, "op": "ref.move"}]
    (run.dir / "faults.jsonl").write_text("".join(json.dumps(op) + "\n" for op in ops))
    text = agent_prompt(run)
    people, stock = text.index("2 of the fault edits"), text.index("1 of the fault edits")
    assert "place-people.SKILL.md" in text[people:stock] and "place-stock.SKILL.md" in text[stock:]
    assert '"skill": "place-people"' in text and '"skill": "place-stock"' in text
    assert {str(run.people_skill), str(run.stock_skill)} <= {str(k) for k, _ in _kept(run)}
    assert str(run.people_skill.parent) in agent_cmd(run, 1.0, 1)
    assert [n for n, *_ in content_skills(run)] == ["place-people", "place-stock"]
    (run.dir / "faults.jsonl").write_text(json.dumps({"n": 1, "op": "ref.move"}) + "\n")
    assert "place-stock" not in agent_prompt(run) and "place-people" not in agent_prompt(run)


def test_grouped_notes_reach_the_lessons_step(repo):
    """A note on several edits reaches the lessons agent once, with exactly the edits it covers said in plain words;
    an older save's per-op note still reads as a note; a taste edit's preference keeps its note's words."""
    r, agent = repo
    save_p = r / "newworld/places/fixture/edits/s1.json"
    save = json.loads(save_p.read_text())
    for op in save["ops"]:
        if op["n"] in (3, 4, 10):
            op["note_group"] = "g1"
        if op["n"] == 2:
            op["note_group"] = "g2"
    save["notes"] = [{"id": "g1", "text": "stalls must never block a walkway", "at": "x"},
                     {"id": "g2", "text": "I like it gone", "at": "x"}]
    save_p.write_text(json.dumps(save))
    subprocess.run(["git", "-C", str(r), "commit", "-qam", "notes"], check=True)
    p = run_chain(r, agent)
    assert p.returncode == 0, p.stderr
    run = r / "out/places/runs/fixture.s1"
    said = json.loads((run / "notes.json").read_text())["notes"]
    assert [(s["text"], s["call"], [o["n"] for c in s["changes"] for o in c["ops"]]) for s in said] == [
        ("off the bank", "fault", [1]), ("I like it gone", "taste", [2]),
        ("stalls must never block a walkway", "fault", [3, 4, 10])]
    moved = said[2]["changes"][2]["ops"][0]
    assert moved["op"] == "ref.move" and moved["from"] and moved["to"] and moved["where"] != "?"
    faults = [json.loads(x) for x in (run / "faults.jsonl").read_text().splitlines()]
    assert {f["n"]: f.get("note") for f in faults}[10] == "stalls must never block a walkway"
    from tools.places.finalise import Run, agent_prompt
    assert "notes.json" in agent_prompt(Run(r, "fixture", "s1"))
    prefs = edits.load_place(r / "newworld/places/fixture")["place"]["preferences"]
    assert [p_["note"] for p_ in prefs if p_["n"] == 2] == ["I like it gone"]


def test_a_save_naming_a_missing_note_is_refused():
    save = {"save_id": "s", "place_id": "p", "ops": [{"n": 1, "op": "veg.clear", "space": "exterior", "items": [],
                                                      "note_group": "g9"}], "notes": []}
    with pytest.raises(edits.EditError):
        edits.check_save(save)


def test_a_stale_world_stamp_makes_the_build_refresh_the_ground_first_and_deploy_last(tmp_path):
    from tools.places import finalise as F
    names = lambda moved: [n for n, _ in F.build_plan(tmp_path, "helstrom", moved)]
    assert names(True) == ["extract", "ground-check", "seat", "build", "check", "navexport", "deploy"]
    assert names(False) == ["seat", "build", "check", "navexport", "deploy"]
    assert F.build_plan(tmp_path, "helstrom", True)[0][1][-2:] == ["--ground", "helstrom"]
