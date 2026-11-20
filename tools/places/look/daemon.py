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
from tools.places.look.scene import LOOK_OUT, LOOK_PORT, ROOT, Scene, data_out

PORT = int(os.environ.get("LOOK_PORT", LOOK_PORT))
IDLE = float(os.environ.get("LOOK_IDLE", "900"))
SOCK = LOOK_OUT / "daemon.sock"
PIDF = LOOK_OUT / "daemon.pid"
LOG = LOOK_OUT / "session.log"
W, H = 768, 576
CHROME_ARGS = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]


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

    # ---------- start and stop ----------
    def start_server(self):
        env = dict(os.environ, PLACES_OUT=str(data_out()), STUDIO_COMMIT="0", STUDIO_BUCKET_SYNC="0", STUDIO_AWAKE="0")
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
        if self.place == place and self.page is not None:
            return
        t0 = time.time()
        if self.page is not None:
            self.page.close()
        self.page = self.browser.new_page(viewport={"width": W, "height": H})
        self.page.goto(f"http://127.0.0.1:{PORT}/?place={place}&agent=1")
        self.page.wait_for_function("window.agent !== undefined", timeout=60000)
        info = self.page.evaluate("agent.ready()")
        self.place, self.page_strokes, self.space = place, [], "exterior"
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
            self.page.evaluate("(ops) => agent.push(ops)", s)
            self.page_strokes.append(s)

    def go(self, space: str) -> dict:
        """The page into a space (the exterior or a room), lit as the studio lights it."""
        if getattr(self, "space", None) != space:
            self.space_info = self.page.evaluate("(s) => agent.space(s)", space)
            self.space = space
        return getattr(self, "space_info", {})

    def scene(self, place: str, strokes, space: str = "exterior") -> Scene:
        key = (place, space, json.dumps(flat(strokes), sort_keys=True))
        if key not in self.scenes:
            if len(self.scenes) > 3:
                self.scenes.clear()
            self.scenes[key] = Scene(place, flat(strokes), space=space)
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
        from tools.places.look import verbs
        out = verbs.run(self, place, sess, verb, args)
        out["ms"] = round((time.time() - t0) * 1000)
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a") as f:
            f.write(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "place": place, "verb": verb, "args": args,
                                "png": out.get("png"), "ms": out["ms"]}) + "\n")
        return out


def _plain(o):
    """numpy numbers and flags as plain JSON."""
    return o.item() if hasattr(o, "item") else o.tolist() if hasattr(o, "tolist") else str(o)


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
        s.listen(4)
        s.settimeout(30)
        last = time.time()
        while time.time() - last < IDLE:
            try:
                conn, _ = s.accept()
            except socket.timeout:
                continue
            last = time.time()
            with conn:
                conn.settimeout(None)
                buf = b""
                while not buf.endswith(b"\n"):
                    chunk = conn.recv(65536)
                    if not chunk:
                        break
                    buf += chunk
                try:
                    req = json.loads(buf)
                    if req.get("verb") == "_ping":
                        conn.sendall(b'{"ok": true}\n')
                        continue
                    if req.get("verb") == "_stop":
                        conn.sendall(b'{"ok": true}\n')
                        break
                    out = {"ok": True, **d.handle(req)}
                except Exception as e:   # one bad call never takes the daemon down
                    import traceback
                    out = {"ok": False, "error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()[-1500:]}
                try:
                    text = json.dumps(out, default=_plain)
                except (TypeError, ValueError) as e:
                    text = json.dumps({"ok": False, "error": f"the answer would not encode: {e}"})
                conn.sendall((text + "\n").encode())
            last = time.time()
    finally:
        d.stop()
    return 0


if __name__ == "__main__":
    sys.exit(serve())
