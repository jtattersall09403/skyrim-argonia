"""`python -m tools.places look <place> <verb> [args]`: eyes and hands for an agent in the place studio
(docs/design/agent-view.md). Each call talks to one warm headless browser on the studio's agent view (daemon.py),
started on first use and gone when idle; prints JSON (a PNG path and/or numbers) on stdout.

Views: at <thing> [--from n|ne|e|se|s|sw|w|nw] [--eye|--high|--top]; orbit <thing>; walk <from> <to>;
section <x1,y1> <x2,y2> | section <thing> [--axis] [--slab u]; overview. Every view: [--plain] [--size WxH] [--grid] [--mesh]
[--no-canopy | --canopy] [--lit] [--ceiling u]. Every verb: [--people] draws people as named stand-ins; [--state <quest state>] sees the place as the player
does in that state of the place's states.jsonl (`python -m tools.places states <place>` lists them; none: the game's start).
Inside a room: look <place> in <room id or the name its door shows> <verb> ... (every verb; `door` is its way out).
Survey: survey [<structure or unit> ...] [--changed | --all]: a scored contact sheet per thing (--all: every unit, in
one call on one warm scene), each sheet within its time budget.
Playwalk: playwalk [<from> <to>] [--plan] [--changed] [--stride u] [--again] [--rooms]: the place walked as a player,
on its built walkable mesh: strips of every station's looks, faults of the capture and of the place told apart.
Every view says what it shows (subject seen, frame filled, occluders, capture good|failed and why) and retries a
failed capture by itself; [--helpers] shows what the game never draws, labelled; [--once] no retries; `at` [--distance k] stands k times as far; `at` [--stand x,y[,z]] stands at that point (the eye over the deck or ground under it).
Sources: look --source <source id> <view verb> [--ring <metres>] [--centre x,y] | units: a candidate source seen
as a place in its own ground, before a draft (srcview.py).
Audit: truth [<place> --sample N]: the golden scene's known answers (or a real draft sampled) held against the pictures.
Compare: versus <other place>: two places on one source from above and at eye level from four sides, one sheet.\nNumbers: probe <thing> | probe --all | probe --mesh [<a> <b>]; measure; pick <png> <px> <py> (what is drawn
there, then behind).
Hands (a scratch session, never the place files): move <thing> dx dy dz; turn <thing> deg; tilt|roll <piece> deg (about its own X: front end down | own Y); sink <thing> [units |
--until-feet-buried [--depth 8] [--force]]; delete <thing>; duplicate <thing> [dx dy] --why "<why>"; steps <deck|door> <point|thing>;
each takes --view <view verb...> for a before/after.
Paint (a stroke of the session like the hands): paint textures | paint <texture> (--circle x,y,r | --polygon
x,y;x,y;... | --stroke x,y[,pressure];...) [--brush soft|hard|scatter] [--size u] [--softness f] [--strength f]
[--seed n] --why "<why>" | paint --erase (--circle|--polygon|--stroke) ... --why "<why>" (tools/places/look/paintverb.py).
undo; snapshot <name>; restore <name>; compare <a|now> <b|now> <view verb...>; reset; status; stop.
commit -m "<why>": the session into the place files as the agent's draft edits (never over an owner's row).
release <row id> [--space <space>] -m "<why>": give a row an agent's hand placed back to the draft stages.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time

from tools.places.look.scene import LOOK_OUT

SOCK = LOOK_OUT / "daemon.sock"
PIDF = LOOK_OUT / "daemon.pid"


RESET = (ConnectionResetError, BrokenPipeError)


def kill_daemon(grace: float = 5.0) -> str:
    """The daemon of PIDF killed with its process group (its browser and studio server share it: it starts in a
    session of its own), SIGTERM then SIGKILL after `grace` seconds; the pid and socket files removed. The way
    `look stop` ends a daemon busy on a verb that never returns."""
    import signal
    try:
        pid = int(PIDF.read_text())
    except (OSError, ValueError):
        pid = None
    what = "no daemon"
    if pid:
        try:
            pg = os.getpgid(pid)
        except OSError:
            pg = None
        if pg is not None and pg == pid:   # never another group (a reused pid in this shell's group)
            for sig, wait in ((signal.SIGTERM, grace), (signal.SIGKILL, 2.0)):
                try:
                    os.killpg(pg, sig)
                except OSError:
                    break
                t = time.time()
                while time.time() - t < wait:
                    try:
                        os.kill(pid, 0)
                    except OSError:
                        break
                    try:
                        os.waitpid(pid, os.WNOHANG)
                    except ChildProcessError:
                        pass
                    time.sleep(0.1)
                else:
                    continue
                break
            what = f"look daemon {pid} and its group"
    for f in (SOCK, PIDF):
        try:
            f.unlink()
        except OSError:
            pass
    return what


def _call_once(req: dict, timeout: float) -> dict:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect(str(SOCK))
        s.sendall((json.dumps(req) + "\n").encode())
        buf = b""
        while not buf.endswith(b"\n"):
            chunk = s.recv(1 << 20)
            if not chunk:
                break
            buf += chunk
    finally:
        s.close()
    if not buf:
        raise ConnectionResetError("the look daemon closed the connection without an answer")
    return json.loads(buf)


def call(req: dict, timeout: float = 900.0) -> dict:
    """One request to the daemon; a connection reset (the daemon restarting under the call) is retried once."""
    try:
        return _call_once(req, timeout)
    except RESET:
        if req.get("verb") in ("_ping", "_stop"):
            raise
        ensure()
        return _call_once(req, timeout)


def _alive() -> bool:
    try:
        os.kill(int(PIDF.read_text()), 0)
        return True
    except (OSError, ValueError):
        return False


def ensure() -> float:
    """The daemon up; returns the seconds it took to start (0 when it was warm)."""
    try:
        call({"verb": "_ping", "place": "", "args": []}, 5)
        return 0.0
    except (OSError, ValueError):
        pass
    if SOCK.exists() and _alive():   # a daemon busy on a long call answers one request at a time: wait for it
        try:
            call({"verb": "_ping", "place": "", "args": []}, 7200)
            return 0.0
        except (OSError, ValueError):
            pass
    for _ in range(200):   # a daemon on its way out finishes first
        if not PIDF.exists():
            break
        time.sleep(0.1)
    t0 = time.time()
    from tools.places.look import daemon as _daemon
    _daemon.reap()   # what a deleted checkout left running (a studio on this checkout's port) goes first
    LOOK_OUT.mkdir(parents=True, exist_ok=True)
    log = open(LOOK_OUT / "daemon.log", "a")
    subprocess.Popen([sys.executable, "-m", "tools.places.look.daemon"], stdout=log, stderr=subprocess.STDOUT,
                     start_new_session=True, cwd=os.getcwd())
    for _ in range(1200):
        if SOCK.exists():
            try:
                call({"verb": "_ping", "place": "", "args": []}, 5)
                return time.time() - t0
            except (OSError, ValueError):
                pass
        time.sleep(0.1)
    raise SystemExit(f"the look daemon did not start: see {LOOK_OUT / 'daemon.log'}")


def main(argv: list[str]) -> int:
    if argv and argv[0] == "--source":   # a source place by itself, read-only (srcview.py)
        from tools.places.look import srcview
        return srcview.main(argv[1:])
    if argv and argv[0] == "truth":   # the audit of the tool itself: look truth [<place> --sample N]
        from tools.places.look import truth
        return truth.main(argv[1:])
    if not argv or argv[0] in ("-h", "--help") or (len(argv) < 2 and argv[0] != "stop"):
        print(__doc__)
        return 0 if argv else 2
    if argv[0] == "stop":
        from tools.places.look import daemon
        for line in daemon.reap():   # daemons of checkouts that are gone
            print(f"stopped {line}")
        try:
            call({"verb": "_stop", "place": "", "args": []}, 10)
        except OSError:
            pass
        for _ in range(50):   # gone, browser and server with it
            if not PIDF.exists():
                break
            time.sleep(0.1)
        if PIDF.exists():   # busy on a long verb (it reads the next request only after it): its whole group goes
            print(f"stopped {kill_daemon()}")
        return 0
    place, verb, args = argv[0], argv[1], argv[2:]
    started = ensure()
    if verb == "versus":   # two places on one source, the same views on one sheet (look/versus.py)
        from tools.places.look import versus
        if not args:
            raise SystemExit("look <place> versus <other place>")
        out = versus.run(place, args[0], lambda p, v, a: call({"place": p, "verb": v, "args": a}, 900.0))
        print(json.dumps(out, indent=1))
        return 0
    t0 = time.time()
    long = 6 * 3600.0 if "--all" in args else 7200.0   # a survey of every unit: about a minute a sheet
    out = call({"place": place, "verb": verb, "args": args}, long if {"playwalk", "survey"} & {verb, *args[:2]} else 900.0)
    out["wall_s"] = round(time.time() - t0, 2)
    if "playwalk" in (verb, *args[:2]) and out.get("ok") and (out.get("lines") or out.get("plan")):   # the plan and each route, one line each
        print("\n".join(out.get("plan") or out["lines"]))
        print(json.dumps({k: v for k, v in out.items() if k not in ("lines", "plan", "trace")}, indent=1))
        return 0
    if verb == "measure" and out.get("ok"):   # the table as text
        print(out["text"], end="")
        return 0
    if verb == "survey" and out.get("ok"):   # one line per structure: its sheet and its failed tiles
        print("\n".join(out["lines"]) + f"\n({out['total_s']} s)")
        return 0
    if started:
        out["daemon_start_s"] = round(started, 1)
    print(json.dumps(out, indent=1))
    return 0 if out.get("ok") else 1
