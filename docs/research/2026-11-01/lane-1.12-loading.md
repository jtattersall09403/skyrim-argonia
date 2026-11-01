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

## Fix (committed, tuned in game)
- tools/navmesh/nif_bounds.py: the visible box of a NIF. data/loading-screens.json carries each model's `bounds`.
- The vanilla calibration was wrong: vanilla's LoadScreenArt meshes are pre-scaled, so "scale × size" says nothing
  about our meshes. Tuned from in-game stills of a save load (out/l112load/fix3-fix5):
  - 140 units across filled the screen, with the egg up-left (fix3);
  - x+ moves the model *left* on screen, so the target went from 41 to -60 (fix4 put the canoe at the left edge);
  - at 75 units and (-60, 0, -45) the egg was centred left-right but sat behind the text box (fix5);
  - **now 75 units, target (-53, 0, -5)**, range ±180. This is untested in game; round 1 of look-1 judges it.
- tests/journeys/loading-look.yaml (in look-1.yaml): a door into B1, then the road back out, each with a
  90-frame / 15 fps burst and a reader.

## Mist, motion, forcing (measured)
- **Mist: absent.** Every loading frame has a pure black background. Dear Diary's intmenufogparticles.nif wins. Its
  textures (FXSteamThinAnim.dds, GradSteamThin.dds) are not overridden by any mod (force.ps1 listing), so they
  resolve (off-game: both are in Skyrim - Textures5.bsa, and no archive list is set anywhere). The fog still does not
  draw. **Fix shipped:** Dear Diary's fog mesh is dropped (data/dependencies.json `drop`), so vanilla's
  meshes/interface/intmenufogparticles.nif (Skyrim - Meshes1.bsa) draws. It is reviewed under 0012 (steam, no
  Nordic element). Unproven in game. This also changes the main menu's fog.
  If it is still black, MistMenu.showMist (CommonLibSSE-NG offset 0x134) may be off on our stack.
- **Motion: none.** Six frames over about 5 s of the egg screen are identical. The engine adds no drift on our
  stack, so route 6 applies: ArgoniaCore turns MistMenu's model slowly (RE::MistMenu::angleZ at 0x104;
  loadScreenModel at 0xF0). **Not built.** The loading screen draws on the loader thread while the main thread is
  blocked, so the driver has to write from its own thread into a menu that can close at any moment. I did not ship
  that crash risk without a game run.
- **Forcing:** setting sForcedLoadScreenEditorID in Documents\My Games\Skyrim Special Edition\Skyrim.ini before
  launch did not force the screen (rormasu was asked for, egg-tooth showed). The MO2 profile may keep its own
  INIs. Screens come up at random, which is enough for two different screens over two loads.
- Door (interior) loads last about 2-3 s and show only black. The model shows on longer loads (saves, exteriors).

## State at hand-back (planner: no game; the owner checks)
- Built and on main: size and centre, the ±180 turn, the vanilla fog mesh, and the loading-look journey.
- Not proved: all of it in game. The last tuning step (target z -45 to -5, x -60 to -53) comes from a still and has
  not been re-shot.
- Not built: the slow turn and drift (route 6, above). Forcing a screen through the INI didn't work (above).
