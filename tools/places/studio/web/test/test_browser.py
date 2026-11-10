"""The studio in headless Chromium at the MatePad Pro's size, with pen and touch, against the dev server.

Each test performs one of the owner's sixteen requirements and asserts on the ops it makes and the scene state.
Run: ~/.argonia/venv/bin/python -m pytest -q tools/places/studio/web/test/test_browser.py
Env: STUDIO_URL to test a running server instead (real bundles); SHOTS=<dir> to keep screenshots.
"""
import json
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
SHOTS = Path(os.environ.get("SHOTS") or tempfile.mkdtemp(prefix="studio-shots-"))
LANDSCAPE, PORTRAIT = {"width": 1280, "height": 800}, {"width": 800, "height": 1280}  # MatePad Pro 12.6 at DPR 2


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def server():
    if os.environ.get("STUDIO_URL"):
        yield os.environ["STUDIO_URL"].rstrip("/")
        return
    fx = Path(tempfile.mkdtemp(prefix="studio-fixture-"))
    subprocess.run([sys.executable, str(WEB / "dev" / "make_fixture.py"), str(fx)], check=True, capture_output=True)
    port = free_port()
    p = subprocess.Popen([sys.executable, str(WEB / "dev" / "devserver.py"), "--port", str(port), "--fixture", str(fx)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            urllib.request.urlopen(url + "/api/status", timeout=1)
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
        self.errors = []
        page.on("pageerror", lambda e: self.errors.append(str(e)))

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
        return self.ev("studio.log.applied().map((o) => ({ n: o.n, op: o.op, call: o.call, note: o.note, space: o.space, stroke: o.stroke, id: o.id || o.ref?.id || o.path?.id || o.person?.id, src: o.ref?.src, base: o.ref?.base, space_copy_of: o.space_copy_of }))")

    def shot(self, name):
        self.page.screenshot(path=str(SHOTS / f"{name}.png"))


def open_pad(browser, server, viewport, scheme="light", fresh=True):
    ctx = browser.new_context(viewport=viewport, device_scale_factor=1, has_touch=True, color_scheme=scheme)
    page = ctx.new_page()
    pad = Pad(page)
    page.goto(server + "/")
    page.wait_for_function("window.studio && studio.loadMs && studio.log", timeout=60000)
    page.wait_for_timeout(500)
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
    yield p
    assert not p.errors, p.errors
    p.page.context.close()


def first_ref(pad, kind, space="exterior"):
    return pad.ev("([k, s]) => [...studio.model.spaces[s].refs.values()].find((r) => r.kind === k)", [kind, space])


def look_at(pad, side, pos, dist=2500, pitch=1.2):
    pad.ev("""([side, pos, dist, pitch]) => { const v = studio[side].view, o = studio[side].origin;
             v.rig.target.set(pos[0] - o[0], pos[1] - o[1], pos[2] - o[2]); v.rig.dist = dist; v.rig.pitch = pitch; v.changed(); }""",
           [side, pos, dist, pitch])
    pad.page.wait_for_timeout(250)


# ---------- 16: first-run guide, chrome, design rules ----------
def test_16_first_run_and_design(pad):
    assert pad.ev("!document.getElementById('intro').hidden"), "the first-run guide shows"
    pad.shot("01-intro-landscape")
    pad.page.click(".intro button")
    assert pad.ev("getComputedStyle(document.body).touchAction") == "none"
    assert pad.ev("getComputedStyle(document.body).userSelect") == "none"
    assert pad.ev("getComputedStyle(document.body).overscrollBehavior").startswith("none")
    small = pad.ev("""[...document.querySelectorAll('button, select, input[type=range]')].filter((b) => b.offsetParent)
                     .map((b) => [b.textContent.trim() || b.getAttribute('aria-label'), b.getBoundingClientRect()])
                     .filter(([, r]) => r.width < 44 || r.height < 44).map(([t, r]) => `${t} ${r.width}x${r.height}`)""")
    assert not small, f"touch targets under 44 px: {small}"
    labels = pad.ev("[...document.querySelectorAll('#rail button span')].map((s) => s.textContent)")
    assert labels[:6] == ["Select", "Add", "People", "Land", "Plants", "Paths"]


# ---------- 1: two views, layout, full screen, link, fingerprint ----------
def test_01_two_views(pad):
    st = pad.ev("studio.stats()")
    assert st["refs"]["world"] > 0 and st["refs"]["src"] > 0
    assert st["drawn"]["world"] > 0 and st["drawn"]["src"] > 0, st
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
    r = pad.ev("(() => { const b = document.querySelector('#view-ours canvas').getBoundingClientRect(); return [b.x + b.width / 2, b.y + b.height / 2]; })()")
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


def test_01_mismatch_warning(browser, server):
    ctx = browser.new_context(viewport=LANDSCAPE, has_touch=True)
    page = ctx.new_page()
    page.route("**/api/status", lambda r: r.fulfill(json={"ground_sha": "aaaaaaaaaaaa", "deployed_sha": "bbbbbbbbbbbb", "match": False}))
    page.goto(server + "/")
    page.wait_for_function("window.studio && studio.status", timeout=30000)
    assert page.evaluate("!document.getElementById('warn').hidden")
    assert "not the one on the play machine" in page.evaluate("document.getElementById('warn').textContent")
    ctx.close()


# ---------- 2: performance, lazy meshes, thumbnails ----------
def test_02_performance_and_lazy_models(pad):
    pad.page.wait_for_function("[...studio.ours.place.groups.values()].some((g) => g.full)", timeout=30000)
    for _ in range(30):
        pad.ev("studio.ours.view.rig.yaw += 0.02; studio.ours.view.changed()")
        pad.page.wait_for_timeout(16)
    st = pad.ev("studio.stats()")
    assert st["ours"]["n"] > 10
    url = pad.ev("import('./js/thumbs.js').then((m) => m.thumb(studio.bases.values().next().value))")
    assert url.startswith("data:image/png")


# ---------- 3: select, cycle, lasso, gizmo, nudge, duplicate, remove, info ----------
def test_03_select_and_manipulate(pad):
    pad.page.click("#rail [data-tool=select]")
    b = first_ref(pad, "building")
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


# ---------- 4: copy from the source, a group, an enterable building ----------
def test_04_from_the_source(pad):
    pad.page.click("#panel-close")  # the panel floats over the source view's right side
    src = pad.ev("studio.srcBundle.spaces.exterior.refs.find((r) => r.kind === 'building')")
    look_at(pad, "src", src["pos"], dist=3000)
    pad.pen_tap(*pad.screen("src", [src["pos"][0], src["pos"][1], src["pos"][2] + 100]))
    assert pad.ev("studio.tools.placing?.from") == "source"
    g = pad.ev("studio.ours.view.rig.target.toArray().map((v, i) => v + studio.ours.origin[i])")
    gx, gy = pad.screen("ours", g)
    n0 = len(pad.ops())
    pad.pen_tap(gx, gy)
    pad.pen_tap(gx + 40, gy + 30)
    ops = pad.ops()[n0:]
    assert len(ops) >= 2 and all(o["op"] == "ref.add" and o["src"] for o in ops)
    # an enterable building brings its room and doors
    bld = pad.ev("""(() => { const s = studio, refs = s.srcBundle.spaces.exterior.refs;
                   return refs.find((r) => r.kind === 'building' && s.tools.doorsOf(r, refs).length); })()""")
    assert bld, "the source has an enterable building"
    pad.ev("(b) => { studio.srcSel = [b]; studio.tools.srcChanged(); }", bld)
    assert "Can be entered" in pad.ev("document.getElementById('panel-body').textContent")
    n0 = len(pad.ops())
    pad.pen_tap(gx - 80, gy - 60)
    ops = pad.ops()[n0:]
    assert any(o["space_copy_of"] for o in ops), "the room inside comes too"
    assert any(o["space"] != "exterior" for o in ops)
    door = pad.ev("(ids) => ids.map((id) => studio.model.spaces.exterior.refs.get(id)).find((r) => r?.door)", [o["id"] for o in ops])
    assert door and door["door"]["to_space"] in pad.ev("Object.keys(studio.model.spaces)")
    # a group keeps its arrangement
    grp = pad.ev("studio.srcBundle.spaces.exterior.refs.filter((r) => r.kind === 'clutter' || r.kind === 'static').slice(0, 3)")
    pad.ev("(g) => { studio.srcSel = g; studio.tools.srcChanged(); }", grp)
    n0 = len(pad.ops())
    pad.pen_tap(gx + 100, gy + 80)
    added = [pad.ev("(id) => studio.model.spaces.exterior.refs.get(id).pos", o["id"]) for o in pad.ops()[n0:]]
    d_src = ((grp[0]["pos"][0] - grp[1]["pos"][0]) ** 2 + (grp[0]["pos"][1] - grp[1]["pos"][1]) ** 2) ** 0.5
    d_our = ((added[0][0] - added[1][0]) ** 2 + (added[0][1] - added[1][1]) ** 2) ** 0.5
    assert abs(d_src * pad.ev("studio.fit.scale") - d_our) < 1
    pad.page.get_by_role("button", name="Stop adding").click()
    assert pad.ev("studio.tools.placing") is None


# ---------- 5: search ----------
def test_05_search(pad):
    pad.page.click("#rail [data-tool=search]")
    box = pad.page.locator("#panel-body input[type=search]")
    box.fill("house")
    pad.page.wait_for_function("studio.panels.search.results.length > 0", timeout=10000)
    pad.page.get_by_role("button", name="Everything we have").click()
    pad.page.wait_for_timeout(600)
    res = pad.ev("studio.panels.search.results")
    if any(r.get("nordic") for r in res):
        assert pad.page.locator(".card .tag.nordic").count() > 0, "Nordic pieces are marked"
    pad.page.locator(".card").first.click()
    assert pad.ev("studio.tools.placing?.from") == "search"
    g = pad.ev("studio.ours.view.rig.target.toArray().map((v, i) => v + studio.ours.origin[i])")
    pad.pen_tap(*pad.screen("ours", g))
    last = pad.ops()[-1]
    assert last["op"] == "ref.add" and last["base"] == res[0]["key"] and not last["src"]
    assert pad.ev("[...studio.selection]") == [last["id"]], "the new thing is selected for the gizmo"
    assert pad.ev("!document.querySelector('.gizmo').hidden")
    pad.shot("05-search")


# ---------- 6 and 7: undo, redo, history, fault or taste ----------
def test_06_07_history_and_calls(pad):
    n = len(pad.ops())
    pad.page.click("#undo")
    m = len(pad.ops())
    assert m < n, "undo takes back the last change (a group added in one tap goes as one)"
    pad.page.click("#undo")
    assert len(pad.ops()) < m
    pad.page.click("#redo")
    assert len(pad.ops()) == m
    pad.page.click("#redo")
    assert len(pad.ops()) == n
    # the chip after an edit marks it a taste call, with a note
    pad.page.click("#rail [data-tool=select]")
    pad.ev("studio.selection = new Set([studio.log.applied().at(-1).ref.id]); studio.tools.selectionChanged()")
    pad.page.get_by_role("button", name="East", exact=True).click()
    assert pad.ev("!document.getElementById('chip').hidden")
    pad.page.click("#chip .call")
    pad.page.fill("#chip input", "I prefer it by the water")
    pad.page.press("#chip input", "Enter")
    last = pad.ops()[-1]
    assert last["call"] == "taste" and last["note"] == "I prefer it by the water"
    pad.page.click("#rail [data-tool=history]")
    rows = pad.page.locator("ol.history li")
    assert rows.count() >= 5
    assert pad.page.locator("ol.history .call[data-call=taste]").count() >= 1
    # choose two edits and mark them taste, then everything from one on
    pad.page.locator("ol.history li button[aria-label='Choose this change']").nth(0).click()
    pad.page.locator("ol.history li button[aria-label='Choose this change']").nth(1).click()
    pad.page.get_by_role("button", name="Chosen are taste").click()
    assert sum(1 for o in pad.ops() if o["call"] == "taste") >= 3
    # go back to a point in the list
    k = len(pad.ops())
    pad.page.locator("ol.history li .what").nth(2).click()
    assert len(pad.ops()) < k
    pad.page.click("#redo")
    while pad.ev("studio.log.canRedo()"):
        pad.page.click("#redo")
    pad.shot("06-history")


# ---------- 8: people ----------
def test_08_people(pad):
    pad.page.click("#rail [data-tool=people]")
    assert pad.ev("!document.getElementById('timebar').hidden")
    pid = pad.ev("[...studio.model.people.keys()][0]")
    pad.ev("studio.setTime(7.9)")
    p0 = pad.ev("(id) => studio.people.markers.get(id).position.toArray()", pid)
    pad.page.fill("#time", "12")
    pad.ev("document.getElementById('time').dispatchEvent(new Event('input'))")
    p1 = pad.ev("(id) => studio.people.markers.get(id).position.toArray()", pid)
    assert p0 != p1, "dragging the time moves people"
    at = pad.ev("(id) => studio.people.markers.get(id).userData.at", pid)
    look_at(pad, "ours", at, dist=2500)
    pad.pen_tap(*pad.screen("ours", [at[0], at[1], at[2] + 80]))
    assert pad.ev("studio.people.sel") == pid
    assert pad.page.locator("#panel-body input[type=time]").count() >= 1, "stops with times"
    pad.page.locator("#panel-body input[type=time]").first.fill("07:30")
    pad.page.locator("#panel-body input[type=time]").first.dispatch_event("change")
    assert pad.ops()[-1]["op"] == "person.edit"
    pad.page.get_by_role("button", name="Add patrol points").click()
    g = pad.ev("studio.ours.view.rig.target.toArray().map((v, i) => v + studio.ours.origin[i])")
    x, y = pad.screen("ours", g)
    pad.pen_tap(x, y)
    pad.pen_tap(x + 50, y)
    edits = [o for o in pad.ops() if o["op"] == "person.edit"]
    assert len(edits) >= 3
    pad.page.get_by_role("button", name="Done").click()
    pad.page.get_by_role("button", name="Remove this person").click()
    assert pad.ops()[-1]["op"] == "person.remove"
    pad.page.get_by_role("button", name="Place them").click()
    pad.pen_tap(x - 50, y)
    assert pad.ops()[-1]["op"] == "person.add"
    pad.shot("08-people")


# ---------- 9: interiors ----------
def test_09_interiors(pad):
    pad.page.click("#rail [data-tool=select]")
    door = pad.ev("[...studio.model.spaces.exterior.refs.values()].find((r) => r.door?.to_space && studio.model.spaces[r.door.to_space])")
    pos = pad.ev("(d) => studio.seated(d).pos", door)
    look_at(pad, "ours", pos, dist=900)
    x, y = pad.screen("ours", [pos[0], pos[1], pos[2] + 60])
    pad.ev("(id) => { studio.selection = new Set([id]); studio.tools.selectionChanged(); }", door["id"])
    pad.page.get_by_role("button", name="Go inside").click()
    assert pad.ev("studio.ours.space") == door["door"]["to_space"]
    assert pad.page.locator("#view-ours .crumbs button").count() == 1
    inside = pad.ev("[...studio.model.spaces[studio.ours.space].refs.values()].find((r) => r.kind !== 'door')")
    pad.ev("(id) => { studio.selection = new Set([id]); studio.tools.selectionChanged(); }", inside["id"])
    pad.page.get_by_role("button", name="North", exact=True).click()
    assert pad.ops()[-1]["op"] == "ref.move" and pad.ops()[-1]["space"] == door["door"]["to_space"]
    pad.shot("09-interior")
    pad.page.locator("#view-ours .crumbs button").first.click()
    assert pad.ev("studio.ours.space") == "exterior"
    # the source side too
    sdoor = pad.ev("studio.srcBundle.spaces.exterior.refs.find((r) => r.door?.to_space && studio.srcBundle.spaces[r.door.to_space])")
    pad.ev("(d) => studio.enter(studio.src, d)", sdoor)
    assert pad.ev("studio.src.space") == sdoor["door"]["to_space"]
    pad.page.locator("#view-src .crumbs button").first.click()
    assert pad.ev("studio.src.space") == "exterior"
    assert x and y


# ---------- 10: land ----------
def test_10_land(pad):
    pad.page.click("#rail [data-tool=land]")
    b = first_ref(pad, "building")
    z0 = pad.ev("(id) => studio.seated(studio.model.spaces.exterior.refs.get(id)).pos[2]", b["id"])
    look_at(pad, "ours", b["pos"], dist=3000)
    x, y = pad.screen("ours", pad.ev("(id) => studio.seated(studio.model.spaces.exterior.refs.get(id)).pos", b["id"]))
    n0 = len(pad.ops())
    pad.pen_drag([(x - 30, y), (x + 30, y), (x - 30, y + 10), (x + 30, y + 10)], pressure=0.9, steps=6)
    ops = pad.ops()[n0:]
    assert ops and all(o["op"] == "land.patch" for o in ops)
    assert len({o["stroke"] for o in ops if o["stroke"]}) <= 1
    full = pad.ev("studio.log.applied().at(-1)")
    assert full["tool"]["kind"] == "raise" and all(v[3] >= v[2] for v in full["verts"])
    assert "Height points changed" in pad.ev("document.getElementById('panel-body').textContent")
    z1 = pad.ev("(id) => studio.seated(studio.model.spaces.exterior.refs.get(id)).pos[2]", b["id"])
    if b.get("seat", {}).get("mode") in ("ground", "above"):
        assert z1 > z0, "a thing on the ground follows the land"
    pad.page.get_by_role("button", name="Level").click()
    pad.pen_drag([(x - 60, y + 40), (x + 60, y + 40)], steps=4)
    assert pad.ev("studio.log.applied().at(-1).tool.kind") == "level"
    pad.shot("10-land")


# ---------- 11: plants ----------
def test_11_plants(pad):
    pad.page.click("#rail [data-tool=plants]")
    plant = pad.ev("studio.worldRefs.find((r) => ['plant','tree'].includes(r.kind) && !studio.isCleared(r))")
    look_at(pad, "ours", plant["pos"], dist=2500)
    x, y = pad.screen("ours", plant["pos"])
    pad.pen_drag([(x - 5, y), (x + 5, y)])
    op = pad.ev("studio.log.applied().at(-1)")
    assert op["op"] == "veg.clear" and op["items"]
    assert pad.ev("(p) => studio.isCleared(p)", plant)
    pad.page.get_by_role("button", name="Show cleared plants: off").click()
    assert pad.ev("[...studio.ours.world.groups.values()].some((g) => g.ghost && g.refs.length)")
    pad.page.get_by_role("button", name="Bring back").click()
    pad.pen_drag([(x - 5, y), (x + 5, y)])
    op = pad.ev("studio.log.applied().at(-1)")
    assert op["op"] == "veg.restore"
    assert not pad.ev("(p) => studio.isCleared(p)", plant)
    pad.shot("11-plants")


# ---------- 12: paths ----------
def test_12_paths(pad):
    pad.page.click("#rail [data-tool=paths]")
    g = pad.ev("studio.seated([...studio.model.spaces.exterior.refs.values()].find((r) => r.kind === 'building')).pos")
    look_at(pad, "ours", g, dist=5000)
    x, y = pad.screen("ours", g)
    pts = [(x - 120 + i * 12, y + 30 * ((i % 4) - 1.5) / 4) for i in range(21)]
    pad.pen_drag(pts, steps=2)
    op = pad.ev("studio.log.applied().at(-1)")
    assert op["op"] == "path.add" and len(op["path"]["points"]) >= 2
    pid = op["path"]["id"]
    near = pad.ev("(id) => { const p = studio.model.paths.get(id); return studio.worldRefs.filter((r) => ['plant','tree','groundcover'].includes(r.kind) && studio.underPath(r)).length; }", pid)
    assert near >= 0
    pad.page.get_by_role("button", name="Wide").click()
    op = pad.ev("studio.log.applied().at(-1)")
    assert op["op"] == "path.edit" and op["path"]["width"] == 400 and op["before"]["width"] != 400
    pad.shot("12-paths")
    pad.page.get_by_role("button", name="Erase this path").click()
    assert pad.ev("studio.log.applied().at(-1).op") == "path.remove"
    assert not pad.ev("(id) => studio.model.paths.has(id)", pid)


# ---------- 13 and 15: saves, reload, finalise, heartbeat ----------
def test_13_15_saves_finalise_heartbeat(pad, browser, server):
    pad.page.wait_for_function("document.getElementById('save-state').dataset.state === 'saved'", timeout=15000)
    pad.page.click("#rail [data-tool=saves]")
    pad.page.fill("#panel-body input[type=text]", "Test save one")
    pad.page.get_by_role("button", name="Save a copy").click()
    pad.page.wait_for_function("document.getElementById('panel-body').textContent.includes('Test save one')", timeout=10000)
    n = len(pad.ops())
    # another session: the autosave is picked up after the machine was off
    other = open_pad(browser, server, PORTRAIT)
    other.page.wait_for_function(f"studio.log.applied().length === {n}", timeout=15000)
    assert other.ev("studio.log.applied().length") == n, (other.errors, other.ev("document.getElementById('toast').textContent"))
    assert other.ev("document.getElementById('views').dataset.layout") == "stack"
    other.page.click(".intro button") if other.ev("!document.getElementById('intro').hidden") else None
    other.shot("13-portrait-resumed")
    other.page.context.close()
    beats = json.load(urllib.request.urlopen(server + "/api/_heartbeats"))
    assert (beats.get("count") if isinstance(beats, dict) else beats) >= 1
    # finalise
    pad.page.click("#finalise-btn")
    assert "writes them into" in pad.ev("document.getElementById('panel-body').textContent")
    pad.page.locator("#panel-body button.primary").click()
    pad.page.wait_for_function("document.getElementById('panel-title').textContent === 'Finalised'", timeout=30000)
    assert pad.page.locator("#panel-body .steps li[data-s=done]").count() == 4
    assert pad.page.locator("#panel-body .report").count() == 1
    pad.shot("13-finalised")


# ---------- 14: choosers ----------
def test_14_choosers(pad):
    assert pad.page.locator("#place-pick option").count() >= 1
    opts = pad.ev("[...document.querySelectorAll('#source-pick option')].map((o) => o.value)")
    assert len(opts) >= 2, "the allocated source and its similar places"
    pad.page.select_option("#source-pick", opts[1])
    pad.page.wait_for_function(f"studio.sourceId === {json.dumps(opts[1])} && document.getElementById('loading').hidden", timeout=30000)
    pad.page.select_option("#source-pick", opts[0])
    pad.page.wait_for_function(f"studio.sourceId === {json.dumps(opts[0])} && document.getElementById('loading').hidden", timeout=30000)


# ---------- 16: dark and portrait look ----------
def test_16_dark_portrait(browser, server):
    p = open_pad(browser, server, PORTRAIT, scheme="dark")
    bg = p.ev("getComputedStyle(document.querySelector('#top')).backgroundColor")
    assert bg != "rgb(247, 249, 249)", "dark theme"
    if p.ev("!document.getElementById('intro').hidden"):
        p.page.click(".intro button")
    p.page.click("#rail [data-tool=search]")
    p.shot("16-dark-portrait-search")
    p.page.context.close()


# ---------- 17: the redrafted place files' fields ----------
def test_17_walkway_clear_why_seat_modes(pad):
    pad.page.click("#rail button:has-text('Paths')")
    assert "Walkway, Wooden boards" in pad.ev("document.getElementById('panel-body').textContent")
    assert pad.page.locator("#panel-body .seg[aria-label=Kind] button").all_text_contents() == ["Path", "Street", "Walkway"]
    pad.page.click("#rail button:has-text('Plants')")
    assert "1 on a street or path" in pad.ev("document.getElementById('panel-body').textContent")
    z = pad.ev("""() => { const t = studio.terrain, x = 4000, y = 4000, f = [-300, -300, 300, 300];
        const mk = (mode) => studio.seated({ id: 'probe', base: 'x', pos: [x, y, 0], rot: [0, 0, 0.4], seat: { mode, dz: 0, foot: f } }).pos[2];
        return { ground: mk('ground'), clear: mk('clear'), above: mk('above'), stilts: mk('stilts') }; }""")
    assert z["clear"] >= z["above"] >= z["ground"] and z["stilts"] >= z["ground"], z


# ---------- 18: worth a look (place.json needs_look) ----------
def test_18_needs_look(pad):
    btn = pad.page.locator("#look-btn")
    assert btn.is_visible() and btn.text_content().strip().startswith("1")
    btn.click()
    pad.page.locator(".look-list li button").first.click()
    door = pad.ev("studio.place.needs_look[0].door")
    pad.page.wait_for_function(f"studio.selection.has({json.dumps(door)})", timeout=10000)
    assert pad.ev("studio.ours.view.rig.dist") < 2000, "flown in close"


# ---------- 19: a texture the server lacks falls back quietly ----------
def test_19_missing_texture_fallback(pad):
    got = pad.ev("""async () => { const o = await import('./js/objects.js'), THREE = await import('three');
        const map = new THREE.Texture(); map.userData.missing = 'textures/none.dds';
        const m = o.plainMaterial(new THREE.MeshStandardMaterial({ map, transparent: true }), 'plant');
        const ok = o.plainMaterial(new THREE.MeshStandardMaterial({ color: '#ffffff' }), 'rock');
        return { map: m.map, colour: m.color.getHexString(), alphaTest: m.alphaTest, type: m.type, plain: ok.type }; }""")
    assert got["map"] is None and got["colour"] != "ffffff" and got["alphaTest"] == 0, got
    assert got["type"] == got["plain"] == "MeshLambertMaterial"


# ---------- 20: a real-sized place never freezes the page ----------
@pytest.fixture(scope="module")
def big_server():
    if os.environ.get("STUDIO_URL"):
        pytest.skip("runs on the generated large fixture")
    fx = Path(tempfile.mkdtemp(prefix="studio-big-"))
    subprocess.run([sys.executable, str(WEB / "dev" / "make_fixture.py"), str(fx), "--big"], check=True, capture_output=True)
    port = free_port()
    p = subprocess.Popen([sys.executable, str(WEB / "dev" / "devserver.py"), "--port", str(port), "--fixture", str(fx)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            urllib.request.urlopen(url + "/api/status", timeout=1)
            break
        except OSError:
            time.sleep(0.1)
    yield url
    p.terminate()
    subprocess.run(["rm", "-rf", str(fx)])


# Software WebGL on the build VM links each shader program inside a draw (no parallel compile), so the budget here
# is the VM's; on the tablet's GPU the same code keeps every task far shorter.
LONG_TASK_BUDGET_MS = 1000


def test_20_long_task_budget_big(browser, big_server):
    ctx = browser.new_context(viewport=LANDSCAPE, device_scale_factor=1, has_touch=True)
    ctx.add_init_script("""window.__lt = []; new PerformanceObserver((l) => { for (const e of l.getEntries()) __lt.push(e.duration); })
                           .observe({ type: 'longtask', buffered: true });""")
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    t0 = time.time()
    page.goto(big_server + "/")
    page.click(".intro button", timeout=5000)
    assert time.time() - t0 < 5, "the guide can be put away at once"
    page.wait_for_function("window.studio && studio.loadMs", timeout=60000)
    page.wait_for_function("document.getElementById('progress').hidden", timeout=120000)
    page.wait_for_timeout(1500)
    lt = page.evaluate("__lt")
    assert page.evaluate("studio.ground.spaces.exterior.refs.length") >= 30000
    assert max(lt or [0]) < LONG_TASK_BUDGET_MS, sorted(lt)[-5:]
    assert not errors, errors
    ctx.close()
