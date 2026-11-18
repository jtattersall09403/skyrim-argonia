"""The studio's offline mode in headless Chromium against a real studio server on Helstrom (docs/design/place-studio.md,
Offline): take the place offline, cut the network and stop the server, reload, edit and write a note, close and reopen
the page and find both, bring the network back, send, and find the save and the note on the server; then a save the
server moved on meanwhile, kept beside the tablet's work and never overwritten.

The server runs from this tree on a scratch copy of the place files and a scratch out/ whose caches and bundles are
links to the main tree's (nothing it writes reaches the live studio's saves). Skipped cleanly without Playwright's
Chromium or without Helstrom's bundles.
Run: ~/.argonia/venv/bin/python -m pytest -q -s tools/places/studio/web/test/test_offline.py
Env: STUDIO_OFFLINE_OUT the out/places to borrow from (default: the main tree's)."""
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import pytest

pw = pytest.importorskip("playwright.sync_api")
WEB = Path(__file__).resolve().parents[1]
REPO = WEB.parents[3]
PID = "helstrom"


def main_out() -> Path:
    if os.environ.get("STUDIO_OFFLINE_OUT"):
        return Path(os.environ["STUDIO_OFFLINE_OUT"])
    common = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=REPO, capture_output=True, text=True).stdout.strip()
    return (REPO / common).resolve().parent / "out" / "places"


SRC = main_out()
if not (SRC / "bundles" / f"ground.{PID}" / "bundle.json").exists():
    pytest.skip(f"no {PID} bundles under {SRC}", allow_module_level=True)


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Server:
    """`python -m tools.places studio` from this tree on a scratch place copy and a scratch out/."""

    def __init__(self):
        self.t = Path(tempfile.mkdtemp(prefix="studio-offline-"))
        out, places = self.t / "out", self.t / "places"
        out.mkdir()
        for e in SRC.iterdir():
            if e.name in ("bundles", "autosave", "nav") or e.name.startswith("studio-"):
                continue
            (out / e.name).symlink_to(e)
        (out / "bundles").mkdir()
        for b in (SRC / "bundles").iterdir():
            if not b.name.startswith("."):
                (out / "bundles" / b.name).symlink_to(b.resolve())
        (out / "nav").mkdir()
        if (SRC / "nav" / f"{PID}.json").exists():
            shutil.copy(SRC / "nav" / f"{PID}.json", out / "nav" / f"{PID}.json")
        shutil.copytree(REPO / "newworld" / "places" / PID, places / PID, ignore=shutil.ignore_patterns("edits"))
        self.port = free_port()
        self.url = f"http://127.0.0.1:{self.port}"
        self.env = dict(os.environ, PLACES_OUT=str(out), PLACES_DIR=str(places), STUDIO_COMMIT="0", STUDIO_BUCKET_SYNC="0",
                        STUDIO_AWAKE="0", STUDIO_ZCACHE=str(self.t / "z"), JOBS_DIR=str(self.t / "jobs"))
        self.p = None

    def start(self):
        self.p = subprocess.Popen([sys.executable, "-m", "tools.places", "studio", "--port", str(self.port)], cwd=REPO, env=self.env,
                                  stdout=open(self.t / "server.log", "ab"), stderr=subprocess.STDOUT)
        for _ in range(600):
            try:
                urllib.request.urlopen(self.url + "/api/places", timeout=60)
                return
            except OSError:
                time.sleep(0.2)
        raise RuntimeError("the studio did not start: " + (self.t / "server.log").read_text()[-2000:])

    def stop(self):
        if self.p:
            self.p.terminate()
            self.p.wait(20)
            self.p = None

    def get(self, path):
        return json.loads(urllib.request.urlopen(self.url + path, timeout=30).read())

    def put(self, path, body):
        r = urllib.request.Request(self.url + path, data=json.dumps(body).encode(), method="PUT", headers={"Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(r, timeout=30).read())


@pytest.fixture(scope="module")
def server():
    s = Server()
    s.start()
    yield s
    s.stop()
    shutil.rmtree(s.t, ignore_errors=True)


@pytest.fixture(scope="module")
def browser():
    with pw.sync_playwright() as p:
        try:
            b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        except Exception as e:  # noqa: BLE001
            pytest.skip(f"no headless Chromium: {e}")
        yield b
        b.close()


def open_page(ctx, url, choose=None):
    page = ctx.new_page()
    page.add_init_script("try { localStorage.setItem('studio.intro.v1', '1'); } catch (e) {}")
    page.goto(f"{url}/?place={PID}")
    page.wait_for_function("window.studio && studio.ready && studio.log", timeout=300000, polling=500)
    page.wait_for_timeout(500)
    if page.locator("#start .sheet").is_visible():
        if choose:
            page.get_by_role("button", name=choose).click()
        else:
            page.get_by_role("button", name="Start from the builder's draft").click()
        page.wait_for_function("document.getElementById('start').hidden", timeout=60000, polling=500)
    return page


def offline_page(ctx, url, choose=None):
    """The studio opened with no connection: the network cut for the context and, by CDP, for the page."""
    ctx.set_offline(True)
    page = ctx.new_page()
    net(ctx, page, False)
    page.add_init_script("try { localStorage.setItem('studio.intro.v1', '1'); } catch (e) {}")
    page.goto(f"{url}/?place={PID}")
    page.wait_for_function("window.studio && studio.ready && studio.log", timeout=300000, polling=500)
    page.wait_for_timeout(500)
    assert page.evaluate("import('/js/offline.js').then((m) => m.off.active)")
    if page.locator("#start .sheet").is_visible():
        page.get_by_role("button", name=choose or "Start from the builder's draft").click()
        page.wait_for_function("document.getElementById('start').hidden", timeout=60000, polling=500)
    return page


def tap(page, sel):
    """A tap on a button (by the page's own click: under software GL Playwright's wait for a steady frame can
    outlast the test while the views draw)."""
    page.wait_for_selector(sel, timeout=60000)
    page.evaluate("(s) => document.querySelector(s).click()", sel)


def net(ctx, page, on: bool):
    ctx.set_offline(not on)
    cdp = ctx.new_cdp_session(page)
    cdp.send("Network.enable")
    cdp.send("Network.emulateNetworkConditions", {"offline": not on, "latency": 0, "downloadThroughput": -1, "uploadThroughput": -1})


def take_offline(page):
    tap(page, "#offline-btn")
    page.wait_for_selector("#panel-body .offline-take")
    t0 = time.time()
    tap(page, "#panel-body .offline-take")
    page.wait_for_function("document.querySelector('#panel-body .offline-progress span')?.textContent.startsWith('Held offline')", timeout=900000, polling=500)
    took = time.time() - t0
    rec = page.evaluate(f"import('/js/offline.js').then((m) => m.off.heldFor('{PID}'))")
    return rec, took


def remove_one(page):
    """Remove the first placed thing outside (an edit the owner makes with the Select tool and Delete)."""
    rid = page.evaluate("""() => { const r = [...studio.model.spaces.exterior.refs.values()].find((x) => x.kind === 'clutter' || x.kind === 'static');
                           studio.tools.use('select'); studio.selection = new Set([r.id]); studio.tools.selectionChanged(); studio.tools.remove(); return r.id; }""")
    page.wait_for_function("document.getElementById('save-state').dataset.state === 'tablet'", timeout=30000, polling=500)
    return rid


def keep_note(page, words):
    page.evaluate("studio.panels.open('notes')")
    page.wait_for_selector("#panel-body textarea.note-text")
    page.fill("#panel-body textarea.note-text", words)
    page.get_by_role("button", name="Keep the note", exact=True).click()
    page.wait_for_function(f"[...document.querySelectorAll('#panel-body .free-notes li')].some((li) => li.textContent.includes({json.dumps(words)}))", timeout=30000, polling=500)


def unsent(page):
    return page.evaluate(f"import('/js/offline.js').then((m) => m.off.unsent('{PID}')).then((u) => u.n)")


def test_offline_round_trip(browser, server):
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, service_workers="allow")
    page = open_page(ctx, server.url)
    rec, took = take_offline(page)
    page.close()
    print(f"\nhelstrom offline: {rec['bytes'] / 1e6:.1f} MB, {rec['files']} files, {took:.1f} s on this machine (the page says {rec['seconds']} s)")
    assert rec["bytes"] > 10e6 and rec["files"] > 100
    # no connection, the build machine stopped
    # (the page is opened again rather than reloaded: after the download's 2,400 requests Playwright's own
    # bookkeeping takes about 90 s to report a reload the browser made in milliseconds)
    server.stop()
    page = offline_page(ctx, server.url)
    assert "Offline" in page.inner_text("#offline-line")
    rid = remove_one(page)
    keep_note(page, "Offline note: the well wants a roof.")
    page.close()
    # closed and opened again, still offline: both are there
    page = offline_page(ctx, server.url, choose="Continue the unsaved work")
    page.wait_for_function("studio.log.applied().length > 0", timeout=60000, polling=500)
    page.wait_for_timeout(2000)   # the save opens after its sheet closes
    ops = page.evaluate("studio.log.applied().map((o) => [o.op, o.id])")
    assert ["ref.remove", rid] in ops
    page.evaluate("studio.panels.open('notes')")
    page.wait_for_function("""(() => { const ok = [...document.querySelectorAll('#panel-body .free-notes li')].some((li) => li.textContent.includes('the well wants a roof'));
                              if (!ok && studio.panels.name !== 'notes') studio.panels.open('notes'); return ok; })()""", timeout=30000, polling=500)
    assert unsent(page) == 2
    # back online: nothing is sent until the owner chooses
    server.start()
    net(ctx, page, True)
    page.evaluate("studio.offline.probeOnce()")
    page.wait_for_function("document.getElementById('offline-line').textContent.includes('The build machine is back')", timeout=30000, polling=500)
    assert unsent(page) == 2
    tap(page, "#offline-btn")
    tap(page, "#panel-body .offline-send")
    page.wait_for_function(f"import('/js/offline.js').then((m) => m.off.unsent('{PID}')).then((u) => (window.__left = u.n)) && window.__left === 0", timeout=60000, polling=500)
    auto = server.get(f"/api/place/{PID}/saves/autosave")
    assert ["ref.remove", rid] in [[o["op"], o.get("id")] for o in auto["ops"]] and auto.get("client_token")
    notes = server.get(f"/api/place/{PID}/notes")
    assert [n["text"] for n in notes if n.get("client_id")] == ["Offline note: the well wants a roof."] and notes[-1]["sent"] is False
    # sending again stores nothing twice
    assert unsent(page) == 0 and len(server.get(f"/api/place/{PID}/notes")) == len(notes)
    assert not page.evaluate("import('/js/offline.js').then((m) => m.off.active)")
    page.close()
    ctx.close()


def test_a_save_moved_on_meanwhile_is_never_overwritten(browser, server):
    if not server.p:
        server.start()
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, service_workers="allow")
    page = open_page(ctx, server.url, choose="Continue the unsaved work")
    take_offline(page)
    page.close()
    page = offline_page(ctx, server.url, choose="Continue the unsaved work")
    assert page.evaluate("import('/js/offline.js').then((m) => m.off.active)")
    mine = remove_one(page)
    # meanwhile the server's autosave moves on (another device)
    cur = server.get(f"/api/place/{PID}/saves/autosave")
    theirs = server.put(f"/api/place/{PID}/saves/autosave", {"name": "Autosave", "ops": [], "rev": cur["rev"], "base": cur.get("base")})
    net(ctx, page, True)
    page.evaluate("studio.offline.probeOnce()")
    page.wait_for_function("document.getElementById('offline-line').textContent.includes('The build machine is back')", timeout=30000, polling=500)
    tap(page, "#offline-btn")
    tap(page, "#panel-body .offline-send")
    page.wait_for_selector("#offline-sheet .sheet", timeout=30000)
    sheet = page.inner_text("#offline-sheet")
    assert "changed while you were offline" in sheet and "Nothing has been overwritten" in sheet
    tap(page, "#offline-sheet .keep")
    page.wait_for_function(f"import('/js/offline.js').then((m) => m.off.unsent('{PID}')).then((u) => (window.__left = u.n)) && window.__left === 0", timeout=60000, polling=500)
    auto = server.get(f"/api/place/{PID}/saves/autosave")
    assert auto["rev"] == theirs["rev"] and auto["ops"] == []   # the server's own, untouched
    kept = [s for s in server.get(f"/api/place/{PID}/saves") if "-tablet-" in s["save_id"]]
    assert len(kept) == 1 and "from the tablet" in kept[0]["name"]
    full = server.get(f"/api/place/{PID}/saves/{kept[0]['save_id']}")
    assert ["ref.remove", mine] in [[o["op"], o.get("id")] for o in full["ops"]]
    page.close()
    ctx.close()
