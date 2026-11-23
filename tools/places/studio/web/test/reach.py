"""The reach of the studio's browser tests, test by test: the scoped gate (tooling/gate.py `per_test`) runs only the
tests whose reach meets a changed path, so one page module costs its own tests and not the whole suite.

A test's reach is the files whose behaviour it drives and asserts, beside the core every test stands on. CORE is
the page shell, the loader, the scene and the two modules nearly every test drives (the tools and the panels): a
change to any of them, or to a suite file itself (its harness), runs every test. Every other page module is in the
reach of the tests that drive it, and of the smoke test (test_01_two_views: the page loads and both views draw), so
a module that throws on load still fails a test. tools/tests/test_studio_browser_reach.py checks the declaration is
whole: every test is here, every named file exists, every page module is core or reached.

When a test starts driving another module, add it to that test's row. test_offline.py drives the real studio server
on the real places (minutes, run by hand when the offline path changes); the saves tests here cover offline.js."""
from pathlib import Path

DIR = "tools/places/studio/web"
FILES = ["test/test_browser.py", "test/test_states_browser.py", "test/test_state_switch_draws.py"]
CORE = ["index.html", "sw.js", "css/*", "dev/*", "vendor/*", "js/main.js", "js/api.js", "js/bundle.js", "js/edits.js",
        "js/view.js", "js/objects.js", "js/terrain_mesh.js", "js/terrain_worker.js", "js/terrain_cells.js",
        "js/governor.js", "js/geom.js", "js/xform.js", "js/ids.js", "js/seat.js", "js/panels.js", "js/tools.js"]

B, S, W = FILES
STATES = ["js/agent.js", "js/states.js", "js/quests.js", "js/quest_ops.js", "js/needs.js", "js/people.js"]
NOTES = ["js/notes_bar.js", "js/note_groups.js"]
SAVES = ["js/offline.js", "js/offline_ui.js"]
_page = sorted(p.relative_to(Path(__file__).resolve().parents[1]).as_posix()
               for p in (Path(__file__).resolve().parents[1] / "js").glob("*.js"))

REACH = {
    f"{B}::test_16_first_run_and_design": ["js/icons.js"],
    f"{B}::test_01_two_views": [p for p in _page if p != "js/agent.js" and p not in CORE],   # the smoke test
    f"{B}::test_01_mismatch_warning": [],
    f"{B}::test_02_performance_and_lazy_models": ["js/thumbs.js"],
    f"{B}::test_03_select_and_manipulate": ["js/units.js", "js/move_map.js"],
    f"{B}::test_04_from_the_source": ["js/units.js"],
    f"{B}::test_05_search": ["js/thumbs.js"],
    f"{B}::test_06_07_history_and_calls": NOTES,
    f"{B}::test_08_people": ["js/people.js", "js/routes.js", "js/navroute.js"],
    f"{B}::test_09_interiors": [],
    f"{B}::test_10_land": [],
    f"{B}::test_11_plants": [],
    f"{B}::test_12_paths": ["js/path_paint.js", "js/paint_rule.js"],
    f"{B}::test_13_15_saves_finalise_heartbeat": SAVES,
    f"{B}::test_14_choosers": [],
    f"{B}::test_16_dark_portrait": [],
    f"{B}::test_17_walkway_clear_why_seat_modes": [],
    f"{B}::test_19_missing_texture_fallback": [],
    f"{B}::test_20_notes_for_the_agent": NOTES,
    f"{B}::test_21_compass": [],
    f"{B}::test_21_effects_never_drawn": [],
    f"{B}::test_21_selected_shows_where": ["js/where.js"],
    f"{B}::test_21_lights_seen_and_handled": ["js/lights.js", "js/lighting.js"],
    f"{B}::test_21_invisible_walls": ["js/markers.js", "js/prims.js"],
    f"{B}::test_21_grass_at_viewing_distance": ["js/grass.js", "js/grass_rules.js"],
    f"{B}::test_21_world_map": ["js/atlas.js"],
    f"{B}::test_22_start_choice": SAVES,
    f"{B}::test_23_contents_and_identities": ["js/contents.js", "js/stock.js", "js/people.js"],
    f"{B}::test_24_note_bar": NOTES,
    f"{B}::test_25_day_and_night": ["js/lighting.js", "js/lights.js", "js/people.js", "js/water.js", "js/water_look.js"],
    f"{B}::test_26_place_switch_releases_gpu_memory": [],
    f"{B}::test_26_context_lost_during_switch_still_draws": [],
    f"{B}::test_26_blank_view_says_so": [],
    f"{B}::test_27_thumb_sticks": ["js/sticks.js"],
    f"{B}::test_28_walking_mesh": ["js/walk_layer.js", "js/walk_tools.js", "js/walkmesh.js", "js/navroute.js"],
    f"{B}::test_29_paint_ground": ["js/paint_tool.js", "js/paint_rule.js", "js/path_paint.js"],
    f"{B}::test_23_raise_of_a_seated_door_stays": ["js/units.js"],
    f"{B}::test_30_units_move_whole": ["js/units.js"],
    f"{B}::test_31_people_select_and_move": ["js/people.js", "js/routes.js"],
    f"{B}::test_32_drag_maps_to_the_view": ["js/move_map.js"],
    f"{B}::test_33_camera_about_the_selection": ["js/sticks.js", "js/units.js"],
    f"{B}::test_34_markers": ["js/markers.js"],
    f"{B}::test_35_tablet_layout_of_the_new_controls": ["js/units.js", "js/people.js", "js/sticks.js"],
    f"{S}::test_the_switch_lists_the_states_and_starts_at_the_games_start": STATES,
    f"{S}::test_a_state_shows_the_place_as_the_player_sees_it": STATES,
    f"{S}::test_an_edit_in_a_state_says_which_state_it_belongs_to": STATES,
    f"{S}::test_a_capture_draws_the_people_a_state_shows_and_not_those_it_hides": STATES,
    f"{W}::test_a_switch_draws_the_ref_it_shows": STATES,
    f"{W}::test_the_agent_shot_waits_for_a_model_a_switch_asks_for": STATES,
}
