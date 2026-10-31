# Lane game-20 (2026-10-31): one deploy, the border link, the deploy heartbeat; hand-off at the g6 move

## Deploy
g20-deploy2 at 4bc31c8 + the border change: every step OK (skse 208 s); base save timed out once on `coc`
("main thread did not run the task within 3000 ms"), rerun alone OK in 10.7 s. Transient; not changed.

## Done (pushed)
- deploy.sh heartbeat (game-19 gap): a background loop runs `run.sh ps hostname` every 300 s (each call touches
  C:\argonia\state\busy), killed on exit. A long single step can no longer outlast idle-stop's 15 min.
- Border region linked from every cell (8cfd642, 990e3a9, d3c163d). Skyrim.esm lists BorderRegionSkyrim (0C5859)
  in 5,610 of 17,568 cells' XCLR; ours listed none. Now the border has an ArgoniaWorld.esm shell (08002F,
  formid row `ARG_Region_borderShell`, entity `land_region.border.shell`); Argonia.esm overrides it with the
  BorderRegion flag (0x40) and the province square; 33,775 of 33,776 cells list it. Sample manifest re-pinned;
  test_border_has_a_shell_every_cell_lists added.
- tk-dodge.toml: the machine's copy had the same content as the stage but CRLF line endings, rewritten
  10/31 04:13 machine time (during game-19's g19-b2 batch window; it was not a push). The staged file was put back.
  `stack.py verify` still says "installed files differ" with no file named after that (22,574 checked, 0 to hash).
  Not resolved: rerun `stack.py verify --full`.

## Still red (precise)
1. world-sample s09-segment-push-west: STILL RED after the XCLR link. Live: start x -251904, then 4 pad pushes
   (2.9 s each) gave -252924, -253983, -255058, -256129, all in ARG_Province. The border is -253952. The record
   checks out: the REGN override has flag 0x40, RPLI 0, 4 points CCW (the same sign as vanilla), and RDAT/RDMP.
   Differences from vanilla left to test: vanilla has RCLR and WNAM 0x3c, ours WNAM points at our WRLD; vanilla's
   cells outside the border may not list it. Next: compare cell -63,22's XCLR against a vanilla border cell (are
   outside cells unlisted in vanilla?), then try listing the border only on inside cells. Fallback: collision
   pieces (invisible-wall STATs) on the province edge from the generator.
2. menus-quit: live, ESC (engine) opens the vanilla Journal on Quests with nothing highlighted (reader), and
   engine `E` x2 does not change the tab. The bridge has no control over Main::resetGame (grep: no
   resetGame/quitGame in skse/ArgoniaBridge). Next: add a DEV bridge call that sets resetGame and closes the
   Journal, so our quit_watch (life.cpp:423-437) fires on the close, then check "saves: ArgoniaSuspend written (quit)".
3. die-and-recover second-death, ui-sweep favourites and barter, xLODGen restore and the Claywater still, touch B
   on the journal: not run. The g6 move at 06:30 took the slot.
