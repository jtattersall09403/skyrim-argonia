"""The front door in stills (1.9 §2, §3; L4): the game launched to the main menu while the machine grabs the screen
about once a second, from the Bethesda intro to our main menu. The stills show whether a blank parchment beat comes
between the intro and the menu, and whether a scrolling bar shows on the menu. DEV ONLY; output in out/.

    python -m tools.ui_theme.front_door [--count 120] [--out out/front-door]     (ARGONIA_PLAY names the machine)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from tools.bridge import HELPER_REMOTE, Bridge  # noqa: E402

REMOTE = r"C:\argonia\logs\front-door"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--count", type=int, default=120)
    ap.add_argument("--out", type=Path, default=REPO / "out" / "front-door")
    a = ap.parse_args(argv)
    b = Bridge()
    b.machine.install()  # Bridge.launch's steps, with the grabs started once the profile is laid (the intro plays
    b.machine.helper("kill", timeout=90)  # only from a cold start)
    laid = b.machine.helper("prepare", timeout=900)
    # One desktop script: the grab loop started as its own process in the desktop session (Desktop Duplication needs
    # it), then the launch to the main menu; two desktop calls at once would share one scheduled task.
    loop = (f"$t0 = Get-Date; for ($i = 0; $i -lt {a.count}; $i++) {{ "
            f"$s = '{{0:D3}}-{{1:N1}}s' -f $i, ((Get-Date) - $t0).TotalSeconds; "
            f"& {HELPER_REMOTE} -Cmd grab -Out \"{REMOTE}\\$s.png\" | Out-Null; Start-Sleep -Milliseconds 400 }}")
    (REPO / "out").mkdir(exist_ok=True)
    local = REPO / "out" / "front-door-grab.ps1"
    local.write_text(loop)
    b.machine.ps(f"Remove-Item -Recurse -Force {REMOTE} -ErrorAction SilentlyContinue; New-Item -ItemType Directory {REMOTE} | Out-Null")
    from tools.bridge import _sh  # noqa: PLC0415
    _sh([b.machine.run, "put", str(local), "C:/argonia/logs/front-door-grab.ps1"], env=b.machine.env)
    menu = b.machine.desktop(r"Start-Process powershell -WindowStyle Hidden -ArgumentList '-ExecutionPolicy','Bypass','-File','C:\argonia\logs\front-door-grab.ps1'; "
                             r"$env:ARGONIA_KEEP='1'; & C:\argonia\infra\stack.ps1 menu", wait=420)
    time.sleep(10)  # a few stills of the settled menu
    b.machine.ps(f"Compress-Archive -Force {REMOTE}\\*.png {REMOTE}.zip")
    a.out.mkdir(parents=True, exist_ok=True)
    z = a.out / "front-door.zip"
    b.machine.get(REMOTE + ".zip", z)
    import zipfile
    zipfile.ZipFile(z).extractall(a.out)
    b.token(refresh=True)
    print(json.dumps({"laid": bool(laid.get("laid")), "main_menu": "MAIN-MENU OK" in menu,
                      "stills": len(list(a.out.glob("*.png"))), "out": str(a.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
