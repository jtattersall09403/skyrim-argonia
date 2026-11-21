"""The look audit (tools/places/look/truth.py): the golden scene rendered by a look daemon of its own, every picture
held to known answers. A browser tier: run with `LOOK_TRUTH=1 pytest tools/tests/test_places_look_truth.py` (about
two minutes), or `python -m tools.places look truth`; skipped otherwise and where no browser is installed."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.skipif(not os.environ.get("LOOK_TRUTH"), reason="the browser tier: LOOK_TRUTH=1")


def test_golden_scene():
    pytest.importorskip("playwright.sync_api")
    keep = Path(tempfile.mkdtemp(prefix="look-truth-"))
    r = subprocess.run([sys.executable, "-m", "tools.places.look.truth", "--keep", str(keep)], cwd=ROOT,
                       capture_output=True, text=True, timeout=900)
    rep = json.loads((keep / "truth.json").read_text()) if (keep / "truth.json").exists() else None
    assert rep, r.stdout[-3000:] + r.stderr[-3000:]
    failed = [f"{x['group']}: {x['check']}: {x['detail']}" for x in rep["results"] if x["status"] == "FAIL"]
    assert not failed, "\n".join(failed)
    subprocess.run(["rm", "-rf", str(keep)])
