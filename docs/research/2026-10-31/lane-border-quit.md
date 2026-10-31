# Lane border-quit (2026-10-31): the border lists only inside cells, a collision wall behind it; dev-quit-to-menu

Build-VM lane; no game machine touched. Both fixes wait on the next game slot (re-prove steps at the end).

## 1. The province border

**Vanilla, measured** (a scratch reader over the owned Skyrim.esm; nothing kept): Tamriel has 11,187 exterior
cells; 5,610 list BorderRegionSkyrim (0C5859) in XCLR. Its one area is a 173-point polygon. Of the listed cells,
5,610 have a corner inside the polygon and 0 have none; of the unlisted, 1 has a corner inside. So vanilla's rule is
"a cell lists the border when it overlaps the polygon", and the cells outside never list it. Ours (game-20) listed
it on 33,775 of 33,776 cells, outside ones too.

**Fix (generator rule):** `regions/api.border_cell_runs(poly)` gives the cells overlapping the border polygon (a
corner 1 unit in, or the centre, inside: a cell that only touches the edge from outside is out); `terrain/world.py`
emits them as `borderCells`; `LandWorld.cs` lists the border only on those. Built: **15,876 cells = 126 x 126**
(cells -62..63 both ways) list 08002F in out/ArgoniaWorld.esm; the 17,900 apron cells do not.
L1: `test_border_listed_only_on_cells_inside_the_polygon` (the province square, and a triangle whose diagonal cells
straddle the edge).

**Fallback (native collision wall):** `regions/api.border_wall_refs` places Skyrim.esm's CollisionMarker STAT
(000021) with a box primitive (XPRM type 1, no XTRI), the way vanilla places 762 of its 2,142 collision refs
(SkyHaven's exterior wall among them). Reviewed under 0012: no mesh, sound or text; only the stop reaches the
player. 504 persistent refs (126 per edge, one per cell), `ARG_BorderWall_<edge>_<i>`, in the WRLD override's
persistent cell; box half-sizes (piece length, 64, 16384) so the pieces overlap whether the engine reads XPRM as half
or full extents (not measured). `RegionWeather.cs` writes `Primitive` when a persistent ref carries one. L1:
`test_border_wall_closes_the_polygon`. Note: the exit gates stand 20 m inside, so the wall also closes the roads
out (the intended closed border).

## 2. menus-quit

`dev-quit-to-menu` (skse/ArgoniaBridge/src/ep_dev.cpp, DEV): on the main thread sets `Main::resetGame`
(CommonLib RE/M/Main.h RUNTIME_DATA, the flag `QuitRequested()` in life.cpp reads), then queues the Journal's kHide
(kShow first when it is not open), so LifeMenuSink sees a close with the quit requested and writes the quit save.
In bridge.py NO_RETRY. tests/journeys/menus-quit.yaml: Esc opens the Journal, `close_menu` closes it once, then
`call: [dev-quit-to-menu]`, expecting `saves: ArgoniaSuspend written (quit)` within 15 s and MainMenu within 30 s.
`run_journey --dry`: 7 steps, ok. Not compiled for Windows here (the SKSE build runs at deploy).

## Re-prove in the next game slot
1. Deploy at this commit (`make plugin` output and the new ArgoniaBridge DLL).
2. `run_journey tests/journeys/world-sample.yaml` from s09 (segment-push-west): the player must stay east of x
   -253952 (expect the border region's push-back; if it still fails, the wall must stop the player within ~64 units
   of the edge). If the region alone holds, both remain (the wall is the safety net); if neither, read `refs 000021
   20000` near the edge (are the boxes loaded?) and record XPRM's half/full semantics from where the player stops.
3. `run_journey tests/journeys/menus-quit.yaml` last in its batch: the quit-save log line, then MainMenu.
