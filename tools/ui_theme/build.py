"""The whole UI theme overlay in one run (installer/steps/ui-theme.md steps 1-2, 0014): the font library, the
retheme and the SkyUI list sizes, all into one folder that stack.py stages above Dear Diary as `argonia-theme`.

    python -m tools.ui_theme.build --mods ~/.argonia/stack/MO2/mods --ttf Pelagiad.ttf --out out/ui_theme/argonia-theme

ui-review3: the font library had been written to a separate folder that was never staged, so every vanilla and SkyUI
menu kept Skyrim's condensed face; and SkyUI's item lists read ~10 px at 1080p from Dear Diary's config sizes.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

from tools.ui_theme import fontlib, retheme

THEMED = ("dear-diary", "wood-and-paper", "oblivion-loading-menu")  # retheme's roots, lowest priority first
CHECKED = ("dear-diary", "skyui", "wood-and-paper", "oblivion-loading-menu")
SKYUI_CONFIG = "interface/skyui/config.txt"
# SkyUI's item-list text (points in its 1280x720 movie); Dear Diary's 14 and 12 read ~10 px at 1080p (ui-review2).
LIST_SIZES = {"defaults.entry.textFormat.size": 20, "defaults.label.textFormat.size": 16}


def list_sizes(config: str, sizes: dict[str, int] = LIST_SIZES) -> tuple[str, list[str]]:
    """The SkyUI config with each named size set; the keys it did not find (a changed config) are returned."""
    missing = []
    for key, v in sizes.items():
        config, n = re.subn(rf"(?m)^(\s*{re.escape(key)}\s*=\s*)\d+", rf"\g<1>{v}", config)
        if not n:
            missing.append(key)
    return config, missing


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mods", type=Path, required=True, help="the profile's mods folder")
    ap.add_argument("--ttf", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    shutil.rmtree(a.out, ignore_errors=True)
    bad = retheme.main(["--mods", *[str(a.mods / m) for m in THEMED], "--ttf", str(a.ttf), "--out", str(a.out)])
    bad |= fontlib.main(["--ttf", str(a.ttf), "--out", str(a.out), "--check", *[str(a.mods / m) for m in CHECKED]])
    src = next((a.mods / m / SKYUI_CONFIG for m in ("dear-diary", "skyui") if (a.mods / m / SKYUI_CONFIG).exists()), None)
    if src is None:
        print("no SkyUI config.txt under dear-diary or skyui")
        return 1
    text, missing = list_sizes(src.read_text(encoding="utf-8-sig", errors="replace"))
    dest = a.out / SKYUI_CONFIG
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8", newline="")
    print(f"{dest}: list sizes {LIST_SIZES} from {src}" + (f"; missing {missing}" if missing else ""))
    return 1 if bad or missing else 0


if __name__ == "__main__":
    sys.exit(main())
