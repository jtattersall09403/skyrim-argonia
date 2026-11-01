"""A loading screen in motion (1.12 lane loading; L5): the machine grabs the screen as fast as it can while the
player goes through a door, and the grabs become one clip (an animated GIF) per load. Each load can force one of
our loading screens by EditorID (the engine's sForcedLoadScreenEditorID), so two loads show two screens.
DEV ONLY; output in out/.
    python -m tools.ui_theme.load_clip --load ARG_Ref_ClaywaterStationB1Door:ARG_Load_rormasu \\
        --load ARG_Ref_ClaywaterStationB1Door:ARG_Load_travel_by_boat [--count 40] [--out out/load-clip]
A load's door is activated by the player (`<door>.activate player`); a door that leads back out works the same.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from tools.bridge import HELPER_REMOTE, Bridge, _sh  # noqa: E402

REMOTE = r"C:\argonia\logs\load-clip"


def grab_loop(count: int, remote: str) -> str:
    """PowerShell that grabs `count` stills, as fast as grab.ps1 allows, named by index and seconds since start."""
    return (f"$t0 = Get-Date; for ($i = 0; $i -lt {count}; $i++) {{ "
            f"$s = '{{0:D3}}-{{1:N1}}s' -f $i, ((Get-Date) - $t0).TotalSeconds; "
            f"& {HELPER_REMOTE} -Cmd grab -Out \"{remote}\\$s.png\" | Out-Null }}")


def to_gif(frames: list[Path], out: Path, width: int = 960) -> int:
    from PIL import Image  # noqa: PLC0415
    ims = []
    for f in frames:
        im = Image.open(f).convert("RGB")
        im = im.resize((width, round(im.height * width / im.width)))
        ims.append(im.convert("P", palette=Image.ADAPTIVE))
    if ims:
        ims[0].save(out, save_all=True, append_images=ims[1:], duration=300, loop=0)
    return len(ims)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--load", action="append", required=True, help="<door ref EditorID>:<LSCR EditorID or ->")
    ap.add_argument("--count", type=int, default=40)
    ap.add_argument("--out", type=Path, default=REPO / "out" / "load-clip")
    a = ap.parse_args(argv)
    b = Bridge()
    a.out.mkdir(parents=True, exist_ok=True)
    result = []
    for n, spec in enumerate(a.load):
        door, screen = spec.split(":", 1)
        remote = f"{REMOTE}{n}"
        if screen != "-":
            b.call("console", f'setini "sForcedLoadScreenEditorID:Interface" "{screen}"')
        local = a.out / f"grab{n}.ps1"
        local.write_text(grab_loop(a.count, remote))
        b.machine.ps(f"Remove-Item -Recurse -Force {remote}* -ErrorAction SilentlyContinue; New-Item -ItemType Directory {remote} | Out-Null")
        _sh([b.machine.run, "put", str(local), f"C:/argonia/logs/grab{n}.ps1"], env=b.machine.env)
        b.machine.desktop(r"Start-Process powershell -WindowStyle Hidden -ArgumentList '-ExecutionPolicy','Bypass','-File',"
                          rf"'C:\argonia\logs\grab{n}.ps1'", wait=60)
        time.sleep(1.5)  # a still or two of play before the door
        b.call("console", f"{door}.activate player", timeout=120)
        time.sleep(4)
        b.machine.ps(f"$n=0; while ((Get-ChildItem {remote}).Count -lt {a.count} -and $n -lt 120) {{ Start-Sleep 1; $n++ }}; "
                     f"Compress-Archive -Force {remote}\\*.png {remote}.zip", timeout=200)
        d = a.out / f"load{n}"
        d.mkdir(exist_ok=True)
        b.machine.get(remote + ".zip", d / "grabs.zip")
        zipfile.ZipFile(d / "grabs.zip").extractall(d)
        frames = sorted(d.glob("*.png"))
        gif = a.out / f"load{n}-{screen}.gif"
        result.append({"door": door, "screen": screen, "frames": to_gif(frames, gif), "clip": str(gif),
                       "player": b.call("player").get("cell")})
    if any(s.split(":", 1)[1] != "-" for s in a.load):
        b.call("console", 'setini "sForcedLoadScreenEditorID:Interface" ""')
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
