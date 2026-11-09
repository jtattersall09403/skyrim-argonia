"""The studio front end's pure JavaScript (edits mirror, xform) against the shared fixtures, under node."""
import shutil
import subprocess
from pathlib import Path

import pytest

WEB = Path(__file__).resolve().parents[1] / "places" / "studio" / "web"


@pytest.mark.skipif(not shutil.which("node"), reason="node is not installed")
def test_web_unit():
    tests = sorted(str(p) for p in (WEB / "test").glob("*.test.mjs"))
    r = subprocess.run(["node", "--test", *tests], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-2000:]
