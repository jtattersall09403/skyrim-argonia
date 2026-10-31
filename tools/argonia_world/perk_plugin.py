"""ArgoniaPerks.esp: the skill-tree perks in our words, derived on the player's machine (1.12 §4; decisions 0003, 0014).

    python -m tools.argonia_world.perk_plugin --out out/perks/argonia-perks

Reads the player's own Skyrim.esm and Dawnguard.esm from `$ARGONIA_GAME_ROOT/Data` and the perk_text table (through db.py), and
writes one PERK override per row (the master's record whole, only FULL and DESC ours) through ArgoniaGen's `perks`
command. The plugin holds the masters' records, so it is git-ignored and never shipped; stack.py stages it as its own
mod above our ESMs (installer/steps/perk-text.md).
"""
from __future__ import annotations

import argparse
import os
import subprocess
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEN = ROOT / "tools" / "ArgoniaGen" / "bin" / "Release" / "net10.0" / "ArgoniaGen"
NAME = "ArgoniaPerks.esp"


def data_dir() -> Path:
    root = os.environ.get("ARGONIA_GAME_ROOT")
    return Path(root) / "Data" if root else Path.home() / "games" / "skyrimse" / "Data"


def build(out: Path, data: Path) -> Path:
    if not (data / "Skyrim.esm").exists():
        raise SystemExit(f"perk_plugin: no Skyrim.esm under {data} (set ARGONIA_GAME_ROOT)")
    home = Path.home()
    env = dict(os.environ, DOTNET_ROOT=str(home / ".dotnet"), DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_NOLOGO="1")
    out.mkdir(parents=True, exist_ok=True)
    esp = out / NAME
    from tools.argonia_world import db  # the perk_text table, read only through db.py (0030)

    rows = out.parent / "perk_text.rows.jsonl"
    rows.write_text("".join(json.dumps({"formkey": r.formkey, "tree": r.tree, "name": r.name,
                                        "description": r.description}) + "\n" for r in db.load().rows("perk_text")))
    r = subprocess.run([str(GEN), "perks", "--in", str(rows), "--data", str(data), "--out", str(esp)],
                       cwd=ROOT, env=env, capture_output=True, text=True, check=False)
    if r.returncode != 0:
        raise SystemExit(f"perk_plugin: failed\n{(r.stdout + r.stderr)[-3000:]}")
    print(r.stdout.strip())
    return esp


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, required=True, help="the mod folder to write ArgoniaPerks.esp into")
    ap.add_argument("--data", type=Path, default=None, help="the game's Data folder (default $ARGONIA_GAME_ROOT/Data)")
    a = ap.parse_args(argv)
    build(a.out, a.data or data_dir())
    return 0


if __name__ == "__main__":
    sys.exit(main())
