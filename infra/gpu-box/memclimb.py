#!/usr/bin/env python3
"""The memory climb (game-9: ~230 MB per loop; game-10 wrote this loop): SkyrimSE's private bytes after each load,
three kinds of load, to find which one grows. Load-only: no journey, no input.
  A  the base save loaded (a full load)
  B  the holding cell, then Claywater's road in (two cell loads with load screens, no save)
  C  the holding cell reloaded (an interior only)
    memclimb.py [N]        N loads of each kind (default 8); run under tooling/job_guard.sh run --gpu
Prints each kind's MB after every load, the per-load deltas and their mean, then the numbers as JSON."""
import json
import pathlib
import re
import subprocess
import sys
import time

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from tools.bridge import Bridge  # noqa: E402

RUN = str(REPO / "infra" / "gpu-box" / "run.sh")


def private_mb():
    o = subprocess.run([RUN, "ps", "(Get-Process SkyrimSE).PrivateMemorySize64/1MB"], capture_output=True, text=True,
                       timeout=90).stdout
    return round(float(re.findall(r"[\d.]+", o)[-1]))


def main():
    b = Bridge()
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    out = {"A": [], "B": [], "C": []}
    for _ in range(n):
        b.call("load", "argoniabase")
        time.sleep(8)  # the load settles in game; the bridge answers before streaming ends
        out["A"].append(private_mb())
    for _ in range(n):
        b.call("console", "coc ARG_HoldingCell")
        time.sleep(6)
        b.call("console", "player.moveto ARG_Ref_ClaywaterStationRoadIn")
        time.sleep(8)
        out["B"].append(private_mb())
    for _ in range(n):
        b.call("console", "coc ARG_HoldingCell")
        time.sleep(6)
        b.call("console", "coc ARG_HoldingCell")
        time.sleep(6)
        out["C"].append(private_mb())
    for k, v in out.items():
        d = [v[i + 1] - v[i] for i in range(len(v) - 1)]
        print(k, v, "per-load MB:", d, "mean", round(sum(d) / max(1, len(d))))
    print(json.dumps(out))


if __name__ == "__main__":
    main()
