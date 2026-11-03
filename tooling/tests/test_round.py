"""infra/gpu-box/round.sh with stub machine, deploy and batch: one job, verdict lines, resume, stop on every exit."""
import os
import pathlib
import shutil
import subprocess

REPO = pathlib.Path(__file__).resolve().parents[2]


def stub(path: pathlib.Path, body: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/usr/bin/env bash\n" + body)
    path.chmod(0o755)


def tree(tmp, deploy_fails=0, batch_items=2, to_run=2):
    root = tmp / "repo"
    (root / "infra" / "gpu-box").mkdir(parents=True)
    shutil.copy(REPO / "infra" / "gpu-box" / "round.sh", root / "infra" / "gpu-box" / "round.sh")
    log = tmp / "calls.log"
    stub(root / "infra" / "gpu-box" / "run.sh", f'echo "run $*" >>{log}\n')
    home = tmp / "home"
    stub(home / ".argonia" / "scripts" / "up_until.sh", f'echo "up $*" >>{log}\n')
    fails = tmp / "deploy_fails"
    fails.write_text(str(deploy_fails))
    stub(tmp / "bin" / "make", f'echo "make $*" >>{log}; n=$(cat {fails}); '
                               f'if [ "$n" -gt 0 ]; then echo $((n-1)) >{fails}; exit 1; fi; exit 0\n')
    (root / "tools").mkdir()
    (root / "tools" / "run_batch.py").write_text(f'''import json, pathlib, sys, time
open("{log}", "a").write("batch " + " ".join(sys.argv[1:]) + "\\n")
if "--plan" in sys.argv:
    print("batch: {to_run} of 2 journeys, {to_run} of 4 steps to run")
    sys.exit(0 if {to_run} else 3)
d = pathlib.Path("out/batch/t") / str(time.time_ns()); d.mkdir(parents=True)
items = [{{"id": "a", "passed": True}}, {{"id": "b", "passed": False}}][:{batch_items}]
(d / "summary.json").write_text(json.dumps({{"items": items}}))
(d / "01-a").mkdir(); (d / "01-a" / "01-x.png").write_bytes(b"png")
sys.exit(1)
''')
    (root / "b.yaml").write_text("id: t\nitems: [a, b]\n")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "x"],
                   cwd=root, check=True)
    env = dict(os.environ, HOME=str(home), PATH=f"{tmp / 'bin'}:{os.environ['PATH']}")
    return root, log, env


def go(root, env):
    return subprocess.run(["bash", "infra/gpu-box/round.sh", "b.yaml", "m1"], cwd=root, env=env,
                          capture_output=True, text=True)


def test_one_job_up_deploy_batch_stills_stop(tmp_path):
    root, log, env = tree(tmp_path)
    r = go(root, env)
    assert r.returncode == 0, r.stdout + r.stderr
    calls = log.read_text().splitlines()
    assert calls[0] == "batch --plan b.yaml"  # the plan, before the machine starts
    assert calls[1].startswith("up m1") and calls[2] == "make --no-print-directory deploy"
    assert calls[3] == "batch b.yaml" and calls[-1] == "run stop"
    assert "ROUND DONE 1/2" in r.stdout and "stills: 1 in" in r.stdout
    stills = next(root.glob("out/batch/t/*/stills.txt")).read_text().split()
    assert len(stills) == 1 and stills[0].endswith("01-x.png")


def test_a_rerun_skips_what_is_done(tmp_path):
    root, log, env = tree(tmp_path)
    go(root, env)
    log.write_text("")
    r = go(root, env)
    calls = log.read_text().splitlines()
    assert calls == ["run stop"], calls  # up, deploy and the batch done for this build
    assert "ROUND DONE 1/2" in r.stdout


def test_nothing_left_to_run_starts_no_machine(tmp_path):
    root, log, env = tree(tmp_path, to_run=0)
    r = go(root, env)
    assert r.returncode == 0 and "ROUND DONE nothing to run" in r.stdout
    assert log.read_text().splitlines() == ["batch --plan b.yaml"]


def test_deploy_retried_once_then_stops_the_machine(tmp_path):
    root, log, env = tree(tmp_path, deploy_fails=1)
    assert go(root, env).returncode == 0
    root2, log2, env2 = tree(tmp_path / "two", deploy_fails=2)
    r = go(root2, env2)
    assert r.returncode == 4 and "ROUND deploy FAIL" in r.stdout
    assert log2.read_text().splitlines()[-1] == "run stop"


def test_resume_goes_on_from_the_first_item_not_reached(tmp_path):
    root, log, env = tree(tmp_path, batch_items=1)
    state_dir = tmp_path / "home" / ".argonia" / "round"
    r = go(root, env)
    assert r.returncode == 0
    st = next(state_dir.glob("t.*.state"))
    st.write_text("\n".join(x for x in st.read_text().splitlines() if x != "batch OK") + "\n")  # died mid-batch
    log.write_text("")
    go(root, env)
    assert "batch --from b b.yaml" in log.read_text().splitlines()
