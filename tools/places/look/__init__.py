"""`python -m tools.places look <place> <verb> [args]`: eyes and hands for an agent in the place studio
(docs/design/agent-view.md). Each call talks to one warm headless browser on the studio's agent view (daemon.py),
started on first use and gone when idle; prints JSON (a PNG path and/or numbers) on stdout.

Views: at <thing> [--from n|ne|e|se|s|sw|w|nw] [--eye|--high|--top]; orbit <thing>; walk <from> <to>;
section <x1,y1> <x2,y2> | section <thing> [--axis] [--slab u]; overview. Every view: [--plain] [--size WxH].
Numbers: probe <thing> | probe --all; pick <png> <px> <py>.
Hands (a scratch session, never the place files): move <thing> dx dy dz; turn <thing> deg; sink <thing> [units |
--until-feet-buried]; delete <thing>; duplicate <thing> [dx dy]; each takes --view <view verb...> for a before/after.
undo; snapshot <name>; restore <name>; compare <a|now> <b|now> <view verb...>; reset; status; stop.
commit -m "<why>": the session into the place files as the agent's draft edits (never over an owner's row).
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


def call(req: dict, timeout: float = 900.0) -> dict:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect(str(SOCK))
    s.sendall((json.dumps(req) + "\n").encode())
    buf = b""
    while not buf.endswith(b"\n"):
        chunk = s.recv(1 << 20)
        if not chunk:
            break
        buf += chunk
    s.close()
    return json.loads(buf)


def ensure() -> float:
    """The daemon up; returns the seconds it took to start (0 when it was warm)."""
    try:
        call({"verb": "_ping", "place": "", "args": []}, 5)
        return 0.0
    except (OSError, ValueError):
        pass
    for _ in range(200):   # a daemon on its way out finishes first
        if not PIDF.exists():
            break
        time.sleep(0.1)
    t0 = time.time()
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
    if not argv or argv[0] in ("-h", "--help") or (len(argv) < 2 and argv[0] != "stop"):
        print(__doc__)
        return 0 if argv else 2
    if argv[0] == "stop":
        try:
            call({"verb": "_stop", "place": "", "args": []}, 10)
        except OSError:
            pass
        for _ in range(200):   # gone, browser and server with it
            if not PIDF.exists():
                break
            time.sleep(0.1)
        return 0
    place, verb, args = argv[0], argv[1], argv[2:]
    started = ensure()
    t0 = time.time()
    out = call({"place": place, "verb": verb, "args": args})
    out["wall_s"] = round(time.time() - t0, 2)
    if started:
        out["daemon_start_s"] = round(started, 1)
    print(json.dumps(out, indent=1))
    return 0 if out.get("ok") else 1
