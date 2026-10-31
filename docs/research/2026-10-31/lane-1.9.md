# lane-1.9: the front door and loads (2026-10-31)

Off-machine work done and committed; every in-game row is owed. argonia-play-2 (London g6 spot) was reclaimed at
~16:00 UTC during the prewarm, and `run.sh up` then exited 3 (no capacity). The coordinator stopped the retries.

## Done (L1/L2, green)
- **Classic loading screens (row 4, data):** each of the 12 LSCRs names a STAT of ours (`ARG_LoadArt_<fact>`,
  000BFE–000C09) over a mesh from our stack. The pairing, scale, rotation, rotation range and translation are in
  data/loading-screens.json. The meshes: canoe (Sailboats Expanded), Hist tree and roots, taproot, fruit and crocodile
  (HTBM Cipactli), eggs (HTBM), Hist sapling, totem, Sithis shrine, wall hanging and mud hut (Mud Mother Grove). Each
  scale is 60 / the mesh's measured collision size (tools/navmesh/nif.py). Scale and offset are first guesses until
  the load stills. The crocodile has no collision, so its size is guessed.
  `loading_screen_errors` now requires a model, and a test checks each model's `mod` is a dependency row.
  tools/ArgoniaGen/LoadScreenRecords.cs writes InitialScale, InitialRotation, RotationOffsetConstraints and
  InitialTranslationOffset. The sourcing register's four rows name the meshes, which are referenced by path only.
- **Scrolling bar (row 2):** Tropical Skyrim ships `meshes/interface/intmenufogparticles.nif`, which draws
  `textures/interface/objects/background.dds` and `background02.dds`, plus a LOADSCREENWALLPAPER. In the MO2 order it
  outranks Dear Diary's steam-fog version. These are dropped from its dependencies row (`drop`); the next stack push
  removes them.
- **Walk save (row 1):** `argoniabase` is ARG_HoldingCell, a black room where only the HUD shows. That matches the
  owner's report, but it is not yet reproduced in game. infra/gpu-box/base_save.py (deploy's last step) now applies
  the claywater scene and saves **ArgoniaWalk**. To remake it alone, run `base_save.py` at the main menu (1.10).
  tests/journeys/walk-save.yaml proves it: relaunch, load ArgoniaWalk, then walk more than 300 units.
- **Squash (row 4):** retheme sets `Stage.scaleMode = "showAll"` as loadingmenu.swf's first frame-1 action
  (swf.set_stage_scale_mode; unit test). This is unproven in game: it only works if the engine's exact-fit stretch
  is the cause.
- **Intro parchment (row 3), a hypothesis:** the start-up Loading Menu (Dear Diary's sheet is 13 % opaque) shows over
  the main menu's parchment wallpaper. That would give "menu flashes, blank parchment, menu again".
  tools/ui_theme/front_door.py grabs about one still a second from launch to the menu to decide it.

## Owed (in game): tests/journeys/batches/lane-1.9.sh
The batch runs in this order: deploy; check that oblivion-loading-menu and Tropical's interface meshes are gone from
the machine; argoniabase reproduced (player read, pad, still); walk-save.yaml; front_door stills; drive.mjs load
stills (3 coc loads) at desktop, v5-unfolded and v5-folded; stop. A reader then judges the stills against each row.
