"""The world file's map step (ArgoniaPlugin NewWorldMap.cs, `nwmap apply`): the file comes out the same bytes from the
first apply as from every later one, its STAT group in one order (`nwmap selftest`: a small world file with statics of
its own and a master's planned as trees, applied three times; no game data). The LOD's keys and a built place's stamp
are read from the file, so an apply that moved bytes would make both stale."""
import os
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
DOTNET = Path.home() / ".dotnet"


def _env():
    return {**os.environ, "DOTNET_ROOT": str(DOTNET), "PATH": f"{DOTNET}:{os.environ['PATH']}",
            "DOTNET_CLI_TELEMETRY_OPTOUT": "1", "DOTNET_NOLOGO": "1"}


def test_apply_writes_the_same_file_from_its_first_run(tmp_path):
    if not DOTNET.exists():
        pytest.skip("~/.dotnet is absent")
    out = REPO / "out" / "tools" / "ArgoniaPlugin"
    b = subprocess.run(["dotnet", "build", "-c", "Release", "-o", str(out), "tools/ArgoniaPlugin"], cwd=REPO, env=_env(),
                       capture_output=True, text=True)
    assert b.returncode == 0, b.stdout[-2000:]
    r = subprocess.run(["dotnet", str(out / "ArgoniaPlugin.dll"), "nwmap", "selftest", str(tmp_path)], cwd=REPO,
                       env=_env(), capture_output=True, text=True)
    assert r.returncode == 0 and "nwmap selftest: PASS" in r.stdout, r.stdout + r.stderr
