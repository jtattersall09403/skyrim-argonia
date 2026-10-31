"""deploy.sh's heartbeat must not outlive the deploy holding the job's gpu.lock fd (game-21)."""
import pathlib, subprocess

def test_heartbeat_frees_the_lock_on_exit():
    sh = pathlib.Path(__file__).with_name("deploy_heartbeat.sh")
    r = subprocess.run(["bash", str(sh)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr
