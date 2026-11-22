"""The look daemon: one studio server of its own and one headless browser on the agent view, kept warm and serving
the look verbs over a unix socket (LOOK_OUT/daemon.sock), one request at a time. Started by the first `look` call,
gone after IDLE seconds with no call (browser and server with it). A restart picks up where it was: the session's
edits live in LOOK_OUT/<place>/session.json and are pushed into the page when it loads."""
from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from tools.places.look import draw
from tools.places.look.scene import LOOK_OUT, LOOK_PORT, ROOT, Scene, data_out, state

PORT = int(os.environ.get("LOOK_PORT", LOOK_PORT))
IDLE = float(os.environ.get("LOOK_IDLE", "1200"))   # seconds with no request: the daemon leaves
SOCK = LOOK_OUT / "daemon.sock"
PIDF = LOOK_OUT / "daemon.pid"
LOG = LOOK_OUT / "session.log"
W, H = 768, 576
CHROME_ARGS = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]


# ---------- this checkout's own data folder ----------
SKIP_OUT = {"bundles", "look", "autosave", "saves", "snapshots", "work"}


def own_out(shared: Path, mine: Path) -> Path:
    """The daemon's PLACES_OUT: the shared out/places seen through links (bundles, converted assets, catalogue), with
    its own draft bundles, so two checkouts never draw each other's working tree. Links to bundles made since are
    added at each page load."""
    (mine / "bundles").mkdir(parents=True, exist_ok=True)
    for src, dst in ((shared, mine), (shared / "bundles", mine / "bundles")):
        if not src.is_dir():
            continue
        for e in src.iterdir():
            n = e.name
            if (dst == mine and n in SKIP_OUT) or n.startswith((".", "draft.")) or (dst / n).exists() or (dst / n).is_symlink():
                continue
            try:
                (dst / n).symlink_to(e.resolve())
            except OSError:
                pass
    return mine


# ---------- the session: edits as strokes, snapshots ----------
def session_path(place: str) -> Path:
    return LOOK_OUT / place / "session.json"


def load_session(place: str) -> dict:
    p = session_path(place)
    if p.exists():
        return json.loads(p.read_text())
    return {"strokes": [], "snapshots": {}, "n": 0}


def save_session(place: str, s: dict) -> None:
    p = session_path(place)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(s, indent=1))
    os.replace(tmp, p)


def flat(strokes: list[list[dict]]) -> list[dict]:
    return [op for s in strokes for op in s]


class Daemon:
    def __init__(self):
        self.server = None
        self.pw = self.browser = self.page = None
        self.place = None
        self.page_strokes: list = []
        self.scenes: dict = {}
        self.timing: dict = {}
        self.shared_out: Path | None = None
        self.drew: dict | None = None

    # ---------- start and stop ----------
    def start_server(self):
        # the working tree as it stands (the numbers read it too), never the last commit
        env = dict(os.environ, PLACES_OUT=str(data_out()), STUDIO_COMMIT="0", STUDIO_BUCKET_SYNC="0", STUDIO_AWAKE="0",
                   PLACES_DRAFT_FROM="worktree")
        log = open(LOOK_OUT / "studio.log", "a")
        self.server = subprocess.Popen([sys.executable, "-m", "tools.places", "studio", "--port", str(PORT)], cwd=ROOT,
                                       env=env, stdout=log, stderr=subprocess.STDOUT)
        for _ in range(300):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{PORT}/", timeout=1).read(1)
                return
            except Exception:
                time.sleep(0.1)
        raise RuntimeError("the look studio server did not start (out/places/look/studio.log)")

    def start_browser(self):
        from playwright.sync_api import sync_playwright
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch(headless=True, args=CHROME_ARGS)

    def stop(self, *_):
        for f in (lambda: self.browser and self.browser.close(), lambda: self.pw and self.pw.stop()):
            try:
                f()
            except Exception:
                pass
        if self.server and self.server.poll() is None:
            self.server.terminate()
            try:
                self.server.wait(5)
            except Exception:
                self.server.kill()
        for p in (SOCK, PIDF):
            try:
                p.unlink()
            except OSError:
                pass

    # ---------- the page ----------
    def open(self, place: str):
        """The page on the place as its files stand now: reloaded whenever the place files, the commit or a bundle
        changed since it was loaded (a redraft, a stage rerun, a commit, an edit by another hand)."""
        st = state(place)
        if self.place == place and self.page is not None and st == self.drew:
            return
        if self.shared_out is not None:
            own_out(self.shared_out, data_out())
        self.scenes.clear()
        t0 = time.time()
        if self.page is not None:
            self.page.close()
        self.page = self.browser.new_page(viewport={"width": W, "height": H})
        self.page_errors = []   # the page's own errors and failed requests: reported with the next answer
        self.page.on("pageerror", lambda e: self.page_errors.append(f"page: {e}"[:300]))
        self.page.on("console", lambda m: (m.type == "error" or m.text.startswith("studio: mesh") or "Failed to parse" in m.text or (m.type == "info" and m.text.startswith("studio: ") and "texture" not in m.text)) and "Failed to load resource" not in m.text
                     and self.page_errors.append(f"console: {m.text}"[:300]))
        self.page.on("response", lambda r: r.status >= 400 and self.page_errors.append(f"{r.status}: {r.url}"[:300]))
        self.page.goto(f"http://127.0.0.1:{PORT}/?place={place}&agent=1")
        self.page.wait_for_function("window.agent !== undefined", timeout=60000)
        info = self.page.evaluate("agent.ready()")
        self.place, self.page_strokes, self.space, self.drew = place, [], "exterior", st
        self.timing["load_s"] = round(time.time() - t0, 1)
        self.timing["load_page_ms"] = info.get("ms")

    def sync(self, strokes: list[list[dict]]):
        """Bring the page's edit log to these strokes: undo what differs, push what is new."""
        k = 0
        while k < min(len(strokes), len(self.page_strokes)) and strokes[k] == self.page_strokes[k]:
            k += 1
        while len(self.page_strokes) > k:
            self.page.evaluate("agent.undo()")
            self.page_strokes.pop()
        for s in strokes[k:]:
            self.page.evaluate("([ops, bases]) => agent.push(ops, bases)", [s, self.added_bases(s)])
            self.page_strokes.append(s)

    def added_bases(self, ops: list[dict]) -> list[dict]:
        """The base rows of the pieces these ops add that only the asset catalogue holds (scene.py `fill_from_catalogue`)."""
        keys = {(op.get("ref") or {}).get("base") for op in ops if op.get("op") == "ref.add"} - {None}
        if not keys:
            return []
        from tools.places import draft_bundle
        cat = draft_bundle.catalogue()
        return [cat[k] for k in keys if k in cat]

    def go(self, space: str) -> dict:
        """The page into a space (the exterior or a room), lit as the studio lights it."""
        if getattr(self, "space", None) != space:
            self.space_info = self.page.evaluate("(s) => agent.space(s)", space)
            self.space = space
        return getattr(self, "space_info", {})

    def page_state(self) -> str | None:
        """The page shows the place in the call's quest state (`--state`), else in the game's start."""
        want = getattr(self, "qstate", None)
        return self.page.evaluate("(s) => agent.questState(s)", want)

    def scene(self, place: str, strokes, space: str = "exterior") -> Scene:
        qs = getattr(self, "qstate", None)
        key = (place, space, json.dumps(flat(strokes), sort_keys=True), json.dumps(self.drew, sort_keys=True), qs)
        if key not in self.scenes:
            if len(self.scenes) > 3:
                self.scenes.clear()
            self.scenes[key] = Scene(place, flat(strokes), space=space, state=qs)
            if space == "exterior":   # a unit's name (house.SeekhatEldersHut, dock.03) names the whole unit
                from tools.places.look import verbs
                verbs.units_aware(self.scenes[key], place)
        return self.scenes[key]

    def shot(self, cam: dict):
        r = self.page.evaluate("(c) => agent.shot(c)", cam | {"helpers": getattr(self, "helpers", False),
                                                               "fill": getattr(self, "fill", False)})
        return draw.from_data_url(r["png"]), r

    # ---------- requests ----------
    def handle(self, req: dict) -> dict:
        place, verb, args = req["place"], req["verb"], list(req.get("args") or [])
        sess = load_session(place)
        t0 = time.time()
        stamp = files_stamp(place)
        if getattr(self, "stamps", {}).get(place) != stamp:   # the place files changed under a warm daemon: reload
            self.scenes = {k: v for k, v in self.scenes.items() if k[0] != place}
            if self.place == place:
                self.place = None
            self.stamps = {**getattr(self, "stamps", {}), place: stamp}
        from tools.places.look import verbs
        out = verbs.run(self, place, sess, verb, args)
        out["ms"] = round((time.time() - t0) * 1000)
        if uncommitted(place):
            out["warning"] = ("the place files differ from the committed ones: the pictures draw what is committed, the "
                              "numbers what is in the working tree; commit the place files by path and look again")
        out["drew"] = drew_of(self, place)
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a") as f:
            f.write(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "place": place, "verb": verb, "args": args,
                                "png": out.get("png"), "ms": out["ms"]}) + "\n")
        return out


def drew_of(d, place: str) -> dict:
    """Which state an answer drew and measured: the page's state when the page stands on this place, else the place
    files' state now (an answer that drew no picture, such as `status`, still says what it read), page False."""
    if d.drew and d.place == place:
        return d.drew
    return {**state(place), "page": False}


def files_stamp(place: str, places=None) -> str:
    """What the daemon's scene and page were drawn from: the place files' sizes and times in the working tree and the
    committed tree the studio page draws (draft_bundle.committed), so a change made outside the session (a `units
    apply`, a commit, a draft stage) is never judged from a stale picture."""
    import subprocess
    from tools.places.seat import PLACES
    pdir = (places or PLACES) / place
    parts = [f"{p.relative_to(pdir)}:{p.stat().st_size}:{p.stat().st_mtime_ns}"
             for p in sorted(pdir.rglob("*.json*")) if p.is_file()] if pdir.is_dir() else []
    t = subprocess.run(["git", "-C", str(pdir), "rev-parse", "HEAD:./"], capture_output=True, text=True)
    return "|".join(parts) + "|" + (t.stdout.strip() if t.returncode == 0 else "")


def uncommitted(place: str, places=None) -> bool:
    import subprocess
    from tools.places.seat import PLACES
    pdir = (places or PLACES) / place
    t = subprocess.run(["git", "-C", str(pdir), "status", "--porcelain", "--", "."], capture_output=True, text=True)
    return t.returncode == 0 and any(ln and "agent-edits" not in ln for ln in t.stdout.splitlines())


def why_leave(d, last: float, now: float, root: Path = ROOT) -> str | None:
    """Why the daemon should leave now, or None: no request for IDLE seconds, its checkout gone, its browser or its
    studio server dead."""
    if now - last >= IDLE:
        return f"idle {now - last:.0f} s"
    if not (root / "tools" / "places").is_dir():
        return f"its checkout {root} is gone"
    if d.browser is not None and not d.browser.is_connected():
        return "its browser died"
    if d.server is not None and d.server.poll() is not None:
        return "its studio server died"
    return None


def reap(dry: bool = False) -> list[str]:
    """Every look daemon on this machine whose checkout is gone or whose working directory is deleted, killed with its
    process group (its browser and server), and every studio server left running in such a checkout (it holds the
    port the checkout's next daemon starts its own on). Run by `look stop` and the tidy."""
    out = []
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit():
            continue
        try:
            cmd = (proc / "cmdline").read_bytes().split(b"\0")
            what = "look daemon" if b"tools.places.look.daemon" in cmd else \
                "studio server" if b"tools.places" in cmd and b"studio" in cmd else None
            if what is None:
                continue
            cwd = os.readlink(proc / "cwd")
        except OSError:
            continue
        if cwd.endswith(" (deleted)") or not Path(cwd, "tools", "places").is_dir():
            out.append(f"{what} {proc.name} in {cwd}")
            if not dry:
                try:
                    os.killpg(os.getpgid(int(proc.name)), signal.SIGTERM)
                except OSError:
                    pass
    return out


def _plain(o):
    """numpy numbers and flags as plain JSON."""
    return o.item() if hasattr(o, "item") else o.tolist() if hasattr(o, "tolist") else str(o)


def _send(conn, data: bytes) -> bool:
    """Send an answer; a caller that went away first (its timeout ran out, a ping given up while a long call ran) is
    logged and skipped, never an error that takes the daemon down and resets every call queued behind it."""
    try:
        conn.sendall(data)
        return True
    except OSError as e:
        print(f"look daemon: the caller left before its answer ({type(e).__name__})", flush=True)
        return False


def answer(d, conn) -> str | None:
    """Read one request from `conn`, run it (the page reloaded first when the place files changed) and send the
    answer. Returns "stop" for `_stop`."""
    conn.settimeout(None)
    buf = b""
    try:
        while not buf.endswith(b"\n"):
            chunk = conn.recv(65536)
            if not chunk:
                break
            buf += chunk
    except OSError:
        return None
    if not buf.strip():
        return None
    try:
        req = json.loads(buf)
        if req.get("verb") == "_ping":
            _send(conn, b'{"ok": true}\n')
            return None
        if req.get("verb") == "_stop":
            _send(conn, b'{"ok": true}\n')
            return "stop"
        out = {"ok": True, **d.handle(req)}
    except Exception as e:   # one bad call never takes the daemon down
        import traceback
        out = {"ok": False, "error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()[-1500:]}
    try:
        text = json.dumps(out, default=_plain)
    except (TypeError, ValueError) as e:
        text = json.dumps({"ok": False, "error": f"the answer would not encode: {e}"})
    _send(conn, (text + "\n").encode())
    return None


def serve() -> int:
    LOOK_OUT.mkdir(parents=True, exist_ok=True)
    if PIDF.exists():
        try:
            os.kill(int(PIDF.read_text()), 0)
            print("a look daemon runs already", file=sys.stderr)
            return 1
        except (OSError, ValueError):
            pass
    PIDF.write_text(str(os.getpid()))
    d = Daemon()
    d.shared_out = data_out()
    os.environ["PLACES_OUT"] = str(own_out(d.shared_out, LOOK_OUT / "data"))
    signal.signal(signal.SIGTERM, lambda *_: (d.stop(), sys.exit(0)))
    t0 = time.time()
    try:
        d.start_server()
        d.start_browser()
        d.timing["start_s"] = round(time.time() - t0, 1)
        try:
            SOCK.unlink()
        except OSError:
            pass
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.bind(str(SOCK))
        s.listen(16)   # callers wait their turn behind a long call
        s.settimeout(30)   # a blocking wait for a request, waking every 30 s to ask whether to leave: never a busy loop
        last = time.time()
        while True:
            why = why_leave(d, last, time.time())
            if why:
                print(f"look daemon leaves: {why}", flush=True)
                break
            try:
                conn, _ = s.accept()
            except socket.timeout:
                continue
            last = time.time()
            with conn:
                if answer(d, conn) == "stop":
                    break
            last = time.time()
    finally:
        d.stop()
    return 0


if __name__ == "__main__":
    sys.exit(serve())
