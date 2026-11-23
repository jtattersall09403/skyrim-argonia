"""The studio in headless Chromium at the MatePad Pro's size, with pen and touch, against the dev server.

Each test performs one of the owner's sixteen requirements and asserts on the ops it makes and the scene state.
Run: ~/.argonia/venv/bin/python -m pytest -q tools/places/studio/web/test/test_browser.py
Env: STUDIO_URL to test a running server instead (real bundles); SHOTS=<dir> to keep screenshots.
"""
import json
import re
import os
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
SHOTS = Path(os.environ["SHOTS"]) if os.environ.get("SHOTS") else None   # screenshots only when asked for: software GL draws them slowly
REAL = bool(os.environ.get("STUDIO_URL"))
REACH_OUT = os.environ.get("REACH_OUT")   # a file to append each test's measured JS reach to (the modules whose code ran)
SLOW = 5 if REAL else 1  # real bundles under software GL load in ~45 s, not ~3 s
WAIT = 90000 * SLOW   # every playwright wait: generous, for a build machine under load (each still ends on its condition)
LANDSCAPE, PORTRAIT = {"width": 1280, "height": 800}, {"width": 800, "height": 1280}  # MatePad Pro 12.6 at DPR 2


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


REPO = WEB.parents[3]


def refuse_shared_saves(url):
    """The real-data run writes saves and starts finalise: only against a server rooted in a scratch clone, whose
    autosaves and named saves land inside that clone, never the main tree's (the live studio's) out/ or place files."""
    port = int(url.rsplit(":", 1)[1].split("/")[0])
    out = subprocess.run(["ss", "-ltnpH", f"sport = :{port}"], capture_output=True, text=True).stdout
    pid = out.split("pid=")[1].split(",")[0] if "pid=" in out else None
    assert pid, f"no local process serves {url}; the real-data run only drives a studio started from a scratch clone"
    env = dict(kv.split("=", 1) for kv in Path(f"/proc/{pid}/environ").read_text().split("\0") if "=" in kv)
    root = Path(os.readlink(f"/proc/{pid}/cwd")).resolve()
    autosave = (Path(env.get("PLACES_OUT", root / "out" / "places")) / "autosave").resolve()
    main = REPO.resolve()
    assert root != main and not root.is_relative_to(main), f"the server at {url} runs in the main tree {root}"
    assert autosave.is_relative_to(root) and not autosave.is_relative_to(main / "out"), \
        f"the server at {url} would write autosaves to {autosave}, outside its clone {root}"


@pytest.fixture(scope="module", autouse=True)
def one_run_at_a_time():
    """Two runs of this suite on one machine fight for its CPU, memory and software GL: a second run waits here (as
    long as the first takes, about ten minutes) for the machine-wide lock, then runs alone."""
    import fcntl
    lock = Path.home() / ".argonia" / "state" / "studio-browser-tests.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    with open(lock, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        yield


@pytest.fixture(scope="module")
def server(one_run_at_a_time):
    if os.environ.get("STUDIO_URL"):
        url = os.environ["STUDIO_URL"].rstrip("/")
        refuse_shared_saves(url)
        yield url
        return
    fx = Path(tempfile.mkdtemp(prefix="studio-fixture-"))
    subprocess.run([sys.executable, str(WEB / "dev" / "make_fixture.py"), str(fx)], check=True, capture_output=True)
    port = free_port()
    p = subprocess.Popen([sys.executable, str(WEB / "dev" / "devserver.py"), "--port", str(port), "--fixture", str(fx)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            urllib.request.urlopen(url + "/api/status", timeout=1 * SLOW)
            break
        except OSError:
            time.sleep(0.1)
    yield url
    p.terminate()
    subprocess.run(["rm", "-rf", str(fx)])


@pytest.fixture(scope="module")
def browser():
    with pw.sync_playwright() as p:
        b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        yield b
        b.close()


class Pad:
    """A page with pen and finger input through the DevTools protocol."""

    def __init__(self, page):
        self.page, self.cdp = page, page.context.new_cdp_session(page)
        self.errors, self.beats = [], []
        page.on("pageerror", lambda e: self.errors.append(str(e)))
        page.on("request", lambda r: "/api/heartbeat" in r.url and self.beats.append(r.url))

    def ev(self, js, arg=None):
        return self.page.evaluate(js, arg)

    def pen(self, kind, x, y, pressure=0.5):
        self.cdp.send("Input.dispatchMouseEvent", {"type": kind, "x": x, "y": y, "button": "left", "buttons": 0 if kind == "mouseReleased" else 1,
                                                   "clickCount": 1, "pointerType": "pen", "force": pressure})

    def pen_tap(self, x, y):
        self.pen("mouseMoved", x, y)
        self.pen("mousePressed", x, y)
        self.pen("mouseReleased", x, y)
        self.page.wait_for_timeout(60)

    def pen_drag(self, pts, pressure=0.6, steps=4):
        self.pen("mouseMoved", *pts[0])
        self.pen("mousePressed", *pts[0], pressure)
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            for i in range(1, steps + 1):
                self.pen("mouseMoved", x0 + (x1 - x0) * i / steps, y0 + (y1 - y0) * i / steps, pressure)
        self.pen("mouseReleased", *pts[-1])
        self.page.wait_for_timeout(80)

    def touch(self, kind, pts):
        self.cdp.send("Input.dispatchTouchEvent", {"type": kind, "touchPoints": [{"x": x, "y": y, "id": i} for i, (x, y) in enumerate(pts)]})

    def finger_drag(self, a, b, steps=8):
        self.touch("touchStart", [a])
        for i in range(1, steps + 1):
            self.touch("touchMove", [(a[0] + (b[0] - a[0]) * i / steps, a[1] + (b[1] - a[1]) * i / steps)])
        self.touch("touchEnd", [])
        self.page.wait_for_timeout(60)


    def pinch(self, c, d0, d1, steps=6):
        pts = lambda d: [(c[0] - d, c[1]), (c[0] + d, c[1])]  # noqa: E731
        self.touch("touchStart", pts(d0))
        for i in range(1, steps + 1):
            self.touch("touchMove", pts(d0 + (d1 - d0) * i / steps))
        self.touch("touchEnd", [])

    def screen(self, side, pos):
        """Page coordinates of a game point in a view."""
        return self.ev("""([side, pos]) => { const v = studio[side].view, r = v.canvas.getBoundingClientRect(), s = v.toScreen(pos);
                         return [r.left + s.x, r.top + s.y]; }""", [side, pos])

    def ops(self):
        return self.ev("studio.log.applied().map((o) => ({ n: o.n, op: o.op, call: o.call, note: o.note || studio.log.notes.get(o.note_group)?.text, note_group: o.note_group, space: o.space, stroke: o.stroke, id: o.id || o.ref?.id || o.path?.id || o.person?.id, src: o.ref?.src, base: o.ref?.base, space_copy_of: o.space_copy_of }))")

    def shot(self, name):
        """A screenshot kept for a look, never a check: on a loaded machine software GL can take longer than the
        screenshot's wait, which then skips the picture rather than failing the test."""
        if SHOTS is None:
            return
        try:
            self.page.screenshot(path=str(SHOTS / f"{name}.png"), timeout=WAIT)
        except pw.TimeoutError:
            print(f"screenshot {name} skipped: the page took too long to draw")


def open_pad(browser, server, viewport, scheme="light", fresh=True, choose="draft"):
    ctx = browser.new_context(viewport=viewport, device_scale_factor=1, has_touch=True, color_scheme=scheme)
    page = ctx.new_page()
    page.set_default_timeout(WAIT)
    pad = Pad(page)
    page.goto(server + "/")
    page.wait_for_function("window.studio && studio.ready && studio.log", timeout=WAIT)
    if REAL:  # the real place builds its land in slices after the first frame
        page.wait_for_function("document.getElementById('progress').hidden", timeout=WAIT)
    page.wait_for_timeout(500)
    if choose and page.locator("#start .sheet").is_visible():  # saved work: nothing applied until chosen
        if choose == "draft":
            page.get_by_role("button", name="Start from the builder's draft").click()
        else:
            page.get_by_role("button", name=choose).click()
        page.wait_for_function("document.getElementById('start').hidden", timeout=WAIT)
    return pad


@pytest.fixture(scope="module")
def pad(browser, server):
    # a clean autosave first, so the run starts from the draft
    req = urllib.request.Request(server + "/api/places")
    pid = json.load(urllib.request.urlopen(req))[0]["place_id"]
    p = open_pad(browser, server, LANDSCAPE)
    if p.ev("studio.log.ops.length"):
        p.ev("studio.loadSave({ ops: [] })")
    p.pid = pid
    p.intro_shown = p.ev("!document.getElementById('intro').hidden")
    if p.intro_shown:
        p.page.click("#intro button")
    yield p
    assert not p.errors, p.errors
    p.page.context.close()


@pytest.fixture(autouse=True)
def fresh_ui(request):
    """Each test that drives the module's tab starts from the same studio state: outside, Select, nothing selected,
    default switches, no panel, so no test depends on what an earlier one (or a failure in one) left behind."""
    if "pad" in request.fixturenames:
        pad = request.getfixturevalue("pad")
        pad.ev("""(() => { const s = studio, T = s.tools;
          if (s.ours.space !== 'exterior') s.leave(s.ours, 0);
          T.use('select'); Object.assign(T.opts, { pieces: false, adds: false, snapFaces: true, snapGround: true, snapRot: true, keepSeat: true, step: 10 });
          s.people.sel = null; s.people.drag = null; T.lastTap = null; T.unit = null; T.inside = null;
          s.selection.clear(); T.selectionChanged(); s.panels.close(); })()""")
    if not REACH_OUT or "pad" not in request.fixturenames:
        yield
        return
    pad = request.getfixturevalue("pad")
    if not getattr(pad, "profiling", False):
        pad.cdp.send("Profiler.enable")
        pad.cdp.send("Profiler.startPreciseCoverage", {"callCount": True, "detailed": False})
        pad.profiling = True
    pad.cdp.send("Profiler.takePreciseCoverage")   # resets the counters: what follows is this test's own
    yield
    ran = pad.cdp.send("Profiler.takePreciseCoverage")["result"]
    mods = sorted({m.group(1) for r in ran if (m := re.search(r"/(js/[a-z_]+\.js)", r["url"]))
                   and any(f["ranges"][0]["count"] for f in r["functions"])})
    with open(REACH_OUT, "a") as f:
        f.write(json.dumps({"test": request.node.name, "js": mods}) + "\n")


def look_at(pad, side, pos, dist=2500, pitch=1.2):
    pad.ev("""([side, pos, dist, pitch]) => { const v = studio[side].view, o = studio[side].origin;
             v.rig.target.set(pos[0] - o[0], pos[1] - o[1], pos[2] - o[2]); v.rig.dist = dist; v.rig.pitch = pitch; v.changed(); }""",
           [side, pos, dist, pitch])
    pad.page.wait_for_timeout(250)


# The place as edited, as one string: every ref (space, id, base, position, turn, scale), plants cleared, land rows,
# paths and people. Two sessions holding the same place give the same string.
DIGEST = """(() => { const m = studio.model, rows = [], r1 = (v) => Math.round(v * 10) / 10;
  for (const [s, sp] of Object.entries(m.spaces)) for (const r of sp.refs.values())
    rows.push(JSON.stringify([s, r.id, r.base, (r.pos || []).map(r1), (r.rot || []).map((v) => Math.round(v * 1000)), r.scale ?? 1]));
  for (const k of m.clear.keys()) rows.push('clear ' + k);
  for (const [k, v] of m.land) rows.push('land ' + k + ' ' + JSON.stringify(v));
  for (const p of m.paths.values()) rows.push('path ' + JSON.stringify(p));
  for (const p of m.people.values()) rows.push('person ' + JSON.stringify(p));
  rows.sort(); let h = 0; const str = rows.join('\\n'); for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) | 0;
  return rows.length + ':' + h; })()"""


# ---------- 16: first-run guide, chrome, design rules ----------
def test_16_first_run_and_design(pad):
    assert pad.intro_shown, "the first-run guide shows"
    pad.ev("studio.panels.intro()")
    pad.shot("01-intro-landscape")
    pad.page.click("#intro button")
    assert pad.ev("getComputedStyle(document.body).touchAction") == "none"
    assert pad.ev("getComputedStyle(document.body).userSelect") == "none"
    assert pad.ev("getComputedStyle(document.body).overscrollBehavior").startswith("none")
    small = pad.ev("""[...document.querySelectorAll('button, select, input[type=range]')].filter((b) => b.offsetParent)
                     .map((b) => [b.textContent.trim() || b.getAttribute('aria-label'), b.getBoundingClientRect()])
                     .filter(([, r]) => r.width < 44 || r.height < 44).map(([t, r]) => `${t} ${r.width}x${r.height}`)""")
    assert not small, f"touch targets under 44 px: {small}"
    labels = pad.ev("[...document.querySelectorAll('#rail button span')].map((s) => s.textContent)")
    assert labels[:9] == ["Select", "Add", "People", "Quests", "Land", "Paint ground", "Plants", "Paths", "Walking"]


# ---------- 1: two views, layout, full screen, link, fingerprint ----------
def test_01_two_views(pad):
    # built things show as their models arrive (no stand-in boxes)
    pad.page.wait_for_function("studio.stats().drawn.place > 0 && studio.stats().drawn.src > 0", timeout=WAIT)
    st = pad.ev("studio.stats()")
    assert st["refs"]["world"] > 0 and st["refs"]["src"] > 0
    # the real ground keeps none of its own things inside the place: from the town, at the lowest detail software GL
    # forces, its nearest trees are beyond the drawn range
    assert (REAL or st["drawn"]["world"] > 0) and st["drawn"]["place"] > 0 and st["drawn"]["src"] > 0, st
    assert pad.ev("studio.ours.terrainMesh.cells.size") > 0 and pad.ev("studio.src.terrainMesh.cells.size") > 0
    assert pad.ev("studio.ours.terrainMesh.water.children.length") > 0, "water planes"
    assert pad.ev("document.getElementById('views').dataset.layout") == "side"
    a, b = pad.ev("['#view-ours','#view-src'].map((s) => document.querySelector(s).getBoundingClientRect().x)")
    assert a < b
    # full screen and back
    pad.page.click("#view-ours .fs")
    assert pad.ev("document.querySelector('#view-ours').classList.contains('full')")
    pad.page.click("#view-ours .fs")
    # finger orbit, pinch zoom
    yaw0, d0 = pad.ev("[studio.ours.view.rig.yaw, studio.ours.view.rig.dist]")
    r = pad.ev("(() => { const b = document.querySelector('#view-ours .canvas-holder').getBoundingClientRect(); return [b.x + b.width / 2, b.y + b.height / 2]; })()")
    pad.finger_drag((r[0], r[1]), (r[0] + 120, r[1]))
    assert pad.ev("studio.ours.view.rig.yaw") != yaw0, "one finger turns the view"
    pad.pinch(r, 60, 160)
    assert pad.ev("studio.ours.view.rig.dist") < d0, "spreading two fingers zooms in"
    # link: moving ours moves the source through the fit
    pad.page.click("#link")
    pad.finger_drag((r[0], r[1]), (r[0] - 80, r[1] + 40))
    t = pad.ev("""(() => { const s = studio, o = s.ours.view.rig.target, so = s.src.view.rig.target;
               const g = [o.x + s.ours.origin[0], o.y + s.ours.origin[1]], q = [so.x + s.src.origin[0], so.y + s.src.origin[1]];
               const f = s.fit, c = Math.cos(f.rot), n = Math.sin(f.rot);
               return [g, [c * q[0] * f.scale - n * q[1] * f.scale + f.dx, n * q[0] * f.scale + c * q[1] * f.scale + f.dy]]; })()""")
    assert abs(t[0][0] - t[1][0]) < 1 and abs(t[0][1] - t[1][1]) < 1, t
    pad.page.click("#link")
    # the fingerprint and its warning
    assert "World build" in pad.ev("document.getElementById('fingerprint').textContent")
    pad.shot("02-two-views-landscape")


# ---------- 3: select, cycle, lasso, gizmo, nudge, duplicate, remove, info ----------
def test_03_select_and_manipulate(pad):
    pad.ev("studio.tools.opts.pieces = true")  # these are about one piece, not its unit (test_30)
    pad.page.click("#rail [data-tool=select]")
    # a building with nothing that follows it (no invisible wall on it): each change is its one op
    b = pad.ev("(() => { const rs = [...studio.model.spaces.exterior.refs.values()]; "
               "return rs.find((r) => r.kind === 'building' && !rs.some((w) => w.seat?.on === r.id)); })()")
    seated = pad.ev("(id) => studio.seated(studio.model.spaces.exterior.refs.get(id)).pos", b["id"])
    look_at(pad, "ours", seated)
    x, y = pad.screen("ours", [seated[0], seated[1], seated[2] + 150])
    pad.pen_tap(x, y)
    sel = pad.ev("[...studio.selection]")
    assert len(sel) == 1
    assert "How it sits" in pad.ev("document.getElementById('panel-body').textContent")
    pad.pen_tap(x, y)  # the same spot again: the next thing there (or the same when alone)
    assert len(pad.ev("[...studio.selection]")) == 1
    # gizmo: move east by dragging the move handle
    pad.ev("(id) => { studio.selection = new Set([id]); studio.tools.selectionChanged(); }", b["id"])
    h = pad.ev("(() => { const r = document.querySelector('.gizmo [data-h=move]').getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; })()")
    n0 = len(pad.ops())
    pad.pen_drag([h, (h[0] + 60, h[1] + 10)])
    ops = pad.ops()
    assert len(ops) == n0 + 1 and ops[-1]["op"] == "ref.move", ops[-1:]
    # rotate handle snaps to 15 degrees
    h = pad.ev("(() => { const r = document.querySelector('.gizmo [data-h=rotate]').getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; })()")
    pad.pen_drag([h, (h[0] - 10, h[1] + 70)])
    last = pad.ev("studio.log.applied().at(-1)")
    assert last["op"] == "ref.move"
    turn = (last["after"]["rot"][2] - last["before"]["rot"][2]) / (3.141592653589793 / 12)
    assert abs(turn - round(turn)) < 0.01
    # lift
    h = pad.ev("(() => { const r = document.querySelector('.gizmo [data-h=lift]').getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; })()")
    pad.pen_drag([h, (h[0], h[1] - 40)])
    assert pad.ev("studio.log.applied().at(-1).after.seat?.dz ?? 0") > 0 or pad.ev("studio.log.applied().at(-1).op") == "ref.move"
    # nudge, ground, duplicate, remove through the panel
    for label in ["North", "Turn right", "Sit on the ground", "Duplicate"]:
        pad.page.get_by_role("button", name=label, exact=True).click()
    ops = pad.ops()
    assert [o["op"] for o in ops[-4:]] == ["ref.move", "ref.move", "ref.move", "ref.add"]
    dup = ops[-1]["id"]
    assert pad.ev("[...studio.selection]") == [dup]
    pad.page.get_by_role("button", name="Remove from our place").click()
    assert pad.ops()[-1]["op"] == "ref.remove"
    # lasso: draw round the building and its neighbours
    look_at(pad, "ours", seated, dist=6000)
    cx, cy = pad.screen("ours", seated)
    pad.ev("studio.selection.clear(); studio.tools.selectionChanged()")
    pad.pen_drag([(cx - 150, cy - 150), (cx + 150, cy - 150), (cx + 150, cy + 150), (cx - 150, cy + 150), (cx - 150, cy - 150)], steps=6)
    assert len(pad.ev("[...studio.selection]")) >= 2, "a lasso selects several"
    pad.shot("03-selection-gizmo")


def unsaved_work(pad, server):
    """Unsaved work of the test's own: a building nudged twice in the module's tab (a place an earlier test finalised is
    opened for work again first: a finalised place is never autosaved), its autosave waited for on the server.
    Returns whether the tab was finalised and the autosave's listing."""
    pid = pad.pid
    was_final = pad.ev("studio.finalised")
    pad.ev("async () => { const s = await (await fetch(`/api/place/${studio.place.place_id}/saves`)).json(); const a = s.find((x) => x.save_id === 'autosave'); if (a) studio.revs.autosave = a.rev; studio.finalised = false; }")
    pad.ev("""(() => { const refs = studio.model.spaces.exterior.refs, id = [...refs.values()].find((x) => x.kind === 'building').id;
        for (const dx of [16, -16]) { const was = [...refs.get(id).pos], now = [was[0] + dx, was[1], was[2]];
          studio.push([{ op: 'ref.move', id, before: { pos: was }, after: { pos: now } }]); } })()""")
    need = len(pad.ops())

    def autosaved():
        saves = json.load(urllib.request.urlopen(f"{server}/api/place/{pid}/saves"))
        return next((x for x in saves if x["save_id"] == "autosave" and (x["ops"] or 0) >= need), None)
    t0 = time.time()
    while (auto := autosaved()) is None and time.time() - t0 < WAIT / 1000:
        pad.page.wait_for_timeout(250)
    assert auto, "the nudges were autosaved"
    return was_final, auto


# ---------- 13 and 15: saves, reload, finalise, heartbeat ----------
def test_13_15_saves_finalise_heartbeat(pad, browser, server):
    unsaved_work(pad, server)
    pad.page.wait_for_function("document.getElementById('save-state').dataset.state === 'saved'", timeout=WAIT)
    pad.page.click("#rail [data-tool=saves]")
    pad.page.fill("#panel-body input[type=text]", "Test save one")
    pad.page.get_by_role("button", name="Save a copy").click()
    pad.page.wait_for_function("document.getElementById('panel-body').textContent.includes('Test save one')", timeout=WAIT)
    n, ops, digest = len(pad.ops()), json.dumps(pad.ops(), sort_keys=True), pad.ev(DIGEST)
    # another session: the autosave is picked up after the machine was off
    other = open_pad(browser, server, PORTRAIT, choose="Continue the unsaved work")
    other.page.wait_for_function(f"studio.log.applied().length === {n}", timeout=WAIT)
    assert other.ev("studio.log.applied().length") == n, (other.errors, other.ev("document.getElementById('toast').textContent"))
    assert json.dumps(other.ops(), sort_keys=True) == ops and other.ev(DIGEST) == digest, "the same edits make the same place"
    assert other.ev("document.getElementById('views').dataset.layout") == "stack"
    other.page.click(".intro button") if other.ev("!document.getElementById('intro').hidden") else None
    other.shot("13-portrait-resumed")
    other.page.context.close()
    if REAL:
        assert pad.beats, "the page beats while it is open"
    else:
        beats = json.load(urllib.request.urlopen(server + "/api/_heartbeats"))
        assert (beats.get("count") if isinstance(beats, dict) else beats) >= 1
    # finalise
    pad.page.click("#finalise-btn")
    assert "writes them into" in pad.ev("document.getElementById('panel-body').textContent")
    pad.page.locator("#panel-body button.primary").click()
    pad.page.wait_for_function("['Finalised', 'Finalise stopped'].includes(document.getElementById('panel-title').textContent)",
                               timeout=(2400000 if REAL else 30000))
    pad.shot("13-finalised")
    if pad.ev("document.getElementById('panel-title').textContent") == "Finalise stopped":
        # the real chain may stop at a build or check step: said plainly, the owner's work kept
        assert REAL, "the fixture chain always finishes"
        assert pad.page.locator("#panel-body .steps li[data-s=failed]").count() == 1
        assert "Your changes are saved" in pad.ev("document.getElementById('panel-body').textContent")
        return
    assert pad.page.locator("#panel-body .steps li[data-s=done]").count() == 4
    assert pad.page.locator("#panel-body .report").count() == 1


def test_22_start_choice(pad, browser, server):
    pid = pad.pid
    was_final, auto = unsaved_work(pad, server)
    # a named save made on an older draft
    old = json.load(urllib.request.urlopen(f"{server}/api/place/{pid}/saves/autosave"))
    body = {**old, "save_id": "older-draft", "name": "Older draft work", "rev": 0, "base": {**old["base"], "draft_key": "an-older-draft"}}
    req = urllib.request.Request(f"{server}/api/place/{pid}/saves/older-draft", data=json.dumps(body).encode(), method="PUT",
                                 headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)
    p = open_pad(browser, server, LANDSCAPE, choose=None)
    assert p.page.locator("#start .sheet").is_visible()
    assert p.ev("studio.log.applied().length") == 0, "nothing applied before the choice"
    text = p.ev("document.getElementById('start').textContent")
    assert "Unsaved work from" in text and f"{auto['ops']} edits" in text and "Older draft work" in text
    p.page.wait_for_function("document.querySelector('#start .older')", timeout=WAIT)
    assert "Made on an older draft" in p.ev("document.querySelector('#start .older').textContent")
    p.shot("22-start-choice")
    b = p.page.get_by_role("button", name="Discard the unsaved work")
    b.click()
    b.click()
    p.page.wait_for_function("!document.getElementById('start').textContent.includes('Unsaved work from')", timeout=WAIT)
    left = {x["save_id"]: x["ops"] for x in json.load(urllib.request.urlopen(f"{server}/api/place/{pid}/saves"))}
    assert left.get("autosave", 0) == 0 and left["older-draft"] == auto["ops"]
    p.page.get_by_role("button", name="Start from the builder's draft").click()
    assert p.ev("studio.log.applied().length") == 0
    p.page.context.close()
    # the module's tab as the next tests expect it: the two nudges gone from its log, finalised as it was
    pad.ev("(f) => { clearTimeout(studio.autoT); studio.log.undo(); studio.log.undo(); studio.log.ops.length = studio.log.cursor; studio.finalised = f; }", was_final)


# ---------- 25: day and night ----------
# The mean brightness (0..255) of a square of a view's canvas round a game point.
BRIGHT = """([side, pos, half]) => { const v = studio[side].view, c = v.renderer.domElement, r = v.canvas.getBoundingClientRect(),
  b = c.getBoundingClientRect(), s = v.toScreen(pos), k = c.width / b.width;
  const x = Math.round((r.left - b.left + s.x - half) * k), y = Math.round((r.top - b.top + s.y - half) * k), w = Math.round(2 * half * k);
  const t = document.createElement('canvas'); t.width = t.height = w; const g = t.getContext('2d'); g.drawImage(c, x, y, w, w, 0, 0, w, w);
  const d = g.getImageData(0, 0, w, w).data; let sum = 0; for (let i = 0; i < d.length; i += 4) sum += (d[i] + d[i + 1] + d[i + 2]) / 3;
  return sum / (d.length / 4); }"""


# ---------- 26: leaving a place lets go of its GPU memory; a lost context during a switch still draws ----------
MEM = "({ ...studio.ours.view.renderer.info.memory })"
DREW = "studio.ours.view.drew?.calls || 0"


# ---------- 27: the thumb sticks ----------
CAM = """(() => { const v = studio.ours.view; v.updateCamera(); const p = v.camera.position;
          return { x: p.x, y: p.y, z: p.z, heading: v.heading(), pitch: v.rig.pitch }; })()"""


def hold(pad, sel, dx, dy, ms=600, tid=0):
    c = pad.ev("(s) => { const r = document.querySelector(s).getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }", sel)
    pt = lambda x, y: [{"x": x, "y": y, "id": tid}]  # noqa: E731
    pad.cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": pt(*c)})
    for i in range(1, 5):
        pad.cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": pt(c[0] + dx * i / 4, c[1] + dy * i / 4)})
    pad.page.wait_for_timeout(ms)
    pad.cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    pad.page.wait_for_timeout(100)
    return c


def test_27_thumb_sticks(pad):
    """The left stick moves the camera where it faces, the right stick turns it right and looks up; a finger on a
    stick changes nothing selected; the sticks sit inside the views, clear of the bars; the tilt slider is gone."""
    pad.ev("studio.panels.close(); studio.focusView(studio.ours.view)")
    assert pad.ev("!document.querySelector('.tilt')"), "the tilt slider is replaced by the right stick"
    assert pad.ev("!document.querySelector('.sticks').hidden"), "shown on a touch device"
    rid = pad.ev("[...studio.model.spaces.exterior.refs.values()].find((r) => r.kind === 'building').id")
    pad.ev("(id) => { studio.tools.use('select'); studio.selection = new Set([id]); studio.tools.selectionChanged(); }", rid)
    boxes = pad.ev("""(() => { const b = (s) => { const r = document.querySelector(s).getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; };
              return { l: b('.stick.left'), r: b('.stick.right'), views: b('#views'), bar: b('#view-ours .view-bar'), compass: b('#view-ours .compass') }; })()""")
    for k in ("l", "r"):
        s = boxes[k]
        assert s[0] >= boxes["views"][0] and s[2] <= boxes["views"][2] + 1 and s[3] <= boxes["views"][3] + 1, boxes
        assert s[1] > boxes["bar"][3], boxes
    assert boxes["l"][0] >= boxes["compass"][2], "the left stick is beside the compass, not over it"
    pad.ev("studio.ours.view.rig.pitch = 0.4; studio.ours.view.changed()")
    a = pad.ev(CAM)
    hold(pad, ".stick.left", 0, -70)   # pushed up to the edge: forward at a run
    b = pad.ev(CAM)
    h = a["heading"] * 3.141592653589793 / 180
    fwd = (b["x"] - a["x"]) * __import__("math").sin(h) + (b["y"] - a["y"]) * __import__("math").cos(h)
    assert fwd > 50, (a, b, fwd)
    hold(pad, ".stick.right", 60, 0, ms=400)   # right: turns right (the heading grows clockwise)
    c = pad.ev(CAM)
    assert 5 < (c["heading"] - b["heading"]) % 360 < 180, (b, c)
    hold(pad, ".stick.right", 0, -60, ms=400)   # up: looks up (the orbit pitch falls)
    d = pad.ev(CAM)
    assert d["pitch"] < c["pitch"] - 0.1, (c, d)
    assert pad.ev("[...studio.selection]") == [rid], "a finger on a stick selects nothing"
    # the pen never moves a stick
    e0 = pad.ev(CAM)
    sx, sy = pad.ev("(() => { const r = document.querySelector('.stick.left').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; })()")
    pad.pen_drag([(sx, sy), (sx, sy - 60)])
    pad.page.wait_for_timeout(200)
    assert abs(pad.ev(CAM)["x"] - e0["x"]) < 1 and abs(pad.ev(CAM)["y"] - e0["y"]) < 1
    assert pad.ev("[...studio.selection]") == [rid]
    # walk: the eye at a person's height over the ground, kept there while moving
    pad.ev("""(id) => { const v = studio.ours.view, r = studio.model.spaces.exterior.refs.get(id);
              v.rig.target.set(r.pos[0] - v.origin[0] - 600, r.pos[1] - v.origin[1] - 600, r.pos[2] - v.origin[2]); v.changed(); }""", rid)
    pad.page.click(".stick-btn[data-act=walk]")
    hold(pad, ".stick.left", 0, -40, ms=500)
    w = pad.ev("""(() => { const v = studio.ours.view, s = studio.sticks, e = s.eyeOf(v), g = s.groundAt(v, e.x, e.y, e.z - 120);
                  return { z: e.z, g }; })()""")
    assert w["g"] is not None and abs(w["z"] - (w["g"] + 120)) < 2, w
    pad.shot("27-sticks-walk")
    assert pad.ev("JSON.parse(localStorage.getItem('studio.sticks.v1')).walk") is True
    pad.page.click(".stick-btn[data-act=walk]")
    assert not pad.errors, pad.errors


# ---------- 30: composite things move as one ----------
UNIT_STATE = """(() => { const m = studio.model, ex = m.spaces.exterior.refs, r2 = (v) => Math.round(v * 100) / 100;
  const refs = {}; for (const [id, r] of ex) refs[id] = { pos: r.pos.map(r2), rot: (r.rot || []).map((v) => Math.round(v * 1e4)), seat: r.seat ?? null, door: r.door || null };
  const room = m.spaces.FixHouse02.refs.get('fixplaceFixHouse02.door');
  return { refs, bram: m.people.get('fixplace.p2'), room: room.door }; })()"""


# ---------- 35: the tablet layout of the new controls, landscape and upright ----------
LAYOUT = """(() => {
  const vis = (e) => e && e.offsetParent !== null && !e.hidden && getComputedStyle(e).visibility !== 'hidden';
  const R = (e) => e.getBoundingClientRect(), view = R(document.querySelector('#view-ours')), out = [];
  const inside = (r, b) => r.left >= b.left - 1 && r.right <= b.right + 1 && r.top >= b.top - 1 && r.bottom <= b.bottom + 1;
  const hs = [...document.querySelectorAll('#view-ours .gizmo .h')].filter(vis);
  for (const h of hs) { const r = R(h); if (r.width < 44 || r.height < 44) out.push(`handle ${h.dataset.h} ${r.width}x${r.height}`); }
  for (let i = 0; i < hs.length; i++) for (let j = i + 1; j < hs.length; j++) {
    const a = R(hs[i]), b = R(hs[j]);
    if (a.left < b.right - 2 && b.left < a.right - 2 && a.top < b.bottom - 2 && b.top < a.bottom - 2) out.push(`handles ${hs[i].dataset.h} and ${hs[j].dataset.h} overlap`);
  }
  for (const sel of ['#frame-sel', '#markers-btn']) {
    const b = document.querySelector(sel); if (!vis(b)) { out.push(`${sel} not shown`); continue; }
    const r = R(b); if (r.width < 44 || r.height < 44) out.push(`${sel} ${r.width}x${r.height}`);
    if (!inside(r, view)) out.push(`${sel} cut off`);
    if (document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2)?.closest(sel) == null) out.push(`${sel} covered`);
  }
  const lab = document.querySelector('#view-ours .unit-label'); if (vis(lab) && !inside(R(lab), view)) out.push('unit label cut off');
  for (const b of [...document.querySelectorAll('#panel-body button')].filter(vis)) { const r = R(b); if (r.width < 44 || r.height < 44) out.push(`panel button "${b.textContent.trim()}" ${r.width}x${r.height}`); }
  return out; })()"""


@pytest.mark.parametrize("viewport", [LANDSCAPE, PORTRAIT], ids=["landscape", "portrait"])
def test_35_tablet_layout_of_the_new_controls(browser, server, viewport):
    p = open_pad(browser, server, viewport)
    if p.ev("!document.getElementById('intro').hidden"):
        p.page.click("#intro button")
    p.page.click("#rail [data-tool=select]")
    house = p.ev("(id) => studio.seated(studio.model.spaces.exterior.refs.get(id)).pos", "fixplace.b1")
    look_at(p, "ours", house, dist=3000, pitch=1.0)
    p.ev("studio.tools.selectUnit(studio.unitIndex().units.get('h01'))")
    p.page.wait_for_timeout(200)
    assert p.ev(LAYOUT) == [], f"unit selected: {p.ev(LAYOUT)}"
    p.shot(f"35-unit-{viewport['width']}")
    one = p.ev("[...studio.model.spaces.exterior.refs.values()].find((r) => r.kind === 'clutter').id")
    p.ev("(id) => { studio.tools.opts.pieces = true; studio.selection = new Set([id]); studio.tools.selectionChanged(); }", one)
    look_at(p, "ours", p.ev("(id) => studio.seated(studio.model.spaces.exterior.refs.get(id)).pos", one), dist=2000, pitch=1.0)
    assert p.ev(LAYOUT) == [], f"one piece: {p.ev(LAYOUT)}"
    p.ev("studio.people.select('fixplace.p2')")
    assert p.ev(LAYOUT) == [], f"people panel: {p.ev(LAYOUT)}"
    p.shot(f"35-people-{viewport['width']}")
    assert not p.errors, p.errors
    p.page.context.close()
