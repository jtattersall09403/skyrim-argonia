# lane 1.12-loading (2026-11-01): the loading screens

Row: "The loading screens: the model large and central, turning slowly with a slow pan and zoom, under a drifting
mist" (L5). **Still owed.** The record fix is committed. No in-game clip has shown a model yet.

## Root causes (found off-game, measured)
1. **Too small.** 1.9 set each scale to 60 / the mesh's *collision* size, so every model was about 60 units across.
   Vanilla's 298 LSCRs (read from Skyrim.esm with a scratch parser, never committed) show models about 100-180
   units across (scale × mesh size; for example, a shield at 1.6, an actor at 1.4). Some of our meshes also have a
   collision box that doesn't match what you see (the Hist trees are about 4,000 units of geometry).
2. **Off to one side.** Every translation was 0,0,0, but our meshes' visible centres are far from their origins.
   The Sithis shrine's centre is at y = -135. The Hist roots' centre is at (1418, -450, -1239). The canoe's is at
   z = +63. Vanilla moves each model so its centre sits near (-10..-25, 0, -10..-50).
3. **Rotation range** was ±45°. Vanilla is ±180° on nearly every screen.
4. **Why 1.9/1.12 passed:** the L1 check proved a model was named, not its size or place. 1.9 called its scales
   "first guesses until the load stills", and no load still with a model was ever read.

## Fix (committed)
- tools/navmesh/nif_bounds.py: the visible box of a NIF (SSE BSTriShape vertices; bounding spheres for skinned or
  dynamic shapes).
- data/loading-screens.json: each model now carries its measured `bounds`. Scale = 140 / the largest side.
  Translation = (-10, 0, -25) - scale·R·centre. Range is ±180. All 12 LSCR YAMLs were regenerated.
- tools/ui_theme/load_clip.py: grabs the screen through a door load and makes a GIF.

## In game (out/l112load/fix1, argonia-play-ie, after a deploy from this tree)
- The door load (ARG_Ref_ClaywaterStationB1Door, Claywater Station) lasts about 2-3 s and is **black throughout**
  at the grab rate (about 1 still/s, grab.ps1). No model, text or fog showed. A short interior load never gets to
  the model's fade-in.
- `setini "sForcedLoadScreenEditorID:Interface"` faults through the bridge, so a forced screen needs the profile
  INI set before launch.
- Earlier probes failed because the shared machines would not reach the main menu on other lanes' dirty builds,
  and other lanes' jobs took the machine mid-batch.

## Mist and motion (findings, not yet proved)
- The fog the engine draws (MistMenu, `Interface/INTMenuFogParticles.nif`) is Dear Diary's on our stack (1.9
  dropped Tropical's). It draws the vanilla `textures\effects\FXSteamThinAnim.dds` and `GradSteamThin.dds`. If
  vanilla effect textures are quarantined or missing, it renders nothing. Check this first.
- The motion is a camera path in MistMenu (CommonLibSSE-NG MistMenu.h: cameraPath, cameraPathController,
  `sUIMistMenu_DefaultLogoCameraPath`), plus the player's mouse/stick rotation (ProcessMouseMove/Thumbstick). It
  only shows on a load long enough to fade the model in.

## Next (hand-off)
1. Take a clip of a long load: an exterior door, or a cell change across the province. Use a faster grab, or the
   stream's recording (drive.mjs) instead of grab.ps1 (about 1 fps). Force two screens by setting
   sForcedLoadScreenEditorID in the profile's Skyrim.ini before each launch.
2. Have a reader judge the size and centre, then tune TARGET/EXTENT (both constants are in the json's `about`).
3. If no mist shows, check the FXSteamThin textures resolve; else (route 2) find a fog mod for INTMenuFogParticles.
4. If the engine's camera path gives no drift, route 6: our SKSE turns MistMenu's model slowly.
