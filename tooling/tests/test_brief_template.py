import subprocess
import sys
from pathlib import Path

TOOL = str(Path(__file__).resolve().parents[1] / "brief_template.py")
GOOD = """Lane: 0.1-x
Paths: tooling/
Acceptance: python3 -m pytest -q tooling/tests
Report path: /tmp/r.md
Test level: L2
Route: 3 no dependency mod or open fork covers it
Prior art: searched field notes, nothing reusable
"""


def run(*a):
    return subprocess.run([sys.executable, TOOL, *a], capture_output=True, text=True)


def brief(tmp_path, text):
    f = tmp_path / "b.md"
    f.write_text(text)
    return str(f)


def test_good_brief_passes(tmp_path):
    assert run("--check", brief(tmp_path, GOOD)).returncode == 0


def test_missing_acceptance_refused(tmp_path):
    r = run("--check", brief(tmp_path, GOOD.replace("Acceptance: python3 -m pytest -q tooling/tests\n", "")))
    assert r.returncode == 2 and "Acceptance" in r.stdout


def test_placeholder_and_vague_acceptance_refused(tmp_path):
    assert run("--check", brief(tmp_path, GOOD.replace("python3 -m pytest -q tooling/tests", "<command>"))).returncode == 2
    assert run("--check", brief(tmp_path, GOOD.replace("python3 -m pytest -q tooling/tests", "looks good"))).returncode == 2


def test_route_needs_a_why(tmp_path):
    assert run("--check", brief(tmp_path, GOOD.replace("3 no dependency mod or open fork covers it", "5"))).returncode == 2


def test_write_prints_all_fields():
    out = run("--write", "--lane", "x").stdout
    assert all(f + ":" in out for f in ("Lane", "Paths", "Acceptance", "Report path", "Test level", "Route", "Prior art"))


def test_chunk_row():
    r = run("--chunk", "0.1")
    assert r.returncode == 0 and "| 0.1 |" in r.stdout and "0.1-bootstrap.md" in r.stdout
    assert run("--chunk", "99.9").returncode == 1
