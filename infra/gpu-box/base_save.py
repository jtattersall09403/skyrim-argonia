#!/usr/bin/env python3
"""The base save (chunk 0.3 §c; decision 0022): from the main menu, a new game that starts in our holding cell, the
studio character made, saved as `argoniabase`. Every scene (`bat <id>`) starts from it. Never committed. DEV ONLY.

    base_save.py [--name argoniabase]          the game at the main menu (make deploy launches it first)

The new game is started by the console's `coc ARG_HoldingCell` at the main menu, which begins a new game with the
start-game-enabled quests running and the player placed in the cell. Our start quest's own move (0.4 §b,
ARG_StartQuestScript) needs its compiled script; until the Creation Kit is installed (owner issue #15) the coc is the
move. The coc's test kit is removed. The studio character (data/quarantine/start.json `studio`) takes the Argonian race; its class and birthsign
records wait for 1.3's setters.
"""
import argparse
import json
import pathlib
import sys
import time

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from tools.bridge import Bridge, BridgeError  # noqa: E402

RACES = {"argonian": "ArgonianRace"}  # Skyrim.esm's playable race the studio character uses (start.json `studio`)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--name", default="argoniabase")
    a = p.parse_args(argv)
    start = json.loads((REPO / "data" / "quarantine" / "start.json").read_text())
    cell, studio = start["cell"]["edid"], start["studio"]
    b, t0 = Bridge(), time.monotonic()
    b.call("console", f"coc {cell}")
    for _ in range(60):  # the new game's load
        time.sleep(2)
        try:
            pl = b.call("player")
            if pl["cell"]["editor_id"] == cell:
                break
        except BridgeError:
            continue
    else:
        raise SystemExit(f"the new game did not reach {cell}")
    time.sleep(3)
    out = {"cell": cell, "new_game_s": round(time.monotonic() - t0, 1)}
    # A coc from the main menu hands the player the engine's test kit (iron armour, a sword, potions, 96.5 kg): not
    # our start, and it put a sheet-less studio character (carry 30 kg) at the overloaded tier, so no roll (game-6).
    b.call("console", "player.removeallitems")
    out["carried_kg"] = b.call("console", "player.getav inventoryweight")["output"].strip()
    out["race"] = b.call("console", f"player.setrace {RACES[studio['race']]}")["output"].strip()
    time.sleep(3)  # the race change rebuilds the player's 3D
    if b.call("console", "IsPC1stPerson")["output"].strip().endswith("1.00"):
        b.call("input", "key", "F", 300)  # the play camera is third person (owner, 2026-10-29)
        time.sleep(1)
    out["quest"] = b.call("quest", start["quest"]["edid"])
    out["mq101"] = b.call("quest", "MQ101")
    out["save"] = b.call("save", a.name)
    out["seconds"] = round(time.monotonic() - t0, 1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
