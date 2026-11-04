import argparse
import sys
from pathlib import Path

from tools.argonia_world.meshes import patch

ap = argparse.ArgumentParser(prog="python3 -m tools.argonia_world.meshes")
sub = ap.add_subparsers(dest="cmd", required=True)
p = sub.add_parser("patch", help="apply data/mesh-patches.yaml to the source mods' meshes")
g = p.add_mutually_exclusive_group(required=True)
g.add_argument("--check", action="store_true", help="before/after per entry, in memory; exit 1 on any bar")
g.add_argument("--out", type=Path, help="write the patched copies into this derived mod folder")
g.add_argument("--list", action="store_true", help="the files the lay step writes, and from where")
p.add_argument("--mods", type=Path, action="append", help="a staged mods root (repeatable; default the stack's)")
a = ap.parse_args()
mods = a.mods or [patch.MODS]
if a.list:
    sys.exit(patch.listing())
sys.exit(patch.run(mods, out=a.out))
