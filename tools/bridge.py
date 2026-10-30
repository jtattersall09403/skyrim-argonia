"""The one client for ArgoniaBridge, the agent's hands in the running game (DEV ONLY, chunk 0.3 §a).

Every call an agent makes into the game goes through this module, so the transport can change under it. A call
is one line `<token> <command> [args]` to the plugin's socket 127.0.0.1:47615 on the game machine, reached from
the build VM through an SSH tunnel this module keeps open; the reply is one JSON line. The token is new at every
launch and read over SSH (infra/gpu-box/bridge.ps1 token). Machine-side chores (health, kill, lay, grab) go
through infra/gpu-box/run.sh and bridge.ps1.

A crash is a failure, reported within 60 s: a call that gets no reply checks the game's health every 20 s, and a
dead process or a Crash Logger file written since this launch raises GameDown with the log's head.

    python3 tools/bridge.py player                     # {"pos": {...}, "cell": {...}, ...}
    python3 tools/bridge.py console player.getav health
    python3 tools/bridge.py save studio-a ; python3 tools/bridge.py load studio-a
    python3 tools/bridge.py launch [--fresh]           # kill any zombie, lay the DLL, start to the main menu
    python3 tools/bridge.py health | screenshot out.png | oracle | commands
    python3 tools/bridge.py pad 'LY=1:800 B:150'       # the virtual pad, at most 3 s
    python3 tools/bridge.py booth 0001A26F out/booth   # six stills of one base record

    from tools.bridge import Bridge;  b = Bridge();  b.call("player")["pos"]["z"]

    python3 tools/bridge.py --machine argonia-play-2 player   # another game machine (or ARGONIA_PLAY); default argonia-play

Exit codes: 0 ok, 1 the bridge or game said no (BridgeError), 2 the game is down (GameDown), 3 no reply in time.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUN = REPO / "infra" / "gpu-box" / "run.sh"
HELPER = REPO / "infra" / "gpu-box" / "bridge.ps1"
HELPER_REMOTE = r"C:\argonia\infra\bridge.ps1"
PORT = 47615  # kTcpPort in skse/ArgoniaBridge/protocol/bridge_protocol.h
STATE = Path.home() / ".argonia" / "bridge"
KEY = Path.home() / ".argonia" / "keys" / "argonia-play"
HEALTH_EVERY = 20.0  # seconds between health checks while a call waits: a crash is seen within 60 s
# Per-command reply caps (seconds); the plugin's own caps are a little shorter, so its error arrives first.
TIMEOUTS = {"load": 150.0, "save": 45.0, "core-suspend": 45.0, "nav": 30.0, "booth": 60.0, "input": 15.0,
            "wait_event": 70.0, "frametime": 120.0}  # 2000 frames at 20 fps is 100 s
DEFAULT_TIMEOUT = 15.0
HEARTBEAT_EVERY = 240.0  # seconds between busy-flag refreshes; idle-stop.ps1 stops after 15 idle minutes
INPUT_CAP_MS = 3000  # kInputCapMs in the plugin


def machine_name() -> str:
    return os.environ.get("ARGONIA_PLAY", "argonia-play")


def machine_index(name: str) -> int:
    """argonia-play is 0, argonia-play-N is N: the local tunnel port is PORT + this, so machines never share one."""
    return 0 if name == "argonia-play" else int(name.rsplit("-", 1)[1])


class BridgeError(Exception):
    """The bridge or the game refused or failed the call; the message is the plugin's error."""


class GameDown(BridgeError):
    """The game process is gone, hung or has written a crash log since this launch."""


class NoReply(BridgeError):
    """No reply within the call's cap while the game still looks alive."""


def _sh(args: list[str], timeout: float = 120.0, env: dict | None = None) -> str:
    p = subprocess.run(args, capture_output=True, text=True, errors="replace", timeout=timeout, env=env)
    if p.returncode != 0:
        raise BridgeError(f"{' '.join(args[:3])}: exit {p.returncode}: {(p.stderr or p.stdout).strip()[-600:]}")
    return p.stdout


def _last_json(text: str) -> dict:
    for line in reversed(text.strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            return json.loads(line)
    raise BridgeError(f"no JSON in the machine's answer: {text.strip()[-400:]}")


def valid_save_name(name: str) -> bool:
    """bridge_protocol's rule: 1..64 of [A-Za-z0-9 _-], no leading or trailing space."""
    import re
    return bool(re.fullmatch(r"[A-Za-z0-9_\- ]{1,64}", name)) and name == name.strip()


class Machine:
    """The game machine over SSH: run.sh for transport, bridge.ps1 for the chores."""

    def __init__(self, run: Path = RUN, name: str | None = None):
        self.run = str(run)
        self.name = name or machine_name()
        machine_index(self.name)  # a bad name fails here, not on the first call
        self.env = dict(os.environ, ARGONIA_PLAY=self.name)

    def ps(self, script: str, timeout: float = 120.0) -> str:
        return _sh([self.run, "ps", script], timeout, env=self.env)

    def install(self) -> None:
        _sh([self.run, "put", str(HELPER), HELPER_REMOTE.replace("\\", "/")], env=self.env)

    def helper(self, cmd: str, *args: str, timeout: float = 120.0) -> dict:
        line = f"powershell -ExecutionPolicy Bypass -File {HELPER_REMOTE} -Cmd {cmd} {' '.join(args)}"
        # A helper that exits 1 still printed its JSON, so the exit code is not read here.
        p = subprocess.run([self.run, "ps", f"if (Test-Path {HELPER_REMOTE}) {{ {line} }} else {{ 'NO-HELPER' }}"],
                           capture_output=True, text=True, errors="replace", timeout=timeout, env=self.env)
        out = p.stdout + p.stderr
        if "NO-HELPER" in out:
            self.install()
            return self.helper(cmd, *args, timeout=timeout)
        return _last_json(out)

    def desktop(self, script: str, wait: int = 240) -> str:
        env = dict(self.env, DESKTOP_WAIT=str(wait))
        return _sh([self.run, "desktop", script], timeout=wait + 60, env=env)

    def get(self, remote: str, local: Path) -> None:
        _sh([self.run, "get", remote.replace("\\", "/"), str(local)], env=self.env)

    def ip(self) -> str:
        return _sh([self.run, "ip"], timeout=60, env=self.env).strip()


class Bridge:
    def __init__(self, machine: Machine | None = None, port: int | None = None, host: str = "127.0.0.1"):
        self.machine = machine or Machine()
        name = getattr(self.machine, "name", "argonia-play")
        port = PORT + machine_index(name) if port is None else port
        self.state = STATE if name == "argonia-play" else STATE.with_name(f"{STATE.name}-{name}")
        self.host, self.port = host, port
        self._token: str | None = None

    # -- transport -------------------------------------------------------------------------------------------
    def tunnel(self) -> None:
        """An `ssh -L` from this port to the machine's loopback port, started once and left running."""
        if self._port_open():
            return
        ssh = ["ssh", "-i", str(KEY), "-o", "StrictHostKeyChecking=accept-new", "-o", "BatchMode=yes",
               "-o", "ExitOnForwardFailure=yes", "-o", "ServerAliveInterval=30", "-f", "-N",
               "-L", f"{self.host}:{self.port}:127.0.0.1:{PORT}", f"Administrator@{self.machine.ip()}"]
        _sh(ssh, timeout=30)
        for _ in range(20):
            if self._port_open():
                return
            time.sleep(0.25)
        raise BridgeError(f"the SSH tunnel to port {PORT} did not open")

    def _port_open(self) -> bool:
        try:
            with socket.create_connection((self.host, self.port), timeout=1):
                return True
        except OSError:
            return False

    def token(self, refresh: bool = False) -> str:
        cache = self.state / "token"
        if self._token and not refresh:
            return self._token
        if not refresh and cache.exists():
            self._token = cache.read_text().strip()
            return self._token
        t = self.machine.helper("token").get("token", "")
        if not t:
            raise GameDown("no ArgoniaBridge.token: the game has not been launched with the plugin")
        self.state.mkdir(parents=True, exist_ok=True)
        cache.write_text(t)
        self._token = t
        return t

    def _exchange(self, line: str, cap: float) -> dict:
        """Send one line; wait for one reply line, checking the game's health every HEALTH_EVERY seconds."""
        with socket.create_connection((self.host, self.port), timeout=5) as s:
            s.sendall(line.encode() + b"\n")
            buf, start = b"", time.monotonic()
            while b"\n" not in buf:
                left = cap - (time.monotonic() - start)
                if left <= 0:
                    self._raise_if_down()
                    raise NoReply(f"no reply to `{line.split(' ', 1)[1][:80]}` within {cap:.0f} s")
                s.settimeout(min(HEALTH_EVERY, left))
                try:
                    chunk = s.recv(65536)
                except socket.timeout:
                    self._raise_if_down()
                    continue
                if not chunk:  # the far end closed: the plugin is not serving (not loaded, or the game died)
                    self._raise_if_down()
                    raise GameDown("the bridge closed the connection without a reply (is the game running?)")
                buf += chunk
        return json.loads(buf.split(b"\n", 1)[0])

    # -- calls -----------------------------------------------------------------------------------------------
    def call(self, command: str, *args, timeout: float | None = None) -> dict:
        """One endpoint call; its `result` on success, else BridgeError (GameDown when the game is down)."""
        self.tunnel()
        self.heartbeat()
        cap = timeout or TIMEOUTS.get(command, DEFAULT_TIMEOUT)
        words = " ".join(str(a) for a in args)
        if command in ("console", "teleport") and "ARG_" in words:  # the game keeps no ref's editor id (tools/ref_ids.py)
            words = self.resolve_refs(words)
        tail = f" {command}" + (f" {words}" if words else "")  # never str.format: a view intent's JSON has braces
        if "\n" in tail or "\r" in tail:
            raise BridgeError(f"{command}: a request is one line")
        reply = self._exchange(self.token() + tail, cap)
        if not reply.get("ok") and reply.get("error") == "bad token":  # a new launch: read its token once
            reply = self._exchange(self.token(refresh=True) + tail, cap)
        if not reply.get("ok"):
            if "did not run the task" in str(reply.get("error")):  # a stalled or crashed main thread
                self._raise_if_down()
            raise BridgeError(f"{command}: {reply.get('error')}")
        return reply.get("result")

    def resolve_refs(self, text: str) -> str:
        """Every ref's editor id in the text as its runtime id (tools/ref_ids.py), for this launch's load order."""
        if getattr(self, "_ref_fix", (None,))[0] != self.token():
            if str(REPO) not in sys.path:
                sys.path.insert(0, str(REPO))
            from tools import ref_ids
            self._ref_fix = (self.token(), ref_ids.resolver(lambda p: self.call("plugin", p)["prefix"]))
        return "\n".join(self._ref_fix[1](line) for line in text.split("\n"))

    def heartbeat(self) -> None:
        """Refresh the machine's busy flag (C:\\argonia\\state\\busy, which idle-stop.ps1 reads) at most every
        HEARTBEAT_EVERY seconds, in the background: bridge calls made outside `job_guard --gpu` did not, and idle-stop
        stopped the machine mid-lane (game-5, 2026-10-30)."""
        stamp = self.state / "heartbeat"
        try:
            if time.time() - stamp.stat().st_mtime < HEARTBEAT_EVERY:
                return
        except OSError:
            pass
        self.state.mkdir(parents=True, exist_ok=True)
        stamp.touch()
        run = getattr(self.machine, "run", None)
        if run:  # run.sh ps touches the flag before its command
            subprocess.Popen([run, "ps", "$null"], env=getattr(self.machine, "env", None), stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)

    def health(self) -> dict:
        return self.machine.helper("health", timeout=60)

    def _raise_if_down(self) -> None:
        h = self.health()
        if not h.get("alive"):
            raise GameDown("SkyrimSE is not running" + (f"; crash log {h['crash_log']}:\n{h['crash_head']}"
                                                         if h.get("crash_log") else ""))
        if h.get("crash_log"):
            raise GameDown(f"Crash Logger wrote {h['crash_log']} (process {h['pid']} still up, a zombie):\n"
                           f"{h['crash_head']}")
        if h.get("responding") is False:
            raise GameDown(f"SkyrimSE {h['pid']} is not responding")

    # -- launch, screenshots ---------------------------------------------------------------------------------
    def launch(self, wait: int = 420, fresh: bool = False) -> dict:
        """Kill any running or zombie game, lay ArgoniaBridge.dll over the profile, start to the main menu
        (0.2's stack.ps1 menu, kept running) and wait for the bridge's ping."""
        self.machine.install()
        killed = self.machine.helper("kill", timeout=90)
        if killed.get("survivors"):
            raise GameDown(f"processes survived the kill: {killed['survivors']}")
        laid = self.machine.helper("prepare", *(["-Fresh"] if fresh else []), timeout=900)
        if not laid.get("laid"):
            raise BridgeError(f"the DLL was not laid: {laid}")
        out = self.machine.desktop(r"$env:ARGONIA_KEEP='1'; & C:\argonia\infra\stack.ps1 menu", wait=wait)
        if "MAIN-MENU OK" not in out:
            raise GameDown(f"the game did not reach the main menu:\n{out.strip()[-1500:]}")
        self.token(refresh=True)
        return {"killed": killed, "laid": laid, "ping": self.call("ping", timeout=30)}

    def screenshot(self, out: Path) -> Path:
        """One still of the game as the stream sees it (Desktop Duplication), copied to `out`."""
        remote = r"C:\argonia\logs\bridge-grab.png"
        text = self.machine.desktop(f"& {HELPER_REMOTE} -Cmd grab -Out {remote}", wait=60)
        if not _last_json(text).get("grabbed"):
            raise BridgeError(f"no still: {text.strip()[-400:]}")
        out.parent.mkdir(parents=True, exist_ok=True)
        self.machine.get(remote, out)
        return out

    def suspend_save(self, why: str = "stream_drop") -> dict:
        """ArgoniaCore's hidden suspend save (2.8 §c): the stream client's hand on a drop ("stream_drop") or a quit
        ("quit"). ArgoniaBridge's `core-suspend` messages ArgoniaCore and answers once ArgoniaSuspend.ess is written;
        any other reason is refused before it is sent."""
        if why not in ("quit", "stream_drop"):
            raise BridgeError(f"suspend_save: {why!r} is not a caller's reason (quit, stream_drop)")
        return self.call("core-suspend", why)

    CORE_NATIVES = ("Version", "SaveCount", "ViewIntent", "ViewState", "GetAttribute", "Families", "FamilyDigest",
                    "RouterLog", "GetFlag", "KnowsTopic", "GetDisposition", "JournalEntries", "RestNotice",
                    "SittingIntent", "GetVastei", "GetPendingLevels", "GetLevel", "GetSkill", "PileState", "WakePoint",
                    "SittingOpen")  # skse/core/src/bridge_call.cpp's whitelist; the plugin refuses anything else too

    def core(self, native: str, arg: str | None = None):
        """An ArgoniaCore native through ArgoniaBridge's `core` (1.7's journeys): its value. Only the reads of
        ArgoniaCore.psc and the two view intents; a setter is refused here before it is sent."""
        if native not in self.CORE_NATIVES:
            raise BridgeError(f"core: {native!r} is not a callable native (reads and view intents only)")
        r = self.call("core", native, *([] if arg is None else [arg]))
        return r["value"]

    def papyrus_queue(self) -> dict:
        """The Papyrus VM's stacks: {"stacks": running + suspended, "running", "suspended", "waiting_latent",
        "waiting_functions", "overstressed"} (the soak's queue length)."""
        return self.call("papyrus-queue")

    def running_quests(self) -> list[dict]:
        """Every running quest: [{"id", "editor_id", "plugin", "stage"}] (the quarantine journey's list)."""
        return self.call("quests")["running"]

    def music(self) -> dict:
        """The music type playing and its queue: {"current": {"id", "editor_id", "name"} | None, "queue": [...]}."""
        return self.call("music")

    def save_bytes(self, name: str = "ArgoniaRest") -> dict:
        """The sizes of Saves\\<name>.ess and its co-save <name>.skse on the machine, in bytes (0 when absent)."""
        if not valid_save_name(name):
            raise BridgeError(f"save_bytes: {name!r} is not a save name")
        out = self.machine.ps(
            "$d=\"$env:USERPROFILE\\Documents\\My Games\\Skyrim Special Edition\\Saves\"; "
            f"foreach($x in 'ess','skse'){{$f=Join-Path $d ('{name}.'+$x); "
            "if(Test-Path $f){'{0} {1}' -f $x,(Get-Item $f).Length}else{'{0} 0' -f $x}}")
        sizes = dict(ln.split() for ln in out.splitlines() if ln.strip()[:3] in ("ess", "sks"))
        if set(sizes) != {"ess", "skse"}:
            raise BridgeError(f"save_bytes: unreadable answer {out.strip()[-200:]!r}")
        return {k: int(v) for k, v in sizes.items()}

    def pad(self, seq: str) -> dict:
        """A real gamepad sequence on the virtual Xbox pad (infra/gpu-box/pad.ps1, ViGEm), capped at 3 s."""
        total = pad_duration_ms(seq)
        _sh([self.machine.run, "put", str(REPO / "infra" / "gpu-box" / "pad.ps1"), "C:/argonia/infra/pad.ps1"])
        out = self.machine.desktop(f"& C:\\argonia\\infra\\pad.ps1 -Seq '{seq}'", wait=30)
        steps = [ln for ln in out.splitlines() if ln[:2].isdigit() and ":" in ln[:3]]
        if len(steps) != len(seq.split()):
            raise BridgeError(f"pad: {len(steps)} of {len(seq.split())} steps played:\n{out.strip()[-600:]}")
        return {"ms": total, "steps": steps}

    def booth(self, form_id: str, out_dir: Path) -> dict:
        """Frame a base record from six angles: place it, a still per view, clear."""
        placed = self.call("booth", "place", form_id)
        stills = []
        try:
            for v in range(6):
                for attempt in range(10):  # the free camera starts a frame or two after it is asked for
                    try:
                        self.call("booth", "view", v)
                        break
                    except BridgeError as e:
                        if "starting" not in str(e) or attempt == 9:
                            raise
                        time.sleep(0.3)
                time.sleep(0.5)  # the frame after the move
                stills.append(str(self.screenshot(out_dir / f"booth-{form_id}-{v}.png")))
        finally:
            self.call("booth", "clear")
        return {"placed": placed, "stills": stills}

    def oracle(self, out_dir: Path, gap: float = 1.0) -> dict:
        """The screenshot oracle is live only if two stills a moment apart differ (a frozen or black capture
        gives the same frame twice)."""
        a = self.screenshot(out_dir / "oracle-a.png")
        time.sleep(gap)
        b = self.screenshot(out_dir / "oracle-b.png")
        diff = frame_difference(a, b)
        return {"a": str(a), "b": str(b), "changed_fraction": diff, "live": diff > 0.0}


def pad_duration_ms(seq: str) -> int:
    """The length of a pad.ps1 sequence; over INPUT_CAP_MS or malformed is refused (0.3 §d: inputs of at most 3 s)."""
    total = 0
    for step in seq.split():
        what, sep, ms = step.partition(":")
        if not sep or not what or not ms.isdigit():
            raise BridgeError(f"pad: a step is NAME:ms, not {step!r}")
        total += int(ms)
    if not seq.split():
        raise BridgeError("pad: an empty sequence")
    if total > INPUT_CAP_MS:
        raise BridgeError(f"pad: {total} ms is over the {INPUT_CAP_MS} ms input cap")
    return total


def frame_difference(a: Path, b: Path) -> float:
    """The fraction of pixels that differ between two stills (bytes compared when Pillow is absent)."""
    try:
        from PIL import Image, ImageChops
    except ImportError:
        return 0.0 if a.read_bytes() == b.read_bytes() else 1.0
    ia, ib = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
    if ia.size != ib.size:
        return 1.0
    d = ImageChops.difference(ia, ib).convert("L").point(lambda v: 255 if v > 8 else 0)
    return d.histogram()[255] / (ia.size[0] * ia.size[1])


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "--machine" and len(argv) > 2:
        os.environ["ARGONIA_PLAY"], argv = argv[1], argv[2:]
    b, cmd, args = Bridge(), argv[0], argv[1:]
    try:
        if cmd == "launch":
            result = b.launch(fresh="--fresh" in args)
        elif cmd == "health":
            result = b.health()
        elif cmd == "kill":
            result = b.machine.helper("kill", timeout=90)
        elif cmd == "screenshot":
            result = {"file": str(b.screenshot(Path(args[0] if args else "out/bridge/still.png")))}
        elif cmd == "pad":
            result = b.pad(" ".join(args))
        elif cmd == "booth" and args and args[0] not in ("place", "view", "clear"):
            result = b.booth(args[0], Path(args[1] if len(args) > 1 else "out/bridge"))
        elif cmd == "oracle":
            result = b.oracle(Path(args[0] if args else "out/bridge"))
            if not result["live"]:
                print(json.dumps(result))
                print("the screenshot oracle is NOT live: two stills are identical", file=sys.stderr)
                return 1
        else:
            result = b.call(cmd, *args)
    except GameDown as e:
        print(f"GAME DOWN: {e}", file=sys.stderr)
        return 2
    except NoReply as e:
        print(f"NO REPLY: {e}", file=sys.stderr)
        return 3
    except BridgeError as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
