"""A ref hidden when the page loads is drawn after a Quest state switch shows it (headless Chromium).

The fixture's place gets a living tree and its dead twin on one enable parent; the twin has a base and model of its
own, so no group of the page holds its model before the switch. The page starts in the default state (the twin
hidden), the camera is framed on the twin's spot, the state is switched, and the twin must then be drawn: its model
loaded and its pixels on the canvas (the spot changes colour), not only a member of the scene. The agent view's
shot must also wait for a model a switch asks for (the look verbs' captures).
Run: ~/.argonia/venv/bin/python -m pytest -q tools/places/studio/web/test/test_state_switch_draws.py"""
import json
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
OPP = "SetEnableStateToOppositeOfParent"


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def add_states(fx: Path):
    d = fx / "bundles" / "draft.fixplace"
    p = d / "spaces" / "exterior" / "refs.jsonl"
    rows = [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
    tree = next(r for r in rows if r.get("kind") in ("building", "static") and not r.get("primitive"))
    bp = d / "bases.jsonl"
    bases = [json.loads(x) for x in bp.read_text().splitlines() if x.strip()]
    tb = next(b for b in bases if b["key"] == tree["base"])
    dead = dict(tb, key="Fix.esm:00DEAD", edid="FixDeadTwin", model="fix/fixdeadtwin.nif", kind="tree")
    # a second twin of its own base on the living tree's model: the model is in the page before the switch, so it
    # arrives as a promise already kept (the case the agent shot used to miss)
    same = dict(tb, key="Fix.esm:00DEA2", edid="FixDeadTwinSameModel")
    bp.write_text("".join(json.dumps(b) + "\n" for b in bases + [dead, same]))
    at = tree["pos"]
    mk = lambda rid, **kw: dict(tree, id=rid, pos=[at[0] + 1500, at[1] + 1500, at[2]], src=None, seat={"mode": "free", "dz": 0}, **kw)  # noqa: E731
    rows += [dict(mk("fixplace.PARENT"), kind="marker"),
             dict(mk("fixplace.HIST", enable_parent={"ref": "fixplace.PARENT", "flags": "0"}), pos=[at[0] + 3000, at[1] + 3000, at[2]]),
             dict(mk("fixplace.DEAD", enable_parent={"ref": "fixplace.PARENT", "flags": OPP}), base=dead["key"], kind="tree"),
             dict(mk("fixplace.DEAD2", enable_parent={"ref": "fixplace.PARENT", "flags": OPP}), pos=[at[0] + 1500, at[1] + 2200, at[2]],
                  base=same["key"])]
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    (d / "states.jsonl").write_text(
        json.dumps({"id": "living", "name": "Hist living", "default": True, "parents": {"fixplace.PARENT": True}}) + "\n"
        + json.dumps({"id": "dead", "name": "Hist dead", "parents": {"fixplace.PARENT": False}}) + "\n")
    return [at[0] + 1500, at[1] + 1500, at[2]]


@pytest.fixture(scope="module")
def page():
    fx = Path(tempfile.mkdtemp(prefix="studio-switch-fixture-"))
    subprocess.run([sys.executable, str(WEB / "dev" / "make_fixture.py"), str(fx)], check=True, capture_output=True)
    spot = add_states(fx)
    port = free_port()
    srv = subprocess.Popen([sys.executable, str(WEB / "dev" / "devserver.py"), "--port", str(port), "--fixture", str(fx)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            urllib.request.urlopen(url + "/api/status", timeout=1)
            break
        except OSError:
            time.sleep(0.1)
    with pw.sync_playwright() as p:
        b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        pg = b.new_context(viewport={"width": 1280, "height": 800}, device_scale_factor=1).new_page()
        pg.errors = []
        pg.on("pageerror", lambda e: pg.errors.append(str(e)))
        pg.goto(url + "/")
        pg.wait_for_function("window.studio && studio.ready && studio.log", timeout=60000)
        pg.wait_for_timeout(500)
        if pg.locator("#start .sheet").is_visible():
            pg.get_by_role("button", name="Start from the builder's draft").click()
            pg.wait_for_function("document.getElementById('start').hidden", timeout=30000)
        if pg.locator("#intro").is_visible():
            pg.click("#intro button")
        pg.spot, pg.base = spot, url
        yield pg
        b.close()
    srv.terminate()
    subprocess.run(["rm", "-rf", str(fx)])


# How many pixels the twin covers in the view's camera: the view's scene as the view left it (no cull of ours, so a
# view that never switched the model on counts none), the twin's meshes alone against nothing (the fixture's boxes
# crowd its spot).
TWIN_PIXELS = """async () => {
  const v = studio.ours.view, r = v.renderer, W = 320, H = 240;
  const g = [...studio.ours.place.groups.values()].find((g) => g.refs.some((x) => x.id === 'fixplace.DEAD'));
  if (!g || !g.full) return 0;
  const mine = new Set(g.full), kept = [];
  v.scene.traverse((o) => { if (o.isMesh && !mine.has(o) && o.visible) { o.visible = false; kept.push(o); } });
  const rt = new THREE.WebGLRenderTarget(W, H), a = new Uint8Array(W * H * 4), b = new Uint8Array(W * H * 4);
  const cam = v.camera.clone(); cam.aspect = W / H; cam.updateProjectionMatrix();
  r.setScissorTest(false); r.setRenderTarget(rt); r.setViewport(0, 0, W, H);
  r.render(v.scene, cam); r.readRenderTargetPixels(rt, 0, 0, W, H, a);
  const vis = g.full.map((m) => m.visible); for (const m of g.full) m.visible = false;
  r.render(v.scene, cam); r.readRenderTargetPixels(rt, 0, 0, W, H, b);
  g.full.forEach((m, i) => { m.visible = vis[i]; }); for (const o of kept) o.visible = true;
  r.setRenderTarget(null); r.setScissorTest(true); rt.dispose(); v.redraw();
  let n = 0; for (let i = 0; i < a.length; i += 4) if (Math.abs(a[i] - b[i]) + Math.abs(a[i + 1] - b[i + 1]) + Math.abs(a[i + 2] - b[i + 2]) > 30) n++;
  return n;
}"""


def test_a_switch_draws_the_ref_it_shows(page):
    assert page.eval_on_selector("#state-pick", "s => s.value") == "living"
    assert not page.evaluate("studio.ours.place.byId.has('fixplace.DEAD')")
    x, y, z = page.spot
    page.evaluate("""([x, y, z]) => { const v = studio.ours.view; v.frame([x - 900, y - 900, x + 900, y + 900, z + 300]);
        v.rig.dist = 4000; v.rig.pitch = 0.5; v.changed(); }""", [x, y, z])
    page.wait_for_timeout(1500)
    page.evaluate("studio.setQuestState('dead')")
    # the page is left to itself, as the owner leaves it after choosing the state: no touch, no call of ours
    page.wait_for_function("""() => { const g = [...studio.ours.place.groups.values()].find((g) => g.refs.some((r) => r.id === 'fixplace.DEAD'));
        return !!g?.full?.[0]?.visible; }""", timeout=30000)
    page.wait_for_timeout(500)
    n = page.evaluate(TWIN_PIXELS)
    assert n > 200, f"the dead twin covers {n} pixels of the view after the switch"
    assert not page.errors, page.errors


def test_the_agent_shot_waits_for_a_model_a_switch_asks_for(page):
    """The look verbs' page in the start, then the agent switches to the dead state and shoots at once: the shot
    waits for the second twin's model (one the page already holds), so nothing is waiting and the twin is drawn."""
    page.goto(page.base + "/?agent=1")     # the look verbs' page: it starts in the game's start, the twin hidden
    page.wait_for_function("window.agent && studio.ready", timeout=60000)
    assert not page.evaluate("studio.ours.place.byId.has('fixplace.DEAD')")
    x, y, z = page.spot
    out = page.evaluate("""async ([x, y, z]) => {
        // on the second twin from the north, its own-model brother (DEAD) behind the camera, out of the frame
        const cam = { w: 320, h: 240, fov: 30, pos: [x, y + 700 + 3000, z + 1500], target: [x, y + 700, z + 300] };
        await agent.shot({ ...cam, pos: [x - 1500, y - 1500, z + 2500], target: [x + 1500, y + 1500, z + 300] });   // the start: the living tree and its model
        const hist = [...studio.ours.place.groups.values()].find((g) => g.refs.some((r) => r.id === "fixplace.HIST"));
        if (!hist?.fullParts) return { setup: "the living tree did not load" };
        await agent.shot(cam); await agent.shot(cam);   // everything the frame needs in the start settled first
        agent.questState('dead');
        const s = await agent.shot(cam);
        const g = [...studio.ours.place.groups.values()].find((g) => g.refs.some((r) => r.id === 'fixplace.DEAD2'));
        return { census: s.census, loaded: !!g?.fullParts, drawn: g?.full?.[0]?.count || 0 }; }""", [x, y, z])
    assert out["census"]["waiting"] == 0 and out["loaded"] and out["drawn"] == 1, out
