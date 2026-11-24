"""The studio's browser tests and what each reaches; the scoped gate (tooling/gate.py `per_test`) runs only the tests
whose reach meets a changed path, and no path outside this folder reaches any of them.

The browser suite is a small smoke set that proves only what a real page can: the page loads and both views draw a
place, touch turns and zooms the view, a tap selects and a drag on the gizmo moves, a save is picked up by another
session and finalised, the start choice over saved work, the thumb sticks, the tablet layout. Every rule of the
page's logic (edits, undo, units, markers, paths, notes, stock, states, the walking mesh) is proved by the fast node
tests beside it (`*.test.mjs`, run by tools/tests/test_studio_web.py) or by a Python test of the server, never here
(the selection's edge-only outline, which needs three.js to draw, by tools/tests/test_studio_outline_rule.py on its source).
A new browser test is added only for something no fast test can prove, each test makes its own state (any one
passes alone), and it is given a row below.

A test's reach is the files whose behaviour it drives, beside the CORE every test stands on (the page shell, the
loader, the scene and the two modules every test drives, the tools and the panels): a change to the core, or to the
suite file itself (its harness), runs every test. The smoke test (test_01_two_views) reaches every page module, so a
module that throws on load still fails a test. tools/tests/test_studio_browser_reach.py checks the declaration is
whole: every test has a row, every named file exists, every page module is core or reached."""
from pathlib import Path

DIR = "tools/places/studio/web"
FILES = ["test/test_browser.py"]
CORE = ["index.html", "sw.js", "css/*", "dev/*", "vendor/*", "js/main.js", "js/api.js", "js/bundle.js", "js/edits.js",
        "js/view.js", "js/objects.js", "js/terrain_mesh.js", "js/terrain_worker.js", "js/terrain_cells.js",
        "js/governor.js", "js/geom.js", "js/xform.js", "js/ids.js", "js/seat.js", "js/panels.js", "js/tools.js"]

_WEB = Path(__file__).resolve().parents[1]
# every module the page loads (agent.js is the look tool's view, proved by tools/tests/test_places_look.py)
PAGE = sorted(p.relative_to(_WEB).as_posix() for p in (_WEB / "js").glob("*.js")
              if p.name != "agent.js" and p.relative_to(_WEB).as_posix() not in CORE)
OUTSIDE = {"js/agent.js": "tools/tests/test_places_look.py"}   # page modules proved outside this suite
SAVES = ["js/offline.js", "js/offline_ui.js"]
B = FILES[0]

REACH = {
    f"{B}::test_16_first_run_and_design": ["js/icons.js"],
    f"{B}::test_01_two_views": PAGE,
    f"{B}::test_03_select_and_manipulate": ["js/units.js", "js/move_map.js"],
    f"{B}::test_13_15_saves_finalise_heartbeat": SAVES,
    f"{B}::test_22_start_choice": SAVES,
    f"{B}::test_27_thumb_sticks": ["js/sticks.js"],
    f"{B}::test_35_tablet_layout_of_the_new_controls": ["js/units.js", "js/people.js", "js/sticks.js"],
    f"{B}::test_36_handles_beside_and_controller": ["js/units.js", "js/sticks.js"],
}
