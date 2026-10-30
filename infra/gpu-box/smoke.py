#!/usr/bin/env python3
"""The 0.2 smoke checks on the game machine, driven from the build VM (chunk 0.2 §c), through tools/bridge.py
(0.3's ArgoniaBridge): the real pad by pad.ps1 (a virtual Xbox 360 pad), real keys by the bridge's `input`, state
and events read by the bridge, a still per step. Results and stills go to ~/.argonia/stack/smoke/<stamp>/.

    smoke.py launch [--save argoniariverwood] [--fresh]   kill any zombie, start to the main menu, load the save
    smoke.py dodge                              a roll in 8 directions and a backstep: distance by position
    smoke.py pad                                RT power attack, LB block, RS lock-on (TDM)
    smoke.py menus                              every menu opened by its key, a still each (the paper-theme check)
    smoke.py scene [--save ...]                 the smoke scene: load, walk, draw, swing, roll, block, lock on, swim,
                                                the menus; the crash and Papyrus logs read after
    smoke.py frametime [--label cs-on] [--seconds 60]   PresentMon over the running game, and the bridge's frame times
"""
import argparse
import json
import math
import os
import pathlib
import subprocess
import sys
import threading
import time

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from tools.bridge import Bridge, BridgeError  # noqa: E402

RUN = str(REPO / "infra" / "gpu-box" / "run.sh")
OUT = pathlib.Path.home() / ".argonia" / "stack" / "smoke" / time.strftime("%Y%m%dT%H%M%S")
RESULTS = {}
B = Bridge()


def player():
    try:
        return B.call("player")
    except BridgeError as e:  # a cell load can hold the main thread past the bridge's 3 s once (2026-10-30)
        if "main thread" not in str(e):
            raise
        time.sleep(2)
        return B.call("player")


def console(cmd):
    return B.call("console", cmd)["output"].strip()


def still(name):
    return str(B.screenshot(OUT / f"{name}.png"))


def record(key, value):
    RESULTS[key] = value
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(json.dumps(RESULTS, indent=1))
    print(key, json.dumps(value), flush=True)


def flat(p0, p1):
    dx, dy = p1["pos"]["x"] - p0["pos"]["x"], p1["pos"]["y"] - p0["pos"]["y"]
    return round(math.hypot(dx, dy), 1), round(math.degrees(math.atan2(dx, dy)) % 360)


def cmd_launch(a):
    r = B.launch(fresh=a.fresh)
    B.call("load", a.save)
    time.sleep(4)  # the load screen fades
    p = player()
    record("launch", {"save": a.save, "cell": p["cell"], "world": p["worldspace"], "ping": r["ping"],
                      "still": still("launch")})


DIRS = {"N": (0, 1), "NE": (0.7, 0.7), "E": (1, 0), "SE": (0.7, -0.7), "S": (0, -1), "SW": (-0.7, -0.7),
        "W": (-1, 0), "NW": (-0.7, 0.7)}


STILLS = True


def dodging_sample():
    v = B.call("graph", "player", "bIsDodging")["vars"].get("bIsDodging") or {}
    return player()["pos"], bool(v.get("bool"))


def moved(seq, name, home):
    """The net move over the sequence, and the dodge's own: from the last sample before TK Dodge's bIsDodging
    graph variable goes true to the first after it falls (the walk before it left out)."""
    B.call("teleport", "pos", home["x"], home["y"], home["z"] + 8)  # every run from the same flat spot
    time.sleep(0.8)
    p0 = player()
    since = B.call("events")["last"]
    samples = [s for s in during(seq, dodging_sample, every=0.05) if not isinstance(s, str)]
    time.sleep(0.3)
    p1 = player()
    units, heading = flat(p0, p1)
    on = [i for i, (_, d) in enumerate(samples) if d]
    roll = None
    if on:
        start = samples[max(on[0] - 1, 0)][0]
        end = samples[min(on[-1] + 1, len(samples) - 1)][0] if on[-1] + 1 < len(samples) else p1["pos"]
        roll = flat({"pos": start}, {"pos": end})
    tags = [e["data"]["tag"] for e in B.call("events", since, "anim")["events"]]
    return {"units": units, "heading_deg": heading, "roll_units": roll and roll[0], "roll_heading_deg": roll and roll[1],
            "samples": len(samples), "stamina": [round(p0["stamina"]["current"], 1), round(p1["stamina"]["current"], 1)],
            "dodge_tags": sorted({t for t in tags if "odge" in t or "oll" in t}), "still": still(name) if STILLS else None}


def off_by(a, b):
    return abs((a - b + 180) % 360 - 180)


def cmd_dodge(a):
    global STILLS
    STILLS = not a.no_stills
    want = a.dirs.split(",") if a.dirs else list(DIRS) + ["back"]
    if a.cell:  # an open floor: at Riverwood a roll toward the trees ends on a trunk (setup only)
        B.call("console", f"coc {a.cell}")
        time.sleep(8)
    if a.drawn:
        B.pad("RB:120 wait:1500")  # RB on sheathed draws: the sword out, as in a fight
    home = player()["pos"]
    # TK Dodge picks the roll from the player's movement, not the stick: after 120 ms of stick the player is not yet
    # moving and every direction gave the backstep's clip (2026-10-30, AMR's log), so the stick is held 500 ms, as a
    # player moving and then dodging does, and stays held past B's release (TK Dodge reads the movement when the
    # sprint key comes up: a stick released with it gave the backstep's clip in about half the runs).
    record("walk-N", moved("+LX=0,LY=1:500 wait:100 -:1500", "walk-N", home))
    for d, (x, y) in DIRS.items():
        if d in want:
            record(f"roll-{d}", moved(f"+LX={x},LY={y}:500 B:100 wait:600 -:1200", f"roll-{d}", home))
    if "back" in want:
        record("backstep", moved("wait:300 B:100 wait:1500", "backstep", home))
    # the camera's heading is the walk's; a roll must cover ground along its stick direction, the backstep away
    # from the facing (the camera's, at rest)
    cam = RESULTS["walk-N"]["heading_deg"]
    rolls = {}
    for d, (x, y) in DIRS.items():
        r = RESULTS.get(f"roll-{d}")
        if r:
            want_h = (cam + math.degrees(math.atan2(x, y))) % 360
            rolls[d] = {"units": r["roll_units"], "heading_off": r["roll_heading_deg"] is not None
                        and off_by(r["roll_heading_deg"], want_h)}
    back = RESULTS.get("backstep", {})
    record("dodge-verdict", {"camera_deg": cam, "rolls": rolls, "backstep": back.get("roll_units"),
                             "backstep_off": back.get("roll_heading_deg") is not None and off_by(back["roll_heading_deg"], cam + 180),
                             "rolls_cover_ground": all((r["units"] or 0) > 150 for r in rolls.values()),
                             "rolls_on_their_stick": all(r["heading_off"] is not False and r["heading_off"] <= 45 for r in rolls.values()),
                             "backstep_moves": (back.get("roll_units") or 0) > 80})


def during(seq, probe, every=0.25):
    """Play a pad sequence and run `probe` repeatedly while it plays (the desktop job starts it some seconds
    after the call); the probe's results in order."""
    seen, done = [], threading.Event()

    def play():
        try:
            B.pad(seq)
        finally:
            done.set()
    t = threading.Thread(target=play)
    t.start()
    while not done.is_set():
        try:
            seen.append(probe())
        except BridgeError as e:
            seen.append(f"error: {e}")
        time.sleep(every)
    t.join()
    return seen


def yes(out):
    """A console condition's answer: `>> 1.00` for most; IsBlocking prints "... is blocking" / "is not blocking"."""
    out = str(out)
    return ">> 1" in out or (" is blocking" in out and "not blocking" not in out)


WOLF = "00023ABE"  # Skyrim.esm: Wolf, an actor base the console places (the bandit leveled list id was refused)


def cmd_pad(a):
    console("player.setav stamina 300")  # setup only: enough stamina for several attacks
    console("player.restoreav stamina 300")
    B.pad("RB:120 wait:1500")  # RB on sheathed draws, so the light attack below is an attack
    for name, seq, want in (("light-RB", "RB:120 wait:1800", "light"), ("heavy-RT", "RT:450 wait:2000", "power")):
        p0 = player()
        since = B.call("events")["last"]
        power = during(seq, lambda: console("player.IsPowerAttacking"))
        p1 = player()
        tags = [e["data"]["tag"] for e in B.call("events", since, "anim")["events"]]
        record(name, {"IsPowerAttacking_seen": any(yes(s) for s in power),
                      "attack_tags": sorted({t for t in tags if "ttack" in t or "eapon" in t}),
                      "stamina": [round(p0["stamina"]["current"], 1), round(p1["stamina"]["current"], 1)],
                      "still": still(name)})
    since = B.call("events")["last"]
    blocking = during("LB:2600", lambda: console("player.IsBlocking"))
    tags = [e["data"]["tag"] for e in B.call("events", since, "anim")["events"]]
    record("block-LB", {"IsBlocking_seen": any(yes(s) for s in blocking),
                        "block_tags": sorted({t for t in tags if "lock" in t}),
                        "released": console("player.IsBlocking")})
    # lock-on needs a target: a wolf placed by the player (setup), then RS; TDM's lock shows its reticle
    console(f"player.placeatme {WOLF} 1")
    console("tai")  # AI off for the target while the lock is read (setup); toggled back below
    time.sleep(1.0)
    B.pad("RX=0:100 RS:120 wait:900")
    record("lockon-RS", {"still": still("lockon-RS")})
    B.pad("RS:120 wait:600")
    console("tai")
    console("killall")


MENUS = [  # key, the menu the bridge's menu events name, the key that closes it
    ("I", "InventoryMenu", "I"), ("P", "MagicMenu", "P"), ("J", "Journal Menu", "J"), ("M", "MapMenu", "M"),
    ("TAB", "TweenMenu", "TAB"), ("SLASH", "StatsMenu", "ESC")]


def cmd_menus(a, tag=""):
    for key, menu, close in MENUS:
        since = B.call("events")["last"]
        B.call("input", "key", key, 120)
        try:
            B.call("wait_event", "menu", menu, 4000, since)
            opened = True
        except BridgeError:
            opened = False
        time.sleep(1.2)  # the menu's open animation
        record(f"menu-{menu}{tag}", {"opened": opened, "still": still(f"menu-{menu.replace(' ', '')}{tag}")})
        B.call("input", "key", close, 120)
        time.sleep(1.0)
        if menu == "StatsMenu":
            B.call("input", "key", "ESC", 120)  # the stats menu returns to the tween menu
            time.sleep(0.8)


def logs_after():
    out = subprocess.run([RUN, "ps", r"$s=\"$env:USERPROFILE\Documents\My Games\Skyrim Special Edition\"; "
                          r"$p = Get-ChildItem \"$s\Logs\Script\Papyrus.0.log\" -EA SilentlyContinue; "
                          r"if ($p) { 'papyrus errors: ' + @(Select-String -Path $p.FullName -Pattern 'error' ).Count } "
                          r"else { 'papyrus: no log (logging off)' }; "
                          r"@(Get-ChildItem \"$s\SKSE\crash-*.log\" | ? LastWriteTime -gt (Get-Date).AddMinutes(-30)).Count"],
                         capture_output=True, text=True)
    return out.stdout.strip().splitlines()


def cmd_scene(a, run=1):
    t0 = time.monotonic()
    B.call("load", a.save)
    time.sleep(4)
    p = player()
    home = p["pos"]
    record(f"scene{run}-load", {"cell": p["cell"]["editor_id"], "still": still(f"scene{run}-load")})
    B.pad("LY=1:1500")
    record(f"scene{run}-walk", {"units": flat(p, player())[0], "still": still(f"scene{run}-walk")})
    since = B.call("events")["last"]
    B.pad("RIGHT:120 wait:1500")  # draw (the d-pad's favourite, else the weapon readied below)
    console("player.setav stamina 300")
    console("player.restoreav stamina 300")
    if console("player.IsWeaponOut").endswith("0.00") or ">> 0" in console("player.IsWeaponOut"):
        B.pad("RB:120 wait:1500")  # RB on sheathed draws in Skyrim
    record(f"scene{run}-draw", {"weapon_out": console("player.IsWeaponOut"), "still": still(f"scene{run}-draw")})
    B.pad("RB:120 wait:1200")
    tags = [e["data"]["tag"] for e in B.call("events", since, "anim")["events"]]
    record(f"scene{run}-swing", {"attack_tags": sorted({t for t in tags if "ttack" in t})[:10]})
    r = moved("+LX=0,LY=1:500 B:100 wait:600 -:1200", f"scene{run}-roll", home)
    record(f"scene{run}-roll", r)
    blocking = during("LB:1800", lambda: console("player.IsBlocking"))
    record(f"scene{run}-block", {"IsBlocking_seen": any(yes(s) for s in blocking)})
    cmd_menus(a, tag=f"-scene{run}")
    record(f"scene{run}-logs", {"logs": logs_after(), "alive": B.health(), "seconds": round(time.monotonic() - t0)})


def cmd_scene2(a):
    for run in (1, 2):
        cmd_scene(a, run)


def cmd_frametime(a):
    """PresentMon over the running game for a.seconds (the player standing in the scene), then median and 1% low;
    the bridge's own per-frame Update intervals beside it."""
    csv = rf"C:\argonia\logs\presentmon-{a.label}.csv"
    # PresentMon's ETW session writes nothing from the SSH service session (2026-10-30): it runs in the desktop one
    out = subprocess.run([RUN, "desktop", rf"Remove-Item {csv} -EA SilentlyContinue; & C:\argonia\tools\presentmon\PresentMon.exe "
                          rf"--process_name SkyrimSE.exe --output_file {csv} --timed {a.seconds} --terminate_after_timed "
                          rf"--no_console_stats --v1_metrics 2>&1 | Select-Object -Last 5"], capture_output=True, text=True,
                         env={**os.environ, "DESKTOP_WAIT": str(a.seconds + 60)}, check=True).stdout
    OUT.mkdir(parents=True, exist_ok=True)
    local = OUT / f"presentmon-{a.label}.csv"
    if subprocess.run([RUN, "get", csv.replace("\\", "/"), str(local)], capture_output=True).returncode:
        # the bridge's frame intervals still answer the bar; PresentMon's absence is recorded beside them
        record(f"frametime-{a.label}", {"presentmon": "no CSV: " + out.strip()[-300:],
                                        "bridge": B.call("frametime", 2000), "still": still(f"frametime-{a.label}")})
        return
    rows = local.read_text().splitlines()
    head = rows[0].split(",")
    col = {n: head.index(n) for n in ("MsBetweenPresents", "msGPUActive") if n in head}
    good = [r.split(",") for r in rows[1:] if r.count(",") >= len(head) - 1]
    ft = sorted(float(r[col["MsBetweenPresents"]]) for r in good)
    gpu = sorted(float(r[col["msGPUActive"]]) for r in good) if "msGPUActive" in col else []
    med, p99 = ft[len(ft) // 2], ft[int(len(ft) * 0.99)]
    record(f"frametime-{a.label}", {"frames": len(ft), "median_ms": round(med, 2), "median_fps": round(1000 / med, 1),
                                    "p99_ms": round(p99, 2), "low1_fps": round(1000 / p99, 1),
                                    "gpu_active_median_ms": round(gpu[len(gpu) // 2], 2) if gpu else None,
                                    "bridge": B.call("frametime", 600), "still": still(f"frametime-{a.label}")})


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("launch")
    s.add_argument("--save", default="argoniariverwood")
    s.add_argument("--fresh", action="store_true")
    s = sub.add_parser("dodge")
    s.add_argument("--dirs", default="", help="a subset, e.g. back,N,E (default: all eight and the backstep)")
    s.add_argument("--no-stills", action="store_true")
    s.add_argument("--drawn", action="store_true", help="the weapon drawn first")
    s.add_argument("--cell", default="qasmoke", help="the cell to roll in (empty: where the player stands)")
    sub.add_parser("pad")
    sub.add_parser("menus")
    s = sub.add_parser("scene")
    s.add_argument("--save", default="argoniariverwood")
    f = sub.add_parser("frametime")
    f.add_argument("--label", default="cs-on")
    f.add_argument("--seconds", type=int, default=60)
    a = p.parse_args()
    {"launch": cmd_launch, "dodge": cmd_dodge, "pad": cmd_pad, "menus": cmd_menus, "scene": cmd_scene2,
     "frametime": cmd_frametime}[a.cmd](a)
    print("results:", OUT / "results.json")


if __name__ == "__main__":
    sys.exit(main())
