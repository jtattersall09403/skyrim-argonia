"""Open-side measure for cliff and rock shells the flora study could not reach (meshes then unstaged): the study's
ray test (out/newworld/research/flora_scripts/hollow_lib.py, nif.py) on meshes found as the game finds them
(tools/navmesh/meshes.Resolver). Writes out/newworld/research/hollow_extra.json: model file name -> back_by_az
(8 horizontal ray directions, 0 = mesh +X, 45 deg steps), read by place.open_sides.

    python3 -m tools.newworld.place.hollow <model> ...
"""
from __future__ import annotations

import json
import math
import sys

import numpy as np

from tools.newworld.place.place import CATALOGUE, DATA, OUT

sys.path.insert(0, str(CATALOGUE.parent / "flora_scripts"))
EXTRA = OUT / "research/hollow_extra.json"


def measure(models: list[str]) -> dict:
    import nif  # flora_scripts
    from hollow_lib import raycast_back, tris_of
    from tools.navmesh.meshes import Resolver
    from tools.navmesh import meshes
    meshes.PROFILE = "NewWorld"  # the new world's card: BM&V plus the world-asset mods
    res = Resolver(DATA)
    out = json.loads(EXTRA.read_text()) if EXTRA.exists() else {}
    for m in models:
        b = res.read(m)
        name = m.replace("\\", "/").rsplit("/", 1)[-1].lower()
        if b is None:
            out[name] = {"error": "mesh not found"}
            continue
        try:
            V, F = tris_of(nif.geometry(b))
        except Exception as e:  # a layout the study's reader does not parse
            out[name] = {"error": f"{type(e).__name__}: {e}"}
            continue
        if len(F) > 6000:
            F = F[np.random.RandomState(0).choice(len(F), 6000, replace=False)]
        dirs = [(math.cos(math.radians(a)), math.sin(math.radians(a)), 0) for a in range(0, 360, 45)]
        back, hits = [], 0
        for d in dirs:
            h, k = raycast_back(V, F, d, n=16)
            back.append(round(k / max(h, 1), 2)); hits += h
        out[name] = {"model": m, "back_by_az": back, "hits": hits} if hits else {"error": "no ray hit the mesh"}
        print(name, back, flush=True)
    EXTRA.write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    measure(sys.argv[1:])
