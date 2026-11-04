# Lane 1.15-r6-light: the olive noon under canopy, the grey dawn, the missing light shafts

L1 and L2, from the bytes. Inputs: Skyrim.esm, Update.esm and Tropical Skyrim.esp in `~/games/skyrimse/Data`, and the
DB. Commit 971f0eee. No game was run.

## 1. Climate and dawn
SkyrimClimate 000812 as the load order writes it is Tropical Skyrim.esp's override. Its TNAM is byte-equal to
Skyrim.esm's: 33/60/96/123, which is sunrise 05:30-10:00 and sunset 16:00-20:30. Ours (climate black-marsh) is
05:30-07:00 and 18:00-19:30, the lore's twelve-hour tropical day. The journeys' 06:30 lies inside both windows, and
our window lies inside the template's sunrise window. The journey hour does not move. The test
`test_climate_dawn_hour_inside_the_template_sunrise` pins this.

**Not measured:** how the engine blends colours across the window. CommonLibSSE's Sky.h carries only the
begin/end getters. One cause is still open: at 06:30 we are 67 % through our 90-minute window, so the scene may
already be blending toward the navy day colours. The fix below also matters: before it, clear-dry's sunrise fog,
sunlight and grade were our own (fogNear 9F8664 against the template's 2F4E5B, tint 0), not the template's.
**L4 state read owed:** read the sky colour at gamehour 6.0, 6.25, 6.5 and 6.75 on the bridge.

## 2. The noon cast under canopy
**Measured from the journey:** every noon stop forces the same weather, clear-dry, Argonia.esm|0x000E9B
(world-panel.yaml lines 48, 196, 344, 492, 640, 788). That covers the clean open lagoon and the olive
deep-river-corridor and deep-sink-basin shores. Identical records cannot make a cast at one stop and not another.
**So the weather is not the cause.**

What differs at those stops is the canopy: the frame is filled with leaf cards in place of sky. Lane r5-sky-2
measured King of the Murkmire's snowgum leaf cards (snowgumbranches01_d) at an olive hue of 62 and saturation 0.47.
→ **lane 1.15-r6-mesh-patcher** (the leaf diffuse and vertex colour).

The records were still not the template's, and the brief requires them to be. They are now:
- **clear-dry (Pleasant):** all 17 NAM0 slots and the four DALC are SkyrimClear's (Tropical). Before the change,
  20 of 20 fog and sunlight fields differed, for example fogFar day A7BABB against the template's 3995F9.
- **Every IMGS:** CNAM and TNAM are the template's. Ours had tint 0 and our own grade. ClearDAY_FF (Tropical) is
  sat 1.3, bright 1.1, contrast 1.25, with a tint of 0.5575 at (0.86, 0.88, 0.68). That is the vanilla-style warm
  tint, and it applies at every stop alike.
- **Proof:** `checks.sky_light` and `checks.sky_grade` in `test_written_sky_follows_its_templates`, which passes
  against the bytes ArgoniaGen writes.
- **Check change:** `weather_slots` no longer applies the round-4 horizon_line and luma heuristics to a weather
  whose slots are all the template's. Tropical's own SkyrimClear fails them: its sunrise horizon and fogFar luma are
  both 139, and its sunrise sunlight luma is 126 against our 147 floor.
- **Not changed:** mist and the other non-clear weathers keep their authored fog, held by the mist_fog_cast rule.

## 3. Light shafts
- **What draws shafts:** the engine's volumetric lighting. That is the WTHR HNAM field (four VOLI links: sunrise,
  day, sunset, night), switched on by SkyrimPrefs [Display] bVolumetricLightingEnable and its quality setting, and
  rendered under Community Shaders by its VolumetricLighting feature.
- **The game files:**
  - Skyrim.esm's HNAM is 1 byte (0x2D) and it holds no VOLI.
  - Update.esm carries 36 VOLI and real links. For example, SkyrimClear has 0D53/0D51/0D52/0D58, and SkyrimFog
    and FogMA have 0D5B/0D59/0D5C/0D5A.
  - **Tropical Skyrim.esp carries HNAM all null on all 8 templates we use.** It is an LE plugin (HEDR 1.70; SSE is
    1.71), so the null is the converter's empty SSE field, not a design choice.
- **What our weathers carry:** the writer now takes the winner's links where it has any, else Update.esm's. So
  clear-dry and mist carry Update's VOLI. `checks.volumetric_links` checks this and the test asserts both are
  non-null.
- **Why no shafts show today:** the laid Community Shaders override
  `SKSE/Plugins/CommunityShaders/Overrides/Argonia_VolumetricLighting.json` (data/dependencies.json) sets
  ExteriorEnabled false. That follows the planner's round-5 sky-bisect ruling (owner-brief 2026-11-03), and this lane
  did not reverse it.
- **For the planner:**
  - Re-enable ExteriorEnabled once the residual grey is bisected.
  - stack.ps1's ini step (infra/gpu-box/stack.ps1:78-91) sets no bVolumetricLightingEnable. The deploy should set
    SkyrimPrefs [Display] bVolumetricLightingEnable=1 (infra, outside this lane's paths).

## 4. Tests
- regions tests (test_regions and test_sky_writer): 28 passed. With the checks tests: 49 passed (venv python).
- The full tools/argonia_world suite did not finish inside 280 s and was not run to the end.

## 5. L4 owed (planner's batch; needs a rebuild of Argonia.esm)
- world-panel, noon: deep-river-corridor-shore and deep-sink-basin-shore (the canopy cast persists → mesh-patcher),
  with coastal-lagoon-shore as the control.
- sky-ab, 06:30: coastal-lagoon-shore and western-frontier-high (rose horizon, slate zenith). Add the state read at
  6.0/6.25/6.5/6.75.
- Shafts: world-panel dawn mist stops 03/05/07/09, only after the CS VolumetricLighting exterior is re-enabled and
  bVolumetricLightingEnable=1 is set.
