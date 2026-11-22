"""The studio's Quest state switch in headless Chromium at the tablet's size: a place with a living and a dead tree
on one enable parent and a state that switches a person off; the switch lists the states, shows each as the player
sees it (refs and people), and marks an edit made in a state other than the start with that state.
Run: ~/.argonia/venv/bin/python -m pytest -q tools/places/studio/web/test/test_states_browser.py (SHOTS=<dir> keeps
the screenshots)."""
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
SHOTS = Path(os.environ.get("SHOTS") or tempfile.mkdtemp(prefix="studio-states-"))
OPP = "SetEnableStateToOppositeOfParent"


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def add_states(fx: Path):
    """The fixture's draft with a parent, a living and a dead tree on it, and two states."""
    d = fx / "bundles" / "draft.fixplace"
    p = d / "spaces" / "exterior" / "refs.jsonl"
    rows = [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
    tree = next(r for r in rows if r.get("kind") in ("building", "static", "furniture") and not r.get("primitive"))
    at = tree["pos"]
    mk = lambda rid, **kw: dict(tree, id=rid, pos=[at[0] + 600, at[1] + 600, at[2]], src=None, seat={"mode": "free", "dz": 0}, **kw)  # noqa: E731
    rows += [dict(mk("fixplace.PARENT"), kind="marker", base=tree["base"]),
             mk("fixplace.HIST", enable_parent={"ref": "fixplace.PARENT", "flags": "0"}),
             mk("fixplace.DEAD", enable_parent={"ref": "fixplace.PARENT", "flags": OPP})]
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    (d / "states.jsonl").write_text(
        json.dumps({"id": "living", "name": "Hist living", "default": True, "parents": {"fixplace.PARENT": True},
                    "key": ["fixplace.HIST"]}) + "\n"
        + json.dumps({"id": "dead", "name": "Hist dead (ending)", "set_by": {"quest": "quest.main.mn19", "endings": ["e-take"]},
                      "parents": {"fixplace.PARENT": False}, "hide": ["fixplace.p1"], "key": ["fixplace.DEAD"]}) + "\n")


@pytest.fixture(scope="module")
def server():
    fx = Path(tempfile.mkdtemp(prefix="studio-states-fixture-"))
    subprocess.run([sys.executable, str(WEB / "dev" / "make_fixture.py"), str(fx)], check=True, capture_output=True)
    add_states(fx)
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
def page(server):
    with pw.sync_playwright() as p:
        b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        ctx = b.new_context(viewport={"width": 1280, "height": 800}, device_scale_factor=1, has_touch=True)
        pg = ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(server + "/")
        pg.wait_for_function("window.studio && studio.ready && studio.log", timeout=60000)
        pg.wait_for_timeout(500)
        if pg.locator("#start .sheet").is_visible():
            pg.get_by_role("button", name="Start from the builder's draft").click()
            pg.wait_for_function("document.getElementById('start').hidden", timeout=30000)
        if pg.locator("#intro").is_visible():
            pg.click("#intro button")
        pg.errors = errors
        yield pg
        b.close()


SHOWN = "(id) => studio.ours.place.byId.has(id)"


def test_the_switch_lists_the_states_and_starts_at_the_games_start(page):
    assert page.locator("#state-wrap").is_visible()
    opts = page.eval_on_selector_all("#state-pick option", "os => os.map(o => [o.value, o.textContent])")
    assert opts == [["living", "Hist living (the game's start)"], ["dead", "Hist dead (ending) (MN19 ending e-take)"]]
    assert page.eval_on_selector("#state-pick", "s => s.value") == "living"
    box = page.locator("#state-pick").bounding_box()
    assert box["height"] >= 28, box        # a finger can take it on the tablet
    assert page.evaluate(SHOWN, "fixplace.HIST") and not page.evaluate(SHOWN, "fixplace.DEAD")
    page.screenshot(path=str(SHOTS / "state-living.png"))


def test_a_state_shows_the_place_as_the_player_sees_it(page):
    page.select_option("#state-pick", "dead")
    page.wait_for_timeout(200)
    assert page.evaluate(SHOWN, "fixplace.DEAD") and not page.evaluate(SHOWN, "fixplace.HIST")
    assert page.evaluate("studio.people.markers.get('fixplace.p1')?.visible") is False
    assert page.evaluate("document.body.dataset.questState") == "dead"
    page.screenshot(path=str(SHOTS / "state-dead.png"))


def test_an_edit_in_a_state_says_which_state_it_belongs_to(page):
    page.select_option("#state-pick", "dead")
    op = page.evaluate("""() => { const r = studio.model.spaces.exterior.refs.get('fixplace.DEAD');
        const [o] = studio.log.push({ op: 'ref.move', id: r.id, before: { pos: [...r.pos] }, after: { pos: [r.pos[0] + 10, r.pos[1], r.pos[2]] } });
        return { state: o.state, n: o.n }; }""")
    assert op["state"] == "dead"
    page.select_option("#state-pick", "living")
    page.wait_for_timeout(100)
    op2 = page.evaluate("""() => { const r = studio.model.spaces.exterior.refs.get('fixplace.HIST');
        const [o] = studio.log.push({ op: 'ref.move', id: r.id, before: { pos: [...r.pos] }, after: { pos: [r.pos[0] + 10, r.pos[1], r.pos[2]] } });
        return { state: o.state ?? null }; }""")
    assert op2["state"] is None             # the start's edits are the place's as ever
    assert page.evaluate(SHOWN, "fixplace.HIST") and page.evaluate("studio.people.markers.get('fixplace.p1')?.visible") is not False
    assert not page.errors, page.errors
