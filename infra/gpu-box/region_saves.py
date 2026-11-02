#!/usr/bin/env python3
"""Region saves for the owner's walk (1.15, owner 2026-11-02): one save per region class, the player standing at that
region's shore panel marker (the 1.15 panel's `ARG_Ref_Panel<Region>Shore` XMarkers, tools/argonia_world/panel.py),
so the owner loads a save and walks the region. Made from the walk save on the game machine; never committed.
    region_saves.py [--from ArgoniaWalk] [--only coastal-lagoon,rootland]   the game at the main menu or in game
Each save is named `Argonia <Region>` (the load menu lists them by name). A region whose marker fails to load is
reported and skipped; the others are still made. DEV ONLY.
"""
import argparse
import pathlib
import sys
import time

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from tools.bridge import Bridge, BridgeError  # noqa: E402

REGIONS = {  # panel marker suffix -> save name (the nine region classes of the 1.15 panel)
    "CoastalLagoon": "Coastal Lagoon",
    "DeepRiverCorridor": "Deep River Corridor",
    "DeepSinkBasin": "Deep Sink Basin",
    "FloodedForest": "Flooded Forest",
    "InteriorSwamp": "Interior Swamp",
    "NorthernTransition": "Northern Transition",
    "Rootland": "Rootland",
    "TidalDelta": "Tidal Delta",
    "WesternFrontier": "Western Frontier",
}


def settle(b: Bridge, since, wait: int = 90) -> None:
    """Until the Loading Menu closes (a moveto across the province loads cells), then the fade-in."""
    for _ in range(wait):
        time.sleep(1)
        try:
            if any(e["data"].get("menu") == "Loading Menu" and not e["data"].get("opening")
                   for e in b.call("events", since, "menu")["events"]):
                break
        except BridgeError:
            continue
    time.sleep(5)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--from", dest="src", default="ArgoniaWalk", help="the save to start from")
    p.add_argument("--only", default="", help="comma-separated region keys (kebab or camel case) to make")
    a = p.parse_args(argv)
    want = {k.replace("-", "").lower() for k in a.only.split(",") if k}
    b = Bridge()
    try:
        pl = b.call("player")
    except BridgeError as e:  # at the main menu the read refuses ("no player in a world"): load the walk save
        if "no player" not in str(e):
            raise
        pl = {}
    if (pl.get("cell") or {}).get("editor_id") in (None, "ARG_HoldingCell"):
        since = b.call("events")["last"]
        try:
            b.call("load", a.src)
        except BridgeError as e:  # the load holds the main thread past the reply; the settle waits for it
            if "did not run the task" not in str(e):
                raise
        settle(b, since, 150)
    made, failed = [], []
    for key, name in REGIONS.items():
        if want and key.lower() not in want:
            continue
        since = b.call("events")["last"]
        t0 = time.monotonic()
        try:
            b.call("console", f"player.moveto ARG_Ref_Panel{key}Shore")
        except BridgeError as e:
            if "did not run the task" not in str(e):
                failed.append((name, str(e)))
                continue
        settle(b, since)
        try:
            pl = b.call("player")
            ws = (pl.get("worldspace") or {}).get("editor_id")
            if ws != "ARG_Province":
                failed.append((name, f"player not in ARG_Province after the moveto: {ws}"))
                continue
            out = b.call("save", f"Argonia {name}")
        except BridgeError as e:
            failed.append((name, str(e)))
            continue
        made.append((name, pl["cell"], round(time.monotonic() - t0, 1)))
        print(f"save: Argonia {name}  cell {pl['cell']}  {made[-1][2]} s  {out}")
    for name, why in failed:
        print(f"FAILED: {name}: {why}", file=sys.stderr)
    print(f"{len(made)} saves made, {len(failed)} failed")
    return 1 if failed and not made else 0


if __name__ == "__main__":
    sys.exit(main())
