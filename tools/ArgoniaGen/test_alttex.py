"""L2: the MODS-dropped override writer (AltTextures.Write) on a synthetic master: each STAT, TREE and FLOR override
exists in our plugin with no alternate texture set while the master's keep theirs (no game data)."""
import os
import subprocess
from pathlib import Path

import pytest

GEN = Path(__file__).parent / "bin" / "Release" / "net10.0" / "ArgoniaGen"


@pytest.mark.skipif(not GEN.exists(), reason="ArgoniaGen not built")
def test_override_drops_mods(tmp_path):
    env = dict(os.environ, DOTNET_ROOT=str(Path.home() / ".dotnet"))
    r = subprocess.run([str(GEN), "alttex-selftest", "--dir", str(tmp_path)], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "3 overrides written, 0 wrong" in r.stdout
