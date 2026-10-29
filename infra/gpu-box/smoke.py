#!/usr/bin/env python3
"""The 0.2 smoke checks on the game machine, driven from the build VM (chunk 0.2 §c): the real pad buttons by
pad.ps1 (a virtual Xbox 360 pad), state read by skylink.ps1 (SkyLink AI's pipe), a still per step by grab.ps1.
Every result and still goes to ~/.argonia/stack/smoke/<stamp>/ (results.json); 0.3 turns this into the runner.

    smoke.py launch [--save ArgoniaRiverwood]   start Skyrim through SKSE (kept running) and load the save
    smoke.py dodge                              a roll in 8 directions and a backstep: distance by position
    smoke.py pad                                RT power attack, LB block, RS lock-on
    smoke.py call '<json list of SkyLink calls>'
"""
import argparse
import base64
import json
import math
import os
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
RUN = str(HERE / "run.sh")
OUT = pathlib.Path.home() / ".argonia" / "stack" / "smoke" / time.strftime("%Y%m%dT%H%M%S")
RESULTS = {}


def ps(cmd, desktop=False, wait=240):
    env = {**os.environ, "DESKTOP_WAIT": str(wait)}
    r = subprocess.run([RUN, "desktop" if desktop else "ps", cmd], text=True, capture_output=True, env=env)
    if r.returncode:
        raise SystemExit(f"run.sh failed: {r.stderr[-400:]}")
    return r.stdout


def sk(*calls, timeout_ms=8000):
    """SkyLink calls, one response each ({"success", "data"|"error"})."""
    b64 = base64.b64encode(json.dumps(list(calls)).encode()).decode()
    out = ps(rf"& C:\argonia\infra\skylink.ps1 -TimeoutMs {timeout_ms} -Calls ([Text.Encoding]::UTF8.GetString("
             rf"[Convert]::FromBase64String('{b64}')))")
    return [json.loads(l) for l in out.splitlines() if l.startswith("{")]


def console(cmd):
    (r,) = sk({"action": "execute_command", "params": {"command": cmd}})
    return r


def pad(seq):
    return ps(rf"& C:\argonia\infra\pad.ps1 -Seq '{seq}'")


def player():
    (r,) = sk({"action": "get_player_info"})
    if not r.get("success"):
        raise SystemExit(f"get_player_info: {r}")
    return r["data"]


def still(name):
    OUT.mkdir(parents=True, exist_ok=True)
    ps(rf"& C:\argonia\infra\grab.ps1 C:\argonia\logs\smoke-{name}.png | Out-Null", desktop=True, wait=60)
    subprocess.run([RUN, "get", f"C:/argonia/logs/smoke-{name}.png", str(OUT / f"{name}.png")], capture_output=True)
    return str(OUT / f"{name}.png")


def record(key, value):
    RESULTS[key] = value
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(json.dumps(RESULTS, indent=1))
    print(key, json.dumps(value))


def settle(cond, what, tries=60):
    """Wait on a game condition (a load, a menu), one SkyLink read a second, bounded."""
    for _ in range(tries):
        try:
            v = cond()
            if v:
                return v
        except (SystemExit, json.JSONDecodeError):
            pass
        time.sleep(1)
    raise SystemExit(f"{what}: not reached in {tries} s")


def cmd_launch(a):
    out = ps(r"$env:ARGONIA_KEEP = '1'; & C:\argonia\infra\stack.ps1 menu", desktop=True, wait=600)
    if "MAIN-MENU OK" not in out:
        raise SystemExit(out[-1500:])
    settle(lambda: sk({"action": "ping"})[0].get("success"), "SkyLink's pipe")
    print(sk({"action": "load_save", "params": {"saveName": a.save}}))
    p = settle(lambda: (lambda d: d if d.get("cellName") not in (None, "unknown") else None)(player()), "the save loaded")
    time.sleep(5)  # the load screen fades
    record("launch", {"save": a.save, "cell": p.get("cellName"), "world": p.get("worldspaceName"),
                      "still": still("launch")})


DIRS = {"N": (0, 1), "NE": (0.7, 0.7), "E": (1, 0), "SE": (0.7, -0.7), "S": (0, -1), "SW": (-0.7, -0.7),
        "W": (-1, 0), "NW": (-0.7, 0.7)}


def moved(seq, name):
    p0 = player()
    pad(seq)
    time.sleep(0.3)
    p1 = player()
    dx, dy = p1["posX"] - p0["posX"], p1["posY"] - p0["posY"]
    return {"units": round(math.hypot(dx, dy), 1), "heading_deg": round(math.degrees(math.atan2(dx, dy)) % 360),
            "stamina": [round(p0["stamina"], 1), round(p1["stamina"], 1)], "still": still(name)}


def cmd_dodge(a):
    # the walk alone over the same stick time is the baseline a roll must clearly beat
    record("walk-N", moved("+LX=0,LY=1:220 -:1500", "walk-N"))
    for d, (x, y) in DIRS.items():
        record(f"roll-{d}", moved(f"+LX={x},LY={y}:120 B:100 -:1500", f"roll-{d}"))
    record("backstep", moved("wait:300 B:100 wait:1500", "backstep"))


def cmd_pad(a):
    for name, seq in (("light-RB", "RB:120 wait:1500"), ("heavy-RT", "RT:120 wait:2000")):
        p0 = player()
        pad(seq.split()[0])  # the press alone, then read the attack in flight
        idle = sk({"action": "get_current_idle", "params": {"refId": "14"}})[0]
        power = console("player.IsPowerAttacking")
        attacking = console("player.IsAttacking")
        time.sleep(1.5)
        p1 = player()
        record(name, {"idle": idle.get("data"), "IsPowerAttacking": power, "IsAttacking": attacking,
                      "stamina": [round(p0["stamina"], 1), round(p1["stamina"], 1)], "still": still(name)})
    # LB held: blocking is read while it is held (pad.ps1 runs the hold in the background of this read)
    holder = subprocess.Popen([RUN, "ps", r"& C:\argonia\infra\pad.ps1 -Seq 'LB:4000'"], stdout=subprocess.DEVNULL)
    time.sleep(3.0)
    record("block-LB", {"IsBlocking": console("player.IsBlocking"), "still": still("block-LB")})
    holder.wait()
    record("block-released", {"IsBlocking": console("player.IsBlocking")})
    pad("RS:120 wait:800")
    record("lockon-RS", {"combat": sk({"action": "get_combat_state"})[0].get("data"), "still": still("lockon-RS")})
    pad("RS:120 wait:800")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("launch").add_argument("--save", default="ArgoniaRiverwood")
    sub.add_parser("dodge")
    sub.add_parser("pad")
    sub.add_parser("call").add_argument("calls")
    a = p.parse_args()
    if a.cmd == "call":
        for r in sk(*json.loads(a.calls)):
            print(json.dumps(r))
        return
    {"launch": cmd_launch, "dodge": cmd_dodge, "pad": cmd_pad}[a.cmd](a)
    print("results:", OUT / "results.json")


if __name__ == "__main__":
    sys.exit(main())
