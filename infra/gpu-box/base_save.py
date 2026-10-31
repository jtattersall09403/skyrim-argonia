#!/usr/bin/env python3
"""The base save (chunk 0.3 §c; decision 0022): from the main menu, a new game that starts in our holding cell, the
studio character made, saved as `argoniabase`. Every scene (`bat <id>`) starts from it. Then the walk save: the
claywater scene applied and saved as `ArgoniaWalk`, the save the owner loads to walk Claywater (1.9 §1; argoniabase
itself is the black holding cell). Never committed. DEV ONLY.

    base_save.py [--name argoniabase] [--walk ArgoniaWalk]   the game at the main menu (make deploy launches it first)

The new game is started by the console's `coc ARG_HoldingCell` at the main menu, which begins a new game with the
start-game-enabled quests running and the player placed in the cell. Our start quest's own move (0.4 §b,
ARG_StartQuestScript) needs its compiled script; until the Creation Kit is installed (owner issue #15) the coc is the
move. The coc's test kit is removed. The player is Argonian from our plugin's Player override (start.json `player`, 1.10);
no setrace. The class and birthsign records wait for 1.3's setters.
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


def walk_save(b: Bridge, name: str) -> dict:
    """The owner's walk save (1.9 §1): `argoniabase` stands in the holding cell, a black room where only the HUD shows
    and nothing can be done (owner play test 3). From it the claywater scene (tests/scenes/claywater.txt, sent by
    deploy's step 5) puts the player on the Blackwood Road into Claywater Station, and the game saves that. Its proof
    is tests/journeys/walk-save.yaml (relaunch, load, walk)."""
    since = b.call("events")["last"]
    b.call("console", "bat claywater")
    for _ in range(60):  # the scene's moveto loads the road's cells: until the Loading Menu closes
        time.sleep(1)
        if any(e["data"].get("menu") == "Loading Menu" and not e["data"].get("opening")
               for e in b.call("events", since, "menu")["events"]):
            break
    time.sleep(5)  # the fade-in and the cells settling before the save
    pl = b.call("player")
    if (pl.get("cell") or {}).get("editor_id") == "ARG_HoldingCell":
        raise SystemExit("the claywater scene did not move the player out of the holding cell")
    return {"cell": pl["cell"], "save": b.call("save", name)}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--name", default="argoniabase")
    p.add_argument("--walk", default="ArgoniaWalk", help="the walk save's name ('' for none)")
    a = p.parse_args(argv)
    start = json.loads((REPO / "data" / "quarantine" / "start.json").read_text())
    cell, studio = start["cell"]["edid"], start["studio"]
    b, t0 = Bridge(), time.monotonic()
    try:
        b.call("console", f"coc {cell}")
    except BridgeError as e:  # the coc's new-game load holds the main thread past the 3 s reply (game-20, game-21 x2):
        if "did not run the task" not in str(e):  # the load goes on; the loop below waits for the cell
            raise
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
    # The race and face come from our plugin's Player override (start.json `player`, 1.10); a console setrace kept
    # the Nord default's head, hair and tints on an Argonian body (owner play test 1, item 6), so none is run.
    out["race"] = b.call("console", f"player.GetIsRace {RACES[studio['race']]}")["output"].strip()
    if not out["race"].endswith("1.00"):
        raise SystemExit(f"the new game's player is not {RACES[studio['race']]} ({out['race']}): is Argonia.esm loaded?")
    if b.call("console", "IsPC1stPerson")["output"].strip().endswith("1.00"):
        b.call("input", "key", "F", 300)  # the play camera is third person (owner, 2026-10-29)
        time.sleep(1)
    out["quest"] = b.call("quest", start["quest"]["edid"])
    out["mq101"] = b.call("quest", "MQ101")
    out["save"] = b.call("save", a.name)
    if a.walk:
        out["walk"] = walk_save(b, a.walk)
    out["seconds"] = round(time.monotonic() - t0, 1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
