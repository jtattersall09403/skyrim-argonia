# 1.15-r6-camera-after-relaunch
Evidence: r6-chain19 sky-ab; stills after the relaunch (03-...-dawn-s5, 06-...-high-dawn-s0..s4) show the player's body (third person) though `camera first` passed.
Cause (from the runner and report.json; no game run): `_camera` accepted the console read `IsPC1stPerson 1.00` / the bridge's `IsInFirstPerson` alone; after a load or relaunch those can say 1 while the view is third, and later reads say 0.00 (the toggle does not reach the camera).
Fix: tools/run_journey.py sets `view_unverified` on every load and relaunch; the next first-person assert also measures the view (camera third, still, camera first, still, `bridge.frame_difference` >= 0.15), retoggling up to 3 times; failing, it raises "the camera never became first" (relaunch-once rule kept).
Owed in game: next sky-ab batch; the 0.15 threshold is unmeasured (read `view diff` in report.json calls tries).
Not found without the game: why the toggle stops reaching the camera in a relaunched process (no camera API in ArgoniaCore beyond the bridge's ForceFirstPerson).
