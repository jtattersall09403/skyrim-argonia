"""The height-fog release asset has Features/ and ExponentialHeightFog/ at its root; CS only loads them under Shaders/."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "infra" / "gpu-box"))
import stack  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def test_height_fog_lays_under_shaders(tmp_path):
    rows = json.loads((ROOT / "data" / "dependencies.json").read_text())
    rows = rows["mods"]
    m = next(r for r in rows if r["id"] == "community-shaders-height-fog")
    src, data = tmp_path / "src", tmp_path / "Data"
    for rel in ("Features/ExponentialHeightFog.ini", "ExponentialHeightFog/ExponentialHeightFog.hlsl"):
        f = src / rel
        f.parent.mkdir(parents=True)
        f.write_text("x")
    data.mkdir()
    stack.place(m, src, data, tmp_path / "tools", tmp_path)
    assert (data / "Shaders/Features/ExponentialHeightFog.ini").is_file()
    assert (data / "Shaders/ExponentialHeightFog/ExponentialHeightFog.hlsl").is_file()
    assert not (data / "Features").exists() and not (data / "ExponentialHeightFog").exists()
