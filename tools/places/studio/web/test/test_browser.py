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
SHOTS = Path(os.environ.get("SHOTS") or tempfile.mkdtemp(prefix="studio-shots-"))
REAL = bool(os.environ.get("STUDIO_URL"))
SLOW = 5 if REAL else 1  # real bundles under software GL load in ~45 s, not ~3 s
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


@pytest.fixture(scope="module")
def server():
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
        self.page.screenshot(path=str(SHOTS / f"{name}.png"))


def open_pad(browser, server, viewport, scheme="light", fresh=True, choose="draft"):
    ctx = browser.new_context(viewport=viewport, device_scale_factor=1, has_touch=True, color_scheme=scheme)
    page = ctx.new_page()
    pad = Pad(page)
    page.goto(server + "/")
    page.wait_for_function("window.studio && studio.ready && studio.log", timeout=60000 * SLOW)
    if REAL:  # the real place builds its land in slices after the first frame
        page.wait_for_function("document.getElementById('progress').hidden", timeout=120000 * SLOW)
    page.wait_for_timeout(500)
    if choose and page.locator("#start .sheet").is_visible():  # saved work: nothing applied until chosen
        if choose == "draft":
            page.get_by_role("button", name="Start from the builder's draft").click()
        else:
            page.get_by_role("button", name=choose).click()
        page.wait_for_function("document.getElementById('start').hidden", timeout=30000 * SLOW)
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


def first_ref(pad, kind, space="exterior"):
    return pad.ev("([k, s]) => [...studio.model.spaces[s].refs.values()].find((r) => r.kind === k)", [kind, space])


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
    assert labels[:6] == ["Select", "Add", "People", "Land", "Plants", "Paths"]


# ---------- 1: two views, layout, full screen, link, fingerprint ----------
def test_01_two_views(pad):
    # built things show as their models arrive (no stand-in boxes)
    pad.page.wait_for_function("studio.stats().drawn.place > 0 && studio.stats().drawn.src > 0", timeout=120000 * SLOW)
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


def test_01_mismatch_warning(browser, server):
    ctx = browser.new_context(viewport=LANDSCAPE, has_touch=True)
    page = ctx.new_page()
    page.route("**/api/status", lambda r: r.fulfill(json={"ground_sha": "aaaaaaaaaaaa", "deployed_sha": "bbbbbbbbbbbb", "match": False}))
    page.goto(server + "/")
    page.wait_for_function("window.studio && studio.status", timeout=30000 * SLOW)
    assert page.evaluate("!document.getElementById('warn').hidden")
    assert "not the one on the play machine" in page.evaluate("document.getElementById('warn').textContent")
    ctx.close()


# ---------- 2: performance, lazy meshes, thumbnails ----------
def test_02_performance_and_lazy_models(pad):
    pad.page.wait_for_function("[...studio.ours.place.groups.values()].some((g) => g.full)", timeout=30000 * SLOW)
    url = pad.ev("import('./js/thumbs.js').then((m) => m.thumb(studio.bases.values().next().value))")
    assert "/api/asset/thumb" in url or url.startswith("data:image/")


# ---------- 3: select, cycle, lasso, gizmo, nudge, duplicate, remove, info ----------
def test_03_select_and_manipulate(pad):
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


# ---------- 4: copy from the source, a group, an enterable building ----------
def test_04_from_the_source(pad):
    if pad.page.locator("#panel-close").is_visible():  # the panel floats over the source view's right side
        pad.page.click("#panel-close")
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
    assert len(ops) >= 2 and all(o["op"] == "ref.add" and o["src"] for o in ops), (n0, ops)
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
    pad.page.wait_for_function("studio.panels.search.results.length > 0", timeout=10000 * SLOW)
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
    # the note bar under the views: the last change alone marked a taste call, with a note
    pad.page.click("#rail [data-tool=select]")
    pad.ev("studio.selection = new Set([studio.log.applied().at(-1).ref.id]); studio.tools.selectionChanged()")
    pad.page.get_by_role("button", name="East", exact=True).click()
    while int(pad.ev("document.getElementById('notebar').dataset.count")) > 1:
        pad.page.click("#notebar .nb-less")
    pad.page.click("#notebar .call")
    pad.page.fill("#notebar .nb-text", "I prefer it by the water")
    pad.page.press("#notebar .nb-text", "Enter")
    last, before = pad.ops()[-1], pad.ops()[-2]
    assert last["call"] == "taste" and last["note"] == "I prefer it by the water"
    assert before["note"] is None and before["call"] == "fault", "the changes left out of the note stay unnoted"
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
    assert pad.page.locator("#panel-body input[aria-label^=\"Starts at\"]").count() >= 1, "stops with times"
    pad.page.locator("#panel-body input[aria-label^=\"Starts at\"]").first.fill("07:30")
    pad.page.locator("#panel-body input[aria-label^=\"Starts at\"]").first.dispatch_event("change")
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
    inside = pad.ev("""(() => { const rs = [...studio.model.spaces[studio.ours.space].refs.values()], b = (r) => studio.bases.get(r.base) || {};
                      return rs.find((r) => /bed/i.test(`${b(r).model} ${b(r).name} ${b(r).edid}`)) || rs.find((r) => r.kind !== 'door'); })()""")
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
    pad.page.wait_for_function("document.getElementById('save-state').dataset.state === 'saved'", timeout=15000 * SLOW)
    pad.page.click("#rail [data-tool=saves]")
    pad.page.fill("#panel-body input[type=text]", "Test save one")
    pad.page.get_by_role("button", name="Save a copy").click()
    pad.page.wait_for_function("document.getElementById('panel-body').textContent.includes('Test save one')", timeout=10000 * SLOW)
    n, ops, digest = len(pad.ops()), json.dumps(pad.ops(), sort_keys=True), pad.ev(DIGEST)
    # another session: the autosave is picked up after the machine was off
    other = open_pad(browser, server, PORTRAIT, choose="Continue the unsaved work")
    other.page.wait_for_function(f"studio.log.applied().length === {n}", timeout=15000 * SLOW)
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


# ---------- 14: choosers ----------
def test_14_choosers(pad):
    assert pad.page.locator("#place-pick option").count() >= 1
    opts = pad.ev("[...document.querySelectorAll('#source-pick option')].map((o) => o.value)")
    assert len(opts) >= 1 and opts[0], "the allocated source first"
    if len(opts) < 2:  # a place with no similar places (real Helstrom): the one source is shown and chosen
        assert pad.ev("studio.sourceId") == opts[0]
        return
    pad.page.select_option("#source-pick", opts[1])
    pad.page.wait_for_function(f"studio.sourceId === {json.dumps(opts[1])} && document.getElementById('loading').hidden", timeout=30000 * SLOW)
    pad.page.select_option("#source-pick", opts[0])
    pad.page.wait_for_function(f"studio.sourceId === {json.dumps(opts[0])} && document.getElementById('loading').hidden", timeout=30000 * SLOW)


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
    assert re.search(r"\d+ on a street or path", pad.ev("document.getElementById('panel-body').textContent"))
    z = pad.ev("""() => { const t = studio.terrain, x = 4000, y = 4000, f = [-300, -300, 300, 300];
        const mk = (mode) => studio.seated({ id: 'probe', base: 'x', pos: [x, y, 0], rot: [0, 0, 0.4], seat: { mode, dz: 0, foot: f } }).pos[2];
        return { ground: mk('ground'), clear: mk('clear'), above: mk('above'), stilts: mk('stilts') }; }""")
    assert z["clear"] >= z["above"] >= z["ground"] and z["stilts"] >= z["ground"], z


# ---------- 19: a texture the server lacks falls back quietly ----------
def test_19_missing_texture_fallback(pad):
    got = pad.ev("""async () => { const o = await import('./js/objects.js'), THREE = await import('three');
        const map = new THREE.Texture(); map.userData.missing = 'textures/none.dds';
        const m = o.plainMaterial(new THREE.MeshStandardMaterial({ map, transparent: true }), 'plant');
        const ok = o.plainMaterial(new THREE.MeshStandardMaterial({ color: '#ffffff' }), 'rock');
        return { map: m.map, colour: m.color.getHexString(), alphaTest: m.alphaTest, type: m.type, plain: ok.type }; }""")
    assert got["map"] is None and got["colour"] != "ffffff" and got["alphaTest"] == 0, got
    assert got["type"] == got["plain"] == "MeshLambertMaterial"


# ---------- saved work is never applied silently ----------
def test_20_notes_for_the_agent(pad, server):
    """A note about the place, and one about a selected thing, reach the server with what they are about."""
    pid = pad.ev("studio.place.place_id")
    pad.ev("studio.selection.clear(); studio.tools.selectionChanged(); studio.tools.use('notes')")
    pad.page.wait_for_selector("textarea.note-text")
    pad.page.fill("textarea.note-text", "More reeds along the bank")
    pad.page.get_by_role("button", name="Leave the note").click()
    pad.page.wait_for_function("document.querySelector('ol.free-notes li')", timeout=10000 * SLOW)
    rid = pad.ev("[...studio.model.spaces.exterior.refs.values()].find((r) => r.kind === 'building').id")
    pad.ev("(id) => { studio.tools.use('select'); studio.selection = new Set([id]); studio.tools.selectionChanged(); }", rid)
    pad.page.get_by_role("button", name="Leave a note about this for the agent").click()
    pad.page.wait_for_selector("textarea.note-text")
    pad.page.fill("textarea.note-text", "Turn this to face the water")
    pad.page.get_by_role("button", name="Leave the note").click()
    pad.page.wait_for_function("document.querySelectorAll('ol.free-notes li').length === 2", timeout=10000 * SLOW)
    notes = json.load(urllib.request.urlopen(f"{server}/api/place/{pid}/notes"))
    assert [n["text"] for n in notes] == ["More reeds along the bank", "Turn this to face the water"]
    assert notes[0]["things"] == [] and [t["id"] for t in notes[1]["things"]] == [rid] and len(notes[1]["view"]["at"]) == 3
    pad.shot("20-notes")
    pad.ev("studio.selection.clear(); studio.tools.selectionChanged(); studio.panels.close()")
    assert not pad.errors, pad.errors


def test_21_compass(pad):
    # each view has a compass; its needle turns with the camera and a tap faces the view north
    assert pad.ev("document.querySelectorAll('.view .compass').length") == 2
    for side, sel in (("ours", "#view-ours"), ("src", "#view-src")):
        pad.ev("(s) => { const v = studio[s].view; v.rig.yaw = 0; v.changed(); }", side)  # the eye east of where it looks
        assert pad.ev(f"document.querySelector('{sel} .compass').dataset.heading") == "270", "looking west"
        assert "rotate(-270deg)" in pad.ev(f"document.querySelector('{sel} .compass .rose').style.transform")
        box = pad.ev(f"(() => {{ const r = document.querySelector('{sel} .compass').getBoundingClientRect(); return [r.width, r.height]; }})()")
        assert min(box) >= 44, box
        pad.page.click(f"{sel} .compass")
        assert pad.ev(f"document.querySelector('{sel} .compass').dataset.heading") == "0", "a tap faces north"
        assert abs(pad.ev("(s) => studio[s].view.rig.yaw", side) + 3.141592653589793 / 2) < 1e-6
    pad.shot("21-compass")


def test_21_effects_never_drawn(pad):
    # the game's effect meshes are never drawn, wherever the mod keeps them (Bethesda names them fx*)
    cases = pad.ev("""import('./js/objects.js').then((m) => [
        { model: 'dlc02/dungeons/apocrypha/clutter/fxapomistlowswirls01.nif' }, { model: 'effects/fxfog01.nif' },
        { model: 'clutter/x.nif', edid: 'FXMistLow01' }, { model: 'clutter/common/candlelanternwithcandle01.nif', edid: 'CandleLantern01' },
        { model: 'landscape/trees/foxtree01.nif' }].map(m.isEffect))""")
    assert cases == [True, True, True, False, False], cases
    shown = pad.ev("""[studio.ours.world, studio.ours.place, studio.src.layer].flatMap((l) => [...l.groups.values()])
        .filter((g) => g.fx && (g.full || []).some((m) => m.visible && m.count)).length""")
    assert shown == 0


def test_21_selected_shows_where(pad):
    pad.page.click("#rail [data-tool=select]")
    b = first_ref(pad, "building")
    pad.ev("(id) => { studio.selection = new Set([id]); studio.tools.selectionChanged(); }", b["id"])
    pos = pad.ev("(id) => studio.seated(studio.model.spaces.exterior.refs.get(id)).pos.map(Math.round)", b["id"])
    where = lambda: pad.ev("document.querySelector('#panel-body dl.where').textContent")  # noqa: E731
    w = where()
    assert f"x {pos[0]}, y {pos[1]}, z {pos[2]}" in w, w
    assert f"Cell{pos[0] // 4096}, {pos[1] // 4096}" in w and "Turned" in w, w
    # it follows the thing when it moves
    pad.page.get_by_role("button", name="East", exact=True).click()
    pad.page.wait_for_function("(x) => document.querySelector('#panel-body dl.where').textContent.includes(`x ${x},`)", arg=pos[0] + 32, timeout=5000 * SLOW)
    pad.shot("21-selected-where")
    # several: the middle of them
    ids = pad.ev("[...studio.model.spaces.exterior.refs.values()].filter((r) => r.kind === 'building').slice(0, 2).map((r) => r.id)")
    pad.ev("(ids) => { studio.selection = new Set(ids); studio.tools.selectionChanged(); }", ids)
    assert "Middle of them" in where()
    pad.ev("studio.log.undo()")


def test_21_lights_seen_and_handled(pad):
    # a light has no model of its own: while selecting it is a small bulb of its colour, picked like anything else
    pad.page.click("#rail [data-tool=select]")
    light = pad.ev("studio.model.spaces.exterior.refs.get('fixplace.l0')")
    lantern = pad.ev("studio.model.spaces.exterior.refs.get('fixplace.lantern0')")
    lp = pad.ev("(id) => studio.seated(studio.model.spaces.exterior.refs.get(id)).pos", light["id"])
    pad.ev("studio.selection.clear(); studio.tools.selectionChanged()")
    look_at(pad, "ours", lp, dist=1800, pitch=1.15)
    pad.page.wait_for_function("studio.ours.place.nBulb >= 2 && studio.ours.place.nRing >= 1", timeout=5000 * SLOW)
    pad.shot("21-lights-overview")
    look_at(pad, "ours", lp, dist=700, pitch=1.3)
    pad.page.wait_for_function("studio.ours.place.nBulb >= 1 && studio.ours.place.bulbs.visible", timeout=5000 * SLOW)
    pad.ev("studio.selection.clear(); studio.tools.selectionChanged()")
    pad.pen_tap(*pad.screen("ours", lp))
    assert pad.ev("[...studio.selection]") == [light["id"]], pad.ev("[...studio.selection]")
    body = pad.ev("document.getElementById('panel-body').textContent")
    assert "reaches 600 units" in body and "casts no shadows" in body and "Fix Lantern" in body, body
    assert pad.ev("studio.ours.place.ringIds.has('fixplace.l0')") and pad.ev("studio.ours.place.nRing") >= 1
    pad.page.wait_for_timeout(200)
    pad.shot("21-light-selected")
    # moving the lantern takes its light with it, in one undo step
    pad.ev("(id) => { studio.selection = new Set([id]); studio.tools.selectionChanged(); }", lantern["id"])
    assert "one light goes with it" in pad.ev("document.getElementById('panel-body').textContent")
    n0 = len(pad.ops())
    pad.page.get_by_role("button", name="East", exact=True).click()
    ops = pad.ops()[n0:]
    assert sorted(o["id"] for o in ops) == sorted([lantern["id"], light["id"]]) and ops[0]["stroke"] == ops[1]["stroke"], ops
    moved = pad.ev("studio.model.spaces.exterior.refs.get('fixplace.l0').pos")
    assert abs(moved[0] - light["pos"][0] - 32) < 0.6 and abs(moved[1] - light["pos"][1]) < 0.6, (moved, light["pos"])
    # a turn carries it round the lantern
    pad.page.get_by_role("button", name="Turn right", exact=True).click()
    last2 = pad.ev("studio.log.applied().slice(-2).map((o) => o.id)")
    assert sorted(last2) == sorted([lantern["id"], light["id"]])
    pad.ev("studio.log.undo()")
    pad.ev("studio.log.undo()")
    assert pad.ev("studio.model.spaces.exterior.refs.get('fixplace.l0').pos") == light["pos"]
    # removing the lantern removes its light; a light alone can be removed by itself
    pad.ev("(id) => { studio.selection = new Set([id]); studio.tools.selectionChanged(); }", lantern["id"])
    n0 = len(pad.ops())
    pad.page.get_by_role("button", name="Remove from our place").click()
    assert sorted(o["id"] for o in pad.ops()[n0:]) == sorted([lantern["id"], light["id"]]) and all(o["op"] == "ref.remove" for o in pad.ops()[n0:])
    pad.ev("studio.log.undo()")
    pad.ev("(id) => { studio.selection = new Set([id]); studio.tools.selectionChanged(); }", light["id"])
    n0 = len(pad.ops())
    pad.page.get_by_role("button", name="Remove from our place").click()
    assert [o["id"] for o in pad.ops()[n0:]] == [light["id"]]
    pad.ev("studio.log.undo()")
    # other tools hide the lights unless the Lights toggle is on
    pad.page.click("#rail [data-tool=land]")
    assert not pad.ev("studio.ours.place.showLights")
    pad.page.wait_for_function("studio.ours.place.nBulb === 0 && !studio.ours.place.bulbs.visible", timeout=5000 * SLOW)
    pad.ev("studio.tools.opts.lights = true; studio.tools.lightsShown()")
    pad.page.wait_for_function("studio.ours.place.nBulb >= 1", timeout=5000 * SLOW)
    pad.ev("studio.tools.opts.lights = false; studio.tools.lightsShown()")
    pad.page.click("#rail [data-tool=select]")
    # inside: the room's lamp is a bulb too, and belongs to its lantern
    door = pad.ev("[...studio.model.spaces.exterior.refs.values()].find((r) => r.door?.to_space && studio.model.spaces[r.door.to_space])")
    pad.ev("(d) => studio.enter(studio.ours, d)", door)
    lamp = pad.ev("[...studio.model.spaces[studio.ours.space].refs.values()].find((r) => r.kind === 'light')")
    pad.ev("(id) => { studio.selection = new Set([id]); studio.tools.selectionChanged(); }", lamp["id"])
    body = pad.ev("document.getElementById('panel-body').textContent")
    assert "casts shadows" in body and "Fix Lantern" in body, body
    look_at(pad, "ours", lamp["pos"], dist=600, pitch=1.0)
    pad.page.wait_for_function("studio.ours.place.nBulb >= 1", timeout=5000 * SLOW)
    pad.shot("21-light-inside")
    pad.page.locator("#view-ours .crumbs button").first.click()
    pad.ev("studio.selection.clear(); studio.tools.selectionChanged()")
    # back outside, the view restored to where it stood (the next tests start from it)
    pad.page.wait_for_function("studio.ours.space === 'exterior' && !studio.ours.returnRig", timeout=30000 * SLOW)
    pad.page.wait_for_timeout(500)


def test_21_invisible_walls(pad):
    # a kept collision box shows with the helpers as a faint outlined box of its real size, one instanced draw
    pad.page.click("#rail [data-tool=select]")
    wall = pad.ev("studio.model.spaces.exterior.refs.get('fixplace.wall0')")
    wp = pad.ev("(id) => studio.seated(studio.model.spaces.exterior.refs.get(id)).pos", wall["id"])
    pad.ev("studio.selection.clear(); studio.tools.selectionChanged()")
    look_at(pad, "ours", wp, dist=2500, pitch=1.2)
    pad.page.wait_for_function("studio.ours.place.nPrim >= 1 && studio.ours.place.primBoxes.visible", timeout=5000 * SLOW)
    assert pad.ev("studio.ours.place.root.children.filter((m) => m.userData.prims && m.visible).length") == 1
    pad.page.wait_for_timeout(300)
    pad.shot("21-invisible-wall")
    # picked by its box; the panel says what it is, whose it is and its size
    pad.pen_tap(*pad.screen("ours", wp))
    assert pad.ev("[...studio.selection]") == [wall["id"]], pad.ev("[...studio.selection]")
    body = pad.ev("document.getElementById('panel-body').textContent")
    assert "an invisible wall: people and the player cannot pass" in body and "Fix Hall" in body, body
    assert "800 by 32 by 240 units" in body, body
    pad.page.wait_for_timeout(200)
    pad.shot("21-invisible-wall-selected")
    # resized by its extents, as one ordinary edit
    n0 = len(pad.ops())
    pad.page.fill(".prim-size input[data-i='0']", "1000")
    pad.page.get_by_role("button", name="Set the size").click()
    ops = pad.ev("(n) => studio.log.applied().slice(n).map((o) => ({ op: o.op, id: o.id, after: o.after }))", n0)
    assert ops == [{"op": "ref.move", "id": wall["id"], "after": {"primitive": {**wall["primitive"], "bounds": [500, 16, 120]}}}], ops
    assert pad.ev("studio.model.spaces.exterior.refs.get('fixplace.wall0').primitive.bounds") == [500, 16, 120]
    pad.ev("studio.log.undo()")
    assert pad.ev("studio.model.spaces.exterior.refs.get('fixplace.wall0').primitive.bounds") == [400, 16, 120]
    # moved and removed like anything else
    pad.ev("(id) => { studio.selection = new Set([id]); studio.tools.selectionChanged(); }", wall["id"])
    n0 = len(pad.ops())
    pad.page.get_by_role("button", name="East", exact=True).click()
    assert [o["id"] for o in pad.ops()[n0:]] == [wall["id"]]
    pad.ev("studio.log.undo()")
    n0 = len(pad.ops())
    pad.page.get_by_role("button", name="Remove from our place").click()
    assert [(o["op"], o["id"]) for o in pad.ops()[n0:]] == [("ref.remove", wall["id"])]
    pad.ev("studio.log.undo()")
    # it belongs to its building: moving, turning, resizing, copying or removing the building takes it along, in one
    # undo step, keeping its offset from the building
    hall = pad.ev("studio.model.spaces.exterior.refs.get('fixplace.b0')")
    pad.ev("(id) => { studio.selection = new Set([id]); studio.tools.selectionChanged(); }", hall["id"])
    assert "one invisible wall goes with it" in pad.ev("document.getElementById('panel-body').textContent")
    n0 = len(pad.ops())
    pad.page.get_by_role("button", name="East", exact=True).click()
    ops = pad.ops()[n0:]
    assert sorted(o["id"] for o in ops) == sorted([hall["id"], wall["id"]]) and ops[0]["stroke"] == ops[1]["stroke"], ops
    hp = pad.ev("studio.model.spaces.exterior.refs.get('fixplace.b0').pos")
    moved = pad.ev("studio.model.spaces.exterior.refs.get('fixplace.wall0').pos")
    assert abs((moved[0] - wall["pos"][0]) - (hp[0] - hall["pos"][0])) < 0.6 and abs(moved[1] - wall["pos"][1]) < 0.6, (moved, wall["pos"], hp)
    pad.ev("studio.log.undo()")
    assert pad.ev("studio.model.spaces.exterior.refs.get('fixplace.wall0').pos") == wall["pos"]
    assert pad.ev("studio.model.spaces.exterior.refs.get('fixplace.b0').pos") == hall["pos"]
    # a turn carries it round the building, turned the same
    pad.page.get_by_role("button", name="Turn right", exact=True).click()
    w1 = pad.ev("studio.model.spaces.exterior.refs.get('fixplace.wall0')")
    h1 = pad.ev("studio.model.spaces.exterior.refs.get('fixplace.b0')")
    assert abs((w1["rot"][2] - wall["rot"][2]) - (h1["rot"][2] - hall["rot"][2])) < 1e-3, (w1["rot"], h1["rot"])
    d0 = ((wall["pos"][0] - hall["pos"][0]) ** 2 + (wall["pos"][1] - hall["pos"][1]) ** 2) ** 0.5
    d1 = ((w1["pos"][0] - h1["pos"][0]) ** 2 + (w1["pos"][1] - h1["pos"][1]) ** 2) ** 0.5
    assert abs(d0 - d1) < 1, (d0, d1)
    pad.ev("studio.log.undo()")
    # a copy of the building comes with a copy of its wall, seated on the copy
    n0 = len(pad.ops())
    pad.ev("studio.tools.duplicate()")
    adds = pad.ev("(n) => studio.log.applied().slice(n).filter((o) => o.op === 'ref.add').map((o) => o.ref)", n0)
    assert len(adds) == 2, adds
    hall2 = next(r for r in adds if not r.get("primitive"))
    wall2 = next(r for r in adds if r.get("primitive"))
    assert wall2["seat"]["on"] == hall2["id"], wall2["seat"]
    pad.ev("studio.log.undo()")
    # removed with it
    pad.ev("(id) => { studio.selection = new Set([id]); studio.tools.selectionChanged(); }", hall["id"])
    n0 = len(pad.ops())
    pad.page.get_by_role("button", name="Remove from our place").click()
    assert sorted((o["op"], o["id"]) for o in pad.ops()[n0:]) == sorted([("ref.remove", hall["id"]), ("ref.remove", wall["id"])])
    pad.ev("studio.log.undo()")
    assert not pad.ev("studio.model.spaces.exterior.refs.get('fixplace.wall0').removed")
    # the plain view never shows it (nor picks it: picking skips helpers while they are hidden)
    pad.ev("studio.selection.clear(); studio.tools.selectionChanged()")
    pad.page.click("#rail [data-tool=land]")
    pad.page.wait_for_function("studio.ours.place.nPrim === 0 && !studio.ours.place.primBoxes.visible", timeout=5000 * SLOW)
    assert not pad.ev("studio.ours.place.showLights")
    pad.page.click("#rail [data-tool=select]")


def test_21_grass_at_viewing_distance(pad):
    # the land texture's grass grows close up and from where one looks at a town (no cut-off at a short range)
    assert pad.ev("studio.ours.grass.on")
    g = pad.ev("studio.seated([...studio.model.spaces.exterior.refs.values()].find((r) => r.kind === 'building')).pos")
    for dist in (1500, 9000):
        look_at(pad, "ours", g, dist=dist, pitch=0.8)
        pad.page.wait_for_function("studio.ours.grass.refs.length > 0 && studio.ours.grass.drawn > 0", timeout=60000 * SLOW)
    # thinned with distance: fewer blades per area from afar, and the larger ring is capped
    assert pad.ev("studio.ours.grass.refs.length") <= 6000
    pad.shot("21-grass-town-distance")


def test_21_world_map(pad, browser, server):
    pad.page.wait_for_function("document.getElementById('atlas-btn').dataset.built === '1'", timeout=10000 * SLOW)
    pad.page.click("#atlas-btn")
    assert pad.ev("!document.getElementById('atlas').hidden")
    assert pad.ev("document.querySelector('#atlas iframe').src").endswith(f"/atlas/index.html#place={pad.pid}")
    frame = pad.page.frame_locator("#atlas iframe")
    if not REAL:  # the dev server's stand-in Atlas shows the place it was asked to open
        assert frame.locator("#place").text_content(timeout=10000 * SLOW) == pad.pid
    pad.shot("21-world-map")
    pad.page.click("#atlas-close")
    assert pad.ev("document.getElementById('atlas').hidden")
    # when the Atlas has not been built, the button says so plainly
    ctx = browser.new_context(viewport=LANDSCAPE, has_touch=True)
    page = ctx.new_page()
    page.route("**/atlas/**", lambda r: r.fulfill(status=404, body="the Atlas has not been built"))
    page.goto(server + "/")
    page.wait_for_function("document.getElementById('atlas-btn').dataset.built === '0'", timeout=30000 * SLOW)
    assert "not built" in page.evaluate("document.getElementById('atlas-btn').textContent")
    ctx.close()


def test_22_start_choice(pad, browser, server):
    pid = pad.pid
    saves = json.load(urllib.request.urlopen(f"{server}/api/place/{pid}/saves"))
    auto = next((x for x in saves if x["save_id"] == "autosave" and x["ops"]), None)
    assert auto, "an earlier test left unsaved work"
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
    p.page.wait_for_function("document.querySelector('#start .older')", timeout=10000 * SLOW)
    assert "Made on an older draft" in p.ev("document.querySelector('#start .older').textContent")
    p.shot("22-start-choice")
    b = p.page.get_by_role("button", name="Discard the unsaved work")
    b.click()
    b.click()
    p.page.wait_for_function("!document.getElementById('start').textContent.includes('Unsaved work from')", timeout=10000 * SLOW)
    left = {x["save_id"]: x["ops"] for x in json.load(urllib.request.urlopen(f"{server}/api/place/{pid}/saves"))}
    assert left.get("autosave", 0) == 0 and left["older-draft"] == auto["ops"]
    p.page.get_by_role("button", name="Start from the builder's draft").click()
    assert p.ev("studio.log.applied().length") == 0
    p.page.context.close()


# ---------- 23: what things hold and who people are ----------
def test_23_contents_and_identities(browser, server):
    """A container's things with their reasons; a thing added, counted, removed and undone; a thing above the place's
    ceiling refused with its reason; a thing laid out; a person's identity, carried things and wares edited; the
    content ops in a named save."""
    if REAL:
        pytest.skip("drives the fixture's stock (the real place's is authored by lane S2)")
    p = open_pad(browser, server, LANDSCAPE)
    if p.ev("!document.getElementById('intro').hidden"):
        p.page.click("#intro button")
    body = lambda: p.ev("document.getElementById('panel-body').innerText")  # noqa: E731
    last = lambda: p.ev("studio.log.applied().at(-1)")  # noqa: E731
    chest = p.ev("studio.model.stock.containers[0]")
    door = p.ev("(s) => [...studio.model.spaces.exterior.refs.values()].find((r) => r.door?.to_space === s)", chest["space"])
    p.ev("(d) => studio.enter(studio.ours, d)", door)
    p.ev("(id) => { studio.tools.use('select'); studio.selection = new Set([id]); studio.tools.selectionChanged(); }", chest["ref"])
    text = body()
    assert "What it holds" in text and "1 × Iron Sword" in text and "Why: The smith's spare blade" in text, text
    assert "Novice" in text and "Belongs to" in text and "Ada Fixwright's household" in text
    assert "T1 Common" in text and "25 gold" in text
    top = "(t) => [...document.querySelectorAll('#panel-body h3')].find((h) => h.textContent === t).scrollIntoView({ block: 'start' })"
    p.ev(top, "What it holds")
    p.shot("23-container-contents")
    # add a thing from the search, one more of it, remove it, and undo back to where it was
    n0 = len(p.ops())
    p.page.fill("#panel-body input[aria-label='Find a thing to add']", "war axe")
    p.page.get_by_role("button", name="Add Iron War Axe").click()
    op = last()
    assert op["op"] == "stock.container.set" and op["before"]["ref"] == chest["ref"]
    assert [i["item"] for i in op["container"]["items"]][-1] == "Fix.esm:00B008"
    assert op["container"]["items"][-1]["why"] == "The owner added it in the studio."
    assert "1 × Iron War Axe" in body() and "Why: The owner added it in the studio." in body()
    p.page.get_by_role("button", name="One more Iron War Axe").click()
    assert last()["container"]["items"][-1]["count"] == 2 and "2 × Iron War Axe" in body()
    p.page.get_by_role("button", name="Remove Iron War Axe").click()
    assert "Iron War Axe" not in body()
    assert [o["op"] for o in p.ops()[n0:]] == ["stock.container.set"] * 3
    p.ev("studio.log.undo()")
    assert "2 × Iron War Axe" in body(), "undo brings it back"
    p.ev("studio.log.undo(); studio.log.undo()")
    assert p.ev("(r) => studio.model.stock.containers.find((c) => c.ref === r).items.length", chest["ref"]) == len(chest["items"])
    assert len(p.ops()) == n0
    # a thing above the place's ceiling is listed with its reason and refused
    p.page.fill("#panel-body input[aria-label='Find a thing to add']", "glass")
    refused = p.page.locator("#panel-body li.refused", has_text="Glass Sword")
    refused.wait_for(timeout=10000)
    assert "above this place's ceiling T2 Sound" in refused.inner_text()
    p.page.get_by_role("button", name="Add Glass Sword").click()
    assert len(p.ops()) == n0, "a refused thing is never added"
    assert "Not allowed" in p.ev("document.getElementById('toast').textContent")
    p.shot("23-refused-with-reason")
    p.page.select_option("#panel-body select[aria-label=Lock]", "Apprentice")
    assert last()["container"]["lock"] == "Apprentice" and "lock Novice → Apprentice" in p.ev("studio.describe(studio.log.applied().at(-1))")
    # a thing laid out on the table shows its reason
    table = p.ev("studio.model.stock.loose[0].on")
    p.ev("(id) => { studio.selection = new Set([id]); studio.tools.selectionChanged(); }", table)
    assert "Laid out on it" in body() and "Her one good ring" in body()
    # a person: identity, what they carry, what they sell
    p.ev("studio.people.select('fixplace.p1')")
    text = body()
    assert "Who they are" in text and "as head" in text and "W3 Modest" in text and "the village forge" in p.ev(
        "document.querySelector('#panel-body input[aria-label=Trade]').value")
    assert "What they carry" in text and "Why: A smith's hammer." in text
    assert "What they sell" in text and "3 × Iron Sword" in text
    p.page.select_option("#panel-body select[aria-label=Wealth]", "W4")
    assert last()["op"] == "identity.edit" and last()["person"]["wealth"] == "W4" and last()["before"]["wealth"] == "W3"
    p.page.fill("#panel-body textarea[aria-label=Backstory]", "She came down the river with nothing but a hammer.")
    p.page.locator("#panel-body textarea[aria-label=Backstory]").dispatch_event("change")
    assert last()["person"]["notes"][0]["text"].startswith("She came down the river")
    p.page.fill("#panel-body input[aria-label=Trade]", "the forge and the boats' iron")
    p.page.locator("#panel-body input[aria-label=Trade]").dispatch_event("change")
    assert last()["person"]["trade"] == "the forge and the boats' iron"
    name = p.page.locator("#panel-body label.field:has-text('Name') input").first
    name.fill("Ada Hot-Hand")
    name.dispatch_event("change")
    pair = p.ops()[-2:]
    assert [o["op"] for o in pair] == ["identity.edit", "person.edit"] and pair[0]["stroke"] == pair[1]["stroke"], pair
    assert p.ev("studio.model.identities.people.find((x) => x.id === 'fixplace.p1').name") == "Ada Hot-Hand"
    p.page.locator("#panel-body input[aria-label=\"Trader's gold\"]").fill("450")
    p.page.locator("#panel-body input[aria-label=\"Trader's gold\"]").dispatch_event("change")
    assert last()["op"] == "stock.trader.set" and last()["trader"]["gold"] == 450
    p.page.fill("#panel-body input[aria-label='Find a thing to add'] >> nth=0", "potion")
    p.page.get_by_role("button", name="Add Potion of Minor Healing").first.click()
    assert last()["op"] == "stock.possessions.set" and last()["possessions"]["items"][-1]["item"] == "Fix.esm:00B006"
    p.ev(top, "Who they are")
    p.shot("23-person-identity")
    p.ev(top, "What they carry")
    p.shot("23-person-carries-and-sells")
    # the history says it in words, and the ops are in a named save like any other edit
    p.page.click("#rail [data-tool=history]")
    hist = body()
    assert "Ada Hot-Hand: wealth W3 → W4" not in hist and "Ada Fixwright: wealth W3 → W4" in hist, hist
    p.page.click("#rail [data-tool=saves]")
    p.page.fill("#panel-body input[type=text]", "Stock test")
    p.page.get_by_role("button", name="Save a copy").click()
    p.page.wait_for_function("document.getElementById('panel-body').textContent.includes('Stock test')", timeout=10000)
    save = json.load(urllib.request.urlopen(f"{server}/api/place/{p.ev('studio.place.place_id')}/saves/stock-test"))
    kinds = [o["op"] for o in save["ops"]]
    assert {"stock.container.set", "identity.edit", "person.edit", "stock.trader.set", "stock.possessions.set"} <= set(kinds), kinds
    assert all(o["call"] in ("fault", "taste") for o in save["ops"])
    assert not p.errors, p.errors
    p.page.context.close()


# ---------- 24: one note for the changes since the last note ----------
def test_24_note_bar(pad, server):
    """Three edits, one note in the bar under the views: the note covers exactly those three, the count starts again,
    undo and redo keep the note with what is applied, a save holds the note once and loads back the same, and the
    History panel gives picked changes one note, edits it and takes it away."""
    bar = "document.getElementById('notebar')"
    pad.ev("studio.panels.close()")
    assert pad.ev(f"!{bar}.hidden")
    # the bar is in the page's flow: below the views, never over the panel or a view's controls
    pad.page.click("#rail [data-tool=history]")
    over = pad.ev(f"""(() => {{ const b = {bar}.getBoundingClientRect(), p = document.getElementById('panel').getBoundingClientRect(),
                      t = document.querySelector('#view-ours .tilt').getBoundingClientRect();
                      return [b.top >= p.bottom - 1, b.top >= t.bottom - 1, b.bottom <= innerHeight + 1, b.height]; }})()""")
    assert over[:3] == [True, True, True] and over[3] <= 120, over
    pad.ev("studio.panels.close()")
    p0 = pad.ev("studio.noteBar.pending().length")
    rid = pad.ev("[...studio.model.spaces.exterior.refs.values()].find((r) => r.kind === 'building').id")
    pad.ev("(id) => { studio.tools.use('select'); studio.selection = new Set([id]); studio.tools.selectionChanged(); }", rid)
    for label in ["East", "North", "Turn right"]:
        pad.page.get_by_role("button", name=label, exact=True).click()
    assert int(pad.ev(f"{bar}.dataset.count")) == p0 + 3
    assert f"{p0 + 3} changes since your last note" in pad.ev(f"{bar}.querySelector('.nb-count').textContent")
    for _ in range(p0):
        pad.page.click("#notebar .nb-less")
    assert "The last 3 changes" in pad.ev(f"{bar}.querySelector('.nb-count').textContent") or p0 == 0
    pad.page.fill("#notebar .nb-text", "stalls must never block a walkway")
    pad.page.click("#notebar .nb-go")
    ops = pad.ops()
    three = ops[-3:]
    assert len({o["note_group"] for o in three}) == 1 and three[0]["note_group"], three
    assert all(o["note"] == "stalls must never block a walkway" for o in three)
    assert p0 == 0 or ops[-4]["note_group"] != three[0]["note_group"], "only the counted changes"
    assert pad.ev(f"{bar}.dataset.count") == "0" and pad.ev(f"{bar}.querySelector('.nb-text').value") == ""
    assert pad.ev("studio.log.notesFor().filter((n) => n.text === 'stalls must never block a walkway').length") == 1
    pad.shot("24-note-bar")
    # the Notes panel: the note with its changes; Select picks the thing they moved
    pad.ev("studio.tools.use('notes')")
    pad.page.wait_for_selector("ol.change-notes li")
    assert "About 3 changes" in pad.ev("document.querySelector('ol.change-notes li').textContent")
    pad.shot("24-notes-panel")
    pad.ev("studio.selection.clear(); studio.tools.selectionChanged()")
    pad.ev("studio.tools.use('notes')")
    pad.page.wait_for_selector("ol.change-notes li")
    pad.page.locator("ol.change-notes li").first.get_by_role("button", name="Select").click()
    assert pad.ev("[...studio.selection]") == [rid]
    # undo keeps it consistent: the note covers what is applied, and the bar counts nothing new
    pad.page.click("#undo")
    gid = three[0]["note_group"]
    groups = "(g) => import('./js/note_groups.js').then((m) => m.groupsOf(studio.log.applied(), studio.log.notes).filter((x) => x.id === g).map((x) => x.ops.length))"
    assert pad.page.evaluate(groups, gid) == [2]
    assert pad.ev(f"{bar}.dataset.count") == "0"
    pad.page.click("#redo")
    assert pad.page.evaluate(groups, gid) == [3]
    # the save holds the note once, and loads back with each note on its changes
    pad.page.click("#rail [data-tool=saves]")
    pad.page.fill("#panel-body input[type=text]", "Notes test")
    pad.page.get_by_role("button", name="Save a copy").click()
    pad.page.wait_for_function("document.getElementById('panel-body').textContent.includes('Notes test')", timeout=10000 * SLOW)
    save = json.load(urllib.request.urlopen(f"{server}/api/place/{pad.ev('studio.place.place_id')}/saves/notes-test"))
    assert [n["text"] for n in save["notes"]].count("stalls must never block a walkway") == 1
    assert [o["n"] for o in save["ops"] if o.get("note_group") == gid] == [o["n"] for o in three]
    assert {o.get("note_group") for o in save["ops"]} - {None} <= {n["id"] for n in save["notes"]}
    before = json.dumps(pad.ops(), sort_keys=True)
    pad.ev("(s) => studio.loadSave(s)", save)
    assert json.dumps(pad.ops(), sort_keys=True) == before
    # History: two changes picked and given one note; the note edited; then taken away
    pad.page.click("#rail [data-tool=history]")
    picks = pad.page.locator("ol.history li button[aria-label='Choose this change']")
    k = picks.count()
    picks.nth(k - 1).click()
    picks.nth(k - 2).click()
    pad.page.fill("input[aria-label='One note for the chosen changes']", "turned the wrong way")
    pad.page.get_by_role("button", name="Note the chosen").click()
    ops = pad.ops()
    assert ops[-1]["note"] == ops[-2]["note"] == "turned the wrong way" and ops[-3]["note"] == "stalls must never block a walkway"
    pad.page.locator("ol.history .said", has_text="turned the wrong way").first.click()
    assert pad.ev("document.querySelector(\"input[aria-label='One note for the chosen changes']\").value") == "turned the wrong way"
    pad.page.fill("input[aria-label='One note for the chosen changes']", "turned to face the wall")
    pad.page.get_by_role("button", name="Note the chosen").click()
    ops = pad.ops()
    assert ops[-1]["note"] == ops[-2]["note"] == "turned to face the wall" and ops[-1]["note_group"] == ops[-2]["note_group"]
    pad.page.locator("ol.history .said", has_text="turned to face the wall").first.click()
    pad.page.get_by_role("button", name="Take their note away").click()
    ops = pad.ops()
    assert ops[-1]["note"] is None and ops[-2]["note"] is None and ops[-3]["note"] == "stalls must never block a walkway"
    pad.shot("24-history-notes")
    pad.ev("studio.selection.clear(); studio.tools.selectionChanged(); studio.panels.close()")
    assert not pad.errors, pad.errors


# ---------- 25: day and night ----------
# The mean brightness (0..255) of a square of a view's canvas round a game point.
BRIGHT = """([side, pos, half]) => { const v = studio[side].view, c = v.renderer.domElement, r = v.canvas.getBoundingClientRect(),
  b = c.getBoundingClientRect(), s = v.toScreen(pos), k = c.width / b.width;
  const x = Math.round((r.left - b.left + s.x - half) * k), y = Math.round((r.top - b.top + s.y - half) * k), w = Math.round(2 * half * k);
  const t = document.createElement('canvas'); t.width = t.height = w; const g = t.getContext('2d'); g.drawImage(c, x, y, w, w, 0, 0, w, w);
  const d = g.getImageData(0, 0, w, w).data; let sum = 0; for (let i = 0; i < d.length; i += 4) sum += (d[i] + d[i + 1] + d[i + 2]) / 3;
  return sum / (d.length / 4); }"""


def test_25_day_and_night(pad):
    """Night is lit by the game's data and differs from day; a light added lights its spot at once, as a real light
    and as a pool; taking it away darkens the spot again; a room is lit by its own lighting; the time of day drives
    both views while the People tool is on."""
    pad.ev("studio.panels.close(); studio.tools.use('select'); studio.selection.clear(); studio.tools.selectionChanged()")
    lamp = pad.ev("[...studio.model.spaces.exterior.refs.values()].find((r) => r.kind === 'light')")
    assert lamp, "the place has a light"
    x, y = lamp["pos"][0] + 300, lamp["pos"][1] + 300
    spot = [x, y, pad.ev("([x, y]) => studio.terrain.heightAt(x, y)", [x, y])]
    # what stands on the ground is put away while the spot is measured, so nothing stands over it
    pad.ev("studio.ours.world.root.visible = false; studio.ours.place.root.visible = false")
    look_at(pad, "ours", spot, dist=1800, pitch=1.45)
    pad.page.wait_for_timeout(400)
    day = pad.ev(BRIGHT, ["ours", spot, 60])
    sky_day = pad.ev("studio.ours.view.scene.background.getHexString()")
    pad.shot("25-day")
    pad.page.click("#view-ours .daynight [data-mode=night]")
    pad.page.wait_for_timeout(500)
    st = pad.ev("studio.ours.view.lighting.state()")
    assert st["mode"] == "night" and not st["plain"] and st["weather"] == "FixClear", st
    assert st["lights"] >= 1 and st["real"] >= 1 and st["lights"] == st["real"] + st["pools"], st
    assert pad.ev("studio.ours.view.scene.background.getHexString()") != sky_day, "the night sky is the weather's"
    assert pad.ev("document.querySelector('#view-ours .daynight [data-mode=night]').getAttribute('aria-pressed')") == "true"
    assert pad.ev("studio.src.view.lighting.state().mode") == "day", "each view has its own switch"
    unlit = pad.ev(BRIGHT, ["ours", spot, 60])
    assert abs(unlit - day) > 3, (unlit, day)
    # a light added over the spot lights it at once, as a real light
    n0 = st["lights"]
    pad.ev("""([base, p]) => studio.push({ op: 'ref.add', ref: { id: 'test.lamp', base, kind: 'light', pos: p, rot: [0, 0, 0], scale: 1,
             seat: { mode: 'free' } } })""", [lamp["base"], [spot[0], spot[1], spot[2] + 150]])
    pad.page.wait_for_timeout(400)
    st = pad.ev("studio.ours.view.lighting.state()")
    assert st["lights"] == n0 + 1 and pad.ev("studio.ours.view.lighting.nearest.length") >= 1, st
    lit = pad.ev(BRIGHT, ["ours", spot, 60])
    assert lit > unlit + 5, (lit, unlit)
    pad.shot("25-night")
    # and as a pool: every light that is not one of the few real ones still lights its spot
    pad.ev("studio.ours.view.lighting.maxReal = 0; studio.ours.view.lighting.invalidate()")
    pad.page.wait_for_timeout(400)
    st = pad.ev("studio.ours.view.lighting.state()")
    assert st["real"] == 0 and st["pools"] >= 1, st
    pooled = pad.ev(BRIGHT, ["ours", spot, 60])
    assert pooled > unlit + 5, (pooled, unlit)
    pad.shot("25-night-pools")
    pad.ev("studio.ours.view.lighting.maxReal = 6; studio.ours.view.lighting.invalidate()")
    # taking the light away darkens its spot at once; undo brings it back
    pad.ev("() => studio.push({ op: 'ref.remove', id: 'test.lamp', before: JSON.parse(JSON.stringify(studio.model.spaces.exterior.refs.get('test.lamp'))) })")
    pad.page.wait_for_timeout(400)
    assert pad.ev("studio.ours.view.lighting.state().lights") == n0
    dark = pad.ev(BRIGHT, ["ours", spot, 60])
    assert dark < lit - 5, (dark, lit)
    pad.page.click("#undo")
    pad.page.wait_for_timeout(300)
    assert pad.ev("studio.ours.view.lighting.state().lights") == n0 + 1
    assert pad.ev(BRIGHT, ["ours", spot, 60]) > dark + 5, "the light is back"
    pad.page.click("#undo")   # and the test's light goes
    # a room by night: its own lighting
    room = pad.ev("Object.keys(studio.model.spaces).find((s) => s !== 'exterior')")
    if room:
        pad.ev("(s) => studio.showSpace(studio.ours, s)", room)
        pad.page.wait_for_timeout(300)
        rs = pad.ev("studio.ours.view.lighting.state()")
        assert rs["mode"] == "night" and not rs["plain"], rs
        pad.shot("25-room-night")
        pad.ev("studio.showSpace(studio.ours, 'exterior')")
    # the time of day drives both views while the People tool is on
    pad.ev("studio.tools.use('people')")
    pad.ev("studio.setTime(12)")
    assert pad.ev("[studio.ours.view.lighting.mode, studio.src.view.lighting.mode]") == ["day", "day"]
    pad.ev("studio.setTime(22.5)")
    assert pad.ev("[studio.ours.view.lighting.mode, studio.src.view.lighting.mode]") == ["night", "night"]
    pad.page.click("#view-src .daynight [data-mode=day]")
    assert pad.ev("studio.time") == 12 and pad.ev("studio.ours.view.lighting.mode") == "day"
    pad.ev("studio.tools.use('select'); studio.ours.world.root.visible = true; studio.ours.place.root.visible = true; studio.ours.view.redraw()")
    assert not pad.errors, pad.errors
