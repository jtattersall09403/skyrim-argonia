# Lane 1.15-r5-panel-harness: the panel's camera, stands and player state

Cause of the third-person stills: `Runner.run` sent `camera:` once, after the scene; `step()` never re-asserted it. The
bridge `camera` reply read `IsInFirstPerson()` in the same call as `ForceFirstPerson()`, before the engine switched, so a
reply could pass while the camera was not yet (or later no longer) first. Water-types aborted in `third_person()`
(scene setup): it pressed the F toggle, which after a first-person item flipped the wrong way; the bridge command was not used there.

Fixes (tools/run_journey.py): `_camera` now confirms the bridge answer with a console `IsPC1stPerson` read after 0.5 s;
`step()` re-asserts and reads it before every still and fails the step if it does not hold; `third_person` tries the bridge
`camera third` before F, three tries.

Stands (tools/journeys/__init__.py): `stand_bad` = eye ray meets ground or a plant within 2 m (3-D, the eye point included,
so a stand inside a trunk), or ground slope over 45 deg (`su.STAND_SLOPE_MAX_DEG`, conservative, not yet measured in
game). `frame` counts it; `stand_near` (2 m grid, 16 m) finds a stand where the approach line has none. Refresh of the
panel: 18 vantages, 8 moved, 0 not clear (before: 4 moved, 6 not clear under the new test). Moved: flooded-forest-shore
4.5 m, northern-transition-shore 2 m, western-frontier-shore 4 m, interior-swamp-shore 2 m, deep-river-corridor-shore 14.6 m,
tidal-delta-shore 2 m, northern-transition-high 10.2 m, tidal-delta-high 4 m.

Scene step 0 (tools/argonia_world/panel.py): `tgm`, `tcai` added to tests/scenes/world-panel.txt. Both are toggles: a scene
run twice in one batch would undo them (not seen: the scene is sent once per resolved text, run once per item).

Checks: test_run_journey + test_journey_lint 47 passed; new test_a_stand_inside_geometry_or_on_a_cliff_is_bad; dry run of
world-panel ok (37 steps). Open: test_journeys stale test fails on creatures-kinds.yaml (z 20000 placeholders, another
lane's file in HEAD). In-game proof (camera first in all 37 stills, water-types running) is owed to the next batch.
