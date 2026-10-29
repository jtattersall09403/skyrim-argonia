"""L4: every ArgoniaBridge endpoint against the running game, each with a pass case and a fail-on-purpose case
(0.3 §a). Not collected by pytest (it needs the game machine); run it in a game slot:

    python3 -m tools.tests.bridge_live --save argoniariverwood [--only player,console] [--crash]

It starts from a launch to the main menu (`--no-launch` reuses a running game), checks the main-menu refusals,
loads the base save, then walks the endpoints. `--crash` ends with the forced crash and times its report, then
relaunches (which kills the zombie). Results go to out/bridge/live.json, stills to out/bridge/.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from tools.bridge import Bridge, BridgeError, GameDown, frame_difference, pad_duration_ms

OUT = Path("out/bridge")
FLAMES = "00012FCD"       # Skyrim.esm: the Flames spell, cast on the player for a hit event
SKYRIM_CLEAR = "0000081A"  # Skyrim.esm: SkyrimClear weather
STORM = "000C8220"         # Skyrim.esm: SkyrimStormRain
GAME_HOUR = "00000038"     # Skyrim.esm: the GameHour global
MQ101 = "0003372B"         # Skyrim.esm: Unbound
IRON_SWORD = "00012EB7"    # Skyrim.esm: a base record for the booth
TAMRIEL = "0000003C"
WOLF = "00023ABE"          # Skyrim.esm: Wolf (an actor base), placed to bite the player for a hit event       # a worldspace: not a bound object, not a quest, not a weather

results: list[dict] = []


def case(endpoint: str, kind: str, fn, expect_fail: bool) -> object:
    """Run one case; a fail-on-purpose case passes only when the bridge refuses it."""
    t0 = time.monotonic()
    try:
        got, refused = fn(), None
    except GameDown:
        raise
    except (BridgeError, AssertionError) as e:
        got, refused = None, str(e)
    ok = (refused is not None) if expect_fail else (refused is None)
    row = {"endpoint": endpoint, "case": kind, "expect": "refused" if expect_fail else "ok", "pass": ok,
           "ms": round((time.monotonic() - t0) * 1000), "said": refused if refused else _short(got)}
    results.append(row)
    print(("PASS " if ok else "FAIL ") + f"{endpoint:10} {kind:44} {row['ms']:6} ms  {str(row['said'])[:110]}")
    return got


def _short(v) -> str:
    s = json.dumps(v)
    return s if len(s) < 300 else s[:300] + "..."


def check(cond: bool, why: str) -> None:
    if not cond:
        raise AssertionError(why)


def at_main_menu(b: Bridge, save: str) -> None:
    case("player", "at the main menu: no player", lambda: b.call("player"), True)
    case("save", "at the main menu: nothing to save", lambda: b.call("save", "bridge-never"), True)
    case("load", "a save that does not exist", lambda: b.call("load", "no-such-save-zz"), True)
    case("load", "a path for a name", lambda: b.call("load", "..\\x"), True)
    case("load", f"the base save {save}", lambda: b.call("load", save), False)


def state(b: Bridge) -> None:
    p = case("player", "in a world", lambda: b.call("player"), False)
    check(p is not None, "no player")

    def getav():
        r = b.call("console", "player.getav", "health")
        check("health" in r["output"].lower() or ">>" in r["output"], f"no output: {r}")
        return r
    case("console", "player.getav health, with its output", getav, False)
    case("console", "a command the console refuses", lambda: b.call("console", "notacommandzz"), True)

    def save_load():
        s = b.call("save", "bridge-test")
        check(s["bytes"] > 100000, f"small save {s}")
        return {"save": s, "load": b.call("load", "bridge-test")}
    case("save", "bridge-test, then load it back", save_load, False)
    case("save", "a name with a path", lambda: b.call("save", "a/b"), True)


def world(b: Bridge) -> None:
    def step():
        p = b.call("player")["pos"]
        r = b.call("teleport", "pos", p["x"] + 128, p["y"], p["z"] + 16)
        check(abs(r["pos"]["x"] - (p["x"] + 128)) < 64, f"not moved: {r}")
        return r
    case("teleport", "pos 128 units east", step, False)
    case("teleport", "cell QASmoke", lambda: b.call("teleport", "cell", "QASmoke"), False)
    case("teleport", "a cell that does not exist", lambda: b.call("teleport", "cell", "NoSuchCellZZ"), True)
    case("time", "set 13.5 and read back", lambda: (lambda r: check(abs(r["hour"] - 13.5) < 0.05, str(r)) or r)(
        b.call("time", 13.5)), False)
    case("time", "hour 25", lambda: b.call("time", 25), True)
    case("weather", "read", lambda: b.call("weather"), False)
    case("weather", "a form that is not a weather", lambda: b.call("weather", TAMRIEL), True)
    case("quest", "MQ101 by id", lambda: b.call("quest", MQ101), False)
    case("quest", "a form that is not a quest", lambda: b.call("quest", TAMRIEL), True)
    case("global", "GameHour", lambda: b.call("global", GAME_HOUR), False)
    case("global", "a form that is not a global", lambda: b.call("global", TAMRIEL), True)
    case("av", "player health", lambda: b.call("av", "Health"), False)
    case("av", "an actor value that does not exist", lambda: b.call("av", "NoSuchValueZZ"), True)
    case("inventory", "the player's", lambda: b.call("inventory"), False)
    case("inventory", "a reference that does not exist", lambda: b.call("inventory", "FFFFFFF0"), True)


def outdoors_weather(b: Bridge, cell: str) -> None:
    """Weather needs an exterior; the base save's place is one."""
    def force():
        r = b.call("weather", STORM)
        check(r["current"]["id"] == STORM, str(r))
        return r
    case("weather", "force SkyrimStormRain outdoors", force, False)
    b.call("weather", SKYRIM_CLEAR)


def events_and_input(b: Bridge, save: str) -> None:
    # back to the base save's exterior: QASmoke (world()) streams every item of the game and held the main
    # thread past 3 s while the input cases ran there (live, 2026-10-29)
    b.call("load", save)
    time.sleep(3)
    last = b.call("events")["last"]

    def hit():
        # A spell the player casts on itself raised no hit, and the console takes no `<form id>.` prefix (live,
        # 2026-10-29): a wolf placed beside the player (setup) bites it; the hit is the real game path.
        since = b.call("events")["last"]
        b.call("console", f"player.placeatme {WOLF} 1")
        try:
            return b.call("wait_event", "hit", "00000014", 15000, since)
        finally:
            b.call("console", "killall")
    case("events", "a hit on the player (a placed wolf bites)", hit, False)


    def walk():
        since = b.call("events")["last"]
        p0 = b.call("player")["pos"]
        r = b.call("input", "key", "W", 1200)
        p1 = b.call("player")["pos"]
        moved = ((p1["x"] - p0["x"]) ** 2 + (p1["y"] - p0["y"]) ** 2) ** 0.5
        check(moved > 50, f"W for 1.2 s moved the player {moved:.0f} units")
        ev = b.call("events", since, "anim")["events"]
        check(len(ev) > 0, "no animation events while walking")
        return {"input": r, "moved": round(moved), "anim_events": len(ev), "tags": sorted({e["data"]["tag"] for e in ev})[:12]}
    case("input", "key W 1.2 s walks, with animation events", walk, False)
    # after the walk: MQ101's stage 5 starts the opening's scripts, which held the main thread past 3 s (live)
    def stage():
        since = b.call("events")["last"]
        b.call("console", f"setstage {MQ101} 5")
        return b.call("wait_event", "quest", MQ101, 5000, since)
    case("events", "a quest stage (setstage MQ101 5)", stage, False)
    case("input", "a 3.5 s hold (over the cap)", lambda: b.call("input", "key", "W", 3500), True)
    case("input", "a key that does not exist", lambda: b.call("input", "key", "NOPE", 100), True)
    case("events", "wait for an animation tag that never comes", lambda: b.call("wait_event", "anim", "NoSuchTagZZ", 800), True)
    case("events", "all since the start", lambda: {"count": len(b.call("events", last)["events"])}, False)

    def pad():
        p0 = b.call("player")["pos"]
        r = b.pad("LY=1:1500")
        p1 = b.call("player")["pos"]
        moved = ((p1["x"] - p0["x"]) ** 2 + (p1["y"] - p0["y"]) ** 2) ** 0.5
        check(moved > 50, f"the left stick for 1.5 s moved the player {moved:.0f} units")
        return {"pad": r, "moved": round(moved)}
    case("input", "pad left stick 1.5 s walks", pad, False)
    case("input", "a pad sequence over 3 s", lambda: pad_duration_ms("LY=1:2000 B:1500"), True)


def frames_nav_booth(b: Bridge) -> None:
    f = case("frametime", "120 frames", lambda: b.call("frametime", 120), False)
    case("frametime", "5 frames (under the minimum)", lambda: b.call("frametime", 5), True)
    if f:
        case("frametime", "a p95 budget of 0.1 ms (fails as designed)",
             lambda: check(f["p95_ms"] < 0.1, f"p95 {f['p95_ms']:.2f} ms"), True)

    def near():
        p = b.call("player")["pos"]
        return b.call("nav", "player", p["x"] + 150, p["y"] + 150, p["z"])
    case("nav", "player to a point 200 units away", near, False)

    def far():
        p = b.call("player")["pos"]
        return b.call("nav", "player", p["x"] + 900000, p["y"], p["z"])
    case("nav", "to a point off every loaded navmesh", far, True)

    def six():
        r = b.booth(IRON_SWORD, OUT)
        check(len(r["stills"]) == 6, str(r))
        d = [frame_difference(Path(r["stills"][i]), Path(r["stills"][i + 1])) for i in range(5)]
        check(min(d) > 0, f"two views gave the same frame: {d}")
        return {"placed": r["placed"], "stills": r["stills"], "view_differences": [round(x, 3) for x in d]}
    case("booth", "the iron sword from six angles", six, False)
    case("booth", "a form that is not a base object", lambda: b.call("booth", "place", TAMRIEL), True)


def oracle(b: Bridge) -> None:
    def live():
        r = b.oracle(OUT)
        check(r["live"], f"identical stills: {r}")
        return r
    r = case("screenshot", "two stills a second apart differ", live, False)
    if r:
        case("screenshot", "a still against itself (a frozen capture)",
             lambda: check(frame_difference(Path(r["a"]), Path(r["a"])) > 0, "identical"), True)


def crash(b: Bridge) -> None:
    b.call("crash", "yes-really")
    t0 = time.monotonic()
    said, ok = "the game still answered", False
    while time.monotonic() - t0 < 90:  # a dead main thread answers "did not run the task" until the health sees it
        try:
            b.call("player", timeout=90)
            break
        except GameDown as e:
            said, ok = str(e)[:400], True
            break
        except BridgeError:
            time.sleep(2)
    secs = time.monotonic() - t0
    results.append({"endpoint": "crash", "case": "forced crash reported", "pass": ok and secs <= 60,
                    "ms": round(secs * 1000), "said": said})
    print(("PASS " if ok and secs <= 60 else "FAIL ") + f"crash      reported in {secs:.1f} s: {said[:200]}")
    t1 = time.monotonic()
    r = b.launch()
    results.append({"endpoint": "crash", "case": "relaunch after the crash", "pass": bool(r.get("ping")),
                    "ms": round((time.monotonic() - t1) * 1000), "said": _short(r["killed"])})
    print(f"relaunch after the crash: {r['killed']} in {time.monotonic() - t1:.0f} s")
    # A zombie: Crash Logger's process exits by itself, so a hung game is made on purpose (its threads
    # suspended); it must be reported as down, and the relaunch must kill it.
    b.machine.helper("hang")
    t2 = time.monotonic()
    said, ok = "the hung game still answered", False
    while time.monotonic() - t2 < 90:
        try:
            b.call("ping", timeout=30)
            time.sleep(2)
        except GameDown as e:
            said, ok = str(e)[:200], True
            break
        except BridgeError:
            time.sleep(2)
    secs = time.monotonic() - t2
    results.append({"endpoint": "crash", "case": "a hung game reported", "pass": ok and secs <= 60,
                    "ms": round(secs * 1000), "said": said})
    print(("PASS " if ok and secs <= 60 else "FAIL ") + f"hung game reported in {secs:.1f} s: {said}")
    t3 = time.monotonic()
    r = b.launch()
    killed = r["killed"]
    zombie = bool(killed.get("killed")) and not killed.get("survivors")
    results.append({"endpoint": "crash", "case": "relaunch kills the zombie", "pass": zombie and bool(r.get("ping")),
                    "ms": round((time.monotonic() - t3) * 1000), "said": _short(killed)})
    print(f"relaunch over the hung game: {killed} in {time.monotonic() - t3:.0f} s")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--save", required=True)
    ap.add_argument("--no-launch", action="store_true")
    ap.add_argument("--fresh", action="store_true", help="lay the profile again before the launch")
    ap.add_argument("--crash", action="store_true")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    b = Bridge()
    if not a.no_launch:
        t0 = time.monotonic()
        r = b.launch(fresh=a.fresh)
        print(f"launched to the main menu in {time.monotonic() - t0:.0f} s; ping {r['ping']}")
    case("ping", "the plugin answers on the main thread", lambda: b.call("ping"), False)
    case("ping", "a bad token is refused", lambda: _bad_token(b), True)
    groups = {"menu": lambda: at_main_menu(b, a.save), "state": lambda: state(b), "world": lambda: world(b),
              "events": lambda: events_and_input(b, a.save), "frames": lambda: frames_nav_booth(b),
              "oracle": lambda: oracle(b)}
    only = set(a.only.split(",")) if a.only else set(groups)
    try:
        for name, g in groups.items():
            if name in only:
                g()
                if name == "state":  # the base save's exterior, before world() goes to QASmoke
                    outdoors_weather(b, "")
        if a.crash:
            crash(b)
    except GameDown as e:
        results.append({"endpoint": "-", "case": "game down mid-run", "pass": False, "said": str(e)[:600]})
        print(f"GAME DOWN: {e}")
    (OUT / "live.json").write_text(json.dumps(results, indent=1))
    bad = [r for r in results if not r["pass"]]
    print(f"{len(results) - len(bad)}/{len(results)} cases as designed; {OUT / 'live.json'}")
    return 1 if bad else 0


def _bad_token(b: Bridge):
    import socket
    b.tunnel()
    with socket.create_connection((b.host, b.port), timeout=5) as s:
        s.sendall(b"0" * 32 + b" ping\n")
        reply = json.loads(s.makefile().readline())
    if not reply.get("ok"):
        raise BridgeError(reply.get("error"))
    return reply


if __name__ == "__main__":
    raise SystemExit(main())
