# Diagnosis 2: the two crashes and four journey failures (batch 20261030T151243)

I took the full crash logs' first 150 lines from the machine into the scratchpad (crash-2026-10-30-15-22-42.log and crash-2026-10-30-15-37-23.log).

## 1. The crashes in 09 fight-roll-burden and 12 smoke (game; plus a code gap in our evidence)

- **09** (uptime 2:16, 3 s after the save load at 15:22:40): EXCEPTION_ACCESS_VIOLATION on the main thread at SkyrimSE.exe+100F207 (`call [rax+0x10]` with rax = 0). That is a null vtable call. Every probable frame (0 to 10) is in SkyrimSE.exe: 77322, 70723, 76019, 36818, 76079, 36567, 36564, 36544, 109636, which is the render or update path. The relevant objects are NiSourceTexture `textures\clutter\soulgem\SoulGemCommon_n.dds` (a vanilla texture), WorldRoot Camera and Main.
- **12** (uptime 14:22): the job thread jumped to garbage at 0x024600000000. The stack scan shows 69036, 21891 and the 6937x cluster. The objects are BSMultiBoundAABB, BSGeometryListCullingProcess and BSJobs::JobThread, with Console on the stack. The router logged Fader Menu and Mist Menu at 15:37:20 (a loading screen), and the scene apply took 9.6 s.
- **Cause:** both crashes are engine crashes in a cell transition that the scene's travel line forces right after a save load in a long-lived process. In 09 it is `player.moveto ARG_Ref_ClaywaterStationAmbushPlayer`; in 12 it is `cow tamriel 2 -4` (tests/scenes/claywater-ambush.txt, last line; tests/scenes/plain-armed.txt, last line). This is the same class as game-6, which the scenes' own comment records. No frame is in ArgoniaCore, ArgoniaBridge or any mod DLL; EngineFixes appears only in the stack scan. The cause is not our DLL, not a record and not the relaunch path: neither crash came right after a relaunch, and the processes had been up 2 and 14 minutes.
- **Code gap:** tools/run_journey.py:536 fetches the crash log with `Get-Content -Tail 200`. That keeps only the module list and loses the header, the call stack and the objects, which sit in the first ~60 lines.
- **Fix:** (a) run_journey.py:536, fetch `-TotalCount 120` (the head) for the crash log. (b) tools/run_batch.py, before sending the scene: wait until the load has settled (no Loading Menu or Fader Menu open, the player's 3D loaded), then wait about 2 s more. The travel line then runs on a settled world, not inside the load's tail.
- **Re-prove:** run `09 fight-roll-burden` and `12 smoke` 3 times each in one batch; the bar is 0 crashes.

## 2. 02 claywater-look, step station-house-inside (journey)

- tests/journeys/claywater-look.yaml:32 moves the player onto the door ref with no offset or facing. The reader saw "[E] Open / Claywater Station House" at screen centre after the 6 s wait, with the player still outside at the porch, so the E press did not open the door. The expectation (`>> 0`) is right.
- claywater-walk.yaml:29-32 passes the same check. It uses `player.moveto ARG_Ref_ClaywaterStationB1Door 37 60 20` plus `player.setangle z 212` and waits 2 s before the E.
- **Fix:** use that same stand-off and facing at line 32.
- **Re-prove:** the one step; GetInWorldspace prints `>> 0`.

## 3. 08 fight-lock-on, step beyond-range (journey): cut it

- tests/journeys/fight-lock-on.yaml:17-19 tests TDM's own acquire and break rules. Our only stake is the value 2000, and tools/argonia_world/content/combat_wiring_rows.py:61 marks it as "GUESS: mod default", so the step tests the modder's work (owner, 2026-10-30).
- The step also relies on an assumed distance: it never reads `dist`, and the deserter closes in during the 2.8 s.
- **Fix:** delete the step. If anything, cover our integration (the setting reaches TDM's config) at L1 against the wiring row. Keep lock-near, which proves our pad-to-TDM join.
- **Re-prove:** `run_journey fight-lock-on`, which ends green on lock-near.

## 4. 20 w3-weather-stills (journey)

- tests/journeys/w3-weather-stills.yaml:11, 15, 19 and 23 have the arguments swapped since d278ae3: `set gamehour to ARG_Weather_mist` and `fw 6`.
- Our weathers are in plugin/Argonia/Weathers/:

  | EditorID | Form ID |
  |---|---|
  | ARG_Weather_mist | 00080F |
  | ARG_Weather_storm | 000811 |
  | ARG_Weather_tannin_haze | 000812 |
  | ARG_Weather_squall | 000810 |

  These are form IDs in Argonia.esm, by EditorID; `fw ARG_Weather_tannin_haze` already works in the scenes.
- **Fix:** write each step as `set gamehour to 6` then `fw ARG_Weather_mist`, and the same for every step. The expect `contains: 6` is also wrong: `read weather current` returns form_ref(currentWeather) (skse/ArgoniaBridge/src/ep_world.cpp:183). Expect `contains: ARG_Weather_mist`, or the form ID if form_ref prints no EditorID.
- **Re-prove:** step mist-06.

## 5. 11 quest-board, step strike (journey)

- tests/journeys/quest-board.yaml:34 has 3 × (120 + 900) = 3060 ms, over the 3000 ms cap.
- **Fix:** `do: [{pad: "RB:120 wait:900"}, {pad: "RB:120 wait:900"}, {pad: "RB:120 wait:900"}]`.
- **Re-prove:** step strike.
