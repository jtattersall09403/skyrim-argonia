# Lane 1.15-r6-camera-native: the camera switched and read natively

- Problem: r6-chain19 lost first person at every relaunch (sky-ab steps 4 and 7, water-types step 2); the runner asserted on the console's IsPC1stPerson.
- Bridge (skse/ArgoniaBridge/src/ep_state.cpp `camera`): `camera first|third|state` on the main thread (on_main_thread task). first|third call PlayerCamera::ForceFirstPerson / ForceThirdPerson, then SetState(the wanted state) when a tween, vanity or furniture state is left holding the camera.
- Every reply carries the native read: `first_person` = currentState == cameraStates[kFirstPerson], `state` (first, third, tween, ...), `native: true`.
- Parser `camera_ask` is pure (protocol/bridge_protocol.cpp), unit-tested in tests/test_protocol.cpp (make check's skse part: 37/37).
- Runner (`_camera`): asks, waits a frame, reads `camera state`; that native read is the primary assert. The frame check (_view_is_first) stays the second opinion for first person after a load or relaunch. An older DLL falls back to IsPC1stPerson, then the F key and cgf.
- Test: tools/tests/test_run_journey.py `test_camera_asserts_on_the_native_state_not_the_console` (console lies 1.00; the step passes and fails on the native state only).
- The DLL needs MSVC: not built on the build VM; the next deploy's "skse build" step compiles it on the game machine.
- Live proof owed: the next deploy, then sky-ab (steps 4 and 7 after a relaunch read `native first`).
